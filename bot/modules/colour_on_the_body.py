"""A colour on a part of the person's own body is answered, not filed.

"my back is red", "my neck is blotchy", "my face has gone bright red" fell to the floor - "Got it.
Is there anything you'd like a hand with?" - and "my ears went red" reached the laundry card,
because the -ed catch-all read "red" as a past tense. The person is showing you something, and what
a patch like that usually is plus one question about it is a better reply than either.

`bot/compose/colour_on_the_body.py` holds the reading and the wording. The band sits above the
small-talk pool and the floor and below the modules that know a subject: this is a shape and two
sentences, not knowledge. `respond` returns None on every line the reading cannot stand behind, so
another reader or the fallback keeps the turn.
"""
from ..compose import colour_on_the_body

# Above `chat` (300), whose -ed catch-all read "my arm is red" as a past tense and whose small-talk
# pool asked "What kind of part do you usually go for?" of a colour. Below everything that knows a
# subject: safety (9000), the loss and grief modules (2,000-2,100) and the knowledge-base modules
# that sit over it (`figure_asked_again` 1000, `my_work` 1150, `aboutachild` 1100).
PRIORITY = 350


def respond(text, memory):
    """The answer to a colour on the person's own body or a blush, or None."""
    try:
        return colour_on_the_body.reply_for(text, memory) or None
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return None
