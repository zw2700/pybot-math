"""The two ends of one night, when the chat gives them one line at a time.

A night is told in pieces, and only the first piece has a bedtime in it:

    i feel knackered all the time   ->  the constant-tiredness card
    i go to bed at about 11         ->  "11pm is a good bedtime - eight hours before a seven
                                        o'clock start"
    and wake at 6                   ->  "Waking at the same time every night is common and it
                                        passes" (advice for somebody who cannot stay asleep)

The last line was read on its own, so the person who had just said their night is eleven to six
was given the wrong leaflet. `bot/memory/asleep.py` holds the reading: the bedtime, the alarm, the
hours between them, and the seven to nine most adults need. This module is the turn it is asked
on, and it answers nothing else - `answer_for` returns None for every line that does not give a
night, so the chatter band and the knowledge entries keep every other turn.

A sleep that names the thing it depends on - "i cant fall asleep without the telly on", "i need
the fan on to get to sleep" - is the same night told by its aid. `bot/knowledge/sleep_aids.py`
holds those rows, and this module answers them here before `chat` can read the line as a bad week.

Above `chat` (300), which owns the night-waking pool this line used to fall into, and below the
memory store and the safety bands, whose turns these are not.
"""
from ..knowledge import sleep_aids
from ..memory import asleep

PRIORITY = 1100


def respond(text, memory):
    """The hours between the two ends of the night they described, or None."""
    if not isinstance(memory, dict):
        return None
    # A sleep that names the telly, the fan or the lamp is a question about that thing, and
    # the chat module's bad-week pool must not take it. The row stands above `chat` (300), as
    # this module always has, and answers nothing else.
    aid = sleep_aids.answer_for(text, memory)
    if aid:
        return aid
    return asleep.answer_for(text, memory) or None
