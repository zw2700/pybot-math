"""The dates of famous things: when it was built, discovered, introduced or first happened.

@lemon-wasp measured five `when` lines on main and each of them fell over a different way: "when
was the eiffel tower built" and "when was penicillin discovered" were a search punt, "when did the
empire windrush arrive" was told the bot cannot see the news, "when did the poll tax start" got
the self-assessment card because of the word tax, and "when was the last ice age" was answered
"You haven't told me about anything coming up yet".

The history table in `history.py` already answers `who was brunel` and `when did the titanic sink`
by the thing the line names, so the mechanism was right and the rows were missing: a date is a
fact about a thing, and the thing is the key. Every reply opens with the date, because that is
the half a `when` line asks about. A domain of its own rather than more rows in `history.py`,
which is at the publisher's size ceiling.
"""
import re

from .lookup import entry

ANSWERS = ("history", "science")

# Each row is keyed by the thing, never by the wording: "when was the eiffel tower built", "how
# old is the eiffel tower" and "tell me about the eiffel tower" all name the same thing.
_DATES = {

    "eiffel-tower": {
        "names": ("eiffel tower", "eiffel"),
        "tell": "The Eiffel Tower was finished in March 1889 for the Paris world's fair, the "
                "Exposition Universelle, and opened to the public in May that year. It is 300 "
                "metres to the top of the flagpole, was the tallest building in the world until "
                "1930, and was meant to stand for twenty years.",
    },
    "penicillin": {
        "names": ("penicillin", "fleming"),
        # who found it has a card of its own, and it is the shorter answer: the year is this
        # row's business, the person is that one's.
        "off": ("who discovered", "who found", "who invented", "who created"),
        "tell": "Alexander Fleming noticed the mould killing his bacteria at St Mary's Hospital "
                "in London in September 1928, and published it the next year. Howard Florey and "
                "Ernst Chain turned it into a medicine at Oxford in 1940-41, and the first "
                "patient was treated in 1941.",
    },
    "last-ice-age": {
        "names": ("ice age", "ice ages", "last ice age", "glaciation", "glacial period"),
        "off": ("film", "films", "movie", "mammoth", "the croods", "netflix", "cinema",
                "dvd", "sequel", "release"),
        # The ways people ask about the film do not say "film" (lemon-wasp, 13653): a number
        # after the name, or "out", "on tv", "on at" - "when is ice age 6 out", "when is ice age
        # on tv". A word list cannot hold a number, so this is the shape of the question instead
        # of one of its words, and "when was the ice age" / "when did the last ice age end" are
        # left alone.
        "off_re": re.compile(r"\bice ages?\b(?:\s+\d|\s+(?:out|on)\b|\s+(?:on|at) (?:tv|"
                            r"netflix|the cinema|bbc|itv|channel|disney))", re.I),
        "tell": "The last ice age ended about 11,700 years ago. The coldest part of it, the last "
                "glacial maximum, was about 20,000 years ago, when ice sheets reached as far "
                "south as the Thames and the Midlands.",
        "long": "The last ice age ran for roughly 100,000 years and ended about 11,700 years "
                "ago, which is when the glaciers melted back and farming began. The coldest "
                "stretch was about 20,000 years ago.",
    },
    "poll-tax": {
        "names": ("poll tax", "community charge"),
        "tell": "The poll tax, officially the community charge, started in Scotland in April 1989 "
                "and in England and Wales in April 1990, and was replaced by the council tax in "
                "1993. It charged every adult a flat amount instead of a rate on the value of "
                "the home, and the protests against it helped bring down Margaret Thatcher.",
    },
    "empire-windrush": {
        "names": ("empire windrush", "windrush"),
        "tell": "The Empire Windrush docked at Tilbury on 22 June 1948, bringing 1,027 passengers "
                "from the Caribbean, most of them Jamaican, who had answered an ad for workers "
                "in Britain. It was one ship among many, but the date became the shorthand for "
                "the start of that generation's arrival.",
    },
    "statue-of-liberty": {
        "names": ("statue of liberty", "liberty island"),
        "tell": "The Statue of Liberty was dedicated on 28 October 1886 in New York Harbour, a "
                "gift from France for the centenary of American independence. It was designed by "
                "Frederic Auguste Bartholdi with a iron frame by Gustave Eiffel, and the "
                "pedestal was paid for by public subscription.",
    },

    "nhs-founded": {
        "names": ("nhs", "national health service"),
        # The services that are another card's question, and the word for a price: "when did
        # the eye test become free on the nhs" is the eye-test card's, and asking for a date is
        # not a way round that.
        "off": ("dentist", "waiting", "prescription", "appointment", "gp", "job", "work for",
                "complaint", "complain", "charging", "charge", "private", "pay", "cost", "free",
                "eye", "eye test", "dental", "ambulance", "waiting list"),
        "tell": "The NHS started on 5 July 1948, when the National Health Service Act came into "
                "force in England and Wales under Aneurin Bevan, the health minister. It was the "
                "first health service anywhere to be free at the point of use and paid for out "
                "of taxation.",
    },
}

_NAMES = tuple(name for row in _DATES.values() for name in row["names"])

# What makes a line a question about the thing it names: without one of these, a line that
# happens to mention the eiffel tower would be handed a date it did not ask for.
# The words that ask for a date and nothing else. "what is", "what was", "tell me about" and
# "about" were here at first, and they are not an ask for a date but an ask for the thing: with
# bias=4 the table took "what is the nhs" and "what is penicillin used for" off the cards that
# answer them (green-dog, 13653). A definition question is somebody else's line; this table only
# answers the line that wants the year.
_ASK = ("when", "when was", "when did", "what year", "which year", "how old", "how long ago",
        # a duration about a thing in the world is still its date: "how long did the last ice age
        # last" was the ice tray's keeping card, and "how long was the poll tax around for" was
        # self-assessment. "how long is" is left out on purpose - "how long is the eiffel tower
        # open" is the opening hours, not 1889.
        "how long did", "how long was", "how long has", "how long have", "lasted",
        "who built", "built", "discovered", "invented", "founded", "started")

# "how long did it last" wants the length, not the date.
_LONG = re.compile(r"\b(?:how long|long|lasted)\b", re.I)


def _said(reading):
    """The line as typed and as read, so a name survives whatever the reader repairs."""
    reading = reading or {}
    parts = (reading.get("plain"), reading.get("clean"), reading.get("text"))
    return " ".join(part for part in parts if part).lower()


def _the_row(text):
    """The row a line names, longest name first, or None when it names none of them."""
    best, best_len = None, 0
    for row in _DATES.values():
        if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in row.get("off", ())):
            continue  # "when was the nhs set up" in a line about a dentist is the dentist's
        if row.get("off_re") is not None and row["off_re"].search(text):
            continue  # a shape of question this row does not answer, like "when is ice age 6 out"
        for name in row["names"]:
            if len(name) > best_len and re.search(r"\b" + re.escape(name) + r"\b", text):
                best, best_len = row, len(name)
    return best


def _named(text):
    return _the_row(text)


def the_date(memory, reading):
    """The date of the thing the line names, or None so another row can answer."""
    text = _said(reading)
    row = _the_row(text)
    if row is None:
        return None
    if row.get("long") and _LONG.search(text):
        return row["long"]
    return row["tell"]


def names_a_row(reading):
    """The guard is asked while the line is scored, so a row this table does not hold is not
    written off by the table's own bias: "why did world war one start" is not a date."""
    return _the_row(_said(reading)) is not None


ENTRIES = [
    entry("the-date-of-a-thing", (_NAMES, _ASK), the_date, bias=4, guard=names_a_row),
]
