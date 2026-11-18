"""Who is going with them, and the ask that wants it back.

"im travelling with my mum" was acknowledged and then dropped: "who is coming with me" three turns
later got a search shrug, and "who am i going with" got "You haven't told me your name yet." The
companion is a fact about the chat, said by the person in their own words, and a friend answers it
from what they were told.

This module keeps the companion and answers the ask for it. A line that puts the companion right
("actually its my sister not my wife") replaces the one held, so the second answer is the true one.
"""
import re

from ..compose import pick

# The verb that says how they are getting there, used by both ways of saying it: "im travelling
# with my mum" and "my mum is coming with me".
_GOING = r"(?:travelling|traveling|flying|driving|heading|off|away|on holiday|going away|going)"
# The ways a companion is said after the verb: "im travelling with my mum", "we're off with my
# sister and her kids", "im taking my mum", "im bringing my dad along".
SAID_WITH = re.compile(
    r"\b(?:i'?m|im|i am|we'?re|were|we are)\s+" + _GOING + r"\s+"
    r"(?:off\s+|away\s+|there\s+|down\s+)?with\s+(?P<who>[a-z][a-z'\u2019 -]{1,40})", re.I)
# The destination comes between the verb and the companion: "we're off to spain with friends",
# "im flying to rome with my sister". Half the ways people say it have somewhere in the middle.
OFF_TO_WITH = re.compile(
    r"\b(?:i'?m|im|i am|we'?re|were|we are)\s+" + _GOING + r"\s+(?:to|into|for|back to)\s+"
    r"[a-z][a-z'\u2019 -]{1,25}?\s+with\s+(?P<who>[a-z][a-z'\u2019 -]{1,40})", re.I)
TAKING = re.compile(
    r"\b(?:i'?m|im|i am|we'?re|were|we are)\s+(?:taking|bringing)\s+(?P<who>[a-z][a-z'\u2019 -]{1,40})",
    re.I)
# The companion comes first: "my mum is coming with me", "my sister's coming too", "the kids are
# coming along".
COMING_WITH = re.compile(
    r"\b(?P<who>(?:my|our)\s+[a-z][a-z'\u2019-]{1,20}"
    r"(?:\s+and\s+(?:her|his|their|my|our)\s+[a-z][a-z'\u2019-]{1,20})?)"
    r"(?:\s+is|\s+are|'?s|s)?\s+(?:coming|going|travelling|traveling)\b", re.I)
# Nothing here: a line about somebody doing something else ("my mum is coming to stay").
_NOT_COMING_ALONG = re.compile(
    r"\b(?:to stay|to visit|to live|to dinner|to lunch|to pick me up|home|back|round|over|"
    r"out|down|up)\b|\bin\s*$", re.I)
# Where the phrase that names the companion stops.
_STOP = re.compile(
    r"\b(?:to|from|on|at|in(?!-law)|for|next|this|tomorrow|tonight|because|but|so|then|and then|"
    r"who|which|when|if|as|while|by|via|through|until|till|after|before)\b|[,.;:!?]", re.I)
# The words that name a person. A phrase no list of people has is not somebody: "im going with the
# blue one" is a choice, and "im travelling with the dog" is the dog.
_A_PERSON = re.compile(
    r"^(?:(?:my|our|the|a|an|his|her|their|two|three|four|five|six|a few|some)\s+)?"
    r"(?:mum|mom|mam|mummy|mother|dad|father|daddy|papa|son|daughter|wife|"
    r"husband|partner|sister|brother|kids?|children|friend|friends|mate|mates|parents|family|"
    r"granny|gran|nan|grandma|grandad|grandpa|aunt|auntie|uncle|cousin|niece|nephew|"
    r"boyfriend|girlfriend|colleague|neighbou?r|in-?laws?|mother-in-law|father-in-law)"
    r"(?:\s+and\s+.*)?$", re.I)
# The person and the one going with them, with the asker first or second: "me and my mate are
# going to spain in may", "my sister and i are going to rome". Whichever way round it is said, the
# companion is the one that is not the asker, and the going verb keeps it a trip rather than a
# line about somebody else ("me and my mate are knackered").
EITHER_SIDE = re.compile(
    r"\b(?:me|i)\s+and\s+(?P<who>(?:my|our|the)\s+[a-z][a-z'\u2019-]{1,20}"
    r"(?:\s+and\s+(?:her|his|their)\s+[a-z][a-z'\u2019-]{1,20})?)\s+"
    r"(?:are|is|were|was)\s+(?:going|off|flying|driving|travelling|traveling|heading)\b"
    r"|\b(?P<other>(?:my|our|the)\s+[a-z][a-z'\u2019-]{1,20})\s+and\s+(?:me|i)\s+(?:are|were)\s+"
    r"(?:going|off|flying|driving|travelling|traveling|heading)\b", re.I)

# The ask for it. Every frame here wants back the person who is coming, so "who is coming to the
# party" (a new question) and "who is coming with my mum" (about the mum) are not one of them.
ASK = re.compile(
    r"\bwho(?:'?s| is| are| else is| else)? (?:else )?(?:coming|going|travelling|traveling|"
    r"flying|driving)\s+(?:with|along with)\s+(?:me|us)\b"
    r"|\bwho (?:am i|are we) (?:going|travelling|traveling|flying|driving|heading)\s+with\b"
    r"|\bis (?:anyone|anybody|someone|somebody) (?:coming|going|travelling|traveling)\s+with\s+"
    r"(?:me|us)\b"
    r"|\bam i (?:going|travelling|traveling)\s+(?:with anyone|with anybody|alone|on my own)\b"
    r"|\bwho did (?:i|you) say (?:is |was )?(?:coming|going)\b", re.I)
# The ask about one person, said by name: "is my mum coming too?", "is my sister coming with us?".
# It wants back whether that very person is coming, so a chat that was told gets the answer.
IS_COMING_TOO = re.compile(
    r"\bis\s+(?P<who>(?:my|our)\s+[a-z][a-z'\u2019 -]{1,20}?)\s+"
    r"(?:coming|going|travelling|traveling|flying|driving)\b", re.I)

# An ask for when, where or why is not an ask for whether. "when is my mum coming" holds the
# same "is my mum coming" the yes/no reading looks for, and answering it with the yes/no line
# drops the day the chat was just put right to ("she moved it to saturday") and answers a
# question nobody asked. The ask for a detail is left to whoever reads that detail; this module
# only ever answers whether the person is coming.
ASKS_FOR_A_DETAIL = re.compile(
    r"^\W*(?:and |so |but |oh |right |also |ok(?:ay)?[ ,]+)*"
    r"(?:when(?:'?s| is| are| was| am| do| does| did| will| would)?\b"
    r"|where\b|why\b|which (?:day|date)\b|what (?:day|date|time)\b"
    r"|how (?:long|soon|many days)\b)", re.I)

# An ask that names somebody else is about them, not about the chat's companion.
_ABOUT_SOMEONE_ELSE = re.compile(r"\bwith\s+(?:my|our|your)\s+\w+", re.I)
# The companion put right: "actually its my sister not my wife". The store keeps the correction
# rather than the mistake - "who am i going with" answered "your wife" after this line is exactly
# what a friend who was not listening would say.
PUT_RIGHT = re.compile(
    r"\b(?:actually |no,? )?(?:it'?s |its |it is |they'?re |they are |that'?s |thats |"
    r"it was |the one is )?(?P<new>[a-z][a-z'\u2019 -]{1,25}?)\s+not\s+"
    r"(?:the |my |our )?(?P<old>[a-z][a-z'\u2019 -]{1,25})$", re.I)


def _bare(who):
    """The companion without the possessive in front: "my wife" -> "wife"."""
    words = str(who or "").lower().split()
    while words and words[0] in ("my", "our", "the", "a", "an", "your"):
        words.pop(0)
    return " ".join(words)


def _the_companion(text):
    """The companion a line names, as they said it, or "" when the line names nobody."""
    said = " ".join(str(text or "").split())
    # "my mother in law" is one person, and every stop word below would cut her name short at the
    # "in": the words are joined into the single relation they are before the phrase is read.
    said = re.sub(r"\b([a-z]+)\s+in[\s-]+(laws?)\b", r"\1-in-\2", said, flags=re.I)
    if not said or said.rstrip().endswith("?"):
        return ""
    for pattern in (SAID_WITH, OFF_TO_WITH, TAKING, COMING_WITH, EITHER_SIDE):
        match = pattern.search(said)
        if not match:
            continue
        who = match.group("who") or match.group("other") or ""
        cut = _STOP.search(who)
        if cut:
            who = who[:cut.start()]
        who = who.strip(" ,.;:-'\u2019")
        if not who:
            continue
        # "and her kids" after the first person keeps them: "my sister and her kids" is three
        # people, not one.
        if " and " in who:
            first, rest = who.split(" and ", 1)
            if _A_PERSON.match(rest) or _A_PERSON.match("my " + rest):
                who = first + " and " + rest
            else:
                who = first
        words = who.split()
        if len(words) > 5:
            continue
        if pattern is COMING_WITH and _NOT_COMING_ALONG.search(said):
            continue
        if not (_A_PERSON.match(who) or _A_PERSON.match("my " + who)):
            continue
        return who
    return ""


def _as_you_would_say_it(who):
    """The companion said back to the person: "my mum" -> "your mum"."""
    said = who.strip()
    for mine, yours in (("my ", "your "), ("our ", "your "), ("i ", "you "), ("me", "you"),
                        ("we ", "you "), ("myself", "yourself")):
        if said.startswith(mine):
            return yours + said[len(mine):]
    return said


def _more_than_one(who):
    """Whether the companion is more than one person, so the verb is "are"."""
    low = who.lower()
    return " and " in low or low.split()[-1].endswith("s")


def _the_correction(text, memory):
    """The companion the line puts right, or "" when the line corrects something else."""
    held = memory.get("company")
    if not isinstance(held, dict) or not held.get("who"):
        return ""
    match = PUT_RIGHT.search(" ".join(str(text or "").lower().split()))
    if not match:
        return ""
    old = _bare(match.group("old"))
    if not old or old != _bare(held["who"]):
        return ""
    new = match.group("new").strip(" ,.;:-")
    return new if _A_PERSON.match(new) or _A_PERSON.match("my " + new) else ""


# A trip on the table: the store files the plan in the person's own words ("Rome on my own in
# may"), so its being there is what makes the ask about company rather than about them.
ON_THEIR_OWN = re.compile(r"\b(?:on my own|alone|by myself|solo|just me)\b", re.I)


def _a_trip_is_here(memory):
    """Whether the chat holds a plan, which is what the ask for company is about."""
    user = memory.get("user") if isinstance(memory, dict) else None
    plans = (user or {}).get("plans") or []
    return any(str(plan or "").strip() for plan in plans)


def _on_their_own(memory):
    """Whether the plan they gave says they are going alone."""
    user = memory.get("user") if isinstance(memory, dict) else None
    plans = (user or {}).get("plans") or []
    return any(ON_THEIR_OWN.search(str(plan or "")) for plan in plans)


# The ask that is not an ask: "is my mum coming too?" wants the company back, and the ASK reader
# above does not have that frame, so the companion reader would answer it as news.
_ASKS = re.compile(r"^\W*(?:is|are|was|were|will|would|can|could|should|shall|do|does|did|"
                   r"who|what|when|where|why|how)\b", re.I)


# The verb that takes them to the place. A frame gets a phrase ("Cornwall in july"), and the
# plan the store keeps is sometimes the whole line they said it in - "me and the kids are going
# to spain in july" - so everything up to the place is cut away before the frame says it.
_THE_MONTHS = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|"
    r"december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\b", re.I)
_TO_THE_TRIP = re.compile(
    r"\b(?:going|off|flying|driving|travelling|traveling|heading|moving|off to|away to)\s+"
    r"(?:to|into|for|off to|down to|back to)\s+(?P<rest>.+)$", re.I)


def _the_phrase_a_frame_can_say(plan):
    """The trip as a phrase, from a plan that may be the whole line it was said in.

    "me and the kids are going to spain in july" is how a person says the plan, and it is not
    what a frame can put in a sentence: the two frames here read it back as "the kids along for
    me and the kids are going to Spain in july, then" and "the kids coming too. the kids and i
    are off to Spain in july goes better shared", which is the person's own line pasted into the
    reply. Cut at the travel verb and the phrase is theirs: "Spain in july".
    """
    plan = " ".join(str(plan or "").split()).strip(" .")
    found = _TO_THE_TRIP.search(plan)
    if found and found.group("rest").strip(" ."):
        plan = found.group("rest").strip(" .")
    if not plan:
        return ""
    # A month is a name in the middle of the phrase too ("spain in july" is "Spain in July"):
    # the plan is typed the way people type, and a frame is a sentence someone reads.
    plan = _THE_MONTHS.sub(lambda m: m.group(0).capitalize(), plan)
    return plan[:1].upper() + plan[1:]


def _the_trip_on_the_table(memory):
    """The trip the chat is on, in as few words as the plan was said: "Cornwall in july".

    A plan is not always a trip: "im making a birthday cake" files a plan too, and "my son is
    coming too" after it is about the cake, not about somebody travelling. The place is what
    makes it a trip, and the plan has to name it.
    """
    user = memory.get("user") if isinstance(memory, dict) else None
    places = (user or {}).get("places") or []
    if not places:
        return ""
    place = str(places[-1]).strip(" .")
    plan = str((user or {}).get("plan") or "").strip(" .")
    if not place or (plan and place.lower() not in plan.lower()):
        return ""
    return _the_phrase_a_frame_can_say(plan) or place


def _new_to_the_chat(who, memory):
    """Whether this is the first line of the chat that names them.

    A companion said once is news; said again it is not, and a line that comes back to them
    ("my mum is coming too, shes 60") is a detail about her, not the trip gaining a person.
    """
    bare = _bare(who)
    if not bare:
        return False
    said = re.compile(r"\b" + re.escape(bare) + r"\b", re.I)
    turns = [str(t.get("user") or "") for t in (memory.get("turns") or [])
             if isinstance(t, dict)]
    if turns and turns[-1].strip() == str(memory.get("understood", {}).get("text") or "").strip():
        turns = turns[:-1]
    return not any(said.search(line) for line in turns)


def _the_one_person_asked_about(text, memory):
    """Whether that very person is coming, or None when the line does not ask about one.

    "we are going to cornwall in july" / "my mum is coming too" / "is my mum coming too?" got a
    search hedge, which is the one answer a chat that has just been told cannot give. A person the
    chat was not told about is still answered honestly - nothing was said about them.
    """
    low = " ".join(str(text or "").lower().split())
    if not low or _NOT_COMING_ALONG.search(low):
        return None
    if ASKS_FOR_A_DETAIL.search(low):
        return None
    found = IS_COMING_TOO.search(low)
    if not found:
        return None
    named = _bare(found.group("who"))
    if not named or not _A_PERSON.match(named) and not _A_PERSON.match("my " + named):
        return None
    held = memory.get("company")
    if not isinstance(held, dict) or not held.get("who"):
        # Nobody was ever named. The chat is still on a trip, so the honest answer is that side
        # of it - "is my mum coming too?" after "we are going to cornwall in july" is a hedge
        # otherwise, which reads as if the trip itself had not been heard.
        if not _a_trip_is_here(memory):
            return None
        return pick(["Nothing said about your " + named + " - you have not said who is coming "
                     "with you.",
                     "You have not told me who is coming, so I cannot say about your " + named +
                     "."], memory, seed_text=low) or None
    who = _as_you_would_say_it(held["who"])
    if named == _bare(held["who"]):
        return pick(["Yes - you said " + who + " is coming with you.",
                     "You said " + who + " is coming, so yes.",
                     who.capitalize() + " - that is who you said was coming."],
                    memory, seed_text=low) or None
    return pick(["You only said " + who + " was coming - nothing about your " + named + ".",
                 "Nothing said about your " + named + " - it was " + who + " you told me about."],
                memory, seed_text=low) or None


def _the_companion_joins(text, memory):
    """The line puts somebody on the plan the chat already has, or None.

    "we are going to cornwall in july" / "my mum is coming too": the store keeps the companion,
    and the turn is the trip gaining a person. That is what a friend takes up - "your mum as
    well, good". Left alone, the carry reader answered it with the tail of the answer just given
    ("July takes the school holidays, so the prices only go one way"), which is the one thing a
    second sentence of a conversation must not be.
    """
    low = " ".join(str(text or "").lower().split())
    if not low or low.rstrip().endswith("?") or _ASKS.match(low):
        return None
    place = _the_trip_on_the_table(memory)
    if not place:
        return None
    who = _the_companion(text)
    if not who or not _new_to_the_chat(who, memory):
        return None
    said = _as_you_would_say_it(who)
    if _the_plan_is_this_line(text, memory):
        # The person named the people and the trip in one breath ("me and the kids are going to
        # spain in july"), so nobody is joining a plan that was already there: the news is the
        # trip with them on it. The joining frames read that line back as "Nice, the kids coming
        # too. Spain in july goes better shared", which answers a line nobody said.
        return pick([
            "Nice - " + place + " with " + said + ".",
            "Lovely - " + place + " with " + said + ".",
            place + " with " + said + " - good.",
        ], memory, seed_text=low) or None
    options = [
        said.capitalize() + " as well - good. " + place + " is better with company.",
        "Nice, " + said + " coming too. " + place + " goes better shared.",
        "Good - " + said + " along for " + place + ", then.",
    ]
    return pick(options, memory, seed_text=low) or None


def _the_plan_is_this_line(text, memory):
    """Whether the plan the chat holds is the line being answered, said in one breath.

    "me and the kids are going to spain in july" makes the plan and names who is going: the
    companion is not joining anything, and the reply is the trip with them on it.
    """
    line = " ".join(str(text or "").lower().split()).strip(" .")
    plan = " ".join(str(((memory or {}).get("user") or {}).get("plan") or "")
                    .lower().split()).strip(" .")
    return bool(line) and bool(plan) and (plan == line or line in plan or plan in line)


def observe(text, memory):
    """Keep the companion the line names, or the one it puts right. None either way."""
    fixed = _the_correction(text, memory)
    if fixed:
        memory["company"] = {"who": fixed, "turns": len(memory.get("turns") or []),
                             "corrected": True}
        return None
    who = _the_companion(text)
    if not who:
        return None
    memory["company"] = {"who": who, "turns": len(memory.get("turns") or [])}
    return None


def answer(text, memory):
    """The companion, said back, or the addition taken up. None when the line does neither."""
    low = " ".join(str(text or "").lower().split())
    if not ASK.search(low) or _ABOUT_SOMEONE_ELSE.search(low):
        one = _the_one_person_asked_about(text, memory)
        if one:
            return one
        return _the_companion_joins(text, memory)
    held = memory.get("company")
    if not isinstance(held, dict) or not held.get("who"):
        # No companion was ever named. The ask is still about the trip, so the honest thing is
        # to say so - "im going to rome on my own in may" / "who am i going with" is not a
        # question about their name, and the name reader answered it with "You haven't told me
        # your name yet." A chat with no trip on the table is not this module's line.
        if not _a_trip_is_here(memory):
            return None
        if _on_their_own(memory):
            return pick(["You said you were going on your own.",
                         "On your own, you said - nobody else was named."], memory, seed_text=low) or None
        return pick(["You haven't said who's going with you.",
                     "Nobody yet - you haven't said who is going with you."],
                    memory, seed_text=low) or None
    who = _as_you_would_say_it(held["who"])
    verb = "are" if _more_than_one(who) else "is"
    if low.rstrip().endswith(("alone", "on my own")):
        return "Not on your own - " + who + " " + verb + " coming with you."
    options = ["You said " + who + " " + verb + " coming with you.",
               who.capitalize() + " - that is who you said you were going with.",
               "You said " + who + " " + verb + " coming with you, and that is all I know."]
    if who.startswith("your "):
        options.insert(1, "Your " + who.split(" ", 1)[1] + ", you told me.")
    reply = pick(options, memory, seed_text=low)
    return reply or None
