"""A near-me ask with the thing left out is answered with the thing put back in.

"Is there one close by" after "im looking for a launderette" fell to the search hedge, although
the named form of the same question - "is there a launderette near me" - has an answer: there is no
local list here, a map app shows what is close, a phone call settles the rest. The pronoun is the
thing the person said a turn ago, so the answer is the named answer with their own word in it.

`bot/compose/nearby_one.py` holds the reading and the wording. The band sits just above the
fallback, because this is a pointer and a shape, not knowledge: any module that knows something
about the thing keeps the turn, and so does every module above -1000. Nothing else is claimed:
`respond` returns None on a named ask, on a line whose thread named no thing, and on a cold line.
"""
from ..compose import nearby_one

# Over the fallback's own pointer (-1000) and under everything else that answers: the pools that
# name a place (bulky, shopping) and the modules that know the subject all keep their turns.
PRIORITY = -995


def respond(text, memory):
    """The map-app answer to a pronoun near-me ask, or None."""
    try:
        return nearby_one.reply_for(text, memory) or None
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return None
