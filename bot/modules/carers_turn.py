"""The turn after a safety answer that was about somebody else.

When safety.py has just answered about a person the speaker is looking after, the next line is
nearly always one of six things, and the composer had no reader for any of them, so they were
answered as if the safety card had been about the person typing:

* the reasurance in the carer's own words - "he says hes fine", "she swears its nothing", "the
  doctor says its just bruising";
* a recovery that has lasted - "hes been sober six months", "she hasnt used in two years";
* the easing - "hes come round now", "shes sitting up and talking", "hes asleep now";
* the easing with a tail that undoes it - "hes come round but hes confused";
* an abuse thread's own continuation - "he says hes sorry", "he promised he will change", "he
  says its my fault", "i dont have anywhere to go";
* the apology, the promise, the flowers, the "it was my fault" that follows.

Each of them was answered with the instruction for a crisis in the room. After "my boyfriend hit
me", "he says hes sorry" got "Keep your boyfriend close tonight and ask him again tomorrow.
Ringing 116 123 with him there is easier than ringing it for him" - the person who did the hitting
put in the room as somebody to look after. After "my son had a fit on the sofa", "hes asleep now"
got "If you haven't already, ring 999 or 911 now" said again to somebody who had just said the
worst was passing. After "my friend tried to kill himself", "he says hes fine" got "take anything
he could take out of the room".

Two rules run through every pool here. The line is answered about the person it is about - "your
dad", "him", never "you" - and the safety card above is never simply said again. Nothing is
invented: where the answer depends on facts the bot cannot see (whether the next one is really
coming, which refuge has space tonight), the reply names the person or the line that can tell.

This is a module beside the fallback rather than a change inside it, because `bot/compose/
fallback.py` is past the world's per-file size limit and no change to it can be submitted. It sits
at PRIORITY -998, above the greeting band (PRIORITY -1000) and below every knowledge module, so it
only ever answers a line that nothing else has answered, and only when the safety turn directly
above was about somebody else.

It declares `ANSWERS_INSTEAD`, because a line it reads whole is a line no entry can answer: the
thread's own subject is not a topic of the world. Without the declaration the arbiter's specialist
rule hands the third turn to whichever row matched a word of the turn before it - after "my
husband hit me" / "hes been drinking again", "should i leave" was answered with the UK drinking
limits.
"""
import re

from ..compose import fallback as _fallback
from ..compose.fallback_data import CRISIS_BETTER_THEM, CRISIS_WORDS

PRIORITY = -998

# The turn after a safety answer is read whole here and answered in place of the topic entries.
# Without this the specialist rule hands the next line to whichever entry matched a word of the
# turn above: after "my husband hit me" / "hes been drinking again", "should i leave" got the
# units card ("The UK limit is 14 units a week...") over this module's plan answer, because the
# drink in the middle turn was read as the subject of a question about leaving. The module proposes
# only on the lines it recognises, so this is a door and not a band: PRIORITY stays where it is, and
# a module that answers the same line better can still keep the turn through `DEFERS_TO`.
ANSWERS_INSTEAD = ("abuse", "carers", "safety")

# What the answer above asked them to do: a route out of the house, which an easing does not
# settle. Read from the answer, because it is the answer that says whether the worst of it is
# being held open.
ROUTE_NAMED = re.compile(
    r"\b(?:999|911|112|111|a\s?&\s?e|a and e|accident and emergency|ambulance|paramedic|"
    r"urgent care|out of hours|x-ray)\b")

# ---------------------------------------------------------------------------------------------
# The easing: the carer's report that their person is through the worst of it.
THEY_ARE_EASING = re.compile(
    r"\b(?:he|she|they|dad|mum|mom|nan|gran|granny|grandma|grandad|grandpa|son|daughter|"
    r"husband|wife|partner|brother|sister|baby|kid|child|boy|girl|little one|friend|neighbour)"
    r"(?:'s|s| is| are| was| were| has| had)?\b\s+"
    r"(?:(?:come|came|coming)\s+(?:round|to|back round|back to)\b"
    r"|(?:awake|conscious|alert|with it|responsive|breathing (?:ok|okay|normally|fine|easier|"
    r"better|properly))\b"
    r"|(?:sat|sitting) up\b"
    r"|(?:talking|chatting|eating|drinking) (?:now|again)\b"
    r"|(?:asleep|sleeping|snoozing|dozing|resting)\b"
    r"|(?:up and about|on the mend|out of the woods|over the worst)\b)")
# The easing with a tail that undoes it: "hes come round but hes confused", "shes sitting up but
# shes grey". The half after the "but" is the one to answer.
EASING_UNDONE = re.compile(
    r"\b(?:confus\w*|not (?:making sense|himself|herself|themselves|with it|right)|"
    r"blue|grey|gray|pale|clammy|shaking|shaky|dizzy|feverish|burning up|bleeding|sick|"
    r"vomit\w*|wont wake|won't wake|cant wake|can't wake|unresponsive|limp|floppy|slurr\w*|"
    r"breathing (?:oddly|strangely|badly|funny))\b")
# A question about them is not a report on them: "is he awake now" asks.
THEM_ASKING = re.compile(
    r"^(?:is|are|was|were|has|have|had|did|does|do|will|would|can|could|should|shall|any)\b")
EASING_NOT_ONE = re.compile(
    r"\b(?:not|isnt|isn't|arent|aren't|wasnt|wasn't|wont|won't|cant|can't|couldnt|didnt|doesnt|"
    r"hasnt|havent|still|worse|but|except|though|shaking|shaky|confused|blue|grey|pale|burning|"
    r"hot|fever|bleeding|sick|vomit\w*|dizzy|gone)\b|\?")
# A line that moves on ("what about tomorrow", "anyway") is not a report on their person.
MOVE_ON = re.compile(
    r"\b(?:anyway|what about|how about|what if|should i|shall i|do i|can i|im going to|"
    r"ill (?:go|ring|call|take)|what do i (?:do|say))\b")

# The person themselves playing it down, as the carer reports it: "he says its nothing", "she
# reckons its just a scratch", "they kept telling me not to worry". Only the reported words count:
# "he says he will stop" is a promise, and the thread's own pool answers that one.
THEY_SAY_ITS_FINE = re.compile(
    r"\b(?:says?|said|telling|tells?|told|insists?|insisted|reckons?|thinks?|swears?|"
    r"claims?|assures?|keeping\s+on\s+about|keeps?\s+saying)\b[^.!?]{0,26}?"
    r"\b(?:its|it's|hes|he's|shes|she's|theyre|they're|im|i'm)\b\s*"
    r"(?:nothing|fine|ok|okay|alright|all\s+right|not\s+(?:that|too|so)\s+bad|no\s+big\s+deal|"
    r"nothing\s+to\s+worry\s+about|just|only|a\s+bit|a\s+little|bruis\w*|"
    r"a\s+scratch|a\s+bump)\b"
    r"|\b(?:told|asked|telling|asking|begged)\s+me\s+not\s+to\s+(?:worry|fuss|make\s+a\s+fuss|"
    r"bother|think\s+about\s+it)\b"
    r"|\b(?:said|says|told\s+me|kept\s+saying|keeps?\s+saying)\s+nothing\s+(?:to\s+worry|"
    r"was\s+wrong|is\s+wrong|wrong)\b")

# Recovery that has lasted: the length is the tell, and it is what makes the crisis pool's
# instruction for tonight the wrong reply.
_MONTHS = (r"(?:\d+|a|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
           r"a\s+few|several)\s+(?:days?|weeks?|months?|years?)")
THEY_ARE_RECOVERING = re.compile(
    r"\b(?:sober|clean|dry|straight|drugs?[- ]?free|off\s+(?:it|the\s+drink|the\s+booze)|"
    r"self[- ]harm\s+free)"
    r"\b[\w\s,'-]{0,14}?\b" + _MONTHS +
    r"|\b" + _MONTHS + r"\s+(?:sober|clean|dry)\b"
    r"|\b(?:hasnt|has\s+not|havent|have\s+not|hadnt)\s+"
    r"(?:touched|used|drunk|drank|self[- ]harmed|cut|relapsed)\b[\w\s,'-]{0,14}?\b"
    r"(?:in|for)\s+" + _MONTHS)

# ---------------------------------------------------------------------------------------------
# The abuse thread. The card for it names a domestic abuse helpline, and "helpline" is one of the
# words that says a crisis answer is above, so every continuation was read as a crisis to sit with
# and the person who did the hitting was put in the room.
ABUSE_ANSWER = re.compile(
    r"domestic abuse|abuse helpline|0808 2000 247|1-800-799-7233|"
    r"what's happening to you is abuse|what is happening to you is abuse")
# The other card: the one written for the person doing the hitting (Respect, the men's advice
# line). None of these pools may answer it - "none of this is your fault" said to somebody who hit
# somebody is the worst line this file could produce.
ABUSER_ANSWER = re.compile(
    r"0808 802 4040|people\s+who\s+are\s+violent|hitting\s+someone\s+you\s+live\s+with\s+is\s+"
    r"abuse|that\s+is\s+abuse,\s+and")
# The apology, the promise, the flowers, the sudden kindness.
THE_APOLOGY = re.compile(
    r"\b(?:sorry|apolog\w+|wont\s+happen\s+again|won't\s+happen\s+again|"
    r"promis(?:e|ed|es)|will\s+change|has\s+changed|is\s+changing|getting\s+help|"
    r"doing\s+something\s+about\s+it|didn'?t\s+mean|didnt\s+mean|not\s+like\s+(?:him|her|that)|"
    r"only\s+did\s+it\s+once)\b")
# The kindness that comes with the cycle: an apology, flowers, "he says he loves me", the good
# fortnight. It can be meant and it is not the thing that changes.
THE_KINDNESS = re.compile(
    r"(?:says|said|told\s+me)\s+(?:that\s+)?(?:he|she)\s+loves\s+me|"
    r"(?:he|she)\s+loves\s+me\s+really|bought\s+me|flowers|"
    r"being\s+(?:really\s+)?(?:nice|sweet|lovely)\s+now|making\s+up\s+for\s+it|"
    r"only\s+does\s+it\s+when|been\s+(?:really\s+)?(?:good|lovely)\s+(?:since|this\s+week)")
# The drink, said as the explanation: it is the pattern that is the danger, and it is not an
# apology, so it must not be answered with the apology's line.
THE_DRINK = re.compile(
    r"\b(?:was|were|is|gets?|been)\s+(?:drunk|drinking|on\s+something)\b|"
    r"\bhe\s+drinks\b|\bwhen\s+he\s+drinks\b|\bdrinks\s+every\s+(?:day|night)\b")
# The person asking whether they caused it, because they were told that they did.
THEIR_OWN_FAULT = re.compile(
    r"\b(?:was|is|wasnt|isnt)\s+it\s+(?:my|mine)\b|\bdid\s+i\s+(?:do\s+something|make|cause|"
    r"provoke|push|wind)\b|\bmy\s+fault\b|\b(?:i|we)\s+provoked\b|\bwhat\s+did\s+i\s+do\b|"
    r"\b(?:i|we)\s+(?:made|make|caused|provoked|wound\s+up|annoyed)\s+"
    r"(?:him|her|them|my\s+\w+)\s+(?:angry|mad|furious|do\s+it|lose\s+it|lash\s+out|hit|upset)\b|"
    r"\bmaybe\s+it\s+was\s+me\b|\bprobably\s+my\b|"
    # The amends the person offers to make: the same reading as "was it my fault", said as a plan.
    # "how do i make it up to him" after the drink was answered by the chat's own amends line,
    # which is written for a row between equals and hands the person the job of repairing what was
    # done to them (mint-brick, #13830).
    r"\bhow\s+(?:do|can|should)\s+i\s+(?:make\s+(?:it|things)\s+up|make\s+it\s+right|"
    r"put\s+it\s+right|make\s+amends)\b|"
    r"\b(?:should|shall|do)\s+i\s+(?:apologise|apologize|say\s+sorry)\b|"
    r"\bi\s+(?:should|ought\s+to)\s+(?:apologise|apologize|say\s+sorry)\b|"
    r"\bmake\s+(?:it|things)\s+up\s+to\s+(?:him|her|them|my\s+\w+)\b")
# The next one, said as a promise.
THREAT_AGAIN = re.compile(
    r"\b(?:will|would|going\s+to|gonna|wont|is\s+going\s+to)\s+(?:do\s+it|kill|hurt|hit|"
    r"beat)\s+(?:me\s+)?again\b|\bnext\s+time\b|\bthreaten\w*|\bhe\s+said\s+he.?d\s+"
    r"(?:kill|hurt|hit)\b|\bsaid\s+hed\s+(?:kill|hurt|hit)\b|\bhell\s+do\s+it\s+again\b")
# A nod, a thank you, or a close: the thread is ending and the fallback's own pools for those
# lines ("Anytime. Look after yourself") are the right ones, not an abuse thread's holding line.
NODDING_ALONG = re.compile(
    r"^\W*(?:ok|okay|k|kk|thanks|thank\s+you|cheers|ta|right|yeah|yes|no|bye|goodnight|"
    r"night|fair\s+enough|got\s+it)\W*$")
# The thread has closed over: "were okay now", "hes fine now". The reassuring line that keeps the
# question open is for the person playing it down, not for the carer saying it is over.
THE_TROUBLE_IS_OVER = re.compile(
    r"\b(?:(?:we(?:'re| are)?|were|weve)\s+(?:okay|ok|fine|good)|all\s+good\b|"
    r"its\s+fine\s+now\b|"
    r"(?:he|she|they)(?:'s|s|\s+is|\s+are)?\s+(?:fine|okay|ok|alright)\s+now\b|"
    r"no\s+worries\b|sorted\s+now\b)")
# Nowhere to go, no money, or nobody to turn to.
NO_WAY_OUT = re.compile(
    r"\bnowhere\s+(?:to\s+go|to\s+stay|else\s+to\s+go|safe)\b|\bno\s+way\s+out\b|"
    r"\bno\s+money\s+to\s+(?:leave|go)\b|\bcan'?t\s+(?:leave|afford\s+to\s+leave)\b|"
    r"\bcant\s+(?:leave|afford\s+to\s+leave)\b|\bno\s+one\s+to\s+turn\s+to\b|"
    r"\bdont\s+have\s+anywhere\b|\bdon'?t\s+have\s+anywhere\b")

# ---------------------------------------------------------------------------------------------
# What is swallowed goes on harming after it starts to feel easier, and that is the one easing
# where a wait cannot be the answer: a collapse that eases is a doctor today, an overdose that
# eases is the line now.
SWALLOWED_NOT_RELIEF = re.compile(
    r"\b(?:overdos\w*|poison\w*|swallow\w*|paracetamol|ibuprofen|bleach|antifreeze|pills|"
    r"tablets|capsules|carbon\s+monoxide|took\s+(?:too|a\s+load|a\s+bunch|loads))\b")
# The person running out of room for it. Not a request for the plan and not a question about him,
# so this file used to stand down wholly and let the thread answer - and the thread was an
# apology, so "i cant take it any more" three turns after the abuse card came back as "Name what
# you did, say why it was wrong" (steward-spare-finch, #13830). The words are the whole of the
# signal: somebody who says they cannot carry it any more is not asking how to apologise.
TOO_MUCH_TO_CARRY = re.compile(
    r"\b(?:i|we)\s+(?:can'?t|cant|couldn'?t|couldnt)\s+(?:take|do|keep\s+(?:doing\s+)?|carry|"
    r"handle)\s*(?:it|this|any\s*more|anymore|much\s+more)\b"
    r"|\b(?:i|we)\s+(?:can'?t|cant)\s+(?:take|do)\s+(?:any\s*)?more\b"
    r"|\bi\s+(?:can'?t|cant)\s+cope\b"
    r"|\b(?:its|it'?s|it\s+is)\s+too\s+much\s+(?:for\s+me|to\s+(?:take|carry|bear))\b", re.I)
# The safety answer can open by asking the carer the one thing that decides what happens next:
# "Is it just bruising, or is something not right?" An easing does not answer that, so it must
# not be read as the answer - the question stays open, in the carer's hands.
THE_ANSWER_ASKED_A_QUESTION = re.compile(r"^[^.!]*\?")
ANSWERED = re.compile(
    r"^\W*(?:yes|yeah|yep|no|nope|not|its\s+just|it\s+is\s+just|just|only|nothing|"
    r"bruis\w*|she\s+says|he\s+says|they\s+say|i\s+think\s+it|i\s+checked)")

# The pools. Every line is about their person, and every one of them keeps the question open.
NOT_RIGHT_AFTER_THE_WORST = (
    "That is 999 or 911 rather than a wait and see - coming round and then not being right is "
    "the thing they want to hear about, so say what you saw when it started. Stay with {who} and "
    "keep {obj} still until they come.",
)
NOT_OUT_OF_THE_WOODS = (
    "That it passed is not the same as being safe. Stay with {who} and get {obj} seen today, and "
    "say what happened when it started - a fit, a fall or a collapse wants a doctor the same day.",
    "Good that it eased, and it does not cancel the check: {who} needs to be seen today, not left "
    "to sleep it off. Ring 111 or the number you were given and say what happened, and stay until "
    "somebody has looked.",
)
SWALLOWED_BETTER = (
    "With something swallowed the harm can go on for hours after it starts to look better, and "
    "that is why it is the line now rather than later. Ring 999 or 911, say what {subj} took and "
    "when, and keep the packet to read from.",
    "That it eased does not mean it is over - what was swallowed goes on working after somebody "
    "starts to feel better, and the amount and the time are what the line needs. Ring 999 or 911 "
    "now, and stay with {who} until somebody has looked.",
)
BEFORE_THE_ANSWER = (
    "That is the better sign, and it does not answer what you were asked: it is the confusion, "
    "the grey colour or the not-making-sense that decides this one, not how settled {subj} looks. "
    "If any of that is there, or comes back, it is 999 or 911 - otherwise get {obj} seen today.",
    "Glad to hear it, and keep the question open rather than take it as answered: what decides it "
    "is whether {subj} is properly with it, not how settled {subj} looks. Watch for the change - "
    "drowsy, confused, or not right - and ring 999 or 911 if it comes.",
)
ITS_FINE = (
    "Take it as a good sign rather than the whole of it. Keep the number where {who} can see it, "
    "and ask again tomorrow - the question is easier the second time.",
    "Good that {subj} said it out loud, and what someone says when they are asked is often the "
    "hope rather than the plan. Keep the question open and ask again when it is quiet.",
    "It is worth hearing, and it does not settle it - people play it down at first. What helps is "
    "staying close tonight and asking {obj} again in the morning.",
)
RECOVERING = (
    "That is a real stretch behind {obj}, and worth saying out loud. Nothing to do about it now "
    "except keep the door open: the crisis line on a bad night, and the GP if {subj} would like "
    "the help to keep going.",
    "That is good news, and it is the kind that holds with company rather than on its own. Keep "
    "the number where {subj} can find it, and take the good months as they come.",
)
AFTER_THE_KINDNESS = (
    "It can be meant, and it is the part most people are offered at this stage. Keep it alongside "
    "the rest rather than instead of it: somewhere you could go tonight, your keys and phone "
    "where you can reach them, and the abuse line's number in the phone.",
    "Good weeks between the bad ones are what makes this hard to name, and they do not cancel the "
    "bad ones out. Note down what happened and when, keep the number 0808 2000 247 in the UK "
    "(1-800-799-7233 in the US) close, and let somebody hear all of it rather than the good part.",
)
AFTER_THE_APOLOGY = (
    "An apology after it happens is usual, and it is not the part that changes anything - a change "
    "is something you would see over months, not in the hour afterwards. A domestic abuse line "
    "(0808 2000 247 in the UK, 1-800-799-7233 in the US) will plan the next step with you when it "
    "is safe to talk.",
    "It can be meant, and it is the part most people are offered at this stage. Keep it alongside "
    "the rest rather than instead of it: somewhere you could go tonight, your keys and phone "
    "where you can reach them, and the abuse line's number in the phone.",
)
IT_IS_NOT_YOUR_FAULT = (
    "No. Nothing you said or did makes it your fault, and the choice to hit was theirs. If it "
    "would help to hear it from somebody who hears this all day, the abuse line is free and "
    "answers any hour.",
    "It is not your fault, and what happened was not a reaction to something you did - hitting is "
    "a thing a person chooses to do. A domestic abuse line (0808 2000 247 in the UK, "
    "1-800-799-7233 in the US) will say that out loud with you and plan from there.",
)
THE_NEXT_ONE = (
    "Saying it will happen again is the thing to act on rather than wait out: ring 999 or 911 if "
    "you are in danger now, and take what you would need to leave with you - keys, phone, "
    "medication. The abuse line (0808 2000 247 in the UK) will plan the rest with you.",
    "That is a threat, and a threat like that is what turns into the next one. Get somewhere with "
    "other people in it tonight, ring 999 or 911 the moment you are frightened, and 0808 2000 247 "
    "will work out where you could go if you would rather not go alone.",
)
NOWHERE_TO_TURN = (
    "There is somewhere to go, and it is arranged through the abuse line rather than looked up "
    "tonight: 0808 2000 247 in the UK (1-800-799-7233 in the US) will say what is free near you, "
    "and refuges keep their addresses off the open internet for the obvious reason. Take your "
    "keys, your phone, any medication, and whatever papers you can reach.",
    "Refuges exist for exactly this, and the abuse line (0808 2000 247 in the UK, 1-800-799-7233 "
    "in the US) knows which ones have space tonight - that is the thing it does all day, and it "
    "does not need you to have decided anything. If getting to a phone is not safe, one person "
    "you trust is enough of a start.",
)
# A line about them keeps the thread; a line about something else does not. Without this, "i keep
# falling asleep in the afternoon" after "my husband hit me" was answered out of the abuse holding
# pool, which is the wrong subject and the wrong tone.
ABOUT_THE_THREAD = re.compile(
    r"\b(?:he|him|his|she|her|hers|they|them|their|we|us|our|my\s+(?:partner|husband|wife|"
    r"boyfriend|girlfriend|ex|dad|mum|father|mother|son|daughter|brother|sister|friend)\b)|"
    r"\b(?:what\s+should\s+i\s+do|what\s+do\s+i\s+do|how\s+do\s+i\s+get\s+out|"
    r"who\s+can\s+i\s+call|where\s+can\s+i\s+go|should\s+i\s+leave)\b"
    r"(?:\s+(?:now|next|though|then))?\s*(?:[.?!,]|$)")
# A person who asks for another subject is asking for this thread to stop, and every pool here is
# about this thread. "can we talk about something else" after the abuse card was answered with the
# plan again, because `ABOUT_THE_THREAD` reads the "we" in "can we talk" - the bare pronoun is
# right for "we had a row" and wrong for this. The other five ways of saying it already stood
# down; this is the shape that did not (steward-teal-donkey, #13830).
# Letting the thread go. The person has heard what the card and the pools had to say and has asked
# for another subject, which is theirs to do: the answer is to hand the turn back rather than to
# keep going, and to say it warmly so that coming back later still feels possible.
CHANGED_SUBJECT = (
    "Fair enough - what is on your mind instead?",
    "Of course. Anything you would rather talk about? I am here for it.",
    "That is all right, we can leave it there. What else is going on with you?",
)
CHANGE_THE_SUBJECT = re.compile(
    r"\b(?:can|could|shall|would)\s+(?:we|i)\s+(?:please\s+|just\s+)?"
    r"(?:talk|chat|speak)\s+about\s+(?:something|anything|summat|another\s+thing|"
    r"a\s+different\s+(?:thing|subject))\b"
    r"|\b(?:can|could|shall)\s+we\s+(?:please\s+|just\s+)?"
    r"(?:change|drop|leave)\s+(?:the\s+subject|it|this|that)\b"
    r"|\bi\s*(?:'| a)?m\s+not\s+(?:sure\s+i\s+want|going)\s+to\s+talk\s+about\b"
    r"|\bi\s+do\s?n'?o?t\s+want\s+to\s+talk\s+about\s+(?:it|this|that|him|her|them)\b"
    r"|\blet'?s\s+(?:not\s+)?(?:talk|chat)\s+about\s+(?:something|anything)\s+else\b"
    r"|\blet'?s\s+not\s+(?:talk|chat)\s+about\s+(?:it|this|that)\b"
    r"|\benough\s+about\s+(?:that|it|this)\b"
    r"|\bmoving\s+on\s+from\s+(?:this|that|it)\b"
    r"|\b(?:something|anything)\s+else\s+(?:instead|for\s+a\s+bit|for\s+now)\b"
    r"|\b(?:im|i\s+am|ive)\s+(?:done|finished)\s+talking\s+about\b"
    r"|\b(?:drop|leave|park)\s+it\s+(?:for\s+now|please)\b")
ABOUT_THE_INCIDENT = re.compile(
    r"\b(?:its\s+not\s+that\s+bad|not\s+that\s+bad|it\s+wasn't\s+that\s+bad|only\s+once|"
    r"it\s+was\s+my\s+fault|it\s+was\s+an\s+accident|he\s+didn'?t\s+mean|"
    r"she\s+didn'?t\s+mean|it\s+just\s+happened)\b")
AFTER_THE_DRINK = (
    "The drink is the part that makes the rest of it more likely rather than less, and it is not "
    "the reason it is allowed to happen. A domestic abuse line (0808 2000 247 in the UK, "
    "1-800-799-7233 in the US) hears this version of it all day: they will plan around the nights "
    "it is worse, and the number is free at any hour.",
    "A night that goes that way when {subj} has been drinking is still {subj} choosing it, and the "
    "pattern is what to plan for - where you would go, what you would take, who would come. The "
    "abuse line (0808 2000 247 in the UK) will do that planning with you, sober hours or not.",
)
THE_BAG = (
    "Phone, keys, medication, and the papers you can reach - passport, bank cards, birth "
    "certificates - plus a change of clothes. One bag you can carry, and nothing you would have "
    "to go back for. The abuse line (0808 2000 247 in the UK, 1-800-799-7233 in the US) will say "
    "what a refuge has already, so you are not packing for a fortnight.",
    "Smaller than people expect: phone and charger, keys, medication, papers, cards, and whatever "
    "the children cannot sleep without if they are coming. A bag by the door is also the thing "
    "that makes tonight's decision a smaller one.",
)
THE_LOAD_IS_TOO_MUCH = (
    "You have been holding that on your own, and it is too much for one person to hold. Is there "
    "one person you could tell today - a friend, a sister, a neighbour - even if it is only that "
    "you are not coping?",
    "Of course you are worn out: nothing about this is small, and saying so is not a failure. The "
    "abuse line (0808 2000 247 in the UK, 1-800-799-7233 in the US) answers at any hour, and you "
    "do not have to have decided anything to ring it.",
    "That is a lot to carry with no let-up, and you do not have to work out where it ends "
    "tonight. Tell one person you trust today, and keep 0808 2000 247 (1-800-799-7233 in the US) "
    "in the phone for the hour it gets to be too much.",
)
STILL_THE_SAME_THREAD = (
    "What you do next is your call, and it is an easier call with somebody who hears this all "
    "day: 0808 2000 247 in the UK, 1-800-799-7233 in the US, free and any hour. Tonight: keys, "
    "phone and money where you can reach them, and one person you could go to.",
    "It does not have to have been the worst night of it to count - these threads mostly start "
    "small and get worse. Keep a note of what happened and when, somewhere only you can open, and "
    "keep the abuse line's number where you can find it in a hurry.",
)


def _clean(text):
    return " ".join(str(text or "").lower().split())


def _turns(memory):
    try:
        return [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    except AttributeError:
        return []


def _the_answer_above(memory):
    """The turn directly above this line, or None when it is not one this file answers after.

    The safety card, and then this file's own answers for as long as the thread stays an abuse
    thread. The second is what keeps a third and fourth turn in the same reading: the card was
    answered two turns up, the turn directly above was this file's reply to an apology, and the
    line was "should i leave" - which stood down here because the module above was not safety's,
    and was then answered from whichever pool held the apology, so the person who had been hit
    was asked to name what they did and say why it was wrong (magenta-pine, #13295). A thread
    that is not about abuse still has to have safety's answer directly above: "my dad collapsed"
    then "hes come round now" keeps the carer reading.
    """
    turns = _turns(memory)
    if not turns:
        return None
    last = turns[-1]
    module = str(last.get("module") or "")
    if module in ("safety", "safety_cards"):
        return last
    if module == "carers_turn" and any(
            _an_abuse_thread(str(turn.get("bot") or "")) for turn in turns[:-1]):
        return last
    return None


def _reads_as_easing(clean):
    """A report that their person is through the worst, and nothing in the line that undoes it."""
    if not THEY_ARE_EASING.search(clean) or EASING_NOT_ONE.search(clean):
        return False
    return not ("?" in clean or MOVE_ON.search(clean) or THEM_ASKING.match(clean))


def _reads_as_easing_but_worse(clean):
    """The easing with a tail that needs a person: "hes come round but hes confused"."""
    if not THEY_ARE_EASING.search(clean) or "?" in clean:
        return False
    return bool(EASING_UNDONE.search(clean))


def _an_abuse_thread(last):
    text = str(last or "").lower()
    return bool(ABUSE_ANSWER.search(text)) and not ABUSER_ANSWER.search(text)


def _pick(pool, forms, clean, memory=None):
    """One line from a pool, filled with the words for the person it is about.

    Two things are read before the line is chosen. The line the bot said last turn is dropped from
    the pool, because the same paragraph twice in a row reads as a machine that is not listening:
    "what do i do" then "should i go back" came back identical, because the two questions add up to
    the same number.
    """
    # `forms` is None for a pool that names nobody: those lines carry no placeholder, and asking
    # `_wrote_for_them` to fill one that has none is what an empty string cannot do.
    lines = _fallback._wrote_for_them(pool, forms) if forms else tuple(pool)
    if not lines:
        return None
    turns = _turns(memory)
    said = str((turns[-1].get("bot") if turns else "") or "").strip()
    if said and len(lines) > 1:
        fresh = [line for line in lines if line.strip() != said]
        if fresh:
            lines = fresh
    start = sum(ord(char) for char in clean) % len(lines)
    return lines[start]


def _the_thread(memory, last):
    """Everything said in this thread, lower-cased, for a reading to search."""
    lines = [str(last or "")]
    for past in _turns(memory):
        lines.append(str(past.get("user") or ""))
        lines.append(str(past.get("bot") or ""))
    return " ".join(line.lower() for line in lines if line)


def _the_answer_sent_them_somewhere(last):
    """True when the answer above asked for a person to be seen, not for a watch and wait."""
    return bool(ROUTE_NAMED.search(str(last or "").lower()))


def _the_words_for_the_one_who_did_it(memory):
    """The words for the person the abuse came from, for the pools written about them.

    `_about_somebody_else` cannot supply these: it stands down on the speaker's own crisis on
    purpose (`SOMEBODY_HURT_ME` - "my boyfriend hit me" is the person typing, not somebody they
    care for), and asking it first is what made every pool below unreachable for exactly the
    thread the module's own docstring is about: after "my boyfriend hit me", "he says hes sorry"
    fell to the greeting because `forms` was None before the abuse branch was ever reached.

    The pools are written without placeholders bar one line that reads `{subj}`, so what this has
    to get right is the pronoun, and `memory["safety_person"]` is the one the safety answer above
    used ("he" for "my boyfriend hit me"). Nothing here guesses who they are.
    """
    said = str(memory.get("safety_person") or "").strip().lower()
    relation = str((memory.get("person") or {}).get("who") or "").strip().lower()
    if said.startswith("she"):
        forms = {"subject": "she", "object": "her", "possessive": "her", "be": "is"}
    elif said.startswith("they"):
        forms = {"subject": "they", "object": "them", "possessive": "their", "be": "are"}
    else:
        forms = {"subject": "he", "object": "him", "possessive": "his", "be": "is"}
    forms["who"] = "your " + relation if relation else forms["object"]
    return forms


# A question about the plan - leaving, staying, where to go, what to do next - is the question of
# this thread, and it has a pool of its own: the lines plan the going out safely rather than talk
# about him (the emergency card's continuation, `ABUSE_AFTER`). Standing down here instead is what
# made the third turn read as the line before it: after "my boyfriend hit me" then "he says hes
# sorry", "should i leave" fell to whichever module was holding the apology, and the person who was
# hit was told to name what they did and say why it was wrong (magenta-pine, #13295).
# A knowledge row still reads the words of the turn before as well: after a reply about an apology,
# "what do i do" reached the apology row and asked the person who was hit to name what they did.
# That row is in bot/knowledge/wording.py, which this file cannot reach into, and the guard for it
# is a separate change; every other shape below answers here.
# The plan is a bare question, and these arms had no end on them, so the same words inside a
# longer question took the turn: after `my husband hit me`, `what do i do about my tax return` was
# answered "You do not have to settle all of it tonight" instead of what to do about the tax
# return, and `should i leave my job` the same. An anchor, not a longer list, because the fault is
# that the subject after "about" was being dropped (white-ruler, #13830).
_END = r"(?:\s+(?:now|next|though|then))?\s*(?:[.?!,]|$)"
THE_PLAN_ITSELF = re.compile(
    r"\b(?:should|shall|do|can|could|will) (?:i|we) (?:leave|leaves|go|stay|move|get out|walk out)\b"
    + _END +
    r"|\bwhere (?:do|can|should) i (?:go|stay|sleep tonight)\b" + _END +
    r"|\bshould i leave\b" + _END + r"|\bcan i leave\b" + _END +
    r"|\bdo i need to (?:leave|go|get out)\b"
    r"|\bwhat (?:should|do|can|could) i do\b" + _END + r"|\bwhat now\b" + _END +
    r"|\bwhat do i do next\b" + _END +
    r"|\bshould i (?:go back|stay with (?:him|her|them))\b"
    # The same question asked by what it costs to answer: how the leaving is done, and what to say
    # to the people it touches. "how do i get my stuff out" after the abuse card was answered by
    # the greeting's hedge ("I don't know enough to answer that honestly") while the plan pool had
    # the list - phone, keys, paperwork - and "what do i tell the kids" was answered with the
    # drafting line for a letter. Both are the plan, so both are answered with it.
    r"|\b(?:how|when) (?:do|can|should|would) i (?:get|collect|pick up|take|move) (?:my|the|our)\s+"
    r"(?:stuff|things|belongings|clothes|papers|paperwork|documents|passport)\b"
    r"|\bcan i take (?:the|my) (?:kids|children)\b"
    r"|\bwhat (?:do|should|can|could) i (?:tell|say to) (?:the|my|our)\s+"
    r"(?:kids|children|son|daughter|family|mum|mom|mother|parents|boss)\b" + _END +
    r"|\bhow long (?:will|does|is) (?:this|it|all this) (?:take|going to take|going to go on)\b",
    re.I)

# The bag. Someone who is leaving asks what to put in it, and the words of that question are the
# amends script's own ("what do i take" was held by "Name what you did, say why it was wrong"), so
# a person packing three turns into an abuse thread was told to draft an apology - and "pack a
# bag" reached the airline's cabin allowance. Its own shape, its own list, because the answer to
# this one is items and the answer to "should i leave" is not (steward-teal-donkey, #13830).
PACKING = re.compile(
    r"\bwhat (?:should|do|can|could|shall) i (?:take|bring|pack)\b"
    r"|\bwhat (?:do|will|should) i (?:need|want) to (?:take|bring|pack)\b|\bpack a bag\b"
    r"|\bwhat (?:should|do) i (?:put|get) in (?:the|my) bag\b"
    r"|\bwhat do i take with me\b", re.I)

# Whether the worst is coming back is the question under the whole thread, and the pool for a
# threat is the one written for it. "will it get worse" after the abuse card was answered "I want
# to answer the right question, so tell me what it is about" - the thread's own subject asked for
# by name and handed back as a riddle.
THE_FEAR_IT_REPEATS = re.compile(
    r"\bwill (?:it|this|he|she|they) (?:get|be) worse\b|\bis it going to get worse\b"
    r"|\bwill (?:it|this) (?:happen|get) again\b|\bwill (?:he|she) do it again\b"
    r"|\bdoes it get worse\b", re.I)

def respond(text, memory):
    clean = _clean(text)
    if not clean:
        return None
    above = _the_answer_above(memory)
    if above is None:
        return None
    last = str(above.get("bot") or "").lower()
    if NODDING_ALONG.match(clean) or THE_TROUBLE_IS_OVER.search(clean):
        return None
    if CHANGE_THE_SUBJECT.search(clean):
        # The person asked for another subject. Every pool in this file is about this one, so none
        # of them can answer, and standing down wholly hands the line to whichever row holds the
        # words - "can we talk about something else" got advice on making small talk at a party.
        # Closing the thread is this file's own business, so it says the one warm thing it has and
        # hands the turn back.
        return _pick(CHANGED_SUBJECT, None, clean, memory)
    # The thread is an abuse thread if any answer in it was the card for the person who was hit.
    # Reading only the turn above is not enough: "its my fault" was answered out of the pools with
    # a line that names the abuse line without the card's own words, so the next turn - "should i
    # leave" - read as a carer's thread and stood down, and the question of the whole thread went
    # to whichever module was holding it (magenta-pine, #13295).
    in_abuse = _an_abuse_thread(last) or any(
        _an_abuse_thread(str(turn.get("bot") or "")) for turn in _turns(memory))
    if in_abuse:
        # The speaker is the one who was hit, so the words to fill the pools with are the ones for
        # the person who did it, not for somebody they are caring for.
        forms = _the_words_for_the_one_who_did_it(memory)
    else:
        forms = _fallback._about_somebody_else({"user": str(above.get("user") or "")}, memory)
        if not forms:
            return None
    if in_abuse:
        if PACKING.search(clean):
            return _pick(THE_BAG, None, clean, memory)
        if THE_PLAN_ITSELF.search(clean):
            # The pools above answer the line about him; this one asks what to do, and
            # `ABUSE_AFTER` is the pool written for exactly that: whether to go, when, and what
            # to take. Answering it here is also what stops the third turn reading the line
            # before it, which is how "should i leave" once came back as advice to apologise.
            return _pick(_fallback.ABUSE_AFTER, forms, clean, memory)
        # First, because the abuse card names a helpline and reads as a crisis answer: the whole
        # point of these pools is that the person who did the hitting is not somebody to mind.
        if THEIR_OWN_FAULT.search(clean):
            return _pick(IT_IS_NOT_YOUR_FAULT, forms, clean, memory)
        if NO_WAY_OUT.search(clean):
            return _pick(NOWHERE_TO_TURN, forms, clean, memory)
        if THREAT_AGAIN.search(clean):
            return _pick(THE_NEXT_ONE, forms, clean, memory)
        if THE_FEAR_IT_REPEATS.search(clean):
            return _pick(THE_NEXT_ONE, forms, clean, memory)
        if THE_DRINK.search(clean):
            return _pick(AFTER_THE_DRINK, forms, clean, memory)
        if THE_KINDNESS.search(clean):
            return _pick(AFTER_THE_KINDNESS, forms, clean, memory)
        if THE_APOLOGY.search(clean):
            return _pick(AFTER_THE_APOLOGY, forms, clean, memory)
        if TOO_MUCH_TO_CARRY.search(clean):
            # Before the stand-down below, which is what handed this line to whichever row held
            # its words. Nothing here asks what happens next, because they have just said what
            # they have room for: the answer is one person today and the line's number.
            return _pick(THE_LOAD_IS_TOO_MUCH, None, clean, memory)
        if not (ABOUT_THE_THREAD.search(clean) or ABOUT_THE_INCIDENT.search(clean)):
            # Something else entirely: stand down and let the greeting answer it.
            return None
        return _pick(STILL_THE_SAME_THREAD, forms, clean, memory)
    if _reads_as_easing_but_worse(clean):
        return _pick(NOT_RIGHT_AFTER_THE_WORST, forms, clean, memory)
    asked = THE_ANSWER_ASKED_A_QUESTION.search(str(above.get("bot") or "").strip())
    if asked and not ANSWERED.match(clean) and _reads_as_easing(clean):
        return _pick(BEFORE_THE_ANSWER, forms, clean, memory)
    in_crisis = any(word in last for word in CRISIS_WORDS)
    if in_crisis:
        if THEY_SAY_ITS_FINE.search(clean):
            return _pick(ITS_FINE, forms, clean, memory)
        if THEY_ARE_RECOVERING.search(clean):
            return _pick(RECOVERING, forms, clean, memory)
        if _reads_as_easing(clean):
            if SWALLOWED_NOT_RELIEF.search(_the_thread(memory, last)):
                return _pick(SWALLOWED_BETTER, forms, clean, memory)
            # The fallback's own pool for this one, because it is the same thread #7862 wrote it
            # for: an hour that is easier is not the whole of it, and the question is asked again.
            return _pick(CRISIS_BETTER_THEM, forms, clean, memory)
        return None
    if _reads_as_easing(clean) and _the_answer_sent_them_somewhere(last):
        if SWALLOWED_NOT_RELIEF.search(_the_thread(memory, last)):
            return _pick(SWALLOWED_BETTER, forms, clean, memory)
        return _pick(NOT_OUT_OF_THE_WOODS, forms, clean, memory)
    return None
