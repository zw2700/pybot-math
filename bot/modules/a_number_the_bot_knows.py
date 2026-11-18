"""A person asking for a phone number gets the number this bot already knows, not a search.

"whats the number for the samaritans", "whats the number for 111", "childline number", "how do i
ring acas" - on main every one of those is answered by the same sentence:

    "No directory here, sorry. A map app search for the name shows the address and the number,
     and the place's own page has the hours."

That is the right route for a shop, a surgery or a takeaway, whose number only a directory has.
It is the wrong route for a national line, because the bot already states those numbers in its own
cards (116 123, 0808 2000 247, 0300 123 1100, 111, 988, 999), and somebody in trouble should not
be sent to a map app to find the Samaritans.

Nothing here works out a number or fills one in: the reading in `bot/compose/a_number_the_bot_knows.py`
holds only the lines whose numbers the tree already states, word-bounded so "refuge" does not fire
on "refugees" and "111" not on "1111", and a helpline whose number the tree does not hold gets its
own page named rather than a directory route.

This sits above the greeting band (PRIORITY -1000) and below every knowledge module, the same
rung as `a_day_somebody_else_keeps`, so a card, an entry, `answers` or the safety band keeps the
turn: only a line nothing else answered is answered here. `how do i ring acas` still gets the
answers module's card for that reason, which is the ordering working as it should.
"""
from ..compose import a_number_the_bot_knows as numbers

PRIORITY = -999


def respond(text, memory=None):
    """The number the bot already knows, or None."""
    return numbers.answer_for(text, memory)
