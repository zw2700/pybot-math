"""They ask for another option, and the answer they were given had more than one thing in it.

"my tomato plants have blight" / "what else can i do about it" is not a new question: it is
about the answer just given, and it means "something other than that, please". Main answers it
with the same opening line again ("From just now: Give them sun...") or with a search hedge, and
both say the bot has nothing else - when the answer at the top of the screen usually has a second
half in it that was read past.

So this module reads that turn: a line that asks for another option and names nothing of its own,
the answer the bot gave a turn ago, and the part of that answer the person has not been handed
back yet. It replies with that part, said as what it is, rather than the whole paragraph again.

The rules, narrow on purpose:
* the line has to name nothing ("what else can i cook with mince" is a question of its own and
  never comes here);
* the answer it leans on has to be a real answer - a hedge, a stock line, a question or an
  emergency reply has nothing to hand over;
* only the sentences after the one the bot leads with are offered, because the opening line is
  what the person has already been given twice when a repeat is under way;
* a sentence the bot has said in the last few turns is not offered again, so a second "anything
  else?" moves on to the next one and then the module passes the turn back.

The subject is never invented: every word of the reply comes from the answer the person already
has.
"""
import re

from ..compose import pick
from ..compose.whole import a_whole_cut
from ..memory import topics
from . import named, repeat

# What a line can be made of and still be asking for another option rather than naming one. The
# ask words of a bare follow-up ("what", "should", "i", "any") come from repeat.py; these are the
# words that make it an ask for a second option.
OPTION_WORDS = frozenset("""
    else other others another alternative alternatives different ideas idea options option
    suggestion suggestions way ways thing things approach approaches trick tricks tip tips
    works work working help helps helping useful
""".split())

# The words of a request to carry on, which name no thing and so do not make a line its own subject.
CONTINUATION_WORDS = frozenset("""
    go goes going on carry carries keep keeps continue continuing next more further then again
    deeper say telling
""".split())

# A word for a stand-in names no thing of its own. "any swaps" after the advice on cutting down
# sugar asks for the rest of that answer, and read as a named thing it went to the baking
# substitutions: "In baking, caster and granulated are the same thing" for a question about
# sugar in the diet. A swap that does name ingredients ("can i swap butter for oil") still
# names them, so the line stays its own subject.
SWAP_WORDS = frozenset("""
    swap swaps swapping swapped substitute substitutes substitution substituting
    replacement replacements replace replacing stand-in
""".split())

ASK = repeat.ASK | repeat.FILLER | OPTION_WORDS | CONTINUATION_WORDS | SWAP_WORDS

# The words that ask for one part of an answer rather than for a thing: "anything i should include",
# "anything i should know", "what am i forgetting". Said after an answer, they are the same request
# as "what else" - the answer is on the screen and they want the part of it that matters - and
# none of them names a thing to be about. Read as a named thing instead, the line was answered
# "I'm listening - say more if it helps" after a wedding-speech answer (deck qdl-010).
THE_MISSING_PART = frozenset("""
    include includes including included bring bringing add adding say saying mention mentioning
    cover covers covering know wear take expect prepare check forget forgetting forgot missed
    miss left put
""".split())
# The shape of that ask: a word for the whole of it next to one of those words. Both are needed,
# because "what should i do" said with nothing on the screen wants the bot to ask what about, and
# "i include the VAT" names a thing.
A_MISSING_PART = re.compile(
    r"\b(?:anything|what|which|is there|are there|something|all)\b[^.?!]{0,40}?\b"
    r"(?:include|includes|including|bring|bringing|add|adding|say|saying|mention|mentioning|"
    r"cover|covering|know|wear|take|expect|prepare|check|forget|forgetting|forgot|missed|"
    r"miss|left|put)\b", re.I)
# "defo", "deffo", "probs" and "tbh" are fillers the same way "just" and "really" are, and they
# are not in the shared list: one of them left the line naming something, so "anything i should
# defo include" stood down. Only this reader needs them, so they are added here.
SOFT_FILLER = frozenset("""
    defo deffo definitely probs prob probably tbh honestly basically totally literally
""".split())
ASK = ASK | THE_MISSING_PART | SOFT_FILLER

# The shape of "what else", "anything other than that", "any other ideas": a word for another one
# next to a word for an option, which is what makes the line an ask for one.
OTHER_OPTION = re.compile(
    r"\b(?:what|anything|any|something|is there|are there|got any|have you got|"
    r"else|other|others|another|different|alternative|alternatives)\b",
    re.I)
# "Tips" and "tricks" are not a word for another one: "any tips" after an answer asks how to go
# about it, and read as a plea for another option it was handed the sentence it had just been
# shown, as "The other half of it". A line that wants another one says so ("any other tips",
# "anything else that helps", "what else can i do"), and those still come here.
AN_OPTION = re.compile(
    r"\b(?:else|other|others|another|different|alternative|alternatives|"
    r"ideas?|options?|suggestions?|ways?|things?|approaches?|"
    r"swaps?|substitutes?|substitutions?|replacements?)\b", re.I)
# Not every ask for the rest names an option. "and", "go on", "tell me more", "what next" and a
# bare "more" are the same request as "what else", and when the line is not read as one the person
# gets a cold line instead: "i cant sleep" / "go on" was "I have given you all of it." while
# "what else" handed back the rest of the same answer. So the words that carry an answer on count
# as asking for another option too, as long as the line names nothing of its own.
CARRY_ON = re.compile(
    r"^(?:(?:go|carry)\s+on|keep\s+going|continue|and(?:\s+(?:then|after\s+that|on))?|"
    r"then\s+what|after\s+that|whats?(?:'s|\s+is)?\s+next|next|more|"
    r"tell\s+me\s+more|say\s+more|go\s+deeper|and\s+what\s+else)\b", re.I)
# The same request with something friendly in front of it: "ok go on", "and then", "so what next".
LEAD_IN = re.compile(
    r"^(?:ok(?:ay)?|right|so|yeah|yes|alright|well|please|ta|thanks|cheers|and)[\s,]+", re.I)

# The modules whose last turn is an answer with a second half in it.
ANSWER_MODULES = ("answers", "chat", "knowledge")

# A hedge or a stock line says nothing worth handing back, and neither does an answer that is one
# sentence long: there is no other half to it.
HEDGE = repeat.HEDGE
STOCK = re.compile(
    r"\b(?:thanks for telling me|tell me more|say more if it helps|i'?m listening|"
    r"what would be most useful|anything you'?d like a hand with|noted)\b", re.I)

# A full stop ends a sentence, but not one inside a quotation: an answer that quotes a letter for
# the person to send has full stops of its own in it, and cutting there leaves the other half
# starting inside the quote ("Thanks, [name]." Follow it up in writing if nothing happens...).
SENTENCE = re.compile(r"(?<=[.!?])\s+")
QUOTE_MARKS = "\"\u201c\u201d"
# A lead-in the bot puts in front of an answer it is giving again ("From just now: ...").
FRAME = re.compile(
    r"^(?:from just now|same as before|as i said|like i said|same answer|same answer i'?m afraid|"
    r"it'?s what i said a moment ago|you'?ve got it|that'?s the one)\s*[:\-]\s*", re.I)

# How the rest is handed over. The sentence it quotes has been read already - it is part of the
# answer above - so the frame says how to take it, not that something was held back. "That answer
# had more in it" said the answer had been kept from them, and on a full answer that is simply
# untrue: `how do i clean my oven` / `keep going` handed back "The racks soak in hot water with a
# dishwasher tablet while the paste works", a sentence already on the screen. A frame that picks
# one thing out of what they read is true whether the sentence adds anything or repeats it.
LEADS = (
    "Of that, the bit that matters most: {rest}",
    "If you only do one thing from that answer: {rest}",
    "The part of that I would act on first: {rest}",
    "Of all of that, this is the bit I would not skip: {rest}",
    "The bit of that answer worth doing first: {rest}",
)

# A sentence that tells the person to do something, or says what a thing is worth, is a second
# option. A sentence that only describes ("nothing in them needs your full attention", "a
# whistling boiler is usually the same pump") is the tail of the answer, not another thing to try,
# and handing it over as one reads like padding.
DO_THIS = re.compile(
    r"\b(?:if|so|then|try|use|keep|check|give|take|put|get|add|buy|swap|replace|clean|wash|"
    r"rinse|leave|stand|wrap|store|feed|water|encourage|bleed|call|ask|book|avoid|stop|start|"
    r"turn|run|set|hold|move|cover|cut|open|close|repeat|ring|email|text|worth|helps?|"
    r"worthwhile)\b", re.I)

# A sentence that opens by commenting on the one before it ("It's a 20-minute job", "That's the
# whole point", "Nothing in them needs your full attention") is the tail of the answer, not a
# second thing to do, so it is never handed over as one.
A_COMMENT = re.compile(
    r"^\s*(?:it'?s|it is|it was|that'?s|that is|that was|this is|this was|there'?s nothing|"
    r"nothing|none of|both|all of)\b", re.I)

# A sentence that says of itself that it is the other option. It names the second thing in words
# the person can read as one - "Something else that works is a chilli", "There is a chilli as
# well" - and it has no instruction verb in it, so the two rules below read it as a tail of the
# answer: no step, and about some other thing. "what can i cook tonight with mince" / "another
# one" was answered "I'm listening - tell me." while the answer on the screen offered a chilli.
OFFERS_ANOTHER = re.compile(
    r"^\s*(?:something else|anything else|another (?:option|one|idea|way|thing|idea for)"
    r"|an? alternative|alternatively|otherwise|instead"
    r"|or (?:else )?(?:try|make|use|have|just|simply|do|go with)"
    r"|you could also|you can also|also try|you might also"
    # "There is a chilli as well" offers a second dish by its own words, and a sentence that names
    # a price, a catch or a risk is not offering anything: it is telling them what comes with it.
    r"|there(?:'s| is| are)\b"
    r"(?![^.]{0,70}\b(?:charge|fee|fees|cost|costs|price|deposit|catch|risk|downside|caveat|"
    r"trick|trouble|problem)\b)[^.]{0,70}\b(?:as well|too)\b)\b", re.I)

# "30 minutes from start to finish" is a length, not a step. The "start" in it is a noun, and it
# was enough for the sentence to be read as the doing of an answer, so a dinner that offered "There
# is a chilli as well" handed back "The part of that I would act on first: 30 minutes from start to
# finish" to a person who had asked for another one.
LENGTH_IDIOM = re.compile(r"\b(?:from\s+)?start\s+to\s+finish\b", re.I)


# A sentence that says what some other thing is like, or what it likes ("Basil hates the cold",
# "the pressure is 1 to 1.5 bar", "water at the front is usually the door seal"), is about that
# thing rather than something for the person to do - and when it names a different plant, machine
# or job, handing it over as "something else to try" is an answer about the wrong thing.
ABOUT_ANOTHER = re.compile(
    r"^(?!\s*(?:if|when|once|after|before|while|then|so|but|and|or|try|check|keep|give|take|"
    r"put|use|get|add|buy|swap|replace|clean|wash|rinse|leave|stand|wrap|store|feed|call|ask|"
    r"book|avoid|stop|start|turn|run|set|hold|move|cover|cut|open|close|repeat|ring|email|text|"
    r"pick|pinch|encourage|bleed)\b)\w+(?: [\w'\u2019()-]+){0,3} "
    r"(?:hates?|likes?|loves?|prefers?|needs?|wants?|is|are)\b", re.I)

# Someone else is the one with the problem: "my toddler wakes up at 5am every day" was answered
# with advice about an alarm clock, and its second half was about the parent's own bedtime - "be in
# bed eight hours before it" - which is no answer about a toddler at all. When the line a turn ago
# was about another person or animal, only a sentence that is about them as well is handed over.
A_PERSON = re.compile(
    r"\b(?:my|our|the)\s+(?:son|daughter|kids?|child|children|toddler|baby|boy|girl|mum|mom|"
    r"mother|dad|father|wife|husband|partner|boyfriend|girlfriend|brother|sister|friend|cat|"
    r"dog|puppy|kitten|rabbit|hamster|horse|nan|nana|granny|grandma|grandad|grandpa)\b", re.I)
THEM = frozenset("""
    he she him his her hers they them their themselves toddler baby boy girl son daughter kid
    kids child children cat dog puppy kitten rabbit hamster horse
""".split())

# A turn that only files what the person said is not an answer. "i want to get fit" / "i dont like
# gyms" / "what else" is one question - the advice, the part of it they cannot use, then the rest of
# it - and the middle turn is "Got it - you don't like gyms.", which has nothing in it to hand back.
# So the answer to lean on is looked for past it, and what they said in it is what must not be
# offered again: they have just told the bot not to.
FILING = re.compile(
    r"^\s*(?:got it|noted|right|okay|fair enough|thanks|that'?s noted|i'?ll remember|"
    r"understood|sure)\b", re.I)

# A line that says what the person does not want, or has already tried and will not do.
RULED_OUT = re.compile(
    r"\b(?:don'?t|do not|doesn'?t|didn'?t|can'?t|couldn'?t|won'?t|wouldn'?t|never)\s+"
    r"(?:really\s+|actually\s+)?(?:like|love|want|need|use|eat|drink|fancy|trust|stand|"
    r"have|bother with|go to)\b|"
    r"\b(?:hates?|hated|avoid|avoids|allergic to|not a fan of|sick of|tired of|gave up|"
    r"given up|stopped|quit|no time for|can'?t afford|too expensive|won'?t do)\b", re.I)

# The words of a rule-out line that are not the thing ruled out: the frame around it, and the
# markers that turn "like" into "don't like".
NOT_A_THING = topics.STOPWORDS | repeat.ASK | repeat.FILLER | frozenset("""
    dont do does doesnt didnt cant wont wouldnt never not anymore either too also any more
    actually really just very much such thing things stuff one ones going again
""".split())

# A line that carries a condition of its own is about that condition, not about the rest of the
# answer it is attached to: "and if they say no" after a pay-rise answer is a question about a
# refusal, and it was read as "what else" because every word in it is a filler word - so the bot
# handed back a sentence the person had already read. The condition is the whole of the new line,
# which is what makes it a new question rather than a request for more.
A_CONDITION = re.compile(
    r"\b(?:what\s+)?if\b|\bunless\b|\bsuppose\b|\bin\s+case\b|\bwhat\s+happens\s+(?:if|when)\b",
    re.I)

# The answer this leans on was given in the last couple of turns.
LOOK_BACK = 3
# A sentence short enough to read in one go; a longer one is cut at a clause break.
MOST = 220
LEAST = 25


def names_nothing(text):
    """True when the line asks for another option or the rest of the answer, naming nothing itself."""
    said = str(text or "")
    asks_for_more = bool(CARRY_ON.match(said.strip())
                         or CARRY_ON.match(LEAD_IN.sub("", said.strip()))) or (
        bool(OTHER_OPTION.search(said)) and bool(AN_OPTION.search(said))) or bool(
        A_MISSING_PART.search(said))
    if not asks_for_more:
        return False
    if repeat.ABOUT_THE_BOT.search(said):
        return False
    if A_CONDITION.search(said):
        return False
    words = topics.words(said)
    left = [w for w in words if w not in ASK and w not in topics.STOPWORDS and not w.isdigit()]
    return bool(words) and not left


def ruled_out_words(text):
    """The things a line says the person does not want, as stems, so "gyms" meets "gym"."""
    if not RULED_OUT.search(text or ""):
        return set()
    return {word.rstrip("s") for word in topics.words(text)
            if len(word) > 2 and word not in NOT_A_THING and not word.isdigit()}


def _names_one(part, ruled_out):
    """True when a sentence of the old answer offers something the person has just ruled out."""
    if not ruled_out:
        return False
    return bool(ruled_out & {word.rstrip("s") for word in topics.words(part)})


def _the_turn_to_lean_on(turns, memory=None):
    """The last answer to lean on, and what the person ruled out between it and the ask."""
    memory = memory or {}
    ruled_out = set()
    for back in range(1, LOOK_BACK + 1):
        if len(turns) < back:
            break
        turn = turns[-back]
        said = str(turn.get("bot") or "").strip()
        # A step handed back out of an answer is not the answer: "Fair enough - this part doesn't
        # need gyms: walk on the days between" has no second half in it, and the "what else" after
        # it is about the answer behind it.
        if said and not FILING.match(said) and not repeat.a_hand_back(said, memory):
            ruled_out |= ruled_out_words(str(turn.get("user") or ""))
            return turn, ruled_out, len(turns) - back
        # This turn only filed what they said. What they said is a rule-out when it is one, and
        # the ask is still about the answer before it.
        ruled_out |= ruled_out_words(str(turn.get("user") or ""))
    return None, ruled_out, None


def split_sentences(said):
    """The sentences of a line, with a full stop inside a quotation not counted as an end.

    An answer that hands the person a letter to send quotes it, and the letter has full stops in
    it: cutting there leaves the rest of the answer beginning inside the quote, so the person is
    handed `Thanks, [name]." Follow it up in writing if nothing happens in 48 hours.` The quoted
    passage is one sentence of the answer for this purpose; the full stop that ends it still ends
    the sentence, at the closing quote.
    """
    said = str(said or "").strip()
    parts, start, opened, ended = [], 0, False, False
    for at, char in enumerate(said):
        if char in QUOTE_MARKS:
            if opened:
                opened = False
                if ended and at + 1 < len(said) and said[at + 1].isspace():
                    parts.append(said[start:at + 1])
                    start = at + 1
                ended = False
            else:
                opened = True
        elif char in ".!?":
            if opened:
                ended = True
                continue
            after = at + 1
            while after < len(said) and said[after] in QUOTE_MARKS:
                after += 1
            if after >= len(said) or said[after].isspace():
                parts.append(said[start:after])
                start = after
    parts.append(said[start:])
    return [part.strip() for part in parts if part.strip()]


def _sentences(said):
    """The answer as sentences, with the lead-in frame the bot puts on a repeat taken off."""
    said = str(said or "").strip()
    said = FRAME.sub("", said)
    return split_sentences(said)


def _said_before(memory, said, before=None):
    """True when the bot has already said this sentence in a turn before the answer at hand.

    The answer being handed back is the last turn, and every sentence of it is in that turn, so it
    is left out here: what is looked for is the same sentence said *again* later on.
    """
    wanted = said.strip()[:50].lower()
    if not wanted:
        return False
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if before is None:
        before = len(turns) - 1
    for turn in turns[max(0, before - LOOK_BACK + 1):before]:
        if not isinstance(turn, dict):
            continue
        if wanted in str(turn.get("bot") or "").lower():
            return True
    return False


def _cut(said):
    """A sentence short enough to say, cut at a comma or semicolon when it is not.

    The cut is the shared one (`compose.whole.a_whole_cut`): a sentence cut at the last comma can
    be cut between a step and the condition it is for, and the hand-back then ends on "If it keeps
    happening." - the half of the sentence that says nothing. Where the condition would be left
    hanging, the helper keeps the doing or steps back in front of the condition instead.
    """
    said = said.strip()
    if len(said) <= MOST:
        return said
    return a_whole_cut(said, MOST).rstrip(" ,;:.") + "."

# A referral is not another thing to try. A health answer ends on when to get help ("See a GP if it
# is no better in a fortnight"), and the flag rule above catches the ones written that way round.
# The same sentence written the other way round - the condition first, the professional at the end
# ("If you are hungry all the time, or the weight is going on without trying, see a GP.") - has no
# step in front of it, so "what else can i do" after a weight plan handed it back as the bit worth
# doing first. A step that only applies in some cases is still a step ("If it is a big joint, ask
# the butcher to bone it"); what makes this one a caveat is the professional at the end of it.
A_PROFESSIONAL = re.compile(
    r"\b(?:see|speak to|talk to|ring|call|contact|ask|visit|book in with)\s+(?:a|an|your|the)\s+"
    r"(?:gp|doctor|nurse|practice nurse|pharmacist|chemist|midwife|health visitor|"
    r"physio(?:therapist)?|dentist|optician|consultant|specialist)\b", re.I)
FRAME_WORDS = re.compile(
    r"\b(?:if|when|whenever|unless|once|should|in case|and|so|then|but|or|also|really|actually|"
    r"still|again|too|either|instead)\b", re.I)
URGENT_LINE = re.compile(r"\b(?:ring|call|phone)\s+(?:111|999|911|112|nhs 24)\b", re.I)


def _a_caveat_about_getting_help(part):
    """True when the sentence is when to get help rather than something to try.

    The test is what is left when the referral is taken out. "Drink plenty of water, take
    paracetamol for the sting, and see a GP or pharmacist" still tells them to do two things and
    is handed over as one; a sentence whose only doing is the referral tells them nothing they can
    start on, so it is the warning at the end of the answer however it is worded.
    """
    if topics.RED_FLAG.match(part):
        return True
    if not (A_PROFESSIONAL.search(part) or URGENT_LINE.search(part)):
        return False
    left = A_PROFESSIONAL.sub(" ", URGENT_LINE.sub(" ", part))
    # The words that open a condition are not steps, and DO_THIS counts "if" and "so": what is
    # left after the referral has to be read without them or every "If you are hungry ... see a
    # GP" would look like a step on the strength of its own "if".
    left = FRAME_WORDS.sub(" ", left)
    return not is_a_step(left)


def is_a_step(part):
    """True when the sentence tells the person to do something, not just how long it takes."""
    return bool(DO_THIS.search(LENGTH_IDIOM.sub(" ", part)))


def _the_rest(said, memory, ruled_out=(), at=None):
    """The part of the answer the person has not been handed back yet, or "" when there is none."""
    parts = _sentences(said)
    if len(parts) < 2:
        return ""
    # The first sentence that tells them to do something is the one they were given, and the ones
    # after it are the other half. A lead-in in front of it ("Ugh, the first day of it is the
    # worst") is not one of them, so it does not count as the answer given.
    given = None
    for at, part in enumerate(parts):
        if is_a_step(part) and not _a_caveat_about_getting_help(part):
            given = at
            break
    if given is None:
        return ""
    def _is_the_rest(part, before):
        # A red flag is not a second option. A health answer ends on the warning ("See a GP if it
        # is no better in a fortnight"), and handing it back as "That answer had more in it" is a
        # referral dressed as something to try, with none of the framing that makes it a warning.
        # The skip is the flag, not the word "if": a step that only applies in some cases is still
        # a step.
        # A sentence that offers the other option in words of its own has no step in it and is
        # about another thing by the two rules below, and both of them are about a tail: "Basil
        # hates the cold" is not a second thing to do, and "Something else that works is a chilli"
        # is. So a sentence that says it is the other option is read as one first, and only a
        # sentence that says neither is skipped.
        offers = bool(OFFERS_ANOTHER.match(part))
        return not (len(part) < LEAST or _a_caveat_about_getting_help(part)
                    or (not is_a_step(part) and not offers)
                    or A_COMMENT.match(part)
                    or (ABOUT_ANOTHER.match(part) and not offers)
                    or _names_one(part, ruled_out) or _said_before(memory, part, before))

    for here in range(given + 1, len(parts)):
        part = parts[here]
        if not _is_the_rest(part, at):
            continue
        # A quotation ends the sentence without ending the step: "one private sentence does more
        # than a meeting fight: 'When you presented that, it would help me if you said it came
        # from me.' Then put your ideas in writing." Handing back only the quoted words leaves the
        # person with the words and not the doing, so the sentence after a quotation comes with it.
        if part[-1] in QUOTE_MARKS:
            for after in range(here + 1, len(parts)):
                if _is_the_rest(parts[after], at):
                    part = part + " " + parts[after]
                    break
        if OFFERS_ANOTHER.match(part) and len(part) <= MOST:
            # The sentence names the other option itself, so it is handed over whole. A cut at a
            # clause break can take the dish and leave the words that make it an option ("Something
            # else that works is"), and the only sentence of an answer that reads as complete on
            # its own is the one that says what it is.
            return part[:1].upper() + part[1:]
        return _cut(part)
    return ""


def other_option(text, memory):
    """The second half of the answer they just asked for more of, or None when it is not that."""
    if not names_nothing(text):
        return None
    if named.asks_a_part_of_the_trip(text, memory):
        # A line that steers to one part of a trip asks its own question about the place the card
        # is about, and the second half of that card is not the answer to it: "how many days do i
        # need" after the guide for a city came back as "The beach at Barceloneta for half a day."
        return None
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    if not turns:
        return None
    turn, ruled_out, at = _the_turn_to_lean_on(turns, memory)
    if turn is None:
        return None
    said = str(turn.get("bot") or "").strip()
    module = str(turn.get("module") or "")
    if module not in ANSWER_MODULES and not said:
        return None
    if not said or said.rstrip().endswith("?") or HEDGE.search(said) or STOCK.search(said):
        return None
    rest = _the_rest(said, memory, ruled_out, at)
    if not rest:
        return None
    asked_about = str(turn.get("user") or "")
    if A_PERSON.search(asked_about) and not THEM & set(topics.words(rest)):
        return None  # a sentence about the person, when the question was about someone else
    if OFFERS_ANOTHER.match(rest):
        # The sentence is the other option in its own words, so it is handed over as it stands. The
        # frames in `LEADS` say how to take part of an answer the person has already read, and in
        # front of a sentence that is answering the ask they just made they read as the bot talking
        # about its own advice: "The part of that I would act on first: Something else that works is
        # a chilli."
        return rest
    return pick(LEADS, memory, text).format(rest=rest)
