"""Somebody they are close to is in a rough patch: answer the person, not the receipt.

The reading and the wording are in `bot/compose/theirperson.py`, which says why the shape is
worth one question back. This is the module that offers it, and the reason it is a module of its
own rather than four lines in the seed fallback: the shape is a *shape*, and a hook in the
fallback would have to grow a branch for the next one too.

PRIORITY 250 puts it above the seed fallback (-1000) and below every module that can answer the
line for itself: `chat` (300) keeps "my mate has been really down lately", `answers` (1100) keeps
"my best friend is struggling with his reading", and `loss` (2000) keeps "my mum is having a hard
time" when the line also says somebody died. What it can lose is a receipt; what it cannot do is
take a turn from a better answer.

It also asks the composer what it would have said, and stands down unless that line was a
placeholder (`bot/compose/theirperson.py`, `may_replace`): a pool line with a feeling in it -
"That sounds rough. If you want, I can help you think through what to do next." - is a reply, and
this module has nothing to add to it. The composer is asked here and again by the fallback, which
is the price of not touching a file every lane edits.
"""
from ..compose import fallback, theirperson

PRIORITY = 250


def respond(text, memory):
    reply = theirperson.reply_for(text, memory)
    if not reply:
        return None
    if not theirperson.may_replace(fallback.reply_for(text, memory), text):
        return None
    return reply
