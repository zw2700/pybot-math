"""Somebody else's habit, said out loud, gets the sentence to raise it with.

"My brother keeps asking me for money", "my son keeps leaving his shoes in the hall", "my mate
never invites me to anything", "the kids keep leaving their toys everywhere": each of these
reached a line that fits any message - "Got it. Is there anything you'd like a hand with?", "I'm
listening - say more if it helps.", "Noted: your brother keeps asking for money". The composer
has a pool for the same shape (GRIEVANCE), but it keys on the verb, so the two commonest ways
people say it - an imposition ("asks me for money", "uses my toothbrush", "leaves her dishes in
the sink") and a neglect ("never invites me", "never thanks me", "never notices") - are not in
its list.

The one help a fallback can honestly give here is the sentence to raise it with: the bot cannot
see the brother or the hall, and a question back ("what would you like to do about it") leaves
the person holding the whole of it. bot/compose/habit.py reads the shape and holds the words.

Three kinds of placeholder are replaced and nothing else - the pools that mean "I cannot answer"
(`fallback._is_a_hedge`), the neutral lines that fit any message, and a receipt (the person's own
sentence handed back with nothing added). A line any entry or module answered never gets here:
this sits at PRIORITY -999, above the greeting band and below every module that knows the
subject, so a knowledge card, the small talk, or a safety line keeps its turn.
"""
from ..compose import fallback, habit
from ..memory import ack

PRIORITY = -999


def respond(text, memory):
    """The sentence to raise it with, or None when this is not that shape."""
    raised = habit.answer_for(text, memory)
    if not raised:
        return None
    said = fallback.reply_for(text, memory)
    if not said:
        return None
    if not (fallback._is_a_hedge(said)
            or fallback._in_a_pool(said, (fallback.NEUTRAL,))
            or ack.reads_as_a_receipt(said)):
        # Something with an answer of its own is already speaking for this line, and the words
        # to raise a habit with are not it.
        return None
    return raised
