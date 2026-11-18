"""A person in a role who keeps doing the same thing, or was brushed off: "my boss keeps moving
the goalposts", "my manager says its just how it is".

These lines name no ask at all, so on main they reached the two pools that fit any message ("Got it.
Is there anything you'd like a hand with?", "I'm listening - say more if it helps"). The person has
said the whole of it and is waiting to hear whether they are being unreasonable. Nothing in the line
can be looked up - it is between them and somebody else - so the reply says that in a few words and
asks the one thing that decides the next step: said to them, or taken higher.

Every reply leads with the step the bot does know - put it in writing once, dates and what you want,
keep a copy - and then names where the rest of it lives: one rung above, ACAS, the complaints
procedure, the ombudsman. A pointer on its own, or a question back on its own, is not an answer, and
neither is a warm line that says nothing.

The reading lives here rather than in `bot/compose/fallback.py` because that file is over the size
the world accepts, so a change to it cannot be submitted at all. `bot/modules/receiving_end.py` is
its band: `PRIORITY` -980, above the greeting fallback (-1000) and below the nudge (-950), so it can
only ever replace the two pools that fit any message. It returns None on every other line.
"""
import re

from .fallback import (_choose, _grief_thread, _in_a_loss_thread, _in_a_pool, _the_line_before,
                       in_a_safety_thread)

ROLE_WITH_SOMEBODY_ABOVE = (
    r"(?:boss|manager|line\s+manager|team\s+lead|team\s+leader|team\s+manager|supervisor|"
    r"shift\s+lead|foreman|colleague|co-?worker|teacher|head\s?teacher|tutor|lecturer|"
    r"landlord|landlady|letting\s+agent|social\s+worker|social\s+services|housing\s+officer|"
    r"housing\s+association|jobcentre|council|school|nursery|college|university|"
    r"gp\s+surgery|doctors\s+surgery|surgery|practice|hr|payroll|recruiter|agency)")
# A complaint says something is wrong, and a line that does not is not one: "my colleague keeps
# bringing in cake" and "my old boss always gave me a lift home" are warm lines about a person,
# and asking who is above them reads as though the person were in trouble. The words here are the
# ones a person reaches for when a thing is going wrong, not a list of every complaint: a line
# with none of them keeps whatever reply it already had.
A_COMPLAINT_WORD = re.compile(
    r"\b(?:never|not|no|wont|won'?t|doesnt|doesn'?t|didnt|didn'?t|ignores?|ignored|forgets?|"
    r"forgot|losing|loses|lost|lies|lying|lied|shouts?|shouted|yell\w*|blames?|blamed|"
    r"criticis\w*|undermin\w*|gaslight\w*|cancel\w*|clos\w*|chang\w*|changes|moves?|moved|"
    r"goalposts|overrules?|shuts? me down|snaps? at me|rolls? (?:his|her|their) eyes|leaves? me out|"
    r"rules|last minute|wrong|unfair|credit|favourites?|piling|pile|micromanag\w*|hiding|"
    r"refuses?|refused|picks on|picked on|talks over|talked over|belittles?|belittled|"
    r"mess(?:ed)? up|muck\w*|stops? me|stopped me|keeps me|kept me|delay\w*|chase\w*|"
    r"impossible|nightmare|stress\w*|awful|horrible|useless|lazy|rude|bully\w*|unprofessional)\b",
    re.I)
# "again and again" in the person's own words. A single "wont" is not one of these: "my manager
# wont put anything in writing" already has a better reply above this reading, and one refusal
# is not a pattern.
KEEPS_DOING_IT = re.compile(
    r"\b(?:keeps?|always|never|constantly|every\s+(?:single\s+)?(?:time|week|day|shift|month|"
    r"term)|again\s+and\s+again|over\s+and\s+over|all\s+the\s+time|ignores?|ignored|"
    r"picks?\s+on\s+me|undermines?\s+me|talks?\s+over\s+me|belittles?\s+me|gaslights?)\b",
    re.I)
A_PERSON_WHO_KEEPS = re.compile(
    r"\b(?:(?:my|our|his|her|their|the)\s+(?:new\s+|old\s+|current\s+|ex\s+)?)?"
    + ROLE_WITH_SOMEBODY_ABOVE + r"\b", re.I)
# A memory is not a complaint: "my teacher always said i was good at maths" is a warm line about
# somebody, and asking who is above them reads as though the person were in trouble.
A_WARM_MEMORY = re.compile(
    r"\b(?:always|used\s+to)\s+(?:said|told|taught|gave|made\s+me|let\s+me|wanted|encouraged)\b"
    r"|\b(?:was|were)\s+(?:great|lovely|kind|good|brilliant|fair|helpful)\b", re.I)
# The other half of the same turn: the person did say it, and the one above them closed it
# down. "my manager says its just how it is", "my landlord shrugs it off", "the school says thats
# life", "my boss says everyone has to put up with it", "my team lead keeps saying we'll see".
# The brush-off is the complaint - there is no wrong word to look for, and nothing in the line
# to look up - so this half needs the role and the dismissal, and no complaint word beside it.
A_BRUSH_OFF = re.compile(
    r"\b(?:says?\s+(?:that\s+)?(?:its|it'?s|thats|that'?s)\s+(?:just\s+)?(?:how|the\s+way)\b"
    r"|says?\s+(?:that\s+)?(?:its|it'?s|thats|that'?s)\s+life\b"
    r"|shrugs?\s+(?:it\s+off|it|and)\b"
    r"|says?\s+(?:to\s+)?(?:just\s+)?(?:get\s+on\s+with\s+it|put\s+up\s+with\s+it)"
    r"|says?\s+(?:everyone|everybody|we\s+all)\b[^.?!]{0,40}?(?:put[s]?\s+up\s+with|has\s+to)"
    r"|keeps?\s+saying\s+(?:we'?ll\s+see|next\s+(?:month|week|year)|soon|in\s+a\s+(?:bit|minute|while))"
    r"|won'?t\s+even\s+(?:say|answer|reply|discuss))\b", re.I)
THE_BRUSH_OFF_REPLIES = (
    # What the bot knows: a shrug is not an answer, and the move that works is the same one every
    # time - in writing, with a date, and a copy kept. Where the rest of it lives is named too,
    # because a question back on its own is not an answer.
    "That is a brush-off rather than an answer. Nothing to look up here, but the move that works "
    "is a short email: say what they said, what you want changed, and ask for a reply by a date. "
    "If the date passes, that email is what you take one rung above them, or to ACAS if it is a "
    "workplace.",
    "When the answer is that is just how it is, ask once more in writing - what you want changed "
    "and by when - and keep the reply. That email is what the next rung reads: ACAS for a "
    "workplace, or the complaints procedure every school, council and surgery has to follow.",
    "Nothing to look up here, but do not leave it spoken: put the request in writing with a date "
    "on it and keep a copy. If {role} will not answer that, the next step is one rung above them, "
    "and after that the ombudsman, which is free to use and is where a case finally gets looked "
    "at.",
    "There is a shape to these answers and it is worth naming: ask for the reason in writing, "
    "once, with the date you want it by. A recorded refusal is something you can challenge, and "
    "the complaints procedure is the route - it has to end somewhere, usually with the ombudsman.",
)
PERSON_WHO_KEEPS_REPLIES = (
    "Nothing in that to look up, but the step is the same as for any pattern like this: put it in "
    "writing once - the date, what happened, what you want - and keep a copy. If it does not come "
    "back in a week, it goes one rung above {role}, and ACAS gives free advice on the wording if "
    "it is a workplace.",
    "When it happens again and again the wording decides it: dates, what you asked for, what "
    "happened next. Send that once to {role} and ask for an answer by a date. If it does not come, "
    "ask for the written complaints or grievance procedure and follow the step it names.",
    "Keep a short record - the date, what happened, what you asked for. A record is what makes "
    "{role} have to answer, and it is what the next rung reads. Every school, council and GP "
    "surgery has a complaints procedure with named steps, and asking for a copy is the first one.",
    "That is a pattern rather than one bad day, so put it in writing rather than say it again: "
    "what you want changed, with dates. Nothing to look up here, but the complaints procedure is "
    "where this goes next - ask for a copy of it and follow the step it names.",
)


# The role as it is said back: a small word kept as the person wrote it and the two that are
# said with an article. "hr shrugs it off" answered "what would you want hr to actually do?"
# reads as a typo, and a reply that looks careless is the placeholder in another shape.
ROLE_SAID_BACK = {"hr": "HR", "gp surgery": "the surgery", "doctors surgery": "the surgery",
                  "surgery": "the surgery", "school": "the school", "nursery": "the nursery",
                  "council": "the council", "university": "the university",
                  "college": "the college", "jobcentre": "the jobcentre"}


# Whose person it is, turned to face them: "my boss" -> "your boss", "his teacher" -> "their
# teacher". A reply that says "it is between you and my boss" is the bot reading the person's own
# words back at them, which is the placeholder in another shape.
THEIR = {"my": "your", "our": "your", "his": "their", "her": "their", "their": "their"}


def _the_role_said_back(found):
    """The role as the person wrote it, facing them the right way round."""
    role = " ".join(str(found or "").split()).lower()
    if role in ROLE_SAID_BACK:
        return ROLE_SAID_BACK[role]
    if role.startswith(("the ", "a ")):
        return role
    first, _, rest = role.partition(" ")
    if first in THEIR and rest:
        return THEIR[first] + " " + rest
    if first in ("your", "their", "the", "a"):
        return role
    # A role the line reaches through somebody else - "my sons teacher keeps losing his work" -
    # is matched from the role word on, so the possessive is not in it: "the teacher" reads right
    # where a bare "teacher" reads like a missing word.
    return "the " + role


# A body in the thread is never this reading's turn. "he held a knife to my throat" then "my boss
# shrugs it off" is not a person asking about a manager: the thing above it is the answer, and a
# written complaint about a boss is the wrong reply inside it. This is a stand-down only - it never
# answers anything itself, so over-reading is the safe direction.
A_BODY_LINE = re.compile(
    r"\b(?:knife|gun|knives|weapon|throat|strangl\w*|chok\w*|punch\w*|beat (?:me|him|her)|"
    r"hit (?:me|him|her|my)|hits? me|hurt(?:ing)? me|hurts? me|threaten\w*|threats?|"
    r"kill me|kill(?:ed)? (?:him|her|them)|bruis\w*|abus\w*|assault\w*|rape\w*|"
    r"black eye|broken (?:arm|nose|ribs?))\b", re.I)


def _a_body_line_above(memory):
    """True when one of the last two things the person said was about a body or a threat."""
    if not isinstance(memory, dict):
        return False
    said = [str(turn.get("user") or "") for turn in (memory.get("turns") or [])
            if isinstance(turn, dict)]
    return any(A_BODY_LINE.search(" ".join(line.lower().split())) for line in said[-2:])


def _a_person_who_keeps(clean, repaired, memory):
    """The question back to "my boss keeps moving the goalposts", or None.

    Both halves of the turn are read here because they are the same turn: the thing happens
    again and again, or the person said it once and was brushed off. In either case nothing in
    the line can be looked up and the next step is the same question.
    """
    said = " ".join(str(clean or "").split())
    if not said:
        return None
    role = None
    for line in (said, " ".join(str(repaired or "").split())):
        match = A_PERSON_WHO_KEEPS.search(line)
        if not match:
            continue
        # The role the line names, with everything in front of it ("my line manager"), and the
        # words after it are where the habit is: "my boss keeps moving the goalposts".
        after = line[match.end():match.end() + 70]
        # The habit needs a complaint word beside it, because a warm line about a person is not a
        # complaint. A brush-off needs neither: the dismissal is the complaint.
        brush = A_BRUSH_OFF.search(after)
        if (brush or (KEEPS_DOING_IT.search(after) and A_COMPLAINT_WORD.search(line))) \
                and not A_WARM_MEMORY.search(line):
            role = _the_role_said_back(line[match.start():match.end()])
            pool = THE_BRUSH_OFF_REPLIES if brush else PERSON_WHO_KEEPS_REPLIES
            break
    if not role:
        return None
    if (in_a_safety_thread(memory) or _grief_thread(memory) or _in_a_loss_thread(memory)
            or _a_body_line_above(memory)):
        # A crisis, a death or a person leaving has its own pool, and "does it need to go above
        # them?" is no reply inside one.
        return None
    says = str(_the_line_before(memory) or "")
    if says and _in_a_pool(says, (PERSON_WHO_KEEPS_REPLIES, THE_BRUSH_OFF_REPLIES)):
        # The same paragraph in other words a turn later is the placeholder said twice.
        return None
    return _choose([line.format(role=role, Role=role[0].upper() + role[1:])
                    for line in pool], memory, clean)


def reply_for(clean, repaired, memory):
    """The reply to a role that keeps doing it, or none for every other line."""
    return _a_person_who_keeps(clean, repaired, memory)
