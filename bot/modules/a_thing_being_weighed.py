"""A statement that names something the person is deciding gets help, not a receipt.

"im looking at an electric blanket for the winter", "we are looking at a venue for the wedding",
"its for a warehouse supervisor role": nobody asked a question, so nothing is looked up, and the
seed fallback answers with one of its three receipts - "Got it. Is there anything you'd like a
hand with?". That is the right answer to "the dog did a funny thing today" and the wrong answer to
somebody standing in front of a decision: they have said which decision, and the bot has said
nothing about it.

The reply is built in `bot/compose/a_thing_being_weighed.py`: the kind of decision is read off the
words, the thing is said back in the words the person used, and the two or three things that settle
that kind of decision come with the one question a friend would ask next. Nothing is looked up and
no price, model or date is named, so no line here can go stale.

Why this is a module of its own rather than one more reader inside the seed fallback: a reader
added to `bot/modules/greeting.py` has to be inserted at the end of a chain other lanes add to
every few minutes, so it cannot be landed without a rebase, and a rebase that re-cuts somebody
else's reader is how a fallback loses a turn it had. As a module it is one new file, and the rule
it needs is the one the chain already has: a receipt answers when nothing else does.

It sits at -999, above the seed fallback (-1000) and beside the other modules that replace one of
its lines (`bulky`, `a_day_somebody_else_keeps`). It asks the seed fallback for the reply it would
give (`greeting.respond`, the same turn the runtime would have run) and answers only where that
reply is one of the three receipts in `fallback_data.NEUTRAL`, so every card, every entry and
every reader's own answer keeps its turn: `looking at a new boiler` is still the boiler-age card's,
`looking at an air fryer` is still the air fryer's.

The reading is narrow on purpose and passes on almost every line: it needs a thing named, the kind
read off the last word of the name, and no reason to think the thing is already theirs
("im thinking of selling my car").
"""
from ..compose import a_thing_being_weighed
# The seed fallback itself, asked for the reply it would give. `talkto` and `judge_ask` ask it the
# same way; nothing here is imported by `greeting`, so the import is safe at load.
from . import greeting

# Above the seed fallback (-1000), where the receipts come from.
PRIORITY = -999


def respond(text, memory):
    # The reading is the cheap half and it passes on almost every line, so it is asked first and
    # the seed fallback is only run for a line this module could answer.
    if not a_thing_being_weighed.pool(text):
        return None
    try:
        reply = greeting.respond(text, memory)
    except Exception:  # noqa: BLE001 - a broken seed keeps its own turn
        return None
    if not isinstance(reply, str) or not reply.strip():
        return None
    return a_thing_being_weighed.answer_for(text, memory, reply)
