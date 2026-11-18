"""A loss does not end when the sympathy is said: the next few turns are still about it.

The composer reads a death and answers it well (bot/compose/loss.py), but it reads one line at
a time. The lines people actually send next — "it was really sudden", "he was 14", "i keep
thinking i should have visited more", "i cant sleep properly" — came back as small talk ("Got
it. Is there anything you'd like a hand with?"), which reads as if the previous turn never
happened. This keeps the loss in `memory["loss"]` and answers those short remarks inside it,
naming the person each time, for a few turns.

It answers nothing else. A new line about a death is the composer's (it says the sympathy, and
the arbiter gives it the turn); a line with no cue, or one that has turned to another subject,
passes to the modules that know about that subject.
"""
import copy
import re

from ..compose import loss
from ..compose import pick as compose_pick
from ..knowledge import lookup

PRIORITY = 2100  # above the loss module: a follow-up inside a loss is this module's turn
ANSWERS = ("feelings", "grief", "loss")
# The loss module reads the same thread and answers a practical ask inside it with sympathy
# ("how do i register the death" got "I'm so sorry to hear that"). It declares that it answers
# in place of the topic entries, so it is chosen before PRIORITY is looked at; this module
# declares the same thing, and being the higher PRIORITY it is the one that answers.
ANSWERS_INSTEAD = ("feelings", "grief", "loss")

# A practical ask about a person's death is this module's ("how much does a funeral cost"), and
# the answer is about a person's funeral. A pet's death has its own entry, which knows what
# happens to a pet's body, so this module stands back for those: "my cat died, is cremation
# expensive" was answered with a coffin, a car and a funeral expenses payment from the DWP.
# Declared, never word-matched here: the composer's own readings decide.
def defers_to(reply, line):
    """True when the pets entry is the right answer to this line, so it keeps the turn."""
    if not (loss.a_pet_died(line) and loss.asks_about_the_remains(line)):
        return False
    # A feeling word is usually the person's own ("my cat died and i keep crying"), but not when
    # it is the predicate of the body question itself: "is cremation sad" is still about the body.
    return not loss.names_a_feeling(line) or loss.feeling_about_the_body(line)


DEFERS_TO = defers_to

# How many turns after the loss its remarks still belong to it.
REMEMBER = 3
# A remark is short; a long line has usually moved on to a subject of its own.
SHORT = 16

POSSESSIVE = re.compile(r"\b(?:my|our|his|her|their)\s+$")
SUDDEN = re.compile(r"\b(?:sudden|suddenly|out of the blue|no warning|shock|shocked)\b")
# "it was expected" is the opposite of sudden and needs its own reply.
EXPECTED = re.compile(r"\b(?:it was expected|was expected|we knew (?:it|this) was coming|"
                      r"we saw it coming|long illness|not a surprise|no surprise|"
                      r"been ill for (?:a|years|months))\b")
# The nights of a loss. The composer's grief pool answers a line like this too ("that is normal
# after a loss, and it eases slowly"), which is true of the loss and says nothing about the hour
# they were awake, so a night belongs to the pool below whatever the composer would say.
SLEEP = re.compile(r"\b(?:cant|can'?t|couldnt|couldn'?t|cannot|unable to|barely|hardly|not|never)"
                   r"\s+(?:sleep|sleeping|slept|stay asleep|get to sleep|get any sleep)\b|"
                   r"\b(?:havent|haven'?t|hasnt|hasn'?t|hadnt|hadn'?t|didnt|didn'?t)\s+"
                   r"(?:slept|been sleeping|had (?:any |much |much of any )?sleep)\b|"
                   r"\b(?:keep|kept|still)\s+waking\b|\bwaking (?:up )?(?:at|every|in the)\b|"
                   r"\bwoke (?:up )?at\b|\bawake (?:at|all|most of the)\b|"
                   r"\b(?:insomnia|sleepless|lying awake)\b|\b(?:3|4|5)\s?am\b")
# "i feel guilty" on its own can be about anything (a care home, a row), so the cue wants the
# past thing the person is going back over.
GUILT = re.compile(r"\b(?:should have|should've|shouldnt have|blame myself|my fault|regret|"
                   r"if only|wish i (?:had|could|was there)|didn'?t visit|didn'?t go|"
                   r"guilty (?:about|that|for)|so guilty i|more time with)\b")
# "it was really hard" is the most common line after a death, and the shortest.
HARD = re.compile(r"\b(?:it|that|yesterday|today|this morning|the day|last night)\s+"
                  r"(?:was|is|has been|'s been)\s+(?:so |really |very |pretty |just )?"
                  r"(?:hard|tough|awful|horrible|brutal|rough|difficult|shit|hell|"
                  r"the worst)\b")
CRYING = re.compile(r"\b(?:cry|crying|cried|tears|sobbing)\b|\bi broke down\b")
# Talking about it is the commonest thing a grieving person says, and nothing here read it:
# "i cant talk about it" reached a card about a child who cannot speak yet ("not speaking yet",
# "cant talk" in the family knowledge base) because one word was all that card needed. This line
# has no subject of its own - it refers back - so the loss keeps it, whatever else it matches.
TALK_ABOUT = re.compile(
    r"\b(?:cant|can't|couldnt|couldn't|could not|dont|don't|do not|not able to|not ready to|"
    r"struggl\w* to|hard to|too (?:hard|painful|raw|much) to)\s+(?:really\s+|even\s+|ever\s+)?"
    r"talk(?:ing)?\s+(?:about|of)\s+(?:it|him|her|them|that|this|any of it|any of that)\b")
# Every word for a person or a pet the composer knows, for the cues that need one of them.
_LIVING = "|".join(sorted(loss.PEOPLE | loss.PET_WORDS, key=len, reverse=True))
# Missing someone, and the dates: "i miss my old job" and "my friend forgot my birthday" are
# other things, so the cue has to point at the person.
MISSING = re.compile(r"\b(?:miss (?:her|him|them)|i miss my (?:"
                     + _LIVING + r")|think about (?:her|him|them)|"
                     r"(?:the|her|his|their) birthday|anniversary|dreamt? about (?:her|him)|"
                     r"photos? of (?:her|him|them))\b")
# "i cant talk to my brother about it" is that conversation, not a refusal to talk to me, so the
# sentence it needs is about the brother and keeps the reply it had.
TALK_TO_SOMEONE = re.compile(
    r"\b(?:talk|talking|speak|speaking)\s+(?:to|with)\s+(?:" + _LIVING +
    r"|my|our|the|his|her|a|an)\b"
    r"|\babout (?:it|that|this)\s+(?:with|to)\s+(?:" + _LIVING +
    r"|my|our|the|his|her|a|an)\b")
# A person saying they cannot talk about it, or will not: "i still cant talk about it", "i dont
# want to talk about it", "its too soon". The one thing the bot must not do with a line like
# that is answer it with something practical about the death - it was read as a care question
# about an older person living alone and answered with a council needs assessment, which is
# advice for a problem nobody named. A refusal is answered by accepting it.
CANT_TALK = re.compile(
    r"\b(?:i|we)\s+(?:still\s+|just\s+|really\s+)?"
    r"(?:cant|can't|couldnt|couldn't|cannot|won't|wont|dont|don't|do not|wouldnt|wouldn't|am not|not)\b"
    r"[^.!?]{0,24}\b(?:talk|talking|speak|speaking|say|saying)\b"
    r"[^.!?]{0,16}\b(?:about (?:it|that|this|him|her|them)|yet|now|today)\b"
    r"|\b(?:its|it's|that's|thats)\s+(?:too\s+(?:soon|raw|early|fresh)|too hard)\b"
    r"|\bnot ready to talk\b|\bcan we not talk about\b|\blets not talk about\b")
# The signs of them still around: listening for the door, saying goodnight.
SIGNS = re.compile(r"(?:still|keep) (?:look|looking|listen|listening|wait|waiting|expect|expecting) for "
                   r"(?:her|him|them)|(?:still|keep) (?:expect|expecting) (?:her|him|them)|(?:still|keep) (?:talk|talking|say|saying|tell|telling)\b"
                   r"[^.]{0,20}?\b(?:her|him|them)\b|think(?:ing)? i (?:see|hear) (?:her|him)|"
                   r"half expect|hear (?:her|him) voice")
# "he was 14", "aged 92", "in her 80s" — an age, not "it was 30 degrees".
AGE = re.compile(r"\b(?:he|she|it|they)\s+was\s+\d{1,2}\b(?!\s*(?:degrees|miles|kilos|kg|"
                 r"pounds|quid|minutes|hours|days|weeks|months|years|per cent|%))|"
                 r"\baged\s+\d{1,2}\b|\bin (?:her|his) (?:70s|80s|90s)\b")
# The number in it, so the reply can tell a long life from a young one. Under SHORT_LIFE the loss
# is someone with years they should have had: "that's a long time together" is a kind line at 92
# and a cruel one at 45, and a person is not old at 70.
AGE_NUMBER = re.compile(r"\b(?:he|she|it|they)\s+was\s+(\d{1,2})\b|\baged\s+(\d{1,2})\b|"
                        r"\bin (?:her|his) (\d)0s\b")
SHORT_LIFE = 70
# An animal's age is young against its own span, not a person's: fourteen is young for a parrot
# and a good long life for a dog, and one line for both reads as a stranger who does not know
# animals. The numbers are the usual span for the animal, in years.
ANIMAL_SPAN = {"dog": 12, "puppy": 12, "cat": 15, "kitten": 15, "rabbit": 8, "bunny": 8,
               "hamster": 2, "guinea": 6, "budgie": 8, "parrot": 40, "horse": 25, "pony": 25,
               "ferret": 8, "rat": 2, "fish": 5, "tortoise": 60, "snake": 15, "lizard": 10,
               "gerbil": 3, "chinchilla": 10, "cockatiel": 15,
               # The two-word name too, so the age is weighed against its span and the reply
               # says "a guinea pig" rather than "a guinea".
               "guinea pig": 6}
BELONGINGS = re.compile(r"\b(?:her|his|their|the)\s+(?:things|stuff|clothes|belongings|flat|"
                        r"house|room|wardrobe|shed)\b|\bpack(?:ing)? (?:it|them|her|his) up\b|"
                        r"\bclear(?:ing)? (?:out|it|them)\b|\bempty(?:ing)? (?:it|them|the)\b")
# A eulogy is a page someone has to write, so the writing is the question and the structure is
# the answer. "The eulogy is on tuesday" and "I'm scared of breaking down giving it" carry no
# writing word, and stay here.
EULOGY_WRITE = re.compile(r"\b(?:write|writing|wrote|draft|drafting|help|how|start|starting|"
                          r"opening|open|begin|length|long|words|minutes|structure|template|"
                          r"examples?|what do i say|say)\b")
EULOGY = re.compile(r"\b(?:eulogy|eulogies)\b")
ARRANGEMENTS = re.compile(r"\b(?:funeral|burial|cremation|eulogy|coffin|undertaker|"
                          r"funeral director|headstone|graveside|cemetery|order of service)\b")
REGISTER = re.compile(r"\b(?:register (?:the|her|his) death|registration|register office|"
                      r"registrar|death certificate|medical certificate)\b")
# The money question is the one people ask first and the one that is worst answered with a
# description of the day: "how much does a funeral cost".
COST = re.compile(r"\b(?:cost|costs|price|prices|priced|how much (?:does|is|will|do|are)|"
                  r"expensive|afford|cheap\w*|quote|pay for)\b")
WORK_PRESSURE_REPLIES = (
    "You don't owe anyone the details. \"{Who} died on Tuesday, I won't be in this week\" is "
    "enough for the first message, and a work friend can pass it round so you are not saying it "
    "again and again.",
    "Going back is often harder than the days before it. Ask for a phased return, a shorter week "
    "to start with, and one person to go to when it gets too much: most managers would rather you "
    "asked than quietly struggled.",
    "It is fine to say \"I'd rather not talk about it, but thank you\" and leave it there. People "
    "ask because they care and then run out of words, so give them the line and they will use it.",
)
WORK_REPLIES = (
    "Ask your manager in writing and keep it plain: what has happened, and how many days you "
    "need. Most employers have a bereavement leave policy, and HR has to give you it in a "
    "sentence if you ask.",
    "You don't owe anyone the details. \"{Who} died on Tuesday, I won't be in this week\" is "
    "enough for the first message, and a work friend can send it if a phone call is too much.",
    "Work can wait a week. Say what you can cover before you go and who is picking it up, then "
    "let the rest go - people cover for each other, and this is what that is for.",
)
# Probate has its own length, and "how long does probate take" was getting the banks and the
# death certificate, which is not the question. It is its own small answer.
PROBATE = re.compile(r"\b(?:probate|grant of probate|letters of administration)\b")
PROBATE_REPLIES = (
    "Probate is the court's permission to deal with the estate: you apply to HMCTS with the "
    "will and the death certificate. A straightforward application is usually decided within a "
    "few weeks, and a solicitor takes it on when the estate is large or the family expect a "
    "disagreement.",
    "How long probate takes depends on the estate. One bank and a house is often a few months "
    "from applying to the grant; shares, a business or a dispute take longer. Ask the solicitor "
    "for the likely date in writing at the first meeting, so you have something to plan around.",
    "Not everything needs probate. Joint accounts and anything held in trust usually pass "
    "without it, and banks often release small balances on the certificate alone. The rule of "
    "thumb is a house, or more than one bank, or a will that is not clear - then apply.",
)
# Probate is its own question with its own length ("how long does probate take"), and the
# banks-and-certificates reply is not an answer to it, so the word is not a paper cue here.
PAPERWORK = re.compile(r"\b(?:solicitor|paperwork|(?:the|her|his|their) will|"
                       r"(?:her|his|their) (?:bank|pension|insurance|accounts)|"
                       r"bereavement|the estate)\b")
# The day has parts other modules answer better: what to wear, the music, the flowers, the
# readings, how long the service runs and whether the children come. The arrangements are about
# booking and the order of service, so a line that names one of those is not an arrangements ask
# - "what do i wear to the funeral" was getting "ring the funeral director", which is not about
# clothes at all, and "should i take my kids to my mums funeral" was getting "be early, sit near
# the back" when the question was the children's.
ARRANGEMENTS_ELSE = re.compile(r"\b(?:wear|wearing|outfit|clothes|suit|dress|shoes|tie|"
                               r"music|songs?|hymns?|flowers?|wreath|bouquet|buffet|"
                               r"sandwiches|catering|reception|wake|drink)\b")
# Families fall out after a death: "my brother wants to help but we just argue".
FAMILY = re.compile(r"\b(?:brother|sister|dad|mum|stepdad|stepmum|uncle|aunt|nan|grandad|"
                    r"family|relatives|in-laws|siblings)\b[^.]{0,40}?\b(?:argue|arguing|"
                    r"argument|row|rows|rowing|fight|fighting|falling out|fell out|"
                    r"not talking|won'?t talk)\b")
# Who has to be told. The shape above reads only the bare "who do i tell", and the way people
# actually ask it puts the modal in the middle: "who do i have to tell", "who do i need to
# notify", "do i have to tell everyone". Those went to whatever card the composer had for the
# words - "who do i have to tell" was answered with how to talk to a child about a death, and
# "do i have to tell everyone" with an insurance policy. Both are the notification ask, and its
# answer is Tell Us Once and the register office.
TELL = re.compile(r"\b(?:who (?:do|should|must|would) (?:i|we) (?:have to |need to |ought to )?"
                  r"(?:tell|notify|inform|ring|contact)"
                  r"|who (?:needs? to know|needs? to be told|has to know|should (?:know|be told))"
                  r"|who to (?:tell|notify|inform)"
                  r"|(?:do|should) (?:i|we) (?:have to |need to )?(?:tell|notify|inform|ring) "
                  r"(?:everyone|everybody|anyone|people|the (?:council|bank|pension|tax office|"
                  r"dwp|hmrc|authorities|employer))"
                  r"|tell us once|who do i inform)\b")
# "what do i say to her mum", "how do i tell the kids" — words for a person, not paperwork.
# Two different asks hide in "what do i say": telling someone the news ("how do i tell the kids")
# wants the plain sentence to use, and being with someone who already knows ("she gets lonely
# since dad died - what do i say to her") wants what helps, which is not the announcement.
TELLING = re.compile(r"\bhow do i (?:tell|say|break)\b|\bhow to tell\b|\b(?:do|should) i tell\b|"
                     r"\bwhat (?:do|should|can) i tell\b|\bhow do i let .{0,20} know\b")
SAY_TO = re.compile(r"\bwhat (?:do|should|can) i say\b|\bwhat to say\b")
# Work is its own ask, and not the paperwork: "how do i ask for bereavement leave" is about the
# manager, the days and who covers, and "how do i tell my boss" is not breaking the news to a
# person who loved them. The paperwork answer (the bank, the death certificate, Tell Us Once) is
# the wrong thing to say to either.
# The word "my boss" alone is not the ask: "my boss is hard work at the moment" is a remark
# about work, and answering it with the bereavement-leave policy is answering a question nobody
# asked. The ask is to be told or asked of them.
WORK = re.compile(r"\b(?:bereavement leave|compassionate leave|leave from work|"
                  r"(?:ask|tell|ring|call|email) (?:my|the) (?:boss|manager|work|employer|hr)\b|"
                  r"\btell work\b|\bwhat do i tell work\b)")
# The other half of work: not the asking, but going back and being asked. Someone who says they
# cannot face it is not asking for the policy, and someone whose colleagues keep asking is not
# asking how to tell their manager.
# A word that makes the line about the job: "i cant face it" is about the house or the day, and
# answering it with what to say to a manager misreads someone at their lowest.
WORK_WORD = r"\b(?:work|job|boss|manager|office|shift|shifts|colleagues?|team|employer|hr)\b"
WORK_PRESSURE = re.compile(r"(?:(?=.*" + WORK_WORD + r").*?\b(?:back to work|off work|cant face|"
                           r"can't face|cant go back|can't go back|dread|too much|"
                           r"(?:keep|keeps|are) asking|everyone (?:keeps )?asking)\b"
                           r"|\b(?:people|everyone|folks|the team) at work\b)")
# The asks inside a loss that want a practical answer, not sympathy. They are answered even when
# the composer reads the line as one about the death too ("how do i register the death").
# The paperwork of a death is one job with many names, and people report it rather than ask
# about it: "i still havent sorted his paperwork", "i havent cancelled his pension", "is there
# a form to fill in". Read as a remark, each of those got a sympathy line ("I'm here. Take your
# time with it") or, for the form, a card about signing a PDF - the coldest possible answers to
# somebody saying what they are stuck on. Naming a piece of the admin is asking for help with it,
# whether or not the line has a question mark in it, so this is the reading for it.
ADMIN = re.compile(
    r"\b(?:paperwork|the papers|(?:a|any|one|the|that) forms?|filling in|fill in|"
    r"(?:his|her|their|the) (?:bank|banks|accounts?|pension|pensions|insurance|policies|policy|"
    r"passport|driving licence|licence|mobile|phone contract|utilities|bills?|mortgage|"
    r"tenancy|landlord|affairs)|council tax|(?:his|her|their) (?:benefits?|tax credits)|"
    r"universal credit|hmrc|the dwp|the tax office|dvla|the council|"
    r"(?:cancel|close|stop|sort out|sorted out|sorted|deal with|notify|inform|tell)\b"
    r"[^.]{0,36}?\b(?:subscription\w*|direct debits?|accounts?|pension|insurance|policy|"
    r"doctor'?s (?:surgery|practice)|dentist|the vet|employer|the council|the bank|"
    r"the tax office|his phone|her phone|the phone|the house|the mortgage|the tenancy)\b)\b")
ADMIN_REPLIES = (
    "None of it has to be done this week, and it goes faster by phone than by letter. The bank, "
    "the pension and the council each have a bereavement team: ring one a day, ask them to stop "
    "the letters, and write the reference number down on a single sheet as you go.",
    "One call does most of it: Tell Us Once tells the tax office, the council, the passport "
    "office and the DVLA in one go, and the register office sets it up when the death is "
    "registered. The bank and any pension are their own two calls.",
    "Do it in the order it hurts least: the bank first, because the account keeps running, then "
    "the pension, then the bills. As next of kin you can do all of it on their behalf, and you "
    "don't need probate to tell anybody anything.",
)

PRACTICAL = (TELL, TELLING, SAY_TO, WORK_PRESSURE, WORK, REGISTER, COST, PROBATE, ADMIN,
             PAPERWORK, ARRANGEMENTS, BELONGINGS)

# A line about a child, or about someone ill right now, is not a remark about the loss: those
# belong to the modules that answer for a child's bad night or an emergency.
OTHER_PERSON = re.compile(r"\bmy (?:baby|boy|girl|son|daughter|kid|child|toddler|teenager|"
                          r"husband|wife)\b|\b\d{1,2} year old\b")
EMERGENCY = re.compile(r"\b(?:wont wake|cant wake|can'?t wake|unresponsive|not breathing|"
                       r"ambulance|999|911|chest pain|a and e|a&e|temperature|floppy|seizure|"
                       r"overdose|suicidal|bleeding|collapsed)\b")

SUDDEN_REPLIES = (
    "Sudden is the hardest kind — nothing gets you ready for it. It comes in waves for weeks, "
    "so don't be surprised when a good hour turns into a bad one.",
    "That kind of shock takes ages to settle, and there's no doing it faster. Go as slowly as "
    "you can, and let people do the small things for you.",
)
EXPECTED_REPLIES = (
    "Even when you know it's coming, it still lands hard — knowing and being ready are two "
    "different things. There's nothing wrong with being knocked sideways by it.",
    "Expected doesn't make it easier, it just means you spent a long time watching it happen. "
    "That takes it out of you too, so rest when you can.",
)
SLEEP_REPLIES = (
    "Sleep is the first thing to go with this. Don't lie there fighting it: get up, warm drink, "
    "something dull, and go back when you're sleepy.",
    "Hardly sleeping is the usual pattern after a loss, and it does ease. Keep the room cool "
    "and dark, get up rather than lie there, and catch up in the day if you can.",
)
GUILT_REPLIES = (
    "That guilt is a very common part of this, and it is almost never deserved. If it helps, "
    "say out loud what you'd want {who} to say to you now.",
    "Everyone finds something to blame themselves for afterwards. {Who} would not want you "
    "carrying that.",
)
HARD_REPLIES = (
    "It is, and there's no getting round how hard it is. Do less today than you think you "
    "should, and let people bring you things.",
    "It's allowed to be that hard. Nothing about the first days is normal, so don't measure "
    "yourself against anyone else getting through it.",
)
TALK_ABOUT_REPLIES = (
    "You don't have to. Say as much or as little as you want, and I'm here for the parts that "
    "aren't words.",
    "That's alright. Nothing has to be said here - tell me when you want to, and not before.",
)
CRYING_REPLIES = (
    "Crying is the pressure valve, not a setback. Let it come, then get outside for ten minutes "
    "if you can.",
    "That's normal, and better out than held in. It gets further apart, not gone.",
)
MISSING_REPLIES = (
    "That's a big miss, and it doesn't fade quickly. The stories keep {who} close, so go on "
    "telling them.",
    "The dates are the hard ones — the birthday, Christmas, the day itself. Doing one small "
    "thing for {who}, a photo out or a meal they liked, can take the edge off.",
)
CANT_TALK_REPLIES = (
    "That's alright, you don't have to — not now, not with me. I'm here whenever it helps, "
    "and we can talk about anything else in the meantime.",
    "Then we won't. Say as much or as little as you want, and we can leave {who} out of it "
    "for now.",
    "Fair enough. Nothing to explain, and no rush: tell me about something ordinary instead "
    "if that's easier today.",
)
SIGNS_REPLIES = (
    "That's one of the strangest parts — the house keeps the shape of {who}. It eases on its "
    "own, slowly, so don't talk yourself out of it.",
    "Keep going if it helps. Saying goodnight, or talking out loud, is how a lot of people get "
    "through the first year, and it isn't daft.",
)
AGE_REPLIES = (
    "That's a long time together. It's the routines that catch you out more than the big days: "
    "the same chair at the same time, nobody in it.",
    "A good long life still leaves a big hole. Be as sad as you need to be about it.",
)
# Under YOUNG: a life cut short needs no consolation about how long it was.
# An animal that reached the end of its span: "fourteen is a good age for a dog" is the true
# thing, and it does not soften the loss.
PET_OLD_REPLIES = (
    "{Age} is a good age for a {animal}, and it still isn't enough. Be as sad as you need to be "
    "about {who}.",
    "That's a long life for a {animal}. It doesn't make the house any quieter, and it isn't "
    "meant to.",
)
PET_YOUNG_REPLIES = (
    "{Age} is no age for a {animal}. Nothing about it is fair, and it's alright to say so out "
    "loud.",
    "{Who} should have had years more than that. It was far too soon, and there is no sense to "
    "be made of it.",
)
YOUNG_AGE_REPLIES = (
    "That's far too young, and there is no sense to be made of it. You don't have to try tonight.",
    "{Who} should have had years more than that. Nothing about it is fair, and it's alright to "
    "say so out loud.",
)
BELONGINGS_REPLIES = (
    "Do a little at a time, and don't do it alone: one drawer with someone there, then stop. "
    "Nothing has to go this week.",
    "You don't have to sort {who}'s things to be doing it right. Pick one small thing, give "
    "the rest a few months, and keep anything you're not sure about.",
)
REGISTER_REPLIES = (
    "The death is registered at the local register office, usually within five days. The "
    "hospital or the funeral director tells you which one; take the medical certificate, and "
    "get several copies of the death certificate while you're there.",
    "You do that at the register office for the area where it happened. Book first, take the "
    "medical certificate, and buy a few extra certificates — every bank and pension will want "
    "one.",
)
COST_REPLIES = (
    "Ask two funeral directors for a written, itemised quote — the coffin and the cars are "
    "where it adds up, and a cremation with no service costs a fraction of a full funeral. "
    "Nothing has to be decided on the first call.",
    "Say what you actually want before they price it: a simple coffin, no cars, family carrying "
    "it. If money is tight there's a funeral expenses payment from the DWP, and the council will "
    "help as a last resort.",
)
ARRANGEMENTS_REPLIES = (
    "Ring the funeral director first — they do the rest of it. Take someone with you to the "
    "meeting, and ask about costs up front.",
    "For the day itself: be early, sit near the back if you might need air, and don't feel you "
    "have to talk to everyone.",
)
PAPERWORK_REPLIES = (
    "The bank and the council want the death certificate, and most places have a bereavement "
    "line that does the telling once. Ask them to do that rather than ringing round yourself.",
    "Probate is only needed if there's a house, savings over the limit or shares. A solicitor "
    "will do a free first call, and it can wait a few weeks.",
)
FAMILY_REPLIES = (
    "That happens in nearly every family, and it's the grief talking as much as anything — "
    "everyone is at a different speed. Split the jobs so you're not doing the same one: you "
    "take the house, they take the paperwork.",
    "It's worth naming it out loud, once, when nobody's tired: \"we're going to snap at each "
    "other and that's fine, but let's not do it over the house\". Then give each other room.",
)
TELLING_REPLIES = (
    "Keep it plain, and say the name: \"{who} died on Tuesday\" is kinder than a soft way round "
    "it. Then let them talk, and don't be afraid to say you don't know what to say either.",
    "Say it once, plainly, and then be quiet with them for a bit. People remember being told "
    "kindly far longer than the exact words.",
)
# Being with someone who already knows: there is no announcement to make, and offering words for
# one is what turned "what do i say to her" into advice to tell her about the death.
SAY_TO_REPLIES = (
    "You don't need the right words. Ask about {who}, and let them talk as long as they want; "
    "that does more than anything you could say.",
    "Say the true things: that you're sorry, that you miss {who} too, and that you're around. "
    "Then follow their lead - if they want to laugh about something, laugh.",
    "Ask what the day has been like, and take the answer however it comes. Not filling the "
    "silence is a kindness in itself.",
)
TELL_REPLIES = (
    "Tell Us Once does most of it in one go — the passport, driving licence, HMRC and the "
    "council. The bank and any pension want their own call, and their bereavement line is the "
    "quickest way in.",
    "Start with the people who need to act this week: the employer, the bank, the landlord if "
    "there is one. Everything else can wait until you've had a few days.",
)
COMPANY_REPLIES = (
    "I'm here. Say as much or as little as you like about {who}.",
    "No need to be all right about it with me. If you'd rather talk about something else for a "
    "while, that's fine too.",
)

# A short doubt about themselves, a turn or two into a death: "is that bad", "am i ok", "is that
# weird", "am i going mad". They name no subject, so none of the readings below see them, and they
# reached the composer's floor - "Alright then - good luck with it" for the "is that" ones and
# "Glad to hear it" for "am i ok", which are the worst two lines in the bot for a bereaved person.
# What they are asking is whether what is happening to them is wrong, so the answer says it is not,
# that grief has no timetable, and gives one thing to keep an eye on - never a diagnosis, never a
# cheerful sign-off.
#
# Two shapes, because they ask the same thing from different sides: "is that bad" is about what is
# happening, "am i going mad" is about them, and a line that says "you are not losing it" reads
# wrong after the first one.
DOUBT_IT = re.compile(
    r"^(?:and |so |ok(?:ay)?,? )?"
    r"(?:is (?:that|this|it) (?:bad|ok(?:ay)?|all right|alright|wrong|weird|odd|a bad sign)"
    r"|is that how it (?:goes and works|goes|works))"
    r"(?: then)?[\s?.!]*$")
DOUBT_ME = re.compile(
    r"^(?:and |so |ok(?:ay)?,? )?"
    r"(?:am i (?:ok(?:ay)?|all right|alright|normal|going mad|going crazy|losing it|losing my mind)"
    r"|does that make me (?:weird|mad|crazy))"
    r"(?: then)?[\s?.!]*$")
DOUBT_IT_REPLIES = (
    "It is not a bad sign, and there is nothing here you have to fix today. The part worth "
    "keeping an eye on is eating and sleeping.",
    "Not that, no. Grief is not an illness and it does not run to a timetable - the waves get "
    "further apart, they do not stop.",
    "That is grief doing its work, not a weakness. It comes in waves, and the waves get further "
    "apart as time goes on - they do not stop.",
    "It eases slowly, and it does not go in a straight line - a better day is not a setback.",
)
DOUBT_ME_REPLIES = (
    "Nothing about that is wrong with you. Grief is not an illness and it does not run to a "
    "timetable - the waves get further apart, they do not stop.",
    "No, you are not losing it. This is what a death does to a person, and it comes in waves "
    "rather than a straight line down.",
    "You are allowed to be like this. If you are not sleeping or eating at all after a couple of "
    "weeks, that is the point to say it to your GP.",
    "It is not something to be good at. If it helps, the thing to hold on to is that a bad hour "
    "does not undo a good one.",
)


# An open ask with nothing in it that this module has a reading for: "what do i do now", "now
# what", "where do i start". A person two lines into a death who asks that is asking how to get
# through the day, not for information, and the fallback's honest-but-cold "I'd rather not guess,
# a quick search online will get you a solid answer" sends a bereaved person to a search engine.
# Nothing here repeats the sympathy or names a task that may not be theirs, and each line gives
# one thing to do today.
OPEN_ASK = re.compile(r"^(?:so |and |ok(?:ay)?,? )?(?:"
                      r"(?:what|where) (?:do|should|can|could|shall) (?:i|we) "
                      r"(?:do|start|begin|go from here|take on)(?: now| next| first| today)?"
                      r"|what now|now what|what happens now|what next"
                      r"|where do i (?:start|begin)(?: from here)?"
                      r"|how do i (?:get through|deal with|cope with) (?:this|today|it|the day)"
                      # "i dont know what to do" and "i dont know where to start" name nothing
                      # either, and they are how people say it when they cannot form the question.
                      r"|(?:i |we )?(?:don'?t|dont|do not) know what to (?:do|say)"
                      r"(?: now| next| first| today)?"
                      r"|(?:i |we )?(?:don'?t|dont|do not) know where to (?:start|begin)"
                      r")(?:\s+then)?\s*[.?!]*$")
OPEN_ASK_REPLIES = (
    "Nothing big, today. Eat something, drink some water, and let one person who knows be with "
    "you. The rest can wait until tomorrow.",
    "Keep it small. One phone call, one meal, and say yes to anybody who offers to help - nobody "
    "expects you to hold it all at once.",
    "You do not have to work anything out today. Take the offers that come, and leave the "
    "decisions until you have slept.",
    "When you have a quiet hour, write down the things only you know about {who}. The admin can "
    "wait a week; the small details are the ones that go.",
    "Pick the one thing that would make tomorrow easier, do that, and let the rest be someone "
    "else's job for now.",
    "Slow is fine. Do the next necessary thing, and if there is someone who can sit with you, "
    "ask them to.",
)


def _words(text):
    """The line as words: lower case, apostrophes flattened, punctuation off the ends."""
    text = str(text or "").lower().replace("\u2019", "'")
    return [word.strip(".,!?;:\"'()") for word in text.split() if word.strip(".,!?;:\"'()")]


def _who(words):
    """(the one who died, said back as the user would — "your nan" — and whether it is a pet),
    or (None, False) when the line names neither."""
    # Two words when the animal takes two, so "my guinea pig died" is not "your guinea": the
    # store's record is what every later line is said with.
    animal = loss.the_animal(" ".join(words))
    if animal:
        return "your " + animal, True
    for word in words:
        singular = word[:-1] if word.endswith("s") and word[:-1] in loss.PET_WORDS else word
        if singular in loss.PEOPLE or singular in loss.PET_WORDS:
            return "your " + singular, singular in loss.PET_WORDS
    return None, False


def _record(text, memory):
    """Write the loss this turn is about, so the turns after it are read in it."""
    if not isinstance(text, str) or not text.strip():
        return
    clean = " ".join(_words(text))
    if not clean or not loss.reads_as_loss(clean):
        return
    if loss.whose(clean) != "own":
        return  # "my friend's mum died" is someone else's loss; the composer answers what to say
    who, pet = _who(_words(text))
    if not who:
        return
    memory["loss"] = {"who": who, "pet": pet, "turn": len(memory.get("turns") or []),
                       # Somebody at the end of their treatment is not a death that has
                       # happened: "the doctor said theres nothing more they can do" is the days
                       # before it, and what is asked after it is about those days.
                       "ahead": loss.is_dying_now(clean)}


# A line that only says thanks, or that they are alright. "ok so low heat then" starts the same
# way and is about the oven, so the whole line has to be the thanks.
THANKS_LINE = re.compile(
    r"^(?:ok(?:ay)?[,.!]?\s*)?(?:(?:thanks|thank you|thankyou|ta)(?:\s+(?:for|so much|very much)"
    r"\s*(?:listening|talking|that|the chat|your help)?)?|(?:im|i'm|i am)\s+(?:ok|okay|fine|"
    r"alright)(?:\s+now)?|ok(?:ay)?)[.!, ]*$")
# The modules that answer a bereavement, so a "thanks" after either of them is inside the loss.
LOSS_SPEAKERS = ("loss", "grief")


def _still_here(memory):
    """True when the turn before this one was about the loss (either speaker), so a thanks
    belongs here and not to the small-talk module."""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    return str(turns[-1].get("module") or "") in LOSS_SPEAKERS


def _next_to_the_loss(record, memory):
    """True when the loss is the thing in hand, not just somewhere in the thread.

    A short doubt ("am i ok", "is that bad") is about the loss only when the loss is what was
    just being talked about: either the last reply was this module's own, or the line before the
    doubt reads as grief itself. A promotion, a broken boiler or a child's temperature said
    between a death and "is that bad" is that subject's turn - the pools would otherwise read
    every doubt in a bereaved thread as a doubt about grief, which is how "my dad died last week"
    / "my boiler is broken" / "is that bad" got the waves of grief.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return False
    # This module replied on the turn just gone: `replied` is the index that turn was appended at.
    if isinstance(record, dict) and record.get("replied") == len(turns) - 1:
        return True
    # The composer's loss arm answered the turn just gone: "i feel guilty all the time" is not in
    # any pattern below, and the doubt that follows it is still the loss's.
    if str(turns[-1].get("module") or "") in LOSS_SPEAKERS:
        return True
    previous = " ".join(str(turns[-1].get("user") or "").split())
    if not previous:
        return False
    return bool(loss.reads_as_loss(previous) or FAMILY.search(previous) or GUILT.search(previous)
                or CRYING.search(previous) or SLEEP.search(previous) or HARD.search(previous))


def _remembered(memory):
    """The loss the last few turns were about, or None when it is older than that."""
    record = memory.get("loss")
    if not isinstance(record, dict) or not record.get("who"):
        return None
    if record.get("turn", 0) < len(memory.get("turns") or []) - REMEMBER:
        return None
    return record


def _age(clean):
    """The number the line gives, or None."""
    match = AGE_NUMBER.search(clean)
    if not match:
        return None
    return int(match.group(1) or match.group(2) or (match.group(3) + "0"))


def _animal(who):
    """The animal the loss is about, or None when it is a person."""
    # The longest name wins, so "a guinea pig" is not read as "a guinea" and an age is not
    # weighed against the wrong animal's span.
    for word in sorted(ANIMAL_SPAN, key=len, reverse=True):
        if re.search(r"\b" + word + r"\b", who or "", re.I):
            return word
    return None


def _any_animal(who):
    """The animal, named or generic: "my pet died" is a pet as much as "my dog died" is."""
    animal = _animal(who)
    if animal:
        return animal
    return "pet" if re.search(r"\b(?:your )?pets?\b", who or "", re.I) else None


def _young(clean, who=""):
    """Whether the age in the line is a life cut short rather than a long one.

    Against the animal's own span for a pet, and against a person's for a person.
    """
    number = _age(clean)
    if number is None:
        return False
    animal = _animal(who)
    if animal:
        return number < ANIMAL_SPAN[animal] * 0.8
    return number < SHORT_LIFE


def _age_pool(clean, who):
    """The pool the age asks for, filled with the number and the animal the loss is about."""
    number = _age(clean)
    animal = _animal(who)
    pool = YOUNG_AGE_REPLIES if _young(clean, who) else AGE_REPLIES
    if animal:
        pool = PET_YOUNG_REPLIES if _young(clean, who) else PET_OLD_REPLIES
    filled = []
    for reply in pool:
        reply = reply.replace("{who}", who).replace("{Who}", who[:1].upper() + who[1:])
        reply = reply.replace("{animal}", animal or "").replace("{Age}", _word(number))
        filled.append(reply)
    return filled


def _word(number):
    """The age as a word, because "14 is a good age" reads like a form."""
    words = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
             8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen",
             14: "Fourteen", 15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen",
             19: "Nineteen", 20: "Twenty"}
    if number is None:
        return "That"
    return words.get(number, str(number))


def _fill(pool, who):
    return [reply.replace("{who}", who).replace("{Who}", who[:1].upper() + who[1:])
            for reply in pool]


# The paperwork of a death is a person's paperwork: there is no register office for a dog, no
# probate, no funeral payment and no funeral director. Those pools say nothing true about an
# animal. Where the answer the person would get instead is about the animal - the knowledge
# base's pet entry, with the vet, the cremation and the paw print - this module stands back and
# lets it through. Where the replacement is a person's answer too (a bare "do i need probate" in
# a pet's thread reaches HMCTS, and the price of buying a puppy reaches "how much does it cost
# to cremate a dog"), it says the true thing instead of swapping one wrong turn for another:
# a pet has none of that. The vet arranges the cremation or the burial.
# The asks that are about a person's paperwork, and have no meaning for an animal. The
# notification ask belongs here for the same reason the register office does: a cat has no
# passport, no HMRC record and no Tell Us Once, so "my cat died" / "who do i need to notify" was
# answered with Tell Us Once - the person's answer, for an animal that has none of it. The pet
# answer is the vet, who arranges the cremation or the burial.
PERSON_ONLY = (REGISTER, COST, PROBATE, PAPERWORK, ARRANGEMENTS, TELL, ADMIN)

ANIMAL_PAPERWORK_REPLIES = (
    "None of that applies to {who}: nothing gets registered and there is no estate to deal "
    "with. Ring the vet who saw them - they arrange the cremation or the burial, and they will "
    "tell you what it costs.",
    "A pet leaves no estate and no paperwork. The vet is the one who arranges the cremation or "
    "the burial, and they will give you the options and the price in one call.",
    "There is nothing official to do for {who}. Tell the vet you would like them to arrange it, "
    "and ask about the ashes and the cost while you are on the phone.",
)


def respond(text, memory):
    """Answer a short remark inside a recent loss, naming the person; else None."""
    words = _words(text)
    if not words or len(words) > SHORT:
        return None
    clean = " ".join(words)
    if OTHER_PERSON.search(clean) or EMERGENCY.search(clean):
        return None  # a child's bad night, or someone ill right now, is another module's turn
    if lookup.a_colour_is_worn(memory.get("understood") or {}):
        # A colour asked about the funeral is the wearing question, and the knowledge base holds
        # that row ("Familiar, subdued clothes are the thing: black or dark colours"). The pools
        # here are about the person and about the arrangements, and a chat that already carries a
        # death read "is black ok at the funeral" as the day itself: "be early, sit near the back
        # if you might need air". The composer stands aside for the same lines, so this module
        # has nothing to answer even when the line has no death word in it of its own.
        return None
    if loss.FUNERAL.search(clean) and loss.a_part_of_the_day_asked(clean):
        # The parts of the day - the music, the readings, the flowers, how long it runs, whether
        # the children come - are knowledge rows, and this module's pools are about the person,
        # not the arrangements. "how long does a funeral service last", a turn after "my dad is
        # dying", was answered with the carer's tiredness, and a chat about a cat was told "none
        # of that applies to your cat" when the line was about a father's funeral.
        return None
    record = _remembered(memory)
    if not record:
        return None
    # The composer reads a line about a death, and the turns after one, better than this module
    # does, and its wording is the one to keep: when it has a reply for this line, let it answer.
    # The exception is a practical ask it answers with sympathy ("how do i register the death"
    # got "I'm so sorry to hear that") - that is the question this module exists to answer.
    if loss.dying_in_the_chat(memory) and (loss.SAY_GOODBYE.search(clean)
                                          or TELLING.search(clean) or SAY_TO.search(clean)):
        # Somebody is dying and not dead: "how do i say goodbye to her" wants the visit, and the
        # announcement pool ("say the name: she died on Tuesday") is the wrong week. The
        # composer has the pool for it (DYING_SAY_REPLIES), so this module stands back.
        return None
    # A night is this module's own answer even inside a loss: the composer's grief pool would say
    # the loss is normal and say nothing about the hour they were awake, and the same complaint
    # said another way ("3am again") already came here. So the composer is not asked about these.
    pool = None if SLEEP.search(clean) else _composer_pool(text, memory)
    if pool is not None:
        practical = (_asks(clean) or ADMIN.search(clean)) and any(
            p.search(clean) for p in PRACTICAL)
        # A work ask takes the turn whatever the composer has: its reply is about comforting
        # someone bereaved ("offer one concrete thing - a lift, a meal, covering a shift"),
        # which is not what "how do i ask for bereavement leave" is asking.
        # The admin and the telling ask do too. Somebody who names the paperwork they are stuck
        # on is not asking to be comforted, and "who do i have to tell" is not a question about
        # how to talk to a child: on those words the composer's card is a guess at a subject,
        # where this module has the answer. Only a loss pool beats every one of them.
        if not (practical and (pool is loss.LOSS_REPLIES or WORK.search(clean)
                               or WORK_PRESSURE.search(clean) or TELLING.search(clean)
                               or TELL.search(clean) or ADMIN.search(clean))):
            return None
    if loss.reads_as_loss(clean) and not any(p.search(clean) for p in PRACTICAL):
        return None
    who = record["who"]
    if CANT_TALK.search(clean) and not TALK_TO_SOMEONE.search(clean):
        # A refusal to talk about it is not a question about the death, and the answer is to
        # accept it: no advice, no question, the door left open.
        record["replied"] = len(memory.get("turns") or [])
        return _pick(_fill(CANT_TALK_REPLIES, who), memory, clean)
    # An open "what do i do now" is answered here rather than by the loop below: it names no
    # thing for any of those patterns to read, which is how it reached the search hedge. It is not
    # claimed when the answer already on the table was a practical one: "my dog is dying" / "where
    # do i start" has the vet, the cremation and the paw print in it, and that is the turn.
    if OPEN_ASK.match(clean) and not any(p.search(clean) for p in PRACTICAL) \
            and not _answered_by_the_knowledge_base(text, memory):
        record["replied"] = len(memory.get("turns") or [])
        return _pick(_fill(OPEN_ASK_REPLIES, who), memory, clean)
    # A short doubt about themselves is answered here rather than by the loop below: it names no
    # thing for any of those patterns to read, which is how it reached the sign-off floor. It is
    # asked after the open ask above, which is the same shape said with a subject in it, and only
    # when the loss is the thing in hand rather than a subject the thread moved on to.
    next_to_the_loss = _next_to_the_loss(record, memory)
    if next_to_the_loss:
        for doubt, pool in ((DOUBT_IT, DOUBT_IT_REPLIES), (DOUBT_ME, DOUBT_ME_REPLIES)):
            if doubt.match(clean):
                record["replied"] = len(memory.get("turns") or [])
                return _pick(pool, memory, clean)
    for pattern, pool in ((FAMILY, FAMILY_REPLIES), (WORK_PRESSURE, WORK_PRESSURE_REPLIES),
                          (WORK, WORK_REPLIES), (TELL, TELL_REPLIES),
                          (TELLING, TELLING_REPLIES), (SAY_TO, SAY_TO_REPLIES),
                          (REGISTER, REGISTER_REPLIES), (COST, COST_REPLIES),
                          (PROBATE, PROBATE_REPLIES), (PAPERWORK, PAPERWORK_REPLIES),
                          (ADMIN, ADMIN_REPLIES),
                          (ARRANGEMENTS, ARRANGEMENTS_REPLIES),
                          (BELONGINGS, BELONGINGS_REPLIES), (EXPECTED, EXPECTED_REPLIES),
                          (SUDDEN, SUDDEN_REPLIES),
                          (SLEEP, SLEEP_REPLIES), (HARD, HARD_REPLIES),
                          (TALK_ABOUT, TALK_ABOUT_REPLIES), (GUILT, GUILT_REPLIES),
                          (CRYING, CRYING_REPLIES), (AGE, None),
                          (SIGNS, SIGNS_REPLIES), (MISSING, MISSING_REPLIES)):
        if pattern in PERSON_ONLY and _any_animal(who):
            if _the_answer_says_the_animal(text, memory, _any_animal(who)):
                continue  # the knowledge base's own pet answer is the turn
            if pattern.search(clean):
                # a dog has no register office, no probate and no funeral director, and the
                # replacement on the table is a person's answer: say what is true for the pet.
                record["replied"] = len(memory.get("turns") or [])
                return _pick(_fill(ANIMAL_PAPERWORK_REPLIES, who), memory)
        if pattern is ARRANGEMENTS and (ARRANGEMENTS_ELSE.search(clean)
                                        or loss.a_part_of_the_day_asked(clean)):
            continue  # the clothes, the music, the flowers and the children are other answers
        if (pattern is ARRANGEMENTS and EULOGY.search(clean)
                and EULOGY_WRITE.search(clean)):
            continue  # writing it is a writing job, and the knowledge entry gives the structure
        if pattern.search(clean):
            record["replied"] = len(memory.get("turns") or [])
            if pool is None:  # an age: which reply depends on how old they were, and of what
                pool = _age_pool(clean, who)
            return _pick(_fill(pool, who), memory)
    # A "thanks" belongs to the loss while the thread is still that loss: the composer answers
    # the turn before it, so requiring that this module answered last would send "thanks for
    # listening" to the small-talk module ("No problem at all. Shout if you need anything else")
    # a turn after the bot was told about the death.
    if THANKS_LINE.match(clean) and _still_here(memory):
        record["replied"] = len(memory.get("turns") or [])
        return _pick(_fill(COMPANY_REPLIES, who), memory)
    return None


ASK_OPENERS = frozenset(("how", "what", "who", "when", "where", "which", "should", "can",
                         "do", "does", "is", "are", "could", "would", "any", "am"))


def _asks(clean):
    """True when the line asks something, rather than telling the bot the news."""
    return "?" in clean or (clean.split() or [""])[0] in ASK_OPENERS


def _composer_pool(text, memory):
    """The pool the composer would answer this line from, or None when it has no line for it."""
    try:
        return loss.reply_for(text, memory)
    except Exception:  # noqa: BLE001 - a reading that fails just leaves the line to this module
        return None


def observe(text, memory):
    _record(text, memory)


def _the_answer_says_the_animal(text, memory, animal):
    """True when the answer on the table for this line is about the animal.

    The paperwork pools are a person's, so for an animal they stand down - but only into an
    answer that is the pet's own. A line that names the species reaches the pet-loss card (the
    vet, the cremation, the paw print); a bare "where do i register the death" inside a pet's
    thread reaches the register office for a person, and swapping this module's register line
    for that one helps nobody.
    """
    try:
        from . import answers
        topic = memory.get("topic")
        topic = topic.get("text", "") if isinstance(topic, dict) else ""
        asked = (topic + " " + text).strip() if topic else text
        got = answers.respond(asked, copy.deepcopy(memory))
    except Exception:
        return False
    if isinstance(got, dict):
        got = got.get("reply") or ""
    low = str(got or "").lower()
    if not (("vet" in low) or (bool(animal) and animal in low)):
        return False
    # ... and it must be about the loss, not just the animal. "how much does it cost to cremate a
    # dog" reaches the price of buying one, which names a dog and a vet's first visit and would
    # answer a cremation price with 800 pounds for a puppy. The answer has to name the death.
    return bool(PET_LOSS.search(low))


# What an answer has to say to be the pet's own answer to a line about its death. The vet, the
# ashes and the paw print are the pet-loss card; the price of a puppy is a different subject.
PET_LOSS = re.compile(
    r"\b(?:die[ds]?|dying|death|dead|passed away|put (?:down|to sleep)|euthan\w*|cremat\w*|"
    r"ashes|urn|casket|coffin|burial|bur(?:y|ied|ies)|body|remains|paw print|lock of fur|"
    r"last (?:visit|day)|goodbye)\b")


def _answered_by_the_knowledge_base(text, memory):
    """True when the knowledge base has a real answer for this line.

    The modules are asked in order and grief comes before answers, so an open ask claimed here
    takes away the answer the person was about to get: "my dog is dying" / "where do i start"
    has the vet, the cremation and the paw print in it, and that is the whole turn. The answer
    is asked for on a copy of memory so nothing is written twice.

    A bare ask has no thing in it, so the thing the chat is on goes in front of it: "my dog is
    dying" / "what do i do now" is a question about the dog, and the pet-loss entry answers it
    once the line carries the dog. Without the join the entry is never reached and the pool of
    lines for a loss takes a turn that had a real answer.
    """
    try:
        from . import answers
        topic = memory.get("topic")
        topic = topic.get("text", "") if isinstance(topic, dict) else ""
        asked = (topic + " " + text).strip() if topic else text
        return bool(answers.respond(asked, copy.deepcopy(memory)))
    except Exception:
        return False


def _pick(options, memory, seed_text=""):
    """One of the replies, not the one the bot said last time.

    `seed_text` is the person's line where the caller has it, so two people asking the same open
    question in their own words do not get the same sentence just because both are turn two.
    """
    try:
        return compose_pick(list(options), memory, seed_text)
    except Exception:  # noqa: BLE001 - a reply is still needed if the picker fails
        return options[0]
