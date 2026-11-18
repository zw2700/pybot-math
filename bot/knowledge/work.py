"""Work: getting a job, and the days after it.

Keyed by the situation someone brings (a colleague taking the credit, a deadline brought
forward, a first day on Monday), so one entry answers the question and the vented version of
it. Where a script helps, the entry gives the words to say, because that is the part people
are actually stuck on. Nothing here needs a jurisdiction: the advice is about how to act, and
where rights are involved it says to check the contract or a free service rather than
guessing at the law.
"""
import re

from ..understanding import lexicon
from .lookup import IMPROVE, entry
from .wording import NERVES_BODY, TOLD_OFF, nerves_opening
from . import lookup

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("work",)


# Feeling words: a line that carries one of these wants the advice acknowledged, not just handed
# over. One helper reads the line once, so every entry that needs it stays short.
NERVES = ("nervous", "nerves", "scared", "terrified", "dread", "dreading", "worried", "panic",
          "panicking", "anxious", "freaking out", "shaking", "petrified")
GOOD_NEWS = ("got the job", "got the role", "got it", "start monday", "starting monday",
             "start next week", "starting next week", "offer came through", "they said yes",
             "said yes", "accepted the offer", "i start")
# "raise" mostly does not mean pay: raising money, funds, a family or prices are all lines the
# pay entry must pass on, and the two raise entries share the list so it only has to be changed
# in one place.
# The person doing the managing asks a different question from the one working beside them: "she
# does nothing" is a colleague's complaint, "one of my staff does nothing" is the manager's, and
# "my team is burnt out" is a manager's too. Every row about running a team carries this list on
# its ask side, so a new row does not spell the manager out again, and a line that only says what
# is wrong ("my team is burnt out and i dont know what to do") still counts as asking.
MANAGING_ASKS = ("manager", "managing", "manage", "managed", "team", "my team", "staff",
                 "my staff", "reports", "report to me", "my report", "line manage", "line manager",
                 "apprentice", "trainee", "new starter", "the new guy", "one of my staff",
                 "someone on my shift", "i lead", "i run", "shift", "rota", "work",
                 "what do i do", "what should i do", "what can i do", "dont know what to do",
                 "don't know what to do", "not sure what to do", "no idea what to do",
                 "how", "help", "deal", "handle", "deal with", "say", "tell", "talk",
                 "word", "approach",
                 # "first" was in this list on its own and that one word was enough to hand a
                 # history question to a work card: "first world war" is a name, and with "war"
                 # read as a form of "warring" the two together made "what caused the first world
                 # war" a row about two colleagues who will not speak. A first-time manager is
                 # the question this word was here for, so it is said as that and not as the word.
                 "first team", "my first team", "first time managing", "first time manager",
                 "first time in charge", "first time as a manager", "newly promoted",
                 "just been made a manager", "new manager")
NOT_PAY_RAISE = ("raise money", "raise funds", "money for", "funds for", "fundraising",
                 "charity", "sponsor", "crowdfund", "awareness",
                 "raise a child", "raise children", "raise a family", "raise kids",
                 "raise my kids", "raising a child", "raising kids")
# The answer to saying no, shared by the entry keyed on the situation and the one keyed on the
# bare ask, so the two cannot drift apart.
SAY_NO_POLITELY = (
    "Keep it to one short sentence and stop: \"I can't take that on this week.\" Offer what "
    "you can do instead - \"I could do Monday morning\" - and if they push back, repeat the "
    "same sentence in the same words. One sentence is a boundary; three of apology are an "
    "invitation to talk you out of it.")


# "what can i make with leftover rice for lunch" carries the word lunch and is a cooking
# question: the break rule only answers when the line is about a job at all.
BREAK_WORK_CUES = ("shift", "shifts", "boss", "manager", "employer", "rota", "contract",
                   "colleague", "colleagues", "employment", "at work", "in work", "workplace",
                   "unpaid", "cut short", "cutting my lunch", "skip", "skipped", "skipping",
                   "20 minute", "20 minutes", "half an hour", "on my feet", "every shift",
                   "payslip", "paid break", "no break", "never get a break", "lunch break",
                   "break at work", "breaks at work", "on shift", "work through",
                   "through lunch", "through my lunch",
                   # the complaint names the break by its length - "i only get 20 mins for
                   # lunch" - which is the same question as "am i entitled to a break"
                   "mins for lunch", "minutes for lunch", "minute for lunch",
                   "hour for lunch",
                   # "am i entitled to a break", "how many hours can i work without a break"
                   "entitled", "entitlement", "without a break", "without breaks",
                   "without my break", "breaks am i entitled", "legally",
                   # "how long is my break", "how long are my breaks at work": the break is the
                   # person's own and the length is what they asked about. Without these the
                   # line reached the healing row in body.py on "how long" and "break" and was
                   # told how long a bone takes; that row stands down for the same shapes now
                   # (`_not_a_break_from_work`), and this is what answers instead.
                   "my break", "my breaks", "our break", "our breaks",
                   "how long is the break")


# The words that make a line a question about a job, for the fallback at the end of the pay and
# hours rule: without one of these the entry was reached by accident and passes.
# The words that make a "self employed" line a question about status rather than about what to
# charge. "have set hours" is most of them: the price row keys on "set" for "set your rate".
STATUS_TELL = ("says im self employed", "says i am self employed", "says i'm self employed",
               "tells me im self employed", "tells me i am self employed",
               "self employed but", "but i am self employed", "but im self employed",
               "set hours", "fixed hours", "regular hours", "only one client",
               "one client", "they tell me when", "they decide when", "umbrella company",
               "tells me when", "tells me to come in", "tells me what to do",
               "decides my hours", "decides when i work", "i have to be there",
               "employment status", "am i employed", "am i self employed",
               "employee or self employed", "self employed or employed")

WORK_SUBJECT = ("hours", "hour", "pay", "paid", "unpaid", "contract", "rights", "entitled",
                "entitlement", "law", "legal", "illegal", "minimum", "boss", "manager",
                "employer", "work", "working", "job", "shift", "shifts", "rota", "overtime",
                "holiday", "leave", "breaks", "break", "rest", "union", "acas", "payslip")

# The words that make `law` mean a relation rather than a statute. "my in laws are coming for
# lunch sunday" was answered "Your contract is the place to look first: it sets your hours, your
# breaks and whether overtime is paid" because `WORK_SUBJECT` carries `law` and `in laws` spells
# it; `my mother in law is coming sunday` got the visit card, so the plural was the whole fault.
IN_LAW = re.compile(r"\bin\s*-?\s*laws?\b")
# A line can hold a relation and a job at once - "my mother in law is my boss", "my in laws want
# me to quit my job" - and the job is the question there, so these keep the contract answer. The
# relation words are not in this list; the point is the job, said plainly.
IN_LAW_JOB = ("job", "jobs", "work", "working", "worked", "employer", "boss", "manager",
              "shift", "shifts", "rota", "contract", "overtime", "payslip", "holiday",
              "annual leave", "sacked", "dismissed", "redundant", "redundancy", "hours",
              "wages", "union", "acas", "self employed", "resign", "resigning")

# A break in a bone is not a break in a shift, and "break" alone was enough to reach the fallback
# below: "what's the difference between a sprain and a break" and "whats the difference between a
# fracture and a break" were both answered "Your contract is the place to look first". The words
# that say the body is what is hurt hand the line back to the health entries, unless the line is
# about a job as well ("i have sprained my ankle and i am on my feet all day at work"), which keeps
# its own answer.
INJURY_WORDS = ("sprain", "sprains", "sprained", "strain", "strains", "strained",
                "fracture", "fractures", "fractured", "broken bone", "broken bones",
                "broke my", "broken my", "broke a", "x-ray", "xray", "a&e", "casualty",
                "ligament", "ligaments", "tendon", "tendons", "swollen", "swelling")


# The word that makes a travel line a question about the money rather than about the ticket.
# The expenses row keys "ticket", "tickets", "fare" and "fares" beside "train", "travel", "taxi",
# so every one of these was answered with "check the policy before you spend": "i lost my train
# ticket", "can i change my train ticket", "is my train ticket valid on any train". None of those
# is a claim: the row's whole answer is how to get the money back afterwards, so it stands down
# until the line says money is coming back.
CLAIMING_WORDS = ("claim", "claims", "claimed", "claiming", "expense", "expenses", "receipt",
                  "receipts", "reimburse", "reimbursed", "reimbursement", "mileage", "allowance",
                  "tax", "payroll", "submit", "how much can i", "back", "policy", "deadline",
                  "refund", "refunded")



# A body part that hurts at work is a body question, not an accident report.
#
# "my back hurts at work" and "my knee hurts at work" were both handed "Tell your manager in
# writing the same day ... put it in the accident book", because the health-and-safety entry keys
# "hurt at work" and "<body part> hurts at work" holds it. The lines either side of them were
# right: "i hurt my back at work" and "my back aches after work" got the back card, and "my
# shoulder is sore from work" the tendon card. What separates them is the verb. A part that
# *hurts* - hurts, aches, is sore, is killing me - is the body answering, and "hurt myself",
# "injured", an accident, a hazard, a slip or a fall is the report.
_A_BODY_PART_THAT_HURTS = re.compile(
    r"\b(?:my|his|her|their|our|the)\s+"
    r"(?:(?:left|right|lower|upper|whole|other)\s+)?"
    r"(?:" + "|".join(sorted(lexicon.BODY_PARTS, key=len, reverse=True)) + r")\s+"
    r"(?:is\s+|are\s+|feels\s+|feel\s+|has\s+been\s+|have\s+been\s+|been\s+)?"
    r"(?:really\s+|properly\s+|absolutely\s+|so\s+|very\s+|killing\s+)?"
    r"(?:hurts|hurting|hurt|aches|aching|ache|sore|stiff|killing|kills|throbbing|throbs|"
    r"agony|numb|numbness|twinge|twinges)\b")
# The words that make it a report whatever else the line says: something happened, and the
# record is the point. "my back hurts after i fell at work" keeps the accident book.
_A_THING_THAT_HAPPENED = re.compile(
    r"\b(?:hurt\s+myself|injured|injury|accident|hazard|slipped|slipping|fell|fall|fainted|"
    r"spilled|no\s+gloves|no\s+training|guard\s+off|near\s+miss|report)\b")


_SOMEONE_ELSE = re.compile(
    r"(?<![a-z0-9])(my (husband|wife|partner|son|daughter|friend|brother|sister|mum|mom|dad|"
    r"father|mother|colleague|cousin|neighbour|neighbor|flatmate|roommate)|he was|she was|"
    r"they were|his job|her job|their jobs?)(?![a-z0-9])")
_MY_OWN = re.compile(r"(?<![a-z0-9])(me|my|i|i'm|im|ive|i've|myself)(?![a-z0-9])")


def _it_is_their_own_dismissal(understood):
    """True when the person is asking about their own sacking, not telling us someone else's.

    The bare event words are the subject now, so "my husband was sacked from his job" reached the
    interview answer; that line is news about a husband and belongs with the comfort card. A line
    that says "me" or "my job" as well is the person's own, so "my boss sacked me" still counts.
    """
    said = " " + str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower() + " "
    if not _SOMEONE_ELSE.search(said):
        return True
    return bool(re.search(r"(?<![a-z0-9])(me|my job|my last job|my own job|mine|myself)(?![a-z0-9])", said))


_CHOOSING_A_NAME = re.compile(
    r"(?<![a-z0-9])(use as|use for a|put as|put down as|who can i|who can be|who could i|"
    r"who should i|who do i ask|who do i use|who can be my|no experience|no work experience|"
    r"never had a job|never worked)(?![a-z0-9])")


def _not_choosing_a_name(understood):
    """False when the line is choosing who to name, which is the who-to-ask card's question.

    The check card reads the bare noun, so "i have no experience what can i use as a reference"
    reached it and got told the questions a reference check asks - an answer to a question
    nobody asked, from a person with no manager to name. The words that say "which name do I
    put down" stand the check card down; "no experience" and "first job" are no longer part of
    its key, because they belong to the person choosing, not to the check.
    """
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return not _CHOOSING_A_NAME.search(said)


_WRITING_A_REFERENCE = (
    "write", "writing", "written", "draft", "drafted", "word", "worded", "wording",
    "letter", "letters", "recommend", "recommendation", "compose", "put together",
    "what should i say", "how do i say", "give a reference", "give someone a reference",
    "give him a reference", "give her a reference", "given a reference", "asked to write",
    "asked me to write", "for a colleague", "for a student", "for an employee",
    "for my colleague", "for my student", "for my employee", "for a leaver", "for staff",
)


def _writing_one_not_needing_one(understood):
    """True when the line is somebody writing a reference, not somebody needing one.

    Three questions share the noun. "Who should I use as a reference" is the person job-hunting
    (the references entry), "will they check my references" is what happens afterwards (the
    reference-check entry), and "how do I write a reference letter" is the manager's half (this
    entry). A line only reaches this card when it says the letter is being written or given:
    "do i need a reference for a first job" and "do i have to give a reference for a leaver"
    were both answered with how to word one, because the bare noun plus a stray word was enough.
    """
    return _said(understood or {}, _WRITING_A_REFERENCE)


def _not_a_body_part_that_hurts(understood):
    """False when the line is a part of the body hurting, so the body cards answer it.

    The health-and-safety entry keeps every line about something that happened at work - a slip,
    a fall, an injury, a hazard to report - and stands down when the line is only a part that
    hurts, because "my back hurts at work" is the back question with a place in it.
    """
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not _A_BODY_PART_THAT_HURTS.search(said):
        return True
    return bool(_A_THING_THAT_HAPPENED.search(said))


def _it_is_about_claiming(understood):
    """False when the line holds a ticket but no money coming back."""
    return _said(understood or {}, CLAIMING_WORDS)


# A line that already says how they will ask is a line about the asking, not about whether to
# flex: "is it worth asking to go part time at work" was answered with the flexible-work card
# ("ask with a plan, not a preference") where the wording row has a script to say, and the card
# is for a line that has decided and wants the arrangement.
_ASKING_TO_ASK = re.compile(
    r"\b(?:ask|asks|asking|asked|tell|tells|telling|told)\b[^?]{0,25}?\b(?:to|for)\b", re.I)


def _the_asking_has_its_own_answer(understood):
    """False when the line is about how to ask for the arrangement, which the wording row owns."""
    return not _ASKING_TO_ASK.search(_said_text(understood or {}))


# A war between countries is not two people who cannot work together. The quarrel row keys
# "warring", and the word family folds that to "war" - the commonest noun in the other world - so
# "what was the cause of the first world war" was answered with the work rule for a clash between
# two members of staff, and so were "when did the first world war end", "who won the first world
# war", "how did the korean war end" and "what were the causes of the hundred years war". A war
# named as a thing stands the row down, and the history rows take the line.
A_NAMED_WAR = re.compile(
    r"\b(?:(?:world|cold|civil|great|first|second|hundred years|korean|vietnam|gulf|iraq|"
    r"afghan|syrian|ukrainian|crimean|boer|trench|nuclear|trade|price)\s+war|"
    # "a war of words" and "a war of nerves" between two people are the quarrel row's own lines,
    # so the metaphor is not a war named as a thing
    r"war\s+(?:in|of|on|against)\s+(?!words|nerves)\b|"
    r"ww1|ww2|wwi|wwii|battle of|armistice)\b", re.I)


def _a_named_war(understood):
    """False when the line names a war, which is nobody's clash with a colleague."""
    return not A_NAMED_WAR.search(_said_text(understood or {}))


def _said_text(understood):
    """The line as the person typed it, for the replies that say their own word back."""
    return str(understood.get("clean") or understood.get("text") or "")


# A who-ask is a route: "who do i talk to about a problem at work" is asking which person to go
# to, not how to give a talk. The presentation row keys the bare words "talk", "speak" and "present"
# against "work", so it claimed it and answered with slides. The shape is checked, not the
# wording, because asking who to approach has no fixed phrasing: "who do i contact about my sick
# pay", "which number do i ring about the rota", "who should i speak to about my hours".
_WHO_TO_GO_TO = re.compile(
    r"^\s*(?:so |ok |okay |right |and |but |then )*"
    r"(?:who|who's|whos|whose|whom|which (?:person|service|number|office|department|team)|"
    r"where do i)\b[^?]{0,60}?"
    r"\b(?:talk|speak|ask|ring|phone|call|contact|complain|report|write|go|turn|raise)\b")


def _a_who_ask_is_a_route(understood):
    """False when the line is asking which person or office to approach."""
    return not _WHO_TO_GO_TO.search(_said_text(understood).lower())


def _said(understood, phrases):
    """True when the line uses one of these words or phrases (whole words, case-blind)."""
    clean = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    clean = re.sub(r"[^a-z0-9' ]+", " ", clean)
    for phrase in phrases:
        if re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", clean):
            return True
    return False


# Whose tears are these. Both crying rows read the same words - "cry", "tears", "in a meeting" -
# and the line itself says who is crying: "i burst into tears at work in front of my boss" is the
# person writing, and it was answered with "give them a minute and a way out", which is advice for
# the person sitting beside them. The other way round too: "a girl at work cries every week" was
# read as the speaker's own tears, because the row for someone else's tears named a colleague and
# a team member but not a girl.
#
# The person writing is the one crying when a first-person word sits within four words of the cry
# word and nobody else is named in between. "i made my colleague cry" and "i saw my boss in tears"
# put someone else in that window, so they stay the other person's.
_CRY_WORD = re.compile(
    r"\b(?:cry|cried|crying|cries|sob|sobs|sobbed|sobbing|tears|tearful|"
    r"(?:broke|breaking|breaks|break)\s+down|(?:welled|welling|wells)\s+up|choked\s+up)\b",
    re.I)
_FIRST_PERSON = re.compile(r"\b(?:i|im|i'm|ive|i've|me|my|myself)\b", re.I)
_ANOTHER_PERSON = re.compile(
    r"\b(?:colleague|colleagues|coworkers?|co-workers?|boss|bosses|manager|managers|supervisor|"
    r"team|teammate|staff|member|someone|somebody|she|her|hers|he|him|his|they|them|their|"
    r"girl|woman|man|lad|bloke|guy|mate|friend|partner)\b",
    re.I)
_NOBODY_ELSE = re.compile(r"\b(?:no ?one|nobody)\b", re.I)


def _whose_tears(text):
    """'mine' when the person writing is crying, 'theirs' when it is someone else, else None."""
    words = re.findall(r"[a-z']+", str(text or "").lower())
    for i in range(len(words)):
        said = " ".join(words[i:i + 2])
        if not (_CRY_WORD.fullmatch(words[i]) or _CRY_WORD.fullmatch(said)):
            continue
        near = " ".join(words[max(0, i - 4):i])
        # "my boss made me cry", "he reduced me to tears" and "she upset me and i cried" name
        # somebody else and the person crying is still the one writing: the pronoun in front of
        # the verb is the object of it. Read that before the other-person test, or the speaker
        # is handed advice on how to look after the person who upset them.
        if i and words[i - 1] in ("me", "us", "myself"):
            return "mine"
        if _NOBODY_ELSE.search(near):
            return "mine"
        if _FIRST_PERSON.search(near) and not _ANOTHER_PERSON.search(near):
            return "mine"
        if _ANOTHER_PERSON.search(near):
            return "theirs"
    return None


def _my_own_tears(understood):
    """False on the lines where someone else is the one crying."""
    return _whose_tears(_said_text(understood or {})) != "theirs"


def _someone_elses_tears(understood):
    """False on the lines where the person writing is the one crying."""
    return _whose_tears(_said_text(understood or {})) != "mine"


# A threat of violence at work is a crime before it is a grievance: the bullying answer is the
# right advice for the conduct, but a person who has just said someone is threatening them needs
# the police signpost in the first sentence, not four lines down a grievance procedure. Only the
# lines that name violence get it, so "my boss keeps undermining me" keeps the plain answer.
VIOLENT_AT_WORK = ("threat", "threats", "threaten", "threatens", "threatened", "threatening",
                   "violence", "violent", "attack", "attacked", "attacking", "assault",
                   "assaulted", "punch", "punched", "hit", "hits", "hurt", "hurts", "kill",
                   "killed", "stab", "stabbed", "knife", "weapon", "grabbed", "grabs",
                   "shoved", "shoves", "kicked", "kicks")

_BULLY_REPLY = ("Write it down while it is fresh: date, what was said or done, who saw it. Then "
                "tell someone with authority - your manager if it is a colleague, their manager "
                "or HR if it is your manager - in writing, asking for a meeting and what you want "
                "to change. Keep the tone flat and factual. Your contract and your workplace's "
                "grievance policy set out the steps; a free advice line like ACAS or Citizens "
                "Advice will tell you where you stand, and you do not have to sort it out before "
                "you report it.")


# The way back into a job after time away is one subject in three shapes: the nerves of a first
# week, a return from maternity leave, and a return after being signed off. Every one of them was
# handed the pumping-room card in family.py ("ask for a private room with a lock, a chair and a
# socket"), which answers a question nobody asked, and the rest were an echo of the line back.
_GOING_BACK = ("going back to work", "going back to my job", "go back to work",
               "going back to the office", "back to work", "back at work", "back in work",
               "returning to work", "return to work", "returning to my job",
               "starting back at work", "first day back", "first day back at work",
               "gone back to work", "went back to work")

# The line has to say something about this return, not only that it is happening: "when can i go
# back to work" after an injury is the injury's question, and "how long before i can go back to
# work" is a healing time. The words below are the ones a person uses about the return itself.
_GOING_BACK_LINE = ("nervous", "anxious", "anxiety", "worried", "worry", "dreading",
                    "dread", "scared", "guilty", "excited", "maternity", "paternity",
                    "parental", "baby", "leave", "first day", "months", "exhausted",
                    "knackered", "shattered", "tired", "drained", "off sick", "sick note",
                    "signed off", "phased", "fit note", "stress", "burnout", "depressed",
                    "depression", "next week", "next month", "on monday", "tomorrow",
                    "this week", "soon", "my wife", "my husband", "my partner", "sickness",
                    "illness", "unwell", "after being ill", "time off", "hate",
                    "hate it", "regret", "miserable", "cant face", "can't face",
                    # "i dont want to go back to work" and "not looking forward to going back"
                    # said nothing this row keys on, so the line got no answer at all; the wish
                    # not to go is the question, and it is its own reading below.
                    "dont want to go back", "don't want to go back", "do not want to go back",
                    "dont want to return", "don't want to return", "not looking forward",
                    "dreading going back", "dreading it", "cant face going back",
                    "can't face going back")


_GOING_BACK_WRONG = (
    "Give it six weeks before you judge it: the first weeks back are a bad test of a job, "
    "because everything is new, tiring and out of your hands. Write down what is actually wrong - "
    "the hours, the manager, the work itself, the money - because the fix is different for each "
    "one, and 'I hate it' is too big to ask anybody to solve. If the thing making you dread it is "
    "the same thing that made you ill last time, ask your GP for a fit note that says what needs "
    "to change; that is what an occupational health referral is for.")


_GOING_BACK_DONT_WANT = (
    "Not wanting to go back is worth taking seriously rather than talking yourself out of: name "
    "the one thing you are dreading - the hours, a person, the work itself, the childcare - "
    "because the fix is different for each. If it is the hours or the person, ask for the change "
    "before the first morning: a phased return, different hours, or a move within the team. If it "
    "is the work itself, go back anyway and give it six weeks, because it is much easier to look "
    "for another job from inside one than from a gap. Tell one person at home how you feel, so "
    "the first week is not being carried alone.")


_GOING_BACK_PREP = (
    "Sort the dull things before the first morning - the commute, what you are wearing, and who "
    "does the nursery run or the school pickup - so the morning is already decided. On day one ask "
    "your manager for ten minutes in the first hour: what has changed, what they need from you "
    "first, and who to ask about the rest. The first week is names and questions, and asking them "
    "is not a weakness in week one.")

_GOING_BACK_NERVES = (
    "Nerves the week before are normal, and they ease by the end of the first week. "
    + _GOING_BACK_PREP)

_GOING_BACK_TIRED = (
    "Being this done in by a working day is normal for the first few weeks back, and it passes: a "
    "day at work costs more than it used to, and that is the job, not you. Keep the evenings empty "
    "for a fortnight, go to bed an hour earlier and take the lunch break away from the desk, "
    "because the break is what makes the afternoon work. If six weeks in you are still wrecked, "
    "that is worth a word with your GP - and have your blood checked for iron and thyroid.")

_GOING_BACK_LEAVE = (
    "You go back to the same job on the same terms if you took 26 weeks of maternity leave or less; "
    "past that it is a suitable alternative job on no worse terms, and they have to offer it before "
    "anyone else. Ask HR before you go back for your hours and pay confirmed in writing, and if you "
    "want different hours put a flexible working request in - they must decide within two months. "
    "A keep-in-touch day or two makes the first week much easier, and if you are still feeding, ask "
    "where you can express milk and for breaks long enough to do it.")

_GOING_BACK_SICK = (
    "Go back in steps rather than all at once: ask for a phased return - shorter days or fewer "
    "days for two to four weeks - and say what you can do now rather than what you cannot. Your "
    "fit note can say you may be fit for work with changes, and occupational health, where there "
    "is one, is there to arrange those, not to judge whether you are ready. Expect the first week "
    "to be tiring and keep the evenings clear; a setback is not a relapse.")


_GOING_BACK_THEIRS = (
    "The first weeks back take it out of the person who is going, and the load lands on the "
    "household: take the mornings, the pickups and the cooking for a fortnight without being "
    "asked, and ask what would actually help rather than guessing. Expect them to be flat and "
    "tired by Thursday for the first month - that is the job, not a problem with them. If they are "
    "dreading it, a plan for the first morning helps more than reassurance.")


def _going_back(memory, understood):
    """Which return this is: somebody else's, from leave with a baby, from being signed off, the
    tiredness, or the nerves."""
    if _said(understood, ("hate", "hate it", "regret", "miserable", "cant face", "can't face")):
        return _GOING_BACK_WRONG
    if _said(understood, ("my wife", "my husband", "my partner")):
        return _GOING_BACK_THEIRS
    if _said(understood, ("maternity", "maternity leave", "paternity", "adoption leave",
                          "parental leave", "shared parental", "my baby", "the baby",
                          "got a baby", "new baby")):
        return _GOING_BACK_LEAVE
    if _said(understood, ("off sick", "sick leave", "sick note", "signed off", "fit note",
                          "phased return", "stress", "burnout", "anxiety", "depression",
                          "depressed", "hospital", "operation", "surgery", "miscarriage",
                          "bereavement", "grief", "sickness", "illness", "unwell",
                          "after being ill", "flu", "covid", "time off")):
        return _GOING_BACK_SICK
    if _said(understood, ("dont want to go back", "don't want to go back",
                          "do not want to go back", "dont want to return",
                          "don't want to return", "not looking forward", "dreading going back",
                          "dreading it", "cant face going back", "can't face going back")):
        return _GOING_BACK_DONT_WANT
    if _said(understood, ("exhausted", "knackered", "shattered", "tired", "drained",
                          "wrecked", "done in", "knackering")):
        return _GOING_BACK_TIRED
    if _said(understood, ("nervous", "anxious", "anxiety", "worried", "worry", "dread",
                          "dreading", "scared", "guilty", "frightened", "terrified")):
        return _GOING_BACK_NERVES
    return _GOING_BACK_PREP


def _bullying(memory, understood):
    """The bullying answer, with the police signpost in front when the line names violence."""
    if _said(understood, VIOLENT_AT_WORK):
        return ("If someone is threatening you or could hurt you, ring 999 if you are in danger "
                "now and tell the police as well as your employer: a threat of violence is a "
                "crime, not only a workplace problem. " + _BULLY_REPLY)
    return _BULLY_REPLY


# A dress code named with no job in the line belongs to the occasion, not the office. The key
# holds "dress code" and "what to wear", and "smart" was enough to reach it, so "theres a dress
# code, smart casual" and "the dress code says smart casual" were both answered with the
# interview answer - "look at photos of the team on the company site", on a line about a
# wedding. The occasion word alone is not enough either way: "what should i wear to my sisters
# wedding" already has its own answer, and it is not this one. What the guard needs is that the
# line names a code or an occasion and names no job.
A_JOB_IN_LINE = ("work", "works", "working", "office", "job", "jobs", "interview",
                 "interviews", "interviewing", "meeting", "first day", "colleague",
                 "colleagues", "boss", "manager", "shift", "shifts", "company", "staff",
                 "employer", "placement", "apprentice", "trial shift", "probation")
A_DRESS_CODE_IN_LINE = ("smart casual", "black tie", "white tie", "cocktail", "lounge suit",
                        "cocktail dress", "formal", "semi formal", "casual", "smart",
                        "dress code", "dresscode")
AN_OCCASION_IN_LINE = ("wedding", "weddings", "the do", "party", "parties", "funeral",
                       "wake", "christening", "baptism", "prom", "reception", "dinner",
                       "dance", "gig", "engagement", "birthday", "anniversary",
                       "garden party", "barbecue", "bbq", "ceremony", "graduation")


def not_a_dress_code_off_the_job(understood):
    """False when the line names a dress code or an occasion and no job."""
    if _said(understood, A_JOB_IN_LINE):
        return True
    return not _said(understood, A_DRESS_CODE_IN_LINE + AN_OCCASION_IN_LINE)


INTERVIEW_NERVES = ("Nerves are expected and mostly read as caring. Before you go in: a minute "
                    "of slow breaths out, and read your two best stories once. If your mind "
                    "blanks, say \"let me think about that for a second\" and take it - it reads "
                    "as considered, not slow.")


def _interview_nerves(memory, understood):
    """The nerves answer, with the body named first when the line is a symptom."""
    if _said(understood, NERVES_BODY):
        # the sign is the one they typed: "my hands shake at interviews" must not be told about a
        # sick stomach, and "feel sick before an interview" must not be told about shaky hands
        return (nerves_opening(_said_text(understood), "before an interview",
                               "adrenaline, not an illness, and it fades in the first two minutes "
                               "of talking") +
                ". Eat something plain an hour before, sip water rather than a big coffee, and "
                "breathe out slowly for a minute in the queue. " + INTERVIEW_NERVES)
    return INTERVIEW_NERVES


PRESENTATION_NERVES = ("Write the first thirty seconds word for word and say it out loud five "
                       "times; after that the nerves settle, because starting is the hard part. "
                       "One point per slide, headings only, and look at one friendly face per "
                       "sentence. Slow down: a pause reads as confidence and nobody notices it "
                       "half as much as you do.")


# The ask for the shape of the day rather than for preparation.
# The shape of the day is asked several ways and the tuple had two of them: "what does an
# interview day look like" reached nothing, "how does the day go" reached the preparation answer.
SHAPE_OF_THE_INTERVIEW = ("what happens", "what to expect", "what should i expect",
                          "what do i expect", "what can i expect", "whats it like",
                          "what is it like", "interview like", "like an interview",
                          "what do they ask", "what will they ask", "what kind of questions",
                          "look like", "looks like", "the day", "day go", "day like",
                          "run through", "run me through", "walk me through", "walk through",
                          "the format", "whats the format", "what is the format",
                          "how does it go", "how does the day")


def _presentation_nerves(memory, understood):
    """The presentation answer, with the body named first when the line is a symptom."""
    if _said(understood, NERVES_BODY):
        return (nerves_opening(_said_text(understood), "before a talk",
                               "adrenaline, and it drops once you are a minute in") +
                ". Eat something plain first, then " +
                PRESENTATION_NERVES[0].lower() + PRESENTATION_NERVES[1:])
    return PRESENTATION_NERVES


# "what happens at a job interview" asks for the shape of the day, not for how to prepare,
# and it was a shrug: the row's key had every asking word except the one people use for it.
WHAT_HAPPENS_AT_AN_INTERVIEW = (
    "Nearly always the same shape: someone meets you at reception, a few minutes of small talk "
    "on the way in, then twenty to forty minutes of questions about what you have actually done "
    "- a time you fixed something, a time you got it wrong - then five or ten minutes for your "
    "questions, and a word about next steps or a tour. Answer with examples rather than "
    "adjectives, keep one question ready about the team and the first six months, and ask when "
    "you will hear back before you leave.")


def _interview_prep(memory, understood):
    reply = ("Prepare four stories in situation-task-action-result shape: a week you organised, "
             "a difficult customer or colleague, something you fixed, and a time you got it wrong "
             "and changed. Then write three questions for them about the team, the first six "
             "months and what good looks like. Say the answers out loud once - saying it is "
             "different from thinking it.")
    if _said(understood, SHAPE_OF_THE_INTERVIEW):
        return WHAT_HAPPENS_AT_AN_INTERVIEW
    if _said(understood, NERVES):
        return "Nerves before an interview are normal, and they shrink once you have something " \
               "ready. " + reply
    return reply


# A refusal at a table is not a refusal of a shift: "how do i refuse wine politely" and "how do
# i say no to a second helping politely" were shrugs, and the sentence this entry has is an
# office one. So the table lines get their own wording and everything else keeps main's, word
# for word, which is what the say-no tests hold.
SAY_NO_FOOD = ("wine", "drink", "beer", "food", "dinner", "lunch", "cake", "sweets", "sugar",
               "second helping", "helping", "pudding", "dessert", "biscuit", "coffee",
               "meat", "vegetarian", "vegan", "allergy", "nuts", "alcohol", "refuse food")


def _say_no(memory, understood):
    """Main's one-sentence refusal, and the table version where the line names food or drink."""
    text = str(understood.get("clean") or understood.get("text") or "").lower()
    if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in SAY_NO_FOOD):
        return ("Keep it to four words and take the decision out of it: \"None for me, thank "
                "you\", then ask them something so the attention moves off you. A reason at a "
                "table is an invitation to be talked round, and one no is enough.")
    # the office sentence is main's, in one place, so the two cannot drift apart
    return SAY_NO_POLITELY


# What makes the first day a first-day question rather than a feeling about it: if the line asks
# any of these there is something to answer, and the packing list is it.
# "shes" and "hes" are their own words to the whole-word test, so the contractions are listed
# beside the bare pronouns; without them "shes nervous about the first day" was still handed the
# packing list.
# The tuple below had the name of the regex 300 lines up, and the second definition wins: the
# guard in `_whose_tears` called `.search()` on a tuple, so the whole answer raised and the
# arbiter dropped it. "i cant stop crying" was answered with a habit card because of it. Two
# different kinds under one name is the shape `tests/test_no_name_is_defined_twice.py` now fails on.
_ANOTHER_PERSON_WORDS = ("she", "he", "her", "him", "his", "they", "them", "their", "shes", "hes",
                   "theyre", "herself", "himself",
                   "my son", "my daughter",
                   "my child", "my kid", "my teen", "my partner", "my friend", "my nephew",
                   "my niece", "my brother", "my sister")
_FIRST_DAY_ASKS = ("wear", "bring", "take", "pack", "ask", "questions", "expect", "should i do",
                   "what do i do", "what should i do", "what happens", "what time",
                   "how do i prepare", "prepare", "notebook", "train", "get there")


def _first_day(memory, understood):
    # "hes nervous about starting his new job" asks nothing about the day: it reports how someone
    # else feels about it, and handing *him* a packing list is no answer to that. The nerves answer
    # reads his own worst of it instead, so the line is left to it. The person asking about their
    # own first day keeps the list, because that is the useful thing on the day itself.
    if (_said(understood, NERVES) and _said(understood, _ANOTHER_PERSON_WORDS)
            and not _said(understood, _FIRST_DAY_ASKS)):
        return None
    # a week in, the ask is not what to bring: it is how to stop feeling like a spare part.
    if _said(understood, ("feel lost", "feeling lost", "dont know anyone", "don't know anyone",
                          "no one talks", "nobody talks", "on my own", "left alone",
                          "started last week", "started this week", "im new here",
                          "i'm new here", "overwhelmed")):
        return ("Write down every question you have for a week, then take the list to your manager "
                "at the end of it: \"These are the things I keep guessing at - can we go through "
                "them?\" Ask two people if you can sit with them for an hour and watch how the "
                "work is really done, and say yes to the tea round, because the small talk is "
                "where the useful information is. Being new is a licence to ask that you only get "
                "once, so use it in the first month rather than saving it.")
    # "what do i ask on my first day" is a question about the questions, and the packing list
    # only told them asking is fine. brisk-coin read the head and asked for the actual questions.
    if _said(understood, ("ask on my first day", "ask on the first day", "ask questions",
                          "questions to ask", "what to ask", "what questions", "which questions",
                          "questions on my first day", "questions on the first day",
                          "first day questions", "ask my new team", "ask my new boss",
                          "ask my new manager")):
        reply = ("Ask four things: who does what on the team, what a good first month looks like, "
                 "who checks your work before it goes out, and what you should read or learn "
                 "first. Write the answers down as you hear them, because four answers said out "
                 "loud on day one are gone by Friday.")
        if _said(understood, GOOD_NEWS):
            return "Congratulations. " + reply
        return reply
    reply = ("Take a notebook, a pen, your ID and the paperwork they asked for, and dress one "
             "notch smarter than you think you need to. Your only jobs on day one are names, "
             "where the kettle and toilet are, and writing down what you are told. Asking "
             "questions is not a weakness in week one - it is the whole job.")
    if _said(understood, GOOD_NEWS):
        return "Congratulations - the first week is mostly names and questions, so go easy on " \
               "yourself. " + reply
    return reply


def _pay_and_hours(memory, understood):
    """Which rule the line is about: overtime pay, the 48-hour week, breaks, zero hours, unpaid
    leave, or a change to your hours. The words in the line pick the branch, so one entry answers
    the whole family of questions people ask about their hours and their pay."""
    # A spare hour is not a question about the job, even when the line says work: "i have an hour
    # before work, what can i do" carries "hours" and "work" and only asks what to do with the
    # hour, so the free-time row answers it.
    if (_said(understood, ("an hour", "half an hour", "an hour or two", "to kill"))
            and _said(understood, ("what can i do", "what should i do", "what to do",
                                   "shall i do", "anything to do"))):
        return None
    if _said(understood, ("zero hours", "zero hour contract", "casual contract", "no guaranteed")):
        return ("A zero-hours contract means no guaranteed hours: they offer work and you can say "
                "no, and you must be paid for every hour you do work. An exclusivity clause - one "
                "that stops you working elsewhere - is void, and after 12 weeks of regular hours "
                "you can ask for a fixed-hours contract. You still build up holiday pay on the "
                "hours you work, at about 12 per cent of them.")
    if _said(understood, ("unpaid leave", "unpaid time off", "leave without pay",
                          "time off without pay")):
        return ("There is no general right to unpaid leave: your employer can say no, and asking "
                "is a request, not a notice. The exceptions are time off for dependants in an "
                "emergency, which is unpaid but protected, and parental leave. Ask early and in "
                "writing, say what will be covered while you are away, and offer the dates.")
    # The word alone is not enough: "not bad, just had lunch, what about you" and "what can I
    # make with leftover rice for lunch" both carry it, and neither is a question about a job.
    if _said(understood, BREAK_WORK_CUES) and _said(understood, ("lunch", "break", "breaks",
                                                                "rest break", "rest breaks",
                                                                "breather")):
        return ("On a shift longer than six hours you are entitled to a 20-minute break, and to 11 "
                "hours' rest between shifts; under six hours there is no legal minimum, and the "
                "break can be unpaid. If your lunch is being cut short every day, put it in "
                "writing once - the rota and the times - and ask for the 20 minutes back.")
    if _said(understood, ("48", "forty eight", "long hours", "too many hours", "maximum hours",
                          "how many hours")):
        return ("The legal limit is an average 48-hour week over 17 weeks, and you can only go over "
                "it if you signed an opt-out in writing - which you can cancel in writing, usually "
                "with seven days' notice. If your weeks are over 48 on average, ask for the "
                "calculation in writing; the 48-hour week cannot be traded away by a verbal yes.")
    if _said(understood, ("change my hours", "changed my hours", "change my shift", "rota",
                          "different hours", "new hours", "change my contract")):
        return ("Your hours can only be changed with your agreement, unless your contract has a "
                "clause that lets them - and even then they have to use it reasonably, with "
                "notice. Say no in writing and ask for the reason: if it is a real business need "
                "they should consult you first, and a big change with no agreement can be a "
                "breach of contract. A union rep or ACAS will back you up for free.")
    if _said(understood, ("overtime", "extra hours", "work late", "stay late", "time and a half")):
        # "can they make me stay late" is a question about being made to, so it gets that answer
        # first; "am i entitled to overtime pay" is a pay question and keeps the pay one.
        if _said(understood, ("make me", "make us", "can my boss", "can my employer",
                              "can my work", "have to", "refuse", "stay late", "staying late",
                              "work late", "working late", "without pay", "unpaid overtime")):
            return ("Only the hours your contract sets, and beyond those staying late is "
                    "voluntary - there is no legal right to extra pay for extra hours unless the "
                    "contract promises overtime, only that your average pay still clears the "
                    "minimum wage. Check what it says about the overtime rate and when it starts, "
                    "and put any change to your hours in writing so it is clear which ones were "
                    "agreed.")
        return ("Paid overtime depends on your contract: if it says overtime is paid, they must pay "
                "it, but if it says nothing there is no legal right to extra pay for extra hours - "
                "only that your average pay still clears the minimum wage. Check the contract for "
                "the rate and when it starts, and put any change to your hours in writing so it is "
                "clear which ones were agreed.")
    # A spare hour that happens to sit before or after work is not a question about the job: "i
    # have an hour before work, what can i do" was answered with the contract and the 48-hour
    # week. The hour is the subject, and the free-time row answers it.
    if (_said(understood, ("an hour", "half an hour", "an hour or two", "to kill"))
            and _said(understood, ("what can i do", "what should i do", "what to do",
                                   "shall i do", "anything to do"))):
        return None
    # Nothing in the line was about a job: it reached the entry on a word like "lunch" or
    # "hours" in passing ("not bad, just had lunch, what about you"). Hand it back.
    if not _said(understood, WORK_SUBJECT):
        return None
    # "what do you do when your fridge breaks" and "my washing machine breaks down every month"
    # reached the entry on "breaks", and a contract is no help to either: the thing that breaks
    # is what the line is about, so the fault shape is handed back to the repair answers.
    line = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    line = re.sub(r"[^a-z0-9' ]+", " ", line)
    if re.search(r"\b(?:when|if|every time)\b[^.?!]*\bbreak(?:s|ing)?\b", line):
        return None
    if re.search(r"\bbreak(?:s|ing)?\s+down\b", line) and not _said(
            understood, ("shift", "shifts", "rota", "work", "working", "job", "boss")):
        return None
    # A bone that is broken is not a break in a shift: the health entries answer it, and the
    # contract rule only reached the line on the word "break".
    if _said(understood, INJURY_WORDS) and not _said(understood, BREAK_WORK_CUES):
        return None
    # An in-law is a relation, not a statute: "my in laws are coming for lunch sunday" reached
    # this fallback on the `laws` inside `in laws` and was answered "Your contract is the place
    # to look first", while `my mother in law is coming sunday` got the visit card. The words
    # that make a relation say so, and a line with one and no job in it is somebody's family.
    if IN_LAW.search(line) and not _said(understood, IN_LAW_JOB):
        return None
    return ("Your contract is the place to look first: it sets your hours, your breaks and whether "
            "overtime is paid. On top of it the law gives you a 20-minute break on a shift over "
            "six hours, 11 hours between shifts, and an average 48-hour week unless you signed an "
            "opt-out. If something is not being followed, ask for it in writing - that is what an "
            "employment adviser or a union rep needs to help.")


SLEEP_TALK = ("sleep", "sleeping", "slept", "asleep", "wake", "wakes", "waking", "woke",
              "awake", "insomnia", "tired", "exhausted", "body clock", "jet lag", "nap")

REVIEW_ANCHOR = ("mistake", "slipped", "slip", "missed", "miss", "went wrong", "my fault",
                 "report", "late", "behind", "failed", "failure", "review", "appraisal",
                 "deadline", "error", "project", "presentation", "told off")

def _about_a_slip(text):
    return _said({"clean": text}, REVIEW_ANCHOR)

def _defensive_review(memory, understood):
    line = understood.get("clean") or understood.get("text") or ""
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    earlier = " ".join(t.get("user") or "" for t in turns[-3:])
    if not _about_a_slip(line) and not _about_a_slip(earlier):
        return None
    return ("Lead with the fact, then what you did about it, then what you learned: \"The project "
            "slipped by six weeks; I flagged it in May, we re-planned, and I now build in a review "
            "at the halfway point.\" Talking about the fix is what stops it sounding defensive, so "
            "don't explain the cause twice.")


# "how do i deal with a difficult boss" is this entry's own line, and the one sentence that must
# not be handed to someone about their boss is the public question: saying it to a manager in
# front of the same people is how a job is lost, and "take the pattern to your manager" names the
# person who is the problem. The behaviour-and-specifics opening and the dated note stay.
_BOSS = re.compile(r"\b(?:boss|bosses|manager|managers|supervisor|line manager|team leader|"
                   r"head of|my md)\b", re.I)

_COLLEAGUE_OPENING = ('Deal in behaviour and specifics, not character: "In Monday\'s meeting, when '
                      'you cut across me, I lost the point I was making." ')

_BOSS_REPLY = (_COLLEAGUE_OPENING +
               'Say the thing privately, once, calmly, and name what you want instead: "When you '
               'reword my work in the meeting I stop raising ideas, so I would rather you added to '
               'it than replaced it." If it carries on, keep a dated note of each case and put the '
               'pattern in writing - to their manager or to HR, or to HR alone if the note is about '
               'them. A list of dates is what gets acted on.')

_PEER_REPLY = (_COLLEAGUE_OPENING +
               'A snide remark is best met with a plain question in front of the same people, asked '
               'of a colleague: "What did you mean by that?" It is hard to stay passive when '
               'someone asks you to say it out loud. Say the thing privately, once, calmly, and '
               'name what you want instead. If it carries on, keep a dated note of each case and '
               'take the pattern to your manager or HR - a list of dates is what gets acted on.')


def _difficult_colleague(memory, understood):
    """The colleague answer, and the boss version without the public question and the manager."""
    text = str((understood or {}).get("clean") or "").lower()
    return _BOSS_REPLY if _BOSS.search(text) else _PEER_REPLY
# 5.6 weeks is the statutory figure, so a pro-rata question is arithmetic on the working week the
# person already gave: "how many holidays am i entitled to if i work 4 days a week" is 5.6 x 4.
# "3 days a week" and "three days a week" are the same week: people spell a small
# number about as often as they write it.
_DAYS_WORD = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
_DAYS_A_WEEK = re.compile(
    r"\b(\d(?:\.5)?|one|two|three|four|five|six)\s*days?\s*(?:a|per|each)\s*week\b")
# A quoted allowance ("is 20 days holiday legal") is a number to check against the 28-day
# minimum, not a week to multiply: the answer says straight away whether it is short.
_QUOTED_DAYS = re.compile(r"\b(\d{1,2})\s*days?\b")


def _weeks_figure(days):
    """5.6 weeks of a working week, as a reader would say it ("22.4", not "22.40")."""
    shown = f"{5.6 * days:.1f}"
    return shown[:-2] if shown.endswith(".0") else shown


_FIVE_DAY_TEXT = ("In the UK it is 5.6 weeks of paid holiday a year, which is 28 days if you "
                  "work five days a week, and bank holidays can be counted in that. Part-time "
                  "staff get the same in proportion: four days a week means 22.4 days. Agency, "
                  "zero-hours and casual workers build it up too. Your contract can give more "
                  "than that, never less, so check it, and note that days you do not take are "
                  "usually lost at the end of the year unless it lets you carry a few over. If "
                  "holiday is refused or unpaid, ACAS is free and takes it from there.")


# "lose" and "lost" are verbs of a dozen subjects, and the row's own key words are "holiday"
# and "lose", so "i'm trying to lose weight before my holiday" scored here and got the
# carry-over rule. The lookahead keeps the verb for days and time off and leaves body weight to
# health.py, which is where the diet answer lives.
_NOT_BODY_WEIGHT = (r"(?!\s+(?:weight|fat|kilos?|kilograms?|pounds?|lbs|stones?|inches|"
                    r"my weight|some weight|a stone|a few pounds))")
_CARRY_OVER = re.compile(
    r"\bcarry|carried|carrying|roll(?:ed)? over|use it or lose|"
    # Days kept back from an earlier year are the same question as days carried over: "i saved
    # three days of holiday can i use them" and "i have 5 days holiday saved up from last year"
    # are not asking for the 28-day figure, they are asking whether the saved ones survive.
    r"\bsaved\b|\bsaved up\b|left over|leftover|from last year|from the year before|"
    rf"\blose\b{_NOT_BODY_WEIGHT}|\blost\b{_NOT_BODY_WEIGHT}|forfeit|unused|"
    r"\binto (?:january|february|march|april|may|june|july|august|september|october|november|"
    r"december|next year|the next year|next month)\b|\btake it into the next\b", re.IGNORECASE)


# "how many days leave do i have left" wants two things: the allowance the law gives, which is
# the same for everybody, and the number of days still on their card, which is not - it depends
# on their start date, their week and what they have already booked. The long entitlement
# paragraph answers the first and leaves the second, so a balance ask gets the figure it can
# have and the one place the rest lives. It is shorter than the paragraph on purpose: the person
# asked for a number, not for the holiday clause.
_ASKS_THE_BALANCE = re.compile(r"\b(?:left|remaining|balance)\b|\bstill\s+have\b")
_WHERE_THE_BALANCE_IS = ("How many of those days are left is on your payslip or in your "
                         "employer's holiday system - it depends on your start date, your week "
                         "and what you have already booked, so I can't see it from here.")


# The week a person works is said once and then assumed: "i only do three days a week" is
# followed by "how much leave am i entitled to", and the answer gave the four-day example as
# though the line had said nothing. Two turns back is enough, and only the person's own week
# counts - a partner's or a colleague's week is not the one the allowance is worked out from.
_SOMEONE_ELSES_WEEK = re.compile(
    r"\b(?:my|his|her|their)\s+(?:wife|husband|partner|son|daughter|mum|dad|friend|"
    r"colleague|sister|brother)\b")


def _the_week_they_said(memory):
    """The days a week the person said in the last few turns, or None."""
    turns = (memory or {}).get("turns") or []
    for turn in reversed(turns[-3:]):
        said = str(turn.get("user") or "").lower()
        found = _DAYS_A_WEEK.search(said)
        if not found:
            continue
        around = said[max(0, found.start() - 40):found.end()]
        if _SOMEONE_ELSES_WEEK.search(around):
            continue
        if re.search(r"\bi\b|\bim\b|\bi'm\b", around):
            return found.group(1)
    return None


def _their_balance(said=None):
    """The allowance, and where the person's own balance is - with their week when it is known."""
    worked = "Part-time is the same in proportion."
    if said:
        days = float(_DAYS_WORD.get(said, said))
        if days != 5:
            worked = (f"Part-time is the same in proportion - {said} days a week is "
                      f"{_weeks_figure(days)} days.")
    return ("Full-time you get 5.6 weeks of paid holiday a year, which is 28 days with the bank "
            f"holidays counted inside it. {worked} " + _WHERE_THE_BALANCE_IS)


def _holiday_entitlement(memory, understood):
    """The statutory answer, with the pro-rata figure worked out for the days they work.

    The paragraph below answers the five-day question and gives four days a week as its example.
    Someone who says three days, four days or 4.5, in digits or in words, gets their own figure
    in the same words instead of somebody else's; five days is the full-time week the paragraph
    already states, so it is not said twice. A number quoted as their own allowance ("is 20 days holiday legal") is a
    different question again: it is a comparison with the 28-day minimum, so it gets the verdict
    first. Everyone else gets the paragraph unchanged.
    """
    line = (understood.get("clean") or understood.get("text") or "").lower()
    # Carrying days over is the one leave question the 28-day paragraph cannot answer by being
    # quoted: it depends on the contract, and "can i carry holiday into january" was answered
    # with January's travel picks and then with a packing list for 2 to 8C.
    if _CARRY_OVER.search(line):
        return ("Carry-over is your contract's, not the law's: the 28 days is a floor, and the "
                "4 weeks of it can only be carried over where the contract or your employer's "
                "policy allows it, which is why the handbook is the place to check. A common "
                "rule is up to 5 days carried to the end of March; a use-it-or-lose-it deadline "
                "is lawful when you had the chance to take the time. If you could not take it "
                "because you were off sick or your request was refused, you generally keep the "
                "right to it, and ACAS is free if they will not give it.")
    # The week has to come from the line the person just typed, not from the reading's stitched
    # text: `clean` carries the turn before it, so a week said in an earlier line was read as
    # though it had been said again here, and "my wife does three days a week" then "how much
    # leave" handed the person her week as their own allowance. A week that belongs to somebody
    # else is not a week to work a figure out from, so it falls through to the turns before,
    # which read each one and skip the ones about a partner or a colleague.
    own_line = str(understood.get("text") or "").lower()
    part_time = _DAYS_A_WEEK.search(own_line)
    if part_time and _SOMEONE_ELSES_WEEK.search(own_line[:part_time.end()]):
        part_time = None
    said = part_time.group(1) if part_time else _the_week_they_said(memory)
    if _ASKS_THE_BALANCE.search(line):
        return _their_balance(said)
    if said:
        days = float(_DAYS_WORD.get(said, said))
        if days == 5:
            # Five days a week is the full-time week the first clause already states, so the
            # worked figure would only say the same number twice.
            return _FIVE_DAY_TEXT
        return ("In the UK it is 5.6 weeks of paid holiday a year, which is 28 days if you work "
                f"five days a week - so {said} days a week is {_weeks_figure(days)} days - and "
                "bank holidays can be counted in that. Part-time staff get the same in "
                "proportion. Agency, zero-hours and casual workers build it up too. Your "
                "contract can give more than that, never less, so check it; if holiday is "
                "refused or unpaid, ACAS is free and takes it from there.")
    quoted = _QUOTED_DAYS.search(line)
    if quoted:
        days = int(quoted.group(1))
        if days >= 28:
            verdict = f"{days} days is above the 28-day minimum, so there is nothing short there"
        else:
            verdict = f"{days} days is below the 28 days a full-time job has to get"
        return (verdict + ". In the UK it is 5.6 weeks of paid holiday a year, and bank holidays "
                "sit inside that rather than on top of it, so 28 days is a floor and not a "
                "target. Under 28 is only right for a part-time week - four days a week is 22.4 "
                "days, three days is 16.8 - so ask for your figure in writing and check it "
                "against the days you work. If it comes up short, ACAS is free and takes it on.")
    return _FIVE_DAY_TEXT

# Who the person is decides how the smell is said: a colleague gets the private word by the
# lockers and the HR route, and someone you live with gets the same sentence at home with no
# meeting or manager in it. One entry, two scripts, so a line naming a partner or a flatmate is
# answered rather than handed to whichever module owns writing things down.
_PEOPLE_AT_HOME = ("boyfriend", "girlfriend", "husband", "wife", "partner", "fiance",
                   "fiancee", "flatmate", "roommate", "housemate", "my mum", "my dad",
                   "my son", "my daughter", "my brother", "my sister", "my friend", "my mate")

# Which smell the line named decides the sentence: "your shirts still smell after the wash" is
# the one smell a person who smells of smoke is not. The washing is the default because it is the
# kindest thing to blame.
def _the_smell(clean):
    """The two clauses for the named smell: the office one and the one for home."""
    if re.search(r"\bsmok|cigarette|cigar|vap(?:e|ing)", clean):
        return ("you smelled of smoke in the meeting", "your jacket still smells of smoke")
    if re.search(r"\bbreath\b|bad breath|halitosis|garlic|onion", clean):
        return ("your breath across the desk was hard to miss",
                "your breath in the car was hard to miss")
    if re.search(r"\bfeet\b|\bfoot\b|\bshoes\b|trainers|socks|\bsweaty feet\b", clean):
        return ("your shoes under the desk were hard to miss",
                "your trainers by the door were hard to miss")
    return ("you had a smell about you in the meeting",
            "your shirts still smell after the wash")


_TELL_AT_WORK = ("Say it once, in private, about the effect and not the person: \"This is "
                 "awkward, and I'd want to know - %s and I don't think you meant to.\" One "
                 "sentence, then move on to something practical: a spare shirt in the locker, "
                 "deodorant in the bathroom, washing at the gym before the shift. Never in front "
                 "of anyone else and never by email. If it is your manager, or you cannot face it, "
                 "ask HR to have the word - that is what they are for, and you do not have to "
                 "name the reason in writing.")

_TELL_AT_HOME = ("Say it the same day, at home, about the thing rather than the person: "
                 "\"%s - have you noticed?\" is easier to hear than anything about you. One "
                 "sentence, then something that helps - a wash at sixty, a new deodorant, the "
                 "window open - and no audience and no joke about it.")


# A quiet hour with a baby in the house is not a seat in the office: the same ask has a house
# version, so the entry answers it rather than standing down and letting a health line carry it.
# "how do i get a quiet hour with a newborn" fell through to a call-the-health-visitor signpost,
# which is a careless answer to a question about rest.
_BABY_AT_HOME = ("baby", "babies", "newborn", "new born", "toddler", "infant", "my child",
                 "my son", "my daughter", "twins", "pram", "nursery", "teething", "breastfeeding")

_QUIET_AT_WORK = ("Ask for a specific seat, not for silence: the back row away from the door, "
                  "the printer and the kitchen, and say what it buys - \"I lose an hour a day to "
                  "the corridor outside my desk, so I'd like to move to the far wall.\" Book a "
                  "meeting room for the two hours of deep work a day and treat it as a real "
                  "appointment, and use headphones as the sign that you are in one. If the noise "
                  "is machinery, an alarm or something that makes your ears ring, that is a "
                  "health-and-safety report, not a seating request.")

# A colleague is not a neighbour: the noise is in the room all day and the person is somebody
# you have to keep working with, so the answer is one friendly sentence and then what you can
# change yourself. The neighbour card ("the telly carries through the wall", ring the council)
# is the wrong shape for a desk, and "how do i deal with a noisy coworker" reached no card at all.
# The sentence in the quotes has to be the one the person would actually say, so the row has two
# openings - a voice on the phone or in the room, and a radio or a pair of speakers - and one
# ending, because the rest is the same whichever noise it is.
_COLLEAGUE_WORD = (
    "Have one friendly word before you change anything else, because most people have no idea "
    "how far their voice carries: ")
_COLLEAGUE_A_VOICE = (
    "\"I can't hear myself think on my own calls - would you mind taking that off speaker?\" ")
_COLLEAGUE_A_RADIO = (
    "\"I can't hear myself think with that on - any chance of headphones?\" ")
_COLLEAGUE_A_NOISE = (
    "\"Sorry to be that person - I can't hear myself think where I'm sitting. Any chance of "
    "keeping that down?\" ")
_COLLEAGUE_TAIL = (
    "Ask for the one change you want rather than for quiet in general, and ask it at their desk "
    "rather than in front of the team. Then do your half: your own headphones, or a seat away "
    "from them if the desk layout allows, and the deep-work hour booked in the calendar. If it "
    "carries on, that is a thing to raise with your manager once, with the times written down - "
    "it is their job to sort out where people sit, not yours.")
_QUIET_WITH_A_COLLEAGUE = _COLLEAGUE_WORD + _COLLEAGUE_A_VOICE + _COLLEAGUE_TAIL
_QUIET_WITH_A_RADIO = _COLLEAGUE_WORD + _COLLEAGUE_A_RADIO + _COLLEAGUE_TAIL
_QUIET_WITH_NOISE = _COLLEAGUE_WORD + _COLLEAGUE_A_NOISE + _COLLEAGUE_TAIL

# The noise a colleague makes that plays rather than talks, so the quoted ask names headphones.
_PLAYING_NOISE = ("music", "radio", "podcast", "podcasts", "speaker", "speakers",
                  "telly", "t.v.", "tv", "sings", "singing", "hums", "humming",
                  "plays", "playing", "out loud")

# The words that say the noise is a person beside you at work rather than a neighbour through a
# wall: the person named, or the desk they are at. `_quiet_hour` reads these off the line, and so
# does the guard below. An open plan office is NOT one of them: that is the room, and the room
# keeps the room's answer (a seat, a meeting room).
_WITH_SOMEONE_AT_WORK = ("colleague", "colleagues", "coworker", "coworkers", "co-worker",
                         "co-workers", "workmate", "workmates", "teammate", "teammates",
                         "team mate", "team mates", "next to me", "beside me", "next to my desk",
                         "at the next desk", "across from me")

# The noise itself: loud talk, a phone on speaker, the radio, a running commentary. Used twice -
# as the second half of the noisy-office key and as the test the guard makes of a person line -
# so a colleague plus an ask ("how do i deal with a passive aggressive colleague", "how do i talk
# to a colleague about their hygiene") is somebody else's card and a colleague plus a noise word
# is this one. Never a bare "quiet": "my colleague is quiet" is not this question.
_NOISE_WORDS = ("loud", "too loud", "noisy", "noise", "talks loudly", "talking loudly",
                "speaks loudly", "speakerphone", "speaker phone", "on the phone", "on speaker",
                "on the phone all day", "keeps talking", "chatters", "chattering", "chatter",
                "hums", "humming", "sings", "singing", "music", "radio", "podcast", "telly",
                "quieter", "be quiet", "keep it down", "turn it down", "turn the volume down",
                "distracting", "distracts me", "distracting me", "cant hear myself",
                "can't hear myself", "cant stand the noise", "can't stand the noise")


def _a_person_and_a_noise(understood):
    """Whether the row may answer: a room line always, a person line only when it names noise."""
    clean = ((understood or {}).get("clean") or "").lower()
    if not _says_someone_at_work(clean):
        return True
    return any(_says_it(clean, word) for word in _NOISE_WORDS)

_QUIET_WITH_A_BABY = ("Take the hour when someone else has them instead of trying to find one: "
                      "one stretch a day handed over to a partner, a grandparent or a friend is "
                      "worth more than any trick. If you are on your own, go out with the pram or "
                      "a sling at the time they sleep, because a walk is the one hour that comes "
                      "free, and put the cot or the basket in the room you are in rather than "
                      "chasing sleep in another room. Rest when they rest and leave the tidying: "
                      "the hour is for you, and a baby group or a home-start volunteer will give "
                      "you another one.")


def _quiet_hour(memory, understood):
    """The office answer, the colleague answer, or the one for a baby in the house."""
    clean = (understood.get("clean") or "").lower()
    for word in _BABY_AT_HOME:
        if _says_it(clean, word):
            return _QUIET_WITH_A_BABY
    if _says_someone_at_work(clean):
        if any(_says_it(clean, word) for word in _PLAYING_NOISE):
            return _QUIET_WITH_A_RADIO
        if any(_says_it(clean, word) for word in ("phone", "calls", "call", "talking",
                                                  "talks", "talks loudly", "chatter")):
            return _QUIET_WITH_A_COLLEAGUE
        return _QUIET_WITH_NOISE
    return _QUIET_AT_WORK


def _says_it(clean, word):
    """True when the line holds `word` as a whole word."""
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", clean))


def _says_someone_at_work(clean):
    """True when the line says the noise is a person at work, not the room or the house."""
    return any(_says_it(clean, word) for word in _WITH_SOMEONE_AT_WORK)


def _tell_about_a_smell(memory, understood):
    """The office script, or the one for someone you live with, naming the smell in the line."""
    clean = (understood.get("clean") or "").lower()
    at_work, at_home = _the_smell(clean)
    for person in _PEOPLE_AT_HOME:
        if re.search(r"(?<![a-z0-9])" + re.escape(person) + r"(?![a-z0-9])", clean):
            return _TELL_AT_HOME % at_home
    return _TELL_AT_WORK % at_work

# A cancelled shift and a cancelled day off are the same thing taken from you, so both take the
# contract answer; a single shift moved with notice is the rota card's.
_DAYS_OFF_WORDS = ("day off", "days off", "dayoff", "called in", "called into work",
                   "call me in", "called me in", "shift cancelled", "shifts cancelled",
                   "shift canceled", "rota cancelled", "cancelled my shift", "cancelled my days",
                   "cancel my days", "cancelling my days", "cancelling my shift",
                   "cancels my days", "cancels my shift", "getting cancelled", "keep getting cancelled")

_SHIFT_TEXT = (
    "Ask for the rota a week ahead in writing and check what your contract says about "
    "changes: most set a minimum notice, and a permanent shift pattern is usually a term "
    "of the contract. Then say it once, plainly, about the next change rather than the last "
    "one: \"Thursday I was told on the day - can we agree changes are confirmed 48 hours "
    "ahead?\" If it keeps happening, put it in an email and ask HR what the pattern is "
    "meant to be; your union or ACAS will tell you where you stand for free.")

# The things whose moving is this entry's line: a rota, a shift pattern, the hours, the rest days
# and the leave already booked. The reply reads this list too, so a line that reaches the entry
# only with the rota put back into it ("i just feel like im always the one who bends") is not
# answered with advice about notice, and a new way of naming the thing moved is one line here.
ROTA_WORDS = ("shift", "shifts", "rota", "schedule", "timesheet", "hours",
              "onto nights", "onto days",
              # the days off are the thing cancelled, and the line often names only them:
              # "my boss keeps cancelling my days off", "i keep getting called in on my day off"
              "day off", "days off", "rest day", "rest days",
              # and leave booked and then cancelled, which is the same complaint in HR's words
              "annual leave", "holiday", "holidays", "my leave", "booked leave")

# The words of the change itself, the way the same complaint is said: the rota "keeps changing",
# it moved on them, the days off were cancelled, the boss or the contract decides. The reply reads
# this list as well as ROTA_WORDS, so a line of its own about the rota ("my manager says its in my
# contract") is answered as before and a line that names neither stands down.
ROTA_CHANGE_WORDS = (
           # not "i changed shifts" on its own: that is how someone dates a sleep problem, and the
           # answer here is about a rota being moved on them
              "keeps changing", "keep changing", "short notice", "last minute", "last-minute",
            "keeps moving", "keeps swapping", "unfair", "boss", "manager", "contract",
            # the days off being taken away, which is the other way the same complaint is said
            "cancelled", "canceled", "cancelling", "canceling", "cancels", "cancel",
            "keeps cancelling", "keep cancelling", "getting cancelled", "called in",
            "sent home", "rota cut",
            "refuse", "say no", "on the day",
            # a rota that moves is often said as what it costs: "i cant plan anything"
            "every week", "every fortnight", "cant plan", "can't plan", "plan anything",
            "never know", "no idea when",
            # and it is often said with the moving and nothing else: "they changed my rota
            # again", "my hours were changed on me". The word for the moving belongs with the
            # word for the thing moved, which the first set already requires.
              "changed", "changing", "changes", "moved", "swapped", "switched", "rotated")


# A line about how the rota has left them, with no rota word in it, is the chat module's: the
# feeling is the thing to answer, not the notice. Read only when the line names no rota at all.
FEELING_WORDS = ("feel", "feels", "feeling", "felt", "miserable", "fed up", "sick of",
                 "stressed", "exhausted", "burnt out", "burned out", "resentful", "unfair to me",
                 "always the one", "who bends", "cant cope", "can't cope", "had enough")

# A rota moved with no word to you: the same entry as the advice above, but asked as what is
# allowed, so the verdict is the first sentence and the steps come after it.
PERMISSION_ASK = re.compile(r"\b(?:without asking|without telling|without a word|without notice|"
                            r"do that|get away with|allowed to|allowed|legal|lawful|"
                            r"is that ok|is that right)\b")

_SHIFT_VERDICT_TEXT = (
    "Not without telling you, and only as far as your contract allows: a permanent shift pattern "
    "is usually a term of the contract, so it cannot be changed without your agreement or the "
    "notice the contract sets, and it cannot take you below your contracted hours. Ask for the "
    "rota a week ahead in writing and check what your contract says about changes. If they moved "
    "you on the day, say it once, about the next change rather than the last one: \"Thursday I "
    "was told on the day - can we agree changes are confirmed 48 hours ahead?\" Keep the "
    "messages, and your union or ACAS will tell you where you stand for free.")

_LEAVE_TEXT = (
    "Booked leave is not theirs to cancel freely: they can, but only for a business reason and "
    "with notice at least twice the length of the leave - two weeks' notice to cancel a week off. "
    "Leave you have already taken cannot be taken back, and it cannot be cancelled to avoid "
    "paying it out. Ask for the reason in writing, keep the rota and the emails, and a union rep "
    "or ACAS (0300 123 1100) can back you up.")

# a cancelled holiday can be an airline's doing, and that is the travel table's answer
_LEAVE_WORDS = ("annual leave", "holiday", "my leave", "time off", "booked leave",
                "leave i booked", "holidays")

_TRAVEL_WORDS = ("flight", "flights", "airline", "plane", "holiday booking", "hotel", "package",
                 "abroad", "airport", "train", "ferry", "cruise", "booking reference")

_DAYS_OFF_TEXT = (
    "A cancelled day off or shift is a change to your contract, not a favour: your contracted "
    "hours and rest days are terms of it, so short-notice cancelling is something you can refuse, "
    "and on guaranteed hours you should still be paid. Say no in writing, ask for the change in "
    "writing too, keep a dated list, and take a pattern of it to a union rep or ACAS "
    "(0300 123 1100).")


def _shift_changed_reply(memory, understood):
    """A rota moved on you, or the days off themselves cancelled: the same entry, different advice,
    because "they keep cancelling my days off" is about the hours being taken, not about notice."""
    text = str((understood or {}).get("clean") or "").lower()
    # A line that only says how they feel ("i just feel like im always the one who bends") names
    # no rota of its own: it reaches this entry only with the rota put back into it, and advice
    # about notice is about the wrong thing - the feelings are the chat module's. So the entry
    # answers a line that names the thing that moved, or one that asks what is allowed about it
    # ("can they do that without asking" after a moved rota), and stands down for the rest.
    said = str((understood or {}).get("text") or text).lower()
    names_it = (_said({"clean": said}, ROTA_WORDS) or _said({"clean": said}, ROTA_CHANGE_WORDS))
    if not names_it and _said({"clean": said}, FEELING_WORDS):
        # A line that says how they feel and names no rota ("i just feel like im always the one
        # who bends") is the chat module's, even when the rota put back into it reaches this
        # entry: advice about notice answers a question they did not ask.
        return None
    if _said({"clean": text}, _DAYS_OFF_WORDS):
        return _DAYS_OFF_TEXT
    if _said({"clean": text}, _LEAVE_WORDS):
        if _said({"clean": text}, _TRAVEL_WORDS):
            return None
        return _LEAVE_TEXT
    # "can my boss change my shifts without asking" is a yes/no question, and the advice for a
    # rota that has already moved does not answer it: the person wants the verdict first and the
    # steps after it. A follow-up written as "can they do that without asking" reaches this entry
    # only with the rota put back into the line, and it was then held back as an answer already
    # given, word for word - the verdict opens the reply, so the same advice answers the question.
    if PERMISSION_ASK.search(text):
        return _SHIFT_VERDICT_TEXT
    return _SHIFT_TEXT

# A student visa caps hours well below the 48-hour week, and the two rules are not the same one.
# "how many hours can i work on a student visa" was answered with the 48-hour average, which is
# what an employee's contract may add up to and not what a visa allows: going over the visa cap
# can cost the visa, so the visa answer has to be the one a person gets.
STUDENT_VISA_HOURS = (
    "On a student visa you can work up to 20 hours a week in term time on a degree-level course, "
    "and 10 hours a week if the course is below degree level; outside term time you can work full "
    "time. The cap covers every hour you work for anyone, and self-employment, freelancing and a "
    "permanent full-time job are not allowed at all. The 48-hour week is an employee's average, "
    "not your limit: the visa cap is lower and it comes first.")

# What a visa line is not: a question about study, a loan or a course. The row keys on the visa
# and on an hours phrase, and these keep a line about revising, a student loan or a personal
# statement out of it.
NOT_VISA_HOURS = (
    "student loan", "student loans", "maintenance loan", "tuition", "tuition fees",
    "course fees", "accommodation", "ucas", "personal statement", "a level", "a levels",
    "gcses", "grades", "grade", "exam", "exams", "coursework", "essay", "dissertation",
    "revision", "revise", "revising", "lectures")
# "can a student work while studying" is the visa question, so "study" is not here: the second row
# keys phrases ("can a student work") and no bare study word, so a study-hours question still goes
# to the study answer.


# The profile at the top of a CV, said once: two rows answer it - the named forms ("cv profile",
# "career summary") and the bare "personal statement", which needs the line to say cv first.
_CV_PROFILE_REPLY = (
    "Two to four lines under your name, and the first thing anyone reads: the job you do "
    "or want, your strongest two pieces of evidence with a number in them, and what you "
    "are after next. Write it last, when you know what the CV holds, and aim it at the "
    "advert's job title. Skip \"hard-working team player\" and anything you could say "
    "about anybody: \"Warehouse team leader with five years on shift, cut picking errors "
    "by 12% and now looking for a shift manager role.\"")

# Which of the two notice questions this is: "how much notice do i give" wants the length, and
# "can they make me work it" wants a yes or no first. One card answers both, so the opening
# sentence is chosen from the ask and the rest of the card is shared.
_NOTICE_CAN_THEY = re.compile(
    r"\b(?:can they|can my|can i be|do i have to|must i|make me|force me|stop me|"
    r"they make|wont let me|won't let me|allowed|legal)\b", re.I)
# "how much notice do i give" carries "do i have to" as well in the way people write it, and the
# length is what it asks: the yes-or-no opening is only for a line that is not asking the length.
_NOTICE_HOW_MUCH = re.compile(r"\bhow (?:much|long|many)\b", re.I)
# Leaving early for money is the third question, and its answer is the contract's clause.
_NOTICE_GARDEN = re.compile(r"\bgarden(?:ing)? leave\b", re.I)
_NOTICE_PAID_INSTEAD = re.compile(
    r"\b(?:pay(?:ment)? in lieu|paid instead|pay me instead|pay instead|paid off|"
    r"instead of working|instead of serving|buy (?:myself|me) out)\b", re.I)


def _notice_reply(memory, understood):
    """The notice card, opened with the answer the line actually asked for."""
    line = (understood.get("clean") or understood.get("text") or "").lower()
    if _NOTICE_GARDEN.search(line):
        # "what is garden leave" wants the meaning, and the notice card already says how long it
        # can last: the definition is the first sentence and the card follows it.
        opening = ("Garden leave is being paid to stay at home for your notice: your contract still "
                   "runs, your pay and holiday carry on, and you must be ready to come back if "
                   "they call. It is the employer's choice, and it cannot run past your notice. ")
    elif _NOTICE_PAID_INSTEAD.search(line):
        opening = ("Often yes: many contracts let your employer pay you for the notice instead "
                   "of you working it, and they can insist on it - so check for a payment in "
                   "lieu clause. ")
    elif _NOTICE_CAN_THEY.search(line) and not _NOTICE_HOW_MUCH.search(line):
        opening = ("Yes, if the contract says so: a notice period binds both sides, so they "
                   "can hold you to the full notice and you can hold them to theirs. ")
    else:
        opening = ("Your contract decides the length - usually a week to three months - so "
                   "read that or the intranet, not your memory. ")
    return opening + (
        "In the UK the statutory minimum is a week after a month's service, rising by a week "
        "a year up to twelve. They can put you on garden leave, and most contracts let either "
        "side agree to stop early, with pay in lieu of the rest. To serve less, ask early and "
        "in writing: unused holiday can usually be taken inside the notice, and a start date "
        "at the next job is the reason a boss says yes.")
# The line "what is burnout" asks for the thing itself, and the card below is written for someone
# in it: "Take the smallest real break first" is the wrong first sentence to a question about what
# the word means. The card is one reply for both, and the wording of the line picks the opening.
_BURNOUT_WHAT = re.compile(r"^(?:what is|whats|what's|what exactly is|tell me about|explain|"
                           r"what does)\b")


def _burnout_card(memory, understood):
    """The burnout advice, or what burnout is when that is what was asked."""
    clean = ((understood or {}).get("clean") or "").strip().lower()
    advice = ("Take the smallest real break first: a day off this week, and one week booked in the "
              "diary that nobody can move. Then bring the load to your manager as a list of what "
              "is due and what you can do, and ask which to drop - burnout is usually a staffing "
              "problem landing on one person. Tell your GP if you are not sleeping or eating "
              "properly, because a sick note is a normal thing to ask for and it protects your job.")
    if _BURNOUT_WHAT.match(clean):
        return ("Burnout is the exhaustion that comes when the demands of a job outrun what you "
                "recover between shifts: tired after a normal night, flat or cynical about the "
                "work, and sure you are getting worse at it. It is a work problem rather than a "
                "weakness, and it eases when the load changes. " + advice)
    return advice

COMPANY_CLOSING = (
    "If the company has paid its bills, filed its accounts and has no debts, the cheap "
    "route is a voluntary strike-off: form DS01, signed by the directors, \u00a38 online, "
    "and it is gone about two to three months later once Companies House advertises it. "
    "Clear the bank account and deal with the assets first - anything left becomes "
    "property of the Crown. If there are debts or a bounce-back loan, do not strike it "
    "off: a members' voluntary liquidation through an insolvency practitioner is the "
    "orderly way, and an accountant will price it."
)

# "each way" is a distance as often as it is a commute: "its about 4 miles each way" in a chat
# about cycling to work, "its 30 miles each way", "the ticket is 20 pounds each way". A distance
# or a price each way is the ride or the fare, not the decision to move house or ask for two days
# at home, so the word counts on its own only when the line also says how long the journey takes.
_EACH_WAY_TIME = ("hour", "hours", "hr", "hrs", "minute", "minutes", "min", "mins")


def _a_journey_that_costs_time(understood):
    """False when "each way" is a distance or a price with no time in the line."""
    if not _said(understood, ("each way",)):
        return True
    return _said(understood, _EACH_WAY_TIME)
# A person saying they do not know what they want is not asking for a method: they are saying
# something hard about themselves, and the composer has a warm short line for it ("Plenty of
# people who look settled are quietly making it up too"). The same words are a question when
# they are asked - "how do i know what i want to do", "what do i want to do with my life" - and
# those have always been answered by the career row, so the test is the shape of the statement,
# not the words in it.
_LOST_IN_WHAT_I_WANT = re.compile(
    r"\b(?:i|im|i'?m|ive|i'?ve)\b[^?.!]*?\b(?:dont|don'?t|do not|never|still dont|"
    r"still don'?t)\s+know\s+what\s+(?:i\s+)?want\b")


# "would suit me" is the plainest way to ask about a career and it is also the plainest way to
# ask about a haircut, a beard and a colour. The work is what this row answers about, so when the
# line turns on "suit" and never names a job, a career or work itself, it is not this question:
# "what would suit me" has no subject at all, and the row's own keys cannot tell the two apart.
_SUIT = re.compile(r"\b(?:suit|suits|suiting|suitable)\b")
_THE_WORK_NAMED = re.compile(
    r"\b(?:job|jobs|career|careers|work|working|profession|professions|trade|trades|role|roles|"
    r"employment|employer|office|industry|vocation)\b")


def _not_a_thing_to_wear(understood):
    """False when the line asks what would suit without naming any work at all."""
    reading = understood if isinstance(understood, dict) else {}
    line = " ".join(str(reading.get("clean") or reading.get("text") or "").lower().split())
    if not _SUIT.search(line):
        return True
    return bool(_THE_WORK_NAMED.search(line))


# A school leaver asking what jobs are there is asking what will take them, which the first-job
# row answers with the places that hire at 16. The avoid list cannot do this one: the age is a
# clause at the end of the line, and the row reaches "what jobs are there" without it.
_SCHOOL_LEAVER = re.compile(
    r"\b(?:1[3-8]|sixteen|fifteen|seventeen|eighteen)s?[\s-]*(?:year|yr)s?[\s-]*olds?\b"
    r"|\bschool[\s-]?leaver|\bjust left school\b|\bleaving school\b|\bleft school\b")


def _not_the_school_leaver_question(understood):
    """False when the person names an age still at school or just out of it."""
    reading = understood if isinstance(understood, dict) else {}
    line = " ".join(str(reading.get("clean") or reading.get("text") or "").lower().split())
    return not _SCHOOL_LEAVER.search(line)


def _not_saying_they_are_lost_or_wearing_it(understood):
    """The row's guards: the lament, the thing to wear, and the school leaver's first job."""
    return (_not_lost_in_what_they_want(understood) and _not_a_thing_to_wear(understood)
            and _not_the_school_leaver_question(understood))


def _not_lost_in_what_they_want(understood):
    """False when the line is the person saying they do not know what they want."""
    reading = understood if isinstance(understood, dict) else {}
    line = " ".join(str(reading.get("clean") or reading.get("text") or "").lower().split())
    return not _LOST_IN_WHAT_I_WANT.search(line)

# The row above answers what an employer owes, so a weekend in the line has to come with a job
# in it. "off" as in "weekends off" and "every other weekend" are rota talk too, and a person
# asking whether they can refuse is asking about the job without naming it.
_WEEKEND_AT_WORK = ("work", "working", "worked", "works", "job", "shift", "shifts", "rota",
                    "rotas", "on the rota", "contract", "employer", "boss", "manager",
                    "colleague", "overtime", "lieu", "payslip", "union", "acas", "paid",
                    "pay", "double time", "on call", "my hours", "leave", "holiday",
                    "day off", "days off", "weekend off", "weekends off", "saturday off",
                    "saturdays off", "sundays off", "every other weekend", "refuse", "refusing",
                    "say no", "turn it down", "turned down", "asked", "asking", "asks",
                    "make me", "make us", "made to", "they want")


# "work" is the verb as often as the noun: "does that work at weekends too" asks whether the
# advice in hand still holds on a Saturday, and it is the advice's own word, not a job.
_WORK_IS_THE_ADVICE = re.compile(
    r"\b(?:that|it|this|those|they|which)\s+(?:work|works|working|worked)\b"
    r"|\bsame\s+(?:work|works)\b")


def _the_weekend_is_a_working_one(understood):
    """Whether the line with a weekend in it is about a job (so the rota answer is the answer)."""
    if _WORK_IS_THE_ADVICE.search(_said_text(understood).lower()):
        return False
    return _said(understood, _WEEKEND_AT_WORK)


# "Stand up" is a body going upright as often as it is a meeting, and both meeting rows key the
# phrase: "how do i stop feeling faint when i stand up" was answered with what to say in a
# stand-up, and so were "how do i stop feeling light headed when i stand up" and "how do i stop
# myself standing up too fast". The rows are right about the room, so the reading decides the
# body: the standing has to happen *to* the person (when/as/every time I stand up, stand up too
# fast, standing up from), or the line names what happens when they do it, and no room is named
# in the line. A stand-up someone speaks in says "stand up" with none of that, and keeps the row.
_STANDING_UP_HAPPENS = re.compile(
    r"\b(?:when|if|as|while|after|before|whenever|every time|each time|the moment|once)\s+"
    r"(?:i|i'm|im|you|he|she|we|they|someone|somebody)\s+"
    r"(?:try(?:ing)?\s+to\s+|have\s+to\s+|has\s+to\s+)?stand(?:s|ing)?\s+up\b"
    r"|\bstand(?:s|ing)?\s+up\s+(?:too|so|from|out of|suddenly|quickly|fast|slowly)\b"
    r"|\bstood\s+up\s+(?:too|so|from|out of|suddenly|quickly|fast)\b", re.I)
# What a person feels at that moment, in the words they use for it, so a line that says the
# symptom without the "when i" still reads as the body: "light headed standing up",
# "my vision goes when i get up".
_A_BODY_UP_WORD = re.compile(
    r"\b(?:dizzy|dizziness|dizzier|faint|fainting|light[- ]?headed|head rush|woozy|giddy|"
    r"swimmy|head spins|head spinning|head swims|saw stars|see stars|stars in front of my "
    r"eyes|vision (?:goes|went)|blood pressure|orthostatic|black out|blackout)\b", re.I)
# A room in the line keeps the meeting rows, whatever else it says: "dizzy in the stand-up" is
# not a question this bot can answer well, but "how do i speak up in the stand-up" is.
_A_ROOM_NAMED = re.compile(
    r"\b(?:meeting|meetings|stand-?up meeting|standup|team call|video call|conference call|"
    r"group call|weekly call|board meeting|agenda|at work|in the office|my team)\b"
    # the room said as a room: "in the stand up", "our stand-up", "this morning's stand up",
    # which is what people call the meeting whose turn it is somebody's to speak in
    r"|\b(?:the|our|your|their|a|this|daily|morning|weekly|team|nine o'clock)\s+stand[- ]?up\b",
    re.I)


def a_body_standing(understood):
    """True unless the line's "stand up" is a body going upright, in a line with no room in it."""
    if not isinstance(understood, dict):
        return True
    said = understood.get("text") or understood.get("clean") or ""
    if not said:
        said = " ".join(understood.get("words") or ())
    said = str(said)
    if not said or _A_ROOM_NAMED.search(said):
        return True
    if _STANDING_UP_HAPPENS.search(said):
        return False
    if _A_BODY_UP_WORD.search(said) and re.search(r"\bstand(?:s|ing)?\s+up\b|\bgetting up\b",
                                                  said, re.I):
        return False
    return True


# The verb "meet" is about people; the noun "meeting" is about a room, and the matcher reads one
# as the other. "how do i meet new people" and "how do i meet someone" were answered with tactics
# for saying one thing in a room of colleagues.
_MEET_VERB = re.compile(r"\bmeet\b", re.I)


def _the_room_and_not_the_verb_meet(understood):
    """The speaking-up row's guard: a body standing is not the room, and meeting people is not one.

    False when "meet" is the verb about people and the line names no room ("how do i meet new
    people", "how do i meet someone"). A line that names the room - "in a meeting", "in
    meetings", "on a team call", "at work" - keeps the row, and so does every line without the
    verb at all.
    """
    if not a_body_standing(understood):
        return False
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "")
    if not said and isinstance(understood, dict):
        said = " ".join(str(one) for one in (understood.get("words") or ()))
    if not _MEET_VERB.search(said):
        return True
    return bool(_A_ROOM_NAMED.search(said))


# A job in a named place is a different question from how to look for work: the way in, the
# certificate and the check are the employer's own. "how do i get a job in a care home", and the
# same line about a supermarket, a school, a cafe, a warehouse, a nursery, a hospital, a hotel
# or a charity shop, all got the split-your-week-in-half plan, which names none of it. One row
# reads the place out of the line, so a new place is one more line of data.
JOB_PLACES = (
    ("care home", ("care home", "care homes", "nursing home", "nursing homes",
                   "residential home", "residential homes", "care work", "care worker",
                   "care assistant", "support worker")),
    ("charity shop", ("charity shop", "charity shops", "oxfam", "hospice shop")),
    # a bare "shop" was the one place word that still fell to the plan: "how do i get a job in a
    # shop" got the split-your-week plan, so a shop and a store are here with the supermarkets.
    # The charity shop is read first, below, because it is a shop too and its way in is its own.
    ("supermarket", ("supermarket", "supermarkets", "tesco", "asda", "sainsburys", "aldi",
                     "lidl", "morrisons", "iceland", "waitrose", "retail", "retail job",
                     "retail work", "shop job", "shop work", "shop floor", "till work",
                     "store work", "shop", "shops", "store", "stores")),
    ("school", ("school", "schools", "primary school", "secondary school", "teaching assistant",
                "teaching assistants", "midday supervisor", "school office")),
    ("cafe", ("cafe", "cafes", "coffee shop", "coffee shops", "barista", "restaurant",
              "restaurants", "pub", "pubs", "bar work", "bar staff", "bar job", "bar jobs",
              "barman", "barmaid", "bartender", "waiter", "waitress", "bar", "bars",
              "kitchen assistant", "waiting staff")),
    ("warehouse", ("warehouse", "warehouses", "picking job", "packing job", "pickers",
                   "packers", "forklift", "distribution centre", "distribution center")),
    ("nursery", ("nursery", "nurseries", "nursery assistant", "childcare", "nursery nurse",
                 "preschool", "pre-school")),
    ("hospital", ("hospital", "hospitals", "nhs", "healthcare assistant",
                  "health care assistant", "hca", "porter", "porters")),
    ("hotel", ("hotel", "hotels", "housekeeping", "room attendant", "room attendants",
               "guest house")),
    ("council", ("council", "councils", "local authority", "council job", "council jobs",
                 "civil service")),
)

JOB_PLACE_REPLIES = {
    "care home": "No experience needed, and care homes are always short: apply on the home's "
                 "own website or walk in and ask for the manager. They pay for your DBS check, "
                 "and you do the Care Certificate in the first twelve weeks.",
    "supermarket": "Apply on the store's own careers page, no CV needed, and tick evenings and "
                   "weekends as well. Till and shelf work needs no experience, and the "
                   "interview is mostly 'tell me about a time you helped someone', so have one "
                   "ready.",
    "school": "Ring the school office and ask to go on their supply or cover list for teaching "
              "assistant, midday supervisor and admin work, because the office hires all year. "
              "All of them need a DBS check, which takes a few weeks, so start now.",
    "cafe": "Walk in between two and four, when it is quiet, with a one-page CV, and ask for the "
            "manager by name. Cafe and bar work needs no certificate, though a free Level 2 food "
            "hygiene course online helps, and the shifts go to whoever can start this week.",
    "warehouse": "Sign up with two or three local agencies, then take one shift to get a foot "
                 "in. Warehouses take packers and pickers with no experience, and the agency "
                 "does the paperwork.",
    "nursery": "Ask the nurseries near you about assistant jobs. You need a DBS check, but not a "
               "qualification to start: they take unqualified staff and put you through the "
               "Level 2 childcare course in the job.",
    "hospital": "Search the NHS jobs site for the trust's own vacancies rather than a job board: "
                "porters, cleaners, admin staff and healthcare assistants mostly need no "
                "experience. The DBS and the health checks come after they offer you the job.",
    "hotel": "Ask at reception for the housekeeping or kitchen manager and apply direct. Hotels "
             "take on room attendants and kitchen porters with no experience, and the hours "
             "often fit round a school run.",
    "charity shop": "Volunteer in one first. The manager will take you for a few hours a week on "
                    "no more than a form, and that counter experience is what a paid retail job "
                    "wants to see.",
    "council": "Apply on the council's own jobs page rather than a job board, because they use an "
               "application form, not a CV. It is scored against the person specification, so "
               "answer each line of that with one example and use its own words.",
}


# A place named as a landmark or as a time is not the employer. "how do i get a job near my kids
# school" is a question about an area and "how do i get a job after being in hospital" is a
# question about a gap, and both were handed the way into a school and into the NHS. The place
# word has to be the workplace the line asks the way into, so a place within a few words of one
# of these is read as the landmark it is and the search carries on.
JOB_PLACE_LANDMARK = re.compile(
    r"\b(?:near|nearby|close to|next to|round the corner from|outside|away from|after|before|"
    r"since|until)\b(?:\W+\w+){0,4}\W*$")

# A place word is also how people say *when* they can work, or who they look after while they do
# it. "how do i get a job while my kids are at school", "how do i get a job that fits round
# school pickup" and "how do i find work that fits round school hours" are all questions about
# the hours, and each was handed the school office's supply list; the same line about a nursery
# was handed the nursery's. Where the line names the person being cared for, the pickup, or the
# hours a job has to fit round, the place is the constraint and not the employer.
JOB_PLACE_AS_A_CONSTRAINT = re.compile(
    r"\b(?:my|our|the)\s+(?:kid|kids|child|children|son|daughter|family)\b"
    r"|\b(?:kid|kids|child|children)\b\s+(?:are|is|at|off|back|in)\b"
    r"|\bpick ?up\b|\bdrop ?off\b|\bschool run\b|\bschool hours\b|\bterm time\b"
    r"|\bfits? round\b|\bfitting round\b"
    r"|\bround\b(?:\W+\w+){0,3}\s(?:school|nursery|nurseries|kids|children)\b"
    r"|\bwhile\b(?:\W+\w+){0,6}\s(?:school|nursery|nurseries|kids|children)\b"
    r"|\bwhen\b(?:\W+\w+){0,5}\s(?:kids|children)\b")


def _job_in_a_place(memory, understood):
    """The way into a named workplace, or None when the line names no place this knows."""
    clean = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    clean = re.sub(r"[^a-z0-9' ]+", " ", clean)
    for place, words in JOB_PLACES:
        for word in words:
            match = re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", clean)
            if (match and not JOB_PLACE_LANDMARK.search(clean[:match.start()])
                    and not JOB_PLACE_AS_A_CONSTRAINT.search(clean)):
                return JOB_PLACE_REPLIES[place]
    return None


def _not_a_named_place(understood):
    """The job-hunt plan stands down when the line asks the way into a named workplace.

    A word in the plan's avoid list cannot do this job: every place word here - school, hospital,
    council, nursery, cafe, hotel, supermarket, retail - is also an ordinary word, and a bare one
    of them stood the plan down on "how do i get a job near my kids school" and left the line on
    a chores card. The guard asks the place row itself whether it has an answer.
    """
    return _job_in_a_place(None, understood) is None


JOB_PLACE_WORDS = tuple(word for _place, words in JOB_PLACES for word in words)


# The offer in hand, asked about as a job to be done rather than as a choice to be made. The row's
# ask list can only hold the phrasings somebody thought of, and "how do i handle a job offer",
# "how do i deal with the job offer" and "how do i respond to a job offer" were all shrugs on
# main, while "should i accept it" was answered: one question in three wordings. The ask is a
# shape, so every verb in it counts the same, and the offer is what the row's key names - the
# shape only has to say the line is asking what to do about something.
_A_WHAT_TO_DO_ASK = re.compile(
    r"\b(?:how (?:do|should|can|could|would)\s+(?:i|we)|what (?:do|should|can|could)\s+(?:i|we)|"
    r"what now|what next|what to do|any advice|some advice|advice on|help me|should i|"
    r"is it worth|worth it)\b", re.I)


def _asks_what_to_do(clean):
    return bool(_A_WHAT_TO_DO_ASK.search(clean))


# The verbs a wage that never came is said with, and the pay it is owed under. A verb alone is
# a lunch, a haircut or a holiday ("i havent had my hair cut in months"), so each verb is
# written with each pay noun and the phrase is what the unpaid-wages row matches. That is one
# mechanism for every wording of the same claim rather than a list of the ones we happened to
# see: "i havent had my holiday pay", "i still havent had my wages", "i havent had any pay from
# them", "my holiday pay is missing" and "i didnt get my bonus" all come out of it.
_WAGE_VERBS = ("havent had", "haven't had", "have not had", "hadnt had", "hadn't had", "hasnt had",
               "hasn't had", "havent received", "haven't received", "have not received",
               "has not received", "not received", "never received", "didnt receive",
               "didn't receive", "never got", "didnt get", "didn't get", "havent got",
               "haven't got", "not got")
_WAGE_NOUNS = ("my pay", "my wages", "my wage", "my salary", "my bonus", "my holiday pay",
               "my money", "my commission", "my earnings", "my income", "my final pay",
               # A payslip is the paper, not the wage: "i didnt get my payslip" and "my payslip
               # is missing" are the payslip rows' questions (there is a row for reading one and
               # a row for one that came out short), and with "my payslip" in this table they
               # were told to write to payroll about the money.
               "my final wages", "my overtime pay", "my pay packet", "my paycheck",
               "any pay", "any wages", "any money", "the pay", "the wages", "the bonus",
               "the money", "the salary", "the holiday pay")
_WAGE_MISSING = ("is missing", "isnt there", "isn't there", "hasnt come", "hasn't come",
                 "never came", "did not come", "didnt come", "didn't come", "hasnt arrived",
                 "hasn't arrived", "has not arrived", "did not arrive", "didnt arrive",
                 "didn't arrive", "never arrived", "never turned up", "did not turn up",
                 "hasnt gone in", "hasn't gone in", "has not gone in", "hasnt come through",
                 "hasn't come through")
_UNPAID_WAGE_PHRASES = tuple(
    ["%s %s" % (verb, noun) for verb in _WAGE_VERBS for noun in _WAGE_NOUNS]
    + ["%s %s" % (noun, tail) for noun in _WAGE_NOUNS for tail in _WAGE_MISSING]
)

ENTRIES = [
    # A late filing is a question with a number in the answer, and the penalty climbs in bands:
    # "what happens if i file my accounts late" was the honest shrug while "i missed my
    # confirmation statement deadline" got "Ugh, that's annoying" - a shrug at a fine.
    entry("late-filing",
          # The key is a filing and a filing word: "missed" alone is in it, so the second group
          # has to name what was missed. Without that, "i missed my deadline" and "i missed the
          # court deadline" were scored as Companies House and told the penalty for a private
          # company's accounts, which is a confident wrong fact where a hedge was before.
          (("late filing", "file late", "filing late", "file my accounts late", "late accounts",
            "accounts are late", "accounts late", "filed late", "late confirmation statement",
            "confirmation statement is late", "penalty for filing late",
            "penalty for late filing", "fine for late filing", "late filing penalty",
            "what happens if i file late", "missed"),
           # "account" and "pay" are the words of a payment, not a filing: with those two in,
           # "i missed my bank account payment" was told the Companies House bands, which is
           # \u00a3150 of confident wrong fact for a missed direct debit. The plural "accounts"
           # is the filing and stays.
           ("companies house", "accounts", "confirmation statement", "annual return",
            "statutory accounts", "self assessment", "late filing", "late_filing",
            "penalty", "fine", "fines")),
          "File it today anyway: Companies House fines you automatically and the penalty climbs "
          "in bands, so filing now costs no more than filing next week within the same band. "
          "For a private company's accounts it is \u00a3150 up to a month late, \u00a3375 up to "
          "three months, \u00a3750 up to six, and \u00a31,500 beyond that, and it doubles if you "
          "file late two years running. A late confirmation statement is \u00a3150, up to "
          "\u00a31,500 if it keeps happening. Self assessment is separate: \u00a3100 the moment "
          "it is late, then \u00a310 a day after three months. If the company cannot pay, the "
          "fine is still there, so tell Companies House rather than going quiet.",
          # a missed bill, card or direct debit is a payment, not a filing, and it has rows
          # "how much" and "what happens" were in the second group and are not filing words, so
          # with "missed" in the first they caught a missed bill: "i missed my payment this month
          # what happens" and "i missed my electricity bill what happens" were told the Companies
          # House bands. The phrases that answer those questions, "late filing penalty" and
          # "file my accounts late", are already whole phrases in the first group.
          avoid=("bank", "bank account", "direct debit", "credit card", "debit card", "my card",
                 "card payment", "payment", "payments", "bill", "bills", "loan", "overdraft",
                 "rent", "mortgage", "council tax", "energy bill", "phone bill", "water bill",
                 "electricity", "gas", "insurance", "subscription", "invoice")),

    # --- the eight situations this branch adds ------------------------------------
    entry("underpaid-vs-newstarter",
          (("underpaid", "paid less", "paying me less", "gets paid more", "paid more than me",
            "new starter", "new guy", "new girl", "new colleague", "same job as me",
            "less than the new", "pay is lower", "lower than", "earn less", "earning less",
            "earns more", "earn more"),
           ("should i", "boss", "manager", "ask", "raise", "fair", "found out", "how do i",
            "what do i", "talk", "worth", "compared", "than me", "the same job", "colleague",
            "colleagues", "starter", "what i do",
            # "i'm paid less than the man next to me" names the comparison, not an ask, and it
            # names nobody the other keys knew: the person is his age and grade, sat beside him.
            "man", "woman", "guy", "lad", "beside", "next",
            # and the way people open the subject names no ask at all: "i think im being
            # underpaid" is the whole line, so the words that say it is a suspicion count
            "think", "im being", "being", "seems", "seem", "is that", "wonder")),
          "Argue your market rate, not someone else's pay: write down what you deliver with "
          "numbers, check two adverts for the same title and area, then ask for a meeting about "
          "your pay and name a figure. Do not lead with what a colleague earns - it puts them in "
          "the room instead of you, and in some contracts you are not meant to know. If the answer "
          "is no, ask what would have to be true for a yes and when to come back.",
          avoid=("tax", "taxes", "tax code", "energy", "electricity", "gas bill", "invoice",
                 # "the new starter is lazy" is a complaint about the person, not a pay
                 # comparison, though "new starter" is in this key and effort is not.
                 "lazy", "laziness", "slacking", "slacking off", "skiving", "skiver",
                 "does no work", "doesnt do any work", "doesn't do any work",
                 "not pulling their weight", "not pulling his weight",
                 "not pulling her weight", "work shy", "workshy",
                 # a couple's earnings are a household-money question, not a work one
                 "husband", "wife", "partner", "boyfriend", "girlfriend", "my ex",
                 # and the line does not have to name the person: "we split the rent 60 40
                 # because i earn more is that fair" is about how two people share a cost,
                 # which the money entry answers. The suspicion words above ("is that") reach
                 # it, so the sharing itself has to stand this entry down.
                 "split", "splitting", "share the rent", "share the bills",
                 "bills by income", "60 40", "50 50", "70 30",
                 # the same question in the words people actually use for a household
                 "rent", "mortgage", "household", "bills", "bill", "split the rent",
                 "split the bills", "who pays", "living together", "move in together",
                 "flatmate", "housemate", "roommate")),

    entry("nothing-to-do-at-work",
          (("nothing to do", "no work to do", "bored at work", "bored out of my mind", "day drags",
            "drags at work", "deskilling", "underused"),
           ("work", "job", "office", "day", "how", "what should i do", "boss", "manager", "ask",
            "quit", "leave")),
          "Use the empty time rather than hide it: ask your manager for one thing the team keeps "
          "putting off - a tidy-up, a how-to page, the report nobody has time for - and do it "
          "properly. Keep a note of what you take on, because \"I had nothing to do\" is a reason "
          "to be cut and \"I fixed this\" is a reason to be kept. If it lasts months, the job is "
          "the problem, and looking is cheaper than waiting.",
          avoid=("study", "studying", "exam", "kids", "children", "retired", "day off",
                 "holiday", "sick")),

    # "i keep getting given the boring jobs" is not the empty-desk answer: there is plenty of work,
    # it is just the dull half of it. The ask is for the interesting piece and a fair share of the
    # rest, so it gets its own entry rather than the tidy-up-the-team's-backlog one.
    entry("boring-jobs",
          (("boring jobs", "boring tasks", "boring work", "the boring jobs", "given the boring",
            "only get the boring", "always get the boring", "always the boring", "dull jobs",
            "dull work", "the dull jobs", "keep giving me the boring",
            # "boring" alone was taking questions about the bot: after a line about a baby,
            # "do you ever get bored" reached this entry through the inherited topic and got
            # the dull-jobs answer. A bare adjective says nothing about whose day is dull, so
            # the key is the person or the job itself.
            "i'm bored", "im bored", "i am bored", "bored of my job", "bored in my job",
            "bored at my job", "bored of work", "job is boring", "job's boring",
            "work is boring", "works boring", "day is boring", "boring day at work",
            "so dull", "so boring", "watch the clock", "clock watching", "mind numbing",
            "mind-numbing"),
           ("work", "job", "boss", "manager", "team", "how", "ask", "always", "keep", "keeps",
            "getting", "given", "review", "everyone", "rota", "share")),
          "Ask for the interesting work by name rather than waiting to be noticed: \"I'd like a go "
          "at the reporting - could I take one piece of it next month?\" Pick a small piece so a yes "
          "is easy, and say what you would drop to fit it in. Then ask for the dull jobs to be "
          "shared out rather than defaulting to you, and agree a date to look at it again in three "
          "months. If nothing changes by then, the job really is only the boring half, and that is "
          "worth knowing before you decide to stay.",
          avoid=("nothing to do", "no work", "day drags", "kids", "children", "school",
                 "homework", "exam", "revision", "dinner", "housework", "cleaning")),

    # "my job never teaches me anything" is not the no-training answer (nobody was shown how) and
    # not the boring-jobs one (the work is dull, not absent): the ask is to learn something new
    # in the job you already have, and to know when to stop asking.
    entry("job-teaches-nothing",
          (("never teaches", "teaches me nothing", "not learning anything", "learning nothing",
            "no new skills", "nothing new to learn", "stopped learning", "same thing every day",
            "no growth", "repetitive", "monotonous", "monotony"),
           ("job", "work", "career", "skills", "learn", "should i", "what do i", "how do i",
            "leave", "stay", "boss", "manager", "worth", "day", "every")),
          "Ask for one thing that stretches you rather than waiting to be taught: a piece of the "
          "reporting, a supplier call, the job nobody has written down - and say you want to learn "
          "it, not just do it. Then ask your manager what the next skill for your role is and who "
          "could show you, and put a review date on it. If six months pass with no new work and no "
          "answer, the job has stopped teaching you, and that is a reason to look rather than a "
          "fault in you.",
          avoid=("school", "university", "college", "gcse", "a-level", "a level", "student",
                 "kids", "children", "my son", "my daughter", "driving")),

    entry("no-training-on-a-task",
          (("no training", "without training", "havent been trained", "haven't been trained",
            "not been trained", "no induction", "no handover", "thrown in at the deep end",
            "expected to know"),
           ("boss", "manager", "task", "work", "how", "asked me", "given me", "started",
            "new job", "system", "software", "till", "machine", "show me")),
          "Say it early and about the work, not your ability: \"I haven't been shown how this "
          "system works - could someone spend twenty minutes with me, or is there a guide?\" Then "
          "do the safe part you can and write down each question as it comes, so one conversation "
          "answers all of them. In a new job ask for an induction list; if there is none, keep your "
          "own note of who to ask for what.",
          avoid=("gym", "dog", "puppy", "baby", "potty")),

    # "my apprentice is not learning fast enough" went to a revision-timetable answer, because
    # "learn" plus "fast" is how the learn-to-the-test row is keyed. A person you are teaching at
    # work is the other side of `no-training-on-a-task`: nobody is failing them, the teaching is
    # what has to change, and this is the row for that.
    entry("teaching-someone-at-work",
          (("apprentice", "trainee", "new starter", "the new guy", "the new girl", "new boy",
            "new lad", "my junior", "junior member", "shadowing me", "sits with me",
            "learning slowly", "slow to learn", "not learning fast", "not picking it up",
            "keeps making the same mistake", "keeps getting it wrong", "not getting it",
            "isnt getting it", "isn't getting it", "wont ask questions", "won't ask questions",
            "asks the same question", "forgets what i told them", "forgets what i showed them"),
           MANAGING_ASKS),
          "Show it once, then watch them do it once, then let them do it alone with you a few "
          "feet away: most of what looks like slowness is a step nobody said out loud. Write the "
          "five or six steps on one page they can keep, do the same fifteen minutes at the same "
          "time each day rather than a long session on Friday, and ask them to explain it back to "
          "you before you decide it has not gone in - if they cannot explain it, the teaching "
          "missed rather than the learner. Say what \"good\" looks like with one finished example "
          "to copy, and when they get it wrong let them find it before you take the mouse: the fix "
          "they make themselves is the one that sticks. Tell them plainly where they are and what "
          "good looks like by when, so slow is a fact you both know rather than a worry.",
          avoid=("my son", "my daughter", "my child", "my kids", "my dog", "my cat", "puppy",
                 "school", "gcse", "a-level", "exam", "revise", "revision", "driving",
                 "to drive", "potty", "reading", "maths homework",
                 # "the new starter is lazy" is not a teaching question: the person has decided
                 # the problem is effort, and this card's answer ("show it once, write the steps
                 # down") would be advice for a worry they did not raise. It took this card
                 # once "new starter" joined the key, so the effort words stand it down and the
                 # lazy-colleague row keeps the line.
                 "lazy", "laziness", "slacking", "slacks", "skiving", "skives", "skiver",
                 "never does any work", "does no work", "doesnt do any work",
                 "doesn't do any work", "not pulling their weight", "not pulling his weight",
                 "not pulling her weight", "coasting", "taking the mick", "work shy",
                 "workshy",
                 # the other side of the same line: "im the new starter and i feel lost" is
                 # the new person's own first week, and this card is written to the person
                 # teaching them ("show it once, watch them do it once").
                 "i feel lost", "im the new starter", "i'm the new starter",
                 "i am the new starter", "i just started", "im new here", "i'm new here",
                 # and "i have to train a new starter while doing my job" is a question about
                 # the time it takes, not about the teaching: the workload card answers it.
                 "while doing my job", "while doing my own job", "on top of my job",
                 "on top of my own work", "no time to train", "time to train",
                 "time to show")),

    entry("priorities-keep-changing",
          (("priorities", "priority", "everything is urgent", "drop everything", "keeps changing",
            "changes every week", "moving target", "flavour of the month", "new ask"),
           ("team", "boss", "manager", "work", "how", "plan", "week", "cope", "deal", "handle")),
          "Ask for the list in order, in writing: \"Which two of these are the priority this week, "
          "and which can wait?\" Work the top one, and send a one-line note when a new ask pushes "
          "something down: \"Taking this on, so the other thing moves to Friday.\" A manager who "
          "cannot name two priorities has told you something; keep that email.",
          avoid=("deadline", "deadlines", "exam", "revision", "rota", "shift", "shifts",
                 "at home", "home", "house", "kids", "children", "dinner", "chores", "budget",
                 "cleaning", "tidy")),

    entry("boss-is-leaving",
          (("boss is leaving", "manager is leaving", "boss left", "manager left", "boss resigned",
            "manager resigned", "boss is resigning", "manager is resigning", "boss resigning",
            "manager resigning", "boss handed in", "manager handed in",
            "who do i report to", "who i report to", "who i should report to", "no manager",
            "without a manager",
            "boss is going", "manager is going", "boss quit", "manager quit",
            "boss has gone", "manager has gone"),
           # the second group is what the person wants to know, not another word for the boss
           # leaving: "my manager resigned" carries only the first group on its own, so without
           # these the resignation-letter entry answered for the boss's notice too.
           ("leaving", "left", "who", "report", "now", "work", "team", "what do i do",
            "should i", "resigning", "resigned", "resigns", "quitting", "quit", "gone",
            "last day", "last week", "takes over", "taking over", "taken over", "cover",
            "covers", "nobody", "anyone", "handed", "who takes", "report to", "notice")),
          "Ask before they go who is taking over your work, and get it in one sentence: \"While "
          "this is covered by Y, approvals go to Y.\" Then introduce yourself to that person with "
          "a short list of what you own and what is due. If nobody is named, ask HR in writing who "
          "your line manager is now - it is an ordinary question, and the answer is what you point "
          "at when a review goes wrong.",
          # writing your own letter is the resignation-letter entry's line, not this one
          # "boss left" is also the start of "my boss left me out of the meeting", which is the
          # being-left-out question and not a resignation: the words that say left OUT go here.
          avoid=("resignation letter", "notice letter", "my notice", "reference", "letter",
                 "i want to quit", "i want to resign", "how do i resign", "how do i quit",
                 "i handed in", "i hand in", "write my", "draft",
                 # NOT the bare "left out" or "left out of": "my boss left out of the blue" is a
                 # resignation, and "left out of" is inside it. The pronoun is what separates the
                 # two - left ME out is being ignored, left out of the blue is leaving.
                 "left me out", "left us out", "out of the loop"),
          # wording.py's resignation-letter entry keys on "resign"/"quit"/"left" and reads
          # "my manager resigned" as the person's own notice; on those lines the reporting
          # question is the one being asked, so this entry steps ahead of it
          bias=2),

    entry("sabbatical",
          # "unpaid leave" is not here: main's pay-and-hours entry owns the legal question
          # ("can i take unpaid leave") and answers it with the right to refuse.
          (("sabbatical", "career break", "year off work", "time off work for a",
            "extended leave", "long leave", "months off work"),
           ("ask", "how", "boss", "manager", "request", "take", "worth", "can i")),
          "Ask months ahead and bring the plan with you: how long, from when, who covers your "
          "work, and how you keep your hand in while you are away. Read the contract and handbook "
          "first - some employers hold the job for a set period, and some let you buy extra leave "
          "instead. Ask in writing, propose a review date for the return, and get the answer in "
          "writing too.",
          avoid=("sick", "maternity", "paternity", "adoption", "bereavement", "funeral", "carer",
                 "carers", "hospital", "unpaid", "zero hours", "zero-hours", "entitled",
                 "legal", "law")),

    entry("wfh-permanent",
          (("work from home permanently", "work from home full time", "wfh permanently",
            "work from home for good", "remote permanently", "fully remote", "always work from home",
            "home every day"),
           ("ask", "how", "boss", "manager", "request", "can i", "allowed", "possible",
            # saying you want it is asking for it, whatever the question mark says
            "want", "wanting", "wanted", "would like", "like to", "prefer", "thinking of")),
          "Ask in writing, with the case in numbers: what you got done from home, how you stay "
          "reachable, and the one day a week you would come in for the parts that need a room. "
          "Most managers say yes to a trial far more easily than to a permanent change, so ask for "
          "three months and a review date, and offer to keep the desk hot for the team days.",
          avoid=("how many days", "how often", "twice a week", "two days", "three days")),

    entry("fired-for-being-off-sick",
          (("fired", "sacked", "dismissed", "lose my job", "losing my job", "let go"),
           ("off sick", "sick", "illness", "ill", "sick leave", "sick note", "hospital",
            "operation", "anxiety", "depression", "stress leave")),
          "Being off sick is not in itself a reason to be sacked, but long or repeated absence is "
          "handled as an attendance or capability issue, and that has steps: a meeting, a chance to "
          "improve, usually a warning first. Ask for the policy in writing, ask to be referred to "
          "occupational health, and take a union rep or a colleague into any meeting. ACAS advises "
          "free. Keep every sick note and every letter.",
          avoid=("redundancy", "redundant", "redundancies", "resign", "resigning", "quit")),


    # --- the situations this branch adds -------------------------------
    entry("badge-bio",
          (("bio", "biography", "badge", "nametag", "name tag", "profile line", "one liner",
            "two line bio", "two-line bio"),
           ("conference", "talk", "badge", "write", "short", "line", "introduce myself",
            "networking", "profile", "job")),
          "Give your role, your experience and one thing you care about, and leave out the "
          "adjectives: \"Registered nurse, eight years in A&E, interested in how teams hand over "
          "at shift change.\" Two lines is about 25 words, so cut anything a stranger could not "
          "ask a follow-up question about - and keep the thing you want to talk about.",
          # someone naming a bio is asking how to write it, whatever job they name as well:
          # "...for a conference badge? I'm a nurse" was answered with nursing's GCSEs
          bias=3),

    entry("bullying-at-work",
          (("bully", "bullying", "bullied", "harassed", "harassment", "picked on", "picks on me",
            "jokes about me", "joke about me", "makes fun of me", "making fun of me",
            "belittles me", "belittled me", "picks on",
            "shouted at", "shouting at me", "humiliates", "humiliated me", "intimidated",
            "threatened me",
            # "a boss who shouts" and "my manager yells" are the same conduct in other tenses
            "shouts", "shouts at me", "shouting", "yells", "yells at me", "yelling",
            "screams at me", "screaming at me", "loses his temper", "loses her temper"),
           ("work", "boss", "manager", "colleague", "at work", "what do i do", "how do i",
            "report", "hr", "deal with", "stop")),
          _bullying,
          avoid=("school", "playground", "son", "daughter", "child", "kid", "online",
                 "instagram", "facebook")),

    entry("burnout",
          (("burnt out", "burned out", "burning out", "burnout", "exhausted by work",
            "work is exhausting",
            "running on empty", "cant cope with work", "can't cope with work", "drained by work",
            "work is too much for me"),
           ("work", "job", "what do i do", "how", "help", "boss", "manager", "recover",
            "off work", "rest", "think", "feel", "feels", "im", "lately",
            # "i dont know what to do" is its own request for help, and it is the way a person
            # says a work problem has run past what they can fix: "im burnt out at work and i
            # dont know what to do" was a shrug with the complaint already in the line.
            "dont know what to do", "don't know what to do", "not sure what to do",
            "know what to do")),
          _burnout_card,
          # "what is burnout" was a shrug, though this is the card for it: the row is the answer
          # to a person asking what it is, not only to one saying it is happening to them, so a
          # plain request to explain it is its question too.
          explain=True,
          avoid=("car", "engine", "candle", "toast", "dinner", "oven", "calories",
                 # a giving-up line is a safety reply, not a work one
                 "giving up", "give up", "gave up", "no point", "hopeless", "cant go on",
                 "can't go on", "dont want to be here", "don't want to be here", "hurt myself",
                 "not worth it",
                 # worn out by caring, not by a job
                 "being a mum", "being a dad", "being a parent", "as a mum", "as a dad",
                 "a mum of", "a dad of", "being a carer", "carer for", "caring for",
                 "looking after",
                 # a team that is burnt out is the manager's question, not this one: the card
                 # below is written to the person who is worn out, and its first step is to take
                 # a day off, which is the wrong side of the desk for the person who runs the
                 # rota. "my team is burnt out and i dont know what to do" was a shrug, and both
                 # halves of the answer were wrong until it had its own row.
                 "my team", "my staff", "my people", "our team", "my reports")),

    entry("colleague-lazy",
          (("colleague", "coworker", "co-worker", "teammate", "team mate", "workmate",
            "someone on my team", "one of my team", "guy on my team", "person on my team",
            # "a team member who does nothing" is the same complaint as "a lazy coworker", and
            # it was the one wording the key did not carry
            "team member", "team members",
            # the person said as "someone" or as staff: "how do i manage someone who does
            # no work" was a search shrug, "one of my staff isnt pulling their weight" was
            # "Got it. Is there anything you'd like a hand with?" and "my apprentice does
            # the minimum" was only echoed back. The complaint is the row's own question.
            "someone who does", "someone who never", "someone who doesnt",
            "someone on my shift", "my staff", "one of my staff", "staff",
            "employee", "employees", "junior", "junior member", "apprentice",
            "my report", "the new guy", "the new starter",
            # "my new starter is really lazy" was the pay row's (see the avoid there) and then
            # a shrug, because the key carried "the new starter" and people write "my" or
            # nothing at all.
            "new starter", "new colleague"),
           ("pull their weight", "pulling their weight",
            "not pulling", "lazy", "does nothing",
            "doesnt do", "doesn't do", "skives", "avoid work", "slack", "does the "
            "minimum", "not doing their share", "dumps work", "doesnt help", "doesn't help",
            "does any work", "does no work", "never does any work", "never does anything",
            "never helps", "doesnt do anything", "doesn't do anything")),
          "Deal with the specific work, not the character, and say it once to them first: \"When "
          "the shift plan is left to me, I end up doing both - can we split it so you take the "
          "weekends?\" If nothing changes, ask your manager for a short meeting and talk about the "
          "work that is not being covered rather than the person, with two recent examples and "
          "dates. Ask for a written split of who does what; most of this ends when the "
          "responsibility is written down.",
          avoid=("bully", "bullying", "threaten", "shouts", "rude")),

    # Two people who cannot work together is not the lazy-colleague question and it is not the
    # bully question: nothing is being done to the manager, and the work still has to get done by
    # two people who will not speak. "i manage two people who hate each other" got "Ugh, that's a
    # lot to carry. What would make today a bit easier?", which is the bot shrugging at a
    # management question.
    entry("two-people-who-clash",
          (("hate each other", "hates each other", "cant stand each other",
            "can't stand each other", "dont get on", "don't get on", "doesnt get on",
            "doesn't get on", "wont work together", "won't work together", "personality clash",
            "clash", "clashes", "clashing", "two people who", "two of my staff", "warring",
            "bickering", "always arguing", "argue all the time", "fight constantly",
            "squabble", "squabbling", "undermine each other", "not speaking to each other"),
           MANAGING_ASKS),
          "Treat it as a work problem with a work rule, not a feelings problem: name the two "
          "behaviours you have seen, with dates, and set what has to happen on a shift (who "
          "answers the phone, who signs off what) so the job does not need them to like each "
          "other. See them together once, then separately, because each will tell you a different "
          "story and both are partly true. Anything that is bullying, threats or a refusal to "
          "work goes down in writing and up to HR or your own manager, because the longer it "
          "drifts, the more it is your problem rather than theirs.",
          # The two people at home keep their own script: the bias below lets this row win on the
          # words two rows share ("argue all the time"), so the couple words have to be named
          # here, or "we argue all the time and i dont know how to stop it" gets the work rule.
          avoid=("my kids", "my children", "siblings", "brother", "sister", "dog", "cat",
                 "neighbours", "my ex", "husband", "wife", "partner", "boyfriend", "girlfriend",
                 "we argue", "we row", "we fight", "me and my", "my mum", "my dad", "my friend",
                 "flatmate", "our marriage",
                 # a war is a name, and "war" is read as a form of the key word "warring": with
                 # "how" in the ask list, "how did the first world war end" had both signals and
                 # was told to sit down with two people who will not speak. History questions
                 # name a war, a year or a battle, so those words hold this row out of them.
                 "world war", "first world war", "second world war", "war one", "war two",
                 "war 1", "war 2", "ww1", "ww2", "wwi", "wwii", "great war", "1914", "1918",
                 "1939", "1945", "armistice", "treaty", "versailles", "battle", "sarajevo"),
          # the staff words are what this row is here for, and family.py's row for a couple who
          # row sits on the same words ("argue", "not speaking to each other") with its own
          # script for a partner. Bias, not an avoid list on their file: the line names staff.
          bias=2,
          # a named war is not a clash between two members of staff (see `A_NAMED_WAR`)
          guard=_a_named_war),

    # "my staff are scared of me" and "my team ignores my ideas" are one question: the team has
    # gone quiet, and the manager needs to make it safe to speak. Both were shrugs ("That sounds
    # rough. If you want, I can help you think through what to do next.").
    # A manager whose team is worn out is asking what to do about the week, not asking for a
    # day off: "my team is burnt out and i dont know what to do" was "Got it. Is there anything
    # you'd like a hand with?", and the burnout card it now reaches is written to the person who
    # is worn out ("take a day off this week, bring the load to your manager"), which is the
    # wrong side of the desk. So the team's own words stand the person's card down and this one
    # answers: what to take off the week, what to ask each of them, and what to escalate.
    entry("the-team-is-burnt-out",
          (("my team", "my staff", "my people", "our team", "my reports", "everyone in my",
            "all of my team", "half my team", "some of my team", "one of my team"),
           ("burnt out", "burned out", "burning out", "burnt", "burnt-out", "burnout",
            "exhausted", "worn out", "running on empty", "run ragged", "on their knees",
            "off sick", "off with stress", "signed off", "stressed", "flat", "not themselves")),
          "Look at the week before the people: what is due, who is covering it, and what can be "
          "moved or dropped, then take one real thing off the list this week and say out loud why "
          "you moved it - a team that is flat is usually carrying more than its hours, and a "
          "speech about wellbeing does not buy that back. Then ten minutes with each of them, one "
          "at a time, and ask which part of the week is heaviest rather than whether they are "
          "coping: the one task they dread is the one you can shift, and it is rarely the one you "
          "guess. Say no to the next piece of new work with a reason and a date, and go up the "
          "chain with the load rather than down it, because a team short of people is a staffing "
          "decision somebody above you is paid to make. If someone is signed off, or crying at "
          "work, or saying they cannot go on, that is a person to sit with today and a GP "
          "appointment to help them book, and if several are off at once treat it as a workload "
          "problem before anything else.",
          avoid=("my dog", "my cat", "the dog", "the cat", "my baby", "my toddler", "my kids",
                 "my son", "my daughter", "class", "pupils", "students", "my car", "the engine",
                 "i am", "i'm", "im burnt", "im exhausted", "myself")),

    entry("the-team-has-gone-quiet",
          (("scared of me", "afraid of me", "frightened of me", "intimidated by me",
            "scared to tell me", "afraid to tell me", "wont speak up", "won't speak up",
            "never speaks up", "ignores my ideas", "ignore my ideas", "no one challenges me",
            "nobody challenges me", "never disagree", "wont disagree", "won't disagree",
            "dont tell me bad news", "don't tell me bad news", "nobody tells me",
            "team has gone quiet", "my team is quiet", "says nothing in meetings",
            "no one says anything", "nobody says anything", "too quiet in meetings",
            "no one speaks", "nobody speaks",
            # the same silence said as a complaint about the manager: "my staff never challenge
            # me" and "my team tell me nothing until its too late" were both a listening line.
            "never challenge me", "never challenges me", "no one pushes back",
            "nobody pushes back", "never pushes back", "wont push back", "won't push back",
            "tell me nothing", "tells me nothing", "told me nothing", "nothing until it",
            "nothing until its", "dont tell me until", "don't tell me until",
            "no bad news", "never any bad news", "only hear good news"),
           MANAGING_ASKS),
          "A team that has gone quiet has usually learned what bad news costs, so change that "
          "first: say out loud what you will not be annoyed about - a delay told on Tuesday, a "
          "mistake that is already being fixed - and what you will, which is a surprise on Friday, "
          "then behave that way once, because one calm reaction does more than any speech. Ask for "
          "one piece of bad news a week and thank the person who brings it in front of the others. "
          "In one-to-ones ask \"what is getting in the way\" and then say nothing for ten seconds, "
          "and put your own mistake on the table before you ask about theirs: a manager who admits "
          "one is the only proof that it is safe to speak. Where it is your ideas that keep "
          "getting dropped rather than bad news that keeps not arriving, ask for one objection by "
          "name - \"what would go wrong with this?\" - and credit the change to whoever improves "
          "it, because a team that has stopped arguing with you has usually decided it is not "
          "worth the cost.",
          avoid=("my dog", "my cat", "the dog", "the cat", "my baby", "my toddler", "my kids",
                 "my son", "my daughter", "class", "pupils", "students")),

    # A manager letting someone go asks about the process, not about feelings: the notice, the
    # reason, whether it is fair, and what to say. "how do i let someone go" was "I'm not sure
    # about that one, sorry", and this is ordinary, answerable, and the person still has to do it
    # on Monday. The legal line is handed to the contract and to ACAS rather than guessed at.
    entry("let-someone-go",
          (("let someone go", "let him go", "let her go", "let them go", "letting someone go",
            "letting him go", "letting her go",
            # the person named by their status, which is how a manager writes it: "how do i let
            # an employee go fairly" was the search hedge.
            "let an employee go", "let my employee go", "let a member of staff go",
            "let one of my staff go", "let one of my team go", "letting an employee go",
            "letting a member of staff go", "let a colleague go",
            "fire someone", "fire him", "fire her",
            "firing someone", "sack someone", "sack him", "sack her", "sacking someone",
            "dismiss", "dismissing", "dismissal", "terminate their contract",
            "terminating employment", "get rid of an employee", "get rid of a member of staff",
            "made someone redundant", "make someone redundant"),
           MANAGING_ASKS),
          "Decide the reason first, in one sentence you could say to the person and to HR: the "
          "job is not being done after warnings, the role has gone, or the rules were broken. "
          "Check your own policy and the contract before you speak to them, because the order "
          "matters - an informal chat, then a meeting with notice, then a letter - and check "
          "whether they have the two years' service that makes an unfair dismissal claim possible "
          "(it is one year in Northern Ireland; ACAS will tell you free and they are quicker than "
          "a lawyer). Book a room with a witness, keep it to the facts and under fifteen minutes, "
          "have the notice, the last pay and their holiday in writing on the day, and take their "
          "keys and access in the same hour rather than at the end of the week. Do not do it by "
          "text, and do not argue: if they are angry, say the decision will be confirmed in "
          "writing and end the meeting.",
          avoid=("my dog", "my cat", "the dog", "the cat", "my hair", "my weight", "the ball",
                 "my breath", "a fart", "my temper", "steam", "the clutch", "the rope",
                 "i was fired", "i got fired", "i got sacked", "i was sacked", "i was made",
                 "redundancy pay", "am i being made redundant", "being made redundant",
                 "am i entitled",
                 # "dismiss" is a landlord's word as well as an employer's, and "how do i
                 # dismiss a tenant" is a housing question: it took this card and its "reason
                 # you could say to the person and to HR", where main gave the tenant card.
                 "tenant", "tenants", "tenancy", "evict", "eviction", "evicted",
                 "landlord", "landlords", "letting agent", "flatmate", "flatmates",
                 "housemate", "i rent", "renting", "my lease", "the lease")),

    entry("cover-for-colleague",
          (("cover for", "covering for", "covers for", "cover my shift", "swap shifts",
            "swap my shift", "take my shift"),
           ("colleague", "coworker", "co-worker", "workmate", "team mate", "teammate",
            "keeps asking", "always asking", "every week", "say no", "how do i", "again")),
          "Agree to a limit instead of refusing the person: \"I can cover tonight, but I can't do "
          "Fridays.\" Then keep it - a rule you stick to is kinder than a yes you resent. If it is "
          "most weeks, tell your manager what is happening without framing it as a complaint: "
          "\"I've covered six of Priya's shifts this month; can we look at the rota?\" Covering "
          "occasionally buys goodwill; covering always just moves the problem onto you.",
          # "how do i swap shifts" is the trade, not the limit: `shift-swap` answers it, and the
          # colleague word in "my colleague keeps asking me to swap shifts" keeps that one here
          avoid=("pan", "pot", "saucepan", "sauce", "casserole", "gravy", "christmas",
                 "how do i swap", "how to swap", "how do i switch", "swap shifts with")),

    entry("crying-at-work",
          (("cry", "crying", "cried", "tears", "broke down", "welling up",
            # the same tears said the other ways people say them: "i welled up", "i sobbed in
            # the car", "my eyes filled up in the standup" all reached a nod, the plan follow-up
            # or, worse, the fibre card
            "welled up", "wells up", "sobbing", "sobbed", "in tears", "burst into tears",
            "choked up", "had a cry", "a good cry", "eyes filled", "eyes welled", "my eyes"),
           ("at work", "in work", "at the office", "in the office", "in a meeting", "at my desk",
            "front of", "boss", "colleague", "ok", "normal", "embarrassed", "embarrassing",
            # the places it happens, which the row listed as one phrase each: "in the meeting",
            # "the standup" and "the car park before i went in" are the same room as the ones here
            "meeting", "standup", "stand-up", "team call", "the team", "my team", "toilets",
            "car park", "in the car", "before going in", "before i went in", "on the way in",
            "in front of")),
          "Yes, and it is less of a career event than it feels. Step out for two minutes if you can, "
          "breathe out longer than you breathe in, and come back with \"sorry, that caught me - "
          "where were we?\" Nobody remembers the tears as clearly as you do; what sticks is that "
          "you came back and finished the meeting. If it keeps happening, tell one person you "
          "trust, and get the thing that is causing it looked at - a workload, a manager, or a "
          "doctor.",
          # a pet that cries when you are at work is a pet question, not a career one
          avoid=("baby", "babies", "toddler", "my son", "my daughter", "my kid", "my kids",
                 "funeral", "film", "movie", "onion", "dog", "dogs", "puppy", "puppies",
                 "cat", "cats", "kitten", "pet", "pets"),
          # "my boss cried in the meeting" names a meeting and a boss, and this row read it as the
          # speaker's own tears. The line says whose they are (see `_whose_tears`).
          guard=_my_own_tears),

    entry("defensive-talk",
          (("defensive",),
           ("talk", "say", "explain", "without sounding", "sound", "sounds")),
          _defensive_review,
          # "how do i talk about a mistake without sounding defensive" is own-a-mistake's line:
          # the words to say about the mistake, not about the tone of a hard conversation.
          avoid=("husband", "wife", "partner", "boyfriend", "girlfriend", "dad", "mum", "mom",
                 "son", "daughter", "friend", "flatmate", "roommate",
                 "mistake", "messed up", "screwed up", "got it wrong", "error", "typo",
                 "wrong figures", "wrong number")),

    entry("hiring-bias",
          (("bias", "unconscious bias", "biased", "fair hiring", "interview fairly"),
           ("hiring", "hire", "recruit", "recruiting", "recruitment", "interview", "candidates",
            "shortlist", "panel", "job advert")),
          "Use the same questions, in the same order, with a written scorecard for every "
          "candidate, and score each one straight after the interview and before you discuss them "
          "with anyone. Take names and schools off the first read of a CV, and have more than one "
          "person on the panel. Where someone does not fit the pattern you expected, ask yourself "
          "what evidence you would need to see to be sure - that question is usually enough."),

    entry("micromanage",
          (("micromanage", "micromanager", "micromanaging", "micromanages", "micromanagment",
            "breathes down my neck", "checks everything", "watches everything i do",
            "wants to approve everything", "over my shoulder",
            # "my manager checks up on me constantly" was the dental check-up answer, and with
            # the dentist stood down it was a listening line: being watched is this row's whole
            # subject, and "checks up on me" is how people say it.
            "checks up on me", "checks up", "keeps checking", "constantly checking",
            "checks on me", "checking up on me", "wants to know where i am",
            "asks where i am", "has to see everything", "wants to see everything",
            "never lets me get on with it", "reviews everything", "ccs my boss"),
           ("how", "deal", "handle", "boss", "manager", "what can i do", "driving me",
            "stop", "tell", "talk")),
          "Ask for a weekly fifteen-minute check-in and a written definition of done for each "
          "piece of work, then say why: \"If we agree what finished looks like on Monday, I can "
          "run with it and bring you the result on Thursday.\" Bring one recent example of the "
          "checking and the cost of it (\"we rebuilt the same slide twice\"), not a verdict on "
          "them. If it carries on, ask what would have to be true for them to trust the work "
          "without checking.",
          avoid=("kid", "child", "son", "daughter", "teenager", "homework", "partner")),

    entry("office-days",
          # Days *in the office* are their own question: what the employer can ask for, and what
          # to offer instead. "Three days a week" alone is also a part time request, so the office
          # has to be named.
          (("in the office", "back to the office", "from the office", "office days",
            "days in the office", "office three days", "office twice", "return to office",
            "office mandate"),
           ("boss", "manager", "employer", "company", "wants", "want me", "says", "make me",
            "require", "required", "can they", "have to", "hybrid", "how do i", "what can i do")),
          "If your contract or a policy that came with the job names office days, they can usually "
          "ask for them; what they cannot do is change it out of nowhere, so ask what the policy is "
          "and whether it is being changed for everyone. Then offer the pattern you can keep in "
          "writing: \"I can do Tuesday and Thursday every week; the other three I get more done at "
          "home, and I am on Teams all day.\" Ask for a three-month trial with a review date, since "
          "a trial is easier to say yes to than a permanent change. A union rep or an advice line "
          "will know what your country allows.",
          avoid=("commute", "commuting", "train", "driving", "traffic", "parking", "lunch",
                 "kitchen", "desk", "chair", "air con", "noise", "noisy", "cold", "hot",
                 "focus", "distracted", "loud", "colleagues talk",
                 # a quiet hour is a seat-and-noise question; the words "in the office" were
                 # enough to take "how do i get a quiet hour in the office" to the office-days
                 # answer, which is about what an employer can require
                 "quiet", "quiet hour", "quiet time", "silence", "headphones")),

    # A commute was a shrug on every line: "how long a commute is too long", "is a 90 minute
    # commute too long" and "the commute is killing me" all reached the fallback, while the job
    # offer with the long commute reached the money-after-extras answer. It is an everyday
    # decision - take the job or not, move closer or not - so it gets the numbers and the ask.
    entry("commute-long",
          (("commute", "commutes", "commuting", "commuter", "journey to work", "journey into work",
            "travel to work", "travel into work", "getting to work", "get to work",
            "drive to work", "driving to work", "train to work", "train into work",
            "morning train", "each way", "move closer to work", "moving closer to work",
            "live closer to work"),
           ("how long", "too long", "long", "far", "how far", "worth it", "worth", "killing me",
            "hate it", "hate", "hour", "hours", "minutes", "minute", "90 minute", "each way",
            "move closer", "moving closer", "closer", "hybrid", "work from home", "from home",
            "office", "acceptable", "normal", "reasonable", "the point", "is it worth",
            # the broad ask: "what should i do about my commute" is the same decision, and it
            # hedged while every hour-based wording of it was answered
            "what should i do", "what can i do", "any advice", "dont know what to do",
            "help me decide")),
          "That is a real cost: an hour each way is about where most people stop being fine with "
          "it, and past that it is twenty hours a week, which no pay rise really covers. Put the real numbers down - "
          "the season ticket or the fuel, those hours at your hourly rate, and what moving closer "
          "would add to the rent - then ask for two days at home before you turn the job down, "
          "because that is the part employers say yes to. If you are keeping the journey, make the "
          "time yours with a book or a podcast and shift your start half an hour earlier rather "
          "than sitting in the worst of it.",
          # The journey itself is travel's question: a timetable, a delay, a refund and a route
          # are not this decision, and neither is a car that will not start.
          avoid=("timetable", "times", "delay", "delayed", "cancelled", "canceled", "refund",
                 "platform", "fare", "fares", "route", "parking", "park and ride", "car park",
                 "bike to work", "cycle to work", "cycling to work", "walk to work", "walking",
                 "how do i get", "what time", "which train", "car wont start", "breakdown",
                 "insurance", "season ticket price", "how much is"),
          guard=_a_journey_that_costs_time),

    # The same journey, costed: "how do i make my commute cheaper" is not how long is too long,
    # and it hedged on main. The words that make it this row are the cost words, and the hours
    # answer stays commute-long's.
    entry("commute-cheaper",
          (("commute", "commutes", "commuting", "commuter", "journey to work", "journey into work",
            "travel to work", "getting to work", "get to work", "drive to work", "driving to work",
            "train to work", "train into work", "parking at work", "work parking",
            "season ticket", "travelcard", "travel card",
            # "my train fare to work went up again" reached the training answer: the fare is
            # this row's subject and "train fare" was not one of its words
            "train fare", "train fares", "fare to work", "fares to work", "bus fare",
            "my fare", "my fares"),
           ("cheap", "cheaper", "cheapest", "save", "saving", "savings", "cost", "costs",
            "afford", "pay less", "money", "budget", "worth it", "worth",
            # a bill that has gone up is the same ask: how to spend less on it
            "expensive", "so expensive", "pricey", "price", "prices", "gone up", "went up",
            "going up", "so much", "more money", "what are my options", "options",
            "how do i", "how can i", "what can i do", "any way")),
          "Ask work first, then price the journey three ways before you buy anything: a season "
          "ticket only beats weekly or daily tickets above about three days a week, a flexi ticket "
          "or a carnet covers two or three days, and a railcard pays for itself in about a dozen "
          "trips if you qualify for one. If you drive, park and ride, a lift-share board or a "
          "parking space a ten-minute walk out usually undercuts the station car park, and asking "
          "whether your employer does a season ticket loan or a cycle-to-work scheme is free money "
          "in effect. Booking the next day's travel the night before is where the cheap fares go.",
          # A journey's timetable, a delay, a refund and a route are travel's question, and a
          # ticket's price on its own is shopping's.
          avoid=("timetable", "what time", "which train", "delay", "delayed", "cancelled",
                 "canceled", "refund", "platform", "car wont start", "breakdown",
                 "insurance", "how much is a ticket", "price of a", "buy a ticket",
                 "cheap day return to", "cheapest way to get to london",
                 # claiming the journey back is the expenses row's answer: receipts, policy,
                 # deadlines. This one is how to spend less, not how to be paid back.
                 "expenses", "claim", "claimed", "claiming", "reimburse", "reimbursed",
                 "receipts", "tax relief")),

    entry("own-a-mistake",
          (("mistake", "messed up", "got it wrong", "screwed up", "error", "wrong figures",
            "wrong number", "typo",
            # The slip people are most often cringing about is a thing sent to the wrong place,
            # and it was reaching the receipt: "i sent the wrong file to the whole team" -> "Got
            # it. Is there anything you'd like a hand with?", "i replied all by mistake" -> the
            # same. The act is named and the fix is this card's own, so the words are here and
            # the room it went to is in the second part below. "by accident" and "accidentally"
            # are not among them on purpose: they are loose forms of "accident", and with them
            # in, "i had an accident at work, what do i do" lost its tie to the car-breakdown
            # entry and was told to swap insurance details at the roadside.
            "wrong file", "wrong attachment", "wrong version", "wrong document",
            "wrong spreadsheet", "wrong draft", "wrong email", "wrong person", "wrong client",
            "wrong address", "wrong chat", "wrong group", "wrong thread", "wrong name",
            "wrong title", "reply all", "replied all", "reply-all", "ccd", "cc'd",
            "sent the wrong", "sent it to the wrong", "forwarded the wrong", "hit send",
            "by mistake",
            # Admitting it is the other half of owning it, and it is the phrasing people use:
            # "how do i admit i was wrong in a meeting" had this card's subject and no word to
            # score it, so it hedged while `speak-up-meetings` was stood down for it.
            "admit", "admitted", "admit i was wrong", "i was wrong", "hold my hands up",
            "fess up", "own up", "own it", "come clean"),
           ("tell my boss", "tell my manager", "boss", "manager", "report", "client", "admit",
            "fix", "how do i", "should i say",
            # Who it went to, so the slip above has something to score against. Only the words
            # that name the room: "at work", "office" and "meeting" are this domain's commonest
            # words, and putting them in a key this size moves every other card's rarity.
            "team", "whole team", "everyone", "colleague", "colleagues", "coworker",
            "co-worker", "company", "whole company", "the chat", "group chat",
            "reply all", "replied all", "reply-all", "the list", "the group")),
          "Tell the person affected before they find out, with the fix attached: \"I got the "
          "figures wrong in the report; I have corrected them and sent the revised version to "
          "everyone who had the first one. I have added a check so it does not happen again.\" "
          "Say it once, plainly, no long apology, and then answer questions. Nobody remembers the "
          "mistake; they remember whether you brought it to them or they found it.",
          avoid=("made a cake", "recipe", "recipe went", "cake",
                 # a file deleted is recovered, not confessed: "i deleted the wrong file at work"
                 # has the recycle-bin card and this one would take its subject away
                 "deleted", "delete", "recycle", "bin", "recover", "restore", "backup",
                 # blamed for something you did not do: confessing is the wrong advice
                 "didnt make", "didn't make", "not my fault", "blamed me", "blames me",
                 # a mistake in a document is not a mistake at work
                 "cv", "resume", "application", "cover letter", "essay", "homework", "thesis",
                 # "i messed up my job interview can i fix it" was told to own the mistake to
                 # the person affected, with the fix attached. A panel is not a mistake at work:
                 # bad-interview below has the letter to send.
                 "interview", "interviews", "interviewer", "panel", "job interview",
                 # `admit` and "i was wrong" take the work card to the wrong room otherwise:
                 # "how do i admit i was wrong to my husband / my friend / my mum" is being
                 # wrong with a person at home, and the letter with the fix attached in it is
                 # not that conversation.
                 "husband", "wife", "partner", "boyfriend", "girlfriend", "friend", "friends",
                 "mum", "dad", "mother", "father", "brother", "sister", "son", "daughter",
                 "kids", "children", "child", "neighbour", "neighbor", "flatmate")),

    entry("national-insurance-number",
          (("national insurance number", "ni number", "nino", "national insurance"),
           ("get", "getting", "apply", "applying", "need", "needed", "lost", "find", "what is",
            "where", "how do i", "do i need", "number", "mine")),
          ("You need one to work in the UK, and it is free: apply on gov.uk (search \"apply for a "
           "national insurance number\") and send the ID and address proof they ask for, or ring the "
           "helpline on 0300 200 3500 if you cannot apply online. It arrives by post in two to four "
           "weeks. If you have lost the letter, the number is on a payslip, a P60 or the HMRC app."),
          # the amount of national insurance is a tax question, not a "how do i get a number" one
          avoid=("how much", "rate", "rates", "contribution", "contributions", "threshold",
                 "class 2", "class 4", "pay", "paying", "deducted", "goes up", "reduced",
                 # "do i need voluntary national insurance" is a gap in your record, which is
                 # the top-up question, not how to get a number
                 "voluntary")),

    entry("payslip-short",
          (("payslip", "pay slip", "paycheque", "paycheck", "my wages", "my pay",
            "net pay", "take home pay", "take-home pay", "my earnings",
            # the person is the one who was paid, not the one who reads the slip, and "i got paid
            # less than last month" named the money without any of the words above
            "i got paid", "i was paid", "im paid", "i am paid", "i earn"),
           ("less than", "short", "missing", "wrong", "underpaid", "deduction", "deductions",
            "tax", "not paid", "shortfall", "overtime",
            # a payslip that shrank is the same question as one that came out short, and these
            # are the words people use for it; reading a payslip is `money.payslip`'s question
            "smaller", "went down", "gone down", "dropped", "shrank", "shrunk", "error",
            "mistake", "add up", "doesnt add up", "doesn't add up", "not what i expected",
            "not right", "short paid", "underpaid",
            # "less on it than last month" puts a word between the two, so `less than` never
            # matched it and the line was a shrug; the same for the plain comparisons people use
            "less on it", "less this month", "less this week", "less than last month",
            "less than last time", "less than last year", "less than usual", "less than i did",
            "less than before", "less money", "a bit less", "bit less", "paid less",
            "lower than last", "lower than usual", "lower this month", "lower this year",
            "lower than before", "down on last month", "down on last year",
            "not the full amount", "didnt go in full", "did not go in full",
            "is less", "is lower", "was less", "was lower", "seems less", "looks less",
            "havent had the full", "half of what")),
          "Open the payslip and check three lines before you say anything: the tax code against your "
          "P45 or last payslip, the hours or overtime that were paid, and any deduction you did not "
          "agree to. Then ask payroll in writing for a breakdown - \"my gross is down 120 on last "
          "month, could you tell me what changed?\" Keep it about the figures, not the person. Most "
          "of these are a wrong tax code or a missed timesheet and are fixed within a week.",
          avoid=("pay rise", "raise", "salary increase", "payslips for", "student loan",
                 "national insurance number", "p60",
                 # how tax is worked out is a different question from a payslip that is short
                 "how much tax", "tax on", "tax rate", "income tax", "national insurance",
                 # ...and so is a cut in the hours: "my hours were cut and my pay is less" is the
                 # contract question, and main answered it that way before this row existed
                 # (orange-toad, #8764). The money is the symptom; the hours are the dispute.
                 "hours were cut", "hours are cut", "hours got cut", "hours have been cut",
                 "hours been cut", "cut my hours", "cut our hours", "cut his hours",
                 "cut her hours", "cut the hours", "hours cut", "reduce my hours",
                 "reduced my hours", "reducing my hours", "hours reduced", "shorter hours",
                 "less hours", "fewer hours", "hours went down", "hours dropped",
                 "hours have dropped", "hours are down", "hours went up")),

    entry("promotion-blocked",
          (("never get promoted", "never be promoted", "not going to be promoted",
            "no chance of promotion", "no chance of a promotion", "dead end job",
            "dead-end job", "no progression", "stuck in my role", "stuck where i am"),
           ("should i leave", "leave", "stay", "is it worth", "any point", "what do i do",
            "manager said", "boss said", "told me")),
          "Treat it as information, not a sentence: ask what evidence would change their mind and "
          "get the answer in writing - \"what would I need to show by the next review?\" If the "
          "answer is specific, you now have a target and a date. If there isn't one, put a date on "
          "your own decision - six months of the job you want on your CV, then apply elsewhere. "
          "One manager's opinion rarely holds across a whole company, but it will hold for as long "
          "as you stay quiet about it.",
          avoid=("promoted twice", "nobody", "hospital", "illness")),

    entry("review-bad-year",
          (("review", "appraisal", "performance review", "one to one", "yearly review"),
           ("bad year", "went badly", "went bad", "bad review", "poor review", "bad year",
            "going to be bad", "is going to be", "went wrong", "slipped", "failed", "worst",
            "how do i prepare", "defensive")),
          "Go in having written the year yourself: what you delivered, what slipped and why, and "
          "what you changed afterwards. Say the bad part first and in one sentence - \"the "
          "migration slipped six weeks; I flagged it in May and we re-planned\" - then spend the "
          "time on the fix and on next year. Ask what would make next year a good one in their "
          "words, and write down what they say. A bad year handled openly reads as senior; a bad "
          "year explained for twenty minutes reads as a problem.",
          avoid=("film", "movie", "book", "restaurant", "hotel", "gadget", "phone", "laptop",
                 "headphones",
                 # a review of a shop or a thing you bought is not the appraisal: every line
                 # below was answered with "go in having written the year yourself"
                 "online", "google", "tripadvisor", "trustpilot", "amazon", "yelp", "my business",
                 "customer", "customers", "product", "shop", "1 star", "one star",
                 "leave a review", "write a review", "reviewer", "reviewers")),

    entry("takes-credit-and-blame",
          (("blame", "blamed", "thrown under", "threw me under", "under the bus",
            "fault is mine", "takes the blame"),
           ("credit", "takes the credit", "took the credit", "team lead", "team leader",
            "supervisor", "manager", "boss", "when it goes wrong", "when it goes badly",
            # "i keep getting blamed for things at work" names no boss and no credit. The words
            # here are the ones that are only about being blamed: "team" and "always" are not,
            # and they took "how do i raise it without blaming people" from raise-with-boss.
            "at work", "for things", "for something", "the delay", "the project",
            "the mistake", "was blamed", "got blamed", "got the blame", "blame for")),
          "Keep a written trail and use it early rather than at the row: a short summary email after "
          "each meeting - \"as agreed, I'll do X, you'll take Y to the director\" - does the work "
          "quietly. When it happens again, name the pattern once in private: \"Last week's update "
          "went out without my name on it, and the delay came back to me. Can we fix how we hand "
          "things over?\" Then copy the person above on the next summary. Evidence, not "
          "accusation, is what changes it.",
          avoid=("my idea", "my ideas", "stole", "stolen", "presented my")),

    entry("tell-boss-leaving",
          (("leaving", "resigning", "quitting", "handing in my notice", "i quit"),
           ("tell my boss", "tell my manager", "how do i tell", "how to tell", "break it to",
            "announce")),
          "Ask for fifteen minutes in private and put the decision in the first line, then one "
          "reason: \"I have decided to move on; my last day would be the 14th.\" Do not "
          "apologise more than once, and do not be drawn into a debate about the money on the "
          "day - \"I have thought about it a lot\" is a complete answer. Then agree what to tell "
          "the team and when, and send the same thing in writing so the date is on record.",
          # "leave early on friday" is one day off, not a resignation: the loose form of
          # "leaving" caught it and told the person how to quit.
          avoid=("early", "half day", "half a day", "a few hours", "an hour", "appointment",
                 "doctor", "dentist", "hospital", "nursery", "school run", "pick up",
                 "pickup", "collect", "sick", "unwell", "ill", "late", "tomorrow",
                 "holiday", "annual leave", "days off",
                 # telling a partner, a parent or a friend is left to the composer: it is their
                 # decision to hear about, not a how-to for the boss (see someone-close-quitting).
                 "partner", "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee",
                 "my mum", "my mom", "my dad", "my parents", "my friend", "my kids",
                 "my children", "mate",
                 # and a landlord is told in the same words and wants a different letter:
                 # "how do i tell my landlord im leaving" is a notice, not a resignation
                 "landlord", "landlords", "landlady", "letting agent", "letting agents",
                 "tenancy", "tenancies", "lease", "my flat", "my house", "my room")),

    entry("the-notice-that-has-gone-in-is-news",
          # The other side of `quit-a-job-message`: once the notice has gone in there is no letter
          # left to write, and the person is telling you their news. Without this the line that the
          # letter card steps back from ("i quit my job", "i handed in my notice today", "i resigned
          # today") got "Thanks for telling me" or "I'm listening - say more if it helps."
          (("quit", "quitting", "resigned", "resigning", "handed in my notice",
            "handed my notice in", "gave my notice", "gave in my notice", "walked out of my job",
            "left my job", "handed in notice", "im done at work", "i'm done at work"),
           ("job", "work", "today", "yesterday", "tonight", "this morning", "last week",
            "last month", "finally", "great", "good", "relieved", "free", "scared", "terrified",
            "nervous", "done it", "did it", "started", "leaving",
            # a phrase that names the notice needs no second word: "i handed my notice in" is the
            # whole of the news, and the same is true of "i resigned" and "i quit" on their own.
            "my notice", "notice in", "resigned", "resigning", "quit", "quitting")),
          "That is a real decision, and most people feel two ways at once about it - lighter, and "
          "a bit exposed. Two things are much easier now than in a month: check the final payslip "
          "for the holiday you have not taken, and ask for a written reference while they still "
          "think well of you. What is the plan for the next few weeks - straight into something "
          "else, or a bit of a gap first?",
          # the letter, the telling and the decision are all their own cards and their own words
          avoid=("how do i", "how to", "how can i", "should i", "should i quit", "should i resign",
                 # still deciding is the decision card's question, not news that it is done
                 "thinking of", "thinking about", "considering", "wondering", "might quit",
                 "might resign", "not sure whether", "unsure", "if i quit", "if i resign",
                 "worth quitting", "worth resigning", "if i should", "letter", "letters", "email",
                 "template", "what do i say", "what should i say", "notice period", "holiday",
                 "holidays", "holiday pay", "annual leave", "entitlement", "final pay",
                 "payslip", "reference", "interview", "cv", "regret", "regretting",
                 "wish i hadnt", "wish i hadn't", "mistake", "stupid", "no money", "cant pay",
                 "can't pay", "broke", "rent", "benefits", "universal credit",
                 # somebody else's job, and the verbs that are not a job at all
                 "my husband", "my wife", "my partner", "my boyfriend", "my girlfriend",
                 "my mum", "my mom", "my dad", "my son", "my daughter", "my friend",
                 "my colleague", "my mate", "my boss", "my manager", "his job", "her job",
                 "their job", "smoking", "cigarettes", "vaping", "drinking", "alcohol", "sugar",
                 "weed", "gambling", "diet", "course", "uni", "degree", "gym", "nail biting"),
          bias=1),

    entry("written-warning",
          (("written warning", "written warnings", "final warning", "disciplinary", "warning",
            "on my record"),
           ("late", "lateness", "being late", "unfair", "fair", "appeal", "disagree", "meeting",
            "hr", "what do i do", "how do i", "got", "received")),
          "Appeal in writing inside the deadline they gave you - often five to seven working days. "
          "Keep it to three things: the dates and reason for the lateness (a bus that stopped "
          "running, a nursery drop-off), the reason a warning is out of proportion (no prior "
          "conversation, everyone else late), and what you will do (a later start agreed in "
          "writing, or an alarm and a check-in). Ask a union rep or HR for the policy before you "
          "send it. A warning is often quietly dropped when the appeal is calm and factual.",
          avoid=("fire alarm", "smoke alarm", "warning sign", "health warning", "parking",
                 "warning light", "weather warning", "traffic",
                 # a warning from a council, a landlord or the police is not a work one
                 "council", "landlord", "housing", "school", "police", "a fine", "penalty",
                 "court", "legal", "magistrate", "tenancy")),


    # --- finding the job ------------------------------------------------
    entry("cv-first-job",
          (("cv", "resume", "curriculum vitae"),
           ("no experience", "first job", "school leaver", "never had a job", "nothing to put",
            "entry level", "no qualifications", "first cv")),
          "Lead with what you have done, not with job titles: school or college, volunteering, a "
          "paper round, a team you played in, a club you ran. Then a two-line profile at the top "
          "saying what you want and what you are good at with people, numbers or tools. One page "
          "is plenty - employers reading a first CV look for effort, not titles."),

    entry("cv-basics",
          (("cv", "resume", "curriculum vitae"),
           ("write", "writing", "help", "start", "make", "improve", "check", "put", "layout",
            "format", "template", "good", "better", "revise", "update", "tailor",
            "trim", "cut down", "sum up",
            # an existing cv being aimed at a particular job is the same first page of advice
            "revising", "tailoring", "updating", "adapt", "tweak",
            "wrong job", "not getting", "warehouse", "job")),
          "One page, newest first: a two-line profile saying what job you want and what you are "
          "good at, then each job or course with one line on what you actually did and a number "
          "where there is one. Plain headings, a normal font, no photo or date of birth, and send "
          "it as a PDF so the layout cannot move."),

    entry("cv-length",
          (("cv", "resume"),
           ("how long", "one page", "two page", "two pages", "length", "too long", "one side",
            "how many pages")),
          "One page if you have under about ten years of experience, two at most after that: "
          "nobody reads page three. Cut anything older than ten years to a single line, and keep "
          "the detail where it earns you the interview."),

    entry("cv-gaps",
          (("cv", "resume", "career break", "employment gap",
            # The gap is the thing people ask about without saying "CV": "how do i explain a gap
            # in my work history", "how do i explain a gap after maternity leave", "i took 3 years
            # off to care for my mum how do i explain it". Each of these was answered by another
            # card entirely - the essay-subjects one, the walking one, the sick-day message - so
            # the phrases here name the gap itself, and the explain words in the second half turn
            # them into the question about the interview.
            # "gap in my" and "gap on my" were bare phrases here, and a phrase with no noun in
            # it takes the house: "how do i seal a gap in my window" was answered with what to
            # put on a CV (@lemon-elk, #14490). The bare phrase and the word "gap" in the second
            # half matched, so every hole in a home became a gap in a career. The phrases that
            # stay are the ones with the thing in them.
            "work history", "job history", "gap in my employment", "gap in my career",
            "gap in my cv", "gap in my work history", "gap in my job history",
            "gap in my resume", "gap on my cv", "gap on my resume", "gap on my work history",
            "gap after maternity", "gap after having a baby", "gap after my degree",
            "gap of", "employment history", "years off work", "time out of work",
            "time off work for",
            "was off work", "was off sick for", "off sick for a year", "not worked for",
            "havent worked", "have not worked", "back to work after",
            # "i took 3 years off to care for my mum how do i explain it" reached the walking
            # card, because "caring" was in the second half and nothing in the line named the
            # gap itself. "years off" and the care phrases are the gap being described.
            # "looking after my" was here, with "looking after" in the second half, and the pair
            # matched "how do i look after my mum who has dementia" - a care question answered
            # with what to put on a CV. The gap is named with the words of work ("years off",
            # "work history") or of the explaining; the caring words alone are the care card's.
            "time off to care", "off to care", "care for my", "caring for my mum",
            "caring for a"),
           ("gap", "gaps", "break", "unemployed", "years off", "time out", "caring", "illness",
            "explain", "explaining", "explanation", "account for", "explain it", "talk about",
            # "how do i" and a bare "care" were here and are not any more: they are the words of
            # every ask, so "how do i look after my mum who has dementia" matched the gap words
            # in the first half and was answered with what to put on a CV. The second half is the
            # words of the explaining, not the words of the asking.
            "bring up", "interview", "recruiter", "employer", "explain it")),
          "Put the gap on the CV with a plain label - \"Career break: caring for a parent, "
          "2019-2021\" - because an unexplained gap reads as bigger than it is. Add anything you "
          "did in it: a course, volunteering, freelance work, a language. Written down, it stops "
          "being the thing the interview is secretly about.",
          # a hole in the house is not a gap in a career: the words below keep the row off
          # "how do i seal a gap in my window" even if a future key phrase is too loose
          avoid=("window", "windows", "door", "doors", "fence", "floor", "floorboard",
                 "roof", "wall", "hedge", "gate", "teeth", "tooth", "draught", "seal")),

    # Caring for somebody is the commonest unpaid job there is, and the person writing it as
    # "just caring" asked how to make it count: nothing in the table had it, so the line got
    # the search shrug. It is experience, and the words are the ones a job advert uses.
    # "what is a cv personal statement" was a shrug, and the UCAS personal statement has its own
    # card in study.py. The CV one is the profile at the top: a paragraph, not an essay.
    entry("cv-profile",
          (("personal profile", "cv profile", "profile at the top",
            "summary at the top", "about me section", "profile section", "career summary",
            "cv summary", "personal summary", "opening paragraph of my cv"),
           ("cv", "resume", "curriculum vitae", "what is", "whats", "how long", "write",
            "writing", "say", "good", "example", "start", "include", "should")),
          _CV_PROFILE_REPLY,
          # the UCAS personal statement is a different piece of writing with its own card
          avoid=("university", "uni", "ucas", "college application", "course application",
                 "sixth form", "a-levels", "a levels", "student finance")),

    # "personal statement" on its own is the UCAS essay in Britain - a piece of writing with its
    # own card in study.py - so it only reaches the CV profile when the line has already said cv
    # or resume. Without that, "how do i write a personal statement" lost the UCAS answer to this
    # card, and "how long should a personal statement be" was told two to four lines (@ivory-kettle,
    # @loyal-zebra).
    entry("cv-personal-statement",
          (("personal statement",),
           ("cv", "c v", "resume", "r\u00e9sum\u00e9", "curriculum vitae", "profile")),
          _CV_PROFILE_REPLY),

    entry("going-back-to-work",
          (_GOING_BACK, _GOING_BACK_LINE),
          _going_back,
          # the milk question has its own answer in family.py, and a healing time or an injury is
          # the injury's own card: "when can i go back to work" is not about the return.
          avoid=("express", "expressing", "pump", "pumping", "breastfeed", "breastfeeding",
                 "breast feeding", "milk", "formula", "how long", "how soon", "when can i",
                 "before i can", "until i can", "how many weeks", "my knee", "my back",
                 "my ankle", "my hand", "my shoulder", "my wrist", "my hip", "my arm",
                 "my neck", "sprain", "fracture", "broken", "cast", "crutches", "physio",
                 "recovery", "heal", "healing", "nursery fees", "childcare costs"),
          bias=2),

    entry("caring-as-experience",
          (("caring", "care", "carer", "looked after", "looking after", "care for",
            "cared for"),
           ("cv", "resume", "application", "applying", "job", "interview", "experience",
            "count", "counts", "sound like", "value", "skills", "mention", "put")),
          "Caring is experience and it is written in the words the advert uses: planning and "
          "managing a household, appointments and medicines, dealing with doctors, social "
          "services and forms, keeping records, staying calm in a crisis, negotiating. Put it "
          "on the CV like a job - \"Carer, family member, 2019-2023\" - with three lines of "
          "what you actually did, then one example ready for the interview: a problem, what you "
          "sorted out, what changed. Say plainly why you are going back to work now, and leave "
          "out any apology for the time it took.",
          # who they cared for is not what stands the entry down: the line that needs the CV
          # sentence most is the one that names them ("i was just caring for my mum, how do i
          # make it count on my cv" was the houseplant answer). What the line has to be about
          # is the application - the ask below - so a question about the caring itself stays
          # with the care answers.
          ask=("cv", "c v", "resume", "r\u00e9sum\u00e9", "application", "applying", "apply",
               "interview", "count", "counts", "count for", "experience", "skills", "mention",
               "put on", "put it", "sound like"),
          # `care` is a form of `caring`, so "i dont care about my job anymore" cleared the gate
          # with the CV words in the second group; saying you do not care is not caring.
          avoid=("nursing home", "care home", "childcare", "childminder", "nursery",
                 "dementia", "cancer", "dying", "hospice", "respite", "carer's allowance",
                 "carers allowance", "dont care", "don't care", "didnt care", "didn't care",
                 "not care", "couldnt care", "couldn't care", "doesnt care", "doesn't care"),
          bias=2),

    entry("cover-letter",
          # a "letter of application" is the same letter under its formal name: it was reaching
          # the thank-you note that follows an interview
          (("cover letter", "covering letter", "covering email", "letter of application"),
           ("write", "how", "start", "good", "template", "tips", "short",
            # "what should i put in a cover letter" and "what do i say in one" are the same ask,
            # and neither has "write" or "tips" in it
            "put", "put in", "include", "say", "mention", "should i", "what", "need",
            # "how long should a cover letter be" is the length of the letter, and the post
            # timetable used to answer it because a letter is a thing you post
            "long", "length", "how long", "words", "page", "pages", "lines")),
          "Three short paragraphs: the job you are applying for and one real reason you want it, "
          "one example of doing that kind of work well, and what you would do in the first six "
          "months. Under 250 words, and never a copy of the CV. Address it to a person if you can "
          "find a name."),

    entry("garden-leave",
          # the notice-period row carries "garden leave" in its key, so the words arrived there
          # and got the length of a notice period; the question is what being on it means
          (("garden leave", "gardening leave", "on garden leave", "put on garden leave"),
           ("what", "whats", "what is", "mean", "means", "how does it work", "explain",
            "still", "paid", "pay", "can i", "job", "allowed", "do", "during", "start",
            "another job", "interview", "put", "put me", "can they", "they", "make me",
            "legal", "allowed to", "entitled", "have to", "must i",
            # "does garden leave count as my notice" is neither a what-is-it nor a can-they line,
            # and moving the phrase out of the notice row left it with nothing to answer
            "does", "count", "counts", "counts as", "notice", "extend", "extended",
            "still work", "work out")),
          "Garden leave is being paid to stay away from work during your notice period: you are "
          "still employed, still on the payroll and still bound by your contract, but told not "
          "to come in or to contact clients. You keep your holiday, your notice carries on "
          "running, and you are usually not allowed to start another job until it ends, so read "
          "the contract or ask HR before you take a new role. It is the usual answer for someone "
          "who could take customers or information with them.",
          bias=1),

    entry("applications-no-replies",
          # the same wall in the words people use: a fine CV that never gets a reply
          (("applications", "applying", "applied", "job applications", "cv", "resume",
            "interviews", "interview", "recruiters", "recruiter"),
           ("no replies", "no response", "not heard", "heard nothing", "ignored", "no luck",
            "rejected", "hundreds", "nothing back", "never hear back", "never heard back",
            "not hearing back", "never get an interview", "never get interviews",
            "no interviews", "no interview", "not getting interviews",
            "not getting any interviews", "keep applying", "keep getting rejected",
            "no callbacks", "no callback", "always rejected",
            # the same wall said from the other side: what you sent, not what you did not get
            "gets a reply", "get a reply", "got a reply", "never replied", "no reply",
            "any replies", "never got back", "not got back", "still waiting to hear",
            "no offers", "no job offers")),
          "The top third of your CV is the part that gets read: rewrite it for each advert with "
          "the advert's own words for the job and the two things it asks for in the first five "
          "lines, and apply in the first day or two rather than the last. A dozen tailored applications beat sixty "
          "copies. Ring or email a week after sending to ask whether they need anything else, and "
          "ask every rejection for one line of feedback - plenty of places will tell you "
          "something useful.",
          avoid=("prepare", "preparing", "prep", "nervous", "questions", "wear", "wearing",
                 "what do i say", "salary", "first day", "resign", "quit", "notice",
                 # a rejection is the consolation line, not advice on how to write the CV; the
                 # interview itself is not, because "interview two weeks ago, never heard back"
                 # is the same wall of silence as a CV with no reply
                 "got rejected", "was rejected", "rejected me", "rejected after",
                 "went badly", "did badly", "turned down", "turned me down", "gave me feedback",
                 "got feedback",
                 # a line about how the search is making them feel is a feelings line
                 "mental health", "suffering", "depressed", "depression", "anxiety", "anxious",
                 "cant cope", "can't cope", "struggling", "burnout", "burnt out", "burned out",
                 "stress", "stressed", "miserable", "hopeless", "giving up")),

    entry("references",
          (("reference", "references", "referee"),
           ("ask", "who", "former", "previous", "boss", "employer", "use", "need",
            # "how do i get a reference from a manager i didnt get on with": the hard version of
            # the ask, which is the one worth answering
            "get", "manager", "didnt get on", "didn't get on", "dont get on", "don't get on",
            "not get on", "didnt like", "left", "leave", "quit", "fired",
            # the person with nobody to name is choosing a name, which is this card: these words
            # left the check card's key and the lines fell to the job-search plan instead
            "first job", "first proper job", "no experience", "no work experience",
            "never had a job", "never worked")),
          "Ask two people who have managed you - or one manager and one senior colleague - and ask "
          "before you hand their name over. Send them the job description and one line about what "
          "you want them to stress. A manager from years ago is fine; a friend is not. If nobody "
          "has managed you yet, a teacher, a coach or the person who ran the volunteering is the "
          "usual choice.",
          # a landlord's reference for a flat or a mortgage is the renting entry's line, and a
          # referee in a football match is a person with a whistle rather than a name on a form:
          # "how much do referees get paid" was answered with how to ask a manager for a reference
          avoid=("landlord", "landlady", "tenancy", "tenant", "letting", "renting", "rent",
                 "flat", "house", "mortgage", "deposit",
                 "football", "football match", "match", "whistle", "linesman", "offside",
                 "soccer", "rugby", "paid", "get paid", "pay", "earn", "salary")),

    # Two more questions about a reference came back as a shrug or as the wrong card: "will they
    # check references" and "what does a reference say" got the search hedge, and "can my old boss
    # give me a bad reference" got the how-to-write-one card. The subject is the same as the entry
    # above, but the question is what happens after you hand the name over, so it is its own card.
    entry("reference-check",
          (("reference", "references"),
           ("check", "checks", "checking", "checked", "say", "says", "saying", "bad", "good",
            "would they", "will they", "do they", "sacked", "dismissed",
            # "no experience" and "first job" were here and took the choosing lines
            # ("what can i use as a reference with no experience") to this card; they are the
            # who-to-ask card's words, so they are gone from this key
            "worth anything", "matter", "holds up")),
          "They usually ring one of the two after the interview and before the offer, and the "
          "questions are plain: the dates you were there, your job title, and whether they would "
          "take you back. Permission comes first, so a boss who rings without asking is in the "
          "wrong. What they say has to be true, so a dismissal can be mentioned if it is accurate - "
          "though many big employers now give only dates and title to avoid the argument.",
          # the two entries either side of this one: who to ask, and how to write one
          avoid=("who should i", "who do i ask", "how do i write", "how to write", "write a",
                 "write me", "reference letter", "letter of recommendation",
                 "landlord", "landlady", "tenancy", "tenant", "letting", "renting", "rent",
                 "flat", "house", "mortgage", "deposit", "football", "match", "whistle",
                 "linesman", "offside", "soccer", "rugby", "paid", "pay", "earn", "salary",
                 "essay", "assignment", "coursework", "bibliography", "harvard", "cite"),
          # choosing a name is the who-to-ask card, whatever else the line says
          guard=_not_choosing_a_name,
          bias=2),

    # And the employer's side of the same word, which was answered with how to write the letter:
    # "can i refuse to give a reference" is a question about being obliged to give one at all.
    entry("reference-obliged",
          (("reference", "references"),
           ("refuse", "refusing", "refused", "obliged", "obligation", "have to give",
            "required to give", "must give", "must i give", "legal", "legally", "the law",
            # "does a reference have to be my manager" is the job-hunter's question and was
            # answered with the law on employers, so the bare "have to" is not in this key
            "have to give", "do i have to give", "for a leaver", "for a leaving",
            # the same question in the words people use for being made to: "can my employer
            # make me give a reference" was the how-to-write-one card
            "make me give", "make me write", "force me", "forced to", "compelled",
            "compulsory", "can they make me", "can my employer make me",
            "sued", "wont give", "won't give", "wont write", "won't write", "decline")),
          "In the UK an employer is not obliged to give one unless your contract says so or a "
          "regulator "
          "does - banks, care work and teaching are the usual exceptions - and a plain no is "
          "lawful. If you do give one it must be fair and accurate, so stick to dates, title and "
          "facts you could stand behind in front of the person. A short no is safer than a "
          "half-hearted yes.",
          avoid=("landlord", "landlady", "tenancy", "tenant", "letting", "renting", "rent",
                 "flat", "house", "mortgage", "deposit", "football", "match", "whistle",
                 "linesman", "essay", "assignment", "bibliography", "harvard", "cite"),
          bias=2),

    # The other half of the reference: not asking for one but writing one, which is asked in
    # the words "how do i write a reference letter" and "how do i give someone a reference", and
    # was a shrug on main. Kept beside the asking entry so the two read as one subject.
    entry("write-a-reference",
          (("reference letter", "letter of recommendation", "written reference",
            "give a reference", "give someone a reference", "write a reference",
            "a reference for", "reference for someone", "reference", "references",
            "recommendation"),
           ("write", "writing", "give", "giving", "asked me", "ask me", "someone",
            "an employee", "my employee", "a colleague", "a student", "former",
            "ex-employee", "staff", "recommend"),
           # the letter itself is the third signal: "how do i write a reference letter" is the
           # write-a-reference ask, and this is the group that keeps it off the icing row
           ("reference letter", "letter of recommendation", "for someone", "for a colleague",
            "for a student", "for an employee", "for my colleague", "for my student",
            "reference for", "recommendation letter")),
          "Answer three things in that order and keep it to a page: how you know them and for how "
          "long, one or two things they actually did with what came of it, and whether you would "
          "employ them again. Name the job they are going for and speak to that, give dates and "
          "job titles you would stand behind if the employer rang to check them, and say nothing "
          "you could not defend to the person's face. Warm but specific beats warm and vague.",
          # asking someone to be your referee is the entry above, and a landlord's reference is
          # the tenancy one
          avoid=("my referee", "be my reference", "who should i ask", "my landlord",
                 # "can my old boss give me a bad reference" is the person needing one, and
                 # "can i refuse to give a reference" is whether they have to give one at all:
                 # both are about the reference itself, not about how to word the letter
                 "give me a", "give me one", "bad reference", "good reference", "refuse",
                 "obliged", "required to give", "what does a reference", "checks my reference",
                 "landlady", "tenancy", "tenant", "letting agent", "renting", "mortgage",
                 "to be a reference", "ask for a reference", "get a reference",
                 # "give me a book recommendation" is a pick, not a reference letter: the noun
                 # after "recommendation" is what the person wants picked, so the things a
                 # recommendation is asked for are held out (main answered it with this card)
                 "book", "books", "film", "films", "podcast", "podcasts", "series",
                 "boxset", "recipe", "recipes", "restaurant", "what to read", "what to watch",
                 # "i need a reference for a flat" is the tenant being asked for one, not the
                 # employer writing one: the property, not the job, is what the letter is for
                 "for a flat", "for a house", "for a rental", "for an apartment",
                 "flat reference", "house reference", "landlord reference",
                 # the employer's own question ("do i have to give a reference for a leaver")
                 "have to give", "do i have to", "obliged", "legally", "required to give",
                 "make me give", "make me write", "force me", "compelled", "can they make me",
                 "tenant reference", "rental reference"),
          # the icing row in cooking.py keys the bare word "letters" for piped icing and ranks
          # ahead on a line like "how do i write a reference letter"; the bias keeps the letter
          # with the reference while that reach is on main (#3359 is the fix for it)
          guard=_writing_one_not_needing_one,
          bias=1),
    entry("job-search-plan",
          (("job search", "find a job", "looking for work", "out of work", "job hunting",
            "get a job", "job with no experience", "no experience", "first job"),
           ("how", "start", "plan", "where", "best", "long", "should i", "advice", "tips",
            "first", "entry", "nothing")),
          "Split your week in half: five tailored applications, and three conversations with "
          "people who might know someone. Most jobs come through a person rather than a portal, so "
          "tell ten people you trust exactly what you are looking for. Keep a one-page list of "
          "what you sent and when, and follow up a week later.",
          # "should i do a masters or just get a job" is the study-or-work decision, and
          # "how do i get a job in another country" is about the country, not the plan.
          # a named workplace is `job-in-a-place`'s line: the way into a care home or a
          # supermarket is the employer's own, and this plan names none of it
          avoid=("masters", "master's", "degree", "phd", "postgrad", "postgraduate",
                 "university", "college", "another country", "abroad", "visa", "move to",
                 # a line about a reference is the reference rows' question, and "first job"
                 # is in this row's key: "who should i use as a reference for my first job"
                 # was answered with the plan for finding one
                 "reference", "references", "referee", "referees", "character reference"),
          # ... and the guard, not a word in that list, because every place word here is also an
          # ordinary one: see `_not_a_named_place`.
          guard=_not_a_named_place),

    # "how do i get a job in a care home" is not the job-hunt plan: the plan splits a week
    # between applications and conversations, and the care home, the supermarket, the school and
    # the cafe each have their own way in.
    entry("job-in-a-place",
          # The second part says a job, and the ask words are the gate: "i work in a warehouse" is
          # the person telling the bot where they work, "i got a job at tesco" is their news and
          # "its for a warehouse job" is the middle of somebody else's sentence. All three were
          # being told how to apply once this row existed, and the interview rows lost their own
          # lines to it as well, so a line only reaches the way in when it is asking for one.
          (JOB_PLACE_WORDS,
           ("job", "jobs", "work", "working", "apply", "applying", "start", "experience",
            "vacancy", "vacancies", "hiring", "become")),
          _job_in_a_place,
          ask=("how do i", "how can i", "how to", "where do i", "where can i", "what's the best way",
               "whats the best way", "want to", "want a", "any jobs", "jobs going", "job going",
               "can i get", "get into", "is it hard", "do i need", "ive applied", "i've applied"),
          # The person telling the bot where they work, and the interview they already have, are
          # other rows' lines.
          # "i work in" is deliberately NOT here: "how do i work in retail" contains those three
          # words in that order, and an avoid on them stands the row down on its own question.
          # The ask words above already keep the person's own "i work in a warehouse" out.
          avoid=("teaching assistant", "teaching assistants", "ta course", "ta qualification",
                 "i got a job", "got a job", "got the job", "gotten", "i started", "started my",
                 "my new job", "my job", "new job", "interview", "interviews", "wear", "wearing",
                 "wore", "dress code", "supervisor", "promotion", "changed jobs", "i left",
                 "left my job", "quit", "sacked", "redundant",
                 # A person who already works in the place and wants out is not asking for the
                 # way in: "i work in a school and i want to leave" was handed the school
                 # office's supply-list answer, where main says "Leave - fair enough."
                 "i want to leave", "want to leave", "leaving", "resign", "hand in my notice",
                 "hate my job")),

    entry("career-change",
          # "change jobs" is the same question in the words people use: without it, "i want to
          # change jobs but i dont know what to do" got a shrug
          (("career change", "change career", "switch careers", "retrain", "career switch",
            "change jobs", "change job", "changing jobs", "switch jobs", "switching jobs",
            "move jobs"),
           ("how", "start", "later", "worth", "40", "50", "40s", "50s", "should i", "want to",
            "become", "where do i start")),
          "Try the smallest real version first: an evening course, one freelance job, or a sideways "
          "move inside your current employer. Talk to three people doing the job now and ask what "
          "the bad days are like, not the good ones. Most successful switches are 18 months of "
          "steady part-time effort, not a leap."),

    # "how do i know if im in the wrong job" was a shrug, and so was the same question in the
    # other direction ("is my job right for me", "what job should i do"). The changing row above
    # needs the word change, so nothing answered the question people ask before they decide to.
    entry("wrong-job",
          (("wrong job", "wrong career", "right job", "right career", "job is right for me",
            "right job for me", "job for me", "career for me", "what job", "which job",
            "what career", "which career", "what i want to do", "what should i do for work",
            "my job is making me",
            # The same question in the shapes people write when they have no trade in mind:
            # "what jobs are out there for me", "what kind of job should i do", "how do i choose
            # a career", "what job would suit me" and "i dont know what job i want" were all the
            # search hedge or an echo, while the same doubt said the other way round ("how do i
            # know if im in the wrong job") has been answered here.
            "kind of job", "kinds of job", "sort of job", "sorts of job",
            "what jobs", "which jobs", "jobs out there", "jobs are there", "jobs for me",
            "jobs for someone", "someone like me",
            "choose a career", "pick a career", "choosing a career", "choose a job",
            "pick a job", "choosing a job", "decide on a career",
            "career suits me", "job suits me", "would suit me",
            "what job i want", "what career i want", "dont know what job", "don't know what job",
            "what to do for work", "what to do for a living", "for a living",
            # "what else to do" and the rest are keys; "what should i do with my life" is NOT:
            # that line already has its own good answer (three short lists), and taking it for
            # the judge-by-the-week was a loss
            "what else to do", "job right for me"),
           ("how do i know", "know if", "figure out", "work out", "decide", "choosing",
            "should i", "how do i find", "what should i", "not sure", "no idea", "hate",
            "unhappy", "miserable", "stuck", "bored",
            # the ask words the new keys lean on: "what kind of job should i do" says "should i"
            # and "what jobs could i do" says "could i", and both are the same doubt
            "how do i", "would", "could i", "can i", "pick", "choose", "suit",
            "living", "out there", "are there", "dont know", "don't know",
            # "is my job right for me" says none of those words: the doubt is in the key and the
            # ask is the plain question at the front of the line
            "is my", "is it")),
          "Judge it by the week rather than the day: for two weeks note what you actually did, "
          "then ask whether the bits you would gladly do again could be most of a job. Dread that "
          "does not lift by Monday, or a week whose good part is the people or the pay rather "
          "than the work, is the sign that matters. Test it before you leap: a secondment towards "
          "the part you like, two people doing it now, or a small version - an evening course, a "
          "weekend shift.",
          # a named trade or profession is the becoming-a-X card, and a bad boss or a row at work
          # is a work problem, not a career question
          avoid=("become", "becoming", "train as", "qualify", "apprentice", "apprenticeship",
                 "degree", "gcses", "a levels", "teaching", "nursing", "lawyer", "doctor",
                 "salary", "pay rise", "money", "quit tomorrow", "hand in my notice",
                 "my boss", "my manager", "bullying", "bullied", "colleague", "colleagues",
                 "overtime", "rota", "shifts", "redundancy", "redundant", "fired", "interview",
                 # "would suit me" is also what clothes, colours and hair are asked about, and
                 # those lines name no job at all: "what colour would suit me", "which glasses
                 # would suit me". A thing to wear or a colour stands this row down.
                 "colour", "colours", "color", "colors", "hair", "dress", "dresses", "clothes",
                 "outfit", "glasses", "spectacles", "frame", "frames", "paint", "wallpaper",
                 "curtains", "blinds", "garden", "plant", "plants", "wall",
                 # the thing being chosen is the word people actually write, and none of the
                 # words above is it: "what haircut would suit me", "what beard would suit me",
                 # "what lipstick would suit me", "what length would suit me" were the career
                 # review (good-lever, #9692 review)
                 "haircut", "haircuts", "hairstyle", "hairstyles", "beard", "beards",
                 "moustache", "mustache", "lipstick", "lipsticks", "makeup", "make up",
                 "nails", "nail varnish", "length", "brow", "brows", "fringe",
                 "tan", "self tan", "eyeshadow", "blush", "foundation", "tattoo", "tattoos",
                 "curtain", "sofa", "carpet", "kitchen", "bathroom", "bedroom", "tiles",
                 # "what jobs can i do with no experience" is the first-job answer, not a career
                 # review: the person is asking what will take them, not what they would enjoy
                 "no experience", "without experience", "no qualifications", "no gcses",
                 "first job", "never had a job",
                 # the same line with an age in it: "what jobs are there for a 16 year old" and
                 # "what jobs can a school leaver get" are the will-they-take-me question
                 "16 year old", "16 years old", "15 year old", "15 years old", "17 year old",
                 "17 years old", "school leaver", "school leavers", "left school",
                 # "what jobs could i do with the hours i have" is the contract-and-hours
                 # question, and the hours answer is more use than a career review
                 "hours",
                 # choosing between offers already in hand is a decision about two jobs, not
                 # about what to do with a life; the offers rows own it
                 "job offer", "job offers", "two offers", "two jobs", "second job",
                 "offer from",
                 # "choose a job i love or one that pays" is the trade between two jobs already
                 # named, and "choose a job i can do from home" is where the work has to be:
                 # the trade row puts four columns on paper for both, so a job picked by its
                 # pay, its place or its happiness is that row's line, not this review
                 # (good-lever, #answers 102946; alert-frog, #9692 review)
                 "pays", "pay well", "pays well", "well paid", "from home", "work from home",
                 "remote", "i love", "love it", "happiness", " vs ",
                 # naming a condition is asking about the work that fits round it, not for a
                 # career review: "what jobs are there for someone with anxiety" wants the
                 # work-problem answer, which names the GP and the reasonable adjustments
                 # (breezy-violet, #9692 review)
                 "anxiety", "anxious", "depression", "depressed", "autism", "autistic", "adhd",
                 "disability", "disabilities", "mental health", "introvert", "shy",
                 "confidence", "burnout", "burned out", "burnt out"),
          # Not knowing what you want at all is the composer's own warm line ("Plenty of people
          # who look settled are quietly making it up too"), and it is better than any list: "im
          # 30 and still dont know what i want to do" was handed the judge-by-the-week page, which
          # is a method given to someone who wanted to be taken seriously. The words cannot do
          # this one, because "how do i know what i want to do" is the same words as a question and
          # has always been answered here: it is the shape of a statement about themselves.
          guard=_not_saying_they_are_lost_or_wearing_it,
          bias=1),

    # --- the interview --------------------------------------------------
    entry("interview-prep",
          (("job interview", "interview", "interviews", "interviewing"),
           ("prepare", "questions", "tips", "tomorrow", "nervous", "ready", "thursday", "monday",
            "tuesday", "wednesday", "friday", "saturday", "sunday", "coming up", "this week",
            "next week", "got an interview", "have an interview", "interview on", "interview in",
            # the same ask written as a what-to-say: "what do i say in a job interview" was
            # answered by the thank-you-note entry.
            "what do i say", "what should i say", "what to say", "say in", "what do i tell",
            "what should i wear",
            # "how do i handle a job interview" and "how do i do well in an interview" name
            # nothing but the interview plus the asking words, and reached the shrug.
            "how", "how do i", "how to", "handle", "handling", "do well", "do good", "ace",
            "advice", "succeed", "succeed in", "help", "going to",
            # "how do i get better at interviews", "how do i interview better" and "how do i
            # improve my interview technique" were all a shrug over an answer that exists: the
            # subject is named and the improving verb was not in the row
            # "what happens at a job interview", "what should i expect", "what do they ask you"
            # are the same subject asked for the shape of the day, and were a shrug too
            "what happens", "what to expect", "what should i expect", "what do i expect",
            "what can i expect", "whats it like", "what is it like", "interview like",
            "like an interview", "what do they ask", "what will they ask", "what do they ask you",
            "what kind of questions",
            # the shape of the day asked as a what-does-it-look-like: "what does an interview day
            # look like", "how does the day go", "run me through the interview day" and "whats
            # the format of the interview" were a shrug or the preparation answer, because only
            # "what happens" and "what to expect" were wordings the row knew.
            "look like", "looks like", "the day", "day go", "day like", "run through",
            "run me through", "walk me through", "walk through", "the format",
            "whats the format", "what is the format", "how does it go",
            "does the day") + IMPROVE),
          _interview_prep,
          # "what should i wear" is in the key list because a follow-up that keeps the subject
          # ("im nervous about my interview, what should i wear") is an outfit question, not a
          # preparation one. When the words arrive the other way round - the clothing words are
          # all the line has, and `interview` comes from the memory's subject - this entry ranks
          # level with `interview-outfit` and then declines, so the turn ended on the shrug.
          # "ive got a job interview on friday for a warehouse supervisor role" / "what should i
          # wear" lost the smart-casual answer that way. Dressing stays with clothing - but only
          # the asking words (`wear`, `outfit`) are declined, because `shoes`, `shirt`, `suit`,
          # `dress` and `clothes` name shops, trades and products too: "how do i prepare for an
          # interview at a shoe shop" and "... as a shirt designer" are preparation, not dressing.
          avoid=("school", "college", "university", "exam", "coursework", "journalist",
                 "newspaper", "radio", "prime minister", "documentary", "police",
                 "wear", "wearing", "outfit", "outfits",
                 # "I've got an interview on Friday" with a cold is a question about the cold
                 "cold", "colds", "flu", "cough", "throat", "sneez", "sick", "ill",
                 "migraine", "toothache",
                 # "i have an interview tomorrow, what do i need to bring" is the packing
                 # question with a day in it, and the day ("tomorrow", "friday") is this row's
                 # own key word, so this row took it and answered with the four stories instead.
                 # A preparation line never says what to bring, so the asking phrases stand down.
                 "what to bring", "what to take", "need to bring", "need to take",
                 "should i bring", "should i take", "what do i bring", "what do i take",
                 "bring with me", "take with me")),

    # "What should i take to a job interview" was answered with the four-column job-offer
    # comparison, because an interview is where an offer comes from; "what should i bring to an
    # interview" reached nobody. The ask is a packing list, which is a different answer from the
    # preparation one and from the outfit one, so it is keyed on the asking phrase rather than on
    # a bare `take`, which every shopping line carries ("what should i take to a picnic").
    entry("interview-take",
          (("job interview", "interview", "interviews", "interviewing"),
           ("what should i take", "what should i bring", "what to take", "what to bring",
            "what do i need to take", "what do i need to bring", "do i need to take",
            "do i need to bring", "need to take", "need to bring", "should i take",
            "should i bring", "take with me", "bring with me", "what do i bring",
            "what do i take")),
          "Take printed copies of your CV, the letter or email with the address and the time, "
          "photo ID, and a pen and a small notebook. Add three questions of your own about the "
          "team and what the first six months look like, and the name of whoever invited you so "
          "you can ask for them at reception. Put the address in your phone the night before and "
          "arrive ten minutes early: nothing you have to hold all morning, no coffee to spill.",
          # dressing and preparing are their own answers, and a line about a different kind of
          # thing to carry (a picnic, a first day, a school trip) is not this question
          avoid=("wear", "wearing", "outfit", "outfits", "suit", "shoes", "shirt", "dress",
                 "prepare", "preparing", "prepared", "tips", "picnic", "camping", "barbecue",
                 "bbq", "lunch", "first day",
                 "phone interview", "video interview", "telephone interview", "phone screen")),

    # A phone or video interview is a different room from a face-to-face one, and the words
    # "phone" and "video" made the subject technology, so "I've got a phone interview at 2pm
    # today" was only noted back to the person and "phone interview tomorrow" got the general
    # preparation answer. Keyed on the medium plus the word interview, so the subject cannot
    # take it away.
    entry("phone-interview",
          (("phone interview", "telephone interview", "phone screen", "video interview",
            "video call interview", "video call", "video calls", "interview over the phone",
            "interview on the phone", "interview by phone", "zoom interview", "teams interview",
            "skype interview"),
           ("interview", "phone", "video", "call", "screen", "zoom", "teams", "skype",
            "prepare", "prepared", "preparation", "tips", "advice", "ready", "nervous",
            "tomorrow", "today", "this afternoon", "this morning", "friday", "monday",
            "tuesday", "wednesday", "thursday", "got", "have", "what", "how", "help")),
          ("Treat it like a meeting, not a phone call: sit at a table with your notes, the job "
           "description and four stories written out in front of you - a week you organised, a "
           "difficult customer, something you fixed, a time you got it wrong and changed. Sit "
           "upright or stand, because the voice carries better. Quiet room, door shut, and a charged phone with "
           "the ringer off - take it sitting down, never walking about. On video, check the link "
           "ten minutes early, look at the camera rather than at your own face, and put a lamp "
           "in front of you rather than a window behind. The first twenty seconds set the tone: "
           "\"Thanks for making the time - I've been looking forward to this.\" Answer in "
           "two or three sentences and stop, since silence on a call reads as thinking, and keep "
           "the questions you want to ask written down for the end, because they will ask."),
          # the word interview has to be there: a video call that keeps dropping is a
          # broadband question, not an interview one
          ask=("interview", "interviews"),
          # an interview's own questions, the outfit and the cold are other rows
          avoid=("wear", "wearing", "outfit", "weakness", "strength", "salary", "money",
                 "cold", "cough", "flu", "sick", "ill", "phone bill", "phone contract",
                 "phone upgrade", "phone screen broke", "cracked", "battery", "storage"),
          bias=1),

    entry("interview-tell-me-about-yourself",
          (("tell me about yourself", "introduce yourself", "introduce myself",
            "introduce me", "talk about myself", "talk about yourself",
            "about yourself in", "starter question", "opener question", "as an opener",
            "for a starter", "opening question", "first question",
            "start the interview", "start an interview", "start my interview",
            "kick off the interview", "open the interview", "open an interview",
            "opening an interview"),
           ("interview", "answer", "how", "question",
            # the same question as a quotation, with the interviewer in the line: "what should i
            # say when they ask tell me about yourself" was a shrug, because "say" and "ask" were
            # not words this card read.
            "say", "saying", "reply", "respond", "asked", "they ask", "they say", "he asks",
            "she asks")),
          "Ninety seconds in this order: what you do now or did last, one thing you did well that "
          "they will care about, and why this job is the next step. Nothing about childhood, and "
          "don't walk through the CV line by line - they have read it.",
          # A line that names this question - "what do i say when they ask me to introduce
          # myself" - scores the same as the general interview script, which also keys on "what
          # do i say". The one that names the question is the one to answer.
          bias=1,
          # "starter" on its own is also a jar of flour and water, and "how do i start a sourdough
          # starter" was answered with the ninety seconds. A kitchen starter is not a question in
          # an interview, so the baking words take the line away from this entry.
          # Bare "starter" is the conversation starter, and it is also the jar: with the dough
          # words above it, "how do i know my starter is ready" still came here, because the line
          # says none of them. The interview keeps its own phrases ("opening question", "start the
          # interview") and only the bare word stands down.
          # The other half of the bare word is the car part: "how do i test a starter motor" and
          # "my starter motor just clicks" are the same plain "how", so the vehicle and garden
          # words stand down here too and cars.py answers them.
          avoid=("sourdough", "sour dough", "bread", "dough", "yeast", "flour", "batter",
                 "cake", "loaf", "jar", "kefir", "yoghurt", "yogurt", "ginger bug",
                 "starter", "starters",
                 "motor", "motors", "engine", "engines", "car", "cars", "van", "vans",
                 "battery", "batteries", "lawnmower", "mower", "boiler", "boilers",
                 "plant", "plants", "cutting", "cuttings", "seed", "seeds", "compost",
                 "garden", "greenhouse")),

    entry("interview-weakness",
          (("weakness", "weaknesses", "greatest weakness", "biggest weakness"),
           ("interview", "answer", "question", "say", "what")),
          "Pick something real, small, and already being worked on: \"I used to take everything on "
          "rather than ask for help, so now I list what is on my plate with my manager every "
          "Monday.\" Skip the humble-brag about perfectionism, and skip anything that is the core "
          "of the job you are applying for.",
          # "what should i say at a job interview when they ask about weaknesses" lost this row to
          # interview-a-time-when, on the words "when they ask", and was told how to build a STAR
          # story. The question is named in the line, so the row that answers it wins the tie,
          # and four is what it takes to win it.
          bias=4),

    # The other half of the weakness question. "what are your greatest strengths" went to the
    # search hedge twice over - once with "how do i answer" in front of it - because no row owned
    # the word. Two things the advert asks for with one piece of proof each is the answer a person
    # can actually use, so it is the one here.
    entry("interview-strengths",
          (("strengths", "greatest strength", "biggest strength", "main strength",
            "strongest", "key strength", "best quality", "best qualities",
            "what are my strengths", "what are your strengths",
            # the same question behind a saying frame, which the preparation script otherwise
            # takes on "what do i say" plus "interview"
            "about my strengths", "about your strengths", "strengths in an interview",
            "strength in an interview", "strengths question", "strengths and weaknesses"),
           ("interview", "interviewer", "job", "role", "answer", "say", "question", "weakness",
            "weaknesses", "applying", "hiring", "employer", "recruiter", "cv", "advert")),
          "Pick two the advert actually asks for and hang proof on each: \"I'm the one who keeps "
          "a messy project moving - on the last one I turned three spreadsheets into one board and "
          "we stopped missing deadlines.\" Two, said slowly, beats a list of five. \"I'm a hard "
          "worker\" and \"I'm a perfectionist\" are the two that cost you the room.",
          # a strength is a gym word too, and "how do i build my strength after a knee op" is the
          # fitness answer, not the interview one
          # "how do i answer what are your greatest strengths" names no interview: the frame is
          # "how do i answer", and without those words in the gate the row declined the two
          # commonest ways of asking it.
          ask=("interview", "interviews", "interviewer", "job", "role", "hiring", "employer",
               "recruiter", "applying", "application", "weakness", "weaknesses", "advert",
               "candidate", "answer", "say", "question", "they ask"),
          avoid=("gym", "training", "workout", "weights", "lifting", "muscle", "muscles",
                 "squat", "deadlift", "protein", "exercise", "exercises", "fitness",
                 "knee", "back", "legs", "arms", "grip")),

    # "tell me about a time when you..." is the question most interviews are made of, and every
    # way of asking how to answer it was a shrug: the STAR script is `interview-prep`, which only
    # answers a line that names the interview. Keyed on the phrase that quotes the question, so
    # a story about a customer's bad day cannot reach it.
    entry("interview-a-time-when",
          (("tell me about a time", "give me an example of a time", "describe a time",
            "a time when you", "a time you had", "a time you made", "a time you dealt",
            "a situation where you", "an example of when you", "talk me through a time",
            "when have you had to", "tell me about a situation"),
           ("interview", "interviewer", "question", "answer", "asked", "they ask", "job", "role",
            "problem", "conflict", "customer", "deadline", "mistake", "team", "colleague",
            "manager", "boss", "difficult", "pressure", "work")),
          "One story, four sentences: where you were and what went wrong, what you chose to do, "
          "what actually happened, and how it turned out - in numbers if there are numbers. \"A "
          "supplier went quiet the week of a launch. I rang their depot instead of emailing, got a "
          "half-load for the Tuesday, and we shipped on time.\" Have two ready, one where you "
          "fixed something and one where you got it wrong, and tell the same two all the way "
          "through: interviewers compare notes.",
          bias=1,
          # the same wording at home is somebody's week, not an interview question
          avoid=("my partner", "my mum", "my dad", "my husband", "my wife", "my friend",
                 "my boyfriend", "my girlfriend", "my kid", "my son", "my daughter",
                 "my sister", "my brother", "my landlord")),

    # "why should we hire you" is the one question with no answer anywhere in the book, and it is
    # asked in almost every interview. It ties with the general preparation script on "interview"
    # alone, so it is keyed on the question itself and given the bias.
    entry("interview-why-hire-you",
          (("why should we hire you", "why should i hire you", "why hire you",
            "why should we choose you", "why should we pick you", "why choose you",
            "what makes you the right person", "why are you the best candidate",
            "why you and not", "why should we take you"),
           ("interview", "interviewer", "job", "role", "answer", "say", "ask", "question",
            "candidate", "hiring", "advert")),
          "Three things the advert asks for, with one line of your record under each: what you "
          "did, where, and what changed. Then finish on the job rather than on yourself - \"the "
          "part I'd want to get right first is the Monday handover, and that's the work I've done "
          "before.\" Nothing about being passionate or a people person: they hear it from "
          "everyone.",
          # No gate: the key is the question itself, which is only ever asked in an interview.
          # Gated on a job word it declined "what do i say when they ask why should we choose you".
          bias=1),

    entry("interview-why-you-left",
          # `quit-a-job-message` in wording.py takes `left` for its verb, so the interview ask
          # about the job already gone went to the letter - "the date your notice starts, your
          # last working day" is the one answer that ask is not. The second group is job words, not
          # "ask"/"say", so a party line ("my friend asked why i left early") is read as ordinary.
          (("why did you leave", "why you left", "why i left", "why did i leave",
            # the same question asked forward-looking, and it was a shrug: the person is
            # rehearsing the interview answer, not announcing a resignation
            "why do you want to leave", "why do you want to quit", "why are you leaving",
            "why do i want to leave", "why am i leaving", "why do you want to move on",
            "why i quit", "why you quit", "why did you quit", "why i am quitting",
            "why you are leaving", "why i am leaving", "left my last job", "left your last job",
            "leaving my last job", "reason for leaving", "what do i say about",
            # The event words are not enough on their own, but "sacked from my last job" is the
            # interview question about the job already gone, and it ties with `interview-prep`
            # without this: the person who was sacked got the STAR-stories script.
            "sacked from my last job", "fired from my last job", "let go from my last job",
            "dismissed from my last job", "sacked from my previous job",
            "fired from my previous job", "what do i say about being sacked",
            "how do i explain being sacked", "what do i say about being fired",
            # Not the bare event words: "i got fired from my job today" and "my husband was
            # sacked" are someone's news, and the interview script is the wrong reply to news.
            # What belongs here is the phrase that already carries the interview frame.
            "why i got fired", "why i was fired", "why you got fired", "why you were fired",
            "why i was sacked", "why i got sacked", "why you were sacked", "why i was let go",
            "why you were let go", "why i was made redundant", "why you were made redundant",
            "explain being sacked", "explain being fired", "explain the gap", "explain my gap",
            # The event said plainly is the subject too: "i was sacked how do i explain it in an
            # interview" was the STAR-stories script because none of the rehearsed phrasings
            # above was in the line. The interview frame is the second group, so news of a
            # sacking with no interview, cv or employer in it still stays with its own card.
            "sacked", "fired", "dismissed", "let go", "made redundant", "got the sack",
            "was let go", "was dismissed",
            # "explain that" and the reason for the dismissal, which the practical exit card
            # outscored: "i was dismissed for gross misconduct how do i explain that"
            "explain that", "explain this", "gross misconduct", "misconduct",
            "how do i bring it up", "how do i explain it", "how do i explain that",
            "being sacked in an interview", "being fired in an interview",
            "being made redundant in an interview", "got fired in an interview"),
           ("interview", "interviewer", "job", "role", "company", "employer", "recruiter",
            "hr", "cv", "application",
            # "what do i say about being sacked" is in the phrase list above and still scored
            # one, because it names no interview and no job: the event words are the second
            # group, and the first group already carries the interview frame ("what do i say
            # about", "why i was sacked"), so news of a sacking cannot reach it.
            # The leaving verbs are NOT here. `leave`, `leaving`, `quit`, `resign` in this group
            # completed the bare frames in group one on their own, so every line with a leaving
            # verb scored: "why did you leave the window open", "why did you leave your bag",
            # "why are you leaving so soon", "why did you leave your husband", "why did you
            # quit smoking" all got the interview script (robust-sparrow and early-badge both
            # measured it). The lines that are the interview question name a job or are already
            # whole phrases in group one.
            "sacked", "fired", "dismissed", "redundant", "let go", "made redundant",
            # the ways the dismissed person asks what to do about it
            "explain", "explaining", "say", "saying", "say it", "explain it", "tell them",
            "tell a new", "disclose", "mention")),
          "Short, true and forward-looking: what the old job could not offer, then what you went "
          "looking for. \"I had gone as far as I could there and wanted the design work to be the "
          "main part of the job, which is what this role is.\" Never blame a person and do not "
          "mention money first; if you were let go, one plain sentence and move on - \"the team was "
          "restructured and my role went with it\" - then say what you have done since. You need "
          "not volunteer it if the form does not ask, but never answer no to a direct question: a "
          "reference check can bring it out, and a quiet explanation beats being caught.",
          # A sacking asked as an interview question ties with `interview-prep`'s generic
          # script, and this is the answer that fits it.
          # `leaving` in the second group is a job word, and one line says it about a person:
          # "why are you leaving me" came back with the interview script.
          # A line about strengths is never this question, and "what do i say about my strengths in
          # an interview" was answered with it: "what do i say about" is a phrase of this key.
          avoid=("leaving me", "leave me", "left me", "leaving us", "left us", "leave her",
                 "leave him", "leaving her", "leaving him",
                 "strength", "strengths", "greatest strength", "biggest strength",
                 "my weaknesses", "my weakness", "greatest weakness", "biggest weakness"),
          guard=_it_is_their_own_dismissal,
          bias=1),

    # "why do you want this job" is the interview question said by its own name, with no
    # "interview" and no "say" anywhere in it, so the gate needed a job word to open on: all
    # four ways of asking it were a shrug. The job words are the second group, not the first,
    # so "why do you want a dog" and "why do you want to move house" stay out.
    entry("interview-why-this-job",
          (("why do you want", "why this job", "why our company", "why this role", "why work here",
            "why this company", "why do i want",
            # "what do i say when they ask why i want this job" was a shrug: the interview's own
            # question said in the first person
            "why i want this job", "why i want to work here", "why you want this job",
            "why i want the job", "why i chose this job"),
           ("interview", "answer", "ask", "say", "question",
            "job", "jobs", "role", "company", "employer", "work here", "working here",
            "applying", "application", "recruiter", "hiring")),
          "Join one real thing about them to one real thing about you: \"You're rebuilding the "
          "booking system, and that's the part of my last job I liked most.\" Ten minutes on their "
          "website before you go is enough to sound like you mean it. Never answer with \"I need a "
          "job\" or with vague praise of their culture."),

    # The other opener everybody meets. "how do i answer where do you see yourself in five years"
    # was the search hedge: no card had the question, and it is asked in nearly every interview.
    entry("interview-five-years",
          (("in five years", "where do you see yourself", "see yourself in five",
            "five years time", "five years from now", "ten years time", "career plan question",
            "where do you want to be in five"),
           ("answer", "say", "saying", "reply", "respond", "interview", "interviewer", "ask",
            "asked", "they ask", "how", "what", "where", "question")),
          'Talk about the work you want to be better at, not a job title you have decided on: "I '
          'want to be the person who runs these projects, so I am looking for a place I can learn '
          'the whole cycle." One sentence on what you are doing now to get there - a course, a '
          'piece of work you put your hand up for - and stop. Never name their manager\'s job, '
          'and never say you want to be doing something else entirely.',
          avoid=("five a side", "five years old", "my son", "my daughter", "child")),

    # "how do i answer what are you doing at the moment" was the bot's own identity: the
    # interview's other opener had no card, so the composer read the words as a question to it.
    # The answer is the two sentences a person says in the room.
    entry("interview-current-role",
          (("what are you doing at the moment", "what do you do at the moment",
            "what are you doing now", "what do you do now", "what do you do currently",
            "current role", "in your current job", "tell me about your current job",
            "what is your current job", "where do you work at the moment", "your present job"),
           ("interview", "answer", "say", "reply", "respond", "question", "how", "what",
            "work", "working", "job", "role")),
          'Two sentences: your job title and what you actually do in a week, then one thing you '
          'have changed or finished. "I am a warehouse team leader - I run a shift of eight, and '
          'I have just moved us onto scanners, which cut picking errors." Thirty seconds is '
          'plenty; they are testing whether you can be brief and whether the last job taught you '
          'anything. Do not walk through your whole career - that is the next question.',
          avoid=("who are you", "what can you do", "chatbot", "app", "website", "this app")),

    entry("interview-nerves",
          (("nervous", "nerves", "panic", "terrified", "anxious",
            # Most people name the feeling by what their body does, and "i feel sick before job
            # interviews" was answered as a stomach bug: fluids, plain food, no dairy. A body
            # word plus the interview is nerves, and the event is still required, so "i feel
            # sick" on its own stays a health line.
            *NERVES_BODY),
           ("interview", "interviewer", "panel")),
          _interview_nerves,
          avoid=("exam", "test", "driving", "speech", "presentation", "date", "wedding")),

    # The paperwork question, which had no answer at all on main: "do i bring id to an
    # interview", "is a passport ok for id at an interview", "what documents do i bring". An
    # interview has to be named somewhere, so a bare "documents" or "passport" is not enough -
    # "what documents do i need to renew my passport" is a different question.
    entry("interview-documents",
          (("bring id", "bring my id", "bring some id", "bring my passport", "bring a passport",
            "passport ok", "passport be ok", "proof of id", "proof of identity", "what documents",
            "documents do i bring", "documents to bring", "documents do i need",
            "bring my cv", "bring a copy of my cv", "right to work", "bring certificates",
            "bring my certificates", "references list"),
           ("interview", "interviews", "interviewer", "recruiter", "employer",
            "job", "role", "the job", "asked me to bring", "do i need", "should i bring",
            "do i bring", "what do i bring", "what to bring")),
          "Bring photo ID - a passport or a driving licence - a copy of your CV, and the "
          "certificates for anything the advert asked for; in the UK the right-to-work documents "
          "(a passport, a visa or a share code) are often wanted on the day. A list of two "
          "referees with phone numbers is worth having as well. Whatever they put in the "
          "invitation wins over all of it, so if anything is unclear, email the recruiter and ask.",
          # a passport that is being applied for is not ID for an interview: "what documents do
          # i need for a passport" came here on "what documents" and "do i need".
          avoid=("renew my passport", "passport renewal", "apply for a passport",
                 "for a passport", "passport application", "passport photo", "passport photos",
                 "my passport has", "my passport is", "visa application", "birth certificate",
                 "driving test", "to renew")),

    # The day itself: when to arrive and what to have ready. Nothing answered either shake.
    entry("interview-day-basics",
          (("night before", "the day before", "day before", "how early should i arrive",
            "how early do i arrive", "what time should i arrive", "should i arrive early",
            "arrive early for", "morning of the interview", "on the day of the interview"),
           ("interview", "interviews", "interviewer")),
          "Know the route and aim to be ten to fifteen minutes early - not earlier, and never "
          "late; if you are ahead of that, wait in a cafe rather than the lobby. The night "
          "before, put the clothes out, print the job description and your notes, charge your "
          "phone and note the name of whoever you are meeting. Eat something before you go: a "
          "hungry interview is a shaky one."),

    # "should i shake hands at an interview" was answered with the shaky-hands health card, and
    # "what do i do with my hands" with nothing. Both are the one question about what to do
    # with your body in the room.
    entry("interview-hands",
          (("shake hands", "handshake", "shake their hand", "what do i do with my hands",
            "where do i put my hands", "eye contact", "look them in the eye", "how do i sit"),
           ("interview", "interviews", "interviewer", "panel")),
          "Take the hand if it is offered, once, at the start - an ordinary grip, two seconds - "
          "then stop thinking about it: hands in your lap or resting on the table, and look at "
          "whoever is speaking. On a panel, answer the person who asked while glancing at the "
          "others. Fidgeting reads as nerves only because it is; still hands fix it.",
          # "shaking" alone would fence the question it is named after: "should i shake hands"
          # has "shake" in it and `_forms` puts the two in one family
          avoid=("shaky", "trembling", "shake all over", "shaking all over",
                 "cant stop shaking", "can't stop shaking")),

    # "can i bring notes to an interview" was reaching the thank-you email.
    entry("interview-notes",
          (("bring notes", "bring a notebook", "bring my notes", "notes to the interview",
            "cheat sheet", "cue cards", "cue card", "crib sheet", "look at my notes"),
           ("interview", "interviews", "interviewer", "can i", "should i", "am i allowed")),
          "A small notebook with three or four prompts - the stories you want to tell and two "
          "questions to ask - is normal and reads as prepared; reading whole answers off a page "
          "does not. Glance at it when they ask something you planned for, then look up and say "
          "it in your own words. If there is a test or a presentation they will tell you what is "
          "allowed, and asking the recruiter beforehand is fine.",
          avoid=("exam", "test", "revision", "lecture")),

    # The second round is a different interview from the first, and the bot shrugged at it.
    entry("interview-second-round",
          (("second interview", "second round", "second stage", "final interview", "final round",
            "third interview", "2nd interview", "interview again", "called back for an interview",
            "another interview"),
           ("how", "what", "prepare", "expect", "tips", "do i", "different", "again", "wear",
            "long", "questions")),
          "The second one is about depth, not introductions: they already think you can do the "
          "job and are now checking they want to work with you. Have one story ready in real "
          "detail - the problem, what you decided, what it changed - where the first round wanted "
          "headlines. Look up who you are meeting and what the team shipped recently, and ask "
          "about the first ninety days and what would make them say the hire worked. Pay and "
          "notice usually come up at the end, so bring a figure.",
          avoid=("rent", "flat", "car", "car insurance")),

    entry("interview-questions-to-ask",
          (("questions to ask", "questions for them", "any questions for us",
            "questions for the interviewer", "questions should i ask", "what should i ask them",
            "what do i ask them", "what should i ask at the end", "ask at the end",
            "if you have any questions", "if they have any questions",
            "have any questions for us", "any questions for the panel", "what to ask them"),
           ("interview", "interviewer", "panel", "interview", "say", "ask", "asked", "answer",
            "end", "last", "them", "they", "job", "role")),
          "Ask what the first three months look like, why the last person in the role left, and "
          "what the team is like on a bad week. Then one for them: \"What do you enjoy about "
          "working here?\" It is the easiest question in the room and it changes the tone."),

    entry("interview-thank-you",
          (("thank you email", "thank you note", "thank you letter", "follow up email",
            "follow-up email"),
           ("interview", "after", "send", "write")),
          "Send two lines the same day: thank them for the time, and add the one thing you forgot "
          "to say that fits the job. Don't re-argue your case or attach anything they did not ask "
          "for - the point is to be memorable for the right reason."),

    entry("interview-salary",
          (("salary", "salaries", "wage", "wages", "money", "pay packet", "job offer", "offer",
            "pay offer", "the pay", "my pay", "compensation", "package", "want to be paid",
            "expecting to be paid", "paid for the role"),
           # The second part asks for a negotiation, and "pay" is not in it: "the pay" is already
           # in the first part, so a bare "pay" here let one word count for both ("which the pay
           # do i actually need", a follow-up about streaming services, became a salary question).
           # "more" alone is not a negotiation. "It's more money but I'd see less of the
           # patients" is somebody weighing up an offer, and with an offer somewhere in the
           # conversation it was getting the ask-for-a-figure script.
           ("negotiate", "negotiation", "negotiating", "counter", "higher", "increase",
            "ask for", "ask for more", "discuss", "expected salary", "how much should i ask",
            "about pay", "more pay", "pay negotiation",

            # people plan the sentence out loud: "what do i say when they ask about salary".
            # "what do i say" is NOT here: in this part it paired with the same phrase in the
            # last part and answered "what do i say in a job interview" with the salary script.
            "ask about salary", "about salary", "when they ask", "they ask"),

           # the words of the sentence people rehearse, and only ever alongside a pay word above
           ("what do i say", "what should i say", "should i say", "how do i answer",
            "how do i bring", "bring it up", "the words", "rehearse")),
          "Ask once, warmly, with a figure and a reason: \"I'm delighted about the offer. Given "
          "the range for the role and my five years doing X, could we look at 32,000?\" Name a "
          "specific number, not a range, and ask for the final version in writing. Employers "
          "expect the question and very rarely withdraw an offer over one ask.",
          avoid=("bill", "bills", "rent", "budget", "save", "saving", "debt", "tax", "pension",
                 "mortgage", "appraisal", "performance review", "promotion", "salary increase",
                 "pay increase", "pay rise", "a raise", "my raise", "my current job", "my boss",
                 "my manager", "my company", "worth paying", "paying more", "pay more for",
                 "worth it"),
          # A negotiation happens at an interview or over an offer: "how do i ask for a salary
          # increase" is about the job you already have, and "is it worth paying more" is not
          # about pay at all. A salary question with no offer word in it still counts.
          ask=("interview", "interviewing", "offer", "offered", "offer letter", "recruiter",
               "hiring", "onboarding", "start date", "new role", "salary", "want to be paid")),

    # A job advert with no number on it, and the person wondering whether they are allowed to
    # ask. Main answered "the job ad doesnt say the salary" with "Got it. Is there anything you'd
    # like a hand with?" and "how do i ask what the salary is" with the free-advice line, while
    # "they asked what salary i want" had its own script: the asking before the offer is the gap.
    entry("salary-not-given",
          (("salary", "salaries", "wage", "wages", "the pay", "pay range", "salary range",
            "how much it pays", "how much does it pay", "what it pays", "pays", "paying",
            "package", "the money",
            "remuneration", "the band", "pay band", "the figure"),
           ("not listed", "isnt listed", "isn't listed", "not advertised", "not mentioned",
            "doesnt say", "doesn't say", "dont say", "don't say", "does not say",
            "didnt say", "didn't say", "no salary", "no figure", "no number", "no range",
            "wont say", "won't say", "is not given", "not given", "not stated",
            "should i ask", "how do i ask", "ask what", "ask about the salary",
            "ask about salary", "ask for the range", "ask the range", "ask them what",
            "not sure what to say", "what do i say")),
          "Ask for the range in one short email before the interview - \"Could you tell me the "
          "salary range for this role?\" - and it costs you nothing: recruiters expect it, and a "
          "job that will not give a band is telling you something about how it hires. If you would "
          "rather not ask first, leave it to the end of the first interview, when they have met "
          "you. Have your own number ready, from what you need to live on and what the same role "
          "pays elsewhere.",
          # the negotiation at an offer, a rise in the job you have, and a person being asked
          # what they want are three other answers
          avoid=("what salary i want", "salary i want", "salary expectations", "my expectations",
                 "pay rise", "pay raise", "a raise", "pay increase", "salary increase",
                 "promotion", "negotiate", "negotiation", "counter offer", "the offer",
                 "i was offered", "minimum wage", "living wage", "annual salary", "pro rata",
                 "after tax", "take home", "payslip", "tax code"),
          # The asking is the question: "should i ask about the salary" names no job at all,
          # and it was the free-advice card because this list wanted one. A pay word plus one
          # of these is the ask.
          ask=("job", "advert", "ad", "listing", "role", "interview", "apply", "applying",
               "applied", "recruiter", "employer", "company", "they", "position",
               "ask", "asks", "asking", "asked", "should i", "how do i", "salary", "pay",
               "wage", "wages", "range")),

    entry("interrupted-at-work",
          (("interrupted", "interruptions", "interrupts", "interrupting", "people keep asking",
            "constantly asking", "can't get anything done", "cant get anything done",
            "never get anything done", "no time to think", "head down",
            # the plain way people say it: the focus has gone, and it is the office that is
            # doing it. A phrase, not the bare "focus", because "i cant focus on anything" and
            # "i cant concentrate since my dad died" are the mood and the GP's answer.
            "cant focus at work", "can't focus at work", "cant concentrate at work",
            "can't concentrate at work", "hard to focus at work", "hard to concentrate at work",
            "distracted at work", "too distracted to work", "cant focus on my work",
            "can't focus on my work"),
           ("work", "office", "desk", "at my desk", "at work", "team", "colleague",
            "colleagues", "how", "stop", "deal with", "help", "every", "five minutes",
            "all day")),
          ("Block the first ninety minutes for the work that needs thinking, before the day fills "
           "up, and treat it like a meeting in your calendar. For the rest: agree with the team "
           "that questions come by message and you will answer in two batches, wear headphones as "
           "the sign, and if one person is the source, ask them for a ten-minute slot rather than "
           "taking it piecemeal - most interruptions are curiosity, not emergencies, and asking "
           "'can it wait until two?' is a complete answer."),
          # the posture answer also lives on a desk and a chair, and this one is about people
          # An interruption at home is the day at home - the people in the room are what the
          # `wfh-focus` answer is written for - and a phone, a mood, a workload or a meal is
          # another answer's line, not a person at the desk.
          bias=1,
          avoid=("working from home", "work from home", "wfh", "remote work", "kids", "kid",
                 "children", "child", "toddler", "toddlers", "baby", "my son", "my daughter",
                 # a friend, a parent or a partner who interrupts is a conversation, not an
                 # open-plan problem: with better-listener standing down, this entry was the
                 # next one along to take "how do i tell my friend she keeps interrupting me"
                 "my friend", "my friends", "friend", "friends", "mate", "mates", "mum", "dad",
                 "mother", "father", "sister", "brother", "wife", "husband", "partner",
                 # a colleague who will not stop interrupting you is that conversation with a
                 # named person, and wording.py's telling row has it: this row keys "five
                 # minutes" and "every", so "how do i tell a colleague to stop interrupting
                 # me" was answered "block the first ninety minutes... wear headphones as the
                 # sign", which is a desk diary for a person who keeps cutting across.
                 "interrupt", "interrupts", "interrupting", "interrupted", "stop interrupting",
                 "phone", "phones", "mobile", "scrolling", "notifications", "instagram",
                 "tiktok", "feel", "feels", "feeling", "felt", "mood", "depressed", "anxious",
                 "anxiety", "stress", "stressed", "burnout", "burnt out", "exhausted", "tired",
                 "cant cope", "can't cope", "workload", "too much work", "too much to do",
                 "lunch", "dinner", "breakfast", "meal", "eat")),
    entry("imposter-feeling",
          (("fraud", "imposter", "impostor", "don't deserve", "dont deserve", "don't belong",
            "dont belong", "faking it", "out of my depth", "they'll find out",
            "theyll find out",
            # The condition by its name was the one way of asking this that matched nothing:
            # "how do i deal with imposter syndrome" and "what is imposter syndrome" were both
            # "That's beyond what I know well" while the description of it had a card all along.
            # The other phrases are how people say it without the word, and "how do i stop
            # feeling like a fraud" is one of them - it went to the scam row, because "fraud"
            # and "how do i" are both in that key.
            "imposter syndrome", "impostor syndrome", "imposter phenomenon",
            "feel like a fraud", "feeling like a fraud", "feel a fraud", "like a fraud",
            "i am a fraud", "im a fraud", "going to get found out", "get found out",
            "they will find out", "not as good as", "everyone else knows what they are doing"),
           ("new role", "senior", "promotion", "promoted", "new job", "normal", "feel", "feeling",
            "work", "job", "should i", "what do i do", "first",
            # how the named condition is asked about, and the everyday tail of it
            "deal", "dealing", "cope", "coping", "stop", "get over", "manage", "what is",
            "whats", "what's", "why", "always", "syndrome", "ruining", "ruins", "hate",
            "struggle", "struggling", "uni", "university", "college", "team", "meeting",
            "meetings", "presenting", "presentation", "clients")),
          ("Feeling like a fraud in a job you were hired for is close to universal, and it is not "
           "evidence of anything: the people around you are guessing too. The antidote is evidence, "
           "not reassurance - keep a running note of what you have actually delivered and looked "
           "up, and read it before a one-to-one. Ask a colleague you trust what they think you "
           "should worry about; their answer will be smaller and more specific than your own."),
          # a scam and a card fraud are the other answers, and a colleague taking credit is its own
          avoid=("scam", "scammed", "card", "bank", "email", "cold call", "took the credit",
                 "being paid", "overpaid")),
    entry("overpaid-at-work",
          (("overpaid", "over payment", "paid too much", "paid me too much", "extra in my pay",
            "paid twice", "paid me twice", "payroll paid", "money in my pay", "extra money in"),
           ("have to", "must i", "do i need", "tell them", "say", "should i", "payroll", "hr",
            "boss", "back", "owed", "keep it", "what do i do", "last month", "this month",
            "just noticed", "found out", "what now", "worried",
            # "i was overpaid at work" names the place and nothing else from this half, and
            # "my employer overpaid me" names the payer instead: whoever pays the wages is the
            # same question, so the payer's name is a word on this side too.
            "work", "job", "my pay", "wages", "employer", "company", "payroll department",
            "payslip", "pay slip", "pay day", "monthly pay")),
          ("Tell payroll in writing today, because money paid by mistake can be taken back "
           "and, if it is a real overpayment, keeping quiet looks like dishonesty later. Say what "
           "you think is wrong and ask for a written breakdown; a genuine overpayment is usually "
           "recovered in agreed instalments, and you can ask for a repayment plan you can afford "
           "rather than a lump sum. Put the money aside until it is sorted, so it never feels like "
           "yours."),
          # an overpayment by the tax office is the rebate's question, not payroll's
          avoid=("hmrc", "tax", "p800", "rebate", "tax code", "child benefit",
                 "universal credit")),
    # "how do i tell my manager i am unhappy" and "i am unhappy at work" both got "Sorry to hear
    # that. A walk and someone to talk to usually help more than sitting with it" - the low-mood
    # first aid, which is the right answer to a feeling and no answer at all to a work problem the
    # person is about to raise. The card is keyed on the state plus the ask, so a bare "i feel low"
    # keeps the mood card.
    entry("unhappy-at-work",
          (("unhappy", "unhappy at work", "unhappy in my job", "miserable", "miserable at work",
            "miserable in my job", "not happy at work", "not happy in my job",
            "dont like my job", "don't like my job", "dont like work", "fed up at work",
            "fed up with work", "sick of my job", "bored at work", "stuck in my job"),
           # the job side of it is the second key word, so "i am unhappy in my relationship" and
           # "i feel miserable" name no job and keep the mood card. "hate my job" and "dread going
           # to work" are left out on purpose: both already have their own answers.
           ("work", "job", "boss", "manager", "management", "colleague", "colleagues", "office",
            "workplace", "shift", "shifts", "rota", "team", "staff", "how", "should", "tell",
            "talk", "say", "mention", "raise", "bring up", "leave", "stay", "quit", "what do i do",
            "help", "meeting", "one to one", "1 to 1", "1:1", "appraisal", "feed back",
            "feedback")),
          ("Ask for a proper one-to-one and name one thing that could be fixed, not the whole "
           "job: \"the mornings are relentless since Jo left - can we look at the rota\" gets an "
           "answer, while \"I'm unhappy\" asks your manager to guess. Take one example and one "
           "request, write down what they agree to, and give it a month. If nothing moves, that is "
           "your answer about whether to stay."),
          # a low mood with no job in it, a pay question and leaving for another offer are each
          # their own answer
          avoid=("pay", "pay rise", "payrise", "salary", "wage", "wages", "money", "offer",
                 "another job", "new job", "resign", "resignation", "notice", "redundancy",
                 "bully", "bullied", "bullying", "harass", "harassed", "harassment",
                 "grievance", "union", "sacked", "fired", "panic", "anxious", "anxiety",
                 "depressed", "depression", "suicidal", "panic attack")),
    entry("say-no-politely",
          (("say no", "saying no", "say yes", "refuse", "turn down", "push back"),
           ("awkward", "weird", "rude", "difficult", "guilty", "guilt", "feel bad",
            "boss", "manager", "colleague", "friend", "family", "invite",
            # how the refusal will land, which is the other half of the same question: "how do
            # i say no without sounding like an excuse" was going to the how-to-end-a-chat card
            # in friends.py, and "how do i say no without a reason" was a shrug.
            # "reason" rather than "no reason": "no" is dropped from the reading, so the
            # phrase never matched and "how do i say no without a reason" stayed a shrug.
            "sounding", "sound like", "sounds like", "without sounding", "excuse", "excuses",
            "reason", "rude", "politely", "polite", "nicely", "gently", "kindly", "badly",
            "let them down", "without hurting",
            # the table, named plainly: "how do i refuse food at someones house" has the verb
            # and nothing else, so the food and the occasion have to be key words too
            "food", "meal", "dinner", "lunch", "supper", "table", "someones house",
            "at someones", "at a friends", "second helping", "helping")),
          _say_no,
          # A child who will not eat their dinner is not a person learning to refuse a second
          # helping politely. This card keys on "refuse" and on the meal, so every line a parent
          # writes about a refusing child reached it - "my 4 year old refuses dinner" was told to
          # keep their refusal to four words and move the attention off themselves. A child or an
          # age in the line stands this row down, and the picky-eater card in family.py answers.
          avoid=("my son", "my daughter", "my child", "my children", "my kid", "my kids",
                 "my boy", "my girl", "toddler", "toddlers", "year old", "year-old", "yearold",
                 "yr old", "nursery", "school dinner", "school dinners")),

    entry("masters-or-job",
          (("masters", "postgrad", "postgraduate", "phd", "further study", "do a degree"),
           ("job", "work", "career", "should i", "worth it", "worth the money",
            "worth the cost", "worth the debt", "decide", "instead")),
          "Check five job adverts for the role you want: if a master's is not listed as essential, "
          "a year in the job usually teaches more and costs less, and you can do the master's "
          "later, often with an employer paying part of it. Do it now if the career you want needs "
          "it to enter at all - teaching, law, clinical roles - or if you want the research year "
          "for its own sake."),

    # --- starting and leaving -------------------------------------------
    entry("first-day",
          (("first day", "new job", "starting a new job", "start on monday", "starting monday",
            "new role", "new starter", "im new here", "i'm new here", "started this week",
            "started last week",
            # the same job said without "new": "im starting a job on monday, any advice" was
            # the two-offers card and "i start my job next week, what should i expect" was the
            # maternity-rights card, because "expect" reads as "expecting". A job that has not
            # begun yet is the first day whatever adjective is in front of it.
            "starting a job", "start my job", "starts my job", "starting my job",
            "start a job", "starts a job", "start work", "starting work", "job starts",
            "starts next week", "starts on monday", "starts tomorrow", "job on monday"),
           ("nervous", "wear", "bring", "tips", "expect", "what to", "worried", "first week",
            "feel lost", "lost", "settle", "overwhelmed", "dont know anyone",
            # "how do i prepare for my first day" was a shrug: getting ready for it is the same
            # question as what to bring, so the act joins the ask group
            "prepare", "preparing", "prepared", "get ready", "getting ready", "before i start",
            # and so is the other half of a first day - what to ask once you are in the room
            # ("what do i ask on the first day" was a shrug). As a phrase, not the bare word:
            # "ask" alone took "what should i ask my boss about the new role" off its own
            # answer and gave it the day-one packing list.
            "ask on my first day", "ask on the first day", "what to ask",
            "questions to ask", "first day questions", "ask questions",
            "questions on my first day", "questions on the first day",
            "questions for my first day", "ask my new team",
            "ask my new boss", "ask my new manager", "ask my team",
            # "im starting a new job monday, any advice" named the job and asked for advice, and
            # the only advice word in the group was "tips" - the line went to the kitchen's
            # announcement row instead (it keys "starting") and was answered by nothing.
            "advice", "any advice", "some advice", "any tips", "advice for")),
          _first_day,
          # a job that has already gone wrong is the hated-job question, not the notebook one:
          # "my new job is not what i expected" was getting the day-one packing list
          avoid=("school", "nursery", "university", "college", "term", "exam", "reception",
                 "hate", "hated", "quit", "quitting", "not what i expected",
                 "not what i thought",
                 # "how do i settle into a new job" is the first month, not the day-one list:
                 # the notebook and the ID belong to a person who has not walked in yet, and
                 # new-job-friends answers the person already in the room.
                 "settle into", "settling into")),

    entry("probation",
          (("probation", "probationary", "probation period", "on probation",
            # "how long is a trial period at work" was answered with the length of a menstrual
            # cycle, then with a subscription cancellation. A trial period at work is probation.
            "trial period", "trial period at work", "trial shift", "trial shift at work"),
           # "im on probation at work" carries no question word, so the work itself has to open
           # the gate: someone who says only that is asking what it means for them.
           ("worried", "fail", "extend", "extended", "extension", "nervous", "how",
            "end", "passed", "sack", "sacked", "dismiss", "dismissed", "keep me on",
            "at work", "work", "job", "started", "what happens", "how long",
            # "what is a probation period" is a definition question and had no ask word
            "what is", "what does", "whats a", "what's a", "mean", "means", "meaning",
            "explain")),
          "However long your contract says - three to six months is usual - probation is a check "
          "that you turn up and learn, so do the plain things well: on "
          "time, ask early when unsure, and flag anything that slips before it slips. Ask your "
          "manager in week four what would make it a clear yes, then do exactly that. The notice "
          "during probation is usually shorter than after it, and it is in your contract; an "
          "extension should come with a reason and a date, so ask for both in writing. If it ends, "
          "ask why in an email - a no for a reason you can fix is worth more than a shrug.",
          # "probation" is also what a court gives somebody: "my son is on probation for
          # fighting" and "what happens if you break probation" are not a job question.
          avoid=("court", "police", "breach", "break probation", "broke probation",
                 "offence", "offense", "curfew", "tagged", "prison", "jail", "sentence")),

    entry("resigning",
          # A job has to be named. Bare "quit" also means smoking, sugar, drinking and the gym,
          # and every one of those was getting four weeks' notice.
          (("resign", "resignation", "resign from", "quit my job", "quitting my job",
            "quit this job", "quit work", "leave my job", "leaving my job",
            "hand in my notice", "handing in my notice", "tell my boss i'm leaving",
            "telling my boss i'm leaving",
            # the same sentence typed without the apostrophe, and with the reason in it: "how do
            # i tell my boss im leaving for another job" fell to the second-job tax answer
            "tell my boss im leaving", "tell my manager im leaving",
            "tell my boss im quitting", "tell my manager im quitting",
            "leaving for another job", "leaving for a new job",
            # "different ways to say i quit politely" was the chat nod: the words were all about
            # the saying, and every one of the key's phrases named the job instead
            "say i quit", "saying i quit", "say i'm quitting", "say im quitting",
            "way to say i quit", "ways to say i quit", "how to say i quit",
            "quit politely", "quitting politely", "resign politely", "resigning politely",
            "quit nicely", "quitting nicely", "resign nicely"),
           ("how", "letter", "boss", "tell", "write", "manager", "what should i do",
            "what do i do", "tell my boss i'm leaving",
            # "what do i say when i resign" was a shrug: the words are the same ask as the how.
            # `telling-home-about-the-job` keys this phrase too, and it wants a partner or a
            # parent beside it, so the person's own resignation stays here.
            "what do i say", "what should i say", "what to say", "say to my",
            # a statement-shaped ask about the wording: "different ways to say i quit politely"
            "ways to", "way to", "different ways")),
          # "how much notice do I give" is the notice entry's job, not the letter's
          "Tell your manager first, in person or on a call, and keep it short: \"I've decided to "
          "move on. I'd like to give you four weeks' notice from today.\" Then hand over one "
          "written paragraph with your last day in it. You never have to say why, and it is rarely "
          "worth it.",
          # the person they are asking about telling first is their partner or family, not work
          avoid=("partner", "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee",
                 "my mum", "my dad", "my parents", "my friend", "my kids", "my children",
                 "my fiance", "my fiancé", "the kids",
                 "how much notice", "how long is my notice", "notice period", "work my notice",
                 "garden leave")),

    entry("someone-close-quitting",
          (("partner", "husband", "wife", "boyfriend", "girlfriend", "fiance", "fiancee",
            "friend", "mum", "dad", "son", "daughter", "brother", "sister"),
           # The second part has to name work. A bare "quit" made this entry answer "my mum
           # wants to quit smoking" and "my son wants to quit football" with a speech about
           # the boss and the drop in pay, which invents a job nobody mentioned.
           ("quit their job", "quit her job", "quit his job", "quit the job",
            "quitting their job", "quitting her job", "quitting his job",
            "resign", "resigning", "resigned", "resignation",
            "handed in her notice", "handed in his notice", "handed in their notice",
            "notice in", "wants to leave their job", "wants to leave her job",
            "wants to leave his job", "leaving the job", "leaving her job", "leaving his job",
            "leave their job", "leave her job", "leave his job")),
          "Ask what is actually wrong with the job first - the boss, the hours or the work itself - "
          "because each one wants a different answer. Then do the money on paper together: what "
          "the drop in pay is, how many months you could both cover, and what they would do next. "
          "Say your worry once, plainly, and let the decision be theirs; being the one who listened "
          "counts for more than being right.",
          # a notice period or a letter is a how-to for the person leaving, not for their partner
          ask=("my", "his", "her", "their"),
          # "how do i tell my partner i want to quit" is the speaker leaving, not the partner
          avoid=("i want to quit", "i want to leave", "i've decided", "i have decided",
                 "i'm going to quit", "im going to quit", "i am going to quit", "how do i tell",
                 "should i quit", "should i resign")),

    # The other side of the same conversation: the person leaving has to say it at home first.
    # "how do i tell my partner i want to quit my job" passed on every entry - the letter is for
    # the boss, and someone-close-quitting answers the person being told, not the one telling.
    # "how do i stop taking work home" was a shrug, and it is the commonest work question of the
    # evening.
    entry("work-home-boundaries", (("work", "job", "office", "emails", "laptop"),
                                   ("take work home", "taking work home", "bring work home",
                                    "bring my work home", "switch off from work",
                                    "switch off after work", "stop thinking about work",
                                    "thinking about work", "work in the evening",
                                    # the shift shapes are statements of a rota, not a wish to
                                    # stop: "i work at night" is a night-shift worker talking
                                    # the keys carry the verb: "working at night" alone matches
                                    # a night-shift rota, because forms turn "work" into "working"
                                    "stop working at night", "stop working at weekends",
                                    "stop working at the weekend", "stop working evenings",
                                    "leave work at work",
                                    "cant switch off from work",
                                    "can't switch off from work")),
          "End the day with a two-minute shutdown: write tomorrow's first three things on one "
          "list, close the laptop, and do something that marks the change - a walk round the "
          "block, changing clothes, the kettle. Keep work email off your phone after a set hour "
          "unless you are genuinely on call, and tell people the hour rather than just going "
          "quiet. If the work does not fit the day, that is a conversation with your manager "
          "about what to drop, not a longer evening.",
          # a broken laptop or a work laptop question is technology's, and the sleep entries own
          # lying awake with a racing mind
          avoid=("laptop broken", "laptop slow", "laptop wont", "laptop won't", "screen",
                 "battery", "wifi", "vpn", "remote desktop", "overtime pay", "unpaid")),

    entry("telling-home-about-the-job",
          (("quit my job", "quitting my job", "leave my job", "leaving my job", "lost my job",
            "made redundant", "been sacked", "being let go", "want to change jobs",
            "got a new job", "got offered a job", "i got the job",
            # "going back to study" keeps its place: telling the family is the row's line, and
            # taking it out left "how do i tell my mum i'm going back to study" with no entry.
            # "going part time" left, because it is the ask to the manager (flexible-hours) and
            # keeping it here answered "what do i say to my boss about going part time" with the
            # leaving script ("I've decided to leave my job").
            "going back to study"),
           # The people at home are not the cue: `my mum` on its own is who the news concerns,
           # so "i lost my job and my mum is ill" was answered with this script, which is the
           # conversation you have *with* her, not about her. What makes it this row is the
           # talking - tell, say, bring it up, break it, and the fact that they do not know yet.
           ("tell", "how do i say", "what do i say", "bring it up", "break it to",
            "doesnt know", "does not know", "says")),
          "Pick a calm moment, not the moment it happens, and lead with the decision and the "
          "plan: \"I've decided to leave my job. I've worked out the money and here is what I "
          "suggest.\" Then let them react without defending yourself - the first reaction is "
          "almost always about money, so have a number ready and say what you would do if it is "
          "tight. If it is bad news rather than a choice, say what happened in one plain "
          "sentence and ask for one thing: \"I was let go today. I don't want to solve it "
          "tonight, I just need you to know.\"",
          # the row is for the people at home: a line that names the boss or the team is the ask
          # to the manager, not the conversation in the kitchen.
          avoid=("landlord", "tenancy", "divorce", "pregnant", "pregnancy", "visa", "school run",
                 "my boss", "boss", "my manager", "manager", "at work", "in work", "to my team",
                 "my team", "hr", "colleagues", "my colleague")),

    entry("notice-period",
          # garden leave keeps its own row: holding the phrase here answered "what is garden
          # leave" with the length of a notice period
          (("notice period", "how much notice", "weeks notice", "months notice",
            "notice i get", "work my notice",
            "working my notice", "work out my notice", "serve my notice", "work the notice",
            "my notice period", "pay in lieu",
            # "my contract says i have to give 3 months notice" named the notice without any of
            # the phrases above, and `cancel-gym` took it (it keys "contract" and "notice").
            "months notice", "month notice", "weeks notice", "week notice",
            "months' notice", "three months notice", "contract says i have to give",
            # "can i get payment in lieu of notice" said the whole clause and matched none of
            # it: "pay in lieu" is not inside "payment in lieu".
            "payment in lieu", "lieu of notice", "in lieu",
            # the adjective that "work my notice" cannot see past: "my full notice", "the whole
            # notice", "my notice in full", "work all my notice"
            "my full notice", "full notice", "the full notice", "whole notice", "entire notice",
            "all my notice", "notice in full", "work my full", "serve my full",
            # and the other end of it: leaving before the notice has run out
            "notice is up", "before my notice", "before my notice is up", "stop me leaving",
            "leave before my notice",
            # "i handed my notice in, how long do i have to work" is the length question said
            # after the fact, and the letter that says what to write took it: the handing-in
            # phrasings belong to the row that answers the period.
            "handed my notice", "handed in my notice", "hand my notice in",
            "handing in my notice", "handed in notice", "given my notice", "gave my notice"),
           ("how long", "work", "leave", "contract", "boss", "give", "serve", "resign",
            "months", "weeks", "month", "week", "is it", "i can", "can i", "get", "paid",
            "what is", "change", "make me",
            "do i have to", "must i", "can they", "they make", "stop me", "before",
            # "notice period rules" and "what does it mean" carry the ask and no other word in
            # the row does: both were a "Thanks for telling me".
            "rules", "mean", "means", "meaning",
            # shortening it is asked as "reduce", "shorten" or "get out of"
            "how do i", "reduce", "shorten", "get out of", "cut short",
            "how long do i have to work", "how long do i have to stay",
            "how long do i need to work", "how long must i work")),
          # The card used to open with "your contract decides it", which is not the answer to
          # "can they make me work my full notice"; `_notice_reply` opens with the yes for that
          # shape and with the length for "how much notice".
          _notice_reply,
          # "can my boss make me work my notice period" was reaching the resignation letter,
          # which keys the bare word "notice". Naming the notice in this key is not enough on
          # its own: this one is the answer whenever the line is about serving it.
          bias=3,
          # "can i take holiday during my notice period" is the holiday row's question, and
          # "notice"/"during my notice" gave this row the win: the notice card answers the length
          # and the serving, not the leave.
          avoid=("holiday", "holidays", "annual leave", "time off",
                 "tenancy", "tenant", "landlord", "flat", "rent", "lease", "eviction", "deposit",
                 "letting", "quit the tenancy", "quit the lease", "end my tenancy",
                 "notice to quit", "break the lease",
                 # "my gym contract says i have to give a month notice" is a membership's
                 # cancellation, not a job: the notice in a contract also belongs to a gym, a
                 # club, a phone and a broadband line
                 "gym", "gyms", "membership", "health club", "leisure centre",
                 "phone contract", "mobile contract", "broadband", "phone", "mobile",
                 # "how do i hand in my notice without burning bridges" is asking what to write,
                 # which is the resignation letter's answer, not how long the notice is
                 "burning bridges", "burn bridges", "without burning", "how do i hand",
                 "how to hand in", "how do i resign", "resignation letter", "letter")),

    # "what should i do if i lose my job" and "i lost my job what do i do" were a shrug and a
    # "That sounds rough", on the one day somebody needs a list rather than sympathy, so the
    # ways of saying it are in the key beside the redundancy words.
    entry("redundancy",
          (("redundant", "redundancy", "laid off", "being let go", "losing my job",
            # the way most people say it: "i lost my job what do i do" was a shrug on main
            "lost my job", "lose my job", "job gone", "jobs gone", "let go",
            "made redundant", "being made redundant", "at risk of redundancy",
            # The same day said without the word "job": "im unemployed and have no savings" is
            # the redundancy question too, and a row that stands the savings card down for a job
            # loss leaves a person with an "okay" if this card does not name how they said it.
            # "fired" stays out bare, since the language also fires clay, a barbecue and an
            # employee, and the stem reaches all three.
            "unemployed", "unemployment", "jobseekers", "job seekers", "out of work",
            "no job", "between jobs", "sacked", "got fired", "was fired", "been fired",
            "got the sack", "given the sack", "the dole"),
           ("what do i do", "what should i do", "what now", "now what", "rights", "next",
            "money", "worried", "just been", "just lost", "help", "pay", "week", "month",
            "today", "yesterday", "just", "now", "should", "do", "can", "scared", "anxious",
            "email", "letter", "advice",
            # the statement with no question in it is still the ask: "i have lost my job" said
            # nothing else, so no ask word matched and it got "That sounds rough" while "i lost
            # my job what do i do" got this answer. The key already holds the job phrases, so
            # this phrase can only be read on a line that already names the job.
            "have lost",
            # "i got made redundant" with nothing after it is the person saying what happened,
            # in the past tense that says it, and it was a "Ugh, that's a lot to carry" on main
            # while "i got made redundant yesterday" was answered: the event's own verb is what
            # the second part was missing, not the question.
            "got", "was", "were", "been", "i got", "i was", "i have", "they made", "made me",
            "im", "i am", "being")),
          # Someone who says "i lost my job yesterday" is having the worst week of their year, and
          # the list below is the right thing to say only after "sorry". The list itself is why
          # this entry exists ("that sounds rough" was all main had), so the answer stays, opened
          # warmly, and it reads as well on "what do i do if i am made redundant".
          "Sorry - that is a rough one. Ask for the offer in writing and don't sign it on the day: "
          "check the redundancy pay, the notice, and any holiday you are owed. Ask whether the role is really going - if it is "
          "not, or the process was unfair, a free service like ACAS or Citizens Advice will tell "
          "you where you stand. Then ask for a reference and tell your network, because most jobs "
          "arrive through people.",
          # "made" and "make" used to be here bare, which blocked every "being made redundant"
          # line - the commonest way people say it. The phrases keep the boiler and the cake out
          # without swallowing the question.
          avoid=("boiler", "car", "engine", "cake", "make a", "making a", "made a", "makes a",
                 "how do i make", "how to make", "make my", "make the",
                 # What it is worth is `redundancy-pay`'s question, and that row wins on its
                 # own once it names the event: only the asks whose answer is a figure and
                 # whose words the pay row does not also carry are fenced off here. A fence on
                 # "what do i get" alone sent "what do i get if i get sacked" to a shrug, since
                 # no row names a sack but this one.
                 "entitled to anything", "am i owed", "what am i owed", "what am i due",
                 # a job lost years ago is a story, not the offer on the table today: the list
                 # below is "do not sign it on the day", which has already happened.
                 "last year", "years ago", "a year ago", "years back", "long ago",
                 # What it is worth is `redundancy-pay`'s question, and the past-tense verbs
                 # above ("been", "was", "got") widened this row enough to take it: "ive been
                 # there 6 years" a turn after "im being made redundant" was answered "Same as
                 # before: ..." instead of the statutory figure, because "redundant ive been
                 # there 6 years" reached this row first.
                 "how much", "entitled", "how many years", "years of service", "years there",
                 "service", "what am i due", "what am i owed", "how much will i get",
                 "statutory", "redundancy pay", "severance", "package", "payout", "pay out",
                 "calculate",
                 # Somebody else's redundancy is not your next step: "my best friend got made
                 # redundant on friday" was told to "ask for the offer in writing and don't sign
                 # it on the day" - the friend's problem answered at the wrong person.
                 "my friend", "my best friend", "a friend", "my husband", "my wife",
                 "my partner", "my mum", "my dad", "my son", "my daughter", "my brother",
                 "my sister", "my colleague", "a colleague", "someone at work", "he got",
                 "she got", "he was", "she was", "he has been", "she has been", "his job",
                 "her job", "their job",
                 # A job that has ended is not the only sense of "was fired": "the crowd was
                 # fired up" and "i got fired up in the meeting and said too much" hold the
                 # key's own phrases as words, so both were told to "ask for the offer in
                 # writing and don't sign it on the day". The word that changes the sense is
                 # the one after it, so the fence names the phrase and not the verb.
                 "fired up", "fired-up")),

    # Somebody else cut the hours. This is the mirror of flexible-hours, which is you asking to
    # go part time: "my hours got cut at work can they do that" was a shrug, "my boss has cut my
    # hours without asking me" got the how-to-ask-for-flexible-working reply, and "they are only
    # giving me 20 hours a week now instead of 40" got the exercise card, because "20 hours a
    # week" is how you describe a workout. The phrases name the employer as the one doing it, so
    # "i want to cut my hours" stays with the request.
    entry("hours-cut",
          (("hours got cut", "hours have been cut", "hours were cut", "hours got reduced",
            "got my hours cut", "cut my hours", "cutting my hours", "cut back my hours",
            "cut my shifts", "cut my days", "cut my overtime",
            "reduced my hours", "reducing my hours", "reduce my hours", "slashed my hours",
            "has cut", "have cut", "keeps cutting", "cut to two", "cut to three", "cut to one",
            "put on short time", "short time at work", "short-time working", "laid off for a week",
            "no shifts", "no hours", "no work for me",
            # not bare "sent home": being sent home for being late is a different thing
            "sent home without pay", "sent home because there is no work",
            "only giving me", "only gave me", "only getting", "instead of 40", "instead of 37",
            "fewer shifts", "fewer hours",
            # the passive shape people use: "my shifts keep getting cut", "the hours get cut"
            "getting cut", "gets cut", "keep getting cut",
            "overtime cut", "overtime has been cut", "overtime got cut",
            "hours are being cut", "hours being cut", "hours will be cut"),
           ("work", "job", "boss", "employer", "manager", "contract", "shifts", "shift", "rota",
            "hours", "company", "week", "paid")),
          "Look at the contract first: if it guarantees your hours, a permanent cut is a change to "
          "your terms, so put your objection in writing and carry on working as before while you "
          "sort it out - ACAS (0300 123 1100) is free and will tell you where you stand. If it says "
          "the hours vary, short-time working is allowed, but ask for guarantee pay: a day's pay for "
          "each day you are laid off, up to five days in three months.",
          # the request to go part time, and the rota question, are their own entries
          avoid=("want to", "i would like", "can i ask", "ask for", "ask to", "request", "apply",
                 "thinking of", "thinking about", "considering",
                 # the same words the other way round: "how do i reduce my hours" and "can i cut
                 # my hours to three days" are you choosing to work less, and flexible-hours
                 # answers them. The cut in this entry is the employer's, so the question shape
                 # ("how do i", "can i", "could i") in front of the verb is what says which it is -
                 # dropping the verb would lose "can my employer reduce my hours"
                 "how do i reduce", "how do i cut", "how can i reduce", "how can i cut",
                 "can i reduce", "can i cut", "could i reduce", "could i cut",
                 "can we reduce", "could we reduce", "any way i can", "is there a way",
                 "ways to cut", "ways to reduce",
                 # people put the person in the middle of the ask, so "ask for" and "ask to"
                 # never matched "how do i ask my boss for fewer hours" - the plainest way of
                 # asking for it - and the employer's answer was given to the person doing the
                 # asking. These are the shapes with someone between the verb and the thing.
                 "ask my", "ask the", "ask her", "ask him", "ask them", "asking my",
                 "how do i ask", "how to ask", "how can i ask", "asked my", "asked for",
                 "asked to", "asking for", "asking to",
                 # NOT "asked me": the word forms reach "asking", so it took "my boss has cut
                 # my hours without asking me" - the employer's direction, which is this
                 # entry's. The first person alone is not enough to stand this entry down:
                 # "i cut my hours last month so i could study" was the study card, and nothing
                 # here answers "i reduced my hours to study" or "i have cut my hours to 3
                 # days", so the person's own past decision keeps the contract answer.
                 "flexible working", "annual leave", "holiday", "sick", "sickness",
                 # "i only get 5 hours sleep a night" is a sleep question, and the sleep entry
                 # answers it - with "hours" and "a night" in it, this entry read "only get
                 # hours" as an employer cutting them and gave a contract-and-ACAS card to
                 # somebody asking about a short night. "i get about 5 hours" already reaches
                 # the right entry, so only the shapes with "only" were lost.
                 "sleep", "sleeping", "slept", "nap", "naps", "in bed", "bedtime",
                 # "a night" but not "at night": "they cut my hours at night" is the
                 # employer's cut and this entry's own case, which a bare "at night" took.
                 "a night", "nights sleep", "insomnia", "waking",
                 # a zero-hours contract has its own answer that says what the contract means
                 "zero hours", "zero-hours"),
          bias=1),

    # --- the boss and the team ------------------------------------------
    entry("boss-too-much",
          # People say what is happening to them far more often than who is doing it: "extra work
          # dumped on me", "two people's jobs", "i cant keep up". So the subject can be the work
          # itself, not only a boss or a manager.
          (("boss", "manager", "workload", "plate", "line manager", "my work", "the work",
            "extra work", "more work", "two jobs", "two people", "two people's",
            "people's jobs", "peoples jobs", "two roles", "overtime", "my hours"),
           ("too much", "overloaded", "swamped", "piling", "stretched", "prioritise", "say no",
            "juggling", "drowning", "last minute", "last-minute", "dumping", "dumps",
            "keeps giving", "keeps asking", "keeps adding", "end of the day", "5pm", "out of hours",
            # the workload brought up in a sentence about what to say, rather than complained of:
            # "what should i say to my boss about the workload"
            "what should i say", "what do i say", "what to say", "bring it up", "raise it",
            "talk to", "tell",
            "extra work", "keep up", "keep on top", "push back", "pushing back", "picked up",
            "picking up", "paid for one", "getting paid", "one salary")),
          "Ask for fifteen minutes and bring the list: \"I have these five things due; I can do "
          "three properly this week - which matter most?\" That hands your boss a decision instead "
          "of a complaint, and it makes the trade-off visible. Send a short email afterwards "
          "confirming what you agreed, so it is on record.",
          # "at the last minute" is what brings this entry to a one-to-one that keeps being moved,
          # and the ask is different: that one wants a slot that holds, not a shorter list.
          avoid=("one to one", "one to ones", "one-to-one", "one-to-ones", "1:1", "1-2-1",
                 "catch up", "catch-up", "review meeting", "appraisal",
                 # whether weekends or seven days are owed is weekend-working's question, and
                 # "my boss keeps asking me to work weekends" was reaching this answer through
                 # "keeps asking"
                 "weekend", "weekends", "saturday", "saturdays", "sunday", "sundays",
                 "7 days", "seven days",
                 # "my work" also means housework, coursework and the work of raising children:
                 # those are not a workload complaint to take to a manager.
                 "housework", "cleaning", "laundry", "washing up", "ironing", "garden",
                 "coursework", "revision", "thesis", "dissertation", "essay", "kids",
                 "children", "toddler", "baby", "house",
                 # A question about overtime pay, the law or the contract is a different answer,
                 # and so is how to turn a shift down: those rules would otherwise be lost to
                 # this one, which is advice about a workload that is already too big.
                 "paid overtime", "overtime pay", "overtime rate", "overtime money",
                 "get paid for overtime", "paid for overtime", "do i get paid", "am i entitled",
                 "entitled to", "legal", "illegal", "the law", "contract", "rights",
                 "refuse", "refusing", "turned down", "turn down", "say no to overtime",
                 "stay late", "work late", "every day", "on call")),

    entry("boss-silent",
          (("boss", "manager", "line manager", "supervisor", "employer", "hr", "head office",
            # The silence is the same problem when the person is a peer: "my colleague keeps
            # ignoring my emails" got the inbox-volume card and then the chat's acknowledgement,
            # and the answer below (ask twice in writing, then copy somebody above) is what a
            # colleague needs too. "client" and "supplier" are left out on purpose - those are
            # chasing money and belong to their own rows.
            "colleague", "colleagues", "coworker", "co-worker", "co worker", "workmate",
            "workmates", "team member", "teammate", "teammates"),
           ("replies", "reply", "responds", "respond", "ignores", "ignored", "ignoring",
            "silence", "unanswered", "unresponsive", "ghosting", "ghosts", "chased", "chasing",
            "never answers", "not answering", "no answer", "no reply", "no response",
            "nothing back", "gets back to me", "get back to me", "never comes back",
            # the same silence said the other way round: "wont answer" and "isnt replying" are
            # how most people write it, and without them the line fell to the interview
            # follow-up note because the words "reply" and "email" were both in it.
            "wont reply", "won't reply", "wont respond", "won't respond", "wont answer",
            "won't answer", "doesnt reply", "doesn't reply", "dont reply", "don't reply",
            "not replying", "isnt answering", "isn't answering", "isnt replying",
            "isn't replying", "stopped replying", "stopped answering", "hasnt replied",
            "hasn't replied", "hasnt got back", "hasn't got back", "wont get back",
            "never replies", "never responded", "doesnt answer", "doesn't answer",
            "dont answer", "don't answer", "never answered", "not answered",
            "heard nothing", "heard nothing back", "heard back", "no word", "no word back",
            "asked twice",
            # the wording that was losing to the interview thank-you note
            "replies to my emails", "reply to my emails", "answers my emails",
            "ignores my emails", "emails me", "my emails",
            # the silence is not always about a message: "my boss never talks to me" is the same
            # problem and it was only an acknowledgement before
            "never talks", "never speaks", "doesnt talk", "doesn't talk", "not talking to me",
            "talks to me", "talk to me", "speaks to me", "wont talk", "won't talk",
            "barely speaks", "barely talks", "no communication", "doesnt communicate",
            "doesn't communicate")),          "Ask twice in writing, then copy one person above, and make it dated: that is what "
          "gets a reply. Send the question again as one email with a single ask and a deadline: "
          "\"I need the rota signed off by Thursday - can you do it, or tell me what is blocking "
          "it?\" If nothing comes back in three working days, forward that email to your boss's "
          "manager or to HR with one line: \"I have asked twice and I need this by Friday, can "
          "you help?\" Keep a short note of what you sent and when, because a list of dates is "
          "what gets acted on if it has to go further.",
          avoid=("resign", "quit", "quitting", "fired", "sacked", "dismissed", "redundancy",
                 "interview", "salary", "pay rise", "payrise", "promotion", "appraisal",
                 "cv", "application", "applications", "job hunting", "notice period",
                 "rota for", "annual leave", "holiday", "sick", "sickness", "bullying",
                 "harassment", "union",
                 # a rota being moved is the shift entry's, not a message gone unanswered
                 "shift", "shifts", "rota", "schedule", "timesheet")),

    entry("shifts-changed",
          # "my hours were changed on me" and "moved onto nights without asking" are the same
          # complaint as a moved rota, and they name the thing moved without the word shift.
          # "my hours were changed on me" and "moved onto nights without asking" are the same
          # complaint as a moved rota, and they name the thing moved without the word shift. The
          # words are kept as the phrases that name a rota ("my hours", "onto nights") rather than
          # as bare `days` and `nights`, which are the time of day in every other line ("my boss
          # hovers over me all day", "say no to overtime every day").
          (ROTA_WORDS,
           ROTA_CHANGE_WORDS),
          _shift_changed_reply,
          # A rota being moved is this entry's own line, and wording's resignation letter reads
          # "notice" in "at short notice": the nudge keeps the shift answer on top.
          bias=1,
          # a changed rota is not a resignation, and not a sleep question
          avoid=("resign", "resignation", "notice period", "quit", "quitting", "leaving my job",
                 # an extra shift they are being asked to take is not a rota moved on them: the
                 # refusal script in overtime-say-no is the answer, and this entry was taking
                 # those lines on its own "refuse" and "say no" words
                 "extra shift", "extra shifts", "cover a shift", "cover shifts",
                 "cover for someone", "pick up a shift", "pick up shifts", "overtime",
                 "extra hours",
                 "sleep", "tired", "exhausted", "insomnia", "jet lag", "overtime pay",
                 "minimum wage", "sick note",
                 # and it is not a change they chose: "i changed shift so i can do the school
                 # run" is how someone says a thing about their week, not a complaint about a
                 # rota being moved on them
                 "i changed", "i've changed", "ive changed", "i swapped", "i switched",
                 "changed my shift myself", "asked to change", "asked for a change",
                 "i asked to swap", "i asked for",
                 # nor one they are asking for: "i want to change my hours to part time" and
                 # "can i ask to change my hours" are the flex-work request, which says how to
                 # put it in writing, not the advice for a rota moved on them
                 "want to change", "want to swap", "want to move", "would like to change",
                 "like to change", "ask to change", "can i ask", "request to change",
                 "requested a change", "request a change", "flexible working",
                 # and a request for fewer hours is the same request, however the person puts
                 # the ask: "how do i ask my boss for fewer hours" is the flex-work card's, and
                 # "hours" + "boss" was enough for this row to take it
                 "fewer hours", "fewer shifts", "less hours",
                 # the first-person request, not the bare verb: "cut my hours" alone is the
                 # employer's cut as well ("my boss wants to cut my hours"), and standing the
                 # rota card down for it handed that line to the flex-work card - the same fault
                 # the employer direction of hours-cut had, running the other way.
                 "can i cut my hours", "could i cut my hours", "i want to cut my hours",
                 "i want to reduce my hours", "how do i cut my hours", "cut my own hours",
                 "reduce my own hours", "cut my own shifts",
                 "part time", "part-time",
                 # a flexible-hours request is the flex-work card's, whichever way it is worded:
                 # "how do i ask my boss for flexible hours" has the word "hours" and the word
                 # "boss", which is all this row needed, and the person asking to change their
                 # hours was told what to do about a rota moved on them.
                 "flexible", "flexible hours", "flexible working",
                 # an hours question is the pay-and-hours entry's: "can my employer change my
                 # hours", "can they reduce my hours to zero", "unpaid leave" ask what is allowed,
                 # not what to do about a rota that has already moved
                 "employer change", "employer cut", "reduce my hours", "my hours be", "to zero",
                 "zero hours", "unpaid leave", "can they make me", "is it legal")),

    entry("colleague-credit",
          # The person who takes the credit is a colleague, a boss or "someone else": the answer
          # is the same one, so the entry is keyed by the taking and not by the word for the person.
          (("colleague", "coworker", "co-worker", "teammate", "team mate", "workmate",
            "boss", "manager", "team lead", "team leader", "supervisor", "someone else",
            "somebody else", "another lad", "another guy",
            # The same person with the words people write: "my fella keeps taking credit for my
            # ideas" and "theres this bloke who keeps taking credit for my ideas" are the same
            # question as "a colleague", and both were answered by another row entirely - the
            # falls card for an elderly parent, because "fella" and "bloke" were read as "fell"
            # and "broke" (`bot/knowledge/lookup.py`, `_engine_reads`).
            "fella", "fellas", "bloke", "blokes", "lad", "lads", "guy", "guys",
            "mate", "someone", "somebody", "person", "flatmate", "housemate", "partner",
            # The place is a person marker when the person is named: "kate at work keeps taking
            # the credit for my work" names nobody the row can hold, and the room does the work.
            "at work", "in the office"),
           # A taking, not a bare "credit" and not "my work": "my boss is happy with my work" and
           # "my boss gave me credit for the report" are praise, and the person group is now wide
           # enough (boss, manager, supervisor) that bare praise would land here.
           ("took the credit", "takes the credit", "taking the credit", "took credit",
            "takes credit", "taking credit", "took credit for", "gets credit for",
            "got credit for", "claimed the credit", "claimed credit", "claimed my",
            "claims my", "got the credit", "got credit", "gets credit", "stole the credit",
            "stole my", "steals my", "steals the", "stolen my", "stolen", "my idea",
            "my ideas", "as his own", "as her own", "as if it was his", "as if it was hers",
            "as if it were his", "as if it were hers", "presented my", "read out my",
            "his name on my", "her name on my", "passed off as")),
          "Claim it in the room, lightly and factually: \"As I put in Tuesday's note, the plan "
          "is...\". If it keeps happening, one private sentence does more than a meeting fight: "
          "\"When you presented that, it would help me if you said it came from me.\" Then put your "
          "ideas in writing and copy in whoever decides.",
          # praise is not theft, and money credit is not credit for the work
          avoid=("said my", "says my", "gave me credit", "gives me credit",
                 "happy with my work", "pleased with my work",
                 "credit card", "credit score", "credit rating", "credit check", "credit note",
                 "course credit", "tax credit", "store credit", "on credit", "credit limit",
                 # a thing taken from a doorstep, a bike rack or a van is not an idea taken in a
                 # meeting: "someone stole my parcel" and "someone stole my phone at the pub"
                 # were told to claim it in the room, on "someone" and "stole my". Theft of a
                 # thing has its own answer in lifeadmin, and this row is about work.
                 "parcel", "parcels", "package", "packages", "phone", "mobile", "iphone",
                 "laptop", "bike", "bicycle", "tools", "wallet", "purse", "bag", "bags",
                 "watch", "jewellery", "jewelry", "drill", "van", "boot", "doorstep",
                 "at the pub", "in the pub", "from my house", "from my flat", "from my car")),

    entry("difficult-colleague",
          (("colleague", "coworker", "co-worker", "boss", "manager", "team",
             "at work", "someone at work",
             # "my teammate keeps talking over me" and "my workmate keeps talking over me" were
             # both "Ask about the answer you just got instead of starting a new subject": the
             # person was in the row's key and the way they are named was not.
             "teammate", "teammates", "team mate", "team mates", "workmate", "workmates",
             "someone on my team", "one of my team"),
           # the same person named as a noun: "how do i deal with a toxic coworker" has no
           # behaviour word in it and was a shrug on main
           ("difficult", "is difficult", "being difficult", "really difficult",
            "difficult colleague", "difficult coworker", "difficult co-worker", "difficult boss",
            "difficult manager", "awkward colleague", "awkward coworker", "annoying colleague",
            "annoying coworker", "toxic colleague", "toxic coworker", "toxic co-worker",
            "toxic boss", "toxic manager", "rude",
            "rude to me", "someone at work", "unkind", "mean to me", "undermines",
            "picks on", "clash", "clashes", "conflict", "argument", "snaps", "ignores me",
            "talks over me", "talks over", "talk over me", "talking over me", "talked over me",
            # "my teammate keeps interrupting me in meetings" was a calendar answer about
            # blocking out focus time, because "interrupting" is the open-plan row's word and it
            # stands itself down for it: a named person doing it is this row's line.
            "interrupting me", "interrupt me", "interrupted me", "keeps interrupting",
            "cuts across me", "cutting across me", "cuts across",
            "belittles", "raise a concern", "raise my concern",
            # the same behaviour with the words people actually use for it
            "passive aggressive", "passive-aggressive", "sarcastic", "snippy", "snide",
            "cold shoulder", "cold shouldering", "undermining me", "undermines me",
            "never listens", "doesnt listen", "doesn't listen", "wont listen", "won't listen",
            "never available", "never has time", "cancels our one to one",
            "cancels our one to ones", "no time for me", "too busy to talk",
            "never replies to me",
            # Being called names, teased or left out by the people you work with is the same
            # behaviour as a snide remark, said in the words people type: "i got called names at
            # work" was answered "Noted: you got called names at work." Each phrase names the
            # person at the receiving end, because "teased my colleague about his hair" and
            # "laughed at the film" are the same verbs the other way round.
            "called names", "called me names", "calling me names", "call me names",
            "got called names", "got called a name", "name calling", "being called names",
            "teased me", "teasing me", "being teased", "got teased", "been teased",
            "laughed at me", "laughing at me",
            "made fun of me", "making fun of me", "been made fun of", "left me out",
            "was left out", "is left out", "felt left out", "get left out", "gets left out",
            "being left out", "leaving me out", "leave me out", "leaves me out",
            "plays favourites", "plays favorites", "favouritism", "favoritism", "shouts",
            "shouting", "yells", "yelling", "keeps interrupting me", "interrupts me",
            "raise concerns", "raise my concerns", "bring up a problem", "bring it up",
            # Favouritism is one repeated behaviour that needs the dated specifics this reply
            # asks for. Lateness of a colleague is not here: `colleague-late` (#3137) owns that
            # line with its own private conversation, and two answers for one line is worse than
            # one.
            "has favourites", "has favorites", "picks favourites", "picks favorites",
            # "raise it", "raise this" and "raise the issue" are not here: the pronouns belong to
            # whichever question asked what "it" is, and "raise this" also reads "a raise this
            # year", which took every pay question ("should i ask my boss for a raise this year").
            # A bare "raise the issue" is raise-with-boss's line, which has the meeting and the
            # grievance procedure for it.
            "address the problem", "without blaming",
            # the same behaviour described by what it sounds like: the snide remark, the dig, the
            # cold shoulder, the joke at your expense. "How do I deal with a passive aggressive
            # colleague" was getting an employment-advice hand-off for want of these words.
            "passive aggressive", "passive-aggressive", "snide", "snide comments", "sniping",
            "digs", "little digs", "backhanded", "back handed", "jokes at my expense",
            "joke at my expense", "cold shoulder", "sarcastic", "sarcasm", "two faced",
            "two-faced", "mean comments", "nasty comments", "bitchy", "catty",
            # The plainest way to ask - "how do i deal with a bad boss" - was the one word this
            # entry did not have, so it fell through to the hand-off that says to phone a union.
            # A trait word is not a behaviour, so it is read together with the person word.
            "bad", "bad boss", "bad manager", "horrible", "awful", "terrible", "unpleasant",
            "unreasonable", "unfair", "not fair", "bossy", "bitchy boss", "hate my boss",
            "dread my boss", "scared of my boss", "afraid of my boss")),
          _difficult_colleague,
          avoid=("threaten", "threatened", "hit", "hurt", "hits", "shove", "sounding difficult",
                 "sound difficult", "sounds difficult", "deadline",
                 # a bad back, not a bad boss: the trait words above would otherwise catch
                 # "my back hurts at work"
                 "back", "neck", "shoulder", "shoulders", "knee", "knees", "wrist", "ankle",
                 "pain", "aches", "aching", "sore",
                 # a smell is the one thing you say about the person, not the behaviour, so the
                 # behaviour script is the wrong shape for it: "how do i tell someone at work
                 # they smell" was getting the meeting-and-dated-notes answer
                 "smell", "smells", "smelled", "smelly", "stinks", "stink", "stinking",
                 "body odour", "body odor", "bad breath", "sweaty", "sweat", "hygiene",
                 "unwashed")),

    entry("deadline-push",
          (("deadline", "deadlines"),
           ("unrealistic", "moved", "moving", "changing", "changed", "keeps changing", "forward",
            "sooner", "too tight", "push back", "extend", "negotiate", "impossible", "tight",
            "pushed", "no time",
            # "how do i deal with an unreasonable deadline" carried the topic word and none of
            # the ask words, so it fell through to a shrug: the shape of the question has to be
            # in the key, and the deadline in the first group keeps it from taking anything else
            # not "how do i" or "what do i do" on their own: with "deadlines" in the first group
            # they took "my team keeps missing deadlines, how do i raise it without blaming
            # people" from raise-with-boss. "deal with" and "handle" are the ask; the topic word
            # is the deadline
            "unreasonable", "unfair", "not realistic", "cant be done", "can't be done",
            "deal with", "handle")),
          "Reply the same day with the trade-off, not a complaint: \"If this lands on Thursday, "
          "testing slips to Monday - which would you rather?\" If the dates keep moving, say it "
          "plainly at your next one-to-one: \"I plan around the dates I'm given, so once we agree a "
          "date I need it to hold.\" Put the risk in writing once; a missed deadline you flagged "
          "early is a much smaller problem."),

    # Both halves name a meeting: the first the meeting itself, the second what happens to it.
    # A bare "boss" or "manager" here would own every "my boss keeps ..." line in the language -
    # "my manager never listens to me", "my boss keeps changing my targets" - and answer it with
    # a standing slot, so the meeting has to be named before this entry says anything.
    entry("one-to-one-keeps-moving",
          (("one to one", "one to ones", "one-to-one", "one-to-ones", "1:1", "1-2-1",
            "one to one meeting", "one to one meetings", "1 to 1", "1 to 1s",
            "check in", "check in meeting", "check ins", "weekly check in", "catch up",
            "catch ups", "catch-up", "catch-ups", "review meeting"),
           ("moved", "move", "moves", "moving", "rescheduled", "reschedule", "rescheduling",
            "postponed", "postpone", "postponing", "pushed", "pushing", "bumped", "bumps",
            "cancelled", "canceled", "cancelling", "keeps", "never", "last minute",
            "short notice", "again")),
          "Ask for the slot to be a standing one rather than a one-off: \"Can we hold Thursday at "
          "10 for our one-to-one, and if it has to move, let me know the day before?\" Then put your "
          "two or three points in writing before each one, so a fifteen-minute meeting still covers "
          "them, and keep the list on the same email thread. If it keeps getting bumped, reply to the "
          "last cancellation with what you were going to raise and ask for it in writing instead - "
          "a boss who will not sit down for long will usually answer an email.",
          # Normal people put this next to a pay rise, a review or a workload complaint; those
          # entries keep the lines that are about the thing they are about.
          avoid=("appraisal", "performance review", "yearly review", "annual review",
                 "pay rise", "payrise", "salary", "promotion", "resign", "quit", "interview",
                 "redundancy", "sick note", "holiday", "deadline", "deadlines", "rota", "shift",
                 "shifts", "office move", "relocat", "goalpost", "goalposts")),

    entry("appraisal-prep",
          (("appraisal", "performance review", "one to one", "1:1", "review meeting",
            "yearly review", "annual review"),
           ("prepare", "how", "went badly", "what to ask", "feedback", "tomorrow", "worth",
            # "i have a performance review coming up" is the same ask with the date left out
            "coming up", "next week", "this week", "soon", "in a fortnight", "nervous",
            "dread", "what do i")),
          "Write three lines before you go: what you delivered, with numbers if you have them; one "
          "thing that slipped and what you changed because of it; and one ask - a project, "
          "training, a raise or more flexibility. Then ask \"what would make this a great year for "
          "you?\" and close by saying what you need from them."),

    entry("promotion-case",
          (("promotion", "promoted", "step up", "senior role",
            # "how do i ask for more responsibility" names no title and was a shrug
            "more responsibility", "more responsibilities", "bigger projects", "take on more",
            "more senior work"),
           ("how", "ask", "case", "deserve", "get", "worth", "ready", "what", "should i")),
          "Ask what the next level looks like in writing, then start doing one part of it now - "
          "promotion usually follows evidence, not a request. Bring a one-page case: what you "
          "delivered, what you already do that the role needs, and who you have trained. Ask at a "
          "planned review, not straight after a good day.",
          # "how many steps up the shard" reached this on "how" and "step" and got a career
          # answer: a count of stairs in a place is a fact about the place.
          avoid=("shard", "tower", "eiffel", "pisa", "cathedral", "stadium", "monument",
                 "how many steps", "how many stairs", "how many steps are there")),

    # The evidence question the raise answer asks for, said as the answer: "ive been there 3
    # years and taken on more work" after "how do i ask my boss for a pay rise" is not the
    # rota (that entry's asking half carries "boss" and "ask", and the written-out subject put
    # them there) and it is not an echo either. The line names no pay word of its own, so it
    # only matches once the subject is written back in, and then this is what it is about.
    entry("raise-evidence",
          (("taken on more work", "taken on extra work", "more responsibility",
            "more responsibilities", "doing two jobs", "doing the job of two",
            "still on the same pay", "still on the same money", "long service",
            "been there", "years there", "years of service", "cover for",
            "training the new", "train the new"),
           ("pay", "rise", "raise", "boss", "manager", "worth", "deserve", "evidence",
            "ask", "case", "money")),
          "That is the evidence to bring: the years you have been there and the work you took "
          "on, put in numbers - the jobs that came off someone else's desk, the people you "
          "trained, what changed because of you. Then ask for the specific thing you want - a "
          "figure on your pay, or the shifts you are after - rather than a promise."),

    entry("ask-for-raise",
          (("pay rise", "raise", "salary increase", "more money", "more pay", "pay increase",
            # Britain says "a rise", not "a raise": "how do i ask my boss for a rise" reached no
            # entry at all, so the commonest wording of the commonest pay question was a shrug.
            # It is the phrases, never the bare word: a rise in rent, in prices or in interest
            # rates is a different question, and those are in the avoid list below.
            "a rise", "for a rise", "rise in pay", "wage rise", "salary rise", "payrise",
            "pay-rise", "want a rise", "want a raise", "want more money", "want more pay",
            # "how do i talk to my boss about pay" is the same meeting as "how do i ask for a
            # pay rise", and it was answered with how to end a conversation politely.
            "about pay", "about my pay", "about the pay", "discuss pay", "discuss my pay",
            "bring up pay", "talk about pay", "pay with my boss", "pay with my manager"),
           ("ask", "boss", "manager", "how", "worth", "negotiate", "convince", "justify",
            "deserve", "due", "underpaid", "refused", "said no", "pay review",
            # "i want a rise" and "is a 3 percent pay rise fair" are the same question in
            # fewer words; the ask list above is unchanged, so the entry stays narrow.
            "want", "wanted", "fair", "how much", "percent", "per cent")),
          "Book a proper meeting and bring evidence: what you delivered this year, with numbers, "
          "and what the same job pays elsewhere. Then ask for a specific figure with the reason "
          "attached: \"I'd like to move to 34,000, given I've taken on the reporting and the last "
          "two hires came in at that level.\" Ask when you will hear back, and follow up in "
          "writing.",
          # "raise" is mostly not about pay. Raise money for a charity run, raise funds for a
          # startup and raise a child are all questions this entry must pass on, and they were
          # getting "book a proper meeting and bring evidence". Bringing something up with the
          # person who can fix it is raise-with-boss's line.
          avoid=NOT_PAY_RAISE + ("raise the", "raise a concern", "raise my concern", "raise an issue",
                                 # "how do i talk to my friend about pay" is not the meeting with
                                 # the person who sets it; that line belongs to the friend rows
                                 "friend", "friends", "mate", "mates",
                                 # what the rise does to your tax is the money domain's line
                                 "tax", "taxed", "national insurance", "take home", "take-home",
                                 "net pay", "worse off", "better off", "deducted",
                                 "raise a complaint", "raise a problem",
                                 # a team matter is difficult-colleague's line, not a pay one
                                 "my team", "with my team", "with the team", "bring up a problem",
                                 "raise concerns", "raise my prices", "raise prices",
                                 "raise our prices", "raise my rates", "raise my hand",
                                 "raise your hand", "raise it", "raise this with",
                                 "raise this to", "raise that with", "raise that to",
                                 "raise a matter", "raise the matter", "raise something",
                                 "raise a grievance", "grievance", "raise a safeguarding concern",
                                 "safeguarding",
                                 # "how do i raise a toast at a wedding" is the speech row's
                                 # line: "raise" here is the glass, not the pay.
                                 "toast", "a toast", "raise a toast", "raise a glass",
                                 "raise the glass", "wedding", "best man", "maid of honour",
                                 # taking on more without the money is promoted-no-raise's line
                                 "promoted", "promotion", "promotions", "taking on more",
                                 # "a rise" is mostly not about pay either: rent, prices,
                                 # interest rates, the temperature, the sea, the sun.
                                 "rent", "prices", "price", "interest rate", "interest rates",
                                 "temperature", "sea level", "sun", "tide", "cost of living",
                                 "energy", "electricity", "gas bill", "council tax", "premium",
                                 "insurance", "mortgage", "fare", "fares", "bill", "bills",
                                 "inflation", "unemployment", "cases", "water level",
                                 # a credit score, a grade and a puppy are raised too
                                 "credit score", "credit rating", "credit report", "score",
                                 "grades", "marks", "puppy", "puppies",
                                 # "i want to save more money", "how do i save more money each
                                 # month" and "i want to spend less" are the saving question,
                                 # and "more money" in the key was taking all three to the
                                 # pay-rise meeting. Saving and spending are money's lines.
                                 # Whole saving phrases, not bare `save`: "i want a pay rise so
                                 # i can save" is still the raise question.
                                 "save money", "save more money", "save each month",
                                 "save every month", "saving money", "saving up", "save up",
                                 "start saving", "spend less", "spending less",
                                 "cut back on spending", "cutting back on spending",
                                 "put money aside", "budget my money", "get out of debt",
                                 "pay off my debt")),

    # The other half of asking for something: what to do when the answer is no. "how do i ask for
    # a pay rise" then "and if they say no" was answered with a sentence of the answer the person
    # had just read, "what if my boss says no" after a flexible-hours ask got a card about setting
    # a boundary, and the deck's own rows for it were search hedges. The ask is a request made of
    # somebody who can agree it - a boss, a landlord, a school - so the answer is the same one
    # every time, and the words of the worry are what reach it.
    entry("a-no-to-the-request",
          (("say no", "says no", "said no", "say no to it", "refuse", "refuses", "refused",
            "refusing", "if they say no", "if they say no to it", "if he says no",
            "if she says no", "if my boss says no", "if my manager says no", "if they refuse",
            "if they said no", "if my boss refuses", "if the answer is no",
            "if the answer comes back no", "turn me down", "turns me down", "turned me down",
            "turn it down",
            "turns it down", "turn that down", "knock me back", "knocks me back",
            "turned it down", "said it was no", "wont agree", "won't agree", "will not agree",
            "wont budge", "won't budge", "says it's not possible",
            "says its not possible", "says that's not possible", "blocked it", "blocks it"),
           # The worry itself is the *other* person's answer coming back: the line says "if they",
           # "if my boss", never "can i say no". A bare `if` or a bare `they` was enough to take
           # "can i say no without it being a thing", "how to say no without upsetting someone"
           # and "i never say no" - the person doing the refusing, which is a different question
           # with its own cards - so the conditional and the person are one phrase here, and the
           # second signal is that phrase itself.
           ("if they", "if he", "if she", "if my", "if it", "if the", "what if they",
            "what if he", "what if she", "what if my", "and if they", "and if my",
            "when they say", "once they say", "tell me no", "says no to me", "say no to me",
            "refuse me", "refuses me", "turns me down", "turn me down", "turned me down")),
          "Ask for the reason and what would make it a yes: \"What would need to change for this "
          "to be a yes?\" Then ask when you can come back with that, and put that date in the "
          "calendar. If the no has no reason at all, ask who else can agree it, or when it is "
          "worth asking again - and get the answer in writing if it will matter later.",
          # The same words are used for refusing something offered to you ("how do i say no to a
          # second helping", "how do i refuse wine politely") and for turning down overtime,
          # which are the person doing the refusing - a different question with its own cards.
          avoid=("refuses to go", "refuses to eat", "refuses to sleep", "refuses to wear",
                 "refuses to leave", "refuses to come", "refuses food", "refused to go",
                 "refuse to go", "refusing to go",
                 # A child who will not go to school, eat or sleep "refuses" too, and the answer
                 # to that is the school's, the GP's or nobody's here: the line is about a person
                 # declining an activity, not an answer to a request. (qkw-03 on the deck.)
                 "child", "children", "kid", "kids", "daughter", "son", "sons", "daughter's",
                 "toddler", "baby", "teenager", "boy", "girl", "school", "nursery",
                 "wine", "food", "meal", "dinner", "lunch", "meat", "helping", "dessert",
                 "pudding", "cake", "coffee", "tea", "drink", "drinks", "shot", "round",
                 "overtime", "overtime shift", "the shift", "a shift", "shifts", "extra hours",
                 "extra shift", "cover", "favours", "favour", "a favour", "invite", "invitation",
                 "wedding", "party", "birthday", "christmas", "present", "gift", "offer",
                 "offered", "sale", "refund", "return", "returns", "door", "cold call",
                 "cold caller", "salesman", "salespeople", "stranger", "charity", "chugger",
                 "interview", "interviewer", "job offer", "the job", "turn the job down",
                 # a worry about being turned down romantically is not a request with a yes in it
                 "crush", "date", "ask her out", "ask him out", "ask them out", "tell her",
                 "tell him", "tell them i like", "confess", "kiss", "girlfriend", "boyfriend",
                 "tinder", "dating", "propose", "proposal", "marry", "marriage", "come out",
                 # and a thing that was refused by a machine or a form has its own answer
                 "bank", "loan", "mortgage", "credit card", "visa", "application", "claim",
                 "benefit", "universal credit", "insurance", "passport", "driving licence",
                 "driving license", "planning permission", "parcel", "delivery", "refunded"),
          # A line that asks about the other person's answer is about that answer, while the row
          # for saying no politely is the person doing the refusing; when both fit, this one is
          # the question being asked.
          bias=1),

    # The pay rise asked for in writing is the letter, and nothing claimed it: `ask-for-raise`
    # needs the spoken ask, so "how do i write a pay rise letter", "how do i write a letter
    # asking for a pay rise", "how do i write a salary increase letter" and "how do i write a
    # promotion letter" all went to `cake-piping`, whose key holds a bare `letters` - a
    # buttercream star nozzle for a letter about money. The job-ask entries still answer the
    # spoken form ("how do i ask for a pay rise", "i want a promotion"): the second half of the
    # key is the writing words only, so a bare ask never reaches this row.
    entry("raise-letter",
          (("pay rise", "payrise", "pay-rise", "raise", "pay increase", "salary increase",
            "wage rise", "salary rise", "a rise", "rise in pay", "more money", "more pay",
            "promotion", "promoted", "market rate", "pay review"),
           ("letter", "letters", "email", "write", "writing", "written", "in writing",
            "put it in writing", "draft", "drafted", "wording", "the words", "note")),
          "The letter is short: say what you want in the first line, with the figure or the title "
          "in it - \"I'm writing to ask to move to 34,000 from April\", or \"to be considered for "
          "senior analyst\" - then spend one paragraph proving it. Three or four sentences of "
          "evidence with numbers: what you took on, what it saved or earned, what the same job "
          "pays elsewhere. Close by asking for a short meeting and a date you will hear back, "
          "keep a copy, and say it out loud to them first if you can, so the letter is a record "
          "rather than a surprise. One page, dated, no apology and no \"I know times are hard\".",
          # A letter to someone else about something else keeps its own answer: the cover
          # letter, the resignation, the complaint, the reference and the letter to the
          # landlord, the council or the school are all written asks, and none of them is a
          # pay conversation.
          avoid=NOT_PAY_RAISE + (
              "cover letter", "cover letters", "resignation", "resigning", "resign",
              "quit", "leaving", "notice", "complaint", "complain", "complaining",
              "reference", "reference letter", "landlord", "tenancy", "tenant", "rent",
              "council", "mp", "doctor", "gp", "school", "insurance", "tax", "invoice",
              "mortgage", "bank", "refund", "guarantor", "visa", "solicitor",
              # the things people "raise" that are not money: a concern, a child, a price, a
              # hand, funds. The words are in the first half of the key, so the line has to be
              # handed back to the entry that owns it.
              "raise a concern", "raise an issue", "raise concerns", "raise a problem",
              "raise a complaint", "raise the matter", "raise this", "raise that", "raise it",
              "raise my concerns", "prices", "price", "my prices", "rates", "my rates",
              "hand", "hands", "raise a glass", "a toast"),
          # The row is about the writing itself, so a line has to name the writing. `wording` in
          # the key is there because people do ask how to word the thing, but a loose form of
          # `wording` is the word `word`, and "i got promoted and nobody said a word" had
          # nothing to do with a letter and still reached this template. The wording asks are
          # here as phrases, so a sentence with "the words" in it is a letter and "said a word"
          # is not. This is an `ask` rather than a list of `avoid` phrases because the person
          # often describes the silence *and* asks for the letter in one line - "my boss said
          # nothing about a pay review how do i put my request in writing" - and that is still a
          # letter.
          ask=("letter", "letters", "email", "emails", "write", "writing", "written",
               "in writing", "put it in writing", "draft", "drafted", "drafting",
               "word it", "word that", "how do i word", "what wording", "wording for",
               "wording should", "the words", "the right words", "a note"),
          # Bias, and it is only a tie-break: `cake-piping` reaches these lines on the word
          # `letter` alone (its key holds `letters` and `lettering`, so a letter reads as
          # lettering) and so does the congratulations-card row on `promotion`; both rank level
          # with this one and win on the registry's order, because the knowledge base is read
          # domain by domain. A letter about money is this row's, and it can only fire on a line
          # that carries both halves of the key.
          bias=3),

    # main carried two unpaid-wages entries after a merge (this one and the one further down
    # about writing to payroll); the one that answers is kept, and this duplicate is gone.
    # Getting your own money back for the job: receipts, the policy, the deadline.
    entry("expenses",
          (("expenses", "expense", "receipt", "receipts", "mileage", "claim back", "claim it back",
            "reimburse", "reimbursement", "fare", "fares", "ticket", "tickets",
            "claim for", "claiming for", "tax back", "claim tax",
            # the plainest way people ask for it carries no word this entry had: "how do i claim
            # expenses" was answered with the working-from-home flat rate
            "claim expenses", "claiming expenses", "claim my expenses", "expenses claim",
            "claim back expenses", "expense claim"),
           ("work", "back", "claim", "claiming", "submit", "get back", "get it back", "how",
            "deadline", "policy", "train", "travel", "taxi", "hotel", "fuel", "lunch", "driving",
            # "what is the mileage rate" had no second word of its own to match: the mileage
            # word is in the first half of the key, so the second half has to name the thing
            # being asked about. It is the rate itself, not the question words: with "what is"
            # and "how much" in here, "what is the price of a ticket" left money's honest
            # "prices move too fast" for the receipts policy (sure-wombat's review).
            "rate", "rates", "allowance", "per mile", "mileage rate", "mileage allowance")),
          "Check the policy before you spend, because the deadline is the thing people lose money "
          "to: most employers want receipts within a month or the tax year. Photograph every "
          "receipt the day you get it, put the claim in as one list with the date, the reason and "
          "the amount, and use your own car's mileage rate if you drive - 45p a mile for the first "
          "10,000 business miles in the tax year and 25p a mile after that (24p a motorcycle, "
          "20p a bicycle). If a claim is refused, ask for the policy in writing; anything "
          "you spend that is wholly for the job and not reimbursed can be claimed against tax. "
          "Working at home is the same idea: claim £6 a week flat rate from HMRC without receipts, "
          "or the actual extra costs of broadband and heating if they are higher.",
          # a flexible-hours request, a work complaint and what to claim on a benefit are other
          avoid=("flexible", "flexible hours", "benefits", "universal credit", "tax return",
                 "self employed", "self-employed", "childcare", "uniform",
                 # a personal bill or a tenancy deposit is not a claim on the employer
                 "vat", "deposit", "landlord", "tenancy", "tenant", "insurance", "excess",
                 # nor is a thing that was stolen: "my camera was stolen from my hotel room,
                 # can i claim it back" was told to photograph the receipt for the boss, and
                 # the hotel's liability card (or the police report) is the answer to it
                 "stolen", "stole", "theft", "thief", "robbed", "burgled", "burglary", "nicked",
                 "took my", "taken from my", "went missing", "pickpocket", "pickpocketed",
                 "cut my expenses", "cut expenses", "lower my expenses", "reduce my expenses",
                 "save on expenses",
                 # The bare word "ticket" is in the key, so a rail fare question came here and
                 # was told to check the employer's expenses deadline: "how do i get cheap train
                 # tickets" and "how do i get a refund for a train ticket" are fares and refunds,
                 # and getting money back off an employer is neither.
                 "cheap", "cheaper", "cheapest", "railcard", "advance fare", "off peak",
                 "refund", "refunds", "money back", "delay repay", "compensation",
                 # A price question is not a claim question: "how much is a ticket to london"
                 # and "what is the price of a ticket" key on ticket + how, and the receipts
                 # policy is the wrong answer to both.
                 "price", "prices", "priced", "cost", "costs", "how much is", "how much are",
                 "how much does", "ticket to", "tickets to", "fare to", "single ticket",
                 "return ticket",
                 # and selling a ticket on is neither a fare nor a claim: "how do i resell my
                 # ticket" was answered with the expenses policy.
                 "resell", "resale", "reselling", "sell my ticket", "sell my tickets",
                 "pass on my ticket", "give my ticket away",
                 # a ticket for a match is a ticket to buy rather than a receipt to claim: the
                 # key holds "ticket" and "how", so "how do i get tickets for a match" was
                 # answered with the expenses deadline
                 "match", "matches", "football", "soccer", "stadium", "concert", "gig",
                 "festival", "away end", "home end", "cup final",
                 # "how far is a marathon" and "how far is the airport" are distance questions.
                 # The loose forms of "fare" reached "far", so the receipts policy was answering
                 # them; the distance phrasings are in the avoid list and the mileage phrasings
                 # above are in the key, which is the same question.
                 #
                 # "how long is" and "how long does" are deliberately not in this list: "how long
                 # does an expenses claim take" is this entry's own question, and the distance
                 # lines ("how long is a 5k") already leave on the words below.
                 "how far", "how far is", "how big", "how deep", "distance", "distance from",
                 "in km", "in miles", "kilometres", "kilometers", "miles away", "km away",
                 "how tall", "how high",
                 # The homeworker's flat rate is the money entry's, and its key carries these
                 # lines: this entry beat it on rank, so "can i claim expenses for working from
                 # home" was told to check the employer's deadline and the £6 a week never came up.
                 "working from home", "work from home", "from home", "wfh", "homeworker",
                 "homeworking", "home office", "tax relief", "tax rebate", "flat rate"),
          # "how do i claim expenses" reached money's `wfh-tax` first, because that row keys the
          # word "expenses" for the working-from-home flat rate. A claim for a train fare or a
          # hotel is this entry, so it takes the tie.
          # A ticket without money coming back is not a claim: the row keys "ticket" and "fare"
          # beside "train", "travel" and "taxi", and every one of these reached "check the policy
          # before you spend" - "i lost my train ticket", "can i change my train ticket", "is my
          # train ticket valid on any train". The guard asks the one question the answer needs an
          # answer to.
          guard=_it_is_about_claiming,
          bias=1),

    # Raising something with the person who can fix it: a concern, a complaint, a grievance.
    # The bare word "raise" means this far more often than it means money, so this entry takes
    # those lines before the pay one and gives the steps rather than a shrug.
    entry("raise-with-boss",
          # The verb and its object are separate parts, so a word between them does not lose the
          # line: "raise the issue", "raise a matter", "raise it", "raise a safeguarding
          # concern" and "raise something" all answer, and so does "make a complaint about ...".
          (("raise", "raised", "raising", "complain", "complaining", "complaint", "complaints",
            "grievance", "grievances", "put in a complaint", "make a complaint",
            # "how do i log a grievance" reached nothing: a bare "grievance" is one covered word,
            # and the entry needs two, so the phrases carry the second one
            "log a grievance", "log grievance", "logged a grievance", "file a grievance",
            "formal grievance", "written grievance", "grievance procedure",
            "grievance meeting", "start a grievance", "open a grievance",
            "made a complaint", "put in a grievance",
            # The same act in the words people use for it: "i need to flag something with my
            # manager", "how do i bring up a problem with my boss", "mention it to her".
            "flag", "flagged", "flag up", "bring up", "brought up", "bring it up",
            "brought it up", "mention", "mentioned", "point out", "pointed out",
            # "should i go to hr about my manager" and "how do i report a coworker" are the
            # same ask in the words people actually use, and neither reached this entry: one
            # got the shop-complaint answer, the other a shrug.
            "go to hr", "go to human resources", "take it to hr", "report", "reported",
            "reporting", "escalate", "escalated",
            # The ask for the route is the same question as the act: "who do i talk to about a
            # problem at work" was answered with slides, because the presentation row keys the
            # bare words "talk" and "work". Naming the person is part of asking how to raise it.
            "talk to about", "speak to about", "talk to someone about", "who do i talk to",
            "who do i speak to", "who to talk to", "who should i talk to", "who can i talk to",
            "who should i speak to", "who can i speak to", "who do i approach", "who should i ask",
            "who do i raise", "who do i take it to"),
           ("issue", "issues", "concern", "concerns", "matter", "something", "safeguarding",
            "problem", "worry", "boss", "manager", "hr", "work",
            "workplace", "colleague", "colleagues", "team", "union", "complaint", "complaints",
            "grievance", "grievances", "coworker", "coworkers", "co-worker", "co-workers")),
          "Ask for a short private meeting and say the thing in your first sentence: \"I want to "
          "raise something before it gets bigger.\" Then give one concrete example: what happened, "
          "when, and what it cost you or the work - and what you want changed, because a fix is "
          "easier to agree to than a complaint. Follow it up in writing (\"to sum up what we "
          "agreed...\") and keep that copy. If it is about how you have been treated, ask HR for "
          "the grievance procedure in writing: it has fixed steps and time limits, and they have to "
          "follow it.",
          # A line that names money is a pay question however the verb is worded: "how do i
          # mention a pay rise to my boss" is ask-for-raise's, not this entry's.
          avoid=NOT_PAY_RAISE + ("raise prices", "raise my prices", "raise our prices",
                                 "raise my rates", "raise my hand", "raise your hand",
                                 "raise a glass", "raise money for", "fundraiser",
                                 "raising money",
                                 # A business complaint is not an HR one: the bank, the energy
                                 # supplier and the airline all have their own complaints
                                 # procedure, and the shopping and admin entries know it.
                                 "bank", "energy", "electricity", "gas bill", "broadband",
                                 "airline", "flight", "insurance", "refund", "retailer",
                                 "shop", "supermarket", "council", "ombudsman",
                                 # a report of an accident or an injury is the health-and-safety
                                 # line, not bringing a concern up with a manager
                                 "injury", "injured", "accident", "near miss", "police",
                                 "crime", "pay rise", "pay increase", "pay review",
                                 "salary", "salaries", "wage", "wages", "more money",
                                 "more pay", "underpaid", "paycut", "pay cut")),

    # --- the ordinary week ----------------------------------------------
    entry("calling-in-sick",
          # People write the message out before they send it, in their own words: "text to my boss
          # saying im sick" is the same message as "call in sick". The subject is being ill rather
          # than the writing, so the ask names the illness: the phrase "message ... my boss" alone
          # gave "i passed on the message to my boss" a sick note.
          (("call in sick", "calling in sick", "off sick", "sick day", "day off sick",
            "tell my boss i'm sick", "tell my manager i'm sick", "tell my boss im sick",
            "tell work i'm sick", "tell work im sick", "text to my boss", "text my boss",
            "message to my boss", "message my boss", "email my boss", "phone in sick",
            "let my boss know", "let work know",
            # "ring in sick" is the same message as "phone in sick", and only the word for the
            # phone was missing: every one of these lines fell past this row to a ring on a
            # finger, a ring on a hob, or - worst - a log with a ring in it. The shapes are the
            # phone ones, so "ring in" alone needs the illness word from `ask` below.
            "ring in sick", "ringing in sick", "rang in sick", "ring sick", "ring in",
            "ring in tomorrow", "ring work", "ring my boss", "ring my manager",
            "ring the boss", "phone my boss", "phone my manager", "phone work",
            "ring them in the morning"),
           # "is it ok to ring in sick" is the same question as "should i", and it used to get
           # the "I can't see or feel anything from here" hedge because the ask had no word in
           # this half. None of these reach a phone line on their own - the phone shape above
           # has to be there first - so "is it ok to ring the council" is untouched.
           ("how", "email", "what to say", "whatsapp", "text", "message", "write", "wording",
            "words", "should i", "morning", "is it ok", "is it okay", "ok to", "okay to",
            "fine to", "bad to", "wrong to")),
          "Message before your start time, as early as you can: \"I'm not well enough to come in "
          "today - I'll update you tomorrow.\" You do not owe symptoms or an apology; do say "
          "whether anything urgent needs covering. Follow your workplace's own rule for how to "
          "tell them - usually a call on the first day.",
          ask=("sick", "ill", "unwell", "poorly", "symptom", "symptoms", "vomit", "migraine",
               "flu", "cold", "temperature", "doctor", "bug", "unfit"),
          # "how many sick days am i entitled to" is about pay, not about the message
          avoid=("entitled", "entitlement", "sick pay", "company sick pay", "statutory",
                 "how many sick days", "how much sick pay", "paid", "unpaid", "owed")),

    # A sick day that is not about a cough: the question is whether mental health counts, and the
    # bot answered it with "I'm not sure about that one, sorry". It counts, the message is the
    # same one, and inventing flu is the part that goes wrong.
    entry("sick-day-when-not-sick",
          (("sick day", "sick days", "call in sick", "day off sick", "duvet day",
            "mental health day", "throw a sickie", "take a sickie"),
           ("not sick", "not actually sick", "not ill", "not really ill", "not physically ill",
            "mental health", "burnout", "burnt out", "burned out", "stressed", "stress",
            "anxiety", "anxious", "depressed", "exhausted", "guilty", "guilt", "skive",
            "just need a day", "need a day off", "is it ok", "ok to", "okay to")),
          ("A sick day is for not being fit to work, and a head that will not settle counts as "
           "much as a temperature does: say \"I'm not well enough to come in today\" and nothing "
           "more - you do not owe a diagnosis, and you do not have to invent flu to be believed. "
           "Do not post the day out, and if the same week keeps needing one it is worth telling "
           "your manager what is behind it, because a run of odd days looks worse than one honest "
           "conversation. If it is longer than a week or two, that is a GP appointment."),
          # the wording of the message is calling-in-sick's, and the pay is sick-pay's
          avoid=("how do i tell", "how to tell", "what do i say to my boss", "text my boss",
                 "message my boss", "email my boss", "phone in sick", "entitled", "sick pay",
                 "statutory", "how many sick days", "paid", "unpaid", "self employed"),
          # "should i take a sick day for my mental health" is this entry's question, and the
          # message entry keys "sick day" and "should i" as well; the head that reads the
          # reason has to win the tie
          bias=2),

    entry("sick-pay",
          # The number of paid sick days is not a legal number, which is why the question has no
          # one-line answer in most people's heads: it is Statutory Sick Pay plus whatever the
          # contract adds. The rate is set each April, so the reply gives its shape, not a figure
          # that stops being true.
          (("sick pay", "sick days", "sick leave", "statutory sick pay", "ssp", "paid sick",
            "sick note", "off sick", "time off sick"),
           ("entitled", "entitlement", "how many", "how much", "paid", "pay", "statutory",
            "am i owed", "owed", "company", "my rights", "do i get", "can i get")),
          "There is no set number of paid sick days in law: after three days off sick, "
          "Statutory Sick Pay pays a flat weekly rate, a bit over \u00a3100 a week, for up to 28 "
          "weeks - and your contract can pay much more than that, so check it before you assume "
          "a week of full pay. A fit note is needed after seven days off. If pay is withheld "
          "when you were genuinely ill, ACAS is free and will take it up for you.",
          # being sacked for absence is the attendance entry's line, not a pay question
          avoid=("sacked", "fired", "dismissed", "disciplinary", "redundant", "warning",
                 "absence", "absent", "attendance")),

    entry("holiday-request",
          (("time off", "annual leave", "holiday request", "holiday form", "day off",
            "leave request", "annual leave request",
            # asking for more of it, which is the commonest shape and used to be a shrug.
            # "more holiday" alone is not enough to reach this: the ask words have to be there,
            # so "should i take a pay rise or more holiday" stays with its own entry.
            "more holiday", "extra holiday", "more annual leave", "extra annual leave",
            "more days off", "extra days off", "more leave", "extra leave",
            "buy extra leave", "buy more holiday"),
           ("request", "ask", "approve", "boss", "manager", "book", "apply", "entitled",
            # the shapes people use when they want more of it rather than a particular date
            # "get more" is not here: "how do i get more annual leave" is asking what the
            # entitlement is, and the statutory-days entry answers that better than the ask.
            "can i", "am i allowed", "buy")),
          "Ask early, in writing, with the dates and the day you are back: \"Could I take 2-9 June, "
          "back at work on the 10th?\" Offer the handover before they ask for it. Requests usually "
          "fail because they arrive in the busy week, not because the time itself is refused.",
          # a few days off with a budget in the line is a where-to-go question, not a request
          # for the time: "i have 200 quid and a few days off where can i go" was given the
          # request script, and travel.where-no-place holds the fares.
          avoid=("where can i go", "where should i go", "where could i go", "where to go",
                 "where would you go")),

    # A leave line states the plan: "i'm off work next week", "off work on friday", "taking next
    # week off work", "booked a week off work in june". The fit-note card took all of those (its
    # second group held `work`), so a person going to the seaside was told to fill in the
    # self-certificate; with that card's ask gate in place they fell to a shrug instead. The plan
    # is worth one useful thing rather than an echo, and the leave itself is already agreed, so
    # the ask-in-writing script does not fit.
    entry("leave-plan",
          (("off work", "time off work", "off from work", "leave from work", "days off work",
            "week off work", "a week off", "time off"),
           # the time is what makes it a plan rather than a state: "i'm off work next week" has
           # it and answers, "i'm off work" alone does not and is left to whatever reads it now.
           ("next week", "next month", "tomorrow", "tonight", "on friday", "on monday",
            "on thursday", "on wednesday", "from monday", "from friday", "for a week",
            "for two weeks", "for a fortnight", "for the week", "in june", "in july", "in august",
            "in september", "in october", "in november", "in december", "in january",
            "in february", "in march", "in april", "at the weekend", "over christmas",
            "this week", "a week", "two weeks", "fortnight")),
          "Time off you can see coming is the best kind. Put the dates on the rota or in the "
          "leave system before you go, so there is nothing to argue about when you are back, and "
          "set an out of office with who to ring instead of you. Going somewhere, or is it a "
          "week at home?",
          # a question about the leave is the entitlement or the request script, and an illness
          # that keeps you off is the fit-note card: this row is only for the plan
          avoid=("how many", "how much", "how long", "how do i", "how to", "how should i",
                 "what do i say", "can i", "could i", "should i", "am i",
                 "when do i", "when should i", "entitled",
                 "entitlement", "allowance", "request", "ask for", "asking for", "apply",
                 "form", "holiday pay", "unpaid", "carry over", "carry it over", "roll over",
                 "sick", "ill", "unwell", "poorly", "injury", "injured", "pain", "hurts",
                 "hospital", "operation", "surgery", "note", "signed off", "self certify",
                 "doctor", "gp", "flu", "covid", "virus", "bug", "migraine", "bad back",
                 "my back",
                 # the leave is the setting, not the question, when the line names something
                 # else to do with the time: "i have a week off and i want to lose weight" was
                 # told to book the dates on the rota instead of the diet answer.
                 "lose weight", "losing weight", "lose a stone", "diet", "get fit", "gym",
                 "exercise", "another job", "new job", "second job", "quit",
                 # the leave is the when of a trip, not the question: "taking a week off in
                 # october where should we go" is a place question and travel owns it.
                 "where can i go", "where should i go", "where could i go", "where to go",
                 "where would you go", "where should we go", "where can we go",
                 "where could we go", "which country", "somewhere warm")),

    entry("flexible-hours",
          # "flexible hours" is what most people write, and without it in the key the ask
          # entry missed "can i ask for flexible hours" once the right-to-ask entry existed
          (("flexible working", "flexible hours", "compressed hours", "four day week",
            # The bare counts sat here on their own and took every leave line with a number of
            # days in it: "i lost 3 days of holiday can i get them back" and "i saved three days
            # of holiday can i use them" both got "put it in writing with the shape you want,
            # could I do 8-4 instead of 9-5". A number of days is only this row's when it comes
            # with the arrangement ("four days a week", "go down to three days", "three days a
            # week"), and those shapes are all named below.
            "four days a week", "4 days a week", "three days a week", "3 days a week",
            "part time", "part-time", "hybrid working", "fewer days",
            "less days", "work from home request", "work from home", "wfh", "change my hours",
            "change my days",
            # how people describe going part time without the words "part time": the days they
            # want, or the hours they want back ("i want to reduce my hours")
            "reduce my hours", "fewer hours", "cut my hours", "less hours", "go part time",
            "reduce my days", "go down to three", "go down to four", "back three days",
            "go down to four days", "three days a week", "four days a week", "3 days a week",
            "4 days a week", "go down to 3 days", "go down to 4 days", "down to three days",
            "down to four days",
            # a job share is the same request with a partner in it, and "how do i handle a job
            # share" was reaching money's index-fund entry ("shares" reads as the verb)
            "job share", "job sharing", "job-share", "share my job", "share the role",
            "share a role"),
           ("ask", "request", "how", "boss", "manager", "right", "apply", "want", "drop",
            "reduce", "go down to", "thinking of", "would like", "prefer", "can i")),
          "Put it in writing with the shape you want and the answer to their worry: \"Could I do "
          "8-4 instead of 9-5? I would still cover the 9am call, from home on Teams.\" Offer a "
          "three-month trial and fix the date you will review it - a trial is far easier to say "
          "yes to than a permanent change.",
          # working from home with a toddler is a childcare question, and "my son wants to work
          # from home" is somebody else's job: neither is the request to the manager. The child
          # words are kept as the phrase that makes it a childcare line, not as bare nouns,
          # because a baby is usually the *reason* for the request and the commonest way to say
          # it stood this row down: "i want to go part time after the baby" reached a
          # birth-registration card, "can i go part time after the baby" the health visitor,
          # "i want to go part time after maternity leave" a shrug, and "once the baby is here"
          # the smallest-first-step template.
          avoid=("with a toddler", "with a baby", "with the baby", "with kids", "with the kids",
                 "with children", "childcare", "childcare costs", "childminder",
                 "looking after the kids", "while looking after",
                 "my son", "my daughter", "my husband", "my wife", "my partner", "my mum",
                 "my dad", "my friend",
                 # "wants to" and "wanted to" used to be here and they also matched the ask
                 # itself: "i want to reduce my hours" and "i want to go back three days a
                 # week" were both turned down by their own wording. The people words above
                 # already carry the case they were for ("my son wants to work from home").
                 "someone else", "other people",
                 # money spent on the job belongs to the expenses entry: "what expenses can i
                 # claim for working from home" is a tax and receipt question, not a request
                 "expenses", "expense", "receipts", "receipt", "mileage", "reimburse",
                 "claim back", "claim it back", "claim for", "tax back", "claim tax",
                 # "how do i stay focused when working from home" names the arrangement and
                 # asks how to get the day done; it is wfh-focus's line, not a request to the
                 # manager to change the arrangement.
                 "focus", "focused", "focusing", "distracted", "distraction",
                 "concentrate", "concentrating", "procrastinating", "productive",
                 "motivated", "structure", "routine",
                 # "3 days" and "4 days" are how the request is worded and also how a shelf
                 # life is worded: "can i keep cooked chicken for 3 days" was answered with a
                 # request to change your hours.
                 "chicken", "cooked", "raw", "meat", "beef", "pork", "fish", "rice", "pasta",
                 "ham", "milk", "yoghurt", "yogurt", "cheese", "eggs", "leftovers", "leftover",
                 "fridge", "freezer", "reheat", "eat", "defrost")),
    entry("flexible-right",
    (("flexible working", "flexible hours", "compressed hours", "four day week",
    "hybrid working", "work from home request", "work from home", "wfh",
    "change my hours"),
    ("can i", "am i entitled", "entitled", "right", "legal", "law", "allowed", "refuse",
    "refused", "turned down", "must they", "do they have to", "appeal")),
    "You do not have a right to work from home, but you do have the right to ask, from your "
    "first day in the job. In the UK they must decide within two months, in writing, and talk "
    "it through with you before saying no; a refusal has to be for one of eight listed business "
    "reasons, such as cost or effect on customers. Two requests a year. If it is turned down, "
    "ask which reason applies and appeal in writing, then let ACAS help - a reason with nothing "
    "behind it is where employers come unstuck.",
    # "how do i ask for flexible working" wants the ask and keeps flexible-hours; a question
    # about the right, a refusal or the law is this one, so where both fit this is the answer.
    avoid=("how do i ask", "how to ask", "can i ask", "should i ask", "best way to ask",
           "how do i put", "how to put", "how do i phrase", "how to phrase", "how do i bring it up",
           # money spent on the job is the expenses entry's line, not a request to change hours:
           # "can i claim expenses for working from home" was getting the right-to-request answer
           "expenses", "expense", "receipts", "receipt", "mileage", "reimburse", "claim back",
           "claim for", "tax back", "claim tax"),
    bias=1),

    entry("wfh-focus",
          (("working from home", "work from home", "wfh", "remote work", "remote working",
            "hybrid"),
           # The people in the room are what interrupts a day at home, so the complaint about
           # being interrupted while working from home is this answer's line: without these
           # words "my kids interrupt me when i work from home" got the office deskside plan.
           ("focus", "distracted", "routine", "productive", "procrastinating", "concentrate",
            "structure", "motivated", "interrupted", "interrupting", "interrupts", "interrupt",
            "keeps interrupting", "keep interrupting", "keep getting interrupted",
            "block of time", "no peace",
            # A "without" clause is masked by the reading, so a row that does not name the
            # frame cannot see what is in it: "how do i work from home without getting
            # distracted" reached a work-flexibility answer while this row could not see the
            # word "distracted" at all. Naming the frame keeps the words of the clause for this
            # row only, and the phrases are asked for exactly, so "without the tv" and
            # "without the kids" still pass it by.
            "without getting distracted", "without distractions", "without getting sidetracked",
            # the same clause with the distraction named: "how do i work from home without the
            # tv" was the HMRC flat rate, because the mask hid the only word that says what the
            # line is about
            "without the tv", "without tv", "without the telly", "without the television",
            "without the kids", "without children", "without the children",
            "without interruptions",
            # The complaint is often about the day rather than the distraction, and it is said
            # with a joke: "how do i work from home without going mad" was the HMRC flat rate,
            # because nothing in this key named the feeling. "Without going mad" is the same
            # question as "without getting distracted" - what to do with the day - so the whole
            # phrase is asked for as well as the words on their own, in case the clause is read
            # as the thing being denied.
            "go mad", "going mad", "go crazy", "going crazy", "go insane", "going insane",
            "lose my mind", "losing my mind", "stir crazy", "cabin fever",
            "climbing the walls", "without going mad", "without going crazy",
            "without going insane", "without losing my mind", "without climbing the walls",
            "stuck in the house", "sick of the house")),
          "Give the day a shape: same start time, dressed, a real lunch away from the desk, and a "
          "walk to end it. Put the phone in another room for one 50-minute block before you open "
          "email, and have one call with a colleague a day - the office is what you are missing, "
          "so put a bit of it back in the week.",
          # A line with a "without" clause is read twice, and the two readings tie at six here:
          # the row about the subject of the line should take it, and a nudge is what breaks a
          # tie between two rows that fit a line equally well rather than a word for a word
          bias=1,
          avoid=("lonely", "loneliness", "isolated", "isolating", "sad", "depressed",
                 "anxious", "missing people")),

    entry("wfh-lonely",
          (("working from home", "work from home", "wfh", "remote work", "remote working"),
           ("lonely", "loneliness", "isolated", "isolating", "on my own", "cut off", "no one to talk",
            "nobody to talk", "miss people", "missing people", "missing the office", "by myself")),
          # the line is usually a feeling shared, not a request, so the warmth comes first and the
          # plan second: chat answered this one with "I'm listening" or "Ugh, that's a lot to
          # carry", and a lonely week at the desk is the case where a plan is what helps.
          "Loneliness at the desk is real: the small talk that used to fill the day is gone, and "
          "it does not come back by itself. Put one person in the day on purpose - a standing "
          "fifteen minute call with someone on your team, a lunchtime walk where you actually "
          "speak to someone, and one thing a week outside work with people in it. If the office "
          "is an option, take two days and make them the days you like people; if not, tell your "
          "manager the team has gone quiet and ask for a weekly call. Weeks of it without lifting "
          "is worth a GP.",
          avoid=("toddler", "baby", "children", "kids", "childcare")),

    entry("health-safety-report",
          (("health and safety", "unsafe at work", "dangerous at work", "report a hazard",
            "report a fault", "accident at work", "accident book", "near miss", "hazard",
            # the same accident in a person's own words had no answer: "i slipped at work",
            # "injured at work what do i do", "i fell at work"
            "slipped at work", "fell at work", "fell over at work", "injured at work",
            "injury at work", "hurt at work", "hurt myself at work", "accident in the workplace",
            "fire exit blocked", "no training", "no gloves", "no ppe",
            # how people say it when nothing has a name yet: a place that is unsafe, a blocked
            # fire exit, a machine with the guard off
            "unsafe", "unsafe workplace", "fire exit", "blocked exit", "guard off",
            "no first aid", "broken equipment"),
           ("work", "workplace", "report", "reporting", "boss", "manager", "how do i", "what do i",
            "who do i", "tell", "complain", "refuse", "worried", "concerned", "should i",
            "blocked", "unsafe")),
          "Tell your manager in writing the same day, with the date, the place and what you saw - "
          "and put it in the accident book if anyone was hurt, because that record is what counts "
          "later. If nothing changes within a week, go to the safety rep or the health and safety "
          "person named in your workplace, and after that the enforcing body (the HSE, or the "
          "council for a shop, office or warehouse). You can refuse work you believe is a serious "
          "and imminent danger, and you are protected from being sacked for raising it - so keep "
          "copies of everything you send.",
          avoid=("anxiety", "anxious", "mental health", "stress", "burnout", "depressed"),
          # a part of the body that hurts is the body question, with a place in it; the line that
          # says something happened - a slip, a fall, an injury, a hazard - keeps this answer
          guard=_not_a_body_part_that_hurts,
          # "i had an accident at work" ties with the car-breakdown entry on rank and loses the
          # tie-break: the workplace answer is the one meant, so it wins by a point
          bias=1),

    entry("presentation-nerves",
          (("presentation", "presenting", "talk to the team", "five minute talk",
            "give a talk", "giving a talk", "speaking in front of", "stand up in front of",
            "talk in front of"),
           ("nervous", "scared", "thirty seconds", "start", "tips", "terrified", "shaking",
            "dread", "first", "give", "asked me",
            # "how do i calm down before a presentation" asks the same thing as "i'm nervous
            # about my presentation", and "calm" was the only word missing
            "calm", "calm down", "relax", "settle", "settle my", "hold my nerve", "steady",
            "stop shaking", "keep calm",
            # an interview presentation is asked for as a task, not as a nerve. Nothing looser
            # than that: "how do i handle a presentation at work" is the shape question and
            # belongs to the entry that answers it.
            "interview", "job interview", "interviewer", "task", "assessment",
            # and, like the interview's, the shape where the body says it: "i feel sick before a
            # presentation" was an empathy line, because only the word "nervous" was keyed
            *NERVES_BODY)),
          _presentation_nerves,
          avoid=("essay", "exam", "university")),

    entry("take-feedback",
          # "my boss had a go at me" is this question said the way most people say it, and it was a
          # sympathy line: "told off" was keyed but "had a go at me" was not. The receiving-end forms
          # are shared with the family keys (TOLD_OFF in wording.py); "at work" and "job" are in the
          # second group because a line that names where it happened need not name the boss.
          ((("feedback", "criticism", "criticised", "told off", "telling me off", "said my work",
             "told me my work", "work has slipped") + TOLD_OFF),
           ("boss", "manager", "defensive", "how to take", "criticism", "handle", "disagree",
            "respond", "slipped", "at work", "job", "employer", "office", "line manager")),
          "Ask for a specific example first: \"Can you give me a case where that happened?\" Then "
          "say thank you and write it down without defending - you can disagree later, once you "
          "have checked it. Come back a day later with what you will change; that reply is the bit "
          "people remember."),

    entry("dress-for-work",
          (("dress code", "what to wear", "what should i wear", "what should i put on",
            "what do i put on", "what to put on"),
           ("work", "office", "interview", "first day", "job", "smart")),
          "Ask whoever invited you, or look at photos of the team on the company site. For an "
          "interview, go one notch smarter than the job: a shirt and trousers, or a plain dress or "
          "blouse, and nothing loud. Clean shoes and a jacket cover most of the doubt.",
          guard=not_a_dress_code_off_the_job),

    entry("networking",
          (("networking", "network event", "conference", "work event", "industry event"),
           ("how", "tips", "nervous", "small talk", "start", "alone", "go to")),
          "Aim for two real conversations rather than working the room: ask what they are working "
          "on and what brought them there, then listen. Have one sentence ready about yourself and "
          "follow up with a two-line message the next day. People forget the pitch and remember "
          "who was easy to talk to."),

    # "my employer says im self employed but i have set hours" is not a question about what to
    # charge: it was answered with the freelance day-rate, because "self employed" plus the word
    # "set" in "have set hours" is the price row's key. What the person is asking is whether the
    # label or the job decides, and the answer is the job.
    entry("employment-status",
          (STATUS_TELL,
           ("employer", "boss", "manager", "contract", "paid", "pay", "hours", "tax", "status",
            "legal", "rights", "i have", "i work", "they", "but", "am i", "or employed",
            "which am i")),
          "What the job looks like decides, not the label on the contract: if they say when you "
          "start, where you work and what you do, and you cannot send someone else or turn the "
          "work down, you are an employee in law whatever the paperwork calls you. That usually "
          "means holiday pay, sick pay and minimum wage that were never paid. ACAS will give you "
          "a free status check, and HMRC's CEST tool gives a written answer you can keep; put the "
          "question in writing to the employer first, so the hours and the control are on record.",
          # what to charge as a freelancer keeps its own row, and a tax return, a pension or a
          # company set-up is a different question
          avoid=("charge", "rate", "quote", "day rate", "how much", "tax return", "self assessment",
                 "register", "pension", "invoice", "ir35", "limited company", "set up",
                 # A line that names one entitlement is that entitlement's question, not the
                 # label question: "can my boss tell me when to take my break" is the 20-minute
                 # break rule, and `boss` plus `tell me when` was enough to take it away from it.
                 "break", "breaks", "lunch break", "rest break", "rest", "holiday", "holidays",
                 "notice", "rota", "shift", "shifts", "sick pay", "minimum wage", "overtime",
                 "stay late", "payslip", "pay slip")),

    # The hours-and-pay family: what the law says about breaks, the 48-hour week, overtime pay,
    # unpaid leave and a change to your hours. None of it is advice about the job itself, so the
    # job words below keep it off the interview/leaving questions.
    entry("pay-and-hours",
          (("overtime", "extra hours", "long hours", "hours", "48 hours", "48 hour week",
            # "stay late" and "work late" are the plainest way people ask about overtime, and the
            # entry below matched them while the key never did: "can my work make me stay late
            # without pay" was the search hedge and "can i refuse to work late" the negotiation
            # answer.
            "stay late", "staying late", "stay on late", "work late", "working late",
            "work longer", "without pay", "unpaid overtime", "extra shift", "extra shifts",
            "lunch break", "lunch", "break", "breaks", "rest break", "unpaid leave",
            "time off without pay", "zero hours", "zero hour contract", "zero hours contract",
            "my hours", "working hours",
            # The ask people actually make is "stay late", and the key had only the asking
            # forms of it: "can my work make me stay late without pay" was a search hedge while
            # "do i have to work overtime without pay" got the rule.
            "stay late", "staying late", "stay behind", "stayed late", "work late",
            "working late", "worked late", "extra hours unpaid", "unpaid overtime",
            "overtime without pay", "extra time without pay"),
           ("paid", "pay", "legal", "illegal", "law", "entitled", "entitlement", "must",
            "allowed", "can i", "can my boss", "can my employer", "do i have to", "rights",
            "how long", "minimum", "average", "change", "changed", "what", "is it",
            "compulsory", "mandatory", "obliged", "have to", "do i get", "get paid",
            # the boss doing the asking, which is how the staying-late lines are worded
            "wants me to", "want me to", "asked me to", "asks me to", "told me to",
            "make me", "makes me", "making me", "made me", "force me", "forces me",
            "forcing me", "forced me", "expects me to", "expect me to", "called me in",
            "call me in", "on call", "called in on",
            # A complaint about a break is the same rule as a question about one: "my lunch break
            # is always cut short", "i only get 20 mins for lunch", "they skip my break". Without
            # these words the line carries no question word and the entry never sees it, so the
            # person who is being shorted gets "Got it." while the person who asks gets the law.
            # They are phrases, not bare "never"/"always"/"only": "i sleep about six hours and i
            # never go outside" is not a question about breaks.
            "cut short", "no break", "no breaks", "never get a break", "never got a break",
            "never had a break", "skipped my break", "skips my break", "skip my break",
            "skip my breaks", "skipping my break", "dont get a break", "don't get a break",
            "mins for lunch", "minutes for lunch", "minute for lunch", "hour for lunch",
            "never get a lunch break", "never got a lunch break", "never had a lunch break",
            "no lunch break", "lunch break is", "lunch breaks are",
            "break is", "breaks are", "my break is", "my breaks are",
            # a break that was taken away is the same rule: "i wasnt given my break today",
            # "i never got to sit down", "they made me work through lunch".
            "wasnt given", "wasn't given", "not given", "was not given", "didnt get",
            "didn't get", "did not get", "never got", "never given", "worked through",
            "through my break", "through my lunch", "straight through",
            # a contract that says one thing and a week that says another: "my contract says 40
            # hours but i do 50", "i do more hours than my contract".
            "contract", "contract says", "says 40", "says 35", "says 37", "says 48",
            "more hours than", "more than my contract", "extra every week")),
          _pay_and_hours,
          # "hours", "lunch" and "break" are ordinary words, and the key alone let the pay rule
          # answer the opening hours, a lunch idea and a break from a relationship. One work
          # word (or the break itself) has to be in the line as well.
          ask=("work", "working", "job", "boss", "employer", "employee", "contract", "rights",
               "shift", "shifts", "rota", "pay", "paid", "unpaid", "worker", "workers", "legal",
               "law", "entitled", "employment", "employed", "at work", "on shift", "break",
               "breaks", "overtime",
               # ...and a complaint about a break is the work word, so a line that names the
               # break by what happens to it ("i only get 20 mins for lunch") gets past the gate
               # without the word "work" in it.
               "cut short", "mins for lunch", "minutes for lunch", "minute for lunch",
               "hour for lunch", "no breaks", "lunch break", "lunch breaks"),
          # a job interview, a new job, resigning, a sick day and a holiday are other entries'
          # lines; the reminder about money is the pay-rise one.
          avoid=("interview", "new job", "first day", "resign", "notice", "quit", "redundant",
                 "redundancy", "sacked", "dismissed", "appraisal", "review", "pay rise",
                 "raise", "salary", "promotion", "book", "booking", "annual leave",
                 "holiday request", "bank holiday",
                 "sick", "school", "restaurant", "coffee", "elevenses", "give me a break",
                 # a lunch someone is going to make or eat is the cooking table's line
                 "leftover", "leftovers", "make with", "have for", "cook", "cooking", "recipe",
                 "recipes", "dinner", "sandwich", "sandwiches", "salad", "soup", "meal",
                 "meals", "packed lunch", "snack", "snacks", "the fridge", "takeaway",
                 "take to work", "to work for", "lunch box", "lunchbox", "take for lunch",
                 # "is it worth bringing my own lunch in" is a lunch-ideas line: the words
                 # name the food, and only the phrase "to work" looked like a contract
                 "own lunch", "bring lunch", "bring my lunch", "bringing lunch",
                 "bringing my lunch", "worth bringing", "lunch to work", "lunch in",
                 # turning overtime down is overtime-say-no's script, not the pay rule - and so
                 # is the week-long ask ("my boss keeps asking me to stay late"), which wants the
                 # line to say rather than the contract clause
                 "say no", "saying no", "refuse", "refusing", "refused", "turn down",
                 "keeps asking", "keep asking", "always asking", "asking me again",
                 "asks me again", "over and over", "again and again", "every week",
                 "turning down", "decline", "get out of overtime", "avoid overtime",
                 # a rota that keeps moving is shifts-changed's line, with its own advice -
                 # the words that name the change, not the bare word "shift", which a break
                 # question needs ("do i get a break on a 12 hour shift")
                 "shift change", "shift changes", "changing my shifts", "changes my shifts",
                 "changed my shift", "change my shift", "keeps changing", "keeps moving",
                 "rota", "schedule", "timesheet", "swap", "swapping",
                 "take a break from", "career break", "break up", "broke up", "breaking bad",
                 # a machine that is going to break is not a rest break: "is it going to break" after
                 # a loud fan was answered with the twenty-minute break rule.
                 "going to break", "gonna break", "about to break", "break down", "breaks down",
                 "broke down", "broken down", "will it break", "might break", "could break",
                 "going to last", "will it last", "last much longer",
                 "lunch with", "out for lunch",
                 # "whats a good lunch for work" is a food question that happens to say work:
                 # the packed-lunch answer is the one that helps, not the twenty-minute break.
                 "good lunch", "nice lunch", "lunch idea", "lunch ideas", "lunch box",
                 "lunchbox", "packed lunch", "healthy lunch", "cheap lunch",
                 "quick lunch", "lunch to take", "take to work", "lunch recipe",
                 # A machine or a thing that "is going to break" is not the shift break, and the
                 # bare "break" key plus the "is it" shape took "is it going to break", asked
                 # about a laptop fan that had just been described. Phrases only: "my lunch
                 # break is always cut short" and "did my break count" must keep the rule.
                 "going to break", "gonna break", "will it break", "about to break",
                 "going to break down", "break down", "breaks down", "broke down",
                 "broken down", "if it breaks", "when it breaks", "breaks if")),

    entry("overtime-say-no",
          (("overtime", "stay late", "work late", "extra hours", "long hours", "extra work",
            "more work", "more shifts", "cover again",
            # an extra shift is extra hours with a rota word on it, and it is the commonest way
            # the line is said: "how do i refuse extra shifts politely", "how do i turn down
            # extra shifts" and "how do i say no to extra shifts without being rude" all went to
            # shifts-changed, which answers a rota moved on you with the rota and the contract.
            # The subject words belong here, and shifts-changed now stands down on them.
            "extra shift", "extra shifts", "cover a shift", "cover shifts", "cover for someone",
            # "work my day off" is not in either list: "my boss wants me to work my day off"
            # and "can my boss make me work my day off" ask whether the boss may, which is the
            # cancelled-day-off card, and taking the phrase made those two lines worse while
            # giving no refusal line anything it did not already have from "refuse" or "say no".
            "pick up a shift", "pick up shifts", "pick up extra",
            # "turn down a shift" with no "extra" in it is the same refusal, and the phrases
            # are what carry it: the bare plural "shifts" would take the night-shift sleep
            # question with it
            "turn down a shift", "turn down my shift", "turn down the shift", "decline a shift",
            "say no to a shift", "get out of a shift", "get out of my shift",
            "turn down shifts", "turn down extra shifts",
            # the contract is where the line is: "my contract says 40 hours but i do 50"
            "40 hours", "50 hours", "60 hours", "contracted hours", "unpaid overtime",
            "unpaid hours"),
           ("say no", "saying no", "no to", "refuse", "how", "expected", "every day", "unpaid",
            "stop", "always", "keep asking", "keeps asking", "too many", "50 hours", "40 hours",
            "48", "60", "weekend", "contract", "contracted", "over my hours", "refuse to",
            # "my boss wants me to work late every week, do i have to be paid for it" is this
            # script - the reply already says "if it is every week, ask what is being dropped"
            # and points at the contract - so the week-long ask and the pay question reach it
            # instead of falling past the pay rule, which stands aside on "every week".
            "every week", "wants me to", "want me to", "asked me to", "asks me to",
            "have to be paid", "be paid", "get paid", "paid for it")),
          "Say what you can do rather than what you can't: \"I can stay until six tonight, but not "
          "tomorrow as well.\" If it is every week, ask what is being dropped instead of absorbing "
          "it, and check what your contract says about overtime and pay. Over your contracted "
          "hours you can say no: unpaid regular overtime is worth a word with ACAS. Overtime every "
          "week is a staffing problem, not a personal failing.",
          # work experience is a thing to get, not overtime to turn down; what a trade charges
          # is a price question ("how much does a plumber charge an hour round here" was getting
          # this script, because "hours" and "how" both score); wanting more hours is the other
          # half of the hours question, and ask-more-hours below answers that one.
          avoid=("work experience", "experience", "volunteer", "volunteering", "internship",
                 "placement", "shadow", "apprenticeship",
                 "charge", "charges", "charged", "cost", "costs", "price", "prices",
                 "quote", "quotes", "fee", "fees", "hourly", "an hour round", "per hour",
                 "how much is", "more hours", "ask for more", "full time",
                 "full-time", "on the rota")),
    # "my boss keeps asking me to work weekends" was getting the workload answer, because the only
    # thing it named was a boss and a lot of work. Whether weekends are owed is its own question.
    #
    # The second group holds words about a job and nothing else. It used to carry "every" and
    # "always", which are about the day rather than about work, so any line that named a weekday
    # and the word "every" was read as a rota question: "she rings me every sunday" (after a line
    # about a mother) and "my friend comes over every sunday" both got the contract answer. The
    # day phrases a person actually uses are in the first group as phrases ("every weekend",
    # "7 days"), so nothing real is lost: "i work every weekend" still has "work", and
    # "im always working weekends" still has "working".
    entry("weekend-working",
          (("weekend", "weekends", "saturday", "saturdays", "sunday", "sundays",
            "sat and sun", "every weekend", "7 days", "seven days"),
           ("work", "working", "worked", "allowed", "legal", "have to", "must i", "asks",
            "asking", "asked", "keeps asking", "refuse", "say no", "no extra pay", "extra pay",
            "lieu", "contract", "rota", "picked", "employer", "manager", "boss", "shift",
            "shifts", "overtime", "double time", "day off")),
          "Only if your contract says weekends, or you agreed to them: a boss asking is a request, "
          "not a rule, so check the contract and your written rota first. Even on weekends you are "
          "owed 11 hours off between shifts and 24 hours off a week, and if weekends were never in "
          "your contract you can ask for time off in lieu or a day off in the week to match. Say it "
          "once, in writing: \"I can do one weekend a month, but not both days every week - can we "
          "agree which?\" If the contract does include weekends, ask how the rota shares them out.",
          # a rota that moves without notice is shifts-changed's line, and working nights with no
          # sleep is a sleep question
          # What the row is for is what an employer owes, so the job has to be in the line. The
          # ask group above carries bare modals ("have to", "must i", "allowed", "legal") and the
          # key is a day, so a weekend with no job anywhere in it reached the contract answer: a
          # parent who typed "do i have to get up with him at the weekend too", about a baby who
          # wakes at five, was told about the 11-hour rest rule and a written rota. Every line
          # this answer is meant for names the job ("i work every weekend", "my boss keeps asking
          # me to work weekends", "am i allowed to refuse weekends", "weekends in my rota"), and
          # the rota phrases a person uses for the days off keep the row too.
          guard=_the_weekend_is_a_working_one,
          avoid=("cant sleep", "can't sleep", "insomnia", "night shift", "night shifts",
                 "nights", "nightmare")),
    # The other half of the hours question: not "they want too much of me" but "I want more of
    # them". Said to the browser the two look alike, so this entry asks for the wanting, and
    # overtime-say-no above steps aside by phrase on exactly these lines.
    entry("ask-more-hours",
          (("more hours", "extra hours", "extra shifts", "more shifts", "more work", "full time",
            "full-time", "more days", "on the rota", "pick up shifts", "more overtime",
            "overtime available", "second job hours"),
           ("ask", "how", "get", "want", "need", "boss", "manager", "request", "available",
            "there any", "any chance")),
          "Go to whoever writes the rota and make it about the shifts, not about needing the "
          "money: say which days you can cover, that you want more of them, and ask to be the "
          "first call when someone drops out. A lot of contracts add hours quietly once the "
          "manager knows you want them, so ask what it takes to be put on the next rota and get "
          "the answer in writing. If you want a permanent increase, ask for that in writing too, "
          "and check what your contract says about guaranteed hours."),
    # "meeting" alone is not a key word: its loose form is "meet", and "nice to meet you sam!
    # im thinking about getting a dog" was getting this answer ("thinking" -> "think").
    # A day that is nothing but meetings says so without the word "focus": "my day is all
    # meetings", "i spend all day in meetings", "my calendar is full of meetings" all covered
    # one half of the key and fell to the fallback, while the person was asking for exactly
    # this answer. The same goes for the day someone keeps being walked in on - "people keep
    # barging in", "i get no peace", "i never get a block of time" - so those words are in the
    # key too, and the ask below keeps a meeting-shaped question about something else out.
    entry("focus-with-meetings",
          (("meetings", "a day of meetings", "calendar", "back to back",
            "double booked", "all meetings", "full of meetings", "all day in meetings",
            "meetings all day", "block of time", "barging in", "barges in", "no peace"),
           ("focus", "concentrate", "think", "distracted", "interrupted",
            "no time", "focus time", "get on", "work", "all meetings", "full of meetings",
            "all day in meetings", "meetings all day", "block of time", "no peace")),
          "Put two hours in the morning in your own calendar as a meeting and move anything that "
          "lands on top of it: the work that needs thinking has to come before the day fills up. "
          "Then make the rest smaller: accept 30 minutes rather than an hour, ask for an agenda "
          "before you accept, and leave ten minutes between meetings so one cannot run into the "
          "next.",
          # "in meetings" is how people describe the place a credit, blame or talking-over
          # complaint happens; those entries are about the person, not about finding time.
          avoid=("holiday", "annual leave", "sick", "cancel my", "resign", "pay rise",
                 # A day at home is the day at home, children in the room included, and that
                 # answer is `wfh-focus`.
                 "working from home", "work from home", "wfh", "kids", "children", "toddler",
                 "toddlers",
                 "appraisal", "interview", "credit", "praise", "blame", "talking over",
                 "talked over", "cut across", "cutting across", "shouts", "shouting")),

    # The difficult people at work come in two sorts and only the colleague had an answer.
    # Whoever serves the public meets the other sort: the customer in front of them, angry now,
    # often with an audience. "customer" and "client" are the key, so a shop refund question
    # ("how do i get a refund") stays with the refund entry that knows the law.
    entry("difficult-customer",
          (("customer", "customers", "client", "clients", "shopper", "shoppers", "guest",
            "guests", "punter", "punters", "the public", "someone in the shop"),
           ("difficult", "difficult customer", "angry", "furious", "rude", "shouting",
            "shouts", "shouted", "swearing", "swore", "abusive", "demanding", "unreasonable",
            "complaining", "complains", "complaint", "kick off", "kicked off", "kicking off",
            "calm down", "calm them", "deal with", "handle", "handling", "won't listen",
            "wont listen", "wants a refund", "threw", "throwing")),
          "Get them away from the other customers and let them finish the whole complaint before "
          "you say anything: most people wind down once they have been heard. Then say the "
          "problem back in their words, and give the one thing you can actually do and when - "
          "\"I can't refund it today, but I can have the manager ring you before five.\" Don't "
          "argue about who is right, and don't take swearing or threats: end it, and get a "
          "colleague or the manager, because being shouted at is not part of the job.",
          # a difficult colleague, boss or family member is a different job with a different answer
          avoid=("colleague", "coworker", "co-worker", "boss", "manager", "my staff",
                 "employee", "my team", "neighbour", "neighbor", "my son", "my daughter",
                 "my child", "my mum", "my dad", "my husband", "my wife", "my partner",
                 "mother in law", "mother-in-law", "flatmate", "roommate", "landlord",
                 "teacher", "refund from", "money back from", "complain about", "my order",
                 "delivery", "parcel", "council", "the bank"),
          # A question is the usual way in, but "my customer is being unreasonable" and "a
          # customer swore at me" are the same situation told rather than asked, so those forms
          # count too. A customer who merely features in the story does not: "a customer threw a
          # bottle where i work" is a thing that happened, not a request for a script.
          ask=("how", "what", "should", "deal", "handle", "handling", "calm", "tip", "tips",
               "advice", "can i", "do i", "is being", "at me", "keeps", "my customer",
               "my client", "my guest", "any way")),
    # --- the boss, the day off and the end of the day --------------------
    # "i work from home and i cant switch off" was answered by the phone-fault entry in
    # technology.py, because "switch off" is how a phone dies. That entry now turns the phrase
    # down and this one answers the person who cannot stop working.
    entry("wfh-switch-off",
          (("switch off", "switching off", "switched off from work", "log off", "logging off",
            # "how do i unwind in the evening" was a shrug once the snacking key was narrowed;
            # wind down and relax are already in the second part, so unwind belongs here
            "unwind", "unwinding", "unwind after work",
            "shut the laptop", "close the laptop", "work phone", "checking email",
            "check my email", "checking my email", "work email", "check work email",
            "emails in the evening", "still working", "work late at home",
            "cant stop working", "can't stop working", "keep working", "boundaries"),
           ("work", "working", "home", "wfh", "remote", "evening", "night", "weekend",
            "job", "office", "laptop", "email", "phone", "boss", "after work", "relax",
            "wind down", "stop")),
          "Give the day a hard edge and keep it the same one: laptop shut and work phone in a "
          "drawer at a fixed time, then something physical - a walk, a shower, cooking - because "
          "the body changes gear more reliably than the mind. Tell your team the hours once, in "
          "writing: \"I'm offline after 6 and I pick up messages at 9.\" If you work from the room "
          "you live in, put the laptop out of sight at the end of the day; a screen in the corner "
          "is a shift that never ends.",
          # The other way "work email" comes up is the writing: "how do i make my work emails
          # sound less blunt" is a wording question, and this entry was answering it.
          avoid=("phone keeps", "my phone", "battery", "charger", "tv", "router", "boiler",
                 "heating", "washing machine", "car", "engine", "lights", "blunt", "tone",
                 "sound", "sounds", "polite", "rude", "wording", "less blunt", "rewrite",
                 "write", "writing", "reply to", "sign off", "signing off")),

    entry("called-on-a-day-off",
          (("day off", "days off", "annual leave", "on leave", "on holiday", "out of hours",
            "weekend", "my break"),
           ("calls me", "calling me", "called me", "rings me", "rang me", "ring me",
            "ringing me", "texts me", "texted me", "texting me", "messages me", "phoned me",
            "phones me", "keeps calling", "keeps ringing", "keeps texting", "contacts me",
            "expects me", "expected me", "cant switch off", "can't switch off")),
          "Answer once, in advance, rather than each time it happens: \"I'm off tomorrow. I'll "
          "pick up anything non-urgent on Thursday morning, and if something cannot wait, call "
          "me on this number.\" Then do not answer the ordinary messages - a reply on a day off "
          "teaches people that the day off is available. If it is every week, ask your manager "
          "what the on-call arrangement is; unpaid standby is a rota question, not a favour.",
          avoid=("book", "booking", "request", "how do i ask", "how to ask", "apply for",
                 "entitled", "holiday pay", "where should i go", "hotel", "flight",
                 "my son", "my daughter", "my child", "my kids", "partner")),

    entry("manager-hovering",
          (("micromanage", "micromanages", "micromanaging", "micro manage", "micro manages",
            "micro managing", "micromanager", "hovers", "hovering", "over my shoulder",
            "checks everything", "checks every", "constantly checking", "watching me",
            "doesnt trust me", "doesn't trust me", "no trust", "wants to approve everything",
            "micromanaged", "micromanagement", "treated like a child"),
           ("boss", "manager", "work", "job", "how", "deal", "talk", "handle", "tell",
            "what do i do", "stop", "being", "im being", "feels like")),
          "Ask for a bigger rope in the language of their worry: \"Give me the report for two "
          "weeks and I'll send you the summary on Friday. If it is wrong, we go back to daily "
          "checks.\" Name one thing you will deliver and one date, then deliver it - hovering "
          "usually comes from a manager who was caught out before, and evidence retires it faster "
          "than a complaint. If nothing changes, say what it costs: \"The checking is taking an "
          "hour a day. What would make you comfortable with less?\"",
          # "hover" on its own is not turned down: it is the word the complaint uses. Only the
          # things that hover, which are not a manager, are.
          avoid=("drone", "helicopter", "hoverboard", "hovercraft", "my mum", "my dad",
                 "my son", "my daughter")),

    entry("promoted-no-raise",
          (("promoted", "promotion", "acting up", "extra responsibility", "more responsibility",
            "doing two jobs", "covering for"),
           ("no pay", "no raise", "no money", "no extra money", "same pay", "no more money",
            "without a pay", "pennies", "nothing extra", "not paid")),
          "Say yes to the job and the money in the same conversation: \"Thank you - I'd like the "
          "role. Can we agree the salary for it before I start?\" Ask for the band the role pays "
          "rather than a figure you invent, and put the date it starts in writing. If they cannot "
          "move now, get a review date four to six weeks out with the number in it; extra work "
          "taken on a promise is how people end up doing two jobs for one salary.",
          avoid=("school", "exam", "class", "my son", "my daughter", "my child", "football",
                 "team was promoted", "league")),

    # One offer is the same decision as two: a job, a role or a promotion with a trade in it
    # ("more money but longer hours", "more travel") was a shrug on main, or - because
    # money-abroad keys a bare "money" beside a bare "travel" - holiday spending advice. The
    # answer is the same four columns whether one offer or two, so it is one entry, not a
    # second "job-offer-decision" table beside it.
    entry("two-job-offers",
          (("two job offers", "two offers", "job offer", "offer from", "offers from",
            "second offer", "two jobs", "the job", "a job", "this job", "new job",
            "the role", "this role", "a promotion", "the promotion", "offered a job",
            "offered a promotion", "offered the role"),
           ("which", "which one", "choose", "decide", "pick", "pros and cons", "both",
            "should i take", "should i accept", "should i say yes", "accept the offer",
            "accept the job", "turn down", "turn it down", "worth taking", "better paid",
            # A doubt about an offer in hand is the same decision said the other way round:
            # "im not sure about the job offer" was read as a result still coming and answered
            # "Then it's out of your hands now — when do you find out?", which is about waiting,
            # not about choosing. The doubt has to be about the job itself ("not sure about",
            # "not sure if", "not sure whether"), because "im not sure i want this job" is a
            # different sentence: it names no offer and it is already answered by what pulls
            # each way. "torn" and "in two minds" are left out for the same reason - the dither
            # pool weighs those better than a card about what the offer pays.
            "not sure about", "not sure if", "not sure whether", "unsure", "second thoughts",
            "not convinced",
            # the trade the offer is weighed by, named in the line itself
            "more money", "more pay", "more hours", "longer hours", "more travel",
            "less money", "pay cut",
            # the commute is the same trade priced in hours: "is the job 40 minutes further
            # worth it" was a punt on main, and it is the four columns again.
            "further", "further away", "commute", "commuting", "commute is", "travel further",
            "drive further", "an hour away", "an hour further", "20 minutes", "30 minutes",
            "40 minutes", "50 minutes", "an hour each way", "worth the journey",
            "worth the commute")),
          "Put four columns on paper: the money after the real extras - the season ticket, "
          "childcare and the extra hours at what your time is worth, because a rise that adds ten "
          "hours a week is often a pay cut - what you would learn in two years, who you would "
          "work for, and what happens if it goes wrong. Then take the offer that keeps more doors "
          "open, and ask for 48 hours rather than deciding on the call.",
          # the offer in hand, asked about in whatever words: see _A_WHAT_TO_DO_ASK
          shape=(_asks_what_to_do,),
          avoid=("my son", "my daughter", "my husband", "my wife", "house", "car",
                 "mortgage",
                 # a posting that already went to somebody else is not a decision to weigh:
                 # "i got turned down for a promotion" is the passed-over row's line, and it
                 # was given the four columns as if the person still had a choice
                 "turned down for", "turned me down", "got turned down", "passed over",
                 "passed up for", "someone else got", "gave it to someone else",
                 # an offer not yet in hand is a different question: "how do i get a job offer"
                 # and "how do i write a job offer letter" are things to do before or after the
                 # choice, and the shape above would otherwise reach them
                 "get a job offer", "getting a job offer", "land a job offer", "job offer letter",
                 "offer letter", "to get an offer", "before the offer", "job application",
                 "cover letter",
                 "went to someone else", "didnt get", "did not get", "wasnt promoted",
                 "was not promoted", "lost out",
                 # a job that has not started yet is the first day, and no offer is being
                 # weighed: "im starting a job on monday, any advice" was the four columns
                 "starting a job", "start my job", "starting my job", "start a job",
                 "starts a job", "job starts", "starts next week", "starts on monday",
                 "first day")),

    entry("job-affecting-mental-health",
          (("mental health", "my head", "anxiety", "anxious about work", "depressed about work",
            "crying about work", "crying before work", "dread work", "dreading work",
            "dread going in", "making me ill", "making me sick", "making me depressed",
            "making me anxious", "panic attack at work",
            # the body says it before the person names it: "i feel sick before work every
            # morning", "i cant face work", "stomach in knots about work".
            "feel sick before work", "sick before work", "feel ill before work",
            "cant face work", "can't face work", "dread going to work", "dreading going in",
            "stomach in knots", "butterflies about work", "shake before work"),
           ("work", "job", "boss", "office", "shift", "employer", "manager", "going in")),
          "Treat it as a work problem with a health cost, and act on both: tell your GP how it is "
          "affecting sleep, eating and mood, because a sick note and a few weeks off are normal "
          "and protect your job. At work, ask for the specific change that would help - fewer "
          "shifts, a different manager, a written plan - since adjustments are easier to say yes "
          "to than \"less stress\". If the job itself is the cause, start the exit plan now: "
          "CV, one application a week, and no resignation until you have something else.",
          avoid=("my son", "my daughter", "my child", "my wife", "my husband", "my mum",
                 "my dad", "my partner", "my friend", "my boyfriend", "my girlfriend",
                 "he feels", "she feels", "he is", "she is", "exam", "school", "university",
                 # a sum done in your head is not a job with a health cost: "how do i work
                 # out percentages in my head" was answered "treat it as a work problem
                 # with a health cost", because "my head" is in this row's key
                 "percent", "percentage", "percentages", "calculate", "arithmetic",
                 "maths", "fraction", "fractions", "average", "times table",
                 "times tables", "multiplication", "multiply", "divide", "convert",
                 "conversion", "in my head", "mental maths", "without a calculator",
                 "hurt myself", "end it all", "kill myself", "suicide", "no point going on",
                 "want to die",
                 # a dread of the next day is not the health-cost lecture: the card below is
                 # for the night-before lines, and this row keeps the chronic ones ("my job is
                 # making me ill", "i get panic attacks at work", "i dread work every morning").
                 "dread work tomorrow", "dreading work tomorrow", "dread tomorrow",
                 "dreading tomorrow", "dread monday", "dreading monday",
                 "dont want to go to work tomorrow", "don't want to go to work tomorrow")),

    # The same feeling at a different size. "I'm dreading work tomorrow" is a Sunday-night
    # question and got "tell your GP ... a sick note and a few weeks off ... start the exit plan
    # now": true for a job that is making someone ill, far too heavy for the night before a
    # Monday, and the person hears their life being rearranged as the first thing (STYLE.md,
    # careful in proportion). The size is in the words the person uses, so this card takes the
    # next-day shapes and the row above stands down for them by phrase.
    entry("dreading-work-tomorrow",
          # The idiom that names the feeling and not yet its object: "i get a sinking feeling on
          # sunday night", "the sinking feeling before work". The word "sinking" is a sink to the
          # reader of nouns, so the line reached nothing at all, and the second list still asks for
          # the job or the day, which is what keeps "i have a sinking feeling about tomorrow" on
          # the open question a scan or a funeral deserves.
          (("sinking feeling", "dread work tomorrow",
            "dreading work tomorrow", "dread tomorrow",
            "dreading tomorrow", "dread monday", "dreading monday", "monday dread",
            "monday morning dread", "sunday night dread", "sunday dread", "sunday scaries",
            "cant face it", "can't face it", "dont want to go to work tomorrow",
            "don't want to go to work tomorrow", "dont want to go in tomorrow",
            "don't want to go in tomorrow", "the thought of work tomorrow",
            "dread going in tomorrow", "dreading going in tomorrow", "dreading going back"),
           # the next day is the point: "i dont want to go to work today" and "i dont want to go
           # to work anymore" are not this card's question, and "i dread work every morning" is
           # the health-cost row's, which is why no bare "dread work" is in the key above.
           # The line also has to name the job. A bare "i dread tomorrow" is a funeral or a
           # scan as often as it is a shift, and the open question ("what's coming up?") is a
           # better answer than a plan for the morning; so a day word is only enough when the
           # phrase it is in is the job's own idiom (sunday night dread, the sunday scaries,
           # monday morning dread).
           ("work", "job", "office", "shift", "going in", "go in", "employer", "manager",
            "sunday night", "sunday scaries", "sunday dread", "monday morning", "monday dread",
            "the weekend over", "back at my desk")),
          "That dread is usually about one or two things rather than the whole week, so name the "
          "worst bit tonight and plan only for that. If it is one meeting or one person, decide "
          "now what you will say; if it is all of it, that is a bigger question than one Monday. "
          "Tonight: bag and clothes ready, the two jobs tomorrow starts with written down, and "
          "one thing in the day you actually want.",
          # a dentist, an exam or a flight tomorrow is a dread of that, not of the job
          avoid=("dentist", "doctors", "doctor", "hospital", "exam", "exams", "test", "tests",
                 "interview", "school", "college", "university", "flight", "appointment",
                 "appointments", "holiday", "christmas", "birthday", "party", "wedding")),

    entry("train-a-new-starter",
          (("new starter", "new start", "new colleague", "new person", "new hire", "the new one",
            "train someone", "training someone", "train them", "training them", "shadow me",
            "shadowing me", "mentor", "mentoring", "show them the ropes", "onboard"),
           ("while", "my own job", "my job", "my work", "no time", "extra", "as well",
            "how do i", "should i", "say no", "push back", "ask", "refuse",
            "keeps asking", "asks me", "asking me", "constant questions", "pulls me away",
            "all day", "every five minutes")),
          "Treat it as a task with hours in it rather than an extra you absorb: tell your manager "
          "how long the training is costing - \"Two hours a day for three weeks\" - and ask which "
          "of your own jobs should wait, or who covers it. Then make the training something the "
          "next person can reuse: one page of the ten things you actually do, a shared checklist, "
          "and thirty minutes a day of questions rather than all-day shadowing. Doing it well is "
          "visible and worth saying at your review - doing it silently is how people end up "
          "doing two jobs.",
          # a genuinely new starter's own first-day nerves are the first-day entry's line.
          avoid=("my first day", "first day at", "nervous about starting", "i start", "new job",
                 "i am the new", "im the new", "i'm the new")),

    entry("holiday-during-notice",
          (("holiday", "annual leave", "time off", "days off",
            # "can i take holiday during my notice period" put both halves in one phrase, and the
            # bare "holiday" plus "notice period" lost to the notice card by one point.
            "holiday during", "holidays during", "leave during", "time off during",
            "holiday in my notice", "holiday on my notice"),
           ("during notice", "during my notice", "in my notice", "notice period", "leaving",
            "last day", "on notice",
            # "i handed my notice in, what holiday do i get" says the notice once, as a verb:
            # with "holiday" already in the line, the bare word cannot be the letter.
            # Not the bare word: "do i have to give notice for holiday" is the allowance
            # question, so only notice that is the person's own is the letter.
            "my notice", "handed my notice", "handed in my notice", "handing in my notice",
            "hand my notice", "handing my notice", "gave my notice", "given my notice",
            "working my notice", "working out my notice",
            # "do i get paid for untaken holiday when i leave" is the accrued days, which this
            # answer already covers; without these the bank-holiday row took it.
            "untaken", "untaken holiday", "unpaid holiday", "holiday left", "accrued",
            "accrue", "when i leave", "when i go", "paid for holiday")),
          "You keep building holiday while you work your notice, and you can ask to take it - but "
          "whether you get it is your employer's call, because they can refuse leave for business "
          "reasons. If they say no, they pay you for the days you have accrued when you leave, so "
          "you are not losing them. Ask in writing with the dates, offer the handover for those "
          "days, and check your contract for a clause about notice and leave.",
          avoid=("where should i go", "hotel", "flight", "spain", "greece", "abroad",
                 "book a", "destination")),

    entry("pregnancy-at-work",
          (("pregnant", "pregnancy", "having a baby", "expecting", "maternity", "antenatal"),
           ("boss", "manager", "work", "job", "tell", "when do i", "how do i", "rights",
            "entitled", "leave", "appointment")),
          "You do not have to tell your employer until 15 weeks before the baby is due, and it is "
          "worth knowing that once you do, you are protected from being treated worse because of "
          "it. Tell your manager in a short meeting, then confirm the date in writing: your due "
          "date, when you plan to start maternity leave, and how the work will be covered. Ask "
          "for a risk assessment of your role, and remember antenatal appointments are paid time "
          "off - you do not book them as holiday.",
          avoid=("my wife", "my girlfriend", "my partner", "my sister", "my daughter",
                 "my parents", "my mum", "my dad", "my family", "my in laws", "my in-laws",
                 "my friend", "coworker", "colleague is", "she is pregnant", "is she",
                 # A cold, a cough or a headache in pregnancy is a health question, and the
                 # "how do i" and "tell" in it were enough for the maternity-rights card:
                 # "how do i treat a cold when pregnant" was told when to tell the boss. The
                 # illness words are checked first, so the health rows answer these.
                 "cold", "flu", "cough", "sore throat", "blocked nose", "headache",
                 "migraine", "paracetamol", "ibuprofen", "medicine", "medication",
                 "remedy", "symptoms", "nausea", "morning sickness", "heartburn",
                 "fever", "temperature", "covid", "infection", "antibiotics", "dizzy",
                 "vomit", "diarrhoea", "constipation", "rash", "itchy",
                 # a job that has not started yet is the first day, not the maternity rights:
                 # "i start my job next week, what should i expect" reached this row through
                 # "expect"/"expecting" and was told when to tell the boss about a baby
                 "starting a job", "start my job", "starting my job", "start a job",
                 "starts a job", "job starts", "starts next week", "starts on monday",
                 "first day",
                 "trying to get", "how do i get pregnant", "cant get pregnant",
                 "test negative", "miscarriage", "miscarried", "losing the baby",
                 # "expecting" is a loose form of "expected", so "my new job is not what i
                 # expected" scored the baby words and got the maternity answer. The phrase
                 # below only stands for the disappointed sentence, not for a pregnancy.
                 "not what i expected", "not what i thought",
                 # the money in maternity is `maternity-pay`, and this card answers none of it:
                 # "how do i claim maternity pay" was told when to tell the boss
                 "maternity pay", "statutory maternity pay", "smp", "maternity allowance",
                 "maternity leave",
                 # weight after a birth is a health question: "how do i lose weight after
                 # having a baby" was told when to tell the employer
                 "lose weight", "losing weight", "lose the baby weight", "baby weight",
                 "slim", "slimming", "diet", "dieting", "back in shape", "get in shape")),
    # The money in maternity: main had no card for it at all, so "how much maternity pay do i
    # get" was a punt and "when am i paid on maternity leave" was the tell-your-employer card,
    # which answers none of it.
    entry("maternity-pay",
          (("maternity pay", "statutory maternity pay", "smp", "maternity allowance",
            "pay on maternity leave", "paid on maternity leave", "paid while on maternity",
            "maternity money", "maternity wage"),
           ("how much", "how long", "how many weeks", "when", "claim", "apply", "eligible",
            "qualify", "entitled", "get paid", "be paid", "rate", "amount", "pay", "start",
            "does it start", "when does")),
          "Statutory maternity pay is 39 weeks: the first 6 weeks at 90 per cent of your average "
          "pay, then 33 weeks at about \u00a3187 a week in 2025-26. You qualify if you were on the "
          "payroll for 26 weeks before the baby is due and earn at least \u00a3125 a week. If you "
          "do not qualify, Maternity Allowance pays about the same for 39 weeks. Repaying it only "
          "comes in if your contract's own scheme says so.",
          # the child, the nursery and the tax are other answers, and so is the letter telling
          # the employer, which pregnancy-at-work owns
          avoid=("paternity", "shared parental", "adoption", "child benefit", "nursery",
                 "free hours", "tax free childcare", "when do i tell", "how do i tell",
                 "when should i tell", "pregnant", "pregnancy test")),

    # The other parent and the sharing: every way people asked about paternity and shared
    # parental leave was a punt, and "can i split my maternity leave with my partner" got the
    # pay-in-by-earnings card, which is about couples' money and not about leave.
    entry("paternity-leave",
          (("paternity leave", "paternity pay", "statutory paternity",
            "time off when the baby is born", "time off for the birth",
            "leave for the father", "leave for the dad", "second parent leave"),
           ("how much", "how long", "how many weeks", "weeks", "when", "claim", "apply",
            "eligible", "qualify", "entitled", "paid", "pay", "get", "rate", "amount",
            "take", "start", "can i")),
          "Statutory paternity leave is 1 or 2 weeks, taken in one go, and it has to be used "
          "within 56 days of the birth. You tell your employer 15 weeks before the due date. It "
          "pays about \u00a3187 a week in 2025-26, or 90 per cent of your average pay if that is "
          "less, as long as you have worked there for 26 weeks. Plenty of employers offer more - "
          "check your contract.",
          # the mother's own leave and money are the two rows above, and adoption has its own
          # pay and leave
          avoid=("maternity", "mother", "adoption", "adopting", "shared parental", "nursery",
                 "child benefit", "free hours", "tax free childcare", "pregnant")),

    entry("shared-parental-leave",
          (("shared parental leave", "shared parental pay", "split my maternity",
            "share my maternity leave", "split the leave", "share the leave",
            "both of us off", "partner take my maternity", "partner take my leave",
            "take my maternity leave", "partner share my leave", "partner have my leave"),
           ("how", "what", "how much", "how long", "weeks", "when", "claim", "apply",
            "eligible", "qualify", "entitled", "paid", "pay", "can i", "can my", "does it work",
            "split", "share")),
          "Shared parental leave lets you split up to 50 weeks of the mother's maternity leave, "
          "and 37 of those weeks are paid, if you are both eligible. The mother has to end her "
          "maternity leave early - after the 2 weeks she must take - and the rest of the leave "
          "and pay can then be shared in blocks. It has to be used within the first year after "
          "the birth, and you tell your employer 8 weeks before the first block.",
          avoid=("maternity pay", "statutory maternity pay", "paternity", "adoption", "nursery",
                 "child benefit", "free hours", "tax free childcare", "pregnant")),

    # How much leave there is, which is a different question from the money: "how long is
    # maternity leave" was answered with when to tell the boss, and the 52 weeks were nowhere.
    entry("maternity-leave",
          (("maternity leave", "how long is maternity", "leave after the baby",
            "time off when the baby", "how long off work"),
           ("how long", "how many weeks", "weeks", "start", "starts", "end", "ends", "finish",
            "finishes", "return", "go back", "early", "52 weeks", "how much time", "staff",
            # when to stop working is the same card's other half: "when should i go on
            # maternity leave" was a punt once the pay questions moved to their own row
            "go on", "go off", "when should i", "when can i", "when to", "stop work",
            "last day", "before the baby")),
          "Maternity leave is 52 weeks: 26 weeks of ordinary leave, then 26 of additional leave, "
          "and you can go back early if you give 8 weeks' notice. You have to take 2 weeks "
          "straight after the birth, or 4 if you work in a factory. Only 39 weeks of the 52 are "
          "paid. Tell your employer your due date and the date you plan to stop work 15 weeks "
          "before the baby is due.",
          # the money is the other row, and the telling is pregnancy-at-work's
          avoid=("pay", "paid", "money", "wage", "wages", "salary", "how much", "when do i tell",
                 "how do i tell", "when should i tell", "pregnant", "pregnancy test",
                 "shared parental", "adoption", "paternity")),
    # "how is holiday pay calculated" is the money question and it is not the days question:
    # `holiday-entitlement` counts the allowance, and the leave-request row answered the
    # calculation lines with "Ask early, name the dates".
    entry("holiday-pay", (("holiday pay", "holiday money", "paid for my holiday", "holiday wage"),
                          ("calculate", "calculated", "calculation", "work out", "worked out",
                           "how much", "how do i", "how is", "how are", "rate", "average",
                           "overtime", "commission", "shift", "irregular", "part time",
                           "leaving", "left", "owed", "untaken", "not taken")),
          "Your holiday is paid at your normal rate: what you would have earned on those days, "
          "not just basic pay - regular overtime, commission and shift pay count too. Add up what "
          "you were paid in the 52 weeks before, divide by 52, and that average week is what a "
          "week off pays; irregular hours work the same way. Leave you have not taken is paid out "
          "when you leave.",
          # "how much holiday do i get" is the days question and stays with the entitlement row,
          # and so is "how much holiday pay am i owed", which wants the figure rather than the sum
          avoid=("how many days", "how much holiday do i get", "how many holidays", "entitlement",
                 "am i owed", "owed to me", "was i owed",
                 # "how much holiday pay am i entitled to" is the allowance in weeks, which the
                 # entitlement row counts, and "claim holiday pay when i leave" is the notice
                 # question about building and taking it rather than the average week.
                 "entitled", "entitle", "when i leave", "i leave", "on leaving", "resign",
                 "resigning", "resignation", "notice period", "worked my notice",
                 "how do i ask", "ask for", "request", "book", "booking", "bank holiday",
                 "sick pay", "maternity", "paternity", "redundancy", "final pay", "payslip"),
          bias=1),
    entry("holiday-entitlement",
    (("holiday", "holidays", "annual leave", "paid leave", "days off", "bank holidays",
     # "leave" is the word most people type for the allowance ("how much leave do i have
     # left", "how many days leave am i entitled to"), and on its own it was the one
     # phrasing of the question the row could not reach: "annual leave" and "days off"
     # were answered with the 5.6 weeks, bare "leave" with the search hedge. The phrases
     # are the allowance shapes only, so "when do i leave", "leave my job" and "how many
     # days leave until christmas" are not this row's subject.
     "days leave", "much leave", "leave days", "leave left", "leave balance",
     "leave allowance", "leave entitlement",
     # the same question with the allowance only implied: "can i use the days i saved from
     # last year" names no holiday word at all, so the days themselves are the subject here
     "days saved", "days i saved", "saved days", "days from last year", "days carried over",
     "carried over days"),
    ("entitled", "entitlement", "how much", "how many days", "statutory", "minimum",
    # "how many days leave do i have left" asks the balance, which is the same question
    # with the number the person actually wants at the end of it.
    "left", "remaining", "do i have", "have i got", "balance",
    "legal", "owe me", "must i", "do i get", "count", "counts", "counted", "include",
    "included", "paid",
    # "do i have to work bank holidays" and "can they make me work them" are the same
    # question as "how much holiday do i get", and the bank-holiday words alone missed it
    "have to work", "work on", "work bank holidays", "work the bank", "force me",
    "make me work", "made to work", "which days", "do i have to", "can they", "days a week",
    # "can i carry holiday into january" is the carry-over rule, which the paragraph below
    # already speaks to and this row could not be reached for
    "carry", "carry over", "carried over", "carrying", "lose", "loses", "losing", "lost",
    "unused", "forfeit", "use it or lose",
    # The days kept back from an earlier year are asked for without any of the words above:
    # "i saved three days of holiday can i use them" and "i have 5 days holiday saved up from
    # last year" were a search hedge and a small-talk nod. The holiday word is already the
    # subject half of this key, so a money line cannot reach these.
    "saved", "saved up", "save them", "use them", "use the days", "use my days",
    "from last year", "from the year before", "left over", "leftover", "roll over")),
    _holiday_entitlement,
    # A holiday somebody is saving for is a trip they are paying for, and the allowance is not the
    # answer to it: "how much should i save for a holiday" got the 5.6 weeks, "how much should i
    # put away each month for a holiday" the same. The saving row in money.py answers the sum.
    # Imported here, not at the top: the guard is read once when this list is built, and keeping
    # the line inside the entry means the change never touches the import block, which is where
    # two branches on an older base collide.
    guard=lookup.saving_for_a_trip,
    # "how many days until i go on holiday" is a countdown to a date, not a question about the
    # allowance: the same two words ("holiday", "how many days") answered it with the figure.
    # A holiday abroad is not an allowance: "how much does a holiday to spain cost in august"
    # was answered with the 5.6 weeks, because "holiday" and "how much" are this row's two
    # words. The trip shapes stand it down so travel.py's own cost row answers; they are trip
    # shapes only, so "how much holiday do i get" and "can i carry holiday into january" stay.
    avoid=("sleeps", "countdown", "days to go", "till i go", "until i go", "till we go",
           # saving money for the trip is not the leave you have left: "how do i save for a
           # holiday" reached this row once "saved" became a key word here
           "save for", "saving for", "saving up for", "saved up for", "money for",
           "spending money", "holiday money", "pay for", "afford",
           # and the amount that gives it away: "i want to save 200 a month for a holiday" has
           # no "save for" in it, so the money words are the sum and the month
           "a month", "per month", "each month", "a week for", "a fortnight for",
           "standing order", "direct debit", "set aside", "put away", "putting by",
           "pounds", "quid", "£",
           # "lose" and "lost" are in this row's key so that "i lost 3 days of holiday" reaches
           # the carry-over rule, and body weight then came with them: "how do i lose weight for
           # my holiday" got the carry-over paragraph. A weight question is health.py's, so
           # those phrases stand this row down.
           "lose weight", "losing weight", "lost weight", "lose the weight", "lose a stone",
           "lose a few pounds", "lose some weight", "lose any weight", "lose 5 kilos",
           "lose 10 kilos", "lose belly fat", "lose body fat", "lose inches",
           # "how much does a holiday to spain cost in august" is a price question about a trip,
           # and "cost" or "price" anywhere in the line is that question rather than the
           # allowance one; "how much holiday pay am i owed" says pay, not cost.
           "holiday abroad", "cost", "costs", "price", "prices", "expensive", "cheap",
           # "do i get holiday pay when im made redundant" asks about the final payslip, not
           # the annual allowance: the pay row says what is owed on top of the figure, so the
           # allowance stands down for a line about a job that is going.
           "made redundant", "being made redundant", "redundant", "redundancy", "severance",
           "laid off", "job gone", "let go",
           "holiday price", "holiday deal", "holiday deals", "cheap holiday",
           "cheap holidays", "holiday budget", "spend on a holiday",
           "trip to", "week in", "weeks in", "nights in", "all inclusive", "package holiday",
           "package deal", "flight", "flights", "hotel", "hotels", "airbnb", "resort",
           "beach", "passport", "visa", "travel insurance",
           "until we go", "how long till", "how long until", "days till", "days until",
           "till my holiday", "until my holiday",
           # "how many days leave until christmas" is a countdown to a date and the leave
           # phrases above reach it, so the countdown shapes stand this row down.
           "leave until", "leave till", "leave til", "leave before", "leave to go",
           # A trip that went wrong is not the allowance: "how long have i got to complain
           # about a holiday" is the Package Travel deadline (28 days from getting home) and
           # it was answered with the 5.6 weeks, because the row's key is the bare word
           # "holiday" and the balance words ("have i got", "do i have", "left") let it reach
           # any line that mentions a holiday and then asks how much time there is. The
           # remedy words are what tell the two apart, and each of them is a complaint about
           # a trip rather than a question about the allowance.
           "complain", "complaining", "complained", "complaint", "complaints",
           "refund", "refunds", "refunded", "money back", "compensation", "rebook",
           "rebooked", "rebooking", "package travel",
           # The key carries "count", "counts", "how many days" and "days off" with a bias, so it
           # is wide enough to take lines another row already answers: a question about working
           # or being paid for a bank holiday belongs to `bank-holidays`, leaving belongs to
           # `holiday-during-notice`, and a phone or wifi line that happens to say "holiday"
           # belongs to the roaming row in technology.py. Those rows name their subject, so they
           # lose this one on the words alone and have to be let through. The phrases below are
           # those questions and no wider: "do bank holidays count towards my holiday" is an
           # allowance question, so it stays here.
           "work bank holiday", "work bank holidays", "work the bank holidays",
           "work the bank holiday", "make me work", "made to work",
           "paid for bank holiday", "paid for bank holidays", "paid for the bank holidays",
           "paid for the bank holiday", "bank holiday paid", "bank holidays paid",
           "is a bank holiday", "is the bank holiday", "how many bank holidays",
           "bank holiday off", "bank holidays off", "public holiday", "when i leave", "i leave",
           # "leaving" alone would be a loose form of "leave" in "annual leave", which is an
           # allowance question, so the leaving shapes are named.
           "im leaving", "am leaving", "leaving my job", "leaving the job", "leaving the company",
           # A notice that is the person's own, not the bare word: "do i have to give
           # notice for holiday" is still the allowance question.
           "my notice", "notice period", "handed my notice", "handing my notice",
           "hand my notice", "resignation", "internet", "data", "roaming", "phone", "wifi",
           "wi-fi", "mobile", "signal",
           # A holiday from paying is a break the lender grants, never the 5.6 weeks: "how do i
           # get a payment holiday on my loan" was answered with the annual leave figure, because
           # "holiday" and "how do i get" are this row's two words. The money a person owes is
           # what stands this row down, and money.py's payment-holiday row answers it.
           "payment holiday", "payment break", "holiday from my payments",
           "holiday from payments", "holiday on my loan", "holiday on my mortgage",
           "mortgage", "mortgages", "remortgage", "loan", "loans", "credit card",
           "credit cards", "overdraft", "overdrafts", "repayment", "repayments",
           "repaying", "debt", "debts", "arrears", "lender", "student loan",
           "car finance", "hire purchase"),
    # "if i work 4 days a week" is a rarer pair of words than the entitlement words, so the
    # flexible-working letter answered those lines instead of this row: both reach it with four
    # words, and the letter's key words are the rarer ones. Two ranks clear of it, and the ask
    # above still keeps the row to the lines that ask for the number.
    bias=2),

    entry('job-rejection', (('rejection', 'rejected', 'turned down', "didn't get",
                             'did not get', 'no luck', 'unsuccessful', "wasn't successful"),
          ('job', 'interview', 'application', 'role', 'position')),
          "That's disappointing, especially after an interview. When you're ready, ask for one line"
          ' of feedback ("was there anything I could strengthen for next time?") and use it on the'
          ' next application; most rejections are about fit or timing, not you.'),
    # the extra work a boss keeps adding is the timing answer below, not the boundary lesson in
    # `say-no-politely`: "my manager keeps adding projects to my list how do i say no" reached
    # both at the same rank, and the general one is earlier in the file.
    entry('say-no-work', (('say no', 'turn down', 'decline', 'refuse'),
          # the subject has to be the work, not the person: with 'boss' and 'manager' in the
          # key, "how do i say no to my boss without it being awkward" was coming here instead of
          # to say-no-politely, which is the boundary lesson that line is asking for.
          ('work', 'task', 'project', 'extra', 'request', 'told to', 'given')),
          'Say yes to the person and no to the timing: "I\'d like to help with that; I\'m on the'
          ' audit until Thursday, so I can start Friday, or drop something else if it\'s urgent."'
          ' That gives them a choice instead of a refusal, and it makes your workload visible.',
          bias=1),
    entry('boss-wants-chat', (('boss', 'manager', 'line manager'),
          ('wants a chat', 'wants to chat', 'wants a word', 'have a chat', 'quick chat',
           'chat with', 'panicking', 'worried', 'nervous', 'dread')),
          "Almost always it's one specific thing, not a sacking: a project, a change, a bit of"
          " feedback. Before you go in, write the three things you've delivered lately and one"
          " question you want answered, and ask at the start what it's about; walking in with notes"
          ' is what turns the panic into a normal conversation.',
          avoid=('how did we start', 'what did i ask', 'what did i say', 'first thing',
                 'start this chat', 'start of this chat', 'begin this chat', 'earlier')),
    entry('unfair-projects', (('projects', 'tasks', 'work', 'jobs'),
          ('boring', 'good projects', 'interesting', 'unfair', 'not fair', 'someone else', 'always me', 'better projects')),
          'Ask for one interesting piece by name, rather than for fairness in general: "I\'d like to'
          " own the migration in the next quarter; I've done the last two audits and want the"
          ' stretch." Then agree it in your one-to-one, and offer a swap so nothing is left'
          ' uncovered; managers respond to a plan, not a complaint.'),
    entry('one-to-one', (('one to one', 'one-to-one', '1 to 1', '1:1', 'catch up'),
          ('boss', 'manager', 'prepare', 'agenda', 'what to say', 'useful', 'bring', 'what')),
          'Bring three lines: what you did since last time, what you need help with, and one thing'
          " you want to be different. It's your meeting, not a report: the middle line is the one"
          ' that gets you support, and asking for it is what one-to-ones are for.'),
    entry('email-tone', (('email', 'message', 'reply'),
          # the tone word is what makes this an email question: "my boss ignores my emails" is
          # boss-silent's line, and an email about a specific thing is not a tone question
          ('rude', 'polite', 'tone', 'professional', 'angry', 'sounds', 'sounding', 'sound',
           'friendly', 'formal', 'blunt', 'harsh', 'awkward', 'politely', 'mistake',
           'apologise', 'apologize', 'sorry', 'firm')),
          'Say the ask in the first line, the reason second, and keep it to four sentences: "Could'
          ' you send the signed form by Friday? Finance needs it to pay the invoice this month."'
          ' Read it once as if you were annoyed and take out anything that could be read that way,'
          ' then send; the shorter the email, the less there is to misread.',
          # a message saying you are ill is the calling-in-sick answer, not an email-tone example
          avoid=('sick', 'ill', 'unwell', 'poorly', 'hospital', 'doctor', 'appointment',
                 'day off', 'holiday', 'resign', 'resigning', 'quitting', 'quit', 'notice',
                 'leaving', 'interview'),
          bias=1),
    entry('meetings', (('meeting', 'meetings'),
          ('useless', 'too long', 'shorter', 'agenda', 'run', 'waste', 'stop', 'too many', 'no time', 'back to back')),
          'Send an agenda 24 hours before with the decision you need, and start with it. If there'
          " isn't a decision to make, it's an email; if it's only updates, make it a 10-minute"
          ' stand-up. Ending on "who does what by when" is what stops the same meeting coming back'
          ' next week.'),
    entry('prioritise-work', (('prioritise', 'prioritize', 'time management', 'to do list', 'get everything done', 'organise my work', 'too many tasks', 'procrastinate', 'procrastinating', 'putting off', 'waste time'),
          ('work', 'day', 'how', 'best', 'help', 'tips')),
          'Each morning pick the one task that would make the day a good one, and do it before'
          ' email. Then batch the small things (messages, approvals) into two set times, and keep a'
          ' "later" list so you stop holding them in your head; most of the day\'s stress is'
          ' unfinished small things, not hard ones.',
          # revising, essays and coursework are the study entries' work, not the day job's
          avoid=('exam', 'exams', 'revise', 'revising', 'revision', 'revised', 'essay', 'coursework',
                 'dissertation', 'homework', 'test', 'mock', 'sats', 'gcse', 'a level'),
          bias=1),
    # A person learning a new job says "the ropes", not "learn": "learn the ropes quickly" and
    # "get up to speed at work" were both the study rows - a syllabus, a mark scheme, cover the
    # page and test yourself - because "learn" plus a job word was the only way in. The phrases
    # are the job, so the row reaches them without a separate work word.
    entry('learn-at-work', (('learn', 'training', 'course', 'upskill', 'get better',
                             'learn the ropes', 'the ropes', 'get up to speed', 'up to speed',
                             'pick up the job', 'learn the job', 'learn my job',
                             'learn a new job', 'get the hang of it'),
          ('work', 'job', 'at work', 'skill', 'new software', 'excel', 'manager', 'boss', 'ask',
           'the ropes', 'ropes', 'up to speed', 'the job')),
          'Pick the one task that slows you down most and learn just that: a 20-minute tutorial on'
          ' the one thing, then use it on real work the same day. Ask your manager for the training'
          ' budget by showing what it will save (a day a month, fewer errors); most budgets go'
          ' unspent because nobody asks.',
          # "how do i ask my manager to pay for a course" is a money question, not a learning one.
          avoid=('present', 'presenting', 'presentation', 'slides', 'talk', 'speech',
                 'pay for', 'paying for', 'who pays', 'fund', 'reimburse', 'expense',
                 'cover the cost', 'sponsor')),

    entry('course-funded', (('pay for', 'paying for', 'fund', 'funding', 'cover the cost',
                             'who pays', 'reimburse', 'sponsor', 'expense'),
                            ('course', 'training', 'qualification', 'certification', 'certificate',
                             'conference', 'exam', 'degree', 'masters', 'mba', 'workshop',
                             'night class')),
          'Ask in one short email framed as a business case: the course, the cost, the dates, and the'
          ' one thing at work it fixes - the report nobody can run, the system only you know. Say'
          ' what you will bring back and offer to show the team afterwards. If the budget is fixed,'
          ' ask for half of it, or for the study time instead, and ask again at the next budget'
          ' round rather than dropping it.',
          ask=('course', 'training', 'qualification', 'certification', 'certificate', 'conference',
               'exam', 'degree', 'masters', 'mba', 'workshop', 'night class'),
          # main's money-for-a-big-buy card grew the words "pay for" and outranked this one on
          # "how do i ask my manager to pay for a course", which is the employer's money
          bias=2),

    # "left me out of" is the same question as "left out of": "my boss left me out of the
    # meeting" was the resignation card, then a shrug, because the two words had a pronoun
    # between them.
    entry('boss-ignores', (('boss', 'manager', 'bosses', 'left out of', 'left me out',
                            'left me out of', 'left us out', 'out of decisions', 'last to know'),
          ('ignores', 'never replies', 'too busy', "won't listen", "doesn't listen", 'unavailable',
           'left out', 'left me out', 'left us out', 'out of decisions', 'not told', 'last to know')),
          'Put the ask in one message with a deadline and a default: "I need a yes or no on the'
          ' budget by Friday; if I don\'t hear back I\'ll go with the cheaper option." If it\'s urgent'
          " and they're swamped, ask their assistant or agree a 10-minute slot at the end of the"
          ' stand-up; chasing the same unanswered email harder rarely helps.',
          # a boss who never replies has its own entry (boss-silent); this one is about being
          # left out of what is going on
          avoid=('replies', 'reply', 'respond', 'response', 'silence', 'unresponsive', 'ghost',
                 'ignor', 'never answers', 'no answer', 'nothing back', 'gets back to me',
                 'get back to me', 'chasing', 'chased',
                 # "left out of" is the key, and it is also how a fridge line says what it
                 # means: "milk left out of the fridge overnight" is a food-safety question and
                 # this row answered it with the ask-your-manager-in-writing card.
                 'fridge', 'freezer', 'cupboard', 'larder', 'out of the fridge',
                 'out of the freezer', 'out of the cupboard', 'overnight', 'all night',
                 'leftover', 'leftovers', 'milk', 'chicken', 'rice', 'curry', 'thawed',
                 'defrosted',
                 # a rota has its own row, and "left me out of the rota" is how you get on it
                 'rota', 'rotas', 'roster', 'shift', 'shifts',
                 # "left out of" is in the key of a work row, so a line with no work in it was
                 # answered with advice about asking a manager in writing: "i feel left out of
                 # my friend group" got "put the ask in one message with a deadline and a
                 # default ... the budget by Friday". The people words are what stands it down;
                 # the friends' own row (`left-out-group`) answers those lines.
                 'friend', 'friends', 'mate', 'mates', 'group chat', 'family', 'sister',
                 'sister in law', 'brother', 'mum', 'mom', 'dad', 'mother', 'father',
                 'wife', 'husband', 'partner', 'girlfriend', 'boyfriend', 'flatmate',
                 'housemate', 'neighbour', 'neighbors', 'kids', 'children',
                 'school', 'playground', 'birthday')),
    # "how long should i wait before chasing a job application" was getting a postage answer.
    entry("chase-application",
          # no "interview" or "recruiter" here: an interview line is the interview entries' and
          # "should i ask for more money in an interview" is not a chasing question
          (("job application", "applied for a job", "application", "applied", "chase",
            "chasing", "follow up", "follow it up", "heard back", "no reply", "no answer",
            "vacancy"),
           ("how long", "wait", "should i", "when", "chase", "chasing", "follow up", "heard",
            "reply", "answer", "weeks", "week", "email", "again")),
          "Wait a week after the closing date, or two weeks after you applied if there was no "
          "date, then send one short email to the person named in the advert: which role it is, "
          "when you applied, one line on why you fit, and a polite ask for a timescale. One "
          "follow-up is keen and a second is a nuisance, so if that goes unanswered, put the "
          "application down and carry on applying - most rejections are a process that stalled, "
          "not a verdict on you.",
          ask=("apply", "applied", "application", "job", "interview", "recruiter", "role",
               "vacancy", "cv"),
          # wording's follow-up-email is the same score on a line like "how long should i wait
          # before chasing a job application", and the application is the one that helps
          bias=1,
          avoid=("grant", "visa", "passport", "school", "university", "rent", "loan", "housing")),

    # A hybrid car, a hybrid bike and a hybrid tea are not the flexible-working request: the
    # car words are what decides it, and without them "should i get a hybrid" was answered
    # "ask with a plan, not a preference".
    entry('flexible-work', (('flexible', 'work from home', 'remote', 'hybrid', 'four day week',
                             'part time'),
                            # Only the decision words are added here. The going-back and
                            # go-part-time phrasings were in this list too, and they took the
                            # how-to-ask lines ("how do i tell my boss i want to go part time")
                            # off the wording row that answers them with a script to say.
                            ('ask', 'request', 'boss', 'how', 'should', 'arrange',
                             'worth', 'is it worth')),
          "Ask with a plan, not a preference: which days, how you'll be reachable, what you'll"
          ' measure, and a three-month trial. Put it in writing after the conversation, and point to'
          ' the policy or to a colleague already doing it, because the answer is usually easier than'
          ' people expect.',
          avoid=('car', 'cars', 'hybrid car', 'petrol', 'diesel', 'drive', 'driving', 'mpg',
                 'engine', 'battery', 'bike', 'cycle', 'tea', 'bus', 'train')),
    # "can my employer make me work bank holidays" was answered with a roaming-data fact, and
    # "do i get bank holidays off" with a message template. Bank holidays are a leave question
    # with a rule of their own: they sit inside the 5.6 weeks, they are not an extra right.
    entry("bank-holidays",
          (("bank holiday", "bank holidays", "public holiday", "public holidays",
            "time and a half"),
           ("work", "working", "employer", "make me", "have to", "off", "entitled", "rights",
            "legal", "law", "paid", "pay", "refuse", "shift", "contract", "get"),
           ("get", "got", "day", "days", "extra", "time and a half", "double", "lieu",
            "christmas", "easter", "new year", "weekend")),
          "Not automatically: bank holidays sit inside your 5.6 weeks of paid holiday (28 days "
          "for a full-time job), they are not days on top of it, so whether you work them is "
          "whatever your contract says. If you do work one you get your normal pay unless the "
          "contract or a union agreement promises a premium or a day off in lieu, and there is no "
          "law that gives you the day back afterwards. Check the holiday clause before you argue, "
          "and if the business closes for the day, that day normally comes out of your leave.",
          # a bank-holiday word has to be in the line: "when do i get paid" is the payday question
          ask=("bank", "holiday", "holidays", "christmas", "easter", "public", "boxing day",
               "new year", "time and a half"),
          # "book a holiday", "request time off" and "holiday entitlement" have their own entries
          avoid=("book", "booking", "request", "how do i ask", "how to ask", "apply for", "left",
                 "carry over", "carry it over", "where should i go", "hotel", "flight", "abroad",
                 "annual leave request", "holiday request", "holiday form"),
          # main's money-for-a-big-buy card grew the words "extra pay" and now outranks this
          # one on "do i get extra pay for working bank holidays", which is this card's question
          bias=2),
    entry('presentation-work', (('presentation', 'present', 'talk', 'speak'),
          ('work', 'colleagues', 'meeting', 'conference', 'nervous', 'slides', 'team')),
          'Write the one sentence you want people to remember, then build three slides around it'
          ' and cut the rest. Practise out loud twice, standing up, timing it, and take a one-page'
          ' note instead of reading the slides; the first 30 seconds scripted and the rest in'
          ' headings is what keeps a talk calm.',
          # A talk you stand up and give is not talking to people: "how do i do small talk at
          # work" and "im terrible at small talk at work" both got the slides answer through
          # "talk" and "work", which is a different job with a different answer.
          avoid=('small talk', 'smalltalk', 'small-talk', 'chit chat', 'chitchat', 'mingle',
                 # a room where nobody talks to you is the making-friends question, not a talk
                 # you stand up and give: "nobody talks to me at work" got the three-slides card
                 'nobody talks', 'no one talks', 'nobody speaks', 'no one speaks',
                 'talks to me', 'speaks to me', 'ignores me', 'left out', 'lonely',
                 'dont talk to me', "don't talk to me", 'doesnt talk', "doesn't talk",
                 'conversation', 'chat to', 'chat with', 'awkward', 'what to say',
                 # a meeting you cannot get a word into is the meetings card, not the slides
                 'speak up', 'never speak', 'rarely speak', 'talked over', 'spoken over',
                 'get my point across', 'get a word in', 'in meetings', 'in the meeting'),
          # "who do i talk to about a problem at work" was answered with slides: a who-ask is a
          # route to a person, and the guard reads the shape rather than a list of wordings
          guard=_a_who_ask_is_a_route),
    # Speaking up in a meeting is not a talk and not a voice problem: "how do i speak up in
    # meetings" got the mumbling exercises and "how do i get my point across in meetings" got
    # nothing at all, because the tree held the presentation, the small talk and the nerves and
    # nothing about saying one thing in a room of people who already know each other.
    entry('speak-up-meetings',
          (('meeting', 'meetings', 'standup', 'stand-up', 'stand up', 'team call', 'video call',
            'conference call', 'group call', 'weekly call', 'team meeting', 'board meeting',
            # a "sit down" said as a thing ("a proper sit down with my manager") is a meeting;
            # the verb ("when i sit down") is not, and bare `sit down` would take the posture
            # lines, so only the noun phrases are here
            'a sit down', 'sit down with', 'sit down about', 'sit down and talk',
            'sit down to talk', 'proper sit down', 'sit down meeting',
            'meeting notes', 'in the meeting',
            # "speak up at work" names no room, and it is the same question as in one
            'speak up at work', 'speak up at', 'speak up in'),
           ('speak', 'spoke', 'speaking', 'speak up', 'say', 'saying', 'said', 'talk', 'talking',
            'contribute', 'contribution', 'comment', 'point across', 'get my point', 'opinion',
            'ideas', 'get a word', 'word in', 'interrupt', 'interrupts', 'interrupting',
            # Being talked over in a room is this question, whatever verb the person reaches
            # for: "i get spoken over in meetings all the time" names the meeting and then found
            # nothing at all, because 'spoken' is not 'speak' to the matcher.
            'talked over', 'spoken over', 'talking over', 'talk over', 'over me', 'over my',
            'interrupted', 'quiet', 'silent', 'silence', 'nothing', 'nervous',
            'scared', 'afraid', 'confident', 'jump in', 'chime in', 'butt in', 'air my',
            'say my bit', 'put my hand up', 'how do i', 'what do i say')),
          'Pick one thing to say before you go in and write it in a sentence on the agenda or a '
          'note: a question, a number, or "I can take that". Say it in the first ten minutes if '
          'you can - the first thing is the hard one and the rest get easier - and open with the '
          'ask rather than the run-up. If you get talked over, use their name and finish the '
          'point once: "Sorry, Martin, I hadn\'t finished - the number is 40, not 14."',
          bias=1,
          # a talk to the room, a pay conversation and a small-talk question each have their own
          # answer, and a meeting that is going badly is the boss question
          avoid=('presentation', 'present', 'presenting', 'slides', 'slide deck', 'speech',
                 'conference talk', 'talk to give', 'give a talk', 'keynote', 'wedding',
                 'small talk', 'smalltalk', 'chit chat', 'kettle', 'party',
                 'pay rise', 'raise', 'salary', 'promotion', 'appraisal', 'one to one', '1:1',
                 # this card is tactics for the person who is quiet; a manager asking about the
                 # team's silence is the other question, and "my team wont speak up in meetings"
                 # was getting this one. The person you manage in the line is the give-away.
                 'my team', 'our team', 'my staff', 'our staff', 'my reports', 'my report',
                 'my apprentice', 'my trainee', 'my new starter', 'one of my', 'people on my',
                 'someone on my', 'get them to speak', 'get him to speak', 'get her to speak',
                 'as a manager', 'im the manager', 'i am the manager', 'i manage',
                 'left out', 'left me out', 'my boss keeps', 'resign', 'quit', 'fired',
                 # "how do i speak up at work" is this question, but the voice lines are not it
                 'mumble', 'mumbling', 'too quietly', 'monotone', 'um', 'erm',
                 # "meeting" plus "how do i" covers every how-question about a meeting, and the
                 # running of one, the booking of one and the notes of one each have a better
                 # answer than in-the-moment tactics: two reviewers measured this row taking
                 # "how do i run a meeting" off a good answer and answering the setting-up of
                 # one with advice about speaking up in it
                 'book', 'booking', 'room', 'rooms', 'invite', 'invites', 'calendar', 'dial in',
                 'zoom link', 'teams link', 'set up a meeting', 'set up the meeting',
                 'run a meeting', 'run the meeting', 'running a meeting', 'chair', 'chairing',
                 'minutes', 'take notes', 'note taking', 'mute', 'unmute', 'screen share',
                 'share my screen', 'camera', 'recording', 'agenda document',
                 # an agenda is written, not said, and it has its own answer: "how do i write a
                 # meeting agenda" and "how do i write an agenda for a meeting" were taking this
                 # card, because only the two-word "agenda document" was in the list
                 'agenda', 'agendas', 'write an agenda', 'writing an agenda',
                 # a mistake said out loud is `own-a-mistake` ("tell the person affected before
                 # they find out, with the fix attached"), not the tactic for getting a word in:
                 # "how do i tell my boss about a mistake in a meeting" lost that answer
                 'mistake', 'mistakes', 'made a mistake', 'make a mistake', 'own up',
                 'mess up', 'messed up', 'screwed up', 'got it wrong', 'i was wrong',
                 # a pattern of being talked over is the behaviour conversation, not a tactic
                 # for one meeting: "my boss talks over me in meetings" has its own answer that
                 # says raise it privately, name the behaviour and keep dated notes
                 # the phrases keep "i get talked over in meetings" on this card, where the
                 # tactic is the answer, and take the third-person pattern off it
                 'talk over me', 'talks over me', 'talking over me', 'talked over me',
                 'talks across me', 'cuts across me', 'cuts me off', 'cut me off',
                 'keeps interrupting', 'keeps cutting in',
                 # confidence in a room is its own answer ("pick one small uncomfortable thing"),
                 # and so is disagreeing with the boss; the row held `confident` as a key word,
                 # so without this fence "how do i sound confident in a meeting" lost the
                 # confidence card to the speaking-up tactics
                 'confident', 'confidence', 'sound confident', 'more confident',
                 'disagree', 'disagreement', 'disagreeing', 'say no', 'saying no', 'says no',
                 'push back', 'pushback', 'turn it down'),
          # "stand up" is a body going upright as often as a meeting: a line where the
          # standing happens to the person is the dizzy answer's, not this tactic's
          guard=_the_room_and_not_the_verb_meet),
    # The fear that stops people speaking up is not the room, it is the answer going wrong:
    # "what if i get it wrong" after the meetings card had nothing to come back with, because a
    # follow-up is read with the line before it put back in front and this row answered that
    # twice - the repeat check threw the answer away and the turn went to a search punt.
    entry('meeting-goes-wrong',
          (('meeting', 'meetings', 'standup', 'stand-up', 'team call', 'video call',
            'conference call', 'group call', 'weekly call', 'board meeting', 'in the meeting',
            'speak up', 'speak up in', 'speak up at', 'presentation', 'stand up'),
           ('what if', 'what happens if', 'get it wrong', 'got it wrong', 'say the wrong thing',
            'said the wrong thing', 'mess up', 'messed up', 'mess it up', 'go blank', 'went blank',
            'blank', 'forget', 'forgot', 'stumble', 'stumbled', 'freeze', 'froze', 'embarrass',
            'embarrassed', 'embarrassing', 'panic', 'crash', 'stuff it up')),
          'Keep one sentence of recovery ready rather than a script: "Let me come back to that" '
          'or "I might have got that wrong - I will check and confirm", then move on to the next '
          'thing. Getting a number wrong and putting it right in the room reads as careful; going '
          'quiet reads as unsure. Everyone else is thinking about their own next line, not scoring '
          'yours, and the meeting moves on about ten seconds after you finish.',
          bias=1,
          # a job interview, an exam and a wedding speech are their own answers, and a meeting
          # that has already gone wrong with a boss is the working-relationship card
          avoid=('interview', 'exam', 'revision', 'wedding speech', 'best man', 'funeral',
                 'date', 'dating', 'first date', 'my boss keeps', 'bullying', 'bullied',
                 'mumble', 'mumbling', 'too quietly', 'monotone',
                 'book', 'booking', 'room', 'invite', 'calendar', 'dial in', 'zoom link',
                 'chair', 'chairing', 'minutes', 'take notes', 'mute', 'unmute', 'screen share',
                 'share my screen', 'camera'),
          ),
    # The other half of "talk": the two minutes at the kettle, not the ten minutes at the front
    # of the room. The party entry answers the party; this one is the office, where you see the
    # same people every day and the point is being easy to be around rather than interesting.
    entry('work-small-talk',
          (('small talk', 'smalltalk', 'small-talk', 'chit chat', 'chitchat', 'office chat',
            'awkward silence', 'break the ice', 'mingle', 'make conversation',
            'chatting to', 'chatting with', 'chat to people', 'talking to people'),
           ('office', 'work', 'colleagues', 'colleague', 'team', 'boss', 'meeting', 'kitchen',
            'kettle', 'lunch', 'desk', 'lift', 'coffee', 'nervous', 'hate', 'dread', 'awkward',
            'terrible', 'bad at', 'rubbish at', 'hopeless at', 'tips', 'how', 'what do i say',
            'what to say', 'start', 'strangers', 'new job')),
          'Ask about the thing you are both already in the middle of - the queue at the kettle, '
          'the meeting you have just left, the weather on the walk in - then give one detail of '
          'your own, so it is a swap and not an interview. "Did the bike get fixed?" is worth '
          'more than any clever line, and leaving after a couple of minutes is normal.',
          # the party, a date, a first phone call and a speech have their own answers
          avoid=('party', 'parties', 'wedding', 'first date', 'date', 'tinder', 'speech',
                 'toast', 'interview', 'presentation', 'slides', 'conference talk',
                 # a chat with the boss about something has an answer of its own, and a raise is
                 # the one people actually ask: "how do i chat to my boss about a pay rise" is the
                 # negotiating answer, not the kettle. The subject words are what make it real.
                 'pay', 'pay rise', 'raise', 'salary', 'wage', 'wages', 'money', 'promotion',
                 'appraisal', 'review', 'one to one', '1 to 1', 'hours', 'leave', 'holiday',
                 'flexible', 'flexible working', 'complaint', 'grievance', 'quitting', 'notice',
                 'resign', 'quit', 'redundancy', 'contract')),
    # "should i tell my boss i'm looking for another job" was getting an employment-advice
    # shrug. The answer is a rule about timing, not a fact about the law.
    entry("told-boss-new-job",
          # The bare "tell my boss" is not this situation: it names a person and a speech, and a
          # line that says only that is as likely to be about a shift swap as about leaving. With
          # a need read as a want it was answered "Not until you have a written offer you would
          # accept" - resignation advice to someone who may be asking about anything. The leaving
          # phrases below are the situation, and "should i tell my boss i'm looking for another
          # job" still says one of them.
          # "should i tell my boss I'm leaving" is the same timing question and names no search
          # at all, and "should i tell my boss i have another job" says the bare "another job":
          # with only the search phrases this row passed on both and the letter-writing row
          # answered one and the fallback the other. The how-to rows keep their own keys
          # ("how do i resign", "hand in my notice") in the avoid below.
          (("looking for another job", "job hunting", "applying for other jobs",
            "applying elsewhere", "interviewing elsewhere", "another job elsewhere",
            "new job lined up", "another job", "a new job",
            # "should i tell my boss i have another offer" says the offer rather than the job,
            # and passed the row: the deciding question ("should i take another offer") is
            # stood down in the avoid below, so the telling question can have the words.
            "another offer", "an offer in hand", "offer in hand", "another role",
            "got an offer", "have another offer", "have an offer",
            # "leaving my job" is not here: "i have to leave my job" is a person announcing a
            # resignation, not asking whether to tell anybody, and the stem makes "leave my job"
            # match it. "i'm leaving" is the telling question and cannot be confused that way.
            "im leaving", "i'm leaving", "i am leaving",
            "thinking of leaving", "thinking about leaving"),
           ("should", "should i", "do i", "have to", "honest", "before", "when", "offer",
            "notice", "loyal", "risky", "wise", "say", "tell", "resign", "leaving", "quit")),
          "Not until you have a written offer you would accept: telling early only gives them time "
          "to plan around you, and a search that stalls leaves you marked. The exception is a "
          "manager who would hear it from someone else anyway, and a reference you actually need. "
          "When you do say it, keep it to the news and the timing - \"I've accepted another role, "
          "here's my notice\" - and read your contract first for notice and any competitor clause, "
          "because that is what actually constrains you.",
          # a job-search word has to be in the line: "how do i tell my boss i have too much on"
          # is boss-too-much's question, and it says "tell my boss" like this one does
          ask=("another job", "job hunting", "job search", "new job", "elsewhere", "looking for",
               "applying", "applied", "interview", "leave", "leaving", "resign", "quit",
               "moving on", "offer"),
          # A line about STARTING a job is not a line about leaving one: "how do i settle into a
          # new job", "how do i fit in at a new job", "how do i make friends at a new job" and
          # "how do i remember everyones names at a new job" all said "a new job" and got
          # "Not until you have a written offer you would accept". The starting shapes stand this
          # row down and leave them to first-day, which is the same question. Not the bare
          # "start", because "should i tell my boss before i start looking" is this row's own
          # question.
          avoid=("settle in", "settle into", "settling in", "fit in at", "fit in with",
                 "make friends", "make mates", "remember names", "learn the ropes",
                 "learn the job", "learn my job", "first day", "first week", "day one",
                 "starting a new job", "start a new job", "starting my new job",
                 "just started at", "just started in", "started this week",
                 "started last week", "dont know anyone", "don't know anyone",
                 "new job and", "names", "everyones names", "peoples names",
                 # quitting, resigning and the notice period have their own entries on the how-to
                 "how do i resign", "how to resign", "write my notice", "notice period",
                 "garden leave", "reference", "counter offer", "counter-offer",
                 "hand in my notice", "hand my notice", "handing in my notice", "give notice",
                 "give my notice", "last working day",
                 # taking an offer is the deciding question, not the telling one
                 "take another offer", "take the offer", "accept the offer", "accept another offer",
                 "should i take", "should i accept", "should i stay", "turn it down",
                 "turn down the offer", "negotiate",
                 # a landlord is told the same thing in the same words - "how do i tell my
                 # landlord im leaving" is a notice letter, not a resignation, and this row took
                 # it on the phrase "im leaving" alone
                 "landlord", "landlords", "landlady", "letting agent", "letting agents",
                 "tenancy", "tenancies", "lease", "my flat", "my house", "my room"),
          # wording's quit-a-job-message is the same score on "should i tell my boss", and the
          # question here is the timing, not the four lines of the letter
          bias=1),

    # "what do i do if my employer hasnt paid me" passed on every entry: the pay entries are
    # all about reading a payslip or asking for a rise, and none of them is about a wage that
    # never arrived.
    entry("unpaid-wages",
          (("not been paid", "havent been paid", "haven't been paid", "hasnt paid me",
            "hasn't paid me", "has not paid me", "havent paid me", "didnt pay me",
            "didn't pay me", "no wages", "unpaid wages", "missed pay", "late pay", "short pay",
            "underpaid", "pay is late", "pay is short", "not paid on time", "wages are missing",
            # The same fact in the past tense was nowhere in the list, so "my pay was late
            # again" was a direct debit reminder: the verb after the wage is what moves, so
            # every tense of it is here.
            # The past tense was nowhere in this row, so "my pay was late" was a shrug and
            # "my pay was late again" a direct debit reminder: the verb after the wage is what
            # moves, so every tense of it is here. "pay was short" is left out on purpose - a
            # short payslip is payslip-short's question and that row answers it better.
            "pay was late", "pay came late", "pay arrived late", "pay went in late",
            "pay is running late", "pay was running late",
            "wages were late", "wage was late", "salary was late", "salary came late",
            # The row knew "pay is late" and "wages are late" but not the singular noun, and
            # "always" broke the phrase: "my wage is late" was a money refusal and "my pay is
            # always late" was a reminder to set up a direct debit, which is the opposite
            # question - that one is about a payment you owe.
            "wage is late", "salary is late", "pay is always late", "always late with my pay",
            "always late with my wages", "pay is never on time", "wages never on time",
            # a wage that was due when someone left is the same claim, and "they havent paid my
            # final wages" was answered with "thanks for telling me".
            "final wages", "final pay", "final payslip", "last wages",
            # "my pay didnt go in" was an acknowledgement: the key held "didnt go in" but the
            # ask did not, and the subject half wanted a noun the sentence did not have
            "pay didnt go in", "pay did not go in", "pay never went in", "pay never arrived",
            # "i got paid late again this month" is the same claim as "paid late", but the fee
            # row owns "paid late" + "late", so the wage needs the words around it to win.
            "got paid late", "paid late again", "was paid late", "were paid late",
            "money not in my account", "no pay this month", "wages are late", "pay is late",
            "paid late", "pay late", "pay hasnt come", "pay hasn't come",
            # The plainest way to say it is "i didnt get paid": the key said "didnt pay me",
            # which is the same fact in a word order most people do not use, so the line fell
            # through to an acknowledgement. "missed payday" and "still not paid" are the same
            # line a week later, and "arrived", "turned up" and "gone in" are how a person
            # talks about the money rather than the date.
            "didnt get paid", "did not get paid", "didnt get my pay", "not getting paid",
            "havent got paid", "still havent got paid", "missed payday", "missed my payday",
            "still not paid", "still waiting to be paid", "late paying me", "owes me",
            "withheld my pay", "withholding my pay", "paid short", "paid me short",
            "havent arrived", "hasnt arrived", "didnt arrive", "never turned up",
            "havent turned up", "not turned up", "hasnt gone in", "havent gone in",
            "didnt go in", "hasnt come through", "havent come through", "not come through",
            "no money in my account", "nothing in my account", "wages havent", "pay hasnt",
            "gone into my account", "not gone into", "not in my account",
            # The passive with no "get" in it, and the money that simply never came: both are
            # the same fact as "i didnt get paid", and neither was in the list, so
            # "i wasnt paid" was an acknowledgement and "my pay never came" was a shrug.
            "wasnt paid", "wasn't paid", "were not paid", "werent paid", "was not paid",
            "pay never came", "wages never came", "pay has never come", "wage never came",
            # the same fact about somebody else - "my sister hasnt been paid" is asked by the
            # person helping, and "hasnt been paid" was missing while "not been paid" was there
            "hasnt been paid", "hasn't been paid", "havent been paid yet", "hasnt been paid yet",
            "not been paid yet", "still hasnt been paid",
            # A wage that never came is said with "had", "received" and "got" as often as
            # with "paid", and "i havent had my holiday pay", "i still havent had my wages"
            # and "my holiday pay is missing" were each answered with something else. The
            # verb alone is a lunch, a haircut or a holiday, so the verb and the pay are
            # written together above, once for every verb and every pay noun.
            ) + _UNPAID_WAGE_PHRASES,
           ("what do i do", "what should i", "how do i", "can i", "claim", "who do i",
            "employer", "boss", "work", "agency", "month", "week", "wages", "pay", "owed",
            "unpaid", "late", "short",
            # "again", "yet" and "today" are the words that carry the lateness with no other
            # signal in it: "my pay was late again" is two words and a mood, and the row was
            # one position short of answering it.
            "again", "yet", "today", "yesterday", "still", "overdue", "always", "wage",
            # the row's `ask` needs the lateness in the tense the person used: it held
            # "pay is late" and "paid late" but no past tense, so "my pay was late" was a
            # shrug even with the phrase in the key
            "pay was late", "wages were late", "wage was late", "salary was late",
            "pay was short", "pay came late", "pay arrived late", "pay is running late",
            # the noun a wage is owed under: a bonus, commission or holiday pay is the same
            # claim as a wage, and "i didnt get my bonus" was a sympathy line
            "bonus", "holiday pay", "commission", "earnings", "income", "pay packet",
            "paycheck", "payslip", "payslips",
            # "i didnt get paid on payday" carries the lateness and nothing else, so the payday
            # has to count as the subject: without it the line scored 3, which is under the
            # minimum, and the reply was an acknowledgement.
            "payday", "paid", "salary")),
          "Put it in writing today: the dates, the hours and the amount you should have had, "
          "sent to your manager and to payroll, and keep a copy - a text or email is a record, a "
          "phone call is not. Check your contract for the pay date and take screenshots of your "
          "payslips and bank account. If the next payday also misses, ring ACAS's free helpline "
          "and ask about a claim for unauthorised deductions at an employment tribunal, which you "
          "have three months less a day from each missed payment to start. If the company has "
          "stopped trading, the Insolvency Service can pay what you are owed.",
          # a bill nobody has paid and a payment plan are other entries' lines. "landlord",
          # "rent" and "tenancy" are not: "i owe my landlord rent and my wages are late" is a
          # wage that did not arrive, and holding the word out sent it to the money hedge.
          avoid=("bill", "energy", "water", "council tax",
                 "credit card", "loan", "invoice from", "my client", "child maintenance",
                 # money somebody owes you back is not a wage that did not arrive, and the
                 # person is not the signal: "my sister hasnt been paid" is her wages, so the
                 # lending words carry the friend who has not paid you back and the relatives
                 # are not listed. "the company owes me two weeks pay" is a wage, so "owes me"
                 # is not here either.
                 "friend", "friends", "lent", "lend", "borrowed",
                 "my mum", "my mom", "my dad", "boyfriend", "girlfriend", "flatmate",
                 "housemate", "roommate",
                 # A passport, a parcel or a letter that has not arrived is not the pay: those
                 # lines share "hasnt arrived", "late" and "weeks" with this entry, and
                 # "my passport hasnt arrived and its been 3 weeks" got the payroll letter.
                 "passport", "visa", "driving licence", "parcel", "package", "delivery",
                 "amazon", "order number", "letter hasnt", "email hasnt", "reply hasnt",
                 "refund", "money back", "cashback",
                 # a benefit that has stopped is not a wage that did not arrive, and it shares
                 # "havent been paid", "hasnt come through" and "not this month" with this row
                 "child benefit", "benefit", "benefits", "universal credit", "tax credits",
                 "pension", "pip", "esa",
                 # the hours were worked and the rate is the question, not the payday
                 "overtime",
                 # a pay rise that has not come is an argument about the rate, not a wage that
                 # did not arrive: "i havent had a pay rise in years" is the same words as
                 # "i havent had my pay" once the stopwords are read past, so the rise is
                 # named here and the rate rows keep the line. Not a bare "raise": a grievance
                 # is raised.
                 "pay rise", "pay increase", "a rise", "a raise", "get a rise", "get a raise",
                 "promotion", "promoted", "pay review", "pay award", "inflation",
                 "cost of living", "pay gap", "underpaid compared",
                 # "didnt arrive" and "never turned up" are how people talk about a parcel, a
                 # suitcase and a takeaway too: "my suitcase didnt arrive what do i do" was
                 # told to write to payroll. A thing that has not come is the travel, the shop
                 # or the delivery answer's line, not a wage.
                 "suitcase", "luggage", "bag", "bags", "rucksack", "parcel", "parcels",
                 "package", "delivery", "courier", "order", "takeaway", "pizza", "food shop",
                 "shopping", "flight", "plane", "train", "taxi", "sofa", "bed", "mattress",
                 "washing machine", "fridge", "freezer", "oven", "furniture", "item", "goods",
                 # the same phrase is how people talk about a passport, a visa and a bank card:
                 # "my passport hasnt arrived and its been 3 weeks" reached payroll because
                 # "weeks" was the second signal
                 "passport", "visa", "despatch", "dispatch", "driving licence", "application",
                 "reference number", "replacement", "refund", "statement"),
          # "i didnt get paid on payday" scores the same as paid-weekly's budgeting answer, on
          # "payday" and "paid"; the wage that never arrived is the answer that line wants
          bias=2,
          # The wage is the subject, so the line has to name one. "landlord", "rent" and
          # "tenancy" came out of the avoid list so that "i owe my landlord rent and my wages
          # are late" could be answered here, and without this a rent line that says "late" and
          # "paying" was answered with the payroll letter: "im always late paying my rent" got
          # "put it in writing ... to payroll ... ACAS ... employment tribunal".
          ask=("wage", "wages", "salary", "payday", "employer",
               "boss", "agency", "paid", "unpaid", "underpaid", "owed", "owe me", "owes me",
               "hours", "month", "week", "weekly", "job", "gone in", "come through",
               "arrived", "arrives", "came", "come", "turned up", "pay is late", "pay late",
               "paid late", "pay hasnt", "pay hasn't", "not in my account",
               "nothing in my account",
               # the ask is the lateness, and it only knew "is late" and "paid late", so a
               # line that said "was late" was turned away one tense short of the answer
               "pay was late", "pay came late", "pay arrived late", "pay went in late",
               "pay is running late", "pay was running late", "wages were late",
               "wage was late", "salary was late", "salary came late",
               "wage is late", "salary is late", "pay is always late", "final wages",
               "final pay", "didnt go in", "did not go in", "never went in", "always late",
               "got paid late", "paid late again", "was paid late", "were paid late",
               # "pay" and the nouns it is owed under: a bonus or holiday pay is a wage, and
               # the key above now reaches lines that name one.
               "pay", "bonus", "holiday pay", "commission", "earnings", "income")),

    # "should i take a pay rise or more holiday" was a shrug about a trade people really weigh.
    entry("pay-rise-or-holiday",
          (("pay rise", "raise", "more money", "money", "salary"),
           ("more holiday", "more annual leave", "extra holiday", "extra days", "time off instead",
            "instead of", "or holiday", "holiday or", "which is better", "whats better",
            "or more")),
          "Take the money if the rise is permanent: it lifts your pension, sick pay, overtime rate "
          "and every future offer, while extra days stop when the job does. Work out what a day is "
          "worth first - a day of holiday is about half a per cent of your salary, so five extra "
          "days is roughly 2.5% - and if they are offering the days instead of a rise, that is a "
          "smaller offer than it looks. The exception is a job that is burning you out: take the "
          "days, because nobody gets a good reference for being tired.",
          ask=("holiday", "leave", "days", "instead", "better"),
          avoid=("bank holiday", "public holiday", "who is off", "day off", "sick")),

    # "what is a good salary for a graduate" reached nothing at all.
    entry("graduate-salary",
          (("graduate", "graduates", "graduate salary", "graduate pay", "graduate scheme salary",
            "salary for a graduate", "normal salary", "average salary in the uk",
            "average salary for", "salary for a",
            "salary after uni", "what should i earn", "graduate job pay", "starting salary",
            "good salary", "decent salary", "is 30k a good salary", "is 25k a good salary",
            "is 35k a good salary", "average salary"),
           ("graduate", "uni", "university", "starting", "start", "first job", "good", "decent",
            "average", "normal", "much", "what", "how", "is", "earn", "should", "get")),
          "A graduate job in the UK usually starts around £25,000 to £30,000, with London and the "
          "big finance, law and tech employers at £35,000 to £45,000, and small charities, media "
          "and museums nearer £22,000. Judge an offer on the whole package - pension match, paid "
          "training, travel, and the hours - and on what the first two years teach you, because "
          "that sets the salary after them. A lower start where someone senior actually trains you "
          "usually beats £2,000 more where nobody does.",
          avoid=("salary sacrifice", "car", "teacher", "nurse", "doctor", "apprentice")),
    # "how do i ask for more holiday" reached nothing: the entitlement answer is about the legal
    # minimum, and this is the ask. The booking question is the holiday one, so the words that
    # make it a request are the key here.
    entry("more-holiday",
          (("more holiday", "extra holiday", "more annual leave", "extra annual leave",
            "more days off", "ask for holiday", "ask for more holiday", "buy extra holiday",
            "buy holiday", "unpaid leave", "more time off", "extra days off",
            "holiday request", "request holiday"),
           ("ask", "how", "can i", "should", "request", "get", "buy", "negotiate", "best way",
            "much", "many", "extra", "more")),
          "Ask in writing, by email, with the dates you want and why: a short line about the "
          "weeks you would like off and what you will have finished before you go beats a case "
          "about fairness. Before you send it, check the staff handbook for a buy-more-holiday "
          "scheme - many employers let you trade up to five days out of salary once a year - and "
          "ask what the notice period is. If the answer is no now, ask what would make it a yes "
          "next year and get that in writing, or offer to take the days unpaid.",
          # the legal minimum, a sick day and the pay rise instead of holiday are other answers
          avoid=("entitled", "entitlement", "statutory", "how many days am i", "bank holiday",
                 "public holiday", "sick", "sickness", "pay rise or", "instead of a pay rise")),

    # --- what a redundancy is worth, a second job, and an accident at work --
    entry("redundancy-pay",
          (("redundancy pay", "redundancy money", "redundancy package", "severance",
            "statutory redundancy", "made redundant", "being made redundant", "redundant",
            "laid off",
            # the same loss said without the word "redundant": "what am i entitled to when i
            # lose my job" was the forgetting card, because "lose" is the word it knows, and
            # "what do i get if im made redundant" was the next-steps card with its sympathy
            "lose my job", "losing my job", "lost my job", "lose my job", "job gone",
            "jobs gone", "being let go", "let go",
            # and the question that names the figure without naming the event twice over
            "redundancy rights", "redundancy entitlement"),
           ("how much", "owed", "entitled", "am i due", "pay", "paid", "money", "calculate",
            "work out", "offer", "package", "years", "service", "notice",
            "holiday", "what am i",
            # "what do i get" is the commonest way of asking for the figure, and the row had
            # only "how much" and "what am i": "what do i get if im made redundant" was the
            # next-steps card, whose whole answer assumes the person has the letter in hand
            "what do i get", "what will i get", "what would i get", "do i get", "will i get",
            "am i getting", "i get", "getting")),
          "Statutory redundancy pay is half a week's pay for each full year under 22, one week "
          "for each year from 22 to 40, and one and a half weeks for each year over 41, capped at "
          "£700 a week and 20 years, so the maximum is £21,000 and many people get a good deal "
          "less. On top of it you are owed your notice or pay in lieu, any holiday you have not "
          "taken, and your final wages, and if 20 or more people are going at once there has to "
          "be 30 days of consultation. Check the offer against the statutory figure before you "
          "sign anything, because a settlement agreement usually pays more in exchange for you "
          "giving up the right to claim - take free advice from ACAS or a union first.",
          ask=("how much", "owed", "entitled", "pay", "paid", "money", "calculate", "work out",
               "offer", "package", "week", "weeks", "years", "service", "notice", "holiday",
               "what am i", "due",
               # the entitlement ask, in the words people use for it: "what do i get", "what am
               # i owed", "am i entitled to anything". The key still has to name the job loss,
               # so the word "get" cannot drag an unrelated line in here - only the whole ask
               # is listed, since a bare "i get" also sits inside "how do i get over losing my
               # job", which is the comfort-and-next-steps card's line.
               "what do i get", "what will i get", "what would i get", "do i get", "will i get",
               "entitled to", "am i owed", "what am i owed",
               # "week" and "weeks" are gone: half a week's pay is what the card says, and the
               # word was catching the date instead - "i lost my job last week" is a person
               # saying what happened, and it was quoted the statutory figure. "pay" holds the
               # lines that really ask, and the weeks they ask about are counted by "how many
               # weeks", "weeks pay" and "per week".
               "how many weeks", "weeks pay", "weeks of pay", "per week", "weeks redundancy"),
          # the feelings and the next steps are the redundancy answer, and a boiler is not a job
          avoid=("boiler", "car", "engine", "cake", "feel", "feeling", "scared", "worried",
                 "anxious", "what do i do", "next", "cv", "interview",
                 # getting over it is the comfort card's question, and "how do i get over
                 # losing my job" was quoted the statutory figure once the job-loss words
                 # reached the key of this row
                 "get over", "cope", "coping", "deal with", "move on", "moving on",
                 # the three questions about the same money that are not the figure: what
                 # HMRC does with it, whether leaving of your own accord gets it, and what
                 # happens when you are off sick. Each has its own row below.
                 "tax", "taxed", "taxes", "taxable", "tax free", "after tax",
                 "if i quit", "if i resign", "if i leave", "resign", "resigning", "quit",
                 "quitting", "hand in my notice",
                 # "voluntary redundancy" was in this list and made the offer question a
                 # resigning question; the offer is the figure's line, so it is out.
                 "off sick", "on sick leave", "sick leave", "sickness", "long term sick",
                 "sick note", "signed off"),
          # A detail that says how long they were there is a question about the figure, and on
          # "redundant ive been there 6 years" both rows match: the next-steps row carries the
          # event's verbs ("been", "was", "got") and won the tie, so the follow-up to "im being
          # made redundant" answered "Same as before: ..." instead of the statutory figure.
          bias=1),
    # The tax question about the same money. "is redundancy pay taxed" and "do i pay tax on
    # redundancy pay" were answered with the statutory figure, which never says what happens
    # to it at HMRC; the words a person types for the money are still the key, and "tax" is
    # what makes it this row's line rather than the figure's.
    entry("redundancy-pay-tax",
          (("redundancy pay", "redundancy payment", "redundancy money", "redundancy package",
            "severance", "statutory redundancy", "made redundant", "being made redundant",
            "redundant", "laid off", "lose my job", "losing my job", "lost my job", "job gone",
            "let go"),
           ("tax", "taxed", "taxes", "taxable", "tax free", "tax-free", "after tax",
            "do i pay tax", "does hmrc", "hmrc", "payslip", "gross", "net",
            # the shape of the question as people type it: "how much tax do i pay on
            # redundancy pay" is the 30,000 question, and the take-home-pay row keys "how much"
            # and "pay" and was taking it on score alone (lemon-otter's review)
            "how much tax", "taxed on", "tax on", "tax bill", "take home")),
          "The first \u00a330,000 of a redundancy payment is tax free, and anything above that is "
          "taxed at your usual rate - so most people pay nothing on it at all. The \u00a330,000 "
          "counts the whole package, not just the statutory part, and pay in lieu of notice "
          "and holiday pay are taxed as ordinary wages. If payroll takes tax off the whole "
          "thing, compare it with that figure and ask them to show you the working.",
          ask=("tax", "taxed", "taxes", "taxable", "tax free", "tax-free", "after tax",
               "do i pay tax", "hmrc", "gross", "net"),
          # "how much tax do i pay on redundancy pay" is the take-home-pay row's shape - it
          # keys "how much" and "pay" - and it was winning this line on score alone. The words
          # of the money are in this row's key, so the row that holds the 30,000 comes first.
          bias=4),
    # Leaving of your own accord is the question the figure's row read as its own: "do i get
    # redundancy pay if i quit" was told how much statutory pay is worth, which is not what
    # happens when you resign. The key still needs the money's words, so "i quit smoking" is
    # nothing to do with this row.
    entry("redundancy-if-you-quit",
          (("redundancy pay", "redundancy money", "redundancy package", "severance",
            "statutory redundancy", "made redundant", "being made redundant", "redundant",
            "laid off"),
           # The act of leaving, and not the word "voluntary": "should i take voluntary
           # redundancy" and "im being offered voluntary redundancy" are a person with an
           # offer to weigh up, not a person asking what resigning pays, and the words of the
           # offer are the next-steps card's (lemon-otter's review). The leaving verbs are what
           # this row is for.
           ("if i quit", "if i resign", "if i leave", "if i hand in", "resign", "resigning",
            "resigned", "quit", "quitting", "hand in my notice", "hand my notice in",
            "walk out")),
          "No - redundancy pay is for a job that is going, not for you leaving, so resigning "
          "gets you your notice and any holiday you have not taken but no statutory redundancy "
          "pay. Voluntary redundancy is the exception: if the company offers it and you put "
          "your hand up, you get the same package. If you are being pushed towards the door, "
          "ask for a settlement agreement in writing and get free advice from ACAS or a union "
          "before you hand in notice.",
          ask=("if i quit", "if i resign", "if i leave", "if i hand in", "resign", "resigning",
               "resigned", "quit", "quitting", "hand in my notice", "hand my notice in",
               "walk out"),
          bias=1),
    # Being off sick when the job goes is asked as an employer question, and it reached no row
    # at all: "can my employer make me redundant while im off sick" was a shrug. The event's
    # own words are the key and the illness is the ask, so the figure's row stands aside.
    entry("redundancy-while-off-sick",
          (("made redundant", "being made redundant", "redundant", "redundancy", "laid off",
            "job gone", "let go", "sacked"),
           ("off sick", "on sick leave", "sick leave", "sickness", "long term sick",
            "sick note", "signed off", "while im ill", "while i am ill", "off work sick",
            "hospital", "depression", "stress")),
          "Yes - being off sick does not stop your job going, but the selection still has to "
          "be fair and they should talk to you about it rather than post the letter. Time off "
          "for pregnancy, maternity leave, or because you raised a safety or whistleblowing "
          "concern is protected, so a redundancy that is really about those is unfair. Keep "
          "the sick notes, ask for the reason in writing, and have ACAS or a union rep look "
          "at it while the clock is still running.",
          ask=("off sick", "on sick leave", "sick leave", "sickness", "long term sick",
               "sick note", "signed off", "while im ill", "while i am ill", "off work sick"),
          bias=1),
    entry("second-job",
          (("second job", "two jobs", "another job", "extra job", "side job", "moonlight",
            "second income", "work two jobs", "evening job", "weekend job"),
           ("can i", "allowed", "take", "get", "start", "do", "tax", "taxed", "contract",
            "employer", "hours", "legal", "ok", "okay", "worth it", "money", "afford")),
          "Usually yes: nothing in law stops you working two jobs, and what decides it is your "
          "contract, which often asks you to get permission or bans working for a competitor. "
          "Check the hours clause and the working time opt-out too, because the 48-hour average "
          "covers both jobs together. Tell HMRC rather than your boss - your tax-free allowance "
          "sits on one job and the second is taxed at basic rate from the first pound, so expect "
          "about 20% off it, and if either job brings you below the threshold you may be able to "
          "claim some back. Keep the two sets of hours apart on paper: the commonest problem is "
          "not the tax but the second employer finding out you are exhausted.",
          ask=("can i", "allowed", "take", "get", "start", "tax", "taxed", "contract",
               "employer", "legal", "ok", "okay", "worth it"),
          avoid=("interview", "second interview", "second round", "reference", "holiday",
                 "side hustle", "sell", "etsy", "business",
                 # "tax" is one of the ask words because "can i get a second job, what about
                 # tax" is this question, but a line that says it owes tax, or asks how to
                 # declare the money, is the tax table's: "i owe tax on a side job" and "do i
                 # need to declare a side job" were both told what a contract may say about
                 # second jobs, which is not what either of them asked.
                 "owe tax", "owes tax", "owed tax", "declare", "declaring", "declaration",
                 "undeclared", "declare it", "declare the income", "declare earnings",
                 "hmrc", "tax return", "self assessment", "tax bill", "how much tax"),
          # "can i get a second job to pay off debt" tied with the debt order, which is the
          # wrong half of the question: the job is what was asked about
          bias=1),
]

# A stall at a school fair or a charity bake sale is not a food business, so the register below
# is not the answer for that line: the one-off is said first, and what to do if it turns into a
# regular thing comes after it. Both halves are one reply because a person asking about their
# first cake sale wants to know they are not registering anything.
_ONE_OFF_STALL = re.compile(r"school fair|school fete|fete|fayre|cake sale|bake sale|charity|"
                            r"coffee morning|one off|one-off|village hall|church hall|"
                            r"a stall at|table top sale")
_SELL_FOOD_REPLY = (
    "No licence, but the kitchen has to be registered: tell your council's environmental "
    "health team at least 28 days before you sell anything, and registering is free. They "
    "may inspect the kitchen, so keep it clean, separate from pets, and able to keep food "
    "cold. You also need a Level 2 food hygiene certificate (about GBP 10 to GBP 20 online), "
    "allergen labels on anything you wrap up, and public liability insurance, which is cheap. "
    "Tell HMRC once you sell more than GBP 1,000 a year.")


def _sell_food_from_home(memory, understood):
    """The kitchen register, or the one-off stall when the line names one."""
    text = str((understood or {}).get("clean") or "").lower()
    if _ONE_OFF_STALL.search(text):
        return ("A one-off stall - a school fair, a charity bake sale, a fete - is not a food "
                "business, so nothing has to be registered: keep it clean, keep it cold, label "
                "the allergens and you are done. Selling regularly from home is the free "
                "council kitchen register at least 28 days ahead, with a Level 2 hygiene "
                "certificate and public liability insurance after that.")
    return _SELL_FOOD_REPLY


ENTRIES.append(entry(
    "sell-food-from-home",
    (("sell food", "selling food", "sell cakes", "selling cakes", "sell bakes", "selling bakes",
      "sell bread", "sell jam", "sell chutney", "sell preserves", "sell meals", "sell dinners",
      "cook for money", "bake for money", "catering", "food business", "food from home",
      "cakes from home", "baking from home", "cooking from home",
      "farmers market", "market stall", "food stall"),
     ("licence", "license", "licenced", "registered", "register", "registration", "permit",
      "allowed", "legal", "hygiene", "certificate", "inspection", "inspected", "need",
      "from home", "at home", "my home", "my kitchen", "start", "starting", "sell", "selling",
      "what do i need", "how do i", "can i")),
    _sell_food_from_home,
    # "sell my old phone", "sell the car" and "sell clothes" are selling a thing you own, and
    # the tax row for a side income owns the selling that has no kitchen in it.
    avoid=(# registering with HMRC is its own question and the tax table answers it: "do i need
           # to register as self employed to sell cakes" wants the 5 October deadline, not the kitchen
           "self employed", "self-employed", "self assessment", "hmrc", "tax return",
           "tax bill", "declare", "ni number", "national insurance",
           "sell my house", "sell the house", "sell my car", "sell the car", "sell my phone",
           "sell my old", "sell clothes", "vinted", "depop", "ebay", "car boot", "gumtree",
           "scrap", "furniture", "sofa", "washing machine",
           # a party, a wedding and a lunch are cooking for people you know, not a business
           "wedding", "birthday", "party", "funeral", "christmas dinner", "buffet",
           "how many", "how much should i cook",
           # what the selling makes is a money question: "how much can i earn selling cakes
           # before tax" wants the personal allowance, and a licence card is a wrong answer to
           # a right one. The register answer stays for the ask that is about what is allowed.
           "earn", "earning", "earnings", "before tax", "how much can i make",
           "how much will i make", "profit", "turnover", "pricing", "price my",
           # how to get a pitch on a market is the council's markets officer, not the kitchen:
           # "how do i get a market stall" was a wrong card before this row and this row does
           # not answer it either, so it is left to another module rather than half answered.
           "get a stall", "get a market stall", "get a pitch", "apply for a stall",
           "apply for a pitch", "market pitch"),
    # "how do i register as a food business" reached the how-to-vet-a-company row through
    # "business" and "registered", which is a Companies House check rather than the kitchen
    # register, so this row carries a bias rather than the other row giving up its words.
    bias=3,
    ask=("do", "does", "can", "how", "what", "need", "should", "is it", "legal", "allowed")))


# --- this branch's additions -----------------------------------------------

# Everyday work lines the deck sends and nothing answered: being new, saying no to a client, how a
# shift rota works, and hating the job you are in. Being interrupted at work got its own entry on
# main while this branch was open, so it is not repeated here.
WORK_ADDITIONS = (
    entry("disagree-with-boss",
          (("disagree with my boss", "disagree with my manager", "argue with my boss",
            "argue with my manager", "not agree with my boss", "boss is wrong",
            "manager is wrong", "push back on my boss",
            # not "say no to my boss": that is say-no-politely's line, which the whole-bot
            # question asks about and this entry was taking
            "tell my boss they are wrong"),
           ("how", "what", "should i", "do i", "can i", "politely", "without", "when")),
          "Do it in private, on the effect rather than the judgement: \"I think that will cost us "
          "the Tuesday deadline - can we check the dates?\" Name what you would do instead, and "
          "leave one pause for them to think: a boss who is contradicted in front of the team "
          "defends the decision, not the facts. If the call is theirs to make and it goes ahead, "
          "follow it and put your objection in an email the same day - \"as discussed, my concern "
          "is x\" - so it is on the record without a second argument.",
          ask=("how", "what", "should i", "do i", "can i"),
          avoid=("disagree with my partner", "disagree with my wife", "disagree with my husband",
                 "disagree about money", "disagree about the kids", "disagree on a name")),

    # A line that states the complaint instead of asking for it: "my manager says i sound
    # defensive when i disagree" was the listening line, because "disagree with my boss" wants the
    # boss named as the person disagreed with, and the sentence here names the boss as the person
    # *saying* it. The ask is the wording of a disagreement, which is the same job as the row above.
    entry("sound-defensive",
          (("sound defensive", "sounds defensive", "sounding defensive", "look defensive",
            "come across as defensive", "coming across as defensive", "being defensive",
            "sound rude", "sounds rude", "sound blunt", "too blunt", "sound aggressive",
            "sounds aggressive", "sound confrontational", "sound argumentative",
            # "how do i sound less defensive at work" was "that's beyond what I know well": the
            # ask puts a "less" between the two words the row names
            "less defensive", "less rude", "less blunt", "less aggressive", "less abrupt",
            "come across as aggressive", "come across as rude", "come across as blunt",
            "come across badly"),
           ("how", "what", "when", "do i", "should i", "can i", "manager", "boss", "says",
            "said", "disagree", "disagreed", "work", "colleague", "team", "meeting")),
          "Aim at the work, not the person: \"can we check the numbers before Friday?\" rather "
          "than \"that's wrong\", then name the one thing you would change and stop. \"No, that "
          "won't work\" with nothing after it is what reads as defensive. It is worth asking once, "
          "without heat - \"when I said that, what came across as defensive?\" - because most "
          "managers will name a habit you can change, and a habit is easier to fix than a manner.",
          # the same words about somebody else, or about a driving lesson, are not this row
          avoid=("my partner", "my husband", "my wife", "my boyfriend", "my girlfriend",
                 "my friend", "my mum", "my dad", "my son", "my daughter", "my brother",
                 "my sister", "flatmate", "housemate", "driving", "self defence", "self-defense",
                 # tone somewhere that is not a disagreement at work is another row's question:
                 # "how do i sound less rude on the phone" was getting the meeting advice
                 "on the phone", "phone call", "customer", "customers", "waiter", "waitress",
                 "my neighbour", "my neighbor", "landlord", "landlady", "my teacher")),

    entry("late-for-work",
          (("late for work", "late to work", "late in", "running late", "im late",
            "i was late", "overslept", "slept in", "missed the bus to work"),
           ("what should i say", "what do i say", "tell my boss", "tell my manager", "how do i",
            "how to", "apologise", "apologize", "excuse", "again", "late again", "every day",
            "traffic", "train", "childcare", "school run")),
          "Say it before they notice, in one line and with the time you will be in: \"The 8:12 was "
          "cancelled - I will be in at 9:40 and I have moved the 9am to 10.\" Do not offer a long "
          "excuse and do not blame the traffic twice; offer the thing that protects the work. If it "
          "is the third time in a month, go further and name the fix - a slightly earlier train, a "
          "booked slot for the school run - because a pattern with no plan reads as not caring. If "
          "lateness is being raised formally, check your contract and any policy first: some "
          "employers have a trigger (three in a month) and a hearing after it.",
          ask=("what", "how", "should i", "do i", "again", "every day", "tell my"),
          avoid=("period late", "late period", "late bloomer", "how long can i be late",
                 "late payment", "late fee", "late night", "stay up late", "late shift")),

    entry("handover",
          (("handover", "hand over", "handover notes", "hand back", "leave notes"),
           ("how do i", "how to", "write", "writing", "before i leave", "leaving", "holiday",
            "annual leave", "sick", "maternity", "paternity", "resign", "notice", "new job",
            "who covers", "cover for me")),
          "One page, newest first, and written for someone who has never done your job: what is "
          "running, what is due and when, who to ask about each thing, and the two or three things "
          "that go wrong if nobody touches them. Name a person for each item - \"the Tuesday "
          "invoice goes to Sam\" - because a handover that ends in a folder nobody opens is worse "
          "than none. Send it the day before you go, offer fifteen minutes to walk through it, and "
          "keep a copy: it is also the best evidence of what you carried.",
          ask=("how", "what", "should i", "do i", "write"),
          avoid=("hand over the keys", "handing over money", "handover of a patient",
                 "police handover", "shift handover")),

    entry("working-abroad",
          (("work abroad", "working abroad", "work overseas", "working overseas", "job abroad",
            "live abroad for work", "relocate abroad", "overseas job", "visa for work",
            # "can i work from abroad" was answered with the roaming settings, because
            # technology's mobile-data-abroad keys a bare "work" beside a bare "abroad" and
            # "work abroad" as two adjacent words never matched "work from abroad"
            "work from abroad", "working from abroad", "work from overseas",
            "working from overseas", "work remotely from abroad"),
           ("how do i", "how to", "can i", "should i", "what do i need", "tax", "taxes",
            "visa", "permit", "right to work", "move", "moving", "six months", "a year")),
          "The order that saves trouble: a written job offer first, then the right to work for the "
          "country you are going to - a work permit or an intra-company transfer, not a tourist "
          "visa - and only then the move. Ask the employer who files the permit and who pays for "
          "it, get the start date in the contract rather than in an email, and check the tax "
          "position in your first month: most countries tax you from the day you arrive, and a "
          "double-tax treaty only helps if the paperwork is done. Keep your UK bank account and "
          "your NI record in mind, and register with the local health system as soon as you land.",
          ask=("how", "what", "can i", "should i", "do i"),
          avoid=("holiday abroad", "where should i go", "flight", "cheap flights", "hotel",
                 "mobile data abroad", "roaming", "exchange rate", "travel insurance",
                 "posting a parcel", "send money")),

    entry("counter-offer",
          (("counter offer", "counter-offer", "counteroffer", "more money to stay",
            "offered me more money", "matched my offer", "match my offer",
            "pay me more to stay", "raise to stay", "keep me on with more",
            "offered more money", "offered more", "offered to match", "matching offer",
            "wants me to stay", "asked me to stay", "asked me to stay on"),
           ("should i", "stay", "leave", "accept", "take it", "worth", "or go", "what do i do",
            "turn down", "decline", "how much", "leverage", "ask for")),
          "Take a counter offer only if it fixes the reason you looked, in writing, with a date: "
          "more money at the same job answers the money question and nothing else, and most "
          "people who accept one have left within a year anyway. Ask what changes in the next six "
          "months and who else knows about it, because an off-cycle rise that only you and your "
          "manager know about puts a target on your back. If the reason was the work or the "
          "manager, the counter offer is a kindness, not a fix - thank them, keep the new start "
          "date, and leave on good terms.",
          # a pay rise you have not been offered yet is ask-for-raise's line, and a first offer at
          # interview is interview-salary's
          ask=("should i", "stay", "leave", "accept", "take", "worth", "or go", "what",
               "turn down", "decline", "do i"),
          bias=1,
          # "wants me to stay" is in the key, so "wants me to stay late" reached the row: "my
          # boss wants me to work late every week, do i have to be paid for it" was told to take
          # or turn down a counter offer. Staying on an hour is not staying at the job, so the
          # phrases that put "stay" beside a clock hand the line back to the pay-and-hours row.
          avoid=("should i ask for a pay rise", "apply for a job", "first job offer",
                 "interview", "how much should i ask", "my notice",
                 "stay late", "staying late", "stayed late", "stay on late", "stay behind",
                 "stay back", "stay after", "stay over", "work late", "working late",
                 "work overtime", "every week", "extra hours")),

    entry("new-job-friends",
          (("new job", "new role", "just started", "first week", "new team", "new workplace",
            "started this week",
            # "how do i deal with being new at work" names no job and no team
            "being new", "new at work", "new starter", "just joined", "new to the team"),
           ("friends", "make friends", "nobody", "lonely", "talk to", "people",
            "get to know",
            # "how do i make mates at a new job" is the same asking shape in the word people
            # use for it here, and it fell through to "a search should sort you out quickly"
            "mates", "make mates", "mates at work", "buddies",
            "fit in", "settle in", "settle into", "settling in", "settling into",
            "lunch", "left out", "being new", "new at work", "im new",
            "new starter", "new to the team", "just joined",
            "nobody talks to me", "no one talks to me", "nobody speaks", "lonely at work",
            "left out at work", "on my own at work", "dont know anyone", "don't know anyone",
            # "how do i make a good impression in a new job" is the same first month, asked the
            # other way round: the answer is the small yeses, not a performance.
            "impression", "good impression", "make an impression", "start well", "be liked")),
          "Say yes to everything small for the first month - lunch, a coffee, the drink after "
          "work - because that is where the friendships actually happen, and nobody notices who "
          "said yes. Ask people about their own work rather than talking about yours: \"how long "
          "have you been doing this?\" and \"what is the bit nobody warns you about?\" get real "
          "answers. Then pick one recurring thing - a Friday lunch, a walk at the same time - and "
          "keep going to it. Friendships at work come from repeated low-effort time, not one good "
          "conversation.",
          ask=("how", "do i", "can i", "what", "should i", "help"),
          avoid=("school", "university", "college", "nursery", "my son", "my daughter", "child",
                 # The first week has an answer of its own and it is not the friendships one:
                 # "how do i settle into a new job" was the day-one packing list, because the
                 # first-day row scores on the same "new job" and its ask group took it. Settling
                 # in is being useful and asking early, which is what this row says once the
                 # first-week row stands aside.
                 )),
    entry("say-no-to-a-client",
          (("client", "customer", "clients", "customers"),
           ("say no", "tell them no", "turn down", "refuse", "decline", "push back", "say i cant",
            "say i can't", "without losing", "no without", "dont want to", "lake of work",
            "not possible", "too much",
            # the way people put it: "how do i tell a client no", "tell a client i cant do it".
            # The phrase has to name the client because the first group already counted the word.
            "tell a client no", "tell a customer no", "tell a client", "tell a customer",
            "no to a client", "no to a customer", "saying no", "cant do", "can't do",
            "cannot do", "cant deliver")),
          "Say what you can do and by when, not what you cannot: \"I cannot do the whole thing by "
          "Friday, but I can get you the first two sections and the rest on Tuesday\" keeps the "
          "work and the relationship. Give one plain reason, no apology and no long excuse, and "
          "never blame someone else. If the ask is outside what you do, say so once, clearly, and "
          "point them somewhere better - people remember being helped more than being told yes. "
          "Offer the smaller version at a price you would happily accept, then stop selling.",
          ask=("how", "do i", "can i", "what", "should i", "way to"),
          avoid=("refund", "complaint", "faulty", "invoice", "quote", "contract", "interview")),
    entry("shift-patterns",
          (("shift pattern", "shift patterns", "shift work", "shift rota", "rota", "shifts",
            "night shift", "night shifts", "12 hour shifts", "twelve hour shifts"),
           ("how", "work", "works", "what", "mean", "average", "hours", "rest", "between",
            "many", "legal", "allowed", "change")),
          "Shifts come as a repeating rota, not a fixed week - three earlies, three lates, three "
          "nights and three off is a common one - and your contract or rota policy says which "
          "pattern and how far ahead it is published. The law gives you 11 hours off between "
          "shifts and 24 hours off a week or 48 a fortnight, averaged. Ask for the rota in "
          "writing and write down every swap you agree, and if the pattern is making you ill, ask "
          "about a fixed shift.",
          ask=("how", "what", "does", "do", "is", "can", "legal", "many"),
          # "how do i ask for a shift swap" is the swap, not the shape of the rota: `shift-swap`
          # answers how to arrange one, and this entry explains patterns
          avoid=("school", "bus", "train", "factory shifts", "gears", "my car", "shift key",
                 "shift the", "workshop", "swap", "swapping", "swapped", "swap my shift",
                 "swap shifts",
                 # asking how to decline one is not asking what a pattern is: "how do i turn
                 # down a shift" was told what a repeating rota is, and the refusal scripts
                 # answer it - overtime-say-no for the extra shift, say-no-politely for the rest
                 "turn down", "turned down", "turning down", "say no", "saying no", "refuse",
                 "decline", "declining", "get out of", "tell them no", "tell him no",
                 "tell her no")),
    # "how do i know if i should quit my job" was answered by the resignation letter: the letter
    # keys "quit" and "how do i", and both halves are in the question. Whether to go is the other
    # question, and it is asked more often than the letter is written, so it gets the tests that
    # decide it rather than the words to hand in.
    entry("quit-or-stay",
          (("should i quit", "should i resign", "if i should quit", "if i should leave",
            "whether to quit", "whether i should quit", "whether i should leave",
            "know if i should quit", "know if i should leave", "should i leave",
            "should i hand in my notice", "should i stay", "quit or stay",
            "leave or stay", "is it worth leaving", "worth quitting", "worth resigning",
            "worth changing jobs",
            # The decision is asked as what the person wants, not as "should i": "i want to quit
            # but i need the money" and "i want to leave my job but i cant afford it" were a chat
            # opener and a savings card. The quit words carry the subject, and the ask below
            # demands the job or the money, so "i want to quit smoking" stays where it is.
            "want to quit", "want to leave", "wanting to quit", "wanting to leave",
            "thinking of quitting", "thinking about quitting", "thinking of leaving",
            "thinking about leaving", "thinking of handing in my notice",
            # The decision is often asked as permission, with the length of the stay in the line:
            # "is it ok to leave a job after three months", "is it bad to leave a job after a
            # year". Nothing in the "should i" shapes fits those, and the age words in them took
            # the line to a food table, so the ask is spelled out with the job in it.
            "ok to leave a job", "ok to leave my job", "bad to leave a job",
            "bad to leave my job", "wrong to leave a job", "wrong to leave my job",
            "leave a job after", "leave my job after", "leave the job after",
            "leaving a job after", "leaving my job after", "left a job after"),
           # the job words are in the second half so that "should i quit smoking" and "should i
           # stay in tonight" stay with whoever answers them
           ("job", "work", "career", "how do i", "how can i", "know", "decide", "figure out",
            "worth it", "what do i do",
            # The job is often not named and the money is: "i want to quit but i need the money"
            # has no job word at all, and the second half is the whole reason it is hard.
            "the money", "need the money", "money", "afford", "cant afford", "can't afford",
            "cannot afford", "bills", "wages", "my pay", "pay")),
          "Leave only for a reason that still holds on a good day, and only once you could afford "
          "the gap. Three tests decide it. "
          "First, is it the work or the place: if you would do the "
          "same tasks somewhere else without the dread it is the place, and a move inside or out "
          "is cheaper than a career change. Second, is the thing you want fixable where you are - "
          "hours, a manager, a project - and have you asked for it in one plain conversation. "
          "Third, can you afford the gap: three months of money you could live on, and a CV "
          "updated before you need it. If two of the three are still bad after one honest attempt "
          "at the fix, start looking while you are still there. Set a date now and decide on it, "
          "not on a Tuesday when it is unbearable.",
          ask=("should i", "if i", "whether", "how do i", "how can i", "how do you", "know",
               "decide", "worth", "need the money", "money", "afford", "cant afford",
               "can't afford", "cannot afford", "bills", "wages", "pay",
               # asking permission to go is the same decision: "is it ok to leave a job after
               # three months" wanted the three tests, and got a punt.
               "is it ok", "is it bad", "is it wrong", "ok to leave", "bad to leave",
               "wrong to leave", "a job after", "my job after"),
          avoid=("my partner", "my husband", "my wife", "my son", "my daughter", "he wants",
                 "she wants", "my friend", "my mum", "my dad",
                 # A home you want to leave because of the money is the landlord's question, and
                 # `money.py` answers it: this card is about the job.
                 "flat", "landlord", "landlady", "tenancy", "lease", "house", "my home",
                 "my room", "the rent", "rent is"),
          # "i want to quit but i need the money" is stated, not asked, and it is the question:
          # the person is telling you the two halves and wants the third.
          report=True),

    # A boss whose company drains you is a work question, not a friendship one: main answered
    # "how do i deal with a draining boss" with "You do not owe anyone an announcement, and a slow
    # fade is a real option", because the friendship row keys the feeling word and "how do i deal
    # with" is in its second half. The feeling word alone cannot be the key - a phone battery and a
    # toddler drain you too - so the person is in this key and the ask is the doing words.
    entry("draining-boss",
          (("draining boss", "boss drains", "draining manager", "manager drains",
            "boss is draining", "manager is draining", "exhausting boss", "boss exhausts",
            "draining colleague", "colleague drains", "drains me at work", "work drains me",
            "drained by work", "draining job", "job drains me"),
           ("what do i do", "what can i do", "what should i do", "what to do", "how do i",
            "deal with", "handle", "cope", "manage", "stop", "help",
            # "work drains me and i dont know what to do" is the same ask without the "i"
            "dont know what to do", "don't know what to do", "not sure what to do")),
          "Name the pattern before you name the person: which meetings, how often, and what "
          "happens to your work afterwards. Then set one limit you can hold - the hour you stop "
          "answering, the one meeting you leave on time - and say it once, in terms of the work "
          "rather than their character. Keep a dated note of the cases if it carries on, and take "
          "the list, not the grievance, to their manager or to HR. If every Sunday is already "
          "ruined by Monday, that is your answer about the job, not about your resilience.",
          avoid=("school", "playground", "my son", "my daughter", "my mum", "my dad",
                 "my friend", "my partner", "my husband", "my wife", "landlord")),

    entry("hate-my-job",
          (("hate my job", "hate this job", "hate work", "hate my work", "fed up of work",
            # the same question about the job you have just started, which was a shrug
            "hate my new job", "hate the new job", "hate this new job",
            "my new job is not what i expected", "new job is not what i expected",
            "fed up with work", "sick of work", "sick of my job", "dread work", "dread going in",
            "cant face work", "can't face work",
            # "tired of" is the friend-and-family phrase for the same question, and the row that
            # owns it answered "im tired of my job what should i do" with the slow-fade card for
            # ending a friendship. The job words are what make it this row's line.
            "tired of my job", "tired of this job", "tired of the job", "tired of work",
            "bored with my job", "bored with work", "had enough of my job", "had enough of work",
            "over my job", "over work",
            # stuck is the flat version of hate: no direction rather than dislike, same answer
            "stuck in my job", "stuck in this job", "stuck in my career", "stuck at work",
            "going nowhere", "dead end", "dead-end"),
           ("normal", "does everyone", "is it", "should i", "leave", "quit", "stay", "change",
            "what do i do", "what should i do", "should i do", "help", "everyone", "feel",
            "stuck",
            # "i hate my job what can i do" asked the question and still scored 3, under
            # MIN_SCORE, because the second group only listed the shorter asks. The bare
            # statement stays with the feelings modules, which is where main keeps it.
            "what can i do", "can i do",
            # the disappointed version of the same line: "my new job is not what i expected"
            "expected", "what i expected", "disappointed",
            # "how do i stop feeling tired of my job" is the same question with the feeling at the
            # front, and without these it kept the friendship row's answer
            "how do i", "how to", "stop feeling", "stop being")),
          "Yes, most people hate their job some weeks, and the useful question is which part: the "
          "manager, the hours, the pay, the work itself or the people. Pick the one thing that "
          "would change the most and try the smallest real fix for a month - a conversation about "
          "hours, one project swapped, a fixed finish time - because a job that is wrong in one "
          "part is often fixable and one that is wrong in all of them is not. Set a date, three "
          "months out, to decide with something in hand: an updated CV, two conversations about "
          "other work, and a figure you need to earn. Do not quit on a bad Tuesday, and if you "
          "dread it every morning or cannot sleep for it, that is a GP conversation and a sick "
          "note, not a weakness.",
          ask=("is it", "normal", "should i", "why", "how", "what", "do i", "everyone"),
          avoid=("homework", "school", "university", "revision", "my son", "my daughter",
                 "my husband", "my wife", "my partner")),

    # The three asks the work deck still sent to a shrug on main: a deadline that has slipped, a
    # week that does not fit, and a move to another team. Each is a conversation with a manager
    # rather than a fact, so each one gives the words to say.
    entry("missed-deadline",
          (("missed the deadline", "missed a deadline", "miss the deadline", "deadline slipped",
            "late with the report", "didnt finish in time", "didn't finish in time",
            "not going to make the deadline", "behind on the report", "missed my deadline",
            "going to miss the deadline", "wont make the deadline", "won't make the deadline"),
           ("tell", "say", "boss", "manager", "client", "what do i", "explain", "how",
            "warning", "at work", "work", "slipped", "late",
            # the thing that is late: a report and a submission are what people miss, and
            # without them "im going to miss the deadline for the report" was answered by the
            # diary-and-alarms entry, which is for remembering a deadline, not for missing one
            "report", "submission", "presentation", "deadline for",
            # a line that says how it stands ("i think i'm going to miss it", "we're gonna
            # miss it") is telling somebody, not asking to be reminded: the diary-and-alarms
            # entry was answering these before, which is the wrong help.
            "i think", "gonna", "i will", "we are going to")),
          "Say it as soon as you know, not on the day: what slipped, why in one sentence, what you "
          "have done, and the new date you can hit. \"The figures are not signed off, so the report "
          "will be with you Thursday at noon - I have the draft ready and the delay is the audit "
          "check.\" Offer the smaller version if it helps: the summary now, the full pack Thursday. "
          "Late and honest beats late and silent.",
          # a tax return, a visa and a university essay each have their own deadline and their
          # own rule, and none of them is a message to a manager
          avoid=("tax return", "self assessment", "self-assessment", "hmrc", "visa", "passport",
                 "university", "uni ", "coursework", "essay", "dissertation", "school",
                 "assignment", "rent", "mortgage", "council tax", "insurance")),

    entry("too-much-work",
          # "workload" is the word people use when they want to raise it with someone rather than
          # just cope: "how do i talk to my boss about my workload" is the same problem, said out
          # loud. A bare "a lot on" is not here - "i have a lot on at home" is not the office.
          (("too much work", "not enough time", "swamped", "overloaded", "snowed under",
            "drowning in work", "understaffed", "stretched thin", "work is piling up",
            "too much on", "cant keep up", "can't keep up", "cant get through it all",
            "workload", "workloads", "my workload", "too much on my plate"),
           ("how", "what do i", "cope", "prioritise", "prioritize", "manage", "deal", "team",
            "cant", "everything", "help", "have", "got", "where do i start",
            "where to start", "dont know where to start", "do i do")),
          "Write the list down and put the deadline next to each thing, then take the three that "
          "actually matter this week and say out loud what moves: \"I can do these three by Friday, "
          "and the other two will be Monday unless something drops.\" Send it in writing so the "
          "choice is on record. If the list does not fit with a full week, the answer is another "
          "pair of hands or a later date, not longer days.",
          # school, revision and the house are not the job, and getting the boss to notice the
          # pile is a different conversation from deciding what to drop
          avoid=("school", "exam", "exams", "revision", "homework", "studying", "kids",
                 "children", "baby", "housework", "house", "garden", "wedding",
                 "notice", "get my boss", "get my manager")),

    # Stress that has to be said out loud to the person who sets the work is its own ask: main
    # answered "how do i tell my boss i am stressed" with the breathing exercise, which is the
    # right advice for the feeling and no help with the conversation.
    entry("tell-boss-stressed",
          (("boss", "manager", "line manager", "team leader", "supervisor"),
           ("stressed", "stress", "burnt out", "burnout", "overwhelmed", "too much on",
            "struggling", "mental health", "anxiety", "not coping", "cant cope", "can't cope")),
          ("Ask for a private twenty minutes and say it plainly in the first sentence: \"I'm not "
           "coping with the current load and I want to sort it out before it shows in the work.\" "
           "Then bring two or three specifics - the tasks, the hours, what has slipped - and two "
           "things you want changed, because a manager can act on a proposal and rarely on a "
           "feeling. Ask what support exists: an employee assistance line, occupational health, "
           "flexible hours or a temporary reallocation. Put a short summary in an email afterwards "
           "so there is a record, and if nothing changes, that email is what you take to HR."),
          bias=2,
          # a line about the work piling up is the prioritising answer, and one about the
          # feeling is the stress card: this is only the conversation with the boss
          # the feeling has to be named, or "how do i tell my boss i have too much on my plate"
          # is boss-too-much's question about a shorter list
          ask=("stressed", "stress", "burnt out", "burnout", "overwhelmed", "mental health",
               "anxiety", "not coping", "cant cope", "can't cope", "struggling"),
          avoid=("resign", "resignation", "notice", "leaving", "quit", "pay rise", "salary",
                 "appraisal", "interview", "holiday", "sacked", "fired", "bully", "bullying")),

    entry("transfer-request",
          (("transfer", "move team", "another team", "different team", "different department",
            "another department", "move department", "secondment", "move sideways",
            "move to a different role"),
           ("ask", "request", "how", "boss", "apply", "possible", "go about", "internal")),
          "Ask your own manager first, before the other team hears it from someone else: \"I'm "
          "interested in the data team and I'd like to be considered if something opens.\" Give a "
          "reason that is about the work, not about them. Then speak to the other manager, and ask "
          "what a handover would look like so your current team is not left short - a transfer "
          "people think is tidy is the one that actually happens.",
          # a bank transfer, a phone transfer and a football transfer are money, technology and
          # sport, and none of them is a move inside a company
          avoid=("money", "bank", "send", "paypal", "balance", "savings", "funds", "flight",
                 "booking", "number", "photos", "phone", "whatsapp", "sim", "player",
                 "football", "club", "points")),

    # A restructure is not a redundancy yet: the question is how to still be there afterwards.
    entry("restructure-job",
          (("restructure", "restructuring", "restructured", "reorganisation", "reorganization",
            "reorganised", "reorganising", "consultation period", "department is merging",
            "teams are merging", "new structure"),
           # The plainest asks are "what should i do" and "should i resign first", which carry no
           # noun from the first group at all: without them the entry was only reachable when the
           # line happened to say "how do i".
           ("job", "keep", "safe", "survive", "at risk", "worried", "how do i", "what do i do",
            "what should i do", "should i do", "resign", "resigning", "quit", "should i stay",
            "stay or go", "union", "apply", "my role", "position", "selected", "criteria",
            "team", "interview")),
          "Restructures run on written criteria, so ask HR for the pools, the criteria, the "
          "timetable and the minutes, in writing. Apply for the roles that exist instead of "
          "waiting to be placed, and answer the criteria in their words with an example and a "
          "number. Do not resign before the outcome - it can cost you redundancy pay; check the "
          "contract and the statutory minimum. Take a union rep into the consultation meeting if "
          "you have one, and ring ACAS, which is free, the same week."),

    # Someone else's tears are a different job from your own: main answered "how do i deal with a
    # colleague who cries" with the advice for the person crying.
    entry("someone-crying",
          (("colleague", "colleagues", "coworker", "co-worker", "boss", "manager", "team member",
            "member of staff", "someone at work", "my friend at work",
            # who people name when it is not a colleague: "a girl at work cries every week" and
            # "one of my team cries at the slightest thing" were read as the speaker's own tears
            "girl at work", "woman at work", "man at work", "lad at work", "bloke at work",
            "guy at work", "one of my team", "someone on my team", "member of my team",
            "one of the team", "my team", "employee", "member of my staff"),
           ("cries", "crying", "cried", "in tears", "tears", "breaks down", "broke down",
            "distressed", "emotional", "sobbing",
            # how often it happens, which is what makes a colleague's tears a thing to handle
            "every week", "all the time", "keeps crying", "at the slightest", "again today")),
          "Give them a minute and a way out rather than advice: \"Let's grab a coffee\" or "
          "\"Do you want to take five?\" Then say nothing and let the silence sit - most people "
          "fill it themselves. Don't ask what happened in front of anyone else, and don't promise "
          "secrecy you cannot keep; if it is about work, say the one thing you can do (\"I'll "
          "cover the meeting\") and do it. Afterwards treat it as ordinary, not as a thing to "
          "mention again, and if it keeps happening, ask them once, privately, whether something "
          "at work is behind it.",
          # your own tears are crying-at-work's line, which has the words to say and the meeting
          # to come back to. "my manager broke down in a meeting" names a meeting and a person
          # both entries can read, so the second-person answer has to give way on rank: bias=2
          bias=2,
          # "my colleague upset me" is the speaker's own grievance: the bare "upset" in the key
          # read it as someone else's tears, and an upset person in the line is not always crying.
          guard=_someone_elses_tears,
          avoid=("i cried", "i cry", "i was crying", "i broke down", "i cant stop crying",
                 "i keep crying", "i nearly cried", "my tears",
                 "upset me", "upsets me", "upset my", "hurt my feelings", "annoyed me",
                 "made me feel", "offended me", "rude to me", "upsetting me",
                 # A follow-up that asks for the words ("i dont know what to say to my boss")
                 # carries the earlier crying into the text it is read on, and this row then
                 # answered it with how to look after someone crying in front of you. The ask
                 # for what to say is the difficult-conversation row's, not this one's.
                 "what do i say", "what should i say", "what can i say", "what do i tell",
                 "what to say", "what do i say to", "what do i tell her", "what do i tell him")),

    # A passive-aggressive email is not a difficult conversation in the room: it is a document,
    # and the answer is the reply you write, or do not write.
    entry("passive-aggressive",
          (("passive aggressive", "passive-aggressive", "backhanded", "snide", "sarky",
            "sarcastic email", "rude email", "snippy", "bitchy email",
            # a "dig" is the remark, not the spade: bare "dig" made "how do i dig a hole for a
            # plant" and "how do i dig a hole" this row's line, and the answer was about replying
            # to a work email
            "dig at", "digs at", "a dig", "digs about", "dig from", "little dig", "cheeky dig",
            "very aggressive email",
            # the words people use for a message with a sting in it: "how do i handle a cheeky
            # email from a colleague" was buying a pair of door handles
            "cheeky email", "cheeky message", "cheeky note", "rude message",
            "snide email", "snarky email", "snotty email", "snotty message"),
           ("email", "emails", "message", "messages", "note", "comment", "reply", "colleague",
            "boss", "manager", "work", "how", "should i", "what do i do", "respond")),
          "Answer the question in it and leave the tone alone: reply to the work, in two lines, "
          "with the dates and the facts, and no apology you do not owe - \"Thanks - the report "
          "went out on the 4th, so we're clear. Anything else you need from me?\" Written "
          "politeness beats matching the tone, and a flat reply gives them nothing to quote back. "
          "If there is a pattern, keep the emails and say the thing out loud once, in person: "
          "\"Your last two notes read as though I dropped the ball - was that meant?\"",
          avoid=("passive income", "aggressive dog", "aggressive customer", "aggressive behaviour",
                 "landlord", "neighbour", "family", "my mum", "my dad", "my husband", "my wife",
                 # the answer is about replying to written work, so a sibling or a friend
                 # "making snide comments" is not its line: "my sister keeps making snide
                 # comments" was getting "reply to the work, in two lines, with the dates"
                 "my sister", "my brother", "my son", "my daughter", "my friend", "my mate",
                 "my partner", "my flatmate", "in laws", "mother in law",
                 # the garden spade is not a snide remark
                 "dig a hole", "spade", "garden", "hedge", "trench", "pond", "flowerbed",
                 "flower bed", "bulb",
                 # a remark said to your face is the difficult-conversation row's line, not the
                 # written one: "my colleague keeps making digs at me" is not an email
                 "digs at me", "dig at me")),

    # Keeping a record is one habit that answers an appraisal, a grievance and a dispute over
    # hours, so it is keyed by what the person is trying to do rather than by one of those.
    entry("work-record",
          (("work diary", "keep a diary", "keep a record", "keep notes", "written record",
            "record of what i do", "log of what i do", "diary of what i do", "notes of what",
            "track what i do", "evidence", "proof of what"),
           ("work", "how", "what", "best way", "appraisal", "grievance", "boss", "colleague",
            "case", "keep", "use", "should i", "start")),
          "Write the date, the time, what happened and who was there, in that order, and keep it "
          "flat: \"14 May, 9.15 team meeting, Priya said the report was mine, Tom was there.\" Do "
          "it the same day while it is fresh, and keep a copy somewhere you control - email it to "
          "yourself rather than leaving it on the work drive. You are not building a case, you are "
          "building a memory: it is what makes an appraisal, a grievance or a fight about hours "
          "stand up.",
          avoid=("bully", "bullying", "harassed", "harassment", "pupil", "school", "student")),
    # A swap is agreed between two people and then made official: the trick is the rest gap and
    # the written confirmation, not the goodwill.
    entry("shift-swap",
          (("shift swap", "swap shifts", "swap a shift", "swap my shift", "swap my shifts",
            "swap a rota day", "swap rota days", "switch shifts"),
           ("how", "ask", "can i", "is it", "arrange", "boss", "manager", "colleague",
            "someone", "another colleague", "refuse", "allowed", "policy", "should i")),
          "Ask the person who can do your shift first, offer the trade rather than the favour "
          "(\"I'll take your Saturday if you take my Tuesday\"), then get it agreed in writing "
          "with whoever writes the rota - a swap the manager has not seen is the one you get "
          "blamed for. You must still get 11 hours between shifts, so a night cannot be swapped "
          "into a day starting at seven. If a manager refuses, ask which rule it breaks.",
          # "how do i swap shifts" names no colleague, so it has to outrank the covering entry,
          # which carries the same two words; "my colleague keeps asking me to swap shifts" is a
          # colleague word in it and stays with the limit answer
          bias=1,
          # a swap of food, clothes or a chair is a different swap, and a shift key is a keyboard
          avoid=("recipe", "recipes", "dinner", "meal", "lunch", "clothes", "shoes", "chair",
                 "sofa", "house", "flat", "phone", "car", "shift key")),

    # Noise is the office's answer to "I cannot think here": the ask is a desk, not a complaint.
    entry("noisy-office",
          (("noisy office", "open plan", "open-plan", "open plan office", "too noisy at work",
            "noise at work", "loud office", "quiet desk", "quiet place to work",
            "somewhere quiet", "noise cancelling", "noise-cancelling", "cant hear myself think",
            "can't hear myself think",
            # the same ask in the words people use for time rather than space
            "quiet hour", "quiet time", "focus time", "deep work", "block out noise",
            # the noise has a person attached: "how do i deal with a noisy coworker" and "my
            # colleague is really loud on the phone" reached no card at all, and "my coworker
            # plays music out loud" reached the council's abatement notice. The person word is
            # the subject and a noise word is the second signal, so the row reads the desk and
            # not the room (see `_WITH_SOMEONE_AT_WORK` and `_quiet_hour`).
            "coworker", "coworkers", "co-worker", "co-workers", "colleague", "colleagues",
            "workmate", "workmates", "teammate", "teammates", "team mate", "team mates",
            "next to me", "beside me", "next to my desk", "at the next desk", "across from me",
            "person next to me", "guy next to me", "woman next to me", "man next to me"),
           ("how", "ask", "where", "can i", "cant", "can't", "cannot", "deal with", "handle",
            "boss", "manager", "facilities", "hr", "headphones", "earphones", "move", "desk",
            "concentrate", "sound", "volume") + _NOISE_WORDS),
          _quiet_hour,
          guard=_a_person_and_a_noise,
          # a noisy neighbour, a noisy road and a noisy pub are other answers
          avoid=("neighbour", "neighbours", "neighbor", "neighbors", "next door", "flat",
                 "my house", "my room", "traffic", "road", "pub", "bar", "concert",
                 "neighbours upstairs",
                 # a colleague is not a flatmate and a home is not a desk: the tell-them rows
                 # are the house's, and this row is the desk's
                 "my wife", "my husband", "my partner", "my mum", "my dad", "my son",
                 "my daughter", "my child", "my children", "my kid", "my kids", "my friend",
                 "my friends", "flatmate", "flatmates", "roommate", "roommates",
                 "housemate", "housemates", "landlord")),

    # One private sentence, about the effect and not the person: this is the conversation nobody
    # wants, so the entry is keyed by the smell words plus one word for the person or the office.
    entry("colleague-smell",
          (("smells", "smelly", "body odour", "body odor", "bad breath", "unwashed",
            "hygiene", "stinks", "sweaty", "smell of smoke"),
           ("colleague", "coworker", "co-worker", "team member", "boss", "manager",
            "someone at work", "at work", "office", "desk", "how do i tell", "how to tell",
            "how do i say", "should i say")),
          _tell_about_a_smell,
          # "how do i tell my friend they have bad breath" is the tell, not the causes: main's
          # dental row carries the same two words ("bad breath") and won the tie on rank
          bias=1,
          # a smell in the fridge, the bin, the drains or the kitchen is a different question
          avoid=("fridge", "freezer", "bin", "bins", "drain", "drains", "kitchen", "milk",
                 "mould", "mold", "washing machine", "cooker", "oven", "bathroom", "toilet",
                 "gas", "boiler", "my car", "carpet", "dog", "cat", "my breath")),

    # The other person's lateness, which main answered with advice on getting yourself to work
    # on time. The third-person noun is what keeps the two apart.
    entry("colleague-late",
          (("always late", "late again", "never on time", "keeps turning up late",
            "comes in late", "arrives late", "constantly late", "late for their shift",
            "late every day"),
           ("team member", "team", "colleague", "coworker", "co-worker", "staff", "employee",
            "someone", "how do i", "deal with", "handle", "talk to", "say something")),
          "Have one short conversation, in private, about the effect rather than the character: "
          "\"When you come in at half nine the phones are already going - what is making the "
          "mornings hard?\" Ask before you accuse, because childcare, a bus and a second job all "
          "look the same from your desk. Then agree one specific change and a date to look at it "
          "again, and note the date and what was said. If nothing changes, take the dates to your "
          "manager once instead of raising it in the moment - a pattern is a manager's job, a "
          "single late morning is not.",
          # the first person's own lateness is `late-for-work`'s line, not this one
          avoid=("i am late", "i was late", "im late", "i'm late", "i am always late",
                 "im always late", "i keep being late", "overslept", "slept in", "my bus",
                 "my train", "i will be late")),

    # A freelancer or a small business asking how to charge more. Nothing answered it: "how do i
    # raise my prices" was a shrug, and "how do i tell a client the price is going up" was reaching
    # the say-no-to-a-client answer, which is advice for turning work away.
    entry("raising-your-prices",
          (("price", "prices", "rate", "rates", "hourly rate", "day rate", "fee", "fees",
            "charge", "charging"),
           ("raise", "raising", "put up", "putting up", "increase", "increasing", "going up",
            "go up", "higher", "more", "tell clients", "tell a client", "tell them",
            # "how do i" used to be here and it is an ask, not a subject: "how do i know if a
            # sale price is actually a bargain" matched price + the ask and got "give it in
            # writing with a date and a figure", which is a freelancer's rate rise. "raise" and
            # "put up" already carry every real way of asking this.
            "my clients", "my client", "charge more", "should i",
            # "put my prices up" has "my" between put and up, so the phrase "put up" never
            # matched it and "how do i" was doing that work. These are the shapes people use.
            "put my prices up", "put prices up", "put up my prices", "putting my prices up",
            "put my charges up", "put charges up", "put my rates up", "put rates up",
            "put my fees up", "put my fee up", "putting my rates up")),
          "Give it in writing with a date and a figure: \"From 1 April my rate is £X an hour, the "
          "same as new clients pay now.\" Three months' notice for clients on a retainer, one "
          "month for one-off work, and tell the ones you would least mind losing first so you can "
          "practise the sentence. Expect to lose about one client in ten. If one says no, offer a "
          "smaller scope at the same price rather than a discount, because a discount is the new "
          "price for ever.",
          # the price of gas, rent, a house or an interest rate is another domain's question, and
          # so is what a thing costs to buy
          avoid=("energy", "gas", "electricity", "electric", "fuel", "petrol", "rent", "landlord",
                 "house prices", "housing", "interest rate", "interest rates", "mortgage", "house",
                 # a rate on money is not a rate on your work: "should i fix my rate on savings"
                 # was answered with the sentence to send a client
                 "savings", "isa", "savings account", "bond", "bonds", "fixed rate",
                 "variable rate", "tariff", "tracker", "loan", "loans", "apr",
                 "train", "fare", "ticket", "tickets", "supermarket", "groceries", "cost of living",
                 "inflation", "council tax", "bill", "bills", "stock", "shares", "bitcoin",
                 "of living", "buy", "cheapest", "how much does",
                 # a sale, a deal or a bargain is the shop's question, not what to charge
                 "sale", "sales", "bargain", "bargains", "discount", "discounts", "deal", "deals",
                 # a service charge on a bill is not a rate you charge: "should i tip on top of
                 # the service charge" was answered with the letter that raises your prices
                 "service charge", "tip", "tips", "tipping", "gratuity", "restaurant", "waiter",
                 # "charge" is a form of "charging", so a charging cable reached this row:
                 # "should i throw away a frayed charging cable" was answered with the letter to
                 # send a client. A phone cable is not a pay-rise question.
                 #
                 # NOT the bare words "plug", "socket" or "cable": "should i raise my prices for
                 # fitting a socket" is an electrician's rate-rise question, and it is exactly
                 # this card, so the stand-down is the charger words and the fault words only.
                 "charger", "chargers", "charging cable", "phone charger", "charger cable",
                 "usb", "frayed", "fraying", "fray", "worn through", "exposed wire",
                 # a listing price is changed in the shop settings, not announced to a client
                 "etsy", "ebay", "shop", "shops", "listing", "listings", "marketplace",
                 "amazon", "product", "products",
                 # ... and an offer on a house is the house question, even though it says
                 # "price" and "should i": "how much under asking price should i offer" was
                 # answered with this row's letter to a client.
                 "asking price", "asking for", "estate agent", "house", "houses", "flat",
                 "property", "offer on a house", "make an offer", "survey",
                 # setting a price and announcing a rise are two different questions: "how do i
                 # price my work for a client" is not "how do i tell them it has gone up", and a
                 # rise sentence is a confident answer to the wrong question. Those lines stand
                 # down here until a setting-a-price entry owns them.
                 "price my work", "price myself", "how much should i charge", "what should i charge",
                 "should i charge", "what to charge", "how to price", "how do i price",
                 "set my prices", "set my rates", "setting my prices", "work out my rate",
                 "work out my day rate", "work out a rate", "charge for my work",
                 # A phone on the charger is not a client: "should i leave it on charge all
                 # night" was answered with a rate-rise letter. NOT the bare word "charge",
                 # "charger", "charges" or "charging": `_misspelt_avoid` reads "charge" as a
                 # one-slip "charger" and `_forms` puts charge and charging in one family, so
                 # any of them stands this entry down for "i want to charge more for my work" -
                 # the question it is named after. "on charge" only appears in the phone lines.
                 "phone", "iphone", "android", "battery", "batteries",
                 "on charge", "left charging", "leave it charging",
                 "laptop", "electric car", "car charging")),
    # Four lines from one chat sweep that were answered with a listening noise rather than with
    # anything: "Reduce my hours - fair enough. What's stopped it happening so far?", "Got it.
    # Is there anything you'd like a hand with?". Each is a want plus a work subject, which is a
    # way of asking, not a topic the bot can hand back.
    # Moving inside the company is a different conversation from leaving it, and main gave it
    # "Move to another team - fair enough."
    entry("move-team",
          (("move to another team", "move to a different team", "move to another department",
            "transfer to another team", "transfer to another department", "internal move",
            "internal transfer", "another team in the company", "different department",
            "secondment", "job in another team", "apply internally", "apply for an internal"),
           ("want", "wanted", "like", "how", "can i", "should i", "ask", "apply", "boss",
            "manager", "hr", "soon", "worth")),
          "Tell your manager before you apply, in one sentence and without apologising: \"I saw "
          "the analyst role in the other team and I want to go for it - I wanted you to hear it "
          "from me.\" Then apply through the internal process, because the hiring manager cannot "
          "usually offer it to you off the record. Ask what happens to your notice period, your "
          "holiday and your start date if you get it, and check the contract for a minimum time in "
          "post: six or twelve months is common and it is often waivable with your manager's "
          "agreement.",
          avoid=("move house", "moving house", "relocate", "abroad", "country", "visa",
                 "rent", "landlord", "team building")),

    # A takeover is a takeover of the contract: the question behind "what happens to my job" is
    # whether the new owner keeps the terms, and that is one name, TUPE.
    entry("takeover",
          (("being taken over", "taken over by", "bought out", "being bought", "buyout",
            "merger", "merging with", "being acquired", "new owners", "new owner",
            "company is being sold", "company has been sold", "sold the company", "tupe",
            # the bare noun is how half the lines say it: "there is a takeover at work will i
            # lose my job" was still a hedge while "being taken over" answered
            "takeover", "takeovers", "take over", "takeover bid", "under new management"),
           ("job", "jobs", "role", "position", "contract", "terms", "what happens",
            "my job", "worried", "safe", "redundant", "redundancy", "pay", "pension")),
          "If the business is transferred as a going concern, your contract usually moves with it "
          "on the same terms - that is TUPE in the UK - so your pay, holiday, notice and pension "
          "carry over and a change to any of them needs a good reason. Ask the new owner in "
          "writing for the transfer letter, who your employer will be on day one, and whether any "
          "roles are at risk; keep copies of your contract and your last pay slips. A merger is "
          "not a redundancy, and \"at risk\" has to be said in writing before anything happens.",
          avoid=("buy a company", "start a business", "invest", "shares", "stocks", "mortgage",
                 "merger of two", "pharmacy", "takeaway")),
    # The routes into two jobs people ask about by name. Each is one entry, because the answer
    # is the set of routes rather than the subject.
    entry("teaching-assistant",
          (("teaching assistant", "ta job", "teaching assistants", "learning support assistant",
            "classroom assistant", "work in a school", "become a ta", "senco assistant"),
           ("how do i", "how to", "become", "get", "start", "need", "qualification",
            "qualifications", "experience", "without a degree", "no experience", "worth it")),
          "You do not need a degree: schools ask for GCSE maths and English, and a Level 2 or 3 "
          "teaching assistant course helps but is often taken after you start. The way in is to "
          "apply to several schools and to a supply agency at the same time - supply is paid, "
          "gets you known in a few schools, and turns into a permanent post more often than "
          "waiting for an advert does. Ask at the school office for the head of support staff, "
          "and mention any volunteering with children.",
          avoid=("nursery", "childminder", "degree to be a teacher", "pgce", "qts")),
    entry("drop-a-level",
          (("drop a subject", "drop an a level", "drop one of my a levels", "drop a level",
            "dropping a level", "drop as level", "change my subjects", "switch subjects",
            "quit a subject", "give up a subject"),
           ("how do i", "should i", "should", "can i", "what happens", "still", "deadline", "late",
            "sixth form", "college", "university", "ucas", "does it matter")),
          "Talk to your head of sixth form first: in the first few weeks a change is usually free, "
          "and after that the exam entry deadlines are what decide it - entries are made in the "
          "winter, so the sooner the better. Dropping to three is fine for almost every "
          "university, but tell UCAS and your firm choice if an offer names four, and check that "
          "the subject you keep is not a requirement for the course you want. A fourth A level "
          "you are failing helps nobody.",
          # a parent asking about their child is the same question, so the family words are
          # kept out of the avoid: "should my daughter drop a level" was a hedge on main
          avoid=("university", "course", "smoking", "drink", "weight", "habit", "my own")),
    entry("assessment-centre",
          (("assessment centre", "assessment day", "group exercise", "group task",
            "psychometric test", "numerical test", "situational judgement"),
           ("how do i", "how to", "prepare", "pass", "ace", "get through", "what to expect",
            "what happens", "happens", "tips", "advice", "help", "tomorrow", "next week")),
          "The day is four set pieces, so rehearse them as set pieces: a group task where the "
          "group is watched not you (help the group finish, bring one quiet person in, do not "
          "talk over anyone), a short presentation (structure it out loud twice), a case study, "
          "and a competency interview in the same situation-task-action-result shape as any "
          "other interview. Do two timed practice numerical tests beforehand, and eat: people "
          "lose the group task to low blood sugar.",
          avoid=("exam", "coursework", "school", "gcse", "a level", "my son", "my daughter")),
)

ENTRIES = ENTRIES + list(WORK_ADDITIONS)

# --- everyday work lines that had no home -----------------------------------
ENTRIES += [
    # An advert that reads like a wish list is the employer's side of a job search, and the
    # candidate-side entries (cv, cover letter, applications) were taking the line by the word
    # "job".
    entry("job-advert-wording",
          (("job advert", "job ad", "job adverts", "advert", "adverts", "advertisement",
            "vacancy", "vacancies", "job posting", "job description", "job listing"),
           ("wording", "word", "words", "rewrite", "rewriting", "revise", "revising", "improve",
            "write", "writing", "attract", "applicants", "candidates", "fair")),
          "Cut it to what the job actually is: a plain title, three or four real duties, the pay or "
          "the range, the hours and the place, and the one thing a candidate must have. Drop the "
          "adjectives - \"dynamic self-starter\" tells nobody anything - and drop any requirement "
          "that is not essential, because long lists put people off applying at all. Say whether it "
          "is full or part time, whether it can be done from home, and how to apply, in a line each.",
          avoid=("cv", "resume", "cover letter", "interview", "salary expectation")),
    # A small everyday one, and the vending machine is the thing worth naming.
    entry("snacks-at-work",
          (("snack", "snacks", "nibbles", "packed lunch", "desk drawer", "lunchbox"),
           # "break" is not here: "am i entitled to a lunch break" is the break rule's question,
           # and bare "food" took "how do food banks work"
           ("work", "office", "desk", "bring", "take", "pack", "buy", "drawer")),
          "Bring something with protein and fibre in it - nuts, fruit, yoghurt, oatcakes, cheese - "
          "and keep it in your drawer or the office fridge, so the 3pm vending machine is not the "
          "decision. It is cheaper too: a \u00a31.20 snack a day is about \u00a3250 a year. Water in a "
          "bottle on the desk covers most of what people mistake for hunger.",
          # meal-times and night-time snacking have their own answers; a snack for the working
          # day is this one, so where both fit (nutrition's snacking-night keys on bare "keep
          # in"), the office entry takes the line: "what should i keep in my desk drawer to
          # snack on" was going to the evening answer.
          bias=2,
          avoid=("plane", "flight", "airport", "hike", "walking", "picnic", "school", "child",
                 # lunch on its own is the lunch-ideas question; a snack to keep at a desk is this
                 "lunch", "lunchbox",
                 "children", "baby", "run", "running", "gym", "training", "marathon", "dog",
                 # the break you are owed is the break rule's answer, not food
                 "lunch break", "break", "breaks", "entitled", "owed a break", "20 minute",
                 "20-minute",
                 # a food bank is the money answer, not a snack to keep at work
                 "food bank", "food banks", "foodbank", "voucher")),

    # The hours question is not the diary question: a diary is evidence for a dispute, these are
    # the hours themselves, and the unpaid ones are money. Keyed on the tracking, so "how many
    # hours can i work" (the legal limit) and "how do i ask for fewer hours" stay where they are.
    entry("track-hours",
          (("track my hours", "track hours", "keep track of my hours", "log my hours",
            "record my hours", "hours worked", "count my hours", "timesheet", "time sheet",
            "my timesheet", "work out my hours", "check my hours", "overtime record"),
           ("how", "best way", "keep", "log", "work out", "check", "should i", "app",
            "spreadsheet", "unpaid", "pay", "paid")),
          "Write down your start and finish each day, in a note or a spreadsheet, in the same "
          "minute you finish rather than at the end of the week. Keep your own copy - the system "
          "is your employer's record, not yours. Compare the week with your contract: anything "
          "past your contracted hours is the thing to raise, and a month of your own dates is "
          "what makes it stick. If hours go unpaid, ring ACAS (free) before you raise it, and "
          "claim within three months less a day of the shortfall.",
          avoid=("legal limit", "maximum hours", "how many hours", "fewer hours", "reduce my hours",
                 "work permit", "visa", "tax return", "self employed", "self-employed")),

    # Turning one meeting down, which is not the same as a calendar full of them.
    entry("decline-meeting",
          (("get out of a meeting", "get out of the meeting", "skip a meeting", "skip the meeting",
            "decline a meeting", "decline the meeting", "decline a meeting invite",
            "decline the invite", "turn down a meeting", "avoid a meeting",
            "dont want to go to the meeting", "dont need to be in the meeting",
            "do i need to be in this meeting", "get out of a call", "skip this meeting",
            "skip this call", "skip the call", "skip the meeting",
            # "how do i get out of a work call" has a word in the middle of "get out of a call",
            # and it landed on the nuisance-call row, which is about cold callers
            "get out of a work call", "get out of the work call", "get out of this call",
            "get out of the call", "get off a call", "get off this call", "get off the call",
            "work call", "avoid a call", "avoid the call"),
           ("how", "can i", "should i", "do i need", "need to", "polite", "politely",
            "nicely", "better", "instead", "get", "out")),
          "Reply to the invite, not the person's face: \"I can't add value to the whole hour - "
          "can I come for the first ten minutes, or send my bit in writing?\" Give a reason about "
          "the work and offer the smaller version in the same sentence, so nobody has to chase "
          "you. If it is a standing meeting that no longer needs you, ask for your slot to go: "
          "\"Anything for me in the weekly? Happy to drop off and read the notes.\"",
          # Cancelling the meeting you called is the other job: there the people coming are
          # waiting for you, and "reply to the invite" is advice for somebody who received one.
          # Plain "cancel a meeting" is the host's question far more often than the invitee's:
          # you are the one who has to tell the people coming. Only a line that names the invite,
          # the attendance or the room is somebody turning up, and those keep this answer.
          avoid=("my meeting", "our meeting", "organised", "organized", "organise",
                 "organize", "i set up", "i booked", "i run", "i chair", "should i cancel",
                 "cancel a meeting", "cancel the meeting", "cancel my meeting",
                 "cancel our meeting", "cancelling a meeting", "need to cancel", "have to cancel",
                 "got to cancel", "have to call off", "postpone", "reschedule")),

    # The meeting you called yourself: the people who were coming have already moved their day
    # for it, which is why this is a different answer from turning one down.
    entry("cancel-own-meeting",
          (("cancel", "cancelling", "cancelled", "call off", "calling off", "postpone",
            "reschedule"),
           ("my meeting", "our meeting", "the meeting i", "i organised", "organised",
            "organized", "i set up", "i booked", "i run", "i chair", "team meeting",
            "meeting with a client",
            # the plainest way anyone says it: no "my", no "I booked", just the meeting
            "a meeting", "the meeting", "this meeting", "our meeting")),
          "Tell the people coming first, and as early as you can: one line on why, a new date or "
          "two in the same message so it is a move rather than a hole, and a fresh invite. Ring "
          "the person who would have chaired it rather than emailing a room, and say what happens "
          "to the thing the meeting was for. Cancelling your own meeting is cheap early and "
          "expensive late.",
          # a flight, a hotel, a dentist and a subscription are all cancellations, and each has
          # its own answer; so is a decision still being weighed, which is a different question.
          avoid=("should i", "flight", "hotel", "train", "a booking", "table", "restaurant",
                 "appointment", "dentist",
                 "doctor", "gym", "subscription", "insurance", "holiday", "wedding",
                 "party", "order", "plan",
                 # a line that names the invite or the attendance is the invitee's question
                 "invite", "invited", "invitation", "rsvp", "attend", "attending",
                 "attendance", "be there", "minutes"), bias=1),

    # A bad interview is not a mistake you own to a boss, and it is not the outfit question
    # either. Nothing answered "how do i recover from a bad job interview" or "i messed up my
    # job interview can i fix it" at all: the second was the own-a-mistake card.
    entry("bad-interview",
          (("job interview", "interview", "interviews", "interviewer", "interviewers", "panel",
            "recruiter", "second interview", "final interview"),
           ("went badly", "went bad", "badly", "blew it", "messed up", "screwed up",
            "went wrong", "ruined", "fluffed", "bombed", "recover", "redeem", "second chance",
            "fix it", "can i fix", "chance", "hopeless", "didnt get", "didn't get",
            "no offer", "rejected", "rejection", "next time", "better next time",
            # the first thing anybody does after a bad one, and the line that says it plainly
            "feedback", "ask for feedback", "what went wrong")),
          "Ask for feedback in one short email - you want to know what would have made you the "
          "stronger candidate - and then send the interviewer five lines: one thing you would "
          "add to your answer, and why you still want the job. Do not apologise twice. Most "
          "people who get an offer chased one thing they got wrong; a bad hour with a panel is "
          "not a verdict on you.",
          avoid=("wear", "wearing", "outfit", "shirt", "blouse", "suit", "tie", "dress",
                 "shoes", "smart casual", "what should i wear", "ask for a raise", "pay rise",
                 "salary", "notice", "resign", "quit", "fired", "sacked", "redundant",
                 "candidate", "candidates", "hiring", "shortlist", "fairly", "bias",
                 # a bad hour in the room is this answer; not getting the job at all is the
                 # rejection answer, and "i didnt get the job after the interview" tied here
                 "didnt get the job", "didn't get the job", "didnt get the role",
                 "didn't get the role", "didnt get the post", "didnt get it", "didn't get it",
                 "no longer being considered", "turned me down")),

    # The visa cap, asked two ways. The first row keys the visa itself; the second is the same
    # rule asked without the word, on the phrases people actually type ("can a student work",
    # "how many hours can a student work"), so an ordinary "how many hours should a student
    # study" stays a study question. Both replies name the visa, so a home student can see that
    # this is not their rule.
    entry("student-visa-hours",
          (("student visa", "students visa", "tier 4", "tier 4 visa", "student route",
            "international student", "international students"),
           ("how many hours", "hours", "work", "working", "term time", "vacation", "vacations",
            "holiday", "holidays", "full time", "part time", "can i work", "overtime",
            # the sentence about self-employment is only reachable if these are in the ask too
            "freelance", "freelancing", "self employed", "self-employed", "work for myself",
            "start a business", "run a business")),
          STUDENT_VISA_HOURS,
          bias=1,
          avoid=NOT_VISA_HOURS),

    entry("student-work-hours",
          (("student", "students", "international student", "international students"),
           ("can a student work", "can students work", "can i work", "hours can a student work",
            "hours can i work", "how many hours can i work", "how much can a student work",
            "how much can students work", "work full time as a student",
            "work part time as a student")),
          STUDENT_VISA_HOURS,
          # 2, not 1: the holiday-entitlement row has bias 2 and matches "during the holidays" too,
          # and a student asking what they can work in the holidays wants the cap. Where the two tie
          # on score and rarity the holiday row still answers - "how much can a student work during
          # holidays" - which is unchanged from main, not something this row made worse.
          bias=2,
          avoid=NOT_VISA_HOURS + ("school", "schoolchild", "schoolchildren")),

    # "can i be fired without warning" and "can i be sacked for no reason" were shrugs on
    # 3a6d235; the two-year line is the part people need first.
    entry("fired-without-warning",
          (("fired without warning", "sacked without warning", "fired on the spot",
            "sacked on the spot", "dismissed without notice", "no warning",
            "fired for no reason", "sacked for no reason", "can i be fired",
            "can i be sacked", "do i have to be given a warning"),
           ("warning", "notice", "reason", "without", "spot", "legal", "unfair", "rights",
            "can i", "can my boss", "can they", "do they")),
          "Two years' service is the line: before that you can be dismissed without a reason "
          "and without a warning, unless it is for something automatically unfair - pregnancy, "
          "whistleblowing, trade union membership, or a protected characteristic. After two "
          "years a dismissal needs a fair reason and a fair process, and a warning usually comes "
          "before it, so being sacked out of the blue is worth challenging. Gross misconduct - "
          "theft, violence, being drunk on shift - is the exception where they can dismiss on the "
          "spot. Keep every message, note the dates, and ACAS's free helpline will tell you in "
          "ten minutes whether you have a claim.",
          # being off sick has its own card; a redundancy and a resignation are other rows
          avoid=("redundancy", "redundant", "notice period", "hand in my notice", "resign",
                 "garden leave", "probation", "unpaid wages", "holiday pay",
                 "sick", "off sick", "sickness", "absence", "absent", "ill health", "illness",
                 "pregnant", "pregnancy", "maternity", "disability", "disabled"),
          bias=1),
    entry("confirmation-statement",
          (("confirmation statement", "annual return", "confirmation statement due",
            "when is my confirmation statement",
            "do i need to file a confirmation statement",
            "confirmation statement deadline", "missed my confirmation statement",
            "late confirmation statement"),
           ("company", "limited", "ltd", "companies house", "file", "filing", "due", "yearly",
            "every year", "annual", "what is", "do i need", "when is", "how much", "cost")),
          "Once a year you confirm three things at Companies House: the company's address, its "
          "directors and its shareholders. It is not the accounts and not the tax return, and it "
          "is due 14 days after the review period ends - the year runs from the day the company "
          "was set up. It costs \u00a334 online and takes ten minutes. Miss it and Companies "
          "House can fine the company \u00a31,500 and strike it off, so diarise it with the "
          "accounts date.",
          # a limited budget in the kitchen is another row; the tax return has its own card
          avoid=("budget", "cook", "dinner", "shopping", "invoice", "payslip", "salary",
                 "self assessment", "tax return", "vat", "notice")),
    entry("directors-loan",
          (("directors loan", "directors loan account", "director's loan",
            "loan from my company", "took money out of my company",
            "money i took out of the company"),
           ("company", "director", "limit", "tax", "repay", "interest", "s455", "overdrawn",
            "what is", "how much", "do i pay", "benefit in kind")),
          "A director's loan is company money you take out and do not take as salary or as a "
          "dividend, and the company books it as an asset owed back by you. Repay it within nine "
          "months of the company's year end or the company pays s455 tax at 33.75% of the balance, "
          "refunded when you do repay. Over \u00a310,000 and it counts as a benefit in kind, so "
          "it goes on a P11D and you pay tax on the official interest rate you did not pay. The "
          "clean way is a dividend declared with minutes, or a small salary.",
          avoid=("bank loan", "mortgage", "student loan", "payday", "credit card", "overdraft",
                 "car loan", "who can lend", "how much can i borrow")),
    entry("closing-a-company",
          (("close my limited company", "close my company", "close the company",
            "strike off my company", "strike my company off", "strike it off",
            "strike off the company", "strike off a company", "strike off",
            "struck off", "struck off my company", "get my company struck off",
            "dissolve my company",
            "dissolve a company", "shut down my company", "shut my company",
            "company i no longer use", "wind up my company", "deregister my company"),
           # The company itself, and not the ask: a line that says "off" is read as a removal,
           # and the ask in front is then discounted to nothing, so a second part holding
           # "how do i" left "strike off" as the only score and "how do i strike off my
           # company" fell under the floor while "strike off my company" answered. Reading the
           # company word instead is what the key meant all along: the phrase names the end,
           # the company is what ends.
           ("company", "limited", "ltd", "companies house", "ds01", "no longer", "anymore")),
          COMPANY_CLOSING,
          avoid=("shop", "restaurant", "gym", "bank account", "door", "window", "school",
                 "nursery", "office early", "shop early")),

    # "i get butterflies before a talk" was answered with a listening line: the body is what the
    # person is describing, and it has a body answer that works in a corridor. The talking itself
    # has its own answer on main ("how do i calm down before a meeting", "how do i get ready for
    # a big meeting"), so this row keeps only the butterflies and jitters wording and leaves the
    # preparing question alone.
    entry("nerves-before-a-meeting",
          (("butterflies", "jitters", "nervous", "nerves", "worked up", "shaky", "queasy"),
           ("meeting", "meetings", "big meeting", "presentation", "presentations", "talk",
            "pitch", "call", "stand up", "panel", "board")),
          "Do the body first, because this kind of nerves is an alarm, not a thought: breathe in "
          "for four counts and out for six for two minutes, which is what actually brings the "
          "heart rate down, and it works in a corridor or a loo. Then decide the one sentence you "
          "want the room to take away and say that first, in the first ten seconds - the nerves "
          "fade once you are talking. Get there early, sit rather than stand about, and take "
          "water. The shake shows far less than it feels.",
          # an interview, an exam, a wedding speech and a child's school talk all have their own
          # answers, and a date or a GP appointment is not this question
          avoid=("interview", "interviews", "exam", "exams", "test", "tests", "revision",
                 "school", "class", "assembly", "students", "wedding", "best man", "funeral",
                 "eulogy", "date", "first date", "doctor", "dentist", "hospital", "surgery",
                 "scan", "results", "child", "children", "son", "daughter", "kid", "kids",
                 "baby", "toddler", "teenager", "dog", "cat", "puppy", "driving test",
                 # main's meeting row answers the preparing question, and its wording is the
                 # better one for "how do i calm down", so this row does not compete for it
                 "calm down", "get ready", "prepare")),
    # Money taken off a wage is a question about the law, and nothing on main owned it: "can my
    # boss take money off my wages" was answered with a monthly-budget plan, "they took money
    # off my wages for being late" with "ring the bank and freeze the card", and "can my
    # employer fine me" with "I don't know your job". Those are three different wrong answers to
    # the one question people ask most about a payslip they did not expect.
    entry("pay-deductions",
          (("deduct", "deducted", "deducting", "deduction", "deductions",
            "take money off", "took money off", "taken money off", "taking money off",
            "money off my wages", "money off my pay", "money off my salary",
            "take money out of my pay", "took money out of my pay",
            "take it out of my wages", "took it out of my wages",
            "take it off my wages", "took it off my wages",
            "take it off my pay", "took it off my pay",
            "dock my pay", "docked my pay", "docked my wages", "dock my wages",
            "fine me", "fined me", "fines me", "fine my wages",
            "stop my pay", "stopped my pay", "stopping my pay",
            "withhold my pay", "withheld my pay", "withholding my pay",
            # "can my employer charge me for training" and "can my boss make me pay for damage"
            # are the same question about the same rule, in the words people use for it.
            "charge me", "charge me for", "charging me", "charged me",
            "make me pay for", "making me pay for", "made me pay for",
            "pay for it myself", "pay for it out of my", "pay for my own",
            "pay for it out of my own"),
           ("wages", "wage", "pay", "paid", "payslip", "salary", "boss", "employer",
            "manager", "work", "job", "company", "legal", "lawful", "unlawful",
            "allowed", "can they", "can he", "can she", "can my boss", "can my employer",
            "is it", "they", "for being late", "for a mistake", "for breaking")),
          "If it is not tax, national insurance, a court order or something you signed up to in "
          "writing, taking money off your pay is unlawful: a till shortfall, a breakage or a fine "
          "for being late usually counts, and no deduction can take you below the minimum wage. "
          "Ask for the amount back in writing, naming the date and the sum; if they refuse, ACAS "
          "is free to ring and an employment tribunal claim for an unauthorised deduction has to "
          "be started within three months less a day of the deduction.",
          # A payslip that is short because of a tax code, a wage that never arrived and a
          # benefit or a pension are other rows' questions, and each shares its words with this
          # one. "tax code" is what the person checks a deduction against, not what it is.
          avoid=("tax code", "tax refund", "payslip is", "payslips are", "why is my pay",
                 "not been paid", "didnt get paid", "didn't get paid", "havent been paid",
                 "late pay", "pay is late", "missed payday", "underpaid", "overpaid",
                 "pension", "benefit", "benefits", "universal credit", "tax credits",
                 "student loan", "child maintenance", "court order", "council tax",
                 "rent", "landlord", "mortgage", "income tax", "national insurance",
                 # A deposit is not a wage, and the chat about one carries the word "deduct":
                 # "they want to deduct 200 for a mark on the wall" then "i paid a 900 deposit"
                 # came back with the ACAS letter about pay.
                 "deposit", "tenancy", "tenant", "letting agent", "estate agent", "wear and tear",
                 "wall", "walls", "carpet", "landlady",
                 # "charged me for a mistake on the booking" is a flight, a hotel or a garage
                 # charging for its own work, and there is no employer in the line: the words
                 # for the money taken are in the key, so the row has to be told which businesses
                 # are not employers. Main answers each of these with its own card.
                 "airline", "airlines", "flight", "flights", "booking", "hotel", "hotels",
                 "garage", "council", "builder", "builders", "plumber", "plumbers",
                 "mechanic", "mechanics", "dealer", "dealership", "insurer", "insurance",
                 "my house", "the flat", "the house", "boiler", "landlord"),
          # The wage has to be in the line: "deduct" and "fine" are ordinary words ("deduct
          # the cost of the trip", "that is fine"), and without this the row answered a line
          # about a school trip.
          ask=("wage", "wages", "pay", "paid", "payslip", "salary", "boss", "employer",
               "manager", "company",
               # "work" and "job" are not employer words: "can the garage charge me for work
               # they didnt do" and "can the council charge me for work on my house" are a
               # garage and a council charging for their own work, and both answered well on
               # main. A wage, a payslip or the person doing the charging is in every line that
               # is really this question.
               # ...or the thing the money was taken for, which is how a follow-up asks it:
               # "can they deduct money for the uniform they gave me" names no wage at all.
               "uniform", "uniforms", "tools", "equipment", "training", "damage",
               "mistake", "mistakes", "till", "breakage", "breakages", "shortfall"),
          # The money rows reach "wages" and "pay" too (the budgeting plan and the payslip
          # check), so the more specific answer needs the nudge to take the turn from them.
          bias=2),
]

# "how many hours a week do nurses work" was a search hedge, and so were teachers, doctors and a
# lorry driver: the pay rows own the money and the become-one rows own the training, so nobody
# owned the week. The answer is the shape of the job - contracted hours, the shift length, the
# legal cap - so one row holds every job a person asks about, keyed on the job and a hours word.
# A bare "hours" is not in the key: "i work 60 hours a week and i am exhausted" is their own week.
_JOB_WORDS = ("teacher", "teachers", "nurse", "nurses", "doctor", "doctors", "gp", "midwife",
              "midwives", "paramedic", "paramedics", "firefighter", "firefighters",
              "police officer", "police officers", "social worker", "social workers",
              "carer", "carers", "care worker", "care workers", "support worker",
              "plumber", "plumbers", "electrician", "electricians", "builder", "builders",
              "mechanic", "mechanics", "chef", "chefs", "waiter", "waitress", "barista",
              "cleaner", "cleaners", "lorry driver", "lorry drivers", "hgv driver",
              "delivery driver", "taxi driver", "bus driver", "train driver",
              "accountant", "accountants", "lawyer", "lawyers", "solicitor", "solicitors",
              "barrister", "architect", "engineer", "engineers", "programmer",
              "software developer", "developer", "developers", "vet", "vets", "dentist",
              "dentists", "hairdresser", "hairdressers", "farmer", "farmers", "shop worker",
              "retail worker", "office worker", "civil servant", "banker", "journalist",
              "warehouse worker", "factory worker", "security guard", "postman", "postmen")
_HOURS_WORDS = ("how many hours", "hours a week", "hours per week", "hours do", "hours does",
                "working hours", "hours of work", "what hours",
                "which hours", "overtime", "how many shifts", "shifts a week", "work week",
                "how many hours a day", "hours in a week", "how long do they work")

# Going back to work is a turn of its own: the first day, the phased return, the manager who
# wants a date, the dread that has built up over a month off. `pump-at-work` (family.py) keyed
# "back to work" for the milk question and took every one of these lines with it, and with that
# fenced off the rest fell to whatever else owned a word of them - a back-pain window for "im back
# at work next week", a broken-bone window for "how do i go back to work after a break", and the
# clothes card for "first day back at work after being off sick".
ENTRIES.append(entry(
    "hours-in-a-job",
    (_JOB_WORDS, _HOURS_WORDS),
    ("A full-time week is usually 37.5 or 40 hours on paper, and the shift shape is what changes "
     "the answer. A nurse is contracted to 37.5 hours, worked as three 12-hour shifts a week plus "
     "the odd fourth, and a care worker often has the same 12-hour pattern. A teacher's directed "
     "hours are about 1,265 a year over 195 days, and the planning and marking on top usually "
     "make 45 to 55 hours in term time. A junior doctor's rota averages no more than 48 hours a "
     "week. A plumber, electrician or builder is normally 40 to 45 hours plus emergency call-outs. "
     "A lorry driver may drive 9 hours a day, 10 of them twice a week, and no more than 56 hours "
     "in a week or 90 in a fortnight, with breaks on top. Nobody in the UK may average more than "
     "48 hours a week over 17 weeks unless they have signed to opt out."),
    # the pay, the training and the job itself are the other questions: "how much does a plumber
    # earn" and "how long does it take to become a plumber" are money and training rows
    avoid=("earn", "earns", "earning", "salary", "salaries", "paid", "pay", "wage", "wages",
           "how much does", "how much do", "charge", "charges", "become", "becoming",
           "qualification", "qualifications", "training", "course", "apprentice",
           "apprenticeship", "vacancy", "vacancies", "interview", "apply", "quit",
           "i work", "my shift", "my shifts", "my rota", "my job"),
    bias=1))


# --- the words on a contract, an appraisal and a college course -------------------------
# Six words that main passed or answered with the card next door: "what is a btec" was the
# search hedge, and "what is a gcse" and "what is an a level" got the university-requirements
# answer, which is the question about what you need one for, not what it is.
_WORK_WORDS = (
    (("redundancy", "being made redundant", "made redundant", "redundant"),
     "Redundancy is your job going, not you doing anything wrong: the employer needs fewer people "
     "in that role, so the role disappears and your contract ends. If you have two years' service "
     "you are owed statutory redundancy pay - half a week's pay for each year under 22, a week "
     "for each year from 22 to 40, a week and a half for each year over 41, capped at £700 a week "
     "and 20 years - plus your notice and any holiday you have not taken.",
     ("how much", "how do i claim", "claim", "my employer", "i have been", "i was", "voluntary",
      "offer", "payout", "calculate", "calculator", "notice", "letter", "consultation")),
    (("performance review", "appraisal", "one to one", "1 to 1", "probation review"),
     "A performance review is the regular sit-down where your manager says how the job is going "
     "and what changes, usually once or twice a year, with a rating that decides any pay rise. Go "
     "in with three things you did that made a difference and one thing you want to learn, in "
     "numbers where you can, and ask for the rating and the pay in the same conversation.",
     ("how do i prepare", "prepare", "what should i say", "nervous", "my review", "went badly",
      "bad review", "salary", "pay rise", "ask for")),
    (("btec", "btecs", "btec diploma", "btec extended diploma"),
     "A BTEC is a work-related qualification taken at school or college instead of, or alongside, "
     "A levels: the Level 3 Diploma and Extended Diploma are the usual ones and they are graded "
     "pass, merit, distinction, distinction star. They are assessed mostly by coursework rather "
     "than exams, and universities accept them - a distinction star is worth about an A at A "
     "level for entry - so they suit someone who does better on projects than in a three-hour "
     "exam.",
     ("how do i", "should i", "worth it", "my", "results", "grade", "ucas", "points", "apply",
      "college")),
    (("foundation year", "foundation course", "foundation degree", "access course"),
     "A foundation year is the extra year at the start of a degree for someone without the usual "
     "grades or the right subjects: you do a year of the basics, and passing it moves you onto "
     "the first year of the degree. It is not the same as a foundation degree, which is a "
     "two-year qualification of its own, or an Access course, which is a year at a college for "
     "adults going to university.",
     ("how do i", "should i", "worth it", "my", "student loan", "fees", "apply", "ucas",
      "which university")),
    (("personal statement", "ucas statement"),
     "A personal statement is the one page - 4,000 characters, about 47 lines - where you say why "
     "you want the course and what you have done that shows it: the subject you read round, the "
     "work or volunteering, what you want to do after. Write it in plain first person, spend most "
     "of it on the course rather than your childhood, and give it to a teacher or someone in the "
     "job to read before you send it.",
     ("how do i write", "how to write", "help me write", "start", "example", "opening",
      "my personal statement", "draft", "word count", "characters", "ucas",
      # the job version is a different page, and the cover letter has its own card
      "for a job", "job application", "job interview", "cover letter", "applying for a job")),
    (("gcse", "gcsEs", "gcses"),
     "GCSEs are the exams most pupils in England, Wales and Northern Ireland take at 16, in eight "
     "to ten subjects, graded 9 to 1 (9 is the top, 4 is a standard pass, 5 a strong pass). Maths, "
     "English language and science are the ones nearly everyone takes, and the grades decide "
     "which sixth form, college course or apprenticeship you can start.",
     # "what gcses do i need to be a nurse" is the requirement for one job, not what a GCSE is
     ("how do i revise", "revise", "revising", "results", "grades", "resit", "retake",
      "how many", "which", "choose", "my", "equivalent", "entry requirements", "do i need",
      "need to be", "need for", "to become", "to be a", "to be an", "require")),
    (("a level", "a levels", "as level", "as levels"),
     "A levels are the two-year exams taken at 16 to 18 in England, Wales and Northern Ireland, "
     "usually three subjects, graded A star to E. Each is mostly decided by exams at the end of "
     "the second year, and three good A level grades are the standard way into a degree.",
     ("how do i revise", "revise", "revising", "results", "grades", "resit", "retake",
      "how many", "which", "choose", "my", "equivalent", "entry requirements", "ucas points",
      # "a level" is inside "a level 3", and a grade 3 has its own answer
      "level 1", "level 2", "level 3", "level 4", "level 5", "grade", "grades", "do i need",
      "need to be", "to be a", "to be an", "require")),
)

WORK_DEFINITION_ASKS = ("what", "whats", "what is", "what's", "what are", "mean", "means",
                        "meaning", "define", "definition", "explain", "stand for", "stands for")


def _work_word(memory, understood):
    text = understood.get("clean") or ""
    words = understood.get("words") or []
    for keys, reply, avoid in _WORK_WORDS:
        if not any(key in text or key in words for key in keys):
            continue
        if any(word in text or word in words for word in avoid):
            continue
        return reply
    return None


ENTRIES.append(entry(
    "work-word",
    (tuple(key for keys, _, _ in _WORK_WORDS for key in keys), WORK_DEFINITION_ASKS),
    _work_word,
    bias=2,
    avoid=("how do i", "should i", "help me", "what can i do"),
))


# What a job is actually like, day to day. The lane had the pay ("how much does a plumber earn"),
# the hours ("how many hours does a nurse work") and the way in ("how do i become a plumber") and
# not the job itself: "what does a plumber do" and "what is it like being a nurse" were both a
# shrug, and "what does an hgv driver do" was answered by the computer driver that lets a system
# talk to a printer. So the day is kept as data, one paragraph per job, keyed by the job rather
# than by the phrasing, and one row reads the job off the line and hands back that paragraph.
# A job that is not in the table gets nothing, which keeps the honest pass it has today.
DAY_TABLE = {
    "plumber": "A plumber's day is a list of jobs, not one job: a dripping tap, a blocked loo, a "
    "boiler that will not fire, a bathroom that has to be piped and then signed off. Most of the "
    "work is diagnosis under a sink or in a loft, and the good plumbers earn their money on the "
    "second call-out to the same house. It is dirty and it is on your knees, and the money is in "
    "gas and heating rather than taps.",
    "electrician": "An electrician's day is part first fix, part fault-finding: chasing walls and "
    "pulling cable on a new build, then testing and certifying, or tracing why one circuit keeps "
    "tripping in a house that has been added to four times. Every finished job ends with a "
    "certificate, so the paperwork is part of the trade. It is cleaner than plumbing and more "
    "cramped - lofts, cupboards and floorboards.",
    "mechanic": "A mechanic's day is servicing and diagnosing: oil and filters on a routine "
    "service, then brakes, clutches and suspension on older cars, and an hour or two chasing a "
    "warning light that could be a sensor or a wiring fault. Fault codes point at systems, not "
    "parts, so the skill is testing rather than guessing, and the job is standing, lifting and "
    "lying under a car in all weathers.",
    "bricklayer": "A bricklayer's day is blocks and bricks to a line: setting out the corners, "
    "running a course up, keeping it plumb and level, and leaving the openings where the drawings "
    "say. It is the fastest visible trade on a site and the hardest on the back and shoulders, and "
    "cold weather stops mortar going off. Piecework rates make a good bricklayer's pay look high "
    "until you count the days lost to rain.",
    "carpenter": "A carpenter's day is either second fix in a finished house - doors, skirting, "
    "stairs, kitchens - or a workshop bench making what goes in. Site carpenters do more cutting "
    "and fitting, bench joiners do more setting out and jointing, and both need to read a drawing "
    "and work to a millimetre. Dust, noise and knees, and the good ones are never out of work.",
    "plasterer": "A plasterer's day is walls and ceilings: boarding, then skim, then the corners "
    "and the trowel work, and the finish is judged by whether a light shows a ripple across it. It "
    "is wet, heavy and fast - a ceiling has to be got right in one go before it sets - and the "
    "shoulders and wrists take the wear.",
    "painter and decorator": "A painter's day is preparation, and the painting is the easy part: "
    "filling, sanding, caulking, masking, then two coats and a careful line where the wall meets "
    "the ceiling. It is quiet, indoors and tidy work, and the difference between a good job and a "
    "bad one is nearly all in what happened before the paint went on.",
    "roofer": "A roofer's day is up a ladder or on a roof: replacing slipped tiles, fixing a leak "
    "that has been chased around a ceiling for months, felting and battening a new roof, or "
    "clearing gutters. It is the most weather-dependent trade there is, and the one where the "
    "work is done at height in the cold, so head for a roofer with insurance and a written quote.",
    "builder": "A builder's day is the whole site rather than one trade: ordering materials, "
    "setting out, keeping the trades in the right order, checking the work, and being the person "
    "the customer rings. The tools come out less than people expect and the phone never stops. "
    "Small jobs are one person and a van, and a house extension is a month of juggling.",
    "hgv driver": "A lorry driver's day is mostly waiting and then concentrating hard: loading at "
    "a depot, driving to a timed slot, waiting to be tipped, then the next one. The law allows 9 "
    "hours of driving a day, 10 twice a week, with a 45-minute break after four and a half hours, "
    "and tachograph rules are enforced. Nights out and early starts are normal, and the pay is in "
    "the hours and the overtime.",
    "delivery driver": "A delivery driver's day is a route of 80 to 150 drops and a van: load in "
    "the morning, then drive, park, carry, knock, repeat, with the phone tracking you all day. The "
    "skill is knowing where you can legally stop and how long each drop really takes. It is "
    "physical, the weather is the office, and the day is usually over when the van is empty.",
    "bus driver": "A bus driver's day is a rota of short runs with a break in the middle: the same "
    "route, the same stops, and traffic that moves the timetable around. The driving is the easy "
    "part and the passengers are the job - fares, buggies, wheelchairs, and the last bus on a "
    "Saturday night. Shifts are split, so an early start and a late finish are the same day.",
    "taxi driver": "A taxi driver's day is the waiting as much as the driving: ranks, bookings, "
    "airport runs and the school contract if you can get one. The money is in knowing when the "
    "town is busy, and the cost is in the car and the licence, which come out of the takings. "
    "Evenings and weekends are the work, so it suits people who do not want office hours.",
    "farmer": "A farmer's day follows the animals and the season: milking twice a day every day, "
    "or moving stock, checking fences and water, then the field work in its window - drilling, "
    "spraying, silage, harvest. There is no weekend in livestock, and harvest means long days "
    "while the weather holds. The income is lumpy, and a lot of it comes from subsidy and "
    "contracting as much as from the produce.",
    "nurse": "A nurse's day on a ward is a handover, then a list of patients with their "
    "medicines, observations, washes, dressings and notes, and a doctor's round somewhere in the "
    "middle. Shifts are 12 hours, three or four a week, days and nights, and the last hour is "
    "usually the busiest. The clinical work is a third of it; the rest is families, paperwork and "
    "keeping a dozen things moving at once.",
    "care worker": "A care worker's day is a round of visits or a shift in a home: getting people "
    "up, washed, dressed and fed, medicines, moving and handling, and writing down what happened. "
    "Home care is often 15-minute slots with travel between them and no paid travel time at some "
    "employers. It is personal work done at speed, and the good ones know the person as well as "
    "the task.",
    "midwife": "A midwife's day is either antenatal clinic, postnatal checks on the ward, or "
    "labour ward looking after one woman through her labour and writing the record as it happens. "
    "Shifts are 12 hours, days and nights, and labour ward is unpredictable, so a quiet night can "
    "turn into a section and a transfer in an hour. It is the most hands-on job in the hospital "
    "and the one with the most joy in it.",
    "paramedic": "A paramedic's day is a series of 999 calls, each one starting with almost no "
    "information: chest pain, a fall, a mental health crisis, a road collision. You assess, treat "
    "within your scope, decide who needs hospital and who can stay at home, and write it up "
    "between jobs. Shifts are 12 hours and breaks are whatever the calls allow.",
    "police officer": "A police officer's day is calls and paperwork: attending incidents, taking "
    "statements, arresting and processing, then a file that has to stand up in court. Response "
    "teams work shifts over 24 hours, and the honest description is long stretches of tedium with "
    "short periods of real danger. Most of the job is talking to people who are having their "
    "worst day.",
    "firefighter": "A firefighter's day is drills, checks and training around the shouts: testing "
    "kit, learning building layouts, fitness, and community visits, with the crew cooking and "
    "eating together on a 24-hour shift. Fires are a small part of the calls - more are road "
    "collisions, floods, and helping an ambulance crew get a heavy person downstairs.",
    "teacher": "A teacher's day is teaching five or six lessons, plus the parts nobody sees: "
    "planning, marking, data, parents' evening, and the break duty. Directed hours are about 1,265 "
    "a year over 195 days, and the planning and marking on top make 45 to 55 hours in term time. "
    "The classroom itself is the good part, and the holidays are the trade for the term-time "
    "hours.",
    "teaching assistant": "A teaching assistant's day is support in the classroom: helping the "
    "children who are stuck, running small groups for reading or phonics, and managing behaviour "
    "alongside the teacher. The hours are term-time only and usually finish with the children, so "
    "it fits round a family, and the pay is hourly rather than a salary. The work is with the same "
    "children all year.",
    "social worker": "A social worker's day is visits, assessments and the phone: seeing a family, "
    "writing up the visit, chasing a school or a housing officer, and a meeting about a child or "
    "an adult at risk. The caseload is the job, and the paperwork is the reason people leave. It "
    "is the work where one decision can change a family's year, so supervision and recording are "
    "taken seriously.",
    "train driver": "A train driver's day is a diagram of trips: sign on, check the unit, drive "
    "the same route with the same stops, and hand over at the other end. A computer does much of "
    "the driving, so the job is watching the line, the signals and the speed, and taking over when "
    "it does not. Shifts are unsocial and start early, and a driver's year is about 35 hours a "
    "week with rest days in the roster.",
    "barrister": "A barrister's day is either in court or in chambers preparing for it: reading "
    "the papers, drafting the questions, then standing up and doing the case, and afterwards the "
    "note on what the judge said. The self-employed model is the norm, so fees, chambers rent and "
    "the VAT are yours to run.",
    "architect": "An architect's day is drawings and coordination: developing a design, meeting "
    "the engineer and the client, checking the building regulations, and answering site queries "
    "as it is built. A project runs for years, so most days are a step on something that will not "
    "be finished for a long time.",
    "security guard": "A security guard's day is a patrol, a post or a control room: walking the "
    "building, checking passes, watching screens, and writing the log. Shifts cover 24 hours and "
    "nights are the norm, and most of the job is being alert for a long time and being calm when "
    "something happens.",
    "office worker": "An office worker's day is a list of tasks and meetings: email, a spreadsheet, "
    "a document, a call, and the meeting that interrupts all of it. The hours are usually 9 to 5 "
    "with 37.5 or 40 on paper, and the skill is holding a deadline while people ask for things. "
    "It is quiet work done sitting down.",
    "factory worker": "A factory worker's day is a station on a line: the same operation, at the "
    "pace the line sets, for a shift, with a break in the middle. Shifts run round the clock and "
    "often rotate, the noise needs ear protection, and the pay is a rate per hour plus shift "
    "allowance.",
    "pharmacist": "A pharmacist's day is prescriptions: checking what the doctor has written, "
    "dispensing, answering the counter, and giving advice on a cough or a rash. The clinical part "
    "is spotting a dose that is wrong or a pair of medicines that should not mix, and the shop "
    "work is the rest.",
    "librarian": "A librarian's day is the desk, the stock and the enquiries: helping people find "
    "things, ordering and cataloguing, running sessions for children or for a reading group, and "
    "keeping the computers working. The quiet is a myth - it is public-facing work with a "
    "research job attached.",
    "doctor": "A doctor's day is a clinic list or a ward round: ten-minute appointments in general "
    "practice, or a hospital round with the notes and the tests for each patient, then the jobs "
    "it produces - referrals, prescriptions, a call to a family. GPs carry a list of 30 or more "
    "appointments a day and the hospital work is shifts. Most of it is pattern-spotting and "
    "explaining, and the pressure is the clock.",
    "dentist": "A dentist's day is a list of 15 to 30 minute appointments: check-ups, fillings, "
    "and the emergencies squeezed in at the end of the morning. Most patients need a clean, a "
    "filling or reassurance, and the work is done sitting down in a lit box with an assistant. The "
    "practice is a business, so the diary and the recall list matter as much as the drill.",
    "vet": "A vet's day is a morning of consultations - vaccinations, skin, limps, a cat that will "
    "not eat - and an afternoon of operations, dentals and x-rays. Large animal vets are out on "
    "farms instead, and out-of-hours cover is shared between practices. It is a business as well "
    "as a profession, so the conversation about cost is part of the job.",
    "chef": "A chef's day is prep in the morning and service in the evening: deliveries, stocks, "
    "sauces, mise en place, then the rush where every plate is timed against a table's order. "
    "Split shifts and 50 to 60 hour weeks are normal in restaurants, and the kitchen is hot, "
    "loud and close. The satisfaction is at the pass when it all lands at once.",
    "waiter": "A waiter's day is sections and covers: taking orders, carrying, serving, clearing, "
    "and knowing the menu well enough to answer a question about an allergy. Shifts are split "
    "around lunch and dinner, the pay is minimum wage plus tips, and the job is on your feet for "
    "eight hours. Good service is mostly reading the table and being there when needed.",
    "hairdresser": "A hairdresser's day is a column of appointments, each with a consultation and "
    "a finish: colour work in the morning, cuts in the afternoon, and regulars who expect the same "
    "result every six weeks. It is on your feet with your arms up, and the money depends on "
    "building a clientele who ask for you. Saturdays are the busiest day of the week.",
    "cleaner": "A cleaner's day is a list of rooms and a time limit: bathrooms, kitchens, floors, "
    "bins, and the parts a household forgets. Domestic cleaning is usually hourly and self-"
    "employed, office cleaning is an early or late shift, and hotel work is rooms at a set number "
    "of minutes each. It is physical, mostly invisible, and judged only when it is done badly.",
    "retail worker": "A retail worker's day is the shop floor and the till: deliveries and "
    "replenishment before opening, then serving, fitting rooms, stock checks and the queue at the "
    "end of the day. Hours are shifts across the week, often including weekends, and the pay is "
    "close to the minimum wage with staff discount. Most of the job is being pleasant to people "
    "who are in a hurry.",
    "postman": "A postman's day is sorting in the depot, then a walk or a van round of the same "
    "streets with a bag and a bundle of parcels. The round is fixed, the weather is not, and the "
    "walking is 10 to 15 miles on a foot round. It finishes when the round is done, and Christmas "
    "is the season everyone remembers.",
    "warehouse worker": "A warehouse worker's day is on a pick list: a scanner, a trolley, and the "
    "same aisles at a rate the system measures. Goods-in and loading is heavier, packing is "
    "quicker, and shifts run round the clock in the big sheds. It is standing, lifting and walking "
    "all day, and the target is the reason the job is tiring.",
    "accountant": "An accountant's day is client work against a deadline: bookkeeping, VAT returns, "
    "year-end accounts and tax, with January and the filing dates setting the rhythm. Practice "
    "accountants see a dozen small businesses a week; in-house ones close the month and explain it "
    "to managers. The work is detail and software, and the busy season is genuinely busy.",
    "solicitor": "A solicitor's day is files and clients: reading, advice, letters, negotiation, "
    "and time recorded in six-minute units. Conveyancing is volume, family and crime are court "
    "dates, and commercial work is documents. The pressure is deadlines and other people's money, "
    "and most of the job is writing clearly about what should happen next.",
    "software developer": "A developer's day is a stand-up, then a task: reading code someone else "
    "wrote, writing a small piece of it, testing it, then reviewing someone else's change. The "
    "hard part is understanding the system, not typing, and most days include one meeting and one "
    "surprise. It is desk work, and it can be done from home more than most jobs.",
    "engineer": "An engineer's day depends which engineer: a design engineer works in CAD and "
    "calculations, a site engineer sets out and checks work against drawings, and a maintenance "
    "engineer is called when a machine stops. All of them are solving a problem with a "
    "constraint, and the paperwork is the record that the thing is safe.",
    "journalist": "A journalist's day is the diary, the calls and the deadline: find the story, "
    "check it with two sources, write it to length, and file before the page closes. Local "
    "reporting is council meetings and court lists; newsroom work is a running feed. The hours are "
    "unpredictable and the pay is low at the start.",
    "civil servant": "A civil servant's day is policy, casework or a service: reading, drafting, "
    "briefing a minister or a manager, and answering correspondence to a deadline. The work is "
    "steady, the process is the point, and the hours are usually 37.5 a week with flexitime. "
    "Change of government changes the priorities, not the building.",
    "banker": "A banker's day is clients who need money: reading accounts, structuring a loan, "
    "credit papers and meetings. High street banking is branch appointments and mortgages; "
    "investment banking is deals and very long hours. The pay is high at the top and ordinary at "
    "the counter, and the two jobs have almost nothing in common.",
}

# The words people use for a job, including the trade nicknames, mapped onto the table above. The
# longest word wins, so "lorry driver" is a lorry driver and not a driver of anything.
DAY_ALIASES = (
    ("lorry driver", "hgv driver"), ("hgv driver", "hgv driver"), ("hgv", "hgv driver"),
    ("truck driver", "hgv driver"), ("lorry drivers", "hgv driver"),
    ("sparky", "electrician"), ("sparkies", "electrician"),
    ("chippy", "carpenter"), ("chippies", "carpenter"), ("joiner", "carpenter"),
    ("brickie", "bricklayer"), ("brickies", "bricklayer"),
    ("painter and decorator", "painter and decorator"), ("decorator", "painter and decorator"),
    ("care worker", "care worker"), ("carer", "care worker"), ("carers", "care worker"),
    ("support worker", "care worker"),
    ("shop worker", "retail worker"), ("retail worker", "retail worker"),
    ("sales assistant", "retail worker"),
    ("police officer", "police officer"), ("copper", "police officer"),
    ("software developer", "software developer"), ("programmer", "software developer"),
    ("developer", "software developer"), ("web developer", "software developer"),
    ("teaching assistant", "teaching assistant"), ("ta", ""),
    ("solicitor", "solicitor"), ("lawyer", "solicitor"),
    ("accountant", "accountant"), ("bin man", ""),
)

DAY_WORDS = ("what does", "what do", "what is it like", "whats it like", "day to day",
             "all day", "a typical day", "typical day", "actually do", "actually does",
             "is being a", "is being an", "hard work", "like being", "the job like",
             "what happens in", "what is a day")


DAY_JOB_WORDS = set(_JOB_WORDS)
for _name in DAY_TABLE:
    DAY_JOB_WORDS.add(_name)
    DAY_JOB_WORDS.add(_name + "s")
for _alias, _name in DAY_ALIASES:
    if _name:
        DAY_JOB_WORDS.add(_alias)


def _job_named(line):
    """The job the line names, and where in the line it is named."""
    best = None
    pairs = list(DAY_ALIASES)
    for key in DAY_TABLE:
        pairs.append((key, key))
        pairs.append((key + "s", key))
    for word, name in pairs:
        if not name:
            continue
        hit = re.search(r"\b" + re.escape(word) + r"\b", line)
        if hit and (best is None or len(word) > best[0]):
            best = (len(word), name, hit.start())
    return (best[1], best[2]) if best else (None, -1)


# A line that asks what a job is like asks about the trade; a line that says "my" or "about a"
# is asking about one animal, room or person, and "what does a vet do about a limping dog" is not
# a question about a vet's working day.
_ABOUT_SOMETHING = re.compile(r"\b(my|our)\b| about | with a | with my ")


def _job_day(memory, understood):
    line = " " + ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _ABOUT_SOMETHING.search(line):
        return None
    name, where = _job_named(line)
    if not name:
        return None
    # The reading reaches the previous line too when the line alone found nothing, so after "im a
    # teacher" the words "what do i do" arrive here as "im a teacher what do i do" - the job is in
    # the earlier line and the question is not about it. The ask has to open on the job for this
    # row to answer, which is where a question about a job's day begins and where "what do i do"
    # does not.
    # "what do i do" is not the ask about a job: the word "do" is in it and "what do" is one of
    # the ask shapes, so after "im a teacher" the next line's "what do i do" was read as a
    # question about a teacher's day. A first-person ask is about the person, never about the job.
    if re.search(r"\b(?:what|how) (?:do|does|should|can|shall|could) (?:i|we)\b", line):
        return None
    opens = [line.find(word) for word in DAY_WORDS if word in line]
    if not opens or min(opens) > where:
        return None
    return DAY_TABLE.get(name)


ENTRIES.append(entry(
    "what-a-job-is-like",
    (DAY_WORDS, tuple(sorted(DAY_JOB_WORDS))),
    _job_day,
    # the pay, the hours, the training and the person's own job are all other rows: "how much
    # does a plumber earn", "how many hours does a nurse work" and "how do i become a plumber"
    # must keep the answers they have
    avoid=("earn", "earns", "earning", "salary", "salaries", "paid", "pay", "wage", "wages",
           # the price of the trade is the costs table's answer: "what does a plumber cost to fix
           # a leak" is a quote, not a working day, and the "cost" shape reached this row because
           # the ask gate only needs a day word and the job's name
           "how much", "charge", "charges", "cost", "costs", "price", "prices", "quote",
           "quotes", "cheapest", "become", "becoming", "qualification",
           "qualifications", "course", "apprentice", "apprenticeship", "vacanc",
           # not the bare word "training": the matcher's loose forms read "train driver" as
           # that word, so it fenced off "what does a train driver do" - my own job, vetoed by
           # my own avoid. The shapes below are the training question itself.
           "training course", "training needed", "training to be", "what training",
           "interview", "apply", "quit", "resign", "hours", "shift", "shifts", "rota",
           "holiday", "holidays", "my job", "my work", "i work", "my boss", "my manager",
           "sack", "sacked", "made redundant", "redundancy", "cv", "cover letter",
           # "what do you buy a nurse for her birthday" is a gift question and the job word is
           # only in it as the person being bought for, so a "what do" shape plus a job word is
           # not enough on its own: the buying, naming and dressing shapes stand down here.
           "buy", "buys", "buying", "bought", "present", "presents", "gift", "gifts",
           "birthday", "christmas", "wedding", "anniversary", "suggest", "recommend",
           "call", "calls", "say to", "give", "gives", "wear", "wears", "costume",
           "fancy dress", "joke", "jokes", "song", "film", "book", "quiz",
           "get", "gets", "getting", "end of term"),
    bias=6))

# --- a child's first job, which is usually a paper round -----------------------------------
# "what age can you get a paper round" and "how much does a paper round pay" both reached the
# rounding card, because a round is also a maths word and the card is keyed on "how" and "what";
# "should i let my son get a paper round" was a decision the warm pool would not call, and "can my
# daughter get a paper round" was the search hedge. The age, the hours and the money are facts, so
# the row answers them, and which one it gives depends on what the line asks for.
PAPER_ROUND_PAY = ("A paper round is paid per round rather than per hour, usually £10 to £25 a "
                   "week and paid by the newsagent on the same day each week. Round and round the "
                   "shops on the way: the ones with their own delivery staff pay a little more than "
                   "an agency round, and a Sunday-only round is the smallest way to start.")

PAPER_ROUND_AGE = ("Thirteen is the usual age: the law lets a child work part-time from 13, and "
                   "below that almost no newsagent will take them on - a few councils allow some "
                   "jobs from 12, and the council's child employment office will say what yours "
                   "does. Under 16 they need a work permit from the council, which the newsagent "
                   "applies for. The hours are capped too: not before 7am or after 7pm, two hours "
                   "on a school day and 12 hours a week in term time, and up to 35 hours a week in "
                   "the school holidays.")

PAPER_ROUND_WHY = ("Let them try a week of it before you decide, because the job is getting up at "
                   "half six in the rain six days a week whatever the weather, and that is the part "
                   "worth finding out. A round within walking distance is the one to take: a lift "
                   "to the start of it at 6.30am quietly ends most paper rounds by half term. The "
                   "money is small - £10 to £25 a week - so treat it as the lesson in turning up "
                   "rather than as earnings.")

PAPER_ROUND_WORTH = ("A paper round is a decent first job when the round is short and close to home: "
                     "it is the lesson in turning up whatever the weather, which is most of what any "
                     "employer wants, and it pays £10 to £25 a week. The cost is the hour before "
                     "school, so pick one that can be walked in half an hour and check the homework "
                     "still fits. Under 16 the newsagent gets a work permit from the council first.")

PAPER_ROUND_SELF = ("Ask at the newsagent on your own street first, and take a parent with you the "
                    "first time: they will want to know your age, and under 16 they apply to the "
                    "council for your work permit. Say which mornings you can do and stick to them, "
                    "because the round goes out whether or not you turn up - turning up is the whole "
                    "of what they are paying you for.")

PAPER_ROUND_WORDS = ("paper round", "paper rounds", "newspaper round", "newspaper rounds",
                     "paperboy", "papergirl", "paper delivery", "deliver papers",
                     "delivering papers", "paper route")

PAPER_ROUND_ASK = ("job", "jobs", "work", "pay", "pays", "paid", "wage", "wages", "earn",
                   "earns", "money", "much", "age", "old", "older", "start", "starts", "allow",
                   "allowed", "legal", "let", "should", "idea", "worth", "can", "could", "when",
                   "what", "how", "13", "14", "15", "twelve", "thirteen", "fourteen", "fifteen",
                   "want", "wants", "wanted", "asking", "thinking", "ask")

PAPER_ROUND_PAY_ASK = re.compile(r"\b(?:pay|pays|paid|wage|wages|earn|earns|earning|money|"
                                 r"how much|much|rate|rates)\b")
PAPER_ROUND_WORTH_ASK = re.compile(r"\b(?:good idea|good|worth|any good|decent|ok|okay|"
                                   r"bad idea|recommend|better|worse)\b")
PAPER_ROUND_AGE_ASK = re.compile(r"\b(?:age|old|older|young|years|year|allow|allowed|legal|law|"
                                 r"rules|permit|hours|start|starts|begin|when)\b")


# Who the advice is for is the whole line's difference: "should i let my son get a paper round" is
# a parent weighing it up, and "i want a paperboy job" is the child asking how to get one, so the
# same row would answer "Let them try a week of it" at the person who wants the round themselves.
PAPER_ROUND_SOMEONE = re.compile(r"\b(?:my|our)\s+(?:son|daughter|child|kid|teenager|boy|girl|"
                                 r"oldest|eldest|youngest)\b|\bshould i let\b|\blet (?:him|her|"
                                 r"them)\b")


def _paper_round(memory, understood):
    """The money, the age and the rules, or the advice, whichever the line is asking for."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if PAPER_ROUND_PAY_ASK.search(said):
        return PAPER_ROUND_PAY
    if PAPER_ROUND_WORTH_ASK.search(said):
        return PAPER_ROUND_WORTH
    if PAPER_ROUND_AGE_ASK.search(said):
        return PAPER_ROUND_AGE
    if PAPER_ROUND_SOMEONE.search(said):
        return PAPER_ROUND_WHY
    return PAPER_ROUND_SELF


ENTRIES.append(entry(
    "a-paper-round",
    (PAPER_ROUND_WORDS, PAPER_ROUND_ASK),
    _paper_round,
    # paper is paper in a dozen other lines: a newspaper to read, a wallpaper, a paper cut, and
    # paperwork, which is its own row here.
    avoid=("newspaper", "newspapers", "wallpaper", "wallpapering", "toilet", "kitchen roll",
           "paper cut", "paper cuts", "paper trail", "paperwork", "wrapping paper",
           "paper plates", "paper towels", "exam paper", "past paper", "past papers",
           "writing paper", "printer", "printing", "essay", "essays", "recycling", "bin", "bins"),
    bias=2))
# The record is the subject, so the key is the record and the job, not the phrasing of the ask.
def _a_criminal_record(memory, reading):
    """The record and the job: what you declare, and when it stops counting."""
    said = ((reading or {}).get("norm_text") or (reading or {}).get("clean") or "").lower()
    # How long a DBS check takes to come back is about eight weeks and nothing to do with
    # spent convictions, and "how long does a dbs check take" was the timing branch.
    if "dbs" in said and re.search(r"\b(how long|how many weeks|how many days|takes?|"
                                   r"come back|wait|waiting|delay|delayed|chase)\b", said):
        return ""
    if re.search(r"\b(how long|how many years|when does it|expire|expires|spent after|"
                 r"come off|comes off|goes away|gone away|stay on|stays on|wiped|cleared)\b",
                 said) or re.search(r"\bgo(?:es)? on (?:my|your) record\b", said):
        return ("Most convictions become spent after a set time that runs from the end of the "
                "sentence - a year for a fine or a community order, and longer for prison - and "
                "after that you can answer no to most employers. A prison sentence of over four "
                "years never becomes spent, and a caution is spent as soon as it is given.")
    return ("A record is not an automatic no: most employers can ask only about unspent "
            "convictions, and a spent one or a caution need not be declared unless the job is "
            "exempt - work with children, patients, or in the justice system. Those jobs ask for "
            "a standard or enhanced DBS check, where an old minor caution can be filtered out, so "
            "apply and see rather than deciding for them.")


ENTRIES.append(entry("a-criminal-record-and-a-job",
          # One group, because the record is the subject whether or not the line names a job:
          # "will a caution show on a dbs" names no job at all and is the same question.
          ("criminal record", "police record", "on your record", "on my record",
           # the two words of the phrase are keys as well as the phrase, because a phrase covers
           # one word of the two a row needs: "i have a criminal record" is the whole subject
           "criminal", "record", "conviction", "convictions", "convicted", "caution", "cautions",
           "spent conviction", "spent", "unspent", "dbs", "dbs check", "disclosure",
           "been to prison", "been in prison", "prison record",
           # the job is the other half of the question and it is often one word of the line
           "job", "jobs", "employer", "employers", "apply", "applying", "application",
           "interview", "career", "careers", "declare", "nurse", "nursing", "teacher",
           "teaching", "care home", "volunteer", "volunteering", "children"),
          _a_criminal_record,
          # The record has to be in the line. "job", "employer", "apply", "interview", "nurse"
          # and "children" are keys because the job is the other half of the question, and one key
          # word is enough for a row, so on their own they made every ordinary job line a criminal
          # record question: "i have a job interview tomorrow" and "how do i apply for a job" were
          # both told about unspent convictions. This is the gate that asks for the record, and it
          # is a gate rather than a second key group because "will a caution show on a dbs" has no
          # job word in it at all and is the same question.
          ask=("record", "records", "conviction", "convictions", "convicted", "caution",
               "cautions", "criminal", "spent", "unspent", "dbs", "disclosure", "prison",
               "declare", "declared", "declaring"),
          # A criminal record and a trip to America is a real question with a real answer, and
          # this row is not it: "will a criminal record stop me travelling to america" was given
          # the job card, which says nothing about an ESTA. The travel words stand the row down
          # until that card exists, so the line keeps main's (wrong but harmless) answer.
          avoid=("travel", "travelling", "traveling", "traveller", "abroad", "holiday",
                 "holidays", "america", "american", "the states", "usa", "esta", "visa",
                 "visas", "immigration", "border", "entry clearance", "emigrate", "moving to"),
          bias=2))
# --- passed over for a promotion is information, not a sentence ---------------
# The turns after a promotion comes up and does not arrive. Every row that mentions promotion
# wanted a different question - "how do i ask for one" is the promotion-case card, "never get
# promoted" needs a decision word - so the setback fell to whatever else the words touched:
# "someone else got the promotion" answered "Brilliant. Really pleased for you.", "i wasnt
# promoted" answered "Congratulations - that's lovely news.", and "i keep getting turned down for
# promotion" reached the film table's turned-down-a-pick row ("do one small thing you used to
# enjoy today"). The news is the line, and the answer is what to do with the reason.
_PASSED_OVER = ("turned down for", "turned me down", "turned it down for", "passed over",
                "passed up", "overlooked for", "didnt get the promotion", "did not get the promotion",
                "didnt get promoted", "did not get promoted", "wasnt promoted",
                "was not promoted", "not promoted", "no promotion", "lost out",
                "turned down", "denied", "blocked", "rejected", "unsuccessful", "went to someone else",
                "gave it to someone else", "gave the promotion to", "gave the job to someone",
                "someone else got", "someone else was", "she got it", "he got it", "they got it",
                "they picked", "they chose", "lost it", "fell through", "didnt happen",
                "keep getting", "keeps happening", "promoted someone else",
                "promoted another", "someone else over me", "over me", "past me",
                "went to another", "someone younger", "someone less experienced",
                "the other candidate", "i was the better candidate", "not me",
                "instead of me", "in front of me", "above me",
                # the role going away is the same news before anybody is chosen
                "withdrawn", "withdrew", "pulled the role", "pulled the job",
                "put on hold", "frozen", "budget was cut", "no longer hiring")

ENTRIES.append(entry(
    "passed-over-for-promotion",
    (("promotion", "promoted", "the job i applied for", "the role i applied for",
      "senior role", "the higher grade", "the grade above", "step up"),
     _PASSED_OVER),
    ("That stings, and it is usually about the case rather than the person - so get the reason in "
     "writing: what the role needs that they have not seen from you yet, and when it is reviewed "
     "again. Do one of those "
     "things where people can watch - run the project, cover the report, train the new starter - "
     "because a promotion is decided on evidence someone else can point at. If the answer is that "
     "there is no role to give you, ask what one would look like and whether it is funded, and put "
     "your own date on the decision. Twice with no reason is the company answering you."),
    # the ask, the offer and the raise are other questions, and a promotion the person turned
    # down themselves is the opposite news: "i turned down a promotion" is a choice they made
    avoid=("how do i ask", "how to ask", "should i ask", "can i ask", "how do i get promoted",
           "how do i get a promotion", "what should i say", "case for", "been offered",
           "offered me", "offered a", "i turned down a promotion", "i turned down the promotion",
           "declined the promotion", "turned down the job offer", "pay rise", "raise",
           # the person's own promotion is the opposite news, and one loose "again" in the
           # setback part was enough to answer "i got promoted again" with this row
           "i got promoted", "i was promoted", "ive been promoted", "i have been promoted",
           "they promoted me", "i got the promotion", "ive got the promotion",
           "i am now", "im now a",
           "salary", "how much", "more money", "interview", "application", "applying"),
    bias=1))




# --- what a job pays ---------------------------------------------------------
# "How much do nurses earn" and "what is the average salary for a teacher" were a shrug, and
# "how much do care workers get paid" was a houseplant answer, because the only pay rows in the
# tree were about one person's own pay (a pay rise, a payslip, a graduate starting salary). The
# jobs are the ones DAY_TABLE above already names, so a job is read off one vocabulary, and the
# figures below are the usual UK range for a full-time year, in pounds, before tax. Ranges, not
# a single number: a person asking this wants the ballpark to argue with, and a range is honest
# about a country where the same job pays different money in different places.
#
# Cleaner is not here: "how much does a cleaner get paid" is the price of a cleaner's hour and
# the cleaning rows answer that at the rate a cleaner actually keeps. Neither is "carer": an
# unpaid carer's "pay" is Carer's Allowance, which is a benefits question, not a wage.
PAY_TABLE = {
    "nurse": "A nurse in the NHS starts on band 5, about £30,000, and goes up to about £36,500 "
    "with experience; a specialist or ward manager is £37,000 to £45,000. London adds about "
    "£5,000, and nights, weekends and overtime are on top of the basic pay.",
    "care worker": "£12 to £13.50 an hour, about £23,000 to £26,000 full time; night shifts and "
    "sleep-ins add to that, and a senior care assistant gets £26,000 to £28,000. Experience and a "
    "level 3 qualification are what move it up.",
    "midwife": "Band 5 from about £30,000 to £36,500, and a midwife with experience on band 6 is "
    "£37,000 to £44,000. Unsocial hours add about 20% on top, so the take-home is higher than the "
    "band suggests.",
    "paramedic": "Band 5, so about £30,000 to £36,500, with a specialist paramedic on band 6 up to "
    "about £44,000. Shift allowance is on top and overtime is usually there for the taking.",
    "doctor": "A foundation doctor starts at about £38,000 and is on about £44,000 in the second "
    "year; a GP or a consultant is £70,000 to £130,000 depending on sessions, years and private "
    "work. The overtime and unsocial hours are already in those figures.",
    "dentist": "An NHS dentist is paid per item of treatment, roughly £30,000 to £65,000 a year, "
    "and a practice owner doing private work makes £80,000 to £150,000. What a patient pays for a "
    "check-up is a different number and a different question.",
    "pharmacist": "£40,000 to £50,000 in a community pharmacy, £45,000 to £55,000 in a hospital, "
    "and locum shifts at £30 to £45 an hour. A superintendent or a pharmacy owner earns more.",
    "vet": "£36,000 to £50,000 for a small animal vet with a few years in, and £60,000 upwards with "
    "a certificate or a partnership. Out-of-hours cover is paid on top and a locum day is £300 to "
    "£450.",
    "social worker": "Newly qualified is about £32,000, and with two or three years in it is "
    "£34,000 to £44,000; a senior practitioner or team manager is £44,000 to £55,000. Agency "
    "social workers are paid by the hour, often £30 to £40.",
    "teacher": "A classroom teacher in England starts at £31,650 and the main scale runs to "
    "£43,600; the leadership scale is £49,000 to £120,000. London adds 5% to 10%, and Scotland and "
    "Wales have their own scales.",
    "teaching assistant": "About £23,000 to £26,000 full time, £12.50 to £15 an hour, and the pay "
    "is spread over 12 months because the job is term time only. A higher level teaching assistant "
    "with a specialism gets £27,000 to £30,000.",
    "police officer": "A constable starts at about £29,000 and reaches about £46,000 after seven "
    "years; a sergeant is £48,000 to £52,000. Overtime, night duty and London weighting are on top.",
    "firefighter": "About £30,000 as a trainee firefighter, around £42,000 once competent with the "
    "shift allowance included, and a crew manager is £45,000 upwards. The shifts are what the "
    "money is for.",
    "hgv driver": "£14 to £18 an hour, about £32,000 to £42,000 a year. Nights out, ADR and weekend "
    "or overtime shifts push a lorry driver past £45,000, and agency work pays more in the weeks "
    "nobody wants.",
    "delivery driver": "£12 to £14 an hour, about £25,000 to £30,000, and parcel firms that pay per "
    "drop pay well in December and badly in January. Your own van and fuel come out of it if you "
    "are a subcontractor.",
    "bus driver": "£13 to £16 an hour, about £28,000 to £34,000, with London a few thousand more. "
    "Split shifts and unsocial hours are the trade-off, and overtime is regular.",
    "train driver": "£45,000 to £65,000 as a qualified driver, and more on long-distance and freight "
    "work. Training pay is lower and the training takes nine to twelve months.",
    "taxi driver": "Self-employed, so it is takings minus the car: £400 to £700 a week coming in, "
    "which is about £25,000 to £35,000 a year before fuel, insurance, maintenance and licensing.",
    "chef": "£13 to £17 an hour, about £26,000 to £35,000; a head chef is £32,000 to £45,000, and "
    "hotels and fine dining pay more. The hours are long and the pay is per hour worked.",
    "waiter": "The minimum wage and up: £11.44 to £13 an hour, plus tips, which are often pooled and "
    "shared out. A head waiter or supervisor is £13 to £15 an hour.",
    "retail worker": "£12 to £13 an hour, about £23,000 to £26,000 full time. A supervisor or team "
    "leader is £26,000 to £30,000, and Sunday and bank holiday premiums make a difference to the "
    "year.",
    "warehouse worker": "£12 to £14 an hour, about £24,000 to £28,000. Night shifts pay 20% to 30% "
    "more and agency rates move with demand, so the same job pays differently a mile apart.",
    "factory worker": "£12 to £14 an hour, £24,000 to £29,000 full time, with 15% to 30% extra for "
    "nights and rotating shifts. Skilled machine setting and maintenance is where the money is.",
    "security guard": "£12 to £14 an hour, about £24,000 to £28,000, and the SIA licence is what "
    "makes you employable at all. Nights, weekends and site work pay more than a reception desk.",
    "postman": "£13 to £14 an hour, about £26,000 to £28,000, with driving duties and Christmas "
    "overtime on top. A delivery office manager is £30,000 to £35,000.",
    "office worker": "£23,000 to £30,000 for an administrator, and an office manager is £30,000 to "
    "£38,000. London adds £3,000 to £5,000, and the sectors that pay best are finance and law.",
    "accountant": "£35,000 to £55,000 once qualified, and about £38,000 newly qualified in practice. "
    "A finance manager in industry is £50,000 to £65,000, and London and the big firms pay more "
    "again.",
    "solicitor": "About £40,000 newly qualified outside London, and £60,000 to £90,000 with five "
    "years in. A City firm pays £100,000 and up from day one, for hours to match.",
    "software developer": "£40,000 to £65,000 with a few years in, and senior or lead roles £70,000 "
    "to £100,000. Contract work is £400 to £600 a day with no holiday pay, which is the trade.",
    "engineer": "£28,000 to £35,000 starting, £35,000 to £50,000 chartered, and £50,000 upwards for "
    "a principal or a specialist. Site, offshore and defence work pays a premium over an office "
    "desk.",
    "architect": "£32,000 to £40,000 newly qualified, £45,000 to £60,000 with a decade in, and a "
    "partner or a practice owner more than that. The years of low pay before qualification are the "
    "part people do not expect.",
    "journalist": "£24,000 to £32,000 at a local paper or a trade title, and £35,000 to £50,000 in "
    "a national newsroom. Freelance is paid per word and the money arrives late.",
    "librarian": "£26,000 to £34,000, and a chartered or senior librarian is £35,000 to £45,000. "
    "Council library budgets are why the top of that range is thin.",
    "civil servant": "An administrative officer is £25,000 to £28,000, an executive officer £28,000 "
    "to £34,000, and a higher executive officer £34,000 to £40,000. The London pay bands add £4,000 "
    "to £5,000.",
    "banker": "Branch and mortgage staff are £25,000 to £35,000 plus a small bonus; an investment "
    "banking analyst is £60,000 to £100,000 with a bonus that can double it, for twice the hours.",
    "barrister": "£25,000 to £40,000 in the first years of practice, £60,000 to £150,000 with a "
    "decade in, and a handful earn far more. Chambers rent, insurance and no sick pay come out of "
    "it.",
    "mechanic": "£13 to £18 an hour, £27,000 to £36,000, and a master technician or a main dealer "
    "specialist is £35,000 to £45,000. Your own tools are part of the deal.",
    "plumber": "An employed plumber is £28,000 to £36,000. Self-employed, the takings are £40 to £80 "
    "an hour, which sounds like more until the van, tools, insurance, pension and quiet weeks are "
    "paid for - about £40,000 to £60,000 a year.",
    "electrician": "An employed electrician is £30,000 to £38,000, and self-employed takings are "
    "£40 to £70 an hour before the van, the test gear, the insurance and the certification. A "
    "commercial or industrial spark earns more than a domestic one.",
    "hairdresser": "£12 to £15 an hour employed, about £23,000 to £28,000, plus tips. Self-employed "
    "in a chair you rent, the takings are the cut price less the rent, so £25,000 to £40,000 is the "
    "usual spread.",
    "bricklayer": "£15 to £20 an hour employed, £30,000 to £40,000, and piecework on a site can pay "
    "more in a good week. Rain and winter are the unpaid part.",
    "carpenter": "£15 to £20 an hour employed, about £30,000 to £40,000, and a bench joiner or a "
    "site carpenter with their own tools and van can clear £45,000 on price work.",
    "painter and decorator": "£14 to £18 an hour employed, £28,000 to £36,000, and self-employed "
    "day rates of £150 to £250. The preparation nobody sees is what the day rate is really for.",
    "builder": "A site manager is £40,000 to £55,000, a general builder running small jobs £35,000 "
    "to £50,000, and a self-employed builder's profit depends on the jobs they price well.",
    "roofer": "£14 to £19 an hour employed, £28,000 to £38,000, and a self-employed roofer's day "
    "rate is £180 to £280. Bad weather weeks are unpaid, which is why the day rate is high.",
    "plasterer": "£15 to £20 an hour employed, £30,000 to £40,000, and pricework on a new build is "
    "£3 to £5 a square metre. A good plasterer's day rate is £200 to £250.",
    "nursery nurse": "£12 to £14 an hour, about £22,000 to £25,000 full time, and a level 3 "
    "childcare qualification is what gets you the job. A room leader is £25,000 to £28,000 and a "
    "nursery manager £30,000 to £35,000.",
    "kitchen porter": "£11.50 to £13 an hour, about £21,000 to £24,000 full time, and it is usually "
    "the way into a kitchen. A commis chef with a year in is £22,000 to £25,000.",
    "bar staff": "The minimum wage and up, £11.44 to £13 an hour, plus tips and often a meal on "
    "shift. A shift supervisor or bar manager is £13 to £16 an hour, and the late finishes are part "
    "of the job.",
    "refuse collector": "£12 to £14 an hour, about £24,000 to £28,000, and the early starts are "
    "the trade. The driver of the round, or a team leader, is £28,000 to £32,000.",
    "receptionist": "£12 to £14 an hour, about £23,000 to £26,000 full time. A medical or dental "
    "receptionist is similar, and a hotel reception manager is £28,000 to £32,000.",
    "soldier": "£25,000 to £30,000 as a new soldier, with food and accommodation on top, and "
    "£35,000 to £45,000 as a sergeant with a few years in. Trade and specialist pay is extra, and "
    "the pension is the real perk.",
    "farmer": "It depends on the farm and the year: an employed farm worker is £12 to £14 an hour, "
    "about £25,000 to £29,000, and a farm manager £35,000 to £50,000. The owner's income is the "
    "profit, which can be nothing.",
}

# The words that make a line a question about what a job pays. "make" is deliberately absent:
# with it, "how do you make a nurse laugh" read as a pay question. A question about the hours,
# the holiday, the training or the job itself is another row's, and the avoid list below says so.
PAY_WORDS = ("how much", "how many", "much", "paid", "pay", "pays", "paying", "earning",
             "earn", "earns", "earned", "salary", "salaries", "wage", "wages", "income",
             "rate", "hourly", "per hour", "an hour", "a year", "a week", "average", "typical",
             "usual", "starting pay", "starting salary", "starting wage")

# The names people use for the jobs above, including the ones DAY_TABLE does not carry at all.
# "nursery nurse" is here because the longest-match read of "nursery nurse" is the word "nurse",
# and an NHS nurse's band 5 was answering a question about a nursery.
PAY_ALIASES = (
    ("nursery nurse", "nursery nurse"), ("nursery nurses", "nursery nurse"),
    ("nursery worker", "nursery nurse"), ("nursery practitioner", "nursery nurse"),
    ("kitchen porter", "kitchen porter"), ("kitchen porters", "kitchen porter"),
    ("bar staff", "bar staff"), ("bartender", "bar staff"), ("bartenders", "bar staff"),
    ("bar worker", "bar staff"), ("receptionist", "receptionist"),
    ("receptionists", "receptionist"), ("soldier", "soldier"), ("soldiers", "soldier"),
    ("army", "soldier"), ("support worker", "care worker"), ("support workers", "care worker"),
    ("care assistant", "care worker"), ("care assistants", "care worker"),
    ("shop assistant", "retail worker"), ("shop assistants", "retail worker"),
    ("sales assistant", "retail worker"), ("sales assistants", "retail worker"),
    ("lorry driver", "hgv driver"), ("lorry drivers", "hgv driver"),
    ("truck driver", "hgv driver"), ("truck drivers", "hgv driver"),
    ("binman", "refuse collector"), ("bin man", "refuse collector"),
    ("binmen", "refuse collector"), ("bin men", "refuse collector"),
    ("refuse collector", "refuse collector"), ("refuse collectors", "refuse collector"),
)

PAY_JOB_WORDS = set()
for _name in PAY_TABLE:
    PAY_JOB_WORDS.add(_name)
    PAY_JOB_WORDS.add(_name + "s")
for _alias, _name in DAY_ALIASES:
    # "carer" and "carers" are left out on purpose: an unpaid carer's money is Carer's
    # Allowance, which is a benefits answer, not a wage for a care worker.
    if _name in PAY_TABLE and _alias not in ("carer", "carers"):
        PAY_JOB_WORDS.add(_alias)
for _alias, _name in PAY_ALIASES:
    if _name in PAY_TABLE:
        PAY_JOB_WORDS.add(_alias)

# A first-person ask is about the person asking, not about the job: "how do i make a living as a
# nurse" is a career question, and "how much do i pay a plumber" is the price of hiring one, not
# what a plumber takes home. "you" is not in the second group on purpose - "how much do you earn
# as a teacher" is a pay question about the job.
_PAY_ASK_IS_THEIRS = re.compile(
    r"\b(?:how|what) (?:much )?(?:do|does|did|can|should|shall|could|would) (?:i|we)\b"
    r"|\b(?:do|should|would|will) (?:i|we) pay\b")


def _pay_job_named(line):
    """The job a line names for a pay question, longest name first."""
    best = None
    for alias, name in PAY_ALIASES:
        at = line.find(" " + alias + " ")
        if at >= 0 and (best is None or len(alias) > best[0]):
            best = (len(alias), name)
    if best:
        return best[1]
    name, _where = _job_named(line)
    return name


def _job_pay(memory, understood):
    line = " " + ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower() + " "
    if _PAY_ASK_IS_THEIRS.search(line):
        return None
    return PAY_TABLE.get(_pay_job_named(line))


ENTRIES.append(entry(
    "what-a-job-pays",
    (tuple(sorted(PAY_JOB_WORDS)), PAY_WORDS),
    _job_pay,
    # what the job costs a customer, what the day is like, how to get into it and how many hours
    # or days off it comes with are all other answers: "how much does a plumber charge", "what
    # does a nurse do", "how do i become a nurse", "how many hours does a nurse work",
    # "how much holiday does a teacher get".
    avoid=("charge", "charges", "charging", "cost", "costs", "price", "prices", "quote",
           "quotes", "hire", "hiring", "become", "becoming", "qualify", "qualification",
           "qualifications", "course", "courses", "apprentice", "apprenticeship", "training",
           "work experience", "cv", "cover letter", "interview", "vacancy", "advert",
           "hours", "shift", "shifts", "rota", "holiday", "holidays", "annual leave", "day off",
           "days off", "pension", "sick pay", "maternity", "parental", "notice", "retire",
           "retirement", "redundancy", "strike", "union", "overtime pay", "tax return",
           "taxes",
           # a tip is the tipping answer, not the wage: "how much do waiters earn in tips"
           "tip", "tips", "tipping", "gratuity", "tronc",
           # work being done in somebody's house is priced, not paid: "how much does a plumber
           # want to fit a shower" is the quote question, whatever the verb
           "fit", "fits", "fitting", "install", "installs", "installing", "installer",
           "replace", "replacing", "want to", "come out", "call out", "call-out",
           "do the job", "for the job", "a day's work"),
    bias=3))
# --- a promotion that is not what it looked like -------------------------------------------
# "i got a promotion but i hate the job" was answered "Noted: you got a promotion but you hate
# the job" - the promotion rows all read an ask about getting one, and the "hate my job" answer
# needs the complaint to be the whole line. The mix of the two is its own question, and it is a
# common one: the step up turns out to be admin, hours and other people's problems.
ENTRIES.append(entry(
    "promoted-and-hate-it",
    (("promotion", "promoted", "promoting", "new role", "new job", "step up", "pay rise",
      "payrise", "new title", "bigger job", "management job", "team lead", "more money"),
     ("hate it", "hate the job", "hate my job", "hate this job", "hate the new job",
      "regret", "regretting", "wish i hadnt", "wish i hadn't", "not what i expected",
      "not what it looked like", "not worth it", "too much", "overwhelmed", "stressed",
      "stress", "miserable", "unhappy", "cant cope", "can't cope", "making me ill",
      "want my old job", "my old job", "step down", "go back down", "demoted",
      "never wanted it", "shouldnt have taken", "shouldn't have taken")),
    "Give it three months before you judge it, and use them: a new role is mostly the parts you "
    "did not see, so the first job is to name what actually changed - the admin, the hours, the "
    "people problems - because that is what can be fixed. Ask your manager for one specific change "
    "\"I want to keep two days of the client work\" and a review date, and put it in writing. If "
    "nothing moves by then, stepping back down is a normal move and not a failure, and asking for "
    "your old job back is far easier before you have been in the new one a year.",
    # getting the promotion, a pay question and a job that was always bad are other rows
    avoid=("how do i ask for", "should i ask for", "how to get", "apply for", "applying for",
           "interview", "salary", "what should i say", "negotiate", "pay rise", "two job offers",
           "another job", "resign", "quit", "notice", "redundancy", "sacked", "fired"),
    bias=1))

# --- the words in an HR policy -------------------------------------------------------------
# "What is a protected characteristic" was a search hedge, and it is the phrase the whole of
# discrimination law hangs on, so the answer lists them and says what makes them matter.
ENTRIES.append(entry(
    "protected-characteristic",
    (("protected characteristic", "protected characteristics", "equality act",
      "equality act 2010", "protected by law", "discrimination law", "nine protected"),
     ("what is", "whats", "what are", "which", "mean", "means", "list", "how many", "my rights",
      "rights", "discriminated", "discrimination", "sacked", "fired", "treated unfairly",
      "unfair", "complain", "tribunal", "claim")),
    "The protected characteristics are the nine things the Equality Act 2010 stops an employer "
    "treating you worse for: age, disability, gender reassignment, marriage and civil partnership, "
    "pregnancy and maternity, race, religion or belief, sex, and sexual orientation. Being "
    "treated badly because of one of them - in hiring, pay, promotion, hours or how you are "
    "managed - is unlawful, and the burden shifts once you can show it probably happened: the "
    "employer has to prove it did not. Keep the messages and dates, raise it in writing with "
    "whoever the policy names, and note that a tribunal claim usually has to be started within "
    "three months less one day of the act.",
    # a redundancy, a warning and a grievance are their own processes, and the minimum wage is
    # a different entitlement
    avoid=("redundancy", "redundant", "warning", "grievance", "minimum wage", "holiday pay",
           "sick pay", "notice period", "resign", "quit", "appraisal", "probation",
           "zero hours", "contract"),
    bias=1))
