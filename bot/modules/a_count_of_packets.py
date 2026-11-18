"""A count of packets is the poisons card, not a nod and not the tablet card.

The reading is in `bot/compose/a_count_of_packets.py`; this module is here so the shape has a band
of its own. It asks for nothing safety already answers: `is_a_dose` reads only a count of
containers, which no arm of the poisons case in `safety.py` reads, and the card it hands back is
safety's own pool and safety's own note, so a follow-up ("is he going to be alright") lands in the
same conversation.

The band is the safety one (9000), because this is an emergency card and nothing below that band
survives the arbiter's passing-over rules - at 8900 the tablet-taking card still won the turn. A
card safety already has is never displaced: `safety.respond` is asked first, and a line it answers
is left to it.
"""
from ..compose import pick
from ..compose.a_count_of_packets import is_a_dose
from ..knowledge.crisis_replies import REPLIES
from . import safety, urgent

PRIORITY = 9000  # the safety band: an emergency is never outvoted


def respond(text, memory):
    """The poisons card for a count of packets, or None for every other line."""
    if not is_a_dose(text):
        return None
    # Safety's own reading comes first: every arm it has is better than this one, and a count it
    # already reads - "i took a whole packet", "i took 20 paracetamol" - is its turn. `urgent` is
    # asked as well, because a child who has swallowed a packet is its card and not this one.
    if safety.respond(text, memory) or urgent.respond(text, memory):
        return None
    if isinstance(memory, dict):
        memory["safety_case"] = "poison"
        memory["safety_safe"] = False
    return safety._fit(pick(REPLIES["poison"], memory), text, "poison")
