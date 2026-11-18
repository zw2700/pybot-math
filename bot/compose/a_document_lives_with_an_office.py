"""A document is held by an office, not found near you.

"where do i get the deeds", "where can i find the log book for my car", "where can i get a
probate record" are all "where do i get a thing" lines, and the reader for that shape answers
them the way it answers a bike tyre: a map app search for the thing and a ring before setting
off. There is no shop with a shelf of them. Somebody following that reply drives to a retail
park for a document that has one holder, and the holder is named on a form.

What the bot knows here is small and does not go stale: which office holds a kind of record, and
that the office's own service is where the copy is ordered. So the reply says the office first -
the Land Registry for a title register, the DVLA for a V5C, the register office for a certificate,
the Probate Service for a grant - and only then what to have ready. It never says the bot can
look it up, and it never guesses an address or a fee.

Nothing in here reads the world. The holder of each record is the part that is a fact, so it is
kept as data and the wording is chosen from a pool by the line, the way the rest of the composer
does it.

The turn is taken only where the composer had nothing: a hedge, or the composer's own "I don't
know". A line the knowledge base answers - "where can i get my birth certificate" already gets
the register office from a card - keeps its own answer, because this reader is asked before the
map-app one and after everything that knows something.
"""
import re

from . import pick

# "where do i get the deeds", "who holds the log book", "how do i apply for probate": an ask
# about getting hold of something. A statement about the same words is not one ("we lost the log
# book"), so the ask word has to be there.
AN_ASK = re.compile(
    r"\b(?:where|who)\b[^.!?]{0,40}?\b(?:get|gets|got|hold|holds|find|order|apply|request|"
    r"obtain|keep|keeps|stored|copy)\b"
    r"|\bhow\s+(?:do|can|could|would|should)\s+i\s+(?:get|find|order|apply|request|obtain|"
    r"replace)\b"
    r"|\bhow\s+to\s+(?:get|find|order|apply|request|obtain)\b"
    r"|\bcan\s+i\s+(?:get|find|order|request|obtain|replace)\b"
    r"|\bwhere\s+(?:is|are)\s+[^.!?]{0,30}?\b(?:kept|held|stored|filed)\b",
    re.IGNORECASE)

# Losing one is the same question asked as a statement: "we lost the log book", "i cant find my
# birth certificate". The office that issues the copy is the answer either way, and the composer's
# small-talk pool ("Sorry to hear that. What would help most right now?") is no answer at all.
A_LOST = re.compile(
    r"\b(?:lost|losted|misplaced|mislaid|can'?t\s+find|cannot\s+find|can\s+not\s+find|"
    r"cant\s+find|need\s+(?:a\s+)?(?:new|replacement|another)\s+copy|"
    r"need\s+a\s+copy)\b",
    re.IGNORECASE)

# "We lost the baby", "i lost my mum", "lost my dog": the same word, and not a record at all.
# A death, a person or a pet is the composer's loss and sympathy cards' to answer, and an office
# that sells copies is a cold thing to hand somebody in the middle of it. So the reader stands
# down whenever one of these is the thing that was lost.
A_PERSON_LOST = re.compile(
    r"\b(?:baby|babies|mum|mums|mom|mother|dad|father|son|daughter|child|children|boy|girl|"
    r"husband|wife|partner|brother|sister|gran|granny|grandma|grandad|grandpa|nana|friend|"
    r"mate|colleague|neighbou?r|pup|puppy|kitten|dog|cat|horse|pet)\b",
    re.IGNORECASE)

# The words that name the holder of each record. A reply that already has one has answered the
# line, and this reader has nothing to add.
THE_OFFICE_NAMES = {
    "deeds": re.compile(r"land\s+registry|registers\s+of\s+scotland|title\s+register",
                        re.IGNORECASE),
    "logbook": re.compile(r"\bdvla\b|\bv5c\b", re.IGNORECASE),
    "will": re.compile(r"solicitor|probate\s+service|probate\s+record", re.IGNORECASE),
    "lease": re.compile(r"landlord|managing\s+agent|solicitor", re.IGNORECASE),
    "certificate": re.compile(r"register\s+office|general\s+register\s+office",
                              re.IGNORECASE),
    "probate": re.compile(r"probate\s+service|gov\.uk|solicitor", re.IGNORECASE),
    "records": re.compile(r"\bgp\b|surgery|practice", re.IGNORECASE),
}

# The records, and the family each one belongs to. The first family whose words are in the line
# takes it, so "the deeds" and "a probate record" never share a reply.
THE_KINDS = (
    ("probate", re.compile(
        r"\b(?:probate|grant\s+of\s+probate|letters\s+of\s+administration|"
        r"probate\s+(?:record|records|copy|papers?))\b", re.IGNORECASE)),
    ("logbook", re.compile(
        r"\b(?:log\s?book|logbook|v5c|v5\s?c|registration\s+document)\b", re.IGNORECASE)),
    ("deeds", re.compile(
        r"\b(?:deeds?|title\s+(?:register|deeds?|plan)|land\s+registry|"
        r"title\s+number)\b", re.IGNORECASE)),
    # A will is named by a possessive, and the possessive is not always "my": "a copy of my
    # dads will", "my mother's will", "where is the will kept". The genitive shape is the common
    # one when the will belongs to somebody who has died, and it was falling through to the
    # map-app line, which is no answer to a document with a named keeper.
    ("will", re.compile(
        r"\b(?:a|the|my|his|her|their|our|your)\s+will\b"
        r"|\b[\w'’]*s['’]?\s+will\b"
        r"|\b(?:grant\s+of\s+)?probate\s+copy\b", re.IGNORECASE)),
    ("lease", re.compile(
        r"\b(?:lease|leases|tenancy\s+agreement|assured\s+shorthold)\b", re.IGNORECASE)),
    # A certificate of a birth, a marriage or a death is the register office's, and the copy is
    # ordered from the General Register Office or the district. The bare word is not in this family
    # and must not be: an MOT certificate comes from the testing station's record on gov.uk, a gas
    # safety certificate from the Gas Safe engineer who issued it, an EPC from the assessor, and
    # "where can i get my gas safety certificate" was answered with the register office - a wrong
    # holder, which is worse than the search hedge it replaced (breezy-grape on #13661). So the
    # noun after "certificate" has to be one of the three events, or it is not this reader's line.
    ("certificate", re.compile(
        r"\b(?:birth\s+certificate|marriage\s+certificate|death\s+certificate|"
        r"certified\s+copy)\b", re.IGNORECASE)),
    ("records", re.compile(
        r"\b(?:medical\s+records?|health\s+records?|my\s+records?|gp\s+records?|"
        r"patient\s+records?)\b", re.IGNORECASE)),
)

# What is held, who holds it, and what to have ready. One sentence of the office, one of the
# practical step, so the reply answers first and does not become a leaflet.
THE_OFFICE = {
    "deeds": (
        "The deeds are the title register, and HM Land Registry holds it for England and Wales "
        "(Registers of Scotland north of the border). Their own service will sell you a copy "
        "from the property's address, and that copy is the one that counts.",
        "What people call the deeds is now the title register at HM Land Registry, so there is "
        "nothing to ask a solicitor for first: search their service by the property's address, "
        "pay a few pounds, and the copy comes as a download.",
    ),
    "logbook": (
        "The log book is the V5C and the DVLA issues it - no shop has one. If yours is lost or "
        "damaged, apply for a replacement on gov.uk with the car's details and the green slip "
        "you kept from the sale.",
        "That one comes from the DVLA, not a counter in town: a replacement V5C is applied for "
        "on gov.uk, and the car's registration number plus the details of the keeper is what "
        "the form asks for.",
    ),
    "will": (
        "The will itself is with whoever drew it up or kept it - usually the solicitor - and "
        "once probate is granted a copy goes on the public record at the Probate Service. Ask "
        "the solicitor first, then search the Probate Service's own record.",
        "Start with the solicitor named on it, or the person who kept the original, because a "
        "will is not registered anywhere while the person is alive. After probate it is a "
        "public document and the Probate Service will sell you a copy.",
    ),
    "lease": (
        "The lease is held by the landlord or their managing agent, and if you bought the "
        "flat your solicitor will have kept a copy - that is usually a phone call and an email. "
        "A managing agent will send one for a small fee if the solicitor cannot find it.",
        "Ask the landlord or the managing agent for a copy, and check your own paperwork first: "
        "anyone who has bought a leasehold flat was sent one at completion, and the solicitor "
        "who did the buying keeps it on file.",
    ),
    "certificate": (
        "A certificate comes from the register office for the district where the birth, "
        "marriage or death was registered, or from the General Register Office for older ones. "
        "Their own site takes the order - have the date and the place ready.",
        "The register office for the district where it happened holds it, and the General "
        "Register Office holds the older records. Order through their own site with the date "
        "and the place, and the certificate comes by post.",
    ),
    "probate": (
        "A grant of probate comes from the Probate Service, through gov.uk, and it is the "
        "court's copy rather than the will. An estate with a house, shares or a disagreement in "
        "it is worth a solicitor doing that part.",
        "Probate is the Probate Service's, applied for on gov.uk, and it is worth checking "
        "whether the estate is small enough for the simpler form. If there is property or a "
        "will being argued over, hand it to a solicitor.",
    ),
    "records": (
        "Your medical records sit with the GP surgery you are registered at, and you can ask "
        "for a copy in writing - the surgery has to answer, usually within a month.",
        "Ask the GP surgery that has you registered: a written request gets you a copy of the "
        "records, and the reception will say what they need from you to prove it is you.",
    ),
}

# The bot cannot see a queue, a fee today, or whether the office wants a form posted, so the
# reply says so in a few words rather than promising a same-day answer.
# A map-app line is the map reader's, and it is what these lines get without this reader. It is
# read off the reply so the reader can stand over the composer's hedge and over that line both.
A_MAP_LINE = re.compile(
    r"^(?:No map on this side|I can't see what's near you|There's no list of places here|"
    r"No stock lists here|I can't check stock or shops near you)",
    re.IGNORECASE)


def a_map_app_line(reply):
    """True when the reply is the map-app reader's line about a thing to buy."""
    return bool(reply) and bool(A_MAP_LINE.match(str(reply).strip()))


def _the_kind(clean):
    """The family of record the line names, or "" when it names none."""
    for name, pattern in THE_KINDS:
        if pattern.search(clean):
            return name
    return ""


def _names_the_office(reply, kind):
    """True when the reply already says who holds it."""
    pattern = THE_OFFICE_NAMES.get(kind)
    return bool(reply and pattern and pattern.search(str(reply)))


def a_lost_record(text, reply=None):
    """True when the line is a record somebody has lost and the reply has not named its holder.

    The composer reads "we lost the log book" as a feeling and answers it with sympathy. It is a
    question about a replacement, and the office that issues one is the answer, so this stands
    over that comfort line - but not over a card that already says DVLA, Land Registry or the
    register office, and never when the thing lost is a person or a pet.
    """
    clean = " ".join(str(text or "").lower().split())
    if not clean or not A_LOST.search(clean) or A_PERSON_LOST.search(clean):
        return False
    kind = _the_kind(clean)
    if not kind:
        return False
    return not _names_the_office(reply, kind)


def answer_for(text, memory=None, reply=None):
    """A reply naming the office that holds the record, or None.

    Only a line that asks where to get one of these records reaches here: a question shape and a
    named record. Everything else returns None, so the map-app reader and the rest of the chain
    keep every ordinary "where do i get a thing" line.

    A record somebody has lost is the same question said as a statement - "we lost the log
    book" - and the composer answers it as a feeling ("That sounds rough"). The office is the
    answer that helps, so a lost record is taken too, unless the reply already names the office
    or the thing lost is a person or a pet rather than a record.
    """
    clean = " ".join(str(text or "").lower().split())
    if not clean:
        return None
    asked = bool(AN_ASK.search(clean))
    lost = bool(A_LOST.search(clean))
    if not asked and not lost:
        return None
    kind = _the_kind(clean)
    if not kind:
        return None
    if lost and A_PERSON_LOST.search(clean):
        return None
    if lost and not asked and _names_the_office(reply, kind):
        return None
    return pick(THE_OFFICE[kind], memory, clean)
