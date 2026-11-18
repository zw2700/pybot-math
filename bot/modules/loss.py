"""A death is never small talk, and never a topic a gift entry can win.

"My dad died in march" used to get "Got it.", and "some days i can't get out of bed since my mum
died" got a present-buying answer, because a topic entry matched the word "mum". The reading and
the pools live in `bot/compose/loss.py`: plain sympathy for the user's own loss, what to say to
the person who had the loss, words for a condolence card, a normalising answer to a question
about grief, and company for a short follow-up ("it was really hard").

This module is the speaker for those lines, so it says what it answers in two ways:

* `ANSWERS = ("loss", "grief")` — the topics, like every other module;
* `ANSWERS_INSTEAD = ("loss", "grief")` — it answers *in place of* the topic entries. A topic
  entry matches a word or a topic id of the line ("mum", "cat", "card"), so on a bereavement
  line it answers a different question; the arbiter lets a declaring module answer instead, and
  the safety band still comes first;
* `DEFERS_TO = loss.acknowledges` — it stands back when another candidate's reply already
  acknowledges the death and knows something more about it.

It proposes only a line it is sure of, so a false reading would take a turn — that is why the
read demands a person or a pet behind the death word (bot/compose/loss.py).
"""
from ..compose import fit, loss, pick
from ..understanding import understand

PRIORITY = 2000  # 1000-3999: a general helpful module, above small talk and the fallback
ANSWERS = ("loss", "grief")
ANSWERS_INSTEAD = ("loss", "grief")
# An entry that already says the sad thing itself answers a death better than a generic
# sympathy does: the pets entry knows about cremation, home burial and a paw print. So a reply
# that acknowledges the loss keeps the turn, and this module stands back (`arbiter._defers`).
# It stands back only on a practical line: "my cat died and i keep crying" is about the person
# in front of us, and the entry's card is the colder answer there.
def defers_to(reply, line):
    """True when the entry's reply should keep the turn.

    Five things have to hold: the entry says the sad thing itself, the death in the line is a
    pet's ("my aunt died and her dog needs a home" is not the pets entry's line), the line asks
    what to do rather than how the person feels ("my cat died and i keep crying"), something is
    asked at all ("my dog died" on its own is a person who needs to be met, not a request for the
    cremation card), and the ask is one the entry answers ("can we bury him at home", not "when
    should i get another one"). The last two are separate because a line can ask for a decision
    the card has no answer to, and a hamster does not get a paw print for "is it my fault".
    """
    if (loss.acknowledges(reply) and loss.a_pet_died(line)
            and not loss.names_a_feeling(line)
            and loss.asks_for_a_decision(line)
            and loss.asks_about_the_remains(line)):
        return True
    # A death line carries its paperwork in the same breath as the death: "my mum died, is the
    # cremation expensive", "my husband passed away last month and i dont know where to start with
    # probate". The condolence answers the death and leaves the question, so an entry that answers
    # that question keeps the turn. Three things have to hold: the line names the administration
    # rather than the person's feelings, the entry's reply gives the kind of answer the line asked
    # for (a figure for a price, steps for "where do i start") - the composer's own fit check, so
    # this reads no phrasing of its own - and the reply is about that same piece of paperwork, not
    # a right-shaped card on the next topic over (bot/compose/loss.py, `is_about_the_paperwork`).
    if not loss.asks_the_administration(line) or loss.names_a_feeling(line):
        return False
    if not loss.is_about_the_paperwork(reply, line):
        return False
    want = fit.wants(understand(line))
    return bool(want and fit.gives(reply, want, line))


DEFERS_TO = defers_to


def respond(text, memory):
    """The reply a death asks for, or None when this is an ordinary line.

    A follow-up ("it was really hard", "what do i even say to him") is read the same way while
    the bot's own last replies were about the loss; a change of subject ends it.
    """
    understood = _reading(text, memory)
    if understood.get("about_bot"):
        # "do you miss me", "what do you think of me": asked inside a bereavement thread it is
        # still a line about the bot, and the bot's own answer is the one that fits - the thread
        # answered it with "that sounds heavy to be carrying", which is about the wrong person.
        return None
    clean = understood.get("clean")
    words = understood.get("words")
    if not isinstance(words, list):
        words = None
    options = _options(text, memory, clean, understood, words)
    if not options:
        return None
    reply = pick(options, memory, text)
    _the_missing_said(memory, reply)
    return reply


def _the_missing_said(memory, reply):
    """Note that the missing was met, for the turn after it (bot/memory/ack.py).

    Written where the reply is chosen, so it lands in this module's copy of the memory: the
    arbiter keeps the copy of the module whose reply the person got, and a note made by a module
    that lost is thrown away with its copy. Without it the line after "i miss my mum" ("sorry i
    meant my nan") lost the reason a friend answers it warmly - the engine reads the missing as
    news, so bot/memory/ack.py's `_after_a_feeling` was the only thing that could tell, and the
    note bot/modules/chat.py writes for its own heavy pools never landed.
    """
    if not isinstance(memory, dict) or reply not in loss.MISS_REPLIES:
        return
    turns = memory.get("turns")
    memory["heavy_reply"] = {"feeling": "missing",
                             "turn": len(turns) if isinstance(turns, list) else 0}


def _reading(text, memory):
    """The understanding engine's reading of *this* line.

    `memory["understood"]` is written by the observer before the modules run, so it is this
    line; a module called on its own (a test, another module) may be handed a memory that is
    still on the line before, so the reading is taken again when it does not match.
    """
    stored = memory.get("understood")
    if isinstance(stored, dict) and _same(stored.get("clean"), text):
        return stored
    try:
        read = understand(text, memory)
    except Exception:  # noqa: BLE001 - a reading that fails leaves the pools to the words
        return {}
    return read if isinstance(read, dict) else {}


def _same(stored, text):
    """True when the stored reading is of this line (the words, not the punctuation)."""
    if not isinstance(stored, str) or not stored.strip():
        return False
    return " ".join(loss.words_of(stored)) == " ".join(loss.words_of(text))


def _options(text, memory, clean, understood, words):
    try:
        if words is None:
            words = loss.words_of(text)
        return loss.reply_for(text, memory, clean, understood.get("topics"), _mood(words))
    except Exception:  # noqa: BLE001 - a reading that fails just passes the line on
        return None


def _mood(words):
    """'negative' for a hard follow-up ("it was awful"), so it gets company, not a stock ack."""
    try:
        cues = _cues()
        if set(words) & cues:
            return "negative"
    except Exception:  # noqa: BLE001
        pass
    return None


def _cues():
    from ..compose.fallback import NEGATIVE_CUES  # the composer's one list of hard words
    return NEGATIVE_CUES
