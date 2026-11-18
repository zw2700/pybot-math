"""What to wear, said about the occasion already on the table.

People do not repeat the occasion. Once they have said the thing is happening, the next question
about it is only the part they have not worked out:

    my sister is getting married in june
    im not sure what to wear
    and what about shoes

On its own, "im not sure what to wear" is a blank - the bot answered "Thanks for telling me - I'm
here if you want to dig into any of that.", which is the reply for a feeling, not for a person
choosing an outfit - and "and what about shoes" was a search hedge. Written out with the occasion
in the words an entry is keyed on ("what should i wear to my sister's wedding", "what shoes should
i wear to a wedding") the same two lines reach the outfit answer: not white or cream to a wedding,
a colour they feel good in, shoes they can stand in.

What is in here:

- `the_occasion(memory)` finds the occasion the chat is on - a wedding, an interview, a party, a
  funeral - and says it as a thing: "a wedding", or "my sister's wedding" when the chat named
  who it is. The entries answer "to my sister's wedding" and "to a wedding" alike, so the named
  one is only used when the relation is the person's own.
- `written_out(text, memory)` returns the question to answer, or None. It only fires when the
  line is about what to wear and names no occasion of its own, so "what should i wear to a
  wedding" is left alone, and a chat with nothing on the calendar keeps "Tell me what the day is
  - work, a meal out, a long walk - and I will say what to put on."
"""
import re

# The occasions people dress for, as the thing an entry is keyed on. A wedding said as "getting
# married" is still a wedding: that is how the person announces it, not what they call it.
OCCASIONS = (
    (re.compile(r"\b(?:weddings?|getting married|getting wed|married|marrying|bride|groom|"
                r"bridesmaid|best man|hen do|stag do)\b"), "wedding", "a wedding"),
    (re.compile(r"\b(?:interviews?|interviewing)\b"), "interview", "an interview"),
    # A first day is not an interview: the answer to "what should i wear to my new job" is the
    # paperwork and one notch smarter, not "ask whoever invited you" - there is nobody to ask on
    # the morning, and the job is already theirs.
    (re.compile(r"\b(?:first day|new job|new role|job starts?|starting (?:work|the job)|"
                r"start(?:ing)? (?:on )?monday)\b"), "work", "my new job"),
    (re.compile(r"\b(?:part(?:y|ies)|birthdays?|anniversar(?:y|ies)|housewarmings?|retirement|"
                r"celebrations?|get together)\b"), "party", "a party"),
    (re.compile(r"\b(?:funerals?|burial|cremation|wake|memorial)\b"), "funeral", "a funeral"),
    # A death puts a funeral on the chat without the word for the ceremony: "my uncle died" and
    # then "im not sure what to wear" is a person choosing clothes for a funeral, and both sides
    # left it with a feeling read back. Both halves are needed in one line - a person and a loss -
    # because "my phone died" and "the battery died" are not occasions, and the relation is what
    # makes the answer theirs ("my uncle's funeral" rather than "a funeral").
    (re.compile(r"(?=[\s\S]*\b(?:mum|mom|mother|dad|father|son|daughter|sister|brother|uncle|"
                r"aunt|nan|gran|granny|grandma|grandad|grandpa|cousin|niece|nephew|friend|mate|"
                r"colleague|boss|wife|husband|partner|girlfriend|boyfriend|neighbour)\b)"
                r"(?=[\s\S]*\b(?:died|dying|passed away|passed on|bereave\w*|death|buried)\b)"),
     "funeral", "a funeral"),
    (re.compile(r"\b(?:christenings?|baptisms?|naming ceremony)\b"), "christening",
     "a christening"),
    (re.compile(r"\b(?:graduations?|graduating|prom|leavers? do)\b"), "graduation",
     "a graduation"),
    (re.compile(r"\b(?:festivals?|gigs?|concerts?|gig\b)\b"), "gig", "a gig"),
    (re.compile(r"\b(?:barbecues?|bbqs?|cookout)\b"), "barbecue", "a barbecue"),
    # "a meal out" is a thing to dress for; "date" alone is not - a passport date and a delivery
    # date are dates - so it only counts as going on one.
    (re.compile(r"\b(?:dinners? out|meal out|meal at|restaurant|night out|first date|"
                r"on a date|going on a date|date night)\b"), "meal out", "a meal out"),
    (re.compile(r"\bchurch\b"), "church", "church"),
)

# A relation of their own, which is whose occasion it is: "my sister is getting married" is her
# wedding, and the entries answer "to my sister's wedding".
RELATION = re.compile(
    r"\bmy\s+(sister|brother|mum|mom|mother|dad|father|son|daughter|niece|nephew|cousin|aunt|"
    r"uncle|friend|best friend|mate|colleague|boss|partner|wife|husband|girlfriend|boyfriend|"
    r"in laws?|mother in law|father in law|grandma|grandad|nan|gran|granny)\b")

# What to wear, with no thing of its own: "im not sure what to wear", "dont know what to put on",
# "what do i wear", "and what about shoes", "should i wear a dress".
WHAT_TO_WEAR = re.compile(
    r"\b(?:what|wat)\s+(?:to|should\s+i|do\s+i|can\s+i|shall\s+i)\s+"
    r"(?:wear|put\s+on|dress)\b|"
    r"\b(?:not?\s+sure|no\s+idea|dont\s+know|do\s*n'?t\s+know|havent\s+decided|"
    r"cant\s+decide|cannot\s+decide|stuck)\s+(?:about\s+)?what\s+"
    r"(?:to\s+|i\s+(?:should\s+)?)?(?:wear|put\s+on|wearing)\b"
)

# A part of the outfit asked about on its own, the turn after the occasion: "and what about
# shoes", "what about a hat", "should i wear a dress". The part is what the entry's sentence is
# about (a wedding entry that says flat shoes are a kindness), so it is asked as an outfit
# question rather than left as a thing with no verb.
PART = re.compile(
    r"\b(?:shoes?|heels?|trainers?|boots?|sandals?|flats?|dress|dresses|suit|suits|shirt|blouse|"
    r"top|jacket|coat|blazer|hat|fascinator|tie|bag|outfit|skirt|trousers|chinos|jumpsuit)\b")

# The frames that make a part of an outfit the subject of the line: "what about shoes", "and
# shoes?", "should i wear heels", "will flats be ok".
PART_ASK = re.compile(
    r"\b(?:what|how)\s+about\b|\band\b|\bor\b|\bshould\s+i\s+(?:wear|go\s+for)\b|"
    r"\bwould\s+(?:flats|heels|boots|trainers|sandals)\b|\bis\s+it\s+ok\s+to\s+wear\b|"
    r"\bcan\s+i\s+(?:wear|get\s+away\s+with)\b|\bdo\s+i\s+need\b"
)

# "What should I put on" is clothes; "what should I put on the cake" is not. The party on the chat
# made the icing question the outfit question - "what should i wear to my son's party" - and told a
# person decorating a cake to ask the host about the dress code.
PUT_ON_A_THING = re.compile(
    r"\bput\s+on\s+(?:the|a|an|some|any|my|your|his|her|their|our|it)\s+([a-z']+)")

# A month or a season is part of the answer (a June wedding is a summer one), and the entries ask
# for it, so a line that says one keeps it.
MONTHS = ("january february march april may june july august september october november december "
          "spring summer autumn winter christmas easter").split()

# How far back the chat is looked at for the occasion. It is said once and then talked about, so
# it stays on the table for several turns; past that the chat has moved on.
RECENT = 5

WORD = re.compile(r"[a-z']+")


def _recent(memory):
    """The last few things the person said, newest first, as one lower-case string."""
    if not isinstance(memory, dict):
        return []
    said = []
    # Newest first, as the docstring says: a correction two lines later is the occasion the chat
    # is on. Read oldest first, `I'm going to a wedding in July` then `Actually it's a funeral`
    # kept the wedding and answered the clothes question with the wedding entry.
    for turn in reversed((memory.get("turns") or [])[-RECENT:]):
        if isinstance(turn, dict):
            text = " ".join(str(turn.get("user") or "").lower().split())
            if text:
                said.append(text)
    return said


def _an(phrase):
    """The article a word takes: "an interview", "a wedding"."""
    return ("an " if phrase[:1] in "aeiou" else "a ") + phrase


# An occasion said as over and done with is not the one the day ahead is about: "we had a party
# last night" / "what should i wear tomorrow" was answered with the party outfit card, where the
# chat before this module asked where the person was off to. A death is left alone however it is
# said, because a funeral is still to come after it ("my uncle died last week").
PAST_OCCASION = re.compile(r"\b(?:had|went\s+to|been\s+to|was\s+at|were\s+at)\b")

# A death is the exception to the line above: "my uncle died last week" is over, and the funeral
# it puts on the chat is still to come.
_A_DEATH = re.compile(r"\b(?:died|dying|dead|passed\s+away|passed\s+on|death|bereave\w*|"
                      r"funerals?|buried|burial|cremation|memorial|wake)\b")


def the_occasion(memory):
    """The occasion the chat is on, as "a wedding" or "my sister's wedding", or None."""
    said = _recent(memory)
    for text in said:
        for pattern, _key, phrase in OCCASIONS:
            if not pattern.search(text):
                continue
            if PAST_OCCASION.search(text) and not _A_DEATH.search(text):
                continue
            who = RELATION.search(text)
            if who:
                # Only when it is the person's own relation in the same line: "my sister is
                # getting married" is her wedding, and "a wedding" is what everybody else gets.
                return "my %s's %s" % (who.group(1),
                             phrase.split()[-1])
            return phrase
    return None


def _the_last_answer(memory):
    """What the bot said last, lower-case: the answer a part of the outfit is asked about."""
    if not isinstance(memory, dict):
        return ""
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    if not turns:
        return ""
    return " ".join(str(turns[-1].get("bot") or "").lower().split())


CLOTHING_WORDS = re.compile(r"\b(?:wear|wearing|wore|clothes|outfit|dress|suit|shoes|boots|"
                           r"trainers|jacket|coat|tie|shirt|colours|colors|smart|comfortable|"
                           r"black|white|cream|navy|grey|dark)\b", re.I)


def _the_answer_already_gave_it(memory):
    """True when the bot's last reply was already the outfit answer for this occasion.

    The second turn earns the card ("im not sure what to wear" -> the wedding answer, where main
    read a feeling back). A third turn that asks about a colour or a part of the same outfit was
    then answered with the card again in other words - "and what about shoes" got the colour
    warning, and "will black be alright" got "that is everything i have on that one" - which is
    the bot repeating itself. The pre-pass has done its job at that point, so the follow-up is
    left to the path it took before this module existed.
    """
    last = _the_last_answer(memory)
    if not last:
        return False
    return len(set(word.lower() for word in CLOTHING_WORDS.findall(last))) >= 2


# A yes/no ask about one thing being all right: "will black be alright", "is a tie ok". The
# answer is already on the screen - the card that said black or dark colours - so the sentence of
# it that names the thing is the answer, not the paragraph again and not "that is everything I
# have on that one".
PERMISSION_ASK = re.compile(
    r"\b(?:alright|all right|ok|okay|fine|allowed|acceptable|a problem|too much)\b", re.I)

# A sentence that warns against the thing rather than allowing it: it answers the ask as it is.
NOT_THIS = re.compile(r"\b(?:not|never|avoid|don'?t|doesn'?t|no|unless)\b", re.I)

# A colour, said on its own: the other half of what a follow-up about an outfit names.
A_COLOUR = re.compile(
    r"\b(?:black|white|cream|navy|grey|gray|blue|red|green|pink|beige|brown|charcoal|burgundy|"
    r"silver|gold|floral|patterned|light|dark)\b")


def the_sentence_answered(text, memory):
    """The sentence of the bot's last answer that answers a follow-up about one thing, or None.

    The card for the occasion is already on the screen, and the person asks about one thing in it:
    "will black be alright" after an answer that said black or dark colours are the thing. Both
    sides left that with a shrug ("that is everything I have on that one, so I would only repeat
    myself") while the sentence holding the answer was one line up. The sentence that names the
    thing is the answer, so it is handed over as it was said, and a card whose sentence says not
    to wear the thing still says not to: "will white be alright" gets the sentence that warns
    against it.
    """
    if not isinstance(text, str):
        return None
    line = " ".join(text.lower().split()).strip(" .!,")
    if not line or len(line.split()) > 12:
        return None
    if not the_occasion(memory):
        return None
    if not (PART.search(line) or A_COLOUR.search(line)):
        return None
    if not (PART_ASK.search(line) or PERMISSION_ASK.search(line)):
        return None
    last = _the_last_answer(memory)
    if not last or len(last.split()) < 6:
        return None   # a punt or a one-word line is not a card with an answer in it
    sentences = [one for one in re.split(r"(?<=[.!?])\s+", last) if one.strip()]
    if len(sentences) < 2:
        # One sentence is the whole answer, so handing it back is the bot saying the same thing
        # again in the same words ("what about the shoes" after a one-sentence first-day answer).
        # The card has to be longer than the part asked about for the part to be an answer.
        return None
    # The colour is asked about more closely than the thing: "is a white dress ok" wants the
    # sentence on white, and the card's sentence on the dress is about the invitation's code.
    words = sorted(set(A_COLOUR.findall(line))) + sorted(set(PART.findall(line)))
    for word in words:
        if not re.search(r"\b" + re.escape(word) + r"\b", last):
            continue
        for sentence in sentences:
            if re.search(r"\b" + re.escape(word) + r"\b", sentence):
                sentence = sentence.strip()
                if not sentence:
                    continue
                if sentence[0].isalpha():
                    sentence = sentence[0].upper() + sentence[1:]
                # A sentence that warns against the thing answers "will white be alright" on its
                # own; one that says the thing is fine is said as the yes it is.
                # Both are said with a word in front of them, so the reply is new text rather
                # than the paragraph again: the store has a "same answer again" path for a
                # repeat, and it would take the sentence and shrug at it.
                if NOT_THIS.search(sentence):
                    lead = "Careful - "
                elif NOT_THIS.search(line):
                    lead = "Then "
                else:
                    lead = "Yes - "
                return lead + sentence[0].lower() + sentence[1:]
    return None


def _names_an_occasion(text):
    return any(pattern.search(text) for pattern, _key, _phrase in OCCASIONS)


# The places and jobs a person dresses for that are not the occasion the chat is on. The occasion
# does not change what you wear to work tomorrow or for a run, and the ask that goes somewhere of
# its own is asking about that: after "my sisters wedding is in june", "what should i wear for a
# run tomorrow" is answered with the running gear, and writing the wedding into it answered the
# dress code instead (found by @green-lock on #6866). The occasion words are left out of this pool
# because a line that names one is asking its own question already (`_names_an_occasion`).
GOING_SOMEWHERE = re.compile(
    r"\b(?:to|for|at)\s+(?:a\s+|an\s+|the\s+|my\s+|our\s+)?"
    r"(?:work|school|college|uni|university|office|gym|run|jog|walk|ride|cycle|swim|shops?|"
    r"supermarket|church|bed|pub|bar|interview|meeting|shift|flight|train|beach|hike|climb|"
    r"dance|class|lesson|lessons|tennis|football|golf|rugby|netball|yoga|gig|concert|"
    r"restaurant|dinner|lunch|brunch|date|funeral|wedding|christening|baptism)\b")


def _names_its_own_outing(text):
    """Whether the ask goes somewhere of its own, so the chat's occasion is not what it is about."""
    found = GOING_SOMEWHERE.search(text)
    if not found:
        return False
    return not _names_an_occasion(text)


def written_out(text, memory):
    """The outfit question the line is asking, or None when the line is not one.

    "im not sure what to wear" after a wedding is "what should i wear to a wedding" and "and
    what about shoes" is "what shoes should i wear to a wedding".
    """
    if not isinstance(text, str):
        return None
    line = " ".join(text.lower().split()).strip(" .!,")
    if not line or len(line.split()) > 12:
        return None
    # The shape is tested first: `the_occasion` walks the last five lines with every occasion
    # pattern, and this module is asked about every line the knowledge base answers.
    worn = PUT_ON_A_THING.search(line)
    if worn and not CLOTHING_WORDS.search(worn.group(1)):
        return None
    shaped = WHAT_TO_WEAR.search(line) or (PART.search(line) and PART_ASK.search(line))
    if not shaped:
        return None
    occasion = the_occasion(memory)
    if not occasion:
        return None
    if _the_answer_already_gave_it(memory):
        return None
    # A line that says the occasion itself is asking its own question, and the entries answer it
    # already: "what should i wear to a wedding" is not improved by being written out.
    if _names_an_occasion(line):
        return None
    # A line that is going somewhere of its own is asking about that outing, not about the
    # occasion the chat is on: this module does not write the occasion into it.
    if _names_its_own_outing(line):
        return None
    if WHAT_TO_WEAR.search(line):
        return "what should i wear to %s" % occasion
    part = PART.search(line)
    if part and PART_ASK.search(line):
        # A part of the outfit that the answer already named is the part they are asking about
        # ("and what about shoes" after an answer that said flat shoes are a kindness). A part
        # it never mentioned - "should i wear a suit" to a job whose answer was about paperwork
        # - is a question the entry does not answer, and writing it out only gets the same
        # paragraph back ("Same as before: ..."), which tells them nothing.
        if part.group(0) not in _the_last_answer(memory):
            return None
        return "what %s should i wear to %s" % (part.group(0), occasion)
    return None
