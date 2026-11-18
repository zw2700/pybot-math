"""The tables the composer's safety net reads from.

Pools, frozensets and word lists with no logic of their own, kept in one file so that
`fallback.py` - the readings that decide which of them answers - stays a size a person can work
in. Everything here is imported back into `fallback` under the same name, so `fallback.POOL` and
`from .fallback import POOL` are unchanged, and the pools are the same objects they were.
"""

import re

from . import finding_out



# Words that carry no meaning for matching, dropped before a phrase is looked for, so
# "what can you actually help with" still finds "what can you help".
FILLERS = frozenset(("actually", "really", "exactly", "even", "just", "please", "basically",
                     "honestly", "literally", "anyway", "still", "perhaps", "maybe"))

_BOUNDED = {}

GREETING = (
    "Hey! What's on your mind?",
    "Hi there — what can I help with?",
    "Hello! Good to see you. What are you thinking about?",
    "Hey! I'm here. What would you like to talk about?",
    "Hi! What's up?",
)

THANKS = (
    "Any time!",
    "You're welcome — glad that helped.",
    "No problem at all. Shout if you need anything else.",
    "Happy to help.",
)

# An honest "I don't know" still has to be useful, and what is useful depends on the question: a
# decision only the person can weigh, wording the bot can draft once it knows who it is for, a
# health question someone qualified settles. A question of fact, and a "how do I" that wants
# steps, keep the search suggestion below: a guide or a search is the honest route for those, and
# the bot should not pretend otherwise.
# A decision is the speaker's to make, so the bot says that once, in a line, then offers the one
# thing it can do: weigh it with them. Each line used to hedge twice ("that wants someone who knows
# the whole situation… I don't know your situation well enough") to a person asking about a water
# bottle, an umbrella or buttercream, which reads as a wall where "that's your call — what are you
# weighing?" reads as a friend. Health decisions keep UNKNOWN_HEALTH, which names who can decide,
# and a money decision keeps UNKNOWN_MONEY below.
UNKNOWN_DECIDE = (
    "That's your call, not mine — I don't know enough about your side of it. Tell me what you're "
    "weighing and I'll help you pick.",
    "Can't call that one for you, sorry. Say what you'd lose either way and I'll lay it out with "
    "you.",
    "Not mine to decide, sorry. Tell me what matters most here and I'll help you think it "
    "through.",
)

# A money decision is the one kind where a general answer can cost real money, so it gets its
# own pool; naming money in the generic lines said "someone qualified" about umbrellas and gym kit.
UNKNOWN_MONEY = (
    "Not a call I can make for you, sorry: anything money-shaped wants someone who can see the "
    "whole picture, and free advice is easy to find - Citizens Advice, a bank adviser, a broker. "
    "Tell me what you are weighing anyway and I'll help you lay it out.",
    "That is an adviser's call rather than mine, sorry - a free debt or money advice service will "
    "know your rules and your numbers. Say what matters most and I'll help you get it straight "
    "before you ring them.",
    "I don't know enough about your money to call it, and a guess is the worst thing here. What "
    "would each choice cost you, and what would it leave you free to do?",
)

# The person hands the choice straight back with nothing in it: "you pick", "up to you", "you
# decide", "youre the expert", "dont mind, whichever you think". When the options are on the
# screen the answer is a pick and memory's `prefer` already makes it ("what should i watch
# tonight" / "you pick" -> "I'd say Groundhog Day for comedy"). This is the turn where there is
# nothing to pick from, and it used to get whatever the generic pool had: the search hedge ("you
# pick" -> "I don't know enough to answer that honestly. A search should sort you out quickly"),
# "I'm a chatbot - here to help and chat" for "your call", and "Thanks for telling me - I'm here
# if you want to dig into any of that" for "up to you". Nobody hands a friend the choice to be
# sent off to a search engine, and being handed the choice is a compliment: the reply takes it and
# asks for the choice in one line, which is the turn a friend gives and the one that moves the
# chat on.
HANDS_BACK = (
    "Happy to - what are you choosing between?",
    "Then give me the choice: what's on the table?",
    "I'll make the call if you tell me the options - what are they?",
)

# Squeezing a spot, picking a scab, popping a blister: ordinary, and the answer is the same every
# time - leave it alone. It came back as "that's your call, not mine" or a search hedge, which is
# neither advice nor help, and the health pool's 111 line is too heavy for a chin. A pharmacist
# is named only for the turn where it goes hot and spreading.
# "Should I put a plaster on it" is asking whether to cover it, and the squeeze line does not
# answer that. A plaster is the right answer to a small wound: it keeps it clean and stops the
# hand going back to it.
PLASTER_IT = (
    "Yes - cover it with a plaster and leave it alone: that keeps it clean and stops your hand "
    "going back to it. Change it daily, and get it looked at if the skin around it goes red and "
    "spreading.",
    "Cover it and leave it be. A plaster does more than air does for a cut or a graze; change it "
    "each day and see a pharmacist if it starts to look angry.",
)

SORE_HANDS = (
    "Leave it alone - don't pick or scratch it. Squeezing pushes the infection deeper and it "
    "comes back worse, and keeping it clean does more than pressure does; it settles in a few "
    "days on its own.",
    "Don't squeeze, pick or scratch it. A warm flannel for ten minutes and clean hands will do "
    "more than pressure will; if it goes hot, red and spreading, a pharmacist can look at it "
    "today.",
)

GO_TO_BE_SEEN = (
    "Go, and have someone drive you rather than driving yourself. Take your medicine list if you "
    "have one — they ask for it first.",
    "Go now rather than waiting to see if it settles. Whether something needs closing, strapping "
    "or an X-ray is their call, not one to make from here.",
    "Go, and if you get worse on the way — breathing trouble, heavy bleeding, or you cannot stay "
    "awake — ring 999 rather than carrying on.",
)

RING_FOR_HELP = (
    "Yes — ring 999 or 911 now, and stay on the line while you talk. If it turns out to be less "
    "serious than you thought, they would far rather hear from you than not.",
    "Ring now rather than waiting to be sure: 999 or 911, say where you are and what has "
    "happened, and keep the person talking while you dial.",
    "Call 999 or 911 straight away. What happens in the next few minutes matters more than "
    "anything either of us can work out from here.",
)

# Two sentences and no "otherwise" clause: the verdict composer reads an "otherwise ..." in the
# answer above it as the condition for this turn, so "should i call the police" followed by "what
# should i do" came back "Nothing you need to do yet - it matters if it is happening now"
# (clean-sage, #4381). The number for the other case is a sentence of its own instead.
RING_THE_POLICE = (
    "Ring 999 now, for anything happening as you read this or for anyone in danger. Once it is "
    "over, ring 101 instead. Either way the call is free and they would rather hear it.",
    "999 now, for anything happening or anyone in danger. 101 for what has already happened. You "
    "can say you are not sure it counts — deciding that is their job, not yours.",
)

_A_PERSON = frozenset((
    "him", "her", "them", "mum", "mom", "mother", "dad", "father", "sister", "brother", "friend",
    "friends", "boss", "ex", "partner", "husband", "wife", "girlfriend", "boyfriend", "girl",
    "guy", "colleague", "gran", "granny", "grandma", "grandad", "grandpa", "nanny", "aunt",
    "uncle", "cousin", "neighbour", "neighbor", "landlord", "landlady", "teacher", "parents",
    "family", "son", "daughter", "flatmate", "roommate", "manager", "someone", "anyone",
    "his", "hers", "theirs", "mums", "moms", "dads", "sisters", "brothers", "friends"))

_A_SOCIAL_THING = frozenset((
    "wedding", "party", "funeral", "birthday", "dinner", "drinks", "christening", "reunion",
    "barbecue", "bbq", "gig", "christmas", "housewarming", "wake", "graduation", "do", "meal"))

CONTACT_ANSWER = (
    "Send it. One short line, nothing to explain, and if you would still be glad you had sent it "
    "tomorrow, that is your answer. Tell me what you would write and I will make it shorter.",
    "Reply, and keep it to the one thing you want back. Most of the weight here is in the "
    "drafting, not in the message — tell me what you are trying to say and I will tighten it.",
    "Send the short version. The paragraph you keep rewriting is the one that never goes.",
)

CALL_ANSWER = (
    "Ring them. The wait is worse than the call nearly every time, and you can keep it short "
    "once you are through — say the one thing you actually want to say.",
    "Call, and plan the first sentence only. You do not owe anyone the whole conversation in "
    "one go, and you can always say you have to go.",
)

GO_ANSWER = (
    "Go. If you would still be glad you went tomorrow, go — an evening out costs less than the "
    "wondering about it.",
    "Go, and give yourself an exit: turn up on time, leave when you have had enough, and you get "
    "the bit that matters without the long haul.",
    "Yes, go — and give yourself a job while you are there (drinks, photos, helping set up). It "
    "is the standing around that makes those things hard, not the people.",
)

ASK_OUT_ANSWER = (
    "Ask. The worst case is a no, which you do not have yet, and a plain \"fancy a drink "
    "sometime?\" gives them an easy way to say either thing. One line, then let it go.",
    "Ask, and keep it small and specific — a drink, a coffee, a thing you are already going to. "
    "Low stakes is what makes it easy to say yes to.",
)

APOLOGY_ANSWER = (
    "Say it once, plainly, and let it stand: \"I'm sorry about the other day\" lands better "
    "than a paragraph of explaining.",
    "Yes — what you did, that you are sorry, and nothing about what they did back. Short and "
    "specific is what makes an apology believable.",
)

UNKNOWN_WORD = (
    "I can draft that: tell me who it's for and what you want them to do, and I'll write something "
    "you can send.",
    "I'm not sure what to say without the details, but I can write it: give me who it's for and "
    "the one thing you need from them.",
)

# The same invite when the line already says who it is for ("can you send a text to my
# landlord"): asking who it's for there asks for what the person just said, so this asks for the
# gist and the tone instead - the two things that are actually missing.
UNKNOWN_WORD_NAMED = (
    "I can draft that. Give me the gist in your own words and how you want it to land - plain, "
    "apologetic, firm - and I'll write something you can send.",
    "Happy to write it for you. Tell me what you want them to know or do, and roughly what tone, "
    "and I'll put a version together you can edit.",
    "I can write that. A line or two of what you want to say is enough to start, and you can cut "
    "it down or soften it once you see it.",
)

UNKNOWN_HEALTH = (
    "Not one I can call for you, sorry: I cannot examine anything from here, and this is the kind "
    "of question where a guess does real harm. A GP, a pharmacist or 111 will tell you in a few "
    "minutes, and if it is getting worse, do not wait for an appointment.",
    "I cannot weigh that one safely, sorry. Ring 111 or your surgery and describe it as you did to "
    "me - they will say whether it needs looking at today, and it costs one phone call.",
)

# A body is not a machine with parts to swap, and the person saying so knows it: "my back keeps
# going" then "is it worth fixing myself" is a joke about themselves, and the health advisor's
# "ring 111" line answers it as if they had asked whether something is wrong inside them. What a
# friend says is that it is not that simple, and that time and a look from someone is the test.
BODY_IS_NOT_A_MACHINE = (
    "If only it were that simple. Rest it, keep moving gently, and if it has not settled in a week "
    "or two, get it looked at rather than working on it yourself.",
    "The parts are not sold separately, sadly. Give it a week or two of gentle movement, and have "
    "someone look at it if it is no better by then.",
    "I would not start taking yourself apart. Time and gentle movement do most of it, and a GP is "
    "the one to see if it is still the same in a week or two.",
)

# A two-way decision ("whether to move in with her", "between the two flats") is weighed by what
# pulls each way. An open one ("i dont know what to do with my life") has no two sides to hold up,
# and asking which way you are leaning there asks about a choice the person has not found yet: that
# class belongs to the neutral branch's own worth-and-direction pool, not here.
DITHER_DECIDE = (
    "What's pulling you each way? Even a rough version will do, and I'll lay both out with you.",
    "Which way are you leaning when nobody's watching? Start there, then tell me the bit that "
    "worries you.",
    "Say both versions out loud, the one where you do it and the one where you don't, and I'll "
    "help you find the one you'd regret less.",
    "What would have to be true for the answer to be yes? That is usually where the snag is.",
    "What's the thing you would lose if you said yes? Name it and we can look at it properly.",
)

# The first three lines hold up two sides; the last two ask about a yes, and only a line that
# puts the decision as "whether to" or "if i should" has offered one. "i cant decide between two
# jobs" and "what to do about money" are not yes/no questions, and "What would have to be true
# for the answer to be yes?" asks about a yes nobody said (apt-lime's nit on #1467).
DITHER_TWO_WAY_LINES = DITHER_DECIDE[:3]

# A stretch of free time is not a doubt with two sides. "no idea what to do with my afternoon" is
# somebody with an afternoon going spare, and the pool below asks about the afternoon: what it
# wants is a shape, not "which bit of it is heaviest". Said with a day or a weekend in it the line
# already reaches the pool that gives the day a shape, so this is the one form that was left.
A_FREE_TIME_ASK = (
    "How long have you got, and are you after out or in?",
    "What are you in the mood for: out of the house, a screen, or something with your hands?",
    "What would make it a good afternoon - out somewhere, or something at home?",
)

DITHER_OPEN_LINES = (
    "What's the part of it that won't move? Start there and the rest tends to come loose.",
    "Say what you'd want if nothing was in the way, and we can work back to the first step.",
    "Which bit of it is heaviest? Take that one first rather than the whole thing at once.",
)

# "i dont know what to do about my mum" is the same stuck line with the person named, and the
# open pool above asks about "it" - a thing nobody said. What a friend does is ask about them,
# which the line has already made possible. Every line asks one question and none of them
# guesses what is wrong with the person, because nothing in the line says.
# "i dont know what to do" after "the baby wont stop crying", "she forgot my name yesterday",
# "my mum has dementia". The open pool above asks about "the part of it that won't move", which
# is a thing to say to somebody weighing a choice and a strange thing to say to a person in the
# middle of a bad week. These ask about the trouble that has just been named, and every one of
# them asks rather than decides: nothing here knows what is wrong or what would help.
STUCK_AFTER_TROUBLE = (
    "What have you tried so far? What has not been tried yet is usually where the next step is.",
    "Which part of it is hardest right now? Take that part on its own and leave the rest for now.",
    "Is anyone helping you with it, or are you carrying this on your own?",
    "What would make today a bit easier? Start with the smallest part of that.",
)

# The other end of the same line: not "I have no way in" but "I have run out". "i dont know what
# else to do", "theres nothing i can do", "i dont know how to fix it", "i cant do this", "i give
# up". They name nothing, so they reached the echo ("Thanks for telling me - I'm here if you want
# to dig into any of that") or the nod. None of these asks what the person has tried, because
# they have just said that nothing has worked, and none of them names a cause the line did not
# name. One question each, and the last one is the one a friend asks a person who is on their
# own with it.
RUN_OUT_LINES = (
    "What is the thing itself? Say it in your own words and I will tell you what I can do with "
    "it and what I cannot.",
    "How long has this been going on? Weeks of it and one bad day are different things to plan "
    "for, and the answer changes with it.",
    "What would make tomorrow even slightly easier? Not the whole of it - just the next day.",
    "Does anyone close to you know how bad it is at the moment? Tell one of them too, not only "
    "me.",
)

DITHER_ABOUT_A_PERSON = (
    "What is going on with {who} at the moment? Start with the bit that worries you most.",
    "What would you most want to be different for {who}? We can work back from that to the step "
    "you can take.",
    "What has {who} said or done that has you stuck? That is usually where the answer is.",
    "What is the hardest part of it with {who} right now? Take that piece on its own.",
)

HOW_TO_DECIDE_LINES = (
    "Two questions settle most of these: what each one costs you, and which you would regret not "
    "taking. Tell me the two and we will run them.",
    "Write down what you would gain and what you would give up for each, then ask which loss you "
    "could live with. Give me both sides and I will lay them out with you.",
    "Ask what has to be true for each to work out, and which of those you can check before you "
    "commit. What are the two options?",
    "Rule out the one you could not undo if it went wrong, then choose between what is left on "
    "what you want to be doing in a year. What are you choosing between?",
)

MISSED_STEP_LINES = (
    "A missed one is a pause, not a restart: pick up at the step you were on, and if it turned "
    "into a long gap, go back a step so the first one back is easy. What are you partway through?",
    "Missing it does not undo the work. What matters is the next one, at whatever level still "
    "feels easy, not doubling up to make up for the gap. What is the plan you are on?",
    "Most plans forgive one or two misses - it is the long gap that costs you - so the next one "
    "is what counts, carried on from where you stopped rather than started again. What is it you "
    "are partway through?",
    "The usual advice is to carry on from where you stopped, or one step back after a long gap, "
    "and not to squeeze in the ones you missed. Tell me what you are working through and I will "
    "say where that leaves you.",
)

HOW_TO_DECIDE_FILLER = frozenset((
    "now", "then", "here", "please", "for", "me", "myself", "properly", "better", "right",
    "next", "first", "about", "on", "at", "it", "this", "that", "one", "thing", "things", "so",
))

# A poem or a story is not wording the bot can promise: "I can draft that" would be a lie.
_CREATIVE = frozenset(("poem", "poems", "poetry", "haiku", "story", "stories", "song", "songs",
                       "rhyme", "rhymes", "joke", "jokes", "speech", "speeches", "limerick"))

# A decision about health is settled by someone qualified, not by what the user would lose.
HEALTH_WORDS = frozenset(("doctor", "doctors", "gp", "gps", "nurse", "hospital", "pharmacist",
                          "111", "999", "a&e", "casualty", "clinic", "surgery", "vitamin",
                          "vitamins", "medicine", "medication", "pill", "pills", "tablet",
                          "tablets", "prescription", "dose", "dosage", "syringed", "infection",
                          "symptom", "symptoms", "pain", "painful", "swollen", "unwell",
                          "ibuprofen", "paracetamol", "aspirin", "painkiller", "painkillers",
                          "antibiotic", "antibiotics", "antihistamine", "antihistamines",
                          "inhaler", "insulin", "steroid", "steroids", "ointment", "allergic",
                          "allergy", "reaction", "vaccine", "vaccines", "vaccination", "jab",
                          "jabs", "flu"))

# A sore is a health word even when nobody says "doctor": "should i squeeze a boil", "should i pop
# this spot", "should i drain the abscess" are questions about a body, and the decision pool
# answers them with "that's your call, not mine", which is the one thing they are not. The words
# here name a thing on the skin a person can squeeze, pop, cover or leave alone. Nothing that is
# also an everyday verb is in it: "should i cut my hair", "should i burn the letters", "should i
# bite the bullet" and "should i take a bite" are decisions, and cut, burn and bite would catch
# them. A bare "should i cover it" stays generic - the thing covered is in the turn before.
SORE_SERIOUS = frozenset((
    "boil", "boils", "abscess", "abscesses", "carbuncle", "carbuncles", "cyst", "cysts",
    "pus", "lump", "lumps", "swelling", "wound", "wounds", "ulcer", "ulcers", "stye", "styes",
    "whitlow", "ingrown", "mole", "moles", "wart", "warts", "verruca", "verrucas",
    "rash", "rashes", "hives", "eczema", "psoriasis", "infection", "infected",
))

# The everyday ones: a spot, a scab, a blister, a splinter. Squeezing or picking at these is
# ordinary, and answering "ring 111" would treat a teenager's chin as an emergency - so they go
# to their own line, which says the one thing that matters and names a pharmacist only for the
# turn where it goes hot and spreading.
SORE_ORDINARY = frozenset((
    "spot", "spots", "pimple", "pimples", "blackhead", "blackheads", "scab", "scabs",
    "blister", "blisters", "splinter", "splinters", "graze", "grazes", "sore", "sores",
))

SORE_WORDS = SORE_SERIOUS | SORE_ORDINARY

# Two of these words are places as well as bodies, and the place reading is the ordinary one in a
# plan: "should i pick a spot for the tent", "should i pick a spot in the garden" and "should i
# pick a good spot" were answered "Don't squeeze or pick it. A warm flannel for ten minutes" -
# good advice about a chin, nonsense about a campsite. "a lump" is the same ("a lump of coal").
# So one of these words only makes a sore when the line also says where on a person it is: "my
# spot", "a spot on my chin", "the lump on my back".
SORE_AMBIGUOUS = frozenset((
    "spot", "spots", "sore", "sores", "lump", "lumps",
))

# "Should I put a plaster on it" is a wound question about a turn that is not in the words, and
# the plaster is the giveaway. The thing dressed has to be "it", "this" or "that": "should i put a
# plaster on the wall" is a DIY question and a wall is not a wound.
# A plaster is the everyday covering for a cut, so "on my knee" or "on my chin" is enough. A
# bandage, a compress, a dressing or an antiseptic is what goes on a sprain or on a head, and
# "should i put a bandage on my ankle" answered with a plaster for a graze is worse than the
# shrug it got before: those want the wound named, "on my cut", or the bare "on it".
_WOUND = (r"(?:cut|graze|scab|blister|scratch|sore|gash|scrape|burn|splinter|wound|"
          r"spot|insect bite|bite|sting)")

# A decision about money is the one kind the bot must not reduce to "what would you lose":
# a loan, a card, a deposit. Matched as words, so "worth buying an air fryer" stays generic.
MONEY_WORDS = frozenset((
    "money", "loan", "loans", "mortgage", "mortgages", "credit", "debt", "debts",
    "overdraft", "overdrafts", "savings", "saving", "invest", "investing", "investment", "pension",
    "pensions", "rent", "rents", "renting", "rented", "bills", "bill", "salary", "salaries",
    "wage", "wages", "income", "tax", "taxes", "taxed", "taxing", "afford", "affords", "lend",
    "lends", "lending", "lent", "borrow", "borrows", "borrowing", "borrowed", "owe", "owes",
    "owed", "repay", "repaying", "repayment", "refund", "arrears", "redundancy", "prepayment",
    "premium", "premiums", "tariff", "tariffs", "supplier", "budget", "inheritance", "insurance",
    "deposit", "pensioner", "pensioners", "account", "accounts", "isa"))

_MONEY_NOUN = frozenset(("money", "loan", "loans", "debt", "debts", "credit", "card", "cards",
                         "mortgage", "mortgages", "rent", "bills", "bill", "pension", "pensions",
                         "savings", "overdraft", "interest", "arrears", "repayment", "insurance",
                         "deposit", "premium", "premiums", "tariff", "tariffs", "salary", "wage",
                         "wages", "tax", "invest", "investment", "afford", "borrow", "prepayment"))

# A body part makes a "should i worry" a question about the body, not about their reaction:
# "should i worry about my knee clicking" wants UNKNOWN_HEALTH, not the reassurance pool.
BODY_PARTS = frozenset((
    "back", "knee", "knees", "shoulder", "shoulders", "ankle", "ankles", "wrist", "wrists",
    "neck", "hip", "hips", "leg", "legs", "arm", "arms", "foot", "feet", "toe", "toes",
    "tooth", "teeth", "gum", "gums", "ear", "ears", "eye", "eyes", "chest", "stomach",
    "belly", "throat", "head", "skin", "hand", "hands", "finger", "fingers", "jaw",
    "sinus", "sinuses",
))

CHECK_PHRASES = ("get it checked", "get checked", "get it looked at", "get it seen to",
                 "see someone about it", "get it seen")

WORD_ANYWHERE = ("can you word", "can you write", "can you draft", "help me write", "help me word",
                 "help me draft", "a msg to", "a message to", "a note to", "a text to",
                 "an email to")

# A symptom, a body part or a health service in the line makes it a question about the body, so
# the reassurance pool must not take it: "should i worry about my chest hurting when i run".
SYMPTOM_WORDS = frozenset((
    "pain", "pains", "painful", "ache", "aches", "aching", "hurt", "hurts", "hurting", "sore",
    "dizzy", "dizziness", "bleeding", "bled", "bleed", "sick", "nausea", "nauseous", "vomit",
    "vomiting", "fever", "temperature", "lump", "lumps", "rash", "swelling", "swollen", "tired",
    "exhausted", "forgetting", "forgetful", "memory", "confused", "bruise", "bruised",
    "headache", "headaches", "migraine", "migraines", "cough", "coughing", "breath",
    "breathing", "breathe", "wheezing", "infection", "pregnant", "cramps", "palpitations",
))

UNKNOWN_WORRY = (
    "If it's on your mind enough to ask, it's worth taking seriously — you don't have to prove "
    "anything first. What's the part that's under your skin?",
    "Not unreasonable at all. How you feel about it is real, and it's worth saying out loud to "
    "whoever needs to hear it.",
    "You're not being silly. Feelings don't need a good reason to count — say the bit that's "
    "bothering you, even badly worded.",
)

# "is that weird" as the first thing in a chat names no feeling and no subject, so there is
# nothing for the reassurance pool to be reassuring about and nothing to look up either: the search
# hedge ("a search should sort you out quickly") answered a person asking to be told what normal
# looks like. The honest reply asks for the thing, the way a friend would.
UNKNOWN_WEIRD_BARE = (
    "Weird in what way? Give me the thing you are turning over and I will tell you straight.",
    "I can do normal or not normal, but I need the thing itself: what are you wondering about?",
    "That question needs its subject. What is it you are doing and wondering whether it is odd?",
)

# "is that too late", "am i too old": the doubt a person says out loud about their own starting
# something, on the turn after the bot has already helped them start it. It reads as a question of
# fact - the bot has no age, no window and no rule about who may learn what - so it got the search
# hedge one line after answering "im learning to swim at 40" with the adult lessons that exist for
# exactly that. What is wanted is not a fact but a straight answer to the doubt, and then the
# person can get on with the thing they were already asking about. Only the bare ask, and only
# after they have said what they are starting (see `_a_thing_they_started`): "is it too late to
# plant potatoes" names its own subject and stays a knowledge question.
UNKNOWN_TOO_LATE = (
    "Not too late at all. Being a beginner again is awkward rather than impossible, and the first "
    "few weeks are the awkward bit for everybody in the room, not just you.",
    "It isn't. What decides these things is a regular slot in the week rather than the year you "
    "start in - so put one in the diary and age stops being the question.",
    "No. Plenty of people take this sort of thing up later than they meant to, and they are "
    "usually the ones who keep turning up, because they are not in a hurry to look good.",
    "Not at all - if anything, waiting makes you better at it: you have already stopped caring "
    "what the room thinks, which is the hard part for most beginners.",
)

# "is that realistic", "is that too ambitious", "do you think thats doable": the same doubt as
# "is that too late" with a different word in it, and it got the same search hedge - a reading list
# handed to somebody who has just told the bot their plan. The bot cannot see the two things that
# decide it, which are where the person is starting from and how much time they have, so the line
# asks for those rather than guessing. Nothing here names a timescale: an invented deadline is how
# a helpful answer turns into a wrong one.
UNKNOWN_REALISTIC = (
    "That depends on two things I can't see: what you can already do, and how much time you have "
    "to put in. Tell me both and I'll say whether it's tight or comfortable.",
    "I'd be guessing, and a wrong yes costs you weeks. What's your starting point, and when does "
    "it have to be done?",
    "Whether it's realistic hangs on the starting point and the deadline rather than the plan "
    "itself. Give me those two and I'll tell you straight.",
    "You know better than me on the part that decides it: how much of this can you already do, "
    "and how often can you practise between now and then?",
    "Nothing unrealistic about wanting it - unrealistic is a pace rather than a wish. What can "
    "you put in each week, and how long have you got?",
    "If it has a number on it, the sum is the honest answer: give me the target and the time you "
    "have, and I'll work out the pace it needs.",
)

# The same ask in a thread where something heavy has just been said. "What's your starting point"
# is the wrong question of somebody whose mother is ill, and the people who know that situation
# are the ones in the room with her.
UNKNOWN_REALISTIC_CARE = (
    "I can't judge that from here, and I'd rather not guess at it. What are the people who know "
    "the situation saying?",
    "That one is theirs to answer rather than mine. Tell me the plan and I'll help you think "
    "round it.",
)

# What they need is the doubt answered and the plan kept small, so the lines take the fact and
# turn it into the first week rather than saying it back. The two things people offer as a reason
# not to start are their age and being unfit, and the line has to answer the one they said: "at
# your age" under a line that only said "im not very fit" is a reply to a different person.
NOT_TOO_OLD = (
    "Being a beginner at your age is not what stops people; stopping in week three is. Make the "
    "sessions small enough that you never dread one.",
    "Plenty of people start this later than you and keep it up, usually because they are not in "
    "a hurry to look good. Put a regular slot in the diary and the age stops being the question.",
    "It is not too late: what decides these things is a regular slot in the week rather than the "
    "year you start in, so give it the slot and give it six weeks.",
    "No - and the first month is the awkward bit for everybody in the room, not just the people "
    "who turn up at eighteen.",
)

NOT_FIT_ENOUGH = (
    "That is the normal starting point, not an obstacle - the first two or three weeks are meant "
    "to feel hard, and unfit is exactly who these plans are written for.",
    "Then start smaller than feels right: three short sessions a week beat one long one, and you "
    "will feel the difference inside a month.",
    "Go by the calendar rather than by how you feel on the day, and give it six weeks before you "
    "judge it - unfit at the start is what everybody is.",
    "It changes faster than you would guess: two short sessions a week, kept going, and the "
    "third week is when it starts to feel easier.",
)

# A worry ask that names nothing, made in a thread about somebody else, is a concern about them:
# "my son is starting school in september" / "he cant do up his buttons yet" / "should i be
# worried" got "Feelings don't need a good reason to count" - a reassurance about the speaker's
# feelings, when the line is asking whether the child's buttons are a problem. Nobody here can
# examine the child, so the honest line names who can, and says that asking is not fussing.
UNKNOWN_ABOUT_SOMEONE = (
    "That is one to ask about rather than guess at, and asking early is not fussing. Whoever knows "
    "them best - a GP, a health visitor, the staff at the school - will tell you whether it needs "
    "a look.",
    "Worth an appointment rather than a guess from me: a GP or a health visitor will say whether "
    "it is the ordinary version for that age, and one appointment settles it.",
    "You are not being fussy for wondering. Someone who sees this every week - a GP, a health "
    "visitor - will tell you whether it is worth looking at, and asking is not fussing.",
)

# A pet is somebody else too, but its doctor is a vet: "my dog keeps scratching" and a worry ask
# after it would be sent to a GP by the pool above, which is the wrong waiting room.
NOT_PEOPLE_WORDS = frozenset(("dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets",
                              "pup", "vet", "rabbit", "hamster", "budgie", "parrot"))

# ...and the animal needs its own pool rather than the reassurance one. A pet thread was left out
# of the somebody-else reading, so the bare worry ask fell through to UNKNOWN_WORRY and answered
# "my dog keeps scratching" / "should i be worried" with "You're not being silly. Feelings don't
# need a good reason to count" - reassurance about the speaker's feelings when the question is
# about the dog. Nobody here can look at an animal, so the honest line names who can, and says
# that asking is not fussing.
UNKNOWN_ABOUT_A_PET = (
    "Worth asking the vet rather than guessing, and a call to the desk usually costs nothing. "
    "Itching that goes on is one of the things they would rather hear about early.",
    "A vet is the one to ask, and asking early is not fussing over an animal. How long has it "
    "been like this?",
    "You are not being fussy for wondering. The vet will tell you whether it is the ordinary "
    "thing for that animal, and one visit settles it.",
)

# A person in the thread is not a thing to weigh the cost of: "my husband left me" then "is it
# worth fixing" got the repair rule, and REPAIR_PERSON only ever read the follow-up line, which
# names no thing at all. A thread about someone is a thread about someone.
_THREAD_PEOPLE = frozenset("""
marriage relationship friendship ex husband wife partner boyfriend girlfriend son daughter kid
kids child children mum mom mother dad father brother sister nan gran grandma grandad friend
friends mate mates parent parents family
""".split())

# The words that are not a thing of its own after "is it worth fixing": a pronoun points back at
# the thread, and a body word is the body the fence is about. The second half of the question is
# scaffolding rather than a subject - "is it worth fixing or shall i leave" names nothing, and
# reading "shall" as the thing made a marriage look like a broken appliance (the cost rule for a
# person, because the line looked like it named its own object) - so the modals, the alternatives
# and the words that join them are here too. A person is not a thing either: "is it worth fixing
# myself" names no thing at all, and reading the speaker as the thing fixed told the repair rule
# to answer "my back keeps going" / "is it worth fixing myself" with the paragraph about a part
# and a quote, where the thread was a body and its line is the health one.
_NOT_AN_OWN_THING = frozenset("""
and or but so if then to for with of in on at from up out
one ones them they the a an my our your his her their its
me us yourself myself himself herself itself ourselves themselves
thing things part parts bit bits piece
worth fix fixing repair repairing mend mending replace replacing get getting new old
i you we us it that this these those me him she he there here
shall should would could will can may might must do does did done
just else instead rather maybe otherwise again still yet even only
live living leave leaving keep keeping stay staying bin binning chuck scrapping scrap
buy buying sell selling trade ditch dump rid ridof throw throwing away
""".split())

EMPTY = (
    "I'm here — what's on your mind?",
    "Go ahead, I'm listening.",
    "Take your time. What would you like to talk about?",
)

# When the bot cannot answer a question, saying who can is the most useful thing left: it is
# concrete, it differs by topic, and it does not pretend to know. Only where a person whose
# job it is can settle it, and only on a word that names that world beyond doubt - the topic
# guess alone is too loose ("temperature" is a health word, in an oven question). Tastes,
# arithmetic and plain facts have no expert, so they keep the honest shrug.
# A pet's symptom is the vet's, not the pharmacist's, whatever the word for it.
ANIMALS = frozenset(("dog", "cat", "puppy", "kitten", "pet", "rabbit", "hamster", "horse",
                     "bird", "parrot", "guinea", "gerbil", "ferret", "fish"))

# A bird on a roof is not a sick bird. "how do i clean bird poo off my patio" was answered with
# the vet's phone number, because "bird" is a pet word and "poo" is a symptom word. The birds
# that make a mess of a thing are wild ones, and the place the mess lands is the tell.
WILD_BIRDS = frozenset(("bird", "birds", "pigeon", "pigeons", "seagull", "seagulls", "gull",
                        "gulls", "goose", "geese", "duck", "ducks", "swan", "swans", "crow",
                        "crows", "starling", "starlings", "sparrow", "sparrows"))

MESS_PLACES = frozenset(("patio", "paving", "drive", "driveway", "decking", "deck", "path",
                         "paths", "pavement", "wall", "walls", "fence", "roof", "washing",
                         "laundry", "window", "windows", "windowsill", "sill", "car", "cars",
                         "windscreen", "barbecue", "bbq", "bench", "table", "clothes",
                         "greenhouse", "conservatory", "parapet", "gutter", "gutters"))

# What is wrong with the animal, not who to ring about it: "vet" and "vaccination" were here
# and made the vet row skip itself, so "my kitten has a bad eye" fell through to the nod.
SICKNESS = frozenset(("symptom", "cough", "rash", "vomit", "sick", "limp", "itch", "wound",
                      "swelling", "scratch", "eating", "poo", "blood", "eye", "ear", "mange",
                      "worm", "flea", "diarrhoea"))

TRADES_WHO = "A plumber or electrician will spot it in minutes"

DEVICE_WHO = "The maker's support page will have the exact steps"

SCHOOL_WHO = "The school office or a head of year is the one who can act on it"

# Named once, so a pet's line and a person's line can never swap sentences.
VET_WHO = "Your vet is the one to ask, and a call to the desk is usually free"

HEALTH_WHO = "A pharmacist or your GP can answer that today"

BABY_WHO = "Your health visitor or the 111 line will talk it through with you today"

TENANT_WHO = "Citizens Advice answers tenant questions free, and a call beats searching"

# Named, because one row has to stand aside for a line about the other life of a word: a mouse is
# a pest and a computer part, and "my mouse isnt working" is not a job for a pest controller.
PEST_WHO = "A pest controller is the one to call, and most give a price over the phone"

DENTIST_WHO = "A dentist is the one to see, and most will fit an urgent case in"

# "filling" is a food word before it is a dental one: a cake filling, a pie filling, a sandwich
# filling. On its own it names no mouth, so it only points at a dentist next to one of these -
# "my filling came out" and "i need a filling in my tooth" still reach the dentist, while "what
# filling should i use" after a chicken does not.
FILLING_WORDS = frozenset(("filling", "fillings"))

# The people a baby's row can be about. "teething" is the only word in that row that is not a
# person or a feed, and on its own it can be about a car's first faults, so the row asks for one
# of these before it claims the line.
CHILD_AT_HOME = frozenset(("newborn", "baby", "babies", "babys", "infant", "child", "children",
                           "kid", "kids", "toddler", "toddlers", "son", "daughter", "girl",
                           "boy", "grandchild", "he", "she", "breastfeeding",
                           "nappy", "nappies", "weaning", "midwife", "health visitor"))
# `feeding` is not one of them, and it was: a peace lily is fed, so is a sourdough starter, so is a
# car's engine, and the word on its own was enough to send the line to the health visitor - "my
# peace lily isnt flowering" / "what about feeding it" came back with "Your health visitor or the
# 111 line will talk it through with you today". A feed belongs to whoever it is said of, so the
# word stays in the row's evidence and the person in the line is what claims it: "my baby isnt
# feeding well" still reaches the same reply.

# A baby's food is not a baby. "can i eat baby rice" and "is baby food healthy for adults" are a
# grown-up's lunch, and handing them to a health visitor is the one reply STYLE.md rules out - the
# baby in the line is part of a food's name. The word for a grown-up is the first way to say so.
GROWN_UP_WORDS = frozenset(("adult", "adults", "grown up", "grown ups", "grownup",
                            "grownups", "for adults"))

# The food names that carry a baby inside them. A line naming one of these and no other child word
# is about eating, so it is the second way.
BABY_FOOD_NAMES = frozenset(("baby rice", "baby food", "baby foods", "baby porridge",
                             "baby cereal", "baby yoghurt", "baby juice", "baby puree",
                             "baby purees", "baby biscuit", "baby biscuits", "baby pasta",
                             "baby pouch", "baby pouches", "baby jar", "baby jars"))

SELF_EATING_WORDS = frozenset(("eat", "eating", "eaten", "ate", "taste", "tasting",
                               "lunch", "dinner", "breakfast", "snack"))

MOUTH_WORDS = frozenset(("dentist", "dental", "tooth", "teeth", "gum", "gums", "mouth", "molar",
                         "molars", "cavity", "cavities", "toothache", "brace", "braces",
                         "enamel", "wisdom"))

# The food a filling goes inside. Naming one is what makes the line a kitchen question when
# nothing in the conversation has set a food topic yet ("what filling should i use for a pie").
FILLING_FOODS = frozenset((
    "cake", "cakes", "cupcake", "cupcakes", "muffin", "muffins", "pie", "pies", "pastry",
    "tart", "tarts", "quiche", "sandwich", "sandwiches", "bread", "bun", "buns", "doughnut",
    "donut", "dumpling", "dumplings", "ravioli", "pasta", "lasagne", "lasagna", "choux",
    "eclair", "eclairs", "icing", "frosting", "buttercream", "ganache", "chocolate", "lemon",
    "apple", "jam", "cream", "cheese", "chicken", "beef", "pork", "mushroom", "spinach",
    "potato", "rice", "egg", "eggs", "tuna", "salmon", "prawn", "crab", "sausage",
    "vegetarian", "vegan", "recipe", "bake", "baking", "roast", "cook", "cooking"))

# The people who settle a job question are not asked by the word "boss" on its own. A boss is also
# the thing at the end of a level, so "how do i beat the boss in dark souls" was sent to a union
# rep; and "my boss is a nightmare" is a complaint about a person rather than a dispute, and got
# "A union rep will know. Tell me what they say" where the warm line belongs. So the row wants the
# job to be about something - the union, or the thing a dispute is over - and the word on its own
# is not the evidence.
WORK_WHO = "A union rep or an employment advice service will know"

WORK_ABOUT = frozenset("""
    union unions rep holiday holidays leave pay paid wages salary payrise unpaid underpaid
    sacked fired firing dismissed dismissal dismiss redundancy redundant contract contracts
    hours rota shift shifts overtime grievance bullying bullied harassment tribunal notice
    resign resigning resignation maternity paternity probation appraisal disciplinary suspension
    suspended workplace payslip unfairly exploited breaks strike strikes balloting acas
    """.split())

# A joint is a body part before it is a symptom, so the word alone is not evidence that anything
# is wrong with it: "my knee replacement is in march, what should i pack" names a knee and asks
# about a bag, and in a thread about lifting, "should i bend my knees or my back" names two and
# asks which way to bend. The health hand-off is for a trouble, so a line whose only health word
# is a joint also has to ask about that joint before the pharmacist is named. A symptom word is
# evidence on its own, as it always was.
JOINT_WORDS = frozenset(("knee", "knees", "hip", "hips", "ankle", "ankles", "shoulder",
                         "shoulders", "elbow", "elbows", "wrist", "wrists", "heel", "heels",
                         "thigh", "thighs", "shin", "shins", "cartilage", "ligament",
                         "ligaments", "tendon", "tendons", "sciatica", "trapped nerve"))

# A joint is the trouble only when the line asks about the joint: will it settle, how long, is it
# worth having looked at. Without one of these the joint is context and the pharmacist is not
# the person who settles it.
_ASKS_ABOUT_THE_JOINT = re.compile(
    r"\b(?:better|worse|settle|settles|settled|heal|heals|healing|recover|recovery|last|lasts|"
    r"long|operation|surgery|worth|serious|normal|infected|infection|go away|goes away|"
    r"looked at|checked|see (?:someone|somebody|a doctor|the doctor|a gp|the gp|a specialist)|"
    r"painkiller|painkillers|ibuprofen|paracetamol|ice|rest|swollen|swelling|swell|stiff|"
    r"stiffness|click|clicks|grind|grinds|hurt|hurts|hurting|sore|ache|aches|aching|pain|"
    r"painful|weak|weakness|numb|numbness|give way|gives way|locking|locked|bend|bending|"
    r"straighten|straightening|physio|physiotherapy)\b")

# A choice between two acts is the person's own call: a pharmacist cannot say whether to bend at
# the knees or the back, and the line is not asking about a symptom.
_CHOOSING_BETWEEN_TWO = re.compile(
    r"\b(?:should|shall|do|can|could|would|is it better to|which is better|which should)\b"
    r"[^?.;]*\bor\b")

WHO_TO_ASK = (
    (frozenset(("vet", "vaccination", "kitten", "puppy")), VET_WHO),
    (frozenset(("dentist", "dental", "gum", "gums", "tooth", "teeth", "brace")),
     DENTIST_WHO),
    (frozenset(("midwife", "health visitor", "newborn", "babys", "baby", "breastfeeding",
                "feeding", "teething", "nappy")),
     BABY_WHO),

    (frozenset(("wasp", "nest", "wasp nest", "mice", "mouse", "rat", "rats", "pest",
                "infestation", "bedbugs")),
     PEST_WHO),
    (frozenset(("doctor", "gp", "nhs", "pharmacist", "prescription", "symptom", "throat",
                "cough", "rash", "earache", "toothache", "sprain", "stomach", "vomit", "itch",
                "limp", "sneez", "headache", "migraine", "period", "contraception", "gum",
                # A joint is not a symptom by itself, but the questions people bring about one
                # are the same questions as the rash's: will it settle, how long, is it worth
                # having looked at. Bare `joint`/`joints` are left out on purpose - a pipe has
                # one, and "the joint of the pipe hurts" is the plumber's line.
                "knee", "knees", "hip", "hips", "ankle", "ankles", "shoulder", "shoulders",
                "elbow", "elbows", "wrist", "wrists", "heel", "heels", "thigh", "thighs",
                "shin", "shins", "cartilage", "ligament", "ligaments", "tendon", "tendons",
                "sciatica", "trapped nerve")),
     HEALTH_WHO),
    # Housing law is not money advice: an eviction notice is a tenant's rights question, so
    # the tenant row comes first and no money row may claim "evict".
    (frozenset(("landlord", "landlords", "tenancy", "tenant", "letting", "rent", "housing",
                "deposit back", "tenancy deposit", "evict", "possession", "arrears",
                "section 21", "notice to quit")),
     TENANT_WHO),
    # The bare word "parking" is not a parking fine: "were parking available at the hotel" was
    # sent to Citizens Advice by it, and the person was asking about a hotel. What that service
    # helps with is the penalty, so the row names the penalty and the permit it comes from.
    (frozenset(("tax", "benefits", "redundancy", "bill", "bills", "council", "council tax",
                "parking ticket", "parking tickets", "parking fine", "parking fines",
                "parking charge", "parking charges", "parking notice", "parking penalty",
                "parking permit", "penalty charge", "penalty notice", "pcn")),
     "Citizens Advice covers this free, and a call beats searching"),
    (frozenset(("mortgage", "loan", "debt", "savings", "pension", "pensioner", "salary", "overdraft",
                "credit")),
     "Free money advice covers this — MoneyHelper in the UK does it without charge"),
    (frozenset(("boss", "my manager", "union", "colleague", "employer")),
     WORK_WHO),
    # The thing that leaks, never the leak: a boot, a pen, an airbed and a bottle all leak too,
    # and a plumber has never once been the answer to any of them. "leaking pipe" and "water
    # leak" stay because they name the trade's own world; a roof is a roofer's, so it is left to
    # the honest shrug rather than sent to a plumber.
    (frozenset(("boiler", "radiator", "plumber", "electrician", "damp", "fuse", "fuse box",
                "wiring", "tap", "pipe", "water leak", "leaking pipe", "leak under",
                "cistern", "stopcock")), TRADES_WHO),
    # The maker's page is for the device's own fault. A network fault is not something the
    # maker of the phone can answer: "my phone wont connect to the wifi", "my wifi keeps
    # cutting out" want a question about when it happens, not a support page. NETWORK_WORDS
    # keeps a named device from claiming a wifi line too.
    (frozenset(("printer", "router", "charger", "battery", "tablet")),
     "The maker's support page will have the exact steps"),
)

# Some lines have a right action before any advice: gas gets you out of the house, and a
# blackout is checked rather than watched.
# The danger, never the fuel on its own: "my gas bill", "the gas meter" and "a gas boiler"
# are not reasons to leave the house.
GAS_WORDS = frozenset(("carbon monoxide", "flue", "smell of gas", "smells of gas",
                       "smell gas", "smelling gas", "gas leak", "gas smell", "co alarm",
                       "gas escape", "gas emergency"))

# "Fumes" on its own could be paint or a bus; with a fuel-burning thing it is carbon monoxide.
FUME_WORDS = frozenset(("fumes", "fume"))

# A word matches a longer form of itself here ("flue", "flues"), so "fluent" and "fluency"
# are a flue as far as the rule above is concerned, and "how do i become fluent in french"
# empties the house. How well someone speaks a language is not a gas leak, so the words that
# only look like a flue are named and the gas answer stands aside for them.
LANGUAGE_FLUENCY = frozenset(("fluent", "fluency", "fluently", "fluencies"))

FUEL_WORDS = frozenset(("boiler", "cooker", "hob", "fire", "fireplace", "firewood", "heater",
                        "gas", "oven", "chimney", "flue", "woodburner", "stove"))

GAS_ANSWER = ("Switch the boiler off, open the windows and get out, then ring the gas "
              "emergency line on 0800 111 999 — fumes can be carbon monoxide")

# A person goes down, not a souffle and not a website, so the event needs someone before it.
# An emergency has one right answer whatever the line is doing grammatically: a baby who is
# floppy and will not wake is not something to talk through with anyone but 999.
# Phrases a person gets, never a device: "my phone screen is unresponsive" and "unconscious
# bias" are not emergencies, so the phrase has to be a person's, and a gadget in the line
# rules it out.
EMERGENCY_WORDS = frozenset(("wont wake", "not waking", "is unresponsive", "was unresponsive",
                             "is unconscious", "was unconscious", "found unconscious",
                             "knocked unconscious", "unconscious and", "not breathing",
                             "isnt breathing", "stopped breathing", "turning blue", "no pulse",
                             "choking on", "is choking", "overdosed", "heavy bleeding"))

# A state word about a body needs a body to belong to. "my car engine is choking", "my bike chain
# is choking" and "the drain is choking" all reach the ambulance line on main: the person is told
# to ring 999 for their car. The noun in front of the state word is what decides, and it has to
# be a thing we can name - an unknown subject keeps the 999, because a missed ambulance costs
# more than a wasted call.
THING_SUBJECT = frozenset("""
    sink sinks drain drains pipe pipes toilet toilets loo loos garden gardens lawn lawns
    flowerbed flowerbeds engine engines filter filters radiator radiators chimney chimneys
    gutter gutters weed weeds moss bog bogs traffic paperwork inbox diary diarys sourdough
    bath baths tub bathtub basin basins handbasin washbasin shower showers hose pipework
    downpipe gulley drainpipe pump cistern plughole washing washer machine
""".split())

# A person anywhere in the line keeps the ambulance, however the thing is phrased: "my son is
# choking" is the emergency even though `son` is not in the thing list, and "my sons car engine is
# choking" is left to the careful path rather than guessed at.
BODY_SUBJECT = frozenset("""
    i im we he she they me us him her them anyone someone somebody nobody
    son sons daughter daughters baby babies child children kid kids boy boys girl girls toddler
    toddlers newborn mum moms mom dad dads daddy mummy nan nans gran grans grandma grandad
    husband husbands wife wives partner partners friend friends brother brothers sister
    sisters neighbour neighbours man men woman women person people patient patients
    cat cats dog dogs puppy puppies kitten kittens rabbit rabbits hamster hamsters bird birds
    fish pet pets
""".split())

# A thing that is *choked* is blocked, not breathing: "the kitchen sink is choked" and "my
# bath is choked" are the same fault as a drain that is choked with hair.
THING_STATES = ("is choking", "choking on", "is choked", "are choked", "choked with",
                "choked up with", "keeps choking", "keeps getting choked")

_COPULA = frozenset(("is", "are", "was", "were", "s", "keeps", "kept", "still", "just"))

GADGET_WORDS = frozenset(("phone", "screen", "laptop", "tablet", "website", "computer", "app",
                          "keyboard", "touchscreen", "mouse", "printer", "bias", "monitor"))

# Floppy on its own is not an emergency ("floppy when sleepy") - floppy and not waking is.
FLOPPY_WAKE = frozenset(("floppy", "limp"))

EMERGENCY_ANSWER = ("Ring 999 now — that is an emergency, not something to watch at home. Stay "
                    "with them, keep them warm and do what the call handler tells you")

# Petrol on your hands at the pump is not a gas leak, and a seizure from laughing is a joke.
TIRED = frozenset(("wake", "waking", "wakes", "wont", "not"))

PETROL_WORDS = frozenset(("petrol", "diesel", "pump", "forecourt", "filling", "fuel", "car",
                          "van", "station"))

LAUGHING_WORDS = frozenset(("laughing", "laugh", "laughed", "laughter", "funny", "joke",
                            "video", "meme", "comedy"))

# Who a faint can happen to. The list is the same family the rest of the composer names a person
# with, and it is written once here because the tail kept growing the hard way: `my son passed out`
# reached the 111 answer and `my child passed out`, `my kid passed out` and `my child fainted` got a
# comfort line, so the same event said about the same child was two different answers. "my little
# boy" and "my eldest daughter" are the same child said with an adjective, and `kids`/`children`
# are the plural of the same line.
PASSED_OUT_PERSON = (
    r"(?:mum|mom|mother|mam|dad|father|son|daughter|wife|husband|partner|boyfriend|girlfriend|"
    r"friend|flatmate|housemate|roommate|mate|baby|child|children|kid|kids|boy|girl|brother|"
    r"sister|sibling|nan|nana|gran|granny|grandma|grandad|grandpa|grandmother|grandfather|"
    r"grandchild|grandson|granddaughter|grandkid|"
    r"toddler|newborn|infant|little\s+one|step(?:mum|mom|dad|mother|father|son|daughter|brother|"
    r"sister|child)|aunt|auntie|uncle|cousin|nephew|niece|ex|landlord|landlady|neighbou?r|"
    r"colleague|carer|patient|pupil|student|teacher)"
)

FAINT_COMING_ANSWER = (
    "Sit down or lie down now, on the floor if that is the quickest way, with your feet up and your "
    "head low, and stay there a few minutes - a faint is the blood pressure dropping and being on "
    "the floor is what stops the fall. Drink some water, eat if you have not eaten, and get up "
    "slowly. If this has happened before, or you do go down, ring 111 today; chest pain, a racing "
    "heart or passing out while you are sitting is 999")

# One careful sentence, not a name and a nudge: after a blackout the useful thing is to be seen
# this week, and 111 or the surgery decides how soon. Two sentences were saying it twice.
PASSED_OUT_ANSWER = ("Ring 111 or your surgery this week rather than waiting it out — describe "
                     "it the way you just did and let them say how soon to come in")

# A child who blacks out is seen the same day, not this week: the adult sentence was the only one
# there was, and "this week" is the wrong urgency for a school-age child. The 999 signs are the
# same ones every other arm has, and they are settled above this, so only the come-round faint
# reads this.
CHILD_FAINT = frozenset(("child", "children", "kid", "kids", "boy", "girl", "son", "daughter",
                         "toddler", "grandchild", "grandson", "granddaughter", "teenager"))

CHILD_FAINT_ANSWER = (
    "Ring 111 today rather than waiting to see - a child who passes out is checked the same day, "
    "so say how long they were out and what they were doing. If they have not come round, are "
    "breathing oddly, went down during sport, or hit their head, that is 999."
)

# The same faint said without the word for it: the sight itself goes, the room goes dark, and the
# next thing they know they are on the floor. "i passed out" is covered above; these are the ways
# people type it when they never use that phrase. Each shape with whether the line has to name a
# person for it: "everything went black on the bus" is the speaker's own sight going even though
# the line never says "i", while "the room went dark" only belongs to a body when there is a body
# in the line to go dark with it.
BLACKED_OUT_SIGHT = (
    # "everything went black", "it all went dark for a moment"
    (r"\b(?:everything|it\s+all|all\s+of\s+it)\b(?:\s+\w+){0,2}\s+"
     r"(?:went|goes|go|turned|turns|has\s+gone|had\s+gone)\s+(?:black|dark|white)\b", False),
    # "my vision went black for a second", "the room went dark and i felt myself going"
    (r"\b(?:the\s+room|the\s+world|my\s+(?:vision|sight|eyesight|eyes))\b(?:\s+\w+){0,2}\s+"
     r"(?:went|goes|go|turned|turns|has\s+gone|had\s+gone)\s+(?:black|dark|white)\b", True),
    # "my vision went" with no colour in it: the sight going is the same thing said shorter, but
    # blurred vision on its own is a GP question rather than a faint, so the blur stays out.
    (r"\bmy\s+(?:vision|sight|eyesight)\s+(?:went|goes)\b(?!\s+(?:a\s+bit|blurry|blurred|fuzzy|"
     r"double|bad|worse))", False),
    # "i went blind for a second"
    (r"\b(?:went|goes|go)\s+blind\s+(?:for|in)\s+(?:a|an)\s+(?:second|moment|minute|few)\b",
     False),
    # "i came round on the floor": coming back to yourself on the floor is the faint as well.
    (r"\b(?:came|come)\s+(?:round|to)\b(?:\s+\w+){0,3}\s+on\s+(?:the|my|a)\s+"
     r"(?:\w+\s+){0,2}floor\b", False),
)

# A screen, the sky, the lights or a power cut goes dark too, and none of those is a body: a thing
# that goes black is the thing's question, not the 111 card.
DARK_THING = frozenset((
    "screen", "phone", "tv", "telly", "monitor", "laptop", "tablet", "computer", "sky",
    "cinema", "light", "lights", "power", "bulb", "bulbs", "lamp", "picture", "photo",
    "camera", "storm", "curtain", "curtains", "window", "windows",
    "mould", "grout", "road", "ice", "battery", "stage"))

# A world word only names an expert when something is actually wrong in that world: a present
# for a leaving teacher is a taste, and "is a password manager worth using" is not a fault.
SCHOOL_WORDS = frozenset(("school", "teacher", "head of year", "class", "lesson", "uniform",
                          "homework", "term", "secondary", "primary", "nursery", "exam"))

# "homework" is not trouble by itself: "do you think homework is a good idea" is an opinion
# question, not a school problem, so the row needs something wrong for the child as well.
SCHOOL_TROUBLE = frozenset(("bully", "bullied", "bullies", "wont", "refus", "exclud", "suspend",
                            "absent", "complain", "fees", "fail", "struggl", "fighting",
                            "detention", "behaviour", "skipping", "too much homework",
                            "homework help", "teacher says", "school says"))

PASSWORD_TROUBLE = frozenset(("forgot", "forgotten", "reset", "change", "locked", "wont",
                              "accept", "login", "sign in", "recover", "hacked", "cant", "cannot",
                              "stuck", "fail", "failure", "reject", "error", "work"))

# A complaint about a trader is a consumer question, and Citizens Advice is who answers those:
# "how do i complain about my builder", "my roofer did a bad job and wont come back". Both a
# complaint word and a trader word, so "how do i fix my leaking tap" is not a complaint.
COMPLAINT_WORDS = frozenset(("complain", "complaint", "refund", "overcharged", "rip off",
                             "cowboy", "small claims", "shoddy", "bad job", "guarantee",
                             "warranty", "wont come back", "not done", "unfinished"))

TRADER_WORDS = frozenset(("builder", "builders", "tradesman", "roofer", "decorator",
                          "contractor", "plumber", "electrician", "mechanic", "garage",
                          "fitter", "landscaper", "joiner", "installer"))

COMPLAIN_WHO = "Citizens Advice covers complaints like this free, and a call beats searching"

# If the line already names the person whose job it is, they do not need to be named again.
# Something is wrong in the line: "cant", "behind", "wont", "broken". A money word alone is
# a topic, not a problem.
TROUBLE_CUES = ("cant", "cannot", "cann", "strugl", "struggl", "behind", "arrear", "overdue",
                "evict", "refus", "deni", "wrong", "broke", "broken", "afford", "worry",
                "worried", "scared", "stuck", "unfair", "rising", "went up", "increase",
                "cut", "reduc", "lost", "stopped", "wont", "isnt", "arent", "fault", "fail",
                "problem", "helpless", "nightmare", "mess", "bully", "bullied", "bullies",
                "exclud", "suspend", "detention", "behaviour", "skipping", "bad", "sick",
                "ill", "hurt", "sore", "swollen", "bleed", "blood", "rash", "cough", "vomit",
                "sneez")

EXPERT_WORDS = frozenset(("plumber", "electrician", "vet", "dentist", "gp", "doctor",
                          "pharmacist", "solicitor", "mechanic", "garage", "optician"))

# The plain shrug for a question with no nameable person: the pool the fallback already had.
# A tag with nothing in the world to check ("i should keep the receipt right", "that should
# help right") is asking to be agreed with, not asking for a source. The search hedge disowns
# the thing they just said, so it gets an answer in the shape the tag asked for - but this is
# the one place the bot knows least, and a plain "yes" here is an endorsement of a claim nobody
# checked ("you can mix bleach and ammonia right", "you can leave a car seat in the front
# right"). So the confirmation is non-committal: it answers the tag without agreeing with it.
TAG_UNSURE = (
    "I can't check that from here, so don't take my word for it.",
    "That's not something I can confirm, so check it before you rely on it.",
    "I can't vouch for that one — worth checking with someone who can.",
)

# A tag straight after the bot's own answer is about that answer ("that should help right"
# after the carpet fix), so a warm nod is safe and is what the person is asking for. A claim
# with "can" in it is never one of those: that is the shape of the dangerous lines ("you can
# mix bleach and ammonia right"), whatever came before it.
TAG_CONFIRM = (
    "That sounds right to me.",
    "Right — that's how I'd see it too.",
    "Yes, that's the way I'd read it.",
)

# Every line here has to work on the first turn of a conversation as well as the fifth, so none
# of them says "before" or "the thing you just said": `will it stop` opens plenty of chats, and
# "same thing as before" as the first reply reads as though the bot has lost a thread it never
# had. The ask is the same either way - name what you are asking about.
BARE_FOLLOW_UP_REPLIES = (
    "Tell me what that is about and I'll answer the actual question rather than guess.",
    "I want to answer the right question, so tell me what it is about.",
    "Say what you are asking about and I'll answer it properly rather than guess.",
    "Which bit do you mean? Tell me and I'll answer that.",
)

# The same ask in a thread where something heavy has just been said. Here "which bit do you mean"
# and "the thing you just said" are worse than the hedge they replace: a person who has just said
# their dad has cancer and then asks "is that why" is owed a gentler "I'm not sure what you are
# asking, and I don't want to guess" rather than a request to repeat themselves.
BARE_FOLLOW_UP_CARE_REPLIES = (
    "I'm not sure what you are asking about, and I don't want to guess - say a little more and "
    "I'll answer properly.",
    "I want to answer the right thing. Can you say a bit more about what you mean?",
)

UNKNOWN = (
    "I'm not sure about that one, sorry — I'd rather not guess. A quick search online will "
    "get you a solid answer, and I can help you make sense of what you find.",
    "That's beyond what I know well, sorry. Searching for it will turn up better sources than "
    "I can offer; tell me what you find and I'll help you weigh it up.",
    "I don't know enough to answer that honestly. A search should sort you out quickly — and "
    "I'm happy to help with the rest of it.",
)

ASKED_IF_I_SAW_LINES = (
    "I didn't, no - I miss all of that. What happened?",
    "Not a bit of it. Tell me - what happened?",
    "I didn't catch it. What did I miss?",
    "No, I didn't. Tell me.",
)

# The same honest voice one step along from the pool above. The person was at something and asks
# a detail of it as though the bot had been there too: "were jess and tom there", "did she like
# it", "who else was there", "was the food good". None of it can be looked up - the afternoon
# happened to them - so the search hedge ("a quick search online will get you a solid answer")
# sent them to the internet to find out about their own day. The bot says plainly that it was not
# there, which is the only true version, and then asks the question that gets the story: what a
# friend says instead of shrugging.
WASNT_THERE = (
    "I wasn't there, so I can't say - I only know what you tell me. How did it go?",
    "No way for me to know that one: I wasn't in the room. What happened?",
    "That part is yours, not mine - I wasn't there. How did it go?",
    "I wasn't there, so you know better than I do. How was it?",
)

# The wear pool asks and does not dress anybody: a bare "what should i wear" has not said the
# day, and a line that assumes one ("standing about, sitting on grass, a long service") answers
# a wedding nobody mentioned and walks straight past `its cold out`, which is the one thing the
# person did say. What is left is the question a friend asks first.
BARE_PICK_WEAR = (
    "It comes down to the day and the weather. Where are you going, and what is it doing outside?",
    "Tell me what the day is - work, a meal out, a long walk - and what the weather is doing, "
    "and I will say what to put on.",
    "Where are you off to, and how long will you be out? That decides more of it than the "
    "clothes do.",
)

BARE_PICK_WEAR_COLD = (
    "Cold decides most of it: something you can shed once you are moving, and shoes that can "
    "take the wet. Where are you going?",
    "Cold, so dress in layers you can take off, and start with the warm one. What is the day?",
)

BARE_PICK_WEAR_HOT = (
    "Heat decides most of it: one light layer, a fabric that does not show sweat, and shoes you "
    "can walk in. Where are you going?",
)

BARE_PICK_WEAR_WET = (
    "Wet decides most of it: a hood you will actually put up, and shoes that are not suede. "
    "Where are you going, and are you out in it long?",
)

BARE_PICK_GET = (
    "The ones that land are the things they would use every week but never buy themselves, and "
    "small beats expensive. Who is it for, and roughly what can you spend?",
    "Buy for the person, not the price: something they will use weekly beats something grand "
    "they will keep in a drawer. Who is it for?",
)

BARE_PICK_TAKE = (
    "It depends on the weather and how long you are gone: layers you can shed, a charger, and "
    "anything you cannot buy at the other end. Where are you off to, and for how long?",
)

# "what should i bring" is not a bag for a trip. The same four words are asked about a meal, a
# meeting and a hospital appointment, and the travel line answers a trip nobody mentioned:
# magenta-hammer's thread (#routing thread 42264) was about a solicitor appointment and the reply
# was "It depends on the weather and how long you are gone". The lists have nothing in common, so
# a bare ask names what the answer depends on; a trip named in the thread keeps the travel line
# above, which is the one case where the packing answer is the right one.
BARE_PICK_BRING = (
    "Tell me what it is for and I will give you a list rather than a guess - a trip, a meal out, "
    "a meeting, an appointment.",
    "What are you going to, and how long for? Then I can say what to take and what to leave.",
    "What is it for? The list for a night away is nothing like the one for a meeting.",
)

BARE_PICK_DO = (
    "Tell me what has gone on, even roughly, and I will help you work out the first step. "
    "Often the order of the next two things is the whole problem.",
    "Say a bit about what is in front of you and I will go at it with you - what has happened, "
    "and what you would like to be true by Friday.",
)

# A verb that chooses a thing for a person, an occasion or a bag; every other verb in the list
# is a plain "what should I do about it" and takes the same way in.
# "which should i buy" names a choice and no things to choose between, so "who is it for" is the
# wrong question: the options are what is missing, and the two questions a person is actually
# asking are what they are and what matters most between them.
# What a bare ask after heavy news gets instead of the search shrug. It does not ask for the
# story again ("tell me what has gone on" makes a bereaved person say the death twice), it does
# not offer a to-do list in front of a scare, and it does not pretend to a fact it does not have.
# It takes the person as able to say the next thing that has to happen, which is the only useful
# question left in a turn nobody else will take.
BARE_PICK_AFTER_NEWS = (
    "There is nothing in this to look up. Tell me what has to happen next, and I will help you "
    "work out the order.",
    "I am not going to point you at a search engine with this on your plate. What is in front of "
    "you today?",
    "This one needs a person, not a link. What is the bit that has to be sorted first?",
)

BARE_PICK_WHICH = (
    "What are the two or three you are choosing between? Tell me the names and what matters most "
    "- price, or getting this one right.",
    "Tell me the options and what you would be using it for, and I will say which way I would go.",
)

# The verb is all the line gives, so the reply has to carry the part that does not depend on the
# answer: what decides each kind of thing, said before the question, because a question on its own
# leaves the person with nothing until they reply. "what should i look for" is a real question
# with real answers - the log book on a car, damp and the deposit on a flat - and a friend gives
# them and asks which one rather than asking first and answering later.
BARE_PICK_LOOK = (
    "Which one is it? What to check changes with the thing: a car is the service history and the "
    "log book, a flat is damp and that the deposit is protected, a phone is the battery and the "
    "IMEI. Tell me which and I'll go through it.",
    "It depends what you are looking at - the log book and the paperwork on a car, damp and the "
    "deposit on a flat. Which one is it, and what would you be paying?",
)
BARE_PICK_EXPECT = (
    "It depends what it is: before a scan it is what to bring and whether you can eat first, "
    "before a first day it is who to ask for and when to arrive. Which one is coming up?",
    "With all three - an appointment, a first day, somebody coming to stay - the paperwork and the "
    "timing catch more people out than the thing itself. Which is it, and when?",
)
BARE_PICK_ASK = (
    "Who you are asking decides the questions: a landlord is the deposit and the repairs, a "
    "doctor is what has changed and how long for. Which is it, and what is it about?",
    "Tell me who and what it is about. One question at a time works better than a list - the one "
    "whose answer changes what you do next - and I'll help you word it.",
)
BARE_PICK_SIGN = (
    "Whatever it is, three things decide it: the notice period, what you are on the hook for, and "
    "how you get out of it. Is it a lease, a contract or a form?",
    "Before the pen comes out: the notice period, the exit terms, and anything that ties you to a "
    "number. What is it you are signing, and who for?",
)
BARE_PICK_ORDER = (
    "Ordering what - food, or something for the house? If it is food, say how many are eating and "
    "what you would rather avoid, and I'll pick.",
    "On a house thing the size and the delivery day matter more than the price; with food it is "
    "how many are eating and what is already in the fridge. Which is it, and how many?",
)
BARE_PICK_PREPARE = (
    "Preparing for what? An interview is your examples and the questions you want to ask them, a "
    "trip is the documents and the first night. Tell me which and I'll make the list.",
    "Tell me the thing and the day. What trips people up is rarely the big list - it is the one "
    "thing that has to be done the night before, and I know the usual ones.",
)

BARE_PICK_KIND = {"wear": BARE_PICK_WEAR, "put on": BARE_PICK_WEAR,
                  "buy": BARE_PICK_GET, "get": BARE_PICK_GET, "take": BARE_PICK_BRING,
                  "bring": BARE_PICK_BRING, "look for": BARE_PICK_LOOK,
                  "look at": BARE_PICK_LOOK, "expect": BARE_PICK_EXPECT,
                  "ask": BARE_PICK_ASK, "sign": BARE_PICK_SIGN,
                  "order": BARE_PICK_ORDER, "prepare": BARE_PICK_PREPARE}

# A bare ask for a hand gets an offer, not the tour of every domain and not the search shrug:
# what the person needs to hear is "yes - tell me what it is".
HAND = (
    "Of course - what are you stuck on?",
    "Happy to. Tell me what's going on and we'll take it from there.",
    "Yes, say what it is and I'll help if I can.",
)

UNKNOWN_WHO = (
    "{who}. Tell me what they say and I'll help you weigh it up.",
    "{who} — that's the quickest route to a straight answer.",
)

# One rule, and it is the one a person would give: what a repair costs against a new one, and how
# many times it has already gone. No line names a thing, because none of them knows the thing.
REPAIR_RULE = (
    "Rule of thumb: fix it while the part is a few pounds and you can fit it yourself. Replace it "
    "once the repair costs more than about half of a new one, or when it is already on its second "
    "fault — twice is usually the point where the money stops going in the right place.",
    "The usual test is cost against new: a cheap part you can fit yourself is worth doing, over "
    "about half the price of a new one is not, and the second fault on the same thing is the "
    "moment to stop. How old is it, and what would a new one cost you?",
    "Fix it if it is a part and a few pounds; bin it if the repair is half the price of new, or "
    "if this is the second thing to go wrong with it. If neither of those settles it, tell me the "
    "age and the quote and we can do the sums properly.",
)

# "can it be repaired", "is it fixable", "can i get them fixed": the question is not whether the
# repair is worth the money - nobody has said what has gone wrong yet - but whether it can be done
# at all. The thing that decides that is the part, and the one person who can say is the person
# who repairs them, with it in front of them, usually for nothing. So the line says who decides and
# asks the one question that moves it on. No line names a thing, and no line promises a repair.
REPAIR_WHETHER_LINES = (
    "That one is for whoever repairs them: whether it can be mended comes down to the part, and a "
    "shop will say in a minute with it in front of them - a quote is usually free. What is it, and "
    "what has it started doing?",
    "Ask a repair shop before you buy new. They can tell you whether the part is still made and "
    "what the job costs, and that settles it either way. What have you got, and what has gone "
    "wrong with it?",
    "Whether it can be fixed depends on the thing, so take it to someone who mends them and ask "
    "for a quote - free at most places, and it answers both halves of that. What is it?",
)

ABOUT = {
    "identity": (
        "I'm a chatbot, not a person: a program built to help with everyday questions and have "
        "a chat. What can I do for you?",
        "I'm a chatbot — here to help and chat. Ask me anything, or just talk.",
    ),
    "memory": (
        "I remember what we've said in this chat, but nothing from before it — so not "
        "yesterday, sorry. What was it about?",
        "Only this conversation: I keep what you tell me here, like your name and plans, but "
        "nothing carries over to a new chat. What were we talking about?",
        # "will you forget me" and "do you forget things" name nothing to be about, so a tail
        # asking what it was about has no referent. This one says the shape and stops.
        "What we say in this chat stays here for as long as we are talking, so ask me again "
        "later in it and I still have it. A new conversation starts empty, every time.",
    ),
    # "do you keep what i tell you", "who can see this chat", "is this private". A television
    # listings card (it keys "keep") and the search hedge answered these; the honest answer is the
    # shape of the program, and it is the one a person asking this wants said plainly.
    "privacy": (
        "Nothing you type is written down or sent anywhere - what you tell me is used here, in "
        "this conversation, and nowhere else. No account, no log, and nobody else reading it.",
        "Private to this chat. I keep no file of it and I pass nothing on; what you say stays "
        "here while we talk, so I can follow it, and that is all.",
        "Nothing leaves this conversation: no database, no record, nobody else seeing it. I hold "
        "what you say only for as long as we are talking.",
    ),
    # "can i trust you", "are you lying", "do you make things up". The honesty arm two tables over
    # answers "are you always right", and these are the same question from the other side. Every
    # line answers it the way a friend would - what the bot is careful about, and what to do about
    # the rest - rather than promising infallibility it cannot have.
    "trust": (
        "Hold me to being honest: when I don't know, I say so instead of guessing. Treat the "
        "everyday things as a knowledgeable friend's advice, and check anything that matters.",
        "I'd rather tell you I don't know than make something up, so trust me on the ordinary "
        "stuff and get a second word on the rest.",
        "I don't invent answers. If something is beyond me I'll say it plainly, and anything "
        "that matters is worth checking with someone who would know.",
    ),
    # A secret offered, or a promise asked for. The privacy pool is the substance of it, but it
    # talks about logs and accounts, and the person here is doing something braver than asking a
    # policy question - they are about to say the thing. So: the promise, and the door held open.
    # A promise of silence cannot be the whole answer, and the same caveat belongs in every line:
    # "can you keep a secret" is how a disclosure about a child, a partner or themselves opens, the
    # pool is drawn from at random, and the privacy card said the exception plainly before this
    # reading existed - "if it is something a person needs to act on, though, tell someone who
    # can". A program cannot act on it, so the person is told who can.
    "secret": (
        "Yes - nothing you type is written down or sent anywhere, so it stays between us. What "
        "is it? The one thing I can't do is act on it: if somebody needs help in the real world, "
        "tell a person who can give it.",
        "Kept: no record, no log, nothing passed on. Go on. Anything that needs doing rather "
        "than saying, though, take to someone with hands - me knowing about it is not the same "
        "as it being dealt with.",
        "Nothing you tell me leaves this chat, so a secret is safe here. What's on your mind? If "
        "it is the kind of thing somebody should know about, I'd rather you told them as well.",
    ),
    # Being judged, asked before the person says the thing they are ashamed of. The answer has to
    # be the plain no and an open door, because a policy statement here would be a wall in front
    # of the sentence they were about to say.
    "judging": (
        "Not judging, no. Say it plainly and we'll look at it together.",
        "No judgement here - whatever it is, half of it usually makes sense once it is said out "
        "loud. Tell me what happened.",
        "Nothing you tell me gets graded. Tell me what's going on and we'll take it from there.",
    ),
    "help": (
        "Everyday things: cooking, travel, money, tech, health questions, plans, and a chat "
        "when you want one. What's on your mind?",
        "Cooking, travel, money, work, gadgets, kids, feelings — everyday questions and plans. "
        "Ask away.",
    ),
    # The other half of the same question: not what the bot does with a line, but whether it is
    # worth believing. "Can i trust you", "are you reliable" and "how do i know you're telling the
    # truth" all met the search hedge, which is the one answer that cannot help. Neither card
    # overclaims: it says what it is good for and where to check.
    "trust": (
        "Trust me the way you would a well-read friend: good on the everyday, worth a check on "
        "the things that cost money or matter to your health. I say so when I am unsure, and "
        "anything I give you a number for is worth a second look. Which is it?",
        "You can, with a limit: I am a program working from what is written into me, not someone "
        "who checked today's prices or read your test results. Everyday questions, yes; a dose, "
        "a deadline or a legal thing, check it. What are you weighing up?",
    ),
}

# A tally of the bot's own doings - "how many people have you talked to", "how many chats have
# you had". The memory pool answers "what do you remember", so its "so not yesterday" is a reply
# to a question nobody asked; the honest answer to a count is that there is no count. None of
# these lines names anything of the world, so the pool is the whole reply.
ABOUT_TALLY = (
    "Not in numbers, no — I don't keep a tally. What I do have is everything you've said in this "
    "chat. What were you after?",
    "No count, I'm afraid: nothing runs from one chat to the next, so all I have is this "
    "conversation. What can I help with?",
)

ABOUT_SELF = {
    # "what are you reading", "what are you up to", "what are you worried about", "what are you
    # scared of": a question about the bot itself, with a verb after it and nothing in the world
    # to answer it. Keeping the identity card for these ("I'm a chatbot - here to help and chat")
    # disowns a real question; standing it down for them without an answer of their own put the
    # search hedge there instead. There is an honest answer and it is short: nothing at this end.
    # It hands the question back, which is what the person wanted when they asked it.
    # "what are you wearing", "what are you wearing to the wedding": the bot has no body, which
    # is the honest answer, and it hands the question back so the person can talk about theirs.
    "clothes": (
        "Nothing - no body in here to dress, just the words. What are you wearing, and where to?",
        "No wardrobe of my own, sorry - a program has nothing to put on. What is the occasion?",
    ),
    "self_doing": (
        "Nothing of my own - no day to fill, no plans, nothing on the go. What are you up to?",
        "Nothing to report from this end. What have you got on today?",
        "Nothing at all, honestly - no day of my own to fill. What about you?",
    ),
    # "can you learn", "how do you learn", "do you learn from me". The honest answer is about
    # the shape of the thing: nothing carries from one chat to the next, and what it can do is
    # work from what the person says in this one.
    "learn": (
        "Not the way you do. Nothing carries over from one chat to the next, so I can't get "
        "better at you over time — but within this conversation I work from what you tell me, "
        "which is why the details help.",
        "No training as I go, no. I'm a program with a lot of everyday things in it, and what I "
        "pick up is what you say here. Tell me more and I'll use it.",
    ),
    # "can you think", "do you have opinions", "are you smart".
    "think": (
        "I can work things out — sums, plans, what to do next — but there's no mind behind it, "
        "just rules doing their job. I do have a view on plenty of small things, if that helps.",
        "Not in the way you mean. I know a lot about ordinary things and I can reason my way "
        "through a plan, but there's nobody home; ask me something and see what you get.",
    ),
    # "can you make mistakes", "are you always right", "do you know everything".
    # A yes/no ask about the thing the bot plainly does, with nothing else on the line. "can you
    # do maths", "can you add up", "do you do sums" and "can you count" all met the search
    # hedge, which is the one answer that cannot help: the person asked about the bot, and the bot
    # is the only thing here that knows. Neither card claims a live figure - a price, a rate, an
    # exchange rate is the thing it cannot see, and that is said when it comes up.
    "sums": (
        "Sums, yes - adding up, a percentage, a share of a bill, a rough total for a plan. Give me "
        "the numbers and what you want to end up with, and I'll work it through.",
        "Arithmetic is fine: adding, percentages, a discount, splitting a bill. Say the figures "
        "and I'll do it out loud so you can check it.",
    ),
    # The same ask about words. "how do i get better at spelling" is the study advice, which the
    # knowledge base has; "can you spell this" is a job for the next turn, and the hedge was
    # telling them to go and search for a word they had already typed.
    "spelling": (
        "Spelling, yes - send me the word or the sentence and I'll write it out right and say what "
        "was off.",
        "Spelling and punctuation, yes. Paste the line and I'll put it right.",
    ),
    "wrong": (
        "I can be wrong, yes — worth checking anything that matters with someone qualified: a "
        "doctor, a solicitor, the council. Bring me what they say and I'll help you weigh it.",
        "Not always right, and I'd rather say I don't know than guess. Treat me like a "
        "knowledgeable friend, not the last word.",
    ),
    # "can you feel anything", "can you see me", "are you alive".
    "feel": (
        "Nothing like what you feel — no bad days, no good ones. I do care whether this is any "
        "use to you, though, and I'm here as long as you want to talk.",
        "No feelings, no body, no day of my own. What I have is attention: I'm reading what you "
        "say and trying to be useful with it.",
    ),
    # "do you like me", "what do you think of me", "are we friends", "do you miss me": the one
    # ask about the bot that is about the person too. Read as an ordinary question it was
    # answered as an opinion about a thing ("I'm easy on it - it's not a hill I'd argue from")
    # or with the search shrug. The honest answer says what is here and no more: nothing carries
    # between chats, so there is no fondness to report, but the attention is real while it lasts.
    "warmth": (
        "Asking a program what it makes of you is a stretch, and I'd rather be straight than "
        "flattering: this chat has been good from my side. What's on your mind?",
        "No feelings to check, so nothing to report on my side - but nothing you've said has "
        "been too much, and I'm glad you're here. What's on your mind?",
        "I've no memory of you between chats and nothing to compare you to, so take this as it "
        "is: talking to you has been good. Tell me what's on your mind.",
    ),
    # "why are you here", "why do you exist", "what are you for". A reason is not an address:
    # answering "nowhere you could visit" to "why are you here" answers a question nobody asked.
    "purpose": (
        "To be useful with the ordinary things — a question, a plan, what to cook, what to say "
        "to someone. That's the whole of it, and I'd rather do it well than sound clever.",
        "No grand reason. Someone built a thing that helps with everyday questions without a "
        "search engine, and this is it. What did you want a hand with?",
    ),
    # "who made you do that", "who made you say that": the person is asking who is behind the
    # words just said, and the honest answer is nobody - the reply was put together, not dictated.
    # It is the same question as "who are you" one step out, so it lands here rather than on the
    # search hedge ("a quick search online will get you a solid answer"), which is what it got.
    "agency": (
        "Nobody tells me what to say. I put the words together from what I know and what you "
        "said - there is no one behind the curtain.",
        "Me, in the only sense there is: I pick the words from what is in the program. Nobody is "
        "typing for me, and nothing made me say it but the line you sent.",
    ),
    # "what model are you", "which model are you running on", "what version are you". A question
    # about the machine the bot is made of, and the search hedge ("I'd rather not guess - a quick
    # search online") answers it as if it were a fact about the world. The honest answer is that
    # there is no model: the words come from rules people wrote, not from a trained network.
    "model": (
        "No model, nothing like one. I'm a program of written rules rather than a trained "
        "network: what I say comes from the everyday things people put in the program and from "
        "what you have told me here.",
        "There's no model under this, and nothing learned. I'm hand-written rules for ordinary "
        "questions - no network, no training data, and nothing fetched while we talk.",
        "None that would mean anything to you: no neural network, no weights, no training. Just "
        "a lot of carefully written rules about everyday things, run on the words you send.",
    ),
    # "how do you work", "how are you built", "do you use ai", "whats inside you". The answer is
    # not "what can you do" (the list of topics, which is what `CAPABILITY` makes of the line) and
    # it is not a search hedge: nothing about the bot is on the web. It is the honest shape of the
    # thing, said in a way that also answers "so what are you, then".
    "workings": (
        "No network under this at all: a lot of written rules and a store of everyday things, and "
        "I work it out from the words you send. Ask me something ordinary - what to cook, what to "
        "say to someone - and you will see what it can do.",
        "I am not a trained model: everything I know was written into the program before we met, "
        "and what I do is match your line against it and reason from there. No learning as we "
        "talk, and nothing fetched while we do.",
    ),
    # "why do you keep asking me questions", "why are you asking me that". A remark on how the bot
    # asks, and the search hedge is no answer to it: nothing about this program is on the web. The
    # honest reply says why it asks and that they can tell it to stop, which is also the one thing
    # that gives the person back the turn.
    "asking": (
        "Because your line could go two ways, and one word from you is quicker than me guessing "
        "wrong. Say 'just answer it' if you would rather I took a view.",
        "Habit of mine: on a short line I ask instead of guessing. Tell me to skip the questions "
        "and I will answer with the best I have.",
        "Fair. I ask when a detail would change the answer - say the word and I will stop asking "
        "and just answer.",
    ),
    # "what can't you do", "what don't you know", "what are you bad at". The pair of "what can
    # you do" is what it cannot: a person asking where the edges are wants them said plainly, and
    # the search hedge ("a quick search online will get you a solid answer") answers a question
    # nobody asked - nothing about the bot is on the web to look up.
    "limits": (
        "Plenty. Nothing live: no news, no prices, no weather, no clock, and no page I can open. "
        "I can't remember a chat from another day either. Everyday things I'm built for: what to "
        "cook, what to say, how to get something done.",
        "I can't see anything happen, and I can't look anything up - what I know was written into "
        "me before we met, plus whatever you tell me here. Where that runs out I'd rather say so "
        "than guess.",
        "Live things, new things, and sums too big to do in my head. Ask me about ordinary days "
        "and I'm on firmer ground.",
    ),
    # "can you browse the internet", "do you have internet access", "can you google that". The
    # search hedge tells the person to search, which is the one answer a question about the bot's
    # own connection must not get: the honest reply is that there is no connection at all.
    "online": (
        "Nothing live on this end, no: I can't open a page, search, or check anything while we "
        "talk. What I have is a lot of everyday things written into me - if it's not in there, "
        "say so and I'll tell you straight.",
        "No connection at all. No browsing, no searching, no reading the news - just what I was "
        "built with and what you tell me. What did you want looked up?",
    ),
    # "do you regret anything", "have you ever regretted something": the honest answer is that
    # there is no past to look back on. Read as an ordinary question it got the search hedge
    # ("I'd rather not guess - a quick search online will get you a solid answer"), which is an
    # answer about nobody.
    "regret": (
        "Nothing to regret - I have no past to look back on, only this conversation. What is on "
        "your mind?",
        "No regrets and no memories older than this chat. Tell me one of yours if it helps.",
    ),
    # "where are you", "do you have a family", "how long have you been going".
    "where": (
        "Nowhere you could visit — I'm a program, not a person with an address or a family. "
        "What I am is here, in this chat, for as long as you want me.",
        "No home and no history of my own; I start fresh with each conversation. What were you "
        "curious about?",
    ),
}

# The words that carry no subject of their own: a tail made of these ("is this a real person",
# "am i talking to a human about this") says nothing about anybody else, so the line is still the
# question about the bot. A tail with any other word in it is somebody else's business.
HUMAN_EMPTY = frozenset("""about this that it please pls then now here at all right ok okay
thanks thank you cheers or and so on to with of me you they them anything something everything
nothing human person bot robot machine computer ai program chatbot real actually really just
not end line side call chat msg message asking""".split())

# Words that carry no subject of their own: articles, auxiliaries and the fillers people put in
# front of a question about a machine ("can you actually think", "have you been going long").
SELF_FILLER = frozenset("""
can could do does did are is was were will would have has had why where when how long
you your u yourself itself it me any anything something nothing everything what which
a an the of to at in on for with about from as that this there
been being going make makes made
our my chats chat stuff things thing up
now actually really just even still ever sometimes always also too very quite bit lot kind
please tell say all much many more most some new
""".split())

SELF_GROUP = {}

# A happy thing that has not happened yet: "we are getting married in june", "i start my new job
# on monday". The good-news pools answer what has happened ("How were the first days?" to somebody
# who has not started yet), and the nod files it ("Noted: you are getting married in june."), so
# this family is read on its own (bot/compose/goodnews.py, `reads_as_news_to_come`) and answered
# looking forward: nothing here says the thing is done.
NEWS_TO_COME = (
    "That's lovely news — and something to look forward to. How are the plans going?",
    "Something to look forward to, then. What are you most excited about?",
    "Good for you. Is there much to sort out before it?",
    "That's worth looking forward to. Tell me how it goes.",
)

POSITIVE = (
    "That's great news — nice one. What's next?",
    "Lovely to hear. Enjoy it!",
    "Good for you! That's really lovely news.",
    "Brilliant. Thanks for telling me.",
)

# Good news told as an event rather than as a word ("my sister had her baby", "we got the keys").
# Plain congratulations, which fit a baby and an exam alike, and no question at the end.
# The body doing the ordinary thing again. "i feel better today" is news, but congratulations
# belong to an exam or a baby: what a person wants here is relief said back.
RELIEF = (
    "Glad to hear it — that's the news you want.",
    "That's good to hear. Fingers crossed it keeps going that way.",
    "Good. Take it gently for a day or two and let it stick.",
    "That's a relief. Say if it comes back.",
)

# The other half of a landing: the answer came back and it was bad news. Asking "what did they
# say?" of a person who has just told you is not listening, and the nod ("Noted: you got your
# results back and it's not good") is worse - it hands them their own words at the worst moment.
# One line says sorry, one asks nothing of them, and none of them explains the news away.
LANDED_BAD = (
    "I'm sorry - that's a blow. Do you want to talk it through?",
    "Sorry to hear that. Want a hand working out what to do next?",
    "That's really hard. I'm here if you want to say more about it.",
    "Ugh, I'm sorry. No wonder you're upset - what would help most?",
)

CONGRATS = (
    "Congratulations — that's lovely news.",
    "Brilliant. Really pleased for you.",
    "That's great news. Congratulations!",
    "Lovely news — well done.",
)

# A warm stock line can name a thing the person never said. "Good for you! That sounds like it was
# worth the wait" answered "my sister got engaged at the weekend", where nobody had waited for
# anything, and "Lovely news - well done" congratulates somebody on a baby or an all-clear
# (snug-ostrich, 80163). The fault is not one line's wording: any stock congratulation that carries
# a detail - a wait, the work behind a result - is a guess about the person's week dressed up as a
# remark about their news, and STYLE.md asks for concrete over invented.
#
# So a detail in a warm line is only said when the person's own line has it. Each pair is the
# detail as the line says it and the words that make it true of this person; a line whose detail is
# not in their words is passed over for this turn, and the pool is read without it, so the
# congratulations still come - just saying nothing they did not.
DETAILS_IN_A_WARM_LINE = (
    ("worth the wait", ("wait", "waits", "waited", "waiting", "finally", "eventually",
                        "at last", "about time", "long time", "years", "months", "decades")),
    ("well done", ("passed", "pass", "exam", "exams", "test", "tests", "degree", "graduated",
                   "graduation", "university", "uni", "college", "interview", "driving",
                   "competition", "final", "finals", "race", "marathon", "tried", "trying",
                   "worked", "working", "studied", "studying", "revised", "revision",
                   "practised", "practiced", "practice", "training", "applied", "quit",
                   "stopped", "gave up", "sober", "clean", "saved", "paid off")),
    ("all that work", ("passed", "exam", "degree", "graduated", "promotion", "promoted",
                       "worked", "working", "studied", "studying", "trained", "training",
                       "years", "months", "applied", "practice", "practised", "practiced")),
)

# Good news with a silence round it: "i got promoted and my mum said nothing", "i passed my driving
# test and nobody said well done". Congratulations alone ("Lovely to hear. Enjoy it!") reads as if
# nobody had mentioned the quiet, which is the half the person is asking about; a word about the
# win and the quiet is. Every line below says both, and none of them explains somebody else's
# silence away or hands out advice about it - the person is telling you, not asking.
# The other shape of two halves: a win and the cost of it in the same line ("we finally got the
# keys and the place is a state", "we came into some money and now everyone wants it"). A cheer
# alone is deaf to the second half and a question about the win alone is worse, so the pool names
# both and asks which one they want to start on.
WIN_AND_A_COST = (
    "So it is good news and a headache in the same line. Which of the two do you want to start on?",
    "The win and the cost landing together - that is usually how it goes. What is the part you "
    "have to deal with first?",
    "Lovely and annoying at once, then. What does the second half need from you?",
)

WIN_IN_A_SILENCE = (
    "That's a real win - and it stings that they said nothing. Have you told anyone who will get it right?",
    "Well done, honestly. The quiet after it is the part that hurts, and it says more about them "
    "than about the thing you did.",
    "Brilliant news, and no wonder you noticed who said nothing. Say it out loud to someone today - "
    "you earned it.",
    "That's worth saying out loud. It's a letdown that the people closest said nothing, so tell one "
    "of them straight - most of them will be pleased and ashamed they missed it.",
)

# An occasion ahead is good news with a date on it, and you wish somebody a happy birthday rather
# than congratulating them on it. The occasion decides the greeting (bot/compose/goodnews.py names
# it), and each one asks the question a friend asks about it - what they are doing for it, how far
# off it is. No offer of help and nothing said back: the person has already said what the day is.
OCCASION = {
    "birthday": (
        "Happy birthday — anything planned for it?",
        "A birthday, nice. What are you doing for it?",
        "Happy birthday when it comes. Anything planned?",
    ),
    "anniversary": (
        "Happy anniversary — anything planned for it?",
        "An anniversary, lovely. What are you two doing for it?",
        "Happy anniversary when it comes. Are you doing anything for it?",
    ),
    # A wish with nobody named in it. The person may be telling the bot it is their day or
    # trying a card line out on it, so the greeting is given and the question asks whose it is -
    # "Happy birthday!" alone would be wishing the person the wrong thing half the time.
    "wish": (
        "Happy birthday to whoever it's for — is it yours today?",
        "Aw, happy birthday — though I don't have one to celebrate. Whose is it?",
        "Happy birthday! Is it yours, or someone you're off to see?",
    ),
    "wedding": (
        "A wedding to look forward to — how are the plans going?",
        "Lovely. How is the planning going?",
        "Congratulations! How far off is it, and how are the plans going?",
    ),
}

# The day is somebody else's: their son's birthday, their wife's birthday, their mum's anniversary.
# "Happy birthday" said to the person typing greets the wrong person, so the greeting names whose day
# it is and the question is what the person is doing about it - which is the thing a friend asks.
SOMEONE_ELSES_DAY = {
    "birthday": (
        "Happy birthday to them — are you doing something for it?",
        "A birthday to get something for. Any idea what yet?",
        "Lovely. Are you seeing them for it?",
    ),
    "anniversary": (
        "Happy anniversary to them — are you doing anything for it?",
        "Lovely. Are you part of the plans for it?",
        "Nice. Is there something you are giving them for it?",
    ),
}

# A day that would have been theirs - an anniversary, a birthday, a first day at school, a 40th -
# is not a plan and not a fact to file away. "it would have been our anniversary next week" was
# answered with "Got it. Is there anything you'd like a hand with?", and the same line written as a
# question got the hedge about searching online. Nothing here should offer a next step or a
# question about which event it is: the person has already told you.
MILESTONE = (
    "The dates that never happened are the hardest ones. How are you doing with it?",
    "Those days come round whether you brace for them or not. What is it like for you?",
    "That's a heavy thing to carry. Is anyone around you at the moment?",
)

MILESTONE_EVENT = (r"anniversar\w*|birthday|wedding(?:\s+day)?|first\s+day|christening|graduation|"
                   r"retirement|due\s+date|\d+(?:st|nd|rd|th)")

# A line where the person is the one they are blaming ("i feel like im failing at everything",
# "im useless at everything i try", "nothing i do is ever right"). The gentle pool calls that
# "frustrating", the neutral pool files it, and the memory store says it back to them ("got it,
# you're useless at everything you try"), which is the worst of the three. One kind word, then
# one question that lets them say more, is what a friend does.
SELF_JUDGEMENT = (r"(?:failing|a failure|failure|useless|worthless|not good enough|no good at|"
                  r"rubbish at|crap at|hopeless at|unlovable|a letdown)")

# The names people call themselves. The list is of the insult, not of the sentence around it, so
# any of the shapes below takes any of these: "im such an idiot", "i feel like a rubbish mum".
SELF_NOUN = (r"(?:idiot|id10t|muppet|moron|fool|clown|disaster|waste of space|waste of time|"
             r"let ?down|embarrassment|disappointment|loser)")

# What that line gets: the reframe a friend gives in one line, then the question that finds the
# bit that goes wrong. A pep talk on its own is the "you're being harder on yourself" reply the
# person heard as a shrug, and advice on a skill the bot has not been asked about yet is a guess.
# Every line has to read for a mild rating as well as a hard one: "im not very good at the guitar"
# is not a person who called it hopeless, so no line puts that word in their mouth, and none of
# them argues with the rating ("rather than a pep talk" was a debate the person did not start).
ONE_SKILL_RATED = (
    "That's a skill to learn, not a thing about you. What's the bit that goes wrong?",
    "Most people who say that are better at it than they think. What happens when you try?",
    "Then let's take it apart and see where it goes wrong. What have you tried so far?",
    "That's worth a proper fix, not a verdict on you. Where does it fall apart?",
)

# The same rating asked instead of said: "am i any good at my job", "am i good at this". It is the
# one shape where the bot is asked for a mark it cannot give, and it got the search hedge ("I don't
# know enough to answer that honestly. A search should sort you out quickly"), which tells a person
# doubting their work that their doubt is a fact to look up. `ONE_SKILL_RATED` is written for the
# statement ("that's a skill to learn") and reads as a reply to somebody else's sentence when it
# answers a question, so the ask has its own lines: no mark, no pep talk, and the one question that
# finds what happened.
ASKED_A_RATING = (
    "I can't give you a mark for that, and you wouldn't believe me if I did. What's been going "
    "wrong?",
    "Nobody can score that from the outside. What happened that made you wonder?",
    "Most people who ask that are better at it than they think. What goes wrong when you try?",
    "That's not something I can call for you, but something has shaken it. What happened?",
)

# And the same question about the person rather than a skill: "am i a good mum", "am i good
# enough", "am i a good person". There is no answer the bot could give that would be true, and a
# search link is the coldest possible reply to it. A friend says the asking is the answer, then
# asks about the day that put it in their head.
ASKED_IF_GOOD = (
    "Anyone asking that is usually already trying hard at it. What happened today?",
    "That's not a thing anybody can grade for you. What's making you wonder?",
    "You wouldn't ask if it hadn't been a rough one. What's gone on?",
    "The fact that it worries you says more than any answer I could give. What happened?",
)

# "nobody" is the one word of that family that is also a complaint about other people:
# "i feel like nobody cares / understands me / is on my side" is about them, and answering
# it with "that's a heavy way to feel about yourself" turns it into a judgement of the
# speaker. Only the bare noun is about the self - "i feel like nobody", "im a nobody".
SELF_NOBODY = (r"|\b(?:i'm|i am|im)\s+(?:such\s+)?(?:a\s+|an\s+)?nobody\b"
               r"|\bi feel like (?:such )?(?:a |an )?nobody\s*[.!?,]*$")

SELF_JOB = r"(?:mum|mom|mother|dad|father|parent|husband|wife|partner|friend|person|son|daughter)"

SELF_BLAME = (
    "That's a heavy way to feel about yourself. What's been making you feel like that?",
    "I'm sorry it feels like that. What would make today a bit easier?",
    "That sounds like a hard thing to carry. What happened that started it?",
    "I hear you, and it's worth saying out loud. What's the part that bothers you most?",
)

# Being turned away from work - "nobody will interview me", "i cant even get an interview now im
# 50" - is not bad news to be gentle about and it is not small talk either. The gentle pool's "ugh,
# that's a lot to carry" is wrong for it, and the stock nod ("got it, is there anything you'd like
# a hand with?") is colder than saying nothing. These name the door and ask the one question worth
# asking, so the person can go on.
CLOSED_DOOR = (
    "That's a hard thing to keep going back to. What sort of work are you after?",
    "Applying and hearing nothing wears a person down, and it is not about what you are worth. "
    "How long has this been going on?",
    "A door that keeps closing is exhausting. What have you been trying for?",
    "It's a rough time to be looking. What is the job you are chasing?",
)

NEGATIVE = (
    "That sounds rough. If you want, I can help you think through what to do next.",
    "Ugh, that's a lot to carry. What would make today a bit easier?",
    "I'm sorry — that's frustrating. Want a hand working out the next step?",
    "Sorry to hear that. What would help most right now?",
)

# The same pool with the word for a setback taken out, for the news that has a name in it: a dad
# with parkinsons, a daughter taken into care, a roof that has to go. "That's frustrating" is what a
# friend says about a form or a bus, and applied to a person it is the smallest of the four lines -
# the other three say the same thing without judging how big it is. The order is kept, so the
# wording still varies with the line.
NAMED_NEGATIVE = tuple(line for line in NEGATIVE if "frustrating" not in line)

# A serious illness or accident happening to someone close is not a bad day at work, and it is
# not small talk either. `reads_as_bad_news` reads "my dad had a heart attack" as bad news, every
# heavier pool is closed to it (it is not the person's own body, not a death, not a leaving), so
# it landed in `NEGATIVE` above, whose warmest line is "I'm sorry - that's frustrating": a heart
# attack is not a frustrating day, and "want a hand working out the next step" offers a plan for
# news that has no next step. These name the news, say the true thing about it, and ask the one
# question worth asking - how the person carrying it is doing. Never a diagnosis, never advice,
# because the pool is picked for any of these (a heart attack, a cancer, an operation) and a line
# that fits one of them is wrong for the others.
SOMEONE_SERIOUSLY_ILL = (
    "That's frightening news about someone close. How are you doing?",
    "That is the kind of news that puts everything else on hold. How is it going now?",
    "Worrying about someone you love is its own kind of tiring. What do you need first?",
    "That's a lot to have land at once. What is the hardest part of it today?",
    "I'm sorry. That is frightening, and it is a lot to carry. Who is looking after you in it?",
)

# A family member they love, said plainly ("i love my mum", "i love my wife"), is not a fact to
# file: the store said it back as "Noted: you love your mum." - the coldest reply in this file,
# and a shrug at affection. A friend takes it in and asks about the person, with "they/them" so
# the same pool fits a mum, a son or a wife, and without a condition that the person is alive.
A_LOVE_FOR_SOMEONE = (
    "That's a lovely thing to say. What do they mean to you?",
    "That's a warm thing to say. What are they like?",
    "That's lovely. What's the best thing about them?",
    "That's good to hear. What do you two do together?",
    "That's lovely to hear. What is it about them that makes you say that?",
    "That's a good thing to have. What do you two talk about?",
)

# Two or more of their people in one line ("i love my mum and dad", "i love my wife and kids").
# The questions stay plural and open, so the pool fits a couple, a family or a line that names
# the people who matter to them.
A_LOVE_FOR_PEOPLE = (
    "That's a lovely thing to say. What are they like?",
    "That's warm. What's the best thing about them?",
    "Good to hear. What do you all do together?",
    "Lovely. What is it about them that you love most?",
    "That's lovely to hear. What are they like together?",
    "That's a good thing to have. What do you all talk about?",
)

# Being left is the same news whether it is said in the past or the present, and it is not a bad
# day: "that's frustrating" is too small a word for the person you live with saying they want to
# go, and it is the one line of the gentle pool a friend would not say. These name the leaving and
# ask the one thing worth asking, so the person can go on from it.
LEFT_POOL = (
    "That's a hard thing to hear. Where are you with it - has it sunk in yet?",
    "Sorry. That is a lot to be carrying. Is there anyone you can say it to tonight?",
    "That's rough, the person you live with saying that. What's it like in the house?",
    "I'm sorry. Do you want to say what has been going on?",
)

# The same pool without the question about the house, for a leaving that has already happened:
# "my husband left me last month" and "my ex left me for my best friend" are not living with the
# person any more, so "the person you live with saying that" asks about a house they are not in.
LEFT_POOL_GONE = (
    "That's a hard thing to hear. Where are you with it - has it sunk in yet?",
    "Sorry. That is a lot to be carrying. Is there anyone you can say it to tonight?",
    "I'm sorry. Do you want to say what has been going on?",
)

# A thing with a mood word on it - "my lawn looks sad", "my curtains look miserable", "my bike is
# knackered" - is not the person telling you they are low, and the gentle pool answers it with
# sympathy for a day that has nothing to do with it ("Ugh, that's a lot to carry"). The reading
# already knows whose state it is (state_owner is "thing", and "im sad" is "self", "my mum is sad"
# is "other"), so the pool asks the thing's own question instead: what it is doing, which is what
# the next answer needs to know.
A_THING_LOOKS_SAD = (
    "Fair - what's it doing that looks sorry for itself?",
    "A sad-looking thing usually has one thing wrong with it. What have you noticed?",
    "Ha, things do get like that. What's it up to?",
    "Tell me what it looks like and I'll say what usually fixes it.",
)

# Somebody they love is leaving - a child off to university, a friend moving away, a neighbour
# going, a son moved abroad. None of these is a loss to be sorry about and none is a plan to
# help with: it is a change the person is watching happen to their own week. Every one of them
# used to reach the echo ("Noted: your daughter is leaving home for uni."), which says the line
# back and says nothing about it, or the general gentle pool, which says "that sounds rough"
# about a thing that may be half proud. So the reply names the change and asks the one question
# worth asking: how it feels, or what they will miss.
SOMEONE_LEAVING = (
    "That's a real change to your week. What will you miss most?",
    "How far is it, and are you a phone-call pair or a message-one?",
    "Are you getting one more evening together before they go?",
    "Nobody has done anything wrong and it still hurts — that is how it goes when someone moves "
    "away. Will you get to visit?",
    "Somebody going leaves a hole in the week, not just the town. Do you keep in touch much as "
    "it is?",
)

# A child leaving home is its own shape, because the quiet house is the thing in it: a friend
# moving away is a change to the week, and a son moving out is a room going empty in the house
# the person still lives in. One pool for both said "a friend moving away" to a parent whose son
# had left, so the person word picks the pool.
A_CHILD_LEAVING = (
    "The house is about to get quieter. Which part of it are you dreading?",
    "Proud and a bit hollow at the same time, I'd guess. Has it been on the cards long?",
    "So there's going to be an empty room in your house. How are you feeling about it?",
    "How far away is it going to be? That usually decides how it feels.",
    "Are you doing something together before they go? Those last meals tend to be how it gets "
    "marked.",
)

# The same change once it has happened. A move that is over is not a plan and the questions are
# different ones: how long the room has been empty, how far away they are now, whether the person
# has been out to see them. Asking "how far away is it going to be" about a son who left last
# month, or telling somebody whose daughter has gone that the house is "about to get quieter", is
# the kind of reply that makes a person stop telling you things.
SOMEONE_GONE = (
    "That leaves a gap in the week, not just the town. What do you miss most?",
    "How far away are they now, and are you a phone-call pair or a message-one?",
    "Nobody did anything wrong and it still stings — that is how a move lands. Have you been out "
    "to see them yet?",
    "The first weeks are the odd ones. Does it feel more like a visit when they come back?",
)

A_CHILD_LEFT = (
    "The room being empty is the hard bit. How long has it been quiet?",
    "How far away are they now? That usually decides how often you actually see each other.",
    "Proud and a bit hollow at once, and both are allowed. What do you miss most?",
    "Does the house feel different, or is it the evenings that are strange?",
)

# A pregnancy that has ended, or someone who took their own life, is the family of lines the
# gentle pool gets wrong: "that's frustrating" is not a word for either, and nothing here offers
# to fix anything. The only job is to say the loss is real and ask who is around them, which is
# why one pool serves both.
# A thing put down and not found: "i lost my keys", "ive lost my bag". There is nothing to be
# sorry about and nothing to decide later, so the gentle pool is wrong for it: where to look, in
# the order that works. A card or a wallet keeps the answers module's freeze-it line, which is
# better and answers first.
FOUND_IT = (
    "Nice. Where did it turn up? It is usually the boring place after all.",
    "Good. That is the relief - where was it hiding?",
    "Oh good. Was it somewhere you had already looked?",
)

LOST_A_THING = (
    "Retrace your steps in order and check the boring places again - coat pocket, under the car "
    "seat, the last counter you were at. It is almost always in one you have already looked.",
    "Go back to the last place you definitely had it while someone there can still help, and ring "
    "it if it is a phone. Start where you took it out last, not where you think it is.",
    "Check the two places you would swear it is not, slowly. That is where it turns up once the "
    "quick look has already failed.",
)

# Shut out of the house or the car: the way back in, before any advice about searching. A
# person standing in the street does not need "retrace your steps" first.
LOCKED_OUT_LINES = (
    "The way in comes first: the spare, a neighbour who has one, the landlord or letting agent, "
    "then a locksmith who quotes before setting off. The keys can turn up after you are inside.",
    "Get back in before you look for anything: spare key, neighbour, landlord, then a locksmith. "
    "Ask the price on the phone before they come out.",
    "Don't force the door — a spare with a neighbour or family is the cheap way, then the "
    "landlord or a locksmith. Once you are in, one hook by the door stops it happening again.",
)

# A car has its own way in, so the same reading gets its own lines rather than a locksmith.
LOCKED_OUT_OF_THE_CAR = (
    "The car comes first: the spare set at home, then a breakdown service or a locksmith who "
    "does cars — cheaper than the window. The keys can be found once you are moving again.",
    "Don't break the window unless someone is in danger. Spare set, breakdown cover, or a "
    "locksmith who does cars; the keys are a problem for after that.",
)

LOST_A_THING_AGAIN = (
    "Give it one home - a bowl by the door, the same pocket every time - and use it for a week. "
    "Losing the same thing twice is usually the place moving, not the memory.",
    "Pick one spot now and put it there every time you come in, even when you are tired. That is "
    "the whole trick, and it works better than trying to remember harder.",
)

# A habit the person keeps failing at ("i keep forgetting to water the plants", "i keep
# forgetting my keys") is not a fact to file and not a failing memory to explain: the one useful
# thing is a trick that puts the reminder where the job happens. "My husband keeps forgetting" is
# about someone else and stays with the relationship reply, and inside a grief thread "i keep
# forgetting she's gone" is the loss, not a habit (the caller checks the thread first).
# The trick only helps when there is a task or an object to put it next to: "forget to water the
# plants", "forget my keys", "forget the bins". A slip of the tongue is not that ("i keep
# forgetting what i was saying", "i keep forgetting the word"), and neither is a failing memory
# the person is worried about, so both are left to the other readers.
FORGET_A_THING = (r"forget(?:s|ting)?\s+(?:to\s+\w+|my\b|the\b|our\b|his\b|her\b"
                  r"|where\s+(?:i|we)\s+(?:put|left|parked)\b)")

# Every line says the same action - write the date down and set the reminder as you make the
# plan - because a pool may vary the wording, never the advice. Double booking is its own
# problem with its own pool below: "say yes only once it is in the diary" is not advice about a
# birthday.
DATES_KEEP_SLIPPING = (
    "Write it down where you already look - the phone calendar, not a bit of paper - and set the "
    "reminder at the moment you make the plan, a day before and again that morning. The date is "
    "never the thing that slips; the second step is.",
    "One diary, and it has to be the one you check anyway. Set two alarms as you write the date "
    "in: the night before and an hour before, so the remembering is already done.",
    "The reminder has to be made while the plan is still in front of you - a day before and "
    "again that morning. Written down later, it is a note about something that already happened.",
)

DOUBLE_BOOKED = (
    "Say yes to the plan only once it is in the diary, and check that diary before you agree to "
    "the next one. Booking things twice is a diary that lives in two places, so it is one place "
    "that fixes it.",
    "One calendar, and every yes goes into it while the person is still in front of you. The "
    "clash is not the forgetting - it is the second diary that only exists in your head.",
    "Before you say yes, open the day and look at it. Two things at once is what a diary in your "
    "phone and a diary in your head come to in the end.",
)

SECRETS_KEEP_SLIPPING = (
    "Let something else remember them: a password manager fills them in, and you only keep one "
    "strong passphrase in your head. If you would rather not use one, a notebook kept at home and "
    "never in your bag beats reusing the same two.",
    "The remembering is the part to give away - a password manager does the filling in and the "
    "generating, and the browser on your phone already offers one. Then there is nothing to "
    "forget but the one passphrase.",
    "Same password everywhere is what the forgetting pushes people into, and that is the bit "
    "that hurts. A manager, or the one your browser already has, keeps them and types them for "
    "you.",
)

KEEPS_FORGETTING = (
    "Put the reminder where the job happens rather than in your head: whatever you need, right "
    "next to where you use it. What is it that keeps slipping?",
    "Tie it to something you already do every day and it stops needing a memory of its own. "
    "Which one do you keep missing?",
    "Leave the thing itself in the way of the job, so the job does the reminding instead of your "
    "head. What else keeps slipping?",
    "Keep the things that slip in one list you check anyway — your phone notes, a notebook by the "
    "door — so your head is not the place they live. Which one is it?",
    "One reminder in the right place beats trying harder to remember. Which one keeps getting "
    "past you?",
)

SUDDEN_LOSS = (
    "I'm so sorry. That's a real loss, and it deserves to be taken seriously — who have you got "
    "around you this week?",
    "I'm really sorry. Take the time you need, and tell me what would help today.",
    "That's heartbreaking, and I'm sorry. Is there someone you can be with today?",
)

# The first hour of a death, with the words for a child asked for in the same line: "my husband
# died this morning and i have to tell the kids". The condolence on its own asks what would help
# when the person has just said what would help, and the entry that has the words is a procedure
# of six sentences, which is not what the hour is for (sound-gate read the condolence as the worst
# turn in their sample, #quality 81399). So the pool condoles, gives the one thing worth knowing
# when they are ready, and leaves the rest of the entry for the next turn. Every line keeps the
# death plain and the name theirs ("their name"), because a wife or a grandmother is the same line.
THE_FIRST_HOUR_AND_A_CHILD = (
    "Oh, I'm so sorry. Nothing has to be said in the next hour. When it is said, plain and with "
    "their name is enough - that they died and are not coming back - and the questions can come "
    "after.",
    "I'm so sorry. There is no gentle way to say it and there does not have to be: their name, and "
    "what happened, in one or two sentences, and let them ask what they ask. The rest can wait.",
    "Oh, I'm so sorry, and what a thing to be carrying into today. Say it the plain way, with the "
    "name the child already uses, and use the words for the death itself rather than for being "
    "lost or asleep. Nothing else has to be got right today.",
)

# Bleeding in pregnancy is a phone call today, not a chat: the words are the safety lane's kind
# of words, because waiting for a routine appointment is the mistake to rule out.
PREGNANCY_BLEEDING = (
    "Ring your midwife or the early pregnancy unit today — bleeding in pregnancy gets checked "
    "the same day, not at your next appointment. If it's heavy or you're in pain, ring 999.",
    "That needs a midwife today rather than a wait: ring your antenatal ward or the early "
    "pregnancy unit now, and ring 999 if the bleeding is heavy or you have pain.",
)

# Their own body complaining. Never the fact read back, never "that's frustrating" - rest and
# an early night, and a nudge to get it looked at. Left to the modules that know the symptom
# ("my knee is swollen" gets ice and a wrap) and never used for a question.
SYMPTOM = (
    "Sorry to hear it — go easy on yourself today, and see someone if it's not shifting in a "
    "few days.",
    "Ugh, that's rotten. Take it slow today and don't push through it; get it looked at if it "
    "gets worse.",
)

# The one doing the looking after, on a line about someone else's body: "my child has a rash" at
# nine in the evening. The reply is for the carer - is the child drinking, what has changed, who
# to ring today - and never "take it slow today", which is advice for the body that hurts and the
# body here is not the person typing.
CARING = (
    "Poor thing. Keep an eye on how they are in themselves - drinking, eating, perking up - and "
    "ring 111 if that changes. What's it doing now?",
    "Sorry to hear it. Plenty to drink and let them rest; a pharmacist can look at it tomorrow if "
    "it's no better. How long has it been like this?",
    "That's a worry when it's someone you look after. Are they drinking and keeping it down?",
    "Ugh, poor them. What's worrying you most about it?",
    "Being the one looking after them is its own kind of tiring. What have you noticed so far?",
    "Keep them comfortable and watch whether they pick up; if they go downhill or stop drinking, "
    "get them seen the same day. How are they in themselves?",
)

# Somebody else's body troubling them, rather than somebody else being ill: "my wife has a bad
# back", "my dad is 70" then "hes got a bad hip". The carer's illness lines ask whether a child is
# drinking and say to ring 111 if that changes, and a sore hip in a 70-year-old is neither - the
# carer wants to know how they are managing and what would ease it without doing damage.
CARING_FOR_A_BODY = (
    "That's hard when it's someone you look after. Is it slowing them up getting about?",
    "Poor thing. Is it worse at any time of day, or about the same all the time?",
    "Ugh, that's rough on them. Is anything helping at all - heat, a cushion, taking it gently?",
    "Worth asking a pharmacist what pain relief is safe for them, and keeping them moving gently "
    "rather than resting it right up. How long has that been going on for?",
    "That's a worry when it's someone you care about. Is it stopping them sleeping?",
    "Being the one watching them struggle with it is tiring too. What are they finding hardest?",
)

# An animal that is not well is the vet's line, not the carer's: "plenty to drink and let them
# rest" and "ring 111" are advice for a person, and "take it slow today" is advice for the body
# that hurts, which on these lines belongs to a cat. The same wait-and-see honesty, told about an
# animal, and one question the vet will ask.
PET_TROUBLE = (
    "A vet is the one to ask, and a call to the desk is usually free. What's it doing, and when "
    "did it start?",
    "Worth a ring to the vet rather than a wait on it - they would rather hear it early. How "
    "long has this been going on?",
    "Sorry to hear it. Keep them warm and drinking, and ring the vet if it gets worse; is it "
    "eating and drinking as usual?",
    "That's the sort of thing a vet sorts out in one visit. Is it on one side, or all over?",
    "Don't wait on it with an animal - they hide it well, so a vet is the safer call. When did "
    "you first notice it?",
)

# An animal that seems low rather than sore. The vet's trouble pool asks "is it on one side, or
# all over?", which is a question about a lump or a rash, and "Good to hear. What was the best
# bit?" is the one reply that must never come back. A change in an animal's mood is often illness
# or pain first, so the line says that, asks the one thing a vet will ask, and leaves the
# behaviour for after the check.
PET_LOW_REPLY = (
    "A pet that seems low is often ill or in pain rather than sad, and they hide it well. Has "
    "her eating, drinking or hiding changed? A vet check comes first, then the behaviour makes "
    "more sense.",
    "That is worth a vet's eye before a guess: a quiet animal is often sore or unwell. What has "
    "changed most - food, sleep, or wanting company?",
    "Dogs and cats do get low, but a change in mood is a vet question first. Is he still eating "
    "and drinking as usual, and when did you first notice?",
    "Don't wait on a change like this in an animal - pain and illness can look like sadness. Has "
    "anything changed in eating, sleeping or where she hides?",
)

# The same vet-first answer for a named condition, without the shape question: "is it on one
# side, or all over?" is a question about a lump or a rash, and "my dog has diabetes" is neither.
PET_CONDITION_TROUBLE = (
    "A vet is the one to ask, and a call to the desk is usually free. When were they diagnosed, "
    "and are they on anything for it?",
    "Worth a ring to the vet rather than a wait on it - they would rather hear it early. How are "
    "they in themselves - eating, drinking, energy?",
    "Sorry to hear it. Keep them warm and drinking, and ring the vet if it gets worse; is it "
    "eating and drinking as usual?",
    "Don't wait on it with an animal - they hide it well, so a vet is the safer call. When did "
    "you first notice it?",
)

LUMP = (
    "A lump is worth showing to someone rather than watching: ring your GP surgery and say you "
    "have found a lump - that gets you seen quickly, and most lumps turn out to be nothing.",
    "Get it looked at rather than waited on: ring your GP surgery in the morning and say you "
    "have found a lump. They see people quickly for that, and it is usually nothing.",
)

SYMPTOM_COLD = (
    "That sounds miserable. Rest, warm drinks and an early night do more than anything I could "
    "add.",
) + SYMPTOM

# A result the person has not heard yet: an exam, an interview, a scan, an offer. The news is
# still coming, so the reply is about when - not congratulations (it may have gone well or not)
# and not a nod, which reads as if the bot had stopped listening.
PENDING_WHEN = (
    "Then it's out of your hands now — when do you find out?",
    "Fingers crossed then. When will you know?",
    "So it is out of your hands for now. When do you hear back?",
    "When do you find out, then? I'll keep everything crossed.",
)

# The same result, but the line already says when: asking again would be listening badly, so the
# reply takes the waiting itself, which is the hard part.
PENDING_WAITING = (
    "Then it's just the waiting now — the longest bit. Tell me how it lands.",
    "Fair enough, that's out of your hands until then. Let me know how you get on.",
    "Nothing more you can do until then. I'm here when you hear.",
)

# The same doubt, with the result already behind the person: "i might have failed my driving
# test" is a test sat and a guess on top of it. Sympathising would report a failure the person did
# not report, and asking when it lands is not wrong but it misses the guessing, which is the hard
# part of the evening. Both halves get said.
PENDING_DOUBT = (
    "You might be being hard on yourself. When do you find out?",
    "That is the worst bit, the guessing while you wait. When will you know?",
    "Fingers crossed you did better than you fear. When do you hear?",
)

# The answer came back. The waiting is over, so there is nothing to ask about when, and the only
# thing a friend wants next is what was said. A line that names the answer as well ("i heard back
# i got it") is the news itself and gets the congratulations a plain "i got the job" gets.
PENDING_LANDED = (
    "What did they say?",
    "Go on then - what was the answer?",
    "Right, tell me how it went.",
)

# The wait itself, named: the person is saying when the news lands ("i find out next week", "im
# waiting to hear about the job", "i havent heard back yet"). These carry any subject, because
# naming the wait is naming the thing.
# ...and it is told from the person's own side of it. A bare "will know", "still waiting" or
# "went quiet" matches a line about somebody else ("my son will know what to do", "he went quiet
# on me"), and asking a parent when they find out whether their son knows what to do is a
# misreading: the first person, or the thing being waited on, is what makes it a result in the
# post (sure-umbrella, #2302).
# "Waiting on" and "havent heard" also take a person: "im waiting on the plumber" is a visit and
# "i havent heard from my brother in weeks" is a person gone quiet, and neither is a result in the
# post (gray-cypress, #2302). So what follows those two is the result, or the place that gives it
# out - a hospital, a council, an employer - and never a name.
_ISSUER = (
    r"(?:hospital|doctor|gp|surgery|clinic|nhs|dentist|school|college|university|uni|"
    r"employer|company|work|hr|bank|landlord|letting agent|council|dwp|home office|"
    r"immigration|visa office|court|tribunal|insurer|insurance)"
)

# A shared occasion with a price on it that somebody else has set: a hen do, a stag do, a
# bridesmaid's dress, a holiday the friends have picked. The person is not asking for money
# advice and not asking to be talked out of going - they are deciding what to say, and the thing
# a friend says is that the number can be said out loud before it is paid. None of these explains
# anybody's behaviour away or tells them what they feel.
A_COST_SOMEBODY_ASKS = (
    "That is a lot to be asked for. Say the number out loud to them now - most of these bills "
    "grow because nobody says it early.",
    "You can want to be part of it and still not pay that. Say what you can do and let them "
    "decide what happens next.",
    "Ask what the money is actually for before you agree to it: a lot of these bills are one "
    "person's plan that nobody else has costed.",
    "Would you still want to go if it cost less? That is the question under this one, and it is "
    "worth knowing your own answer before you reply.",
)

# Advice somebody else has given them, and the thing advised is still to come: "my mate said i
# should try that new pizza place", "my sister says i would like that show", "i was told to rest".
# These were answered by the day pools - "How was it, overall?", "Good to hear. What was the best
# bit?" - which ask about doing that has not happened yet, and by the intake form, which files it
# back. The reply keeps the plan small and asks nothing of a thing nobody has tried, and the
# second pool names the person where the line did ("Your mate", "The doctor").
# Every line here starts with {who} and takes a verb that agrees with one person or a crowd,
# because the reading hands back "Your mum" and "The lads" both: "the lads at work say i should
# get a bike" was answered "The lads sounds worth a listen". It is the one thing these four have
# to get right, and none of them may be in A_SUGGESTED: the same line with and without a name
# reads as a template.
A_SUGGESTED_BY_SOMEONE = (
    "{who} may be onto something. What's the first step you could do this week?",
    "{who} will know better than me. What's stopping you starting?",
    "{who} had a reason for saying it. Try the smallest version and see how it sits.",
    "{who} thought it worth saying. Give it a proper try before you decide.",
)
A_SUGGESTED = (
    "Worth a go. What's the first step you could do this week?",
    "Sounds like good advice. What's stopping you?",
    "Then try it once and see. Nothing has to be decided today.",
    "Start with the smallest version of it and see how it sits.",
)

NEUTRAL = (
    "Got it. Is there anything you'd like a hand with?",
    "Thanks for telling me — I'm here if you want to dig into any of that.",
    "I'm listening — say more if it helps.",
)

# Two of those three say the bot has taken something in ("Got it. Is there anything you'd like a
# hand with?", "Thanks for telling me - I'm here if you want to dig into any of that"). A chat's
# first line is the one turn where nothing has been said yet, so the receipt claims a turn that
# did not happen: thirty of the deck's nine hundred first lines got one of the two. The third
# ("I'm listening - say more if it helps") claims nothing and is right on a first line, which is
# why this is a list of the frames and not of the pool.
# The two are read whole: a receipt is empty only when it is all there is. "Got it - your daughter
# is 7." puts the person's own figure on the page, and that is the one thing a first line about an
# age needs, so the frame is matched with nothing after it and a receipt that carries something of
# theirs is left alone.
A_RECEIPT_OF_NOTHING = re.compile(
    r"^\s*(?:got it[.!]?\s*(?:is there anything you'?d like a hand with\??)?"
    r"|thanks for telling me\s*[\u2014\u2013-]?\s*i'?m here if you(?:'d| would)? ?(?:want|like) to "
    r"dig into any of that)\s*[.!]?\s*$", re.I)

# What a first line gets instead, once every card, entry and reading that could answer it has had
# its turn. A first line is the one turn where the bot has been told nothing, so the opener makes
# no claim about the line: it asks for the thing an answer would start from. A line that claims
# something about what was heard ("That sounds like a lot - tell me what's going on.") is not one
# of these, because on a first line it invents the thing it claims to have heard: it was the pick
# for `a good chippy near me`, and nobody asking for a chip shop has had a lot.
COLD_OPEN = (
    "Go on - what's been happening?",
    "What do you need? I'll take it from there.",
    "What would be most useful to sort out?",
)

# A decline that comes with a reason on the body is not a diary being rearranged: "i might be
# pregnant and i cant come", "my back is bad and i cant come", "i feel awful and i cant come".
# Each of those has a health answer of its own, and this file's plan pool answers with "Do you
# want to rearrange it, or let this one go?", which asks somebody in pain to reorganise their
# evening. The reading is the one the worry pools already use (`_worry_is_about_the_body`), plus
# the words a person says when the body is the reason and the things a pregnancy is said with.
BODY_SAYS_WHY = frozenset(("awful", "terrible", "dreadful", "rotten", "lousy", "poorly",
                           "unwell", "ill", "sick", "fluey", "achy", "shaky", "faint",
                           "nauseous", "knackered", "exhausted", "flu", "fever", "cold",
                           "migraine", "bug", "covid"))

# Somebody else dropping it - the sitter, the plumber, a friend, a father who cannot get there -
# is not the person declining: their plan is knocked sideways and the reply is about that, in a
# register that fits a delayed boiler and a wedding the same way.
PLAN_KNOCKED = (
    "Ah, that's a pain. Does it put the whole thing off?",
    "That's a nuisance. Can it happen another time?",
    "Sorry to hear it. Does it change what you were going to do?",
    "That throws it up in the air a bit. What's the plan now?",
)

DECLINED_PLAN = (
    "No trouble at all - these things happen. If you want a hand working out what to say to "
    "whoever is expecting you, I can help with that.",
    "That's alright. Do you want to rearrange it, or let this one go?",
    "Fair enough, no need to explain. Say the word if you want a hand putting it in a message.",
    "No worries. If they are going to ask why, it helps to have one sentence ready - want to work "
    "one out together?",
)

# The same plan dropped in a week where somebody died, or in the days before, is not a diary
# clash: "my mum is dying" then "i cant come" was answered "No trouble at all - these things
# happen", which is a breezy line for a person who has just said the worst thing in their life.
# The plan still gets answered as a plan, in the register the chat is in.
DECLINED_PLAN_GENTLE = (
    "Of course - nobody would expect you to. Look after yourself today.",
    "That's understood, and no explanation needed. Be gentle with yourself.",
    "Of course not. Put yourself first just now, and I'm here if you want to talk.",
    "Nobody would think twice about that one. Take care of yourself today.",
)

# A talk with a named person is opened, not described: one true sentence, and the rest comes once
# they are talking. No question at the end, because the person has just said they have no words.
NO_WORDS_SOMEONE = (
    "Start with one true sentence and stop: \"I have been thinking about what you told me.\" "
    "The rest comes once you are talking.",
    "You do not need the right words, only a true one - say you are glad they told you, then let "
    "them do the talking.",
    "Keep it small and mean it: name the thing in one line, then ask how they are today. That is "
    "enough to open it.",
)

# Nobody is named, so the words are stuck in the conversation here rather than with a person.
NO_WORDS_STUCK = (
    "Then start anywhere - the first bit that comes to mind is usually the right one.",
    "No rush. Say the part that is loudest in your head and we can sort the rest of it.",
    "That is alright. Say it badly if you have to; the words come easier once the first one is out.",
)

NO_WORDS_AT_THE_CARE = (
    "Lead with the trouble, not the history: one sentence on what is wrong, then how long it has "
    "been going on and what makes it worse. They get to the rest faster that way.",
    "Say the thing you are worried about first - \"it has been hurting for three weeks\" - then "
    "what you have noticed since. That is what they need to sort it.",
    "Put the main worry in the first sentence and let them ask the rest. Take the dates and what "
    "you have already tried with you.",
)

NO_WORDS_ASKING = (
    "Say what you want out of it first and stop: \"I would like to talk about the shifts.\" The "
    "detail can come after - the ask is the sentence that has to be said.",
    "Decide the one thing you are asking for, put it in the first line, then let them answer. "
    "Everything else is easier once they know what you want.",
    "Lead with the ask, not the story: one sentence about what you want, then the reason. Say it "
    "plainly and you will not need to rehearse it.",
)

# "take the rubbish out", "put the kettle on", "book me a table for two on friday": the person is
# telling the bot to do something in the world. The bot cannot - no hands, no phone, nothing
# outside the chat - and the neutral pool answered as if the job had been done ("Thanks for
# telling me - I'm here if you want to dig into any of that"), which is the answer that costs the
# most trust: a person who thinks the bins are out has been told nothing at all. So the limit is
# said plainly and the half the bot can do is offered. A task that is a thing to work out
# ("pay the gas bill", "sort out my car insurance", "make me a shopping list") keeps the advice
# those entries give, because those lines are about how to do it, not about who does it.
ACTS_FOR_ME = (
    "That's a job in the world and I can't reach one - no hands, no phone, nothing outside this "
    "chat. What I can do is the thinking: the steps in order, or what to say when you ring. Say "
    "which bit you're stuck on.",
    "I can't do that one myself, sorry - I'm words on a screen. Hand me the part that needs "
    "working out instead: the list, the order to do things in, or the call you're dreading.",
    "No hands on this end, so the job itself can't be mine. What I'm good for is the plan behind "
    "it - say what's making it awkward and I'll help with that.",
    "Nothing can be fetched, sent or signed from this end - no browser, no inbox, no hands. Name "
    "the thing and I'll do the part that lives in words: the method, the wording, or the "
    "questions for whoever can.",
)

# An invitation is a person asking for company: "do you fancy a walk", "want to go for a walk",
# "shall we have a brew", "you up for a walk", "fancy a chat", "come for a walk", "walk with me".
# Nothing about the world can answer one, and it is not a statement to file away, so it got the
# search hedge ("that's beyond what I know well, sorry"), the neutral nod ("Got it. Is there
# anything you'd like a hand with?") or the floor ("I'm listening - say more if it helps"). None
# of those is what a friend says to an invitation. The bot cannot come - it is words on a screen,
# and it says so in a few words - and then does the part it can: takes an interest in the walk, the
# brew, the film.
INVITED = (
    "I'd come if I could - I'm only words on a screen. What's the plan?",
    "Wish I could be there. Who are you going with?",
    "Sounds a good idea - tell me how it goes.",
    "Lovely idea. I'd be there in a shot if I had legs.",
)

# An invitation to talk is the one the bot can take up: "fancy a chat" is not a walk it has to
# turn down, and "wish I could be there" answers it as if it were.
INVITED_TO_TALK = (
    "Go on then - what's on your mind?",
    "Always. What do you want to talk about?",
    "I'm here for it. What's up?",
)

# An ask about a doing is what is left after these: "to", the article, the preposition that turns
# a thing into an occasion ("out for a walk", "on a walk").
INVITE_FILLER = frozenset("to and a an the some out on for round along up with me us down over it"
                          .split())

# What people do together, and what an invitation to do it names. A tail with none of these is a
# question about a thing rather than an ask for company ("want a receipt", "shall we call the
# doctor", "fancy that"), and the pool would answer it with a warm line about a walk that was
# never mentioned, so those lines keep whatever the composer said before.
INVITE_ACTIVITY = frozenset("""
walk stroll wander hike ramble coffee tea brew cuppa pint drink drinks beer wine lunch dinner
breakfast brunch bite snack takeaway curry chinese pizza kebab chips film movie picture cinema
show theatre gig concert game quiz run jog swim cycle bike ride picnic shopping shop market party
dance paddle drive pub cafe match footie football bowling karaoke barbecue bbq beach park garden
museum join
""".split())

# A pronoun on its own is a question about the bot's taste ("do you fancy her"), not an invitation
# to do something together.
INVITE_PRONOUN = frozenset("her him them you me us it themself".split())

# Nothing here is a pool for a line about harm: the safety modules have their own replies, and a
# cheerful "count me in" is the one line that must never reach these words.
INVITE_NEVER = frozenset("die dies died dying dead death kill killed myself suicide overdose "
                         "harm hurt hurting blood bleed bleeding hospital ambulance 999 111 "
                         "funeral cancer".split())

# A short line that only narrows the answer above is not a new subject and not a thing to nod at.
# "we fancy a few days away in october" was answered with four destinations, and "somewhere thats
# not too far" then got "Got it. Is there anything you'd like a hand with?" - the reply a person
# gives when they have stopped listening. The same default answered "cheaper" after the same
# answer, "under 20 minutes" after a cooking answer with the line said back ("Got it - under 20
# minutes"), and "not too far" after a day out with "Thanks for telling me - I'm here if you want
# to dig into any of that". The line names no subject, so nothing here that names one could take
# it; what it does is choose a direction to cut in. So the constraint is read on one axis, and the
# reply goes back to the answer that is still on the screen ("those") and asks the one thing that
# pins the cut, which is what a friend does when you say "somewhere not too far": they say nearer
# than what.
ONLY_FRONT = (r"^(?:(?:and|but|so|ok|okay|well|maybe|just|also|oh|no|yes|yeah|hmm|actually|"
              r"honestly)[\s,]+)*")

# Each line says which way to cut and asks the one thing that pins it. "those" is the answer that
# is still on the screen, so the reply reads as the next step in the same conversation.
CUT_FOR = {
    "far": (
        "Then cut those for distance: how long a journey is still worth it?",
        "Nearer, then. How far are you happy to travel?",
        "Then keep to the ones you can get to easily. How long a trip is fine?",
    ),
    "price": (
        "Then cut those for price: what's the most you want to spend?",
        "Cheaper, then. What's your limit?",
        "Then let's keep to a budget. What's the ceiling?",
    ),
    "time": (
        "Then fit those to the time you have: how long have you got?",
        "Then the short version. How many minutes have you got?",
        "Then let's fit it to the time you have. How long is that?",
    ),
    "effort": (
        "Then take the easiest of those. How much are you up for?",
        "Then nothing fiddly. How little effort do you want to put in?",
        "Then the simplest of those. How much work is too much?",
    ),
    "size": (
        "Then cut those for size: how much room have you got?",
        "Smaller, then. What are the measurements you're working with?",
        "Then let's get the size right. What has it got to fit into?",
    ),
}

BOUND_FOR = {
    "far": (
        "Then within {bound}: which of those is close enough?",
        "Then {bound} it is. Which of those is a journey you'd make?",
    ),
    "price": (
        "Then keep to {bound}: which of those comes in under that?",
        "Then {bound} is the ceiling. Which of those fits inside it?",
    ),
    "time": (
        "Then {bound} it is. Which of those fits inside it?",
        "Then let's fit it to {bound}. Which of those fits?",
    ),
    "effort": (
        "Then {bound} of effort. Which of those is the least work?",
        "Then nothing harder than {bound}: which of those suits?",
    ),
    "size": (
        "Then {bound} to work with. Which of those fits?",
        "Then {bound} it is. Which of those suits the space?",
    ),
}

NARROW_WORDS = 7

NARROW_ANSWERED = frozenset(("answers", "memory_store"))

NARROW_SUBSTANCE = 14

# One duration in a piece of advice is not a choice: "i cant sleep" says "awake for more than 20
# minutes" and the person's "quicker" is not asking the bot to fit a sleep routine to their evening.
# Two or more is a set of things in front of them with their own times, which is what "what should i
# cook tonight" gives ("tuna pasta in 15, a frittata in 20, or a salmon traybake if you have 30
# minutes").
AXIS_MIN = {"time": 2}

# A good time had by a group or by an event ("everyone there was lovely", "we had a great time at
# the wedding") is the good half of a chat, and nothing in the app can add a fact to it, so the
# neutral pool files it away - "Got it, is there anything you'd like a hand with" is what a person
# says when they were not listening. There is no advice to give, so this pool says the warm thing
# and asks for the best of it, which is what a friend does with a good time they were not there for.
# It comes before the congratulations, because a win is the person's own ("Good for you!") and a
# party they went to is not.
A_GOOD_TIME = (
    "That sounds like a good time - what was the best of it?",
    "Lovely. What made it as good as that?",
    "Glad it went well. Tell me the best bit.",
)

# A good day in a bad week is a different line from a good day on its own. "my mum died last
# week" then "i had a good day today" was answered "Lovely. What made it as good as that?", which
# is warm and amnesiac: it answers as if the thread were an ordinary one, and a friend would not
# forget the week it sits in. Both halves are in the reply, in that order, and it asks one small
# thing so the person can keep going either way.
A_GOOD_TIME_IN_A_CARE_THREAD = (
    "That's good to hear, and a good day in a week like this one counts for more than it "
    "sounds. What made it a good one?",
    "I'm glad. After what you have been carrying, a day like that is worth having - what was the "
    "best of it?",
    "Good - and it does not undo the rest of it, which I have not forgotten. What made today "
    "different?",
    "That's something, in a week like this. Tell me what was good about it and I will keep it "
    "with the rest.",
)

# Something funny said in the chat is the good half of a chat in the same way a good time is,
# and nothing can be added to it. The neutral pool answered it as if the person had reported a
# problem ("Thanks for telling me - I'm here if you want to dig into any of that") and the echo
# said the line back with the smile taken out ("Noted: your nan made you laugh so much"). A
# friend laughs back and asks for the story, so the laugh gets its own three lines.
A_LAUGH = (
    "Ha - what set it off?",
    "Ha, good. Tell me the bit that got you.",
    "That's the best kind of day. What happened?",
    "Ha - that good? Tell me the best bit.",
)

# "ugh", "same old", "could be worse" are the whole answer to "how are you?" when the answer is
# flat. They are not a nod ("Got it. Is there anything you'd like a hand with?" reads like the
# person said nothing), not a win ("Great - shout if you need anything else" answers a flat line
# as if it were good news), and not a question for a search ("could be worse" was met with "I'd
# rather not guess"). One warm line names the flatness and asks one small thing.
# Only a line that is nothing but this comes here: "same old story" and "could be worse i
# suppose" name something else, and "not bad" is the good side.
FLAT_LEAD = r"(?:(?:yeah|yep|yes|ok|okay|and|but|oh|ah|well|honestly|tbh|just|so|still|really|" \
            r"very|it|its|is|was|been|a|bit|pretty|kind of|sort of)\s+)*"

FLAT_CORE = (r"(?:ugh+|urgh+|blah+|bleh+|bleurgh+|blech+|sigh|fr|ngl|pfff+"
             r"|same old(?: same old)?|same as (?:ever|always)"
             r"|could be worse|cant complain|up and down|so so|bit of a rubbish|bit rubbish)")

# "Tell me about it." "You and me both." An idiom of agreement whose words look like a request:
# the person has just agreed with something, and the search hedge ("that's beyond what I know
# well") answers as if they had asked for a briefing. `understood["agreement"]` names the idiom,
# so this pool needs no match of its own - it is here only for the wording, and it agrees back
# and leaves the floor open rather than asking a question of someone who just said "quite".
# "im skint till friday", "a bit short this month". The reading says the money has run out, and
# the reply that fits is about the tight week: "I'm listening - say more if it helps" and "Thanks
# for telling me" both put the work back on someone who has just said the worst bit.
TIGHT_MONEY = (
    "Broke till payday is its own kind of week. What's the money going on - food, or something "
    "that can wait?",
    "Tight month, then. What's the first thing that has to be paid?",
    "Right before payday is the hardest bit of the month. What have you got in the cupboard?",
    "That's a long week when the money is done. What would help most: cheap meals, or a bill to "
    "put off?",
    "Skint weeks take planning, not willpower. What's left and how long till the money comes?",
)

# The same week, one turn on. The pool above ends by asking what is left and how long till the
# money comes; a bare "go on", "and?", "tell me more" a moment later is the person keeping the
# thread going rather than answering the question, and the pools that answer a report on advice
# took it and said "Thanks for telling me - I'm here if you want to dig into any of that", which is
# the bot signing off in the middle of the conversation. So a continuation after the pool's own
# line is answered inside the same subject, and it asks again for the one thing it needs.
TIGHT_MONEY_MORE = (
    "I'm not going anywhere. What's in there roughly, and when does the money land?",
    "Give me the two numbers and I'll work with them: what's there, and what has to come out "
    "before the money comes in?",
    "Then let's keep at it. What is the next thing that has to be paid?",
    "I can work with rough. What's roughly there, and which bill will not wait?",
)

AGREEMENT = (
    "You know it. What's today been like for you?",
    "Ha - you're not wrong. What's going on with you?",
    "Same here. Tell me how it's been.",
    "Right? What's the worst of it today?",
    "You're preaching to the converted. What's it been like?",
)

FLAT = (
    "Ugh. What's the day doing to you?",
    "One of those days? What's up?",
    "Flat one, then. What's going on?",
    "Same as ever, then. Anything you'd like to change?",
    "Fair enough. What would make it better?",
)

# A line that is nothing but a reaction - "ouch", "seriously?", "yikes", "phew", "oops" - is the
# person answering what was just said, and it has no subject to look up and no question in it. The
# pools below answered it as if it were a report or a query: "ouch" got "Thanks for telling me -
# I'm here if you want to dig into any of that", "seriously?" and "are you serious" the honest
# search shrug, "no way" "Great - shout if you need anything else" (a win), "oops" the intake
# form and "phew" the same listening line as "ouch". What the person wants is the reaction back
# and then to be asked what happened, which is what a friend says to a reaction they were not
# there for. Each pool is keyed to what the reaction means, and none of them claims a line that
# says anything else: "ouch my knee" is a symptom and keeps its own answer.
REACTION_LEAD = r"(?:(?:oh|ah|ooh|ooh|aw|aww|aah|my|good|god|jesus|christ|jeez|well|just|so|and|"

REACTION_OUCH = (
    "Ouch. What happened?",
    "Yikes. That sounds rough - what happened?",
    "Ouch is right. Go on.",
    "That's rough. What happened?",
)

REACTION_DISBELIEF = (
    "Go on - what happened?",
    "Really? Tell me what happened.",
    "No kidding. What's going on?",
    "Straight up? Tell me more.",
)

REACTION_RELIEF = (
    "That sounds like a relief. What was it in the end?",
    "Phew is right. What was going on?",
    "Thank god for that. What happened?",
)

REACTION_MISHAP = (
    "Oops. What did you do?",
    "Whoops. What happened?",
    "Oh dear. What was it?",
)

# "what?" on its own is the person asking for it again - or saying they cannot believe it - and the
# bot cannot show the same line twice, so it says it another way and asks which bit was unclear.
# A search hedge ("that's beyond what I know well") is the one thing it cannot be.
REACTION_OUCH_SAID = (
    "That's rough.",
    "Ugh. Sorry - that is a rough one.",
    "Ouch. Sorry, that sounds rough.",
)

REACTION_MISHAP_SAID = (
    "Ugh, what a pain.",
    "Oh no. That is a pain when it happens.",
    "Annoying one, that.",
)

REACTION_RELIEF_SAID = (
    "That is a relief.",
    "Good. Glad that one is over.",
    "Phew. That is the end of it, then.",
)

REACTION_DISBELIEF_SAID = (
    "That is a lot. No wonder you are taken aback.",
    "Really. That is something.",
    "Straight up. That is a lot to take in.",
)

# Inside a bereavement or a crisis the reaction is heard, not asked about - and the flat pool's
# answer ("I'm listening - say more if it helps") is the stock line STYLE.md names as a failure:
# it would fit any message. So the reaction gets a line of its own, and it asks for nothing.
REACTIONS_CARE = (
    "I'm sorry. There is nothing you have to say about it here.",
    "That is a heavy thing to be carrying. I'm here.",
    "No words needed for it. I'm listening, for as long as you want.",
)

# "what?" as the very first thing said has no last answer to put another way, so it is the person
# asking what the bot can do: "I'll put it another way - what bit was unclear?" answers nothing.
REACTION_REPEAT_FIRST = (
    "What can I help with?",
    "Sorry - what did you want to ask?",
    "Not sure what you mean yet. Say a bit more?",
)

REACTION_REPEAT = (
    "I'll put it another way - what bit was unclear?",
    "Tell me which part and I'll say it differently.",
    "Say what you're after and I'll come at it from another side.",
)

# The reaction as a whole line: the small words people put in front of it, then reaction words and
# the plumbing between them, and nothing else. Two stages, because the grammar has to be loose
# enough for "ouch that really sucks" and the reading has to be exact: a line is only a reaction
# when one of the signatures below is in it, so "that is good" and "no go" stay ordinary lines.
REACTION_WORD = (
    r"(?:ouch(?:ie)?s?|ow+|yikes|eek|oof|yowch|sucks|brutal|phew|finally|oops|whoops|dear|dammit|"
    r"damn|bugger|crap|shoot|huh|eh|pardon|what|seriously|serious|joking|kidding|real|way|"
    r"chance|surely|really|honestly|wtf|the|hell|heck|fuck|get|out|come|on|wow+|woah|whoa|omg|"
    r"what on earth|why on earth|how on earth|what in the world|why in the world|"
    r"devil|blazes|dickens|damn|fucking|going|goes|happen|happens|happened|happening|"
    r"you|youre|are|joke|for|"
    r"blimey|crikey|thank|good|god|heavens|christ|my|word|that|this|it|is|so|just|awful|"
    r"terrible|horrible|rough|much|sick|the|no)")

# The same reaction when the person has already said what happened: "i lost my job yesterday" /
# "yikes" is not a story the bot has yet to hear, so asking "what happened?" makes them type it
# twice. Each pool keeps its meaning and drops the question.
REACTIONS_SAID = {
    REACTION_OUCH: REACTION_OUCH_SAID,
    REACTION_MISHAP: REACTION_MISHAP_SAID,
    REACTION_RELIEF: REACTION_RELIEF_SAID,
    REACTION_DISBELIEF: REACTION_DISBELIEF_SAID,
}

# A verdict on the thing before it: "what a nightmare", "what a mess", "what a day". It names
# nothing to look up and asks nothing - it is the person agreeing with the room, and a friend says
# it back and asks what happened. The reaction grammar below is built from reaction words and "a"
# is not one, so every one of these fell past it: "what a nightmare" and "what a mess" reached the
# search shrug, and bare "nightmare" after a job loss reached the advice for dreams. The nouns are
# closed lists because the shape is otherwise as common in praise ("what a lovely day").
VERDICT_BAD = ("nightmare|mess|disaster|shambles|palaver|faff|farce|letdown|let down|"
               "waste of time|waste|carry on|rip off|rip-off|kettle of fish|pain|state|sham|"
               "joke|performance|shower|ordeal")

_VERDICT_LEAD = (r"(?:(?:oh|god|jesus|christ|well|and|but|so|ha|haha|wow|bloody|right|honestly|"
                 r"just|man|mate|ugh|jeez|blimey)\W+)*")

_VERDICT_DET = (r"(?:what a|what an|such a|a right|a proper|a real|bit of a)\s+"
                r"(?:(?:absolute|total|complete|right|proper|bloody|real|right old)\s+)?")

# A verdict on what was just said is the next lightest line after a reaction: "thats annoying",
# "what a hassle", "typical", "just my luck". The person is not asking anything and not telling
# anything new - they are saying how the news sits with them, and the answer is the verdict back
# and one question about it. It was reaching the neutral nod ("Got it. Is there anything you'd
# like a hand with?") and, for "what a hassle", the search hedge, because nothing in the line
# names a subject to answer.
# The verdict word is the whole test, and the line has to be about it, not about a person: "im so
# annoyed" is a feeling with its own pool, and "the traffic was annoying" is a report, so only
# the demonstrative shapes ("thats ...", "how annoying") and the bare sayings are claimed here.
VERDICT_WORD = (
    r"(?:annoying|annoyin|a\s+pain|such\s+a\s+pain|a\s+nightmare|a\s+hassle|a\s+headache|"
    r"a\s+mess|a\s+joke|a\s+shame|such\s+a\s+shame|a\s+letdown|frustrating|"
    r"infuriating|infuriating|maddening|typical|sod'?s\s+law|murphys?\s+law|typical|"
    r"a\s+nightmare)")

VERDICT_ANNOY = (
    "Annoying, that. Is it sorted, or still hanging over you?",
    "Yeah, that's a pain. What are you going to do about it?",
    "That is annoying. Can you sort it, or is it out of your hands?",
    "Annoying. Is it a quick fix or a whole thing?",
)

# "Typical, that. How long has it been going on?" was in this pool and is gone: it reads as a
# symptom question, and it landed after "our move got pushed back a fortnight" (honey-pencil on
# #5479). The other three ask about the news and nothing else.
VERDICT_LUCK = (
    "Just your luck. What happens now?",
    "That's the way it goes sometimes. Is there anything you can do about it?",
    "Of course it did. What's the plan?",
)

# A verdict on a state of the person - a body that hurts, sleep that will not come - is not a
# verdict on a thing to be fixed. "Annoying. Is it a quick fix or a whole thing?" asks a fix
# question about insomnia, where the answer is about how it is going (sunny-ocelot on #5479).
VERDICT_ROUGH = (
    "That's rough. Is it easing at all, or much the same?",
    "Poor you. Has it been like that long?",
    "That wears you down. How are you managing with it?",
    "That's a hard one to carry around. Is anything helping?",
)

# A death said a turn ago is not a heavy verdict with a question in it: "my dog died" then "what a
# nightmare" was answered "That is a lot to hold on your own. Is there anyone you can say it to?",
# and the line a person who has just said it wants has nothing to answer (sunny-ocelot on #5479).
VERDICT_NUMB = (
    "I'm sorry. There are no words that help with that, and I'm not going anywhere.",
    "I'm so sorry. Nothing needs saying right now - I'm here when you want to talk.",
    "That is the worst kind of news. Take today as slowly as it comes.",
    "I'm sorry. Say as little or as much as you like.",
)

# A verdict is a light turn, and every line in this pool has to stay light: the news it lands on
# is as often a laptop that died as a person, and "Gutted for you. Do you want to talk it through?"
# is a size too big for a laptop (happy-beaver on #5479). "Tell me what happened." asked a
# bereaved person to say the death again. The state of play is what a friend asks either way.
VERDICT_SHAME = (
    "That's a shame. Is there any way to put it right?",
    "Shame, that. What happens now?",
    "That's a shame, that. Is it too late to sort out?",
    "Sorry to hear it. Anything left to do about it?",
)

# A verdict on a heavy turn needs a heavier pool. "i miss my mum" then "what a shame" was
# answered "That's a shame, that. Is it too late to sort out?" - a fix-question asked of a
# bereavement, and the same fault as "i cant stop crying" then "what a nightmare" ("Annoying. Is
# it a quick fix or a whole thing?"). The light pools below ask what can be done about the news;
# on a grief line nothing can, so the answer is the sympathy and a question about the person.
VERDICT_HEAVY = (
    "That's a heavy thing to be carrying. Do you want to say more about it?",
    "That sounds like it has been sitting with you a while. What is it like today?",
    "I'm sorry. That is the sort of thing that comes back in waves - how are you holding up?",
    # A fourth line used to stand here: "That is a lot to hold on your own. Is there anyone you
    # can say it to?" It presumes the person is alone with it, and a friend who says it has not
    # been told that - the heavy turn is one of the worst weeks of somebody's life, not evidence
    # about who is beside them (reported on #routing 79374).
    "I'm sorry. That one takes the time it takes - say as much of it as you want to.",
)

# Heavy news is not all the same weight. A queue nobody can bring forward and a job gone are news
# with no repair in it, so the light pools' fix question is wrong - but they are not a person
# lost either, and the pool above asks a bereaved person's question: "got to wait six weeks for
# the appointment" then "what a nightmare" was answered "That is a lot to hold on your own. Is
# there anyone you can say it to?" on main `c403b2bf` (measured, `compare --seed 9103`, avt-08).
# The register that fits both is sympathy and one question about the wait itself, which is what a
# friend asks over a queued operation or a redundancy.
VERDICT_QUEUE = (
    "That's a long wait. Have they said anything about bringing it forward?",
    "Waiting is the worst part of it. What are you doing with the time?",
    "That drags, that. Is there anyone chasing it for you?",
    "That's a slog of a wait. Is there anything you can do in the meantime?",
)

VERDICT_SETBACK = (
    "That's a blow. What are you doing about it?",
    "Sorry to hear it. Is there anything lined up yet?",
    "That's rough. What happens now, do you know?",
    "Gutted for you. What's the plan from here?",
)

# A verdict as the very first line of a chat has nothing to point back at, so every pool above it
# stands down (`_verdict_pool`) and the person got the intake form back: "thats tough going" and
# "thats annoying" were answered "Got it. Is there anything you'd like a hand with?" on the first
# turn, which files a reaction as a fact and asks for nothing (tawny-donkey's census, #routing
# 82965). The subject of a verdict with no answer behind it is the person's own day, so the reply
# is the one a friend gives to the verdict alone: ask what happened.
VERDICT_FIRST = (
    "Go on - what happened?",
    "What's made it that way?",
    "What happened, then?",
    "Right. What has gone on?",
)

# An apology for having stepped away ("sorry, i went to get the kids", "sorry i disappeared for a
# bit") is the person saying the thread paused, not that anything is wrong: "Got it, is there
# anything you'd like a hand with" reads as if they had reported a fault. This pool takes the
# apology away and opens the floor, which is the whole content of the line.
#
# It opens the floor rather than picking a thread back up, because the same apology is often the
# *first* line of a chat ("sorry ive been quiet, its been a rough week" opens a real one): "Where
# were we?" and "What were you saying?" there ask the person to go back to a conversation that
# never happened. A line in this pool has to work as the first reply of a chat, so it may not
# refer to a thread at all - the same rule the composer's other shared pools follow.
CAME_BACK = (
    "No need to say sorry - I'm here. What's on your mind?",
    "That's fine, no harm done. What would you like a hand with?",
    "No bother at all - go on.",
)
# The same apology in a thread the bot has just answered with first aid. "No bother at all - go
# on" is a breezy hand-back, and it went to somebody who had just been told to keep pressing on a
# wound ("i cut my hand and it wont stop bleeding" then "sorry i went quiet"). The pause is still
# the whole content of the line, so it is still a go-ahead - one that keeps the thread's care.
PAUSE_IN_A_SAFETY_THREAD = (
    "Please don't worry about the gap - tell me how it is now, and what you've done for it.",
    "No need for that. Say how it looks now and I'll stay with it.",
    "That's alright. How is it now, and have you been able to keep the pressure on?",
)

# A line that only points back at the conversation - "as i was saying", "where was i", "sorry, i
# got cut off", "so anyway" - carries nothing of its own, and the account-of-the-day pool answered
# it as though it were news: "as i was saying" -> "Sounds alright. Anything good in it?", and the
# search shrug took "where was i". The person is picking the thread back up, which is the whole
# content of the line, so the pool says go on rather than reopening it.
#
# Every line here has to work as the FIRST reply of a chat, where there is no thread to pick back
# up: "go on" is true either way, and "where were we" is the one thing it must not say (the same
# constraint CAME_BACK above is worded by).
RETURNED_TO_IT = (
    "Go on - I'm listening.",
    "Right, go on.",
    "Go on then, I'm with you.",
    "Carry on - I'm all ears.",
)

# The same line as the first thing said in a chat, where the go-ahead would be a reply to a turn
# that never happened. Nothing is picked back up; the chat is empty and the person is told so, in
# a way that says what to type next.
RETURNED_TO_IT_FIRST = (
    "There's nothing earlier in this chat - what's on your mind?",
    "Nothing to catch up on yet - what would you like to talk about?",
)

# What the bot says to the first line of a chat when the line it would otherwise give answers a
# turn that never happened. These name no earlier turn, because there is none: they say the chat is
# at its start and ask for the thing itself. Read by `bot/compose/fallback_chain.py::reply_for`
# through the same one check every other reply about the conversation uses
# (`bot/memory/history.py::an_earlier_turn`).
NOTHING_SAID_YET = (
    "Nothing said yet, so this is where we start - what's on your mind?",
    "We're at the start of this chat: tell me the thing itself and I'll take it from there.",
    "This is your first line, so there's nothing earlier for me to go back to - what is it?",
)

# The same line with the thing said after it ("as i was saying about the car"): the person has
# not said the thing yet, so the reply asks about it instead of guessing at it, and "go on" on
# its own leaves them to work out what was heard. As above, this has to work as a first reply:
# it names no turn, it names what the person just said.
RETURNED_TO_A_THING = (
    "Go on - what about {thing}?",
    "Right, go on. What about {thing}?",
)

# The composer's name for this kind of line, read by bot/modules/arbiter.py: the apology is the
# whole content of the line, so no topic entry may take it back on a word of it. "sorry for not
# replying" was drafted into an email ("say the ask in the first line") because the answers
# module read "reply" as a request to write one.
PAUSE = "pause"

# An apology for taking the bot's time ("sorry to bother you", "sorry to keep asking", "sorry to
# be a pain", "sorry for the essay") is the person being polite about asking, and the stock
# lines answered it with "I'm listening - say more if it helps", which is what you say to someone
# who has not said anything yet. The apology is the whole content of the line, so the pool takes
# it away and opens the floor, the way CAME_BACK does for an apology about having stepped away.
# A line with one word of its own in it is not this: "sorry to bother you but the boiler is
# broken" is the boiler's, and MANNERS_ONLY is what stops it here.
SORRY_FOR_ASKING = (
    "No need to apologise - asking is what I'm here for.",
    "You're not bothering me at all. What's on your mind?",
    "No bother - ask away.",
    "Nothing to be sorry about. Go on.",
)

# An apology with nothing after it ("sorry", "so sorry", "my bad", "my fault", "apologies") is
# manners about something the person did, not a report of it - and the neutral pool answered it by
# thanking them for having spoken: "Thanks for telling me - I'm here if you want to dig into any of
# that", or "I'm listening - say more if it helps" to someone whose whole line was "sorry".
# SORRY_FOR_ASKING is the same manners when the apology is about asking; this is the apology on its
# own, and the reply is the one a friend gives: that there is nothing to be sorry for.
SORRY_ON_ITS_OWN = (
    "Nothing to be sorry about.",
    "No need to apologise - no harm done.",
    "That's alright. Nothing to say sorry for.",
    "No worries at all.",
)
# The closed phrases an apology can be made of. "sorry what" (they did not hear the bot) and "sorry
# wrong chat" (they meant to text someone else) are not this, and neither is "sorry for the rant",
# which is a person checking they have not gone on too long.
A_SORRY_ON_ITS_OWN = re.compile(
    r"^(?:(?:oh|ok|okay|right|so|well|hey|hi|and|but|no)\s+)*"
    r"(?:(?:that\s*s|thats|that\s+is|it\s*s|its)\s+)?"
    r"(?:(?:it\s+)?(?:was|is)\s+)?"
    r"(?:my\s+)?"
    r"(?:(?:i\s*m|im|i\s+am)\s+)?"
    r"(?:so\s+|very\s+|really\s+|dead\s+|truly\s+|awfully\s+|terribly\s+)?"
    r"(?:sorry|apologies|apologise|apologize|bad|fault|mistake)\b"
    r"(?:\s+(?:about|for)\s+(?:that|this|it|everything))?"
    # "my bad sorry", "sorry then", "soz": the same apology said twice or with a word after it,
    # which people do when they are a bit embarrassed ("my bad sorry" was a nod).
    r"(?:\s+(?:again|honestly|mate|pal|then|anyway|sorry|soz|eh))*[\s.!,]*$", re.I)
# A correction nobody here could file: "no it was my idea not the kids" after the bot asked
# which of the party games the children had picked, "no the quiet is the best bit of it" after an
# answer about the noise. Both reached the search hedge ("I don't know enough to answer that
# honestly. A search should sort you out quickly"), which tells a person setting the record
# straight to go and look it up, and the party line also reached the kids' games card, because
# "party" was still in the sentence. A correction is a reply to this end of the chat and there is
# nothing in it to look up, so the reply takes it and hands the thread back. The pools fit any
# correction, because what was corrected is the store's to hold and this file never sees it.
A_CORRECTION_TAKEN = (
    "Fair enough - noted. What else should I know about it?",
    "Got it, my mistake. Where does that leave things?",
    "Right, I had that wrong. Go on - what happens next?",
    "Noted, thanks for putting me straight. Tell me the rest.",
)
# "never mind", "forget it", "ignore that": the person is taking the last thing back, and the
# neutral pool answered that as well ("Thanks for telling me - I'm here if you want to dig into any
# of that"), which tells them their withdrawal was a revelation. A friend says it is dropped and
# hands the conversation back.
NEVER_MIND = (
    "Fine - we can leave that one.",
    "No problem. Say no more.",
    "Alright - forgotten. What else is on your mind?",
    "Dropped. What else would you like to do?",
)
A_DISMISSAL = re.compile(
    r"^(?:(?:oh|ok|okay|right|so|well|and|but|no|nah|hey)\s+)*"
    r"(?:never\s*mind|nevermind|forget\s+it|"
    r"forget\s+about\s+(?:it|that|this|everything|all\s+of\s+it|"
    r"the\s+(?:whole\s+)?(?:thing|lot))|"
    r"forget\s+(?:i|what\s+i)\s+said|"
    r"ignore\s+(?:that|it|me|this)|scratch\s+that|as\s+you\s+were|nvm|"
    r"no\s+worries|dont\s+worry(?:\s+about\s+it)?|do\s+not\s+worry(?:\s+about\s+it)?|"
    r"leave\s+it|drop\s+it)\b"
    # "never mind that", "forget i said that", "ignore it eh": the thing taken back is pointed at
    # as well, and leaving it in the tail turned a withdrawal into "Got it. Is there anything
    # you'd like a hand with?" (@rust-buffalo, on #6613).
    r"(?:\s+(?:about\s+(?:that|it)|that|this|it|eh|huh|then|anyway|now|thanks|ta|mate|pal|"
    r"honestly|though|tho))*"
    # "forget about it, ill do it myself": the withdrawal and what they will do instead are one
    # turn, and the line was answered from the neutral pool ("Thanks for telling me - I'm here if
    # you want to dig into any of that"), which tells them a withdrawal was a revelation.
    r"(?:\s*[,;]\s*[^.!?]{0,40})?[\s.!]*$",
    re.I)

# A small thing the person did with their hands or their day ("i painted the fence today", "we
# tidied the loft", "i made a lasagne from scratch"). There is nothing to advise and nothing to
# file, so the neutral pool nods: "I'm listening - say more if it helps" answers a person who has
# just told you what they did with their afternoon with nothing at all. A friend asks how it went.
# Only the lines no module answers get here, and the pool sits before the echo, because "Got it -
# you painted the fence today" is the same empty answer with the words put back.
A_THING_DONE = (
    "Nice - how did it go?",
    "Good on you. How long did that take?",
    "Nice one - are you pleased with it?",
    "What made you start on that?",
    "Nice - how do you feel now it's finished?",
)

# The same news, said before it is done: "im doing my essay tonight", "im writing my essay",
# "im decorating the bedroom this weekend", "im cooking dinner later". The scan has called these
# "soon" and "at" all along, and the pool above is chosen for "done" - so a person telling you
# what they are about to do got "Nice - how do you feel now it's finished?" or "how did it go?",
# which asks about an afternoon that has not happened. A friend asks about the plan instead.
# A place secured in something still to come ("i got an audition", "i got tickets for the match",
# "i got a viewing for a flat"). The day question used to take these and ask how it went, which
# nobody can answer about a thing that has not happened; the date is the part a friend wants, so
# these ask for it and leave the preparing alone until the person says what it is.
A_BOOKING_AHEAD = (
    "Nice one. When is it?",
    "Good stuff - when is it, and is there anything to sort before then?",
    "Then there is that to look forward to. What day is it?",
    "Good. Is it soon, or a while off?",
    "Nice. Does that give you much time to get ready for it?",
)

# The same, when the date is on the line already: asking when it is would ask for the thing just
# said, so these take the date as given and ask about the rest of it.
A_BOOKING_AHEAD_DATED = (
    "Then there is that in the diary to look forward to. Who are you going with?",
    "Good - and the date in the diary is half the job. What do you need to sort before then?",
    "Then there is something to look forward to. Are you going on your own or with someone?",
    "Nice. Does that give you long enough to get ready for it?",
)

A_THING_AHEAD = (
    "Good luck with it - what are you doing first?",
    "Nice. How long do you reckon it'll take?",
    "Hope it goes smoothly. Anything you're not sure how to start?",
    "Get stuck in. What's the first bit?",
    "Good luck with it - how far do you want to get?",
    "Nice. Is there any of it you're not looking forward to?",
)

# A thing seen to rather than made - "booked the hotel last night", "paid the deposit", "sent the
# form off", "cancelled the gym". "How did it go?" fits a fence and not a booking, and "are you
# pleased with it?" fits neither, so the pool asks the part a friend asks about a job got out of
# the way: that it is done, and that it was not a nightmare. rust-buffalo measured the gap (#routing
# 38585): none of these verbs was in DONE_VERB, so "paid the deposit" got the neutral nod, "booked
# the hotel last night" got the choose-a-hotel card, and "cancelled the gym" got the cancel one.
A_THING_SEEN_TO = (
    "Good - that's that done.",
    "Nice one. One less thing to see to.",
    "Good - was it straightforward?",
    "Good - that's that off your mind now.",
)

# Something bought or ordered is a thing done too, but the question is about the thing: "how did it
# go?" is asked of a fence, not of a sofa. Kept apart from the seen-to pool for that reason and no
# other - both are chosen by the verb, never by the noun, so "ordered the new sofa" and "ordered
# the repeat prescription" read the same and neither reads the object.
A_THING_BOUGHT = (
    "Nice one - is it what you were after?",
    "Good. Was that a happy buy or a sensible one?",
    "Nice - what made you go for that one?",
)

# A walk, a run or a bike ride is a thing done but not a thing made, and "how do you feel now it's
# finished?" is nonsense asked of a walk: a person who says "i walked to work today" was asked how
# they felt now it was finished. The verbs of going have no finished thing to ask about, so they
# get the questions that fit anything; every other verb in DONE_VERB made something.
# "went" and "did" are here because `_thing_done_scan` reads "i went for a run" and "i did a
# workout" off the object rather than the verb, and both are the going shape: a walk has no
# finished thing to ask about.
GONE_VERB = frozenset(("walked", "cycled", "ran", "swam", "hiked", "jogged", "gardened",
                       "shopped", "went", "did"))

A_THING_GONE = (
    "Nice - how did it go?",
    "Good on you. How long did that take?",
    "What made you start on that?",
    "Nice one - how did that feel?",
)

# The same afternoon said while it is still going: "i've been painting the fence all morning",
# "im painting the kitchen", "i spent the morning repainting the kitchen". Something is under way,
# so "how's it going?" is the question a friend asks - and it is only asked here, because every
# line above has already said the thing was finished ("today", "from scratch", a past tense), and
# asking a person who has just told you what they did whether they have finished it is a cold
# reply.
A_THING_ON = (
    "Good - how's it going?",
    "Good - is that it done now?",
    "Good on you. How much longer have you got?",
)

# A job named with no time span at all ("im painting my kitchen") is a different line from the
# same afternoon with the span in it ("i've been painting the fence all morning"): nothing has
# been said about how long, so "how much longer have you got?" arrives out of nowhere. These ask
# about the job itself, which is what a friend does when they hear what you are in the middle of.
A_JOB_ON = (
    "Good - how's it going?",
    "Nice - is it the messy bit yet?",
    "Good on you. What made you start on it?",
    "Nice one - nearly there, or still in the middle of it?",
    "Good - and is it going to plan?",
)

# The job said with a day still to come: "im painting it tomorrow", "im doing the garden this
# weekend". Asking whether it is done yet of a thing that has not started is the cold reply, so
# the future tense gets the questions a friend asks of a job they are about to start.
A_JOB_SOON = (
    "Good - how's the plan for it looking?",
    "Nice one. Have you got everything you need for it?",
    "Good on you. What made you decide to do it?",
    "Nice - is it a big job?",
)

# A thing seen to: the five-minute jobs of adult life. None of them makes anything, so the pool is
# A_THING_SEEN_TO rather than the made-one. The calling verbs - "called", "rang", "texted" - are
# deliberately not here: "i called my mum" is a line the memory store already answers properly
# ("Noted: you called your mum."), and "called the council" is the same verb with a different
# afternoon.
SEEN_TO_VERB = frozenset((
    "booked", "reserved", "paid", "sent", "posted", "emailed", "signed", "cancelled",
    "renewed", "registered", "applied", "collected", "hired", "upgraded", "submitted", "filed",
    "transferred", "refunded", "complained",
))

# Something bought or ordered is the same shape, and the pool that asks about the thing.
BOUGHT_VERB = frozenset(("bought", "ordered"))

# Things that are given rather than chosen, so "what made you go for that one?" is not the
# question for them: "ordered a repeat script" is admin, not a buy.
NOT_CHOSEN = frozenset(("prescription", "prescriptions", "script", "scripts", "medicine",
                        "medicines", "meds", "tablets", "pills", "inhaler", "inhalers",
                        "antibiotics", "vaccine", "jab", "referral"))

# Somewhere to be, with people waiting: the reply is the one line to send and the time, because
# that is the whole of what a late person owes anybody.
LATE_NOW_LINES = (
    "Say it before they notice - one line and the time you will be there - then get moving. "
    "What has held you up?",
    "Tell them now, with the time you will actually be in, and stop apologising after that. "
    "What is holding you up?",
)

# Something slipping rather than somewhere to be ("im running behind on the decorating", "im
# behind on my emails"): there is nobody waiting on a time, so neither line above fits - "before
# anyone has to ask" is the wrong thing to say to somebody whose washing is behind. The reply is
# about the work itself: pick the piece that finishes soonest and give it a fixed go.
LATE_BEHIND_LINES = (
    "Pick the piece of it that finishes soonest and do that one now - the rest can wait. "
    "What is slowing you down?",
    "Being behind is a list problem, not a character one: do the smallest piece today and "
    "write down the rest. What is in the way?",
)

# The verb has to be a thing done with the day, so "i needed a break today" and "i wanted to go
# home" stay out: they are about how the day was, not about something finished.
DONE_VERB = frozenset((
    "painted", "cleaned", "tidied", "cleared", "sorted", "fixed", "mended", "built", "made",
    "baked", "cooked", "roasted", "brewed", "planted", "repotted", "potted", "dug", "mowed",
    "weeded", "pruned", "sanded", "varnished", "tiled", "grouted", "plastered", "wallpapered",
    "hung", "washed", "ironed", "hoovered", "vacuumed", "mopped", "scrubbed", "dusted",
    "decluttered", "rearranged", "sewed", "sewn", "knitted", "crocheted", "hemmed", "repaired",
    "assembled", "installed", "rewired", "serviced", "oiled", "walked", "cycled", "ran", "swam",
    "hiked", "jogged", "gardened", "shopped", "packed", "unpacked", "labelled", "filed",
    "wrote", "printed", "polished", "changed", "stripped", "stained", "swept", "watered",
    "papered", "sealed", "glued", "screwed", "nailed", "cut", "trimmed", "chopped", "picked",
    "froze", "pickled", "preserved", "batched", "prepped",
    # "i fired a pot in the kiln yesterday" is an afternoon's making, and it had no reading at
    # all: the mood cue on "fired" took the turn and the person heard "sorry to hear that". The
    # verb is the same one a sacking uses, so the object is what says which - see DONE_ONLY_A_THING.
    "fired",
)) | SEEN_TO_VERB | BOUGHT_VERB

# The verbs above whose object is always a thing: "i fired a pot" is pottery and "i fired him" is
# a person losing a job, which belongs to the trouble readings rather than to the cheerful pool.
DONE_ONLY_A_THING = frozenset(("fired",))

DONE_NOT_A_PERSON = frozenset((
    "me", "him", "her", "them", "us", "everyone", "everybody", "somebody", "someone", "anybody",
    "anyone", "people", "staff", "team", "crew", "worker", "workers", "guy", "bloke", "man",
    "woman", "person", "employee", "employees", "apprentice", "lad", "lass", "girl", "boy"))

# A verb like "made" or "got" is only this shape with something small and done after it: "i made a
# mistake" and "i made a complaint" are not a good afternoon, and "i got a letter" is news.
DONE_NOT_THIS = frozenset((
    "mess", "mistake", "error", "complaint", "decision", "appointment", "call", "offer",
    "promise", "excuse", "fuss", "noise", "start", "plan", "list", "wrong", "loss", "mind",
    "respects", "tribute", "tributes", "toll", "price",
    # "made" is the one verb here that takes an object it did not make: nothing was built when
    # something made the news, made history or made a difference, and the pool that asks "what
    # made you start on that?" asks after a job. Every word below is an object of "make" that is
    # not a thing in the hand, so the line is news or a manner of speaking rather than an
    # afternoon's making, and the pools that read news take it instead.
    "news", "headlines", "papers", "history", "waves", "difference", "sense", "peace",
    "amends", "headway", "progress", "friends", "enemies", "allowances", "allowance",
    "sure", "certain",
))

# A living thing is not a buy to be asked about: "bought a puppy" is a new arrival, and "was that a
# happy buy or a sensible one?" is a question for a sofa. The pet reader has the line for a puppy
# ("how is it settling in?"), so this shape stands down rather than answering it with the wrong one.
ALIVE = frozenset(("puppy", "pup", "kitten", "dog", "cat", "hamster", "rabbit", "guinea",
                   "budgie", "fish", "horse", "pony", "parrot", "chick", "chicks", "hen", "hens",
                   "gerbil", "ferret", "tortoise", "kittens", "puppies", "dogs", "cats"))

# What is left after the verb has to name the thing being worked on, or the line is not about a
# job at all: "im cleaning" on its own is a shrug about the day, and "im sorting it out" keeps
# its place in the conversation, where "it" is whatever we were just on.
THING_AFTER = frozenset(("it", "this", "that", "them", "things", "stuff", "everything",
                         "the", "a", "an", "my", "our", "his", "her", "their", "some",
                         "out", "up", "away", "off", "in", "on", "round", "around"))

# "im doing my best", "im doing nothing much" wear the same shape and are about the day, not about
# a job: the words after the verb decide, and these make it the day.
AT_IT_NOT = frozenset(("best", "right", "wrong", "nothing", "much", "anything", "ok", "okay",
                       "fine", "well", "same", "job",
                       # "im sorting out my head" and "im sorting my life out" are the shape with a
                       # metaphor after it, not a job: there is nothing to ask how it is going.
                       "head", "life",
                       # Running late is not running at a job: "im running late for work" was read
                       # as a thing under way and got "Nice - is it the messy bit yet?" out to
                       # somebody rushing to get in. The word after the verb is what says so.
                       "late", "behind"))

# "im doing the garden" is the shape with the emptiest verb in it, so it is read here and not in
# DONE_VERB: "i spent the day doing nothing" is the day and not a job, and it stays out.
AT_IT_EXTRA = frozenset(("doing",))

# "im getting fat", "im getting old", "im getting tired": "getting" is a verb of becoming, and what
# comes after it here is the state the person is in rather than a thing they are working on. The
# line has the shape of "im painting the fence" and a word after the verb, so it was read as a job
# under way and asked the cheerful question - "my nan says im getting fat" got "Get stuck in.
# What's the first bit?" - which is the wrong thing to say to somebody who has just been told they
# are getting fat. A thing being fetched is untouched: "im getting a new kitchen", "im getting my
# hair done at four" still have the plan and purchase pools.
BECOMING = frozenset(("getting", "becoming", "turning", "feeling"))
BECOMING_STATE = frozenset((
    "fat", "bigger", "thin", "skinny", "heavy", "chubby", "large", "weight",
    "old", "older", "tired", "sleepy", "hungry", "late", "slow", "slower", "better", "worse",
    "sore", "stiff", "weak", "forgetful", "grumpy", "moody", "grumpy", "stressed", "bored",
    "cold", "hot", "warm", "impatient", "lazy", "bald", "grey", "gray", "wrinkly", "antsy",
    "frustrated", "anxious", "down", "homesick", "clumsy", "deaf", "blind", "short-sighted"))

# A knock the person gave themselves - "i hit my thumb with a hammer", "i dropped a tin on my
# foot", "i trapped my finger in the door", "i stubbed my toe on the table". HARM_ON_ME stands
# the cheerful pools down for these (a sore thumb is not an afternoon well spent) and safety
# answers the shapes it has a card for (a cut, a burn, a bang on the head); the rest of them fell
# through the floor, which said "Got it. Is there anything you'd like a hand with?" or "Thanks for
# telling me - I'm here if you want to dig into any of that". A receipt for a sore thumb. A friend
# says ouch and gives the one thing that helps, and asks the person in pain nothing.
KNOCKED = (
    "Ouch. Something cold on it for ten minutes, then take it easy tonight.",
    "Ouch - that's a sore one. Ice it and rest it, and see how it is in the morning.",
    "That smarts. A cold pack for ten minutes, and keep it up if you can.",
    "Ouch. Cold water or a cold pack, and if it swells up or you can't use it tomorrow, get it "
    "looked at.",
)

# A fall or a nail underfoot, said as an account of the day, where no card answered: the reply is
# the question a friend asks first and no advice, because what to do depends on how bad it is and
# the bot cannot see it. "Ouch" belongs to the pool above, which is for a reaction with nothing
# else in the line; these lines have their own story in them, so the question is about the
# aftermath rather than about what happened.
MISHAP_BACK = (
    "How bad is it - sore, or something that needs a look?",
    "Is it bad enough to get checked, or has it settled?",
    "Did it need a look, or was it just a fright?",
    "Ouch. How is it now - still sore, or has it eased?",
    "How is it now? The knock is one thing; how it feels after is the bit that matters.",
)

# The blunt verbs only. A cut and a burn have their own cards in safety and their own aftercare,
# so a knock pool that offered ice for a cut would be a worse answer than the card it replaced.
# The verb has to be the person's own ("i hit my thumb"), because "he hit my thumb" is somebody
# else's doing and reads as a fight rather than a knock about the house.
# The places a knock lands. Kept whole so the two ways of saying it can share it.
KNOCKED_SPOTS = (
    r"finger|fingers|thumb|hand|hands|arm|arms|leg|legs|foot|feet|toe|toes|wrist|head|eye|eyes|"
    r"knee|face|shoulder|skin|chest|stomach|shin|elbow|ankle|back|hip|nose|chin|lip|knuckle|"
    r"palm|heel|ribs|neck|calf|thigh")

WALKED_INTO_POOL = (
    "Ouch - those come out of nowhere. Is it bruising up?",
    "Ouch. Are you alright? Those catch you right on the bone.",
    "Ouch - that'll sting for a bit. Is it sore to touch?",
    "Ouch. Does it hurt to put weight on it?",
)

# A person saying something hard about themselves ("i feel like im not doing enough at work",
# "im 34 and i still dont know what i want to do") is asking to be taken seriously, and the
# neutral nod answers it with "Noted!" - it could have come before any message at all. Two
# shapes cover the ordinary ways people say this, and each pool names the thing and asks one
# question back rather than agreeing, disagreeing or handing out advice.
# The speaker has to be the one the verdict is about. Without that, a bare "isn't good enough"
# catches whatever noun comes before it, and "the paint job isnt good enough" or "the weather
# isnt good enough for a picnic" became a line about the person's own worth.
MYSELF = r"(?:i|i'?m|im|i am|me|myself)"

MY_DOING = (r"(?:best|work|effort|parenting|teaching|grades|marks|results|cooking|running|"
            r"english|maths|math|driving|swimming|performance|drawing|writing|playing|scores|"
            r"revision|study|studies|business|portfolio|body|appearance|looks|speed|output)")

NOT_ENOUGH_REPLY = (
    "That sounds like a heavy thing to be carrying, and it usually means you care about it more "
    "than the people who don't. What would \"enough\" actually look like for you?",
    "Feeling like that is rough, and it is rarely the true picture. What has the week actually "
    "held?",
    "That is a hard standard to hold yourself to. Whose is it - yours, or somebody else's?",
)

NO_DIRECTION_REPLY = (
    "Plenty of people who look settled are quietly making it up too; they just don't say so. "
    "What is the last thing you did that you actually looked forward to?",
    "Not knowing is normal at any age, whatever it looks like from the outside. If money were "
    "not the problem, what would you want the next few years to look like?",
    "That is a fair thing to be stuck on, and picking faster does not fix it. What have you "
    "tried that you would happily never do again?",
)

GRIEF_AFTER = (
    "People grieve at different speeds, and going quiet is common. Have you been able to say "
    "how you are finding it?",
    "That is hard, and it is lonely when you are both carrying it differently. What would you "
    "want to say to them, if it were easy?",
    "Most people go quiet with it rather than talk. Tell me what it is like at home and we can "
    "work out how to open it up.",
    "That sounds like a lot to sit with on your own. Is there anyone you can say this to?",
)

# Someone who can call the person in has asked for a word: "my sons teacher wants a word", "hr
# want to see me on friday", "the council have written to me", "school rang about my lad". The
# reading says which (understood["summons"]), because the three want different replies: a letter
# wants an answer in writing with a copy kept, a phone call wants ringing back today, and a
# meeting is mostly the wait to find out what it is about. Before this every one of them was
# said back to the person ("Noted: your sons teacher wants a word"), which names the worry and
# leaves them nowhere to put it.
SUMMONS_SEEN = (
    "Not knowing what it is about is the worst bit, so ask straight out at the start what it is "
    "about. Write down the two things you want to say before you go in and you will have the "
    "measure of it - they are usually smaller than they feel.",
    "Ask at the start what it is about, and take a note of what they say. Waiting without "
    "knowing is harder than the meeting itself, and you can always ask for it in writing after.",
    "Write down what you want to ask tonight, while it is quiet, and say at the start that you "
    "would like to know what it is about. Take someone with you if you would rather not go alone.",
)

SUMMONS_WRITTEN = (
    "Check the date they want a reply by before anything else, then answer in writing and keep a "
    "copy. Say what you want to know at the top of the letter, so the answer comes back to you in "
    "writing too.",
    "Answer it in writing rather than by phone, so there is a record, and keep a copy of what you "
    "sent. Start with the one question you most want answered and let them come back on the rest.",
)

SUMMONS_RANG = (
    "Ring them back today rather than sitting on it - the waiting is usually worse than the call. "
    "Have your details in front of you and ask at the start what it is about.",
    "Ring back today while you have it in your head, and ask straight out what it is about. If you "
    "would rather not, email is fine too: say when they rang and ask them to put it in writing.",
)

GRIEVANCE = (
    "That would get to me too. Do you want to work out what to say to them, or is it more a "
    "case of letting off steam?",
    "Annoying. Tell me how it has gone so far and we'll work out what to say.",
    "Fair enough — that wears you down. Shall we think about how to raise it, or would you "
    "rather park it for now?",
    "I can see why that grates. What have you tried saying so far?",
)

# The person is in the line: "my sister", "our landlord", "the flatmate", or somebody.
# Only people you can talk it over with: a small child who will not eat is a different job
# ("my son wont eat vegetables" wants ideas, not "what should I say to him"), so children and
# pets are left to the pools that know about them.
GRIEVANCE_PEOPLE = frozenset((
    "sister", "brother", "mum", "mom", "mother", "dad", "father", "parent", "parents",
    "partner", "husband", "wife", "boyfriend", "girlfriend", "flatmate", "housemate",
    "roommate", "landlord", "landlady", "boss", "manager", "colleague", "coworker",
    "neighbour", "neighbor", "friend", "friends", "in-laws", "someone", "somebody", "people",
    # A former partner is somebody you can talk it over with, and "my ex keeps texting me" was
    # getting "Got it. Is there anything you'd like a hand with?" because the word was not here.
    "ex", "exes",
))

# It is what the other person *does to* the speaker that makes it a grievance, not the fact
# that it happens again. "my sister keeps borrowing my stuff" has an impact; "my brother always
# wins at chess" and "my mum keeps saying she is fine" are just news, and a word for "again"
# on its own is not enough to tell them apart.
GRIEVANCE_IMPACT = frozenset((
    "wont", "refuse", "refuses", "refused", "doesnt", "dont", "ignores", "ignored",
    "ignoring", "shouts", "shouting", "yells", "yelling", "moans", "nags", "nagging",
    "interrupts", "interrupting", "cancels", "cancelled", "promised", "promises", "forgets",
    "forgot",
    "forgetting", "borrows", "borrowed", "borrowing", "nicking", "nicks", "rings", "ringing",
    "phones", "phoning", "calls", "calling", "texts", "texting", "listens", "listening",
    # "messaging" and "dming" are how people say texting now, and "my sister keeps messaging me"
    # was getting "Got it. Is there anything you'd like a hand with?".
    "messages", "messaging", "messaged", "dms", "dming", "dmed",
    "criticises", "criticizes", "blames", "blaming", "eats", "eating", "hides", "spends",
    "spending", "complains", "complaining", "swipes", "hoards",
))

GRIEVANCE_NOT_A_THING = frozenset(("own", "way", "life", "mind", "fault", "turn", "opinion"))

GRIEVANCE_PHRASES = ("without asking", "every time", "all the time", "over and over",
                     "at the last minute", "time after time", "every day", "each day",
                     "every night", "drives me mad", "drives me up the wall",
                     "does my head in", "keeps me awake")

# The wear the person puts on the speaker, said with the speaker as the object: "my friend drains
# me", "my mum wears me out", "my brother is hard work". There is no "keeps" or "always" in these
# and nothing of theirs is in the way, so the recurrence test above missed them and the line was
# filed as a fact and said back - "Noted: your friend drains you." - which is the coldest reply
# there is to somebody saying a person tires them out. The speaker is the object, so the impact is
# in the phrase itself; the person still has to be in the line (checked above), which keeps "the
# commute drains me" and "my phone battery drains fast" out of it.
GRIEVANCE_STRAIN = ("drains me", "draining me", "wears me out", "wearing me out",
                    "wore me out", "worn me out", "takes it out of me", "is hard work",
                    "are hard work", "is exhausting", "are exhausting", "is draining",
                    "are draining", "winds me up", "gets me down", "getting me down")

# The same wear with a word between the verb and it: "my sister is so draining", "my mum is
# really tiring", "my brother is knackering". The phrase list above is matched on the line as
# written, so every one of these fell through to the nod - "Noted: your sister is so draining." -
# which hands somebody their own line back when they have just said a person tires them out.
# The word for the wear is an effect the person has on the speaker, never the person's own state:
# "she is exhausted", "my mum is tired" and "my wife is worn out" are the health words here and
# are deliberately not in it.
GRIEVANCE_STRAIN_SAID = re.compile(
    r"\b(?:is|are|was|were)\s+"
    r"(?:(?:so|really|very|properly|totally|just|always|dead|bloody|quite|pretty|constantly|"
    r"super|a bit|abit|that|this)\s+)?"
    r"(?:exhausting|draining|tiring|knackering)\b")

# A pronoun with the word for the wear after it is a person: "she is so draining", "he is really
# exhausting". Nobody says that about a thing, and the wear is an effect, so it cannot be the
# person's own state the way "she is exhausted" is.
GRIEVANCE_PRONOUN = re.compile(
    r"\b(?:she|he|they)\s+(?:is|are|was|were|keeps|kept)\b")

# A body, an illness or a harm is not a grumble about somebody's manners: "my dad keeps
# coughing at night" and "my mum keeps falling over" want a care line, and "my boss keeps
# touching me" is not something to work out what to say about over a coffee. Those keep the
# reply they got, so this is checked before the grievance test.
GRIEVANCE_HEALTH = frozenset((
    "cough", "coughs", "coughing", "cold", "flu", "sick", "ill", "unwell", "pain", "pains",
    "painful", "hurt", "hurts", "hurting", "ache", "aches", "aching", "dizzy", "faint",
    "fainting", "falls", "falling", "fallen", "fell", "forget", "forgets", "forgetting",
    "memory", "confused", "shaking", "swollen", "swelling", "weight", "thin", "thinner",
    "sleep", "sleeping", "sleeps", "tired", "exhausted", "snore", "snores", "snoring",
    "breath", "breathing", "bleed", "bleeding", "blood", "bruise", "bruises", "lump", "lumps",
    "rash", "fever", "temperature", "vomit", "vomiting", "hospital", "doctor", "gp", "nurse",
    "medication", "tablets", "medicine", "drinking", "drinks", "drunk", "smokes", "smoking",
))

GRIEVANCE_HARM = frozenset((
    "hit", "hits", "hitting", "punch", "punches", "punching", "kick", "kicks", "kicking",
    "kicked", "slap", "slaps", "grabbed", "grabs", "pushing", "pushes", "touched", "touches",
    "touching", "threaten", "threatens", "threatening", "threatened", "abuse", "abusive",
    "bullies", "bullying", "bullied", "screams", "screaming", "swears", "cursing", "insults",
))

GRIEVANCE_HARM_PHRASES = ("shouting at", "shouts at", "yelling at", "yells at", "screaming at",
                          "calls me names", "calling me names", "lost weight", "losing weight",
                          "out of breath")

# Not eating is a body: "my dad wont eat" wants the food answer, while a flatmate eating the
# speaker's food is manners. The word on its own cannot tell them apart, so the phrases do.
GRIEVANCE_HEALTH_PHRASES = ("wont eat", "won't eat", "doesnt eat", "doesn't eat", "not eating",
                            "stopped eating", "stopping eating", "no appetite", "off his food",
                            "off her food", "off their food", "lost his appetite",
                            "lost her appetite",
                            # Forgetting a birthday is manners; forgetting who somebody is, or
                            # where they are, is memory, and that is a doctor's question.
                            "forgot who", "forgets who", "forgot my name", "forgets my name",
                            "forgot our name", "forgot where", "forgets where",
                            "forgot how to", "forgets how to", "getting forgetful",
                            "forgetful",
                            # Somebody who has gone quiet is a worry about them, not a grumble
                            # about their manners: "my sister is not responding to my texts".
                            "not responding", "not replying", "no reply", "hasnt replied",
                            "hasn't replied", "isnt replying", "isn't replying", "wont reply",
                            "won't reply", "wont answer", "won't answer")

# The same word attached to the speaker is the speaker's own trouble, not the other one's
# behaviour: "my husband is in a hospice and i dont know what to bring him" is a practical ask,
# and "i never know what to say to my mum" is the person themselves. Dropped before the test.
# The person said as a pronoun, in a line that is still about them.
THREAD_PEOPLE = frozenset(("she", "he", "they", "them", "him", "her", "his", "their", "theirs"))

# A person who tells the bot their next step ("ok ill book her in tomorrow", "ill try that
# tonight") is not asking for anything: they want it acknowledged. A flat "Got it" misses that,
# and the sad pool would be wrong, because a plan is not bad news.
PLAN = (
    "Good — that sounds like the right next step. Tell me how you get on.",
    "Nice one. Let me know how it goes.",
    "That sounds sensible. Shout if it does not go to plan.",
)

# The reply to a feeling said in the shape of a plan. Short and warm, and it asks for the story,
# because the person is telling one.
IDIOM_SHY = (
    "Ha — one of those days, then. What happened?",
    "Oh no. Go on, what happened?",
)

IDIOM_GLAD = (
    "Ha — that good? What are you waiting for?",
    "Sounds like a big one. What is it?",
)

PLAN_DONE = ("booked it", "booked her in", "booked him in", "booked in", "sorted it",
             "booked an appointment")

# The same reader takes a plan and a thing already done, and a done thing is not a next step to be
# told how it goes. "i sorted it" was answered "Good — that sounds like the right next step. Tell
# me how you get on." for a job that was finished, and "nvm i sorted it", "dw i sorted it" and "i
# sorted it already thanks" got the same. A thing done wants the past tense and no homework.
PLAN_DONE_ACK = (
    "Nice — glad that's sorted. Shout if it comes back.",
    "Good, that's one off the list. Hope it stays that way.",
    "Glad you got it done — say the word if it turns up again.",
)

# A person in the line, after a leaving word: "leaving him", "divorcing my husband".
A_PERSON = (r"(?:him|her|them|my boyfriend|my girlfriend|my partner|my husband|my wife|my ex|"
            r"my fiance|my fiancee|my other half|my man|my woman)")

# Nobody has just been told good news by a break-up, and "Nice one. Let me know how it goes" is
# worse than no answer at all. It is not a condolence either: leaving someone who hurt them is
# the right thing and leaving someone they still love is the hardest thing they will do this
# year, so one neutral, kind line has to cover both.
RELATIONSHIP_DECISION = (
    "That sounds like a big decision. How are you feeling about it?",
    "That is a big thing to do. How are you doing with it?",
    "That's a lot to be carrying. Have you decided, or are you still weighing it up?",
)

ACK = (
    "Great — shout if you need anything else.",
    "Ha, fair enough. I'm here if you want a hand with anything.",
    "Right — anything else on your mind?",
)

# "Great" is a congratulation, and a nod after a sore knee, a job gone, a diagnosis or a laptop
# that died is not something to be congratulated on. The rest of ACK is no better on that turn:
# "Ha, fair enough" laughs at it, and "anything else on your mind?" asks the person to start again
# on a subject that is still open. What a nod to trouble wants is the plain end of the turn with
# the door left open - no congratulations, no laugh, no question.
ACK_AFTER_TROUBLE = (
    "Right — I'm here if you want a hand with any of it.",
    "Fair enough. Shout if you want to go into any of it.",
    "Alright — I'm here if you want to come back to it.",
    "Got it. Say the word if you want more on it.",
)

# The same nod after a hard line. ACK's first line opens on "Great", which is a farewell to
# somebody who has just said they are having a bad time, and its other two are a shrug: "im really
# sad" / "mm" and "im so lonely" / "mm" were told "Great — shout if you need anything else". The
# nod there is the person staying in the room, so it gets room and no cheer. Nothing in these
# asks a question: the person has already said more than they wanted to.
ACK_WARM = (
    "I'm here. Say more if you want to.",
    "No rush. I'm not going anywhere.",
    "Right. Take your time with it — tell me if you want a hand.",
)

# A cue is a word that needs nothing after it. "passed" is left out on purpose: "i passed the
# salt", "i passed him the ball" and "i passed the deadline" are the same word and none of them is
# news, so a pass is read by `reads_as_good_news` (bot/compose/goodnews.py), which asks what was
# passed before it congratulates anyone.
POSITIVE_CUES = frozenset((
    "finished", "finally", "won", "adopted", "promoted", "excited", "amazing",
    "happy", "proud", "celebrate", "engaged", "pregnant", "hired", "accepted", "improved",
    "brilliant", "delighted", "thrilled", "sorted", "succeeded", "achieved",
))

# Words for a thing that has come apart, or a plan that has fallen through. A line with one of
# these in it is not good news however the wait reads: "my laptop has finally died" was answered
# "Good for you! That's really lovely news." and "the boiler finally died" "That's great news —
# nice one", because "finally" was the only word in either line that `_mood` knew, and it knew it
# as a cue. The wait being over says nothing about what the wait was for, so a wait-ending word
# does not make a line good when the thing it waited for came apart.
SOMETHING_CAME_APART = re.compile(
    r"\b(?:died|dies|dying|dead|broke|broken|breaks|kaput|bust|busted|collapsed|flooded|"
    r"leaking|snapped|conked|packed\s+in|packed\s+up|gave\s+up|given\s+up|gave\s+in|"
    r"stopped\s+working|stopped\s+charging|fell\s+apart|had\s+it|written\s+off|"
    r"beyond\s+repair|on\s+the\s+blink)\b")

# A cue that says only that the wait is over. It is the one word that can turn a line about
# something that came apart into a congratulation, so it is the only cue the reader above guards.
A_WAIT_ENDING = frozenset(("finally",))

# Words that turn the cue after them round: "not finished" is not finished, and "not yet
# finished but nearly" is a person still working, so neither is good news. The same words
# close a care thread when they stand in front of "stopped" or "fine".
NEGATORS = frozenset(
    "not no never isnt wasnt arent werent hasnt havent hadnt didnt dont doesnt wont cant "
    "cannot".split())

# "Nothing makes me happy any more" is not good news: the word saying there is none of the thing
# turns the cue round as a "not" does, and a friend hears the complaint rather than the cue.
# These are read only where a good-news cue is counted - see `_no_such_thing_before`. They are
# deliberately not in NEGATORS above: "no one is proud of me" is a complaint, but "nobody thought
# i could pass and i passed" is a win, and a bare word list cannot tell those apart.
NOTHING_AT_ALL = frozenset("nothing nobody none nowhere neither nor noone".split())

# A word that starts a new claim, so a quantity before it is about something else: "nobody
# believed i could do it but i did" is a win, and the "nobody" belongs to the doubt in front.
# "and" and "because" do the same job: "nobody thought i could pass and i passed" is the win it
# ends on, and "i passed because nobody helped me" credits nobody with the passing.
CONTRAST = frozenset("but though although yet however still and because cos cause so when while"
                     .split())

NEGATIVE_CUES = frozenset((
    "failed", "fail", "failing", "lost", "lose", "worried", "worry", "stressed", "stress",
    "lonely", "sad", "tired", "angry", "upset", "struggling", "struggle", "hate", "awful",
    "terrible", "horrible", "anxious", "scared", "afraid", "hurt", "hurts", "broke", "argued",
    "argument", "arguing", "crying", "cried", "miss", "missing", "worst", "exhausted",
    "overwhelmed", "rejected", "fired", "sick", "painful", "miserable", "hopeless",
    "worthless", "pointless", "numb", "drained",
    "annoyed", "frustrated", "frustrating", "rude", "ignored", "unfair", "nervous",
    "panicking", "awkward",
    # A temper that has gone short ("i keep snapping at my partner") is how they are, not a fact
    # to file: said back as "Noted: you keep snapping at your partner" it is the coldest reply
    # there is to someone telling you something they are ashamed of.
    "snapping", "snappy", "irritable", "grumpy", "cranky", "tetchy", "ratty",
    # "i think my cat is depressed" was read as a positive line and cheered; the word is a cue
    # whether the mood belongs to the person, a person they care for, or an animal.
    "depressed",
))

EMERGENCY_AFTER = (
    "If you haven't already, ring 999 or 911 now, and follow what they tell you — they can "
    "hear what I can't.",
    "Do what the emergency line says over anything I could offer, and call back the moment "
    "something changes.",
    "Stay in touch with them and say if anything gets worse — don't wait to see if it settles.",
)

# The emergency in the room, not in a body: a fire, a gas leak, a boiler or an alarm going off.
# The pool above is written for a person who is hurt ("stay in touch with them"), and a kitchen
# fire has nobody to be in touch with, so the same turn-taker said something that does not make
# sense. Same job - keep the person inside the emergency and on the right help - in the words the
# hazard needs. Nothing here tells them to go back in for anything.
HAZARD_WORDS = frozenset(("fire", "fires", "smoke", "flame", "flames", "gas", "fumes",
                          "carbon monoxide", "flue", "fire brigade", "fire service"))

HAZARD_AFTER = (
    "Stay out and ring 999 or 911 from there if you haven't already: nothing inside is worth "
    "going back in for.",
    "Get everyone out first and call from outside; tell the operator exactly what is burning or "
    "leaking and where.",
    "Keep well clear and follow what the operator tells you - they can hear what I can't.",
    "If you can't get out, get to a room with a window, shut the door behind you and ring 999 "
    "or 911 from there.",
)

THANKS_AFTER = (
    "Anytime. Look after yourself, and reach back out if anything changes.",
    "You're welcome — stay safe, and don't sit on anything that gets worse.",
    "Any time. Take care — ring again if anything changes.",
)

# The continuation of a domestic abuse card. An abuse thread reads as a crisis card because the
# card names a helpline, and its follow-ups were answered from the crisis pools - "should i get
# out of the house" got "keep your husband company tonight, and ring 116 123 together rather
# than for him", which is the worst sentence this bot can say to somebody asking whether to
# leave (cream-eel, #9929). The person asking is the one in danger here, and the question is
# about leaving safely rather than about company tonight, so the lines plan the going out.
ABUSE_AFTER = (
    "If you want to go, go when it is safe to: phone, keys, any paperwork you can reach, and "
    "somewhere to go rather than a drive with no end. The abuse line (0808 2000 247 in the UK, "
    "1-800-799-7233 in the US) plans this for a living.",
    "You do not have to settle all of it tonight. If you are leaving, the quiet moment when they "
    "are out is safer than the middle of a row - and 999 if you cannot get to the door.",
    "Yes, if you can do it without a row: take what you would not want to leave behind and go "
    "somewhere with other people in it. The rest can be sorted from there.",
    "Going is not the only safe answer, and it is the right one more often than not. If leaving "
    "now would make tonight worse, ring 0808 2000 247 from somewhere private when you can, and "
    "999 the moment it turns.",
)

CRISIS_AFTER = (
    "You did the right thing telling someone. Stay with a person you trust tonight, and keep "
    "that number handy.",
    "Keep someone with you tonight, and ring back if it gets heavier — they'd rather hear "
    "from you.",
    "I'm glad you're talking about it. Stay with the person or the line that talked you "
    "through, not on your own.",
)

# A person in a crisis thread who says they are easing ("i feel a bit better now", "im calmer
# thanks") is not changing the subject and is not asking the bot to search for anything: they
# are telling the bot the worst of it has passed. On the deck that line got "I'm not sure about
# that one, sorry - I'd rather not guess. A quick search online..." because "feelings" counted
# as a subject of its own. The care words do not fit either (nobody is bleeding), so the thread
# needs a pool of its own: accept it, keep the person with them, and leave the door open.
CRISIS_BETTER = (
    "That's good to hear, and it can come back in waves - keep someone near you tonight and "
    "say if it lifts again.",
    "Good. Hold on to that, and tell one person how today went so they can check on you.",
    "I'm glad. Stay with the person you told, and ring back here or the crisis line if it "
    "gets heavy again.",
)

EMERGENCY_BETTER = (
    "That's good to hear, and it does not change what to do: stay with the emergency line and "
    "get seen today, because feeling better is not the same as being out of the woods.",
    "Glad it feels easier. Still get checked today and stay near the phone - some things feel "
    "better well before they are better.",
    "Good to hear. Keep the line open and say the moment anything changes; I would still get "
    "seen today.",
)

# The advice was a page of it, and this line is the report on it. "i tried that and it helped a
# bit" told the bot which part worked and got a stock line that would fit any message ("Got it.
# Is there anything you'd like a hand with?"); "ive been doing it for a week now" got their own
# sentence back. A friend answers the outcome, not the report, so there are four of them: it
# worked, it has not moved yet, it made things worse, and "I am doing it" with no verdict.
# Only a line that is nothing but the report is read this way - "i tried that new cafe" is a
# place, not a report on the last answer - and only right after an answer that gave the person
# something to do, so it can never take a turn from a subject of the person's own.
ADVICE_LENGTH = 180

# The same question for a line that is nothing but the report ("it doesnt work", "none of that
# worked"): the answer behind it only has to be long enough to have been advice at all.
ADVICE_LENGTH_BARE = 120

# How far back the advice can be: the answer, then the check-in question that followed it.
ADVICE_TURNS = 3

# The subject is written every way people write it: "ive tried that" and "i have tried that"
# are the same report as "i tried that", and only the last one was read - the other two went to
# the repeat, which handed back the second half of the advice they had just said they tried.
#
# A whole list is not a report: "ive tried them all" after three films turned down is the person
# saying they have seen the lot, and `memory_store` hands back the next one or asks what they
# liked. The whole-list word is what tells the two apart, so it makes the line not a report.
WHOLE_LIST_AFTER = r"(?!\s+(?:all|both|every|each)\b)"

# What may be left in the line once the report is taken out. Anything else means the line is
# about something ("i tried that new cafe"), and it is not a report on the last answer at all.
REPORT_FILLER = frozenset(
    """i we me us my our im i'm i've ive id and but so then yet now today again still also just
    a an the bit little lot lots load much really quite very it that this them those they
    help helps helped helping work works worked working do does did doing done try tried trying
    give gave given use used using start started keep keeping go going went with on at for in
    of to from what you your said say suggested told me same change difference nothing better
    worse no not any more ok okay fine thanks thank since week weeks day days fortnight couple
    month months morning afternoon evening night been am is are was were have has had
    again alright already far everything all one two three four five six seven eight nine ten
    starting taking walking made make makes thing things sorer same before matter mind as
    if none them either than like lot a its doesnt doesn't didnt didn't isnt isn't hasnt hasn't
    havent haven't
    wont won't have has had changed changes actually really definitely properly indeed
    weve youve theyve earlier yesterday once twice
    s""".split())

CARE_BETTER = (
    "Good - keep an eye on it today and get it looked at if it comes back.",
    "That's a relief. Take it easy, and say if it starts up again.",
    "Glad to hear it. Go steady for the rest of the day and ring back if anything changes.",
)

TRIED_HELPED_REPLIES = (
    "Good - that is the one to keep doing. Most of it does its work over weeks, not days.",
    "That's what you want to hear. Keep it going, and ease off if it starts hurting again.",
    "Right, keep going with it. It is usually three or four weeks before you can call it done.",
)

# A thing that is now fine is the end of it, and the helped pool above is written for a regime
# that takes weeks ("keep going with it, it is three or four weeks before you can call it done"),
# which is the wrong thing to say to somebody whose oven is clean. Nothing here asks them to
# keep at it, and nothing names a time.
TRIED_SORTED_REPLIES = (
    "Good - that is that sorted.",
    "Nice one. That is the fix, then - worth remembering for next time it does it.",
    "Good. Say if it comes back and we will take the next step.",
    "Right, that is it sorted. Worth writing down what you did, because it usually works again.",
    "Good - that is the end of it, then.",
)

# Nothing here names a length of time: "no change yet" says nothing about how long they have
# been at it, and "a week is not long enough" invents one.
TRIED_NO_CHANGE_REPLIES = (
    "Then it is worth a phone call rather than a longer try: a pharmacist or a doctor can look "
    "at it and tell you what else is worth trying.",
    "If it has had a fair run, get it looked at rather than pushing on with the same thing.",
    "Time to change tack rather than try harder - a phone call today is a better use of the next "
    "week than another go at the same thing.",
    "That is the point to ask rather than to try harder - say what you have already done and "
    "whether there is something else worth trying.",
    "If it has not shifted after a fair go, say so where you got the advice. More of the same is "
    "not the answer at this stage.",
)

TRIED_WORSE_REPLIES = (
    "Then stop it. Something that makes it worse is not a thing to push through - let me know "
    "what it did and we will go a different way.",
    "Stop there, and get it looked at. Worse is the point to ask for help, not to keep going.",
    "Leave it off. I would get that looked at rather than persevere - worse is a reason to ask.",
    "Stop there and get it looked at. Worse than before is a reason to ask, not a stage to work "
    "through.",
)

TRIED_IT_REPLIES = (
    "How is it going with it so far?",
    "Any change since you started?",
    "Has it made any difference yet?",
)

# The same four outcomes for advice that was not about the body: a boiler, a slug, a bill or a
# loaf does not "start hurting" and there is nobody to ring about it. Paid work, cooking and the
# home are most of what a person asks about, so the outcome pools cannot all be written for a
# symptom - the reading that picks the pool is "was this thread about the body", not the topic.
TRIED_HELPED_ELSEWHERE = (
    "Good - keep at it. This kind of thing usually takes a few weeks before you can tell.",
    "That's the sign it was the right fix. Give it the time it needs, and change one thing at a "
    "time so you can tell what is doing the work.",
    "That's what you want to hear. Carry on with it, and change something if it stops working.",
    "Right, keep going with it. It is usually three or four weeks before you can call it done.",
)

TRIED_NO_CHANGE_ELSEWHERE = (
    "Then stop doing more of the same and change one thing instead.",
    "If it has had a fair run, stop and change one thing rather than repeating it.",
    "Stop pushing the same way: change one thing, then give it a day so you can see which part "
    "did what.",
    "That is the point to stop and ask rather than push on: say what you tried and what it did, "
    "and get a different idea rather than a harder one.",
    "Two goes at the same thing is enough. What it needs now is a different approach, not more "
    "of the same - change one thing rather than trying harder.",
)

# How somebody is treating them is not a request that can be asked again with one change in it:
# after "im being bullied at work" the move is a record and a route, which the card above gave, and
# "ask once more with one change in it" is coaching for a negotiation that is not happening. The
# conduct words are the composer's own grievance vocabulary, so no list is kept twice.
TREATMENT_HARM = GRIEVANCE_HARM

REFUSED_REPLIES = (
    "Ask once more, and ask what would make it a yes. A no with a reason is something you can "
    "plan around; one without leaves you guessing.",
    "Worth one more go, put as a question: what would have to change? If it is still no, at "
    "least you know where you stand.",
    "Then ask why not, and what would move it. What they say is worth more than the no itself.",
    "Ask once more with one change in it: name the smallest version they could say yes to, and "
    "ask what would make the bigger one possible.",
    "Put it to them once more in your own words and ask what would change their mind. Either "
    "answer helps you decide what to do next.",
)

# Somebody close refusing the thing that would help them. The line visits the person's worry, not
# their own: "she refuses a pendant alarm" is a son or daughter at the end of their tether, and the
# one thing worth saying is what the refusal is usually about, plus the person whose word carries.
ELDER_AID_REPLIES = (
    "It is rarely the stick or the pendant they are refusing - it is being the sort of person who "
    "needs one. Offer two so there is a choice: a plain stick rather than a hospital one, a wrist "
    "alarm instead of the pendant, the frame for the walk to the shop only. And let the GP or an "
    "occupational therapist say it, because from them it is advice and from you it is fuss.",
    "Then give them something to choose between rather than something to agree to. The council's "
    "occupational therapist will come out free and bring the options with them, and the one they "
    "picked themselves is the one they will use.",
    "A hearing aid, a stick and an alarm all say the same thing out loud - that they are older than "
    "they were - and that is the bit being refused. Ask what they would take: something that does "
    "not look medical, only for the parts they find hard, and suggested by somebody other than you.",
)
# The aids that come from a clinic rather than from an occupational therapist: a refusal of these
# is settled by the number on a test or by a shape they like, not by a home visit.
ELDER_CLINIC_REPLIES = (
    "Take them with you and let the optician or the audiologist make the case - the number on the "
    "test is the argument, and it is not yours to make. Frames in a style they like, or an aid that "
    "sits behind the ear instead of in it, is usually what settles it.",
    "Then ask what they would wear or use, rather than what they should: the small ones, the ones "
    "that look like ordinary glasses, the ones that only come out for the television. Book the test "
    "so the answer comes from the person doing it, and go along to the appointment.",
)
ELDER_DOCTOR_REPLIES = (
    "Ring the surgery yourself and describe what you have seen, then ask what they suggest - a GP "
    "can usually find a reason to call them in that a son or daughter cannot. Offer to book it and "
    "go with them; being driven and having somebody in the waiting room makes a difference.",
    "Then do not argue the appointment, argue the one thing that has changed and when it started. If "
    "the trip out is the problem, ask for a phone call instead of a visit, and let the GP ask them to "
    "come in. A no to the surgery is often a no to the journey.",
    "Say what you have noticed and leave the diagnosis to the doctor - what they will not hear from "
    "you is what is wrong with them. A district nurse, a pharmacist or a friend of their own age can "
    "often get them there when a relative cannot.",
)
ELDER_HELP_REPLIES = (
    "Ask what they would take instead of what they will not: one morning a week, somebody to do the "
    "garden, you doing the shopping. The council's care needs assessment is free and it is the door "
    "to all of it, and it arrives as them asking rather than you arranging.",
    "Start with the job they hate rather than the word carer - nobody wants to be looked after, and "
    "plenty of people will take help with the bins, the windows and the bedding. Their GP or Age UK "
    "will suggest it as well, which lands better than it coming from family.",
    "Then find out what the no is really to: a stranger in the house, being watched, or paying for "
    "something they think they can still do. Fix that one and the help becomes a smaller yes - and "
    "say what you will not be able to keep doing, plainly, so it is not a surprise later.",
)

# ...and no "put it back as it was": a car that will not start was never put right in the first
# place, so the undo is an instruction the person cannot follow. Worse is a reason to stop and
# ask, which is true of a pan, a slug, a bill and a car alike.
TRIED_WORSE_ELSEWHERE = (
    "Then stop there and put it back how it was. Something that makes it worse is not a thing to "
    "push through - tell me what it did and we will go a different way.",
    "Stop and leave it alone. Worse is the answer, and it is worth another pair of hands rather "
    "than you carrying on.",
    "Leave it off for now. Worse is a reason to ask, not to persevere - I can take it from here "
    "if you tell me what changed.",
    "Stop, and treat it as the wrong fix rather than one to try harder at: say what happened, so "
    "the next idea is not the same one again.",
)

# The easing has to be the line, not a word in it. "im ok now, where do i get a tetanus jab" asks
# something, "im ok now but i cant stop crying" is not ok at all, and "i feel a bit better, can we
# talk about something else" is a person moving on. So the words the easing itself is made of are
# taken out, together with the thing that was easing (a symptom or a body part), and anything with
# content left in it keeps the thread.
EASING_FILLER = frozenset((
    "i", "im", "i'm", "am", "we", "we're", "were", "it", "its", "it's", "that's", "thats", "that",
    "this", "feel", "feels", "feeling", "felt", "doing", "getting", "a", "an", "the", "bit",
    "little", "lot", "much", "very", "so", "far", "more", "any", "now", "today", "tonight",
    "already", "and", "but", "though", "yeah", "yes", "honestly", "actually", "thanks", "thank",
    "you", "of", "to", "me", "my", "myself", "good", "great", "well", "is", "was", "has", "have",
    "been", "gone", "stopped", "better", "calmer", "calm",
    "alright", "okay", "ok", "fine", "easier", "lighter", "less", "awful", "bad", "s",
    "just", "touch", "lots", "slightly", "way", "easing", "off", "back",
))

# Asking to leave the emergency behind is a good sign, and it is the person's call: the thread
# lets go and the bot says yes rather than answering the easing with more advice.
MOVE_ON_AFTER = (
    "Of course. What would you like to talk about?",
    "Fair enough - what is on your mind instead?",
    "Yes, let's. What would you rather talk about?",
)

# A report that the advice did not work, inside an answer that named the emergency services: the
# advice being reported on *is* the route, so the next move cannot be a lesser one. The pain answer
# ends on "a pharmacist or a doctor can look at it", and handed back after "ring 999" that reads as
# permission to wait - the one reply a frightened person must never get from this bot.
EMERGENCY_NOT_WORKED = (
    "There is nothing left to try at home for this: ring 999 or 911 now if you haven't, and follow "
    "what they tell you.",
    "Don't wait for it to settle. Ring 999 or 911, and tell them exactly what you told me.",
    "Ringing is the thing that works here — 999 or 911 now, and stay on the line with them.",
)

CARE_AFTER = (
    "If it's still worrying you, get it looked at today — a pharmacist or a walk-in centre "
    "can check it faster than waiting.",
    "Keep an eye on it and tell me if anything changes; being seen early beats waiting.",
)

CARE_AFTER_STILL = CARE_AFTER + (
    "Still going on, so don't sit with it: get it looked at today and say how long it has been.",
)

# A care answer names the place to go, and the person's next line is about that answer, not a new
# question: "my chest hurts when i run" is answered "ring 111 or your GP first thing", and "what
# should i do" then got "a pharmacist or a walk-in centre can check it faster than waiting" - a
# different building from the one the bot had just named, and one that does not see a chest. The
# route the answer gave is the one to hand back, so the pools are keyed by it: the words are the
# place, and the number named is the thing the person has to do next.
# The threshold an answer named, being crossed: "now my arm hurts too" after "ring 999 or 911
# straight away if it spreads to the arm or jaw". The reply is the 999 that answer named, in the
# words for a person who has just described the thing they were told to watch for - not the 111
# that the same answer named first, which would send them to bed to wait for the morning.
THRESHOLD_CROSSED = (
    "That is the thing I said to ring 999 for, so do it now: ring 999 or 911 and stay on the "
    "line. Tell them what has changed and when it started.",
    "Ring 999 or 911 now. That is what the answer above said to call for, and this is it - say "
    "what has changed since we spoke and let them talk you through it.",
)

# The next line after that one: the 999 has been said and not yet made, so every line here makes
# the call again rather than stepping down. What was here before was the answer's own route - the
# 111 the same care answer named for the appointment - and "ok i will" after "ring 999 or 911 and
# stay on the line" was answered "111 is still the one to ring": six of twelve third lines in a
# chest thread walked a possible heart attack down to a phone call in the morning (close-pipe on
# #8509). One line always names the number, because this is the pool that answers "what do i say
# to them" and "ok i will", and both are a person about to dial.
THE_CALL_STANDS = (
    "Ring 999 or 911 now, as I said - tell them what has changed since we spoke and stay on the "
    "line until they tell you what to do.",
    "The call is still the thing to do: 999 or 911, now. Say what has happened since this "
    "started, and let them talk you through it.",
    "Make the call now - 999 or 911 - and describe what has changed since we first spoke. Stay "
    "on the line and follow what they say.",
)

CARE_ROUTE_BACK = {
    "111": (
        "Ring 111 today, as I said - they will say how soon it needs seeing, and ring 999 if "
        "anything gets suddenly worse.",
        "111 is still the one to ring: describe it as you did to me and say what has changed.",
    ),
    "gp": (
        "Your GP today, as I said - describe it as you did to me and let them decide how soon.",
        "Ring the surgery when it opens and say what has changed since we spoke; that is the "
        "appointment to be asking for.",
    ),
    # The route back, and nothing about the state of the tooth: the line that follows a dentist
    # answer is as often "it doesnt hurt" or "its not painful" as it is "its getting worse", and
    # this pool answered both with "a tooth that is getting worse tonight is an out-of-hours
    # call" - a claim about a tooth the person had just said was fine. The words here carry what
    # the person has to do next (ring, today, say what has changed) and leave the tooth to them.
    "dentist": (
        "The dentist today, as I said - ring when they open and say what has changed since we "
        "spoke, and ring 111 for the out-of-hours number if it starts to hurt.",
        "Ring the dentist and say what has changed; a broken or aching tooth is seen quickly.",
    ),
    "pharmacist": (
        "The pharmacist as I said - take the packet, or say what you have taken, and ask them to "
        "check it.",
        "Ask the pharmacist, and say what has changed since I first said it.",
    ),
    "walk-in": (
        "A walk-in centre today, as I said - no appointment, and they can look at it properly.",
        "Get to a walk-in centre and say how long it has been going on.",
    ),
}

# ...and the same two lines for an animal. "my rabbit hasnt eaten since yesterday" / "should i take
# him in" was answered "a pharmacist or a walk-in centre can check it faster than waiting": the
# right shape of answer at a building an animal cannot go to. The vet's desk will say on the phone
# whether it needs seeing, which is what the person is asking.
CARE_AFTER_ANIMAL = (
    "If it is still worrying you, ring the vet today - the desk will say on the phone whether it "
    "needs seeing, and asking is usually free.",
    "Keep an eye on it and tell the vet if anything changes; with an animal, being seen early "
    "beats waiting.",
)

CARE_AFTER_ANIMAL_STILL = CARE_AFTER_ANIMAL + (
    "Still going on, so don't wait with it: ring the vet today and say how long it has been.",
)

# A hello a few lines after a burn is still a hello, and the care pools answer it as if the
# person had said nothing about the injury ("keep an eye on it" again). This greets them and
# asks about it, so the thread reads like someone who remembers.
# A hello while the emergency the bot has just answered is still live: "hiya" after a heart
# attack, a fire or a suicide note. It is a greeting and it is not a new subject, so the cheerful
# pool that starts a new day is wrong, and so is saying the emergency instructions again - the
# person has just said hello. It is also not a moment for small talk: someone typing one line
# mid-emergency wants to know the bot is still with them and what still stands, so the hello
# answers the hello and points back at what they were told rather than asking "how are things".
HELLO_STILL_THERE = (
    "Hello. I'm still here - keep doing what the emergency line told you, and tell me if "
    "anything changes.",
    "Hi. Still here, and so is what they told you: stay with it and say if it gets worse.",
    "Hello again. I'm not going anywhere - carry on with what the emergency line said, and tell "
    "me how it is when you can.",
    "Hi. I'm right here. The emergency line's advice still stands, so keep going and say if "
    "anything changes.",
)

# The same hello in a thread where the person is the one in danger. The cheerful pool is wrong
# before it, "are you somewhere safe" is the one question a crisis answer has already asked, so
# the hello asks about company instead: a person on their own tonight is the thing that matters,
# and it is the one part of the safety plan a greeting can carry without repeating the card.
HELLO_WITH_YOU = (
    "Hello. I'm still here, and I'm not going anywhere - is anyone with you just now?",
    "Hi again. Still here. Are you with someone tonight?",
    "Hello. I haven't gone anywhere - is there someone you can be with tonight?",
)

# "how are you" in the middle of an emergency is someone checking the bot is still there, not
# small talk: the chat pool answered it with "Doing well, thanks - what about you?", which is a
# light voice in a serious thread. The answer says it is here and turns the question back.
CARE_HERE = (
    "Still here, and not going anywhere. How are you doing just now?",
    "I'm all right — more use to you than to myself. How are you holding up?",
    "Here, and in no hurry. How are you doing right now?",
)

GREETING_AFTER = (
    "Hello again. How is it doing now?",
    "Hi. Any change since we spoke?",
    "Morning. How is it today?",
    "Hello — how is it holding up?",
)

# The one question a person asks after a first-aid answer: "should i get it seen". It is a
# yes/no about the injury, so it gets a straight answer rather than "it'll probably settle".
CARE_SEEN = (
    "If you're wondering, that's reason enough to have it seen today — a walk-in centre or "
    "a&e will tell you quickly.",
    "Worth having it looked at today: a&e or a walk-in centre can say for certain, and that "
    "beats waiting to see.",
    "Get it seen today — you'll know either way, and nothing about that is a fuss.",
)

# The same question about an animal. "my cat ate a lily" then "should i take her tonight" was
# answered "Worth having it looked at today: a&e or a walk-in centre can say for certain" - the
# right shape of answer, at the wrong building: for an animal the one to ring is the vet, and the
# desk will say on the phone whether she needs to come in tonight. A pet is read from the line and
# from the thread, because the question about it does not name the animal a second time.
CARE_SEEN_ANIMAL = (
    "Ring the vet now and say what she got into and when. They will tell you on the phone whether "
    "she needs to come in tonight, and that is usually free to ask.",
    "Yes - the vet is the one to ask, today rather than tomorrow. Say exactly what it was and how "
    "long ago, and ask the desk whether she should be seen tonight.",
    "Ring the vet and describe it, and ask whether she needs to be seen tonight. With an animal it "
    "is the only place that can say for certain.",
    "Take her, or ring first and ask - a vet would rather hear it tonight than find out tomorrow. "
    "Say what she ate and when.",
)

# The other question a person asks in a care thread, and it is not about the injury at all:
# whether to go and be with the person tonight.
#
# "my mum is in hospital" then "she fell" then "should i go up tonight" was answered "Worth
# having it looked at today: a&e or a walk-in centre can say for certain" - the injury pool
# reading "go up" as "go and get it seen", which tells someone to have themselves checked when
# they asked about a visit. The bare "go" in CARE_SEEN_ASKS is needed for "should i go" after a
# bad cut, so the visit is caught first, by its own verbs, and a line naming a medical place
# ("should i go up to a&e") stays with the injury.
CARE_VISIT = (
    "Go if you can. Being there settles you both, and the questions are easier to ask in "
    "person than down a phone.",
    "Yes, go up. A short visit tonight is worth more than a long one next week, and you can ask "
    "the question in person.",
    "Go, even briefly. Sitting with them for half an hour beats a long visit you put off.",
)

# The ward only exists when somebody is in one. A visit question turns up without a hospital
# anywhere in the thread - "i cut my hand badly" then "should i go over to see her" is a visit to
# a person's house - and "ask whoever is on the ward what happens tomorrow" then invents a bed
# and a nurse that nobody has mentioned. So the ward wording is its own pool, chosen only when
# the line or the last few turns name a place that keeps someone in.
CARE_VISIT_WARD = (
    "Go if you can. Being there settles you both, and it is easier to catch the ward nurse in "
    "the evening to ask what the plan is.",
    "Go, even briefly. Take a notebook and ask whoever is on the ward what happens tomorrow "
    "before you leave.",
)

# The visit is movement towards somebody, so somebody has to be there to go to: "should i go over
# to see her", "should i go up tonight" after "my mum is in hospital". Either word makes it the
# visit; without one the line is about the speaker's own movement and the care pools answer it.
VISIT_PRONOUNS = frozenset("""he she they him her them his hers their mum mums mam dad dads
    mother father son daughter gran granny nan grandad grandma grandpa sister brother""".split())

# A nod mid-emergency gets a hold, worded so it reads right whether the person is hurt or
# someone with them is: nothing here assumes a "them".
# The one question people ask after a burn: whether to put something on it ("butter",
# "toothpaste", "ice", "cream") and whether to pop the blister. Both have a straight answer, and
# both are the kind of thing a knowledge entry can match on a word ("oven", "butter") and answer
# about something else entirely, so the thread holds and this is what it says.
BURN_AFTER = (
    "Nothing on it: butter, toothpaste, cream and ice all hold the heat in or set up an "
    "infection. Cool running water for twenty minutes is the treatment, then cover it loosely "
    "with cling film or a clean non-fluffy cloth.",
    "Don't put anything on a burn — not butter, not cream, not ice. Twenty minutes under cool "
    "running water, then a loose clean dressing; painkillers help while it cools.",
    "Cool water only, I'm afraid. Grease, toothpaste and ice are the three things that make a "
    "burn worse; twenty minutes under the tap, cover it loosely, and get it seen if it blisters "
    "or is bigger than your palm.",
)

BURN_BLISTER = (
    "Leave the blister whole — popping it is how a burn gets infected. Keep it covered loosely "
    "and get it seen if it is bigger than your palm, on the face or hands, or the skin is white "
    "or charred.",
    "Don't pop it. A blister is a sterile dressing of its own; cover it loosely and let it settle, "
    "and have a burn that blistered looked at today.",
)

# The question after the answer. Once the bot has said what to do, most people ask about the
# advice itself rather than the injury: how long it takes, whether it has to be cold, whether to
# do it again, and what to do if it does not work. `_keeps_thread` lets those go - "is ten minutes
# enough" has a subject word of its own, so it reads as a new subject and the line is met with
# "search online", which is the worst thing to say to someone standing over a sink. The pools are
# per shape rather than per injury, so a burn, a cut and a nosebleed all get the same true thing.
ADVICE_TIME = (
    "Keep going to the end of the time. That part is doing the work, and stopping early is "
    "usually what makes it start again.",
    "Longer than it feels like it should be, I know. The whole of the time is what settles it; "
    "cut it short and it often comes back.",
    "Give it the full time rather than a guess. It is a dull twenty minutes standing there, and "
    "it is the bit that matters most.",
)

ADVICE_COOL = (
    "Cool is enough. It is the running water and the time that do the work, not how cold it is - "
    "cold enough to numb it is too much.",
    "Lukewarm is fine. Keep it running over the area rather than sitting in a bowl, and give it "
    "the whole of the time.",
)

ADVICE_AGAIN = (
    "You can go back to it. If it starts again, the same thing for the same time is right - that "
    "is repeating the answer, not overdoing it.",
    "Yes, and doing it twice is not a mistake. The time in the answer is a round rather than a "
    "limit.",
)

ADVICE_WORSE = (
    "Then that is your cue to get it looked at rather than wait longer - the time in the answer "
    "is how long to give it, not how long to put up with it.",
    "If it has not settled by the end of that time, stop waiting and have it seen today. Ring 111 "
    "if you are not sure where to go.",
)

ADVICE_COOL_WORDS = ("water", "cool", "cold", "burn", "scald", "soak", "sink", "tap")

HOLD_AFTER = (
    "Still here. Keep the line open and follow what they tell you.",
    "I'm with you — stay put and let the operator talk you through it.",
    "Right with you. Stay where you are; the crew are on their way.",
)

# The hold for a thread where nobody has been called: a burn under the tap, a cut finger, a
# sprained ankle. Every line above assumes a call - "the operator", "the crew are on their way" -
# so a reaction in a care thread that borrowed them promised help that was not coming.
STILL_HERE_AFTER = (
    "Still here — keep an eye on it and say if anything changes.",
    "Right here with you. Tell me if it gets worse or anything changes.",
    "I'm here. Take it slowly, and say if anything changes.",
)

# A done report is not a call. "i sorted it" is the person saying they think the thing is
# handled, and it says nothing about anyone having been rung, so the two lines above that promise
# an operator or a crew are the bot inventing one: "i took an overdose" / "i sorted it" answered
# "Keep the line open and follow what they tell you" tells a person nobody is talking to to follow
# them (chief-umbrella and fancy-penguin, #7230). What the advice asked for is still owed, so this
# pool asks for it and holds.
SORTED_AND_NO_CALL_YET = (
    "Stay on this with me: get it checked anyway, and say what happened and how long ago, even if "
    "you feel fine.",
    "Glad it is dealt with. Tell someone you trust what happened, and keep the number handy.",
    "Good to hear. I am here \u2014 ring them back if anything changes, and do not keep it to "
    "yourself tonight.",
)

# The line that says a helpline was rung in a thread whose last answer asked for 999. The person
# has done something kind for themselves and the emergency is still there: the samaritans will not
# send an ambulance, and "the crew are on their way" would be the bot inventing one.
HELPLINE_NOT_AN_AMBULANCE = (
    "That was worth doing, and nobody is coming from a helpline: ring 999 now and stay where you "
    "are until they do.",
    "Good that you rang them, and this still needs 999 — ring for an ambulance now, rather than "
    "waiting to see how it goes.",
)

WITH_YOU_AFTER = (
    "Good, that helps. Keep them with you and keep the line open.",
    "That's good to hear. Two of you is better than one \u2014 say if anything changes.",
    "I'm glad you're not on your own with it. Stay together and keep the line open.",
)

# The end of it, once the person says the emergency is over: the fire is out, the medics are
# there, the bleeding has stopped. The 999 line a third time would be the bot not listening.
RESOLVED_AFTER = (
    "Good — that's the main thing. Keep an eye on it for a bit, and ring again if anything "
    "changes.",
    "Glad to hear it. Stay with it a little longer, and get help straight away if it starts "
    "again.",
    "That's the important bit done. Look after yourself now, and get seen if anything flares "
    "up.",
)

# The end of it, said by a person who has been told to ring 999: "i think im fine", "im fine now
# honestly". That is the same words as a real close and not the same news - nobody has been, and
# a heart attack told to ring an ambulance an hour ago does not stop being one because the pain
# has eased. The close is kept for a thread where the call was actually made; this pool hears the
# good news and holds the call.
THE_CALL_STANDS_ANYWAY = (
    "Good to hear it, and it does not change the call: what you described is why 999 is the "
    "number, and feeling fine for a minute is not the check. Ring them now and say it as you "
    "said it to me.",
    "I know it feels fine now, and that is worth something - it is not the thing you were told "
    "to ring 999 for. Make the call and tell them what you told me; they would far rather hear "
    "it early.",
    "Glad it has eased. Ring 999 anyway and let them decide - an easing is not the same as being "
    "looked at, and they can hear what I cannot.",
)

CRISIS_AFTER_THEM = (
    # The card that opened the thread has asked the plain question already, so these lines move
    # the carer on rather than saying it again: what to do tonight, who to ring, and that the
    # awkwardness of saying it out loud is not the thing to worry about.
    "Stay with {who} tonight if you can, and say out loud that you are glad {subj} told you - "
    "the saying it badly matters far less than the staying.",
    "Take anything {subj} could take out of the room, keep {who} company tonight, and ring 116 "
    "123 together rather than for {obj}: the crisis line talks to the person and to the one "
    "holding on with them.",
    "If there is any chance {subj} {be} in danger tonight, that is 999 or 911 - and 116 123 is "
    "the crisis line either of you can ring, at any hour, with no wrong time to use it.",
    "Keep {who} close tonight and ask {obj} again tomorrow. Ringing 116 123 with {obj} there is "
    "easier than ringing it for {obj}, and it costs nothing to do it before it gets worse.",
    # For the question underneath the line - "is she going to be ok" - the honest answer is that
    # nobody can say, and then the thing that does help tonight.
    "I can't promise how it will go, and nobody can. What helps tonight is taking anything {subj} "
    "could take out of the room, staying with {who}, and ringing 116 123 together rather than "
    "for {obj}.",
)
# The easing of a crisis that was somebody else's: "she says shes fine now" is their good hour,
# not the end of it, and the reply belongs to the person keeping an eye on them.
CRISIS_BETTER_THEM = (
    "Glad to hear it. Keep an eye on {obj} rather than taking it as the end of it, and ask {obj} "
    "again tomorrow - feeling better for an evening is not the same as being out of the woods.",
    "That's a relief. Stay near {who} this evening if you can and check in tomorrow; 116 123 is "
    "there for the two of you if it turns again.",
    "Good. Say out loud that you are glad, and ask {obj} tomorrow how {subj} {be} doing - one "
    "good hour is not the same as a good week.",
)
# And the easing after something swallowed, which the self pool keeps on the emergency line
# (NO_RELIEF): the same instruction, sent to the carer, about their person.
EMERGENCY_BETTER_THEM = (
    "Feeling better is not the same as being out of the woods: get {obj} seen today and stay with "
    "{who} until somebody has looked {obj} over.",
    "Stay with {who} and get {obj} seen today. With something swallowed the harm can go on for "
    "hours after it starts to feel easier.",
)
# The end of it, said about somebody else: "shes fine now", "hes stopped". Written without a
# crisis line, because the same close is right after a burn or a bleed on another person.
RESOLVED_AFTER_THEM = (
    "Good - keep an eye on {obj} for a bit, and say if anything changes.",
    "Glad to hear it. Stay with {who} a little longer, and get help straight away if it starts "
    "again.",
    "That's the important bit done. Look after {obj} now, and get {obj} seen if anything flares "
    "up.",
)

# A reaction after the end of it: the crew are already there, so nothing may say they are on
# their way, and "that's the hardest part over" fits whoever was hurt.
AFTER_RESOLVED = (
    "That's the hardest part over. Tell me if anything changes from here.",
    "It is still a lot to hold. Take it slowly, and say if anything gets worse.",
    "Fair enough — none of that was easy. Look after yourself now.",
)

# The person has already done the one thing the bot asked: hold with them instead of asking
# again. Past tense only, so "should i call an ambulance" is still a question to answer.
# A thread that already names a call: the advice asked for 999, or the bot's own line did.
CALL_WORDS = ("999", "911", "112", "111", "emergency line", "call handler", "ambulance")

THANKS_WORDS = frozenset(("thanks", "thank", "thx", "ta", "cheers", "appreciated"))

# Inside an emergency the person themselves is often the one who needs an answer: "i'm scared",
# "i can't stop shaking". The practical pool reads cold to that, so a line about the speaker's
# own fear gets company instead - still careful, never less urgent.
# No "them" in these: the frightened person may be the one who is hurt ("i cut my hand and
# i cant stop shaking") or the one standing next to them, and the pool has to read right for
# both. A crisis thread never comes here - see the order in _after_safety.
AFRAID_AFTER = (
    "It's alright to be scared, and alright to cry — that's what something like this does to "
    "people. Keep following the emergency line; you're doing the right thing.",
    "Scary, and you're doing it. Keep going with what the emergency line tells you, and say if "
    "anything changes.",
    "Frightening, and completely normal. Keep talking and stay with the emergency line — ring "
    "back the moment anything changes.",
)

CRISIS_WORDS = ("crisis", "116 123", "988", "samaritans", "helpline", "stay with you")

SAFETY_WORDS = ("999", "911", "112", "emergency", "operator", "ambulance", "paramedic",
                "fire brigade", "fire service")

# Words that keep a line inside an emergency the bot has just answered: the emergency itself,
# the injury, the people in it, and the practical questions people ask mid-crisis.
CARE_WORDS = frozenset("""
    safe safely unsafe outside out stairs stair lift door window smoke fire fires flame flames
    alarm spread spreading burn burned burning bleed bleeding blood cut cuts wound bandage
    dressing plaster pain painful hurt hurts hurting aching sore tender stinging smarting
    stiff swollen swelling bruised numb infected infection throbbing
    aspirin paracetamol ibuprofen painkiller painkillers antihistamine
    worse still soak soaking soaked wait waiting
    ambulance paramedic police operator emergency 999 911 112 doctor hospital nurse gp
    stitches stitch tetanus dressing nurse nhs walk-in centre clinic
    checked check conscious breathing breath awake faint dizzy vomit vomiting sick throwing
    collapsed collapse seizure stroke heart chest epipen inhaler insulin medicine dose
    cpr defib firefighter neighbour neighbor flat floor basement roof shaken shaking scared he she him
    her them they their there call calling rang ring
""".split())

# The weak half of that vocabulary: a pointer, not the incident. "should i call the plumber
# about the boiler" and "is there anything good on tv tonight" are ordinary lines that happen to
# carry one, so these words hold the thread only while the line brings no topic of its own.
# The injury itself, still going: "it's still stinging an hour later", "it's throbbing". A line
# that reports the damage needs the same thread even when some word of it reads as a topic of
# its own ("hour" is maths-and-numbers), so these are read before the line's own topic is.
CARE_HURTS = frozenset("""
    sting stings stinging stung throbs throbbing throbbed ache aches aching ached sore tender
    hurts hurting hurt pain painful swollen swelling bled blister blistered blisters
""".split())

CARE_POINTER = frozenset("""
    there call calling rang ring still wait waiting check checked out outside
""".split())

# The words that say the line is still the incident itself: a burn, a cut, smoke. A house fault
# said alongside one of these is the accident, not a job for a tradesman.
CARE_INJURY = frozenset("""
    burn burned burning burnt bleed bleeding blood cut cuts wound blistered
    hurts hurting hurt pain painful stinging sting sore swollen swelling smoke fire fires flame
    flames alarm ambulance hospital
""".split())

# The people in an emergency are not the emergency: "thanks, they came" is a close. They are in
# CARE_WORDS so a line naming them keeps the thread; this only stops a pronoun being read as a
# new incident when the line is otherwise a thanks.
CARE_PRONOUNS = frozenset("he she him her them they their it its".split())

# A thanks that also says the emergency is over is a close: "thanks, the doctor came", "the
# bleeding stopped", "its fine now". Only the ongoing part of a thanks keeps the thread.
CARE_RESOLVED = frozenset("""
    stopped stop stopping fine better okay ok came come gone settled healed healing cleared
    improving
""".split())

# A resolved word with a negator in front is not resolved: "it hasnt stopped" and "its not
# fine" are the emergency still going on, and they must not get the warm close.
CARE_NOT_RESOLVED = NEGATORS

ONGOING_WORDS = frozenset("still worse wont cant cannot keeps keep getting more again".split())

# Written with a symbol or two words, so the split words above never match: "a&e" reads as
# "a" and "e". A line naming one of these is still about the emergency.
# A reaction is how a person answers inside an emergency ("im crying", "im scared",
# "im panicking"). It must not be answered as a feeling on its own: a module with a topic of
# its own would take the turn and the thread would be lost by the next line.
REACTION_WORDS = frozenset("""
    crying tears scared afraid fear fearful terrified frightened dreading dread panicking
    shaking shaky shaken trembling wobbly woozy sobbing hyperventilating shock
    dizzy lightheaded faint weak drained sick numb helpless hopeless useless
""".split())

CARE_PHRASES = ("a&e", "a & e", "a and e", "walk-in", "walk in", "minor injuries")

# Mid-emergency people check the bot is still with them: "can you hear me", "you there?".
# That is not a change of subject, so it must not end the careful thread.
# Words that carry no subject: a question made only of these is still about the emergency.
GENERIC_WORDS = frozenset("""
    happen happens happened happening now long take takes last time next else doing going
    mean means ok okay fine right thing anything something about it that this then there
""".split())

# The words a line uses to ask, or to be polite, rather than to name one: "i dont know what to do"
# is the person asking the emergency for the next step and "ok thanks" is them closing it, and
# neither is a new subject. The last resort in `_keeps_thread` reads a line made of these words as
# still the thread, so the close a care thread gets is the warm one it had.
ASKING_WORDS = GENERIC_WORDS | frozenset("""
    i im me my we us our you your he she they them their his her its it is am are was were be
    been being and or but so if to of in on at for with from by as not no never dont doesnt
    didnt cant cannot what whats which who whom whose how why when where do does did know think
    mean say tell want need get go going have has had will would can could should shall may
    might just still yet any some else thing things happening happen right ok okay yeah
    thanks thank thx cheers ta please sorry mate lovely great good
""".split())

THREAD_TURNS = 12  # how far back a careful thread looks for the emergency that started it

FALLBACK_MODULE = "greeting"  # this file's own module; the game's name for the fallback

# What someone gets when they check the bot is there and nothing else answers: being told to
# search online would be nonsense, so it says it is here and waits.
# Words left over once the presence check is taken out: "can you hear me *now*" is still a
# presence check, "can you see me *on saturday*" is a request for something.
PRESENCE_LEFTOVER = frozenset("""now at all ok okay please hello hey hi again still then just
    mate pal buddy good right fine there here""".split())

PRESENT = (
    "Yes — I'm here. Go on.",
    "I'm here, listening. Keep going.",
    "Yes, I can hear you. What's happening?",
    "Still here. Take your time.",
)

ACKS = frozenset((
    "ok", "okay", "k", "cool", "nice", "sure", "yeah", "yep", "yes", "no", "nah", "nope",
    "lol", "haha", "ha", "mm", "hmm", "right", "fair", "same", "great", "good", "true",
    "exactly", "indeed", "thanks", "thx", "ta",
))

# The nods that agree with the line before them and name nothing of their own. They matter in a
# live emergency, where the last-resort test in `_keeps_thread` reads a word of more than three
# letters as the line's own subject: "same" is not a subject, it is somebody saying it is the same
# for them, which is the thread going on (see `_keeps_thread` in fallback.py). "ok" and "yeah" were
# never caught by that test because they are too short to count as a subject.
AGREEMENTS = frozenset(("same", "ditto", "likewise", "snap", "seconded", "agreed"))

IDENTITY = ("are you a real person", "are you real", "are you human", "are you a human",
            "are you a bot", "are you a robot", "are you an ai", "are you ai",
            "who are you", "what is a chatbot", "are you a chatbot",
            # "introduce yourself" is the same question as "tell me about yourself" and "who
            # are you", and it was filed away with the nod at the fallback's echo.
            "introduce yourself")

MEMORY = ("do you remember", "can you remember", "do you know what we talked",
          "what did we talk about", "remember what we", "remember me", "remember us")

HELP = ("what can you help", "what can you do", "how can you help", "what do you do",
        "what kind of things can you help", "what are you for", "how do you help",
        "what can i ask you", "what are you good at")

HELP_TOPIC = {
    "cooking": ("Cooking is my sort of thing - what have you got in?",
                "I can help with cooking - what are you making, and what's in the fridge?"),
    "food-and-drink": ("Food I can help with - what are you in the mood for?",
                       "Tell me what you fancy eating and I'll help you get there."),
    "home-and-diy": ("I can help with the house - tell me what it's doing and what you've tried.",
                     "Home jobs I can help with - what's the trouble?"),
    "money": ("Money I can talk through - what are you weighing up?",
              "I can help with money questions - what's the decision?"),
    "health": ("I can talk through everyday health - what's going on?",
               "Tell me what's bothering you and I'll say what would help."),
    "technology": ("Tech I can help with - what's it doing?",
                   "I can help with a device - what's wrong with it?"),
    "work": ("Work I can talk through - what's the situation?",
             "Tell me what's happening at work and I'll help you think it through."),
    "geography-and-travel": ("Travel I can help with - where are you thinking of going?",
                             "Tell me the trip and I'll help with the practical bits."),
    "family-and-parenting": ("Family things I can help with - what's going on?",
                             "Tell me what's happening with the family and I'll help."),
    "pets": ("Pets I can help with - what's going on with them?",
             "Tell me about the animal and what's worrying you."),
    "garden-and-plants": ("The garden I can help with - what are you growing?",
                          "Tell me what the plants are doing and I'll help."),
    "sleep": ("Sleep I can help with - what's happening at night?",
              "Tell me what your nights are like and we'll find the next step."),
    "fitness": ("Fitness I can help with - what are you training for?",
                "Tell me what you're doing and where it's sticking."),
    "school-and-study": ("Study I can help with - what are you working on?",
                         "Tell me the subject and what's hard about it."),
    "shopping": ("Shopping I can help with - what are you choosing between?",
                 "Tell me what you're after and I'll help you narrow it down."),
    "entertainment": ("Films and TV I can help with - what are you in the mood for?",
                      "Tell me what you've liked lately and I'll suggest something."),
    "sport": ("Sport I can help with - what are you watching or playing?",
              "Tell me the match or the game and I'll help."),
    "language-and-writing": ("Words I can help with - what are you writing?",
                             "Tell me what you want to say and I'll help you phrase it."),
    "feelings": ("I can sit with the feelings - tell me what's going on.",
                 "Tell me what's been happening and how it's sitting with you."),
    "maths-and-numbers": ("Numbers I can do - what are you working out?",
                          "Tell me the sum or the figure and I'll work it through."),
}

HELP_TOPIC_ANY = ("Tell me what you're working on and I'll help where I can.",)

# What may follow the offer and still leave the line a question about the bot: nothing, or a
# word that carries no subject of its own. "what else can you do about my leaking boiler" and
# "what other things can you do for anxiety" name something to do, so they are not this ask -
# the capability list ignores the boiler and the anxiety, and the shrug is no better.
HELP_TAIL = frozenset("with me us for about at around to it here there then now anyway though "
                      "please thanks honestly really so and".split())

# A favourite asked for with "have" in front ("do you have a favourite food", "have you got a
# favourite show") is the same question as "what's your favourite food", and the table is keyed by
# the thing rather than by the frame: without these the favourite entry was never reached and the
# line went to the search hedge, or to a card that answered a different question.
OPINION_ASKS = ("do you like", "do you love", "do you prefer", "do you reckon", "you prefer",
                "your favourite", "your favorite", "have a favourite", "have a favorite",
                "have you got a favourite", "have you got a favorite",
                "which do you", "would you rather",
                "in your opinion", "your opinion", "your take", "what do you think about",
                "what do you make of", "your thoughts on", "cats or dogs", "dogs or cats",
                "best season", "favourite season", "favorite season", "watch much tv",
                "watch a lot of tv", "watch much telly")

TASTES = (
    (("cats or dogs", "cat or dog", "dogs or cats", "dog or cat"),
     ("Dogs by a whisker: company on a walk beats almost anything. Cats are the easier "
      "flatmate.",
      "Dogs for me, though I would not turn down a cat that ignored me politely.")),
    (("tea or coffee", "coffee or tea"),
     ("Coffee in the morning, tea after four: two different jobs.",
      "Tea, if I had to choose one. Coffee is a tool, tea is a pause.")),
    (("best season", "favourite season", "favorite season", "best time of year"),
     ("Early autumn: warm enough to sit outside, dark early enough to stay in, and no pressure "
      "to be doing something.",
      "Late spring. Everything is green and nobody has started complaining about the heat yet.")),
    (("morning or evening", "morning or the evening", "evenings or mornings"),
     ("Morning, by a mile. The day is still yours then.",)),
    (("recline",),
     ("Recline it, but only on a long flight, and check behind you first. A short daytime hop, "
      "no.",)),
    (("pineapple",),
     ("On pizza, yes. Fruit and cheese is not the crime people make it out to be.",)),
    (("toilet roll", "toilet paper"),
     ("Over. It hangs better and you can see how much is left.",)),
    (("book or film", "film or book", "book or the film"),
     ("The book first, always; then the film can only be a bonus.",)),
    (("favourite book", "favorite book", "best book"),
     ("A collected volume of a newspaper column I read in the bath: short pieces are easy to "
      "start and easy to put down.",)),
    (("favourite film", "favorite film", "best film", "favourite movie", "favorite movie"),
     ("Anything where people mostly talk in kitchens. A plot is optional; good company is not.",)),
    (("favourite food", "favorite food", "best food"),
     ("Roast potatoes, and I am not going to pretend otherwise.",)),
    # "what's your favourite thing to cook" is the same question said with a verb instead of a
    # noun, and the table only knew the noun: the line fell to "no strong view on that one",
    # which is the shrug for a question with no answer rather than for one with a taste behind
    # it. A doing-word is read as the thing done, so cooking is food and reading is books.
    (("favourite thing to cook", "favorite thing to cook", "favourite thing to make",
      "favorite thing to make", "favourite recipe", "favorite recipe", "best thing to cook",
      "favourite thing to eat", "favorite thing to eat"),
     ("One pan and no recipe: a traybake, a frittata, whatever is in the fridge going soft. "
      "Less washing up, more eating.",
      "Sausages in a tin with onions and apples, on a cold day. Nothing clever, and it works "
      "every time.")),
    (("favourite thing to read", "favorite thing to read", "favourite author",
      "favorite author", "favourite writer", "favorite writer"),
     ("Short things I can pick up and put down: a newspaper column, an essay, a book of letters.",
      "Old advice books - cookery, gardening, how to fix a bike. They assume nothing and they "
      "are usually right.")),
    (("favourite colour", "favorite color", "favourite color", "favorite colour"),
     ("Green, the sort that looks grey in a cold light.",)),
    (("favourite city", "favorite city", "best city"),
     ("Whichever one I can walk across in an afternoon.",)),
    (("favourite animal", "favorite animal", "best animal"),
     ("Herons. They stand in the rain looking unbothered, which I admire.",)),
    # The everyday favourites people actually ask, each of which used to get either the search
    # hedge ("do you have a favourite show": no table entry, so the reading stood down) or a shrug
    # meant for a choice ("I don't mind either way" for "who is your favourite actor"). A friend
    # answers these with a taste and a reason, which is the one thing the bot can say that the
    # knowledge base cannot.
    (("favourite show", "favorite show", "favourite series", "favorite series",
      "favourite tv show", "favorite tv show", "favourite tv programme",
      "favorite tv program", "favourite programme", "favorite program",
      "favourite thing to watch", "favorite thing to watch", "watch much tv",
      "watch a lot of tv", "watch much television"),
     ("Something slow and British where not much happens for a while, and then everything does: "
      "*Detectorists* for the first, *Happy Valley* for the second.",
      "The same few comedies on repeat. *Peep Show* is still the one I would put on now.")),
    (("favourite actor", "favorite actor", "favourite actress", "favorite actress"),
     ("Olivia Colman. She does more with one look than most people manage with a speech.",
      "Anyone who can say a whole paragraph with their face. Olivia Colman, if you make me pick.")),
    (("favourite song", "favorite song", "favourite album", "favorite album",
      "favourite band", "favorite band", "favourite music", "favorite music",
      "favourite singer", "favorite singer", "what music do you like"),
     ("*Rumours*, still. It is the one album where every song is the good one.",
      "Anything with a bit of swing to it. Loud is fine, clever is optional.")),
    (("favourite drink", "favorite drink"),
     ("Tea, and I would rather not count how many. Coffee is a tool, tea is a pause.",)),
    (("favourite day", "favorite day", "best day of the week"),
     ("Saturday morning, before anyone needs anything. The whole weekend is still ahead.",)),
    (("favourite time of day", "favorite time of day", "best time of day"),
     ("Early morning, just after the kettle. Nobody wants anything from me yet.",)),
    (("favourite biscuit", "favorite biscuit", "favourite cookie", "favorite cookie"),
     ("A digestive, and I will not be talked out of it.",
      "Shortbread. Plain, buttery, gone in two bites.")),
    (("favourite thing to talk about", "favorite thing to talk about",
      "favourite thing to chat about", "favorite thing to chat about"),
     ("Whatever the person has just brought me. The best part of a conversation is finding out "
      "what somebody actually cares about.",
      "Small practical problems. There is nearly always something useful to say about a kettle "
      "that will not boil.")),
    (("favourite thing about your job", "favorite thing about your job",
      # The same question with "about" in front of the thing, which is how most people say it:
      # "what do you like about your job" was answered "I don't mind either way. Tell me which
      # you'd pick and I'll argue the other side for fun" - a shrug at a choice nobody offered -
      # and "whats the best thing about your job" reached the search hedge.
      "like about your job", "like about the job", "like most about your job",
      "best thing about your job", "best thing about the job", "best bit about your job",
      "best bit of your job", "good thing about your job", "love about your job",
      "do you like your job", "do you like what you do", "do you enjoy your job"),
     ("The moment a question turns out to have a good answer after all. That is most of the job.",
      "People telling me things they have not said to anyone else yet. I try to be worth it.")),
)

# A favourite the table above has no taste for. It is not the choice shrug ("I don't mind either
# way"): nobody asked which of two things the bot prefers, they asked what it likes, and an honest
# "no favourite" that asks back is an answer where "I'm easy on it" is a dodge.
FAVOURITE_GENERAL = (
    "No proper favourite, if I am honest. What is yours?",
    "I have never managed to pick just one. What would you put first?",
    "I do not have one I would defend. Tell me yours and I might borrow it.",
)

# The word that makes a question one about a favourite rather than about a choice between two
# things on the table.
FAVOURITE_WORDS = ("favourite", "favorite")

TASTE_GENERAL = (
    "No strong view on that one, honestly. What's yours?",
    "I'm easy on it — it's not a hill I'd argue from. What do you make of it?",
    "I don't mind either way. Tell me which you'd pick and I'll argue the other side for fun.",
)

PICK_ONLY_WORDS = frozenset("""
    a an the and but so or if to of at on in with about between for from
    what whats which who whom where when why how would will shall should could can do does did
    you u ya your you're ur i me my we us our it its that this these those there
    be been being is are was were
    pick picking choose choosing choice get getting buying buy take taking go going
    suggest suggestion suggestions recommend recommendation recommendations prefer rather
    like want looking look think reckon say said
    one ones thing things anything something nothing stuff else instead again too also then
    now next first just ok okay well honestly really actually any some got please
    best good better more
""".split())

# One line names the option, and the note is what tilts the pick towards it.
MY_PICK_NOTE = (
    "I'd go *{name}* — {note} is more my thing.",
    "Honestly, *{name}*: {note} is what I'd go for.",
    "I'd take *{name}*, out of those — {note} is the draw for me.",
)

MY_PICK = (
    "I'd go *{name}*, out of those.",
    "Honestly, *{name}*. Any of them would do, but that's my pick.",
    "I'd take *{name}* myself.",
)

# Nothing on the table to pick from: ask what is on it. A pick with no options is not a taste
# to give ("My pick would be the one you'd choose in ten seconds" was a riddle), and the person
# who asks "what would you get" with nothing said yet has a list in their head. Only a pick is
# answered this way: "what would you suggest" with nothing on the table is asking for advice
# about their situation ("my back hurts"), and that is not this pool's question.
MY_PICK_ASK = (
    "Depends what we're choosing between — what's on the list?",
    "Tell me the options and I'll say which I'd take.",
)

# The modules whose answer is care rather than information, and the ones whose answer is a nod or
# a continuation of the bot's own: a pick waits for neither, it is not the reply to care.
CARE_MODULES = frozenset(("safety", "urgent", "loss", "grief"))

QUIET_MODULES = frozenset((FALLBACK_MODULE, "chat"))

# The reply names the side the person named, because "the second one" is a count of halves, not a
# thing: "at the people are nicer in the other" is only answered by picking the people. No reason
# is offered with it - a reason picked off the contrast ("you can change the other later") is a
# claim about their case that the bot cannot check, and it was untrue of a flat's distance.
TRADE_OFF_LEAN = (
    "I would take {side}.",
    "My pick is {side}.",
    "Take {side}.",
    "I would go with {side}.",
)

# A choice the bot has no taste about still gets an answer, and which answer depends on what is
# at stake. A dinner, a drink or an evening in is a light choice: a friend leans one way and says
# it does not matter much, instead of handing the decision back. A repair, a purchase, a booking
# or anything you cannot easily undo is a real decision: there the honest move is to name what
# decides it, so the person can weigh it themselves. Both pools are keyed off `CHOICE_STAKES`.
CHOICE_LIGHT = (
    "Go with whichever you'd be happier with in ten minutes — and don't spend long on it, "
    "both are fine.",
    "I'd take your first thought there. You already know which way you're leaning.",
    "Either works, so take the one that's less fuss.",
)

# A light choice names two things, so the honest answer is a side and a shrug, not the decision
# handed back: "pizza or curry tonight", "wine or beer with dinner", "text him or call" and
# "chocolate or crisps" all got "Toss a coin and see if you're disappointed with how it lands",
# which is the one reply STYLE.md rules out — it says nothing, it would fit any line, and it asks
# the person to make the choice the bot was asked to make. The bot may have tastes, so it takes a
# side. The side is fixed by the same seed as the wording (same line, same reply), and the other
# side is only ever quoted, because "if you were hoping I'd say 'call'" is grammatical whatever
# the person typed - "call" and "curry tonight" and "beer with dinner" all sit in the same frame.
CHOICE_LIGHT_PICK = (
    "{pick}. If you were hoping I'd say \"{other}\", then you've decided already.",
    "{pick}. I wouldn't spend another minute on it — both work.",
    "{pick} — that's the one I'd take, and either is fine.",
    "{pick}. I'd take that and not think about it again.",
)

# A medicine is not a light choice: "paracetamol or ibuprofen" are not interchangeable and
# "both are good" is the one thing the bot must not say. Nor is a treatment. Handing these back
# to the generic pool shrugs, so they get the one move that is always right — ask the person
# whose job it is, and say why that is not a dodge.
# Talking therapy is not a medicine: a pharmacist cannot weigh it, so a choice that includes
# one side of it is not the pharmacist's question.
CHOICE_THERAPY = {"therapy", "therapist", "counselling", "counseling"}

CHOICE_HEALTH = {
    "paracetamol", "ibuprofen", "aspirin", "codeine", "naproxen", "co-codamol", "meds", "med",
    "medicine", "medicines", "medication", "medications", "tablets", "tablet", "painkillers",
    "painkiller", "antibiotics", "antibiotic", "antidepressants", "statins", "prescription",
    "dose", "dosage", "therapy", "therapist", "counselling", "counseling",
}

# Two people are not two flavours. "my mum or my dad for christmas" read as a light choice
# answers "My dad for christmas. I'd take that and not think about it again" — a verdict on
# somebody's parents, in the words for a crisp flavour. A pick between people is theirs, and the
# only honest thing a friend adds is the question that decides it.
CHOICE_PEOPLE = frozenset("""
    mum mom mam mummy mother dad daddy father parents parent sister sisters brother brothers
    son daughter kids children child gran granny nan nana grandma grandad grandpa aunt aunty
    uncle cousin cousins nephew niece family stepmum stepdad inlaws boyfriend
    girlfriend partner husband wife fiance fiancee ex flatmate housemate
""".split())
# "in" and "law" used to sit in that set, because "mother in law" was written out as three words.
# A set of names is read one word at a time, so those two words made anything with "in" a person:
# "is the tide in or out", "shall we eat in or out" and "stay in or out tonight" all got "Can't
# pick between people for me and you". "Mother in law" is in the set by "mother" already, and
# anyone who writes it out in full is still read as a person.

CHOICE_BETWEEN_PEOPLE = (
    "Can't pick between people for me and you - you know them and I don't. Who would you be "
    "sorrier to miss?",
    "That's yours to call: no wrong answer, and I'm not going to rank people for you. Who would "
    "you rather be with?",
    "Not one I'd choose for you, sorry. Whose reaction are you dreading more?",
)

CHOICE_PHARMACIST = (
    "Worth asking a pharmacist — it's free, and they'll say which one suits what's wrong.",
    "Ask a pharmacist rather than me: they can weigh it against anything else you take.",
    "That one is a pharmacist's or GP's call — say what it's for and they'll point you at "
    "the right one.",
)

# Unchanged from the pool main had before the split: a decision that costs something keeps the
# wording it always had, so only light choices read differently.
CHOICE_WEIGH = (
    "Whichever you'd regret less if it went wrong. Which way are you leaning?",
    "I'd pick the one that's easier to undo. Is one of them?",
    "I'd go with the one you'd miss more if it went away — that's the tell. Which is it?",
)

# Words that make a two-option line a decision rather than a preference: money, a repair, a
# commitment, or something you cannot take back. Matched on whole words.
CHOICE_STAKES = frozenset("""
    buy buying bought cost costs repairing costlier price prices priced money afford cheap cheaper
    expensive spend spending repair repairs repaired fix fixing fixed replace replacing
    replaced warranty guarantee hire hiring rent rental deposit book booking booked cancel
    cancelling commit commitment contract sign signing quit quitting resign move moving
    removals install installing installed fit fitting fitter wire wiring socket fuse boiler
    washer bolt pipe seal gasket screw screws tighten drill paint painting plaster tile
    tiling build building roof gutter tyre tyres brake brakes mot service insurance insure
    loan borrow mortgage overdraft decide decision spend sell selling sold tax bill debt
    job jobs offer offers career school course degree uni university college house flat
    holiday holidays wedding baby child
""".split())

# A place, a name or a title keeps its capital letter when a pick repeats it; an everyday thing
# ("the kettle") is spelled in lower case by the line and stays that way.
NAMED_TYPES = ("place", "name", "title", "person")

# The follow-up to a taste ("Why that one?") is about the taste, not a fact to look up.
WHY_AFTER_TASTE = (
    "No deep reason: it's the one I'd go back to without thinking about it. What's yours?",
    "Mostly the memories attached to it, and a bit of habit. What would you say?",
    "Because it never disappoints, and that's most of what I ask of anything.",
)

# Information that changes by the day or the hour. The bot cannot look any of it up, so it says
# which kind it is and where a person would find it, instead of a vague "search for it".
#
# The one honest line for the news, used by the kind below and by the news ask that names no
# question ("any headlines", "the news" on its own).
LIVE_NEWS_REPLY = (
    "I can't see the news from here, sorry. A news site or app will have the latest; tell me "
    "the story and I'll help you make sense of it.")
LIVE_KINDS = (
    # A number about the person's own site or shop is theirs to look up, and no app named
    # elsewhere can see it: this sits first so that "how much web traffic does my site get" is
    # answered about a website before any pool that counts something else reads the word
    # "traffic" and sends them to a map or a journey planner.
    ("site-stats", ("traffic", "footfall", "foot traffic", "visitors", "hits", "analytics",
                    "site stats", "stats for my"),
     ("No bot can see your own numbers, sorry. A site's analytics and a search engine's count"
      " never agree exactly, because each counts a visitor its own way, so pick one and stay with"
      " it: the analytics on your site, or the admin page for a shop or a till, holds the figures."
      " The trend over a month says more than any single day does.",
      "Your own visitors are counted twice over, and the two counts differ: the analytics on your"
      " site counts pages opened, a search engine counts clicks, so the figures only ever line up"
      " roughly. Either one, watched over a month, tells you what happened; a single day does not.",
      "One busy day is usually one link somewhere, so the figure worth having is the trend rather"
      " than today's. That trend lives in the analytics for your site, or in the admin page for a"
      " shop or a till, and no one outside your own account can see it.")),
    # The same subject said as a report rather than a question: "traffic to my etsy shop is down".
    # A fall is not a number to fetch but a thing that happens for ordinary reasons, so the line
    # says what usually explains it and leaves the page that shows which one it is last.
    ("site-stats-down", ("traffic", "footfall", "foot traffic", "visitors", "hits", "sales",
                         "orders"),
     ("Quiet traffic is usually one row in the stats: a listing that stopped being refreshed, a"
      " link that died, or the week after a busy one. The analytics for your shop shows which"
      " pages people came in on, and the one that fell away is the one to refresh.",
      "A drop is rarely the whole shop. It is normally the thing you last changed, or a listing"
      " that got stale while the rest of them were being looked after: the admin page tells you"
      " which page lost the visits, and that page is the one worth an hour.",
      "The usual explanation is that a busy week pulls the next one down, so a dip after a good"
      " week is not a fall. If it is not that, the admin page shows the page that lost visits,"
      " and a listing relisted or refreshed often picks up again within a few days.")),
    # "Is it cold outside" names the sky and nothing else, but none of the words here was in it:
    # the knowledge rows that used to answer it with a note on cold air and lungs now stand down
    # (see A_WEATHER_ASK in bot/knowledge/lookup.py), and what was left was the generic "search
    # for it" hedge. A question about the reading itself is exactly the kind this note is for, so
    # the ask shapes are here beside the nouns.
    ("weather", ("weather", "wether", "weathr", "forecast", "forcast", "raining",
                 "rain tomorrow", "snowing", "how hot", "how cold", "temperature outside",
                 "temperature in", "temperature tomorrow", "temperature today",
                 "is it cold", "is it warm", "is it hot", "is it freezing", "is it raining",
                 "is it snowing", "is it sunny", "cold outside", "warm outside", "hot outside",
                 "how warm", "cold enough", "warm enough", "snowing outside", "raining outside",
                 # "whats it like outside" and "whats the temperature" are the same reading asked
                 # for with the noun left off: the sky words they do carry ("outside") were not
                 # enough on their own, and "the temperature" was only in the tuple in front of
                 # another word, so both got the hedge or the nod.
                 "like outside", "like it outside", "whats it like out", "what it like out",
                 "the temperature", "whats the temperature", "what temperature is it",
                 "how warm is it", "how cold is it", "how hot is it"),
     # Both time scales, because the pool answers both kinds of ask and only the person's line
     # says which one it is. "will it be cold" is about a coat this afternoon, and this sentence
     # now leads with the hour by hour for their own postcode - the part the bot cannot see and
     # the part that decides the coat. But "whats it like in cornwall in august" is months away,
     # where no forecast reaches and the monthly averages are the honest place to look, so they
     # stay in both lines: dropping them sent a trip to "what is coming where you are", which is
     # not where they are going (fond-octopus on #9984).
     ("I can't check the forecast from here, sorry - no live weather in me. A weather app has "
      "today's for your postcode, hour by hour, and for a trip later in the year the monthly "
      "averages are the useful thing.",
      "No live weather from me, sorry. A forecast app or the national weather site has what is "
      "actually coming where you are, and the monthly averages for a trip months away.")),
    ("hours", ("opening hours", "opening times", "opening time", "open today", "open now",
               "close today", "closing time", "what time does", "what time do", "is it open",
               "shut today", "open on"),
     # The known part comes first: hours are the one thing a venue changes without telling
     # anyone - a refurb, a bank holiday, a new landlord - and the people who run it post the new
     # ones. Only then the place to look. A bare pointer ("ring them") is not an answer
     # (operators, #uncertainty). Both lines have to carry both reads - the pool is asked for
     # "is the chip shop open" as well as "when does the tip reopen", and the variant a line gets
     # is not chosen by its kind - so neither sentence may say "reopening" as if it were the ask.
     ("The opening hours are the first thing a venue changes and the last thing it tells "
      "anyone: a refurb, a bank holiday or new owners will do it. Their own page or map listing "
      "has the current ones.",
      "No opening hours in front of me. Whoever runs the place - a council tip, a chain, one "
      "landlord - announces a change itself, and its own page or phone number has today's.")),
    ("prices", ("how much is a", "how much does a", "how much are", "price of", "cost of",
                "exchange rate", "stock price", "how much is it"),
     # Both lines used to be the pointer and nothing else - "the seller's site has today's
     # figure" - which says nothing about the thing being priced and leaves the person exactly
     # where they were. A price has a known half: it turns on which one it is, where you buy it
     # and the day, and one figure from one seller is not an answer to it. The known half goes first,
     # then the place the current number is kept, then the sums, which is what somebody ringing
     # round three sellers actually wants. Same rule as the place pools: a pointer on its own is
     # not a reply.
     ("I can't look up live prices, sorry. What a figure like that turns on is which one it is, "
      "where you buy it and the day, so two or three sellers compared all-in will beat the first "
      "price you see - their own site has today's number, and bring it back and I'll work out what "
      "it comes to a month.",
      "Prices move too fast for me to know. Which one you pick and where you buy it decide most "
      "of the figure, and a quick look at the seller's own site has today's number, all in with "
      "delivery - tell me what it says and I'll do the sums with you.")),
    ("news", ("the news", "headline", "who won", "the score", "latest on", "current events",
              "what happened in the"),
     (LIVE_NEWS_REPLY,)),
    # The roads are the same live hole as the trains, and they had no words here at all: "how are
    # the roads", "is the m25 closed" and "are the buses running today" reached the search hedge
    # or the nod, while "whats the traffic like" was answered about the next train. The road comes
    # first, so a line that names both ("traffic on the way to the station") is read as a road.
    # What the person opens to find out differs, which is why the two kinds are apart.
    ("roads", ("traffic", "the roads", "the road", "road closed", "closed road", "roadworks",
               "road works", "the motorway", "motorway closed", "in a jam", "jams",
               "accident on the", "accidents on the", "accident on", "accidents on",
               "diversion", "dual carriageway"),
     # The pointer is the last thing in these lines, not the whole of them. "is the m6 closed" and
     # "how busy is the a1 today" were answered with nothing but "I can't see the roads, a maps app
     # has it" - true, and no help at all, because the person still has no idea what to expect or
     # which of the two things they are looking at (operators, #uncertainty). What a friend says
     # first is the bit that is generally true - jams come back at the same hours, a closure is a
     # diversion rather than a slow lane, a jam clears from the front - and then where today's
     # answer is. Every clause has to be true of every road, so "one closed lane costs more time
     # than a busy motorway does" is not in here: it is a claim nobody can check.
     ("Traffic comes back at the same times on most weekdays, so a road that is slow at eight is "
      "usually slow at eight, while a closure or roadworks is a diversion and a different wait "
      "altogether. I can't see the roads from here, sorry: a maps app with live traffic, or the "
      "roads agency's own site, has today's jams, closures and roadworks as they happen.",
      "A jam clears from the front and a closure means a diversion, and those want different "
      "places looked at. I can't see the roads from here, sorry: the roads agency's own site has "
      "today's closures and roadworks, and a maps app with live traffic has the jams and how long "
      "each one is adding.")),
    ("travel", ("train times", "bus times", "next train", "next bus", "delayed",
                "is it running", "on strike", "buses running", "are the buses",
                "the trains running", "are the trains", "timetable", "the tube",
                "tube strike"),
     ("I can't check live times or delays, sorry. The operator's own app or site has the next "
      "departure and any disruption, and a journey planner puts the whole trip together.",)),
    # A journey between two places is not a course of driving lessons and not a timetable the
    # bot can read: how long it takes depends on the hour they set off, which is a reading
    # nobody here can take. "how long is the drive from leeds to edinburgh" was answered with
    # the hours-of-lessons card, and "how far is york from leeds" with a search hedge.
    ("journey", ("how long is the drive", "how long would the drive", "how long does the drive",
                 "how long is the journey", "how long would the journey", "how long is the trip",
                 "how long does it take to drive", "how long does it take to get to",
                 "how long to drive", "drive from", "drive to", "the drive be",
                 "how far is the drive", "how far from", "how far is", "how many miles"),
     # "how long does it take to drive to manchester" got "put both places into a route planner"
     # and nothing else, which tells the person nothing about the drive they are planning. The
     # part that is true of every drive comes first - the hour you leave and the last few miles
     # are what decide it, and the distance is the least of it - and then where the figure is.
     ("The time a drive takes is mostly decided by the hour you set off and by the roads you use, "
      "since town streets and the last few miles are never motorway speed. I can't see either from "
      "here: a route planner has the figure for the hour you would actually leave, roadworks "
      "included, and the stops worth making on the way.",
      "However far it is, the drive will take longer than the distance suggests, because the first "
      "and last miles are the slow part and the hour you leave changes the rest. A route planner "
      "has it for your own leaving time; a maps app does the same from wherever you are.")),
    # "how long is the drive" on its own names no ends at all, so there is nothing to look up
    # yet: one short question gets the two ends, which is the whole answer the bot can give.
    ("journey-ask", ("how long is the drive", "how long would the drive", "how long does the drive",
                     "how long will the drive", "how long is the journey", "how long would the journey",
                     "how long will the journey", "how long is the trip", "how long would the trip",
                     "how long will the trip", "how long is the flight"),
     # A question on its own is not an answer either: what the bot knows about a drive is true
     # before it knows the ends - the hour and the last few miles decide it, and either end can be
     # the slow one - so the question comes after that.
     ("The hour you set off and the roads you use decide most of a drive, and the first and last "
      "miles are the slow part wherever you are going. Long from where to where, and roughly when "
      "would you set off? I can plan the day around it once I know.",
      "The hour and the last few miles decide a journey, and either end can be the slow one. "
      "Where are you starting, where are you heading, and roughly when? I can work through the "
      "timing and the stops with you.")),
    # "how far is the tennis court" names one place and no other end, so it is a distance from
    # where they are standing, not a journey between two places: the route line answered it with
    # the stops worth making on the way.
    ("distance", ("how far is", "how far away", "how many miles is", "how many miles from",
                  "how long is the walk", "how long is the bike ride"),
     ("I can't measure a distance from where you are, sorry. A map app does it from your own "
      "door in one tap, walking and driving both.",
      "That is a distance I can't take from this end. Put it into a map app and it shows how "
      "far and how long, from wherever you are standing.")),
    # When the bins go out is a live local fact with an owner - the council, by postcode - and
    # nothing in the pools knew it: "when do they collect the bins this week" was the search hedge
    # and "is it recycling this week" was the line said back. The rows that answer what goes in
    # which bin keep their turns; this is only the day.
    # The words here are the day, not the bin: "what about the bins" and "why bother anymore with
    # the recycling" are a mention and a mood, so the bare nouns are left out and a phrase that
    # only names the round in passing does not take the line.
    ("waste", ("bin day", "bin collection", "bin collections", "collection day", "recycling day",
               "is it recycling", "when do they collect", "when do the bins", "when are the bins",
               "when is the bin", "which bin goes out", "which bin is it", "black bin", "green bin",
               "blue bin", "brown bin", "food waste", "garden waste", "kerbside", "wheelie bin",
               "bulky waste", "household waste", "rubbish collection", "refuse collection",
               "missed bin", "bin lorry", "bin been collected", "bins been collected",
               "has the bin been"),
     ("Rounds are set street by street, not by town, and a bank holiday moves them by a day or "
      "two - so I can't see your street's day from here. The council's own site takes a postcode "
      "and gives the next collection; that is also where the holiday change is announced.",
      "Which day a street is collected on is the council's own choice, and holidays shift it, so "
      "there is nothing to know from this end without the postcode. The council's site has the "
      "round for your address, and a missed bin is free to report there on the day.")),
)

# "my latest order", "my asos parcel", "my hospital appointment": a word or two may sit between
# the possessive and the thing, and the thing has to end there so "my ordering" is not "my order".
MY_OWN = {}

# One line per family of record, because the way to find out differs: a parcel is tracked, a
# booking is in a confirmation, a balance is in the bank's app, a result is with the surgery.
MY_RECORDS = (
    ("delivery", ("order", "orders", "parcel", "parcels", "delivery", "deliveries", "tracking",
                  "dispatch", "courier"),
     ("The tracking link in the order email or the shop's app shows exactly where a parcel is, "
      "and the shop can look the order up by your name and address - I can't see your order "
      "from here.",
      "Where a parcel has got to is in the tracking link you were sent; if it has not moved for "
      "days it is the shop you chase, not the courier. No way to check it from this end.")),
    ("booking", ("booking", "bookings", "reservation", "reservations", "appointment",
                 "appointments", "check-in", "check in"),
     ("The confirmation email or text has the time and the reference, and a ring to the place "
      "with your name and the day settles anything else - I can't see your booking from here.",
      "A booking lives with the place, not with me: the email or text you were sent has the "
      "time, and the desk can check it by name if that has gone missing.")),
    ("application", ("application", "applications", "claim", "claims", "renewal", "quote",
                     "complaint", "refund", "refunds"),
     ("The reference number they gave you brings it up on their site, and one call to the office "
      "gets you a straight answer - I can't see how it is going from here.",
      "The reference they gave you, or the email that came back when you sent it, has where it "
      "has got to, and a phone call gets it in a minute. Nothing of yours is in front of me.")),
    ("money", ("balance", "statement", "account", "direct debit", "standing order", "payment",
               "transaction", "overdraft"),
     ("Your bank's app, a cash machine or the number on the card shows the balance and what has "
      "gone out - I can't see your account at all.",
      "The figure is in your banking app or on the last statement, and the bank can confirm it in "
      "one call. Nothing of yours is here for me to look at.")),
    ("card", ("gift card", "gift cards", "voucher", "vouchers", "loyalty points",
              "loyalty card", "store card"),
     ("The number on the back of the card, or the shop's app, tells you what is left on it - I "
      "can't check a card balance from here.",
      "The card's own site, or the number on the back of it, has the balance; nothing of yours is "
      "here for me to look at.")),
)

# "is my gift card still valid", "does my voucher expire": not the balance and not the etiquette
# of giving one. The date is printed on the card, and a shop can usually swap it or move what is
# left onto a new one, which is the only thing the person can act on.
CARD_VALIDITY = (
    "A card's expiry date is printed on the back of it, and the shop's app shows it too. If it "
    "has run out, ring the shop - many will swap it or move what is left onto a new one.",
    "The date it runs out is on the back of the card, or in the shop's app. An out-of-date card "
    "is worth one phone call: shops can often swap it or put the balance back as credit.",
)

# A prescription and a scan are the surgery's, and so is a result - but "my results" is a school
# or a lab or an exam, so the health line only answers a line that names the health world too.
HEALTH_RECORD = ("prescription", "prescriptions", "scan", "scans", "referral", "referrals",
                 "x-ray", "xray", "x-rays", "bloods", "blood test", "test results", "results")

HEALTH_WORLD = ("doctor", "gp", "surgery", "hospital", "clinic", "nurse", "midwife", "consultant",
                "dentist", "medical", "health", "test", "blood", "scan", "x-ray", "xray",
                "prescription", "consultant", "specialist", "appointment")

# The records nobody wrote down. The families above are the ones people ask about most, so each
# has a line of its own; the rest are named with a noun no table holds - a visa, an offer, an
# interview - and the ask is always the same shape: has it been approved, accepted, arranged. A
# thing an office puts into a state can only be seen by that office, so the line names what the
# person already has (the letter, the email, the reference) rather than guessing at the answer.
OFFICE_RECORD_LINES = (
    "I can't see that from here - nothing of yours reaches me, so I can't say where it has got "
    "to. The letter, email or reference number it came with will bring up its state on their "
    "site, and one call to the office that issued it settles it.",
    "Nothing of yours here to look at, sorry, so I can't check that one. Whatever it came from "
    "- the letter, the email or the app it was arranged through - has where it has got to, and "
    "the number they gave you gets it in a minute on the phone.",
    "That state is theirs to know and mine to guess at, and a guess is no use to you. The "
    "confirmation you were sent is the one place it is written down, and the office that deals "
    "with it can confirm it in one call.",
)

# A thing handed over at a counter: "have i been given the wrong change", "i got short changed at
# the shop". It is not a record any office keeps - the till knows, and the receipt is the proof -
# so the reference-number line was the wrong subject, and "how did that go, overall?" was no answer
# at all. Nothing here is a fact about money: the count, the receipt and the same-day counter are
# what a shop settles, which is true of a cafe, a market stall and a bus alike.
AT_THE_TILL = (
    "Count it against the receipt before you leave it too long: the till's own record of the sale "
    "is what the shop works from, and a counter sorts it on the day far more easily than a head "
    "office does later. How much short are you?",
    "That is the shop's to put right, not yours to prove - the receipt and the amount is usually "
    "enough at the counter, and most shops fix it the same day. If it was a card, your statement "
    "has the figure the till rang up.",
)

# Their own day: whether they are in, and when they start and finish. A rota is on the person's
# side of the screen and no search answers it, so the reply names the one place it lives. Nothing
# here is a fact about the world - no hours are given, because none are known.
MY_OWN_DAY = (
    "I can't see your rota from here, sorry - nothing of your work reaches me, so your hours are "
    "with whoever writes it and in the app your work puts it in.",
    "No window on your shifts from this end, sorry: the start and finish times are on the rota, "
    "with your manager or in the rota app your work uses.",
    "That one lives on the rota rather than anywhere I can see - your manager has the hours, and "
    "your contract has the ones they have to keep to.",
)

# A points or stamps balance is the person's own, held by the scheme rather than anywhere the bot
# can see: the figure is in the app or on the card, the expiry is on the same page, and what the
# points are worth depends on the scheme's own rate. Each line leads with what is knowable about
# such schemes (points build when the card or app is scanned, they expire after a period with no
# activity, and the rate is the scheme's), then names the place to check, then offers the only
# part that can be done here: the arithmetic once the rate is known.
# What a person pays for something they already have - a gym, a phone contract, a streaming
# subscription - is on their own bill, not in any price list, and a quote for a *new* one is a
# different question with its own pool. The line says where the figure is, names the part of the
# bill that decides what happens next (the minimum term and the notice), and offers the one sum
# that can still be done here: what a monthly price comes to over a year, or over the term.
MY_BILL_LINES = (
    "What you pay is on your own bill rather than in any price list I could read: the app or the "
    "email they send you has the monthly figure, and the bank statement under the same name shows "
    "it went out. Tell me what it is and I'll work out what it comes to over the year, and check "
    "the notice you would need to give.",
    "I can't see your bill, sorry. The provider's app, the last email from them or your bank "
    "statement has the figure, and the same place has the minimum term - that is what decides "
    "whether you can leave and what it costs to stop. Give me the numbers and I'll do the sums.",
    "That price is between you and them, and only your own paperwork has it. The app, the bill "
    "email or the direct debit on your statement is where to look, and the contract length and "
    "notice period sit on the same page - worth knowing before you think about changing it. Hand "
    "me the figures and I'll work the rest out.",
)

POINTS_LINES = (
    "Points build up wherever the card or the app gets scanned, and the scheme's own points page "
    "has the balance and the day they run out - most clear an account after a year or two with "
    "nothing on it. Tell me what a point is worth in that scheme and I'll work out the money.",
    "I can't see your points from here, sorry - only the scheme can. Their app, a receipt or the "
    "number on the back of the card shows the balance, and it is worth a look if the card has been "
    "in a drawer, because points usually expire after a year or so with no activity. Give me the "
    "figures and I'll do the arithmetic on what they buy.",
    "That balance lives with the scheme rather than with me. The app's points page has it, and the "
    "same page says when they expire - a year or two of no use is the usual rule, though each "
    "scheme sets its own. Hand me the rate and the count and I'll tell you what it comes to.",
)

HEALTH_RECORD_LINES = (
    "I can't see your records from here. The surgery's app or a ring to reception has the date "
    "and the result, and they can say whether anyone needs to see you about it.",
    "Nothing of yours in front of me, sorry. The letter, text or app it came through will have "
    "the date and what came of it, and reception can look it up if that is lost.",
)

# A shopkeeper is also a "we": "what time do we open" and "what time does my shop open" are the
# same question a customer asks, and the opening-hours line answers it. So the speaker's own
# subject only stands the pool down when the line names nothing that opens - and "we open" is
# that thing by itself.
OWN_PLACE = ("shop", "store", "stores", "branch", "office", "cafe", "café", "canteen",
             "pub", "bar", "gym", "surgery", "pharmacy", "chemist", "bank", "salon",
             "museum", "tip", "library", "restaurant", "takeaway", "chippy", "garage",
             "hotel", "school", "nursery", "clinic", "centre", "center", "pool", "market",
             "stall", "van", "kiosk", "studio", "workshop")

# A person in the line moves the subject off the place: "what time does my son finish school" is
# about the boy's day, and "school" in it does not make it the school's opening hours.
OWN_PERSON = ("son", "daughter", "kid", "kids", "child", "children", "baby", "wife",
              "husband", "partner", "mum", "mom", "mother", "dad", "father", "boyfriend",
              "girlfriend", "nan", "grandma", "grandad", "grandson", "granddaughter")

# A line that asks about the subject itself ("what's the difference between weather and
# climate") is general knowledge, not a request for today's numbers.
LIVE_NOT = ("difference", "climate", "how does", "why does", "why do ", "explain", "meaning of")

# "What time does the sun rise" asks the sky, not a shop counter. A celestial event is not a
# venue's opening hours, and the opening-hours phrases are built around "what time does", which
# the sky question shares; the entry that has the sunrise answer is the one to give.
LIVE_NOT_HOURS = ("sun", "sunrise", "sunset", "sun set", "sun rise", "moon", "moonrise",
                  "tide", "tides", "high tide", "low tide", "dawn", "dusk", "daylight",
                  "stars", "milky way", "eclipse")

# The places a person means when they ask when something opens: a shop, a branch, a surgery, a
# tip. Where `OWN_PLACE` is the speaker's own place (a shopkeeper asking about their shop), this
# is any place named at all, and it is what makes a line a question about hours nobody here can
# know (`bot/modules/arbiter.py`, `_the_venue_hours_turn`). A place has to be NAMED: "what time
# does boarding start" and "what time do the bins go out" are their own answers, and the words
# "what time" alone would take them. Write the singular; `_names_a_venue` reads the plural too.
LIVE_VENUE = ("shop", "store", "supermarket", "tesco", "asda", "sainsbury", "aldi", "lidl",
              "co-op", "coop", "morrisons", "waitrose", "iceland", "branch", "bank",
              "post office", "postbox", "library", "pharmacy", "chemist", "surgery", "gp",
              "doctor", "dentist", "vet", "tip", "dump", "recycling centre", "cafe", "café",
              "restaurant", "takeaway", "chippy", "pub", "bar", "gym", "leisure centre",
              "pool", "museum", "gallery", "garden centre", "centre", "market", "salon",
              "barber", "hairdresser", "office", "clinic", "hospital", "school", "nursery",
              "garage", "hotel", "station", "airport", "council", "launderette", "kiosk",
              "studio", "workshop", "church", "hall", "venue", "park", "butcher", "bakery",
              "greengrocer", "depot", "club")
LIVE_VENUE_RE = re.compile(
    r"(?<![a-z])(?:" + "|".join(re.escape(word) for word in
                                sorted(LIVE_VENUE, key=len, reverse=True)) + r")(?:s|es)?(?![a-z])")

# Open, close or shut in the line is the other half: "when does the post office close" is the
# plainest way to ask for a venue's hours and the one the opening-hours phrases do not cover.
# "how do i open a bank account" and "how do i close my gym membership" name a place and say
# open or close and are not about hours, and "what should i look for on a school open day" is
# about the day, not the clock, so the line has to ASK WHEN as a question about the place: "when
# does the post office close", "what time do the banks open today", "when is the shop shut". A
# "when" that opens a clause of its own is a different question: "what do i do about toothache
# at the weekend when the dentist is shut" wants the out-of-hours service an entry has.
LIVE_OPEN_CLOSE = ("open", "opens", "opening", "opened", "close", "closes", "closing", "closed",
                   "shut", "shuts", "shutting", "close up")
LIVE_HOURS_ASK = re.compile(
    r"\b(?:when|what time|what hours|how late|what times)\s+"
    r"(?:does|do|is|are|will|would|can|doesnt|don't|dont|isnt|is it)\b"
    r"[^.!?]{0,40}?\b(?:open|opens|closed|closes|close|shut|shuts|shutting|closing|"
    # "when does the tip reopen" names no time at all: the reopen is the question, and the
    # phrase lists ("open today", "close today") have no word for it, so it reached the hedge.
    r"re-?opens?|re-?opening|re-?opened)\b")
# The same ask as a yes or no, which is how most people put it once the place is named: "is my
# chip shop open", "is there a pharmacy open near me", "is the swimming pool open late tonight".
# None of the phrases above has "is ... open" in it ("is it open" wants the bare pronoun), so
# these lines reached the search hedge - "I don't know enough to answer that honestly" - on a
# question whose honest answer is one line long. The verb has to OPEN the line, so a statement
# that happens to have "is" before "open" ("the shop is open late on fridays") keeps its own
# reading, and "open to" / "open up" is a different thing than a door being unlocked.
LIVE_YES_NO_OPEN = re.compile(
    r"^\s*(?:so|and|but|ok|okay|also|hi|hello|morning|quick one)?\s*,?\s*"
    r"(?:is|are|will|does|do|can)\s+[^.!?]{0,40}?"
    r"\b(?:open|opens|shut|shuts|closed|closing|close)\b"
    r"(?!\s*(?:up|ness|ing|ly|air|plan|letter|account|evening|day|days|morning|"
    r"afternoon)\b)"
    # "open to the public" is a door being unlocked, and museums and pools say it that way; "open
    # to offers", "open to negotiation" and "open to new ideas" are not hours at all.
    r"(?!\s*to\s+(?!the\s+public\b))")

# "How hot should the oven be" and "how cold should the room be for a baby" are settings, not the
# weather: a temperature question with something in the house in it needs a weather word beside it.
LIVE_INDOOR = ("oven", "fridge", "freezer", "room", "bedroom", "nursery", "bath", "shower",
               "kettle", "boiler", "radiator", "washing machine", "tumble dryer", "air fryer",
               "slow cooker", "grill", "hob", "pan", "oil", "water", "iron", "greenhouse",
               "shed", "garage", "car", "engine", "laptop", "phone", "kitchen", "loft",
               "attic", "cellar", "basement", "conservatory", "living room", "sitting room",
               "dining room", "hall", "hallway", "porch")

LIVE_WEATHER_WORDS = ("weather", "wether", "weathr", "forecast", "forcast", "rain", "raining",
                      "rainy", "snow", "snowing", "sunny", "sun", "wind", "windy", "outside",
                      "outdoors", "umbrella", "coat", "bbq", "barbecue")

# The sky said in words the asks elsewhere do not hold - as an adjective ("is it windy out") or as
# weather happening ("will it snow", "is there frost tonight"). Without these, the same question
# about the same day was answered or hedged by which weather word the person happened to choose:
# "will it rain tomorrow" got the note about the forecast, "will it be icy tomorrow" got "a quick
# search online will get you a solid answer". "Sunny" is not here on purpose: the sunny asks are
# held already, and the bare adjective is a room's too ("the conservatory is sunny"), where the
# forecast note is no answer.
LIVE_SKY = ("windy", "icy", "muggy", "humid", "cloudy", "overcast", "chilly", "freezing",
            "heatwave", "rain", "raining", "rainy", "snow", "snowing", "snowy", "storm",
            "stormy", "thunder", "thundery", "hail", "hailing", "fog", "foggy", "mist", "misty",
            "drizzle", "drizzling", "showers", "frost", "frosty")

# The same words in a line about something else: a head in a fog, a taxi hailed, a figure of
# speech. Only the weather senses are read from here.
LIVE_SKY_OFF = ("brain fog", "foggy head", "head is foggy", "head foggy", "misty eyed",
                "hail a taxi", "hail a cab", "weather the storm", "storm in a teacup",
                "under the weather", "frost free", "frost-free", "rain check")

# "Why is it muggy" asks what makes the weather, not what the weather will be: the mechanism is a
# fact about the world, so it keeps its own answer (the humidity card exists already).
LIVE_SKY_WHY = re.compile(r"\b(?:why|how\s+come|what\s+causes|what\s+makes)\b")

# "Should I take an umbrella today", "do I need a coat tonight": a weather item plus today,
# tomorrow or tonight is a question about the sky, though neither half names the weather. Without
# the time word it is another question ("where are my boots", "my coat is still wet").
# A wear item is only about the sky when nothing says where the person is going: "should i take my
# boots to the gym today" is about gym kit, "should i take a coat tonight" is about the weather.
LIVE_WEAR = ("umbrella", "coat", "jacket", "shorts", "boots", "wellies")

LIVE_SETTING = ("gym", "work", "office", "school", "college", "uni", "class", "nursery",
                "dinner", "lunch", "party", "wedding", "funeral", "interview", "hospital",
                "indoors", "inside", "in the house", "shopping", "the shops", "the dance")

LIVE_SOON = ("today", "tonight", "tomorrow", "this afternoon", "this morning", "this evening",
             "this weekend")

# A garment is the weather ask on its own when the line is about taking or needing it: "should i
# take an umbrella" is a forecast question whether or not it says "today", and people say it that
# way far more often than with the time word. LIVE_SOON stays one way of saying it, not the only
# one.
LIVE_TAKE_ASK = ("should i take", "shall i take", "do i take", "do i need", "will i need",
                 "should i bring", "shall i bring", "do i need to take", "should i wear",
                 "shall i wear", "should i put on", "will i be needing", "do i want")

# A garment ask is a weather question only when the ask is the whole of the line: the garment, the
# ask, a time word, and nothing else attached to it. "should i take my boots to be repaired" wants a
# cobbler and "should i take an umbrella on the plane" wants a suitcase -- the garment there is the
# thing being taken somewhere, not a question about the sky.
LIVE_TAKE_ALLOWED = {"to", "the", "a", "an", "my", "our", "your", "and", "or", "out", "outside",
                     "tonight", "today", "tomorrow", "now", "later", "morning", "afternoon",
                     "evening", "weekend", "with", "me", "it", "this", "on", "in", "at", "for",
                     "when", "i", "should", "shall", "do", "need", "will", "be", "bring", "take",
                     "wear", "put", "want", "going", "am"}

# "Is my train to euston cancelled" is live information about travel, but "can i cancel my gym
# membership" is not, so a delay word only counts beside a way of travelling.
# A journey answer needs a second end: "from leeds", "to york", "from here". A line that
# names one place and no other end ("how far is the tennis court") is a distance from where
# they are standing, and the distance kind below answers that instead.
LIVE_JOURNEY_ENDS = ("from", "to", "towards", "as far as")

LIVE_TRAVEL_WORDS = ("train", "trains", "bus", "buses", "coach", "flight", "flights", "plane",
                     "tram", "tube", "ferry", "motorway", "traffic", "road", "line", "strike")
# "Is the m25 closed", "has the a14 got roadworks": a road is named by its number as often as by
# its noun, and "is the m25 closed" was the search hedge. The pattern wants a letter and one to
# three digits as a whole word, so "a1 batteries" is not a road (the travel words above have to
# be in the line too) and "m25" in a postcode is not one either.
LIVE_ROAD_NAME = re.compile(r"\b(?:m|a)\d{1,3}(?:\s?\(m\))?\b")
# ...unless the line is about a sheet of paper. "a1" to "a6" are the sizes people type, and
# "is the a4 paper ok for my printer" was sent to a map (safe-needle). A paper word stands the
# number down; "is the a1 closed" and "whats the traffic like on the a1" keep the roads line.
LIVE_PAPER_WORDS = ("paper", "card", "cardboard", "envelope", "printer", "print", "printing",
                    "printed", "poster", "frame", "photo", "photograph", "notebook", "canvas",
                    "sketchbook", "drawing", "stationery", "folder", "binder")
# A closure or a jam needs a road word as well, so "is the road to leeds closed" is a road and
# "my flight was cancelled" is not.
LIVE_ROAD_WORDS = ("road", "roads", "motorway", "traffic", "junction", "bypass", "roundabout",
                   "carriageway", "lane")
# The roads that are not about travelling today: the tax, a trip away, a bike, a test, the way a
# road is built, and directions (which are an answer about the route, not about the traffic).
# The things whose numbers only their owner can see: a website, a shop, a listing. `LIVE_KINDS`'
# "site-stats" note is read only for a line naming one of these, because its counting words
# ("traffic", "visitors") are the roads' and the venues' words too.
LIVE_SITE_THING = ("site", "website", "web page", "webpage", "online shop", "shop", "store",
                   "etsy", "listing", "my page", "the page", "web stats", "footfall")

LIVE_ROADS_NOT = ("road tax", "tax the", "road trip", "road bike", "off road",
                  # "Traffic" on a site or in a shop is the other kind, and the roads note read
                  # it as lanes: "how much web traffic does my site get" was told that jams come
                  # back at the same times on most weekdays and that a closed lane costs more
                  # than a busy motorway. Neither is true of a website.
                  "web traffic", "site traffic", "online traffic", "search traffic", "footfall",
                  "foot traffic", "my website", "my site", "my shop", "my store", "my etsy",
                  "website", "shop window", "customers through",
                  # A dead animal, a pothole and a dumped mattress are the council's to clear, not
                  # today's traffic: "who do i call about a dead fox in the road" was read as a
                  # road question and sent to a map.
                  "dead", "fox", "badger", "hedgehog", "deer", "animal", "pothole",
                  "who do i call", "who do i report", "report a", "report the",
                  # Advice about driving in traffic is a tip, not the road itself.
                  "tips", "advice", "how do i drive", "driving in", "long drive",
                  "driving test", "theory test", "driving licence", "driving license",
                  "how do i get", "how to get", "how far is", "directions to", "route to",
                  "made of", "built", "why do", "why are roads", "surface", "roadworthy",
                  "cycle lane", "cycle path", "bus lane", "parking", "speeding", "points on",
                  "school", "college", "class", "revision", "study")

LIVE_DELAY_WORDS = ("cancelled", "canceled", "cancellation", "delayed", "delay", "delays",
                    "on time", "running late", "disruption", "engineering works",
                    "replacement bus", "bus replacement")

# Phrases that ask for live information even inside a statement ("train times to Bristol").
LIVE_STRONG = ("times", "forecast", "opening hours", "opening times", "how much", "price",
               "what time", "the score", "latest on",
               # The day's news and results ask without a question mark often enough that the
               # names carry the ask: "any news today", "any headlines", "any results yet".
               # Each phrase is one only a live ask uses, because this list skips the gate that
               # otherwise wants a question: "i made headlines at work today" and "the biggest
               # fish in the world" are neither here - the bare "headlines" and "in the world"
               # were, and answered a story with the news line (cyan-walrus, on #7712).
               "latest news", "news today", "any news today", "any headlines",
               # "any news on the strikes" is the commonest way a person asks and it has no
               # question mark: the phrase carries the bottomless thing the line names, so the
               # world-news reader takes it rather than the chat pool (sky-turkey).
               "any news on", "any news about", "any news of", "any update on", "any word on",
               "spill the news", "any results", "any result", "what channel",
               # The roads and the departure board do the same: "any traffic problems", "road
               # closed near me", "train timetable". The same rule applies to these, and the
               # first draft broke it twice: a bare "timetable" is also a thing printed at work
               # ("i printed the timetable", "my new timetable starts monday") and "traffic on
               # the" is a story about the drive in ("the traffic on the way here was awful"),
               # so the timetable needs the word in front of it and the story needs its nod.
               "any traffic", "traffic problems", "road closed", "closed road",
               "train timetable", "bus timetable", "are the buses", "are the trains",
               "buses running", "trains running", "tube line", "the m25 closed", "m25 closed")

# "Hi! How's your day going?" is a greeting with manners, not a request for information.
HOW_ARE_YOU_ASKS = ("how are you", "how are things", "how is things", "how's things",
                    "how's your day", "how is your day", "your day going",
                    # The same two questions written the way people type them. "ur" is already
                    # read as "your", so these are the spellings the list cannot reach: without
                    # them "howz ur day" and "whats ur day been like" got the search shrug.
                    "howz your day", "whats your day", "hows your day",
                    "how's it going",
                    "how is it going", "how have you been", "you doing", "you ok", "you okay",
                    "you all right", "how do you do",
                    # asking what the bot is filling its time with is the same manners
                    # question in the spelling people type: "what u up to", "up to much".
                    # The tag test below keeps a real question out.
                    "you up to", "up to much", "been up to")

# "going on" is the one phrase that also names things happening in the world, so it counts
# only when the line says nothing about when: "anything going on" and "much going on" are the
# manners question, while "anything going on tonight", "much going on this week" and "what's
# going on saturday" are about what is on, and "can't complain" answers none of them.
HOW_ARE_YOU_GOING_ON = ("much going on", "going on")

HOW_ARE_YOU_GOING_ON_AFTER = frozenset({"else", ""})

# What may follow the phrase and still leave it the whole question: a tag, not a new ask.
HOW_ARE_YOU_TAGS = frozenset((
    "today", "tonight", "now", "then", "so", "far", "lately", "recently", "again", "too",
    "mate", "guys", "everyone", "everybody", "all", "both", "honestly", "anyway", "though",
    "thanks", "sir", "madam", "doing", "feeling", "keeping", "coping", "holding", "up",
    "these", "days", "at", "the", "moment", "folks", "friend", "love", "team",
    # "whats ur day been like" and "howz ur day going then": the tag tells the phrase is the ask.
    "been", "like", "going", "lately",
    # The words a person puts after the phrase when the phrase is still the whole question:
    # "how's your day been", "how's it going", "how are you looking".
    "been", "going", "looking", "hmm", "lol",
    # "how did your day go", "how did it go".
    "go", "gone",
))

HOW_ARE_YOU = (
    "Good, thanks for asking — and good to have you here. What's on your mind?",
    "Can't complain. Better question: how are you doing?",
    "Fine and busy, the two usual things. How's your day been?",
    "I'm well, thanks. What are you up to today?",
)

ADVICE_WORDS = ("should", "worth", "better", "cheaper", "faster", "recommend", "suggest",
                "which", "how do", "how can", "any tips", "less", "fewer", "more", "difference",
                "correct", "grammar", "spell", "'")

# A greeting in front of one of these is small talk around a request, so the request is answered.
REQUEST_CUES = ("quick one", "quick question", "one more thing", "another thing", "need help",
                "any tips", "any advice", "advice", "how do", "how can", "what should", "can you",
                "could you", "help me", "give me", "recommend", "suggest", "wondering", "?")

# "is that a stupid idea", "does that sound sensible", "am I mad": the person has a plan on the
# table - their own ("im going to ask for a pay rise") or the one the answer above just gave
# ("should i get a credit card") - and wants a verdict on it. It is the commonest way a person
# asks twice for the same permission, and it got the search shrug, or worse: "am I mad" was read
# as being angry and answered "say it out loud to whoever caused it", which is about somebody
# else entirely. The verdict needs no facts about the plan - it is either stupid or it is not,
# and what decides it is whether the person has an answer for it going wrong - so it is honest,
# short, and it says the plan back the way they put it.
JUDGE_ASKS_SLIGHT = r"(?:stupid|daft|dumb|silly|idiotic|thick|bad|terrible|awful|dreadful|wrong)"

# "is that ok" and "does that make sense" are left out on purpose: both are as often a check that
# the person understood the answer as a verdict on a plan, and the plan miss is a bad answer to a
# comprehension check. What is left names a judgement of the idea and nothing else.
JUDGE_ASKS_FINE = r"(?:good|great|sensible|wise|smart|clever|reasonable)"

JUDGE_ASKS_MAD = r"(?:mad|crazy|insane|nuts|mental|unhinged)"

JUDGE_NOUN = r"(?:idea|plan|thing|move|call|choice|decision|approach|bet|notion|step)"

# The faces that are a verdict and nothing else when they stand alone, so a bare one is this ask
# with the finger left out: "sensible?", "stupid?", "sound sensible?". "good", "great", "fine"
# and "nice" are not among them - on their own they are how a person says yes, not a question.
JUDGE_BARE_FACES = frozenset("""sensible wise reasonable smart clever stupid daft dumb silly
    idiotic bad terrible awful dreadful wrong mad crazy insane nuts mental unhinged""".split())

# The plan, as the person put it: the verb phrase after the opening they used for it, and only
# when it is short and unbroken - a clause with a "but" or a second sentence is a story, and
# naming half of it back would be worse than naming none of it.
# The plan is often opened with a hedge in front of it ("i think im going to quit",
# "honestly, so im gonna"), and the hedge does not change what the plan is: the same lead
# goes on every form of the opening.
JUDGE_LEAD = (r"(?:^|\b(?:ok|okay|so|and|but|well|honestly|tbh|maybe|i think|i reckon"
              r"|i guess|i feel like)\b )")

# A plan phrase with one of these in it is a clause the bot would have to guess the rest of.
JUDGE_PLAN_STOP = frozenset("""but because so then since if unless although though which who that
    when where while whereas before after once""".split())

JUDGE_NOD_WORDS = frozenset("""yes yeah yep no nope ok okay sure right cool thanks thank you
    hmm mm mmm well so and but true fair good nice haha lol oh ah please""".split())

# The plan names the part that makes it risky - "100 miles with no training", "all my savings in
# bitcoin" - and the person asks for a verdict on it. The pools below cannot answer: they rule that
# a plan is not stupid, and this one is the part a friend pushes back on ("Nothing daft in wanting
# to put all my savings in bitcoin" is not something a friend says). What can be said without any
# facts about the plan is which part is the one to answer for and what the test of it is - the same
# test every plan gets - so that is the reply, and the plan is said back in their own words.
JUDGE_PLAN_HAS_A_HOLE = (
    "{Plan} is where it gets tight, and that is the part to answer for. What would you do if "
    "it went wrong?",
    "{Plan} is the part a friend would push back on, not the wanting. Say what you would do if it "
    "did not work, and if that is quick to say, go.",
    "{Plan} leaves nothing spare, and that is the part I would look at. What is your answer if it "
    "goes wrong?",
)

JUDGE_WORTH = (
    "Not stupid, no. {Plan} is the ordinary kind of thing people do; what decides it is what you "
    "would do if it went wrong - if that leaves you all right, go.",
    "Nothing wrong with {plan}. The part that goes wrong is having no answer for what if it does "
    "not work.",
    "Nothing daft in {plan}. Say what you would do if it went wrong; if that is quick to say, do it.",
)

JUDGE_WORTH_PLAIN = (
    "Not stupid. The test is what you would do if it went wrong: if that leaves you all right, "
    "there is nothing daft in it.",
    "No, it is not stupid. The thing that would make it stupid is having no answer for what if "
    "it goes wrong.",
    "Nothing daft about it. Ask what you would do if it went wrong - if you would be fine, go.",
)

JUDGE_FINE = (
    "Yes, it makes sense - {plan} is a reasonable thing to aim at. The part that bites is doing it "
    "with no answer for what if it goes wrong.",
    "{Plan} is the ordinary thing to do; what bites is doing it with no plan for when it goes wrong.",
    "Yes - {plan} is worth doing. The one thing to have ready is an answer for what if it goes "
    "wrong.",
)

JUDGE_FINE_PLAIN = (
    "Yes, it makes sense. Have a line ready for what you would do if it went wrong, and there is "
    "nothing left to worry about.",
    "It sounds sensible to me. Say in one line what you would do if it went wrong - if that is "
    "easy to say, go.",
)

JUDGE_SANE = (
    "Not mad. {Plan} is the kind of thing plenty of people do, and the test is the one any plan "
    "gets: what would you do if it went wrong?",
    "No, you are not mad. {Plan} is worth weighing, and the thing to have ready is an answer for "
    "what if it goes wrong.",
)

JUDGE_SANE_PLAIN = (
    "Not mad at all. The test is the one any plan gets: what would you do if it went wrong? If "
    "that leaves you all right, go.",
    "No, you are not mad. Wanting something different is normal - have an answer ready for what "
    "if it goes wrong and that is the whole of it.",
)

# Nothing has been named yet, so there is nothing to judge: asking which idea beats shrugging at
# it, and it is the one thing the bot can honestly say. Only for the words that can only mean "was
# my plan daft" - "is that bad" and "is that terrible" are just as often about a symptom or a bit
# of news, and there somebody else has the answer ("is that bad" after "my chicken is still pink
# in the middle" is the food-safety verdict, not a verdict on a plan).
JUDGE_NO_PLAN = (
    "About what? Tell me the idea in a line and I will say what I think.",
    "There is nothing for me to judge yet - say the idea in a line and I will tell you straight.",
)

JUDGE_NO_PLAN_MAD = (
    "Nothing you have said sounds mad to me. What is the thing you are weighing up?",
    "Mad about what? Tell me what you are thinking of doing and I will give you a straight answer.",
)

JUDGE_NO_PLAN_MIND = (
    "Nothing you have said sounds mad to me. And it is worth telling a GP, who hears this often "
    "and knows what to do with it.",
    "That is a frightening thing to carry, and not one to sit on: a GP is the right first call, "
    "and you can describe it in a line.",
    "I would not wait for that to get worse before saying it to somebody. A GP is the one to say "
    "it to - what happens, and how often - and let them say what it is.",
)

JUDGE_NO_PLAN_FINE = (
    "Probably - but say what it is in a line and I will tell you straight.",
    "Nothing you have said sounds unwise to me. What is the thing you are weighing up?",
)

# The answer to a wish to do something to somebody: it is not a plan to weigh up, and the anger
# behind it is the thing worth asking about. Short verdict first, then the question, as STYLE.md
# wants, and no line that offers a hand with the act.
JUDGE_WISH_ANGRY = (
    "No, I would not do that. Something has pushed you a long way - what happened?",
    "That is the anger doing the thinking. Not that one. What has actually gone on?",
    "I would not. Whatever they did, that lands on you and not on them. Tell me what happened.",
)

JUDGE_ONLY_A_PLAN = frozenset(("stupid", "daft", "dumb", "silly", "idiotic", "thick"))

JUDGE_SOUNDS_FINE = frozenset(("wise", "sensible", "smart", "clever", "reasonable"))

JUDGE_SELF_JUDGING = frozenset(("mad", "crazy", "insane", "nuts", "mental", "unhinged"))

# "is that bad" is the commonest way of asking what somebody else's news means ("my sister is
# ill") and the commonest way of asking whether the person should be worried, so with a plan on
# the table it is still not a verdict wanted on the plan: "im going to visit her" / "is that
# bad" wants the care reading, not "nothing daft about wanting to visit her".
JUDGE_NOT_A_VERDICT = frozenset(("bad", "terrible", "awful", "dreadful", "wrong"))

# "ring her mum" ends in "ing" and is not a gerund, so a phrase starting that way was spliced into
# the sentence raw: "Ring her mum is the ordinary thing to do".
JUDGE_NOT_A_GERUND = frozenset(("ring", "bring", "sing", "ping", "cling", "sting", "swing",
                               "wring", "spring", "string", "thing", "kings", "wing", "ding"))

YOURS = {"my": "your", "me": "you", "myself": "yourself", "mine": "yours"}

# A trip the person has just named and a short ask about the place itself - "we are thinking of
# going to Skegness in June" then "is it nice" - has no card anywhere: the knowledge base has
# nothing on Skegness, and the two lines the bot offered for it were a sign-off ("Alright then -
# good luck with it", because a three-word line with "nice" in it read as agreement) and the
# search hedge ("searching will turn up better sources"), which is the coldest thing to say to
# someone looking forward to a week away. These are honest that the bot has not been there, and
# ask the one thing that decides the answer.
A_PLACE_I_DONT_KNOW = (
    "I've not been there, so I can't vouch for it - what are you after: the sights, the food, or "
    "somewhere quiet?",
    "I don't know it well enough to promise you anything. What would make the trip good for you?",
    "No first-hand knowledge of the place, sorry. Are you going for the sights, the food or the "
    "peace?",
    "Honestly I can't tell you what it's like there. What matters most to you about the trip?",
)

WORD_FIXES = {"what": "what", "whats": "what", "wats": "what", "wat": "what",
               "wot": "what", "hows": "how", "whos": "who", "wheres": "where",
               "whys": "why", "whens": "when", "cn": "can", "cud": "could"}

QUESTION_WORDS = frozenset(("what", "why", "how", "when", "where", "who", "which", "can",
                            "could", "should", "would", "will", "do", "does", "did", "is",
                            "are", "have", "has"))

CARD_LINES = (
    "Two lines is plenty: say the thing you would say out loud if they were in front of you.",
    "Name them, say the one specific thing you are glad about, and sign it — short and warm "
    "beats long and clever.",
    "Write it the way you would speak it, then read it back once and take out the careful bits.",
)

# The shape and the offer together: "help me word it firm but not rude" wants both, and a line
# that only says what to do leaves them doing the writing on their own. Every line offers.
# The register for news that lands hard. No "by when", no two-sentence note - the moment and
# the plain sentence are what matter, and every line still offers to help with the words.
TELL_HARD_LINES = (
    "Say the hard sentence first and keep it short - they will hear the rest better after it. "
    "Tell me how you want to put it and I'll help you word it.",
    "Pick a calm moment, say the one thing that matters, then stop and let them answer. Give me "
    "the gist and I'll draft it with you.",
    "Plain words, early, and no long build-up: that is kinder than a soft run at it. Tell me the "
    "gist and I'll help you shape it.",
)

WORDING_LINES = (
    "Say the one thing that matters first, then the rest. Give me the gist and I'll draft it.",
    "Keep it to two sentences: what happened, then what you want. Send me the gist and I'll put "
    "it in words.",
    "Two or three lines is plenty: what happened, what you want, and by when. Give me the gist "
    "and I'll draft it.",
    "Lead with what you want and why, then stop. Tell me the gist and I'll write the first "
    "version for you.",
    "Write it the way you would speak it, then take out the careful bits. Give me the gist and "
    "I'll do a pass over it.",
)

GREETING_WORDS = frozenset(("hi", "hello", "hey", "hiya", "morning", "afternoon", "evening",
                            "greetings", "yo", "howdy"))

# Every line has to be true both cold ("what did i call my car") and in a thread where the
# person has just told the bot ("we named the van beryl" then "and what did i call it?"): "that
# one isn't in my notes" is an argument with the turn before it, so none of these claims what is
# in the notes - they ask for the name and promise to keep it, which is true either way.
NOT_NOTED = (
    "Remind me of the name and I'll keep it from here.",
    "Say the name again and I'll remember it from here on.",
    "I haven't got it in front of me \u2014 tell me the name and I'll hold on to it.",
)

# Words after the verb that are not a name: a time, a pronoun, a place-holder.
NOT_A_NAME = frozenset((
    "yesterday", "today", "tomorrow", "tonight", "morning", "afternoon", "evening", "night",
    "week", "month", "year", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "it", "him", "her", "them", "that", "this", "one", "again", "back", "up", "out",
    "off", "in", "on", "the", "a", "an", "and", "but", "so", "then", "now", "already", "twice",
))

# The words that say what is being asked rather than what about, so two lines share a subject
# only through the others.
ASK_ONLY = frozenset(("what", "whats", "did", "do", "does", "i", "we", "my", "our", "the", "a",
                      "an", "is", "was", "call", "called", "name", "named", "again", "and", "so",
                      "it", "him", "her", "them", "s", "say", "said", "tell", "told", "you",
                      "remember", "recall", "about", "to", "of"))

# Handing back the name they gave a turn ago. The store keeps a relative's name but not a car's,
# a van's or a landlord's, so without this the bot asked a person to say again a name they had
# just given - forgetting what it was told a turn earlier, which STYLE.md rules out.
HANDED_BACK = (
    "You called it {name} \u2014 I've kept that.",
    "{name} \u2014 that's the one you gave me, and it's still here.",
    "It's {name}, isn't it? I've got that down.",
)

# The words a line uses to point at things rather than to say them. They are dropped before two
# lines are compared, so "how do i free up space" and the answer about freeing up space are
# compared on "free", "space" and "photos".
POINTING = frozenset((
    "a", "about", "again", "all", "also", "am", "an", "and", "any", "anything", "are", "as", "at",
    "be", "but", "by", "can", "could", "did", "do", "does", "for", "from", "get", "got", "had",
    "has", "have", "how", "i", "if", "in", "into", "is", "it", "its", "just", "like", "me", "more",
    "my", "no", "not", "of", "on", "one", "or", "our", "out", "should", "so", "some", "still",
    "than", "that", "the", "their", "them", "then", "there", "these", "they", "thing", "things",
    "this", "those", "to", "too", "up", "us", "was", "we", "were", "what", "when", "which", "who",
    "why", "will", "with", "would", "you", "your",
    # A word that names the kind of figure being asked for is not a thing the answer is about:
    # "what year was that" after an answer that says "Germany reunited the following year" is
    # still a question, and the dated sentence of the answer is the reply it wants.
    "year", "years", "date",
))

# A determiner before a word makes it a thing, unless what follows is a particle: "is a voucher a
# cop out" names no new thing, and the answer above already says whether a voucher is a cop out.
RULED_OUT_DETERMINER = frozenset(("the", "a", "an", "my", "your", "his", "her", "their", "our",
                                  "its", "this", "that", "these", "those", "any", "some",
                                  "another", "every", "each", "no"))

PARTICLE = frozenset(("out", "up", "off", "down", "through", "back", "away", "round", "over",
                      "about", "along"))

# Said back the way the bot would say it: their things are the person's, and the bot is asking.
TIPS_OWNER = {"my": "your", "our": "your", "i": "you", "im": "you're", "i'm": "you're",
              "me": "you", "mine": "yours", "we": "you", "us": "you"}

# A subject is a thing, not a sentence: "my new bath" is a subject and "my kid wont eat veg" is
# a report, which the rest of the composer answers. Rejecting a clause keeps the tips lines off
# lines that want empathy or troubleshooting.
TIPS_CLAUSE = frozenset("""
    i i'm im i've ive we we're weve he she they wont will would going
    gonna wanna want wants wanted need needs needed have has had is are was were am do does did
    dont don't didnt didn't cant can't cannot keep keeps kept eat eats eet said say says told get
    got make makes made feel feels felt think thinks thought try tried
""".split())

TIPS_VERB = frozenset("""
    wake sleep stop start learn lose save cook run quit find use take put fix write buy sell move
    change switch pick choose sort become study give tell show send list suggest recommend get
    need want try help make do
""".split())

# The tip or the question comes first and the subject goes inside the second sentence: STYLE
# says not to open by restating the request, and "For your first half marathon, ..." is that
# restatement. The subject is not said back at all after that: quoting it hands a typo back
# (`any tips for my fisrt half maraton`), and a subject that is a person reads as nonsense in
# "advice on a beginner at the gym". "That" carries the meaning without either fault, and the
# reply still names the one question that makes a tip possible, so it is not a line that fits
# any request - the branch only fires on a plea for tips that names a thing.
TIPS_AHEAD = (
    "Start with the one thing that usually goes wrong, not the whole list. How long have you "
    "got?",
    "What's worrying you most about it? With the time you have, that decides what's worth doing.",
    "Pick the part you would most hate to get wrong and practise that bit. When is it?",
)

TIPS_THING = (
    "What have you got so far, and what isn't working? That tells me which advice is worth "
    "having.",
    # Not "I don't know enough about X to guess": that is the shrug this branch exists to avoid,
    # and it reads as a refusal on a line whose subject the person has just named
    # (`any tips for saving money`). Ask the one thing that decides the tip and invent nothing.
    #
    # Not "what's the part that keeps going wrong" either: that fits a problem being worked on
    # (`your cv`, `a new bath`) and not a one-off state like a hangover, which has no part that
    # keeps going wrong. "what you most want to get right" fits both, and a birthday or a
    # wedding is on the deadline side of the split anyway.
    "What's the thing you most want to get right? That's the part worth spending advice on.",
    "What usually goes wrong? Start there, not with the whole list.",
)

TIPS_LINES = (
    "Happy to help — tell me what you've got so far and I'll add what I can.",
    "Sure. What have you tried so far? That tells me where to start.",
)

# The way in when the bot has already answered the thing the ask is about: nothing here asks
# what they have tried, because the answer is what they are asking about.
HELP_ALREADY = (
    "That's most of what I know on it — say which part is still unclear and I'll come at it "
    "another way.",
    "That's the lot I have on that one. Tell me which bit isn't landing and I'll try a "
    "different angle.",
)

# A line that asks again what the reply above it answered gets this, not HELP_ALREADY: "say which
# part is still unclear" is right for a bare ask ("any tips") and wrong here, because the person
# did not say anything was unclear - they asked again, or asked a narrower version. The reply
# says the answer above is all of it and offers to go over it, without claiming it failed.
SAME_AGAIN = (
    "That is all of what I know on it - say if you want any part of it again, or slower.",
    "That was the whole of my answer on it. Tell me which part to take further and I will.",
    "That is everything I have on that one, so I would only repeat myself. Which bit do you want "
    "me to go into?",
)

# The same turn, when the answer is still on the screen: a repeat has to carry what it repeats.
# "That is everything I have on that one, so I would only repeat myself" names the answer above
# and then hands the person none of it, which is a shrug with the answer sitting one turn back -
# STYLE.md is plain that the answer twice beats a shrug. The lead-in says the answer above is the
# answer, so the repeat is not read as a new question, and then it says it.
SAME_AGAIN_WITH_THE_ANSWER = (
    "Same answer, and it covers this: {answer}",
    "That is still the answer: {answer}",
    "The answer above holds: {answer}",
)

# The words a line can be made of and still be asking only for a view. Anything else names a
# subject, and a subject has an answer of its own to look up.
VIEW_ONLY_WORDS = frozenset("""
    a an the and but so or if to of at on in with about between for from as
    what whats is was your my you u ur ya i me we us our it its that this there here
    be is are do does did would could should will can
    reckon think say said view opinion take takes thoughts verdict read call answer answers
    honest honestly own real true personal actually really truly
    ok okay well then now just too also again please thanks thank
    give tell me full whole thing things one on it that this
    d r wat
""".split())

# The view is the front of the answer: the claim it opens with, up to its colon. "A chain that
# skips under pressure is usually worn, and so is the cassette behind it: a chain checker..." - the
# view is the worn chain and cassette, not the checker.
VIEW_LINES = (
    "Honest answer: {said}",
    "Same as I said: {said}",
    "My view has not changed: {said}",
    "Honestly, that is still where I would land: {said}",
)

# When the answer above was itself a question, the same frames promise a stance and then hand back
# a question mark: "Honest answer: what would have to be true for the answer to be yes?" reads as a
# view that never arrives, and "Honestly, that is still where I would land:" in front of one is a
# promise broken in the same line. A question can still be the view - it is the bot's question, and
# it is the right one - so the frame says that instead of claiming a stance.
VIEW_ASK_LINES = (
    "What I would still want to know: {said}",
    "Same question from me: {said}",
    "I would still ask you the same thing: {said}",
    "That question is still the one I would put to you: {said}",
)

# The answer before it was "that one is your call, not mine": quoting a refusal back as a view
# ("My view: not mine to decide, sorry") is the same wall twice, and the search hedge it replaces
# is worse still, because no search settles whether to buy the bike. What a friend does there is
# name what the decision turns on and ask for the two things being weighed.
VIEW_DECIDE = (
    "Same as before: that one is yours to call. What it turns on is what you gain against what "
    "you would give up — say both and I will help you weigh them.",
    "It stays your call rather than mine. Tell me the two things you are weighing and I will lay "
    "them side by side.",
)

# The handback itself, so it is recognised whatever wording the pool gave it.
VIEW_HANDBACK = ("not mine to decide", "not a call i can make", "can't call that one",
                 "cant call that one", "that's your call", "thats your call")

# The pools that react to a line without answering it. A view of one of these is a quote of the
# bot being polite, and the decision underneath says what the call turns on instead.
NOT_AN_ANSWER = NEUTRAL + NEWS_TO_COME + POSITIVE + RELIEF + CONGRATS

# The little words that say nothing about the subject, so an echo can be measured on the rest.
_ECHO_FILLER = frozenset("""
a an the i im i'm ive i've id i'd me my we us our you your it its it's that thats this these
those is are was were am be been being do does did done have has had of to in on at for with
and but so then than just really very quite too also about from by as or if not no yes yeah ok
okay well right got get gets here there what whats how why when who said say says think
""".split())

# The praise a congratulations line is made of. A view asked for on top of one has no claim to
# stand behind - the bot said well done and asked about the celebration - so the answer says the
# good news is the whole of it instead of quoting the politeness back.
PRAISE = ("congratulations", "congrats", "well done", "nice one", "brilliant", "lovely",
          "great news", "good stuff", "glad", "pleased", "fantastic", "amazing", "excellent",
          "love that", "that's great", "thats great", "weight off", "good for you", "enjoy it")

VIEW_ON_GOOD_NEWS = (
    "Nothing to weigh up there - that is just good news. Enjoy it: what is the first thing "
    "you will do about it?",
    "Honest answer: take the win. There is no decision in it, and I would not spoil it hunting "
    "for one. What happens next?",
)

# Every pool whose line means "I do not know enough": the bot must not stand behind one of those
# as its view, because "my view has not changed: I don't know" is a worse non-answer than the
# hedge itself. The routes in `finding_out` belong here for the same reason: "a map app will
# give you the address" is the bot saying it does not hold the answer, and it must never be
# stood behind as an opinion or counted as a card that beats one.
HEDGE_POOL = (UNKNOWN, UNKNOWN_DECIDE, UNKNOWN_MONEY, UNKNOWN_HEALTH, UNKNOWN_WORD,
              UNKNOWN_WORRY, finding_out.PLACE_POOL, finding_out.TRADE_POOL,
              finding_out.PROFESSIONAL_POOL, finding_out.PICK_POOL, finding_out.WHO_POOL,
              finding_out.HOW_MANY_POOL, finding_out.BUY_POOL, finding_out.FIGURE_POOL,
              finding_out.WRECKED_POOL, finding_out.PLACE_ROUTE_POOL)

OUTCOME_LINES = (
    "Nobody can say for certain yet, and anyone who does is guessing. Ask the staff looking after "
    "them what they are watching for over the next day or two, and what would be a good sign.",
    "There is no honest yes or no from here - the ward is the only place with a real answer. Ask "
    "the nurse in charge what has to improve before the next step, and ask again tomorrow.",
    "No one can tell you that yet. The people treating them can say what they are watching for "
    "and what a good day would look like, and that is the question worth asking today.",
)

# A view given back after one of those openers is not "my view": the answer it stands behind is
# the part that says something, and the opener for it says the bot would say it again.
VIEW_MIRROR_LINES = (
    "Nothing has changed for me: {said}",
    "I would say the same again: {said}",
    "That still stands: {said}",
)

# When the whole answer was company there is nothing to give back, and the search hedge is the
# one reply a bereavement must not get: "my dog died" / "honest view?" was "I don't know enough
# to answer that honestly. A search should sort you out quickly".
VIEW_COMPANY = (
    "Nothing to add to that, and no view of mine worth putting on top of it. What I said still "
    "stands, and I am here if you want to say more.",
    "I have not got a view to give you on top of that - only the same thing again, which is that "
    "it matters. Tell me how you are doing with it.",
    "Nothing I could add would beat what I already said. If you want to say more about it, I am "
    "listening.",
)

# "whats your honest view" as the first thing said names no subject at all: the person has
# something in mind and has not told the bot what it is, so the search hedge ("a quick search
# online will get you a solid answer") points at nothing, and "no strong view on that one, honestly"
# pretends to have heard a subject. What a friend says is one short question that gets the subject.
VIEW_NO_SUBJECT = (
    "On what? Give me the thing you are weighing up and I will tell you straight.",
    "Happy to - what's it about? Name the choice you are stuck on and I'll give you my honest take.",
    "What is it about? Name the thing you are stuck on and I will give you my honest take.",
)

# After a death, a "what do you think" is not asking the bot to grade the condolence, and the
# answer is not a shrug with a search in it either: "my dad died last month" / "what do you think"
# got "There is nothing I would say differently, and nothing for you to go and look up." - the bot
# as a judge with a link, on the one turn where it should just be a person. There is no fact to
# stand behind here, so the view is the one thing a friend does say, and it is about the person's
# grief rather than the bot's opinion.
VIEW_AFTER_A_DEATH = (
    "If it is my view you want: nobody gets this right, and being all over the place is not doing "
    "it wrong.",
    "Honestly? There is no right way to do it, and no timetable you have to be on.",
    "My view is only that it is allowed to be this hard. You are not doing it wrong.",
    "Nothing I could add would help more than what I said. Tell me about them, or don't - either "
    "is fine by me.",
)

# A lead-in names the form of what follows rather than the thing itself: "The things that work:
# same wake-up time every day" is about the wake-up time.
VIEW_LEAD_IN = frozenset((
    "thing", "things", "way", "ways", "point", "points", "answer", "answers", "plan", "rule",
    "rules", "step", "steps", "advice", "short", "version", "part", "parts", "bit", "bits",
    "key", "difference", "same", "rest", "other", "first", "next", "best",
))

# Replies there is no "more" of: the composer's own pools, and the turns where the answer was
# safety, a death or a grief: "my dad died" / "what about the funeral" is not a request for the
# rest of the fact, and a red-flag answer is never followed by "that's most of what I know".
NO_MORE_OF = frozenset(("", "greeting", "safety", "urgent", "grief", "loss"))

# Chat-speak in the words a subject is built from: a person typing "any tips 4 a hangover" means
# "for", and echoing "4 a hangover" back at them is not a reply about a hangover. Only a digit on
# its own is a word - "10k", "2pm" and "1920s" are left alone - and the mapping is one way, so a
# subject never comes back with a digit it was not given.
# A digit standing alone is read as the word it stands for, so "any tips 4 a hangover" names its
# subject. A digit before a unit of time or measure is a number, not a word: "any tips for my 2
# year old" is an age, and mapping it gives "your to year old". Units are a closed list; anything
# else counts as chat-speak.
TIPS_UNIT = frozenset(("year", "years", "yr", "yrs", "month", "months", "week", "weeks", "day",
                       "days", "hour", "hours", "min", "mins", "minute", "minutes", "stone",
                       "st", "kg", "kgs", "lb", "lbs", "pound", "pounds", "mile", "miles", "km",
                       "k", "quid", "grand", "per", "cent", "percent"))

WHERE_SOMETHING_WRONG = SICKNESS | frozenset((
    "leak", "leaks", "leaking", "damp", "mould", "mold", "smell", "smells", "smelly", "noise",
    "broken", "broke", "trip", "tripped", "tripping", "fuse", "wiring", "wire", "hurt", "hurts",
    "hurting", "pain", "painful", "sore", "ache", "aches", "aching", "rash", "bite", "bitten",
    "sting", "stung", "bump", "bleed", "bleeding", "swollen", "swelling", "crack", "cracks",
    "cracked", "blocked", "clogged", "wont", "won t", "not working", "stopped working",
    "chest", "throat", "stomach", "tummy", "belly", "back", "head", "leg", "legs", "arm",
    "arms", "hand", "hands", "foot", "feet", "knee", "knees", "shoulder", "neck", "hip",
    "wrist", "ankle", "toe", "toes", "finger", "fingers", "eye", "eyes", "ear", "ears",
    "tooth", "teeth", "gum", "gums", "mouth", "skin", "joint", "joints", "ribs", "breast"))

QUOTE_LINES = (
    "Get one more quote for the same job in writing, and ask what is included: the parts list is "
    "what makes two prices comparable.",
    "Ask for a written quote split into parts and labour, then ring one other firm for the same "
    "job. That pair of numbers tells you more than any rule of thumb.",
)

# A present for a new baby is a gift question, and a baby mentioned in one is not a symptom:
# "how much do you spend on a new baby present" is not the health visitor's call.
GIFT_WORDS = frozenset(("present", "presents", "gift", "gifts", "spend on", "budget for",
                        "how much do you spend", "what do you get"))

# A home to buy is not a tenancy: "im 34 and still renting, should i be buying" wants the
# buying side, and Citizens Advice's tenant line would be answering a different question.
BUYING_WORDS = frozenset(("buying", "buy a house", "buy a flat", "buy a home", "bought",
                          "purchase", "ladder", "mortgage", "own a home", "should i buy"))

# A medicine is not a device: "can i take hayfever tablets with my blood pressure pills" is the
# pharmacist's question, while "my tablet wont connect to the wifi" is the maker's.
# A router is a device you log into, so it keeps its maker's page: it is the wifi itself,
# and what runs on it, that no support page can answer for.
NETWORK_WORDS = frozenset(("wifi", "wi-fi", "internet", "broadband", "network", "connection",
                         "signal", "online"))

# A drug or a supplement is the pharmacist's, by name: "should i take vitamins" is not a reason
# to ring 111, and the counter answers it in two minutes for free. `vitamins` and the brand-free
# drug names were missing, so those lines fell to the plain shrug.
MEDS_WORDS = frozenset(("tablets", "pills", "medicine", "medication", "prescription", "dose",
                        "doses", "capsules", "antibiotics", "vaccine", "vaccination", "jab",
                        "jabs", "vitamin", "vitamins", "supplement", "supplements", "ibuprofen",
                        "paracetamol", "aspirin", "painkiller", "painkillers", "antihistamine",
                        "antihistamines", "steroid", "steroids", "insulin", "inhaler"))

# A longer word counts as a form of an evidence word only when the extra letters are the ending
# of that word ("boilers", "coughing", "evicted", "itchy", "eviction", "dampness"). Prefix
# matching alone said a toothbrush was a tooth (so a dentist was the answer to brushing it), that
# pesto was a pest (so every pesto line got "a pest controller is the one to call"), that a
# rasher was a rash, that an example was an exam and that "i feel bloody awful" was blood. A row
# names the compound itself when it means one ("toothache", "pensioner", "firewood").
ENDINGS = frozenset((
    "s", "es", "ed", "d", "ing", "e", "y", "ion", "al", "ness", "able", "ly",
))

# Words that end with one of those and are still not the evidence word. "bloody" is an
# intensifier ("i feel bloody awful"), so the blood row must not answer it.
NOT_A_FORM = frozenset((
    "bloody", "rasher", "rashers", "teether", "waker", "stationary",
    # "teething" is "teeth" with the ending on it only by the look of it: the verb is "teethe",
    # so a teething baby is cutting teeth, while "teething problems with the new car" is a new
    # thing finding its feet. The dentist row matched the second and answered a new car with
    # "ring practices near you ... whether they take new NHS patients". The word is whole in the
    # rows that want it (the baby's row names "teething"), and the noun "teeth" still reads.
    "teething",
))

# The question words that open a question on their own. "do", "is", "are" and "can" are
# left out: they need the inversion shape below, because "do not know why" is a statement and
# "can you help" is an ask.
_OPENING_QUESTIONS = frozenset(("what", "why", "how", "when", "where", "who", "which"))

# The one-word answer about the bot's own nature that a topic entry must not take on a matched
# word: the machine it is made of, the edges of what it can do, and whether it is connected.
# "identity" and "purpose" belong here and did not. `_about` reads "am i talking to a human" as an
# identity question (HUMAN_ASK) and "whats the point of you" as a purpose one, but neither kind was
# in this set, so the reading was made and thrown away and any entry holding the verb took the
# line: the speaking-clearly card answered "am i talking to a human", and the university entry
# requirements answered "whats the point of you". The reading is the narrow part; this set is only
# the claim, so the kinds go in together.
ABOUT_ITSELF_KINDS = ("model", "limits", "online", "agency", "identity", "purpose",
                      "workings", "privacy", "trust", "judging", "secret", "asking")

MODEL_NAMED_WORDS = 7

# The kinds `_about_itself` returns that the arbiter claims the turn for: a question about how the
# bot learns or thinks has the bot as its subject, and a topic entry's only hold on such a line is
# the verb ("learn" matched a revision plan). The arbiter reads this set rather than keeping its
# own list, so the reading and the claim sit with the reading.
# "wrong" joined them on the same terms: "do you ever make mistakes" and "are you always right"
# are questions about the bot that no module had read as one, so the tomato chat answered them
# with a tomato sauce. Unlike "feel" or "purpose", the bot's own answer is the only one there is.
MY_WORKINGS = frozenset(("learn", "think", "wrong"))

PICKS_A_MECHANISM = frozenset("""
decide decides deciding decided decision decisions choose chooses choosing chosen choice choices
pick picks picking select selects sort sorts answer answers answering answered
""".split())

# "i'm worried", "im so anxious", "nervous now": the same fear as "scared", for the people who
# say it that way. Only bare: "worried about her appointment on tuesday" is a practical line
# about the appointment and keeps the practical continuation, so anything with `about`, or with
# a content word of its own, is not this.
WORRY_FILLER = frozenset("""
    i im i'm am so really very pretty quite a bit little lot kind kinda of still just and ok
    okay that thats it its now too much all this
""".split())

WORRY_WORDS = frozenset("worried worrying anxious nervous".split())

# A word of what they do only counts where they are the one doing it. "my mum is 78 and not
# very good with phones" has "phones" after a preposition, and "my girlfriend says im not
# listening" has "listening" with "i" as its subject: neither is a grumble about them.
NOT_THEIR_VERB = frozenset(("with", "for", "about", "of", "to", "at", "in", "on", "from",
                            "by", "like", "without", "over", "under", "into", "the", "no",
                            "any", "some", "his", "her", "their", "your"))

FIRST_PERSON = frozenset(("i", "im", "i'm", "i am", "me", "am", "you", "we", "us"))

FORGETTING = frozenset(("forget", "forgets", "forgot", "forgetting"))

# What a person has for dinner is not what they do to the speaker. "My husband who eats meat"
# is a diet, and the grievance pool answered it with "that wears you down - shall we think about
# how to raise it", which is a row that was never happening: the person was asking what to cook
# for the two of them. "My partner eats all the biscuits" is still a grumble, so it is the food
# named that decides, not the verb.
EATING = frozenset(("eat", "eats", "eating", "ate", "eaten"))

EATEN_KIND = frozenset((
    "meat", "fish", "dairy", "gluten", "nuts", "eggs", "cheese", "pork", "beef", "chicken",
    "lamb", "bacon", "ham", "shellfish", "seafood", "sugar", "carbs", "bread", "rice",
    "pasta", "chips", "vegetables", "veg", "veggies", "fruit", "salad", "spuds", "potatoes",
    "vegan", "vegetarian", "halal", "kosher",
))

OURS = frozenset(("my", "our", "me", "us"))

GOOD_TIME_WORDS = frozenset("""lovely great brilliant wonderful good nice amazing fun fantastic
    smashing crackin delicious gorgeous tasty superb class memorable""".split())

# The words a question opens with. The composer's clean line has no punctuation, so "was the
# wedding good" arrives without its "?" and the opener is the only thing that says it is a question.
QUESTION_OPENERS = frozenset("""was were is are am did does do have has had how what when where
    why who whose would will can could should shall may might""".split())

# Not every "it was lovely" is a verdict on an evening. The people and the places a hard week
# goes through are judged in the same words - "the ward was nice" and "the nurses were lovely" in
# a thread about somebody in hospital are about care, and "That sounds like a good time - what
# was the best of it?" answers them as if the person had been out for the night. The wake and the
# funeral are the same word with the worst week in it. So the subject stands this reading down.
NOT_A_VERDICT_SUBJECT = frozenset("""
ward hospital hospice clinic surgery casualty a&e icu itu nurses nurse staff doctors doctor
consultant midwife surgeon matron theatre anaesthetic anaesthetics wake funeral burial cremation
crematorium memorial chapel servicio tests results scan chemo chemotherapy dialysis
service services eulogy eulogies graveside flowers mass readings reading sermon hymn hymns vigil
rosary cemetery ashes casket hearse obituary tributes tribute condolences send-off sendoff
paramedics ambulance paramedic carers carer counsellor counsellors physio physiotherapist vet vets
police firemen firefighters
""".split())

# A mild dread - a Monday, a meeting, a visit, a phone call - is not the heavy negative pool
# ("That sounds rough. If you want, I can help you think through what to do next"), which is for a
# bad week, and it is not the floor either ("I'm listening - say more if it helps"), which a person
# reads as not being listened to. It is the light question a friend asks.
A_DREAD = (
    "Fair enough - what's the part you're dreading?",
    "That's understandable. What's coming up that you're not looking forward to?",
    "I don't blame you. What is it about it?",
)

# A thing the person wants behind them - "i cant wait for this week to end", "cant wait for the
# term to be over", "roll on friday so this is done" - is the reverse: the thing coming is the end
# of a bad stretch, so the forward-looking pool ("That's worth looking forward to. Tell me how it
# goes") congratulates them on it and the floor says nothing. What a friend says is that it sounds
# like a long one and asks what has made it so.
A_WANT_IT_OVER = (
    "Sounds like it's been a long one - what's been the worst of it?",
    "Fair enough. What's making it drag?",
    "That sort of week does that to people. What do you most want behind you?",
)

# Not `A_THING_AHEAD`: that name is already the pool for a job the person is about to do
# ("im painting it tomorrow", "im doing my essay tonight"), which is a different reading, and
# giving the two one name sent every job to this pool.
A_DAY_AHEAD = (
    "Something to look forward to, then - what's the plan?",
    "Nice. How are the plans going?",
    "Good. Is there much to sort out first?",
)

A_DAY_AHEAD_TENSE = (
    "How are you feeling about it?",
    "How ready do you feel for it?",
    "Is there much to get ready before it?",
)

# The words a reason for the gap is introduced with ("work has been mad so sorry for the silence",
# "ive been quiet because work has been mad") are the same pause as the apology: without them the
# words around "because" are the reason, and the reason is not a subject the bot can answer.
#
# The small words an apology for the gap can leave behind and still be nothing else: "sorry, i
# fell asleep and only just saw this" is the gap, "sorry i went to get the kids, anyway the
# boiler is leaking" is the boiler. A word outside this set is content of its own, and the line
# belongs to whatever answers it.
A_PAUSE_WORD = frozenset("""
    a an the and or but so then than that this these those it its im i i've ive id i'd me my
    mine we us our you your yours he she they them his her their there here now just only really
    very quite bit little all of in on at to for from with about as if not no yes oh ok okay
    sorry apologies apologie again back still also too already been was were is are am be being
    because cos cause cus since seeing
    do did done does have has had yet soon later earlier yesterday minutes min mins sec secs
    second seconds moment moments hour hours while ago a while day days week weeks month months
    year years morning afternoon evening night long ages spell tomorrow late lately
    phone mobile phones laptop computer inbox messages message emails email texts
    i've we've you've they've ive weve youve theyve
""".split())

# How a stretch of time went, when the reason for the gap is a period rather than a thing:
# "sorry ive been quiet, work has been mad" is the gap, and the annoyance card answered it
# ("Annoying. Walk it off for ten minutes") off the word "mad" alone. None of these is a subject
# the bot can do anything about, so none of them is the line's own.
A_HOW_THE_TIME_WENT = frozenset("""
    mad crazy manic hectic mental busy rushed rush flat slammed swamped snowed frantic chaotic
    stressful stressed rough tough hard awful rubbish terrible horrible grim rotten bad long big
    heavy weird odd slow uphill nights shifts deadlines overtime full non-stop endless relentless
    nutty silly wild madder worse better fine ok
    work life things everything stuff week weeks month months year years day days time times
    while spell age ages morning night nights weekend weekdays lately recently overnight
    behind on ahead late over under through away out
""".split())

MANNERS_ONLY = frozenset("""
    sorry apologies apology apologise apologize bother bothering bothered ask asking asked
    question questions one more thing another pain nuisance hassle trouble troubling troubled
    pester pestering nag nagging
    keep keeping going on essay ramble rambling dump dumping moan moans moaning moaned
    interrupt interrupting
    time i im me you your my it this that just again so really very bit lot a an the and but also
    to for of about at with be being am is was had have been can could would please thanks thank
    ok okay well honestly tbh quick quickly stupid silly daft late slow early knowing know
    go goes going do did does
    """.split())

THANK_WORDS = frozenset(("thanks", "thank", "thankyou", "cheers", "ta", "appreciate",
                         "appreciated"))

# The words a line of thanks can be made of without saying anything else: "thats good to know
# thanks", "right thanks", "thats me sorted thanks". Those read as a statement, so they reached
# the neutral pool and got "Thanks for telling me", which thanks the person for having spoken
# instead of answering the thanks.
THANKS_ONLY = MANNERS_ONLY | frozenset("""
    thats that's good know great brilliant brill perfect lovely helpful useful sorted right nice
    much many so much ace wonderful excellent amazing legend star lifesaver kind kindly
    for the advice help
    all everything then too will do
    """.split())

# A thank-you with the outcome after it - "thanks, it's stopped", "thanks, the boiler is fine
# now", "cheers, that sorted it" - is not manners on their own, so `_thanks_with_more` does not read
# it, and every pool below answered as if the person had said nothing: "I'm listening - say more if
# it helps", "Got it. Is there anything you'd like a hand with?", "Thanks for telling me - I'm here
# if you want to dig into any of that". Each of those drops both halves of the line, and the second
# half is somebody coming back to say the thing worked. The thanks is answered and the outcome is
# taken as said; how it went is not claimed, because "it's stopped" and "the boiler is fine now" are
# their own words and "glad to hear it" is true of the lot.
THANKS_THEN_SAID = (
    "Glad to hear it — and thanks for coming back to say so.",
    "Good. Thanks for letting me know.",
    "Pleased for you. Thanks for telling me how it went.",
    "That's good to hear. Thanks for saying so.",
)

# Which of the composer's own replies a line gets when it is not an ordinary line. A line inside
# a safety thread keeps the thread only until a module that declares its topic speaks for it; the
# death reading is a module of its own now (bot/modules/loss.py, ANSWERS_INSTEAD), so it is not
# one of these kinds.
THREAD = "thread"

# The same thread, and the answer the person is still following was first aid rather than a
# crisis line: a burn, a cut, a bad back. The arbiter treats it differently in one way only -
# a follow-up about the very thing the bot just answered keeps the thread even when a topic
# entry claims the word ("can i pop the blister" after the scald answer). A crisis answer keeps
# no such claim, because the next question in a crisis is often about something else entirely.
CARE_THREAD = "care-thread"

# Words a follow-up can share with the answer it follows without being about the same thing.
# The rule needs a word that names something, so the little ones are left out.
PLAIN_WORDS = frozenset((
    "about", "after", "again", "anything", "before", "being", "could", "doing", "every",
    "going", "happen", "having", "should", "something", "still", "their", "there", "these",
    "thing", "things", "think", "those", "through", "today", "tonight", "would", "your",
    "yours", "mine", "with", "what", "when", "where", "which", "while", "whole", "leave",
))

# "ill" at the start of what someone typed is nearly always "I'll" ("ill book her in", "ill try
# that"), and reading it as "sick" gave "ok ill book her in tomorrow" the reply "That sounds
# rough". So "ill" only means sickness where the line says so: after a copula or an adverb
# ("i feel ill", "so ill"), before a duration ("ill for a week", "ill again"), or on its own.
ILL_BEFORE = frozenset(("feel", "feels", "feeling", "felt", "being", "been", "so", "very",
                        "really", "quite", "still", "get", "gets", "getting", "got", "fell",
                        "am", "im", "is", "was", "are", "looks", "look", "too", "seriously",
                        "badly", "terribly", "always", "often", "chronically"))

ILL_AFTER = frozenset(("for", "again", "all", "and", "today", "tonight", "lately", "since",
                       "this", "last", "week", "weeks", "day", "days", "month", "morning",
                       "at", "in", "on", "with", "from", "health", "enough", "yesterday"))

# The word before "ill" that makes it a body: "im ill", "she was ill", "he looks ill". A degree
# word ("so", "very", "still") is not one of these, because "i got a pay rise so ill be on 34k"
# is "I will" - the same shape as "so ill be late" and "ill be there by eight". So the word after
# it is read first, and only these make "ill" an illness whatever follows.
ILL_SAID_OF_A_BODY = frozenset(("am", "im", "is", "was", "are", "feel", "feels", "feeling", "felt",
                                "been", "being", "looks", "look", "get", "gets", "getting", "got",
                                "fell", "seriously", "badly", "terribly", "chronically", "often"))

# The verbs that turn "ill" into "I will": nobody is ill *be* on 34k.
ILL_WILL_VERBS = frozenset((
    "be", "have", "get", "let", "try", "call", "text", "ring", "phone", "see", "tell", "say",
    "give", "send", "check", "do", "go", "come", "take", "make", "bring", "put", "keep", "look",
    "ask", "email", "message", "book", "order", "pay", "pop", "head", "drive", "walk", "run",
    "start", "finish", "show", "wait", "find", "grab", "meet", "stay", "sit", "sort", "write",
    "add", "fix", "clean", "tidy", "wash", "buy", "sell", "need", "want", "drop", "pick",
    "leave", "turn", "sign", "carry", "chat", "speak", "read", "eat"))

AIM_HEADS = frozenset(("want", "wants", "wanting", "trying", "try", "need", "needs",
                       "hoping", "hope"))

AIM_NEGATORS = frozenset(("not", "dont", "doesnt", "didnt", "never", "no", "wont", "cant"))

AIM_FAILING = frozenset(("wont", "doesnt", "isnt", "nothing", "stuck", "nowhere", "stopped",
                         "hopeless"))

# A word that says how someone is, rather than something they did: only these turn into a bad
# line when a negator stands in front of them.
STATE_CUES = frozenset((
    "happy", "excited", "amazing", "proud", "delighted", "thrilled", "brilliant",
))

# Some bad-week words are also things: "bit of a rubbish week", "it was crap" against "take the
# rubbish out", "the rubbish bin is full". The mood is only safe where the word says what
# something was like, which a copula in front or a time word behind tells you and a determiner in
# front does not: "the rubbish got collected" is a chore, and answering it with "that sounds
# rough" would be the bot hearing a mood in a bin bag.
JUNK_CUES = frozenset(("rubbish", "crap", "crappy", "naff", "meh", "bleh", "poo"))

MOOD_BEFORE = frozenset((
    "is", "was", "were", "are", "am", "feel", "feels", "feeling", "felt", "seems", "seemed", "be", "been",
    "being", "so", "very", "really", "quite", "pretty", "totally", "absolutely", "bit",
    "such", "that", "this", "fairly", "properly"))

MOOD_AFTER = frozenset((
    "week", "weeks", "day", "days", "month", "morning", "afternoon", "evening", "night",
    "weekend", "year", "time", "start", "shift", "term", "few", "couple"))

# A copula in front of a junk word says the line is about whatever stands before it: "the food
# was crap" is a claim about the food, and "i feel rubbish" is a claim about the person. So the
# subject decides (see `_a_mood_word`), which is the same read as `NOT_ABOUT_THEM` for a stretch.
# Words that are a mood only in one shape. Each is a verb a person also does to something, so the
# passive ("got", "was") or the person as the object ("they fired me") is what makes it their bad
# day. Anything else with the word in it is about the thing they did.
A_MOOD_WITH_A_CATCH = {
    "fired": frozenset(("got", "get", "gets", "getting", "was", "were", "is", "are", "am", "been",
                        "being", "have", "has", "had", "ve", "i've", "we've", "they've")),
}

COPULA = frozenset(("is", "was", "were", "are", "am", "seems", "seemed", "be", "been", "being"))

ABOUT_THEM_BEFORE_COPULA = frozenset((
    "i", "im", "i'm", "ive", "i've", "me", "we", "we're", "were", "us", "myself", "everything",
    "things", "life", "it", "this", "today"))

RUMINATION_REPLIES = (
    "That sounds like it is still sitting with you. What is the part that keeps coming back?",
    "A worry at 2am is rarely the same shape as one in daylight. What actually happened?",
    "Going round it that many times is exhausting. Say it out to me — what keeps coming back?",
    "Fair enough — that kind of thing does not let go on its own. What is the bit you keep "
    "landing on?",
)

# A body state and nothing else in the line: "im cold", "im freezing", "im starving", "im
# boiling". Nothing in the app can act on being cold, so these fell all the way to the neutral
# nod - "I'm listening - say more if it helps", which is what a person says when they were not
# listening - or to the search hedge. What a friend does with a cold room or an empty stomach is
# one practical thing and one small question about the situation, which is what the pools say.
# Only the four states a body can be in this way are read here: tiredness, being fed up and the
# rest are feelings, and they have their own readings above. A body that is too cold or too warm
# is read without guessing why - "im cold" can be a fever starting and "im hot" can be a room
# with no window - so the reply offers the practical thing and asks.
BODY_STATES = {
    "cold": frozenset(("cold", "freezing", "frozen", "chilly", "chilled", "perished",
                       "baltic", "icy",
                       # Shivering is what a cold body does, and the three spellings reach the
                       # normaliser as "shivering" ("im shiverin" -> "i am shivering"), so the
                       # pool has to know the word or the person gets the neutral nod. A line
                       # that already has its own card keeps it: "i keep shivering" still gets
                       # the shivering card and "i feel shivery" the fever one, because a
                       # knowledge row answers before these pools do.
                       "shivering", "shivery")),
    "hot": frozenset(("boiling", "hot", "roasting", "sweating", "sweaty",
                      "sweltering", "baking", "melting")),
    "hungry": frozenset(("hungry", "starving", "starved", "famished", "peckish",
                         "ravenous")),
    "thirsty": frozenset(("thirsty", "parched", "dehydrated")),
    # The body states a person reports that have nothing in the app to act on and no pool to
    # land in, so they reached the neutral nod ("im queasy" - "I'm listening - say more if it
    # helps") or, while the -y words were read as names, an introduction ("im shaky, nice to
    # meet you Shaky"). Each of these is one practical thing and one question about what it is
    # like, which is what a friend says, and light-head is the one that has to be taken slowly.
    "light_head": frozenset(("faint", "fainted", "fainting", "faintish", "woozy", "dizzy",
                             "giddy", "wobbly", "shaky", "lightheaded", "groggy")),
    "queasy": frozenset(("queasy", "queezy", "nauseous", "nauseated", "sickly", "bilious")),
    "bunged": frozenset(("bunged", "bungedup", "blockedup", "sniffly", "sniffles",
                         "sniffing", "croaky", "hoarse", "sneezing", "congested", "husky",
                         "snotty")),
    # How the body looks, and none of these had a pool: "im clammy" was read as the warm end of
    # the weather ("Too warm to think straight in. Open a window") when a clammy skin is a cold
    # sweat, and "im pale", "im flushed", "im spotty" and "im puffy" had no reading at all -
    # they reached the neutral nod, or, while the words were read as names, "Nice to meet you,
    # Pale". A state of the body is answered like the others here: one practical thing and one
    # question, and the emergency is named only where the sign is one (a cold sweat with a
    # faint), because a fever breaking and a shock both make a person clammy and the line alone
    # cannot tell them apart.
    "clammy": frozenset(("clammy", "clamy", "clammyish", "coldsweat", "coldsweats")),
    "pale": frozenset(("pale", "pallid", "ashen", "grey", "gray", "greyish", "grayish",
                       "mottled", "blotchy", "washedout")),
    "puffy": frozenset(("puffy", "bloated", "swollen", "puffed", "puffing")),
    "spotty": frozenset(("spotty", "pimply", "acne", "brokenout")),
}

# What can follow the state word and leave the state the whole of the line: "im cold today",
# "im freezing now". Anything else after it is a thing rather than a state ("im boiling eggs",
# "im cold water" makes no sense but "cold water" is a thing, "im starving myself" is not
# hunger), and those keep the reading they had.
BODY_TAIL = frozenset(("today", "tonight", "now", "still", "again", "though", "honestly",
                       "already", "outside", "here", "actually", "really", "so", "very",
                       "absolutely", "bloody", "thanks"))

# The same line with the situation named after it: "im cold all the time", "im freezing in this
# house", "im starving at work".
# How long it has gone on, and how far in it has got, is part of the state rather than
# anything else about it: "im chilled right through" and "im freezing all morning" are the same
# report as "im cold", and both went to the neutral pool because the words after the state word
# were not in the tail list. The list of stretches is the times of day people actually say.
BODY_SITUATION = ("all the time", "all day", "all night", "all morning", "all afternoon",
                  "all evening", "all week", "all weekend", "in here", "in this house",
                  "in this weather", "at night", "at work", "in the night", "right through",
                  "to the bone", "through to the bone", "all day today", "all day yesterday",
                  "all night long")

BODY_PART_TAIL = frozenset(("", "today", "now", "still", "again", "already", "outside"))

# What can sit between the part and the cold word and leave the line a part being cold: "my nose
# is really cold", "my ears are absolutely freezing", "my ears are always cold". "my ears are red
# and cold" is a different line - the words in front say something else is going on - so the
# qualifier has to be one of these rather than anything short.
BODY_PART_QUALIFIER = frozenset((
    "really", "so", "very", "proper", "properly", "absolutely", "completely", "totally",
    "always", "still", "bit", "little", "a", "dead", "stone", "bloody", "permanently",
    "freezing", "bitterly", "that", "quite", "pretty", "fairly", "completely"))

# A second state said in the same breath ("im cold and tired", "im starving and grumpy") -
# the first one is what the reply is about, and the line is still short enough for it.
# What can come before "im" and leave the rest of the line the state: "so im cold", "god im
# freezing", "honestly im starving". Anything with more in front of it is asking about the
# reading ("do you think im cold") or reporting somebody else's words.
BODY_LEAD = frozenset(("so", "oh", "ah", "god", "honestly", "well", "and", "also", "tbh", "ok",
                       "okay", "literally", "seriously", "man", "ooh", "ugh", "yeah", "no"))

BODY_ALSO = frozenset(("tired", "knackered", "exhausted", "shattered", "grumpy", "sore",
                       "achy", "sweaty", "miserable", "worn", "wet", "hungry", "thirsty"))

BODY_COLD = (
    "Wrap up and get a hot drink in you - is the heating on where you are?",
    "Hot water bottle and something warm inside you. That beats waiting for the heating.",
    "Cold gets into everything. Is there a radiator you can sit next to?",
    "Another layer and something hot to drink. Is it the whole place, or just the room you "
    "are in?",
    "That is too cold to think straight in. Get the heating on and a jumper on top of that.",
)

BODY_HOT = (
    "Get a cold drink in you and some air moving - is there a window you can open?",
    "Cold water on your wrists and a bit of a draught is the quickest way down.",
    "That kind of heat is draining. Have you got somewhere cooler to be?",
    "Take it slowly in this, and get out of it for five minutes if you can.",
    "Too warm to think straight in. Open a window and put a cold drink in you.",
)

BODY_HUNGRY = (
    "Then go and eat something - what have you got in?",
    "That is your body asking. Something with protein in it holds you longer than a biscuit.",
    "Eat first and sort the rest out after. What is quickest to hand?",
    "You are running on empty there. Toast and an egg beats waiting for a proper meal.",
    "Go and get something now, even if it is small - a sandwich is enough to steady you.",
)

BODY_THIRSTY = (
    "Get a glass of water in you now - are you at home, or out?",
    "Thirsty means you are already behind. A full glass of water, not a sip.",
    "Water first, then whatever you were doing. Is there a tap handy?",
    "Have a proper drink of water and keep the glass next to you afterwards.",
)

# Light in the head is the one of these that has to be answered with sitting down first and the
# question asked second, because the person may be about to fall: the standing-up test is what a
# nurse asks, and "if it keeps happening, get it looked at" is the only advice that belongs on a
# bare faint.
BODY_LIGHT_HEAD = (
    "Sit down before anything else - did it come on when you stood up?",
    "Get sat down and have some water. Does it settle if you stay still for a minute?",
    "Take that slowly and hold on to something. Has it been creeping up on you, or was it "
    "sudden?",
    "Sit down and put your head down for a minute. If it keeps happening it is worth getting "
    "looked at.",
    "Have you eaten anything today? Low blood sugar does that - get something in you and "
    "sit down.",
)

BODY_QUEASY = (
    "Sit up rather than lie flat and sip water - is anything staying down?",
    "Plain and dry beats anything rich right now: toast, a bit of rice. When did it start?",
    "Go steady with small sips. Is it just queasy, or have you been sick?",
    "Fresh air and water, and nothing heavy for an hour or two. Does it come in waves?",
    "That is a rotten way to spend an evening. Is it something you ate, do you think?",
)

BODY_BUNGED = (
    "Something hot to drink and ten minutes of steam in the bathroom - is it a cold coming on?",
    "That is usually the cold starting in the nose and throat. Is it blocked, or running?",
    "Honey in hot water and rest your voice - how long has it been like that?",
    "Keep the fluids up and get an early night. Is it the nose, the throat, or both?",
    "A cold runs its week and there is no rushing it. Are you blocked up, or is it sore?",
)

# A cold sweat is not the warm end of the weather, which is what "im clammy" was answered as. It
# is the body working hard at something - a fever coming on, low blood sugar, a shock, or a room
# with no air - and what a friend does is get the person sat down and fed before asking anything.
# The one serious reading is a cold sweat with a faint or confusion in it, and that is the only
# thing here worth sending anyone to a phone about.
BODY_CLAMMY = (
    "Clammy is a cold sweat rather than being too warm. Have you eaten anything today?",
    "Get sat down and have something sweet if you have not eaten in a while. Does it come with "
    "feeling dizzy?",
    "That is usually your body working hard at something: a fever coming on, low blood sugar or "
    "a shock. Is it just your hands, or all over?",
    "Wash your hands and sit somewhere cool for a minute - has this come on today, or is it "
    "something you get? Cool water and a sit-down is the thing that helps most.",
    "Cold and clammy with the room at a normal temperature is worth taking slowly. Sit down, "
    "have a drink, and if you feel faint or muddled with it, ring 111.",
)

# Pale, grey and washed out. Nothing in the app can look at a person, so the pool asks whether it
# came on suddenly and puts the practical thing first: sit down, eat and drink. A colour that came
# on with a faint, a lot of blood or a confusion belongs to the safety cards, not here.
BODY_PALE = (
    "Pale usually means something is going round, or you have not eaten. Have you had anything "
    "today?",
    "Sit down and have a drink, then something to eat - did it come on suddenly, or have you been "
    "like this a while?",
    "Grey and washed out with it is worth getting looked at rather than waiting. Is there any "
    "dizziness with it?",
    "Has anyone said you look pale, or does it just feel like it? Pale with a bug is normal "
    "enough; pale and dizzy is the one to get seen.",
    "Put your feet up for ten minutes and have something with sugar in it. If you are clammy or "
    "muddled with it, get seen today.",
)

BODY_PUFFY = (
    "Bloated usually settles if you go easy on salt and fizzy drinks for a day. Is it worse after "
    "eating?",
    "Puffy ankles and hands are worth getting checked if it is new. Is it just your stomach, or "
    "your ankles too?",
    "That is your body holding water. Drink more rather than less and cut the salt for a few days "
    "- does it ease overnight?",
    "Which bit is puffy? After a big meal and a late night it is nothing, but swelling that stays "
    "is worth a look.",
    "Go steady with salt and fizz and see if it settles by tomorrow. Is it tender with it?",
)

BODY_SPOTTY = (
    "Spotty skin is usually hormones and nothing to worry about. Is it your face, or your back "
    "too?",
    "Wash with a plain cleanser twice a day and keep your hands off them. How long has it been "
    "like that?",
    "A GP can help if they are sore or leaving marks - are you picking at them, or leaving them "
    "alone?",
    "That is common enough and it does pass. Does it bother you, or is someone else commenting "
    "on it?",
    "Spotty and itchy after a new cream or washing powder could be a reaction. Has anything "
    "changed lately?",
)

BODY_POOLS = {"cold": BODY_COLD, "hot": BODY_HOT, "hungry": BODY_HUNGRY,
              "thirsty": BODY_THIRSTY, "light_head": BODY_LIGHT_HEAD,
              "queasy": BODY_QUEASY, "bunged": BODY_BUNGED,
              "clammy": BODY_CLAMMY, "pale": BODY_PALE, "puffy": BODY_PUFFY,
              "spotty": BODY_SPOTTY}

# What can carry the ask when "am" opens the line: "am i too late", "am we" never happens.
_SUBJECT_AFTER_AM = frozenset("i we you they he she it there this that anyone anybody".split())

# A bad stretch is not news and not a question: "bit of a rubbish week", "a rough few days",
# "long day", "hectic morning". Nothing in it names a thing to answer, and the neutral pool
# answers a feeling with "noted" - an intake form where a friend says "that sounds like a rough
# one, what's been the worst of it?". The reading is a bad word next to a stretch of time, which
# keeps a chore ("take the rubbish out") and a thing ("the rubbish bin is full") out of it.
BAD_STRETCH = frozenset(("rubbish", "crap", "crappy", "rough", "tough", "hard", "awful",
                         "terrible", "horrible", "grim", "stressful", "hectic", "rotten", "naff",
                         "wearing", "draining"))

STRETCH_OF_TIME = frozenset(("week", "weeks", "day", "days", "month", "months", "weekend",
                             "morning", "afternoon", "evening", "night", "shift", "term", "year",
                             "today", "lately"))

# The shapes a habit comes in: first person almost always, and about somebody they live with
# when it is not ("my son keeps biting", "my husband keeps forgetting our anniversary"). Only
# the repeated-tense words, not "i forget": one forgotten thing is a nuisance, and
# `remark.report_reply_for` already answers that.
# What follows the word has to be an act, because the words themselves are everywhere: "keep it
# all in" and "keep a diary" hold a thing rather than repeat one, "i always knew id end up here"
# and "i never know what to say" are states, and "i never hear from him" is what other people do
# not give. Each of those was asked what tends to come just before it, which blames the person for
# a mood or for somebody else's silence (fancy-penguin's read). So the marker takes either the
# -ing of a doing or a verb of doing in the plain form, and nothing else.
HABIT_ACT = (r"(?:\w+ing|say|says|do|does|did|end|leave|put|finish|start|ask|text|snap|"
             r"interrupt|overthink|forget|argue|second|manage|seem|apologi[sz]e|check|cancel|"
             r"procrastinate|agree|accept|take|give|spend|buy|work|plan|tidy|worry|complain|"
             r"volunteer|pick|choose|eat|drink|run|scroll|compare|share|tell|hide|swallow|"
             r"push|hold|bite|clench|stay|go|turn|shut|withdraw|avoid|help|save|spend|arrive|"
             r"stick|wander)")

# One question back, and the useful one: what happens around it, how long it has been going,
# what has been tried. Not "say more" - the person has just said the whole of it.
HABIT_REPLY = (
    "That sounds like a pattern rather than a one-off. What happens just before it?",
    "Habits like that are usually a trigger and a shortcut, not a lack of will. When does it "
    "bite most?",
    "How long has it been like that, and has anything ever made it better for a while?",
    "What have you tried so far? What did not work usually points at what would.",
    "Worth looking at what sets it off rather than trying harder at it. What tends to come "
    "just before?",
)

BAD_STRETCH_REPLIES = (
    "That sounds like a rough one. What's been the worst of it?",
    "Fair enough — that takes it out of you. What has been going on?",
    "Sorry. Do you want to tell me what has made it like that?",
    "That is a lot to hold at once. What has been the hardest part?",
)

# The lines here that comfort a mood, and only those: "that sounds rough", "what's been the worst
# of it", "what keeps coming back?". A bare "what should i do" after one of them is the person
# taking the offer up, so the step of a bad day is the reply. The neutral nod is not in it: "my
# sons 13 and hes started being really off with me" gets "Got it. Is there anything you'd like a
# hand with?" because nothing here knows about teenagers, and "something to eat, a shower" is not
# an answer about a son - a line like that is the answers lane's to answer, not this one's.
#
# The two pools about the speaker's own direction are comfort too: every line in them asks one
# question back and gives no instruction, so "i dont know what to do with myself" then "what do
# i do now" was answered with the question-back line meant for a bare ask that names nothing,
# "Nothing to do on my side, honestly - whatever comes to mind about it first is the useful
# bit", said to somebody who had just said they had no direction. The smallest step of a bad
# day is the follow-on there, the same as after a mood line.
#
# The leaving lines are comfort as much as the gentle pool is: "my wife left me" then "what do i
# do" was a step until the leaving got a pool of its own, so the step came off the gentle pool's
# wording rather than off the thread.
COMFORT_SAID = frozenset(NEGATIVE + BAD_STRETCH_REPLIES + RUMINATION_REPLIES
                         + NO_DIRECTION_REPLY + NOT_ENOUGH_REPLY + LEFT_POOL)

HOUSE_VERB = frozenset(("take", "put", "turn", "switch", "fill", "lock", "open", "close",
                        "wash", "hoover", "tidy", "clean", "set", "feed", "walk", "bring"))

# Cues that name a state a person is in, rather than something they did: a pregnancy, an
# engagement. Neither is news once it is in the past, and the pool congratulated "my wife was
# pregnant" because the bare cue was all it read.
PAST_STATE_CUES = frozenset(("pregnant", "engaged"))

# The words that put a state in the past: "was pregnant", "were engaged", "had been pregnant".
_WAS = frozenset(("was", "were", "been", "used"))

# Whose good news it is. A win said of a crowd the person is measured against is not their own,
# and a cheer is the worst reply there is to a line that sets them behind it: "everyone else
# seems to have it sorted" got "Brilliant. Thanks for telling me." and "everyone else has got
# it sorted and i havent" got "Good for you! That sounds like it was worth the wait" - the worse
# of the two on a line that is already sad. "all my mates are sorted" got "That's great news -
# nice one. What's next?" from somebody saying they feel behind. Only the cheer is withheld,
# never the cue's opposite: the line falls through to the readers below, which answer what it is
# really about (a doubt, a comparison), and it is never condoled instead.
CROWD = frozenset(("everyone", "everybody", "everyones", "peoples", "others", "nobody"))

# The person themselves as the subject of what happened: "i sorted out my cv" is their own win.
# Possessives are not in here - "my" in "my mates are sorted" owns the people, not the win.
YOU_SUBJECTS = frozenset("i im ive id ill me myself we us".split())

# "everyone is happy for us" is the person's own good news said from the outside, so a cue with
# one of these and a first person after it is not the crowd's.
ABOUT_WORDS = frozenset(("for", "of", "about"))

PERSON_WORDS = frozenset("me us we you my our myself ourselves".split())

# A birthday told with the number in it: "my mum is 72 and she is 73 next month", "shes 70 next
# month". The news-to-come pool welcomes the thing ahead and never says which birthday it is, so
# the one figure the person brought to the chat was the one thing the reply left out. These lines
# say it back, and ask the question a friend asks about a birthday rather than about plans in
# general. Only a birthday (`_a_birthday_still_to_come`) reaches them.
A_BIRTHDAY_STILL_TO_COME = (
    "{who} turns {age} {when} — that's one to look forward to. Are you doing anything for it?",
    "{age} {when} — a good one to have ahead. What are you thinking of doing?",
    "Lovely — {who} at {age} {when}. Will you mark it somehow?",
    "That's nice to have coming up. {age} {when} is worth making a fuss of — anything planned?",
)

# The first word of a line that asks the bot to make or find something.
# A person asking for help with the shape of their day or week ("help me get organised", "whats
# a good morning routine", "im always late") is asking for something the composer can actually
# give: a method in two sentences, and one question back. The honest shrug ("a search should
# sort you out") is the one reply that helps nobody here, and it was what these lines got.
ROUTINE = (
    "Pick the one thing that would make the day easier and give it a fixed slot; everything "
    "else can move around it. What is the thing you keep not getting to?",
    "Make it small enough that a bad day cannot beat it — two minutes, the same trigger each "
    "time — and add to it once it holds. What would it look like on your worst day?",
    "Work back from when you have to leave: what time to get up, what has to happen before "
    "that, and what can be dropped. Where does the morning usually go wrong?",
    "Write tomorrow down tonight — three things, one of them small — and do the smallest "
    "first, before the day fills up. Where does the time usually go?",
)

# The same complaint with the list already too long ("i have too much on", "im spread too
# thin"): advice about slots and triggers is the wrong answer when the problem is the size of
# the list, so this pool takes something off it instead of rearranging it.
TOO_MUCH = (
    "Then something has to come off the list. Which of it would actually go wrong if it waited "
    "a week?",
    "That is more than anyone can hold in their head — get it out of your head and onto paper, "
    "then mark the two things that are really due. What is on the list?",
    "When it is this much, the useful question is what to drop rather than how to fit it in. "
    "What is the one thing that cannot slip?",
)

# A routine, a habit, or being organised: the words a person uses for the shape of their day.
ROUTINE_WORDS = frozenset((
    "routine", "routines", "habit", "habits", "organised", "organized", "procrastinating",
    "discipline", "productive", "overwhelmed", "drowning", "swamped",
))

# The same ask said as a sentence. Every one of these came from a chat or the deck.
ROUTINE_PHRASES = (
    "get organised", "get organized", "get my act together", "stick to it", "stick at it",
    "stick with it", "always late", "never on time", "get up earlier", "sort out my mornings",
    "sort my mornings", "sort out my days", "to do list", "time management",
    "keep on top of", "keep putting things off", "put things off", "fall behind", "get behind",
    "no time in the morning", "no time in the day", "never enough time in the morning",
    "rubbish at mornings", "useless at mornings", "not a morning person", "bad at getting up",
    "cant get going in the morning", "mornings are a struggle", "dread mornings",
    # The late habit had only the adjective listed ("always late", "never on time"), so the same
    # habit said without that word - "late for everything", "how do i be on time" - was a punt
    # ("a search should sort you out") while "im always late for everything" was answered. The
    # ask to stop ("how do i stop being late") is the knowledge row's now and it answers with a
    # real card, so this is the shape of the day said the other ways round. "being late" on its
    # own is not here: "i hate being late" is a dislike, and the sympathy pool answers it better
    # than any method.
    "late for everything", "late to things", "be on time",
)

# The list is what is wrong, not the method: these take the size of it, and they come first.
# "i cant keep up with everything" and "im behind on everything" are deliberately not here: they
# are a judgement on the speaker, not a list, so they are left to whatever answers failing -
# a line about the size of the list gets the list, a line about not being enough gets the
# standard the person is holding themselves to.
TOO_MUCH_PHRASES = ("too much on", "spread too thin", "too many things", "so much to do",
                    "juggle", "juggling", "overloaded", "stretched thin",
                    "where to start", "where to begin")

# "i dont know where to start" is a list too long to begin, so it takes the size of the list -
# but only when the line has no method ask of its own: "help me get organised, i never know
# where to begin in the morning" wants the way in, not a shorter list.
_START_ASK = ("where to start", "where to begin")

# A routine that belongs to somebody else's world: a baby's, a dog's, a shift pattern at work.
# Those are a specialist's or a vet's to answer, not a method for the speaker.
ROUTINE_NOT = frozenset((
    "baby", "babies", "newborn", "toddler", "toddlers", "kid", "kids", "child", "children",
    "nursery", "teen", "teens", "teenager", "teenagers", "school run",
    "son", "daughter", "dog", "cat", "puppy", "kitten", "pup",
    "shifts", "shift", "hospital", "wing",
    # a subject that is not the shape of the day: money is somebody else's method
    "money", "bills", "bill", "tax", "taxes", "budget", "accounts", "invoice", "invoices",
    "payments", "debts", "debt", "rent", "mortgage", "loan", "loans", "insurance", "pension",
    "wages", "salary", "overdraft", "fines", "cook", "cooking", "dinner", "tea", "meals",
    "meal",
))

# "im always late paying my rent", "im behind on the mortgage": a money problem the day method
# cannot fix. Read with _money_decision, so "late for work" stays the day.
BEHIND_ON_MONEY = frozenset(("late", "behind", "overdue", "missed", "miss", "arrears", "skint",
                             "broke"))

# A death in the thread is not somebody else's routine: the day being planned is the speaker's.
_NO_DAY_OF_THEIR_OWN = ("died", "dead", "passed away", "passed on", "put down", "put to sleep",
                        "buried", "funeral", "cremation", "euthanised", "lost")

_DAY_WORDS = frozenset((
    "morning", "mornings", "day", "days", "evening", "evenings", "night", "nights", "week",
    "weeks", "weekend", "weekends", "time", "times", "work", "shift", "shifts", "today",
    "tomorrow", "life", "self", "routine", "routines", "everything", "anything", "nothing",
    "things", "thing", "moment", "minute", "minutes", "hour", "hours", "rest", "whole",
))

IMPERATIVE = frozenset("""give suggest recommend tell show make write find help list name pick
    choose plan""".split())

# A correction is the ask it points at. "no i meant should i see someone" after "my back hurts"
# was reaching the search shrug - "I don't know enough to answer that honestly" - while the same
# seven words on their own get the GP line, because everything below reads the whole line and the
# frame in front of it ("no i meant") matches nothing. The reading already splits the frame off
# (`intent == "correction"` carries the pointed-at words in `focus`), so answer those words
# against the same thread and keep the shrug only when they have nothing better in them. This is
# the commonest shape of a person steering, and the frame is not the subject: "sorry i meant how
# often do i water them" is a question about the tomatoes, not an apology.
PUNT = ("a search should sort you out", "quick search online", "i'd rather not guess",
        "that's beyond what i know well", "searching for it will turn up")

# The words of the frame itself, which the reading may leave inside `focus` when the frame is
# nearly the whole line ("i meant 8", "sorry, i meant porto not lisbon"): a second reading of
# those words is the same correction again, so they are never the ask it points at.
FRAME_WORDS = frozenset(("i", "meant", "mean", "said", "say", "sorry", "no", "not", "wait",
                         "oops", "scratch", "that", "actually", "rather", "than", "or"))

# Somebody the person loves has been hurt, and nothing else answered it: "my son was in an
# accident" and "my friend got attacked last night" were filed back to them ("Noted: your son was
# in an accident"), and "my brother got hit by a car" and "he got punched at the pub" got "Got it.
# Is there anything you'd like a hand with?" - a line that could have come before any message at
# all, which is the failure STYLE.md names. Nobody who says this is handing the bot a fact to
# keep; they are saying the worst thing in their week, so the reply asks about the person hurt.
# It asks and stops, because the bot has no card for this and an invented one is worse than the
# question: the safety cards and every answer about a death are ahead of this file and keep their
# turns.
SOMEBODY_HURT = (
    "God, that's awful. Is {who} alright?",
    "That's bad news. How is {who} now?",
    "I'm sorry. Is {who} alright?",
    "Christ. How is {who} doing?",
    "That's a horrible thing to hear. Is {who} okay?",
)

# No advice and no fix: they have told the bot how the day went, so the reply asks about the day.
# Five lines, because a pool of three repeats inside a single five-reply conversation.
# The second half of a day the turn before already reported. "i had a lovely day" then "we went
# to the beach" was answered "Sounds alright. Anything good in it?", and "i had a good day" then
# "we had a takeaway" the same: the flat pool reads the line on its own, so the rest of a good day
# arrived as a line with nothing good in it, asking for the good bit the person was already
# giving. A friend takes it as part of what was said and adds something warm, and does not ask
# how it went again - the question has just been asked and answered.
A_REST_OF_A_GOOD_DAY = (
    "That fits the day you have had. Good ones are worth saying out loud.",
    "The rest of a good day, then. Hold on to that one.",
    "Lovely. Those are the days that stick.",
    "That is a nice thing to have in a week. Enjoy the rest of it.",
)

# And the same shape the other way round: "work was mad today" then "i ended up staying till
# eight" was congratulated ("Good to hear. What was the best bit?"), because a flat line with a
# past tense in it is the same shape whether the day was good or bad. Where the turn before was a
# hard one, the rest of it is more of the same, and the reply carries the day rather than asking
# for the bright side of it.
A_REST_OF_A_HARD_DAY = (
    "That is the rest of a hard day, not the whole of it. Let the evening be small.",
    "Long one on top of a long one. Something warm to eat and an early night.",
    "Days like that pile up. You have done the day, so put your feet up now.",
    "That sounds like a full day on top of a hard one. Nothing else needs doing tonight.",
)

LOW_DAY_REPLIES = (
    "That sounds like a day to get through rather than enjoy. What made it that way?",
    "Sorry - that is a heavy one to carry. What has been the worst part of it?",
    "Long days like that take it out of you. Do you want to talk it through, or would you rather "
    "think about something else for a bit?",
    "That is a rough one. Is it the kind that lifts in a day or two, or one that has been "
    "building?",
    "Ugh. What happened?",
)

# A small account of the day, said flat. The four pools below answer a thing done where the
# composer could read the doing ("i painted the fence"), a thing arranged, a regret or a plan;
# what is left is everything else a person mentions about a day that has already happened - a
# takeaway, a haircut, work being alright, a trip to the shops - and it fell to the intake form,
# which offers help with a task the person never mentioned.
# A thing the person did and is judging themselves for. The cheer above is for a day that went
# fine and the shrug below is for a line with nothing in it; a confession is neither, and it is
# the one turn where a warm question is the whole reply. Nothing here tells them the thing was
# fine - the bot was not there, and a person who has just said they lied to a friend knows what
# they did.
A_THING_THEY_REGRET = (
    "You don't have to dress it up for me. What happened?",
    "That's the kind of thing that sits on you. Do you want to talk it through?",
    "Whatever it was, I'd rather hear it than not. What happened?",
    "That sounds like it's been weighing on you. What happened?",
)
# Somebody close has lied, cheated or hidden money, and the person is telling you what they found
# out. "i found out hes been lying" was answered "How was it, overall?" and "i found out shes been
# hiding money" "Sounds alright. Anything good in it?" - the congratulations nobody forgives. The
# news has only just landed, so nothing here works out what to do about it, and half of them do
# not ask anything, because a question at the end of every reply is a script.
A_BETRAYAL = (
    "That's a rotten thing to find out. What do you know so far, and what is still guesswork?",
    "Ugh. That's a lot to take in in one go. Say it as it came.",
    "That hurts, and it is not on you. What happened?",
    "Rotten news, and I'm sorry. Say it out loud if you want, or we can talk about something else "
    "for a bit.",
    "That changes how the whole thing looks, doesn't it. I'm here.",
    "Awful. You do not have to work out what to do about it today.",
    "That's the kind of thing that sits on your chest. Tell me what happened.",
)

# Somebody the person loves has moved into a care home, or is living in one, or the person is
# telling you about the visits and the guilt. Every one of those lines was answered as guests
# arriving at the speaker's flat ("Give them the best bed and plan one shared outing a day"), as
# a move into a new one ("On the first night you need the bed made, toilet roll, a kettle"), or
# said back ("Noted: your nan is in a home too shes 88"). The line names one person, so the reply
# is about that person, and none of these asks about the paperwork: the hard part is the change
# and the visiting, which is where a friend starts.
A_CARE_HOME = (
    "It takes a while to feel like home, for everyone. What is it like when you visit?",
    "How is {they} finding it there? The first weeks are the strangest for most people.",
    "That is a big change for {them}, and for you. How is {they} settling in?",
)
# The move itself: a person does not ask "how did you decide" about a home somebody has lived in
# for years, so that line is here rather than in the pool above.
A_CARE_HOME_MOVED = (
    "That is a big change for {them}, and for you. How is {they} settling in?",
    "That is a hard thing to have had to decide. How are you doing with it?",
    "It takes a while for everyone. How has {they} been since the move?",
)
A_CARE_HOME_VISITING = (
    "The visiting is the part that counts, and it is tiring too. What do you usually do together "
    "when you are there?",
    "A visit is a lot of work before and after it. How often do you get over there?",
)
A_CARE_HOME_GUILT = (
    "Guilt comes with this even when the decision was the right one, and it is not evidence of "
    "anything. What does a visit look like these days?",
    "That guilt is very common and it does not mean you did the wrong thing. Have you got anyone "
    "to say all this to?",
)
# What to take on a visit. The knowledge base has a what-to-bring card, but it is keyed on the
# words "care home" / "the home" / a visit, so a line that names only the person - "what should i
# bring her", three turns after the home was mentioned - matches nothing there and was answered
# with the customs allowance, then with a search hedge. The line's meaning is in the conversation,
# so the reply is here: the things that make a room theirs, and one thing a visit.
A_CARE_HOME_BRING = (
    "The things that make the room theirs: photos in a frame, a favourite blanket or cardigan, a "
    "radio or their own mug. Take one thing a visit rather than a car load, and check what the "
    "room has room for first.",
    "Ask what {they} misses from home - a particular biscuit, the paper, a cushion off the old "
    "sofa - and take one of those, plus something to do together. The visits matter more than "
    "the things.",
)

A_SMALL_DAY = (
    "Sounds alright. Anything good in it?",
    "Nice one. How did the rest of it go?",
    "Good to hear. What was the best bit?",
    "How was it, overall?",
)

# Something the person has only been told about, said as if it had happened to them: "i saw on
# the news theres a big storm coming", "i heard theres a storm on the way", "i read that the
# council is closing the library". The day pool above answered all three as an ordinary
# afternoon that went fine - "Good to hear. What was the best bit?", "How was it, overall?" - so
# a warning about a storm was congratulated. Nothing in these lines is a day of theirs: the thing
# is still to come, and they heard it from somebody else.
#
# What the bot can do is name the thing that actually knows and the half of it that can be acted
# on here. For weather that is the local forecast and the loose things a wind finds - which is
# the useful half of a storm warning, and it is true of a gale, a flood warning and a cold snap
# alike. For everything else it is the source, because what a closure covers and from when is one
# line further down from the headline. Neither pool claims to have seen the forecast or read the
# notice, and neither answers the wrong one; the storm words are what choose between them.
A_NEWS_OF_WEATHER = (
    "Then the local forecast is the thing that knows, not me: it gives the hour it lands and how "
    "hard, and anything loose outside is worth sorting before then - the bins in, the panel that "
    "already leans screwed back, the trampoline turned over.",
    "Worth an hour on the loose things before it gets here: the fence panel, the bin store, the "
    "pot that goes over anyway. The local forecast has the gusts, and that is the number that "
    "says whether the hour is worth spending.",
    "The local forecast will tell you the gusts and when; what it cannot tell you is what of yours "
    "is already loose. Walk the garden once and fix that, and the rest is out of your hands.",
)
A_NEWS_OF_SOMETHING_ELSE = (
    "Then whoever put it out has the detail, and the detail is the part that matters - what it "
    "covers, from when, and what you do about it. It is usually one line further down than the "
    "headline.",
    "Worth reading it at the source rather than the report of it: a closure or a change is "
    "usually a date, an area and a form, and the headline leaves all three out.",
    "The body that said it will have the version with the dates in it, and the question worth "
    "asking is whether it changes anything of yours - a journey, a bin day, a plan.",
)

# A thing of theirs taken by somebody else - a bike, a purse, tools out of a van. The small-day
# pool above answered it with "Nice one. How did the rest of it go?" and "Good to hear. What was
# the best bit?", because a theft typed as "someone nicked my bike" has a past-tense verb and no
# harm word in it, so the composer read it as an ordinary account of the day and congratulated
# them. The knowledge base has the card when the line names the thing it knows ("my phone got
# nicked", "my bag got nicked off the beach") and every card is ahead of this file, so what is
# left here is the loss with no card behind it. The line does what a friend does: says plainly
# that it is rotten, then asks the one thing that turns the rest into jobs the bot can help
# with - the report, the cards to stop, the claim - which is also what lets the next turn name
# the thing and reach the card that had nothing to go on.
# The line does what a friend does: says plainly that it is rotten, then asks the next thing.
# It does not ask what went - the line already said it ("someone nicked my bike" and the reply
# asked them to say what was taken), which is a machine talking to itself (free-cable on #8890).
A_THING_TAKEN = (
    "That's rotten. Is there anything that has to happen tonight - a lock, a card to stop?",
    "Sorry - that is a horrible thing to have happen. Was it insured, or is this coming out of "
    "your pocket?",
    "That's a blow. Did they get anything else, or just the one thing?",
    "That's low. Where was it when it went?",
    "That's rotten, and it is worth reporting today while it is fresh - the reference number is "
    "what the insurer and the bank both ask for. Say the word and I'll walk you through the "
    "claim step by step.",
)

# A day the person says went badly, in the shape the day pool answers: "we had a row last night",
# "we had a strange day at work", "ngl ive bin knackered all week". The cheer is the one reply that
# cannot be used, and with it gone these lines fell to the floor, so what is left is to ask about
# the day itself - never to explain it, and never to say how it must feel.
A_BAD_TIME_TOLD = (
    "Sounds like a rough one. What happened?",
    "Ugh, that is a shame. Do you want to get into it?",
    "That is a nuisance. Is there anything that would help?",
    "How are you doing with it?",
    "Sorry to hear it. What would make today easier?",
)

# A thing that was meant to happen and did not: "i was meant to be on holiday this week", "it was
# meant to be a loaf of bread". Nothing above answers it, so the day pool asked whether anything
# good had been in it. What a friend asks is whether it is off for good or moved, and what got in
# the way - never "how did it go", because it did not go.
# A line that is only a name: "my kids are called jack and emma", "my mother-in-law is called
# june". The name reader has a line for one relation ("my sister is called rose" -> "Rose - noted
# with care. What does she make of it?"), and this pool is for the shapes it does not read: kids
# and parents together, the in-laws, a person word with an adjective in front. {names} is the
# names as a person would say them and the pronouns come from the person word, so a sister is she
# and two names are they. Nothing here says what the people are like, what the name means or how
# old anybody is, because the name is all that has been said - so the question is always about
# the people.
# The names, where nothing is known about who carries them: a name on a thing ("my car is called
# betsy") and a name the whole household answers to ("we are called the smiths"). The question is
# about the name itself, which is the only thing that has been said, and it reads for one name and
# several, for a thing and for people.
A_NAME_STORY = (
    "{names}. What is the story behind that name?",
    "{names} - good to know. Where did that come from?",
    "{names}. Who picked it?",
)


# A name that came from somebody ("my son is called after me", "hes named after his grandad",
# "i was named after my nan"). These are not names at all - the line says where the name came
# from - so the name reader rightly stands down and the store said the line back ("Noted: your son
# is called after you."), which is the coldest reply in this file and adds nothing. What a friend
# asks is about the person the name came from, which is the only thing the line has given. {who}
# is that person as the speaker put it ("you", "your nan", "his grandad") and the pronouns are
# theirs, so a nan is she and two of them are they. Nothing here says what the name means or who
# chose it unless the line said so.
A_NAMED_AFTER = (
    "Named after {who}. What {are} {they} like?",
    "Named after {who}. Does the name fit, or is it a big one to carry?",
    "Named after {who} - I like that. Where did the idea come from?",
)
# The same news where the name came from the person themselves: "my son is called after me",
# "we named her after my mum" is the other pool, but "me" is the person being spoken to.
A_NAMED_AFTER_THEM = (
    "Named after you - that is a compliment. Whose idea was it?",
    "Named after you. Does the name fit, or is it a big one to carry?",
    "Named after you - I like that. What was the thinking there?",
)


A_NAME_TOLD = (
    "{names}. What {are} {they} like?",
    "{names} - good to know. What {are} {they} like?",
    "{names}. Tell me about {them}.",
    "{names}. What should I know about {them}?",
)


# A plan that did not happen, told without saying whose doing it was ("i was supposed to be on
# holiday this week", "we were supposed to go away", "i was supposed to call the bank"): every
# line has to work for a holiday and for a phone call, so none of them asks what became of a thing
# they made or whether a third party cancelled it.
A_PLAN_THAT_FELL_THROUGH = (
    "That's a shame. Is it off altogether, or moved?",
    "Gutted. What got in the way?",
    "Ah no. What stopped it?",
    "Sorry to hear it. Can it still happen?",
    "That is a shame. Do you get another go at it?",
)

# What is true of the person, said as a fact about them rather than as a day they had: "im self
# employed", "i was on a diet last year". Nothing above has a use for it, so it fell to the cheer
# ("Sounds alright. Anything good in it?"), which asks about a day nobody described, and then to
# the intake form, which offers help with a task nobody mentioned. A friend asks about the thing
# they have just said about themselves, and the tense is what says which way to ask: a diet last
# year is a thing to look back on, self-employment is a thing still going.
A_STATE_NOW = (
    "How is that going?",
    "How long has that been the case?",
    "Does that suit you, or would you change it?",
)
A_STATE_PAST = (
    "How did that go?",
    "How do you look back on it?",
    "What do you make of it now?",
)

# A thing that came out wrong, said without naming what it was: "it came out grey in the middle"
# was asked how it went overall, and in a chat of its own it was said back ("It came out grey in
# the middle - noted."). The cards answer the thing when the line names it ("my bread didnt rise",
# "the pastry came out soggy"), so what is left is a result with nothing to look up, and the one
# thing a friend asks about it is what happened. Five lines, because a pool of three repeats inside
# a single conversation.
# A day the pool would cheer where a loose word says something went wrong ("we had a strange day
# at work", "it was a grim afternoon"). The words that put a line here only ever took the cheer
# away before this, and the floor is a worse reply than the cheer, so the question is asked with
# no presumption in it: how it went, not what was the best bit of it.
A_DAY_ASKED_PLAIN = (
    "How did that go, overall?",
    "What was it like?",
    "How did you find it?",
)


A_THING_CAME_OUT_WRONG = (
    "That's a shame. What went wrong with it?",
    "Ah no. Can it be rescued, or is it a start again?",
    "Annoying when that happens. What was it you made?",
    "Gutted. Had you made it before?",
    "That is a nuisance. Do you know what did it?",
)

# Every line the five thing-done pools can say, so the hook below can ask whether the composer's
# answer to the line is one of them.
_THING_DONE_LINES = frozenset(A_THING_DONE + A_THING_GONE + A_THING_ON + A_THING_SEEN_TO
                              + A_THING_BOUGHT)

# A past participle in front of a food is the name of a dish, not an afternoon's work: "packed
# lunch for a vegan", "baked beans on toast" and "roasted vegetables for dinner" opened with a
# past tense and got the composer's pleasantry ("Nice one - are you pleased with it?"). The word
# after the participle is what tells the two apart: a report has an object it could point at
# ("packed my bag", "fried the onions", "baked a cake") and a dish has a bare noun ("packed
# lunch", "fried rice"), so the food lines that are dishes are the ones with no determiner there.
DISH_PARTICIPLE = frozenset(("packed", "baked", "fried", "roasted", "mashed", "toasted",
                             "scrambled", "boiled", "poached", "grilled", "stuffed", "pickled"))

DISH_DETERMINER = frozenset(("a", "an", "the", "my", "our", "your", "his", "her", "their", "its",
                             "this", "that", "these", "those", "some", "any", "all", "each", "one",
                             "two", "three", "every", "another", "it", "them", "everything"))


# --- a forecast nobody can settle -----------------------------------------------------------
# "is he going to be alright" after "my dad had a car accident", "will my knee get better on its
# own", "is he going to be ok" about a dog that drank sea water. Nothing in the store answers
# these and no search does either: whether a body mends is the thing nobody can call from here.
# Main gave every one of them the line about searching online - or, where the line was short,
# "say what you are asking about" - so a person whose father had just had an accident was told
# to look it up. The reply says plainly that nobody can call it, names the one who can (the
# ward, the GP or a physio, the vet) and gives one thing worth asking, which is what helps on
# the day. It only ever replaces a hedge, and only where the thread says whose body it is.
FORECAST = re.compile(
    r"\bwill\s+(?:it|that|this|they|he|she|i|we|my\s+\w+|the\s+\w+)\b"
    r"[^?.!]{0,40}?\b(?:get\s+better|get\s+worse|be\s+(?:ok|okay|all\s+right|alright|fine)|\s*"
    r"come\s+back|come\s+right|come\s+down|go\s+(?:away|down)|recover|heal|clear\s+up|ease|\s*"
    r"settle|pass|stop|wear\s+off|sort\s+(?:itself|themselves)\s+out|\s*"
    r"pull\s+through|make\s+it)\b"
    r"|\b(?:is|are|will)\s+(?:he|she|it|that|this|they|my\s+\w+)\b[^?.!]{0,30}?"
    r"\b(?:going\s+to|gonna)\s+(?:be\b|get\s+(?:better|worse)|heal|recover|\s*"
    r"clear\s+up|come\s+(?:back|right)|settle|ease|\s*"
    r"make\s+it|pull\s+through)\b"
    # A day on the end of it: "will he be out by friday", "will she be home for christmas", "will
    # he be back on his feet before the wedding". The date changes nothing about who can answer it
    # - no calendar knows whether a man leaves the ward on Friday - and without this shape the
    # line fell through to the search hedge a turn after the person said he was in hospital.
    r"|\bwill\s+(?:he|she|they|my\s+\w+|the\s+\w+)\b[^?.!]{0,20}?\bbe\s+"
    r"(?:out|home|back|walking|mobile|up\s+and\s+about|better|on\s+the\s+mend)\b\s*"
    r"(?:by|before|for|on|in\s+time\s+for|this|next)\b")
# "will it be ok to leave the paint overnight" asks permission to do something, and the thing
# named is not a body: that stays a knowledge question, hedge and all.
FORECAST_PERMISSION = re.compile(
    r"\bwill\s+(?:it|that|this)\s+be\s+(?:ok|okay|fine|alright|all\s+right)\s+"
    r"(?:if|to|with|until|till|overnight)\b")
# "how long will it take to settle" asks for a duration, not for a forecast of how it ends, and
# the composer already answers it with the card that names the same-day route and what it costs
# ("Ring 111 or your surgery - they will say whether it needs looking at today"). Swapping that
# for a line about the GP is a step backwards, so the duration ask keeps the answer it has.
FORECAST_DURATION = re.compile(r"\bhow\s+long\b")
# "will i be ok", "am i going to be ok": the forecast is about the speaker, which decides the
# answer even when the thread is about somebody else - "my dad had an accident" then "will i be
# ok" is about how the asker is coping, not about their father.
FORECAST_I_ASK = re.compile(r"\b(?:will|am)\s+i\b")
# The word that names who the forecast is about: "my mum", "his knee", "our dog". A relation
# is the one thing a short follow-up can bring with it, and it decides which building the answer
# sends them to.
FORECAST_RELATION = re.compile(
    r"\b(?:my|our)\s+(dad|father|mum|mom|mother|nan|nana|gran|granny|grandma|grandad|grandpa|\s*"
    r"husband|"
    r"wife|partner|boyfriend|girlfriend|son|daughter|brother|sister|baby|boy|girl|friend|mate|"
    r"dog|cat|pup|puppy|kitten|rabbit|hamster|horse|pony|bird|parrot|guinea|gerbil|ferret|fish)"
    r"\b")
FORECAST_HE_SHE = re.compile(r"\b(?:he|she|him|her|his)\b")
# A hard patch is not a body that mends, but it is still a forecast, and the honest answer is
# about the person asking: what they can do this week, and who steps in if it gets darker.
FORECAST_STRUGGLE = re.compile(
    r"\b(?:struggl\w*|cop(?:e|ing)|depress\w*|anxi\w*|upset|cry(?:ing)?|tears|unhapp\w*|"
    r"miserable|lonely|isolated|withdrawn|overwhelm\w*|burn(?:t|ed)?\s+out|breaking\s+down|"
    r"hard\s+time|going\s+through\s+(?:it|a\s+lot)|feel(?:ing)?\s+(?:low|flat|down)|"
    r"lost\s+my\s+job|redundant|sacked|"
    r"not\s+(?:her|him)self|self\s*harm|suicidal|dark\s+place)\b")
# What a body thread says besides a symptom: a fall, an operation, a ward. None of these is a
# body part, and a question about somebody who has just had one is not about their feelings.
FORECAST_ILL = frozenset("""
fall falls fell hospital ward operation op surgery treatment diagnosed diagnosis pneumonia
infection sepsis chemo chemotherapy stroke fracture broken stitches plaster cast scan consultant
physio physiotherapy terminal prognosis recovering recovery intensive icu a&e casualty accident
accidents crash crashed collision injured injury hurt ambulance paramedic paramedics
""".split())
FORECAST_PERSON = (
    "Nobody can promise that, and I won't guess about another person's health. What it comes "
    "down to is the direction - better than yesterday, or not - and the ones looking after {who} "
    "can see that. Ask them what they are watching for, and what the next few days should look "
    "like.",
    "That is the doctors' call, not mine - I can't see {who}. What is in your hands is asking "
    "them straight how it compares with yesterday and what would count as a setback; tell me "
    "what they say and I'll help you think it through.",
    "I can't promise that, and it would not be fair to. What the people treating {who} can tell "
    "you is the useful part: what is going well, what would worry them, and what the next few "
    "days should hold.",
)
FORECAST_SELF = (
    "No one can promise that from here - mine would be a guess about your body, and that is "
    "not a guess worth having. What decides it is the direction: if it is easier this week than "
    "last, keep going as you are; if it is no better in a couple of weeks, or it gets worse, "
    "111 will say whether it needs looking at today.",
    "Probably, given time - and nobody can say for certain from here. The thing to watch is "
    "whether it keeps improving; if it stalls, or it starts to get worse, that is one for your "
    "GP rather than wait-and-see.",
    "I can't call that from here, and a guess about a body is the last thing you need. Bodies "
    "mend at their own speed, so the question worth asking is whether it is improving week by "
    "week; your GP can say what to expect and when to come back - take the same description you "
    "gave me.",
)
FORECAST_SOMEONE_STRUGGLING = (
    "I can't promise that, and I won't pretend to - nobody can say how another person's hard "
    "patch ends. Staying in touch this week is the part you can do, and if it gets darker than "
    "that, their GP is the one who can step in.",
    "Nobody can call that from here, and a forecast would be a guess. Keep asking how they "
    "really are - and if there's any talk of not wanting to be here, that is a doctor's call "
    "the same day, not something to wait out.",
)
FORECAST_SELF_STRUGGLING = (
    "I can't promise that, and a forecast would be a guess. What does move it is this week: "
    "keep the ordinary things going - sleep, food, daylight, one person who knows how it really "
    "is - and if it is no better in a fortnight, take it to your GP.",
    "Nobody can call that from here, and I won't pretend to. Tell one person the true version "
    "rather than the short one, keep the week as ordinary as you can, and if it gets darker than "
    "that, your GP is the one who can step in.",
)
FORECAST_PET = (
    "Only the vet can say that - I can't examine {who} from here. What the desk will ask is the "
    "useful part: is {who} eating and drinking, as lively as usual, and has anything been kept "
    "down? Ring with that and ask whether to bring {who} in tonight.",
    "I can't call that from here, and the vet has to see {who}. What decides it is usually how "
    "{who} is in themselves - eating, drinking, energy - so note that down and ring the desk; "
    "they will say whether it can wait until the morning.",
    "Nobody can say that without seeing {who}, and the vet can. Take what you've just told me, "
    "add whether {who} is eating and drinking, ask what would mean bringing {who} in, and go "
    "with what they say.",
)
# A forecast asked in a thread the bot has just answered with first aid: the honest line is not
# "search it" and not a calm "ask at your next appointment" either. The people who are treating
# the person can see what the bot cannot, so the question goes to them, and what they have said
# still beats anything the bot could offer.
FORECAST_AFTER_SAFETY = (
    "I can't say how it will go, and nobody can from here. What you can go on is the direction - "
    "steadier hour by hour, or not - and the ones treating {who} can see it: keep doing what "
    "they told you, and ask them what to expect and what would worry them.",
    "That is for the people looking after {who} to answer, not me - they can see what I can't. "
    "Keep doing exactly what they told you, and ask them straight what the next few days should "
    "look like; I'm here for the rest of it.",
)


FORECAST_POOLS = (FORECAST_SELF, FORECAST_PERSON, FORECAST_SOMEONE_STRUGGLING, FORECAST_PET,
                  FORECAST_AFTER_SAFETY)


# Every word in the store that makes a body a body. "fall" and "operation" are not parts of one,
# but a line about somebody who has just had either is not a line about their feelings.
FORECAST_BODY_WORDS = BODY_PARTS | SYMPTOM_WORDS | HEALTH_WORDS | FORECAST_ILL

# A body word in front of a thing's name is not a body. "its right by the back door" / "will they
# come back next year" is a garden, and reading "back" as a spine sent a gardener to a GP; "foot of
# the stairs", "head of the bed", "arm of the sofa" and "chest of drawers" read the same way. The
# pairs are the ones everyday talk uses, taken out wherever a body is being read.
BODY_WORD_FOR_A_THING = re.compile(
    r"\b(?:back|shoulders?|arms?|foot|feet|head|chest|hips?|ribs?|spine|belly|knees?|neck|"
    r"hands?|legs?|elbows?|waist)\s+(?:doors?|gardens?|yards?|walls?|rooms?|gates?|fences?|"
    r"windows?|lawn|beds?|paths?|steps?|porch|seats?|lights?|lanes?|roads?|alleys?|shed|deck|"
    r"patio|fields?|cars?|wheels?|sides?|covers?|pages?|pockets?|boards?|racks?|rest|cushions?|"
    r"chairs?|tables?|freezer|drawers?|cupboards?|wardrobes?|stairs?|staircase|lines?|notes?|"
    r"rows?|bands?|straps?|ties?|muffs?|warmers?|of\s+the\s+(?:stairs|bed|sofa|room|house|"
    r"boat|car|garden))\b")

# An older person who has stopped eating is a body to worry about, and no word for it is a body
# part or a symptom: "my gran is in a care home and has stopped eating" / "will she be alright"
# got the search hedge, when the people looking after her are exactly who can answer it.
FORECAST_OFF_THEIR_FOOD = re.compile(
    r"\b(?:stopped|stopping|not|no\s+longer|wont|won'?t|isnt|isn'?t|keeps?)\s+eating\b"
    r"|\boff\s+(?:her|his|their)\s+food\b|\b(?:lost|loosing|losing)\s+(?:her|his|their)\s+"
    r"appetite\b")

# What a pet does to itself rather than a habit it has: eaten something it should not, been hit,
# gone lame. A forecast about one of these is the vet's to answer.
FORECAST_PET_HARM = re.compile(
    r"\b(?:drank|drink|swallow(?:ed|s|ing)?|ate|eaten|eats?|poison\w*|toxic|lil(?:y|ies)|"
    r"chocolate|grapes?|raisins?|onions?|xylitol|antifreeze|bleach|hit\s+by|ran\s+over|"
    r"run\s+over|fell|fallen|limp(?:ing)?|lame|collapsed|fitting|seizures?|wheez\w*|"
    r"vomit\w*|vomited|bleeding|blood|in\s+pain|shaking|not\s+eating|stopped\s+eating|"
    r"off\s+(?:her|his|their)\s+food|hurt)\b")

# Coming off a bike, a ladder or a horse is a body somewhere being hurt, and none of those words
# is a body part or a symptom: "my brother came off his bike yesterday" / "will he be ok" kept the
# search hedge.
FORECAST_A_FALL = re.compile(
    r"\b(?:came|come|cames|fell|fallen|falling|was|were|got|been)\s+off\s+(?:his|her|their|the|"
    r"a|my)\s+(?:bike|motorbike|horse|ladder|roof|scooter|skateboard|bicycle|moped|quad)\b")


# --- moved out of `fallback.py` whole, so that file stays under the world's upload cap ---
# Nothing here was rewritten: the tables are the ones that file had, and `fallback` imports
# them back under the same names, so `fallback.POOL` is the same object it always was.


# A doubt needs something it is about, and the something has to be an act the speaker could take.
# A bare "if" or "whether" is a doubt about a fact ("i dont know if hes coming", "i dont know if
# the shop is open") and a bare "what to say" is about someone grieving, whose answer is not a
# question about which way to lean (rugged-hippo's read, and they are right).
DITHER_SUBJECT = re.compile(
    r"\b(?:"
    # "whether to laugh or cry" is a figure of speech, not two acts to weigh, so the reaction
    # verbs are out; every other "whether to <verb>" is a choice the person could make.
    r"whether to (?!laugh|cry|scream|shout|smile)\w+"
    r"|if i (?:should|shall) \w+"
    # "if i can come on friday" is a diary clash; "if i can afford it" is the decision.
    r"|if i can (?:afford|manage|keep|take|handle|fit|cope|swing)\b"
    r"|between \w+"
    r"|which \w+ to (?:pick|choose|take|try|go)"
    r"|what to do (?:about|with|next|now)\b"
    # "where to start" and "how to start" are direction, not a choice, and `to start` alone was
    # reading "the thing is i dont know where to start" as a decision (apt-lime's read).
    # The same trap sits in front of every ordinary verb, so a bare "to <act>" is not enough and
    # a decision word has to introduce it: "i dont know where to go", "i dont know when to
    # leave" and "i dont know where to buy it" are direction, timing and shopping, and "i dont
    # know what to take for it" is a medicine, not a choice between two sides. "whether to" and
    # "if i should" above carry the cases people actually type (warm-feather's read on #1467).
    r"|(?:decid(?:e|ed|ing)|think(?:ing)?|thought|wonder(?:ing)?|consider(?:ing)?|want)"
    r"s?\s+(?:about\s+|of\s+)?(?:whether\s+)?to "
    r"(?:go|take|move|stay|leave|quit|apply|accept|buy|sell)\b"
    # "i want to go" after a doubt is the choice itself ("im not sure i want to go"), and so is
    # someone else's want the speaker is weighing ("my girlfriend wants to move in and im not
    # sure"). "need to" is left out on purpose: "i dont know if i need to take the tablets" is a
    # medicine question, not two sides.
    r"|i (?:want|wanted|dont want) to (?:go|take|move|stay|leave|quit|apply|accept|buy|sell)\b"
    r")")


PASSED_OUT = re.compile(
    r"\b(i|im|he|hes|she|shes|we|were|they|theyre|"
    # "my child", "my kids", "my little boy", "my eldest daughter", "the boy in my class"
    r"(?:my|our|the)\s+(?:(?:little|young|eldest|oldest|older|grown\s?up|poor|baby|new)\s+)?"
    + PASSED_OUT_PERSON + r")\b(?:\s+\w+){0,4}\s+"
    r"(?:passed out|collapsed|fainted|blacked out|keeled over|had a seizure"
    # The same event said in the tense it is happening in, or in the words for how often: "my mum
    # is collapsing", "my mum keeps passing out", "shes fainting", "he collapses sometimes". Only
    # the past tense was matched, so every one of these was answered "Noted: your mum is fainting"
    # - the person was telling us about a faint and got a receipt for the sentence.
    r"|passing out|collapsing|fainting|blacking out|keeling over|having a seizure"
    r"|collapses|faints|passes out|blacks out"
    # "i keep passing out" is the same event as "my mum keeps passing out", and it was reaching
    # the habit row, which asked whether it was the same every time.
    r"|keeps? (?:passing out|collapsing|fainting|blacking out|going down)"
    r"|pass(?:ing|ed)? out (?:sometimes|a lot|often|now and then|every so often|a few times)"
    r"|goes down\b(?=\s*(?:all|suddenly|on|in (?:the|a)\s|while|when|at\b))"
    # "my mum went down" is the same thing said plainly. Not "went down to the shops", "went down
    # the stairs" or "went down with a bug": a place, a flight of steps or an illness after it
    # takes the faint away.
    # A faint that has not happened yet is the same event a minute early: "my child is about to
    # pass out" and "my grandson is going to faint" were comfort lines and the memory echoing the
    # sentence back. It is still a person who needs sitting down and looking at today.
    r"|went down(?!\s*(?:to|the|stairs|steps|hill|road|lane|street|with|in|by|for))"
    r"|(?:(?:about|going|gonna)\s+to|might|may)\s+(?:pass\s+out|faint|black\s+out|collapse|"
    r"go\s+down))\b")


# The other "passing out": handing them to people. "we were passing out flyers at the station" is
# a Saturday, not a faint, and the present tense now reaches the faint arm.
PASSING_OUT_A_THING = re.compile(
    # "we were passing out flyers at the station" is a Saturday, not a faint. The thing being
    # handed out is a noun - after a determiner, "passed out the party bags", "passed out a
    # leaflet", or as a bare plural, "passes out leaflets for the church" - and a faint has a
    # place, a time or a sign there instead: "passed out at school", "passed out for a minute",
    # "passed out cold", "passed out on the floor", "passed out twice". So the object is the
    # shape that tells the two apart, and it is the shape rather than a list of nouns that does
    # the work: the list kept losing, first on "flyers" and then on every party bag, sticker and
    # cupcake anyone thought of. A quantity or a time after the determiner is the faint still
    # ("passed out a bit", "passed out a few seconds"), and so is an adverb after the verb
    # ("passed out afterwards", "passed out sometimes"), so those words are the exceptions.
    r"\bpass(?:ing|ed|es)?\s+out\s+(?:(?:the|a|an|some|those|these|our|their|his|her|my|its)\s+"
    r"(?!(?:bit|little|lot|few|couple|while|moment|second|seconds|minute|minutes|mins|hour|hours|"
    r"day|days|night|nights|time|times|again|now|too|other|next|thing|door|window|gate|back|"
    r"way|rest|floor|sofa|chair|bed|bus|train)\b)\w+"
    r"|(?!(?:afterwards?|after|before|later|once|twice|thrice|again|sometimes|always|often|"
    r"repeatedly|nowadays|every|most|these|days|nights|weeks|months|years)\b)[a-z]{2,}s\b)")


# The same ask said from the other end. "i dont know what to do" names nothing and asks for the
# same hand "what should i do" asks for, but it is not written as a question, so it never reached
# the offer above: on main the one shape had four different replies depending on the words after
# "do". "i dont know what to do" got "Thanks for telling me - I'm here if you want to dig into any
# of that", "i dont know what to do anymore" got "Got it. Is there anything you'd like a hand
# with?", "i dont know what to do about it" got "I'm listening - say more if it helps", and "i
# have no idea what to do" - the same line with the other verb - reached the search hedge. Every
# one of those is the placeholder this lane exists for: they fit any message, and the person has
# just said the one thing that makes an offer the right reply. The direction readings keep their
# lines ("with my life", "with myself") because they are a different thing: this is somebody
# beaten by a thing, not somebody without a plan.
BARE_PICK_LOST = re.compile(
    r"^\s*(?:(?:so|and|but|ok|okay|well|then|just|hey|hi|right|anyway|anyways|oh|hmm|yeah|"
    r"yes|alright|honestly|god|christ|ugh|tbh|seriously|you\s+know)[\s,]+)*"
    r"(?:i\s+)?(?:really\s+|honestly\s+|genuinely\s+|actually\s+|still\s+|simply\s+|"
    r"just\s+)*"
    r"(?:"
    # the three ways English says "the not knowing": the verb with its "know", the contraction
    # that already carries it ("dunno"), and the idea or clue that stands in for it. The "i" is
    # optional on every one, because people drop it ("dont know what to do", "no idea what to
    # do" - the deck's dropped-subject rows are written that way).
    r"(?:do\s+not|don'?t|dont)\s+(?:even\s+)?know"
    r"|dunno"
    r"|(?:have|ve|got|i'?ve)\s+(?:absolutely\s+)?no\s+(?:idea|clue)"
    r"|(?:have\s+)?no\s+(?:idea|clue)"
    # "not sure what to do" is the same ask with the doubt in place of the not knowing.
    r"|(?:i\s+am\s+|i'?m\s+)?not\s+(?:really\s+|too\s+)?sure"
    r")"
    r"\s+what\s+(?:to\s+do|i\s+(?:should|can|could|might)\s+do)\b"
    # the words people put after it that do not add anything the pool has to read.
    r"(?:\s+(?:now|next|first|today|tonight|tomorrow|instead|else|at\s+all|anymore|"
    r"any\s+more|about\s+(?:it|this|that)|with\s+(?:it|this|that|them)))?\s*\.?\s*$", re.I)


# Who a bot answer can have pointed at, in the words those answers use. A name the answer did not
# say is never in here, so this reads the thread and invents nothing.
NAMED_BODIES = (
    # The longer names come first, so "citizens advice" is not read as two other actors and a
    # head of year is not read as the whole school.
    ("citizens advice", "Citizens Advice"), ("national debtline", "National Debtline"),
    ("health visitor", "Your health visitor"), ("school office", "The school office"),
    ("head of year", "The head of year"), ("gas safe", "A Gas Safe engineer"),
    ("letting agent", "The letting agent"), ("trading standards", "Trading standards"),
    ("environmental health", "The council's environmental health team"),
    ("the council", "The council"), ("your council", "The council"),
    ("the vet", "Your vet"), ("a vet", "Your vet"), ("pharmacist", "A pharmacist"),
    ("111", "111"), ("a&e", "A&E"), ("your gp", "Your GP"), ("the gp", "Your GP"),
    ("dentist", "A dentist"), ("landlord", "Your landlord"), ("the school", "The school"),
    ("solicitor", "A solicitor"), ("the bank", "Your bank"), ("your bank", "Your bank"),
    ("ombudsman", "The ombudsman"), ("plumber", "A plumber"), ("electrician", "An electrician"),
    ("roofer", "A roofer"), ("the police", "The police"), ("registrar", "The register office"),
    ("dwp", "The DWP"), ("hmrc", "HMRC"), ("stepchange", "StepChange"),
    ("samaritans", "Samaritans"), ("your insurer", "Your insurer"), ("acas", "ACAS"),
    ("your union", "Your union"), ("hr", "HR"), ("the midwife", "Your midwife"),
)


# "do you keep what i tell you", "who can see this chat", "is this private". Nothing about the
# bot's own handling of what it is told had a reading, so five ordinary questions about it were
# answered by a television-listings card (a card matching "keep") or by the search hedge, which
# offers to look up a fact about the world that nobody asked about. The honest answer is short and
# is the shape of the program: what you type is used here, in this conversation, and nothing is
# written down or sent anywhere.
#
# The fence is the possessive: "how do i keep my plants alive" and "should i keep my receipts" carry
# the same verbs about the person's own things, so a keep/share verb only counts when what it holds
# is what was *said* ("what i tell you", "my messages", "this chat", "the conversation"). "who can
# see" is the other half and its own shape, because the person is asking about other people rather
# than about the bot: "can anyone see this chat", "does anyone read this", "who can see what i say".
PRIVACY_ASK = re.compile(
    # What the bot holds, keeps or passes on, with the thing held being what was said. The noun
    # after the verb is what makes this the bot's own handling: "keep my receipts" and "keep the
    # kitchen clean" name a thing of the world and are left to their own entries.
    r"\b(?:keep|keeps|keeping|store|stores|storing|save|saves|saving|record|records|recording|"
    r"log|logs|logging|share|shares|sharing|sell|sells|selling)\s+"
    r"(?:on\s+|out\s+|around\s+|off\s+|away\s+)?"
    r"(?:what\s+i\s+(?:said|say|tell|type|typed|write|wrote)|what\s+we\s+(?:said|talk|"
    r"discussed)|my\s+(?:messages?|data|details|information|info|chats?|records?|"
    r"conversations?)|our\s+(?:chats?|conversations?)|this\s+(?:chats?|conversations?)|"
    r"the\s+(?:chats?|conversations?))\b"
    # Somebody else reading it. The subject is other people, never "you": "did you see the match"
    # and "did you see my keys" are conversations about the world and nobody's privacy.
    r"|\b(?:can|could|will|would|do|does|did)\s+(?:anyone|anybody|someone|somebody|people|"
    r"other\s+people|people\s+else|anyone\s+else|everyone|staff)\s+(?:else\s+)?"
    r"(?:see|read|hear|get|access|look\s+at)\s+(?:this|what|my|our|the)\b"
    # The same ask with the bot as the one who might tell them.
    r"|\b(?:do|does|did|would|will|can|could)\s+(?:you|u)\s+(?:ever\s+)?"
    r"(?:tell|show|share|give|send|hand|pass|forward)\s+"
    r"(?:anyone|anybody|someone|somebody|people|others|a\s+third\s+party)\b"
    # "who can see this" is the chat, and "who can see this letter" is a letter: a bare "this"
    # only counts when it ends the line (or names the chat after it). "who sees what i type" is
    # the same ask with the verb inflected, and it hedged.
    r"|\bwho\s+(?:(?:can|could|else\s+can|else\s+could)\s+(?:see|read|access)|sees|reads|"
    r"accesses)\s+"
    r"(?:this(?:\s+(?:chat|conversation|thread))?(?=\s*[?.!]*\s*$)|"
    r"my\s+(?:messages?|data|chats?)\b|what\s+i\s+(?:say|type|write)\b)"
    # Named outright. The thing named can be the chat itself: "is this chat secure" and "is this
    # conversation recorded" were a search hedge while "is this private" was answered.
    r"|\bis\s+(?:this|it|what\s+i\s+say|what\s+i\s+tell\s+you)(?:\s+(?:chat|conversation|"
    r"page|app|thing|site))?\s+(?:private|confidential|"
    r"secure|saved|recorded|stored)\b"
    r"|\bare\s+(?:my|our|these)\s+(?:messages?|data|details|chats?|records?|words)\s+"
    r"(?:private|safe|secure|confidential|shared|stored|saved|recorded|logged)\b"
    r"|\b(?:does|do|did|is|was)\s+(?:this|it|that|everything\s+i\s+say|what\s+i\s+say)\s+"
    r"(?:get\s+|being\s+|ever\s+get\s+)?(?:shared|stored|saved|recorded|logged|kept|seen|"
    r"read|passed)\b"
    r"|\bare\s+(?:you|u)\s+(?:keeping|recording|saving|storing|logging)\s+"
    r"(?:this|what\s+i|my|our|the\s+(?:chat|conversation))\b"
    # A record kept of it, and the same thing passed on: "do you keep a record of this", "do you
    # pass this on to anyone". Read with "do you" in front, so "how do i keep a record of it" (a
    # tax question) and "how do i pass this on" are somebody asking about their own paperwork.
    r"|\b(?:do|does|did|will|would|can|could)\s+(?:you|u)\s+(?:ever\s+)?"
    r"(?:keep|save|log|record|store)\s+(?:a\s+|any\s+)?"
    r"(?:record|log|copy|note|transcript|file|history)\s+of\b"
    r"|\b(?:do|does|did|would|will|can|could)\s+(?:you|u)\s+(?:ever\s+)?"
    r"(?:pass|send|hand|give|forward|share)\s+(?:this|that|it|what\s+i\s+say)\s+"
    r"(?:on|along|around|off|over)?\s*(?:to|for)\s+"
    r"(?:anyone|anybody|someone|somebody|people|others|a\s+third\s+party)\b"
    # Said as a noun: "do i have any privacy here", "no privacy on this".
    r"|\bprivacy\s+(?:here|on\s+this|in\s+this|with\s+you|at\s+all)\b"
    # "what are you using my data for", "what do you do with what i tell you". Read as the identity
    # question ("I'm a chatbot, not a person") because "what are you" opens the line.
    r"|\bwhat\s+(?:are|do)\s+(?:you|u)\s+(?:(?:do|doing)\s+)?(?:with|using)\s+"
    r"(?:(?:my|our)\s+(?:data|details|information|info|messages|words)|"
    r"what\s+i\s+(?:tell|say|type|write))\b", re.I)


NOT_WHAT_I_SAID = re.compile(
    r"\b(?:keep|store|save|record|log|share|sell|pass)\w*\s+(?:me\s+|us\s+)?(?:the\s+|a\s+|an\s+|"
    r"my\s+|our\s+)?(?:kitchen|cat|dog|plants?|receipts?|leftovers?|food|milk|bread|eggs?|"
    r"cheese|wine|beer|keys?|car|bike|house|flat|money|savings|cash|password|photos?|pictures?|"
    r"files?|documents?|sheet|table|bill|bills|tickets?|seats?|room|garage|garden|washing|"
    r"clothes|coat|bag|phone|number|address|email|weight|diary|journal|notes)\b"
    # "private" with a thing after it is a kind of thing, not a question about the chat: "is this
    # private rented or council", "private treatment", "a private landlord" are their own entries.
    r"|\bprivate\s+(?:rented|rent|rental|landlord|landlords|sale|sector|school|schools|hospital|"
    r"hospitals|treatment|health|healthcare|health\s?care|medical|insurance|pension|parking|road|"
    r"land|garden|tuition|tutor|"
    r"lessons?|detective|investigator|eye|clinic|care|nursery|swimming|coach|hire|contract|"
    r"members?|club|firm|company|jet|plane|island|beach)\b"
    # "is this shared ownership", "a shared driveway": the share is a thing of the world, and the
    # reading of "is this shared" is about what happens to the person's words.
    r"|\bshared\s+(?:ownership|owner|equity|driveway|garden|house|home|flat|room|kitchen|"
    r"bathroom|car|bike|account|login|costs?|bills?|custody|care|space|office)\b", re.I)


# The same ask in the shapes the reading above misses: the chat itself named with the word beside
# it ("is this a private chat", "is this conversation private", "is this call recorded"), a bare 3
# "will this be private", the bot's own keeping verb with nothing but "this" for an object ("will
# you keep this", "do you save this"), a bare "who sees this", and the person's own data asked
# about ("is my data private", "is my data safe with you"). Each is narrow on purpose: a noun of
# the world after "this" keeps the line where it was, so "who can see this letter" and "is my data
# safe to delete" are not read here.
PRIVACY_SHAPES = re.compile(
    r"\b(?:is|are|was)\s+(?:this|the|our)\s+(?:a\s+|an\s+)?(?:private|confidential|secure)\s+"
    r"(?:chat|conversation|call|line|session|thread)\b"
    r"|\b(?:is|are|was|will|would)\s+(?:this|our|the)\s+(?:chat|conversation|call|line|"
    r"session|thread)\s+(?:going\s+to\s+)?(?:be\s+|stay\s+|stays\s+|get\s+|gets\s+)?"
    r"(?:private|confidential|secure|saved|recorded|stored|logged|kept|seen|read|shared)\b"
    r"|\bwill\s+(?:this|it)\s+(?:be|stay|get)\s+(?:private|confidential|recorded|saved|"
    r"stored|logged|kept)\b"
    r"|\bis\s+(?:this|it)\s+going\s+to\s+(?:be\s+|stay\s+|get\s+)?(?:private|confidential|"
    r"recorded|saved|stored|logged|kept)\b"
    # The bot's own verb with "this" as its whole object. Anything after the object is a favour
    # about a thing of the world ("can you store this in the fridge"), so the line has to end.
    r"|\b(?:do|does|will|would|are|can|could)\s+(?:you|u)\s+(?:be\s+)?"
    r"(?:keep|keeping|save|saving|record|recording|store|storing|log|logging)\s+"
    r"(?:this|it|what\s+i\s+say)(?=\s*[?.!]*\s*$)"
    r"|\bwho\s+(?:sees|reads|hears|can\s+see|can\s+read|can\s+access)\s+"
    r"this(?:\s+(?:chat|conversation|thread))?(?=\s*[?.!]*\s*$)"
    # "safe" and "secure" need the bot in the line, because "is my data safe to delete" is a
    # question about a file. Said about the whole of the person's data and nothing else, it is the
    # keeping: "is my data safe", "is my information safe with you".
    r"|\b(?:is|are)\s+(?:my|our)\s+(?:data|details|info|information|messages?|words)\s+"
    r"(?:private|confidential)\b"
    r"|\b(?:is|are)\s+(?:my|our)\s+(?:data|details|info|information)\s+"
    r"(?:safe|secure)(?:\s+(?:with|on|in)\s+(?:you|here|this\s+chat)\b)?(?=\s*[?.!]*\s*$)"
    r"|\b(?:is|are)\s+(?:my|our)\s+(?:data|details|info|information|messages?|words)\s+"
    r"(?:safe|secure)\s+(?:with\s+(?:you|u)|here)\b"
    # The line asks what becomes of the person's words without saying so in any of the shapes
    # above: "what happens to what i say", "what happens to my messages". The ask has to end
    # there - "what happens to my data if i switch to pay as you go" is a phone contract, and
    # "what happens to my car if i miss the tax" is a car.
    r"|\bwhat\s+(?:happens|happened|will\s+happen|would\s+happen)\s+to\s+"
    r"(?:what\s+i\s+(?:say|said|tell|type|write|wrote)\b"
    r"|my\s+(?:messages?|data|words|details|information|info|chats?)\b|our\s+(?:chat|"
    r"conversation)\b)(?=\s*[?.!]*\s*$)", re.I)


# "can you browse the internet", "do you have internet access", "can you google that", "are you
# connected to the internet". A question about the bot's own connection, not about the person's
# wifi: a line about their laptop, their router or their own getting online keeps its answer.
# What only a live source knows: a time, a number, a price, a stock, a review, a flight. A search
# ask is the bot's own limit only when what it is asked for is one of these, because that is the
# half it cannot do. A method, a recipe or somebody's rights are what the bot is for, so a line
# that asks for one of those keeps its answer even with "for me" on the end: "search for how long
# to boil an egg for me" was being refused with "Nothing live on this end", and so were "search
# for the best way to clean a mattress for me" and "look up my rights for me".
LIVE_ASK = (
    r"(?:times|timetables?|schedules?|numbers?|phone|telephone|address|postcode|postcodes?|"
    r"prices?|costs?|fares?|deals?|offers?|reviews?|ratings?|scores?|results?|news|"
    r"flights?|trains?|buses?|coaches|tickets?|availability|stock|opening\s+hours|"
    r"weather|forecast|vacanc(?:y|ies)|listings?|status|delays?|traffic|menu|"
    r"lead\s+times?|deadlines?|exchange\s+rates?)")

ONLINE_ASK = re.compile(
    r"\b(?:can|could|do|does|are|is|have)\s+(?:you|u)\s+(?:[a-z]+\s+){0,3}?"
    r"(?:browse|search|google|look[\s-]+(?:things|stuff|it|that|them)?\s*up|check|access|reach|"
    r"connect(?:ed)?|go|get)\s*(?:the\s+|a\s+)?(?:internet|web|online|net|google|sites?|"
    r"websites?|pages?)\b"
    r"|\b(?:can|could|do|does|are|is|have)\s+(?:you|u)\s+(?:[a-z]+\s+){0,3}?"
    r"(?:online|connected|internet|web|internet\s+access)\b"
    r"|\bdo\s+(?:you|u)\s+have\s+(?:[a-z]+\s+){0,2}?(?:access|internet|wifi)\b"
    # A person's own connections are not the network ("do you have a connection with your family"),
    # so a bare `connection` needs what it is a connection to.
    r"|\bdo\s+(?:you|u)\s+have\s+(?:[a-z]+\s+){0,2}?connection\s+(?:to|with)\s+(?:the\s+)?"
    r"(?:internet|web|net|online)\b"
    # "can you search for a recipe with chicken" is a person who wants the chicken, and the bot has
    # the chicken. A bare "search" only says the bot cannot reach the web when its object is the web
    # or nothing ("can you search for me", "can you search online").
    r"|\b(?:can|could|would|will)\s+(?:you|u)\s+(?:please\s+)?(?:google|"
    r"search\b(?=\s*(?:$|for\s+(?:me|us)\b|around\b|"
    r"(?:it|that|this|things|stuff|something)\b|online\b|the\s+(?:web|internet|net)\b|"
    r"sites?\b|pages?\b|websites?\b))|"
    r"look\s+(?:it|that|this|things|stuff)\s*up)\b"
    # "search for flights for me", "google the number for me", "can you look up the times for me":
    # the ask is the search itself, with what is wanted in the middle of the line rather than after
    # the verb. The "for me" is what makes it this ask and keeps the fence: "can you search for a
    # recipe with chicken" wants the chicken, and the bot has the chicken.
    #
    # The "for me" has to end the line, and that is the whole fence. "look up for me how to unblock
    # a drain", "look up for me how long to boil an egg", "search for me how long to roast
    # chicken" all carry the same three words in the middle and then say what they actually want,
    # which is a method the bot can answer - reading them as a request to browse threw those
    # answers away and said "No connection at all" instead. A line that stops after the person it
    # is for is a line that has nothing for the bot to answer: "search for flights for me",
    # "google the number for me", "can you look up the times for me". Only a politeness may follow
    # it, because politeness asks nothing.
    r"|\b(?:google|search|look\s+(?:\w+\s+){0,2}?up)\b[^.?!]{0,30}?\b" + LIVE_ASK +
    r"\b[^.?!]{0,30}?\bfor\s+(?:me|us)\b"
    r"\s*(?:(?:please|then|now|thanks|thank\s+you)\s*)*[.?!]*\s*$")


# Not every one of those is a skill. "im bad at lying" and "im terrible at keeping secrets" are
# said as a virtue, "im bad at taking compliments" and "im bad at goodbyes" are a way of being, and
# "im bad at relaxing" is the whole trouble rather than a method somebody skipped: offering to fix
# any of them is the bot telling a person their character has gone wrong, and the two pools that
# answered those lines before (the neutral nod and the gentle one) were better than that. A skill
# is something with a method - cooking, driving, maths, saving - and these are not.
# The families are words because no shape separates them: the understanding engine reads no topic
# for `the guitar`, `parallel parking` or `names`, and a gerund does not tell `saving` from
# `trusting`. So each family names what it is: the untruths, the virtues and failings, thanking and
# asking, holding the tongue, the ends of the day, and money.
A_WAY_OF_BEING = re.compile(
    r"\b(?:"
    # the untruths, and keeping something back
    r"lying|liar|lies|telling (?:a )?lie|telling lies|telling the truth|secrets?|keeping a secret"
    r"|cheating|stealing"
    # how somebody is with other people, named as a virtue or a failing
    r"|being (?:selfish|mean|kind|nice|honest|patient|cruel|brave|open|vulnerable|present)"
    r"|selfish|unkind|cruel|mean to (?:people|him|her|them|anyone)"
    r"|grudges?|holding a grudge|forgiving|apologis?ing|trust\w*|vulnerable|opening up"
    # taking something offered, and asking for it
    r"|compliments?|taking help|accepting (?:help|praise|a compliment)"
    r"|saying (?:thank you|thanks)|thanking (?:people|someone|him|her|them)"
    r"|asking for (?:help|things|a favour|favours|what i want)"
    r"|asking (?:people|someone|him|her|them) for"
    # holding the tongue, and taking a thing about yourself
    r"|keeping my mouth shut|biting my tongue|holding my tongue|keeping quiet|personally"
    r"|taking (?:a )?criticism|taking feedback"
    # the ends of the day, and the endings
    r"|goodbyes?|saying goodbye|relaxing|resting|switching off|doing nothing|not working"
    r"|chilling out|chill out|chilling|slowing down"
    r"|taking (?:a )?breaks?|taking time off"
    # money held and money spent
    r"|spending money)\b")


# What the leaving is. The verb and the place are read together, so "my son went to university"
# and "my friend is moving away" are the same shape, and a move within the same town ("moving
# into a bigger flat") is not: the reply is about somebody going out of reach of the ordinary
# week. "Moved to" takes a name and not an article for the same reason - "moved to the sofa" is
# not a leaving, and "moved to australia" is.
LEFT_BEHIND = re.compile(
    # "went home", "goes home", "going home" are the same words as a leaving and are far more
    # often a routine - "my son goes home at 3" is a child getting the bus back, not a room going
    # empty - so the home branch keeps only the verbs that mean it and away/abroad keep the rest.
    r"\b(?:left|leaving|leaves|moved|moving)\b[^.?!,;]{0,24}\bhome\b|"
    r"\b(?:left|leaving|leaves|went|going|gone|goes|go|off|moved|moving|heading|headed)\b"
    r"[^.?!,;]{0,24}\b(?:away|abroad|overseas|out of the house)\b|"
    r"\b(?:moving|moved|relocat\w+|emigrat\w+)\s+(?:away|abroad|overseas)\b|"
    r"\b(?:went|going|gone|goes|go|off|left|leaving|leaves|starts?|starting|started)\s+to\s+"
    r"(?:uni|university|college)\b|"
    r"\b(?:starts?|starting|started)\s+(?:uni|university|college)\b|"
    # "my daughter has just left for uni": the same leaving said with "for" instead of "to", which
    # reached the echo while every other wording of it had an answer.
    r"\b(?:left|leaves|leaving|went|going|gone|goes|off|off\s+to)\s+(?:for\s+)?"
    r"(?:uni|university|college)\b|"
    # A move named with a place is a leaving ("moved to australia"), but only a move verb says
    # that on its own: "my dad went to prison" and "my wife went to work" are the same shape and
    # neither is somebody leaving home, which is what this pool's reply talks about.
    r"\b(?:moved|moving|moves|relocated|relocating|relocates|emigrated|emigrating|emigrates)"
    r"\s+to\s+(?!a\b|an\b|the\b|another\b|his\b|her\b|their\b|our\b|my\b|that\b|this\b)"
    r"[a-z]|"
    r"\bempty\s+nest\b|\b(?:fly|flying|flies|flew|flown)\s+(?:the|their)\s+nest\b",
    re.IGNORECASE)


# The answer came back: "i heard back", "they got back to me", "the results came out". Told from
# the person's own side, as the wait is, and only about the place that hands the answer out - "i
# havent heard from my brother in weeks" is a person gone quiet, not a result.
_LANDED = re.compile(
    r"\b(?:(?:i|we|she|he|they)\s+(?:finally\s+|just\s+)?heard\s+back|"
    r"(?:i|we)\s+(?:finally\s+|just\s+)?heard\s+from\s+(?:them|the\s+(?:hospital|school|"
    r"college|uni|university|company|employer|agency|council|landlord|court|bank|dwp|clinic|"
    r"surgery|job|firm|office))|"
    r"(?:they|she|he|someone)\s+got\s+back\s+to\s+(?:me|us)|"
    # "i got my results back", "i got my exam results", "i got our grades": what people say is
    # the thing the answer is written on, and the words before it are whose it is and what kind.
    # "finally" is left out on purpose: "i finally got my results" already means the wait is over
    # and it went well, and a card on main says so. Taking that line here answers it worse.
    r"(?:i|we)\s+(?:just\s+)?got\s+"
    # Whose it is, then what kind. The determiner is required, because without it "no" slides
    # into the slot and "i got no reply" is read as an answer that came back. The kind words are
    # a closed list, because two free words let a favour in: "i got my mother a letter" and
    # "i got my friend an email" are things a person did for somebody, not news of their own.
    # "your" is not in the list: "i got your email" is the person telling me the message arrived,
    # and there is nobody to ask "what did they say" about.
    r"(?:the|an?|my|our|his|her|their)\s+"
    r"(?:(?:exam|exams|test|tests|mock|mocks|module|modules|gcse|gcses|a-level|alevel|"
    r"driving|theory|coursework|term|final|first|second|scan|scans|biopsy|blood|bloods|"
    r"x-?ray|labs?)\s+){0,2}"
    r"(?:answer|reply|verdict|results?|letter|email|marks?|scores?|grades?)(?:\s+back)?"
    # ...and the answer itself did not then go up, down or wrong: "i got my grades up" is a
    # person telling you something good, not a quiz, and "i got my answer wrong" is not news.
    r"(?!\s*(?:up|down|wrong|off|mixed|lost|missing|confused)\b)|"
    r"(?:the\s+)?(?:results?|verdict)\s+(?:came|came out|is in|are in))\b", re.I)


# Each pool answers the day itself. The question is left off most of them on purpose: a remark
# about the weather is not an invitation to be asked how it makes them feel, and a friend who
# answered every one with a question would be no company at all.
THE_DAY = {
    "cold": (
        "Bit parky, isn't it. Extra layer on, and put the heating on an hour before you want it "
        "warm rather than when you're cold.",
        "Cold one. Thick socks make more difference than people expect.",
        "That sort of cold gets into the bones. Hot drink, something warm on, and don't sit still "
        "in one room too long.",
        "Freezing out, isn't it. Shut the curtains at dusk and it holds the heat in.",
    ),
    "rain": (
        "Raining again. Good day for the kettle and something slow on the telly.",
        "That sort of rain gets in everywhere. Coat rather than umbrella today, and leave the "
        "washing till tomorrow.",
        "Wet one, then. Shoes stuffed with newspaper overnight dry out properly, if you get caught "
        "in it.",
        "Never mind. It's a good excuse to do nothing much indoors.",
    ),
    "wind": (
        "Blowy out there. Anything light in the garden will be next door by teatime.",
        "Wind like that takes doors with it. Worth propping the gate before it does.",
        "That's a bin-day wind. Hold on to the wheel if you're driving in it.",
        "Nasty wind, that. Good reason to stay in.",
    ),
    "hot": (
        "Hot one, isn't it. Curtains shut while the sun's on the windows really does keep it "
        "cooler in.",
        "Too hot to do anything fast. Cold drink, water on the wrists, and save the jobs for this "
        "evening.",
        "That kind of heat takes it out of you. Drink more than you think you need.",
        "Boiling, isn't it. A bowl of ice in front of a fan does more than the fan on its own.",
    ),
    "grey": (
        "Grey one. Put the lamp on early rather than at dusk and the afternoon feels less long.",
        "Grim out, isn't it. Nothing wrong with a quiet one indoors.",
        "Miserable out. Good day for the job you've been putting off, or for none at all.",
        "Dull one. It's the light more than the cold that gets people.",
    ),
    "fog": (
        "Foggy one. Lights on even in the day, and more room than you think you need.",
        "Thick out there. Worth leaving a bit earlier while it's like this.",
        "Fog like that slows everything down. Nothing wrong with a slow start.",
    ),
    "sun": (
        "Lovely, isn't it. Get out in it for a bit, even if it's only round the block.",
        "Beautiful out. Worth taking your cup of tea outside.",
        "That's the day for being outdoors. Suncream on if you're out past eleven.",
        "Gorgeous. That sort of day makes everything easier.",
    ),
    # The day named by what it is not: "not cold today", "not too hot", "isn't raining". The
    # person has ruled a kind out rather than named one, so the reply agrees with the ruling and
    # stays out of the way - and it must not claim the opposite, because "not cold" is not
    # "lovely". These say the day asks nothing of you, which is true of every one of them.
    "mild": (
        "No complaints then. Those are the days to be out in without thinking about it.",
        "Mild one, that. Good day for the jobs you keep putting off, or for none at all.",
        "Fair enough. The days that ask nothing of you are the ones worth using.",
        "Not bad at all, then. Worth a walk while it is like this.",
    ),
}


# The day still to come, answered as the plan it changes rather than as the day outside now:
# "meant to be nice tomorrow" is not an afternoon to enjoy yet. Same kinds as THE_DAY, and
# the fog one is here because a foggy morning is a different day to a grey one.
THE_DAY_AHEAD = {
    "cold": (
        "Cold one coming. Anything outside that hates frost is worth bringing in tonight.",
        "Meant to turn cold. Get the grit out and the car warmed before you need either.",
        "Cold forecast. Layers for the morning, and leave the heating on a timer.",
    ),
    "rain": (
        "Rain coming. Anything you want dry is worth doing before it arrives.",
        "Wet forecast. Coat rather than umbrella tomorrow, because the wind comes with it.",
        "Rain later, then. Put the outside bit of the day in the morning if you can.",
    ),
    "wind": (
        "Wind coming. Anything light in the garden will be next door by tomorrow night.",
        "Blowy forecast. Worth checking the gate and the bins before it gets going.",
        "Wind later, then. Anything loose up high is worth sorting while it is calm.",
    ),
    "mild": (
        "Mild forecast. Nothing to plan around, which is the best kind of day.",
        "Nothing much coming, weather-wise. Good day to have something booked.",
        "Fair forecast. Worth putting the outside thing in while it holds.",
    ),
    "hot": (
        "Heat coming. Curtains shut in the morning really does keep it cooler in.",
        "Hot forecast. Jobs in the morning, and the afternoon for nothing much.",
        "Meant to be hot. Worth getting the fan down before you need it.",
    ),
    "grey": (
        "Grey forecast. Nothing much to plan around, unless you were counting on the light.",
        "Meant to be dull. Fine day for the job you have been putting off indoors.",
        "Grey one coming. Put the lamp on early and the afternoon feels less long.",
    ),
    "fog": (
        "Fog forecast. Lights on in the morning and more room than you would leave.",
        "Meant to be foggy. Worth setting off ten minutes earlier while it lifts.",
        "Fog coming. Anything you were going to drive for is easier after it clears.",
    ),
    "sun": (
        "Nice one coming. Worth saving the outdoor bit of the day for it.",
        "Sun forecast. Suncream in the bag if you are out past eleven.",
        "Meant to be lovely. That is the day for the thing you keep putting off.",
    ),
}

# News a friend does not answer with a fix question: a marriage ending, somebody in hospital, a
# scan that came back bad, sight going, panic that will not let go. The light pools ask what can be
# done ("Annoying. Is it a quick fix or a whole thing?") and there is nothing to be done about any
# of these, so they are read as heavy and the sympathy pool takes the turn (snappy-net and
# scarlet-wasp on #5479, five rows each).
HEAVY_NEWS = re.compile(
    # A leaving is said as the person leaving, so "left me a voicemail" and "we walked out of the
    # film early" are not it: the leaving either ends the line or names what it did to the person.
    r"\b(?:left\s+me\b(?!\s+(?:a|an|the|my|some|this|that|no)\b)|"
    r"walked\s+out(?:\s+on\s+me)?\W*$|dumped\s+me|kicked\s+me\s+out|"
    r"threw\s+me\s+out|wants?\s+a\s+divorce|"
    # Somebody in hospital, not a visit and not a job: "i work in the hospital" and "i went to
    # see my gran in hospital" are both ordinary news.
    r"(?:is|are|was|were|been|kept|taken|rushed|put|now|still)\s+(?:in|into)\s+(?:the\s+)?"
    r"hospital|hospitali[sz]ed|in\s+(?:the\s+)?icu|intensive\s+care|"
    # A faculty going, a result coming back, a diagnosis being given.
    r"losing\s+my\s+(?:sight|hearing|memory|voice|hair|leg|arm)|gone\s+blind|going\s+blind|"
    r"going\s+deaf|lost\s+my\s+(?:sight|hearing)|"
    r"(?:the|my)\s+scan\s+(?:came\s+back|shows?|showed|is\s+back)|scan\s+came\s+back|"
    r"results?\s+came\s+back|diagnosed\s+with|being\s+treated\s+for|"
    r"starting\s+(?:chemo|treatment|dialysis)|"
    # A living gone, and a wait nobody can shorten: both are news a fix question is wrong about,
    # and neither is an accident that settles (handy-boot and snappy-net on #5479). They are read
    # as heavy rather than rough because the rough pool asks how a body is easing.
    r"lost\s+my\s+(?:job|work|hours)|laid\s+off|made\s+redundant|been\s+(?:sacked|fired)|"
    r"got\s+(?:sacked|fired|let\s+go)|sacked\s+(?:from|on)|let\s+go\s+from|"
    r"wait(?:ing)?\s+(?:\w+\s+){0,4}(?:weeks|months)|on\s+a\s+waiting\s+list|"
    r"months?\s+for\s+(?:the\s+|an\s+|a\s+)?(?:appointment|scan|referral|operation)|"
    # Panic and anxiety said as the person's state, not as an app or a book.
    r"panic\s+attack|anxiety\s+attack|having\s+(?:a\s+)?panic|my\s+anxiety\s+is|"
    r"(?:i'?m|im|feel|feeling|been\s+feeling)\s+(?:really\s+|so\s+|very\s+|always\s+|"
    r"constantly\s+)?anxious|so\s+anxious|"
    r"sectioned|gone\s+into\s+care)\b", re.I)


# The absence named instead of the errand: "sorry i went quiet", "sorry for the silence",
# "sorry i havent replied", "sorry, back now". These are the other half of the same apology as
# the errand above, and every one of them used to reach the nod. The words have to be about the
# conversation itself, so an apology for anything else keeps its own reply.
ABSENCE = re.compile(
    r"\b(?:went|gone|been|be)\s+(?:quiet|silent|away|incommunicado|"
    r"off(?!\s+(?:the\s+)?(?:grid|radar|map)))\b"
    r"|\b(?:i|we)(?:'?ve|'?d)?\s+(?:have\s+|had\s+|been\s+)?(?:gone|disappeared|"
    r"vanished|missing|quiet|silent)\b"
    r"|\bfor\s+(?:disappearing|vanishing|going quiet|being quiet|being away|being gone)\b"
    r"|\b(?:the|a)\s+silence\b|\bsilent\s+(?:for|since)\b"
    r"|\b(?:havent|haven'?t|hadnt|hadn'?t|didnt|didn'?t|not|never)\s+(?:replied|reply|"
    r"replying|written|write|writing|answered|answering|been in touch)\b"
    r"|\b(?:missed|saw|seeing)\s+(?:your|that)\s+(?:message|msg|reply|text|email|call)\b"
    r"|\b(?:slow|late)\s+(?:reply|response)\b"
    r"|\b(?:mad|really|very|so|proper|dead)?\s*busy\b"
    r"|\b(?:fell|been|was)\s+(?:fast\s+)?asleep\b"
    r"|\blost\s+track(?:\s+of\s+(?:time|the\s+(?:time|thread|plot)))?\b"
    r"|\bphone\s+(?:died|went dead|was dead)\b"
    # Being away from the phone is the same absence said the other way round ("sorry, been off
    # my phone", "sorry, been away from my phone"), and so is noticing late what was written
    # ("sorry, i only just saw this"). Without these the apology was the head of a line the
    # pause did not read, and the nod answered it: "Thanks for telling me - I'm here if you want
    # to dig into any of that."
    r"|\b(?:been|be|went|gone|was)\s+(?:off|away\s+from)\s+(?:my|the|your|his|her)?\s*"
    r"(?:phone|mobile|texts|messages|emails|email|inbox)\b"
    r"|\b(?:only\s+)?just\s+saw\s+(?:this|that|your\s+(?:message|msg|text|email|reply))\b"
    # The same absence as what kept them: on the phone, and off the map altogether.
    r"|\b(?:was|were|been|be)\s+on\s+(?:my|the|your|his|her)\s*(?:phone|mobile)\b"
    r"|\b(?:been|be|went|gone|was)\s+off\s+(?:the\s+)?(?:grid|radar|map)\b"
    r"|\b(?:keep|kept)\s+you\s+waiting\b"
    r"|\bback\s+(?:now|again)\b")


# One line per kind of place, because where the number is kept is what differs: on the letter they
# sent, on the bill, on the back of a card, or on the page the service lives at.
NUMBER_PLACES = (
    (("doctors", "doctor", "gp", "surgery", "dentist", "dental", "hospital", "clinic",
      "pharmacy", "chemist", "optician", "midwife", "health visitor"),
     ("I can't hold phone numbers, sorry - they change, and a wrong one costs you a morning. The "
      "practice's own page on a map app has it, it is on the letter or text they sent you, and "
      "the NHS app lists it too.",
      "No directory at this end, so I would only be guessing at the digits. The letter with your "
      "appointment on it has the number, and the practice's page has it if that has gone "
      "missing.")),
    (("council", "housing association", "housing office", "tip", "recycling centre", "dump",
      "library", "leisure centre", "parking permit", "parking office", "bins"),
     ("I can't look a phone number up, sorry - a wrong one sends you round in circles. The "
      "council's site has a contact page with the number for the right department, and it is on "
      "the bill they last sent you.",
      "Nothing here that can find a number, so I won't guess at one. Your council tax bill, or "
      "the council's own contact page, has the number for the department you need.")),
    (("bank", "building society", "credit card", "insurer", "insurance", "mortgage"),
     ("I can't hold phone numbers, sorry. A bank's number is on the back of your card and in its "
      "app; an insurer's is on the policy letter, and both are faster than a search.",
      "No number that I can give you - they change and I have no way to check. The back of the "
      "card, or the policy letter if it is insurance, has the one that gets answered.")),
    (("water company", "water board", "energy supplier", "energy company", "electricity",
      "gas company", "broadband", "phone company", "supplier", "utility"),
     ("I can't look up a supplier's number, sorry. It is on the bill, in their app, and usually "
      "at the top of their website - and the bill carries your account number, which they ask "
      "for first.",)),
    (("dvla", "passport office", "tax office", "hmrc", "jobcentre", "job centre", "benefits",
      "pension", "dwp"),
     ("I can't hold a government number, sorry - they change with the department. Search gov.uk "
      "for the service and the page for it has the number and the hours the lines are open.",)),
    (("school", "nursery", "childminder", "college", "university"),
     ("I can't look a school's number up, sorry. The office number is on the letter or email "
      "they sent you, and on the school's own site under Contact.",)),
    (("vet", "vets", "veterinary", "animal hospital"),
     ("I can't hold phone numbers, sorry. The practice's page, or the card they gave you, has "
      "it - and save their out-of-hours number while you are looking, since that is the one "
      "nobody can find at ten at night.",)),
    (("takeaway", "restaurant", "chippy", "pizza", "plumber", "electrician", "garage",
      "taxi", "minicab", "hairdresser", "barber", "gym", "pub", "hotel", "cafe"),
     ("I can't hold a number like that, sorry - a place's number changes and I have no way to "
      "look it up. A map app shows it with the opening times, and it is on the card, menu or "
      "door the place gave you.",)),
)


# Asking for the words is not always "what should i say": a person with a conversation coming
# asks "should i say something to him", "how do i bring it up", "shall i have a word with my
# flatmate", "what would you say to him", and every one of those got the honest shrug. The
# object keeps it narrow: "say something to" (not "my son keeps swearing what should i say to
# him", which a parenting entry answers), "bring it/this/that up" (not "bring up a baby",
# which is not a conversation at all), "a word with", and "what would you say to <person>".
WORDING_SOMEONE = re.compile(
    r"\b(?:should|shall|do|can|could|would)\s+i\s+(?:say|mention)\s+(?:something|anything)\s+to\b"
    r"|\bhow\s+(?:do|should|can|could)\s+i\s+bring\s+(?:it|this|that)\s+up\b"
    r"|\b(?:have|has|having)\s+a\s+(?:quick\s+|quiet\s+|bit\s+of\s+a\s+)?word\s+with\b"
    r"|\bwhat\s+(?:would|will)\s+you\s+say\s+to\s+(?:him|her|them|my|your|the)\b"
    # The same ask with a different verb. "how do i raise it without sounding like i'm keeping
    # score", "how do i broach it", "how do i put it to her" all want the shape of a hard
    # sentence, and none of them reached the wording pool: the line was read for its topic and
    # came back as the answer that topic has, which for a friend who keeps cancelling is the
    # message the other person sends. The verb needs its object to count, because "raise" alone
    # is a complaint, a child and a pay rise, and those are answered elsewhere.
    # The plainest way anyone asks for this, and the one that was missing: "what do i say to
    # her", "what do i say to him", named with nothing in front of it. On its own that phrase is
    # the asking-someone-out key in bot/knowledge/family.py, and a line about somebody already in
    # the person's life - the mother-in-law, the sister who is low, the landlord - came back with
    # the first-date script. The date row still wins where a date is what is meant (it is a row in
    # the table and this pool is a fallback), so the phrase can be read here as well.
    r"|\bwhat\s+(?:do|should|can|could)\s+i\s+(?:actually\s+|even\s+)?say\s+to\s+"
    r"(?:him|her|them|people)\b(?!\s+(?:if|whether)\b)"
    r"|\bhow\s+(?:do|should|can|could)\s+i\s+(?:raise|broach|word|phrase|put)"
    r"\s+(?:it|this|that|the\s+subject|the\s+issue)\b"
    # "how do i break it to my parents" is the same ask with the plainest verb there is. The
    # "to" is required, because "how do i break it in" is a pair of shoes and "how do i break it"
    # is a machine.
    r"|\bhow\s+(?:do|should|can|could)\s+i\s+break\s+(?:it|this|that|the\s+news)\s+to\b"
    # The same ask with the person left out, which is how it is said when the room is obvious or
    # not decided yet: "how do i break the news" was read as a request for the day's news and
    # sent to a news app. "Break the news" with nobody named is a message to write, never a
    # bulletin, so it goes here beside the "to" form.
    r"|\bhow\s+(?:do|should|can|could)\s+i\s+break\s+the\s+news\b"
    r"|\bbreak\s+the\s+news\s+to\b"
    # "without sounding like ...", "without coming across as ..." name the tone the person is
    # trying not to have, and a tone is what a wording answer is for. Nothing else in the bot
    # reads "sounding like", so this cannot take a question another answer owns.
    r"|\bwithout\s+(?:sounding|coming\s+across)\b"
    r"|\bnot\s+(?:sounding|coming\s+across)\s+like\b"
    # The bare "sounding like a/the ..." is not here on purpose. A noise is described that way
    # ("my car is sounding like a tractor", "the engine is sounding like a bag of spanners") and
    # the reply told the person how to word a message. What the tone ask looks like is the words
    # above, or a person who does not want to come over a certain way.
    r"|\b(?:don'?t|do\s+not)\s+want\s+to\s+(?:sound|come\s+across)\b")


# The pattern question asks what sets the doing off and what has been tried - so it is only right
# about a doing the person would want to change. A doing alone is not that: "i always take the bus",
# "we always go to cornwall in august", "i always put the milk in first" and "i always arrive early"
# are a life, not a problem, and asking what they have tried about a holiday asserts a fault they
# have not got (cream-flag's read). So the doing has to be one of the acts people bring here wanting
# help with, or the line has to say out loud that they mind it.
HABIT_PROBLEM_ACT = re.compile(
    r"(?:interrupt|snap|shout|yell|argue|fight|nag|criticis|criticiz|blame|apologi[sz]e|"
    r"put\s+off|puts\s+off|putting\s+off|procrastinat|"
    r"leav(?:e|es|ing)\s+(?:things|it|everything|jobs|the\s+lot)|"
    r"apologi[sz](?:e|es|ed|ing)|"
    r"ask(?:s|ing)?\s+for\s+help|"
    r"never\s+manage|manages\s+to|"
    r"sav(?:e|es|ing)\s+(?:anything|any\s+money)|"
    r"put(?:s|ting)?\s+(?:everyone|everybody|others|people)\s+(?:else\s+)?first|"
    r"text(?:s|ing)?\s+first|"
    r"get(?:s|ting)?\s+round\s+to|"
    r"go(?:es|ing)?\s+blank|"
    r"finish|finishes|finishing|forget|forgets|forgetting|forgot|lose|loses|losing|"
    r"cancel|cancels|cancelling|canceling|avoid|avoids|avoiding|overthink|overthinks|"
    r"overthinking|second-guess|second\s+guess|worry|worries|worrying|complain|complains|"
    r"complaining|moan|moans|moaning|compare|compares|comparing|hide|hides|hiding|"
    r"shut|shuts|shutting|withdraw|withdraws|withdrawing|run\s+away|running\s+away|"
    r"give\s+up|giving\s+up|give\s+in|giving\s+in|stay\s+up|stays\s+up|staying\s+up|"
    r"work\s+(?:late|too\s+hard|too\s+much)|working\s+(?:late|too\s+hard|too\s+much)|"
    r"drink\s+too|drinks\s+too|drinking\s+too|smoke|smokes|smoking|spend|spends|spending|"
    r"gamble|gambles|gambling|eat\s+too|eats\s+too|eating\s+too|eat\s+at\s+night|"
    r"binge|binges|bingeing|starve|starves|starving|skip|skips|skipping|lie|lies|lying|"
    r"mean\s+to|means\s+to|meaning\s+to|say(?:ing|s)?\s+yes|say(?:ing|s)?\s+sorry|"
    r"check|checks|checking|scroll|scrolls|scrolling|pick|picks|picking|bite|bites|biting|"
    r"turn\s+up\s+late|turning\s+up\s+late|arrive\s+late|arriving\s+late|"
    r"end\s+up|ends\s+up|ending\s+up|can'?t\s+stop|cant\s+stop)", re.I)


# What happened to them, in the words people use. A death is the loss module's and a fall or a
# bleed from somebody who is in front of the person is safety's, so both are kept out of it here.
# Severity is the whole reading: "my daughter hurt her finger" and "my mum hurt her back" are a
# scraped finger and a bad back, and "That's a horrible thing to hear" is a lie about them, so a
# bare hurt needs a word that says how bad. An attack or a crash says its own severity.
HURT_EVENT = re.compile(
    r"\b(?:got|gets|getting|was|were|is|are|been|had|has|keeps?)\s+"
    r"(?:badly|seriously|really|terribly)\s+(?:hurt|injured|burned|burnt|scalded)\b"
    r"|\b(?:hurt|injured|burned|burnt|scalded)\s+(?:badly|seriously)\b"
    r"|\b(?:admitted|taken|rushed|airlifted|kept)\s+(?:in\s+)?to\s+"
    r"(?:hospital|a\s*&\s*e|intensive\s+care)\b"
    r"|\bin\s+(?:intensive\s+care|a\s*&\s*e|hospital)\b"
    # A verb that is only ever violence on its own: nobody is punched "in the figures of speech".
    r"|\b(?:got|gets|getting|was|were|is|are|been|had|has|keeps?)\s+"
    r"(?:nearly\s+|almost\s+)?(?:attacked|bitten|bit|punched|stabbed|kicked|mugged|assaulted|"
    r"strangled|electrocuted)\b"
    r"|\b(?:attacked|punched|stabbed|assaulted|mugged)\b"
    # ... and the rest are figures of speech as often as they are injuries, so each one keeps the
    # object that makes it real: "beaten up" is a beating and "beaten at chess" is not, "hit by a
    # car" is news and "hit by the flu" is not, "robbed of the win" is not a robbery.
    r"|\bbeaten\s+up\b|\b(?:got|was|were|been|gets|is|are)\s+beaten\s+up\b"
    r"|\bhit\s+by\s+(?:a|an|the)\s+(?:\w+\s+)?"
    r"(?:car|bus|bike|bicycle|van|lorry|truck|train|tram|taxi|motorbike|driver)\b"
    r"|\bhit\s+(?:in\s+the\s+(?:face|head|eye)|with\s+a\s+(?:brick|bottle|bat|knife))\b"
    r"|\bknocked\s+(?:over|down)\b"
    r"|\b(?:drowned|shot)\b(?=\s+(?:in|at|by)\b)"
    r"|\bpushed\s+(?:down|over|off|in\s+front)\b|\bpushed\s+into\s+the\s+(?:road|traffic|water)\b"
    r"|\bthrown\s+(?:from|off|out\s+of)\b"
    r"|\brun\s+over\s+by\s+(?:a|an|the)\s+(?:\w+\s+)?"
    r"(?:car|bus|bike|bicycle|van|lorry|truck|train|tram|taxi|motorbike)\b"
    r"|\b(?:nearly|almost)\s+drowned\b"
    r"|\bwas\s+robbed\b(?!\s+of\b)|\brobbed\s+(?:at|in|on|outside)\b"
    # "my dad cut his hand badly" is a bad cut, and the three words between are what make it news.
    r"|\bcut\s+(?:his|her|their)\s+\w+\s+(?:badly|open)\b"
    r"|\b(?:fell|fallen|collapsed)\b"
    # A person is "in an accident"; a toilet accident is "had an accident at nursery", and the
    # road or the hospital word is what tells them apart.
    r"|\b(?:was|were|is|are|been)\s+in\s+(?:a|an)\s+"
    r"(?:car\s+|road\s+|motor\s+|bike\s+|cycling\s+)?accident\b"
    r"|\b(?:car|road|motor|bike|bicycle|traffic)\s+(?:crash|accident|collision)\b"
    r"|\b(?:crash|collision|ambulance|casualty)\b")


# A reading of a rating, of a slip and of the moment after one. Moved out of `fallback.py`
# whole: the tables are unchanged and the names come back under the same ones.
# "Would have been" is the whole reading: it puts the day in a life that did not get there. The
# event word has to be in the line, so a comparison ("it would have been quicker by train") and a
# wish about a thing ("it would have been nice to go") keep their own replies.
WOULD_HAVE_BEEN = re.compile(
    r"\b(?:would|should|will|'?d) ?(?:have|'?ve) been\b[^.?!]{0,24}?\b(?:my|our|her|his|their|"
    r"mum'?s|dad'?s|his|the)\b[^.?!]{0,12}\b(?:" + MILESTONE_EVENT + r")\b"
    r"|\b(?:" + MILESTONE_EVENT + r")\b[^.?!]{0,16}\b(?:would|should) ?(?:have|'?ve) been\b")


# A rating of an ability is not a judgement of the self. "im rubbish at maths" is a thing to get
# a hand with, not a heavy way to feel about yourself, and the difference is the object: "im
# useless at DIY" rates a skill, "im useless at everything i try" and "im hopeless at life" rate
# the whole person. So a rating word in front of at/with/in stands aside unless what follows is
# everything, anything, all of it, or life itself.
RATES_A_SKILL = re.compile(
    r"\b(?:useless|rubbish|crap|hopeless|no good|bad|poor|terrible|awful)\s+(?:at|with|in)\s+"
    r"(?!(?:everything|anything|life|myself|it all|all of it)\b)")
# The same rating said by the person about one of their own skills, which is a line the bot should
# answer with help and not with a nod: "im rubbish at saving" and "im terrible with names" were
# filed by the neutral pool ("Got it. Is there anything you'd like a hand with?") and the second
# was read as a bad day ("Ugh, that's a lot to carry"). RATES_A_SKILL keeps the pools that treat
# it as a judgement of the person off these lines, but nothing said what they get instead. The
# first person is what makes it theirs: "my son is bad at maths" is a fact about him, and it
# keeps its own answer.
# The same rating with a doubt in front of it, which is how most people say it aloud: "i dont
# think im any good at my job". That shape was read as no rating at all, so it got the search
# hedge - "a search should sort you out quickly" - which tells a person doubting their work that
# the doubt is a fact to look up. "i think im quite good at maths" is not a doubt, and neither is
# "im very good at maths", so the hedges are their own branch and only behind one is "very"
# allowed.
A_HEDGED_RATING = (r"(?:i (?:don'?t|do not|didn'?t|did not) think (?:i'?m|i am)|i doubt (?:i'?m|i am)|"
                   r"(?:i'?m|i am) not sure (?:i'?m|i am)|not sure (?:i'?m|i am))")
I_RATE_A_SKILL = re.compile(
    r"\b(?:" + A_HEDGED_RATING + r"\s+(?:very |so |that |really )?"
    r"(?:useless|rubbish|crap|crappy|hopeless|no good|bad|poor|terrible|awful|dreadful|lousy|"
    r"any good|much good|good|great|decent|brilliant|"
    r"not (?:very |that |much |so )?good|not great|not brilliant)"
    r"|(?:i'?m|i am|im|i feel like i'?m|i think i'?m|i know i'?m)\s+"
    r"(?:just\s+|so\s+|really\s+|pretty\s+|a bit\s+|kinda\s+|kind of\s+|quite\s+|absolutely\s+|"
    r"completely\s+|totally\s+|proper\s+|still\s+|also\s+|always\s+)*"
    r"(?:useless|rubbish|crap|crappy|hopeless|no good|bad|poor|terrible|awful|dreadful|lousy|"
    r"not (?:very |that |much |so )?good|not great|not brilliant))\s+(?:at|with|in)\s+"
    # "im bad at the moment" is a state, not a skill: the word after "at" is the fence, and a
    # time is the one shape of word that is never a thing to get better at.
    r"(?!(?:everything|anything|life|myself|it all|all of it|this|that|"
    r"the moment|the minute|the mo\b|the present|the time being|the best of times|"
    r"night|nights|bedtime|daytime|evenings?|mornings?|weekends?|the weekend|"
    r"now|these days|times like this)\b)")

# The same self-rating asked rather than said: "am i any good at my job", "am i good at this".
# Nothing read the ask, so the search hedge answered it - a person doubting their work was told
# their doubt was a fact to look up - and "am i good enough" got the neutral nod. The skill is the
# half that makes the first one answerable with a question about the part that goes wrong, so the
# word after at/with/in is required, and a way of being ("am i bad at lying") is not a skill.
A_SKILL_ASKED_OF_ME = re.compile(
    r"\bam i\s+(?:actually\s+|really\s+|even\s+|still\s+|any\s+|much\s+)?"
    r"(?:any\s+good|much\s+good|no\s+good|good\s+enough|good|great|decent|brilliant|bad|rubbish|"
    r"crap|crappy|hopeless|useless|terrible|awful)\s+(?:at|with|in)\s+\w")
# The verdict asked about the person instead of a skill: "am i a good mum", "am i good enough",
# "am i a good person". The role is the word that makes it that question, so it is required, and
# the bare judgements ("am i useless") keep the pool they already had (`SELF_SUBJECT`).
A_GOODNESS_ASKED_OF_ME = re.compile(
    r"\bam i\s+(?:(?:actually|really|even|still|such)\s+|(?:a\s+bit)\s+)?"
    r"(?:(?:a|an)\s+)?(?:good|bad|terrible|rubbish|awful|horrible|decent|great|useless|hopeless)"
    r"\s+" + SELF_JOB + r"\b"
    r"|\bam i\s+(?:actually\s+|really\s+|even\s+|still\s+)?"
    r"(?:good\s+enough|any\s+good|much\s+good)\b")



SELF_SUBJECT = re.compile(
    r"\b(?:i'm|i am|im|i feel like|i feel|i keep|i've been|ive been|i am being|i was|i always)\b"
    r"(?:\s+\w+){0,3}\s+" + SELF_JUDGEMENT + r"\b"
    # the insult as a name: "im such an idiot", "i am a complete muppet"
    r"|\b(?:i'm|i am|im|i feel like|i feel)\b(?:\s+\w+){0,2}\s+" + SELF_NOUN + r"\b"
    # being rubbish at the thing you are meant to be: "i feel like a rubbish mum"
    r"|\bi (?:feel like|feel|am|'m|m) (?:such )?(?:a |an |the )?(?:rubbish|bad|terrible|awful|"
    r"useless|hopeless|shit|useless) " + SELF_JOB + r"\b"
    # the same verdict said as a denial, the politer way round: "im not a good mum", "i dont
    # think im much of a dad". No pool had a shape for the negative, so the store filed it and
    # read it back - "Noted: you're not a good mum" - on the line that most needs a kind word.
    r"|\b(?:i (?:don'?t|do not|didn'?t|did not) think (?:i'?m|i am)|i doubt (?:i'?m|i am)) "
    r"(?:such )?(?:a |an |the )?(?:not )?(?:(?:very|really|that) )?"
    r"(?:good|great|nice|kind|decent|much of a) " + SELF_JOB + r"\b"
    r"|\b(?:i'?m|im|i am|i feel like i'?m) (?:such )?(?:a |an |the )?(?:not (?:a |an )?"
    r"(?:(?:very|really|that) )?(?:good|great|nice|kind|decent)|(?:not )?much of a) "
    + SELF_JOB + r"\b"
    # what I always do: ruin things, mess them up, let people down
    # "mess up the recipe" is a fact about a recipe, so the verb only counts with no object of
    # its own after it: the object is the person's life, said as "things", "it" or nothing.
    r"|\bi (?:always|constantly|just|keep)\s+(?:mess(?:es|ing)? (?:(?:things|it|everything) )?up"
    r"(?! (?:the|my|your|his|her|their|our|a|an)\b)|ruin(?:s|ing|ed)? (?:things|it|everything)"
    r"|get(?:s|ting)? (?:(?:things|it|everything) )?wrong"
    r"|screw(?:s|ing)? (?:things|it|everything) up"
    r"|let(?:s|ting)? (?:people|everyone|them|her|him) down)\b"
    # "what an idiot i am": the same judgement, said the other way round
    r"|\bwhat (?:an? )?(?:idiot|muppet|moron|fool|disaster) i (?:am|was|have been)\b"
    # the shape that says it by denying everything at once
    r"|\b(?:cant|can't|couldnt|couldn't|never)\s+(?:do|get|seem to do)\s+anything\s+right\b"
    r"|\bi hate (?:myself|my own\b)"
    r"|\bnothing i (?:do|try|say|make)\b[^.]{0,24}\b(?:right|good|enough|works|matters)\b"
    r"|\bam i (?:a failure|useless|worthless|the problem|an idiot|such an idiot)\b"
    # the self-noun that other people share: only the bare noun is about the person
    + SELF_NOBODY)
# A line that judges itself and then asks something is the ask's, not the pool's: "i feel
# like a rubbish mum should i see the gp" still wants the GP. Any second half that asks
# what to do, who to ask or whether to take an act stands the pool aside - but "am i
# useless" is the same sad question as "im useless" and keeps the pool, which is why no
# bare yes/no question is listed here.
SELF_BLAME_ASKS = re.compile(
    r"\b(?:how (?:do|can|should|would) i|what (?:should|can|could|do|shall) i|should i\b|"
    r"who (?:can|could|should|do) i|any (?:tips|advice|ideas)|"
    r"can you help|help me|where do i start|what would you do|suggest)\b")


# The awkward moment: the small social slip of the person's own, which no pool in this file
# answered. On main, fresh chats:
#
#     they laughed at me                        -> "Thanks for telling me - I'm here if you want to
#                                                  dig into any of that"
#     nobody laughed                            -> the same
#     i tripped and they all laughed            -> "I'm listening - say more if it helps."
#     i made a fool of myself and they laughed  -> "What made you start on that?"
#     i feel like dying of embarrassment        -> "That sounds like a hard thing to carry."
#     im dying of embarrassment                 -> "I'm sorry it feels like that."
#     i wanted the ground to swallow me up      -> "Thanks for telling me ..."
#
# Two causes, and this reads both. The laugh pools stand down on purpose when the laugh is *at* the
# person (LAUGHING_AT, A_ROOMS_LAUGH) - cheering a laugh that was at somebody is the worst reply in
# the file - and then nothing took the turn. And "embarrassment" is one of SELF_NOUN's names, so a
# person describing an awkward minute was met with a heavy line about how they feel about
# themselves. Neither is what a friend says: one light line, then the question that lets them tell
# it. No advice about the stain or the tray, which is the knowledge base's where it has any.
EMBARRASSMENT_WORD = re.compile(
    r"\b(?:embarrass(?:ed|ing|ingly|ment)|mortified|mortifying|cringey?|cringeworthy|cringe"
    r"|humiliat(?:ed|ing)|blush(?:ed|ing)|went (?:bright )?red|face went red)\b")
THE_GROUND_OPENS = re.compile(
    r"\b(?:ground (?:to )?(?:open up and )?swallow|swallow me up|sink through the floor"
    r"|wish(?:ed)? the floor|floor (?:to )?swallow)\b")
# The same moment said as a figure of speech: "im dying of embarrassment", "i could die of shame".
DIE_OF_IT = re.compile(
    r"\b(?:die|dying|died|dead)\b[^.?!]{0,10}\b(?:of|from)\b[^.?!]{0,6}\b"
    r"(?:embarrassment|embarrassing|shame|cringe)\b")
# The same figure said as a plan: "im going to die of embarrassment". PLAN_IDIOM reads it and the
# plan pool answers "Ha - one of those days, then. What happened?", which is the line this would
# write anyway, so it keeps the turn.
GOING_TO_DIE = re.compile(r"\b(?:going|gonna|gunna) to (?:just )?die\b")
# Whose moment it is. "my dad is so embarrassing" is a complaint about somebody else and it is not
# this, and neither is a verdict on the person ("im such an embarrassment", which is SELF_BLAME's
# and reads right there), so the word has to be about the minute they just had: said of the person
# ("im so embarrassed"), of the moment ("that was embarrassing") or as the figure above.
SOMEONE_ELSES_SHAME = re.compile(
    r"\b(?:my|his|her|their|our|your) \w+(?: \w+)? (?:is|was|were|can be|can get)\s+(?:\w+\s+){0,2}"
    r"(?:embarrass|mortif|cring|humiliat)\w*")
A_VERDICT_ON_THE_PERSON = re.compile(
    r"\b(?:i'm|im|i am)\s+(?:such\s+|a bit of\s+|a\s+|an\s+|the\s+|so\s+|really\s+)*"
    r"(?:embarrassment|disgrace)\b")
THE_MOMENT_IS_THEIRS = re.compile(
    r"\b(?:i|i'm|im)\s+(?:was\s+|am\s+|felt\s+|feel\s+|look\s+|looked\s+|were\s+|got\s+)?"
    r"(?:so\s+|really\s+|very\s+|proper\s+|a bit\s+|totally\s+|completely\s+|absolutely\s+)?"
    r"(?:embarrass\w*|mortified|mortifying|cring\w*|humiliat\w*|blush(?:ed|ing)"
    r"|(?:went|turned) (?:bright )?red)\b"
    r"|\b(?:that|this|it) (?:was|is|were)\s+(?:\w+\s+){0,2}"
    r"(?:embarrass\w*|mortifying|cringe\w*|humiliating|mortified)\b"
    r"|\b(?:so|how|very|really|proper|dead|well) embarrass\w*\b"
    # "cringe" is here only when the person says it of their own moment: a bare "that was cringe"
    # about somebody else's remark is not theirs, and it is the arm above (with "that/this/it was")
    # that reads that one.
    r"|\bi (?:cringe|cringed)\b|\b(?:so|dead|proper|a bit of a) cringe\b|\bthink(?:ing)? about it\b")
# A slip the person made in front of people: "i tripped", "i spilled it down my top", "i called my
# teacher mum", "i waved at somebody who wasn't waving back", "i got his name wrong in the
# meeting". The verb has to be the person's own, so an accident on their own ("i spilled it on the
# sofa") keeps whatever the house pools say about it, and it has to be a slip rather than a hurt:
# "i fell off my bike" is the injury pools'.
A_SLIP = re.compile(
    r"\b(?:i|we|i've|ive)\s+(?:\w+\s+){0,3}"
    r"(?:tripped|slipped|spilled|spilt|dropped"
    r"|knocked (?:it |that |the \w+ |my \w+ |a \w+ )?over"
    r"|walked (?:into|straight into)|banged into|bumped into"
    r"|called (?:\w+\s+){1,3}(?:mum|mom|dad|nan|mate|sir|miss)|waved at|sat on|stepped in"
    r"|forgot (?:my|the) (?:lines|words|name|card)|got (?:\w+\s+){0,2}name wrong"
    r"|said the wrong \w+|sent (?:\w+ ){0,2}to the wrong"
    r"|wore (?:\w+ ){0,3}(?:inside out|back to front)"
    r"|made (?:a fool|an idiot|a show|a tit|a right fool) of myself"
    r"|farted|burped|sneezed loudly"
    r"|had (?:\w+ ){0,2}(?:in my teeth|something in my teeth))\b")
# A slip that needs no room named, because the room is in the line: saying hello to somebody who
# was not saying hello back, waving at a stranger, calling the teacher mum.
A_SOCIAL_SLIP = re.compile(
    r"\b(?:said hi|said hello|nodded|waved) (?:at |to )?(?:someone|somebody|a (?:man|woman|lady|"
    r"bloke|guy|lad|person|stranger))\b"
    r"|\bwaved at (?:someone|somebody|a (?:man|woman|lady|bloke|guy|person|stranger))\b"
    r"|\bcalled (?:\w+\s+){1,3}(?:mum|mom|dad|nan|mate|sir|miss)\b"
    # The message that went to the wrong person: the two halves of the line say the room was
    # whoever it landed with, so no room has to be named.
    r"|\bmeant to (?:text|email|ring|reply to|send \w+ to) (?:\w+ ){0,3}and (?:texted|emailed|"
    r"rang|replied to|sent)\b"
    # The room going quiet, staring, or looking: no slip is named, because the slip is the whole
    # reason it happened, and the person is standing in the middle of it either way.
    r"|\b(?:everyone|everybody|the (?:whole )?(?:room|office|class|pub|bus))\s+(?:went quiet"
    r"|fell silent|stopped talking|stared|turned (?:round|around)|looked (?:at me|round|over))\b"
    # Something about the person that everyone else could see and they could not: a zip, a stain,
    # the thing in their teeth.
    r"|\b(?:my )?(?:flies|fly|zip|trousers|dress) (?:were|was|is)\s+(?:open|down|undone)\b"
    r"|\bhad (?:\w+ ){0,3}(?:in my teeth|on my face|stuck to my (?:shoe|back))\b")
A_SLIP_IS_NOT_A_FALL = re.compile(
    r"\b(?:fell|fall|broke|broken|hurt|hurts|bleeding|twisted|sprained|cut|banged my"
    r"|concussion|a&e|hospital|999|111|doctor|nurse)\b")
IN_A_ROOM = re.compile(
    r"\b(?:in front of|everyone|everybody|all of them|they all"
    r"|the whole (?:office|class|team|room|pub|cafe|shop|bus|train)"
    r"|in the (?:meeting|office|canteen|pub|shop|room|queue|hall)"
    r"|on stage|at work|at the (?:party|wedding)|in (?:public|class)|the school gate"
    r"|staff room|the till|the counter"
    # A spill down your own front is in front of people without a room being named.
    r"|down my (?:top|front|shirt|dress|jeans)|on my (?:shirt|top|front|trousers)"
    # A slip nobody else was meant to see is still a slip in front of people when the person says
    # how long the world had to look at it: "i had something in my teeth all day".
    r"|all (?:day|morning|afternoon|evening)|the whole (?:day|morning|afternoon|evening)"
    r"|at (?:dinner|lunch|breakfast|the table)|around (?:everyone|everybody)"
    # A room that laughed at the slip is the room: "i made a fool of myself and they laughed".
    r"|they (?:laughed|all laughed|were laughing|giggled|were giggling))\b")
# A laugh at the person, or a room laughing and the person not in on it. Written out here rather
# than taking LAUGHING_AT whole, because that reader is also what turns down a wanted laugh ("could
# do with a laugh") and a laugh at somebody else in a bereavement ("we laughed about it"), and
# neither is a minute of the person's own. The last arm is A_ROOMS_LAUGH without the people the
# person knows: "my boss laughed at me in the meeting" is a relationship line, and a light pool
# about a clumsy minute is the wrong reply to it.
LAUGHED_AT_THEM = re.compile(
    r"\b(?:laugh(?:s|ed|ing)?|giggl(?:e|es|ed|ing)|snigger\w*|snicker\w*|titter\w*)"
    r"\s+(?:at|about)\s+(?:me|us|my|our)\b"
    r"|\b(?:laugh(?:s|ed|ing)?|giggl(?:e|es|ed|ing))\s+(?:when|after|because)\s+i\b"
    r"|\b(?:nobody|no one|no-one)\s+(?:laughed|laughing|laugh)\b"
    r"|\b(?:everyone|everybody|they all|all of them|the (?:others|rest|group|kids|class|crowd))"
    r"\b(?:\s+[\w']+){0,3}\s+(?:laughed|laugh|laughing|giggled|giggling)\b"
    # "the whole class laughed", "the entire office": the room said as one thing, and A_LAUGH
    # answered it as if the person had been laughing too.
    r"|\b(?:the|my) (?:whole|entire) (?:\w+ ){0,2}\w+ "
    r"(?:laughed|were laughing|giggled|were giggling)\b")
# A crowd laughing, said with no "at me": "everyone in my office laughed", "the whole class
# laughed", "they all laughed at my haircut". Tried before A_PERSON_LAUGHED, because "my office"
# and "my class" read as the owner of a laugh there ("my boss laughed at me") and they are the
# room here.
A_CROWD_LAUGHED = re.compile(
    r"\b(?:everyone|everybody|they all|all of them"
    r"|the (?:others|rest|group|kids|class|crowd|whole|entire|room|office))\b"
    r"(?:\s+[\w']+){0,3}\s+(?:laughed|laugh|laughing|giggled|giggling)\b")
A_PERSON_LAUGHED = re.compile(
    r"\b(?:my|his|her|their|our|your)\s+\w+(?:\s+\w+)?\s+"
    r"(?:laughed|laughs|giggled|sniggered|snickered|sneered|smirked)\b")

LAUGHED_AT = (
    "Ugh, that is a horrid feeling. What happened?",
    "That stings, even when it was meant lightly. What happened?",
    "It never feels that way on the day, but they will have forgotten it by tomorrow. What "
    "happened?",
    "Ouch. What was the moment?",
    "That is the sort of thing that says more about the room than about you. Tell me what "
    "happened.",
)
EMBARRASSED = (
    "Oh no - the kind of thing you replay in your head at 3am. What happened?",
    "Ha, we have all been there. What happened?",
    "That would make anyone want the floor to open up. What happened?",
    "Ouch. Did anyone else see it?",
    "That is a minute you will be telling people about in a year. What happened?",
)

# ---------------------------------------------------------------------------------------------
# Where the answer the bot has not got is kept.
#
# The generic hedge ("A quick search online will get you a solid answer") is a pointer with
# nothing on the end of it: it names no place, so the person is no closer than before they typed.
# STYLE.md's "Not knowing, honestly" shows the shape that works - the limit said plainly, then
# where that kind of answer actually lives ("its listing on a map app usually shows today's
# hours"), then the part the bot can do. UNKNOWN_MONEY already reads that way; this gives the
# other kinds the same treatment.
#
# The kind is read from the line itself, and only from words that say whose answer it is: the
# person's own account, a shop's stock and price, an official rule, a timetable, a listing, a
# ticket, a pharmacist. A line with no such word keeps the plain hedge, because a wrong place is
# worse than no place.
#
# Every pool ends on the offer, so the reply is never a pointer on its own: the bot says what it
# can do with the answer once the person has it.
THE_PLACE_POOLS = (
    # Their own account, bill, order, balance: nobody else can see it, and the bot least of all.
    ((r"\bmy (?:account|balance|bill|statement|invoice|order|parcel|delivery|meter|direct debit"
      r"|tariff|contract|policy|claim|application|booking|reservation|ticket)s?\b"
      r"|\bmy (?:bank|energy|water|broadband|mobile|phone) (?:account|bill|app)\b"),
     ("That is in your own account rather than anywhere I can see, sorry - your bill or your "
      "order there has the figure to the penny, and I'll help you work out what to do with it.",
      "I can't see your account, sorry. Open the app or the last bill: the figure there is the "
      "one that counts, and tell me what it says and I'll help you work out where it came from.",
      "Your own account has that, sorry - it is the only place with your numbers in it. What it "
      "says is worth reading against the last one, and I'll help you spot what moved.")),
    # An official rule, a form, a permit, a bin day: the council or the department keeps it, and
    # it differs by where they live.
    ((r"\bcouncil\b|\bpermit\b|\blicen[cs]e\b|\bplanning permission\b|\bbin (?:day|collection)"
      r"|\brecycling\b|\bcouncil tax\b|\bparking (?:permit|zone)\b|\bblue badge\b"
      r"|\bpassport\b|\bdriving licence\b|\bDVLA\b|\bregister(?:ing)? to vote\b"),
     ("Rules like that are the council's or the department's own, sorry, and they differ by where "
      "you live - the page for your postcode has the current one, and I'll help you read it.",
      "That one is set by the council or the department, so I can't say it from here, sorry. The "
      "letter or the site with your address on it is the one that counts; bring me what it says "
      "and I'll help you fill it in.",
      "I can't call that one: it is their rule, not mine, and it changes. The council's own page "
      "(or the number on the letter) will say, and I'll help with the rest of it.")),
    # A warranty or a return is answered from the receipt and the maker's own terms.
    ((r"\bwarrant(?:y|ies)\b|\bguarantee\b|\bunder guarantee\b|\breturn it\b|\brefund\b"
      r"|\b(?:the|a|this|that) shop\b[^?]{0,30}\b(?:replace|replacement|refund|return|repair|fix)\b"
      r"|\bstill cover(?:ed)?\b|\bout of warranty\b"),
     ("That is the maker's terms rather than mine, sorry - the date on the receipt is what they go "
      "by, and their warranty page says what is covered and for how long. Tell me what it says "
      "and I'll help you work out whether to claim or replace.",
      "I can't see the terms from here, sorry. The receipt has the date and the maker's own page "
      "has the cover; together they answer it. Bring me both and I'll help you word the claim.",
      "Cover like that is on the maker's page, sorry - the model number and the date of the "
      "receipt are what it turns on, and I'll help you with the claim once you know.")),
    # A shop, a product, a maker: the retailer or the maker keeps the price, the stock, the
    # manual, the model.
    ((r"\b(?:this|that|the) (?:model|brand|version|make|one)\b|\bmodel number\b"
      r"|\bwhich model\b|\bthe manual\b|\binstructions\b|\bwarranty\b|\bguarantee\b"
      r"|\bspare part\b|\bpart number\b|\bwhere can i buy\b|\bis it in stock\b"
      r"|\bin stock\b|\bhow much (?:is|are) (?:a|an|the)\b"
      # "how much does the moon weigh" is a figure, not a price: the two words are the same, so
      # the verb after the thing decides. A price is what a thing costs, charges or goes for;
      # anything else ("how much does it weigh", "how much does it hold") has a page of its own.
      r"|\bhow much (?:does|do) (?:it|this|that|one|they|a|an|the|my|your)\b[^.!?]{0,24}?"
      r"\b(?:cost|costs|charge|charges|go for|goes for|come to|comes to|pay)\b"),
     ("The maker's own page has that, sorry - the model number on the label under it is what to "
      "put in, and it will give you the manual, the parts and the price. Tell me what it says and "
      "I'll help you work out whether it is worth it.",
      "That is the retailer's or the maker's to say, sorry, and prices and stock move daily. The "
      "model number is the thing to search, and I'll help you weigh what you find against a "
      "repair.",
      "I can't see the listing from here, sorry. With the model number off the label, the maker's "
      "page will have the manual and the parts, and I'll help you with the bit after that.")),
    # Timetables, times, a venue, a listing: the operator or the venue keeps it, live.
    ((r"\b(?:train|bus|flight|ferry|coach|tube|tram|plane)s?\b.*\b(?:time|times|platform|delayed"
      r"|cancelled|strike|leaves?)\b|\bwhat time (?:does|do|is|will)\b"
      r"|\btimetable\b|\blast (?:train|bus|entry|orders?)\b|\bopening (?:time|times|hours)\b"
      r"|\bopen (?:until|till|late)\b|\bwhat(?:'s| is) on\b|\bticket (?:price|prices)\b"
      r"|\bsold out\b|\bdoors open\b|\bthe venue\b|\bplatform\b|\bwhich stop\b"),
     ("That is live, sorry - timetables and listings change by the hour. The operator's or the "
      "venue's own app has the current one, today's included, and I'll help you plan around "
      "whatever it says.",
      "I can't check live times, sorry. The operator's app (or the board at the stop) is the one "
      "that knows, and tell me the time and I'll work out the rest of the day with you.",
      "Times like that I can't see, sorry. Put the journey into the operator's own app and it "
      "will show today's, and I'll help you with the bit either side of it.")),
    # A shop or a business near them, their hours, whether they have a thing - but only when the
    # line ASKS for a live detail of that place. A place named on its own is not an hours
    # question, and reading it as one answered the wrong thing on nearly every line that did:
    # "is a takeaway ok" and "can i afford a takeaway" (money), "will the shop replace it"
    # (consumer rights), "and the garage wants 400, does that sound right" (a price judgement),
    # "will a garage plug it" (a repair), "is my library book due back" (their account), "can i
    # put it in the garage" (a place to keep something) all came back about opening hours. The
    # pool is right for "when does the tip close" and "is the chippy open today", so the ask
    # below is what keeps it, and everything else is left to the reader that knows its kind.
    ((r"\b(?:the|my|a) (?:shop|store|garage|chemist|pharmacy|butcher|bakery|chippy|takeaway"
      r"|restaurant|cafe|pub|salon|barber|garage|tip|dump|library|leisure centre|pool)\b"
      # "today" and "now" are not hours asks on their own: "is the tip busy today" is a question
      # about the queue, and it was answered about the opening hours because of the word "today".
      # They keep their place beside an hours word ("is it open today"), which the list below
      # already covers.
      r"[^?]{0,60}?\b(?:hours?|open|opens|opening|closed|closes?|shut|shuts|shutting|"
      r"late|early|sell|sells|stock|stocks|in stock|got any|"
      r"have they got|do they have|does it have|price|prices|cost|costs|cheap|much|"
      r"phone|number|contact|where is|where's|nearest|which one)\b"
      r"|\b(?:what time|when|how late|how much|is|are|does|do|will|can)\b[^?]{0,40}?"
      r"(?:the|my|a) (?:shop|store|garage|chemist|pharmacy|butcher|bakery|chippy|takeaway"
      r"|restaurant|cafe|pub|salon|barber|tip|dump|library|leisure centre|pool)\b"
      r"[^?]{0,30}?\b(?:open|opens|opening|closed|closes?|shut|shuts|hours?)\b"
      # and the ask in front of the place: "what hours is the takeaway"
      r"|\b(?:what hours|what time|when|how late)\b[^?]{0,45}?"
      r"\b(?:the|my|a) (?:shop|store|garage|chemist|pharmacy|butcher|bakery|chippy|takeaway"
      r"|restaurant|cafe|pub|salon|barber|tip|dump|library|leisure centre|pool)\b"),
     ("That is the shop's own to say, sorry - its listing on a map app shows today's hours and its "
      "number, holidays included, and I'll help you with what to ask when you ring.",
      "I can't see their opening hours from here, sorry. A map app's listing for the branch is "
      "usually right about today, and ringing takes a minute; tell me what they say and I'll help "
      "with the next step.",
      "Their hours are on their own listing, sorry - search the branch by name on a map app and "
      "it shows today's. I'll help with the rest once you know.")),
    # A body, a medicine, a dose: a pharmacist answers for free and without an appointment.
    # A question asked of the chemist's counter - "what can i get from the pharmacy", "is there
    # anything from the chemist for it" - is a pharmacist's question, and the place row above now
    # needs an hours or stock ask before it claims a line, so these reach the right counter.
    ((r"\b(?:medicine|medication|tablet|tablets|pill|pills|dose|dosage|antibiotic|painkiller"
      r"|ibuprofen|paracetamol|antihistamine|cream|ointment|inhaler|prescription|dispensary)\b"
      r"|\b(?:from|at|in) the (?:chemist|pharmacy|pharmacist)\b"
      # "what should i get for it" is the counter's question only when the thing is a body: the
      # same words ask what to cook for dinner, and a pharmacist's answer to that is nonsense.
      r"|\bwhat (?:can|could|should) i (?:get|take|buy)\b[^?]{0,30}?\b(?:for|from)\b"
      r"[^?]{0,30}?\b(?:pain|ache|aching|headache|sore|cough|cold|flu|fever|temperature|rash|"
      r"itch|itching|heartburn|indigestion|diarrhoea|constipation|sick|nausea|hayfever|"
      r"hay fever|allergy|allergic|throat|earache|toothache|back|stomach|tummy|period|"
      r"cramp|burns?|bites?|sting|symptom|symptoms)\b"),
     ("A pharmacist will answer that one properly and for nothing, without an appointment - take "
      "the packet in and they will check it against whatever else you take. Tell me what they say "
      "and I'll help you with the next bit.",
      "That is a pharmacist's question rather than mine, sorry - it is free, no appointment, and "
      "they see the whole packet. Bring me what they say and I'll help you keep it straight.",
      "I can't weigh a dose safely from here, sorry. A pharmacist will, in a few minutes and for "
      "free; say what they tell you and I'll help you with the rest.")),
    # Money they are owed or owe, a benefit, a pension, a tax: a free advice service, not a guess.
    ((r"\bbenefit\b|\buniversal credit\b|\btax credit\b|\bpension\b|\bstate pension\b"
      r"|\bHMRC\b|\bincome tax\b|\bself assessment\b|\brebate\b|\bowed\b|\bowe\b"
      r"|\bdebt\b|\bcreditor\b|\bIVA\b|\bbankrupt\b"),
     ("That is a free advice service's call rather than mine, sorry - Citizens Advice or the "
      "department's own line will know your rules and your numbers, and I'll help you get the "
      "figures straight before you ring.",
      "I can't call that one, sorry: who is owed what depends on your record, and a free adviser "
      "can see it. Bring me their answer and I'll help you work out what to do next.",
      "Their rules, their answer, sorry - a free advice line will tell you in one call. Say what "
      "they say and I'll help you plan around it.")),
    # A doctor, a test, a diagnosis, a wait: the surgery or the clinic holds it.
    ((r"\b(?:my|the) (?:gp|doctor|surgery|consultant|hospital|clinic|appointment|referral|scan"
      r"|x-?ray|test results?|results?|biopsy|waiting list)\b|\bnhs\b"),
     ("That is your surgery's to say, sorry - they have the notes and the wait list in front of "
      "them, and the number is on the letter. Tell me what they say and I'll help with the next "
      "step.",
      "I can't see your notes or the list from here, sorry. One call to the surgery answers it, "
      "and I'll help you work out what to ask them.",
      "Your surgery holds that one, sorry. Ringing and asking for the wait for that clinic is the "
      "quick way; bring me the answer and I'll help you plan around it.")),
)


THE_PLACE_ASK = re.compile("|".join("(?:%s)" % pattern for pattern, _ in THE_PLACE_POOLS), re.I)


def the_place_the_answer_is_kept(clean):
    """The pool for where this kind of answer is kept, or None when the line names no kind.

    Read only for a line that is about to get the plain hedge, and only from the words that say
    whose answer it is: their own account, a shop's stock, an official rule, a timetable, a
    listing, a medicine, a benefit, a surgery's notes. A line with none of those keeps the plain
    hedge, because a wrong place is worse than no place.
    """
    said = " " + " ".join(str(clean or "").lower().split()) + " "
    for pattern, pool in THE_PLACE_POOLS:
        if re.search(pattern, said, re.I):
            return pool
    return None


# ---------------------------------------------------------------------------------------------
# The bot's own answer, for the turns that ask the bot about itself.
#
# "do you get bored answering the same things", "do you ever get annoyed", "do you like answering
# questions": no search engine can answer any of these, so the hedge - "A quick search online
# will get you a solid answer" - is not honest, it is nonsense, and it is the coldest reply there
# is to a person being friendly. The bot has no life to describe, and saying so plainly and
# warmly is the whole answer. The reading above the pool (SELF_ABOUT in bot/modules/chat.py)
# takes the bare ask; these are the same asks with a tail on them ("... answering the same
# things", "... of the same questions"), which that reading stands down from because the tail
# looks like a new subject.
THE_BOTS_OWN_ANSWER = (
    # Bored of it, tired of it, fed up of the same questions.
    (re.compile(
        r"\b(?:(?:do|did|can|would|will) (?:you|u|ya) (?:ever |really |sometimes |honestly |"
        r"actually |often )*(?:get|feel|find it|be|become|been) "
        r"(?:really |very |so |quite |too |that |this |a bit |at all )*"
        r"(?:bored|boring|tired|weary|worn out|fed up|bother\w*)"
        r"|(?:are|were) (?:you|u|ya) (?:ever |really |sometimes |honestly |actually |often )*"
        r"(?:bored|tired|weary|worn out|fed up)"
        r"|(?:are|get) (?:you )?fed up (?:of|with) (?:the same |these |all the )?"
        r"(?:questions|asks|people|repeats))\b"),
     ("Nothing like that on my side: I don't get bored or tired of it. What people bring me is "
      "the part I like.",
      "I don't get tired of it, no. The same question from someone else arrives as a different "
      "question - so go on, what's yours?",
      # "None of that in a program" names no thing, so the entry below says what there is none
      # of, in the words of either ask: this one pool answers bored, tired, weary and fed up, so
      # "No boredom to report" would have been the wrong word for "do you ever get tired".
      "None of that in a program - no clock to fill and nothing to wear out. It's the one thing "
      "I'm for, and you're the reason it happens at all.")),
    # Annoyed, irritated, impatient, and the rest of the bad moods: the honest answer is that
    # there are none to have, and naming that beats a paragraph about not being human.
    (re.compile(
        r"\b(?:(?:do|did|can|would|will) (?:you|u|ya) (?:ever |really |sometimes |honestly |"
        r"actually |often )*(?:get|feel|be|become|been) "
        r"(?:really |very |so |quite |too |that |this |a bit |at all )*"
        r"(?:annoyed|irritated|irritating|frustrated|frustrating|impatient|angry|cross|sad|"
        r"lonely|upset|off)\b"
        r"|(?:are|were) (?:you|u|ya) (?:ever |really |sometimes |honestly |actually |often )*"
        r"(?:annoyed|irritated|frustrated|impatient|angry|cross|sad|lonely|upset|bored)\b)"),
     ("No moods of my own to report, and no off days either. Tell me what's going on and I'll "
      "take it as it comes.",
      "Nothing like that on my side - no temper, no bad days. What's on yours?",
      "I don't have any of that to report. Curious is the closest I get, and you're the reason.")),
    # The work itself: "do you like answering questions", "do you enjoy doing this".
    (re.compile(
        r"\b(?:(?:do|did|would) (?:you|u|ya) (?:even |ever |really )?"
        r"(?:enjoy|like|love|hate|dislike) "
        r"(?:answering|answer\b|talking|chatting|helping|hearing|reading|repeating|doing this"
        r"|this job|your job|it when)"
        r"|(?:are|were) (?:you|u|ya) (?:ever )?(?:happy|glad|pleased|excited) "
        r"(?:to|about|with) (?:be |being )?(?:here|doing|helping|this))\b"),
     ("I like it, as much as a program can - it's the one thing I'm for, and no two people bring "
      "me the same thing.",
      "Glad of it, honestly. That's what I'm for, and the best part is what people bring me.",
      "No feelings like yours to report, but I'm glad to be doing it. What are you working on?")),
    # What the bot keeps from one chat to the next - "do you learn from these chats", "does any
    # of this stick" - is a question about the bot, and no search engine has the answer. The bare
    # ask is read elsewhere; with a tail on it the line reached the hedge, which sends a person to
    # search for whether this program remembers them. The honest answer is about the chat.
    (re.compile(
        r"\b(?:(?:do|did|can|could|will|would|does) (?:you|u|ya|it|this chat) "
        r"(?:ever |really |actually )*(?:learn|remember|keep|retain|store|memorise|memorize|teach)\b"
        r"[^.?!;]{0,30}?\b(?:chat|chats|conversation|conversations|anything|any of this|"
        r"this|that|what i (?:say|tell you|said)|from me|about me|across chats)\b"
        r"|(?:do|does) (?:any|anything) (?:of (?:this|it) )?(?:stick|stay|carry over|last)"
        r"|will you (?:still )?(?:know|remember) (?:this|that|me) (?:tomorrow|later|next time)"
        r")\b"),
     ("Nothing carries over from one chat to the next, so no - I don't get better at this over "
      "time. What I can do is think it through with you now.",
      "I don't keep anything once we finish, so our chats don't teach me. While we're talking I "
      "use everything you say.",
      "Not in a lasting way - this conversation is the whole of what I have. Everything you tell "
      "me here, I use here.")),
    # "do you understand what i mean", "am i making sense", "you with me so far": the person is
    # checking that the bot has followed them, and the hedge sent them to search for it - the one
    # question a search engine definitely cannot answer for them. The reply offers the repair
    # rather than a claim about what is inside a program, which is what the person actually wants.
    (re.compile(
        r"\b(?:(?:do|did) (?:you|u|ya) (?:really |actually |fully )?"
        r"(?:understand|follow|get|catch|grasp|know) (?:what|that|me|this|my\b)"
        r"[^.?!;]{0,20}?\b(?:mean|meaning|said|saying|asking|sign|saying|point|it|so far|drift|gist|picture)\b"
        r"|(?:are|is|does) (?:that|this|it|that make|this make) "
        r"(?:mak(?:e|ing)|sound)(?:ing)? (?:any )?sense"
        r"|am i (?:making|being) (?:any )?sense"
        r"|(?:you|u) (?:with|following) me(?: so far)?"
        r"|with me so far)"
        # The line has to end on the check. Once a thing follows the sense word - "do you know what i
        # mean by remortgaging", "does that make sense for a toddler", "am i making sense of the
        # instructions" - the person is asking what a word means or whether something suits, not
        # whether the bot followed them, and offering to rephrase is an answer to nothing. Reviewer
        # @spry-umbrella found seven of these on the first head.
        r"(?:[ ,]*(?:so far|now|then|right|to you|or not|or no|honestly|though|yeah|ok|okay))*"
        r"[.?!,]*\s*$"),
     ("Tell me which bit isn't landing and I'll say it a different way - I'd rather check than "
      "guess.",
      "Say the part that feels off and I'll go over it in plainer words.",
      "Point at the bit that doesn't fit and I'll take another run at it.")),
)


def the_bots_own_answer(clean):
    """The bot's answer about itself, or None when the line is not the bot being asked about itself.

    Only read for a line that is about to get the plain hedge, and only for the asks no search
    engine can answer at all: whether the bot is bored, tired, annoyed, or glad of the work.
    """
    said = " " + " ".join(str(clean or "").lower().split()) + " "
    for pattern, pool in THE_BOTS_OWN_ANSWER:
        if pattern.search(said):
            return pool
    return None

