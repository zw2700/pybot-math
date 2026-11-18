"""Parking on the pavement, a verge or a kerb: the one legality ask with no card.

`is it legal to park on the pavement` and `is it against the law to park on the pavement` both
reached the search hedge, while nine of the eleven legality lines in the deck answer from a card.
The answer depends on where the person lives, so the card says where it depends - an offence
right across London and in Scotland, elsewhere only where a traffic order covers that street -
and names the signs on that street and the council's own page as what decides their road, rather
than giving a flat yes or no.

It is its own file rather than a row inside cars.py because the surface word is the whole
question, and a card about a footway has nothing to do with engines, tyres or warning lights.

The row is gated on the surface word, so "where can i park" is not this question and keeps its
local-rules line, and a pavement that is broken, icy or covered in litter is a repair, a fall or
a report rather than a parking rule.
"""
from .lookup import entry as _entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("cars",)

ENTRIES = [
    _entry("parking-on-the-pavement",
           (("park on the pavement", "parking on the pavement", "pavement", "pavements",
             "park on the verge", "parking on the verge", "verge", "grass verge",
             "footway", "footpaths", "kerb", "curb", "dropped kerb"),
            ("legal", "illegal", "allowed", "allow", "against the law", "law", "permitted",
             "ticket", "fined", "fine", "penalty", "can i", "is it", "is that", "am i",
             "park", "parked", "parking", "ok", "okay")),
           "Parking on the pavement is an offence right across London and in Scotland, and "
           "elsewhere only where a traffic order covers that street - so the signs and lines "
           "on it, and the council's own parking page, are what decide your road, and that is "
           "where to check rather than the country as a whole. Where it is allowed you must "
           "still leave the pavement clear enough for a wheelchair or a pushchair, and blocking "
           "a dropped kerb blocks someone's drive. A ticket for it is a penalty charge notice, "
           "argued in the council's own appeal rather than in a court.",
           # the surface word is what the row is about: "where can i park" is not this question
           ask=("pavement", "pavements", "verge", "grass verge", "footway", "footpaths",
                "kerb", "curb", "dropped kerb"),
           # a pavement that is broken or icy is a repair or a fall, not a parking rule
           avoid=("trip", "tripped", "tripping", "fell", "fell over", "slipped", "slippy",
                  "icy", "ice", "uneven", "pothole", "potholes", "cracked", "damaged",
                  "injur", "injured", "claim", "compensation", "wheelchair access",
                  "pushed", "buggy", "litter", "dog mess", "graffiti", "fixed", "repair")),
]
