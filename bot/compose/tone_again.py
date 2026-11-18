"""The draft the bot has just written, said again in the tone that was asked for.

    i need to write to my landlord
      "Happy to write it for you. Tell me what you want them to know or do, and roughly what
       tone, and I'll put a version together you can edit."
    the boiler has been broken for 2 weeks
      'Something like this works: "Hi, the boiler has been broken for 2 weeks. Thanks."'
    make it firm but polite
      "That's beyond what I know well, sorry. Searching for it will turn up better sources than I
       can offer; tell me what you find and I'll help you weigh it up."

Nothing in that last reply is true: the ask is not a fact about the world and there is nothing to
search for. It is an edit of words the bot itself printed a turn ago, and the person is not asking
the internet to make their message firmer - they are asking the bot. So the bot does it: the draft
comes back with the hedges out and the ask in, or one word shorter, or with the courtesy put in.

What this reads, and what it keeps off, because a wrong draft is worse than the shrug it replaces:

- the line has to be **tone only**. "make it firm but polite" names no subject; "make the boiler
  message firm" does, and that is a drafting question for `draft.py`;
- the reply just given has to **hold the draft**, in quotes. "make it firmer" three turns after a
  recipe has no words to edit, and inventing a message is not an improvement;
- a draft about a person still gets its tone changed: the edit is the tone, not the content.

It is consulted from `fallback_chain.py` before the pools, in place of the search hedge.
"""
import re


# The words that ask for a tone rather than a thing. One list for reading the ask and for taking
# the tone words out again when the line is checked for a subject of its own.
FIRM = frozenset("""
firm firmer firmest firmly assertive stronger strongest direct directly blunt blunter
apologetic unapologetic no-nonsense stern serious
""".split())
POLITE = frozenset("""
polite politely courteous respectful nicer nice friendly friendlier warm warmer kinder kind
softer gentle gentler professional tactful diplomatic
""".split())
SHORT = frozenset("""
shorter short brief briefer concise tighter trim condensed
""".split())
FORMAL = frozenset("""
formal officially
""".split())
CASUAL = frozenset("""
casual chatty relaxed informal
""".split())

# The frames a tone ask arrives in, which are not content: "make it X", "can you make that a bit
# X", "say it X", "sounds X", "a version that is X", "in a X way".
FRAME = re.compile(
    r"\b(?:make|makes|making|say|sound|sounds|sounding|write|rewrite|word|put|say it|said|"
    r"again|version|tone|it|that|this|a|an|the|bit|more|less|much|very|really|far|too|"
    r"could|can|would|will|you|i|me|my|please|and|but|so|just|to|of|in|on|as|is|be|"
    r"need|want|like|something|text|message|email|note|letter|reply|draft|line|lines|words|"
    r"one|ones|now|then|instead|also|still|shorter|again)\b")

# The phrases that make a message soft, and what a firm version puts in their place. A firm
# message is the same facts with the apology, the hedge and the "whenever" taken out.
SOFT = (
    (r"\bi\s+was\s+(?:just\s+)?wondering\s+(?:if|whether)\b", "I need to know"),
    (r"\bi\s+just\s+wanted\s+to\s+(?:ask|check|say)\b", "I am writing about"),
    (r"\bwould\s+it\s+be\s+possible\s+to\b", "please"),
    (r"\bif\s+you\s+(?:get|have)\s+a\s+(?:chance|moment)\b", ""),
    (r"\bwhen\s+you\s+(?:get|have)\s+a\s+(?:chance|moment)\b", ""),
    (r"\bat\s+your\s+earliest\s+convenience\b", ""),
    (r"\bi\s+hope\s+you\s+(?:don't|do not)\s+mind\b", ""),
    (r"\bi\s+know\s+you(?:'re| are)\s+busy\b", ""),
    (r"\bsorry\s+to\s+(?:bother|trouble|disturb)\s+you\b", ""),
    (r"\bif\s+possible\b", ""),
    (r"\bif\s+you\s+wouldn't\s+mind\b", "please"),
    (r"\bjust\b", ""),
)
SOFT_WORDS = re.compile("|".join(one for one, _ in SOFT))

# What a firm message says at the end: the ask, and that an answer is wanted. No date is invented -
# the person's own date is the one thing the bot cannot make up, so it asks for it.
THE_ASK = re.compile(r"\?|\bplease\b|\bcan you\b|\bcould you\b|\bwould you\b|\blet me know\b",
                     re.I)
DATE_ASKED = re.compile(r"\b(?:by|before|on|for)\s+(?:monday|tuesday|wednesday|thursday|friday|"
                        r"saturday|sunday|the\s+\d+|\d+\s*(?:st|nd|rd|th)?\b|tomorrow|today|"
                        r"the\s+end\s+of\s+the\s+week|next\s+week|this\s+week|end\s+of\s+month)")

# Saying thank you is what a message needs to be polite, and a draft can end without it.
THANKED = re.compile(r"\b(?:thank(?:s|\s+you)|cheers|much\s+appreciated|grateful)\b")
CONTRACTIONS = ((r"\bi'm\b", "I am"), (r"\bi've\b", "I have"), (r"\bi'd\b", "I would"),
                (r"\bdon't\b", "do not"), (r"\bdoesn't\b", "does not"),
                (r"\bdidn't\b", "did not"), (r"\bit's\b", "it is"), (r"\bthat's\b", "that is"),
                (r"\bcan't\b", "cannot"), (r"\bwon't\b", "will not"), (r"\bwe're\b", "we are"),
                (r"\bthey're\b", "they are"), (r"\bhavent\b", "have not"),
                (r"\bhasnt\b", "has not"), (r"\bdont\b", "do not"), (r"\bcant\b", "cannot"),
                (r"\bim\b", "I am"), (r"\bive\b", "I have"))

HELLO = re.compile(r"^(?:hi|hey|hello|dear)\b[ ,]*", re.I)
SIGN_OFF = re.compile(r"\b(?:thanks|thank\s+you|cheers|kind\s+regards|many\s+thanks|regards)"
                      r"[\s.!]*$", re.I)


def _clean(line):
    low = " ".join(str(line or "").lower().replace("\u2019", "'").split())
    return re.sub(r"[^a-z' -]", " ", low)


# "less blunt" and "less rude" are a politeness ask whatever the word on its own says: the
# "less" turns the tone the other way, and a message that stops being blunt does not stop having
# the ask in it.
LESS = re.compile(r"\bless\s+([a-z']+)\b")
TURNED_OVER = {"blunt": "polite", "blunter": "polite", "rude": "polite", "abrupt": "polite",
               "aggressive": "polite", "harsh": "polite", "formal": "casual",
               "stiff": "casual", "wordy": "short", "long": "short", "soft": "firm",
               "soppy": "firm", "apologetic": "firm", "wordy": "short"}
# The words that only ever name a tone, so they are not mistaken for the subject of the line.
TONE_EXTRA = frozenset(set(TURNED_OVER) | set(TURNED_OVER.values()))


def _tones(low):
    """The tones the line names, in the order they are read."""
    turned = set()
    for word in LESS.findall(low):
        if word in TURNED_OVER:
            turned.add(TURNED_OVER[word])
    found = [name for name in ("firm", "polite", "short", "formal", "casual") if name in turned]
    for word in re.findall(r"[a-z']+", low):
        for name, group in (("firm", FIRM), ("polite", POLITE), ("short", SHORT),
                            ("formal", FORMAL), ("casual", CASUAL)):
            if word in group and name not in found:
                found.append(name)
    return found


def _is_tone_only(low):
    """True when nothing but a tone is named: no subject for anybody to look up."""
    left = [w for w in re.findall(r"[a-z']+", low)
            if w not in FIRM and w not in POLITE and w not in SHORT and w not in FORMAL
            and w not in CASUAL and w not in TONE_EXTRA and not FRAME.fullmatch(w)]
    # Anything left is a subject: "make the boiler message firm" is a drafting ask, not this.
    return not left


def _the_draft(text):
    """The message the bot handed over, or "" when the last reply held none."""
    text = str(text or "")
    # Only the quotation marks a draft comes wrapped in. A single quote is an apostrophe in half
    # the sentences the bot writes ("the landlord's job, so if they ignore you…"), and reading
    # that as the draft handed over half a sentence back as if it were the person's message.
    for pattern in (r'"([^"]{8,400})"', r"\u201c([^\u201d]{8,400})\u201d"):
        found = re.search(pattern, text)
        if found:
            return " ".join(found.group(1).split())
    return ""


def _the_draft_near(memory):
    """The draft in the last reply, or in the one before it.

    A person says thank you between the draft and the change of tone ("cheers - can you make it
    shorter"), and the words to edit are still exactly as the bot wrote them. Older than that and
    the chat has moved on, so nothing is picked up.
    """
    turns = list(memory.get("turns") or [])[-2:]
    for turn in reversed(turns):
        draft = _the_draft((turn or {}).get("bot"))
        if draft:
            return draft
    return ""


def _firm(draft):
    """The same message with the apology, the hedge and the "whenever" taken out."""
    said = draft
    for pattern, instead in SOFT:
        said = re.sub(pattern, instead, said, flags=re.I)
    said = " ".join(said.split())
    said = SIGN_OFF.sub("", said).strip()
    if not THE_ASK.search(said):
        said = said.rstrip(" .;,") + ". Please confirm when it will be done"
    said = said.rstrip(" .;,")
    return said if said.endswith(("?", "!", ".")) else said + "."


def _polite(draft):
    """The same message with one courtesy on it: the ask is already there, the thanks are not."""
    said = SIGN_OFF.sub("", " ".join(draft.split())).strip()
    if not re.search(r"\bplease\b", said, re.I) and THE_ASK.search(said):
        said = said.rstrip(" .;,")
        if said.endswith("?"):
            said = said[:-1].rstrip() + ", please?"
        else:
            said = said + ", please"
    elif not THE_ASK.search(said):
        # A draft with no ask in it yet (the bot handed over a statement) still gets one: a
        # message that only says what is wrong is the half that starts the argument.
        said = said.rstrip(" .;,") + ". Please let me know what happens next"
    said = said.rstrip(" .;,")
    if not THANKED.search(said):
        said = said + (" Thank you." if said.endswith(("?", "!")) else ". Thank you")
    return said if said.endswith(("?", "!", ".")) else said + "."


def _short(draft):
    """The first sentence and the ask, which is what a shorter version keeps."""
    parts = [p.strip() for p in re.split(r"(?<=[.?!])\s+", " ".join(draft.split())) if p.strip()]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    asked = [p for p in parts[1:] if THE_ASK.search(p)]
    return " ".join([parts[0]] + asked[:1])


def _formal(draft):
    said = " ".join(draft.split())
    for pattern, instead in CONTRACTIONS:
        said = re.sub(pattern, instead, said, flags=re.I)
    said = HELLO.sub("Dear Sir or Madam, ", said)
    if not said.startswith("Dear"):
        said = "Dear Sir or Madam, " + said
    said = SIGN_OFF.sub("Yours faithfully.", said)
    return " ".join(said.split())


def _casual(draft):
    said = HELLO.sub("Hi, ", " ".join(draft.split()))
    said = SIGN_OFF.sub("Cheers.", said)
    return " ".join(said.split())


# What the bot says. Each line names the change in the words the person used, hands the draft
# back, and asks for the one thing only they know - the date they want an answer by - rather than
# inventing it.
FIRM_LINES = (
    'Firm is the same facts with the apology and the "just" taken out: "{draft}" That leads with '
    "the fact and ends with the ask. Give me the date you want an answer by and I will put it in.",
    'Here it is with the soft words out: "{draft}" The boiler and the two weeks do the arguing; '
    "a firm message only needs a date on the end - say one and I will write it in.",
    'Stripped back: "{draft}" No apology, no "whenever you get a chance", and the ask is the last '
    "sentence. Tell me the date you want to name and I will put it in for you.",
)
POLITE_LINES = (
    'One courtesy does it: "{draft}" That is the same ask with a please and a thank you round it, '
    "which is all politeness is on a message like this.",
    'Politer, same content: "{draft}" The please goes on the ask and the thanks on the end - any '
    "more than that and the ask gets lost in it.",
    'With the courtesy in: "{draft}" Say the thing plainly and put the please and thank you around '
    "it; that reads better than a paragraph of softening.",
)
SHORT_LINES = (
    'Cut to the two sentences that do the work: "{draft}" A message like this only needs what is '
    "wrong and what you want - say if you want the date in it and I will add one line more.",
    'Shorter, same ask: "{draft}" Everything after the first sentence and the ask was doing '
    "nothing, so it is gone.",
)
FORMAL_LINES = (
    'Formal is no contractions and the full form of address: "{draft}" If you have a name and an '
    "address for them I will put those in instead.",
    'In the formal register: "{draft}" Same facts, no shortened words, and the salutation and '
    "sign-off to match.",
)
CASUAL_LINES = (
    'Casual keeps the facts and drops the ceremony: "{draft}" That is how you would say it to a '
    "neighbour rather than a council.",
    'Loosened off: "{draft}" Nothing in the meaning changed - only the greeting and the sign-off.',
)
# "firm but polite" is both, and the firm version with its please kept is what that asks for.
BOTH_LINES = (
    'Firm but polite is the ask in plain words with the courtesy kept: "{draft}" The fact first, '
    "then please, then the date. Give me the date and I will put it in.",
    'Both at once: "{draft}" Nothing soft, nothing rude - the facts, a please, and the ask at the '
    "end. Say the date you want and it is ready to send.",
)


# The draft is already in the tone asked for. Handing it back with "here it is firmer" on top of
# identical words is a lie, so the reply says the draft already reads that way and names the one
# thing it is still short of - which is what the person needed to hear.
ALREADY = {
    "firm": 'That draft already reads firm: "{draft}" The facts are there and the ask is in it. '
            "The one thing it is short of is the date you want an answer by.",
    "polite": 'It already reads politely: "{draft}" There is a request in it and no edge. If you '
              "want it warmer still, say how you know them and I will open with that.",
    "short": 'That is as short as it goes without losing the facts: "{draft}" The date and the '
             "thing that is wrong are the parts that have to stay.",
    "formal": 'That is already the formal version: "{draft}" What it still needs is their name '
              "and address at the top rather than a greeting you make up.",
    "casual": 'That is already casual enough: "{draft}" Nothing in it sounds like a letter.',
}


def retone(memory, line):
    """The draft just given, said again in the tone this line asks for, or None."""
    draft = _the_draft_near(memory)
    if not draft:
        return None
    low = _clean(line)
    if not low or not _is_tone_only(low):
        return None
    tones = _tones(low)
    if not tones:
        return None
    if "firm" in tones and "polite" in tones:
        pool, draft = BOTH_LINES, _polite(_firm(draft))
    elif "firm" in tones:
        pool, draft = FIRM_LINES, _firm(draft)
    elif "short" in tones:
        pool, draft = SHORT_LINES, _short(draft)
    elif "formal" in tones:
        pool, draft = FORMAL_LINES, _formal(draft)
    elif "casual" in tones:
        pool, draft = CASUAL_LINES, _casual(draft)
    else:
        pool, draft = POLITE_LINES, _polite(draft)
    draft = " ".join(draft.split()).strip()
    if not draft:
        return None
    # A draft the tone did not change is not handed back as a new message, but it is not nothing
    # to say either: the draft is already like that, and saying so (and what it is still missing)
    # is a real answer. It was a search hedge before.
    if draft.strip(" .;,").lower() == _the_draft_near(memory).strip(" .;,").lower():
        return ALREADY.get(tones[0], ALREADY["polite"]).format(draft=draft)
    turns = memory.get("turns") or []
    seed = len(turns) * 7919 + sum(ord(c) for c in low)
    import random
    return random.Random(seed).choice(pool).format(draft=draft)
