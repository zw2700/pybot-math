"""A condition added to a choice is answered about the choice, not about the condition.

The person has just been given something to think about - a pet, a car, a move, a course - and
answers with the fact from their own life that decides it: "but i work long hours", "and i have a
small flat". The line names no thing of its own, so the knowledge entries for the choice cannot see
it, and whatever the condition reaches on its own wins the turn: "but i work long hours" after a
question about getting a cat was answered with the card about working hours and the rota, which is
a different conversation, while the pet entries hold exactly the answer wanted ("An adult cat is
fine with a working day...").

This module carries the thing in hand into the line and asks the knowledge base the question the
person would have made of it. It answers only when

- the line opens like an addition ("but", "and", "though", "only", "the thing is") and asks nothing,
- the store has nothing of its own for it, and
- the answer that comes back names the thing in hand, so an entry about something else cannot win.

So a condition that has an answer of its own keeps it, and a line that opens a new subject never
reaches this at all.
"""
import re

from . import repair as a_repair
from . import topics

# The ways a person adds a fact to what they were just told. "and" on its own is here because it
# is how a list of conditions is spoken: "should i get a cat or a dog" / "and i have a small flat".
CONDITION = re.compile(
    r"^(?:but|and|though|although|however|only|except|also|plus|mind you|the thing is|thing is|"
    r"the problem is|problem is|the catch is|my worry is)\b")
# A fact about the person offered without a joining word is the same thing: "im a beginner" after
# the gym induction, "i have about 400 pounds" after a choice. It is only ever a condition when it
# opens on the person saying something about themselves, so a line that starts anywhere else (a
# thing, a question, a greeting) never reaches this.
MINE = re.compile(r"^(?:im|i'm|i am|i have|i've|ive|i only|i just|i usually|i always|i never|"
                  r"i work|i live|we have|we've|we live|we work|my \w+ is)\b")

# A plan they are about to act on is a subject of its own, not a state of the person that
# constrains the choice in hand: "i booked flights to spain" / "im going to work on my cv" was
# answered with the Spain card, because "im going to ..." was read as a condition on the trip and
# the thing in hand was put back in front of the ask. The lines this reader is for are traits and
# facts - "im a beginner", "i work long hours", "i have 400 pounds" - and a state phrased with a
# plan keeps it ("im going to be out at work all day" after "should i get a dog"), so the frame
# is followed by a verb that is not be, have, need or want.
A_PLAN = re.compile(r"^(?:going to|gonna|about to|planning to|planning on|off to)\s+"
                    r"(?!be\b|have\b|need\b|want\b)\w")

# A job on a thing of their own is a subject of its own too. "also i need to fix my bike" after a
# question about fish was carried onto the fish - the ask built from it was "i need to fix my
# bike, ok so something with fish" - and the fish entry answered it with a new tank. The line is
# not a fact that decides the choice in hand: it is a piece of work on a different thing, and its
# own answer (or the reply that follows) is the turn.
A_JOB = re.compile(
    r"\b(?:need|needs|have|has|got|want|wants|ought|must)\s+to\s+"
    r"(?:fix|mend|repair|replace|service|sort|clean|build|install|fit|change|bleed|adjust|tune|"
    r"patch|pump|oil|grease)\b")

# A figure makes a personal line a quantity rather than a condition on a choice - a measurement,
# a budget, a count - and the store has its own readers for those, which say the figure back. So
# "im 5 foot 6 and 14 stone" keeps the store's answer rather than being taken as a condition on
# the wish to lose weight.
# A condition is a condition on a decision. The chat has to be about something the person is
# weighing up - a pet, a car, a course, a trip - because it is that decision the fact decides. A
# fact offered in the middle of a problem ("i have a work chair that doesnt adjust", after an
# answer about back pain) is not a condition on anything, and building an ask from it answered a
# chair with the general paragraph about back pain.
DECIDING = re.compile(
    r"\b(?:cook|cooking|bake|baking|make|making|eat|eating|dinner|tea|supper|lunch)\b|"
    r"\b(?:thinking (?:of|about)|should i|shall i|do i want|considering|im after|i'?m after|"
    r"im going to|i'?m going to|im about to|i'?m about to|im planning|planning to|"
    r"going to get|i want to get|what should i get|which one|worth it|do i need)\b", re.I)

# "ive been like this since about march" is not a fact that constrains a choice, it is how the
# person is, and the store's own readers answer it ("You've been like this since about march -
# noted."). Taken as a condition on the pet or the trip in hand, the ask built from it was won by
# the month and a hard feelings chat ended on a travel card.
A_STATE = re.compile(r"^(?:im|i'm|i am|ive|i've)\s+(?:been|felt|feeling|still|not|so|really|"
                     r"like\b)", re.I)

# A month or a weekday in a condition is a date, and a date is the store's to say back: the same
# feelings line reached the month entry ("Marrakesh or Seville at about 20C") through it.
A_DATE = re.compile(r"\b(?:january|february|march|april|may|june|july|august|september|october|"
                    r"november|december|monday|tuesday|wednesday|thursday|friday|saturday|"
                    r"sunday)\b", re.I)

A_FIGURE = re.compile(r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                      r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
                      r"half|a few|a couple)\b")

# Words that make the line a question about the choice rather than a condition on it. "but can i
# still have a cat" asks something and is answered as an ask.
ASKS = re.compile(r"\?|\b(?:can|could|should|would|will|do|does|did|is|are|was|were|what|how|"
                  r"why|when|where|which|who)\b")


def _flat(text):
    return " ".join(str(text or "").split())


def _the_thing_in_hand(text, memory):
    """The subject of the chat before this line: the newest topic that is not this line itself."""
    said = _flat(text).lower().rstrip(".")
    seen = []
    record = memory.get("topic")
    if isinstance(record, dict):
        seen.append(record)
    topics_seen = memory.get("topics")
    if isinstance(topics_seen, list):
        seen.extend(other for other in reversed(topics_seen) if isinstance(other, dict))
    for other in seen:
        words = _flat(other.get("text"))
        if not words or words.lower().rstrip(".") == said:
            continue
        thing = a_repair._the_thing_the_last_line_named(words)
        if thing:
            return words, thing
    return None, None


def _a_fresh_memory(memory):
    """The facts the person stated, without the chat: the ask is read as a line of its own.

    `aside` says so to the modules that read the store's own bookkeeping: the chat is not here, so
    nothing in it was just said, and a name in the facts is one the person gave turns ago
    (`bot/compose/__init__.py: _name_just_given`).
    """
    from ..understanding import understand  # noqa: PLC0415 - understanding imports this package

    fresh = {"turns": [], "aside": True}
    for key in ("user", "others", "facts_log"):
        if key in memory:
            fresh[key] = memory[key]
    return fresh


def _the_answer_without_the_condition(subject_text, memory):
    """What the knowledge base says to this line as it was said, on its own."""
    from ..modules import answers  # noqa: PLC0415 - answers imports this package

    try:
        return answers.respond(subject_text, _a_fresh_memory(memory)) or ""
    except Exception:
        return ""


def _named_in(reply, thing, subject):
    """Does the answer talk about the thing in hand? A plural counts as its own word."""
    said = _flat(reply).lower()
    if not said:
        return False
    for word in topics.keywords(subject):
        # The thing in hand is the one word the answer has to reach: an entry that scored on the
        # words of the condition alone answers about something else, and the person would be told
        # about a thing they never raised. The rest of the subject's words count as naming it,
        # because an entry writes the thing its own way ("rescue" for a rescue dog).
        forms = topics.forms(word) or {word}
        if word == thing or topics.alike(word, thing):
            forms = set(forms) | set(topics.forms(thing) or ()) | {thing}
        for form in forms:
            if re.search(r"\b" + re.escape(form) + r"\b", said):
                return True
    return False


def _already_on_the_screen(reply, memory):
    """Is this the answer the person has just read? Then the condition added nothing to it.

    "but we go away a lot" after "should i get a cat or a dog" reaches the same comparison the
    person has just been given, word for word, and a second copy of it framed as "same answer"
    is worse than the plain acknowledgement the composer would have said. The check is on the
    opening of the answer, which every entry writes its own way, and it searches the replies
    rather than matching them exactly, because a repeat is framed with a lead-in in front of the
    same body.
    """
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return False
    said = _flat(reply).lower()
    opening = " ".join(said.split()[:10])
    if not opening:
        return False
    # Every turn of the chat, not only the last: a condition that reaches an answer already given
    # reads as the same paragraph twice in one conversation, which is the thing the deck's
    # multi-turn rows exist to catch.
    return any(opening in _flat((turn or {}).get("bot")).lower() for turn in turns)


# A short list of the words that come after a determiner and name nothing the answer is about.
NOT_A_THING = frozenset((
    "bit", "few", "good", "great", "little", "load", "lot", "many", "moment", "quick", "right",
    "same", "sort", "thing", "time", "while", "whole",
))


# A thing named in a condition comes with the word in front of it that makes it one - "a cat",
# "my sister", "the flat". The words of a condition that carry nothing ("long", "hours", "busy")
# come without one, so this is what tells a thing of the person's own from a way they live.
A_NAMED_THING = re.compile(
    r"\b(?:a|an|the|my|our|your|his|her|their|another|no|two|three)\s+([a-z][a-z'\-]{2,})")

# How many things a verdict is tried against: the one it names last, and the one the chat named
# before it, which is the subject when the newest thing is a plan of theirs.
THE_MOST_THINGS_A_VERDICT_TRIES = 2


def _a_verdict_on_the_other_thing(reply, condition, thing, subject):
    """True when the answer weighs the thing in hand against a thing the condition named.

    "im thinking of getting a rescue dog" / "but i already have a cat" is a question about a dog
    in a house with a cat. The condition names a thing of its own - a cat - and the answer that
    came back is the cat-or-dog verdict: "Dogs, by a whisker... A cat is the kinder choice if
    you're out all day." That is an answer to a different question, so this module stands down
    and lets the chat say what it was going to say. A condition that names nothing ("but i work
    long hours", "but its busy in term time") is not this, and keeps its carried answer.
    """
    said = _flat(reply).lower()
    if not said:
        return False
    held = [str(word).lower() for word in topics.keywords(subject) or ()]
    for word in A_NAMED_THING.findall(_flat(condition).lower()):
        if word in NOT_A_THING or any(topics.alike(word, one) for one in held):
            continue
        if re.search(r"\b" + re.escape(word) + r"\b", said):
            return True
    return False


def _a_decision_in_the_chat(memory):
    """True when what the chat is about is something the person is weighing up."""
    said = []
    for turn in (memory.get("turns") or [])[-6:]:
        if isinstance(turn, dict) and turn.get("user"):
            said.append(str(turn["user"]))
    topic = memory.get("topic")
    if isinstance(topic, dict) and topic.get("text"):
        said.append(str(topic["text"]))
    return any(DECIDING.search(one) for one in said)


# The person asks for a verdict on what the chat has been about: "is that fair", "is that
# enough", "would that be ok", "is that too much". The line names nothing of its own, and a line
# made only of the ack words is read as agreeing with the turn before it, so every one of these
# was answered with the shrug "Fair enough." - which neither answers the question nor takes the
# chat anywhere. What the person wants is the judgement on their own case, which is the entry for
# the thing in hand asked again with what they have since said about it: "we are thinking of a
# dog" / "we both work full time" / "is that fair" is the working-day answer, not a shrug.
VERDICT = re.compile(
    r"\b(?:fair|ok|okay|alright|right|fine|enough|acceptable|reasonable|sensible|safe|legal|\n"
    r"    allowed|normal|typical|usual|weird|rude|polite|necessary|worth|expensive|cheap|\n"
    r"    bad|good|wise|risky|dangerous|healthy|a problem|an issue|a mistake|a good idea|\n"
    r"    a bad idea|too much|too many|too long|too short|too big|too small|too early|too late)\b".replace(
        "\n", ""), re.I)
# What a verdict question is made of, once the verdict word is taken out: the question's own
# grammar and the filler people put round it ("is that really too much then"). A line with any
# other word in it names something of its own and is somebody else's question.
VERDICT_FILLER = frozenset("""a an the that this it they these those there is are was were be
been being would will shall do does did should can could i we you me us my our your his her their
too so really very quite all then still just much many long short big small early late often
now good bad ok okay fine right thing one to of in on for with get getting have has had if what
how more less time way idea problem issue mistake deal worth going go at as by from up out and
the""".split())
# The line has to ask: the question in front ("is that fair") or the mark on the end of it
# ("that is fair?"). A statement of the same words is agreement, and the chat's ack pool is
# right about it.
ASKS_A_VERDICT = re.compile(
    r"^(?:is|are|was|were|would|will|shall|do|does|did|should|can|could|have|has)\b", re.I)


def _a_verdict_asked(clean):
    """True when the whole line is a verdict asked about the chat, not a thing of its own."""
    low = clean.lower().strip(" .!")
    if not low or not VERDICT.search(low):
        return False
    if "?" not in clean and not ASKS_A_VERDICT.match(low):
        return False
    for word in re.findall(r"[a-z']+", low):
        if word in VERDICT_FILLER or VERDICT.search(word):
            continue
        return False
    return True


def the_verdict_in_the_chat(text, memory):
    """The verdict on the thing in hand, asked with what the person has since said, or None.

    Only the facts they have added since the thing was named go in front of it ("we both work
    full time"), because those are what the verdict is about: a chat about a dog and then a fact
    about working hours is a question about a dog left alone all day. The ask is read as a line
    of its own, and the answer has to name the thing in hand, so an entry that scored on the
    words of the fact alone cannot win.
    """
    line = _flat(text)
    if len(line.split()) > 8 or not _a_verdict_asked(line):
        return None
    for subject_text, thing, since in _the_things_the_verdict_is_about(memory, line):
        reply = _the_verdict_answer(memory, line, subject_text, thing, since)
        if reply:
            return reply
    return None


def _the_verdict_answer(memory, line, subject_text, thing, since):
    """The answer to a verdict about one thing the chat named, or None."""
    if not subject_text or not thing:
        return None
    from ..modules import answers  # noqa: PLC0415 - answers imports this package

    # The facts they added come first and the thing in hand last, the order people say them in
    # ("we both work full time, what about a dog") and the order the entries are written against.
    asked = ", ".join([one for one in since if one] + [subject_text, line])
    try:
        reply = answers.respond(asked, _a_fresh_memory(memory))
    except Exception:
        return None
    if not isinstance(reply, str) or not reply.strip():
        return None
    if not _named_in(reply, thing, subject_text):
        return None
    if _already_on_the_screen(reply, memory):
        # The verdict is a paragraph the person has already read. When it is the answer just given,
        # standing down is right: the composer's acknowledgement answers "but we go away a lot"
        # better than a second copy of the comparison would. When it is from earlier in the chat,
        # standing down handed the turn to the chat module's own line about the thing - "is that
        # dangerous" about a boiler answered "Worth doing rather than worrying about" while the
        # pressure answer the verdict repeats held the answer - so it goes back framed as the
        # repeat it is, in the whole of itself (`bot/memory/again.instead`, `earlier=True`).
        if not _the_answer_just_given(reply, memory):
            try:
                from . import again as _again  # noqa: PLC0415 - same package, imported late
                framed = _again.already_had(reply, memory)
            except Exception:  # noqa: BLE001 - the plain answer is still the answer
                framed = None
            if framed:
                return framed
        return None
    return reply.strip()


def _the_answer_just_given(reply, memory):
    """True when this reply is the last answer word for word, or the opening of it."""
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return False
    mine = _flat(reply).lower()
    last = _flat(turns[-1].get("bot")).lower()
    if not mine or not last:
        return False
    return mine == last or last.startswith(mine) or mine.startswith(" ".join(last.split()[:10]))


def _the_things_the_verdict_is_about(memory, line):
    """The things the chat named that the verdict could be about, newest first.

    The thing is the last one the chat named with a word in front of it - "a dog", "the kitchen" -
    and a line that names no thing ("we both work full time") is what the verdict is about rather
    than the thing it is about, so it is carried along in front of it and never becomes one.

    More than one is offered because the newest thing named can be the person's own plan for the
    chat's subject - "my boiler keeps losing pressure" / "im going to bleed the radiators" /
    "is that dangerous" - and no entry answers a verdict about a plan: the question is still about
    the boiler, so the thing named before it is tried in its place.
    """
    said = _flat(line).lower().rstrip(".")
    order = []
    for other in _the_lines_of_the_chat(memory):
        words = _flat(other)
        if not words or words.lower().rstrip(".") == said:
            continue
        if order and order[-1].lower().rstrip(".") == words.lower().rstrip("."):
            continue
        order.append(words)
    found = []
    for index in range(len(order) - 1, -1, -1):
        one = order[index]
        thing = _the_thing_they_named(one)
        if thing:
            found.append((one, thing, order[index + 1:]))
            if len(found) >= THE_MOST_THINGS_A_VERDICT_TRIES:
                break
    return found


def _the_thing_they_named(line):
    """The thing the line names with a word in front of it: "a dog", "my dog", "the kitchen".

    A thing comes with a determiner, and that is what tells the thing a verdict is about from a
    word that is only part of a figure or a way they live: "i take 1000 units of vitamin d" names
    no thing this way, and the question about it is the store's, not a verdict on a vitamin.
    """
    found = [word for word in A_NAMED_THING.findall(_flat(line).lower())
             if word not in NOT_A_THING and word not in NOT_A_THING_AS_A_MEASURE]
    return found[-1] if found else None


# A word in front of a thing makes it one, but "twice a day", "an hour" and "a week" are when and
# how long rather than what the person has: a verdict is about a thing, so these never become it.
NOT_A_THING_AS_A_MEASURE = frozenset((
    "day", "days", "week", "weeks", "month", "months", "year", "years", "hour", "hours",
    "minute", "minutes", "morning", "afternoon", "evening", "night", "nights", "weekend",
    "time", "times", "while", "moment", "second", "seconds", "chance", "lot", "lotta",
))


def _the_lines_of_the_chat(memory):
    """Every line the person said, oldest first.

    The history is the whole chat, including the lines nothing kept a topic for: "we go away a
    lot" after a question about a cat is answered by the greeting pool, so the topic record never
    moved, and reading the topics alone lost the fact the verdict is about.
    """
    order = []
    turns = memory.get("turns")
    if isinstance(turns, list):
        order.extend((turn or {}).get("user") for turn in turns if isinstance(turn, dict))
    return [one for one in (_flat(line) for line in order) if one]


def the_subject_in_the_condition(text, memory):
    """The answer to the choice with the person's own condition in it, or None."""
    line = _flat(text)
    if not line or ASKS.search(line):
        return None
    found = CONDITION.match(line.lower())
    mine = None
    if not found:
        mine = MINE.match(line.lower())
        if not mine or A_FIGURE.search(line.lower()):
            return None
        if A_STATE.match(line) or A_DATE.search(line):
            # A line about how they are, or one that names a date, is the store's own answer.
            return None
        if A_PLAN.match(line.lower()[mine.end():].strip()):
            # "im going to work on my cv" is what they are doing next, not a condition on the
            # choice two turns back: the answers have their own line for it or the next reader
            # takes it, and either is better than the card about the trip they have moved on from.
            return None
        found = mine
    if not found:
        return None
    if not _a_decision_in_the_chat(memory):
        return None
    subject_text, thing = _the_thing_in_hand(text, memory)
    if not thing:
        return None
    from ..modules import answers  # noqa: PLC0415 - answers imports this package

    # The words of the condition are said first and the thing in hand last, which is the order
    # people say them in ("i work long hours, is it fair to get a cat") and the order the entries
    # are written against.
    condition = line[found.end():].strip(" ,.?!")
    if not condition:
        return None
    if A_JOB.search(condition):
        job_thing = a_repair._the_thing_the_last_line_named(condition)
        if job_thing and job_thing != _flat(thing):
            # The job names a thing other than the one in hand: a new subject, not a condition on
            # the choice. The carry would put both in one ask and the entry for the thing in hand
            # would answer it with advice about something the person has moved on from.
            return None
    ask = "%s, %s" % (condition, subject_text)
    try:
        reply = answers.respond(ask, _a_fresh_memory(memory))
    except Exception:
        return None
    if not isinstance(reply, str) or not reply.strip():
        return None
    held = list(topics.keywords(condition) or ())
    own = _the_answer_without_the_condition(line, memory)
    if own and held and any(re.search(r"\b" + re.escape(word) + r"\b", own.lower())
                            for word in held[-1:]):
        # The limit has an answer of its own in the knowledge base, and that answer is about the
        # limit: "but i dont have scales" reaches the card about measuring with a mug. The carry
        # is for a condition with no answer of its own, and taking the turn away from this one
        # answered the cake instead - "im baking a cake" then "but i dont have scales" came back
        # as a two-layer sponge that never mentions scales.
        return None
    if not _named_in(reply, thing, subject_text):
        # An entry about something else scored on the words of the condition alone: the person
        # would have been answered about a thing they never raised.
        return None
    if _a_verdict_on_the_other_thing(reply, condition, thing, subject_text):
        return None
    if _already_on_the_screen(reply, memory):
        return None
    return reply.strip()


# --- a quality of the dish, when the line names no dish -----------------------
# The other half of the same job. A person who has just been offered something to cook answers
# with what they want out of it rather than with a dish: "hows about something cold", "anything
# warm", "something lighter". Nothing in the line names food, so no entry can reach it and the
# turn fell to the search hedge - while the knowledge base answers the same words the moment the
# course is in them:
#
#   hows about something cold          -> I'd rather not guess. A quick search online...
#   hows about something cold for pudding
#                                      -> Something cold: an Eton mess, a lemon posset, or affogato.
#   something lighter                  -> Got it. Is there anything you'd like a hand with?
#   something lighter for dinner       -> Quick: a chickpea salad in 10, or vegetable soup...
#
# The course is in the chat, so it is carried into the line the same way the condition above is.
QUALITY_LEAD = re.compile(
    r"^(?:(?:how|hows|what)\s+about\s+(?:a|an\s+)?|how\s+about\s+|whats\s+|what\s+is\s+"
    r"|and\s+|so\s+|ok(?:ay)?\s*,?\s*)*", re.I)
# The qualities a person names instead of a dish. They are all words a dish is picked for, and
# every one of them is about the food rather than about the person.
QUALITY_WORDS = frozenset("""
cold warm hot chilled filling fillin light lighter sweet savoury savory salty spicy mild creamy
cheesy quick quickish easy simple healthy fresher fresh veggie vegetarian vegan meaty
fishy hearty substantial summery wintery
""".split())
# The meal the chat is about, in the words a person uses for it. A sweet named anywhere in the
# last turn or two makes it a pudding chat, which is the one that had nothing at all.
A_PUDDING = re.compile(r"\b(?:pudding|puddings|pud|dessert|desserts|afters|sweet\s+course)\b", re.I)
A_MEAL = re.compile(r"\b(?:dinner|supper|lunch|brunch|meal|meals|cook|cooking|cooked|"
                    r"bake|baking|baked|recipe|dish|dishes|food|eat|eating|roast|hob|oven|"
                    r"fryer)\b", re.I)


def _the_quality(line):
    """The quality the line asks for, as "something cold", or None."""
    said = re.sub(r"\s+", " ", line).strip(" ,.!?").lower()
    if not said:
        return None
    lead = QUALITY_LEAD.match(said)
    if lead:
        said = said[lead.end():].strip(" ,.!?")
    if not said.startswith(("something ", "anything ", "summat ")):
        return None
    words = said.split()
    if len(words) < 2 or len(words) > 4:
        return None
    if any(word not in QUALITY_WORDS for word in words[1:]):
        return None
    return "something " + " ".join(words[1:])


# A quality the sweet cannot be. The person is on the pudding and says what they want out of it,
# and most qualities can be a pudding - cold, light, quick, creamy, sweet. Heat and savour are the
# meal's: "something spicy" a turn after the pudding was offered is the dinner being asked for
# again, and asked as a pudding it came back with a dessert and a tip about chilli in the same
# breath.
NOT_A_PUDDING = frozenset("spicy savoury salty meaty fishy hearty filling substantial ".split())


def _the_course(memory, quality=""):
    """"pudding" when the chat is about the sweet, "dinner" when it is about the meal, else None."""
    if not isinstance(memory, dict):
        return None
    # The person's own lines only. The knowledge base answers with a paragraph that mentions
    # eating and food whatever it is about, and read from the bot's side a chat about too much tea
    # was a chat about dinner.
    lines = [str(turn.get("user") or "") for turn in (memory.get("turns") or [])[-4:]
             if isinstance(turn, dict)]
    record = memory.get("topic")
    if isinstance(record, dict):
        lines.append(str(record.get("text") or ""))
    if not lines or not any(line.strip() for line in lines):
        return None
    said = " ".join(lines)
    words = set(str(quality or "").split())
    if A_PUDDING.search(said) and not (words & NOT_A_PUDDING):
        return "pudding"
    if A_MEAL.search(said):
        return "dinner"
    return None


def _is_a_hedge(reply):
    from ..compose import fallback  # noqa: PLC0415 - compose imports the memory package
    try:
        return bool(fallback.is_a_hedge(reply))
    except Exception:
        return False


def the_quality_in_the_chat(text, memory):
    """The dish that answers the quality the person asked for, or None."""
    line = _flat(text)
    if not line:
        return None
    quality = _the_quality(line)
    if not quality:
        return None
    course = _the_course(memory, quality)
    if not course:
        return None
    from ..modules import answers  # noqa: PLC0415 - answers imports this package

    # The knowledge base has its own reader for most of these words ("something light", "something
    # spicy", "something veggie" all reach a dish), and one that answers the line as it stands is
    # the better answer: this is only for the qualities it drops. The probe is a copy, so nothing
    # the entries remember is written back into the chat.
    probe = dict(memory)
    try:
        direct = answers.respond(line, probe)
    except Exception:
        direct = None
    if direct and not _is_a_hedge(direct):
        return None
    ask = "%s for %s" % (quality, course)
    try:
        reply = answers.respond(ask, _a_fresh_memory(memory))
    except Exception:
        return None
    if not isinstance(reply, str) or not reply.strip():
        return None
    if _is_a_hedge(reply):
        return None
    if _already_on_the_screen(reply, memory):
        return None
    return reply.strip()


# --- a limit on the answer before it ----------------------------------------
# The same job once more, for the line that only takes something away: "and no dairy" after a
# chicken dish, "no horror" after a film list. The understanding engine reads it as a limit
# (`understood["constraint"]` and `["excludes"]`), and bot/compose/limit.py cuts the answer above
# where the answer carries the thing ruled out. What it cannot do is answer again: asked for a
# chicken dish and then told "no dairy", the answer above does not hold the word "dairy" - the
# yoghurt in it does - so there is nothing to cut, and the turn fell to the search hedge:
#
#   what should i have for dinner / something with chicken
#   and no dairy    -> I'm not sure about that one, sorry - I'd rather not guess.
#
# The dish is in the chat, so the line is put to the knowledge base with the dish still on it
# ("something with chicken, no dairy") and the answer, which is dairy free, is the turn.
def _the_last_ask(lines, said):
    """The last line of the person's own that asked for something, near enough to still be on."""
    for line in reversed(lines):
        words = _flat(line).strip()
        if not words or words.lower().rstrip(".") == said:
            continue
        if len(words.split()) > 14:
            return None
        return words
    return None


# The foods a free-from thing is made of. An answer that never says "dairy" can still be a dairy
# answer: the chicken card's "the whole bird pulled into tacos with lime and yogurt" passed the
# dairy guard, and the word list on `FREE_FROM` was right there. Read both ways.
FREE_FROM_FOODS = {
    "dairy": ("milk", "cheese", "butter", "cream", "yogurt", "yoghurt", "custard", "ghee",
              "fromage", "kefir", "buttermilk"),
    "gluten": ("bread", "pasta", "flour", "couscous", "barley", "rye", "wheat", "noodle",
               "noodles", "cracker", "pastry"),
    "wheat": ("bread", "pasta", "flour", "couscous", "barley", "noodle", "noodles", "pastry"),
    "nuts": ("almond", "almonds", "cashew", "cashews", "walnut", "walnuts", "pecan", "pecans",
             "hazelnut", "hazelnuts", "pistachio", "pistachios", "peanut", "peanuts",
             "praline", "marzipan"),
    "nut": ("almond", "almonds", "cashew", "cashews", "walnut", "walnuts", "pecan", "pecans",
            "hazelnut", "hazelnuts", "pistachio", "pistachios", "peanut", "peanuts"),
    "peanuts": ("peanut", "peanuts", "groundnut", "satay"),
    "peanut": ("peanut", "peanuts", "groundnut", "satay"),
    "eggs": ("egg", "eggs", "mayonnaise", "meringue", "custard"),
    "egg": ("egg", "eggs", "mayonnaise", "meringue", "custard"),
    "meat": ("chicken", "beef", "pork", "lamb", "bacon", "ham", "sausage", "sausages",
             "mince", "turkey", "chorizo", "steak"),
    "pork": ("bacon", "ham", "sausage", "sausages", "chorizo", "gammon", "prosciutto"),
    "beef": ("steak", "mince", "burger", "burgers", "brisket"),
    "fish": ("salmon", "tuna", "cod", "haddock", "prawn", "prawns", "anchovy", "anchovies",
             "sardine", "sardines", "mackerel", "trout"),
    "shellfish": ("prawn", "prawns", "crab", "mussel", "mussels", "lobster", "scallop",
                  "scallops", "prawn", "squid"),
    "soya": ("soy", "soya", "tofu", "edamame", "tempeh"),
    "soy": ("soy", "soya", "tofu", "edamame", "tempeh"),
    "sugar": ("honey", "syrup", "jam", "chocolate", "biscuit", "cake", "sweets"),
    "salt": ("salted", "crisps", "bacon", "soy", "soya", "stock cube"),
}


def _speaks_of(reply, things):
    """True when the answer carries the thing that was ruled out, by its name or as a food."""
    said = _flat(reply).lower()
    for thing in things:
        forms = {thing} | set(topics.forms(thing) or ())
        for food in FREE_FROM_FOODS.get(thing.lower(), ()):
            forms |= {food} | set(topics.forms(food) or ())
        for form in forms:
            if form and re.search(r"\b" + re.escape(form) + r"\b", said):
                return True
    return False


# The things a kitchen can be free of. The knowledge base has an answer for each of these on its
# own ("dairy free", "gluten free", "nut free"), so a dish asked for with one of them taken out can
# be answered again; a limit on anything else is a part of the answer above, which is the composer's
# job (bot/compose/limit.py), and re-asking about a word the entries have no dish for gains nothing.
FREE_FROM = frozenset("""
dairy gluten wheat nuts nut peanuts peanut eggs egg milk cheese butter cream meat pork beef fish
shellfish soya soy sugar salt spice spices chilli alcohol
""".split())


def _a_free_from(things):
    return all(any(topics.alike(word, known) for known in FREE_FROM) for word in things)


# The words of the ask that carry the subject and nothing else. "something with chicken" is about
# the chicken; the rest of it is how the question is put, so an answer does not have to say it.
CARRY_STOP = frozenset("""
something anything cook cooking make making tonight dinner lunch tea supper idea ideas meal meals
have want need what can could should recipes recipe please
""".split())


def _the_subject_named(reply, base):
    """Does the answer name the thing the ask was about? Then the ask was answered, not another."""
    said = _flat(reply).lower()
    for word in topics.keywords(base):
        if word in CARRY_STOP:
            continue
        for form in {word} | set(topics.forms(word) or ()):
            if form and re.search(r"\b" + re.escape(form) + r"\b", said):
                return True
    return False


def the_limit_in_the_chat(text, memory):
    """The dish or list the person still wants, with what they ruled out, or None."""
    if not isinstance(memory, dict):
        return None
    said = _flat(text).strip()
    read = memory.get("understood")
    if not isinstance(read, dict) or not read.get("constraint"):
        return None
    things = [str(thing).strip() for thing in (read.get("excludes") or []) if str(thing).strip()]
    if not things or len(said.split()) > 5 or not _a_free_from(things):
        # A limit and nothing else: "and no dairy" is the carry's, "and no dairy so what can i
        # have instead" asks its own question and is answered as one.
        return None
    lines = [str(turn.get("user") or "") for turn in (memory.get("turns") or [])[-3:]
             if isinstance(turn, dict)]
    base = _the_last_ask(lines, said.lower())
    if not base:
        return None
    from ..modules import answers  # noqa: PLC0415 - answers imports this package

    # Two ways of asking the same thing. The first is the ask they made with the limit in it.
    # The second is the same ask as a cook would put it, because the dish picker answers by the
    # words in the line: "something with chicken, no dairy" came back with the cuts of chicken to
    # cook and a recipe with yoghurt in it, while "what can i cook with chicken, no dairy" is the
    # entry on cooking round the dairy.
    asks = ["%s, no %s" % (base, " or ".join(things))]
    subject = [word for word in topics.keywords(base) if word not in CARRY_STOP]
    if subject:
        asks.append("what can i cook with %s, no %s"
                    % (" ".join(subject[:2]), " or ".join(things)))
    for ask in asks:
        try:
            reply = answers.respond(ask, _a_fresh_memory(memory))
        except Exception:
            continue
        if not isinstance(reply, str) or not reply.strip():
            continue
        if _is_a_hedge(reply) or _already_on_the_screen(reply, memory):
            continue
        if _speaks_of(reply, things):
            # An answer that still carries the thing they ruled out answers the wrong question -
            # unless what it carries is the thing being cooked round ("dairy free is easy to cook
            # around: oat milk in place of milk").
            if not _cooks_around_it(reply):
                continue
        elif not _the_subject_named(reply, base):
            # The dish picker answers by the words in the line, and a limit in it can move the pick
            # to another shelf: "ideas for a packed lunch, no nuts" came back with a potato hash.
            # An answer that never names what the ask was about is not that ask answered.
            continue
        return reply.strip()
    return None


# The words that make an answer *about* the thing ruled out rather than one carrying it: what to
# put in its place.
COOKS_AROUND_IT = re.compile(
    r"\b(?:in place of|instead of|swap(?:ped)?|replace|leave (?:it|that|them) out|"
    r"free[- ]from|free of|\w+[- ]free\b|without\b|use more|go easy on)\b")


def _cooks_around_it(reply):
    """True when the answer names the thing ruled out in order to say what goes in its place."""
    return bool(COOKS_AROUND_IT.search(_flat(reply).lower()))
