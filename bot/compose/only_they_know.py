"""What only the person in front of it can know or judge.

Three shapes of line reached the search hedge or a placeholder when nothing else knew, and none
is a look-up:

- a judgement put to the bot - "do you think shes too old for a day out", "was i out of order",
  "do you think i handled it badly", "am i too old for a festival". "A quick search online will
  get you a solid answer" sends somebody off to read about their own mother;
- a yes/no about one of their own people - "does my mum like golf", "does she drive", "do they
  get on at that age". No page anywhere knows their mother's taste in golf;
- how somebody else feels about the asker, or why they did a thing to them - "is he avoiding me",
  "is my dad proud of me", "why did she not invite me", "am i annoying her". The answer is in
  another person's head, and a guess is worse than saying so.

All three are answered here instead: the reply hands back what only they can say, and asks a question
so the turn keeps going. A judgement is not a fact gap, so the honest hedge is the wrong shape for
it, and a fact about somebody the bot has never met is not on any page.

This lives beside the composer rather than inside `fallback.py`, which the world caps at 1 MiB and
was over it when this was written (772 KB today), and `bot/modules/greeting.py` calls it the way it
calls `repeat` and `too_late`: only when the reply in hand is the composer's own "I cannot answer
that" note, so a line with an answer of its own keeps it. `should` (advice), permissions ("is it ok to text an ex") and "what do you think about my
sister" (talking about a person, not judging one) all stand down, as does the bare "am i too old",
which is the too-late reading's turn.
"""
import re

from . import fallback

# A person asking the bot to judge somebody it has never met - "do you think shes too old for a
# day out", "do you think hes ready for school", "do you think my mum would like this" - got the
# search hedge ("a quick search online will get you a solid answer"), which tells somebody to go
# and look up their own mother. There is nothing to look up: the bot cannot see the person, so the
# judgement is the asker's to make, and what a friend says is that the number is a poor test and
# the one thing that would settle it. The row they are in is the same - "was i out of order", "do
# you think i handled it badly", "do you think i did the right thing" were all told to search,
# and one side of a row always sounds better, so what is needed is the rest of it.
# The words that make an ask a verdict rather than a request for advice or a look-up: a person
# putting a judgement to the bot. "do you think i should take the job" is not one of these - the
# advice asks have their own place - and neither is "what do you think about my sister", which
# wants the bot to talk about somebody rather than to call something.
JUDGEMENT_WORDS = re.compile(
    r"\b(?:too\s+\w+|old\s+enough|ready|fair|fair\s+enough|right|wrong|harsh|strict|soft|hard\s+on|"
    r"badly|rude|unkind|unfair|blunt|mean|a\s+bit\s+much|overreact\w*|over\s+the\s+top|out\s+of\s+order|unreasonable|"
    r"mistake|handled|selfish|childish|silly|stupid|ok(?:ay)?|alright|worth\s+it|"
    r"would\s+(?:like|love|enjoy|hate|mind|be\s+upset))\b")
# "is it ok to text an ex", "would it be alright to leave him with my mum" - whether a thing is
# allowed is a different question from whether the person was in the wrong, and the ones that
# have an answer keep it.
PERMISSION_ASKED = re.compile(
    r"\b(?:is|would|will)\s+it\s+(?:ok(?:ay)?|alright|fine|rude|weird|bad)\b"
    r"|\bis\s+(?:it|that)\s+ok(?:ay)?\s+(?:to|if)\b"
    r"|\bits\s+(?:ok(?:ay)?|alright|fine)\s+(?:to|if)\b")
ASKS_MY_VIEW = re.compile(
    r"\b(?:do|did|would)\s+(?:you|u|ya)\s+(?:think|reckon)\b"
    # "dya think", "d'you reckon" and the bare "u think i handled it badly" are the same ask with
    # the words worn down, and they were the search hedge too.
    r"|\b(?:d'?you|dya)\s+(?:you\s+)?(?:think|reckon)\b"
    r"|^\s*(?:u|ya|you)\s+think\b"
    r"|\bwould\s+you\s+say\b"
    r"|\bwhat\s+(?:do|would)\s+(?:you|u|ya)\s+(?:think|reckon|say)\b")
# The same ask with no "do you think" in it: "was i out of order", "did i do the right thing",
# "was that too harsh". The judgement word is what makes it the ask rather than a report.
A_VERDICT_ASKED_FOR = re.compile(
    r"^\s*(?:(?:and|so|but|ok|okay|well|honestly|seriously|be\s+honest)\s+)*"
    r"(?:was|were|am|did|do|have)\s+(?:i|we|that|it)\b[^.?!]{0,40}"
    r"\b(?:out\s+of\s+order|overreact\w*|over\s+the\s+top|too\s+(?:harsh|strict|hard|soft|much|"
    r"blunt|quick)|unreasonable|in\s+the\s+wrong|right\s+thing|wrong(?:ly)?|handled|fair|"
    r"badly|rude|unfair|unkind|mean|a\s+mistake)\b")
# The same verdict said with a hedge word instead of "too", and often after the report rather than
# at the start of the line: "was that a bit soft", "was that a bit harsh of me",
# "i told him no, was that harsh". The grade is the ask either way - what the person wants is
# somebody to tell them whether they were in the wrong - and every one of these was reaching the
# search hedge, which sends them off to read about somebody else's row. The bare grade is read
# only at the end of the line ("was that harsh"), because "was that hard to learn" asks how
# difficult a thing is and has its own answer.
A_MILD_GRADE = re.compile(
    r"\b(?:was|were|am|is|did)\s+(?:i|that|it|we)\b[^.?!]{0,32}?"
    r"(?:\b(?:a\s+bit|a\s+little|rather|quite|being)\s+(?:harsh|soft|strict|blunt|mean|hard|much)\b"
    r"|\b(?:harsh|soft|strict|blunt|mean|hard)\s+(?:of|on)\s+(?:me|him|her|them|us|my)\b"
    r"|\b(?:harsh|soft|strict|blunt|mean)\b\s*[?.!]*\s*$)")
# Somebody else is in the line as the person judged, so the reply hands the judgement back rather
# than answering for a face the bot cannot picture. "shes" and "hes" are how the two are usually
# typed, and the clean line has no apostrophe to hang the pronoun on, so the contracted spellings
# are part of the pattern.
# The people a person keeps, named as families rather than phrases. A question is about one of
# these or about a bare pronoun, and never about "my <any noun>": "does my phone support 5g" is a
# question about a phone, and "I have never met them" answers it with somebody who is not there.
_RELATION = (
    r"mum|mom|mother|dad|father|parent|parents|son|daughter|kid|kids|child|children|baby|"
    r"brother|brothers|sister|sisters|sibling|siblings|nan|nana|grandma|grandad|granny|"
    r"grandparents?|wife|husband|partner|boyfriend|girlfriend|ex|friend|friends|mate|mates|"
    r"neighbour|neighbours|flatmate|housemate|landlord|boss|manager|colleague|carer|"
    r"boy|girl|little\s+ones?|teenager|teen|toddler|lad|lass|bloke|in[- ]laws?|"
    r"aunt|auntie|uncle|cousin|cousins|niece|nephew|family"
)
SOMEONE_ELSE_JUDGED = re.compile(
    r"\b(?:he|he'?s|she|she'?s|they|they'?re|him|her|them)\b"
    r"|\b(?:my|our|his|her|their)\s+(?:" + _RELATION + r")\b")
_THE_TWO_OF_US = re.compile(r"\b(?:we|us|our\s+(?:relationship|marriage))\b")
# A thing of theirs that is not a person: "do you think my laptop is too old" puts the laptop up
# for judgement, not the person typing, so handing it back as their own conduct ("What did you
# actually say to them?") answers a question nobody asked. A line with "i", "me" or "myself" in
# it is still theirs to weigh ("what i said to my mate"), so only the bare thing stands down.
_THING_OF_THEIRS = re.compile(
    r"\b(?:my|our)\s+(?!" + _RELATION + r")\w+")
_ABOUT_THE_ASKER = re.compile(r"\b(?:i|me|myself|ive|im)\b")
# "am i too old for a festival", "am i too old to go back to college" - the age is the doubt
# being put to the bot, and the search hedge ("a quick search online will get you a solid
# answer") tells somebody to go and read about their own age. Nothing to look up: the bot has no
# idea how old they are, and the number is the least useful part of it anyway.
AM_I_TOO_OLD = re.compile(
    r"^\s*(?:(?:and|so|but|ok|okay|well|honestly)\s+)*"
    r"(?:am\s+i|do\s+you\s+think\s+i(?:\s+am|'?m|\s+was)|a?m\s+i)\b[^.?!]{0,30}"
    r"\b(?:too\s+old|past\s+it|over\s+the\s+hill)\b")
# "past it for" is the same doubt as "too old for": "am i past it for a festival" got the search
# hedge because only the word "too" was read as naming the thing.
A_THING_IT_IS_TOO_OLD_FOR = re.compile(
    r"\b(?:too\s+old|past\s+it)\s+(?:for|to)\b")
# "am i too old for a mammogram", "too old to fast", "too old to join the army", "too young to
# vote": the age is the whole question, and the answer is a rule or a screening the bot cannot
# see - a line about enjoying it instead would be worse than the hedge. A doubt about a thing
# they want to do is the other half ("too old for a festival", "too old to start running"), and
# only that half is read here.
AGE_IS_THE_RULE = re.compile(
    r"\b(?:mammogram|smear|screening|screen\w*|scan|test|surgery|operation|operat\w*|"
    r"replacement|transplant|hrt|hormone\w*|medication|medicine|jab|vaccine|vaccinat\w*|"
    r"fast|fasting|blood|donor|donat\w*|army|navy|raf|forces|military|police|fire\s*service|"
    r"foster\w*|adopt\w*|vote|voting|voter|licence|license|driv\w*|pension|retire\w*|"
    r"insurance|mortgage|visa|pilot|airline|midwife\w*|nurse|teach\w*|carer|childminder)\b")
TOO_OLD_FOR_IT = (
    "The number is the least useful part of it: what matters is whether you would enjoy the "
    "thing. What is the bit you would look forward to?",
    "Nobody is too old for a thing they want to do - the ones who regret it are the ones who "
    "waited. What is it that has you hesitating?",
    "I would go on what you want rather than on your age, honestly. What would you do if nobody "
    "was going to comment?",
)
JUDGE_SOMEONE_ELSE = (
    "I would go on what you have seen them do - you know them and I never will. What is it you "
    "are not sure about?",
    "Only you know them well enough to say, and I would trust that over anything I could guess. "
    "What has you wondering?",
    "That one is yours rather than mine, honestly: you are the one who knows them. What would a "
    "good version of it look like?",
)
# The same ask with an age or a milestone in it - "do you think shes too old for a day out", "do
# you think hes ready for school" - where the number really is the thing being weighed, and a
# reply about a number is right. Without one in the line it says nothing: "was that too harsh
# what i said to my mate" is not a question about anybody's age.
JUDGE_SOMEONE_AT_AN_AGE = (
    "I would go on what you have seen them do, not on a number - you know them and I never will. "
    "What is it you are not sure about?",
    "Nobody can weigh that from outside, and the number is the least useful part of it anyway. "
    "What would a good day of it look like for them?",
)
A_NUMBER_IN_THE_LINE = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|"
    r"seventy|eighty|ninety|hundred)\b"
    r"|\b(?:years?\s+old|how\s+old|old\s+enough|too\s+(?:old|young)|ready|at\s+that\s+age)\b")
# "do you think she would like this gift" is not a judgement of anybody's capability: it is
# whether a thing suits a person's taste, and that is theirs to say.
A_GIFT_OR_TASTE_ASKED = re.compile(
    r"\b(?:would|will|do\s+you\s+think)\b[^.?!]{0,25}"
    r"\b(?:like|love|want|wear|use|enjoy|suit)\b[^.?!]{0,20}\b(?:this|that|it|these|those)\b")
JUDGE_THEIR_TASTE = (
    "Whether {who} would like it is for {them} to say, not mine to guess. What is it, and what "
    "has {who} liked before?",
    "I have never met {who}, so I cannot tell you {poss} taste. What is the thing, and what does "
    "{who} usually go for?",
    "Only {who} knows what {who} likes, honestly. What were you thinking of getting?",
)
# Every line here is about a row, because the ask that names one - "do you think i handled it
# badly", "was that too harsh what i said to my mate" - is asking what the bot makes of their own
# conduct in it. An ask about their own head or their own plan names no row ("do you think thats
# stupid", "do you think its too late to start now"), and hearing "one side of a row always
# sounds better" about a decision nobody argued over is the reply reading a row that is not
# there, so those lines get their own pool below.
A_ROW_IN_THE_LINE = re.compile(
    r"\b(?:said|say|saying|told|tells|texted|messaged|wrote|replied|answered|shouted|snapped|"
    r"argued|arguing|argument|row|rowed|fought|fighting|fight|falling out|fell out|"
    r"handled|handle|overreacted|overreacting|rude|harsh|unfair|out of order|my fault|"
    r"apologise|apologize|apology|confronted|tackled it|brought it up)\b")
JUDGE_MYSELF = (
    "I cannot call that from one line, and one side of a row always sounds better. What did you "
    "actually say?",
    "Not from here, no. Tell me what happened and what you would do differently, and I will tell "
    "you what I make of it.",
    "That needs the whole thing rather than a line of it. What is the bit you keep going back "
    "over?",
)
# The same doubt about their own head or their own plan, with no row in the line.
JUDGE_MYSELF_NO_ROW = (
    "I cannot call that one for you from a line, and I would rather not guess at it. What is it "
    "that has you doubting it?",
    "That is yours to weigh rather than mine, honestly. What would change your mind?",
    "No way for me to say yes or no to that. Tell me what you would do if it went well.",
)
JUDGE_THE_TWO_OF_US = (
    "Nobody outside the two of you can weigh that, me least of all. What are the rows like "
    "after - forgotten by the next day, or sore for a while?",
    "I cannot count somebody else's rows from here. Are they about the same thing each time?",
)


def _a_judgement_i_am_asked_for(clean, words):
    """The pool for a person asking the bot's judgement, or None when it is another question.

    Asked last, on the lines nothing else answered, so a question with an answer of its own - how
    to do the thing, who can settle it, whether it is worth the money - keeps its own reply.
    """
    if not (ASKS_MY_VIEW.search(clean) or A_VERDICT_ASKED_FOR.match(clean)
            or A_MILD_GRADE.search(clean) or AM_I_TOO_OLD.match(clean)):
        return None
    # An ask with "should" in it is asking what to do, and a permission ("is it ok to text an
    # ex") is asking whether a thing is allowed: both have their own place ahead of this one.
    if re.search(r"\bshould\b", clean) or PERMISSION_ASKED.search(clean):
        return None
    # The judgement word is what makes an ask a verdict rather than a wish to talk about
    # somebody: "do you think my sister is too old for it" is one, "what do you think about my
    # sister" is the other and is left to the modules that know how to ask about a person.
    if not (JUDGEMENT_WORDS.search(clean) or AM_I_TOO_OLD.match(clean)):
        return None
    if AM_I_TOO_OLD.match(clean) and not SOMEONE_ELSE_JUDGED.search(clean):
        # A bare "am i too old" is a doubt the thread already holds, and the too-late reading
        # above answers it with the thing itself: "i cant swim and im 38" then "am i too old" is
        # the adult-lessons line, not a philosophy about age. Only the ask that names what it is
        # too old for comes here.
        if A_THING_IT_IS_TOO_OLD_FOR.search(clean) and not AGE_IS_THE_RULE.search(clean):
            return TOO_OLD_FOR_IT
        return None
    # "was that too harsh what i said to my mate" is their own conduct with somebody named in
    # the line, so the row is theirs to weigh and not the other person's.
    if re.search(r"\bwhat\s+i\s+(?:said|did|wrote|sent|texted|told)\b", clean):
        return JUDGE_MYSELF
    if A_GIFT_OR_TASTE_ASKED.search(clean) and SOMEONE_ELSE_JUDGED.search(clean):
        subject, them, possessive = _said_person(clean)
        return tuple(line.replace("{who}", subject).replace("{them}", them)
                     .replace("{poss}", possessive) for line in JUDGE_THEIR_TASTE)
    if _THE_TWO_OF_US.search(clean) and not SOMEONE_ELSE_JUDGED.search(clean):
        return JUDGE_THE_TWO_OF_US
    if SOMEONE_ELSE_JUDGED.search(clean):
        return JUDGE_SOMEONE_AT_AN_AGE if A_NUMBER_IN_THE_LINE.search(clean) else JUDGE_SOMEONE_ELSE
    if _THING_OF_THEIRS.search(clean) and not _ABOUT_THE_ASKER.search(clean):
        return None
    # A row in the line is the one thing that makes "what did you actually say" the right question.
    return JUDGE_MYSELF if A_ROW_IN_THE_LINE.search(clean) else JUDGE_MYSELF_NO_ROW


# The fence the fact reader uses. It is NOT_A_FEELING_ASK without the pet words: a dog or a cat is
# not somebody who has feelings about you, which is why the feelings reader stands down on one, but
# "does my nan have a dog" is a plain fact about their nan that no page holds - the pet word is the
# thing asked about, not the person it is asked of.
NOT_A_FACT_ASK = re.compile(
    r"\b(?:should|shall|how\s+do\s+i|how\s+can\s+i|what\s+do\s+i\s+do|what\s+should\s+i|"
    r"hit|hits|hitting|hurt|hurts|shout\w*|scream\w*|push\w*|grab\w*|threat\w*|"
    r"abuse\w*|touch\w*|assault\w*|rape\w*|"
    r"died|dying|death|passed\s+away|funeral)\b")

# A question about a body or an illness is another lane's, and it has an answer of its own: "does
# he have a temperature", "does she take insulin", "is he unwell" must keep the medical line rather
# than being told that only they can say. A habit word ("does he eat meat", "does he sleep") is
# not one of these, so the everyday questions still come here.
A_BODY_OR_ILLNESS = re.compile(
    r"\b(?:temperature|fever|flu|covid|cough|cold|ill|sick|unwell|poorly|pain|pains|ache|"
    r"aches|aching|sore|hurt|hurts|hurting|injury|injured|symptom|symptoms|rash|swelling|"
    r"swollen|bleed\w*|blood|dose|doses|insulin|inhaler|medication|medicine|tablet|tablets|"
    r"pill|pills|antibiotic\w*|doctor|gp|hospital|nurse|pharmac\w*|checkup|check-up|scan|"
    r"pregnan\w*|asthma|diabet\w*|dementia|depress\w*|anxious|anxiety|allerg\w*|"
    r"eat\s+enough|eating\s+enough)\b")

# A question about one of their own people - "does my mum like golf", "does she drive", "do they
# get on at that age" - is not a look-up either, and the search hedge ("a search should sort you
# out quickly") is the one answer that cannot help: no page anywhere knows their mother's taste in
# golf. The person asking is the one who can say, so the reply says that and asks what they had in
# mind. Every ask about a body, a dose, a rule or a pet keeps its own reply: this reader only
# knows the person's own preferences and habits, and only when the ask is a bare yes/no about a
# named relation of theirs ("my mum", "our nan") or a bare pronoun ("she", "they"). A word on its
# own is not one of their people: "do i like fish" and "do i actually want him back" name nobody
# of theirs and keep whatever reply they had.
# The verbs a question about one of their own people turns on. The list is a fence and not a
# vocabulary: what no page can hold is how somebody lives - what they like, how they sleep,
# where they work - so the verbs here are the everyday ones. A verb outside it keeps the
# composer's reply, because a question about a body, a dose or a rule is another lane's.
EVERYDAY_VERBS = (
    r"like|love|hate|prefer|want|enjoy|mind|drive|drink|smoke|play|support|vote|"
    r"get\s+on|get\s+along|take\s+(?:sugar|milk)|eat|care|"
    r"sleep|nap|walk|run|swim|read|cook|bake|garden|fish|shop|work|live|earn|study|"
    r"go\s+out|go\s+to|come\s+to|come\s+round|visit|call|text|ring|write|draw|sing|"
    r"dance|travel|watch|listen|collect|keep|wear|use|remember|know|think|believe|"
    r"volunteer|retir\w*|cycle|park|belong|help\s+out|help|"
    r"have\s+a|have\s+any|need\s+a"
)
# The person an ask can be about: a bare pronoun, one of their own named by relation, or one
# of theirs said through another of theirs ("his wife", "her husband").
_ANY_PERSON = (r"(?:he|she|they|him|her|them|(?:my|our|his|her|their)\s+(?:" + _RELATION + r"))")
A_FACT_ABOUT_THEIR_PERSON = re.compile(
    r"^\s*(?:(?:and|so|but|ok|okay|well|also|anyway|btw)\s+)*"
    r"(?:does|do|did|would|will)\s+"
    r"(?P<who>" + _ANY_PERSON + r")\s+"
    r"(?:(?:still|actually|even|really|ever|now)\s+)?"
    r"(?:" + EVERYDAY_VERBS + r")\b")
# The same question with a wh-word in front of it - "what is she into", "where does he work",
# "who does he live with" - reached the search hedge as well, and it is the same nonsense: the
# answer is in the person they know and nowhere a search could reach.
A_WH_ABOUT_THEIR_PERSON = re.compile(
    r"^\s*(?:(?:and|so|but|ok|okay|well|also|anyway|btw)\s+)*"
    r"(?:what|where|who|when|whats|wheres|how\s+often|how\s+long)"
    r"(?:'s|\s+is|\s+was|\s+does|\s+do|\s+did|\s+has|\s+had|"
    r"\s+are|\s+were)?\s+"
    r"(?P<who>" + _ANY_PERSON + r")\s+"
    r"(?:(?:still|actually|even|really|ever|now|usually|normally)\s+)?"
    r"(?:up\s+to|into|do|doing|say|spend|" + EVERYDAY_VERBS + r")(?:s|es|ed|d|ing)?\b")
# "is my dad retired", "is she married": a state rather than a habit, and the verb list above takes
# does/do/did only, so these were left to the search hedge. Only the states that are the person's
# own business are here - "is my mum coming" asks about a plan and keeps the reply it had, because
# a plan is something the chat can have been told.
A_STATE_ABOUT_THEIR_PERSON = re.compile(
    r"^\s*(?:is|was|are|were)\s+(?P<who>" + _ANY_PERSON + r")\s+"
    r"(?:(?:still|actually|even|really|now|also)\s+)?"
    r"(?:retired|married|single|divorced|separated|widowed|ok|okay|alright|happy|unhappy|"
    r"well|better|alive|working|studying|at\s+home|back|settled|keeping\s+well)\b")
# Where one of their people is: "is my sister in cork", "is my dad in hospital", "is she in town
# yet". The same not-a-look-up as the rest - no page holds where somebody is this week - and it was
# the search hedge. A word said with "in" that is a state rather than a place is not this shape
# ("is my mum in pain", "is she in labour"), so those keep their own reply.
A_PLACE_ABOUT_THEIR_PERSON = re.compile(
    r"^\s*(?:is|was|are|were)\s+(?P<who>" + _ANY_PERSON + r")\s+"
    r"(?:(?:still|actually|even|really|now|already|finally|back)\s+)?"
    r"(?:in|at|near|round|around|off\s+to|down\s+in|up\s+in|over\s+in|back\s+in|out\s+in)\s+"
    r"(?!a\s|an\s|the\s|pain|trouble|danger|labour|labor|tears|need|agony|hospital\s+bed)"
    r"[a-z]")
# "is my son 5", "is my mum 72" - the person puts a figure to the bot for checking, and no page
# holds it either. Only the number that comes after the person is read, so a question with a verb
# in it ("is my mum coming", "is my son sleeping") keeps the reply it had.
A_FIGURE_ABOUT_THEIR_PERSON = re.compile(
    r"^\s*(?:is|was|are|were)\s+"
    r"(?P<who>" + _ANY_PERSON + r")\s+"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|"
    r"seventy|eighty|ninety)\b")
THEIR_PERSON_WORD = re.compile(r"\b(?:my|our)\s+(" + _RELATION + r")\b")
# Somebody of theirs said through another of theirs: "what does his wife do", "does her husband
# work". The same ask as "what does your brother's wife do", and the same answer - only they
# can say - so the words are said back as they came.
THEIR_PERSON_THROUGH_ANOTHER = re.compile(r"\b(?:his|her|their)\s+(" + _RELATION + r")\b")
# Not "I have never met him": after "he works at the hospital" that reads as a bot that forgot the
# line before it. What is true whenever the ask arrives is that the person in question is the one
# who knows, so each line says that and points at the ask that settles it - the way the post
# office line names the branch listing.
THEIR_PERSON_WH_LINES = (
    "I cannot check that from here - {she} is the one who knows. Ask {who}, and tell me what "
    "you get.",
    "Nothing on this side holds that; only {she} can say. What made you ask?",
    "You would have to ask {who} - that is not a thing I can look up. What has you wondering?",
)
THEIR_PERSON_FIGURE_LINES = (
    "I cannot check that from here, and {she} would know better than any page. Ask {who}, and "
    "tell me what you get.",
    "Nothing I can see holds that one - {she} is the one to check with. What has you asking?",
)
THEIR_PERSON_LINES = (
    "I have never met {who}, so that one is yours to answer. What made you ask?",
    "That is a fact about {who} rather than something I could look up. What were you thinking of "
    "doing about it?",
    "Only you can say that about {who}, honestly. What has you wondering?",
)
# "does he care about me", "does she love me" is the same not-a-look-up but a colder line about
# facts would be wrong for it: what is being asked is how somebody feels, and no page settles it.
# The reply says only they can answer it and asks what happened, rather than handing back a fact.
THEIR_FEELINGS_LINES = (
    "Only {subject} can tell you that, and I would not guess at it. What has happened between you?",
    "That is not mine to answer, but I would ask {object} plainly rather than sit guessing. What "
    "has you wondering?",
    "Nobody can settle that from outside the two of you. What made you ask?",
)
ABOUT_ME_ASKED = re.compile(
    r"\b(?:about|for|with|of)\s+me\b"
    r"|\b(?:love|loves|like|likes|want|wants|need|needs|miss|misses|fancy|fancies|hate|hates)"
    r"\s+me\b")
_PERSON_SUBJECT = {"him": "he", "her": "she", "them": "they"}
# A bare pronoun is said back in the form the sentence needs: "does she drive" reads "I have never
# met her", not "them", and it is the person's own word either way.
_PERSON_OBJECT = {"he": "him", "she": "her", "they": "them",
                  "him": "him", "her": "her", "them": "them"}
# The three forms a reply needs for the person the ask is about: the subject, the object and the
# possessive. A relation said by name ("your dad") reads right in all three slots.
_PERSON_FORMS = {
    "he": ("he", "him", "his"), "him": ("he", "him", "his"), "his": ("he", "him", "his"),
    "she": ("she", "her", "her"), "her": ("she", "her", "her"), "shes": ("she", "her", "her"),
    "hes": ("he", "him", "his"), "theyre": ("they", "them", "their"),
    "they": ("they", "them", "their"), "them": ("they", "them", "their"),
    "their": ("they", "them", "their"),
}

# A question about how somebody else feels about the asker, or why they did a thing to them -
# "is she annoyed with me", "has he gone off me", "is my dad proud of me", "does my boss dislike
# me", "why did she not invite me", "why is my son so quiet with me", "am i annoying her". None of
# these is a fact on a page either: the answer is in the other person's head, and a bot that
# guessed at it would do the one thing worse than saying it cannot know. What a friend says is
# that only they can tell you, and then the one question that opens it. A suspicion about a
# partner ("is he seeing someone else") is the same not-a-look-up said colder, so it gets its own
# gentler line rather than a fact handed back.
THEIR_FEELING_TOWARD_ME = re.compile(
    r"\b(?:is|was|are|were|has|have|had|does|do|did|why)\b[^?]{0,45}?"
    r"\b(?:annoyed|angry|upset|mad|cross|bothered|proud|disappointed|ashamed|embarrassed|"
    r"jealous|bored|fed\s+up|gone\s+off|gone\s+quiet|gone\s+cold|stopped\s+talking|"
    r"avoiding|ignoring|cheating|done\s+with\s+me|over\s+me|"
    r"hate|hates|dislike|dislikes|think|thinks|talk(?:ing)?\s+to\s+me)\b[^?]{0,30}?"
    r"\b(?:me|us)\b")
# The why of a thing somebody did to the asker, with no feeling named: "why did she not invite
# me", "why is my son so quiet with me", "why hasnt he text me back".
WHY_TOWARD_ME = re.compile(
    r"\bwhy\b[^?]{0,40}?\b(?:not\s+invite|invite|text|call|visit|ignore|avoid|leave\s+me|"
    r"shut\s+me\s+out|cancel|forget|forgot|blank\s+me|quiet\s+with|off\s+with|cold\s+with|"
    r"short\s+with|distant)\b[^?]{0,20}?\b(?:me|us)\b")
# The same why with the withdrawal named as a state rather than an act: "why is my wife so
# distant", "why has my son been so quiet". Only a person can be read this way, so a relation or
# a person's pronoun has to be in the line - "why is my car being weird" is not this.
WHY_WITHDRAWN = re.compile(
    r"\bwhy\b[^?]{0,30}?\b(?:so|being|been|suddenly|always|acting|gone|getting)\s+"
    r"(?:distant|quiet|cold|off|short|snappy|withdrawn|weird|strange|funny)\b")
# Another person's relation is not the asker's to be told about: "is her mum proud of her" wants a
# fact about somebody the bot has never met, in a row somebody else is in.
SOMEBODY_ELSES_PERSON = re.compile(r"\b(?:his|her|their)\s+\w+")
# "am i annoying her", "am i too much for him" - the asker turned into the question.
AM_I_TOO_MUCH = re.compile(
    r"^\s*am\s+i\s+(?:being\s+)?(?:too\s+)?(?:annoying|boring|clingy|much|needy|pushy|"
    r"a\s+lot|hard\s+work|too\s+much)\b")
# A suspicion about a partner is not answered with advice to ask plainly: there may be nothing to
# ask about, and the bot cannot see any of it.
A_SUSPICION = re.compile(
    r"\b(?:is|was)\s+(?:he|she|they|(?:my|our)\s+\w+)\s+"
    r"(?:seeing|cheating\s+on|two-timing|lying\s+to)\b")
# These are not the other person's feelings to be asked about: a body, a symptom, an animal, or
# violence in the line has its own answer and its own lane.
NOT_A_FEELING_ASK = re.compile(
    r"\b(?:should|shall|how\s+do\s+i|how\s+can\s+i|what\s+do\s+i\s+do|what\s+should\s+i|"
    r"hit|hits|hitting|hurt|hurts|hitting|shout\w*|scream\w*|push\w*|grab\w*|threat\w*|"
    r"abuse\w*|touch\w*|assault\w*|rape\w*|"
    r"died|dying|death|passed\s+away|funeral|"
    r"dog|dogs|cat|cats|puppy|puppies|kitten|pet|pets|horse|rabbit|hamster)\b")
THEY_FEEL_ABOUT_ME = (
    "Only {who} can tell you that, and guessing at it makes it worse. Ask once, plainly - "
    "'you seem off with me, have I done something?' What has changed lately?",
    "That answer is in {poss} head and nowhere else, so I would not guess at it. Ask {them} "
    "straight out rather than reading the gaps; being asked is not the same as being accused. "
    "What has you wondering?",
    "Nobody outside that conversation can settle it. What has {who} done - or stopped doing?",
)
WHY_THEY_DID_THAT = (
    "The reason is in {poss} head, not on a page. Ask {them} once and in one sentence - no list "
    "of charges - and leave room for an answer you did not expect. What do you think it was?",
    "I can't know that, and the guess you make up in the gap is usually the unkindest one. Ask "
    "{them} straight out. What has you asking now?",
    "Only {who} knows why. Ask {them} plainly, and be ready for an answer you did not want. What "
    "has you asking now?",
)
A_SUSPICION_LINES = (
    "That is not something I can see or check, and I would not guess at it. What has made you "
    "wonder?",
    "I can't know what is going on there, and guessing will hurt more than asking. Is there "
    "something specific that has changed?",
    "That one is between the two of you - I have none of it in front of me. What happened that "
    "has you asking?",
)


def _said_person(clean):
    """The three forms of the person the line is about: subject, object, possessive."""
    through = THEIR_PERSON_THROUGH_ANOTHER.search(clean)
    if through:
        # "his wife" is already the words a person used for them, and they read right in every
        # slot, so they are the ones said back.
        who = through.group(0)
        return who, who, who + "'s"
    named = THEIR_PERSON_WORD.search(clean)
    if named:
        # "your dad" reads right in every slot, so the name of the relation is said back.
        who = "your " + named.group(1)
        return who, who, who + "'s"
    said = _feeling_subject(clean)
    return _PERSON_FORMS.get(said, ("they", "them", "their"))


def _a_feeling_toward_me(clean):
    """The pool for how one of their people feels about them, or why they did that; or None."""
    if NOT_A_FEELING_ASK.search(clean) or SOMEBODY_ELSES_PERSON.search(clean):
        return None
    withdrawn = WHY_WITHDRAWN.search(clean) and (
        THEIR_PERSON_WORD.search(clean) or re.search(r"\b(?:he|she|they|him|her)\b", clean))
    subject, them, possessive = _said_person(clean)
    fill = lambda pool: tuple(line.replace("{who}", subject).replace("{them}", them)
                              .replace("{poss}", possessive) for line in pool)
    if A_SUSPICION.search(clean):
        return A_SUSPICION_LINES
    if WHY_TOWARD_ME.search(clean) or withdrawn:
        return fill(WHY_THEY_DID_THAT)
    if AM_I_TOO_MUCH.search(clean) or THEIR_FEELING_TOWARD_ME.search(clean):
        return fill(THEY_FEEL_ABOUT_ME)
    return None


# The pronoun the ask is about, so the reply says "only she can tell you" rather than "only them":
# "am i annoying her" is about her, and "is he avoiding me" about him.
def _feeling_subject(clean):
    for word in re.findall(r"\b[a-z']+\b", clean):
        if word in _PERSON_FORMS:
            return word
    return "they"


def _a_fact_about_their_person(clean):
    """The pool for a question only the asker can answer about their own people, or None."""
    # Where somebody is comes first and needs no body fence: "is my dad in hospital" is still only
    # his to answer, and the hospital in the line is the place he is in, not a symptom to treat.
    place = A_PLACE_ABOUT_THEIR_PERSON.match(clean)
    asked = (place
             or A_FACT_ABOUT_THEIR_PERSON.match(clean) or A_WH_ABOUT_THEIR_PERSON.match(clean)
             or A_STATE_ABOUT_THEIR_PERSON.match(clean)
             or A_FIGURE_ABOUT_THEIR_PERSON.match(clean))
    if not asked:
        return None
    # A body, a dose, an illness, a death, a pet or an ask for advice in the line has its own
    # answer and its own lane, whatever person the question names.
    if not place and (NOT_A_FACT_ASK.search(clean) or A_BODY_OR_ILLNESS.search(clean)):
        return None
    wh = not (A_FACT_ABOUT_THEIR_PERSON.match(clean) or A_STATE_ABOUT_THEIR_PERSON.match(clean))
    _who_said, _them_said, possessive = _said_person(clean)
    found = THEIR_PERSON_WORD.search(clean) or THEIR_PERSON_THROUGH_ANOTHER.search(clean)
    # "your mum" reads right where "mum" does not ("I have never met son"), and the bare pronoun
    # lines ("does she drive") fall back to "them" or to the pronoun itself.
    said = asked.group("who")
    object_word = (found.group(0) if found and found.re is THEIR_PERSON_THROUGH_ANOTHER
                   else "your " + found.group(1) if found
                   else _PERSON_OBJECT.get(said, "them"))
    subject = object_word if found else _PERSON_SUBJECT.get(said, said)
    if ABOUT_ME_ASKED.search(clean):
        return tuple(line.replace("{subject}", subject).replace("{object}", object_word)
                     for line in THEIR_FEELINGS_LINES)
    if A_FIGURE_ABOUT_THEIR_PERSON.match(clean):
        pool = THEIR_PERSON_FIGURE_LINES
    elif wh:
        pool = THEIR_PERSON_WH_LINES
    else:
        pool = THEIR_PERSON_LINES
    return tuple(line.replace("{she}", subject).replace("{who}", object_word)
                 .replace("{them}", object_word).replace("{poss}", possessive)
                 for line in pool)




def answer_for(text, memory):
    """A reply for a judgement put to the bot, or a fact about one of their own people; or None.

    Called with the composer's "I cannot answer that" reply already in hand, so anything this
    returns is replacing a hedge rather than an answer. The reading is made on the clean line the
    composer read - as typed, so a word the person put in caps still reads - and on the repaired
    line after it, so "does my mum lyk golf" gets the same reply as the spelling right.
    """
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        understood = {}
    clean = understood.get("clean") or " ".join(str(text or "").lower().split())
    words = understood.get("words") or clean.replace("'", "").split()
    repaired = " ".join(str(word) for word in words)
    for line in (clean, repaired):
        if not line:
            continue
        pool = (_a_judgement_i_am_asked_for(line, words)
                or _a_fact_about_their_person(line)
                or _a_feeling_toward_me(line))
        if pool:
            return fallback._choose(pool, memory, clean)
    return None
