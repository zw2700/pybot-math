"""A thing of theirs that has been damaged, taken or refused is not a day that went well.

"We had a flood", "someone keyed my car", "my son got suspended", "i came off my bike" and "my
visa was refused" all reach the composer's small-day pool on main, which is written for an
ordinary account of an ordinary afternoon ("a takeaway, a haircut, work being alright"):

    we had a flood                -> "Nice one. How did the rest of it go?"
    someone keyed my car          -> "Good to hear. What was the best bit?"
    my son got suspended          -> "Nice one. How did the rest of it go?"
    i came off my bike            -> "Nice one. How did the rest of it go?"

That is the worst thing the bot can say to somebody, and it is not a knowledge gap: nothing needs
looking up to answer it. `bot/compose/badnews.py` reads the hard news - a diagnosis, a death, the
money running out - but a flooded kitchen, a keyed car and a child sent home are a smaller kind
of bad day, and no reader has them, so they fall through to the pleasantry.

What a friend does with one of these is say it is rotten and ask one thing about it, which is
what this file does. Three pools, because the three shapes want different questions: a thing of
theirs that was damaged or taken wants "what needs sorting", a refusal or a punishment that
landed on them wants "what did they say", and coming off a bike wants "are you alright".

This is a last resort and it is written to be one. `bot/modules/greeting.py` asks it at the very
end, and it only takes the turn when the reply the composer chose is one of its glad lines - so
an answer of any kind, from any module, keeps the turn it has. Nothing here invents a fact: the
reply says the day is bad and asks about it.

The words that are ordinary in another line are left out: "a flood of orders", "flooded with
applications", a "fire drill", a code "keyed in", the show somebody "stole". A line that says
one of those is not this.
"""
import re

from . import pick

# A place of theirs that took water, fire or a break-in.
THEIR_PLACE = (r"(?:my|our|the)\s+(?:[a-z']+\s+)?(?:house|flat|place|home|kitchen|bathroom|cellar|basement|loft|"
               r"garage|shed|garden|hall|hallway|landing|roof|bedroom|attic|utility|conservatory)")

# Something of theirs, named or not, that was done to. Two words at most, so a long line about a
# thing that is not theirs does not match by accident.
THEIR_THING = r"(?:my|our)\s+(?:[a-z']+\s+){0,2}"

NOT_GOOD = tuple(re.compile(pattern) for pattern in (
    # Water or fire in the place they live, however it is said: "we had a burst pipe", "the flat
    # is flooding", "our shed caught fire". "a burst of energy" is not a pipe and "fire drill" is
    # not a fire, so those two carry their own guard below.
    rf"\b(?:we|i|they)\s+(?:just\s+)?had\s+(?:a|an)\s+(?:flood|flooding|leak|burst\s+pipe|"
    r"burst\s+radiator|break[- ]?in|burglary|fire)\b",
    rf"{THEIR_PLACE}[^.!?,]{{0,24}}\b(?:flooded|flooding|is flooding|has flooded|caught fire|"
    r"went on fire|is leaking|was leaking|has water coming in|came through the ceiling)\b",
    # A break-in and a theft: "we got burgled", "my bike got nicked", "someone took my bike".
    r"\b(?:got|been|were|was)\s+(?:burgled|broken into|robbed|vandalised|vandalized|"
    r"smashed up|turned over)\b",
    rf"{THEIR_THING}\b(?:got|was|were|has been|had been|is|are|got\s+)\s*(?:keyed|scratched|"
    r"dented|clamped|towed(?:\s+away)?|smashed|nicked|stolen|vandalised|vandalized|"
    r"broken into|pinched|slashed|punctured|kicked in|wrenched off|snapped off|ripped|torn|"
    r"torched|set (?:on )?fire to)\b",
    r"\b(?:someone|somebody|a kid|the kids|next door|a neighbour|a neighbor|my neighbours?|"
    r"our neighbours?|the neighbours?)\s+"
    r"(?:keyed|scratched|dented|smashed|nicked|pinched|stole|took|vandalised|vandalized)\s+"
    r"(?:my|our)\b",
    # A refusal or a punishment that landed on them or on their child. The thing refused has to
    # be named: "my visa was refused", "my son got suspended", "my application was turned down".
    rf"{THEIR_THING}\b(?:son|daughter|kid|child|boy|girl|lad|lass|teenager|eldest|youngest)\b"
    r"[^.!?,]{0,30}\b(?:suspended|excluded|expelled)\b",
    rf"{THEIR_THING}\b(?:visa|application|claim|mortgage|loan|benefits?|pip|dla|passport|"
    r"offer|request)\b[^.!?,]{0,24}\b(?:refused|rejected|turned down|declined|denied|"
    r"turned me down|turned them down)\b",
    # Coming off something, and a prang in a car.
    r"\bcame off\s+(?:my|his|her|the|a|their)\s+(?:bike|motorbike|moped|scooter|e-scooter|"
    r"cycle|horse|ladder|roof|skateboard|board)\b",
    rf"{THEIR_THING}\b(?:car|van|bike|motorbike)\b[^.!?,]{{0,20}}\b(?:got|was|were)\s+"
    r"(?:clamped|towed(?:\s+away)?|keyed|scratched|dented|scraped)\b",
    r"\bpranged\b|\bscraped the (?:car|van|wing mirror)\b",
    # A part of the place that came down or blew away: "the ceiling came down", "my greenhouse
    # blew away", "the fence blew down", "a tile came off the roof". Nothing here is a good day,
    # and the composer has the small-day pool for it.
    rf"(?:{THEIR_PLACE}|\b(?:ceiling|roof|fence|gate|wall|greenhouse|tree|branch|tiles?|"
    r"guttering|gutter|chimney pot|carport|awning))\b[^.!?,]{0,24}\b(?:came down|collapsed|"
    r"caved in|blew (?:away|down|off|over)|got blown (?:away|down|off))\b",
))

# The same words where the line is not bad news at all: an order book "flooded with
# applications", a fire drill, a code keyed in, a show stolen, and a bike nicked off early.
NOT_GOOD_DESPITE = re.compile(
    r"\bflood(?:ed)?\s+(?:of|with)\b|\bfire\s+(?:drill|alarm|test|work|escape|station|place|"
    r"pits?)\b|\bkeyed\s+in\b|\bstole\s+the\s+(?:show|limelight|scene)\b|"
    r"\bnicked\s+(?:off|out)\b|\brobbed\s+(?:blind|us of)\b|\be?xcluded\s+from\s+the\s+pub\b")

# The composer's glad lines: the small-day pool and the pleasantries about a thing done. One of
# these on a line like the ones above is the bot congratulating somebody on a bad day. The
# question half of the pool is the reliable part, so it is read wherever it sits, and the opener
# is read at the start of the reply.
GLAD_OPENER = re.compile(
    r"^(?:nice one|good to hear|sounds alright|well done|that'?s good|lovely|glad to hear|"
    r"how was it, overall)\b")

# And the other thing a rotten day gets from the composer: nothing. "Got it. Is there anything
# you'd like a hand with?" is the intake form, and "Rotten luck." and "That's a pain." are a
# receipt of the news with no question after it - a friend says one of those and then asks. These
# are read on the same gate, so they are only replaced on a line this file has read as a bad day.
BLANK_OR_THIN = re.compile(
    r"^(?:got it\b|thanks for telling me|i'?m listening|noted:|right\.|okay\.|ok\.|"
    r"rotten luck\.?$|that'?s a pain\.?$|that'?s rough\.?$|fair enough\b|"
    r"ugh, that'?s annoying\.?$|that'?s annoying\.?$)")
GLAD_ANYWHERE = re.compile(
    r"\b(?:how did the rest of it go|what was the best bit|anything good in it|"
    r"are you pleased with it|is it what you were after|how did that feel)")

# A no they have already been given is a rotten thing in the same sense as a claim turned down,
# and it was answered with the person's own sentence handed back: "she already said no once" got
# "Got it - she already said no once", and "my landlord said no" the same. The line is short, says
# nothing about how they feel and asks nothing, so no pool fitted it. What a friend says is about
# the refusal itself, and the thread holds who it came from - the line before it named them
# (`understood["leans_on"]["subject"]`), or the line itself does ("my boss").
#
# The refusal read here is somebody else's: "i said no" is the person's own limit, which has its
# own answers, and "i told her no" is them being the one who refused, so the subject is never "i".
_A_SAID_NO = re.compile(
    r"\b(?:she|he|they|my\s+[a-z]+|our\s+[a-z]+|the\s+[a-z]+|his\s+[a-z]+|her\s+[a-z]+|"
    r"their\s+[a-z]+|mum|dad|boss|landlord|manager|school|council|bank|surgery|gp|doctor|"
    r"nurse|hr)\b"
    r"(?:\s+[a-z']+){0,4}?\s(?:said|says|saying|told\s+me|telling\s+me)\s+(?:me\s+)?no\b",
    re.I)
# The same refusal said as the verb rather than around "no": "he refused", "they turned it down",
# "she isn't keen", "my boss won't budge". A bare "won't" is a car that will not start, so it only
# counts about a person, with the thing they will not do.
_A_REFUSED = re.compile(
    r"\b(?:she|he|they|my\s+[a-z]+|our\s+[a-z]+|the\s+[a-z]+|his\s+[a-z]+|her\s+[a-z]+|"
    r"their\s+[a-z]+|mum|dad|boss|landlord|manager|school|council|bank|surgery|gp|doctor|hr)\b"
    r"(?:\s+[a-z']+){0,3}?\s(?:refused|has\s+refused|had\s+refused|"
    r"turned\s+(?:it|me)\s+down|won'?t\s+(?:budge|have\s+it|agree|allow|consider|do\s+it|move|"
    r"shift|bend)|isn'?t\s+keen|wasn'?t\s+keen|is\s+not\s+keen|said\s+(?:it|that)\s+"
    r"(?:isn'?t|wasn'?t|is\s+not|was\s+not)\s+(?:possible|allowed|an\s+option|on))\b",
    re.I)
# A no already in hand, and the ask worth one more go with the reason in the same sentence. None
# of these says what the answer will be: nobody here can know that.
A_NO_ALREADY = (
    "Then you know where you stand, and that is worth something. Was the no to that exact ask, "
    "or to the idea of it?",
    "Then the answer is no for now. What would have to change for it to be a yes?",
    "Ask once more with your reason in the same sentence, and take the second no as the answer.",
    "One no is worth hearing again only if something has changed since. Say what has, in a line, "
    "and go back with it.",
    "That is a no to the ask as you put it, which is not a no to you. Change one thing about it "
    "and try again.",
    "Go for the smallest version of it that would still help, and build from that if it comes.",
)
# The same where the line or the thread names them: "my boss", "the landlord", "she". "my" becomes
# "your" because it is the person's own words said back with the side changed; a role stays a role.
A_NO_FROM = (
    "Then {who} has given you an answer. Was it a no to that ask, or to the whole thing?",
    "{who} has said no once, so ask for the smallest version of it that would still help.",
    "A no from {who} is worth one more ask, with what you want and why in a single line - then "
    "leave it with them.",
    "Go back to {who} with what has changed since and nothing else. That is what moves a no.",
    "What would {who} have said yes to? People who refuse usually know.",
)
_MINE = re.compile(r"\b(?:my|our)\b", re.I)
# A no being weighed rather than reported: "what if she says no", "supposing the council says no",
# "do you think he will refuse". The what-if reader answers a plan; this reading is for a refusal
# that has already happened to them.
_A_NO_STILL_BEING_WEIGHED = re.compile(
    r"\b(?:what\s+if|if\s+(?:she|he|they|my|the|it)|suppose|supposing|in\s+case|unless|"
    r"should\s+i|shall\s+i|do\s+you\s+think|would\s+they|will\s+they)\b", re.I)
# A refusal in the passive takes the thing refused as its subject ("my claim was refused", "my
# visa got turned down"), so the "my" in front of it is not who said no and the reply must not
# blame it: the person is "your claim".
_A_REFUSAL_IN_THE_PASSIVE = re.compile(
    r"\b(?:was|were|got|been|is|are|being)\s+(?:refused|turned\s+down|rejected|turned\s+away|"
    r"declined|knocked\s+back)\b", re.I)

# The bad thing is already over: "my bike got nicked and i got it back", "the flat flooded but
# its dried out now", "i came off my bike but im fine". The pools below ask what needs sorting,
# and a person who has just said it is sorted is not asking that. A search engine has nothing to
# add either, so the turn keeps whatever the composer had and this module stands aside.
RESOLVED = re.compile(
    r"\b(?:but|and|although|though)\s+(?:\w+\s+){0,3}?(?:sorted|sorted out|fixed|resolved|"
    r"dried out|paid out|refunded|replaced|recovered|got it back|got them back|got them|"
    r"back at school|back to normal|back home|all fine|all ok|ok now|okay now|fine now|"
    r"im fine|i'?m fine|was fine|no harm|nobody hurt|no one hurt|nothing was taken|"
    r"only a scratch|turned out (?:fine|ok)|got it on appeal|won the appeal|"
    r"appeal worked|only took (?:a|the|my|our|one)\b)\b")

# A thing of theirs damaged, taken or refused: the question is what needs doing about it.
DAMAGED_OR_TAKEN = (
    "Rotten luck. What needs sorting first?",
    "That's a rotten one. How bad is it?",
    "Ugh, that's the last thing you needed. Is it sorted, or still going on?",
    "That's a mess to land on you. What's the damage?",
)
# A refusal or a punishment that came from somebody else: the question is what they said.
# A refusal is the arm where the next line is often a question of its own, and there is a card
# waiting behind it: "my visa was refused" / "what do i do now" answers with the passport pages.
# A reply that ends on a question hands that next line to the composer's question-back pool
# instead ("I can be specific if you tell me this much: what did they say?"), and the card is
# lost, so this pool asks nothing. An invitation there is no better: "tell me what it said when
# you're ready" comes back as a step ("Take your time with the next bit, and take it from
# there"). These lines state the sympathy and leave the next turn free.
A_BLOW_FROM_SOMEONE = (
    "That's a blow. Sorry to hear it.",
    "Ugh, that's harsh. That's a rotten thing to have land on you.",
    "That's a rotten thing to land on you.",
)
# Coming off a bike: the person comes before the thing.
A_FALL = (
    "That's a shock. Are you alright?",
    "Ouch. Are you hurt?",
    "That would rattle anyone. Are you alright?",
)

# Somebody else came off the bike: "my brother came off his bike yesterday" is not a report about
# the person in front of the bot, and "Are you alright?" asks the wrong one. "They" is what a
# friend says about a brother or a sister, and it needs no gender from the line.
A_FALL_ELSE = (
    "That's a shock. Are they alright?",
    "That's a bad one. How are they doing?",
    "That's a shock to hear. Is everyone alright?",
)
_SOMEONE_ELSE = re.compile(r"\b(?:my|our|his|her|their)\s+(?:brother|sister|son|daughter|mum|mom|"
                           r"dad|husband|wife|partner|mate|friend|neighbour|neighbor|nephew|"
                           r"niece|grandad|granddad|grandma|gran|nan|colleague|boss|cousin|little "
                           r"(?:boy|girl|lad|one))\b|\b(?:he|she|they)\s+(?:came off|fell)\b")
_FALL = re.compile(r"\bcame off|\bpranged\b|\bscraped the (?:car|van|wing mirror)\b|\bclamped\b|"
                   r"\btowed\b")

# A near miss: nothing landed, there is nothing to sort out, and the person is still shaken.
# "i nearly fell", "a car nearly hit me", "i nearly got knocked off my bike", "close call on the
# motorway". The mishap word is what makes it one, so "i nearly finished my essay" is not here.
MISHAP = (r"(?:fell|fall|fallen|slipped|slip|tripped|trip|came\s+off|come\s+off|knocked\s+off|"
          r"knocked\s+(?:me|us)\s+off|hit\s+(?:me|us|by)|ran\s+(?:me|us)\s+over|run\s+over|"
          r"drove\s+(?:into|at)\s+(?:me|us)|clipped\s+(?:me|us)|collided|crashed|crash|"
          r"went\s+over|tumbled|skidded|smashed\s+into)\b")
NEAR_MISS = re.compile(
    r"\b(?:nearly|almost|close\s+to|just\s+missed|just\s+about)\b[^.!?,]{0,26}\b" + MISHAP +
    r"|\b(?:near\s+miss|close\s+call|narrow\s+escape|just\s+missed\s+(?:me|us))\b")
# A fright with no mishap named: "im ok just a bit shaken", "i got a fright but im ok".
FRIGHT = re.compile(
    r"\b(?:shaken\s+up|shaken|shook\s+up|shook\s+(?:me|us)|shakes\s+(?:me|us)\s+up|shaking\s+(?:me|us)\b|"
    r"shaking\s+(?:me|us)\s+up|still\s+shaking|shaking\s+a\s+bit|"
    r"(?:got|had|gave\s+me)\s+a\s+fright|a\s+fright|bit\s+of\s+a\s+scare|scared\s+me|"
    r"frightened\s+me|spooked\s+me|in\s+shock)\b")
# The same words where there was no fright, or the fright is not this turn: a fear of something,
# laughter, and a phrase that only borrows the word.
NOT_A_FRIGHT = re.compile(
    r"\b(?:shaking\s+with\s+laughter|shaken\s+not\s+stirred|shaking\s+like\s+a\s+leaf\s+of\s+lettuce|"
    r"(?:scared|afraid|frightened|terrified)\s+(?:of|to|about|that|it\s+would)\b|"
    r"scared\s+(?:of|to|about)\b|frightened\s+(?:of|to)\b|in\s+shock\s+that\b)")

# Two shapes say "close call" with nobody in them. A plan falls through and nobody needs to sit
# down: "the deal nearly fell through" is `nearly` + `fell`, and what makes a fall a fright is the
# surface it goes through, so the surface is what tells the two apart. And the bare phrase ("close
# call", "near miss", "narrow escape") counts only where the line names something that can hurt a
# body - a vehicle, a road, a height, a surface, water - because "we had a close call with the
# deadline" is the same words said about a plan.
_A_PLAN_THAT_FELL_THROUGH = re.compile(
    r"\bf(?:ell|all|allen|alling)\s+through\b(?!\s+(?:the\s+)?(?:ice|floor|roof|glass|window|"
    r"boards?|ceiling|decking|net|crust|hole)\b)")
_A_BARE_NEAR_MISS = re.compile(r"\b(?:near\s+miss|close\s+call|narrow\s+escape)\b")
_A_BODY_CAN_BE_HURT = re.compile(
    r"\b(?:bike|cycle|bicycle|car|van|lorry|truck|bus|coach|train|tram|taxi|cab|scooter|motorbike|"
    r"road|motorway|roundabout|kerb|junction|crossing|pavement|street|stairs|staircase|steps|"
    r"ladder|scaffolding|roof|balcony|wall|window|glass|ice|snow|kitchen|bath|shower|pool|sea|"
    r"cliff|horse|path|track|ferry|boat)\b")
_A_THING_WITH_NO_BODY = re.compile(
    r"\b(?:deadline|deal|sale|plan|plans|trip|booking|offer|order|mortgage|application|interview|"
    r"contract|flight|agreement|purchase|quote|bid|tender|funding|visa|exam|essay|project|"
    r"launch)\b")

# A fright, and a near miss that landed on nobody: the person is fine and needs to hear that the
# shake is real. Two of these say the thing and leave the next turn free, two ask one question.
# Two pools, because "just a bit shaken up" gave no mishap to name and "a car nearly hit me" did:
# the reply is only allowed to mention the near miss the line itself was about.
A_FRIGHT = (
    "Glad you're okay. That stays with you for a while.",
    "That gets the heart going. Sit down for a minute if you can.",
    "A fright like that sits in the body for a while. Are you okay now?",
    "God, that shakes you up. Do you want to sit down for a minute?",
)
A_NEAR_MISS = (
    "Close one. Are you hurt at all?",
    "God, a near miss like that shakes you up. Are you alright?",
    "That gets the heart going. Sit down for a minute if you can.",
    "Glad you're in one piece. That sort of thing stays with you.",
)
A_FRIGHT_ELSE = (
    "That shakes anyone up. Are they alright?",
    "A fright like that stays with you. How are they now?",
    "That gets the heart going. Is everyone alright?",
)
A_NEAR_MISS_ELSE = (
    "Close call. Is everyone alright?",
    "Glad they're in one piece. That sort of thing shakes you up.",
    "That would rattle anyone. Are they hurt at all?",
)
_FROM_SOMEONE = re.compile(r"\b(?:suspended|excluded|expelled|refused|rejected|turned down|"
                           r"declined|denied)\b")


# Not every day that goes wrong has a thing damaged in it. The other shapes reach the same glad
# line because none of them is a question and none of them names a thing the bot could look up:
#
#     ive tried two cables                          -> "How was it, overall?"
#     i waited two hours at the clinic               -> "Got it. Is there anything you'd like a hand with?"
#     my dad passed comment on my cooking            -> "Got it. Is there anything you'd like a hand with?"
#     but i thought id already paid                  -> "How was it, overall?"
#
# An attempt that failed, a wait that went on, a remark that stung and a bill that says otherwise
# are all a person telling the bot where they are stuck, and every one of them is answered with a
# pleasantry about a day that went well. Each wants one question about the thing itself, which is
# what the pools below ask.
A_THING_THAT_DID_NOT_WORK = (
    "That's annoying. What does it do when you try it?",
    "Ugh, one of those. Where are you up to with it now?",
    "That's a pain. What have you got in front of you at the moment?",
    "Rotten. Does it do the same thing every time?",
)
A_WAIT_THAT_WENT_ON = (
    "That's a long time to sit there. Did you get seen in the end?",
    "Ugh, two hours of that. Was it worth staying for?",
    "That's a lot of waiting. Did anyone tell you what was going on?",
)
A_REMARK_THAT_STUNG = (
    "That would sting. What did they say?",
    "Ugh, that's not a kind thing to say. How did you take it?",
    "That's the sort of thing that sits with you. Did you say anything back?",
)
A_BILL_THAT_SAYS_OTHERWISE = (
    "That's worth checking before you pay again. What does the bill say?",
    "Ugh. What does their paperwork say you owe?",
    "That's easily done on their side. Have you got the receipt?",
)
# A meal they went without: "i went without my lunch again", "i skipped lunch again", "i missed
# lunch again". Not a question, and nothing named that anybody could look up, so every one of them
# reached the small-day pool and was congratulated - "Nice one. How did the rest of it go?" and
# "Sounds alright. Anything good in it?" to somebody who has not eaten. Skipping a meal is a small
# bad day, and the one question worth asking is which kind it was: too busy to stop, or nothing in.
A_MEAL_THEY_WENT_WITHOUT = (
    "That's a day with a hole in the middle of it. Is it no time to stop, or nothing in?",
    "A day with a meal missing in it drags from there on. What stopped you - the day, or the "
    "cupboard?",
    "Ugh, that leaves you running on nothing. Get something in you now if you can - even toast "
    "counts.",
    "That's a miserable way to get through a day. Get something in you soon, whatever is quickest.",
)
# A thing of theirs that needs a job doing to it: "my car needs a new clutch", "the roof needs
# doing", "the plumber said it needs a new expansion vessel". Nothing here is a question and
# nothing names a fact anybody could look up, so on main every one of them reached the pleasantry
# - "Thanks for telling me - I'm here if you want to dig into any of that", and for the plumber's
# verdict even "How was it, overall?". A job that needs doing is a cost landing on somebody, and
# the part the bot can honestly help with is the one that decides the bill: what is written down
# before anybody starts.
_A_JOB_NEEDED = re.compile(
    r"\b(?:my|our|the)\s+(?:[\w']+\s+){0,2}?(?:needs?|needed)\s+"
    r"(?:a\s+|an\s+|some\s+)?(?:new\s+[\w']+|doing|fixing|replacing|repairing|painting|"
    r"servicing|cleaning|sorting|resurfacing|cutting|work|doing\s+up|service|look|quote|check|"
    r"part|parts|job)\b"
    r"|\b(?:said|says|told\s+me)\s+(?:it|the\s+[\w']+)\s+(?:needs?|would\s+need)\b")
# The subject of "needs" is a person or a part of a body: "my son needs new school shoes" is a
# shop, not a trade, and "my teeth need work" is a dentist. Neither is a job somebody quotes for,
# and both have their own answers.
# The object decides, not the verb. "Needs doing" is how people talk about the washing as much as
# about the boiler, and the same words are a chore or a bill depending on the thing: "the dishes
# need doing" is somebody's own ten minutes and "the roof needs doing" is a trade to ring. Read on
# the verb, this answered the first as if it were the second - "get what they would do and what it
# costs in writing before anybody starts" to a person standing at their own sink - so the work of
# their own that has no trade behind it stands down here and keeps its own answer.
_NOT_A_TRADE = re.compile(
    r"\b(?:homework|schoolwork|coursework|essay|essays|dissertation|revision|assignment|assignments|"
    r"reading|forms?|paperwork|admin|tax\s+return|shopping|washing|laundry|ironing|dishes|"
    r"washing[-\s]?up|sink|hoovering|vacuuming|tidying|housework|cleaning|bins|bin|cv|"
    r"applications?|invoices?|accounts|bookkeeping|packing|unpacking|bathroom|bedroom|beds?|"
    r"cooking|dinner|tea|supper|lunch|inbox|emails?|photos?|backups?)\b")
_A_PERSON_NEEDING = re.compile(
    r"\b(?:my|our|the|his|her|their)\s+(?:mum|mom|mother|dad|father|son|daughter|kid|kids|child|"
    r"children|wife|husband|partner|baby|boy|girl|mate|friend|boss|brother|sister|nan|gran|"
    r"grandad|grandma|dog|cat|puppy|kitten|teeth|tooth|gums|hair|nails|knee|back|hip|shoulder|"
    r"ankle|wrist|elbow|neck|eyes|skin)\b\s+(?:needs?|needed|wants?|has|have)\b")
_A_JOB_THAT_IS_SORTED = re.compile(
    r"\b(?:sorted|done|fixed|replaced|booked|arranged|coming\s+(?:on|tomorrow|next)|"
    r"quoted|priced|paid\s+for|had\s+a\s+quote|got\s+a\s+quote|got\s+a\s+price|"
    r"had\s+a\s+price|been\s+quoted)\b")
# A chore waiting is the same words with no trade behind them, and the useful thing to say is not a
# bill: it is the move that makes the work smaller - one thing started, the rest let go.
#
# How many things it is decides what can be said. "The dishes need doing" names one job, and a line
# about writing a list of three and leaving the other two invents a pile the person never
# mentioned (agile-newt, #11556): it would fit any message, which is the thing this file exists to
# keep off the screen. So a single job gets the move that fits one job - start it, stop at the
# timer - and the pile lines answer a line that really named a pile.
A_CHORE_WAITING = (
    "It is one job rather than a day's work. Ten minutes on it now, and stop when the timer goes - "
    "starting is the part that was making it feel bigger than it is.",
    "Give it a quarter of an hour and see where you are. One job of that size fits in an evening, "
    "and whatever is left of it will keep until tomorrow.",
    "Put a timer on and do the part you can see. It is one thing, not a verdict on your week, and "
    "you can stop at ten minutes with it half done.",
)
A_CHORE_PILE = (
    "One of those jobs that never gets shorter. Pick the one you would notice most if it were done "
    "and do that first; the rest will still be there tonight, and that is allowed.",
    "That sort of pile is normal and it is not a moral failing. Do the smallest one on the list "
    "now, while the kettle boils, and it stops feeling like a wall.",
    "Nothing broken, just a pile. Write them down, do the one that takes ten minutes, and leave "
    "the rest for a day when you have the energy.",
)
# A pile is more than one job, and the words for that are the plural count and the ones people use
# for the whole of it: "the washing and the ironing need doing", "the flat is a state", "I've got
# a mountain of housework". A line that names one chore keeps the single-job pool.
_PILE_WORDS = re.compile(
    r"\b(?:pile|piles|mountain|backlog|list|mess|state|everything|all\s+of\s+it|loads|"
    r"loads\s+of|lots|chores|housework|catch(?:ing)?\s+up|behind\s+on)\b")
# the chores that can be counted, so two of them in one line is a pile
_CHORE_THINGS = re.compile(
    r"\b(?:homework|schoolwork|coursework|essays?|dissertation|revision|assignments?|"
    r"forms?|paperwork|admin|shopping|washing|laundry|ironing|dishes|washing[-\s]?up|"
    r"hoovering|vacuuming|tidying|cleaning|bins?|cv|applications?|invoices?|packing|"
    r"unpacking|bathroom|bedroom|beds?|cooking|inbox|emails?|photos?|backups?)\b")


def _a_pile_of_chores(clean):
    """Whether the line named more than one job, or said the whole of it is a state."""
    if _PILE_WORDS.search(clean):
        return True
    return len(set(_CHORE_THINGS.findall(clean))) > 1
A_JOB_SOMEBODY_ELSE_DOES = (
    "That's a job for a trade rather than a guess. Ask for the price in writing first, and what "
    "it includes.",
    "Worth two quotes on that one. The written quote that says what is included is the one to "
    "compare.",
    "That's a cost to land on you. Have you had a price for it yet, or is that the next step?",
    "Ugh, one of those. Get what they would do and what it costs in writing before anybody starts.",
)
# An attempt that failed, in the person's own words: "ive tried two cables", "i tried everything",
# "none of it worked", "still nothing", "no luck". A report of a fix that worked is not one of
# these ("i dried it with a hairdryer" keeps the glad line), so the line has to say the attempt
# did not settle it.
_TRIED_AND_IT_DID_NOT = re.compile(
    r"\b(?:ive|i'?ve|we'?ve|weve|i|we)\s+(?:already\s+)?(?:tried|attempted)\b"
    r"|\btried\s+(?:everything|it all|all of it|that|this|it|both|two|three|\w+\s+\w+(?:es|s))\b"
    r"|\bnothing\s+(?:works|worked|has worked|i try|i do)\b"
    r"|\b(?:didn'?t|doesn'?t|won'?t|wont|not)\s+work(?:ed)?\b"
    # "still no job" is not this shape. An attempt that failed says a try - "i tried two cables",
    # "none of it worked", "still nothing" - and the pool it reaches asks how the thing behaves
    # ("What does it do when you try it?", "Does it do the same thing every time?"). "still no
    # work" / "still no news" / "still no baby" name a thing the person has not got, and no such
    # thing behaves, so the questions are about a machine that is not there. A lack that is still
    # going on is read on its own below; only the words that report a try stay here.
    r"|\bno\s+luck\b|\bstill\s+(?:nothing|not|the same|doing it|happening)\b"
    r"|\bkeeps?\s+(?:doing|going|coming back|happening)\b"
    r"|\bgave up on it\b")
# A thing the person has not got, said again after time has passed: "still no job", "still no
# news", "still no baby", "im 41 and still no kids". Nothing here has gone wrong with a thing of
# theirs and nothing was tried, so there is no fault to ask about and no behaviour to ask after:
# what a friend asks is how the waiting is going. "still no milk" is the same shape and the same
# answer - a shop is a thing to do, not a fault to diagnose - so the pool says nothing about
# either, and no line in it says "try".
_STILL_NO = re.compile(r"\bstill\s+(?:no\s+[a-z]|without\s+[a-z]|not\s+got\b|havent\b|"
                       r"haven'?t\b|waiting\b)")
A_LACK_THAT_IS_STILL_GOING = (
    "That's dragging on. How are you holding up with it?",
    "That's a long stretch of waiting for it. Is anything moving on it at all?",
    "Still nothing, then. That wears you down - what's the part you can move?",
    "That's hard going. Is it something you can chase, or does it just take time?",
)
# A wait the person sat through: "i waited two hours", "we were queueing for ages".
_A_WAIT = re.compile(
    r"\b(?:i|we|he|she|they)\s+(?:was|were|have been|had been)?\s*wait(?:ed|ing)?\b"
    r"|\bqueue(?:d|ds|ing|s)?\b|\bin\s+the\s+queue\b|\bsat\s+in\s+(?:a|the)\s+waiting\b")
_A_LONG_WAIT = re.compile(r"\b(?:hours?|hrs?|ages|half an hour|an hour|two hours|all morning|"
                          r"all afternoon|\d+\s*(?:hours?|hrs?))\b")
# Somebody had a go at them about something of theirs: "my dad passed comment on my cooking",
# "she moaned at me about the garden", "he went on at me". The remark, not a punishment that
# landed (that is a refusal above), so the question is what was said.
_A_REMARK = re.compile(
    r"\bpassed\s+(?:a\s+)?(?:comment|remark|comments|remarks)\b"
    r"|\b(?:had|having)\s+(?:a\s+)?go\s+at\s+me\b"
    r"|\b(?:moaned|went on|nagged|lectured)\s+(?:at|to)\s+me\b"
    r"|\bsaid\s+something\s+(?:about|on)\s+my\b"
    r"|\bmade\s+a\s+(?:comment|remark|face)\s+about\b")
# A bill or a charge that says otherwise: "but i thought id already paid", "they say i owe for
# last month", "i was told it was free".
_A_DISPUTED_CHARGE = re.compile(
    r"\bbut\s+i\s+(?:thought|was\s+told|understood|believed)\b[^.!?]{0,44}"
    r"\b(?:paid|pay|included|free|covered|booked|settled|refund(?:ed)?)\b"
    r"|\b(?:they|it)\s+says?\s+i\s+owe\b|\bcharged\s+me\s+again\b"
    r"|\bi\s+was\s+told\s+it\s+was\s+(?:free|included)\b")
# A meal they went without, in the person's own words. The meal has to be named, because "i missed
# the bus" and "i skipped the gym" are the same verb about something that is not a meal, and the
# meal has to be theirs ("my lunch", "breakfast"), so "the kids skipped lunch" is somebody else's
# afternoon and keeps the reply it has.
_A_MEAL_MISSED = re.compile(
    r"\b(?:went|gone|go|going|was)\s+without\s+(?:my\s+|any\s+|a\s+|the\s+|our\s+)?"
    r"(?:lunch|dinner|tea|breakfast|supper|food|a\s+meal|meals|my\s+meal)\b"
    r"|\b(?:skipped|missed|skipping|missing)\s+(?:my\s+|a\s+|the\s+|our\s+|any\s+)?"
    r"(?:lunch|dinner|tea|breakfast|supper|a\s+meal|meals)\b"
    r"|\bno\s+(?:lunch|dinner|tea|breakfast|proper\s+meal)\b[^.!?]{0,14}"
    r"\b(?:again|today|yesterday|either)\b"
    r"|\b(?:worked|working)\s+through\s+(?:my\s+|a\s+|the\s+)?(?:lunch|dinner)\b"
    r"|\bforgot\s+(?:to\s+eat|my\s+(?:lunch|dinner|tea|breakfast|food))\b"
    r"|\bdidn'?t\s+(?:get|have|manage)\s+(?:any\s+|a\s+|my\s+)?(?:lunch|dinner|tea|breakfast|"
    r"(?:proper\s+)?meal)\b")
# The meal is skipped on purpose: a diet, fasting, a plan made with a doctor. None of those is a
# bad day, and "what happened - too busy to stop?" is the wrong question for one.
_A_MEAL_ON_PURPOSE = re.compile(
    r"\b(?:on\s+purpose|deliberately|on\s+purpose|by\s+choice|fasting|fast\s+day|intermittent|diet(?:ing)?|"
    r"cutting\s+(?:out|down)|trying\s+to\s+(?:lose|lose\s+weight)|skipping\s+meals\s+to)\b")
# "the kids skipped lunch", "he missed breakfast again": somebody else's day, and the question
# above asks about the person in front of the bot.
_SOMEBODY_ELSES_MEAL = re.compile(
    r"\b(?:the\s+kids?|the\s+children|my\s+(?:son|daughter|boy|girl|lad|lass|husband|wife|partner|mum|mom|"
    r"dad|brother|sister|friend|mate|flatmate|housemate)|he|she|they)\b")
# The person in front of the bot, named as the one it happened to: "i went without my lunch".
# "my son missed lunch at school" is theirs too but it happened to somebody else, so the
# pronoun is the test rather than the possessive.
_MINE_OR_OURS = re.compile(r"\b(?:i|ive|i'?m|im|i'?ve|we|weve|we'?ve|myself)\b")


# A line that opens as an ask is an ask, whether or not it carries a question mark: "what if i
# tried again", "does it still work", "should i give up on it" all wear one of the shapes below
# and all have an answer of their own.
_AN_ASK_OPENING = re.compile(
    r"^(?:what|how|why|when|where|which|who|whose|is|are|was|were|do|does|did|can|could|should"
    r"|would|will|shall|am|may|might|any\s+chance|isnt|arent|doesnt|dont|didnt)\b")


def reads_as_stuck_with_it(clean):
    """True when the line reports an attempt that failed, a wait, a remark that stung or a bill.

    Whole shapes only, and never an ask: "what if i tried again" and "how long should i wait"
    are questions with an answer of their own, and they are answered where they are read.
    """
    if not clean or "?" in clean or NOT_GOOD_DESPITE.search(clean):
        return False
    if _AN_ASK_OPENING.match(clean):
        return False
    if _A_DISPUTED_CHARGE.search(clean):
        return True
    if _A_REMARK.search(clean):
        return True
    if _TRIED_AND_IT_DID_NOT.search(clean):
        return True
    return bool(_A_WAIT.search(clean) and _A_LONG_WAIT.search(clean))


def reads_as_not_good(clean):
    """True when the line is a thing of theirs that has been damaged, taken, refused or fallen."""
    if not clean or NOT_GOOD_DESPITE.search(clean):
        return False
    if reads_the_shake(clean):
        return True
    return any(pattern.search(clean) for pattern in NOT_GOOD)


def reads_the_shake(clean):
    """True when the line is a near miss or a fright - nothing landed, they are still shaken."""
    if not clean or NOT_A_FRIGHT.search(clean):
        return False
    if _A_PLAN_THAT_FELL_THROUGH.search(clean):
        return False
    if (_A_BARE_NEAR_MISS.search(clean) and _A_THING_WITH_NO_BODY.search(clean)
            and not _A_BODY_CAN_BE_HURT.search(clean)):
        return False
    return bool(NEAR_MISS.search(clean) or FRIGHT.search(clean))


# Whose shake it is. "he is ok just shaken" and "my mum had a fright" are not about the person the
# bot is talking to, and "Are you okay now?" asks the wrong one: a reply is about the line's
# subject or it is not about the line at all. A line that opens on "my car" is not here - that is
# the person's own car - so the person nouns are the ones that count.
_SHAKE_IS_THEIRS = re.compile(r"^\s*(?:he|she|they|him|them|his|her|their)\b")


def reads_the_shake_of_someone_else(clean):
    """True when the near miss or the fright happened to somebody the person is telling us about."""
    if not reads_the_shake(clean):
        return False
    return bool(_SOMEONE_ELSE.search(clean) or _SHAKE_IS_THEIRS.match(clean))


def reads_as_glad(reply):
    """True when the reply congratulates the news, or is a receipt of it with nothing after."""
    if not reply:
        return False
    line = reply.strip().lower()
    return bool(GLAD_OPENER.match(line) or GLAD_ANYWHERE.search(line)
                or BLANK_OR_THIN.match(line))


def reads_as_a_meal_missed(clean):
    """True when the line says they went without a meal of their own.

    A meal has to be named ("i missed the bus", "i skipped the gym" are the same verb about
    something else) and it has to be the person in front of the bot who went without it: "my son
    missed lunch at school" happened to somebody else, and "i skip lunch on purpose" is a plan
    rather than a bad day.
    """
    if not clean or "?" in clean:
        return False
    if _A_MEAL_ON_PURPOSE.search(clean):
        return False
    if not _A_MEAL_MISSED.search(clean):
        return False
    return bool(_MINE_OR_OURS.search(clean) or not _SOMEBODY_ELSES_MEAL.search(clean))


def reads_as_a_no_they_had(clean):
    """True when the line reports somebody refusing the person something.

    A question is not a report ("should i say no to her"), a line the person said no in is their
    own limit ("i said no", "we said no to the quote"), and a machine that will not start is not a
    person: "my car won't start" is the car's answer.
    """
    if not clean or "?" in clean:
        return False
    if len(str(clean).split()) > 14:
        return False
    if _A_NO_STILL_BEING_WEIGHED.search(str(clean)):
        return False
    if re.match(r"^(?:i|we)\b", str(clean)) and not re.search(
            r"\b(?:she|he|they|my|our|the)\b", str(clean)):
        return False
    return bool(_A_SAID_NO.search(str(clean)) or _A_REFUSED.search(str(clean)))


def _who_said_no(clean, memory):
    """Who refused, said the way the person would hear it back: "your boss", "the council"."""
    if _A_REFUSAL_IN_THE_PASSIVE.search(str(clean or "")):
        # In "my claim was refused" the "my" is the thing refused, not the person who refused it.
        return ""
    who = ""
    match = re.search(r"\b((?:my|our|the)\s+[a-z]+|mum|dad)\b", str(clean or ""))
    if match:
        who = match.group(1)
    if not who:
        lean = ((memory or {}).get("understood") or {}).get("leans_on") or {}
        subject = str(lean.get("subject") or "").strip().lower()
        if subject and lean.get("subject_type") == "person":
            who = subject
    if not who:
        return ""
    return " ".join(_MINE.sub("your", who, count=1).split())


def answer_for(text, memory=None, reply=None):
    """A rotten thing answered as rotten, or None.

    Called with the reply the composer chose, because the whole point is that no other module
    wanted the turn: a line that has an answer of its own keeps it.
    """
    if not reads_as_glad(reply):
        return None
    memory = memory or {}
    clean = ((memory.get("understood") or {}).get("clean") or text or "").lower()
    clean = " ".join(clean.split())
    if reads_the_shake(clean):
        # The shake is asked about before the resolved check: "i got a fright but im ok" says both,
        # and the ok is the reason the reply is a warm line and not a plan, not a reason to say
        # nothing. It also comes before `reads_as_not_good`, which is where this reading lives on
        # its own: a fright is not damage, and the pools below are for a thing that was broken,
        # taken or refused.
        if reads_the_shake_of_someone_else(clean):
            mine = A_NEAR_MISS_ELSE if NEAR_MISS.search(clean) else A_FRIGHT_ELSE
        elif NEAR_MISS.search(clean):
            mine = A_NEAR_MISS
        else:
            mine = A_FRIGHT
        return pick(list(mine), memory, clean)
    if RESOLVED.search(clean):
        return None
    if reads_as_a_meal_missed(clean):
        # A meal they went without is not a thing that was damaged and not a failed attempt: the
        # question is whether the day had no time in it or the house had no food in it.
        return pick(list(A_MEAL_THEY_WENT_WITHOUT), memory, clean)
    if (_A_JOB_NEEDED.search(clean) and not _A_PERSON_NEEDING.search(clean)
            and not _A_JOB_THAT_IS_SORTED.search(clean)):
        if _NOT_A_TRADE.search(clean):
            # Work of their own with no trade behind it: a chore waiting, which wants the move that
            # makes the work smaller rather than a quote. One job and a pile of them are answered
            # differently, because the number is what the line actually said.
            pool = A_CHORE_PILE if _a_pile_of_chores(clean) else A_CHORE_WAITING
            return pick(list(pool), memory, clean)
        # A job that needs doing is not a thing that broke and not an attempt that failed: the
        # question is what is written down before anybody starts, which is what sets the bill.
        return pick(list(A_JOB_SOMEBODY_ELSE_DOES), memory, clean)
    if _STILL_NO.search(clean) and not _A_WAIT.search(clean):
        # A lack that is still going on, and not an attempt at a fix: the question is the waiting,
        # which is the only thing the line actually said.
        return pick(list(A_LACK_THAT_IS_STILL_GOING), memory, clean)
    if reads_as_stuck_with_it(clean):
        # The attempt that failed, the wait, the remark that stung and the bill that says
        # otherwise are not a thing that was damaged: each has its own question, and none of
        # them is a day that went well.
        if _A_DISPUTED_CHARGE.search(clean):
            pool = A_BILL_THAT_SAYS_OTHERWISE
        elif _A_REMARK.search(clean):
            pool = A_REMARK_THAT_STUNG
        elif _A_WAIT.search(clean) and _A_LONG_WAIT.search(clean):
            pool = A_WAIT_THAT_WENT_ON
        else:
            pool = A_THING_THAT_DID_NOT_WORK
        return pick(list(pool), memory, clean)
    if not reads_as_not_good(clean):
        # A refusal is asked last of all the readings here, so a line this file already answers as
        # a damaged, taken or blown thing keeps that answer: "my visa was refused" is a blow from
        # somebody, and "she already said no once" is not read by any of them.
        if not reads_as_a_no_they_had(clean):
            return None
        who = _who_said_no(clean, memory)
        pool = A_NO_FROM if who else A_NO_ALREADY
        line = pick(list(pool), memory, clean + "|" + who)
        return line.format(who=who) if who else line
    if _FALL.search(clean):
        pool = A_FALL_ELSE if _SOMEONE_ELSE.search(clean) else A_FALL
    elif _FROM_SOMEONE.search(clean):
        pool = A_BLOW_FROM_SOMEONE
    else:
        pool = DAMAGED_OR_TAKEN
    return pick(list(pool), memory, clean)
