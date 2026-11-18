"""A phone bought for what the person does with it.

"i need a new phone" and then "i only use it for photos and calls" is one buying question, and the
use is the half of it that decides the answer: photos want storage and a decent camera, calls and
texts want the cheapest handset that still gets security updates. The transfer row in
`technology.py` keys "new phone" and "photos", so a use statement reached it and a person who had
not chosen a phone yet was told how to copy their data onto one.

This is its own file rather than rows in `shopping.py` and `technology.py` because those two are
long and busy: a domain is one file with ENTRIES in it, and a use statement about a phone is not
the only row either of them needs. The key carries the use as a phrase ("use it for", "only use
it for") so it scores as the phrase it is against the transfer row's single word "photos", and
the guard below keeps it out of every line that is a move, a fault or a phone already in hand.
"""
import re

from .lookup import entry

ANSWERS = ("technology",)

# The words a person uses to say what the phone is for, read off the line rather than keyed: the
# same sentence answers a camera question and a texts question and the halves are different.
_PHOTOS = re.compile(
    r"\b(?:foto|fotos|photo|photos|picture|pictures|pics|camera|video|videos|instagram|tiktok|"
    r"youtube)\b", re.I)
_CALLS = re.compile(
    r"\b(?:call|calls|calling|text|texts|texting|message|messages|messaging|ring|ringing)\b", re.I)
_PHONE_THING = re.compile(
    r"\b(?:phone|phones|iphone|iphones|android|handset|mobiles?)\b", re.I)

# A use said on the next turn ("its mostly for photos") names no phone, so the turn before it
# has to be about one: the whole buying question is "which phone" and then "what for".
_HEAVY = re.compile(
    r"\b(?:game|games|gaming|work|email|emails|spreadsheet|spreadsheets|editing|design)\b", re.I)

# A line that is a move, a fault, a purchase already made or a how-to is another row's question.
_NOT_A_USE = re.compile(
    r"\b(?:transfer|moved|move|migrat|sync|backed up|back up|set up|setup|restore)\b"
    r"|\b(?:battery|batteries|charg\w*|screen|cracked|crack|broken|repair|fix|water|wet|hot|slow|"
    r"full|storage|wifi|wi-fi|signal|sim|contract|bill|tariff|stolen|lost|wont|won't|doesn't|"
    r"not working)\b"
    r"|\b(?:got a new phone|got a phone|have a new phone|have a phone|already got|already have|"
    r"just got|just bought|i bought|ive bought|how do i|how to|how can i)\b"
    # A phone for somebody else, and especially for a child, is a different question: what a
    # nine-year-old needs is a cheap handset in the parent's name, not a camera.
    r"|\b(?:my child|my son|my daughter|my kid|my kids|my teen|my teenager|for a child|for children|"
    r"for my son|for my daughter|for a kid|for a 1[0-6] year old|grandson|granddaughter)\b", re.I)

# A statement of use is not a request to choose a phone: it needs a word that makes it one, here
# or in the turn before ("i need a new phone" then "its mostly for photos").
_A_BUYING_QUESTION = re.compile(
    r"\b(?:need|needs|needed|want|wants|looking|after|get|getting|buy|buying|bought|should|"
    r"which|what|whats|recommend|suggest|advice|worth|budget|cheap|cheapest|best|good|better|"
    r"new|old|oldest|upgrade|replace|replacing|broke|broken|dying|dead|knackered|ancient)\b",
    re.I)


def _the_use(understood):
    """The line as text: the reading carries it, and an entry only gets the dict."""
    if not isinstance(understood, dict):
        return ""
    return str(understood.get("text") or understood.get("clean") or "")


def _phone_words(line):
    return bool(_PHONE_THING.search(line))


def _a_use(understood):
    """True when the line says what the phone is used for, rather than how to move or fix one."""
    line = _the_use(understood)
    if not line.strip():
        return False
    return not _NOT_A_USE.search(line)


def _phone_for_that_use(memory, understood):
    """The handset for what the line says the phone is used for, or None when it says no use."""
    line = _the_use(understood).lower()
    before = ""
    if isinstance(memory, dict):
        topic = memory.get("topic") or {}
        if isinstance(topic, dict):
            before = str(topic.get("text") or topic.get("of") or "")
    if not _phone_words(line) and not _phone_words(before):
        return None
    if not (_A_BUYING_QUESTION.search(line) or _A_BUYING_QUESTION.search(before)):
        return None
    photos = bool(_PHOTOS.search(line))
    calls = bool(_CALLS.search(line))
    heavy = bool(_HEAVY.search(line))
    if not (photos or calls or heavy):
        return None
    if photos and not heavy:
        return ("Photos are the part worth paying for: a mid-range phone at £200 to £300 takes "
                "pictures as good as a flagship did a few years ago, so put the extra into "
                "storage - 128GB at least, 256GB if you keep videos - and let cloud backup at a "
                "few pounds a month carry the rest.")
    if calls and not photos and not heavy:
        return ("Calls and texts need nothing special, so buy the cheapest phone that still gets "
                "security updates: about £120 to £180 new, less refurbished. Check the maker "
                "promises four or five years of updates and that the battery is 4,500mAh or more, "
                "and ignore how many cameras it has.")
    if heavy and not photos:
        return ("For games or work on a phone, spend on the processor and the screen: £300 to "
                "£450 buys a mid-range chip that will not stutter, and 256GB of storage, because "
                "games take a lot of room. A two-year-old flagship at the same money is the other "
                "good buy if the battery health is over 85%.")
    return ("For photos and everything else, £200 to £300 buys a mid-range phone that covers "
            "calls, photos, maps and video, and 128GB of storage matters more than the camera. "
            "Buy it outright rather than on a contract if you can, because the contract usually "
            "costs more over two years.")


ENTRIES = [
    # The use is said in the words people use for it, and the phrases are in the key so the row
    # scores as a phrase rather than as the bare "photos" the transfer row also holds.
    entry("a-phone-for-that-use",
          (("phone", "iphone", "android", "handset", "mobile"),
           ("use it for", "use my phone for", "use a phone for", "used for", "using it for",
            "only use", "just use", "mostly use", "mainly use", "only need", "just need",
            "mostly for", "mainly for", "only for", "just for", "it is for", "its for",
            "for photos", "for pictures", "for calls", "for texts", "for messages",
            "for games", "for emails")),
          _phone_for_that_use, bias=6,
          ask=("use it for", "use my phone for", "use a phone for", "using it for", "used for",
               "only use", "just use", "mostly use", "mainly use", "only need", "just need",
               "mostly for", "mainly for", "only for", "just for", "it is for", "its for",
               "for photos", "for pictures", "for calls", "for texts", "for messages",
               "for games", "for emails"),
          guard=_a_use),
]
