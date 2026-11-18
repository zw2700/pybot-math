"""A question about somebody's care is the ward's, not a search (bot/compose/ward.py).

"How long will she be in hospital", "when can she come home", "what ward is she on", "is he
allowed visitors" all reach the composer's search hedge, and no search settles any of them: the
stay, the discharge, the ward, the theatre list and the results are in that person's notes, and
the people holding the notes are the ones looking after them. Each reply says plainly that
nothing here can see the notes, then names the ward and the one thing to do - ring and ask for
the nurse looking after them. Nothing is guessed: no number of days, no ward name, no visiting
hour. The reading itself is in `bot/compose/ward.py`; this module is only where it is asked from.

`PRIORITY = -985` puts it above the composer's own fallback (-1000) and below every real answer,
so a knowledge card keeps every line it already answers. It is also above the verdict reader
(`a_verdict`, -990): a care question beats a question about how to word something.
"""
from ..compose import ward

PRIORITY = -985

def respond(text, memory):
    return ward.answer_for(text, memory)
