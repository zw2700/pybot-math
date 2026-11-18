"""A standing situation of theirs, said on its own, is where they are starting from.

People open a conversation with a stranger with the fact that decides what help is worth giving:
"i rent", "im a carer", "im self employed", "im on benefits", "im disabled", "im divorced".
Today each of those is read as something it is not:

- "im a tenant", "im a carer", "im a single parent" reach the role pool, which asks about it as
  a job - "Tenant - good to know. What do you like most about it?";
- "im disabled" and "im self employed" reach the small-day pool, which answers a day that went
  by - "Good to hear. What was the best bit?" to somebody saying they are disabled;
- "im divorced" is read as bad news - "I'm sorry - that's frustrating";
- "i rent", "im on benefits" reach the receipt - "Thanks for telling me", which files the fact
  and gives the person nothing.

None of those is a reply to the situation. What a friend does with it is take it in, say the one
thing it changes, and ask the question that opens the next turn. That is what this module does,
with its own lines for each kind, so the reply is about their situation rather than any message.

Only the whole line counts, and only the simple forms of it. "im a carer for my mum who has
dementia" is about her and keeps its own reading, as does "i rent and the boiler is broken",
which is about the boiler.
"""

import re

# How people type the copula.
_AM = r"(?:i\s*m|im|iam|i\s+am)"
_ARE = r"(?:we\s*'?\s*re|we\s+are)"

# The words that end a line without adding anything to it: "im a carer tbh", "i rent lol".
_TONE = re.compile(
    r"(?:\s+(?:tbh|tho|though|now|anyway|actually|really|literally|honestly|i\s+suppose|"
    r"i\s+guess|still|also|too|by\s+the\s+way|btw|atm|at\s+the\s+moment|lol|ha|haha|"
    r"lmao|so\s+yeah|yeah|innit|mate|dude))+$")

# The situations worth their own reply, each with the lines it can be answered by: three, so a
# conversation that comes back to the same situation twice does not hear the same sentence.
_SITUATIONS = (
    # Renting decides who has to act on the building, which is why it is worth taking in first.
    ("tenant", re.compile(
        rf"^(?:{_AM}|{_ARE})\s+(?:a\s+|an\s+)?(?:private\s+|council\s+|housing\s+association\s+)?"
        r"(?:tenant|tenants|renter|renters|lodger|lodgers)$"
        r"|^(?:i|we)\s+rent(?:ing)?(?:\s+(?:a|an|my|our|the)\s+"
        r"(?:flat|house|home|place|bungalow|room|council\s+flat|housing\s+association\s+flat))?$"
        r"|^(?:i|we)\s+pay\s+rent$"), (
        "Good to know - renting decides who has to act when something in the place goes wrong. "
        "What's on your mind?",
        "Right, so you rent. What are you trying to sort out?",
        "Renting, noted. What would you like a hand with?",
    )),
    # Caring is work with no clocking off, and the useful question is whose need it is.
    ("carer", re.compile(
        r"^(?:i\s*m|im|iam|i\s+am)\s+(?:a\s+|an\s+)?(?:unpaid\s+|full[- ]time\s+|part[- ]time\s+|"
        r"young\s+|family\s+)?carer$"
        r"|^(?:i\s*m|im|iam|i\s+am)\s+(?:a\s+)?carer\s+for\s+(?:a\s+)?"
        r"(?:relative|someone|somebody|family)$"), (
        "Carers carry a lot that nobody gets to see. Is it help for you you're after, or "
        "something for the person you look after?",
        "Good to know. What would help most - something for you, or something for them?",
        "Caring is a job with no clocking off. What's the hard bit at the moment?",
    )),
    ("single_parent", re.compile(
        rf"^(?:{_AM})\s+(?:a\s+|an\s+)?(?:single|lone|solo)\s+"
        r"(?:parent|mum|mom|dad|mother|father|mam)$"), (
        "One pair of hands for all of it. What's the part that's hardest at the moment?",
        "Good to know - that's a lot to hold on your own. What are you trying to sort out?",
        "Right. What would help most this week?",
    )),
    ("student", re.compile(
        rf"^(?:{_AM})\s+(?:a\s+|an\s+)?(?:(?:mature|full[- ]time|part[- ]time|postgrad|"
        r"phd|undergrad|university|uni|college)\s+)*student$"), (
        "Student, then. What are you trying to work out?",
        "Good to know. What's the thing on your mind?",
        "Student life - what would help?",
    )),
    # Owning the place makes the fixing theirs to arrange, which is the fact worth saying back.
    ("owner", re.compile(
        rf"^(?:{_AM})\s+(?:a\s+|an\s+)?home\s*owner$"
        r"|^(?:i|we)\s+own\s+(?:my|our|the)\s+(?:house|flat|home|place)$"
        r"|^(?:i|we)\s+own\s+(?:it|mine|ours)$"), (
        "Good to know - owning it means the repairs are yours to arrange. What's on your mind?",
        "So it's your own place. What are you trying to sort out?",
        "Home owner, noted. What would you like a hand with?",
    )),
    ("self_employed", re.compile(
        rf"^(?:{_AM})\s+(?:a\s+)?self[- ]?employed$"
        r"|^(?:i|we)\s+work\s+for\s+(?:myself|ourselves)$"
        rf"|^(?:{_AM})\s+(?:a\s+)?(?:freelancer|contractor|sole\s+trader)$"), (
        "Self-employed, so no payroll to fall back on and nobody to ask upstairs. What are you "
        "trying to sort out?",
        "Working for yourself, then. What's on your mind?",
        "Good to know. What would help most?",
    )),
    ("benefits", re.compile(
        rf"^(?:{_AM}|{_ARE})\s+on\s+(?:benefits|universal\s+credit|uc|tax\s+credits|"
        r"pip|esa|jsa|income\s+support|housing\s+benefit)$"), (
        "Good to know - the rules on that are worth checking before you decide anything. What "
        "are you trying to work out?",
        "Right. What are you trying to sort out?",
        "Noted. What's the thing you need a hand with?",
    )),
    # Said flatly this is a fact about the person, not a day that went well.
    ("disabled", re.compile(
        rf"^(?:{_AM})\s+(?:disabled|a\s+disabled\s+person)$"
        r"|^(?:i|we)\s+have\s+(?:a\s+)?disabilit(?:y|ies)$"
        rf"|^(?:{_AM})\s+(?:registered\s+)?(?:blind|deaf|partially\s+sighted)$"), (
        "Good to know, and I won't assume what it means for you. What do you need a hand with?",
        "Thanks for telling me - it's useful to know rather than guess. What would help most?",
        "Right, noted. What's on your mind?",
    )),
    ("separated", re.compile(
        rf"^(?:{_AM})\s+(?:divorced|separated|a\s+divorcee|newly\s+single|recently\s+single)$"
        r"|^(?:i|we)\s+got\s+divorced$"), (
        "Right - that's a lot to carry, and a pile of admin along with it. What needs sorting "
        "first?",
        "Good to know. What's on your mind about it?",
        "Noted. What would you like a hand with?",
    )),
)

_POOLS = {kind: lines for kind, _pattern, lines in _SITUATIONS}


def _line(clean):
    """The line as this reader wants it: lower case, no edge punctuation, no tone on the end."""
    said = str(clean or "").replace("\u2019", "'").strip().lower()
    said = said.strip(" .,!;:-\"'")
    said = re.sub(r"\s+", " ", said)
    while True:
        trimmed = _TONE.sub("", said)
        if trimmed == said:
            return said
        said = trimmed


def reads_as_situation(clean):
    """The kind of situation the whole line is, or None.

    Whole lines only: a line that goes on to say something else ("i rent and the boiler is
    broken", "im a carer for my mum who has dementia") is about that something else.
    """
    said = _line(clean)
    if not said or "?" in said:
        return None
    for kind, pattern, _lines in _SITUATIONS:
        if pattern.match(said):
            return kind
    return None


def pool(clean):
    """The lines that answer this situation, or None when the line is not one."""
    kind = reads_as_situation(clean)
    if not kind:
        return None
    return _POOLS[kind]
