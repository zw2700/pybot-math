"""A doubt on top of "get it looked at" is "was that an overreaction", and it was not.

`bot/compose/verdict` answers "is that bad" over an answer from the knowledge base, and it does
that well. Where it stands aside, chat's acknowledgement pool closes the conversation instead:
after "Get it checked by a GP within two weeks" the person asked "is that bad" and got "Alright
then - good luck with it.", and the same pool answered "is that ok" and "is that enough" with the
same sign-off. The acknowledgement pool is for the end of a topic, and this is not the end of one.

Only the shape this file can answer is here. A doubt on top of an answer that named somebody to
see or somewhere to go ("get it checked", "see your GP", "ring 111", "go to A&E") is asking
whether the call was fussing, and the answer is that it was not: the call is the point of the
answer above. Every other doubt is left to the composer and to chat, because what it is about is
in the answer above and guessing at it from here is how a sentence lands about the wrong thing.

Nothing here names a symptom, a body part, a person or a pronoun, so it cannot say whose it is.
A safety, urgent, grief or loss answer is never read back: after one of those the person has
already been told what to do now, and a line about the call being right is not the next thing.
"""
import re

from . import pick

# The whole line, and only the shapes a person types after an answer they are unsure of. A doubt
# with a subject of its own ("is that bad for the baby", "is my knee normal") is not this
# reading: the subject is in the line, and the knowledge base answers that one.
BARE_DOUBT = re.compile(
    r"^(?:and |so |but |ok |okay |oh |right |hmm )*"
    r"(?:(?:is|was|are|were|does|do|did) (?:that|this|it)(?: all)?"
    r"(?: (?:really|actually|very|too|that|so))?"
    r"(?: (?:bad|normal|serious|dangerous|ok|okay|fine|safe|good|alright|"
    r"a lot|too much|too often|too many|enough|much of a problem|a problem|"
    r"something to worry about|anything to worry about))"
    r"|(?:should|do|ought) i (?:be )?(?:worried|worry|worrying|bothered)"
    r"|am i (?:ok|okay|alright|all right|normal|right))"
    r"(?: then| though| honestly| here)?$")

# A doubt about an amount ("is that a lot", "is that enough") is not asking whether a call was
# fussing, and "yes, worth getting seen" is not an answer to it.
QUANTITY_ASK = re.compile(r"\b(?:enough|a lot|too much|too many|too often)\b")

# An answer that named somebody to see or somewhere to go. The doubt on top of it is "was that
# fussing", and it was not.
#
# Only as an instruction, at the start of a sentence: "Get it checked by a GP within two weeks."
# is a call, and "Blood in it, breathlessness or three weeks of it is a reason to ring the surgery"
# is not - that one is a red flag inside an if, and answering it with "yes, worth getting seen
# rather than waiting on" turns "ring if" into "ring now".
CALL_MADE = (
    r"(?:get (?:it|that|them|yourself) (?:checked|looked at|seen)|get (?:an|a) "
    r"(?:appointment|referral)|see (?:a|your|the) (?:gp|doctor|nurse|dentist|optician|physio)|"
    r"ring (?:999|911|112|111|your gp|the gp|the surgery)|call (?:999|911|112|111)|"
    r"go to (?:a&e|the hospital|a walk-in|minor injuries)|book (?:an appointment|a gp)|"
    r"photograph it|have it looked at)")
CARE_NAMED = re.compile(r"(?:^|[.!?]\s+)(?:then |also |first )?" + CALL_MADE, re.I)

# The person's own line behind the answer, when it is a report of a referral they were given:
# "the pharmacist said to see a gp", "the nurse told me to get it checked", "my doctor wants me to
# have it looked at".
#
# This is the fence that keeps the reading off a doubt the composer already answers well. "should
# i get my mole checked" / "is that bad" sits under an answer that opens "Get it checked by a GP
# within two weeks", and the composer's own line for a doubt over an instruction answers it better
# than a bare yes does - it names who to see and what to say when they get there ("that answer
# already said by whom. Get that booked, and say how long it has been going on"). The doubt this
# file is for is a different one: the referral has already been made by somebody qualified, and
# the person is asking whether it was fussing. Only their own words say that.
SOMEBODY_TOLD_THEM = re.compile(
    r"\b(?:gp|doctor|doctors|pharmacist|chemist|nurse|practice|surgery|dentist|optician|"
    r"physio|physiotherapist|midwife|health visitor|consultant|vet|vets|111|a&e|hospital|"
    r"walk-in|paramedic|ambulance)\b", re.I)
TOLD = re.compile(
    r"\b(?:said|says|say|told|tells|tell|advised|advises|wants|wanted|reckons|thinks|"
    r"suggested|recommended|sent me|referred|booked|making me|making me go|insisted)\b", re.I)

CARE_LINES = (
    "Yes - worth getting seen rather than waiting on.",
    "Yes, get it seen. Asking is not fussing.",
    "Yes - that is a call worth making, not an overreaction.",
)

# The modules whose last line is never read back.
NOT_READ_BACK = frozenset(("safety", "urgent", "grief", "loss"))


def _last_bot(memory):
    """The bot's last line before this turn, as (text, module)."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return "", ""
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        text = str(turn.get("bot") or "")
        if text:
            return text, str(turn.get("module") or "")
    return "", ""


def reads_as_a_doubt(clean):
    """True when the whole line is a doubt about the answer above and nothing else."""
    flat = re.sub(r"[^a-z0-9 ]+", " ", str(clean or "").lower())
    flat = re.sub(r"\s+", " ", flat).strip()
    return bool(flat) and BARE_DOUBT.match(flat) is not None


def _the_line_behind(memory):
    """The person's own line that the answer above was answering, lowercased."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ""
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        if str(turn.get("bot") or ""):
            return str(turn.get("user") or "").lower()
    return ""


def reply_for(clean, memory):
    """The answer to a doubt on top of a call to get it seen, or None."""
    if not reads_as_a_doubt(clean):
        return None
    if QUANTITY_ASK.search(str(clean or "").lower()):
        return None
    said, module = _last_bot(memory)
    if not said or module in NOT_READ_BACK:
        return None
    if not CARE_NAMED.search(said):
        return None
    # Somebody qualified already made the referral: the doubt is "was that fussing", not "is
    # this thing bad". Without that in the person's own line the composer's own reading of the
    # doubt is the better one, and this file stands aside. See `SOMEBODY_TOLD_THEM`.
    behind = _the_line_behind(memory)
    if not (SOMEBODY_TOLD_THEM.search(behind) and TOLD.search(behind)):
        return None
    # Picked, not drawn: the same conversation has to get the same sentence, or a deck
    # comparison cannot be repeated and the bot looks like it changes its mind between runs.
    return pick(CARE_LINES, memory, clean)
