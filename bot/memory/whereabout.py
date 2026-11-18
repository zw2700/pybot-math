"""A place said on its own is the question just asked, in that place.

    any ideas for a cheap day out with kids
      -> Free ones that work: a walk with a purpose (a park, a canal, the woods) ...
    near leeds
      -> I'm listening - say more if it helps.                              (main)

"near leeds" is not news about the person, and it is not a question of its own. It is the question
they asked a turn ago with a place put on it, and the knowledge base answers that question: "Day
trips from Leeds: York (25 minutes by train), the Yorkshire Dales (an hour by car), Harrogate for
a spa afternoon". Main had nothing to do with the place, so it handed the line to the filler that
asks for more, which is the one thing a place is not.

So this reads the place out of the line, puts the question back with the place in it, and hands
that back as the line to answer. It decides nothing about the reply: the caller answers the
question it returns the way it answers any other question, and drops it when the answer it gets is
the hedge or the answer already on screen. That last part is what keeps a place said after a
question no place can narrow ("im knackered" then "near leeds") from being answered as if it were
the question.

A place is not only a name. "somewhere warm and cheap" after "i need a holiday" is the same
shape said as a wish: it is the question with what they want put on it, and the knowledge base
answers the two together ("The cheapest sun is the Algarve or the Costa Blanca outside July and
August"). Main answered the wish with "Thanks for telling me - I'm here if you want to dig into
any of that."

The rule is narrow on purpose:
* the line has to be a place and nothing else - "near leeds", "somewhere near leeds", "in
  birmingham", "round here" - so "its near leeds and the traffic was awful" stays a line of its
  own, and a bare "leeds" is left alone because a town on its own is as likely to be a plan as a
  place to go;
* the place has to be a place, so "in june", "in the morning", "near the oven" and "in bed" are
  not read as one;
* there has to be a question in the turn just finished, and one a place narrows ("where", "any
  ideas", "what should i do", "can you recommend"), so a place said after a statement is left
  alone;
* the place must be one the answer on screen does not already say, so an answer that named Leeds
  is not the whole question asked again.
"""
import re

# The way a place is said on its own: a lead-in and the place, and nothing else. "somewhere" and
# "anywhere" are people hedging about a place, so they lead one too.
PLACE_LINE = re.compile(
    r"^(?:(?:its|it'?s|it is|were|we'?re|we are|im|i'?m|i am|somewhere|anywhere|out)\s+)?"
    r"(?:right\s+)?(?P<lead>near|round|around|close to|not far from|outside of|outside|by|in)\s+"
    r"(?P<place>[a-z][a-z' .-]{1,28})$", re.I)

# A place asked for as a wish: "somewhere warm and cheap", "anywhere with sun". The words after
# "somewhere" are the thing the question gets narrowed by, so a place led in by one is read the
# same way and put back on the question the same way.
QUALIFIED_LINE = re.compile(
    r"^(?:somewhere|anywhere|out somewhere|away somewhere)\s+(?P<place>[a-z][a-z' -]{2,28})$",
    re.I)

# The words a place is not. A month or a day is a when, "the morning" and "bed" are a time of day,
# and the rooms are what "near" and "in" are said about in an answer that has just named one.
NOT_A_PLACE = frozenset("""
january february march april may june july august september october november december
jan feb mar apr jun jul aug sep sept oct nov dec
monday tuesday wednesday thursday friday saturday sunday
morning afternoon evening night nights week weekend month year
day days time times moment minute hour
bed home house garden kitchen oven bath bedroom lounge hall office car van toilet sink
here there it this that
fact general particular short long end total all once first last
future public private secret common advance writing person people
progress practice tears pain shock doubt error trouble
""".split())

# A question a place narrows, and only those: a place on the end of "what should i cook tonight"
# is a line about nothing, and the answer it reaches is another dish and not the place. So the ask
# has to be one that is about going somewhere, or about what there is where the person is.
ASKS_FOR_A_PLACE = re.compile(
    r"\b(?:where|somewhere|anywhere|place|places|ideas?|recommend|suggest(?:ion)?|"
    r"days? out|day trip|holiday|holidays|weekend away|getaway|trip|travel|visit|stay|"
    r"eat out|restaurant|pub|cafe|coffee shop|walk|see|explore|"
    r"go out|going out|things to do|whats on)\b", re.I)


def the_place(line):
    """The place a line that is only a place says, or "" for any other line."""
    text = (line or "").strip().strip(" .!,").lower()
    if not text or len(text.split()) > 5:
        return ""
    match = PLACE_LINE.match(text)
    if not match:
        # "somewhere warm and cheap" is the same shape said as a wish rather than as a place: it
        # narrows "i need a holiday" as surely as "near leeds" narrows "any ideas for a day out",
        # and the knowledge base answers the two of them together ("The cheapest sun is the
        # Algarve or the Costa Blanca outside July and August"). Main answered the wish with
        # "Thanks for telling me - I'm here if you want to dig into any of that."
        match = QUALIFIED_LINE.match(text)
        if not match:
            return ""
    place = match.group("place").strip(" .")
    if not place:
        return ""
    first = place.split()[0]
    if first in NOT_A_PLACE or place in NOT_A_PLACE:
        return ""
    # "in a minute" and "in an hour" are a when. A place is not said with an article in front of
    # it in a line this short.
    if first in ("a", "an"):
        return ""
    # "in the oven" and "in the garden" are a room, not a place to go: the words after the lead
    # are read for one of those too.
    if place.startswith("the ") and place[4:] in NOT_A_PLACE:
        return ""
    return place


def the_question_with_the_place(text, memory):
    """The question this line puts a place on, with the place in it; or "".

    The question is looked for in the three turns before this one, not only the last, because a
    place is often said after something else about the answer: "any ideas for a cheap day out with
    kids" then "its raining" then "near leeds" is still the day-out question with a place on it,
    and the answer the bot gave to the rain ("I'm listening - say more if it helps") is the one
    thing a place is not.
    """
    place = the_place(text)
    if not place:
        return ""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    for turn in reversed(turns[-3:]):
        if not isinstance(turn, dict):
            continue
        asked = str(turn.get("user") or "").strip()
        if not asked or not ASKS_FOR_A_PLACE.search(asked):
            continue
        # The place has to be new to this conversation: an answer that already says Leeds is not
        # answered by the question with Leeds on it.
        said = set(re.findall(r"[a-z']+", str(turn.get("bot") or "").lower()))
        if place.split()[0] in said:
            return ""
        return asked.rstrip(" ?.") + " " + (text or "").strip().strip(" .!")
    return ""
