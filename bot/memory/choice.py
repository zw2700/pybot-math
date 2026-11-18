"""When the person hands the decision back: "you pick", "your call", "either is fine".

The bot offered two or three things a turn ago ("pasta, eggs on toast, or cold rice"), and the
person answers "you pick". That is not a new question about the world: it asks the bot to
choose between options it has just proposed. Reading it back as a fresh question gives a search
hedge, and reading it as nothing gives "Noted!".

So this reads the bot's own last reply, takes the options out of it and says one. It keeps the
choice general: a bulleted list, a "X, Y or Z" list, italics (*Groundhog Day*) and a "would you
rather X or Y?" question are all read the same way, so every lane's answers get followed up on
without each of them teaching the bot about picks.

It is deliberately narrow. The whole line has to be the ask (a real question like "which one
would you pick for a wedding present?" carries its own subject and belongs to the answers
lane), and a reply with no readable list of two or more options returns None, so the rest of the
bot answers as it did before.
"""
import random
import re

from ..compose import pick

from . import last_bot, recent

# The whole line, asking the bot to choose. Short, and about the offer rather than about the
# world: "you pick", "you choose the film", "your call", "up to you", "surprise me".
_LEAD = r"^(?:(?:ok|okay|fine|right|well|so|then|hmm|ha)[, ]+)*"
_PICK_ASK = re.compile(
    _LEAD +
    r"(?:"
    r"(?:you|u|yous)[ ]?(?:pick|choose|decide|select|choose one|pick one|decide for me)"
    r"|(?:you|u) (?:can )?(?:pick|choose|decide)(?: (?:one|it|for me|the (?:one|rest|\w+)))?"
    r"|your (?:call|choice|pick|decision)"
    r"|(?:i'?ll |i will |i'?d )?let you (?:pick|choose|decide)(?: (?:one|it|for me|this time))?"
    r"|(?:can|could|will|would) you (?:pick|choose|decide)(?: (?:one|it|for me))?"
    r"|up to you|over to you|you tell me|you know best|surprise me"
    r"|(?:i )?(?:don'?t|do not) mind[, ]+you (?:pick|choose|decide)"
    r"|(?:either|any|whatever)(?: one| of (?:them|those|these))?(?: is| are)? (?:fine|good|ok|okay)"
    r"(?:[, ]+(?:you|u) (?:pick|choose|decide))?"
    r"|(?:you|u) (?:pick|choose|decide)(?:[, ]+(?:i )?(?:don'?t|do not) mind)?"
    r")"
    r"(?: (?:then|please|thanks|for me|between (?:them|those|these|the two)))?"
    r"[.?!]*$", re.I)

# A piece of a reply that is not an option: a clause with a verb in it ("tell me what is in the
# fridge and i will pick one"), a question, a hedge.
_CLAUSE = re.compile(
    r"\b(?:i|i'll|i'd|you|you'll|we|they|tell me|let me|if|but|because|which|whichever|whatever|"
    r"search|google|not sure|don'?t know)\b", re.I)

_TAIL_STRIP = re.compile(r"[\s.;:,]+$")
# Words that make a comma-separated piece a step in a method rather than a thing to choose.
_STEP = re.compile(r"\b(?:with|then|until|after|before|for \d|at \d|under|onto|over|into|"
                   r"using|while|once)\b", re.I)
# Words that make a piece a description rather than one of the things on offer: the tail of a
# sentence ("veg are all nut-free", "potatoes works").
_NOT_A_THING = re.compile(r"\b(?:so|are|is|was|were|works|tastes|means|are)\b|^-", re.I)


def _clean_option(piece):
    """One option, trimmed, or "" when the piece is a clause rather than a thing to choose."""
    piece = piece.strip(" \t*_-\u2014")
    piece = re.sub(r"^(?:or|and|either|then|else)\s+", "", piece, flags=re.I)
    piece = _TAIL_STRIP.sub("", piece)
    words = piece.split()
    if not piece or len(words) > 11 or len(piece) > 70:
        return ""
    if _CLAUSE.search(piece):
        return ""
    if piece[-1:] in "?!:" or piece.endswith("..."):
        return ""
    return piece


def _from_italics(text):
    """Options marked out as titles: "*Groundhog Day* for comedy, or *Arrival* ..."."""
    found = re.findall(r"\*([^*\n]{2,40})\*(?: ([^,;.\n]{1,30}))?", text)
    options = []
    for title, tail in found:
        title = _clean_option(title)
        if not title:
            continue
        # A tail that is a clause ("if you want energy") is the bot's reason, not part of the
        # name: keep the name alone so the pick can still be said.
        tail = "" if _CLAUSE.search(tail or "") else (tail or "")
        options.append(_clean_option((title + " " + tail).strip()) or title)
    return options


def _segment(text):
    """The part of a line that could hold the list: after a colon or a dash, else all of it."""
    body = text
    for sep in (":", " \u2014 ", " - "):
        head, found, tail = body.rpartition(sep)
        if found and len(tail.split()) >= 2:
            return tail
    return body


def _from_list(text):
    """A plain list: "pasta with garlic and oil; eggs on toast; or cold rice fried with veg"."""
    body = _segment(text)
    # A sentence that follows the list ("Tell me what is in the fridge and I will pick one")
    # is not one of the options.
    body = re.split(r"\.\s+[A-Z]", body)[0]

    def things(pieces, steps=False):
        """The pieces that are a thing to choose, not a step or the tail of a sentence.

        A piece split off by a semicolon or an "or" is a list item whatever words it uses
        ("cold rice fried with frozen veg"); a piece split off only by a comma can be a step in
        a method ("a quarter turn at a time"), so only those are checked for step words.
        """
        out = []
        for piece in pieces:
            if _NOT_A_THING.search(piece) or (steps and _STEP.search(piece)):
                continue
            option = _clean_option(piece)
            if option:
                out.append(option)
        return out

    # Only a reply that offers a choice is read as one: a measurement "20 minutes per 500g,
    # then rest it" is a single answer with a comma in it, not two options.
    if " or " in body.lower() or ";" in body:
        pieces = [p for p in re.split(r";", body) if p.strip()]
        options = things(pieces)
        if len(options) < 2:
            options = things([p for p in re.split(r",\s+|\s+or\s+|\s+and\s+", body) if p.strip()])
        if len(options) >= 2:
            return options
    # A comma list is an offer when it is three or more short things ("nice soap, woolly socks,
    # a book"): "a radiator key, a quarter turn at a time, with a cloth under it" is one
    # instruction with commas in it, not a choice.
    comma = [o for o in things([p for p in re.split(r",\s+", body) if p.strip()], steps=True)
             if len(o.split()) <= 8]
    return comma if len(comma) >= 3 else []


def _from_labels(text):
    """A reply that answers with named dishes or options and explains each: "Scrambled eggs: ...
    Aglio e olio: ..." The names are the things to choose between, not the explanations."""
    labels = []
    for label in re.findall(r"(?:^|[.;]\s+)([A-Za-z][^:.;\n]{2,30}):", text):
        option = _clean_option(label)
        if option:
            labels.append(option)
    seen, unique = set(), []
    for label in labels:
        if label.lower() not in seen:
            seen.add(label.lower())
            unique.append(label)
    return unique


def _from_question(text):
    """The bot's own either/or question: "Would you rather go Saturday or Sunday?"."""
    if not text.rstrip().endswith("?") or " or " not in text.lower():
        return []
    body, again = re.subn(r"^\W*(?:so |then )?(?:would you rather|would you prefer|shall we|"
                          r"do you want|do you fancy|which would you rather|are you (?:thinking|"
                          r"leaning)|how about|which one)\s+", "", text.strip(), flags=re.I)
    if not again:
        return []
    body = body.rstrip("?")
    return [_clean_option(p) for p in re.split(r"\s+or\s+", body) if _clean_option(p)]


def options_in(reply):
    """The options the bot offered in one reply, or [] when it did not offer a choice."""
    if not reply:
        return []
    text = " ".join(str(reply).split())
    for reader in (_from_italics, _from_labels, _from_question, _from_list):
        options = reader(text)
        # The same thing twice ("the pasta, pasta") is not a choice.
        seen, unique = set(), []
        for option in options:
            key = option.lower()
            if key not in seen:
                seen.add(key)
                unique.append(option)
        if len(unique) >= 2:
            return unique
    return []


def asks_for_a_pick(text):
    """True when the whole line hands the choice back to the bot."""
    low = " ".join(str(text or "").lower().split())
    return bool(_PICK_ASK.match(low))


PICKS = (
    "My pick: {option}.",
    "I'd say {option}.",
    "If it were me: {option}.",
    "{option} \u2014 that's the one I'd choose.",
)


# The person asked for suggestions, and the bot answered with options. Without that, handing
# the choice back ("either is fine thanks") is a comment, not a question: only a line that asked
# for help makes choosing one of the bot's own options the natural next turn.
_ASKED = re.compile(r"^(?:\W*(?:what|which|who|when|where|why|how|any|anyone|anything|can|could|"
                    r"should|would|do|does|did|is|are|shall|give me|tell me|suggest|recommend)\b"
                    r"|.*\?\s*$)", re.I)


def _from_user_line(memory):
    """The choice the person put on the table themselves: "should i get a cat or a dog".

    When the bot's own answer offered nothing, the options the person named are still the
    choices in front of them, and "you pick" still means one of those.
    """
    turns = recent(memory, 1)
    line = " ".join(str((turns[-1].get("user") if turns else "") or "").lower().split())
    if " or " not in line:
        return []
    body = re.sub(r"^\W*(?:(?:so|ok|okay|but)[, ]+)?(?:should|could|do|would|shall|can|will)\s+"
                  r"(?:i|we)\s+|^\W*(?:is it better to|which is better,?|what about|"
                  r"is it worth)\s+", "", line.rstrip("?"))
    options = []
    for piece in re.split(r"\s+or\s+", body):
        option = _clean_option(piece)
        if option and len(option.split()) <= 5:
            options.append(option)
    if len(options) < 2:
        return []
    # "get a cat or get a dog" is a choice between the cat and the dog: the shared verb is the
    # shape of the question, not part of the answer.
    first = {o.split()[0] for o in options}
    if len(first) == 1 and all(len(o.split()) > 1 for o in options):
        rest = [" ".join(o.split()[1:]) for o in options]
        if all(r[:1].isalpha() for r in rest):
            options = rest
    # "get a cat or a dog": the determiner on the second one says the first verb is shared.
    if len(options[0].split()) > 1 and re.match(r"(?:a|an|the)\b", options[1]):
        options = [" ".join(o.split()[1:]) if len(o.split()) > 1 else o for o in options]
    return options


def _asked_for_help(memory, n=4):
    """True when the person has asked for suggestions in the last few turns.

    The ask is usually the line just before the bot's offer ("what should i cook tonight"), but
    it can be one turn further back ("what should i cook" / "i only have eggs and pasta in" /
    "you pick"). A choice handed back long after a statement ("i have a nut allergy" /
    "either is fine") is a comment, not a request to pick.
    """
    for turn in reversed(recent(memory, n)):
        line = " ".join(str(turn.get("user") or "").split())
        if line and _ASKED.match(line):
            return True
    return False


# The same hand-back said without a verb: "i dont mind", "dont mind really", "im easy", "im not
# bothered", "anything works". These only mean "you choose" when the answer in front of them has
# something to choose, so they are read only where two or more options are readable - a shrug on
# its own is a comment, and the rest of the bot should answer it.
_BARE_HAND_BACK = re.compile(
    r"^(?:(?:ok|okay|fine|right|well|so|then|and|hmm|ha)[, ]+)*"
    r"(?:"
    r"(?:i\s)?(?:don'?t|do not|dont) mind(?: (?:really|either|much|at all|tbh))?"
    r"|(?:i'?m|im) (?:easy|not bothered|not fussed)(?: (?:either|really|tbh))?"
    r"|(?:either|any|anything)(?: one| of (?:them|those|these))?"
    r"(?: ?(?:is|are)? ?(?:fine|good|ok|okay|works))?"
    r"|(?:any|either) of (?:them|those|these)"
    r"|whatever (?:you|u) (?:think|reckon|say|like)"
    r")"
    r"[.?!]*$", re.I)

# The bot already made the pick a turn ago ("I'd say tuna pasta in 15.", "My pick: eggs on toast.")
# and the person hands it back again. The answer is the same pick, said plainly: a second "you
# pick" is not a new question, and on main it got "Thanks for telling me - I'm here if you want to
# dig into any of that", which is the one reply a follow-up must never get.
_PICK_SAID = (
    re.compile(r"^(?:my pick:|if it were me:|i'?d say|i'?d go with|i would go with) *(.+?)[.!]*$", re.I),
    re.compile(r"^(.+?)\s+\u2014\s+that's the one i'?d choose[.!]*$", re.I),
)
# How the bot insists, and how a pick said twice reads its own phrasing back as the option
# ("Same as before: is still tuna pasta in 15."). One lead-in list is used for both reading and
# peeling, so a line cannot be said by one and unheard by the other.
_INSIST_LEAD = r"then it is|my pick is still|same pick:|i'?ll decide then:|go with"
_INSIST_SAID = re.compile(r"^(?:%s) *(.+?)[.!](?:\s|$)" % _INSIST_LEAD, re.I)
_INSIST_WRAP = re.compile(r"^(?:%s) *(.+?)[.!]*$" % _INSIST_LEAD, re.I)

# Nothing here opens with the composer's own repeat frames ("Same as before: ...", "Still ...",
# "Same answer, and it covers this: ..."): the composer adds one of those to a reply it has already
# given, and a pool line that starts the same way reads as a doubled frame.
# The option never opens one of these. A pick read back off the screen and put at the front of a
# sentence printed "tuna pasta in 15. I have not changed my mind", and capitalising it to fix that
# made a pick read back as "Tuna pasta in 15" and put mid-sentence ("Then it is Tuna pasta in 15").
INSISTED = (
    "Then it is {option}. You can blame me if it is wrong.",
    "My pick is still {option}.",
    "Same pick: {option}.",
    "I'll decide then: {option}.",
    "Go with {option}. Someone has to choose, so I have.",
    "Then it is {option}. There is nothing else to weigh up.",
)
# Nothing readable to choose from - the answer a turn ago was advice, or a question. A friend
# still decides: what they say is the rule to decide by, not "I don't know enough to answer that
# honestly" and not a search hedge. Every line here fits a dinner, a film and a week away.
BY_A_RULE = (
    "Then take the cheapest one that fits the time you have, and sort the details as you go.",
    "Go with the one you would be annoyed to lose. The rest is noise.",
    "Pick the first one you liked the sound of. That instinct is usually right.",
    "Then choose the one that leaves you the most time. The rest sorts itself out.",
)


def _peeled(option):
    option = option.strip(" *_\u2014,.;:")
    for _ in range(3):
        match = _INSIST_WRAP.match(option)
        if not match:
            break
        option = match.group(1).strip(" *_\u2014,.;:")
    return option


# An option that is a quantity, not a thing: "about 130 to 150 calories per 100g cooked" was read
# off a calorie answer and handed back as the pick for "you pick".
_A_MEASURE = re.compile(
    r"\b(?:\d+(?:\.\d+)?\s*(?:cal|calories|kcal|g|kg|mg|ml|l|gram|grams|kilo|kilos|litre|litres"
    r"|min|mins|minutes|hour|hours|degrees?|percent|%)|per\s+\d)", re.I)


def _readable(options):
    """The options a person could actually be choosing between.

    A list read off an answer that was not an offer is full of the answer's own figures, so
    anything carrying a quantity is dropped, and so is a mouthful that runs to a whole clause. A
    thing being chosen is a name ("eggs on toast", "Croatia before the crowds"), not a measurement.
    """
    keep = []
    for option in options:
        text = str(option).strip()
        if not text or len(text.split()) > 6 or _A_MEASURE.search(text):
            continue
        keep.append(option)
    return keep


def _already_picked(memory, back=3):
    """The one thing the bot said it would choose, if it said one a turn or two ago."""
    for turn in reversed(recent(memory, back)):
        said = " ".join(str(turn.get("bot") or "").split())
        if not said or said.endswith("?"):
            continue
        for pattern in (_INSIST_SAID,) + _PICK_SAID:
            match = pattern.match(said)
            if not match:
                continue
            option = _peeled(match.group(1))
            if option and len(option.split()) <= 8 and "?" not in option:
                return option
    return None


def reply_for(text, memory):
    """One option from what the bot just offered, or None when there was no choice to make."""
    asked = asks_for_a_pick(text)
    shrug = False if asked else bool(
        _BARE_HAND_BACK.match(" ".join(str(text or "").lower().split())))
    if not (asked or shrug):
        return None
    turns = memory.get("turns") or []
    picked = _already_picked(memory)
    options = _readable(options_in(last_bot(memory)))
    if len(options) < 2:
        options = _readable(_from_user_line(memory))
    if len(options) >= 2:
        short = [o for o in options if len(o.split()) <= 8]
        options = short or options
        chosen = random.Random(len(turns)).choice(options)
        line = random.Random(len(turns) + 7).randrange(len(PICKS))
        said = PICKS[line].format(option=chosen)
        return said[:1].upper() + said[1:]
    if picked:
        # "you decide" then "up to you": the pick is on the screen, so it is given again. The
        # option goes in at the front of one of the lines, so the reply is capitalised here rather
        # than printed as "tuna pasta in 15. I have not changed my mind".
        return pick(INSISTED, memory, seed_text=text).format(option=picked)
    if _asked_for_help(memory):
        # Handed a choice to make with nothing listed: the rule to decide by, not a search hedge.
        return pick(BY_A_RULE, memory, seed_text=text)
    return None


# The other half of a choice: the person has settled on one of the things, and then asks what they
# settled on. "im thinking of getting a cat" / "actually a dog" / "what did i decide to get" named
# nothing the store could answer, because a deciding ask carries no subject of its own - the
# subject is the thing in the line where they changed their mind.
DECIDING_ASK = re.compile(
    r"^(?:(?:ok|okay|fine|right|well|so|then|and|but|hmm|ah)[, ]+)*"
    r"(?:(?:what|which)(?:\s+(?:one|thing|of them))?\s+(?:did|do|have|had)\s+(?:i|we)\s+"
    r"(?:decide|decided|settle|settled|pick|picked|choose|chose|go for|go with|"
    r"end up with|end up getting|come down to|land on|get|got|buy|bought)"
    # the same ask in the present tense, which is the shape people use when they want the
    # answer rather than the story: "so what am i getting", "what are we having"
    r"|(?:so\s+)?what\s+(?:am|are)\s+(?:i|we)\s+(?:getting|having|going for|picking|"
    r"ending up with|settling on))"
    r"\b[^?.!]{0,24}[?.!]*$", re.I)

# The turn where they settled it: "actually a dog", "no, the dog", "i've decided on a dog",
# "let's go with the dog", "make it a dog". Only these, so an ordinary "no" ("no, its in the
# kitchen") brings no thing with it and the ask is left to the rest of the bot.
#
# The change word on its own is not a change of mind: "picked", "went for" and "landed on" are
# ordinary past tense too, and on their own they read a preposition or a fragment as the thing
# ("i picked up a bug" -> "up", "i went for a run" -> "a run"). So the two kinds are apart. The
# words that cannot mean anything but a decision ("actually", "make it", "i've decided") are read
# wherever they come, and the weak verbs are read only after a word that hands the choice over
# ("no", "ok", "so", "lets", "actually") - and then only with a definite thing after them, which
# is what "lets go with the grey" has and "i went for a run" has not.
STRONG_CHANGE = re.compile(
    r"\b(?:actually|instead|on second thoughts?|changed my mind|then again|make it|"
    r"i(?:'| a)?ve decided|i decided|we decided|we(?:'| a)?ve decided|decided on|"
    r"settled on|settling on|i(?:'| a)?ve settled|we(?:'| a)?ve settled)\b", re.I)

WEAK_CHANGE = re.compile(
    r"\b(?:go with|going with|go for|going for|went with|went for|end up with|ended up with|"
    r"land on|landed on|opt for|opted for|pick|picked|picks|choose|chose|chosen)\b", re.I)

CHANGED_IT = re.compile(STRONG_CHANGE.pattern + "|" + WEAK_CHANGE.pattern, re.I)

# The words a line can have before a weak change word and still be handing the choice over:
# "no, ok, so, lets, actually" and the like. A sentence about somebody else ("she picked up the
# kids") and one about the person's own day ("i went for a run") are not decisions.
CUE = frozenset("""no nope ok okay so then well and but lets let fine right actually instead
    hmm ah yes yeah""".split())

# A frame word between the change word and the thing is not the thing: "actually make it 60" is
# 60 and "actually lets go with the grey" is the grey.
SECOND_FRAME = re.compile(
    r"^\W*(?:(?:make (?:it|that)|go (?:with|for)|going (?:with|for)|decided on|settled on|"
    r"settling on|(?:i|we)(?:'ve|'a)?ve?\s+(?:decided|settled)(?:\s+(?:on|to))?|"
    r"lets|let us|to (?:get|go|buy|have)|just|then|so|ok|okay|instead|actually)\b[\s,]*)+",
    re.I)

# A thing cannot start with one of these: "i landed on my feet" names the feet and the landing,
# and "i picked up a bug" names a bug picked up, but neither names a choice, so "my feet" and
# "up" are not things they settled on.
NOT_AT_THE_START = frozenset("""up out off on down back in into onto over around through about
    at by from with without for to of after before since until away along across""".split())

# A definite thing after a weak change word: "lets go with the grey", not "i went for a run".
DEFINITE = frozenset("the this that these those my our your his her their".split())

# Words that end the thing without being part of it: "actually a dog for the kids" is a dog.
TRAIL = frozenset("""instead actually really probably maybe i think though anyway honestly then
    now please thanks for with to on in at about of and but so also too both""".split())

# A fact they are putting right, not a choice they made: "actually its the radiator", "actually im
# 35", "actually its shellfish". The copula is the tell - the line is saying what something is.
CORRECTION = re.compile(
    r"^\W*(?:its|it's|it is|theyre|they're|they are|theres|there's|thats|that's|"
    r"hes|he's|shes|she's|im|i'm|i am|we're|we are)\b", re.I)

# The words that put a choice on the table, which a bare "actually" then answers. Without one of
# them, an "actually ..." line is the person correcting the bot rather than settling anything, and
# "The radiator - that's the one you settled on." is a confident statement about nothing.
A_CHOICE = re.compile(
    r"\b(?:thinking (?:of|about)|consider(?:ing)?|deciding|decided between|chose between|"
    r"choosing between|torn between|looking at|can'?t decide|undecided|options?|"
    r"should i (?:get|go|buy|have|pick|choose)|which (?:one|would)|instead of|whether)\b",
    re.I)

# The change words that are also ordinary English, so the line only settles a choice when there is
# one on the table already ("im thinking of getting a cat" / "actually a dog"). The explicit ones
# ("make it", "i've decided", "settled on", "on second thoughts") say it themselves.
BARE_CHANGE = frozenset(("actually", "rather"))

# Words that come before the thing without being it, so "ive decided to get a dog" reads "dog"
# and "make it the small one" reads "small one" rather than "to get a" or "the".
DETERMINERS = frozenset("a an the my our your his her their this that".split())

# "no, a dog" is the same correction as "actually a dog", and it is only read at the start of the
# line: an ordinary "no" inside a sentence ("no, its in the kitchen") brings no thing with it.
NO_THEN_THING = re.compile(r"^\W*(?:no|nope)\b[\s,!]+", re.I)

# The same "no" after the change word: "actually no, a scooter" moves the choice to a scooter, and
# the "no" is the correction talking, not part of the thing. It is only taken off when something
# is left after it.
CORRECTION_OPENER = re.compile(r"^\W*(?:(?:actually|oh|sorry|ok|okay|well|right|wait)\s+[,.]?\s*)*"
                               r"(?:no|nope)\b[\s,.!-]+", re.I)
# What "no" keeps saying when it is not a correction: "no longer smoking", "no more", "no way".
# The opener is not taken off in front of one of these, so the line is read exactly as before.
NO_CONTINUES = frozenset("longer more way thanks thank such bother idea need chance matter doubt".split())

# A word that is the person's doing or feeling, not the thing they chose. "i actually like it"
# carries the change word but names no choice, so it settles nothing.
VERBISH = frozenset("""
like likes liked love loved hate hated want wanted need needed think thought know knew
said say says tell told do did does done be been being is are was were will would can
could should might have has had get got go went feel felt seems seem sound sounds work works
""".split())

NOT_THE_THING = frozenset("""
a an the my our your his her their this that these those it its it's them they he she hes shes
one ones you your yours i im ive we us there here
to get getting have having buy buying go going for with on about at in
of and or but so then now instead actually really probably maybe i think we
something anything nothing else more better different
""".split())

# What is said back: the thing, and that it was the one they landed on. Short, because the ask is
# short and the answer they want is one word with a nod.
SETTLED = (
    "{thing} \u2014 that's the one you settled on.",
    "You settled on {thing}.",
    "The one you landed on was {thing}.",
    "{thing}, as far as this chat goes.",
)


def _the_thing_in(line):
    """The thing named after the word that says they changed their mind, or ""."""
    weak = False
    said = STRONG_CHANGE.search(line)
    if said is None:
        said = WEAK_CHANGE.search(line)
        weak = said is not None
    if said is None:
        # "no, a dog": the correction said on its own, with nothing after it but the thing. A
        # "no" that opens an ordinary sentence ("no, its in the kitchen") names no choice.
        said = NO_THEN_THING.match(line)
        if not said or len(line[said.end():].split()) > 3:
            return ""
    elif weak and not _hands_the_choice_over(line[:said.start()]):
        return ""
    tail = line[said.end():]
    # "actually no, a scooter" says its own "no" after the change word, and the thing is what
    # follows it: without this the choice was kept as "No a scooter" and the deciding ask answered
    # "No a scooter - that's the one you settled on."
    for _ in range(2):
        opened = CORRECTION_OPENER.match(tail)
        rest = tail[opened.end():] if opened else ""
        if not rest.strip() or rest.split()[0].lower().strip(",.!?") in NO_CONTINUES:
            break
        tail = rest
    for _ in range(3):
        frame = SECOND_FRAME.match(tail)
        if not frame:
            break
        tail = tail[frame.end():]
    if CORRECTION.match(tail):
        # "actually its the radiator" says what something is, and no thing has been chosen.
        return ""
    words_after = [w.strip(",.!?;:'\"()") for w in tail.split()]
    kept = []
    lead = ""
    for word in words_after:
        if not word:
            continue
        if word.lower() in DETERMINERS and not kept:
            # "actually a dog" and "ive decided to get a dog" are both "a dog": the article is
            # part of the name of the thing, not part of the sentence around it.
            lead = word.lower()
            continue
        if word.lower() in NOT_THE_THING and not kept:
            # "the small one" keeps its "one": only the words before the thing are skipped.
            continue
        if kept and word.lower() in TRAIL:
            break
        kept.append(word)
        if len(kept) == 3:
            break
    if not kept and said.group(0).lower() == "instead":
        # The change word can come after the thing: "no a kitten instead" is a kitten, and the
        # rest of the line without the "instead" is where it is named.
        return _the_thing_in(line[:said.start()])
    if not kept or kept[0].lower() in VERBISH:
        return ""
    if kept[0].lower() in NOT_AT_THE_START:
        return ""
    if weak and lead not in DEFINITE:
        # "the grey" is a thing on offer and "a run" is what somebody did this morning.
        return ""
    return " ".join(([lead] if lead else []) + kept)


def _hands_the_choice_over(before):
    """True when the words before a weak change word are only the ones that hand a choice over."""
    words_ = [w for w in re.findall(r"[A-Za-z']+", before or "")]
    if not words_:
        return True
    return len(words_) <= 2 and all(word.lower() in CUE for word in words_)


def settled_on(memory):
    """The thing the person last settled on, in their own words, or "".

    Read from the last few things they said, newest first, and only from a line that carries a
    change of mind: the thing has to be named in the line that moved the choice.
    """
    for turn in reversed(recent(memory, 3)):
        line = " ".join(str(turn.get("user") or "").split())
        if not line:
            continue
        thing = _the_thing_in(line)
        if not thing:
            continue
        if _bare_change(line) and not _a_choice_in_hand(memory, line):
            # "im 34" / "actually 35": a bare change word alone does not say a choice was made.
            continue
        return thing
    return ""


def _bare_change(line):
    """The change word when every one the line carries is an ordinary English one, or "".

    "actually make it 60" carries both kinds, and the explicit one says the choice was made, so
    the line is read without asking for a choice already on the table."""
    text = str(line or "")
    for match in STRONG_CHANGE.finditer(text):
        if match.group(0).strip().lower() not in BARE_CHANGE:
            return ""
    first = STRONG_CHANGE.search(text)
    return first.group(0).strip().lower() if first else ""


def _a_choice_in_hand(memory, this):
    """True when an earlier line of the chat put a choice on the table."""
    for turn in reversed(recent(memory, 8)):
        line = " ".join(str(turn.get("user") or "").split())
        if not line or line == this:
            continue
        if A_CHOICE.search(line) or " or " in line.lower():
            return True
    return False


def the_decision(text, memory):
    """The thing they settled on, said back, on a deciding ask. None on every other line."""
    line = " ".join(str(text or "").split())
    if not DECIDING_ASK.match(line):
        return None
    thing = settled_on(memory)
    if not thing:
        return None
    said = _a_way_of_saying_it(thing, memory)
    return said[:1].upper() + said[1:]


def _a_way_of_saying_it(thing, memory):
    """One of the SETTLED lines, not the one used on the last deciding ask."""
    last = " ".join(str(last_bot(memory) or "").split()).lower()
    frames = [frame for frame in SETTLED if frame.format(thing=thing).lower() != last]
    frames = frames or list(SETTLED)
    return random.Random(len(memory.get("turns") or [])).choice(frames).format(thing=thing)


def offered(memory, n=1):
    """The options the bot offered over its last n replies, oldest first."""
    out = []
    for turn in recent(memory, n):
        out.extend(options_in(turn.get("bot") or ""))
    return out
