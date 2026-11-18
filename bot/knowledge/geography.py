"""Geography: the everyday facts people check, in quizzes, homework and arguments.

The answers lane owns this domain. Capitals and city guides live in bot/knowledge/travel.py;
this file is the other side of geography: how many, how big, how long, with the one number
or caveat that makes an answer worth remembering.
"""
import re

from .lookup import entry

# A named region has its own count: a world or general-country answer would be wrong there.
_REGIONS = ("africa", "europe", "asia", "north america", "south america", "central america",
            "caribbean", "oceania", "australia", "uk", "britain", "england", "scotland",
            "wales", "ireland")


# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("geography-and-travel",)

# One row per peak people ask the height of: the name as it is written, the height in metres,
# and the one thing that makes it worth remembering. Heights are the published figures, so the
# answer and a map agree. Feet are worked out from the metres in the reply, so a new peak is one
# line of data and both units are right.
PEAKS = {
    "ben nevis": ("Ben Nevis", 1345, "the highest mountain in the UK, in Scotland above Fort "
                                     "William. The walk up from Glen Nevis is about 8 hours there "
                                     "and back."),
    "snowdon": ("Snowdon (Yr Wyddfa)", 1085, "the highest mountain in Wales, and the busiest in "
                                             "the UK. The Snowdon Ranger path is the gentlest way "
                                             "up without the train."),
    "yr wyddfa": ("Snowdon (Yr Wyddfa)", 1085, "the highest mountain in Wales, and the busiest in "
                                               "the UK."),
    "scafell pike": ("Scafell Pike", 978, "the highest mountain in England, in the Lake District, "
                                          "and the hardest of the three national peaks to walk "
                                          "because of the loose stone."),
    "slieve donard": ("Slieve Donard", 850, "the highest mountain in Northern Ireland, right above "
                                            "Newcastle in County Down."),
    "carrauntoohil": ("Carrauntoohil", 1038, "the highest mountain in Ireland, in the MacGillycuddy's "
                                             "Reeks, and the usual way up is through the Devil's "
                                             "Ladder."),
    "pen y fan": ("Pen y Fan", 886, "the highest point in the Brecon Beacons and the most popular "
                                    "walk in south Wales, about 4 miles there and back."),
    "helvellyn": ("Helvellyn", 950, "the third highest in England, and Striding Edge is the ridge "
                                    "that makes it famous - a scramble, not a walk."),
    "kilimanjaro": ("Kilimanjaro", 5895, "the highest mountain in Africa and the tallest "
                                         "free-standing mountain in the world, rising straight "
                                         "out of the plain with no range around it."),
    "mont blanc": ("Mont Blanc", 4808, "the highest peak in the Alps and in western Europe, on the "
                                       "French-Italian border."),
    "matterhorn": ("The Matterhorn", 4478, "the pyramid on the Swiss-Italian border, and the last "
                                           "of the great Alpine peaks to be climbed, in 1865."),
    "k2": ("K2", 8611, "the second highest mountain in the world, on the Pakistan-China border, and "
                       "a much harder and deadlier climb than Everest."),
    "denali": ("Denali", 6190, "the highest mountain in North America, in Alaska, and the biggest "
                               "rise of any mountain measured base to summit."),
    "aconcagua": ("Aconcagua", 6961, "the highest mountain in South America and the highest "
                                     "anywhere outside Asia."),
    "elbrus": ("Mount Elbrus", 5642, "the highest mountain in Europe if the Caucasus counts as "
                                     "Europe; otherwise the European record is Mont Blanc."),
    "fuji": ("Mount Fuji", 3776, "the highest mountain in Japan, a volcano that last erupted in "
                                 "1707, and a day's climb in summer."),
    "table mountain": ("Table Mountain", 1085, "the flat-topped mountain over Cape Town, and the "
                                                "cable car or the Platteklip Gorge path gets you up."),
    "kosciuszko": ("Mount Kosciuszko", 2228, "the highest mountain in mainland Australia, a long "
                                             "walk rather than a climb."),
    "aoraki": ("Aoraki / Mount Cook", 3724, "the highest mountain in New Zealand, in the Southern "
                                            "Alps, and a serious climb rather than a walk."),
}

# The highest point of a place, asked as "the highest mountain in Wales" rather than by name.
# The place is read from the line; a place not in this table falls through to the world answer's
# own guard rather than getting Everest for Snowdonia.
HIGHEST_IN = {
    "wales": "Snowdon (Yr Wyddfa) is the highest, at 1,085 metres (3,560 ft)",
    "england": "Scafell Pike is the highest, at 978 metres (3,209 ft)",
    "scotland": "Ben Nevis is the highest, at 1,345 metres (4,413 ft)",
    "northern ireland": "Slieve Donard is the highest, at 850 metres (2,789 ft)",
    "ireland": "Carrauntoohil is the highest, at 1,038 metres (3,406 ft)",
    "uk": "Ben Nevis is the highest, at 1,345 metres (4,413 ft)",
    "britain": "Ben Nevis is the highest, at 1,345 metres (4,413 ft)",
    "great britain": "Ben Nevis is the highest, at 1,345 metres (4,413 ft)",
    "europe": ("Mount Elbrus is the highest, at 5,642 metres (18,510 ft), if the Caucasus counts "
               "as Europe. If it does not, the record is Mont Blanc at 4,808 metres (15,774 ft)"),
    "africa": "Kilimanjaro is the highest, at 5,895 metres (19,341 ft)",
    "asia": "Everest is the highest, at 8,849 metres (29,032 ft)",
    "north america": "Denali is the highest, at 6,190 metres (20,310 ft)",
    "south america": "Aconcagua is the highest, at 6,961 metres (22,838 ft)",
    "australia": ("Mount Kosciuszko is the highest on the mainland, at 2,228 metres (7,310 ft). "
                  "The highest in Australian territory is Mawson Peak on Heard Island"),
    "oceania": "Puncak Jaya in New Guinea is the highest, at 4,884 metres (16,024 ft)",
    "antarctica": "Mount Vinson is the highest, at 4,892 metres (16,050 ft)",
    "alps": "Mont Blanc is the highest, at 4,808 metres (15,774 ft)",
    "usa": "Denali is the highest, at 6,190 metres (20,310 ft)",
    "united states": "Denali is the highest, at 6,190 metres (20,310 ft)",
    "canada": "Mount Logan is the highest, at 5,959 metres (19,551 ft)",
    "spain": "Mount Teide in Tenerife is the highest, at 3,715 metres (12,188 ft)",
    "france": "Mont Blanc is the highest, at 4,808 metres (15,774 ft)",
    "italy": ("Mont Blanc (Monte Bianco) is the highest, at 4,808 metres (15,774 ft), on the "
              "French border"),
    "japan": "Mount Fuji is the highest, at 3,776 metres (12,388 ft)",
    "india": "Kangchenjunga is the highest, at 8,586 metres (28,169 ft)",
    "new zealand": "Aoraki / Mount Cook is the highest, at 3,724 metres (12,218 ft)",
}


def _world(reply):
    """A world record, unless the line asks about a named region: Africa's biggest country is
    Algeria, not Russia, its highest mountain is Kilimanjaro, and the UK is four countries, not
    195. Passing is better than the world answer to a region question."""
    place = re.compile(r"\b(?:in|of|make up|makes up|making up)\s+(?:the\s+)?([a-z']+)")
    whole = ("world", "earth", "planet", "all", "them", "these", "those")
    # "how tall is everest in feet" is not a question about feet: a unit is not a region.
    unit = ("feet", "foot", "metres", "meters", "metre", "meter", "kilometres",
            "kilometers", "km", "miles", "mile", "centimetres", "centimeters", "cm",
            "inches", "inch", "total")

    def answer(memory, understood):
        clean = understood.get("clean") or ""
        named = place.search(clean)
        if named and named.group(1) not in whole and named.group(1) not in unit:
            return None
        return reply
    return answer


def _feet(metres):
    """The same height in feet, so an answer works in either unit."""
    return int(round(metres / 0.3048))


def _said(understood):
    return " " + (understood.get("clean") or "").lower() + " "


def _peak_named(understood):
    """The peak row the line names, the longest name first so "table mountain" wins over a word."""
    text, found, best = _said(understood), None, ""
    for name, row in PEAKS.items():
        if len(name) > len(best) and re.search(r"\b" + re.escape(name) + r"\b", text):
            found, best = row, name
    return found


def _peak(memory, understood):
    row = _peak_named(understood)
    if row is None:
        return None
    name, metres, note = row
    return ("%s is %s metres (%s feet) high: %s"
            % (name, format(metres, ","), format(_feet(metres), ","), note.rstrip(".") + "."))


def _highest_in_place(memory, understood):
    text = _said(understood)
    # the longest place name first: "northern ireland" is not "ireland"
    for place in sorted(HIGHEST_IN, key=len, reverse=True):
        if re.search(r"\b" + re.escape(place) + r"\b", text):
            return HIGHEST_IN[place] + "."
    return None


# How many countries a continent has is a separate fact from the world total, and the counts
# people argue about are the ones with a caveat. The continent is picked from the line, not
# from the key alone, so every way of naming it gets the same number.
_CONTINENT_COUNTS = (
    ("north america", "North America has 23 countries, from Canada down to Panama; the Caribbean "
                      "islands are counted separately as part of the region."),
    ("south america", "South America has 12 countries, from Colombia and Venezuela round to "
                      "Argentina and Chile."),
    ("africa", "Africa has 54 countries, or 55 if you count Western Sahara, which is disputed. "
               "Nigeria is the most populous and Algeria the largest by area."),
    ("europe", "Europe has 44 countries, or about 50 if you count the transcontinental ones such "
               "as Russia and Turkey. The exact number depends on where you draw the eastern edge."),
    ("asia", "Asia has 48 countries, or 49 if you count Taiwan. Russia and Turkey are usually "
             "counted in Europe as well, which is why some lists differ."),
    ("oceania", "Oceania has 14 countries, spread across Australia, New Zealand, Papua New Guinea "
                "and the Pacific island states."),
    ("antarctica", "Antarctica has no countries. It is governed by the Antarctic Treaty, and the "
                   "only people there are scientists at research stations."),
)


def _continent_count(memory, understood):
    """The continent's own total, unless the line asks about a subset of its countries.

    Read the raw line, not the widened reading: after "how many countries in africa" the
    next line "how many countries have free healthcare" carries africa in its context and
    would otherwise get the Africa answer again. A trailing "have" is the natural
    "how many countries does africa have"; a have/has/with before a noun is a subset.
    """
    text = (understood.get("text") or "").lower()
    trimmed = re.sub(r"\s+(?:have|has)\s*[?.!]*$", "", text)
    if re.search(r"\b(?:have|has|with|without|allow|allows|legal|banned?|bans|speak|speaks|"
                 r"use|uses|need|needs)\b", trimmed):
        return None
    for name, count in _CONTINENT_COUNTS:
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            return count
    return None


# "The largest country in Africa" is not Russia, and it is not the count of countries either: the
# line names a region, and the region has its own fact. One table holds every shape a person asks
# for - the biggest, the smallest, the most people, the fewest people, and the top and bottom
# three - so the record entry and the world entries in travel.py answer from the same facts.
_PLACES = ("north america", "south america", "central america", "caribbean", "africa", "europe",
           "asia", "oceania", "antarctica")

_REGION_COUNTRY = {
    "africa": {
        # "area" is the biggest and "small" the smallest, because travel.py's world entries ask
        # for those two kinds; the rest of the shapes are the other questions a continent gets.
        "area": ("Algeria is the largest country in Africa by area, at about 2.4 million square km "
                 "- most of it Sahara. The Democratic Republic of the Congo is second."),
        "small": ("The Seychelles is the smallest African country by area, an island nation of "
                  "about 115 islands. If you mean the smallest on the mainland, it is The Gambia."),
        "people": ("Nigeria", "Ethiopia", "Egypt", "DR Congo", "South Africa"),
        "populous": ("Nigeria has the most people in Africa, about 230 million. Algeria is the "
                     "biggest by area and the Seychelles is the smallest country."),
        "least": ("The Seychelles has the fewest people in Africa, about 100,000, and it is the "
                  "smallest country there by area too."),
        "top": ("The three biggest countries in Africa by area are Algeria (2.4 million square km), "
                "DR Congo (2.3 million) and Sudan (1.9 million). By people it is Nigeria first, then "
                "Ethiopia and Egypt."),
        "bottom": ("The three smallest countries in Africa by area are the Seychelles (455 square km), "
                   "São Tomé and Príncipe (about 1,000) and Comoros (about 1,900)."),
    },
    "europe": {
        "area": ("Ukraine is the largest country wholly inside Europe, at about 600,000 square km; "
                 "European Russia is bigger but is usually counted separately."),
        "small": ("Vatican City is the smallest country in Europe, and in the world, at about 0.49 "
                  "square km. Monaco is second, at about 2 square km."),
        "people": ("Russia", "Germany", "United Kingdom", "France", "Italy"),
        "populous": ("Russia has the most people in Europe, about 110 million in its European "
                     "part, and Germany the most of any country entirely in Europe, about 84 "
                     "million. Vatican City is the smallest."),
        "least": ("Vatican City has the fewest people in Europe, a few hundred, and it is the "
                  "smallest by area too."),
        "top": ("The three biggest countries in Europe by area are Russia's European part, Ukraine "
                "(604,000 square km) and France (551,000, without its overseas parts). By people it "
                "is Russia first, then Germany and the United Kingdom."),
        "bottom": ("The three smallest countries in Europe by area are Vatican City (half a square km), "
                   "Monaco (about 2) and San Marino (61)."),
    },
    "asia": {
        "area": ("China is the largest country in Asia, at about 9.6 million square km. India is "
                 "second; Russia is bigger but is counted as transcontinental."),
        "small": ("The Maldives is the smallest country in Asia, at about 300 square km spread over "
                  "some 1,200 islands."),
        "people": ("India", "China", "Indonesia", "Pakistan", "Bangladesh"),
        "populous": ("India has the most people in Asia, about 1.45 billion. China is the biggest "
                     "country entirely in Asia and the Maldives is the smallest."),
        "least": ("Brunei has the fewest people in Asia, about 455,000, though the Maldives is "
                  "smaller by area."),
        "top": ("The three biggest countries in Asia by area are China (9.6 million square km), India "
                "(3.3 million) and Kazakhstan (2.7 million). By people it is India first, then China "
                "and Indonesia."),
        "bottom": ("The three smallest countries in Asia by area are the Maldives (about 300 square km), "
                   "Singapore (about 730) and Bahrain (about 780)."),
    },
    "north america": {
        "area": ("Canada is the largest country in North America, at about 10 million square km; "
                 "the United States is a close second."),
        "small": ("Saint Kitts and Nevis is the smallest country in North America, at about 260 "
                  "square km. Grenada and Saint Vincent are close behind."),
        "people": ("United States", "Mexico", "Canada", "Guatemala", "Haiti"),
        "populous": ("The United States has the most people in North America, about 340 million. "
                     "Canada is the biggest by area and Saint Kitts and Nevis is the smallest."),
        "least": ("Saint Kitts and Nevis has the fewest people in North America, about 47,000, and "
                  "it is the smallest by area too."),
        "top": ("The three biggest countries in North America by area are Canada (10 million square km), "
                "the United States (9.8 million) and Mexico (1.96 million). By people it is the United "
                "States first, then Mexico and Canada."),
        "bottom": ("The three smallest countries in North America by area are Saint Kitts and Nevis "
                   "(about 260 square km), Grenada (about 340) and Saint Vincent and the Grenadines "
                   "(about 390)."),
    },
    "central america": {
        "area": ("Nicaragua is the largest country in Central America, at about 130,000 square km; "
                 "Honduras and Guatemala come next."),
        "small": ("El Salvador is the smallest country in Central America, at about 21,000 square "
                  "km, and the most densely populated on the mainland."),
    },
    "south america": {
        "area": ("Brazil is the largest country in South America, at about 8.5 million square km - "
                 "nearly half the continent. Argentina is second."),
        "small": ("Suriname is the smallest country in South America, at about 164,000 square km. "
                  "Uruguay and Guyana are next."),
        "people": ("Brazil", "Colombia", "Argentina", "Peru", "Venezuela"),
        "populous": ("Brazil has the most people in South America, about 215 million. It is the "
                     "biggest by area too, and Suriname is the smallest."),
        "least": ("Suriname has the fewest people in South America, about 620,000, and it is the "
                  "smallest by area too."),
        "top": ("The three biggest countries in South America by area are Brazil (8.5 million square km), "
                "Argentina (2.8 million) and Peru (1.3 million). By people it is Brazil first, then "
                "Colombia and Argentina."),
        "bottom": ("The three smallest countries in South America by area are Suriname (164,000 square "
                   "km), Uruguay (176,000) and Guyana (215,000)."),
    },
    "oceania": {
        "area": ("Australia is by far the largest country in Oceania, at about 7.7 million square "
                 "km; Papua New Guinea is a distant second."),
        "small": ("Nauru is the smallest country in Oceania, at about 21 square km - the smallest "
                  "island country in the world. Tuvalu is next."),
        "people": ("Australia", "Papua New Guinea", "New Zealand", "Fiji", "Solomon Islands"),
        "populous": ("Australia has the most people in Oceania, about 26 million. It is the "
                     "biggest by area too, and Nauru is the smallest."),
        "least": ("Nauru has the fewest people in Oceania, about 12,000, and it is the smallest by "
                  "area too."),
        "top": ("The three biggest countries in Oceania by area are Australia (7.7 million square km), "
                "Papua New Guinea (463,000) and New Zealand (268,000). Australia has by far the most "
                "people too, then Papua New Guinea and New Zealand."),
        "bottom": ("The three smallest countries in Oceania by area are Nauru (21 square km), Tuvalu "
                   "(26) and the Marshall Islands (181)."),
    },
    "caribbean": {
        "area": ("Cuba is the largest country in the Caribbean, at about 110,000 square km; the "
                 "Dominican Republic is second."),
        "small": ("Saint Kitts and Nevis is the smallest country in the Caribbean, at about 260 "
                  "square km, and the smallest in the Americas."),
    },
    # Antarctica has no countries, so every shape says that rather than passing: it is the answer
    # to the question, and Russia is not.
    "antarctica": {
        "area": ("Antarctica has no countries, so there is no biggest one: the whole continent is "
                 "governed by the Antarctic Treaty and the only people there are scientists at "
                 "research stations."),
        "small": ("Antarctica has no countries, so there is no smallest one: it is governed by the "
                  "Antarctic Treaty and the only people there are scientists at research stations."),
        "populous": ("Antarctica has no countries and no permanent residents, only scientists at "
                     "research stations under the Antarctic Treaty."),
        "least": ("Antarctica has no countries and no permanent residents, only scientists at "
                  "research stations under the Antarctic Treaty."),
        "top": ("Antarctica has no countries, so there is no ranking: it is governed by the "
                "Antarctic Treaty and the only people there are scientists at research stations."),
        "bottom": ("Antarctica has no countries, so there is no ranking: it is governed by the "
                   "Antarctic Treaty and the only people there are scientists at research "
                   "stations."),
    },
}


# ---- is a place being crossed? -------------------------------------------------------------
# "Can I bring this food somewhere" is two questions with one set of words: a dish to carry to a
# do, and a food rule at the border. The rows that answer them (travel's `customs-food` and
# occasions' `bring-dish`) have to agree on which one the line is, or the dish row tells somebody
# asking about carrying food into Brazil to bring a traybake. Two hand-written lists of countries
# cannot agree - whatever is left off one gets the picnic - so both rows ask this one reading,
# and it is written as the shape of the line rather than as a list of places.
#
# A line crosses a border when it says so: a crossing word ("back", "home", "abroad", "customs",
# "import", "declare", "duty"), a bag that travels (a suitcase, hold luggage), or a direction
# followed by a place that is not an everyday one. The everyday places only have to cover the
# rooms, buildings and dos a person carries a dish to, which is a short list that people do not
# invent; the places on the other side are countries, which they do - so the country side is read
# from COUNTRIES above and a place that is not in either list is treated as a border, because a
# wrong picnic is worse than a hedge.
_BRITAIN = ("uk", "u.k.", "united kingdom", "britain", "great britain", "england", "scotland",
            "wales", "northern ireland", "country", "the country", "this country",
            "our country", "home", "back home")

_CROSSING_WORD = re.compile(
    r"\b(?:abroad|overseas|customs|import|imports|importing|imported|declare|declaring|duty|"
    r"back home|"
    # "can i bring cheese back" says the return with "back" a word or two after the verb, and the
    # verb is what makes it a return: "back home" is only the same phrase when nothing sits
    # between. "brings it back up" is a dog and its dinner rather than a border, so "back up" is
    # left out of it.
    r"(?:bring|brings|bringing|brought|take|takes|taking|took)\s+"
    r"(?:(?!the\s+back\b)\w+\s+){0,3}?back(?!\s*up\b)|"
    r"from abroad|"
    # "can i bring ham home" says the return without the word "back": the verb and "home" are what
    # make it a crossing, and "what can i bring home for dinner" is the same shape, so it is read
    # as a return too - a dinner question is not a dish-to-a-do question either way.
    r"(?:bring|brings|bringing|brought|take|takes|taking|took)\s+(?:\w+\s+){0,3}?home|"
    r"suitcase|suitcases|luggage|hold bag|hold luggage|"
    r"checked bag|checked luggage|carry-on|carry on bag|rucksack|backpack)\b")

# "from", "into" and "to" are the directions a border is said with. "in" is deliberately not
# here: "bake it in the oven", "in a cool bag" and "in case" are how a dish line talks.
# The words after the direction stop at the next direction word or joining word, so "into the
# country from spain" is read as "the country" and not as "country from".
_DIRECTION = re.compile(
    r"\b(?:from|into|to)\s+(((?!(?:from|into|to|in|at|for|with|and|but|if|when|because|so|on|"
    r"about|before|after)\b)[a-z][a-z'\u2019.-]*\s*){1,3})")

# Rooms, buildings, journeys and dos: the places a dish is carried to, where nothing is crossed.
_EVERYDAY_PLACE = (
    "work", "the office", "office", "school", "nursery", "college", "university", "class",
    "the library", "library", "canteen", "staff room", "cafeteria", "the hospital", "hospital",
    "ward", "clinic", "surgery", "care home", "the church", "church", "mosque", "temple",
    "synagogue", "the restaurant", "restaurant", "cafe", "the pub", "pub", "bar", "cinema",
    "theatre", "theater", "gig", "concert", "festival", "the match", "match", "gym", "club",
    "meeting", "interview", "shift", "the station", "station", "the airport", "airport",
    "ferry", "the ferry", "train", "the train", "bus", "the bus", "coach", "plane", "flight",
    "the car", "campervan", "caravan", "tent", "campsite", "the hotel", "hotel", "hotel room",
    "hostel", "b&b", "airbnb", "house", "flat", "the park", "park", "the beach", "beach",
    "party", "birthday", "dinner", "dinner party", "lunch", "tea", "supper", "brunch",
    "breakfast", "barbecue", "bbq", "picnic", "buffet", "potluck", "bake sale", "wake",
    "funeral", "christening", "wedding", "housewarming", "baby shower", "engagement",
    "anniversary", "reunion", "do", "get-together", "gathering", "playdate", "sleepover",
    "fair", "fete", "market", "sale", "christmas", "easter", "thanksgiving", "hanukkah",
    "diwali", "eid", "mothers day", "fathers day", "a meet", "the class",
)

# A word after "to" is usually a verb, not a place: "can i bring something to eat".
_NOT_A_PLACE = ("eat", "make", "cook", "bake", "bring", "take", "do", "share", "serve", "drink",
                "feed", "contribute", "prepare", "buy", "get", "have", "go", "be", "see", "help",
                "keep", "put", "leave", "give", "add", "use", "find", "stay", "come", "know",
                "say", "ask", "try", "start", "fill", "cover", "heat", "freeze", "store",
                "carry", "hold", "wrap", "cut", "mix", "pick", "choose", "order", "book")

_ARTICLE = re.compile(r"^(?:a|an|the|my|our|his|her|their|your|some|any|this|that|these|those)\s+")


def _bare_place(phrase):
    """The place words after a direction, without the article in front of them."""
    phrase = (phrase or "").strip().strip(".,!?;:")
    while True:
        shorter = _ARTICLE.sub("", phrase, count=1)
        if shorter == phrase:
            return phrase
        phrase = shorter


def directed_place(line):
    """The place a line carries something towards, in its own words, or None.

    "can i bring food into brazil" -> "brazil"; "what should i bring to a dinner party" ->
    "dinner party". The last word of a longer phrase is what decides, so "into the north of
    spain" is read through "north of spain".
    """
    for match in _DIRECTION.finditer(line or ""):
        place = _bare_place(match.group(1))
        if place and place not in _NOT_A_PLACE:
            return place
    return None


def _is_everyday(place):
    """True when the place words name a room, a building or a do rather than a country."""
    place = _bare_place(place)
    for name in _EVERYDAY_PLACE:
        if place == name or place.startswith(name + " ") or place.endswith(" " + name):
            return True
    return False


def _is_a_place(line):
    """The place the line travels towards, if it is one and not an everyday room or do."""
    place = directed_place(line)
    if place is None or _is_everyday(place):
        return None
    return place


def crosses_a_border(line):
    """True when the line carries something across a border rather than to a do.

    `customs-food` speaks only for these lines and `bring-dish` stands down for them, so the two
    rows can never read one line two ways.
    """
    line = (line or "").lower()
    if _CROSSING_WORD.search(line):
        return True
    return _is_a_place(line) is not None


_DESTINATION = re.compile(
    r"\b(?:into|to)\s+(((?!(?:from|into|to|in|at|for|with|and|but|if|when|because|so|on|"
    r"about|before|after)\b)[a-z][a-z'\u2019.-]*\s*){1,3})")


def destination_place(line):
    """The place a line travels into or to, in its own words, or None.

    Only "into" and "to": "back from france" names where the food came from, which is the
    question the Great Britain rule answers, so it is not a destination.
    """
    for match in _DESTINATION.finditer((line or "").lower()):
        place = _bare_place(match.group(1))
        if place and place not in _NOT_A_PLACE:
            return place
    return None


def carries_it_out_of_britain(line):
    """True when the place travelled to is named and is not Britain.

    The food rule in this knowledge base is the one for coming into Great Britain, so a line
    about carrying food into Spain or China is not that row's question: it stands down and the
    bot hedges rather than give one country's rule for another. A line with no place named
    ("can i bring cheese back from france", "can i bring ham home") is coming here, and speaks.
    """
    place = destination_place(line)
    if place is None or _is_everyday(place):
        return False
    return place not in _BRITAIN

_ORDINAL = re.compile(r"\b(?:second|third|fourth|fifth|2nd|3rd|4th|5th)\b")

# Which place an ordinal names, so "the second biggest country in africa by population" can say
# Ethiopia instead of listing the area top three and hoping the reader finds it.
_ORDINAL_POS = {"second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4,
                "fifth": 5, "5th": 5}
_POS_WORD = {2: "second", 3: "third", 4: "fourth", 5: "fifth"}


def _ordinal_position(clean):
    """Which place an ordinal names: 2 for "second" and "2nd", or None."""
    for word, position in _ORDINAL_POS.items():
        if re.search(r"\b" + re.escape(word) + r"\b", clean):
            return position
    return None


def _has(clean, words):
    return any(re.search(r"\b" + re.escape(w) + r"\b", clean) for w in words)


def _region_name(clean):
    """The region a line names, adjectives included, or None.

    "which african country is the largest" names Africa with the adjective, so the plain names in
    _PLACES are not enough on their own.
    """
    for word, region in _CONTINENT_WORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", clean):
            return region
    for name in _PLACES:
        if re.search(r"\b" + re.escape(name) + r"\b", clean):
            return name
    return None


def _region_row(clean, table=None):
    table = table if table is not None else _REGION_COUNTRY
    name = _region_name(clean)
    if name and name in table:
        return table[name]
    # A place that is not a world region - England, the UK, Ireland - is still its own answer
    # where the table has a fact for it, and it must be read before a region word in the line is
    # not. Longest name first, so "northern ireland" is not read as "ireland" and "great britain"
    # is not read as "britain".
    for key in sorted((key for key in table if key not in _PLACES), key=len, reverse=True):
        if re.search(r"\b" + re.escape(key) + r"\b", clean):
            return table[key]
    return None


def country_extreme(kind, world_reply):
    """The region's own largest or smallest country, or the world record on an unqualified line.

    kind is "area" for the biggest and "small" for the smallest; world_reply is the world answer
    the entry already had, so nothing a person got for "the biggest country" changes.
    """
    def answer(memory, understood):
        clean = (understood or {}).get("clean") or ""
        clean = clean.lower()
        row = _region_row(clean)
        if not row:
            return world_reply
        # "the smallest country in asia by area" says the size, not which end of it, so the word
        # smallest decides: the area key alone would answer it with the largest country.
        look = "small" if _has(clean, _RECORD_SMALLEST) else kind
        # "name the three biggest countries in africa" is a list, and one country does not
        # answer it; the plural and the number are what say so.
        ranked = row.get("bottom" if look == "small" else "top")
        # "the second biggest country in africa by population" wants one country, and the area
        # ranking does not name it: the people row does, by count.
        position = _ordinal_position(clean)
        people = row.get("people") or ()
        if position and _has(clean, _RECORD_POPULOUS) and len(people) >= position:
            where = (_region_name(clean) or "").title()
            return ("%s has the %s most people in %s: %s is first, then %s and %s."
                    % (people[position - 1], _POS_WORD[position], where, people[0], people[1],
                       people[2]))
        # "the second biggest country in africa" is answered by the ranked three, which name it in
        # order; the single record would say Algeria, which is confidently wrong there.
        if _ORDINAL.search(clean):
            return ranked or world_reply
        if _RECORD_LIST.search(clean):
            return ranked or world_reply
        return row.get(look) or world_reply
    return answer


# How a line names the continent it means. The adjective first ("which african country is the
# largest"), then the name itself, longest names first so "north america" is not read as
# "america".
_CONTINENT_WORDS = (("north american", "north america"), ("south american", "south america"),
                    ("north america", "north america"), ("south america", "south america"),
                    ("african", "africa"), ("africa", "africa"),
                    ("european", "europe"), ("europe", "europe"),
                    ("asian", "asia"), ("asia", "asia"),
                    ("oceania", "oceania"), ("antarctica", "antarctica"))

# The record words, so a continent count is not read as a record question and the other way round.
_RECORD_BIGGEST = ("biggest", "largest", "biggest by area", "largest by area")
_RECORD_SMALLEST = ("smallest", "tiniest", "smallest by area")
_RECORD_POPULOUS = ("most populous", "most people", "biggest population",
                    "largest population", "most populated", "by population",
                    "in population", "population wise", "by people",
                    # "what is the largest country in africa in terms of population" said the
                    # area answer, because the phrase around "population" was not one of these.
                    "in terms of population", "in terms of people")
_LEAST = ("fewest people", "least populous", "smallest population", "fewest population",
          "smallest by population", "least people", "least in population", "least populated",
          "fewest in population")

# A list question asks for several countries, and one record does not answer it: "name the three
# biggest countries in africa" said "three", and "what are the biggest countries" said the plural.
_LIST_COUNT = r"\b(?:two|three|four|five|six|seven|eight|nine|ten|\d+)\b"
_RECORD_LIST = re.compile(
    r"\b(?:list|top|rank|ranking)\b"
    r"|" + _LIST_COUNT + r"\s+(?:of\s+the\s+)?(?:biggest|largest|smallest|tiniest|populous)"
    # "biggest countries in africa" is a list; the plural has to be part of the question, because
    # the follow-up path appends the subject ("and which one is the biggest countries africa") and
    # that line is one country's record.
    r"|\b(?:biggest|largest|smallest|tiniest|populous)\s+countries\s+(?:in|of)\b")


def _continent_record(memory, understood):
    """Africa's biggest country, Europe's smallest, Asia's most people: the record inside the
    continent the line names, with the record that was asked for first.

    Only a continent this file knows is answered, and Antarctica is answered with the fact that
    it has no countries rather than passed, because that is the answer to the question.
    """
    text = (understood.get("clean") or understood.get("text") or "").lower()
    row = _region_row(text)
    if not row:
        return None

    def has(words):
        return any(re.search(r"\b" + re.escape(w) + r"\b", text) for w in words)

    # "smallest country in Asia by population" is the fewest people, not the least land: the
    # Maldives has less land than Brunei, which has fewer people, so answering the area record
    # there would be confidently wrong.
    if has(_LEAST) or (has(_RECORD_SMALLEST) and has(_RECORD_POPULOUS)):
        return row.get("least")
    if has(_RECORD_POPULOUS):
        return row.get("populous")
    # The plain biggest, the plain smallest and the list shapes are travel.py's biggest-country
    # and smallest-country, which answer from this same table through country_extreme. Answering
    # them here as well would be a second entry for one question, so this one passes.
    return None


# The world record for a river, a mountain or a desert is not the record of the region the line
# names, and passing on those lines ("the longest river in africa") was the bot's most common shrug
# in this domain. The same shape as the country table: a fact per region, written out.
_REGION_EXTREME = {
    "africa": {
        "river": ("The Nile, at about 6,650 km - the longest river in Africa and usually counted "
                  "the longest in the world. The Congo carries far more water."),
        "mountain": ("Kilimanjaro, at 5,895 m, in Tanzania - the highest mountain in Africa, and a "
                     "walk-up rather than a climb, though the altitude is the hard part."),
        "desert": ("The Sahara, at about 9 million square km - the largest hot desert in the world, "
                   "roughly the size of the United States."),
    },
    "europe": {
        "river": ("The Volga, at about 3,530 km, running through Russia to the Caspian Sea. The "
                  "Danube is second, at about 2,850 km, and passes through ten countries."),
        "mountain": ("Mount Elbrus, at 5,642 m, in the Russian Caucasus - the highest in Europe and "
                     "one of the seven summits."),
    },
    "asia": {
        "river": ("The Yangtze, at about 6,300 km - the longest river wholly in Asia. Russia's Ob "
                  "and Yenisei are longer but are only partly in Asia."),
        "mountain": ("Mount Everest, at 8,849 m - the highest in Asia and in the world."),
        "desert": ("The Arabian Desert, at about 2.3 million square km. The Gobi is the biggest cold "
                   "desert, and the Sahara is the biggest hot one - it is in Africa."),
    },
    "north america": {
        "river": ("The Missouri-Mississippi, at about 6,275 km from source to the Gulf of Mexico. "
                  "The Mississippi alone is about 3,770 km."),
        "mountain": ("Denali, at 6,190 m, in Alaska. Mount Logan in Canada is second, at 5,959 m."),
        "desert": ("The Great Basin Desert, at about 490,000 square km, in the western United States. "
                   "The Chihuahuan, shared with Mexico, is the biggest hot one."),
    },
    "south america": {
        "river": ("The Amazon, at about 6,400 km, and far and away the biggest by water - about a "
                  "fifth of all the river water on Earth."),
        "mountain": ("Aconcagua, at 6,961 m, in Argentina - the highest mountain outside Asia."),
        "desert": ("The Patagonian Desert, at about 670,000 square km. The Atacama is the driest "
                   "desert, not the biggest."),
    },
    "oceania": {
        "river": ("The Murray, at about 2,508 km, with the Darling - the longest river system in "
                  "Oceania, running through Australia."),
        "mountain": ("Puncak Jaya, at 4,884 m, in Indonesian Papua. Australia's own highest is Mount "
                     "Kosciuszko, at 2,228 m."),
        "desert": ("The Great Victoria Desert, at about 348,000 square km, in Australia."),
    },
    # The home islands are four countries and a shared island, so each one has its own answer:
    # "the longest river in england" is the Severn and "in scotland" is the Tay, and the world
    # record is neither. Nothing here came back for those lines before.
    "uk": {
        "river": ("The Severn, at about 354 km (220 miles), is the longest river in the UK, rising "
                  "in Wales and reaching the sea past Bristol. The Thames is second at about 346 km."),
        "lake": ("Lough Neagh in Northern Ireland is the largest lake in the UK by area, at about "
                 "383 square km. Loch Ness holds the most water, about 7.5 cubic km."),
        "deep lake": ("Loch Morar is the deepest lake in Britain, at 310 metres, deeper than the "
                      "North Sea is in most places. Loch Ness is 230 metres but holds far more water."),
        "desert": ("There are no deserts in the UK: nowhere here is dry enough to count as one. The "
                   "closest thing is a dune system such as the Sefton coast or Braunton Burrows."),
    },
    "britain": {
        "river": ("The Severn, at about 354 km, is the longest river in Britain, with the Thames "
                  "second at about 346 km and the Trent third."),
        "lake": ("Loch Lomond, at about 71 square km, is the largest lake in Britain by area. "
                 "Windermere is the largest in England at about 14.7 square km."),
        "deep lake": ("Loch Morar, at 310 metres, is the deepest lake in Britain. Loch Ness is "
                      "second at 230 metres and holds more water than all the lakes of England and "
                      "Wales together."),
    },
    "england": {
        "river": ("The Severn, at about 354 km (220 miles), is the longest river in England, though "
                  "it rises in Wales. The Thames is second at about 346 km, and the longest river "
                  "wholly inside England."),
        "lake": ("Windermere is the largest lake in England, about 14.7 square km and 18 km long. "
                 "Wastwater is the deepest, at 74 metres, and was voted Britain's favourite view."),
        "deep lake": ("Wastwater in the Lake District is the deepest lake in England, at 74 metres, "
                      "and the coldest: it is a long narrow trench under the Screes."),
    },
    "scotland": {
        "river": ("The Tay, at about 188 km (117 miles), is the longest river in Scotland and the "
                  "biggest by water, carrying more than the Thames and the Severn together."),
        "lake": ("Loch Lomond is the largest lake in Scotland by area, about 71 square km. Loch "
                 "Ness is bigger by volume and holds more fresh water than all of England and "
                 "Wales put together."),
        "deep lake": ("Loch Morar in the west Highlands is the deepest lake in Scotland and in "
                      "Britain, at 310 metres."),
    },
    "wales": {
        "river": ("The Severn rises in the Welsh hills and is the longest river to run through "
                  "Wales, at about 354 km. The longest river wholly inside Wales is the Tywi, at "
                  "about 120 km."),
        "lake": ("Llyn Tegid, also called Bala Lake, is the largest natural lake in Wales at about "
                 "4.8 square km, and it has its own species of whitefish, the gwyniad."),
    },
    "northern ireland": {
        "river": ("The Bann, at about 129 km, is the longest river in Northern Ireland: the Upper "
                  "Bann feeds Lough Neagh and the Lower Bann carries it to the sea at Coleraine."),
        "lake": ("Lough Neagh is the largest lake in Northern Ireland and in the British Isles, at "
                 "about 383 square km, and it supplies much of Belfast's drinking water."),
    },
    "ireland": {
        "river": ("The Shannon, at about 360 km, is the longest river in Ireland, running from the "
                  "Cavan hills south to Limerick and the Atlantic."),
        "lake": ("Lough Neagh, in Northern Ireland, is the largest lake on the island of Ireland at "
                 "about 383 square km. The largest in the Republic is Lough Corrib, about 176 "
                 "square km, in County Galway."),
    },
    "antarctica": {
        "river": ("There are no real rivers: the Onyx is a seasonal meltwater stream about 30 km "
                  "long, and it is the longest in Antarctica."),
        "mountain": ("Vinson Massif, at 4,892 m - the highest in Antarctica, and the coldest of the "
                     "seven summits."),
        "desert": ("Antarctica is itself the largest desert on Earth, at about 14 million square km: "
                   "a desert is about how little it rains, not about sand."),
    },
}

# The regions this file has no fact for keep passing on those lines, so a named region never gets
# the world answer.
_REGION_EXTREME_WORDS = tuple(_REGION_EXTREME)


def region_extreme(kind, world_reply):
    """The region's own river, mountain or desert; the world answer only on an unqualified line.

    The fallback is _world, so a named place this file has no fact for (a country, a subregion)
    still passes rather than gets the world's answer.
    """
    world = _world(world_reply)

    def answer(memory, understood):
        clean = ((understood or {}).get("clean") or "").lower()
        row = _region_row(clean, _REGION_EXTREME)
        if row is None:
            return world(memory, understood)
        # A known region with no such fact (Europe's desert) passes rather than borrows the world's.
        return row.get(kind)
    return answer


# --- the countries table: which continent, and which countries touch it --------------------
#
# "which countries border france", "what continent is egypt in" and "does spain border
# portugal" are quiz, homework and dinner-table questions people bring to the bot, and every one
# of them was a search hedge: this file knew the world's records but not which countries sit
# next to which. One row per country, keyed by the country's name, so one fact answers every
# wording of the question.
#
# Each row is (continent, land borders, note): the continent is the usual quiz answer, the
# borders are the countries it shares a land border with (a tuple of the names used as keys
# here, so a yes/no answer can compare two rows), and the note is the one thing worth adding -
# a second continent, a bit of the country that is somewhere else. A country with no land
# neighbour has () there, which is the answer, not a missing fact. A country with no row at all
# passes rather than borrows a guess (see `_borders`).
#
# Only land borders: a sea crossing is not a border, and the two places where that is a quiz
# gotcha are in the notes (France's South American border, Spain's two African ones).
COUNTRIES = {
    # --- Europe
    "albania": ("Europe", ("montenegro", "kosovo", "north macedonia", "greece"), ""),
    "andorra": ("Europe", ("france", "spain"), ""),
    "austria": ("Europe", ("germany", "czech republic", "slovakia", "hungary", "slovenia",
                           "italy", "switzerland", "liechtenstein"), ""),
    "belarus": ("Europe", ("poland", "lithuania", "latvia", "russia", "ukraine"), ""),
    "belgium": ("Europe", ("france", "luxembourg", "germany", "netherlands"), ""),
    "bosnia and herzegovina": ("Europe", ("croatia", "serbia", "montenegro"), ""),
    "bulgaria": ("Europe", ("romania", "serbia", "north macedonia", "greece", "turkey"), ""),
    "croatia": ("Europe", ("slovenia", "hungary", "serbia", "bosnia and herzegovina",
                           "montenegro"), ""),
    "cyprus": ("Europe", (), "It is an island in the eastern Mediterranean, closer to Turkey and "
                             "Syria than to Greece, but it is in the EU."),
    "czech republic": ("Europe", ("germany", "poland", "slovakia", "austria"), ""),
    "denmark": ("Europe", ("germany",), ""),
    "estonia": ("Europe", ("latvia", "russia"), ""),
    "finland": ("Europe", ("sweden", "norway", "russia"), ""),
    "france": ("Europe", ("belgium", "luxembourg", "germany", "switzerland", "italy", "monaco",
                          "spain", "andorra"),
               "It also has a border in South America, through French Guiana, with Brazil and "
               "Suriname."),
    "germany": ("Europe", ("denmark", "poland", "czech republic", "austria", "switzerland",
                           "france", "luxembourg", "belgium", "netherlands"), ""),
    "greece": ("Europe", ("albania", "north macedonia", "bulgaria", "turkey"), ""),
    "hungary": ("Europe", ("austria", "slovakia", "ukraine", "romania", "serbia", "croatia",
                           "slovenia"), ""),
    "iceland": ("Europe", (), "It is an island in the North Atlantic, about 290 km from "
                              "Greenland and further from anywhere else."),
    "ireland": ("Europe", ("united kingdom",),
                "The border is the one between the Republic of Ireland and Northern Ireland."),
    "italy": ("Europe", ("france", "switzerland", "austria", "slovenia", "san marino",
                         "vatican city"), ""),
    "kosovo": ("Europe", ("serbia", "montenegro", "albania", "north macedonia"), ""),
    "latvia": ("Europe", ("estonia", "russia", "belarus", "lithuania"), ""),
    "liechtenstein": ("Europe", ("switzerland", "austria"), ""),
    "lithuania": ("Europe", ("latvia", "belarus", "poland", "russia"),
                  "The Russian border is with Kaliningrad, which is cut off from the rest of "
                  "Russia."),
    "luxembourg": ("Europe", ("belgium", "germany", "france"), ""),
    "malta": ("Europe", (), "It is an island country south of Sicily."),
    "moldova": ("Europe", ("romania", "ukraine"), ""),
    "monaco": ("Europe", ("france",), ""),
    "montenegro": ("Europe", ("croatia", "bosnia and herzegovina", "serbia", "kosovo",
                              "albania"), ""),
    "netherlands": ("Europe", ("germany", "belgium"), ""),
    "north macedonia": ("Europe", ("serbia", "kosovo", "bulgaria", "greece", "albania"), ""),
    "norway": ("Europe", ("sweden", "finland", "russia"), ""),
    "poland": ("Europe", ("germany", "czech republic", "slovakia", "ukraine", "belarus",
                          "lithuania", "russia"), ""),
    "portugal": ("Europe", ("spain",), ""),
    "romania": ("Europe", ("ukraine", "moldova", "bulgaria", "serbia", "hungary"), ""),
    "russia": ("Europe and Asia", ("norway", "finland", "estonia", "latvia", "lithuania",
                                   "poland", "belarus", "ukraine", "georgia", "azerbaijan",
                                   "kazakhstan", "china", "mongolia", "north korea"),
               "It is the biggest country in the world, and most of its land is in Asia."),
    "san marino": ("Europe", ("italy",), "It is a tiny country inside Italy."),
    "serbia": ("Europe", ("hungary", "romania", "bulgaria", "north macedonia", "kosovo",
                          "montenegro", "bosnia and herzegovina", "croatia"), ""),
    "slovakia": ("Europe", ("czech republic", "poland", "ukraine", "hungary", "austria"), ""),
    "slovenia": ("Europe", ("italy", "austria", "hungary", "croatia"), ""),
    "spain": ("Europe", ("portugal", "france", "andorra"),
              "It also has two small borders in Africa, with Morocco at Ceuta and Melilla, and "
              "the border with Gibraltar is with the UK."),
    "sweden": ("Europe", ("norway", "finland"), ""),
    "switzerland": ("Europe", ("france", "germany", "austria", "liechtenstein", "italy"), ""),
    "ukraine": ("Europe", ("belarus", "russia", "poland", "slovakia", "hungary", "romania",
                           "moldova"), ""),
    "united kingdom": ("Europe", ("ireland",),
                       "That is the border between Northern Ireland and the Republic of Ireland: "
                       "England, Scotland and Wales are on islands, so they have no land border."),
    "vatican city": ("Europe", ("italy",), "It is the smallest country in the world, inside Rome."),

    # --- Asia
    "afghanistan": ("Asia", ("iran", "pakistan", "china", "tajikistan", "uzbekistan",
                             "turkmenistan"), ""),
    "armenia": ("Asia", ("georgia", "azerbaijan", "iran", "turkey"), ""),
    "azerbaijan": ("Asia", ("russia", "georgia", "armenia", "iran", "turkey"), ""),
    "bahrain": ("Asia", (), "It is an island country in the Persian Gulf, joined to Saudi Arabia "
                            "by a causeway rather than a border."),
    "bangladesh": ("Asia", ("india", "myanmar"), ""),
    "bhutan": ("Asia", ("china", "india"), ""),
    "brunei": ("Asia", ("malaysia",), "It is on the island of Borneo, surrounded by Malaysia."),
    "cambodia": ("Asia", ("thailand", "laos", "vietnam"), ""),
    "china": ("Asia", ("north korea", "russia", "mongolia", "kazakhstan", "kyrgyzstan",
                       "tajikistan", "afghanistan", "pakistan", "india", "nepal", "bhutan",
                       "myanmar", "laos", "vietnam"), ""),
    "georgia": ("Asia", ("russia", "azerbaijan", "armenia", "turkey"),
                "The US state of Georgia is in North America."),
    "india": ("Asia", ("pakistan", "afghanistan", "china", "nepal", "bhutan", "bangladesh",
                       "myanmar"), ""),
    "indonesia": ("Asia", ("malaysia", "papua new guinea", "timor-leste"),
                  "It is the biggest group of islands in the world, with more than 17,000 of them."),
    "iran": ("Asia", ("iraq", "turkey", "armenia", "azerbaijan", "turkmenistan", "afghanistan",
                      "pakistan"), ""),
    "iraq": ("Asia", ("turkey", "iran", "kuwait", "saudi arabia", "jordan", "syria"), ""),
    "israel": ("Asia", ("lebanon", "syria", "jordan", "egypt"),
               "It also borders the West Bank and the Gaza Strip."),
    "japan": ("Asia", (), "It is an island country: four main islands and thousands of small "
                          "ones, with no land border."),
    "jordan": ("Asia", ("israel", "syria", "iraq", "saudi arabia"),
               "It also borders the West Bank."),
    "kazakhstan": ("Asia", ("russia", "china", "kyrgyzstan", "uzbekistan", "turkmenistan"),
                   "It is the biggest landlocked country in the world."),
    "kuwait": ("Asia", ("iraq", "saudi arabia"), ""),
    "kyrgyzstan": ("Asia", ("kazakhstan", "china", "tajikistan", "uzbekistan"), ""),
    "laos": ("Asia", ("china", "myanmar", "thailand", "cambodia", "vietnam"),
             "It is the only country in South East Asia with no coast."),
    "lebanon": ("Asia", ("syria", "israel"), ""),
    "malaysia": ("Asia", ("thailand", "indonesia", "brunei"),
                 "The border with Indonesia is on the island of Borneo."),
    "maldives": ("Asia", (), "It is a chain of about 1,200 islands in the Indian Ocean."),
    "mongolia": ("Asia", ("russia", "china"), ""),
    "myanmar": ("Asia", ("bangladesh", "india", "china", "laos", "thailand"), ""),
    "nepal": ("Asia", ("china", "india"), ""),
    "north korea": ("Asia", ("china", "russia", "south korea"), ""),
    "oman": ("Asia", ("united arab emirates", "saudi arabia", "yemen"), ""),
    "pakistan": ("Asia", ("iran", "afghanistan", "china", "india"), ""),
    "philippines": ("Asia", (), "It is a group of more than 7,000 islands, with no land border."),
    "qatar": ("Asia", ("saudi arabia",), "Saudi Arabia is its only land border."),
    "saudi arabia": ("Asia", ("jordan", "iraq", "kuwait", "qatar", "united arab emirates",
                              "oman", "yemen"), ""),
    "singapore": ("Asia", (), "It is an island city-state joined to Malaysia by a causeway."),
    "south korea": ("Asia", ("north korea",), "North Korea is its only land border."),
    "sri lanka": ("Asia", (), "It is an island south of India."),
    "syria": ("Asia", ("turkey", "iraq", "jordan", "israel", "lebanon"), ""),
    "taiwan": ("Asia", (), "It is an island about 130 km from the coast of China."),
    "tajikistan": ("Asia", ("kyrgyzstan", "china", "afghanistan", "uzbekistan"), ""),
    "thailand": ("Asia", ("myanmar", "laos", "cambodia", "malaysia"), ""),
    "timor-leste": ("Asia", ("indonesia",), "It is on the eastern half of the island of Timor."),
    "turkey": ("Europe and Asia", ("greece", "bulgaria", "georgia", "armenia", "azerbaijan",
                                    "iran", "iraq", "syria"),
               "Most of it is in Asia, with a small part in Europe across the Bosphorus."),
    "turkmenistan": ("Asia", ("kazakhstan", "uzbekistan", "afghanistan", "iran"), ""),
    "united arab emirates": ("Asia", ("saudi arabia", "oman"), ""),
    "uzbekistan": ("Asia", ("kazakhstan", "kyrgyzstan", "tajikistan", "afghanistan",
                            "turkmenistan"), ""),
    "vietnam": ("Asia", ("china", "laos", "cambodia"), ""),
    "yemen": ("Asia", ("saudi arabia", "oman"), ""),

    # --- Africa
    "algeria": ("Africa", ("tunisia", "libya", "niger", "mali", "mauritania", "morocco",
                           "western sahara"), "It is the biggest country in Africa by area."),
    "angola": ("Africa", ("namibia", "zambia", "democratic republic of the congo",
                          "republic of the congo"), ""),
    "benin": ("Africa", ("togo", "burkina faso", "niger", "nigeria"), ""),
    "botswana": ("Africa", ("namibia", "zambia", "zimbabwe", "south africa"), ""),
    "burkina faso": ("Africa", ("mali", "niger", "benin", "togo", "ghana", "ivory coast"), ""),
    "burundi": ("Africa", ("rwanda", "tanzania", "democratic republic of the congo"), ""),
    "cameroon": ("Africa", ("nigeria", "chad", "central african republic", "gabon",
                            "equatorial guinea", "republic of the congo"), ""),
    "cape verde": ("Africa", (), "It is a group of islands in the Atlantic, about 570 km off "
                                 "the coast of West Africa."),
    "central african republic": ("Africa", ("chad", "sudan", "south sudan", "cameroon",
                                            "republic of the congo", "democratic republic of the "
                                            "congo"), ""),
    "chad": ("Africa", ("libya", "sudan", "central african republic", "cameroon", "nigeria",
                        "niger"), ""),
    "djibouti": ("Africa", ("eritrea", "ethiopia", "somalia"), ""),
    "egypt": ("Africa", ("libya", "sudan", "israel"),
              "The Sinai peninsula, across the Suez Canal, is in Asia."),
    "equatorial guinea": ("Africa", ("cameroon", "gabon"), ""),
    "eritrea": ("Africa", ("sudan", "ethiopia", "djibouti"), ""),
    "eswatini": ("Africa", ("south africa", "mozambique"),
                 "It used to be called Swaziland."),
    "ethiopia": ("Africa", ("eritrea", "djibouti", "somalia", "kenya", "south sudan",
                            "sudan"), ""),
    "gabon": ("Africa", ("cameroon", "equatorial guinea", "republic of the congo"), ""),
    "gambia": ("Africa", ("senegal",), "Senegal surrounds it on every side but the sea."),
    "ghana": ("Africa", ("ivory coast", "burkina faso", "togo"), ""),
    "guinea": ("Africa", ("guinea-bissau", "senegal", "mali", "ivory coast", "liberia",
                          "sierra leone"), ""),
    "guinea-bissau": ("Africa", ("senegal", "guinea"), ""),
    "ivory coast": ("Africa", ("liberia", "guinea", "mali", "burkina faso", "ghana"), ""),
    "kenya": ("Africa", ("ethiopia", "somalia", "south sudan", "uganda", "tanzania"), ""),
    "lesotho": ("Africa", ("south africa",), "South Africa surrounds it completely."),
    "liberia": ("Africa", ("sierra leone", "guinea", "ivory coast"), ""),
    "libya": ("Africa", ("tunisia", "algeria", "niger", "chad", "sudan", "egypt"), ""),
    "madagascar": ("Africa", (), "It is the fourth largest island in the world, off the east "
                                 "coast of Africa."),
    "malawi": ("Africa", ("zambia", "tanzania", "mozambique"), ""),
    "mali": ("Africa", ("algeria", "niger", "burkina faso", "ivory coast", "guinea", "senegal",
                        "mauritania"), ""),
    "mauritania": ("Africa", ("western sahara", "algeria", "mali", "senegal"), ""),
    "mauritius": ("Africa", (), "It is an island country in the Indian Ocean."),
    "morocco": ("Africa", ("algeria", "western sahara"),
                "It also borders Spain at Ceuta and Melilla, two small Spanish territories on "
                "its coast."),
    "mozambique": ("Africa", ("tanzania", "malawi", "zambia", "zimbabwe", "south africa",
                              "eswatini"), ""),
    "namibia": ("Africa", ("angola", "zambia", "botswana", "south africa"), ""),
    "niger": ("Africa", ("algeria", "libya", "chad", "nigeria", "benin", "burkina faso",
                         "mali"), ""),
    "nigeria": ("Africa", ("benin", "niger", "chad", "cameroon"), ""),
    "rwanda": ("Africa", ("uganda", "tanzania", "burundi", "democratic republic of the congo"), ""),
    "senegal": ("Africa", ("mauritania", "mali", "guinea", "guinea-bissau", "gambia"), ""),
    "sierra leone": ("Africa", ("guinea", "liberia"), ""),
    "somalia": ("Africa", ("djibouti", "ethiopia", "kenya"), ""),
    "south africa": ("Africa", ("namibia", "botswana", "zimbabwe", "mozambique", "eswatini",
                                "lesotho"),
                     "It completely surrounds Lesotho, which is the third country in the world "
                     "to sit inside another."),
    "south sudan": ("Africa", ("sudan", "ethiopia", "kenya", "uganda",
                               "democratic republic of the congo", "central african republic"), ""),
    "sudan": ("Africa", ("egypt", "libya", "chad", "central african republic", "south sudan",
                         "ethiopia", "eritrea"), ""),
    "tanzania": ("Africa", ("kenya", "uganda", "rwanda", "burundi", "zambia", "malawi",
                            "mozambique", "democratic republic of the congo"), ""),
    "togo": ("Africa", ("ghana", "burkina faso", "benin"), ""),
    "tunisia": ("Africa", ("algeria", "libya"), ""),
    "uganda": ("Africa", ("south sudan", "kenya", "tanzania", "rwanda",
                          "democratic republic of the congo"), ""),
    "western sahara": ("Africa", ("morocco", "algeria", "mauritania"),
                       "It is a disputed territory, not a country most lists count."),
    "zambia": ("Africa", ("angola", "democratic republic of the congo", "tanzania", "malawi",
                          "mozambique", "zimbabwe", "botswana", "namibia"), ""),
    "zimbabwe": ("Africa", ("zambia", "mozambique", "south africa", "botswana"), ""),

    # --- North America and the Caribbean
    "antigua and barbuda": ("North America", (), "It is a group of islands in the Caribbean."),
    "bahamas": ("North America", (), "It is a group of about 700 islands off Florida."),
    "barbados": ("North America", (), "It is an island in the eastern Caribbean."),
    "belize": ("North America", ("mexico", "guatemala"), ""),
    "canada": ("North America", ("united states",),
               "The border with the United States is the longest land border in the world, "
               "about 8,890 km."),
    "costa rica": ("North America", ("nicaragua", "panama"), ""),
    "cuba": ("North America", (), "It is the largest island in the Caribbean."),
    "dominica": ("North America", (), "It is an island in the eastern Caribbean."),
    "dominican republic": ("North America", ("haiti",),
                           "It shares the island of Hispaniola with Haiti."),
    "el salvador": ("North America", ("guatemala", "honduras"), ""),
    "grenada": ("North America", (), "It is an island in the eastern Caribbean."),
    "guatemala": ("North America", ("mexico", "belize", "honduras", "el salvador"), ""),
    "haiti": ("North America", ("dominican republic",),
              "It shares the island of Hispaniola with the Dominican Republic."),
    "honduras": ("North America", ("guatemala", "el salvador", "nicaragua"), ""),
    "jamaica": ("North America", (), "It is an island south of Cuba."),
    "mexico": ("North America", ("united states", "guatemala", "belize"), ""),
    "nicaragua": ("North America", ("honduras", "costa rica"), ""),
    "panama": ("North America", ("costa rica", "colombia"),
               "The border with Colombia is the one where Central America meets South America."),
    "saint kitts and nevis": ("North America", (), "It is a two-island country in the Caribbean."),
    "saint lucia": ("North America", (), "It is an island in the eastern Caribbean."),
    "saint vincent and the grenadines": ("North America", (), "It is a group of Caribbean islands."),
    "trinidad and tobago": ("North America", (), "It is a two-island country off Venezuela."),
    "united states": ("North America", ("canada", "mexico"),
                      "It has 50 states, and Alaska is the part that touches Canada's west."),

    # --- South America
    "argentina": ("South America", ("chile", "bolivia", "paraguay", "brazil", "uruguay"), ""),
    "bolivia": ("South America", ("peru", "brazil", "paraguay", "argentina", "chile"), ""),
    "brazil": ("South America", ("french guiana", "suriname", "guyana", "venezuela", "colombia",
                                 "peru", "bolivia", "paraguay", "argentina", "uruguay"),
               "It borders every country in South America except Chile and Ecuador, and French "
               "Guiana is part of France."),
    "chile": ("South America", ("peru", "bolivia", "argentina"), ""),
    "colombia": ("South America", ("panama", "venezuela", "brazil", "peru", "ecuador"), ""),
    "ecuador": ("South America", ("colombia", "peru"), ""),
    "guyana": ("South America", ("venezuela", "brazil", "suriname"), ""),
    "paraguay": ("South America", ("bolivia", "brazil", "argentina"), ""),
    "peru": ("South America", ("ecuador", "colombia", "brazil", "bolivia", "chile"), ""),
    "suriname": ("South America", ("guyana", "brazil", "french guiana"), ""),
    "uruguay": ("South America", ("brazil", "argentina"), ""),
    "venezuela": ("South America", ("colombia", "brazil", "guyana"), ""),

    # --- Oceania
    "australia": ("Oceania", (), "It is the only country that is a whole continent, so it has no "
                                 "land border."),
    "fiji": ("Oceania", (), "It is a group of more than 300 islands in the Pacific."),
    "new zealand": ("Oceania", (), "It is two main islands in the south Pacific, with no land "
                                   "border."),
    "papua new guinea": ("Oceania", ("indonesia",),
                         "It shares the island of New Guinea with Indonesia."),
    "samoa": ("Oceania", (), "It is an island country in the Pacific."),
    "solomon islands": ("Oceania", (), "It is a group of islands in the Pacific."),
    "tonga": ("Oceania", (), "It is a group of about 170 islands in the Pacific."),
    "vanuatu": ("Oceania", (), "It is a group of islands in the Pacific."),
}

# The French overseas department Brazil borders is part of France, but it is not a country of
# its own, so it is in the border list above and named here for the display.
_NOT_A_COUNTRY = {"french guiana": "French Guiana (France)"}

# The names people use for a country that are not the key in the table. A name in the table is
# its own alias, so the scan below reads this dict and the table together.
_COUNTRY_ALIASES = {
    "usa": "united states", "u s a": "united states", "the united states": "united states",
    "united states of america": "united states", "the states": "united states",
    "uk": "united kingdom", "the uk": "united kingdom", "britain": "united kingdom",
    "great britain": "united kingdom", "the united kingdom": "united kingdom",
    "holland": "netherlands", "burma": "myanmar", "czechia": "czech republic",
    "swaziland": "eswatini", "cabo verde": "cape verde", "macedonia": "north macedonia",
    "east timor": "timor-leste", "ivory coast": "ivory coast", "cote divoire": "ivory coast",
    "uae": "united arab emirates", "the uae": "united arab emirates",
    "saudi": "saudi arabia", "the philippines": "philippines",
    "the netherlands": "netherlands", "the bahamas": "bahamas", "the gambia": "gambia",
    "the congo": "republic of the congo", "drc": "democratic republic of the congo",
    # "the vatican" is the country, and "is the vatican a country" was the pope card
    "vatican": "vatican city", "the vatican": "vatican city", "holy see": "vatican city",
}

# The country names a line can name, longest first, so "south sudan" is not read as "sudan" and
# "north macedonia" not as "macedonia".
_COUNTRY_PHRASES = sorted(set(COUNTRIES) | set(_COUNTRY_ALIASES), key=len, reverse=True)

# Every name a country goes by, for the keys of the entries below: a line says "the uk" and
# "holland" as often as "united kingdom" and "netherlands", and one row should answer both.
_COUNTRY_WORDS = tuple(COUNTRIES) + tuple(_COUNTRY_ALIASES)

# Countries whose name takes "the" in a sentence.
TAKES_THE = ("united states", "united kingdom", "netherlands", "united arab emirates",
             "philippines", "bahamas", "gambia", "maldives", "central african republic",
             "democratic republic of the congo", "republic of the congo")


def _display_country(name):
    """A country key as it is written in a sentence: Czech Republic, the US, Ivory Coast."""
    if name == "united states":
        return "the US"
    if name == "united kingdom":
        return "the UK"
    if name == "united arab emirates":
        return "the UAE"
    if name in _NOT_A_COUNTRY:
        return _NOT_A_COUNTRY[name]
    words = []
    for word in name.split():
        if word in ("and", "of", "the") and words:
            words.append(word)
        elif "-" in word:
            words.append("-".join(part.capitalize() for part in word.split("-")))
        else:
            words.append(word.capitalize())
    return " ".join(words)


def _the_country(name):
    """The name as it reads in a sentence: "France", "the Netherlands", "the UK"."""
    shown = _display_country(name)
    if shown.startswith("the ") or name not in TAKES_THE:
        return shown
    return "the " + shown


def _asked(understood):
    """Whether the line is a question at all, which is what these facts answer.

    A country is named in a great many statements - "my neighbour is from france", "the people
    next door are from poland", "our neighbours in spain are friendly" - and a border is not what
    any of them are about. The understanding engine already reads a line as a question or a
    statement, so these rows only answer the questions and pass on the rest.
    """
    return ((understood or {}).get("kind") or "") == "question"


def _sentence(answer):
    """The reply with its first letter a capital, for the names that start with "the"."""
    return answer[:1].upper() + answer[1:] if answer else answer


def _countries_said(clean):
    """The countries a line names, in the order it says them, as keys into COUNTRIES."""
    found, taken = [], []
    for phrase in _COUNTRY_PHRASES:
        for match in re.finditer(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", clean):
            start, end = match.span()
            if any(before < end and start < after for before, after in taken):
                continue
            taken.append((start, end))
            found.append((start, _COUNTRY_ALIASES.get(phrase, phrase)))
    found.sort()
    said = []
    for _, name in found:
        if name not in said:
            said.append(name)
    return said


def _join_names(names):
    """A list said the way a person says it: one, two and three."""
    names = [_the_country(n) for n in names]
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


# The continents a line can name, and the one thing a list of that continent's countries should
# say about the edges of the list.
_CONTINENTS = {"europe": "Europe", "european": "Europe", "asia": "Asia", "asian": "Asia",
               "africa": "Africa", "african": "Africa", "north america": "North America",
               "south america": "South America", "oceania": "Oceania",
               "australasia": "Oceania"}

_CONTINENT_NOTES = {
    "Europe": "Kosovo is counted by some lists and not others, and Russia and Turkey straddle "
              "Europe and Asia, so the total depends on where you draw the edge.",
    "Asia": "Russia and Turkey are usually counted in Europe as well, and Taiwan is counted by "
            "some lists and not others.",
    "Africa": "Western Sahara is counted by some lists and not others.",
    "North America": "Central America and the Caribbean are part of North America, which is why "
                     "the count is higher than the three big countries people think of.",
    "South America": "It is 12 countries plus French Guiana, which is part of France.",
    "Oceania": "The usual count is 14, with the Pacific island states making up most of them.",
}


# What a continent answer should add, by country: the ones where "X is in Europe" alone is not the
# whole answer a person needs. The note in COUNTRIES is about the country's borders and stays there.
_CONTINENT_NOTES_BY_COUNTRY = {
    "russia": "It is the biggest country in the world, and most of its land is in Asia, but most "
              "of its people live in the European part.",
    "turkey": "Most of it is in Asia, with a small part in Europe across the Bosphorus, and "
              "Istanbul sits on both sides.",
    "egypt": "The Sinai peninsula, across the Suez Canal, is in Asia, which is why Egypt is "
             "sometimes called transcontinental.",
    "georgia": "The US state of Georgia is in North America, not Europe.",
    "cyprus": "It is an island in the eastern Mediterranean, closer to Turkey and Syria than to "
              "Greece, but it is in the EU.",
    "australia": "It is the only country that is a whole continent, which is why the answer is "
                 "both.",
    "kazakhstan": "A small part of it west of the Ural river is in Europe.",
    "spain": "It is in Europe, and it also has two small pieces of land in Africa, Ceuta and "
             "Melilla.",
}


def _continent_said(clean):
    """The continent a line names, as the name this file uses, or None."""
    best = None
    for phrase, name in sorted(_CONTINENTS.items(), key=lambda row: len(row[0]), reverse=True):
        if re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", clean):
            best = name
            break
    return best


def _borders(memory, understood):
    """Which countries touch the one the line names, and whether two of them touch each other."""
    if not _asked(understood):
        return None
    clean = ((understood or {}).get("clean") or "").lower()
    said = _countries_said(clean)
    if not said:
        return None
    first = said[0]
    row = COUNTRIES.get(first)
    if row is None:
        return None
    _, next_to, note = row
    if len(said) > 1:
        other = said[1]
        if other in next_to or first in (COUNTRIES.get(other) or ("", ()))[1]:
            return _sentence("Yes - %s and %s share a border." %
                             (_the_country(first), _display_country(other)))
        return _sentence("No - %s and %s do not share a land border." %
                         (_the_country(first), _display_country(other)))
    if not next_to:
        return _sentence("%s has no land neighbours.%s" %
                         (_the_country(first), (" " + note) if note else ""))
    if re.search(r"\bhow many\b", clean):
        return _sentence("%s has %d land neighbours: %s." %
                         (_the_country(first), len(next_to), _join_names(next_to)))
    answer = "%s borders %s." % (_the_country(first), _join_names(next_to))
    return _sentence(answer + ((" " + note) if note else ""))


def _continent(memory, understood):
    """The continent a named country is in, and whether it is in the one the line names.

    "what continent is egypt in" and "is egypt in africa" are the same fact said two ways, so the
    same row answers both: the second one starts with yes or no and says where it is instead.
    """
    if not _asked(understood):
        return None
    clean = ((understood or {}).get("clean") or "").lower()
    said = _countries_said(clean)
    if not said:
        return None
    row = COUNTRIES.get(said[0])
    if row is None or not row[0]:
        return None
    where = row[0]
    answer = "%s is in %s." % (_the_country(said[0]), where)
    asked = _continent_said(clean)
    if asked is not None and asked.lower() in where.lower() and asked != where:
        # A country in two continents is in the one asked about, so say so before the note.
        answer = "Yes - " + answer
    elif asked is not None and asked != where:
        answer = "No - " + answer
    note = _CONTINENT_NOTES_BY_COUNTRY.get(said[0], "")
    return _sentence(answer + ((" " + note) if note else ""))


def _continent_countries(memory, understood):
    """The countries usually counted in a continent, from the same table the borders come from."""
    if not _asked(understood):
        return None
    clean = ((understood or {}).get("clean") or "").lower()
    region = _continent_said(clean)
    if region is None:
        return None
    members = [name for name, row in COUNTRIES.items() if row[0] == region]
    if not members:
        return None
    return ("The countries usually counted in %s: %s. %s" %
            (region, _join_names(members), _CONTINENT_NOTES.get(region, "")))


# The 27 countries in the EU, as the keys this table uses.
EU_MEMBERS = (
    "austria", "belgium", "bulgaria", "croatia", "cyprus", "czech republic", "denmark",
    "estonia", "finland", "france", "germany", "greece", "hungary", "ireland", "italy", "latvia",
    "lithuania", "luxembourg", "malta", "netherlands", "poland", "portugal", "romania",
    "slovakia", "slovenia", "spain", "sweden",
)

# The countries people ask about by name, with the one thing that explains the answer.
_NOT_IN_EU = {
    "united kingdom": "the UK left the EU on 31 January 2020, after the Brexit vote in 2016.",
    "norway": "it is in the single market through the EEA, so it follows most EU rules without "
              "a vote on them.",
    "switzerland": "it has a set of agreements with the EU instead, and its own currency.",
    "iceland": "it is in the single market through the EEA, and not a member.",
    "turkey": "it has been a candidate for years, and talks have been frozen since 2018.",
    "ukraine": "it applied in 2022 and was made a candidate, but joining takes years.",
    "serbia": "it is a candidate, in talks since 2014.",
    "montenegro": "it is a candidate, and the furthest along of the Balkan countries.",
    "bosnia and herzegovina": "it is a candidate, since 2022.",
    "georgia": "it is a candidate, since 2023.",
    "moldova": "it is a candidate, since 2022.",
    "albania": "it is a candidate, in talks since 2024.",
    "north macedonia": "it is a candidate, in talks since 2022.",
    "kosovo": "it applied in 2022 but is not a candidate, partly because five EU countries do "
              "not recognise it.",
    "russia": "it is not a member and never has been.",
}


def _in_eu(memory, understood):
    """Whether a named country is in the EU, or which countries are."""
    if not _asked(understood):
        return None
    clean = ((understood or {}).get("clean") or "").lower()
    said = _countries_said(clean)
    if not said:
        return ("Twenty-seven countries are in the EU: Austria, Belgium, Bulgaria, Croatia, "
                "Cyprus, Czech Republic, Denmark, Estonia, Finland, France, Germany, Greece, "
                "Hungary, Ireland, Italy, Latvia, Lithuania, Luxembourg, Malta, the Netherlands, "
                "Poland, Portugal, Romania, Slovakia, Slovenia, Spain and Sweden.")
    country = said[0]
    if re.search(r"\b(leave|leaves|leaving|left|quit|quitting|brexit)\b", clean):
        # "did britain leave the eu" is asked from the other side: yes, and when.
        if country == "united kingdom":
            return ("Yes - the UK left the EU on 31 January 2020, after the Brexit vote in 2016. "
                    "It has been outside the single market and customs union since then.")
        if country in EU_MEMBERS:
            return _sentence("No - %s is still in the EU; it is one of the 27 members." %
                             _the_country(country))
        return _sentence("No - %s was never in the EU, so there was nothing to leave." %
                         _the_country(country))
    if country in EU_MEMBERS:
        return _sentence("Yes - %s is one of the 27 countries in the EU." %
                         _the_country(country))
    reason = _NOT_IN_EU.get(country)
    if reason:
        return _sentence("No - %s is not in the EU: %s" % (_the_country(country), reason))
    return _sentence("No - %s is not in the EU." % _the_country(country))


# "What is the difference between Great Britain and the UK" and "is England the same as
# Britain" are the same question the row above already answers for one nation at a time: which of
# these names is which. Nothing answered them - both were search hedges - and "is england the same
# as britain" was worse than a hedge: the travel row that keys a country with "same" answered
# "England uses the same three square pins as the UK, so what you bring from home fits". The word
# that makes it a comparison is the key here, and the travel row no longer keys it.
_COMPARES_NATIONS = ("difference between", "different from", "same as", "the same", "difference",
                     "versus", " vs ", "or britain", "or the uk", "or england", "british isles",
                     "great britain", "the uk and britain", "britain and the uk")


def _the_nations_explained():
    """The one explanation every comparison of these names comes to."""
    return ("Great Britain is the island: England, Scotland and Wales. The UK is the country, "
            "which is that island plus Northern Ireland. So England is in Britain and in the UK, "
            "Northern Ireland is in the UK but not in Britain, and the British Isles is only "
            "geography - both islands, including the Republic of Ireland, which is a separate "
            "country.")


# "Is X part of Y" names two of these names, and the answer is about that pair, not about the
# UK. The row answered every one of them with "Yes - England is part of the UK", because it read
# whichever part the line named first and never read the thing it was being asked to be part of:
#
#     is wales part of england             -> "Yes - England is part of the UK."
#     is scotland part of england          -> "Yes - England is part of the UK."
#     is northern ireland part of england  -> "Yes - England is part of the UK."
#
# Wales, Scotland and Northern Ireland are not in England, so "yes" is a confident wrong answer
# to every one of them - worse than the hedge main gave. Where the thing after "part of" is the
# UK the old sentence is right and this returns None, so it is the answer as before.
_NATION_NAMED = re.compile(
    r"\b(northern ireland|great britain|united kingdom|england|scotland|wales|britain|uk|"
    r"ireland|europe)\b")
_NATION_SAID = {"uk": "the UK", "united kingdom": "the UK", "britain": "Britain",
                "great britain": "Great Britain", "england": "England",
                "scotland": "Scotland", "wales": "Wales",
                "northern ireland": "Northern Ireland", "ireland": "Ireland"}
_THE_FOUR = ("england", "scotland", "wales", "northern ireland")


def _the_pair_a_part_of_names(clean):
    """The answer for "is X part of Y" when both are named, or None when the UK is the answer."""
    split = re.search(r"\bpart of\b", clean)
    if not split:
        return None
    before = _NATION_NAMED.findall(clean[:split.start()])
    after = _NATION_NAMED.findall(clean[split.end():])
    if not before or not after:
        return None
    one, two = before[-1], after[0]
    if one == two:
        return None
    if two in ("uk", "united kingdom"):
        return None                     # "is england part of the uk" is the sentence it was
    if two == "europe":
        if one in _THE_FOUR or one in ("britain", "great britain", "uk", "united kingdom"):
            return ("Yes - %s is in Europe. Every part of the UK is: the UK left the European "
                    "Union in 2020, but it never left the continent." % _NATION_SAID[one])
        return ("Yes - Ireland is in Europe, and in the European Union. It is a separate country "
                "from the UK: only Northern Ireland is part of the UK.")
    if one in _THE_FOUR and two in _THE_FOUR:
        return ("No - %s is not part of %s. They are both part of the UK, which is England, "
                "Scotland, Wales and Northern Ireland." % (_NATION_SAID[one], _NATION_SAID[two]))
    if two in ("britain", "great britain"):
        if one in ("northern ireland", "ireland"):
            return ("No - %s is not in Great Britain: Great Britain is England, Scotland and "
                    "Wales.%s" % (_NATION_SAID[one],
                                  " Northern Ireland is in the UK all the same, on the island "
                                  "of Ireland." if one == "northern ireland" else
                                  " The Republic of Ireland is a separate country."))
        return ("Yes - %s is part of Great Britain, the island that also has %s on it. Great "
                "Britain and Northern Ireland together are the UK."
                % (_NATION_SAID[one],
                   "England and Wales" if one == "scotland" else
                   "Scotland and Wales" if one == "england" else "England and Scotland"))
    if two in ("ireland",) and one in _THE_FOUR:
        return ("No - %s is not part of Ireland. Ireland is a separate country; %s"
                % (_NATION_SAID[one],
                   "Northern Ireland is the part of the UK on the same island."
                   if one == "northern ireland" else
                   "it shares its island with Northern Ireland, which is part of the UK."))
    return None


def _uk_part(memory, understood):
    """Whether a part of the UK is in the UK, and whether Ireland is one of them."""
    clean = ((understood or {}).get("clean") or "").lower()

    def says(phrase):
        return re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", clean) is not None

    comparison = (says("british isles") or says("difference") or says("same")
                  or says("versus") or says(" vs "))
    # "is great britain the same as england" is read as a statement - there is no "?" on it and
    # "is" opens it - so the question gate would pass on a comparison. A comparison of two of
    # these names is a question about them however it is written, and the answer is the same.
    if not _asked(understood) and not comparison:
        return None
    if comparison:
        return _the_nations_explained()
    pair = _the_pair_a_part_of_names(clean)
    if pair is not None:
        return pair
    if says("northern ireland"):
        part = "Northern Ireland"
    elif says("ireland"):
        return ("No - Ireland is not part of the UK. The Republic of Ireland is a separate "
                "country; Northern Ireland is the part of the UK on the same island. Great "
                "Britain is England, Scotland and Wales.")
    else:
        part = next((name.title() for name in ("england", "scotland", "wales") if says(name)),
                    None)
    if part is None:
        return None
    if says("a country") or says("independent country") or says("sovereign"):
        # "is scotland a country" is a yes with a caveat: a country, not a sovereign state.
        if part == "Northern Ireland":
            return ("Northern Ireland is called a province or a region rather than a country, "
                    "but it is part of the UK all the same: the UK is England, Scotland, Wales "
                    "and Northern Ireland.")
        return ("Yes - %s is a country, one of the four in the UK. It is not a sovereign state "
                "on its own: the UK is the country that sits at the UN and signs treaties." %
                part)
    if says("independent") or says("separate country"):
        return ("No - %s is not a separate country: it is one of the four parts of the UK, "
                "along with England, Scotland, Wales and Northern Ireland. The UK is the "
                "country." % part)
    return ("Yes - %s is part of the UK. The UK is England, Scotland, Wales and Northern "
            "Ireland; Great Britain is the island with the first three on it." % part)


_RIVER_NAMES = ("nile", "amazon", "mississippi", "missouri", "danube", "volga", "yangtze",
                "congo", "rhine", "seine", "thames", "loire", "po", "tagus", "elbe", "oder",
                "ganges", "indus", "mekong", "yellow river", "ob", "yenisei", "murray",
                "darling", "colorado", "rio grande", "parana", "orinoco", "niger", "zambezi",
                "yangtze kiang", "amur", "lena", "irrawaddy", "euphrates", "tigris")

# One sentence each, the length first, because the length is what the line asked for. The
# figures are the usual published ones: where the source is disputed the card says about.
_RIVER_LENGTHS = (
    ("nile", "The Nile runs about 6,650 km from its source to the Mediterranean, which makes it "
             "the longest river in Africa and usually the longest in the world - with the Amazon "
             "a close second and carrying far more water."),
    ("amazon", "The Amazon runs about 6,400 km from its source in the Peruvian Andes to the "
               "Atlantic, and it is the biggest river in the world by water - about a fifth of "
               "all the river water on Earth."),
    ("mississippi", "The Mississippi is about 3,770 km from Minnesota to the Gulf of Mexico, or "
                    "about 6,275 km if you count the Missouri from its source, which is how it "
                    "is usually measured."),
    ("missouri", "The Missouri is about 3,767 km, from Montana to where it joins the "
                 "Mississippi near St Louis - the longest river in North America on its own."),
    ("danube", "The Danube runs about 2,850 km from Germany's Black Forest to the Black Sea, "
               "through ten countries - more than any other river in the world."),
    ("volga", "The Volga runs about 3,530 km through Russia to the Caspian Sea, the longest "
              "river in Europe."),
    ("yangtze", "The Yangtze runs about 6,300 km across China to the sea at Shanghai, the "
                "longest river in Asia."),
    ("congo", "The Congo runs about 4,700 km, the deepest river in the world and second only to "
              "the Amazon by water."),
    ("rhine", "The Rhine runs about 1,230 km from the Swiss Alps to the North Sea at Rotterdam, "
              "and it is the busiest freight river in Europe."),
    ("seine", "The Seine runs about 775 km, from Burgundy through Paris to the sea at Le Havre."),
    ("thames", "The Thames runs about 346 km, from the Cotswolds through London to the Thames "
               "Estuary."),
    ("loire", "The Loire runs about 1,006 km, the longest river in France, from the Massif "
              "Central to the Atlantic at Saint-Nazaire."),
    ("po", "The Po runs about 652 km across northern Italy to the Adriatic, the longest river in "
           "Italy."),
    ("tagus", "The Tagus runs about 1,007 km from Spain through Portugal to Lisbon and the "
              "Atlantic, the longest river on the Iberian peninsula."),
    ("elbe", "The Elbe runs about 1,094 km from the Czech Republic through Germany to the North "
             "Sea at Hamburg."),
    ("oder", "The Oder runs about 840 km from the Czech Republic to the Baltic, most of it along "
             "the border between Germany and Poland."),
    ("ganges", "The Ganges runs about 2,525 km from the Himalayas to the Bay of Bengal, and "
               "with its delta it is one of the most populous river basins in the world."),
    ("indus", "The Indus runs about 3,180 km from Tibet through Pakistan to the Arabian Sea, and "
              "the civilisation along it was one of the first cities anywhere."),
    ("mekong", "The Mekong runs about 4,350 km from the Tibetan plateau through China, Laos, "
               "Thailand, Cambodia and Vietnam to the South China Sea."),
    ("yellow river", "The Yellow River runs about 5,464 km across northern China, the second "
                     "longest in the country after the Yangtze."),
    ("ob", "The Ob runs about 3,650 km across Siberia to the Arctic Ocean, or about 5,410 km "
           "with its main tributary, the Irtysh."),
    ("yenisei", "The Yenisei runs about 3,487 km across Siberia to the Arctic, and with its "
                "headwaters it is one of the longest river systems in the world."),
    ("murray", "The Murray runs about 2,508 km through Australia to the sea in South Australia, "
               "and with the Darling it is the longest river system in the country."),
    ("darling", "The Darling runs about 1,472 km through New South Wales and Queensland, the "
                "longest single river in Australia."),
    ("colorado", "The Colorado runs about 2,330 km from the Rocky Mountains to the Gulf of "
                 "California, through the Grand Canyon on the way."),
    ("rio grande", "The Rio Grande runs about 3,051 km from Colorado to the Gulf of Mexico, and "
                   "it forms the border between Texas and Mexico."),
    ("parana", "The Parana runs about 4,880 km through Brazil, Paraguay and Argentina to the "
               "Rio de la Plata, second in South America only to the Amazon."),
    ("orinoco", "The Orinoco runs about 2,140 km through Venezuela to the Atlantic, and it links "
                "to the Amazon through a natural channel, the Casiquiare."),
    ("niger", "The Niger runs about 4,200 km in a great curve through West Africa to the Gulf of "
              "Guinea, the longest river in the region."),
    ("zambezi", "The Zambezi runs about 2,574 km through southern Africa to the Indian Ocean, and "
                "Victoria Falls is on it."),
    ("amur", "The Amur runs about 2,824 km along the border between Russia and China to the "
             "Pacific, or about 4,444 km with its headwaters."),
    ("lena", "The Lena runs about 4,400 km across Siberia to the Arctic Ocean, and it freezes "
             "solid for months each winter."),
    ("irrawaddy", "The Irrawaddy runs about 2,170 km through Myanmar to the sea, the country's "
                  "main river for transport and rice."),
    ("euphrates", "The Euphrates runs about 2,800 km from Turkey through Syria and Iraq to the "
                  "Shatt al-Arab, where it joins the Tigris."),
    ("tigris", "The Tigris runs about 1,850 km from Turkey through Iraq to the Shatt al-Arab, "
               "and the land between it and the Euphrates is ancient Mesopotamia."),
)

_RIVER_NAME_NEEDS_RIVER = frozenset(("amazon", "po", "ob", "lena", "darling", "congo", "niger",
                                    "elbe", "oder", "amur", "parana", "colorado", "murray"))

_RIVER_LENGTH_ASK = re.compile(
    r"\b(how long|how far|long is|length|km|kilometres|kilometers|miles|distance)\b")


def _river_length(memory, reading):
    """The length of the river the line names, or None when it names none of them."""
    clean = str((reading or {}).get("text") or (reading or {}).get("clean") or "").lower()
    if not _RIVER_LENGTH_ASK.search(clean):
        return None
    for name, text in _RIVER_LENGTHS:
        if not re.search(r"\b" + re.escape(name) + r"\b", clean):
            continue
        # "amazon" is a shop, "po" is a post office and "darling" is somebody's name, so those
        # only count when the line says river as well: "how long is the amazon prime
        # subscription" was answered with the length of the Amazon.
        if name in _RIVER_NAME_NEEDS_RIVER and not re.search(r"\briver\b", clean):
            continue
        return text
    return None


ENTRIES = [
    entry("continent-record", ((_RECORD_BIGGEST + _RECORD_SMALLEST + _RECORD_POPULOUS + _LEAST),
                               ("africa", "african", "europe", "european", "asia", "asian",
                                "north america", "north american", "south america",
                                "south american", "oceania", "antarctica")),
          _continent_record, bias=1,
          # The count, the world record and the other records a continent has are other questions.
          # A country's size is one record among many (an economy, a mountain, a second place),
          # and a subregion such as South East Asia has its own biggest country, so those pass.
          avoid=("how many", "number of", "count", "world", "highest", "longest", "deepest",
                 "mountain", "river", "lake", "desert", "island", "islands", "ocean", "sea",
                 "city", "cities", "capital", "continent", "continents",
                 "economy", "economies", "gdp", "richest", "poorest", "wealthiest", "richer",
                 "poorer", "second", "third", "fourth", "fifth", "next biggest",
                 "south east asia", "southeast asia", "east asia", "central asia", "south asia",
                 "west africa", "east africa", "north africa", "southern africa", "sub saharan",
                 "western europe", "eastern europe", "northern europe", "southern europe",
                 "middle east", "european union", "scandinavia", "balkans", "latin america")),
    entry("countries-count", ("countries", ("how many", "world", "in the world")),
          _world("The usual answer is 195: 193 members of the United Nations plus the Vatican and "
                 "Palestine, which are observers. Some lists count Taiwan or Kosovo, which is why "
                 "you sometimes see 196 or 197."),
          avoid=("largest", "biggest", "smallest", "tiniest", "populous",
                 "have i", "i've", "ive", "been to", "visited", "africa", "europe", "asia",
                 "north america", "south america", "oceania", "antarctica", "uk",
                 "united kingdom", "britain", "great britain", "states",
                 "have", "has", "with", "without", "allow", "allows", "legal", "ban",
                 "bans", "speak", "speaks", "drive", "use", "recognise", "recognize",
                 # "how many countries border russia" is the neighbour count, not the world's
                 # 195: country-borders answers it from COUNTRIES in this file.
                 "border", "borders", "next to", "neighbour", "neighbours", "adjacent")),
    entry("countries-healthcare", ("countries", ("free healthcare", "free health care",
                                                  "universal healthcare", "universal health care",
                                                  "healthcare", "health care")),
          ("There's no single number: it depends whether you count tax-funded systems, insurance "
           "schemes and small fees. The WHO's universal health coverage index and Our World in "
           "Data's country list are the usual places to check the current figure."),
          avoid=_REGIONS + ("in the world",)),
    entry("continent-count", ("countries", ("africa", "europe", "asia", "north america",
                                            "south america", "oceania", "antarctica")),
          _continent_count,
          avoid=("largest", "biggest", "smallest", "tiniest", "populous",
                 "richest", "poorest", "most populous", "population",
                 # "the biggest country in africa" is a question about one country, not a
                 # count: Algeria is the largest by area and Nigeria the most populous, and
                 # the count reply answers a question nobody asked. The plural "countries" is
                 # the key and a plural in -ies now reads as its singular, so the record words
                 # are needed for the records this file answers and the ones it passes on.
                 "longest", "shortest", "tallest", "highest", "lowest", "deepest", "cheapest",
                 "have i", "i've", "ive", "been to", "visited", "which", "list", "name",
                 "speak", "language", "languages", "currency", "euro", "capital",
                 "monarchy", "monarchies", "free", "healthcare", "health care",
                 "death penalty", "capital punishment", "abortion", "weed", "marijuana",
                 "same sex", "gay marriage", "drive", "recognise", "recognize")),
    entry("uk-countries", ("countries", ("uk", "united kingdom", "britain", "great britain")),
          "The UK is four countries: England, Scotland, Wales and Northern Ireland. Great "
          "Britain is the island with the first three on it, which is why people mix the two up.",
          # "which countries are in the uk" is the same question, so it is not avoided here.
          avoid=("city", "cities", "capital", "have i", "visited",
                 "have", "has", "with", "without")),
    entry("us-states", ("states", ("us", "usa", "united states", "america")),
          "The United States has 50 states, plus Washington DC, which is a federal district rather "
          "than a state. Alaska and Hawaii are the two outside the mainland.",
          avoid=("australia", "india", "mexico", "brazil", "south america", "north america",
                 "central america", "have i", "been to", "visited", "which", "list", "name",
                 # "capital of united states" said without "the" is the capitals question, and
                 # the count of states is not the answer to it.
                 "capital", "capital city",
                 "have", "has", "with", "without", "legal", "allow", "allows", "banned",
                 "ban", "weed", "marijuana", "abortion", "vote")),
    # A named peak's own height: "how tall is ben nevis" wants 1,345 metres, not Everest, and the
    # world answer below steps aside for every peak in the table.
    entry("named-peak", (tuple(PEAKS),
                         ("high", "higher", "height", "tall", "taller", "metres", "meters",
                          "feet", "how high", "how tall", "summit", "big")),
          _peak),
    # "the highest mountain in Wales" names no peak, so the peak table cannot reach it.
    entry("highest-in-place", (("highest", "tallest", "high", "biggest", "highest mountain"),
                               ("mountain", "mount", "peak", "point", "summit")),
          _highest_in_place),
    entry("highest-mountain", (("mountain", "mount", "everest"),
                               ("highest", "tallest", "everest", "world", "tall", "high",
                                "how", "metres", "feet", "big")),
          region_extreme("mountain",
                         "Mount Everest is the highest, at 8,849 metres (29,032 feet) above sea "
                         "level. Measured from the base to the summit, Mauna Kea in Hawaii is "
                         "taller, because most of it is under the sea."),
          # a named peak that is not Everest ("how tall is ben nevis") is a different fact,
          # so the line has to be about the highest one
          ask=("everest", "highest", "tallest", "world"),
          avoid=("how many", "number of", "count", "climb", "climbing", "deaths", "died")
          # every peak and place named in the tables above is its own answer: the highest in
          # Wales is Snowdon, and "how tall is ben nevis" is not a world record question
          + tuple(PEAKS) + tuple(HIGHEST_IN)),
    entry("oceans-count", (("ocean", "oceans", "sea"), ("how many", "five", "world", "largest",
                                                        "biggest", "deepest", "deep")),
          _world("There are five oceans: Pacific, Atlantic, Indian, Southern and Arctic. The "
                 "Pacific is the biggest and deepest; its Mariana Trench goes down about 11 km, "
                 "deeper than Everest is tall."),
          avoid=("how deep", "how far down", "depth", "deep is")),
    entry("ocean-depth", (("ocean", "oceans", "sea"), ("how deep", "how far down", "depth",
                                                      "mariana", "trench")),
          _world("The ocean averages about 3.7 km deep. The deepest point is the Mariana Trench "
                 "in the Pacific, at about 10.9 km down - if Everest stood there, its summit would "
                 "still be more than 2 km under the surface.")),
    entry("continents-count", (("continent", "continents"), ("how many", "seven", "world")),
          _world("Seven is the usual count: Africa, Antarctica, Asia, Europe, North America, "
                 "Oceania and South America. Some countries teach six, joining Europe and Asia "
                 "into Eurasia."),
          avoid=("largest", "biggest", "smallest")),
    entry("world-population", (("population", "people"), ("world", "earth")),
          _world("About 8.2 billion people, and it is still rising, though more slowly. India "
                 "passed China as the most populous country in 2023, and both have around 1.4 "
                 "billion."),
          avoid=("hungry", "starving", "poor", "without", "have", "has", "live in", "living in",
                 "speak", "speaking", "died", "die", "born", "own", "use", "need")),
    entry("largest-desert", ("desert", ("largest", "biggest", "hot", "world")),
          region_extreme("desert",
                         "Antarctica is technically the largest desert, because a desert is "
                         "defined by how little it rains. The Sahara is the largest hot desert, at "
                         "about 9 million square kilometres, roughly the size of the United States."),
          avoid=("how many deserts", "number of deserts", "count deserts")),
    entry("largest-island", ("island", ("largest", "biggest", "world")),
          _world("Greenland is the largest island, at about 2.2 million square kilometres. "
                 "Australia is bigger but is counted as a continent rather than an island, which "
                 "is the usual quiz gotcha."),
          avoid=("how many islands", "number of islands", "count islands")),
    # "what is the smallest country in the world" was answered with Russia, because travel.py's
    # biggest-country reads "country" plus the word world and won the tie. The nudge is a
    # tie-break rather than a stand-down there, because "the smallest country in asia by area" is
    # the same question and already had the right answer from that entry.
    entry("smallest-country", ("country", ("smallest", "world")),
          country_extreme("small", "Vatican City is the smallest country, at about 0.49 square "
                                   "kilometres and roughly 800 people. Monaco is the second "
                                   "smallest, and both are smaller than most city parks."),
          bias=2,
          # The end of the scale the line names decides which row answers: a line that says
          # "largest" or "biggest" ties this row with the biggest-country row on "country" and
          # "world", and the bias below handed it the smallest answer. The other end stands
          # this row down. None of these words is in this row's own key.
          avoid=("how many countries", "number of countries", "count countries",
                 "largest", "biggest", "largest by area", "biggest by area",
                 # A country's size is its area, so a line that asks how many people live there
                 # is a population question: "most populous country in the world" came back as
                 # Vatican City, the smallest country in the world.
                 "population", "populous", "people live", "inhabitants", "most people",
                 "have", "has", "with", "without", "allow", "allows", "legal", "ban", "bans")),

    # --- the world records people ask in quizzes and homework ---------------------
    entry("largest-continent", ("continent", ("largest", "biggest", "world")),
          _world("Asia is the largest continent, at about 44.6 million square kilometres - roughly "
                 "30% of the world's land. Africa is second and Antarctica third."),
          avoid=("how many", "number of", "count", "smallest")),
    entry("smallest-continent", ("continent", ("smallest", "world")),
          _world("Australia is the smallest continent, at about 8.6 million square kilometres. "
                 "Some lists call the region Oceania, which also includes New Zealand and the "
                 "Pacific islands, but Australia is the continent itself."),
          avoid=("how many", "number of", "count", "largest", "biggest")),
    entry("highest-waterfall", (("waterfall", "falls"), ("highest", "tallest", "world")),
          _world("Angel Falls in Venezuela is the highest waterfall, at 979 metres. Its water "
                 "drops in one unbroken fall of about 807 metres, so it is still falling long "
                 "after Niagara would have hit the bottom.")),
    entry("largest-lake", ("lake", ("largest", "biggest", "world")),
          region_extreme("lake",
                         "The Caspian Sea is the largest lake, at about 371,000 square kilometres, "
                         "and it is salty. Lake Superior is the largest freshwater lake by area; "
                         "Lake Baikal holds the most fresh water."),
          avoid=("how many", "number of", "count", "deep", "deepest", "depth",
                 "near me", "nearby", "local", "around here")),
    entry("deepest-lake", ("lake", ("deepest", "depth", "deep")),
          region_extreme("deep lake",
                         "Lake Baikal in Siberia is the deepest lake, at 1,642 metres. It holds "
                         "about a fifth of the world's unfrozen fresh water, more than all the "
                         "Great Lakes together."),
          avoid=("largest", "biggest", "near me", "nearby", "local", "around here")),
    entry("longest-mountain-range", (("mountain range", "range of mountains"),
                                     ("longest", "biggest", "world")),
          _world("The Andes is the longest mountain range above sea level, running about 7,000 km "
                 "down the west of South America. The Mid-Atlantic Ridge is longer, but almost all "
                 "of it is under the sea.")),
    entry("hottest-place", ("hottest", ("place", "earth", "world", "temperature", "ever",
                                        "recorded")),
          _world("Death Valley in California holds the highest air temperature reliably recorded: "
                 "56.7C in 1913. The Danakil Depression in Ethiopia and Dasht-e Lut in Iran are "
                 "often called the hottest places on average, because they are hot for longer."),
          ask=("place", "earth", "world", "planet", "on earth", "in the world", "temperature")),
    entry("coldest-place", ("coldest", ("place", "earth", "world", "temperature", "ever",
                                        "recorded")),
          _world("Antarctica is the coldest place on Earth: Vostok Station recorded -89.2C in "
                 "1983. The coldest place with people living in it is Oymyakon in Siberia, where "
                 "winter temperatures reach about -50C."),
          ask=("place", "earth", "world", "planet", "on earth", "in the world", "temperature")),

    # --- which continent, and which countries touch it ------------------------------------
    #
    # One row per country in COUNTRIES answers three questions: the continent ("what continent is
    # egypt in"), the neighbours ("which countries border france", "does spain border portugal",
    # "how many countries border russia") and both, when the line asks both. The ask list keeps
    # the table off every other line that names a country: a holiday, a move or a news story is
    # not a geography question.
    entry("country-borders",
          (_COUNTRY_WORDS, ("border", "borders", "bordering", "next to", "neighbour",
                              "neighbours", "neighbouring", "neighboring", "neighbor",
                              "neighbors", "adjacent", "touches", "touch", "share a border",
                              "shares a border", "land border", "adjoin", "adjoins")),
          _borders,
          ask=("border", "borders", "bordering", "next to", "neighbour", "neighbours",
               "neighbouring", "neighboring", "neighbor", "neighbors", "adjacent", "touches",
               "share a border", "shares a border", "land border", "adjoin", "adjoins"),
          # A trip, a move or a person over there is a different question, and a country named
          # in passing is not a geography question at all.
          avoid=("holiday", "holidays", "trip", "visit", "visiting", "move", "moving", "moved",
                 "emigrate", "immigrate", "visa", "flight", "flights", "fly", "flying",
                 "going", "went", "been", "live", "lives", "living", "relocate",
                 "hotel", "stay", "staying", "drive", "driving", "work there", "job there")),
    entry("country-continent",
          (_COUNTRY_WORDS, ("continent", "continents", "which continent", "what continent",
                            "part of the world", "europe", "european", "asia", "asian",
                            "africa", "african", "north america", "south america", "oceania")),
          _continent,
          ask=("continent", "continents", "part of the world", "in europe", "in asia",
               "in africa", "in north america", "in south america", "in oceania"),
          avoid=("holiday", "trip", "visit", "move", "moving", "emigrate", "visa", "flight",
                 "go to", "going to", "honeymoon", "live in", "living in",
                 # "is france in the eu" and "is england in europe at the euros" are membership
                 # and sport questions, not the continent.
                 "eu", "euros 20", "european union", "world cup", "olympics", "qualify")),
    entry("eu-membership",
          (_COUNTRY_WORDS + ("eu", "european union"),
           ("eu", "european union", "in the eu", "member", "members", "part of", "join",
            "joined", "belong")),
          _in_eu,
          ask=("eu", "european union"),
          # A euro is money and a European holiday is a trip, so the two-letter word has to be
          # the union itself before this row answers.
          avoid=("holiday", "trip", "visa", "flight", "travel", "moving", "live", "living",
                 "work there", "study there", "euro note", "euro coin", "euros", "exchange")),
    entry("continent-countries",
          (("europe", "european", "asia", "asian", "africa", "african", "north america",
            "south america", "oceania"),
           ("which countries", "what countries", "countries", "names of the countries")),
          _continent_countries,
          ask=("which countries", "what countries", "countries"),
          # A count is its own question and has its own row, and a trip is not a list of countries.
          avoid=("how many", "number of", "visit", "holiday", "trip", "best", "should i",
                 "worth", "cheap", "expensive", "go to", "moving", "live", "fly", "flight",
                 "city", "cities", "capital")),
    entry("most-people-country",
          (("most people", "most populous", "biggest population", "largest population",
            "most population", "highest population", "most populated",
            # "largest country by population" measures people, not area: without the bare word
            # the line was answered with Russia, the biggest country by area.
            "population", "populous"),
           ("country", "countries", "nation", "world")),
          _world("India has the most people, at about 1.45 billion, just ahead of China at "
                 "about 1.41 billion since 2023. The United States is a distant third, at about "
                 "340 million."),
          avoid=("city", "cities", "town", "state", "states", "continent", "county", "counties",
                 "in my", "school", "class", "office", "team", "street")),
    # "how long is the nile" and "how long is the amazon river" had no answer at all, and the
    # Amazon one was answered by the cancel-a-subscription card, because "amazon" plus "how" is a
    # subscription even when the line says river. The length is the fact people ask for by name,
    # so each river that gets asked about has one sentence.
    entry("river-length", (_RIVER_NAMES + ("river", "river long", "length of the"),
                           ("how long", "how far", "long is", "length", "km", "kilometres",
                            "kilometers", "miles", "distance", "longest")),
          _river_length,
          ask=("how long", "how far", "long is", "length", "km", "kilometres", "kilometers",
               "miles", "distance"),
          avoid=("cruise", "cruise ship", "boat", "kayak", "canoe", "paddle", "swim", "dive",
                 "fish", "fishing", "holiday", "trip", "visit", "hotel", "walk", "hike",
                 "bank", "banks", "flood", "flooding", "pollution", "sewage", "clean up")),

    entry("australia-both",
          ("australia", ("continent", "country", "both", "continent or a country")),
          "Both: Australia is the smallest continent and the only country that is a whole "
          "continent. It is also the sixth largest country by area, and the only one that is "
          "both a country and a continent.",
          ask=("continent", "country", "both"),
          avoid=("how many", "number of", "cities", "city", "capital", "visa", "holiday", "trip",
                 "flight", "weather", "move", "living", "live", "visited", "been")),
    entry("euro-countries",
          (("euro", "euros", "eurozone", "single currency"),
           ("which countries", "what countries", "countries", "members", "use", "using",
            "adopt", "adopted", "currency")),
          "Twenty countries use the euro: Austria, Belgium, Croatia, Cyprus, Estonia, Finland, "
          "France, Germany, Greece, Ireland, Italy, Latvia, Lithuania, Luxembourg, Malta, the "
          "Netherlands, Portugal, Slovakia, Slovenia and Spain. Kosovo and Montenegro use it "
          "without being in the eurozone, and Denmark has a fixed rate but keeps the krone.",
          ask=("euro", "euros", "eurozone", "single currency"),
          avoid=("take", "bring", "change", "exchange", "worth", "rate", "cash", "cashpoint",
                 "atm", "card", "holiday", "spend", "spending", "budget", "cheaper")),
    entry("uk-parts",
          (("ireland", "northern ireland", "england", "scotland", "wales", "british isles",
            "great britain", "britain"),
           # "is england part of europe" names a part and a bigger thing, and the answer is
           # about the continent the pair names. The phrase is kept whole: a bare "part of" in
           # this group made "is scotland part of the eu" answer about the UK, which is true and
           # is not the question.
           ("part of europe", "in europe", "part of the uk", "part of uk",
            "in the uk", "in uk", "british", "uk", "britain",
            "independent", "separate country", "same country", "a country", "country",
            "sovereign", "difference", "different", "same", "versus", " vs ", "isles",
            "mean",
            # two of the names in one line is the comparison itself: "the difference between
            # great britain and the uk" says "great britain" and "the uk", and "is england the
            # same as britain" says two of them as well. The comparison word is read as the ask,
            # so without the names here the line has only one key signal and reaches nothing.
            "england", "scotland", "wales", "ireland", "northern ireland", "britain", "uk",
            "united kingdom", "great britain", "british isles")),
          _uk_part,
          ask=("part of", "in the uk", "in uk", "british", "independent", "separate",
               "in britain", "part of britain", "a country", "country", "sovereign",
               # a comparison of two of the names is the same question asked with both of them
               # in it: "the difference between great britain and the uk", "is england the same
               # as britain", "what are the british isles"
               "difference", "different", "same", "versus", "isles", "british isles",
               "the same as", "mean"),
          avoid=("holiday", "trip", "visit", "moving", "move", "live", "living", "drive",
                 "flight", "going", "hotel", "weather", "visa", "job", "food", "best",
                 "what is there", "worth",
                 # A line naming two of the nations is a comparison, and a plug, socket, currency
                 # or driving question compares two of them merely as the two places it is about:
                 # "is the plug the same in ireland as england" is a plug question, and the plug
                 # row answers it with the adapter. Those words belong to the other rows.
                 "plug", "plugs", "socket", "sockets", "adapter", "adaptor", "voltage",
                 "charger", "currency", "cash", "euro", "euros", "pound", "pounds",
                 # The everyday dimensions two places get compared on. "is council tax different
                 # in scotland", "is the drinking age the same in scotland", "are house prices
                 # the same in scotland and england": the nation names are only the places being
                 # compared, and the comparison word is read as the ask, so both key signals are
                 # there while the subject is the tax, the age or the price. This row has nothing
                 # to say about any of them, and it should not pretend the line asked which
                 # country Scotland is in.
                 "weather", "climate", "nhs", "health", "hospital", "tax", "vat", "council tax",
                 "wage", "wages", "salary", "price", "prices", "cost", "costs", "cheap",
                 "expensive", "school", "schools", "education", "university", "exam", "exams",
                 "age", "aged", "drinking", "alcohol", "law", "laws", "legal", "police", "crime",
                 "passport", "licence", "license", "train", "trains", "bus", "buses", "rent",
                 "mortgage", "house prices", "benefits", "pension", "pensions", "pint", "beer",
                 "dog", "dogs", "pet", "pets")),
]
