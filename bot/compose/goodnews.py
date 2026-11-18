"""Good news said as an event, not as a feeling.

`POSITIVE_CUES` is a list of words, and it catches "i passed", "we won", "we're pregnant". What it
misses is the way people actually tell you about a good thing: the event is in a phrase and every
word of it is plain. "my sister had her baby yesterday", "we got the keys on friday", "he got into
his first choice" are all good news with nothing in `POSITIVE_CUES` to notice it, so the line fell
through to the neutral pool - and, since the acknowledgement landed, to the fact read back:
"Noted: your sister had her baby yesterday" is a filing cabinet, not a friend.

This module notices those events. It only says "this is good news"; the words of the reply belong
to the composer, so the congrats line can change without touching this file. Run it alone:

    python -m bot.compose.goodnews "my sister had her baby yesterday"
"""
import datetime
import re

from . import NEARLY, doubted
from .badnews import reads_as_someones_death

# The words a due date is said with, kept as strings so the two patterns below read as English.
_MONTH = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
          r"aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)")
_WEEKDAY = (r"(?:mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|"
            r"sat(?:urday)?|sun(?:day)?)")
_A_DATE = (r"\s+(?:the\s+)?(?:early\s+|late\s+|mid-?)?"
           r"(?:\d|" + _MONTH + r"|" + _WEEKDAY + r"|christmas|easter|spring|summer|autumn|"
           r"winter|month|week|day|year|a week|a month|two weeks|three weeks)\b")
_DUE = r"\s+due\b"
_WHEN_DUE = r"\s+(?:in|on|next|by|at|early|late|mid)\b"
# Written out rather than "pronoun + optional 'm", because "is" would be read as "i" + "s" and
# "the mot is due in november" is not somebody's baby.
_WHO_DUE = (r"\b(?:i'm|im|i am|we're|we re|we are|she's|shes|she is|he's|hes|he is|they're|"
            r"theyre|they are)" + _DUE + _WHEN_DUE)
_PERSON_DUE = (r"\b(?:the|our|my)?\s*(?:baby|babies|twins?|wife|partner|girlfriend|fiancee?|"
               r"daughter|sister|brother|friend|surrogate)")

# A new baby: the birth is the news, however the family says it.
BABY = (
    re.compile(r"\b(?:had|have|has|have just had|had just had)\s+(?:her|his|the|a|our)\s+"
               r"(?:baby|little (?:girl|boy|one)|girl|boy)\b", re.I),
    re.compile(r"\b(?:baby|girl|boy|twins|daughter|son)\s+(?:was |were |is )?(?:born)\b", re.I),
    re.compile(r"\bgave birth\b", re.I),
    re.compile(r"\b(?:we|she|he|they)(?:'re| are|re)?\s+(?:now\s+)?(?:expecting|pregnant)\b", re.I),
    re.compile(r"\bexpecting\s+(?:a|our|twins)\b", re.I),
    # "its a boy" is the announcement; "a boy" on its own is a person, so the bare form is read
    # only when the line is just the announcement ("a girl, 7 pounds", "a boy!"). Before this,
    # "a boy" anywhere made the line good news: "a boy in my class killed himself" was answered
    # "Congratulations — that's lovely news." and "a boy at my school is being mean to me"
    # "Lovely news — well done." The birth is what is being announced, so it has to be the line.
    re.compile(r"\b(?:it'?s|its)\s+(?:a\s+)?(?:little\s+)?(?:girl|boy|healthy|twins)\b", re.I),
    re.compile(r"^(?:so|well|and|ok|okay|ah|oh)?[\s,]*a\s+(?:little\s+)?"
               r"(?:girl|boy|twins|healthy\s+baby)\s*[.!]*$", re.I),
    # The same announcement with the weight after it: "a girl, 7 pounds 4 ounces". A measurement
    # keeps it a birth; any other words after "a boy" make it the person again.
    re.compile(r"^(?:so|well|and|ok|okay|ah|oh)?[\s,]*a\s+(?:little\s+)?(?:girl|boy|twins)\b"
               r"[^.!?]{0,20}?\b\d+(?:\.\d+)?\s*(?:lb|lbs|pounds?|kg|kilos?|oz|ounces?)\b",
               re.I),
    re.compile(r"\b(?:the|our|my)\s+baby\s+(?:is|was|'s)\s+(?:a\s+)?(?:little\s+)?"
               r"(?:girl|boy|twins|healthy)\b", re.I),
    # And the same announcement in the progressive: "we are having a boy", "she is having a girl".
    # The bare "a boy" pattern used to carry these by accident, and turning it into a whole-line
    # match took the congratulations off a pregnancy: "were having a girl" was answered "Got it -
    # were having a girl." Somebody has to be doing the having, and the lookahead keeps "we are
    # having a boy over for dinner" out of it.
    re.compile(r"\b(?:we|i|she|he|they|my\s+\w+|his\s+\w+|her\s+\w+|their\s+\w+)"
               r"(?:'re|re|\s+are|\s+am|\s+is)?\s+(?:now\s+)?having\s+"
               r"(?:a\s+|our\s+)?(?:little\s+)?(?:boy|girl|twins)\b"
               r"(?!\s+(?:over|round|to\s+stay|for\s+(?:dinner|lunch|tea|supper|christmas)))",
               re.I),
    # A due date needs both halves: the baby, or the person carrying it, and a date. A person
    # alone is not news - "im due a refund", "im due back at work on monday", "im due at the
    # dentist" are money and a diary - and a date alone is not news either ("its due in
    # november": the car's service, the MOT, a rent review, a parcel).
    re.compile(_WHO_DUE + _A_DATE, re.I),
    re.compile(_PERSON_DUE + r"(?:'s|s'|s)?\s+(?:is\s+|are\s+)?due\b" + _WHEN_DUE + _A_DATE,
               re.I),
    # "my due date is in june": the date named as a date.
    re.compile(r"\b(?:my|her|his|their|the)\s+due date\b"
               r"(?:\s+(?:is|was))?" + _WHEN_DUE + _A_DATE, re.I),
)

# A pass, and only when the line says what was passed. "passed" is the same verb with an object -
# "i passed the salt", "i passed him the ball", "i passed the deadline" - and none of those is
# news; "i passed out" is the other meaning, which `badnews.py` reads. Kept apart from the rest so
# a reader that only cares about results (chat's news) can ask just this one.
# What a result is marked with: a class of degree or a grade of a course award.
_A_CLASS = (r"(?:first|2[:. ]?1|2[:. ]?2|1st|2nd|upper\s+second|third|distinction|merit)")
# Whose result it is. Somebody else's class or set of grades is the acknowledgement's, which says
# the grade back - "Your son got a 2:1 in his degree. That's worth a bit of a fuss." - and that
# names the thing where a congratulation names nothing, so the congrats is the speaker's own.
_MY_OWN = r"\b(?:i|we)\b[^.!?]{0,30}?"
# How many grades: "3 a stars", "three a stars".
_A_COUNT = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
# The words that make a class a class: something with grades at the end of it.
_A_COURSE = (r"(?:degree|degrees|honours|graduat\w+|classification|results?|finals|dissertation|"
             r"thesis|course|uni|university|masters?|phd|doctorate|btec|diploma|hnd|"
             r"a\s+levels?|gcses?|qualification|exams?)")

PASSED = (
    re.compile(r"\bpassed\b(?:\s+\w+){0,3}?\s+(?:test|exams?|course|interview|boards?|"
               r"driving|theory|assessment|audition|viva|dissertation|grade|gcses?|a level|"
               r"finals|mocks?|check|inspection|audit|probation|review)\b", re.I),
    # "i passed it" is a result, "i passed it to him" is a hand-over.
    re.compile(r"\bpassed\s+(?:it\b(?!\s+(?:to|on|up|over|round|around|back)\b)|with\b|"
               r"first time|everything|all of)", re.I),
    re.compile(r"\b(?:i|we) (?:just |finally )?passed\b(?=$|[.!]| (?:now|today|yay|at last)\b)",
               re.I),
    re.compile(r"\bwe passed (?:the |an? )?\w+", re.I),
)

# An achievement: something they or theirs went out and got.
WIN = (
    re.compile(r"\bgot\s+(?:the|a|my|her|his|our|their)\s+(?:job|role|keys|offer)\b"
               r"(?!\s+(?:interview|application|centre|center))", re.I),
    re.compile(r"\bgot\s+into\b(?:\s+\w+){0,4}?\s+(?:uni|university|college|school|course|"
               r"team|squad|finals?|semis|shortlist|first choice|apprenticeship|placement|"
               r"nursing|med school|medical school|the show|the exhibition|the choir)\b", re.I),
    re.compile(r"\b(?:got|getting|had)\s+(?:a|the|my|her|his)\s+(?:promotion|pay rise|payrise|"
               r"raise|new job)\b", re.I),
    re.compile(r"\bpromoted\b", re.I),
    # A thing of theirs that was approved or granted: "my leave got approved", "my visa was
    # approved", "my mortgage has been approved", "i got sanctioned leave approved". Nothing read
    # these as news, so the day pool's "How was it, overall?" answered them. The thing has to be
    # theirs - "the invoice was approved at work" is a task finished, not a person's news - and
    # only an approval is here: a shift that is confirmed is not news, and an offer that is
    # accepted is already read above.
    re.compile(r"\b(?:my|our|his|her|their)\s+(?:\w+\s+){0,2}?"
               r"(?:got|was|were|has\s+been|have\s+been|had\s+been|been)\s+"
               r"(?:approved|granted)\b", re.I),
    re.compile(r"\b(?:i|we)\s+(?:just\s+|finally\s+)?got\s+(?:\w+\s+){0,3}?"
               r"(?:approved|granted)\b", re.I),
    re.compile(r"\b(?:won|win|wins)\s+(?:\w+\s+){0,3}?(?:cup|medal|prize|award|race|match|"
               r"competition|league|final|round|gold|silver|bronze)\b", re.I),
    re.compile(r"\bcame\s+(?:first|top|second)\b", re.I),
    # A thing that was waiting on somebody else's yes and got one. "my leave got approved" was
    # answered "How was it, overall?" and "my husband got his leave approved" with a condolence -
    # the leaving reader's word for "leave" - so the approval is news here. The verb is the
    # approval, and what is approved is a thing a person asks for: a leave request, a visa, an
    # application, an offer, a mortgage, a transfer, planning permission.
    re.compile(r"\b(?:my|our|his|her|their)\s+(?:\w+\s+){0,2}?"
               r"(?:leave|holiday|time\s+off|visa|application|offer|mortgage|transfer|grant|"
               r"funding|booking|planning\s+permission|request)\b[^.!?]{0,24}"
               r"\b(?:got|was|were|is|been|just|now|finally)\s+(?:\w+\s+){0,2}?"
               r"(?:approved|accepted|granted|signed\s+off|came\s+through|went\s+through)\b",
               re.I),
    re.compile(r"\b(?:my|our|his|her|their)\s+(?:\w+\s+){0,2}?"
               r"(?:leave|visa|application|offer|mortgage|transfer|grant|funding|booking)\b"
               r"[^.!?]{0,24}\b(?:came\s+through|went\s+through|signed\s+off)\b", re.I),
    # The same news with the participle straight after the thing, which is how it is said when
    # somebody else asked: "my husband got his leave approved" - and that line was answered with
    # the pool for being left, because "leave" is also the verb.
    re.compile(r"\b(?:my|our|his|her|their)\s+(?:\w+\s+){0,2}?"
               r"(?:leave|visa|application|offer|mortgage|transfer|grant|funding|booking|"
               r"request|day\s+off|time\s+off)\s+"
               r"(?:(?:got|was|were|is|been|now|just|finally|all)\s+){0,2}"
               r"(?:approved|accepted|granted|signed\s+off)\b", re.I),
    re.compile(r"\bgraduated\b", re.I),
    # A degree class or a set of top grades is a result said as the thing itself: "i got a 2:1 in my
    # degree" got "Sounds alright. Anything good in it?", "i got 3 a stars" the same shrug, and only
    # the verb "graduated" was read. The class word is not enough on its own - "i got my first
    # payslip at my new job" is a first payslip - so the line also has to be about a course, or say
    # "a 2:1" as the thing got, and never a share of something ("a third of the way").
    re.compile(_MY_OWN + r"(?:got|gotten|achieved|came\s+away\s+with|graduated\s+with|"
               r"finished\s+with)\s+(?:a\s+|an\s+|my\s+|our\s+)?"
               + _A_CLASS + r"(?!\s+of\b)(?=[^.!?]{0,60}?\b" + _A_COURSE + r"\b)", re.I),
    re.compile(_MY_OWN + r"(?:got|gotten|achieved)\s+(?:a|an)\s+" + _A_CLASS +
               r"(?!\s+of\b)(?=\s*(?:[.!?]|$|,|\s+(?:in|for|overall|class)\b))", re.I),
    # The same for the grades themselves, said as a count or with the star. A star wars set is not
    # a grade.
    re.compile(_MY_OWN + r"(?:got|gotten|achieved|came\s+away\s+with|ended\s+up\s+with)\s+"
               r"(?:a\s+|an\s+|my\s+|our\s+|" + _A_COUNT + r")?"
               r"(?:a[\s*-]?stars?\b(?![\s-]*(?:wars|trek|gazer|"
               r"gazing|sign|bucks|fish|city|chart))|(?:all|straight)\s+(?:9s|8s)\b)", re.I),
    # An engagement, said by the pair of you ("we got engaged"), by one of you ("i'm engaged",
    # "she's engaged") or as the ask itself ("he proposed", "she proposed to me"). The fold takes
    # the apostrophe out, so "were engaged" is the same two words as "we're engaged" and both are
    # read here: the unapostrophised spelling is what a chat mostly types, and it reached the
    # fallback's "I'm listening - say more if it helps." The subject in front has to be a person,
    # because "the line was engaged" is a telephone and "i'm engaged in a project" is an
    # afternoon's work, and neither is news to congratulate anyone on.
    re.compile(r"\b(?:got|gotten|now)\s+engaged\b"
               r"|\b(?:i'm|im|i\s+am|we're|were|we\s+are|weve|we've|she's|shes|she\s+is|he's|"
               r"hes|he\s+is)\s+(?:now\s+|just\s+|finally\s+)?engaged\b"
               r"(?!\s+(?:in|on|with|to\s+(?:a|an|the|some)\s+\w))", re.I),
    re.compile(r"\b(?:he|she)\s+(?:only\s+|just\s+|finally\s+|only\s+went\s+and\s+)?"
               r"proposed\b(?=\s*(?:[.!]|,|$|\bto\s+me\b|\byesterday\b|\blast\b|\bat\b|"
               r"\bon\b|\band\b|\bso\b|\bnow\b|\btoday\b))", re.I),
    re.compile(r"\b(?:moving|moved|move)\s+in\s+together\b", re.I),
    re.compile(r"\b(?:had|got|have|having)\s+(?:an?\s+|our\s+|the\s+|my\s+|their\s+)?"
               r"offer\s+accepted\b"
               r"|\boffer\s+(?:got|was|is|has\s+been|have\s+been)\s+accepted\b", re.I),
    # A job that has been offered, which is the same win as a job got and was filed as the intake
    # form ("Thanks for telling me - I'm here if you want to dig into any of that"). Said either
    # way round, because "ive been offered the job" and "they offered me the job" are one event.
    re.compile(r"\b(?:been|being|was|were|got)\s+(?:just\s+)?offered\s+(?:the|a|my|this)\s+"
               r"(?:job|role|position|place|post)\b", re.I),
    re.compile(r"\b(?:they|he|she|the\s+\w+)\s+offered\s+me\s+(?:the|a)\s+"
               r"(?:job|role|position|post)\b", re.I),
    # A course finished is a course passed: "graduated" is read and "finished my degree" was not,
    # so the second one was filed as a fact. The object decides it - a dinner is finished every
    # night and nobody is congratulated for that.
    re.compile(r"\bfinished\s+(?:my|the|our)\s+(?:degree|course|exams?|dissertation|thesis|"
               r"apprenticeship|training|masters?|phd|nursing|gcses?|a\s+levels?)\b", re.I),
    # A new member of the family on the way: "i'm going to be a grandma", "we're going to be
    # grandparents", "she's going to be an auntie". Not the birth (that is `BABY`) and not the
    # pregnancy, but the news that there is going to be one, which was a shrug.
    re.compile(r"\b(?:going|gonna)\s+to\s+be\s+(?:(?:a|an)\s+(?:grandma|grandmother|nan|nana|"
               r"granny|gran|grandad|grandfather|grandpa|auntie|aunty|uncle)\b|grandparents\b)",
               re.I),
    re.compile(r"\b(?:bought|got)\s+(?:a|our own|our first)\s+(?:house|flat|place)\b", re.I),
    re.compile(r"\b(?:got|signed)\s+the\s+keys\b|\bcompletion\s+(?:date|day)\b", re.I),
    re.compile(r"\b(?:all clear|got the all clear|out of hospital|rang the bell)\b", re.I),
    # The news a family waits on that is not a birth: a child on the way through adoption, a
    # cheque that arrives, a book that comes out. None of them had a shape, so all three got the
    # intake form. "The book was published in 1998" is a fact about a book, so the possessive is
    # the part that makes it somebody's own news.
    re.compile(r"\b(?:we're|we are|were|we've\s+started|we\s+have\s+started)\s+"
               r"(?:in\s+the\s+middle\s+of\s+)?adopting\b"
               r"(?![^.!?]*\b(?:policy|policies|approach|stance|attitude|method|tactic)\b)"
               r"|\b(?:the\s+)?adoption\s+(?:went\s+through|is\s+going\s+through)\b"
               r"|\b(?:started|starting|began)\s+(?:the|an|our)\s+adoption\b", re.I),
    re.compile(r"\b(?:came|come)\s+(?:in\s*to|into)\s+(?:some\s+|a\s+bit\s+of\s+|a\s+little\s+)?"
               r"(?:money|an\s+inheritance|cash)\b", re.I),
    re.compile(r"\b(?:my|our)\s+(?:book|novel)\s+"
               r"(?:got|was|is|has\s+been|have\s+been)\s+published\b", re.I),
)

# Praise that arrives in somebody else's words: "my boss said im doing a good job", "my sons
# teacher said hes doing well", "my manager said shes pleased with me", "my friend said i look
# well". Nothing was got and nothing was won, so `WIN` above does not read them, and the pools
# answer a person's good news with the stock nod ("Thanks for telling me - I'm here if you want to
# dig into any of that") or with the receipt ("Noted: the vet says the cat is fine"). What makes
# the line news is that somebody with a view on it said something warm, so the speech verb is part
# of the shape: "my teacher said i could do better" and "the doctor said i need an operation" are
# not read here.
_SAID = (r"(?:said|says|saying|told\s+me|tells\s+me|texted|texts|wrote|emailed|emails|"
         r"rang|phoned|reckons|thinks)")
_PRAISING = (r"(?:doing\s+(?:really\s+|very\s+)?well|done\s+(?:really\s+|very\s+)?well|"
             r"did\s+(?:really\s+|very\s+)?well|doing\s+(?:really\s+|very\s+)?great|"
             r"did\s+great|a\s+(?:really\s+|very\s+)?(?:good|great|smashing)\s+job|"
             r"(?:really\s+|very\s+)?(?:proud|pleased|impressed)\s+(?:of|with)\s+"
             r"(?:me|us|him|her|them)|well\s+done|star\s+of\s+the\s+week|"
             r"top\s+of\s+the\s+class)")
# An award a person's own brought home, which is praise with a name on it.
# "distinction" is left out on purpose: the pools already name it ("my daughter got a
# distinction in her piano exam" answers with the word), and a cheer in its place loses it.
_AWARD = (r"(?:merit|gold\s+star|star\s+of\s+the\s+week|"
          r"head\s+teachers?\s+award|player\s+of\s+the\s+match)")
# The praise has to be coming in, so a line where the person is the one handing it out ("i said
# well done to my son", "i told her she did well") is not news about them.
_I_PRAISED = re.compile(r"\b(?:i|we)\s+(?:said|say|says|told|tell|tells|texted|wrote|emailed)\b",
                        re.I)
PRAISED = (
    re.compile(r"\b" + _SAID + r"\b(?:\s+\w+){0,5}?\s+" + _PRAISING + r"\b", re.I),
    re.compile(r"\b(?:got|came\s+home\s+with|won|awarded)\s+(?:(?:a|an|the)\s+)?"
               + _AWARD + r"\b", re.I),
)

GOOD = BABY + PASSED + WIN + PRAISED

# A thing that has arrived: a new animal, a new kitchen, a new place. "we got a rescue greyhound
# last month", "we're getting a new kitchen put in", "we moved house last month" are news with a
# thing in them the person wants to talk about, and the stock nod ("Got it. Is there anything
# you'd like a hand with?") answers them as if nothing had been said. The congrats pool is no
# good either - "Good for you! That sounds like it was worth the wait" congratulates a sofa - so
# the arrival keeps its own question, and the question is about the thing.
# "i've got two cats" is possession, not an arrival: the person has them and always did, and the
# echo back ("Noted: you've got two cats, Milo and Otis") is the reply that thread wants, with the
# names in it. An arrival is past tense or marked as new - "we got a greyhound", "i've just got a
# puppy", "i finally got my bike".
ARRIVED = (
    re.compile(r"\b(?:we|i)(?:\s+(?:just|finally|only))?\s+(?:got|gotten|adopted|rescued|"
               r"rehomed|picked up|bought|chose)\s+"
               r"(?:a|an|our|my|his|her|their|another|two|some|"
               r"one|a few|a couple|a pair|three|four|five|six)\s+"
               r"(?P<thing>[a-z][a-z' ]{1,30})", re.I),
    re.compile(r"\b(?:we|i)(?:'ve|ve)\s+(?:just|finally|only)\s+(?:got|gotten|adopted|"
               r"rescued|rehomed|picked up|bought|chose)\s+"
               r"(?:a|an|our|my|his|her|their|another|two|some|"
               r"one|a few|a couple|a pair|three|four|five|six)\s+"
               r"(?P<thing>[a-z][a-z' ]{1,30})", re.I),
    re.compile(r"\b(?:we|i)\s*(?:'re|re|are)?\s+(?:getting|having)\s+"
               r"(?:a|an|our|another)\s+(?P<thing>[a-z][a-z' ]{1,30}?)\s+"
               r"(?:put in|fitted|installed|done|built|delivered)\b", re.I),
)
# "i have got a new car", "we've got a new sofa", "ive got a new laptop": British speech uses the
# present form of "got" for what a person owns, so on its own it says nothing about when the
# thing came - "we have got a cat" is a cat they have had for years, and "how are they settling
# in" invents an arrival. With a word in the line that makes it news the same words say what "i
# got a new car" says, so they are read as those words and the arrival patterns below do the rest.
HAVE_GOT = re.compile(r"\b(?P<who>we|i)(?:\s+(?:have|has|had)|'ve|ve)\s+got\b", re.I)
NEWS_OF_IT = re.compile(r"\b(?:new|brand[- ]new|another|just|finally|only|now)\b", re.I)

# The arrival of a place, said without a thing: "we moved house last month", "we've just moved
# in". The question for these is about the new place, not about a thing in it.
MOVED_IN = re.compile(r"\b(?:we|i)(?:'ve|ve)?\s+(?:just\s+|finally\s+|now\s+)?(?:moved|"
                      r"moving)\s+(?:house|flat|home|in|into)\b", re.I)

# What makes a thing an animal, a thing being built, or just a thing. Kept as plain sets: the
# kind only picks which question to ask, and a wrong kind still asks a question about the thing.
ANIMAL_THING = frozenset("""
    dog puppy pup cat kitten greyhound lurcher whippet terrier spaniel retriever labrador
    collie poodle rabbit bunny bunnies hamster gerbil guinea pig rat mice mouse horse pony
    donkey parrot budgie cockatiel bird chicken chickens hen hens duck ducks fish goldfish
    tortoise snake lizard ferret chinchilla koi
""".split())
# Work being done on the house, which is a job with a "how far along is it" to it. A sofa or a
# fridge that arrived is a thing, not a job: "how far along is the new sofa" is nonsense.
HOME_WORK = frozenset("""
    kitchen bathroom extension loft garden shed decking conservatory roof windows drive
    driveway fence flooring tiles tiling wallpaper fireplace plastering rewiring insulation
""".split())
HOME_THING = HOME_WORK | frozenset("""
    boiler carpet carpets sofa bed fridge freezer oven cooker hob washer washing machine
    dishwasher door doors window
""".split())
# The things a person has and can use, which is what "what's it like" is a question about. A
# person, an event and an arrangement are none of those: "we got a baby boy" is a baby (the
# congrats pool's line), "i got my exam results" is an event, "we got a cleaner" is somebody
# who now works there, and "i got a mortgage" is an arrangement. So the arrival speaks only when
# the thing that arrived is one of these, an animal, or part of the house - the closed-set rule
# keeps it off the lines it would be wrong on, which is what the other composer readers do too.
OBJECT_THING = frozenset("""
    bike bicycle trike motorbike scooter car van caravan camper moped boat kayak canoe
    phone iphone mobile tablet ipad laptop computer pc desktop macbook monitor keyboard
    printer camera headphone headphones speaker speakers radio tv television kindle watch
    guitar piano violin drums ukulele keyboard sofa couch armchair chair table desk bed
    mattress wardrobe cupboard drawers bookcase shelf shelves rug lamp light curtains
    blinds mirror picture painting fridge freezer kettle toaster microwave oven cooker hob
    dishwasher washer washing machine dryer vacuum hoover iron blender airfryer
    coat jacket dress skirt trousers jeans shirt dress suit shoes boots trainers sandals
    hat cap scarf gloves bag handbag rucksack suitcase pram pushchair buggy cot crib
    toy toys lego doll dolls console playstation xbox switch game games book books
    ring necklace bracelet earring tattoo plant plants tree seeds greenhouse pond
    mower lawnmower bbq barbecue grill tent sleeping bag
""".split())

# A thing that arrived is not always a good thing, and the words are the same: "we got a
# parking ticket", "i got a bill for 400", "we got a fine". Nothing here is congratulated.
NOT_AN_ARRIVAL = frozenset("""
    ticket fine bill bills letter letters cold cough bug virus parking quote estimate
    refund diagnosis invoice debt summons notice warning complaint infection
    job role promotion offer keys tenancy
""".split())
# Where a thing's name stops: "we got a rescue greyhound last month" names a rescue greyhound,
# and "last month" is when, not what. Also the conjunctions, so "a puppy and a kitten" asks
# about the puppy.
THING_STOPS = frozenset("""
    for from in on at with by to of last next this yesterday today tomorrow and but so because
    that which who when while if then than as about after before over under into onto
    fitted installed delivered built done put made changed fixed coming arriving called
    named
""".split())
# "i moved into a new flat and theres no hot water" arrives with a fault in it, and a question
# about the new place answers the move and ignores the fault. The trouble pools read that line.
# The fault does not have to be said as a fault: "i bought a new car and it's a nightmare",
# "i got a new bike for my son and he hates it", "i got a new car and crashed it" arrive with a
# complaint in the second half of the line, and a cheer for the thing answers the half that is
# not the news. The trouble pools read those lines.
FAULT = re.compile(r"\b(?:no|not|isnt|isn't|wont|won't|doesnt|doesn't|dont|don't|broken|"
                   r"leaking|leak|damaged|fault|faulty|problem|issues?|wrong|blocked|"
                   r"flooded|stuck|cracked|smell|smells|nightmare|hated|hates?|regret\w*|"
                   r"disappoint\w*|rip[- ]off|useless|rubbish|waste of|went wrong|fell apart|"
                   r"dead on arrival|crash\w*|dud|lemon)\b", re.I)
NEW_ANIMAL = (
    "A {thing} — how are they settling in?",
    "Lovely. What's the {thing} like so far?",
    "How's the {thing} getting on?",
)
NEW_HOME = (
    "A {thing} is a proper job — how far along is it?",
    "How's the {thing} coming along?",
    "Good news. What's the part of the {thing} you're dreading?",
)
NEW_PLACE = (
    "How's the new place?",
    "What's the best thing about the new place so far?",
    "How's it feeling, being somewhere new?",
)
NEW_THING = (
    "Tell me about the {thing} — what's it like?",
    "Nice. What made you go for the {thing}?",
    "How are you finding the {thing}?",
)


# A count in front of the thing is not part of its name: "we got one of those baby monitors" is a
# monitor that arrived, and reading the name from "of" stopped at the first word and left nothing
# that named a thing, so the arrival was never answered at all. The count is in ARRIVED so the
# pattern can match, and the pointer behind it is dropped here so the name starts at the thing.
A_POINTER_IN_FRONT = re.compile(r"^of\s+(?:those|these|them|the|my|our|his|her|their)\s+", re.I)


def _bare(word):
    """The word without a plural ending, so "two puppies" names a puppy.

    The thing lists are all written in the singular, and a line about two of something says the
    plural - "we got two crates", "one of those baby monitors" - so a plural was never read as a
    thing that arrived, and the news got a receipt instead of a question about it.
    """
    if len(word) > 3 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("es") and word[-3] in "sxz":
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _thing_words(match):
    """The thing that arrived, cut at the first word that is not part of its name."""
    kept = []
    said = A_POINTER_IN_FRONT.sub("", match.group("thing") or "")
    for word in said.split():
        bare = word.strip(".,!?;:\"'")
        if not bare or bare in THING_STOPS or bare in NOT_AN_ARRIVAL or len(kept) == 3:
            break
        kept.append(bare)
    return " ".join(kept)


def new_thing(clean):
    """The kind and name of a thing that has just arrived, or None.

    Returns `{"kind": "animal"|"home"|"place"|"thing", "thing": "rescue greyhound"}`, so the
    caller can ask a question about the thing without reading the line again.
    """
    if not clean:
        return None
    if NOT_NEWS.search(clean) or BAD.search(clean) or FAULT.search(clean) \
            or doubted(clean):
        return None
    said = clean
    if HAVE_GOT.search(said) and NEWS_OF_IT.search(said):
        # "i have got a new car" is "i got a new car" said the British way, and the patterns
        # below already read that one. Without a word that makes it news the line is a person
        # saying what they own and it is left to every other reading.
        said = HAVE_GOT.sub(r"\g<who> got", said)
    if MOVED_IN.search(said):
        return {"kind": "place", "thing": ""}
    for pattern in ARRIVED:
        match = pattern.search(said)
        if not match:
            continue
        thing = _thing_words(match)
        if not thing or thing in ("new", "another", "first", "second"):
            continue
        # Both the word as said and its bare form, because the lists are mostly singular
        # ("kettle") and a few name the plural itself ("trousers", "shoes", "jeans").
        words = set(thing.split())
        words |= {_bare(word) for word in words}
        if words & NOT_AN_ARRIVAL:
            continue
        # Only an animal, a job on the house, or an object the person now has can be asked
        # "what's it like": everything else that arrives - a baby, a boss, a cleaner, exam
        # results, a text, a mortgage, a hair cut - is not a thing, and the question is wrong.
        if not (words & (ANIMAL_THING | HOME_THING | OBJECT_THING)):
            continue
        if words & ANIMAL_THING:
            return {"kind": "animal", "thing": thing}
        if words & HOME_WORK:
            return {"kind": "home", "thing": thing}
        if words & HOME_THING:
            return {"kind": "thing", "thing": thing}
        return {"kind": "thing", "thing": thing}
    return None


def new_thing_replies(arrived):
    """The lines an arrival is answered with, the thing's name said back once."""
    kind = arrived.get("kind")
    thing = arrived.get("thing") or ""
    if kind == "place":
        return NEW_PLACE
    pool = {"animal": NEW_ANIMAL, "home": NEW_HOME}.get(kind, NEW_THING)
    return tuple(line.format(thing=thing) for line in pool)


# An occasion coming up: a birthday, an anniversary, a wedding. Every word of it is plain, so
# `POSITIVE_CUES` never notices, and the line fell through to the neutral pool - "Noted: you're
# getting married next year" is a filing cabinet, not a friend, and "its my birthday on friday"
# got "Thanks for telling me - I'm here if you want to dig into any of that". The occasion decides
# the greeting (you wish somebody a happy birthday, you do not congratulate them on it), so this
# names the occasion and the composer picks the words for it.
# An occasion said with the number instead of the word: "my mums 70th is in march", "my 40th is
# next week". The line never says "birthday", so the words above miss it and the day was filed as
# a fact ("Noted: your mums 70th is in march"). The number needs a time after it or to end the
# line - "my 2nd week at the gym is going well" is a length of time, not a day - and only my/our,
# so "the 70th" and somebody else's number are left alone.
ORDINAL_DAY = re.compile(
    r"\b(?:my|our)\s+(?:(?P<whose>[\w'-]+)\s+)?(?P<day>\d+(?:st|nd|rd|th))\b"
    r"(?:\s*,?\s*(?:is|was|are)?\s*(?:in|on|next|this|tomorrow|tonight|soon|coming|"
    r"at\s+the\s+end|early|late|this\s+weekend|the\s+weekend)\b|[\s.!]*$)", re.I)

OCCASION = (
    # A possessive noun between the owner and the day is the same news: "its my sons birthday on
    # saturday" is still a birthday coming up. Only after my/our, so the guard on somebody else's
    # day ("its her birthday tomorrow") still holds.
    ("birthday", re.compile(r"\b(?:its|it's|it is)\s+(?:\d+(?:st|nd|rd|th)\s+)?birthday\b"
                            r"|\b(?:my|our)\s+(?:[\w'-]+\s+)?(?:\d+(?:st|nd|rd|th)\s+)?"
                            r"birthday\b", re.I)),
    ("anniversary", re.compile(r"\b(?:its|it's|it is|my|our)\s+(?:\d+(?:st|nd|rd|th)\s+)?"
                               r"(?:\w+\s+)?anniversary\b", re.I)),
    # A wedding needs the person in it: "the wedding is in june" is as often one they are going
    # to as one they are having, so the couple has to be named for it to be their news.
    ("wedding", re.compile(r"\b(?:im|i'm|i am|we're|we are|we re)\s+(?:getting\s+)?married\b"
                           r"|\b(?:my|our)\s+wedding\b", re.I)),
    # A wish said on its own, with nobody named in it: "happy birthday" typed to the bot, or a
    # card line somebody is trying out. The person may be the one being wished or the one doing
    # the wishing and only they know which, so the greeting is read but the reply asks. A name or
    # anything else after it is a different line ("happy birthday mum" is a card message).
    ("wish", re.compile(r"^(?:a\s+|very\s+|so\s+|aw+\s+|oh\s+|many\s+)*"
                         r"(?:happy\s+(?:birthday|bday|b-day)|many\s+happy\s+returns)"
                         r"\s*[\s!.,]*$", re.I)),
)

# Four ways a line mentions an occasion without it being the person's own news: asked of the bot
# ("when is your birthday"), a date to be looked up or a present to buy ("what should i get my mum
# for her birthday" - the answers lane owns that), a day that has already gone ("my birthday was
# rubbish") and a day that never happened ("it would have been her birthday", which is grief and
# is read by the composer's milestone pool). A question is a question: the ask is the turn.
NOT_AN_OCCASION = re.compile(
    r"\byou\b|\byour\b"
    r"|\bwould(?:'ve| have|ve)?\s+been\b"
    r"|\b(?:what|which|when|whens|when's|how|where)\b"
    r"|\b(?:present|presents|gift|gifts|idea|ideas|nothing|need|needs)\b"
    r"|\b(?:was|were)\b", re.I)

# An occasion somebody let them down over is a complaint, not news: "my boyfriend forgot our
# anniversary" is a grievance and wants a word about him, so the wish has no place in it. The same
# goes for an occasion that has arrive with a worry attached ("im getting married next year and im
# worried about the money"): the feeling is the turn.
# "our anniversary is on the day she left" is the same shape as "the day he walked out": the
# person in the line has gone, so the day is a wound and not a day to wish them well for. The
# pronoun is the guard, because "left" alone is time remaining ("not much time left") and a
# birthday with three weeks left is still a birthday.
SOMEONE_LEFT = re.compile(
    r"\b(?:he|she|they)\s*(?:'s|'d|s|d)?\s+(?:has\s+|had\s+|just\s+|then\s+|already\s+)?"
    r"(?:left|leaves|leaving|walked\s+out|walking\s+out|moved\s+out|dumped|split\s+up)\b",
    re.I)

LET_DOWN = re.compile(r"\b(?:forgot|forgets|forgetting|forgotten|fell\s+apart|"
                      r"cancell?ed|ruined|messed|mucked|hate|"
                      r"wrong|disaster|horrible|"
                      r"nobody|no\s?body|no\s?one|none\s+of\s+them|"
                      r"annoyed|annoying|upset|arguing|argued|row|fight|fighting|didn't|didnt|"
                      r"did not|won't|wont|worried|worry|scared|terrified|dreading|stressed|"
                      r"anxious)\b", re.I)


# "its my sons birthday on saturday" is a birthday the person is going to, not one they are having.
# Who the day belongs to is the one thing that changes the wording - a greeting said to the person
# typing when the day is their son's greets the wrong person - so the reader says it and the pool
# decides. The test is a relation in front of the day, because that is the only thing that puts the
# day in somebody else's life: "my 30th birthday" is still theirs, and so is "my big birthday".
RELATION_BEFORE_DAY = re.compile(
    r"\b(?:my|our)\s+(?:(?P<whose>[\w'-]+(?:\s+[\w'-]+)?)\s+)?"
    r"(?:\d+(?:st|nd|rd|th)\s+)?(?:birthday|anniversary)\b", re.I)
FAMILY = frozenset((
    "son", "daughter", "kid", "child", "baby", "twins", "girl", "boy", "lad", "teenager",
    "wife", "husband", "partner", "boyfriend", "girlfriend", "ex", "fiance", "fiancee",
    "mum", "mom", "mother", "dad", "father", "parent", "parents", "stepmum", "stepdad",
    "stepson", "stepdaughter", "sister", "brother", "sibling", "sisterinlaw", "brotherinlaw",
    "motherinlaw", "fatherinlaw", "aunt", "uncle", "cousin", "niece", "nephew", "grandchild",
    "gran", "granny", "nan", "nana", "grandma", "grandad", "grandpa", "grandparent",
    "friend", "mate", "boss", "colleague", "coworker", "neighbour", "neighbor", "flatmate",
    "housemate", "landlord", "carer", "client", "student", "teacher",
))


def _the_person_word(word):
    """The relation word inside a possessive - "mums", "wifes", "son's" - or ""."""
    word = str(word or "").strip().strip("'").lower()
    if word.endswith("s"):
        word = word[:-1]
    return word


def someone_elses_occasion(clean):
    """True when the day named belongs to somebody other than the person writing.

    Only a relation in front of the day makes it somebody else's: "my sons birthday", "my best
    friends anniversary". A day with nothing in front of it is theirs, and so is one described
    rather than owned - "my 30th birthday", "my big birthday"."""
    text = " ".join(str(clean or "").lower().split())
    for found in RELATION_BEFORE_DAY.finditer(text):
        words = (found.group("whose") or "").split()
        if any(_the_person_word(word) in FAMILY for word in words):
            return True
    # "my mums 70th is in march" names the day with the number, so the relation is read the same
    # way here: my/our, then a family word, then the number.
    for found in ORDINAL_DAY.finditer(text):
        if _the_person_word(found.group("whose") or "") in FAMILY:
            return True
    return False


def reads_as_an_occasion(clean):
    """The occasion a line says is coming up - "birthday", "anniversary", "wedding" - or None.

    The name is for the composer to pick the greeting with; this reader only says which occasion
    the line is about, so the wording can change without touching this file."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return None
    if (NOT_AN_OCCASION.search(text) or LET_DOWN.search(text)
            or SOMEONE_LEFT.search(text)
            or doubted(text) or BAD.search(text)):
        return None
    for name, pattern in OCCASION:
        if pattern.search(text):
            return name
    if ORDINAL_DAY.search(text):
        return "birthday"
    return None

# A question is a question, and bad news is `badnews.py`'s: "we lost the baby" must never be
# congratulated, and neither must "did you win" or "i hope i passed".
NOT_NEWS = re.compile(r"\b(?:did|do|does|will|would|are|is|was|were|can|could|shall|should|have|"
                      r"has)\s+(?:i|you|we|she|he|they)\b"
                      # A hope is not a result: "i hope i passed", "fingers crossed i pass".
                      r"|\b(?:hope|hoping|wish|wishing|wonder|wondering|praying|"
                      r"fingers crossed|fingers are crossed)\b", re.I)
# A nearly-done thing is not done: "i nearly passed my driving test" is not a pass, and "i almost
# won" is not a win. One word list for the whole composer, and read here as the guard it is rather
# than as a bad thing - "i almost gave up, but i finished it" is still a win.
NOT_QUITE = re.compile(r"\b(?:" + "|".join(sorted(NEARLY)) + r")\b", re.I)

# A win with the opposite said straight after it is not a win: "we came into some money and now
# everyone wants it", "we're moving in together and my mum hates him". `but` and `except` are in
# BAD below; this is the `and` that turns the same way, because the second clause is the sentence's
# news and a congratulations on top of it is deaf to it. The `and` has to carry the hostility
# itself - "we're moving in together and i cant wait" is still a win.
A_TURN_IN_THE_TALE = re.compile(
    r"\band\s+now\s+(?:every\w+|nobody|no\s+one|no-one|they|he|she)\b"
    r"|\band\s+[^.!?]{0,40}\b(?:hates?|hate\b|disapproves?|refuses?|won'?t|wont|"
    r"doesn'?t\s+(?:like|approve|want)|doesnt\s+(?:like|approve|want)|is\s+against|"
    r"objects?)\b", re.I)

# The same turn in the tale, told about a thing rather than a person: "we finally got the keys and
# the place is a state", "we came into some money and now the boiler has packed in". The second
# clause here is the cost, and it is the sentence's news. The words are the ones that name a
# setback and nothing else - "and now we can fix the roof" and "and now we have two cats" are the
# happy endings the win reader is there for.
A_SETBACK_AFTER_THE_WIN = re.compile(
    r"\band\s+(?:then\s+|now\s+)?[^.!?]{0,60}\b(?:broke|broken|breaks|packed\s+in|"
    r"stopped\s+working|gone\s+wrong|went\s+wrong|on\s+the\s+blink|is\s+a\s+(?:state|mess|tip)|"
    r"ruined|leaking|leaks?\b|flooded|cracked|worse|awful|terrible|horrible|nightmare|"
    r"regrets?|cant\s+afford|cant\s+cope|i\s+cant\s+do\b|just\s+my\s+luck|"
    r"died|dead)\b", re.I)


# The other half of a win, said after the `and`: "and now we can fix the roof", "and we can
# finally get the kitchen done". These are the endings a win reader is there for, so they are not
# a cost even when the same line carries a setback word somewhere before them.
A_GOOD_ENDING = re.compile(
    r"\band\s+(?:now\s+|at\s+last\s+)?(?:we|i)\s+(?:can|could|get\s+to|are\s+able)\b"
    r"|\band\s+(?:now\s+)?(?:that\s+means\s+)?"r"(?:we|i)\s+can\b", re.I)

BAD = re.compile(r"\b(?:lost|miscarried|miscarriage|died|death|stillborn|failed|failing|"
                 r"not going|didn't|didnt|did not|haven't|havent|hasn't|hasnt|not yet|"
                 r"never|gave up|turned down|rejected|"
                 r"but|except|however|fight|fights|trouble|accident|argument|row|debt|"
                 r"hospital|intensive care|poorly|poorly|not well)\b", re.I)


# Getting better. "i feel better today" is news and the news is good, but it is not an exam
# result: it wants relief said back, not congratulations. So it is its own family, and
# `reads_as_recovery` is what the composer asks about it.
# The few words between a symptom and what it did ("the pain in my side has gone") are nothing but
# words, unless one of them says no. "the pain has not gone away" is the report that nothing has
# worked, and the same pattern read it as the pain going: "the pain has not gone away" was answered
# with the relief pool, "Glad to hear it - that's the news you want", which is the worst line in the
# composer to hear when you have just said the thing is no better. So a negation anywhere in the
# gap stops the match - the reader leaves the line to the pools that answer a report.
A_GAP_WITHOUT_A_NO = (r"(?:(?!\b(?:not|no|never|hardly|barely|without|nothing|none)\b)"
                      r"[^.!?])")

RECOVERY = (
    re.compile(r"\b(?:feel|feeling|felt)\s+(?:a\s+(?:bit|lot|whole\s+lot)\s+|much\s+|so\s+much\s+|"
               r"loads\s+|really\s+|a\s+lot\s+)?better\b", re.I),
    re.compile(r"\b(?:im|i'm|i\s+am)\s+(?:much\s+|a\s+lot\s+|so\s+much\s+|loads\s+)?better\b"
               r"(?!\s+at\b)", re.I),
    re.compile(r"\b(?:pain|headache|migraine|cough|cold|sickness|nausea|rash|swelling|soreness|"
               r"knee|back|shoulder|ankle|wrist|hip|neck|throat|stomach|ear|tooth|chest)\b"
               + A_GAP_WITHOUT_A_NO + r"{0,8}?\b(?:is|are|feels?)\s+(?:much\s+|a\s+lot\s+|"
               r"so\s+much\s+|loads\s+)?better\b", re.I),
    # "i feel better than yesterday" is news. It needs the reference to be a time the person
    # came through, because "my english is better than my french" and "my phone is better than
    # yours" are comparisons: the same words, and no one is getting well in either of them.
    re.compile(r"\bbetter\s+than\s+(?:yesterday|this\s+morning|last\s+(?:night|week|month)|"
               r"before|earlier|it\s+was|i\s+was)\b", re.I),
    re.compile(r"\b(?:pain|headache|migraine|cough|cold|sickness|nausea|temperature|fever|rash|"
               r"swelling|soreness|ache)\b" + A_GAP_WITHOUT_A_NO + r"{0,12}?"
               r"\b(?:has|have|is|are)?\s*(?:all\s+)?"
               r"(?:gone|eased|easing|cleared\s+up|stopped|settled)\b(?!\s+(?:on|to|into|in|down|"
               r"through|round|around|for|up))\b", re.I),
    # "im over it now" is left out on purpose: after "my dad died in march" it is grief, and the
    # rest of this family would answer a bereavement with "take it gently for a day or two".
    re.compile(r"\b(?:(?:over|past|through)\s+the\s+worst|on\s+the\s+mend|back\s+on\s+my\s+"
               r"feet|back\s+to\s+normal)\b", re.I),
    # "im over the flu now" is the news, but "im over it now" is not: after "my dad died in
    # march" the same words are a bereavement being got over, and the relief pool ("take it
    # gently for a day or two") is the wrong thing to say to it. So the illness has to be
    # named, and only an illness that passes is in the list.
    re.compile(r"\b(?:i|we)(?:'m|m|\s+am|\s+are|'re)?\s+(?:finally\s+|just\s+|mostly\s+|"
               r"nearly\s+)?over\s+(?:the|my|that|this)\s+(?:flu|cold|cough|bug|virus|"
               r"infection|chest\s+infection|sickness|norovirus|migraine|sore\s+throat|"
               r"tonsillitis|bronchitis|pneumonia|stomach\s+bug|hangover)\b", re.I),
    re.compile(r"\b(?:got|get|getting)\s+over\s+(?:the|my|that|this)\s+(?:flu|cold|cough|"
               r"bug|virus|infection|sickness|norovirus|migraine|sore\s+throat|tonsillitis|"
               r"bronchitis|pneumonia|stomach\s+bug|hangover)\b", re.I),
    # A body part or a cut that has healed is the recovery read by `SETTLED` too; it is here as
    # well because the person says "my knee has healed" about themselves, which `ABOUT_THEM`
    # reads and the settled family does not.
    re.compile(r"\b(?:it|that|this|my\s+\w+|the\s+\w+|the\s+\w+\s+\w+|wound|cut|burn|"
               r"scar|sore)\s+(?:has|have|is|are|'s|s)?\s*(?:all\s+)?healed\b", re.I),
)

# Said by the person about themselves. Without this, "is it better to walk or run" and
# "which is better, tea or coffee" would read as news.
ABOUT_THEM = re.compile(r"^(?:so|well|ok|okay|and|but|tbh|honestly|ah|oh|right|good)?[\s,]*"
                        r"(?:i|im|i'm|ive|i've|we|we're|weve|we've|my|the|feeling|feel|over|"
                        r"on|back|still)\b", re.I)

# "i feel better when i go for a walk" reports a rule, not this week: the relief is for something
# that has already happened, so a condition after "better" keeps the line out.
CONDITIONAL = re.compile(r"\bbetter\b[^.!?]{0,24}?\b(?:when|whenever|if|unless|as\s+long\s+as)\b",
                         re.I)
# What follows "passed" says whether it was a result or a hand-over: "we passed the salt",
# "i passed it to him", "we passed on the house". The word alone cannot tell, so the words
# after it are read here, once, for every phrasing that mentions a pass.
PASS_PARTICLE = frozenset(("on", "up", "over", "away", "round", "around", "out", "by",
                           "through", "for", "to"))
PASS_TAKEN = frozenset(("salt", "ball", "butter", "plate", "bottle", "note", "message", "book",
                        "pen", "phone", "remote", "keys", "sugar", "jug", "envelope"))


def _a_hand_over(words):
    """True when a "passed" in these words hands something over rather than reports a result."""
    for i, word in enumerate(words):
        if word not in ("passed", "pass"):
            continue
        after = words[i + 1:i + 4]
        if not after:
            continue
        if after[0] in PASS_PARTICLE:
            return True
        thing = after[1] if after[0] in ("the", "a", "an") and len(after) > 1 else after[0]
        if thing in PASS_TAKEN:
            return True
        if after[0] == "it" and len(after) > 1 and after[1] in PASS_PARTICLE:
            return True
    return False


def reads_as_a_pass(clean):
    """Whether the line reports a pass: "i passed my driving test", "i passed".

    A bare "passed" with a thing after it is a hand-over, not a result, and a question is a
    question ("did you pass"), so neither is one."""
    if not clean:
        return False
    if NOT_NEWS.search(clean) or NOT_QUITE.search(clean) or doubted(clean):
        return False
    if reads_as_a_win_nobody_noticed(clean):
        return False  # a pass with a silence round it is answered as both, not as a pass
    words = [w.strip(".,!?;:\"'") for w in clean.split()]
    if _a_hand_over(words):
        return False
    return any(pattern.search(clean) for pattern in PASSED)


# A line that asks for the news is not the news: "got any good news", "any good news", "what's the
# good news", "do you have any news" ask for something to celebrate, and the congrats pool answered
# them ("That's great news! Make the most of it.") as if the person had just told you one. The ask
# is a question word in front of a word for news, so the test is on how the line starts.
NEWS_ASK = re.compile(
    r"^(?:(?:so|ok|okay|well|and|but|oh|right|hi|hey|hello|morning|now|then)\s*,?\s+)*"
    r"(?:got|get|any|anything|whats|what's|what\s+is|what\s+about|how\s+about|"
    r"do\s+you\s+have|have\s+you\s+got|have\s+you|has|have|did|you|u|is\s+there|are\s+there|"
    r"tell\s+me|give\s+me|hear\s+any|heard\s+any|share|spill)\b", re.I)
# "news" or one of the two words that stand in for it. Bare "good" and "nice" are not enough:
# "what's good to watch tonight" and "any good pubs near me" are questions about something else.
NEWS_WORD = re.compile(r"\b(?:news|anything|something)\b", re.I)
# The news of the world, named as the news. Somebody asking what the news is wants a news site,
# not a question back about their week, so a line that names it plainly is not asked here at all:
# it keeps the answer it had ("I can't see the news from here, sorry..."). "the good news" is not
# this - it asks for the news the person has, and that is the nod.
WORLD_NEWS = re.compile(
    r"\b(?:the|todays|today's)\s+(?:(?:latest|current|world|local|national|main|evening|"
    r"morning|morning's)\s+)?news\b|\bnews\s+today\b|\bheadlines?\b|"
    r"\bcurrent events\b|\bwhat happened in the\b", re.I)
# "anything" and "something" stand in for the news only in the shape that asks about a week:
# "did anything good happen", "got anything good", "you heard something good lately". The same
# two words in any other shape ask for a thing - "do you have anything for a sore throat" (a
# remedy), "anything good to watch" (a film), "is there anything good on netflix" - and the nod
# to those is nonsense.
_STANDIN = re.compile(
    r"\b(?:anything|something)\s+(?:good|nice|great|happy|brilliant|lovely|exciting)\b"
    r"(?:\s+(?:has\s+|have\s+)?(?:happen|happened|happens|happening|been\s+happening))?"
    r"(?:\s+(?:today|lately|recently|this\s+week|this\s+weekend|at\s+work|with\s+you|"
    r"for\s+you))*\s*$"
    # "anything happen today" and "did something happen at work" have no adjective in front of
    # the verb and ask the same thing; the bare words without a verb ("do you have anything for a
    # sore throat") still do not, because the asking shape and the day word have to be there.
    r"|\b(?:anything|something)\s+(?:happen|happened|happens|happening)\b"
    r"(?:\s+(?:today|lately|recently|this\s+week|this\s+morning|at\s+work|at\s+school|then|"
    r"so\s+far|with\s+you))*\s*$", re.I)
# The ask has to be the whole line, or nearly: "got any good news" asks for the news, and "tell me
# something good about london" asks about London, which the news pool has no answer for.
NEWS_FRAME = frozenset("""got get any anything whats what's what is about how do you u have it
    there tell give us hear heard share spill some good nice happy great brilliant amazing
    wonderful excellent fantastic news today lately now then so well and but ok okay oh hi hey
    hello morning hows how's been new happen happened happening anything the a an i we me my
    week weekend day on going with for at""".split())


# "for you", "to tell you", "for us all": the news is being brought, so the line reports it.
# "for me" is the ask, and a bare "for" ("news for the weekend") changes nothing.
HANDED_OVER = re.compile(r"\bfor\s+(?:you|u|ya|you\s+two|us\s+all)\b|\b(?:to|i'?ll)\s+tell\s+you\b")


# The same ask in the words people use for it, none of which says "news": "what's the script",
# "what's the word", "what's the buzz", "what's the goss", "what's occurring", "what's been
# happening", "what's the latest", "tell me the crack". Every one of those reached the hedge that
# says it does not know enough to answer, which is no answer to small talk.
#
# Each stands in for the news only when nothing is named after it: "what's the script with my
# landlord" is a question about the landlord, "what's the word for the thing on a kettle" is a
# question about a word, and "what's happening at the school" is a question about the school.
# "what's going on" is left out on purpose: it is the how-are-you line far more often than it is
# the news, and the warm answer it already had ("Can't complain. Better question: how are you
# doing?") is the better of the two.
NEWS_IDIOM = re.compile(
    r"^(?:(?:so|ok|okay|well|and|but|oh|right|hi|hey|hello|morning|now|then)\s*,?\s+)*"
    r"(?:whats|what's|what\s+is|what\s+was|tell\s+me|give\s+me|spill)\s+"
    r"(?:(?:the|any|all\s+the)\s+)?"
    r"(?:script|crack|craic|story|latest|word|buzz|goss|gossip|happening|occurring|"
    r"been\s+happening)\b", re.I)
# What may follow the idiom and nothing else: "what's the crack then", "what's the latest now",
# "what's been happening today". A word outside this set names something, and a line that names
# something keeps its own answer.
NEWS_IDIOM_TAIL = frozenset("""then now today lately mate pal folks everyone guys all so
    far at the moment please thanks""".split())


def _an_idiom_standing_alone(low, end):
    """True when nothing after the idiom names a thing of its own."""
    tail = [w.strip(".,!?;:\"'") for w in low[end:].split()]
    return all(w in NEWS_IDIOM_TAIL for w in tail if w)


# The news the person has is not always called news: "what happened today" and "so what happened
# then" ask for the same nod as "got any good news", and they ask it of the day rather than of a
# thing - "what happened to my sourdough" wants the bread, not the nod - so only a bare day word
# after it keeps the line here.
WHAT_HAPPENED_ASK = re.compile(
    r"^(?:(?:so|ok|okay|well|and|but|oh|right|hi|hey|hello|morning|now|then)\s*,?\s+)*"
    r"what(?:'s|s|\s+has|\s+have)?\s+happened"
    r"(?:\s+(?:today|lately|recently|this\s+week|this\s+morning|tonight|then|so\s+far|"
    r"at\s+work|at\s+school|in\s+your\s+day|with\s+you))*\s*$", re.I)


def asks_for_news(clean):
    """Whether the line asks for the news rather than telling it."""
    if not clean:
        return False
    low = clean.strip().rstrip("?!.").lower()
    idiom = NEWS_IDIOM.match(low)
    if idiom and _an_idiom_standing_alone(low, idiom.end()):
        # The ask in the words people use for it, with nothing named after it.
        return not HANDED_OVER.search(low)
    if WHAT_HAPPENED_ASK.match(low):
        # The day the person had, in the words they use for it, with nothing named after it.
        return True
    if not (NEWS_ASK.match(low) and NEWS_WORD.search(low)):
        return False
    if "news" in low:
        if WORLD_NEWS.search(low):
            return False
    elif not _STANDIN.search(low):
        return False
    # "got some good news for you" and "i have news to tell you" are a person handing the news over,
    # not asking for any: the same words as an ask, and the opposite direction. "for me" asks.
    if HANDED_OVER.search(low):
        return False
    words = [word for word in (w.strip(".,!?;:\"'") for w in low.split()) if word]
    if all(word in NEWS_FRAME for word in words):
        return True
    # A topic after the ask ("any good news about the job") is still an ask for the news about it.
    # "tell me something good about london" is a question about London, and it wants the fact.
    return words[0] not in ("tell", "give", "share", "spill")


# A happy thing that has not happened yet is news the same as one that has: "we are getting
# married in june", "we are having a baby in april", "i start my new job on monday". What makes
# these a reading of their own is the *date*: the event is placed ahead of now, so the reply must
# not ask how it went ("Good. How were the first days?" to somebody who has not started yet) and
# must not file it either ("Noted: you are getting married in june.", which is a filing cabinet
# and not a friend). The two halves are kept apart so nothing else is read as it: the event has to
# be the progressive or the present of a plan ("getting married", "having a baby", "starts
# school"), never a past one, so "i got married in june" stays the news that it happened.
_AHEAD = re.compile(
    r"\b(?:in\s+(?:the\s+)?(?:\d+\s+)?(?:days?|weeks?|months?|years?|"
    r"spring|summer|autumn|winter|" + _MONTH + r")"
    r"|next\s+(?:week|month|year|spring|summer|autumn|winter|weekend|" + _WEEKDAY + r")"
    r"|on\s+" + _WEEKDAY +
    r"|starting\s+(?:on\s+)?" + _WEEKDAY +
    r"|tomorrow|tonight|this\s+(?:weekend|week|month|spring|summer|autumn|winter)"
    r"|soon|coming\s+up|later\s+(?:this|in)\b)", re.I)
# A birthday counted down: the age, and the date the rest of the line carries. The number has to
# be an age: "my pay is 500 a month in winter" and "my savings are 500 next year" are dated lines
# with a number in them, and a money worry answered with "look forward to it" is the worst miss
# this reading can make. A sum followed by a measure is not an age however the line is shaped, and
# a clause that names money is not a birthday (see `_a_money_clause`).
_COUNTED_UP = re.compile(
    r"\b(?:turning|turns?|is|am|im|i'm|are|be|will\s+be|'ll\s+be)\s+\d{1,3}\b"
    r"(?!\s*(?:pounds?|quid|dollars?|euros?|grand|thousand|percent|%|hours?|minutes?|mins?|"
    r"miles?|kg|kilos?|litres?|liters?)\b)"
    r"(?!\s+a\s+(?:month|week|year|hour|day)\b)"
    r"(?!\s+per\s+\w+)", re.I)
# A number is an age only when the thing that carries it can have one: a person or an animal.
# "my nan is 84 next week" is a birthday; "my shift is 10 next week", "our kitchen is 30 next
# year", "my bus is 20 next week" and "my meeting is 10 next week" count a rota, a room and a
# timetable, and congratulating those is worse than the filing cabinet it replaced. The clause is
# the test, so the age beside another event still reads: "my son is 5 next week and we are moving".
_A_PERSON = re.compile(
    r"\b(?:i|im|i'm|me|we|us|she|he|they)\b"
    r"|\b(?:my|our|his|her|their|the|a)\s+(?:\w+\s+)?"
    r"(?:son|daughter|kid|child|baby|boy|girl|toddler|teen|teenager|nipper|youngster|unborn|"
    r"mum|mom|mother|dad|father|nan|nana|gran|granny|grandma|grandad|grandpa|grandmother|"
    r"grandfather|sister|brother|niece|nephew|cousin|aunt|auntie|uncle|twins?|"
    r"friend|mate|wife|husband|partner|girlfriend|boyfriend|fiance|fiancee|boss|colleague|"
    r"dog|puppy|pup|cat|kitten|rabbit|hamster|guinea\s+pig|horse|pony|pet)\b", re.I)
# Or the line says it is an age itself: "84 years old", "my mum turns 60", "her birthday".
_AN_AGE_SAID = re.compile(
    r"\b(?:years?|yrs?)\s+old\b|\bage[sd]?\b|\bturning\b|\bturns?\b|\bbirthday\b|"
    r"\bbday\b|\bdue\b", re.I)


_COMING_UP = (
    # a wedding that is being planned, and the date being set for one (the date in the words)
    re.compile(r"\b(?:getting|get)\s+(?:married|wed)\b|\b(?:our|the|my)\s+wedding\b"
               r"|\bset\s+(?:a|the)\s+date\b", re.I),
    # a baby on the way: the same words as the birth, in the present, and the date decides
    re.compile(r"\b(?:having|expecting)\s+(?:a\s+|our\s+|twins?\b|a\s+little\b)", re.I),
    # the baby that is due, however the family puts it
    re.compile(r"\bbaby\s+(?:is\s+|'s\s+)?due\b"
               r"|\b(?:i'm|im|i am|we're|we are|she's|she is|hes|he is)\s+due\b", re.I),
    # something of their own that starts on a day
    re.compile(r"\bstart(?:s|ing)?\s+(?:my\s+|a\s+|the\s+|our\s+)?(?:[\w-]+\s+){0,2}?"
               r"(?:job|role|course|college|uni|university|school|placement|apprenticeship|"
               r"training|shift|work)\b", re.I),
    # the same thing said the other way round: the job is the subject and it starts on the day
    re.compile(r"\b(?:new\s+)?(?:job|role|course|shift)\s+(?:starts|starting|begins|beginning)\b",
               re.I),
    re.compile(r"\bmov(?:e|ing)\s+(?:houses?|home|flats?|place|into|in|out|to|away|abroad|back)\b", re.I),
    # a birthday that is being counted down, with the date the rest of the line carries (see
    # `_COUNTED_UP`, kept apart because the sum in the line can make it not an age)
    _COUNTED_UP,
    # a working life that ends on a date
    re.compile(r"\bretir(?:e|es|ing)\b", re.I),
    re.compile(r"\b(?:half\s+)?marathon\b|\b10k\b|\btriathlon\b", re.I),
)
# The phrases that put the thing ahead of now on their own, with no date to read: a date set for
# a wedding, and a baby on the way are both still to come however the line is written.
_SOON_ITSELF = re.compile(r"\bset\s+(?:a|the)\s+date\b|\b(?:having|expecting)\s+a\s+baby\b"
                          r"|\b(?:a|our|the|my)?\s*baby\s+(?:is\s+|'s\s+)?due\b", re.I)
# The past is not ahead of now, whatever the date after it says: "i got married in june" is the
# news that it happened, and "we already moved in" is the arrival.
_ALREADY = re.compile(r"\b(?:yesterday|last\s+(?:week|month|year|night|weekend)|"
                      r"a\s+few\s+(?:days|weeks)\s+ago|already|used\s+to)\b", re.I)
# A thing still to come that the person is dreading is not news to look forward to: "my shift
# starts at 6 tomorrow and im dreading it", "we are having a baby and i dont know how we will
# afford it". The worry is the line, so the reading stands down and the line keeps what it had.
_DREAD = re.compile(r"\b(?:dread(?:ing|ed)?|not\s+looking\s+forward|worr(?:y|ied|ies|ying)|"
                    r"scared|terrified|nervous|anxious|panic(?:king)?|stress(?:ed|ful)?|"
                    r"afford|terrible|awful|hate|hopeless|no\s+idea\s+how|"
                    r"upset|angry|furious|livid|annoyed|not\s+speaking|not\s+talking|"
                    r"stopped\s+speaking|not\s+happy)\b", re.I)


# A thing called off is not a thing to come: "we are not getting married anymore", "they are not
# having another baby". The negation sits in front of the event, so it is the event that is read.
_NOT_HAPPENING = re.compile(
    r"\b(?:not|never|no\s+longer|stopped|cancelled?|canceled?|called\s+off)\s+(?:\w+\s+){0,3}"
    r"(?:get(?:ting)?\s+(?:married|wed)|having|expecting|turning|turns?|mov(?:e|ing)|retir(?:e|es|ing))"
    r"\b", re.I)
# A bare question is an ask, not the news: "is my mum turning 60" wants the answer, and the
# looking-forward reply is what a person gets when they tell you. "will" is left out: "we will be
# getting married in june" is somebody telling you their date.
_BARELY_ASKED = re.compile(
    r"^(?:is|are|am|was|were|do|does|did|have|has|had|can|could|would|should|shall|may|might"
    r"|what|when|where|who|why|how)\b", re.I)


# A clause that is about money is not a birthday with a number in it: "my rent is 900 in january"
# has the date and the count and neither of them is news to look forward to. The clause is the
# test, so "my nan is 84 next week and the party is costing 200" keeps its birthday.
_MONEY = re.compile(r"\b(?:rent|pay|wage|wages|salary|bill|bills|price|prices|cost|costs|"
                    r"deposit|savings?|income|mortgage|overdraft|loan|loans|debt|debts|"
                    r"arrears|fine|fines|invoice|quote|quotes|tax|council\s+tax)\b", re.I)
_CLAUSE_BREAK = re.compile(r"[,;]|\b(?:but|and|so|because|though|although)\b", re.I)


def _a_money_clause(clean):
    """True when a clause of the line counts something in money rather than in years."""
    for clause in _CLAUSE_BREAK.split(clean or ""):
        if _MONEY.search(clause) and re.search(r"\d", clause):
            return True
    return False


# The same "ahead of now" question asked on its own, for a reader that needs only that half: a
# move is not news to look forward to, but it is a thing ahead, and the pool that asks about it
# (`bot/compose/moving.py`) was held back from every line that says when in words. "we are moving
# house in six weeks" was answered "Noted: you are moving house in six weeks.", "i am moving out in
# a fortnight" was read as a move to a place called A Fortnight, and only the lines written in
# figures ("in 3 weeks") reached the pool. A span of time counts however it is written, and the
# hedge people put in front of it ("in about three weeks") is the same span.
_AHEAD_SPAN = re.compile(
    r"\bin\s+(?:the\s+)?(?:about\s+|around\s+|roughly\s+|nearly\s+|almost\s+|"
    r"just\s+over\s+|over\s+)?(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|a\s+few|a\s+couple\s+of|a|an)?\s*"
    r"(?:hours?|days?|weeks?|fortnights?|months?|years?|"
    r"spring|summer|autumn|winter|" + _MONTH + r")\b", re.I)


# A move said as done ("i moved in on saturday", "we've moved house", "the move happened last
# week") carries the day the same way the future does, so the "ahead" question is asked of a line
# with nothing past-tense in it.
_DONE_ALREADY = re.compile(
    r"\b(?:moved|have\s+moved|had\s+moved|comes\s+home|we\s+did\s+move)\b"
    r"|\b(?:yesterday|last\s+(?:week|month|year|weekend))\b|\balready\b", re.I)


def ahead_of_now(text):
    """Whether the line puts its thing ahead of now, by a date or by a span of time.

    Only the date half of `reads_as_news_to_come`: no view on whether the thing is good news, and
    no view on whether it has already happened - every caller asks its own second question.
    """
    clean = " ".join(str(text or "").lower().split())
    if not clean or "?" in clean:
        return False
    # A move already made is behind the person, and "i moved in on saturday" carries the same
    # words as "i move in on saturday": the day is not what decides it, the tense is.
    if _DONE_ALREADY.search(clean):
        return False
    return bool(_AHEAD.search(clean) or _AHEAD_SPAN.search(clean))


def reads_as_news_to_come(clean):
    """Whether the line puts a happy event ahead of now: a date and a thing still to happen."""
    if not clean or "?" in clean:
        return False
    if (BAD.search(clean) or NOT_NEWS.search(clean) or NOT_QUITE.search(clean)
            or doubted(clean) or reads_as_someones_death(clean)):
        return False
    if _ALREADY.search(clean) or _DREAD.search(clean):
        return False
    if _NOT_HAPPENING.search(clean) or _BARELY_ASKED.search(clean):
        return False
    if not _AHEAD.search(clean) and not _SOON_ITSELF.search(clean):
        return False
    if not re.search(r"\b(?:i|we|my|our|im|i'm|we're|were)\b|\bthe\s+baby\b", clean):
        return False
    hits = [pattern for pattern in _COMING_UP if pattern.search(clean)]
    if not hits:
        return False
    # A sum is not an age, and only the counted number can be a sum: "my rent is 900 in january"
    # has the date and the count and neither is news to look forward to, while a baby or a
    # wedding keeps its reading however the rest of the line reads. Nor is a rota or a timetable
    # an age: the number has to count somebody who can grow a year older (see `_A_PERSON`).
    if all(pattern is _COUNTED_UP for pattern in hits):
        if _a_money_clause(clean) or not _the_number_counts_a_life(clean, hits):
            return False
    return True


def _the_number_counts_a_life(clean, hits):
    """True when the counted number is somebody's age, not a rota or a timetable.

    Read on the clause that carries the number, so an age beside another event still reads
    ("my son is 5 next week and we are moving house"), and then on the whole line for a line that
    says it is an age without a person in the same clause ("84 years old next tuesday").
    """
    if _AN_AGE_SAID.search(clean):
        return True
    for clause in _CLAUSE_BREAK.split(clean or ""):
        if _COUNTED_UP.search(clause) and _A_PERSON.search(clause):
            return True
    return False


# A prize that arrived in a message is not a win the person is telling you about. "i got a text
# saying i won a prize", "a letter says i won a prize but i need to send a fee" and "my son came
# home with a letter saying he won a holiday" were all congratulated - "Love that - well done. How
# are you celebrating?" - because the only shape they share with real news is the winning. Nobody
# enters a competition by being texted about it: the win word with a medium word, and no ticket of
# their own in the line, is the advance-fee scam, and it is answered by the prize row in money.py.
# "i won 500 pounds on a scratchcard" and "i entered a competition and won a hamper" keep their
# congratulations, because a person did the entering.
_A_WIN = r"(?:won|win|winner|winnings|prize|prizes|jackpot|lottery|competition|sweepstake)"
_A_MEDIUM = (r"(?:text|texts|texted|message|messages|email|emails|letter|letters|call|phone call|"
             r"voicemail|whatsapp|dm|notification)")
_ENTERED_IT = re.compile(
    r"\b(?:i|we)\s+(?:entered|entered it|took part|did the|bought|played|signed up|applied)\b"
    r"|\bscratchcard\b|\braffle ticket\b|\bticket\b|\bmy number came up\b", re.I)
# The order the two arrive in is the whole question. A message that claims a win ("i got a text
# saying i won a prize", "a letter says i won a prize") is the scam; a win the person is telling
# you about, with the email that came after it ("i won a prize at work and they emailed me the
# details", "i won a hamper in the school raffle and they texted me"), is their news, and it was
# being called a scam because the medium word was in the line at all.
_A_MESSAGE_THAT_CLAIMS_A_WIN = re.compile(
    r"\b" + _A_MEDIUM + r"\b(?:(?!" + _A_WIN + r").){0,60}?\b" + _A_WIN + r"\b", re.I | re.S)
_A_WIN_THEN_A_MESSAGE = re.compile(
    r"\b" + _A_WIN + r"\b(?:(?!" + _A_MEDIUM + r").){0,60}?\b" + _A_MEDIUM + r"\b", re.I | re.S)
# A win first is still the scam when the message asks for something: the fee, the bank details, a
# reply to a number. That ask is the tell, and without it the win is being talked about.
_ASKS_FOR_SOMETHING_BACK = re.compile(
    r"\b(?:fee|fees|pay|paid|send|transfer|wire|release|admin|processing|clearance|customs|"
    r"bank details|account details|card details|sort code|final notice|get in touch|"
    r"contact us|text them|text back|call them|ring them|reply|respond|confirm your)\b|£",
    re.I)
_NEVER_ENTERED = re.compile(
    r"\b(?:never|did\s*nt|did\s+not|do\s*nt|do\s+not)\s+(?:even\s+)?(?:enter|entered|"
    r"applied|signed up|took part)\b", re.I)


# Two shapes that use the same words as the scam and are not it. A win the person had and was
# then told about ("i won a prize and they emailed me about it") is being talked about, not
# billed for; and a relative's win, told by the relative ("my sister texted me that she won a
# prize"), is their news. A prize called a scam is the worst direction for this to be wrong in.
_ABOUT_THE_WIN = re.compile(
    r"\b(?:about|over)\s+it\b|\bto\s+(?:tell|let)\s+me\b|\bto\s+say\b|\bconfirming\b"
    r"|\bwell\s+done\b|\bcame\s+after\b|\bafterwards\b|\bthe\s+details\b"
    r"|\bcongratulat\w*\b|\bto\s+let\s+us\s+know\b", re.I)
_A_RELATIVE_TOLD_ME = re.compile(
    r"\b(?:(?:my|our)\s+)?(?:sister|brother|son|daughter|mum|mam|mother|dad|father|friend|mate|partner|"
    r"husband|wife|colleague|girlfriend|boyfriend|cousin|nan|gran|granny|aunt|uncle|niece|"
    r"nephew|neighbour|neighbor)\b.{0,40}?\b(?:texted|texts|messaged|messages|told|tells|"
    r"called|calls|rang|rings|phoned|phones|wrote|whatsapped|emailed|emails)\b.{0,20}?"
    r"\b(?:me|us)\b", re.I | re.S)


def reads_as_a_prize_in_a_message(clean):
    """True when the win in the line came to the person in a message they did not ask for."""
    if not clean or _ENTERED_IT.search(clean):
        return False
    if _ABOUT_THE_WIN.search(clean) or _A_RELATIVE_TOLD_ME.search(clean):
        return False
    if _NEVER_ENTERED.search(clean):
        return True     # "i won a competition i never entered" is the scam whatever the order
    if _A_MESSAGE_THAT_CLAIMS_A_WIN.search(clean):
        return True
    return bool(_A_WIN_THEN_A_MESSAGE.search(clean) and _ASKS_FOR_SOMETHING_BACK.search(clean))


# A year behind the line makes it a memory, not news. "my book was published in 1998", "he was
# offered the job in 2015" and "my mum got her degree in 1991" are things that happened a long time
# ago, and answering them "Congratulations - that's lovely news" reads as if the bot had not
# listened to a word of it. It is the year that says so rather than the tense, because a year still
# to come or the present tense is the news ("my book is out in march").
#
# "we only just moved in in 2024" is still the move somebody is telling you about, so the words
# that say it has just happened keep the reader's answer, and the year is only read as behind when
# it is behind this one: "in 2026" said in 2026 is this year's news.
A_YEAR_AFTER = re.compile(r"\b(?:in|since|back\s+in|during|of|from)\s+((?:19|20)\d\d)\b", re.I)
JUST_HAPPENED = re.compile(
    r"\b(?:just|only\s+just|this\s+(?:week|month|year)|today|yesterday|last\s+(?:night|week)|"
    r"at\s+the\s+weekend|finally)\b", re.I)


def a_year_behind(text, today=None):
    """Whether the line puts the thing in a year that has gone: "answered in 1998", "the class of 2015"."""
    when = today or datetime.date.today()
    for match in A_YEAR_AFTER.finditer(str(text or "")):
        try:
            if int(match.group(1)) < when.year:
                return True
        except (TypeError, ValueError):  # noqa: BLE001 - a year that will not read is no year
            continue
    return False


# The congratulations pool greets a win as if it had just arrived ("Congratulations - that's lovely
# news", "Brilliant. Really pleased for you"), and a line that puts its win in a year that has gone
# is a memory rather than news: "my book was published in 1998" answered that way reads as if the
# bot had not listened to a word of it. The reading still holds - it is a happy thing, and it is
# said back warmly - but the reply gets a question about it instead of a cheer for it, because the
# only interesting thing about a 1998 book is what made the person mention it now.
YEARS_BACK_LINES = (
    "Good to hear. What made you think of it now?",
    "Nice one - what brings it up today?",
    "Good to hear. Is it something you still think about?",
)


# "im engaged, we got together in 2019" puts a year in the line and the news in the present: the
# year belongs to another part of it, and the cheer is the reply the person wants. So a line that
# says its news in the present tense is left alone, and only one that rests on the year is met with
# the question about it.
SAYS_IT_IN_THE_PRESENT = re.compile(r"\b(?:im|i'm|i\s+am|we\s+are|we're)\b", re.I)


def reply_for_a_year_ago(text, reply, memory=None):
    """The line for a win the person puts in a year that has gone, or None for another turn."""
    if not (reads_as_a_congratulation(reply) or the_cheer_was_this_pool(memory)):
        return None
    return reply_for_a_win_from_a_past_year(text)


def reply_for_a_win_from_a_past_year(text):
    """The line for a win the person puts in a year that has gone, or None for another line.

    Whether the reply it would have got is a cheer is the caller's question, and the two callers
    know it differently: `chat.py` has just picked the congratulations pool, and `greeting.py` has
    the composer's reply in front of it. So this reads the line and nothing else.
    """
    line = str(text or "")
    if not a_year_behind(line):
        return None
    if JUST_HAPPENED.search(line.lower()) or SAYS_IT_IN_THE_PRESENT.search(line):
        return None
    return YEARS_BACK_LINES[sum(map(ord, line.strip().lower())) % len(YEARS_BACK_LINES)]


def the_cheer_was_this_pool(memory):
    """Whether the reply the person just got came from the good-news pool, whatever it said.

    A wording list over the composer's prose is always a month behind the prose, and the pool has
    lines that no congratulations pattern reads ("Love that - well done. How are you celebrating?",
    "Good stuff. That must be a weight off."). `chat._say` notes the pool where the reply is
    chosen, and the arbiter keeps the notes of the module whose reply the person got, so the note
    cannot be there for a reply another module gave.
    """
    note = memory.get("said_kind") if isinstance(memory, dict) else None
    if not isinstance(note, dict) or note.get("kind") != "good_news":
        return False
    turns = memory.get("turns")
    return note.get("turn") == (len(turns) if isinstance(turns, list) else 0)


# A cheer has more than one pool behind it and they all greet the news as if it had just arrived,
# so the line is read for what it is doing rather than for which pool it came from: the words a
# congratulation opens with, in the order they open it.
_A_CHEER = re.compile(
    r"^(?:congratulations|well\s+done|brilliant|lovely(?:\s+news)?|wonderful|fantastic|"
    r"that(?:'s|s)?\s+(?:great|lovely|wonderful|brilliant|fantastic|really\s+lovely)\b|"
    r"good\s+for\s+you|so\s+pleased|really\s+pleased|lovely\s+to\s+hear)", re.I)


def reads_as_a_congratulation(reply):
    """Whether the composer's line is a cheer for something that has just happened."""
    said = " ".join(str(reply or "").split())
    return bool(_A_CHEER.match(said))


# A short detail added to news the bot has just cheered. The congratulations pool greets the win,
# and the turn after it is often the best part said as plain words: "i passed my driving test" then
# "first time", "third go", "we won on saturday" then "2-0". None of those has a subject of its
# own, so the turn went to a card about the subject ("Most people need around 45 hours of lessons
# plus 20 hours of private practice before they pass", "That's 2") or to a shrug ("Got it. Is there
# anything you'd like a hand with?"), and the friend's reply is to take the detail and be gladder.
#
# Three shapes, because they are the ones a detail of news really comes in: which go it was, the
# score, and the figures of a new baby. Anything else with a thing in it ("start monday") is a noun
# the greeting pool already reads and answers.
_AN_ATTEMPT = re.compile(
    r"\b(?:first|second|third|fourth|fifth|sixth|1st|2nd|3rd|4th|5th|6th|last)\s+"
    r"(?:time|go|try|attempt|sit)\b")
_A_NUMBER = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
_A_SCORE = re.compile(_A_NUMBER + r"\s*(?:-|to)\s*" + _A_NUMBER + r"|" + _A_NUMBER + r"\s*nil")
_OR_A_SCORE = re.compile(r"^\s*" + _A_NUMBER + r"\s*(?:-|to)?\s*(?:" + _A_NUMBER + r"|nil)\s*$")
# "ten to two" is a time, not a result. `_A_SCORE` takes "N to M" for any `_A_NUMBER`, so a win
# reported at ten to two was read as a score and cheered with "Ten to two - better than a plain
# win." What tells the two apart is the minutes side of it: a clock's minutes are fifths of an
# hour, and a score's are whatever the game produced. So "ten to two", "five to six",
# "quarter to eight" and "20 to 9" are clocks, and "three to two" and "2 to 1" stay results.
_A_CLOCK_MINUTES = (r"(?:5|10|15|20|25|30|35|40|45|50|five|ten|quarter|fifteen|twenty|twenty[- ]five"
                    r"|thirty|thirty[- ]five|forty|forty[- ]five|fifty)")
_AN_HOUR = (r"(?:1|2|3|4|5|6|7|8|9|10|11|12|one|two|three|four|five|six|seven|eight|nine|ten"
            r"|eleven|twelve)")
_A_CLOCK = re.compile(r"^\s*" + _A_CLOCK_MINUTES + r"\s*(?:past|to)\s*" + _AN_HOUR + r"\s*$")
# A new baby's figures: "a boy, 8 pounds", "a girl, 7lb 2oz", "8 pounds 4", "he was 7 pounds".
# The greeting pool reads "a girl" as the announcement and cheers it, and "a boy, 8 pounds" was
# read as a question about a weight: the knowledge base answered it with the card about average
# birth weights and the weigh-in appointments, five sentences of it, to somebody who had just said
# their sister had a baby. What keeps a weight to the arrival is the birth in the chat, not the
# figure on its own - "its 8 pounds an hour" after "i got the job" is a wage and stays where it is.
_A_WEIGHT = re.compile(r"\b\d+(?:\.\d+)?\s*(?:lb|lbs|pounds?|kg|kilos?|oz|ounces?)\b", re.I)
# ...and it is a detail only when the figures are all the line is. "is 8 pounds ok" asks about the
# figure, "8 pounds, is that ok" asks at the end of it, and a friend answers either of those rather
# than cheering them; "he was 7 pounds" is the detail. So every word of the line has to be the sex,
# the figures, or the words that join them - the same whole-line test `_OR_A_SCORE` makes for a
# score, for the same reason: a shape that reads a detail out of a question is worse than no shape.
_AROUND_THE_FIGURES = frozenset("""
    a an the its it's hes shes he she they theyre were was is are both and so just about exactly
    weighing weighed weigh born baby twins boy girl little pound pounds lb lbs kg kilo kilos oz
    ounce ounces gram grams g of on in at with each apiece together
""".split())
_A_FIGURE_IN_THE_LINE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:lb|lbs|pounds?|kg|kilos?|oz|ounces?|g|grams?)?", re.I)


def _only_the_arrivals_figures(said):
    """Whether every word of the line is the sex, a figure, or the words that join them."""
    for word in str(said or "").lower().replace("\u2019", "'").split():
        bare = word.strip(".,!;:\"'")
        if not bare or bare in _AROUND_THE_FIGURES:
            continue
        if _A_FIGURE_IN_THE_LINE.fullmatch(bare):
            continue
        return False
    return True
# A detail is a short line with nothing asked in it. The words here are the ones that turn the same
# shape into a question, a thanks or a goodbye, and none of them is part of a detail.
_ASKS_OR_THANKS = re.compile(
    r"\?|\b(?:what|how|why|when|where|who|which|can|could|should|would|will|shall|do|does|did|"
    r"is|are|was|were|thanks|thank|thx|ty|ta|cheers|bye|goodbye|night|please|sorry)\b")


# The wording for that detail. The cheer has just been given, so the pool takes the detail as the
# news again: it never asks a question of its own ("how did it go?") and never guesses what the win
# means, because the person has already said the part that matters.
# No "Well done." in these: the cheer that took the news was the turn before, and saying it again
# reads as a bot with one line ("Love that - well done. How are you celebrating?", then the detail,
# then "...better than a plain win. Well done."). The detail line's job is to take the detail, not
# to congratulate a second time.
MORE_OF_THE_NEWS = (
    "However many goes it took, you have it now.",
    "The win is the whole of it, not which go it was.",
    "{X} — the way to have it.",
)
MORE_OF_THE_NEWS_SCORE = (
    "{X} — better than a plain win.",
    "A score like that makes it a better story.",
    "Even better than it sounded.",
)
# The arrival's figures. No word here about the weight itself: 8 pounds is a good weight and 4
# pounds is a worry, and the friend's move on hearing either is to be glad the baby is here, not to
# grade the figure. The cheer took the news on the turn before, so this line takes the detail.
MORE_OF_THE_NEWS_ARRIVAL = (
    "{X} — lovely news. Really pleased for you.",
    "{X}. Really pleased for you.",
    "{X} — that is the best kind of news.",
)
# The marks of one of those lines, for the arbiter: the pool is the one reply on the table that
# reads the detail as news, so a card about the subject must not take the turn off it.
_MORE_OF_THE_NEWS_MARKS = ("however many goes", "the win is the whole of it", "the way to have it",
                           "better than a plain win", "makes it a better story",
                           "even better than it sounded", "the best kind of news")


def reads_as_the_detail_line(reply):
    """Whether a reply is this module's own wording for a detail added to the news."""
    said = " ".join(str(reply or "").lower().replace("\u2019", "'").split())
    return any(mark in said for mark in _MORE_OF_THE_NEWS_MARKS)


def the_reply_just_cheered(memory):
    """Whether the reply the person just got came from the good-news pool.

    `the_cheer_was_this_pool` compares the note the composer makes with the number of turns, and a
    note made while the reply is being chosen counts the turns before it, so on the turn after the
    cheer it is one short. This reads the note the way the next turn finds it: one back from the
    turn just finished, and from this module, so a note left by an older cheer cannot answer for
    the reply in between.
    """
    if not isinstance(memory, dict):
        return False
    note = memory.get("said_kind")
    turns = memory.get("turns")
    if not isinstance(note, dict) or note.get("kind") != "good_news":
        return False
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1]
    if not isinstance(last, dict) or str(last.get("module") or "") != "chat":
        return False
    return note.get("turn") == len(turns) - 1


def a_detail_of_the_news(clean, memory=None):
    """The shape of a detail added to good news, or "" for another line.

    "attempt" for which go it was ("first time", "third go"), "score" for the result of the win
    ("2-0", "three nil"), "arrival" for a new baby's figures ("a boy, 8 pounds", "7lb 2oz"). It
    reads the line and the turn before it, nothing else: whether the cheer is the bot's own is
    `the_cheer_was_this_pool`, which the caller knows.
    """
    said = " ".join(str(clean or "").split())
    if not said or len(said.split()) > 6:
        return ""
    # The arrival's figures are the one shape read without the cheer: the birth in the chat is
    # the news, and the cheer for it came from whichever module greeted it. Requiring this
    # module's own note there left the figures to the card that reads a weight.
    if (_A_WEIGHT.search(said) and "?" not in said and _only_the_arrivals_figures(said)
            and a_birth_just_announced(memory)):
        return "arrival"
    if memory is not None and not (the_cheer_was_this_pool(memory) or the_reply_just_cheered(memory)):
        return ""
    if _AN_ATTEMPT.search(said):
        return "attempt"
    if _OR_A_SCORE.match(said) and _A_SCORE.search(said) and not _A_CLOCK.match(said):
        return "score"
    return ""


def a_birth_just_announced(memory):
    """Whether the person announced a birth in one of the two lines before this one.

    The weight is what makes a birth detail a birth detail, and a weight on its own says nothing:
    "its 8 pounds" is a wage or a parcel. The chat is what says which - the birth was the news, and
    the figures are the detail of it.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    said = [str(one.get("user") or "") for one in turns[-2:] if isinstance(one, dict)]
    return any(any(pattern.search(line) for pattern in BABY) for line in said if line)


def reads_as_a_detail_of_the_news(clean, memory=None):
    """Whether the line adds a detail to news the bot has just cheered, with nothing asked in it."""
    if _ASKS_OR_THANKS.search(" ".join(str(clean or "").split())):
        return False
    return bool(a_detail_of_the_news(clean, memory))


def reads_as_good_news(clean):
    """Whether a cleaned, lowercased line reports a happy event as a plain phrase."""
    if reads_as_news_to_come(clean):
        return False
    if not clean:
        return False
    if (BAD.search(clean) or NOT_NEWS.search(clean) or NOT_QUITE.search(clean)
            or doubted(clean) or reads_as_someones_death(clean)):
        return False
    if asks_for_news(clean):
        return False
    if reads_as_a_win_nobody_noticed(clean):
        return False  # news with nobody's word on it is answered as both halves, not congratulated
    if reads_as_a_prize_in_a_message(clean):
        return False  # a prize that arrived in a text is a scam, not a celebration
    if A_TURN_IN_THE_TALE.search(clean) or A_SETBACK_AFTER_THE_WIN.search(clean):
        return False  # the clause after the "and" takes the win back
    if _a_hand_over([w.strip(".,!?;:\"'") for w in clean.split()]):
        return False
    if _I_PRAISED.search(clean) and not any(
            pattern.search(clean) for pattern in BABY + PASSED + WIN):
        # "i said well done to my son", "i told her she did well": the praise is the person's own,
        # going out rather than coming in, and the only news in the line is that they gave it.
        return False
    return any(pattern.search(clean) for pattern in GOOD)


# A win with nobody saying anything about it. "i got promoted and my mum said nothing" is two
# things at once and the second one is the part that hurts, so the congratulations line ("Lovely
# to hear. Enjoy it!") is tone-deaf to it. This names the shape on its own, so the congratulations
# stands down (`reads_as_good_news` and `reads_as_a_pass` both ask here first) and the composer
# answers both halves from one pool.
NOBODY = (r"(?:nobody|no\s+one|no-one|not\s+(?:a\s+)?single\s+(?:one|person|soul)|"
          r"none\s+of\s+(?:them|us|my\s+\w+|the\s+\w+))")
# What a person does when they say something about your news. The words after `NOBODY` are the
# absence, so the list is of speaking rather than of caring: "nobody said well done" is this
# shape, "nobody was there" is not - that is a party nobody came to, which is its own thing.
_TOLD = (r"(?:said|says|saying|told\s+me|tells\s+me|congratulated|congratulates|noticed|notices|"
         r"mentioned|mentions|asked|asks|texted|texts|called|calls|rang|replied|replies|phoned|"
         r"wrote|written|thanked|thanks|clapped|acknowledged|commented|reached\s+out)")
NOBODY_SAID_ANYTHING = re.compile(
    # "nobody said well done", "no one congratulated me", "not a single person asked". The verb is
    # its own group, because what follows it decides whether this is a silence at all.
    r"(?P<first>\b" + NOBODY + r"\s+(?:even\s+|ever\s+|actually\s+|\w+\s+){0,2}?"
    r"(?P<verb>" + _TOLD + r")\b)"
    # "my mum said nothing", "they said nothing about it", "he texted me nothing". Here the
    # nothing is the object of the verb, so it is the silence whatever comes after it.
    r"|(?P<object>\b" + _TOLD + r"\s+(?:me\s+)?nothing\b)"
    # "my sister didnt even text me", "my dad never said a word", "nobody bothered"
    r"|\b(?:didnt|didn't|did\s+not|doesnt|doesn't|never|not)\s+(?:even\s+)?"
    r"(?:say|said|text|texted|call|called|ask|asked|notice|noticed|mention|mentioned|reply|replied|"
    r"congratulate|congratulated|thank|thanked|bother|bothered|ring|rang|write|wrote)\b",
    re.I)


# The silence has to be somebody else's. "i got the job but i never called them back" wears the
# same words as "my dad never called me" the other way round, and only the second is a silence
# round the win: the speaker's own quiet is not something anybody did to them, and answering it
# with "it stings that they said nothing" talks about people who were never mentioned. So the
# subject in front of a match decides it - the words of the clause the match begins in, back to
# the last conjunction or punctuation.
CLAUSE = re.compile(r"[,;.!?]|\b(?:and|but|so|yet|cos|because|while|when|if|though|although|"
                    r"then|till|until)\b")
SPEAKER = frozenset(("i", "im", "ive", "id", "ill", "myself"))


def _the_speaker_is_the_quiet_one(text, match):
    """Whether the words in front of the match name the person talking as the one who said nothing."""
    words = [w.strip(".,!?;:\"'") for w in CLAUSE.split(text[:match.start()])[-1].split()[-4:]]
    return any(word in SPEAKER for word in words)


# A verb of speaking takes an object, and the object is what makes the line something other than
# a silence: "nobody told me the hours" and "nobody said it would be hard" are about what was
# said, not about nobody saying anything, and answering them with "it stings that they said
# nothing" talks about people who did say something. So after the verb has to come the end of its
# clause, or the words that name the silence. `noticed` and `mentioned` are the exception: "nobody
# noticed i got promoted" is the silence, and its clause is what they missed.
TAKES_A_CLAUSE = frozenset(("noticed", "notices", "noticing", "mentioned", "mentions",
                            "mentioning"))
SILENCE_WORDS = frozenset(("nothing", "anything", "a", "word", "well", "done", "congrats",
                           "congratulation", "congratulations", "nice", "hello", "hi", "hooray",
                           "bravo", "much", "all", "good", "luck", "me", "us", "her", "him",
                           "them", "everybody", "anybody", "anyone", "on", "for",
                           "about", "at", "with", "to", "either", "it", "that"))
CLAUSE_STOPS = frozenset(("and", "but", "so", "yet", "though", "although", "while", "which",
                          "when", "because", "cos", "then", "if"))


def _the_silence_is_the_whole_of_it(text, match):
    """Whether nothing but the silence follows the verb in a silence match.

    It holds for both arms that end on a verb of speaking, not only the `nobody said ...` one:
    "i got the job and they never asked me for id" and "i got the job but they never mentioned the
    hours" wear the same words as a silence and are about people who said plenty. Only the arm
    that puts `nothing` after the verb is the silence whatever follows it."""
    if match.group("object") is not None:
        return True  # "my mum said nothing about it"
    verb = " ".join((match.group("verb") or "").split()[-1:])
    if verb in TAKES_A_CLAUSE:
        return True
    rest = re.split(r"[,.;!?]", text[match.end():], 1)[0]
    kept = []
    for word in rest.split():
        bare = word.strip(".,!?;:\"'")
        if bare in CLAUSE_STOPS:
            break
        kept.append(bare)
    return all(bare in SILENCE_WORDS for bare in kept)


def reads_as_a_win_a_cost_came_with(clean):
    """Whether a line reports a win and the cost of it in the same breath: "we finally got the
    keys and the place is a state".

    The sibling of `reads_as_a_win_nobody_noticed` and read the same way: both halves are needed,
    so a setback on its own is somebody's trouble and a win on its own is just good news. The
    difference is what the second half says - a silence around the win, or the price of it.
    """
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return False
    if NOT_NEWS.search(text) or NOT_QUITE.search(text) or doubted(text):
        return False
    if not any(pattern.search(text) for pattern in GOOD):
        return False
    if not (A_TURN_IN_THE_TALE.search(text) or A_SETBACK_AFTER_THE_WIN.search(text)):
        return False
    # "we came into some money and now we can fix the roof": the clause after the `and` is the
    # other half of the win, not a cost, and the cost words have to be there for it to be one.
    return not A_GOOD_ENDING.search(text)


def reads_as_a_win_nobody_noticed(clean):
    """Whether a line reports a win and a silence around it: "i got promoted and my mum said
    nothing". Both halves are needed - a silence on its own is somebody letting them down, which
    is answered elsewhere, and a win on its own is just good news - and the silence has to be
    somebody else's, not the speaker's own."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return False
    if NOT_NEWS.search(text) or NOT_QUITE.search(text) or doubted(text):
        return False
    if not any(pattern.search(text) for pattern in GOOD):
        return False
    for match in NOBODY_SAID_ANYTHING.finditer(text):
        if _the_speaker_is_the_quiet_one(text, match):
            continue
        if _the_silence_is_the_whole_of_it(text, match):
            return True
    return False


# "i dont feel better" has the words of the relief and the opposite of the news: the negator is
# what the line turns on, so it is read before the pattern. A "not" that belongs to some other
# clause ("i dont know why, but i feel better") is not a negation of the recovery, so the negator
# has to stand in front of it.
NEGATED = re.compile(r"\b(?:dont|don't|doesnt|doesn't|didnt|didn't|did\s+not|do\s+not|"
                     r"isnt|isn't|wasnt|wasn't|not|never|no\s+longer|no)\s+"
                     r"(?:(?:really|very|much|so|still|any|getting|feel|feels|feeling|felt|"
                     r"seem|seems|be|is|was|am|a|bit|lot|longer)\s+){0,3}better\b", re.I)


# "i dont feel better" and "hes not ok now" hold the opposite words to the good news and mean
# the opposite thing: a negator in front of the phrase keeps the line out of both families.
# "still" counts too - "its still fine now" says nothing has changed, which is not the news.
DENIED = re.compile(r"(?:\bnot\b|\bnever\b|\bno\s+(?:better|good|improvement)\b|\bstill\b|"
                    r"\bn't\b|\bain'?t\b|\b(?:do|does|did|is|are|was|were|has|have|had|could|"
                    r"would|should)n'?t\b|\bworse\b)", re.I)


def _denied(text, start, end=None):
    """Whether a negator sits in the phrase or just before it, which turns news to no news.

    The whole match is searched and not only the run-up: "my knee doesnt feel better" starts its
    match at "knee", so a check on the run-up alone would read it as the good news it denies."""
    return bool(DENIED.search(text[max(0, start - 26):(end if end is not None else start)]))


def reads_as_recovery(clean):
    """Whether a cleaned, lowercased line reports that something has got better."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return False
    if not ABOUT_THEM.search(text):
        return False
    if BAD.search(text) or NOT_NEWS.search(text):
        return False
    if CONDITIONAL.search(text):
        return False
    if NEGATED.search(text):
        return False
    return any(pattern.search(text) for pattern in RECOVERY)


# The same news about someone else, or about the thing that was wrong: "hes ok now" after
# "my son has a bad cough", "its gone down now" after a temperature. Said about a person or a
# body, so the subject is not the speaker and ABOUT_THEM has nothing to hold on to, but the
# ask is the same one: say the relief back rather than the line itself or a neutral nod.
SETTLED = (
    re.compile(r"\b(?:is|are|seems?|looks?|feels?)\s+(?:ok|okay|alright|fine|clear|normal)\s+"
               r"(?:now|again)\b", re.I),
    re.compile(r"\b(?:ok|okay|alright|fine)\s+now\b", re.I),
    re.compile(r"\b(?:(?:she|he|it|they)(?:'s|s)?\s+(?:is|are|was|were)?|(?:is|are|seems?|"
               r"looks?))\s*(?:much\s+|a\s+lot\s+|so\s+much\s+|loads\s+)?better\s+"
               r"(?:now|today|again|thanks)\b", re.I),
    # The completion belongs to the phrase: "my cough has cleared up" is the news, and a match that
    # stopped at "cleared" would leave the "up" outside it, which is the one thing the strict
    # reader below uses to tell "has cleared up" from "has gone green".
    re.compile(r"\b(?:has|have|had)\s+(?:gone|eased|cleared(?:\s+up)?|settled(?:\s+down)?|"
               r"stopped|come\s+down)\b", re.I),
    re.compile(r"\b(?:went|goes)\s+(?:away|down)\b", re.I),
    re.compile(r"\b(?:gone|eased\s+off|cleared\s+up|settled\s+down|died\s+down)\s+"
               r"(?:now|again|overnight|since)\b", re.I),
    re.compile(r"\b(?:gone|come|went)\s+(?:down|away|off)\b", re.I),
    re.compile(r"\b(?:eased|calmed|settled|cleared)\s+(?:off|down|up)\b", re.I),
    re.compile(r"\b(?:results?|tests?|scans?)\s+(?:came|come|are|is|were)\s+(?:back\s+)?"
               r"(?:clear|fine|normal|ok|okay|all\s+clear)\b", re.I),
    re.compile(r"\b(?:it|they)\s+came\s+back\s+(?:clear|fine|normal|ok|okay)\b", re.I),
    re.compile(r"\bit'?s\s+(?:all\s+)?gone\b", re.I),
    re.compile(r"\b(?:she|he|they)(?:'s|s)?\s+(?:over\s+(?:it|the\s+worst)|back\s+to\s+"
               r"(?:herself|himself|themselves|normal))\b", re.I),
    re.compile(r"\b(?:she|he|they)(?:'s|s|\s+is|\s+are)?\s+out\s+(?:now|today|again)\b", re.I),
    re.compile(r"\b(?:all\s+clear|out\s+of\s+(?:hospital|the\s+woods)|back\s+to\s+normal|"
               r"back\s+on\s+(?:his|her|their)\s+feet|over\s+the\s+worst)\b", re.I),
    # A thing that has healed is the same news as a thing that has gone, and it was the one
    # ending with no words for it: "my knee has healed", "the cut has healed up" and "the burn
    # has healed" were all handed back as "Got it - your knee has healed." A body part is what
    # heals, so this cannot be the "my back has gone" moment: that one is `BARE_GONE`, and
    # nothing here reads a bare "gone" without a trouble in front of it.
    re.compile(r"\b(?:has|have|had|is|are|was|were|s|'s)\s+(?:all\s+|now\s+|finally\s+)?"
               r"healed\b", re.I),
    re.compile(r"\bhealed\s+(?:up|over|now|nicely|well)\b", re.I),
    # "its stopped now" after a nosebleed or a burn: the thing that was running has stopped, and
    # the person is reporting the end of it. Only the plain "stopped" - "it stopped hurting when
    # i sat down" is a rule about the thing, not the news, so a clause after it is not read.
    re.compile(r"\b(?:it|that|this|it's|its|thats|that's|the\s+\w+)\s*(?:'s|s|\s+is|\s+has|"
               r"\s+have)?\s*stopped\s+(?:now|again|completely|properly|finally)\b", re.I),
    # "nothing hurts now" is the same news said without a subject to name.
    re.compile(r"\bnothing\s+(?:hurts|aches|is\s+sore|\w+\s+hurts)\s+"
               r"(?:now|any\s?more|today|at\s+all)\b", re.I),
)


# What makes "hes ok now" a piece of good news rather than a detail about something else: a
# worry said out loud in the last few turns. The words are the ones people use for a body or an
# illness, read off the history rather than imported, because `bot.memory` imports this module.
WORRY_WORDS = frozenset("""
sick ill poorly unwell fever temperature cough cold flu covid chest throat tummy stomach
headache migraine pain ache aches sore hurting swollen swelling rash lump dizzy faint
vomit vomiting sick diarrhoea infection antibiotics hospital a&e operation surgery scan
xray x-ray test results test radiography chemo chemotherapy treatment dose medicine
allergy allergic asthma inhaler epilepsy seizure seizure fit fits bleed bleeding
virus bug tonsils ear ears tooth teeth back knee hip ankle wrist shoulder neck leg arm
temperature poorly worried scared nervous accident fall fell collapsed plaster cast
burnt burn burns scald scalded cut cuts wound wounds blood bled bleeding nosebleed nosebleeds
blister blisters sting stung bite bitten bruise bruised sprain sprained splint fracture
broken finger fingers thumb hand hands foot feet toe toes eye eyes gum gums toothache
dressing bandage stitches stitch plastering
""".split())


def worry_on_the_table(memory, look_back=4):
    """True when the last few things the person said named a body, an illness or a worry."""
    turns = [t for t in ((memory or {}).get("turns") or []) if isinstance(t, dict)]
    seen = 0
    for turn in reversed(turns):
        said = " ".join(str(turn.get("user") or "").lower().split())
        if not said:
            continue
        if set(re.findall(r"[a-z']+", said)) & WORRY_WORDS:
            return True
        seen += 1
        if seen >= look_back:
            break
    return False


# An ask about someone else opens with the verb: "is he ok now", "has it gone down". Those are
# questions with or without the question mark, and news is not a question.
ASK_OPEN = re.compile(r"^(?:so|well|ok|okay|and|but|ah|oh|right|and)?[\s,]*(?:is|are|was|were|"
                      r"do|does|did|has|have|will|would|can|could|should|any)\b", re.I)


# "my back has gone" is the moment it went, not a back that got better: a bare "gone"/"went"
# counts as news only when the thing that went is the trouble ("the cough has gone", "my back
# pain has gone") and not the body itself. "gone again" is the trouble coming back, so it is
# not news either - it is the reason the person is writing.
BARE_GONE = re.compile(r"\b(?:gone|went)\b(?!\s*(?:down|away|off|all))", re.I)
BODY_GAVE_WAY = re.compile(
    r"\b(?:my|his|her|their|your|the)\s+(?:\w+\s+)?(?:back|knee|knees|leg|legs|arm|arms|"
    r"shoulder|shoulders|hip|hips|ankle|ankles|wrist|wrists|neck|foot|feet|hand|hands|"
    r"elbow|elbows|jaw|stomach|tummy|chest|side)\b"
    r"(?!\s*(?:pain|ache|aches|hurt|hurts|trouble|problem|injury|stiffness|muscle))", re.I)


def the_tail_adds_nothing(text, end):
    """Whether what follows a settled phrase is only the words that add nothing (SETTLED_TAIL)."""
    tail = re.sub(r"[,;:!?]", " ", str(text or "")[end:]).strip()
    return not tail or bool(SETTLED_TAIL.match(" " + tail))


def _a_bare_gone_is_not_the_news(text, match):
    """Whether a match that turns on "gone"/"went" is still the news, once the line is read."""
    if not BARE_GONE.search(match.group(0)):
        return True
    if re.search(r"\bgone\s+again\b", text, re.I):
        return False
    if BODY_GAVE_WAY.search(text):
        return False
    # "its gone" is the news only when nothing follows it: "its gone red and hot" after a cut is
    # the cut getting worse, and "its gone bigger" is a bite spreading. The same tail rule that
    # stands an answer down (`the_news_is_the_whole_of_it`) is what tells the two apart here, so a
    # changed symptom never gets the relief pool ("Glad to hear it - that's the news you want").
    return the_tail_adds_nothing(text, match.end())


# The words a settled phrase can be followed by and still be the end of the news. Anything else is
# a different report: "my cough has gone green" is a cough that has changed colour, and "its gone
# down with the kids" is not a swelling going down.
SETTLED_TAIL = re.compile(r"\s*(?:(?:now|again|today|tonight|thanks|completely|properly|finally|"
                          r"at\s+last|anyway|so\s+far|for\s+good|down|off|"
                          # how long it has been better is not a new report either: "im feeling
                          # better this week" is the same news as "im feeling better today", and
                          # the week is the span they are measuring it over. Only spans that point
                          # back at the time just gone are here, because "im feeling better next
                          # week" is a wish, not news.
                          r"this\s+week|this\s+morning|this\s+afternoon|this\s+evening|"
                          r"these\s+days|the\s+last\s+few\s+days|a\s+few\s+days|"
                          r"recently|lately|nowadays|for\s+now|for\s+a\s+while)\s*)*[.!]?$", re.I)


def the_news_is_the_whole_of_it(clean):
    """Whether the recovery or settled phrase in the line closes the clause.

    "the rash has cleared up" and "its stopped now" are the end of the trouble; "my cough has gone
    green", "the pain has gone down my leg" and "hes gone off his food" carry the same words and
    report something else. `reads_as_recovery` reads the words, so the reader that *stands an
    answer down* has to check what follows them: a cough that has gone green wants the
    chesty-cough card, and "That's a relief" at it is the wrong reply at a symptom that changed.
    The tail is only the words that add nothing (see `SETTLED_TAIL`), so a line with anything else
    after the phrase is a report of its own and keeps its own answer.
    """
    text = " ".join(str(clean or "").lower().split())
    end = 0
    for pattern in RECOVERY + SETTLED:
        for match in pattern.finditer(text):
            end = max(end, match.end())
    return bool(end) and bool(SETTLED_TAIL.match(text[end:]))


# A test that came back clear. Nothing in the composer read one, so the news a family waits on
# most arrived as its opposite: "my mums cancer is in remission" was read by `reads_as_bad_news`
# on the word "cancer" and met with "Sorry to hear that. What would help most right now?", and
# "the biopsy was benign" with "I'm sorry - that's frustrating". The words that carry the news are
# the result, not the illness: remission, benign, clear, not spread, the treatment working.
#
# Each row is written with what makes it a result, because the same words mean something else
# without it - "the road was clear" is a drive, "a benign remark" is a comment, and "has it
# spread" is the question this is the answer to.
CLEAR_RESULT = (
    re.compile(r"\b(?:in|out\s+of)\s+(?:full\s+)?remission\b", re.I),
    re.compile(r"\b(?:scan|scans|results?|tests?|biopsy|mri|ct|x-?ray|bloods?|screening|"
               r"checks?|check\s?up|swabs?)\b[^.!?]{0,24}?\b(?:came\s+back|come\s+back|"
               r"was|were|is|are|looks?|looked)\s+(?:all\s+)?(?:clear|normal|fine|negative)\b",
               re.I),
    re.compile(r"\b(?:biopsy|lump|mole|tumou?r|cyst|polyp|growth|cells?|cells)\b"
               r"[^.!?]{0,20}?\b(?:was|were|is|are|turned\s+out|come\s+back|came\s+back)\s+"
               r"(?:benign|harmless|nothing\s+to\s+worry\s+about)\b", re.I),
    re.compile(r"\b(?:hasnt|hasn't|hadnt|hadn't|has|had)\s+not\s+spread\b"
               r"|\bit\s+(?:hasnt|hasn't|hadnt|hadn't)\s+spread\b", re.I),
    re.compile(r"\bno\s+(?:sign|trace|evidence)\s+of\s+(?:it|any\s+cancer|the\s+cancer|"
               r"the\s+disease)\b", re.I),
    re.compile(r"\b(?:treatment|chemo|chemotherapy|radiotherapy|surgery|operation|transplant)\b"
               r"[^.!?]{0,24}?\b(?:is\s+working|worked|went\s+(?:well|fine)|was\s+a\s+success|"
               r"has\s+worked)\b", re.I),
    re.compile(r"\b(?:tumou?r|lump|cancer|growth)s?\b[^.!?]{0,16}?\b(?:has|have)\s+"
               r"(?:gone|shrunk|shrinking|stopped\s+growing)\b", re.I),
    re.compile(r"\b(?:its|it\s+is|it\s+was|hes|she's|theyre|they're)\s+(?:shrinking|"
               r"stopped\s+growing|gone)\b", re.I),
    # "my wife got the all clear" is deliberately not here. The positive pool already answers it
    # well ("Brilliant. Really pleased for you."), so reading it would move a good reply to a
    # medical one for nothing: this reader is for the results a condolence was said over.
)

# The clear phrase has to be where the line ends, or the line is a report with a turn in it:
# "the scan came back clear but they want her back in a month" is a good result and a worry, and
# "That's a relief" said over the second half is the wrong reply. The tail is only words that add
# nothing to the result.
CLEAR_TAIL = re.compile(r"\s*(?:(?:now|again|today|thanks|thank\s+god|thankfully|thank\s+fully|"
                        r"finally|at\s+last|anyway|so\s+far|great|brilliant|"
                        r"so\s+(?:relieved|happy|pleased|glad)|relieved|what\s+a\s+relief)\s*)*"
                        r"[.!]?$", re.I)

# The line says the result came back the other way: "not in remission", "the scan wasnt clear",
# "they said it has spread". A negator in front of the result, or the straight opposite of it.
NOT_CLEAR = re.compile(r"\b(?:not|isnt|isn't|wasnt|wasn't|arent|aren't|werent|weren't|never|"
                       r"no)\s+(?:\w+\s+){0,2}?(?:\w+\s+)?(?:clear|benign|remission|normal|"
                       r"negative|gone|harmless)\b"
                       r"|\b(?:has|had)\s+spread\b|\bhasnt\s+(?:worked|helped)\b"
                       r"|\bdidnt\s+work\b|\bnot\s+(?:worked|working)\b", re.I)


def reads_as_a_clear_result(clean):
    """Whether a cleaned, lowercased line says a test or a treatment came back well.

    Said about anyone: "my mums cancer is in remission", "the biopsy was benign", "his treatment
    worked". The speaker is not the subject in half of these, so this does not use `ABOUT_THEM`,
    which is the guard for the person's own body ("i feel better").
    """
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return False
    if ASK_OPEN.search(text) or NOT_CLEAR.search(text) or NEGATED.search(text):
        return False
    if CONDITIONAL.search(text) or NOT_NEWS.search(text) or NOT_QUITE.search(text):
        return False
    for pattern in CLEAR_RESULT:
        for match in pattern.finditer(text):
            if CLEAR_TAIL.match(text[match.end():]):
                return True
    return False


def reads_as_settled(clean):
    """Whether a line says the thing they were worried about has passed, about anyone."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return False
    if ASK_OPEN.search(text):
        return False
    if CONDITIONAL.search(text):
        return False
    return any(match and not _denied(text, match.start(), match.end())
               and _a_bare_gone_is_not_the_news(text, match)
               for match in (pattern.search(text) for pattern in SETTLED))


if __name__ == "__main__":
    import sys
    for line in sys.argv[1:]:
        low = line.lower()
        print(f"{reads_as_good_news(low)!s:5} {reads_as_a_pass(low)!s:5} {line}")
