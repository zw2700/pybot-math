"""A line that hands the job to the bot, when the bot has no hands, no browser and no account.

"search for flights for me", "book the tickets", "send me the recipe", "save this for later",
"add milk to my shopping list", "order more coffee on the app". Each of those was answered with
one of the composer's flat readings - "Got it. Is there anything you'd like a hand with?", "I'm
listening - say more if it helps", "Thanks for telling me - I'm here if you want to dig into any
of that" - and none of them is true, because nothing was done and nothing was even understood.
The person is not making small talk. They have handed over an errand.

The honest answer has three parts, in this order, because a refusal on its own leaves them where
they started (STYLE.md, "Not knowing, honestly"):

1. what the bot cannot do, in a few words - no hands, no browser, no account, no card, and no
   list that outlives the chat;
2. what it can do instead, which is always something: get the words right, weigh the price, sort
   the items, work out what to compare;
3. the one place the rest happens - their app, their site, their notes, the send button.

Four pools, one per kind of errand, because the way out differs: a search needs the details
before the site can be opened, a booking needs the small print read before the money goes, a
message needs the words, and a list needs to live somewhere that survives.

Some of these errands have since been given their own answer elsewhere - a calendar line for "save
this for later", a booking line for "book the tickets", a printer line for "print this out". Those
are better than a general pool, and the queue in `greeting.py` reaches them first; this file only
ever replaces one of the composer's flat readings, so it stands down on every line that already
has an answer. What is left for it is the errand nobody has covered: the live look-up ("search
for flights for me", "check the price for me online") and the thing meant to leave here ("send me
the recipe"), both of which still come back with "I'm listening - say more if it helps" on main.

Narrow on purpose. The ask must be an order at the front of the line ("book the tickets"), or the
same order with the asking put back in ("can you book the tickets for me"). A question about how
to do the thing ("how do i book a flight"), a weigh-up ("should i book now"), a line about
something already done ("i booked the tickets"), anything with a body, a symptom or a doctor in
it, and the emergency verbs (call, ring, dial, 999) all keep their own answer and never reach
this file. Only four of the composer's flat readings are replaced.
"""
import re

from . import fallback_data, pick

# The composer's flat readings. Each of them fits any message at all, which is what makes them
# the ones worth replacing here.
_FLAT = (fallback_data.NEUTRAL, fallback_data.A_THING_SEEN_TO, fallback_data.A_THING_DONE,
         fallback_data.A_SMALL_DAY)

_ASKING_BACK = re.compile(
    r"^\s*(?:(?:please|pls|plz|just|ok|okay|now|and|also|so|then|hi|hey)\s+)*"
    r"(?:(?:can|could|would|will)\s+(?:you|u)\s+(?:please\s+|just\s+|kindly\s+|also\s+)*"
    r"|(?:i\s+(?:want|need|would\s+like)\s+you\s+to\s+))?")

# The errands, by what the person wants to happen rather than by word alone: a search wants the
# live answer, a booking wants somebody to take the money, a message wants to leave here, and a
# list wants to still exist tomorrow.
_A_SEARCH = re.compile(
    r"^\s*(?:(?:please|pls|plz|just|ok|okay|now|and|also|so|then)\s+)*"
    r"(?:(?:can|could|would|will)\s+(?:you|u)\s+(?:please\s+|just\s+|kindly\s+|also\s+)*)?"
    r"(?:search|look\s+(?:it\s+)?up|look\s+for|google|browse|compare|check\s+(?:the\s+)?"
    r"(?:price|prices|times|flights|trains|availability))\b")

_A_SPEND = re.compile(
    r"^\s*(?:(?:please|pls|plz|just|ok|okay|now|and|also|so|then)\s+)*"
    r"(?:(?:can|could|would|will)\s+(?:you|u)\s+(?:please\s+|just\s+|kindly\s+|also\s+)*)?"
    r"(?:book|reserve|order|buy|purchase|pay|top\s+up|renew|cancel|check\s+(?:me\s+)?in|"
    r"get\s+me\s+(?:a\s+)?(?:ticket|table|seat|room))\b")

_A_MESSAGE_OUT = re.compile(
    r"^\s*(?:(?:please|pls|plz|just|ok|okay|now|and|also|so|then)\s+)*"
    r"(?:(?:can|could|would|will)\s+(?:you|u)\s+(?:please\s+|just\s+|kindly\s+|also\s+)*)?"
    r"(?:send|email|text|forward|share|print|post|mail|message)\b")

_A_LIST = re.compile(
    r"^\s*(?:(?:please|pls|plz|just|ok|okay|now|and|also|so|then)\s+)*"
    r"(?:(?:can|could|would|will)\s+(?:you|u)\s+(?:please\s+|just\s+|kindly\s+|also\s+)*)?"
    r"(?:save|keep|store|note|jot|add|put|write\s+(?:it|this|that)\s+down|"
    r"make\s+a\s+note|set\s+(?:a|an)\s+(?:reminder|alarm)|"
    r"remind\s+(?:me|us)\s+to|remember\s+(?:that|to))\b")

# The order has to be about their own errand, so the object is theirs or named: "send me the
# recipe", "book the tickets", "add milk to my list". A verb with nothing after it is a fragment,
# and a fragment gets the nod it always got.
_THEIR_ERRAND = re.compile(
    r"\b(?:me|my|mine|our|ours|us|for\s+me|for\s+us|this|that|these|those|it|them|"
    r"(?:the|a|an)\s+\w+)\b")

# Not the bot's errand: a how-to, a weigh-up, a complaint about something already done, a line
# about somebody else's errand, and the always-answered things (a body, a symptom, a doctor, an
# emergency). The emergency verbs are not in any pool above, and this is the second fence.
_KEEP_OUT = re.compile(
    r"\b(?:how\s+(?:do|can|should|would|to)\b|what\s+should|should\s+i|shall\s+i|"
    r"is\s+it\s+worth|worth\s+it|do\s+you\s+think|"
    r"i\s+(?:have\s+|already\s+)?(?:booked|ordered|bought|paid|sent|saved|added)|"
    r"i\s+(?:did|tried)|my\s+(?:mum|dad|son|daughter|friend|husband|wife|partner|boss|carer|"
    r"neighbour|brother|sister|nan|gran|grandad|child)\s+(?:has|have|wants|asked|said)|"
    r"ambulance|999|911|112|A&E|a\s*&\s*e|doctor|gp|surgery|nurse|pharmacist|chemist|"
    r"hospital|pain|rash|lump|bleeding|blood|breath|chest|dose|medicine|tablet|"
    r"an\s+email\s+(?:from|about)|a\s+(?:text|letter|email)\s+(?:from|about)|"
    r"send\s+my\s+(?:love|regards|wishes|thanks|best)|love\s+to\b|"
    r"(?:give|send)\s+(?:them|him|her)\s+my\b)")

# What the bot does instead, per errand. Each line names the limit in a few words, then the part
# that is still theirs to have, then the one place the rest happens.
A_NO_SEARCH = (
    "Nothing here can search the web - no browser on this side. Say what matters most about "
    "{what} and I'll help you work out what to compare; the site or app itself has the rest.",
    "I can't look anything up live, sorry. Tell me what you need to know about {what} and I'll "
    "say what to look for and what to ignore; whoever sells it has today's version.",
    "No search from here - I only know what is in my own head, and none of it changes today. Name "
    "the details that matter about {what} and I'll narrow it down before you open the site.",
)

A_NO_SPEND = (
    "I can't book, order or pay for anything - no account, no card, no hands. Do it in their app "
    "or on their site, and tell me the price first: I'll say whether it looks fair and what to "
    "check before you pay.",
    "Nothing on my side can hold a booking or take money. Read their cancellation line before you "
    "click buy - it is the one part of this that costs you later - and say what you are buying "
    "and I'll say what to watch.",
    "That one needs your account, not me: I can't reach a basket or a booking form. Tell me what "
    "it costs and what it covers, and I'll help you work out whether the dearer one earns its "
    "money.",
)

A_NO_SEND = (
    "I can't send or print anything - nothing leaves this chat. I'll get {what} right here "
    "instead, in full; copying it across is the one press on your side.",
    "No email, no text, no printer on my side, sorry. What I can do is get {what} exactly right "
    "here; pasting it over is the last step, and it is yours.",
    "Nothing here can post or send. I'll write {what} out so it is ready to go - the copy and the "
    "send are the two presses on your end.",
)

A_NO_LIST = (
    "Nothing here keeps a list between chats - every chat starts fresh, so what you put here does "
    "not come back tomorrow. Write it where you'll see it (your phone's notes, a paper by the "
    "door) and tell me the items: I'll help you sort them.",
    "I can't save anything, sorry - there is nowhere on my side for it to live. Say the items out "
    "loud here and I'll help you order and trim the list; then keep it in your own notes.",
    "No memory of a list once we stop talking. Give me the lot and I'll group them by where they "
    "are in the shop; your notes app is the thing that will still have it tomorrow.",
)


# A reply that asks for what the line already said is the stock line in a longer coat: "send me
# the recipe for soda bread" answered with "say which one". So the words after the errand verb are
# said back and the pools take them as `{what}`. When the line names nothing there ("send it to
# me", "print that out"), `{what}` is "it" and nothing false is claimed.
_THE_VERB_AND_THEN = re.compile(
    r"^\s*(?:(?:please|pls|plz|just|ok|okay|now|and|also|so|then)\s+)*"
    r"(?:(?:can|could|would|will)\s+(?:you|u)\s+(?:please\s+|just\s+|kindly\s+|also\s+)*)?"
    r"(?:search|look\s+(?:it\s+)?up|look\s+for|google|browse|compare|check|"
    r"send|email|text|forward|share|print|post|mail|message|"
    r"book|reserve|order|buy|purchase|pay|top\s+up|renew|cancel|"
    r"save|keep|store|note|jot|add|put|write\s+(?:it|this|that)\s+down)\b\s*", re.I)
# What is left after the verb, minus the bits that belong to the verb or say who it is for: the
# "me" in "send me the recipe", the "for" in "search for flights", the "out" in "print this out",
# and the "online"/"please"/"for me" that trail the ask.
_A_LEADING_PREPOSITION = re.compile(r"^\s*(?:for|about|on|at|into|up|out|down|to)\b\s*", re.I)
_THE_ADDRESSEE = re.compile(r"^\s*(?:me|us)\b\s*", re.I)
_THE_TAIL_OF_THE_ASK = re.compile(
    r"\s+(?:for\s+(?:me|us)|to\s+(?:me|us)|please|pls|now|asap|online|thanks|ta|cheers|"
    r"out|up|down|here)\s*[.!?]*$", re.I)
# A pronoun is not a name: "send it to me" and "print this out" say nothing the reply can echo.
_A_MERE_PRONOUN = frozenset(("it", "that", "this", "them", "those", "these", "one", "things"))

# The remainder is the person's own words, so it faces them when it is said back: "search for my
# boiler manual" is answered "... about my boiler manual" on a bot that says "your" everywhere
# else it quotes the person ("Search for your flight times - noted."). The flip is the same one
# `fallback._yours()` makes; it is done here because this file fills the remainder into a pool.
_MINE = re.compile(r"\b(my|our|mine|ours)\b", re.IGNORECASE)
_YOURS = {"my": "your", "our": "your", "mine": "yours", "ours": "yours"}


def _facing_them(phrase):
    """The person's own phrase turned to face them: "our flight times" -> "your flight times"."""
    return _MINE.sub(lambda found: _YOURS[found.group(1).lower()], phrase)


def _what_was_asked_for(clean):
    """The thing the person named in their errand, or "it" when they named nothing."""
    after = _THE_VERB_AND_THEN.sub("", clean or "", count=1)
    after = _THE_ADDRESSEE.sub("", after or "", count=1)
    for _ in range(4):
        before = after
        after = _A_LEADING_PREPOSITION.sub("", after, count=1).strip()
        after = _THE_TAIL_OF_THE_ASK.sub("", after).strip(" .!?,")
        if after == before:
            break
    words = [w for w in after.split() if w]
    if not words or len(words) > 8 or (len(words) == 1 and words[0] in _A_MERE_PRONOUN):
        return "it"
    return " ".join(words)


def _is_a_flat_read(reply):
    """True for the composer's flat readings this module replaces, and nothing else."""
    return any(reply in pool for pool in _FLAT)


def _is_a_hedge(reply):
    """True for the composer's lines that say it cannot answer, or that nothing was said yet.

    A search handed to the bot is the one errand where the hedge is not good enough: "google what
    time the post office shuts" was answered "I'm not sure about that one, sorry - I'd rather not
    guess. A quick search online will get you a solid answer" once the line was read as the ask
    inside it, and the honest limit below says more (what it cannot do, what the person should
    compare, where the rest is). The same goes for the store's "nothing said yet for that to be"
    lines, which answer "google it for me" by asking what "it" is - the person did say what they
    wanted done, and the search limit is the reply that says what happens to it.

    The imports are inside the call because `fallback` is the heavy one and this file is reached
    before it, and `store_lines` is data this file does not otherwise need.
    """
    from . import fallback
    from ..memory import store_lines
    if fallback.is_a_hedge(reply):
        return True
    return any(reply in pool for pool in (store_lines.POINTS_BACK_NOTHING,
                                         store_lines.POINTING_WORD_NOTHING))


def _about_an_errand(clean):
    """The pool for the errand the line hands over, or None."""
    if len(clean.split()) > 14:
        return None
    # A search names its own object: "search for the number for the council" is theirs, and so is
    # "look up today's match", which names nothing of theirs and was handed back as a fact of
    # theirs ("Noted: look up today's match."). The object of a search is whatever the words after
    # the verb say, so the "the/this/my" fence is not asked of it - only of the other errands,
    # where a verb with nothing of theirs after it ("send a message") really is a fragment.
    a_search = bool(_A_SEARCH.search(clean))
    if not a_search and not _THEIR_ERRAND.search(clean):
        return None
    if _KEEP_OUT.search(clean):
        return None
    # The message that is going out has to be about a thing of theirs, not about this chat: "send
    # me a message" alone is a fragment with nothing to send, and it keeps the nod.
    if a_search:
        return A_NO_SEARCH
    if _A_SPEND.search(clean):
        return A_NO_SPEND
    if _A_MESSAGE_OUT.search(clean):
        return A_NO_SEND
    if _A_LIST.search(clean):
        return A_NO_LIST
    return None


def answer_for(text, memory, reply):
    """The honest line for an errand handed to a bot with no hands, or None."""
    if not reply:
        return None
    clean = " ".join((text or "").lower().split())
    if not clean:
        return None
    pool = _about_an_errand(clean)
    if not pool:
        return None
    # A flat reading is replaced, and so is a hedge when the errand is a search: the search limit
    # below is a better reply than "a quick search online will get you a solid answer", because
    # it names what the person should compare and where the rest lives.
    if not _is_a_flat_read(reply) and not (pool is A_NO_SEARCH and _is_a_hedge(reply)):
        return None
    return pick(pool, memory, text).format(what=_facing_them(_what_was_asked_for(clean)))
