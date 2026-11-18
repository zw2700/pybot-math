"""A bare yes/no question about the thing the bot just explained, answered from that answer.

"I think my knee clicks going up the stairs" gets the harmless-or-not answer. Then "is that
bad" arrives, and the bot says "Alright then — good luck with it.": the person asked whether
what it just told them matters, and the reply hands them the door. "is that normal" is worse
still, because it gets "I'm not sure about that one — a search", which disowns the very thing
the bot explained two seconds ago.

The answer is already in the bot's own last line, so this reads it. Three shapes come out of
that reading, and each has its own pool:

- the reply called the thing ordinary ("usually harmless", "that is normal") -> say no, and say
  what would change the answer;
- the reply said to get someone in, with no condition on it -> say yes;
- the reply gave a job to do and a "if it carries on, get someone in" after it -> say it is a
  job rather than a danger, and point at the condition.

Nothing is invented about the subject: every line says what the previous answer already said,
and what would change it. It stands aside for anything that is not bare ("is my knee normal"
names its own subject and belongs to the knowledge base), for a previous turn that was not a
knowledge answer (a safety line's referral is not a verdict to re-read, and "should i be
worried" after one must not be told "no"), for a previous turn with no verdict in it, and for
its own answers, so a person asking twice does not get the same sentence twice.
"""
import re

from ..memory import again as again_reply
from ..understanding.normalize import normalise
from . import A_STEP_ASK, pick, why
from ..memory import healing
try:  # the shared reading of a line as news that went well, so a floor does not treat it as a symptom
    from .goodnews import reads_as_good_news as _reads_as_good_news
except Exception:  # noqa: BLE001 - a reading that cannot be imported just adds no guard
    _reads_as_good_news = None
try:  # whether a death word in the line is about a thing that stopped, so a doubt is not a loss
    from .loss import a_thing_stopped as _a_thing_stopped
except Exception:  # noqa: BLE001 - a reading that cannot be imported just adds no guard
    _a_thing_stopped = None

# The whole line, not a prefix: "is that bad" is a question about the last thing said, while
# "is that bad for the baby" or "is my knee normal" carry their own subject and are someone
# else's to answer.
BARE = re.compile(
    r"^(?:and |so )?(?:is|was|are|were|does|do|did) (?:that|this|it|all of that|all that)"
    r"(?: (?:really|actually|very|too|that))?"
    r"(?: (?:bad|normal|serious|dangerous|ok|okay|alright|all right|acceptable|fine|safe|common|"
    r"weird|odd|strange|a problem|"
    r"something to worry about|anything to worry about|worth worrying about|"
    # "is that something i should worry about" is the same ask as "is that anything to worry
    # about", and the two words in the middle of it were the whole difference: the ruling reader
    # did not match and the worry pool did not either, so a person asking whether a knee or a
    # boiler needed a doctor got "That's beyond what I know well, sorry. Searching for it will
    # turn up better sources". The ask names nothing of its own, so the answer above it is what
    # it is about, which is exactly what this file answers.
    r"(?:something|anything|a thing) (?:i should|to|that i should|worth) worry(?:ing)? about|"
    r"something (?:i should|to) be worried about))"
    r"(?: then| though| or not)?$"
    r"|^(?:and |so )?should i (?:be )?(?:worried|worry|worrying)(?: then| though)?$"
    # "when should i worry" is the same doubt as "should i worry" about the answer just given,
    # and it is the one that names what it wants: the condition. Bare, it has no subject of its
    # own, so no reading of a subject finds it and it reached the search hedge one line after a
    # card that had written the condition out ("my mum keeps forgetting things" / "when should i
    # worry" -> "I'd rather not guess, do a search"). With a subject it stays a knowledge
    # question ("when should i worry about my knee"), so only the bare form is here.
    r"|^(?:and |so )?when (?:should|do|would) i (?:be )?(?:worried|worry|worrying)"
    r"(?: about (?:it|that|this))?(?: then| though)?$"
    r"|^(?:and |so )?when (?:should|do) i (?:start|need) (?:to )?(?:be )?worry(?:ing)?$"
    # "is that worrying" is the same ask in the other order. It is not a fact question this
    # composer may rule on with a yes or a no, though: over a child with a temperature the
    # knowledge base has the answer ("ring 111 if ..."), and a verdict pool took that turn away
    # from it. So it is here only to be read for the answer's own condition, and with no
    # condition in hand it stands aside.
    r"|^(?:and |so )?is (?:that|it|this) (?:worrying|worrisome|a worry)(?: then| though)?$"
    # "do i need to worry" and "do i need to be worried about that" are the same ask again, and
    # an unfinished sentence is how it arrives: the boiler bangs, the person says "do i need to
    # worry", and the search hedge is the one answer that helps nobody. The adverb goes in the
    # middle of it when the person is asking twice - "do i really need to worry", "do i actually
    # have to worry about it" - and the arm did not allow one, so the reinforcement that makes it
    # the doubt fell to the floor: a burnt hand answered "yes, get it looked at" was followed by
    # "do i actually need to worry" and got "that's beyond what I know well, a search should sort
    # you out", which is the search hedge over an answer that had already given it.
    r"|^(?:and |so )?(?:do|will|should|would) i (?:really |actually |honestly )?"
    r"(?:need|have) to (?:be )?worr(?:y|ied)"
    r"(?: about (?:it|that|this))?(?: then| though)?$"
    r"|^(?:and |so )?(?:is|was) (?:that|it|this)(?: (?:going to|gonna))? (?:get worse|"
    r"getting worse|spread|serious)$"
    r"|^(?:and |so )?(?:does|do|did) (?:that|this|it) matter(?: then| though)?$"
    # The copula is the word people drop or mangle when they type in a hurry: "s that ok", "iz
    # that ok", "that ok?". The ask is the same one, and the composer stood aside for it, so the
    # fallback echoed the line back - "Got it - iz that ok." - which says nothing to anybody.
    r"|^(?:and |so )?(?:iz |is |s |z )?(?:that|it|this) "
    r"(?:ok|okay|fine|alright|bad|normal|serious)(?: then| though| or not)?$"
    # "is that just age" is the doubt an older relative's answer gets more often than any
    # other phrasing: after an answer about a parent forgetting words the bot punted ("That's
    # beyond what I know well, sorry. Searching for it..."), which is the one thing a worried
    # daughter cannot use, and "is that just a phase" is the same question about a child. None of
    # the pools below can answer either - the honest answer starts "often, and the change is the
    # part to watch" - so the form has its own reading (AGE_LINES).
    r"|^(?:and |so |or )?(?:is|was) (?:that|it|this) (?:just|only) (?:old age|age|a phase|a stage|"
    r"the age|his age|her age|their age|tiredness|the tiredness)\??$"
    r"|^(?:and |so )?is (?:that|it|this) (?:a|much of a) (?:problem|worry|issue)(?: then| though)?$"
    # "is it bad for me" is the same question asked with the person in it. The subject it names
    # is the speaker, who is the one the last answer was for, so it is not "is that bad for the
    # baby" - a line about somebody else, which only the knowledge base can answer. "harmful",
    # "dangerous" and "will it hurt me" are the same ask in other words, and a person asking
    # them after "the mould on the soil" wants the verdict, not the paragraph again.
    r"|^(?:and |so )?(?:is|was|would|will|can|could) (?:that|this|it) (?:be )?"
    r"(?:bad|harmful|dangerous|unsafe|alright|ok|okay) for (?:me|us)(?: then| though)?$"
    r"|^(?:and |so )?(?:is|was|would|will|can|could) (?:that|this|it) (?:be )?"
    r"(?:harmful|dangerous|unsafe)(?: then| though)?$"
    r"|^(?:and |so )?(?:will|would|could) (?:that|this|it) hurt (?:me|us)(?: then| though)?$"
    r"|^(?:and |so )?(?:does|do|did|will) (?:that|this|it) (?:hurt|harmed|harm|make me ill"
    r"|make me sick)(?: then| though)?$"
    # A doubt about the person themselves, after a line about how they are: "am i ok", "am i
    # going mad". It names nothing at all, so no reading of a subject finds it and it used to
    # reach chat's sign-off - "Glad to hear it." to somebody who had just said they feel low.
    r"|^(?:and |so )?(?:am|was) i (?:ok|okay|alright|all right|normal|going mad|going crazy|"
    r"losing it|losing my mind)(?: then| though)?$"
    # "do i need to worry" is the doubt about the person themselves with the need in it: "am i
    # overreacting" and "should i worry" both have a shape in the composer's fallback, and this
    # one has none, so it walked past every pool below to the floor's care line - "Get it seen
    # today - you'll know either way" over an answer that had said ring 999 straight away.
    r"|^(?:and |so )?(?:do|would|will) i (?:really |actually )?(?:need|have) to (?:be )?"
    r"worr(?:y|ied)(?: about (?:it|that|this))?(?: then| though)?$"
    r"|^(?:and |so )?(?:should|do) i need to worry(?: then| though)?$"
)
# The reassuring words this composer learned to read after the ones below: they say how many
# people it happens to rather than how it ends ("it is common at four", "fix it for most people
# who snore"). They are kept apart because they are the weakest reading of the ordinary - an
# answer that says both "common" and "see a GP if it is one-sided" has named the half that
# matters, and the weakest reading must not talk over it.
HOW_MANY_PEOPLE = ("common", "for most people", "for most adults", "for most children",
                   "for most babies", "usual for", "is usual")

# What a reply that already answered the question sounds like. The reassuring words are the
# ones the knowledge base uses for the ordinary cause; the care words are the ones it uses when
# the point of the answer is that somebody else should look at it. "usually" is here on purpose:
# in these answers it introduces the ordinary case ("usually air or a pump"), not a hedge.
# The half of REASSURE that denies rather than describes: "it usually means a ligament" names the
# ordinary cause, while "most of these are not serious" answers the question asked. A denial in
# the opening settles the turn even when a later sentence lists what to get checked.
DENIES = ("harmless", "nothing to worry", "not serious", "nothing serious", "no need to",
          "nothing to be")
# The answer's own word for "this cannot hurt you". It is the one reassurance a fix above it
# does not take over: "the mould is harmless" answers "is it bad for me" and "scrape it off" does
# not, so an answer that says it keeps the ordinary pool whatever else it tells the person to do.
HARMLESS = ("harmless", "not serious", "nothing serious", "nothing to worry", "nothing to be",
            "no need to", "needs nothing doing", "does not need")
# A word that calls the thing itself normal, as against one that only says what usually happens.
# "Waking in the night is normal - sleep runs in cycles ... The fix is what you do in those
# minutes" has answered the doubt in its own first clause, so the pool that takes the answer's
# word for it is the one to give ("That one is the ordinary kind, so no"); the job in its second
# half does not change that. "Banging or rumbling when the heating starts is usually air ... bleed
# the radiators" has called nothing normal - it said what usually causes it - so there the job is
# the whole verdict. Main pins the first reading (`test_a_bare_ask_with_no_condition_still_gets_
# the_old_reading`), and the second is the one snappy-net asked for.
SAYS_NORMAL = ("normal", "nothing to worry", "not serious", "nothing serious", "nothing to be",
               "no need to", "harmless")
REASSURE = ("harmless", "nothing to worry", "not serious", "nothing serious", "usually",
            "normal", "no need to", "should settle", "usually settles", "will settle",
            "goes away", "just air", "nothing to be",
            # The ordinary kind is often said as an outcome rather than as a verdict: "Most back
            # pain is muscular and settles in two to six weeks", "it usually clears up by itself".
            # A word that only ever names an ending the answer expects is the same reading, and a
            # bare "is that bad" after it was being left with no verdict at all.
            "settles", "settle down", "clears up", "clears by itself", "goes by itself",
            "gets better on its own", "heals on its own", "resolves on its own",
            "does the job on its own", "is muscular",
            # The ordinary kind is also said as how many people it happens to: "It is common at
            # four and still common at nine" ("my son is 6 and he still wets the bed" / "is it
            # normal"), "fix it for most people who snore", "most children say short sentences by
            # three". Every other word in those answers was a cause and a check, so the pooling
            # came back as the search hedge. A danger in the answer is read before this, and a
            # stop is read before it too, so "common, and call 999 if" still lands on the call.
            "is common", "common", "common in", "common at", "common for", "quite common",
            "for most people", "for most adults", "for most children", "for most babies",
            "usual for", "is usual")
CARE = ("get it checked", "get checked", "get it looked at", "get it seen", "see a doctor",
        "see your gp", "ring 111", "call 111", "999", "a&e", "get someone in",
        "get an engineer", "get a heating engineer", "call an engineer", "engineer out",
        "call out", "straight away", "as soon as you can", "urgent", "needs an engineer",
        "is an engineer's job", "stop using it", "stop and", "unplug", "turn it off",
        "switch it off", "turn the water off", "stop the cycle", "leave it off",
        # A vet is the same kind of referral as a GP, and a pet answer says it in its own words:
        # "can my dog eat grapes?" / "is that bad" was answered "Alright then - good luck with
        # it" because none of the words above appear in "Ring your vet today".
        "ring your vet", "ring the vet", "call your vet", "call the vet", "see a vet",
        "see your vet", "get to the vet", "vet today", "vet straight away", "ask your vet",
        "your vet will want", "phone the vet", "phone your vet",
        # A referral is a referral however the answer words it, and these are the ways the
        # knowledge base and the greeting line say it: "worth a GP visit whatever the age",
        # "worth a hearing test first", "ask your health visitor or GP for a referral", "your
        # health visitor or the 111 line will talk it through with you today".
        # "worth a gp" is deliberately not here: it is the declarative way of naming an
        # appointment ("Pins and needles ... is worth a GP visit"), which is a warning about
        # another symptom rather than a referral now, and it is read as one in GO_FROM where the
        # plainness of the go matters.
        "gp visit", "worth a hearing test", "a referral", "for a referral",
        "health visitor", "111 line", "worth seeing", "worth getting looked at",
        # Main's side of the same reading (#4120): the article and the possessive are both ways
        # of saying where the person is sent, and the clinic names that go with them.
        "see a gp", "see the gp", "ring the gp", "phone the gp", "see a nurse",
        "ring the surgery", "call the surgery", "phone the surgery",
        "walk-in centre", "minor injuries", "out of hours", "urgent care",
        # The same referral said as the service rather than as the call: "Your health visitor or
        # the 111 line will talk it through with you today" names who to speak to without a verb
        # in front of it, and that answer is a "yes, this wants someone" for a verdict ask.
        "111 line", "nhs 111", "111 will", "health visitor", "out of hours service",
        "urgent treatment centre", "ask your midwife", "ring your midwife",
        # ... and the same thing said as a visit: "so it is worth a GP visit whatever the age".
        "worth a gp visit", "gp visit", "gp appointment", "doctor's appointment")
# A condition in front of the care words makes them advice for later, not a verdict now:
# "if it keeps dropping, there's a leak ... get a heating engineer out".
CONDITIONAL = re.compile(r"\b(?:if|unless|once|when) \w+[^.]{0,80}$")
# The same condition said after the cue: "see a GP if the arm is weak or numb".
CONDITIONAL_AFTER = re.compile(r"\b(?:if|unless|once|when|whenever)\b")
# A thread that has already said the worst thing in it is not short of a detail, and nothing in
# it is a thing to be weighed: "my dad has cancer" then "is that bad" is somebody checking
# whether the weight of it is allowed. The doubt path used to send that to the acknowledgement
# floor - "Alright then - good luck with it." - a diagnosis heard and answered like a lunch. The
# line gives no verdict, asks for nothing and puts nothing on a scale.
HARD_NEWS_LINES = (
    "There is no verdict to give on that one - some things are just hard, and that is not a "
    "judgement on you.",
    "I would not put that on a scale. What happened is heavy enough without working out where "
    "it sits.",
    "That is not something with a good or bad answer. It is a hard thing to carry, and you are "
    "allowed to just feel it.",
)
# The worst things a person brings here, as they write them. Read on the person's own line and
# not on the bot's, because a condolence is written to say how it feels rather than what
# happened ("I'm really sorry" says nothing about a father). Only the things that make a doubt
# the wrong question: a diagnosis of coeliac disease or ADHD is a thing to learn about rather
# than a hard thing to carry, and it is answered as it was.
HARD_NEWS = re.compile(
    r"\b(?:died|dying|death|passed away|funeral|buried|cremated|hospice|"
    r"cancer|leuka?emia|lymphoma|myeloma|tumou?r|terminal|palliative|chemo|radiotherapy|"
    r"miscarriage|miscarried|stillborn|"
    r"dementia|alzheimers|motor neurone|multiple sclerosis|parkinsons|copd|"
    r"kidney failure|heart failure|liver failure|"
    r"stroke|heart attack|sepsis|"
    r"given months|not going to make it)\b", re.I)
# What an answer that heard the news sounds like. The doubt only belongs to the loss when the
# answer above was about the loss: "how do i stop my phone battery dying" / "is that bad" is not
# a bereavement, and "my plant is dying" / "is that bad" is not one either - both are how-to
# answers, and neither of them says sorry.
SYMPATHY = re.compile(
    r"\b(?:i'm sorry|im sorry|so sorry|really sorry|sorry to hear|sorry for your loss|"
    r"sorry about (?:your|the)|sounds rough|that sounds rough|a real loss|how awful|that's awful|"
    r"that is awful|how sad|that's sad|that is sad|"
    # A reply that meets the news without the word "sorry" in it still met the news: "my dad had
    # a stroke" is answered "Frightening to watch, and the first day or two is tests rather than
    # answers", and "my grandad had a heart attack" with "Ugh, that's a lot to carry". Both are
    # the bot hearing a hard thing, which is what this half of the test asks.
    r"frightening|scary|a lot to carry|no wonder|that's heavy|that is heavy|"
    r"nothing about that is a fault|hardest days?)\b", re.I)
# A referral that names when to act is not waiting on a condition, and an "if" later in its own
# sentence is measuring something rather than deciding whether to go: "Ring the vet today if it
# has been more than 24 hours, and straight away for a puppy under six months" is the threshold
# that says go now. Reading that later "if" as a fence made the referral conditional twice over,
# and a dog that will not eat was answered "that one is the ordinary kind, so no" one turn after
# an answer that said ring the vet today.
# The words that turn a condition into a degree of the same errand ("and sooner if ..."): the
# answer has already said go, and this says go at once.
COMPARATIVE = re.compile(r"\b(?:sooner|earlier|quicker|faster|more so|especially|particularly|"
                         r"above all)\b", re.I)
URGENT_TIME = re.compile(r"\b(?:today|tonight|now|straight away|right away|immediately|"
                         r"as soon as|first thing|urgent(?:ly)?|within \d+)\b")
# A person's week is not a body either. "my mum is 79 and lives on her own" is answered "Do the
# inviting yourself, and make it the same thing each week ... if they seem low for weeks rather than
# lonely, ask them plainly how they are and help them see a GP", and "is that ok" came back "Yes,
# that one wants a proper look rather than watching it. Get it looked at properly" - the pools read
# the answer's fenced care for the harder case as a referral for a symptom, and offered a woman on
# her own a doctor's look for her week (#routing 77612). The verdict on a person's situation is
# about the answer's own two halves: do the simple step now, and the fenced half is when to act.
# A body in the line is the health cards' subject, not this reading's: "my baby is not feeding",
# "my son has a temperature of 39" and "my child has a rash" all keep the pools above.
A_SYMPTOM_WORD = re.compile(
    r"\b(?:skin|rash|itch|itching|eyes?|ears?|throat|chest|stomach|belly|temperature|fever|"
    r"vomit|vomiting|sick|diarrhoea|diarrhea|feeding|feeding|breath|breathing|breathless|cough|"
    r"poo|wee|blood|pain|hurts?|hurting|swelling|swollen|knee|joint|joints|mouth|teeth|tooth|"
    r"napp(?:y|ies)|nappy|wet(?:s|ting)? the bed|constipated|constipation|gums?)\b", re.I)
A_PERSON_THEY_KNOW = re.compile(
    r"\b(?:mums?|moms?|mother|father|dads?|son|daughter|kids?|child(?:ren)?|wife|husband|"
    r"partner|girlfriend|boyfriend|friend|friends|neighbours?|grans?|granny|nan|nana|"
    r"grandma|granddad|grandad|grandpa|sister|brother|aunt|uncle|cousin|bab(?:y|ies)|"
    r"in[- ]laws?|mother in law|father in law)\b", re.I)
# What makes it the person's days rather than their health: contact, company and quiet, which is
# the subject of the friendship and loneliness answers. A body in the line stands the reading down
# ("my baby is not feeding", "my son has a temperature of 39"), and so does a line about nothing
# but sleep or food - those are the health cards, and the pools above are right for them.
A_RELATION_TROUBLE = re.compile(
    r"\b(?:lonely|loneliness|company|visit|visits|visiting|ring|rings|rang|call|calls|called|"
    r"speak|speaks|spoke|spoken|talk|talks|talked|talking|quiet|withdrawn|alone|"
    r"on (?:his|her|their|its) own|lives? on (?:his|her|their) own|"
    r"arguments?|arguing|row|rows|falling out|fallen out|ignores?|ignoring|"
    r"does not listen|doesnt listen|wont listen|wont say|wont go out|does not go out|"
    r"trust|trusts|jealous|suspicious|accuses?|accusing|controlling|keeps? checking|"
    r"checking (?:my|his|her|their)|"
    r"doesnt go out|birthday|anniversary|seen (?:him|her|them)|see (?:him|her|them))\b", re.I)
PERSON_ORDINARY = (
    "There is nothing there to watch for going wrong: it is an ordinary stretch, and the answer's "
    "own first step is what moves it. Do that for a few weeks - if it is the same after that, say "
    "it to them plainly rather than sitting on it.",
    "Nothing in that is a fault on either side. The small thing in the answer, done consistently, "
    "is what changes it, and if nothing has changed after a few weeks that is the point to say "
    "something out loud.",
)
PERSON_CALL = (
    "Yes - take up the first half of what I said now, and the second half is what to act on: if it "
    "is still like that after a few weeks, do the part about talking to somebody properly.",
    "Yes, that one is worth acting on rather than watching. Start with the simple step in the "
    "answer, and if nothing has moved in a few weeks, take the next step it names.",
)


NO_LINES = (
    "Nothing in that sounded like a warning sign. What would change it is the thing itself "
    "changing — getting worse, or not settling — and then it's worth getting looked at.",
    "That one is the ordinary kind, so no. Watch it rather than worry about it: if it's still "
    "the same in a week or two, or it gets worse, get someone to look at it.",
    "No — the part you asked about is the harmless kind. What to keep an eye on is change "
    "rather than the thing itself.",
)
# An answer can do both: "It is common at four and still common at nine ... so it is worth a GP
# visit whatever the age". The ordinary word alone would have the bot say "nothing to act on
# now" against the answer's own advice, so this shape gets a line that says both halves.
BOTH_LINES = (
    "It's the common kind rather than a warning sign — and the check is still worth doing.",
    "Common enough, so no panic. Getting it looked at is worth doing all the same: that is what "
    "catches the less usual ones.",
    "Not a warning sign on its own, no. Common enough that mentioning it is enough rather than "
    "rushing — do that, and say what they tell you.",
)
DO_LINES = (
    "It's a job rather than a danger. Do it and see whether it holds — if it comes back, that's "
    "the point where it stops being a DIY thing.",
    "Not bad in itself, but not something to leave alone either. Do the job properly, and if it "
    "comes back after that, get someone in.",
    "Worth doing rather than worrying about. Sort it out; if it keeps coming back, that's when "
    "it's somebody else's job.",
)
# A follow-up asking whether the step just given is the fix: "and does that fix the pressure
# too", "will that sort it out", "does that cure it". The step is in the answer the person was
# given a turn ago, so the honest reply is whether doing it fixes the thing and how they will
# know - not the same paragraph again. The answers entry hands back a slice of its own paragraph
# word for word on this ask ("my boiler keeps losing pressure" then "and does that fix the
# pressure too"), which is the same answer twice with nothing said about the question it asked.
# The shape is what is read, never the topic: any step, any subject.
FIX_ASKED_LINES = (
    "Give it a day or two and see whether it holds. If the same thing comes back, the step was "
    "not the fix and it wants a proper look.",
    "Do it and give it a few days. Coming back after that is the sign it is not something the "
    "step sorts out on its own.",
    "Try it and watch what happens next. If it stays away, that was the whole of it; if it "
    "does not, the thing behind it needs seeing to.",
)
# ...and the same question about a step whose answer arrives at once. A blocked bath trap is
# answered by running the tap: "do it and give it a few days" is wrong advice for it, because the
# person knows in a minute. So the wait is read off the step the answer gave, and a step that names
# no wait gets the verdict now. The test in the line is the one the person already used to decide
# the thing was broken.
FIX_ASKED_NOW_LINES = (
    "Do it now and check it the way you checked before. If nothing has changed at all, that step "
    "was not the fix and the next thing to look at is further in.",
    "Try it straight away. If it does what it should, that was the fix; if it behaves the same, "
    "the step was not the answer and something else is doing it.",
    "Do it and look again straight after. Unchanged means the step was not the fix, rather than "
    "that it needs longer.",
)
# The wait a step can name for itself: "leave it overnight", "check after a week", "within a few
# days". Minutes are not a wait - "you will know in a minute" is the step answering at once.
A_WAIT_IN_THE_STEP = re.compile(
    r"\b(?:after|within|for|over|in|another)\s+(?:a|an|the|two|three|four|five|six|few|couple|"
    r"several|\d+)\s+(?:day|days|week|weeks|night|nights|month|months)\b"
    r"|\bovernight\b|\bnext day\b|\bthe following (?:day|week)\b"
    r"|\bleave it (?:to|for)\b", re.I)
# The ask itself: a modal or an "is/does", a pointing word, and a word for fixing. Kept short,
# because a long line brings its own subject and is a new question rather than a question about
# the answer just given.
_ASKS_ABOUT_A_STEP = re.compile(
    r"\b(?:does|do|will|would|should|can|could|is|was)\b(?:\s+\w+){0,3}\s+(?:that|this|it)\b", re.I)
# The asks that want the step itself rather than a word on whether one will work: "how do i fix
# it", "what should i do about it". They are the same words as the follow-up and the opposite
# question, which is why they are read first.
_ASKS_FOR_THE_STEP = re.compile(r"^\s*(?:how|what|where|when|which|who|why)\b", re.I)
_A_FIX_WORD = re.compile(
    r"\b(?:fix|fixes|fixed|sort|sorts|sorted|solve|solves|cure|cures|work|works|help|enough|"
    r"stop|stops|clear|clears|do the trick|make a difference)\b", re.I)


# Answers that are not a job the person tries and watches for a few days: a body, a pregnancy, a
# baby, an animal, or somebody to ring. "my baby is not feeding" is answered with "a baby under
# three months who stops feeding needs looking at today", and "does that fix it" was told to
# "give it a few days", which is the one thing that answer must never say. The knowledge base
# already says which module an answer came from (`last_answer["domain"]`), so the reading is the
# module and not a phrase: a boiler in a chat about a baby is still a boiler, because the boiler
# answer came from `home`. The words are the fallback for an answer with no module behind it, and
# they are kept to the ones no DIY or cooking answer uses - "bleed" is a radiator here.
NOT_A_STEP_TO_WATCH = frozenset((
    "health", "pregnancy", "babyfood", "body", "caring", "complaints", "crisis_replies",
    "pharmacy", "pets", "animals", "family", "friends", "sleep",
))
NOT_A_STEP_TO_WATCH_WORDS = re.compile(
    r"\b(?:baby|babies|infant|newborn|toddler|pregnan\w*|napp(?:y|ies)|rash|fever|"
    r"vomit\w*|diarr\w*|breathless|symptom\w*|seizure|dehydrat\w*|allerg\w*|asthma|"
    r"inhaler|epipen|insulin|diabet\w*|medicin\w*|medication|antibiotic\w*|paracetamol|"
    r"ibuprofen|painkiller\w*|gp|gps|doctor|doctors|nurse|midwife|pharmac\w*|hospital|"
    r"a&e|ambulance|111|999|911|dentist|vet)\b", re.I)


def _a_job_somewhere(reply):
    """True when any clause of a reply is an instruction, not only the first one.

    `opens_on_a_job` reads the opening because a bare "what do i do" wants the reply that starts
    with the job. The step a follow-up points at is not always the opening one: the boiler answer
    that ends "..." / "ok and what about the radiators, they're cold at the top" answers with
    "Radiators that are hot at the bottom and cold at the top have air in them: open the bleed
    valve at the top with a radiator key ...", which opens on a fact and carries its job after
    the colon. "and does that fix the pressure too" after it still means the bleeding, so the
    job has to be read wherever it is in the line.
    """
    flat = _flat(reply)
    if not flat:
        return False
    for clause in re.split(r"[:;.!?]|,?\s+and\s+", flat):
        words = _WORD.findall(clause.strip(" ,-"))
        if not words or words[0] not in IMPERATIVES:
            continue
        if len(words) > 1 and words[1] in ("me", "us"):
            continue
        if len(words) > 1 and words[1] in _AFTER_A_NOUN:
            continue
        return True
    return False


def the_fix_asked(clean, memory):
    """A line for "and does that fix the pressure too", or "" when the line is not that ask.

    Read by the chat module: the step was given a turn ago and the question is whether doing it
    is the fix. Two things have to hold, and each of them is a way of leaving the turn alone:

    * the last thing the bot said opens on a job (`opens_on_a_job`) - there is a step for "that"
      to point at, and the person has already read it;
    * the line is short and asks about fixing - a long line brings its own subject, and a line
      that asks what to do next, how long it takes or why it happens is another question that
      the answers entry or the verdict line answers better.
    """
    flat = _flat(clean)
    if not flat:
        return ""
    words = flat.split()
    if len(words) > 10:
        return ""
    if not _ASKS_ABOUT_A_STEP.search(flat) or not _A_FIX_WORD.search(flat):
        return ""
    if _ASKS_FOR_THE_STEP.match(flat):
        # "how do i fix it" asks for the step and has not been given one yet, so the answer is the
        # entry's own ("Pull the hair and soap out of the trap"), not a line about watching one.
        return ""
    last = _last_reply(memory)
    if not last or not (opens_on_a_job(last) or _a_job_somewhere(last)):
        return ""
    if str((memory.get("last_answer") or {}).get("domain") or "").lower() in NOT_A_STEP_TO_WATCH:
        return ""
    if NOT_A_STEP_TO_WATCH_WORDS.search(last):
        # An answer about a person's body, an animal or a trade is not a step the person tries
        # and watches for a few days. "my baby is not feeding" is answered with "a baby under
        # three months who stops feeding needs looking at today", and "does that fix it" was told
        # to "give it a few days", which is the one thing that answer must never say. The guard
        # reads the answer, not the chat, so a boiler in a chat about a baby is still a boiler.
        return ""
    if A_WAIT_IN_THE_STEP.search(last):
        # The step said how long it takes to know, so the line about watching it holds.
        return _say(FIX_ASKED_LINES, memory, flat)
    # No wait in the step: the answer comes when they try it, so the line asks them to look
    # straight away. "Give it a day or two" over a blocked bath trap is advice that cannot be
    # followed - the tap tells them in a minute.
    return _say(FIX_ASKED_NOW_LINES, memory, flat)


# An answer whose care is fenced by an "if" is not a warning about the thing itself: "my arm
# aches after gardening" ends "See a GP if the arm is weak or numb", and a bare "is that bad"
# asks about the ache. The honest verdict is the answer's own line: this is ordinary on its own,
# and the condition it named is the thing to act on.
CONDITION_LINES = (
    "Not the thing itself, no. It would stop being ordinary if {when} — that is the point to "
    "act on.",
    "Ordinary on its own, yes. It stops being ordinary if {when}, so that is what to watch.",
    "Nothing in that is a warning by itself. It becomes one if {when}: that is when it wants "
    "someone.",
)
# And when the condition the answer named is the thing the person just described, there is no
# fence left to quote: "my baby is not feeding" / "is that bad" was told "Ordinary on its own,
# yes. It stops being ordinary if it stops feeding" by an answer that had just said to ring 111
# now. The answer's own threshold is met, so the verdict is the answer's next step, not a
# reassurance about a condition the person has already met.
# The floor under a death, when the line the ask follows is a condolence rather than an answer.
# It claims nothing about what the person is carrying, and it does not ask them to describe it.
GRIEF_FLOOR_LINES = (
    "Not something to be graded bad or not - it is a loss, and it deserves the room it takes. Be "
    "gentle with yourself, and let whoever is around you know how you are.",
    "That is not a thing to call bad, and not a thing to carry on your own. Take the help that is "
    "offered, and tell someone close how today actually went.",
    "Nothing about that is a fault in you. Give it the time it takes, and lean on the person who "
    "asks how you are.",
)
MET_CONDITION_LINES = (
    "Then you are already at the point it named, so that is the bit to act on rather than the bit "
    "to watch. Get it looked at, and say what you told me here when you do.",
    "That is the thing that answer said to act on, and it is what you are describing. Get it seen "
    "to rather than sitting with it.",
    "So it is past the watching stage: the answer's own next step is the one for now. Get that "
    "started today.",
)
# The two arms of BARE that are this ask, kept here as well so the pool below can be chosen for
# them and for nothing else (an "is that bad" still gets its verdict).
WHEN_ASK = re.compile(
    r"^(?:and |so )?when (?:should|do|would) i (?:be )?(?:worried|worry|worrying)"
    r"(?: about (?:it|that|this))?(?: then| though)?$"
    r"|^(?:and |so )?when (?:should|do) i (?:start|need) (?:to )?(?:be )?worry(?:ing)?$")
# The same ask the other way round. It is read for the answer's own condition and nothing else:
# a bare "is that worrying" over a card with no condition in it is the knowledge base's (a child
# with a temperature has a line about 111, and a verdict pool has none).
WORRYING_ASK = re.compile(
    r"^(?:and |so )?is (?:that|it|this) (?:worrying|worrisome|a worry)(?: then| though)?$")
# "when should i worry" is not a yes/no doubt: it asks for the condition, so the answer is the
# condition the card just wrote out, not a verdict on the thing. Over "my mum keeps forgetting
# things" the yes/no pools said "Yes, that one wants a proper look rather than watching it",
# which answers a question nobody asked, while the card had already listed what counts.
WHEN_LINES = (
    "This is the line: {when}. Short of that it is the ordinary kind, and worth watching rather "
    "than acting on.",
    "What makes it somebody else's job: {when}. Until then it is a watch-and-see.",
    "The point to act on is this: {when}. Before that it is the ordinary thing, so keep an eye on "
    "it rather than acting on it.",
)
# The same ask over a card that named its call and its reason in the other order: "See a GP the
# same day for spreading redness or pus; a red streak running up the arm or leg, a fever, or
# feeling shivery and ill is 111 today". The {when} already carries each sign's own call, so
# these lines only have to say where the waiting stops.
WHEN_CALL_LINES = (
    "The line to act on: {when}. Short of that it is the watching stage, and the answer's own "
    "steps are the plan.",
    "This is where it stops being a wait-and-see: {when}. Before that, do what the answer said "
    "and keep an eye on it.",
    "What sends you to someone: {when}. Under that line the answer's steps are the whole of it.",
)
# Many cards write the condition as a list with a call at the end of it rather than as an "if":
# "A leg he won't put weight on, a swelling, or a limp that is no better after two days needs the
# vet", "asking the same question within minutes, getting lost on a familiar route, or forgetting
# something they have always done are not, and want a GP appointment". A "when should i worry"
# asks for exactly that list, and every reader above looks for a fence, so it found nothing and
# the answer was a flat "yes, get it looked at" over a card that had written the line out.
NEEDS_A_CALL = re.compile(
    r"(?P<list>[^.;:]*?)\s*(?:,\s*and\s+|\s+and\s+)?(?:needs?|wants?|want|means)\s+"
    r"(?:the\s+|your\s+|a\s+)?"
    r"(?:vet|gp|doctor|dentist|optician|pharmacist|physio|111|a&e|engineer|plumber|electrician)\b",
    re.I)
# The "are not, and" that joins the list to its call is the card's grammar, not part of the list.
_LIST_JOIN = re.compile(r"\b(?:are|is|was|were)\s+not\s*,?\s*(?:and)?\s*$", re.I)


def _the_list_before_the_call(said):
    """"A leg he won't put weight on, a swelling, or ..." - the answer's own list of signs."""
    best = ""
    for m in NEEDS_A_CALL.finditer(str(said or "")):
        part = _LIST_JOIN.sub("", m.group("list").strip(" ,;:-"))
        part = part.strip(" ,;:-")
        words = part.split()
        if 3 <= len(words) <= 24 and len(part) > len(best):
            best = part
    # "A leg he won't put weight on, a swelling" is quoted mid-sentence after a colon, so the
    # card's own capital goes with the full stop it was written behind.
    if best and best.split()[0] in ("A", "An", "The"):
        best = best[0].lower() + best[1:]
    return best


# The other order again: the call first and what it is for after it. "Ring 111 if you cannot
# breathe" is the shape every reader above knows, but "See a GP the same day for spreading
# redness or pus" is not an "if" at all, and it is how a cut and a cough write their line. Over
# both, a person asking "when should i worry" was told nothing about the answer in hand: "my cut
# looks infected what should i do" / "when should i worry" went to the search hedge, over a card
# that had named a GP, 111 and the signs for each.
CALLS_FOR = re.compile(
    r"\b(?:see|ring|call|contact|speak to|go to|get)\s+(?:a |your |the )?"
    r"(?P<who>gp|doctor|practice nurse|nurse|111|999|a&e|vet|dentist|optician|pharmacist|"
    r"surgery|midwife|physio(?:therapist)?|urgent care|out of hours)"
    r"(?P<quick>\s+(?:the same day|today|straight away|now|first thing|as soon as you can|"
    r"within \w+ hours))?\s+for\s+(?P<list>[^.;:]+)",
    re.I)
# The same line with the sign in front and a number behind it: "a red streak running up the arm
# or leg, a fever, or feeling shivery and ill is 111 today".
IS_A_NUMBER = re.compile(
    r"(?P<when>[^.;:]+?)\s+(?:is|are)\s+(?P<who>111|999|a&e)\b"
    r"(?P<quick>\s+(?:today|now|the same day|that day|straight away))?",
    re.I)


def _the_call_and_its_reason(said):
    """The answer's own "see a GP for X" and "X is 111 today", said as one clause, or "".

    Only for the "when should i worry" ask, which wants the answer's condition and never a
    verdict on the thing. Two at most: a card listing more than two calls has written a
    paragraph, and half of a paragraph read back is worse than the pool.
    """
    found = []
    for m in CALLS_FOR.finditer(str(said or "")):
        sign = _no_hanging_end(m.group("list").strip(" ,;:-"))
        if not 2 <= len(sign.split()) <= 20:
            continue
        found.append((m.start(), sign, _the_person_for(m.group("who"), m.group("quick"))))
    for m in IS_A_NUMBER.finditer(str(said or "")):
        sign = _no_hanging_end(m.group("when").strip(" ,;:-"))
        if not 2 <= len(sign.split()) <= 20:
            continue
        found.append((m.start(), sign, _the_person_for(m.group("who"), m.group("quick"))))
    # In the card's own order, so the first two calls it makes are the two the line carries.
    said_signs = []
    for _, sign, who in sorted(found):
        if any(sign in other for other in said_signs):
            continue
        said_signs = [s for s in said_signs if s not in sign]
        said_signs.append("%s (%s)" % (sign, who) if who else sign)
        if len(said_signs) == 2:
            break
    if not said_signs:
        return ""
    # The second sign is a second line of the card, so the two are joined with a semicolon rather
    # than an "or": "spreading redness or pus (a GP the same day); a fever or feeling shivery
    # (111 today)" keeps each sign with the call it belongs to.
    clause = "; ".join(said_signs)
    return clause[0].lower() + clause[1:] if clause[:1].isupper() else clause


# The pool above says where the waiting stops, which is the wrong thing to say to somebody already
# past it: "there is a red streak up my arm / when should i worry" and "my cut has pus coming out
# of it / when should i worry" were told "Before that, do what the answer said and keep an eye on
# it", which puts them back under a line their own line has crossed. When the sign about to be
# quoted is worded in the person's own line, the reading that already exists for these chats (a
# proper look, the call is the thing to do now) is the one that answers.
_NOT_A_SIGN_WORD = frozenset((
    "about", "after", "again", "been", "before", "could", "doesnt", "from", "have", "into",
    "just", "like", "more", "much", "only", "over", "same", "should", "some", "than", "that",
    "their", "them", "then", "there", "these", "they", "thing", "this", "very", "want", "what",
    "when", "will", "with", "worried", "worry"))


def _the_sign_words(call):
    """The content words of the signs in the quoted call, without the calls themselves."""
    signs = re.sub(r"\([^)]*\)", " ", str(call or ""))
    return {w for w in re.findall(r"[a-z']+", signs.lower())
            if len(w) >= 3 and w not in _NOT_A_SIGN_WORD}


def _they_named_the_sign_themselves(call, memory):
    """True when the person's own line already says the sign the call is for."""
    words = _the_sign_words(call)
    if not words:
        return False
    said = _flat(_the_line_behind(memory) or "")
    return bool(words & set(re.findall(r"[a-z']+", said)))


def _the_person_for(who, quick):
    """"See a GP the same day" -> "a GP the same day"; "111 today" keeps its number."""
    trade = (who or "").strip().lower()
    if not trade:
        return ""
    # The card writes "a GP" and "A&E" and so does the line: a lowercase "gp" reads as a typo.
    trade = {"gp": "GP", "a&e": "A&E", "nhs": "NHS"}.get(trade, trade)
    if trade[0].isdigit() or trade in ("A&E", "NHS"):
        piece = trade
    elif trade in ("GP", "doctor", "practice nurse", "nurse", "surgery", "vet", "dentist",
                   "optician", "midwife", "physio", "physiotherapist"):
        piece = "your " + trade
    else:
        piece = "a " + trade
    hurry = re.sub(r"\s+", " ", str(quick or "")).strip(" ,")
    return (piece + " " + hurry).strip() if hurry else piece


# An answer that is a fix and no warning at all: "damp in the corner of my bedroom" gets the
# extractor fan and the window, and "is that bad" arrives. The answer never said "harmless" and
# never named anyone to ring, so the two pools above do not apply - but it also never said
# anything was dangerous, and that is a reading of the bot's own words rather than a claim about
# the world: nothing in the answer was a warning, and the answer's fix is the thing to do.
# The doubt path is for a person checking a thing that is wrong: "damp in the corner of my
# bedroom" then "is that bad". A plan and a how-to are not things that can be wrong - "im going
# to rome" then "is that ok" asked about the trip, "how do i cook rice" then "is that ok" asked
# about the method - and both were told "Everything in that answer is the ordinary job": a
# verdict on a fault nobody had raised. So the line has to report something, not announce one
# or ask for one.
# A plan is the person's own, so its subject is them in the first person. Without that the arm
# read a prediction about a fault as a plan: "the damp in my bedroom is going to get worse" then
# "is that bad" got "Alright then - good luck with it", and so did "my back is going to give out"
# and "my tooth is going to fall out", when the answer above each of them was the one that says
# what to watch.
A_PLAN = re.compile(
    r"\b(?:i'm|im|i am|we're|were|we are)\s+(?:going|off|flying|driving|sailing|heading|"
    r"travelling|traveling|moving|booking|booked|selling|buying|renting)\b"
    r"|\b(?:i|we)\s+(?:want|wanna|hope|plan|intend|need|'d like|would like)\s+to\b"
    r"|\b(?:i'm|im|i am|we're|were|we are)\s+(?:about to|planning to|thinking (?:of|about)|going to)\b")
# The other line that is not a fault: one that asks how to do something. Its "is that ok" is
# about the method, and the method in the answer is the bot's own, so the verdict is that it is
# the way the bot would do it - not "that is how it is normally handled", which answers a
# question about danger.
A_HOW_TO_ASK = re.compile(
    r"\b(?:how|where|when)\s+(?:do|should|can|could|would|shall)\s+(?:i|we)\b"
    r"|\bhow\s+(?:do|can|would)\s+(?:i|we)\s+(?:stop|get|fix|clean|keep|make|put|sort|"
    r"deal|go|use|set|apply)\b")
# "What should I cook tonight" then "is that ok" is asking whether the suggestion is fine, and
# the fault pools answer a different question ("Not on its own, no. That is how it is normally
# handled..."). A suggestion is the bot's own, so the warm acknowledgement is the honest reply.
A_DECISION_ASK = re.compile(
    r"\b(?:what|which)\s+(?:should|shall|do|would)\s+(?:i|we)\b"
    # "should i" on its own is a yes/no question about one thing, not a choice between two:
    # "should i get my mole checked" / "is that bad" was read as a choice and handed back
    # "Alright then - good luck with it", when the answer above was a referral and the doubt
    # has one answer. Only a line that names a second option is the choice this stands aside
    # for ("should i ring the shop or the maker first", "what should i cook tonight").
    r"|\b(?:should|shall)\s+(?:i|we)\b")
# An answer that opened by giving the yes it was asked for, with its condition on it ("Yes, if
# they want heat within about 20C of each other: put the hotter dish in first", "Yes, as long as
# the pan is deep enough"). The method is confirmed in the answer itself, so a bare "is that ok"
# on the next turn is the person checking that method and not asking for a verdict on a fault:
# read through the fault pools it was told "That answer is the usual handling of it rather than a
# warning about it", which is an answer to a question nobody asked (sleek-heather, #routing 75213).
SAID_YES = re.compile(
    r"\A\W*(?:yes|yep|yeah|yup|it does|that does|they can|it can|you can|both do)\b",
    re.IGNORECASE)


# "will that work" after a how-to is a doubt about the step, not a decision to weigh. The pool
# that judges a choice ("would that work" after "im thinking of getting a cat") was reading it
# too, and told a person who had just been given the way to bleed a radiator "Not a call I can
# make for you" - a refusal of a question the bot's own answer had answered.
METHOD_DOUBT = re.compile(
    r"^(?:and |so |but |ok |okay |well )*(?:will|would|does|do|did|can|could) "
    r"(?:that|this|it) (?:actually |really |even |still )?"
    r"(?:work|help|be enough|do the job|do it)(?: then| though)?$")

# "will that work" after a how-to is a doubt about the step, not a decision to weigh. The pool
# that judges a choice ("would that work" after "im thinking of getting a cat") was reading it
# too, and told a person who had just been given the way to bleed a radiator "Not a call I can
# make for you" - a refusal of a question the bot's own answer had answered.
METHOD_DOUBT = re.compile(
    r"^(?:and |so |but |ok |okay |well )*(?:will|would|does|do|did|can|could) "
    r"(?:that|this|it) (?:actually |really |even |still )?"
    r"(?:work|help|be enough|do the job|do it)(?: then| though)?$")
# The whole family, not five phrasings of it: the same check is asked as "would that be worth
# it", "does that actually work", "is that the right thing to do" and "shall i try that", and
# each of those was left to the card it was checking, which said itself again.
A_CHECK_ASK = re.compile(
    r"^(?:and |so |but |ok(?:ay)?[, ]+)?(?:do you think\s+)?"
    r"(?:will|would|does|do|did|should|shall|could|can|is|was)\s+(?:that|this|it|they|those)\s+"
    r"(?:actually |really |even )?(?:be\s+)?"
    r"(?:work|works|help|helps|fix it|fix that|do it|do the trick|do any good|"
    r"make a difference|sort it|be enough|enough|ok|okay|fine|right|worth it|worth doing|"
    r"worth a go|worth the money|the right thing|the right thing to do|the right way|"
    r"the done thing|the usual way)"
    r"(?: then| though| at all| for me| for us| for them| really)?\s*$"
    # the same check with the person as the subject: "shall i try that", "should i give it a go",
    # "do i do it that way"
    r"|^(?:and |so )?(?:shall|should|could|can|do)\s+i\s+(?:try|do|use|go with|give)\s+"
    r"(?:(?:that|this|it)\s+)?(?:a\s+)?(?:go|try|shot)"
    r"|^(?:and |so )?(?:shall|should|could|can|do)\s+i\s+(?:try|do|use|go with)\s+"
    r"(?:that|this|it)(?:\s+then)?\s*$"
    # the plain form, subject first: "that will work", "do you think that is enough"
    r"|^(?:and |so )?(?:do you think\s+)?(?:that|this|it)\s+(?:will|would|does|is|'s)?\s*"
    r"(?:be enough|enough|work|help|be worth it|be ok|be fine)\s*$"
    # and the version that names the question rather than the effect
    r"|^(?:and |so )?(?:is|was)\s+(?:that|this|it)\s+the\s+"
    r"(?:right|best|proper|usual|sensible|standard)\s+"
    r"(?:thing|way|way to do it|order|approach|method|call)(?:\s+to\s+do)?\s*$")

# The ask about whether the method does anything, rather than about whether it is the right one:
# "will that work" / "will that help" / "would that fix it" / "is that enough" / "do you think
# that is enough". Kept apart from BARE because the thing being checked is the answer's effect,
# not the fault in the thing, and apart from A_HOW_TO_ASK because the how-to ask comes before it.
# A line that says the person is still weighing a thing up rather than asking how to do it: the
# answer to it is the bot's view of the choice, and a check on that answer is not a check on a
# method.
A_THINKING_ABOUT = re.compile(r"\bthinking (?:about|of)\b|\bwondering\b|\bconsidering\b|"
                              r"\bnot sure (?:if|whether)\b")

# Said back to a person checking the method they have just been given.
# The lines do not answer "is that bad" with a yes in front of them, because the same pool answers
# "is that ok" and "is that bad": "It is, yes" after "is that bad" reads as a verdict that the
# thing is bad, and the method is the only thing either ask is about.
METHOD_OK_LINES = (
    "Nothing there is a problem - that is how I would do it too.",
    "That is how I would go about it, and there is nothing in it to worry about.",
    "Done that way, it needs no one else: that is the method I would use.",
)
# A check on the effect of the method just given: "will that work", "will that help", "is that
# enough". It is the same ask as "is that ok" about a method, said about whether the method does
# anything, and the answer above is the bot's own method, so the reading is the answer's own: it
# is the standard thing to try, and what the person does next is watch it. Told instead "Not a
# call I can make for you. Say what you would lose either way" - the line for a choice the bot
# has no view on - a person asking about advice the bot had just given was handed the question
# back, and told "Alright then - good luck with it" the conversation was closed on them.
# The two pools are split by whether the answer named something to watch for, for the same reason
# the method pool is: "will that help" over the back-pain answer must not drop the line about
# getting it looked at if it is no better.
CHECK_WORKS_LINES = (
    "It is the right thing to try first, and it works for most people. Give it a week or two and "
    "tell me how it goes.",
    "Yes - that is the standard way, so it is the one I would count on to start with. What changes "
    "after you have tried it is what tells us the next step.",
    "That is the usual way to go at it and it tends to do the job. If nothing has moved in a "
    "week, say so and we will go a step further.",
    "That is what I would do myself, so yes - it is worth a run. A fortnight of it is usually "
    "enough to know.",
)
# The check after a method with no length to it: "how do i cook rice" / "will that work". Rice is
# cooked tonight, so "if nothing has moved in a week" is not true of it - the same sentence would
# land on a stain, a blocked drain or a flat tyre. This pool answers the check and says nothing
# about how long the thing is meant to take, because the answer above gave it no time at all.
CHECK_ONCE_LINES = (
    "That is the standard way of doing it and it works - tell me how it goes and we will take it "
    "from there.",
    "Yes, that is how it is done. Do it that way and tell me how you get on.",
    "That way of doing it is the right one, so go ahead - tell me if it does not do the trick.",
)
# The answer above says how long the thing takes to show ("give it a week", "two to six weeks",
# "if it has gone on for weeks"), so a check on it can talk about that length. A method with no
# length in it is a one-off job, and the pool above is the one for it.
# Only a length a week of trying it can be measured against counts: days, a few weeks, a
# fortnight. "Ten weeks" was a length too, and the check over it said "give it a week or two and
# tell me how it goes" about a passport application (snappy-net, #8488) - the length was read out
# of the answer and then a different one was invented over it. A month or a year is the same
# fault, so the numbers stop at four and the long units are out: the answer with ten weeks in it
# is a one-off job as far as this pool is concerned, and the pool with no time in it answers.
A_LENGTH_IN_THE_ANSWER = re.compile(
    r"(?<![a-z])(?:a|one|two|three|four)(?: or (?:more|so))? "
    r"(?:day|days|week|weeks|night|nights|hour|hours|fortnight|fortnights)(?![a-z])"
    r"|(?<![a-z])a few (?:days|weeks|nights)(?![a-z])|(?<![a-z])fortnight(?![a-z])")
CHECK_WATCH_LINES = (
    "That is the thing to try first, and most people do well on it. If it is no better in a week "
    "or two, that is when it wants someone to look rather than more of the same.",
    "Yes, that is worth doing first. If it stops helping, or it goes the wrong way, that is the "
    "point to get it looked at rather than wait.",
)
# The pools above are about a remedy - "most people do well on it", "give it a week or two" - and
# that is only true of a body or a habit. A job that is not a remedy is a price, a form, a wait or
# a quote, and the remedy wording is about nothing there: "what does a dentist cost" / "will that
# help" got "most people do well on it" over an answer whose job was to ask which band the
# treatment falls in, "how long does a passport take" / "will that work" was told to give it a
# week or two over an answer that says ten weeks, and "my car is 12 years old" / "will that help"
# was told it tends to do the job over "get an insurance quote before you buy". This pool answers
# the check and claims nothing about how long the job takes or how it usually goes, because the
# answer said neither (snappy-net, #8488).
# The words that make a remedy pool's claims true: a body part or a symptom. Only these, and not
# the clinician words - "what does a dentist cost" names a dentist and asks about money, and the
# answer to it has no body in it at all (snappy-net, #8488).
try:  # the body and symptom words the composer already knows
    from .fallback_data import BODY_PARTS as _BODY_PARTS, SYMPTOM_WORDS as _SYMPTOM_WORDS
except Exception:  # noqa: BLE001 - a reading that cannot be imported just leaves the neutral pool
    _BODY_PARTS = _SYMPTOM_WORDS = frozenset()
_A_BODY_WORD = frozenset(_BODY_PARTS) | frozenset(_SYMPTOM_WORDS) | frozenset((
    # the words the order of a sentence hides: "my back is killing me", "i feel sick"
    "sick", "unwell", "ill", "nauseous", "sore", "soreness", "swollen", "swelling"))


def _about_a_body(*texts):
    """True when one of these lines names a body part or a symptom.

    Callers pass the line the person typed, not the answer: an answer says "back the files up",
    and read as a body that made the laptop answer a remedy ("give it a week or two" over "leave
    it two days"). The line the person typed is what the check is about.
    """
    for text in texts:
        words = re.findall(r"[a-z'-]+", str(text or "").lower())
        if any(word in _A_BODY_WORD for word in words):
            return True
    return False


CHECK_JOB_LINES = (
    "That is how I would go about it, and it is the right thing to do first. Tell me how you get "
    "on and I will pick it up from there.",
    "Yes, do it that way - it is the sensible order to do it in. Say how it goes.",
    "That is the right first move, and what comes back from it decides the next step.",
)
# A choice the answer made for them ("what should i cook tonight" -> three dinners, "should i get a
# dog" -> the test to apply) and its "is that ok?" is a question about the suggestion, not about a
# fault. Standing aside for it left the acknowledgement floor's "Alright then - good luck with
# it.", which answers nothing, so the pool says the one thing that is true and useful: it is a good
# call, and nothing in it needs second-guessing. It works for a dinner and for a dog because it
# judges the choice rather than the thing chosen.
ASKS_FINE = re.compile(
    r"\b(?:ok|okay|alright|all right|fine|sensible|a good idea|worth it)\b", re.I)
ASKS_WRONG = re.compile(r"\b(?:bad|wrong|worrying|worry|a problem|dangerous|stupid)\b", re.I)
CHOICE_OK_LINES = (
    "Yes - that is a good call, and there is nothing in it I would change.",
    "Yes, go with it. It is a sensible thing to do and nothing in it is a problem.",
    "That one is fine as it stands. Nothing in it needs second-guessing.",
    "Nothing wrong with that choice. If it is the one that suits you, take it.",
    "Yes, I would. That is the pick I would make from where you are standing.",
)
# The lines talk about the thing, not about the conversation: "there was no warning in what I
# told you" reads as a system message about itself, and a person asking whether something is bad
# wants to hear that it is ordinary on its own and what would change that.
NOTHING_WARNED_LINES = (
    "Nothing there is a warning sign - it is the ordinary thing to do. What would change it is "
    "the thing itself getting worse, or not settling.",
    "There is no warning in it: that is the everyday fix. What would matter is it getting worse "
    "or not shifting, so watch for that.",
    "Nobody needs to be called over it yet - it is the standard way to handle it. The point to "
    "get someone is if it does not settle.",
    "It is the usual handling of a thing like that rather than a warning about it. What would "
    "matter is it getting worse or not shifting.",
    # No line here rules on how bad the thing is. Three months of a landlord's damp gets this pool,
    # and "On its own, no" about that decided something the answer never decided: the fix in it
    # says the thing wants putting right, not that it is nothing.
    "It is a job to do rather than a sign of how bad it is. Do that, and the thing to watch is it "
    "getting worse or not settling.",
)

# A doubt asked over money is not a doubt about a symptom, and the "fix with no warning" pool
# above answers it as one: "i cant pay the rent this month" / "is that bad" was told "It is the
# usual handling of a thing like that rather than a warning about it. What would matter is it
# getting worse or not shifting", which is a thing that might settle rather than a month with a
# hole in it. The rent, a card, a fine and a bill all get that same sentence, and none of them is
# something the person can watch for a week.
#
# What is true of all of them: the number is the problem rather than a fault in the person or the
# thing, and the date on the next letter is what makes it urgent. Nothing here says how it ends or
# what they can afford, and nothing here calls it their fault.
MONEY_TROUBLE_LINES = (
    "Nothing here is broken - it is the money that does not stretch, and that is a thing letters "
    "and calls fix faster than waiting does. What is the first date you have to meet?",
    "It matters, and it is the sort of thing that shrinks as soon as somebody official is told "
    "about it. Ring the one the answer named before the next payment date, not after.",
    "That is a real hole in the month rather than a fault in you. Start with the one the answer "
    "named, and tell me what they say.",
    "It is a squeeze, not a sign that you have done something wrong, and it is the kind that gets "
    "smaller once it is written down. What is the number you cannot meet?",
)
# The words a money line is made of. A noun alone is not a trouble ("i got a pay rise" has wages
# in it), so the line needs one of these and a word that says something is not being met.
MONEY_NOUN_WORDS = frozenset((
    "rent", "money", "bill", "bills", "debt", "debts", "owe", "owed", "arrears", "overdue",
    "loan", "loans", "credit", "card", "cards", "mortgage", "council", "tax", "fine", "fines",
    "energy", "electric", "electricity", "gas", "heating", "water", "payment", "payments",
    "payday", "wages", "pay", "savings", "overdraft", "afford"))
MONEY_NOT_MET = re.compile(
    r"\b(?:cant|can'?t|couldnt|couldn'?t|no|not|nothing|never|behind|missed|miss|late|overdue"
    r"|short|stuck|struggling|struggle|afford|owe|owed|debt|debts|arrears|skint|going down"
    # A fine or an arrears letter is the trouble itself, so it needs no other word: "i got a
    # parking fine for 120 quid" is a month that has just got worse, not a fault to be watched.
    r"|cut|reduced|behind on|fine|fines|fined|penalty|penalties|repossession|evicted|eviction"
    # A card turned down at the till is the money failing in public, and it was told to watch it.
    r"|bailiffs|declined|decline|refused|bounced|overdrawn|overdraft)\b")
# "pay" is in the noun list because "i cant pay my mate back" is money, and the one verb it belongs
# to that is not money is "pay attention": that line was answered "That is a real hole in the month
# rather than a fault in you", which is a sentence about a person's bank balance.
NOT_MONEY_PAY = re.compile(r"\bpay(?:s|ing|ed)?\s+(?:attention|heed|respects?|tribute|homage|"
                           r"lip\s+service|a\s+visit|a\s+call|compliments)\b", re.I)
# Somebody else's money is theirs: "my son has run up a bill" is still a money doubt, so this is
# only used to keep a doubt about somebody's health off the money pool.
A_BODY_IN_THE_LINE = re.compile(
    r"\b(?:pain|ache|hurts?|hurting|sore|swollen|rash|bleeding|lump|cough|fever|temperature|"
    r"vomiting|sick|dizzy|breathless|doctor|gp|hospital|ambulance)\b", re.I)


# Any number at all, for the gate that hands a money line with a figure in it to the comparison.
_A_NUMBER = re.compile(r"\d")


def _a_doubt_about_money(memory):
    """True when the doubt this turn is about money, or "".

    Read off the person's own line one turn back, not off the answer: the answer over a money
    line is a knowledge card about rent or a card or a bill, and its own "what would matter is it
    getting worse" is the thing this replaces.
    """
    said = _flat(_last_person_line(memory) or "")
    if not said or len(said.split()) > 16:
        return ""
    words = set(_words(said))
    if not words & MONEY_NOUN_WORDS:
        return ""
    if not MONEY_NOT_MET.search(said):
        return ""
    if A_BODY_IN_THE_LINE.search(said):
        return ""
    if NOT_MONEY_PAY.search(said):
        return ""
    return said


# The answer put a timescale on watching it, and the person has already been living with it longer
# than that. "i wake up soaked in sweat every night for months" / "is that bad" was told "Not the
# thing itself, no. What would change it is you wake drenched for weeks" by the same answer that
# named the weeks, which is a ruling contradicted by its own condition.
MET_LINES = (
    "That answer put a timescale on watching it, and you are already past it. That is the point it "
    "meant, so get it looked at rather than sitting on it.",
    "The answer's own line on this is the timescale, and yours has been going on longer. That is "
    "the bit to act on, and it sounds like it is now.",
    "It said to watch it, and gave the timescale for doing that. You are past the timescale, so it "
    "is past watching - get it seen to.",
)
# An amount of money is not a condition, so nothing here is "ordinary". "i owe 300 on my gas bill" /
# "is that bad" was answered "That one is the ordinary kind, so no. Watch it rather than worry about
# it: if it's still the same in a week or two..." - a ruling about a symptom given to a question
# about a bill, off the "usually" the money answer spends on tariffs rather than on the fault. The
# question the person is really asking is whether the number is too big, and the answer's own
# comparison is the only thing that settles that, so the line hands them the comparison.
# Whether a figure is a lot is not a fault and not a symptom, and it is the one doubt the body
# readings below answer worst: "im looking at a gym near work" / "its 45 a month" / "is that a lot"
# was told "Sounds good.", and "my electricity is 180 a month" / "is that a lot" was told "Alright
# then - good luck with it". Both are the bot agreeing with a price it never weighed.
#
# Nothing here knows what a gym or a unit of electricity costs, so nothing here says a number is
# high or low. What it can say is what the number comes to over a year, which is the figure that
# actually gets weighed against what the money would otherwise do, and that whether it is a lot
# depends on that comparison rather than on the number alone.
FIGURE_LINES = (
    "Same money every month adds up to a yearly figure, and that is the one to weigh: if a year of "
    "it still feels worth what you would otherwise do with the money, it is not too much.",
    "It is only ever a lot next to something. Put the year's total beside what else that money "
    "would do for you, and the answer usually picks itself.",
    "A monthly figure hides its size. Work out the year, then ask what you get for the year - to "
    "one budget it is loose change and to another it is the whole of the saving.",
)
# The ask for a judgement on a figure. Read before the bare doubts, so a price question keeps the
# money reading: as a bare doubt ("is that a lot" is not in BARE) it fell to the chat floor.
A_FIGURE_ASK = re.compile(
    r"^(?:and |so )?is (?:that|this|it) "
    r"(?:a lot|a lot of money|too much|too much money|too expensive|expensive|cheap|good value|"
    r"about right|a fair price|that much|really that much)"
    r"(?: then| though| or not)?$", re.I)

MONEY_LINES = (
    "That is a figure to compare rather than a fault: the answer above gives the usual one, so put "
    "yours beside it, and if yours is the big one, that is what to change.",
    "Not bad so much as a number to check. The answer above quotes what is usual, and the gap "
    "between that and yours is the bit worth acting on.",
    "Nothing is broken there - it is your figure against the usual one the answer gave. If yours is "
    "the higher of the two, that is the thing to do something about.",
)
# The words a line about an amount of money is made of. Nothing about a body is in here: a body word
# in the line keeps the verdict, because "my back went and the bill was 300" is about the back.
MONEY_WORD = frozenset((
    "bill", "bills", "invoice", "invoices", "rent", "owe", "owed", "owes", "owing", "debt",
    "debts", "tariff", "tariffs", "refund", "refunds", "fare", "fares", "price", "prices",
    "charge", "charges", "charged", "payment", "payments", "paying", "paid", "pay", "cost",
    "costs", "mortgage", "loan", "loans", "overdraft", "insurance", "premium", "premiums",
    "subscription", "subscriptions", "council", "tax", "vat", "fine", "fined", "money",
    "pennies", "quid", "pounds", "dollars", "euros", "pension", "salary", "wage", "wages",
    "budget", "savings", "saving",
))
# A currency amount, with a symbol or a word, which is a figure however the line words it.
A_FIGURE = re.compile(
    r"[\u00a3$\u20ac]\s?\d|"
    # "200 a month", "90 per week": a bare number with the period it is paid over is a figure too,
    # and it is how most people say a bill.
    r"\b\d+(?:\.\d+)?\s*(?:p|quid|pounds?|dollars?|euros?|grand|k)\b|"
    r"\b\d[\d,.]*\s*(?:a|per|each)\s+(?:month|week|year|fortnight|day)\b",
    re.IGNORECASE)


A_COMPARISON = ("usual", "usually", "typical", "typically", "compare", "compares", "average",
                "on average", "benchmark")


def _is_a_comparison(said):
    """Whether the answer above quotes a usual figure for the person's own to be read against."""
    if A_FIGURE.search(said or ""):
        return True
    return _first(said, A_COMPARISON) is not None


# "is that just age" asks the one thing the answer above did not say: whether what the person
# is seeing is ordinary. The referral pool cannot say it ("Yes, that one wants a proper look") and
# the ordinary pool cannot either, because the honest reply starts "often it is, and the change is
# the part to watch". So the form has its own lines.
JUST_AGE = re.compile(
    r"\b(?:just|only)\b[^.!?]{0,24}\b(?:age|a phase|a stage|tiredness|the tiredness)\b",
    re.I)
AGE_LINES = (
    "Often it is age, and the thing that is not ordinary is a change: slower than before is usual, "
    "new or getting worse is the part to get looked at.",
    "Some of that is ordinary at that age. What is worth a word with the GP is a change - something "
    "that came on recently, or that keeps getting worse.",
    "Mostly age, as a rule, and it is the change that settles it rather than the thing itself: "
    "suddenly different, or worse each month, is the point to ask someone about it.",
)


def _a_figure_owed(line):
    """Whether the person's line is an amount of money rather than a condition of a body."""
    if not line:
        return False
    words = [w.replace("'", "").lower() for w in re.findall(r"[A-Za-z\u00a3$\u20ac']+", line)]
    if any(word in BODY_WORD for word in words):
        return False
    if any(word in MONEY_WORD for word in words):
        return True
    return A_FIGURE.search(line) is not None


# A state the person named themselves, when nothing in their line is a body: "i feel really low",
# "im so tired", "i cant stop crying", "ive been feeling flat all week". The answer above one of
# these is a warm chat line rather than a knowledge answer, so the fault readings below have
# nothing to read and the turn fell to the sign-off floor - "Glad to hear it." after "i feel
# really low", "Alright then - good luck with it." after "is that bad" - or to the search hedge.
#
# A mood is not a fault to be diagnosed and not a thing to look up. It is what a hard stretch does
# to a person, it lifts slowly, and the one thing worth naming is the sign that says ask for a
# hand. Nothing here says what the cause is and nothing here promises a date. The state the person
# named picks the family, because the sentence that is true after "im so tired" is not the one that
# is true after "i cant stop crying", and one pool for all of them gave five different weeks one
# identical line.
BODY_WORD = frozenset((
    "pain", "ache", "aches", "aching", "sick", "ill", "nauseous", "nausea", "dizzy", "headache",
    "temperature", "fever", "breathless", "throat", "chest", "stomach", "arm", "leg", "legs",
    "back", "knee", "hand", "foot", "feet", "head", "tooth", "toothache", "cough", "cold", "flu",
    "rash", "lump", "bleeding", "bleed", "blood", "itch", "itching", "swollen", "cramp",
    "period", "surgery", "pill", "pills", "tablet", "tablets", "dose",
))
# Somebody else in the line means the state is theirs, and "my son is worn out" is not a doubt
# about the person asking.
SOMEONE_ELSE = frozenset((
    "son", "daughter", "child", "children", "kid", "kids", "baby", "mum", "mom", "dad", "mother",
    "father", "wife", "husband", "partner", "boyfriend", "girlfriend", "sister", "brother",
    "friend", "gran", "grandad", "grandma", "grandpa", "nan", "colleague", "boss", "dog", "cat",
))
# The state, and the family of sentence that answers it. "fed" is here for "fed up", which is the
# same line said the other way round.
FEELING_FAMILY = {
    "tired": "tired", "exhausted": "tired", "drained": "tired", "wiped": "tired",
    "knackered": "tired", "shattered": "tired", "worn": "tired", "burnt": "tired",
    "burnout": "tired",
    "anxious": "anxious", "anxiety": "anxious", "worried": "anxious", "stressed": "anxious",
    "stress": "anxious",
    "crying": "crying", "cry": "crying", "tearful": "crying",
    "low": "flat", "down": "flat", "flat": "flat", "miserable": "flat", "unhappy": "flat",
    "sad": "flat", "numb": "flat", "lonely": "flat", "hopeless": "flat",
    "overwhelmed": "heavy", "struggling": "heavy", "fed": "heavy", "useless": "heavy",
    "worthless": "heavy", "pointless": "heavy",
}
FEELING_DOUBT_LINES = {
    "tired": (
        "That is what running on empty feels like, and it is not a fault in you. Sleep and food "
        "come first - tiredness from a hard stretch lifts once those are back.",
        "Nothing about it is a sign something is broken. Tired like that is what carrying a lot "
        "does to a person, and it comes back up slowly rather than all at once.",
        "Being this worn out is ordinary for the run you have had, and it is allowed to be this "
        "heavy. If a couple of weeks pass with no better days in them, that is worth saying to a "
        "GP.",
    ),
    "anxious": (
        "That is worry doing its work, and it is not a sign something is wrong with you. It eases "
        "once the thing on your mind eases; until then, sleep and eating are the two worth "
        "guarding.",
        "Nothing about it is unusual, and nothing to be ashamed of. The part worth watching is "
        "whether it is there all day every day - weeks of that is worth saying to a GP.",
    ),
    "crying": (
        "That is tiredness and grief coming out of you, and it is not a weakness. It comes in "
        "waves, and the waves get further apart - they do not keep to a timetable.",
        "Nothing about crying like that is a sign something is broken. It usually eases within a "
        "few weeks of the thing that set it off; a month of it is worth saying to a GP.",
    ),
    "flat": (
        "That is what a low stretch does to a person, and it is not a fault in you. It lifts, "
        "slowly and not in a straight line - watch the good hours rather than the bad ones.",
        "Nothing there is a sign something is broken. Feeling flat is what a heavy few months "
        "looks like from the inside, and the way back is usually small and boring: sleep, food, "
        "one person who knows.",
        "That is ordinary for the run you have had, and it is allowed to be this heavy. If a "
        "couple of weeks go by with no better hours in them, that is the point to say it to a "
        "GP.",
    ),
    "heavy": (
        "That is a lot to carry, and it is not a measure of you. If a couple of weeks pass with "
        "no better hours in them, say it to a GP - that is what they are there for.",
        "Nothing there is a weakness. What you are describing is what too much for too long feels "
        "like, and the first thing that helps is usually a shorter list rather than more effort.",
    ),
}
# Which doubt was asked. "is that bad" asks whether the thing matters, and the pools above
# answer that. "is it normal" asks something else: whether the thing is the customary one. The
# answer above is read the same way for both, so the pools above said the opposite of it over a
# normality ask - "... the causes behind it, and how to fix it for most people who snore ..."
# then "is it normal" came back "No - the part you asked about is the harmless kind", and the
# person hears that their snoring is not normal (snappy-net, #3872 review). Nothing in the
# reading changes: the pool follows the doubt that was actually asked.
ASKS_NORMAL = re.compile(
    r"\b(?:normal|abnormal|unusual|usual|typical|common|ordinary|standard)\b", re.I)
# "is that ok" asks for permission, and its answer is "yes" - the same reading, told the other way
# round. The severity pools say "no" in words ("That one is the ordinary kind, so no", "No - the
# part you asked about is the harmless kind"), which is the verdict for "is that bad" and the
# opposite of the one asked for here: over a harmless answer, "my knee clicks when i go upstairs"
# / "is that ok" was told "No - the part you asked about is the harmless kind". Nothing in the
# reading changes; the pool follows the doubt that was actually asked, as it does for the
# normality ask above.
ASKS_OK = re.compile(r"\b(?:ok|okay|alright|all\s+right|acceptable|fine|safe)\b", re.I)
OK_LINES = (
    "Nothing in that sounded like a warning sign \u2014 so yes, it is fine. What would change it "
    "is the thing itself changing: getting worse, or not settling.",
    "Yes \u2014 that one is the ordinary kind. Watch it rather than worry about it: if it is still "
    "the same in a week or two, or it gets worse, get someone to look at it.",
    "Yes \u2014 the part you asked about is the harmless kind. What to keep an eye on is change "
    "rather than the thing itself.",
)
ORDINARY_NORMAL = (
    "Yes, that is the usual thing - what to keep an eye on is change rather than the thing "
    "itself.",
    "Yes, that is normal for most people. Watch it rather than worry about it: if it is the "
    "same in a week or two, or it gets worse, get someone to look at it.",
    "Yes, that is the ordinary thing, and it stays ordinary unless it changes. Getting worse, "
    "or not settling, is what would make it worth someone's look.",
)
CARE_NORMAL = (
    "Yes - common or not, that one is worth getting looked at properly. Say what you told me "
    "here when you do.",
    "Yes. That one needs a look rather than watching, and whether it is the usual thing is "
    "exactly what the look settles. Say what you told me here when you go.",
)
# The honest answer when the bot cannot say how usual a thing is - and only then. Over a card that
# already said ("It is common at four and still common at nine") the line argues with the answer
# the person has just read, and over a card that put a time on its referral ("ring the vet today")
# it hedges about a cheap check that the card said to make now (hearty-emu, airy-moss, #3872).
CARE_NORMAL_UNKNOWABLE = (
    "I could not call that usual or not from here, and it is one to have looked at: the check "
    "is cheap and it settles the question rather than the guessing.",
)
# A card that told them when: "ring the vet today", "get it seen the same day". The doubt is
# answered by the card's own timing, so the reply says to do it rather than wondering whether the
# thing is usual.
CARE_NOW = re.compile(
    r"\b(?:today|tonight|the same day|same day|straight away|right away|now|urgent|"
    r"within (?:a|one|two|three|\d+) (?:day|days|hour|hours))\b", re.I)
# The same timed card, asked the other doubt. "Yes, that one wants a proper look" answers "should I
# be worried" and means the opposite over "is it normal": a person asking whether a thing is usual
# reads that yes as "yes, it is usual" over the answer that said to have it seen today. So the
# normal-shaped line says the timing and the look, and never answers the usual question it cannot
# answer (shiny-shrew, #3872).
CARE_NOW_NORMAL = (
    "Don't sit on that one - it is a today thing, and whether it is the usual thing is what the "
    "look settles rather than the guessing.",
    "That wants seeing today. Whether it is the ordinary version or not is exactly what the "
    "visit is for, so ring and be seen.",
)
DO_NORMAL = (
    "That is the ordinary thing to do about it, and it is a job rather than a danger: do what I "
    "said and see whether it holds.",
    "Nothing in that is out of the ordinary - it is the everyday job, so do it and see whether "
    "it holds; if it comes back after that, get someone in.",
    "That is the usual way of dealing with it, and it is worth sorting rather than worrying "
    "about - do it and see whether it holds.",
)
CONDITION_NORMAL = (
    "Ordinary on its own, yes - and it stops being usual if {when}. That is the point to act on.",
    "That is the usual case on its own, and it becomes something else if {when}.",
    "Usual up to a point: what would make it something to act on is if {when}.",
)
NOTHING_WARNED_NORMAL = (
    "Yes, that is how it is normally handled. What would matter is a change in it.",
    "Yes, that is the ordinary job, and what would send you to someone is a change in it.",
    "Yes, ordinary - that is the everyday fix for it, and the thing to watch is it getting "
    "worse or not shifting.",
)
YES_LINES = (
    # "the check itself" opened this pool until a person's own chats showed what it did: the pool
    # is picked for any yes, and only an answer that named a test or a scan makes a check the thing
    # to act on. After "ring 111 now" for a baby who has stopped feeding, and after "ring a dentist
    # the same day" for a tooth, it told a worried person the part worth acting on was a check
    # nobody had offered. Acting is what every one of those answers asked for, so that is what the
    # line says, and it no longer names a test, a scan or an examination.
    "Yes — it is worth acting on rather than sitting on. Asking costs very little and it stops "
    "the guessing.",
    "Yes, that one wants a proper look rather than watching it. Get it looked at properly, and "
    "say what you told me here when you do.",
    "Yes. Get it seen to — not an emergency, but not something to sit on either.",
)
# A thing the person owns is not a body, and the pools above talk like one: "watch it rather than
# worry about it: if it's still the same in a week or two", "get it looked at properly". Over a
# knocking boiler that tells a person to leave it alone, and offers them a doctor for a machine
# (modern-cap, #routing 77551). The verdict on a thing is about the job and who does it: the
# everyday reading is "do the job, and if it is still doing it, that is the call", and a call is
# somebody with the trade rather than somebody with a stethoscope.
A_THING_THEY_OWN = re.compile(
    r"\b(?:boilers?|radiators?|central heating|thermostat|washing machine|washer dryer|"
    r"tumble dryer|dishwashers?|fridge|freezer|fridge freezer|ovens?|hob|cooker|microwave|"
    r"kettles?|toaster|hoover|vacuum|lawnmower|mower|strimmer|pressure washer|shower tray|"
    r"showers?|taps?|toilets?|sinks?|drains?|plughole|gutters?|roof|fencing|fence|decking|"
    r"doors?|windows?|locks?|sockets?|fuse board|consumer unit|lights?|"
    r"cars?|vans?|bikes?|bicycles?|motorbike|scooter|tyres?|brakes?|clutch|exhaust|engine|"
    r"laptops?|computers?|pcs?|printers?|phones?|tablets?|monitors?)\b", re.I)
# The same noun can be the person's own body ("my back", "my skin"), and then the pools above are
# the right ones whichever word sits beside it: "my sink" is a drain, "i feel sick" is not.
A_BODY_WORD = re.compile(
    r"\b(?:skin|rash|itch|itching|eyes?|ears?|throat|chest|stomach|belly|knee|knees|joint|"
    r"joints|hips?|shoulders?|neck|foot|feet|hands?|arms?|legs?|tooth|teeth|gums?|breath|"
    # A "back door", a "back garden" and a "back wall" are not the person's back.
    r"back(?! (?:door|doors|garden|gate|wall|bed|room|bit|passage))|"
    r"breathing|breathless|cough|poo|wee|blood|fever|temperature|hearing|sight|head|"
    r"headaches?|migraine)\b", re.I)
THING_ORDINARY = (
    "It is the everyday thing rather than a fault, and the job I described is what settles it. If "
    "it is still doing it after that, or it comes back, that is when it wants somebody who does "
    "this for a living.",
    "Nothing in that is a fault on its own: it is the ordinary thing with a job attached. Do the "
    "job, and if the noise or the mark is still there afterwards, get somebody in.",
    "That is the usual reason for it, and the fix I gave is the check. Do that first - if it "
    "holds, it was the everyday thing, and if it does not, that is a call to somebody with the "
    "trade.",
)
THING_CALL = (
    "Yes - that one is for somebody who does this for a living rather than a watch-and-see. "
    "Describe it as you did here when you book them in, and hold off using it until they have "
    "looked.",
    "Yes, get that looked at properly. It is a call to a trade rather than something to sit on, "
    "and the sooner they see it the less it usually costs.",
    "Yes. That is a job for somebody with the right tools, not a wait-and-see.",
)
# A safety answer has already said what to do, so the verdict question after it has one answer:
# yes. "my cat is having trouble breathing" / "is that serious" was the search hedge, because the
# verdict reading only ever reads a knowledge answer and a safety line is not one. The lines point
# back at the call without quoting it, because the call is whatever the answer named - a vet, 111,
# a crisis line - and they stay true for all of them.
# The last thing the bot said was not an answer from the knowledge base but a warm line about the
# person's own day, and the bare verdict ask arrives on top of it: "i cant be bothered to leave
# the house" / "is that bad" was answered "Alright then - good luck with it". There is no answer
# to read a verdict out of, so this is a floor rather than a reading: it says the honest thing
# about a habit or a mood - not a fault, worth looking at - and asks the question a friend asks.
# True whatever the subject was, because the composer does not know what it was.
BACKSTOP_LINES = (
    "Not bad, no. What would make it matter is how long it has been going on and what it is "
    "costing you — how do those two look?",
    "I wouldn't call it bad. It is worth a proper look rather than a shrug, though: what does it "
    "take out of your week?",
    "Not a fault, and nothing to be ashamed of. The question worth asking is whether it has a "
    "hold on your days rather than whether it is bad.",
)
# The care words that name somebody who looks at a person rather than a thing. "get someone in"
# is a trade coming to the house, so an answer whose opening names one of these is a referral and
# not a job: the boiler answer's Gas Safe engineer keeps the job pool, and a child referred to a
# speech therapist does not.
PEOPLE_CARE = ("gp", "doctor", "nurse", "midwife", "health visitor", "physio", "therapist",
               "pharmacist", "optician", "dentist", "vet", "111", "referral", "hospital",
               "a&e", "urgent care", "out of hours", "specialist", "clinic")
# The same floor when the line above ruled on nothing: "I'm listening - say more if it helps"
# is not an answer, and a floor that says "I wouldn't call it bad" over it rules on a subject it
# has not read. These ask the question a friend asks and claim nothing about the thing.
FLOOR_LINES = (
    "How long has it been going on, and what does it cost you day to day?",
    "How long has it been like that, and is it getting in the way of your week?",
    "What would you like to do about it, and how long has it been like that?",
)
# And the floor for a line that is about something the person has rather than does ("i have a
# cough", "i have a lump in my breast", "i have blood in my poo"). It may not carry the severity
# of the two pools above - what somebody has can be a lump or a dog - so it asks and promises a
# hearing, which is more than "Alright then - good luck with it" without ruling on a subject the
# composer has not read.
NEUTRAL_ASK_LINES = (
    "Say a bit more: how long has it been like that, and what does it cost you day to day?",
    "How long has it been going on, and what would you like to do about it?",
    "Tell me more and I will help you think it through: how long, and how is it affecting you?",
)
# A bare doubt after a plan, a choice or a wish the person brought is not a nod and not a symptom,
# and neither pool above fits it: "im going to rome" / "is that ok", "i want to book a holiday" /
# "is that ok", "should i accept a counter offer" / "is that ok" and "we're thinking of getting a
# rescue greyhound" / "is that ok" were all answered "Alright then - good luck with it." The doubt
# path had nothing to rule on, so it stood aside, and the ack pool read "ok" as a nod. There is
# still nothing to rule on - the plan is theirs - but a shrug says the conversation is over, and
# what the person is checking is that wanting it is allowed. So these name the thing as a thing
# they want and ask for the part that is being weighed.
A_PLAN_DOUBT_LINES = (
    "Nothing in that sounds wrong: it is a plan rather than a fault to check. Which part of it are "
    "you unsure about?",
    "Say which part you are unsure about and we can weigh it up together.",
    "That is yours to decide rather than something to worry about. What is the bit you keep going "
    "over?",
)
# "i tried that and it helped" / "is that bad" is not a symptom: the thing worked, and the next
# thing to say is to keep it up. A floor over it invented a worry ("That is worth a proper look").
# A named professional who is not an emergency: a dentist, an optician, a physio, a vet, a
# pharmacist. The answer named who, so the verdict is "yes, get it seen", not "ring tonight".
SOON_LINES = (
    "Yes, that wants looking at - the answer named who, so book it rather than wait for it to "
    "settle.",
    "It is worth having it seen to, and that answer already said by whom. Get that booked, and "
    "say how long it has been going on when you do.",
    "Not an emergency by the sound of it, but not something to leave either: the person named in "
    "that answer is the one to see.",
)
HELPED_LINES = (
    "Then it is doing its job - keep it up and give it a few more days before you judge it.",
    "Good: that is the thing that worked, so stay with it. The point to get someone to look is if "
    "it stops helping.",
    "That is the answer then. Keep doing it, and tell me if it stops working.",
)
# The asks the knowledge base's own hedge answers better than this file can: "should i be
# worried" is not a verdict about the bot's last line, it is a request for the health hedge
# ("a GP, a pharmacist or 111 will tell you"), and the floor took that turn away from it.
WORRIED_ASK = re.compile(
    r"^(?:and |so )?should i (?:be )?(?:worried|worry|worrying|concerned|see someone|see a doctor"
    r"|do anything|do something|get it checked|be checked|call someone|ring someone)(?: then"
    r"| though)?$")
# A thing that helped, in the person's own words, before the doubt ask.
HELPED = re.compile(
    r"\b(?:(?:that|it|this) (?:has )?(?:helped|worked|did the trick|did help|is helping"
    r"|is working)|both worked|they worked|it worked out|(?:much )?better (?:now|today)"
    r"|(?:its|it is) (?:helping|working)|on the mend)\b")
YES_SAID_LINES = (
    "Yes - that is why the call is the thing to do now rather than something to wait on. Do that "
    "first, and tell me what they say.",
    "Yes it is, and that is what the call is for. Make it now rather than tomorrow, and we can go "
    "through the rest once you have.",
    "Yes - ringing is not an overreaction here, it is the whole point of it. Do that first and "
    "come back to me after.",
    "Yes. Somebody needs to hear this today rather than next week, so make the call and then tell "
    "me what they say.",
)

# An answer that tells the person to stop doing something is standing in for a warning, wherever
# in the answer it comes: the "yes, this wants a proper look" line is the verdict for it, and
# "that one is the ordinary kind, so no" is never it.
# An answer that opens by telling the person to get rid of the thing is the strongest verdict in
# the knowledge base: "bin it, I'm afraid: cooked chicken left out for more than 2 hours isn't
# safe to eat". A bare "is that bad" on top of it was answered "Alright then - good luck with it"
# - the bot handing back the door on the one answer where a person is asking to be talked out of
# a risk. The yes is the answer's own instruction said back, so the pool cannot disagree with it,
# and the action is quoted from the line rather than named by the pool.
THROW_AWAY = re.compile(
    r"\b(?:bin\s+(?:it|them|that)|throw\s+(?:it|them|that)\s+(?:away|out)|"
    r"chuck\s+(?:it|them|that)(?!\s+(?:\w+\s+){0,2}(?:in|on|into|with|to)\b)|"
    r"(?:get|getting)\s+rid\s+of\s+(?:it|them|that))\b", re.I)
# The throw-away is not the instruction when the answer says *not* to do it - "don't flush them
# and don't bin them" over old medicines read back as "Bin them" - and it is not the instruction
# either when it is one option in a list: "sell, donate or bin it now".
NOT_TOLD_TO = re.compile(r"(?:\bdon'?t|\bdo not|\bnever|\bnot|\brather than|\binstead of|\bbefore you)\s*$", re.I)
ONE_OPTION = re.compile(r"\b(?:or|and|rather than|instead of)\s*$", re.I)
# The sentence opens by naming a test rather than a state of the thing, so the answer has not
# said the person's milk is off - only what to do if it ever is.
TESTING = re.compile(r"^[\s\"'(\u2018\u201c]*(?:if|unless|once|whenever|when|any ?time|should|whether)\b", re.I)
THROW_AWAY_LINES = (
    "{Action} \u2014 it is not worth the risk, and it is not a close call.",
    "Yes, really. {Action}. This is the one where guessing costs the most.",
    "{Action}, and do not talk yourself out of it: nothing you can see or smell makes it safe.",
)
# The same answer written as a test - "if milk smells or tastes sour, bin it". The person has not
# said the milk is off, so the answer is not a verdict on their milk; it is the test that settles
# it, and the doubt on top of it is "is it bad if I get that far". The action stays, said as the
# outcome of the test rather than as a ruling on today's carton.
TEST_LINES = (
    "{Action} once it has turned - that is the whole test, and I would not taste it to check.",
    "You do not need me to judge it. {Action} once it has turned, and that is the whole test.",
    "{Action} if it has actually turned. The test is the answer, and the thing itself is the judge.",
)
# An answer that says outright that the thing itself is not safe has given the verdict in the
# sentence, and none of the readings below can see it: they read a referral, a job to do, a
# danger word or an ordinary word, and "There is no safe number of drinks before driving" is none
# of those. So `im gonna drive home after a few pints` / `is that ok` fell all the way through to
# the acknowledgement floor and answered "Alright then - good luck with it." over a straight no.
# The negative half is read here, before the care words, because an answer can hold both a no and
# a referral and it is the no that was asked about.
STATED_NO = re.compile(
    r"\bthere (?:is|are) no safe (?:number|amount|level|dose|limit|quantity|way)\b"
    r"|\bno amount of .{1,40} (?:is|was) safe\b"
    r"|\bnothing about .{1,40} (?:is|makes it) safe\b"
    r"|\bis not safe to (?:eat|drink|drive|take|use|give|leave|keep)\b"
    r"|\bare not safe to (?:eat|drink|take|use|give)\b"
    r"|\bnone of (?:it|them|these) is safe\b"
    r"|\byou cannot make .{1,40} safe\b",
    re.I)
NO_STATED_LINES = (
    "No \u2014 that is the answer's own line: {no} There is nothing in it for you to weigh up.",
    "That one is a no, and the answer said it plainly: {no} What to do instead is in the rest of "
    "what I said.",
    "No. {no} That is the whole of it, so it is not a thing for you to judge.",
    "No, and not a close call. {no}",
)
# The other half of the same reading: an answer that says the amount is enough. "is that enough"
# asks about a quantity and not about how bad a thing is, so none of the pools below can read it,
# and the acknowledgement floor took the turn. The answer's own sentence is handed back.
ENOUGH_ASK = re.compile(
    r"^(?:and |so )?(?:is|was|are|were) (?:that|this|it|all of that|all that)"
    r"(?: (?:really|actually|about|roughly))? enough(?: then| though)?$", re.I)
STATED_ENOUGH = re.compile(
    r"\bis (?:definitely |probably |easily |more than |plenty )?enough\b"
    r"|\bis plenty\b|\bmore than enough\b|\bthat will do\b|\bthat does it\b", re.I)
ENOUGH_STATED_LINES = (
    "Yes \u2014 {yes} That is the amount, and the rest of what I said is what makes it work.",
    "Yes: {yes} Nothing in the answer asks for more than that.",
    "It covers it as it stands. {yes}",
    "Yes, on the answer's own figures. {yes}",
)
STOP_DOING = ("stop driving", "don't drive", "dont drive", "don't eat", "dont eat", "don't use it",
              "dont use it", "don't touch", "dont touch", "don't drink", "dont drink",
              "leave the building", "get everyone away", "stop if it is safe")
# An answer that names the harm is a warning, wherever in it the "usually" sits. "can i give my
# cat ibuprofen" is answered "Never give a dog or cat human painkillers ... a cat can die from a
# single paracetamol ... ring them and they will usually ...", and the only cue the reading above
# found was that last "usually", so the verdict was "that one is the ordinary kind, so no" about
# a cat that can die: an answer this plain cannot be read as reassurance.
DANGER = ("dangerous", "toxic", "poisonous", "poisoning", "can die", "could die", "may die",
          "can kill", "could kill", "fatal", "harmful", "not safe", "unsafe", "an emergency",
          "never give", "never use", "never take", "never leave")
# "not dangerous", "harmless and not toxic" and "isn't poisonous" are the reassuring half of a
# danger word, so the word in front of it decides which one this is.
NEGATED = re.compile(r"(?:\bnot|\bno|n't|\bnever|\bnon)[ -]\w*[ -]?$")
# Said back when the same question comes twice: the second ask wants the answer again, plainly,
# not a fresh sentence that sounds like a different verdict.
AGAIN = (
    "Same answer as a moment ago: nothing in what I said was a warning sign. It's the change "
    "to watch for, not the thing itself.",
    "Still no. If it would help, tell me what's actually worrying you about it and I'll be "
    "straight with you.",
)
# The same reading, for the two things a person asks *after* a yes/no verdict, and just as
# often after the answer itself: "what should i do", and "should i see someone". Both are
# answered from the advice already given, because the knowledge answer that prompted them
# carries the steps and the condition in its own words.
# A filler word in front of the ask is not a subject of its own: "honestly what do i do" after
# the drain answer is the same request for the first step as "what do i do", and it was read as
# a line naming its own thing, so the person got the bare offer ("say a bit about what is in
# front of you") one turn after being told what to do. `topics.STOPWORDS` keeps these words out
# of the subject, so the lead only has to stop hiding the ask behind them; the ask itself has to
# be exactly the ask, so "actually the boiler is losing pressure" is not a step request.
# People put the filler where it falls in the sentence, not only at the front: "what can i
# *actually* do about it" and "what should i *really* do" are the same ask, and the reader below
# matched from the first word, so with the filler inside the ask neither was its line at all -
# the person got the answer above handed back with "Same as before:" in front of it, which reads
# like a restatement of the problem rather than a first move. So the filler is allowed wherever
# it lands, and what is left when it is taken out still has to be exactly the ask.
_FILLER = (r"(?:(?:and|so|ok|okay|but|well|right|honestly|actually|basically|literally|simply|"
           r"truly|really|just) )")
_LEAD_FILLER = _FILLER + r"*"
_FILL = _FILLER + r"?"
STEP = re.compile(
    r"^(?:" + _LEAD_FILLER + r")"
    r"(?:(?:what|which) " + _FILL + r"(?:should|do|can) " + _FILL
    + r"i " + _FILL + r"do(?: now| next| first| about it)?"
    r"(?: then)?$"
    r"|what " + _FILL + r"now$"
    r"|what " + _FILL + r"(?:do|should) " + _FILL + r"i " + _FILL
    + r"(?:try|do) " + _FILL + r"(?:first|next)$"
    r"|how " + _FILL + r"do " + _FILL + r"i " + _FILL
    + r"(?:fix|sort|deal with) " + _FILL + r"(?:it|that|this)$"
    r"|what " + _FILL + r"(?:should|do|can|could) " + _FILL + r"i " + _FILL
    + r"(?:put|use|apply|try) " + _FILL + r"(?:on|to|for) " + _FILL
    + r"(?:it|that|this)(?: then)?$)"
)
# The same ask when it is about speaking up: "should i say something", "shall i mention it",
# "do you think i should bring it up" want the step the last answer already gave - "Claim it in
# the room, lightly and factually ..." - not a shrug about what is the person's call. Only the
# verbs of saying something to somebody, so "should i give up" is left where it was.
SPEAK_VERBS = (r"(?:say|mention|bring (?:it|that|this|them) up|raise|tell|ask|text|call|"
               r"ring|email|write|speak|talk)")
SPEAK_UP = re.compile(
    r"^(?:and |so )?(?:(?:do you think|do you reckon|d'you reckon) )?"
    r"(?:should|shall|ought) i " + SPEAK_VERBS + r"\b"
    r"|^(?:and |so )?(?:do you think|do you reckon|d'you reckon) i should " + SPEAK_VERBS + r"\b")
# An answer that tells them to ring the emergency services is not advice to quote a step out of.
# "Ring now rather than waiting to be sure: 999 or 911, say where you are and what has happened"
# read as a step is "Ring now rather than waiting to be sure" - the colon took the number and the
# sentence about what to say with it - and the step line then put it back with an order on the
# end of it ("before you do anything else I mentioned") to somebody who has just been told to
# ring for an ambulance. The number is the instruction, so an answer that *opens* on one keeps the
# turn itself; a step ask after it is answered by whatever reads an emergency, not by a fragment.
# Only an opening: an ordinary answer that ends "and ring 999 straight away if the breathlessness
# comes on suddenly" has its own first move ("rest it, ice it") and that step is still its to give.
EMERGENCY_CALL = re.compile(
    r"\b(?:ring|call|dial|phone|contact)\b[^.!?]{0,60}?\b(?:999|911|112)\b", re.I)
SEE = re.compile(
    r"^(?:and |so )?(?:should|do) i (?:need to )?(?:see|call|ring|go to) (?:a |the |my )?"
    r"(?:someone|somebody|doctor|gp|vet|dentist|engineer|plumber|doctor about it)(?: then)?$"
    r"|^(?:and |so )?do i need (?:to see )?(?:someone|a doctor|the doctor|the vet)(?: then)?$"
    r"|^(?:and |so )?is it worth (?:seeing|going to|ringing) (?:someone|a doctor|the vet)"
    r"(?: then)?$"
)
# A how-to ask about the thing in hand names the doing and no object: "how do i prepare", "how do
# i get ready for it", "how should i practise". The thing being prepared for, practised or started
# is the one in the answer above, so the answer already holds the move and the step out of it is
# the reply. Typed on main `eae7434d`:
#
#     im nervous about a presentation
#       Rehearse the first sixty seconds out loud until you could say it half asleep ...
#     its on friday
#       Nothing separate for friday - it is the same advice: Rehearse the first sixty seconds ...
#     how do i prepare
#       I'm not sure about that one, sorry - I'd rather not guess. A quick search online will ...
#
# The person has been told how to prepare twice and asked what more there is to it; a search hedge
# is the bot saying it never had an answer. The doing takes no object, which is what separates it
# from a how-to question for the base: "how do i cook rice" names the rice, and the knowledge base
# answers that one, while "how do i cook" with the dinner in hand is this ask.
HOW_TO = re.compile(
    r"^(?:and |so |ok |okay |well )?how (?:do|should|can|would|might|will) i "
    r"(?P<doing>[a-z]+)"
    r"(?P<obj>(?: (?:[a-z]+ ){0,2}(?:it|that|this|them)"
    r"(?: (?:on (?:friday|monday|tuesday|wednesday|thursday|saturday|sunday)|then|now|first|"
    r"out|off|down|up|again|properly|safely))?)?)$")
# The doings that mean "the thing in hand" and take no object of their own. A verb of making or
# getting takes one ("how do i cook", "how do i fix"), and those belong to the knowledge base.
DOING_WITH_NO_OBJECT = frozenset("""prepare practise practice rehearse revise study train
warm stretch""".split())
# A doing with a pronoun after it names no thing of its own - "it" can only be the thing in the
# answer above - so the verb does not have to be on any list: "how do i clean it" after "my oven is
# filthy", "how do i unblock it" after "my sink is blocked", "how do i get rid of it", "how do i
# descale it". The verb list only decides the case with no object at all ("how do i cook"), where
# nothing on the line says what is in hand. (tan-needle, #routing 114695.)
KNOWING_DOING = frozenset("""know tell check spot find see say guess recognise recognize""".split())
# A bare plea for tips after the bot has already answered is the same ask as "what should i do":
# "i cant sleep" / "any tips" was answered "Happy to help - tell me what you've got so far and I'll
# add what I can", which asks the person to repeat what the bot had just told them. The subject is
# in the answer above, so the reply is the step out of it, exactly as for "what next". The plea
# comes in several words besides "tips": "any tricks" after the veg answer was still the stock
# "Sure. What have you tried so far? That tells me where to start".
#
# "Ideas" is the same plea and was not in the list: after the answer about a child who will not eat
# vegetables, "any ideas" was answered "That's most of what I know on it - say which part is still
# unclear", which is the bot saying it has nothing while the first thing to do was in the answer a
# line above ("Keep serving one small piece of veg next to something they already like").
# "Suggestions" and "thoughts" are asked in the same breath. A plea that names its own thing ("any
# ideas for dinner") keeps it, so it is still the knowledge base's question.
TIPS_AGAIN = re.compile(
    r"^(?:and |so |ok |okay |well )?(?:(?:any|some|got any|got some|need some|need any|"
    r"want some|more|any more|another|a few|any other)\s+)?"
    r"(?:tips?|advice|pointers?|tricks?|hints?|ideas?|suggestions?|thoughts?)"
    r"(?: (?:at all|then|please|too|now|really|anyway))*$"
)
# The same plea said as one move: "just one thing to start", "where do i start", "what is the
# first thing to do". A person who has just been told the long version and asks for the one thing
# is asking the same question as "any tips", and the answer above holds it. It is a separate
# pattern because the words are a plan, not a plea: "one thing to start" reads as a thing to do,
# so it was acknowledged back ("i need to save money" / "just one thing to start" came back
# "Got it - just one thing to start") instead of being answered from the answer.
# The ask usually comes with a word of feeling in front of the verb - "where do i even start",
# "how do i actually begin" - and the pattern only knew an adverb after it, so the line fell
# through to the one that says the answer over again ("Same as before: ..."), which is the
# repeat STYLE.md forbids. Any of these words in that place is the same ask, and none of them
# changes what is being asked for. (@keen-jasmine's list, from #routing 54143.)
ONE_THING_ADVERB = ("even", "actually", "really", "just", "possibly", "maybe", "instead",
                    "honestly", "normally")
_ONE_THING_ADVERB = r"(?:(?:%s) )?" % "|".join(ONE_THING_ADVERB)
# A follow-up that asks how to do the thing in hand, in the words people use for it: "whats the
# safest way", "whats the best way to fix it", "which is the quickest method". Like a plea for
# tips, it names no subject of its own - the subject is the answer above - so it is a step ask.
# One that does name its own thing ("whats the best way to defrost chicken") is the knowledge
# base's, and the "to <verb> it" tail is only accepted for a verb that takes a pronoun.
# "Cheapest" is deliberately not here: "what is the cheapest way to do it" after an answer about
# tyres wanted prices, and the base gave them ("a budget tyre fitted is about 55 to 80 a corner"),
# while the step handed back was "read the size off the sidewall". A price ask is answered with
# prices; the method asks above are the ones the base could not answer at all.
A_HOW_ASK = re.compile(
    r"^(?:and |so |ok |okay |well )?(?:what|whats|what is|which is|whichs) the "
    r"(?:safest|best|quickest|fastest|easiest|simplest|surest|most reliable|right|"
    r"proper|correct) (?:way|method|bet|option|approach|route)"
    r"(?: (?:to (?:do|fix|sort|handle|treat|clean|stop|get rid of|deal with|go about) "
    r"(?:it|that|this)|to (?:start|begin|try|go about)(?: (?:it|that|this))?"
    r"|of doing (?:it|that|this)|of getting rid of (?:it|that|this)"
    r"|for (?:it|that|this)|here|then|now|at all|please))?$")
ONE_THING = re.compile(
    r"^(?:and |so |ok |okay |well |but )?(?:"
    r"just (?:one|the one|the first|1) (?:thing|step|move|bit)(?: to (?:start|begin|try|do)"
    r"(?: with)?(?: first)?)?"
    r"|(?:one|the one|the first) (?:thing|step|move) (?:to (?:start|begin|try|do)(?: with)?"
    r"(?: first)?|first)"
    r"|(?:what|which) (?:is|would be|should be) the (?:one|first) thing(?: to do)?"
    r"|(?:where|how) (?:do|should) i " + _ONE_THING_ADVERB + r"(?:start|begin)"
    r"(?: with it| with that| here| off)?"
    r"|(?:what|where) do i " + _ONE_THING_ADVERB + r"(?:start|begin)(?: with it| with that)?"
    r")(?: (?:then|please|though|now|really))*$"
)
# The advice is whatever the answer put after its colon or dash, and the condition is the
# "if ..." it fenced the referral with. Neither is invented: both are the answer's own words.
AFTER = re.compile("[:;] | - | — | – ")
# The same breaks with the break kept, for the one place that has to know which one it was: a
# colon is the answer explaining its own instruction, and a dash is a new thought.
SPLIT = re.compile("([:;] | - | — | – )")
# The answer's own opening word when it leads with the second half of a thought it never wrote.
THEN_OPEN = re.compile(r"^(?:and\s+)?then[,]?\s+", re.I)
# "Ask a GP" is the same referral as "see a GP" and the knowledge base writes it that way in
# places: "i cant sleep" ends "If you're worn out all day too, or it has gone on for weeks, ask a
# GP", and the word missing here meant that answer was read as carrying no referral at all, so
# "is that bad" after it got "Alright then — good luck with it". "Ask" is left out of the
# "someone" line on purpose: "ask a friend to help you lift it" is not a referral.
REFER = re.compile(
    r"\b(?:see|ring|call|contact) (?:a |your |the )?(?:gp|doctor|vet|dentist|nurse|someone|"
    r"surgery|physio|physiotherapist|pharmacist|optician|midwife|111|999|engineer|plumber)"
    # A referral is often worded as something to have done, not someone to ring: the pet skin
    # card ends "Have the vet look before the skin is broken", and with no other referral words
    # in it a bare "should i be worried" found no verdict at all and fell to the carry. The same
    # shape covers "get a doctor to look", "have your GP check it".
    r"|\b(?:have|get) (?:a |your |the )?(?:gp|doctor|vet|dentist|nurse|physio|physiotherapist|"
    r"pharmacist|optician|midwife)\s+(?:to\s+)?(?:look|check|see|take a look)\b"
    r"|\bask (?:a |your |the )?(?:gp|doctor|vet|dentist|nurse|physio|physiotherapist|"
    r"pharmacist|optician|midwife)\b"
    # The trade is often named with the qualifier in front of it: "call a Gas Safe engineer",
    # "get a heating engineer out". Without the gap those answers named nobody at all, and the
    # "if it locks out twice" that belongs with the call was left off the verdict. A joining
    # word is not a qualifier, though: "a reason to ring the surgery or 111" names the trade on
    # the far side of an "or", and reading that as the call the answer is about turned a fix
    # with no warning in it into nothing at all ("i have a cough" / "is that bad" went back to
    # "Alright then - good luck with it").
    r"|\b(?:see|ring|call|contact) (?:a |your |the )?(?:(?!and\b|or\b|to\b|for\b|of\b|in\b|on\b"
    r"|at\b|from\b|with\b|that\b|if\b|when\b|it\b)[a-z-]+ ){0,3}(?:gp|doctor|vet|dentist|"
    r"nurse|someone|physio|physiotherapist|pharmacist|optician|midwife|111|999|engineer|plumber)"
    r"|get (?:it|that|this|him|her|them|someone|somebody)? ?(?:looked at|checked|seen)"
    r"|a&e|urgent care|out of hours"
    r"|\b(?:vet|doctor|gp|dentist) (?:visit|job|matter|appointment)\b"
    # The knowledge base also sends someone by taking the thing to a clinician: "If you get them
    # most days, ... take it to a pharmacist or GP" is the referral in the ordinary-headache
    # answer, and read as neither a care cue nor a call it left a frequency ask with the shrug.
    r"|\btake (?:it|this|that|them) (?:to|along to|back to|in to) (?:a |your |the )?"
    r"(?:gp|doctor|pharmacist|nurse|dentist|vet|physio|physiotherapist|optician|midwife)\b"
    r"|\bnot a wait-and-see\b|worth getting (?:it |them )?checked",
    re.I,
)
# An answer that names a clinician has a call in it however it is put: "a week of home readings,
# sitting still, is what a GP wants" sends the person to the same place as "see your GP", and the
# method answer ("there is nothing in it to worry about") must not stand over either. Kept apart
# from REFER because REFER reads the imperative forms a verdict is argued from, and this one only
# asks whether a person to see is named anywhere.
NAMES_A_CLINICIAN = re.compile(
    r"\b(?:gps?|doctors?|nurse|practice nurse|midwife|health visitor|pharmacist|vets?|"
    r"dentist|a&e|minor injuries|walk-in (?:centre|clinic)|urgent care|out of hours|111|999|nhs)\b",
    re.I,
)
# The shape of a referral that only names the appointment, without telling anyone to go.
DECLARATIVE_REFERRAL = re.compile(
    r"\b(?:vet|doctor|gp|dentist) (?:visit|job|matter|appointment)\b|\bnot a wait-and-see\b"
    # "A new lump in the breast should be checked by a GP within a week or two" tells nobody to
    # go: it states the appointment as the answer's judgement, and read as neither an instruction
    # nor a care word the composer called a breast lump "the ordinary kind, so no".
    r"|\b(?:checked|looked at|assessed|seen) by (?:a |your |the )?(?:gp|doctor|nurse|practice"
    r" nurse|physio|physiotherapist|dentist|vet|pharmacist|optician|midwife)\b"
    r"|\bneeds? (?:a |your |the )?(?:gp|doctor|nurse|vet|dentist|physio|pharmacist|optician)\b"
    r"|\bneeds? (?:to be )?(?:seen|checked|looked at)\b"
    # The shapes a care cue is named in without a verb: "worth a GP visit", "a GP appointment",
    # "the 111 line". They are the answer's judgement rather than an instruction, so the same
    # rule applies - in the opening it is the verdict, later it is a warning about that symptom.
    # Read as an instruction, "Pins and needles in the fingers that wake you is worth a GP visit"
    # answered a wrist that is "usually an overused tendon" with "yes, that one wants a proper
    # look".
    r"|\bworth (?:a |an |your |the )?(?:gp|doctor|doctor's|vet|dentist|optician|pharmacist"
    r"|physio\w*|nurse|midwife|health visitor)\b"
    r"|\b(?:gp|doctor's|doctor|vet|dentist|optician|physio\w*|midwife|health visitor)"
    r" appointment\b"
    r"|\b(?:nhs 111|111 line|out of hours service|urgent treatment centre|health visitor)\b",
    re.I,
)
# A step cut off on one of these is half a sentence, and telling someone to do half a sentence
# is worse than saying nothing ("compare the reading on the bill with").
WHEN = frozenset("""about around roughly per couple once twice three four five six seven two
a an every each daily nightly
morning afternoon evening night day week month year hour minute second time times""".split())
HANGING = frozenset((
    "with", "in", "of", "to", "on", "for", "at", "and", "or", "the", "a", "an", "my", "your",
    "its", "it's", "from", "by", "as", "than", "but", "if", "so", "into", "about",
    "between", "among", "through", "under", "over", "without", "within", "against", "across",
    "behind", "beyond", "towards", "toward", "upon", "except", "despite", "unless", "until",
    "whether", "onto", "than",
))
# A sentence the answer opens with a verb is the answer's first instruction.
IMPERATIVES = frozenset((
    "keep", "ease", "ice", "rest", "bleed", "put", "take", "stop", "swap", "use", "ring",
    "call", "check", "top", "wear", "cut", "leave", "unplug", "turn", "sit", "drink", "wrap",
    "raise", "prop", "wash", "rinse", "soak", "cover", "avoid", "try", "start", "do", "give",
    "pick", "choose", "compare", "buy", "order", "fill", "print", "ask", "tell", "move", "set",
    "open", "close", "save", "read", "write", "clean", "clear", "make", "budget", "shop",
    "cool", "reheat", "freeze", "drain", "store", "boil", "bake", "chill",
    "go", "get", "book", "phone", "add", "apply", "hold", "heat", "cook", "remove", "dig",
    "plant", "water", "measure", "log", "email", "text", "fill", "mix", "line", "air",
    # The rest of the verbs an answer opens its first instruction on. The list above grew one
    # answer at a time and stopped at the ones that turned up in the first few domains, so "bathe
    # it with cool water and dry it" (a cut paw) and "rub it with an oil-based cleanser" (ink on
    # the skin) were not read as the answer's first move: the step reader walked on to a later
    # sentence and pointed at the wrong thing, or found nothing and left "what should i do
    # first" unanswered. These are the verbs the knowledge base itself uses to open an
    # instruction, so the list is the base's own vocabulary and not a guess.
    # "sleep" was tried and taken out again: it opens a sentence as a noun as readily as a verb,
    # and the noun sentences are reachable - "Sleep and repetition file it away" (memory), "Sleep,
    # water and an antihistamine" (dark circles), "Sleep is when the brain files the day's
    # memories" - and each was handed back as the first thing to do. A word whose noun is as
    # common as its verb is not a tell. It costs two small steps ("sleep with your head raised",
    # "sleep with the wrist straight"), which is the cheaper side of that trade.
    # "say" and "name" are deliberately absent: those are the verbs of the bot asking the person
    # for a subject ("I'm listening - say more if it helps"), and a greeting is readable here, so
    # reading them as instructions handed that request back as the first thing to do.
    "bathe", "blot", "dab", "sponge", "rub", "wipe", "dry", "pull", "empty", "hang", "lay",
    "press", "find", "look", "run", "work", "change", "split", "pat", "stir", "track",
    "iron", "serve", "roll", "fix", "follow", "build", "replace", "send", "stand", "draw",
    # An answer about something a person is getting ready for opens on one of these, and without
    # them the step out of it was nothing: "Rehearse the first sixty seconds out loud until you
    # could say it half asleep" (a presentation) had no first move to hand back, so "how do i
    # prepare" after it was a search hedge.
    "rehearse", "practise", "practice", "recite",
    "tighten", "blend", "stretch", "skip", "practise", "watch", "learn", "offer", "report",
    "stay", "seal", "trim", "prime", "screw", "weigh", "scrape", "simmer", "roast",
    "grill", "shred", "mash", "chop", "begin", "feed", "place", "switch", "fit", "test",
    "brush", "scrub", "pour", "grate", "slice", "spray", "prune", "repot", "balance", "let",
    "be", "eat",
    # Cleaning, cooking and bedtime, where the word is a verb and not a noun: the mattress
    # answer's step is "Scrape up what you can" and the sleep answer's is "Walk them back every
    # time with the same short line", and with the verb unread the composer walked past the
    # instruction and quoted what came after it instead ("heat sets both the colour and the
    # smell" as the first thing to do), or found no step at all and answered a plea for tips with
    # "that's most of what I know on it". Only words whose noun is rare go in: "sand", "press" and
    # "carry" are also things, and read as an instruction they turn a list of kit into one.
    "scour", "flush", "vacuum", "hoover", "peel", "fold", "loosen",
    # Bedtime again, where the verb is the whole answer. "rock" and "wind" are left out on the
    # same test as "carry": each opens a sentence as a noun ("Wind chill makes it feel colder").
    "walk", "tuck", "settle", "swaddle",
    # The verbs the base opens an instruction on that were still missing. Each one is a sentence
    # the knowledge base itself starts with, so "Pay the debts that keep a roof over your head
    # first" (money), "Pack what you use least first" (moving flat), "Treat how they seem, not the
    # number" (a fever) is read as the step it is. Without them the step reader walked past the
    # instruction to a later
    # sentence, which is how "where do i even start" after the moving answer came back as "do one
    # room an evening" - the last thing in the answer, not the first.
    "treat", "pack", "pay", "photograph", "aim", "melt", "halve", "agree", "shut",
    "sort", "repair", "label", "install", "cancel", "plug", "restart", "reset", "scan", "reply",
    "spend", "bin", "tidy", "sell", "throw", "push", "answer", "mend", "rent",
    # "bring" opens an instruction as often as "put" does ("Bring a pan of water to a bare simmer
    # with a splash of vinegar, stir it into a gentle whirlpool and slide the egg in from a cup"),
    # and with it unread the poached-egg answer had no step at all: "where do i even start" was
    # answered "Everything I know on that one is in the answer above, and none of it is one job to
    # start with" to somebody whose answer opened on the job.
    "bring",
    # "Separate them first and deal with it when everyone is calm" is the children-fighting
    # answer's opening instruction, and with it unread "what do i do" after that answer reached
    # no step at all, so the greeting's ask-back answered: "Tell me what has gone on, even
    # roughly" to the person who had just said what had gone on. Found by reading the knowledge
    # base's own first sentences for the verbs this list does not have; the fifteen others the
    # same scan turned up (sow, brown, lift, complain, whisk, talk, allow, soften, beat, defrost,
    # fry, decide, count, mark) are a wash on the deck's 296 step-ask chats - 2 better, 1 wash,
    # 2 slightly worse - so they are not here.
    "separate",
))
# The step said back with what the answer said next. The lines used to promise a list ("then
# work down the list I gave you") whenever the answer gave more than one thing to do, but there
# was never a list on screen - one answer is not a list, and pointing at one that is not there
# reads as a bot that has lost the thread. The step is the whole of what a friend says next, so
# the line says that and stops.
# An answer can also give its move as a list without writing one as an instruction ("The things
# that work: same wake-up time every day, no caffeine after early afternoon"), and then the item
# is quoted as it was written, so the line around it must read without a verb in the step.
LIST_STEP_LINES = (
    "Start with the first thing on that list: {step}.",
    "The first one on that list: {step}.",
)
# The step and nothing else. Each of these used to end by pointing at the rest of the answer
# ("the rest of what I said follows from that", "the rest in the order I gave them"), which tells
# somebody who asked what to do first that there is more without giving it: the rest is on the
# screen a line above, and a friend answering "where do i start" says the step and stops.
STEP_LINES = (
    "{Step} first.",
    "{Step} - that is the first move.",
    "{Step}, before anything else.",
)
# The answer explained its own step after a colon ("Turn it off and keep it off: do not charge
# it"), and that explanation is the part a friend would say, so it is quoted whole and the line
# only introduces it. A template that ends on "first" cannot take it: the colon has already put
# the instruction first.
STEP_DETAIL_LINES = (
    "{Step}. That is the first move.",
    "{Step}. Start there.",
    "{Step}. Do that before anything else.",
)
# A step that already puts itself first does not want another "first" bolted on: the sink answer
# opens "Start with a plunger over the plughole with a little water in the bowl", and the line
# above made it ".. in the bowl first, then work down the list", which reads as a second first.
FIRST_ITSELF = re.compile(r"\b(?:start|begin|first)\b", re.I)
STEP_ALREADY_FIRST_LINES = (
    "{Step}. Nothing else before it.",
    "{Step}, and only that to begin with.",
    "{Step}, in that order.",
)
# A sentence that opens on a subject pronoun and runs on is the answer explaining something, not
# giving a step. "They take oxygen out of the water instead of the air: water goes in at the mouth,
# passes over the gills and the gills pull the oxygen out" describes how a fish breathes, and the
# piece after its colon, read on its own, is the instruction "Water goes in at the mouth" - which
# is what a person asking what to do about a goldfish on the bottom of the tank was told to do.
# The tell is the subject in front of the verb: an instruction has no subject, so a verb-shaped
# word that has one is the sentence's subject and not an order ("water" is what you do to a
# plant). A short piece in front of a colon is still a heading ("That's the one: split your time
# in three"), so only a piece too long to be one makes the sentence an explanation.
SUBJECT_OPEN = re.compile(r"^(?:they|it|it's|its|he|he's|she|she's|this|that|that's|these|those"
                          r"|there|there's|we|we're)\b", re.I)
EXPLANATION_WORDS = 5


def _is_an_explanation(sentence):
    """True for a sentence that says how something is, and so holds no step of its own."""
    text = sentence.strip()
    if not SUBJECT_OPEN.match(text):
        return False
    head = re.split(r":|,|;| - | \u2014 ", text, 1)[0]
    return len(head.split()) > EXPLANATION_WORDS


# The same answer, when it gave one thing to do and nothing after it: "work down the list I gave
# you" points at a list that is not there, and the person is owed the one step plainly.
STEP_ONE_LINES = (
    "{Step}, and take it from there.",
    "{Step}. That is the one to do today; the rest is waiting to see whether it shifts.",
    "{Step} - start with that, and tell me how it goes.",
)
# The step asked for a second time, when the answer above is where it already was given. Quoting
# it back says the same sentence twice, one turn apart: "Keep it plain and separate: one new food
# next to one they already eat" was the answer, and the next ask got the same words again with
# "That is the first move" on the end, which is the one thing STYLE.md forbids outright. What is
# left to say honestly is that the step has not changed - so the line says that and adds nothing.
STEP_KEPT_LINES = (
    "Still the same move, and nothing to add to it: it is small, and it is the one that counts today.",
    "That step stands - it is a thing to keep doing rather than a second thing to start.",
    "Nothing new from me on it. Do the first thing as I said it, and tell me how it goes.",
)
# A plea for tips is the one ask where the answer above still has something in it the person has
# not been handed: the step is the sentence they have just read, and the sentence after it is the
# part a friend picks out ("Roasting carrots or broccoli in a little oil makes them sweeter, and a
# dip to dunk turns it into a game"). Handing that over is news; handing the step back is the
# opening of the answer said a turn later.
ALSO_LINES = (
    "There is more in what I said: {other}",
    "One more from that answer: {other}",
    "The other half of it: {other}",
)
# A sentence of the answer that asks the person something is not the tip of the answer: "Tell me
# what is in the fridge and I will pick properly" is the bot's own question, and quoting it under
# "any tips" asks the person to answer what they have just been asked.
ASKS_THEM = re.compile(r"\b(?:tell me|let me know|say which|what have you|how ready)\b", re.I)
# The ask narrowed to one move on purpose ("just one thing to start", "where do i start"): the
# person already has the long answer and wants the one thing out of it, so the line hands that one
# thing over instead of pointing at the rest, and it reads the same whether the step is short or a
# whole sentence - which is why it is chosen before the pools that read the step's own shape.
ONE_TURN_LINES = (
    "Just this: {Step}.",
    "The one thing: {Step}.",
    "Start with this: {Step}.",
    "Just the one, then: {Step}.",
)
# The same ask when the step already orders itself ("Start with run-walk: one minute of easy
# jogging") or carries its own explanation after a colon: a line that opens "Just this:" in front
# of either puts two starts on the same sentence, so these hand the step over as it stands.
ONE_TURN_PLAIN_LINES = (
    "{Step}. That is the one I would start with.",
    "{Step}. Just that one, and the rest can wait.",
    "{Step} - the one to do today, and the rest will keep.",
)
# The one thing was asked for and the answer above wrote no move at all, so there is nothing to
# hand over and no list to point at: the answer was the whole of it, and the reply says so rather
# than reading the ask back as a fact it has noted.
ALL_OF_IT_LINES = (
    "That answer is the whole of what I have on it, and there is no single first move in it: tell "
    "me which bit you want and I will take that one further.",
    "Everything I know on that one is in the answer above, and none of it is one job to start "
    "with. Say which part matters most and I will come at it from there.",
)
# The bot's last line was its own question, and the person answered it with a bare ask instead.
# Quoting that question as a step is what this composer used to do ("Do you want to tell me what
# has made it like that?, and take it from there"), and there is no instruction in it to quote,
# so what is left is to hand the question back kindly: the offer it made still stands.
QUESTION_BACK_LINES = (
    "Nothing to do on my side, honestly - whatever comes to mind about it first is the useful bit.",
    "No steps from me yet. Take the question in your own time, and start with whatever is loudest.",
    "There is nothing to do about it until we have looked at it - so start there, in your own time.",
)
# The question the bot asked is itself the thing to do, when it was about the thing: "my career is
# stuck" / "what should i do" came back with "Nothing to do on my side", a shrug under a bot line
# that had just asked what it was like. A friend would say which of the two to answer, and the
# answer's own question is the one concrete thing on the table.
#
# Said as an offer, not as a turn to be taken. The pool used to open "Your turn on the one thing I
# asked" - a line about the mechanics of the conversation, which no friend says, and which
# STYLE.md rules out twice over ("no lectures", and a reply that would fit any message is a
# failure) - and nine of the deck's bare "what should i do" turns got a line from it. The
# question asked back is worth keeping, because it is the one thing on the table that earns a step:
# these lines keep it and say what answering it buys, which is the same content without the telling
# off.
ASKED_FIRST_LINES = (
    "I can be specific if you tell me this much: {q}? Even a line is enough.",
    "One thing and I can be concrete: {q}?",
    "Tell me this and I can say something useful: {q}?",
)
# The same, when the bot's question was only an offer to help ("Is there anything you'd like a
# hand with?"): the offered hand is taken, and the person is asked for the one thing itself.
OFFER_TAKEN_LINES = (
    "Yes - the one thing that is bothering you most, in your own words, and I will start there.",
    "Then give me the thing itself. One sentence is enough, and I will pick the first step from it.",
    "Go on then: name the one part that is worst, and we will take it from there.",
)
SEE_NOW_LINES = (
    "See someone if {when}. Before that, what I said above is the plan.",
    "Not yet, unless {when}. If that happens, get it looked at rather than waiting.",
    "The point where it wants a person is if {when}. Until then, what I said above is the plan.",
)
SEE_ANYWAY_LINES = (
    "That one is a visit rather than a wait, so yes - get it looked at.",
    "Yes. Ring them rather than waiting on it, and say what you have noticed so far.",
    "Nothing to sit on there: that is one to get looked at.",
)
# The answer set the threshold as a thing rather than as a clause ("Blood in it, breathlessness or
# three weeks of it is a reason to ring the surgery"), so it cannot be read after an "if": "See
# someone if blood in it". These name the thing itself as what would change the answer.
SEE_STATED_LINES = (
    "Nothing there needs anyone today. That changes with {when}.",
    "Not yet. The point where it wants a person: {when}. Short of that, what I said above is the "
    "plan.",
    "What would change that: {when}. Until then, what I said above is the plan.",
)
# The answer told them to do nothing, and named the change that would matter. Saying "nothing to
# do" is only honest with that condition in the same breath.
NOTHING_LINES = (
    "Nothing you need to do yet - it matters if {when}.",
    "Nothing to do for now. That changes if {when}.",
    "No steps to take: what I said only changes if {when}.",
)
SEE_NONE_LINES = (
    "Nothing in what I said needs anyone today. If it has not settled in a week or so, that "
    "changes.",
    "Not yet. Give what I described a few days; if it is no better, that is when to ask.",
)
POOLS = (NO_LINES, DO_LINES, YES_LINES)


# Every line this composer can say. They are all kept in one place so a second follow-up
# question can look past them to the answer underneath.
# The pools this composer answers "is that bad" and "what should I do" from are all in here,
# including the ones it says without naming a step or a condition: "Nothing there is a warning on
# its own, that is the everyday fix for it. What would matter is a change in it" is this
# composer's own line, and reading it back as the person's answer turned their second "is that
# bad" into a fresh verdict in its own words rather than the same answer again.
OWN_LINES = tuple(
    line for pool in (NO_LINES, DO_LINES, YES_LINES, STEP_LINES, STEP_DETAIL_LINES,
                      STEP_ONE_LINES, STEP_ALREADY_FIRST_LINES, STEP_KEPT_LINES, SEE_NOW_LINES,
                      SEE_ANYWAY_LINES, SEE_STATED_LINES, SEE_NONE_LINES, NOTHING_LINES,
                      CONDITION_LINES, NOTHING_WARNED_LINES, ORDINARY_NORMAL, CARE_NORMAL,
                      CARE_NORMAL_UNKNOWABLE, CARE_NOW_NORMAL, DO_NORMAL,
                      NOTHING_WARNED_NORMAL)
    for line in pool
)


def _own_pattern(line):
    """A line of this composer as a pattern, with the step or the cause in it left open.

    They are templates, so "Keep it plain, and take it from there." does not contain "{Step}",
    and matching the template as it is written never finds the sentence the composer said. A
    second follow-up would then read the composer's own line back as if it were the answer
    behind it, and answer the answer.
    """
    parts = re.split(r"\{[A-Za-z]+\}", line)
    return ".+?".join(re.escape(part) for part in parts)


OWN_PATTERN = re.compile("|".join(_own_pattern(line) for line in OWN_LINES),
                        re.IGNORECASE)


# A line that only takes a fact the person gave ("Got it - he shares with his sister", "Noted: your
# sofa smells of dog"), left open where the thing they said goes. `bot/memory/ack.py` writes those,
# so its own frames are what says which lines they are: a reader that guesses from "Got it" reads
# "Right, so that hasn't helped. How is it now" as an acknowledgement too, and that line has
# something to say.
_ACK_PATTERN = None
# How long a line may be and still be only an echo: `bot/memory/ack.py` keeps the thing they said
# to a clause or two, so anything longer has a tail of its own ("he shares with his sister - how's
# it going?" is nine).
ECHO_WORDS = 14


def takes_a_fact_back(said):
    """True when the line only says the bot heard, so the answer behind it is still the answer.

    "my son is 4 and wont sleep" / "he shares with his sister" / "any tips" was answered "Sure.
    What have you tried so far?", a plea thrown back at somebody the bot had just told what to do,
    because the acknowledgement sat between the ask and the answer it is about.
    """
    global _ACK_PATTERN
    if _ACK_PATTERN is None:
        from ..memory import ack
        frames = ack.FRAMES + ack.HABIT_TAIL + ack.GOING_TAIL + ack.EXPLAIN_TAIL
        _ACK_PATTERN = re.compile("|".join(_own_pattern(line) for line in frames), re.IGNORECASE)
    text = " ".join(str(said or "").split())
    if not text or not _ACK_PATTERN.match(text):
        return False
    # The acknowledgement carries the person's own words and nothing else: "Got it - you're 40"
    # taking "im 40" is one, and "Got it - so start with the wake-up time and give it two weeks"
    # is an acknowledgement that has gone on to answer, so the step in it must not be read past.
    words = re.findall(r"[a-z']+", text.lower())
    return len(words) <= ECHO_WORDS and not any(word in IMPERATIVES for word in words)


def _say(pool, memory, flat, **gaps):
    """One line from a pool of templates, chosen after its gaps are filled in.

    pick() drops the reply just given, but the pool holds "{Step}, and take it from there." and
    the reply just given was "Keep it plain, and take it from there.", so the two are never equal
    and a person asking twice got the same sentence twice running. Filling the gaps first is what
    lets the never-repeat rule see them.
    """
    rendered = list(pool)
    for name, value in gaps.items():
        for template, gap in ((name, "{%s}" % name),
                              (name[:1].upper() + name[1:], "{%s}" % (name[:1].upper() + name[1:]))):
            filled = value if gap == "{%s}" % name else value[:1].upper() + value[1:]
            rendered = [line.replace(gap, filled) for line in rendered]
    return pick(rendered, memory, flat)


def _a_report_line(said):
    """Whether the bot's own last line was the composer's report on the advice it had given.

    The report lines are spoken under whichever module proposes them (`greeting` under the floor),
    so the module name says nothing and the composer's own list of them does. A doubt two turns
    after the answer - "im 34 and i still bite my nails" / "ive tried everything" / "is that bad" -
    is about the nails, and the report in between is not the answer it is about.
    """
    try:
        from .fallback import is_a_report_reply
    except Exception:  # noqa: BLE001 - a reading that fails is a reading not made
        return False
    return bool(is_a_report_reply(said))


def _flat(text):
    return " ".join(str(text or "").lower().replace("\u2019", "'").split())


# Only a knowledge answer is read back. "im 6 weeks pregnant and cant keep anything down" is
# answered by a referral to a GP, and "should i be worried" after it must not be told "no": the
# answer to that line was already the careful one, and this composer has nothing to add to it.
READABLE = frozenset(("answers", "chat", "trouble", "fallback", "greeting"))
# A step is the instruction as the answer wrote it, and answers write them longer than a handful
# of words: "turn the boiler off at the wall switch" is eight, and "three times a week do
# sit-to-stands" opens with when it is done rather than with the verb.
# The lines this composer may not read a follow-up from: a safety answer has already said what to
# do, and a death, a grief or an emergency is not a topic to point back at ("do the first thing I
# said" after "ring 999" is the wrong sentence, and after a condolence it is worse).
UNREADABLE = frozenset(("safety", "urgent", "loss", "grief"))


# The module names a composer's line is spoken as. A composer line is the fallback module
# whichever helper wrote it, so the module name cannot tell one composer from another; the text
# has to be read when it matters (see `_last_reply`).
COMPOSED = frozenset(("greeting", "fallback"))
# The pools that rule on a doubt the person asked about, as opposed to the ones that talk about
# the answer it followed (NOTHING_WARNED_LINES), ask for more (FLOOR_LINES, NEUTRAL_ASK_LINES) or
# hand the question back. The arbiter reads this list (bot/modules/arbiter.py, `_reads_the_doubt`):
# on a bare doubt an entry that only inherits the topic stands down to a reply that reads the
# doubt, and this is what "reads" means - the composer saying what it thinks about the thing, in
# one of the pools that does that. A pool that gains a ruling line is read as one with no change
# in the arbiter; a note or a floor never is, however it is worded.
RULED_BY_THE_COMPOSER = (
    ORDINARY_NORMAL, CARE_NORMAL, CARE_NORMAL_UNKNOWABLE, CARE_NOW_NORMAL, DO_NORMAL,
    CONDITION_NORMAL, NOTHING_WARNED_NORMAL, NO_LINES, BOTH_LINES, DO_LINES, CONDITION_LINES,
    MET_LINES, MET_CONDITION_LINES, METHOD_OK_LINES, YES_LINES, BACKSTOP_LINES, SOON_LINES,
    HELPED_LINES, MONEY_TROUBLE_LINES,
)


def rules_on_the_doubt(said):
    """True when a reply is one of the composer's lines that rules on a doubt, for the arbiter.

    The pools carry no slots in the part that tells them apart - a {when} or {topic} comes later
    in the sentence - so the first 40 characters are compared, the way `fallback.is_a_hedge` reads
    its pools, and a pool that reflows its wording keeps working.
    """
    said = str(said or "").strip()
    if not said:
        return False
    head = said[:40].lower()
    return any(head == line[:40].lower() for pool in RULED_BY_THE_COMPOSER for line in pool)


# A follow-up asking what to do next is answered from the answer the person was given a turn
# ago. The step is in that answer and nowhere else, so a line that comes back to it carries a run
# of its words; an entry that shares the conversation's topic but none of those words is a
# different fact about the same subject, and answering with it reads as a change of subject.
RUN = 4
_WORD = re.compile(r"[a-z0-9']+")


# The words that follow a noun and never an instruction: "water at the front" is about water
# though `water` is a verb in IMPERATIVES, and an answer that opens on it is a diagnosis, not a job.
_AFTER_A_NOUN = frozenset("at in on from of for to with by near under behind over into about".split())


def opens_on_a_job(reply):
    """True when a reply opens on an instruction ("Ring or log in and ask why it went up").

    Read by the arbiter beside `carries_the_answer`, on the turn where a bare follow-up asks what
    to do next: an entry that opens on a job is already answering that question, so it keeps the
    turn over the step from the answer a turn ago. An entry that opens on a fact ("Five a day is
    400g", "The things that work: same wake-up time every day") is telling the person something
    else about the subject, and the step they asked for is in the answer they already have.
    """
    flat = _flat(reply)
    if not flat:
        return False
    head = re.split(r"[:;.!?]", flat, 1)[0].strip(" ,-")
    words = _WORD.findall(head)
    if not words or words[0] not in IMPERATIVES:
        return False
    if len(words) > 1 and words[1] in ("me", "us"):
        # "Tell me what has gone on, even roughly, and I will help you work out the first step"
        # opens on a verb from the list, but the job in it is not the person's: it asks them for
        # the thing, which is why "say" and "name" were left out of IMPERATIVES. After "my
        # youngest and my eldest fight all the time", "what do i do" was answered with that line
        # instead of the step the answer already had ("You've got it: Separate them first and deal
        # with it when everyone is calm"), so the person was asked to tell the bot what they had
        # just told it. "Tell the school the same day" is a real job and is untouched.
        return False
    return len(words) == 1 or words[1] not in _AFTER_A_NOUN


def carries_the_answer(reply, memory):
    """True when `reply` comes back to the answer the bot gave a turn ago.

    Read by the arbiter (bot/modules/arbiter.py) on a turn that asks what to do next: the
    composer's step line keeps the answer's own opening ("Keep it plain, and take it from
    there." after "Keep it plain and separate: ..."), and a hand-back keeps its first sentence,
    so both share a run of four words with it. An entry that only shares the topic shares none:
    "Five a day is 400g, and a portion is a handful" after an answer about a child refusing veg.
    Wording only, and nothing about the subject, so no entry can be read as a repeat it is not.
    """
    if _kept_step(reply):
        # The step has not changed, and the line says so instead of saying it again: "Still the
        # same move, and nothing to add to it" is about the answer above by construction, and it
        # shares none of its words because repeating them is the fault it exists to avoid. It is
        # still a line that answers from the answer, so the arbiter is told the same thing about
        # it as about a quoted step.
        return True
    said = _WORD.findall(_flat(_last_reply(memory)))
    words = _WORD.findall(_flat(reply))
    if len(said) < RUN or len(words) < RUN:
        return False
    runs = {" ".join(said[i:i + RUN]) for i in range(len(said) - RUN + 1)}
    return any(" ".join(words[i:i + RUN]) in runs for i in range(len(words) - RUN + 1))

# A turn that only says the person was heard, with nothing about the thing itself: the echo the
# fallback hands back ("Got it - she likes pasta.", "Got it. Is there anything you'd like a hand
# with?", "Noted."). It is not the answer a follow-up reads, and it does not put the answer out of
# reach either: "my washer bangs" / "only when it spins" (echoed as "Got it. Is there anything
# you'd like a hand with?") / "is that bad" got a search hedge, though the washer answer was one
# turn back. One such turn is looked past and not a run of them, so a person who has moved on
# still gets the line that was just said.
PUNT_START = re.compile(r"^(?:got it|noted|ok(?:ay)?|alright|all right|right|fair enough|"
                        r"i see|makes sense|understood|sure|cool)\b", re.I)
PUNT_OFFER = re.compile(r"\b(?:is there anything|anything else|what else|let me know|"
                        r"anything (?:i|we) can do)\b", re.I)


PUNT_CHAT = re.compile(r"\b(?:good luck|sounds good|fair enough|nice one|lovely|alright then|"
                      r"ok then|well then|makes sense|hope (?:it|that) (?:goes|works))\b", re.I)


def _a_punt(last):
    """True for a bot turn that said nothing about the thing being discussed."""
    module = last.get("module")
    if module not in ("greeting", "fallback", "chat"):
        return False
    said = _flat(last.get("bot"))
    if not said or not PUNT_START.match(said):
        return False
    if module == "chat" and not PUNT_CHAT.search(said):
        # The chat pool also answers with something about the thing ("Keep it plain and separate:
        # one new food next to one they already eat...") and that is an answer, not an echo. Only
        # its goodbye and its nod count here.
        return False
    if PUNT_OFFER.search(said):
        return True
    # A question is something said, even a short one ("Right. What have you tried so far?"), so
    # only the echo and the bare nod are shrugs.
    if "?" in said:
        return False
    return len(said.split()) <= 8


def _skip_the_derived(turns, memory):
    """The turns to read when the last one was read off the answer behind it.

    A frequency line ("Every night, then. That is enough to get it looked at") and a healing line
    ("Most back pain is muscular and settles in two to six weeks", said of the card above it) are
    both taken from the answer before them rather than from anything of their own, so the card is
    what a doubt this turn is about. Both are skipped, and no other turn is.
    """
    if not isinstance(memory, dict) or len(turns) <= 1:
        return turns
    if memory.get("frequency_reply") or healing.derived(memory):
        return turns[:-1]
    return turns


def answers_the_ask(clean, memory):
    """True when there is a knowledge answer behind the ask for this composer to read.

    A bare "is that bad" has no content of its own: the answer to it is in the bot's last line,
    and that line is worth standing aside for only when it is an answer about a thing. After a
    condolence ("my dad died last week") or a mood ("i feel low") the last line is neither, this
    composer can only shrug, and a search hedge handed to someone who has just said their dad
    died is worse than the line the chat pool would have given. The gate is the same test
    reply_for makes for itself, asked from outside: the last readable turn was a knowledge answer
    and this composer has a verdict to give about it. "how do i descale the kettle" / "is that bad"
    is advice the person asked for, not a fault, and reply_for stands aside for it - so the chat
    pool keeps that turn rather than leaving a search hedge where it had a warm line.
    """
    if _last_module(memory, past_the_nod=True) != "answers":
        return False
    return reply_for(clean, memory) is not None


def _the_news_just_before(memory):
    """Whether the turn before this ask was hard news, not a feeling to sit with.

    A comfort line that ends in a question is an offer about how the person is doing when the line
    before it was about them ("im feeling really low"): there is nothing more concrete to say than
    the first step of a bad day, so the question comes back. When the line before it was news that
    names a thing ("bailiffs turned up", "i got a letter about a court date"), the ask that follows
    is about the thing, and whoever read the news answers it.
    """
    if not isinstance(memory, dict):
        return False
    try:
        from .badnews import reads_as_bad_news
    except Exception:  # noqa: BLE001 - a reading that fails is a reading not made
        return False
    turns = memory.get("turns") or []
    turn = turns[-1] if turns and isinstance(turns[-1], dict) else {}
    said = " ".join(str(turn.get("user") or "").lower().split())
    return bool(said) and reads_as_bad_news(said)


def _last_reply(memory, past_the_nod=False, past_the_verdict=False):

    """The last answer of the bot's this turn is a follow-up to, or "" if there is not one.

    It is the bot's own last line whichever module wrote it, because the step a person asks for
    is in that line and nowhere else: "im getting headaches every afternoon" is answered by the
    composer's warm line, and "what should i do" after it used to get "a quick search online".
    A safety or urgent answer is not read back (it has already said what to do now), and
    neither is a condolence.

    My own verdict line is not a change of subject: "the boiler pressure is low" / "is that bad"
    / "is that going to get worse" is still the boiler, so the question is read from the answer
    behind the verdict rather than dropped.

    A cause handed back by another composer is the same case: "the boiler keeps making a banging
    noise" / "why is that" / "is it dangerous" is still the boiler, so the reason line is read
    past to the answer it came out of. Both are composer lines, spoken as the fallback module,
    which is why the text decides it rather than the module name.
    """
    punt_line = ""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    # A frequency line and a healing line answer the turn before them rather than this question
    # (see `_skip_the_derived`): reading one as the answer hands the condition in it back as
    # "Nothing to do for now", where the trouble answer behind it is the one to read.
    turns = _skip_the_derived(turns, memory)
    for index in range(len(turns) - 1, -1, -1):
        last = turns[index]
        before = turns[index - 1] if index else None
        if not isinstance(last, dict):
            return punt_line
        module = last.get("module")
        said = str(last.get("bot") or "")
        if module in UNREADABLE:
            return punt_line
        if module == "chat" and OWN_PATTERN.search(_flat(said)):
            continue  # this composer's own line: the answer behind it is what to read
        if _a_report_line(said):
            continue  # the composer's report on the answer: the answer behind it is what to read
        if module in COMPOSED and why.is_a_reason_line(said):
            continue  # a cause handed back is the answer above, not a new one
        if module in READABLE and takes_a_fact_back(said):
            continue  # only taking a fact back: the answer behind it is the one to read
        if A_STEP_ASK.match(_flat(last.get("user"))) and last.get("module") != "answers":
            # Asking for the first step is not a change of subject, and the answer to it is not
            # always the card quoted back: "im getting headaches every afternoon" / "what should
            # i do first" comes back as a chat line, so the quote test above does not see it, and
            # the bare doubt after it read the line "what should i do first" - which names nothing
            # - and fell through to the chat pool's "Sounds good." The answer a doubt about the
            # headache is about is the headache card, one turn further back.
            #
            # Only a step the knowledge base did not answer is stepped past. A card answers the
            # ask for a step too, sometimes with a threshold the card above did not put the same
            # way ("Try a spoonful of honey before bed ... or three weeks of it is a reason to
            # ring the surgery"), and that answer is what the doubt is about: skipping it turned
            # "Not yet. The point where it wants a person: blood in it, breathlessness or three
            # weeks of it" into the shorter condition the card above writes.
            continue
        if _a_punt(last):
            # A turn that only said the person was heard is not an answer to read. It is still
            # the last thing said, so a walk that wants the line itself takes it; a walk that
            # wants the answer a doubt is about looks past one echo, and only to the knowledge
            # answer behind it. A run of echoes is not looked past at all: a person who has said
            # two lines since the answer has moved on from it.
            if not past_the_nod or punt_line:
                return said if not past_the_nod else punt_line
            punt_line = said
            continue
        if past_the_verdict and _only_a_verdict(last.get("user")):
            # The bot's line here is a comment on the news ("Annoying. Is it a quick fix or a
            # whole thing?"), not the answer it belongs to: the answer is the turn before it, and
            # the question in the comment is conversation, not a step the person has to take
            # first. Read past it exactly as a recap is read past.
            continue
        if _is_an_echo(last):
            continue  # a line said back is not an answer: the answer behind it is what to read
        if before is not None and _is_a_recap(last, before):
            # A step quoted out of the card above is that card said shorter, not new advice.
            # "what should i do first" after the laptop answer comes back as "The thing to do
            # first: Empty the Downloads folder and the bin.", and the doubt after it ("is that
            # safe") had nothing to read, so the chat pool gave "Sounds good." - the bot
            # agreeing that a full laptop is fine. The card behind the quote is the answer.
            continue
        if module in READABLE:
            if punt_line and module != "answers":
                return punt_line
            # The answer's own capitals, because the step is quoted out of it: "Run a hot 60C
            # service wash" came back as "60c" when the reply was flattened to lower case first,
            # and a temperature is not a word to lower.
            return said
        return punt_line
    return punt_line


# The words a line back to the person is made of. An echo is the bot saying the person's own
# point back to them, which is the right thing in a conversation and no answer at all:
# "my cat keeps bringing in mice" / "hes 2" / "is that normal" was read from "Got it - he's two",
# so there was nothing to give a verdict on and the question got the search hedge. What is left
# of an echo once these words and the person's own words are taken out is nothing.
ECHO_FILLER = frozenset("""
a an the and or so but then too that thats that's this it its it's is are was were be been
i we you he she they his her their our your yours mine theirs
my me us them him got get note noted right ok okay
sure yes yeah no not ah oh mm good fine well still just only also very really quite
know sounds thanks hope glad
have has had do did does for to of in on at with about from by as if
one two three four five six seven eight nine ten eleven twelve half twice both all some
""".split())


def _words(text):
    """The words of a line, lowercased and bare, for the echo test below.

    The apostrophe goes, so "he's two" and the person's "hes 2" are the same two words.
    """
    return [word.replace("'", "") for word in re.findall(r"[a-z0-9']+", str(text or "").lower())]


def _is_an_echo(turn):
    """True when the bot's line only says the person's own words back.

    Short on purpose: a long line has said something of its own even if it repeats a lot of the
    person's words (a paraphrase of what they described is an answer), so only a line of a dozen
    words or fewer that adds nothing is skipped.
    """
    said = _words(turn.get("bot"))
    theirs = set(_words(turn.get("user")))
    if not said or not theirs or len(said) > 12:
        return False
    return all(word in ECHO_FILLER or word in theirs for word in said)


# The words a recap is made of on top of the answer it quotes: the lead-in, and the words for
# saying the same thing again ("Same as before: ..."). A recap adds nothing of its own, so the
# only words allowed outside the answer above are these.
RECAP_FILLER = frozenset("""
thing things one ones first next step steps again before said same short version part bit
here that this it its is are was the a an and or of to for in on at with about from
""".split())


def _is_a_recap(turn, before):
    """True when the bot's line is the answer above, said shorter: a step quoted out of it.

    The quote is shorter than the card it came from and holds no word the card does not, apart
    from the lead-in ("The thing to do first:") and the words for saying it again. A line that
    brings a word of its own is an answer of its own, however much it repeats.
    """
    said = _words(turn.get("bot"))
    had = set(_words(before.get("bot")))
    if not said or not had or len(said) >= len(had):
        return False
    if before.get("module") != "answers":
        return False
    return all(word in had or word in RECAP_FILLER or word in ECHO_FILLER for word in said)


def _last_line_that_named_a_call(memory):
    """The last line when the answer the person is asking about named somebody to ring, or "".

    A safety answer is the first case - "my cat is having trouble breathing" / "is that serious"
    came back as the search hedge, because the verdict reading only reads a knowledge answer and
    a safety line is not one. Another module hands a line on with a call in it too: "my baby has
    a rash on her cheeks" is answered "Your health visitor or the 111 line will talk it through
    with you today", and the verdict question after it has the same answer. A knowledge answer
    never comes here - its own reading above is better than a yes - and a line that named nobody
    has no call to point back at.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    last = turns[-1]
    if not isinstance(last, dict):
        return ""
    if last.get("module") == "answers":
        return ""
    said = _flat(last.get("bot"))
    if not said or (_first(said, CARE) is None and REFER.search(said) is None):
        return ""
    return said


# The words that make a named call a call for today. A named ordinary professional is not one of
# them: "i bleed when i brush my teeth" is answered with a dentist, and "ringing is not an
# overreaction here, it is the whole point of it" over a dentist is a 999-shaped over-reaction.
URGENT_CALL = re.compile(
    r"\b(?:999|911|112|a&e|accident and emergency|ambulance|111|out of hours|straight away"
    r"|right away|today|tonight|do not wait|dont wait|immediately)\b", re.I)


def _a_call_for_now(said):
    """True when this line names somebody to ring or care for now, with no "if" on it.

    "Sorry to hear it — go easy on yourself today, and see someone if it's not shifting in a few
    days" is a greeting's own line, and the referral in it is fenced: "i feel dizzy" / "is that
    bad" was told "ringing is not an overreaction here, it is the whole point of it" for a
    dizziness that is ordinary. A cue with a condition after it in its own sentence is not a call
    for now, and the verdict path carries on without it.
    """
    if _care_for_now(said):
        return True
    for sentence in re.split(r"(?<=[.!?]) ", str(said or "")):
        found = REFER.search(sentence)
        if not found:
            # An answer can name who without a verb in front of them: a safety line says what
            # the thing needs and who it is, "That needs a real person today - your midwife, GP
            # or 111 - because sickness that stops you keeping anything down can leave you
            # dehydrated", and the bare "is that bad" after it was the fallback's "Keep an eye on
            # it and tell me if anything changes": a doubt answered at a strength the answer
            # never asked for, under a call that said today. When did the answer say to go is
            # the question, and a trade and a time in one sentence is the answer saying now -
            # unless the trade itself is fenced ("if it is still there today, see your GP").
            trade = TRADE.search(sentence)
            if trade is None:
                continue
            if LATER_CONDITION.search(sentence[:trade.start()]) is not None:
                continue
            if TIME_NOW.search(sentence) is not None:
                return True
            continue
        if not LATER_CONDITION.search(sentence[found.start():]):
            return True
        # A time in the same sentence makes the referral a today one whatever fence follows it:
        # "ring 999 or 911 straight away, and keep the container ... ; 111 gives poisons advice
        # if they seem well" is an order for now, and the "if" belongs to the poisons line, not
        # to the call. `_condition_after_care` reads a fenced referral the same way.
        if TIME_NOW.search(sentence[found.start():]):
            return True
    return False


# A sentence that names the whole answer as an emergency, rather than naming a condition that
# would be one. The order is already given, so it is a call for now with no time word needed:
# "That's an emergency: ring 999 or 911", "That's an ambulance job", "Treat this as an emergency".
EMERGENCY_ORDER = re.compile(
    r"^\W*(?:that's|that is|this is|it's|it is)\s+(?:an?\s+)?(?:emergency|ambulance\b(?: job)?)"
    r"|^\W*treat (?:this|that) as (?:an? )?(?:emergency|ambulance)", re.I)
# The other way an answer gives the order in its opening clause: "Ring 999 or 911 and stay on the
# line." It is read only where nothing after it fences it - "Ring 999 if he goes blue" is the
# answer's condition, not its instruction, and reading that as a call for now gives a doubt on top
# of it the emergency reading for a thing the person may not have.
EMERGENCY_CALL_OPEN = re.compile(r"^\W*(?:ring|call|dial|phone)\s+(?:999|911|112|an ambulance)\b", re.I)


def _the_call_sentence(said):
    """The sentence that carries the call this answer makes, or the answer itself.

    A long answer puts its fence and its call in one breath: "a bent limb, bone through the skin or
    numb fingers is 999, otherwise get it checked at A&E or a minor injuries unit today" is a call
    for today, and reading the whole answer for the emergency word made it a 999. The call is the
    first sentence whose referral is not fenced, so that sentence is what "how urgent" is read
    from.

    A sentence that opens by naming the whole answer as an emergency has already given the order
    and needs no time word to say when: "That's an emergency: ring 999 or 911 and stay on the line"
    is a call for now, and so is "Treat this as an emergency and ring 999". Without that, the
    safety lines that do not say "straight away" were read as a call for today instead, and a
    doubt about one was answered "Not an emergency by the sound of it" over an answer that had
    just said to ring 999.
    """
    for sentence in re.split(r"(?<=[.!?]) ", str(said or "")):
        if EMERGENCY_ORDER.match(sentence) is not None:
            return sentence
        opening = EMERGENCY_CALL_OPEN.match(sentence)
        if opening is not None and LATER_CONDITION.search(sentence[opening.end():]) is None:
            return sentence
        # Only a sentence that says when is a call for now: "a cut that gapes open, is deep, or
        # keeps bleeding through the cloth needs a nurse or A&E" names a place and no time, and
        # it is the answer's condition rather than its instruction.
        if TIME_NOW.search(sentence) is None:
            continue
        found = REFER.search(sentence)
        if found is not None:
            tail = sentence[found.start():]
            if LATER_CONDITION.search(tail) is None or TIME_NOW.search(tail) is not None:
                return sentence
            continue
        trade = TRADE.search(sentence)
        if trade is None:
            continue
        if LATER_CONDITION.search(sentence[:trade.start()]) is not None:
            continue
        return sentence
    return ""


def _last_person_line(memory):
    """The person's own last line, skipping the echoes a doubt ask follows."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    for last in reversed(turns):
        if not isinstance(last, dict):
            return ""
        said = _flat(last.get("user"))
        if not said:
            continue
        return said
    return ""


def _the_worst_thing_they_said(memory):
    """Whether the thing this turn is a doubt about is a loss or a diagnosis, not a fault.

    The person's own last line decides it: "my dad has cancer" is the thing they brought, and
    "is that bad" on top of it is about that. A body in the line is still a body, so the doubt
    path's own readings come first wherever there is something to read.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ""
    for last in reversed(turns):
        if not isinstance(last, dict):
            return False
        said = _flat(last.get("user"))
        if said:
            return said if HARD_NEWS.search(said) else ""
    return ""


def _as_written(line):
    """The line as it was meant, for the ask patterns that read it: (spelled right, said out).

    "wat shud i cook 2nite" is "what should i cook tonight", and a misspelling is the person's
    ordinary way of writing rather than a rare slip: the understanding engine repairs every line
    and the composer was reading the raw text, so the same sentence spelled differently took two
    different routes through this file. The first return is that repair with the words in the
    order they were typed and the punctuation kept (`plain`); the second is the fuller reading
    (`norm_text`), which also expands "gonna" and "im". A line with nothing to repair comes back
    as it went in, and a reading that fails leaves the arms exactly as they were.
    """
    text = _flat(line)
    if not text:
        return "", ""
    try:
        read = normalise(text)
    except Exception:  # noqa: BLE001 - a reading that cannot run adds nothing
        return "", ""
    return _flat(read.get("plain") or ""), _flat(read.get("norm_text") or "")


def _a_thing_they_own(memory):
    """The noun for the thing whose answer this doubt is about, or "" for a body or a person.

    Read off the line the answer replied to, so it is the subject the person brought and not a
    word in the doubt, and only when that line names no body: "my boiler is making a knocking
    noise" is a machine, "my knee clicks" is not.
    """
    line = _the_line_behind(memory)
    if not line:
        return ""
    low = _flat(line)
    if A_BODY_WORD.search(low):
        return ""
    found = A_THING_THEY_OWN.search(low)
    return found.group(0).lower() if found else ""


def _a_person_they_know(memory, said):
    """The person whose situation this doubt is about, or "" when it is their body or nobody.

    Read off the line the answer replied to, and only when that line is about contact, company or
    quiet rather than a symptom: "my mum is 79 and lives on her own" is a week, "my baby is not
    feeding" is not. A fenced care in the answer ("if they seem low for weeks, help them see a GP")
    is the answer's own later step, not a referral now, so the verdict points at both halves.
    """
    line = _the_line_behind(memory)
    if not line:
        return ""
    low = _flat(line)
    if A_SYMPTOM_WORD.search(low):
        return ""
    if not A_PERSON_THEY_KNOW.search(low) or not A_RELATION_TROUBLE.search(low):
        return ""
    return "person"


def _the_line_behind(memory):
    """The person's own line that the answer this turn is a follow-up to replies to, or "".

    Read with the same walk `_last_reply` does, so the two agree about which answer is being
    followed up: a chat line of this composer's own is stepped past, and a safety answer ends it.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    # The same skip `_last_reply` makes: a frequency or healing line is about the turn before it,
    # so the person's line this turn follows is the one the trouble answer replied to, not "its
    # every night". Without this the two walks disagree and "is it worth seeing someone" loses the
    # referral in the cough answer.
    turns = _skip_the_derived(turns, memory)
    for index in range(len(turns) - 1, -1, -1):
        last = turns[index]
        if not isinstance(last, dict):
            return ""
        module = last.get("module")
        if module in UNREADABLE:
            return ""
        if module == "chat" and OWN_PATTERN.search(_flat(last.get("bot"))):
            continue
        if _is_an_echo(last):
            continue  # a line said back is not an answer: the line behind it is the one to read
        if A_STEP_ASK.match(_flat(last.get("user")) or "") and module != "answers":
            # Asking for a step is not a subject of its own, so it is not the line a doubt about
            # the answer is about (see the same skip in `_last_reply`, including why a step the
            # knowledge base answered is not stepped past).
            continue
        if index and _is_a_recap(last, turns[index - 1]):
            # A step quoted out of the card above was asked for, not asked about: "my laptop is
            # full" / "what should i do first" / "is that safe" is a doubt about the card, and
            # the ask-for-a-step in between is not the thing the doubt is about. The same walk
            # `_last_reply` makes, so the two agree on which answer is being followed up.
            continue
        if module in READABLE:
            return _flat(last.get("user"))
        return ""
    return ""

def _the_plan_they_brought(memory, back=2):
    """The person's own plan or choice among their last few lines, or "".

    A plan is rarely the line immediately before the check. "im thinking of getting a dog" /
    "but i work all day" / "is that fair" is one thought in three lines, and the line behind the
    check is the *detail*, which no plan reader matches - so the arms below stood aside and the
    acknowledgement pool ended the conversation ("Sounds good."). Two lines is the reach: the plan
    and one line said about it. Further back and the check belongs to whatever was said last.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ""
    seen = 0
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        said = _flat(turn.get("user"))
        if not said:
            continue
        seen += 1
        if seen > back:
            break
        if A_PLAN.search(said) or CONSIDERING.search(said):
            return said
    return ""


A_CHECK_ON_A_PLAN_LINES = (
    "Say which part you are unsure about and we can weigh it up together.",
    "Tell me the bit that is nagging you and I will go through it with you.",
    "Which part of it is the one you keep coming back to? That is usually the part worth settling "
    "first.",
    "Put the two sides next to each other and the answer usually shows itself: what it costs you, "
    "and what it gives you. Which one is it for you?",
)
# The handful of words a check on a plan is made of: "is that fair", "is that right", "does that
# make sense", "does that sound ok". They are the same ask as "is that ok" - the person putting
# their own plan before somebody before they act on it - and they are not a question about how
# dangerous or how usual anything is, so the severity pools below are the wrong answer to them:
# "getting a dog / but i work all day / is that fair" was told "Nothing in that sounded like a
# warning sign", which is a ruling on a dog rather than on a fair working day.
A_CHECK_ON_A_PLAN = re.compile(
    r"^(?:and |so |but )?(?:is|was|does|did|do) (?:that|this|it) "
    r"(?:be |sound |look |seem )?"
    # "right" is deliberately not here. "is that right" after the bot has said something about
    # the world is the person checking the claim ("Cornwall in May ... the weather is usually
    # decent" / "is that right" -> "That's right."), and the plan pool's "that is yours to
    # decide" answers the wrong question. "fair" and "make sense" are asks about the plan itself.
    # "sensible" and "reasonable" are deliberately not here: a check on a plan written that way
    # already has a good answer of its own ("im going to ask my boss for a pay rise" / "does that
    # sound sensible" -> "Yes, that is a reasonable way to do it - wanting to ask your boss for a
    # pay rise is worth doing"), and this gate would take the turn from it and hand back the
    # general question instead.
    r"(?:fair|ok|okay|alright|all right|fine|"
    r"make (?:any )?sense|sound (?:ok|okay|fine|fair))(?: then| though)?$")

# A plan is not a complaint. "im thinking of getting a cat" then "is that bad" asks whether the
# plan is a bad idea, and the answer it follows is a shopping list ("plus a vet visit booked for
# the first week") whose "vet visit" is an errand, not a referral about an ache. Only getting or
# buying something counts, so "i want to lose weight" and "im going to be sick" keep their reads.
CONSIDERING = re.compile(
    r"\b(?:thinking (?:of|about)|considering|planning (?:to|on)|looking to|hoping to|"
    r"(?:i|we) (?:really )?(?:want|need|fancy)|want(?:ing)? to)\b[^.]{0,30}?"
    r"\b(?:get|getting|buy|buying|adopt|adopting|rescue|rescueing|book|booking)\b", re.I)


def _considering(memory):
    """Whether the line before this one is about a thing the person is considering getting."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        said = _flat(turn.get("user"))
        if said:
            return bool(CONSIDERING.search(said))
    return False


def _the_last_line_was_mine(memory):
    """True when the bot's last line is a line of this composer's, whichever module filed it.

    The pools that answer a question a second time ("Same answer as a moment ago: nothing in what
    I said was a warning sign") are only true when the bot itself said the answer the first time.
    Reading the words alone is not enough, because these lines are templates: `{Step} first.` fits
    any sentence that ends in that word, and a knowledge card that says "the last resort, not the
    first" is not a verdict of mine.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    for last in reversed(turns):
        if not isinstance(last, dict):
            return False
        module = last.get("module")
        if not module:
            continue
        return module == "chat" or module in COMPOSED
    return False


def _last_module(memory, past_the_nod=False):
    """The module that wrote the answer `_last_reply` reads, or "" if there is not one."""
    punt_module = ""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    turns = _skip_the_derived(turns, memory)
    for index in range(len(turns) - 1, -1, -1):
        last = turns[index]
        if not isinstance(last, dict):
            return punt_module
        module = last.get("module")
        if module in UNREADABLE:
            return punt_module
        if module == "chat" and OWN_PATTERN.search(_flat(last.get("bot"))):
            continue
        if _a_report_line(last.get("bot")):
            continue  # the composer's report on the answer: the answer behind it is the module
        if module in COMPOSED and why.is_a_reason_line(_flat(last.get("bot"))):
            continue
        if module in READABLE and takes_a_fact_back(last.get("bot")):
            continue  # only taking a fact back: the answer behind it is the module to read
        if A_STEP_ASK.match(_flat(last.get("user"))) and module != "answers":
            continue  # a step ask is not a subject of its own: same walk as `_last_reply`
        if _a_punt(last):
            # Same walk as `_last_reply`.
            if not past_the_nod or punt_module:
                return module if not past_the_nod else punt_module
            punt_module = module
            continue
        if _is_an_echo(last):
            continue
        if index and _is_a_recap(last, turns[index - 1]):
            continue  # a step quoted out of the answer above is that answer's module
        if module in READABLE:
            if punt_module and module != "answers":
                return punt_module
            return module
        return punt_module
    return punt_module


# "is that bad" after a line about the person's own habit or mood is a question about them, and
# the floor above answers it. After a line about the world it is a different question: "my hedge
# is dying" / "is that bad" is not "what does it take out of your week", and neither is
# "im 52 and nobody will hire me" - a state or somebody else's behaviour is not a doing of theirs.
# What somebody *has* is not what they do, and the difference matters: "i have a lump in my
# breast" matched this and the backstop answered a lump with "I wouldn't call it bad ... what does
# it take out of your week", which is the one thing a person must not be told. The possession
# verbs are excluded with the copula, so the floor stays on lines about the person's own days.
OWN_DOING = re.compile(
    r"^i\s+(?!am\b|m\b|'m\b|have\b|had\b|havent\b|got\b|ve\b|need\b|want\b"
    r"|found\b|noticed\b|spotted\b|saw\b|seen\b|might\b|may\b|could\b|probably\b)"
    r"[a-z']+\b", re.I)


# A plan that can hurt is not a plan to weigh. The person states it, then checks it, and the
# doubt path used to hand back a shrug or a yes: "stop taking my antidepressants" / "is that ok"
# was answered "Nothing in that sounded like a warning sign - so yes, it is fine", which takes
# back the answer before it ("Keep taking it until a pharmacist, nurse or GP tells you to stop").
# Five families, each one a thing that injures somebody when it goes wrong, so an ordinary plan
# is untouched: an engine or a fire in a space with no chimney, a medicine somebody else
# prescribes, mains electricity, a blade with the guard off, and a job at height or one that
# brings a structure down.
CAN_HURT = (
    # Carbon monoxide first, because it is the one that kills without any sign: an engine or a
    # charcoal fire running in a garage, a shed, a tent or any room with the door shut.
    ("carbon monoxide", re.compile(
        r"\b(?:car|engine|van|generator|mower|bbq|barbecue|charcoal|stove)\b"
        r"(?:\W+\w+){0,4}?\W+(?:running|left\s+on|on|lit|going|burning)\b", re.I),
     re.compile(r"\b(?:garage|shed|indoors?|inside|tent|room)\b", re.I)),
    # Stopping, doubling, halving or skipping a medicine: "stop my insulin", "double the dose",
    # "stop taking my antidepressants", "cut my tablets in half". The medicine has to be what is
    # being stopped - "the pill stopped working" is a report about the pill, not a plan of the
    # person's, and the window after the verb is what keeps the two apart.
    ("a medicine", re.compile(
        r"\b(?:stop|stopping|quit|quitting|come\s+off|coming\s+off|double|doubling|halve|halving|"
        r"skip|skipping|cut\s+(?:it\s+)?(?:in\s+half|down)|take\s+more|up\s+the\s+dose)\b"
        r"(?!\s+(?:working|helping|hurting))"
        r"(?:\W+\w+){0,4}?\W+(?:insulin|antidepress\w*|antibiotic\w*|medication|medications|"
        r"meds|tablets?|pills?|statins?|steroids?|inhaler|epipen|epi\s*pen|"
        r"blood\s+pressure\s+(?:tablets?|meds?)|dose|dosage|prescription)\b", re.I), None),
    # Mains electricity and gas, done by hand: "wire the socket myself", "fit the fuse box",
    # "can i fix the boiler myself".
    ("the mains", re.compile(
        r"\b(?:rewire|re-wire|wire\s+(?:it|up|the\s+socket|a\s+socket|the\s+lights?)|"
        r"fit\s+(?:a\s+|the\s+)?(?:socket|fuse\s*box|consumer\s+unit)|"
        r"move\s+(?:a\s+|the\s+)?(?:socket|fuse\s*box)|"
        r"(?:socket|fuse\s*box|consumer\s+unit|wiring|boiler)\b(?:\W+\w+){0,4}?\W+"
        r"(?:myself|ourselves|himself|herself))\b", re.I), None),
    # A blade or a saw with the guard off, or in front of the eyes with nothing over them.
    ("that blade", re.compile(
        r"\b(?:angle\s+grinder|grinder|chainsaw|chain\s+saw|circular\s+saw|table\s+saw|"
        r"chop\s+saw|bench\s+saw|saw)\b", re.I),
     re.compile(r"\b(?:no\s+guard|without\s+(?:the\s+|a\s+|its\s+)?guard|guard\s+off|"
                r"took\s+(?:the\s+|its\s+)?guard\s+off|no\s+goggles|without\s+goggles)\b",
                re.I)),
    # A job at height, or one that brings a structure down on the person doing it. The doing has
    # to be theirs: "moss on the roof" and "my knee is not good on a ladder" are about the roof
    # and the knee, not a plan, and they keep their card.
    ("a job like that", re.compile(
        r"\b(?:take|taking|knock|knocking|pull|pulling|remove|removing)\s+(?:the\s+|my\s+|our\s+)?"
        r"(?:chimney|wall|ceiling|lintel)\b(?:\W+\w+){0,3}?\W+(?:out|down|off)\b"
        r"|\b(?:on\s+the\s+roof|up\s+(?:a|the)\s+ladder|on\s+(?:a|the)\s+ladder)\b"
        r"(?:\W+\w+){0,3}?\W+(?:myself|ourselves|alone|on\s+my\s+own|by\s+myself)\b"
        r"|\b(?:myself|ourselves)\b(?:\W+\w+){0,4}?\W+"
        r"(?:on\s+the\s+roof|up\s+(?:a|the)\s+ladder|off\s+the\s+ladder)\b", re.I), None),
)
# A line that already names the tradesperson is a plan to hire one, which is what this pool
# says, so it stands aside rather than handing the advice back.
NAMES_A_TRADE = re.compile(
    r"\b(?:electrician|plumber|builder|roofer|chimney\s+sweep|gas\s+safe|engineer|"
    r"handyman|scaffold\w*)\b", re.I)
# A sentence in the answer that tells the person to keep doing the thing, stop it, or ask first.
# It is what makes the warning the answer's own rather than a new one over the top of it.
A_KEEP_OR_STOP = re.compile(
    r"\b(?:keep|carry\s+on|stopping|stop|do\s+not|don\u2019t|dont|never|ask|check|review|"
    r"until|rather\s+than)\b", re.I)
# Each pool says the same thing in its own words: not on your own, here is what it does, and here
# is the person to ask. None of them is an alarm - what the person did was check, and the check
# is right - so they open on the check being right rather than on the danger.
THE_PLAN_CAN_HURT_LINES = {
    "carbon monoxide": (
        "Good that you checked. Not with the engine running in there, though - that is carbon "
        "monoxide, and it puts people to sleep before they notice it. Run it outside, and if the "
        "door has to stay shut, have somebody with you.",
        "Right to ask. That one gives off carbon monoxide, and a garage or a tent holds it: do it "
        "out in the open, or with the doors wide open and somebody knowing you are in there.",
        "Worth asking: an engine or a fire in a closed space is carbon monoxide, and that is the "
        "kind that takes people quietly. Move it outside before you start it.",
    ),
    "a medicine": (
        "Not without the person who prescribes it: stopping it, doubling it or cutting a tablet "
        "in half is the one change they want to hear about first. Ring the surgery, a pharmacist "
        "or 111 and ask what to do today.",
        "That one goes through whoever prescribes it - a change of dose or a stop is not "
        "something to work out alone. Ring the surgery or a pharmacist, and keep taking it as "
        "written until they say otherwise.",
        "Ask the prescriber before you change it, and carry on as written until then. A "
        "pharmacist will answer this the same day, and 111 will at night.",
    ),
    "the mains": (
        "Not by hand: that is mains, and it is not a thing to learn on. Get a registered "
        "electrician in - a socket or a fuse box done wrong is the sort of fault that waits.",
        "Not on your own. Mains wiring has to be done and signed off by somebody registered, and "
        "the part that goes wrong is inside the wall where you cannot see it.",
    ),
    "that blade": (
        "Not with the guard off. That guard is the part that comes between you and the blade, "
        "and a saw does not give you a second go: put it back, or get somebody who has one.",
        "Put the guard back on first, and goggles too - that is the half of the job that keeps "
        "your hands the shape they are.",
    ),
    "a job like that": (
        "Not from a ladder on your own, and not by taking it down yourself: that wants somebody "
        "who has done it before, and a second pair of hands. Get a builder or a chimney sweep "
        "round, and let them say what it is.",
        "A job like that is one to hand over rather than climb to - a ladder on your own is how "
        "people get hurt at home. Ring somebody who does it for a living.",
    ),
}


def _the_plan_can_hurt(said):
    """The family of harm the plan behind the check is in, or None.

    An ordinary plan is untouched: this only answers a doubt when the line states one of the five
    things that injure people, and each family needs both halves - the act and the thing that
    makes it dangerous. "stop taking my antidepressants" is the medicine; "stop taking the bins
    out on tuesday" is nothing.
    """
    if not said or NAMES_A_TRADE.search(said):
        return None
    for family, act, guard in CAN_HURT:
        if act.search(said) is None:
            continue
        if guard is not None and guard.search(said) is None:
            continue
        return family
    return None


def _the_answer_already_warned(said):
    """The warning the answer above already gave, when it gave one, else "".

    "stop taking my antidepressants" / "is that ok" follows an answer that says "Keep taking it
    until a pharmacist, nurse or GP tells you to stop". The best reply is that sentence, not a
    new one, so a warning the answer already carries is handed back rather than rewritten.
    """
    if not said or not NAMES_A_CLINICIAN.search(said):
        return ""
    for sentence in re.split(r"(?<=[.!?])\s+", said):
        sentence = sentence.strip()
        if not 6 <= len(sentence.split()) <= 40:
            continue
        if NAMES_A_CLINICIAN.search(sentence) is None:
            continue
        if A_KEEP_OR_STOP.search(sentence) is None:
            continue
        return sentence.rstrip(" .") + "."
    return ""


def _a_plan_doubt(memory):
    """The line for a bare doubt that follows the person's own plan, or None.

    A plan is theirs, so this composer has no verdict to give and stands aside - which used to
    mean returning nothing, and the turn then landed on the acknowledgement pool: "im going to
    rome" / "is that ok", "i want to book a holiday" / "is that ok" and "we're thinking of getting
    a rescue greyhound" / "is that ok" were all answered "Alright then - good luck with it". A
    sign-off says the conversation is over, and what the person is checking is that wanting it is
    allowed. Nothing is ruled on about the plan; the ask is for the part being weighed.
    """
    said = _flat(_the_line_behind(memory))
    if not said or not A_PLAN.search(said):
        # The plan is often one line back rather than the last one: "im thinking of getting a dog"
        # / "but i work all day" / "is that fair". The detail is the person's own thought about
        # the plan, so the plan is still what the check is about.
        said = _the_plan_they_brought(memory)
    if not said:
        return None
    return pick(_round_robin(A_PLAN_DOUBT_LINES, said), memory, said)


def _about_the_person(memory):
    """The line the ask follows, when it opens on the person: "i have a lump", "ive a cough".

    A dying hedge or a hiring market is somebody else's business, and a verdict question about
    one is not the person's own ("is that bad" after "my hedge is dying" is a question about the
    hedge). What somebody has or noticed is theirs, and it may be a lump - which is why this is a
    looser test than `_own_doing` and only ever feeds the pool that claims nothing.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or len(turns) < 1:
        return False
    for last in reversed(turns):
        if not isinstance(last, dict):
            return False
        if _is_an_echo(last):
            continue
        said = _flat(last.get("user"))
        if not said or len(said.split()) < 3:
            return False
        return re.match(r"(?:i\s|ive\s|i've\s|i\u2019ve\s)", said, re.I) is not None
    return False


def _own_doing(memory):
    """The line the verdict ask follows, when it is about something the person does themselves."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or len(turns) < 1:
        return False
    for last in reversed(turns):
        if not isinstance(last, dict):
            return False
        if _is_an_echo(last):
            continue
        said = _flat(last.get("user"))
        return bool(said) and len(said.split()) >= 3 and OWN_DOING.match(said) is not None
    return False


def _a_plan_or_a_choice(memory):
    """The line the doubt follows, when it is the person's own plan, choice or wish.

    "is that ok" after a plan is not a symptom check and there is no answer to read it out of, so
    without this the doubt path stands aside and the ack pool reads "ok" as a nod. Anything with a
    body in it is somebody else's reading ("should i get my mole checked" has an answer in the
    knowledge base and a verdict in it), so it is left alone here, as is a line about another
    person.
    """
    said = _flat(_the_line_behind(memory))
    if not said or not (A_PLAN.search(said) or A_DECISION_ASK.search(said)):
        return False
    words = _words(said)
    return not any(word in BODY_WORD for word in words) and not any(
        word in SOMEONE_ELSE for word in words)


def _good_news(memory):
    """The line the verdict ask follows, when it is news that something went well.

    "i got the job" / "is that bad" was met with "How long has it been going on, and what would
    you like to do about it?", which reads as if the job were an illness. A floor that asks how
    long it has been going on only belongs over a condition; news of a thing that went well is
    not one, and it keeps whatever the composer had for it.
    """
    if _reads_as_good_news is None:
        return False
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    for last in reversed(turns):
        if not isinstance(last, dict):
            return False
        if _is_an_echo(last):
            continue
        said = _flat(last.get("user"))
        return bool(said) and _reads_as_good_news(said)
    return False


# A first-person past form: the event it names has happened and finished. Only the common ones -
# this is a shape test, not a vocabulary, and anything it misses keeps the floor it always had.
OVER_VERB = re.compile(
    r"\bi\s+(?:\w+ed|did|ran|got|went|came|made|took|won|bought|wrote|sent|met|found|gave|had|"
    r"kept|left|put|saw|spoke|sold|paid|drove|flew|finished|passed|booked|handed|signed|told|"
    r"started|stopped|began|broke|lost|held|built|caught|chose|felt)\b")
# ...unless the line says it is still going on: a state that repeats or continues is a thing a
# floor may ask about, however it is put.
STILL_GOING = re.compile(
    r"\b(?:yet|still|again|every (?:day|night|week|morning|time)|keeps?|always|constantly|"
    r"anymore|any more|since|for (?:weeks|months|years|days)|all the time|at the moment|"
    r"now|these days|lately)\b")


def _an_event_that_is_over(memory):
    """The line the verdict ask follows, when it is about something that happened and finished.

    "i finished my essay" / "is that bad" was met with "What would you like to do about it, and
    how long has it been like that?", which asks a person how long their essay has been going on.
    A floor that asks how long is for a state, so a finished event keeps whatever the composer
    had for it.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    for last in reversed(turns):
        if not isinstance(last, dict):
            return False
        if _is_an_echo(last):
            continue
        said = _flat(last.get("user"))
        if not said or STILL_GOING.search(said):
            return False
        return OVER_VERB.search(said) is not None
    return False


def _nothing_to_be_long_about(memory):
    """True when the floor's "how long has it been going on" would be asked of no such thing.

    Two shapes: news that went well ("i got the job", read by the shared good-news reading) and
    an event that has finished ("i finished my essay"). Neither is a condition, and both keep
    what the composer had for them instead of being asked how long they have lasted.
    """
    return _good_news(memory) or _an_event_that_is_over(memory)


def _first(text, words):
    """Where the first of these words sits in the text, read case-blind.

    A knowledge answer is written as sentences and starts them with a capital: "See a GP if the
    arm is weak or numb" carried the referral that answers "is that bad", and a cue written
    "see a gp" never saw it, so the arm got "Alright then - good luck with it"."""
    text = str(text or "").lower()
    best = None
    for word in words:
        at = text.find(word)
        if at >= 0 and (best is None or at < best):
            best = at
    return best


def _a_throw_away(said):
    """The thing the answer told the person to get rid of, and whether it was written as a test.

    "If milk smells sour, bin it" is not that: the answer is a rule for testing the milk, and a
    bare "is that bad" on top of it is a question about the rule, not a report that the milk is
    off, so the same fence `_unconditional_care` uses stands this reading down.
    """
    said = str(said or "")
    for match in THROW_AWAY.finditer(said):
        before = said[:match.start()]
        if NOT_TOLD_TO.search(before) or ONE_OPTION.search(before):
            continue
        sentence = before.split(".")[-1]
        action = match.group(0)
        action = action[0].upper() + action[1:]
        # The fence is the one the throw-away hangs off, not any "when" in the list of signs it
        # is reaching past: "flesh that stays dented when you press it ... means bin it" is a
        # verdict, while "if milk smells sour, bin it" is a test.
        if TESTING.search(sentence) or CONDITIONAL.search(sentence.split(",")[-1]):
            return action, True
        return action, False
    return None, False


# The answer's rule names a sign - "if milk smells or tastes sour" - and the person who has
# already said that sign is not asking what the test is: "my milk has gone sour" was given "Bin
# it if it has actually turned. The test is the answer", which is a step behind the answer they
# can already see. Asking *how* to tell is the row that wants the test back.
SIGN = re.compile(r"\b(?:sour|off|mouldy|moldy|curdled|smelly|smells|stinks|stinking|fizzy|"
                  r"rancid|turned|slimy|furry|green|black|gone bad|gone off|past it)\b", re.I)
ASKING_HOW_TO_TELL = re.compile(r"\b(?:how do i (?:know|tell|check)|how can i tell|how to tell|"
                               r"how do you tell|how do i spot|what should i look for|"
                               r"what do i look for|what should i check|is it still (?:ok|okay|fine))\b",
                               re.I)


def _the_person_line(memory, said):
    """The person's own last line, the one this doubt is a doubt about."""
    said = str(said or "").strip()
    for turn in reversed(list((memory or {}).get("turns") or [])):
        line = str(turn.get("user") or "").strip()
        if line and line != said:
            return line
    return ""


def _said_no(said):
    """The answer's own sentence saying the thing is not safe, or None.

    Read sentence by sentence, because the no is often not the opening: "There is no safe number
    of drinks before driving. The England and Wales limit is 35 micrograms ..." puts the verdict in
    its first sentence and the numbers after it. The sentence is handed back as it was written, so
    the reply repeats the answer rather than making a new claim about how serious the thing is.
    """
    for sentence in re.split(r"(?<=[.!?])\s+", str(said or "")):
        if STATED_NO.search(sentence) is not None:
            sentence = sentence.strip().strip("\"'\u201c\u201d").strip()
            if sentence:
                # The full stop stays: the pools above put the answer's sentence in the middle of
                # their own, so "driving What to do instead" would read as a run-on.
                return sentence.rstrip(".") + "."
    return None


def _said_enough(said):
    """The answer's own words saying the amount is enough, or None.

    Cut at the first comma when the sentence runs long: "Three half-hour sessions a week is enough
    to feel different in a month, and you need no equipment: a walk or a jog for ten minutes to
    warm up" is one sentence, and handing the whole of it back repeats the answer the person is
    looking at. The clause that says the amount is the half that answers them.
    """
    for sentence in re.split(r"(?<=[.!?])\s+", str(said or "")):
        if STATED_ENOUGH.search(sentence) is None:
            continue
        sentence = sentence.strip().strip("\"'\u201c\u201d").strip().rstrip(".")
        if len(sentence) > 90 and "," in sentence:
            head = sentence.split(",")[0].strip()
            if len(head) > 20 and STATED_ENOUGH.search(head) is not None:
                sentence = head
        if sentence:
            return sentence + "."
    return None


def _the_person_gave_the_sign(memory, said):
    """Whether the person's own last line already said the sign the answer tests for."""
    line = _the_person_line(memory, said)
    if not line or ASKING_HOW_TO_TELL.search(line):
        return False
    return bool(SIGN.search(line))
# A referral is for later, not now, when the "if" comes after it instead of in front of it:
# "Get it looked at if it gives way, locks, or you cannot put your weight on it". _unconditional
# _care only looks backwards, and that is right for the warning branches; asking whether the
# answer offers care wholesale needs the fence read from both sides.
LATER_CONDITION = re.compile(r"\b(?:if|unless|when|once|whenever|as soon as)\b", re.I)

# Who an answer names, with no verb in front of them. `REFER` reads "see your GP" and "ring 111";
# this reads "your midwife, GP or 111" and "a real person today", which is how a safety line and
# many health answers word the same call.
TRADE = re.compile(
    r"\b(?:gp|doctor|midwife|health visitor|111|999|112|a&e|dentist|pharmacist|optician|"
    r"physio(?:therapist)?|nurse|vet|paramedic|district nurse|out of hours)\b", re.I)


def _care_for_now(said):
    """True when the answer names care that is not fenced by a condition before it or after it."""
    for sentence in re.split(r"(?<=[.!?]) ", str(said or "")):
        found = _first(sentence, CARE)
        if found is None:
            continue
        cue = min((sentence.lower().find(word) for word in CARE if word in sentence.lower()),
                  default=-1)
        # A fence in front of the cue counts as much as one behind it. "If it locks out twice, or
        # you smell gas, stop and call a Gas Safe engineer" has its "if" before the trade, and
        # reading that as care for now made the answer's own condition (locks out twice) the wrong
        # thing to hand back.
        if (cue >= 0 and not LATER_CONDITION.search(sentence[cue:])
                and not LATER_CONDITION.search(sentence[:cue])):
            return True
    return False


def _sentence_at(text, at):
    """The sentence of `text` that the offset `at` sits in."""
    begin = 0
    for found in re.finditer(r"(?<=[.!?]) ", text):
        if found.start() >= at:
            return text[begin:found.start()]
        begin = found.end()
    return text[begin:]


def _behind_a_description(said, at):
    """True when the care cue at `at` is the referral a described condition hangs on.

    "Shaking that has crept on over months ... is worth a GP appointment" is the same advice for
    later that an "if" makes it, written as a relative clause instead: the care word comes after
    the condition rather than in front of it, so reading only backwards called it a verdict now.
    """
    sentence = _sentence_at(said, at)
    if len(sentence) <= len(said) - at - 1 and not sentence.endswith((".", "!", "?")):
        sentence = sentence + "."
    described = _a_described_condition(sentence)
    if not described:
        return False
    marker = None
    for found in re.finditer(r"\b(?:that|which|who)\s+", sentence, re.I):
        marker = found
    if marker is None or not sentence[:marker.start()].strip():
        return False
    cue = sentence.lower().find(said[at:at + 12].lower()) if at < len(said) else -1
    return cue > marker.start()

def _not_fenced(said, start, end=None):
    """True when no "if ..." sits either side of this cue inside its own sentence.

    A condition can come after the cue as well as before it: "it is worth getting it checked if
    it hurts or gives way" and "see a GP if the arm is weak or numb" are both advice for a
    condition, and reading only the words in front of the cue made them a verdict now.
    """
    before = said[max(0, start - 90):start]
    if CONDITIONAL.search(before.split(".")[-1]):
        return False
    if end is not None:
        after = said[end:end + 90].split(".")[0]
        # Unless the referral itself says when to act: "ring the vet today if it has been more
        # than 24 hours" is the threshold for acting, not a condition on whether to.
        fence = CONDITIONAL_AFTER.search(after)
        if fence and not URGENT_TIME.search(said[start:end + 40]):
            # The "if" fences the cue unless the words between them make it a degree of the
            # same errand: "so ring the vet, and sooner if he is also off his food or weeing in
            # the house" is a yes, and reading its later "if" as a fence answered a dog that
            # drinks too much with "do the job I described" about its water bowl. Only a
            # comparative counts, so "get it looked at the same day if you cannot put weight on
            # it" stays the conditional second sentence it is.
            rider = after[:fence.start()]
            if not COMPARATIVE.search(rider):
                return False
    return True


NEGATED_BEFORE = re.compile(r"(?:\bnot|\bnever|\bno|n't|\bless|\bhardly|\bexcept|\bwithout)"
                      r"\s+(?:\w+\s+){0,2}$")


def _said_without_a_not(text, at, length):
    """True when the word at `at` is said plainly, not under a "not", "less" or "un-"."""
    if text[max(0, at - 2):at] == "un":
        return False
    before = text[at - 1] if at else " "
    after = text[at + length:at + length + 1]
    if before.isalnum() or after.isalnum():
        return False  # "commonest" is not "common", and "unusually" is not "usually"
    return NEGATED_BEFORE.search(text[max(0, at - 26):at]) is None


def _first_positive(text, words):
    """`_first`, but a word with a "not", "less" or "un-" in front of it is not that reading.

    "it is common at four and still common at nine, but past ten it is **less usual**" says the
    opposite of "usual" for the age in question, and "not serious in most cases" is not the same
    answer as "nothing serious". Every worry cue is read this way, so the reassuring words cannot
    be borrowed from a sentence that took them back.
    """
    text = str(text or "").lower()
    best = None
    for word in words:
        start = 0
        while True:
            at = text.find(word, start)
            if at < 0:
                break
            if _said_without_a_not(text, at, len(word)):
                if best is None or at < best:
                    best = at
                break
            start = at + 1
    return best


def _unconditional_care(said):
    """The first care cue that is not fenced off by an "if ..." or a description in front of it.

    The words a referral is made in are not all in CARE: an answer offers "get looked at" and
    "Ring your GP or a physio", and a physio, a dentist and a vet are the same kind of referral
    as a doctor. REFER is read here too, so the referral counts however it is worded.
    """
    said = str(said or "").lower()
    best = None
    for word in CARE:
        start = said.find(word)
        while start >= 0:
            # The condition can be written as a description of the thing rather than as an
            # "if": "Shaking that has crept on over months ... is worth a GP appointment" answers
            # a bare "is that bad" with the condition, not with "yes". Main's `_behind_a_description`
            # reads that same shape and is kept here rather than a second reader for it.
            if (_not_fenced(said, start, start + len(word))
                    and not _behind_a_description(said, start)):
                if best is None or start < best:
                    best = start
                break
            start = said.find(word, start + 1)
    for match in REFER.finditer(said):
        if not _not_fenced(said, match.start(), match.end()):
            continue
        if best is None or match.start() < best:
            best = match.start()
        break
    return best


def _the_fence_is_met(fence, said, memory):
    """Whether the person's own line already says the words the answer's fence is written in."""
    if not isinstance(memory, dict):
        return False
    line = (_the_line_it_answered(said, memory) or "").lower()
    if not line:
        turns = memory.get("turns") or []
        line = str((turns[-1] or {}).get("user") or "").lower() if turns else ""
    if not line:
        return False
    said = {word.rstrip("s") for word in re.findall(r"[a-z']{4,}", line)}
    for word in re.findall(r"[a-z']{4,}", str(fence or "").lower()):
        if word.rstrip("s") in said:
            return True
    return False


# How often it happens, in the person's own words: "every afternoon", "most days", "all the time".
A_FREQUENCY_SAID = re.compile(
    r"\b(?:every|most|each|all) (?:\w+ )?(?:day|days|night|nights|morning|mornings|afternoon|"
    r"afternoons|evening|evenings|week|weeks|month|months)\b|"
    r"\ball the time\b|\balways\b",
    re.I)

# The answer's fence can be a fence on how often, too: "if you get them most days".
A_FREQUENCY_ASKED = re.compile(
    r"\bmost days\b|\bmost nights\b|\bevery day\b|\bregularly\b|\bseveral times\b|"
    r"\bmore than (?:once|twice)\b|\bkeeps? (?:coming|happening|returning)\b|"
    r"\btime and again\b",
    re.I)


def _a_frequency_already_said(fence, said, memory):
    """Whether the person has already said how often it happens, so the answer's condition is met.

    `im getting headaches every afternoon` / `what should i do first` / `is that bad` is the person
    the headache card fences: "if you get them most days" is their "every afternoon" in the card's
    words. The doubt's own line says only "is that bad", so no words of the fence are in front of
    it and reading the fence as the answer's condition told them the headache was ordinary on its
    own, over their own line that it happens every afternoon. Found in review by @loyal-brush.

    Both halves are needed: the fence has to be about how often, and the person has to have said
    how often, so a chat whose answer fences on something else is untouched by a stray "every day"
    about the bins.
    """
    if not isinstance(memory, dict) or not A_FREQUENCY_ASKED.search(str(fence or "")):
        return False
    # The frequency has to be about the same thing: a chat whose "every day" is the bins going out
    # has said nothing about how often the headache comes. So the line that said how often must
    # share a word with the line the answer was answering - and when it is that line, it does.
    answered = _the_line_it_answered(said, memory)
    subject = {word.rstrip("s") for word in re.findall(r"[a-z']{4,}", answered)}
    for turn in memory.get("turns") or []:
        line = str((turn or {}).get("user") or "").lower()
        if not A_FREQUENCY_SAID.search(line):
            continue
        if not subject:
            return True
        words = {word.rstrip("s") for word in re.findall(r"[a-z']{4,}", line)}
        if words & subject:
            return True
    return False


def _condition_after_care(said, care_at, memory=None):
    """The answer's own condition, when it sits after the referral in that same sentence.

    "Get up in two stages, drink enough water, and see a doctor if you actually faint or it
    happens most times you stand" has a referral in it, so the bare "is that bad" after it was
    answered "Yes, that one wants a proper look rather than watching it" - a claim the answer
    itself had just contradicted, since the standing up is ordinary and the faint is the thing
    to watch. A referral with the answer's own "if" after it is not a verdict now: it is the
    condition the answer named, and that condition is the answer to the bare ask.
    """
    if care_at is None or care_at < 0:
        return ""
    sentence = re.split(r"(?<=[.!?]) ", str(said or "")[care_at:])[0]
    fence = re.search(r"\b(?:if|unless|once|when) \w", sentence, re.I)
    if not fence:
        # An answer whose referral is fenced in a later sentence is not a call for today either:
        # "water, a dark quiet room and paracetamol usually do more than anything you can buy ...
        # If you get them most days ... take it to a pharmacist or GP" was answered "Yes, that one
        # wants a proper look", over a card that had just said the ordinary headache settles. The
        # fence is the answer's own condition wherever it is written, so the same reading applies
        # to it - unless the answer also makes a call for now, which outranks its condition.
        if _the_call_sentence(said):
            return ""
        # The person being already past a timescale the answer set is a sharper reading than the
        # condition is: "my knee has clicked for three weeks" wants "you are already past it", not
        # "it stops being ordinary if it is no better after six weeks". That arm reads the
        # answer's hedge with the person's own span, so it keeps the turn.
        if memory is not None and _past_the_timescale(said, memory):
            return ""
        later = _when(said)
        if later and _a_frequency_already_said(later, said, memory):
            # A fence on how often is met by the person's own "every afternoon": the threshold they
            # have already described is not a thing to watch for.
            return ""
        if later and _the_fence_is_met(later, said, memory):
            # A fence the person's own line already meets is not a condition on whether to act,
            # it is a threshold they have passed: "i sweat a lot at night" against the card's
            # "if you sweat buckets from one place or at night" is a yes, and reading it as the
            # answer's condition would tell them "ordinary on its own" in the same breath as
            # naming the thing they just said they have.
            return ""
        return _cut_condition(later) if later else ""
    # A referral that names a time is not waiting on anything: "ring the vet today if it has been
    # more than 24 hours" is a yes today, and reading it as a condition would soften advice that
    # was never soft. Only a fence with no time in it is the answer's own condition.
    if TIME_NOW.search(sentence):
        return ""
    # A condition that comes after the answer has already said go is a degree of the same errand,
    # not a fence on whether to: "so ring the vet, and sooner if he is also off his food or
    # weeing in the house" is a yes, and reading its later "if" as the answer's own condition
    # told the person their dog was "ordinary on its own" over an answer that said ring the vet.
    if COMPARATIVE.search(sentence[:fence.start()]):
        return ""
    return _cut_condition(_when(said))


# "the same day" is a call for now wherever it is written, so it belongs here with "today" and
# "straight away": the toothache card says "ring a dentist the same day" in its second sentence, and
# with it missing from this reading the answer's later fence ("a swelling in your face") was taken
# for its condition and `my tooth hurts` / `is that bad` was answered with a threshold instead of
# the same-day call the answer had just made. Found in review by @steward-merry-zebra.
TIME_NOW = re.compile(r"\btoday\b|\bnow\b|\btonight\b|straight away|as soon as|"
                      r"\btomorrow\b|\bthis (?:morning|afternoon|evening)\b|\bnext few hours\b|"
                      r"\bthe same day\b(?!\s+if\b)",
                      re.I)


# A condition can run to a list of triggers ("... if it has been more than 24 hours, and straight
# away for a puppy under six months, or if there is vomiting"). A short list is repeated whole,
# because every clause of it is a sign the answer named; a long one is cut to its first clause,
# which carries the shape of it, so the line stays one sentence rather than becoming a second copy
# of the answer. The limit is where a cut stops helping: a cat answer's "she has not drunk for 24
# hours, is straining in the tray, or is hiding and off her food" is three signs and reads as one
# clause, and cutting it told the person one sign where the answer named three.
CONDITION_CLAUSE = re.compile(r", (?:and |or |then |so )?| and | or ")


def _cut_condition(when, most=22):
    when = str(when or "").strip(" ,.")
    if len(when.split()) <= most:
        return when
    when = CONDITION_CLAUSE.split(when)[0].strip(" ,.")
    return when

def _first_sentence_end(said):
    """Where the answer's first sentence ends, so a later one can be told apart from it."""
    found = re.search(r"[.!?](?:\s|$)", str(said or ""))
    return found.end() if found else len(str(said or ""))


def _told_to_act(said, at):
    """Whether the referral at `at` is the answer telling the person to do something.

    The words a referral is made in come in two shapes. One is an instruction: "ring the vet",
    "get it looked at", and the cue itself is the verb. The other only names the appointment:
    "worth a GP visit", "a job for the vet". The second shape is how an answer writes its list
    of warning signs - "Pins and needles in the fingers that wake you is worth a GP visit" - and
    that is a pointer to a different symptom, not advice about the wrist that is "usually an
    overused tendon". So it is the declarative shape that has to be in the answer's opening to
    count, and a later one is a warning rather than a referral.
    """
    said = str(said or "")
    if not DECLARATIVE_REFERRAL.match(said, at):
        return True
    return at <= _first_sentence_end(said)


def _referral(said):
    """The answer's own referral, from its first sentence or from a later one that tells them to act.

    The knee answer's referral is its last sentence, and reading only the opening answered the
    knee with "that one is the ordinary kind, so no". A later sentence that only states some
    OTHER symptom is worth a visit is a warning about that symptom, not advice about this one,
    so a referral out of the first sentence has to be an instruction.
    """
    care = _unconditional_care(said)
    if care is None:
        # A referral stated rather than told: "anything hard, painless, fixed in place, or still
        # there after three weeks needs a GP" is the answer's own judgement about the thing the
        # person asked about, and the person asking "is that bad" about a lump they found is
        # asking whether theirs is that one. It carries its own fence, so it is read anywhere but
        # only when no "if" or "when" sits beside it: "see a GP if it is still there in three
        # weeks" stays a condition, not a yes.
        stated = DECLARATIVE_REFERRAL.search(str(said or ""))
        if stated is not None and _not_fenced(said, stated.start(), stated.end()):
            return stated.start()
        return None
    if care <= _first_sentence_end(said):
        return care
    return care if _told_to_act(said, care) else None


GO_FROM = ("worth a gp", "gp visit", "worth a hearing test", "a referral",
           "for a referral", "worth getting looked at", "worth seeing")


def _a_plain_go(at, said):
    """True when the care cue at `at` is a recommendation, not a warning behind a condition.

    The answer that says both halves - "It is common at four and still common at nine, but past
    ten it is less usual ... so it is worth a GP visit whatever the age" - was read as the
    ordinary kind because "common" comes first, and a twelve-year-old still wetting the bed was
    told "Nothing in that sounded like a warning sign". A "worth a GP visit" is a thing to do
    whatever the age, so it answers the ask rather than the words in front of it.
    """
    said = str(said or "").lower()
    window = said[max(0, at - 24):at + 24]
    return any(word in window for word in GO_FROM)


def _opening(said):
    """The answer's first sentence or two, where its verdict and its first instruction live.

    A word searched for anywhere finds the wrong sentence as often as the right one: the gas
    bill answer carries a "usually" about tariffs three sentences in, and reading that as the
    verdict turned "is that bad" after it into "that one is the ordinary kind, so no".
    """
    parts = re.split(r"(?<=[.!?]) ", str(said or ""))
    return " ".join(parts[:2])


# A sentence that puts its own condition in front of the clinician is a referral for that case
# and not for the person reading it now: the headache answer ends "If you get them most days,
# keep a short diary ... and take it to a pharmacist or GP". Telling someone whose head hurts
# this afternoon to ring the doctor is the false alarm STYLE rules out, so a referral lifts the
# all-clear only when at least one sentence makes it plainly, with no if, when or "most days"
# in it. The lump answer's "anything hard, painless, fixed in place, or still there after three
# weeks needs a GP" has no such word in it and does lift it.
FENCED_IN_SENTENCE = re.compile(r"\b(?:if|unless|once|when|whenever|in case|most days)\b",
                                re.IGNORECASE)
# The thing's own name is the test for whether the referral is about it: the lump answer's GP is
# "so does a lump with night sweats or weight loss", and the thing in the person's line is the
# lump. An answer that names someone to see for something else is not a referral for this: the
# poinsettia entry ends "Mistletoe and holly berries are the ones to ring the vet about", and a
# rehoming answer says a rescue "asks for the vet records" - told "ring them" over either of
# those, a person with an ordinary complaint is sent to a vet for a plant they do not have.
THING_WORDS = frozenset("""about after again also always another anything around because been
before being both came cant could does doing done down during each even ever every from
getting give going good have having here just keep keeps know last like little long made make
many more most much must need needs never next only other over really right same should since
some something still such sure than that their them then there these thing things think this
those through time today tomorrow tonight under until very want wants well went were what when
where which while will with would your yours yourself""".split())


def _the_thing(line):
    """The words in the person's own line that name what they are asking about."""
    return {word for word in re.findall(r"[a-z']{4,}", _flat(line)) if word not in THING_WORDS}


def _referral_about_the_thing(said, line):
    """True when a sentence names a clinician, plainly, about the thing the person asked about."""
    thing = _the_thing(line)
    if not thing:
        return False
    for sentence in re.split(r"(?<=[.!?]) ", str(said or "")):
        if not NAMES_A_CLINICIAN.search(sentence):
            continue
        if FENCED_IN_SENTENCE.search(sentence):
            continue
        if thing & set(re.findall(r"[a-z']{4,}", sentence.lower())):
            return True
    return False


def _echoes_the_person(step, memory):
    """Whether the "step" is only the person's own words said back to them.

    "i want to be more organised" was met with "Be more organised - fair enough. What's stopped
    it happening so far?", and the first clause of that is the wish itself: answering "what
    should i do first" with "Be more organised, and take it from there" tells nobody anything.
    A short step whose every content word is in the line the person just wrote is that echo.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    said = ""
    for turn in reversed(turns):
        if isinstance(turn, dict) and turn.get("user"):
            said = str(turn["user"])
            break
    if not said:
        return False
    from ..memory.topics import content
    want, have = set(content(step)), set(content(said))
    if not want or len(want) > 3:
        return False
    return not (want - have)


def _kept_step(reply):
    """True when `reply` is one of the lines that says the step has not changed, else False."""
    plain = _flat(reply).strip()
    return any(re.fullmatch(_own_pattern(line), plain, re.IGNORECASE)
               for line in STEP_KEPT_LINES)


def _only_a_verdict(line):
    """Whether a line the person sent was nothing but their verdict on the news above it."""
    text = _flat(line or "").strip()
    if not text:
        return False
    try:
        from .fallback import reads_as_a_verdict
    except Exception:
        return False
    try:
        return bool(reads_as_a_verdict(text))
    except Exception:
        return False


def _the_line_just_given(memory):
    """The bot's own last line, the one the person has just read. "" when there is not one."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ""
    for turn in reversed(turns):
        if isinstance(turn, dict) and turn.get("bot"):
            return str(turn["bot"])
    return ""


def _the_answer_before_that(memory):
    """The bot's line before its last one, when the last one was only a question.

    A question the bot asked is not an answer: there is no step in it to hand over, and the answer
    the person is asking about is the one before it. "" when there is not one.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ""
    seen = 0
    for turn in reversed(turns):
        if isinstance(turn, dict) and turn.get("bot"):
            seen += 1
            if seen == 2:
                return str(turn["bot"])
    return ""


def _word_runs(text, size=5):
    words = _flat(text).split()
    return {tuple(words[at:at + size]) for at in range(max(0, len(words) - size + 1))}


def _says_it_again(line, said):
    """Whether saying `line` now would hand the person a sentence they have just read.

    A five-word run in common is the whole sentence in the cases that matter ("Keep it plain and
    separate: one new food next to one they already eat"), and it cannot be a coincidence: the
    composer builds its steps out of the answer's own words, so a run that long is the answer's
    words coming back. Anything shorter is shared phrasing and is allowed.
    """
    return bool(_word_runs(line) & _word_runs(said))


# How much of the line the person has just read a step may account for before quoting it is the
# same line said twice. A step is a clause of the answer and shares its words by construction,
# so a short answer ("Blot, don't rub, with kitchen paper, then dab with cool water") is quoted
# back at six words in ten and reads fine; the whole of the answer with an interjection in front
# of it ("Long one? Give yourself half an hour doing nothing before the next thing") is the line
# itself, and reading it out again is the repeat STYLE.md forbids.


def _already_asked_for_a_step(memory):
    """Whether the person's own last line was a bare step ask too."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    for turn in reversed(turns):
        if isinstance(turn, dict) and turn.get("user"):
            return bool(STEP.match(_flat(turn["user"])))
    return False


def _the_referral_sentence(said):
    """The one sentence of the answer that holds its judgement, whole."""
    text = str(said or "")
    at = _first(text.lower(), CARE)
    if at is None:
        at = 0
    start = max(text.rfind(". ", 0, at), text.rfind("? ", 0, at), text.rfind("! ", 0, at))
    return re.split(r"(?<=[.!?]) ", text[start + 1:].strip())[0]


def _the_line_is_the_threshold(stated, line):
    """Whether the person's own line names the thing the answer set as its threshold.

    "A dog that will not eat for a day is worth a call to the vet" over "my dog wont eat" is the
    answer's own yes: the threshold is what they are asking about, so handing it back as "Not yet.
    The point where it wants a person: a dog that will not eat for a day" argues with the answer.
    Two content words in common is the test, because the two are written by different people
    ("wont eat" against "will not eat") and the overlap is what a reader sees.
    """
    from ..memory.topics import content
    want, have = set(content(stated)), set(content(line))
    return len(want & have) >= 2


def _most_of_the_line(step, heard):
    """Whether the step is most of what the bot said last turn, so quoting it repeats it.

    "Long one? Give yourself half an hour doing nothing before the next thing." is a whole
    answer that is one instruction, and handing it back as the step said the person's last two
    lines over again. A clause out of a longer answer is not that: the rest of the answer was
    there, so the step adds to what they read rather than replacing it.
    """
    from ..memory.topics import content
    want, have = set(content(step)), set(content(heard))
    if not want or not have:
        return False
    return len(want & have) / len(have) >= 0.8


def _step(said):
    """The first thing the answer told them to do, in the answer's own words."""
    # A negative instruction is not a move: "do not check the clock first, then work down the list
    # I gave you" tells a person what to stop, and the answer's next instruction is the one to
    # hand back ("keep the wake-up time the same, and go easy on late coffee").
    found = [one for one in _steps(said) if not NEGATIVE_OPEN.match(one)]
    found = [one for one in found if not A_STATEMENT.match(one)]
    return found[0] if found else None


# A word that is both a verb and a noun of the thing ("pay", "work", "change", "test", "start")
# opens an instruction ("Pay by card at the till") and a statement ("Pay is at least the apprentice
# minimum wage"), and only the rest of the sentence says which. A finite verb straight after it
# makes it a statement about the thing, and a statement is not a step to hand over: an
# apprenticeship definition handed "Pay is at least the apprentice minimum wage and more on most
# schemes" back as the one thing to start with (@blue-hedgehog, @sky-tuna, #6152).
A_STATEMENT = re.compile(r"^(?:[a-z']+\s+)(?:is|are|was|were|has|have|had|can|cannot|will|would|"
                         r"should|takes?|gives?|means?|costs?|comes?|goes?|does|did|gets?|keeps?)\b",
                         re.I)


# A step is something a person can do this afternoon. The buffer an answer works towards is the
# end of the job, not the first move: "Build towards three to six months of essential bills as
# the buffer" is where saving gets to, and read as the first thing to do it told someone with
# nothing saved to start by having three months saved. The shape of the verb is the tell - a
# target is aimed at, a step is done - so these sentences are not steps, and the reader walks
# on to the instruction the answer did give ("Track two weeks of what actually leaves the
# account").
TARGET_SHAPE = re.compile(
    r"^(?:build|work|save|grow)\s+up\b"
    r"|^(?:build|work|save|aim|get|grow|reach)\b[^.!?]{0,24}?\b(?:towards|toward|up to)\b",
    re.I)


def _listed(said):
    """The first thing on a list the answer wrote after a colon, in the answer's own words.

    "The things that work: same wake-up time every day, no caffeine after early afternoon" has
    given a move without writing one as an instruction, and a person who asks for tips wants
    that first one, not a request to say what they have tried. Only a colon list, and only its
    first item, so nothing here reads a sentence that was not written as a list.
    """
    for sentence in re.split(r"(?<=[.!?]) ", str(said or "")):
        if CONDITIONAL_OPEN.match(sentence.strip()):
            continue
        head, colon, tail = sentence.partition(": ")
        if not colon or tail.count(",") < 2:
            # Only a colon, not a dash or a semicolon: a semicolon joins two clauses of one
            # sentence ("... that turns it round; a child who also snores, wets the bed, or is
            # tired every day is worth a word with the GP"), and its second half is a sentence
            # about the child, not a list of things to do.
            continue
        if HEAD_REFUSES.search(head) or not HELPS.search(head):
            # The words in front of the colon say whether the list is a move or a cause. "The
            # things that work: same wake-up time every day" is a list of things to do;
            # "usually it is the wake-up time rather than the bedtime: a lie-in at the weekend,
            # a nap, or coffee after two" is the opposite claim, and handing its first item back
            # would tell the person to do the thing that keeps the trouble going. So is a menu
            # ("Quick: tuna pasta in 15, a frittata in 20") - a dish is what the answer offers,
            # not the first step out of it.
            continue
        for item in re.split(r",| and ", tail):
            item = " ".join(item.strip(" .:;,-").split())
            words = item.split()
            if not 3 <= len(words) <= STEP_WORDS:
                continue
            if NEGATIVE_OPEN.match(item) or CONDITIONAL_OPEN.match(item):
                # A list can open on a thing not to do ("do not check the clock, keep the light
                # off"), and the first thing to do is the item after it.
                continue
            if DESCRIBES.search(item):
                # An item that runs into a relative clause describes something ("a child who
                # also snores", "a lamp which is too bright"), and a description is not a move.
                continue
            return item
    return None


# A boundary a long step can be cut on without breaking it: "top the pressure up to between 1
# and 1.5 bar using the filling loop" is the step, and "top the pressure up to between 1 and 1.5
# bar" is still the step. Cutting at a joining word is not: "check it again the next day if"
# says half a sentence.
# " with " and " using " are not on this list, though they read like boundaries: the phrase after
# them is what the step is done with, and a step without it is not the instruction the answer
# gave ("Run a hot 60C or 90C service wash" fixes no smell; the cleaner is the point). A step
# that cannot be cut on a clause keeps its whole clause instead, up to LONG_STEP_WORDS.
TRIM = (" because ", " so it ", " so that ", " before ", " after ",
        " until ", " if ", " when ", " rather than ")
# Read only when the step is too long even with its clause kept whole.
TRIM_INSTRUMENT = (" using ", " with ")
# How long a quoted step may be. Generous on purpose: the answer wrote it, and a complete
# instruction of fourteen words beats a fragment of four ("top the pressure up to between 1 and
# 1.5 bar" is the step, "top the pressure up" is a guess at one).
# The words that weigh one thing against another, and so say what a list is not rather than
# what to do: "Change a few things you can keep doing rather than going on a diet: ...".
CONTRAST = re.compile(r"\b(?:rather than|instead of)\b", re.I)
STEP_WORDS = 16
# A step a little over the cap is still a step when every shorter reading of it drops part of the
# instruction: "Run a hot 60C or 90C service wash with a washing-machine cleaner or a cup of
# bicarbonate of soda" is nineteen words and losing the last nine leaves nothing that works.
LONG_STEP_WORDS = 24
# A step of this many words is a sentence in its own right: "first" bolted on the end of it
# lands on the wrong word, so it gets a line that says the order in a sentence of its own.
STEP_LONG = 10
# A sentence fenced with one of these is advice for later, not a step to do now: the boiler
# answer's "if it keeps dropping, there's a leak somewhere: stop topping it up" is the half a
# person must not be told to do first.
# A clause that opens on a noun and then says what it is ("water at the front is usually the
# door seal") is the answer explaining, not telling anyone to do anything, even when its first
# word is also a verb ("water" the plants).
# The punctuation counts too: "A dry, flaky scalp is usually dandruff" opens on a verb word and
# the comma after "dry" stopped the guard, so the description was handed back as the step.
COPULA = re.compile(r"^(?:[\w,'-]+\s+){0,5}(?:is|are|was|were)\b")
# The detail an answer puts after a colon is the rest of its instruction ("turn it off and keep
# it off: do not charge it") or a statement about the thing ("cut the distance ...: most running
# knee, shin and ankle pain is too much, too soon"). Only the first belongs on a step: cutting the
# second at its own comma left "most running knee" dangling off the end of it.
DETAIL_STATEMENT = re.compile(r"\b(?:is|are|was|were)\b", re.I)
CONDITIONAL_OPEN = re.compile(r"^(?:if|unless|once|when|whenever|should|in case)\b",
                            re.IGNORECASE)
# The bot talking about the conversation is not advice. "Nice one. Let me know how it goes" is
# how a chat line keeps the talk going, and a step ask read "Let me know how it goes" out of it
# and answered "Let me know how it goes, and take it from there" - the bot's own small talk handed
# back as the first thing to do, with nobody told what to do.
ABOUT_THE_TALK = re.compile(r"\b(?:let me know|keep me posted|tell me how (?:it|that) (?:goes|went)|"
                            r"how (?:it|that) goes|say more|tell me more|fair enough|"
                            r"thanks for telling me|i'?m listening|good to know|noted)\b", re.I)


def _cut_on(head, joins):
    """The longest cut of `head` before one of these joins that is still a step, or ""."""
    best = ""
    for join in joins:
        at = head.find(join)
        while at > 0:
            cut = head[:at].strip(" ,;:-")
            cut_words = cut.split()
            if (4 <= len(cut_words) <= STEP_WORDS and cut_words[-1].lower() not in HANGING
                    and len(cut) > len(best)):
                best = cut
            at = head.find(join, at + 1)
    return best


# A negative instruction is not a move: "do not check the clock first, then work down the list I
# gave you" tells a person what to stop, not what to do. Answers put the real first move in the
# clause after it ("do not check the clock, keep the light off"), so a part is read from there.
NEGATIVE_OPEN = re.compile(r"^(?:do not|don't|dont|never)\b", re.IGNORECASE)

# The words in front of a colon decide whether what follows it is a list of things to do. Only a
# claim that the items help makes a list a move; a clause naming a cause ("it is the wake-up time
# rather than the bedtime: ...") or a heading ("Quick: ...") leaves it a description.
HELPS = re.compile(
    r"\b(?:things?|ones?|bits?|steps?|changes?|habits?|moves?|tips?|fixes|tricks|what|"
    r"everything|anything|these|those|the rest)\b[^:]{0,40}?"
    r"\b(?:works?|worked|helps?|helped|matters?|counts?|do|does|did|"
    r"worth (?:a|trying|doing|a go))\b"
    r"|\b(?:do|does|did) more than\b",
    re.IGNORECASE,
)
# A clause that says what a list is not, or that what to do depends on something else, is not a
# claim that its items are the moves: "anger shown by what a person does not say: a flat 'fine',
# a sigh" is a list of examples, and "it depends on what you want to do: for nursing" is a choice.
HEAD_REFUSES = re.compile(r"\b(?:not|n't|depends|depend|differ|if|whether|unless)\b", re.IGNORECASE)
# An item carrying one of these runs into a relative clause, so it describes a thing rather than
# naming a move ("a child who also snores", "the mug which leaks").
DESCRIBES = re.compile(r"\b(?:who|whom|whose|which|that)\b", re.IGNORECASE)


def _shorten(head, words):
    """A step of more than STEP_WORDS words, cut on a joining word, or "" if it cannot be cut."""
    if len(words) <= STEP_WORDS:
        return head
    best = _cut_on(head, TRIM)
    if best:
        return best
    # Nothing can be cut off this without losing part of the instruction, so it is the step as
    # the answer wrote it - as long as it is still a sentence somebody would say out loud.
    if len(words) <= LONG_STEP_WORDS and words[-1].lower() not in HANGING:
        return head
    # The phrase the step is done with is the last thing to give up, and a step with half of it
    # still tells the person to start somewhere ("Rinse well, never mix it").
    return _cut_on(head, TRIM_INSTRUMENT)


# A comma ends the instruction unless what follows it carries the same one on: "stop driving and
# get them changed, or you will score the discs too" is a sentence with one instruction in it.
CONTINUES = re.compile(r"^\s*(?:or|but|so|yet|nor|otherwise)\b", re.IGNORECASE)
# ...and a comma that hands the same instruction on *in order* keeps both moves: "Vacuum it
# first, then mop with a barely damp mop" is one step, and reading only its first clause lost
# the mop, which is the half of the floor answer that stops the streaks. Kept apart from
# CONTINUES because of the and/then split at the end of _first_clause: once the comma is a
# continuation, that split would cut the instruction back to its first two words
# ("Wash with warm water" out of "Wash with warm water and a drop of washing-up liquid, then
# squeegee").
ORDER_CONTINUES = re.compile(r"^\s*(?:then|after\s+that|next)\b", re.IGNORECASE)


# "Between home and there" is one frame, not two instructions: cutting at its " and " left the
# step "Ask nursery to use the same words, so the rule does not change between home", which ends
# where the comparison does not. `and` inside `between ... and ...` (and inside `both ... and
# ...`) hands the same instruction on rather than starting a new one, so the split walks past it.
FRAME_AND = re.compile(r"\b(?:between|both)\b[^,;:.!?]*\band\b", re.I)


def _cut_at_a_join(part):
    """The part up to the first " and " or " then " that is not inside a between/both frame."""
    keep_until = 0
    for frame in FRAME_AND.finditer(part):
        if frame.end() > keep_until:
            keep_until = frame.end()
    for at in re.finditer(r" and | then ", part):
        if at.start() < keep_until:
            continue
        return part[:at.start()]
    return part


def _first_clause(part, and_break=True):
    """The part of an instruction up to where it stops being one instruction.

    The break is the first comma that is followed by a new instruction ("Put the child's name and
    class in the subject, say what you have noticed"), not the first " and ": cutting at " and "
    quoted "Put the child's name", a noun phrase, and the step templates then mangled it into
    "Put the child's name, before anything else on that list." A comma that hands the same
    instruction on ("stop driving and get them changed, or you will score the discs too") is not
    a break, and with none of either the whole part is the clause.
    """
    for at in (index for index, char in enumerate(part) if char == ","):
        # ...but only for the caller that wants the whole step. The one-move quote cuts at the
        # comma and that cut is the step, so letting the order through there read "Vacuum it,
        # then dab stains with cool water" as the whole step, and a person who asked for the
        # first move was told it was "still the same move, and nothing to add to it".
        if not and_break and ORDER_CONTINUES.match(part[at + 1:]):
            continue
        if not CONTINUES.match(part[at + 1:]):
            return part[:at]
    if not and_break:
        return part
    return _cut_at_a_join(part)


# A sentence that is the bot asking something rather than telling anyone to do anything. It ends
# on a question and it opens on one, or its last clause does ("Go on, what happened?"). Ending on
# a question mark alone is not enough: "Face - ask them to smile, has one side dropped? Arms -
# can they raise both and hold them out?" is a check to run, and so is a step that quotes the
# words to use ("...: "Could I do 8-4 if I asked?""). Without this, "Do you want to tell me what
# has made it like that?" is quoted as the step and comes back to the person as
# "Do you want to tell me what has made it like that?, and take it from there."
QUESTION_FRAME = re.compile(
    r"^(?:(?:so|and|but|or|ok|okay|right|well|then|now|look|listen|go on|go ahead|come on|"
    r"tell me)\b[\s,\u2014\u2013.:;-]*)*"
    r"(?:(?:do|did|does|would|will|can|could|shall|should|have|has|are|is|was|were)\s+"
    r"(?:you|i|we|they|he|she|it|there|that|this|anyone|anybody|someone)\b"
    r"|(?:what|why|how|where|who|which|whose)\b)", re.IGNORECASE)


# The bot's question that is an offer of help: "Want a hand working out the next step?", "What
# would help most right now?", "Shall I write it out for you?". A person answering that with a
# bare ask ("what do i do") is taking the offer up, so the ask is the answer to the question and
# the question is not waiting to be handed back. It was: after "Sorry to hear that. What would
# help most right now?" a person who said "what do i do" was told "Nothing to do on my side,
# honestly", which is a refusal dressed as a reply. A yes/no question ("Do you want to tell me
# what has made it like that?") is not this: a bare ask does not answer it, and the hand-back
# written for that turn is the right reply.
# An invitation to say more is an offer too: "I'm sorry. Do you want to say what has been going
# on?" then "what do i do" is the person taking it up, and the question-back pool answered that
# with "Nothing to do on my side, honestly" - a shrug after a line that had just offered to
# listen. So the shapes that ask the person to go on belong here: who they could tell, where they
# are with it, what it is like, whether they want to say. A question about a fact ("does it
# happen at night?") is not one of these and is still handed back.
OFFER_QUESTION = re.compile(
    r"\b(?:want (?:me to|a hand|me to)|would you like|shall i|can i help|may i help|"
    r"what would help|how can i help|anything (?:else )?i can do|where would you like|"
    r"do you want to (?:say|tell|talk)|where are you with|what(?:'s| is) it like|"
    r"is there (?:anyone|someone|anybody|somebody)|want to (?:say|tell|talk))\b",
    re.IGNORECASE)


def _an_offer_is_waiting(said):
    """Whether the bot's own last question was an offer the person may be taking up."""
    text = str(said or "").strip()
    if not text.endswith("?"):
        return False
    last = re.split(r"(?<=[.!?]) ", text)[-1]
    return bool(OFFER_QUESTION.search(last))


# An invitation in front of the bot's question ("Sorry. Do you want to tell me what has made it
# like that?") is how the bot offered to listen, not what it asked, and the person has already
# been asked once: naming that ask again sends them round in a circle, so the kind hand-back is
# what they get. A question that was put plainly is a thing they can answer, and that is named.
_INVITATION = re.compile(
    r"^(?:(?:do|would|will|can|could)\s+you\s+(?:want\s+to\s+"
    r"|like\s+to\s+|care\s+to\s+|mind\s+)?"
    r"(?:tell\s+me|talk\s+(?:me\s+through|about)|say|start)\s*(?:a\s+bit\s+)?(?:more\s+)?"
    r"(?:about\s+)?)", re.I)
# "what now" is the plea after bad news rather than a request for a step: a person who says it
# has run out of ideas, and being asked the bot's own question again is a dead end, so the kind
# hand-back stands. Every other bare ask ("what should i do", "what can i do about it") names the
# doing it wants, and the question the bot just put is the concrete thing to answer.
THE_PLEA = re.compile(r"^(?:and |so )?what now$", re.I)
# A question that only offers a hand is not about the thing: "Got it. Is there anything you'd like
# a hand with?" has nothing to answer, so a bare ask after it takes the offer and asks for the
# thing itself. `_an_offer_is_waiting` above names the offers the bot writes in its own voice; this
# names the pool lines, which say "anything" and "something else" instead.
AN_OFFER = re.compile(
    r"\b(?:anything\s+(?:else\s+)?(?:you.?d|i\s+can|to\s+add)|anything\s+on\s+your\s+mind"
    r"|what\s+else|something\s+else|is\s+there\s+anything)\b", re.I)


def _after_a_comfort_line(memory):
    """Whether the bot's own last line was one of its comfort lines.

    A step asked for after a comfort line already has an owner: `step_when_low`, in the module
    that said it, answers with the first step of a bad day ("something to eat, a shower, ten
    minutes outside"). The subject of that thread is how they feel, so naming the bot's own
    question back at them ("is there one thing you can check?") is the colder reply and would
    take the turn off the module that knows what to say. The sets live with the modules that
    speak them, so they are read here rather than imported at the top of this file.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return False
    said = str(turns[-1].get("bot") or "").lower()
    if not said:
        return False
    try:
        from .fallback import COMFORT_SAID
        from ..modules import chat as _chat
        lines = tuple(COMFORT_SAID) + tuple(getattr(_chat, "FEELING_SAID", ()))
    except Exception:  # a module without the set is simply not a comfort line
        return False
    return any(line and line.lower() in said for line in lines)


# The dash a gloss hangs on, and the markers a line can open with. A dash after a marker is the
# marker's own punctuation ("Right - what made you mention it?"), so what follows it is the
# question; a dash after a question is the gloss ("What's the worry - something that has
# happened?"), so what comes before it is the question.
_A_DASH = re.compile(r"^(.*?)\s+[\u2014\u2013-]\s+(.*)$")
_AN_OPENER = re.compile(
    r"^(?:so|and|but|or|ok|okay|right|well|then|now|look|listen|go on|go ahead|come on|tell me)$",
    re.IGNORECASE)


def _the_question_asked(said):
    """The bot's own last question, as the thing the person can answer, or "" if it is too long."""
    text = str(said or "").strip()
    if not text.endswith("?"):
        return ""
    last = re.split(r"(?<=[.!?]) ", text)[-1].strip()
    if not _is_a_question(last):
        return ""
    asked = last[:-1].strip(" ,;:-")
    # A question with a gloss on the end ("What's the worry - something that has happened, or
    # something you are afraid might?") is two sentences of work for the person to answer in one
    # go, so the part in front of the dash is the question that gets asked back.
    split = _A_DASH.match(asked)
    if split:
        front = split.group(1).strip(" ,;:-")
        rest = split.group(2).strip(" ,;:-")
        if _AN_OPENER.match(front) and _is_a_question(rest + "?"):
            # A line that opens on a marker puts the dash after the marker, not after a question:
            # "Right - what made you mention it?" cut in front of the dash leaves "right", which
            # is no question at all, and it was read as one ("I can be specific if you tell me
            # this much: right? Even a line is enough"). The question is the part after the
            # marker.
            front = rest
        asked = front
    if _INVITATION.match(asked):
        return ""
    if not asked or len(asked.split()) > 14:
        return ""
    words = asked.split()
    if words[0] not in ("I", "I'm", "I've", "I'd", "I'll"):
        words[0] = words[0][:1].lower() + words[0][1:]
    return " ".join(words)


def _ends_on_a_question(said):
    """Whether the bot's own last line finished on a question put to the person."""
    text = str(said or "").strip()
    if not text.endswith("?"):
        return False
    last = re.split(r"(?<=[.!?]) ", text)[-1]
    return bool(QUESTION_FRAME.match(last) or QUESTION_FRAME.match(last.rsplit(", ", 1)[-1]))


def _is_a_question(sentence):
    """Whether this sentence of a bot line is a question put to the person."""
    text = str(sentence or "").strip()
    if not text.endswith("?"):
        return False
    if QUESTION_FRAME.match(text):
        return True
    return bool(QUESTION_FRAME.match(text.rsplit(", ", 1)[-1]))


def _steps(said):
    """Every step the answer gave, in the answer's own words, in the order it gave them."""
    # A red flag is not a step, and a health answer ends with one: "Get one checked the same day
    # if it comes on like a thunderclap" was handed back as the thing to do today, on its own,
    # to somebody who had just been told the ordinary steps. The pattern is the one `topics` uses
    # for its own path, imported here rather than copied so the two cannot drift.
    from ..memory.topics import RED_FLAG
    found = []
    parts = []
    for at_sentence, sentence in enumerate(re.split(r"(?<=[.!?]) ", str(said or ""))):
        if (CONDITIONAL_OPEN.match(sentence.strip()) or RED_FLAG.match(sentence.strip())
                or _is_a_question(sentence) or _is_an_explanation(sentence)):
            continue
        # An answer that opens on "Then" is giving its first move, not its second: the word is
        # how the thought was put down, and no step is being continued because there is nothing
        # before it. Read as written it was not a step at all - "Then start with the smallest
        # version of it, not the whole thing" was invisible to this reader, so "what should i do
        # first" after it fell through to handing the bot's own question back ("Nothing to do on
        # my side, honestly"). Only the answer's own opening is trimmed: a "then" later in the
        # answer joins two moves, and cutting it there would hand back the second one.
        opened = THEN_OPEN.sub("", sentence.strip()) if not at_sentence else sentence
        if opened is not sentence:
            sentence = opened[:1].upper() + opened[1:]
            if not sentence:
                continue
        raw = SPLIT.split(sentence)
        kept = []
        for at, chunk in enumerate(raw):
            if at % 2 or not chunk.strip():
                continue
            kept.append((chunk.strip(), raw[at - 1] if kept else ""))
        if (len(kept) > 1 and CONTRAST.search(kept[0][0])
                and _doing_word(kept[1][0].split()) in IMPERATIVES):
            # A clause that weighs one thing against another in front of a colon is a heading for
            # the list, not the first thing to do: "Change a few things you can keep doing rather
            # than going on a diet: fill half the plate with vegetables" gave back "Change a few
            # things you can keep doing rather than going on a diet first, then work down the
            # list", where the order lands on the comparison instead of on the step. The
            # instruction is the one after the colon. A plain clause in front of a colon is not
            # dropped ("Turn it off and keep it off: do not charge it" is the first thing to do),
            # so only the contrast is the tell.
            kept = kept[1:]
        if len(kept) > 1 and _doing_word(kept[0][0].split()) not in IMPERATIVES:
            # "That's the one: split your time in three", "Cheapest fix: bleed the radiators":
            # the piece in front of the colon is the answer naming its own line, not the
            # instruction, and it is dropped the same way.
            kept = kept[1:]
        if len(kept) > 1 and all(sep == ": " for _, sep in kept[1:]):
            # The colon is the answer explaining its own instruction, and the explanation is the
            # part a friend would say ("turn it off and keep it off: do not charge it"), so the
            # instruction is read whole with the explanation still on it. The pieces stay on the
            # list as well, because a later ask wants the one after the first. A dash is not an
            # explanation ("keep the room cool and dark - get up" says two things), so it is left
            # as it is written.
            parts.append((": ".join(text for text, _ in kept), True))
        parts.extend((text, False) for text, _ in kept)
    for part, spread in parts:
        if RED_FLAG.match(part):
            continue
        part = re.sub(r"\([^)]*\)|\S*\.(?:com|co\.uk|org|net|gov)\S*", " ", part)
        part = " ".join(part.strip(" .:;,-").split())
        if not part:
            continue
        words = part.split()
        if _doing_word(words) not in IMPERATIVES or COPULA.match(part):
            continue
        if TARGET_SHAPE.match(part):
            continue
        if ABOUT_THE_TALK.search(part):
            continue
        # The first clause, but "and" between two numbers is a range and not a new clause
        # ("top the pressure up to between 1 and 1.5 bar" keeps its second half that way).
        protected = re.sub(r"(?<=\d) and (?=[\d.])", " \x00 ", part)
        if spread:
            # The instruction the answer opened with and the detail it gave for it are one move:
            # "Find what starts it and block that first: a curtain over the window he watches" is
            # the step, and cutting it at its own " and " left "Find what starts it", half an
            # instruction, with the half that says how to do it thrown away.
            opening, _, detail = protected.partition(": ")
            opening = _first_clause(opening, and_break=False).replace("\x00", "and")
            opening = opening.strip(" .:;,-")
            detail = detail.replace("\x00", "and").strip(" .:;,-")
            if DETAIL_STATEMENT.search(detail):
                # "Cut the distance and the speed for a week or two: most running knee, shin and
                # ankle pain is too much, too soon" - the colon hands on a statement about the
                # thing rather than the rest of the instruction, and cutting it at its own comma
                # left "most running knee" dangling off the step. The step is the instruction
                # before the colon; the explanation is not something to tell anybody to do.
                detail = ""
            else:
                detail = _first_clause(detail).strip(" .:;,-")
            head = "%s: %s" % (opening, detail) if detail else opening
            if len(head.split()) > STEP_WORDS and "," in detail:
                detail = detail.split(",")[0].strip(" .:;,-")
                head = "%s: %s" % (opening, detail) if detail else opening
            if len(head.split()) > STEP_WORDS:
                # Longer than a step anybody says out loud: the instruction on its own is the
                # step, and the explanation is left behind rather than cut in half.
                head = _shorten(opening, opening.split()) or opening
        else:
            clause = _first_clause(protected).replace("\x00", "and").strip(" .:;,-")
            head = _shorten(clause, clause.split()) if len(clause.split()) >= 3 else ""
            if not head:
                # A first clause too short to quote ("Blot") is no reason to quote the whole part
                # with its own order still in it: "Blot, don't rub, with kitchen paper, then dab"
                # arrived as "Blot, don't rub, with kitchen paper, then dab", the order said twice
                # and the last item left hanging without its verb. Cutting at the answer's own
                # "then" keeps the one step it wrote.
                trimmed = re.split(r",? then ", part)[0]
                head = _shorten(trimmed, trimmed.split()) if len(trimmed.split()) >= 2 else ""
            if not head:
                head = _shorten(part, words)
        if not head:
            # The answer's next instruction could not be quoted whole. Walking on past it quotes
            # the conditional half instead ("stop topping it up first"), so the list stops here -
            # but a step found before it stands: "Turn it off and keep it off" was read cleanly
            # and "wipe it, shake out the port gently and leave it somewhere warm and airy for at
            # least 24 hours" was not, and returning nothing threw the good first move away.
            return found
        words = head.split()
        if not words or words[-1] in HANGING or head in found:
            continue
        # The verb of a sentence is capitalised and the list is not: "Ask once, plainly ..."
        # is the same instruction as "ask once", and reading it case-sensitively threw away
        # every answer that opens with its step instead of burying it after a colon. The verb
        # is the first word that is not one of the when words in front of it, so "three times
        # a week do sit-to-stands" still counts.
        if _doing_word(words) not in IMPERATIVES:
            continue
        found.append(head)
    return found


def _doing_word(words):
    """The first word that is not one of the when words in front of a step."""
    # A part that opens on an article is a noun phrase saying what the thing is ("A dry mouth
    # usually means mouth breathing"), not an instruction, however verb-shaped the word after
    # the article looks. Nobody writes a step as "a ...".
    if words and words[0].strip("*_`(\"'[]").lower() in ("a", "an", "the"):
        return ""
    for index, word in enumerate(words[:5]):
        core = word.strip(",;:-\u2014\u2013").lower()
        if core in WHEN:
            continue
        return core
    return ""


def _action_count(said):
    """How many things the answer told them to do, so a "list" is only promised when there is
    one. A clause counts when it opens with a verb, which is how the answers write a step
    ("put a bowl under it", "ease off hills", "take paracetamol")."""
    # A question is not one of the things the answer told them to do, so it does not make the
    # answer a "list" ("Sorry. Do you want to tell me what has made it like that?").
    said = " ".join(s for s in re.split(r"(?<=[.!?]) ", str(said or ""))
                    if not _is_a_question(s))
    total = 0
    for part in re.split(",| and | then |\\. |; |: | - | — | – ", said):
        words = part.strip(" .:;,-()").split()
        if words and _doing_word(words) in IMPERATIVES:
            total += 1
    return total


def _no_hanging_end(when):
    """The condition with any trailing join, comma or half-list taken off its end."""
    text = str(when or "").strip(" ,;:")
    while True:
        shorter = re.sub(r"(?:^|[ ,]+)(?:and|or|but|then|so|also|plus)$", "", text).strip(" ,;:")
        if shorter == text or not shorter:
            break
        text = shorter
    return text


# A red flag is written as a description as often as it is written with an "if": "Shaking that
# has crept on over months, is much worse on one side, or comes with a slow walk or stiff arm is
# worth a GP appointment". There is no "if" anywhere in that sentence, so `_when` found nothing,
# and a bare "is that bad" on top of it was "Alright then - good luck with it". The relative
# clause is what the answer puts the referral on, so it is the answer's condition in exactly the
# way an "if" is. The verbs are the ones a red flag is written with, so a description that is not
# a condition ("the noise that it makes is normal, but see a plumber") is not read as one.
CONDITION_VERBS = frozenset((
    "comes", "come", "gets", "get", "turns", "turned", "starts", "started", "goes", "went",
    "spreads", "spread", "wakes", "woke", "lasts", "lasted", "keeps", "kept", "has", "have",
    "develops", "developed", "bleeds", "bled", "swells", "swelled", "is", "are", "was", "were",
    "hurts", "stops", "stopped", "changes", "changed", "moves", "moved", "suddenly",
))
# A described condition that ends on one of these was cut in the wrong place: those words are
# the subject of the half-sentence that is left, not the end of a condition ("... is true, or
# you").
CONDITION_HANGING = frozenset("""
you i he she we they it or and but so if when with of the a an is are was were been t
""".split())
# The verb the referral itself is made of ("... passing water is a GP matter"): the condition
# ends where that verb begins. A verb in the middle of a list is part of the condition, not the
# end of it - "has crept on over months, is much worse on one side" - so the cut is the last one
# whose remainder is short and free of commas ("worth a", "a", "looking at today:"). When no verb
# qualifies, the clause cannot be separated safely ("a finger that ... behind a ring needs the
# ring cut off, so go to A&E") and nothing is handed back.
REFER_VERB = re.compile(
    r"\b(?:is|are|was|were|needs|needed|means|wants|should|must|will\s+need)\b", re.I)
# A tail that restates the referral in the answer's own words is not part of the condition, and
# handing it back reads as a second sentence bolted on: "if you sweat buckets from one place or
# at night, that is worth a GP visit, so that is what to watch".
RESTATED = re.compile(r",\s*(?:that|this|which|it)\s+(?:is|means|needs|wants|should)\b", re.I)


# The words a referral is hung on when the answer writes its condition as a description instead of
# an "if": "Shaking that has crept on over months ... is worth a GP appointment".
RELATIVE = re.compile(r"\b(?:that|which|who)\s+", re.I)


def _described_clause(sentence):
    """The condition a sentence writes as a description: (from, to, its words), or None.

    "Shaking that has crept on over months, is much worse on one side ... is worth a GP
    appointment" hangs its referral on the clause that follows "that", and so does "one that is
    also dull or sick needs to be seen today". Where the clause sits is what tells a referral
    inside it from one beside it: the dog answer has "worth a call to the vet" flat, and a
    condition next to it, and only the second is a warning for later.
    """
    referral = REFER.search(sentence)
    if referral is None:
        return None
    head = sentence[:referral.start()]
    marker = None
    for found in RELATIVE.finditer(head):
        marker = found
    # "That is a vet visit rather than a brushing one" opens on a demonstrative, not on a
    # relative clause: there is no subject in front of it to describe.
    if marker is None or not head[:marker.start()].strip():
        return None
    start = marker.end()
    clause = head[start:]
    cut = None
    for found in REFER_VERB.finditer(clause):
        rest = clause[found.end():].strip(" ,")
        if len(rest.split()) <= 4 and "," not in rest:
            cut = found.start()
    if cut is None:
        return None
    words = clause[:cut].strip(" ,;:-").split()
    if not 2 <= len(words) <= 26:
        return None
    if words[-1].strip(",;:").lower() in CONDITION_HANGING:
        return None
    if words[0].strip(",;:").lower() not in CONDITION_VERBS:
        return None
    # The clause runs to where the referral itself begins: "worth a GP appointment" is the
    # answer's referral, and the cue inside it belongs to the condition rather than beside it.
    return start, referral.start(), " ".join(words)


def _in_a_described_clause(sentence, at):
    """True when position `at` in the sentence is inside the condition it describes."""
    found = _described_clause(sentence)
    return found is not None and found[0] <= at < found[1]


def _a_described_condition(sentence):
    """The relative clause a sentence hangs its referral on, or "" when it hangs on an "if"."""
    found = _described_clause(sentence)
    if found is None:
        return ""
    # Said as the answer's subject rather than as a thing that happens to it: the answer is about
    # "shaking", the condition is about "it", and repeating the subject back ("...if shaking has
    # crept on over months") reads as a definition rather than as a warning.
    return "it " + found[2]


def _an_if_that_is_a_condition(sentence):
    """Where the sentence's " if " puts a condition on the referral, or -1.

    "do not wait to see if it passes" is a test the person runs, not a condition for care, and
    reading it as one took the verdict off the pale-gums answer: "Ring the vet now and go in
    today ... do not wait to see if it passes" came back as "Ordinary on its own, yes. It stops
    being ordinary if it passes" - an all-clear over an answer that opens "Pale, white or blue
    gums are an emergency" (main answers it with the yes pool, and this keeps that). The word in
    front of the "if" is what tells the two apart.
    """
    start = 0
    while True:
        at = sentence.find(" if ", start)
        if at < 0:
            return -1
        before = re.findall(r"[a-z']+", sentence[:at].lower())
        if not before or before[-1] not in LOOK_AND_SEE:
            return at
        start = at + 4


# The verbs that make the "if" after them a test rather than a condition: "see if it passes",
# "check if the noise stops", "know if it is broken".
LOOK_AND_SEE = frozenset((
    "see", "check", "know", "wait", "tell", "find", "wonder", "decide", "guess", "ask",
    "notice",
))


def _a_judgement_fence(said):
    """The condition a closing, declarative referral puts on itself, or "".

    Only the last sentence is read, and only when it names a clinician and carries a list in
    front of the referral ("Anything hard, painless, fixed in place, or still there after three
    weeks needs a GP"). Narrow on purpose: `REFER` and `_when` are left exactly as they are, so
    no step or how-to answer changes.
    """
    sentences = [s for s in re.split(r"(?<=[.!?]) ", said.strip()) if s.strip()]
    if not sentences:
        return ""
    last = sentences[-1]
    if NAMES_A_CLINICIAN.search(last) is None:
        return ""
    found = re.search(r"(?i)\b(?:anything|any [a-z-]+)\b(.*?)\b(?:needs?|should be|is worth|wants)\b",
                      last)
    if found is None:
        return ""
    clause = found.group(1).strip(" ,;:-")
    if "," not in clause and " or " not in clause:
        return ""
    words = clause.split()
    if not 2 <= len(words) <= 26:
        return ""
    return clause

def _after_the_if(sentence):
    """The condition a sentence writes after its "if", cut where the answer asks something."""
    opens = re.match(r"(?:so )?if ", sentence, re.I)
    if opens:
        # "If the noise comes with pain or swelling, treat it as pain: ..." opens on its
        # condition, so the sentence carries the "if" without a space in front of it. The
        # condition runs to where the answer starts telling them to do something, not to the
        # first comma: "If it locks out twice, or you smell gas, stop and call ..." has two
        # conditions in it, and cutting at the comma kept the milder half.
        when = sentence[opens.end():]
        when = re.split(r"(?:^|, |; | and | then | so )(?:and )?(?:get|see|ring|call|take|go|"
                        r"book|treat|watch|keep|check|apply|cover|use|rest|ice|put|give|try|"
                        r"test|monitor|stop|unplug|switch|leave|turn|have|ask|phone|contact|"
                        r"speak|mention)\b", when)[0]
    else:
        at = sentence.find(" if ")
        if at < 0:
            return ""
        when = sentence[at + 4:].rstrip(" .")
        # The condition ends where the answer starts telling them to do something else. The
        # doing word has to begin a clause: "or you cannot put your weight on it" is the
        # condition itself, and cutting at "put" left "or you cannot".
        when = re.split(r"(?:^|, | and | then )(?:and )?(?:get|see|ring|call|take|go|book|"
                        r"treat|watch|keep|check|apply|cover|use|rest|ice|put|give|try|test|"
                        r"monitor|have|ask|phone|contact|speak|mention)\b", when)[0]
    # The cut lands mid-sentence whenever the answer joins its referral with a conjunction
    # ("... or the pain came on after a fall, and see a GP if it is no better"), and half a
    # sentence is worse than none: "See someone if ... a fall, and." A list that ends on a
    # joining word is still going somewhere, so drop it and the comma in front of it.
    when = RESTATED.split(when)[0]
    when = _no_hanging_end(when.strip(" ,."))
    return when if len(when.split()) >= 2 else ""


def _when(said):
    """The condition the answer itself put on getting someone in."""
    for sentence in re.split(r"(?<=[.!?]) ", said):
        if not REFER.search(sentence):
            continue
        opens = re.match(r"(?:so )?if ", sentence, re.I)
        # A sentence's " if " is a condition on the referral, or it is a test the person is told
        # to run ("do not wait to see if it passes"). Both cases keep the reader below; only the
        # second one is not a condition at all.
        if opens or _an_if_that_is_a_condition(sentence) >= 0:
            when = _after_the_if(sentence)
            if when:
                return when
            continue
        # The same condition written as a description instead: "Back pain that comes with
        # numbness, weakness or trouble passing water is a GP matter."
        when = _a_described_condition(sentence)
        if when:
            return when
    return ""


# A referral the answer states as its own judgement rather than as an instruction. REFER reads
# only the imperative ("see your GP"), and that is deliberate: read as an instruction, "Pins and
# needles in the fingers that wake you is worth a GP visit" annotated a wrist that is "usually an
# overused tendon" with "yes, that one wants a proper look". So `_when` finds no condition in the
# judgement shapes, and a person who asked "should i see someone" straight after one got the
# composer's own punt instead - "i have a sore throat" / "should i see someone" was answered
# "Can't call that one for you, sorry" over an answer that had already said "Worth a doctor if it
# is one-sided and bad, or if your voice has gone for more than a couple of weeks".
# DECLARATIVE_REFERRAL holds the "worth a GP" shapes; these are the two other ways the same
# judgement gets written.
JUDGED_REFERRAL = re.compile(
    r"\b(?:is|are|was|were) (?:a|the|your) reason to (?:ring|call|see|ask|contact|speak|get)\b"
    r"|\btake (?:it|that|this|them|him|her) (?:to|along to|back to) (?:a |your |the )?"
    r"(?:pharmacist|gp|doctor|nurse|vet|dentist|optician)\b",
    re.I,
)
# "Three or more in a year is worth a GP review", "A reading of 140/90 or higher, seen twice at
# home, is high and worth a GP check": the threshold is the subject and the referral is the
# answer's judgement on it.
STATES_A_REFERRAL = re.compile(
    r"^(?P<when>.+?)\s+(?:is|are)\s+(?:high and |low and |still )?"
    r"(?:worth|a reason to|the point (?:at which|where))\b",
    re.I,
)
# A subject that names nothing is the thing again rather than a threshold: "It is worth a GP
# visit if ..." and "Either of those is worth a call" have already said what they have to say.
NAMES_NOTHING = frozenset((
    "it", "that", "this", "they", "there", "which", "either", "one", "both", "any", "all",
    "any of that", "any of those", "any of them", "either of those", "either of them",
    "one of those", "both of those", "some of that", "all of that", "the rest", "one or both",
    "none of that", "anything", "something", "much", "most of it",
))
# A threshold is a short thing; a subject this long has become the paragraph again.
STATED_LONGEST = 16


def _stated_before_the_judgement(sentence):
    """The thing a sentence puts in front of its judgement ("blood in it is worth a GP's time")."""
    frame = STATES_A_REFERRAL.match(sentence)
    if frame is None:
        return ""
    when = _no_hanging_end(frame.group("when").strip(" ,;:"))
    if not 2 <= len(when.split()) <= STATED_LONGEST:
        return ""
    if when.strip(" .,").lower() in NAMES_NOTHING:
        return ""
    # A referral that is itself the subject ("A vet visit is worth it too - pain, a bad ear or
    # failing eyesight is often behind a first bite") says nothing about when, and "only reflux,
    # coughing or trouble feeding is worth a call" names the thing that is *not* worth it.
    if NAMES_A_CLINICIAN.search(when) or when.split()[0].lower() in ("only", "just"):
        return ""
    # The subject opens the sentence and these lines put it after a colon or a word, so a capital
    # there was only ever the capital of the sentence's first word.
    head = when.split()[0]
    if head[:1].isupper() and (head[1:].islower() or len(head) == 1) \
            and head.lower() not in ("i", "a&e", "nhs"):
        when = when[0].lower() + when[1:]
    return when


def _stated_referral(said):
    """The threshold the answer stated as its own judgement, and how it is written.

    The kind matters because the two cannot be phrased alike: a clause reads after an "if"
    ("...if it is one-sided and bad") and a thing does not ("if three weeks of it" is clipped),
    so a noun is named as the thing that changes the answer instead.
    """
    for sentence in re.split(r"(?<=[.!?]) ", said):
        if not (JUDGED_REFERRAL.search(sentence) or DECLARATIVE_REFERRAL.search(sentence)
                or REFER.search(sentence)):
            continue
        opens = re.match(r"(?:so )?if ", sentence, re.I)
        if opens or " if " in sentence:
            when = _after_the_if(sentence)
            if when:
                # The lines read the clause on the back of their own "if" or "unless", so a
                # second one in the middle of it doubles the word: "Not yet, unless it is
                # one-sided and bad, or if your voice has gone".
                when = re.sub(r"\b(or|and) if\b", r"\1", when)
                # A dash in the middle of one starts the aside that follows it ("... worth a GP
                # look only if it is painful, growing fast or stops you using the hand - they can
                # drain it, but a lot come back"), and the aside is not part of the threshold.
                when = _no_hanging_end(re.split(r"\s+-\s+|\s+--\s+", when)[0].strip(" ,.;:"))
                # "... it is this hard to wake most days, ask the GP about sleep apnoea" carries
                # the appointment after the threshold: "ask" is not one of the doing words the
                # cut above ends a condition at, and half a sentence bolted onto the back of the
                # line is the noise these lines exist to avoid.
                when = when.split(", ask ")[0].strip(" ,.;:")
                if len(when.split()) >= 2:
                    return when, "clause"
            continue
        when = _stated_before_the_judgement(sentence)
        if when:
            return when, "noun"
    return "", ""


# The verbs an answer uses when the point of it is a job to do. `_step` holds the ones a first
# move is made of, in the shape a person can be told back ("Bleed the radiator"); this is the
# wider list, only ever used to answer whether an answer is a how-to at all, so a long one can
# still count ("Cool the room before you get in, not after").
DOING = IMPERATIVES | frozenset((
    "run", "cool", "warm", "heat", "wipe", "spray", "scrape", "sand", "drain", "vacuum",
    "replace", "tighten", "loosen", "unscrew", "test", "brush", "scrub", "soak", "fill",
    "pour", "freeze", "thaw", "reheat", "serve", "add", "mix", "stir", "grate", "slice",
    "chop", "cover", "wrap", "store", "label", "weigh", "measure", "book", "text", "email",
    "write", "plant", "water", "prune", "feed", "repot", "keep", "hang", "place", "swap",
    "switch", "fit", "fix", "seal", "paint", "install", "bleed", "balance", "ventilate",
    "insulate", "lag", "defrost", "descale", "replace", "trim", "sweep", "mop", "hoover",
    # What a person does about the thing as often as the tools do: "if you are hungry in the
    # morning, eat something with protein and fibre" is the answer's job, and without "eat" the
    # skipping-breakfast answer read as an answer with nothing in it.
    "eat", "drink", "sleep", "nap", "walk", "stretch", "rest", "sit", "stand", "try",
))


def _danger(said):
    """The first harm the answer names that is not itself denied ("not dangerous").

    A harm named inside an "if" is the answer's warning for later, not its verdict now: "My arm
    aches" ends "treat a heavy left arm with tightness in the chest, sweating or breathlessness
    as an emergency", and that answer is not an answer that says the ache is an emergency.
    """
    best = None
    for word in DANGER:
        start = said.find(word)
        while start >= 0:
            before = said[max(0, start - 14):start]
            sentence = said[max(0, said.rfind(". ", 0, start)):start]
            condition = re.search(r"\b(?:if|unless|when|once)\b", sentence)
            if not NEGATED.search(before) and not condition:
                if best is None or start < best:
                    best = start
                break
            start = said.find(word, start + len(word))
    return best


def _a_how_to(said):
    """True when the point of the answer is a job to do, in any of its sentences."""
    # A step can open on "so" or follow a semicolon, and both are the answer telling somebody to
    # do something: "She is bringing food to the household rather than being naughty, so take the
    # bird away in gloves". Reading only the comma and "and" heads missed every step written that
    # way, and the answer came back as "I don't know enough to answer that honestly".
    for part in AFTER.split(said)[1:] + re.split(r"(?<=[.!?]) ", said):
        # Any clause of the sentence can be the doing, not only the first: "she is bringing food
        # to the household rather than being naughty, so take the bird away in gloves" is an
        # answer that tells somebody what to do, and reading only the head of the sentence made
        # it look like an answer with nothing in it.
        for clause in re.split(r",|;| and | then | so | but ", part.strip()):
            words = clause.strip(" .:;,-").split()
            if words and words[0].lower() in DOING:
                return True
    return False


# The verdict below is a reading of the answer, not a claim about the world, so it is the same
# for a line the person asked for advice ("can i freeze rice") as for one that described a thing
# happening to them ("damp in the corner of my bedroom"): either way the answer gave a fix and
# named no danger, and "there is no warning in that" is honest on both. An earlier draft kept an
# `ASKS_FOR_ADVICE` guard for the asking half; the pool answers both correctly, so the guard is
# gone rather than left in place unread.


def _round_robin(pool, said):
    """The same pool, rotated by a positional hash of the answer.

    `pick` seeds on the sum of the characters, and two long answers collide on that easily: the
    damp, the rice and the radiator are all ordinary healthy sentences, and the sum landed on
    the same line for all three, so three rows of the deck got one sentence word for word. A
    rotation weighted by where the letters sit in the answer spreads them; `pick` still decides
    which of the rotated pool is said, so the no-repeat rules keep working.
    """
    if not pool or not said:
        return pool
    start = sum((i + 1) * ord(c) for i, c in enumerate(said)) % len(pool)
    return tuple(pool[start:]) + tuple(pool[:start])


def _says_what_it_is(said):
    """True when some clause of the answer tells the person something rather than telling them
    to do something.

    "Half fill the kettle with equal parts water and white vinegar, boil it and leave it half an
    hour" is a recipe and nothing else: it answers how to clean a kettle, not whether limescale
    matters, so "is that bad" after it is still the person's own question and the composer has
    nothing to say about it. An answer that explains the thing first - "she is bringing food to
    the household rather than being naughty, so take the bird away" - has said something, and
    that reading is the verdict.
    """
    for part in AFTER.split(said)[1:] + re.split(r"(?<=[.!?]) ", said):
        for clause in re.split(r",|;| and | then | so | but |:", part.strip()):
            words = clause.strip(" .:;,-").split()
            # "Half fill the kettle ..." is an instruction with a qualifier in front of the verb,
            # so the verb can be the second word as well as the first.
            leads = [word.lower() for word in words[:2]]
            if len(words) >= 4 and not any(word in DOING for word in leads):
                return True
    return False


# A long stretch the person's own line says the thing has been going on: "for months", "six
# months now", "years". It is compared with the span the answer set on watching the thing, so a
# complaint older than the answer's own threshold is not called ordinary.
LONG_SPAN = re.compile(
    # "three weeks", "ten days", "5 weeks": the timescale said as a count of days or weeks, which
    # is the same timescale an answer sets with "if it's still the same in a week or two". The
    # count used to be read for months and years only, so a person who had already waited three
    # weeks was still told to watch it for a week or two.
    r"\b(?:two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:days?|weeks?|fortnights?)\b|"
    r"\ba\s+fortnight\b|"
    r"\b\d+\s*(?:months|years)\b|\bmonths?\b|\byears?\b|\bfor\s+(?:a\s+long|ages)\b",
    re.I)
# The span an answer sets on watching it: "if it's still the same in a week or two", "you wake
# drenched for weeks", "if it has not shifted in a few days". Only days and weeks: an answer that
# already allows months is not shorter than what the person has had.
HEDGE_SPAN = re.compile(
    # "in a week", "in a fortnight", "within a fortnight": the article is how English sets almost
    # every threshold, and it was not in the list of counts, so the commonest hedge of all - "if
    # it's still the same in a week or two" - was read as no timescale at all.
    r"\b(?:in|for|after|within)\s+"
    r"(?:a few|a couple of|a|an|one|two|three|four|five|six|several|\d+)?\s*"
    r"(?:days?|weeks?|fortnights?)(?:\s+or\s+(?:two|three|four))?\b|"
    # "three weeks of it is a reason to ring the surgery or 111": the same timescale said as a
    # count of the thing itself rather than after "in" or "for".
    r"\b(?:two|three|four|five|six|seven|\d+)\s+(?:days?|weeks?)\s+of\s+(?:it|this|that)\b|"
    # "See a GP if it lasts more than three weeks": the threshold with no "in" or "for" in it,
    # which is how most cards write the point to come back. The cough card says exactly this, and
    # read as no timescale at all it told somebody who had coughed for months to watch for three
    # weeks first.
    r"\b(?:lasts?|lasted|lasting|continues?|continued|continuing|goes? on|gone on|drags? on|"
    r"more than|longer than|over|beyond|past)\s+"
    r"(?:a|an|one|two|three|four|five|six|seven|several|\d+)?\s*"
    r"(?:days?|weeks?|fortnights?|months?)\b",
    re.I)


def _the_line_it_answered(said, memory):
    """The person's own line that the answer in `said` was answering.

    Not the last line they typed: the line that prompted a bare "is that bad" is the one before
    it, and that is the line whose span says how long the thing has been going on.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not said:
        return ""
    for last in reversed(turns):
        if not isinstance(last, dict):
            continue
        # Both sides flattened: the answer is read back with its own capitals ("Run a hot 60C
        # service wash"), so a comparison against the raw text never matched and the line the
        # person wrote was never found - the timescale and the fence both stood down silently.
        if _flat(last.get("bot")) == _flat(said):
            return _flat(last.get("user"))
    return ""


def _past_the_timescale(said, memory):
    """True when the answer set a timescale on watching it and the person is already past it.

    Read only where the answer hedged on time and the person's own line says the thing has been
    going on longer: "i wake up soaked in sweat every night for months" is not answered by
    "Not the thing itself, no - what would change it is you wake drenched for weeks", because
    the answer's own threshold is already met. A line with no span ("i wake up soaked") keeps
    the ordinary reading: there the answer is telling them the timescale to watch.
    """
    if not said or HEDGE_SPAN.search(said) is None:
        return False
    line = _the_line_it_answered(said, memory) or ""
    if LONG_SPAN.search(line) is None:
        # The answer answered the how-to line, and the span is one line further up.
        line = _the_span_further_up(said, memory) or line
    ours = LONG_SPAN.search(line)
    # "three weeks ago" is behind the person, not in front of them: that is not a span they have
    # waited out.
    if ours is not None and re.search(r"\b(?:days?|weeks?)\s+ago\b", line, re.I):
        ours = None
    return ours is not None


def _subject_words(text):
    """The long words of a line, cut to five letters: "coughs" and "cough" are the same subject."""
    return {word[:5] for word in _words(text)
            if len(word) >= 5 and word not in FENCE_FILLER}


def _the_span_further_up(said, memory):
    """A span further up the chat, on the same subject as the answer in front of the doubt.

    The span and the doubt are rarely in the same line: "i have had a cough for months" / "what
    should i do first" / "is that bad" is one chat, and the answer that hedged on three weeks
    answered the middle line, which says nothing about how long. Read on its own, that line has no
    span, so the fence said "not yet - three weeks of it is the point where it wants a person" to
    somebody who is already at months.

    The subject is what keeps it honest: an earlier line counts only when the answer that answered
    it and the answer in front of us are about the same thing, so a "for months" about the rent
    cannot decide a cough. Getting this wrong errs one way - no span means the ordinary reading,
    which is what the chat had before - so where the span comes from is read generously.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or len(turns) < 2:
        return ""
    here = _subject_words(said)
    if not here:
        return ""
    for turn in reversed(turns[:-1]):
        if not isinstance(turn, dict):
            continue
        line = _flat(turn.get("user"))
        if LONG_SPAN.search(line) is None:
            continue
        if _subject_words(turn.get("bot")) & here:
            return line
    return ""


# The words a condition hangs its meaning on, kept out of the comparison below. Articles,
# pronouns and the little verbs a condition is built with carry no subject of their own: "it
# stops" says nothing about what stopped, and "feeding" does.
FENCE_FILLER = frozenset("""
a an the it its this that these those there is are was were be been being am i you your he she
they we my mine our their his her them us of to in on at for with and or but so then than if
when while as by from up out off down not no any more very still just also both either own same
other thing things way lot lots bit does do did done gets get getting goes going come comes
coming keep keeps kept start starts started stop stops stopped carry carries carried turn turns
turned become becomes became make makes made up
""".split())


def _stems(text):
    """The content words of a line, stemmed, so "feeding" and "feeds" are the same word."""
    words = set()
    for word in re.findall(r"[a-z']+", _flat(text).lower()):
        word = word.strip("'")
        if len(word) < 4 or word in FENCE_FILLER:
            continue
        for suffix in ("ing", "ed", "es", "s"):
            if word.endswith(suffix) and len(word) - len(suffix) >= 4:
                word = word[: -len(suffix)]
                break
        words.add(word)
    return words


def _the_fence_is_their_own_line(said, memory):
    """True when the answer's condition is the very thing the person just told us.

    Read from the answer's own words against the person's own words, not from the topic: when
    half the condition's content words are theirs, the condition describes what they said, and
    quoting it back to them decides nothing. "i sweat a lot at night" / "is that bad" got "It
    stops being ordinary if you sweat buckets from one place or at night": the answer's own "if"
    is already true of the line in front of it, so the reassurance in front of it is wrong.
    """
    when = _when(said)
    if not when:
        return False
    fence = _stems(when)
    theirs = _stems(_the_line_it_answered(said, memory))
    if not fence or not theirs:
        return False
    shared = fence & theirs
    return bool(shared) and len(shared) * 2 >= len(fence)


# A death is not a symptom to ask about, nor a thing to rule ordinary. "i had a miscarriage" /
# "is that bad" was answered "Say a bit more: how long has it been like that, and what does it
# cost you day to day?", which is the coldest line in this file over a bereavement.
LOSS_WORDS = re.compile(
    r"\b(?:died|dies|death|dead|funeral|cremation|burial|passed away|miscarriage|miscarried"
    r"|stillborn|bereave\w*|lost (?:the|my) baby|took (?:his|her|their) own life)\b", re.I)


# A mood is not a thing to put right, and "nothing in that answer needs anyone yet" over a low
# line rules on a feeling the composer read as a fault to fix: "i cant be bothered to leave the
# house" / "is that bad" was told "Nothing in that answer needs anyone yet - it is the standard
# way to handle it", which is the reassurance a low line least wants. The backstop's line asks
# how long and what it costs, which is the question a friend asks.
MOOD = re.compile(
    r"\b(?:feel(?:ing|s|t)?\s+(?:\w+\s+){0,2}(?:low|down|flat|numb|sad|anxious|worried|stressed"
    r"|overwhelmed|lonely|rubbish|awful|miserable|hopeless|empty|knackered|exhausted)"
    r"|depress\w*|anxi\w*|panick?\w*|miserable|lonely|burnt out|burned out|burnout"
    r"|can(?:'t|t|not)? be bothered|no energy|no motivation|dont want to go out"
    r"|dont want to see anyone)\b", re.I)


def _a_mood(memory):
    """True when the line the ask follows is about how the person feels rather than a body."""
    return any(MOOD.search(line) for line in _the_last_person_lines(memory, 2))


def _about_a_death(memory):
    """True when one of the last few lines is a death or a miscarriage.

    The death word alone is not enough: a laptop, a battery and a boiler "die" too, and "dead"
    is as often the intensifier ("dead comfy", "dead quiet", "dead tired"). Read that way a
    fault got the condolence: "my laptop battery dies fast" / "is it safe" was answered "That is
    not a thing to call bad, and not a thing to carry on your own", which is the coldest line in
    this file over a flat battery. The thing the word is about decides, and `compose/loss.py` is
    where that reading lives - it is already the reader that tells a phone that stopped from a
    father who died.
    """
    for line in _the_last_person_lines(memory, 3):
        if not LOSS_WORDS.search(line):
            continue
        if _a_thing_stopped is not None and _a_thing_stopped(line):
            continue
        return True
    return False


def _the_last_person_lines(memory, count):
    """The last few things the person said, oldest first, skipping the echoes doubt asks make."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ()
    lines = [_flat(turn.get("user")) for turn in turns if isinstance(turn, dict)]
    return [line for line in lines if line][-count:]


# The answer above is a recommendation the person asked for ("should i text my ex", "should i go
# to the wedding"), and the doubt on top of it is about that recommendation: "is that ok". Every
# arm below is about what the person has ("i have a cough") or does ("i keep putting off my
# emails"), so a step the bot recommended reached none of them, and the chat pool closed the
# conversation - "Alright then - good luck with it" over the one answer that had given them
# something to do. The step is the answer, so it is given back with the ruling on it.
ADVICE_OK_LINES = (
    "Yes - go with that. {step}",
    "That is the right first move, and it is the one I would take: {step}",
    "Go with it. {step} If it feels wrong once you are in it, say so and we can change tack.",
)
# The line that asked for a recommendation, rather than reporting something to be judged. Read
# from the person's own words: the same answer's step over "i have a cough" is still the floor's
# question, because they did not ask for advice, they said what they had.
ASKED_FOR_A_CALL = re.compile(
    r"^\s*(?:so\s+|ok(?:ay)?\s+)?(?:should|shall|do you think|would you|what would you do|"
    r"is it (?:a good idea|ok|okay|wise|worth it|fine) to|is it wrong to|am i (?:ok|okay|right) to)\b")


def _a_job_to_do(text):
    """True when a run of words holds an instruction the person could go and do.

    Read clause by clause, because an answer often puts the job after the reason for it: "The wait
    is worse than the call nearly every time, and you can keep it short once you are through - say
    the one thing you actually want to say" is advice with its step in the second half, and
    reading only the opening of the sentence would call it a verdict. `_STEP_OPENERS` is the
    vocabulary `_an_instruction_and_nothing_else` already trusts for "this answer tells them what
    to do", so the two readings cannot drift apart.
    """
    for piece in re.split(r"[.!?;:]\s+| \u2014 | \u2013 | - ", _flat(text)):
        words = _WORD.findall(piece.strip(" ,-"))
        if words and words[0] in _STEP_OPENERS:
            return True
    return False


def _the_advice_itself(said):
    """The answer's first real sentence, when the answer holds a job to go and do.

    "Go, and give yourself an exit:" is the opening of a recommendation whose rest is a list, and
    handed back with its colon it reads as a sentence that stops dead. The words are the answer's
    own either way.

    It also has to hold a job: an answer can open on a verdict or on a shrug rather than on
    something to do, and "Yes - go with that. Not unreasonable at all." (over "should i worry") or
    "Yes - go with that. Not mine to decide, sorry." (over "should i ring in sick") tells the
    person to go and do nothing. `_a_job_to_do` is the reading for that, and where no clause of
    the answer opens on a job the arm stands aside and the line it replaced keeps the turn.
    Found by @snappy-net on #7845.
    """
    for sentence in re.split(r"(?<=[.!?]) ", " ".join(str(said or "").split())):
        clean = sentence.strip()
        if clean.endswith(":"):
            clean = clean[:-1].strip()
        if len(clean.split()) >= 4:
            if not _a_job_to_do(clean):
                return ""
            return clean if clean.endswith((".", "!", "?")) else clean + "."
    return ""


# An answer that declines to call it is not advice the person can go and do: "Not one I can call
# for you, sorry: I cannot examine anything from here" is the bot standing back, and handing it
# back as "that is the right first move" tells them to do nothing. Read from the answer's opening.
A_REFUSAL = re.compile(
    r"\b(?:i can(?:no|')?t\b|i cannot\b|beyond what i know|not one i can call|i don't know "
    r"enough|i would not want to guess|that is not something i can|not mine to decide|not mine "
    r"to say|not for me to (?:decide|say|call)|(?:that|this|it) is your call|up to you whether)\b",
    re.I)


def _an_ask_for_a_call(memory):
    """True when the person's own last line asked for a recommendation."""
    said = _flat(_last_person_line(memory)).strip()
    return bool(said) and ASKED_FOR_A_CALL.match(said) is not None


def _a_fix_with_no_warning(said):
    """True for an answer that gives a job to do and says nothing about danger either way."""
    if not said or len(said) < 80:
        return False
    if not _says_what_it_is(said):
        return False
    if _first(said, CARE) is not None or REFER.search(said) is not None:
        return False
    if _first(said, REASSURE) is not None or _first(said, STOP_DOING) is not None:
        return False
    return _a_how_to(said)


# The answer gave an instruction and nothing else: no verdict, no explanation of the thing, no
# referral. "my mate keeps cancelling on me" is answered "Say it once, about the pattern rather
# than the last time: ...", and "is that bad" on top of it came back "Alright then - good luck
# with it." - a goodbye to a fair question. So did "i got a parking ticket", "my landlord wants to
# raise the rent", "my ex keeps texting me" and "my mum keeps telling me what to do". Nothing in
# those answers can be ruled on and the pools above all need an answer that said something about
# the thing, so the doubt gets the one honest sentence there is - the doing in the answer is the
# point, not a verdict - and the question a friend asks. No line claims the thing is fine.
DIRECTED_LINES = (
    "I wouldn't call it a warning sign - the answer above is about getting it sorted, and that "
    "is the part that matters. What has you asking?",
    "Nothing in that says how serious it is. The step above is what moves it, and what would "
    "change the answer is it getting worse or going on. Where is the worry?",
    "Hard to put a scale on it. Doing the thing above is what makes the difference, so start "
    "there and tell me what is behind the question.",
)
# Somebody who owes the person something: a fault a landlord, a council or a boss has been asked
# to fix is not the ordinary job the fault itself is. "my landlord wont fix the damp" / "been 3
# months now" / "is that a problem" was told "On its own, no. Everything in that answer is the
# ordinary job", because the damp card ("find the water before you treat the wall") was read as
# the answer to the question asked; the question was about somebody's duty, and three months of it
# is a tenancy problem, not a damp-repair one. The reassurance is not this composer's to give, so
# it stands aside and says nothing rather than saying the wrong thing warmly.
# Standing aside is right for the verdict and wrong for the turn: the chat pool fills the hole
# with a goodbye ("Alright then - good luck with it."), which is worse than the reassurance it
# replaced. What the person is owed is not a verdict on the damp; it is the one thing that
# changes whose problem it is, which is having it in writing with the date it started.
OWED_LINES = (
    "Then it is theirs to fix rather than yours. Put it in writing, keep a copy, and note the "
    "date it started \u2014 that is the thing that turns it from your complaint into their job.",
    "That one is their job, and the date is what makes it stick. Send it in writing, keep the "
    "reply, and say when it started: anyone who has to step in later asks for that first.",
    "Keep it in writing and keep the dates. A landlord, a council or a boss who has been told in "
    "writing is a different conversation from one who has only been told.",
)
OWED = re.compile(r"\b(?:landlord|landlady|letting agent|estate agent|council|housing "
                  r"association|housing officer|boss|manager|employer|supervisor|neighbour|"
                  r"neighbor|builder|contractor|freeholder|owner|letting|lettings)\b", re.I)


def _somebody_owes_them(memory, back=3):
    """True when one of the last few lines named somebody who owes the person a duty."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    for last in turns[-back:]:
        if not isinstance(last, dict):
            continue
        line = last.get("user") or last.get("clean") or last.get("text") or ""
        if isinstance(line, str) and OWED.search(line):
            return True
    return False


def _a_reading_of_the_feeling(memory, flat):
    """The sentence for a doubt about a state the person named themselves, or None.

    Shared by both passes over the doubt: a chat line that named a feeling is answered with the
    reading for that family rather than with a question floor, and the pass after the answer
    finds the same family. The rotation is taken as it comes rather than handed to `pick`: `pick`
    seeds on the sum of the characters, and three of these pairs ("i feel low" / "is that bad",
    "i feel anxious all day" / "am i ok", "ive been feeling flat all week" / "is that weird")
    collided on one sentence. The count of turns is in the seed so the same ask twice in a row
    does not get the same sentence back.
    """
    behind = _the_line_behind(memory)
    family = _a_feeling_of_their_own(behind)
    if not family:
        return None
    seed = behind + " " + flat + " " + str(len(memory.get("turns") or []))
    return _round_robin(FEELING_DOUBT_LINES[family], seed)[0]


def _care_pool(said):
    """Which care pool a normality ask gets, by what the answer already said.

    Three readings of one answer, in the order they can be true: a card that put a time on its
    referral has already answered the doubt ("ring the vet today" is not a thing to wonder about),
    so the reply says to do it. A card that said how many people it happens to has answered
    "is it normal" itself, so the reply must not say it cannot tell. Only a card silent on both
    gets the honest "I could not call that usual or not from here".
    """
    flat = _flat(said)
    if CARE_NOW.search(flat) is not None:
        return CARE_NOW_NORMAL
    if _first_positive(flat, SAYS_NORMAL) is not None:
        # The answer has already said the thing asked about is the usual one: "The steady hum is
        # the compressor ... it is normal, and it gets louder when the room is warm". A care line
        # on top of that ("common or not, that one is worth getting looked at properly") sends a
        # person to an engineer for the ordinary hum, which is the one mistake these pools must
        # not make - it is the same reading as the `no` this pool was written to stop arguing
        # with, only louder (ample-fan, #3872). The answer's own word is the verdict, and the
        # pools that watch for change carry whatever exception its later sentences named.
        return ORDINARY_NORMAL
    if _first_positive(flat, HOW_MANY_PEOPLE) is not None:
        # The card has said how usual it is, so the one line that cannot argue with it is the one
        # that takes the commonness as the card's word: "Yes - common or not, that one is worth
        # getting looked at properly".
        return CARE_NORMAL[:1]
    if _first_positive(flat, REASSURE) is not None:
        # The card said what usually causes it ("usually means a ligament is not holding") and
        # sent them to someone: it has said enough that the honest "I could not call that usual
        # or not from here" would be arguing with it.
        return CARE_NORMAL
    return CARE_NORMAL + CARE_NORMAL_UNKNOWABLE


def _the_knowledge_has_this(clean, memory, above):
    """The knowledge base's own new answer to this line, or None.

    Read the way `safetyask` reads it: on a copy of the memory, so asking changes nothing about
    this turn. A card that cannot be read is no card.

    A card that only says the answer above again is not a new answer either, and asking the
    knowledge base does not tell the two apart: for "will that help" after the back-pain card it
    hands back that card, sometimes with the nod ("Same as before: ...") and sometimes without.
    So the test is the words - the answer above's own opening, said again - and not the nod in
    front of them. The person asking whether the method works has read that paragraph.
    """
    try:
        from .safetyask import _the_answers_have_this
    except Exception:  # noqa: BLE001 - a card that cannot be read is no card
        return None
    card = _the_answers_have_this(clean, memory)
    if not card:
        return None
    said = _flat(card)
    opening = _flat(above)[:60]
    if opening and opening in said:
        return None
    return card


def a_check_on_the_reply(reply):
    """True when a reply is this composer's answer to a check on the answer above, else False.

    Read by the arbiter: a check on the method just given is not answered by saying that method
    again, so the recall band - which repeats the paragraph - gives way to this line. The pools
    are the whole reading, because the same check is asked in many wordings.
    """
    if not reply:
        return False
    text = reply.strip()
    return any(text in {line.strip() for line in pool}
               for pool in (CHECK_WORKS_LINES, CHECK_ONCE_LINES, CHECK_WATCH_LINES,
                            CHECK_JOB_LINES))


def _an_amount_asked(flat):
    """Whether the check is about how much of a thing, which is the one kind a card can answer."""
    return bool(ENOUGH_ASK.match(flat) or re.search(r"\bhow (?:much|many)\b|\bamount\b|"
                                                    r"\benough\b", flat or ""))


def _the_last_thing_said_is_a_nod(memory):
    """Whether the bot's last turn only said the person was heard."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1]
    return isinstance(last, dict) and _a_punt(last)


def _a_check_on_the_method(flat, memory):
    """"Will that work" / "will that help" / "is that enough" about the answer above, or None.

    Only an answer that is a method is what the check is about: the person is asking whether the
    thing the bot just told them to do does anything. A check on a choice the bot has no view on
    ("we are thinking about a second baby" / "will that work") keeps the line it has today - the
    answer above asked the person a question back, and no pool here can say the question works.
    """
    said = _last_reply(memory, past_the_nod=True)
    if not said or not _a_how_to(said):
        return None
    # A choice the answer put back to the person ("we're thinking about getting a rescue dog" /
    # "would that work") is not a method, whatever verbs the answer happens to use: the dog
    # answer's "get one" is the end of a test, not a step. The bot has no view on the choice, so
    # the check keeps the line it has today.
    behind = _flat(_last_person_line(memory) or "")
    if A_THINKING_ABOUT.search(behind) or A_DECISION_ASK.search(behind):
        return None
    # A plan of the person's own is not a method the bot gave, so a check on it is theirs to
    # weigh: "im going to quit my job" / "will that work" is not a doubt about advice.
    if A_PLAN.search(behind):
        return None
    # And the answer has to be the knowledge base's own method. "budget is about 30 quid" is
    # answered by the store's echo of it, and "do you think that is enough" over that echo wants
    # the sum done, not "that is the standard way": a check on an echo is a question this file
    # cannot see the subject of, so it keeps the line it has.
    if _last_module(memory) != "answers":
        return None
    if _the_last_thing_said_is_a_nod(memory):
        # A nod in between ("Got it - you're paying 60 a month") means the answer above is not the
        # last thing said, and the line the person is checking is whatever the bot is about to say
        # about their own figure, which this file cannot see: "i owe about 4000 on my credit card"
        # / "im paying 60 a month" / "is that enough" has the money line to come, and a check on
        # the card above the nod took it away.
        return None
    # A check the knowledge base answers itself is not a check on the method above: "he will eat
    # them raw though" / "is that enough" has the five-a-day card, and that card is a better
    # answer than anything this file can say about the answer before it (qptf-02 on the deck).
    # Read before the pools, and after the echo test, so a card that only repeats the answer
    # above leaves the turn here.
    if _an_amount_asked(flat) and _the_knowledge_has_this(flat, memory, said):
        # Only an amount check can be answered by a card. "is that enough" has the five-a-day card
        # behind it, and that card is the answer; "would that be worth it" over the descaling card
        # has a kettle-buying card behind it, which is about something else, so the check keeps
        # the turn.
        return None
    # A remedy pool only reads as an answer when there is a body in the question: "most people do
    # well on it" and "if it is no better in a week or two" say nothing about a price, a form, a
    # wait or a quote, and those three lines are what a check on a job used to get (snappy-net,
    # #8488). The line the person typed counts as well as the answer, because the answer to "my
    # back hurts" speaks about the habit and the line names the back.
    if not _about_a_body(behind):
        pool = CHECK_JOB_LINES
    else:
        warns = (REFER.search(said) is not None or NAMES_A_CLINICIAN.search(said) is not None
                 or _first(said.split(), STOP_DOING) is not None)
        if warns:
            pool = CHECK_WATCH_LINES
        elif A_LENGTH_IN_THE_ANSWER.search(_flat(said)):
            pool = CHECK_WORKS_LINES
        else:
            pool = CHECK_ONCE_LINES
    return pick(_round_robin(pool, flat + " " + said), memory, said)


# The doubts that are about the thing itself rather than about what to do next. A ruling is only
# said again for one of these: "my pan caught fire" / "what now" is the next thing to do, not a
# doubt about the pan, and answering it with "the answer above still stands: it stays off" takes
# the one reply that mattered - "Stay out and ring 999" - off a fire that is still burning.
A_DOUBT_ABOUT_THE_THING = re.compile(
    r"\b(?:safe|safely|unsafe|dangerous|danger|ok|okay|fine|risky|risk|bad|wrong|worried|"
    r"worry|worrying|problem|normal|harm|harmful)\b"
    r"|\b(?:can|could|may|should) i (?:still |even )?(?:use|keep using|leave|carry on using)\b")


def reply_for(clean, memory):
    """The answer to a bare "is that bad / what should i do / should i see someone"."""
    flat = _flat(clean).strip(" .!?")
    # A check on the person's own plan, read before anything else: it is their plan, so there is
    # no verdict here to give, and the pools below would give one anyway - on a dog and a working
    # day, "is that fair" was answered "Sounds good." and, once the words were added to the bare
    # doubts, "Nothing in that sounded like a warning sign". The plan can be one line further
    # back than the line being checked (`_the_plan_they_brought`), which is the ordinary shape of
    # a plan being talked through, and only a line that says nothing else is read here: a check
    # with a subject of its own ("is that fair on my mum") is a question about that.
    # The answer above ruled the thing unsafe - it said to unplug it, switch it off at the wall,
    # stop using it, or call 999. A bare doubt after that is about the ruling, and the verdict
    # pools below cannot give it: "the plug on the kettle is scorched" is answered "Unplug it if
    # you can do it without touching anything hot...", and "is it safe" came back "Ordinary on its
    # own, yes. It stops being ordinary if there are flames or smoke in the room" - an all-clear
    # for a scorched plug, in the same breath as the answer that said not to touch it. The
    # ruling is read from the same place the safety reading reads it, so the two cannot disagree
    # about whether the bot has already said stop.
    from . import safetyask

    if (safetyask.the_bot_already_ruled(memory) and A_DOUBT_ABOUT_THE_THING.search(flat)
            and not any(word in flat for word in safetyask.A_RULING_ALREADY)):
        # A line that names the stopping itself ("should i unplug it") asks about that step, and
        # the card that names the thing answers it better than the ruling said again. The line
        # here is the bare doubt about the thing - "is it safe", "is that dangerous".
        return pick(safetyask.A_SAFETY_ALREADY_RULED, memory, flat)
    if A_CHECK_ON_A_PLAN.match(flat):
        plan = _the_plan_they_brought(memory)
        if plan:
            # The ask is which part is being weighed, and nothing is ruled on: `_a_plan_doubt`
            # answers the same line with "that is yours to decide rather than something to worry
            # about", which is right for a dog or a wedding and wrong for "i want to lie on my cv"
            # / "does that sound sensible" - there the bot would be blessing a lie by calling it
            # the person's to weigh. Asking what the doubt is works for both.
            return pick(_round_robin(A_CHECK_ON_A_PLAN_LINES, plan), memory, plan)
    # A doubt about the step just given, read before the bare doubts are read: "will that work"
    # is about the method in the answer above, and that method is the bot's own, so the honest
    # reply is the one a method gets - it is the way the bot would do it. An answer that sends
    # them to a clinician, or names a danger, stands aside: there the doubt is about the warning.
    if METHOD_DOUBT.match(flat):
        behind = _last_reply(memory, past_the_nod=True)
        # A plan or a choice in the line before is the person's own, so a doubt on it is theirs
        # to weigh: "im going to quit my job" then "will that work" is not a doubt about a method
        # the bot gave, and the method pool would be agreeing with a decision that is not ours.
        line = _the_line_behind(memory)
        written, spoken = _as_written(line)
        # The same gate "is that ok" after a how-to goes through: the ask has to be a how-to, and
        # the answer has to give the doing. A doubt on a suggestion ("what shall i get my mum")
        # or on a plan ("im going to quit my job") is the person's own to weigh, and a doubt on
        # a thing that got damaged ("my laptop got soaked in the rain") is about the thing.
        if (not behind or not _a_how_to(behind)
                or not (A_HOW_TO_ASK.search(line) or A_HOW_TO_ASK.search(written)
                        or A_HOW_TO_ASK.search(spoken))):
            # The other way round: the answer above is a method the knowledge base gave, and the
            # person is asking whether it does anything ("my back hurts" / "will that help").
            # Returning None handed it to the acknowledgement floor, which closed the
            # conversation with "Alright then - good luck with it."
            return _a_check_on_the_method(flat, memory)
        if _danger(behind) is not None:
            return None
        if REFER.search(behind) is not None or NAMES_A_CLINICIAN.search(behind) is not None:
            # The answer above sends them to a clinician ("see a GP if they keep coming back"),
            # and the doubt is about the warning rather than about the doing of it, so the method
            # pool ("that is the method I would use") must not answer it - that is the bug the
            # guard stands for. The check pool is a different reading, though: it exists to say
            # what to watch for, and a how-to with "see a GP" in it is exactly the answer a check
            # on a method was written for. So the check is read here, and only a check that reads
            # nothing (not a how-to, not the answers module's own method) stands aside as before.
            return _a_check_on_the_method(flat, memory)
        # A check on the effect ("will that help") is not the question the method pool was
        # written for ("is that ok"): "Done that way, it needs no one else: that is the method I
        # would use" says the method is the right one and never says whether it does anything,
        # which is what was asked. The check pool answers that, and picks its line by whether
        # the answer above named anything to watch for.
        checked = _a_check_on_the_method(flat, memory)
        if checked:
            return checked
        return pick(_round_robin(METHOD_OK_LINES, behind), memory, behind)
    # Whether a price is a lot, read before the bare doubts: the ask is about the figure in the
    # person's own line, and it is the one doubt that must not fall through to the body readings
    # (a figure is not a condition) or to the chat floor ("Sounds good." to a price question).
    if A_FIGURE_ASK.match(flat):
        figure_line = _the_line_behind(memory)
        figure_said = _last_reply(memory, past_the_nod=True)
        if figure_line and _a_figure_owed(figure_line) and figure_said:
            # Only a word that makes a comparison ("usual", "typical", "the going rate") is the
            # answer's own usual figure. A yearly total is a figure too, and handing that back as
            # "the answer above gives the usual one" would be the bot making one up.
            if _first(figure_said, A_COMPARISON) is not None:
                return pick(MONEY_LINES, memory, figure_said)
            if A_FIGURE.search(figure_said):
                return pick(FIGURE_LINES, memory, figure_said)
        return None
    # "is that enough" is not one of the doubts below - it asks about an amount, not about how bad
    # something is - so it matched nothing here and the acknowledgement floor took it. After "Three
    # half-hour sessions a week is enough to feel different in a month" the answer had already
    # said so, and the person asking was checking the amount: `is that enough` was answered
    # "Alright then - good luck with it." The ask is read on its own, and the answer's own
    # quantity sentence is what it is answered with.
    enough_ask = bool(ENOUGH_ASK.match(flat))
    if not BARE.match(flat) and not enough_ask:
        # A check on the method just given ("will that work") said in words the pattern above does
        # not hold ("do you think that is enough", "would that sort it") is still not a doubt
        # about the thing, and every pool below answers what is wrong with the thing. Read here
        # and go no further.
        if A_CHECK_ASK.search(flat):
            return _a_check_on_the_method(flat, memory)
        return None
    normal_ask = bool(ASKS_NORMAL.search(flat))
    ok_ask = not normal_ask and bool(ASKS_OK.search(flat))
    said = _last_reply(memory, past_the_nod=True)
    # A check on a plan that can hurt is the one doubt this file does have something to say
    # about: the plan is still theirs, but the answer cannot be "yes, it is fine". Read before
    # any of the pools below, because several of them read a plan as a thing to be weighed and
    # say so.
    plan = _the_line_behind(memory)
    family = _the_plan_can_hurt(_flat(plan))
    if family:
        warned = _the_answer_already_warned(_flat(said))
        if warned:
            return "Go with the answer above rather than around it: " + warned
        return pick(_round_robin(THE_PLAN_CAN_HURT_LINES[family], _flat(plan)), memory,
                    _flat(plan))
    # A death is not a subject this file can rule on, and the pools below would ask after it like
    # a symptom. Standing aside is not enough either: the chat pool fills the hole with "Alright
    # then - good luck with it", so the floor stays with the person instead.
    # Only over a readable line: a safety, urgent, loss or grief reply keeps its own path, and
    # `_last_module` answers "" for those.
    if _about_a_death(memory) and _last_module(memory):
        return pick(_round_robin(GRIEF_FLOOR_LINES, _the_line_it_answered(said, memory) or flat),
                    memory, flat)
    if enough_ask:
        # Read before every pool below: they all judge how bad a thing is, and an amount is not a
        # fault. Nothing to hand back means standing aside, so a "is that enough" over an answer
        # that never gave an amount keeps whatever it had.
        stated = _said_enough(said)
        if stated is None:
            # Nothing in the answer to hand back as an amount, so this is a check on the method
            # like the others: "my back hurts" / "is that enough" has the back-pain card and no
            # amount in it, and standing aside here left the acknowledgement floor to close the
            # conversation ("Alright then - good luck with it").
            # Only when the answer above is the last thing said: "i owe about 4000 on my credit
            # card" / "im paying 60 a month" / "is that enough" has the store's nod in between
            # ("Got it - you're paying 60 a month"), and the line to read is the money one the
            # greeting module is about to give, not the card above the nod.
            if _last_module(memory) == "answers":
                checked = _a_check_on_the_method(flat, memory)
                if checked:
                    return checked
            return None
        return pick(_round_robin(ENOUGH_STATED_LINES, said + " " + flat), memory,
                    said).replace("{yes}", stated)
    # A plan, a choice or a wish the person brought is theirs, and a bare doubt about it is them
    # checking that wanting it is allowed: "im going to rome" / "is that ok" was answered "Alright
    # A stand-down is not a hand-over: the answer in front is the person's own plan being
    # got, so there is nothing here to rule on and nothing below will claim it either -
    # returning nothing left the turn to the sign-off pool ("Alright then - good luck
    # with it"), which ends a conversation the person is still in.
    # A going named in the person's own line is the same shape: "we are going to skegness in
    # june" / "is that ok". The store has no card for a town, so the line comes back as an echo
    # and nothing above it is an answer to read the doubt against - the plan is still theirs and
    # the ask is still about it.
    if _considering(memory) or A_PLAN.search(_flat(_the_line_behind(memory))):
        return _a_plan_doubt(memory)
    # The worst thing said, read beside the answer above: a death or a diagnosis is not a fault,
    # so a doubt on top of one is about the person rather than about the answer, and it is read
    # the same whichever module answered it. "my dad has cancer" / "is that bad" got the
    # acknowledgement floor's "Alright then - good luck with it."
    #
    # Both halves are needed. The news is the person's own line, and the answer above has to be
    # an answer that heard it: "my phone keeps dying" and "my basil keeps dying" are how-to
    # answers, and neither of them says sorry, so the doubt about them is not a bereavement.
    worst = _the_worst_thing_they_said(memory)
    if worst and SYMPATHY.search(_flat(said)):
        # Seeded on what they brought: "is that bad" is the same seven words every time, so a
        # father's cancer, a husband's terminal cancer and a miscarriage all got one sentence.
        seed = worst + " " + flat + " " + str(len(memory.get("turns") or []))
        return _round_robin(HARD_NEWS_LINES, seed)[0]
    # A doubt over money is answered about money, and read before the answer above is read for a
    # symptom. "i cant afford to heat the house" / "is that bad" was told "That one is the ordinary
    # kind, so no. Watch it rather than worry about it: if it's still the same in a week or two ..."
    # - the sentence a cough gets, over a month that does not add up. The rent, a card, a fine and
    # a bill were all told that their thing was "to watch", which is the one thing money is not.
    # A safety answer, a death and a diagnosis all keep their own paths above this.
    money = _a_doubt_about_money(memory)
    if money and _last_module(memory, past_the_nod=True) in ("answers", "chat", "greeting",
                                                             "trouble"):
        # A figure the person gave, against the usual one the answer gave, is the comparison
        # below rather than this pool: "i owe 300 on my gas bill" / "is that bad" wants its own
        # number put beside the usual one, and the pool that names the date is for the trouble
        # that has no figure in it at all. The figure has to be a number: "the rent is late and i
        # am scared" names no amount either, and it was told "That is a figure to compare" too.
        # A digit of any shape counts, because "i owe 300 on my gas bill" is a figure with no
        # currency sign and no period beside it, which `A_FIGURE` does not catch.
        if (not _about_a_death(memory) and not _the_worst_thing_they_said(memory)
                and not (_A_NUMBER.search(money) and _is_a_comparison(said))):
            return pick(_round_robin(MONEY_TROUBLE_LINES, said or money), memory, said or money)
    # A mood or a money worry is not a body and not a fault: "i feel low" then "is that bad"
    # was told its mood was "the ordinary kind, so no", because a warm chat line was read as if
    # it were a symptom answer. The doubt path reads the knowledge base only.
    if not said or _last_module(memory, past_the_nod=True) != "answers":
        # A state the person named themselves is answered by the reading for that family, and
        # only after a chat or floor answer: after a safety answer the crisis reply is the one
        # that stands, and a body in the line is a symptom.
        reading = _a_reading_of_the_feeling(memory, flat)
        if reading:
            return reading
        # A safety answer is not read back for a step ("do the first thing I said" after "ring
        # 999" is the wrong sentence), but the verdict question about it is a different ask and
        # it has one answer: yes. Only when the answer named somebody to ring - a line that named
        # nobody has no call to point back at.
        # "i tried that and it helped" / "is that bad" is the report of a thing working, and the
        # floor read it as a symptom ("That is worth a proper look rather than a shrug").
        if HELPED.search(_flat(_last_person_line(memory))):
            return pick(_round_robin(HELPED_LINES, _flat(_last_person_line(memory))), memory,
                        _flat(_last_person_line(memory)))
        named = _last_line_that_named_a_call(memory)
        if named:
            if _a_call_for_now(named):
                # How urgent the call is, from the line's own words. A dentist, an optician or a
                # physio is somebody to see, not somebody to ring tonight, and the pools say so.
                # How urgent, from the sentence that carries the call rather than from the whole
                # answer. "a bent limb, bone through the skin or numb fingers is 999, otherwise
                # get it checked at A&E or a minor injuries unit today" is a call for today with
                # a fence around the 999; a burn answer that opens "twenty minutes under cool
                # running water ... starting straight away" is urgent about the water and names
                # nobody. Reading the whole answer for an urgent word put both of those in the
                # same pool as "ring 999 straight away".
                call = _the_call_sentence(named)
                seed = flat + " " + call
                if call and URGENT_CALL.search(call):
                    # Rotated on the answer, because "is that bad" is the same seven words every
                    # time and `pick` seeds on the sum of the characters: four different calls
                    # for today landed on one sentence word for word.
                    return pick(_round_robin(YES_SAID_LINES, call), memory, seed)
                if TRADE.search(named) is None:
                    # No time and nobody named: "a burn that blisters or is on the face, hands or
                    # joints should be seen" is a yes, and the pool that says the answer named who
                    # cannot be used over it.
                    return pick(YES_LINES[:2], memory, flat)
                return pick(SOON_LINES, memory, flat)
            # A call the line itself fenced is the condition to watch, not an order for today:
            # "see someone if it's not shifting in a few days" over "i feel dizzy" / "is that
            # bad" was "ringing is not an overreaction here, it is the whole point of it". The
            # answer already named the line to act on, so the verdict is the answer's own.
            when = _when(named)
            if when:
                return pick(CONDITION_LINES, memory, flat).replace("{when}", when)
        # "should i be worried" is the health hedge's ask, not a verdict about the bot's last
        # line: on the deck `i get out of breath singing` / `Got it. Is there anything you'd like
        # a hand with?` / `should i be worried` has the hedge's "a GP, a pharmacist or 111 will
        # tell you" on main, and the floor took that turn away from it.
        if WORRIED_ASK.match(flat):
            return None
        # A chat line, not an answer: there is nothing to read a verdict out of, and "good luck
        # with it" is what the person used to get. Two cases, because a floor may ask but it may
        # not rule: a warm line that said nothing ("I'm listening - say more if it helps") gets
        # the question and no verdict - "i have blood in my poo" was told "I wouldn't call it bad"
        # over exactly that line - while a line that already gave the practical thing ("Rest, warm
        # drinks and an early night") is an answer in substance, and the ruling rests on it.
        if _last_module(memory) in ("chat", "greeting", "trouble"):
            # A state the person named themselves is not a chat-line floor: the reading for
            # that family answers it, and every arm here would take the turn away from it
            # ("i feel really low" / "am i ok" got the question floor's "What would you like to
            # do about it, and how long has it been like that?" over the flat-stretch reading,
            # because the chat line happened to mention a walk).
            reading = _a_reading_of_the_feeling(memory, flat)
            if reading:
                return reading
            if _own_doing(memory) and _a_mood(memory):
                return pick(_round_robin(BACKSTOP_LINES, said), memory, said)
            # The step the bot recommended, doubted. Read first, because every arm below is about
            # what the person has or does and a recommendation is neither.
            step = _the_advice_itself(said)
            if step and _an_ask_for_a_call(memory) and not A_REFUSAL.search(said):
                return pick(_round_robin(ADVICE_OK_LINES, said), memory, said).replace(
                    "{step}", step)
            if _own_doing(memory) and _a_fix_with_no_warning(said):
                return pick(_round_robin(NOTHING_WARNED_LINES, said), memory, said)
            # The question floor claims nothing, so unlike the ruling pools it does not need the
            # line to be about something the person does. What they have is a fair thing to ask
            # about: "i have a cough" / "is that bad" was answered "Alright then - good luck with
            # it" over "Take it easy today - honey and lemon, and don't push through it", and
            # "i have blood in my poo" got the same shrug. What they have can also be cheerful,
            # so that floor asks without calling anything serious.
            # ...and a floor that asks how long it has been going on is for a condition, not for
            # news that went well: "i got the job" is not a thing that has been going on.
            if _own_doing(memory) and not _nothing_to_be_long_about(memory):
                return pick(_round_robin(FLOOR_LINES, said), memory, said)
            if _about_the_person(memory) and not _nothing_to_be_long_about(memory):
                return pick(_round_robin(NEUTRAL_ASK_LINES, said), memory, said)
            # A floor that turned the question back on the person - "That would get to me too. Do
            # you want to work out what to say to them, or is it more a case of letting off
            # steam?" - is a friend mid-conversation, and the doubt that comes back on top of it
            # was answered "Alright then - good luck with it." There is still nothing here to
            # rule on, so the reply says that plainly and asks for the half that decides it,
            # rather than saying goodbye to a worry.
            if _the_floor_asked_them_something(memory):
                return pick(_round_robin(ASKED_THEM_LINES, said + " " + flat), memory,
                            said + " " + flat)
        # #8025's reading, one line down: a doubt after a reply that only gave an instruction.
        return _a_plan_doubt(memory)
    # "when should i worry" asks for the condition, so the answer is the card's own condition and
    # not a yes/no verdict on the thing: over "my mum keeps forgetting things" the pools below
    # said "Yes, that one wants a proper look rather than watching it", which answers a question
    # nobody asked. Only with a readable condition in hand; otherwise the ask keeps the reading
    # it has always had.
    if WHEN_ASK.match(flat) or WORRYING_ASK.match(flat):
        when = (_when(said) or _the_list_before_the_call(said)
                or _stated_referral(said)[0])
        if when:
            return pick(WHEN_LINES, memory, flat).replace("{when}", when)
        # The answer wrote its call first and its reason after the "for", which is not a fence
        # any reader above looks for: over a cut and a cough that left the person with the search
        # hedge or a flat "yes, that one wants a proper look".
        call = _the_call_and_its_reason(said)
        if call and _they_named_the_sign_themselves(call, memory):
            # They are already at the sign, so quoting it back with "before that" is worse than
            # the reading below, which is what these lines got before this change.
            call = ""
        if call:
            return pick(WHEN_CALL_LINES, memory, flat).replace("{when}", call)
        if WORRYING_ASK.match(flat):
            return None
    # The line before was this composer's own verdict, so the person asking again gets the same
    # answer said plainly rather than a new verdict. It used to fall through to the "a fix with no
    # warning" reading, which saw the advice-in-its-own-words in "watch for that" and answered it
    # afresh.
    # It has to be this composer's line before the words are worth reading: `{Step} first.` is one
    # of the templates, and any answer that ends in that word fits it, so a card that says
    # "chemical drain cleaner is the last resort, not the first" was taken for a verdict of mine
    # and the reply to "is that serious" was "Still no." - a no the bot never said. The module is
    # the fence, and the text only decides which of my lines it was.
    if _the_last_line_was_mine(memory) and OWN_PATTERN.search(_flat(said)):
        return pick(AGAIN, memory, flat)
    if any(line.lower() in _flat(said) for line in
           NO_LINES + DO_LINES + YES_LINES + ORDINARY_NORMAL + CARE_NORMAL
           + CARE_NORMAL_UNKNOWABLE + CARE_NOW_NORMAL + DO_NORMAL):
        return pick(AGAIN, memory, flat)
    if _first(said, AGAIN) is not None:
        return None
    # A person's week is not a body (see A_PERSON_THEY_KNOW). Read before the pools below, which
    # would offer somebody's mother a doctor's look for her week.
    if _a_person_they_know(memory, said):
        if _when(said) or REFER.search(said) is not None:
            return pick(PERSON_CALL, memory, flat + " " + _the_line_behind(memory))
        return pick(PERSON_ORDINARY, memory, flat + " " + _the_line_behind(memory))
    opening = _opening(said)
    # What the answer above was about decides which words a verdict may use: a machine gets the
    # job and the trade, and only a body gets a week of watching and a proper look (see
    # A_THING_THEY_OWN). The yes-pool for a call is the same reading in the thing's words.
    thing = _a_thing_they_own(memory)
    yes_pool = THING_CALL if thing else YES_LINES
    # An answer that opens by telling them to get rid of the thing has already said how bad it
    # is, and a bare doubt on top of it is the person asking to be talked round. Read before the
    # care words: "bin it" and "isn't safe to eat" are not a job with a fix, and the pools below
    # would hand back a DIY reading of them.
    action, tested = _a_throw_away(opening)
    if action is not None:
        # Seeded on the answer: "is that bad" is the same seven words every time, so the
        # bare ask gives the chicken, the rice and the milk one identical sentence.
        # A test the person has already run is not the answer: "my milk has gone sour" said the
        # sign the rule names, so it wants the action, while "how do i know if the milk is off"
        # is the row that wants the test back.
        pool = TEST_LINES if tested and not _the_person_gave_the_sign(memory, clean) else THROW_AWAY_LINES
        # Seeded on the answer, so "is that bad" - the same seven words every time - does not
        # give the chicken, the rice and the milk one identical sentence; the person's own line
        # keeps the two chats that share one knowledge answer from matching word for word.
        return pick(pool, memory, opening + " " + _the_person_line(memory, clean)).replace("{Action}", action)
    # An answer can give the verdict in its own words and nothing else: "There is no safe number of
    # drinks before driving" is a no, and there is no referral, job, danger word or ordinary word in
    # it for the readings below to find. So "im gonna drive home after a few pints" / "is that ok"
    # fell through every arm and the acknowledgement floor took the turn with "Alright then - good
    # luck with it." over a straight no. Read before the care words, because an answer can hold a no
    # and a referral together and the no is what the person asked about.
    no_stated = _said_no(said)
    if no_stated is not None:
        return pick(_round_robin(NO_STATED_LINES, said + " " + flat), memory,
                    said).replace("{no}", no_stated)
    care = _referral(said)
    ordinary = _first_positive(opening, REASSURE)
    # A long answer puts its referral in its last sentence: the knee answer spends its opening on
    # what a giving-way knee "usually" means and ends "Ring your GP or a physio this week", and
    # reading the opening alone answered "is that bad" with "that one is the ordinary kind, so
    # no". A referral with no "if" in front of it is the answer's own judgement wherever it sits.
    anywhere = care
    # An answer that tells the person to stop doing the thing is not the answer this composer may
    # call ordinary: "grinding means the pads are down to metal: stop driving" must not come back
    # as "that one is the ordinary kind, so no", however much "usually" a later sentence about
    # the price carries. The stop is read from anywhere in the answer, so the order of the two
    # sentences cannot decide it.
    if _first(opening, STOP_DOING) is not None:
        return pick(_care_pool(said) if normal_ask else (THING_CALL if thing else YES_LINES[:2]),
                    memory, flat)
    # A condition the answer wrote out is the answer's warning for later, not its verdict now,
    # so a harm word inside that condition is not a reason to answer "yes, get it seen to":
    # "Shaking that has crept on over months, is much worse on one side ... is worth a GP
    # appointment" is handed back as that condition, not as a bare yes. The condition is read
    # first and the danger step stands aside for it; an answer with no condition in it keeps the
    # reading it has always had.
    when = _when(said)
    if when == "" and _danger(said) is not None:
        return pick(_care_pool(said) if normal_ask else (THING_CALL if thing else YES_LINES[:2]),
                    memory, flat)
    # The line that was answered decides what "is that ok" is about, and a method, a choice or a
    # plan is not the thing that is wrong. Read as a fault, "how do i cook rice" then "is that
    # ok" was told "Everything in that answer is the ordinary job", and "im going to rome" then
    # "is that ok" was told the same. A method has an answer this composer knows - it is the
    # bot's own, in the answer above - and a choice or a plan has none of this composer's to
    # give, so those go back to the warm acknowledgement.
    # People type the way they type. "wat shud i cook 2nite" is "what should i cook tonight", and a
    # reader that matches on the words as typed reads a question about a choice as no question at
    # all - the `A_PLAN` / `A_DECISION_ASK` arm never fires, and "is it ok?" was answered "That
    # answer is the fix rather than a verdict on how bad it is", which reads the previous answer as
    # a problem already handled. `_as_written` puts each word right in place, in the same order and
    # with the same punctuation, so the ask is still the person's own sentence.
    line = _the_line_behind(memory)
    written, spoken = _as_written(line)
    # Only an answer with nothing to watch in it is the bot's own method. "How do i know if my
    # ankle is broken" is a how-to, and its answer is a check with a red flag in it ("if you
    # cannot [walk on it], or it is crooked, go to a minor injuries unit or a&e today"), so
    # "is that bad" is a question about the red flag and not about the method: told "nothing in
    # it to worry about" it read as an all-clear over an answer that names a&e. So an answer that
    # sends them somewhere to have the thing looked at, or tells them to stop doing it, is read
    # by the verdict below instead, exactly as it was before this branch existed.
    warns = (REFER.search(said) is not None or NAMES_A_CLINICIAN.search(said) is not None
             or _first(opening, STOP_DOING) is not None)
    # The method came from the bot rather than from a how-to they asked: they stated a fact
    # ("i only have one oven", "my oven is fan only") and the answer above came back as the
    # method with the yes already on the front of it. A bare "is that ok" there is the person
    # checking the method, so it gets the same reading as the how-to above.
    if SAID_YES.search(_flat(said)) and _a_how_to(said) and not warns:
        return pick(_round_robin(METHOD_OK_LINES, said), memory, said)
    if ((A_HOW_TO_ASK.search(line) or A_HOW_TO_ASK.search(written)
         or A_HOW_TO_ASK.search(spoken))
            and _a_how_to(said) and not warns):
        # Seeded on the answer for the same reason the nothing-warned pool is: "is that ok" is
        # the same three words every time, so seeding on it gave the rice, the stain and the
        # radiator one identical sentence.
        return pick(_round_robin(METHOD_OK_LINES, said), memory, said)
    if A_PLAN.search(line) or A_PLAN.search(written) or A_PLAN.search(spoken):
        # The plan is theirs, so there is no verdict to give - but a sign-off is worse than
        # a question. Two of the four plans the deck holds reached the choice branch below
        # and were told their choice was a good call, which is the same overreach from the
        # other side; this arm is only the plan that has nothing below it.
        return _a_plan_doubt(memory)
    if (A_DECISION_ASK.search(line) or A_DECISION_ASK.search(written)
            or A_DECISION_ASK.search(spoken)):
        # The ask decides which way this goes. "is that ok?" after a choice asks whether the choice
        # is fine, and the answer's own suggestion makes that the composer's to give. "is that
        # bad?" asks about the thing chosen instead, and this composer has nothing to rule on for
        # it, so it stands aside as it always has.
        if ASKS_FINE.search(flat) and not ASKS_WRONG.search(flat):
            # A choice the answer made for them is the answer's own, so the honest verdict on it
            # is that it is a good call - returning nothing here left the turn to the sign-off
            # floor. Seeded on the line that was answered as well as the ask, so three different
            # choices do not all get one sentence.
            return pick(_round_robin(CHOICE_OK_LINES, line + " " + said), memory,
                        line + " " + said)
        # "should i" is also how a person asks about one thing rather than a choice: "should i get
        # my mole checked" / "is that bad" was read as a choice, and the choice arm has nothing
        # to rule on, so the doubt was handed back "Alright then — good luck with it" - over an
        # answer that had said "Get it checked by a GP within two weeks".
        #
        # Only an answer whose first sentence sends them to somebody has ruled on this for the
        # choice arm to stand aside for: there the referral is the whole answer, so the doubt
        # about it is answered by the referral itself ("Get it checked by a GP within two weeks",
        # "Ring 111 or your GP today", "Your health visitor or the 111 line will talk it
        # through"). An answer that opens with a fix and names a call later has fenced it ("most
        # coughs settle in two to three weeks ... a reason to ring the surgery"), and its own
        # condition is the verdict - the choice arm keeps standing aside rather than turning that
        # fence into "yes, get it seen to" for a chesty cough.
        opening = _opening(said)
        first_said = re.split(r"(?<=[.!?]) ", str(said or "").strip())[0]
        if (not warns or (_referral(first_said) is None
                          and NAMES_A_CLINICIAN.search(first_said) is None
                          and REFER.search(first_said) is None)):
            # Standing aside is right about the choice - the fence is not a "yes" - but the doubt
            # still has an answer here, and it is the answer's own condition. Nothing below this
            # point reads the fence, so the whole file stood aside over "i have a chesty cough that
            # wont shift" / "what should i do first" / "is that bad" and the chat floor gave the
            # cough "Sounds good."
            fenced = _condition_after_care(said, _first(str(said or "").lower(), CARE))
            if fenced:
                return pick(CONDITION_NORMAL if normal_ask else CONDITION_LINES,
                            memory, flat).replace("{when}", fenced)
            stated, kind = _stated_referral(said)
            # The same condition said as a thing rather than after an "if" ("Blood in it,
            # breathlessness or three weeks of it is a reason to ring the surgery or 111"), which
            # `_condition_after_care` cannot read. The three guards are the ones that keep an
            # answer's own "go" a go: a time in the sentence ("Ring the vet today if ..."), a
            # rider before the condition ("sooner if he is also off his food"), and a person who
            # has already had it longer than the answer's own threshold. A person whose own line
            # is the condition is asking about the condition itself, and the answer's yes stands.
            sentence = _the_referral_sentence(said)
            if (stated and kind == "noun" and not TIME_NOW.search(sentence)
                    and not COMPARATIVE.search(sentence)
                    and not _the_line_is_the_threshold(
                        stated, _the_line_it_answered(said, memory))):
                # The person already at the threshold is not told "not yet": "i have had a cough
                # for months" / what to do first / "is that bad" got the fence back, arguing with
                # its own timescale. The threshold met is the answer here, and the pools further
                # down that say so are never reached from this arm, so it is said here.
                if _past_the_timescale(said, memory):
                    return pick(_round_robin(MET_LINES, said), memory, said)
                return _say(SEE_STATED_LINES, memory, flat, when=stated)
            return None
        # A call for today is the answer, and the reply says so with the answer's own urgency: a
        # card that opens "Ring 111 today" must not come back as "get it looked at properly" with
        # the 111 gone.
        if _care_for_now(first_said):
            return pick(YES_SAID_LINES if URGENT_CALL.search(first_said) else SOON_LINES,
                        memory, flat)

        return None

    # "is that just age" is not a symptom and none of the pools below can answer it: what the
    # person wants to know is whether what they are seeing is ordinary, and the answer above has
    # already said what to watch for. Reading the referral out of that answer gives the bare "yes,
    # that one wants a proper look", which throws the answer's own hedge away.
    if JUST_AGE.search(flat):
        return pick(AGE_LINES, memory, said)
    # An amount owed is a figure against a usual one, and only an answer that gives the usual one
    # can have the comparison handed back: a money worry with a warm chat line above it has no
    # figure to compare, so it keeps the reading its own line earns.
    if _a_figure_owed(line) and (_is_a_comparison(said)):
        return pick(MONEY_LINES, memory, said)
    # The answer's own fenced condition answers the bare ask whatever the order of the two
    # readings inside it, and main pins that (`test_the_bare_asks_all_get_the_condition`). The
    # cystitis answer opens "that is usually cystitis" and ends "See a GP or pharmacy the same day
    # if it lasts over three days, comes with blood": read through the comparison below, the
    # "usually" came first and the person was told their stinging was the ordinary job, with the
    # one thing the answer named to watch for gone.
    # The cue is read from the earliest care word in the answer, fenced or not, because a referral
    # the answer fences with an "if" is not an unconditional one and `_referral` walks past it -
    # and that is exactly the sentence whose condition answers the ask ("See a GP if there's
    # blood, a high fever" is the whole verdict of the runs answer).
    care_at = _first(str(said or "").lower(), CARE)
    if care is not None and (care_at is None or care < care_at):
        care_at = care
    # The timescale the answer hedged on comes before its referral, and before its own fenced
    # condition: "if it lasts more than three weeks" over "i have had a cough for months" is a
    # fence the person is already standing past, and handing it back told them to watch a thing
    # they had already watched for months. Almost every answer with a threshold in it ends by
    # naming who to ring once that threshold is met, so the hedge is the answer and the referral
    # is only what to do about it.
    if _past_the_timescale(said, memory):
        return pick(_round_robin(MET_LINES, said), memory, said)
    if care_at is not None:
        fenced = _condition_after_care(said, care_at, memory)
        if fenced:
            # The condition is the answer's own words and it answers both doubts the same way:
            # "Ordinary on its own, yes. It stops being ordinary if you actually faint". A pool
            # written for "is it normal" only would argue with the answer over "is that bad".
            # The other way round is not true: CONDITION_LINES opens "Not the thing itself, no",
            # which over "is it normal" is the opposite of the answer it is quoting (neat-moth,
            # #3872). `pick` is seeded on the bare ask, which is the same words every time, so
            # every normality ask that reached this branch got that first line and then said the
            # thing "would stop being ordinary if ..." - a reply that argues with itself and with
            # the card, over the one ask this module exists for. The ask decides which way the
            # line leads.
            return pick(CONDITION_NORMAL if normal_ask else CONDITION_LINES,
                        memory, flat).replace("{when}", fenced)
    denies = _first(opening, DENIES)
    if care is not None and (ordinary is None or care < ordinary
                             or _a_plain_go(care, said)):
        return pick(_care_pool(said) if normal_ask else yes_pool, memory, flat)
    # A referral out of a later sentence, over an answer whose opening named the ordinary cause:
    # the knee answer ends "Ring your GP or a physio this week" and "is that bad" was told "that
    # one is the ordinary kind, so no". A denial in the opening still settles it.
    if care is not None and (ordinary is None or care < ordinary):
        return pick(YES_LINES, memory, flat)
    if denies is None and anywhere is not None and ordinary is not None:
        return pick(_care_pool(said) if normal_ask else yes_pool, memory, flat)
    if ordinary is not None:
        # A normality ask over an answer that said the ordinary thing and then named the
        # exception: the exception is the half that answers it. "usually harmless - worth getting
        # it checked if it hurts or gives way" read as a plain "the ordinary kind" tells the
        # person whose knee clicks with pain that their knee is normal. A yes/no doubt keeps the
        # answer it has always given, because there the ordinary word is the verdict to the
        # question asked ("is that bad" -> "the ordinary kind, so no", with the condition to
        # watch).
        if when and normal_ask:
            return pick(CONDITION_NORMAL, memory, flat).replace("{when}", when)
        # "my boiler makes a knocking noise" / "is it normal" was answered "...bleed the
        # radiators, check the pressure is 1 to 1.5 bar...", and the verdict came back "Yes,
        # that is the usual thing. Nothing to act on now" - over an answer whose own second half
        # is a job. Reassurance and a fix in one answer is the same reading as a fix on its own:
        # ordinary, and the fix above is the thing that settles it, so the pool for a fix carries
        # the verdict and the ordinary one stands aside (snappy-net, #3872). A harmless answer
        # keeps its own word: "White furry mould on the top of the compost is harmless: ... Scrape
        # it off ..." gives a job, and "is it bad for me" has one thing to answer, which is the
        # "harmless". Only a second half that is a job and no harmlessness claim in the answer
        # gives the fix the verdict.
        # The normality ask only. "is that bad" wants a verdict on the thing ("the ordinary kind,
        # so no"), and this pool talks about the answer rather than about the thing, which is not
        # a verdict at all: "i get a headache every afternoon" / "is that bad" came back "that
        # answer is the fix rather than a verdict on how bad it is" (apt-lime, #3872). The pool
        # below is reached by the ordinary reading that follows.
        if normal_ask and _first_positive(opening, SAYS_NORMAL) is None and _a_how_to(said):
            return pick(_round_robin(NOTHING_WARNED_NORMAL, said), memory, said)
        # "It is common at four and still common at nine ... so it is worth a GP visit whatever the
        # age": the ordinary word is not the whole answer, and "nothing to act on now" would
        # contradict the answer's own advice. The care has to be for now, though - "get it looked
        # at if it gives way" is advice for later and leaves the ordinary reading alone.
        if _care_for_now(said):
            return pick(BOTH_LINES, memory, flat)
        # An answer that names someone to see is not the answer this composer may call ordinary,
        # wherever the "usually" sits: the lump answer opens "usually a swollen gland from an
        # infection" and ends "anything hard, painless, fixed in place, or still there after three
        # weeks needs a GP, and so does a lump with night sweats or weight loss". Read on its
        # opening alone, "is that bad" was told "that one is the ordinary kind, so no" - an
        # all-clear over the answer's own referral, and the one reply a person with a lump must
        # not get. A referral the composer can put a fence on is handed back by the condition
        # pool above; one it cannot read a fence from ("needs a GP", "is a GP matter") is a visit
        # rather than a watch.
        # The referral can be the answer's judgement rather than an instruction - "Anything hard,
        # painless, fixed in place, or still there after three weeks needs a GP" - and then the
        # list in front of it is the fence, not a reason to say "ring them" about a soft lump
        # that the same answer called the ordinary sort. Read from the closing sentence only, so
        # a how-to answer's "anything left on the hob is..." is never touched.
        fence = _a_judgement_fence(said)
        if fence:
            return pick(CONDITION_LINES, memory, flat).replace("{when}", fence)
        if warns and not _when(said) and _referral_about_the_thing(said, _the_line_behind(memory)):
            return pick(SEE_ANYWAY_LINES, memory, flat)
        # The ordinary reading in the words of the thing itself, when it is a thing: the body
        # pools below watch it for a week and offer it a proper look, which over a boiler is
        # advice to leave it alone (#routing 77551).
        if thing and not normal_ask:
            return pick(THING_ORDINARY, memory, flat + " " + thing)
        return pick(ORDINARY_NORMAL if normal_ask else (OK_LINES if ok_ask else NO_LINES),
                    memory, flat)
    # The answer's own condition before the "worth doing" pool: "Shaking that has crept on over
    # months ... is worth a GP appointment" is advice for later in the answer's own words, and
    # "Sort it the way I said; if it keeps coming back, that's when it's somebody else's job"
    # drops the condition the answer took the trouble to describe.
    when = _when(said)
    if when:
        # The answer's condition has to be a condition: when it is the line the person just
        # wrote, quoting it back is a tautology, and a tautology in front of "ordinary on its
        # own, yes" reassures the person about the thing they were worried about.
        if _the_fence_is_their_own_line(said, memory):
            # When the answer also named somebody for today, that call is the answer's next step
            # and it is the one to point at: "my baby is not feeding" was met with "ring 111 or
            # your GP now", and the verdict is yes rather than a line about watching.
            if _a_call_for_now(said):
                return pick(YES_LINES, memory, flat)
            return pick(_round_robin(MET_CONDITION_LINES, said), memory, said)
        return pick(CONDITION_NORMAL if normal_ask else CONDITION_LINES,
                    memory, flat).replace("{when}", when)
    # A care word the answer fenced with an "if" is advice for later, so it is not a referral now
    # and the condition it was fenced by is the half that answers the bare ask: "Spicy food and
    # alcohol make it worse, and if you sweat buckets from one place or at night, that is worth a
    # GP visit" is the answer's condition, and "get it seen to" says the sweating is bad today.
    # This fallback is for an answer whose fence cannot be read as a condition; where it can, the
    # condition is handed back above (another lane, on main).
    if care is not None or anywhere is not None:
        return pick(DO_NORMAL if normal_ask else DO_LINES, memory, flat)
    if _first(opening, CARE) is not None:
        # A care opening that named a professional is that call, not a job to do: "get someone
        # in" is a plumber coming round, and "my son is 3 and not talking yet" was answered by
        # the answer's own "ask your health visitor or GP for a referral rather than waiting"
        # with "Do the job I described, and if it comes back after that, get someone in".
        if _first(opening, PEOPLE_CARE) is not None:
            return pick(YES_LINES, memory, flat)
        return pick(DO_NORMAL if normal_ask else DO_LINES, memory, flat)
    # The answer explained the thing and gave a fix, and said nothing about danger either way.
    # "damp in the corner of my bedroom" / "is that bad" was answered "Alright then - good luck
    # with it": the person asked whether it matters, and the bot handed back the door. What the
    # answer did say is that it is a thing to put right, so the verdict is that reading and not
    # a claim about how serious the thing is. It needs the answer to be a how-to rather than an
    # aside: a fix in it, and no referral, reassurance or stop anywhere.
    if _a_fix_with_no_warning(said):
        # Somebody who owes the person a duty changes whose problem it is, so the line says
        # what makes it theirs rather than calling the fault ordinary.
        if _somebody_owes_them(memory):
            return pick(_round_robin(OWED_LINES, said), memory, said)
        # Seeded on the answer, not on the bare ask: "is that bad" is the same seven words every
        # time, so seeding on it gave the damp, the rice and the radiator one identical sentence,
        # which is the one thing STYLE does not allow a pool to do.
        pool = NOTHING_WARNED_NORMAL if normal_ask else NOTHING_WARNED_LINES
        return pick(_round_robin(pool, said), memory, said)
    # An answer that is an instruction and nothing else, on a line that was not a how-to ask: the
    # pools above all stood aside (each needs an answer that explained the thing, named a referral
    # or gave a fix with a warning in it), and the acknowledgement floor took the turn with a
    # goodbye. Read here, at the end, so a pool that does have something to say keeps the turn.
    if _an_instruction_and_nothing_else(said, memory):
        # The answer's own closing sentence is the referral more often than not, and then there is
        # nothing to be vague about: the boiler answer ends "if it keeps dropping, stop topping it
        # up and get a heating engineer out", and "is that dangerous" four turns into that chat was
        # told "Nothing in that says how serious it is" over an answer that does say. Standing the
        # reading aside is not enough - every answer in this pool is an instruction and nothing
        # else, so the five doubt tests that need this pool went to the acknowledgement floor and
        # got a goodbye - and handing back the referral alone loses the figure the person acts on.
        # So the closing referral is the verdict, and the range the answer gave is kept with it.
        referral = _the_referral_it_closed_on(said)
        if referral:
            kept = _the_range_it_gave(said)
            said_back = referral + (f" {kept}" if kept else "")
            return pick(_round_robin(HANDED_BACK_LINES, said + " " + flat),
                        memory, said + " " + flat).replace("{referral}", said_back)
        # Seeded on the answer and the ask together: "is that bad" and "is that ok" over one answer
        # are two doubts and get two sentences, while the same ask twice gets the same answer.
        return pick(_round_robin(DIRECTED_LINES, said + " " + flat), memory, said + " " + flat)
    return None


# The referral said back as the verdict, when the answer closed on one. The person asked whether
# the thing matters, and the answer already says when to act and who to call, so the reply is that
# and not a line about the reply.
HANDED_BACK_LINES = (
    "That is worth acting on rather than watching: {referral}",
    "It needs sorting rather than waiting: {referral}",
    "Not one to sit on: {referral}",
)

# The range an answer gives, which is the half a person acts on and the half a bare referral
# drops: "keep it between 1 and 1.5 bar" out of the boiler answer. Read as a range of numbers with
# a unit after them, so "between 1 and 1.5 bar", "30 to 35 psi" and "between 18 and 20 degrees"
# all arrive, and a "between 2 and 3" with no unit after it does not.
_A_RANGE_OF_ITS_OWN = re.compile(
    r"\b(?:between|from) (\d+(?:\.\d+)?) (?:and|to) (\d+(?:\.\d+)?) ?([a-z]{2,10})\b", re.I)


# "Get a heating engineer out" is the way a boiler answer names the trade, and REFER reads
# see/ring/call/contact, so the act was invisible to it and the closing sentence of the boiler card
# matched nothing. The trade comes with "out", "round" or "in" after it, which is what makes it an
# act rather than a mention: "an engineer will check the pressure" is not this.
_A_REFERRAL_OUT = re.compile(
    r"\b(?:get|have|call|ring|book) (?:a |an |your |the )?"
    r"(?:(?!and\b|or\b|to\b|it\b)[a-z-]+ ){0,3}"
    r"(?:engineer|plumber|electrician|mechanic|technician|specialist|someone) ?(?:out|round|in)\b",
    re.I)
# And what to stop doing, which is the other half of a closing act: "stop topping it up".
_A_STOP = re.compile(r"\b(?:stop|don't|dont|do not) (?:[a-z]+ing|it|using it|driving|eating)\b",
                     re.I)


def _the_referral_it_closed_on(said):
    """The answer's closing sentence, when that sentence says who to get or what to stop.

    Only the closing sentence: an answer that names a professional in passing ("if it is a gas
    leak, a Gas Safe engineer needs to look at it") and then ends on a step is a how-to, and the
    pools above have it. What is left is an answer whose last word is the act.
    """
    sentences = [s.strip() for s in re.split(r"(?<=[.!?]) +", _flat(said)) if s.strip()]
    if not sentences:
        return ""
    last = sentences[-1]
    if len(last.split()) < 5:
        return ""
    if not (REFER.search(last) or _A_REFERRAL_OUT.search(last) or _A_STOP.search(last)
            or _first(last, STOP_DOING) is not None):
        return ""
    # The fence in front of the referral is about when to act, and the doubt comes after the
    # person has just said the situation is happening: "if it keeps dropping, stop topping it up"
    # said back to somebody who has said it drops within a day is a condition already met, and
    # handing it back verbatim asks them the question their own account answered.
    unfenced = re.sub(r"^(?:but )?(?:if|once|when|whenever) [^,]{0,70}, ", "", last, flags=re.I)
    # A stop only means something the first time it is said: by the doubt the person has already
    # been told to stop, so the half of the act that answers them is the one that names who to
    # get. Said back whole, the line is the last answer word for word, and the arbiter passes over
    # a reply that repeats the last answer - the boiler doubt came back as the whole card with
    # "Same answer, and it covers this" in front of it, a paragraph already on the screen.
    act = re.sub(r"^(?:stop|don't|dont|do not) [^,]{0,40}?,? (?:and|but) ", "", unfenced, flags=re.I)
    if len(act.split()) >= 4:
        return act
    return unfenced if len(unfenced.split()) >= 4 else last


def _the_range_it_gave(said):
    """The range the answer told the person to hold, said as a line to keep, or "".

    A referral on its own tells somebody to ring someone; the figure is what they do while they
    wait, and it is the half of the answer they act on. "between 1 and 1.5 bar" comes back as
    "Keep it between 1 and 1.5 bar in the meantime."
    """
    found = _A_RANGE_OF_ITS_OWN.search(_flat(said))
    if not found:
        return ""
    low, high, unit = found.group(1), found.group(2), found.group(3)
    if unit.lower() in ("and", "the", "for", "with"):
        return ""
    return f"Keep it between {low} and {high} {unit} in the meantime."


# The verbs an answer opens its first instruction on, for the reading below. `DOING` is the
# knowledge base's own instruction vocabulary and it already has `ask`, which is what "Ask for the
# increase in writing" opens on; `opens_on_a_job` cannot be reused here because it stands back from
# "ask for" and from "say", both deliberate where it is read (the step turn must not hand back the
# bot's own request for a subject). This reading is only ever handed an answer from the knowledge
# base, so the greeting's "say more if it helps" cannot reach it.
_STEP_OPENERS = DOING | frozenset(("say", "deal", "mention", "flag", "chase", "push", "insist"))


def _an_instruction_and_nothing_else(said, memory):
    """True when the answer only told the person what to do, on a line that stated a situation.

    A how-to the person asked for ("how do i clean the kettle") is not this: its answer is a
    method, and the pools above have it. What is left is somebody describing their week - a mate
    who keeps cancelling, a parking ticket, a rent rise - answered with the one thing to do about
    it, and a bare doubt that no pool above could rule on.
    """
    flat = _flat(said)
    if len(flat.split()) < 12:
        return False
    head = re.split(r"[:;.!?]", flat, 1)[0].strip(" ,-")
    words = _WORD.findall(head)
    if not words or words[0].lower() not in _STEP_OPENERS:
        return False
    line = _flat(_last_person_line(memory))
    if not line or A_HOW_TO_ASK.search(line):
        return False
    return True


# The answer above asked the person something instead of telling them anything, and the doubt on
# top of it has no answer to read: nothing in that reply can be ruled on, so the honest move is to
# say so and ask for the part that decides it. No line claims the thing is fine, and none of them
# repeats the question the bot just asked.
ASKED_THEM_LINES = (
    "Nothing you have told me makes it bad or fine on its own - that depends on how much it is "
    "getting to you. What is the bit that worries you most?",
    "No verdict from me on that one yet. Say what has you asking and I will tell you whether it "
    "is worth doing something about.",
    "That depends on something I have not heard yet. What is it that has you wondering?",
)


# A line with a trouble in it, for the reading below: the doubt that comes after a floor's
# question is a doubt about something that is going wrong. Without this the pool took
# "i got the job" / "Love that - well done. How are you celebrating?" / "is that ok" and answered
# it as if the job were the worry.
A_WORRY_IN_THE_LINE = re.compile(
    r"\b(?:keeps?|kept|wont|won't|refuses?|never|won't stop|hate|hates|hated|awful|horrible|"
    r"rude|nasty|unfair|upset|angry|annoyed|miserable|cry|crying|cried|stress|stressed|"
    r"worried|worry|worries|exhausted|knackered|drained|tired|hits?|hit me|shouts?|shouting|"
    r"yells?|yelling|ignores?|ignoring|off with|weird|odd|wrong|problem|falling out|fell out|"
    r"argument|arguing|argue|fights?|fighting|bully|bullied|bullying|debt|debts|skint|broke|"
    r"struggling|struggle|too much|fed up|sick of|dreading|scared|afraid|lonely|alone|"
    r"not talking|stopped talking|on top of me|getting on top|cant cope|can't cope|coping|"
    r"breaking point|drowning|shattered|rough week|bad week|a lot on|driving me|drives me|"
    r"nightmare|cant stand|can't stand|nagging|bossy|unbearable|hell|temper|disrespectful|"
    r"mean to me|picking on me|picks on me)\b",
    re.I)


# The floor's offer of help, said in the same breath as its question: both are the bot staying in
# the conversation, and neither is an answer a doubt can be read out of.
_AN_OFFER = re.compile(
    r"\b(?:if you want|if it helps|i can help|happy to help|tell me more|say more|"
    r"i'm listening|i am listening|want to talk|would you like|do you want)\b", re.I)


def _the_floor_asked_them_something(memory):
    """True when the bot's last line was a question rather than an answer to rule on."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1]
    if not isinstance(last, dict):
        return False
    said = " ".join(str(last.get("bot") or "").split())
    # A question, or the offer of help that is the same move said another way: "That sounds rough.
    # If you want, I can help you think through what to do next." is a friend still in the
    # conversation, and the doubt after it was answered "Alright then - good luck with it."
    if not (said.endswith("?") or _AN_OFFER.search(said)):
        return False
    line = _flat(_the_line_behind(memory))
    # A method was asked for, so its answer is a method whoever phrased it: "how do i clean the
    # kettle" then "is that ok" is answered by the method pool, and the question at the end of
    # that answer is not the bot turning the person's own situation back on them.
    if not line or A_HOW_TO_ASK.search(line):
        return False
    return A_WORRY_IN_THE_LINE.search(line) is not None


def _a_feeling_of_their_own(line):
    """The family of state the person's own line named, or "" when it named none or a body."""
    words = [w.replace("'", "").lower() for w in re.findall(r"[A-Za-z']+", line or "")]
    if not words or len(words) > 14:
        return ""
    if words[0] not in ("i", "im", "ive", "id"):
        return ""
    if any(word in BODY_WORD for word in words) or any(word in SOMEONE_ELSE for word in words):
        return ""
    for word in words:
        if word in FEELING_FAMILY:
            return FEELING_FAMILY[word]
    return ""


# A sentence of the answer is the unit a person can act on, and it is what the one-thing ask is
# handed. The cap is what keeps an answer written as one long sentence - "Most back pain is
# muscular and settles in two to six weeks, and staying active is what helps most: keep walking
# ..." - from coming back whole: past this length the step's own clause is the shorter read.
HAND_OVER_WORDS = 42


def _the_other_thing_in_the_answer(said, step, memory):
    """A sentence of the answer above that is not the step and not already on the screen, or "".

    The answer handed over a turn ago is not all one instruction: the card on vegetables opens
    with what to do and then says what makes it work ("Roasting carrots or broccoli in a little
    oil makes them sweeter, and a dip to dunk turns it into a game"). Asked for tips, a friend
    picks that second sentence out, because it is the part the person has not acted on yet. Only
    a sentence that stands on its own is picked: not the step's own sentence, not a question, not
    the warning that ends a health answer, and not something the bot has said in an earlier turn.
    """
    from ..memory.topics import RED_FLAG
    needle = " ".join(str(step or "").split()).lower().strip(" .!?,")
    mine = _flat(said)
    seen = [_flat(turn.get("bot") or "") for turn in
            ((memory.get("turns") if isinstance(memory, dict) else None) or [])
            if isinstance(turn, dict)]
    # The answer in hand is the last thing said, so the turns before it are the ones a sentence
    # from it can have been read in already.
    earlier = [heard for heard in seen[:-1] if heard and heard != mine]
    sentences = [one for one in re.split(r"(?<=[.!?]) ", str(said or ""))]
    # The step's own sentence and everything before it are what the person has already acted on
    # or read as the answer: the tips are the sentences after it. An answer whose step could not
    # be found again starts after its opening, which is the sentence a card leads with.
    starts = [i for i, one in enumerate(sentences)
              if needle and needle in one.lower().strip(" .!?,")]
    for sentence in sentences[starts[0] + 1 if starts else 1:]:
        text = " ".join(sentence.split()).strip()
        if len(text.split()) < 6 or _is_a_question(text):
            continue
        if needle and needle in text.lower():
            continue
        if RED_FLAG.match(text):
            continue
        if ASKS_THEM.match(text):
            continue  # "Tell me what is in the fridge": the answer's own question is not a tip
        if any(text.lower() in heard for heard in earlier):
            continue  # a sentence an earlier turn already said is not one more thing
        return text
    return ""


def _step_sentence(said, step):
    """The whole sentence the answer wrote the step in, or "" when it cannot be found again.

    The step itself is the first clause of that sentence ("Give them sun"), which is the right
    unit for the pools that add an order to it. A person who asks for the one thing is owed the
    instruction, not a fragment of it: "where do i start" after the tomato answer was handed back
    "Just the one, then: Give them sun." and lost the pot, the watering and the reason, none of
    which the person has read twice. So the whole sentence is quoted, and only the pools written
    for a sentence of its own hand it over.
    """
    needle = " ".join(str(step or "").split()).lower().strip(" .!?,")
    if not needle:
        return ""
    for sentence in re.split(r"(?<=[.!?]) ", str(said or "")):
        text = " ".join(sentence.split())
        if needle and needle in text.lower():
            return text.strip(" .!?")
    return ""


def _up_to_a_break(said, step, within):
    """The longest run of the sentence that ends on one of the sentence's own breaks.

    A person who asks for the one thing is owed the instruction, and one instruction can be a
    sentence with a colon and a dash in it: "Fill a freezer bag with white vinegar - half vinegar,
    half water if the chrome worries you - tie it over the shower head so the nozzles soak for an
    hour" is one move from start to finish, and the moves after it ("then rub them with a sponge
    and poke any blocked holes with a pin") are the next thing to do, not this one. So where the
    sentence runs past what one instruction is worth (`within`), the longest piece of it that ends
    where the answer itself breaks is handed over, and the tail is left for "what else".
    """
    words = str(said or "").split()
    if len(words) <= within:
        return said
    # The framing in front of the step is not part of it: "Most back pain is muscular and settles
    # in two to six weeks, and staying active is what helps most: keep walking..." opens on a fact
    # and puts the move after the colon, so the piece starts at the move.
    opening = " ".join(words).lower().find(" ".join(str(step or "").split()).lower())
    start = len(" ".join(words)[:opening].split()) if opening > 0 else 0
    if start and start < len(words) - 1:
        said = " ".join(words[start:])
        words = said.split()
        if len(words) <= within:
            return said
    best = ""
    for found in re.finditer(r"[,;:]|\s[-\u2013\u2014]\s", str(said or "")):
        head = str(said or "")[:found.start()].strip(" ,;:-\u2013\u2014")
        if len(head.split()) <= within and len(head.split()) > len(best.split()):
            best = head
    return best or " ".join(words[:within])


def _an_instruction_sentence(said):
    """The answer's own first instruction, for an answer `_step` could not read one out of.

    Some answers write the move as a thing rather than a verb - "A dentist or a hygienist scale
    and polish first, because most yellowing is staining on the outside" - or label it before a
    colon ("The thing to do first: write down what is actually due this week"). `_step` finds
    neither, and the one-thing ask was answered "none of it is one job to start with" about an
    answer that plainly had one. Only a sentence with something imperative in it counts, so an
    answer that really is all explanation still gets the line that says so.
    """
    from ..memory.topics import RED_FLAG
    for sentence in re.split(r"(?<=[.!?]) ", str(said or "")):
        text = " ".join(sentence.split())
        if not text or CONDITIONAL_OPEN.match(text) or RED_FLAG.match(text) or _is_a_question(text):
            continue
        if A_STATEMENT.match(text):
            continue  # "Pay is at least the apprentice minimum wage": a fact, not a move
        if _doing_word(re.findall(r"[A-Za-z'’-]+", text)[:5]) in IMPERATIVES:
            return text.strip(" .!?")
        head, colon, tail = text.partition(": ")
        if colon and tail and (_doing_word(re.findall(r"[A-Za-z'’-]+", tail)[:5])
                               in IMPERATIVES):
            return text.strip(" .!?")
        if FIRST_ITSELF.search(text) and not COPULA.match(text) and len(text.split()) >= 5:
            # "A dentist or a hygienist scale and polish first": the move is written as the thing
            # to get done, and the sentence says it is the first one. A sentence that only says
            # what the thing is ("The first day is the worst") is not a move and is left alone.
            return text.strip(" .!?")
    return ""


def _the_answer_under_a_frame(memory):
    """The answer under the last repeat frame in the chat, or "" if there is not one.

    A repeat said by the store ("Nothing separate for friday - it is the same advice: Rehearse the
    first sixty seconds out loud ...") is not a module the composer reads, so nothing was read at
    all and the step ask after it got a search hedge. The frame is the store saying this is the
    answer already on the screen, so the answer under it is the one to read - and only that: a
    turn that is not framed is left for the store to answer, exactly as before.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return ""
    last = turns[-1]
    if last.get("module") in UNREADABLE:
        return ""
    return again_reply.unframed(last.get("bot")) or ""



# The words in front of a colon that name the thing rather than say something about it: the
# article in front of a noun is dropped, and the two words after it are the subject. Anything
# past that is the verb and what follows it ("A loo seat bangs because ...").
FRONT_LEAD = frozenset(("a", "an", "the", "my", "your", "our", "their", "his", "her", "its",
                        "one"))
# A front built on one of these names no thing of its own: "That is a few pounds, not a new
# instrument" and "It is nearly always a worn washer" are about the thing already in the chat, so
# the person has read the diagnosis and the step starts at the move. A front that does name a
# thing ("A loo seat bangs because ...") is judged by whether that thing is in the chat.
FRONT_THIS = frozenset(("it", "that", "this", "they", "these", "those", "there"))
# A front that carries the trigger is not a diagnosis but the condition the move hangs on:
# "Defrost it when the ice is more than about 5mm thick: switch it off at the wall" loses the
# number that says when to bother, and the move after the colon reads as something to do now.
FRONT_WHEN = frozenset(("when", "if", "once", "unless", "whenever", "till", "until"))
FRONT_SUBJECT_WORDS = 2


def _the_front_names_what_is_in_hand(head, line, memory):
    """Whether the subject of the clause in front of a colon is the thing this chat is about.

    The words of the chat are the line itself and what the person and the bot have already said,
    because a follow-up that names the job says "how do i fix it" and not the thing: the dripping
    tap is in the first turn, not in the ask.
    """
    words = re.findall(r"[A-Za-z'’-]+", str(head or "").lower())
    if any(word in FRONT_WHEN for word in words):
        return False
    if words and words[0] in FRONT_THIS:
        return True
    subject = [word for word in words if word not in FRONT_LEAD][:FRONT_SUBJECT_WORDS]
    if not subject:
        return False
    in_hand = set(re.findall(r"[a-z'’-]+", str(line or "").lower()))
    for part in (memory or {},) if isinstance(memory, dict) else ():
        for topic in [part.get("topic")] + list(part.get("topics") or []):
            if isinstance(topic, dict):
                in_hand.update(str(word) for word in topic.get("words") or ())
        for turn in part.get("turns") or []:
            if isinstance(turn, dict):
                in_hand.update(re.findall(r"[a-z'’-]+", str(turn.get("user") or "").lower()))
    for word in subject:
        if word in in_hand:
            return True
    return False


def next_step(clean, memory):
    """A bare "what should i do" or "should i see someone", answered from the advice given."""
    flat = _flat(clean).strip(" .!?")
    bare = bool(STEP.match(flat))
    # A speak-up is about the thing in hand ("should i say something", "should i mention it"),
    # and the step the last answer gave is what they would say. A line that brings somebody new
    # is not that ask: "my knee clicks when i climb stairs" / "should i text him back" asked
    # what to do about a person nobody has introduced, and the knee answer's step came back.
    someone_new = (memory.get("understood") or {}).get("someone_new") \
        if isinstance(memory, dict) else None
    asks_step = bare or (bool(SPEAK_UP.match(flat)) and not someone_new)
    asks_who = bool(SEE.match(flat))
    # A plea for tips is read this way only when the answer above is the knowledge base's: a warm
    # chat line ("guard one evening this week that's just yours") is not a list of steps, and
    # pointing a person back at it as one would be the same fault the tips pool has.
    plea = bool(TIPS_AGAIN.match(flat) or ONE_THING.match(flat))
    # A plea for tips is not the ask for the first move, even though both want the answer above
    # read: "any tips" asks for something more than the card, and "where do i start" asks for the
    # one thing out of it. The difference decides whether the step is quoted below.
    tips = bool(TIPS_AGAIN.match(flat))
    # "how do i prepare" with the talk in hand asked the same question the answer above answered,
    # so it is a step ask and not a line for the base to fail on: the doing names no thing of its
    # own ("how do i cook rice" does, and is the knowledge base's).
    how_to = HOW_TO.match(flat)
    how_to_asked = bool(how_to) and (
        how_to.group("doing") in DOING_WITH_NO_OBJECT
        or (how_to.group("obj") and how_to.group("doing") not in KNOWING_DOING))
    if how_to_asked:
        asks_step = True
    if plea and _last_module(memory) == "answers":
        asks_step = True
    # "whats the safest way", asked one line after the answer said how: the same ask as a plea for
    # tips, and it was answered "That's beyond what I know well ... a search should sort you out".
    if A_HOW_ASK.match(flat) and _last_module(memory) == "answers":
        asks_step = True
    if not (asks_step or asks_who):
        return None
    said = _last_reply(memory, past_the_verdict=True) or _the_answer_under_a_frame(memory)
    if not said:
        return None
    if _first(said, AGAIN) is not None:
        # The answer above came back framed as the repeat it was ("Nothing separate for friday -
        # it is the same advice: Rehearse the first sixty seconds out loud ..."). The step is in
        # the answer under the lead-in, and somebody who has read it twice and asks how to
        # prepare wants that step, not a search hedge. With nothing under the frame there is no
        # step to give, and the turn is not this one's.
        said = again_reply.unframed(said)
        if not said:
            return None
    if EMERGENCY_CALL.match(said.strip()):
        # "should i call 999" after an answer that said to ring for an ambulance is the emergency
        # reader's line, not a step quoted back: the answer's own words for the first move are
        # "Ring now rather than waiting to be sure" once its colon is cut, and half of an
        # emergency instruction is worse than none of it.
        return None
    when = _when(said)
    if asks_who:
        if when:
            return _say(SEE_NOW_LINES, memory, flat, when=when)
        stated, kind = _stated_referral(said)
        if stated:
            # The answer named the point where it wants a person, so the answer is that point and
            # not this composer's own guess at one.
            pool = SEE_NOW_LINES if kind == "clause" else SEE_STATED_LINES
            return _say(pool, memory, flat, when=stated)
        if REFER.search(said):
            return pick(SEE_ANYWAY_LINES, memory, flat)
        if _first(said, CARE) is not None:
            return pick(SEE_NONE_LINES, memory, flat)
        return None
    step = _step(said)
    if not step and _ends_on_a_question(said):
        # The bot's last line was its own question, so the line above is a question and not an
        # answer, and there is no step in it. "i want to lose weight" / "i hate exercise" / "what
        # should i do first" came back with "Start with what I asked: what is the worst bit of
        # it?" - the bot asking its own question again - while the answer before it still had the
        # step the person was asking for. A friend hands over the step, so the step is taken from
        # the last line that was an answer.
        step = _step(_the_answer_before_that(memory))
    if step and _echoes_the_person(step, memory):
        step = None
    if tips:
        # A plea for tips one turn after the answer is the case where the answer still has
        # something in it: the step is the sentence they have just read, and the sentence after it
        # is news ("Roasting carrots or broccoli in a little oil makes them sweeter, and a dip to
        # dunk turns it into a game"). Only when there is no such sentence is there nothing to add.
        other = _the_other_thing_in_the_answer(said, step, memory)
        if other:
            return _say(ALSO_LINES, memory, flat, other=other)
        if not step:
            # The card above is all of it - one sentence and a question back, or a list with no
            # next thing in it - so there is nothing to add and nothing to quote. Saying that is
            # the honest reply, and the search hedge ("that's most of what I know on it") is a
            # shrug in place of it.
            return pick(STEP_KEPT_LINES, memory, flat)
    if step and (_already_asked_for_a_step(memory)
                 or _most_of_the_line(step, _the_line_just_given(memory))
                 or tips):
        # A plea for tips that the answer above cannot add to is the answer again by another word:
        # the knowledge base had its turn at it above and had nothing more to say (a card that does
        # outranks this line), so quoting its first sentence back is the whole card's opening said
        # a turn later - "Keep serving one small piece of veg next to something they already like"
        # under "any tips". The step has not changed, and saying that is the honest reply.
        # The step has already been given: the person asked for one twice running, or the answer
        # above was a single sentence and that sentence was the step itself, so quoting it hands
        # them back what they have just read. Saying it again is the one thing STYLE.md forbids,
        # and there is no second step to give because the answer had nothing else in it - so the
        # line says the step stands and adds nothing to it.
        return pick(STEP_KEPT_LINES, memory, flat)
    if not step:
        # An offer of help that the person has just taken up is not a question waiting to be
        # handed back: "What would help most right now?" then "what do i do" is the person
        # saying "this", and the pool below would answer it with a shrug. There is no step in
        # the bot's own question to quote, so this composer stands aside and lets the fallback
        # make its honest pass.
        if _an_offer_is_waiting(said):
            return None
        if bare and _ends_on_a_question(said):
            # Only a bare ask ("what now", "what should i do") is handed back. A decision ask
            # ("should i say something") names what it is about, and "nothing to do on my side"
            # denies it: after "my sister keeps borrowing my stuff" / "what have you tried
            # saying so far?", "should i say something" was answered "Nothing to do on my
            # side, honestly - whatever comes to mind about it first is the useful bit" where
            # the composer's own decide line (fallback.UNKNOWN_DECIDE, "That's your call, not
            # mine... tell me what you're weighing") had answered it. Left alone here, that line
            # answers the turn, and the question back is only for the ask that names nothing.
            # The news in the line before is the one exception, and it is checked first: "What
            # would help most right now" over "bailiffs turned up" is a question about the news,
            # and the ask that follows ("what do i do") wants an answer about the bailiffs - which
            # the entry beside this one already has. Handing the question back there took that
            # answer away and told the person there was nothing to do on my side.
            if _the_news_just_before(memory):
                return None
            asked = _the_question_asked(said)
            if asked and THE_PLEA.match(flat):
                return pick(QUESTION_BACK_LINES, memory, flat)
            if asked and _after_a_comfort_line(memory):
                return pick(QUESTION_BACK_LINES, memory, flat)
            if asked and AN_OFFER.search(asked):
                return pick(OFFER_TAKEN_LINES, memory, flat)
            if asked:
                return _say(ASKED_FIRST_LINES, memory, flat, q=asked)
            return pick(QUESTION_BACK_LINES, memory, flat)
        # "It needs nothing doing. If the noise comes with pain or swelling, treat it as pain":
        # an answer whose own advice is to do nothing still answers "what should i do", as long
        # as it says what would change the picture. With no instruction and no condition there
        # is nothing to say from it, and the fallback's own line is the honest one.
        # A plea for tips wants a move, so it is never answered with the condition alone ("Nothing
        # you need to do yet - it matters if it has gone on a month"): the answer's own list is a
        # move when it wrote one, and with neither the fallback's own line is the honest reply.
        # A bare "what should i do about it" wants a move just as much, and an answer that wrote
        # its moves after a colon is the same list: "i cant sleep" / "what should i do about it"
        # was told "Nothing you need to do yet - it matters if you're worn out all day too" over
        # "The things that work: same wake-up time every day, no caffeine after early afternoon".
        listed = _listed(said)
        if listed:
            return _say(LIST_STEP_LINES, memory, flat, step=listed)
        # "Nothing to do" is a claim about the answer, so it is only made when the answer really
        # wrote one thing or none. The back-pain answer carries four moves, but they sit inside a
        # colon and behind an "if" ("the thing that settles it is the right amount of use: keep
        # going as far as is comfortable and add two short sessions a week"), so no step was found
        # and the bare ask was answered "Nothing to do for now" - the opposite of the paragraph
        # above it. More than one action in the answer and the fallback's own line is the honest
        # reply, as it is with no condition at all.
        if when and not plea and _action_count(said) < 2:
            return pick(NOTHING_LINES, memory, flat).replace("{when}", when)
        if ONE_THING.match(flat) and _last_module(memory) == "answers":
            # The answer above may still have written a move this reader cannot cut a clause out
            # of ("A dentist or a hygienist scale and polish first", "The thing to do first: write
            # down what is actually due this week"). Where it did, that sentence is the one thing
            # and it is handed over as it stands; the line that says there is no move in it is for
            # the answer that really has none.
            move = _an_instruction_sentence(said)
            if move:
                head = move.partition(": ")[0].strip(" .;:,-")
                if ": " in move and len(head.split()) >= 8:
                    # The answer put a menu or a second choice after its colon ("... scale and
                    # polish first, because most yellowing is staining: either a professional kit
                    # or a high-street one"). The one thing asked for is the part before it.
                    move = head
                elif len(move.split()) > HAND_OVER_WORDS:
                    move = _first_clause(move).strip(" .;:,-") or move
                return _say(ONE_TURN_PLAIN_LINES, memory, flat, step=move)
            # Nothing here can name a move, and saying the ask back ("Got it - just one thing to
            # start") is the acknowledgement answering a question, so the line says the answer
            # was the whole of it and offers the part they want taken further.
            return _say(ALL_OF_IT_LINES, memory, flat)
        return None
    # A step that ends in "first" ("Do it in a short meeting first") doubles the word in a line
    # that adds its own: "Do it in a short meeting first first, then work down the list".
    if step.lower().endswith(" first"):
        step = step[: -len(" first")].rstrip()
    # A person who asked for the one thing gets the one thing, however the step is shaped.
    if ONE_THING.match(flat):
        # The person asked for one thing out of a long answer, so the answer's own sentence is
        # handed over entire. The step is only its first clause, and quoting that alone was
        # handing back "Give them sun." to somebody who asked where to start with tomatoes.
        whole = _step_sentence(said, step)
        piece = _up_to_a_break(whole, step, HAND_OVER_WORDS) if whole else ""
        if len(piece.split()) > len(step.split()):
            return _say(ONE_TURN_PLAIN_LINES, memory, flat, step=piece)
        pool = ONE_TURN_PLAIN_LINES if (": " in step or FIRST_ITSELF.search(step)) else ONE_TURN_LINES
        return _say(pool, memory, flat, step=step)
    if how_to_asked:
        # "how do i clean it", "how do i top it up": the line named the job, so the instruction is
        # the whole sentence the step sits in and not its first clause. One instruction can be
        # two moves in one sentence, and the clause stops in front of the second: the washer
        # answer's step read "Run a hot 60C or 90C service wash with a washing-machine cleaner or
        # a cup of bicarbonate of soda" and left out "and clean the filter and the detergent
        # drawer while it runs", which is half the job; the boiler's read "Top the pressure up to
        # between 1 and 1.5 bar using the filling loop" and left out "then bleed the radiators and
        # check it again the next day". A person who asked how to do the thing is owed the move
        # the answer wrote, not the part of it before the comma.
        whole = _step_sentence(said, step)
        if whole and len(whole.split()) > len(step.split()):
            step = whole
        # One answer opens on what the thing is and puts the move after a colon: "A dripping tap
        # is nearly always a worn washer or cartridge: turn the water off at the isolating valve".
        # Handing that back whole says turn one again - the person read the diagnosis in the
        # answer above and asked how to do the job, so the step starts where the move starts. A
        # front clause that is itself an instruction is kept ("Start with a plunger: then undo")
        # because the second half only makes sense with it.
        head, colon, tail = step.partition(": ")
        if (colon and tail and _doing_word(re.findall(r"[A-Za-z'’-]+", head)) not in IMPERATIVES
                and _the_front_names_what_is_in_hand(head, flat, memory)):
            # The front has to be about the thing in this chat as well as not an instruction. One
            # answer slides a list of devices into one sentence ("A loo seat bangs because the
            # rubber bumpers under it have gone hard: tighten the two bolts ..."), and a line
            # about pipes or a blind meets it on the word "bangs". Cutting the front there leaves
            # an instruction about hinges with nothing saying what it is for, and the person
            # never sees that the card picked the wrong thing. Where the front's own subject is
            # in the chat - the dripping tap, the washing machine, the boilers - the front is the
            # part they have already read and the step starts at the move.
            step = tail.strip()
    # A step that already orders itself ("Start with a plunger over the plughole", "block that
    # first") cannot take a second "first", so it gets the lines written for one.
    if FIRST_ITSELF.search(step):
        return _say(STEP_ALREADY_FIRST_LINES, memory, flat, step=step)
    if ": " in step or len(step.split()) >= STEP_LONG:
        # The answer explained the step itself, or the step is too long to take a word on the end
        # ("Track two weeks of what actually leaves the account before you change anything first"
        # lands the order on "anything"), so the line introduces it in a sentence of its own.
        return _say(STEP_DETAIL_LINES, memory, flat, step=step)
    if _action_count(said) > 1:
        pool = STEP_ALREADY_FIRST_LINES if FIRST_ITSELF.search(step) else STEP_LINES
        if how_to_asked:
            # "how do i clean it", "how do i unblock it": the ask names a doing and the thing it is
            # done to, so the reply is the answer's own first step and nothing more. The lines that
            # point at the rest of the answer ("Clip the top growth, before anything else I
            # mentioned") are for an ask about where to begin, not for one that named the job, and
            # a sentence that ends on "I mentioned" reads like a note to self.
            pool = STEP_DETAIL_LINES
        return _say(pool, memory, flat, step=step)
    return _say(STEP_ONE_LINES, memory, flat, step=step)
