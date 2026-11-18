"""A limit on what somebody can do, said out loud: a fact about the plan, not a symptom.

People bring a trip or an afternoon out with a limit already in it - "Im taking my mum to Rome in
April." / "She cant walk far.", "my dad cant walk far so we need somewhere flat", "two adults, one
is in a wheelchair" - and on main every one of those lines was answered badly, in three different
ways:

    She cant walk far.                     -> How long has that been going on with your mum?
    Two adults, one is in a wheelchair.    -> Got it - two adults, one is in a wheelchair.
    my dad cant walk far so we need ...    -> Somewhere flat - fair enough. What's stopped it
                                              happening so far?
    she cant walk far                      -> I'm with you. Keep going if you want to.

The first is the worst of them. A person saying what their mum can manage on a trip is not asking
for a health interview about her, and the question ("how long has that been going on") reads as if
the holiday had not been mentioned. A friend hears a limit and says what it means for the plan: one
thing a morning, a sit-down between, a taxi for the last stretch, and the step-free way in.

Four things keep this from answering lines it has no business in:

* the shape is a limit in the words people use for one - cannot walk far, cannot manage stairs,
  cannot stand for long, uses a stick, is in a wheelchair - and nothing else.
* a line that reports a symptom is not a limit: "she cant walk far and her leg is swollen" is for
  the health answers and safety's first. The same goes for a diagnosis or a treatment, because the
  question there is about the illness rather than the plan.
* an animal's limit is its own conversation ("my dog is 14 and cant walk far" is a question about
  the end of a dog's life, not about a step-free entrance).
* a line that asks something is left to the module that can answer it, so "can my mum with a stick
  get round the museum" keeps its question.

The limit is also kept in `memory["limits"]`, because it is a fact about the person that holds for
the rest of the chat: a plan offered two turns later should know the walk is short.
"""
import re

from ..compose import pick

# A person, so the limit has somebody it is about. The pronoun and the possessive are both here
# because the line arrives either way ("she cant walk far", "my mum cant walk far").
_PERSON = (
    r"(?:i|we|my \w+|mum|mom|mother|dad|father|nan|nana|gran|granny|grandma|grandad|grandpa|"
    r"partner|husband|wife|oh|other half|daughter|son|sister|brother|aunt|uncle|cousin|"
    r"friend|mil|fil|she|he|they|her|his|their)"
)
# How a limit is said: cannot, or the words people use instead of it. "struggles with" and "finds
# it hard to" are how most people put it about a parent.
_CANNOT = (
    r"(?:can'?t|cannot|can not|isnt able to|isn'?t able to|not able to|dont|doesn'?t|"
    r"do not|does not|struggles? (?:to|with)|struggling (?:to|with)|finds? it hard to|"
    r"find it hard to|has trouble|have trouble|bad (?:on|at|with))"
)
_WALK = (
    r"(?:walk(?:ing)? (?:far|much|long distances|very far|any distance)|"
    r"manage (?:the )?stairs|do (?:the )?stairs|climb (?:the )?stairs|stairs|"
    r"stand (?:for long|up for long|for very long|about for long|for more than \w+ minutes?)|"
    r"get (?:about|around) (?:much|easily|well)|"
    r"(?:walk|move) (?:as )?(?:well|easily) as (?:she|he|they) used to)"
)
_LIMIT_VERB = re.compile(
    r"\b" + _PERSON + r"\s+" + _CANNOT + r"\s+(?:really |even |anymore |any more )?" + _WALK +
    r"\b", re.I)
# The noun forms: what the person uses to get about, said as a fact rather than as a question. A
# stick and a frame are the commonest, and a wheelchair is the one that decides the whole plan.
_AID = re.compile(
    r"\b(?:uses?|using|needs?|has|got|with|on|in)\s+(?:a |an |his |her |their |my )?"
    r"(?:wheelchair|mobility scooter|scooter|walking stick|stick|walking frame|zimmer|"
    r"rollator|walking aid|walker|crutches)\b", re.I)
# "in a wheelchair" and "on crutches" arrive without a verb of their own.
_IN_A_CHAIR = re.compile(
    r"\b(?:is in|are in|in|into) a wheelchair\b|\bwheelchair[- ]?(?:user|bound)\b"
    r"|\bon crutches\b|cant walk at all|can'?t walk at all|non[- ]?weight ?bearing\b", re.I)
# A flat place is the same limit said as a request for ground rather than for a person. Only the
# ground sense counts: a flat is also a rented home, and "im looking for a flat" was answered with
# advice about short walks ("Volume is weight at the roots" before that, so the flat was a haircut
# and a home before it was a landscape).
_FLAT = re.compile(
    r"\bsomewhere flat\b|\bflat(?:ter)? (?:ground|walk|walking|paths?|route|town|city|seafront|"
    r"promenade|terrain|streets?)\b|\bneed(?:s)? (?:it|somewhere|the ground) flat\b"
    r"|\bkeep (?:it|to) (?:the )?flat\b", re.I)
# A rule about the plan with nobody in the line: "no long walks", "nothing too tiring", "no stairs".
# People say the limit on a trip that way as often as they say who has it, and the line has no
# person for `_LIMIT_VERB` to read, so it fell through to a card about an easy evening in: "no long
# walks" after a week in the Lakes was answered with a film and a box set. The words are the ground
# ones only: "nothing too tiring" is read by the tiredness answers, which own that word, and taking
# it here would be a worse answer to a line about a body than to a line about a trip.
_NO_WALKS = re.compile(
    r"\b(?:no|nothing|not|never|nowt)\s+"
    r"(?:(?:that\s+)?(?:needs?|involves?|involving|means|with)\s+)?"
    r"(?:too\s+|very\s+|much\s+|any\s+|more\s+)*"
    r"(?:long\s+|proper\s+|big\s+|far\s+|steep\s+|many\s+)?(?:walks?|walking|hikes?|hiking|"
    r"hills?|stairs|steps|climbing)\b", re.I)
# A bare rule is the whole line. Said inside a longer one it is usually something else: "im not
# walking to work any more" is a change of commute and "no walk in the park then" is an idiom, and
# both were answered with a plan for short hops on a trip (crimson-plum on #8190). So the rule has
# to be the line: only a connector in front of it, and only a nod or a "today" behind it.
_RULE_LEAD = re.compile(
    r"^(?:(?:and|so|but|then|also|oh|plus|ok|okay|well|just|actually|honestly|now|right)\b[^a-z]*)*",
    re.I)
_RULE_TAIL = re.compile(
    r"^[\s,.;:!-]*(?:(?:please|thanks|ta|then|either|though|too|really|honestly|sadly|unfortunately|today|"
    r"tomorrow|tonight|now|though|any ?more|at all|this time|for (?:me|us)|on (?:this|the) trip|"
    r"i think|i suppose)\b[^a-z]*)*$", re.I)
_STAIRS_SAID = re.compile(r"\b(?:stairs|steps|climbing)\b", re.I)
# Somebody who will not accept an aid is a different conversation from somebody who cannot walk
# far: the useful reply is about the refusing ("she wont use a stick"), and a plan for short hops
# is not it.
# The line arrives after understanding has expanded the contraction ("she wont use a stick" is
# read as "she will not use a stick"), so `will not` and `would not` have to be here as well.
_REFUSES_AID = re.compile(
    r"\b(?:wont|won'?t|will not|would not|refuses?|refused|refusing|hates?|hated|"
    r"doesn'?t want|dont want|does not want|do not want)\b[^.]{0,25}\b(?:stick|frame|zimmer|"
    r"rollator|walker|wheelchair|scooter|aid|rail|handle|crutch(?:es)?)\b", re.I)
# Not everybody who limits a walk is unable to do one. "he hates walking so keep it short" and
# "he'd rather sit in a pub all day" limit the same day out and want the same short-hop plan; on
# main both were answered by whatever the chat was already about (the hiking-water card, or the
# budget card) and neither was kept, so "and what does he not like doing" asked for it in vain.
# The trip gate below is what keeps a job or a house out: "i hate walking to work" names no plan.
_DISLIKES_THE_WALK = re.compile(
    r"\b(?:hates?|hated|dislikes?|can'?t stand|cannot stand|cant stand|doesn'?t like|don'?t like|"
    r"do not like|isn'?t keen on|not keen on|would rather not|prefers? not to)" + r"\b[^.]{0,24}"
    r"\b(?:walk(?:ing)?|hikes?|hiking|rambl(?:e|ing)|hills?|steps?|stairs)\b"
    r"|\brather sit\b|\bsit in a pub\b", re.I)
# A pushchair is a child's seat, not a limit on the person pushing it: "we need somewhere flat for
# the pushchair" is a buggy and its wheels, and a short-walk itinerary is the wrong advice.
_PUSHCHAIR = re.compile(
    r"\b(?:pushchair|pram|buggy|stroller|car ?seat|carrycot|cot|highchair)\b", re.I)
# A flat place to live is a home, not ground to walk on: "my nan needs somewhere flat to live" is
# about housing, and a plan for short walks answers a question nobody asked.
_FLAT_IS_A_HOME = re.compile(
    r"\b(?:to live|to rent|to buy|to move to|a flat|flat to|ground floor flat|bungalow)\b", re.I)

# Nothing here knows about an illness. A symptom, a diagnosis or a treatment means the person is
# asking about the body rather than about the day out, and the health answers and safety own that.
_ILLNESS = re.compile(
    r"\b(?:pain|painful|hurts?|hurting|swollen|swelling|fell|fallen|fall|falls|dizzy|numb|weak|"
    r"unwell|ill|poorly|blood|bleed|bleeding|bruise|broken|fracture|sore|stiff|"
    r"doctor|gp|nurse|hospital|a&e|ambulance|111|999|since (?:her|his|the)|getting worse|"
    r"arthritis|dementia|alzheimers|parkinsons|ms|stroke|surgery|operation|replacement|"
    r"physio|physiotherapy|chemo|cancer|diagnosis|tablets?|medication|prescribed)\b", re.I)
# An animal's limit is about the animal, not about the stairs in a museum.
_PET = re.compile(
    r"\b(?:dog|dogs|puppy|pup|cat|cats|kitten|pet|pets|rabbit|hamster|guinea|horse|pony|"
    r"ferret|parrot)\b", re.I)
# A limit that is asked about, rather than told: the question belongs to whoever can answer it.
_ASKS = re.compile(
    r"^\s*(?:what|where|when|why|how|which|who|can|could|do|does|did|is|are|was|were|will|"
    r"would|should|shall|any|anyone|anybody)\b", re.I)

# The pools below are plans for a day out, and a plan for a day out is only an answer when a trip
# is on the table. "My grandad cant manage the stairs at home" and "i cant stand for long at work"
# are facts about a house and a job: answered with an itinerary they read as the bot not listening,
# which is the fault this module exists to fix, in the other direction.
_A_TRIP = re.compile(
    r"\b(?:trip|trips|holiday|holidays|city break|weekend|days? away|nights? away|day out|days out|"
    r"flight|flights|flying|abroad|visit(?:ing)?|sightsee\w*|tour(?:ing)?|museums?|galleries|"
    r"castles?|cathedral|hotels?|somewhere to stay|what should we see|where should we go|"
    r"things to do|days in|nights in|weeks in|a week|a few days|\d+ (?:days|nights)|"
    r"taking \w+(?: \w+)? (?:to|off)|off to|going to|booked|booking|somewhere to stay|"
    r"seaside|beach|coast|countryside|shopping|old town|town cent(?:re|er))\b", re.I)


def _the_trip_is_on(clean, memory):
    """Whether a trip or a day out is on the table for this limit to shape.

    The line itself can bring one ("my dad cant walk far so we need somewhere flat", "where should
    we go at half term"), or the chat already has one - a place, a plan, or a turn that named a
    trip. The place is the strongest sign, because a person who has said where they are going does
    not have to say it again when the limit comes up a turn later.
    """
    if _A_TRIP.search(clean):
        return True
    if _FLAT.search(clean) and not _FLAT_IS_A_HOME.search(clean):
        return True
    known = (memory or {}).get("user") if isinstance(memory, dict) else None
    if isinstance(known, dict):
        if [place for place in (known.get("places") or []) if str(place).strip()]:
            return True
        if _A_TRIP.search(str(known.get("plan") or "")):
            return True
    for turn in _turns(memory)[-4:]:
        if isinstance(turn, dict) and _A_TRIP.search(str(turn.get("user") or "")):
            return True
    return False


# The replies. Each says what the limit means for the plan and none of them asks after the person's
# health; a friend who has just been told this does not go back over it.
WALK_REPLIES = (
    "Then plan for benches. One big thing a morning, a sit-down after it, and a taxi or a bus for "
    "the long hops - two sights close together beats four across town.",
    "Good to know. Keep the days short and stop before the legs give out rather than after, and "
    "check the step-free way into the one place you most want to see.",
    "That shapes the trip more than the sights do: one thing a day, short walks between, and no "
    "shame in a taxi for the last stretch.",
    "Then build the day around a sit-down every hour or so, and pick your two must-sees rather "
    "than a list. Most museums have a step-free entrance if you ask before you go.",
    "Fair enough - short hops, a stop for a coffee in the middle, and somewhere to sit at the end. "
    "That is a better trip than a marathon of churches anyway.",
)
STAIRS_REPLIES = (
    "Ask about lifts and step-free entrances before you book anything: most big places have them, "
    "and it is usually not the front door.",
    "Then ring ahead for the ones you care about - a lift to the good floors and a loo you can get "
    "to are the two questions worth asking.",
    "Old towns are the hard part, so keep to the flatter streets and take the bus between the bits "
    "at the top of the hill.",
)
CHAIR_REPLIES = (
    "Then ask about the step-free entrance for each place before you go - most big museums have "
    "one. Cobbles and the oldest streets are the thing to plan around.",
    "Ring ahead for the ones that matter: step-free entry, a lift to the good floors, and an "
    "accessible loo. Most places will tell you straight if you ask.",
    "Plan around the ground rather than the sights: smooth pavements, a bus or a taxi between "
    "stops, and one thing a day is plenty.",
)


def _kind(clean):
    """Which limit the line is, or None. The aid comes first: an aid decides a whole day."""
    if _IN_A_CHAIR.search(clean):
        return "chair"
    if _AID.search(clean):
        aid = _AID.search(clean).group(0).lower()
        if "wheelchair" in aid or "scooter" in aid:
            return "chair"
        return "walk"
    if _LIMIT_VERB.search(clean):
        said = _LIMIT_VERB.search(clean).group(0).lower()
        if "stairs" in said:
            return "stairs"
        return "walk"
    if _DISLIKES_THE_WALK.search(clean):
        return "walk"
    if _FLAT.search(clean):
        return "walk"
    lead = _RULE_LEAD.match(clean)
    rule = _NO_WALKS.match(clean, lead.end() if lead else 0)
    if rule and _RULE_TAIL.match(clean[rule.end():]):
        # Nobody in the line, so the rule is about the ground: the stairs get the stairs answer and
        # every other move word gets the short-walk one.
        return "stairs" if _STAIRS_SAID.search(rule.group(0)) else "walk"
    return None


def names_a_limit(text):
    """Whether the line names something the person cannot do, or None.

    "she cant walk far", "he is in a wheelchair", "two adults, one needs the stairs to himself":
    the kind of limit, without needing the chat to be about a trip. A line like this is a fact
    about somebody, and a sentence of the answer already given is not the answer to it.
    """
    return _kind(" ".join(str(text or "").replace("\u2019", "'").split()))


def reply(text, memory):
    """A reply that turns a limit into a plan, or None when the line is not one."""
    clean = " ".join(str(text or "").replace("\u2019", "'").split())
    if not clean or len(clean.split()) > 18:
        return None
    if (_PET.search(clean) or _ILLNESS.search(clean) or _REFUSES_AID.search(clean)
            or _PUSHCHAIR.search(clean)):
        return None
    kind = _kind(clean)
    if not kind:
        return None
    # A question with a limit in it ("can my mum with a stick get round the museum") is somebody
    # else's turn: it asks for a fact, not for the plan.
    if clean.rstrip().endswith("?") or _ASKS.match(clean):
        return None
    if not _the_trip_is_on(clean, memory):
        # Nothing here knows about stairs in a house or a job on your feet, so the turn is left to
        # whatever answers its own subject. The limit is not kept either: a plan offered two turns
        # later would then be shaped like a trip nobody mentioned.
        return None
    kept = {"kind": kind, "text": clean, "turn": len(_turns(memory))}
    if isinstance(memory, dict):
        # The limit holds for the rest of the chat, so it is kept where the plan modules can read
        # it. The list keeps every one said: a trip can have a short walk and a wheelchair in it.
        limits = memory.get("limits")
        if not isinstance(limits, list):
            limits = []
        limits.append(kept)
        memory["limits"] = limits[-6:]
    pool = {"walk": WALK_REPLIES, "stairs": STAIRS_REPLIES, "chair": CHAIR_REPLIES}[kind]
    return pick(pool, memory, seed_text=str(text or ""))


def _turns(memory):
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    return turns if isinstance(turns, list) else []


def said(memory):
    """The last limit told in this chat, or None - what a plan offered later should know about."""
    limits = (memory or {}).get("limits") if isinstance(memory, dict) else None
    if isinstance(limits, list) and limits:
        last = limits[-1]
        if isinstance(last, dict):
            return last
    return None
