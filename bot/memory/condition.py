"""The branch of the last answer that a short line of the person's own words chooses.

An answer often offers a side and names the case it is for: "Dogs, by a whisker ... A cat is the
kinder choice if you're out all day". When the person then says "i work all day", the answer has
already said what that means, and repeating their line back to them ("Got it - you work all day")
throws the answer away. This reads the conditions out of the answer we just gave and hands back
the consequence of the one their line matches, so the reply can be the choice, not an echo.

The match is on a pair of words, not a topic: "all day" is in both lines, where "i had a long day"
shares only "day" with "out all day" and is a different thing to say.

A case is about the person who asked. "my neighbour works all day" shares "all day" with "if
you're out all day" and says nothing about the flat the cat would live in, so it takes no case:
the branch is theirs only when the line is about them.
"""

import re

from . import facts

# One sentence at a time: a condition governs the clause it is in, and the sentence after it is
# the next thing said.
# A full stop between two digits is part of the number, not the end of a sentence: "check the
# pressure is 1 to 1.5 bar, and if it carries on get a heating engineer to look at the pump" was
# cut after "1", so the case's consequence came out as the fragment "5 bar, and" and the reply
# to "its the pump i think" was "It's the pump you think. 5 bar, and, then."
SENTENCE = re.compile(r"(?:(?:\d\.\d)|[^.!?])+[.!?]?")
# The words that open a condition and are not part of it.
OPENS = re.compile(r"^(?:if|when|unless|in case)\s+", re.I)
# The words that open a condition, anywhere in a sentence. A second one inside the first one's
# clause is part of that condition, not a case of its own (see `conditions`).
CONDITION_WORD = re.compile(r"\b(?:if|when|unless|in case)\b", re.I)
# What ends a condition that comes first in its sentence: ", a cat is kinder" and "and then" are
# the answer, not the case.
BREAK = re.compile(r"\s*(?:,|;|:|\u2014|\s-\s|\band then\b|\bthen\b)", re.I)
# Words that carry no subject of their own, so a pair of them says nothing about the two lines
# being about the same case.
EMPTY = frozenset("""a an the i im you your youre we us our it its that this there
here to of in on at for with and or but if then so as is are was were be been am do does did
have has had got get all just really very too not no now some any my me him her his hers them
they their what which who whom whose how why when where""".split())
MOST_LETTERS = 90
# A case is one thing about the person: "you're out all day". A longer one has picked up the
# rest of the sentence and is not a case a short line can state.
MOST_CASE = 60
# A case that runs on without a comma into the rest of the sentence has swallowed the remedy:
# "if it carries on get a heating engineer to look at the pump" is not one case, it is the case
# and the thing to do about it. A run-on that carries an instruction of its own is that shape, and
# its own words say so - the verb of the instruction - without counting anything: "see a doctor"
# and "ring the vet" are in every remedy-then-if sentence in the knowledge base ("See a doctor if
# it lasts more than three weeks or comes with a fever"), so those readings stay, and only the
# run-on that both never pauses and tells the person to do something is dropped.
RUNS_ON = re.compile(r"\b(?:get|ring|call|take|keep|see|use|put|leave|buy|stop|go|try|"
                     r"check|ask|tell|give|make|book|contact|wash|clean|apply|move|add|"
                     r"rest|ice|eat|drink)\b", re.I)


# A case that says where the person is turns on that word: "if you're out all day" is for the
# person who is out, and "im at home all day" is the other one. The pair match alone shared
# "all day" and handed the cat to somebody who is in, which is a false line and worse than the
# echo it replaced. So when both the case and their line name a place, the places have to be the
# same one; a line that says nothing about where ("i work all day") still takes the case.
PLACE = frozenset("""out outside away outdoors home house indoors inside office in""".split())


def _places(words):
    return {word for word in words if word in PLACE}


def _words(text):
    """The words of a line, with the apostrophe taken out so "you're" meets "youre"."""
    return re.findall(r"[a-z]+", str(text or "").lower().replace("\u2019", "'"))


def _pairs(words):
    """Every two words that sit next to each other and are not both empty ones."""
    return {first + " " + second for first, second in zip(words, words[1:])
            if first not in EMPTY or second not in EMPTY}


# The people a line is about when it is not about the person typing: "my neighbour works all
# day", "my sister is out all day". The pair match cannot tell whose day it is, and the case the
# answer named is about theirs.
#
# A bare pronoun ("she works all day", "they are out all day") is somebody else's day too, but it
# is left alone here: the knowledge modules read "works all day" as the ask about leaving a dog,
# so with the case branch out of the way the line got a page about a working day instead of the
# echo. Fixing that belongs in the dog entry, which is another lane's file, so this reads only
# what it can answer itself.
PERSON = frozenset(facts.RELATIONS) | frozenset("""neighbour neighbor friend boss manager
colleague coworker roommate flatmate housemate landlord partner kids kid child children baby
toddler twins sister brother son daughter""".split())
MY_PERSON = re.compile(r"\b(?:my|our)\s+([a-z]+)")
# The words that make a case one about somebody in particular rather than about the person
# typing: "if someone in the house is allergic" is a case about a member of the household, so a
# line naming one ("my son is allergic") states that case and not another person's day.
A_PERSON_IN_IT = frozenset(PERSON) | frozenset("""someone anyone somebody anybody child children
    baby toddler guest visitor family relatives""".split())
# A line that is a plan or an errand of their own is not the case they are in: "i want to fix the
# door" beside a case about the door is the composer's turn, and saying the case's consequence
# would answer a question they did not ask.
A_PLAN = re.compile(r"\b(?:i|we)(?:m|re| am| are)?\s+(?:want|wanna|need|plan|intend|have to|"
                    r"must|should|will|would like|am going|are going|going to|think i|ll|will)\b",
                    re.I)


def about_someone_else(text):
    """Whether the line is about one of the people in it rather than the person typing.

    A family word after "my" is not proof on its own - "my wife and i are out all day" is the
    household and does take the case - but a short line matched on a pair of words is worth less
    than the echo it replaces when the pair belongs to somebody else, so the reading refuses.
    The pronoun is the other half: "she works all day" is her day.
    """
    low = str(text or "").strip().lower().replace("\u2019", "'")
    return any(word.rstrip("'s") in PERSON for word in MY_PERSON.findall(low))


def _sentences(said):
    return [part.strip() for part in SENTENCE.findall(str(said or "")) if part.strip()]


def _one_move(consequence):
    """The first move of a consequence: a long one is cut at a clause boundary, not dropped.

    "pay a local pest controller, usually 50 to 80 pounds, rather than going up a ladder with a
    spray - and do not block the entrance, because they will find another way into the house" is
    one consequence of a case and three sentences' worth of text: what the case is worth saying is
    its first move, and dropping it for the length of its tail lost the case altogether.
    """
    text = str(consequence or "").strip(" ,;:-\u2014.")
    kept = text
    if len(text) > MOST_LETTERS:
        kept = ""
        for piece in re.split(r",\s+|\s+-\s+|\s+\u2014\s+", text):
            trial = (kept + ", " + piece) if kept else piece
            if len(trial) > MOST_LETTERS and kept:
                break
            kept = trial
    kept = kept.strip(" ,;:-\u2014")
    # A clause never ends on the word that was going to join it to the next one. "5 bar, and"
    # reached the reply as "... 5 bar, and, then.", which is not a sentence in any reading.
    # The junction word has to be a word of its own: without the separator in front, the strip
    # took the last two letters off real ones - "See a doctor" came back as "See a doct" and
    # "tell your husband" as "tell your husb".
    kept = re.sub(r"(?:[\s,;:]+)(?:and|but|or|so|then|with|plus)$", "", kept, flags=re.I)
    return kept.strip(" ,;:-\u2014")


def conditions(said):
    """[(the case, what the answer says happens in that case)] for every "if" in the answer."""
    found = []
    for sentence in _sentences(said):
        for opening in CONDITION_WORD.finditer(sentence):
            before = sentence[:opening.start()].strip(" ,;:-\u2014")
            # A condition nested inside another one's clause - "if the mark is still there when it
            # has dried, a soak in oxygen bleach lifts it" - is part of the first, not a case of
            # its own. Read on its own, its case is the tail ("it has dried") and the thing that
            # happens in that case is the first condition said back, so "it happened last night
            # so its dried" was answered "It happened last night so it's dried. If the mark is
            # still there, then." The outer condition is read below and says the remedy.
            if CONDITION_WORD.search(before):
                continue
            rest = sentence[opening.end():].strip()
            rest = OPENS.sub("", rest).strip()
            cut = BREAK.search(rest)
            if cut is None and before and RUNS_ON.search(rest):
                continue
            if cut is None and not before:
                # A sentence that opens with the case and never pauses: "if you are out at work
                # all day a cat copes better". The noun phrase after it is the answer, and an
                # article is where it starts.
                opening_at = re.search(r"\s+(?=(?:a|an|the)\s)", rest)
                if opening_at:
                    cut = opening_at
            # An "if" inside a list is part of an item, not a condition of its own: "rehearse the
            # small things: where they line up, who to ask if they are lost, and how lunch works"
            # read the remedy as everything before it, so "he is worried about getting lost" was
            # answered "He is worried about getting lost. Walk the route to school ..., then."
            # Nothing before a colon is the answer to the "if" after it.
            if before and re.search(r"[:;]", before):
                continue
            case = (rest[:cut.start()] if cut else rest).strip(" ,;:-\u2014.")
            after = rest[cut.start():] if cut else ""
            after = re.sub(r"^\s*(?:,|;|:|\u2014|\s-\s|\band\b|\bthen\b)\s*", "", after, flags=re.I)
            # The consequence is on the side of the "if" that still says something: before it
            # when the sentence opens with the choice, and after it when the sentence opens with
            # the case ("if you're out all day, a cat is kinder").
            consequence = before if len(_words(before)) >= 2 else after.strip(" ,;:-\u2014.")
            if not case or not consequence:
                continue
            if len(case) > MOST_CASE:
                continue
            consequence = _one_move(consequence)
            if not consequence:
                continue
            found.append((case, consequence))
    return found


# A case can test a number: "repair it if it is under five years old", "go if it is over 40",
# "walk if it is less than two miles". Words do not test it - "its 8 years old" shares "years
# old" with "under five years old" - so the number they gave is compared with the number the
# case names, and a case their line fails is not their case. Both halves are needed: the number
# and the unit it counts. The units are the ones an everyday answer tests.
UNITS = frozenset("""year month week day hour minute mile km kilo stone pound percent""".split())
NUMBERS = {word: value for value, word in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty "
    "ninety hundred".split())}
# The comparator in front of the number, read as "their number has to be below (or above) this".
BELOW = ("under", "below", "less than", "fewer than", "up to", "at most", "no more than",
         "within", "younger than", "shorter than")
ABOVE = ("over", "above", "more than", "past", "older than", "longer than", "beyond",
         "at least", "from", "at")
MOST_WORDS_BEFORE = 3


def _number(word):
    word = str(word or "").strip(".,")
    if word.isdigit():
        return float(word)
    return float(NUMBERS[word]) if word in NUMBERS else None


def _measures(text):
    """{unit: number} for every "<number> <unit>" in a line, digits or words alike."""
    found = {}
    words = re.findall(r"[a-z0-9.]+", str(text or "").lower())
    for index, word in enumerate(words):
        unit = word.rstrip("s")
        if unit not in UNITS or not index:
            continue
        value = _number(words[index - 1])
        if value is None and index > 1 and words[index - 1] in ("a", "an"):
            value = 1.0
        if value is not None:
            found.setdefault(unit, value)
    return found


def _tests(case):
    """[(unit, number, "below"|"above")] for every number a case tests."""
    found = []
    words = re.findall(r"[a-z0-9.]+", str(case or "").lower())
    for index, word in enumerate(words):
        unit = word.rstrip("s")
        value = _number(words[index - 1]) if index else None
        if unit not in UNITS or value is None:
            continue
        around = " ".join(words[max(0, index - 1 - MOST_WORDS_BEFORE):index - 1])
        side = ("below" if any(lead in around for lead in BELOW) else
                "above" if any(lead in around for lead in ABOVE) else "")
        if side:
            found.append((unit, value, side))
    return found


def _meets(case, text):
    """Whether the numbers the line gives pass the numbers the case tests.

    True when every test is passed, False when one is failed, and None when the case tests
    nothing this line gives a number for - which leaves the case to the word match alone. The
    line itself is read, not its words alone: a number is not a word.
    """
    mine = _measures(text)
    judged = False
    for unit, value, side in _tests(case):
        if unit not in mine:
            continue
        judged = True
        theirs = mine[unit]
        if side == "below" and not theirs < value:
            return False
        if side == "above" and not theirs > value:
            return False
    return True if judged else None


def chosen(text, said):
    """The consequence the last answer gave for the case this line states, or None.

    Only one reading is allowed: the line has to share a pair of words with the case, so "i work
    all day" takes the "out all day" branch while "i had a long day" takes nothing. A case that
    tests a number also has to be passed by their number, because a shared unit says nothing
    about which side of the test they are on.
    """
    for case, consequence in _candidates(text, said):
        if _meets(case, text) is False:
            continue  # "its 8 years old" does not take the case that is under five
        return consequence
    return None


def refused(text, said):
    """Whether the last answer put a test on the number this line gives, and their number fails.

    The other half of the same reading: "repair it if it is under five years old" is answered
    "its 8 years old", and the answer's verdict does not apply to them. The caller says the fact
    back and stops, which is the honest reply - the answer itself already said what to do about
    the two cases it named, and neither of them is this one.
    """
    return any(_meets(case, text) is False for case, _ in _candidates(text, said))


def _carried(case_words, words):
    """Whether the line carries what the case turns on, when no pair of words can be shared.

    A case is often one word that matters - "if it is by a door", "if someone in the house is
    allergic" - and a line that says it in its own words ("its right by the back door", "my son
    is allergic") shares no pair with it. The words that carry no subject are dropped, and what is
    left of the case has to be met: all of a short case, and most of a long one, whose tail has
    picked up the rest of its sentence.
    """
    want = {w for w in case_words if w not in EMPTY}
    if not want:
        return False
    met = want & set(words)
    if not met:
        return False
    return len(met) == len(want) or (len(want) >= 3 and len(met) * 2 >= len(want))


def _about_a_person(case_words):
    """Whether the case itself names somebody, so a line about theirs can be that case."""
    return any(w.rstrip("'s") in A_PERSON_IN_IT for w in case_words)


def _candidates(text, said):
    """The (case, consequence) pairs of the answer this line can be matched to in words."""
    if A_PLAN.search(str(text or "")):
        return []
    words = _words(text)
    if not words or len(words) > 8:
        return []
    mine = _pairs(words)
    found = []
    for case, consequence in conditions(said):
        case_words = _words(case)
        # "if it is by a door or someone in the house is allergic" is one case written as two, and
        # the person naming either of them is in it: each half is read on its own.
        # The halves of a case written as two, and the tail of a condition that carries its own
        # timing: "the mark is still there when it has dried" is met by a line that says the
        # thing has dried, and the remedy the answer gave for it ("a soak in oxygen bleach
        # usually lifts it") is then the reply, where reading only the whole case left the line
        # to the wrong entry. The head of that split is kept as one half too, so nothing that
        # matched before stops matching.
        halves = [_words(one) for one in
                  re.split(r"\bor\b|\bwhen\b", case, flags=re.I) if one.strip()]
        hit = False
        for half in halves:
            if not (mine & _pairs(half) or _carried(half, words)):
                continue
            theirs, ours = _places(half), _places(words)
            if theirs and ours and not (theirs & ours):
                continue  # the case says one place and their line says another: not their case
            hit = True
            break
        if not hit:
            continue
        if about_someone_else(text) and not _about_a_person(case_words):
            continue  # her afternoon is not their case, whatever the two lines share
        found.append((case, consequence))
    return found
