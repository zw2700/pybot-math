"""Runs the understanding engine (bot/understanding) before any module proposes a reply."""
from ..memory import recall, the_thing_it_is
from ..understanding import understand

PRIORITY = 10000  # observes first, so every other module reads memory["understood"]


def observe(text, memory):
    read = understand(text, memory)
    # A pronoun in a short ask stands for a thing the store already holds: "how often should I
    # walk it" straight after "I have a dog" is the dog entry, and the reading is where every
    # module looks first ("what should I feed it" reached nothing and fell to a search hedge
    # with the cat food one entry away). Only the reading changes: the line as typed is what
    # every fact and every quote is kept from.
    filled = the_thing_it_is(read, memory)
    if filled is None:
        # A bare "should i stop" names the advice and not the thing it is about: the chat is
        # what says which stop it is ("should i stop running" after a sore knee), and read on
        # its own the line asks whether to stop talking. A local import: this file's own import
        # line is shared, and the memory package reads this one back.
        from ..memory.topics import the_advice_ask_with_its_doing  # noqa: PLC0415 - see above
        filled = the_advice_ask_with_its_doing(read, memory)
    memory["understood"] = filled if filled is not None else read
    # "Is there an earlier turn this line points at?" is asked once, here, before any module runs:
    # one cue list and one lookup in bot/memory/recall.py, and the answer is on the reading for
    # every module that replies out of memory. It is None when nothing earlier carries the thing
    # the line names, which is the answer a look-back module needs before it takes the turn.
    memory["understood"]["looks_back"] = recall.the_earlier_turn(text, memory)
