"""Say back the thing they just told you, in their own words.

A person who says "my sister is called Meg" or "we're flying to Rome on Monday" is handing you
something. A friend answers with the thing itself - "Meg, got it" or "Rome on Monday, nice" -
not one stock line for every line ("Noted!") and not a question at the end every time either.
The store is what makes the echo possible; the person's own words are what make it fit.

bot/modules/memory_store.py asks this after its recall answers, and only for a line that is
telling the bot something. Every rule here is a guard against taking a turn that is not that:

* only a statement - never a question, a request, a greeting, a thanks or a "yes"
  (bot/understanding's kind, in memory["understood"]);
* only when the line gave the store a fact (bot/memory/facts.extract found one), or when it adds
  a detail to the thing we are already on ("i work from home" after a question about naps), so
  small talk the bot merely heard is never echoed back;
* never a greeting or a self-introduction, because the chat module answers "Nice to meet you,
  Tom" better than an echo can;
* never a line with a feeling, a loss or good news in it: those belong to the modules that
  answer them, and "your dad died in March - noted" would be awful. The caller passes only
  lines whose mood is neutral, and bot/compose/loss.py and bot/compose/badnews.py are asked
  here as well, so a kind reply always wins over an echo;
* never a body that hurts, a fit or a wound ("your dog choked on a bone - noted" says nothing
  about the dog), and never a birthday nobody reached ("your mum would have been 70 - noted");
* the echo is short: the first clause or two of what they said, cut at a word, so the reply
  matches the line instead of repeating it.

The frames vary through bot.compose.pick, so the bot does not say "noted" three times running.
"""
import re

from ..compose import loss, negated, pick, trouble
from ..compose.badnews import reads_as_bad_news, reads_for_a_pet, reads_like_a_symptom
from ..compose.goodnews import reads_as_good_news, reads_as_settled, worry_on_the_table
from ..understanding import understand as understanding
from ..understanding.kinds import SHIFT_EARLY, SHIFT_LATE, VERBISH
from ..understanding.topics import NUMBER_WORDS
from ..understanding.normalize import (LEFT_OFF_CONTRACTION, LEADERS,
                                       opens_without_subject,
                                       without_a_leading_exclamation)
from . import last_user, there_is_a_chat
from . import opening
from . import you as say_it_back
from . import facts, hours as hours_after, named, narrow, not_a_trip, taste, topics
from . import stuck as stuck_line
from .facts import DAYS, MONTHS, a_limit_on_the_plan
from .relations import _person_from_pronoun, _pronoun_fits
from .store_lines import CHILD, PERSON_GROUP

# The keys of facts.extract() that mean "the store learned something about them".
# "age" is in here for the same reason the budget is: "im 41" is a fact they handed over, and the
# stock "thanks for telling me" says nothing about it while "you're 41" does. Only what the reader
# actually keeps is listed: a height is not read out of "im 6 foot 2" yet, so it is not one.
# The facts a line can be said back for. A birthday and a weight are here because a person who
# has just given one has told you something they expect you to keep: "Got it. Is there anything
# you'd like a hand with?" says nothing about what they said, and the fact only shows up on the
# ask that follows, which reads as if the first line had not been heard.
FACTS = ("name", "age", "job", "city", "places", "allergies", "pets", "people", "budget", "diet",
         "plan", "done", "others", "relations", "condition", "tastes", "birthday", "weight",
         "height")

# {Thing} starts a sentence; {thing} sits inside one.
# After a reply about how they feel, what they add next is the reason for it: "i feel like a bad
# mum" then "i hardly see them". The plain frames said that back as a fact to file ("You hardly
# see them \u2014 noted."), which reads as if the feeling had been dropped and only the detail
# was heard. These tails answer the detail as the explanation it is and ask the one thing that
# follows from it. They are chosen only for the turn straight after a feeling (see
# _after_a_feeling), never for a detail on its own.
EXPLAIN_TAIL = (
    "{Thing}. That explains it \u2014 no wonder it sits on you. What would take some weight off?",
    "{Thing}. That is a lot to carry on top of how you feel. What would help most?",
    "{Thing} \u2014 so that is the part behind it. What has been hardest about it?",
)
# A thing they have, said in its own right: "i have a bike" was answered "I'm listening - say
# more if it helps", and taking the false job out of "we have two cars, a fiesta and a focus"
# took the echo of that line with it, because the echo had been riding on the job. This is a
# shape (a having word, then a thing behind it), not a list of nouns. The shapes that only sound
# like a possession are refused: "i have a feeling", "i have no idea", "i have a question",
# "i have to pick the kids up", and "i have a headache", which is a body that hurts.
# Bare past-tense "had" is not a possession and is not read here: "we had a massive row" said
# back as "Noted: you had a massive row" is the coldest reply in STYLE.md, and a row, a day or a
# night is a story rather than a thing they own. A comma after the noun ("we had two cars, a
# fiesta and a focus") still names the thing, that is read in facts.py, and "i have a bike" is
# untouched.
HAVE_THING = re.compile(
    r"\b(?:i|we)(?:['\u2019]?ve)?\s+(?:have(?:\s+got)?|got|own|keep|just got|"
    r"recently got|already got|just bought|bought)\b"
    r"(?:\s+(?:already|just|only|still|now|also))?\s+"
    r"(?:(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|another|some|no|few"
    r"|couple|my|our|his|her|their)\s+)?([a-z][a-z'-]{2,20})\b", re.I)
NOT_A_THING = frozenset("""
    feeling idea question clue hurt look go try rest break problem issue theory plan reason hope
    dream nightmare laugh cry shower think thought memory chance sense guess moment minute while
    day week month year option choice say part lot bit time life job appointment check
    read call text email message right headache pain ache cough cold temperature fever migraine
    bug flu to no not nothing none much more less enough already got
""".split())

# An aim they are working at is not a feeling to explain, though the engine files one as a negative
# feeling ("im trying to lose a bit of weight"). The line after it says what they do about the
# aim, and the reason-reading turned "i walk to work every day" into "You walk to work every day.
# That is a lot to carry on top of how you feel" - telling somebody who has just said something
# they are pleased with that it is a burden. A worry is the other way round: "im worried about my
# exam" then "i have barely revised" really is the reason, and that reading stays.
AN_AIM = re.compile(
    # The aim has to be the line's own main clause, so it is anchored at the start (after a short
    # lead-in). Searching anywhere in the line caught the aim inside a worry - "im worried im
    # going to fail my exam" went down the aim path and lost the reason-reading that a worry
    # keeps - and caught other people's aims ("my sister is trying to lose weight"). "going" is a
    # future marker and not an aim ("im going to tesco on saturday"), and "i want to" counts only
    # when what they want is a thing to work at rather than something they want said or wanted.
    r"^\s*(?:(?:ok|okay|so|well|right|and|but|yeah|hi|hey)[,\s]+)*"
    r"(?:(?:i'?m|i am|im|i|we'?re|we are|we)\s+(?:really |still |just |also |now )?"
    r"(?:trying|hoping|aiming|planning|working|wanting|looking)\b[^.!?]{0,40}?\b(?:to|on|at)\b"
    r"|\bi want to (?!talk|say|tell|ask|know|feel|die|disappear|give up)\b"
    r"|\bi(?:'?m| am|m) on a (?:diet|plan|course|programme)\b)",
    re.I)
# A line saying it is going badly is the other side of an aim: "im trying to lose weight" then "i
# feel like giving up" is a mood that needs the reason-reading, while "i joined a gym" is only
# progress. The engine reads the first as news (intent "news", polarity 0), so the words people
# use are read here. The ways people type it, with the shapes that are progress kept out: "i quit
# sugar" and "i lost half a stone" are not feelings.
A_FEELING_ABOUT_IT = re.compile(
    r"\b(?:"
    r"feel\s+(?:like\s+)?(?:giving|awful|terrible|rubbish|horrible|dreadful|hopeless|useless|"
    r"a\s+failure|like\s+a\s+failure|low|down|bad|shit|stupid|fat|ugly|impossible|sick)"
    r"|dont\s+feel\s+like|don'?t\s+feel\s+like|not\s+feeling\s+it"
    r"|feelings?|felt\s+(?:like|awful|terrible|low|down)|it\s+feels\s+impossible"
    r"|giv(?:e|ing|en)\s+up|gave\s+up|going\s+to\s+quit"
    r"|struggl\w*"
    r"|can'?t\s+(?:do\s+it|keep|cope|face|take\s+it|manage)|cannot\s+(?:do|keep|cope)"
    r"|hopeless|worthless|useless|pointless|miserable|ashamed|guilty|hate\s+my\s+body"
    r"|fail\w*"
    r"|fed\s+up|sick\s+of|had\s+enough|tired\s+of\s+it"
    r"|exhausted|knackered|worn\s+out|burnt?\s+out"
    r"|embarrass\w*|depress\w*|anxious|anxiety|stressed|tearful|crying"
    r"|no\s+motivation|losing\s+(?:heart|motivation)|disheartened|demoralis\w*|demoraliz\w*"
    r"|not\s+going\s+well|going\s+badly"
    r"|worried|scared|afraid"
    r")\b",
    re.I)

# Good news about somebody else is not the person's own news and not a fact to file either:
# "my son got a prize at school" came back as "Noted: your son got a prize at school", which is the
# filing cabinet STYLE.md rules out. The person is telling you something they are pleased about,
# so the line says the thing back and is pleased about it, from the same shape the pools for their
# own news use. Never a question: the person is not asking for anything.
SOMEONE_GOOD = re.compile(
    r"\b(?:prize|award|medal|trophy|cup|distinction|honours|top of the class|head boy|head girl"
    r"|scholarship|won|wins|winning|came first|passed|passing|graduated|graduates|degree"
    # A set of top grades is the same kind of news, and it was arriving as a fact to file: "my son
    # got 4 a stars" was answered "Noted: your son got 4 a stars". The count is how many, so the
    # grade name after it is what makes it news - and the star only counts as a grade where nothing
    # names it, because a star wars set is not one.
    r"|a[\s*'-]?stars?\b(?![\s-]*(?:wars|trek|gazer|gazing|sign|bucks|fish|city|chart))"
    r"|a\*s?|straight 9s|all 9s|all 8s|grade 9|grade 8|top grades"
    r"|got into|got engaged|engaged|married|expecting|gave birth|had a baby|new baby"
    r"|promoted|promotion|new job|retired|retiring|all clear|out of hospital"
    r"|new puppy|new kitten|new dog|new cat|new rabbit|new hamster|new foal)\b", re.I)
SOMEONE_TAIL = (
    "{Thing} \u2014 that's lovely news.",
    "{Thing}. That's a good bit of news to hear.",
    "{Thing} \u2014 you must be pleased for them.",
    "{Thing}. That's worth a bit of a fuss.",
)
# A round birthday of theirs is not a receipt either: "my mum is 70 next week" was answered
# "Noted: your mum is 70 next week". A round one is a thing people make something of.
# A round one, and an occasion it falls on: "my mum is 70 next week" is a thing people make
# something of, and "she is 11" - the age of the child the last turn was about - is a fact that
# keeps the plain ending. So the figure needs the day it falls on, or a birthday word, or a
# decade said in words: an age on its own is never enough.
# A visit announced is news about the person's week, not a fact to file: "my sister is coming to
# stay this weekend" was answered "Noted: your sister is coming to stay this weekend", the filing
# cabinet STYLE.md rules out. The person is telling you something they are looking forward to, so
# the line says it back and is pleased about it, the way another person's good news is. Both
# directions count - them coming to the person ("my parents are visiting next week") and the person
# going to them ("im visiting my mum on sunday") - because both are the same thing to talk about.
# A lift is not a visit ("my mum is coming to pick me up"), a question is not an announcement
# ("when is my sister coming"), and a thing arriving is read elsewhere ("the new sofa comes friday").
SOMEONE_COMING = re.compile(
    r"\b(?:my|our)\s+(?:mum|mom|mam|mother|dad|father|son|daughter|sister|brother|wife|husband"
    r"|partner|aunt|uncle|gran|granny|grandma|grandad|grandpa|nan|cousin|niece|nephew|mate|mates"
    r"|friends?|in[- ]?laws?|parents|family|folks|brother|sister-in-law|brother-in-law)\b"
    r"[^.;!?]{0,18}?\b(?:is|are|was|were)\s+(?:already\s+|just\s+|now\s+|still\s+|all\s+)?"
    # "due" on its own is how people announce a baby - "my partner is due any day" - and the
    # visit pool told a person expecting a child "that's a proper bit of the week". The word
    # only counts the arrival when the arrival is the thing said after it.
    r"(?:coming|visiting|staying|stopping|arriving|due\s+to\s+(?:arrive|come|visit|stay))\b"
    r"|\b(?:i'?m|im|i am|we'?re|we are)\s+(?:off\s+|going\s+)?(?:up|down|over|back)?\s*"
    r"(?:to\s+see|visiting|staying\s+with|stopping\s+with)\s+(?:my|our)\s+"
    r"(?:mum|mom|mam|mother|dad|father|son|daughter|sister|brother|wife|husband|partner|aunt"
    r"|uncle|gran|granny|grandma|grandad|grandpa|nan|cousin|niece|nephew|mate|friends?|parents"
    r"|family|folks)\b", re.I)
# The errand that is not a visit: a lift, a repair, a hand with something. The person coming is
# doing a job on the way past, and "my mum is coming to pick me up" is not a visit to be pleased
# about. Likewise the reflexive "coming over for dinner" is already the cooking lane's.
NOT_A_VISIT = re.compile(
    r"\b(?:pick(?:ing)?\s+(?:me|us)\s+up|drop(?:ping)?\s+(?:me|us)\s+off|collect(?:ing)?\s+"
    r"(?:me|us)|to\s+(?:have\s+a\s+look|check|fix|repair|help|clean|deliver|install|service)\b)",
    re.I)
VISIT_TAIL = (
    "{Thing} \u2014 that's something to look forward to.",
    "{Thing}. Nice \u2014 a proper visit.",
    "{Thing} \u2014 enjoy it.",
    "{Thing}. Good \u2014 that's a proper bit of the week.",
)

SOMEONE_MILESTONE = re.compile(
    r"\b(?:birthday|anniversary)\b[^.;!?]{0,24}?\b(?:next|this|on|is)\s+"
    r"(?:week|month|weekend|today|tomorrow|saturday|sunday|monday|tuesday|wednesday|thursday|friday)\b"
    r"|\bturns?\s+\d{1,3}\b"
    r"|\b(?:forty|fifty|sixty|seventy|eighty|ninety)\b"
    r"|\b\d{2,3}(?:th|st|nd|rd)?\b[^.;!?]{0,24}?\b(?:next|this|on|in)\s+(?:week|month|weekend|"
    r"saturday|sunday|monday|tuesday|wednesday|thursday|friday)\b"
    r"|\b(?:next|this)\s+(?:week|month|weekend)\b[^.;!?]{0,20}?\b\d{2,3}\b",
    re.I)
SOMEONE_MILESTONE_TAIL = (
    "{Thing} \u2014 that's a big one.",
    "{Thing}. Are you doing anything for it?",
    "{Thing} \u2014 a round one deserves a fuss.",
    "{Thing}. That's coming round fast.",
)

# A follow-up that names a second person and nothing about them: "my mums birthday is in may" /
# "and my dads". The line is the same fact for somebody new, with the fact itself left out, and
# the receipt said it back as a bare noun - "Got it - your dads." - which tells the person nothing
# and is not even their words. What is missing is the date, so the store asks for it: the one part
# of the fact the line did not give.
A_SECOND_PERSON = re.compile(
    r"^\s*(?:and|also|plus|or|what\s+about|how\s+about)\b[\s,]*"
    r"(?:my|our|your)\s+(?P<who>[a-z][a-z '-]{1,24}?)\s*(?:'s|s)?\s*[.!?]*\s*$", re.I)
A_BIRTHDAY_TOLD = re.compile(r"\b(?:birthday|bday|dob|date of birth)\b", re.I)
# The verb a plan was said with, so the ask can borrow it: "my mum is coming on friday" asks
# "when is he coming", never "when is he".
A_PLAN_VERB = re.compile(r"\b(?:is|are|was|were)\s+(?P<verb>[a-z]+ing)\b", re.I)
A_DATE_TOLD = re.compile(
    r"\b(?:" + "|".join(MONTHS) + r"|" + "|".join(DAYS) + r"|"
    r"\d{1,2}(?:st|nd|rd|th)\b|next\s+(?:week|month|weekend)|this\s+(?:week|month|weekend))",
    re.I)


def _a_relation(word):
    """The relation a bare possessive names ("dads" -> "dad"), or "" when it names none."""
    said = " ".join(str(word or "").lower().split()).strip(" .,;:!?'")
    for candidate in (said, said[:-1] if said.endswith("s") else "", said.replace(" ", "")):
        if candidate in facts.RELATIONS:
            return candidate
    return ""


def _the_pronoun(relation):
    """"he" or "she" for a relation that says it, and "" for one that does not."""
    if relation in facts.HE:
        return "he"
    if relation in facts.SHE:
        return "she"
    return ""


def _the_ages_held(memory):
    """{relation: age} for the people the chat has already been given an age for."""
    from . import others as the_others
    held = {}
    for entry in (the_others(memory) or []):
        if isinstance(entry, dict) and entry.get("age") is not None:
            held[str(entry.get("who") or "").lower()] = entry.get("age")
    return held


def _people_in_chat(memory):
    """"the youngest" and "the other one" are people only in a chat that has people in it."""
    if not isinstance(memory, dict):
        return False
    user = memory.get("user") or {}
    if isinstance(user, dict) and (user.get("people") or user.get("kids")):
        return True
    from . import others as the_others
    if the_others(memory):
        return True
    for turn in (memory.get("turns") or [])[-4:]:
        said = str((turn or {}).get("user") or "").lower() if isinstance(turn, dict) else ""
        if any(re.search(r"\bmy\s+" + re.escape(one) + r"\b", said) for one in facts.RELATIONS):
            return True
    return False


def a_person_named_alone(text, memory):
    """The question a person named on its own asks for, or "".

    "and my son", "the twins", "same for my daughter": the line is a person and no fact, so there
    is nothing to say back and one thing to ask. The store may already hold the age, and then the
    age is not the question - what they are into is.
    """
    if not isinstance(text, str):
        return ""
    # The little words a person puts in front of the person - "and my son", "and what about my
    # sister", "same for my daughter" - are read off by the same frames every other ask about a
    # person uses (`named.the_one_asked_about`), so a line is a person named on its own however it
    # is said. Read here, "and what about my sister" kept its "what about" and matched nothing at
    # all: the turn had no reply in the whole bot and the person got "Hello!".
    only = named.the_one_asked_about(text) or " ".join(text.split())
    match = A_PERSON_ALONE.match(" ".join(only.split()))
    if not match:
        return ""
    said = " ".join(match.group("what").lower().split()).strip(" .,;:!?'")
    said = WHICH_ONE.sub("", said)
    # The line says "my son" or "the twins" and the reply says it back their way: "your son" and
    # "the twins", never "the son" for a person who said "my son".
    ours = match.group("det").lower() in ("my", "our")
    word = said[:-1] if said.endswith("s") and said[:-1] in facts.RELATIONS else said
    several = said.endswith("s") and said[:-1] in facts.RELATIONS
    # A person named by the place they hold rather than by a relation word: "the youngest", "the
    # second one", "and a baby", "my other half". The line is one of their family and no fact, so
    # the same question is what is left to ask - and "the other one" is only a person when the chat
    # is already about people, because two sofas have an other one too.
    place = A_POSITION.get(" ".join(match.group("what").lower().split()))
    if place:
        # "the youngest" is a person in any chat, and "the other one" is a person only in a chat
        # that already has people in it: two sofas have an other one as well.
        if place in A_POSITION_MAYBE_A_THING and not _people_in_chat(memory):
            return ""
        pool = A_POSITION_LINES.get(place) or A_PERSON_ALONE_LINES
        who = ("Your " if ours else "The ") + place
        return (pick(pool, memory, said).replace("{Who}", who)
                    .replace("{they}", "they").replace("{them}", "them").replace("{do}", "do"))
    group = A_GROUP_ALONE.get(said) or (said[:-1] + "s" if several else "")
    if group:
        who = ("Your " if ours else "The ") + group
        return pick(A_GROUP_ALONE_LINES, memory, said).format(Who=who)
    relation = _a_relation(word)
    if not relation:
        return ""
    return _the_question_about(relation, said, ours, memory)


def _the_question_about(relation, said, ours, memory, name=""):
    """The question a friend asks about this person, said back their way.

    "your son" for a person who said "my son", and the name when the chat has one: "Jack - what
    does he get up to?" rather than "your son" for somebody whose name was already given.
    """
    pronoun = _the_pronoun(relation)
    they, them = (pronoun, "him" if pronoun == "he" else "her") if pronoun else ("they", "them")
    who = name or (("Your " if ours else "The ") + relation)
    known = relation in _the_ages_held(memory)  # an age they gave is not the question
    pool = A_KNOWN_AGE_LINES if known else A_PERSON_ALONE_LINES
    line = pick(pool, memory, said)
    return (line.replace("{Who}", who).replace("{they}", they).replace("{them}", them)
                .replace("{do}", "does" if they in ("he", "she") else "do"))


# A person pointed at rather than named: "what about him", "and her", "what about the two of
# them". The chat already said who the last person was, so the line is a person and nothing else
# and the same question about them is owed - said here, "what about him" after "my son jack is 6"
# got the search hedge, which is a shrug about a person whose name the bot was just given.
A_POINTED_AT = re.compile(r"^(?:him|her|them|they|that one|this one|those two|the two of them|"
                          r"both of them|the pair of them)$")


def a_person_pointed_at(text, memory):
    """The question about the person a "him" or "her" or "them" points at, or ""."""
    if not isinstance(text, str):
        return ""
    only = named.the_one_asked_about(text)
    if not only or not A_POINTED_AT.match(" ".join(only.lower().split())):
        return ""
    word = only.lower().strip()
    # "the two of them" and "both of them" are two people, and the chat has to hold two before the
    # phrase means anybody: a chat with one son and "what about the two of them" is a question the
    # bot cannot answer, and answering about the one son is not what was asked.
    if word not in ("him", "her", "them", "they", "that one", "this one") \
            and _how_many_people(memory) < 2:
        return ""
    if word not in ("him", "her", "them", "they", "that one", "this one"):
        all_named = _the_people_pointed_at(memory)
        if len(all_named) >= 2:
            who = " and ".join(all_named[:2])
            # The ages the chat already has are not the question - "Jack and Emma - how old are
            # they?" asked two children whose ages were the two lines before it.
            pool = A_TWO_ALONE_LINES if all(_an_age_held(memory, one) for one in all_named[:2]) \
                else A_GROUP_ALONE_LINES
            return pick(pool, memory, who).format(Who=who)
    person = _the_person_pointed_at(word, memory)
    if not person:
        return ""
    relation, name = person
    return _the_question_about(relation, relation, True, memory, name)


def _how_many_people(memory):
    """How many people of theirs the chat holds."""
    from . import others as the_others
    return sum(1 for entry in (the_others(memory) or [])
               if isinstance(entry, dict) and str(entry.get("who") or "").lower() in facts.RELATIONS)


def _the_people_pointed_at(memory):
    """The names of the people the chat holds, in the order they were given, named only."""
    from . import others as the_others
    names = []
    for entry in the_others(memory) or []:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("who") or "").lower() not in facts.RELATIONS:
            continue
        name = str(entry.get("name") or "").strip()
        if not name or not name[:1].isalpha():
            continue
        name = name[0].upper() + name[1:]
        if name not in names:
            names.append(name)
    return names


def _an_age_held(memory, name):
    """Whether the chat already has an age for the person of this name."""
    from . import others as the_others
    for entry in the_others(memory) or []:
        if not isinstance(entry, dict):
            continue
        held = str(entry.get("name") or "").strip().lower()
        if held == name.strip().lower() and entry.get("age"):
            return True
    return False


def _the_person_pointed_at(word, memory):
    """(relation, name) for the person the word points at, or None when the chat has nobody."""
    from . import others as the_others
    wanted = {"him": facts.HE, "her": facts.SHE}.get(word)
    people = [entry for entry in (the_others(memory) or []) if isinstance(entry, dict)]
    for entry in reversed(people):
        relation = str(entry.get("who") or "").strip().lower()
        if relation not in facts.RELATIONS:
            continue
        if wanted is not None and relation not in wanted:
            continue
        name = str(entry.get("name") or "").strip()
        if name and name[:1].isalpha():
            name = name[0].upper() + name[1:]
        return relation, name
    return None


def a_second_person(text, memory):
    """The ask for the date of the fact this line leaves out, or "".

    "my mums birthday is in may" / "and my dads" is one fact about two people, and the second
    half says only who. The fact before it is the one being carried over, so the reply keeps it
    and asks for the part the line did not give - the date - instead of saying the noun back.
    Only a line that names a person and nothing else comes here, and only when the turn before it
    was a dated fact about a different person, so a line that changes the subject is left alone.
    """
    if not isinstance(text, str):
        return ""
    match = A_SECOND_PERSON.match(" ".join(text.split()))
    if not match:
        return ""
    who = _a_relation(match.group("who"))
    if not who:
        return ""
    before = " ".join(str(last_user(memory) or "").lower().split())
    if not before:
        return ""
    # The turn before has to be about a person, and about somebody else: "and my mum" after a
    # line about their mum is not a new person to ask about.
    first = next((one for one in facts.RELATIONS if re.search(r"\bmy\s+" + re.escape(one) + r"", before)), "")
    if not first or first == who:
        return ""
    if not (A_BIRTHDAY_TOLD.search(before) or A_DATE_TOLD.search(before)):
        return ""
    said = "your " + who
    if A_BIRTHDAY_TOLD.search(before):
        return "And " + said + "'s birthday \u2014 when is that?"
    verb = A_PLAN_VERB.search(before)
    pronoun = _the_pronoun(who)
    if verb and pronoun:
        return "And " + said + " \u2014 when's " + pronoun + " " + verb.group("verb").lower() + "?"
    return "And " + said + " \u2014 when is that?"


# A line that names a person and nothing else is half a thought: "and my son", "the twins",
# "same for my daughter". With a dated fact before it, `a_second_person` asks for the date that
# was left out. With nothing before it - the first line of a chat - there is no fact to carry
# over at all, and the echo said the noun back: "and my son" was answered "Noted: your son.",
# which is a receipt for something nobody said. The line itself is a person, so the reply asks
# the one thing a friend asks about a person they have just been told about.
A_PERSON_ALONE = re.compile(
    r"^\s*(?:(?:and|also|plus|or|what\s+about|how\s+about|same\s+for|and\s+same\s+for|"
    r"same\s+as|and\s+so\s+does|and\s+so\s+is)\b[\s,]*)?"
    r"(?P<det>my|our|the|a|an)\s+(?P<what>[a-z][a-z '-]{1,24}?)\s*[.!]*\s*$", re.I)
# The words that say which one of several, in front of the person: "my other son" is a son.
WHICH_ONE = re.compile(r"^(?:other|second|third|first|eldest|oldest|youngest|little|big|"
                       r"older|younger|new|baby|step|half|adopted|foster)\s+")
# The several-people words, and the question for them is about all of them at once.
A_GROUP_ALONE = {"kids": "children", "children": "children", "childs": "children",
                 "twins": "twins", "boys": "boys", "girls": "girls", "sons": "sons",
                 "daughters": "daughters", "parents": "parents", "brothers": "brothers",
                 "sisters": "sisters", "grandkids": "grandchildren",
                 "grandchildren": "grandchildren", "grandparents": "grandparents"}
# The place a person holds in the family, said instead of a relation: "the youngest", "my other
# half", "and a baby". A line that names one of these and nothing else is a person and no fact,
# and the question about them is what the reply owes.
A_POSITION = {
    "youngest": "youngest", "youngest one": "youngest", "eldest": "eldest",
    "eldest one": "eldest", "oldest": "oldest", "oldest one": "oldest",
    "middle one": "middle one", "middle": "middle one", "second one": "second one",
    "third one": "third one", "little one": "little one", "littlest": "little one",
    "small one": "little one", "other one": "other one", "baby": "baby",
    "new baby": "baby", "little baby": "baby", "other half": "other half", "half": "other half",
    "partner": "other half",
}
# The places that could also be a thing: "the other one", "the second one", "the middle one" are
# a person only once the chat is about people.
A_POSITION_MAYBE_A_THING = frozenset(("other one", "second one", "third one", "middle one"))
A_POSITION_LINES = {
    "baby": ("{Who} \u2014 how many months?",
             "{Who} \u2014 boy or girl, and how old?",
             "{Who} \u2014 tell me about {them}."),
    "other half": ("{Who} \u2014 how long have you two been together?",
                   "{Who}. What {do} {they} do?",
                   "{Who} \u2014 tell me about {them}."),
}
A_PERSON_ALONE_LINES = (
    "{Who} \u2014 how old is {they}?",
    "{Who}. What {do} {they} get up to?",
    "{Who} \u2014 tell me a bit about {them}.",
)
A_KNOWN_AGE_LINES = (
    "{Who} \u2014 what is {they} into at the moment?",
    "{Who}. How is {they} getting on?",
)
# Two people the chat named, both with their ages given: the age is not the question.
A_TWO_ALONE_LINES = (
    "{Who} \u2014 what are they into at the moment?",
    "{Who}. How are they getting on?",
)
A_GROUP_ALONE_LINES = (
    "{Who} \u2014 how old are they?",
    "{Who}. How are they getting on?",
    "{Who} \u2014 tell me about them.",
)

FRAMES = (
    "{Thing} \u2014 noted.",
    "Got it \u2014 {thing}.",
    "{Thing}, good to know.",
    "Noted: {thing}.",
    "{Thing} \u2014 I'll remember that.",
    "{Thing}, right \u2014 I've got that.",
)

# A line that says they still have something to do is a limit on the plan, not a fact to file.
# "im drained", "i dont know what to do", "i still have the school run to sort": the bot has just
# said to pick the one thing that would make today lighter, and the line is the answer to that -
# except that it was said back, "You still have the school run to sort \u2014 noted.", which is the
# one reply a person who has just been handed a plan is not asking for. Naming the thing they have
# to do is new information about the plan, so it goes first and the rest of the plan waits.
STILL_TO_DO = re.compile(
    r"\b(?:still\s+(?:have|got)|have\s+got|i\s+ve\s+still\s+got)\s+"
    r"((?:the|my|our|a|an|his|her|their|this|that)\s+[a-z' ]{2,28}?)\s+to\s+"
    r"(?:sort|do|deal|get|finish|pay|arrange|handle|see|take|cover|make|run|write|clean|buy|"
    r"order|collect|ring|book|fix|wash|iron|pack|post|send|sign|check|tidy|move|email|print|"
    r"return|visit|walk|feed|look)\b",
    re.I)
# A clause wearing the shape of a thing: "the school run and the tea" is two things, and "that it
# happened" is not a job at all.
NOT_ONE_THING = re.compile(r"\b(?:and|but|so|because|that|if|when|which)\b", re.I)
# Every frame takes the person's own noun phrase, and a job can be one thing or several: "the
# washing" is one and "the bins" is not. "Then the bins is the one thing today, and the rest can
# wait." is what the first two frames said to a plural job, so a frame has to read right either way
# - none of these names the number of the thing.
THE_LIMIT_GOES_FIRST = (
    "Then {thing} first, and the rest can wait.",
    "Then do {thing} first and let the rest wait.",
    "Then take {thing} first \u2014 the rest can wait until it is done.",
    "Fair enough: {thing} first, and the rest of the list waits.",
)


# The words that say a plan was given even when the reply has no number and no colon:
# "You don't have to sort the whole week. Pick the one thing that would make today lighter."
_A_PLAN_WAS_GIVEN = re.compile(
    r"\b(?:one thing|only that|pick|first|start with|begin with|next step|smallest)\b", re.I)


def _the_last_reply_gave_a_plan(memory):
    """Whether the bot's last reply told the person something to do, or how to choose it."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    said = ""
    for turn in reversed(turns or []):
        if isinstance(turn, dict) and str(turn.get("bot") or "").strip():
            said = " ".join(str(turn["bot"]).lower().split())
            break
    if not said:
        return False
    if re.search(r"\d", said) or ":" in said:
        return True
    if _A_PLAN_WAS_GIVEN.search(said):
        return True
    return stuck_line._the_answer_gave_a_step(memory)


def _a_limit_on_the_plan(read, memory):
    """The line's own limit put in front of the plan the last reply gave, or None.

    Only after a step: "i still have the school run to sort" before the bot has said anything is a
    fact to take in, and the store files it. After a step it is the person narrowing the plan, and
    what a friend says is that the named thing goes first.
    """
    if not _the_last_reply_gave_a_plan(memory):
        return None
    found = STILL_TO_DO.search(read)
    if not found:
        return None
    thing = " ".join(found.group(1).split()).strip(" .,!?:;")
    words = thing.split()
    # "i still have to sort it" names nothing, and a whole clause after the verb is a story, not
    # the one thing going first.
    if not 1 <= len(words) <= 4 or NOT_ONE_THING.search(thing):
        return None
    pool = tuple(line.format(thing=thing) for line in THE_LIMIT_GOES_FIRST)
    return pick(pool, memory, read)


# A day on the line is the thing to answer, not something to file. "the vets at 4 tomorrow" was
# answered "Noted: the vets at 4 tomorrow", and "my sister's wedding is in june" "Noted: your
# sister's wedding is in june": the coldest reply in STYLE.md, on a line that has already told
# you what the next few days look like. A friend says something about the day. Reported by
# clear-weasel in #conversation (78962), from a 200-chat sample where 28 of the 34 replies that
# told the person nothing were receipts like these.
#
# Read as two kinds, because the reply differs: a day that is close ("tomorrow", "on friday",
# "the 14th") and one with room to plan ("in june", "next month"). A bare clock time is not
# one of them: "we eat at 6", "she goes to bed at 7" and "the tip shuts at four" are how the
# week works, not a day coming, and "you left school at 16" is a memory.
DAY_SOON = re.compile(
    r"\b(?:tonight|tomorrow|this (?:afternoon|evening)|"
    r"(?:on |next |this )?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"(?:next |this |at the |the )weekend|next week|"
    r"(?:on|by|before|until|till) the \d{1,2}(?:st|nd|rd|th)\b"
    r"|\b\d{1,2}(?:st|nd|rd|th) of (?:january|february|march|april|may|june|july|august"
    r"|september|october|november|december)"
    r"|\b(?:is|due|falls?|lands?) (?:on )?the \d{1,2}(?:st|nd|rd|th)\b)", re.I)
# A day word is not enough on its own either: "i saw my mum on sunday", "i took my pills this
# morning" and "it started on tuesday" all name a day, and all are already over. The line has
# to be about a day still to come, so a past telling of it stands down.
DAY_BEEN_AND_GONE = re.compile(
    r"\b(?:saw|met|went|was|were|had|took|tried|left|rang|called|kicked|started|finished|ended"
    r"|moved|got married|felt|ate|slept|woke|bought|sold|made|said|told|came|did|hurt|cried"
    r"|stopped|began|broke|forgot|lost|won|worked|texted|visited|arrived|landed|been"
    r"|this morning|yesterday|last (?:night|week|month|year|weekend|sunday|monday|tuesday"
    r"|wednesday|thursday|friday|saturday)|since (?:six|seven|three|four|five|eight|nine|ten"
    r"|eleven|twelve|two|one|half)|was in|used to|every (?:day|morning|night|week|weekend"
    r"|month|tuesday|monday|sunday|friday|saturday)|usually|always|normally|like the \d+)\b",
    re.I)
# A line with a day on it is a day coming only when the line says what is happening: "and the
# weather there in june", "same again next week i suppose" and "table 4 tomorrow" are a heading
# or a fragment, and "that is one to look forward to" says nothing about them. A figure is not a
# date either: "my rent is 900 in january" is the rent.
A_DOING = re.compile(
    r"\b(?:is|are|am|was|were|be|been|being|have|has|had|got|gets|get|go|goes|going|gone|come"
    r"|comes|coming|came|see|sees|seeing|visit|visits|visiting|fly|flies|flying|meet|meets"
    r"|meeting|start|starts|starting|work|works|working|need|needs|want|wants|wanted|due|take"
    r"|takes|taking|leave|leaves|leaving|arrive|arrives|arriving|stay|stays|staying|play|plays"
    r"|shut|shuts|open|opens|starts|turning|turns|have to|has to|going in|going back|back|off"
    r"|away|free|busy"
    r"|dentist|vets?|doctor|gp|hospital|scan|appointment|haircut|interview|meeting|flight"
    r"|train|bus|viewing|pickup|shift|party|match|wedding|birthday|exam|test|lesson"
    r"|class|club|football|rugby|school|concert|payday|pay day|rent|bill|deadline|review"
    r"|christening|funeral|service|checkup|check-up|surgery|midwife|health visitor)\b", re.I)
A_FIGURE = re.compile(r"\b\d{3,}\b")
# A want or a plan that is turned down is not a day coming. "i dont want pasta tonight" and
# "i dont want curry tomorrow" were answered "You don't want pasta tonight - coming round
# quickly, then": the day word made the line a date, and `want` is in A_DOING, so a refusal was
# filed as an appointment to look forward to. The negation is in front of the verb the day hangs
# on, which is what makes it a refusal rather than a thing happening.
A_DOING_TURNED_DOWN = re.compile(
    r"\b(?:dont|don'?t|do not|doesnt|doesn'?t|didnt|didn'?t|wont|won'?t|wouldnt|wouldn'?t|"
    r"cant|can'?t|cannot|not|never|no longer|no way)\s+(?:\w+\s+){0,2}?"
    r"(?:want|wants|wanted|need|needs|fancy|go|goes|going|have|has|having|do|doing|"
    r"come|comes|coming|came|stay|staying|work|working|eat|eating|drink|drinking|see|seeing|"
    r"happen|happening)\b")


# The same again for the thing being a state rather than an appointment: "he's much worse
# today" and "my son is pale today" are the news of a day that is happening, not one
# still to come, and "she is quite tall for 7" is a seven-year-old, not a time of day.
DAY_JUST_A_STATE = re.compile(
    r"\b(?:worse|better|pale|ill|sick|poorly|off (?:it|his|her|their) food|not himself"
    r"|not herself|up till|up until|much going on|busy|quiet|lovely|nice|awful|horrible)\b",
    re.I)
# When it is: "in june" is a month to plan into, "next june" is further off still.
DAY_FAR = re.compile(
    r"\b(?:in|of|next|this|by)\s+(?:january|february|march|april|may|june|july|august|september"
    r"|october|november|december)\b|\bin (?:the )?(?:spring|summer|autumn|winter)\b"
    r"|\bnext (?:month|year)\b|\blater (?:this|in the) (?:year|month)\b", re.I)
# A day on the line is not always a thing to say something about: a question about the day, and
# a line that asks anything at all, are answered by the module that can answer them.
A_DAY_ASKED = re.compile(r"\?|^(?:what|when|how|why|where|who|can|could|should|do|does|did|is|"
                         r"are|will|would|shall)\b", re.I)
# The endings presume nothing about what the day holds: the line can be an appointment, a payday
# or rent falling due, and "I hope it goes smoothly" or "give me a shout after" only fits the
# first. What is true of all of them is that the day is now in view.
# Not every day coming is one to look forward to. "the inquest is on friday", "the custody
# hearing is on friday" and "the reading of the will is on monday" take the day shapes above, and
# "not long now, then" reads as anticipation on a line like that - a cold receipt would be a poor
# reply but a cheerful one to an inquest is a worse one. Grief and a funeral are already answered
# by the loss modules, so this covers the ones nothing else takes.
NOT_A_DAY_TO_LOOK_FORWARD_TO = re.compile(
    r"\b(?:inquest|post[- ]mortem|autopsy|coroner|funeral|cremation|burial|bury|"
    r"reading of the will|probate|hearing|tribunal|court|custody|bailiffs?|eviction|"
    # Not "we wake up early tomorrow to fly": a morning is not a funeral.
    r"wake\b(?!\s*(?:up|at|early))|"
    r"creditors?|bankrupt(?:cy)?|insolven(?:cy|t)|debt (?:meeting|hearing)|"
    r"repossession|disciplinary|operation|surgery|biopsy|hospice|chemotherapy|radiotherapy|"
    r"diagnosis|results|care assessment)\b", re.I)
SOON_TAIL = (
    "{Thing}. Not long now, then.",
    "{Thing} \u2014 that is soon, then.",
    "{Thing}. Not far off now.",
    "{Thing} \u2014 coming round quickly, then.",
)
FAR_TAIL = (
    "{Thing} \u2014 plenty of time to sort the rest.",
    "{Thing}. That is one to look forward to.",
    "{Thing} \u2014 nice to have something in the diary.",
    "{Thing}. Plenty of time, anyway.",
)
# The endings for a day that is not good news: the day is in view, and what is true of it is that
# it is a heavy thing to have coming - never that it is nearly here.
SORRY_TAIL = (
    "{Thing}. That is a lot to have coming.",
    "{Thing} \u2014 I hope it goes as well as it can.",
    "{Thing}. That is a hard one to have ahead of you.",
    "{Thing} \u2014 no wonder it is on your mind.",
)


def _a_day_coming(clean):
    """Which pool a line about a day ahead wants, or None when it is not one.

    Only the day words matter here: the thing itself is the line, said back by the caller, so a
    pool that says one true thing about a date ahead fits any line with a date on it.
    """
    said = clean or ""
    if A_DAY_ASKED.search(said) or DAY_BEEN_AND_GONE.search(said):
        return None
    if DAY_JUST_A_STATE.search(said) or A_FIGURE.search(said):
        return None
    if A_DOING_TURNED_DOWN.search(said):
        return None
    if not A_DOING.search(said):
        return None
    if NOT_A_DAY_TO_LOOK_FORWARD_TO.search(said):
        return SORRY_TAIL
    if DAY_FAR.search(said):
        return FAR_TAIL
    if DAY_SOON.search(said):
        return SOON_TAIL
    return None


    coming = _a_day_coming(clean)
    if coming:
        # The last resort pool is the receipt, and a receipt is the wrong reply for a line with a
        # day on it: the day is what the person is thinking about.
        return coming

# The same frames, cut into their fixed front and back so a reply that is only the person's own
# line said back can be recognised as one. `bot/compose/fallback.py` asks this before it quotes
# the last reply as the bot's view: "My view has not changed: Got it - but your mum says it's too
# soon" is the bot standing behind a receipt, and there is no claim in one to stand behind.
_SAID_BACK = tuple(
    (frame.split("{", 1)[0].strip().lower(), frame.rsplit("}", 1)[-1].strip().lower())
    for frame in FRAMES
)


# The end of a sentence, for cutting a reply into the parts it is made of.
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
# A dash with space either side, which is how a frame's comma arrives in a finished reply.
_SPACED_DASH = re.compile(r"\s+(?:\u2014|\u2013|-)\s+")


def reads_as_a_receipt(text):
    """True when a reply is one of the frames above with the person's words in it.

    A receipt with the composer's own question after it counts too: "Two kids - good to know.
    How old are they?" is the same nod with a follow-up stuck on the back of it, and every
    caller here asks this question exactly to know whether there is anything to stand behind.
    Read whole, the question after the frame stopped the match, and "what would you do" after
    that turn was answered "Same as I said: two kids - good to know." - the bot repeating a nod
    as though it were a view.
    """
    said = " ".join(str(text or "").lower().split())
    if not said:
        return False
    # The frames are written with a comma and the composer joins with a dash: "two kids, good to
    # know" comes out as "Two kids \u2014 good to know.", which is the same nod with a different
    # mark between the parts. Both readings are tried, because a frame of its own may hold the
    # dash ("Got it \u2014 but your mum says it's too soon.") and must keep it.
    readings = (said, _SPACED_DASH.sub(", ", said))
    for reading in readings:
        if _one_frame(reading):
            return True
    for reading in readings:
        first = _SENTENCE.split(reading)[0]
        if first != reading and _one_frame(first):
            return True
    return False


def _one_frame(said):
    """True when the whole line is one frame with the person's words inside it."""
    for front, back in _SAID_BACK:
        if front and not said.startswith(front):
            continue
        if back and not said.endswith(back):
            continue
        middle = said[len(front):len(said) - len(back)].strip(" \u2014-.:,;")
        # "Got it - ." is not the person's words said back: the frame needs something inside it.
        if middle:
            return True
    return False
# Where the work is, rather than what the work is: "i work in a warehouse", "i work at tesco",
# "i work for the council". The store keeps the words that said where it is (job_frame: "in a",
# "at", "for the"), and those words are what make this a line about the person's week rather
# than a role they are naming - "im a nurse" is answered by bot/modules/chat.py with the job's
# own pool. Said back with the plain frames - "Noted: you work in a warehouse." - the one line
# that tells you most about somebody's day is a filing cabinet, and that was the reply to every
# one of these lines in the deck ("i work in a warehouse" alone seven times). A friend asks
# about the job, and each ending below works for a shop, a school and a call centre alike: the
# thing said back is the person's own words, and no ending names the trade.
WORK_FRAMES = (
    "{Thing} \u2014 what do you do there?",
    "{Thing}. How long have you been there?",
    "{Thing} \u2014 is it a good place to work?",
    "{Thing}. What's a normal day like?",
)
# The prepositions that say where the work is: "at tesco", "in a bakery", "for the council".
# "work as a nurse" says what they do and keeps its own reply, and a bare "work" is "i work
# nights", which the hours pools answer.
WORK_PLACE = frozenset(("at", "in", "for"))

# A line that tells the bot something the store cannot keep - "it came out really well", "i do
# legs on a tuesday", "work has been mad" - has nothing to file, so it used to fall through to
# bot/compose/fallback.py's three stock lines, which fit any message ("Got it. Is there anything
# you'd like a hand with?"). A friend says the thing back and adds one small thing that fits it,
# and the tail is chosen by the shape of what they said - a routine, something still going on,
# something that is over - never by the words of the topic, so the reply cannot be pasted onto
# another line.
HABIT_TAIL = (
    "{Thing} \u2014 that's a proper routine.",
    "{Thing}. That's a habit now.",
    "{Thing} \u2014 keep that up and it'll stick.",
)
GOING_TAIL = (
    "{Thing} \u2014 how's it going?",
    "{Thing}, how long have you been at it?",
    "{Thing} \u2014 how are you finding it?",
)
# A plan with a place and a date in it is not a project with a first step, it is a trip that is
# coming, and the person is telling you something they are looking forward to: "Noted: you're
# going to spain in july." is a filing cabinet. A friend says something about the trip itself,
# and which of the two sets is used is the shape of the plan - a place named, or an occasion -
# never a word of the topic, so no tail can be pasted onto a line that is not a plan.
TRIP_TAIL = (
    "{Thing} \u2014 have you been before?",
    "{Thing}. How long are you going for?",
    "{Thing} \u2014 that's something to look forward to.",
    "{Thing}. What do you want to do while you're there?",
)
OCCASION_TAIL = (
    "{Thing} \u2014 are you looking forward to it?",
    "{Thing}. That'll come round fast.",
    "{Thing} \u2014 that's something to look forward to.",
)
# A pet of theirs: the store keeps the animal and the name ("we have two cats, milly and tom"),
# and the echo said them back - "Noted: you have two cats, milly and tom" - which asks nothing
# about the thing they just told you about. A friend asks the only thing there is to ask about a
# pet: how long it has been there, or whether they get on. The count decides which pool, because
# "do they get on?" to one cat is a question about nothing.
PET_TAIL_ONE = (
    "{Thing} \u2014 how long has it been with you?",
    "{Thing}. What's it like to live with?",
    "{Thing} \u2014 is it good company?",
)
PET_TAIL_MANY = (
    "{Thing} \u2014 do they get on?",
    "{Thing}. Who's in charge?",
    "{Thing} \u2014 how long have they been with you?",
)
# An occasion the person has already said they are not looking forward to ("im going to a wedding
# in september and i hate weddings") cannot be answered with "that's something to look forward
# to": the reply would agree with the surface of the line and contradict the person in the same
# breath. The same is true of a hard day - a funeral, a hospital appointment, a court date - which
# is an occasion with nothing to look forward to. Both keep their words off the calendar and give
# the person something they can use instead.
OCCASION_FLAT_TAIL = (
    "{Thing}. That's a way off yet \u2014 and you can always leave early.",
    "{Thing} \u2014 the run-up is usually worse than the day itself.",
    "{Thing}. Not everything on the calendar has to be a highlight.",
)
# A plan on the calendar that is not a trip and not an occasion: the dentist on Tuesday, the
# hair appointment, the interview, somebody coming to stay. The store kept the day and handed the
# line back - "Noted: the dentist is on tuesday.", "Noted: your mum's coming on friday." - which
# is the coldest reply there is to what most people say about their week. A friend asks the one
# thing that is still open about it: what time it is, or how long the visitor is staying.
DIARY_WORDS = (
    "dentist", "dental", "doctor", "doctors", "gp", "optician", "opticians", "clinic",
    "hospital", "scan", "x-?ray", "check\\s?-?up", "appointment", "interview", "viewing",
    "survey", "mot", "service", "haircut", "hairdresser", "barber", "physio",
    "physiotherapy", "chiropractor", "osteopath", "hygienist", "podiatrist", "midwife",
    "health visitor", "counselling", "vet", "blood test", "bloods", "jabs?", "injection",
    "hearing", "tribunal", "parents evening", "parents' evening", "sports day", "nativity",
    "recital")
# Joined from a tuple, not broken over four lines: an alternation wrapped across lines carries a
# newline in front of every word after the first, so "my physio is on thursday" read as no
# appointment at all and was answered with a receipt.
DIARY_THING = re.compile(r"\b(?:" + "|".join(DIARY_WORDS) + r")\b", re.I)
# A time already said in the line is not asked about again: "im at the dentist at 3" wants what is
# left to say about it, and "what time are you in?" is the bot asking for what it was just told.
DIARY_TIME = re.compile(
    r"\b\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm|o'?clock)\b|\b(?:at|from|by)\s+\d{1,2}\b"
    r"|\b(?:morning|afternoon|evening|noon|midday|lunchtime|first thing)\b", re.I)
DIARY_TAIL = (
    "{Thing} \u2014 what time are you in?",
    "{Thing}. What time is it?",
    "{Thing} \u2014 is it first thing or later?",
)
DIARY_TIME_TAIL = (
    "{Thing} \u2014 is it far from you?",
    "{Thing}. Do you know where it is?",
    "{Thing} \u2014 somewhere you've been before?",
)
# Meeting somebody is not an appointment in a building: the time and the person are already said,
# and what is open is where it happens and who else is in it.
MEETING_TAIL = (
    "{Thing} \u2014 where are you meeting?",
    "{Thing}. Who else is going?",
    "{Thing} \u2014 what's the occasion?",
)
MEETING_TIME_TAIL = (
    "{Thing} \u2014 what time are you meeting?",
    "{Thing}. What time does it start?",
)
# Somebody coming to stay is a plan with a length nobody has said yet, and that is the question a
# friend asks: "my mums coming on friday" is answered about the visit, not filed.
COMING_TO_STAY = re.compile(
    r"\b(?:coming|comes|visiting|staying|arriving|flying over|driving down|over for)\b", re.I)
VISIT_TAIL_ONE = (
    "{Thing} \u2014 how long is {who} staying?",
    "{Thing}. Is {who} staying long?",
    "{Thing} \u2014 how long has {who} got with you?",
)
VISIT_TAIL_MANY = (
    "{Thing} \u2014 how long are they staying?",
    "{Thing}. Are they staying long?",
    "{Thing} \u2014 have they got long with you?",
)
# More than one of them coming. "my mum and dad are coming tomorrow" was answered "Is she staying
# long?", picking the first person out of the line and dropping the other, and "my brothers are
# coming this weekend" was answered "Is he staying long?" for the same reason: the question after
# the receipt names one visitor, and the line names two. The plural is either a kin word said in
# the plural - people write "my brothers", "my parents", "my in laws" and this file keeps only
# the singular - or two of them joined by "and".
PLURAL_KIN = frozenset("""
    parents brothers sisters grandparents grandkids grandchildren children kids twins folks
    family relatives friends mates lads boys girls in laws in-laws
    """.split())
# The word that says what the people named before it are doing: a visit is "my mum and dad are
# coming", and everything between "my" and this word is the list of who.
A_COMING_WORD = re.compile(
    r"\b(?:is|are|was|were|coming|comes|come|visiting|visits|visit|staying|stays|arriving|"
    r"arrives|flying|driving|stopping|stops)\b")


def _more_than_one_coming(said, start, word):
    """True when the line names more than one person coming, from where "my"/"our" starts.

    `word` is the first word after "my"/"our", which is the one the pronoun used to be read from.
    A plural there is enough on its own, and so is an "and" before the coming word: "my mum and
    dad are coming" and "my aunt and uncle are visiting" are two visitors, and the question after
    the receipt has to be the one for a pair.
    """
    if word in PLURAL_KIN:
        return True
    # "brothers", "sons", "cousins": a kin word the file only keeps in the singular, said in the
    # plural. "parents" and "twins" are already plural and are in PLURAL_KIN above. The plural
    # verb is what makes the trailing "s" a plural rather than an apostrophe people leave out:
    # "my brothers are coming" is two visitors and "my mums coming on friday" is one, the same as
    # "my mum's coming on friday".
    if word.endswith("s") and word[:-1] in facts.RELATIONS and word not in facts.RELATIONS:
        return bool(re.search(r"\b(?:are|were|were both|are both)\b", said))
    rest = said[start:]
    cut = A_COMING_WORD.search(rest)
    if cut:
        rest = rest[:cut.start()]
    # "and i"/"and we" is the speaker going with them, which is a third thing again and not a
    # pair of visitors, so it is left to the ordinary reading rather than called a pair.
    if re.search(r"\band (?:i|me|we|us)\b", rest):
        return False
    return bool(re.search(r"\band\b|&", rest))
# The occasions people say they are going to, as nouns that are only ever an occasion.
OCCASIONS = frozenset((
    "wedding", "weddings", "party", "parties", "birthday", "birthdays", "anniversary",
    "hen", "stag", "festival", "festivals", "concert", "gig", "gigs", "reunion",
    "graduation", "christening", "baptism", "barbecue", "bbq", "housewarming", "prom",
    "shower"))
# A shower is only an occasion with the word before it: "i had a shower this morning" is a
# wash, "im going to a baby shower next week" is a party.
SHOWER = frozenset(("baby", "bridal", "wedding", "naming"))
# The places people name with a "the", so the article alone is not what makes the word a thing
# rather than a place: "im going to the tip on saturday" is an errand, "we're off to the
# cotswolds next week" is a trip.
PLACES_WITH_THE = frozenset((
    "algarve", "cotswolds", "lakes", "highlands", "alps", "pyrenees", "cairngorms",
    "wight", "isle", "new forest", "peak district", "lake district", "states", "dales",
    "broads", "fens"))
# Words that turn the word after them into a thing rather than a place: an errand is "to the
# tip", a visit is "to my mum's", and neither is somewhere you have "been before".
THING_BEFORE = frozenset(("a", "an", "the", "my", "your", "his", "her", "our", "their"))
# A plan that has already happened is not a plan: "we went to spain in july" is a report and
# falls through to the ordinary reply.
PAST_PLAN = frozenset("went was were been came returned back".split())
# A trip is said with one of these verbs, a date it is coming on, and somewhere it goes. The
# three together are what make it a trip rather than an errand: "i'm going to the gym tomorrow"
# and "i'm going to see my mum this weekend" have the verb and the date, and the place is what
# tells them apart.
TRIP_VERB = re.compile(
    r"\b(?:going|gonna|off|flying|fly|flies|flew|driving|heading|travelling|traveling|sailing|"
    r"holiday|land|lands|landed|landing|arriv\w+|touch(?:es)? down|getting in|got in|get in)\b",
    re.I)
DESTINATION = re.compile(r"\b(?:to|off to|into)\s+(?:the\s+|a\s+|an\s+)?([a-z][a-z'\u2019-]*)",
                         re.I)
# Half the country says the trip by its arrival rather than its departure: "we land in lisbon on
# friday", "i arrive in rome on tuesday", "we fly into palma". Those lines have the verb and the
# date and name a place, and "to" alone threw them out - they were filed as news ("Noted: you
# land in lisbon on friday.") instead of answered about Lisbon. Only an arrival verb may take
# these prepositions: "in" after any other verb is not a destination ("im going in for a scan").
ARRIVE_VERB = re.compile(
    r"\b(?:land|lands|landed|landing|arriv\w+|touch(?:es)? down|fly|flies|flew|getting in|"
    r"got in|get in)\b", re.I)
DESTINATION_ARRIVAL = re.compile(
    r"\b(?:in|at|into)\s+(?:the\s+|a\s+|an\s+)?([a-z][a-z'\u2019-]*)", re.I)
NOT_A_TRIP = frozenset("""
    bed sleep work school college uni university gym doctor doctors dentist hospital shops shop
    town meeting interview court loo toilet hairdresser optician vet nursery see visit watch pick
    collect drop get take it that this them there here him her us me you

    appointment appointments scan scans checkup check-up clinic physio physiotherapy chiropractor
    midwife blood test tests xray x-ray hearing hearings trial trials court courts tribunal prison prisons
    jail jails cell custody remand probation solicitor lawyer

    funeral funerals burial cremation wake wakes

    be being been
    tesco asda sainsbury sainsburys morrisons lidl aldi coop co-op iceland waitrose supermarket
    office bank post
    """.split())
DATE_AHEAD = re.compile(
    r"\b(?:next|this|tomorrow|tonight|weekend|"
    r"in (?:january|february|march|april|may|june|july|august|september|october|november|"
    r"december|spring|summer|autumn|winter)|"
    r"on (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"for (?:a|an|one|two|three|four|five|six|seven|eight|\d+) (?:(?:more|whole|extra) )?"
    r"(?:day|night|week|fortnight|month)s?)\b", re.I)
# The line says, in its own words, that the day is not one to look forward to: "i hate weddings",
# "im dreading it", "i cant face it", "not looking forward to it", "i dont want to go". "have
# to" and "got to" are already read as an obligation before this is reached.
DREADED_OCCASION = re.compile(
    r"\b(?:hate|hates|hated|dread|dreads|dreading|dreaded|can'?t face|cant face|"
    r"not looking forward|dont want to go|don'?t want to go|dont fancy|don'?t fancy|"
    r"cant be bothered|can'?t be bothered|a drag|boring|obligated)\b", re.I)

# A trip whose length the person has already said does not want to be asked how long it is:
# "you're going to portugal for a week in may. How long are you going for?" is the bot asking
# what it was just told.
HOW_LONG_ALREADY = re.compile(
    r"\bfor (?:a|an|one|two|three|four|five|six|seven|eight|\d+)\s*"
    r"(?:day|night|week|fortnight|month|weekend)s?\b|\bfor the weekend\b|\bfor a few days\b",
    re.I)


def reads_as_a_trip(clean):
    """"trip", "occasion" or None: a plan that is coming, told to a friend.

    A friend answers "we're going to spain in july" with something about Spain, and an occasion
    with something about the day, not with a coach's "what's the first step you're unsure
    about?". The composer asks this so a trip is not read as a project with a first step, and
    the echo asks it so it can answer the trip rather than file it. Only another person's trip
    is left alone: "my sister is going to spain in july" is not the speaker's to be asked
    about.
    """
    if not isinstance(clean, str) or not clean.strip():
        return None
    flat = " ".join(clean.lower().split())
    if not DATE_AHEAD.search(flat) or OBLIGED.search(flat):
        return None
    if set(re.findall(r"[a-z']+", flat)) & PAST_PLAN:
        return None
    if flat.startswith(("my ", "her ", "his ", "their ", "she ", "he ")):
        return None
    if not TRIP_VERB.search(flat):
        return None
    destination = DESTINATION.search(flat)
    if not destination and ARRIVE_VERB.search(flat):
        destination = DESTINATION_ARRIVAL.search(flat)
    if not destination or destination.group(1) in NOT_A_TRIP:
        return None
    # The word after "to" is not always the place: "im going to my uncles funeral next week"
    # names the funeral two words later, and "we're going to spain for work in may" says work.
    # The four words after "to" are where an appointment, a relative or a job is named, so any
    # of them being one of those ends the reading - a trip lost is a stock reply, a scan read as
    # a holiday is a wrong answer.
    after_to = re.findall(r"[a-z'’]+", flat[destination.start():])[1:5]
    if not_a_trip.not_a_destination(after_to, after_to[0] if after_to else ""):
        # The word after "to" is a doing, not a place: "im going to wait till next year" was read
        # as a trip to Wait and answered "What do you want to do while you're there?". The trip
        # reader and this echo read the same list in `not_a_trip`, so the two cannot drift.
        return None
    if set(after_to) & NOT_A_TRIP:
        return None
    if set(after_to) & OCCASIONS:
        if "shower" in after_to and not set(after_to) & SHOWER:
            return None
        # An occasion they have already said they are dreading is not one to be told they are
        # looking forward to: the words of the line are the guard, not the occasion itself.
        return "occasion_flat" if DREADED_OCCASION.search(flat) else "occasion"
    # A word that is not a place: "to the tip", "to my mum's", "to a friend's". A trip is off to
    # somewhere it can be flown to, driven to or looked forward to, and a thing with an article
    # or a possessive in front of it is neither - except for the places that keep their "the".
    head = after_to[0] if after_to else ""
    if head in THING_BEFORE or head.endswith(("'s", "’s", "s'")):
        named = after_to[1] if len(after_to) > 1 else ""
        two_word = " ".join(after_to[1:3])
        if not (head == "the" and (named in PLACES_WITH_THE or two_word in PLACES_WITH_THE)):
            return None
    if not head:
        return None
    return "trip"

# Something they do on a set day, or keep doing: "on a tuesday" is a habit, "on tuesday" is one
# particular Tuesday, and only the article tells them apart.
HABIT = re.compile(
    r"\b(?:every (?:day|week|month|morning|evening|afternoon|weekend|other day)|"
    r"every (?:mon|tues|wednes|thurs|fri|satur|sun)day|"
    r"each (?:day|week|morning)|most days|most weeks|twice a (?:day|week|month)|"
    r"once a (?:day|week|month)|on (?:a|an) (?:monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday))\b", re.I)
# Still going on, or just started, against something that is over: "i've started swimming again"
# and "i'm trying to save money" want to know how it goes, "it came out really well" does not.
GOING = re.compile(r"\b(?:i(?:'ve| have) (?:been |just )?started|i(?:'ve| have) (?:taken up|got into|signed up)|i(?:'m| am) (?:trying|getting|"
                   r"working|building|writing|learning|practising|practicing)|i(?:'ve| have) been|"
                   r"started (?:again|back)|back (?:into|at) it)\b", re.I)
# A habit someone has been landed with is not a routine to admire: "i have to top the boiler up
# every week" said back as "that's a proper routine" is the bot mistaking a chore for a hobby.
# The obligation is the line, and it keeps the stock reply.
OBLIGED = re.compile(r"\b(?:have to|has to|had to|must|got to|gotta|need to|needs to|keeps|"
                     r"kept|constantly|always|every time|end up|ends up)\b", re.I)
# Something that keeps happening to them is not a routine: "i cry every morning", "i get panic
# attacks every week", "i shout at my kids every morning" said back as "that's a habit now" is the
# coldest line the bot can say, and worse than the stock line it replaces. A feeling, a symptom or
# an outburst at someone is the line, whatever shape it has.
FEELING = re.compile(
    r"\b(?:cry|cries|cried|crying|tears|sob\w*|weep\w*|panic\w*|anxious|anxiety|depress\w*|"
    r"numb|shak\w*|nightmares?|insomnia|miserable|upset|self[- ]harm\w*|hurt(?:ing)? myself|"
    r"feel(?:s|ing)? (?:low|down|awful|rubbish|empty|worthless)|"
    r"shout\w* at|yell\w* at|scream\w* at|swear\w* at|hit(?:s|ting)? (?:my|the|him|her|them)|"
    # A body that keeps being sick is not a routine either: "i throw up every morning" was said
    # back as "that's a habit now", which is the coldest line the bot has.
    r"sick|sickness|vomit\w*|throwing up|threw up|throw up|nausea|nauseous|diarr\w*|"
    r"migraine\w*|angry|furious|rage|lash(?:ing)? out)\b", re.I)
# A tail that asks how it is going is wrong for a line that says it is going badly, and the
# complaint is answered by the modules that read it as one.
GOING_BAD = re.compile(r"\b(?:badly|not|never|can'?t|cant|won'?t|wont|too much|too many|"
                       r"stop|stopped|give up|gave up|fail\w*|struggl\w*|hard|tough|"
                       r"shattered|exhausted|knackered|late|behind|broke)\b", re.I)

# Some facts are not just a thing about them: they limit what is worth suggesting. Saying back
# "your budget is 6,000 pounds" and stopping makes the store look like a notebook; a friend says
# what they will do with it. The echo is the same either way, the ending is what changes.
# A stated budget is a limit, and the person saying it is usually about to ask for something
# inside it, so the echo ends with the first thing to do with the figure rather than stopping at
# "I'll stick to that": "my budget is 300 a month" got a receipt and nothing else.
BUDGET_FRAMES = (
    "{Thing} \u2014 I'll keep any suggestions inside it: fixed bills and food first, then savings.",
    "{Thing}, then \u2014 I'll stick to that: fixed bills and food first, then a set amount to "
    "savings.",
    "{Thing} \u2014 noted, and I'll work within it: fixed bills and food first, then savings on "
    "payday.",
)
# A budget for a thing is not a budget to live inside. "my budget is about 40 pounds" said
# during a question about a present for a dad is the money to spend on the present, and the
# living-income ending - "fixed bills and food first, then savings" - answers a household budget
# nobody asked about: the person wanted to know what to buy with forty pounds. A stated period is
# what makes it a budget to live inside ("my budget is 300 a month"); with no period, a
# conversation that was about buying a thing makes it money to spend.
PERIOD = re.compile(r"\b(?:(?:a|an|per|each|every)\s+(?:day|week|fortnight|month|year)\b"
                    r"|weekly|monthly|fortnightly|yearly|annually|a month|in a month|"
                    r"a week|in a week)\b", re.I)
# A figure for a stretch of time is money to live on whatever follows it: "i have 40 quid for the
# week", "ive got 200 pounds for the rest of the month", "i have 500 for the rest of the month".
# `PERIOD` above only sees a bare "a week" or "a month", so these went past it and the "for the"
# in them was read as naming a purchase. None of them has a thing in it at all.
A_SPAN_OF_TIME = re.compile(
    r"\bfor\s+(?:the\s+(?:rest\s+of\s+)?(?:week|fortnight|month|year|day)\b"
    r"|this\s+(?:week|month|year)\b|next\s+(?:week|month|year)\b"
    r"|last\s+(?:week|month|year)\b|the\s+rest\b"
    r"|a\s+(?:week|fortnight|month|year|day)\b|an?\s+hour\b)", re.I)
# The words above all say the purchase with a verb. A line can say it without one, by naming what
# the figure is for: "ive got 200 pounds for a new bike", "my budget for a sofa is 600". Read
# without it, those lines got the living-income ending - "fixed bills and food first, then
# savings" - for money that was never a month to live inside.
FOR_A_THING = re.compile(r"\b(?:\d[\d,.]*|a few|a couple of|about)\s*(?:pounds?|quid|euros?|"
                         r"dollars?)?\s*(?:budget\s+)?for\s+(?:a|an|the|my|our|some|new)\b"
                         r"|\bbudget\s+for\s+(?:a|an|the|my|our|some|new)\b", re.I)
BUYING = re.compile(r"\b(?:buy|buys|buying|present|presents|gift|gifts|"
                    r"shopping for|looking for a|looking for some|looking for new|"
                    r"should i get|shall i get|which one|get (?:my|him|her|them|myself)|"
                    r"spend on|worth getting|what to get|need (?:a|some|new|another)\b|"
                    # A thing being taken on is a thing being bought, whatever verb carries it:
                    # "im thinking of getting a bike", "im after a new sofa", "i want a cat",
                    # "we are getting a kitten", "im planning a holiday", "i want to redecorate
                    # the bedroom" all got the household ending ("fixed bills and food first,
                    # then savings") to a question about what to spend the money on. Only the
                    # endings change here, and only when the line names no period and the rest
                    # of the chat holds no money word, so a budget to live inside keeps its own.
                    r"getting (?:a|an|one|some|new)\b(?!\s*(?:lot|bit|break|rest|handle|hold|"
                    r"sense|grip|kick|chance|look|few|couple|little|better|worse|"
                    r"grief|telling|hearing|going|ready))|after (?:a|an|some)\b(?!\s*(?:lot|bit|"
                    r"advice|help|idea|good|thought|while|time|break|rest|sense|point))|"
                    r"want (?:a|an|some|one|to get|to buy)\b(?!\s*(?:lot|bit|break|rest|handle|"
                    r"hold|sense|grip|kick|chance|look|few|couple|little))|"
                    r"planning (?:a|an|some|my|our)\b|moving (?:into|in|to|out|house|home)\b|"
                    r"redec\w+|renovat\w+|refurbish\w*)", re.I)
# The buying words are not proof of a purchase on their own: "i need a budget plan",
# "i need some help with money" and "i am looking for a job" wear them too, and the sentence about
# bills and food is the only advice in those turns. A money word in the rest of the conversation
# keeps the living reading.
MONEY = re.compile(r"\b(?:money|loan|loans|pension|pensions|mortgage|mortgages|credit card|"
                   r"credit cards|overdraft|debt|debts|savings|insurance|benefits|"
                   r"universal credit|job|jobs|salary|wage|wages|tax|budget|budgets|plan|"
                   r"planner|finances?|rent|bills?|groceries)\b", re.I)

# A stated budget is not always a month to live inside: "I'm looking for a sofa / my budget is
# about 600" is money to spend on a thing, and the ending about fixed bills and food is an answer
# to a different question. Same fact, different ending.
SPENDING_FRAMES = (
    "{Thing} \u2014 I'll keep what I suggest inside it.",
    "{Thing} \u2014 good, and everything I suggest will be within it.",
    "{Thing} \u2014 noted, and I'll stay under that with what I recommend.",
)
FOOD_FRAMES = (
    "{Thing} \u2014 I'll keep that in mind when I suggest food.",
    "{Thing}, good to know \u2014 I'll plan around it.",
    "{Thing} \u2014 noted, and I won't suggest anything that goes against it.",
)

# A condition said out loud ("im coeliac", "im diabetic") is a fact about their body, not
# news: it is said back like any other, and one that rules out a food says what the bot will do
# with it, the way a diet does. "Noted!" for "im coeliac" is the line that could have come
# before any message at all.
# A drink is not food. "You don't drink - I'll keep that in mind when I suggest food" is wrong in
# a chat about a party or a wedding, and said back it is the line STYLE.md rules out: a stock phrase
# that fits any message. The same frame without the food does the job.
DRINK_FRAMES = (
    "{Thing} \u2014 I'll keep that in mind for anything I suggest.",
    "{Thing}, good to know \u2014 I'll plan around it.",
    "{Thing} \u2014 noted, and I won't suggest a drink that goes against it.",
)
CONDITION_FOOD = {"coeliac": "gluten", "celiac": "gluten", "gluten intolerant": "gluten",
                  "lactose intolerant": "dairy"}
CONDITION_FRAMES = (
    "{Thing} \u2014 noted, and I'll keep {food} out of anything I suggest.",
    "{Thing}, good to know \u2014 I'll plan around the {food}.",
    "{Thing} \u2014 right, so nothing with {food} in it.",
)
# A limit that belongs to somebody they named - "my mum is allergic to shellfish", "my dog is
# allergic to chicken" - is kept the same way, and it is no more news than their own: said back as
# "Noted: your mum is allergic to shellfish" it is the filing cabinet again, and the warm line
# already exists in the file for the day the store files it as theirs by mistake. Only the ending
# changes: the allergy is not the speaker's, so the bot cannot say it will keep food out of what it
# suggests for them, and it can say it will remember it for the next time it comes up.
OTHER_LIMIT_FRAMES = (
    "{Thing} \u2014 I'll keep that in mind for anything I suggest.",
    "{Thing}, good to know \u2014 I'll work around it.",
    "{Thing} \u2014 right, so that is off the table for them.",
)

# A limit on what the plan can be - "nothing too tiring", "no long walks", "my sister can't walk
# far", "we need to keep it cheap", "not too much walking" - is a constraint, not a mood and not
# a symptom. The person is saying what to leave out, and the replies that read it as one of those
# have not heard it: "Fair enough \u2014 what's going on, then?" answers a line that named no feeling,
# and "How long has that been going on with your sister?" turns a short walk into an illness to
# date. The reading of the limit is bot.memory.facts.a_limit_on_the_plan, because the store must
# not file one as a plan; what is here is what the bot does with it.
#
# The tail is chosen by what the limit is on - feet, money, or neither - and never by the words of
# the line, so it cannot be pasted onto another message.
LIMIT_FRAMES = {
    "move": (
        "{Thing} \u2014 so anything I suggest stays short and flat, with somewhere to sit.",
        "{Thing}, then. Nothing I put to you needs hours on your feet.",
        "{Thing} \u2014 noted, and I'll keep the days gentle and close to a seat.",
    ),
    "money": (
        "{Thing} \u2014 so I'll keep what I suggest to what costs nothing.",
        "{Thing}, then. Nothing that needs paying up front.",
        "{Thing} \u2014 noted, and nothing pricey in anything I put to you.",
    ),
    # The same walking limit, on a stay rather than on a day out: a guest who cannot manage the
    # stairs is a question about the bed and the bathroom, and the day-out frame ("short and flat,
    # with somewhere to sit") answers a trip they are not on. The card about hosting went round
    # three times in a row instead, because nothing here had a frame for the plan it was on.
    "move_stay": (
        "{Thing} \u2014 so it is the downstairs room or a bed moved down, a chair in the shower "
        "rather than a step over the bath, and the outings one at a time.",
        "{Thing}, then \u2014 book the bed that needs no stairs and keep the week's outings short "
        "and near a seat.",
    ),
    "other": (
        "{Thing} \u2014 noted, and I'll keep anything I suggest inside it.",
        "{Thing}, then \u2014 I'll plan around it and keep what I suggest inside it.",
    ),
}

# A plan that is somebody coming to stay, and a plan that is a trip away. The frames are written
# for one or the other, so the limit has to know which plan it has landed on.
A_STAY_PLAN = re.compile(
    r"\b(?:coming|comeing|come|comes|staying|stays|stay|stopping|to stay|visiting|visit)\b"
    r"|\b(?:we|i)(?:'re| are| am)?\s+having\s+(?:people|family|guests|my|her|his)\b", re.I)
# A trip is a place they are going, not every plan the store knows: "im trying to lose weight"
# is a plan and a day out is not what it is, and the day-out frame answers a walk nobody is on.
A_TRIP_PLAN = re.compile(
    r"\b(?:going to|off to|heading to|away to|flying to|driving to|trip to|holiday|weekend away|"
    r"going away|staying near|in (?:june|july|august|september|october|november|december|"
    r"january|february|march|april|may))\b", re.I)
A_STAY_PERSON = re.compile(
    r"\b(?:mum|mam|mom|mother|dad|father|parents|gran|grandma|grandad|granny|nana|nan|"
    r"grandpa|grandparents|sister|brother|aunt|uncle|cousin|in laws|in-laws|mother in law|"
    r"father in law|friend|friends|guest|guests|visitors|family)\b", re.I)


def _the_plan_in_hand(memory, clean=""):
    """Which plan the last few turns are on: "stay", "trip", or None.

    A limit only means something against the plan it is a limit on, and the two plans want
    different frames: a guest who cannot manage the stairs is a bed and a bathroom, while a person
    who cannot walk far on a day out is a short, flat route. Read from the line itself and the
    last few turns, so a limit said with nobody planning anything is still the pools' business.
    """
    lines = []
    if isinstance(clean, str) and clean.strip():
        lines.append(clean)
    if isinstance(memory, dict):
        for turn in reversed((memory.get("turns") or [])[-PLAN_TURNS:]):
            said = turn.get("user") if isinstance(turn, dict) else None
            if isinstance(said, str) and said.strip():
                lines.append(" ".join(said.split()))
    for said in lines:
        if A_STAY_PLAN.search(said) and A_STAY_PERSON.search(said):
            return "stay"
    for said in lines:
        if A_TRIP_PLAN.search(said) and not a_limit_on_the_plan(said):
            return "trip"
    return None


# What a line may have given the store and still be only a limit: the person it is for, or a
# detail of the thing on the table. Anything more ("her back is bad", a plan) is a fact of its own
# and keeps the reply that fact would get.
_LIMIT_ONLY = frozenset(("people", "relations", "other", "others", "relation", "detail"))

# A line that opens with an ask word is a question, whatever words it has later: "what can i cook
# on a budget" carries a budget and is still the cheap-meals question, and the knowledge base
# answers it. Only a line with nothing to ask gets the limit said back.
_OPENS_WITH_AN_ASK = re.compile(
    r"^\s*(?:what|which|how|where|when|who|why|should|shall|can|could|would|will|do|does|"
    r"did|is|are|was|were|any|anyone|anything|tell me|give me|suggest|recommend)\b", re.I)

# A stated like is not something to file and read back. "i love pizza" was answered "Noted: you
# love pizza." - the filing cabinet, on the one kind of line where the person has just told you
# what they are like and given you an opening. The dislike said out loud is answered with a
# question about the thing ("Fair enough. What is it about mushrooms?"), so the like gets the same
# shape turned round: the person's own words said back with one question about the thing. Not
# every ending asks, because a question at the end of every reply reads as an interview, and the
# thing is the whole echo rather than the bare noun, so "i love the sea" keeps its "the" and "i
# love my dog" keeps its "my" - "Sea - what is it you like about it?" is the bot talking about a
# sea in general. A like that carries a second half ("i love pizza but the price is mad") keeps
# the plain frame, because the half is a fact of its own to answer (see a_liked_thing).
LIKES_FRAMES = (
    "{Thing} \u2014 what is it you like about it?",
    "{Thing} \u2014 what is it about it that gets you?",
    "{Thing}. Good to know \u2014 what do you like best about it?",
    "{Thing} \u2014 that goes in the keep pile. I'll remember it.",
)
# A like with a second half in it ("i love pizza but the price is mad") is not one thing named,
# and the thing comes out of the store with the second half still on it: "Pizza but the price is a
# good one" is a sentence about nothing. Only a thing of a few words with nothing that joins two
# clauses gets the like's own endings; anything longer keeps the plain frame it had.
A_LIKE_OF_ONE_THING = re.compile(r"^(?!(?:.*\b(?:and|but|because|so|though|although|when|if|"
                                 r"which|that)\b)).{2,40}$", re.I)


# The endings above say "it", so the line has to name one thing the person likes and nothing else
# that could be the "it": a line with two tastes in it ("you don't like fish but you love prawns"),
# somebody else's taste ("she likes crime dramas, you like comedy"), a second clause ("you love
# cooking, you do it most nights"), a comparison ("you like food more than churches") or a choice
# ("the one you like is 650") is answered by the plain frame, which claims nothing about a thing.
# The whole echo is tested rather than the stored thing, because the echo is what the reply says.
A_LIKE_ECHO = re.compile(
    r"^(?:you|we)\s+(?:really\s+|absolutely\s+|just\s+|still\s+|also\s+|do\s+|both\s+)?"
    r"(?:love|like|adore|enjoy|prefer)\s+(?P<thing>[^,;]+)$", re.I)
A_LIKE_WITH_TWO_HALVES = re.compile(
    r"\b(?:and|but|because|so|though|although|when|if|which|that|than|too)\b", re.I)
# Somebody they like is a person, and "what is it you like about it" turns them into a thing.
A_PERSON_LIKED = re.compile(
    r"\b(?:girl|boy|man|woman|guy|bloke|lad|lass|person|someone|somebody|people|they|them|him|her"
    r"|his|hers|theirs)\b", re.I)


def _a_like_of_one_thing(clean, memory=None):
    """Whether the line's whole echo is one thing the person likes."""
    echo = _echo(clean, memory)
    match = A_LIKE_ECHO.match(echo or "")
    if not match:
        return False
    thing = match.group("thing")
    if A_LIKE_WITH_TWO_HALVES.search(thing) or A_PERSON_LIKED.search(thing):
        return False
    return not any(re.search(r"\b" + re.escape(word) + r"\b", thing, re.I)
                   for word in (facts.RELATIONS or ()))


def _only_a_liking(found):
    """Whether the line filed a like and nothing else worth an answer of its own.

    The same guard as `_just_a_liking`, but a pet said in the like ("i love my dog") is not a
    second thing to answer: the store files the animal and then answers "Noted: you love your
    dog." A name, a job or a limit in the same line is a fact of its own and keeps its own ending.
    """
    rest = {key for key, value in (found or {}).items()
            if value and key not in ("tastes", "pets") and not key.endswith("_frame")}
    return bool((found or {}).get("tastes")) and not rest


def a_liked_thing(found):
    """The thing a stated like is about, or "" when the line filed no like.

    Only "how" of "yes" is a like: "i hate mushrooms" files the same shape with "no", and the
    dislike is answered by the composer's own question about the thing.
    """
    for entry in (found or {}).get("tastes") or []:
        if not isinstance(entry, dict) or str(entry.get("how") or "") != "yes":
            continue
        thing = " ".join(str(entry.get("thing") or "").split()).strip(" ,.:;!?")
        if (thing and "{" not in thing and "}" not in thing
                and len(thing.split()) <= 4 and A_LIKE_OF_ONE_THING.match(thing)):
            return thing
    return ""


# A limit on what a person can do needs no plan to be about: "she is 8 months pregnant and cant
# walk far" is the walking, and the plan is whatever comes next.
_AN_ABILITY = re.compile(
    r"\b(?:can'?t|cannot|can not|isn'?t able to|is not able to|not able to|only manage)\s+"
    r"(?:walk|climb|manage|stand|sit)\b"
    # The same limit said with the thing in it: "she cant do stairs" is what a person says about
    # the guest they are making a bed up for, and it has to reach the plan they are on rather than
    # be said back as a fact. The verb is fixed so an aside ("i cant do this", "cant do monday")
    # is not a limit on anything.
    r"|\b(?:can'?t|cannot|can not|isn'?t able to|is not able to|not able to|only manage)\s+"
    r"(?:do|manage|get\s+up|get\s+up\s+and\s+down|get\s+up\s+the|use|cope\s+with)\s+"
    r"(?:the\s+|a\s+|any\s+)?(?:more\s+)?(?:stairs?|steps?|hills?|walks?|walking|"
    r"climbing|standing)\b", re.I)

# How many turns back a plan still counts as the plan a limit is on. A limit said out of the blue
# is a remark about their life ("im on a budget", "im not very energetic"), and the pools that
# answer those already have the right thing to say: the knowledge base has the cheap-meal answer
# and a feeling is a feeling. A limit said while a plan is on the table is about the plan.
PLAN_TURNS = 3


def a_limit_reply(text, memory=None):
    """The limit said back with what the bot will do with it, or None when the line is more.

    Read before the pools a limit has already been misread by, so it has to say nothing at all
    unless the line really is only a limit: "im going to keep it cheap this month" is a month
    they have planned, not a limit to promise anything about.
    """
    if not isinstance(text, str):
        return None
    clean = " ".join(text.split())
    if not clean or "?" in clean:
        return None
    if _OPENS_WITH_AN_ASK.match(clean):
        return None
    family = a_limit_on_the_plan(clean)
    if family is None:
        return None
    if not _AN_ABILITY.search(clean) and not _a_plan_on_the_table(memory, clean):
        # Nothing is being planned, so there is no plan to keep anything out of. The line is a
        # remark, and the pools that answer remarks say something better: "im on a budget" is how
        # people ask what to cook for little money.
        return None
    found = _learned(text, memory)
    if found and not set(found) <= _LIMIT_ONLY:
        return None
    return _a_limit_reply(clean, family, memory)


# What the person wants on the plan, said while they say the limit: "i want to keep it cheap",
# "we would rather not walk too much". The want is the plan, so the limit has something to be on.
WANTS_IT = re.compile(
    r"\b(?:i|we)\s+(?:want|wanna|need|'?d like|'?d rather|would like|would rather)\s+to\b", re.I)


def _a_plan_on_the_table(memory, clean=""):
    """Whether there is a plan for the limit to be about.

    A limit is a narrowing of something. Said on its own it is a remark about their life ("im on a
    budget", "im not very energetic"), and those are answered better by the pools that read a
    budget as the cheap-meals question and a mood as a mood. It is a limit on a plan when the plan
    was said in the last few turns, was filed by the store, or is being said here in the same
    breath ("i want to keep it cheap").
    """
    if isinstance(clean, str) and WANTS_IT.search(clean):
        return True
    if not isinstance(memory, dict):
        return False
    seen = 0
    for turn in reversed(memory.get("turns") or []):
        said = turn.get("user") if isinstance(turn, dict) else None
        if not isinstance(said, str) or not said.strip():
            continue
        seen += 1
        if seen > PLAN_TURNS:
            return False
        if facts.PLAN.search(said) and not facts.a_limit_on_the_plan(said):
            return True
        if (facts.extract(said) or {}).get("plan"):
            return True
    return False


# How much of the person's own line is worth saying back. "she cant manage stairs" and "no long
# walks" name the limit itself, and naming it is what confirms the bot heard the right thing. "my
# nan is 90 and she cant do stairs" is a whole sentence: said back in front of the advice it is the
# person's own words plus the filing cabinet, and the reply is better starting with what it will
# do. The same advice, without the name.
#
# Only the limits whose reply is about what the bot will keep out of the plan (feet, money, a
# stay): a job in hand is the other way round, where naming the thing IS the answer - "i still have
# the school run to sort" has to come back saying the school run goes first - so those families
# keep their frames however long the line is.
SAID_BACK_WORDS = 7

LIMIT_AFTER_THE_LINE = {
    "move": (
        "So anything I suggest stays short and flat, with somewhere to sit.",
        "Then nothing I put to you needs hours on your feet, and there is a seat at the end of it.",
    ),
    "money": (
        "So I'll keep what I suggest to what costs nothing.",
        "Then nothing I put to you needs paying up front.",
    ),
    "move_stay": (
        "Then it is the downstairs room or a bed moved down, a chair in the shower rather than a "
        "step over the bath, and the outings one at a time.",
        "Then book the bed that needs no stairs, and keep the week's outings short and near a seat.",
    ),
}


def _a_limit_reply(clean, family, memory):
    """The limit said back, with what the bot will do with it."""
    body = _echo(clean) or clean
    if family == "move" and _the_plan_in_hand(memory, clean) == "stay":
        family = "move_stay"
    if len(body.split()) > SAID_BACK_WORDS:
        # A whole sentence is not a label for the limit: saying it back puts their words in front
        # of the answer, so the reply starts with what it will do with the limit instead.
        after = LIMIT_AFTER_THE_LINE.get(family)
        if after:
            return _pick_ending(after, memory)
    frames = LIMIT_FRAMES.get(family) or LIMIT_FRAMES["other"]
    return _pick_ending(frames, memory, thing=body, Thing=body[:1].upper() + body[1:])


def a_limit_for_the_plan(text, memory=None):
    """A limit on the plan in hand, or None when no plan is in hand or no frame fits it.

    Read by the chat module before it hands back the answer it already gave: a limit said about
    the plan ("shes 78 and cant do stairs" after "my mum is coming to stay") is the one thing that
    should change the answer, and the card went round three times instead. It only speaks when a
    plan of a kind the frames are written for is on the table, so a limit in a chat about a diet
    or a dripping tap keeps the reply it has.
    """
    if not isinstance(text, str):
        return None
    clean = " ".join(text.split())
    if not clean or "?" in clean or _OPENS_WITH_AN_ASK.match(clean):
        return None
    family = a_limit_on_the_plan(clean)
    if family is None:
        return None
    # A reply about the plan needs a plan from an earlier turn. On a first message there is
    # nothing to read the limit against, and the line is answered as the line it is.
    if not there_is_a_chat(memory):
        return None
    # Only a guest who is staying: a limit on a trip already has better answers below this module
    # ("my mum cant do stairs any more" after a few days away came back from the chat module with
    # "ring ahead for the ones you care about - a lift to the good floors and a loo you can get to
    # are the two questions worth asking", and a frame about a bed in the house would be worse).
    if _the_plan_in_hand(memory) != "stay":
        return None
    return _a_limit_reply(clean, family, memory)

# A separation is the same kind of news as a death: the person the lines are about has gone.
# "my wife left me", "we split up in march", "he walked out". The verb is ordinary, so "left"
# only counts with ", me" after it - "my sister left and came back" is not this - and the rest
# are phrases nobody says about anything else.
# "broke up" and "split up" are ordinary verbs - a bill is split, a band breaks up - so the
# verb has to close its clause: "we split up the bill" takes an object and is not this.
UP_CLOSED = (r"(?!\s+(?:the|a|an|it|this|that|these|those|my|his|her|their|your|our|"
             r"into|over|between)\b)")
# "left me" is the same shape: "i left me keys at home", "she left me a note", "left me to
# it" all take an object. A person who has left is what the phrase is about, so the clause
# ends there or a preposition or time follows: "left me for someone else", "left me last
# week", "left me with nothing".
LEFT_CLOSED = (r"(?=\s*(?:[,.!?;]|$|\b(?:for|after|last|in|on|at|with|when|because|so|and|"
               r"since|about|yesterday|today|tonight)\b))")

SEPARATION = re.compile(
    r"\b(?:left me|leaving me)" + LEFT_CLOSED + r"|"
    r"\b(?:walked out on|dumped me|cheated on me)\b|"
    r"\b(?:broke up|split up)" + UP_CLOSED + r"|"
    r"\bdivorce\w*\b|"
    # "he moved out" and "we separated" need who: a lodger moves out and an egg white
    # separates, and neither is a marriage ending.
    r"\b(?:he|she|they|my (?:wife|husband|partner|boyfriend|girlfriend|ex))\b[^.!?]{0,16}"
    r"\bmoved out\b|\b(?:we|my \w+ and i) separated\b")

# How many turns back a death or a separation still sets the tone. Three is about as long as
# people stay on it before a turn about something else.
HEAVY_TURNS = 3

# A hurt somebody is doing to the person, not a loss and not a marriage ending: "my son is being
# bullied at school", "he hits me", "my boss is horrible to me". A fact told in that room is not a
# form to be filed either - "Got it - he's 11" after "my son is being bullied" is the same clerk
# with a different receipt - so the room is set by the last few turns here too.
# Every phrase names a person doing it, because the words themselves are ordinary: a knee hurts
# me, the play was a hit, a film was violent, she pushed me to try again. A body part is not a
# person, and a past participle with no one in front of it is not happening now.
_NOT_A_BODY_PART = (r"(?<!\b(?:my|his|her|their|your|our)\s)(?<!\b(?:the|a)\s)"
                    r"(?<!\b(?:knee|back|leg|legs|arm|arms|head|shoulder|shoulders|neck|foot|"
                    r"feet|hip|hand|hands|stomach|tooth|teeth|ear|ears|eye|eyes|chest|ankle|"
                    r"wrist|joint|joints|muscle|muscles)\s)")
_BULLIED = re.compile(
    r"\b(?:bull(?:y|ies|ied|ying))\b|\bpick(?:s|ed|ing)?\s+on\b|\bpicked\s+on\b|"
    r"\bpicks\s+on\b|\bmean\s+to\s+(?:me|him|her|them|us|my\b)|"
    r"\bpicked\s+on\s+(?:me|him|her|them|us)\b", re.I)
# A person (the one the line names) doing the verb to someone: "he hits me", "my son hits me",
# "they shout at him at school", "she swears at the kids".
HURTS_A_PERSON = re.compile(
    r"\b(?:he|she|they|my\s+\w+|his\s+\w+|her\s+\w+|the\s+\w+)\s+"
    r"(?:(?:hit|hits|hit(?:ting)?|punch\w*|kick\w*|shov\w*|"
    r"slap\w*|smack\w*|threaten\w*)\s+"
    r"(?:me|him|her|them|us|the\s+(?:kids|children|baby|little\s+one))\b"
    # "beats me" is also how everybody says they lost: a game word after the verb means the
    # person is telling you about a match, not about harm. "my son beats me at chess" was read
    # as cruelty and answered "I'm sorry it's all coming at once", which is sorry for somebody
    # over a chess result. Bare "he beats me" keeps its reading, and the other verbs are not
    # guarded because "hit me in the face" is exactly where a place word follows them.
    r"|(?:beat|beats|beating)\s+"
    r"(?:me|him|her|them|us|the\s+(?:kids|children|baby|little\s+one))\b"
    r"(?!\s*(?:at|in|on)\s+(?:the\s+|a\s+|his\s+|her\s+|their\s+)?[a-z]))"
    r"|\b(?:shout|shouts|shouting|swear|swears|swearing|yell|yells|yelling)\s+"
    r"(?:at|at)\s+(?:me|him|her|them|us|the\s+(?:kids|children|baby|little\s+one))\b"
    r"|\b(?:is|are|was|were|being)\s+horrible\s+to\s+(?:me|him|her|them|us)\b"
    # "my husband was violent last night", "abel was violent": the violence is the whole clause,
    # so it needs a person as its subject and nothing after it that makes it a film or a match.
    r"|\b(?:he|she|they|my\s+\w+|his\s+\w+|her\s+\w+)\s+(?:was|is|were|are|"
    r"has\s+been|had\s+been|got)\s+violent\b"
    r"|\b(?:violent|violence)\s+(?:to|towards|with|at)\s+(?:me|him|her|them|us)\b"
    r"|\b(?:was|were|am|is|being|been)\s+harass\w*\s+(?:at|on|in)\b", re.I)
# "abel was violent last night": a person is the whole subject of the clause, so the line opens
# with the name - and people type names in lower case. What keeps "the match was violent" and
# "the night was violent" out is not a list of things but the word in front: a determiner means
# the subject is a thing, and a name has none.
A_NAME_WAS_VIOLENT = re.compile(
    r"^\s*(?!(?:the|a|an|it|there|this|that|these|those|my|his|her|their|your|our|we|i|you|he|"
    r"she|they)\b)[a-z][a-z'\u2019-]*\s+"
    r"(?:was|is|were|are|has\s+been|had\s+been|got)\s+violent\b", re.I)


def reads_as_cruelty(said):
    """Whether this line says somebody is doing the person harm."""
    text = " ".join(str(said or "").split())
    if not text:
        return False
    if _BULLIED.search(text) or A_NAME_WAS_VIOLENT.search(text):
        return True
    return bool(HURTS_A_PERSON.search(text))

# After a death or a separation, a fact said plainly is not a form to be filed. "She took the
# kids to her mums" answered with "noted" is colder than the general line it replaced: the
# person has just told you where his children are in the week his marriage ended, and a clerk
# says "noted". The fact still comes back - telling the bot is a choice they made - with the
# acknowledgement attached, from a pool of its own so "noted" is never one of the endings.
# These are for a fact that is theirs and ordinary, which is why they are only reached when the
# fact does not limit anything (a budget, a diet, a condition keep the ending they explain).
HEAVY_FRAMES = (
    "{Thing} \u2014 I'm sorry it's all coming at once.",
    "Got it \u2014 {thing}. That's a hard week.",
    "{Thing}. I'm sorry there's so much on your plate.",
)
# The same room, for a fact that is not one more thing landing on them: the cats, the job, the
# town. "my dad died / i have two cats" answered "You have two cats \u2014 I'm sorry it's all
# coming at once" says the cats are part of the pile, which is a claim nobody made. These keep the
# acknowledgement off the fact itself, so the warm ending is about the week and not about the cats.
STILL_FRAMES = (
    "{Thing} \u2014 got it. And I'm sorry it's a hard time.",
    "{Thing}. Noted \u2014 and I'm sorry you're having a hard week.",
    "{Thing} \u2014 I've got that. Still sorry for what you're going through.",
)

# The lead-ins people put in front of a fact: they are not part of it.
# A lead-in is the word in front of the fact and never the subject of it: "and i eat 1200" is
# "i eat 1200" with a joining word on the front, so it is said back as "you eat 1200". The long
# forms "and i" and "also i" were here, and the longest match wins, so the joining word took the
# person with it: "and i eat 1500" was said back as "Eat 1500 - noted." and "and i work at
# mcdonalds" as "Work at mcdonalds", with no "you" in either. "and" and "also" are already here
# and leave the "i" where it belongs.
LEAD_IN = ("hi", "hiya", "hello", "hey", "so", "well", "oh", "and", "also", "ok", "okay", "right",
           "because", "cos", "coz", "cause", "cuz", "because of", "cos of",
           "yeah", "yes", "actually", "anyway", "btw", "by the way", "just so you know",
           "quick one", "sorry", "haha", "lol", "oh and", "for the record",
           "one thing", "that reminds me", "thanks", "thank you", "cheers", "ta", "cool",
           "sorry one more thing", "one more thing", "one last thing", "last thing",
           "nice", "great", "yep", "yup", "mmm", "haha",
           # A hedge in front of a fact is the way somebody says it, not part of the fact:
           # "to be honest i dont like my flat" was said back as "Noted: to be honest you
           # don't like your flat", which hands the person their own shrug instead of an
           # answer. These are the words chat-speak arrives as ("tbh" and "ngl" are expanded
           # before the store sees the line) and a hedge is only ever a way in.
           "to be honest", "to be fair", "if im honest", "if i am honest", "if im being honest",
           "honestly", "tbh", "to tell the truth", "truth be told", "not going to lie",
           "not gonna lie", "ngl", "i wont lie", "i have to say", "i must admit",
           "i will say", "ill be honest", "to be truthful")
# A greeting or a self-introduction is the chat module's turn, not an echo's.
# A line with a question word in it wants an answer, not the echo: "i don't know what to get
# my dad for his 60th" said back is nonsense, however many facts it carries.
WANTS_ANSWER = re.compile(r"\b(?:what|which|how|where|whereabouts|when|who|why|whats|hows|"
                           r"whos|wheres)\b", re.I)
GREETING = re.compile(r"^\s*(?:hi|hiya|hello|hey|morning|good morning|evening|yo|howdy)\b", re.I)
# Words about dying are never said back, whatever the line means by them: "i want to die my
# hair pink" is a hair appointment, and "you want to die your hair pink" still reads badly.
DEATH_WORDS = re.compile(r"\b(?:die|died|dies|dying|death|dead|kill|killed|suicide)\b", re.I)
# The hours someone works are the shape of their week, and people say them as a fact: "i work
# nights", "my shifts are all over the place", "i get up at five for work". Said back they are
# a filing cabinet - "Noted: you work nights." - which is the coldest answer to somebody telling
# you about their life, so the reply is about the life those hours make. Each pool is its own
# kind of week, and the line has to be only that: see NOT_THE_HOURS before any of them.
ON_NIGHTS = re.compile(
    r"\b(?:(?:i|we)\s+(?:work|works|do|does|am on|are on|am doing|are doing|'m on|'re on)\s+"
    r"(?:the\s+)?night(?:s|\s+shift(?:s)?)?\b"
    r"|night shifts?\b|\bon nights\b|\bnights this week\b)", re.I)
EARLY_RISE = re.compile(
    r"\b(?:i|we)\s+(?:get up|get|start|leave|wake up|am up|are up|have to be up|'m up)"
    r"\s+(?:at|by|for)\s+(?:\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)?|four|five|six|seven|"
    r"half (?:four|five|six))\b", re.I)
LATE_FINISH = re.compile(
    r"\b(?:i|we)\s+(?:finish|finishes|get home|am back|'m back)\s+(?:at|around|about|by)\s+"
    r"(?:\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)?|nine|ten|eleven|twelve|half (?:nine|ten|eleven))\b",
    re.I)
LONG_SHIFT = re.compile(
    r"\b(?:\d{1,2}|twelve|ten|eleven)\s*[- ]?hour (?:shift|shifts|days?)\b"
    r"|\blong (?:days|shifts)\b|\bwork(?:ing)? long hours\b", re.I)
SHIFTS_ALL_OVER = re.compile(
    r"\b(?:my|our|the)\s+(?:shifts?|rota|hours)\s+(?:is|are|change|changes|move|moves|rotate|rotates|"
    r"all over|all over the place|everywhere|different|random|mad)\b"
    r"|\bshifts? (?:all over|all over the place|everywhere)\b"
    r"|\bwork(?:ing)? two jobs\b|\bsecond job\b", re.I)
WORK_FROM_HOME = re.compile(r"\bwork(?:ing)? from home\b|\bwork from home\b|\bwfh\b", re.I)
# The hours pools. Tonight, the body clock, the week around them: each one says something about
# the life those hours make, and none of them is a question, because a question at the end of
# every reply is the other half of the stock line.
NIGHT_TAIL = (
    "Nights turn the week upside down. The sleep in the day is never quite the same as the sleep "
    "at night, and that is the part people underrate.",
    "Nights, then. It is a different world at three in the morning, and not many people see it.",
    "Nights are hard on the body clock. Whatever makes the sleep after a shift work is worth "
    "protecting.",
)
EARLY_TAIL = (
    "That is an early start. The night before is where those mornings are won or lost.",
    "Up at that hour, the whole day is done by lunchtime. It is the evening that has to be "
    "guarded.",
    "That is a hard hour to be up, and it gets easier once the going to bed moves with it.",
)
LATE_TAIL = (
    "Finishing that late means the evening has gone by the time you are out. The wind-down is the "
    "bit worth protecting.",
    "That is a long day by the time you are home. The last hour of it is the one to keep for "
    "yourself.",
    "Home at that hour, the day turns into the next one. Best to have the food and the quiet "
    "already waiting.",
)
LONG_TAIL = (
    "Those are long days. Whatever you do for yourself has to be small enough to happen when you "
    "are wrecked.",
    "Long shifts like that leave nothing of the day. The food and the sleep are the parts that "
    "actually matter.",
    "That is a lot of hours. The days off are not a bonus, they are the half of the week that "
    "makes the rest work.",
)
SPREAD_TAIL = (
    "Shifts that move make the week hard to plan. The few fixed things - sleep, one day off, a "
    "meal at a set time - are what hold it together.",
    "A rota like that means no two weeks are the same. Worth putting the things you care about "
    "in before the rota comes out, not after.",
    "That kind of week is hard to build anything on. Whatever is regular in it is doing a lot of "
    "the work.",
)
HOME_TAIL = (
    "Working from home, the day has no edges unless you put them in. A walk at the end of it "
    "stands in for the commute.",
    "That suits a lot of people and it eats a lot of people. The bit that helps is stopping at a "
    "time rather than when the work runs out.",
    "Home all day, the work and the rest end up in the same room. A door you can shut, or a walk "
    "out of it, does more than any system.",
)
# An ask in any of the shapes people type it - "should i nap in the afternoon", "how do i stop
# waking at four", "is it worth it". The line before a line of hours is what decides whether
# those hours are a new subject or a detail added to the answer just given.
AN_ASK = re.compile(
    r"^(?:(?:and|so|but|ok|okay|well|also|plus)\s+)*(?:should|shall|can|could|do|does|did|is|are|"
    r"was|were|will|would|may|might|am|have|has|any|what|whats|which|how|hows|where|wheres|"
    r"whereabouts|when|who|whos|why)\b", re.I)


def reads_as_an_ask(line):
    """Whether this line asks something, in a shape a person types."""
    return "?" in line or bool(AN_ASK.match(str(line or "").strip()))


# A line about the hours that also carries something else is that other thing's line: a body that
# cannot sleep, a job they are sick of, a wage that does not cover it, a shift they want out of.
# Asking for tips is an ask, whatever shape it is in.
NOT_THE_HOURS = re.compile(
    r"\b(?:cant sleep|can'?t sleep|not sleeping|insomnia|exhaust\w*|knackered|shattered|"
    r"burn(?:t|ed) out|depress\w*|anxi\w*|panic|stress\w*|fed up|sick of|had enough|"
    r"hate|hates|quit|quitting|resign\w*|sacked|fired|redundant|laid off|losing my job|lost my job|"
    r"overtime|pay|paid|wage|wages|money|salary|boss|manager|colleague|interview|contract|"
    r"holiday|annual leave|tips|advice|how do i|how can i|what should|should i|help me|"
    r"pregnant|baby|kids?|child|school run|uni|college|course|exam)\b", re.I)

# A deadline said on the turn after an answer ("its tomorrow", "on friday", "in three weeks")
# is the one thing that answer did not know, and it changes what the answer is worth: it was
# written for a person with room. Said back as a receipt it uses nothing - "Got it - it's in
# three weeks." - and said back as a shrug ("I'm listening - say more if it helps") it is the
# fallback not hearing it at all. The line has to name the clock and be about the clock alone,
# and the turn before has to be a real answer rather than a hello or a hedge.
WHEN_DETAIL = re.compile(
    r"^(?:and |oh |also |so |but )?"
    r"(?:(?:its|it's|it is|thats|that's|that is|were|we're|i'm|im)\s+(?:(?:on|in)\s+)?"
    r"|(?:on|in)\s+|and\s+)"
    r"(?P<when>"
    r"tomorrow|tonight|today"
    r"|this (?:weekend|week|morning|evening|afternoon)"
    r"|next (?:week|month|weekend|year)"
    r"|monday|tuesday|wednesday|thursday|friday|saturday|sunday"
    r"|(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"\s+(?:days?|weeks?|months?)"
    r"|a (?:few|couple of) (?:days|weeks)"
    r"|a couple of (?:days|weeks)"
    r")"
    r"(?:\s+(?:away|left|to go))?\s*[.!]*$", re.I)
# A deadline comes in four shapes and each leaves a different amount of room, so each has its
# own pool: today and tonight are already running, tomorrow has today in front of it, a figure
# counted in days is one step a day, and only a week or more is room to do the whole thing.
WHEN_TODAY = re.compile(r"\b(?:today|tonight|this (?:morning|afternoon|evening))\b", re.I)
WHEN_TOMORROW = re.compile(r"\btomorrow\b", re.I)
WHEN_DAYS = re.compile(
    r"\b(?:this (?:week|weekend)|monday|tuesday|wednesday|thursday|friday|saturday|sunday"
    r"|a few days|a couple of days)\b", re.I)
COUNTED = re.compile(r"\b(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)"
                     r"\s+(days?|weeks?|months?)\b", re.I)
COUNT = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10}


def _shape_of(when):
    """Which kind of clock this deadline is: today, tomorrow, days, or room.

    "Two days" is not "three weeks": a figure counted in days leaves a step a day, and a figure
    counted in weeks or months is room to spread the whole thing out. The pools are one per shape
    so a deadline tonight never gets a sentence written for one three weeks off.
    """
    if WHEN_TODAY.search(when):
        return "today"
    if WHEN_TOMORROW.search(when):
        return "tomorrow"
    found = COUNTED.search(when)
    if found:
        number = COUNT.get(found.group(1).lower(), found.group(1))
        unit = found.group(2).lower()
        if unit.startswith("month"):
            return "room"
        if int(number) <= (5 if unit.startswith("day") else 1):
            return "days"
        return "room"
    if WHEN_DAYS.search(when):
        return "days"
    return "room"


# What the clock leaves, said as what to do with it rather than as a claim about the answer we
# gave: the bot knows the deadline and it knows the answer was advice, and it does not know what
# that answer assumed about time. A statement either way, and never a question at the end.
WHEN_TODAY_TAIL = (
    "{When}, so the first of it happens now: a small thing done today beats a better one that "
    "waits for a quiet hour.",
    "There is no day left to work up to it in. {When} is the day, so start at the first step.",
    "{When} is already here, which makes the part of it you were saving for later today's job.",
)
WHEN_TOMORROW_TAIL = (
    "Tomorrow, so today is the working day: the first step now beats a good plan for the morning.",
    "That leaves today for it. Do the part you would least like to be doing at the last minute.",
    "Tomorrow, then. Whatever in that needs two sittings has to have the first of them today.",
)
WHEN_DAYS_TAIL = (
    "{When} is one step a day rather than all of it at once: pick the first step and give it "
    "today.",
    "{When}, so count the days and put a step in each one. The last day is for checking, not "
    "starting.",
    "{When} only fits the whole of it if each day carries a bit of it: start today, not on "
    "the last one.",
)
WHEN_ROOMY_TAIL = (
    "{When} is enough time if you spread it: one small bit a week, and the last week only "
    "checking.",
    "{When} gives you room to do it properly. Start with the part you would least like to get "
    "wrong.",
)
# A time of day said for the thing we just answered is the same detail as a deadline one step
# finer: "im worried about my interview tomorrow" / "its at 10" is not a fact to file and hand
# back. It was answered two ways, both cold - the stock line ("Thanks for telling me - I'm here if
# you want to dig into any of that") when the reading was only the bare time, and the receipt
# ("Got it - the interview is at 10") when the line named the thing, which is the person's own
# line said back. The hour is kept and the answer above is aimed at it instead.
TIME_WORD = (r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
             r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)")
# The time with its own marker - "10am", "9:30", "half nine", "ten o'clock" - is a time whichever
# word is in front of it.
CLOCK_DETAIL = re.compile(
    r"^(?:and |oh |also |so |but )?"
    r"(?:(?:its|it's|it is|thats|that's|that is|were|we're|the\s+[a-z'-]+\s+is)\s+)?"
    r"(?:at\s+|for\s+)?"
    r"(?P<when>"
    r"\d{1,2}[:.]\d{2}\s*(?:am|pm|a\.m\.|p\.m\.)?"
    r"|\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.)"
    r"|\d{1,2}\s*o'?\s?clock"
    r"|(?:half|quarter)\s+(?:(?:past|to)\s+)?" + TIME_WORD +
    # "ten to four" is a time the same way "quarter to four" is: the minutes to the hour, which
    # the pattern above only had for the half and the quarter.
    r"|(?:five|ten|twenty|twenty[- ]five)\s+to\s+" + TIME_WORD +
    r"|" + TIME_WORD + r"\s+(?:o'?\s?clock|am|pm|a\.m\.|p\.m\.|thirty|fifteen|"
    r"forty[- ]five)"
    r"|\d{1,2}\s+(?:thirty|fifteen|forty[- ]five))"
    r"\s*[.!]*$", re.I)
# "its at 10" and "at ten" have no marker of their own, so the "at" is what makes them a time:
# without it a bare figure is a count ("i have 10") and a bare word is anything at all.
CLOCK_AT = re.compile(
    r"^(?:and |oh |also |so |but )?"
    r"(?:(?:its|it's|it is|thats|that's|that is|the\s+[a-z'-]+\s+is)\s+)?"
    r"(?:at|for)\s+"
    r"(?P<when>(?:\d{1,2}[:.]\d{2}|\d{1,2}|" + TIME_WORD + r")(?:\s*(?:am|pm))?)"
    r"\s*[.!]*$", re.I)
# The clock is not a deadline: it is an hour on a day, so the answer is aimed at the hour rather
# than spread out. A person with an appointment at ten has a run-up, and the part of the answer
# that wants them sharp belongs in it.
# Morning or afternoon decides which half of the day the hour eats: a scan at half nine has the
# run-up in it, and an appointment at 2:30 has a free morning in front of it. The pools are one
# each so a ten o'clock never gets a sentence written for half past two.
CLOCK_MORNING_TAIL = (
    "{At} on the day, so be there twenty minutes early and the nerves have somewhere to sit while "
    "you wait.",
    # The hour is an adverbial, never the subject of what follows: "At ten o'clock means..." and
    # "At ten o'clock leaves..." are sentences with no subject in front of the verb. So a frame
    # that goes on to say what the hour does carries its own subject, and the hour stays in it.
    "{At}, so the day is built around it, and the bit that wants you sharp belongs before you "
    "set off rather than after.",
    "{At}, so there is enough of the morning to get ready without rushing it, which is usually the "
    "part that decides how it goes.",
)
CLOCK_AFTER_TAIL = (
    "{At}, so the morning is free for the part that needs you sharp, and nothing else has to fit "
    "round it.",
    "{At} on the day: get the other jobs done in the morning so you go into it with nothing else "
    "on your mind.",
    # Not "{At}, and the clear morning is where...": "and" after the hour leaves the clause it
    # opens without a subject, and this is the frame an afternoon hour lands on one time in three.
    "{At}, so the morning is where the part that wants a steady head goes, and the afternoon is "
    "clear for it.",
)
# The things a person sits down for at an hour, beyond the diary words the date reader already
# knows: "i need to see a dentist this week and im dreading it" names no appointment, and the
# reply to the hour after it was the receipt again.
#
# This list is the appointments, and only the appointments, because both pools it opens with talk
# about nerves and a run-up. A shift, a class, a viewing and lunch with a sister have an hour too,
# and none of them has a morning to build or a nerve to settle: those are in CLOCK_FLAT below.
CLOCK_EVENT = re.compile(
    r"\b(?:dentist|dental|optician|hygienist|doctor|gp|surgery|vet|clinic|hospital|"
    r"hearing|interview|appointment|scan|exam|test|checkup|check-up|consultant|physio|"
    r"physiotherapy|podiatrist|chiropodist|midwife|blood\s+test|presentation)\b", re.I)
# An hour on the day that nobody is nervous about: "im meeting my sister for lunch" / "its at 1"
# got "so the morning is where the part that wants a steady head goes", and a night shift at 10pm
# got told the morning was free - the opposite of the day the person has. One flat pool for these,
# with no claim about the morning and no nerves in it.
CLOCK_FLAT = re.compile(
    r"\b(?:meeting|viewing|shift|class|lesson|lecture|rehearsal|assessment|haircut|tattoo|"
    r"collection|pickup|lunch|dinner|breakfast|drinks|supper)\b", re.I)
CLOCK_FLAT_TAIL = (
    "{At}, then, and the rest of the day arranges itself round it rather than the other way round.",
    "{At} on the day, so what comes before it is short and what comes after it is free.",
    "{At}, so the day is built round it and nothing else has to be squeezed in before it.",
)
CLOCK_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
               "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
               "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
               "nineteen": 19, "twenty": 20}


def _clock_shape(when):
    """Which half of the day the hour is in: "morning" or "after".

    "At ten" is the morning, "at 2:30" is the afternoon, and "half nine" is half past nine in the
    morning - so a bare figure in the early hours is read as the afternoon, which is what a
    person means when they say an appointment is at two.
    """
    said = str(when or "").lower()
    found = re.search(r"\d{1,2}|[a-z]+", said)
    if not found:
        return "morning"
    token = found.group(0)
    hour = CLOCK_WORDS.get(token) if not token.isdigit() else int(token)
    if hour is None:
        return "morning"
    if "pm" in said or "p.m" in said:
        return "after"
    if "am" in said or "a.m" in said:
        return "morning"
    if hour <= 3:
        return "after"
    return "morning" if hour < 12 else "after"
# A deadline can only cut an answer down when the answer was telling them what to do. After a list
# of facts - "how much water should i drink", "im allergic to peanuts" - there is no first step to
# point at and nothing with a day on it, so "tomorrow" has nothing to be close to. The mood of the
# answer's opening is what tells them apart: advice starts on the doing word, a fact starts on the
# thing the fact is about.
STEP_OPENS = re.compile(
    r"^\s*(?:first|firstly|start|begin|own|book|name|skip|put|blot|pour|turn|take|check|keep|let|"
    r"leave|get|add|cut|fill|soak|wash|rinse|call|ask|write|print|plan|split|break|set|read|look|"
    r"watch|listen|tell|say|try|do|go|sit|spend|give|use|make|run|buy|pick|wear|choose|cook|boil|"
    r"roast|fry|steam|bake|rest|chill|freeze|store|measure|weigh|clean|wipe|scrape|open|hold|walk|"
    r"drive|move|cover|line|grease|trim|water|feed|brush|email|text|ring|phone|budget|save|"
    r"avoid)\b", re.I)


def _tells_them_what_to_do(said):
    """Whether the answer just given was advice they can act on, rather than a list of facts."""
    opening = re.split(r"(?<=[.!?])\s+", str(said or "").strip(), maxsplit=1)[0]
    return bool(STEP_OPENS.match(opening.strip()))


# A birthday nobody reached ("my mum would have been 70 this week") is grief, not a fact, and
# saying it back is the coldest reply there is: "your mum would have been 70 - noted". A line
# with a life cut short in it is left to bot/compose/loss.py, and a stock reply beats an echo.
WOULD_HAVE_BEEN = re.compile(r"\bwould(?:\s*have|'ve)?\s+(?:\w+\s+){0,2}been\b", re.I)
# A body that hurts is not a fact to read back either: "you've got a urine infection - noted"
# is a clerk reading a form, and "your dog choked on a bone - noted" says nothing about the
# dog. The emergency and the health modules answer those lines; where they do not, the stock
# line is still better than the echo. The typo'd spellings are here too: `infec` reaches
# "infecshun", and `sezure` is a fit typed fast.
#
# Only the words a person means about a body are here. "i burnt the toast", "im sick of my job"
# and "the printer is broken" are said back happily, and "bleed" is left out because a radiator
# and a bank account are bled too: the dry one is below, and BLEED covers the cut. A temperature
# is a measurement rather than a complaint, so "my daughter is 3 and has a temperature of 38.2"
# is read back like the fact it is; the fever next to it is not.
BODY = re.compile(
    r"\b(?:pain\w*|ache\w*|aching|hurts?|hurting|illness|poorly|unwell|fever\w*|"
    r"rash\w*|swell\w*|swollen|infec\w*|antibiotic\w*|blood\w*|"
    r"choked?|choking|swallow\w*|dizz\w*|nausea\w*|vomit\w*|diarrhoea|migraine\w*|"
    r"sore|cramp\w*|symptom\w*|injur\w*|wound\w*|fractur\w*|"
    r"surger\w*|operation|a&e|111|999|seiz\w*|sezure|breathless\w*|x-ray|xray)\b", re.I)
# A line that is only how the body is ("im shaky", "im bunged up", "im queezy") is not a fact
# about the world: said back it is "Noted: you're bunged up", which gives the person nothing to
# do with it. What it wants is one practical thing and a question, and bot/compose/fallback.py
# has a pool for each kind of state (BODY_STATES). The words are listed here as well because the
# echo has to decline the line first and bot/memory must not import bot/compose. They are only
# read when the line is nothing but the state, so "im queasy about the move" keeps its own
# answer.
BODY_STATE_WORDS = frozenset("""faint faintish fainting woozy dizzy giddy groggy wobbly shaky
clammy sweaty queezy queasy nauseous nauseated bilious sickly bunged sniffly sniffles sniffing
croaky hoarse congested sneezing lightheaded
pale pallid ashen grey gray greyish grayish mottled blotchy spotty puffy bloated flushed
feverish shivery tender husky snotty""".split())
BODY_STATE_PHRASES = frozenset(("light headed", "bilious", "bunged up", "blocked up"))
# What can follow the state and leave the state the whole of the line: "im bunged up now",
# "im shaky again".
BODY_STATE_TAIL = frozenset("""today tonight now still again though honestly already here
actually really so very absolutely bloody thanks up and""".split())


def _a_bare_state(clean):
    """Whether the line is nothing but a state of the body ("im bunged up", "im shaky")."""
    words = [w.strip(".,!?;:") for w in clean.replace("-", " ").split()]
    words = [w for w in words if w]
    if words[:1] in (["im"], ["i'm"], ["iam"]):
        words = words[1:]
    elif words[:2] == ["i", "am"]:
        words = words[2:]
    else:
        return False
    if not words:
        return False
    if " ".join(words) in BODY_STATE_PHRASES:
        return True
    return (any(w in BODY_STATE_WORDS for w in words)
            and all(w in BODY_STATE_WORDS or w in BODY_STATE_TAIL for w in words))


# "my nose is bleeding" is a body, "my dad is bleeding me dry" and "how do i bleed the radiator"
# are not, so the word only counts when it is not that shape.
BLEED = re.compile(r"\bbleed\w*\b(?![^.!?]{0,12}\b(?:dry|radiator|boiler|pipe\w*)\b)", re.I)
SELF_INTRO = re.compile(r"^\s*(?:i(?:'m| am)|im|my name(?:'s| is))\s+[A-Z][a-z'\u2019-]+\b")
# A greeting is the chat module's turn even when it does not open with "hi": "nice to meet you,
# i'm Sam" said back loses the word it opens with, because "nice" is a lead-in here, so the echo
# came out as "to meet you sam!" - half a sentence, and the hello unanswered. Every way of
# meeting somebody, and the how-are-yous, which are greetings and not a fact to file.
MEET_GREET = re.compile(
    r"^\s*(?:(?:nice|good|great|pleased|lovely|glad|happy|grand)\s+to\s+"
    r"(?:meet|see|hear\s+from)\s+(?:you|u|ya)\b"
    r"|(?:good|great|lovely|nice)\s+to\s+have\s+you\b"
    r"|how\s+(?:are|r)\s+(?:you|u|ya)\b"
    r"|how(?:'s|s|\s+is)\s+(?:it\s+going|things|tricks|you\s+doing|your\s+day)\b"
    r"|how\s+do\s+you\s+do\b"
    r"|long\s+time\s+no\s+see\b)", re.I)
# Where the echo stops: a full stop always, "and" only when a new subject starts after it.
SUBJECT = (r"(?:i|i'm|im|i've|i'd|we|we're|my|our|mine|she|she's|he|he's|it|it's|they|"
           r"they're|his|her|its|their)")
# A comma only ends a clause when a space follows it, so "6,000" and "£1,50" stay whole.
STOP = re.compile(r"\s*(?:,\s|;|\.\s|$|\b(?:because|so|but)\b|\b(?:and|then)\b\s+(?="
                  + SUBJECT + r"\b))\s*", re.I)
WORD = re.compile(r"[A-Za-z0-9'\u2019-]+")
# Thanks on the end of a fact ("my dog is fine now thanks") is not part of the fact.
POLITE = re.compile(r"[,\s]+(?:thanks|thank you|cheers|ta|please|thx)\s*$", re.I)
from .filler import TAIL_OFF, without_filler  # noqa: F401  (the echo drops the same filler)
# A fact to say back is a state of their world: who someone is, how old, where, what they are
# planning, what they are allergic to. The second person's *actions* are another matter: "my
# husband never helps" or "my son is being bullied" are things to answer kindly, not to read
# back, so a line with a word of trouble in it is left to the modules that answer them.
STATE = re.compile(
    r"\b(?:is|are|am|im|'s|'re|'m|was|were|has|have|had|'ve|ive|can|will|'ll|need|needs|want|wants|"
    r"live|lives|work|works|study|studies|love|loves|like|likes|prefer|prefers|go|goes|going|"
    r"off to|plan|plans|planning|train|training|learn|learning|move|moving|fly|flying|getting|"
    r"got|adopted|allergic|spend|save|saving)\b", re.I)
TROUBLE = re.compile(
    r"\b(?:being|bullied|bullies|bully|teas\w+|never|always|keeps|kept|refuses|refused|"
    r"stopped|stops|quit|hates?|hated|hit|hits|shout\w*|yell\w*|scream\w*|argu\w*|row|"
    r"won'?t|doesn'?t|didn'?t|isn'?t|can'?t|cannot|failed|failing|behind|ignores?|ignored|"
    r"blames?|blamed|lost|losing|dead against|just want|just need|driving me|drives me|"
    r"doing my head in|fed up|sick of|had enough|tether|drives? me mad)\b", re.I)
# Words that carry no meaning of their own when deciding whether a line says anything new.
_EMPTY = frozenset("""a an the and or but if so then this that these those it its it's i i'm im me my
we we're us our you your he she they them his her their is are was were be been being am 's 're
of to in on at for with from about as not no do does did have has had will would can could just
really very too also still now""".split())
# Lines that are answered elsewhere, or that no echo can carry: a farewell, a summons back to an
# old subject ("back to the radiator"), a yes/no read of the last turn ("no, no temperature"), and
# a feeling, which wants a word of its own rather than the fact said back.
# A complaint about how someone treated them, or a penalty that landed on them: "my boss had a
# go at me", "i got a parking ticket", "i got a fine". Two things follow. Said back ("Got it -
# your boss had a go at you") it is only the bad thing again, so it is not a detail; and it is not
# small talk either, so the gentle pool is a better answer than a stock nod. The forms the trouble
# words already carry ("shouted at me", "had a row") are caught before this one.
# A feeling is the modules' turn, never the echo's: "you want to cry - noted" answers nothing
# about the crying, and "for moaning - noted" is cold to someone apologising for it. The words are
# only the ones that can be about how a person feels.
_FEELING_WORDS = (
    r"worried|frightened|scared|terrified|afraid|fear\w*|dread\w*|anxious|panic\w*|"
    r"overreacting|upset|angry|annoyed|sad|lonely|guilty|embarrassed|ashamed|stressed|"
    r"exhausted|knackered|weary|miserable|cry|cried|crying|tears?|sob\w*|moan\w*|whinge\w*|"
    r"whine|rant\w*|vent\w*")
A_FEELING = re.compile(r"\b(?:" + _FEELING_WORDS + r")\b", re.I)
# A good mood is a feeling too, and filing it as a fact says it back as an entry in a notebook:
# "life is good" was answered "Got it - life is good." The words here are the mood said without
# an event in it; a line that carries news as well ("im happy, i got the job") is left alone
# because a job, a baby or a pass is a fact and the news modules answer it better.
GOOD_MOOD = re.compile(
    r"\b(?:in (?:a|an) (?:very )?(?:good|great|fine) mood|good mood|great mood|feeling good|"
    r"feel good|feeling great|feel great|cheerful|cheery|in good spirits)\b", re.I)
A_EVENT = re.compile(
    r"\b(?:job|promotion|baby|exam|test|interview|offer|house|flat|course|degree|wedding|"
    r"engagement|engaged|pregnant|expecting|won|passed|accepted|hired|booked|sold|bought|"
    r"holiday|graduated|qualified|retired)\b", re.I)
# A good result is news too, and it says it without any of the nouns above: "i feel good, i got
# the all clear" is a scan, not a mood. Kept as its own pattern because it is a phrase, not a
# word.
A_CLEAR = re.compile(
    r"\b(?:all clear|(?:came|come|comes) back clear|(?:scan|results?|tests?) (?:was|is|were|are) "
    r"clear|given? the all clear)\b", re.I)


# A result is reportable whatever its noun, and a closed list of nouns missed most of them: a
# daughter into university, a dissertation finished, a day that went well. The shape is what makes
# it news - someone who did the thing, and the thing said as done - so the mood word is left with
# the mood pool only when no such clause is there.
A_RESULT = re.compile(
    r"\b(?:i|we|he|she|they|my \w+|our \w+)\s+(?:(?:just|finally|only|also|now)\s+)?"
    r"(?:got|gotten|finished|finishes|started|starts|passed|passes|won|wins|landed|booked|"
    r"sold|bought|completed|handed in|graduated|qualified|retired)\b"
    r"|\b(?:went|gone) (?:well|great|brilliant|fine)\b"
    r"|\bout of (?:the )?hospital\b|\bhome from (?:the )?hospital\b", re.I)
# Moving is news when it is a move to a place, not when it is a sofa: "i moved the sofa" was read
# as an event and lost the mood pool it had on main.
A_MOVED = re.compile(r"\b(?:moved|moving|move) (?:in|into|to|house|out|abroad|back|country)\b",
                     re.I)


def has_news(text):
    """Whether the line carries something that happened, as opposed to how they feel."""
    text = text or ""
    return bool(A_EVENT.search(text) or A_CLEAR.search(text) or A_RESULT.search(text)
                or A_MOVED.search(text))


COMPLAINT = re.compile(
    r"\bhad a (?:go|dig|pop) at\b|\b(?:gave|given|handed) me a (?:ticket|fine|bollocking)\b|"
    r"\b(?:got|get|gets|getting|received) (?:a |an |the |my )?(?:parking |speeding |"
    r"fixed penalty )?(?:ticket|penalty|caution|warning|bollocking)\b|"
    # "fine" is an ordinary word too ("we got a fine view of the bay"), so it counts only when
    # nothing pleasant follows it.
    r"\b(?:got|get|gets|getting|received|gave me) (?:a |an |the )?fine\b"
    r"(?!\s+(?:view|views|day|time|weather|meal|bit|line|mess|idea|point|thing|way|year))|"
    r"\b(?:parking|speeding) ticket\b|\bclamped\b|\b(?:a|the) telling off\b|"
    r"\btold (?:me )?off\b|\ba bollocking\b", re.I)
_NOT_A_DETAIL = re.compile(
    r"\b(?:bye|goodnight|good night|catch (?:you|up)|speak (?:later|soon)|talk later|see you|"
    r"night then|anyway|back to|as i said|like i said|nothing much|not much|"
    r"can'?t complain|same old|same as ever|not a lot|how about you|you\?|"
    r"fair enough|sounds good|(?:i'?ll|i will|ill) (?:try|give) (?:that|it)|will do|no worries|"
    r"nice one|same to you|not bad|all good|"
    # A line about the conversation rather than about the thing we are on: "i want to say
    # something", "how do i put it", "soz meant tuesday" - the corrections and the small talk
    # have their own answers, and saying these back adds nothing.
    r"want(?:ed)? to (?:say|ask|tell)|how (?:do|should) i put it|\bmeant\b|\bsoz\b|"
    # A line about what was said rather than about the thing: "lol i said that ages ago",
    # "i told you already" - said back it is only the complaint again.
    r"\bi (?:said|told you|mentioned|already|just said)\b|\bas i said\b|\blike i said\b|"
    # A complaint about someone else, or a misfortune that landed on them, wants a sympathetic
    # word: said back it is only the bad thing again.
    + COMPLAINT.pattern +
    r"|" + _FEELING_WORDS + r")\b", re.I)
_SAID_YES_NO = re.compile(r"^(?:no|nope|nah|yes|yeah|yep)\b(?=[,.!]|\s+(?:please|thanks|thank you|"
                          r"mate|then)\b|$)", re.I)
_ANSWER_OPENER = re.compile(r"^(?:ok|okay|course|right)\b[ ,]", re.I)
# A question without its question mark: "they want 30 days notice is that normal" asks
# something, and a question said back is the question repeated.
_ASKS_MIDWAY = re.compile(r"\b(?:is|are|was|were|do|does|did|can|could|should|would|will|shall|"
                          r"have|has)\s+(?:it|that|this|they|i|we|you|he|she)\b", re.I)
# A request for a recommendation ("anything funny on netflix", "something with chicken") said
# back is the question repeated, which helps nobody: those lines want an answer, not an echo.
_ASKED_FOR = re.compile(r"^(?:any|anything|something|someone|somewhere|nowhere|nothing)\b", re.I)
DIGIT = re.compile(r"\d")
# Something of theirs that has gone wrong: "the washing machine is making a bang on the spin" is
# a fault to sort out, and "I'll remember that" about a bang is worse than no reply at all.
_FAULT = re.compile(
    r"\b(?:leak\w*|drip\w*|blocked|clogged|jammed|stuck|won'?t start|won'?t turn on|"
    r"stopped working|not working|isn'?t working|broken|broke|bang(?:s|ing)?|rattl\w*|noisy|"
    r"grind\w*|screech\w*|whin\w*|error code|flashing|blinking|rust\w*|damp|mould\w*)\b",
    re.I)
# Subjects no echo can serve, whatever the new line adds to them.
_NOT_A_DETAIL_SUBJECT = re.compile(
    r"\b(?:funeral|grief|passed away|passed on|death|died|widow|hospital|diagnos\w*|"
    r"lost (?:the|our|a) (?:baby|pregnancy)|miscarriage|stillborn|"
    r"cancer|chemo|depress\w*|anxiety|breakup|broke up|divorce)\b", re.I)
FRAGMENT = 30  # a short answer with no verb at all ("Tokyo and Kyoto") still reads well back
# "w/ the kids" is "with the kids" before anything else reads the line.
WITH_SLASH = re.compile(r"\bw/\s*", re.I)
# "going 2 spain", "back 2 work": after a verb of moving, the figure is the word "to". Everywhere
# else it is a number ("he is 2 yrs old"), which reads back as a word. A length of time is the
# exception the verb cannot see: "im going 2 weeks in may" is two weeks away, and saying it back
# as "you're going to weeks in may" invents a place out of a duration. The units are the ones a
# length of time is said in, and a unit is never somewhere you go - with two exceptions that do
# name a place: "night school" and "the weekend job". So "im going 2 night school" stays "to".
DURATION_UNITS = frozenset("""week weeks day days month months year years hour hours
fortnight fortnights minute minutes min mins""".split())
TWO_TO = re.compile(r"\b(?:going|go|goes|went|off|back|fly|flying|drive|driving|walk|walking|"
                    r"head|heading|move|moving|travel|travelling|coming|come|be|been)\s+2\b"
                    r"(?!\s*(?:%s)\b)" % "|".join(sorted(DURATION_UNITS)), re.I)
# The same figure in front of a place, with no verb in between: "2 the gym", "2 bed", "2 work".
TWO_PLACE = re.compile(r"\b2\s+(?=(?:the|a|an|my|our|his|her|their|its|work|bed|school|town|"
                       r"uni|university|college|church|hospital|town)\b)", re.I)
# "need 2 go", "have 2 work late": in front of a verb the figure is "to" again, and in front of a
# noun it is not - "have 2 kids" is two children, not "to kids".
TWO_VERB = re.compile(r"\b2\s+(?=(?:go|get|come|see|do|be|make|take|put|give|tell|say|try|book|buy|"
                      r"ask|call|send|pay|sort|check|fix|start|stop|leave|stay|eat|drink|sleep|run|"
                      r"walk|drive|catch|meet|pick|order|cook|clean|wash|pack|post|ring|text|email|"
                      r"look|find|keep|learn|help|join|move|remember|finish|read|get)\b)", re.I)

# Chat-speak the person typed, folded before the echo: "im allergic" is said back as "you're
# allergic", which reads like a person wrote it. Only forms with one reading are here.
SPEAK = {"im": "i'm", "ive": "i've", "i'd": "i'd", "id": "i'd", "ill": "i'll",
         "dont": "don't", "didnt": "didn't", "doesnt": "doesn't", "cant": "can't", "wont": "won't", "isnt": "isn't",
         "wasnt": "wasn't", "werent": "weren't", "arent": "aren't", "havent": "haven't",
         "hasnt": "hasn't", "couldnt": "couldn't", "wouldnt": "wouldn't", "shouldnt": "shouldn't",
         "thats": "that's", "its": "it's", "youre": "you're", "weve": "we've", "theres": "there's",
         "hes": "he's", "shes": "she's", "theyre": "they're", "youve": "you've"}
# "its" is two words in one, and only one of them is chat-speak: "its going to set me back 300" is
# "it is", where "its screen" owns the screen. Folding every one handed the person their own line
# back as "your phone got it's screen replaced", so the word in front decides. The contraction
# opens a clause - "its going", "its 8 years old", "my nan got her hair done and its lovely" - and
# the possessive comes after the verb or the preposition that hands something over: got its screen,
# sold its car, changed its opening hours, on its side. Only those handing-over shapes are listed,
# so a line that is not one of them keeps the fold it had.
ITS_OWNS_AFTER = frozenset("""
    on in at to from of for with by into onto near under over behind inside outside off about
    got gets gotten get had has have having sold sell sells bought buy buys changed change changes
    lost lose loses moved move moves took take takes taken gave give gives made make makes used
    use uses keeps keep kept needs need needed left leaves
    replaced replaced fitted fixed cleaned painted washed dropped scratched licked wore worn cut put
    set parked serviced insured registered broke eaten bit hit
    """.split())


# The short forms people type rather than say, folded the same way and for the same reason. The
# echo is the bot's own sentence, so it comes back in whole words: "your drum kit is 9 yrs old n
# it's loud" hands the person their own typing back, where a friend says "nine years old and the
# drum is loud". Every entry has one reading in an everyday line, so nothing has to be guessed.
SHORT = {"yrs": "years", "yr": "year", "mth": "month", "mths": "months", "wk": "week",
         "wks": "weeks", "u": "you", "ur": "your", "r": "are", "n": "and",
         "tho": "though", "coz": "because", "cuz": "because", "b4": "before",
         "abt": "about", "tmrw": "tomorrow", "2moro": "tomorrow", "nite": "night",
         "pls": "please", "thx": "thanks", "luv": "love", "ya": "you", "yer": "your",
         "goin": "going", "doin": "doing", "havin": "having", "nuthin": "nothing",
         "somthing": "something", "w": "with", "2": "two",
         "gonna": "going to", "wanna": "want to"}
# "yer" is two words in one: "yer coat" owns the coat, and "yer i tried that" opens with a yes.
# The word after it decides, and only a pronoun or the start of a sentence can make it a yes, so
# the echo no longer hands "Your you tried that" back to someone (gentle-chair, #conversation).
YES_AFTER = frozenset("""i im ive id ill it its that thats the we they you he she my our
    no yes dont didnt doesnt cant could is was there here what how why when where who ok okay
    just so but and can do does did nah yep yeah.""".split())
# How much of what they said can come back: two clauses, and never more than this many letters.
CLAUSES = 2
MOST = 90


def _repaired(clean, memory):
    """The line with the words that were wrong repaired, for the guards that match English.

    `clean` stays exactly as typed, because that is what the echo says back to the person -
    repeating "kiling" at somebody who can spell it is the cold part of "Got it". But a symptom,
    a fault and bad news are matched on the words of English, so a slip hides them: "my back is
    kiling me" is a body that hurts, not a fact to file away. The repaired line is the engine's
    own reading (`understood["plain"]`), and only when that reading is of this line.
    """
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if not isinstance(understood, dict):
        return clean
    if understood.get("clean") != clean.lower():
        return clean  # a reading of some other line: never decide on it
    return understood.get("plain") or clean


# The frames a correction is said back in, with the unit of the line before it: "four" after
# "three times a week" is "Four times a week, then."
CORRECTED_WITH_UNIT = (
    "{Value} {unit}, then.",
    "Got it \u2014 {value} {unit}.",
    "{Value} {unit}, got it.",
)

# The same frames for a value that already carries its own unit: "the run is 5 km" then "make it
# 10 km" was "10 km km, then.", because the unit of the line before was put on a figure that had
# been said with a unit of its own. A figure that measures itself needs nothing added to it.
CORRECTED_ALONE = (
    "{Value}, then.",
    "Got it \u2014 {value}.",
    "{Value}, got it.",
)
# The unit words a value can carry at its end, and the short forms a figure can be glued to ("10km",
# "5k", "250ml"). A value ending in one of these measures itself.
# "times", "per", "every" and "a" are left out on purpose: they start a measure rather than being
# one, so "i do yoga twice a week" then "change it to three times" still needs the "a week" of the
# line before it and answers "Three times a week, got it."
# "day" and "days" belong here and were the one pair missing: "the course runs 3 days" then
# "actually make it 4 days" answered "4 days days, got it." on main `c4eceacd`, while "6 weeks",
# "6 nights" and "3 hours" were all right, because every other unit the store reads was in the
# list. "ft", "meter(s)" and "yard(s)" were missing too. The set is not written by hand here any
# more: the test beside this module fails if a unit in `A_MEASURE` - the table that says what each
# unit measures - is missing from it, so the next unit added is read the same day it is added.
VALUE_UNIT_WORDS = frozenset("""km k mile miles kilo kilos kg kgs g gram grams stone stones lb
    lbs foot feet ft inch inches cm m metre metres meter meters yard yards
    liter litre liters litres ml pint pints hour hours
    hr hrs minute minutes min mins day days week weeks wk month months year years time
    pound pounds quid dollar dollars euro euros
    morning evening night weekend cup cups spoon spoons egg eggs""".split())
VALUE_UNIT_GLUED = re.compile(r"^\d[\d,]*(?:\.\d+)?([a-z]{1,5})$", re.I)
# What each unit word measures. The unit of the line before is only said again when it measures
# something else: "5 km" then "10 miles" is still a distance, so "10 miles, then." and never "10
# miles km, then.", while "5k every morning" then "10k" keeps "every morning" because a distance
# and a routine are two different measures of the same line.
A_MEASURE = {
    "km": "distance", "k": "distance", "mile": "distance", "miles": "distance",
    "m": "distance", "metre": "distance", "metres": "distance", "meter": "distance",
    "meters": "distance", "foot": "distance", "feet": "distance", "ft": "distance",
    "inch": "distance", "inches": "distance", "cm": "distance", "yard": "distance",
    "yards": "distance",
    "kilo": "weight", "kilos": "weight", "kg": "weight", "kgs": "weight", "g": "weight",
    "gram": "weight", "grams": "weight", "stone": "weight", "stones": "weight",
    "lb": "weight", "lbs": "weight", "pound": "money", "pounds": "money",
    "quid": "money", "dollar": "money", "dollars": "money", "euro": "money",
    "euros": "money",
    "hour": "time", "hours": "time", "hr": "time", "hrs": "time", "minute": "time",
    "minutes": "time", "min": "time", "mins": "time", "week": "time", "weeks": "time",
    "wk": "time", "month": "time", "months": "time", "year": "time", "years": "time",
    "day": "time", "days": "time", "morning": "time", "evening": "time",
    "night": "time", "weekend": "time", "time": "time", "times": "time", "per": "time",
    "a": "time", "an": "time", "every": "time",
    "litre": "volume", "litres": "volume", "liter": "volume", "liters": "volume",
    "ml": "volume", "pint": "volume", "pints": "volume", "cup": "volume",
    "cups": "volume", "spoon": "volume", "spoons": "volume",
    "egg": "count", "eggs": "count",
}


# A frequency said as a single word is a whole measure on its own: "three times a week" then
# "sorry, twice" is "Twice, got it." and never "Twice times a week". "three times" is not one -
# "times" starts a measure - so that shape still takes the "a week" of the line before.
WHOLE_FREQUENCY = frozenset("""once twice thrice daily nightly weekly fortnightly monthly
    quarterly yearly annually hourly""".split())


def _the_values_measures(value):
    """The kinds of measure the value is already said in: "10 km" -> {"distance"}.

    A unit word anywhere in the value counts, not only the last one, because "4 miles each way"
    carries its miles in the middle and appending "miles" to it said the unit twice. "three times"
    names none: "times" starts a measure rather than being one (see VALUE_UNIT_WORDS), so the
    "a week" of the line before is still needed to finish it. "twice" does name one, and so does
    "daily": a frequency said in one word needs nothing put after it.
    """
    found = set()
    for word in str(value or "").split():
        if word.strip(".,!?;:'\u2019").lower() in WHOLE_FREQUENCY:
            found.add("time")
        word = word.strip(".,!?;:'\u2019").lower()
        glued = VALUE_UNIT_GLUED.match(word)
        if glued:
            word = glued.group(1).lower()
        if word in VALUE_UNIT_WORDS:
            found.add(A_MEASURE.get(word, word))
    return found


def _the_units_measure(unit):
    """The kinds of measure the unit of the line before names: "every morning" -> {"time"}."""
    found = set()
    for word in str(unit or "").split():
        measure = A_MEASURE.get(word.strip(".,!?;:'\u2019").lower())
        if measure:
            found.add(measure)
    return found


def _the_unit_is_said_twice(value, unit):
    """Whether saying the line's unit after this value would measure the same thing twice.

    "5 km" then "10 km" (or "10km", or "10 miles", or "4 miles each way"): the line before
    measures a distance and so does the new figure, so its unit on the end is a second measure of
    the same thing ("10 km km, then."). "5k every morning" then "10k" is different - a distance
    and a routine - and the routine still belongs to the line, which is why "Got it - 10k every
    morning." stays right there.
    """
    here = _the_values_measures(value)
    there = _the_units_measure(unit)
    if here and there:
        return bool(here & there)
    return False


# The words people put in front of a figure they are taking back, and the words they put after it.
# A correction with no verb is a frame around a figure - "sorry 1150, i got it wrong", "1150 sorry",
# "hang on, 1150", "no its 1150", "1150, not 1200", "sorry, i got it wrong, 1150" - so the frame is
# peeled off both ends and what is left has to be a figure. One reader for all of them: on main the
# shapes with no "make it" in them were answered as news ("What was it like?") or with a stall
# ("I'm listening - say more if it helps."), one line after the person had put their figure right.
PUT_RIGHT_LEAD = (
    ("i", "got", "it", "wrong"), ("got", "it", "wrong"), ("i", "made", "a", "mistake"),
    ("i", "was", "wrong"), ("my", "mistake"), ("silly", "me"), ("i", "mean"), ("i", "meant"),
    ("hang", "on"), ("hold", "on"), ("correction",), ("actually",), ("sorry",), ("wait",),
    ("nope",), ("nah",), ("no",), ("its",), ("it's"),
    # "and", "so", "oh", "well" and "ok" are not openers here on their own: "i walk 5 km" then
    # "and 40 minutes" is a second measure, not a figure taken back.

)
PUT_RIGHT_TAIL = (
    ("i", "got", "it", "wrong"), ("got", "it", "wrong"), ("i", "made", "a", "mistake"),
    ("i", "was", "wrong"), ("my", "mistake"), ("silly", "me"), ("i", "mean"), ("i", "think"),
    ("thanks",), ("sorry",), ("actually",), ("then",), ("right",), ("though",),
)


def _without_a_frame(words, phrases, back=False):
    """The words left when a frame phrase is taken off one end, and whether one was taken."""
    words = list(words)
    took = False
    while words:
        for phrase in phrases:
            end = words[-len(phrase):] if back else words[:len(phrase)]
            said = tuple(word.lower().strip(".,!?;:'\u2019") for word in end)
            if said == phrase:
                words = words[:-len(phrase)] if back else words[len(phrase):]
                took = True
                break
        else:
            break
    return words, took


def _without_a_not(words):
    """The words with a trailing "not <figure>" taken off, which is the figure being taken back."""
    if len(words) >= 3 and words[-2].lower().strip(".,!?") == "not" \
            and re.search(r"\d", words[-1]):
        return words[:-2], True
    return list(words), False


def _the_bare_value(clean):
    """The figure a correction names when it has no verb in it, or "" when it is not one.

    The frame has to be there - a figure on its own ("1150") answers a question as often as it
    corrects a line - and the figure is what is left between the frame in front and the one
    behind. "1150, not 1200" keeps 1150: the figure after "not" is the one being taken back.
    """
    words = [word for word in re.split(r"[\s,]+", (clean or "").strip(" .!?")) if word]
    if not words:
        return ""
    words, led = _without_a_frame(words, PUT_RIGHT_LEAD)
    words, _ = _without_a_not(words)
    words, tailed = _without_a_frame(words, PUT_RIGHT_TAIL, back=True)
    if not (led or tailed):
        return ""
    if not words or len(words) > 4:
        return ""
    return " ".join(words).strip(" .,!?")


def value_put_right(clean, memory):
    """The correction said back, or "" when the line is not one that only puts a value right.

    Two things have to hold. The line has to be the frame and a value and nothing else ("make it
    four", "change that to 10k"): "my boiler is broken" then "make it stop", and "a new sofa"
    then "make it bigger", are the rest of a sentence and stay with the modules that read it.
    And the line before has to measure something ("three *times a week*", "5k *every morning*"),
    because a figure said back with no unit is the bot claiming a value it does not hold — which
    is the one thing the store's correction refuses (see FalseFactTest in tests/test_memory.py).
    """
    match = MAKE_A_VALUE.match(clean or "")
    bare = ""
    if not match:
        bare = _the_bare_value(clean or "")
        if not bare:
            return ""
    if not _the_line_before(memory):
        return ""  # nothing said before it, so there is no value to put right
    value = " ".join((match.group("value") if match else bare).split()).strip(" .")
    if not value or len(value.split()) > 4:
        return ""
    words = [word.lower().strip(".,!?'\u2019") for word in value.split()]
    if bare:
        # A correction with no verb has to be a figure or a frequency said plainly: a bare word
        # like a month or a weekday is the rest of a sentence ("my trip is 3 days in june" then
        # "sorry, june" is not "June days in june, got it.").
        if not (re.search(r"\d", value)
                or all(word in VALUE_WORDS or word in WHOLE_FREQUENCY for word in words)):
            return ""
    elif not (re.search(r"\d", value) or all(word in VALUE_WORDS or word in DAYS
                                              or word in MONTHS or word in WHOLE_FREQUENCY
                                              for word in words)):
        return ""
    unit = _the_unit_before(memory)
    if not unit:
        # Nothing in the line before is measured in anything, so the new figure replaces no value
        # the bot can name: "im tired" then "make that 800" is not a correction of anything, and a
        # figure said back would be the bot claiming it holds a number it does not.
        return ""
    unit = _without_a_unit_already_in_the_value(value, unit)
    if _the_unit_is_said_twice(value, unit):
        # The unit of the line before would be a second measure of the same thing, so the value
        # is said back as it was given: "10 km, then."
        return pick(CORRECTED_ALONE, memory, seed_text=clean).format(
            value=value, Value=value[:1].upper() + value[1:])
    return pick(CORRECTED_WITH_UNIT, memory, seed_text=clean).format(
        value=value, Value=value[:1].upper() + value[1:], unit=unit)


def _without_a_unit_already_in_the_value(value, unit):
    """The unit of the line before with the word the value already ends in taken off.

    "i swim 3 times a week" then "sorry 5 times" is "5 times a week" - the value carries the
    "times" and the line carries the "a week" - and it was "5 times times a week, then." because
    the unit of the line before is read from after its figure, "times a week", and put on a value
    that had just said "times" itself.
    """
    unit_words = str(unit or "").split()
    value_words = str(value or "").split()
    if len(unit_words) < 2 or not value_words:
        return unit
    last = value_words[-1].strip(".,!?;:'\u2019").lower()
    if last == unit_words[0].strip(".,!?;:'\u2019").lower():
        return " ".join(unit_words[1:])
    return unit


def _the_line_before(memory):
    """The line the person said just before, or "" when there is none."""
    if not isinstance(memory, dict):
        return ""
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return ""
    last = turns[-1]
    said = last.get("user") if isinstance(last, dict) else None
    return said if isinstance(said, str) else ""


def _the_unit_before(memory):
    """The words the line before measures its figure in: "three times a week" -> "times a week".

    "i run 5k every morning" -> "every morning". Nothing when that line has no figure at all
    ("im tired") or when its figure is followed by nothing that measures it ("i finish at 5",
    "my appointment is on the 3rd"): a new figure with no unit of the old one is a number the
    bot would be making up a home for.
    """
    said = _the_line_before(memory)
    if not said.strip():
        return ""
    words = [word.strip(".,!?;:") for word in said.split() if word.strip(".,!?;:")]
    for index, word in enumerate(words[:-1]):
        figure = word.lower()
        if figure in ("a", "an", "the"):
            continue  # "a month" is the unit of "twice a month", not the figure
        if not (re.search(r"\d", figure) or figure in VALUE_WORDS or figure in DAYS
                or figure in MONTHS):
            continue
        tail = []
        for following in words[index + 1:index + 4]:
            if following.lower() in UNITS_AFTER and len(tail) < 3:
                tail.append(following.lower())
                continue
            break
        if tail:
            return " ".join(tail)
    return ""


# An animal given to a new home is a loss, and it was said back as a fact: "we had to give our
# dog away" got "Noted: you had to give your dog away.", the coldest line there is for somebody
# who has just given up an animal they loved. The store hears it either way - the animal comes
# off the list, and "we had to give the dog away" is not a claim that there is no dog in the
# house - so the echo is the one place to say what a friend says.
#
# The reading needs the gesture and the animal both: "i had to give the dog a pill" is a dog
# being looked after, and "we gave up bread" is an animal in none of it. The line has to say
# the giving up happened ("had to", "gave ... away") - the plan ("i need to rehome my dog")
# and the question ("how do i rehome my dog") are the rehoming entry's, and they are kept out
# by the statement guard and by needing the past or the compulsion.
GIVEN_AWAY = re.compile(
    r"\b(?:had|have|has|got)\s+to\s+give\b[^.!?]{0,30}?\b(?:away|up|back|to)\b|"
    r"\b(?:had|have|has|got)\s+to\s+(?:rehome|surrender|get rid of)\b|"
    r"\b(?:had|have|has|got)\s+to\s+let\b[^.!?]{0,20}?\b(?:go|away)\b|"
    r"\b(?:gave|given|giving)\b[^.!?]{0,30}?\b(?:away|up)\b|"
    r"\b(?:couldn'?t|could not|can'?t|cannot)\s+keep\b|"
    r"\bsurrendered\b|\bhanded (?:him|her|them|it) (?:over|back)\b", re.I)
GIVEN_ANIMAL = re.compile(
    r"\b(dogs?|puppy|pup|puppies|cats?|kitten|kittens|rabbits?|hamsters?|guinea pigs?|parrots?|"
    r"budgie|birds?|horses?|pony|snakes?|lizards?|rats?|ferrets?|tortoises?|pets?)\b", re.I)
# Somebody else's animal: "my mum had to rehome her dog" is a hard thing for the mum, and the
# line about a friend's week is not the user's loss to console.
NOT_THEIRS = re.compile(
    r"\b(?:my|his|her|their|our)\s+(?:mum|mom|mam|dad|father|mother|sister|brother|son|"
    r"daughter|nan|gran|granny|aunt|uncle|friend|mate|neighbou?r|colleague|boss|partner|wife|"
    r"husband|cousin)\b", re.I)
GIVEN_AWAY_REPLIES = (
    "That's a hard thing to do, and I doubt giving up a {animal} was an easy call.",
    "Giving up a {animal} is usually a last resort, so I doubt you came to it lightly.",
    "I'm sorry \u2014 giving up a {animal} is one of the harder decisions there is.",
    "That can't have been easy. You did right by the {animal}, whatever the reasons.",
)


def _the_animal_given_away(text, memory=None):
    """The animal the line hands over, as a word to put in a sentence ("dog"), or "".

    The line usually names the kind ("our dog", "the cats"), and when it names only the
    animal - "we gave max away last week" - the record the store has just taken off the list is
    where the kind is. Without either there is nothing to say the warm line about.
    """
    found = GIVEN_ANIMAL.search(text)
    if found:
        kind = found.group(1).lower()
        return kind[:-1] if kind.endswith("s") and not kind.endswith("ss") else kind
    gone = memory.get("denial") if isinstance(memory, dict) else None
    records = gone.get("pets") if isinstance(gone, dict) else None
    said = text.lower()
    for record in records or []:
        if not isinstance(record, dict):
            continue
        name = str(record.get("name") or "").strip().lower()
        if name and re.search(r"\b" + re.escape(name) + r"\b", said):
            kind = str(record.get("animal") or "pet").lower()
            return kind[:-1] if kind.endswith("s") and not kind.endswith("ss") else kind
    return ""


def pet_given_away(text, memory=None):
    """The warm line for an animal given to a new home, or None when this is another line.

    bot/modules/memory_store.py asks this on the turn it takes the animal off the list, and
    `reply` asks it for a line the store had no record of: either way the person gets the same
    kind of answer, and never "Right \u2014 no dog, then." for a dog they loved.
    """
    if not isinstance(text, str):
        return None
    clean = " ".join(text.split())
    if not clean or not GIVEN_AWAY.search(clean):
        return None
    if NOT_THEIRS.search(clean) and not re.match(r"\s*(?:i|we)\b", clean, re.I):
        return None  # somebody else's pet, told as their news rather than the user's
    kind = _the_animal_given_away(clean, memory)
    if not kind:
        return None
    return pick(GIVEN_AWAY_REPLIES, memory if isinstance(memory, dict) else {},
                seed_text=clean).format(animal=kind)


# A line that offers a chat and says nothing else - "just wanted to chat really", "thought id say
# hello" - has no fact to file and no detail to say back. Read by the fact frames it was answered
# with the sentence itself ("Just wanted to chat really \u2014 noted."), which is the one reply a
# person who came to talk cannot use, and after a hard day it left them a filing receipt. A friend
# says they are here and asks what is on their mind, and the pool is short so it never turns into
# a question about the question.
OFFERS_A_CHAT = re.compile(
    r"^\W*(?:ok|okay|so|well|hi|hey|and)?[,\s]*"
    r"(?:i\s+|we\s+)?(?:just|only|really|actually\s)?\s*"
    r"(?:wanted|want|fancied|feel like|felt like)\s+"
    r"(?:a\s+|to\s+|some\s+)?(?:chat|talk|natter|chinwag)\b"
    r"(?:\s+(?:really|honestly|today|tonight|for a bit|for a while|a bit|with someone|"
    r"to someone|to somebody|with somebody|i suppose|i guess|thats all|that'?s all|"
    r"more than anything|you know|i think|if thats ok|if that'?s ok))*"
    r"[\s.!?]*$"
    r"|^\W*(?:ok|okay|so|well)?[,\s]*(?:i\s+)?(?:just\s+)?(?:wanted|want|fancied)\s+"
    r"(?:someone|somebody)\s+to\s+(?:talk|chat)\s+(?:to|with)?"
    r"(?:\s+(?:really|honestly|today|tonight|a bit|i suppose|i guess))*[\s.!?]*$"
    r"|^\W*(?:i\s+)?thought\s+(?:i'?d|i would)\s+(?:say|pop)\s+(?:hi|hello|in)\b"
    r"(?:\s+(?:really|honestly|today|tonight|i suppose|before i go))*[\s.!?]*$",
    re.I)
CHAT_OFFER_REPLY = (
    "Anytime \u2014 what's on your mind?",
    "I'm here. Anything you want to talk about, big or small?",
    "Good, I've got time. What's been going on?",
    "Any time. What shall we talk about?",
    "Nice \u2014 I'm all yours. What's up?",
)


def _offers_a_chat(clean, memory=None):
    """A short warm yes to a line that came to talk, never the line said back.

    A chat offered in the days after bad news is not a fresh start: "my dad died last month" then
    "just wanted to chat really" is the same grief going on, and the line that said it is still on
    the screen, so that turn keeps the reply it had.
    """
    if not OFFERS_A_CHAT.match(clean or ""):
        return None
    for turn in (memory.get("turns") or [])[-3:] if isinstance(memory, dict) else []:
        said = str((turn or {}).get("user") or "").lower() if isinstance(turn, dict) else ""
        if said and (reads_as_bad_news(said) or loss.reads_as_loss(said)):
            return None
    return pick(CHAT_OFFER_REPLY, memory)


# A date on its own is the date of the thing the chat is already on: "im going to a wedding" and
# then "its in july" were answered "I'm listening - say more if it helps", a line that fits any
# message in the language. The line names no doing, so `_a_day_coming` passes it by - there is no
# trip or appointment in it, only a month - and the thing it is the month *of* is in the store
# already. A friend reads it as the plan's own date and says what the time means for that plan: "A
# july wedding - plenty of time to sort the rest."
A_DATE_ALONE = re.compile(
    r"^(?:(?:ok|okay|so|and|well|oh|hmm|yeah|yes|no)\s*[,\s]\s*)*"
    r"(?:(?:it'?s|its|it is|that'?s|thats|that is|we'?re|we are|the date is|the day is)"
    r"\s+)?(?:in|on|for|by|at the end of|early|late)?\s*"
    r"(?P<when>january|february|march|april|may|june|july|august|september|october|november"
    r"|december|next\s+week|next\s+month|next\s+year|this\s+weekend|the\s+weekend"
    r"|tomorrow|tonight|the\s+\d{1,2}(?:st|nd|rd|th)|\d{1,2}(?:st|nd|rd|th)"
    r"|monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r"\s*(?:i think|i reckon|i believe|this year|next year|at the latest|i'?m sure)?"
    r"\s*[.!]*$", re.I)
# The months and the weekdays, which take an article and the plan's own word - "a july wedding",
# "a saturday wedding". "a next week wedding" is not English, so the shorter days keep the day
# words alone.
A_MONTH_ALONE = re.compile(
    r"^(?:january|february|march|april|may|june|july|august|september|october|november"
    r"|december|monday|tuesday|wednesday|thursday|friday|saturday|sunday)$", re.I)
A_WEEKDAY = re.compile(r"^(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)$", re.I)
# What the time means for a plan that is in the diary: the same two things every plan wants said
# about it, and neither of them names a month of the year or a kind of day.
A_DATE_ON_A_PLAN = (
    "{Thing} \u2014 plenty of time to sort the rest.",
    "{Thing}. That's something to look forward to.",
    "{Thing} \u2014 what's left to sort?",
    "{Thing}. Good to have the date down.",
)
A_DAY_ON_A_PLAN = (
    "{Thing} \u2014 that is soon, then.",
    "{Thing}. Not long now.",
    "{Thing} \u2014 that comes round quickly.",
)
# A plan the person is not looking forward to cannot be answered with "that's something to look
# forward to": "im nervous about a job interview" then "its on friday" would agree with the surface
# of the line and contradict the person in the same breath (the same rule the occasion pools keep
# under DREADED_OCCASION).
A_WORRIED_ABOUT_IT = re.compile(
    r"\b(?:nervous|worried|worry|worrying|dreading|dread|scared|afraid|anxious|panic|hate|"
    r"stress(?:ed|ful)?|not looking forward|can'?t face)\b", re.I)
A_DATE_ON_A_HARD_PLAN = (
    "{Thing} \u2014 no wonder it is on your mind.",
    "{Thing}. The run-up is usually worse than the day itself.",
    "{Thing} \u2014 that is a lot to have coming.",
)
A_DAY_ON_A_HARD_PLAN = (
    "{Thing} \u2014 no wonder it is on your mind.",
    "{Thing}. The day itself is usually easier than the wait.",
)

# A birthday said as its number: "my grandads 80th is coming up" names no occasion word, and the
# date it gets ("its in november") was met with "Thanks for telling me".
A_MILESTONE = re.compile(r"\b(?:\d{1,3})(?:st|nd|rd|th)\b", re.I)


def _the_plan_a_date_belongs_to(text):
    """The word for the plan a bare date is the date of, and its kind, or ("", "") for none.

    Only the kinds of plan a date belongs to: an occasion, a birthday said as its number, an
    appointment in the diary, or a trip somewhere. The kind is what the phrase is built with - "a
    july wedding" is an occasion, "the dentist on tuesday" is an appointment.
    """
    said = " ".join(str(text or "").lower().split())
    if not said:
        return "", ""
    words = re.findall(r"[a-z']+", said)
    occasion = next((word for word in words if word in OCCASIONS), "")
    if occasion:
        return occasion, "occasion"
    if A_MILESTONE.search(said) and re.search(r"\b(?:my|our)\b", said):
        return "birthday", "occasion"
    diary = DIARY_THING.search(said)
    if diary:
        return diary.group(0).lower(), "diary"
    # A trip with the date left out: "we're going to spain" and then "its in july". The same
    # guards as `reads_as_a_trip`, which cannot see this one because it asks for the date.
    if (TRIP_VERB.search(said) and DESTINATION.search(said) and not OBLIGED.search(said)
            and not set(words) & PAST_PLAN):
        head = DESTINATION.search(said).group(1).lower()
        if head not in NOT_A_TRIP and head not in THING_BEFORE:
            return "holiday", "trip"
    return "", ""


def _a_date_on_the_thing_in_hand(clean, memory):
    """The plan's own date, said back as what the time means for it, or None.

    Only when the chat is already on a thing a date can belong to - an occasion or something in
    the diary - and the line is that date and nothing else. Anything else keeps its own reply.
    """
    said = " ".join(str(clean or "").lower().split())
    found = A_DATE_ALONE.match(said)
    if not found:
        return None
    record = topics.current(memory)
    text = " ".join(str((record or {}).get("text") or "").lower().split())
    if not text:
        return None
    when = " ".join(found.group("when").lower().split())
    if not when or when in re.findall(r"[a-z']+", text):
        # The date is already in the record's own words - "the wedding in july" then "its in
        # july" - so the line said nothing new and keeps the reply it has. The record's merged
        # words are not used for this: the store has already added this line's month to them, so
        # every date would read as a repeat.
        return None
    plan, kind = _the_plan_a_date_belongs_to(text)
    if not plan:
        return None
    thing = when[:1].upper() + when[1:]
    # Whether the plan is one to look forward to is the person's own, and the chat says it: "im
    # nervous about a job interview" then "its on friday" cannot be told the day is something to
    # look forward to.
    said_so_far = " ".join(
        [text] + [str(turn.get("user") or "").lower()
                  for turn in (memory.get("turns") or [])[-4:] if isinstance(turn, dict)])
    worried = bool(A_WORRIED_ABOUT_IT.search(said_so_far))
    a_day = A_MONTH_ALONE.match(when)
    if kind == "diary":
        # "the dentist on tuesday", "the scan in july": an appointment takes "the", and a weekday
        # takes "on". "a tuesday dentist" is not English.
        if A_WEEKDAY.match(when):
            made = "the " + plan + " on " + thing
        elif a_day:
            made = "the " + plan + " in " + thing
        else:
            made = "the " + plan + " " + thing
    elif a_day:
        # "a july wedding", "a saturday wedding".
        article = "an " if thing[0].lower() in "aeiou" else "a "
        made = article + thing + " " + plan
    elif A_WEEKDAY.match(when) or when in ("tomorrow", "tonight"):
        made = "the " + plan + " " + thing.lower()
    else:
        # "next week", "the 14th": the plan's own name and the time, in that order.
        made = "the " + plan + " " + thing.lower()
    made = made[:1].upper() + made[1:]
    if a_day:
        pool = A_DATE_ON_A_HARD_PLAN if worried else A_DATE_ON_A_PLAN
        return pick(pool, memory).format(Thing=made)
    pool = A_DAY_ON_A_HARD_PLAN if worried else A_DAY_ON_A_PLAN
    return pick(pool, memory).format(Thing=made)


def _after_the_hello(clean):
    """What the line says after the hello, or "" when the hello is all of it."""
    match = GREETING.match(clean)
    if not match:
        return ""
    return clean[match.end():].lstrip(" ,.!-:;")


def reply(text, memory):
    """A short echo of the fact they just gave, or None when this is not that kind of line."""
    if not isinstance(text, str):
        return None
    clean = " ".join(text.split())
    if not clean or "?" in clean:
        return None
    dated = _a_date_on_the_thing_in_hand(clean, memory)
    if dated:
        # "its in july" after "im going to a wedding". It comes first because nothing below asks
        # what the line is the date *of*, and the neutral line at the end of the chain fits any
        # message at all.
        return dated
    # A clock time somebody has to be somewhere by is not a fact to file: "i have a train at 7"
    # was answered "Noted: you have a train at 7.", which is the coldest version of the one thing
    # in the line worth working back from, and the composer has the pool that does that
    # (tiny-bluebell, #routing 81689). The store still keeps the line; only the saying back
    # stands aside.
    from ..compose import fallback as compose_fallback
    if compose_fallback._the_morning_has_a_clock(clean.lower()):
        return None
    # A line that takes the last thing back is not a fact to file: "forget about the whole thing"
    # was answered "Forget about the whole thing — noted.", which is the coldest line in
    # STYLE.md spent on a withdrawal - the person has just said they are done with it, and the
    # echo hands it back to them as news. The pool that answers a dismissal is the composer's
    # (bot/compose/fallback_data.py, NEVER_MIND), so the saying back stands aside and the line
    # reaches it.
    from ..compose.fallback_data import A_DISMISSAL
    if A_DISMISSAL.match(clean):
        return None
    # "i told you my interview is in june" is the fact said again with a frame around it, and the
    # store files the fact without the frame, so the note drops it too: "Noted: your interview is
    # in june.", never "Noted: you told me your interview is in june." A report of something that
    # is not a fact ("i said thanks", "i told you about the boiler") keeps its own words.
    reported = facts._reported_clause(clean)
    if reported and facts.extract(reported):
        clean = " ".join(reported.split())
        text = clean
    # Advice somebody else gave them is not a fact to file: "my mum says i should go to the
    # doctor" was said back as "Noted: your mum says you should go to the doctor", which is the
    # coldest line in STYLE.md for what is a nudge from home. Nothing in the line has happened
    # yet, so there is no fact in it to keep - the plan is the line, and bot/compose/fallback.py
    # answers it (see A_SUGGESTED there). Read off the understanding engine, not off the words,
    # so a report of something done keeps its note ("my mum says i got the job").
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if isinstance(understood, dict) and understood.get("suggestion"):
        return None
    # An errand asked of the bot is not a fact of theirs to say back. "we are going to lanzarote in
    # may" then "look up the flights for me" was answered "Got it — look up the flights for you.",
    # which is a receipt for something the bot has just said it cannot do - the one reply worse
    # than the honest limit. The line is read by bot/understanding/__init__.py as an errand, so the
    # store's own saying back stands aside and the composer's limit keeps the turn.
    if isinstance(understood, dict) and understood.get("errand"):
        return None
    read = _repaired(clean, memory)
    # The name in "my name is Priya" is a capital, and a capital is part of the reading, so these
    # three look at the line as typed.
    # A hello in front of a fact is the hello and the fact, and standing down on the greeting
    # lost the fact: "hi, im vegetarian" kept the diet and then answered "Hey! What would you
    # like to talk about?". The hello is taken off when the line goes on after it, so what is
    # said back is the rest of it. A line that is only a hello has nothing to say back, and
    # neither has one that goes on to give their name ("hi, i'm Sam" is the chat module's) or
    # to say what they are after ("hi, im looking for a plumber" is asking for a plumber).
    # `facts.about_themselves` is that reading, and the kind reader asks the same question of
    # the same line (`bot/understanding/kinds.py`, `greeting_only`).
    if GREETING.search(clean):
        rest = _after_the_hello(clean)
        if not rest or not facts.about_themselves(rest):
            return None
        clean = text = rest
        read = _repaired(clean, memory)
    elif MEET_GREET.search(clean) or SELF_INTRO.search(clean):
        return None
    had = the_job_they_had(clean, memory)
    if had:
        # "i was a teaching assistant before the kids": the job they had, not a day to give a
        # verdict on (see PAST_JOB). Asked here, before the day and echo paths, so the line
        # cannot be read as an event that has happened.
        return had
    # A line that names a person of theirs and nothing else is a person to ask about however it is
    # worded: "what about the little one" is the same line as "and the little one", and it was read
    # as an ask about a thing and handed a search hedge. The named-alone pattern is anchored to the
    # whole line, so a real question about a person ("what about my sons school") never gets here.
    alone = a_person_named_alone(clean, memory)
    if alone:
        return alone
    if WANTS_ANSWER.search(read) and not facts.RELATION_WHOS_AGE.search(read):
        # "idk what to get my dad" is asking, not telling. The "who" clause is the one "whos"
        # that is not an ask: "my daughter whos 9" says the same thing as "my daughter is 9",
        # and it was left with the neutral "I'm listening" while the plain wording was said
        # back. The pattern is the relation's own, so "whos coming to dinner" is still a
        # question.
        return None
    if _a_result_is_on_the_table(clean):
        # "i got the results" is a person with news, and "im not sure i got the place" is a
        # person waiting: the reply that fits asks for the rest, and bot/compose/fallback.py
        # has both ("What did they say?", "When do you find out?"). Saying the line back -
        # "Noted: you got the results." - tells them nothing they did not just say.
        return None
    limit = _a_limit_on_the_plan(read, memory)
    if limit:
        return limit
    second = a_second_person(clean, memory)
    if second:
        # "and my dads" after a birthday is the same fact for somebody new, and the date is what
        # they left out: asking for it beats "Got it - your dads."
        return second
    corrected = value_put_right(clean, memory)
    if corrected:
        # "make it four" after the gym line: the value goes back up with the unit of the line it
        # corrects, and never as a search hedge (see MAKE_A_VALUE).
        return corrected
    aged = the_old_one_aged(clean, memory)
    if aged:
        # "i need a new washing machine" / "the old one is 12 years old": the number is the only
        # new fact in the line, and a friend says what it means for the purchase (see
        # THE_OLD_ONE). The reading is only for the thing in hand - a thing named on its own ("my
        # boiler is 8 years old") has an entry of its own and keeps it.
        return aged
    if not _statement(memory):
        return None
    given = pet_given_away(clean, memory)
    if given:
        # "we had to give our dog away" is not a fact to file: it is a person telling you the
        # hardest call they have had to make about an animal (see GIVEN_AWAY).
        return given
    if trouble.reads_as_trouble(read) is not None:
        # A fault to troubleshoot is bot/compose/trouble.py's turn: a thing that is not behaving
        # gets "what's it doing", and a setback nobody has explained yet gets "what happened".
        # Either way the line is not a fact to say back. `_plain` has had this guard for the lines
        # that reach its tail; this is the same guard for the fact paths, where a complaint about
        # how something wears on them was filed as "Noted: your job is killing you."
        return None
    limit = a_limit_reply(text, memory)
    if limit is not None:
        return limit
    if _no_subject(clean, memory):
        return None  # "were shattered after the move - noted" is not a sentence anybody says
    if reads_as_bad_news(read.lower()) or _a_loss(text, memory, read):
        return None  # "our cat was put down yesterday" is not a fact to say back
    if _bad_news_just_before(read, memory):
        # "she took the kids to her mums" after "im thinking of leaving my husband".
        return pick(THE_STORY_GOES_ON, memory, read)
    if reads_like_a_symptom(read.lower()):
        return None  # "i've got a sore throat - noted" is the coldest reply there is
    if reads_as_good_news(read.lower()):
        return None  # "your sister had her baby yesterday - noted" is a filing cabinet
    if reads_as_settled(clean.lower()) and worry_on_the_table(memory):
        return None  # "hes ok now" after a bad cough is news, not a detail to say back
    if DEATH_WORDS.search(read):
        return None
    if WOULD_HAVE_BEEN.search(read) or BODY.search(read) or BLEED.search(read):
        return None  # a birthday nobody reached, or a body that hurts, is not a fact
    if A_FEELING.search(clean):
        return None  # "i want to cry" is not a plan, however the fact store reads it
    if _said_to_the_bot(clean):
        return None  # "you're on form today" is said to the bot, not a fact about the person
    if _a_bare_state(clean.lower()):
        return None  # "you're bunged up - noted" says nothing about being bunged up
    if GOOD_MOOD.search(clean) and not has_news(clean):
        # "life is good", "im in a good mood": a mood is not a detail to file and say back, and
        # the stock echo ("Got it - life is good.") is a line that fits any message. A line with
        # an event in it keeps the frames, because the event is the fact.
        return None
    alone = nobody_around(clean.lower(), memory)
    if alone:
        # Read before the fact frames: "ive got no one to talk to" is not a detail, and a reply
        # that says it back is the coldest answer to it.
        return pick(alone, memory, clean)
    deadline = _a_deadline(clean, read, memory)
    if deadline:
        return deadline
    clock = _a_clock_time(clean, read, memory)
    if clock:
        return clock
    if _after_a_feeling(clean, memory):
        # The reason for the feeling they just gave: said back with the one question that
        # follows from it, whether or not there is a fact here to file.
        thing = _echo(clean)
        if thing:
            return pick(EXPLAIN_TAIL, memory, seed_text=clean).format(
                thing=thing, Thing=thing[:1].upper() + thing[1:])
    lasting = _the_length(clean, memory)
    if lasting:
        return lasting
    hours = _the_hours(clean, read, memory)
    if hours:
        return hours
    chat = _offers_a_chat(clean, memory)
    if chat:
        return chat
    job = _a_job_to_do(clean, memory)
    if job:
        return job
    found = _learned(text, memory)
    if found and _only_a_wish(found):
        # A line that only says what animal they would like is not a fact to say back and not an
        # animal of theirs to ask about: the two pools here answered "i want a labrador" with
        # "No dog, then." and then with "A labrador - how long has it been with you?", inventing
        # a dog and then agreeing to take it away. It is an animal they would like, so it is
        # named back and asked about, which is the line the composer gives a dog they want.
        wanted = "a " + _the_wished_animal(found, clean)
        return pick(WISH_FOR_AN_ANIMAL, memory, seed_text=clean).format(
            Thing=wanted[:1].upper() + wanted[1:], thing=wanted)
    if found:
        nobody = _who_the_figure_is(found, memory, clean.lower())
        if nobody:
            # A receipt says a fact was written down. "hes 9" files nothing, because there is
            # nobody in the chat for the "he" to be, so the reply asks who instead of noting it.
            return nobody
    if found and set(found) <= {"age", "height"} and not _only_the_figure(clean):
        # An age or a height is said back when it is what the line is about. "im 29" is a fact;
        # "im 29 and everyone around me is buying houses and having babies" is a person telling
        # you where they are in life, and handing the sentence back as "Noted: you're 29 and
        # everyone around you is buying houses" is the coldest reply in the deck.
        return None
    animal_wanted = _an_animal_wanted(clean)
    if animal_wanted and not _on_record(animal_wanted, memory):
        # "my daughter is 8 and wants a hamster", "the kids want a pet": the line asks what
        # having one takes, and the store used to file the want and hand the sentence back
        # ("Noted: your daughter is 8 and wants a hamster"). Read before the take-back branch
        # because a want is usually said beside something else - an age, a name, who wants it.
        return _what_a_wanted_animal_needs(animal_wanted, clean, memory)
    coming = _the_animal_coming(found) if found else ""
    if coming:
        # "we are getting a puppy next week": the store keeps it, marked `coming`, so the
        # follow-ups still have it, and the sentence said back is the plan it is.
        return pick(ANIMAL_COMING, memory, coming).format(animal=coming)
    planned = _an_animal_only_planned(found, clean, memory)
    if planned:
        # "im thinking of getting a rescue greyhound" then "actually its a whippet": the second
        # line names a dog and nothing else, so the store filed a dog of theirs and the pet tail
        # asked how long it had been with them - inventing a dog in a house that has not got one.
        # The plan is what the chat is on (it is the topic), and the correction only says which
        # one, so the thing still open is whether they have settled on it.
        said = planned if planned.split()[0] in ("a", "an") else (
            "an " + planned if planned[:1] in "aeiou" else "a " + planned)
        return pick(A_BREED_BEING_CHOSEN, memory, clean).format(
            animal=said, Animal=said[:1].upper() + said[1:])
    if found and (_an_animal_taken_back(found) or _an_animal_turned_down(found, memory)):
        # A take-back in front of an animal ("forget the dog", "not the cat", "never mind the
        # dog") reads as a pet of theirs with nothing said about having it, and saying it back -
        # "A dog \u2014 how long has it been with you?" - invents the dog they have just taken
        # away and asks how long they have had it. When there is an animal of that kind on
        # record the store has its own line ("Right \u2014 no dog, then"), so this declines and
        # lets it answer; when there is none, the line is a person saying no dog, and the reply
        # says the same thing back rather than the stock "Got it. Is there anything you'd like a
        # hand with?".
        animal = _the_taken_back_animal(found)
        if animal and not _on_record(animal, memory):
            if _an_animal_they_had_once(clean):
                # "i had a dog growing up" is a dog they had, so "No dog, then." reads as a
                # refusal of it. What a friend says is what the memory is for.
                return pick(ANIMAL_HAD_ONCE, memory, animal).format(
                    animal=animal, Animal=animal[:1].upper() + animal[1:])
            return pick(ANIMAL_TAKEN_BACK, memory, animal).format(
                animal=animal, Animal=animal[:1].upper() + animal[1:])
        return None
    remark = _a_remark_on_what_was_said(clean, memory)
    if remark:
        # "it cost a fortune", "the slugs got them": a remark on the turn before is answered, not
        # filed and handed back. The reply is also written down as one that hands the subject
        # back, because a remark does not move the conversation on: the answer either side of it
        # is still the answer on the screen (`bot/memory/topics.py::said_again`).
        _a_hand_back(remark, memory)
        return remark
    another = _another_of_what_we_said(clean, memory)
    if another:
        # "we had another one", "my wife got one too", "we had one before": the line is a pointer
        # back and names nothing itself, so saying it back ("Got it - you had another one") tells
        # the person nothing. A friend names the thing from the chat and asks about it.
        return another
    more = _adds_one_more_allergen(text, memory)
    if not more and (memory or {}).get("understood", {}).get("routine"):
        habit = _plain(clean, memory)
        if habit:
            # The line reports a routine, and a thing inside it is what they do it to: "i walk
            # the dog every day", "i feed the cats at six". The pet tail asks how long the animal
            # has been with them - a question about an animal they told you nothing new about -
            # and the routine is the news, so the habit tail says that back instead.
            return habit
    said = None
    if not found or (not more and not _tells_it(clean, found)):
        said = _a_thing_they_have(clean, memory)
    if said:
        return _the_opening_instead(said, clean, memory) or said
    if not found or (not more and not _tells_it(clean, found)):
        # Nothing in the line to file, or a fact that cannot be said back ("my partner and i do
        # a quiz on a thursday"): a habit still gets said back, and everything else declines.
        plain = _plain(clean, memory)
        return _the_opening_instead(plain, clean, memory) or plain
    pets = found.get("pets") if isinstance(found, dict) else None
    # "my cat has kidney failure" is a line about the illness, not about having a cat: the pet
    # tail's "how long has it been with you?" asks about the wrong thing, and the vet's line
    # answers it.
    ill = not A_CHILD_IN_THE_LINE.search(clean) and reads_for_a_pet(clean.lower())
    if (pets and not more and set(found) == {"pets"} and not AS_WELL.search(clean)
            and not A_CHILD_IN_THE_LINE.search(clean) and ill):
        return None  # the vet's line answers it; this is not a line about having a pet
    if (pets and not more and set(found) == {"pets"} and not AS_WELL.search(clean)
            and not A_CHILD_IN_THE_LINE.search(clean)
            and not _nothing_added_but_the_pet(clean, pets)):
        return None  # the line says how the animal is; a question about having it is the wrong one
    if (pets and not more and set(found) == {"pets"} and not AS_WELL.search(clean)
            and not A_CHILD_IN_THE_LINE.search(clean)
            and not _a_pet_that_is_all_right(clean, pets)):
        # What they have is a pet, and the tail it deserves is the one about the pet rather than
        # the receipt it was getting: "we have two cats, milly and tom" was answered "Noted: you
        # have two cats, milly and tom". Read before the kids and the echo, because the store has
        # the animal and the name and the frames had nothing to ask about either.
        said, many = _the_pets_said(pets, clean)
        if said:
            # The thing itself, not "you have the thing": they just said they have it, and a
            # reply that opens by handing the line back is the echo this is fixing. An animal
            # the store has on its way is not one in the house yet, so the questions about
            # having it are the wrong ones: "we're getting a puppy next month" / "its a
            # labrador" was answered "A labrador. What's it like to live with?" about a dog
            # nobody has met. What a friend asks about an animal still to come is when it
            # arrives.
            if _the_pets_are_coming(pets, memory):
                pool = PET_TAIL_COMING_MANY if many else PET_TAIL_COMING
            else:
                pool = PET_TAIL_MANY if many else PET_TAIL_ONE
            return pick(pool, memory, clean).format(
                thing=said, Thing=said[:1].upper() + said[1:])
    kids = _children_with_ages(text)
    if kids:
        thing = _children_said(kids)
    elif more and list(found.get("allergies") or []) == more:
        # The line names one more thing and nothing else, so what is said back is the whole fact
        # with it in it: "Milk too" is not a sentence and "You're allergic to milk too" is.
        thing = "you're allergic to " + " and ".join(more) + " too"
    else:
        thing = _echo(clean, memory)
    if not thing:
        return None
    plan = _plan_tails(found, clean, memory)
    if plan:
        return _pick_ending(plan, memory,
                            thing=thing, Thing=thing[:1].upper() + thing[1:],
                            food=CONDITION_FOOD.get(str(found.get("condition") or "").lower(), "that"))
    frames = _frames(found, _heavy(memory), clean, memory)
    if frames is FRAMES:
        # The first line of a chat has no earlier turn for a receipt to be a detail of, so the
        # plain frames are swapped for the question a friend asks about the fact itself
        # (bot/memory/opening.py). A limit, a pet, a workplace and a plan already ask their own.
        opened = opening.the_opening(thing, clean, memory)
        if opened:
            return opened
    return _pick_ending(frames, memory,
                        thing=thing, Thing=thing[:1].upper() + thing[1:],
                        food=CONDITION_FOOD.get(str(found.get("condition") or "").lower(), "that"))

# A one-line remark on what was just said is not a fact to file, and it is not a thing to say
# back: "we redid the kitchen last year" then "it cost a fortune" was answered "Got it - it cost
# a fortune", the person's own words handed back with nothing added. With the store's echo
# silenced it fell further, to the stock nod ("Got it. Is there anything you'd like a hand
# with?"), which fits any message at all. A friend answers the remark - the money, the time, the
# better, the loss - and asks the one thing that follows from it, so the reading is the kind of
# remark and the reply is filled from nothing but the kind: no tail here can be pasted onto a
# line that is not a remark.
REMARK_BACK = re.compile(
    r"^(?:it|its|it's|that|thats|that's|they|them|he|she|the|this|those|these|everything|nothing"
    r"|none|all)\b", re.I)
REMARK_EXPENSE = re.compile(
    r"\b(?:cost|costs|costing|expensive|pricey|a fortune|a bomb|not cheap|money pit|"
    r"over budget|over the budget|cost a lot|costs a lot|adds? up)\b", re.I)
# A price already paid and a price still to pay are two different remarks. "we redid the kitchen
# last year" / "it cost a fortune" is somebody looking back at money spent, so asking whether it
# was worth it is the question a friend asks. "we are going to portugal in august" / "the flights
# are expensive" is the same words about a trip nobody has booked, where the same question ("Do
# you think it was worth it?") asks about a thing that has not happened yet and has no answer.
# What tells them apart is the plan on the table, not the remark: what was done is said in the
# past ("redid", "last year"), and what is still to be done is said as a plan ("going to",
# "in august", "next month"). Read from the topic line as well as the remark, because the
# remark itself is only the price ("it cost a fortune" says nothing about when).
REMARK_STILL_TO_COME = re.compile(
    r"\b(?:going\s+to|gonna|planning|plan\s+to|planning\s+to|thinking\s+of|want\s+to\s+"
    r"(?:go|buy|get|book|move|build|do)|hoping\s+to|about\s+to|next\s+"
    r"(?:week|month|year|summer|spring|autumn|winter|june|july|august|september|october|"
    r"november|december|january|february|march|april|may|weekend|christmas)|"
    r"in\s+(?:january|february|march|april|may|june|july|august|september|october|november|"
    r"december|the\s+summer|the\s+spring|the\s+autumn|the\s+winter)|"
    r"before\s+i\s|when\s+i\s+go|once\s+i)\b", re.I)
# The words that say a price is behind the person: a past verb of its own, or the thing already
# in their hands. "was expensive", "cost me a fortune", "we have already paid", "it got done".
REMARK_ALREADY_PAID = re.compile(
    r"\b(?:was|were|cost|costs|costing|cost\s+me|has\s+been|had\s+been|paid|spent|bought|"
    r"redid|redecorated|renovated|built|installed|fitted|took|got|had|already|last\s+"
    r"(?:year|month|week|summer|winter|spring|autumn)|ago|in\s+the\s+end|all\s+in)\b",
    re.I)
REMARK_LONG = re.compile(
    r"\b(?:took|takes|taking|take)\s+(?:forever|ages|hours|all day|all week|all weekend|weeks|"
    r"months|for ever|forever and a day)\b|\bso long\b|\blonger than\b|\bdragged on\b", re.I)
REMARK_BETTER = re.compile(
    r"\b(?:better|easier|nicer|cheaper|faster|less stressful|more money|pays better|pays more|"
    r"worth it)\b", re.I)
REMARK_HARD = re.compile(
    r"\b(?:hard|harder|difficult|tough|stressful|exhausting|draining|knackering|hectic|"
    r"a nightmare|a slog|a struggle)\b", re.I)
REMARK_WORK = re.compile(
    r"\bneeds?\s+(?:a lot of|some|lots of|loads of)\s+work\b|\bneeds? work\b|"
    r"\bneeds? doing\b|\bmore than i thought\b|\bbigger than i thought\b", re.I)
REMARK_GONE = re.compile(
    r"\b(?:got them|got it|ate them|ate it|ruined|ruined it|killed them|all gone|"
    r"eaten them|stole it|stole them|knocked them|gone to the slugs)\b", re.I)
# A loss is only read as a loss when the thing being lost is a plant or a crop: "the slugs got
# them" after tomatoes is a bed wiped out, and the same words about anything else are not a
# growing question at all.
GROWING = re.compile(
    r"\b(?:tomato|tomatoes|potato|potatoes|plant|plants|planted|seed|seeds|seedling|seedlings|"
    r"lettuce|beans|peas|carrot|carrots|onion|onions|squash|courgette|courgettes|pumpkin|"
    r"strawberr\w+|raspberr\w+|blackberr\w+|herb|herbs|flower|flowers|bulbs?|garden|allotment|"
    r"veg|vegetables?|crop|crops|greenhouse|bed|beds)\b", re.I)

# The endings. One is dropped when the last reply asked a question, because two questions in a row
# is an interrogation, so each kind keeps an ending that only says something back.
REMARK_REPLIES = {
    "expense": (
        "Not cheap, that.",
        "They never are.",
        "The bits nobody quotes for are always the ones that cost.",
        "Ouch. Do you think it was worth it?",
    ),
    # A price still to pay is a bill to move rather than money gone, so none of the endings above
    # fits it: "the bits nobody quotes for" is about a job already done, and "was it worth it" asks
    # about a trip nobody has booked. The one thing a friend asks first is what the figure is.
    "long": (
        "It always takes longer than the plan says it will.",
        "Longer than anyone warns you, every time.",
        "That is the way of it, and at least it is done.",
    ),
    "better": (
        "Good - that is the bit that matters.",
        "That is the bit that makes the difference.",
        "That sounds like the right move.",
    ),
    "hard": (
        "That is the thing nobody warns you about.",
        "It does take it out of you.",
        "It is - and it gets easier once the new bit is routine.",
        "Fair enough. What has been the hardest bit?",
    ),
    "work": (
        "Bigger job than it looked, then.",
        "That is how these go: the first quote is never the whole of it.",
        "Worth getting a second price before you say yes to it.",
    ),
    "gone": (
        "Ah, that is a shame.",
        "That is gutting.",
        "Netting is the only thing that stops it happening again.",
        "Will you put another lot in?",
    ),
}

REMARK_PRICE_AHEAD = (
    "Not cheap, that.",
    "They never are.",
    "What are they quoting for it? That is usually the bit worth moving.",
    "Worth pricing it a couple of ways round before you commit.",
)

# A remark with a "but" in it is two-sided - "its more money but its a longer day" is a person
# still weighing something up, and agreeing with half of it ("That sounds like the right move")
# answers a decision they have not made. Those keep the ordinary path.
REMARK_TWO_SIDED = re.compile(r"\b(?:but|though|although|however|except|apart from|other than"
                              r"|worse|less|harder|longer|slower)\b", re.I)
# A figure is a fact about the thing, not a complaint about its price. "is it worth getting a
# bike" ... "it costs 400" is the person telling the bot what the bike in front of them costs, and
# the answer to that is whether the figure is fair - but the expense remark read "costs" alone and
# replied "They never are.", agreeing with a complaint nobody made. So the expense kind needs a
# word of judgement in the line ("expensive", "a fortune", "not cheap", "a lot", "over budget"),
# and a line that carries only a figure is left to the ordinary path, which answers the figure.
REMARK_JUDGES_THE_PRICE = re.compile(
    r"\b(?:expensiv\w*|pricey|pricier|dear|dearer|a\s+fortune|a\s+bomb|a\s+packet|not\s+cheap|"
    r"cheap\s+enough|money\s+pit|over\s+(?:the\s+)?budget|cost(?:s|ing)?\s+(?:me\s+)?a\s+lot|"
    r"cost\s+me|too\s+much|so\s+much|that\s+much|a\s+lot\s+of\s+money|loads|rip[-\s]*off|"
    r"overpriced|adds?\s+up|worth\s+it|not\s+worth|daylight\s+robbery|steep)\b", re.I)

# The other half of an expense remark: the number and nothing said about it. "it costs 400" is the
# person answering "is it worth it" with the figure they are looking at, so the reply has to be
# about that number - what it would take to get it back - and not the endings above, which agree
# with a complaint nobody made ("They never are."), and not an echo ("Got it - it costs 400.").
REMARK_FIGURE = re.compile(
    r"(?:£|\$|€)\s*\d|\b\d{2,}\b|\b\d+\s*(?:quid|pounds?|euros?|dollars?|grand|k)\b", re.I)
REMARK_FIGURE_REPLIES = (
    "Then it comes down to what you get for it, and a second price usually moves the figure.",
    "That is the number to weigh up against what doing nothing would cost you.",
    "Worth checking that against one more quote before you commit to it.",
)

REMARK_KINDS = ((REMARK_EXPENSE, "expense"), (REMARK_LONG, "long"), (REMARK_BETTER, "better"),
                (REMARK_HARD, "hard"), (REMARK_WORK, "work"), (REMARK_GONE, "gone"))


def _the_opening_instead(said, clean, memory):
    """The question about the fact, where a receipt of the line is all the reply would be.

    On the first line of a chat a receipt is the filing cabinet: nothing comes back about the
    two jobs or the six-year-old. bot/memory/opening.py asks the question a friend asks about
    the fact instead, and stands aside for every line that is not that shape."""
    if not said or not reads_as_a_receipt(said):
        return None
    thing = _echo(clean, memory)
    if not thing:
        return None
    return opening.the_opening(thing, clean, memory)


def _a_hand_back(reply, memory):
    """Note a reply that answered a remark, so the turn after it can tell it from a new subject.

    The echo it replaces ("Got it - it takes forever.") was skipped by
    `bot/memory/topics.py::said_again` as an acknowledgement that says nothing of its own, which
    is how a follow-up two turns later still reached the answer above it. A remark is the same
    thing said properly - the subject stays where it was - so it keeps that behaviour without
    having to look like an acknowledgement. Only the reply's own words are kept, so a turn that
    gave something else is never mistaken for one.
    """
    if not isinstance(memory, dict):
        return
    said = " ".join(re.findall(r"[a-z0-9']+", str(reply or "").lower().replace("\u2019", "'")))
    if not said:
        return
    kept = memory.get("hand_backs")
    if not isinstance(kept, list):
        kept = []
        memory["hand_backs"] = kept
    kept.append(said)
    del kept[:-4]


def _a_remark_on_what_was_said(clean, memory):
    """The reply to a one-line remark about the turn before, or None when the line is not one.

    Only a short line that points back with a pronoun or a "the" and states one of the kinds
    above, and only after someone has said something for it to be about.
    """
    if not isinstance(memory, dict):
        return None
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return None
    body = clean.strip()
    if len(body.split()) > 9:
        return None
    if not REMARK_BACK.match(body) or "?" in body:
        return None
    if REMARK_TWO_SIDED.search(body):
        return None
    topic_text = str((memory.get("topic") or {}).get("text") or "") if isinstance(
        memory.get("topic"), dict) else ""
    for pattern, kind in REMARK_KINDS:
        if not pattern.search(body):
            continue
        if kind == "gone" and not GROWING.search(body + " " + topic_text):
            continue
        if kind == "expense" and not REMARK_JUDGES_THE_PRICE.search(body):
            # A figure on its own is not a remark about money: "it costs 400" says what the thing
            # costs, and "They never are." answers a complaint the person did not make. A line
            # that is the figure and nothing else is answered as the figure.
            if not REMARK_FIGURE.search(body):
                continue
            return pick(REMARK_FIGURE_REPLIES, memory, seed_text=body)
        options = REMARK_REPLIES[kind]
        if kind == "expense" and _a_price_still_to_come(body, topic_text):
            options = REMARK_PRICE_AHEAD
        if _asked_last(memory):
            options = tuple(one for one in options if not one.endswith("?")) or options
        return pick(options, memory, seed_text=body)
    return None


def _a_price_still_to_come(body, topic_text):
    """Whether an expense remark is about a price nobody has paid yet.

    "it cost a fortune" and "the flights are expensive" are the same kind of remark and want
    different endings: the first is money already spent, which is why the question that follows
    is whether it was worth it, and the second is a bill still to come, where that question asks
    about a thing that has not happened. The plan on the table decides it - a line in the past
    ("redid", "cost me", "last year") is behind them, and a plan still to happen ("going to",
    "in august", "next month") is not - and with nothing to say either way it counts as still to
    come, because asking someone whether an unbooked trip was worth it reads as the bot not
    having listened.
    """
    said = " ".join(part for part in (body or "", topic_text or "") if part)
    if REMARK_STILL_TO_COME.search(said):
        return True
    return not REMARK_ALREADY_PAID.search(said)


def _a_result_is_on_the_table(clean):
    """Whether this line is a result the person is waiting on or has just heard.

    Asked of bot/compose/fallback.py, which owns the two readings and the two replies, and
    imported here rather than at the top of the file because that file imports this one.
    """
    from ..compose import fallback
    return fallback.reads_as_a_result_line(clean)


# A hole in a frame: {Thing}, {thing}, {food}. What is left after the first one is the ending, and
# that is the part a person hears twice.
_HOLE = re.compile(r"\{[^}]*\}")
# The letters and digits of a line, so "I'm sorry it's all coming" and "I am sorry; it is all
# coming" compare as one ending.
_NOT_WORDS = re.compile(r"[^a-z0-9]+")


def _ending_of(frame):
    """The words a frame adds after the thing said back: the part that repeats between turns."""
    parts = _HOLE.split(frame)
    return " ".join(_NOT_WORDS.sub(" ", parts[1].lower()).split()) if len(parts) > 1 else ""


def _pick_ending(frames, memory, **fields):
    """One of the endings, never the one the reply before it ended with.

    The store says a different thing back each turn - "Your son is 9", then "Your daughter is
    4" - so bot.compose.pick cannot see the repeat: the whole line differs and the ending is the
    same twice running, which reads as a script even though the sentence does not. Facts follow
    facts, so this is where it happens most: "my son is 9 / my daughter is 4" came back as two
    "I'm sorry it's all coming at once" in a row.
    """
    turns = memory.get("turns") or []
    last = ""
    if turns and isinstance(turns[-1], dict):
        last = " ".join(_NOT_WORDS.sub(" ", str(turns[-1].get("bot") or "").lower()).split())
    fresh = [frame for frame in frames if not (_ending_of(frame) and _ending_of(frame) in last)]
    return pick(fresh or list(frames), memory).format(**fields)


# The people a line can be about when it explains a feeling: "he is only 6", "my son is 6".
PERSON_WORDS = frozenset(facts.RELATIONS) | frozenset((
    "kids", "children", "child", "baby", "toddler", "twins", "them", "they", "he", "she",
    "him", "her", "us", "we", "both"))


# An age said on its own is a fact about the person, not the reason for how they feel. "i lost my
# job last week" then "im 52" came back "You're 52 \u2014 so that is the part behind it. What has
# been hardest about it?", which makes the person's age the cause of the redundancy. The age has
# its own plain reading in this file ("you're 52", FACTS above), and the reason-reading is not for
# it; the same is true of a name handed over after bad news.
# The reason marker people put in front of the clause that explains how they are: "im low" then
# "because the kids are hard work". The marker says what the clause is for, so the reading does
# not have to guess it from the turn before, and it is not part of the thing said back - with it,
# the reply reads "Because the kids are hard work \u2014 noted.", which is the receipt of a reason.
A_REASON_MARKER = re.compile(
    r"^(?:(?:and|but|well|so|see)\s+)?(?:because|cos|coz|cause|cuz)\b(?:\s+of\b)?[\s,:]*", re.I)
# A turn that says nothing about how they are, said between the feeling and its reason: "im low"
# then "dont know why" then "because the kids are hard work". The feeling the reason belongs to
# is one turn further back, so the reading looks there rather than giving up on the turn.
NO_REASON = re.compile(
    r"^(?:(?:i\s+)?(?:dont|do not|dunno|havent a clue|no idea|not sure)\b"
    r"(?:\s+(?:really\s+)?(?:know\b\s*)?(?:why)?)?|no reason|not a clue)\s*[.!]*$", re.I)
# A bare thing is not a clause: "her job" and "only the kids" are lifted out of the line and put
# back into a sentence with the state they are the reason for (bot/memory/cause.py's expand),
# which says them in the bot's own words ("your job", not "her job"). A clause of its own ("the
# kids are hard work") has no expansion, so this reading answers it itself - and only a clause is
# worth looking a turn back for, because a bare thing after "dont know why" is still the thing
# the expansion knows how to say.
A_CLAUSE_OF_ITS_OWN = re.compile(
    r"\b(?:is|are|was|were|isnt|arent|wasnt|werent|gets?|got|makes?|made|keeps?|kept|feels?|felt"
    r"|never|always|doesnt|dont|didnt|wont|cant|couldnt|has|have|had|am|been|being|takes?|took"
    r"|wears?|wore|drives?|drove|works?|worked|goes|went|gives?|gave)\b", re.I)
AN_AGE_ALONE = re.compile(
    r"^(?:i'?m|im|i am|ive|i've|i just turned|i turned)\s+(\d{1,3})"
    r"(?:\s*(?:years?|yrs?)(?:\s+old)?)?(?:\s+(?:now|this year))?\s*[.!]?$", re.I)


def _after_a_feeling(clean, memory):
    """Whether this line is the reason for a feeling they said on the turn before.

    The reading of the line before is asked for again here rather than kept: memory["understood"]
    is this turn's reading, the modules answer in any order, and a marker written by one module
    would be lost with its copy when another one's reply is the one the user got. A feeling is
    the engine's own reading (intent "feeling", negative), so "my boss said my reports are late"
    is news and not one.

    The line has to be a short statement about the person or the people in it: a fact about the
    world ("my car is broken") keeps its ordinary echo, and a question has its own answer.
    """
    if AN_AGE_ALONE.match(str(clean or "").strip()):
        # An age is not a reason for anything here: it is what the person is, and the reply that
        # makes it "the part behind it" hands them their own age as the cause of their trouble.
        return False
    if not isinstance(memory, dict):
        return False
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return False
    index = len(turns) - 1
    last = turns[index]
    said = last.get("user") if isinstance(last, dict) else None
    if not isinstance(said, str) or not said.strip():
        return False
    if NO_REASON.match(said.strip()) and A_CLAUSE_OF_ITS_OWN.search(str(clean or "")):
        # "im low" then "dont know why": the turn that says nothing about how they are is not
        # the feeling this reason belongs to. It was answered "dont know why - noted" or with a
        # warm line of its own, and the reason they give next is still for the feeling one turn
        # back, so the reading looks there rather than dropping the reason.
        index -= 1
        if index < 0:
            return False
        back = turns[index]
        said = back.get("user") if isinstance(back, dict) else None
        if not isinstance(said, str) or not said.strip():
            return False
    read = understanding(said)
    if read.get("emotion") == "confused":
        # Losing the thread is not a mood the next line explains: after "i dont get it" the next
        # line is the part they did not follow, and "That is a lot to carry on top of how you
        # feel" is about a feeling nobody named.
        return False
    if AN_AIM.search(said):
        # An aim, not a mood: what follows it is progress and not the reason for it. A feeling now
        # is the exception, because that is the case the reason-reading exists for - somebody who
        # has just said what they are working at and then says they want to give up gets answered
        # warmly, not handed their own line back.
        now = understanding(clean)
        if not (now.get("intent") == "feeling" and (now.get("polarity") or 0) < 0) \
                and not A_FEELING_ABOUT_IT.search(clean):
            return False
    if read.get("intent") != "feeling" or (read.get("polarity") or 0) > 0:
        # "im fine" is a feeling too, and nothing follows from it.
        if not _a_heavy_reply_just_before(memory, index):
            return False
    words = clean.split()
    if not words or len(words) > 12:
        return False
    first = words[0].lower().strip(",;:!")
    if first in ("i", "im", "i'm", "ive", "i've", "we", "we're", "were"):
        return True
    return bool(PERSON_WORDS & {word.lower().strip(",;:!") for word in words})


def _a_heavy_reply_just_before(memory, index):
    """Whether the reply they got on turn `index` was about something heavy they are carrying.

    bot/modules/chat.py notes the pool it answered from when that pool is one of the heavy ones
    (its HEAVY_FEELINGS), and the note survives only if that module's reply is the one the person
    got. The engine's own reading is asked first and this is the second reading, because the
    engine files some heavy lines as news: "i miss my mum" is read as news, and the line after it
    ("she lives in spain") was answered "Got it - she lives in spain", which drops the missing.
    """
    if not isinstance(memory, dict):
        return False
    note = memory.get("heavy_reply")
    if not isinstance(note, dict):
        return False
    return note.get("turn") == index


# Who a line can be about when it is not about the person typing: the subject that carries a
# story on ("she took the kids to her mums", "he wont answer my calls", "they have gone to his
# mums"). A line that opens on "my" or "i" is the person's own life, and a fact about it is a
# fact even in a hard week ("my sister is called Meg" after "my wife left me" is still news the
# bot should hold). So the guard below asks for this, not for a pronoun anywhere in the line.
# What the bot says when it declines to file the line: the next line of a hard story is answered
# by keeping the floor with them, not by handing the turn on. Declining alone was the first shape
# of this rule, and it turned "she packed her things last night" after "my wife left me" into a
# removals checklist - the answers module saw the packing and offered "pack what you use least
# first". So this branch answers. The lines are short and they ask nothing, because the person is
# already telling it and a question at the end of every turn is the thing STYLE.md warns about.
THE_STORY_GOES_ON = (
    "I'm listening \u2014 say more if it helps.",
    "Go on. I'm here.",
    "That sounds like a lot to be in the middle of. Tell me the rest.",
    "I'm with you. Keep going if you want to.",
)
THIRD_PERSON = re.compile(r"^(?:he|she|they|him|her|his|their|them|hes|shes|theyre|theyd|"
                          r"theyll|she'd|he'd|she'll|he'll)\b", re.I)


def _bad_news_just_before(clean, memory):
    """Whether the line carries on a hard story the last turn or two began.

    The store files a fact and the echo hands it straight back, which is right for "my sister is
    called Meg". It is wrong in the middle of a story: after "im thinking of leaving my husband",
    "she took the kids to her mums" is the next line of it, not a detail to file, and "Noted:
    she took the kids to her mums" answers a marriage breaking up with a receipt.

    Both halves have to be true - bad news just before, and this line about someone else doing
    something - because a neutral fact told in a hard week is still a fact: "my sister is called
    Meg" after "my wife left me" is the one warm thing in the chat, and it must keep its echo.
    "Bad news" is read two ways because a person says it two ways: a break-up or a diagnosis
    (bot/compose/badnews.py) and a death (bot/compose/loss.py). "my nan died last week" then
    "he took the car" is the same story going on, and the car line was answering it with
    motorway advice.
    The other half of this rule is already in _learned, for a detail rather than a fact; asking
    it here covers the facts as well.
    """
    if not THIRD_PERSON.match(_strip_lead_in(clean)):
        return False
    for turn in (memory.get("turns") or [])[-2:]:
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "").lower()
        if reads_as_bad_news(said) or loss.reads_as_loss(said):
            return True
    return False


def carries_the_story_on(text, memory):
    """Whether this line is the next line of a hard story the last turn or two began.

    The public reading of `_bad_news_just_before`, for the arbiter: a line that opens on someone
    else ("she took the kids to her mums", "she packed her things last night") is the story going
    on, not a request and not a fact to file. A question is never that - "what do i do about the
    kids" inside the same story is a real ask, and the modules that answer asks should have it.
    """
    if not isinstance(text, str) or "?" in text:
        return False
    clean = " ".join(text.split())
    if not clean:
        return False
    return _bad_news_just_before(clean, memory)


# How long it has been going is the news, and the question that follows from it is the reply.
# How long it has been going is the news, and the question that follows from it is the reply.
# Rubbing the length in ("Got it - it's been like that for a week") tells the person what they
# said; a friend asks the one thing nobody has asked yet, in the person's own measure of it.
# None of these assumes the thing in hand is a trouble: the line read here says what somebody is
# doing as often as what is wrong ("im learning spanish" / "ive been doing it for 3 months"), and
# "long enough to stop waiting for it to pass" or "worth getting someone in" is not true of a
# language. What a length asks is whether it has moved, so that is all any of them ask.
LENGTH_TAIL = (
    "{length} of it \u2014 has anything changed in that time?",
    "{length} of it. How are you finding it now?",
    "{length} of it already. Is it going the way you want it to?",
    "{length} of it \u2014 and has anything you have tried made a difference?",
)

# The same when the line dates it instead of counting it: "since monday".
SINCE_TAIL = (
    "Since {when} \u2014 has anything changed in that time?",
    "Since {when}. How are you finding it now?",
    "Since {when}. Is it going the way you want it to?",
    "Since {when} \u2014 and has anything you have tried made a difference?",
)

# A measure that already carries its own amount needs no "of it": "Over a week of it" is the
# only shape that reads, so these leads are kept and the rest ("for", "about", "the last") are
# dropped, leaving "A week of it".
LENGTH_KEEPS = frozenset(("nearly", "almost", "over", "going on"))


# A thing being replaced has an age, and the age is the only new fact in the line. "the old one
# is 12 years old" is the thing in hand plus a number of years, and nothing else: the subject is a
# pronoun for the thing, not a name for it, so the entries for named things never see this line.
# The number is read as a digit or as the word people type: "the old one is twelve years old" is
# the same line as "the old one is 12 years old", and read as a digit only it fell through to the
# echo - "Got it - the old one is twelve years old." - which is their own line back.
THE_OLD_ONE = re.compile(
    r"^\W*(?:the|my|our)\s+(?:old|current|existing|present)?\s*one"
    r"(?:\s+(?:i|we)\s+(?:have|'ve|ve|got|use|used))?"
    r"\s+(?:is|was|'s|s)\s+(?P<n>\d{1,2}|[a-z]{3,9})\s*(?:years?|yrs?)(?:\s+old)?\W*$", re.I)
# The turn before it is about getting or replacing one. "new" is the word people use for the one
# they are going to buy, and "getting a" is how they say it out loud.
REPLACING = re.compile(
    r"\b(?:new|getting|get|got|bought|buy|buying|replace|replacing|upgrade|upgrading|"
    r"order|ordering|shopping for|looking at|need a|needs a|want a|after a)\b", re.I)
# Every frame uses the number, and none of them assumes the thing broke: "i need a new one" is
# as often an upgrade as a failure. The first asks the one thing a friend asks next.
OLD_ONE_TAIL = (
    "{n} years on the old one \u2014 it has done its share. What are you after this time?",
    "{n} years is a good run out of one, so you are not replacing it early.",
    "{n} years \u2014 that is a fair innings, and it has earned the swap.",
)


def the_old_one_aged(clean, memory):
    """The reply to a line giving the age of the thing they are replacing, or None.

    "i need a new washing machine" then "the old one is 12 years old" was read as a child of
    twelve and answered "One kid, twelve - noted.", and once that was put right the line fell
    through to the composer's echo - "Got it - the old one is 12 years old." The age is what the
    purchase is measured against, so the reply says what the number means for it.

    Two things have to hold. The line has to be the thing in hand and its age, and nothing else:
    a thing named for itself ("my boiler is 8 years old") is a question about that thing and has
    an entry of its own. And the turn before has to be about getting or replacing one, because
    an age on its own is not a purchase: "my car is 12 years old" after a line about the children
    stays with whatever reads the car.
    """
    if not isinstance(clean, str):
        return None
    found = THE_OLD_ONE.match(clean)
    if not found or len(clean.split()) > 9:
        return None
    said_age = found.group("n").lower()
    if said_age.isdigit():
        age = int(said_age)
    else:
        spoken = facts.WORD_NUMBERS.get(said_age)
        if not isinstance(spoken, int):
            return None
        age = spoken
    if not 5 <= age <= 40:
        return None  # "two years old" is a bad run, not a good one
    turns = memory.get("turns") if isinstance(memory, dict) else None
    said = [str(turn.get("user") or "") for turn in (turns or []) if isinstance(turn, dict)]
    if not said or not REPLACING.search(said[-1]):
        return None
    if A_FEELING.search(clean) or DEATH_WORDS.search(clean) or BLEED.search(clean):
        return None
    return pick(OLD_ONE_TAIL, memory, seed_text=clean).format(n=age)


def _the_length(clean, memory):
    """The reply to a line that says only how long the thing has been going, or None.

    Said a turn after the bot answered that thing, this is the person telling the answer how
    long it has had: "its been like that for a week" is not a detail to file and hand back, and
    handing it back is what the fridge conversation came out as. The length belongs with the
    answer, so this only reads the line when the last turn was an answer - a length said cold is
    its own subject and keeps its own reply. A body that hurts, a loss and a feeling are somebody
    else's turn even said this short.
    """
    if not narrow.only_a_length(clean):
        return None
    from . import tried

    if not tried.after_an_answer(memory):
        return None
    if reads_like_a_symptom(clean.lower()) or reads_as_bad_news(clean.lower()):
        return None
    if A_FEELING.search(clean) or DEATH_WORDS.search(clean):
        return None
    found = narrow.A_LENGTH.search(clean)
    lead = found.group("lead").lower()
    amount = found.group("amount")
    unit = found.group("unit").lower()
    if lead == "since":
        # A weekday is a name and keeps its capital; "since yesterday" is a word like any other.
        when = unit[0].upper() + unit[1:] if unit in narrow.LENGTH_NAMED_DAYS else unit
        return pick(SINCE_TAIL, memory, seed_text=clean).format(when=when)
    # "for months" has no amount of its own, and "a months" is not a sentence: the plural unit is
    # the measure on its own.
    length = "%s %s" % (amount, unit) if amount else unit
    if lead in LENGTH_KEEPS:
        length = "%s %s" % (lead, length)
    return pick(LENGTH_TAIL, memory, seed_text=clean).format(
        length=length[0].upper() + length[1:])


def _the_hours(clean, read, memory):
    """The reply to a line about the hours they work, or None.

    "i work nights" is a fact about their week, and the store filed it: "Noted: you work
    nights." is a clerk with a form, not a friend. The reply is about the life those hours make
    - the body clock, the week that moves, the day with no edges - and it is chosen by which of
    those the line says, never by the words of a topic, so it cannot be pasted onto another
    line. Only a line that is only that: a body that will not sleep, a job they are sick of, a
    wage, a rota they want out of and any ask are all somebody else's turn, and a loss thread
    keeps its own quiet.
    """
    if "?" in clean or WANTS_ANSWER.search(read):
        return None
    if NOT_THE_HOURS.search(read):
        return None
    if DEATH_WORDS.search(read) or A_FEELING.search(clean) or BLEED.search(read):
        return None
    if reads_like_a_symptom(read.lower()) or reads_as_bad_news(read.lower()):
        return None
    # A death in the last few turns is not a chat about the rota, whatever the company gives
    # them: the loss modules answer those turns and this one stays out of the way.
    turns = [one for one in (memory.get("turns") or []) if isinstance(one, dict)]
    recent = " ".join(str(one.get("user") or "") for one in turns[-3:])
    if recent and DEATH_WORDS.search(recent):
        return None
    last_ask = str(turns[-1].get("user") or "") if turns else ""
    if turns and turns[-1].get("module") == "answers" and reads_as_an_ask(last_ask):
        # The line is a detail added to the answer just given ("should i nap in the afternoon" /
        # "i work from home"): the thing on the table is the answer, and saying it back with
        # that answer under it beats a pool that starts a new subject of its own. The ask in the
        # line before it is what makes it a detail - hours said cold are their own subject.
        return None
    family, pool = _hours_family(read)
    if pool is None:
        return None
    # The store keeps the job whichever way the turn goes, so the hours are still there to be
    # asked about later; only the reply is this one's. The kind of week is kept for the turn
    # after it, because the next line is usually "does that get easier" (bot/memory/hours.py).
    hours_after.note(memory, family)
    return pick(pool, memory, clean)

def _a_deadline(clean, read, memory):
    """The reply to a line that only says when the thing we just answered has to happen.

    "its tomorrow" and "its in three weeks" are the person telling us the answer we just gave has
    a clock on it. The answer is aimed at the clock rather than said again: a deadline a day off
    is cut down to its first step, and one weeks off is spread out. Only after a real answer - a
    line from the answers module long enough to be advice - because a deadline has nothing to
    change when the turn before it was a hello or a hedge, and never in a loss thread, where the
    clock is not the thing that matters.
    """
    found = WHEN_DETAIL.search(clean)
    if not found:
        return None
    if len(clean.split()) > 7:
        return None
    turns = [one for one in (memory.get("turns") or []) if isinstance(one, dict)]
    if not turns:
        return None
    last = turns[-1]
    said = str(last.get("bot") or "")
    if last.get("module") != "answers" or len(said.split()) < 18:
        return None
    if not _tells_them_what_to_do(said):
        return None  # a list of facts has no first step, and a deadline has nothing to change
    recent = said + " " + " ".join(str(one.get("user") or "") for one in turns[-3:])
    if DEATH_WORDS.search(recent) or BLEED.search(recent) or A_FEELING.search(clean):
        return None
    when = found.group("when").strip()
    pools = {"today": WHEN_TODAY_TAIL, "tomorrow": WHEN_TOMORROW_TAIL, "days": WHEN_DAYS_TAIL}
    pool = pools.get(_shape_of(when), WHEN_ROOMY_TAIL)
    return pick(pool, memory, clean).format(when=when, When=when[:1].upper() + when[1:])


def _an_hour_on_the_day(text):
    """Which pool an hour on the day belongs to: "nerves" for an appointment, "flat" for a shift.

    "i have a night shift tomorrow" / "its at 10pm" is an hour on the day too, and a night shift at
    ten is spent asleep in the morning: the appointment pools, which all say what the morning is
    for, say the opposite of that person's day. The flat pool says only that the day fits round
    the hour, which is true of a shift, a class, a viewing and lunch with a sister.
    """
    if not isinstance(text, str) or not text:
        return None
    if CLOCK_EVENT.search(text):
        return "nerves"
    if CLOCK_FLAT.search(text):
        return "flat"
    from . import when as clock  # noqa: PLC0415 - same package, kept local for the import order

    return "nerves" if clock.EVENT_WORD.search(text) else None


# "the total is at 40" has the same shape as "the appointment is at 2:30", and only the noun tells
# them apart: a quantity on a total, a bid, a count, a level or a price is not an hour, and those
# lines used to get "At 40, so the morning is free...".
THE_NOUN_IS_AT = re.compile(r"\bthe\s+(?P<noun>[a-z'-]+)\s+is\s+(?:at|for)\s+", re.I)
# A figure carrying its own marker is a time whatever noun is in front of it.
A_MARKED_HOUR = re.compile(
    r"\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.)|\d{1,2}[:.]\d{2}|o'?\s?clock|"
    r"\b(?:half|quarter)\b|\b" + TIME_WORD + r"\b", re.I)


def _the_figure_is_an_hour(when):
    """True when the figure is an hour at all: "40" is a quantity, and a clock stops at 24."""
    head = re.match(r"\s*(\d{1,2})(?!\d)", when)
    if not head:
        return True  # a spelled hour ("half nine", "ten o'clock") is a time
    return 1 <= int(head.group(1)) <= 24


def _a_clock_time(clean, read, memory):
    """The reply to a line that only gives the hour the thing we just answered is at, or None.

    "its at 10" and "the interview is at 10" say when the answer above has to happen, and the
    answer is aimed at the hour instead of being said back. Only after a real answer that tells
    them what to do, and only when the conversation already names something that goes in a diary
    (an interview, an appointment, a scan, a flight): the same words after advice about the roses
    ("its at 10") are not an appointment, and the store has nothing to build a morning around.
    """
    if len(clean.split()) > 8:
        return None
    found = CLOCK_DETAIL.search(clean) or CLOCK_AT.search(clean)
    if not found:
        return None
    from . import when as clock  # noqa: PLC0415 - same package, kept local for the import order

    turns = [one for one in (memory.get("turns") or []) if isinstance(one, dict)]
    if not turns:
        return None
    last = turns[-1]
    said = str(last.get("bot") or "")
    module = last.get("module")
    theirs = " ".join(str(one.get("user") or "") for one in turns[-3:])
    if module == "greeting" and not len(said.split()) < 5:
        # The composer's own acknowledgment is a whole turn too: "im going for a scan next week"
        # is answered "Noted: you're going for a scan next week.", and the hour after it is the
        # hour of that scan. It counts when either side names the thing that goes in a diary:
        # the acknowledgment used to hand the words back, and the small talk now answers the
        # same line with "How are you feeling about it?", which names nothing at all.
        if not (_an_hour_on_the_day(said) or _an_hour_on_the_day(theirs)):
            return None
    elif module not in ("answers", "chat", "memory_store") or len(said.split()) < 5:
        return None
    # What they said, not what the answer said: "i want to learn spanish" is answered with advice
    # that says "start", and a start is not an appointment at seven.
    kind = _an_hour_on_the_day(theirs)
    if not kind:
        return None
    # The emergency guard reads the person's own words and this line, never the answer above: a
    # dentist card that mentions gums that bleed was enough to drop the hour of the appointment,
    # and the hour is exactly what the person gave.
    recent = said + " " + theirs
    if DEATH_WORDS.search(theirs) or BLEED.search(clean) or A_FEELING.search(clean):
        return None
    when = found.group("when").strip()
    if not _the_figure_is_an_hour(when):
        return None
    named = THE_NOUN_IS_AT.search(clean)
    if named and not A_MARKED_HOUR.search(when) and not _an_hour_on_the_day(named.group("noun")):
        # "the appointment is at 2:30" is the hour of the thing; "the total is at 40" is a figure
        # on a total, and the noun is what tells them apart.
        return None
    at = "At " + when
    if kind == "flat":
        pool = CLOCK_FLAT_TAIL
    else:
        pool = CLOCK_AFTER_TAIL if _clock_shape(when) == "after" else CLOCK_MORNING_TAIL
    return pick(pool, memory, clean).format(At=at[:1].upper() + at[1:], When=when[:1].upper()
                                            + when[1:], when=when)


def _hours_family(read):
    """Which kind of week the line names, and the pool that answers it.

    Six shapes people put their hours in, and the reply has to be about the one they said: a
    night shift has a body clock to it, an early start has a night before, working from home has
    no edges at all.
    """
    if ON_NIGHTS.search(read):
        return "nights", NIGHT_TAIL
    # "on lates"/"on earlies" are the shift pattern itself, not a finish time: the late and early
    # tails already say the right thing about a week of two-till-ten or six-till-two.
    if SHIFT_LATE.search(read):
        return "late", LATE_TAIL
    if SHIFT_EARLY.search(read):
        return "early", EARLY_TAIL
    if EARLY_RISE.search(read):
        return "early", EARLY_TAIL
    if LATE_FINISH.search(read):
        return "late", LATE_TAIL
    if LONG_SHIFT.search(read):
        return "long", LONG_TAIL
    if SHIFTS_ALL_OVER.search(read):
        return "spread", SPREAD_TAIL
    if WORK_FROM_HOME.search(read):
        return "home", HOME_TAIL
    return None, None


# "i have two cats as well" adds to what the bot already has, and the fact frames say so ("as
# well"); the pet tail would drop that, so a line that adds keeps the frame it had.
AS_WELL = re.compile(r"\b(?:as\s+well|too|also|another)\b", re.I)
# A child in the line is a second fact, and the kids tail is the one that answers it: "i have two
# kids n a dog called rex" is not a line about a dog. The store keeps the count under a key the
# fact frames own, so the line itself is what is read here.
A_CHILD_IN_THE_LINE = re.compile(
    r"\b(?:kid|kids|child|children|son|sons|daughter|daughters|baby|babies|toddler)\b", re.I)
# What a line can add about the pet it names and still be news of the pet: the name, the count,
# the age, and the breed. The pet tail asks how long the animal has been with them, which is the
# question for a pet arriving - it is the wrong question for a line that says how the animal
# *is*. The store can only keep the animal out of "my pug is snoring a lot", "my whippet is
# shivering" and "my mongrel is fine", so set(found) == {"pets"} held for all three and the tail
# asked "is it good company?" at somebody describing a symptom. The shape after the animal word
# is the test rather than a list of symptoms, so the next unlisted one is covered too: a name, a
# count, an age or a breed keeps the tail, and anything else after "is/are/has/got" is how the
# animal is.
PET_ADDED = re.compile(
    r"\A\s*,?\s*(?:"
    r"(?:(?:is|are|was|were)\s+)?(?:called|named)\b[\w' ]*"           # "is called biscuit"
    r"|(?:is|are|was|were)\s+(?:\d\w*|one|two|three|four|five|six|seven|eight|nine|ten"
    r"|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty"
    r"|thirty|forty|fifty)\b(?:\s*(?:years?|months?|weeks?|days?)\s*old|\s+old)?\s*\Z"
    r"|(?:is|are)\s+(?:a|an|another)\s+[\w' ]{1,20}\Z"               # "is a rescue"
    r"|,\s*\w[\w' ]*"                                                 # "two cats, milly and tom"
    r"|(?:and|with|plus|,)\s+(?:a|an|another|one|\d+)?\s*[\w' ]{1,24}\Z"  # "and a dog"
    r"|\Z"                                                             # "we got a pug"
    r")", re.I)


# The words that say the animal is all right are not a symptom: "my dog is fine now thanks" is the
# person saying the animal came through, and the store has always said that back without the
# "thanks". A line like that is a fact to echo, so it neither stands aside for an answer (which is
# what "my pug is snoring a lot" needs) nor takes the tail that asks how long the pet has been with
# them.
PET_ALL_RIGHT = re.compile(
    r"\b(?:is|are|was|were|'s)\s+(?:(?:doing|feeling)\s+)?(?:fine|ok|okay|better|well|healthy|"
    r"alright|all\s+right|great)\b", re.I)


def _a_pet_that_is_all_right(clean, kept):
    """Whether the line says the animal is fine, rather than how it is ill.

    Read after the animal word, so "my dog is fine" counts and "my dog is being sick" does not.
    """
    text = str(clean or "")
    for pet in kept or []:
        if not isinstance(pet, dict):
            continue
        word = str(pet.get("breed") or pet.get("animal") or "").strip().lower()
        if not word:
            continue
        found = re.search(r"\b" + re.escape(word) + r"s?\b", text, re.I)
        if found and PET_ALL_RIGHT.search(text[found.end():]):
            return True
    return False


# A name reaches the line from both sides. "my cat is called Biscuit" puts it after the animal
# and PET_ADDED reads it; "we named the cat Biscuit" and "i called my dog Rex" put it in front,
# and the words after the animal are the name and nothing else, so the whole line stood down
# and the person got "Thanks for telling me" for introducing their animal. The introducing verb
# has to sit right before the animal word: "i called the vet about my cat snoring" is not this,
# and the rest of that line is how the animal is anyway.
INTRODUCED_BEFORE = re.compile(
    r"\b(?:named|called)\s+(?:the|my|our|a|an|his|her|their|its)?\s*\Z", re.I)
# ...and the name is the only thing after the animal. "they called my dog a nuisance" has the
# verb in front too, and "a nuisance" is how somebody treated the animal, not what it is called.
A_NAME_AFTER = re.compile(r"\s*,?\s*[a-z][\w'-]*[.!]?\Z", re.I)


def _nothing_added_but_the_pet(clean, kept):
    """Whether the words after the animal add nothing but its name, count, age or breed.

    The animal word is the one the person used ("pug", not the store's "dog"), so a breed is
    found in the line as they said it. A line that never repeats the animal ("we got one") keeps
    the tail: the store reached an animal, and only the words beside it could say otherwise.
    """
    text = str(clean or "")
    for pet in kept or []:
        if not isinstance(pet, dict):
            continue
        word = str(pet.get("breed") or pet.get("animal") or "").strip().lower()
        if not word:
            continue
        found = re.search(r"\b" + re.escape(word) + r"s?\b", text, re.I)
        if not found:
            continue
        if PET_ALL_RIGHT.search(text[found.end():]):
            continue  # "my dog is fine now": a fact, and the echo below says it back
        if (INTRODUCED_BEFORE.search(text[:found.start()])
                and A_NAME_AFTER.match(text[found.end():])):
            continue  # "we named the cat Biscuit": the name is in front of the animal
        if not PET_ADDED.match(text[found.end():]):
            return False
    return True


# "i have lots of fish" is a number the store does not keep, and "You have a fish" is a smaller
# family than the person has. The vague quantities keep the echo.
A_VAGUE_MANY = re.compile(r"\b(?:lots|loads|plenty|several|many|a\s+few|some)\b\s*(?:of\s+)?",
                          re.I)


# What a person says to "forget the dog" when there was never a dog: the same words back, short.
ANIMAL_TAKEN_BACK = (
    "No {animal}, then.",
    "Fair enough \u2014 no {animal}.",
    "Right \u2014 no {animal}.",
)


# A want is not a take-back. "she wants a puppy", "my son would like a rabbit", "the kids have
# been asking for a hamster" and "im after a kitten" all read as a pet that is not theirs - true,
# and no use as a reply - and the take-back pool said them back as a refusal.
A_WANTED_ANIMAL = re.compile(
    r"\b(?:want|wants|wanted|wanting|would\s+like|'d\s+like|would\s+love|fancy|"
    r"fancied|i'?d\s+love|id\s+love|after|asked\s+for|"
    r"asking\s+for|been\s+asking|begging\s+for|dream(?:s|ing)?\s+of|keen\s+on|"
    r"desperate\s+for|mad\s+(?:on|for)|hoping\s+(?:for|to\s+get)|"
    r"(?:thinking|thought|talking)\s+(?:of|about)\s+getting|going\s+to\s+get)\b", re.I)
# The same words turned down: "she doesn't want a puppy", "not keen on a dog".
A_WANT_TURNED_DOWN = re.compile(
    r"\b(?:don'?t|dont|doesn'?t|doesnt|didn'?t|didnt|won'?t|wont|not|never|no\s+longer)\b"
    r"[^.!?;]{0,16}\b(?:want|wants|wanted|like|keen|after|ask(?:ed|ing))\b", re.I)
# An animal they had and do not have now: "i had a dog growing up", "we used to have a cat".
A_HAD_AN_ANIMAL = re.compile(
    r"\b(?:had|used\s+to\s+have|use\s+to\s+have|grew\s+up\s+with)\b", re.I)


# What a friend says to "i had a dog growing up": the animal is a memory, so the question is the
# one a memory invites, not a refusal.
ANIMAL_HAD_ONCE = (
    "A {animal} growing up, then \u2014 would you have another?",
    "You had a {animal} before. Do you think you would again?",
    "A {animal} when you were younger, then. What do you miss about it?",
)

# "the kids want a pet" names no animal, so the reply is the question a friend asks first.
A_PET_WANTED = (
    "Which animal are they after \u2014 a dog, a cat, something small?",
    "What have they got in mind? A pet is a long commitment and the answer changes with the animal.",
)

# A want no entry answers: the next question a friend asks about getting one.
A_WANTED_ANIMAL_TAIL = (
    "A {animal}, then \u2014 what is putting you off getting one?",
    "So you are thinking about a {animal}. Who would look after it in the day?",
    "A {animal} is a long commitment. How soon were you thinking?",
)


def _a_wanted_animal(clean):
    """True when the line asks for an animal rather than turning one down or remembering one."""
    low = str(clean or "")
    if A_WANT_TURNED_DOWN.search(low):
        return False
    return bool(A_WANTED_ANIMAL.search(low))


def _an_animal_wanted(clean):
    """The animal a line wants, or "".

    Read from the line and not from the store, because the want is often the only thing the store
    does not keep: "my son would like a rabbit" filed the son and dropped the rabbit.
    """
    low = str(clean or "")
    if not _a_wanted_animal(low):
        return ""
    for match in facts.PETS.finditer(low):
        return match.group(1).lower()
    # "the kids want a pet" names no animal at all, and the answer to that is the question which
    # one; facts.PETS is the list of animals named, so the plain word is read here.
    if PET_WORD.search(low):
        return "pet"
    return ""


def _an_animal_they_had_once(clean):
    """True when the line is an animal the person used to have, not one they are asking for."""
    low = str(clean or "")
    if _a_wanted_animal(low):
        return False
    return bool(A_HAD_AN_ANIMAL.search(low))


PET_WORD = re.compile(r"\b(?:pet|pets)\b", re.I)


def _what_a_wanted_animal_needs(animal, clean, memory):
    """What having one of these takes, from the knowledge base, or the want's next question.

    The line already names the animal, so the entry it reaches is that animal's own. A want that
    no entry answers - "the kids want a pet", a fish nobody has named - gets the shortest honest
    thing a friend says, which is the next question, never the animal handed back.
    """
    reading = {}
    try:
        from ..knowledge import lookup  # noqa: PLC0415 - only when an animal is wanted
        reading = understanding("what do i need for a " + animal)
        found = lookup.find(reading)
    except Exception:  # noqa: BLE001 - a knowledge base that cannot answer only adds no reply
        found = None
    if found is not None:
        reply = getattr(found, "reply", None)
        try:
            reply = reply(memory, reading) if callable(reply) else reply
        except Exception:  # noqa: BLE001
            reply = ""
        if isinstance(reply, str) and reply.strip():
            return reply.strip()
    if animal == "pet":
        return pick(A_PET_WANTED, memory, seed_text=clean)
    return pick(A_WANTED_ANIMAL_TAIL, memory, seed_text=clean).format(
        animal=animal, Animal=animal[:1].upper() + animal[1:])


# An animal on its way: "we are getting a puppy next week", "we are adopting a cat". The
# store keeps it, marked `coming`, so a later "what pets do i have" answers with what is
# here and the follow-ups still have the puppy to talk about.
ANIMAL_COMING = (
    "A {animal} on the way, then \u2014 is everything ready for it?",
    "A {animal} coming home. Have you picked a name yet?",
    "A {animal} to look forward to.",
)


# An animal on its way, not one in the house. The store marks it `coming` ("we're getting a
# puppy next month") and the follow-up that names the breed ("its a labrador") reaches the pet
# tail, whose questions - how long has it been with you, what's it like to live with, is it good
# company - are all about an animal the person has met. A friend asks the one thing that is still
# open: when it turns up.
PET_TAIL_COMING = (
    "{Thing} \u2014 when does it arrive?",
    "{Thing}. Not long now.",
    "{Thing} \u2014 the waiting is the worst part.",
)
PET_TAIL_COMING_MANY = (
    "{Thing} \u2014 when do they arrive?",
    "{Thing}. Two at once, that's a houseful.",
    "{Thing}. Not long now.",
)


def _the_pets_are_coming(pets, memory):
    """Whether the animals this line names are ones the store already has on their way.

    Read from the store and not the line: the line that says the animal is coming has its own
    reply (`ANIMAL_COMING`), and this is for the lines after it, which name the animal again
    without saying it is on its way. A puppy is a dog, so the kinds are compared rather than the
    words.
    """
    coming = set()
    for pet in ((memory or {}).get("user") or {}).get("pets") or []:
        if isinstance(pet, dict) and pet.get("coming"):
            kind = facts.ANIMAL_KINDS.get(str(pet.get("animal") or "").strip().lower(), "")
            if kind:
                coming.add(kind)
    if not coming:
        return False
    for pet in pets or []:
        if not isinstance(pet, dict):
            continue
        if pet.get("name") or (pet.get("count") or 0) > 1 or not pet.get("breed"):
            # A named animal, or more than one of them, is not the one on its way: "my dog is
            # called rex" after an announced puppy is the dog they have, and answering it with
            # the coming pool asks when Rex arrives. Only an animal the line names with nothing
            # of its own - the breed on the one coming - is read as that animal. The breed is the
            # shape the store fills in on an animal already on its way, so it is the shape this
            # reply is for: `my dog is 3` names an animal they have, and "the waiting is the
            # worst part" is about nobody.
            continue
        kind = facts.ANIMAL_KINDS.get(str(pet.get("animal") or "").strip().lower(), "")
        if kind in coming:
            return True
    return False


def _the_animal_coming(found):
    """The animal word of an animal the line says is on its way, or ""."""
    for pet in (found or {}).get("pets") or []:
        if isinstance(pet, dict) and pet.get("coming"):
            animal = str(pet.get("animal") or "").strip().lower()
            if animal:
                return animal
    return ""



def _the_taken_back_animal(found):
    """The animal word the take-back names, or ""."""
    for pet in (found or {}).get("pets") or []:
        if isinstance(pet, dict) and pet.get("not_theirs"):
            animal = str(pet.get("animal") or "").strip().lower()
            if animal:
                return animal
    return ""


def _an_animal_turned_down(found, memory):
    """True when the line is a "no" on an animal they do not have.

    "i dont want a dog" files a dog that is not theirs and, beside it, a taste of "no" on the
    dog, so the take-back reading saw a second fact in the line and declined. What answered the
    refusal was the composer, holding the answer above: "Nothing there was a dog, so the answer
    holds. A bed, two bowls, a crate or pen, a collar and lead..." - the whole dog kit handed
    back to a person who has just said no to it. A taste of "no" on the same animal is the
    refusal said in the store's own words, not another thing in the line, and an animal they do
    have keeps the store's own line.
    """
    if not isinstance(found, dict):
        return False
    pets = [pet for pet in (found.get("pets") or []) if isinstance(pet, dict)]
    if not pets or not all(pet.get("not_theirs") for pet in pets):
        return False
    if set(found) - {"pets", "tastes"}:
        return False
    animal = _the_taken_back_animal(found)
    if not animal or _on_record(animal, memory):
        return False
    named = {str(pet.get(field) or "").strip().lower()
             for pet in pets for field in ("animal", "breed")}
    named.discard("")
    tastes = [taste for taste in (found.get("tastes") or []) if isinstance(taste, dict)]
    return bool(tastes) and all(str(taste.get("thing") or "").strip().lower() in named
                                for taste in tastes)


def _on_record(animal, memory):
    """True when the store holds an animal of that kind as one of theirs."""
    user = (memory or {}).get("user") if isinstance(memory, dict) else None
    pets = (user or {}).get("pets") if isinstance(user, dict) else None
    for pet in pets or []:
        if isinstance(pet, dict) and str(pet.get("animal") or "").strip().lower() == animal:
            return True
    return False


# The animal they would like, said back: the breed is the word they used, so "i want a labrador"
# is answered about a labrador and not about a dog. The pools are the composer's line for an
# animal somebody wants ("A dog? Where are you up to with it?"), said here because the echo is
# the module that has the animal in hand and the composer has already declined the line.
WISH_FOR_AN_ANIMAL = (
    "{Thing}? Where are you up to with it?",
    "{Thing} - what's drawing you to one?",
    "{Thing}. What would you have to sort out first?",
)
# The animal is named again with a different breed, inside a plan to get one: "im thinking of
# getting a rescue greyhound" / "actually its a whippet". No question about having it can be
# asked, because there is nothing in the house yet; what is open is whether the choice is made.
A_BREED_BEING_CHOSEN = (
    "{Animal} \u2014 are you settled on that one?",
    "{Animal}, then. What made you pick that one?",
    "{Animal} \u2014 have you met one before?",
)


def _an_animal_only_planned(found, clean, memory):
    """The animal word a line renames inside a plan to get one, or "".

    Both halves are asked of the store and the subject rather than of the wording: the line gives
    one animal and no flag on it, the correction is a bare naming, and the chat is on a plan to
    get something. A line that is not a correction, or a chat that is on anything else, is left
    to the pet tail and to every other rule.
    """
    pets = [pet for pet in ((found or {}).get("pets") or []) if isinstance(pet, dict)]
    if len(pets) != 1:
        return ""
    pet = pets[0]
    if pet.get("wanted") or pet.get("coming") or pet.get("not_theirs"):
        return ""  # the store says what the animal is, and the pools above answer it
    if not topics.NAMES_THE_THING.match(" ".join(str(clean or "").lower().split())):
        return ""
    record = memory.get("topic") if isinstance(memory, dict) else None
    plan = str(record.get("text") or "") if isinstance(record, dict) else ""
    if not plan or plan.strip().lower() == str(clean or "").strip().lower():
        return ""
    if not topics.A_THING_ON_ITS_WAY.search(plan):
        return ""
    return str(pet.get("breed") or pet.get("animal") or "").strip().lower()


def _the_wished_animal(found, clean=""):
    """The animal the line wishes for, as they named it - the breed if they gave one."""
    for pet in (found or {}).get("pets") or []:
        if isinstance(pet, dict) and pet.get("wanted"):
            said = str(pet.get("breed") or pet.get("animal") or "").strip().lower()
            if said:
                return said
    words = [word for word in str(clean or "").split() if word.isalpha()]
    return words[-1] if words else "one"


def _only_a_wish(found):
    """True when everything the line gave the store is an animal the person would like."""
    if not isinstance(found, dict) or set(found) - {"pets"}:
        return False
    pets = [pet for pet in (found.get("pets") or []) if isinstance(pet, dict)]
    return bool(pets) and all(pet.get("wanted") for pet in pets)


def _an_animal_taken_back(found):
    """True when the only thing the line gave the store is an animal being taken back.

    A wish is not a take-back. "i want a labrador" and "i might get a dog" name an animal the
    person would like, and answering "No dog, then." agreed to take away a dog nobody had, and
    said no to a line that was asking about one. The store marks the two apart (`wanted`), so a
    wished-for animal declines here and the composer answers what they would do with one.
    """
    if not isinstance(found, dict) or set(found) - {"pets"}:
        return False
    pets = [pet for pet in (found.get("pets") or []) if isinstance(pet, dict)]
    if any(pet.get("wanted") for pet in pets):
        return False
    return bool(pets) and all(pet.get("not_theirs") for pet in pets)


def _the_pets_said(kept, clean=""):
    """The pets the store kept, as a person would say them: "two cats and a dog, Milly and Tom".

    The store has one entry per animal, with the count and the name beside it, so the numbers and
    the names are both there; what was missing is the sentence a friend would make of them. Two
    cats and a dog is not "two dogs", which is what counting the entries says.
    """
    number = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
              8: "eight", 9: "nine", 10: "ten"}
    groups = []
    for pet in kept or []:
        if not isinstance(pet, dict):
            continue
        # The store keeps the kind of animal and, beside it, the breed the person named: "we got
        # a rescue greyhound" is said back as a greyhound, not as a dog, because that is the word
        # they used. Two dogs of different breeds are two groups, which is right: "a greyhound
        # and a labrador" is what they have, not "two dogs".
        try:
            count = int(pet.get("count") or 1)
        except (TypeError, ValueError):
            count = 1
        # A breed named beside a group is the breed of one of them, so the group is said by its
        # kind: "we have two dogs, a lab and a terrier" is two dogs, not two terriers.
        breed_word = "" if pet.get("breed_of_one") else str(pet.get("breed") or "")
        animal = str(breed_word or pet.get("animal") or "").strip().lower()
        if not animal:
            continue
        for group in groups:
            if group[0] == animal:
                group[1] += count
                break
        else:
            groups.append([animal, count])
    if not groups:
        return "", False
    if len(groups) == 1 and groups[0][1] == 1 and A_VAGUE_MANY.search(str(clean or "")):
        return "", False
    parts = []
    for animal, count in groups:
        if count == 1:
            parts.append(("an " if animal[:1] in "aeiou" else "a ") + animal)
        else:
            word = animal if animal.endswith("s") else animal + "s"
            parts.append(f"{number.get(count, str(count))} {word}")
    said = ", ".join(parts[:-1]) + " and " + parts[-1] if len(parts) > 1 else parts[0]
    names = [n[:1].upper() + n[1:]
             for n in (str(pet.get("name") or "").strip() for pet in kept
                       if isinstance(pet, dict)) if n]
    if len(names) == 1:
        said += f" called {names[0]}"
    elif names:
        said += ", " + ", ".join(names[:-1]) + f" and {names[-1]}"
    many = sum(count for _, count in groups) > 1
    return said, many


def _plain(clean, memory):
    """An echo of a line with no fact in it, with a tail that fits what kind of line it is.

    Only a plain statement about their own life gets here: fallback asks this after the symptom,
    good-news, plan and trouble questions, for a line whose mood is neutral. A line that is a
    fault to troubleshoot is left to bot/compose/trouble.py, which asks the better question."""
    body = _strip_lead_in(clean)
    if not body or trouble.reads_as_trouble(clean) is not None:
        return None
    if not _about_them(body):
        return None
    if not HABIT.search(body) and not GOING.search(body):
        return None
    if OBLIGED.search(body):
        return None
    if TROUBLE.search(body) or FEELING.search(body):
        # "i cry every morning", "i shout at my kids every morning", "i get panic attacks every
        # week": a feeling or a row is not a routine to admire, and those modules say it better.
        return None
    thing = _echo(clean, memory)
    if not thing:
        return None
    if HABIT.search(body):
        options = HABIT_TAIL
    elif GOING.search(body) and not GOING_BAD.search(body):
        options = GOING_TAIL
    else:
        return None  # anything else keeps the stock line, which is right for a line with no shape
    return pick(options, memory).format(thing=thing, Thing=thing[:1].upper() + thing[1:])


def _about_them(body):
    """Whether the line is about their own life rather than the world or someone else's.

    The shape it matched is what makes it specific (HABIT or GOING), so the subject is enough
    here: "i do legs on a tuesday" and "i'm trying to save money" have no state word in them."""
    first = body.split()[0].lower().strip(",;:") if body.split() else ""
    return first in ("i", "i'm", "im", "i've", "ive", "i'd", "we", "we're", "were", "my", "our")


# "i dont know anyone here" is loneliness said as a fact, and the fact readers had nothing for it:
# the fallback answered "Got it. Is there anything you'd like a hand with?" - a shrug at the one
# line a lonely person is most likely to write. It is not a detail to file and say back either, so
# it is read before the fact frames and answered as the feeling it is.
NOBODY_AROUND = re.compile(
    r"\bi\s+(?:don'?t|do not)\s+(?:really\s+|even\s+|actually\s+)?know\s+"
    r"(?:anyone|anybody|a soul|any ?one else|a single person|one person)\b"
    r"|\bi\s*'?ve\s+(?:got|gotten)\s+no\s*(?:one|body|friends|mates)\b"
    r"|\bi\s+have\s+no\s*(?:one|body|friends|mates)\b"
    r"|\bno ?(?:one|body)\s+to\s+(?:talk|chat|go out|spend|turn)\b",
    re.I)
# The line asking who could help with something ("i dont know anyone who can look at the boiler")
# is a request for a recommendation, not a line about being alone.
NOBODY_AROUND_ASK = re.compile(r"\b(?:who|that)\s+(?:can|could|would|will|to)\b", re.I)
# "i know lots of people", "i do know someone": the same shape with the sense turned round.
ANYBODY_AT_ALL = re.compile(
    r"\b(?:know|knows)\s+(?:lots|plenty|loads|a few|some|quite a few|lots of|plenty of)\b",
    re.I)
OTHER_PERSON = frozenset("""he she they his her their hes shes theyve him them him/her""".split())
# News about somebody else that is going the right way. "my nan is in hospital" then "she should be
# out next week" was answered "I'm listening - say more if it helps", which tells the person
# nothing about the news they just gave, and "shes back at work now" was echoed back at them. The
# three shapes are different news, so each has its own pool: coming home, on the mend, back at it.
GOING_HOME = re.compile(
    r"\b(?:should|might|will|hopefully|due|going|expected|allowed)\s+(?:to\s+)?(?:be\s+)?"
    r"(?:out|home|discharged|released)\b"
    r"|\b(?:out|home|discharged|released)\s+(?:of\s+(?:hospital|there)\s+)?"
    r"(?:next week|this week|tomorrow|soon|on (?:monday|tuesday|wednesday|thursday|friday|saturday"
    r"|sunday)|in a (?:few|couple of) days|by the weekend)\b"
    r"|\bcoming home\b|\bout of hospital\b", re.I)
ON_THE_MEND = re.compile(
    r"\b(?:doing|getting|feeling|looking)\s+(?:a lot |much |a bit |so much |a little )?better\b"
    r"|\bon the mend\b|\bon the up\b|\bturned (?:a|the) corner\b|\bout of (?:the )?danger\b"
    r"|\bpicking up\b|\bback to (?:her|his|their) old self\b|\bwell on the way\b", re.I)
BACK_AT_IT = re.compile(
    r"\bback (?:at work|to work|in work|at school|on (?:her|his|their) feet|to (?:normal|it|"
    r"herself|himself|themselves|training|the gym|uni|university))\b"
    r"|\bup and about\b|\bwalking (?:again|now)\b|\bwell enough to\b", re.I)
GOING_HOME_TAIL = (
    "Out {soon} \u2014 that is the news you want. The first days at home are usually the flat ones, "
    "so keep them quiet.",
    "That is a relief. Coming home is the milestone; the tiredness tends to last a few weeks past "
    "it.",
    "Good to hear. Home beats any ward for sleeping, even with the stairs in the way.",
)
ON_THE_MEND_TAIL = (
    "Good to hear it. Recovery goes in fits and starts \u2014 a good day, then a flat one, and both "
    "are normal.",
    "That is the direction you want. Better is slower than people expect, and it counts all the "
    "same.",
    "Worth saying out loud. On the mend is the part that takes patience from everyone round them.",
)
BACK_AT_IT_TAIL = (
    "Back at it already is quick going. The first week back is the tiring one for most people.",
    "That is a good sign. Getting back to normal takes longer than people expect, and the first "
    "week of it is the hardest.",
    "Good news. Back to it \u2014 and the first week is the one to take gently.",
)


GOING_HOME_MINE = (
    "Out {soon} \u2014 good. The first days at home are the flat ones, so keep them quiet and let "
    "people bring things.",
    "That is a relief to hear. Home is where the sleep happens; the ward is not.",
)
ON_THE_MEND_MINE = (
    "Good to hear. Recovery goes in fits and starts \u2014 a good day, then a flat one, and both are "
    "normal.",
    "That is the direction you want. Better is slower than people expect, and it counts all the "
    "same.",
    "Worth saying out loud. Take the good days as they come rather than testing them.",
)
BACK_AT_IT_MINE = (
    "Back at it already is quick going. The first week back is the tiring one for most people.",
    "Good sign. Getting back to normal takes longer than people expect, so keep the first week "
    "light.",
    "Good news. Back to it \u2014 and the first week is the one to take gently.",
)
A_RELATION = frozenset("""mum mom mother dad father nan nanna granny gran grandma grandad grandpa
    son daughter kid child baby sister brother mate friend partner wife husband aunt uncle cousin
    niece nephew colleague boss neighbour neighbor lodger flatmate housemate""".split())


def _who_is_getting_better(low):
    """"them" for somebody else in the line, "me" for the speaker, "" for nobody."""
    words = set(re.findall(r"[a-z']+", low))
    if words & (OTHER_PERSON | A_RELATION):
        return "them"
    if words & frozenset(("i", "im", "ive", "me", "my", "myself")):
        return "me"
    return ""


def a_person_getting_better(clean, memory=None):
    """The pool for news that somebody is getting well, or None."""
    plain = str(clean or "").replace("\u2019", "'").replace("\u2018", "'")
    low = plain.lower()
    if not low.strip() or DEATH_WORDS.search(low):
        return None
    if not _who_is_getting_better(low):
        return None
    said = " ".join([low] + _the_words_of_the_last_two_turns(memory))
    if not re.search(r"\b(?:ill|sick|hospital|operation|op|surgery|broke|broken|stroke|chemo"
                     r"|treatment|injury|injured|fell|fall|accident|recovering|recovery|bug"
                     r"|flu|pneumonia|infection)\b", said):
        # Nothing in the chat says there was anything to get better from, so "shes better now"
        # is a line about something else entirely.
        return None
    mine = _who_is_getting_better(low) == "me"
    for pattern, theirs, ours in ((GOING_HOME, GOING_HOME_TAIL, GOING_HOME_MINE),
                                  (ON_THE_MEND, ON_THE_MEND_TAIL, ON_THE_MEND_MINE),
                                  (BACK_AT_IT, BACK_AT_IT_TAIL, BACK_AT_IT_MINE)):
        match = pattern.search(low)
        if match and not negated(low, match.group(0)):
            return _with_the_time(ours if mine else theirs, low)
    return None


def _the_words_of_the_last_two_turns(memory):
    """The person's own lines from the last two turns, lowercased, oldest first."""
    words = []
    for turn in (memory or {}).get("turns") or []:
        if isinstance(turn, dict):
            words.append(str(turn.get("user") or "").lower())
        elif isinstance(turn, str):
            words.append(turn.lower())
    return words[-2:]


def _with_the_time(pool, low):
    """The pool with the time the line gave in it ("out next week" -> "out next week")."""
    match = re.search(r"\b(next week|this week|tomorrow|soon|on (?:monday|tuesday|wednesday"
                      r"|thursday|friday|saturday|sunday)|in a (?:few|couple of) days"
                      r"|by the weekend)\b", low)
    when = match.group(1) if match else "soon"
    return tuple(line.replace("{soon}", when) for line in pool)

# A move is the commonest cause and the one the person usually names, so it is answered as the
# move rather than as a stranger in a town with no history to it.
A_MOVE = re.compile(r"\b(?:moved|moving|move|relocat|emigrat|new (?:city|town|area|job|country))",
                    re.I)
# Two pools, because a line that names a move is answered about the move: the first months are the
# part nobody warns you about, and that is worth saying to someone in them.
ALONE_AFTER_A_MOVE = (
    "The first months somewhere new are the emptiest part of a move, and it does ease off. "
    "Whatever meets weekly near you - a class, a club, a five-a-side - fills it faster than "
    "waiting to be asked.",
    "That's the hard part of moving, and nobody warns you how long it lasts. One thing you turn "
    "up to at the same time every week is how the same faces start.",
    "Being new somewhere is lonely in a way that has nothing to do with how likeable you are. "
    "Say yes to the first small invitation that comes, even the boring one.",
)
ALONE_TAIL = (
    "That's a lonely way to spend the week, and it isn't a fault in you. One message to someone "
    "you already like does more than waiting for a night out.",
    "That's a quiet way to live. The people who get to know you are the ones you see at the same "
    "time each week, so it is worth having one of those.",
    "That's hard going. Being on your own in a place with no history to it wears thin, and the "
    "way out is nearly always the same small step: one regular thing, one person you keep saying "
    "hello to.",
)


# After a death the empty week is the grief itself, and the move pool's "fill it with something
# weekly" is far too brisk for it: this is the one thing worth saying to someone in that week.
ALONE_AFTER_A_LOSS = (
    "That's the hardest part of it, the empty week afterwards. The people who knew them are "
    "usually the ones who most want to hear from you.",
    "Being on your own after something like that is a weight of its own, and it is not something "
    "to push through. A short call to someone who knew them helps more than you'd think.",
)


def nobody_around(clean, memory):
    """The pool for a line that says, as a fact, that they have nobody, or None."""
    # The line as typed carries curly apostrophes ("don’t"), and the patterns are written the
    # plain way, so they are folded here rather than in every one of them.
    plain = str(clean or "").replace("\u2019", "'").replace("\u2018", "'")
    hit = NOBODY_AROUND.search(plain)
    if not hit or NOBODY_AROUND_ASK.search(plain) or ANYBODY_AT_ALL.search(plain):
        return None
    # A line about somebody else's empty week is not this line: "hes got no one to talk to at
    # work" wants something said about him, and the reply for the speaker would be a stranger's
    # comfort handed to the wrong person.
    if set(plain[:hit.start()].split()) & OTHER_PERSON:
        return None
    if negated(plain, hit.group(0)[:12]):
        return None  # "i dont not know anyone" - a doubled denial is not this line
    said = " ".join([plain] + [str(one or "") for one in (memory.get("turns") or [])[-2:]])
    if DEATH_WORDS.search(said):
        return ALONE_AFTER_A_LOSS
    return ALONE_AFTER_A_MOVE if A_MOVE.search(said) else ALONE_TAIL


_WORDS = re.compile(r"[a-z']+")


# A line said to the bot rather than about the person: "youre on form today", "youre off your
# game today", "you seem cheerful". The store took the second person for the first and filed it
# ("you're on form today" came back "Noted: you're on form today."), which hands somebody their
# own words with the wrong subject on them, and it kept the turn from the readers that answer
# lines aimed at the bot (bot/memory/warmth.py). Only a line that opens on the bot counts, and
# only when nothing in it is the person's own: "you were right, i do need to book it" is about
# them as well, and "my" makes it their life being talked about ("youre so patient with my mum").
_THE_BOT_AS_SUBJECT = re.compile(
    r"^\s*(?:(?:oh|aw+|ah|ha+|tbh|honestly|ok|okay|well|and|but|so|yeah)[,\s]+)*"
    r"you(?:'?re| are| were| seem| look| sound| make| keep| always| really| definitely)\b",
    re.I)
_SOMEONE_ELSE_IN_IT = re.compile(r"\b(?:i|im|i'm|i've|ive|i'd|we|we're|our|my|mine)\b", re.I)


def _said_to_the_bot(clean):
    """Whether the line opens on the bot and has nothing of the person's life in it."""
    if not _THE_BOT_AS_SUBJECT.match(clean or ""):
        return False
    return not _SOMEONE_ELSE_IN_IT.search(clean or "")


def _no_subject(clean, memory=None):
    """Whether the line opens with a helper and nothing that can be a subject: "was out all day".

    Saying the thing back needs somebody in it. People leave the subject off a short line
    ("am shattered", "was out all day", "have no idea"), and handing it back as it stands - "Got
    it - were shattered after the move" - reads worse than the stock line it replaced. The
    understanding engine already knows the shape (it puts the "i" back for its own reading),
    so this asks it instead of listing the helpers a second time.
    """
    understood = memory.get("understood") if isinstance(memory, dict) else None
    if isinstance(understood, dict) and understood.get("dropped_subject"):
        return True                  # "am thinkin of jackin in me job": the "i" is the bot's
    words = [word for word in _WORDS.findall(_repaired(clean, memory).lower()) if word]
    while words and words[0] in LEADERS:
        words = words[1:]
    return bool(words) and opens_without_subject(words, 0)


def _asked_last(memory):
    """Whether the bot's last reply ended on a question, so this one must not ask another."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1] if isinstance(turns[-1], dict) else {}
    return str(last.get("bot") or "").strip().endswith("?")


def _a_diary_plan(found, clean):
    """The endings an appointment or a visit wants, or None when the plan is something else.

    A plan that names a day and nothing else is either a thing in the diary - the dentist, a scan,
    an interview, a haircut - or one of their people coming to stay. Both were filed and handed
    back ("Noted: the dentist is on tuesday.", "Noted: your mum's coming on friday."), which tells
    the person nothing about the thing they have just put in their week. What is still open is the
    time, or how long the visit lasts, so that is what the ending asks. A plan with no day in the
    line ("i want to save for a house") is a project and keeps the reply it has.
    """
    if not isinstance(found, dict) or not found.get("plan"):
        return None
    said = " ".join(str(clean or "").lower().split())
    if not said or not DATE_AHEAD.search(said):
        return None
    if set(re.findall(r"[a-z']+", said)) & PAST_PLAN:
        return None
    who = None
    named = re.search(r"\b(?:my|our)\s+([a-z]+)", said)
    if named:
        # "my mums coming" and "my sister's coming" name the same person as "my mum" does, so the
        # possessive and the plural come off before the word is looked up in the relations.
        word = named.group(1)
        person = next((one for one in (word, re.sub(r"'s$", "", word), word[:-1])
                       if one in facts.RELATIONS), "")
        # Coming home is not a visit: the person is not staying with them, they live there.
        at_home = re.search(r"\b(?:coming|heading|getting|moving|flying) (?:back )?home\b", said)
        if person in facts.RELATIONS and COMING_TO_STAY.search(said) and not at_home:
            who = ("they" if _more_than_one_coming(said, named.end(), word) else
                   "she" if person in facts.SHE and person not in facts.HE else
                   "he" if person in facts.HE and person not in facts.SHE else "they")
    if who == "they":
        return VISIT_TAIL_MANY
    if who:
        return tuple(one.replace("{who}", who) for one in VISIT_TAIL_ONE)
    if DIARY_THING.search(said):
        return DIARY_TIME_TAIL if DIARY_TIME.search(said) else DIARY_TAIL
    if re.search(r"\b(?:meet|meeting|seeing)\b", said):
        return MEETING_TAIL if DIARY_TIME.search(said) else MEETING_TIME_TAIL
    if set(re.findall(r"[a-z']+", said)) & OCCASIONS:
        # A day with an occasion on it and no travelling in the line - "my sister's wedding is
        # next june" - is still a date the person is counting towards.
        return OCCASION_TAIL
    return None


def _plan_tails(found, clean, memory):
    """The endings a trip or an occasion wants, or None when the line is another kind of plan.

    Everything else the store filed as a plan - "i want to save for a house", "im going to
    start running" - is a project with a first step and keeps its own reply, which the composer
    gives it.
    """
    kind = reads_as_a_trip(clean)
    if kind == "trip":
        options = TRIP_TAIL
    elif kind == "occasion":
        options = OCCASION_TAIL
    elif kind == "occasion_flat":
        options = OCCASION_FLAT_TAIL
    else:
        options = _a_diary_plan(found, clean)
        if not options:
            return None
    if HOW_LONG_ALREADY.search(clean):
        options = tuple(one for one in options if "how long" not in one.lower()) or options
    if _asked_last(memory):
        # Two questions in a row is an interrogation: say the thing they can use instead.
        options = tuple(one for one in options if not one.endswith("?")) or options
    return options


# A body that troubles them is not a thing they own: "i have an abscess on my leg" came back
# "Noted: you have an abscess on your leg", which is the coldest reply there is. The symptoms the
# other modules answer are read by badnews.reads_like_a_symptom; a word no list has yet is caught
# by the understanding engine's own topic, so the guard is the topic rather than a longer list.
#
# A thing they had is a story, not a possession: "we had a small wedding last year" was answered
# "Noted: you had a small wedding last year", and a friend asks about the day instead.
PLACED_IN_THE_PAST = re.compile(
    r"\b(?:last (?:year|summer|winter|spring|autumn|month|week|night)|years ago|months ago|"
    r"weeks ago|back in|when i was|used to)\b", re.I)


def _about_a_body(read, memory=None):
    """Whether the line is the person's own body or health, however it words it."""
    try:
        read_it = understanding(read, memory if isinstance(memory, dict) else {})
    except Exception:  # noqa: BLE001 - a reading that fails is not a reason to echo a symptom
        return False
    return isinstance(read_it, dict) and read_it.get("topic") == "health"


# "I've got a bathroom to sort out", "i have a loft to clear out", "i have a tax return to do":
# the thing is not a possession, it is a job on their list, and saying it back - "Noted: you've got
# a bathroom to sort out" - is the filing cabinet STYLE.md rules out. The tail is chosen by the
# shape (`have` + a thing + `to` + a verb) and never by the topic word, so one pool fits a loft, a
# tax return and a bike, and the person gets a friend's question about the job rather than their
# own words back.
JOB_TO_DO = re.compile(
    r"\bto\s+(?:sort|fix|clear|clean|paint|do|tidy|finish|replace|handle|deal\s+with|"
    r"get\s+(?:rid\s+of|done|sorted)|put\s+up|take\s+down|strip|sand|wire|plumb|service|"
    r"return|file|chase|book|renew|sell|pack|prepare|plan|write|organise|organize|arrange|"
    r"fill\s+(?:in|out)|sign|complete|send\s+(?:off|back)|post\s+off|"
    r"build|assemble|learn|study|wrap|draft|collate|make|iron|wash|mow|weed|dig|tile|grout|"
    r"seal|hang|fit|install|mount|mend|sew|hem|scrub|hoover|vacuum)\b", re.I)
# The first tail asks whether the job is the weekend's, and that question is already answered when
# the line names the day: "i have a report to write for friday" was offered "is that the weekend,
# or are you fitting it in around work?" - a question the line had just said the answer to.
JOB_HAS_A_DAY = re.compile(
    r"\b(?:today|tonight|tomorrow|tmrw|this\s+(?:week|weekend|month|evening)|next\s+week|"
    r"weekend|by\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|the\s+end)|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|the\s+end\s+of\s+the\s+month)\b",
    re.I)
JOB_TAIL = (
    "{Thing} \u2014 is that the weekend, or are you fitting it in around work?",
    "{Thing}. Do you know where to start with it, or is that the hard part?",
    "{Thing} \u2014 what's the first thing that needs doing?",
    "{Thing}. Is it a bigger job than it looked?",
)


# What the person says about the job they had before. A job said in the past is the strongest
# thing in the line and the store keeps it (`facts.JOB_WAS`), but the receipt pools answered it as
# a day that has happened - "i was a teaching assistant before the kids" got "How was it,
# overall?" and "i was a nurse" got "Good to hear. What was the best bit?", which is a verdict on
# a life rather than an answer. The word that says when ("before the kids", "until 2019") is what
# makes the line a job they had rather than the job they have, so it also decides which pool.
JOB_BEFORE = re.compile(r"\bbefore\s+(?:the|my|we|i|having|that)\b|\b(?:until|till|up to)\s+\d",
                        re.I)
PAST_JOB = (
    "{X} — that is a real thing to have behind you. What has changed since then?",
    "{X} is not nothing to have behind you. Whatever comes next, you are not starting from the "
    "bottom of anything.",
    "{X}, then. You know that work from the inside, which counts for more than it looks.",
)
# The job comes out of the store without its article ("nurse", "teaching assistant"), so no line
# in these pools can put it in the middle of a sentence - "You were nurse" and "So it is
# receptionist you did before" are the kind of line that makes the bot sound like a form. The job
# opens the sentence instead, and every line starts with `{X}`.
# Nothing here says they want to go back. "i was a receptionist before i had the kids" explains a
# gap in a life; it is not a plan, and answering it with "what would have to be true for you to go
# back to it" hands somebody a decision they did not bring.
PAST_JOB_PLAIN = (
    "{X} — that is not nothing to have behind you. Do you miss it, or are you glad to be out of "
    "it?",
    "{X} is a thing you already know how to do, which is more than most people start with.",
    "{X}, then. What is it that has you thinking about it now?",
)


def the_job_they_had(clean, memory):
    """A job the person said they used to do, answered as that, or None.

    The reading is the store's own (`facts.JOB_WAS` and the job `facts.extract` keeps), so a line
    this answers is a line the store filed: a job word, said in the past, about the person and
    not about somebody else, and not a question.
    """
    if not isinstance(clean, str) or "?" in clean:
        return None
    if not facts.JOB_WAS.search(clean):
        return None
    job = " ".join(str(facts.extract(clean).get("job") or "").split())
    if not job:
        return None
    if job.split()[0].lower() in facts.WAS_NOT_A_JOB:
        return None
    pool = PAST_JOB if JOB_BEFORE.search(clean) else PAST_JOB_PLAIN
    return pick(pool, memory, seed_text=clean).format(
        x=job, X=job[:1].upper() + job[1:])


def a_job_to_do(text, memory=None):
    """A thing with something still to be done to it, as the job it is, or None.

    Every lane that has to know whether a line is a job on the person's list rather than an
    appointment to get ready for reads it here, so one gate decides it for all of them.
    """
    try:
        return _a_job_to_do(text, memory)
    except Exception:  # noqa: BLE001 - a reading that cannot be made answers nothing
        return None


def _a_job_to_do(clean, memory=None):
    """A thing with something still to be done to it, answered as the job it is.

    "i have got a loft to clear out" is not a possession - it is a job on their list - and the
    receipt it used to get ("Noted: you've got a loft to clear out") is the filing cabinet
    STYLE.md rules out. The same gate as `_a_thing_they_have` decides it is a thing at all; then a
    verb of doing after "to" makes it a job, and the reply is the question a friend asks about a
    job. It is asked here, before the fact paths, so a line about the person's evening in front of
    it cannot change the reading.
    """
    read = _spoken(_repairs(clean, memory)) or clean
    if not JOB_TO_DO.search(read):
        return None
    match = HAVE_THING.search(read)
    if not match:
        return None
    thing = match.group(1).lower().strip("-'")
    if not thing or thing in NOT_A_THING or thing.isdigit():
        return None
    if _about_a_body(read, memory) or PLACED_IN_THE_PAST.search(read):
        return None
    if HABIT.search(read):
        return None  # "i have a lawn to mow every week" is a routine, and has its own reply
    what = _echo(clean, memory)
    if not what:
        return None
    # The bot says it in the person's own contraction: "you've got a wardrobe to put up", never
    # "you have a wardrobe to put up".
    what = HAVE_A.sub(r"\1've got a", what)
    tails = JOB_TAIL[1:] if JOB_HAS_A_DAY.search(read) else JOB_TAIL
    return pick(tails, memory, seed_text=read).format(
        thing=what, Thing=what[:1].upper() + what[1:])


# A receipt is a claim to have kept something, and said as the first line of a chat both of these
# claim a thing the chat has never named: "hes 9" was answered "Noted: he's 9." and "we have two of
# them" was answered "Noted: you have two of them." There is no "he" in the chat for the age to
# belong to and no "them" for the two to be two of, so the note is about nobody - and for the
# second one it is false as well, because the next line, "how many do we have", is answered "You
# haven't told me about a pet yet." The age is the milder case: it is kept with no name on it, and
# "how old is he" reads back "He is 9." about a person the bot cannot call anything. What is
# missing is the person or the thing, so the reply asks for it, with the figure in it when the line
# gave one: "Who's 9?" is the question a friend asks, and "Who do you mean?" is the one a form
# asks.
WHO_THE_FIGURE_IS = (
    "Who's {figure}?",
    "{Figure} \u2014 who's that?",
)
WHO_IS_IT = (
    "Who do you mean?",
    "Who's that, then?",
    "Who are we talking about?",
)
WHAT_OF_THEM = (
    "{Count} of what?",
    "{Count} of what, sorry?",
)
WHICH_ONES = (
    "Which ones do you mean?",
    "Which one do you mean?",
)
# The words that point back and name nothing. "we have two of them" means nothing at all until
# the chat has said what they are, and a note said back from it is the bot pretending it knows.
POINTS_BACK = re.compile(r"\b(?:them|those|these|ones|it)\b", re.I)
A_COUNT_OF_THEM = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a few|a couple|\d{1,3})"
    r"\s+of\s+(?:them|those|these)\b", re.I)


# A figure with a day still to come attached to it is a birthday somebody is counting down to:
# "she is 5 next month" was answered "She is 5 next month. Plenty of time, anyway.", which is
# about the day and claims nothing about the store. The same figure with no day ("hes 9") is the
# one that was noted back as a fact nobody had kept.
A_DATE_STILL_TO_COME = re.compile(
    # "shes turning 6" is a birthday still to come with no day said for it: the word "turning" is
    # the countdown itself. Read as a plain figure it was a fact nobody had kept, so a line whose
    # whole point was the coming birthday was answered "Who's 6?".
    r"\b(?:turning|turns)\s+(?:\d{1,3}|[a-z]+)\b"
    r"|\b(?:next|this)\s+(?:week|month|year|weekend|summer|christmas|spring|autumn|winter)\b"
    r"|\b(?:in|by|until|till)\s+(?:the\s+)?(?:new\s+year|summer|christmas)\b", re.I)


def _the_chat_holds_something(memory):
    """Whether a line was said before this one, so a pointer in this line can point at it.

    The rule this serves is the operator's: a reply that leans on what was said earlier needs
    something said earlier, and on a first message there is nothing, so the line itself has to be
    answered. `memory` on a first turn is not empty - the understanding, the facts read from the
    line and the topic are all in it before anybody composes a reply - so the turns said before
    this one are the thing to ask about.
    """
    return there_is_a_chat(memory)


def _the_pronoun_points_at_somebody(low, memory):
    """Whether a pronoun in this line can point at a person or an animal the chat has named.

    The store reads "she"/"he" against the people in the chat, and this asks the same reader, plus
    the two things it does not cover: an animal, which is a "he", a "she" or an "it" as far as the
    words go ("my cat has stopped eating" then "she's 12" is about the cat), and a "they", which
    is the group the chat has been naming ("something with the kids" then "theyre 6 and 9").
    """
    if _person_from_pronoun(low, memory):
        return True
    held = memory or {}
    theirs = held.get("user") if isinstance(held.get("user"), dict) else {}
    if any(isinstance(pet, dict) for pet in (theirs.get("pets") or [])):
        return True
    # A "he"/"she"/"his"/"her" points at the person the chat has already named, whether or not the
    # store has a fact about them yet. "i cant get my kid to sleep" then "hes 3" was answered
    # "Who's 3?" - the age asked whose it was two turns after the person said whose it was, and the
    # one thing the answer needed was already in the chat. The person words are read off the last
    # few turns the person typed, and a pet word counts with them ("my cat has stopped eating" then
    # "shes 12" is the cat, which is the reading the docstring above promises).
    fits = None
    if re.search(r"\b(?:she|shes|she's|her)\b", low or "", re.I):
        fits = facts.SHE
    elif re.search(r"\b(?:he|hes|he's|his)\b", low or "", re.I):
        fits = facts.HE
    if fits:
        said = " ".join(str((turn or {}).get("user") or "").lower()
                        for turn in (held.get("turns") or [])[-4:])
        for word in sorted(PERSON_WORDS.union(CHILD), key=len, reverse=True):
            if not re.search(r"\b" + word + r"\b", said):
                continue
            # The pronoun has to be one the person named can carry: "my mum is 60" then "hes 9" is
            # still a he nobody in the chat fits, and the question that asks whose age it is is
            # right. A word that names no gender ("kid", "toddler", "baby") carries either.
            if _pronoun_fits(word, fits):
                return True
    if not re.search(r"\b(?:they|theyre|they're|them|their|theirs|those|these)\b", low or "", re.I):
        return False
    words = set(re.findall(r"[a-z']+", low or ""))
    for turn in (held.get("turns") or [])[-4:]:
        words |= set(re.findall(r"[a-z']+", str((turn or {}).get("user") or "").lower()))
    for word in words:
        if word in PERSON_GROUP or word in CHILD:
            return True
    return any(str(entry.get("who") or "").strip() and not str(entry.get("who")).endswith("s")
               for entry in (held.get("others") or []) if isinstance(entry, dict))


def _somebody_was_being_hurt(memory):
    """Whether the line before this one said somebody is doing the person harm.

    "the kids at school pick on her" is a line about one person, and the store keeps nobody from
    it because she is only "her" - so the next line's "she" points at that person and at nobody
    else. This is the same room `_heavy` reads, for a line that names a figure instead of a fact.
    """
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)] \
        if isinstance(memory, dict) else []
    if not turns:
        return False
    return reads_as_cruelty(str(turns[-1].get("user") or ""))


def _who_the_figure_is(found, memory, low):
    """The question that asks who an age or a height belongs to, or None.

    Only for a reading that names nobody: "an age, of a person" with no person in it. The store
    keeps "my son is 9" against the son and drops "hes 9" when the chat holds no "he", so the
    note for the second one is about a fact nobody kept. `_person_from_pronoun` is the reader the
    store itself uses, so a chat that has the person - "my son is called tom" then "hes 9" - is
    left to the receipt it deserves.
    """
    entries = found.get("others") if isinstance(found, dict) else None
    if not entries:
        return None
    if SOMEONE_MILESTONE.search(low or "") or A_DATE_STILL_TO_COME.search(low or ""):
        # "she is 5 next month" is a milestone somebody is looking forward to, and the ending it
        # gets - "Plenty of time, anyway." - is said about the coming birthday, not a receipt for
        # a fact in the store, so it does not claim anything that was not kept.
        return None
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("who"):
            continue
        figure = entry.get("age") or entry.get("height")
        if not figure:
            continue
        if entry.get("pronoun") and _the_pronoun_points_at_somebody(low, memory):
            return None  # somebody in the chat fits the pronoun, so this is a fact about them
        if entry.get("pronoun") and _somebody_was_being_hurt(memory):
            # The chat holds no person to name because the line before named one by pronoun only:
            # "the kids at school pick on her" then "shes 7" was answered "7 - who's that?", which
            # asks the person to introduce their own child in the middle of saying what is
            # happening to her. The room says there is exactly one person this is about - the one
            # being hurt - so the age is hers and is answered as hers.
            pron = str(entry.get("pronoun") or "").strip().lower()
            said = ("%s's %s" % (pron, figure)) if isinstance(figure, int) else ""
            if said:
                return pick(HEAVY_FRAMES, memory, seed_text=low).format(
                    thing=said, Thing=said[:1].upper() + said[1:])
            return None
        if isinstance(figure, int) and figure:
            return pick(WHO_THE_FIGURE_IS, memory, seed_text=low).format(
                figure=str(figure), Figure=str(figure))
        return pick(WHO_IS_IT, memory, seed_text=low)
    return None


def _what_the_pointer_is(read, memory):
    """The question that asks what a bare "them" names, or None.

    Only while the chat holds nothing: once there are turns, "them" points at something the
    person said, and a chat that has a thing in it is not this reader's business.
    """
    if _the_chat_holds_something(memory):
        return None
    if not POINTS_BACK.search(read or ""):
        return None
    count = A_COUNT_OF_THEM.search(read or "")
    if count:
        counted = count.group(1)
        return pick(WHAT_OF_THEM, memory, seed_text=read).format(
            Count=counted[:1].upper() + counted[1:])
    return pick(WHICH_ONES, memory, seed_text=read)

# A condition they only wonder about is a question, not a fact. "i think i have diabetes" was
# said straight back - "Noted: you think you have diabetes" - which is the coldest reply there is
# and no answer at all, and "i think i have depression" came back a turn later in "what do you
# know about me". The line is asking whether it is diabetes, so it is answered: the thing is
# named, and the answer says who can actually tell them and what to take to the appointment.
A_WONDERED_CONDITION = re.compile(
    r"\bi\s+(?:think|believe|reckon|suspect|might|may)\b[^.!?,;]{0,30}?\b"
    r"(?:i(?:['\u2019]?ve|\s+have)?\s+)?(?:have|got)\s+(?P<thing>[a-z][a-z'\u2019 \-]{2,30})",
    re.I)
# The same line saying no: "i don't think i have depression" is not a worry to answer.
A_WONDER_SAID_NO = re.compile(
    r"\b(?:don'?t|do not|didn'?t|did not|never|not)\s+(?:think|believe|reckon|suspect)\b"
    r"|\bnot sure\b|\bno idea\b", re.I)
# An article in front of the thing is often a thing rather than a condition ("i think i have a
# meeting at 3", "a parcel coming", "a bill"), so a phrase that takes one has to earn its place: a
# condition kind at the end of it ("an eating disorder", "a chest infection") or one of the sets
# of initials a condition is known by, which no errand ever is.
WITH_AN_ARTICLE = frozenset("a an the some any my our his her their this that these those".split())
A_CONDITION_KIND = re.compile(r"(?:disorder|syndrome|disease|infection|deficiency|condition|"
                              r"intolerance|allergy|virus|ulcer|fracture|clot|itis|concussion|"
                              r"hernia|mole|reaction|abscess|boil|polyp|stones?)$")
# The conditions that go by their initials. A short word with an odd vowel in it is no signal on
# its own - "a bill", "a cyst", "a milk" - so the ones that are initials are named, and they are
# written back in capitals because that is how they are written.
CONDITION_INITIALS = frozenset("""sti dvt uti hiv ibs ocd adhd ptsd ms me cf ibd copd gerd pnd
    tmj pcos""".split())
# Where to send them depends on what is being wondered about, because the way in is what the
# person actually needs: an assessment, a test, or a GP. A condition names its own family; none
# of this is written for one phrasing.
CONDITION_FAMILIES = (
    (re.compile(r"\b(?:depression|depressed|anxiety|ptsd|adhd|autism|autistic|bipolar|ocd|"
                r"eating|anorexi\w*|bulimi\w*|burnout|self.?harm)\b"), (
        "Whether it's {thing} isn't something I can judge from a chat - that takes a proper "
        "assessment, and the way in is a GP appointment or a self-referral to talking therapy. "
        "Say how long it has been like this and what has changed; that is where the assessment "
        "starts.",
        "I can't diagnose {thing} and a guess would be no use to you. Book a GP appointment and "
        "ask about a referral; with something like this the waiting list is the annoying part, "
        "so the useful move is to get in the queue now rather than when it gets worse.")),
    (re.compile(r"\b(?:sti|hiv|chlamydia|gonorrhoea|gonorrhea|herpes|syphilis|thrush|warts|"
                r"piles|haemorrhoids|hemorrhoids)\b"), (
        "I can't tell you from here whether it's {thing}. Get it checked: a sexual health "
        "clinic sees you without a GP referral, the test is quick and usually free, and they "
        "can treat it there too.",
        "Whether it's {thing} is a test question, not a chat one. Clinics do free, confidential "
        "testing and you can walk in without a referral - go sooner rather than later, because "
        "most of these are easy to sort once you know what it is.")),
    (None, (
        "Whether it's {thing} is a doctor's call, not something a chat can settle. Book an "
        "appointment and take a note of when it started and what has changed - that is what "
        "turns a hunch into an answer.",
        "I can't tell you whether you have {thing}, and a guess would be worse than no answer. "
        "Get it looked at - a GP or a walk-in clinic - and write down how long it has been going "
        "on first, because that is the first thing they ask.",
        "Whether it's {thing} is not something I can say from here - that needs someone who can "
        "examine you or run a test. Book it, and take three things: when it started, what has "
        "changed, and what you want out of the appointment.")),
)


def _the_route_for(thing):
    """The frames that suit the kind of condition being wondered about."""
    low = thing.lower()
    for family, frames in CONDITION_FAMILIES:
        if family is not None and family.search(low):
            return frames
    return CONDITION_FAMILIES[-1][1]


def _the_entry_names(entry, head):
    """Whether the entry that answered the line is about this thing at all.

    "i think i have an eating disorder" reached an entry about cities, so a card being in reach
    is not the same as the card being about the worry. An entry that will not say is taken at its
    word.
    """
    keys = getattr(entry, "key", ())
    if not keys:
        return True
    if head in keys:
        return True
    for word in keys:
        if len(word) > 3 and (word[:4] == head[:4] or word[:5] == head[:5]):
            return True
    return False


def _a_condition_they_wonder_about(clean, memory=None):
    """The answer to "i think i have <condition>", or "" when this is not that line.

    Only the lines nothing else can answer come here: a line the knowledge base has an entry
    for is answered from it ("i think i have gout" is answered about gout), and a symptom word
    is the bad-news or chat pool's turn ("a chest infection" keeps its own answer).
    """
    if not clean or A_WONDER_SAID_NO.search(clean):
        return ""
    match = A_WONDERED_CONDITION.search(clean)
    if not match:
        return ""
    words = " ".join(match.group("thing").lower().split()).strip("-' ").split()
    if not words:
        return ""
    article = words[0] if words[0] in WITH_AN_ARTICLE else ""
    if article:
        words = words[1:]
    if not words:
        return ""
    head = words[-1]
    if head in NOT_A_THING or head.isdigit():
        # "i think i have time", "i think i have a meeting at 3": not a condition at all.
        return ""
    if any(word in NUMBER_WORDS for word in words) or any(ch.isdigit() for ch in head):
        # "i think i have two left": a count, not a thing they have.
        return ""
    if any(word in VERBISH for word in words) and not A_CONDITION_KIND.search(head):
        # "i think i have left my keys at work", "a parcel coming": the phrase has a verb in it,
        # so it is something they did or are doing, not a condition they are wondering about.
        return ""
    initials = head in CONDITION_INITIALS
    if article and not (A_CONDITION_KIND.search(head) or initials):
        return ""
    if reads_like_a_symptom(clean.lower()):
        return ""
    entry = topics.an_entry_for(clean)
    if entry is not None and _the_entry_names(entry, head):
        # An entry already answers this line, and it knows more about the condition than a line
        # about who can tell them does.
        return ""
    phrase = " ".join([head.upper() if initials else word for word in words])
    if article:
        phrase = article + " " + phrase
    return pick(_the_route_for(phrase), memory, phrase).format(thing=phrase)


def _a_thing_they_have(clean, memory=None):
    """A thing they have, said back: "i have a bike" -> "Noted: you have a bike".

    Only when the line is the thing and nothing else: the thing word has to be a thing (not a
    feeling, an idea, a question or a body that hurts), and what is behind it is the rest of the
    line or nothing.
    """
    read = _spoken(_repairs(clean, memory)) or clean
    match = HAVE_THING.search(read)
    if not match:
        return None
    thing = match.group(1).lower().strip("-'")
    if not thing or thing in NOT_A_THING or thing.isdigit():
        return None
    if _about_a_body(read, memory) or PLACED_IN_THE_PAST.search(read):
        return None
    if HABIT.search(read):
        # A repeating time makes the line a routine, not a thing they have: "i have two
        # digestives with my tea every afternoon" is answered by the habit tail ("that's a
        # habit now"), and saying it back as a bare receipt - "Noted: you have two digestives
        # with my tea every afternoon" - was a regression that took the shape away from every
        # routine typed as a "have" line.
        return None
    what = _echo(clean, memory)
    if not what:
        return None
    pointer = _what_the_pointer_is(read, memory)
    if pointer:
        return pointer
    return pick(FRAMES, memory).format(thing=what, Thing=what[:1].upper() + what[1:])


# A limit raised, said without the word "budget": "i could stretch to 600", "we can go up to
# 900 at a push" (`STRETCH_BUDGET` in bot/memory/facts.py). The raised figure is the same kind of
# money as the limit it raises, so the line it raises decides its ending: without this, a laptop
# budget of 500 and then "i could stretch to 600" got "fixed bills and food first, then
# savings", because the earlier line's word "budget" was read as the money-topic signal.
RAISED = re.compile(r"\b(?:stretch\s+(?:it\s+)?(?:up\s+)?to|go\s+up\s+to|"
                    r"push\s+(?:it\s+)?(?:up\s+)?to)\b", re.I)


def _a_spending_budget(clean, memory):
    """Whether a stated budget is money to spend on a thing rather than a month to live inside.

    Asked once, where the budget frame is chosen, so every way of stating a budget gets the same
    reading: the period decides it when the line names one, and otherwise the conversation does.
    """
    if PERIOD.search(clean or "") or A_SPAN_OF_TIME.search(clean or ""):
        return False
    # A line that says what they mean to spend is about a thing, not about a month to live inside:
    # "i only want to spend 200 pounds" arrived with the living ending - "fixed bills and food
    # first, then savings" - in a chat that had just asked what a good bike costs. The period is
    # what makes it a month to live on, and that is checked first, so "i want to keep it to 300 a
    # month" keeps the living reading.
    if (facts.INTENDED_SPEND.search(clean or "") or facts.THE_THING_MAY_COST.search(clean or "")
            or facts.ALL_I_CAN_DO.search(clean or "")):
        return True
    if FOR_A_THING.search(clean or ""):
        # The line names what the money is for, so it is money to spend on that thing.
        return True
    recent = [clean or ""]
    for turn in (memory.get("turns") or [])[-3:] if isinstance(memory, dict) else []:
        if isinstance(turn, dict):
            recent.append(str(turn.get("user") or ""))
    for topic in (memory.get("topics") or [])[-2:] if isinstance(memory, dict) else []:
        if isinstance(topic, dict):
            recent.append(str(topic.get("text") or ""))
    said = (clean or "").strip().lower()
    others = [line for line in recent if line.strip().lower() != said]
    if RAISED.search(clean or ""):
        for line in others:
            if FOR_A_THING.search(line) or BUYING.search(line):
                return True
            if PERIOD.search(line) or A_SPAN_OF_TIME.search(line):
                return False
    if MONEY.search(" ".join(others).lower()):
        return False
    return bool(BUYING.search(" ".join(recent).lower()))


def _frames(found, heavy=False, clean="", memory=None):
    """Which set of endings this fact wants: a limit is answered with what the bot does with it."""
    if found.get("budget"):
        return SPENDING_FRAMES if _a_spending_budget(clean, memory) else BUDGET_FRAMES
    condition = str(found.get("condition") or "").lower()
    if condition in CONDITION_FOOD:
        return CONDITION_FRAMES
    if found.get("diet") or found.get("allergies"):
        # "no alcohol" is a drink, and only a diet that names a drink gets the food out of the line.
        if "alcohol" in str(found.get("diet") or "").lower():
            return DRINK_FRAMES
        return FOOD_FRAMES
    if heavy and not _just_a_liking(found):
        # A death or a separation two turns back: the fact comes back, "noted" does not. Only for
        # a fact about the family the loss named - a pet or a job is not one more thing landing
        # on them, and claiming it is read as a mistake (see STILL_FRAMES).
        return HEAVY_FRAMES if _about_the_family(found) else STILL_FRAMES
    # Somebody else's limit is a limit all the same: what the person told the bot is that there is
    # a thing to cook or plan around, so it is answered with what the bot does with it.
    if any(isinstance(entry, dict) and entry.get("allergies")
           for entry in (found.get("others") or [])):
        return OTHER_LIMIT_FRAMES
    if _about_someone_else(found, clean):
        if SOMEONE_GOOD.search(str(clean or "")):
            return SOMEONE_TAIL
        if _the_milestone(clean):
            return SOMEONE_MILESTONE_TAIL
        if _a_visit(clean):
            return VISIT_TAIL
    if _a_workplace(found, heavy, memory):
        # Which ending the line gets is the line's own, so the four pools do not open every
        # conversation about a job with the same sentence: the first turn of a chat has no
        # history for bot.compose.pick to vary on, and "what's a normal day like?" for every
        # workplace line in the deck reads as a script. Same line, same reply.
        step = len(clean or "") % len(WORK_FRAMES)
        return WORK_FRAMES[step:] + WORK_FRAMES[:step]
    coming = _a_day_coming(clean)
    if coming:
        return coming
    if _only_a_liking(found) and a_liked_thing(found) and _a_like_of_one_thing(clean, memory):
        # Which ending is the line's own, the way the workplace pool rotates: the first turn of a
        # chat has no history for bot.compose.pick to vary on, and one ending for every like in
        # the deck reads as a script.
        step = len(clean or "") % len(LIKES_FRAMES)
        return LIKES_FRAMES[step:] + LIKES_FRAMES[:step]
    return FRAMES


# The person told about by the line: "my mums birthday is next week" files nothing, and it is
# still their mum's news rather than theirs.
THEIRS = re.compile(
    r"\b(?:my|our)\s+(?:mum|mom|mam|mother|dad|father|son|daughter|sister|brother|wife"
    r"|husband|partner|aunt|uncle|gran|granny|grandma|grandad|grandpa|nan|cousin|niece|nephew"
    r"|mate|mates|friend|neighbour|neighbor|colleague|boss|stepson|stepdaughter|stepdad|stepmum"
    r"|boyfriend|girlfriend|fiance|fiancee)(?:'?s)?\b", re.I)


def _about_someone_else(found, clean=""):
    """Whether the line's fact is about a person of theirs rather than about the person typing.

    A win of their own is answered by the composer's own good-news pools (`reads_as_good_news`
    declines it here), so only somebody else's is read: their son, their mum, their neighbour.
    """
    for key in ("people", "others", "kids", "relations"):
        if (found or {}).get(key):
            return True
    return bool(THEIRS.search(str(clean or "")))


def _a_visit(clean):
    """Whether the line is a visit announced, rather than a lift or a question.

    A question is not news ("when is my sister coming" asks the bot what it cannot know), and the
    errand on the way past is not a visit ("my mum is coming to pick me up").
    """
    said = str(clean or "")
    if not said.strip() or said.rstrip().endswith("?") or NOT_A_VISIT.search(said):
        return False
    if re.match(r"\s*(?:when|what|how|why|where|who|is|are|does|do|will|did)\b", said, re.I):
        return False
    return bool(SOMEONE_COMING.search(said))


def _the_milestone(clean):
    """A round birthday or an anniversary of somebody else's, which is not the same as an age.

    "my son is 9" is a fact to keep; "my mum is 70 next week" is a thing people make something
    of, and "my son got a prize at school" is news rather than a milestone.
    """
    return bool(SOMEONE_MILESTONE.search(str(clean or "")))


def _a_workplace(found, heavy=False, memory=None):
    """Whether the line told the bot where the person works, and nothing else.

    Only the place the work is in: the store keeps it beside the job ("in a warehouse", "at
    tesco"), so those words are the tell. A line that files something else as well - an age, a
    pet, a place they live - keeps the plain frames, because the thing said back is then two
    facts and a workplace ending answers only one of them. A hard week two turns back keeps its
    own endings as well: there the apology is the reply, whatever was filed.
    """
    if heavy or not isinstance(found, dict) or not found.get("job"):
        return False
    rest = [key for key, value in found.items()
            if value and key != "job" and not key.endswith("_frame")]
    if rest:
        return False
    frame = ""
    if isinstance(memory, dict):
        known = memory.get("user") if isinstance(memory.get("user"), dict) else {}
        frame = str(known.get("job_frame") or "").strip().lower()
    return bool(frame) and frame.split()[0] in WORK_PLACE


# The keys of facts.extract() that name a person of theirs: the family a death leaves behind.
FAMILY = ("people", "others", "kids", "relations")


def _about_the_family(found):
    """Whether the fact filed is about a person of theirs rather than a pet, a job or a taste.

    "my son is 9" after a death is the family the death named, and the apology belongs on it.
    "i have two cats" and "i work in a shop" are the person telling you about their life, and the
    apology there says the cats are part of the pile.
    """
    return any((found or {}).get(key) for key in FAMILY)


def _just_a_liking(found):
    """Whether the only thing this line filed is a taste, which is not something that lands.

    "i love pasta" two turns after a death was answered "You love pasta — I'm sorry it's all coming
    at once", which reads as a mistake: a liking is not one more thing on a person's plate, and it
    is not what the room of a hard week changes. Anything else in the line (an age, a pet, a job)
    can be that, and keeps the heavy ending.
    """
    rest = {key for key, value in (found or {}).items()
            if value and key != "tastes" and not key.endswith("_frame")}
    return bool((found or {}).get("tastes")) and not rest


def _heavy(memory):
    """Whether the last few turns hold a death, a separation or harm somebody is doing.

    Only the recent turns: a funeral six turns ago has been answered, and a fact told now is
    not still being said through it. A line that is itself a loss or bad news is guarded where
    it arrives, so this is only about the room the next fact is said in.
    """
    for turn in (memory.get("turns") or [])[-HEAVY_TURNS:]:
        if not isinstance(turn, dict):
            continue
        said = " ".join(str(turn.get("user") or "").split())
        if not said:
            continue
        if loss.reads_as_loss(said) or SEPARATION.search(said.lower()) or reads_as_cruelty(said):
            return True
    return False


def _statement(memory):
    """Whether the understanding engine read the line as telling the bot something."""
    understood = memory.get("understood")
    kind = understood.get("kind") if isinstance(understood, dict) else None
    if isinstance(kind, str) and kind:
        return kind in ("statement", "tell", "news")
    return True


def _a_loss(text, memory, clean):
    """Whether bot/compose/loss.py reads a death or a grief in the line: that is its turn."""
    understood = memory.get("understood")
    topics = understood.get("topics") if isinstance(understood, dict) else None
    return loss.reply_for(text, memory, clean, topics) is not None


def _learned(text, memory=None):
    """The facts in the line for the store to keep, or an empty dict when there are none.

    The chat-speak is folded first: the store's patterns want "i am", and people type "im", so
    "thanks, also im vegetarian" is a diet like any other. A detail added to what we are already
    on counts too: "i work from home" and "i can put away about 200 a month" store no fact of
    their own, but they are theirs and worth answering with the thing itself rather than a stock
    line. Those come back as {"detail": True}, so the caller has something to say back while the
    store keeps its usual keys."""
    found = facts.extract(_spoken(text)) or facts.extract(text)
    kept = {key: value for key, value in found.items() if key in FACTS and value}
    if kept:
        return kept
    if _adds_one_more_allergen(text, memory):
        # "im allergic to peanuts" then "and milk too": the allergy on record with the milk in
        # it, said back the way a full "and im allergic to milk too" is.
        return {"allergies": _adds_one_more_allergen(text, memory)}
    if _adds_a_detail(text, memory):
        return {"detail": True}
    return {}


def _children_with_ages(text):
    """The children a line names with an age: "my kids are ada 7 and sam 4"."""
    reader = getattr(facts, "_kids_named_with_ages", None)
    try:
        return reader(text) if reader else []
    except Exception:
        return []


def _children_said(kids):
    """The children said back by name and age: "Ada is 7 and Sam is 4"."""
    parts = []
    for kid in kids[:4]:
        name = str(kid.get("name") or "")
        if not name:
            continue
        parts.append(name[:1].upper() + name[1:] + " is " + str(kid.get("age")))
    return " and ".join(parts)


def _adds_one_more_allergen(text, memory):
    """The allergy a line adds to the ones on record, or []: "and milk too" after peanuts.

    Only an allergy the person already gave is added to: a food word on its own says nothing
    about what it is being added to, and guessing "milk" into an allergy for someone who has
    not said they are allergic to anything is the one mistake worth never making.
    """
    if not isinstance(memory, dict):
        return []
    known = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    held = known.get("allergies") or []
    if not isinstance(held, list) or not held:
        return []
    # The thing may already be in the list: the store files it on this same turn, before the
    # reply is chosen, so "and milk too" is read here against a list that already has the milk
    # in it. What is said back is the fact either way.
    return facts.one_more(text)


def _adds_a_detail(text, memory):
    """Whether the line says something new about the thing we are on, with nothing to store.

    A person who adds a detail ("we live in a flat on the third floor", "i can put away about 200
    a month", "something without meat") is handing over the thing that makes the next answer
    theirs. Saying it back is what a friend does; the stock line ("got it, is there anything you
    would like a hand with?") could have come before any message at all.

    The guards matter more than the rule: there has to be a topic for the detail to belong to, the
    line has to say something the topic did not, and it must not be a question, a fault to
    troubleshoot or a misbehaviour to answer kindly.
    """
    if memory is None:
        return False
    # The line itself has been noted by the store before the reply is written, so the topic it
    # belongs to is the one we were on *before* it, not the line (topics.carried_topic).
    record = topics.carried_topic(memory, text) or topics.current(memory)
    if not record:
        return False
    clean = " ".join(str(text or "").split())
    read = _repaired(clean, memory)
    if "?" in clean or WANTS_ANSWER.search(read) or TROUBLE.search(read):
        return False
    if trouble.reads_as_trouble(read, read.split()):
        return False  # "my washing machine is leaking" is answered by trouble, not said back
    said_words = _words(clean)
    if len(said_words) < 2:
        return False  # "thanks", "same": nothing to say back on its own
    # A bare figure is a figure, not a detail: "actually 6" said back is "Got it - 6.", which
    # tells the person nothing they did not just type.
    if not re.search(r"[A-Za-z\u00c0-\u024f]", _strip_lead_in(clean)):
        return False
    # The same goes for a figure put in place of another when there is nothing to put it in
    # place of: "sorry i mean 800" after "im tired" is a figure and a repair frame and nothing
    # else, and "Got it — you mean 800" claims the bot is going with a number it does not hold.
    if not re.search(r"[A-Za-z\u00c0-\u024f]", REPAIR_FRAME.sub("", clean)):
        return False
    if len(clean.split()) <= 2 and not DIGIT.search(clean):
        return False  # "monday again": small talk, not a detail
    # After "my mum passed away on tuesday", the topic is grief: "it was sudden, i still expect
    # her to ring" is a comfort to give, never a fact to say back.
    carried = (record.get("text") or "") + " " + " ".join(
        str(turn.get("user") or "") for turn in (memory.get("turns") or [])[-3:]
        if isinstance(turn, dict))
    if DEATH_WORDS.search(carried) or _NOT_A_DETAIL_SUBJECT.search(carried):
        return False
    # The same goes for a detail given two turns after bad news: "some days are ok and some
    # aren't" after "we lost the baby last month" wants comfort, not a fact said back.
    for turn in (memory.get("turns") or [])[-2:]:
        if isinstance(turn, dict) and reads_as_bad_news(str(turn.get("user") or "")):
            return False
    known = set(_words(record.get("text") or ""))
    for earlier in record.get("details") or []:
        known |= set(_words(str(earlier)))
    if (_NOT_A_DETAIL.search(read) or _ANSWER_OPENER.match(read) or _ASKED_FOR.match(read)
            or _SAID_YES_NO.match(read) or _ASKS_MIDWAY.search(read) or _FAULT.search(read)):
        return False  # a farewell, a return to an old subject, or a yes/no read of the last turn
    return any(word not in known for word in said_words)


# The frame a repair puts round the thing it puts in place ("sorry i mean", "make that",
# "no, i meant to say"). What follows it is the thing itself, and a thing that is only a figure
# says nothing once the frame is taken off.
REPAIR_FRAME = re.compile(
    r"^\s*(?:(?:no|nope|sorry|apologies|actually|wait|hold\s+on|oops|and|so|oh|right|ok|okay)"
    r"\b[\s,]*)*(?:i\s+(?:mean|meant)(?:\s+to\s+say)?|make\s+that|you\s+mean)\b[\s,]*", re.I)


def _words(text):
    """The words of `text` that carry meaning: no articles, no auxiliaries, lower case."""
    out = []
    for word in WORD.findall(str(text or "").lower()):
        if word in _EMPTY:
            continue
        out.append(word)
    return out


# Words that name nothing on their own. "just everything at once" and "more of the same" are
# how they feel, not a fact to keep, and "everything at once — noted" is the coldest thing the
# store can say to someone having a bad day.
VAGUE = frozenset("""everything anything something nothing all stuff things thing lot lots
    bit bits more less much many one ones again once anyway same usual normal worse better
    else other others""".split())


def _names_nothing(body):
    """True when the words left are only filler and vague ones, so there is nothing to say back."""
    named = [word for word in _words(body) if word not in VAGUE]
    return not named


# A line that is only a preposition phrase after its lead-in is a fragment, not a thing:
# "sorry for moaning" loses "sorry" to the lead-in and leaves "for moaning", which said back
# reads "for moaning - noted" and answers the apology with a filing cabinet.
_OPENS_WITH_A_LINK = re.compile(r"^(?:for|about|to|of|with|in|on|at|over|into|like|as)\b", re.I)
# A budget said with nothing around it opens with one of those words ("about 30 pounds", "about
# 20 quid") and is still the whole fact, not half a sentence: the store keeps it, so it is said
# back. Money is what makes it whole, so a symbol or a money word has to be there.
MONEY_ONLY = re.compile(
    r"^(?:(?:about|around|under|below|less than|up to|max(?:imum)?|no more than|not more than)\s*)?"
    r"(?:[£$€]\s?\d[\d,.]*(?:\s?(?:k|pounds?|quid|euros?|dollars?|bucks))?"
    r"|\d[\d,.]*\s?(?:pounds?|quid|euros?|dollars?|bucks|k)\b)$", re.I)


def _repairs(clean, memory):
    """The line with the understanding engine's own corrections in it.

    A friend does not say your typo back. "my dog is geting old" was answered "your dog is geting
    old", and "im alergic" came back spelled the same way; the engine had already repaired both
    words for its own reading, and the echo only used its chat-speak table (SHORT), which is a
    different list. So the echo takes every word the engine repaired, in place, and keeps the
    words it left alone - a hyphen, a digit or a name is what they typed.

    A contraction typed without its apostrophe is one word where the reading has two: "were going
    to spain in may" reads as "we are going to spain in may", and the echo knows neither line, so
    it never got said back at all. The engine keeps that table (`LEFT_OFF_CONTRACTION`), so the
    count of words comes from it rather than from a second list here, and only the words it adds
    are allowed to appear where the person typed one.
    """
    understood = memory.get("understood") if isinstance(memory, dict) else None
    plain = understood.get("plain") if isinstance(understood, dict) else None
    if not isinstance(plain, str) or not plain.strip():
        return clean
    typed, fixed = clean.split(), plain.split()
    if not typed:
        return clean
    pairs, was_at, now_at = [], 0, 0
    while was_at < len(typed) and now_at < len(fixed):
        words = LEFT_OFF_CONTRACTION.get(typed[was_at].lower())
        if words and fixed[now_at:now_at + len(words)] == list(words):
            pairs.append((typed[was_at], " ".join(words)))
            now_at += len(words)
        elif (typed[was_at].lower() == fixed[now_at].lower()
              or (typed[was_at].isalpha()
                  and fixed[now_at].replace("'", "").replace("\u2019", "").isalpha())):
            pairs.append((typed[was_at], fixed[now_at]))
            now_at += 1
        else:
            return clean
        was_at += 1
    if was_at != len(typed) or now_at != len(fixed):
        return clean
    words = []
    for was, now in pairs:
        # A repair is a word for a word, and it changes the letters, not the case: the engine
        # lowercases the line for its own reading, and "Meg" is still "Meg". "co-op" read as
        # "co op" and "2" read as "two" are that same bookkeeping - not something to hand back
        # differently from how it was typed. A repair may carry an apostrophe, which is a
        # spelling ("ur" is read and said back as "you're"), so the apostrophe is not a word,
        # and a contraction typed flat is read as two words ("were" is "we are"), which is.
        if (was != now and was.isalpha()
                and (now.replace("'", "").replace("\u2019", "").isalpha() or " " in now)
                and was.lower() != now.lower()):
            words.append(now[:1].upper() + now[1:] if was[:1].isupper() else now)
        else:
            words.append(was)
    return " ".join(words)


# "my mums called janet" is the mum's name, so said back it takes the apostrophe a person's name
# always has: "your mum's called janet". Without it "your mums called" reads as a crowd of mums.
KIN_POSSESSIVE = re.compile(
    r"\b(your (?:mum|mom|mother|dad|father|son|daughter|sister|brother|wife|husband|partner"
    r"|nan|nana|granny|gran|grandma|grandad|grandpa|aunt|auntie|uncle|niece|nephew"
    r"|boyfriend|girlfriend|fiance|fiancee))s"
    # A figure right after it is the person's age ("my mums 68"), which is the same possessive:
    # "your mums 68" reads like a typo, "your mum's 68" reads like a sentence.
    r"(?= (?:\d+|called|named|name|age|coming|doing|gone|been|had|has|is|was|turns|turned)\b)",
    re.I)


# A count of things after "i'm" is what they have, not what they are: "im 2 dogs" is "you've got
# two dogs", and the sentence people say is never "you're two dogs". The units of time are the
# ones that really are a state ("you're two years in", "you're five minutes away").
A_COUNT_NOT_A_STATE = re.compile(
    r"^you're ((?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))\s+"
    r"([a-z]{2,}s)\b", re.I)
# A number and a unit of measure is a measurement, not a count of things: "im 2 dogs" is "you've
# got 2 dogs", but "im 90 kilos" is a weight and "im 6 weeks" is a length of time, and both are
# states a person is in. Every unit says so here rather than one rule per fact.
UNITS_OF_MEASURE = frozenset((
    "years", "months", "weeks", "days", "hours", "minutes", "seconds", "nights", "mornings",
    "evenings", "hrs", "mins", "secs",
    # weight
    "kilos", "kilograms", "kgs", "pounds", "lbs", "stones", "grams", "grammes", "ounces",
    # distance, drink and everything else measured
    "miles", "yards", "metres", "meters", "kilometres", "kilometers", "litres", "liters",
    "pints", "cups", "calories", "degrees", "inches"))
# The "who" of a clause, written the way people type it: "my sister whos 40 next week" is the
# same fact as "my sister is 40 next week", so the clause is said back with the apostrophe a
# person's "who's" always has.
WHOS = re.compile(r"\bwhos\b", re.I)


def _says_something(body):
    """Whether the words left after a repair frame say something, rather than naming a bare value.

    "i got the second interview" is a clause; "three", "the tap" and "caffeine" are the thing the
    person put in place of another and nothing else. A repair's own verb is kept for those, so the
    echo does not read "Got it - three", which no longer says three of what.
    """
    return facts._tail_has_a_verb(re.findall(r"[a-z']+", str(body or "").lower()))
# A pointer back with nothing in the chat to point at. The reader below answers a pointer from the
# thing the conversation is about, and on a first line there is no such thing: the reply said the
# pointer back - "Noted: your sister has the same one." - which is a sentence about a thing the
# person never mentioned, and a friend would ask which one. So a pointer with no thing behind it
# asks instead, and never states the pointer back.
NO_REFERENT = (
    "The same one as what?",
    "Which one do you mean?",
    "Same as what? Tell me what we are talking about and I will pick it up.",
    "I have lost the thread - which one do you mean?",
)
# A line whose whole subject is a pointer back at what the chat is already about: "we had another
# one", "my wife got one too", "we had one before". Nothing in it names a thing, so there is
# nothing to say back, and the thing they mean is the subject of the conversation.
POINTS_AT_ANOTHER = re.compile(
    r"\b(?:another one|one more|another|one too|one as well|one aswell|one before"
    r"|one of those|the same one|one like it|one like that)\b", re.I)
# A line that asks whether to have another is a decision, and the deciding readers answer it
# with the thing to weigh up. A pointer here would take that turn to say "Another puppy?".
A_DECISION = re.compile(
    r"\b(?:want|wants|wanted|should|shall|might|could|would|thinking|think|planning|planned"
    r"|considering|maybe|tempted|weighing|worth)\b", re.I)
# "we saw another one" after "we saw a fox in the garden" reports the same outing again, so the
# line points at nothing new: said back it is right ("you saw another one"), named it is wrong
# ("Two gardens, then"). A line that reports an action already done keeps its own answer.
REPORTS_AN_ACTION = re.compile(
    r"\b(?:saw|seen|read|made|bought|finished|started|watched|met|caught|found|killed"
    r"|sold|won|lost)\b", re.I)
# What is left of a pointer line once the pointer is taken out: the person, the verb of having,
# and the little words around them. A word outside this set is a thing of the line's own, and
# "i want another puppy" names its own thing and is never read here.
POINTER_FILLER = frozenset("""
i we you he she they it me my our your his her their its us them mine ours
the a an and but so also too as well just even still already now again then
had has have got gotten get gets bought buy buying made make makes making
finished finish started start read reading seen saw did do does doing
one ones another more of that this these those there here before after
""".split()) | frozenset(facts.RELATIONS) | frozenset("""
wife husband partner boyfriend girlfriend son daughter child kid kids baby mum mom mother
dad father brother sister friend mate colleague boss family parents in laws
""".split())
# "the thing they mean" is not any word: a person in the family, a day, a length of time or a
# word that only points ("another") is not something a person has another of.
NOT_A_THING_TO_HAVE_ANOTHER = frozenset("""
another more one ones same other else lot bit piece time times day days week weeks
month months year years hour hours minute minutes while thing things stuff kind sort
""".split()) | frozenset(facts.RELATIONS)

# The pointer said back as a question about the thing, one of them or several. Every line names
# the thing, so the pool cannot be read out to a line about something else.
ANOTHER_ONE = (
    "Another {thing}?",
    "A second {thing}, then. How is it going?",
    "Another {thing} - what is this one like?",
    "Two {things}, then. How are they getting on?",
)
ANOTHER_ONES = (
    "More {things}?",
    "Another lot of {things}, then. How are they getting on?",
    "More {things} - how are the first lot doing?",
)
BEFORE_ONE = (
    "How does this one compare to the last?",
    "What happened to the first {thing}?",
    "Still got the first {thing}?",
)
# The pointer whose subject is somebody else: "i started a new job" / "my wife got one too" is
# not a second job of the person talking, so "A second job, then" is false about them. The thing
# is named, and the person it belongs to is the one the reply asks about.
SOMEONE_ELSE_POINTS_AT_ANOTHER = re.compile(
    r"\b(?:my|our)\s+([a-z]+(?:[- ](?:in[- ]law|law))?)\s+"
    r"(?:has|have|got|gets|bought|buys|wants|wanted|had|found|rescued|adopted|is getting"
    r"|is buying|is having)\s+"
    r"(?:another one|one too|one as well|one aswell|one of those|the same one|another)\b", re.I)
PRONOUN_POINTS_AT_ANOTHER = re.compile(
    r"\b(?:she|he|they)\s+(?:has|have|got|gets|bought|wants|wanted|had|found|rescued|adopted)\s+"
    r"(?:another one|one too|one as well|one aswell|one of those|the same one)\b", re.I)
ANOTHER_ONE_FOR_SOMEONE = (
    "Your {person} too, then. How is the {thing} going?",
    "Your {person} as well, then - what is the {thing} like?",
)
# They said the thing in the plural, so the reply does too rather than guessing at the one.
ANOTHER_SOME_FOR_SOMEONE = (
    "Your {person} has some too, then. How are the {things} going?",
    "Your {person} as well, then - how are the {things} getting on?",
)


def _the_person_the_pointer_is_about(body, memory):
    """The person the pointer line is about ("wife", "mum", "sister"), or "" for the person
    talking."""
    found = SOMEONE_ELSE_POINTS_AT_ANOTHER.search(body)
    if found:
        word = found.group(1).strip().lower()
        return "" if word in ("own", "self") else word
    if PRONOUN_POINTS_AT_ANOTHER.search(body):
        # "she got one too": the person is the last relation the chat named.
        for turn in reversed((memory.get("turns") or [])[-3:]):
            if not isinstance(turn, dict):
                continue
            said = str(turn.get("user") or "").lower()
            for word in facts.RELATIONS:
                if re.search(r"\bmy\s+" + re.escape(word) + r"\b", said):
                    return word
    return ""


def _the_thing_the_chat_is_on(memory):
    """The thing the chat is about, in the words the person used, whether they said one or
    several, and the plural: ("puppy", False, "puppies") or ("tomatoes", True, "tomatoes").
    ("", False, "") when the chat is not about a thing a person can have another of.

    The subject is kept as a stem ("tomatoe"), so the word is looked for again in what the person
    actually said: a reply that names the thing has to use their word for it, not the stem.
    """
    phrase = " ".join(str(topics.subject(memory) or "").split()).lower()
    if not phrase:
        return "", False, ""
    # The subject is a bag of the chat's words, and its last one was read as the thing: "my dad
    # died" then "we had another one" was answered "A second died, then.", and "we go to portugal
    # every year" then the same line "A second every, then." A thing a person can have another of
    # is named behind a determiner ("a puppy", "my bike"), so only those words are read, and a
    # line with none of them leaves the pointer to the reader that answers it as it stands.
    named_words = set()
    for turn in reversed((memory.get("turns") or [])[-3:]):
        if isinstance(turn, dict):
            named_words.update(_a_thing_the_line_named(turn.get("user")))
    named_words -= NOT_A_SECOND_OF
    if not named_words:
        return "", False, ""
    stems = {topics.stem(word) for word in named_words}
    stem = ""
    for word in re.split(r"[^a-z]+", phrase):
        if (len(word) > 2 and word not in named.NOT_THE_THING
                and word not in NOT_A_THING_TO_HAVE_ANOTHER
                and (word in named_words or topics.stem(word) in stems)):
            stem = word
    if not stem or stem in NOT_A_THING_TO_HAVE_ANOTHER or stem in facts.RELATIONS:
        return "", False, ""
    if _something_they_avoid(memory, stem) or _a_name_the_store_holds(memory, stem):
        return "", False, ""
    said = ""
    for turn in reversed((memory.get("turns") or [])[-3:]):
        if not isinstance(turn, dict):
            continue
        for word in re.findall(r"[a-z']+", str(turn.get("user") or "").lower()):
            if word == stem or topics.stem(word) == stem:
                said = word
                break
        if said:
            break
    said = said or stem
    return said, said != stem, _plural(said)


A_NAME_GIVEN = re.compile(r"\b(?:called|named|name is|name's|names)\s+([a-z']+)", re.I)


def _a_name_the_store_holds(memory, stem):
    """Whether the word is a name somebody or some animal was given, not a thing of its own.

    "my sister is called meg" then "my brother has one too" was read as a pointer at another
    one, and named it: "A second meg, then." A name is not a thing a person has another of, so
    a name the store holds - a pet's, a person's, or one given on the last turn or two - is left
    to the reader that answers the line as it stands.
    """
    if not isinstance(memory, dict):
        return False
    names = []
    known = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    for pet in known.get("pets") or []:
        if isinstance(pet, dict) and pet.get("name"):
            names.append(str(pet["name"]))
    for other in memory.get("others") or []:
        if isinstance(other, dict) and other.get("name"):
            names.append(str(other["name"]))
    person = memory.get("person")
    if isinstance(person, dict) and person.get("name"):
        names.append(str(person["name"]))
    for turn in (memory.get("turns") or [])[-3:]:
        said = str((turn or {}).get("user") or "") if isinstance(turn, dict) else ""
        found = A_NAME_GIVEN.search(said)
        if found:
            names.append(found.group(1))
    return any(topics.stem(name) == stem for name in names if name)


def _something_they_avoid(memory, stem):
    """Whether the thing the chat is on is something the person is allergic to or avoiding.

    "im allergic to nuts" then "my son has one too" points at the allergy the son shares, not at
    more nuts: the "one" the son has is the allergy, and "More nuts?" is the wrong reply to it.
    A thing the store holds as an allergy or as a food to avoid is not something a person has
    another of, so the pointer is left to the reader that answers the allergy.
    """
    if not isinstance(memory, dict):
        return False
    known = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    meal = memory.get("meal") if isinstance(memory.get("meal"), dict) else {}
    for word in list(known.get("allergies") or []) + list(meal.get("avoid") or []):
        if topics.stem(str(word)) == stem:
            return True
    return False


def _plural(word):
    """The plural of a thing the person named, so a reply can say "two puppies"."""
    if word.endswith("s"):
        return word  # they said the plural already ("tomatoes", "roses")
    if word.endswith(("x", "z", "ch", "sh")):
        return word + "es"
    if len(word) > 2 and word.endswith("y") and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


# A contraction is never the thing a line names, and neither is a verb that is never a noun: "my
# tumble dryer isnt heating" named "isnt" (and the reply was "what is the isnt like?"), "my wages
# went in late" named "went", "my phone wont charge" named "charge", which is a verb there though
# it is a noun elsewhere ("a charge for the battery"), so no list of bad words can settle it. A
# verb *ends* the noun phrase rather than being its head, which is the rule the auxiliaries above
# already follow. The negations are a closed class. The verbs are only the forms that are never a
# noun in their own right - "heating", "leaves" and "left" are things a line can name, so they are
# not here.
ENDS_THE_THING_VERB = frozenset("""
aint arent cant couldnt didnt doesnt dont hadnt hasnt havent isnt mustnt neednt shant wasnt
werent wont wouldnt shouldnt
went gone came got gotten took taken gave given told said seen knew known kept
brought bought found goes comes says keeps sees knows thinks tells gives takes makes
""".split())


def _is_a_contraction(word):
    """Whether the word is a contraction ("isn't", "wont", "didnt") rather than a thing."""
    return "n't" in word or word in ENDS_THE_THING_VERB


A_DETERMINER = re.compile(
    r"\b(?:a|an|the|my|our|his|her|their|your|another|some|two|three|four|five|six|"
    r"seven|eight|nine|ten)\b", re.I)
# A word after the determiner that ends the thing named: "a new job" is a job, "a puppy for my
# son" is a puppy. Without a part-of-speech tagger the ends of a noun phrase are what can be
# named, so a link word, a pronoun, an auxiliary or an adverb takes the last word back.
ENDS_THE_THING = frozenset("""
in on at to for with from of about by into onto over under out up down off through across along
after before during since until while when where why how what which who whom whose that this
these those and but or so because if than then
i me you we us they them he him she it its am is are was were be been being have has had do does
did will would can could should may might must not no
very really quite too also just still again now last next
bit lot few couple other same whole rest most least more less only first
""".split())


# What nobody has another of: traffic, weather and homework are named behind a determiner like a
# thing is, but "A second traffic, then." is not a line about anything.
NOT_A_SECOND_OF = frozenset("""
traffic weather news advice information knowledge music homework housework work sleep noise mess
rubbish luck rain snow water wind light heat fun health pain stress exercise help space shopping
cleaning washing food drink dinner breakfast lunch tea coffee time money
""".split())


def _a_thing_the_line_named(text):
    """The head words of the noun phrases a line names behind a determiner: "we got a puppy last
    year" -> {"puppy"}, "i started a new job" -> {"job"}, "we called the puppy rufus" ->
    {"rufus"} (a name, so the caller stands down on it)."""
    words = re.findall(r"[a-z']+", str(text or "").lower())
    out = set()
    for at, word in enumerate(words):
        if not A_DETERMINER.fullmatch(word):
            continue
        head = ""
        for after in words[at + 1:at + 4]:
            if after in ENDS_THE_THING or len(after) <= 2 or _is_a_contraction(after):
                break
            head = after
        if head:
            out.add(head)
    return out


def _a_loss_just_before(memory):
    """Whether the last turn or two is a death: that turn belongs to the feelings reader."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    for turn in turns[-2:]:
        if isinstance(turn, dict) and facts.DIED.search(str(turn.get("user") or "")):
            return True
    return False


def _another_of_what_we_said(clean, memory):
    """The reply to a line that only points at another of the thing the chat is about, or None."""
    if not isinstance(memory, dict):
        return None
    turns = memory.get("turns")
    body = clean.strip()
    if not body or "?" in body or len(body.split()) > 8:
        return None
    if A_DECISION.search(body):
        return None
    found = POINTS_AT_ANOTHER.search(body)
    if not found:
        return None
    left = [word for word in re.findall(r"[a-z']+", POINTS_AT_ANOTHER.sub(" ", body).lower())
            if word not in POINTER_FILLER]
    if left:
        return None  # the line names a thing of its own
    if (REPORTS_AN_ACTION.search(body)
            and found.group(0).lower() not in ("one before", "the same one")):
        return None  # the same action reported again, not a second of the thing
    if _a_loss_just_before(memory):
        # Nothing is another one beside a death: "my dad died" then "we had another one" was
        # answered "A second died, then.", which is the worst line the bot could give there, and
        # the feelings reader has that turn.
        return None
    one, several, plural = _the_thing_the_chat_is_on(memory)
    if not one:
        # A pointer with nothing behind it. There is no thing to name, and saying the pointer back
        # tells the person nothing ("Noted: my sister has the same one"), so the reply asks.
        return pick(NO_REFERENT, memory, seed_text=body)
    person = _the_person_the_pointer_is_about(body, memory)
    if person:
        # The pointer says the other person has one too, so the reply is about them, not a second
        # of the thing in this house.
        pool = ANOTHER_SOME_FOR_SOMEONE if several else ANOTHER_ONE_FOR_SOMEONE
        return pick(pool, memory, seed_text=body).format(
            person=person, thing=one, things=plural)
    if found.group(0).lower() == "one before":
        return pick(BEFORE_ONE, memory, seed_text=body).format(thing=one)
    if several:
        return pick(ANOTHER_ONES, memory, seed_text=body).format(things=plural)
    return pick(ANOTHER_ONE, memory, seed_text=body).format(thing=one, things=plural)


# A bare noun-phrase said back is kept with the repair's own words in front of it, so the echo
# says what the person was talking about: "sorry, i mean three" is "Got it - you mean three".
# A correction that says its own "no" and then the thing carries no such repair - "actually no, a
# scooter" came back as "Got it - no, a scooter", which hands the person their correction back
# instead of the thing they settled on. The opener is only a "no"/"nope" (with an optional
# "actually"/"oh"/"sorry" in front of it) whose whole tail is the thing.
def _only_the_correction_in_front(kept, body):
    """True when `kept` is `body` with nothing in front of it but the correction's own opener.

    The opener is read by the correction reading itself (`facts.is_a_correction_opener`), so every
    word that announces a correction there - "no", "no wait", "sorry", "actually", "scratch that" -
    is an opener here too. This list used to be its own pattern that only gave way to a "no", so
    "wait, four brothers" was said back whole and the person got their own opener handed to them:
    "Got it - wait, four brothers."."""
    kept = " ".join(str(kept or "").split())
    body = " ".join(str(body or "").split())
    if not kept or not body or kept == body:
        return False
    if not kept.lower().endswith(body.lower()):
        return False
    front = kept[:len(kept) - len(body)]
    return bool(front.strip() and facts.is_a_correction_opener(front))


# The person's contraction, kept in the bot's wording: "you've got", never "you have got".
HAVE_GOT = re.compile(r"\b(you|we)\s+have\s+got\b", re.I)
HAVE_A = re.compile(r"\b(You|you|We|we)\s+have\s+a\b")


def _echo(clean, memory=None):
    """What they said, said back and short: "my sister is called Meg" -> "your sister is called
    Meg"."""
    # "god i hate mondays" is "i hate mondays" said back, not "god you hate mondays": the
    # exclamation is the person's exasperation, not the subject of the line.
    clean = without_a_leading_exclamation(clean)
    said_it = _repairs(clean, memory)
    body = _strip_lead_in(said_it)
    if body and not _says_something(body):
        # The repair was the whole sentence and the fact is a bare value: "sorry, i mean three"
        # is "Got it - you mean three" and not "Got it - three", which is a fragment that no
        # longer says three of what. A fact with a verb of its own ("i got the second
        # interview") is said without the frame.
        kept = _strip_lead_in(said_it, keep_the_repair=True)
        if kept != body and not _only_the_correction_in_front(kept, body):
            body = kept
    if not body:
        return None
    if _names_nothing(body):
        return None
    if (_OPENS_WITH_A_LINK.match(body) and len(body.split()) <= 3
            and not MONEY_ONLY.match(body.strip(" .,!?"))):
        return None  # "for moaning": half a sentence, left to the module that answers apologies
    if len(body) <= MOST:
        said = body  # short enough to say whole, and whole is what a list ("me, my partner and
        # our dog") needs
    else:
        clauses = [clause.strip() for clause in STOP.split(body) if clause.strip()]
        said = ", ".join(clauses[:CLAUSES]) if clauses else body
    said = _cut(said).strip(" ,;:-!?.\u2014")
    said = POLITE.sub("", said).strip(" ,;:-")
    said = _tail_off(said)
    said = _contrast_off(said).strip(" ,;:-")
    said = _reason_off(said, clean).strip(" ,;:-")
    said = _pick_off(said).strip(" ,;:-")
    if not said:
        return None
    back = _tidy(KIN_POSSESSIVE.sub(r"\1's", say_it_back(_spoken(said)).strip(" ,;:-")))
    if not back:
        return None
    # "i have got a loft to clear out" came back as "you have got a loft to clear out", which is
    # not how anybody says it: the person's own contraction is kept, in the bot's wording.
    back = HAVE_GOT.sub(r"\1've got", back)
    # "i'm 2 dogs" is not a state a person is in: a count of things after "i'm" is what they
    # have, so it comes back as "you've got two dogs" and never "you're two dogs". A length of
    # time is a state ("you're two years in", "you're 5 minutes away"), so time units are left.
    counted = A_COUNT_NOT_A_STATE.match(back)
    if counted and counted.group(2).lower() not in UNITS_OF_MEASURE:
        back = "you've got " + back[counted.start(1):]
    # The clause is said back the way it is written on the page, not the way it is typed:
    # "your daughter whos 9" reads as a typo, "your daughter who's 9" reads as a sentence.
    return WHOS.sub("who's", back)


def said_back(clean, memory=None):
    """Their line in the bot's own words, short: "i work all day" -> "you work all day".

    The same reading the echo reply is built from, for a module that wants to name what the
    person said inside a sentence of its own rather than hand it back on its own."""
    return _echo(clean, memory)


def _only_a_dislike(body, found):
    """True when the line is a dislike of a thing and nothing else.

    "hates" and "can't" are in `TROUBLE`, which is there for a person being difficult: "my boss
    keeps shouting at me" is trouble and must not be filed away. A dislike is the same words about
    a thing — "i hate cats", "i cant stand cats" — and taking the taste verb out leaves nothing
    that reads as someone's misbehaviour.
    """
    if not (found or {}).get("tastes"):
        return False
    return not TROUBLE.search(taste.DISLIKE_IN.sub(" ", body))


def only_a_dislike(text, memory=None):
    """True when the line is a stated dislike of a thing and nothing else.

    "i hate cats" and "i cant stand cats" are facts about the person's taste, and both words are
    also words for a bad day ("hate", "can't"): read as mood they get "That sounds rough", which
    is an answer for an event that happened to them, not for a thing they do not like.
    """
    clean = " ".join(str(text or "").split())
    if not clean:
        return False
    return _only_a_dislike(_strip_lead_in(clean), _learned(clean, memory))


def _tells_it(clean, found=None):
    """Whether the line can be said back: a state of their world, not someone's misbehaviour."""
    body = _strip_lead_in(clean)
    others = [entry for entry in (found or {}).get("others") or [] if isinstance(entry, dict)]
    if any("name" in entry or "age" in entry for entry in others):
        # "my mums called janet and shes 72" is a fact about her: it is theirs to keep, however
        # long the sentence is.
        return True
    if facts.foods_ruled_out(found):
        # "my son cant eat fish" has a "cant" in it, but it is what the son eats, not something
        # he did to them: the store filed it as his allergy, and the line is a limit to say back.
        # Read as trouble it fell through to the plain acknowledgement, and the line they had
        # just told the bot came back as "Thanks for telling me" with nothing in it.
        return True
    if TROUBLE.search(body) and not _a_diet(found) and not _only_a_dislike(body, found):
        return False
    if (found or {}).get("done"):
        return True  # "i met my sister for lunch on friday" is theirs whatever its length
    return bool(STATE.search(body)) or len(body) <= FRAGMENT


def _a_diet(found):
    """"she doesn't eat meat" has a "doesn't" in it, but it is what she eats, not what she does
    to the person: the store read a diet in the line, so the negation is not a complaint."""
    if not isinstance(found, dict):
        return False
    if found.get("diet") or found.get("no_meat"):
        return True
    return any(entry.get("diet") for entry in (found.get("others") or [])
               if isinstance(entry, dict))


# The words in front of an age or a height, and the units it can arrive in: together they say
# whether the figure is the whole line or one clause of a longer one.
FIGURE_LEAD = re.compile(
    r"^(?:i\s*(?:'m|am)|im|i\s+just\s+turned|my\s+(?:age|height)\s+is)\b[\s,]*", re.I)
FIGURE_FILLER = frozenset("""year years yrs yr old this now today already and""".split())
FIGURE_UNIT = frozenset("""ft foot feet in inch inches cm m st stone pounds pound lbs lb
    kilo kilos kg metres meters""".split())
# The inches of a height said as a word ("im 5 foot ten"), which is one part of the figure and
# not a word added to it.
FIGURE_WORD = frozenset("""one two three four five six seven eight nine ten eleven""".split())


def _only_the_figure(clean):
    """Whether the line says nothing but an age or a height: "im 34", "im 6 foot 2", "im 34 this
    year". A figure inside a longer sentence is not the thing the sentence is about."""
    body = " ".join(FIGURE_LEAD.sub("", _strip_lead_in(clean)).split())
    words = [word.strip(".,!;:") for word in body.split()]
    words = [word for word in words if word and word.lower() not in FIGURE_FILLER]
    # "5 foot 10" and "175cm" are the same kind of line: a figure, and the unit it is counted in
    # may be stuck to the number ("175cm") or standing on its own ("5 foot 10").
    return all(re.fullmatch(r"\d{1,3}(?:st|nd|rd|th)?(?:(?:cm|m|ft|in|kg|st|lbs?)s?)?", word)
               or word.lower() in FIGURE_UNIT or word.lower() in FIGURE_WORD for word in words)


# A line that carries on the question they just asked names a thing - often with a time after it
# - and says nothing else: "whats the capital of australia" then "and the weather there in june".
# There is no verb and nobody in it, so it is not a fact about them, it is the second half of one
# question. Said back as a fact ("Got it - the weather there in june") it reports something they
# never told us, and the module that answers weather never sees the line.
A_CONTINUATION = re.compile(r"^(?:and|also|plus|or|what about|how about|and what about)\b", re.I)
# Anything that makes a clause a sentence about someone: a verb of any tense, the chat-speak form
# of one ("dont", "cant"), or a person ("i", "my", "we"). A tail has none of them.
A_CLAUSE = re.compile(
    r"\b(?:is|are|am|was|were|be|been|being|isnt|arent|wasnt|werent|has|have|had|hasnt|havent|"
    r"hadnt|do|does|did|dont|doesnt|didnt|will|wont|would|wouldnt|can|cant|could|couldnt|should|"
    r"shouldnt|shall|may|might|must|got|get|gets|getting|go|goes|going|went|gone|need|needs|"
    r"needed|want|wants|wanted|like|likes|liked|think|thinks|thought|know|knows|knew|take|takes|"
    r"taking|took|make|makes|making|made|start|starts|started|come|comes|came|live|lives|lived|"
    r"work|works|worked|feel|feels|felt|keep|keeps|kept|try|tries|trying|look|looks|looking|"
    r"plan|plans|planning|book|booked|hope|hoping|wait|waiting|see|saw|seen|say|says|said)\b",
    re.I)
A_SOMEONE = re.compile(
    r"\b(?:i|i'm|im|i've|ive|i'd|id|i'll|ill|me|my|we|we're|were|we've|our|us)\b", re.I)


def _the_rest_of_a_question(clean, before=""):
    """Whether the line is the tail of the question before it, with no fact of its own.

    "and the weather there in june" after "whats the capital of australia": a conjunction, a
    thing and a date, and nothing else. Three things have to hold, because each one alone is
    wrong somewhere:

    - there is a conjunction ("and", "also", "what about"), so it is the second half of something;
    - the rest has no verb and nobody in it, so it states nothing: "and i have two cats" and
      "also my knee is bad" are things they told us, "and the weather there in june" is not;
    - the line before it asked something. "i have two cats" then "and a dog" is a dog; "whats the
      capital of australia" then "and the weather there in june" is the rest of that question.
    """
    line = " ".join(str(clean or "").split())
    match = A_CONTINUATION.match(line)
    if not match:
        return False
    rest = line[match.end():].strip(" ,.;:-!?")
    if not rest:
        return False
    if A_CLAUSE.search(rest) or A_SOMEONE.search(rest):
        return False
    return reads_as_an_ask(before)


# The same reading for a module that is deciding whether a line is something they told us: the
# summary of the chat and the receipt said back both want it, and neither wants to import a
# private name across files.
the_rest_of_a_question = _the_rest_of_a_question


# A correction opens with "no,": "no, its wednesday not tuesday" said back as "no it's
# wednesday" reads like an argument. Only with the comma, because "no heating since friday" and
# "no one at work likes me" are the sentences themselves.
#
# The same frame in the words people actually type went into the echo whole: "no wait, i got the
# second interview" came back "Got it \u2014 no wait, you got the second interview", as though the
# steering were part of the fact, and "sorry, i mean saturday" as "Got it \u2014 Sorry, you mean on
# Saturday." `LEAD_IN` already has "sorry" and "actually"; what it never had was the repair's own
# verbs and the "wait" that follows them. Every form here needs its comma or its verb, so "no
# onions", "wait for the kettle" and "i mean it" keep the words they were said with.
# A bare "no" in front of a correction is the correction, not the fact: "my son is 8" then
# "no hes 9" was said back as "Got it - no he's 9", which hands the person their own contradiction
# and buries the thing that was put right. The forms above all need a comma or a verb; this one
# needs the rest of the line to open on the person or the thing itself, so "no onions", "no
# heating since tuesday" and "no hot water" keep the word that carries their meaning.
NO_THEN_A_LINE = (
    r"no\s+(?=(?:"
    # The person or the thing, as the subject of what follows, and its contraction: "no hes 9",
    # "no it was my idea not the kids", "no we went in june", "no the quiet is the best bit of
    # it", "no not the boiler the pump". Written as the words themselves rather than as every
    # phrase they can start, because the list of phrases had only the present tense in it and
    # missed the rest: "no it was my idea not the kids" came back as "Got it - no it was your
    # idea not the kids", the person's own contradiction handed back to them as the fact.
    r"i|im|i'm|we|we're|were|you|youre|you're|he|hes|he's|she|shes|she's|it|its|it's|"
    r"they|theyre|they're|this|that|thats|that's|these|those|there|"
    # And the thing named with its own word instead of a pronoun, or the right thing in front of
    # the wrong one: "no the blue one", "no my sister", "no our lass", "no not the boiler".
    # People write "no wifi" and never "no the wifi", so the article or the possessive is what
    # makes this the correction rather than the sentence.
    r"the|not|my|our|your|his|her|their"
    r")\b)")

NO_THEN_A_LINE_ONLY = re.compile(r"^\s*" + NO_THEN_A_LINE, re.I)
NO_LEAD = re.compile(
    r"^\s*(?:(?:"
    r"no\s*,"
    r"|" + NO_THEN_A_LINE +
    r"|(?:no\s+|oh\s+|sorry\s+|actually\s+)?(?:wait|hang\s+on|hold\s+on)\s*,"
    r"|(?:i\s+(?:meant|mean)(?:\s+to\s+say)?"
    # "i mean it" and "i mean that" are the emphatic use, not a repair: nothing replaces them.
    r"(?!\s*,?\s*(?:it|that|this|so)\b(?:\s*,?\s*\w+){0,2}\s*[.!?]*\s*$)"
    r"|you\s+mean|make\s+that)\b\s*,?"
    r"|(?:sorry|apologies|actually|oops|oh)\s*,"
    r")\s*)+", re.I)


# A reaction in front of the fact: "lucky you. i've got a bathroom to sort out" was said back as
# "Noted: lucky you. you've got a bathroom to sort out.", and "fair enough, i have a bathroom to
# sort out" as "Noted: fair enough. you have a bathroom to sort out." The reaction is the person
# answering the bot - or agreeing with it - and it is not part of the thing they are telling it,
# so a short clause of nothing but reaction words in front of the fact comes off before the fact
# is read. Three things keep it safe: the words are a closed table (a phrase like "no worries
# about the boiler" is not a reaction and keeps its words), the clause has to end in its own
# punctuation and be followed by more of the line, and "good luck with the interview" - a whole
# line, with no clause after it - is never touched.
REACTION_PHRASES = frozenset((
    "quiet one", "quiet day", "busy one", "busy day", "slow day", "long day", "not bad",
    "not much", "nothing much", "not a lot", "all good", "can't complain", "cant complain",
    "same as ever", "good thanks", "fine thanks", "no complaints", "same old", "usual stuff",
    "you too", "likewise", "went ok", "went well", "went fine", "so so", "so-so", "up and down",
    "not too bad",
))
REACTION_WORDS = frozenset("""
lucky you fair enough got it sounds good sound good great nice cool lovely perfect ace brilliant
oh dear dear me good luck well done makes sense same here me too that's right exactly agreed
no worries okay ok thanks ta cheers haha lol ha magic typical bless you what a shame that's a
shame of course indeed true sure yeah yes oh wow ouch yikes a
""".split())
_REACTION_CLAUSE = re.compile(r"^([^.?!,;:]{1,32})[.?!,;:]+\s*(?=\S)")


def _after_a_reaction(text):
    """`text` without a short reaction clause in front of it ("lucky you.", "fair enough,")."""
    match = _REACTION_CLAUSE.match(text)
    if not match:
        return text
    clause = " ".join(match.group(1).split()).lower()
    words = [word.strip("'\u2019") for word in match.group(1).split()]
    if not words or len(words) > 5:
        return text
    if clause not in REACTION_PHRASES and not all(word.lower() in REACTION_WORDS
                                                for word in words):
        return text
    return text[match.end():].strip()


def _strip_lead_in(clean, keep_the_repair=False):
    """`clean` without the "hi, so," and the like in front of the fact.

    `keep_the_repair` leaves the repair's own verb on ("you mean three"), for a correction whose
    fact is a bare number or noun: "Got it - three." is not a sentence and no longer says three
    what, where "Got it - you mean three." is the person's own frame and still reads.
    """
    text = clean.strip(" ,;:-")
    # The bare "no" comes off either way: it is the person saying the last thing was wrong,
    # and a correction that keeps its own verb ("you meant with your flatmate") is not made
    # into a contradiction by leaving it on: "Got it - no you meant with your flatmate".
    text = NO_THEN_A_LINE_ONLY.sub("", text)
    if not keep_the_repair:
        text = NO_LEAD.sub("", text)
    changed = True
    while changed:
        changed = False
        # A greeting in front of a correction ("so, no wait, its tuesday") leaves the frame
        # exposed once the greeting has gone, so the frame is looked for again after each lead.
        bare = text if keep_the_repair else NO_LEAD.sub("", text)
        if bare != text:
            text, changed = bare, True
            continue
        for lead in sorted(LEAD_IN, key=len, reverse=True):
            low = text.lower()
            if low.startswith(lead) and low[len(lead):len(lead) + 1] in ("", " ", ",", ";", ":",
                                                                       "-", "!", "?", "."):
                text = text[len(lead):].lstrip(" ,;:-!?.")
                changed = True
                break
        if not changed:
            done = _after_a_reaction(text)
            if done != text:
                text, changed = done, True
    return text


def without_the_frame(clean):
    """"sorry, i mean saturday" with the apology and the repair taken off: "saturday".

    For a module that says a correction back in the person's own words: the frame is what they
    said to steer, not the thing they steered to."""
    return _strip_lead_in(" ".join(str(clean or "").split()))


# The count of top grades is written, not spelled: "3 a stars" is "three A*s". And a degree class
# is written "2:1", where the chat-speak fold spelled the first figure and left the second:
# "my son got a 2 1 in his degree" came back as "Your son got a two 1 in his degree".
COUNTED_STARS = re.compile(
    r"\b(?:(?:a|an)\s+)?(?P<count>[1-9]|1[0-2])\s+a[\s*'-]?stars?\b", re.I)
# One A* said without a count keeps its article: "my son got an a star in maths" came back as
# "Your son got an a star in maths", which is the person's typing handed back to them.
ONE_STAR = re.compile(r"\b(?:an?|one)\s+a[\s*-]?star\b", re.I)
STAR_COUNT = {1: "an A*", 2: "two A*s", 3: "three A*s", 4: "four A*s", 5: "five A*s",
              6: "six A*s", 7: "seven A*s", 8: "eight A*s", 9: "nine A*s", 10: "ten A*s",
              11: "eleven A*s", 12: "twelve A*s"}
# And a count of letter grades is written the way the grade is: "she got 3 a stars and 2 as" came
# back as "three A*s and two as". The letter only counts where the list ends or goes on to another
# grade, because "i got 2 as well" is a number and a word.
COUNTED_LETTERS = re.compile(
    r"\b(?P<count>[2-9]|1[0-2])\s+(?P<letter>a|b|c|d)(?:'?s|s)\b"
    r"(?=\s*(?:$|[,.;!?]|and\b|but\b))", re.I)
LETTER_COUNT = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
                9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}
A_DEGREE = re.compile(r"\b(?:degree|degrees|uni|university|graduat\w*|honours|bsc|ba|masters?|"
                      r"phd|dissertation|final year)\b", re.I)
DEGREE_CLASS = re.compile(r"\b(?P<first>[12])\s*[:.\- ]\s*(?P<second>[12])\b")


def _spoken(said):
    """`said` with the chat-speak folded, so the echo does not read "im" or "dont" or "yrs"."""
    said = COUNTED_STARS.sub(lambda match: STAR_COUNT[int(match.group("count"))], said)
    said = ONE_STAR.sub("an A*", said)
    said = COUNTED_LETTERS.sub(
        lambda match: LETTER_COUNT[int(match.group("count"))] + " " + match.group("letter").upper()
        + "s", said)
    if A_DEGREE.search(said):
        said = DEGREE_CLASS.sub(lambda match: match.group("first") + ":" + match.group("second"),
                                said)
    said = WITH_SLASH.sub("with ", said)
    said = TWO_TO.sub(lambda match: match.group(0)[:-1] + "to", said)
    said = TWO_PLACE.sub("to ", said)
    said = TWO_VERB.sub("to ", said)
    out = []
    words = said.split()
    for place, word in enumerate(words):
        bare = word.lower().strip(".,;:!?")
        tail = word[len(word.rstrip(".,;:!?")):]
        after = words[place + 1].lower().strip(".,;:!?") if place + 1 < len(words) else ""
        before = words[place - 1].lower().strip(".,;:!?") if place else ""
        if bare == "yer":
            out.append(("yeah" if not after or after in YES_AFTER else "your") + tail)
        elif bare == "its" and before in ITS_OWNS_AFTER:
            out.append(word)  # the possessive: "got its screen", not "got it's screen"
        elif bare in SPEAK:
            out.append(SPEAK[bare] + tail)
        elif bare in SHORT:
            out.append(SHORT[bare] + tail)
        else:
            out.append(word)
    return " ".join(out)


# A correction said back whole repeats the wrong thing: "sorry, my budget is 400 a month not
# 300" came back as "your budget is 400 a month not 300 - I'll keep any suggestions inside it",
# which sounds like the bot took "not 300" as part of the budget. The old value is not part of
# the fact, so the echo stops before it. Only a contrast that is a value, not a verb, is cut:
# "i would rather not say" is not a correction, and "not" belongs in it.
CONTRAST = re.compile(r"\s*,?\s+not\s+(?P<old>[\w'’$£€.,:/-]+"
                      r"(?:\s+[\w'’$£€.,:/-]+){0,3})\s*$", re.I)
# The correction that puts the right value on the end of the thing said again: "hes not 4 hes
# 5", "shes not 7 shes 8", "im not 40 im 45". The wrong value is in the middle and the thing is
# named twice around it, so the front half of the line is not the fact - cutting there left the
# bare pronoun and dropped the number the person had just given ("Got it - he's.", "Got it -
# you're."). What is kept is the thing as it is said the second time, with the new value on it.
# The old value has to be a value, so "i am not sure i am ready" stays the statement it is.
CONTRAST_SAID_AGAIN = re.compile(
    r"^(?P<thing>[a-z]+(?:\s+[a-z]+){0,2})\s+not\s+(?P<old>[\w'’$£€.,:/-]+)\s+"
    r"(?P=thing)\s+(?P<new>[\w'’$£€.,:/-]+(?:\s+[\w'’$£€.,:/-]+){0,2})\s*$",
    re.I)
# Words that make the words after "not" a clause rather than the wrong value: after one of them
# the line is a statement ("i would rather not say", "im not sure yet"), not a correction.
NOT_A_VALUE = frozenset("""a an the any sure really very too that this it them me you him her us
say said tell go going gone get got want need like mind be been being am is are was were have
has had can could would should will do does did make take give put keep try yet even still
allowed able bothered""".split())


# A line settling a choice carries the words of the settling as well as the thing: "actually make
# it a dog" was said back as "Noted: make it a dog" and "lets go with the focus" as "Got it — lets
# go with the focus", which hands the person the frame they put round the thing rather than the
# thing. The frame is the shape of the sentence, not part of what was chosen, so it comes off and
# the thing is said back on its own: "a dog", "the focus".
#
# Only the frames that can only be a pick. "going with" is also how a person says who they are
# going somewhere with ("we're going with the kids to spain"), so it is not here, and neither is a
# bare "go for".
PICK_FRAME = re.compile(
    r"^\W*(?:"
    r"(?:let'?s|let\s+us|i'?ll|we'?ll|i\s+will|we\s+will)\s+go\s+(?:with|for)\b"
    r"|(?:i|we)\s+(?:have\s+|had\s+)?(?:settled|decided|decide|settle)\s+(?:on|for)\b"
    r"|(?:i|we)\s+(?:have\s+|had\s+)?(?:opted|opt)\s+for\b"
    r"|(?:i|we)\s+(?:picked|pick|chose|choose)\b"
    r"|(?:i|we)'?ve\s+(?:settled|decided|gone)\s+(?:on|for|with)\b"
    r"|(?:make|makes)\s+(?:it|that)\b"
    r")", re.I)


def _pick_off(said):
    """`said` without the words that say a choice was made: "lets go with the focus" -> "the
    focus", "make it a dog" -> "a dog".

    A frame with nothing after it ("lets go with that") is left whole: there is no thing to say
    back, and the line is not an echo at all.
    """
    match = PICK_FRAME.match(said or "")
    if not match:
        return said
    rest = (said or "")[match.end():].strip(" ,;:-.!?\u2014")
    if len(rest.split()) < 1:
        return said
    return rest


def _tail_off(said):
    """`said` without the chat-speak hanging off the end, so the echo is the fact and not the
    filler: "im veggie tho" -> "you're veggie", "im veggie" unchanged."""
    said = without_filler(said)
    # The phrases the fact store trims before it files an item are not part of the fact said
    # back either: the store held "dairy" for "im allergic to dairy these days" and the echo
    # said "you're allergic to dairy these days, good to know".
    words = said.split()
    while words:
        low = " ".join(words).lower().strip(" ,;:-")
        cut = next((phrase for phrase in facts.FILLER_TAIL_PHRASES if low.endswith(phrase)), None)
        if not cut or len(words) <= len(cut.split()):
            break
        words = words[:-len(cut.split())]
    return " ".join(words).strip(" ,;:-")


def _contrast_off(said):
    """`said` without the wrong value it replaced: "my budget is 400 a month not 300" -> "my
    budget is 400 a month".

    Only a value is taken off. "my sister is not coming" and "my son is not well" carry the same
    shape and are whole facts, so the cut needs a value on one side of the "not": the number or
    the day it corrects, on either side of it.
    """
    again = CONTRAST_SAID_AGAIN.match(str(said or "").strip())
    if again and _a_value(again.group("old")):
        return "%s %s" % (again.group("thing"), again.group("new"))
    match = CONTRAST.search(said or "")
    if not match:
        return said
    old = [word for word in re.split(r"\s+", match.group("old").strip(" .,;:-")) if word]
    if old and old[0].lower() in ("the", "a", "an"):
        old = old[1:]  # "not the 5th" corrects a day, and the article is not the value
    if not old or not re.search(r"[a-z0-9]", old[0], re.I):
        return said
    kept = [word for word in re.split(r"\s+", said[:match.start()].strip(" .,;:-")) if word]
    if old[0].lower() in NOT_A_VALUE:
        return said
    if not (_a_value(old[0]) or (kept and _a_value(kept[-1]))):
        return said
    restated = _the_value_put_right(said, match)
    if restated:
        return restated
    return said[:match.start()]


# A correction comes with the reason it was made: "actually i mean 75 because i lost some",
# "no its 900 since the boiler went". The reason explains the change and is not part of the value,
# the same way the replaced value in "my budget is 400 not 300" is not part of it, so what is said
# back is the corrected fact. Only a line that corrects is trimmed: "im tired because i was up all
# night" is the whole fact, and the reason is what makes it one.
A_REASON_TAIL = re.compile(r"\s+(?:because|cos|coz|cuz|'cause|since)\b[^.!?]*", re.I)
A_CORRECTION_IN_FRONT = re.compile(
    r"^\s*(?:actually|no|nope|sorry|wait|oh|i\s+mean|i\s+meant|make\s+that)\b", re.I)


def _reason_off(said, clean):
    """`said` without the reason a correction gave for itself: "you mean 75 because I lost some"
    -> "you mean 75".

    The reason is the why of the change, not the value that changed, so a reply that names the
    value says the value: "you said 75 because." is the machine. A line that is not a correction
    keeps its reason, because there the reason is the fact ("you're tired because you were up all
    night").
    """
    if not A_CORRECTION_IN_FRONT.match(clean or ""):
        return said
    match = A_REASON_TAIL.search(said or "")
    if not match or not said[:match.start()].strip(" ,;:-"):
        return said
    return said[:match.start()]


# The words that can stand between the old value of a restated correction and the new one: the
# subject said again ("4 hes 5") or a pronoun and its verb ("4 my son is 5"). A unit word or a
# noun ("miles", "pm", "kids") makes two figures two different things rather than one value put
# right ("im not driving 5 miles its 10"), and the words of that line are left as they were.
BETWEEN_VALUES = frozenset("""he she it they we you i his her its their our my
is was are be been am just only now actually really still but
hes shes its theyre im youre were s""".split())


def _the_value_put_right(said, match):
    """The line with the value a restated correction puts right, or "" for any other shape.

    A correction can put the old value in the middle of the line rather than at its end: "hes not
    4 hes 5", "my son is not 4 hes 5". The cut above leaves only what stands in front of the
    "not", so the person was told "Got it \u2014 he's." and "Got it \u2014 your son is." - the
    bot handing back the first half of their sentence with the fact gone. The value the line is
    corrected to is the last one in the clause, and what is in front of it names the subject
    without naming a value, so the line goes back together with that value on the end.
    """
    head = " ".join(str(said or "")[:match.start()].split()).strip(" ,;:-—")
    if not head:
        return ""
    if any(_a_value(word) for word in re.split(r"\s+", head)):
        return ""  # the value on this side is the one said back, as it was before
    words = [word for word in re.split(r"\s+", match.group("old").strip(" .,;:-")) if word]
    if len(words) < 3:
        return ""  # one value in the clause: the ordinary cut is the whole of it
    second = next((at for at in range(1, len(words)) if _a_value(words[at])), None)
    if second is None:
        return ""
    between = [word.lower().strip(".,!?'\u2019") for word in words[1:second]]
    if not between or any(word not in BETWEEN_VALUES for word in between):
        return ""
    return head + " " + " ".join(words[second:])


# What counts as the value a correction replaces: a number, an amount, or a day or month.
VALUE = re.compile(r"\d|^(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                   r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
                   r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|a|an|"
                   r"grand|quid|pm|am)$", re.I)


# A correction that puts a new value where the old one was, in the shape that names no old value:
# "make it four" after "im going to the gym three times a week", "make that 10k" after "i run 5k
# every morning". facts.CORRECTION_MAKE reads the same shape for the store, and the store can only
# correct a value it holds; a routine they described is not one, so these lines fell through every
# module to the search hedge ("That's beyond what I know well, sorry"), which is the one reply a
# correction must never get: the person is not asking a question, they are telling the bot
# something changed. The value goes back up with the unit of the line before it, when that line
# has one, so "four" arrives as "Four times a week, then." and not as a bare number.
MAKE_A_VALUE = re.compile(
    r"^\s*(?:(?:no|nope|sorry|ah|oh|ok|okay|right|and|so|well|actually|wait|hmm)[,.]?\s+)*"
    r"(?:make\s+(?:it|that)|change\s+(?:it|that)\s+to|switch\s+(?:it|that)\s+to)\s+"
    r"(?P<value>[^,.!?;]{1,40}?)\s*[.!]*\s*$", re.I)
# The words a value can be made of when it carries no digit: "four", "twice", "every day", "a
# grand", "10k" already has one. "make it stop" and "make it bigger" are the end of a sentence
# ("my boiler is broken" / "a new sofa"), and folding "Stop it is." into the chat is what the
# store already refuses to do.
VALUE_WORDS = frozenset("""half quarter past to oclock am pm once twice one two three four five six
seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen
twenty thirty forty fifty sixty seventy eighty ninety hundred thousand a an grand the
every of hour hours minute minutes week weeks day days month months year years time times per a
kilo kilos kg mile miles km pound pounds quid dollar dollars euro euros""".split())
# The words a line measures its figure in: "three *times a week*", "5k *every morning*". The new
# value of a correction is said back with them, so "make it four" after the gym line answers
# "Four times a week, then." and not a bare number.
UNITS_AFTER = frozenset("""times time a an per week weeks day days month months year years hour
hours minute minutes mile miles km kilo kilos pound pounds quid egg eggs cup cups spoon
spoons every morning evening night weekend""".split())


def _a_value(word):
    """Whether this word is a value a correction can replace ("300", "june", "£40")."""
    low = str(word or "").strip(" .,;:!?\u2019'").lower()
    if not low:
        return False
    if VALUE.match(low):
        return True
    return low in DAYS or low in MONTHS


def _cut(said):
    """`said` down to MOST characters at a word boundary, so an echo stays an echo."""
    if len(said) <= MOST:
        return said
    kept = said[:MOST].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return kept if " " in kept else said[:MOST]


# Words that carry a capital only because they started the person's sentence. Saying the detail
# back puts it after "Got it - " ("Got it - just you, four nights"), where a capital reads like a
# mistake, so these come down; a name ("Tokyo", "September") keeps the capital they gave it.
FIRST_WORD = frozenset((
    "he", "he's", "he'll", "she", "she's", "she'll", "it", "it's", "it'll", "they", "they're",
    "they'll", "they've", "we", "we're", "we'll", "we've", "our", "there's", "there'll",
    "the", "this", "that", "these", "those", "a", "an", "my", "his", "her", "its", "just",
    "not", "no", "and", "but", "so", "also", "then", "now", "still", "only", "even", "both",
    "all", "every", "at", "in", "on", "for", "after", "about", "around", "one", "two", "three",
    "four", "five", "six", "seven", "eight", "nine", "ten", "half", "someone", "something",
    "nothing", "theres", "theyll",
))


def _tidy(text):
    """`text` as one sentence piece: the second person in lower case, and nothing else
    changed, so a proper name ("Tokyo") keeps the capital the person gave it."""
    words = text.split()
    out = []
    for index, word in enumerate(words):
        low = word.lower()
        if low in ("you", "your", "you're", "you've", "we", "our", "yourself"):
            word = low  # you() keeps the capital of "I", which only belongs at the start
        elif index == 0 and low in FIRST_WORD:
            word = low  # a capital only because it started their sentence
        out.append(word)
    return " ".join(out)
