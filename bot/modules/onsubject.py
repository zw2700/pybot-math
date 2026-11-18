"""A short follow-up names the thing the chat is on, not a search.

"can he do that" after a rent rise, "do i need an adapter there" after a holiday in Spain, "will
they cut me off" after an electric bill: the line names nothing of its own, so no entry is reached
and the seed fallback answers it with the search hedge, as if the bot had not been listening. The
person said what they are talking about one line before, so a friend says it back and says who
settles it. That reply is built in `bot/compose/onsubject.py`.

Why this is a module of its own rather than one more reader inside the seed fallback: a reader
added to `bot/modules/greeting.py` has to be inserted at the end of a chain that other lanes add to
every few minutes, so it cannot be landed without a rebase, and a rebase that re-cuts somebody
else's reader is how a fallback loses a turn it had. As a module it is one new file, and the only
rule it needs is the one the chain already has: a fallback answers when nothing else does.

It sits at -998, above the seed fallback (-1000) and below every fallback-band module that answers
a line by name (`bulky`, -999, is the nearest: one thing being thrown out). It asks the composer
for the reply the seed would give (`fallback.reply_for`, the same call `greeting.respond` makes at
its top) and answers only where that reply is the plain "I don't know" pool - the search hedge,
the shrug, the echo. A hedge that already names who to ask keeps the turn, and so does any real
answer.

The readers the seed runs after that reply is built keep their lines too, because the reading here
is narrower than any of them: a line with no question of its own that names the thing the chat has
just been on (`onsubject.pool`). An answer still on the person's screen, a judgement put to the
bot about their own people, a thing they want to find, and a thing of theirs damaged or refused
are all questions or statements about something else, and this passes them by. What is left is the
line that reaches the search hedge with nothing said back, which is this module's turn.
"""
from ..compose import fallback
from ..compose import onsubject

# Above the seed fallback (-1000) and below `bulky` (-999), which answers one thing by name.
PRIORITY = -998


def respond(text, memory):
    # The reading is the cheap half and it passes on almost every line, so it is asked first and
    # the composer is only run for a line this module could answer.
    reading = onsubject.pool(text, memory=memory)
    if not reading:
        # A there-ask about the place the chat named needs no subject of its own: "do i need an
        # adapter there" after a trip to Orlando is a question about Orlando.
        reading = onsubject.place_pool(text, memory=memory)
    if not reading:
        return None
    try:
        reply = fallback.reply_for(text, memory)
    except Exception:  # noqa: BLE001 - a broken composer keeps its own turn
        return None
    if not isinstance(reply, str) or not fallback._in_a_pool(reply, (fallback.UNKNOWN,)):
        return None
    return reading
