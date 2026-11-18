"""The same thing in another size, asked straight after the answer.

"how long do i roast a chicken" is answered with a rule that already carries the size in it ("20
minutes per 500g plus 20 minutes"), and "what about a bigger one" is the person asking that rule
for their own bird. The follow-up names no food and no number, so every reader refused it and the
person was told the bot did not know enough to answer honestly, with a search suggested - one
turn after an answer that had the whole of it.

Two things follow the answer, and both are said with what the answer already said:

* a rate ("per 500g", "for every pound") is the answer for any size, so the rule is said again
  and the sum is left to the person;
* times that were given for one unnamed size ("6 minutes for a runny yolk", "about an hour for a
  medium potato") are times for that size, so a bigger one wants a few minutes more and a smaller
  one a few minutes less, with the method unchanged.

Only a follow-up that says "bigger", "larger", "smaller" and so on about "one" reaches this, and
only when the answer on the screen gave a time. Anything else is left to the modules below.
"""
import re

# "longer" and "shorter" are left out on purpose: they are durations far more often than sizes, so
# "what about a longer one" after "how long should i rest my ankle" was read as a bigger ankle
# (cream-engine, #7649). A size this reader answers is a physical one.
_ANOTHER_SIZE = re.compile(r"\b(?:big|bigger|large|larger|small|smaller|little|littler|thicker|"
                           r"thinner|wider|narrower)\b", re.I)
# It has to be about the thing already answered, not a new one: "what about a bigger one" and
# "and a larger version" point back, "what about a bigger dog" names a new thing.
# The pointer has to be a size, not any "it" in the line. "shorter if i cut it up" after "how
# long do i bake a potato" is a different method, not a smaller potato, and the loose \bit\b read
# it as one and said "a smaller one wants a few minutes less" (fond-curtain, #7649). So a size
# word counts when a thing-word comes right after it ("a bigger one", "a larger version") or when
# it is the whole ask ("what about bigger", "and smaller?").
_SIZE_WORD = r"(?:bigger|larger|smaller|littler|thicker|thinner|wider|narrower)"
_POINTS_BACK = re.compile(
    _SIZE_WORD + r"\s+(?:one|ones|version|size|sized|that|it|them|those|batch|tin|pot|dish|"
    r"piece|bird|cut|joint|loaf|pan|mug|cup|glass|portion|helping)\b"
    r"|\b(?:what about|and|how about|what if|or|then)\s+(?:a|an|the)?\s*"
    r"(?:bit\s+|little\s+|much\s+|whole\s+)?(?:a|an|the)?\s*" + _SIZE_WORD + r"\s*[?.!]*$",
    re.I)
_A_TIME = re.compile(r"\b\d+\s*(?:-|to)?\s*\d*\s*(?:minutes?|mins?|hours?|hrs?)\b|\b\d+\s*(?:per|a)\b|"
                     r"\b(?:an?|one|two|three|four|five|ten|twenty|thirty|forty|half an)\s+"
                     r"(?:minutes?|mins?|hours?|hrs?)\b", re.I)
# The rule sentence ends where the answer stops being the rule: "..., so a 2kg bird takes 1 hour
# 40 minutes" is the sum done for their bird, and it is not part of the rule.
_RULE_STOPS = re.compile(r",\s*(?:so|which) |; |\s-\s|\s\u2014\s")
# A rate is the answer for every size: "20 minutes per 500g", "for every pound", "per kg".
_A_RATE = re.compile(r"\bper\s+(?:\d+\s*)?(?:g|kg|gram|grams|kilo|kilos|pound|pounds|lb|lbs|"
                     r"centimetre|centimetres|cm|inch|inches|litre|litres|person)\b|"
                     r"\bfor every\b|\beach\s+\d+", re.I)
_SENTENCE = re.compile(r"[^.!?]+[.!?]?")
BIGGER = ("Same rule, just a bigger sum: {rule}", "The rule works at any size: {rule}",
          "Same as before, and the sum does the work: {rule}")
SMALLER = ("Same rule, just a smaller sum: {rule}", "The rule works at any size: {rule}",
           "Same as before, and the sum does the work: {rule}")
# The rule itself has just been said, and saying it a second time word for word is the bot
# repeating itself (loyal-wheel, #7649: "what about a bigger one" then "and a bigger one again").
# What is left to say is that the rule covers the bigger one too, without the rule again.
SAID_BIGGER = ("That rule is the whole of it - the size goes into it and the time comes out.",
               "Same rule, still: nothing changes with a bigger one except the figure you put "
               "into it.",
               "It does not change with the size - put your figure into that rule and it holds.")
SAID_SMALLER = ("That rule is the whole of it - the size goes into it and the time comes out.",
                "Same rule, still: nothing changes with a smaller one except the figure you put "
                "into it.",
                "It does not change with the size - put your figure into that rule and it holds.")
MORE = ("A bigger one wants a few minutes more than that - same method, just check it later.",
        "Give a bigger one longer than those times: a few minutes more, and check it.",
        "Those times are for a normal one, so a bigger one takes a few minutes longer.")
LESS = ("A smaller one wants a few minutes less than that - same method, just check it earlier.",
        "Give a smaller one less time than that: a few minutes fewer, then check it.",
        "Those times are for a normal one, so a smaller one takes a few minutes less.")


def _flat(text):
    return " ".join(str(text or "").rstrip(".").split()).lower()


# This module's own short lines carry no time in them, so a second size ask straight after one
# (the egg row: "what about a bigger one" then "and a smaller one") read the chat as having no
# time in it and answered "A smaller one - noted." (fond-curtain and loyal-wheel, #7649). So the
# walk back steps past these two families to the answer they were said about.
_OUR_SHORT_LINES = frozenset(_flat(shape)
                             for shape in MORE + LESS + SAID_BIGGER + SAID_SMALLER)
# The two families that give the answer's own rule back. A size ask after one of these is the
# rule asked again for the same thing - "and a bigger one again" - and the answer would nest
# inside itself ("The rule works at any size: same rule, just a bigger sum: ..."), so this reader
# leaves it alone.
_OUR_RULE_LEADS = ("same rule, just a bigger sum:", "same rule, just a smaller sum:",
                   "the rule works at any size:", "same as before, and the sum does the work:")


def _one_of_ours(answer):
    """True when the line is one of this module's own shapes."""
    flat = _flat(answer)
    if flat in _OUR_SHORT_LINES:
        return True
    return any(flat.startswith(lead) for lead in _OUR_RULE_LEADS)


# The pointer "one" is a thing that has sizes, and the thing is named in the line before the answer
# rather than in the answer: "how long do i roast a chicken" names a bird, "how long should i rest my
# ankle" names an ankle, and nobody buys a bigger ankle. So a size ask is read only when the answer
# above is a rule by weight, or when the line that was answered names something sold or cooked by
# size (fond-curtain, #7649: "rest my ankle", "i sleep about 6 hours a night" and "my kids are 4 and
# 7" were all answered with the cooking times).
_BY_WEIGHT = re.compile(r"\bper\s+(?:\d+\s*)?(?:g|kg|gram|grams|kilo|kilos|pound|pounds|lb|lbs)\b",
                        re.I)
# What is cooked or sold by size. The answer is read for a food word only: a joint is a cut of meat
# and also a joint in an ankle, so "a sprained ankle ... the joint looks out of shape" was read as
# something to buy a bigger one of. The line the person wrote is read more loosely, because a word
# anybody might use in another sense ("a bigger joint", "a bigger pot") is unambiguous there.
_FOOD = (r"chickens?|birds?|turkeys?|duck|lamb|beef|pork|ham|roasts?|steaks?|chops?|fillets?|fish|"
         r"salmon|cod|trout|eggs?|potatoes|potato|onions?|carrots?|tomatoes|tomato|peppers?|"
         r"courgettes?|aubergines?|cabbage|squash|melon|sausages?|cakes?|loaf|loaves|bread|pizza|"
         r"pastry|pies?|tarts?|sponge|scones?|buns?|pancakes?")
_SIZED_THING = re.compile(r"\b(?:" + _FOOD + r")\b", re.I)
_SIZED_ASKED = re.compile(
    r"\b(?:" + _FOOD + r"|joints?|breasts?|thighs?|legs?|cuts?|tins?|pots?|pans?|dishes|trays?|"
    r"batches?|portions?|helpings?|mugs?|cups?|glasses)\b", re.I)


def _the_thing_asked(memory, text):
    """The line that the answer above answered, word for word, or "".

    The walk goes back the way `_the_answer` does: the current line and this module's own size asks
    are both skipped, so the egg row's second size ask still finds "how long do i boil an egg".
    """
    here = _flat(text)
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed(list(turns or [])):
        if not isinstance(turn, dict):
            continue
        asked = " ".join(str(turn.get("user") or "").split())
        if not asked or _flat(asked) == here:
            continue
        if _one_of_ours(str(turn.get("bot") or "")):
            continue
        return asked
    return ""


def _the_last_line(memory):
    """The bot's last line, word for word, or ""."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed(list(turns or [])):
        if isinstance(turn, dict) and turn.get("bot"):
            return str(turn.get("bot") or "").strip()
    return ""


def _the_answer(memory):
    """The last answer with a time in it, walking back past this module's own lines.

    A line of anybody else's with no time in it is not the answer, so the walk stops there and the
    ask is left to the modules below.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed(list(turns or [])):
        if not isinstance(turn, dict) or not turn.get("bot"):
            continue
        answer = str(turn.get("bot") or "").strip()
        if _one_of_ours(answer):
            continue
        if _A_TIME.search(answer):
            return answer
        return ""
    return ""


def _the_rule(answer):
    """The sentence of the answer that is the rule for any size, or ""."""
    for sentence in _SENTENCE.finditer(answer or ""):
        said = sentence.group(0).strip()
        if not (_A_RATE.search(said) and _A_TIME.search(said)):
            continue
        # A rule can be introduced by a colon, and what comes before it is talk about the answer
        # rather than the rule: an answer quoted back by another reader reads "Nothing separate for
        # a bigger - it is the same advice: About 20 minutes per 500g ..., so a 2kg bird takes 1
        # hour 40 minutes." Cutting at the first stop kept the hedge and said "Same rule, just a
        # bigger sum: nothing separate for a bigger." (fond-curtain, #7649). So the part after the
        # last colon is tried first, and taken only while it is still a rule.
        after = said.rsplit(": ", 1)[1].strip() if ": " in said else ""
        for piece in (after, said):
            if not (_A_RATE.search(piece) and _A_TIME.search(piece)):
                continue
            stop = _RULE_STOPS.search(piece)
            if stop:
                piece = piece[:stop.start()].strip()
            if piece:
                return piece
    return ""


def answer_for(text, memory=None):
    """The same thing in another size, when that is what the line asks; otherwise None."""
    if not isinstance(memory, dict):
        return None
    said = " ".join(str(text or "").strip().split())
    if not said or len(said.split()) > 8:
        return None
    if not (_ANOTHER_SIZE.search(said) and _POINTS_BACK.search(said)):
        return None
    answer = _the_answer(memory)
    if not answer:
        return None
    if not (_BY_WEIGHT.search(answer) or _SIZED_THING.search(answer)
            or _SIZED_ASKED.search(_the_thing_asked(memory, said))):
        return None  # nothing in this chat comes in sizes, so "one" means something else
    bigger = not re.search(r"\b(?:small|smaller|little|littler|thinner|narrower)\b", said, re.I)
    which = int(memory.get("size_said") or 0)
    memory["size_said"] = which + 1
    rule = _the_rule(answer)
    if rule:
        if _one_of_ours(_the_last_line(memory)):
            # The rule was said in the last line, so this one says what is left: that it holds for
            # the size they asked about. Repeating it would be the bot quoting itself.
            answer_shapes = SAID_BIGGER if bigger else SAID_SMALLER
            return answer_shapes[which % len(answer_shapes)]
        shapes = BIGGER if bigger else SMALLER
        said = rule.rstrip(".")
        first = said.split()[0] if said.split() else ""
        if first and not (first.isupper() or first[:1].isdigit()):
            # The rule sits after a colon, so its first letter is an ordinary one again: "Same rule,
            # just a bigger sum: about 20 minutes per 500g". A unit or a figure keeps its case.
            said = said[:1].lower() + said[1:]
        reply = shapes[which % len(shapes)].format(rule=said)
        # The answer's own words keep their capitals ("190C"), so only the reply's first letter is
        # touched, and the sentence is given its full stop back.
        return reply[:1].upper() + reply[1:] + "."
    shapes = MORE if bigger else LESS
    return shapes[which % len(shapes)]
