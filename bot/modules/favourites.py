"""A favourite the person names, and the ask for it a turn later.

A favourite is a fact about the person and nothing in the knowledge base knows it: "my favourite
food is curry" was kept as a taste (and became a dish), "my favourite band is blur" reached the
entry for "band" as an object, "what is my favourite genre" reached the entry for genes, and
"what is my favourite colour" the paint card. The slot and its wording are in
`bot/memory/favourite.py`; this module is the store's face for them.

`observe` keeps one: a colour, a film, a food, a team, a genre, whatever they name, plus the
change said out loud ("i prefer blue now") and the correction ("no wait its blade runner").
`respond` says it back - the receipt for the line that said it, the one thing they named for the
ask - and leaves the turn alone whenever something better answers it: a line that states a
favourite and asks something else in the same breath, and a favourite of a thing the knowledge
base has an entry for, which is answered about the thing rather than as a receipt.

The whole of it is in one module on purpose: a favourite is nobody else's business, and the store
is a big file every lane edits.
"""
from ..compose import pick
from ..knowledge import lookup
from ..memory import favourite
from ..memory.taste import read_all as read_tastes

# The recall band (`bot/modules/arbiter.py`, RECALL = 7000): a favourite is what the person said
# about themselves, the same kind of claim `memory_store` makes about a name, a job or a plan, and
# it is a lead the turn in the same way. A favourite is a whole line of its own - no pool, no
# entry - so nothing below this band has a better claim on the line it answers.
PRIORITY = 7000


def observe(text, memory):
    """Keep the favourite a line names, corrects or changes (bot/memory/favourite.py)."""
    try:
        favourite.watch(text, memory)
    except Exception:  # noqa: BLE001 - an observer must never lose a turn
        return


def TAKES_AS_IT_COMES(text, memory=None):
    """Whether this line is one this module answers as it comes (bot/modules/arbiter.py).

    The arbiter settles a specialist against a generalist by the topic the line fits, and the ask
    for a favourite fits one: "what is my favourite genre" is read as an opinions line, so the
    entry that owns novels and television was given the turn over the one thing the person had
    already said ("A gene is a section of DNA...", for a favourite thing they had named a line
    earlier). A favourite is what the person said about themselves, the same claim `memory_store`
    makes for a name or a plan, and it is answered as it comes for the same reason.

    Asked on a shallow copy of memory, because answering pops the flags the reply was marked
    with - the live memory is the store's to write, not this hook's.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return False
    try:
        return _said_back(text, dict(memory)) is not None
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


def respond(text, memory):
    """Say the favourite back, or leave the turn to whoever answers the line better."""
    try:
        return _said_back(text, memory)
    except Exception:  # noqa: BLE001 - a module must never lose a turn
        return None


def _said_back(text, memory):
    """The favourite a line names or asks for, said back (bot/memory/favourite.py).

    "my favourite food is curry" is a fact about the person and nothing in the knowledge base
    knows it, so the store keeps it. The ask comes back as the one thing they named - "Your
    favourite colour is green." - because the reply that repeated the last paragraph ("Same as
    before: White or cream lets green breathe...") answers a question they did not ask. A thing
    they have never said a favourite of is left to the other modules rather than denied.
    """
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    told = memory.pop("favourite_told", None) if isinstance(memory, dict) else None
    changed = memory.pop("favourite_changed", None) if isinstance(memory, dict) else None
    if favourite.asks_something_too(text):
        # "my favourite genre is comedy, what should i watch" is a fact and a request in one
        # line. The fact is kept above, but the line is answered by whatever answers the
        # question - the store saying the fact back ("Comedy for your favourite genre, then -
        # noted.") leaves the person with no suggestion and reads as not listening.
        return None
    if isinstance(changed, dict) and changed.get("thing"):
        shown = favourite.their_words(changed.get("value"))
        shown = shown[:1].upper() + shown[1:]
        if changed.get("was"):
            return pick([shown + " now, then \u2014 I have your favourite " + str(changed["thing"])
                         + " as " + favourite.their_words(changed.get("value")) + ".",
                         "Changed: your favourite " + str(changed["thing"]) + " is "
                         + favourite.their_words(changed.get("value")) + " now, not "
                         + favourite.their_words(changed.get("was")) + "."],
                        memory, text)
        return shown + " for your favourite " + str(changed["thing"]) + ", then \u2014 noted."
    if isinstance(told, dict) and told.get("thing"):
        # The answer to the bot's own ask a turn ago ("what is it?" -> "green"): said back as the
        # fact it now is, rather than the listening line a short answer otherwise gets.
        return ("Noted: your favourite " + str(told["thing"]) + " is "
                + favourite.their_words(told.get("value")) + ".")
    if favourite.asks_all(text):
        held = favourite.the_favourites(memory)
        if held:
            last = held[-4:]
            parts = ["your favourite " + str(thing) + " is " + str(value) for thing, value in last]
            if len(parts) == 1:
                said_all = "You have told me one: " + parts[0] + "."
            else:
                said_all = "You have told me " + ", ".join(parts[:-1]) + " and " + parts[-1] + "."
            return pick([said_all,
                         said_all.replace("You have told me ", "Here is what I have: ")], memory, text)
        return None
    asked = favourite.asked(text)
    if asked and not favourite.kept(memory, asked) and read_tastes(memory):
        # A taste the store already holds is the nearest thing it has to a favourite, and the
        # taste list is answered by the line about it ("i love cats" then "what are my favourite
        # foods?" -> "You like cats."). The favourite slot has nothing, and "Your favourite foods
        # hasn't come up yet. What is it?" throws away the one thing the store did keep.
        return None
    if asked:
        value = favourite.kept(memory, asked)
        if not value:
            # Nothing on record: the honest answer is that they have not said, and the thing they
            # named is what the bot then asks for. Kept as the slot it is, so the one-word answer
            # ("green") lands on the same favourite rather than on nothing at all.
            memory["favourite_asked"] = asked
            return pick(["You haven't told me your favourite " + asked + " \u2014 what is it?",
                         "I don't have a favourite " + asked + " for you yet. What is it?",
                         "Your favourite " + asked + " hasn't come up yet. What is it?"],
                        memory, text)
        value = favourite.their_words(value)
        shown = value[:1].upper() + value[1:]
        return pick(["Your favourite " + asked + " is " + value + ".",
                     "You said " + value + " \u2014 that is your favourite " + asked + ".",
                     shown + ", you said. That is your favourite " + asked + "."], memory, text)
    said = favourite.read(text)
    if not said:
        return None
    # A favourite of a thing the knowledge base has an entry for is a line the answers module can
    # answer for itself: "my favourite colour is green" has the colours that go with green in it,
    # and the store's receipt ("Green for your favourite colour, then - noted.") stood in front of
    # that answer. The fact is kept in `_observe` either way; only the claim on the turn is given
    # up, so the turn the person gets is the one about the thing they named.
    if isinstance(memory, dict) and isinstance(memory.get("understood"), dict):
        try:
            if lookup.find(memory["understood"]) is not None:
                return None
        except Exception:
            pass
    value = favourite.their_words(said["value"])
    options = ["Noted: your favourite " + said["thing"] + " is " + value + ".",
               "Favourite " + said["thing"] + ": " + value + ". Got it."]
    if len(value.split()) <= 2 and not value.lower().startswith(("my ", "the ")):
        # "Green for your favourite colour, then - noted." reads as a sentence, and "my mums
        # curry for your favourite food, then - noted." does not: a thing they named with more
        # than a word or two in it keeps the plain form.
        options.append(value[:1].upper() + value[1:] + " for your favourite "
                       + said["thing"] + ", then \u2014 noted.")
    return pick(options, memory, text)
