"""A follow-up about the answer the bot has just given is answered out of that answer.

    how do i get rid of the smell in the washing machine
      "The black lives in the fold of the door seal: pull it open, wipe the fold with a cloth and
       a little white vinegar or a mould spray, and dry it. Leaving the door and the drawer open
       between washes is what stops the smell coming back."
    what should i do about the smell
      "That's beyond what I know well, sorry. Searching for it will turn up better sources than I
       can offer; tell me what you find and I'll help you make sense of it."

No entry claims the second line and no module does either, so it reached the search hedge - and
the hedge is not true there, because the answer is on the person's screen already. The same on
"should i cut the leaves off" after the powdery mildew answer ("Not mine to decide, sorry") and on
"does that mean i should stop watering" after the white mould one. What the person wants is the
part of that answer their line is about, so the reply hands back the sentence of it that carries
the words they asked with - the sentence, not the whole answer, because the answer is a paragraph
and they have read it.

Three things have to hold, and each is a way of not taking a turn that has a better answer: the
last turn was a knowledge answer (`_the_answer_to_hand_back` - not a hedge, and not one of the
composer's own notes, which add no fact), the line names no thing of its own (`what about a
helmet` wants a helmet, and no sentence of the bike answer gives one), and there is a sentence of
the answer worth handing back.

It is asked from `bot/modules/greeting.py`, last, and only in place of a hedge: the composer's
repeat card ("that is all of what I know on it") is a real answer to the same question asked
twice, and the arbiter has rules for it (`bot/modules/arbiter.py`).
"""
import re

from ..understanding.kinds import a_stop_ask
from . import fallback, verdict

# A follow-up about the answer the bot has just given, where no entry and no module claims the
# line, reached the search hedge - and the hedge is not true there, because the answer is on the
# person's screen already:
#
#     white powder on my cucumber leaves
#       "White powder on the leaves is powdery mildew ...: water thoroughly at the base rather
#        than sprinkling the leaves, take off the worst of them ..."
#     should i cut the leaves off
#       "Not mine to decide, sorry. Tell me what matters most here and I'll help you think it
#        through."
#
# The same on "does that mean i should stop watering" after the answer about the white mould, and
# on "what should i do about the smell" after the answer that says it lives in the fold of the door
# seal and gives the steps to clean it. What the person wants is the part of that answer their line
# is about, so the reply hands back the sentence of it that carries the words they asked with - the
# sentence, not the whole answer, because the answer is a paragraph and they have read it.
#
# Three things have to hold, and each is a way of not taking a turn that has a better answer:
# the last turn was a knowledge answer (`_the_answer_to_hand_back`, and not a hedge or a note), the
# line names no thing of its own (`what about a helmet` wants a helmet, and no sentence of the bike
# answer gives one), and there is a sentence of the answer worth handing back.
#
# It is asked from `bot/modules/greeting.py`, last, and only in place of a hedge: the composer's
# repeat card ("that is all of what I know on it") is a real answer to the same question asked
# twice, and the arbiter has rules for it (`bot/modules/arbiter.py`).
ON_SCREEN_LINES = (
    "That is in the answer above: {said}",
    "Same answer: {said}",
    "It is in what I said above: {said}",
)

# A bare "should i stop" is not asking where the answer is, it is asking whether the bot still means
# it: the lead-ins above read as a brush-off on that line ("That is in the answer above: keep
# sessions to fifteen minutes and stop when they start to sting"), because they say where the
# answer sits instead of standing by it. The sentence is the same sentence either way.
STANDS_BY_LINES = (
    "I'd go by what I said: {said}",
    "I still stand by this: {said}",
    "Same answer, and it holds: {said}",
)

# The ask that makes a line a follow-up rather than a question of its own: it opens with a
# question word or an auxiliary, the way people type without punctuation.
ON_SCREEN_ASK = re.compile(
    r"^(?:so|and|but|ok|okay|then|also)?\s*,?\s*(?:what|how|which|where|when|who|why|should|"
    r"shall|can|could|do|does|did|is|are|will|would|any)\b", re.I)

# "and what about a helmet" asks about a thing by name, and a thing asked about by name is a new
# question: the sentence about the bike's frame is not an answer about a helmet.
A_THING_NAMED_IN_FRONT = re.compile(
    r"^(?:so|and|but|ok|okay|then|also)?\s*,?\s*what about\b", re.I)

# A sentence of an answer that carries a step, which is what a follow-up asks for when it shares
# no word with the answer at all ("what should i do about the smell").
A_STEP_IN_IT = re.compile(
    r"\b(?:check|clean|clear|call|ring|ask|take|put|add|set|switch|turn|leave|keep|try|use|"
    r"replace|restart|update|move|fix|buy|get|book|look|make|run|wash|start|plug|test|wipe|"
    r"pull|open|close|soak|water|cut|pick|apply|scrub|hoover|vacuum|cover|store|wrap|rinse|"
    # Effort rather than a thing: "should i push through" asks how hard to go at the answer's
    # own subject, and no sentence of that answer has to say "push" for it to be the reply.
    r"push|carry|plough|plow|soldier)\b",
    re.I)
# A sentence that is a sign-off, a hedge or a question of the bot's own says nothing to hand
# back: quoting "Hope that helps" or "A quick search will get you a solid answer" is the shrug
# twice.
NOT_TO_HAND_BACK = re.compile(
    r"^(?:hope\b|good luck|let me know|take care|all the best|sorry\b|i'm sorry|im sorry|"
    r"i don't know|i dont know|i'm not sure|im not sure|i can't|i cant|i would|i'd)", re.I)
# What a follow-up asks for when it names the thing only as a symptom of the answer's thing:
# "what should i do about the smell", "how do i stop it", "does that mean i should stop
# watering". Without one of these, a line that shares no word with the answer is a new question.
ASKS_WHAT_TO_DO = re.compile(
    r"\b(?:what (?:should|do|can) i do|what do i do|how do i|how can i|should i|do i need to|"
    r"does that mean|will that|is that enough|is it enough|how much|how long|how often)\b", re.I)
# The step is only handed back when the line is about the thing the answer was about, and a line
# that shares no word with the answer says so by pointing back at it: "does that mean i should
# stop watering", "what should i do about the smell". "how do i stop condensation on my windows"
# shares no word with the shelf answer and points at nothing in it, so it is a new question and
# keeps whatever answer it can get.
POINTS_BACK = re.compile(
    r"\b(?:it|its|it's|that|this|they|them)\b"
    r"|\b(?:about|with) (?:the|my|our|his|her|their)\b", re.I)
# A line that asks for the action and names nothing of its own - "what should i look for" after a
# fever answer, "should i watch for anything", "what should i expect" - is asking about the action
# the answer takes, so the answer's own first sentence is the reply and saying it again is the
# point of the turn. Only when every word that carries meaning in the line is one of these: a line
# with a thing of its own in it ("what should i look for in a car seat") is a new question.
NAMES_NOTHING_OF_ITS_OWN = frozenset((
    "look", "expect", "watch", "take", "bring", "wear", "say", "ask", "try", "buy", "get",
    "need", "want", "now", "next", "first", "else", "then", "there", "anything", "something",
    "work", "works",
    # An adverb that only presses on the verb adds no subject of its own: "is there anything that
    # actually works" after the snoring answer asks the same thing as "is there anything that
    # works", and it reached the search hedge only because `actually` was a word the answer had
    # not got, which made it look like a thing the answer does not cover.
    "actually", "really", "truly", "genuinely", "seriously", "even", "ever", "honestly",
    # Same for the verb that asks whether the answer does anything, and the one that asks whether
    # it is so: "does anything actually help" after the snoring answer, "is that right" after a
    # card. A line that names its own thing keeps it out of this check whatever is on this list.
    "help", "helps", "helping", "true", "right", "correct", "wrong", "case", "sure",
))
# A line that carries a word the answer has not got names something the answer does not cover,
# and the sentence about the answer's own thing is not its answer: "what should i do about the
# frame" after an answer about a slipping chain, "what should i do about the dog" after the ants,
# "what should i do about the sauce" after an egg. Asking words do not count, because they add no
# subject of their own: "is that enough", "how long", "does that mean i should stop watering",
# "should i cut the leaves off" (a verb in front of the thing).
ASKS_RATHER_THAN_NAMES = frozenset("""
mean means meant stop stops started start keep keeps keeping give gives need needs
help helps try tries use uses used work works working do does doing done happen happening
happens enough better worse best long much many often soon cost costs price way time point
anyway else instead still just really actually suppose supposed about around
off out up down over back away on in through along ahead
""".split())
# A word that describes rather than names, and so stands for the thing the answer is already about:
# the smell is the washing machine's, the leak is the boiler's, the mould is the seedling's. It only
# does that when somebody in the chat has said the word - the line itself, the line before it or the
# answer - because "what should i do about the smell" after an answer about a slow laptop is a
# question about a smell, and handing back the laptop's startup steps for it is worse than a hedge.
# A follow-up that names a thing the chat has not mentioned is asking about something new, and the
# hedge is the honest reply to that.
THE_THINGS_IT_COULD_BE_ABOUT = frozenset("""
smell smells smelly noise noisy sound sounds leak leaks leaking damp mould mold mildew stain
stains colour color taste tastes itch itchy ache aches pain pains mess dirty dirt rust rusty
water wet burning squeak squeaks rattle rattles bang banging drip dripping dust
""".split())
# "do i need to buy anything" after the ants answer asked whether a purchase is needed and was
# handed back the steps, framed as though it were the answer to that. A line that asks about buying
# or paying is only answered by the sentence that names the buying or the price: the steps around
# it are what to do once the thing is in the house.
# "who can i talk to" after a crisis card is asking for the number in the card, and it reached the
# search hedge: a card is the one answer above where the first sentence IS what the line asks for.
WHO_TO_TALK_TO = re.compile(
    r"\b(?:who can i (?:talk|speak|ring|call)|who should i (?:talk|speak|ring|call)|"
    r"who do i (?:talk|speak|ring|call)|where can i get help|who can help me)\b", re.I)
# Where help is, in the words a card uses for it: the sentence to hand back to "who can i talk to"
# is the one with the number or the person in it, not the one that says the feeling is understood.
A_HELP_IN_IT = re.compile(
    r"\b(?:crisis line|helpline|hotline|samaritans|116 ?123|988|999|111|911|emergency number|"
    r"a and e|a&e|gp|doctor|nurse|midwife|health visitor|pharmacist|social worker|"
    r"ring|call|phone)\b", re.I)
A_BUY_ASK = re.compile(
    r"\b(?:do i need to buy|need to buy|anything to buy|what do i need to buy|what to buy|"
    r"will it cost|how much (?:is|does|will)|is it (?:cheap|expensive)|worth buying)\b", re.I)
A_PURCHASE_IN_IT = re.compile(
    r"\b(?:buy|buys|buying|bought|cost|costs|price|prices|pound|pounds|dollar|dollars|"
    r"cheap|cheaper|expensive|order|shop|store|supermarket|pharmacy|chemist|can of|a tube of|"
    r"a bottle of|a packet of|a box of)\b", re.I)
# A sentence lifted out of an answer keeps its discourse word, and framing it reads badly: "Same
# answer: Then run the hottest empty wash the machine has". The word is doing its job in the
# paragraph and none at all in a sentence said on its own, so it goes.
A_LEAD_IN = re.compile(r"^(?:so|then|and|but|also|now|first|next),?\s+", re.I)
# A sentence with a quoted message in it is a draft of what to say to somebody, not an answer to a
# question about the situation: "should i drop it" about a row with a friend is not answered by
# handing back the message the bot wrote out for them to send.
QUOTED = re.compile(r"[\"\u201c\u201d][^\"\u201c\u201d]{2,}[\"\u201c\u201d]")
# "should i cancel the card", "is it worth it" asks for a decision, and only a sentence that
# carries a step answers that: a sentence saying the card can be unfrozen tells them what is true,
# not what to do, and they have already asked what to do.
A_DECISION_ASK = re.compile(r"\b(?:should|shall|ought)\s+i\b|\bis it worth\b|\bdo i need\b",
                            re.I)
LONG_SENTENCE = 52


# Words that join the parts of a line rather than name anything: "is that because they are not
# pricked" asks about `pricked` and adds `because` to the answer's `pricking` as if it were a thing.
# `fallback.POINTING` is most of this list; these are the ones it does not carry.
A_WORD_THAT_ONLY_JOINS = frozenset("""
because cause cos since whether though although while during before after until unless
not dont doesnt didnt cant cannot wont isnt arent wasnt werent havent hasnt couldnt wouldnt
shouldnt am are was were been being have has had having do does did doing can could would
should will shall may might must
""".split())


# The letters that are doubled for the spelling and not for the word: "running" gives "runn",
# never "run", and "stopped" gives "stopp". A doubled s, f or z is the word itself ("less",
# "stuff"), so those come off only with the ending above.
_DOUBLED = "bdgmnprtl"


def _stem(word):
    """The word without the ending that makes it a plural, a past tense or a participle.

    The doubled last letter of "running", "stopped" and "getting" comes off too, so a question in
    the plain form ("can i still run") meets the answer's "-ing" word ("drop the running mileage")
    instead of looking like a thing the answer has never heard of.
    """
    for ending in ("ing", "ed", "es", "s"):
        if len(word) - len(ending) >= 4 and word.endswith(ending):
            word = word[:-len(ending)]
            break
    if (len(word) >= 4 and word[-1] == word[-2] and word[-1] in _DOUBLED):
        word = word[:-1]
    return word


def _the_same_word(word, said):
    """True when `word` is in `said`, plurals and the -ing form counting as the same word."""
    if word in said or word.rstrip("s") in said or word + "s" in said:
        return True
    if _stem(word) in _stems(said):
        return True
    return bool(len(word) >= 5 and any(len(other) >= 5 and word[:5] == other[:5]
                                      for other in said))


def _stems(words):
    return set(_stem(word) for word in words)


# A word of effort, which in a follow-up asks how hard to go at the answer's own subject rather
# than naming one: "should i push through", "shall i carry on", "can i keep going". None of them
# names a thing, so none of them stands the reading down - the answer's own action is the reply.
EFFORT_WORDS = frozenset("""push pushes pushing carry carrying keep keeping continue continuing
on through harder ahead along""".split())


def _names_something_new(mine, said, in_the_chat):
    """True when the line carries a word the answer has not got and that names a thing.

    A word the answer shares is the same subject, a word that asks (`is that enough`, `how long`)
    adds no subject at all, and a word that describes the thing the answer is about (`the smell`,
    `the leak`) adds none either - but only when the chat has already named it, which is what
    `in_the_chat` is. A verb in front of the thing is an action rather than a subject (`should i
    cut the leaves off`); a verb at the end of the line is where a thing would be (`the school
    run`) and counts like any other word. Anything else is something the answer does not have, and
    it stands the reading down.
    """
    last = mine[-1] if mine else ""
    for word in mine:
        if _the_same_word(word, said):
            continue
        if word in ASKS_RATHER_THAN_NAMES or word in EFFORT_WORDS:
            continue
        if word in THE_THINGS_IT_COULD_BE_ABOUT and _the_same_word(word, in_the_chat):
            continue
        if word != last and A_STEP_IN_IT.search(word):
            continue
        return True
    return False


def _the_words_in_the_chat(memory, answer):
    """Every word said in the exchange the answer belongs to: the line before it, and the answer."""
    words = set(fallback._flat_words(answer))
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    for turn in turns[-2:]:
        words |= set(fallback._flat_words(str(turn.get("user") or "")))
    return words


def _the_answer_to_hand_back(memory):
    """The bot's last knowledge answer, skipping notes and repeats of it.

    "what should i do about the smell" comes two turns after the answer, because the line
    between them ("how do i clean it") was itself answered with the composer's "that was the
    whole of my answer on it": the answer is still the one on the person's screen, so it is the
    one to hand back. A turn of the composer's own is not an answer to come back with - the note
    it wrote adds no fact - and a hedge is not either.

    A safety card counts as a knowledge answer: "i was abused growing up" is answered with the
    card that says flinching is what an old injury does, and "is that why i flinch" one line later
    got "Searching for it will turn up better sources than I can offer". The card's own sentence is
    the answer to that, and handing it back cannot take the card away - it was the turn before.

    The reach itself is one check, in `bot/memory/history.py`, so that every module that reads a
    follow-up out of an earlier turn steps back over the same turns (`the_answer_on_screen`).
    """
    from ..memory import history

    return history.the_answer_on_screen(memory)


def _the_answer_is_a_card(memory):
    """Whether the answer above is a safety card rather than a knowledge entry."""
    from ..memory import history

    return history.the_answer_is_a_card(memory)


# The sentence asked about, or the clause of it after a colon: the part of "White powder on the
# leaves is powdery mildew ...: water thoroughly at the base, take off the worst of them" that
# answers "should i cut the leaves off" is the steps, not the naming of the mildew.
CLAUSE_AFTER_A_COLON = re.compile(r":\s+(.+)$")


# An answer sentence can be longer than anything worth saying on its own: the pricking answer is
# one sentence of 50 words, and the half of it that answers "is that because they are not pricked"
# is the half before the colon. A long sentence is read as its parts, and the part that carries the
# word asked about is the piece to hand back.
A_LONG_SENTENCE_SPLIT = re.compile(r":\s+|;\s+")


def _the_parts(sentence):
    """The sentence, or its parts at a colon or a semicolon when it is too long to say on its own."""
    if len(sentence.split()) <= LONG_SENTENCE:
        return [sentence]
    parts = [one.strip() for one in A_LONG_SENTENCE_SPLIT.split(sentence) if one.strip()]
    if len(parts) < 2:
        return [sentence]
    return [parts[0]] + [one[0].upper() + one[1:] for one in parts[1:]]


def _the_sentence_to_hand_back(sentence, mine, said):
    """`sentence`, or its clause after a colon when that is the part the line asks about."""
    tail = CLAUSE_AFTER_A_COLON.search(sentence)
    if tail:
        clause = tail.group(1).strip()
        in_the_clause = any(_the_same_word(word, set(fallback._flat_words(clause)))
                            for word in mine)
        if (len(clause.split()) >= 6
                and (in_the_clause
                     or sum(1 for word in mine if _the_same_word(word, said)) == 0)):
            sentence = clause[0].upper() + clause[1:]
    return sentence


# A line that asks whether to go on with the thing the answer is about: "should i push through",
# "can i carry on", "shall i keep going". It shares no word with a knee answer that says "keep
# going as far as is comfortable", so no sentence of the answer scored and the whole reading stood
# down on the one follow-up where the answer already holds the rule.
A_GO_ON_ASK = re.compile(
    r"\b(?:push(?:\s+(?:on|through|harder))?|carry\s+on|keep\s+(?:going|on|at\s+it|it\s+up)|"
    r"continuing|continue|go\s+on|going\s+on|crack\s+on)\b", re.I)
# "How far do I go" is only answered by a sentence that carries the limit. A step that only says
# what to do is not one: "Check the thigh reads 74C" is a test and "a wasp nest dies in autumn and
# is never reused" is a fact, and neither says where to stop, so a line asking whether to push on
# gets nothing from them and keeps the hedge it had.
A_LIMIT_IN_IT = re.compile(
    r"\bas\s+far\s+as\b|\bfor\s+as\s+long\s+as\b|\bno\s+more\s+than\b|\bnot\s+(?:much\s+)?past\b|"
    # `until` and `till` are only a limit when what follows is the going on being stopped or
    # allowed: "until it eases", "until you can", "till it stops hurting". "Rinse it until the
    # water runs clear" is a step, not a limit, and handing it back to "shall i carry on" is a
    # sentence that does not answer how far.
    r"\b(?:un)?til\s+(?:it|you|they|things|the\s+(?:pain|soreness|swelling|bleeding))\s*"
    r"(?:eases|eased|is\s+(?:better|easier|still|comfortable)|stops|settles|calms|feels|can|are\s+able|hurts|gets\s+worse)?\b|"
    r"\bwhile\s+(?:it|you|the|they)\b|\bshort\s+of\b|\bup\s+to\b|"
    r"\bstops?\s+(?:if|when|as\s+soon|before|at)\b|\bease[sd]?\s+off\b|\bback(?:s|ed)?\s+off\b|"
    r"\bfor\s+(?:a|the\s+first|one|two|three)\s+(?:week|fortnight|day|while|few)\b|"
    r"\bfor\s+a\s+while\b|\bin\s+short\s+bursts\b|\blittle\s+and\s+often\b|"
    r"\bno\s+more\s+of\s+than\b|\bwhen\s+it\s+(?:starts|hurts|gets\s+hard|feels)\b", re.I)
# A step that asks for the one detail that settles it is an answer to "which one" without a
# limit in it: "Tell me what it did - sank, dry, heavy, burnt - and I will give you the fix" names
# the thing that decides, so "should i start again or carry on" is answered by it.
ASKS_WHAT_DECIDES = re.compile(
    r"\b(?:tell|say|let)\s+me\s+(?:what|how|which|whether|if|more)\b|"
    r"\bwhat\s+(?:it|they|you)\s+(?:did|does|looks?\s+like|smells?\s+like|tastes?\s+like)\b", re.I)
# The one place that reads the answer above for a sentence to hand back. It is asked last, from
# `bot/modules/greeting.py`, and only when the composer has nothing but a hedge.
def the_answer_on_screen(text, memory):
    """The sentence of the last answer that answers this line, framed, or "" for none.

    Only a knowledge answer or a safety card counts (`_the_answer_to_hand_back`), because a card's
    answer is the thing worth handing back: the composer's own line has no entry behind it to come
    back with, and a reply that is already an acknowledgement hands back nothing.
    """
    try:
        clean = " ".join(str(text or "").lower().split())
        if not clean or not ON_SCREEN_ASK.match(clean):
            return ""
        if A_THING_NAMED_IN_FRONT.match(clean):
            return ""
        # A follow-up is short: "what should i do about the smell", "can i still travel", "does
        # that mean i should stop watering". A line long enough to ask something of its own is one -
        # "how much does it cost to put up a shelf on plasterboard" is a cost, and the answer
        # above has no cost in it - so it keeps whatever answer it can get.
        if len(clean.split()) > 8:
            return ""
        if fallback._hedged_recently(memory):
            return ""
        answer = " ".join(str(_the_answer_to_hand_back(memory) or "").split())
        if not answer:
            return ""
        sentences = [one.strip() for one in re.split(r"(?<=[.!?])\s+", answer) if one.strip()]
        mine = [word for word in fallback.content_words(clean)
                if word not in A_WORD_THAT_ONLY_JOINS]
        said = set(fallback._flat_words(answer))
        # A line that names nothing of its own at all ("what should i look for") is the strictest
        # case there is, so the check for a new thing has nothing to add to it.
        asks_who_to_talk_to = bool(WHO_TO_TALK_TO.search(clean)) and _the_answer_is_a_card(memory)
        if (not asks_who_to_talk_to
                and not all(word in NAMES_NOTHING_OF_ITS_OWN for word in mine)
                and _names_something_new(mine, said, _the_words_in_the_chat(memory, answer))):
            return ""
        best, best_score, first_step, opening = "", 0, "", ""
        steps = []
        for sentence in sentences:
            if len(sentence.split()) < 5 or sentence.endswith("?"):
                continue
            if NOT_TO_HAND_BACK.match(sentence):
                continue
            if QUOTED.search(sentence):
                continue
            if any(punt in sentence.lower() for punt in fallback.PUNT):
                continue
            step = bool(A_STEP_IN_IT.search(sentence))
            if step:
                steps.append(sentence)
                if not first_step:
                    first_step = sentence
            if not opening:
                opening = sentence
            # Scored on the sentence's own words, not the answer's: every line's words are in the
            # answer somewhere, so scoring on the whole of it makes every sentence a match. A
            # sentence too long to say on its own is scored as its parts, so the half carrying the
            # word asked about can still be the reply.
            for piece in _the_parts(sentence):
                if len(piece.split()) > LONG_SENTENCE:
                    continue
                words = set(fallback._flat_words(piece))
                score = sum(1 for word in mine if _the_same_word(word, words))
                if score and score > best_score:
                    best, best_score = piece, score
        if (not best and first_step and ASKS_WHAT_TO_DO.search(clean)
                and POINTS_BACK.search(clean)):
            # The line shares no word with the answer and asks what to do, so the answer's own
            # step is the reply ("what should i do about the smell" after the door-seal answer).
            best = first_step
        says_it_again = False
        if asks_who_to_talk_to and not best:
            for sentence in sentences:
                if A_HELP_IN_IT.search(sentence) and not NOT_TO_HAND_BACK.match(sentence):
                    best = sentence
                    break
        if not best and opening and asks_who_to_talk_to:
            # A card's first sentence is where the number is ("Ring a crisis line now (116 123 in
            # the UK, 988 in the US) or your local emergency number"), so it is the reply, said
            # again rather than hedged.
            best, says_it_again = opening, True
        if not best and mine and all(word in NAMES_NOTHING_OF_ITS_OWN for word in mine):
            # "what should i look for" shares no word with the fever answer and names nothing of
            # its own: what it asks for is the action the answer takes, and that is its first
            # sentence. It is the one case where the answer's opening is the reply, because that
            # sentence is the part the line is about.
            best, says_it_again = opening, True
        if not best and A_GO_ON_ASK.search(clean):
            # "should i push through" shares no word with the answer, so nothing scored, and what it
            # asks is how far to go - which is the action the answer takes: "keep going as far as
            # is comfortable", "ease off running and keep it moving gently". A step that says what
            # to do and no more ("check the thigh reads 74C", "a wasp nest dies in autumn") is not
            # an answer to how far, and handing it back is a line that would fit any message, so
            # only a step carrying the limit itself is the reply.
            best = next((one for one in steps
                         if A_LIMIT_IN_IT.search(one) or ASKS_WHAT_DECIDES.search(one)), "")
        if not best:
            return ""
        if A_DECISION_ASK.search(clean) and not A_STEP_IN_IT.search(best):
            return ""
        if A_BUY_ASK.search(clean) and not A_PURCHASE_IN_IT.search(best):
            return ""
        # A line asked three times gets the same sentence three times, with a different opener each
        # time: a sentence this reading already handed back is the repeat card's turn, not another
        # round of the same words.
        already = " ".join(fallback._flat_words(best))
        turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
        source = -1
        for place, turn in enumerate(turns):
            if str(turn.get("bot") or "") == answer:
                source = place
        for turn in turns[source + 1:]:
            if already and already in " ".join(fallback._flat_words(str(turn.get("bot") or ""))):
                return ""
        if not says_it_again:
            best = _the_sentence_to_hand_back(best, mine, said)
        # The answer's own opening sentence, said again, is what the person has just read: that
        # is the repeat card's turn, and the arbiter has a rule for it (`bot/modules/arbiter.py`,
        # `_a_shorter_said_again`). A sentence further in is the part the follow-up points at, and
        # handing that back is the point of this reading.
        first_said = " ".join(fallback._flat_words(answer))
        if (not says_it_again
                and first_said.startswith(" ".join(fallback._flat_words(best))[:60])):
            return ""
        given = A_LEAD_IN.sub("", best)
        if given and given != best:
            best = given[0].upper() + given[1:]
        if a_stop_ask(clean):
            frames = STANDS_BY_LINES
        else:
            frames = (ON_SCREEN_LINES[:1] if says_it_again else ON_SCREEN_LINES)
        reply = fallback._choose(frames, memory, clean).replace("{said}", best)
        # The sentence may be the one the bot handed back on the turn before: that reply already
        # said it, and the composer's line for a repeat stands rather than saying it again.
        flat = " ".join(fallback._flat_words(reply))
        recent = {" ".join(fallback._flat_words(str(t.get("bot") or "")))
                  for t in (memory.get("turns") or [])[-3:] if isinstance(t, dict)}
        if flat in recent:
            return ""
        return reply
    except Exception:  # noqa: BLE001 - a reading that fails leaves the composer's reply alone
        return ""




# --- whether there is a conversation at all ---------------------------------------------------
#
# Some replies talk about the conversation itself: "Welcome back. Where were we?", "Hello again.
# What's next?", "As I said", "Still here, if you want to carry on". Each is a good line in the
# middle of a chat and a line that invents one on the first thing a person says. The reading of
# whether there is a conversation to talk about is made once, here, because two places need it -
# the pool of wordings a module answers from (`bot/modules/chat.py`) and the pick among the
# modules (`bot/modules/arbiter.py`) - and two answers to it would drift apart.

_ABOUT_THE_CONVERSATION = re.compile(
    r"\b(?:hello again|hi again|you again|here again)\b"
    r"|\bwhere (?:were we|we (?:were|left off|got to)|did we (?:get to|get))\b"
    r"|\bwhat were we (?:saying|doing|on about)\b"
    r"|\bcarry on where\b|\bpick (?:it |things |up )?where\b"
    r"|\bas (?:i|we) (?:said|mentioned)\b|\blike i (?:said|mentioned|told you)\b"
    r"|\b(?:what|that) i (?:said|told you)\b"
    r"|\byou (?:said|mentioned|told me) (?:earlier|before|last time|a moment ago|just now)\b"
    r"|\byou said\s*:"
    r"|\bsince we last spoke\b|\bsame as before\b|(?<!not )\bthe last time\b|\blast time you\b"
    r"|\bearlier you\b", re.I)


def earlier_turn(memory):
    """Whether anything has been said before this line.

    The runtime appends the turn after the modules have answered, so a memory with no turns in it
    is the opening line of a chat and any turn at all means there is a conversation.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    return bool(isinstance(turns, list) and turns)


def talks_about_the_conversation(reply):
    """Whether a reply refers to something said before it in this conversation.

    Only the reply's own words are read: a line that says "as I said" or "you said earlier" is
    standing on an earlier turn whether or not one happened, and that is the whole test. What the
    person's own life refers to is not this: "welcome back from Leeds" answers someone who has
    just come back from Leeds on the first line, so the pools whose lines are about a real return
    (`trip`, `back_from`) are left alone, and the pools that are only about returning to a chat
    are answered as a greeting instead (`FIRST_LINE_POOL` in `bot/modules/chat.py`).
    """
    # Words in quotation marks are the person's own, put in their mouth by the answer: "come
    # back with 'sorry, that caught me - where were we?'" is advice about what to say, not the
    # bot saying it, so the quoted part is not read.
    unquoted = re.sub(r"[\"“][^\"”]*[\"”]", " ", str(reply or ""))
    return bool(_ABOUT_THE_CONVERSATION.search(unquoted))
