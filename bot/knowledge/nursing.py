"""Entry points for a named job, and the other things a line can call points.

"how many points do i need for nursing" was answered with "Yes - it is the normal way to feed a
baby and it is what the milk is for. Feed on demand ... eight to twelve times in 24 hours." The
feeding card keys on "nursing" and on "how many", the driving card keys on "points", and nothing
held either of them off a question about UCAS points. The careers card in study.py has the
answer - "Nursing wants five GCSEs at grade 4 or above" - but its key asks for the exam words
("what gcses are needed") and a line that says "points" only reached the two cards that are
about something else.

The row here is the pairing that makes the question: a job or a course, and a points word. It
lives in its own domain on purpose. The matcher weighs a key word by how rare it is inside its
own domain, so a second row in study.py that lists every career name would make "nursing" common
there and quietly change which card two other lines reached. A domain of its own leaves every
other card's score exactly as it was.

The answer is study.py's own table, so there is one place that knows what nursing asks for.
"""
import re

from bot.knowledge.lookup import entry
from bot.knowledge.study import CAREER_SUBJECTS, _career_subjects  # noqa: F401 - the table is
# answered here as well as there, and a second copy of it would be the thing that went stale

ENTRIES = []

# The points words, and the order asks that go with them: a "how many" in the line is what keeps
# "whats the point of a dehumidifier" out, and every phrase here names a score rather than a
# purpose.
_POINT_WORDS = ("points", "ucas points", "ucas", "entry points", "tariff points", "tariff",
                "how many points", "points do i need", "points needed", "points for")

# A job or a course, from the one table in study.py that already knows them, so a career added
# there is answered here without a second edit.
_CAREER_NAMES = tuple(name for names, _ in CAREER_SUBJECTS for name in names)

ENTRIES.append(entry(
    "career-entry-points",
    (_CAREER_NAMES, _POINT_WORDS),
    _career_subjects,
    # a licence, a race, a game and a loyalty card are counted in points too, and none of them
    # is a course. The words are the ones those lines carry, so a points question about any of
    # them keeps the card that belongs to it.
    avoid=("licence", "license", "driving", "driver", "penalty", "speeding", "ban", "banned",
           "insurance", "f1", "formula 1", "formula one", "grand prix", "motogp", "lap", "laps",
           "try", "tries", "goal", "goals", "touchdown", "conversion", "rugby", "football",
           "soccer", "cricket", "netball", "basketball", "hockey", "tennis", "match", "game",
           "games", "score", "scored", "scoring", "season", "team", "teams", "loyalty",
           "reward", "rewards", "reward card", "nectar", "clubcard", "club card", "store card",
           "voucher", "vouchers", "coffee", "free coffee", "free drink", "supermarket", "shop",
           "shopping", "air miles", "my card", "dehumidifier", "point of"),
    # the feeding card ranks 7 on the nursing line (two key words plus its own bias of 2), so
    # this row has to rank higher than that rather than tie with it
    bias=6))
