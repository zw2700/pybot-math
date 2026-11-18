"""The order in an answer, asked for again: "what next", "and then", "what now".

An answer that gives its steps in order - "turn the water off at the valve, take the handle off, and
take the old part to a shop to match it" - has an order in it, and the person working through it
asks "what next" after each one. `bot/memory/plan.py` keeps that order and the step the chat has
reached; this module is the turn that hands the next one over.

It runs at PRIORITY 7100, just above the memory store (7000), because the store answers these lines
out of the answer it has in hand: "what next" after the washing-machine answer came back as "The bit
of that answer worth doing first: Leaving the door and drawer open between washes ...", a sentence
from the end of it handed over as if it were the beginning. Nothing else moves: the line is read the
same way every turn, and a line that is not an ask for the next step leaves this module returning
None.
"""
from bot.memory import plan

PRIORITY = 7100


def respond(text, memory):
    if not isinstance(memory, dict):
        return None
    return plan.carry_on(text, memory)
