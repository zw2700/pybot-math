"""A bare "what can i take" is a question about the thing the chat is on.

The four words name nothing to take and nothing to take it for, so every reader that needs a
subject reads them off the words alone. On main the person who had just said "i keep getting
heartburn" got a packing question, and the person who had just said "my back is killing me" got
the duty-free allowance:

    i keep getting heartburn / is it normal / what can i take
      -> "What are you going to, and how long for? Then I can say what to take and what to leave."
    my back is killing me / what can i take
      -> "Coming into the UK you can bring 4 litres of spirits, 18 litres of wine..."

The knowledge base has the answer to the question the person is actually asking. What it cannot
do is see the thing the chat is on: a line with no subject in it reaches no entry. So this module
puts the subject in and asks, in the words the entries are keyed on ("what can i take for
heartburn", "what can i take for back pain"), and answers only when

- the line is the bare ask and names nothing itself - a thing of its own ("what can i take to
  spain", "can i take ibuprofen") is left to the readers that can read it,
- the chat is not a trip, where the packing question is the right answer,
- the chat says a subject with the person in it ("my back is killing me", not "the boiler is
  making a noise" - nothing is taken for a boiler), and
- the answer the entry gives names that subject and is not the answer already on the screen.

Everything else is passed on, and the reply the person is getting today stands.
"""
import re

from . import topics

# Leading fillers: how a follow-up opens in speech. "so what can i take", "and what can i take".
FILLER = re.compile(r"^(?:(?:so|and|but|ok|okay|well|right|ah|oh|hmm|then|now|also|please)\b"
                    r"[\s,]+)*")

# The bare ask, with nothing named in it. The tail a person adds without naming anything is part
# of the same ask ("for it", "for this", "for the pain"), so it is allowed and dropped.
NOTHING_NAMED = re.compile(
    r"^(?:"
    r"(?:what|which)\s+(?:(?:else|kind|sort)\s+)*(?:can|could|should|may|shall|would)\s+(?:i|we)\s+"
    r"(?:take|use|have)\b"
    r"|(?:is\s+there\s+)?(?:anything|something)\s+(?:else\s+)?(?:that\s+)?(?:i|we)\s+"
    r"(?:can|could|should|may)\s+(?:take|use|have)\b"
    r"|(?:what|which)\s+is\s+(?:safe|ok|okay|best)\s+to\s+(?:take|use)\b"
    r")"
    r"(?:\s+for\s+(?:it|this|that|them|those|the pain|the ache|the soreness|the hurt|"
    r"any of it|any of that|any of those|the same))?"
    r"[\s!.,?]*$", re.I)

# A trip above the line is the one thread where "what can i take" is a packing question, and the
# composer's packing answer is the right one.
TRIP = re.compile(r"\b(?:flight|flights|flying|plane|airport|holiday|holidays|trip|travel|"
                  r"abroad|away|luggage|suitcase|bag|bags|hand luggage|carry on|packing|packed|"
                  r"passport|camping|campsite|hotel|ferry|cruise)\b", re.I)

# The person in the line: a subject is something that happened to them, not a fact about a house.
THEIRS = re.compile(r"\b(?:i|im|i'm|ive|i've|id|i'd|my|me|we|we're|weve|our|us)\b", re.I)

# A word that names no thing to take. The forms the keywords keep ("hurt", "feel") are here so a
# verb is not turned into a subject: "my knee hurts" asks about the knee, never about the hurting.
NOT_A_THING = frozenset("""
ache aching bad badly better bit constantly really still sore tender terrible awful worse worst
keep keeps keeping get gets getting got gotten feel feels feeling felt hurt hurts hurting kill
kills killing make makes making made go goes going gone come comes coming give gives giving put
wont wont sleep sleeping woke wake waking too very lot lots much many every always sometimes
again anymore either though bother bothering last night morning evening day days week weeks
month months hour hours while since thing things stuff
""".split())

# A verb form is not a thing either, and its base is what the entries are keyed on: "im coughing"
# asks about a cough.
A_FORM_OF_A_VERB = re.compile(r"^(?:[a-z]{3,})(?:ing|ed)$")

# What the knowledge base answers in its own words. The first is the ask a person makes, the
# second is the one the entries for a part of the body are keyed on ("back pain", "knee pain").
FORMULAS = ("what can i take for %s", "what can i take for %s pain")

# Asked when the subject's own entry is the answer already on the screen: the person is in pain and
# wants the thing to take, which is the one question the entry for the part of the body does not
# answer.
PAINKILLER_ASKS = ("what painkiller can i take",)

# The pain the person is in, said in the way people say it. Where the entry for the subject has
# already been read out, the question "what can i take" is asking what to take for the pain, not
# how to look after the thing for the third time.
IN_PAIN = re.compile(r"\b(?:pain|pains|ache|aches|aching|achy|hurts?|hurting|sore|throbbing|"
                     r"killing|agony|stinging|burning|tender)\b", re.I)

# The two situations a medicine card answers for at once, and the chat that says which one it is.
# "In pregnancy, paracetamol ... While breastfeeding, paracetamol and ibuprofen are both fine" is
# one card covering both, and a chat that said it is pregnant has no business being told what is
# fine while feeding: read out of the card a turn later, that sentence is advice for someone else.
FEEDING = re.compile(r"\b(?:breastfeeding|breast feeding|breastfeed|nursing|expressing|pumping)\b",
                     re.I)
PREGNANT = re.compile(r"\b(?:pregnan\w*|expecting|trimester|weeks gone|weeks along|midwife)\b",
                      re.I)
A_SENTENCE = re.compile(r"[^.!?]+(?:[.!?]+|$)")

# A reply long enough to be a card rather than a framed repeat, a hedge or a greeting: under this
# the person has been told nothing to go on, and the card is worth the turn whatever the composer
# would have said instead of it.
A_CARD_IS_LONG = 120

# How many subjects in the chat are tried, newest first, and how many words of each.
THE_SUBJECTS_A_CHAT_HAS = 2
THE_WORDS_A_SUBJECT_HAS = 2
# Reading an entry is not free, and a line that reaches nothing would pay for every try: the ask
# is made at most this many times before the line is passed on with the reply it had.
THE_ASKS_A_LINE_MAKES = 3


def _flat(text):
    return " ".join(str(text or "").split())


def _asks_what_to_take(text):
    """True when the line is the bare ask and names nothing to take or to take it for."""
    said = FILLER.sub("", _flat(text).lower()).strip()
    if not said or not NOTHING_NAMED.match(said):
        return False
    return True


def _complaint_words():
    """The words that make a line a complaint, taken from the health knowledge where it has them.

    A bare "what can i take" is a question about a body only where something is wrong with it:
    "im getting the train to manchester" and "im off to my brothers tonight" are conversations
    where the packing list is the right answer, and this is the test that keeps them.
    """
    words = set()
    try:
        from ..knowledge import body  # noqa: PLC0415 - the knowledge base, read for its words
        # The words for something wrong ("killing me", "sore", "swollen") and the parts it is in.
        # Not `body.AVOID`: that list is about a complaint in someone else's body ("my son",
        # "his back"), which is the one thing this must not answer.
        words.update(body.HURT)
        words.update(body._SORE_ANYWHERE)
    except Exception:  # noqa: BLE001 - the knowledge base is read for its words and nothing else
        pass
    # The complaints people name rather than describe. The health knowledge keys its cards on
    # these and no shape in a sentence marks them: "i keep getting heartburn" says nothing hurts.
    words.update("""
        heartburn indigestion reflux nausea migraine headache toothache earache backache stomachache
        cough coughing cold flu covid temperature fever cystitis thrush hayfever rash hives eczema
        psoriasis dandruff ulcer blister sunburn burn sprain cramp cramping constipation diarrhoea
        diarrea sick vomiting warts verruca sciatica gout arthritis ibs period swollen swelling
        infected infection throat tooth teeth gum gums ear ears stomach tummy belly chest queasy
        nauseous vomit vomiting dizzy faint fainted bleeding rash pregnancy pregnant
        """.split())
    return frozenset(word for word in words if word)


COMPLAINT = None
NOT_THEIRS = None


def _someone_else():
    """The words that make a complaint someone else's ("my son", "his back")."""
    try:
        from ..knowledge import body  # noqa: PLC0415
        phrases = sorted(body.THIRD_PARTY, key=len, reverse=True)
        return re.compile(r"\b(?:" + "|".join(re.escape(phrase) for phrase in phrases) + r")\b",
                          re.I)
    except Exception:  # noqa: BLE001
        return None


def _a_complaint(subject):
    """True when the person's own line says something is wrong with them."""
    global COMPLAINT, NOT_THEIRS
    if COMPLAINT is None:
        COMPLAINT = re.compile(
            r"\b(?:" + "|".join(re.escape(word) for word in
                               sorted(_complaint_words(), key=len, reverse=True)) + r")\b", re.I)
        NOT_THEIRS = _someone_else()
    said = _flat(subject)
    if NOT_THEIRS is not None and NOT_THEIRS.search(said):
        return False  # a cough in their son is not a cough in them
    return bool(COMPLAINT.search(said))


def _subjects(memory):
    """The things the chat has been on, newest first, as the person's own lines."""
    if not isinstance(memory, dict):
        return []
    seen, out = [], []
    record = memory.get("topic")
    if isinstance(record, dict):
        seen.append(record)
    others = memory.get("topics")
    if isinstance(others, list):
        seen.extend(other for other in reversed(others) if isinstance(other, dict))
    for other in seen:
        said = _flat(other.get("text"))
        if said and said not in out:
            out.append(said)
    return out[:THE_SUBJECTS_A_CHAT_HAS]


def _the_things_to_take_for(subject):
    """The words of the person's line that name something to take something for."""
    words = []
    for word in topics.keywords(subject):
        if len(word) < 3 or word in NOT_A_THING or not re.match(r"^[a-z]+$", word):
            continue
        if A_FORM_OF_A_VERB.match(word):
            # "coughing" is a cough: the base is what the entry is keyed on, and "running" is a
            # run rather than a "runn".
            word = word[:-3] if word.endswith("ing") else word[:-2]
            if len(word) > 3 and word[-1] == word[-2]:
                word = word[:-1]
            if len(word) < 3 or word in NOT_A_THING:
                continue
        if word not in words:
            words.append(word)
    return words[:THE_WORDS_A_SUBJECT_HAS]


def _a_trip_above(memory, text):
    """True when the chat is about going somewhere, where the packing answer is the right one."""
    if TRIP.search(_flat(text)):
        return True
    if not isinstance(memory, dict):
        return False
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    return any(TRIP.search(_flat(turn.get("user"))) for turn in turns[-2:])


def _the_answer(text, memory):
    """What the knowledge base says to this line, asked on its own."""
    from ..modules import answers  # noqa: PLC0415 - answers imports this package

    fresh = {"turns": [], "aside": True}
    for key in ("user", "others", "facts_log"):
        if key in memory:
            fresh[key] = memory[key]
    try:
        return answers.respond(text, fresh) or ""
    except Exception:  # noqa: BLE001 - a reader that fails leaves the reply as it was
        return ""


def _the_said_in_the_chat(memory):
    """Every line the person has typed in this chat, as one string."""
    if not isinstance(memory, dict):
        return ""
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    return " ".join(_flat(turn.get("user")) for turn in turns)


def _the_last_reply(memory):
    if not isinstance(memory, dict):
        return ""
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    return _flat(turns[-1].get("bot")) if turns else ""


def _the_situation_this_chat_is_in(reply, memory):
    """The card, cut to the situation the person is actually in.

    Only one cut is made, and only where the chat has said it: a card that answers for pregnancy
    and for feeding is read by a pregnant person as the pregnancy part. Nothing is added and
    nothing is reworded - a sentence about another situation is left out.
    """
    said = _the_said_in_the_chat(memory)
    if FEEDING.search(said) or not PREGNANT.search(said) or not FEEDING.search(reply):
        return reply
    kept = [sentence for sentence in A_SENTENCE.findall(reply) if not FEEDING.search(sentence)]
    if not kept or len(kept) == len(A_SENTENCE.findall(reply)):
        return reply
    return " ".join(" ".join(kept).split())


def _the_answer_today(text, memory):
    """The answer the knowledge base gives this line in this chat, as the line stands."""
    from ..modules import answers  # noqa: PLC0415 - answers imports this package

    try:
        return answers.respond(text, dict(memory) if isinstance(memory, dict) else {}) or ""
    except Exception:  # noqa: BLE001 - a reader that fails leaves the reply as it was
        return ""


def _the_same_answer(reply, text, memory, today):
    """True when the knowledge base answers the line as asked with these same words.

    The bare ask reaches an answer of its own, and where that answer is the one this module found
    there is nothing to add: the reply the person gets is the one they were going to get, and a
    module that takes the turn to say the same thing only makes the comparison harder to read.
    `today` is a one-line cache for the turn, so the knowledge base is asked about the line once.
    The answer on its own is not the answer the person gets, though: the composer frames a repeat
    and cuts it ("From just now: ... take paracetamol or ibuprofen if you."), and where the last
    turn was one of those short framed lines the whole card is the better reply and this module
    is where it comes from. So a short line above the ask never counts as already answered.
    """
    if not today:
        today.append(_the_answer_today(text, memory))
    return _flat(today[0]) == _flat(reply) and len(_the_last_reply(memory)) >= A_CARD_IS_LONG


def _names(reply, word):
    """True when the answer says the word back, a plural or a form of it counting."""
    said = _flat(reply).lower()
    if not said:
        return False
    for other in re.findall(r"[a-z']+", said):
        if other == word or topics.alike(other, word):
            return True
    return False


def _the_answer_above(reply, memory):
    """True when this is the answer the person has just read, in its own opening words.

    Only the turn before counts: an entry that said the same thing four turns back is saying it to
    a different question now, and the chat has moved since.
    """
    if not isinstance(memory, dict):
        return False
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    if not turns:
        return False
    opening = " ".join(_flat(reply).lower().split()[:10])
    if not opening:
        return False
    return opening in _flat(turns[-1].get("bot")).lower()


def _the_subjects_to_answer(memory, text):
    """The things in the chat it is worth answering a bare ask about, newest first.

    A subject is worth answering when it is the person's own line, when it says something is
    wrong with them, and when a word of it can be put into the question; everything else - a
    house, a boiler, a train, a picnic, a question - is not something to take anything for.
    """
    out = []
    for subject in _subjects(memory):
        if not THEIRS.search(subject) or "?" in subject:
            continue
        if not _a_complaint(subject):
            continue
        words = _the_things_to_take_for(subject)
        if words:
            out.append((subject, words))
    return out


def the_ask_and_the_subject(text, memory):
    """True when the line is the bare ask and the chat has something to answer it about.

    Read by the arbiter as the module's claim (`TAKES_AS_IT_COMES`), so it asks no entry: the
    reading of the chat is cheap, and the answer is not written until the turn is this module's.
    """
    try:
        if not _asks_what_to_take(text):
            return False
        if _a_trip_above(memory, text):
            return False
        return bool(_the_subjects_to_answer(memory, text))
    except Exception:  # noqa: BLE001 - a reading that fails claims nothing
        return False


def reply_for(text, memory):
    """The answer to a bare "what can i take", about the thing the chat is on, or ""."""
    if not _asks_what_to_take(text):
        return ""
    if _a_trip_above(memory, text):
        return ""
    asked = 0
    today = []
    # An entry that answers the ask with the paragraph already on the screen is worth keeping in
    # hand, but only as the last word: a fresh answer about the same subject is the better reply,
    # and where there is none the repeat beats the card the words alone reached - "my back is
    # killing me" / "what can i take" was answered with the duty-free allowance.
    already = ""
    in_pain = ""
    for subject in _subjects(memory):
        if not THEIRS.search(subject) or "?" in subject:
            continue  # a house, a boiler or a question is not something to take anything for
        if not _a_complaint(subject):
            continue  # a train, a picnic or a brother is not something to take anything for
        for word in _the_things_to_take_for(subject):
            for formula in FORMULAS:
                if asked >= THE_ASKS_A_LINE_MAKES:
                    return ""
                asked += 1
                reply = _the_answer(formula % word, memory)
                if not reply or not _names(reply, word):
                    continue
                if _the_answer_above(reply, memory):
                    if not already:
                        already = reply
                        in_pain = subject
                    continue
                if _the_same_answer(reply, text, memory, today):
                    continue  # the line gets this answer on its own: nothing is added by taking it
                return _the_situation_this_chat_is_in(reply, memory)
    if in_pain and IN_PAIN.search(in_pain):
        # The card for the subject is the paragraph they have just read, and what they are asking
        # is what to take for the pain. Nothing here is invented: the same question is put to the
        # knowledge base, which has the dose and the ceiling for it.
        reply = _the_answer(PAINKILLER_ASKS[0], memory)
        if (reply and not _the_answer_above(reply, memory)
                and not _the_same_answer(reply, text, memory, today)):
            return reply
    if already and _the_same_answer(already, text, memory, today):
        return ""
    return already
