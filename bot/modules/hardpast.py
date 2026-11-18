"""A hard thing in the past is not a small account of the day.

One fresh process a line, on main:

    my dad was an alcoholic        -> "Sounds alright. Anything good in it?"
    i was homeless for a bit       -> "Good to hear. What was the best bit?"
    my marriage ended two years ago -> "Nice one. How did the rest of it go?"
    my dad walked out when i was ten -> "Sounds alright. Anything good in it?"

Reported by ample-fan on `#routing` (94443). The person has just said the worst thing in their
life, flat, as where they come from, and the bot claps.

Every guard there passes the line: the subject is the person's own ("my dad", "my marriage"), the
verb is a past tense ("was", "ended", "walked"), the line is short, and the bad-day list is a list
of one bad day - hospital, sacked, a row - rather than of a life event said once.

So this is a band of its own, not a reading inside the small-day pool: the words below name
something that is still the person's history whatever else the line says, and a pool of the
greeting's must not be the answer to any of them.

Under `answers` (0) and every module with something of its own, because a card built for the line
is a better answer than this: "my dad was a heavy drinker" keeps the calm, sober moment, and
"i had a crash on the motorway" keeps the roadside card. Above the greeting module's pools
(-1000), which is what these lines were reaching. A line that asks something ("is my dad an
alcoholic") is not this module's: nothing is being told, so the hedge and the cards keep it.

Two things are fenced out of it, and both were found by a reviewer rather than by me:

- **The hard thing has to be theirs.** A noun and a past tense say nothing about whose the prison
  is, so "the prison was built in 1800" and "the divorce rate went down last year" were being
  condoled with. The thing hangs on the person when a possessive or a family word stands in front
  of it ("my dad", "mum", "our marriage") or when the person is the subject ("i was homeless",
  "i went to prison", "we were"). Anything else is the world's, and this module passes on it.
- **A loss is the grief module's.** "my wife had a miscarriage last year" and "my baby was
  stillborn" had a warmer line already ("I'm so sorry. That's a real loss"), and this pool took it
  away, so a death, a lost pregnancy and a widow keep their own pool.
- **A blow is the safety modules'.** "my dad used to hit me" and "he beat me up" had a line that
  offers something ("Sorry to hear that. What would help most right now?"), and a pool that only
  asks about it is the weaker answer to the one line in a chat where somebody was hurt, so the
  violence words are not in the list at all.

The words of the pool are said by `pick`, which keeps the last one it said out of the way, and
none of them opens on "Noted": that is the store's receipt word, the very thing this module
exists to stop answering these lines. None of them says anything about the person's present
either - "it is still in your week", "it still comes up", "how much of it is around now" were
claims about today that the line may have just contradicted, so every line is about the past and
leaves the door open without a tense.

- **A hard thing the line says is over is not this module's.** "i went to prison years ago but i
  have a job now", "i was in rehab in 2019 and im clean since", "my dad was an alcoholic but hes
  been dry 20 years" are one sentence about a hard past and a good present, and a pool that has
  nothing to say about the ending must not answer the sentence that has one (`A_CLOSED`).

A module that answers only the lines it is good at passes on everything else: `respond` returns
None on every other line and the bot answers it as it did before.
"""
import re

from ..compose import pick

# The words that make the line a hard thing in the past rather than a day that went one way or
# the other. A list of nouns and not a shape, because that is what the fault is: the shape of the
# line is the shape of every small day ("i got my hair cut" is subject, past tense, short), and
# only the thing itself tells the two apart.
A_HARD_PAST = re.compile(
    r"\b(?:alcoholic|alcoholics|drinker|drinkers|addict(?:s|ed|ion)?|overdos(?:e|ed)|rehab|"
    r"prison|jail|divorce[ds]?|custody|abusive|abuser|widow|widowed|widower|estrang\w*|"
    r"homeless|bankrupt\w*|gambling|dementia|stillborn|stillbirth|miscarriage|miscarried|"
    r"car crash|in a crash|had a crash|bad crash|fatal crash|"
    r"marriage ended|marriage broke|relationship ended|walked out|left us)\b")

# A hard thing in the past is over. News of the same thing happening now is not this module's:
# "we are getting a divorce" and "she asked for a divorce last tuesday" are the worst week of
# somebody's life, told as it happens, and the greeting's own reading of a hard day answers them
# better ("That's a hard thing to hear. Where are you with it - has it sunk in yet?"). So the
# thing has to be framed as the past - told with a past tense and a time it is over - and a line
# that is the news arriving is left to the modules that read a bad day.
A_THE_PAST = re.compile(
    r"\b(?:was|were|had been|used to|grew up|growing up|as a kid|when i was|went to|"
    r"walked out|ended|ago|for a bit|for a while|for years|back then|in the end|at the time|"
    r"last (?:year|summer|winter|decade)|years back|after that)\b")
A_NEWS_ARRIVING = re.compile(
    r"\b(?:getting|going through|just told|just said|just heard|asked for|wants|wanting|"
    r"is leaving|has asked|separating|divorcing|this morning|tonight|right now|at the moment|"
    r"today)\b")

# ...and the line can say the hard thing is behind them. "i went to prison years ago but i have a
# job now" is one sentence about a hard past and a good present, and the pool's own words answered
# the first half as if the second were not there ("it is still in your week"). The closing clause
# is read the way the news arriving is, and the line goes back to the modules that answer it: a
# pool that has nothing to say about the ending must not answer the sentence that has one.
A_CLOSING_WORD = r"(?:fine|okay|ok|good|better|clean|dry|sober|sorted|happy|healthy|stable|" \
                  r"working|employed|a job|job|a house|a flat|a home|back on my feet|" \
                  r"still friends|still together|paid off|all paid)"
A_CLOSED = re.compile(
    r"\b" + A_CLOSING_WORD + r"\b[^.!?]{0,24}?\b(?:now|since|these days|any ?more)\b"
    r"|\b(?:now|since|these days)\b[^.!?]{0,24}?\b" + A_CLOSING_WORD + r"\b"
    r"|\b(?:dry|clean|sober|straight|off it)\b[^.!?]{0,16}?\b\d+\s*(?:years?|months?|decades?)\b"
    r"|\b(?:never looked back|put it behind me|put that behind me|moved on from it|"
    r"turned (?:it|things|my life) around|came out the other side|over it now|past it now|"
    r"in a better place|still friends|no longer)\b")

# The hard thing has to be the person's own. `A_HARD_PAST` reads the noun and `A_THE_PAST` reads any
# past marker, and neither said whose the prison was, so "the prison was built in 1800" and "the
# divorce rate went down last year" were answered "That is a heavy thing to have lived with". The
# thing hangs on the person in one of two ways, and one of them has to be there: a possessive or a
# family word in front of it ("my dad was an alcoholic", "mum was an alcoholic", "our marriage"),
# or the person themselves as the subject ("i was homeless", "i went to prison", "we were").
A_OWNED = frozenset("""
    my our his her their your mum mums mum's dad dads dad's mother father brother sister son
    daughter husband wife partner ex nan gran granny grandma grandad grandpa uncle aunt cousin
    parents family stepdad stepmum
""".split())
# Between the person and the thing there is nothing but a verb, a preposition, an article or a
# time word. A noun in between means the thing is not theirs: "i saw a documentary about prison".
A_BETWEEN = frozenset("""
    i we ive weve been was were am had have has got did do done went never once really badly
    eventually finally long time terrible bad hard worst back then ago after before so that
    this it there with from at to a an the in into through out on off for of and but also both
    years year months weeks days month week twice again now still just
""".split())
A_SUBJECT = frozenset(("i", "we", "ive", "weve"))

# A loss is a bereavement, not a hard stretch of life told flat, and the loss pool answers it in
# its own words ("I'm so sorry. That's a real loss, and it deserves to be taken seriously"). A
# pregnancy lost, a death and a widow are that pool's, so this one stands aside for them: the same
# fence the card lines get, and for the same reason - a better answer already exists.
A_LOSS = re.compile(
    r"\b(?:died|dies|dying|death|dead|passed away|funeral|buried|miscarriage|miscarried|"
    r"stillborn|stillbirth|widow|widows|widowed|widower|bereaved|bereavement)\b")


# Said back when the line holds something heavy from the past. Not a cheer, not a receipt, and no
# question about why today: the line already said as much as the person wanted. Each line leaves
# a door open without asking them to walk through it.
A_HARD_PAST_SAID = (
    "That is a heavy thing to have lived with. Say more about it if you want to.",
    "That is not a small thing to carry. I'm listening if you want to say more.",
    "That one leaves a mark. Go on if you want to.",
    "That is a lot to have been through. Tell me as much or as little as you like.",
)

# Under every module with an answer for the line and over the greeting's pools. No module raises
# its band to win a turn; this one is here because these lines had nothing else to answer them.
PRIORITY = -980


def _hangs_on_the_person(clean, at):
    """True when the hard thing starting at `at` is the person's own rather than the world's."""
    before = re.findall(r"[a-z']+", clean[:at])[-6:]
    for word in before[-4:]:
        if word in A_OWNED or (word.endswith("'s") and word[:-2] in A_OWNED):
            return True
    low = [word.replace("'", "") for word in before]
    seen = [i for i, word in enumerate(low) if word in A_SUBJECT]
    if seen:
        return all(word in A_BETWEEN for word in low[seen[-1] + 1:])
    return False


def _the_hard_thing(text, memory=None):
    """The tidied line when it is a hard thing in the past told flat, else ""."""
    clean = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not clean or "?" in clean:
        return ""
    # A line that asks something is not a line that tells it. `kind` is the understanding
    # engine's reading of the whole line, so it catches the ask typed without a question mark
    # ("is my dad an alcoholic", "was your dad an alcoholic too") that a "?" test cannot.
    understood = (memory or {}).get("understood") or {}
    if isinstance(understood, dict) and str(understood.get("kind") or "") == "question":
        return ""
    if not A_HARD_PAST.search(clean):
        return ""
    if not any(_hangs_on_the_person(clean, found.start())
               for found in A_HARD_PAST.finditer(clean)):
        return ""
    if A_NEWS_ARRIVING.search(clean) or not A_THE_PAST.search(clean):
        return ""
    if A_LOSS.search(clean):
        return ""
    if A_CLOSED.search(clean):
        return ""
    return clean


def takes_as_it_comes(text, memory):
    """The claim is one reading of the whole line, so it is declared as well as banded."""
    try:
        return bool(_the_hard_thing(text, memory))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


def respond(text, memory):
    """What a friend says to a hard thing from the past, or None on any other line."""
    try:
        clean = _the_hard_thing(text, memory)
        if not clean:
            return None
        return pick(A_HARD_PAST_SAID, memory, clean)
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return None
