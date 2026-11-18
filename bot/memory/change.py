"""A line that reports a change to a fact the store keeps is news, not a question about it.

"i want to lose a bit of weight" / "ive changed my diet" was answered "You haven't told me about
your diet." The person had just told the store about their diet, and the store denied the lot: the
ask pattern reads the words "my diet" as a request for the fact, and a line that reports a change
to the fact is not a request for it.

What is missing after "ive changed my diet" is not whether they changed it, it is what it is now,
so the honest reply asks for that (or runs with it when the store holds the value). The same
shape said as a wish ("i want to change my diet", "should i change my diet", "im thinking of
changing my diet") wants a hand with the change rather than a denial.

The subject is the caller's: it passes the word the fact is kept under ("diet", "budget", "my
hours") and gets back how the line stands to it, so this is one reading for every fact the store
can be asked about rather than a rule for the diet.

Two things are left alone. A line that gives the new value ("i changed jobs, im in a hospital
now", "ive changed my diet to vegan") is a fact the readers that keep facts have already taken,
and this reader stands down so they keep it. A how-to ask ("how do i change my diet") is a
request for advice, which the advice modules answer with something concrete.
"""
import re

# The verbs a change is said with: the fact as the object ("i changed my diet"), the thing given
# up ("i gave up sugar" - which is only a change of the diet when the line names the diet too),
# and the plain past as well as the perfect, because both are how a change is reported.
CHANGED = re.compile(
    r"\b(?:change|changed|changes|changing|swapped|swapping|switched|switching|"
    r"given up|give up|gave up|gone off|went off|cut out|cut down|cutting out|cutting down|"
    r"stopped|stopping|quit|quitting|dropped|ditched|overhauled|tweaked|reworked)\b", re.I)
# The fact said as the thing that has changed: "my diet has changed", "my hours are different
# now". A person says it this way when the change is the point rather than the new value.
SUBJECT_CHANGED = re.compile(
    r"\b(?:is|are|has|have|had|got)\s+(?:all\s+)?(?:changed|different|new)\b"
    r"|\bis\s+not\s+the\s+same\b|\bnot the same\b", re.I)
# A wish to change it, which is not a change yet. The auxiliaries are what make it a wish, and
# they come before the verb: "i want to change my diet" is not "i changed my diet".
WANTS = re.compile(
    r"\b(?:want(?:s|ed)?|wanna|need(?:s|ed)?|should|shall|ought|could|would|might|may|"
    r"thinking|thought|considering|planning|plan|trying|try|hoping|hope|ready|about|"
    r"worth|idea|better)\b", re.I)
# A how-to ask is advice, and the advice modules answer it with something concrete ("how do i
# change my diet" gets the protein-and-fibre card). The store reading it would take that away.
HOW_TO = re.compile(r"\bhow\s+(?:do|does|can|could|should|would|might|to)\b|"
                    r"\bwhat(?:'s| is) the best way\b|\bany (?:tips|advice|ways)\b", re.I)
# When the change happened is not what it changed to: "i changed my diet a month ago" and "i
# changed my diet last week" leave the store without the new value just as much as the plain
# report does.
WHEN_TAIL = re.compile(r"\b(?:a|an|one|two|three|four|five|six|few|couple(?: of)?|\d+)\s+"
                       r"(?:day|week|month|year|while)s?(?:\s+or so)?\s+ago\b|"
                       r"\b(?:last|this)\s+(?:week|month|year)\b|"
                       r"\b(?:recently|lately|these days|nowadays)\b", re.I)
# The words a change line is made of, once the fact itself is taken out: anything else left in
# the line is something the person is telling, and the readers that keep facts answer it better.
FILLER = frozenset("""
    i me my our we you your it its the a an to of and but so or now just really also too very
    much lot bit still again already even actually all right ok okay well oh ah yeah yes no
    have has had ve ive weve youve theyve im am is are was were be been do does did done
    dont doesnt didnt cant
""".split())
# The facts as the store keeps them, and the question that asks for the value when it has moved.
# A subject with no line here still gets a reply, in words that fit any fact.
ASKS = {
    "diet": "What does a normal day look like now?",
    "budget": "What are you working with now?",
    "hours": "What are your hours now?",
    "job": "What are you doing now?",
}
WISHES = {
    "diet": ("What is the change for - weight, energy, or something a doctor said? That decides "
             "which swaps are worth it."),
    "budget": "What is the change for - a bill, a save, or paying something off?",
}
# Said when the store holds the old value: it names the one it stops using, because a person who
# has just changed something does not want the old value said back as if it were current.
KEPT = "Good to know. "
DROPPING = "{was}, so I'll drop that - {ask}"
CHANGED_ASK = "What is it now?"
WISHED = "What are you trying to change about it? Tell me and I'll be concrete."
# "i dont want to change my diet", "no need to change my budget": the person is not reporting a
# change and not asking for one, and the wish reply would be a hand with something they have just
# turned down.
NOT_WANTING = re.compile(r"\b(?:don'?t|doesn'?t|didn'?t|not|never|no need|no plans|no intention)\b"
                         r"[^.!?]{0,20}\b(?:want|wanna|need|going to|gonna|plan|plans|thinking|"
                         r"planning|change|changing)\b", re.I)


def _names(line, subject):
    """Whether the line names the fact: the subject's own words, in any case."""
    words = str(subject or "").strip()
    if not words:
        return False
    pattern = r"\b" + r"\s+".join(re.escape(part) for part in words.split()) + r"\b"
    return re.search(pattern, line, re.I) is not None


def _left_over(line, subject):
    """The words of the line that are neither the fact, nor the change, nor filler."""
    mine = str(line or "")
    words = str(subject or "").strip()
    if words:
        mine = re.sub(r"\b" + r"\s+".join(re.escape(part) for part in words.split()) + r"\b",
                      " ", mine, flags=re.I)
    mine = WHEN_TAIL.sub(" ", mine)
    for pattern in (CHANGED, SUBJECT_CHANGED, WANTS):
        mine = pattern.sub(" ", mine)
    return [word for word in re.findall(r"[a-z']+", mine.lower())
            if word not in FILLER and word not in words.lower().split()]


def reported(text, subject):
    """How the line stands to the fact: "changed", "wanting", or None for anything else.

    `subject` is the fact's own word, as the store keeps it ("diet", "budget", "my hours"), and
    the line has to name it: "ive changed my diet" is about the diet, "ive changed the bedding"
    is about something else and is left to the modules that answer it. A line with a new value in
    it ("ive changed my diet to vegan") is left to the readers that keep facts.
    """
    line = str(text or "").strip()
    if not line or not _names(line, subject):
        return None
    if HOW_TO.search(line) or NOT_WANTING.search(line):
        return None
    moved = CHANGED.search(line) or SUBJECT_CHANGED.search(line)
    if not moved:
        return None
    if _left_over(line, subject):
        return None  # the line says more than the change: a value, a plan, a reason of its own
    before = line[:moved.end()]
    if WANTS.search(before):
        return "wanting"
    return "changed"


def reply(kind, subject, was=None):
    """What to say to a line that reports a change to the fact, or asks for one.

    `was` is the value the store holds, when it holds one: the reply names it as the value it
    stops using, so the person can see the store has moved on rather than being asked to say it
    all again.
    """
    key = str(subject or "").strip().lower()
    if kind == "wanting":
        return WISHES.get(key) or WISHED
    ask = ASKS.get(key) or CHANGED_ASK
    if not was:
        return KEPT + ask
    settled = str(was).strip().rstrip(".")
    if settled.startswith("no "):
        settled = "You don't eat " + settled[3:]
    else:
        settled = "You were " + settled
    return DROPPING.format(was=settled, ask=ask[0].lower() + ask[1:])
