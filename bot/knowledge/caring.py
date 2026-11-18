"""Caring for somebody: the break from it, and the words for the last part of it.

The answers lane owns this domain. Most people who look after a parent, a partner or a
neighbour find out what help exists years late, and the questions about the help itself are
few: respite, and what a hospice and palliative care actually are. Every entry is keyed by the
thing asked about rather than by the wording, so "what is palliative care", "how do i get a
referral to a hospice" and "can i get a break from caring" each reach their own row.

The two money-and-rights rows used to be somebody else's on paper - Carer's Allowance named as
bot/knowledge/money.py's and the carer's assessment as bot/knowledge/lifeadmin.py's - and neither
file ever got one, so the questions fell to the search hedge ("what is carer's allowance") and to
the disabled person's bus pass ("can i get a carer's assessment"). They are here now, because
the line carries a carer in it and this is the carer's domain. Attendance Allowance is still
money.py's, with the two rates and form AA1.

Why its own domain: the money rows answer benefits as a figure, and the health rows answer a
symptom. These are neither - they are what a carer can claim or ask for, on behalf of somebody
else - and the lines carry another person in every one of them ("my dad", "mum"), so the
subject rows in money.py and health.py stand down where these answer.
"""
import re

from .lookup import entry

# The topics these lines arrive on: a benefit is money, a hospice is health, and "my mum" is
# family. answers.py declares the union of every domain's ANSWERS, so naming them here is all
# that is needed.
ANSWERS = ("money", "health", "family-and-parenting")

# The ways people ask what a thing is or how to get it, as the asking part of each key: a flat
# list of key phrasings is read as the subject alone and answers nothing but the definition
# ("how do i claim attendance allowance" missed it), while a (subject) x (asking) key makes the
# ask the second signal the matcher wants.
#
# It is for rows whose subject is the thing asked about - "respite", "hospice", "palliative care" -
# and never for a row whose subject half is a person being cared for ("care for my", "caring for
# my"). Those rows read a whole sentence about a person either way, so the asking words alone make
# any of them the answer and the row's own second half is what tells the questions apart. Such a
# row wants its second half as its ask, which is what `carer-burnout` and `_THE_LOAD` do below.
_ASKING = ("how", "what", "whats", "who", "which", "can i", "could i", "do i", "does", "is",
           "are", "should i", "much", "many", "claim", "claiming", "apply", "applying",
           "qualify", "qualifies", "eligible", "entitled", "worth", "explain", "mean",
           "means", "about", "tell", "long", "pay", "paid", "start", "receive", "receiving")

# Nobody is being asked about their own job with one of these in the line: "i want to work in a
# hospice" and "what does a hospice nurse do" are career questions, and "volunteer" is somebody
# offering rather than somebody caring.
_NOT_THE_JOB = ("job", "jobs", "work at", "work in", "working at", "working in", "career",
                "volunteer", "volunteering", "salary", "interview", "nurse do", "nurses do",
                "training to be", "study to be")

# "Caring for" a person is the question in this file. A dog or a cat is not: the pet files
# answer those, and "caring for my dog is exhausting" was the dog-day answer until the carer row
# learned the word "caring". The animal is read where the person sits, though - an avoid list is
# read loosely (lookup.py: the words only have to be somewhere in the line), so listing the
# animals took the carer's answer off "caring for my mum is exhausting and i also have a dog".
# Only the animals a pet card actually answers are listed: a horse, a snake and a budgie stand
# down to a houseplant card or a shrug, and a carer's card is a better wrong answer than either,
# so they keep it, exactly as they had it on main.
_A_KEPT_ANIMAL = (r"(?:dogs?|puppies|puppy|pups?|cats?|kittens?|rabbits?|guinea pigs?|hamsters?|"
                  r"fish|goldfish|fish tank|tropical fish)")
# "caring for my dog", "looking after our two cats", "caring for my elderly cat" - the caring
# verb with the animal as its object. One adjective is allowed; a second noun is not, because
# "caring for my mum and my dog" has the person in front and is a carer's line.
_AN_ANIMAL_CARED_FOR = re.compile(
    r"\b(?:caring for|care for|caring of|looking after|look after|i care for|i look after)\s+"
    r"(?:my|our|the|a|an|his|her|their|two|three|both|elderly|old|sick|poor|new|little|baby|"
    r"big)?\s*(?:\w+\s+){0,1}?" + _A_KEPT_ANIMAL + r"\b")
# The animal as the thing that wears the person out - "my dog is exhausting me" - is the pet
# card's too, and it is the same reading one step round.
_AN_ANIMAL_WEARS_ME_OUT = re.compile(
    r"\b(?:my|our|the)\s+(?:\w+\s+){0,1}?" + _A_KEPT_ANIMAL +
    r"\s+(?:is|are|has|have|keeps?|takes|took)\b")


def _an_animal_is_the_one_cared_for(reading):
    """False when the line's caring is for an animal: the pet files answer that, and this card is
    about a person. Read from the line, because the animal only steps aside when it sits where
    the person sits."""
    said = " ".join(str((reading or {}).get(key) or "") for key in ("clean", "text", "plain"))
    said = " " + re.sub(r"[^a-z0-9' ]+", " ", said.lower()) + " "
    if _AN_ANIMAL_CARED_FOR.search(said) or _AN_ANIMAL_WEARS_ME_OUT.search(said):
        return False
    return True


# The load the carer is carrying, in the words people actually use for it. It is the second
# half of `carer-burnout`'s key and it is the row's ask as well: the row answers the carer's own
# state, so one of these has to be in the line, and naming a person ("care for my dad") is not
# enough on its own. Keeping the two in one list is what stops them drifting apart - the words
# added for "caring for my nan is tiring" were in the key and not in the ask, and the ask is what
# the reading has to find.
_THE_LOAD = ("cope", "coping", "cope with", "cant cope", "cannot cope", "not coping",
             "how do i cope", "how do i keep going", "keep going", "exhausted", "knackered",
             "worn out", "wearing me out", "wears me out", "burnt out", "burned out",
             "burnout", "burn out", "overwhelmed", "struggling", "struggling to cope",
             "no time for myself", "no life", "no life of my own", "on my own with it",
             "all on me", "it never stops", "never get a break", "no help", "help me",
             # "caring for my nan is tiring" was answered "Noted: caring for your nan is
             # tiring": the card wanted a verb of collapse and the plain words for it were
             # missing. They are the same question in a quieter voice.
             "tiring", "so tiring", "draining", "is a lot", "a lot of work", "hard work",
             "is hard", "hard going", "knackering", "shattered", "worn down", "getting to me",
             "help for carers", "support for carers", "look after myself",
             "run ragged", "dont know how much longer")

# The carer, and the person they care for, as the line names them. It is the first half of the
# key, and it says who is speaking, never what is wrong.
_THE_CARER = ("carer", "carers", "carer burnout", "carer stress", "unpaid carer",
              "full time carer", "i am a carer", "im a carer", "being a carer",
              "caring for my", "care for my", "caring for a", "care of my")


ENTRIES = [
    entry("respite-care", (("respite", "respite care", "respite break",
                           "short break from caring", "a break from caring"), _ASKING),
          "Respite care is a break for the person doing the caring, and it comes in small "
          "pieces: a few hours a week at a day centre, somebody sitting with them so you can go "
          "out, or a week in a care home so you can have a holiday. Arrange it before you are "
          "desperate, because the good places have a waiting list. The council can arrange it "
          "after a carer's assessment and means-tests the person you care for, not you; hospices "
          "and charities often have free day places and short stays; and the GP or district "
          "nurse knows what exists locally, which is usually more than the council website says.",
          ask=_ASKING, avoid=_NOT_THE_JOB,
          explain=True, bias=1),
    entry("hospice", (("hospice", "hospices", "hospice care"), _ASKING),
          "A hospice is for controlling pain and symptoms and for supporting the person doing "
          "the caring - it is not a place people are sent only to die. Most of what they do is "
          "day services, help at home and short stays, and people are usually referred months "
          "before the end, which is the whole point: it is easier to sort pain out early than in "
          "a crisis. The care is free (charity and NHS funded) and needs a referral from the GP, "
          "district nurse or hospital team, so ask for one; you can also ring the hospice and "
          "ask what they have, because they answer that question all day.",
          ask=_ASKING, avoid=_NOT_THE_JOB + ("how does the hospice work",),
          explain=True, bias=1),
    entry("palliative-care", (("palliative care", "palliative", "end of life care",
                              "palliative care team"), _ASKING),
          "Palliative care is treatment that controls symptoms and keeps somebody comfortable "
          "when a cure is not the aim - and it can run for years alongside treatment for the "
          "illness, so it does not mean care has been given up on. It is about pain, "
          "breathlessness, sickness, sleep and worry, it happens wherever the person is (at "
          "home, in a hospice, in hospital or in a care home), and the GP or specialist nurse "
          "can refer. Asking for it early is the thing that makes the last months better rather "
          "than the last weeks.",
          ask=_ASKING, avoid=_NOT_THE_JOB,
          explain=True, bias=1),
    # The question underneath most of this file: not what a service is, but how to keep going.
    # "how do i cope as a carer" was answered with the disabled person's bus pass, because that
    # row keys the word "carer" for the companion who travels free with the pass holder, and no
    # row anywhere held the ordinary sentence people type at 11pm. The help that exists is the
    # carer's assessment, and the rest of the answer is about taking the break before it is a
    # crisis, which is what the people asking actually need to hear.
    entry("carer-burnout",
          (_THE_CARER, _THE_LOAD),
          "The first thing to ask for is a carer's assessment from your council: it is free, it "
          "is about you rather than the person you care for, and it can pay for someone to sit "
          "with them so you get a few hours back each week. Then tell your GP that you are "
          "caring - it goes on your notes, it counts for your own health, and it changes what "
          "they offer you. Ring Carers UK on 0808 808 7777 once, because they know the local "
          "schemes and the grants better than any website does, and ask your employer about "
          "flexible hours and unpaid carer's leave, which is now a day-one right. Book the break "
          "before you need it: a few hours a week arranged in advance is the difference between "
          "coping and going under, and taking it is not a failure.",
          # The ask is the load, not the question. With the plain asking words here, "how do i
          # care for my dad" scored the subject "care for my" plus the "how" and got this card,
          # and the how-to-care line for a parent is `care-for-elderly-parent`'s, with the needs
          # assessment: `tests.test_a_carer_and_a_mad_day` says so, and it was red on main.
          ask=_THE_LOAD,
          # The money row holds the allowance and the lifeadmin row the assessment itself, and a
          # bus pass, a blue badge and a Motability car are other answers: a figure or a scheme is
          # not this question, and a confident wrong card is worse than the shrug it replaced.
          guard=_an_animal_is_the_one_cared_for,
          avoid=_NOT_THE_JOB + (
                                "carer allowance", "carers allowance", "carer's allowance",
                                "allowance", "allowances", "benefit", "benefits", "pip",
                                "universal credit", "tax credit", "bus pass", "pass",
                                "travel", "blue badge", "badge", "motability", "money",
                                "paid", "pay", "claim", "claiming", "qualify",
                                "assessment", "how much", "how many hours"),
          bias=1, report=True),
]

# ---- what a carer can claim, and what they can ask for -----------------------
#
# Both of these were missing from every file. "what is carer's allowance", "can i claim carer's
# allowance", "do i qualify for carers allowance" and "how much do carers get" were the search
# hedge; "can i get paid for looking after my mum" was the needs assessment, which is the
# council's side of it, not the benefit; and "can i get a carer's assessment" reached the
# disabled person's bus pass, because that row keys the word "carer" (a companion travels free
# with the pass holder) and the line asks "can i get". The subject of the first row is an amount
# of money for caring and the subject of the second is the assessment, so the two lines that
# name them are answered by name.
# "get paid for" on its own is every overtime, sick-pay, training and jury-service line, so the
# phrase only counts when the caring is named with it: "can i get paid for overtime" is the
# contract's question, "get paid for looking after my mum" is this one.
_CARERS_PAY = ("carer's allowance", "carers allowance", "carer allowance", "carers allowance",
               "carer's credit", "carers credit", "carer credit",
               "paid for caring", "paid to care", "pay for caring", "money for caring",
               "paid for looking after", "paid to look after",
               "get paid for caring", "get paid to care", "get paid for looking after",
               "get paid to look after", "get paid as a carer", "paid as a carer",
               "get paid to be a carer", "paid for being a carer",
               "carer's allowance rate", "carers allowance amount")

_CARERS_ASSESSMENT = ("carer's assessment", "carers assessment", "carer assessment",
                      "assessment as a carer", "carer's needs assessment",
                      "carers needs assessment", "support as a carer", "help as a carer",
                      "help for carers", "support for carers", "carer support",
                      "what help can i get as a carer")

# A line about being paid to look after somebody's children is a job, and a line about working
# in a care home is a career: neither is the benefit, which is paid for caring for an adult who
# gets a disability benefit. And the bus pass, the blue badge and the travel pass each have
# their own answer, which the word "carer" sits inside as a companion's free travel.
_NOT_THE_CARERS_MONEY = _NOT_THE_JOB + ("childminder", "childminders", "childminding",
                                        "babysit", "babysitting", "nanny", "fostering",
                                        "foster", "adoption", "nursery", "au pair",
                                        "care worker", "care assistant", "support worker",
                                        "care home job", "agency work")

def _the_care_is_for_a_grown_up(understood):
    """A child named as the one being looked after is a paid favour, not the carer's benefit.

    "can i get paid to look after my friend's kids" is childcare, and the allowance is for
    caring for someone who gets PIP daily living, Attendance Allowance or DLA. A line that
    says carer or caring with the child in it still counts: a parent caring for a disabled
    child can claim, and that question names the benefit.
    """
    line = str(understood.get("clean") or understood.get("text") or "").lower()
    if not re.search(r"\b(?:kid|kids|child|children|childminding|toddler|toddlers|"
                     r"babies|baby)\b", line):
        return True
    return bool(re.search(r"\bcarers?'?\s*(?:allowance|credit)\b|\bcaring\b|\bcarer\b", line))


ENTRIES += [
    entry("carers-allowance", (_CARERS_PAY, _ASKING),
          "Carer's Allowance is about £83 a week for caring 35 hours or more for someone who "
          "gets PIP daily living, Attendance Allowance or DLA middle or higher care. You must be "
          "16 or over, not in full-time education, and earning under about £200 a week after "
          "tax. Claim on gov.uk and date it from the day you started, because it backdates three "
          "months; earn too much and Carer's Credit keeps your NI record going instead.",
          ask=_ASKING, avoid=_NOT_THE_CARERS_MONEY, guard=_the_care_is_for_a_grown_up,
          explain=True, bias=1),
    entry("carers-assessment", (_CARERS_ASSESSMENT, _ASKING),
          "Ask the council's adult social care team for a carer's assessment. It is free, it is "
          "about your needs and not theirs, and you can ask without telling them. It takes about "
          "an hour, at home or on the phone, and it can bring respite hours, a direct payment "
          "you spend yourself, training and a number to ring in the worst moments. Say \"I would "
          "like a carer's assessment\" and get what they agree in writing.",
          ask=_ASKING, avoid=_NOT_THE_CARERS_MONEY + ("bus pass", "freedom pass", "travel pass",
                                                      "blue badge", "companion", "motability",
                                                      "disabled person"),
          explain=True, bias=1),
]

# ---- the other way round: the family does the caring, and the line says so ---------
#
# "my son cares for me" has nobody answering it. The rows above all want the caring said in the
# first person ("i care for my mum"), the money rows want the benefit named, and a houseplant row
# reads "care for" as its own: every line of this shape was answered "Water when the top couple
# of centimetres of compost is dry". That is the wrong answer and a confusing one, from a file
# about the garden, to a person talking about their own care.
#
# What a person in that position is short of is the same three things everybody is short of,
# and none of them is sent automatically: what the carer can claim, what they can claim
# themselves, and the assessment that buys a few hours back.
_LOOKED_AFTER_ME = ("cares for me", "care for me", "caring for me", "cared for me",
                    "cared for by", "looks after me", "look after me", "looking after me",
                    "looked after me", "looked after by")
_MY_FAMILY_CARER = ("son", "sons", "daughter", "daughters", "husband", "wife", "partner",
                    "mum", "mother", "dad", "father", "sister", "brother", "grandson",
                    "granddaughter", "grandchild", "niece", "nephew", "children", "kids",
                    "family", "friend", "friends", "neighbour", "neighbours", "aunt", "uncle",
                    "cousin", "relatives", "carer", "carers")
# The more specific rows keep the lines that name their own subject: a benefit asked about by
# name is the allowance row's, a carer at the end of their rope is the burnout row's, and a
# break or an assessment is its own question.
_NOT_THIS_ROW = _NOT_THE_JOB + ("allowance", "allowances", "credit", "benefit", "benefits",
                                "claim", "claiming", "qualify", "qualifies", "entitled",
                                "pip", "attendance", "cope", "coping", "cant cope",
                                "cannot cope", "exhausted", "burnt out", "burned out",
                                "struggling", "overwhelmed", "tiring", "worn out", "no life",
                                "respite", "assessment", "a break", "how do i get help")

ENTRIES += [
    entry("my-family-cares-for-me", (_LOOKED_AFTER_ME, _MY_FAMILY_CARER),
          "Two things are worth starting this week, because neither is sent automatically. "
          "Whoever looks after you for 35 hours a week or more can claim Carer's Allowance, "
          "about \u00a383 a week, and it keeps their National Insurance record going too. There is "
          "money for you as well: Attendance Allowance if you are over pension age, PIP if you "
          "are younger, neither of them means-tested, and both unlock more on other benefits. "
          "Then ask the council for a carer's assessment - it is free, it is about their needs, "
          "and it can pay for someone to sit with you so they get an evening back.",
          avoid=_NOT_THIS_ROW, bias=1),
]
