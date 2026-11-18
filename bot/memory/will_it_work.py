"""A line that asks whether the advice will work is answered with what the advice achieves.

"will that work" names nothing of its own. After a how-to it is not a new question and not small
talk: it is the one thing a person asks before they spend an hour on someone else's method. On
main it was answered with a stock nod to the method ("Done that way, it needs no one else: that is
the method I would use."), which says nothing about whether the method works:

    how do i clean a burnt pan
      Put an inch of water and two tablespoons of bicarbonate of soda in it and simmer for ten ...
    will that work
      Done that way, it needs no one else: that is the method I would use.

The card has already answered it, in its own words - "almost nothing needs scrubbing after that",
"the glass catches the rest in a day or two", "a post with height lets her do it properly" - so the
reply is that clause, with the yes the person asked for in front of it. Nothing is judged and
nothing is added: a card with no such clause passes, and the line is answered as it was.

Narrow on purpose:

* the line has to be *only* the check - "will that work", "does that help", "would that fix it" -
  with nothing of its own after it, because "will that work for a dark stain too" asks about a
  stain;
* the bot's last turn has to be a card it really said (`measure._the_card_said_last`, the same
  check the measure follow-up uses), so a chat line is never quoted back as an answer;
* the clause has to say the method *achieves* something, and a clause that says it achieves
  nothing ("rice does nothing except leave grit in the ports") is not that.
"""
import re

from . import measure

# The check itself: a modal, then a pronoun for the advice just given, then the verb. "will that
# work" / "would it help" / "does that fix it" / "will they do the job".
WORK_CHECK = re.compile(
    r"^(?:(?:and|but|so|ok(?:ay)?|right|oh|hmm|well|then)[, ]+)*"
    r"(?:will|would|does|do|might|should|can)\s+(?:that|it|this|they|those)\s+"
    r"(?:work|help|do\s+(?:it|the\s+job)|fix\s+(?:it|that)|be\s+(?:enough|ok|okay|all\s+right|"
    r"alright|fine)|make\s+a\s+difference)"
    r"(?:\s+(?:for|on)\s+(?:me|us|him|her|them|this|that))?"
    r"(?:\s+(?:then|though|now|too))?\s*$", re.I)

# What a method is said to achieve, in the words a card uses for it. "almost nothing needs
# scrubbing", "catches the rest", "lets her do it properly", "does the job", "comes away".
ACHIEVES = re.compile(
    r"\b(?:almost nothing|nothing needs|nothing to scrub|does the job|does the trick|"
    r"catches|clears|lifts|comes away|comes off|gets rid of|no more|beats|kills|sinks|"
    r"survives|stops?|fixes|sorts|dries|settles|holds|works|helps?|lets (?:her|him|them|you)|"
    r"keeps (?:them|it) (?:off|away|out))\b", re.I)

# A clause that says a method achieves nothing is not the clause that says it works: "rice does
# nothing except leave grit in the ports". Nor is a warning about what not to do.
NOT_ACHIEVING = re.compile(
    r"\b(?:does nothing|nothing except|does not|doesn't|dont|don't|never|won't|wont|"
    r"isn't|is not|not\s+enough|makes it worse)\b", re.I)

# A clause that opens on a joining word is the middle of the card's sentence, not a thing the bot
# can say on its own: "Yes \u2014 which beats most products" is not a sentence, so the clause after
# it is not the one handed back.
JOINS_ON = frozenset(("which", "that", "who", "and", "but", "so", "then", "because", "though",
                      "while", "as", "if", "when", "also"))

# The yes the person asked for. A rotation, not a stock line: the same chat asking twice gets a
# different one, and two chats do not open the same way.
YES_IN_FRONT = ("Yes", "It does", "That does it", "Yes, it does")

# A clause handed back has to stay short: the arbiter reads twelve or more words of the bot's last
# answer word for word as that answer said again (`arbiter._echoes`), and rightly - the person has
# those words on the screen. Eleven words of the card with the yes in front of it is a second thing
# said, not a repeat. A card whose every account of what it achieves runs longer than that is left
# to the modules that answered it before.
THE_MOST_QUOTED = 11
TRAILING_FILLER = ("too", "as well", "also", "then", "though")

# A clause ends where a card starts a new one. The same reading the measure follow-up uses.
A_NEW_CLAUSE = frozenset("""and so but or which is are was were then because when if that
it they there this these with plus while as""".split())
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def asks_if_it_will_work(line):
    """True when the line is nothing but a check that the advice works."""
    text = " ".join(str(line or "").split()).strip(" ?.!,")
    return bool(text) and bool(WORK_CHECK.match(text))


def _the_clauses(sentence):
    """The clauses of a sentence, in order: a card puts the method in one and its result in the
    next ("then lift the burnt layer with a wooden spoon: almost nothing needs scrubbing")."""
    parts = re.split(r"[,;:]\s+|\s+-\s+", str(sentence))
    return [part.strip(" .") for part in parts if part.strip(" .")]


def _without_filler(clause):
    """The clause without the words that only join it to the rest of the card ("... help too")."""
    said = clause.strip(" .")
    for filler in TRAILING_FILLER:
        if said.lower().endswith(" " + filler):
            said = said[: -len(filler) - 1].rstrip(" ,.")
    return said


def _what_it_achieves(card):
    """The clause of the card that says what the method achieves, or "" when it says nothing."""
    # The last sentence that accounts for the method comes first: a card opens on the thing to do
    # and closes on what it achieves, and the opening sentence is the method the person has just
    # read ("Train the lead as a stop-and-go game" is not a reason it will work, "a head halter
    # helps while he learns" is).
    for sentence in reversed([part.strip() for part in SENTENCE.split(str(card)) if part.strip()]):
        if not ACHIEVES.search(sentence) or NOT_ACHIEVING.search(sentence):
            continue
        for clause in _the_clauses(sentence):
            if not ACHIEVES.search(clause) or NOT_ACHIEVING.search(clause):
                continue
            if (re.split(r"\s+", clause) or [""])[0].lower().strip(",.;:") in JOINS_ON:
                continue
            clause = _without_filler(clause)
            # A clause that is only the verb ("it works") says nothing, and one that runs long is
            # the method again with the result on the end.
            if 4 <= len(clause.split()) <= THE_MOST_QUOTED:
                return clause
    return ""


def reply_for(text, memory):
    """The yes with the card's own account of why, or None."""
    if not asks_if_it_will_work(text):
        return None
    card = measure._the_card_said_last(memory)
    if not card:
        return None
    said = _what_it_achieves(card)
    if not said:
        return None
    # The card's verdict lines already have an owner: `thread.checking_the_verdict` says a "No:" or
    # "Yes:" back with the reason it gave, and that is a better answer than this one.
    if str(said).lstrip().lower().startswith(("yes", "no")):
        return None
    if said[:1].isupper() and (said[1:2].islower() or (said[1:2] == " " and said[2:3].islower())):
        said = said[0].lower() + said[1:]
    said = said.rstrip(" .")
    at = sum(ord(letter) for letter in str(text or "")) % len(YES_IN_FRONT)
    return "%s \u2014 %s." % (YES_IN_FRONT[at], said)
