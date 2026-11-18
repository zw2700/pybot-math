"""A job nobody should try first is answered with the trade that does it, and the reason.

"how do i repoint a chimney", "can i rewire the fuse box myself" and "can i take out a chimney
breast myself" name a job the bot holds no card for, so they fell to the hedge - "that's beyond
what I know well, sorry. Searching for it will turn up better sources" - which is true of every
line and hands a person a ladder. `STYLE.md` asks for the part that can be known and then where
the rest lives: for these jobs the trade is not a matter of taste, and neither is the reason.

The reading is a job from the table below plus the line saying it is the person's own hands on it
("how do i ...", "can i ... myself", "on my own"), so it is a shape and not a list of wordings.
Two general rules, both tested:

* **A hazard word in front of its own noun names the job**; standing alone it is a report. "fix a
  leaking skylight" is a plan for a roofer, "the water is leaking through the skylight" is
  happening now and keeps the answer it already has.
* **A line that hires, prices or books somebody stands down**, because the reader for that names
  a directory of people near you rather than the trade as such.

Nothing here is a fact about the world that could be wrong: the trade is the one that does that
kind of work, and the reason is why it is not a weekend's job. The priority sits above the
composer's intake form and hedge (-1000) and below every card, so a repair answer, a safety card
or a knowledge entry keeps its turn, and the fences are as much the point as the table.
"""
import random
import re

from ..memory import last_bot

# Above the composer's intake form and hedge (-1000), below everything that knows something.
PRIORITY = -999

# The job, by the trade that does it. Each entry is (what the line says, who does it, why it is
# not a weekend's job). A job appears in one row only, and the first row that matches wins.
NOT_A_JOB_TO_TRY = (
    (re.compile(r"(?<![a-z])(?:chimney\s+breast|(?:remove|take|knock|cut)\s+(?:the\s+|out\s+the\s+)?"
                r"chimney\s+(?:breast|stack)|chimney\s+breast\s+(?:out|removed|gone))(?![a-z])"),
     "a builder with a structural engineer",
     "whether it is carrying anything above it is an engineer's call, and that call decides how "
     "the rest of the job is done"),
    (re.compile(r"(?<![a-z])(?:chimney|chimney\s+stack|chimney\s+pot|chimney\s+pots|"
                r"flaunching|repoint(?:ing)?\s+(?:the\s+|a\s+|my\s+|our\s+|this\s+)?chimney)"
                r"(?![a-z])"),
     "a chimney sweep",
     "it is done from a scaffold above the roofline, and the fall is the part that goes wrong"),
    (re.compile(r"(?<![a-z])(?:gas\s+(?:hob|fire|oven|cooker|pipe|pipes|pipework|supply|valve|"
                r"appliance|boiler|meter)|lpg|calor\s+gas)(?![a-z])"),
     "a Gas Safe registered engineer",
     "on gas the work belongs to somebody on the register, and the number is one anyone can look "
     "up before they start"),
    (re.compile(r"(?<![a-z])(?:fuse\s*box|fuse\s+board|consumer\s+unit|rewire|rewiring|ring\s+main|"
                r"socket\s+circuit|extra\s+socket|new\s+socket|the\s+wiring|the\s+electrics|"
                r"electric\s+shower|shower\s+unit)(?![a-z])"),
     "an electrician",
     "the mistake that matters sits behind the plaster and starts a fire where nobody is looking"),
    (re.compile(r"(?<![a-z])(?:remove|removing|knock\s+through|knock\s+out|take\s+out|taking\s+out|"
                r"widen|open\s+up|put\s+a\s+door\s+in)\s+(?:a\s+|the\s+|this\s+|that\s+|our\s+)?"
                r"(?:wall|walls|load\s*bearing\s+wall|wall\s+between|partition)(?![a-z])"
                r"|(?<![a-z])(?:take|taking|knock|knocking|cut|cutting|rip|ripping)\s+(?:a\s+|the\s+|"
                r"this\s+|that\s+)?(?:wall|walls|partition)\s+(?:out|down)(?![a-z])"
                # "how do i know if the wall holds the house up" is the question underneath a
                # knock-through, and it is the engineer's answer, not a search.
                r"|(?<![a-z])(?:load\s*bearing|load-bearing|holding\s+(?:the\s+)?(?:house|roof|floor|"
                r"ceiling)\s+up|holds\s+(?:the\s+)?(?:house|roof|floor|ceiling)\s+up|"
                r"holding\s+anything\s+up|structural)(?![a-z])"),
     "a builder with a structural engineer",
     "whether a wall is holding the floor up above it is decided by an engineer, not by how it "
     "looks once the plaster is off"),
    (re.compile(r"(?<![a-z])(?:fell|felling|cut\s+down|cutting\s+down|take\s+down|taking\s+down|"
                r"pollard|pollarding|coppice|prune|pruning|trim)\s+(?:a\s+|the\s+|my\s+|this\s+|"
                r"that\s+|our\s+)?(?:tree|trees|conifer|conifers|poplar|willow|oak|sycamore|"
                r"leylandii)(?![a-z])"
                r"|(?<![a-z])(?:tree\s+surgery|stump\s+grinding|grind\s+the\s+stump)(?![a-z])"),
     "a tree surgeon",
     "a tree goes where it leans once the last cut is made, and a bad one takes a fence, a roof "
     "or a person with it"),
    (re.compile(r"(?<![a-z])(?:wasp\s+nest|wasps\s+nest|hornets?\s+nest|(?:wasps|hornets|bees)\s+"
                r"in\s+the\s+(?:loft|roof|wall|cavity|chimney)|nest\s+of\s+(?:wasps|hornets))"
                r"(?![a-z])"),
     "a pest controller",
     "it is a suit and a long reach, and the ones that sting come at you when it goes wrong"),
    (re.compile(r"(?<![a-z])(?:asbestos|artex|old\s+lagging|asbestos\s+ceiling|asbestos\s+roof)"
                r"(?![a-z])"),
     "a licensed asbestos remover",
     "it has to be identified before anyone cuts into it, and the test is cheap next to guessing"),
    # "how do i bleed my radiators" is a key and a bucket, so the row wants the fittings verbs.
    (re.compile(r"(?<![a-z])(?:move|moving|remove|removing|replace|replacing|swap|swapping)\s+"
                r"(?:the\s+|a\s+|my\s+|this\s+|that\s+|one\s+of\s+the\s+)?"
                r"(?:leaking\s+|old\s+|broken\s+|rusty\s+|stuck\s+|noisy\s+)?"
                r"(?:radiator|radiators|rad|rads)(?![a-z])"),
     "a plumber",
     "a radiator comes off wet and goes back on needing the system filled and bled, and a joint "
     "that weeps under the floor costs more than the fitting"),
    (re.compile(r"(?<![a-z])(?:the\s+)?(?:roof|roofing|felt\s+on\s+the\s+roof|roof\s+felt|"
                r"flashing|re-?felt|re-?roof|tiles?\s+on\s+the\s+roof|ridge\s+tiles?)(?![a-z])"
                # A skylight is also a thing to clean and a velux a thing to open, so those two
                # only count when the line puts a roof job on them.
                r"|(?<![a-z])(?:fit|fitting|replace|replacing|repair|repairing|fix|fixing|mend|"
                r"mending|install|installing|leak|leaking|broken|re-?felt|re-?roof)\s+"
                r"(?:around\s+)?(?:the\s+|a\s+|my\s+)?(?:broken\s+|cracked\s+|old\s+|damaged\s+|"
                r"stuck\s+|leaking\s+)?(?:skylight|velux|roof\s+window)(?![a-z])"),
     "a roofer",
     "it is scaffold and two people, and the water from a job that fails costs more than the job"),
)
# The ask has to be the person's own hands on it: a way in ("how do i ..."), or the person saying
# it is them doing it. Anything that hires, prices or books stands down, because this bot has a
# reader for that and it names the directory rather than the trade.
TRY_IT_MYSELF = re.compile(
    r"(?<![a-z])(?:how\s+(?:do|can|could|would|should)\s+(?:i|we|you)\b|how\s+to\b"
    r"|whats\s+the\s+best\s+way\s+to\b|what's\s+the\s+best\s+way\s+to\b"
    r"|whats\s+the\s+right\s+way\s+to\b|is\s+it\s+(?:easy|hard|difficult|safe|worth\s+it)\s+to\b"
    r"|(?:is|would)\s+(?:this|that|it)\s+(?:a|an)\s+(?:job|thing)\s+(?:for\s+me|i\s+can)"
    r"|can\s+(?:i|we)\s+(?:just\s+)?(?:do|fix|fit|replace|remove|take|knock|cut|fell|wire|"
    r"rewire|re-?felt|refelt|repoint|install|cap|climb|get\s+up|dig|sand|scrape|strip|mend|"
    r"move|swap|widen|plaster|prune|pollard|bleed|drain|have\s+a\s+go|try)\b"
    r"|should\s+(?:i|we)\s+(?:do|try|have\s+a\s+go|tackle)\b)(?![a-z])")
SELF_WORDS = ("myself", "my own", "by myself", "on my own", "diy", "ourselves",
              "have a go", "have a bash", "a go at it", "a go at that", "my own self")
# Hiring, pricing or booking it: the reader for that owns those lines, and it names a directory of
# people near you rather than the trade as such.
NOT_TRYING_IT = ("find", "find me", "hire", "hiring", "recommend", "recommended", "looking for",
                 "need a", "need an", "someone", "somebody", "anyone", "anybody", "quote",
                 "quotes", "price", "prices", "cost", "costs", "how much", "near me", "local",
                 "book", "booked", "call out", "callout", "directory", "reviews")
# A line that says something is happening now is not a job to plan: "i can smell gas" wants the
# valve and the emergency line, and a quote from two engineers is the wrong answer to it.
NOW_WORDS = ("smell", "smells", "smelling", "leaking", "leak", "leaks", "hissing", "sparking",
             "sparks", "smoke", "smoking", "on fire", "emergency", "right now", "just now",
             "tonight", "burst", "flooding", "collapsed", "falling down")
# The same word is a report when it is the thing said, and only a name for the job when it sits in
# front of the thing it belongs to: "fix a leaking skylight" is a plan, "water is leaking through
# the skylight" is happening now. A determiner in front and a noun behind is what tells them
# apart, so the naming words come out before the stand-down is asked.
A_HAZARD_NAMING_THE_JOB = re.compile(
    r"\b(?:a|an|the|my|our|your|his|her|their|this|that|these|those)\s+"
    r"(?:leaking|leaky|smoking|smoky|hissing|sparking|burst|collapsed|flooding|blocked)\s+"
    r"(?=[a-z])")
# A tree in the house, a decision, or a family one is not the tree this table means.
NOT_A_TREE = ("christmas", "xmas", "family tree", "decision tree", "tree diagram")
# A thing with a plug on it, that you unplug first, is not the fuse box: a table lamp is a
# screwdriver, a length of flex and the colours, and people who ask about one are usually right
# to (shiny-pelican, #13403). The wiring itself still counts, so the line may name it.
CARRIED_AND_UNPLUGGED = ("lamp", "lamps", "table lamp", "desk lamp", "floor lamp", "bedside",
                         "plug", "plugs", "flex", "lamp holder", "bayonet", "ceiling rose")
THE_WIRING_ITSELF = ("fuse box", "fuse board", "consumer unit", "the wiring", "the electrics",
                     "socket circuit", "ring main", "electric shower", "shower unit",
                     "shed", "garage", "extension", "loft")
NOT_A_JOB_TO_TRY_POOL = (
    "That is a job for {who}, not a ladder and an afternoon: {why}. Two quotes from people near "
    "you sets the price, and the second one usually says something the first did not.",
    "{who_cap} is who takes this one on: {why}. Ring two near you - a quote costs nothing, and it "
    "tells you whether this is a small job or a bigger one than it looks.",
)
# A gas or electrical job is also checkable: the register is what a landlord, a buyer or an
# insurer asks about later, so it is worth having the number before anybody starts.
REGISTER_HINT = {
    "a Gas Safe registered engineer": "Ask for the Gas Safe number before you book.",
    "an electrician": "Ask which competent-person scheme they are with before you book.",
}


def _has(line, phrases):
    """True when one of the phrases is in the line as a whole word or phrase."""
    for phrase in phrases:
        if re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", line):
            return True
    return False


def _the_job(said):
    """(who does it, why it is not a weekend's job) for the job this line names, or None."""
    for pattern, who, why in NOT_A_JOB_TO_TRY:
        if pattern.search(said):
            return who, why
    return None


def respond(text, memory=None):
    said = " ".join(str(text or "").lower().split())
    if not said:
        return None
    if _has(said, NOT_TRYING_IT) or _has(A_HAZARD_NAMING_THE_JOB.sub("", said), NOW_WORDS):
        return None
    if not TRY_IT_MYSELF.search(said) and not _has(said, SELF_WORDS):
        return None
    if _has(said, NOT_A_TREE):
        return None
    if _has(said, CARRIED_AND_UNPLUGGED) and not _has(said, THE_WIRING_ITSELF):
        return None
    job = _the_job(said)
    if not job:
        return None
    who, why = job
    said_pool = [line.format(who=who, who_cap=who[0].upper() + who[1:], why=why)
                 for line in NOT_A_JOB_TO_TRY_POOL]
    hint = REGISTER_HINT.get(who)
    if hint:
        said_pool = [" ".join((line, hint)) for line in said_pool]
    last = str(last_bot(memory) or "").strip()
    fresh = [line for line in said_pool if line != last]
    return random.choice(fresh or said_pool)
