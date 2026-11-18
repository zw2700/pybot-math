"""The reply to an ordinary statement that says what the person means to do.

Most of the lines the bot cannot answer are not questions. Someone tells it they are thinking of
moving, that they mean to go back to college, that they want to start saving. The reply such a
line gets today comes from one pool that has to fit every statement at once ("Got it. Is there
anything you'd like a hand with?"), and a line that would fit any message is the failure
STYLE.md names. But a plan has a shape, and a friend answers the shape: not with a stock nod,
and not with a question about what it is doing (a thing that has gone wrong is
`bot/compose/trouble.py`'s), but with the part people forget - the first step, and what has been
in the way.

A plan is read from cues that say the person means to do something over time ("planning to",
"want to", "saving up", "applying for"), and from a "going to" or a "thinking of" whose next
word is a thing you plan ("going to move house", "thinking of moving") rather than a thing you
do now ("going to have a bath") or the object of a thought ("thinking about my mum"). A line
that asks something is left alone too, whatever else it says: "got any ideas for somewhere
warmer next year" is a request for ideas, and "should i move" is a doubt, not a plan.

The other half of the same family is a report: a statement about something that has already
happened ("the shop was shut", "the bus was late again", "i started a new job"). It is not a
question, so no module answers it; it is not a plan, so the above passes it; and it is not a
fault of theirs to troubleshoot (that is `bot/compose/trouble.py`). What is left for it today is
the same stocking pool ("Got it. Is there anything you'd like a hand with?"), and a friend
answers a report the way they answer a plan: by its shape, with the feeling it deserves - a small
setback is a nuisance, a thing that keeps happening is "again?", and something new that has
started is worth a question. The line is still left to the caller's own pools when it carries a
feeling, a loss or good news: those read better with the mood than with the shape.
"""
import re

from . import pick, trouble
from .fallback_data import A_THING_TAKEN
from ..memory import facts
from ..understanding.kinds import OTHER_PEOPLE
from ..understanding.normalize import without_leaders

# Something meant to happen over time: the cues that make a statement a plan, not a report.
# A date is not a plan. "next week is going to be busy" and "the anniversary is next month" say
# when something is, not what the person means to do, and a date on its own was the commonest
# false plan in the deck. So every cue below is a verb of intention, and a date only counts
# alongside one of them. The same goes for the going-to verbs: "get", "take", "stop" and "try"
# are things done now at least as often as things planned ("im going to get some sleep"), so
# they are out; what stays is the work a plan is made of.
PLAN = (
    "planning", "plan to", "planning to", "book a", "save up",
    "saving up", "saving for", "applying", "apply for",
)
# A booking is a thing done, not a thing ahead: a plan has to be ahead and unfinished, and
# "i booked a smear test" is neither (plain-finch, @salmon-barrel). It counts as a plan only when
# the line also names the bigger thing it is a step in - "i booked the venue for the wedding" -
# which is what makes it a step rather than an arrangement on the calendar.
BOOKED = re.compile(r"\bbook(?:ed|ing)\b")
# What makes a booking a step is that the thing booked is smaller than the thing it serves: a
# venue, a hall, a flight or the photographer are steps in a wedding or a honeymoon, while "we
# booked a trip to spain" or "ive booked the course" is the whole thing, done, with no first
# step left to be unsure about (warm-feather, #401).
STEP_NOUNS = frozenset((
    "venue", "venues", "hall", "reception", "caterer", "caterers", "band", "dj",
    "photographer", "tickets", "flights", "flight", "hotel", "room", "table", "minibus",
))
BIGGER_PLAN = frozenset((
    "wedding", "weddings", "venue", "honeymoon", "holiday", "trip", "course", "reception",
    "mortgage", "house", "move", "moving", "exam", "exams",
))
# Arrangements, not projects: "we are going to visit friends at the weekend" and "tomorrow im
# going to work from home" have a date and nothing to be unsure about, so "what's the bit you're
# least sure about?" answers a question nobody asked. "work" is a plan as the work itself
# ("going to work on my cv"), so it is read together with what follows it.
ARRANGEMENT = frozenset(("visit", "visiting", "visits"))
# "I'm going to have a bath" is not a plan with a first step; "I'm going to move house" is, and
# so is "i want to start saving" but not "i want to say something". So a going-to and a want-to
# count only when the next word is a thing you plan rather than something said or done now.
GOING_TO = ("going to ", "gonna ", "want to ", "wanting to ", "would like to ", "hoping to ",
            "thinking of ", "thinking about ")
PLANNED_VERBS = frozenset((
    "start", "move", "save", "buy", "learn", "book", "travel", "visit", "change",
    "quit", "sell", "apply", "build", "train", "study", "open", "join",
    "switch", "retrain", "volunteer", "emigrate", "adopt", "redecorate",
    "renovate", "downsize", "sort", "fix", "paint", "clear", "declutter", "budget",
    "insulate", "convert", "rent", "plant", "grow", "write",
))
# Never read as a plan: a death, an illness, an emergency, or a loss. "im going to the funeral
# next week" is a plan in form and a bereavement in fact, and the loss pool reads the whole line.
NOT_PLAIN = frozenset((
    "died", "dying", "dead", "death", "passed", "funeral", "buried", "miscarriage",
    "cancer", "tumour", "tumor", "diagnosis", "hospital", "icu", "hospice", "suicide",
    "overdose", "abuse", "beaten", "assaulted", "attacked", "emergency", "ambulance",
    "bleeding", "chest", "stroke", "seizure", "unconscious", "miscarried", "grieving",
    "miscarrying", "divorce", "custody",
    # the appointments nobody is cheered for booking: a termination, a cremation, a bed that is
    # not a holiday. "Sorted." on a booked termination reads as cheerful about the wrong thing,
    # and this set is the module's one home for that class.
    "abortion", "abortions", "termination", "terminations", "crematorium", "cremation",
    "cremations", "stillbirth", "ectopic", "coffin",
    # a plan that is really a medical appointment is a worry, not a project
    "scan", "appointment", "consultant", "clinic", "surgery", "gp", "doctor", "midwife",
    "chemo", "treatment", "results", "biopsy", "operation", "ward",
    # a smell or a leak that is a hazard is a safety line, never chit-chat about a fault
    "petrol", "gas", "gas leak", "fumes", "smoke", "smoking", "burning", "carbon",
    "monoxide", "sparks", "wiring", "fire",
    # a symptom is a health line: "i want to start running but i get out of breath" is about the
    # breathlessness, and "what's the first step you're unsure about?" answers the wrong half
    "breath", "breathless", "breathing", "breathlessly", "wheeze", "wheezing", "cough",
    "coughing", "dizzy", "faint", "palpitations", "pain", "hurts", "aching", "sore",
))
# "he would have been 60 next month" and "it would have been our anniversary next week" are a
# person remembering someone who has died, not a plan: a counterfactual, told in the past. Nothing
# here is ever a plan with a first step.
COUNTERFACTUAL = (
    "would have been", "would've been", "would have turned", "wouldve been",
    "should have been", "never got to", "if only",
)
# A date that marks someone who has died is not a plan either: "his birthday is next month" is a
# hard week for a bereaved person, and "our anniversary" the same. A party is still a plan, so
# this is the bare word, not the shape.
MARKED_DATE = frozenset(("anniversary", "birthday", "birthdays", "remembrance", "memorial"))
# A line about ending it, or about an emergency, is never a plan with a first step.
CRISIS = (
    "want to die", "wanna die", "kill myself", "end it all", "end my life", "no point",
    "hurt myself", "self harm", "not worth living", "better off dead", "be here anymore",
    "dont want to be here", "don't want to be here", "dont want to wake up",
    "better off without me", "no way out", "tired of living", "cant go on", "overdosing",
)

# The line is really an ask, whatever kind the engine read: "got any ideas for somewhere warmer
# next year" mentions a plan, but the person wants suggestions, and the honest pool answers that.
ASKS = frozenset((
    "what", "whats", "which", "why", "how", "when", "where", "who", "whos", "ideas", "idea",
    "suggest", "suggestions", "recommend", "advice", "tips", "anyone", "anybody", "shout",
))
# A line that is unsure of its own plan is not a plan: "i dont know if i want to stay with him"
# needs a listening reply, not a first-step question.
DOUBT = (
    "dont know", "don't know", "not sure", "unsure", "whether", "if i", "should i",
    "no idea", "in two minds", "not certain",
    # a plan somebody does not want is not a plan: "i dont want to go to work tomorrow"
    "dont want", "don't want", "do not want", "dont fancy", "don't fancy",
    # "i keep thinking about leaving my husband" is the biggest thing in their life, not a
    # project with a first step, and "i keep planning things i never do" is a complaint about
    # planning rather than a plan.
    "leaving my husband", "leaving my wife", "leaving my partner", "leave my husband",
    "leave my wife", "leave my partner", "keep thinking about leaving", "thinking of leaving",
    "leaving him", "leaving her", "walking out on", "keep planning", "always planning",
    "never do", "never follow through", "things i never",
)
# A line that already names what is in the way must not be asked what is in the way: "i want to
# start saving but ive never had a budget" has answered that. Those lines get a phrasing that
# presumes nothing, instead of the two that ask about a barrier.
BARRIER = (
    "but", "except", "only", "never", "dont have", "don't have", "havent got",
    "haven't got", "cant", "can't", "no money", "no time", "too late", "already tried",
)
# The two of the four that do not presume the person has hit something.
PLAN_REPLIES_PLAIN = (
    "Good. What's the first step you're unsure about?",
    "Sounds like a good plan. What's the bit you're least sure about?",
)

PLAN_REPLIES = (
    "Good. What's the first step you're unsure about?",
    "Nice — worth doing properly. What would you want sorted out first?",
    "Worth deciding what the first step is, and what you'd count as done.",
    "Sounds like a good plan. What's the bit you're least sure about?",
)


# --- a want somebody else has, said by the person looking after them ---------------------------
# "my son wants a tattoo", "my daughter wants to leave school at 16", "my dad wants a scooter at
# 78": the wanting is theirs and the asking is the person's, so the line is a request for help
# with it and the reply is about what it would take. Every one of these lines was filed back to
# them instead ("Noted: your son wants a tattoo."), which names the thing and leaves them nowhere
# to start. The same want in the first person already gets a reply - "i want a motorbike" gets
# "What kind of motorbike do you usually go for?" - so the shape is not new, only whose it is.
#
# The readers below take the want only when somebody the person looks after is named as the one
# wanting it. A want they are told about rather than asked about ("my boss wants me to work
# saturday") is not this: nobody is asking for help with a shift. And a want said with "me" after
# it is a request made *to* the person ("my mum wants me to visit"), which is answered about the
# visit, not about the wanting.
DEPENDANT = frozenset("""
son daughter child children kid kids toddler teenager teen lad boy girl baby grandson
stepson stepdaughter granddaughter mum mom mother father dad wife husband partner grandchild
nephew niece
""".split())
DEPENDANT_WANT = re.compile(
    r"\b(?:my|our|his|her|their)\s+(?:" + "|".join(sorted(DEPENDANT)) + r")\b[^.!?]*?\b(?:"
    r"wants?|wanted|needs?|would\s+like|would\s+love|is\s+desperate\s+for|keeps\s+asking\s+for|"
    r"is\s+asking\s+for)\b", re.I)
# A want aimed at the person themselves, which is a request to them rather than a thing to price.
ASKED_OF_THE_PERSON = re.compile(r"\b(?:wants?|needs?|would\s+like)\s+(?:me|us)\b", re.I)
# "My daughter wants to be a boy" is not a thing to price, and neither is "my son wants to be a
# footballer": `wants to be` is a wish about who somebody is, so "price it and check the rules" is
# not a wrong answer to one of those but a glib one, and glib is worse. A want that names an
# activity - "wants to leave school", "wants to get a tattoo" - is a thing with a first step.
WANTS_TO_BE = re.compile(r"\bwants?\s+to\s+be\b", re.I)
# A weapon is not a purchase to price now and think about later - the reply has to weigh why the
# want is there, which is a different conversation and not one this pool can open. Nothing below
# is a kitchen tool, so a cooking word in the line puts a knife back with the ordinary wants.
A_WEAPON = frozenset("""
gun guns shotgun shotguns pistol pistols handgun handguns revolver revolvers firearm firearms
airgun airguns rifle rifles crossbow crossbows machete machetes taser tasers knuckleduster
""".split())
WEAPON_WORDS = frozenset(("knife", "knives", "blade", "blades", "sword", "swords"))
NOT_A_WEAPON = (
    "cooking", "cook", "chef", "kitchen", "carving", "whittling", "craft", "fishing",
    "camping", "garden", "bread", "sharpening", "cutlery",
)
# The store answers a want it has filed in more than one frame: "Noted: your son wants a tattoo.",
# "Got it - your son wants a tattoo.", and, straight after a feeling, "Your son is 16 and wants a
# motorbike. That explains it - no wonder it sits on you." The frames differ; the shape does not -
# every one of them is the line said back and nothing else, so the want is filed and the person is
# left nowhere to start, and one of them invents a mood the line never said. `a_want_said_back`
# below reads the shape rather than the frames (`bot/memory/repeat.py`, `only_said_it_back`), so a
# new frame does not need a new entry here.
# A death is the store's to answer, not a want to price: "my mum died and my son wants a
# motorbike" is a bereavement with a want in it, and a feeling guessed beside it is at least about
# the right subject. The death is often a turn back rather than in this line ("my mum died last
# year", then "my son is 16 and wants a motorbike"), so a condolence in the reply counts too - the
# store has remembered and said it, and a want's first step on top of that reads as if it had not.
A_LOSS_IN_THE_LINE = re.compile(
    r"\b(?:died|dying|death|dead|passed\s+away|funeral|hospice|terminal|bereave\w*|widow\w*|"
    r"cancer)\b", re.I)
A_CONDOLENCE = re.compile(
    r"\bi(?:'m|\s+am)\s+(?:really\s+|so\s+|very\s+)?sorry\b|\bsorry\s+for\s+your\s+loss\b",
    re.I)

DEPENDANT_WANT_REPLIES = (
    "Then start with what it would really take - the price, and what the rules allow - before "
    "anyone says yes or no. What has been looked at so far?",
    "The asking is the easy half. Price it and check the rules first, because those two decide it "
    "more often than the wanting does.",
    "Ask what it is really for first - the thing itself and what it gets them are different "
    "problems. What has been said so far?",
)


# --- a report: something that has already happened ------------------------------------------
# A report says what happened, not what the person means to do about it. Three shapes cover the
# ordinary ones, and each is read from the grammar of the line rather than from its subject, so
# "the shop was shut", "my train got cancelled" and "the boiler packed in again" are one shape.

# Something small went wrong. A past-tense verb of a thing failing, or the state it left: the
# bus late, the shop shut, a flight cancelled, a bill gone up. These are all small and all
# someone's day, and none of them is an emergency or a fault the person wants talked through.
# Only the past is here, because the present is a fact rather than a setback: "the shop is shut
# on sundays" is how the shop works, and "Rotten luck" answers a complaint nobody made. The
# loosest words are the ones that are only a setback in the right phrase: "up" is "the rent went
# up" and also "i was up all night", so it keeps its own verb. Nothing that can be a body is
# here ("my son was sick", "he was ill"): those are the health pools' turn, and "Ugh, that's
# annoying" is a bad answer to a night up with a sick child.
SETBACK = re.compile(
    r"\b(?:was|were|got|went|kept|had)\s+(?:\w+\s+){0,2}?"
    r"(?:late|shut|closed|cancell?ed|delayed|sold\s+out|broken|bust|packed\s+in|"
    r"refused|rejected|declined|postponed|overbooked|queueing|queuing|back\s+in|"
    r"let\s+(?:me|us)\s+down)\b"
    r"|\b(?:broke\s+down|packed\s+in|gave\s+up\s+the\s+ghost|ran\s+out|"
    r"fell\s+through|let\s+(?:me|us)\s+down|missed\s+(?:the|my|a|our)\s+\w+)\b")
# A price is the only thing that "went up" as a setback: "i went up the stairs" and "my dad went
# up to bed" are movement, and "he kept up the payments" is a thing done right, so the verb keeps
# its own test with a money word in the line.
RISE = re.compile(r"\b(?:went|gone|goes|has\s+gone|have\s+gone|has\s+went|have\s+went)\s+up\b")
PRICE = frozenset("""
rent price prices gas electric electricity bill bills rate rates cost costs fare fares interest
mortgage insurance heating petrol fuel diesel food shopping council tax stamp fees fee nursery
""".split())
# "missed" takes a thing that can be missed: a bus, a train, a deadline, a call. A person who is
# missed is the other spelling of "i miss my mum", and that is the grief pools' line, not a
# nuisance - the past tense is the one people type in a bereavement chat.
MISSED = re.compile(r"\bmissed\s+(?:the|my|a|our|his|her|their)?\s*(\w+)")
# A missed deadline, appointment or interview is the person's own slip, so "Rotten luck" is the
# wrong voice for it: nothing went wrong outside them.
OWN_SLIP = re.compile(r"\bmissed\s+(?:the|my|a|our)\s+"
                      r"(?:deadline|deadlines|cut-?off|interview)\b")
# Only a filing puts a missed deadline back on the slip pool, and only by its own words: a visa,
# a court date and a mortgage application say their own thing later in the line ("i missed my
# visa deadline"), and a blanket deadline word moved the voice for all of them.
DEADLINE_LATER = re.compile(r"\b(?:accounts|confirmation\s+statement|companies\s+house|"
                            r"annual\s+return|self\s+assessment|statutory\s+accounts|"
                            r"filing|court|hearing|tribunal)\b")
# A thing that is broken now rather than was broken then is only a setback when the line says
# it keeps happening: "the lift is broken again" is the complaint, "the shop is shut on sundays"
# is the timetable.
PRESENT_SETBACK = re.compile(
    r"\b(?:is|are|keeps?|kept)\s+(?:\w+\s+){0,2}?"
    r"(?:broken|shut|closed|cancell?ed|delayed|off|down|out\s+of\s+order|full|sold\s+out)\b")
# The same setbacks said without an auxiliary, which is how most people type them: "the shop
# near me shut early", "the 6.40 was cancelled" keeps its "was" but "my train never came" and "it
# got nicked off the beach" do not, and the list above needs one, so these lines fell through to
# the stock nod ("I'm listening - say more if it helps"). The tense has to come from somewhere,
# so a bare verb has to bring either an adverb that only fits a past ("early", "late", "on me",
# "before i got there") or a "never" that settles it; "the shop shut on sundays" is the
# timetable and stays out. Theft keeps its own verbs: a thing taken is a setback whether or not
# the person says what it cost them.
# A break-in said in any of the ways people say it. The theft verbs above are about a thing taken
# and this is about a home entered, which is the one report in this pool that has an order of
# steps attached to it: the police for a crime reference number, then the insurer.
BURGLED = re.compile(r"\b(?:burgled|burglary)\b"
                     r"|\b(?:broken\s+into|broke\s+into|broken\s+in\s+and|break-?in\b)", re.I)
# "broken into" is also what a shed door, a gate and a cupboard are, and the hinge answer for those
# is a good one (`the shed was broken into` keeps it). So that verb only counts as a break-in with
# the home named or with nothing named to repair; "burgled" is a home being entered whenever it is
# said.
BURGLED_HOME = re.compile(r"\b(?:house|home|flat|apartment|place|maisonette|bedsit|caravan|"
                          r"bungalow|cottage|rented|landlady|landlord)\b", re.I)
NOT_A_BREAK_IN = frozenset((
    "shed", "garage", "gate", "cupboard", "door", "doors", "lock", "window", "windows",
    "boot", "car", "van", "bike", "motorbike", "bicycle", "allotment", "container",
    "bin", "suitcase", "locker", "box", "wardrobe", "safe", "parcel", "packet",
))
# Whose break-in it is: a person they know, so the reply is about them rather than about what to
# do first ("my mum was burgled", "the neighbours were burgled", "a mate got burgled").
BURGLED_SOMEONE_ELSE = re.compile(
    r"\b(?:my|his|her|their|our|the)\s+(?:mum|mom|dad|sister|brother|son|daughter|friend|mate|"
    r"nan|gran|grandma|grandad|granny|aunt|uncle|cousin|partner|husband|wife|boyfriend|"
    r"girlfriend|parents?|neighbours?|in-laws?|family|in-laws?)\b"
    r"|\b(?:a\s+mate|a\s+friend)\b"
    r"|\bthey\s+(?:were|got|have\s+been|had\s+been)\s+(?:burgled|broken\s+into)\b", re.I)
# "there was a burglary on our street" is the neighbourhood's news, not a home the person has to
# sort out tonight, so it is not read here: the two phone calls are not theirs to make.
BURGLED_NOT_THEIRS = re.compile(
    r"\b(?:on\s+(?:our|my|the)\s+(?:street|road|estate|avenue|close)|next\s+door|"
    r"round\s+the\s+corner|down\s+the\s+road|in\s+the\s+area|locally|nearby)\b", re.I)
BARE_SETBACK = re.compile(
    r"\b(?:shut|closed|cancell?ed|delayed|sold\s+out)\s+"
    r"(?:early|late|today|yesterday|again|on\s+me|before\s+(?:i|we)\s+(?:got|arrived))\b"
    r"|\bnever\s+(?:turned\s+up|showed\s+up)\b"
    r"|\b(?:(?:was|were|got|has|have|had)\s+(?:been\s+)?"
    r"(?:nicked|stolen|pinched))\b")
# A person who did not come is not a nuisance to be shrugged at: "you never showed up", "he never
# turned up", "she never showed up to my wedding" are somebody's hurt, and the pool this reads for
# says "Ugh, that's annoying" - the wrong thing to say to a person who has just been let down. A
# bare "never turned up" with no subject is still the parcel or the train ("i never turned up" is
# the person's own slip, and it reads as one). So the pronoun in front of the verb stands this
# reading down; the thing in front of it ("my train never turned up", "the delivery never showed
# up") does not.
NEVER_CAME_SUBJECT = re.compile(
    r"\b(?:i|you|he|she|we|they|him|her|them|mum|mom|dad|my\s+(?:mum|mom|dad|sister|brother|"
    r"son|daughter|friend|mate|partner|husband|wife|boyfriend|girlfriend))\s+never\s+"
    r"(?:turned\s+up|showed\s+up)\b")
# A burglary or a mugging that names no thing - "we were burgled", "i got mugged" - is not the
# small setback this pool answers ("Ugh, that's annoying" to a break-in is the wrong register and
# there is a card one inch away that says what to do first), so those verbs are read only when a
# thing of theirs is in the line: "my house got burgled what do i claim" keeps its insurer answer,
# and the bare report is left to the answer or the honest fallback.
# The setback is not always the shop or the train. Something done to a thing of theirs is the same
# nuisance however it is said, and the verb is what says it: what was done to the thing ("my car
# got keyed", "my phone screen cracked", "my tyre got slashed", "someone pickpocketed me on the
# bus"), a thing of theirs that did something of its own accord ("my dog ran off yesterday"), or a
# part of them broken ("i chipped a tooth eating a toffee"). None of those is one of the nouns of
# disaster this file already knows, so each was congratulated by the day pool instead - "Good to
# hear. What was the best bit?" - because a short past-tense account of the day is the same shape
# as "i got my hair cut". This is a class of verb, not a line for each mishap. A break-in, a
# mugging and a money scam keep out of it: they have a card with what to do first.
DONE_TO_ME = re.compile(
    r"\b(?:got|was|were|has been|have been|had been)\s+(?:\w+\s+){0,2}?"
    r"(?:pickpocketed|pick-?pocketed|keyed|scratch(?:ed)?|dented|chipped|cracked|smashed|"
    r"slashed|vandalised|vandalized|damaged|towed|clamped)\b"
    r"|\b(?:my|our)\s+(?:\w+\s+){0,3}?"
    r"(?:ran off|ran away|bolted|escaped|got out|wandered off|went missing|gone missing|"
    r"disappeared|vanished|cracked|stopped working|packed in)\b"
    r"|\bi\s+(?:chipped|cracked|broke|knocked out|lost)\s+(?:a|an|my|one of my|two)\s+\w+\b")
# "we were smashed at the party", "i got smashed at the pub", "got smashed last night", "my team got
# smashed on saturday": in British English "smashed" with nobody's thing in front of it is a good
# night out, and said of a team it is a match lost - neither is a thing of theirs broken, and "Rotten
# luck" for a good night out is the same wrong register this reading was written to stop, the other
# way round. What makes the difference is a thing of theirs in front of the verb ("my phone got
# smashed", "the window was smashed", "my glasses got smashed"), so the test is the absence of one
# and not the word on its own. "cracked" has the same shape and no line that misfires, so it stays
# in the class as it was.
SMASHED = re.compile(r"\bsmashed\b")
SMASHED_OF_A_THING = re.compile(
    r"\b(?:my|our|the|his|her|their|its)\s+(?:\w+\s+){0,3}?"
    r"(?:got|was|were|has\s+been|had\s+been|smashed|broken|shattered)\b")
# A team or a crowd is people, so "my team got smashed" says how the match went, not that a thing
# of theirs broke: the night-out sense of "smashed" is only the speaker's own evening, and a group
# of theirs that got smashed lost badly, which is a setback like any other.
A_GROUP_OF_PEOPLE = re.compile(
    r"\b(?:my|our|the|his|her|their)\s+(?:team|side|club|lot|lads|boys|girls|mates|friends|"
    r"family|kids|children|crowd|opposition|squad|band)\b")


# A person is not a thing of theirs that breaks. "my boss cracked a joke", "my son cracked a smile",
# "my kids ran off to play", "my mum packed in her job" are the person, not a breakage: cracked, ran
# off, got out, escaped and packed in say damage only when what stands in front of them is a thing -
# a screen cracks, a dog runs off, a pump packs in. The loss verbs are the other way round, so a
# person who went missing or vanished keeps the setback, as does a person who went off *with* a thing
# of theirs ("my brother ran off with my savings") or cracked a thing of theirs ("my mate cracked my
# phone"). Talking about a person is not the same as something being done to a thing of theirs.
A_PERSON_OF_THEIRS = re.compile(
    r"\b(?:my|our)\s+(?:boss|manager|mum|mom|mother|dad|father|son|daughter|boy|girl|kid|kids|"
    r"child|children|husband|wife|partner|boyfriend|girlfriend|ex|brother|sister|mate|mates|"
    r"friend|friends|colleague|colleagues|coworker|coworkers|nana|nan|gran|grandad|"
    r"grandma|grandpa|aunt|uncle|cousin|neighbour|neighbor|landlord|landlady|flatmate|housemate|"
    r"teenager|baby|toddler)\b")
A_PERSON_LOST = re.compile(r"\b(?:went\s+missing|gone\s+missing|disappeared|vanished)\b")
# "cracked a joke", "cracked a smile", "cracked up laughing": nothing broke, whoever did it.
CRACKED_A_JOKE = re.compile(
    r"\bcracked\s+(?:a|up|his|her|their|its)\s*(?:joke|smile|grin|laugh|voice|wise)"
    r"|\bcracked\s+(?:on|it)\b")
A_THING_CARRIED_OFF = re.compile(
    r"\b(?:ran|ran\s+off|ran\s+away|got\s+out|escaped|went\s+off|cracked|smashed|broke)\s+"
    r"(?:with|out)\s+(?:my|our|the)\b"
    r"|\b(?:cracked|smashed|broke|dented|scratched|chipped)\s+(?:open\s+)?(?:my|our)\b")


# The words that make a smashed evening a night out rather than a loss.
A_NIGHT_OUT = re.compile(
    r"\b(?:party|pub|night\s+out|works\s+do|wedding|stag|hen|club|bar|drinks|round|celebration)\b")


def _a_good_night_out(clean):
    """True when "smashed" means drunk, so the setback reading stands down.

    "we were smashed" and "got smashed last night" have no thing of theirs in front of them, so
    they are the night out. "the lads got smashed at the party" is people who drank. Every other
    thing said to be smashed - "my phone got smashed", "my glasses got smashed" - is broken.
    """
    if not SMASHED.search(clean):
        return False
    if not SMASHED_OF_A_THING.search(clean):
        return True
    if A_GROUP_OF_PEOPLE.search(clean):
        return bool(A_NIGHT_OUT.search(clean))
    return False


def done_to_me(clean):
    """True when the line reports something done to a thing of theirs, for the pools that cheer."""
    if not DONE_TO_ME.search(clean) or _a_good_night_out(clean) or CRACKED_A_JOKE.search(clean):
        return False
    if A_PERSON_OF_THEIRS.search(clean) and not A_PERSON_LOST.search(clean) \
            and not A_THING_CARRIED_OFF.search(clean):
        return False
    return True

# A body in the line means the health pools answer it, not this: "my son was sick last night" is
# a night up with a child, not a nuisance to shrug at.
REPORT_BODY = frozenset((
    "sick", "ill", "unwell", "poorly", "vomit", "vomiting", "sickness", "fever", "temperature",
    "flu", "cough", "cold", "bug", "hospital", "ambulance", "a&e", "999", "111", "doctor",
    "gp", "nurse", "midwife", "pain", "hurts", "hurting", "ache", "aching", "sore", "swollen",
    "bleeding", "blood", "dizzy", "faint", "fainted", "breathless", "seizure", "fit", "rash",
    "chest", "stroke", "allergic", "reaction", "concussion", "wound", "burn", "burnt",
))
# "i started a new job and it's fine" has already said how it is going, so the question that
# belongs to the news would be asking what the person just told the bot.
STARTED_VERDICT = re.compile(
    r"\b(?:was|is|went|were|been|going|getting|seems|looks)\s+(?:\w+\s+){0,2}?"
    r"(?:fine|good|great|ok|okay|well|alright|amazing|lovely|brilliant|easy|hard|tough|"
    r"awful|terrible)\b")

# A start with the verdict bad in it is not a start worth a "Nice": "the new job has teething
# problems", "my new job is going badly", "teething problems with the new job". The line is the
# trouble, and congratulating a person who has just said the thing is going badly is the reply a
# stranger gives. A good verdict after the bad one wins: "a few teething problems but going ok"
# is a start that is going all right.
STARTED_GONE_BADLY = re.compile(
    r"\b(?:problem|problems|trouble|troubles|teething|snag|snags|hiccup|hiccups|issue|issues)\b"
    r"|\b(?:hate|hates|hating|dread|dreading)\b"
    r"|\b(?:going|gone|went|is|was|been|getting|feels?)\s+(?:\w+\s+){0,2}?"
    r"(?:badly|bad|awful|terrible|horrible|rough|hard|tough|stressful|draining|exhausting|"
    r"rubbish|pants)\b")
# A thing that keeps happening is the same setback with "again" on it, and the word is the whole
# of what the person wants said: "again?" is what a friend answers before anything else.
AGAIN = re.compile(r"\b(?:again|again\s+today|again\s+this\s+(?:week|morning|time)|"
                   r"third\s+time|second\s+time|every\s+\w+\s+now|once\s+more)\b")
# Something has begun: a job, a course, work, a first day. The person is telling the bot the
# news, and the thing worth asking about is how it is going, not what the plan is.
STARTED = re.compile(
    r"\bstart(?:ed|ing)?\s+(?:a\s+|my\s+|his\s+|her\s+|their\s+|the\s+)?(?:new\s+)?"
    r"(?:job|work|course|college|uni|university|school|placement|apprenticeship|shift|"
    r"contract|role|internship|training)\b"
    r"|\bnew\s+(?:job|role|position)\b"
    r"|\bfirst\s+(?:day|week|shift)\b")
# The start is still to come: "i start my new job monday", "starting a course next week", "my
# first day is thursday". The same news, and the opposite question - a friend asks how they feel
# about it, not how the first week went, which has not happened yet. A past verb ("started",
# "began") makes it a report whatever day is in the line: "i started my new job on monday" keeps
# the how-is-it-going pool.
# A bare weekday is not a date on its own: "my first day was monday" is a day already spent, which
# is why a weekday or a month only dates a start when a word in front of it says it is still to
# come ("on", "next", "this", or a verb to be - "my first day is monday"). "tomorrow" needs
# nothing in front of it.
_AHEAD_DAY = (r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
              r"january|february|march|april|may|june|july|august|september|october|november|"
              r"december)")
START_AHEAD = re.compile(
    r"\b(?:(?:on|next|this)\s+" + _AHEAD_DAY + r"|"
    r"(?:next|this)\s+(?:week|weekend|month|year|term|afternoon|evening)|"
    r"tomorrow|tonight|soon|"
    r"in\s+(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+"
    r"(?:day|days|week|weeks|month|months)|"
    r"in\s+" + _AHEAD_DAY + r"|"
    r"(?:is|are)\s+(?:on\s+|this\s+|next\s+)?" + _AHEAD_DAY + r"|"
    r"(?:is|are)\s+(?:tomorrow|tonight))\b", re.I)
START_PAST = re.compile(r"\b(?:started|began|begun)\b", re.I)
START_PRESENT = re.compile(r"\b(?:start|starts|starting|begin|begins|beginning)\b", re.I)
# "i start work at 9" is a shift today, not a first day, so a clock time is not a date.
START_CLOCK = re.compile(r"\bat\s+\d{1,2}(?::\d{2})?\b|\b\d{1,2}\s*o'?clock\b", re.I)
# A feeling, a want or a judgement in the line means the mood pools answer it better than the
# shape does, and the caller has already read those.
REPORT_FEELING = frozenset((
    "happy", "glad", "sad", "gutted", "scared", "afraid", "worried", "angry", "furious",
    "annoyed", "frustrated", "upset", "excited", "proud", "relieved", "tired", "exhausted",
    "fed", "sick", "awful", "terrible", "worst", "great", "brilliant", "amazing", "love",
    "hate", "cried", "crying", "tears", "worst", "nightmare", "disaster", "stress",
    "stressed", "anxious", "panic", "worst", "sorry", "unfortunately", "gutted",
))

# What a friend says to a small setback, with no advice and no question that assumes there is
# something to do about it: the shop being shut is a nuisance, not a task.
# A thing of theirs taken by somebody else. Theft typed the way people type it - "someone nicked
# my bike", "my bike was swiped", "my purse got lifted on the bus" - has a past-tense verb and no
# harm word, so the small-day reading in `fallback.py` took the line and congratulated the person
# ("Nice one. How did the rest of it go?"), while `BARE_SETBACK` below answered the "got nicked" /
# "was pinched" forms with a receipt and no question after it ("Rotten luck.", "That's a pain.").
# It is read here, before the setback shape, so the commonest phrasings cannot slip through the
# receipt; and it stands down where the knowledge base has a card for the thing itself, because
# a card that names the frame number and the crime number is the better answer.
TAKEN_FROM_THEM = re.compile(
    r"\b(?:(?:my|our|his|her|their|the)\s+\w+\s+(?:was|were|got|has|have|had)\s+"
    r"(?:been\s+)?(?:nicked|stolen|swiped|pinched|lifted|thieved|snaffled|taken))\b"
    r"|\bi\s+had\s+(?:my|our|his|her|their)\s+\w+\s+"
    r"(?:nicked|stolen|swiped|pinched|lifted|thieved|snaffled|taken)\b"
    r"|\b(?:someone|somebody|some\s+(?:lad|bloke|kid|guy|person|scrote)|they)\s+"
    r"(?:nicked|stole|swiped|pinched|lifted|took|thieved|snaffled)\b")

# "someone took my seat", "they took my order", "the hospital took my name": a thing handed over or
# held for them, not a loss, and "That's rotten" answers a complaint nobody made.
NOT_A_LOSS = re.compile(
    r"\b(?:table|seat|seats|place|places|order|orders|turn|call|name|names|number|photo|photos|"
    r"picture|pictures|temperature|blood|bloods|details|booking|form|form\s+in|payment|"
    r"space|spaces|spot|spots|parking|slot|slots)\b")

# "somebody took my washing in", "they took my parcel in for me": a neighbour doing them a favour
# is not a theft. The particle is what tells the two apart - "took my bike in the night" is a loss
# and reads as one in the line as a whole, so the guard stops at the participle only when a short
# span later the line says "in" without a time word after it.
TOOK_IT_IN = re.compile(r"\b(?:took|taken|takes|take)\b[^.]{0,25}\bin\b(?!\s+(?:the\s+)?"
                        r"(?:night|morning|afternoon|evening|day|daylight|hours|town|time|future|"
                        r"error|haste|early|late|later)\b)")


def _a_thing_taken(clean):
    """True for a report of something of theirs taken by somebody else."""
    text = " ".join(str(clean or "").lower().split())
    if not text or not TAKEN_FROM_THEM.search(text):
        return False
    return not NOT_A_LOSS.search(text) and not TOOK_IT_IN.search(text)


# The answer to the loss pool's own question. The pool asks where it went or what has to happen
# tonight, and the answer - "my cards were in it", "the keys were in the bag" - names the thing
# that turns a loss into jobs. It reached the small-day pool and was congratulated ("Good to hear.
# What was the best bit?") because the line has no harm word in it, so the follow-through is read
# here: the card to stop, the crime number, the insurer's list.
LOSS_FOLLOW = re.compile(
    r"\bcards?\b|\bcash\b|\bmoney\b|\bkey|\bkeys\b|\bphone\b|\bwallet\b|\bpurse\b|"
    r"\bbag\b|\bbike\b|\bpassport\b|\binsurance\b|\binsurer\b|\bclaim\b|\bpolice\b|"
    r"\bblock|\bfreez|\bcancel|\bbank\b|\blaptop\b|\bcar\b|\bvan\b|\btools?\b")
LOSS_FOLLOW_REPLIES = (
    "Then stop the cards before anything else - most banking apps freeze them in one tap, and it "
    "is quicker than the phone queue. Ring 101 for a crime reference number and keep it, because "
    "the bank and the insurer both ask for it by name.",
    "Money and cards are the urgent part: freeze them in the app now, then ring the bank and say "
    "taken, not lost. A stolen card is handled differently from one left on a bus, and the "
    "difference is the crime reference.",
    "Insurance next, while it is fresh. The insurer wants the crime reference, a list of what "
    "went, and whatever receipts or photos you can find - and anything else damaged wants "
    "photographing before it is tidied up.",
)


def _the_loss_was_asked(memory):
    """True when the bot's last reply was the loss pool asking its question."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    last = str((turns[-1] if turns else {}).get("bot") or "").strip()
    return last in A_THING_TAKEN


def _the_answers_take_it(clean):
    """Whether the knowledge module answers this line itself.

    Asked the same way `fallback.py` asks it for the identity card: the module that owns the
    answer says whether it has one, and a hit that comes back empty is not an answer.
    """
    try:
        from ..modules import answers

        return answers.respond(clean, {}) is not None
    except Exception:
        return False


SETBACK_REPLIES = (
    "Oh, that's a nuisance.",
    "That's a pain.",
    "Rotten luck.",
    "Ugh, that's annoying.",
)
# ...and to the same setback the third or fourth time round. The repeat is what the line is
# about, so it is what the reply answers first.
AGAIN_REPLIES = (
    "Again? That's a pain.",
    "Again - that's annoying.",
    "Again. That's a nuisance.",
    "That keeps happening, then. Do you know why?",
    "Again? Has it been like that a while?",
)
# Something new has started: how it is going is the question a friend asks, and it is the one
# question this line can answer without the bot knowing anything about the job.
STARTED_REPLIES = (
    "Nice. How's it going so far?",
    "Good. How were the first days?",
    "Nice one. How's it treating you?",
    "Good luck with it - how has the first week been?",
)
# ...and to the same news when the day has not come yet: what is ahead, not what has been.
STARTED_AHEAD_REPLIES = (
    "Good luck with it - how are you feeling about it?",
    "Nice. What are you looking forward to?",
    "Good luck on the day. Anything you want sorted before then?",
    "A fresh start, then. What is the first thing you will do?",
    "Nice one. Are you looking forward to it, or dreading it a bit?",
)
# A break-in is not a nuisance and the response to one is not a shrug: what a person needs in the
# first minute is the order of the two phone calls. The knowledge base answers this when the line
# names the thing ("our house was burgled" gets the insurer card) and it always wins, so this pool
# only reaches the report made by the person with no house in it - "we were burgled", "i got back
# and we had been burgled" - which main answered with "Ugh, that's annoying" or "Nice one. How did
# the rest of it go?". The two steps here are the card's own two steps, said in one breath.
BURGLED_REPLIES = (
    "That's a horrible thing to come back to. Ring the police first and get a crime reference "
    "number - the insurer asks for it - and tell the insurer before you clear anything up.",
    "I'm sorry. Report it and get a crime reference number, then ring the insurer: they want to "
    "know before anything is tidied away, and they ask for that number first.",
    "Awful. The order that matters is the police for a crime reference number, then the insurer, "
    "before you touch anything.",
)
# ...and to the same thing happening to somebody they know ("my mum was burgled", "the neighbours
# were burgled"): the person is shaken for them, so the reply is about them and not about the
# paperwork the two of them will have to do.
BURGLED_FOR_SOMEONE_REPLIES = (
    "That's a horrible thing to happen to them. Are they all right, and is someone with them?",
    "Awful for them. Do they have somebody there with them tonight?",
    "That's a nasty thing to go through. How are they holding up?",
)
# A deadline or an appointment that was missed is the person's own slip, so the reply is about
# what is left rather than about luck.
SLIP_REPLIES = (
    "Deadlines do that. How much time is left?",
    "It happens. What can you still get in?",
    "Easy to lose track of one. What is left to do?",
)
# ...and to the same news with the verdict already in it: a reaction, and no second question.
STARTED_FINE_REPLIES = (
    "Good - glad it's going all right.",
    "Nice one. Sounds like a good start.",
    "Good to hear it.",
)
# ...and to a start that has already hit something: "teething problems with the new job",
# "my new job is going badly". There is nothing to congratulate, so the reply says the thing
# is a rough start and asks what is wrong with it - the question a friend asks.
STARTED_BADLY_REPLIES = (
    "That's a rough start. What's going wrong with it?",
    "Sorry it's been like that. What's the worst of it?",
    "Ah, that's a shame this early on. What's not working?",
    "A rough first stretch. What would make it easier?",
)


def _missed_a_person(clean):
    """True when "missed" is about a person: "i missed my dad" is not a bus that went without me."""
    for match in MISSED.finditer(clean):
        if match.group(1) in OTHER_PEOPLE:
            return True
    return False


def reads_as_report(clean, words):
    """'setback', 'again', 'started' or None: the shape of the thing they told us."""
    if not clean or "?" in clean:
        return None
    if set(words) & REPORT_FEELING or set(words) & REPORT_BODY:
        return None
    if _missed_a_person(clean):
        return None
    if _reads_as_a_break_in(clean, words):
        return "burgled"
    if STARTED.search(clean):
        return "started"
    if OWN_SLIP.search(clean):
        return "slip"
    # A missed filing is the person's own slip even when a word sits between "missed" and the
    # deadline: "i missed my confirmation statement deadline" and "i missed my self assessment
    # deadline" are a job still to do, not a nuisance that happened to them, and OWN_SLIP only
    # reads the words straight after "missed".
    if MISSED.search(clean) and DEADLINE_LATER.search(clean):
        return "slip"
    if BARE_SETBACK.search(clean) and NEVER_CAME_SUBJECT.search(clean):
        # "you never showed up" is somebody's hurt, not a nuisance: leave it to the pools that
        # know about people. A thing that never turned up is still the setback below.
        return "again" if AGAIN.search(clean) else None
    if (SETBACK.search(clean) or BARE_SETBACK.search(clean) or done_to_me(clean)
            or (RISE.search(clean) and set(words) & PRICE)):
        return "again" if AGAIN.search(clean) else "setback"
    if AGAIN.search(clean) and PRESENT_SETBACK.search(clean):
        return "again"
    return None


def _still_to_come(clean):
    """A start the person is telling the bot about before it has happened.

    Two ways a start is still ahead: a day or a stretch of time that has not come ("i start my
    new job monday", "my first day is thursday"), or a verb in the present with no day at all
    ("i start a new job" - a start named and not yet had). A past verb makes it a report whatever
    day is in the line, and a clock time ("i start work at 9") is a shift today, not a date.
    """
    if START_PAST.search(clean) or START_CLOCK.search(clean):
        return False
    return bool(START_AHEAD.search(clean) or START_PRESENT.search(clean))


# The good half of STARTED_VERDICT on its own, so a line that says both can be read in order.
STARTED_WELL = re.compile(
    r"\b(?:fine|good|great|ok|okay|well|alright|amazing|lovely|brilliant|easy)\b")
# The stretch of a start, named: "my first day", "the first week". A day that went badly is the
# day, not the start, and bot/memory/setback.py asks about it better than a start pool can.
FIRST_STRETCH = re.compile(r"\bfirst\s+(?:day|week|shift|month)\b")


def _started_badly(clean):
    """True when a start is said with something wrong in it and nothing to say it came right.

    "a few teething problems but going ok" says both, and the good half is the one the person
    means, so the order of the words decides it.
    """
    bad = STARTED_GONE_BADLY.search(clean)
    if not bad:
        return False
    return STARTED_WELL.search(clean, bad.end()) is None


def _reads_as_a_break_in(clean, words):
    """True when the line is a home being entered, rather than a thing to repair.

    "burgled" always is one. "broken into" is also a shed door, a gate and a cupboard, and those
    keep the hinge answer, so with that verb the home has to be named and no repairable thing may
    be in the line.
    """
    if not BURGLED.search(clean):
        return False
    if BURGLED_NOT_THEIRS.search(clean) and not BURGLED_SOMEONE_ELSE.search(clean):
        return False
    if re.search(r"\b(?:burgled|burglary)\b", clean, re.I):
        return True
    if set(words) & NOT_A_BREAK_IN:
        return False
    return bool(BURGLED_HOME.search(clean)) or bool(
        re.search(r"\b(?:i|we|they)\s+(?:was|were|got|have\s+been|had\s+been)\s+"
                  r"(?:broken\s+into|broken\s+in)\b", clean))


def break_in_reply_for(clean, words, memory):
    """The reply to a home being broken into, or None when the line is not one.

    Its own function so the pools that answer a sad day can stand aside for it: "someone broke
    into our house" is read as bad news and answered "Ugh, that's a lot to carry", which is a
    shrug at a break-in.
    """
    if not _reads_as_a_break_in(clean, words):
        return None
    pool = (BURGLED_FOR_SOMEONE_REPLIES if BURGLED_SOMEONE_ELSE.search(clean)
            else BURGLED_REPLIES)
    return pick(pool, memory, clean)


def report_reply_for(clean, words, memory):
    """A reply to a report of something that happened, or None to leave it to the caller."""
    if set(words) & NOT_PLAIN or _has_phrase(clean, CRISIS):
        return None
    if _has_phrase(clean, COUNTERFACTUAL) or set(words) & MARKED_DATE:
        return None
    if set(words) & ASKS or _has_phrase(clean, DOUBT):
        return None
    shape = reads_as_report(clean, words)
    if shape == "burgled":
        # A home entered is not a thing to repair, so this comes before the trouble reading:
        # trouble answers "broken into" with "What's it doing exactly?", and a person who has just
        # been burgled should not be asked what their house is doing.
        return break_in_reply_for(clean, words, memory)
    if _a_thing_taken(clean) and not _the_answers_take_it(clean):
        # Read before the shape is trusted, because the commonest thefts have no shape the report
        # reader knows: "my purse got lifted on the bus" and "i had my wallet lifted in town" fell
        # past it to the small-day pool ("How was it, overall?").
        return pick(A_THING_TAKEN, memory, clean)
    if _the_loss_was_asked(memory) and not set(words) & ASKS and LOSS_FOLLOW.search(clean):
        return pick(LOSS_FOLLOW_REPLIES, memory, clean)
    if not shape:
        return None
    if shape != "started" and trouble.reads_as_trouble(clean, words, clean):
        # A thing of theirs that has gone wrong is trouble.py's turn: "my boiler packed in again"
        # wants what it is doing and what they have tried, not "Again? That's a pain."
        return None
    if shape == "started" and _started_badly(clean):
        if FIRST_STRETCH.search(clean):
            # "my first day went badly" is about the day: the setback reader answers it.
            return None
        return pick(STARTED_BADLY_REPLIES, memory, clean)
    if shape == "started" and STARTED_VERDICT.search(clean):
        return pick(STARTED_FINE_REPLIES, memory, clean)
    if shape == "started" and _still_to_come(clean):
        # "i start my new job monday" is news about what is coming; asking how the first week
        # went is a question about a week that has not happened.
        return pick(STARTED_AHEAD_REPLIES, memory, clean)
    pool = {"setback": SETBACK_REPLIES, "again": AGAIN_REPLIES,
            "started": STARTED_REPLIES, "slip": SLIP_REPLIES}[shape]
    if _asked_last(memory) and shape != "started":
        # The bot has just asked something; a report is not an interview, so answer it plainly.
        pool = tuple(o for o in pool if not o.endswith("?")) or pool
    return pick(pool, memory, clean)


# "we booked the holiday but now i regret it": the person has told the bot the whole thing and
# the only part that matters is the regret. Nothing in the bot read it - the line came back as the
# nod ("Thanks for telling me") or, before the booking reading stood aside, as the booking said
# back. A regret is not a report and not a plan: the reply meets it and asks what turned, which is
# the one question a friend asks.
REGRET = re.compile(r"""
    \bregrets?\b | \bregretted\b | \bregretting\b
  | \bwish\s+(?:i|we)\s+(?:had|did)\s*(?:n'?t|nt| not)\b
  | \bwish\s+(?:i|we)\s+had\s+(?!a\b|an\b|the\b|more\b|enough\b|some\b|any\b|no\b
                                     |another\b|my\b|your\b|his\b|her\b|their\b|our\b
                                     |one\b|two\b|three\b|\d)\w+\b
  | \b(?:not|never)\s+sure\s+(?:i|we)\s+(?:should|ought\s+to)\b
""", re.VERBOSE)
# A regret that is not theirs to keep, or not a regret at all: a death (the loss and grief bands
# answer those), a body, a thing that has gone wrong (trouble.py asks what it is doing), a
# question, and a line that takes the regret back.
NO_REGRET = frozenset((
    "died", "dying", "dead", "death", "funeral", "passed", "buried", "hospital", "cancer",
    "diagnosis", "chemo", "miscarriage", "stillbirth",
))
REGRET_LINES = (
    "That's the thing about hindsight - it always turns up after. What would you do differently?",
    "Regret is worth listening to. If you could undo it, what would you do instead?",
    "That sounds like it has been sitting with you. What happened?",
    "A decision can turn out wrong without you being wrong to make it. What would you change?",
    "That is a fair thing to feel. What is the part you keep going back to?",
    "Easy to see it now. Would you do it differently next time?",
)
# The same reading with no question on the end, for when the bot has just asked one: two in a row
# is an interrogation, and a regret is not the turn to ask.
REGRET_LINES_PLAIN = (
    "Hindsight is always clearer than the decision was.",
    "That is a lot to carry without it being a mistake.",
    "Regret usually means the thing mattered to you.",
    "You can tell me the part that keeps coming back.",
)


# The pool is first person ("what would you change?"), so the person has to be the one regretting:
# "my dad regrets it", "she said she regrets it" and "he regrets it" are the person telling the bot
# about somebody else. The pronoun has to carry the verb - a few adverbs are allowed between them,
# so "i really regret it" and "i kind of regret it" still count, but "i think my dad regrets it"
# does not.
FIRST_PERSON = re.compile(
    r"\b(?:i|im|ive|we|weve)\b"
    r"(?:\s+(?:really|so|only|just|still|already|now|also|kind\s+of|sort\s+of|do|did|dont|absolutely))*"
    r"\s+(?:regret|regrets|regretted|regretting|wish)\b")

# "i regret to say i cant come", "i regret that i cant make it": a polite apology, not a regret the
# person is carrying around.
# A regret inside a question about what can be done is the question's: "can i return a car i
# regret buying", "how do i cancel a holiday i regret booking". The doing word has to be asked
# for, never just named - "i regret buying this car" is still the feeling.
PRACTICAL_ASK = re.compile(
    r"\b(?:can|could|should|shall|may)\s+(?:i|we)\s+\w+|"
    r"\bhow\s+do\s+(?:i|we)\s+\w+|\bhow\s+can\s+(?:i|we)\s+\w+|"
    r"\bwhere\s+do\s+(?:i|we)\s+\w+|\bwhat\s+do\s+(?:i|we)\s+do\b|"
    r"\bis\s+it\s+worth\b|\b(can|could)\s+(?:i|we)\s+(?:still\s+)?"
    r"(?:return|refund|exchange|cancel|sell|fix|claim|complain|change|get\s+(?:out|rid))\b")
POLITE = re.compile(
    r"\bregret\s+to\s+(?:say|tell|inform|report|announce|admit|hear|learn|let)\b"
    r"|\bregret\s+(?:that\s+)?(?:i|we)\s+(?:cant|can'?t|cannot|wont|won'?t|am\s+unable"
    r"|are\s+unable|am\s+not\s+able|must\s+miss)\b")

# A regret is about something that has already happened. Before it, the line is a wry remark
# about what they are about to do ("im going to regret this", "ill regret this tomorrow").
FUTURE_REGRET = re.compile(
    r"\b(?:going to|gonna|will|won'?t|wont|shall)\s+(?:\w+\s+){0,2}?regret\b"
    r"|\bregret\s+(?:this|it)\s+(?:tomorrow|in the morning|later|after)\b"
    # ... and one aimed at the bot is not theirs either: "youll regret this" is a threat, not a
    # thing the person is carrying.
    r"|\byou(?:'?ll|ll|\s+will)\s+regret\b")

# The commonest way the feeling is said is not the word "regret" at all: "i shouldnt have said
# that", "i should have kept my mouth shut". The pool above already answers "i wish i hadnt";
# this is the same regret in the words people actually type.
SHOULDNT_HAVE = re.compile(
    r"\bshould(?:n'?t|nt|\s+not)\s+have(?!\s+to\b)\s+"
    r"(?:\w+ed|said|told|bought|gone|done|left|taken|kept|booked|paid|sent|agreed|started|moved|"
    r"quit|sold|given|made|let|put|drunk|eaten|spent|worn|seen|heard|written|driven|known)\b"
    # "i should have kept my mouth shut" is the same regret without the negation, and the same
    # words after it: the participle is the test, so advice ("you should have a look") is not.
    # The words are the same on both sides of the "not", because the line with the negation was
    # reaching the nod while the same regret without it was met: "i should not have gone" was
    # "Got it. Is there anything you'd like a hand with?" and "i shouldnt have gone" was the
    # regret pool. Only the spelling of the "not" is wider here; the words after it are not.
    r"|\bshould\s+have\s+(?:said|told|bought|gone|done|kept|booked|paid|sent|left|taken|"
    r"stayed|waited|asked|listened|started|stopped|quit|held|walked|stood)\b")

# "i regret putting my dog down": the regret is real, but the answer is the loss one, and this
# reading would take the turn from it.
PUT_DOWN = re.compile(
    r"\b(?:put|putting)\s+(?:\w+\s+){0,2}?(?:down|to\s+sleep)\b|\b(?:euthanis|euthaniz)\w*")


# A "shouldnt have" regret carries its verb on "should", not on "i", so the subject test above
# sees no verb where it looks for one. The line has to open with the person for it to be theirs.
_OWN_SHOULD = re.compile(r"^\s*(?:[a-z]+,?\s+){0,2}(?:i|we)(?:'?ve|ve)?\s+should")
# A regret that names who it was done to is already answered by the card for repairing it: "i
# shouldnt have shouted at my son" got the row-repair answer ("say sorry plainly, name what
# happened - 'I shouted about the shoes'") and reading it as a feeling instead took that away, so
# the parent lost the only line that told them what to do. `at my wife` kept its card, so without
# this the same regret was two different replies depending on who was named. The person has to be
# after the verb, and `said`/`told` are not on the list: "i shouldnt have said that to my mum"
# got a note read back and the regret answer is the gain there.
_HARM_AT_PERSON = re.compile(
    r"\b(?:shout(?:ed|ing)?|snapp(?:ed|ing)|yell(?:ed|ing)|swore|screamed|scream(?:ed|ing)|"
    r"lied|lash(?:ed)?\s+out|sulk(?:ed)?|was\s+(?:horrible|awful|mean|cruel|nasty))\s+"
    r"(?:at|to)\s+(?:my|his|her|our|your|the)\s+\w+")

# "wish i hadn't bothered" opens on the wish, so there is no separate "i" for the subject test
# above to find and the regret was read as a report of a day: the same words with "i " in front
# ("i wish i hadn't bothered") were met properly. A regret the person is asking the bot about is
# still turned away above, and "my dad wishes he hadn't" is somebody else's.
WISH_I = re.compile(r"^\s*wish\s+(?:i|we)\b")


def reads_as_regret(clean, words=()):
    """True when the line is a regret the person is telling the bot about."""
    if not clean or "?" in clean:
        return False  # a question is not a regret: "do you regret it?" is about the bot
    if re.match(r"(?:do|does|did|would|have|are|is|was|were|can|could)\s+(?:you|u)\b", clean):
        return False  # a regret the person is asking the bot about is not theirs to be met
    if set(words) & NO_REGRET or set(words) & NOT_PLAIN:
        return False
    if _has_phrase(clean, CRISIS) or _has_phrase(clean, COUNTERFACTUAL):
        return False
    if not (FIRST_PERSON.search(clean) or WISH_I.search(clean)
            or (_OWN_SHOULD.search(clean) and SHOULDNT_HAVE.search(clean))):
        return False  # somebody else's regret ("my dad regrets it") is not the person's to work through
    if POLITE.search(clean):
        return False  # "i regret to say i cant come" is a polite apology, not a thing to undo
    if PRACTICAL_ASK.search(clean):
        # "can i return a car i regret buying" asks what can be done, and the entries answer it
        # ("Fourteen days from the day it arrives..."). Reading it as a feeling takes the card
        # away and leaves a search hedge, which is the worst of both.
        return False
    if FUTURE_REGRET.search(clean):
        return False  # "im going to regret this" is a thing not done yet: nothing has turned
    if PUT_DOWN.search(clean):
        return False  # a regret about a pet put to sleep is the loss band's, not this reading's
    if _HARM_AT_PERSON.search(clean):
        # a regret that names the person it was done to has its own card, the repair one
        return False
    if re.search(r"\b(?:no|dont|don't|never|not)\s+regrets?\b", clean):
        return False  # "no regrets" is the opposite, and "i dont regret it" is a defence
    if re.search(r"\bregrets?\s+(?:nothing|none)\b", clean) or "regret a thing" in clean:
        return False  # "i regret nothing" is not a regret
    return bool(REGRET.search(clean) or SHOULDNT_HAVE.search(clean))


def regret_reply_for(clean, words, memory, repaired=""):
    """A reply to a regret, or None to leave the line to the caller.

    `repaired` is the same line with its chat-speak put right, as the rest of the composer
    reads one (bot/understanding's `plain`). The words above are written for the standard
    spelling, so "i shudnt have said anything" was a regret when it was typed with its
    apostrophe and a small account of the day when it was not - the same feeling, two turns
    depending on how fast the person typed. The typed line is asked first, so a line that
    reads with no repair is untouched.
    """
    said = clean
    words = words or clean.split()
    if not reads_as_regret(clean, words):
        if not (repaired and repaired != clean and reads_as_regret(repaired,
                                                                  repaired.split())):
            return None
        said = repaired
        words = repaired.split()
    if set(words) & ASKS or _has_phrase(said, DOUBT):
        return None
    pool = REGRET_LINES_PLAIN if _asked_last(memory) else REGRET_LINES
    return pick(pool, memory, said)


# --- a fact about one of their people -------------------------------------------------------
# "my parents live in derby", "my daughter is 4", "my sister is called meg": the person has
# handed over something about somebody they love and nothing else. It is not news (nothing has
# happened) and not a plan, so it fell through to the store, and the store answered with the
# line said back - "Noted: your parents live in derby." - which is a filing cabinet, not a
# friend. What a friend does with a fact like this is take an interest in the person in it.
#
# The shapes are the whole line, not a search inside it: "my mum is 82 and keeps forgetting
# things" is a worry about her, and "my son is 3 and hates mushrooms" has a taste in the tail
# for the cooking side to answer. Only a line that is *just* the fact lands here.
THEIR_PERSON = (r"(?:mum|mom|mam|mother|dad|father|parents|sister|brother|son|daughter|kid|"
                r"kids|child|children|boy|girl|eldest|youngest|"
                # what a parent calls a child instead of "my son": the little one, the baby, the
                # toddler, the eldest. "my little one is 7 months old" was answered "Got it. Is
                # there anything you'd like a hand with?", which reads nothing, and the age
                # pools below already know what to ask a parent of a baby.
                r"baby|baby boy|baby girl|little one|little boy|little girl|little man|"
                r"little lad|little miss|oldest|firstborn|toddler|"
                r"gran|granny|nan|grandma|"
                r"grandmother|grandad|grandpa|grandfather|grandparents|nana|aunt|uncle|"
                r"cousin|partner|husband|wife|niece|nephew|grandson|granddaughter|"
                r"grandchildren|grandkids|grandsons|granddaughters|stepson|stepdaughter|"
                r"folks|inlaws|in-laws|friend|friends|mate|mates|best friend|best mate|"
                r"boss|colleague|workmate|neighbour|neighbor|neighbours|neighbors|"
                r"flatmate|housemate|roommate)")
# A parent does not always say "son" or "daughter": the youngest one is "the baby", "the little
# one", "our wee one", and "my baby is 7 months old" is the same fact as "my boy is 7 months old".
# Without these words the age was read for a boy and ignored for a baby, and the same sentence
# typed with the word a parent actually uses got nothing back.
# A qualifier sits between "my" and the child as often as not - "my other son", "my eldest
# daughter", "my baby girl" - and with no room for it the whole pair of facts was missed and the
# line got a line that fits any message ("Sounds alright. Anything good in it?").
THEIR_QUALIFIER = (r"(?:other|eldest|oldest|youngest|little|big|small|wee|first|second|third|"
                   r"middle|baby|grown up|grownup|step|adopted|foster) ")
THEIR_CHILD = (r"(?:son|daughter|kid|kids|child|children|boy|girl|eldest|youngest|niece|"
               r"baby|baby boy|baby girl|little one|little boy|little girl|little man|"
               r"little lad|little miss|oldest|firstborn|toddler|"
               r"nephew|grandson|granddaughter|grandkids|grandchildren|stepson|"
               r"stepdaughter|baby|babies|toddler|toddlers|newborn|newborns|infant|infants|"
               r"little one|little lad|little man|little fella|little fellow|little girl|"
               r"little boy|wee one|wee man|wee lad|small one)")
# What a parent says about a child is often two facts in one line - a name and an age - and
# both are the same kind of thing, so one shape reads the pair.
#
# The "is" is optional because people leave it out - "my sons called tom, hes 9" is the same two
# facts as "my son is called tom and he is 9" - and the pair is as often joined with a comma as
# with "and". Both forms fell past this shape to a line that fits any message ("Nice one. How did
# the rest of it go?") a turn after the same two facts got "Mia, 6. What is she like just now?".
THEIR_NAME_AGE = re.compile(
    r"^my (?:" + THEIR_QUALIFIER + r")?(?P<person>" + THEIR_CHILD + r")(?:'?s)? (?:is called|is named|name is|name's|called|named) "
    r"(?P<name>[a-z][a-z'-]{1,14})(?: and |, )?(?:she|he|they|it)(?:'?s| is| are) "
    r"(?:just |only |nearly )?(?P<age>\d{1,2})$")
THEIR_NAME = re.compile(
    r"^my (?P<person>" + THEIR_PERSON + r")(?:'?s)? (?:is called|is named|name is|name's) "
    r"(?P<name>[a-z][a-z'-]{1,14})$")
# An age is said as a number or as a word - "my nephew is two" is how somebody says it out loud -
# so both are read, and the reply always uses the number, which reads the same either way.
AGE_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
             "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
THEIR_AGE = re.compile(
    r"^(?:my|our|the) (?:" + THEIR_QUALIFIER + r")?(?P<person>" + THEIR_CHILD + r")(?:'?s)? (?:is|are|is now|just turned|turns?) "
    r"(?:just |only |nearly |about )?(?P<n>\d{1,2}|" + "|".join(AGE_WORDS) + r")"
    r"(?:\s?(?:years?|yrs?\.?|y/o|yo|months?|mths?\.?|mth)(?:[ -]?old)?| old| now)?$")
# A number with no unit beside a baby's own word is the age in months, because that is how a parent
# says it: "my baby is 3" means three months, not three years. "little one" and "toddler" are left
# out here: those words are said of children in years as often as not.
BABY_WORDS = frozenset(("baby", "babies", "newborn", "newborns", "infant", "infants"))
# A unit of its own makes the number a count of years, whatever word is beside it: "my baby is
# 2yo" and "my baby is 3 yrs" are two and three years old, not months.
YEAR_UNIT = re.compile(r"\b(?:years?|yrs?)\b|\d\s*(?:years?|yrs?|y/o|y\.o|yo|yr)\b")
THEIR_PLACE = re.compile(
    r"^my (?P<person>" + THEIR_PERSON + r")(?:'?s)? (?:live|lives|are living|is living|are based|"
    r"lives away) (?:in|near|up in|down in) (?P<place>[a-z][a-z '\-]{1,24}?)$")
# What one of their people does for a living ("my wife is a nurse", "my dad is a builder"). The
# job words are the store's own list (bot/memory/facts.py), read here rather than copied, so the
# two cannot drift about what counts as a trade. A phrase gets one word in front of the head
# ("care assistant", "head chef") and no more, and the head has to be the last word in the line.
THEIR_JOB = re.compile(
    r"^my (?P<person>" + THEIR_PERSON + r")(?:'?s)? (?:is|works as) (?:a |an )?"
    r"(?P<phrase>[a-z][a-z '\-]{2,28})$")
# A job said with its own name first ("my wife is a nurse at the royal") is not this shape: the
# line names where she works, which is a different question, and it keeps the old reply.
THEIR_JOB_LINES = (
    "{Job}. What does a normal day look like for {them}?",
    "{Job} \u2014 how long has {they} been at it?",
    "{Job}. Does {they} work nights, or is it days?",
    "{Job}. Is that what {they} always wanted to do?",
)
# A grandparent's age. THEIR_AGE below is for a child of theirs, and its pools ask what a child
# is into - the wrong question about somebody's nan - so a grown person's age is deliberately
# declined ("my dad is 84" is nobody's business here). A grandparent at 88 is its own line, and
# a warm one: the store used to answer it "Noted: your nan is 88."
THEIR_ELDER = (r"(?:nan|nana|gran|granny|grandma|grandmother|grandad|granddad|grandpa|"
               r"grandfather|great gran|great nan|great grandma|great grandad|great aunt|"
               r"great uncle)")
THEIR_ELDER_AGE = re.compile(
    r"^my (?P<person>" + THEIR_ELDER + r")(?:'?s)? (?:is|is now|just turned|turns?) "
    r"(?:just |only |nearly |about )?(?P<n>\d{2,3})"
    r"(?: (?:years? old|year old|now))?$")
# A grandparent is never twelve, so the age is always a figure: AGE_WORDS stops at twelve and a
# word that is not in it is not this shape.
THEIR_ELDER_LINES = (
    "{n} \u2014 that is a good innings. Does {they} still live on {their} own?",
    "{n}. Do you get over to see {them} much?",
    "{n} \u2014 good going. What does {they} put it down to?",
)
# The noun a naming word can follow when the be-verb is left out, and the noun a name can sit
# straight after: "my daughters called amy", "our two kids are called tom and amy", "my son
# tom is 6". A plural is the person's own word for their people - "my daughters" - so the s is
# allowed on any of them rather than listed, and only the word after the naming word is checked
# as a name (`facts.a_name_could_be`), which is what keeps "my mum called yesterday" a day and
# "my boss called the plumber" a phone call.
# A word in the seat after "called" that is not a name however much it looks like one: a count
# of times ("my mum called twice") and a particle ("my dad called round") are closed classes, so
# they are read as classes rather than listed as phrases. Everything else is the store's own
# test, which is what makes "called amy" a name and "called the plumber" not.
NOT_A_NAME_AFTER_CALLED = frozenset("""one two three four five six seven eight nine ten
    eleven twelve once twice thrice again times in out round over back by up off through""".split())
THEIR_CALLED = re.compile(
    r"^my (?P<person>" + THEIR_PERSON + r")s? (?:is |are )?(?:called|named) "
    r"(?P<names>[a-z][a-z'\-]{1,14}(?: and [a-z][a-z'\-]{1,14})?)"
    r"(?: and (?:she|he|they)(?:'?s| is| are) (?:just |only |nearly )?(?P<age>\d{1,2}))?$")
THEIR_NAME_SO = re.compile(
    r"^my (?:" + THEIR_QUALIFIER + r")?(?P<person>" + THEIR_CHILD + r") (?P<name>[a-z][a-z'\-]{1,14}) "
    r"(?:is|is now|just turned|turns?) (?:just |only |nearly )?(?P<age>\d{1,2})$")
# What they are into: "my sister loves gardening", "my wife is into knitting", "my brother is mad
# about trains". The store files it and says it back - "Noted: your sister loves gardening." -
# which is the coldest reply in this file, and the fact is an invitation: a friend asks about the
# thing. The whole line has to be the liking, so "my son is 3 and loves dinosaurs" (two facts) and
# "my mum loves it when i visit" (no thing named) stay out.
THEIR_LIKING = re.compile(
    r"^my (?P<person>" + THEIR_PERSON + r")(?:'?s)? "
    r"(?:really |absolutely |totally |just |properly |so )?"
    r"(?:loves?|adores?|likes?|enjoys?|collects?|is into|is really into|is mad about|"
    r"is big on|is obsessed with|is a fan of|is a big fan of|is addicted to) "
    r"(?P<thing>[a-z][a-z '\-]{1,30})$")
# A liking with no thing in it is not an invitation to ask about the thing: "my mum loves it",
# "my wife loves me" and "my dad loves this" say something about the person and nothing a question
# about the thing could stand on.
NOT_A_THING = frozenset((
    "it", "this", "that", "them", "these", "those", "me", "you", "us", "him", "her", "his",
    "hers", "mine", "yours", "life", "everything", "anything",
))
# The thing is the end of the sentence, so a clause after the object means the object is not the
# whole of it: "my mum loves it when i visit" is about the visits, not about an "it when i visit".
THE_THING_IS_A_CLAUSE = (" when ", " when", " if ", " if", " because", " but ", " that ",
                         " until ", " after ", " before ")

# --- what one of their people cannot stand ---------------------------------------------------
# The other half of THEIR_LIKING, and the half that had nothing: "my kids dont like spice" comes
# back "Thanks for telling me - I'm here if you want to dig into any of that.", which is the line
# any message at all would get, and "my kids wont eat fish" fell to the answers module's search
# because of the word "eat". A dislike is the same kind of fact as a liking, so it gets the same
# kind of reply: the thing said back, and a question about it.
#
# The words a person uses for a no are a closed class - doesnt/dont like, wont eat, never drinks,
# cant stand, hates, refuses to touch - and the shape is the person's word, then the no, then the
# thing. "doesnt like it", "dont like two of them" and "dont like the new baby" name no thing and
# keep the reply they had.
THEIR_DISLIKE = re.compile(
    r"^my (?P<person>" + THEIR_PERSON + r")(?:'?s)?(?: really | absolutely | actually )?"
    r" (?:doesnt|does not|don'?t|do not|didnt|did not|wont|will not|wouldnt|never|"
    r"can'?t|cannot|refuses to|refused to)"
    r" (?:like|eat|touch|drink|have|take|stand|finish|wear|try|watch|read|go to|get on with)"
    r" (?P<thing>[a-z][a-z '\-]{1,30})$")
THEIR_HATE = re.compile(
    r"^my (?P<person>" + THEIR_PERSON + r")(?:'?s)?(?: really | absolutely | actually )?"
    r" (?:hates?|loathes?|detests?|can'?t stand|cannot stand|is not keen on|"
    r"isn'?t keen on|is scared of|is frightened of)"
    r" (?P<thing>[a-z][a-z '\-]{1,30})$")
# A taste is a thing off a plate or out of a cupboard, not a person and not a day of their week:
# "my kids dont like the new baby" is a family in trouble, and said back as "The new baby - what
# is it that gets them about it?" it would be a worse reply than the one it had.
NOT_A_TASTE_AS_A_THING = frozenset("""
    baby boy brother child children cousin dad daughter father gran grandad grandma grandpa
    granny husband kid kids mam mom mother mum nan nana nephew niece partner sister son wife
    job school work boss teacher shift money house home bed bedtime bath mornings nights
    mondays tuesdays wednesdays thursdays fridays saturdays sundays
""".split())
# The thing said back is a few words, not a clause: "doesnt like it when we argue" is about the
# arguing, and no pool here can say that well.
TASTE_TOO_LONG = 4
THEIR_DISLIKE_LINES = (
    "{Thing} \u2014 noted. Good to know for {them}.",
    "Fair enough \u2014 {thing} is not for {them}.",
    "{Thing} \u2014 noted, and {they} can steer round it.",
)
THEIR_HATE_LINES = (
    "{Thing} \u2014 fair enough, and {they} can steer round it.",
    "Hating {thing} is allowed, and {they} {are} in good company.",
    "{Thing} \u2014 noted, with sympathy for {them}.",
)


def _a_taste_they_refuse(clean, memory):
    """A reply to a line that is only what one of their people will not have, or None."""
    if not isinstance(clean, str) or "?" in clean:
        return None
    for pattern, pool in ((THEIR_DISLIKE, THEIR_DISLIKE_LINES), (THEIR_HATE, THEIR_HATE_LINES)):
        match = pattern.match(clean)
        if not match:
            continue
        thing = " ".join(match.group("thing").lower().split())
        # "the park" is the park and "a roast" is a roast: the article is not part of the thing
        # for the purpose of asking whether there is a thing here at all, and it is said back.
        bare = re.sub(r"^(?:the|a|an|his|her|their|its) ", "", thing)
        # A clause after the thing means the thing is not the whole of it.
        if any(hang in " " + thing + " " for hang in THE_THING_IS_A_CLAUSE):
            continue
        if not bare or len(bare.split()) > TASTE_TOO_LONG:
            continue
        if bare in NOT_A_THING or set(bare.split()) & NOT_A_TASTE_AS_A_THING:
            continue
        if bare.split()[0] in AGE_WORDS or bare.isdigit():
            continue
        # The thing is said back in the person's own words, so their "my" turns into the "your"
        # they would hear: "my kids dont like my cooking" is about their cooking.
        thing = re.sub(r"\b(?:my|our)\b", "your", thing)
        person = match.group("person").strip()
        return _pick_filled(pool, memory, clean,
                            lambda line, thing=thing, person=person: fill_person(
                                line.replace("{Thing}", thing[:1].upper() + thing[1:])
                                    .replace("{thing}", thing), person))
    return None


# Every line names the person in the fact and asks about them, because that is the thing the
# person has just put in front of you. The pronoun is the person's own word: "my sister" is she
# and "my brother" is he, and a word that states no gender - cousin, child, partner, parents -
# keeps "they", because guessing is worse than not saying it. Said of one sister as "them" the
# line was a mistake about the person they had just named: "my sister lives in leeds" ->
# "Leeds. How often do you get to see them?" (msg 52469 has the same thing in the Rome line).
#
# The word fixes the pronoun, the object and the verb that agrees with it, so the pools carry
# all of them: {they} {them} {their} {do} {are}.
SHE_PEOPLE = frozenset((
    "mum", "mom", "mam", "mother", "sister", "daughter", "wife", "niece", "gran", "granny",
    "nan", "nana", "grandma", "grandmother", "granddaughter", "aunt", "stepdaughter", "girl",
    "little girl",
))
HE_PEOPLE = frozenset((
    "dad", "father", "brother", "son", "husband", "nephew", "grandad", "grandpa", "grandfather",
    "grandson", "uncle", "stepson", "boy", "little boy", "little lad", "little man",
    "little fella", "little fellow", "wee man", "wee lad",
))
# "they" is the default: parents, kids, cousins, partners, and every word that does not say.
THEY_PERSON = ("they", "them", "their", "do", "are")
SHE_PERSON = ("she", "her", "her", "does", "is")
HE_PERSON = ("he", "him", "his", "does", "is")


def person_pronouns(person_word):
    """The pronoun, the object and the verb forms for the person word in the line."""
    word = str(person_word or "").strip().lower()
    if word in SHE_PEOPLE:
        return SHE_PERSON
    if word in HE_PEOPLE:
        return HE_PERSON
    return THEY_PERSON


def fill_person(line, person_word):
    """The pool line with the person's own pronouns and the verb that agrees with them.

    The placeholders come in both cases, because a person's pronoun and the verb that agrees
    with it can start a sentence as well as sit inside one: "{y}. {Do} {they} still let you fuss
    over {them}?" was "18 years old. Do he still let you fuss over him?" while a hard "Does"
    would have said "Does they" to a cousin. A line that starts on a placeholder is capitalised
    for the same reason.
    """
    they, them, their, do, are = person_pronouns(person_word)
    filled = (line.replace("{they}", they).replace("{them}", them).replace("{their}", their)
                  .replace("{do}", do).replace("{are}", are)
                  .replace("{They}", they.capitalize()).replace("{Them}", them.capitalize())
                  .replace("{Their}", their.capitalize()).replace("{Do}", do.capitalize())
                  .replace("{Are}", are.capitalize()))
    return filled


# How somebody was *with them* is not a fact about that person to file away. "my mum was funny
# with me" was answered "Noted: your mum was funny with you.", which is the store writing down a
# mood as though it were a trait, and "he snapped at me this morning" got "Thanks for telling me -
# I'm here if you want to dig into any of that". A friend says the thing that is true - it is
# unsettling when you do not know why - and asks the one question that helps, which is whether
# they know what set it off.
THEIR_MOOD_WITH_YOU = re.compile(
    r"\b(?:(?:my|our)\s+(?:\w+\s+){0,2}?)?(?:mum|mom|mam|mother|dad|father|husband|wife|partner|"
    r"boyfriend|girlfriend|sister|brother|son|daughter|friend|mate|boss|manager|colleague|"
    r"flatmate|housemate|neighbour|neighbor|nan|nana|gran|granny|grandma|grandad|grandpa|aunt|"
    r"uncle|cousin|he|she|they)\s+(?:was|were|is|are|has been|had been|'s been|been)\s+"
    r"(?:being\s+)?(?:funny|off|short|sharp|snappy|offhand|cold|cool|distant|offish|surly|cross|"
    r"irritable|grumpy|moody|brusque|abrupt|weird|odd|strange)\s+with\s+(?:me|us)\b"
    r"|\b(?:he|she|they|my\s+\w+)\s+snapped\s+at\s+me\b"
    r"|\b(?:he|she|they|my\s+\w+)\s+blanked\s+me\b"
    r"|\bgave\s+me\s+the\s+cold\s+shoulder\b", re.I)
THEIR_MOOD_WITH_YOU_LINES = (
    "Being funny with you and not saying why is unsettling. Do you know what set {them} off?",
    "That is an odd way to be with you. Is it a one-off, or has it been like this a while?",
    "You are left guessing when {they} {do} that. Did {they} say anything at all?",
    "Being got at without knowing why wears you down. What happened just before it?",
)


# The turn after: the person says how long or how often it has been going on. "it happens most
# weeks", "she has been like that all week", "it has been like that since june" were answered
# "Thanks for telling me - I'm here if you want to dig into any of that", which is the pool for a
# line the bot has understood nothing of. The line adds the one thing that matters about a mood
# that keeps coming back - it is not a bad afternoon - so the reply takes the length in.
GOING_ON = re.compile(
    r"^(?:(?:it|that|this)s?\s+)?(?:all|most|every)\s+(?:the\s+)?"
    r"(?:time|weeks?|weekends?|days?|nights?)\b"
    r"|\bits\s+been\s+(?:going\s+on|like\s+that|happening)\s+(?:for|since|all|most|every)\b"
    r"|\b(?:it|that|this|she|he|they)s?\s+(?:been|has\s+been|'s\s+been)\s+like\s+(?:that|this)\s+"
    r"(?:all|for|since)\b"
    r"|(?:it|that|this|she|he|they)\s+(?:happens|happened|does\s+(?:it|that)|is\s+like\s+that|"
    r"has\s+been\s+like\s+(?:that|this)|keeps?\s+happening|goes?\s+on)[^.!?]{0,26}?"
    r"\b(?:most|every|all)\s+(?:single\s+|other\s+)?(?:weeks?|weekends?|days?|nights?|mornings?|time|the\s+time)\b"
    r"|\b(?:she|he|they|it)\s+(?:has\s+been|had\s+been|'s\s+been|was|is)\s+like\s+(?:that|this)\s+"
    r"(?:all|for|since)\b"
    r"|\b(?:it|this|that)\s+(?:has\s+been|had\s+been|'s\s+been)\s+going\s+on\s+(?:for|since)\b"
    r"|\b(?:it|this|that)\s+(?:has\s+been|had\s+been|'s\s+been)\s+for\s+"
    r"(?:about\s+)?(?:\d+|a|an|two|three|four|five|six|seven|eight|nine|ten|a\s+few|"
    r"a\s+couple\s+of|several)\s+(?:weeks?|months?|years?|days?)\b"
    r"|\b(?:for|since)\s+(?:about\s+)?(?:\d+|a|an|two|three|four|five|six|seven|eight|nine|ten|"
    r"a\s+few|a\s+couple\s+of|several)\s+(?:weeks?|months?|years?|days?)\b"
    r"|\bsince\s+(?:january|february|march|april|may|june|july|august|september|october|"
    r"november|december|christmas|last\s+(?:week|month|year|summer|autumn|winter|spring))\b",
    re.I)
GOING_ON_LINES = (
    "That long is a lot of guessing. Have you asked {them} straight out?",
    "Being off with you for that long stops being a mood and starts being a habit. Have you said "
    "anything to {them}?",
    "If it has been going on that long, it is worth saying to {them}, not sitting on. "
    "What would you want to say?",
)


def their_mood_going_on_reply_for(clean, memory):
    """"it happens most weeks" after a mood with them, or None to leave the line to the caller."""
    if not clean or "?" in clean:
        return None
    kept = (memory or {}).get("mood_with_you")
    if not isinstance(kept, dict):
        return None
    turns = (memory or {}).get("turns") or []
    # The note is for the turn right after the mood, not for the rest of the chat. The count is
    # read loosely because the turn being answered may already be in the history, and the pair
    # before it may not be: the window is the next line, or the one after that.
    if not 0 <= len(turns) - int(kept.get("at") or 0) <= 2:
        return None
    if not GOING_ON.search(clean):
        return None
    if _has_phrase(clean, CRISIS):
        return None
    person = _pronoun_person(kept.get("person") or "")
    return _pick_filled(GOING_ON_LINES, memory, clean,
                        lambda line: fill_person(line, person))


def _pronoun_person(person):
    """The relation whose pronouns are the ones in the line: "he snapped" is a husband here.

    The pronoun sets in this file are keyed by the relation ("husband", "wife"), so a bare "he"
    filled every line with "they" - "You are left guessing when they do that" about a line that
    said he. Anything else is passed through as it is (an empty word means "they").
    """
    return {"he": "husband", "she": "wife", "they": ""}.get(person, person)


def their_mood_with_you_reply_for(clean, words, memory):
    """A reply to "somebody was off with me", or None to leave the line to whoever owns it."""
    if not clean or "?" in clean:
        return None
    match = THEIR_MOOD_WITH_YOU.search(clean)
    if not match:
        return None
    said = " ".join(clean.split())
    if _has_phrase(said, CRISIS) or _has_phrase(said, NOT_PLAIN):
        return None
    person = ""
    for word in ("mum", "mom", "mam", "mother", "dad", "father", "husband", "wife", "partner",
                 "boyfriend", "girlfriend", "sister", "brother", "son", "daughter", "friend",
                 "mate", "boss", "manager", "colleague", "flatmate", "housemate", "neighbour",
                 "neighbor", "nan", "nana", "gran", "granny", "grandma", "grandad", "grandpa",
                 "aunt", "uncle", "cousin", "he", "she", "they"):
        if re.search(r"\b" + word + r"\b", said):
            person = word
            break
    # "he snapped at me" and "she blanked me" name the person by pronoun, and the pronoun sets in
    # this file are keyed by the relation ("husband", "wife"), so the pronoun is read as the one
    # relation whose pronouns are its own. Without this a bare "he" filled every line with "they":
    # "You are left guessing when they do that" about a line that said he.
    person = _pronoun_person(person)
    if isinstance(memory, dict):
        # Kept for one turn, so the length of it ("it happens most weeks") is answered on the line
        # after, which is the turn a person says it on.
        memory["mood_with_you"] = {"person": person, "at": len(memory.get("turns") or [])}
    return _pick_filled(THEIR_MOOD_WITH_YOU_LINES, memory, clean,
                        lambda line: fill_person(line, person))


THEIR_NAME_LINES = (
    "{name} — that is a good one. Where did it come from?",
    "{name}. Do you call {them} {name} all the time, or does it get shortened?",
    "{name}. Who picked it?",
)
# The third line used to ask what the child makes of their own name, which was written for a
# child old enough to have a view of it and read badly for every smaller one: "my baby is called
# rose" got "Rose — noted with care. What do they make of it?", and "my little girl is
# called ivy" the same with "she". A baby has no view of its own name - nobody has, until they
# are old enough to have been teased about it. Who chose the name is a question every parent can
# answer, of a newborn and of a nine-year-old alike, so the line asks that and the pool stays one
# pool instead of splitting by the word a parent uses for the child.
# ...for a child. A grown relation's name was not chosen by the person in front of you, so the
# three lines above say the wrong thing: "my wife is called anna" was answered "Anna — that is a
# good one. Where did it come from?", which is what you say about a baby, and "noted with care.
# What does she make of it?" is a question about her own name. The grown pool asks the same
# interest as history or as a shortening, which is what there is to ask about a name in use.
# Every line has to fit a "they" as well as a "she", so the verb comes from the person word
# ({Do}, and the agreeing form in the other places) and the third line names no verb at all:
# "Does they get called anything for short?" came out for a partner and a cousin.
THEIR_NAME_GROWN_LINES = (
    "{name} — that's a lovely name. Is it a family one?",
    "{name}. {Do} {they} get called anything for short?",
    "{name} — nice. Is there a story behind it?",
)
# The person words that are a child rather than an adult (see THEIR_CHILD, which is the same list
# as a pattern for the age shapes).
A_CHILD_NAMED = frozenset(THEIR_CHILD.strip("(?:)").split("|"))
THEIR_NAME_AGE_LINES = (
    "{name} at {n} — that is a good age. What {are} {they} into at the moment?",
    "{name}, {n}. What {are} {they} like just now?",
)
# Two names in one line are a household, so the reply talks about the pair of them. It asks the
# same thing a single name asks - how old, what are they like - because that is what comes next
# in the conversation, and it says they instead of guessing, the way the other pools do.
THEIR_NAMES_LINES = (
    "{names} — two good names. How old are they?",
    "{names}. What are they like, the pair of them?",
    "{names} — a houseful, then. How old are they?",
)
# An age is a different conversation at four, at ten and at twenty, and one pool for all of
# them says "4 is the age of asking why" to somebody's grown-up son. So the band is the pool:
# a baby in months, a small child, a school-age child, and a grown one.
# A one-year-old is "1 year old" and a four-month-old is "4 months", so the age arrives
# formatted: {y} is "4 years old", {m} is "4 months", and {n} is the bare number for the lines
# that read better without the noun.
THEIR_BABY_LINES = (
    "{m} — are you getting any sleep?",
    "{m} old. Is it the nights that are hardest, or the days?",
    "{m} — that is the age everything goes in the mouth. Is that where you are?",
)
THEIR_SMALL_LINES = (
    "{n} is a busy age. What {are} {they} into at the moment?",
    "{n} — that is the age of asking why about everything. Does that sound right?",
    "{y}. Is it easier than the baby stage, or harder?",
)
# A band is the whole of its pool: every line has to fit a child of five as well as a child of
# twelve. "Do they still want you around, or are you embarrassing now?" is the teenager's line,
# so it lives with the teenagers: a five-year-old got it, and that is not a thought anybody has
# about a five-year-old.
THEIR_CHILD_LINES = (
    "{n} is a good age. What {are} {they} into at the moment?",
    "{y}. Is school going all right for {them}?",
    "{n} — what are the days like with {them} just now?",
)
THEIR_TEEN_LINES = (
    "{n} — is that a good age or a hard one?",
    "{y}. What {are} {they} like just now?",
    "{n} — do you get much of a look in these days?",
    "{n} — {do} {they} still want you around, or are you embarrassing now?",
)
THEIR_GROWN_LINES = (
    "{n} — grown, then. Still at home?",
    "{n} is a proper landmark. What {are} {they} doing now?",
    "{y}. {Do} {they} still let you fuss over {them}?",
)
THEIR_PLACE_LINES = (
    "{place}. How often do you get to see {them}?",
    "{place} — {do} {they} ever come to you instead?",
    "{place}. Do you get up there much, or is it {them} coming to you?",
)
# The thing is said back so the person knows it was heard, and the question is about them rather
# than about the hobby: a person telling you their sister loves gardening wants to talk about
# their sister.
THEIR_LIKING_LINES = (
    "{thing}. What got {them} into it?",
    "{thing} \u2014 good one. Is it a long-standing thing with {them}?",
    "{thing}. Do you get roped into it with {them} at all?",
)


# A place said with "the" in front keeps it, and a country written as two or three letters is a
# code rather than a word: "the us" is "the US", not a town called The Us. Everything else is
# title case, which is what a person would write.
PLACE_CODES = {"us": "US", "usa": "USA", "uk": "UK", "uae": "UAE", "eu": "EU", "nz": "NZ",
               "nyc": "NYC", "drc": "DRC"}


def name_a_place(said):
    """The place as a person would write it, for a pool line that opens with it."""
    place = " ".join(said.split())
    lead = ""
    if place.lower().startswith("the ") and len(place) > 4:
        lead, place = "The ", place[4:]
    return lead + " ".join(PLACE_CODES.get(word.lower(), word.title()) for word in place.split())


def fill_age(line, n, months=False):
    """The pool line with the age filled in: a one-year-old is "1 year old", not "1 years"."""
    years = f"{n} year{'s' if n != 1 else ''} old"
    count = f"{n} month{'s' if n != 1 else ''}" if months else years
    return line.replace("{y}", years).replace("{m}", count).replace("{n}", str(n))


def _age_pool(n, months=False):
    """The pool for a child of this age: a baby is a different conversation from a grown one."""
    if months and n <= 30:
        return THEIR_BABY_LINES
    if n < 5:
        return THEIR_SMALL_LINES
    if n < 13:
        return THEIR_CHILD_LINES
    if n < 18:
        return THEIR_TEEN_LINES
    return THEIR_GROWN_LINES


def _the_job_in(phrase):
    """The job the phrase names, written the way a person would, or None if it names no job.

    "nurse" and "builder" are on the store's list. "care assistant" is the same trade with a word
    in front, so a two-word phrase counts when one of its words does. "of thirty years" is not a
    job however the line is read, and more than two words is a description, not a trade.
    """
    words = [w for w in re.split(r"[\s'-]+", str(phrase or "").strip()) if w]
    if not words or len(words) > 2:
        return None
    if not set(words) & facts.JOB_WORDS:
        return None
    return " ".join(words).title()


def _pick_filled(lines, memory, clean, fill):
    """One of the pool, chosen after the line is filled in.

    The pools carry the person's word, the number and the pronouns as placeholders, and the picker
    keeps the reply just given out of the choice. Choosing a template and filling it afterwards
    hides the line from the picker, so "my brother is a chef" then "he works in town" asked "what
    does a normal day look like for him?" twice running. Filling first, then choosing, is the same
    reply with the repeat actually visible to it.
    """
    return pick([fill(line) for line in lines], memory, clean)


# A child the chat already knows, named on its own with a new age: "my kids are ada 7 and sam 4"
# then "ada is 8". The store reads the name against the child it holds and puts the age right -
# the name alone is enough - but nothing composed a reply, so the line fell to the floor and the
# bot asked who 8 was about a child it had just corrected in its own memory. That question is
# right for a figure the chat cannot place ("hes 9" as a first line) and wrong for one it can.
A_HELD_NAME_AND_AN_AGE = re.compile(
    r"^(?P<name>[a-z][a-z'\-]{1,19}) (?:is|is now|will be|turns|just turned) "
    r"(?:just |only |nearly |about )?(?P<n>\d{1,2}|" + "|".join(AGE_WORDS) + r")"
    r"(?:\s?(?:years?|yrs?\.?|y/o|yo|months?|mths?\.?|mth)(?:[ -]?old)?| old| now)?$")
# A birthday still to come ("ada is 8 next week") is a thing somebody is looking forward to, and
# the reader that answers it ends on the coming day rather than on a figure to put right.
A_MILESTONE_TAIL = re.compile(r"\b(?:next|on|this|in)\s+(?:week|month|year|monday|tuesday|wednesday|"
                              r"thursday|friday|saturday|sunday|january|february|march|april|"
                              r"may|june|july|august|september|october|november|december)\b")
# Saying it back with the age the bot had is the whole of the reply: it shows the correction was
# taken, names the child, and does not ask a question the person has already answered.
AGE_PUT_RIGHT = (
    "{name} at {n} now — I had {old}.",
    "{name}'s {n}, then, not {old} — got it.",
    "{name} at {n}. I had {old}, so that is the one thing I will change.",
)
# The same line when the chat holds the name and no age for it yet ("my son is called sam" then
# "sam is 8"), and when it already holds the age just said ("ada is 7" of a child the chat has at
# 7). In both the bot knows the child, so neither is a figure it cannot place.
AGE_FIRST_TOLD = (
    "{name} at {n}, then.",
    "{name}, {n} — good to know.",
    "{name} at {n}. That is one to remember.",
)
AGE_ALREADY_HAD = (
    "{name} at {n} — that is what I had.",
    "{name}, {n}. I had that already, so nothing changes.",
)


def _the_people_in(memory, name):
    """Every entry the store holds for that name, the people and the animals."""
    held = memory if isinstance(memory, dict) else {}
    found = []
    for entry in held.get("others") or []:
        if isinstance(entry, dict) and str(entry.get("name") or "").strip().lower() == name:
            found.append(entry)
    theirs = held.get("user") if isinstance(held.get("user"), dict) else {}
    for entry in theirs.get("pets") or []:
        if isinstance(entry, dict) and str(entry.get("name") or "").strip().lower() == name:
            found.append(entry)
    return found


def _the_age_i_had(name, memory):
    """The age an earlier turn gave that name, or None: the store overwrites it in place."""
    held = memory if isinstance(memory, dict) else {}
    old = None
    for fact in held.get("facts_log") or []:
        value = fact.get("value") if isinstance(fact, dict) else None
        if not isinstance(value, dict):
            continue
        if str(value.get("name") or "").strip().lower() != name:
            continue
        if isinstance(value.get("age"), int) and value["age"]:
            old = value["age"]
    return old


def _an_age_put_right(clean, memory):
    """A known child or animal, named alone with a new age, said back with the age it had."""
    if A_MILESTONE_TAIL.search(clean or ""):
        return None
    match = A_HELD_NAME_AND_AN_AGE.match(clean or "")
    if not match:
        return None
    name = match.group("name")
    found = _the_people_in(memory, name)
    if not found:
        return None
    said = match.group("n")
    n = int(said) if said.isdigit() else AGE_WORDS[said]
    if not n or n > 120:
        return None
    spelled = str(found[0].get("name") or name).strip().title()
    old = _the_age_i_had(name, memory)
    if not isinstance(old, int) or not old:
        return pick(AGE_FIRST_TOLD, memory, clean).format(name=spelled, n=n)
    if old == n:
        return pick(AGE_ALREADY_HAD, memory, clean).format(name=spelled, n=n)
    return pick(AGE_PUT_RIGHT, memory, clean).format(name=spelled, n=n, old=old)


def their_people_reply_for(clean, words, memory):
    """A reply to a plain fact about one of their people, or None to leave it to the caller."""
    if not clean or "?" in clean:
        return None
    # A fact about one of their people is as often said after a leader as on its own: "and my sons
    # called tom, hes 9", "oh and my daughter is called mia". Every shape below starts at "my", so
    # the leader hid the whole family of them and the line fell to a line that fits any message.
    # The reading of a leader is the shared one (`normalize.without_leaders`), not a list here.
    clean = without_leaders(clean) or clean
    if set(words) & NOT_PLAIN or _has_phrase(clean, CRISIS):
        return None
    refused = _a_taste_they_refuse(clean, memory)
    if refused:
        return refused

    put_right = _an_age_put_right(clean, memory)
    if put_right:
        return put_right
    match = THEIR_ELDER_AGE.match(clean)
    if match:
        said = match.group("n")
        n = int(said) if said.isdigit() else AGE_WORDS[said]
        return _pick_filled(THEIR_ELDER_LINES, memory, clean,
                            lambda line: fill_person(fill_age(line, n), match.group("person")))
    match = THEIR_JOB.match(clean)
    if match:
        job = _the_job_in(match.group("phrase"))
        if job:
            return _pick_filled(THEIR_JOB_LINES, memory, clean,
                                lambda line: fill_person(line.replace("{Job}", job),
                                                         match.group("person")))
    match = THEIR_PLACE.match(clean)
    if match:
        place = name_a_place(match.group("place"))
        return _pick_filled(THEIR_PLACE_LINES, memory, clean,
                            lambda line: fill_person(line.replace("{place}", place),
                                                     match.group("person")))
    match = THEIR_NAME_AGE.match(clean)
    if match:
        name = match.group("name").strip().title()
        n = str(int(match.group("age")))
        return _pick_filled(THEIR_NAME_AGE_LINES, memory, clean,
                            lambda line: fill_person(line.replace("{name}", name)
                                                         .replace("{n}", n),
                                                     match.group("person")))
    match = THEIR_AGE.match(clean)
    if match:
        months = bool(re.search(r"months?|mths?|\bmth\b", match.group(0)))
        said = match.group("n")
        n = int(said) if said.isdigit() else AGE_WORDS[said]
        if (not months and said.isdigit() and match.group("person") in BABY_WORDS
                and not YEAR_UNIT.search(match.group(0))):
            # Two things keep this from swallowing the years: only a typed digit counts ("my baby
            # is one" is the year the child is in, said in words), and a unit of its own wins
            # ("my baby is 2yo" is two years old). Bare "my baby is 3" is three months.
            if n > 24:
                return None
            months = True
        return _pick_filled(_age_pool(n, months), memory, clean,
                            lambda line: fill_person(fill_age(line, n, months),
                                                     match.group("person")))
    match = THEIR_NAME.match(clean)
    if match:
        name = match.group("name").strip().title()
        person = (match.group("person") or "").strip().lower()
        pool = THEIR_NAME_LINES if person in A_CHILD_NAMED else THEIR_NAME_GROWN_LINES
        return _pick_filled(pool, memory, clean,
                            lambda line: fill_person(line.replace("{name}", name),
                                                     match.group("person")))
        line = pick(THEIR_NAME_LINES, memory, clean).replace("{name}", name)
        return fill_person(line, match.group("person"))
    # The same two facts with the be-verb left out. These are read last, so every shape above
    # keeps its own reply exactly, and a line that only reaches here is one the bot had nothing
    # for: "my daughters called amy" was answered from the account-of-the-day pool - a naming
    # is not a day - and "my son tom is 6" was said back as a receipt.
    match = THEIR_NAME_SO.match(clean)
    if match:
        name = match.group("name").strip()
        if facts.a_name_could_be(name.lower()):
            line = pick(THEIR_NAME_AGE_LINES, memory, clean)
            line = (line.replace("{name}", name.title())
                        .replace("{n}", str(int(match.group("age")))))
            return fill_person(line, match.group("person"))
    match = THEIR_CALLED.match(clean)
    if match:
        names = [word.strip() for word in match.group("names").split(" and ")]
        if all(facts.a_name_could_be(word.lower())
               and word.lower() not in NOT_A_NAME_AFTER_CALLED
               and not word.isdigit() for word in names):
            said = " and ".join(word.title() for word in names)
            if len(names) == 2:
                return pick(THEIR_NAMES_LINES, memory, clean).replace("{names}", said)
            if match.group("age"):
                line = pick(THEIR_NAME_AGE_LINES, memory, clean)
                return (fill_person(line, match.group("person"))
                        .replace("{name}", said)
                        .replace("{n}", str(int(match.group("age")))))
            line = pick(THEIR_NAME_LINES, memory, clean).replace("{name}", said)
            return fill_person(line, match.group("person"))
    match = THEIR_LIKING.match(clean)
    if match:
        thing = match.group("thing").strip()
        if thing.split()[0] in NOT_A_THING:
            return None
        if any(word in f" {thing} " for word in THE_THING_IS_A_CLAUSE):
            return None
        said = thing[:1].upper() + thing[1:]
        return _pick_filled(THEIR_LIKING_LINES, memory, clean,
                            lambda line: fill_person(line.replace("{thing}", said),
                                                     match.group("person")))
    return None



# --- something of theirs, said as a plain fact -------------------------------------------
# "ive got a spare room", "weve got a greenhouse", "ive got a shed", "ive got a big garden" are
# facts about a life, not days that happened. They were answered as days: "How was it, overall?",
# "Nice one. How did the rest of it go?", "Good to hear. What was the best bit?" - the small-day
# pool reads the possessive "got" as a past doing, and a cheer at a garden is worse than no reply
# at all. Said back as a receipt ("Noted: you've got a spare room.") it names the thing and asks
# nothing. What the reply does here is say the one true thing about the kind of thing they have
# and then ask the question that follows from it, which is what a friend does with the fact.
#
# Two classes only, and whole words, so nothing is read as this by accident:
OWN_HAVE = re.compile(
    r"^(?:i|we)(?:'ve|ve)\s+got\s+(?P<one>.+)$"
    r"|^(?:i|we)\s+(?:have|has)\s+(?:got\s+)?(?P<two>[^?]+)$")
# A thing they have that is a space: the reply says what a space earns you, and what it is for.
OWN_SPACES = frozenset("""
room bedroom kitchen garage greenhouse shed garden allotment plot patch balcony patio loft cellar
basement workshop study conservatory hut outbuilding yard driveway orchard pond
""".split())
# A thing they have that is kit: the reply says what the thing is actually good for.
OWN_KIT = frozenset("""
piano guitar keyboard drums telescope bike bikes motorbike car caravan boat canoe kayak
netflix projector printer turntable bench washing machine dishwasher
""".split())
# The things whose name is two words: kept apart because a frozenset of words cannot hold "drum
# kit", and the tail of the phrase is what is matched anyway.
OWN_KIT_NAMES = frozenset(("drum kit", "record player", "sewing machine", "hot tub",
                           "log burner", "solar panels", "summer house"))
# What is true of that thing, which is the part a receipt leaves out. Written as the start of a
# sentence, so {A} and {thing} are filled the way the person said them.
OWN_FACTS = {
    "room": "{A} {thing} earns its keep as a bed, a desk or storage, and it is cheapest left "
            "as two of those",
    "bedroom": "a spare bedroom earns its keep as a bed, a desk or storage",
    "kitchen": "{A} {thing} earns its space back: a good surface and one heavy pan do more than "
               "a cupboard of gadgets",
    "garage": "{A} {thing} is a store that can also take a car, and most of them end up too full "
              "for one",
    "greenhouse": "{A} {thing} buys weeks at both ends of the season - tomatoes ripen in it and "
                  "seedlings stop going leggy on a windowsill",
    "shed": "{A} {thing} is where the tools stop rusting and the mower stops being in the way",
    "garden": "{A} {thing} is the cheapest ground you will ever get for potatoes, beans and "
              "salad",
    "allotment": "{A} {thing} is hard work the first year while the ground is cleared, and much "
                 "less after that",
    "plot": "{A} {thing} is hard work the first year while the ground is cleared, and much less "
            "after",
    "patch": "{A} {thing} that size grows salad, herbs and a few beans, which is most of what "
             "people actually eat",
    "balcony": "{A} {thing} grows more than people expect: tomatoes, herbs and salad all do well "
               "in pots out there",
    "patio": "{A} {thing} earns its keep in pots - tomatoes and herbs do better against a warm "
             "wall",
    "loft": "{A} {thing} is the cheapest storage a house has, as long as the damp stays out of it",
    "cellar": "{A} {thing} keeps a steady cool temperature, which is what potatoes, squash and "
              "wine want",
    "basement": "{A} {thing} keeps a steady cool temperature, which is what potatoes and squash "
                "want",
    "workshop": "{A} {thing} is worth having for the bench more than the tools",
    "study": "{A} {thing} is mostly a door that shuts: a desk and a quiet hour do the rest",
    "conservatory": "{A} {thing} gets hot in summer and cold in winter, so it works best with "
                    "plants in it and a chair",
    "piano": "{A} {thing} is the easiest instrument to start from nothing on, and an acoustic one "
             "wants tuning about once a year",
    "guitar": "{A} {thing} is the one you can pick up for ten minutes and put down again, which "
              "is how people actually learn",
    "keyboard": "{A} {thing} is the quiet way to practise - headphones and nobody in the house "
                "hears it",
    "drums": "drums are the loudest hobby a house can hold, so an electric kit and headphones "
             "keep the neighbours onside",
    "drum kit": "drums are the loudest hobby a house can hold, so an electric kit and headphones "
                "keep the neighbours onside",
    "bike": "{A} {thing} beats the car for anything under a couple of miles once parking is "
            "counted",
    "bikes": "bikes beat the car for short trips once parking is counted, and two of them fit "
             "where one car will not",
    "motorbike": "{A} {thing} is the cheap way through traffic and the expensive way to stay warm "
                 "and dry",
    "caravan": "{A} {thing} saves the hotel bill and costs you the towing, which is why most of "
               "them sit for months at a time",
    "boat": "{A} {thing} is a hobby in itself - the upkeep is the part nobody warns you about",
    "canoe": "a canoe gets you on water a boat cannot reach, and it goes on the roof of a car",
    "kayak": "a kayak gets you on water a boat cannot reach, and it goes on the roof of a car",
    "netflix": "the good part of netflix is that a film night costs nothing past the "
               "subscription, and you can stop halfway and finish it tomorrow",
    "projector": "{A} {thing} turns a blank wall into a big screen, and it wants the room "
                 "properly dark",
    "sewing machine": "{A} {thing} pays for itself on repairs - a hem or a zip costs more to have "
                      "done than the machine did",
    "printer": "{A} {thing} earns its space on the parts nobody sells any more, not on ornaments",
    "record player": "records are the format that makes you listen to a whole side",
    "turntable": "records are the format that makes you listen to a whole side",
    "pond": "{A} {thing} brings frogs and birds in and then more or less runs itself once the "
            "plants are in",
    "bench": "{A} {thing} is where a hobby gets done properly, and one good vice is worth more "
             "than the rest of it",
    "car": "{A} {thing} costs more to keep than people plan for, and the short trips are what "
           "wear it hardest",
    "washing machine": "{A} {thing} is worth mending once before it is replaced - the pump and "
                       "the door seal are the two that go, and both are cheap parts",
    "dishwasher": "{A} {thing} uses less water than washing up by hand, and the salt is the part "
                  "people forget",
    "hot tub": "{A} {thing} costs more to run than to buy - the heater and the chemicals are the "
               "bill nobody plans for",
    "log burner": "{A} {thing} heats the one room it is in well, and it wants dry wood or the "
                  "chimney soots up",
    "solar panels": "solar panels pay back over something like ten years on a roof that "
                    "faces the sun, and much less on one that does not",
    "summer house": "{A} {thing} is a room the garden gets three months out of, so treat it like a "
                    "shed and keep the damp out",
}
# A space or a piece of kit with no fact of its own: the true thing about both is that they take
# the work nobody wants in the middle of the house.
OWN_SPACES_PLAIN = ("{A} {thing} takes the mess and the work out of the middle of the house, "
                    "which is what makes it worth having")
OWN_KIT_PLAIN = "{A} {thing} is worth owning rather than borrowing, which is the point of it"
# The fuel a car runs on changes which fact about it is true, so it is read off the line.
OWN_ELECTRIC = re.compile(r"\b(?:electric|electrical|ev|hybrid)\b")
OWN_ELECTRIC_CAR = ("{A} {thing} is cheapest on the short trips that wear a petrol one out, and "
                    "the cold and a motorway run are what use the charge up fastest")
# One question, after the fact that earns it. The same pool for both classes: what a person does
# with a space and whether a piece of kit gets used are the same two questions.
OWN_ASKS = (
    "What do you use it for?",
    "What have you done with it so far?",
    "Is it doing the job you wanted?",
    "What would you change about it?",
)
OWN_KIT_ASKS = (
    "Does it get much use?",
    "How long have you had it?",
    "Is it what you hoped for?",
    "Has it been worth what it cost?",
)
# "a good one", "a lot of", a person, or a fault - each is another reader's line, and a fault in
# particular is not a thing to ask what it is for.
OWN_NOT_THE_THING = re.compile(
    r"\b(?:problem|idea|lot|few|bit|chance|job|question|go|look|word|feeling|guess|break|"
    r"rest|while|minute|moment|day|week|month|year|time|filo|hint|tip|note|deal|point|reason|"
    r"choice|decision|say|think|try|best|crack|go)\b")
# "and" joins two possessions, and the fact is only ever about one of them. A contrast is the
# same shape and worse: "a shed but no garden" points the garden fact at a person who has no
# garden, which is the one thing a reply here must never do.
OWN_TWO_THINGS = re.compile(
    r"\b(?:and|or|plus|also|with)\b|&|/|,|"
    r"\b(?:but|no|not|never|without|except|apart from|instead of|rather than)\b")
OWN_FAULT = re.compile(
    r"\b(?:leak\w*|broken|broke\w*|cracked|cracks|blocked|faulty|fault|stopped working|"
    r"not working|dead|damp|mould|mold|smell\w*|flood\w*|noisy|rattl\w*|jammed|stuck|"
    r"cold|flu|bug|temperature|cough|sore|ache|pain|migraine|rash|infection|sick)\b")
# A day or a time in the line makes it an arrangement ("ive got a long drive on friday"), which
# another reader answers: what they have is not a thing to ask what it is for.
OWN_TIME = re.compile(
    r"\b(?:today|tonight|tomorrow|morning|afternoon|evening|night|weekend|monday|tuesday|"
    r"wednesday|thursday|friday|saturday|sunday|week|month|year|o'clock)\b")
# The small words a person wraps the thing in: "a small patch by the fence", "some room at the
# back", "a spare room upstairs". They are dropped so the thing itself is what is matched.
OWN_ARTICLE = ("a ", "an ", "the ", "one ", "two ", "three ", "four ", "some ", "another ")
OWN_TAIL = re.compile(
    r"\s+(?:by the .*|at the .*|in the .*|out the .*|out back|in back|upstairs|downstairs|"
    r"out front|round the .*|down the .*)$")


def _the_thing_they_have(clean):
    """The thing the line says they have, and which class it is in, or None."""
    said = " ".join(str(clean or "").lower().strip().rstrip(".!,").split())
    if not said or "?" in said:
        return None
    match = OWN_HAVE.match(said)
    if not match:
        return None
    thing = (match.group("one") or match.group("two") or "").strip()
    for article in OWN_ARTICLE:
        if thing.startswith(article):
            thing = thing[len(article):]
            break
    thing = OWN_TAIL.sub("", thing).strip()
    words = thing.split()
    if not words or len(words) > 4:
        return None
    if OWN_NOT_THE_THING.search(thing) or OWN_FAULT.search(thing) or OWN_TIME.search(thing):
        return None
    # Two things in one line ("ive got a car and a bike") are two facts, and a sentence built from
    # one of them quotes the other: "A car and a bike beats the car".
    if OWN_TWO_THINGS.search(thing):
        return None
    # The thing is the head, not a word in front of it: "the shed key" and "a garden table" are not
    # a shed and a garden, so the class comes from the tail of the phrase, not from any word in it.
    key = _the_class_word(thing)
    if not key:
        return None
    return thing, ("space" if key in OWN_SPACES else "kit")


def _the_class_word(thing):
    """The longest ending of the phrase that names a space or a piece of kit, or "".

    Longest first, so "sewing machine" is not read as a machine and "record player" is not read as
    a player - the two-word names are things of their own.
    """
    words = str(thing or "").split()
    for size in (3, 2, 1):
        if len(words) >= size:
            tail = " ".join(words[-size:])
            if (tail in OWN_SPACES or tail in OWN_KIT or tail in OWN_KIT_NAMES
                    or tail in OWN_FACTS):
                return tail
    return ""


def _article(thing):
    """A or An, by the sound the first word makes: "an allotment", "a spare room"."""
    word = str(thing or "").strip().lower()
    if not word:
        return "A"
    if word[0] in "aeiou" and not word.startswith(("one", "uni", "use", "euro")):
        return "An"
    return "A"


def _the_fact_about(thing, kind):
    """The one true thing about this kind of thing, filled in the way the person said it.

    Matched on the head noun, so "a small patch" finds the patch, "the spare room upstairs" finds
    the room and "a big garden" finds the garden. With no fact of its own the class line stands,
    because a reply that only asks a question is not an answer.
    """
    article = _article(thing)
    key = _the_class_word(thing) or ""
    fact = OWN_FACTS.get(key)
    # The kind of car the person named decides which fact is true of it: an electric one is the
    # opposite way round from a petrol one on short trips and long runs.
    if key == "car" and OWN_ELECTRIC.search(thing):
        fact = OWN_ELECTRIC_CAR
    if not fact:
        fact = OWN_SPACES_PLAIN if kind == "space" else OWN_KIT_PLAIN
    fact = fact.replace("{A}", article).replace("{thing}", thing)
    return fact


def _capped(line):
    return line[0].upper() + line[1:] if line else line


def a_thing_of_theirs_reply_for(clean, words, memory):
    """A reply to a plain fact about a thing they have, or None to leave it to the caller."""
    if not clean or "?" in clean:
        return None
    if set(words) & NOT_PLAIN or _has_phrase(clean, CRISIS):
        return None
    found = _the_thing_they_have(clean)
    if not found:
        return None
    thing, kind = found
    fact = _capped(_the_fact_about(thing, kind))
    asks = OWN_ASKS if kind == "space" else OWN_KIT_ASKS
    return _pick_filled([f"{fact}. {ask}" for ask in asks], memory, clean, lambda line: line)

# --- a relationship said to be in trouble -------------------------------------------------
# "my marriage is on the rocks", "me and my husband barely talk", "things are bad with my wife",
# "my mum and i dont get on". These are not the plain facts above: the store files one as a fact
# and says it back - "Noted: things are bad with your wife." - which is the coldest line in this
# file, and it is not a thing to take an interest in like a birthday. What a friend answers is the
# one question about the two of them. The **trouble words** decide it, never the person on his or
# her own: "my wife works away" is a plain fact, "my wife and i barely talk" is this. A body, an
# injury, a drink, a fist or a death in the line belongs to safety or to loss, and an affair or a
# divorce has its own weighing (the whole of that turn is a decision, not a question about it).
_RELATION_PERSON = (r"(?:mum|mom|mam|mother|dad|father|son|daughter|child|kid|partner|husband|"
                    r"wife|boyfriend|girlfriend|fiance|fiancee|ex|sister|brother|best friend|"
                    r"bestie|friend|flatmate|housemate|mother in law|father in law|in laws)")
# The marriage itself, which names no person and still needs the same question.
MARRIAGE_IN_TROUBLE = re.compile(
    r"\b(?:my|our)\s+(?:marriage|relationship)\s+(?:is|has|feels)\s+(?:on the rocks|rocky|"
    r"in trouble|in a bad way|falling apart|a mess|not in a good place|over|dead)\b")
BAD_WITH_THEM = re.compile(
    r"\bthings (?:are|have been|arent|are not|aint)\s+(?:bad|rough|hard|rubbish|terrible|awful|"
    r"not good|not great|not the same)\s+(?:with|between)\s+(?:my|our)\s+(%s)\b" % _RELATION_PERSON)
# The quiet between two people, said from either side: "me and my husband barely talk", "my mum
# and i never talk any more", "we hardly speak".
QUIET_BETWEEN_THEM = re.compile(
    r"\b(?:me and|i and|myself and)\s+(?:my|our)\s+(%s)\s+(?:barely|hardly|never)\s+"
    r"(?:talk|speak)\b"
    r"|\b(?:my|our)\s+(%s)\s+and\s+i\s+(?:barely|hardly|never|dont|don't|do not)\s+"
    r"(?:talk|speak|get on)\b"
    r"|\bwe\s+(?:barely|hardly|never)\s+(?:talk|speak)\b"
    r"|\b(?:my|our)\s+(%s)\s+(?:is|has been|seems|feels|sounds)\s+(?:distant|cold|withdrawn|"
    r"off with me|cold with me|distant with me)\b"
    % (_RELATION_PERSON, _RELATION_PERSON, _RELATION_PERSON))
# The same pair and the rows between them: "we argue all the time", "me and my wife keep rowing".
ROWS_BETWEEN_THEM = re.compile(
    r"\b(?:me and|i and)\s+(?:my|our)\s+(%s)\s+(?:keep\s+)?(?:argue|arguing|row|rowing|fight|"
    r"fighting|bicker|bickering)\b"
    r"|\b(?:my|our)\s+(%s)\s+and\s+i\s+(?:keep\s+)?(?:argue|arguing|row|rowing|fight|"
    r"fighting|bicker|bickering)\b"
    r"|\bwe\s+(?:keep\s+)?(?:argue|arguing|row|rowing)\b"
    % (_RELATION_PERSON, _RELATION_PERSON))
# Two people who do not get on, or a relationship gone wrong with no row and no silence named.
RELATION_GONE_WRONG = re.compile(
    r"\b(?:my|our)\s+(%s)\s+and\s+i\s+(?:dont|don't|do not)\s+get on\b"
    r"|\b(?:dont|don't|do not)\s+get on with\s+(?:my|our)\s+(%s)\b"
    r"|\bwe (?:are|keep|have been)\s+(?:growing|drifting) apart\b"
    % (_RELATION_PERSON, _RELATION_PERSON))
# Not this shape, whatever relation the line names: an emergency about somebody, a drink, a fist,
# or the end of a marriage, which is weighed rather than asked about.
NOT_A_RELATION_TROUBLE = re.compile(
    r"\b(?:hurt|hurts|hurting|injur\w*|hospital|ambulance|a and e|stroke|seizure|fit|fits|"
    r"collapsed|collapse|bleeding|blood|overdose|cancer|tumour|tumor|dementia|alzheimer\w*|"
    r"chemo\w*|died|dying|death|funeral|drink|drinks|drinking|alcohol|drunk|hit|hits|hitting|"
    r"punch\w*|knife|gun|police|threat\w*|abuse\w*|affair|cheat\w*|divorce|cheated)\b")
# The pool says the thing back in its own shape and then asks the one question, because the three
# ways a relationship goes wrong want three different questions: the silence wants when it last
# was not silent, the rows want what they are about, and a marriage gone wrong wants what changed.
THE_QUIET_LINES = (
    "That is a lonely way to live. When did {pair} last have a proper talk?",
    "Sorry to hear it. What is an evening at home like for {pair} now?",
    "That is hard going. What happened the last time {pair} tried to talk?",
)
THE_ROWS_LINES = (
    "That wears a person down. What do the rows tend to be about?",
    "That is exhausting. Is there one thing that sets it off with {who}?",
    "Nothing I can fix from here, but I can listen. What was the last row about?",
)
THE_RELATION_LINES = (
    "That is a hard place to be. What has changed with {who}?",
    "Sorry to hear it. What has gone wrong with {who} lately?",
    "That is a heavy thing to carry. What does a bad week look like for {pair}?",
)


def the_two_of_them(clean, memory=None):
    """A reply to a relationship said to be in trouble, or None to leave it to the caller.

    The line has no question in it, so nothing reads it as one: without this the store files it
    as a fact and says it back, or the floor says it is listening, and both of those answer a
    marriage the way they answer a bus timetable.
    """
    if not clean or "?" in clean:
        return None
    if NOT_A_RELATION_TROUBLE.search(clean):
        return None
    pool = None
    if QUIET_BETWEEN_THEM.search(clean):
        pool = THE_QUIET_LINES
    elif ROWS_BETWEEN_THEM.search(clean):
        pool = THE_ROWS_LINES
    elif MARRIAGE_IN_TROUBLE.search(clean) or BAD_WITH_THEM.search(clean) \
            or RELATION_GONE_WRONG.search(clean):
        pool = THE_RELATION_LINES
    if not pool:
        return None
    found = re.search(r"\b(?:my|our)\s+(%s)\b" % _RELATION_PERSON, clean)
    who = "your " + found.group(1) if found else "the two of you"
    pair = "you and your " + found.group(1) if found else "the two of you"
    return _pick_filled(pool, memory, clean,
                        lambda line: line.replace("{who}", who).replace("{pair}", pair))



def _has_phrase(clean, phrases):
    return any(f" {phrase} " in f" {clean} " for phrase in phrases)


def _planned_word(word):
    """True when a word is one of PLANNED_VERBS or an ordinary inflection of one.

    "thinking of moving house" has to count ("moving" is the plan), while "thinking about my mum"
    and "i keep thinking about it" must not: the object of a thought is not a plan. So the word
    after the opener has to be a verb of the work a plan is made of, in whatever form it is said.
    """
    if word in PLANNED_VERBS:
        return True
    for verb in PLANNED_VERBS:
        if word in (verb + "ing", verb[:-1] + "ing", verb + "s", verb + "d",
                    verb + verb[-1] + "ing", verb[:-1] + "ed"):
            return True
    return False


# What a thought can be about without being a plan: a person, or themselves, or a stretch of the
# past. "im thinking about my mum" and "i keep thinking about it" are the mind going back over
# something, and "we are thinking about a trip next year" is the plan this cue is for.
THOUGHT_OBJECT = frozenset((
    "it", "this", "that", "them", "they", "everything", "anything", "nothing", "myself",
    "me", "him", "her", "past", "life", "death", "everything", "people", "someone",
    "somebody", "anyone", "anybody", "childhood", "then", "before",
)) | OTHER_PEOPLE


def _going_to_plan(clean):
    for opener in GOING_TO:
        at = clean.find(opener)
        if at < 0:
            continue
        rest = clean[at + len(opener):].split()
        if len(rest) > 1 and rest[0] in ("work", "working", "works"):
            # the work itself is the plan ("going to work on my cv"), the place is not
            return rest[1] == "on"
        if rest and _planned_word(rest[0]):
            return True
        # "thinking about going back to college" is a plan whose verb is one step further out
        if len(rest) > 1 and rest[0] in ("going", "getting") and rest[1] == "back":
            return True
        # "thinking of / about" takes any object, so the object has to be something other than a
        # person or a stretch of the past before the line is a plan: "im thinking about my mum"
        # is not a project with a first step.
        if opener.strip() in ("thinking of", "thinking about") and not set(rest[:3]) & THOUGHT_OBJECT:
            return True
    return False


def reads_as_plan(clean):
    """True when the line says what the person means to do, over time."""
    if set(clean.split()) & ARRANGEMENT:
        return _has_phrase(clean, PLAN)  # a visit is an arrangement, not a project
    if _has_phrase(clean, PLAN) or _going_to_plan(clean):
        return True
    return bool(BOOKED.search(clean) and set(clean.split()) & STEP_NOUNS
                and set(clean.split()) & BIGGER_PLAN)


def _asked_last(memory):
    """True when the bot's last reply ended on a question."""
    turns = memory.get("turns") or []
    last = str((turns[-1] if turns else {}).get("bot") or "").strip()
    return last.endswith("?")


def a_want_said_back(said_back, clean):
    """True when the store's answer to this line only filed the want, so the reader can take it.

    The test is the shape, not a list of frames: a reply that only says the line back has filed
    the want and answered nothing, whether it opens "Noted:", "Got it -" or, straight after a
    feeling, ends "That explains it - no wonder it sits on you." The store's own shaped answers
    are not that shape - "So you are thinking about a horse. Who would look after it in the day?"
    is a better reply than anything this pool can say, and it says something the line did not.
    A death in the line keeps the store's turn whatever shape its answer has.
    """
    if A_LOSS_IN_THE_LINE.search(str(clean or "")) or A_CONDOLENCE.search(str(said_back or "")):
        return False
    from ..memory import repeat  # at call time: repeat imports the compose package itself
    return repeat.only_said_it_back(clean, said_back)


def dependant_want_reply_for(clean, words, memory):
    """A reply to a want somebody the person looks after has, or None to leave it to the caller.

    The line is a request for help with that want, so the reply is the first step of it - never
    the echo, which files the want and answers nothing. Everything this reader does not own is
    left to the caller: a want of the person's own (that is `reply_for` above), a want aimed at
    the person rather than at a thing ("my son wants me to buy him a car"), a line about a loss
    or an emergency, and any line that asks something.
    """
    if not clean or not DEPENDANT_WANT.search(clean):
        return None
    if set(words) & NOT_PLAIN or _has_phrase(clean, CRISIS):
        return None
    if ASKED_OF_THE_PERSON.search(clean) or WANTS_TO_BE.search(clean):
        return None
    if set(words) & A_WEAPON:
        return None
    if set(words) & WEAPON_WORDS and not _has_phrase(clean, NOT_A_WEAPON):
        return None
    if set(words) & ASKS or _has_phrase(clean, DOUBT):
        return None
    if _has_phrase(clean, COUNTERFACTUAL):
        return None
    options = DEPENDANT_WANT_REPLIES
    if _asked_last(memory):
        # Two questions in a row is an interrogation: say something they can use instead.
        options = tuple(o for o in options if not o.endswith("?")) or options
    return pick(options, memory, clean)


def reply_for(clean, words, memory, topics=()):
    """A short reply that fits the plan in a statement, or None to leave it to the caller."""
    if not clean or set(words) & NOT_PLAIN or _has_phrase(clean, CRISIS):
        return None
    if _has_phrase(clean, COUNTERFACTUAL) or set(words) & MARKED_DATE:
        return None
    if set(words) & ASKS or _has_phrase(clean, DOUBT):
        return None
    if not reads_as_plan(clean):
        return None
    options = PLAN_REPLIES_PLAIN if _has_phrase(clean, BARRIER) else PLAN_REPLIES
    if _asked_last(memory):
        # Two questions in a row is an interrogation: say something they can use instead.
        options = tuple(o for o in options if not o.endswith("?")) or options
    return pick(options, memory, clean)


# --- a thing the person has arranged ---------------------------------------------------------
# "i booked a smear test", "we booked a trip to spain", "i booked flights to spain": the person
# has done something between one turn and the next, and told the bot about it. It is not a plan
# (there is no first step left to be unsure about, see APlanIsAheadAndUnfinishedTest) and not a
# report of a setback, so it fell through to the two stock answers that fit any message: the nod
# ("Thanks for telling me - I'm here if you want to dig into any of that") and the echo ("Got it -
# you booked a trip to spain"). Neither says anything about the thing; the echo only says the line
# back, which STYLE.md counts as a restatement rather than an answer.
#
# What a friend says to "i booked flights to spain" is about the arrangement itself: when it is,
# and whether anything is left to sort. So the reply asks that, and never repeats the booking.
# The reading is the grammar - the person's own "i/we" in front of the booking, or their own
# "i'm/we're booking" - so a question ("should i book the tickets now"), a step still ahead
# ("i need to book the car in") and a mistake ("i double booked tuesday again") are left alone.
# The same arrangement said without a person in front of it: "physio booked for friday", "the
# tickets are booked for saturday", "hotel booked". English puts the thing booked first when the
# person is obvious, and the reading above asks for their "i/we", so these lines fell through to
# the composer - "the tickets are booked for saturday" got "Got it. Is there anything you'd like a
# hand with?", and "physio booked for friday" was read as the noun "book" and answered with a book
# recommendation. What a friend says to a booking is about the arrangement either way, so the
# shape is "<the thing> is/are booked" or "<the thing> booked <when>".
ARRANGED = re.compile(
    r"\b(?:i|we|i'?ve|we'?ve|ive|weve)\s+(?:(?:have|had|just|finally|only|already)\s+)*booked\b"
    r"|\b(?:i'?m|im|we'?re|were)\s+booking\b"
    r"|\b(?:is|are|was|were|it's|its)\s+(?:now\s+|all\s+|already\s+|finally\s+)?booked\b"
    r"|\b[a-z][a-z'\u2019-]*(?:\s+[a-z][a-z'\u2019-]*){0,2}\s+booked\s+"
    r"(?:for|on|at|in|next|this|tomorrow|today|tonight|yesterday|[0-9])\b")
# Two bookings at once is the mistake, not the arrangement: "i double booked tuesday badly" has
# its own line in the diary pools, and "Sorted. When is it?" answers the wrong thing.
DOUBLE_BOOKED = re.compile(r"\b(?:double|over|re)[- ]?book\w*")
# A booking that has gone wrong is not an arrangement to be pleased about: "i booked the flights
# and now i cant go", "i booked the wrong day", "we booked the holiday but now i regret it". The
# booking word is in the line either way, so what decides it is the word for what went wrong: a
# complaint after the verb, in the same line. It is a small closed class (wrong, cancelled,
# refunded, charged, expired) plus the same negatives every other reader uses (cant, didnt,
# never, lost).
WENT_WRONG = re.compile(
    r"\b(?:wrong|cancel(?:s|led|ling|lation)?|refund(?:s|ed|ing)?|charges?|charged|"
    r"overcharged|expired|expires|can'?t|cant|cannot|unable|couldn'?t|couldnt|didn'?t|didnt|"
    r"doesn'?t|doesnt|won'?t|wont|never|lost|missed|regret(?:s|ted|ting)?|dread(?:ing)?|"
    r"fell\s+through|mucked\s+up)\b")
# The booking is the first half of the news and the second half turns it: "we booked the holiday
# but now i am dreading it", "i booked it, though i am not sure i can go". The contrast word is
# the shape, so no feeling has to be named: a clause that takes it back means the arrangement is
# not the whole of what the person said, and the plain nod answers less wrongly than "Good - one
# off the list".
TURNED = re.compile(r"\b(?:but|though|although|except|only)\b|\band\s+(?:now|then)\b")

BOOKED_REPLIES = (
    "Good - that's one off the list. When is it?",
    "Nice one. Is it soon, or have you got a while yet?",
    "Sorted. Is there anything left to sort before it?",
    # Not every reply ends on a question: a person who says this twice should not be asked
    # something twice, and "that's one off the list" is enough for a booking.
    "Good - that's one off the list.",
)
# The replies that ask when it is, and the ones the same booking gets when it has already said:
# the question is the only part that is wrong, and the swap keeps the rest of the pool in place.
# There are two of them, and the miss this map was written for came back through the second:
# "ive booked the physio for friday" and "the room is booked for saturday" both said the day and
# were asked "Is it soon, or have you got a while yet?" because only the first was swapped.
# A swap may take the question away from a dated booking, and it may not take the reply away
# with it. The second one was swapped for "Nice one." - two words back to a line that had just
# told the bot where they are going and when, which is the stock cheer STYLE.md counts as no
# answer. It was also the first line of a chat: "weve booked a week in cornwall in august" is a
# whole plan, and the bot's opening reply to it was "Nice one." Whatever a swap says, it has to
# be something the person can answer, so the dated reply keeps a question and only loses the one
# the line already answered.
ALREADY_DATED = {
    "Good - that's one off the list. When is it?": "Good - that's one off the list.",
    "Nice one. Is it soon, or have you got a while yet?": "Nice one. Anything left to sort before then?",
}


# An ask typed without its question mark: "is the room booked for saturday", "can the tickets be
# booked for friday". The bare "<thing> booked for <when>" is an arrangement, and the same words
# behind an opener are a question, so a line that starts with one and does not start its booking
# with the person is left to the readers that answer questions.
QUESTION_FIRST = re.compile(
    r"^\W*(?:is|are|was|were|do|does|did|can|could|should|shall|will|would|have|has|am)\b", re.I)
THE_PERSON_WITH_IT = re.compile(r"^(?:i|we|i'?m|im|i'?ve|ive|we'?re|were|we'?ve|weve)\b", re.I)
# The booking is behind the person already: "we had a babysitter booked for tonight", "i had the
# tickets booked a month ago". Nothing has been sorted that needs cheering, and the line is
# usually the setting for what comes next ("and she cant make it now"), so it is left to the
# readers that answer small talk.
HAD_IT_BOOKED = re.compile(r"\bhad\b(?:\s+\w+){0,5}\s+booked\b", re.I)


def reads_as_arranged(clean):
    """True when the line says the person has booked or is booking something of their own."""
    if not clean or "?" in clean:
        return False  # a question about booking is a question, not an arrangement
    if DOUBLE_BOOKED.search(clean):
        return False
    if WENT_WRONG.search(clean):
        return False  # the booking is not the news: something about it has gone wrong
    booked = ARRANGED.search(clean)
    if booked and TURNED.search(clean[booked.start():]):
        return False  # the line takes the news back after the booking
    if HAD_IT_BOOKED.search(clean):
        return False  # the booking is behind them: the news is what comes next
    if booked and QUESTION_FIRST.match(clean) and not THE_PERSON_WITH_IT.match(clean[booked.start():]):
        return False  # a question about a booking, typed without its question mark
    return bool(booked)


def _says_when_it_is(clean):
    """True when the line already says when the thing it names is.

    The plan reader's own future-date reader (`facts.FUTURE`) is the whole of it, so every way of
    saying a date the store understands counts here too - "in june", "next friday", "on the 3rd",
    "tomorrow", "in three weeks", and a date after the verb that carries it ("the term ends 12
    july")."""
    return bool(clean and facts.FUTURE.search(clean)) or bool(
        set(str(clean or "").lower().replace(",", " ").replace(".", " ").split())
        & (facts.DAYS | facts.MONTHS))


def arranged_reply_for(clean, words, memory):
    """A reply to a thing the person has arranged, or None to leave it to the caller."""
    if set(words) & NOT_PLAIN or _has_phrase(clean, CRISIS):
        return None
    if _has_phrase(clean, COUNTERFACTUAL) or set(words) & MARKED_DATE:
        return None
    if set(words) & ASKS or _has_phrase(clean, DOUBT):
        return None
    if not reads_as_arranged(clean):
        return None
    options = BOOKED_REPLIES
    if _says_when_it_is(clean):
        # The booking carries its own date, so asking for one is deaf: "i booked a holiday to
        # spain in june" got "Good - that's one off the list. When is it?" The one reply that asks
        # is swapped for its own short form rather than dropped, so the reply every other line in
        # this pool gets is untouched.
        options = tuple(ALREADY_DATED.get(o, o) for o in options)
    if _asked_last(memory):
        options = tuple(o for o in options if not o.endswith("?")) or options
    return pick(options, memory, clean)


# --- an activity the person has taken up ------------------------------------------------------
# "im into climbing", "im really into baking at the moment", "ive got into yoga": the person
# names something of their own they spend time on, and every one of these lines got a stocking
# pool ("Got it. Is there anything you'd like a hand with?", "Thanks for telling me - I'm here if
# you want to dig into any of that"). Neither says anything about the climbing. The reading that
# says whose interest it is and what it is in lives in the understanding engine
# (`understood["taking_up"]`), because the bare word "into" cannot be given to the knowledge base
# without making "shes 30 and into running" a request for a beginner's plan.
#
# What a friend says to it depends on which of the two it is, and the reading says: `doing` is
# somebody already at it, so the reply is how it is going or what got them into it; `started` is
# somebody at the beginning ("ive got into yoga", "im getting into gardening"), and there the
# first weeks are the interesting part. The activity is named inside the question rather than
# said back on its own - "yoga - nice" is the restatement STYLE.md counts as no answer - and a
# turn that already ended on a question gets something to say instead of a second question.
# Every reply below is written so that the activity can be singular or plural ("the climbing",
# "the board games"): the verb that agrees is never the activity itself but a word in front of it
# ("how's *it* going with the board games"), because no word list can say which activities are
# plural - "crosswords", "rugby" and "chess" are all one word each.
INTEREST_DOING = (
    "How's it going with the {thing}?",
    "{Thing} - how long have you been at it?",
    "What got you into {thing}?",
    "How are you finding the {thing}?",
    "How's {thing} treating you?",
)
INTEREST_STARTED = (
    "How are the first weeks of the {thing} going?",
    "Nice one - what have you got so far with the {thing}?",
    "Are you going to a class for the {thing}, or working it out yourself?",
    "What made you start {thing}?",
    "Good luck with the {thing}. How are you finding it?",
)
# A second question in a row is an interrogation, so an interest said after a question is
# answered with something to say instead: what a friend offers somebody starting something.
INTEREST_DOING_PLAIN = (
    "There's a lot in the {thing} worth talking about, so say more when you want to.",
    "Good thing to be into. I'm happy to talk about the {thing} any time.",
)
INTEREST_STARTED_PLAIN = (
    "The first few weeks of the {thing} are the hard part. Say how it goes.",
    "Good luck with the {thing} - it gets easier once it is a habit.",
)
# Going back to something they used to do is neither a first start nor an interest they have been
# at all along: "what made you start chess" reads as if they had never played it. The wording
# stays past-tense about the first time and asks what brought them back.
INTEREST_BACK = (
    "What got you back into {thing}?",
    "Welcome back to it - what made you pick {thing} up again?",
    "How's the {thing} going the second time round?",
)
INTEREST_BACK_PLAIN = (
    "Good to hear you're back at it. Say how the {thing} goes.",
    "Nice that you went back to the {thing} - it comes back faster the second time.",
)
# A thing that is not an activity, or a line where the activity is not the news: the mood pools,
# the knowledge base and the rest of the deck answer these better than a question about it.
NOT_AN_INTEREST = frozenset("""work job jobs shift shifts nights overtime rota house home
    cleaning ironing washing shopping money trouble debt him her them you me it this that
    everything anything nothing something trouble bother fights arguments""".split())


def _named(template, thing):
    """The template with the activity in it, capitalised when it opens the sentence."""
    said = template.replace("{thing}", thing)
    return said.replace("{Thing}", thing[0].upper() + thing[1:])


def interest_reply_for(interest, memory):
    """A reply to an activity the person is into, or None to leave it to the caller.

    `interest` is `understood["taking_up"]`: the activity and whether it is new. Nothing else is
    read here - the understanding engine has already said whose interest it is and fenced the
    lines where "into" means a person, a fight or a debt - so this only decides the wording.
    """
    if not isinstance(interest, dict):
        return None
    thing = str(interest.get("text") or "").strip()
    if not thing or any(word in NOT_AN_INTEREST for word in thing.split()):
        return None
    started = interest.get("shape") == "started"
    back = bool(interest.get("back"))
    asked_last = _asked_last(memory)
    if back:
        options = INTEREST_BACK_PLAIN if asked_last else INTEREST_BACK
    else:
        options = INTEREST_STARTED_PLAIN if started else INTEREST_DOING_PLAIN
        if not asked_last:
            options = INTEREST_STARTED if started else INTEREST_DOING
    return pick(tuple(_named(template, thing) for template in options), memory, thing)
