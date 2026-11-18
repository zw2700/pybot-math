"""A qualifier after a knowledge answer gets the test the answer gave, not a receipt.

    i keep getting heartburn     "An antacid settles most heartburn ... See a GP if it lasts more
                                  than three weeks or you find food sticking on the way down."
    im 34 and not overweight     before: "I'm listening - say more if it helps."
                                  now: "Got it. The test does not turn on that: see a GP if it lasts
                                  more than three weeks or you find food sticking ... That is the
                                  bit that decides it."

The person is not asking anything. They are putting a fact about themselves against what they were
just told, and the reply they get should say which part of it that fact bears on. The answer above
already gave the test, so this reading quotes it and invents nothing (bot/compose/what_decides_it.py
holds the whole reading and the guards).

The band is -998: over the greeting fallback (-1000) where the receipt comes from, under every
module with a real answer for the line. It also reads memory to know it is in that seat: the bot's
own last turn has to have been a knowledge answer (`answers`), so a card, an entry, a question back
or the fallback's own line above means the line is not this reading's.
"""
from ..compose import what_decides_it

PRIORITY = -998


def respond(text, memory):
    """The test the answer above gave, or None on every other line."""
    try:
        return what_decides_it.answer_for(text, memory)
    except Exception:  # noqa: BLE001 - a reading that raises answers nothing
        return None
