"""Travel: capitals, city guides, weather by month, jet lag, packing and the airport.

The answers lane owns this domain. City knowledge is a table keyed by the city name, so
"what shouldn't I miss in Lisbon" and "lisbon in may, three days" reach the same facts;
the replies say what to book or avoid as well as what to see.
"""
import datetime
import math
import re
import string

from ..memory.when import the_plan
from .geography import (carries_it_out_of_britain, country_extreme, crosses_a_border,
                        region_extreme)
from ..compose import pick
from .lookup import (a_price_not_a_loan, a_weight, entry, not_the_flat_of_something_made,
                     not_the_flat_you_live_in, tokens)

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("geography-and-travel", "nature-and-weather")

# A named region has its own biggest country or longest river; a world record would be wrong.
REGIONS = ("africa", "europe", "asia", "america", "americas", "north america",
           "south america", "central america", "caribbean", "oceania", "australia",
           "uk", "britain", "england", "scotland", "wales", "ireland", "china", "india",
           "france", "italy", "spain", "germany", "egypt",
           # Antarctica has no countries at all, so Russia is not the answer to its biggest one.
           "antarctica")

# A flight or airport word: what turns a question about food or drink into a security one.
FLIGHT = ("plane", "planes", "flight", "flying", "airport", "security", "hand luggage",
          "carry on", "carry-on", "on board", "cabin bag")

# The same words, loose, for reading the topic of a short follow-up ("can I take my own
# sandwiches?") in a flight thread, where the line itself names no flight at all.
FLIGHT_THREAD = frozenset({"plane", "planes", "flight", "flights", "flying", "fly",
                           "flew", "airport", "airports", "security", "security-check",
                           "boarding", "gate", "cabin", "luggage"})

FLIGHT_FOOD = ("Yes: solid food is fine to take through security and on the plane, so sandwiches "
               "and fruit are no problem. Only liquids are limited to 100ml containers in a clear "
               "bag, and there's a bin before security for anything over.")

FLIGHT_LIQUIDS = ("Only containers of 100ml or less, all fitting in one clear plastic bag, can go "
                  "through security. Fill an empty bottle after security, or ask for water on the "
                  "plane.")


_TICKET_LOST = re.compile(r"\b(lost|lose|losing|left|left it|forgot|forgotten)\b")
_TICKET_CHANGE = re.compile(r"\b(change|changed|changing|amend|amended|alter|altering|"
                            r"missed|earlier|later|different train|another train|wrong train)\b")
_TICKET_VALID = re.compile(r"\b(valid|any train|any time|off peak|restriction|restricted)\b")
_TICKET_PRINT = re.compile(r"\b(print|printed|paper|phone|mobile|app|e ticket|eticket|"
                           r"barcode|screenshot)\b")


def _a_ticket_already_bought(memory, understood):
    """What to do with the ticket in hand, read off the line."""
    said = ((str((understood or {}).get("clean") or "") + " "
             + str((understood or {}).get("text") or "")).lower())
    if _TICKET_LOST.search(said):
        return ("Tell the train company as soon as you know: with an e-ticket you can show the "
                "confirmation again, and most operators will let you travel on the booking "
                "reference and the card you paid with. A paper ticket is rarely replaced, so "
                "photograph it when you buy it, and if it is lost at the station go to the ticket "
                "office before boarding rather than after.")
    if _TICKET_CHANGE.search(said):
        return ("It depends which ticket it is: an advance ticket can usually be changed up to "
                "the departure for a set fee (about £10 on most operators) plus any difference in "
                "fare, and an off-peak or anytime ticket needs no change at all, because it is "
                "already good for any train in its band. If the train is cancelled, your ticket "
                "is valid on the next one, and on a later one if you decide not to wait.")
    if _TICKET_PRINT.search(said):
        return ("An e-ticket on your phone is enough at almost every gateline now: have it open "
                "and the brightness up before you reach the barrier, and screenshot it in case "
                "signal drops. Print it only if the operator asks you to or you are crossing a "
                "border, where a paper copy is easier to show.")
    return ("Check the ticket's own restriction: an advance ticket is only good for the train it "
            "names, while an off-peak or anytime ticket is valid on any train in its band, so a "
            "different time is usually fine on those. If you are on the wrong train with an "
            "advance, speak to the guard before the ticket check rather than after it.")

# The three ways of making a booked journey, and the words that name each in a line. The ferry
# list holds the crossing words ("the crossing", "sailing") because a person asking about the
# boat to France writes "the ferry" or "the crossing" and not always the word ferry.
JOURNEY_MODES = (
    "ferry", "ferries", "boat", "boats", "crossing", "crossings", "sailing", "sailings",
    "train", "trains", "rail", "railway", "railcard", "coach", "coaches", "national express",
    "megabus", "bus", "buses",
)

_FERRY_ASK = re.compile(r"\b(ferry|ferries|boat|boats|crossing|crossings|sailing|sailings|"
                        r"channel|dover|calais|holyhead|dublin|isle of wight)\b")
_COACH_ASK = re.compile(r"\b(coach|coaches|megabus|national express|bus|buses)\b")
_SEAT_ASK = re.compile(r"\b(seat|seats|reservation|reserve)\b")


def _book_a_journey(memory, understood):
    """How far ahead the ferry, the train or the coach is booked, in that order."""
    said = ((str((understood or {}).get("clean") or "") + " "
             + str((understood or {}).get("text") or "")).lower())
    if _FERRY_ASK.search(said):
        return ("Book the ferry as soon as the dates are fixed: foot passengers can usually buy "
                "on the day, but a car needs booking ahead and a summer weekend sailing sells "
                "out. Book with the operator itself rather than a resale site, and take the "
                "flexible ticket if the price is close, because a missed sailing with a car is "
                "the expensive way to learn. Turn up an hour before with a car and 30 minutes on "
                "foot, with the booking reference to hand.")
    if _COACH_ASK.search(said):
        return ("Book the coach two or three weeks ahead: the cheapest seats are the first to go "
                "and a seat bought on the day can cost two or three times as much. Pick the seat "
                "when the site offers it, be at the stop 15 minutes early because coaches leave "
                "on time, and take the luggage rules seriously - one case in the hold is usual "
                "and anything extra is paid for at the stop.")
    if _SEAT_ASK.search(said) and not _FERRY_ASK.search(said):
        return ("Reserve the seat when you book the ticket: on most trains a reservation is free "
                "with an advance ticket and a few pounds on a walk-up fare, and it is worth having "
                "on any long trip. Friday evening and Sunday afternoon trains are the busiest, so "
                "a booked seat there is the difference between sitting and standing.")
    return ("Book the train as soon as the date is fixed: advance singles tied to one train are "
            "usually about half the walk-up fare, and they go on sale around 12 weeks ahead. A "
            "railcard pays for itself in one or two long journeys, and check the price of two "
            "singles as well as a return - two advances are often cheaper than one return.")


def _the_booking_is_behind_them(understood):
    """False when the line says the booking has already happened.

    "ive booked a flight to rome" is news, and "we booked the flights and now i wish we hadnt" is
    a person with a feeling about something they have already done. The avoid words "just" and
    "already" were the only ones that said so, and a past tense needs no such word: every one of
    those lines was told to compare fares on a search site. The row's whole answer is how to
    book one, so it stands down on the word that says the booking is behind them.
    """
    words = understood.get("words") if isinstance(understood, dict) else None
    if isinstance(words, (list, tuple)) and words:
        low = " " + " ".join(str(word) for word in words).lower() + " "
    else:
        low = " " + str((understood or {}).get("clean") or "").lower() + " "
    return " booked " not in low


# "Do it myself" is not a travel phrase on its own: a person says it about a kitchen, a bathroom
# and a wardrobe as often as about a holiday, and the row below answered "hire a builder or do it
# myself" with a package-holiday card about flights and transfers. The trade the row is about
# only exists in a trip, so the row asks for the trip to be in the line - unless the line names
# the package itself, which is travel whatever else it says.
_THE_TRIP_IN_THE_LINE = re.compile(
    r"\b(?:holiday|holidays|holidaymaker|trip|trips|travel|travelling|traveling|flight|flights|"
    r"fly|flying|hotel|hotels|abroad|away|resort|resorts|villa|cruise|airport|city\s+break|"
    r"beach|abroad|all\s+inclusive|package|packages|tour|tours|itinerary|hotel\s+and\s+flight|"
    r"flights\s+and\s+hotel|transfer|transfers|operator|operators|atol|booking)\b", re.I)


def _a_trip_to_arrange(understood):
    """True unless "do it myself" is about a job rather than a trip.

    A package holiday against booking it yourself is a real trade - protection and transfers
    against price - and the row is good at it. The same words are ordinary for a bathroom or a
    wardrobe, where the trade is a guarantee against an afternoon's work and the holiday card is
    no answer at all. So the words the line names have to include the trip.
    """
    text = (understood or {}).get("clean") or ""
    if not text:
        words = (understood or {}).get("words") or ()
        text = " ".join(str(word) for word in words)
    return bool(_THE_TRIP_IN_THE_LINE.search(str(text).lower()))


def _in_a_flight_thread(memory):
    """Whether the last exchange was about a flight, so a short follow-up belongs to it.

    The understanding engine resets a topic as soon as a line changes the subject, so this
    reads the previous turn (and the user's line in it) rather than memory["topic"].
    """
    if not isinstance(memory, dict):
        return False
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1]
    if not isinstance(last, dict):
        return False
    said = " ".join(str(last.get(key) or "") for key in ("user", "bot"))
    return any(word in FLIGHT_THREAD for word in tokens(said))


TIP_US = ("In the US, tip 18 to 20% in restaurants (on the bill before tax), a dollar or two a "
          "drink at the bar, and 2 to 5 dollars a day for hotel housekeeping: staff there are paid "
          "by tips, so leaving nothing reads as a complaint.")

TIP_EUROPE = ("In most of Europe service is usually included and 5 to 10% is plenty for good "
              "service - round up in cafes and leave about a euro a drink at the bar.")

TIP_TAXI = ("For a taxi, round the fare up to the next note in most places and leave about 10% "
            "in the US; in Japan you tip nothing, and where there is no meter agree the fare before "
            "you get in.")

TIP_JAPAN = ("In Japan you don't tip at all: staff are paid properly and leaving money can cause "
             "offence, or a flustered chase down the street to give it back.")

TIP_ELSEWHERE = ("Where you are not sure, 10% is a safe default in a sit-down restaurant, "
                 "nothing is expected in a cafe, and a coin or two a day is plenty for hotel "
                 "housekeeping if the room has been done well.")


def _travel_advice(memory, understood):
    """"Is it safe to travel to X" - the Foreign Office page, named, for the country asked about."""
    place = _place_in(memory, understood, WATER)
    if not place:
        return None
    return (f"For {place.title()} the Foreign Office travel advice is the page to read before you "
            f"book: it says which areas to avoid and what has changed lately, and it is the page "
            f"your insurer reads too. Insurance can be void in an area it advises against. Take the "
            f"embassy number with you.")


# A city names its country as well as the country's own name does, and "how much do you tip in
# new york" is the US answer, not the UK one. The lists are the places people ask about by name;
# anything else falls through to the general answer below.
_US_PLACE = (r"\b(america|american|usa|states|new york|nyc|florida|california|vegas|"
             r"las vegas|los angeles|san francisco|miami|chicago|boston|seattle|washington|"
             r"texas|hawaii|orlando|brooklyn|manhattan|hollywood)\b")
_EUROPE_PLACE = (r"\b(france|paris|italy|rome|spain|portugal|greece|germany|europe|netherlands|"
                 r"amsterdam|london|lisbon|barcelona|madrid|berlin|munich|florence|venice|"
                 r"athens|crete|malta|cyprus|croatia|dubrovnik|prague|vienna|zurich|geneva|"
                 r"brussels|copenhagen|stockholm|oslo|helsinki|warsaw|budapest|istanbul|"
                 r"britain|england|scotland|wales|ireland|dublin)\b")


def _tipping(memory, understood):
    """The country the line names decides the answer; a general tip line when it names none."""
    clean = understood.get("clean", "")
    # A cab has its own rule, and the restaurant default is wrong for it: nobody leaves 18% of a
    # fare, they round the note up. The country still decides how generous to be.
    if any(word in clean for word in ("taxi", "cab", "uber", "driver", "minicab")):
        return TIP_TAXI
    if any(word in clean for word in ("japan", "japanese", "tokyo", "kyoto")):
        return TIP_JAPAN + " In the US it is the opposite, 18 to 20%."
    # "the us" is the country, but a bare "us" is usually the pronoun ("tell us a tip"):
    # only a word before it makes it the United States.
    if (re.search(_US_PLACE, clean) or re.search(r"\bin (the )?us\b", clean)):
        return TIP_US + " Most of Europe includes service instead."
    if re.search(_EUROPE_PLACE, clean):
        return TIP_EUROPE + " The US is the big exception."
    # A hotel line and a tour line are travel lines however little of the world they name:
    # "should i tip a hotel cleaner" and "should i tip a tour guide" are read as travel
    # questions, so the money table's answer is out of reach here and the room's or the guide's
    # own rule is the answer. It is the same text the money table gives, taken from there rather
    # than written twice.
    if any(word in clean for word in ("hotel", "housekeeping", "porter", "concierge", "bellboy",
                                      "maid", "room service", "tour guide", "tour", "excursion",
                                      "walking tour", "coach driver", "mover", "movers",
                                      "removal men", "man and van")):
        from .lifeadmin import _tipping as _the_uk_tip   # no cycle: lifeadmin imports nothing here
        said = _the_uk_tip(memory, understood)
        if said:
            return said
    return TIP_ELSEWHERE


LONDON_AIRPORTS = (
    (("heathrow",), "From Heathrow the Elizabeth line is 30 minutes to Paddington for about 13 "
                    "pounds, the Piccadilly line about an hour for about 5.60, and the Heathrow "
                    "Express 15 minutes to Paddington for about 25."),
    (("gatwick",), "From Gatwick the train to Victoria takes 30 to 40 minutes: the Gatwick Express "
                   "is about 20 pounds, the ordinary Southern or Thameslink train about half that "
                   "and only ten minutes slower."),
    (("stansted",), "From Stansted the Stansted Express runs to Liverpool Street in about 47 "
                    "minutes for around 20 pounds, and a coach to Victoria is cheaper but slower."),
    (("luton",), "From Luton the shuttle bus runs to Luton Airport Parkway, then a fast train to "
                 "St Pancras takes about 25 minutes - book the bundle and it is cheaper."),
)


# Getting to London by coach, by train or by tube is not an airport question, however many of
# its words are in the line: "bus or train to london" was answered with London City and the DLR.
# A deadline said as the person's own need is a planning question, not a route one: "i need to get
# to heathrow for 6am" wants the journey worked back from six, and the transfer card said the train
# times to Paddington to somebody who had to be airside by six. "how do i get to gatwick by 5am"
# still asks the route, so only the need-and-clock shape stands the card down.
A_DEADLINE_NEED = re.compile(r"\b(?:i|we)\s+(?:need|needs|have|has|have got|got|want|wants|"
                             r"must)\b[^.!?]{0,40}?\b(?:get|be|make it|arrive)\b[^.!?]{0,20}?"
                             r"\b(?:for|by|before)\s+\d{1,2}(?:[.:]\d\d)?\s*(?:am|pm)?", re.I)

GROUND_TRANSPORT = re.compile(r"\b(?:bus|buses|coach|coaches|national express|megabus|train|"
                              r"trains|tube|underground|oyster|travelcard|travel card|driving|"
                              r"drive|parking|congestion charge|ulez)\b")
AIRPORT_WORD = re.compile(r"\b(?:airport|airports|heathrow|gatwick|stansted|luton|london city|"
                          r"city airport|southend|flight|flights|fly|flying|terminal)\b")


def _london_airport(memory, understood):
    """The airport the line names gets its own route; otherwise the closest-airport answer."""
    clean = understood.get("clean", "")
    if GROUND_TRANSPORT.search(clean) and not AIRPORT_WORD.search(clean):
        return None
    if A_DEADLINE_NEED.search(clean):
        return None
    for names, answer in LONDON_AIRPORTS:
        if any(name in clean for name in names):
            return (answer + " A black cab is the expensive option: the train beats it into the "
                    "centre every time.")
    return ("London City is the closest airport to the centre: about 25 minutes to Bank on the "
            "DLR. Of the big four, Heathrow is the quickest into town - the Elizabeth line takes "
            "30 minutes to Paddington for about 13 pounds.")


def _flight_followup(answer):
    """Answer a short food or drink follow-up only inside a flight thread, else pass."""
    def reply(memory, understood):
        return answer if _in_a_flight_thread(memory) else None
    return reply

CAPITALS = {
    "australia": "Canberra, not Sydney: it was purpose-built as the compromise between Sydney and "
                 "Melbourne.",
    "canada": "Ottawa, not Toronto.",
    "brazil": "Brasília, not Rio, and a planned city built in four years.",
    "turkey": "Ankara, not Istanbul.",
    "switzerland": "Bern, the de facto capital; Switzerland has no official one.",
    "united states": "Washington DC, not New York.",
    "usa": "Washington DC, not New York.",
    "america": "Washington DC, not New York.",
    "netherlands": "Amsterdam, though the government sits in The Hague.",
    "france": "Paris.",
    "spain": "Madrid.",
    "portugal": "Lisbon.",
    "italy": "Rome.",
    "germany": "Berlin, since reunification in 1990.",
    "japan": "Tokyo.",
    "china": "Beijing.",
    "india": "New Delhi, not Mumbai.",
    "russia": "Moscow.",
    "new zealand": "Wellington, not Auckland.",
    "norway": "Oslo.",
    "sweden": "Stockholm.",
    "denmark": "Copenhagen.",
    "finland": "Helsinki.",
    "greece": "Athens.",
    "ireland": "Dublin.",
    "poland": "Warsaw.",
    "austria": "Vienna.",
    "belgium": "Brussels.",
    "hungary": "Budapest.",
    "czechia": "Prague.",
    "czech republic": "Prague.",
    "south korea": "Seoul.",
    "mexico": "Mexico City.",
    "argentina": "Buenos Aires.",
    "south africa": "Pretoria, though the parliament sits in Cape Town and the courts in "
                    "Johannesburg.",
    # The rest of the world, because "what is the capital of Peru" was a shrug: the table held
    # about forty countries and answered every way only for those. A country is one row, so one
    # row answers "capital of Peru", "what is the capital city of Peru" and "Peru's capital", and
    # a row is added where people ask rather than in the order someone listed them. A note says
    # the thing people get wrong (the old capital, the biggest city, the second seat of
    # government); everything else is the one word, which is the answer they asked for.
    "afghanistan": "Kabul.",
    "albania": "Tirana.",
    "algeria": "Algiers.",
    "andorra": "Andorra la Vella.",
    "angola": "Luanda.",
    "antigua and barbuda": "Saint John's.",
    "armenia": "Yerevan.",
    "azerbaijan": "Baku.",
    "bahamas": "Nassau.",
    "bahrain": "Manama.",
    "bangladesh": "Dhaka.",
    "barbados": "Bridgetown.",
    "belarus": "Minsk.",
    "belize": "Belmopan, not Belize City.",
    "benin": "Porto-Novo, though the government sits in Cotonou.",
    "bhutan": "Thimphu.",
    "bolivia": "Sucre is the constitutional capital; La Paz is where the government sits.",
    "bosnia and herzegovina": "Sarajevo.",
    "bosnia": "Sarajevo.",
    "botswana": "Gaborone.",
    "brunei": "Bandar Seri Begawan.",
    "bulgaria": "Sofia.",
    "burkina faso": "Ouagadougou.",
    "burma": "Naypyidaw, not Yangon, which was the capital until 2006.",
    "burundi": "Gitega, since 2019; Bujumbura was the capital before that.",
    "cambodia": "Phnom Penh.",
    "cameroon": "Yaounde.",
    "cape verde": "Praia.",
    "central african republic": "Bangui.",
    "chad": "N'Djamena.",
    "chile": "Santiago.",
    "colombia": "Bogota.",
    "comoros": "Moroni.",
    "congo": "Two countries share the name: Brazzaville for the Republic of the Congo, Kinshasa "
             "for the Democratic Republic of the Congo.",
    "costa rica": "San Jose.",
    "cote d'ivoire": "Yamoussoukro, not Abidjan.",
    "croatia": "Zagreb.",
    "cuba": "Havana.",
    "cyprus": "Nicosia.",
    "democratic republic of the congo": "Kinshasa.",
    "djibouti": "Djibouti.",
    "dominica": "Roseau - not Santo Domingo, which is the Dominican Republic's capital.",
    "dominican republic": "Santo Domingo.",
    "dr congo": "Kinshasa.",
    "ecuador": "Quito.",
    "el salvador": "San Salvador.",
    "equatorial guinea": "Malabo.",
    "eritrea": "Asmara.",
    "estonia": "Tallinn.",
    "eswatini": "Mbabane for the administration, Lobamba for the parliament; the country was "
                "called Swaziland until 2018.",
    "ethiopia": "Addis Ababa.",
    "fiji": "Suva.",
    "gabon": "Libreville.",
    "gambia": "Banjul.",
    "georgia": "Tbilisi - the country's capital. The US state of Georgia has Atlanta.",
    "ghana": "Accra.",
    "grenada": "St George's.",
    "guatemala": "Guatemala City.",
    "guinea": "Conakry.",
    "guinea-bissau": "Bissau.",
    "guyana": "Georgetown.",
    "haiti": "Port-au-Prince.",
    "holland": "Amsterdam, though the government sits in The Hague.",
    "honduras": "Tegucigalpa.",
    "indonesia": "Jakarta, though the government is moving to a new capital, Nusantara, in Borneo.",
    "iran": "Tehran.",
    "iraq": "Baghdad.",
    "israel": "Jerusalem, which Israel calls its capital; most countries keep their embassies in "
              "Tel Aviv because the status is disputed.",
    "ivory coast": "Yamoussoukro, not Abidjan, which is the biggest city.",
    "jamaica": "Kingston.",
    "jordan": "Amman.",
    "kazakhstan": "Astana, which was called Nur-Sultan from 2019 to 2022.",
    "kiribati": "South Tarawa.",
    "kuwait": "Kuwait City.",
    "kyrgyzstan": "Bishkek.",
    "laos": "Vientiane.",
    "latvia": "Riga.",
    "lebanon": "Beirut.",
    "lesotho": "Maseru.",
    "liberia": "Monrovia.",
    "libya": "Tripoli.",
    "liechtenstein": "Vaduz.",
    "lithuania": "Vilnius.",
    "luxembourg": "Luxembourg City.",
    "madagascar": "Antananarivo.",
    "malawi": "Lilongwe.",
    "malaysia": "Kuala Lumpur, though the government sits in Putrajaya.",
    "maldives": "Male.",
    "mali": "Bamako.",
    "malta": "Valletta.",
    "marshall islands": "Majuro.",
    "mauritania": "Nouakchott.",
    "mauritius": "Port Louis.",
    "micronesia": "Palikir.",
    "moldova": "Chisinau.",
    "monaco": "Monaco itself - the country is one city.",
    "mongolia": "Ulaanbaatar.",
    "montenegro": "Podgorica.",
    "mozambique": "Maputo.",
    "myanmar": "Naypyidaw, not Yangon, which was the capital until 2006.",
    "namibia": "Windhoek.",
    "nauru": "Yaren, where the government sits; Nauru has no official capital.",
    "nepal": "Kathmandu.",
    "nicaragua": "Managua.",
    "niger": "Niamey.",
    "north korea": "Pyongyang.",
    "north macedonia": "Skopje.",
    "oman": "Muscat.",
    "pakistan": "Islamabad, not Karachi.",
    "palau": "Ngerulmud, a purpose-built capital; the biggest town is Koror.",
    "panama": "Panama City.",
    "papua new guinea": "Port Moresby.",
    "paraguay": "Asuncion.",
    "peru": "Lima.",
    "philippines": "Manila, not Quezon City, which is the bigger city.",
    "qatar": "Doha.",
    "romania": "Bucharest.",
    "rwanda": "Kigali.",
    "saint kitts and nevis": "Basseterre.",
    "saint lucia": "Castries.",
    "saint vincent and the grenadines": "Kingstown.",
    "samoa": "Apia.",
    # The territories people ask about by their own name. "american samoa" holds the
    # word samoa, and the longest key wins, so it has to be here or the answer is
    # Samoa's capital: Apia, a different country 80 km away.
    "american samoa": "Pago Pago, on Tutuila - a US territory of its own, not Samoa, whose capital is Apia.",
    "guam": "Hag\u00e5t\u00f1a, a US territory in the Pacific.",
    "puerto rico": "San Juan, a US territory, not a state.",
    "bermuda": "Hamilton, a British territory - not Hamilton, Ontario.",
    "san marino": "San Marino.",
    "sao tome and principe": "Sao Tome.",
    "saudi arabia": "Riyadh.",
    "senegal": "Dakar.",
    "serbia": "Belgrade.",
    "seychelles": "Victoria.",
    "sierra leone": "Freetown.",
    "singapore": "Singapore itself - the country is one city.",
    "slovakia": "Bratislava.",
    "slovenia": "Ljubljana.",
    "solomon islands": "Honiara.",
    "somalia": "Mogadishu.",
    "south sudan": "Juba.",
    "sri lanka": "Sri Jayawardenepura Kotte, though Colombo is the one everyone names.",
    "sudan": "Khartoum.",
    "suriname": "Paramaribo.",
    "swaziland": "Mbabane for the administration and Lobamba for the parliament; the country is "
                 "called Eswatini now.",
    "syria": "Damascus.",
    "taiwan": "Taipei.",
    "tajikistan": "Dushanbe.",
    "tanzania": "Dodoma, not Dar es Salaam, which is the biggest city.",
    "thailand": "Bangkok.",
    "timor-leste": "Dili.",
    "togo": "Lome.",
    "tonga": "Nuku'alofa.",
    "trinidad and tobago": "Port of Spain.",
    "tunisia": "Tunis.",
    "turkmenistan": "Ashgabat.",
    "tuvalu": "Funafuti.",
    "uae": "Abu Dhabi, not Dubai.",
    "uganda": "Kampala.",
    "ukraine": "Kyiv.",
    "united arab emirates": "Abu Dhabi, not Dubai.",
    "united kingdom": "London.",
    "uk": "London.",
    "britain": "London.",
    "great britain": "London, though Great Britain is the island, not the country: the UK is the four nations together.",
    "uruguay": "Montevideo.",
    "uzbekistan": "Tashkent.",
    "vanuatu": "Port Vila.",
    "vatican city": "Vatican City, which is the whole country.",
    "venezuela": "Caracas.",
    "vietnam": "Hanoi, not Ho Chi Minh City.",
    "washington": "Olympia if you mean the state, Washington DC if you mean the city - the two "
                  "are different, and neither is New York.",
    "yemen": "Sanaa.",
    "zambia": "Lusaka.",
    "zimbabwe": "Harare.",
    # Regions, states and provinces, not just countries. _find_in takes the longest key that
    # appears in the line, so "new south wales" beats "wales" and "south australia" beats
    # "australia": without these rows "the capital of New South Wales" was Cardiff and "the
    # capital of Northern Ireland" was Dublin.
    "northern ireland": "Belfast, not Dublin - Dublin is the capital of the Republic of Ireland.",
    "new south wales": "Sydney, not Canberra - Canberra is the capital of the country.",
    "queensland": "Brisbane, not Canberra - Canberra is the capital of the country.",
    "south australia": "Adelaide, not Canberra - Canberra is the capital of the country.",
    "western australia": "Perth, not Canberra - Canberra is the capital of the country.",
    "tasmania": "Hobart, not Canberra - Canberra is the capital of the country.",
    "victoria": "Melbourne, not Canberra - Canberra is the capital of the country.",
    "northern territory": "Darwin, not Canberra - Canberra is the capital of the country.",
    "scotland": "Edinburgh, not London - London is the capital of the UK.",
    "wales": "Cardiff, not London - London is the capital of the UK.",
    # The American states, because "the capital of Texas" is Austin and not one of the big
    # cities, and "the capital of New York" is Albany. A state whose name is also a country
    # (Georgia) is left out: there the country's capital is the answer people want.
    "new york state": "Albany, not New York City - the city is not the capital of the state.",
    "new york": "Albany, not New York City - the city is not the capital of the state.",
    "california": "Sacramento, not Los Angeles or San Francisco.",
    "texas": "Austin, not Houston or Dallas.",
    "florida": "Tallahassee, not Miami.",
    "illinois": "Springfield, not Chicago.",
    "pennsylvania": "Harrisburg, not Philadelphia.",
    "michigan": "Lansing, not Detroit.",
    "missouri": "Jefferson City, not St Louis or Kansas City.",
    "maryland": "Annapolis, not Baltimore.",
    "alaska": "Juneau, not Anchorage.",
    "washington state": "Olympia, not Seattle - and not Washington DC, which is a different city.",
    "ohio": "Columbus.",
    "arizona": "Phoenix.",
    "colorado": "Denver.",
    "nevada": "Carson City, not Las Vegas.",
    "oregon": "Salem, not Portland.",
    "utah": "Salt Lake City.",
    "massachusetts": "Boston.",
    "north carolina": "Raleigh.",
    "south carolina": "Columbia.",
    "tennessee": "Nashville.",
    "virginia": "Richmond.",
    "minnesota": "St Paul, not Minneapolis.",
    "wisconsin": "Madison, not Milwaukee.",
    "indiana": "Indianapolis.",
    "kentucky": "Frankfort, not Louisville.",
    "oklahoma": "Oklahoma City.",
    "iowa": "Des Moines.",
    "kansas": "Topeka, not Wichita.",
    "nebraska": "Lincoln, not Omaha.",
    "idaho": "Boise.",
    "maine": "Augusta, not Portland.",
    "new mexico": "Santa Fe, not Albuquerque.",
    "hawaii": "Honolulu.",
    "alabama": "Montgomery.",
    "arkansas": "Little Rock.",
    "connecticut": "Hartford.",
    "delaware": "Dover.",
    "louisiana": "Baton Rouge, not New Orleans.",
    "mississippi": "Jackson.",
    "montana": "Helena.",
    "new hampshire": "Concord.",
    "new jersey": "Trenton.",
    "north dakota": "Bismarck.",
    "rhode island": "Providence.",
    "south dakota": "Pierre.",
    "vermont": "Montpelier.",
    "west virginia": "Charleston.",
    "wyoming": "Cheyenne.",
    "england": "London.",
    "morocco": "Rabat, not Casablanca.",
    "egypt": "Cairo.",
    "kenya": "Nairobi.",
    "nigeria": "Abuja, not Lagos.",
    "iceland": "Reykjavík.",
}

CITIES = {
    "lisbon": ("Alfama on foot and the 28 tram, Belém for the tower and the custard tarts, and "
               "LX Factory or Time Out Market for lunch. May is warm and busy, so book the tower "
               "and the popular restaurants ahead."),
    "rome": ("the Colosseum with a timed ticket, the Pantheon, and Trastevere in the evening for "
             "dinner. Book the Vatican museums online, and carry a refillable bottle: the "
             "fountains are free."),
    "florence": ("the Duomo climb, the Uffizi (book a slot), and the Oltrarno side of the river "
                 "for food. Two days is enough for those three if you don't queue for everything."),
    "paris": ("walk the Île de la Cité to the Marais, pick one big museum rather than three, and "
              "eat in a market street rather than by the Eiffel Tower. Book the Louvre or Orsay "
              "timed entry online."),
    "barcelona": ("the Gothic Quarter, the Sagrada Família (book weeks ahead), and the beach at "
                  "Barceloneta for half a day. Eat lunch at 2pm like locals; the good places open "
                  "then."),
    "madrid": ("the Prado, the Retiro park and the tapas streets around Plaza Mayor. Dinner "
               "starts late here, so plan on eating at 9pm or later."),
    "amsterdam": ("the Jordaan on foot, the Rijksmuseum and a canal walk at dusk. Book Anne Frank "
                  "House tickets online weeks ahead; they sell out completely."),
    "berlin": ("the Wall memorial and East Side Gallery, Museum Island, and Kreuzberg for food. "
               "It's a big, spread-out city, so buy a day travel ticket."),
    "prague": ("the Old Town at 7am before the crowds, Charles Bridge early, and the castle on the "
               "hill. Beer is cheaper than water, but change money at a bank, not a kiosk."),
    "vienna": ("the Ringstrasse, one grand coffee house and the Naschmarkt. Book the Spanish "
               "Riding School or a concert only if you're sure: they are pricey."),
    "edinburgh": ("the Royal Mile and the castle, Arthur's Seat for the view, and Leith for food. "
                  "In December it's dark by 4pm and the Christmas market fills the centre."),
    "london": ("pick one area a day rather than criss-crossing: South Bank, the museums in South "
               "Kensington, and the markets in the East End. The Tube is quickest; walking between "
               "central stops is often as fast."),
    "dublin": ("a walk through Trinity College and the Book of Kells, the Guinness Storehouse, and "
               "pubs away from Temple Bar for music. Book the Book of Kells online."),
    "porto": ("the river walk to Ribeira, a port cellar tour in Gaia, and the Lello bookshop early "
              "or late. The trams are the nicest way to see the city."),
    "seville": ("the Alcázar (book ahead), the cathedral and oranges everywhere in the streets of "
                "Santa Cruz. In high summer it is 40C, so sightsee before 11am and after 7pm."),
    "copenhagen": ("Nyhavn for the picture, Tivoli if it's open, and the food market at Torvehallerne. "
                   "Bikes are the real way to get around; hire one."),
    "stockholm": ("Gamla Stan, the Vasa ship museum, and a ferry out to one of the islands. "
                  "Everything is walkable in the centre."),
    "athens": ("the Acropolis first thing with a timed ticket, the Acropolis Museum, and the Plaka "
               "in the evening. It is hot and shadeless up there, so take water and a hat."),
    "istanbul": ("Hagia Sophia, the Blue Mosque and the Grand Bazaar on the old side, and a ferry "
                 "across to Asia for lunch. Buy an Istanbulkart for the trams and ferries."),
    "new york": ("pick two neighbourhoods a day: the High Line and Chelsea, the Lower East Side, "
                 "and Brooklyn across the bridge. Book the big attractions online and walk a lot."),
    "tokyo": ("one district a day: Shibuya and Shinjuku, Asakusa and Ueno, and Tsukiji or "
              "Toyosu for breakfast. Get a Suica card for the trains and carry cash for small "
              "places."),
    "kyoto": ("Fushimi Inari at 7am before the crowds, the bamboo grove early too, and Gion at "
              "dusk. Buses are slow and packed: the subway plus walking is better."),
    "reykjavik": ("the harbour and Hallgrímskirkja, and use the city as a base for the Golden "
                  "Circle. Book the Blue Lagoon ahead and don't rinse the cave water off in the "
                  "showers."),
    "venice": ("get lost in Cannaregio and Dorsoduro away from St Mark's, cross the Grand Canal "
               "on the traghetto, and go early or late. Day-trippers leave by 5pm and the city "
               "feels completely different."),
    "boston": ("walk the Freedom Trail, eat in the North End, and cross to Cambridge for a "
               "half-day. The T is small and easy."),
    "bath": ("the Roman baths and the Pump Room, the Royal Crescent and the Circus, and a walk "
             "along the canal. It is small enough for a day, and the baths sell timed tickets "
             "that are worth booking the night before."),
    "ljubljana": ("the riverside cafes and the Triple Bridge, the castle on the hill for the "
                  "view, and a walk through Tivoli park. It is small and flat, so a day covers "
                  "it before you head out to Lake Bled."),
    "krakow": ("the main square and the cloth hall, Wawel castle, and Kazimierz for food and "
               "bars. Book Auschwitz-Birkenau a few days ahead and take the early bus: it is a "
               "full half-day."),
    "budapest": ("the parliament and the Danube bank, the thermal baths (Szechenyi or Gellert), "
                 "and the ruin bars in the old Jewish quarter. Buy a travel card for the trams "
                 "and metro; the city is long, not wide."),
    "brussels": ("the Grand Place, the comic-strip museum and the art nouveau houses, with the "
                 "waffles and fries people come for. Two days covers it, and Bruges or Ghent is "
                 "an hour away by train."),
    "milan": ("the Duomo and its roof terraces, the Last Supper (book weeks ahead) and the "
              "Navigli canals in the evening. Most people use it as a base: Lake Como is an hour "
              "by train."),
    "naples": ("the archaeology museum first, then pizza in the old town, and Pompeii or "
               "Herculaneum on a day trip by train. It is loud and fast, so keep bags in front "
               "of you and use the metro rather than the buses."),
    "munich": ("Marienplatz and the English Garden, the beer halls, and a day out to "
               "Neuschwanstein or Dachau if you have the time. The trains are excellent; buy a "
               "day ticket rather than singles."),
    "zurich": ("the old town on both sides of the river, a boat on the lake and the view from "
               "Uetliberg. Everything is expensive, so eat lunch from a bakery or a supermarket "
               "counter and save the restaurants for one evening."),
    "oslo": ("the opera house roof you can walk on, the Vigeland park and the fjord boats. It "
             "is compact but pricey: buy a seven-day transport pass, and take the train to Bergen "
             "if you have three days."),
    "helsinki": ("the cathedral square, the market hall and the design district, with a ferry "
                 "to Suomenlinna for half a day. In summer the evenings are light until "
                 "midnight, so eat late."),
    "tallinn": ("the walled old town, the viewing platforms on Toompea, and the cafes in "
                "Kalamaja. A day covers the old town; take a ferry to Helsinki or a bus to Riga "
                "if you have longer."),
    "dubrovnik": ("walk the city walls early or after 5pm once the cruise crowds have gone, "
                  "then the cable car for the view. Take water and a hat up there, and swim off "
                  "the rocks by the Buza gate."),
    "marrakech": ("the Jemaa el-Fna at dusk, the Bahia palace and the Ben Youssef school, and a "
                  "hammam. Agree taxi prices before you get in, and buy in the souks slowly: the "
                  "first price is never the price."),
    "santorini": ("Oia for the sunset once, but stay in Imerovigli or Pyrgos so you can sleep, "
                  "and take a boat out to the volcano. Book months ahead for July and August, or "
                  "come in May or September for the same light and half the people."),
    "valencia": ("the City of Arts and Sciences, the old town round the cathedral, and the "
                 "beach a short tram ride away. This is the home of paella, so eat it at lunch, "
                 "not in the evening."),
    "granada": ("the Alhambra first (book weeks ahead, it sells out), then the Albaicin at "
                "sunset from the San Nicolas viewpoint, with free tapas with drinks. Two nights "
                "is right: one is not enough for both."),
    "san sebastian": ("the two beaches, the pintxos bars in the old town, and the walk up Monte "
                      "Igueldo for the view. Eat standing at the bar: one or two pintxos a place, "
                      "then move on."),
    "san francisco": ("the Golden Gate on foot or by bike, the ferry building, and one "
                      "neighbourhood properly rather than five badly. Layers matter: the fog "
                      "rolls in and the temperature drops ten degrees by the water."),
    "chicago": ("the architecture boat tour, the Art Institute and the river walk, then deep "
                "dish once for the experience. The Loop is walkable and the trains from O'Hare "
                "run all night."),
    "los angeles": ("pick two areas and expect to drive between them: Venice or Santa Monica, "
                    "the Griffith observatory at sunset, and one studio tour if you want one. It "
                    "is far bigger than it looks on a map."),
    "toronto": ("the islands for the skyline view, Kensington market and the Distillery "
                "district, and the St Lawrence market for lunch. The streetcars work well, and "
                "Niagara Falls is a day trip by train."),
    "sydney": ("the harbour walk from the Opera House to Mrs Macquarie's chair, the Bondi to "
               "Coogee coastal path, and the ferry to Manly. Use the ferries as sightseeing: the "
               "Opal card caps the day."),
    "singapore": ("the hawker centres for every meal, Gardens by the Bay in the evening, and "
                  "the southern ridges walk. It is hot and humid all year, so walk early and "
                  "save the air-conditioned museums for midday."),
    "bangkok": ("the Grand Palace and Wat Pho early, the river boats rather than taxis, and "
                "street food in Chinatown at night. April and May are the hottest months, and "
                "from June the rain comes in short afternoon bursts."),
    "dubai": ("the old creek and its abra boats, the desert at sunset, and one tall building "
              "rather than three. From June to September it is over 40C and people live indoors; "
              "November to March is the season."),
    "cape town": ("Table Mountain first thing if the cloud is off it, the Cape Point drive, and "
                  "Bo-Kaap and the V&A for the afternoon. The wind and cloud decide your plan, "
                  "so keep the mountain day flexible."),
    "mexico city": ("the Zocalo and the Templo Mayor, the Frida Kahlo house in Coyoacan, and "
                    "the food markets. It sits at 2,240m, so take the first day slowly, and use "
                    "the metro in the day and taxis at night."),
    "havana": ("the old town in the morning, the Malecon at sunset, and a 1950s car once for "
               "the ride rather than the tour. Bring cash: foreign cards often do not work, so "
               "take enough for the whole trip."),
    "buenos aires": ("Recoleta and the cemetery, San Telmo on a Sunday for the market, and a "
                     "steak and a tango show in the evening. People eat at 10pm, so shift your "
                     "day later or you will be dining alone."),
    "rio de janeiro": ("Copacabana and Ipanema for the beach, Sugarloaf and Christ the Redeemer "
                       "early before the crowds, and Santa Teresa for the afternoon. Take nothing "
                       "valuable to the beach and use the metro after dark."),
    "hanoi": ("the old quarter on foot with a pho stop, Hoan Kiem lake in the morning, and a "
              "coffee on a balcony over the traffic. Cross the road by walking steadily: the "
              "mopeds go round you, not through you."),
    # The cities a person in Britain or Ireland asks about are the ones they can get to for a
    # weekend, and the table was all abroad: "whats manchester like", "what should i do in
    # belfast" and "cheap places to eat in leeds" reached nothing but a search hedge, while the
    # same questions about Lisbon were answered. These are the same shape of card - the two or
    # three things worth the trip, and one thing that saves the day - and every row below also
    # feeds the day-trip, cheap-eats, best-time and length-of-stay rows, which key on this table.
    "manchester": ("the Northern Quarter for food and records, the Museum of Science and Industry "
                   "in the old station, and a tram out to Salford Quays for the Lowry and the "
                   "Imperial War Museum North. Book the Old Trafford or Etihad tour ahead."),
    "liverpool": ("the Albert Dock and the two cathedrals, the Cavern and the Beatles Story if you "
                  "want the music, and the ferry across the Mersey for the skyline. The Walker and "
                  "the World Museum are free."),
    "birmingham": ("the canals round Brindleyplace, the museum and art gallery, and a curry in the "
                   "Balti Triangle rather than the middle of town. The library roof is free and "
                   "has the best view in the city."),
    "leeds": ("the Victoria Quarter and Kirkgate Market in the centre, then Headingley or Chapel "
              "Allerton for dinner. The Royal Armouries is free, and so are the city's galleries."),
    "sheffield": ("the Winter Garden and the Peace Gardens, then Kelham Island for food and a "
                  "brewery tap. The Peak District is half an hour by bus, which is the reason "
                  "most people go."),
    "newcastle": ("the Quayside and the Millennium Bridge, Grainger Town for the arcades, and the "
                  "Baltic in Gateshead for the view. The metro to Tynemouth is a good half day at "
                  "the coast."),
    "nottingham": ("the castle and the Trip to Jerusalem, which is built into the rock, then "
                   "Hockley for food and shops. Wollaton Hall and its deer park are free and a "
                   "good hour."),
    "bristol": ("the harbourside and the SS Great Britain, the Clifton Suspension Bridge, and "
                "Wapping Wharf or Stokes Croft for food. It is a walking city; the buses are the "
                "weak point."),
    "brighton": ("the pier and the pebble beach, the Lanes for shops and the North Laine for food. "
                 "The i360 is the view and the South Downs are a short bus ride."),
    "york": ("the Minster, the Shambles and the city walls, which take an hour and cost nothing. "
             "Book the Minster and the Jorvik ahead in summer."),
    "glasgow": ("Kelvingrove and the Burrell Collection, the Necropolis for the view, and the West "
                "End for food. The subway is a single loop and gets you round the centre."),
    "cardiff": ("the castle in the middle of town, the old arcades for covered shopping streets, "
                "and Cardiff Bay for the waterfront. The national museum is free."),
    "belfast": ("the Titanic museum on the old slipway, the Cathedral Quarter for pubs, and a black "
                "taxi tour if you want the history. The Giant's Causeway is a day out north."),
    "cork": ("the English Market for lunch, St Anne's tower for the bells, and a pint in the old "
             "town. Kinsale and Cobh are short bus or train trips."),
    "galway": ("the Latin Quarter for pubs and buskers, the Claddagh walk along the water, and a "
               "day on Inishmore or in Connemara. Book the Aran ferry ahead in summer."),
}


# The other half of a trip: a city guide answers "what should i do in rome", and the country
# rows answer the weather, the plugs and the money, but the first question - where in the
# country - had nothing behind it, so "where should i go in spain" was a search hedge.
# Three picks with the reason for each, because a list of names is not a choice. The cities
# are the ones with a guide row of their own where there is one, so the next turn ("what
# about seville", "how long in porto") answers properly.
WHERE_TO_GO = {
    "spain": ("Spain",
               "Barcelona for a city and a beach in one trip. Seville for the Alcázar and "
               "the tapas. Madrid for the museums, with Toledo a short train ride away."),
    "italy": ("Italy",
               "Rome for the ancient city and the Vatican. Florence for the art you can walk "
               "between. Naples and the Amalfi coast for pizza and sea."),
    "france": ("France",
               "Paris for the museums and the food. Lyon for the best eating in the country. "
               "Provence for small towns and markets, and don't rush it."),
    "portugal": ("Portugal",
               "Lisbon for trams, tarts and the river. Porto for the port cellars and the "
               "bookshop. The Algarve for beaches and cliffs."),
    "greece": ("Greece",
               "Athens for the Acropolis and street food. Santorini for the view. Naxos for "
               "beaches and cheaper rooms."),
    "japan": ("Japan",
               "Tokyo for the city and the food. Kyoto for temples and old streets. Osaka "
               "for eating, with a rail pass once you visit more than one."),
    "netherlands": ("The Netherlands",
               "Amsterdam for the canals and the museums. Haarlem or Delft as a quieter "
               "base. The country is small, so everywhere is easy to reach."),
    "germany": ("Germany",
               "Berlin for the history and the nightlife. Munich for beer gardens and the "
               "Alps. The Rhine and Mosel valleys for small wine towns."),
    "ireland": ("Ireland",
               "Dublin for a city break. Galway and the Burren if you fly into Shannon. "
               "The west is the trip."),
    "scotland": ("Scotland",
               "Edinburgh for the castle and the Old Town. The Highlands for lochs and "
               "mountains. A car helps north of the cities."),
    "england": ("England",
               "London for the museums and the markets. Bath for the Roman baths. The Lake "
               "District for hills and walking."),
    "turkey": ("Turkey",
               "Istanbul for mosques, bazaars and the ferries up the Bosphorus. Cappadocia "
               "for the balloon flights at sunrise. The coast if you want to swim."),
    "morocco": ("Morocco",
               "Marrakech for the medina and the food. Fes for the crafts and the old city. "
               "Essaouira for the coast and the wind."),
    "croatia": ("Croatia",
               "Split for a Roman palace and ferries to the islands. Dubrovnik for the "
               "walls, early before the crowds. Zadar for quieter evenings."),
    "iceland": ("Iceland",
               "Reykjavik for the city. The south coast to Vik for waterfalls and black-sand "
               "beaches. The ring road takes longer than most people think."),
    "norway": ("Norway",
               "Oslo for the museums and the opera house. The train to Bergen for the "
               "fjords, because the journey is half the point. Tromsø in winter for the "
               "northern lights."),
    "thailand": ("Thailand",
               "Bangkok for temples and street food. Chiang Mai for the north. A flight "
               "south for the islands."),
    "mexico": ("Mexico",
               "Mexico City for the food and the museums. Oaxaca for markets and mezcal. "
               "Tulum if you mainly want the beach."),
    "united states": ("The States",
               "New York for a first trip. San Francisco and the coast for California. "
               "Chicago for food and the lake in summer."),
    "india": ("India",
               "Delhi for the history. Jaipur and Jodhpur for Rajasthan. Kerala for the "
               "backwaters, and one region rather than criss-crossing the country."),
    "australia": ("Australia",
               "Sydney for the harbour and the beaches. Melbourne for food, with the Great "
               "Ocean Road from there. Flying between the cities is normal."),
    "egypt": ("Egypt",
               "Cairo for the pyramids and the museum. Luxor for the temples and the Valley "
               "of the Kings. Aswan for a slower stretch by the river."),
    "canada": ("Canada",
               "Toronto and Montreal for cities. Banff and Jasper for the Rockies. Vancouver "
               "if you want sea and mountains together."),
    "czechia": ("Czechia",
               "Prague for the old town and the castle. Český Krumlov for a smaller, quieter "
               "base. Brno for wine and fewer tourists."),
    "hungary": ("Hungary",
               "Budapest for the baths, the ruin bars and the parliament. The Danube bend if "
               "you want a break from the city. Lake Balaton in summer."),
    "poland": ("Poland",
               "Kraków for the old town, with Auschwitz as a sobering trip out. Warsaw for "
               "the rebuilt city and the museums. Gdańsk for the coast."),
    "austria": ("Austria",
               "Vienna for the palaces and the coffee houses. Salzburg for the old town and "
               "the hills. Innsbruck for the Alps."),
    "switzerland": ("Switzerland",
               "Zurich or Lucerne as a base. The Bernese Oberland for the mountain trains. A "
               "rail pass pays off fast."),
    "belgium": ("Belgium",
               "Brussels briefly, for the Grand Place and the museums. Bruges for the "
               "canals, and Ghent for the same with fewer people. Both are short train rides "
               "from Brussels."),
    "sweden": ("Sweden",
               "Stockholm for the islands and the museums. The archipelago in summer. "
               "Gothenburg for a second city."),
    "denmark": ("Denmark",
               "Copenhagen for the city and the food. Aarhus for a second city. Malmö is a "
               "train ride over the bridge."),
    "finland": ("Finland",
               "Helsinki for the design and the saunas. Lapland in winter for the snow and "
               "the northern lights. A summer cabin by a lake in the other season."),
    "new zealand": ("New Zealand",
               "Queenstown and the southern lakes for the mountains. The North Island for "
               "beaches and volcanoes. Pick one island rather than trying both."),
    "china": ("China",
               "Beijing for the Wall and the Forbidden City. Xi'an for the terracotta army. "
               "Shanghai for a city you can walk."),
    "vietnam": ("Vietnam",
               "Hanoi for the old quarter and the food. Hoi An and the coast by train or a "
               "short flight south. Ha Long Bay for limestone islands and a boat."),
    "dubai": ("Dubai",
               "A short trip: the old creek and the souks in the morning. The desert in the "
               "evening. One big mall, and the marina at night."),
    "singapore": ("Singapore",
               "The hawker centres first. Gardens by the Bay after dark. A walk round Tiong "
               "Bahru for the old flats and the coffee."),
    "cape town": ("Cape Town",
               "Table Mountain on a clear morning. The Cape peninsula drive. The winelands "
               "for the wine farms, and a car to do any of it."),
    "cuba": ("Cuba",
               "Havana for the old town and the cars. Viñales for tobacco country. Take "
               "cash, because cards barely work."),
    "argentina": ("Argentina",
               "Buenos Aires for the food and the nightlife. Mendoza for wine. Patagonia if "
               "you have the time."),
    "brazil": ("Brazil",
               "Rio for the beaches and the views. The Pantanal for wildlife. Salvador for "
               "music and the old town."),
}

# Ways of naming the same country, so one table covers them all.
COUNTRY_ALIASES = {
    "usa": "united states",
    "the states": "united states",
    "america": "united states",
    "us": "united states",
    "uk": "england",
    "great britain": "england",
    "britain": "england",
    "holland": "netherlands",
    "czech republic": "czechia",
    "uae": "dubai",
}


# A country is not something anybody counts or owns, so an article or a possessive in front of
# one of these words means it is the thing of that name and not the place. "how long do i cook a
# chicken for" / "and what about a turkey" was answered "Turkey: Istanbul for mosques, bazaars and
# the ferries up the Bosphorus" - the bird is the only turkey in a line that says "a turkey".
# "what about turkey", "is turkey cheap" and "what about the netherlands" are untouched.
# The word straight in front of the place name is the one that decides, so "a trip to spain" and
# "a week in spain" keep the country's answer: the article there belongs to the trip. Only an
# article or a possessive with nothing between it and the name means the thing, plus the words
# that say how the bird is sold, which nobody says of a country.
COUNTS_AS_A_THING = re.compile(
    r"\b(?:a|an|some|any|another|one|no|every|this|that|these|those|my|your|our|their|his|"
    r"her|its|roast|roasted|frozen|whole|raw|stuffed|cooked|leftover|defrosted|fresh|"
    r"smoked)\s+$", re.I)
# The word after the name decides the other way, because a country is also how people describe
# the trip: "a spain holiday" and "we booked a turkey holiday" are the place, and "a week in a
# spain resort" is the place too. A travel word straight behind the name keeps it a country, and
# anything else ("a turkey sandwich", "a china bowl") leaves it the thing the name is shared with.
COUNTS_AS_A_TRIP = re.compile(
    r"\s+(?:holiday|holidays|vacation|vacations|trip|trips|break|breaks|getaway|getaways|"
    r"week|weeks|weekend|weekends|fortnight|resort|resorts|flight|flights|hotel|hotels|"
    r"hostel|hostels|tour|tours|guide|guides|map|maps|visa|visas|beach|beaches|city|"
    r"coast|island|islands|airport|airports|transfer|transfers|excursion|excursions|"
    r"adventure|adventures)\b", re.I)


# The article only makes a thing of a name that is a thing as well as a place, and that is a fact
# about these few words rather than about a line: turkey the bird, china the plates, jersey the
# shirt, guinea the pet, chile the pepper. There is no Greece the object, so "how long for a
# greece" and "how many days in a spain" are the country said with one article too many, and they
# keep the itinerary. A country that is not here is never fenced by its article alone.
ALSO_A_THING = frozenset({"turkey", "china", "jersey", "guinea", "chile"})


def _a_thing_not_a_place(clean, name):
    """Whether the place word in this line is preceded by a word that makes it a thing.

    Every mention of the name has to be the thing: "a turkey for christmas, then two weeks in
    turkey" names the country as well, and the country is what the line is about. A mention with
    a travel word behind it is the place too, so one of those is enough to keep the country.
    """
    if str(name or "").strip().lower() not in ALSO_A_THING:
        return False    # no such object, so the article belongs to the place
    low = " " + " ".join(str(clean or "").lower().split()) + " "
    found_a_thing = False
    for match in re.finditer(r"\b" + re.escape(name.lower()) + r"\b", low):
        if COUNTS_AS_A_THING.search(low[:match.start()]):
            if COUNTS_AS_A_TRIP.match(low[match.end():]):
                return False
            found_a_thing = True
        else:
            return False
    return found_a_thing

# A trip is said in words of its own: "where should i go in turkey", "what about a trip to spain",
# "somewhere warm in january". A country named without one of them is the country, not a
# destination.
TRIP_WORDS = re.compile(
    r"\b(?:trip|trips|holiday|holidays|travel\w*|visit\w*|flying|flights?|honeymoon|abroad|"
    r"somewhere|city break|weekend (?:away|in)|a week in|fortnight|beach\w*|going away|"
    r"get away|day out|get(?:ting)? to|where (?:should|shall|do|can) i go)\b", re.I)


# A question whose answer is a fact of the country itself - its capital - is not a travel
# question, and the same question about the next country is not one either: "and what about
# canada" after the capital of Australia is the capital of Canada, and the answers entry has
# Ottawa. The shape is one ask on purpose: a fact the knowledge base does not hold ("how big is
# canada") is answered better by the picks than by a search hedge, so only the ask that is
# answered is turned away from them.
A_FACT_OF_THE_COUNTRY = re.compile(r"\bcapital\b", re.I)


def _the_country_was_the_question(memory, name):
    """Whether the place named here is the subject of the question before it.

    "whats the capital of australia" then "and what about canada" is the capital of Canada, and
    the picks answered it with "Canada: Toronto and Montreal for cities". A country named in a
    follow-up belongs to the line before it when that line was a fact question about a
    country; the picks are for a line that says, in words of its own, that it is about going
    somewhere.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return False
    last = turns[-1]
    said = last.get("user") if isinstance(last, dict) else None
    if not isinstance(said, str) or not said.strip():
        return False
    if TRIP_WORDS.search(said):
        return False
    if not A_FACT_OF_THE_COUNTRY.search(said):
        return False  # "my sister lives in spain" is about the sister, and the picks still fit
    before = _find_in(said, WHERE_TO_GO) or _find_in(said, COUNTRY_ALIASES)
    if not before or before == name:
        return False  # the same country named again is a question about that country
    return True


def _where_to_go(memory, understood):
    """"Where should i go in spain": the picks, and the reason for each one."""
    clean = understood.get("clean", "")
    name = _find_in(clean, WHERE_TO_GO) or _find_in(clean, COUNTRY_ALIASES)
    if not name:
        return None
    if _a_thing_not_a_place(clean, name):
        return None
    if _us_is_a_pronoun(clean, name):
        return None
    if not TRIP_WORDS.search(clean) and _the_country_was_the_question(memory, name):
        return None
    country = COUNTRY_ALIASES.get(name, name)
    label, body = WHERE_TO_GO[country]
    return f"{label}: {body}"


# "us" is the pronoun far more often than it is the country: "i have 20 pound to feed us for a
# week" is a sum and a person, and the picks answered it with New York and San Francisco. The
# country is only ever said with its article, and the line says "the us" when it means the place.
_US_AS_A_PLACE = re.compile(r"\bthe\s+us\b", re.I)


def _us_is_a_pronoun(clean, name):
    """Whether the "us" this line found is the country or the people in it."""
    if str(name or "").strip().lower() != "us":
        return False
    return not _US_AS_A_PLACE.search(str(clean or ""))


def _country_trip(memory, understood):
    """"We are going to greece in july": the country's picks, since nowhere in it is named.

    The country table is the same one the "where should i go in spain" line reads, so a bare
    mention of the country gets the three places rather than an acknowledgement of the news.
    """
    clean = understood.get("clean", "")
    name = _find_in(clean, WHERE_TO_GO) or _find_in(clean, COUNTRY_ALIASES)
    if _us_is_a_pronoun(clean, name):
        return None
    label, body = WHERE_TO_GO[COUNTRY_ALIASES.get(name, name)]
    return f"{label}: {body}"


# The words that make a country name a trip rather than a fact about the place: "im going to
# spain", "we are off to greece in july", "booked a trip to portugal".
COUNTRY_TRIP_WORDS = ("going to", "going", "off to", "heading to", "heading off to", "fly to",
                      "flying to", "flew to", "trip to", "travel to", "travelling to",
                      "traveling to", "holiday in", "holidays in", "visiting", "visit to",
                      "week in", "fortnight in", "honeymoon in", "booked to", "we are in",
                      "im in",
                      # "what should i see in portugal in a week" and "best places to visit in
                      # spain for a week" name the country with a trip and were reaching the
                      # search hedge and the away-for-a-week card. A length of stay said after
                      # the country is the same trip as "a week in spain".
                      "see in", "visit in", "in a week", "for a week",
                      "in a fortnight", "for a fortnight")

# A line about what to put in the case names the country only to say where the case is going:
# "what should i pack for a week in spain in october" is the packing list's question, and "week
# in" alone was enough to hand it the three places instead. The packing row reads the country
# itself for the climate, so it loses nothing by keeping the line.
PACKING_WORDS = ("pack", "packs", "packing", "packed", "suitcase", "suitcases", "luggage",
                 "clothes", "clothing", "wear", "wearing", "jumper", "jumpers", "coat",
                 "coats", "jacket", "jackets", "shoes", "trainers", "toiletries",
                 "swimwear", "bikini", "hand luggage", "carry on")

# The rows that name a country for some other reason, all of which keep their own answer.
NOT_A_COUNTRY_TRIP = ("live in", "living in", "move to", "moving to", "emigrate", "residency",
                      "work in", "working in", "job in", "jobs in", "study in", "driving",
                      "drive", "car hire", "hire car", "licence", "insurance", "visa",
                      "safe", "safety", "dangerous", "crime", "hospital", "doctor", "school",
                      "schools", "how much", "cost", "costs", "money", "currency", "weather",
                      # The money question is asked with the cost adjective as often as with
                      # "how much": "is spain expensive for a week" was the cost card until a
                      # length of stay said after the country became a trip, and the adjective
                      # was the only thing that kept the two apart.
                      "expensive", "cheap", "cheaper", "cheapest", "pricey", "affordable",
                      "costly", "dear", "prices", "price", "budget", "luxury", "spend",
                      "worth it",
                      # "is 400 enough for a week in spain" has an amount and no cost word at
                      # all, so "a week in" was enough to hand it the three places to go.
                      "enough", "cover it", "cut it", "go far",
                      "too hot", "too cold", "best time", "what month", "when to go",
                      "time difference", "plug", "adaptor", "adapter", "water", "tap water",
                      "jab", "jabs", "vaccine", "vaccinations", "malaria", "pet", "dog", "cat",
                      # how long the flight is, which is the air time and not the pick of places
                      "how long to fly", "how long is the flight", "flight time",
                      "hours in the air", "how long does it take to fly")
NOT_A_COUNTRY_TRIP += PACKING_WORDS

# A rough monthly range in Celsius that most years stay inside, by climate.
CLIMATES = {
    "mediterranean": {1: (8, 15), 2: (9, 16), 3: (11, 18), 4: (12, 20), 5: (15, 24), 6: (19, 29),
                      7: (22, 32), 8: (22, 32), 9: (19, 28), 10: (15, 23), 11: (11, 18),
                      12: (9, 15)},
    "temperate": {1: (1, 7), 2: (1, 8), 3: (3, 11), 4: (5, 15), 5: (8, 19), 6: (11, 22),
                  7: (13, 24), 8: (13, 24), 9: (11, 20), 10: (8, 15), 11: (4, 10), 12: (2, 7)},
    "hot-summer": {1: (0, 4), 2: (-1, 5), 3: (3, 10), 4: (8, 17), 5: (13, 23), 6: (17, 27),
                   7: (19, 29), 8: (18, 28), 9: (14, 23), 10: (8, 16), 11: (3, 9), 12: (1, 5)},
}
CITY_CLIMATE = {
    "lisbon": "mediterranean", "rome": "mediterranean", "florence": "mediterranean",
    "barcelona": "mediterranean", "madrid": "mediterranean", "athens": "mediterranean",
    "seville": "mediterranean", "istanbul": "mediterranean", "venice": "mediterranean",
    "porto": "mediterranean", "paris": "temperate", "amsterdam": "temperate",
    "london": "temperate", "edinburgh": "temperate", "dublin": "temperate",
    "berlin": "temperate", "copenhagen": "temperate", "stockholm": "temperate",
    "reykjavik": "temperate", "new york": "temperate", "boston": "temperate",
    "prague": "hot-summer", "vienna": "hot-summer", "budapest": "hot-summer",
}
MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9,
    "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


# The cities people ask "when should I go" about, mapped to the country note they belong to.
CITY_COUNTRY = {"rome": "italy", "venice": "italy", "florence": "italy", "milan": "italy",
                "naples": "italy", "paris": "france", "lisbon": "portugal", "porto": "portugal",
                "barcelona": "spain", "madrid": "spain", "seville": "spain", "athens": "greece",
                "santorini": "greece", "crete": "greece", "tokyo": "japan", "kyoto": "japan",
                "bangkok": "thailand", "istanbul": "turkey", "dubai": "dubai",
                "reykjavik": "iceland", "oslo": "norway", "bergen": "norway",
                "edinburgh": "scotland", "marrakech": "morocco", "mexico city": "mexico",
                "sydney": "australia", "melbourne": "australia", "delhi": "india",
                "mumbai": "india", "split": "croatia", "dubrovnik": "croatia", "zadar": "croatia"}


# When to go, per city. The country row answers a country question, and a city inherits
# everything its country gets wrong about it: "when should I go to Porto" came back with "July
# and August are hot and busy on the Algarve, and the north is wet from November", which is
# Lisbon's answer and the wrong way round for Porto. A city row is one fact per city, so the
# answer is about the place that was asked about.
CITY_BEST_TIME = {
    "london": "May, June and September: 18-22C and the long evenings. July and August are warm "
              "and crowded, and November to February is grey, wet and dark by 4.30pm.",
    "edinburgh": "May, June and September: 15-20C, and daylight until nearly 11pm in June; August "
                 "is the Festival and the Fringe, which is either why you go or when to avoid. "
                 "November to February is dark by 4pm.",
    "bath": "May to September for the baths, the crescent and the canal; April and October are "
            "quieter and still fine. December is the Christmas market, which is the busiest "
            "weekend of the year.",
    "dublin": "May, June and September: 16-20C and the longest days. July and August are the "
              "driest and busiest, and November to February is wet, with dark by 4.30pm.",
    "amsterdam": "April to June and September: 15-22C and the canals at their best, with the "
                 "tulips at Keukenhof in late April. July and August are the busiest, and "
                 "November to February is cold, wet and dark early.",
    "brussels": "May, June and September: 17-22C, and the Grand Place flower carpet in mid-August "
                "every second year. July and August are warm and quiet at weekends, and winter "
                "is grey and wet.",
    "paris": "April to June and September to early October: 18-24C and the parks at their best. "
             "July and August are hot and many small restaurants close, and November to February "
             "is grey and cool.",
    "munich": "May to September: 20-25C, beer gardens and the Alps an hour away; late September "
              "is Oktoberfest, which doubles hotel prices. December brings the Christmas markets.",
    "zurich": "May to September for the lake, the old town and the mountain railways, at 22-26C in "
              "midsummer. December to February is cold and clear, which is when the Alps look "
              "their best.",
    "berlin": "May to September: 20-25C, outdoor cafes, the lakes, and the city at its most "
              "relaxed. July and August are the warmest and busiest, and November to February is "
              "grey and cold.",
    "prague": "April to June and September: 15-22C and the old town before the crush. July and "
              "August are busy and 25C+, and December is cold with the Christmas markets.",
    "vienna": "April to June and September: 18-24C, and the ball season runs January to March. "
              "July and August are hot and the opera houses close, and December has the markets.",
    "budapest": "April to June and September: 20-26C, and the thermal baths are good in cool "
                "weather too. July and August are 30C+, and December brings the Christmas "
                "markets along the Danube.",
    "krakow": "May to September: 20-25C and the main square at its best; April and October are "
              "quiet and still fine. December to February is cold with snow and a Christmas "
              "market.",
    "ljubljana": "May, June and September: 20-26C, and Lake Bled is warm enough to swim from "
                 "June. July and August are the busiest, and winter is cold and quiet.",
    "copenhagen": "May to August: 18-22C, long days, and the harbour baths open from June. July "
                  "is the busiest and the jazz festival, and November to February is dark by "
                  "4pm and cold.",
    "stockholm": "May to August: 18-23C and light until late, with midsummer at the end of June. "
                 "The archipelago is best from July to mid-August, and winter is dark with short "
                 "days.",
    "helsinki": "June to August: 18-23C with almost no night, and the archipelago ferries "
                "running. January and February are the coldest, with the best chance of snow, "
                "and December is dark.",
    "tallinn": "June to August: 18-22C, the old town at its best and white nights in June. "
               "December to February is cold and snowy, and the Christmas market is one of the "
               "prettiest in Europe.",
    "reykjavik": "June to August gives midnight sun, open highland roads and puffins; February and "
                 "March are best for the northern lights. November is dark, wet and icy, so it is "
                 "the one month I would skip.",
    "oslo": "May to September: 18-23C, and the fjord islands are a ferry ride from the centre. "
            "June has the longest days, and November to February is cold and dark, with skiing an "
            "hour out of town.",
    "bergen": "May to September: 15-19C and the fjord trips running, with light until late in June "
              "and July. It rains most of the year, so pack a shell whatever the month.",
    "rome": "April, May, late September and October: 20-26C and the ruins walkable. July and "
            "August are 30C+ with the fountains as the only relief, and August means half the "
            "restaurants shut.",
    "venice": "April, May, late September and October: 18-24C, warm, not crowded and everything "
              "open. July and August are hot and packed, and November to January brings acqua "
              "alta.",
    "florence": "April to June and September to October: 20-28C and the galleries without the "
                "August crush. July and August are 30C+ and busy, and winter means cool days and "
                "short queues.",
    "milan": "April to June and September: 20-27C and the aperitivo season. July and August are "
             "hot and humid and the city half empties, and January is cold with the sales on.",
    "naples": "April to June and September: 22-27C, with the ferries to Capri and the Amalfi "
              "coast running. July and August are hot and busy, and November to March is quiet "
              "and wet.",
    "lisbon": "May, June and September: warm and dry with fewer people. July and August are hot "
              "and busy with the tourists, and November to February is wet, though milder than "
              "the north.",
    "porto": "May, June and September: 18-24C and dry, with the Douro valley at its best and the "
             "vines in leaf. July and August are warm and busy, and November to March is wet and "
             "grey.",
    "valencia": "April to June and September to October: 20-26C, and the sea still swimmable in "
                "October. July and August are 30C+ and busy, and March is Las Fallas if you want "
                "the crowds.",
    "granada": "April to June and September to October: 18-28C, and the Alhambra bookable without "
               "a fight. July and August are 35C+ inland, and winter is cold up at the Alhambra.",
    "san sebastian": "June to September: 20-24C for the beach and the pintxos, with the film "
                     "festival at the end of September. July and August are the busiest, and the "
                     "rest of the year is wet.",
    "barcelona": "May, June and September: 22-27C, the sea warm enough to swim and the terraces "
                 "full. August is hot and packed, and November to February is cool with some "
                 "rain.",
    "madrid": "April, May, June and September: 20-28C and dry, with the terraces out and the "
              "Prado quiet. July and August are 35C+ and the city empties, and winter is cold and "
              "clear.",
    "seville": "March to May and October: 20-28C and the orange trees in flower or in fruit, with "
               "Semana Santa and the April fair the peak. July and August are 40C+, so people "
               "live at night.",
    "athens": "April, May, October and early November: 20-26C and the sites walkable. July and "
              "August are 35C+ and the Acropolis is a scramble by 10am, and the islands are at "
              "their best in June and September.",
    "santorini": "May, June, September and early October: 24-27C, warm sea and no crush. July and "
                 "August are 30C+ with the cruise crowds landing mid-morning, and many hotels "
                 "close from November to March.",
    "crete": "May, June, September and early October: 24-28C and the sea warm, and the Samaria "
             "gorge opens in May. July and August are 30C+ and busy, and winter is mild on the "
             "south coast.",
    "split": "May, June, September and early October: 22-27C, with the ferries to Hvar and Brac "
             "running. July and August are the peak and the old town is packed by day, and many "
             "islands shut from October.",
    "dubrovnik": "May, June, September and early October: 22-27C and the city walls walkable. "
                 "July and August are the peak and the cruise ships fill the old town by 10am, "
                 "and winter is quiet.",
    "zadar": "May, June and September: 22-27C and the sea warm enough to swim, with the Kornati "
             "islands as a day trip. July and August are busy, and winter is quiet.",
    "istanbul": "April, May, September and October: 18-25C and dry, and the Bosphorus ferries at "
                "their best. July and August are hot and humid, and December to February is cold "
                "and wet.",
    "tokyo": "Late March to April for the blossom, and October to November for the autumn colour "
             "and the clearest skies. June is the rainy season, August is hot and humid, and the "
             "New Year week closes many places.",
    "kyoto": "Late March to early April for the blossom, and mid-November for the maples. July "
             "and August are hot and humid, and the New Year week is the busiest of the year.",
    "bangkok": "November to February: dry, warm and clear, which is why it is the season. March "
               "to May is hot and hazy, and June to October is the monsoon with short, heavy "
               "afternoon rain.",
    "hanoi": "October to December: 20-26C, dry and clear. January to March is cool and damp with "
             "drizzle, and May to September is hot and wet, with the heaviest rain in July and "
             "August.",
    "singapore": "Any month works: it is 30C and humid all year, with rain in short bursts. "
                 "February to April is the driest, November to January the wettest, and the haze "
                 "can arrive in September.",
    "dubai": "November to March, when it is 20-30C and you can be outside. From June to "
             "September it is over 40C, so people live in air conditioning and the hotel prices "
             "fall.",
    "marrakech": "March to May and October to November: 20-28C by day, cool at night, no extreme "
                 "heat. July and August are 40C+ in the city, and the desert is cold at night all "
                 "year.",
    "cape town": "November to March: dry, 25-28C, the beaches and the Table Mountain cableway at "
                 "their best. July and August are wet and windy, which is the whale season in "
                 "Hermanus.",
    "havana": "November to April: dry and 24-28C. May to October is hot and wet, and August to "
              "October is hurricane season, though the rain usually comes in short afternoon "
              "storms.",
    "buenos aires": "March to May and September to November: 18-25C and the parks at their best. "
                    "December to February is hot and humid and the city empties in January, and "
                    "July and August are cool and damp.",
    "rio de janeiro": "December to March is hot, 28-32C, and Carnival falls in February or early "
                      "March. May to October is cooler and drier, and the sea is still warm in "
                      "September.",
    "mexico city": "March to May: dry, warm and clear, before the rains. June to October is the "
                   "wet season with short afternoon storms, and December to February is dry with "
                   "cold nights.",
    "sydney": "September to November and March to May: 20-26C, warm without the scorch. December "
              "to February is 30C+ and the beaches are packed, and June to August is mild, with "
              "whale watching.",
    "melbourne": "March to May and September to November: 18-24C, and the city is at its best in "
                 "autumn. December to February is hot and changeable, and winter is cold and "
                 "football.",
    "delhi": "October to March: dry and cooler, 15-25C. April to June is brutally hot at 40C+, "
             "and the monsoon runs July to September with flooding in some years.",
    "mumbai": "November to February: dry, 25-30C and the most comfortable. March to June is hot "
              "and humid, and the monsoon runs June to September with heavy rain.",
    "new york": "May to June and September to October: mild and walkable at 20-26C. July and "
                "August are hot and humid, January and February are cold with snow, and the "
                "Christmas weeks are the most expensive of the year.",
    "boston": "May, June, September and October: 18-26C, and October for the foliage. July and "
              "August are hot and humid, and January and February are cold with snow.",
    "chicago": "May, June and September: 20-27C and the lakefront at its best. July and August "
               "are hot and humid, and January and February are brutal with the wind off the "
               "lake.",
    "san francisco": "September and October: the warmest, clearest months at 18-24C. July and "
                     "August are foggy and cool, and the rain comes November to March.",
    "los angeles": "March to May and September to November: 20-26C and clear. June to August is "
                   "warm but the marine layer can sit all day at the beaches, and winter is mild "
                   "with the odd storm.",
    "toronto": "May to June and September to October: 18-25C. July and August are hot and humid, "
               "and December to March is cold with snow.",
}

# The regions people ask about by name - Cornwall, Devon, the Lakes, Norfolk, Yorkshire - are
# not cities, and they are kept out of CITY_BEST_TIME on purpose: the memory store reads that
# table to add the season of a place to a trip already booked ("we booked a cottage in
# Cornwall for august"), and there the general note about the school-holiday crush is the
# sharper sentence. This table is read by the when-to-go rows only, which had nothing to say
# about any of these places while Rome and Paris were in the table.
REGION_BEST_TIME = {
    # The home counties and the coasts were missing from this table while Rome, Paris and Berlin
    # were in it: "best time to visit cornwall" was a search hedge. Each is a region and not a
    # country, so each gets its own row rather than England's.
    "cornwall": "May, June and September: 16-20C, the coast path at its best and the lanes still "
                "quiet. July and August are the warmest weeks and the busiest by a long way, and "
                "October is mild and much emptier, with the Atlantic at its biggest.",
    "devon": "May, June and September: 16-20C, both coasts open and the beaches half empty. Late "
             "July and August are the school-holiday crush on the sand and the roads, and October "
             "is still mild if you do not mind a shower.",
    "lake district": "May, June and September for long clear days at 15-20C; September is the "
                     "quietest dry-ish month and the fells are at their best. July and August "
                     "bring the crowds to Windermere and the passes, and November to February is "
                     "wet, dark and often icy on the tops.",
    "norfolk": "May to September: the Broads and the north Norfolk coast at 18-22C, and the seal "
               "trips running. July and August fill the coastal villages, and October to March is "
               "quiet, cheap and cold, with huge skies and good birdwatching.",
    "yorkshire": "May to September: 16-20C, the Dales and the moors dry and open, and the coast "
                 "best in June and September. The towns are busy at half term and in August, and "
                 "the moors are bleak from November to February.",
}

# Every place with a when-to-go note, for the rows that answer "when" rather than "what is it
# like in august": the two are read apart so the memory store cannot pick up a region.
WHEN_TO_GO = {**CITY_BEST_TIME, **REGION_BEST_TIME}

# When to go, per destination: the months worth paying for, and the month to skip, and why.
# Written as a whole sentence because "when should I go" has a different answer for Iceland
# and for Seville, and the reason matters as much as the month.
BEST_TIME = {
    "iceland": "June to August gives midnight sun, open highland roads and puffins; February and "
                "March are best for the northern lights. November is dark, wet and icy, so it is "
                "the one month I would skip.",
    "greece": "May, June, September and early October: warm sea, open tavernas and no crush. August "
              "is 35C and the islands are packed, and many small hotels close from November to "
              "March.",
    "spain": "April to June and September to October, when it is 20-28C and the coast is quiet. "
             "July and August are 35C+ inland and busy on the coast; the north stays green and "
             "cooler in summer.",
    "italy": "April, May, late September and October: warm, not crowded, everything open. July and "
             "August are hot and packed, and August in the cities means half the restaurants shut.",
    "portugal": "May, June and September: warm and dry with fewer people. July and August are hot "
                "and busy on the Algarve, and the north is wet from November to February.",
    "croatia": "June and September: the sea is warm and the coast is not yet rammed. July and "
               "August are the peak, and many islands shut down entirely from October.",
    "turkey": "May, June and September for the coast, and April or October for Istanbul. July and "
              "August are hot and crowded, and the coast is quiet and mild in winter.",
    "japan": "Late March to April for the blossom, or October to November for the autumn colour. "
             "June is the rainy season, August is hot and humid, and the New Year week is the "
             "busiest travel period of the year.",
    "thailand": "November to February: dry, warm and clear. March to May is hot and hazy, and June "
                "to October is the monsoon, when the islands get rough seas and some boats stop.",
    "dubai": "November to March, when it is 20-30C and you can be outside. From June to September "
             "it is over 40C, so people live in air conditioning and the hotel prices fall.",
    "new york": "May to June and September to October: mild and walkable. July and August are hot "
                "and humid, January and February are cold with snow, and the Christmas weeks are "
                "the most expensive of the year.",
    "norway": "June to August for the fjords, the midnight sun and the coastal ferries. The "
              "northern lights need September to March and a clear, dark sky, and much of the "
              "mountain roads close in winter.",
    "scotland": "May to September for the Highlands, the islands and the long evenings. Midges "
                "are worst in July and August, and November to February has very short days.",
    "morocco": "March to May and September to November: warm days, cool nights, no extreme heat. "
               "July and August are 40C+ inland, and the desert is cold at night all year.",
    "mexico": "November to April is the dry season, which is why it is the busy one. May to "
              "October is hot and wet, with rain usually in short afternoon storms.",
    "australia": "September to November and March to May for the south: warm, not scorching. "
                 "December to February is 35C+ in Sydney and Melbourne, and the north is tropical "
                 "wet season then.",
    "india": "October to March for most of the country: dry and cooler. April to June is "
             "brutally hot in the north, and the monsoon runs June to September.",
    "usa": "It depends where: May and September for the northeast, spring and autumn for the "
           "southwest, and June to September for the national parks and mountains. Avoid the "
           "July 4th week and Thanksgiving for flights.",
}

# Getting from the airport into the centre: what it costs and how long it takes. The reply is
# the cheapest sensible way first, because that is what people are asking.
AIRPORT_TRANSFER = {
    # The London airports have their own entry (london-airport), because one city with five
    # airports is a different question: keeping a copy here made the older text win.
    "fiumicino": "the Leonardo Express to Termini is 32 minutes and \u20ac14, or a regional train to "
                 "Trastevere and the metro for less. A taxi is a flat \u20ac55 to the centre.",
    "lisbon airport": "the metro (red line) into town is 20 minutes for about \u20ac2 with a Viva "
                      "card; a taxi is 15-20 minutes and \u20ac15-20. Uber works too.",
    "charles de gaulle": "the RER B into the centre is 35 minutes and about \u20ac11.80; a taxi is a "
                         "flat \u20ac56 to the right bank. Orly has the Orlyval plus RER, and a "
                         "tram now too.",
    "barcelona airport": "the Aerobus to Plaza Catalunya is 35 minutes and about \u20ac7.50; the "
                         "train to Sants is cheaper and slower. A taxi is a flat \u20ac35.",
    "amsterdam airport": "the train to Centraal is 15-20 minutes and about \u20ac6; buy the ticket "
                         "from the machine before the gates, not on board.",
    "dublin airport": "the Aircoach or the 747 bus to the centre is about \u20ac7-10 and 30-45 "
                      "minutes; a taxi is \u20ac25-30. There is no train link yet.",
    "edinburgh airport": "the tram or the 100 bus to the centre is about 30 minutes and \u00a36.50; "
                         "a taxi is \u00a325-30. The tram stops at Haymarket and Princes Street.",
    "jfk": "the AirTrain plus the subway is about \u20ac10 and 60-75 minutes; the LIRR from Jamaica "
            "is faster. A yellow cab is a flat fare to Manhattan, plus tolls and tip.",
    "berlin airport": "the FEX or S9 train to Hauptbahnhof is 30 minutes and about \u20ac4.40; a "
                      "taxi is \u20ac40-50.",
    "porto airport": "the metro line E to the centre is 30 minutes for about \u20ac2 with an "
                     "Andante card; a taxi is 20-25 minutes and \u20ac20-25.",
    "dubrovnik airport": "the Atlas shuttle to the old town is about \u20ac8 and 30-40 minutes, "
                         "timed to the flights; a taxi is \u20ac40-50. There is no train.",
    "krakow airport": "the train to the main station is 20 minutes for about 12 zloty, and bus "
                      "252 runs too; a taxi is 25-30 minutes and 70-90 zloty.",
    "budapest airport": "bus 100E to Deak Ferenc ter is 30 minutes for about 900 forint, and no "
                        "metro reaches the airport; a taxi is 25-30 minutes and about 10,000 "
                        "forint.",
    "venice airport": "the ATVO bus to Piazzale Roma is 20 minutes and \u20ac10, and the Alilaguna "
                      "boat to San Marco is 75 minutes and \u20ac15; a water taxi is \u20ac100+.",
    "copenhagen airport": "the metro to Kongens Nytorv is 15 minutes and about 30 kroner, and the "
                          "train also runs to the central station; a taxi is 250-300 kroner.",
    "athens airport": "metro line 3 to Syntagma is 40 minutes and \u20ac9, and the X95 bus is "
                      "\u20ac5.50 and slower; a taxi is 35-45 minutes and \u20ac40.",
    "seville airport": "the EA airport bus to the centre is 35 minutes and \u20ac4; a taxi is 20 "
                       "minutes and about \u20ac25. There is no train link.",
    "florence airport": "the T2 tram to Santa Maria Novella is 20 minutes and \u20ac1.50; a taxi "
                        "is 20 minutes and about \u20ac25.",
    "marrakech airport": "bus 19 to the medina is 30 minutes and 30 dirham; a taxi should be about "
                         "100 dirham, and agree the price before you get in.",
    "naples airport": "the Alibus to the central station and the port is 20-25 minutes and "
                      "\u20ac5; a taxi is about \u20ac25, agreed first.",
    "madrid airport": "the metro line 8 to Nuevos Ministerios is about \u20ac5 and 40 minutes; the "
                      "Cercanias train to Atocha is faster. A taxi is a flat \u20ac33.",
    # The price in the local currency, because a euro figure is the wrong note at a Prague
    # ticket machine. This key was written twice and a dict keeps only the last one, so the
    # koruna answer was dead and every line got the euro one.
    "prague airport": "bus 119 to the metro at Nadrazi Veleslavin is 15 minutes and 40 koruna, "
                      "then the metro, or the Airport Express bus to the main station in about "
                      "40 minutes; a taxi is 30 minutes and 500-600 koruna, and agree the price "
                      "first.",
    "istanbul airport": "the metro or the Havaist bus to the centre is about \u20ac2-5 and takes "
                        "40-60 minutes; a taxi is much more and the traffic is bad.",
    "lisbon": "the metro (red line) into town is 20 minutes for about \u20ac2 with a Viva card; a "
               "taxi is 15-20 minutes and \u20ac15-20.",
    "rome": "from Fiumicino the Leonardo Express to Termini is 32 minutes and \u20ac14; the regional "
             "train plus metro is cheaper. A taxi is a flat \u20ac55.",
    "paris": "from Charles de Gaulle the RER B is 35 minutes and about \u20ac11.80; from Orly the "
              "Orlyval plus RER, or the tram. A taxi from CDG is a flat \u20ac56 to the right bank.",
    # The transfer half of the cities the AIRPORT_NAME table answers for. A city in that table
    # was still shrugging on "how do i get from vienna airport to the city", because this is the
    # table the transfer question reads.
    "vienna airport": "the S-Bahn S7 to Wien Mitte is 25 minutes for about \u20ac4.60, and the City "
                      "Airport Train is 16 minutes and \u20ac14.90. A taxi is a flat \u20ac40.",
    "zurich airport": "the train to the main station is 10 to 12 minutes for about 7 francs, and "
                      "it runs every few minutes. A taxi is 30 to 40 francs and slower.",
    "munich airport": "the S-Bahn S1 or S8 to the centre is 40 minutes on a normal city ticket, "
                      "about \u20ac13; a taxi is \u20ac70 or more and no quicker in traffic.",
    "frankfurt airport": "the S-Bahn S8 or S9 to the main station is 15 minutes and about "
                         "\u20ac6.50; a taxi is 25 minutes and \u20ac35-40.",
    # Written twice as well, so the first answer - which said only that the express was the most
    # expensive way - was dead, and the live one had the prices. One key carries both now.
    "stockholm airport": "the Arlanda Express to the central station is 20 minutes and about "
                         "320 kronor, and the commuter train is 40 minutes and cheaper; the "
                         "express is the most expensive way. A taxi is 45 minutes and 500 "
                         "kronor or more.",
    "oslo airport": "the Flytoget to the central station is 20 minutes for about 240 kroner, and "
                    "the Vy regional train is slower and half the price. A taxi is 45 minutes "
                    "and very expensive.",
    "helsinki airport": "the I or P train to the central station is 30 minutes for about "
                        "\u20ac4.10, and it is the same ticket as the city trams.",
    "tokyo airport": "Haneda is the quick one: the monorail to Hamamatsucho is 20 minutes for "
                     "about 500 yen, and the Keikyu line goes to Shinagawa. From Narita the "
                     "Skyliner to Ueno is 41 minutes and about 2,570 yen.",
    "kyoto": "Kansai airport is 75 minutes away on the Haruka train, which is the easiest way; a "
              "taxi is not worth the price.",
    "brussels airport": "the train to the central station is 20 minutes and about \u20ac11, and "
                        "it runs four times an hour. From Charleroi the bus to Midi takes an "
                        "hour.",
    "bangkok airport": "the Airport Rail Link from Suvarnabhumi to Phaya Thai is 30 minutes for "
                       "45 baht, and the metro joins it there. A taxi with tolls is 40 to 60 "
                       "minutes and 400 to 500 baht.",
    "singapore airport": "the MRT to the city is 30 to 40 minutes for about S$2, changing at "
                         "Tanah Merah. A taxi is 20 to 30 minutes and S$20-30 with the airport "
                         "surcharge.",
    "hanoi airport": "bus 86 to the old quarter is 45 minutes for 35,000 dong, and a Grab or a "
                     "taxi is about 350,000 dong and 40 minutes.",
    "cape town airport": "an Uber or a taxi to the centre is 20 to 30 minutes and about 250 "
                         "rand. There is a train, but not one to take with bags.",
    "mexico city airport": "the metro line 5 is the cheap way and slow with luggage; a taxi from "
                           "the official stand inside the terminal is 30 to 45 minutes and "
                           "about 250 pesos.",
    "havana airport": "a taxi to the old town is 25 to 30 minutes and about 25 dollars or the "
                      "same in euros; the airport bus is not worth the wait.",
    "buenos aires airport": "Ezeiza is 45 minutes by taxi and about 30 dollars, and bus 8 is the "
                            "cheap way but slow. Aeroparque is in the city itself.",
    "rio airport": "Galeao is 30 to 50 minutes by taxi, and the BRT bus to the centre is cheaper "
                   "and takes about an hour. Santos Dumont is in the city.",
    "sydney airport": "the Airport Link train to Central is 13 minutes for about 20 Australian "
                      "dollars. A taxi is 25 to 35 dollars and slower in the morning peak.",
    "toronto airport": "the UP Express to Union station is 25 minutes for about 12 Canadian "
                       "dollars and runs every 15 minutes.",
    "chicago airport": "the CTA Blue Line from O'Hare runs all night, 45 minutes for $5. A taxi "
                       "is 40 to 60 minutes and $50 or more with the tip.",
    "boston airport": "the Silver Line SL1 bus from the terminals takes about 20 minutes for a "
                      "normal subway fare, and the water taxi across the harbour is the fun way.",
    "san francisco airport": "BART to the city is 30 minutes for about $10. A taxi is 25 to 40 "
                             "minutes and $50 or more.",
    "los angeles airport": "the FlyAway bus to Union Station is about 45 minutes and $10; a taxi "
                           "or a rideshare is 30 to 60 minutes and $50 or more, depending on the "
                           "traffic.",
}

# Which airport serves a city, and the first thing to know about getting in. "what airport is
# closest to lisbon" asks for the name, not for a security procedure or a shrug.
AIRPORT_NAME = {
    "dubrovnik": "Dubrovnik (DBV) is 20km south-east, and the Atlas shuttle to the old town is "
                 "about \u20ac8 and 30-40 minutes, timed to the flights; a taxi is \u20ac40-50.",
    "krakow": "Krakow John Paul II (KRK) is 11km west, and the train to the main station is 20 "
              "minutes for about 12 zloty; a taxi is 70-90 zloty.",
    "budapest": "Budapest Ferenc Liszt (BUD) is 16km south-east, and bus 100E to Deak Ferenc ter "
                "is 30 minutes for about 900 forint; a taxi is about 10,000 forint.",
    "venice": "Venice has two: Marco Polo (VCE) for most flights, 13km north, and Treviso (TSF) "
              "for budget ones, 40km away. From Marco Polo the ATVO bus to Piazzale Roma is 20 "
              "minutes and \u20ac10.",
    "athens": "Athens (ATH) is 20km east, and metro line 3 to Syntagma is 40 minutes and \u20ac9; "
              "a taxi is \u20ac40.",
    "copenhagen": "Copenhagen (CPH) is 8km south-east, and the metro to Kongens Nytorv is 15 "
                  "minutes for about 30 kroner.",
    "florence": "Florence (FLR) is 5km north-west and small, and the T2 tram to Santa Maria "
                "Novella is 20 minutes for \u20ac1.50; a taxi is about \u20ac25.",
    "seville": "Seville (SVQ) is 10km north-east, and the EA bus to the centre is 35 minutes for "
               "\u20ac4; there is no train link.",
    # The closest question is the common one, so it comes first and names the airport.
    "london": "London City (LCY) is the closest to the centre: about 25 minutes to Bank on the "
              "DLR. London has five, though, and which one suits depends where you are going: "
              "Heathrow (LHR) for most long-haul, Gatwick (LGW) for charters and short-haul, City "
              "itself if you are staying in the east. From Heathrow the Piccadilly line is an "
              "hour and about \u00a35-6.",
    "rome": "Rome has two: Fiumicino (FCO), the main one, 30km south-west, and Ciampino (CIA) "
            "for budget flights, 15km east. From Fiumicino the Leonardo Express is 32 minutes to "
            "Termini for \u20ac14.",
    "lisbon": "Lisbon Humberto Delgado (LIS) is 7km north of the centre, and the red metro line "
              "takes 20 minutes for about \u20ac2 with a Viva card.",
    "porto": "Porto Francisco Sa Carneiro (OPO) is 11km north-west, and the metro line E to the "
             "centre takes about 30 minutes for \u20ac2; a taxi is \u20ac25-30.",
    "paris": "Paris has two: Charles de Gaulle (CDG) for most long-haul, 25km north-east, and "
             "Orly (ORY) to the south for domestic and short-haul. The RER B from CDG is 35 "
             "minutes and about \u20ac11.80.",
    "barcelona": "Barcelona El Prat (BCN) is 12km south-west, and the Aerobus to Plaza Catalunya "
                 "is 35 minutes and about \u20ac7.50.",
    "madrid": "Madrid-Barajas (MAD) is 12km north-east, and the metro line 8 into the centre is "
              "about \u20ac5 and 40 minutes; a taxi is a flat \u20ac33.",
    "amsterdam": "Amsterdam Schiphol (AMS) is 15km south-west, and the train to Centraal is "
                 "15-20 minutes for about \u20ac6.",
    "dublin": "Dublin (DUB) is 10km north, and the Aircoach or the 747 bus to the centre is about "
              "\u20ac7-10 and 30-45 minutes; there is no train link yet.",
    "edinburgh": "Edinburgh (EDI) is 13km west, and the tram or the 100 bus to the centre takes "
                 "about 30 minutes for \u00a36.50.",
    "new york": "New York has three: JFK for most international flights, Newark (EWR) for many "
                "too, and LaGuardia (LGA) for domestic. From JFK the AirTrain plus the subway is "
                "about $10 and 60-75 minutes.",
    "berlin": "Berlin Brandenburg (BER) is 25km south-east, and the FEX or S9 train to "
              "Hauptbahnhof is 30 minutes for about \u20ac4.40.",
    "prague": "Prague Vaclav Havel (PRG) is 15km west, and bus 119 to the metro, or the Airport "
              "Express to the main station, is about \u20ac1.50-2.50.",
    "istanbul": "Istanbul has two: IST on the European side, the main one, and SAW on the Asian "
                "side for budget flights. From IST the metro or the Havaist bus is 40-60 minutes.",
    "milan": "For Milan it is Malpensa (MXP) for long-haul, 50km north-west, or Linate (LIN) for "
             "short-haul, 7km east. The Malpensa Express to the centre is 50 minutes.",
    "dubai": "Dubai International (DXB) is 5km from the centre, and the metro red line reaches "
             "most of the city for a few dirhams.",
    # The cities whose airport people ask about and which had no row: "what airport is near
    # vienna", "which airport do i fly into for tokyo". The name, the distance and the one
    # transfer that matters, in that order, because that is the order the question comes in.
    "vienna": "Vienna (VIE) is 18km south-east, and the S-Bahn S7 to Wien Mitte is 25 minutes "
               "for about \u20ac4.60; the City Airport Train is 16 minutes and \u20ac14.90. A taxi is "
               "a flat \u20ac40.",
    "stockholm": "Stockholm Arlanda (ARN) is 40km north, and the Arlanda Express is 20 minutes "
                 "and about 320 kronor; the commuter train takes 40 minutes and costs less. "
                 "Bromma (BMA) is close to the city but only for domestic flights.",
    "tokyo": "Tokyo has two: Haneda (HND), 20km south and the convenient one, and Narita (NRT), "
             "60km east, which most long-haul flights use. From Haneda the monorail to "
             "Hamamatsucho is 20 minutes for about 500 yen.",
    "brussels": "Brussels (BRU) is 12km north-east, and the train to the central station is 20 "
                "minutes for about \u20ac11. Charleroi (CRL) is the budget airport, 60km south, and "
                "the bus into town takes an hour.",
    "munich": "Munich (MUC) is 38km north-east, and the S-Bahn S1 or S8 to the centre is 40 "
              "minutes for about \u20ac13; a taxi is \u20ac70 or more.",
    "zurich": "Zurich (ZRH) is 12km north, and the train to the main station is 10 to 12 minutes "
              "for about 7 francs, which is the easiest airport transfer in Europe.",
    "oslo": "Oslo Gardermoen (OSL) is 47km north, and the Flytoget is 20 minutes for about 240 "
            "kroner; the Vy regional train is slower and about half the price.",
    "helsinki": "Helsinki-Vantaa (HEL) is 20km north, and the I or P train to the central "
                "station is 30 minutes for about \u20ac4.10.",
    "tallinn": "Tallinn (TLL) is 4km from the centre, so it is a tram or a short taxi rather than "
               "a transfer: tram 4 gets you in for the price of a city ticket.",
    "reykjavik": "Keflavik (KEF) is the airport people mean, 50km south-west, and the Flybus to "
                 "the city is 45 minutes for about 3,500 kroner. Reykjavik (RKV) is a small city "
                 "airport for domestic flights only.",
    "boston": "Boston Logan (BOS) is 6km east, and the Silver Line SL1 bus from the terminals "
              "takes about 20 minutes for a normal subway fare; the water taxi across the harbour "
              "is the fun way in.",
    "san francisco": "San Francisco (SFO) is 21km south, and BART to the city is 30 minutes for "
                     "about $10. Oakland (OAK) is across the bay and often cheaper.",
    "los angeles": "Los Angeles (LAX) is 30km south-west and the one people mean; the FlyAway "
                   "bus to Union Station is about 45 minutes. Hollywood Burbank (BUR) is closer "
                   "for domestic flights.",
    "chicago": "Chicago O'Hare (ORD) is 27km north-west, and the CTA Blue Line runs all night, "
               "45 minutes for $5. Midway (MDW) is nearer the city and on the Orange Line.",
    "toronto": "Toronto Pearson (YYZ) is 27km north-west, and the UP Express to Union station is "
               "25 minutes for about 12 Canadian dollars.",
    "sydney": "Sydney (SYD) is 8km south, and the Airport Link train to Central is 13 minutes "
              "for about 20 Australian dollars; a taxi is 25 to 35.",
    "singapore": "Singapore Changi (SIN) is 20km east, and the MRT to the city is 30 to 40 "
                 "minutes for about S$2. Allow an hour there before your flight: the Jewel "
                 "waterfall is inside the airport.",
    "bangkok": "Bangkok has two: Suvarnabhumi (BKK), the main one 30km east, and Don Mueang "
               "(DMK), 25km north, for budget flights. From Suvarnabhumi the Airport Rail Link "
               "is 30 minutes for 45 baht.",
    "hanoi": "Hanoi (HAN) is 35km north, and bus 86 to the old quarter is 45 minutes for 35,000 "
             "dong; a taxi or a Grab is about 350,000 dong and 40 minutes.",
    "cape town": "Cape Town (CPT) is 20km east, and a taxi or an Uber to the centre is 20 to 30 "
                 "minutes and about 250 rand. There is a train, but not one to take with bags.",
    "mexico city": "Mexico City (MEX) is 13km east, and the metro line 5 is cheap and slow; a taxi "
                   "from the official stand inside the terminal is 30 to 45 minutes and about "
                   "250 pesos.",
    "havana": "Havana (HAV) is 15km south of the city, and a taxi to the old town is 25 to 30 "
              "minutes and about 25 dollars or the same in euros; the airport bus is not worth "
              "the wait.",
    "buenos aires": "Buenos Aires has two: Ezeiza (EZE), 30km south, for long-haul, and "
                    "Aeroparque (AEP) in the city for domestic flights. From Ezeiza a taxi is "
                    "45 minutes and about 30 dollars; bus 8 is the cheap way.",
    "rio de janeiro": "Rio has two: Galeao (GIG), 20km north, for international flights, and "
                      "Santos Dumont (SDU) in the city for the Sao Paulo shuttle. From Galeao a "
                      "taxi is 30 to 50 minutes.",
    "naples": "Naples (NAP) is 6km north-east, and the Alibus to the central station and the "
              "port is 20 minutes for \u20ac5; a taxi is about \u20ac25, and agree the price first.",
    "valencia": "Valencia (VLC) is 9km west, and metro line 3 or 5 to the centre is 20 minutes "
                "for about \u20ac5.",
    "granada": "Granada (GRX) is 17km west and small, and the airport bus to the centre is 40 "
               "minutes for \u20ac3. Most people fly to Malaga instead and take the bus, which is "
               "two hours.",
    "santorini": "Santorini (JTR) is 6km from Fira, and the bus meets the flights; a taxi is 20 "
                 "to 30 euros. It is a small airport with a short runway, so summer flights are "
                 "often delayed.",
    "san sebastian": "San Sebastian (EAS) is 20km east at Hondarribia and has very few flights, "
                     "so most people fly to Bilbao (75 minutes by bus) or Biarritz (40 "
                     "minutes).",
    "ljubljana": "Ljubljana (LJU) is 25km north, and the airport bus to the centre is 30 "
                 "minutes for about \u20ac4; a taxi is \u20ac25 to \u20ac30.",
    "kyoto": "Kyoto has no airport of its own: fly into Osaka Kansai (KIX), which is 75 minutes "
             "away on the Haruka train, or into Tokyo and take the shinkansen.",
    "bath": "Bath has no airport: Bristol (BRS) is 30km west, and the Flyer bus runs to Bath in "
            "55 minutes. By train, come into Bath Spa from Bristol Temple Meads.",
}

# An easy day out from a city, with the travel time: the thing people mean by "what else is
# near here".
DAY_TRIPS = {
    "london": "Bath (80 minutes by train), Oxford and Cambridge (about an hour), and Brighton "
              "(an hour) for the sea. Book the train a week ahead and you halve the fare.",
    "edinburgh": "Glasgow (50 minutes by train from Waverley), Stirling for the castle (50 "
                 "minutes), and North Berwick (35 minutes) for the beach and the boat out to the "
                 "Bass Rock. St Andrews is about 90 minutes by train and bus, and worth the day "
                 "for the ruins and the beach rather than the golf.",
    "paris": "Versailles (40 minutes on the RER C), Chartres for the cathedral, and Giverny for "
              "Monet's garden from April to October. Go early: the first trains are the quietest.",
    "rome": "Ostia Antica for the Roman ruins (30 minutes on the metro and train), Tivoli for the "
             "villa gardens, and Orvieto for the cathedral. Pompeii is two hours each way, so it "
             "is a full day.",
    "lisbon": "Sintra for the palaces (40 minutes by train), Cascais for the beach (40 minutes "
               "on the same line), and Obidos for the walled town (an hour by bus from Lisbon's "
               "Campo Grande, and no train goes there). Buy the train ticket at the machine and "
               "go before 9am.",
    "barcelona": "Montserrat (an hour by train and cable car), Girona (40 minutes) and Sitges "
                  "for the beach (40 minutes). Girona plus Figures makes a good full day.",
    "amsterdam": "Haarlem (15 minutes), Utrecht (25 minutes) and the Zaanse Schans windmills "
                  "(40 minutes). Keukenhof is worth it only in tulip season, mid-March to mid-May.",
    "madrid": "Toledo (30 minutes by train), Segovia (30 minutes) and El Escorial. Toledo and "
               "Segovia both deserve a full day rather than an afternoon.",
    "munich": "Neuschwanstein (two hours by train and bus), Salzburg (90 minutes) and the "
               "Bavarian lakes. Buy a Bayern ticket: it covers the regional trains for a group.",
    "edinburgh": "Glasgow (50 minutes by train), Stirling for the castle, and North Berwick for "
                 "the beach and the seabird centre. The Highlands need a car or a full day tour.",
    "dublin": "Howth for the cliff walk (30 minutes on the DART), Malahide castle, and Glendalough "
               "in the Wicklow mountains, which needs a car or a bus tour.",
    "berlin": "Potsdam for Sanssouci (30 minutes by train) and Sachsenhausen, which is a heavy "
               "half-day and worth it. Both are covered by the Berlin ABC travel card.",
    "tokyo": "Nikko for the shrines and Kamakura for the Buddha (both about two hours), or Hakone "
              "for a view of Fuji if the sky is clear. Go on a weekday: the weekend trains are "
              "packed.",
    "leeds": "York (25 minutes by train), the Yorkshire Dales (an hour by car) and Harrogate for "
              "a spa afternoon. Manchester is 50 minutes by train if you want a city.",
    "florence": "Pisa (an hour by train) for the tower, Siena (90 minutes) for the square, and "
                "Lucca for the walls and the bikes. Fiesole is 30 minutes by bus for the view "
                "back over Florence.",
    "venice": "Verona (an hour by train) for the arena, Padua for the Scrovegni chapel, and the "
              "islands in the lagoon: Murano for glass and Burano for the coloured houses, on a "
              "vaporetto day pass.",
    "naples": "Pompeii and Herculaneum (40 minutes on the Circumvesuviana), the Amalfi coast by "
              "ferry or bus, and Ischia for a slower island day. Vesuvius is a bus and a walk "
              "from Ercolano.",
    "seville": "Cordoba for the mosque-cathedral (45 minutes by train), Ronda for the gorge and "
               "the bridge, and Jerez for the sherry bodegas. Granada is three hours by bus, so "
               "it wants a night.",
    "porto": "The Douro valley by train to Pinhao for the vineyards, Braga and Guimaraes for the "
             "churches and the old town, and Aveiro for the canals. The Douro line is the "
             "scenic one, so sit on the right.",
    "athens": "Cape Sounion for the temple at sunset, Delphi for the ruins (two and a half hours "
              "by bus), and Aegina or Hydra by ferry for an island day. The fast ferries are "
              "worth the extra.",
    "istanbul": "The Princes' Islands by ferry (an hour and a half) where there are no cars, "
                "Bursa for the Ottoman tombs, and the Bosphorus village of Anadolu Kavagi at "
                "the mouth of the Black Sea.",
    "prague": "Kutna Hora for the bone church and the silver mines (an hour by train), Karlstejn "
              "for the castle, and Cesky Krumlov, which is three hours each way so it wants a "
              "night.",
    "vienna": "Bratislava (an hour by train), the Wachau valley by boat for the vineyards and "
              "Durnstein, and Baden for the spa. The Einfach-Raus ticket covers a group on the "
              "regional trains.",
    "brussels": "Bruges (an hour by train) for the canals, Ghent (35 minutes) for the old port, "
                "and Leuven for the university town. Book Bruges ahead in summer, it fills up.",
    "copenhagen": "Roskilde for the cathedral and the Viking ships (25 minutes), Malmo across "
                  "the bridge (35 minutes) for a cheaper lunch, and the Louisiana museum up the "
                  "coast, which is the best half-day of the lot.",
    "stockholm": "The archipelago by ferry from Stromkajen, Uppsala for the cathedral and the "
                 "Vikings (40 minutes by train), and Drottningholm by boat for the palace "
                 "theatre.",
    "split": "Hvar by catamaran (an hour) for the old town and the lavender, Trogir (30 minutes "
             "by bus) for the walled centre, and Krka for the waterfalls, which needs a car or "
             "a tour.",
    "dubrovnik": "Mostar in Bosnia (two and a half hours by bus) for the bridge, Montenegro for "
                 "Kotor and the bay, and the Elaphiti islands by boat. Take your passport for "
                 "Mostar and Montenegro.",
    "ljubljana": "Lake Bled (an hour by bus) for the island church, Postojna for the caves and "
                 "the castle, and Skocjan for the bigger cave, which is the one to pick if you "
                 "only do one.",
    "bath": "Stonehenge (an hour by bus) with a booked slot, Lacock for the village and the "
            "abbey, and Bradford-on-Avon for the canal and the tithe barn, 15 minutes by train.",
    "marrakech": "The Atlas mountains and Ourika valley (an hour by car), Essaouira for the "
                 "seafront and the fish (two and a half hours by bus), and Ait Benhaddou, which "
                 "is a long day or a night on the way to the desert.",
    "bangkok": "Ayutthaya for the ruined temples (an hour and a half by train), Kanchanaburi for "
               "the bridge over the River Kwai, and the floating market at Damnoen Saduak, "
               "which needs a very early start.",
    "hanoi": "Halong Bay for the boats (two and a half hours by bus, and a night on the water "
             "is better than a day), Ninh Binh for the river rowing boats, and Sapa by night "
             "train for the rice terraces.",
    "bristol": "Bath (15 minutes by train), Wells for the cathedral, and the Mendips or the Gower "
                "if you have a car. Cardiff is 50 minutes by train.",
    "manchester": "the Peak District (40 minutes by train to Edale), Liverpool (50 minutes) and "
                   "Chester for the walls and the rows. York is 90 minutes.",
    "glasgow": "Loch Lomond (40 minutes by train), Stirling for the castle, and Edinburgh in an "
                "hour. The islands need a ferry and a full day.",
    "liverpool": "Chester (40 minutes by train), the Wirral coast, and Manchester in under an "
                  "hour. North Wales is a longer day by train.",
    "birmingham": "Stratford-upon-Avon (40 minutes by train), Warwick castle and the Cotswolds by "
                  "car. The Black Country museum is a good wet-day half-day.",
    # The cities with a day-trip question and no row. Every one names the train or bus time,
    # because "how far is it" is the second half of "what should we do for a day".
    "new york": "Beacon for Dia:Beacon (80 minutes on Metro-North), Philadelphia (90 minutes on "
                "Amtrak) and the Hamptons by the LIRR. The Jersey shore is a longer day.",
    "chicago": "Milwaukee (90 minutes on Amtrak), the Indiana Dunes for the beach (an hour by "
               "train and bus) and the Baha'i temple at Wilmette, which is free and half a day "
               "on the Purple line.",
    "san francisco": "Muir Woods and Sausalito (ferry, then a shuttle you book ahead), Napa by "
                     "car, and Santa Cruz over the hill. Yosemite is four hours, so it wants a "
                     "night.",
    "los angeles": "Santa Monica and Malibu down the coast, Disneyland in Anaheim (an hour by "
                   "car) and Catalina island by ferry from Long Beach. Almost all of it needs a "
                   "car.",
    "boston": "Salem for the witch museum (30 minutes by train), Concord and Lexington for the "
              "revolution, and Providence (an hour on Amtrak). Cape Cod is 90 minutes by car.",
    "toronto": "Niagara Falls (two hours by train or bus, and the falls are free), "
               "Niagara-on-the-Lake for the wineries on the same trip, and Stratford for the "
               "Shakespeare festival.",
    "sydney": "The Blue Mountains (two hours by train), the Hunter Valley for wine (three hours, "
              "better on a tour) and Manly or Watsons Bay by ferry for a beach day close in.",
    "singapore": "Johor Bahru across the causeway (the bus queue is long at weekends), Batam by "
                 "ferry, and Malacca, which is three and a half hours each way. The Botanic "
                 "Gardens and the southern ridges are free and in the city.",
    "dubai": "Abu Dhabi for the grand mosque and the Louvre (90 minutes by car or bus), the "
             "desert for a dune drive, and Hatta for the mountains and the kayaks. The Abu Dhabi "
             "bus leaves from Al Ghubaiba.",
    "cape town": "The Cape of Good Hope and the Boulders Beach penguins, which is a full day by "
                 "car, Stellenbosch and Franschhoek for wine (an hour), and Hermanus for whales "
                 "from June to November.",
    "mexico city": "Teotihuacan for the pyramids (an hour by bus from the north terminal), "
                   "Puebla and Cholula (two hours by bus), and Taxco for silver, which is a long "
                   "day.",
    "havana": "Vinales for the tobacco valley (three hours by bus, better with a night), the "
              "beach at Santa Maria del Mar (30 minutes by taxi), and Matanzas for the river and "
              "the poets.",
    "buenos aires": "Tigre for the delta boats (an hour by train), Colonia in Uruguay by ferry "
                    "(an hour, and take your passport), and San Antonio de Areco for the gaucho "
                    "town.",
    "rio de janeiro": "Petropolis for the imperial palace (90 minutes by bus), Niteroi for the "
                      "museum and the beaches across the bay, and Buzios, which is three hours "
                      "and wants a night.",
    "budapest": "Szentendre for the artist town and the Danube bend (40 minutes on the H5 "
                "train), Esztergom for the basilica, and Lake Balaton, which is two hours and "
                "wants a night.",
    "krakow": "Auschwitz-Birkenau (90 minutes by bus, and book a timed entry), the Wieliczka "
              "salt mine (30 minutes by train) and Zakopane for the mountains (two hours). "
              "Auschwitz is a heavy half-day, not a sight.",
    "milan": "Lake Como for Bellagio (an hour by train to Como, then a boat), Bergamo for the "
             "old town (50 minutes) and Turin (an hour on the fast train). The Last Supper needs "
             "booking weeks ahead.",
    "zurich": "Lucerne (45 minutes by train), the Rhine Falls (an hour) and Interlaken for the "
              "mountains (two hours). A travel pass covers the trains and the boats.",
    "oslo": "The fjord by boat from the city hall pier, Drobak for the fortress and the old "
            "town (an hour by bus), and Bergen by train, which is the best rail journey in the "
            "country and wants a night.",
    "helsinki": "Suomenlinna by ferry (15 minutes on the same ticket as the trams), Porvoo for "
                "the wooden old town (an hour by bus) and Tallinn by ferry (two hours, and take "
                "your passport).",
    "tallinn": "Lahemaa national park for the manors and the coast (an hour by bus), Tartu (two "
               "and a half hours) and Helsinki by ferry in two hours.",
    "reykjavik": "The Golden Circle - Thingvellir, Geysir and Gullfoss - is the full day out and "
                 "needs a car or a tour, the Blue Lagoon is 45 minutes by bus and booked ahead, "
                 "and Snaefellsnes is a very long day.",
    "santorini": "Oia for the sunset and Akrotiri for the Minoan town under the ash are the day, "
                 "and both are 20 to 30 minutes by bus from Fira; boats to Thirasia and the "
                 "volcano leave from the old port.",
    "valencia": "The Albufera for the rice fields and the lagoon (30 minutes by bus), Sagunto "
                "for the Roman theatre, and Requena for the wine. The City of Arts is in the "
                "city, not a day out.",
    "granada": "The Alhambra is the day, not a detour: book a timed ticket weeks ahead. The "
               "Alpujarras villages are an hour and a half by bus, and Cordoba is two and a "
               "half hours by train, so it wants a night.",
    "san sebastian": "Bilbao for the Guggenheim (an hour and a quarter by bus), Saint-Jean-de-Luz "
                     "across the French border (40 minutes) and Getaria for the txakoli wine. "
                     "Hondarribia is 25 minutes by bus.",
    "kyoto": "Nara for the deer and the great Buddha (45 minutes by train), Osaka (30 minutes) "
             "and Hikone for the castle on Lake Biwa. Fushimi Inari and Arashiyama are in Kyoto, "
             "so go at dawn instead.",
}

# The day trips are named inside the city's line, so a person who names one reached nothing of
# its own and the city answered instead: at the end of a Lisbon chat "is sintra worth it" gave
# back the Alfama and Belem paragraph word for word, and "how do we get to sintra" gave the
# metro-into-town note. Each name here is taken from the city's own day-trip line, so the answer
# can be the clause about that place and not the whole card again. "bath" is left out because it
# is a city of its own in this file, and a name already claimed is kept with the first city that
# named it.
DAY_TRIP_PLACES = {
    "abu dhabi": "dubai", "ait benhaddou": "marrakech", "akrotiri": "santorini",
    "auschwitz-birkenau": "krakow", "aveiro": "porto", "ayutthaya": "bangkok",
    "baden": "vienna", "beacon": "new york", "bergamo": "milan",
    "bilbao": "san sebastian", "bradford-on-avon": "bath", "braga": "porto",
    "bratislava": "vienna", "brighton": "london", "bruges": "brussels",
    "burano": "venice", "bursa": "istanbul", "buzios": "rio de janeiro",
    "cambridge": "london", "cape sounion": "athens", "cascais": "lisbon",
    "cesky krumlov": "prague", "chartres": "paris", "chester": "manchester",
    "cholula": "mexico city", "concord": "boston", "cordoba": "seville",
    "delphi": "athens", "drobak": "oslo", "durnstein": "vienna",
    "el escorial": "madrid", "essaouira": "marrakech", "esztergom": "budapest",
    "franschhoek": "cape town", "getaria": "san sebastian", "geysir": "reykjavik",
    "ghent": "brussels", "girona": "barcelona", "giverny": "paris",
    "glasgow": "edinburgh", "guimaraes": "porto", "haarlem": "amsterdam",
    "halong bay": "hanoi", "harrogate": "leeds", "hatta": "dubai",
    "herculaneum": "naples", "hermanus": "cape town", "hikone": "kyoto",
    "howth": "dublin", "interlaken": "zurich", "ischia": "naples",
    "jerez": "seville", "kamakura": "tokyo", "kanchanaburi": "bangkok",
    "karlstejn": "prague", "krka": "split", "kutna hora": "prague",
    "lacock": "bath", "lake balaton": "budapest", "lake bled": "ljubljana",
    "lake como": "milan", "leuven": "brussels", "lexington": "boston",
    "liverpool": "manchester", "loch lomond": "glasgow", "lucca": "florence",
    "lucerne": "zurich", "malacca": "singapore", "matanzas": "havana",
    "milwaukee": "chicago", "montenegro": "dubrovnik", "montserrat": "barcelona",
    "muir woods": "san francisco", "nara": "kyoto", "neuschwanstein": "munich",
    "niagara falls": "toronto", "niagara-on-the-lake": "toronto", "nikko": "tokyo",
    "ninh binh": "hanoi", "niteroi": "rio de janeiro", "north berwick": "edinburgh",
    "obidos": "lisbon", "oia": "santorini", "orvieto": "rome",
    "osaka": "kyoto", "ostia antica": "rome", "oxford": "london",
    "padua": "venice", "petropolis": "rio de janeiro", "philadelphia": "new york",
    "pisa": "florence", "pompeii": "naples", "porvoo": "helsinki",
    "postojna": "ljubljana", "potsdam": "berlin", "providence": "boston",
    "puebla": "mexico city", "requena": "valencia", "ronda": "seville",
    "roskilde": "copenhagen", "sachsenhausen": "berlin", "sagunto": "valencia",
    "salem": "boston", "salzburg": "munich", "santa monica": "los angeles",
    "sausalito": "san francisco", "segovia": "madrid", "siena": "florence",
    "sintra": "lisbon", "sitges": "barcelona", "skocjan": "ljubljana",
    "stellenbosch": "cape town", "stirling": "edinburgh", "stonehenge": "bath",
    "stratford": "toronto", "stratford-upon-avon": "birmingham", "szentendre": "budapest",
    "tartu": "tallinn", "taxco": "mexico city", "teotihuacan": "mexico city",
    "the albufera": "valencia", "the blue mountains": "sydney", "tigre": "buenos aires",
    "tivoli": "rome", "toledo": "madrid", "trogir": "split",
    "turin": "milan", "uppsala": "stockholm", "utrecht": "amsterdam",
    "verona": "venice", "versailles": "paris", "vinales": "havana",
    "wells": "bristol", "york": "leeds", "zakopane": "krakow",
}

# A famous site is its own question and it is not "when should I go" or "what is there to do":
# "is it worth visiting pompeii" was getting "That's your call, not mine", which is no answer to
# a person holding a guidebook. One row per site: how long it takes, the one thing that changes
# the day, and what to book. Nothing here says a place is worth it in someone else's taste; it
# says what the visit costs them in time and heat, so they can decide.
SITE_NOTES = {
    "pompeii": "Give Pompeii most of a day: it is 66 hectares and there is no shade, so go at "
               "opening time, take water and wear shoes with grip. Book a timed ticket and the "
               "train from Naples on the Circumvesuviana; the audioguide is worth it and the "
               "walk to the amphitheatre is the quiet half.",
    "herculaneum": "Herculaneum takes two or three hours rather than a day, and the woodwork, "
                   "frescoes and upper floors survived in a way Pompeii's did not, so it is the "
                   "better visit if you have one afternoon. It is the same train line as Pompeii, "
                   "one stop closer to Naples, and the site is small enough to see in one go.",
    "vesuvius": "Vesuvius is a bus up from Ercolano and a steep 20-minute walk from the car park, "
                "with the crater rim roped off. Go on a clear morning, take a jacket because it is "
                "cold and windy at the top, and check the bus times for the way back: the last "
                "one leaves early.",
    "alhambra": "The Alhambra is a half day and the Nasrid palaces need a timed slot booked weeks "
                "ahead, in the morning if you can. Take your passport or ID card: it is checked "
                "against the ticket, and people are turned away without it.",
    "colosseum": "The Colosseum together with the Forum and Palatine is one ticket and most of a "
                 "day, so start early and take water. Book the timed entry and the underground or "
                 "arena add-on if you want them, because they sell out first.",
    "stonehenge": "Stonehenge is two hours at most, and the stones are seen from a path rather "
                  "than walked among. Book a timed slot including the shuttle from the visitor "
                  "centre, and pair it with Avebury or Salisbury if you are driving that far.",
    "eiffel tower": "The Eiffel Tower wants a booked time slot and two to three hours with the "
                    "queues and the lifts, or 45 minutes if you walk up to the second floor. The "
                    "stairs are cheaper and shorter, and the last lift up is around 11pm.",
    "vatican museums": "The Vatican Museums and the Sistine Chapel are three hours at a fast "
                       "walk and half a day at a normal one, so book the first entry of the day. "
                       "Cover your shoulders and knees, and note the chapel is silent with no "
                       "photographs.",
    "sagrada familia": "The Sagrada Familia needs a timed ticket bought online, and an hour and a "
                       "half inside. Add the tower lift if you want it - it is a separate ticket - "
                       "and go in the morning when the east windows are lit.",
    "auschwitz": "Auschwitz-Birkenau is a heavy half day, five or six hours with the bus, and the "
                 "timed entry must be booked ahead. Go with a guide, take tissues, and plan "
                 "something gentle for afterwards.",
}

# People name a visit by the country it sits in or by the chapel inside it: "is the vatican worth
# a whole day" is the Vatican Museums row, and "how long does the sistine chapel take" is the same
# afternoon. The alias points at the row rather than repeating its sentence.
SITE_ALIASES = {
    "vatican": "vatican museums",
    "the vatican": "vatican museums",
    "sistine chapel": "vatican museums",
}

# Getting from one place to another is not a guide to either of them. The pairs below are the
# ones people actually ask, each with the honest fastest way and the cheap way.
ROUTE_BETWEEN = {
    ("naples", "sorrento"): "Naples to Sorrento: the Circumvesuviana train from Napoli Garibaldi "
                            "takes about an hour and costs a few euros, and it is crowded with "
                            "luggage at commuter times. The fast ferry from Molo Beverello is "
                            "35 to 45 minutes and pleasanter, but it runs only in season.",
    ("naples", "amalfi"): "Naples to the Amalfi coast: the season ferry from Molo Beverello to "
                          "Amalfi or Positano is the pretty way and takes 75 minutes; the SITA "
                          "bus from Sorrento or Salerno is cheaper and slower, and the coast road "
                          "is the part that jams in summer. A car is a liability in August.",
    ("sorrento", "amalfi"): "Sorrento to Amalfi: the SITA bus along the coast road is about 90 "
                            "minutes and the ferry is 25, but the ferry runs from spring to "
                            "October only. Sit on the left of the bus going east for the view, "
                            "and buy the ticket before you queue.",
    ("rome", "pompeii"): "Rome to Pompeii: the fast train to Naples takes 70 minutes, then the "
                         "Circumvesuviana to Pompeii Scavi, so about two and a half hours door "
                         "to door and a long day. Herculaneum is the same trip and half the "
                         "walking.",
    ("naples", "pompeii"): "Naples to Pompeii: the Circumvesuviana from Napoli Garibaldi to "
                           "Pompeii Scavi takes 35 to 40 minutes and drops you at the site gate. "
                           "Get off at Pompeii Scavi, not Pompei town, and keep your bag in front "
                           "of you on the train.",
    ("florence", "pisa"): "Florence to Pisa: the regional train from Santa Maria Novella takes "
                          "about an hour and the tower is a 20-minute walk from Pisa Centrale. "
                          "Book the tower climb separately and go early, because the slots are "
                          "timed and the station is far from the airport side.",
    ("london", "paris"): "London to Paris: the Eurostar from St Pancras is two hours twenty to "
                         "the Gare du Nord, city centre to city centre, and the cheapest fares go "
                         "on sale months ahead. Check in 75 to 90 minutes before, and the coach "
                         "is cheaper but a whole day.",
}

# "how do i get to the amalfi coast" names no starting point, so there is nothing to compare:
# the answer is the way in, and it is per place rather than per pair.
GET_TO = {
    "amalfi coast": "Getting to the Amalfi coast: fly to Naples, then the ferry from Molo "
                    "Beverello to Amalfi or Positano in season, or the Circumvesuviana train to "
                    "Sorrento and the SITA bus along the coast. A private transfer is the only "
                    "sensible option with heavy luggage.",
    "cinque terre": "Getting to the Cinque Terre: trains from Pisa or Genoa run to La Spezia, "
                    "then the local line stops at each village. Parking is almost impossible in "
                    "the villages, so leave the car at La Spezia or Levanto.",
    "machu picchu": "Getting to Machu Picchu: fly or bus to Cusco, then the train from Poroy or "
                    "Ollantaytambo to Aguas Calientes, then the bus up. The Inca Trail needs a "
                    "permit booked months ahead with a licensed operator, and entry tickets are "
                    "timed.",
    "great barrier reef": "Getting to the reef: fly to Cairns or Port Douglas and take a day boat "
                          "from the marina, or go out from Airlie Beach in the Whitsundays. Book "
                          "two days ahead, take the seasickness tablets before you board.",
    "isle of skye": "Getting to Skye: drive over the bridge from Kyle of Lochalsh, or take the "
                    "train to Kyle and the bus, or the ferry from Mallaig to Armadale. Book "
                    "accommodation months ahead for summer and expect single-track roads.",
}

# Getting in from the airport and getting around the city are two different questions, and people
# ask the second one far more often than the bot used to admit: "how do i get around paris" was
# answered with the RER from Charles de Gaulle. One row per city, keyed by city, holding the card
# or pass to buy, roughly what a ride costs, and the one thing that changes how they travel.
CITY_TRANSIT = {
    "london": "Tap a contactless card or phone on the bus and the Tube and it charges the cheapest "
              "fare of the day, with a daily cap, so a paper travelcard rarely beats it. Buses are "
              "a flat £1.75 and take no cash.",
    "paris": "Get a Navigo Easy card and load ten tickets: a single is €2.15 and ten is cheaper, "
              "and it covers the Metro inside the city. Keep the ticket until you are out of the "
              "gate, because inspectors fine on the spot.",
    "rome": "A ticket is €1.50 and lasts 100 minutes on the metro and the buses, validated in the "
            "machine on board. There are only two metro lines, so walk the centre and take a bus "
            "for the rest.",
    "milan": "A €2.20 ticket covers 90 minutes of metro, trams and buses, and you can tap a bank "
             "card at the metro gate. The centre is small enough to walk, the metro is for the "
             "outer bits.",
    "florence": "Walk: the historic centre is 20 minutes across and a car is a liability. A bus "
                "ticket is €1.50 for 90 minutes, from a tabacchi or the app rather than the driver.",
    "venice": "The vaporetto is the road here: a single is €9.50 and a 24-hour pass about €25, so "
              "the pass pays off after two rides. Walk between the Rialto and San Marco and take "
              "the boat for the islands.",
    "naples": "A ticket is €1.10 and lasts 90 minutes on the metro, the buses and the funicular, "
              "bought at a tabacchi. Metro line 1 is worth riding for the art in the stations.",
    "barcelona": "A T-casual card is ten rides for about €12.50 but it is one person only: for "
                 "two or more of you the T-familiar is eight rides over 30 days and can be passed "
                 "back over the gate. The metro reaches nearly everything and runs late.",
    "madrid": "A ten-ride Metrobus card is the cheapest way to ride the metro and the buses, about "
              "€1.20 a trip, and the centre is walkable anyway. The metro is fast and air "
              "conditioned.",
    "seville": "Walk: the centre is flat and 20 minutes across. Beyond that a bus ticket is €1.40 "
               "and the tram crosses the old town, and bikes are easy to hire on the cycle lanes.",
    "valencia": "A metro ticket is €1.50 and gets you from the old town to the City of Arts; the "
                "centre itself is walkable and the old river bed is now a park you can walk "
                "through.",
    "granada": "Walk the centre and take a bus up the hill for the Alhambra: a ticket is €1.40 and "
               "the C30 and C32 go from the Plaza Nueva. Taxis are cheap for the station.",
    "san sebastian": "Everything is walkable: the two beaches are 15 minutes apart. A bus ticket "
                     "is about €2 for the ride out to Monte Igueldo, and there is a funicular for "
                     "the view.",
    "lisbon": "Get a Viva Viagem card from the machine and load it: a single is €1.85 and a "
              "24-hour pass €6.80. Tram 28 is beautiful and pickpocketed, so ride it early or "
              "take the metro instead.",
    "porto": "An Andante card covers the metro and the buses at about €1.60 a trip, plus 60 cents "
             "for the card itself. The historic tram is a separate €3.50 and worth doing once.",
    "amsterdam": "Tap in and out with a contactless card or an OV-chipkaart: a trip inside the "
                 "city is about €3.40 and forgetting to tap out costs you. The trams go "
                 "everywhere and the centre is small.",
    "berlin": "A single AB ticket is €3.50 and a 24-hour ticket about €10, so the day ticket wins "
              "after three rides. There are no ticket gates and the inspectors do fine, so "
              "validate before you board.",
    "munich": "A single is €3.90 and a day ticket for the inner zone about €8.60; the U-Bahn and "
              "S-Bahn are the way round and both run late. Validate the ticket before you get on.",
    "prague": "A 30-minute ticket is 30 crowns and a 90-minute one 40, from a machine or the app, "
              "and you stamp it on the first ride. The trams are the best sightseeing in the city.",
    "vienna": "A single is €2.40 and a 48-hour pass about €14, which is what a weekend wants. The "
              "U-Bahn is fast, the Ringstrasse is a 40-minute walk, and you validate the ticket "
              "once.",
    "budapest": "A single is 350 forints and a 24-hour ticket about 2,500, from the machine, "
                "validated before you board. Tram 2 along the Danube is the best ride in the "
                "city and costs the same as any other.",
    "krakow": "The old town and the castle are walkable; a 20-minute bus or tram ticket is 4 "
              "zloty from a machine, and the airport train is separate. The trams are old and "
              "cheap.",
    "istanbul": "Get an Istanbulkart from the machine and top it up: a ride is about 20 lira on "
                "the card and nearly double as a single, and one card covers several people. The "
                "trams and the ferries go where the traffic will not.",
    "athens": "A ticket is €1.20 and lasts 90 minutes on the metro, the trolleybuses and the "
              "trams; the airport line is separate. The centre under the Acropolis is walkable "
              "and the hills are not.",
    "dublin": "A Leap card takes about 30% off, so a bus or tram ride is €2 on it rather than the "
              "cash fare. The centre is 20 minutes across on foot and the DART follows the coast.",
    "edinburgh": "Lothian buses are a flat £2 and you tap a card, with no change given. The old "
                 "town and the new town are 15 minutes apart on foot, and the tram is only worth "
                 "it for the airport.",
    "copenhagen": "Tickets are by zone and a 24-hour city pass is about 90 kroner; a bike is what "
                  "everyone actually uses and most of the centre is a five-minute ride. The "
                  "harbour bus is a cheap boat trip.",
    "stockholm": "A single on the SL is about 39 kronor and a 72-hour pass about 270; the T-bana "
                 "is the way round and the old town is walkable. Tickets are cashless, so buy on "
                 "the app or tap a card.",
    "oslo": "A single on Ruter is about 40 kroner and a 24-hour ticket about 120; the trams and "
            "the metro are clean and the centre is walkable. Buy on the app before boarding.",
    "helsinki": "A ticket inside the city is about €3 and a day ticket €9, and the trams cover "
                "the centre on their own. The ferry to Suomenlinna runs on the same ticket.",
    "reykjavik": "The centre is walkable and a bus ticket is about 630 kronur, needed only for "
                 "the pools and the outer suburbs. Tours collect from stops near the hotels "
                 "rather than the door, so check which stop is yours.",
    "zurich": "Buy by zone on the ZVV app or at a machine: a trip across the city is about 4.30 "
              "francs and there are no barriers. The trams go everywhere and run to the minute.",
    "brussels": "A single on the metro, tram or bus is €2.60 and you tap a bank card at the gate. "
                "The Grand Place is 20 minutes from most of the centre on foot.",
    "new york": "Tap a contactless card or phone on the turnstile: a subway ride is $2.90 whatever "
                "the distance and trains run all night. Take the express where there is one, "
                "because the local stops every block.",
    "chicago": "A Ventra card or a contactless tap is $2.50 a ride on the L and the buses, and "
               "most L lines run all night. The loop is walkable and the L is for everything "
               "outside it.",
    "boston": "A CharlieCard is $2.40 a ride on the T and contactless works at the gates too. The "
              "subway covers the centre and the Freedom Trail is a walk between the stops.",
    "san francisco": "Tap a Clipper card or a phone on Muni: $2.50 buys 90 minutes on the buses "
                     "and the metro. BART is a separate fare for the airport, and the hills are "
                     "real, so take the cable car once.",
    "los angeles": "A TAP card is $1.75 a ride and a day caps at about $5, and the metro is fine "
                   "for Hollywood and Santa Monica. The traffic is the reason to plan, so stay "
                   "near where you are going.",
    "toronto": "A PRESTO tap is about $3.30 for two hours of streetcars, buses and subway. The "
               "centre is walkable and the PATH tunnels keep you out of the weather.",
    "mexico city": "The metro is 5 pesos a ride on a card from the machine, fast and very "
                   "crowded at rush hour. Uber is cheap and easier at night, and the pink line "
                   "covers most of the centre.",
    "tokyo": "Get a Suica or Pasmo card, or add one to your phone: a metro ride is about 180 yen "
             "and the machines take cash. Trains stop around midnight, so plan the last one.",
    "kyoto": "Buses are a flat 230 yen and the subway is only two lines, so the bus does the "
             "temples. Tap an IC card, and walk the Gion and Higashiyama side rather than ride.",
    "osaka": "An ICOCA card or a phone covers the metro and the private lines, about 190 yen a "
             "ride. The loop line gets you round the centre and Dotonbori is walkable.",
    "seoul": "A T-money card is about 1,400 won a ride and works on the metro, the buses and in "
             "taxis. The metro is cheap, clean, signed in English and the fastest way across the "
             "city.",
    "bangkok": "Get a Rabbit card for the BTS Skytrain: a ride is 17 to 45 baht and it goes over "
               "the traffic rather than through it. The metro is a separate ticket, and the river "
               "boats are the cheapest way along the Chao Phraya.",
    "singapore": "Tap a contactless card on the MRT and the buses: a trip is about S$2 and the "
                 "system is spotless. It stops around midnight, and a taxi or Grab after that.",
    "hong kong": "Get an Octopus card: it pays for the MTR, buses, ferries and shops, and a ride "
                 "is about HK$10 to 20. The MTR is the fastest way anywhere and the Star Ferry is "
                 "the cheapest sightseeing.",
    "sydney": "Tap on and off with a bank card or an Opal: a city trip is about A$4, and the "
              "train from the airport is a separate A$19. The ferries are the best value "
              "sightseeing in the city.",
    "melbourne": "A myki card or a contactless card covers trams, trains and buses at about A$5 "
                 "for two hours, and the tram zone in the centre is free. Trams run through the "
                 "night at weekends.",
    "dubai": "A Nol card covers the metro and the buses, and a ride is about 3 to 7.5 dirham. "
             "The metro is driverless and clean and goes to the malls; taxis are cheap by "
             "European standards.",
    "cape town": "There is no useful metro for visitors: use Uber or a MyCiTi bus, which is "
                 "about 8 rand a trip on a card, and hire a car for the Winelands and the Cape. "
                 "Agree the fare before you get in a taxi.",
    "vancouver": "A Compass card or a contactless tap covers the SkyTrain, the buses and the "
                 "SeaBus, and a trip inside the city is about C$3.15. The SkyTrain from the "
                 "airport costs a few dollars more, and the centre is walkable.",
    "marrakech": "Small taxis are the way round: 20 to 30 dirham inside the city, agreed before "
                 "you get in. The medina is walkable and a guide the first day is money well "
                 "spent.",
}

# A rough daily cost per person in pounds, room excluded, so "is X enough for a week" can be
# answered with arithmetic rather than an opinion. (low, high, what moves the number)
DAILY_BUDGET = {
    "spain": (45, 80, "eating at the bar and using trains rather than taxis is the difference"),
    "portugal": (40, 75, "the north is cheaper than the Algarve, and lunch is half the price of "
                          "dinner"),
    "italy": (55, 95, "coffee standing at the bar and one big meal at lunch keeps it down"),
    "greece": (45, 80, "the islands cost more than the mainland, mostly because of the ferries"),
    "france": (65, 110, "Paris is the top of that range; anywhere else is nearer the bottom"),
    "croatia": (50, 90, "July and August roughly double the accommodation, not the food"),
    "turkey": (30, 60, "the lira works in your favour if you change money there, not at home"),
    "japan": (60, 110, "the rail pass is a big fixed cost on top of these daily numbers"),
    "thailand": (30, 60, "street food and local buses keep it at the bottom of that range"),
    "dubai": (70, 130, "alcohol is the thing that pushes it up, and it is only sold in hotels"),
    "new york": (90, 160, "the city tax and the tip on every bill are what people forget"),
    "iceland": (90, 150, "petrol and eating out; the supermarkets are the way to keep food down"),
    "morocco": (30, 55, "a riad is cheap for what it is, and eating where locals do is cheaper"),
    "mexico": (30, 60, "the peso goes far outside the resort areas"),
    "australia": (70, 120, "it is a long way from anywhere, so food and fuel both cost more"),
    "lisbon": (45, 80, "eating at the bar and using the metro rather than taxis is the difference"),
    "porto": (40, 70, "it is cheaper than Lisbon and the portions are bigger"),
    "rome": (55, 95, "coffee standing at the bar and one big meal at lunch keeps it down"),
    "venice": (70, 120, "the water buses add up, so buy a multi-day pass once you are there"),
    "florence": (55, 95, "stay outside the centre and walk in: the hotels halve in price"),
    "paris": (65, 110, "lunch from a bakery and the metro rather than taxis is the difference"),
    "barcelona": (50, 85, "the menu del dia at lunch is half the price of the same meal at night"),
    "madrid": (45, 80, "tapas at the bar with a drink is cheaper than a sit-down dinner"),
    "amsterdam": (60, 100, "hire a bike rather than trams, and eat away from the canal belt"),
    "prague": (35, 65, "eat and drink away from the old town square and it halves"),
    "berlin": (50, 85, "it is cheaper than the rest of western Europe, especially eating out"),
    "edinburgh": (55, 90, "August doubles the hotel prices because of the festival"),
    "dublin": (60, 100, "the hotels are the expensive part, so book early"),
    "tokyo": (70, 120, "convenience store breakfast and a rail pass change the total completely"),
    "london": (65, 110, "the tube and eating away from the centre is what keeps it down"),
    "new york": (90, 160, "the city tax and the tip on every bill are what people forget"),
    # The country row answered "is croatia expensive" and left "is dubrovnik expensive" with
    # nothing: the day rate is per place, and people name the place they are going to. Cities
    # whose country is already above are given here for the same reason.
    "dubrovnik": (55, 95, "the old town is the top of that range and the walls are paid for"),
    "split": (40, 75, "it is the ferry port as much as a city, so eating inland costs less"),
    "athens": (40, 75, "the ruins are the cost here, not the food: lunch in a taverna is cheap"),
    "krakow": (30, 60, "the old town is the pricey part and the tram takes you out of it"),
    "budapest": (30, 60, "the baths and the ruin bars are where the money goes"),
    "seville": (45, 80, "tapas at the bar is the whole trick, and it is what locals do"),
    "valencia": (45, 80, "the beach is free and it is cheaper than Barcelona for the same food"),
    "vienna": (55, 95, "coffee and cake add up, and the transport pass is worth it"),
    "zurich": (95, 160, "everything is dear, so a supermarket lunch and the lake save the most"),
    "brussels": (55, 90, "the centre near the Grand Place is where the prices double"),
    "copenhagen": (70, 120, "bikes rather than taxis, and lunch from a bakery rather than a cafe"),
    "stockholm": (65, 110, "alcohol is the shock: eat and drink where people live, not in Gamla Stan"),
    "istanbul": (30, 60, "the tourist quarter is the dear part, and the ferries are cheap"),
    "bangkok": (25, 55, "street food is a few pounds a meal, and the skytrain beats the traffic"),
    "singapore": (60, 110, "hawker centres keep food cheap and hotels are what pushes it up"),
    "cape town": (35, 70, "the rand helps, and the wine is cheaper than the food"),
    "sydney": (70, 120, "coffee and transport are dear, and the beaches cost nothing"),
    "san francisco": (90, 160, "the hotel tax and the tip are the parts people forget"),
    "orlando": (70, 130, "the park tickets are the cost, not the meals"),
    "marrakesh": (25, 55, "haggling in the souk is expected, and a riad is cheap for what it is"),
}

TRIP_UNITS = (("weekend", 2), ("long weekend", 3), ("a week", 7), ("one week", 7),
              ("two weeks", 14), ("fortnight", 14), ("a month", 30), ("four nights", 4),
              ("three nights", 3), ("two nights", 2), ("five nights", 5))


# --- the practical questions every trip brings ------------------------------------------
# "How long should I stay in Rome" is a number, and the number is per city: a table, because the
# same question is asked about every city in CITIES and a sentence of advice fits them all.
CITY_DAYS = {
    "amsterdam": 2, "athens": 2, "bangkok": 3, "barcelona": 3, "bath": 1, "berlin": 3,
    "boston": 2, "brussels": 2, "budapest": 2, "buenos aires": 3, "cape town": 4, "chicago": 2,
    "copenhagen": 2, "dubai": 3, "dublin": 2, "dubrovnik": 2, "edinburgh": 2, "florence": 2,
    "granada": 2, "hanoi": 3, "havana": 2, "helsinki": 2, "istanbul": 3, "krakow": 2,
    "kyoto": 3, "lisbon": 3, "ljubljana": 1, "london": 4, "los angeles": 3, "madrid": 3,
    "marrakech": 2, "mexico city": 3, "milan": 2, "munich": 2, "naples": 2, "new york": 4,
    "oslo": 2, "paris": 4, "porto": 2, "prague": 3, "reykjavik": 3, "rio de janeiro": 3,
    "rome": 3, "san francisco": 2, "san sebastian": 2, "santorini": 2, "seville": 2,
    "singapore": 3, "stockholm": 2, "sydney": 3, "tallinn": 1, "tokyo": 4, "toronto": 2,
    "valencia": 2, "venice": 2, "vienna": 3, "zurich": 2,
}

# The sockets, by the place people name: the letter on the plug, the shape of the pins, and the
# one thing that surprises people about the supply. One table, so "do i need an adapter in japan"
# and the same question about thirty countries are one fact each rather than a shrug.
_PLUG_GROUPS = (
    (("G", "three square pins", ""),
     ("uk", "england", "scotland", "wales", "ireland", "malta", "cyprus", "singapore",
      "hong kong", "malaysia", "uae", "dubai", "saudi arabia", "qatar", "kuwait", "bahrain",
      "kenya", "nigeria", "ghana")),
    (("C and E", "two round pins", ""),
     ("france", "germany", "spain", "portugal", "greece", "netherlands", "belgium", "austria",
      "poland", "czechia", "hungary", "croatia", "slovenia", "slovakia", "romania", "bulgaria",
      "estonia", "latvia", "lithuania", "luxembourg", "turkey", "morocco", "tunisia", "egypt",
      "iceland", "norway", "sweden", "finland", "russia", "south korea", "indonesia",
      "vietnam", "thailand", "cambodia", "nepal")),
    (("C and J", "two round pins, with a third offset one in some sockets", ""),
     ("switzerland",)),
    (("C and K", "two round pins, with a third one in some sockets", ""), ("denmark",)),
    (("C, F and L", "two round pins, and the old three-in-a-row socket", ""), ("italy",)),
    (("C and H", "two round pins, with a third one in some sockets", ""), ("israel",)),
    (("A and B", "two flat pins", ""),
     ("usa", "america", "the states", "canada", "taiwan", "philippines")),
    (("A and B", "two flat pins", "The supply is 100 volts, half of ours, so check anything with "
     "a motor or a heating element."), ("japan",)),
    (("A and B", "two flat pins", "The supply is 127 volts, so check anything with a motor."),
     ("mexico",)),
    (("I", "two slanted flat pins", ""),
     ("australia", "new zealand", "argentina", "fiji", "china")),
    (("C, D and M", "three fat round pins", ""),
     ("india", "south africa", "sri lanka", "bangladesh", "pakistan")),
    (("C and N", "two round pins", ""), ("brazil",)),
)
PLUG_TYPES = {place: plug for plug, places in _PLUG_GROUPS for place in places}

# Where the tap water is fine and where it is not. Only the places people ask about, and only
# where the answer is stable: anywhere else gets the general rule rather than a guess.
WATER_OK = ("uk", "england", "scotland", "wales", "ireland", "france", "spain", "portugal",
            "italy", "germany", "austria", "switzerland", "netherlands", "belgium", "denmark",
            "sweden", "norway", "finland", "iceland", "greece", "croatia", "slovenia", "poland",
            "czechia", "malta", "cyprus", "usa", "america", "the states", "canada", "australia",
            "new zealand", "japan", "south korea", "singapore", "uae", "chile",
            "argentina", "south africa", "israel", "hungary", "slovakia", "estonia", "latvia",
            "lithuania", "bulgaria", "romania")
WATER_NO = ("mexico", "india", "nepal", "bangladesh", "pakistan", "sri lanka", "thailand",
            "vietnam", "cambodia", "laos", "indonesia", "philippines", "malaysia", "china",
            "egypt", "morocco", "tunisia", "turkey", "kenya", "nigeria", "ghana", "tanzania",
            "zanzibar", "peru", "bolivia", "colombia", "brazil", "cuba", "jamaica",
            "dominican republic", "hanoi", "bangkok", "marrakech", "mexico city", "istanbul",
            "dubai")
WATER = {place: True for place in WATER_OK}
WATER.update({place: False for place in WATER_NO})

# The answer when no place is named: the same rule the entry gave before it had a table.
TAP_WATER_HOME = (
    "Tap water from the mains is safe to drink without boiling it, and it is tested far more "
    "often than anything in a bottle: in the UK the results are published by the water company, "
    "and bottled water is not held to a higher standard. Run the cold tap for half a minute "
    "first, because water that has sat in the pipes overnight picks up the taste of them, and "
    "fill a bottle from the cold tap to carry round. Only a notice from your water company to "
    "boil it means boiling.")
# The colour complaint and the taste complaint are the same tap but not the same first step, so
# each leads with its own cause instead of the answer opening on the other one's sentence.
TAP_WATER_HOME_BROWN = (
    "Brown or yellow water is usually a burst main nearby, or rust shaken out of old iron pipes: "
    "run the cold tap for two minutes, and ring your water company if it does not clear, because "
    "they flush the main for free. If your house is old, ask them whether the supply pipe is "
    "lead, and never drink from the hot tap.")
TAP_WATER_HOME_TASTE = (
    "A taste or smell of chlorine is the disinfectant that keeps the water safe, and it fades if "
    "you let a jug stand in the fridge for an hour. A metallic taste is usually old pipes, so run "
    "the cold tap for a minute first, ask your water company whether the supply pipe is lead, and "
    "never drink from the hot tap.")
TAP_WATER_GENERAL = (
    "Tap water is fine in most of southern Europe and in Australia; in Mexico, most of "
    "Africa, India and much of South-East Asia it is not, so drink bottled or filtered "
    "water and skip ice from street stalls. Use bottled water for brushing your teeth if "
    "you are unsure, and eat fruit you peel yourself for the first few days.")


# Which way the clock moves tells you which way to shift your sleep, and people say where they
# are going rather than "east": "i get terrible jet lag going to asia" was a shrug because the
# entry only knew the word east. From the UK the long-haul destinations split cleanly.
JET_EAST = ("asia", "japan", "china", "hong kong", "singapore", "thailand", "vietnam", "bali",
            "indonesia", "malaysia", "korea", "seoul", "tokyo", "beijing", "shanghai", "dubai",
            "india", "delhi", "mumbai", "sri lanka", "maldives", "australia", "sydney",
            "melbourne", "new zealand", "auckland", "fiji", "south africa", "cape town")
JET_WEST = ("america", "the states", "usa", "us", "canada", "new york", "boston", "chicago",
            "florida", "miami", "california", "los angeles", "san francisco", "seattle",
            "hawaii", "mexico", "cuba", "brazil", "rio", "argentina", "buenos aires", "peru",
            "chile", "colombia", "iceland", "reykjavik")

# The words the two entries key on, so a test can check the sets stay apart.
JET_EAST_KEYS = ("east", "eastwards", "forward", "ahead") + JET_EAST
JET_WEST_KEYS = ("west", "westwards", "back") + JET_WEST

# Hours ahead of the UK in winter and in summer, so the answer holds whichever side of the clock
# change it is asked. Places that do not keep daylight saving show a different pair: Dubai is
# four hours ahead in winter and three in summer, Sydney eleven and nine.
TIME_ZONES = {
    "london": (0, 0), "dublin": (0, 0), "edinburgh": (0, 0), "lisbon": (0, 0), "reykjavik": (0, 0),
    "marrakech": (0, 0), "paris": (1, 1), "berlin": (1, 1), "madrid": (1, 1), "rome": (1, 1),
    "amsterdam": (1, 1), "brussels": (1, 1), "vienna": (1, 1), "prague": (1, 1),
    "copenhagen": (1, 1), "stockholm": (1, 1), "oslo": (1, 1), "zurich": (1, 1), "lagos": (1, 1),
    "tunis": (1, 1), "athens": (2, 2), "helsinki": (2, 2), "cairo": (2, 2), "cape town": (2, 2),
    "tel aviv": (2, 2), "amman": (2, 2), "istanbul": (3, 3), "moscow": (3, 3), "nairobi": (3, 3),
    "qatar": (3, 3), "dubai": (4, 3), "abu dhabi": (4, 3), "delhi": (5.5, 4.5),
    "mumbai": (5.5, 4.5), "sri lanka": (5.5, 4.5), "bangkok": (7, 6), "hanoi": (7, 6),
    "singapore": (8, 7), "hong kong": (8, 7), "beijing": (8, 7), "shanghai": (8, 7),
    "bali": (8, 7), "kuala lumpur": (8, 7), "perth": (8, 7), "tokyo": (9, 8), "seoul": (9, 8),
    "sydney": (11, 9), "melbourne": (11, 9), "fiji": (12, 11), "auckland": (13, 11),
    "new york": (-5, -5), "boston": (-5, -5), "toronto": (-5, -5), "miami": (-5, -5),
    "havana": (-5, -5), "bogota": (-5, -5), "lima": (-5, -5), "chicago": (-6, -6),
    "mexico city": (-6, -6), "los angeles": (-8, -8), "san francisco": (-8, -8),
    "seattle": (-8, -8), "vancouver": (-8, -8), "honolulu": (-10, -10), "rio": (-3, -4),
    "sao paulo": (-3, -4), "buenos aires": (-3, -3), "santiago": (-4, -4),
    # Countries that keep one clock. The multi-zone ones (below) get their own answer, because
    # "what time is it in australia" has three right answers.
    "uk": (0, 0), "the uk": (0, 0), "britain": (0, 0), "england": (0, 0), "scotland": (0, 0),
    "wales": (0, 0), "ireland": (0, 0), "portugal": (0, 0), "morocco": (0, 0), "iceland": (0, 0),
    "france": (1, 1), "germany": (1, 1), "italy": (1, 1), "spain": (1, 1), "holland": (1, 1),
    "netherlands": (1, 1), "belgium": (1, 1), "austria": (1, 1), "switzerland": (1, 1),
    "czech republic": (1, 1), "czechia": (1, 1), "denmark": (1, 1), "sweden": (1, 1),
    "norway": (1, 1), "croatia": (1, 1), "poland": (1, 1), "hungary": (1, 1), "nigeria": (1, 1),
    "finland": (2, 2), "greece": (2, 2), "egypt": (2, 2), "israel": (2, 2), "jordan": (2, 2),
    "turkey": (3, 3), "kenya": (3, 3), "qatar": (3, 3), "uae": (4, 3), "oman": (4, 3),
    "india": (5.5, 4.5), "thailand": (7, 6), "vietnam": (7, 6), "china": (8, 7),
    "singapore": (8, 7), "malaysia": (8, 7), "indonesia": (8, 7), "japan": (9, 8),
    "south korea": (9, 8), "new zealand": (13, 11), "fiji": (12, 11), "mexico": (-6, -6),
    "cuba": (-5, -5), "peru": (-5, -5), "colombia": (-5, -5), "chile": (-4, -4),
    "argentina": (-3, -3), "florida": (-5, -5), "california": (-8, -8), "texas": (-6, -6),
}

# Countries with more than one clock: the answer names the zones that matter instead of guessing.
MULTI_ZONES = {
    "australia": ("Sydney and Melbourne are eleven hours ahead of the UK in winter and nine in "
                  "summer, Perth eight and seven, so it depends where you land"),
    "america": ("New York is five hours behind the UK, Chicago six, Los Angeles and San Francisco "
                "eight, so it depends which side you are on"),
    "usa": ("New York is five hours behind the UK, Chicago six, Los Angeles and San Francisco "
            "eight, so it depends which side you are on"),
    "canada": ("Toronto is five hours behind the UK and Vancouver eight, so it depends which end"),
    "brazil": ("Rio and Sao Paulo are three hours behind the UK in winter and four in summer"),
    "russia": ("Moscow is three hours ahead of the UK all year; the far east runs to nine"),
}


_TIME_ZONE_SHAPE = ("time difference", "time zone", "whats the time", "what time is it",
                    "what is the time", "the time in", "local time", "hours ahead", "hours behind",
                    "ahead of us", "behind us", "how many hours ahead", "clock in")

# Where to stay: one row per city, three areas and what each is good for. The question is asked
# in a dozen shapes ("best area to stay in paris", "where should we stay in rome", "which
# neighbourhood is good in lisbon"), so it is keyed on the city and on the asking words, and the
# row is the answer.
CITY_AREA = {
    "rome": ("Monti for the Colosseum on foot and quiet nights, Trastevere for restaurants and "
             "cobbles, or Prati for the Vatican and a calmer evening"),
    "paris": ("Le Marais for the centre and cafes, Saint-Germain for the classic postcard, or "
              "Canal Saint-Martin for cheaper nights and a younger crowd"),
    "london": ("Bloomsbury to walk to most of it, the South Bank for the river and theatres, or "
               "Shoreditch for bars and a late night"),
    "barcelona": ("the Eixample for a grid that is easy to walk and safe at night, Gracia for a "
                  "village feel, or El Born for tapas and narrow streets"),
    "madrid": ("La Latina for tapas on the doorstep, Malasana for going out, or Salamanca for "
               "somewhere smart and quiet"),
    "lisbon": ("Alfama for the old streets and the views but steep and noisy, Baixa and Chiado to "
               "be in the middle of it, or Principe Real for quiet and smart"),
    "amsterdam": ("the Jordaan for canals and quiet, De Pijp for the food market and locals, or "
                  "the centre if you want everything on foot and do not mind noise"),
    "berlin": ("Mitte for the centre and the museums, Kreuzberg for nightlife and grit, or "
               "Prenzlauer Berg for cafes and families"),
    "vienna": ("the Innere Stadt to walk to the palaces and concerts, Leopoldstadt for the Prater "
               "and cheaper rooms, or Neubau for small shops and cafes"),
    "prague": ("Vinohrady for leafy streets and local restaurants, Mala Strana for quiet and "
               "pretty, or the Old Town for the middle of it and the noise"),
    "budapest": ("District V for the centre, District VII for the ruin bars and the noise, or the "
                 "Buda side for quiet and the views"),
    "copenhagen": ("Norrebro for food and a local feel, Vesterbro for bars near the meatpacking "
                   "district, or Indre By to be in the middle"),
    "stockholm": ("Sodermalm for bars and views, Gamla Stan for the postcard and the crowds, or "
                  "Ostermalm for somewhere smarter"),
    "oslo": ("Grunerlokka for cafes and the river, the centre for the harbour and the station, or "
             "Majorstuen for quiet"),
    "helsinki": ("Kallio for bars and cheaper rooms, the Design District for the centre on foot, "
                 "or Kamppi for the transport hub"),
    "dublin": ("Portobello for quiet and locals, St Stephen's Green to be central, or Temple Bar "
               "for the pubs and the noise that comes with them"),
    "edinburgh": ("the New Town for Georgian calm and everything on foot, the Old Town for the "
                  "Royal Mile and tourists, or Leith for the food"),
    "venice": ("Cannaregio for local life and canals, Dorsoduro for art and quiet, or San Marco "
               "for the middle of it and the day trippers"),
    "florence": ("Santa Croce for the centre and a lively square, Oltrarno for artisans and "
                 "quiet, or around Santa Maria Novella for the station"),
    "naples": ("Chiaia for the seafront and somewhere smart, the Centro Storico for food and "
               "chaos, or Vomero for the hill and a calm night"),
    "milan": ("Brera for chic and central, the Navigli for canals and nightlife, or Porta Romana "
              "for quieter streets"),
    "athens": ("Koukaki for the museum and local tavernas, Plaka for under the Acropolis, or "
               "Exarchia if you want the edgier side"),
    "istanbul": ("Sultanahmet for the sights on foot and quiet nights, Beyoglu for going out, or "
                 "Kadikoy on the Asian side for food and locals"),
    "marrakech": ("a riad inside the medina for the atmosphere, Gueliz for modern hotels and "
                  "quiet, or the Kasbah for the sights"),
    "seville": ("Santa Cruz for narrow streets and the Alcazar, Triana for ceramics and locals, "
                "or the Alameda for bars"),
    "porto": ("Ribeira for the river and the crowds, Cedofeita for shops and cafes, or Bonfim for "
              "local streets and cheaper rooms"),
    "new york": ("Midtown for the sights and the noise, the Lower East Side for food and bars, or "
                 "Brooklyn for cheaper rooms and 20 minutes on the train"),
    "san francisco": ("the Mission for food and the sun, North Beach for Italian and the wharf, "
                      "or SoMa for the middle of it"),
    "los angeles": ("Santa Monica for the beach, Hollywood for the sights and grit, or Downtown "
                    "for the arts and the bars"),
    "chicago": ("River North to walk to the lake and the galleries, Wicker Park for bars, or the "
                "Loop for the trains"),
    "tokyo": ("Shinjuku for the transport and the nightlife, Asakusa for the old town and quiet, "
              "or Shibuya if you want to be in the middle of it"),
    "kyoto": ("Kawaramachi for the centre and dinner, Gion for the old streets, or Arashiyama for "
              "quiet and the bamboo"),
    "singapore": ("Chinatown for food and value, Marina Bay for the sights, or Orchard for "
                  "shopping"),
    "bangkok": ("Sukhumvit for hotels and food, the riverside for views and boats, or Khao San for "
                "the backpacker end"),
    "sydney": ("Surry Hills for cafes and bars, Circular Quay for the harbour on the doorstep, or "
               "Bondi for the beach"),
    "dubai": ("Dubai Marina for the beach and towers, Downtown for the Burj and the malls, or "
              "Deira for the souks and lower prices"),
    "reykjavik": ("101 downtown to walk to everything, or Laugavegur for the shops and bars and a "
                  "short walk to the harbour"),
    "mexico city": ("Roma and Condesa for leafy streets and cafes, Centro for the sights, or "
                    "Coyoacan for quiet"),
    "toronto": ("King West for bars and the centre, Kensington Market for food and a local feel, "
                "or the Distillery District for cobbles"),
    "boston": ("Back Bay for the shopping and the river, Beacon Hill for the postcard streets, or "
               "the North End for Italian food"),

    "bath": ("the centre by the Abbey to walk to the baths and the shops, or the Royal Crescent "
             "end for Georgian streets and quiet"),
    "ljubljana": ("the old town by the river for cafes and everything on foot, or Tivoli park "
                  "side for green and quiet"),
    "krakow": ("the Old Town for the square and the sights on foot, or Kazimierz for bars, food "
               "and a local feel"),
    "munich": ("the Altstadt for the beer halls and the sights, Schwabing for a student feel and "
               "the English Garden, or near the station for day trips"),
    "zurich": ("the Niederdorf for the old town on foot, or the west side near the river for "
               "bars and cheaper rooms"),
    "tallinn": ("the old town for the walls and the square, or Kalamaja for wooden houses and "
                "cafes and a short walk in"),
    "dubrovnik": ("inside the walls for the postcard and the noise, or Lapad and Babin Kuk for "
                  "beaches and calmer nights and a bus into town"),
    "santorini": ("Imerovigli or Pyrgos for the view without the crowds, or Oia for the sunset "
                  "and the people who come to see it"),
    "valencia": ("the Carmen for the old town and bars, or the beach end for sand and the tram"),
    "granada": ("the Albaicin for the views and the old streets, or the centre near the cathedral "
                "for tapas on the doorstep"),
    "san sebastian": ("the old town for pintxos on the doorstep, or Gros for the surf beach and "
                      "quieter nights"),
    "cape town": ("the city bowl for the restaurants and the mountain, Camps Bay for the beach, "
                  "or Stellenbosch if you want the wine farms"),
    "havana": ("Habana Vieja for the old streets on foot, or Vedado for 1950s hotels and a local "
               "evening"),
    "buenos aires": ("Palermo for restaurants and going out, Recoleta for the grand streets, or "
                     "San Telmo for the old quarter"),
    "rio de janeiro": ("Ipanema for the beach and the bars, or Santa Teresa for the old streets "
                       "on the hill"),
    "hanoi": ("the old quarter for the street food and the lake on foot, or the French quarter "
              "for quieter nights"),
}

# The same question said by the thing rather than the frame: "and a hotel?" after "we're going to
# lisbon in june" is where to stay there, and so is "accommodation" or "somewhere to stay". The
# article is part of the phrase on purpose - a bare "hotel" is a word of a dozen other entries
# (wifi sign-in, a hotel break, a hotel bill), and only the asking shape belongs here.
WHERE_TO_STAY = ("where should i stay", "where shall i stay", "where do i stay", "where to stay",
                 "where should we stay", "best area to stay", "area to stay", "which area",
                 "what area", "where is good to stay", "best place to stay", "good area",
                 "neighbourhood", "neighborhood", "part of town", "which part",
                 "a hotel", "a hostel", "somewhere to stay", "a place to stay",
                 "accommodation", "places to stay", "hotels to stay", "a bed for the night",
                 # "where should i sleep" and "where can i sleep" ask the same thing with the
                 # older word for it, and both reached nothing at all.
                 "where should i sleep", "where can i sleep", "where do i sleep",
                 "where should we sleep", "where shall we sleep", "where should i kip",
                 "somewhere to sleep", "a place to sleep",
                 # "where do we stay" is the same ask with the other helper, and it reached the
                 # card for an evening at home because "we stay in <town>" holds "stay in".
                 "where do we stay", "where can we stay", "where can i stay",
                 "where could i stay", "where should i stay the night",
                 # "what area should i stay in" says the stay as "stay in", which is also the
                 # phrase for an evening at home, so the area is what makes it the booking.
                 "area should i stay", "area to stay in", "area do i stay")

# A place whose name is also an everyday word: "bath" and "split". A bare match on one of these
# answers a question nobody asked ("whats the best time to take a bath" got the Roman baths, and
# "the best time to split firewood" got a ferry to Hvar), so the word only counts as a place in a
# travel shape: "go to Bath", "in Split", "visit Bath", "a trip to Bath".
# "cork" is a city and the stuff in a bottle and on a noticeboard, so it is a place only when the
# line says so ("whats cork like", "the train to cork", "cork is worth visiting") - the same test
# bath and split get.
AMBIGUOUS_PLACES = ("bath", "split", "cork")
_PLACE_SHAPE = (r"\b(?:go|goes|going|went|get|getting|travel|travelling|traveling|trip|holiday|"
                r"visit|visiting|stay|staying|fly|flying|from|in|near|see|seeing)\s+(?:to\s+)?%s\b")


# "Is Bath worth a day trip" and "is Bath worth visiting" are the commonest way a person asks
# about a place whose name is also an everyday word, and neither has a travel verb in it: the
# verdict question comes first and the place is named inside it. On its own _PLACE_SHAPE answered
# "is bath worth visiting" with a hedge while "what is there to do in bath" found the guide.
def _worth_a_visit(text, name):
    """True when the line asks whether the place is worth the journey, naming it as a place."""
    name = re.escape(name)
    return re.search(r"(?<![a-z])" + name + r"\s+(?:is\s+)?worth"
                     r"|\bis\s+" + name + r"\s+worth"
                     r"|\bworth\s+(?:visiting|seeing|going to)\s+" + name + r"\b", text) is not None


def _names_place(text, name):
    """True when the word is being used as a place and not as the everyday word it shares."""
    if name not in AMBIGUOUS_PLACES:
        return True
    if re.search(_PLACE_SHAPE % re.escape(name), text) is not None:
        return True
    return _worth_a_visit(text, name)


def _find_in(text, table):
    """The key of table the line names, longest first, or None.

    The whole word has to be there: a key is a name, and a name that sits inside a longer word
    is a different word. ``oman`` is inside ``roman`` and ``german``, ``us`` inside ``business``,
    ``mali`` inside ``malian`` - matching those answered "capital of the roman empire" with
    Muscat. The boundary is only on letters, so a key followed by a full stop still matches.
    """
    for name in sorted(table, key=len, reverse=True):
        if re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", text) and _names_place(text, name):
            return name
    return None


# The entry is in the key as a country name, and a chat about capitals leaves the word behind it, so
# the reply asks the line itself whether capital is what it is about.
CAPITAL_WORD = re.compile(r"\bcapitals?\b")


def _capital(memory, understood):
    said = understood.get("clean", "") or ""
    if not CAPITAL_WORD.search(said):
        # The word came from the turn before, not from this line: after a capital question,
        # "how long do i roast a turkey" names a country and nothing else, and the table in
        # the key answered it "Ankara, not Istanbul." A line that does not say capital is
        # handed back, so the turkey's own card gets the turn.
        return None
    country = _find_in(said, CAPITALS)
    if not country:
        return None
    return f"{CAPITALS[country]}"


def _place_in(memory, understood, table):
    """The place the line names, or the one the last turn or two named: "what should we do
    there" is about the city from the turn before."""
    clean = understood.get("clean", "")
    name = _find_in(clean, table)
    if name:
        # Every row that reads a country as a destination reads it through here, and a country
        # named as a thing is not one: "how long for a turkey" was three full days in Istanbul,
        # and the rows for a country's weather, its money and its airports had the same hole.
        # A country is never "a" anything, so the determiner says which word the line used.
        if table is WHERE_TO_GO and _a_thing_not_a_place(clean, name):
            return None
        return name
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return None
    for turn in reversed(turns[-2:]):
        if not isinstance(turn, dict):
            continue
        name = _find_in(str(turn.get("user") or "").lower(), table)
        if name:
            return name
    return None


# A month or a season, said anywhere in the conversation, is when they are going. A guide that
# ends on its own season ("May is warm and busy") then answers a question they did not ask and
# contradicts the month they gave: "we're going to Edinburgh in July" came back with "In December
# it's dark by 4pm". The seasonal sentence is kept when it is about the time they said, and taken
# off when it is about another one; a guide with no season in it is left alone.
SEASON_MONTHS = {"spring": {3, 4, 5}, "summer": {6, 7, 8}, "high summer": {7, 8},
                 "autumn": {9, 10, 11}, "fall": {9, 10, 11}, "winter": {12, 1, 2}}
SEASON_NOUNS = ("spring", "summer", "autumn", "fall", "winter")
_MONTH_IN_TEXT = re.compile(
    r"(?:^|(?<=in )|(?<=for )|(?<=until )|(?<=from )|(?<=to )|(?<=by )|(?<=early )"
    r"|(?<=late )|(?<=mid ))(%s)\b" % "|".join(sorted(MONTHS, key=len, reverse=True)))
_SEASON_IN_TEXT = re.compile(r"\b(%s)\b" % "|".join(SEASON_NOUNS))


# "may", "march" and "fall" are ordinary words as well as months: "we may go to Edinburgh" is
# not a date, so these count only when the sentence puts them in time ("in May", "early March")
# or when they are capitalised, which is how a person writes the month and not the verb.
AMBIGUOUS_MONTHS = frozenset(("may", "march", "fall"))


def _time_terms(text, loose=False):
    """The months and seasons a piece of text names: (set of month numbers, set of seasons).

    Loose reads a bare month word ("october", "oct"), which is how a person types the month they
    are going. Both readings still add a month the sentence puts in time ("in May", "from June to
    September") and a month written with a capital, so "we may go to Edinburgh" is not May while
    "Edinburgh in May" is.
    """
    if not isinstance(text, str) or not text.strip():
        return set(), set()
    low = " ".join(text.lower().split())
    words = set(tokens(low))
    months = {MONTHS[match.group(1)] for match in _MONTH_IN_TEXT.finditer(low)}
    if loose:
        months |= {number for word, number in MONTHS.items()
                   if word in words and word not in AMBIGUOUS_MONTHS}
    for word, number in MONTHS.items():
        if len(word) > 3 and re.search(r"\b%s\b" % word.capitalize(), text):
            months.add(number)
    seasons = {match.group(1) for match in _SEASON_IN_TEXT.finditer(low)}
    if "high summer" in low:
        seasons.add("high summer")
    # "June to September", "November - March": a run of months is one season, and a guide that
    # says the season is over 40C is about the month they said if their month is inside it.
    for match in _MONTH_RANGE.finditer(low):
        months |= _between(MONTHS[match.group(1)], MONTHS[match.group(2)])
    return months, seasons


_MONTH_RANGE = re.compile(
    r"\b(%s)\s*(?:to|-|–|until|till|through)\s*(%s)\b"
    % ("|".join(sorted(MONTHS, key=len, reverse=True)),
       "|".join(sorted(MONTHS, key=len, reverse=True))))


def _between(first, last):
    """Every month number from first to last, round the year when it wraps ("November to March")."""
    months, number = set(), first
    for _ in range(12):
        months.add(number)
        if number == last:
            break
        number = number % 12 + 1
    return months


def _when_said(memory, understood):
    """The months and seasons named by this line or one just before it: what they are planning.

    A plan the store is holding is read first, because the store rewrites it when the person
    takes part of it back: "i'm going to lisbon in may" then "sorry, june" leaves the plan as
    June, and reading the older line as well would keep May in the answer ("May is warm and
    busy" for a June trip). The turns are still read when the plan carries no time in it.
    """
    months, seasons = _time_terms(understood.get("clean", ""), loose=True)
    planned = the_plan(memory)
    if planned:
        planned_months, planned_seasons = _time_terms(planned, loose=True)
        if planned_months or planned_seasons:
            return months | planned_months, seasons | planned_seasons
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if isinstance(turns, list):
        for turn in reversed(turns[-2:]):
            if isinstance(turn, dict):
                more_months, more_seasons = _time_terms(str(turn.get("user") or ""), loose=True)
                months |= more_months
                seasons |= more_seasons
    return months, seasons


def _season_fits(sentence, when):
    """True when a guide's last sentence is about the time they said, or says no time at all."""
    stated_months, stated_seasons = when
    if not stated_months and not stated_seasons:
        return True
    months, seasons = _time_terms(sentence)
    if not months and not seasons:
        return True
    if months & stated_months:
        return True
    for season in seasons:
        if SEASON_MONTHS[season] & stated_months:
            return True
        if not stated_months and season in stated_seasons:
            return True
    return False


def _without_the_season(text, when):
    """The guide with a last sentence about another month or season taken off."""
    if not isinstance(text, str):
        return text
    sentences = re.split(r"(?<=[.!?]) ", text.strip())
    if len(sentences) < 2 or _season_fits(sentences[-1], when):
        return text
    return " ".join(sentences[:-1])


_WORTH_ASK = re.compile(r"\bworth (?:visiting|going|a visit|it)\b")
# "What should i eat in rome" is the plate, not the sights: the city card is a list of things to
# see, and the answer to a line that says eat is the cheap-meal card or the country's dish table.
# Only a line that names no eating word at all is the guide's own question.
_EAT_ASK = re.compile(
    r"(?<![a-z])(?:eat|eats|eating|ate|food|foods|dinner|dine|dining|lunch|breakfast|"
    r"restaurant|restaurants|dish|dishes|cuisine|menus?|street food)(?![a-z])", re.I)


# A city read out of the conversation is only the subject when the line says it is a follow-up.
# "is a museum membership worth it" three turns after a trip to Rome is a question about
# museums, not a request for a tour of Rome, so the city has to be in the line itself or the
# line has to point back at it.
FOLLOW_MARKS = ("there", "that city", "this city", "also", "too", "what about", "and ",
                "anything else", "any more")


# The cheap meal in a city is a different question from the guide: "cheap places to eat in rome"
# was answered with the Colosseum and a note to carry a water bottle, which names no price. What
# makes a city cheap to eat in is a few local habits, and the ones that travel well are the same
# everywhere: the fixed lunch, the counter, the market and the bakery. A city with its own line
# gets it, and any other city gets the habits.
CHEAP_EATS = {
    "rome": "In Rome the cheap meal is pizza al taglio, sold by weight and eaten standing, or a "
            "panino from a bakery counter; supplì and a slice of pizza bianca are a couple of "
            "euros. Eat in Testaccio or Trastevere rather than beside a monument, and take your "
            "coffee standing at the bar, where it costs a third of the table price.",
    "paris": "In Paris the cheap lunch is a bakery one: a jambon-beurre is about five euros, and "
             "a market street such as Rue Cler or Rue Mouffetard does the same for less. The plat "
             "du jour at a neighbourhood bistro is half the evening price, tap water is free and "
             "normal, and a picnic on the quays beats a table by the Eiffel Tower.",
    "barcelona": "In Barcelona the cheat code is the menú del día at lunch: three courses and a "
                 "drink for around twelve to fifteen euros, in the Eixample or Gràcia, not on Las "
                 "Ramblas. Standing at a bar with tapas and a vermut costs a few euros a round, "
                 "and the Boqueria's back stalls are cheaper than its front ones.",
    "madrid": "In Madrid the menú del día at lunch is the cheap meal, and tapas around La Latina "
              "or Lavapiés are a few euros each, with the drink included in most bars. Standing "
              "at the bar is cheaper than a table, and dinner starts late, so lunch is the meal "
              "to spend on.",
    "lisbon": "In Lisbon a bifana or a pastel de nata at a counter costs a couple of euros, and "
              "the prato do dia at lunch in Alfama or Graça is the full cheap meal. Drink at a "
              "kiosk rather than a terrace, and the Time Out Market is the easy one-stop version.",
    "florence": "In Florence the cheap meal is a panino from a busy shop (a big one is about six "
                "euros), pizza al taglio, or a trattoria across the river in the Oltrarno; a "
                "table on a piazza with a view is the expensive version of the same food.",
    "amsterdam": "In Amsterdam the cheap meal is a broodje from a bakery, a portion of chips with "
                 "mayonnaise, or the market at Albert Cuypstraat; a supermarket picnic in the "
                 "Vondelpark costs less than a café lunch, and tap water is free if you ask.",
}

def _place_in_the_plan(memory, table):
    """The place the chat's plan names, when the last turn or two have moved off it.

    "im taking my wife to lisbon in may" is kept as the plan for the whole chat, so a follow-up
    three turns later ("what should we eat there") still knows the city even though no line
    since has said it. Only the plan's own words are read, newest first - and the newest of all
    is "the_plan", the one line the store rewrites when the person takes a detail back, so
    "sorry not lisbon, porto" cannot leave the older city being used.
    """
    user = memory.get("user") if isinstance(memory, dict) else None
    if not isinstance(user, dict):
        return None
    current = the_plan(memory)
    if isinstance(current, str) and current.strip():
        name = _find_in(current.lower(), table)
        if name:
            return name
        # The plan names somewhere this table has nothing to say about. An older plan in the same
        # chat is a place the person has taken back ("sorry not lisbon, porto"), so its answer
        # would be about the wrong city: better nothing than that.
        if _find_in(current.lower(), CITIES):
            return None
    plans = user.get("plans")
    if not isinstance(plans, list):
        plans = [user.get("plan")]
    for plan in reversed([one for one in plans if isinstance(one, str) and one.strip()]):
        name = _find_in(plan.lower(), table)
        if name:
            return name
    return None


def _cheap_eats(memory, understood):
    """The cheap meal in the city named or planned, or the habits that work in any city."""
    clean = (understood.get("clean") or understood.get("text") or "").lower()
    city = next((one for one in CHEAP_EATS if one in clean), None)
    if not city:
        # "what should we eat there": the city is not in this line, and the last two turns were
        # about the wife's fish, so read the plan the chat still holds.
        city = _place_in_the_plan(memory, CHEAP_EATS)
    if city:
        return CHEAP_EATS[city]
    if "eat there" in clean:
        # A bare "there" with no city anywhere in the chat is not a travel question this answer
        # can place; leave it to whoever else can read it rather than give the any-city habits.
        return None
    return ("Three habits make any city cheap to eat in: take the fixed lunch rather than "
            "dinner - menu del día, plat du jour, prato do dia, Mittagsmenü - which is the same "
            "kitchen at half the price; eat where people work and shop, at a market hall, a "
            "bakery counter or a busy bar, rather than where they sightsee; and stand up to eat, "
            "because pizza by the slice, a kebab, a bowl of noodles at a counter or a picnic "
            "from a supermarket costs a fraction of a table with a view. Coffee and breakfast at "
            "a bar, and tap water in a bottle you refill, save the rest.")

def _guide(memory, understood):
    clean = understood.get("clean", "")
    # "is Lisbon worth visiting" is what there is to do there, so the guide answers it. Add a
    # month and the question is about when, which only the table can answer: "is it worth
    # visiting Venice in august" wants the heat, not the traghetto.
    if _WORTH_ASK.search(clean) and any(_time_terms(clean, loose=True)):
        return None
    # The city has to be named in this line: a city remembered from earlier turns is the city
    # for "what should we do there", which is city-followup's question, not for every line with
    # a museum word in it.
    # A booking ask is not a "what is there to do" ask, and this note's own text says "book the
    # Vatican museums online", so on a base where the note is keyed on that word a line asking
    # when to book came back with the things-to-do list - a confident answer to another question.
    # city-best-time answers these, which is where the booking window is said.
    if BOOK_ASK.search(clean):
        return None
    # The meal in a city is what to eat there, and the sights card is no answer to it. Only for a
    # city the cheap-meal table actually holds, though: where it has no card the guide is the
    # better answer ("whats good to eat in naples" already names the pizza in the old town).
    if _EAT_ASK.search(clean) and _find_in(clean, CHEAP_EATS):
        return None
    city = _find_in(clean, CITIES)
    if not city:
        # The city was named in the line before and this line asks about it: the guide is one
        # paragraph and it has just been served, so the question "what should i see" next to it
        # is asking for what comes after it, not for it again. The follower owns that answer.
        if SIGHTSEEING_ASK.search(clean):
            return _guide_next(memory, understood)
        return None
    body = _without_the_season(CITIES[city], _when_said(memory, understood))
    # A line that asks nothing is not a new question about the city: "we are staying near
    # waverley" and "we have 4 nights" are statements about the trip, and the line after the
    # guide that carries no ask is not asking for the day trips. Only a line with an ask gets
    # the next thing; a statement keeps the guide it was already given.
    if _already_guided(memory, city) and understood.get("asks"):
        said = (understood.get("plain") or understood.get("text") or clean).lower()
        if _said_before_in_the_chat(memory, clean, understood):
            # The same line typed again, with the city still in hand from the turns before it
            # ("what should i see" after the plan named Lisbon). The guide is what was asked for
            # both times, so the guide is what comes back and the composer frames the repeat
            # ("Same as before: ..."). Day trips here would answer a question nobody asked: the
            # day-trip branch below is what a *new* ask after the guide gets.
            return f"In {city.title()}: {body}"
        if _find_in(said, CITIES) == city and _asked_for_the_guide_before(memory, city, clean):
            # The same ask again wants the same answer. The composer frames a repeated answer
            # ("Same as before: ...") instead of turning a repeat into a request for the next
            # thing, which would lose the guide to a day-trip list and then leave the follow-up
            # "is sintra worth it" with nothing to answer.
            return f"In {city.title()}: {body}"
        # The city was named and guided earlier; this line came back to it after a digression
        # ("is sintra worth it" is read as Lisbon again), so the guide is the one answer that
        # must not be served twice. The next thing about the city is the day trips or the detail
        # it names; when there is none, another entry answers.
        return _about_city(city, memory, clean, understood)
    return f"In {city.title()}: {body}"


# The words a line is made of that say nothing about what is being asked: the grammar, and the
# city the reading writes into a line that only pointed at it.
NOT_THE_ASK_WORDS = frozenset("""the a an in to for at of on and or but it its there here this
    that these those do does did i we me my us you your should could would can what whats
    trip""".split())


def _the_ask_words(text):
    """The words of a line that say what is being asked, with the city and the grammar out."""
    words = set()
    for word in str(text or "").lower().replace("?", " ").replace(",", " ").split():
        word = word.strip(string.punctuation)
        if len(word) < 3 or not word.isalpha():
            continue
        if word in NOT_THE_ASK_WORDS or word in CITIES:
            continue
        words.add(word)
    return words


def _said_before_in_the_chat(memory, clean, understood=None):
    """Whether this is a line they typed earlier, not a new way of asking.

    The line the guide is read on is not the line they typed: "what should i see" in a chat whose
    plan named Lisbon arrives here as "and what should i see husband planning trip lisbon", with
    the plan's own words written into it and its grammar left out. So the comparison is between
    the words that are the ask on both sides, with the city, the plan and the grammar taken out;
    comparing the lines themselves would only ever match a repeat that named the city.
    """
    said = understood if isinstance(understood, dict) else {}
    mine = _the_ask_words(said.get("text") or said.get("plain") or clean) - _the_plan_words(memory)
    if not mine:
        return False
    for turn in (memory.get("turns") or []):
        if not isinstance(turn, dict) or not turn.get("bot"):
            continue  # the turn being composed, which is this line
        if _the_ask_words(turn.get("user")) - _the_plan_words(memory) == mine:
            return True
    return False


def _the_plan_words(memory):
    """The words of the trip the chat is planned around, which are not what a line asks."""
    user = memory.get("user") if isinstance(memory, dict) else None
    if not isinstance(user, dict):
        return frozenset()
    plans = [str(one) for one in ([user.get("plan")] + list(user.get("plans") or [])) if one]
    words = frozenset()
    for plan in plans:
        words = words | _the_ask_words(plan)
    return words


# The words that say the person is asking about being in the place, rather than only naming it.
# They are not a trip frame on their own ("we stay in each night" is a habit), so they count
# only beside the place they are about, which is the line "how long should i stay in rome".
STAYS_THERE = re.compile(r"\b(?:stay|stays|staying|stayed|nights?|days?)\b", re.I)


def _the_lines_said(memory, understood):
    """What the chat has said, newest first, the line itself first."""
    said = [understood.get("clean") or ""]
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed((turns or [])[-2:]):
        if isinstance(turn, dict):
            said.append(str(turn.get("user") or ""))
    return said


def _lines_about(place, said):
    """Only a line that names the place can say anything about it."""
    return [line.lower() for line in said if line and str(place) in line.lower()]


def _a_trip_to(place, memory, understood):
    """Whether the chat says they are going to the place, rather than living there or back from it.

    A city the chat named is not a stay: "i live in edinburgh" then "how many days" is a person
    who lives there, "my sister lives in lisbon" is their sister's home, and "i went to
    edinburgh last year" is behind them. A holiday length is a confident wrong answer to all
    three, so the city has to be one the chat is going to.
    """
    from ..memory.topics import LIVES_THERE, going_there  # lazy: that module reads this one
    said = _the_lines_said(memory, understood)
    low = _lines_about(place, said)
    # "how long should i stay in rome" is the stay question itself, and the reason main could not
    # tell it from a line about the empire is that the word "stay" was not read as a trip: the
    # trip words are "going", "trip", "holiday", "fly", and this line has none of them. Asking
    # how long to stay somewhere is planning to be there, so the stay words count as the trip
    # frame - on a line that names the place, and not when the chat says they live in it.
    if any(_lives_in(place, line) for line in low):
        # "i live in edinburgh" then "how many days should i stay in edinburgh" is a person
        # asking about their own home: the length is read off the first line, so both are read.
        return False
    if any(STAYS_THERE.search(line) for line in low):
        return True
    # Only a line that names the place can say they are going there: the frame words in another
    # line ("how many days") say nothing about the city.
    if any(going_there(place, line) for line in said
           if line and str(place) in line.lower()):
        return True
    # The frame and the place can also be in different turns. "where should i go in spain" /
    # "what about seville" / "how many days should i spend there" is a trip, though no one line
    # holds both the going and the city, and it was answered with the daily budget. A length
    # asked in this line is the frame for the place the turns before named; a line that says
    # they live there, or that they have been, still turns it down.
    from ..memory.topics import LIVES_THERE  # lazy, as above
    if ASKS_A_LENGTH.search(understood.get("clean") or ""):
        turns = memory.get("turns") if isinstance(memory, dict) else None
        since = [str((turn or {}).get("user") or "").lower()
                 for turn in reversed((turns or [])[-3:]) if isinstance(turn, dict)]
        if any(str(place) in line for line in since) and not any(
                str(place) in line[found.end():found.end() + 40]
                for line in since for found in LIVES_THERE.finditer(line)):
            return True
    return False


# A journey takes minutes and a suitcase takes minutes to pack: neither is a stay, and both
# arrive with "how long", so no length table answers the line.
A_JOURNEY_OR_A_BAG = re.compile(
    r"\b(?:flight|flights|fly|flying|train|trains|bus|coach|drive|driving|journey|"
    r"walk|walking|ferry|transfer|queue|wait|pack|packing|clothes|suitcase|luggage|"
    r"case)\b")

# A line that asks a length about the place in it is about a trip to the place, not a life in it:
# "how long in japan" was a search hedge because the trip frame ("going", "trip", "nights") that
# the stay tables wait for was not in the line. The frame is only missing from the line, not from
# the meaning, and the one thing that turns it down is the person saying they live there.
ASKS_A_LENGTH = re.compile(
    r"\b(?:how long|how many days|how many nights|how much time|enough time|too long|"
    r"too short|days in|nights in)\b", re.I)


def _lives_in(place, line):
    """Whether the line gives the place as where the person lives, as "i live in edinburgh" does.

    The word has to be the thing they live in: "how long should i stay in rome to see the works"
    is about a holiday, so only a place just after the verb counts, as topics.going_there reads it.
    """
    from ..memory.topics import LIVES_THERE  # lazy: that module reads this one for its table
    for match in LIVES_THERE.finditer(str(line or "").lower()):
        if str(place) in str(line or "").lower()[match.end():match.end() + 40]:
            return True
    return False


def _stay_length(memory, understood):
    """How many days the city is worth. A journey takes minutes, so those words are not this."""
    clean = understood.get("clean", "")
    if A_JOURNEY_OR_A_BAG.search(clean):
        return None
    # "i have three days in lisbon" already knows how long and wants the plan, which is the
    # guide's answer: this table only answers a line that asks.
    stated = re.search(r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a few|"
                       r"a couple of|several)\s+(?:full\s+)?(?:days|nights|day|night)\b", clean)
    # "is four days enough for lisbon" asks the table's own question with the number in it, so
    # only a line that has settled the length ("i have four days", "we're there for four days")
    # is somebody else's: that one wants the guide.
    asking = re.search(r"\b(?:enough|too long|too short|too much|worth it|worth|do i need|"
                       r"should i|should we|do we need)\b", clean)
    if stated and not asking:
        return None
    if not asking and not re.search(r"\b(?:how long|how many days|how many nights|how much time)\b",
                                    clean):
        return None
    place = _place_in(memory, understood, CITY_DAYS)
    if not place:
        return _country_stay_length(memory, understood)
    if not _a_trip_to(place, memory, understood):
        # The ask is its own frame. "how long do i need in rome" and "how long should i spend in
        # florence" name no trip word at all - the question is where somebody is going - and on
        # main the Rome one was answered with the duration of the Roman Empire and the Florence
        # one with a search hedge. A line that puts the city after in or at and asks how long is
        # a person going there, which is the one thing _a_trip_to asks for.
        if not (_find_in(clean, CITY_DAYS)
                and re.search(r"\b(?:in|at|to see|to visit|around|for)\s+"
                              + re.escape(place), clean)):
            return None
        # ...unless the chat says they live there: "i live in edinburgh" then "how many days
        # should i stay in edinburgh" is a resident asking about their own city, and the length
        # of a holiday is a confident wrong answer to it.
        said = _the_lines_said(memory, understood)
        if any(_lives_in(place, line) for line in _lines_about(place, said)):
            return None
    return _stay_days(place)


def _the_places_the_country_card_names(country):
    """The cities of the where-to-go card for a country, in the order the card puts them.

    The card is prose ("Lisbon for trams, tarts and the river. Porto for the port cellars"), but
    the cities it names are the ones with a guide row of their own, so the days-per-city table is
    what turns the card into a length: Portugal is Lisbon, then Porto, and the Algarve has no row.
    """
    body = WHERE_TO_GO.get(country, ("", ""))[1].lower()
    found = []
    for name in CITY_DAYS:
        found_at = re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", body)
        if found_at:
            found.append((found_at.start(), name))
    return [name for _, name in sorted(found)]


def _country_stay_length(memory, understood):
    """How long to give a country the card named three places in.

    "how many days should i spend in portugal" was answered with the daily budget (the money row
    is keyed on the country and the word "spend"), and "how long should we go for" after the
    Portugal card was a search hedge, because the days table is keyed on cities and Portugal is
    not one. The length of a country trip is the length of the cities the card itself named, so
    the answer is built from the same table rather than guessed.
    """
    clean = understood.get("clean", "")
    if A_JOURNEY_OR_A_BAG.search(clean):
        return None
    country = _place_in(memory, understood, WHERE_TO_GO)
    if not country:
        return None
    # A city named in the line or in the turns since is a smaller subject than the country it sits
    # in, and the city's own row answers it ("what about seville" and then "how many days should i
    # spend there" is two full days in Seville, not the whole of Spain).
    if _place_in(memory, understood, CITY_DAYS):
        return None
    # "there" points back at the last place named, and a country is only ever the one the card
    # named turns ago: "what about seville" and then "how many days should i spend there" is
    # Seville, and the carried country on the end of the line ("... there in spain") is the
    # reading's, not the person's. A pointing word is left to the row that reads it.
    if re.search(r"\b(?:there|that city|this city|the city)\b", clean, re.I):
        return None
    # The country has to be in the words the person typed. A follow-up that names nothing comes
    # here twice: once as typed, and once with the country carried onto the end ("how many days
    # should i spend the spain"), and the carried one answers the whole country to a question
    # about the city the last turn named.
    typed = str(understood.get("text") or "").lower()
    if typed and str(country) not in typed:
        return None
    if not (_a_trip_to(country, memory, understood)
            or (ASKS_A_LENGTH.search(clean) and str(country) in clean.lower())):
        return None
    from ..memory.topics import LIVES_THERE  # lazy: that module reads this one for its table
    if any(str(country) in clean[found.end():found.end() + 40]
           for found in LIVES_THERE.finditer(clean)):
        return None  # "i live in japan": a length of stay is no answer
    places = _the_places_the_country_card_names(country)
    if not places:
        return None
    label = WHERE_TO_GO[country][0]
    if len(places) == 1:
        return _stay_days(places[0])
    words = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")
    first, second = places[0], places[1]
    text = (f"{label}: {first.title()} {_full_days(CITY_DAYS[first])}, "
            f"{second.title()} {words[CITY_DAYS[second] - 1]}, so "
            f"{words[sum(CITY_DAYS[name] for name in (first, second)) - 1]} days in all with the "
            f"journey between them")
    if len(places) > 2 and places[2] in CITY_DAYS:
        text += f", and a day or two more for {places[2].title()}"
    return text + "."


def _full_days(count):
    """A number of days said the way a friend says it: "three full days", "one full day"."""
    words = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")
    if count == 1:
        return "one full day"
    if count < len(words):
        return words[count - 1] + " full days"
    return str(count) + " full days"


def _stay_days(place):
    """The number of days for one city, said as a full sentence."""
    days = CITY_DAYS[place]
    words = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")
    length = "One full day" if days == 1 else f"{words[days - 1].title()} full days"
    text = (f"{length} in {place.title()}, not counting the day you arrive or the day you fly "
            f"home: that covers the main sights at a normal pace, with time to sit down for lunch")
    if place in DAY_TRIPS:
        text += ", and a day more if you want one of the day trips"
    return text + "."


def _stay_there(memory, understood):
    """"How long should i spend there" - the city is the one the last turn or two named."""
    clean = understood.get("clean", "")
    if _find_in(clean, CITY_DAYS):
        return None  # the line names a city: city-stay answers that one
    place = _place_in(memory, understood, CITY_DAYS)
    if not place or not _a_trip_to(place, memory, understood):
        return None
    return _stay_days(place)


def _adapter(memory, understood):
    """The plug question, answered for the country the line names."""
    clean = understood.get("clean", "")
    # "do i need an adapter there" names no country: the trip named in the last turn or two did.
    place = _place_in(memory, understood, PLUG_TYPES)
    if not place:
        return None  # no country named: the general line is travel-adapter's own text
    letter, shape, note = PLUG_TYPES[place]
    if letter == "G":
        return (f"{place.title()} uses the same three square pins as the UK, so what you bring "
                f"from home fits. Take an adapter only for anything with a European plug on it, "
                f"and check that the voltage is the same, which it is in most of these places.")
    text = f"In {place.title()} the sockets are type {letter}, {shape}, so a UK plug needs an adapter"
    if note:
        text += ". " + note
    return text.rstrip(".") + (
        ". Phone and laptop chargers handle 100 to 240 volts; hairdryers and straighteners "
        "often do not, so look at the label before you pack them.")


_HILL = re.compile(r"\b(?:hike|hiking|hill|hills|mountain|mountains|fell|munro|ridge|trek|trekking|coast path|rambl"
                    r"|summit|peak|dales|moors?)\b")


def _city_pack(memory, understood):
    """What goes in the bag for a city break, colder the more the line says about the weather."""
    clean = understood.get("clean", "")
    if not re.search(r"\b(?:cold|winter|snow|snowing|freezing|december|january|february|"
                     r"november)\b", clean):
        return ("Take what you can walk in all day and layer: one pair of comfortable shoes, a "
                "warm mid-layer for the evening, a light waterproof you can fold into a bag, and "
                "a small day bag. One evening outfit is enough, plus a charger and your tickets.")
    return ("Pack for 2 to 8C, wind and rain: a waterproof coat with a hood, warm layers you can "
            "take off indoors, and shoes you can walk a hill in. It gets dark around 4pm in "
            "December, so a small torch and plans for the afternoon indoors help.")


def _hike_day(memory, understood):
    """A day on a hill: lead with the food when the line asks what to eat, water otherwise."""
    clean = understood.get("clean", "")
    if (re.search(r"\b(?:every day|everyday|daily|most days|each day)\b", clean)
            and not _HILL.search(clean)):
        # A walk round the block is not a day on a hill: "i walk every day and i dont eat much"
        # got "about 60g of carbohydrate an hour - sandwiches, oatcakes, nuts" because "walk" and
        # "eat" are both in the key, and that is the food for a climb. Said with a hill name it is
        # still the day-out question ("how much water should i drink every day on a hike").
        return ""
    water = ("half a litre an hour of walking is the working rule, so two litres for a half day "
             "out and three or four for a full one, more in heat or on a climb, and carry it since "
             "a stream is not safe to drink but a tap or a cafe will fill you up")
    food = ("about 60g of carbohydrate an hour - sandwiches, oatcakes, nuts, dried fruit, a "
            "flapjack - eaten little and often rather than as one big lunch, with something salty "
            "for what you sweat out")
    # What goes in the bag is a packing question: the water and the food are two items on a short
    # list, and the list is the answer. "what should i pack for a day hike" got "half a litre an
    # hour ... for food, 60g" and nothing about layers, which is not a packing answer. A quantity
    # is not a packing ask either: "how much water should i take on a hike" says "take" and was
    # handed the layers and the boots, when the figure it asked for is the water.
    if (not re.search(r"\b(?:how much|how many|how long)\b", clean)
            and re.search(r"\b(?:pack|packing|packed|bring|take|carry|wear|kit|bag|rucksack|backpack)\b",
                          clean)
            and re.search(r"\b(?:what|which|anything|need|should)\b", clean)):
        kit = ("Layers, a waterproof, and the water and food: base layer, fleece, a shell you "
               "can get into in the wind, spare socks; half a litre an hour, so two litres for a "
               "half day; 60g of carbohydrate an hour. Add a map or a charged phone with the "
               "route, a torch, hat and gloves, a blister kit, and a foil blanket.")
        if re.search(r"\b(?:pack|packing|packed|bring|carry|wear|kit|bag|rucksack|backpack)\b",
                     clean):
            return kit + " Leave the jeans and the cotton at home."
    if (re.search(r"\b(?:eat|eating|ate|food|snack|snacks|lunch|fuel|energy|hungry|"
                  r"carb|carbs|carbohydrate)\b", clean)
            and not re.search(r"\b(?:water|drink|drinking|liquid|litre|litres)\b", clean)):
        return (food[0].upper() + food[1:] + ". For the drink, " + water + ".")
    return (water[0].upper() + water[1:] + ". For food, aim at " + food + ".")


def _tap_water(memory, understood):
    """Whether the water out of the tap is drinkable, where the answer is stable."""
    clean = understood.get("clean", "")
    # A bottle through security, a hot drink, and how much to drink in a day are other questions.
    if re.search(r"\b(?:liquids|bottle|bottles|hand luggage|cabin bag|security|plane|flight|"
                 r"fountain|how much|more water|enough water|glasses|dehydrat|hot water|"
                 r"boil|watering|water the|water my|water it|water them|bill|leak|pressure|"
                 r"heater|plant|plants|houseplant|houseplants|leaves|leaf)\b", clean):
        return None
    if not re.search(r"\b(?:tap|safe|drink|drinking|ice|okay|ok|fine|stomach|ill)\b", clean):
        return None
    place = _place_in(memory, understood, WATER)
    city = None
    if not place:
        # A city answers as its country does: nobody asks about Rome and means Lazio's pipes.
        city = _place_in(memory, understood, CITY_COUNTRY)
        country = CITY_COUNTRY.get(city or "", "")
        if country in WATER:
            place = country
    if not place:
        # A place we have no row for, or a home plumbing question ("my tap water is cloudy"),
        # which is not about a holiday at all.
        if re.search(r"\b(?:abroad|holiday|holidays|trip|travelling|traveling|travel)\b", clean):
            return TAP_WATER_GENERAL
        # A tap at home is the same question as a tap abroad, and it used to be passed on to
        # whatever else the line's words caught: a trades shrug, a sink-cleaning answer.
        if not re.search(r"\b(?:tap|taps|mains|bottled|safe|water company|water supply)\b", clean):
            return None
        if re.search(r"\b(?:brown|yellow|orange|rust|rusty|gritty)\b", clean):
            return TAP_WATER_HOME_BROWN
        if re.search(r"\b(?:smell|smells|smelled|taste|tastes|tasted|chlorine|metallic|"
                     r"lead|discoloured|discolored)\b", clean):
            return TAP_WATER_HOME_TASTE
        return TAP_WATER_HOME
    label = (city or place).title()
    if WATER[place]:
        return (f"Tap water in {label} is safe to drink: it is treated, the restaurants serve it, "
                f"and a refillable bottle saves money all week. Bottled is only worth it if the "
                f"plumbing in an old building makes the taste odd.")
    return (f"In {label}, drink bottled or filtered water, and skip the ice from street "
            f"stalls: the local water upsets visitors far more than locals. Use bottled for "
            f"brushing your teeth, and eat fruit you peel yourself for the first few days.")


# The clock a line about a flight gives: "at 6am", "7.30", "18:40", "9 pm". A bare number is a
# clock only behind one of the little words people put one behind ("at 7", "is 7", "by 7"), so
# "2 hours before the flight" stays a length of time and is not read as half past one.
_CLOCK_AFTER = re.compile(r"\b(?:at|is|by|around|about|for|before)\s+(\d{1,2})(?:[:.](\d{2}))?"
                          r"\s*(am|pm)?\b")
_CLOCK_MERIDIEM = re.compile(r"\b(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)\b")
# How long something takes: "an hour", "40 minutes", "an hour and a half", "two hours".
_LENGTH_SAID = re.compile(r"\b(\d{1,2}|an?|one|two|three|four)\s*(?:hours?|hrs?)\b")
_LENGTH_MINS = re.compile(r"\b(\d{1,3})\s*(?:minutes?|mins?)\b")
# The words that say a clock is when the person leaves the house rather than when the flight goes.
_LEAVE_SAID = re.compile(
    r"\b(?:leave|leaves|leaving|left|set off|setting off|sets off|set out|head off|heads off|"
    r"drive|driving|coming from|get going)\b")
# The words that say it is the flight's own time.
_FLIGHT_SAID = re.compile(
    r"\b(?:flight|flights|fly|flies|flying|departs?|departure|takes? off|take off|takeoff|"
    r"boarding|board|gate|landing|lands)\b")
# The drive to the airport, when the line says how long it is.
_DRIVE_SAID = re.compile(
    r"\b(?:drive|driving|journey|taxi|cab|train|bus|tube|ride|commute|to the airport|"
    r"get to the airport|get there|from home|away|takes?)\b")
_SMALL_COUNT = {"one": 1, "two": 2, "three": 3, "four": 4}


def _clock_pairs(text):
    """Every clock time in the line, with the side of the trip it belongs to.

    A line can carry two - "i leave at 5 for a 7am flight" - and which is which is read from the
    nearest word that names it: the leaving words on one side, the flight words on the other.
    """
    found, seen = [], set()
    for pattern in (_CLOCK_AFTER, _CLOCK_MERIDIEM):
        for match in pattern.finditer(text):
            hour, minute = int(match.group(1)), int(match.group(2) or 0)
            meridiem = (match.group(3) or "").lower()
            if hour > 23 or minute > 59 or (hour > 12 and not meridiem and not match.group(2)):
                continue
            if re.match(r"\s*(?:hours?|minutes?|mins?|days?|weeks?|nights?)\b",
                        text[match.end():]):
                continue  # "at 2 hours before" is a length of time
            key = (hour, minute, meridiem)
            if key in seen:
                continue
            seen.add(key)
            head = text[max(0, match.start() - 34):match.start()]
            tail = text[match.end():match.end() + 26]
            # A leaving word right in front of the clock settles it, and so does a flight word
            # right behind: "set off at 6 will i miss my flight" is a leaving time, because the
            # flight is the worry named after it, and "leave at 5 for a 7am flight" is both.
            near_head = head[-16:]
            if _LEAVE_SAID.search(near_head) and not re.search(r"\b(?:miss|make|catch)\b",
                                                              near_head):
                role = "leave"
            elif _FLIGHT_SAID.search(near_head) or _FLIGHT_SAID.search(tail[:16]):
                role = "flight"
            else:
                role = "leave" if _nearest(_LEAVE_SAID, head, tail) >= 0 else "flight"
            if meridiem:
                hour = hour % 12 + (12 if meridiem == "pm" else 0)
            found.append({"hour": hour, "minute": minute, "meridiem": meridiem,
                          "role": role,
                          "sep": ":" if ":" in (match.group(0) or "") else "."})
    return found


def _nearest(pattern, head, tail):
    """How far the nearest word of a pattern is from the clock, either side; -1 for none."""
    best = -1
    for match in pattern.finditer(head):
        distance = len(head) - match.start()
        if best < 0 or distance < best:
            best = distance
    for match in pattern.finditer(tail):
        distance = match.start() + 1
        if best < 0 or distance < best:
            best = distance
    return best


def _length_said(text):
    """A length of time a line gives, in minutes: "an hour and a half", "40 minutes", "90"."""
    if re.search(r"\b(?:an?\s+hour|hour)\s+and\s+a\s+half\b", text):
        return 90
    if re.search(r"\bhalf\s+an?\s+hour\b", text):
        return 30
    hours = _LENGTH_SAID.search(text)
    if hours:
        word = hours.group(1)
        count = 1 if word in ("a", "an") else (int(word) if word.isdigit()
                                                 else _SMALL_COUNT.get(word, 0))
        if count:
            after = text[hours.end():hours.end() + 20]
            more = re.search(r"\b(?:and\s*)?(\d{1,2})\s*(?:minutes?|mins?)\b", after)
            return count * 60 + (int(more.group(1)) if more else 0)
    minutes = _LENGTH_MINS.search(text)
    if minutes:
        return int(minutes.group(1))
    return None


_NUMBER_WORD = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
                "ten", "eleven", "twelve")


def _long_said(minutes):
    """A length of time as people say it: "an hour", "two and a half hours", "40 minutes"."""
    if minutes < 60:
        return f"{minutes} minutes"
    hours, extra = divmod(minutes, 60)
    base = "an hour" if hours == 1 else f"{_NUMBER_WORD[hours - 1] if hours <= 12 else hours} hours"
    if not extra:
        return base
    if extra == 30:
        return ("an hour and a half" if hours == 1
                else f"{_NUMBER_WORD[hours - 1]} and a half hours")
    if extra == 15:
        return ("an hour and a quarter" if hours == 1
                else f"{_NUMBER_WORD[hours - 1]} and a quarter hours")
    return f"{base} and {extra} minutes"


def _at_a_time(clock, minutes):
    """The clock time a length of minutes before (a negative number) or after a stated time."""
    total = (int(clock["hour"]) * 60 + int(clock["minute"]) + minutes) % (24 * 60)
    return total // 60, total % 60


def _a_flight(clock_said, noun=""):
    """"a 7am flight", "an 8.30 flight": the article the spoken clock takes, and the noun.

    Say it out loud and the hour decides: eight, eleven and eighteen start with a vowel sound
    while seven, four and sixteen do not.
    """
    digits = re.match(r"\d+", str(clock_said))
    hour = int(digits.group(0)) if digits else 0
    article = "an" if hour in (8, 11, 18) else "a"
    return f"{article} {clock_said}" + (f" {noun}" if noun else "")


def _a_clock(hour, minute, clock):
    """A time said the way the line said its own: "4am" for "6am", "5" for "7", "16:40".

    Nobody types a meridiem and wants a bare number back, and a plain "at 7" is read and answered
    in the same plain form rather than guessed into "4am" or "4pm".
    """
    if clock.get("meridiem"):
        return _clock(hour, minute)
    if clock.get("sep") == ":":
        return f"{hour % 24:02d}:{minute:02d}"
    tail = f".{minute:02d}" if minute else ""
    return f"{hour % 24 or 12}{tail}"


def _airport_early(memory, understood):
    """How long before the flight to be there, and the clock that comes of it.

    The rule is the same for everyone; what changes is the line. "my flight is at 6am what time
    should i leave" wants the two hours taken off 6, "will i miss my flight if i leave at 5"
    wants it added on, "how long before boarding should i be at the gate" is the gate's own
    clock, and "is 2 hours enough before a flight" is the rule asked as a yes or a no.
    """
    clean = understood.get("clean", "")
    text = clean.lower()
    long_haul = re.search(r"\b(?:long haul|long-haul|transatlantic|usa|america|the states|"
                          r"canada|australia|new zealand|japan|china|asia|dubai|south africa|"
                          r"long flight)\b", text)
    bag = re.search(r"\b(?:checked bag|checked luggage|bag to check|suitcase|hold bag|"
                    r"check a bag|checked in bag|check my bag|check a suitcase|bag drop|"
                    r"hold luggage|check luggage)\b", text)
    hand = re.search(r"\b(?:hand luggage|cabin bag|carry on|carry-on|no bag|no luggage|"
                     r"hand baggage)\b", text)
    if long_haul:
        lead, lead_said = 180, "three hours before departure"
    elif hand and not bag:
        lead, lead_said = 90, "ninety minutes before departure"
    else:
        lead, lead_said = 120, "two hours before departure"
    if hand and not bag:
        # Nothing to drop off, so the bag desk is not their deadline and naming it is noise.
        closes = ("The gate closes 20 to 30 minutes before the flight, so being through security "
                  "45 minutes before it is the deadline that matters.")
        shuts = "The gate shuts 20 to 30 minutes before the flight."
    else:
        closes = ("The bag drop closes 45 to 60 minutes before the flight and the gate 20 to 30, "
                  "so the bag drop is the real deadline, not the departure time.")
        shuts = "Bag drop shuts 45 to 60 minutes before the flight and the gate 20 to 30."
    clocks = _clock_pairs(text)
    leaving = next((one for one in clocks if one["role"] == "leave"), None)
    flying = next((one for one in clocks if one["role"] != "leave"), None)
    drive = _length_said(text) if _DRIVE_SAID.search(text) else None
    # How early the line already intends to be there, if it says it: "is 2 hours enough", "can i
    # arrive 45 minutes before my flight".
    says_before = re.search(r"(?:before|ahead of)\s+(?:my|the|our|a|departure|boarding)\b", text)
    planned = (None if drive is not None or not says_before
               else _length_said(text))
    if re.search(r"\b(?:land|lands|landing|arrive at the other|get in at)\b", text) and not \
            re.search(r"\b(?:airport|before|leave|early)\b", text):
        # When it lands is on the booking, and the air time is a different question.
        return ""
    if _FLIGHT_LENGTH_ASK.search(text):
        # "how long is the flight to rome" is the air time, and the rule about the airport is no
        # answer to it at all.
        return _flight_length(memory, understood)
    if re.search(r"\b(?:connecting|connection|connections|layover|stopover|transit|"
                 r"change planes|changing planes)\b", text):
        # The time between two flights is not the time before one: the bags go through and the
        # person walks a terminal, and what breaks it is the first leg running late.
        if planned is not None:
            said = _long_said(planned)
            if planned >= 90:
                return (f"{said[0].upper() + said[1:]} at Heathrow is comfortable if both flights "
                        f"are on one ticket: the bag goes through and the walk and security again "
                        f"are 30 to 60 minutes. The shortest connection airlines sell there is 60 "
                        f"to 90 minutes.")
            return (f"{said[0].upper() + said[1:]} is under what I would want between flights at "
                    f"Heathrow: 60 to 90 minutes is the usual minimum on one ticket, and that "
                    f"leaves nothing for a late first leg. If the first flight is late the airline "
                    f"has to move you on, but only when both legs are on one booking.")
        return ("Allow 60 to 90 minutes at Heathrow between flights on one ticket, and two "
                "hours if they are separate bookings or you have to collect a bag and check it "
                "again. A "
                "late first leg is what breaks a connection, so one ticket is worth paying a "
                "little more for.")
    if re.search(r"\b(?:cancel|cancelled|canceled|cancelling|refund|refunds|compensation|"
                 r"delay|delayed|voucher)\b", text):
        # A flight that has gone wrong is the airline-rights answer's, and the rule about being
        # early says nothing to somebody whose flight was cancelled an hour ago.
        return ""
    if re.search(r"\b(?:book|books|booking|booked|cheap|cheaper|cheapest|price|prices|"
                 r"fare|fares|deal|deals|cost)\b", text):
        # When to book and what it costs is the fares answer's: "when should i book flights for
        # christmas" was answered with how early to be at the airport.
        return ""
    if re.search(r"\b(?:food|foods|snack|snacks|eat|eating|meal|meals|sandwich|sandwiches|"
                 r"lunch|picnic|drink|drinks)\b", text) and re.search(
            r"\b(?:take|bring|carry|pack|eat)\b", text):
        # What to carry to eat on the plane is the flight-food answer's question, and the clock is
        # no answer to it: "what food should i take on a long flight" was told to allow three
        # hours. "long flight" is one of the words this row reads, which is how food got here.
        return ""
    if re.search(r"\b(?:cruise|ferry|ferries|boat|ship|train|trains|rail|eurostar|coach|"
                 r"bus|hotel|hostel|campsite|airport transfer|transfer)\b", text):
        # Check-in and boarding are not only the airport's: a ship, a coach and a train have their
        # own clocks, and the entries that keep them answer "how early should i check in for a
        # cruise" better than this one can.
        return ""
    if not clocks and re.search(r"\b(?:miss|missed|missing|misses)\b.*\b(?:flight|plane)\b",
                               text) and re.search(
            r"\b(?:what happens|what do i do|missed|too late|no.?show|rebook|refund|claim|"
            r"compensation|rebooked)\b", text):
        # A flight already missed, or the trouble of missing one, is the no-show answer's and it
        # is the next entry along: this one is about getting there in time, and saying nothing
        # here is what lets that answer take the turn.
        return ""
    # The gate and the desk have clocks of their own, and a line asking about those wants them.
    # "what time is boarding for an 8pm flight" asks the same clock as the gate does, so the words
    # that name it both count; "on board" is being on the plane and is not this
    if re.search(r"\b(?:gate|gates|boarding)\b", text) and not re.search(
            r"\bboarding (?:pass|passes|card)\b", text):
        if flying is not None:
            shut = _a_clock(*_at_a_time(flying, -25), flying)
            board = _a_clock(*_at_a_time(flying, -40), flying)
            return (f"For {_a_flight(_a_clock(flying['hour'], flying['minute'], flying), 'flight')}"
                    f" the gate shuts about {shut} and boarding starts around {board}: be in the "
                    f"departure lounge before that, which means through security an hour ahead.")
        return ("Boarding starts about 40 minutes before departure and the gate shuts 20 to 30 "
                "minutes before it, so be through security and in the departure lounge an hour "
                "ahead. The gate's clock is the one that costs you the seat if you miss it.")
    if re.search(r"\bcheck(?:ing)?[ -]?in\b|\bcheckin\b", text) and not re.search(
            r"\b(?:what time should i leave|leave home)\b", text):
        if re.search(r"\bhow long\b", text) and re.search(r"\b(?:take|takes|queue|wait)\b",
                                                             text):
            return ("Ten to twenty minutes at the desk with your bag ready and the documents out, "
                    "and more like half an hour at six in the morning. The desk shuts 45 to 60 "
                    "minutes before departure, so the queue is not what makes you late.")
        return ("Check in online as soon as it opens - 24 to 48 hours before the flight at most "
                "airlines, and the pass appears in their app - and then the airport is only bag "
                "drop and security. The desk shuts 45 to 60 minutes before departure, and 90 "
                "minutes on some long-haul flights.")
    if planned is not None:
        said = _long_said(planned)
        if planned >= lead + 45:
            return (f"That is plenty: {lead_said} is the safe rule, so {said} leaves room for the "
                    f"bag queue and a coffee. {shuts}")
        if planned >= lead:
            return (f"That is about right: {lead_said} is the rule, and "
                    f"{'that' if planned == lead else said} works as long as the bag queue is "
                    f"short. {shuts}")
        if planned >= lead - 30:
            return (f"That is tight: {said} is under the {_long_said(lead)} I would allow, so a "
                    f"queue at the bags or at security is what makes you late. {shuts}")
        return (f"Too tight unless you have no bag to drop and a boarding pass already: {said} "
                f"leaves nothing for the queue at security, and {lead_said} is the safe rule. "
                f"{shuts}")
    if leaving is not None and flying is not None:
        # Both ends of the trip are in the line ("i leave at 5 for a 7am flight"), so the two are
        # put against the rule and the answer is whether it works, not what each one implies.
        road = drive if drive is not None else 30
        leave_at = leaving["hour"] * 60 + leaving["minute"]
        fly_at = flying["hour"] * 60 + flying["minute"]
        if not leaving["meridiem"] and flying["meridiem"]:
            # "leaving home at 4.30 for an 8pm flight": the half of the day the leaving time is
            # in is the one that puts it before the flight, so the flight's meridiem says it.
            while fly_at - leave_at - road > 12 * 60:
                leave_at += 12 * 60
            leaving = dict(leaving, hour=(leave_at // 60) % 24,
                           meridiem="am" if (leave_at // 60) % 24 < 12 else "pm")
        gap = fly_at - leave_at - road
        if gap < -720:
            gap += 24 * 60  # a leaving time after midnight for a flight just after it
        said_flight = _a_clock(flying["hour"], flying["minute"], flying)
        there = _a_clock(*_at_a_time(leaving, road), leaving)
        sides = (f"with {_long_said(road)} on the road" if drive is not None
                 else "with a half-hour drive")
        if gap >= lead + 60:
            earlier = _a_clock(*_at_a_time(flying, -(lead + road)), flying)
            return (f"You are early: leaving at "
                    f"{_a_clock(leaving['hour'], leaving['minute'], leaving)} {sides} puts you at "
                    f"the airport for {there}, {_long_said(gap)} before "
                    f"{_a_flight(said_flight, 'flight')}, so {earlier} would still be there "
                    f"{_long_said(lead)} ahead. {shuts}")
        if gap >= lead:
            return (f"That works: leaving at "
                    f"{_a_clock(leaving['hour'], leaving['minute'], leaving)} {sides} gets you "
                    f"there for {there}, {_long_said(gap)} before "
                    f"{_a_flight(said_flight, 'flight')}. {shuts}")
        if gap >= lead - 30:
            return (f"Cutting it fine: {there} is only {_long_said(gap)} before "
                    f"{_a_flight(said_flight, 'flight')} and I would allow {_long_said(lead)}. "
                    f"Leave half an hour earlier if you have a bag to drop. {shuts}")
        return (f"That is too late for {_a_flight(said_flight, 'flight')}: {there} leaves "
                f"{_long_said(gap)} at the airport, and bag drop shuts 45 to 60 minutes before "
                f"departure. Leave by "
                f"{_a_clock(*_at_a_time(flying, -(lead + road)), flying)} at the latest.")
    if leaving is not None:
        # "will i miss my flight if i leave at 5": the same arithmetic forwards, said as the
        # flight time the leaving time suits.
        if drive is not None:
            there = _a_clock(*_at_a_time(leaving, drive), leaving)
            head = (f"Leaving at {_a_clock(leaving['hour'], leaving['minute'], leaving)} with "
                    f"{_long_said(drive)} on the road puts you at the airport for {there}, ")
        else:
            there = _a_clock(*_at_a_time(leaving, 30), leaving)
            head = (f"Leaving at {_a_clock(leaving['hour'], leaving['minute'], leaving)} puts you "
                    f"at the airport for {there} if the drive is about half an hour, ")
        suits = _a_clock(*_at_a_time(leaving, (drive if drive is not None else 30) + lead), leaving)
        return (f"{head}which is {_long_said(lead)} before {_a_flight(suits, 'flight')} - about "
                f"right. A "
                f"longer drive needs a later flight. {shuts}")
    if flying is not None:
        # "my flight is at 6am what time should i leave": the rule taken off the flight time.
        said = _a_clock(flying["hour"], flying["minute"], flying)
        there = _a_clock(*_at_a_time(flying, -lead), flying)
        if drive is not None:
            home = _a_clock(*_at_a_time(flying, -(lead + drive)), flying)
            return (f"For {_a_flight(said, 'flight')}, be at the airport by {there}: "
                    f"{lead_said} is the safe rule, and with {_long_said(drive)} on the road that "
                    f"means leaving home around {home}. {shuts}")
        home = _a_clock(*_at_a_time(flying, -(lead + 30)), flying)
        return (f"For {_a_flight(said, 'flight')}, be at the airport by {there}: "
                f"{lead_said} is the safe rule. Work back from that for the drive - half an hour "
                f"on the road means leaving home around {home}. {shuts}")
    if re.search(r"\b(?:leave home|leave the house|leave my house|leaving home|set off|"
                 r"set out|get going|need to leave|should i leave|when do i leave|"
                 r"leave for the airport|leaving for the airport|head off)\b", text):
        # "how long before my flight should i leave home" is the same rule with the drive on top
        # of it, and the answer that stops at the airport leaves the actual question unanswered.
        return (f"{lead_said[0].upper() + lead_said[1:]} at the airport, and the drive comes on "
                f"top: half an hour on the road means leaving home {_long_said(lead + 30)} before "
                f"the flight. {shuts}")
    return (f"{lead_said[0].upper() + lead_said[1:]} is the safe rule. {closes} "
            f"Add half an hour at a big airport in the early morning or on a Friday.")


# Hours in the air from the UK, for "how long is the flight to rome". The line almost never says
# where the person flies from, so the answer says the assumption out loud. A city reads through
# to its country, because a flight to Porto is the flight to Portugal.
FLIGHT_HOURS = {
    "ireland": 1.25, "france": 1.5, "belgium": 1.25, "netherlands": 1.25, "germany": 1.75,
    "switzerland": 1.75, "austria": 2, "italy": 2.5, "spain": 2.5, "portugal": 2.75,
    "croatia": 2.5, "greece": 4, "turkey": 4, "morocco": 3.5, "iceland": 3, "norway": 2,
    "sweden": 2.25, "denmark": 1.75, "finland": 3, "poland": 2.25, "czechia": 2, "hungary": 2.5,
    "egypt": 5, "dubai": 7, "south africa": 11, "india": 9, "thailand": 12, "china": 11,
    "japan": 12, "usa": 8, "america": 8, "canada": 8, "mexico": 11, "australia": 21,
    "new zealand": 25, "scotland": 1.25, "england": 1, "wales": 1,
    # the rest of the map an ordinary week or a family visit goes to, so the answer is the place
    # rather than the continent-sized average the fallback gives
    "northern ireland": 1.25, "jersey": 1, "guernsey": 1, "isle of man": 1, "luxembourg": 1.25,
    "slovenia": 2.5, "slovakia": 2.5, "estonia": 3, "latvia": 3, "lithuania": 3, "cyprus": 4.5,
    "malta": 3.25, "tunisia": 3, "albania": 3, "bulgaria": 3.25, "romania": 3.25,
    "cabo verde": 6, "cape verde": 6, "gambia": 6, "senegal": 6, "nigeria": 6.5, "ghana": 6.5,
    "kenya": 8.5, "tanzania": 9, "rwanda": 8.5, "uganda": 8.5, "ethiopia": 8, "namibia": 10.5,
    "zimbabwe": 11, "botswana": 11, "zambia": 11, "mozambique": 11, "madagascar": 12,
    "mauritius": 12, "seychelles": 10.5, "jamaica": 10, "barbados": 8.5, "antigua": 8.5,
    "st lucia": 8.5, "saint lucia": 8.5, "cuba": 9.5, "dominican republic": 9,
    "trinidad": 10, "bahamas": 9,
    "qatar": 6.5, "saudi arabia": 6.5, "bahrain": 6.5, "kuwait": 6.5, "oman": 7.5,
    "israel": 4.75, "jordan": 5, "lebanon": 4.5, "russia": 4,
    "sri lanka": 11.5, "maldives": 10.5, "nepal": 10.5, "pakistan": 8.5, "bangladesh": 10,
    "singapore": 13, "malaysia": 13, "hong kong": 12.5, "vietnam": 12, "cambodia": 12.5,
    "indonesia": 16, "philippines": 15, "south korea": 11.5, "taiwan": 13.5,
    "brazil": 11.5, "argentina": 13.5, "chile": 14.5, "peru": 12.5, "colombia": 10.5,
    "costa rica": 11.5, "panama": 11,
}
# The city a person names is the holiday, not the country's average: New York is seven and a half
# hours and Los Angeles eleven, and "how long is the flight to new york" was answered with the
# two-to-four-hours-across-Europe line because no table had the name at all. This one is read
# before CITY_COUNTRY and only by the flight length, so the city tables that answer "where to
# stay" keep the names they have.
AIR_HOURS_CITY = {
    # America, by state and by the city people fly to
    "florida": "usa", "california": "usa", "texas": "usa", "hawaii": "usa", "nevada": "usa",
    "new england": "usa", "new york": "usa", "new york city": "usa", "orlando": "usa",
    "miami": "usa", "key west": "usa", "las vegas": "usa", "los angeles": "usa",
    "san francisco": "usa", "boston": "usa", "chicago": "usa", "washington": "usa",
    "seattle": "usa", "denver": "usa", "new orleans": "usa", "san diego": "usa",
    "atlanta": "usa", "houston": "usa", "dallas": "usa", "philadelphia": "usa",
    "phoenix": "usa", "nashville": "usa", "austin": "usa", "honolulu": "usa",
    "toronto": "canada", "vancouver": "canada", "montreal": "canada", "calgary": "canada",
    "quebec": "canada", "banff": "canada", "nova scotia": "canada",
    "cancun": "mexico", "tulum": "mexico", "playa del carmen": "mexico", "los cabos": "mexico",
    "havana": "cuba", "montego bay": "jamaica", "kingston": "jamaica", "bridgetown": "barbados",
    "punta cana": "dominican republic", "nassau": "bahamas",
    # Spain and its islands, where the package holiday goes
    "benidorm": "spain", "malaga": "spain", "alicante": "spain", "palma": "spain",
    "ibiza": "spain", "majorca": "spain", "mallorca": "spain", "menorca": "spain",
    "tenerife": "spain", "lanzarote": "spain", "fuerteventura": "spain",
    "gran canaria": "spain", "costa del sol": "spain", "valencia": "spain",
    "bilbao": "spain", "san sebastian": "spain", "granada": "spain", "cordoba": "spain",
    "girona": "spain", "murcia": "spain", "almeria": "spain", "cadiz": "spain",
    "santiago de compostela": "spain", "salou": "spain", "costa brava": "spain",
    # Portugal
    "faro": "portugal", "algarve": "portugal", "madeira": "portugal", "funchal": "portugal",
    "lagos": "portugal", "coimbra": "portugal", "evora": "portugal", "sintra": "portugal",
    "azores": "portugal", "the azores": "portugal",
    # Italy
    "pisa": "italy", "bologna": "italy", "turin": "italy", "palermo": "italy",
    "catania": "italy", "sicily": "italy", "sardinia": "italy", "cagliari": "italy",
    "olbia": "italy", "verona": "italy", "sorrento": "italy", "amalfi": "italy",
    "capri": "italy", "positano": "italy", "taormina": "italy", "tuscany": "italy",
    "lake como": "italy", "genoa": "italy", "bari": "italy", "rimini": "italy",
    "matera": "italy", "lecce": "italy", "the dolomites": "italy", "dolomites": "italy",
    # Greece and its islands
    "corfu": "greece", "rhodes": "greece", "kos": "greece", "zakynthos": "greece",
    "kefalonia": "greece", "mykonos": "greece", "halkidiki": "greece",
    "thessaloniki": "greece", "heraklion": "greece", "chania": "greece", "zante": "greece",
    "skiathos": "greece", "skopelos": "greece", "naxos": "greece", "paros": "greece",
    "milos": "greece", "lefkada": "greece", "kalamata": "greece", "mykonos island": "greece",
    # Turkey
    "antalya": "turkey", "dalaman": "turkey", "bodrum": "turkey", "marmaris": "turkey",
    "izmir": "turkey", "fethiye": "turkey", "side": "turkey", "belek": "turkey",
    "alanya": "turkey", "kusadasi": "turkey", "cappadocia": "turkey", "goreme": "turkey",
    # Cyprus and Malta
    "larnaca": "cyprus", "paphos": "cyprus", "limassol": "cyprus", "ayia napa": "cyprus",
    "protaras": "cyprus", "north cyprus": "cyprus", "valletta": "malta", "gozo": "malta",
    "sliema": "malta",
    # France
    "nice": "france", "lyon": "france", "marseille": "france", "bordeaux": "france",
    "toulouse": "france", "corsica": "france", "ajaccio": "france", "bastia": "france",
    "disneyland paris": "france", "cannes": "france", "antibes": "france",
    "avignon": "france", "montpellier": "france", "nantes": "france",
    "strasbourg": "france", "lille": "france", "grenoble": "france",
    "chamonix": "france", "biarritz": "france", "normandy": "france", "brittany": "france",
    "dordogne": "france", "provence": "france", "loire valley": "france",
    "saint tropez": "france", "monaco": "france",
    # Croatia
    "pula": "croatia", "hvar": "croatia", "zagreb": "croatia", "rovinj": "croatia",
    "sibenik": "croatia", "makarska": "croatia", "trogir": "croatia", "korcula": "croatia",
    "brac": "croatia", "vis": "croatia",
    # the Low Countries, Germany, Austria and Switzerland
    "amsterdam": "netherlands", "rotterdam": "netherlands", "the hague": "netherlands",
    "eindhoven": "netherlands", "utrecht": "netherlands", "brussels": "belgium",
    "bruges": "belgium", "ghent": "belgium", "antwerp": "belgium", "leuven": "belgium",
    "berlin": "germany", "munich": "germany", "frankfurt": "germany", "cologne": "germany",
    "hamburg": "germany", "dusseldorf": "germany", "stuttgart": "germany",
    "nuremberg": "germany", "dresden": "germany", "heidelberg": "germany",
    "bavaria": "germany", "black forest": "germany", "leipzig": "germany",
    "vienna": "austria", "salzburg": "austria", "innsbruck": "austria",
    "hallstatt": "austria", "graz": "austria", "kitzbuhel": "austria",
    "zurich": "switzerland", "geneva": "switzerland", "basel": "switzerland",
    "bern": "switzerland", "lucerne": "switzerland", "interlaken": "switzerland",
    "zermatt": "switzerland", "lausanne": "switzerland", "grindelwald": "switzerland",
    "st moritz": "switzerland", "davos": "switzerland",
    # Ireland, Scotland, England and Wales
    "dublin": "ireland", "cork": "ireland", "galway": "ireland", "shannon": "ireland",
    "belfast": "northern ireland", "edinburgh": "scotland", "glasgow": "scotland",
    "aberdeen": "scotland", "inverness": "scotland", "the highlands": "scotland",
    "isle of skye": "scotland", "skye": "scotland", "st andrews": "scotland",
    "london": "england", "manchester": "england", "cornwall": "england",
    "newquay": "england", "bristol": "england", "birmingham": "england",
    "liverpool": "england", "leeds": "england", "newcastle": "england",
    "york": "england", "bath": "england", "oxford": "england", "cambridge": "england",
    "the cotswolds": "england", "cotswolds": "england", "lake district": "england",
    "brighton": "england", "torquay": "england", "isle of wight": "england",
    "snowdonia": "wales", "pembrokeshire": "wales", "cardiff": "wales",
    "anglesey": "wales", "brecon beacons": "wales",
    # the Nordics and the Baltic
    "copenhagen": "denmark", "stockholm": "sweden", "gothenburg": "sweden",
    "helsinki": "finland", "rovaniemi": "finland", "lapland": "finland",
    "tromso": "norway", "stavanger": "norway", "akureyri": "iceland",
    "prague": "czechia", "budapest": "hungary", "krakow": "poland", "warsaw": "poland",
    "gdansk": "poland", "wroclaw": "poland", "bratislava": "slovakia",
    "tallinn": "estonia", "riga": "latvia", "vilnius": "lithuania",
    "bucharest": "romania", "sofia": "bulgaria", "varna": "bulgaria",
    "burgas": "bulgaria", "plovdiv": "bulgaria", "tirana": "albania",
    "ljubljana": "slovenia", "lake bled": "slovenia", "bled": "slovenia",
    # Africa and the Indian Ocean
    "casablanca": "morocco", "fez": "morocco", "tangier": "morocco", "agadir": "morocco",
    "essaouira": "morocco", "rabat": "morocco", "cairo": "egypt",
    "sharm el sheikh": "egypt", "hurghada": "egypt", "luxor": "egypt",
    "tunis": "tunisia", "hammamet": "tunisia", "djerba": "tunisia", "sousse": "tunisia",
    "cape town": "south africa", "johannesburg": "south africa", "durban": "south africa",
    "nairobi": "kenya", "mombasa": "kenya", "zanzibar": "tanzania",
    "dar es salaam": "tanzania", "addis ababa": "ethiopia", "lagos": "nigeria",
    "accra": "ghana", "banjul": "gambia", "dakar": "senegal", "sal": "cape verde",
    "boa vista": "cape verde", "praia": "cape verde", "port louis": "mauritius",
    "windhoek": "namibia", "harare": "zimbabwe", "kigali": "rwanda",
    # the Gulf, and the eastern Mediterranean
    "abu dhabi": "dubai", "doha": "qatar", "riyadh": "saudi arabia",
    "jeddah": "saudi arabia", "muscat": "oman", "manama": "bahrain",
    "amman": "jordan", "petra": "jordan", "aqaba": "jordan", "tel aviv": "israel",
    "jerusalem": "israel", "eilat": "israel", "beirut": "lebanon",
    # Asia
    "osaka": "japan", "hiroshima": "japan", "sapporo": "japan", "okinawa": "japan",
    "seoul": "south korea", "busan": "south korea", "beijing": "china",
    "shanghai": "china", "macau": "hong kong", "taipei": "taiwan",
    "phuket": "thailand", "chiang mai": "thailand", "koh samui": "thailand",
    "krabi": "thailand", "pattaya": "thailand", "kuala lumpur": "malaysia",
    "penang": "malaysia", "langkawi": "malaysia", "borneo": "malaysia",
    "bali": "indonesia", "jakarta": "indonesia", "lombok": "indonesia",
    "hanoi": "vietnam", "ho chi minh city": "vietnam", "da nang": "vietnam",
    "hoi an": "vietnam", "siem reap": "cambodia", "phnom penh": "cambodia",
    "colombo": "sri lanka", "male": "maldives", "kathmandu": "nepal",
    "delhi": "india", "mumbai": "india", "goa": "india", "kerala": "india",
    "jaipur": "india", "agra": "india", "taj mahal": "india",
    "bangalore": "india", "chennai": "india", "kolkata": "india", "karachi": "pakistan",
    "islamabad": "pakistan", "lahore": "pakistan", "dhaka": "bangladesh",
    # Oceania and South America
    "brisbane": "australia", "perth": "australia", "adelaide": "australia",
    "cairns": "australia", "gold coast": "australia", "hobart": "australia",
    "auckland": "new zealand", "wellington": "new zealand", "christchurch": "new zealand",
    "queenstown": "new zealand", "rio de janeiro": "brazil", "sao paulo": "brazil",
    "buenos aires": "argentina", "santiago": "chile", "lima": "peru", "bogota": "colombia",
    "san jose": "costa rica", "panama city": "panama",
}
# A flight length is asked about the air time, not about the airport or the holiday: "how long is
# the flight to rome" was answered with how many days to spend there.
_FLIGHT_LENGTH_ASK = re.compile(
    r"\b(?:how long(?:'s| is) (?:the |a |my )?flight|how long does (?:the |a )?flight take|"
    r"how long to fly|how many hours (?:is|does|to) (?:a |the |my )?flight|"
    r"how many hours to fly|how long is the plane|is it a long flight|is it a long plane|"
    r"long flight to|flight time to|how long will (?:the |my )?flight take|"
    r"how long (?:does|do) it take to (?:fly|get)(?= to (?!the airport|an airport|the "
    r"terminal))|how long to fly to)\b")


# Where a flight starts, said just before the airport in a line: "from manchester", "out of
# bristol", "leaving dublin". A place said this way is where they set off, never where they go.
_STARTS_AT = re.compile(
    r"\b(?:from|out of|leaving|leave|depart(?:ing)? from|fly out of|flown? out of)\s+$")


def _a_place_the_flight_starts_at(named, clean, memory):
    """True when the conversation names this place as where the flight starts from.

    A line can say it ("is it a long flight from manchester"), and so can the turn before it
    ("we fly from manchester", then "how long is the flight"). The lookup that guards the first
    shape only read the line it was answering, so a departure airport said on a turn of its own
    became the place the flight was measured to: a trip to Rome came back "about an hour in the
    air from the UK to Manchester", and a trip to Florida the same. The store had the
    destination all along (`user.places` is Rome, the plan is "Rome in june"); what was missing
    was knowing that Manchester in the turn before was the airport and not the holiday.
    """
    texts = [clean]
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in (turns or [])[-3:]:
        if isinstance(turn, dict):
            texts.append(str(turn.get("user") or "").lower())
    for text in texts:
        match = re.search(r"(.{0,24})\b" + re.escape(named), text)
        if match and _STARTS_AT.search(match.group(1)):
            return True
    return False


def _a_place_said_after(named, clean):
    """A second place in the same line, once the start has been said: "from dublin to new york"."""
    return _find_in(clean.split(named, 1)[-1], AIR_HOURS_CITY)


def _the_destination_in_the_turns(memory):
    """The last place named in a turn or two, skipping one said as where the flight starts."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed((turns or [])[-3:]):
        if not isinstance(turn, dict):
            continue
        found = _find_in(str(turn.get("user") or "").lower(), AIR_HOURS_CITY)
        if found and not _a_place_the_flight_starts_at(found, "", {"turns": [turn]}):
            return found
    return None


def _flight_length(memory, understood):
    """How many hours in the air, for the place the line names."""
    clean = understood.get("clean", "") or ""
    named = _place_in(memory, understood, AIR_HOURS_CITY)
    if named and _a_place_the_flight_starts_at(named, clean, memory):
        # "is it a long flight from manchester", or the same said a turn before, names where the
        # flight starts: the hour to Manchester is no answer to a flight to Florida. The air time
        # asked about is to the place after it, then the plan's, then the last one before.
        named = (_a_place_said_after(named, clean)
                 or _place_in_the_plan(memory, AIR_HOURS_CITY)
                 or _the_destination_in_the_turns(memory))
    country = AIR_HOURS_CITY.get(named or "", "")
    if country in FLIGHT_HOURS:
        return _flight_hours_said(named.title(), FLIGHT_HOURS[country])
    city = _place_in(memory, understood, CITY_COUNTRY) or _place_in(memory, understood, CITIES)
    country = CITY_COUNTRY.get(city or "", "")
    if country in FLIGHT_HOURS:
        return _flight_hours_said(city.title(), FLIGHT_HOURS[country])
    place = _place_in(memory, understood, FLIGHT_HOURS)
    if place in FLIGHT_HOURS:
        return _flight_hours_said(place.title(), FLIGHT_HOURS[place])
    return ("The airline's timetable has the exact time, and the booking shows it to the minute. "
            "As a rule the air time is two to four hours across Europe, seven to eight to the "
            "east coast of America, and eleven to thirteen to Asia.")


def _flight_hours_said(name, hours):
    """The air time to a place, said with the airport at each end counted in."""
    in_the_air = _long_said(int(hours * 60))
    if hours >= 20:
        return (f"To {name} it is {in_the_air} in the air from the UK even non-stop, and a day of "
                f"it with a stop: book a night flight if you can sleep on a plane, and the return "
                f"leg is longer still.")
    return (f"About {in_the_air} in the air from the UK to {name}, plus the airport at both ends, "
            f"so half a day door to door. The booking shows the exact time.")


def _my_flight_time(memory, understood):
    """Where the time of their own flight is, for a bot that cannot see the booking."""
    clean = understood.get("clean", "")
    if re.search(r"\b(?:land|lands|landing)\b", clean):
        return ("The landing time is on your ticket and in the airline's app, and it is the local "
                "time where you land rather than the time back home. It moves with the flight, so "
                "the live arrival time in the app is the one to trust on the day.")
    if re.search(r"\b(?:gate|terminal)\b", clean):
        return ("The gate and terminal are on your boarding pass and in the airline's app, and "
                "they can change on the day: the app and the departure boards after security are "
                "the "
                "ones to trust, and the gate is worth checking once more when you sit down.")
    told = _flight_told(memory)
    if told:
        clock, day = told
        said = _a_clock(clock["hour"], clock["minute"], clock)
        there = _a_clock(*_at_a_time(clock, -120), clock)
        return (f"You told me your flight is at {said}{day}, so be at the airport by {there}: two "
                f"hours before departure is the safe rule. The drive comes on top, so half an "
                f"hour on the road means leaving home at "
                f"{_a_clock(*_at_a_time(clock, -150), clock)}.")
    return ("I can't see your booking, so I can't look it up: the time is on your ticket and in "
            "the airline's app, in the local time of the airport you fly from. Tell me the time "
            "and I'll work back to when you need to leave.")


_DAY_SAID = re.compile(r"\b(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|"
                       r"sunday|tomorrow|tonight|this morning|this evening)\b")


def _flight_told(memory):
    """The flight time they gave a turn or two ago, with the day if they named one.

    "my flight is at 7 on friday" then "what time is my flight" is a question the conversation
    already answered: repeating it back is better than saying the booking cannot be seen. The
    plan the store keeps is asked first, because it is where a correction has already landed:
    "my flight is at 6am" then "sorry, its at 8pm" is a plan at 8pm, and reading the turns for it
    would quote the 6am back and send them to the airport two hours early.
    """
    held = _the_plan_told(memory)
    if held:
        return held
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed(list(turns or [])[-3:]):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "").lower()
        if not _FLIGHT_SAID.search(said):
            continue
        clock = next((one for one in _clock_pairs(said) if one["role"] == "flight"), None)
        if clock is None:
            continue
        day = _DAY_SAID.search(said)
        return clock, (f" on {day.group(1).title()}" if day else "")
    return None


def _the_plan_told(memory):
    """The flight clock the store keeps as a plan, with its day, or None.

    A plan is one sentence the store has already put right ("my flight is at 6am" corrected to
    "flight at 8pm"), so it is read the same way a turn is: the clock that belongs to the flight
    in it, and the day if the sentence has one.
    """
    user = memory.get("user") if isinstance(memory, dict) else None
    if not isinstance(user, dict):
        return None
    plans = user.get("plans")
    if not isinstance(plans, list):
        plans = [user.get("plan")]
    for plan in reversed([one for one in plans if isinstance(one, str) and one.strip()]):
        low = plan.lower()
        if not _FLIGHT_SAID.search(low):
            continue
        clock = next((one for one in _clock_pairs(low) if one["role"] == "flight"), None)
        if clock is None:
            continue
        day = _DAY_SAID.search(low)
        return clock, (f" on {day.group(1).title()}" if day else "")
    return None


def _clock(hour, minute=0):
    """A 24-hour time as people say it: "9am", "4pm", "7.30pm"."""
    hanging = "am" if hour % 24 < 12 else "pm"
    twelve = hour % 12 or 12
    tail = f".{minute:02d}" if minute else ""
    return f"{twelve}{tail}{hanging}"


def _uk_summer(day=None):
    """True when the UK is on summer time. The clocks go forward on the last Sunday of March and
    back on the last Sunday of October."""
    day = day or datetime.datetime.now(datetime.timezone.utc).date()
    if 4 <= day.month <= 9:
        return True
    if day.month in (3, 10):
        # The last Sunday of the month, counted back from the end.
        last = day.replace(day=28) + datetime.timedelta(days=4)
        last_sunday = last - datetime.timedelta(days=last.weekday() + 1)
        return day >= last_sunday if day.month == 3 else day < last_sunday
    return False


def _now_there(hours):
    """The clock on the wall at the other end, given the hours it is ahead of the UK."""
    here = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        hours=1 if _uk_summer() else 0)
    there = here + datetime.timedelta(hours=hours)
    return _clock(there.hour, there.minute), _clock(here.hour, here.minute)


# The clock on this wall. "What time is it" with no city in it named nothing the time-there row
# could answer, so it went to the search hedge - the one line in the chat where the honest answer
# is a number the bot already has, because it reads the clock to answer "what time is it in
# tokyo". A time of day is a different question and the words give it away: "what time do i take
# my pill", "what time does the shop shut", "what time is kick off".
_WHEN_IT_IS = re.compile(
    r"\b(?:what(?:'s|\s+is)?\s+the\s+time|what\s+time\s+is\s+it|whats\s+the\s+time|what\s+time\s+is\s+it\s+there|"
    r"the\s+time\s+(?:now|please|there)|got\s+the\s+time|have\s+you\s+got\s+the\s+time|"
    r"know\s+the\s+time|what\s+o'?clock|"
    # the same question wrapped in a please: "do you know the time", "can you tell me the time",
    # "do you have the time" - three shapes people type, and all three were the search hedge
    r"(?:do|did|can|could|would)\s+you\s+(?:have|know|tell\s+me|give\s+me)\s+the\s+time|"
    r"tell\s+me\s+the\s+time)\b")
# A clock asked for and a time of day asked for look the same until the tail of the line: these
# are the tails that make it a time of day.
# The auxiliary only counts when it comes straight after "time": "what time do i take my pill"
# is a time of day, and "do you know the time" is the clock with a please in front of it.
_TIME_OF_DAY = re.compile(
    r"\b(?:what|which)\s+time\s+(?:do|does|did|should|shall|will|would|can|could|must)\b|"
    r"\b(?:to|for)\s+(?:take|takes|"
    r"taking|go|going|leave|leaves|leaving|start|starts|starting|finish|finishes|finishing|end|ends|"
    r"ending|eat|eating|bed|sleep|sleeping|wake|waking|shut|shuts|shutting|open|opens|opening|"
    r"close|closes|closing|call|calling|ring|ringing)\b|\b(?:pills?|tablets?|medication|meds|dose|"
    r"insulin|appointment|kick\s*off|kickoff|sunrise|sunset|shift|bus|train|ferry|flight|meeting|"
    r"match|game|film|movie|show|class|lesson|interview|closes?|opens?)\b")


# "all the time" says how often, not what the clock says. `_WHEN_IT_IS` matches "the time now"
# inside it, so "my laptop fan is loud all the time now" was answered with "It is 8.01pm here, on
# the UK clock" - a clock nobody asked for. A line that says how often is not asking the time.
_HOW_OFTEN = re.compile(
    r"\b(?:all|most|half|some|much|none|part|lots?|a\s+lot|any)\s+(?:of\s+)?the\s+time\b", re.I)
_TIME_TO_DO_SOMETHING = re.compile(r"\bthe\s+time\s+to\s+\w+")
_clock_here_doc = None


def _the_clock_here(memory, understood):
    """"What time is it" with no place named: the clock on the wall the bot reads. Else None."""
    clean = understood.get("clean", "")
    if not _WHEN_IT_IS.search(clean):
        return None
    # "do you have the time to help me with my cv" is asking whether the bot is free, not what the
    # clock says: `the time to <verb>` is a plan, and it keeps its own answer.
    if _HOW_OFTEN.search(clean):
        return None  # how often it happens, not what the clock says
    if _TIME_TO_DO_SOMETHING.search(clean):
        return None
    if _TIME_OF_DAY.search(clean):
        return None
    if _place_in(memory, understood, TIME_ZONES) or _find_in(clean, MULTI_ZONES):
        return None  # a place is named, and the time-there row says what the clock is there
    here = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        hours=1 if _uk_summer() else 0)
    return (f"It is {_clock(here.hour, here.minute)} here, on the UK clock - if you are somewhere "
            f"else your own clock is the one to trust.")


# A hotel line is not always the area question, and the row owns the word "a hotel" because that
# is how it is asked: "a hotel in lisbon in june". What a line does with the hotel decides it.
# When to book it, what it costs, how to find one and whether to book at all are different
# questions with different owners, and this row answered all four with the three areas of the
# city: "when should i book a hotel in rome" got Monti, Trastevere and Prati.
_NOT_WHERE_ASKS = frozenset(("when", "how_long", "how_much", "how", "steps", "yesno", "why"))


def _asks_where(understood):
    """True when the line asks where to stay rather than when, how much or whether to."""
    asks = (understood or {}).get("asks") or ()
    return not any(ask in _NOT_WHERE_ASKS for ask in asks)


def _where_to_stay(memory, understood):
    """"Best area to stay in paris" - the three areas a city is worth splitting between."""
    if not _asks_where(understood):
        return None
    place = _place_in(memory, understood, CITY_AREA)
    if not place:
        return None
    return f"Stay in {CITY_AREA[place]}."


# Roughly thirty cities have an area worth naming, and everyone else's town - Cleethorpes,
# Skegness, Tenby, Blackpool, Falmouth - got "I don't know enough to answer that honestly". The
# same few rules hold in any town, so a place that is not in the table still gets an answer, and
# the paragraph says how to pick rather than pretending to know streets it has never seen.
TOWN_STAY = (
    "Book close to the middle of town and a street or two back from the main road: the station, "
    "the food and the evening are then walkable, and the rooms just off the front are quieter and "
    "cheaper. At the seaside that means a street back from the front rather than the front itself. "
    "Look at the map for a bar or a through road under the window, check the last bus or train if "
    "you will be out late, and book somewhere with free cancellation so you can move if the area "
    "is not what you hoped.")


# When to book it, what it costs, how to find one and whether to book at all are four different
# questions, and none of them is the area to stay in - "how much is a hotel in skegness" is a
# price, not a street. "a hotel" is one of the asking shapes, so the row has to look at what the
# line does with it.
_NOT_WHERE_ASKS = frozenset(("when", "how_long", "how_much", "how", "steps", "yesno", "why"))


_A_CAR_NIGHT = re.compile(
    r"\b(?:in|inside)\s+(?:my|the|our|his|her)\s+(?:car|van|motorhome|camper|campervan|truck)\b"
    r"|\b(?:tent|camping|tourer|caravan|motorhome|campervan|camper)\b")


# When and how to sleep is a sleep question even when the line says "where": "where do i sleep on
# a night shift" and "where should i sleep after a night shift" are the sleep card's lines, and
# the stay shape read them as a town to book in.
_A_SHIFT_WORK = re.compile(
    r"\bshift(?:s|work|work\s+pattern)?\b|\bon nights?\b|\bworking nights?\b|\bwork nights?\b"
    r"|\bnight\s*worker\b|\bday\s+shift\b")


_A_FLIGHT_WORD = re.compile(
    r"\b(?:airport|airports|terminal|flight|flights|flying|heathrow|gatwick|stansted|luton)\b")


_A_STAY_ASK = re.compile(
    r"\b(?:where|which)\b[^.!?]{0,30}\b(?:stay|staying|sleep|sleeping|kip|hotel|book|night)\b"
    r"|\b(?:hotel|hotels|place|somewhere|room)\b[^.!?]{0,25}\b(?:near|at|by|close to|around)\b"
    r"[^.!?]{0,20}\b(?:airport|terminal|heathrow|gatwick|stansted|luton)\b")


# The shapes that ask where to stay: the where/which ask, the "an area to stay in" ask, and the
# "a hotel near the airport" ask. A line can hold the word hotel without asking any of them -
# "i want to leave a bad review for a hotel" holds it and is a review - so the town paragraph
# reads the shape, not the word.
_A_STAY_PLACE_ASK = re.compile(
    r"\b(?:where|which)\b[^.!?]{0,30}\b(?:stay|staying|sleep|sleeping|kip|hotel|book|night)\b"
    r"|\b(?:area|place|somewhere|part of town|neighbourhood|neighborhood|district)\b[^.!?]{0,20}"
    r"\b(?:to stay|stay in|staying in|to sleep|for the night)\b"
    r"|\b(?:hotel|hotels|b&b|hostel|guest house|place|somewhere|room)\b[^.!?]{0,25}"
    r"\b(?:near|at|by|close to|around|in)\b[^.!?]{0,20}"
    r"\b(?:airport|terminal|heathrow|gatwick|stansted|luton|beach|sea|seafront|centre|center|"
    r"station|town|city|old town|harbour|marina|lake|coast)\b")


def _a_night_near_the_airport(understood):
    """True when the line is a booking for the night, not an airport chore.

    "Where should i stay near heathrow", "a hotel by the terminal", "where do i sleep before an
    early flight" are the booking. A security queue, a lost bag and a coffee price name the same
    airport and are not.
    """
    clean = (understood or {}).get("clean", "") or ""
    return bool(_A_STAY_ASK.search(clean))


def _a_town_stay(memory, understood):
    """The paragraph for a town nobody has a card for, or nothing when a city is in the chat.

    "We are thinking about tokyo in april" then "where should we stay" names no city in the
    second line, and the city is what the person means: the row that reads it out of the
    conversation answers with its three areas, and this paragraph must stand aside for it.
    """
    if _place_in(memory, understood, CITY_AREA):
        return None
    return TOWN_STAY


def _a_town_stay_line(understood):
    """True when the line asks where to stay, and names no city the table knows.

    The city rows answer their own cities, so this paragraph stands down the moment one of them
    is named: it is the answer for a town nobody has written a card for. It also stands down on a
    line that asks when, how much or whether, because the same three words are in those lines.
    """
    if any(ask in _NOT_WHERE_ASKS for ask in ((understood or {}).get("asks") or ())):
        return False
    # A flight is not a town: the night before a departure has its own row, and the general
    # paragraph about a market square tells nobody where to sleep before a 6am check-in.
    if _A_FLIGHT_WORD.search((understood or {}).get("clean", "") or ""):
        return False
    # Sleeping in the car is a car question, not somewhere to book.
    if _A_CAR_NIGHT.search((understood or {}).get("clean", "") or ""):
        return False
    # A shift is a sleep-hygiene question, not a town: the sleep card says when and how to sleep
    # in the day, and this paragraph named it a seaside front.
    if _A_SHIFT_WORK.search((understood or {}).get("clean", "") or ""):
        return False
    # "i want to leave a bad review for a hotel" holds the word hotel and asks nothing about
    # staying; only a line with a stay shape gets this paragraph.
    if not _A_STAY_PLACE_ASK.search((understood or {}).get("clean", "") or ""):
        return False
    return _find_in(understood.get("clean", "") or "", CITY_AREA) is None


def _time_zone(memory, understood):
    """"What time is it in tokyo" - the clock there, or the difference to here."""
    clean = understood.get("clean", "")
    if re.search(r"\b(fly|flight|flying|flights|drive|driving|walk|walking|train|bus|queue|"
                 r"check in|checking|passport|shops|dinner|kick off|kickoff|lunch|sunrise|"
                 r"sunset|tablets|bed|check out|checkout)\b", clean):
        return None  # a time of day there, not the clock
    place = _place_in(memory, understood, TIME_ZONES)
    if place is None:
        wide = _find_in(clean, MULTI_ZONES)
        if wide is None:
            return None
        return f"{wide.title()} has more than one clock: {MULTI_ZONES[wide]}."
    winter, summer = TIME_ZONES[place]
    name = place.title()

    def size(hours):
        whole = int(abs(hours))
        word = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                "eleven", "twelve", "thirteen", "fourteen")
        if abs(hours) != whole:
            return f"{word[whole - 1]} and a half hours"
        return f"{word[whole - 1]} hour" if whole == 1 else f"{word[whole - 1]} hours"

    gap = summer if _uk_summer() else winter
    given = re.search(r"\b(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)\b", clean)
    if given and re.search(r"\bhere\b", clean):
        # "what time is it in new york when its 3pm here" asks for the sum, not the clock.
        hour = int(given.group(1)) % 12 + (12 if given.group(3) == "pm" else 0)
        minute = int(given.group(2) or 0)
        there_given = _clock(hour + int(gap), minute + (30 if gap % 1 else 0))
        return (f"{given.group(1)}{':' + given.group(2) if given.group(2) else ''}"
                f"{given.group(3)} here is {there_given} in {name}.")
    there, here = _now_there(gap)
    if winter == 0 and summer == 0:
        if place in ("uk", "the uk", "britain", "england", "scotland", "wales"):
            return f"It is {here} here, and the same clock in the UK."
        return (f"{name} runs on the same clock as the UK, so it is {there} there now and "
                f"{here} here.")
    asked_how_far = re.search(r"hours|difference|ahead|behind|zone", clean)
    if winter == summer:
        if asked_how_far:
            return (f"{name} is {size(winter)} {'ahead of' if winter > 0 else 'behind'} the UK all "
                    f"year, so it is {there} there now and {here} here.")
        return f"It is {there} in {name} now, and {here} here."
    if asked_how_far:
        return (f"{name} is {size(winter)} ahead of the UK in winter and {size(summer)} in summer, "
                f"because its clocks do not move when ours do: it is {there} there now and {here} "
                f"here.")
    way = "ahead of" if winter > 0 else "behind"
    return (f"It is {there} in {name} now, and {here} here: {name} is "
            f"{size(summer) if _uk_summer() else size(winter)} {way} us at the moment.")


# "when is the best time to book it" is about how far ahead, not which month is nicest, and the
# visit note is the wrong answer to it. Booking something that is not the trip names it ("book a
# restaurant in Rome", "book tickets for a show"), and those keep the answer they had.
BOOK_ASK = re.compile(r"\b(?:book|booking|booked|reserve|reserving|reservation)\b", re.I)
BOOK_NOT_THE_TRIP = re.compile(
    r"\b(?:restaurant|table|dinner|lunch|breakfast|meal|show|concert|gig|cinema|film|"
    r"appointment|doctor|dentist|haircut|taxi|cab|car|van|hire|tour|tickets? for)\b", re.I)
_LONG_MONTH = ("january", "february", "march", "april", "may", "june", "july", "august",
               "september", "october", "november", "december")


def _plan_month(memory):
    """The month of the trip they said they are taking, when they gave one."""
    mine = memory.get("user") if isinstance(memory, dict) else None
    plan = str((mine or {}).get("plan") or "").lower()
    for name in sorted(MONTHS, key=len, reverse=True):
        if re.search(r"\b" + name + r"\b", plan):
            return _LONG_MONTH[MONTHS[name] - 1]
    return None


def _when_to_book(memory):
    """How far ahead to book, dated to the trip when the chat knows the month.

    "six to eight weeks ahead" is the answer to the booking question; a trip in May is booked by
    March, so the plan they gave turns the general window into the date it means for them.
    """
    window = ("six to eight weeks ahead for short-haul and two to four months for long-haul, "
              "with Tuesday and Wednesday usually the cheapest days to fly")
    month = _plan_month(memory)
    if not month:
        return "Book " + window + "."
    earlier = _LONG_MONTH[(MONTHS[month] - 3) % 12]
    return ("For a trip in " + month.title() + ", book by mid-" + earlier.title() + ": " + window
            + ".")


def _best_time(memory, understood):
    clean = understood.get("clean", "")
    # "is Lisbon worth visiting" asks what there is there, so the guide takes it; with a month
    # in the line the same words ask about the time of year, which is this table's question.
    if _WORTH_ASK.search(clean) and not any(_time_terms(clean, loose=True)):
        return None
    # A booking ask is not a when-to-go ask. "when is the best time to book it", after they said
    # they are going in May, came back with the month-by-month visit note: a concrete answer to a
    # question nobody asked, which is worse than an honest short one. They want how far ahead,
    # and the plan they already gave says which date that lands on.
    if BOOK_ASK.search(clean) and not BOOK_NOT_THE_TRIP.search(clean):
        return _when_to_book(memory)
    # A city has its own row, because its country's row is about the country: Porto is not
    # the Algarve and Edinburgh is not the Highlands.
    city = _place_in(memory, understood, WHEN_TO_GO)
    if city:
        return f"For {city.title()}: {WHEN_TO_GO[city]}"
    place = _place_in(memory, understood, BEST_TIME)
    if not place:
        return None
    return f"For {place.title()}: {BEST_TIME[place]}"

# ---- what there is to do in a region -----------------------------------------
#
# "What should we do in cornwall", "things to do in the lake district" and "best beaches in
# devon" were all the search hedge. The when-to-go table knows these five regions and nothing
# else in the file did, so a person planning the commonest British holiday got nothing to act
# on. One card per region, and the beaches as their own line, because "best beaches in devon"
# is a narrower question than "what should we do in devon" and wants a shorter answer.
REGION_DAYS = {
    "cornwall": ("St Ives for the beach and the Tate, Padstow for the food and the Camel trail, "
                 "the Eden Project's two biomes near St Austell, the Minack theatre cut into the "
                 "cliff above Porthcurno, and Tintagel for the Arthur legend. The coast path "
                 "between St Ives and Padstow is the day out that beats all of them."),
    "devon": ("Dartmoor for the ponies and the tors, the South West Coast Path in either "
              "direction, Torquay and Paignton for the sand and the steam train to Dartmouth, "
              "and Exeter for the cathedral and the quay. Salcombe and Woolacombe are the two "
              "beaches people drive for."),
    "lake district": ("Windermere for the steamer and the low walks, Keswick for Catbells, which "
                      "is the best short climb in the country, Dove Cottage in Grasmere for the "
                      "Wordsworth, and the Honister pass for the slate mine. Scafell Pike is the "
                      "hill, and the Ullswater steamer is the easy day."),
    "norfolk": ("The Broads by boat from Wroxham, the seal trip from Blakeney Point, Holkham for "
                "the beach behind the pines, Sandringham if they like the royal houses, and "
                "Norwich for the cathedral and Elm Hill. Cromer for crab and the pier."),
    "yorkshire": ("Malham Cove and Gordale Scar in the Dales, Whitby for the abbey and the "
                  "Dracula steps, Robin Hood's Bay for the village at the bottom of the hill, "
                  "the North Yorkshire Moors railway from Pickering, and York for the Minster "
                  "and the Shambles."),
    "scotland": ("Edinburgh for the castle and Arthur's Seat, then the Highlands: Glencoe for "
                 "the glen, Skye for the Quiraing and the Fairy Pools, Glenfinnan for the "
                 "viaduct, and the Cairngorms for a hill day. A car is what makes it, since the "
                 "trains only reach the edges."),
    "wales": ("Snowdonia for Snowdon by the Pyg track and Betws-y-Coed for the slate, "
              "Pembrokeshire for the coast path and the beaches at Barafundle and Whitesands, "
              "and the Brecon Beacons for the waterfalls walk. Cardiff for the castle and the "
              "bay if the weather turns."),
    "peak district": ("Mam Tor and the Great Ridge for the classic day, Chatsworth for the "
                      "house and the garden, Dovedale for the stepping stones, and Bakewell for "
                      "the pudding. Edale is the station if you come by train."),
    "cotswolds": ("Bourton-on-the-Water for the river running through the village, Castle Combe "
                  "for the street everyone photographs, Chipping Campden and Broadway for the "
                  "stone, and the Slaughters for a walk between them. It is a place for driving "
                  "and stopping rather than one long walk."),
    "isle of wight": ("The Needles and Alum Bay, Shanklin and Ventnor for sand and the coastal "
                      "path, Carisbrooke Castle, and the cycle path that goes round the island. "
                      "It is small enough for a long weekend."),
    "dorset": ("The Jurassic Coast: Lulworth Cove and Durdle Door for the walk, Chesil Beach "
               "and Portland, Swanage for the steam train to Corfe Castle, and Studland for the "
               "sand. The fossil beaches are west of Charmouth."),
    "northumberland": ("Hadrian's Wall at Housesteads and Vindolanda, Alnwick Castle and the "
                       "garden, Bamburgh and its beach, and Lindisfarne across the causeway at "
                       "low tide. The dark skies park is the evening."),
}

REGION_BEACHES = {
    "cornwall": ("Porthmeor at St Ives for surf and a town behind it, Kynance Cove on the "
                 "Lizard for the water, and Sennen or Watergate Bay for space. Car parks are "
                 "full by ten in August, so go early or go in the evening."),
    "devon": ("Woolacombe for surf and sand that goes on, Blackpool Sands near Dartmouth for "
              "the shelter and the cafe, and Bantham for the walk to the village. The Exmouth "
              "end is sand and shallow, which is the one for small children."),
    "norfolk": ("Holkham for the pines and the space, Wells-next-the-sea for the beach huts "
                "and the pine walk, and Cromer for the pier and the crabs."),
    "yorkshire": ("Whitby for sand and the abbey above it, Robin Hood's Bay for rock pools at "
                  "low tide, and Filey for the long flat one that suits children."),
    "wales": ("Barafundle in Pembrokeshire for the walk down through the woods, Whitesands "
              "near St Davids for surf, and Tenby for a harbour and a town. The coast path "
              "links them if you want a leg of it."),
    "dorset": ("Studland for sand and the nature reserve behind it, Weymouth for the long "
               "shallow bay, and Charmouth for fossils at low tide after a storm."),
    "northumberland": ("Bamburgh for the castle above the sand, Embleton for the dunes, and "
                       "Alnmouth for a village at the end of the beach."),
    "isle of wight": ("Sandown and Shanklin for sand and a promenade, Compton Bay for surf "
                      "and the cliffs, and Bembridge for rock pools when the tide is out."),
}

# The regions whose names need "the" in front, so a reply does not read "In Isle Of Wight".
REGION_NAMES = {
    "isle of wight": "on the Isle of Wight",
    "peak district": "the Peak District",
    "cotswolds": "the Cotswolds",
    "lake district": "the Lake District",
}


def _region_lead(region):
    """The name in a sentence: "In Cornwall", "In the Peak District", "On the Isle of Wight"."""
    named = REGION_NAMES.get(region)
    if named:
        return named[0].upper() + named[1:] if named.startswith("on") else f"In {named}"
    return f"In {region.title()}"


# The towns people name instead of the region: nobody asks what to do in "Cornwall" when they
# are staying in St Ives. Each maps to the region whose card answers it.
REGION_TOWNS = {
    "st ives": "cornwall", "padstow": "cornwall", "newquay": "cornwall",
    "falmouth": "cornwall", "penzance": "cornwall", "tintagel": "cornwall",
    "st austell": "cornwall", "kynance": "cornwall", "porthcurno": "cornwall",
    "torquay": "devon", "dartmouth": "devon", "salcombe": "devon", "woolacombe": "devon",
    "ilfracombe": "devon", "paignton": "devon", "dartmoor": "devon",
    "keswick": "lake district", "windermere": "lake district", "ambleside": "lake district",
    "coniston": "lake district", "grasmere": "lake district", "kendal": "lake district",
    "ullswater": "lake district",
    "cromer": "norfolk", "wroxham": "norfolk", "hunstanton": "norfolk",
    "blakeney": "norfolk", "holkham": "norfolk",
    "whitby": "yorkshire", "malham": "yorkshire", "ripon": "yorkshire",
    "scarborough": "yorkshire", "skipton": "yorkshire", "hawes": "yorkshire",
    "helmsley": "yorkshire",
    "highlands": "scotland", "skye": "scotland", "glencoe": "scotland",
    "fort william": "scotland", "inverness": "scotland", "oban": "scotland",
    "cairngorms": "scotland", "edinburgh": None,
    "snowdonia": "wales", "pembrokeshire": "wales", "brecon": "wales",
    "betws-y-coed": "wales", "barafundle": "wales", "anglesey": "wales",
    "mam tor": "peak district", "bakewell": "peak district", "buxton": "peak district",
    "dovedale": "peak district", "chatsworth": "peak district", "edale": "peak district",
    "bourton-on-the-water": "cotswolds", "castle combe": "cotswolds",
    "chipping campden": "cotswolds", "moreton-in-marsh": "cotswolds",
    # not "the needles": a person holding knitting needles asked "what should i do with the
    # needles" and got a holiday brochure. Nobody names the island by its rocks alone.
    "shanklin": "isle of wight", "ventnor": "isle of wight",
    "lulworth": "dorset", "durdle door": "dorset", "swanage": "dorset",
    "bamburgh": "northumberland", "alnwick": "northumberland",
    "lindisfarne": "northumberland", "housesteads": "northumberland",
}

# A place that has a card of its own is not a region question: Edinburgh's guide is the city
# guide, and answering "what should we do in edinburgh" with the Highlands would be the wrong
# country half the time.
REGION_TOWNS = {name: region for name, region in REGION_TOWNS.items() if region}

# Every name that leads to a region card: the region itself, and the towns inside it.
REGION_PLACES = dict({name: name for name in REGION_DAYS}, **REGION_TOWNS)

# The ask a "what is there to do" question wears. "worth a visit" is here because "is padstow
# worth a visit" is the same question, and the when-to-go row stands down for it when no month
# is named.
_DAYS_ASK = ("what should we do", "what should i do", "what can we do", "what is there to do",
             "whats there to do", "what is there", "whats there", "things to do", "thing to do",
             "things to see", "anything to do", "worth a visit", "worth visiting",
             "where should we go", "day trips", "day trip", "must see", "must do",
             "what to see", "what to do", "best beach", "best beaches", "good beach",
             "good beaches", "which beach", "a beach", "beaches", "beach")

_A_BEACH = re.compile(r"\bbeach(?:es)?\b", re.I)


def _region_days(memory, understood):
    """What there is to do in a named region, or the beach answer when that is the ask."""
    clean = str((understood or {}).get("clean") or "").lower()
    # A month in the line is the when-to-go question, and this card has nothing to say about
    # the weather: "is it worth visiting skye in january" is that row's, or a search.
    if any(re.search(r"\b%s\b" % re.escape(name), clean) for name in MONTHS):
        return None
    named = _find_in(clean, REGION_PLACES)
    if not named:
        return None
    region = REGION_PLACES[named]
    if _A_BEACH.search(clean):
        # The Lakes have no beach card, and their answer is a walk: rather than say "no beaches",
        # let the row that does hold beaches have the turn.
        return REGION_BEACHES.get(region)
    return f"{_region_lead(region)}: {REGION_DAYS[region]}"


# The first hour after a train, a coach or a ferry is four questions in the same clothes: how do I
# get to where I am staying, what do I do when it is late, how do I get about once I am there, and
# which station do I want. The airport rows answer these for a named airport; with no city named,
# every one of them was a hedge, a hotel-booking note (for "from the station to my hotel"), the
# Spanish phrase card (for "from the train station to the hotel") or the coach-fares card.
_ARRIVAL_KINDS = ("station", "train station", "railway station", "coach station", "bus station",
                  "port", "ferry port", "terminal", "metro", "tram", "bus stop", "ferry",
                  "platform", "interchange", "land", "new city")

_ARRIVING_ASK = ("how do i get", "how do i go", "how to get", "how will i get", "best way",
                 "best to get", "get to my hotel", "get to the hotel", "to the hotel",
                 "to my hotel", "into town", "to the centre", "to the city centre", "city centre",
                 "to the town", "get to town", "where do i get", "is there a bus", "is there a train",
                 "is there a metro", "is there a tram", "is there a taxi", "how do i use",
                 "how do i plan", "get around", "getting around", "get round", "getting round",
                 "arrive at", "arriving at", "land at", "landing at", "which station",
                 "what station", "closest station", "nearest station", "which stop",
                 "last train", "last metro", "last bus", "travel card", "day ticket",
                 "how much is a taxi", "what does a taxi cost", "taxi cost", "taxi fare")

_ARRIVAL_LATE = ("late", "late at night", "night", "midnight", "dark", "after 10", "after 11",
                 "10pm", "11pm", "12pm", "1am", "00:", "22:", "23:")

_ARRIVAL_ABOUT = ("get around", "getting around", "get round", "getting round", "metro",
                  "tram", "subway", "underground", "bus pass", "travel card", "day ticket",
                  "metro card", "contactless", "how do i use", "how do i plan", "ticket machine")

_ARRIVAL_FARE_ASK = ("how much is a taxi", "what does a taxi cost", "taxi cost", "taxi fare",
                     "how much for a taxi", "what will a taxi cost")

_ARRIVAL_FARE = (
    "From the main station to the centre a taxi is usually 15 to 25 euros in a European city and "
    "5 to 15 in a smaller town, and the official rank outside the main exit charges the meter or "
    "the fixed fare: check the posted figure or the app price before you get in. The metro, tram "
    "or express bus is 2 to 5 euros for the same trip, so take that with a case you can wheel and "
    "keep the taxi for a late arrival or a lot of luggage.")

_ARRIVAL_PICK = ("which station", "what station", "closest station", "nearest station",
                 "which stop", "closest to", "nearest to", "closest one")

_ARRIVAL_TOWN = (
    # The first sentence has to work for both shapes this row answers - "how do i get from the
    # station to my hotel" and "whats the best way from the station into town" - so it names the
    # ride and not the bed. It used to open "Get to your bed on the metro", which is a sentence
    # about lying down that arrived as the answer to a question about a train.
    "From the main station, take the metro, tram or airport-style express bus and leave the taxi "
    "for the "
    "cases and the late hour: in most European cities the ride from the main station to the centre "
    "is 2 to 5 euros and a taxi is 15 to 25. Buy the ticket at the machine or on the app before "
    "you board, walk to the official rank outside the main exit rather than taking an offer from "
    "someone inside, and have the address written down or on the phone screen.")

_ARRIVAL_LATE_NOTE = (
    "Check the last metro or bus before you travel - in most cities it is between half eleven and "
    "half twelve - and if it has gone, take the rank outside the station or ring the hotel and ask "
    "them to book a car, rather than getting in with someone who offers. Tell the hotel you will "
    "be late so they hold the room and give you the door code, and keep 20 euros of cash on you "
    "for the ride.")

_ARRIVAL_ABOUT_NOTE = (
    "Tap a contactless bank card or your phone if the city takes it, and you pay the local fare "
    "with no ticket to buy or validate; otherwise get a day or three-day travel card from the "
    "machine, which usually pays off after three or four rides. Validate the ticket or tap in at "
    "the start of every journey, because an unvalidated one counts as no ticket, and keep the same "
    "card for the way back so the daily cap applies.")

_ARRIVAL_PICK_NOTE = (
    "Pick the station named for the part you are staying in - the old town, the centre, the "
    "harbour - rather than the city's biggest one, and put both on a route planner before you "
    "book: the walk from the door to the hotel is the figure that decides it. A station with the "
    "city name plus a district in its name is usually the one closest to the old town.")


# A fare question about a journey between two cities is cheap-trains' question, not the first hour
# after a train. The bare "how do i get" is an arrival ask and "train" is one of its kinds, so
# "how do i get cheap train tickets" was answered with the metro-and-taxi note about getting from
# the station into town. The same words are the right ask when the line also says where it is
# going - the centre, the hotel, the last train home - so those lines keep the arrival note.
_FARES_ASK = ("cheap", "cheaper", "cheapest", "advance", "railcard", "save money", "save on",
              "best price", "cheapest way to", "how much is a train ticket",
              "how much are train tickets", "how much is a rail ticket")
_FARES_GOING_SOMEWHERE = ("to the centre", "to the city centre", "city centre", "into town",
                          "to the town", "to the hotel", "to my hotel", "from the station",
                          "from the airport", "which station", "what station", "last train",
                          "last metro", "last bus", "get to my hotel", "get to the hotel")


def _arriving(memory, understood):
    clean = (understood.get("clean") or "").lower()
    if any(w in clean for w in _FARES_ASK) and not any(w in clean for w in _FARES_GOING_SOMEWHERE):
        return None
    # An airport has rows of its own that know the fare and the bus for the city named on the
    # line: "how much is a taxi from Dublin airport to the centre" was answered with this row's
    # general 15 to 25 euros instead of "a taxi is EUR25-30 from Dublin".
    if "airport" in clean or "flight" in clean or "fly" in clean:
        return None
    if any(k in clean for k in _ARRIVAL_FARE_ASK):
        return _ARRIVAL_FARE
    if any(k in clean for k in _ARRIVAL_PICK):
        return _ARRIVAL_PICK_NOTE
    if any(k in clean for k in _ARRIVAL_ABOUT):
        return _ARRIVAL_ABOUT_NOTE
    if any(k in clean for k in _ARRIVAL_LATE):
        return _ARRIVAL_LATE_NOTE
    return _ARRIVAL_TOWN

# ---- an airport with no city named -----------------------------------------------------------
#
# "how do i get from the airport to the city", "whats the cheapest way from the airport to the city",
# "how do i get to my hotel from the airport", "is there a train from the airport", "how do i get from
# the airport to the port" and "how do i get to the airport for an early flight" were all search
# hedges, because AIRPORT_TRANSFER can only answer for an airport it knows. The method is the same
# everywhere and it is what people want before they fly, so the reply answers the general question and
# keeps the named table for when a city is said. Which of the methods the line wants is a table read
# by one function: the shape of the ask picks the paragraph, not one phrasing.
_AIRPORT_TO_THE_AIRPORT = (
    "to the airport", "to the airport for", "for an early flight", "early flight", "early morning "
    "flight", "get to the airport", "getting to the airport", "airport in the morning",
    "before my flight", "before an early flight", "at 5am", "at 6am", "at 4am")
_AIRPORT_CHEAPEST = ("cheapest", "cheaper", "cheap way", "budget", "least expensive", "save money",
                     "cheapest way")
_AIRPORT_FASTEST = ("best way", "quickest", "fastest", "easiest", "best", "quick")
_AIRPORT_TRAIN = ("is there a train", "train from", "train to", "metro", "subway", "rail",
                  "is there a bus", "bus from", "underground")
_AIRPORT_HOTEL = ("my hotel", "the hotel", "hotel from", "to the hotel")
_AIRPORT_PORT = ("the port", "to the port", "cruise port", "cruise", "the ship", "my ship",
                 "to the ship")

_AIRPORT_WAY_IN = (
    "Check the airport's own website before you fly, on its 'to and from the airport' page: it lists "
    "the official ways into the centre with the price and the running time, which saves guessing at "
    "a machine after a flight. In most cities the train or metro is the quickest and cheapest way in, "
    "so follow the signs for trains or rail rather than the taxi rank; the airport bus or shuttle is "
    "cheaper and slower, and a taxi is the most expensive and the easiest with luggage or after dark. "
    "Buy the ticket before you board, and ignore anyone inside the terminal offering a taxi.")
_AIRPORT_CHEAPEST_REPLY = (
    "The cheapest way in is nearly always the train, the metro or the airport bus, and which of the "
    "three depends on the airport: its own 'to and from' page lists every option with the price, and "
    "it is worth a look before you fly. If the train or metro goes near where you are staying, take "
    "it; if not, take the bus to the main station and carry on from there. A taxi is the last choice "
    "for the money, and the most expensive thing you can do is accept a lift from someone who "
    "approaches you inside the terminal.")
_AIRPORT_FASTEST_REPLY = (
    "Fastest is the train or metro where there is one, because a taxi sits in the same traffic as "
    "everyone else: an airport express train, where a city has one, is quickest of all for a few "
    "euros more, and the metro is close behind. Take a taxi only if you land late, have heavy bags, "
    "or the railway does not run at that hour - and then the official rank or a car booked on an app, "
    "not anyone offering you a ride indoors.")
_AIRPORT_TRAIN_REPLY = (
    "Most big airports have a train or metro into the centre, and the airport's own website says so "
    "under 'to and from the airport', with the platform, the price and the last train of the night - "
    "check that last one before you book a late flight. Where there is a station sign, follow it: it "
    "is almost always cheaper than a taxi, and the ride is usually 15 to 40 minutes. Smaller airports "
    "run a bus to the nearest station instead, and a few have no rail link at all, in which case the "
    "shuttle bus or the official taxi rank is the way in.")
_AIRPORT_HOTEL_REPLY = (
    "Use the hotel's own directions, because they name the station or stop nearest the door and "
    "hotels write that down better than anyone: an email to them gets you the answer before you fly. "
    "Then take the train or bus into the centre and walk from the station, or hop in a short taxi from "
    "there if it is far. A taxi all the way from the airport is the easiest with luggage, so check the "
    "price first and take it from the official rank.")
_AIRPORT_PORT_REPLY = (
    "A cruise port is usually some way from the airport, and the simple answer is the transfer the "
    "cruise line sells: it is priced per person and it waits for the plane if the flight is late, "
    "which no taxi will. If you would rather make your own way, the port's own website lists the "
    "terminal and the local buses, and a taxi is worth it if there are two or more of you with "
    "luggage - agree the price before you get in, because port taxis know you have a ship to catch.")
_AIRPORT_EARLY_REPLY = (
    "Sort the journey the night before rather than on the morning: at 5am the first train often has "
    "not started, so it is a taxi booked in advance, a lift, or a hotel at the airport, and an airport "
    "hotel is worth its price for a flight before about 7am. Work backwards from the departure time - "
    "be there two hours before a short-haul flight and three before a long-haul one, add the journey, "
    "and let the drive take 30 minutes more than the map says at that hour. Check the night rate and "
    "any drop-off charge when you book, because both cost more at that time.")
_AIRPORT_SLEEP_REPLY = (
    "It is allowed in most airports and nobody minds, but be ready for it: the seats before security "
    "are the bright, busy ones, and the quiet corners are past security, which you cannot reach until "
    "check-in opens. For a layover over four hours a pod or an airport hotel is worth the money, and "
    "for a short one a hoodie or a scarf as a pillow, an eye mask, and something to drink gets you a "
    "couple of hours. Keep your bag looped round an arm, set two alarms, and find out where your gate "
    "is before you settle.")


def _airport_without_a_city(understood):
    """An airport question with no airport named: the method, by the shape of the ask."""
    words = [str(word).lower() for word in (understood.get("words") or ())]
    text = " ".join(words)

    def has(options):
        return any(option in words or option in text for option in options)

    # getting *to* the airport is the opposite question to getting out of one, and the two cards
    # `to-the-airport` and `sleep-at-the-airport` own those: a line that says "to the airport" and
    # not "from the airport" is theirs, whatever else it says
    if "to the airport" in text or "to the terminal" in text:
        if "from the airport" not in text:
            return None
    if has(_AIRPORT_PORT):
        return _AIRPORT_PORT_REPLY
    if has(_AIRPORT_HOTEL):
        return _AIRPORT_HOTEL_REPLY
    if has(_AIRPORT_CHEAPEST):
        return _AIRPORT_CHEAPEST_REPLY
    if has(_AIRPORT_TRAIN):
        return _AIRPORT_TRAIN_REPLY
    if has(_AIRPORT_FASTEST):
        return _AIRPORT_FASTEST_REPLY
    return _AIRPORT_WAY_IN


def _airport(memory, understood, general=True):
    clean = understood.get("clean", "")
    place = _place_in(memory, understood, AIRPORT_TRANSFER)
    if not place and "airport" in clean:
        # "how do i get from the airport to the city in barcelona" says the city and the
        # airport the other way round, so the key "barcelona airport" is not in the line.
        for name in sorted(AIRPORT_TRANSFER, key=len, reverse=True):
            if name.replace(" airport", "") in clean:
                place = name
                break
    if not place:
        # "how do i get from the airport to the city" names no airport, and the method is the same
        # everywhere: the transfer table answers when a city is said, this when none is. The taxi
        # card asks with general=False, because a cab price with no city named is its warning and
        # the general way in is not an answer to "how much is a taxi from the airport".
        return _airport_without_a_city(understood) if general else None
    return f"From {place.title()}: {AIRPORT_TRANSFER[place]}"


# A scam line wants the rank-and-meter warning whatever city it names; every other taxi line at a
# named airport is the price, and the transfer note has it.
_TAXI_TROUBLE = ("scam", "scammed", "ripped", "rip off", "rip-off", "overcharged", "overcharge",
                 "meter", "rigged", "cheat", "cheated")

_TAXI_WARNING = ("Use the official rank at the airport rather than anyone who approaches you inside, "
                 "and check the app price or the posted fare before you get in. Insist on the meter, "
                 "or agree the total first, and keep small notes so you are not waiting for change.")


def _taxi_abroad(memory, understood):
    """What a cab costs at a named airport is the transfer note's answer; the warning is the rest.

    "how much is a taxi from Dublin airport to the centre" is a price question about a city whose
    bus and taxi fares are known, so it takes that note; "is a taxi from the airport expensive"
    names no city, and the warning about ranks and meters is all there is to say.
    """
    clean = understood.get("clean") or ""
    # A rip-off, a rigged meter or a cheat wants the warning whatever city it names: the note is a
    # timetable and a price, and "how do i avoid getting ripped off by a taxi in rome" is not that
    # question, even though Rome is named on it.
    if any(word in clean for word in _TAXI_TROUBLE):
        return _TAXI_WARNING
    return _airport(memory, understood, general=False) or _TAXI_WARNING


def _city_airport(memory, understood):
    """"what airport is closest to Lisbon": the airport by name, then the way in."""
    city = _place_in(memory, understood, AIRPORT_NAME)
    if not city:
        return None
    return AIRPORT_NAME[city]

def _two_places(clean):
    """The places a route line names, longest name first so "amalfi coast" is not "amalfi"."""
    names = sorted({name for pair in ROUTE_BETWEEN for name in pair}, key=len, reverse=True)
    return [name for name in names if re.search(r"\b%s\b" % re.escape(name), clean)]


def _route_between(memory, understood):
    """A journey between two named places: the pair is the key, either order."""
    names = _two_places(understood.get("clean", ""))
    for first in names:
        for second in names:
            if first == second:
                continue
            for pair in ((first, second), (second, first)):
                if pair in ROUTE_BETWEEN:
                    return ROUTE_BETWEEN[pair]
    return None


def _get_to(memory, understood):
    """One place named and no starting point: the way in rather than a comparison."""
    clean = understood.get("clean", "")
    for place in sorted(GET_TO, key=len, reverse=True):
        if re.search(r"\b%s\b" % re.escape(place), clean):
            return GET_TO[place]
    return None


SITE_WORDS = tuple(sorted(set(SITE_NOTES) | set(SITE_ALIASES), key=len, reverse=True))


def _site_note(memory, understood):
    clean = understood.get("clean", "")
    for site in SITE_WORDS:
        if re.search(r"\b%s\b" % re.escape(site), clean):
            return SITE_NOTES[SITE_ALIASES.get(site, site)]
    return None


def _day_trip(memory, understood):
    city = _place_in(memory, understood, DAY_TRIPS)
    if not city:
        return None
    return f"Day trips from {city.title()}: {DAY_TRIPS[city]}"


def _clauses(line):
    """The day-trip line split at its commas and its "and", but never inside a bracket.

    Each place in the line is one clause ("Sintra for the palaces (40 minutes by train)"), and a
    clause is what a person who names that place is answered with. Splitting on every comma cut
    through the bracket when a place's own directions had one in it - "Obidos for the walled town
    (an hour by bus from Lisbon's Campo Grande, and no train goes there)" became "and no train
    goes there)" - so a bracket is read as one word of the clause it belongs to. An "and" only
    starts a new place when a place name follows it, which keeps "Oxford and Cambridge" together
    as one clause with one time.
    """
    pieces, piece, depth = [], "", 0
    text = " " + line + " "
    at = 0
    while at < len(text):
        word = text[at]
        depth += (word == "(") - (word == ")")
        if word == "," and depth <= 0:
            pieces.append(piece)
            piece = ""
            at += 1
            continue
        join = text[at:at + 5].lower()
        if join == " and " and depth <= 0:
            after = text[at + 5:at + 30].strip(" ,").lower()
            after = " ".join(after.split()[:2])
            if any(after == name or after.startswith(name + " ")
                   for name in DAY_TRIP_PLACES):
                pieces.append(piece)
                piece = ""
                at += 5
                continue
        piece += word
        at += 1
    pieces.append(piece)
    tidy = []
    for piece in pieces:
        piece = re.sub(r"^\s*(?:and|plus)\s+", "", piece).strip(" ,")
        if piece:
            tidy.append(piece)
    return tidy


def _day_trip_clause(line, place):
    """The clause of a day-trip line about one place, with the words that explain it.

    A place can be named with nothing after it ("Oxford and Cambridge (about an hour)" was one
    clause before the "and" was split on), so the clause grows to the next piece until it holds
    what the place is for or how far it is - otherwise the answer to "is oxford worth it" is
    "From London: Oxford", which says nothing at all.
    """
    pieces = _clauses(line)
    for place_at, piece in enumerate(pieces):
        if not re.search(r"(?<![a-z])" + re.escape(place) + r"(?![a-z])", piece.lower()):
            continue
        said = piece
        for more in pieces[place_at + 1:]:
            if " for " in said.lower() or "(" in said:
                break
            said += " and " + more
        return said
    return ""


def _place_named_in_the_chat(memory):
    """The day trip the last turn or two was about, for the follow-up that does not repeat it.

    "and how do we get there" and "is it worth it then" are about the place the turn before
    named; the place itself is only in that line, not in this one.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return None
    for turn in reversed(turns[-2:]):
        if not isinstance(turn, dict):
            continue
        place = _find_in(str(turn.get("user") or "").lower(), DAY_TRIP_PLACES)
        if place:
            return place
    return None


def _day_trip_place(memory, understood):
    """The one day trip the line names, and what it costs them in time.

    "is sintra worth it" is about Sintra, not about Lisbon: the clause the city's line already
    has says what it is for and how far it is, and the advice after it is the part that changes
    the day ("Buy the train ticket at the machine and go before 9am"). Nothing here calls a place
    worth it in someone else's taste - it says what the visit costs in time, so they can decide.
    """
    clean = understood.get("clean", "")
    # The two asks are different questions. "How do we get there" is the journey and nothing
    # else, and it came back as "Same as before: <the whole of the answer above>", which is the
    # bot reading its own answer out again; "is it worth it" wants what there is to see. The
    # travel time is already in brackets in the clause, so the journey answer is that alone.
    way = re.search(r"\bhow (?:do|can|would|should) (?:i|we|you) get\b|\bhow to get\b"
                    r"|\bhow far\b|\bhow long does it take\b", clean)
    place = _find_in(clean, DAY_TRIP_PLACES)
    if not place and way:
        # "is sintra worth it" then "and how do we get there" is one question in two parts: the
        # second names no place because the first did. Without this the journey ask was answered
        # "Same as before: From Lisbon: Sintra for the palaces (40 minutes by train)" - the same
        # sentence again rather than the one line that holds the train.
        place = _place_named_in_the_chat(memory)
    if not place:
        return None
    city = DAY_TRIP_PLACES[place]
    # The city in hand decides whether this is their day trip at all. "what about bruges" at the
    # end of a Lisbon chat was answered "From Brussels: Bruges (an hour by train)" - true, and
    # about a city they are not in. The name is answered when the city that reaches it is the one
    # they have been talking about, or when the chat names no city at all and the trip is all the
    # line can be read as.
    # The city in hand is the one the chat is *about*, not the one in the last two turns: after
    # two day-trip turns a Lisbon chat names no city at all, and "what about bruges" was answered
    # "Day trips from Brussels: Bruges (an hour by train)" - true, and about a city they are not
    # in, where main punts and a punt is the better reply. The plan the chat still holds is the
    # city they are going to, so it is read after the line and the turns just before it.
    in_hand = _place_in(memory, understood, CITIES) or _place_in_the_plan(memory, CITIES)
    if in_hand and in_hand != city:
        return None
    first, _, rest = DAY_TRIPS[city].partition(". ")
    clause = _day_trip_clause(first, place)
    if not clause:
        return None
    how_long = re.search(r"\(([^)]*)\)", clause)
    if way and not how_long:
        # "how far is chartres" is a question about distance, and the clause without a figure in
        # it answers a different one ("From Paris: Chartres for the cathedral"). Rather than say
        # a distance the file does not have, the whole day-trip line is the answer - it holds the
        # times for the places it does know and does not pretend to a figure it lacks.
        return _without_the_season(f"Day trips from {city.title()}: {DAY_TRIPS[city]}",
                                   _when_said(memory, understood))
    if way:
        # The figure, and only the figure: the bracket can carry more than the journey ("an hour
        # by bus from Lisbon's Campo Grande, and no train goes there"), and the city is added
        # only when the figure does not name where it starts from already.
        journey = how_long.group(1).split(",")[0].strip()
        if " from " in journey.lower():
            said = f"{place.title()}: {journey}."
        else:
            said = f"{place.title()}: {journey} from {city.title()}."
    else:
        # The line still opens the way the day-trip card does ("Day trips from Lisbon:"), because
        # that is what the answer is: the day trips, cut down to the one named. #8047's own test
        # reads the phrase, and the reader who asked about Sintra is not told about Cascais.
        said = f"Day trips from {city.title()}: {clause}."
    # The advice after the list is about the way the rest of it is reached - "Buy the train ticket
    # at the machine" is a good last sentence for Sintra and the wrong one for Obidos, which has
    # no train, so a clause that names its own way of getting there keeps its own advice only.
    # A line that asked for the journey gets the journey: the advice was in the answer to the
    # worth-it question a turn before, and saying it again reads as the bot repeating itself.
    if rest and not way and not re.search(r"\b(bus|coach|car|drive|ferry)\b", clause):
        said += " " + rest
    # The city guides already take off a last sentence about another month ("Book Bruges ahead
    # in summer" to a person going in November is the guide talking to itself), and a day trip
    # named deserves the same reading of the month they gave.
    return _without_the_season(said, _when_said(memory, understood))


# The card's name is the city, and people name the card instead of the city: "is it worth getting
# an oyster card" never says London. Longest phrase first, and each one is the phrase people use,
# so "nol card" cannot match inside "knowledge".
TRANSIT_CARDS = {
    "oyster card": "london",
    "navigo easy": "paris",
    "navigo card": "paris",
    "suica card": "tokyo",
    "pasmo card": "tokyo",
    "octopus card": "hong kong",
    "opal card": "sydney",
    "presto card": "toronto",
    "myki card": "melbourne",
    "clipper card": "san francisco",
    "t-money card": "seoul",
    "nol card": "dubai",
    "andante card": "porto",
    "viva viagem": "lisbon",
    "ov-chipkaart": "amsterdam",
    "icoca card": "osaka",
    "charliecard": "boston",
    "ventra card": "chicago",
    "compass card": "vancouver",
    "metrobus card": "madrid",
}

# A line about getting round the city is not a line about getting in from the airport, and the two
# share every word people use - "how do i get", "the metro", "the train". What separates them is
# the shape of the question, so the entry keeps a list of booking and airport words it will not
# answer, and this callable takes the city from the line or the turn before.
# The words that make a line a getting-around line. A bare "card" or "pass" is not one: "can i
# use my bank card in lisbon" is a money question, and "can i use my bank card on the metro" is a
# metro question, and only the second one has one of these.
_TRANSIT_WORDS = ("get around", "getting around", "get about", "getting about", "get round",
                  "getting round", "around town", "metro", "subway", "underground", "tube",
                  "u-bahn", "tram", "trams", "bus", "buses", "public transport", "transport",
                  "transit", "travelcard", "travel card", "day pass", "metro card",
                  "how do i travel", "how do people travel", "contactless", "top up",
                  "chipkaart", "oyster", "ticket")

# Words that name one city's transport system, so a line with no city in it still has one.
CITY_TELLS = {"the tube": "london", "london underground": "london", "tube station": "london"}

# The words that make a line a question about a travel card rather than about getting around.
CARD_WORDS = ("travel card", "travelcard", "day pass", "metro card", "transit card", "oyster",
              "pass for the", "weekly pass", "monthly pass", "tap in", "contactless")

# The same words as a name for the thing, so a line that asks for a card and names no city
# reaches the entry at all: "how do i get a travel card" scored nothing and came back with
# "take two cards from different banks", which is a cash question.
CARD_NAMES = ("travel card", "travelcard", "day pass", "metro card", "transit card",
              "oyster card", "oyster", "weekly pass", "monthly pass", "tap in")

GENERAL_CARD = ("The rule is the same in most cities: tap a contactless bank card or your phone "
                "if the system takes one, because it charges the cheapest fare and usually caps "
                "the day, and if it does not, buy the stored-value card at a machine in the "
                "station - Oyster in London, Navigo in Paris, Suica in Tokyo. Compare a day or "
                "three-day pass with single tickets before you buy one: it only wins if you make "
                "several journeys a day, and the machines take a card, not always cash.")

_TRANSIT_NOT = ("airport", "flight", "flights", "fly", "flying", "booking", "book a", "hotel",
                "day trip", "day trips", "day out", "worth visiting", "best time", "rent a car",
                "hire a car", "car hire", "parking", "taxi from", "uber from")


def _transit(memory, understood):
    clean = understood.get("clean", "")
    if any(word in clean for word in _TRANSIT_NOT):
        return None
    if not any(word in clean for word in _TRANSIT_WORDS) and not _find_in(clean, TRANSIT_CARDS):
        return None
    city = _place_in(memory, understood, CITY_TRANSIT)
    if not city:
        # The chat's plan keeps the city for the whole chat, and a getting-around question
        # comes after several lines that name nothing ("were going to edinburgh in august" /
        # "two adults and a baby" / "for four days" / "is the castle ok with a pram" /
        # "what about getting around"). The last turn or two carry no city, so the plan is
        # where a follow-up late in a travel chat finds one.
        city = _place_in_the_plan(memory, CITY_TRANSIT)
    if not city:
        city = _find_in(clean, TRANSIT_CARDS)
        city = TRANSIT_CARDS[city] if city else None
    if not city:
        # "on the tube" names no city and names London all the same: the tube is not a tram in
        # Lisbon. Only the words that belong to one city are here.
        tell = _find_in(clean, CITY_TELLS)
        city = CITY_TELLS[tell] if tell else None
    if not city or city not in CITY_TRANSIT:
        # A card question with no city in it is not a city question: the rule is the same
        # everywhere, so the general one is a real answer rather than a shrug.
        if _find_in(clean, CARD_WORDS):
            return GENERAL_CARD
        return None
    return f"In {city.title()}: {CITY_TRANSIT[city]}"


def _already_guided(memory, city):
    """True when the guide for this city is already in the conversation.

    A chat can leave the plan for several turns and come back to it ("what about a day trip",
    then "is sintra worth it"): the guide was given before the digression, so the next Lisbon
    line wants the day trips, not the same paragraph. The mark is the guide's own opening
    sentence, not "In {city}:", because the transport card and the airport note begin that way
    too - a chat that has only had the metro card has not been round the city yet.
    """
    turns = memory.get("turns") or []
    guide = (CITIES.get(city) or "")[:40].lower()
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        if guide and guide in (turn.get("bot") or "").lower():
            return True
    return False


def _asked_for_the_guide_before(memory, city, clean):
    """True when an earlier line asked this city's guide and the guide answered it.

    A person who types the same question twice wants the same answer, not the day trips. A new
    ask after a digression ("what should we do in lisbon" after a day-trip question) has no
    earlier guide ask behind it, so it still gets the next thing.
    """
    body = (CITIES.get(city) or "")[:40].lower()
    for turn in memory.get("turns") or []:
        if not isinstance(turn, dict):
            continue
        said = (turn.get("user") or "").lower()
        if not said:
            continue
        if _find_in(said, CITIES) != city:
            continue
        if body and body in (turn.get("bot") or "").lower():
            return True
    return False


def _guided_off_a_question(memory, city):
    """True when the guide in this chat answered a question, not a statement naming the trip.

    "im going to edinburgh in june" takes the guide because naming the trip is enough to want it,
    but it did not ask for it. The sightseeing question after it ("what should i see") is new, so
    it wants what comes after the guide, not the guide again under "same as before". Only a line
    that asked (a question word or a question mark) counts as having asked.
    """
    body = (CITIES.get(city) or "")[:40].lower()
    for turn in memory.get("turns") or []:
        if not isinstance(turn, dict):
            continue
        said = (turn.get("user") or "").lower().strip()
        if not said or _find_in(said, CITIES) != city:
            continue
        if not (_A_QUESTION_OPENS.match(said) or "?" in said):
            continue
        if body and body in (turn.get("bot") or "").lower():
            return True
    return False


# "and what about food" is one part of the city, so the guide answers that part rather than the
# whole paragraph again or the day trips: the words that name the part, and the words the guide
# itself uses for it.
DETAIL_PARTS = (
    (("food", "eat", "eating", "dinner", "lunch", "breakfast", "restaurant", "restaurants",
      "meal", "meals", "drink", "drinks", "bar", "bars", "tapas", "coffee", "market",
      "markets", "nightlife", "club", "clubs"),
     ("food", "eat", "eating", "dinner", "lunch", "breakfast", "restaurant", "restaurants",
      "meal", "meals", "drink", "drinks", "bar", "bars", "tapas", "coffee", "market",
      "markets", "nightlife", "club", "clubs")),
    (("museum", "museums", "gallery", "galleries", "art", "arts", "sight", "sights",
      "sightseeing", "see", "visit", "castle", "cathedral", "ruins", "history", "park"),
     ("museum", "museums", "gallery", "galleries", "art", "sights", "castle", "cathedral",
      "colosseum", "palace", "abbey", "church", "park", "view", "walk")),
    (("shop", "shops", "shopping", "buy", "souvenir", "souvenirs", "present", "presents"),
     ("shop", "shops", "shopping", "market", "markets", "souvenir", "souvenirs")),
)


# The words that ask what there is to see are not a part of the city named: "what should i see"
# is the whole of it, and the guide's own sentence for "see" handed the paragraph back - under
# "Same as before" after the guide, and instead of the day trips. Only a word like "museum" or
# "castle" names a part.
ASKING_ONLY = frozenset("""see sight sights sightseeing visit visited miss anything something
somewhere worth goto go""".split())
# The words that ask about eating in a city. A city with a cheap-eats card answers the eating
# part with that card, not with the guide sentence that happens to mention lunch: asked "and the
# food like there" after the Lisbon guide, the person got "there is nothing separate on the food"
# - the guide's own sentence about the Time Out Market, handed back as a shrug - when the card
# that lists the bifana, the prato do dia and the market was sitting in the same file. DETAIL_PARTS
# keeps the words for the other parts; this is the one with an answer of its own.
_EATING_WORDS = frozenset(DETAIL_PARTS[0][0])


def _detail_line(city, clean):
    """The part of the guide about the thing they named, or None when they named no part."""
    words = set(clean.split())
    if words & _EATING_WORDS and city in CHEAP_EATS:
        return CHEAP_EATS[city]
    for asked, said in DETAIL_PARTS:
        # A part named is a part asked about: "what should i see" and "what should i visit" name
        # nothing, and the sightseeing words in the group are the question's, not a part's.
        if not (words & set(asked)) - ASKING_ONLY:
            continue
        for sentence in CITIES[city].split(". "):
            if set(sentence.lower().split()) & set(said):
                sentence = sentence.rstrip(".")
                return f"In {city.title()}: {sentence}."
    return None


# A line that opens with a question word is a question even when the reading finds no ask in
# it: "what do you do about that" after a guide is still asking, and it wants the next thing.
_A_QUESTION_OPENS = re.compile(
    r"^\s*(?:and\s+|so\s+|but\s+)?(?:what|how|where|when|which|who|why|can|could|should|"
    r"would|do|does|did|is|are|was|were|will|any|tell|recommend|suggest|give|show)\b")


# "What should i see first" is a pick, not the whole list again: the person has three things and
# wants to know which one to do first. After the guide it read "Same as before: In Rome: the
# Colosseum with a timed ticket, the Pantheon, and Trastevere in the evening for dinner" - the
# card they had just read, handed back with a frame in front of it.
WHICH_FIRST = re.compile(
    r"\bwhat\b[^.?!]{0,30}\b(?:see|do|visit)\b[^.?!]{0,20}\bfirst\b"
    r"|\bwhere (?:should|shall|do|would) (?:i|we) (?:start|begin)\b"
    r"|\bfirst thing (?:to (?:see|do)|i should|we should)\b"
    r"|\bwhat(?:'s| is) the first thing\b", re.I)


# A card that opens "In Barcelona:" is a city's guide, and the list under it is places to go.
_IN_A_CITY = re.compile(r"^\s*in ([a-z][a-z .'-]{1,20}):", re.I)


def a_city_card_is_in_front(card):
    """True when the answer in hand is a city guide whose list of places it opens with."""
    found = _IN_A_CITY.match(str(card or ""))
    if not found:
        return False
    return found.group(1).strip().lower() in CITIES


# The ask the composer stands down for on a city card: which of these to do first.
WHICH_ONE_FIRST = re.compile(r"\b(?:see|do|visit)\b[^.?!]{0,20}\bfirst\b", re.I)

# The words a city's list of places opens on when the item is a thing rather than a doing.
_A_PLACE_OPENS = ("the ", "a ", "an ", "one ", "two ", "three ", "some ", "my ", "your ")


def asks_which_one_first(text):
    """True when the line asks which of the things already named to do first."""
    return bool(WHICH_ONE_FIRST.search(str(text or "")))


def _the_first_thing(city):
    """The one to do first, from the city's own sights: "Start with the Colosseum, then ...".

    The sights are one sentence in `CITIES`, written as a list of two or three, so the first two
    are the first comma-separated parts of it. The rest of the card - the ticket note, the water
    bottle - is not an answer to which one comes first.
    """
    sights = CITIES.get(city) or ""
    head = sights.split(". ")[0].rstrip(".")
    items = [part.strip() for part in head.split(",") if part.strip()]
    items = [part[4:] if part.lower().startswith("and ") else part for part in items]
    if not items:
        return None
    rest = f", then {items[1]}" if len(items) > 1 else ""
    # A city writes its list either as places ("the Colosseum with a timed ticket") or as things
    # to do ("walk the Ile de la Cite to the Marais"), and "Start with walk the Ile" is not a
    # sentence. The frame follows the first item: a place is started with, a doing opens the reply
    # in its own words.
    first = items[0]
    if first[:1].isupper() or first.lower().startswith(_A_PLACE_OPENS):
        return f"Start with {first}{rest}."
    return f"{first[:1].upper() + first[1:]}{rest}."


def _about_city(city, memory, clean, understood=None):
    """The next thing to say about a city the conversation already named."""
    # A named part of the city (food, museums, shops) is answered by the guide's own line for
    # it: the day trips are no answer to "and what about food".
    # Which to do first is answered by the city's own list, whichever turn it is asked on, and
    # before the part-of-the-city line: "what should i see first" names "see", which is the
    # sights part and would hand back the whole sentence the person already has.
    if WHICH_FIRST.search(clean):
        first = _the_first_thing(city)
        if first:
            return first
    detail = _detail_line(city, clean)
    if detail:
        return detail
    if _already_guided(memory, city):
        # Saying the same guide twice reads as a machine: the ask after it wants something the
        # chat has not had. Which card that is depends on the ask - "any day trips" wants the
        # places around it, and "what should i see" wants more of the city's own advice - so the
        # cards are tried in order and the first one this chat has not had yet is the answer.
        # A line with no ask is not a new question about the city: "we are staying near
        # waverley" is a statement about the trip, and the day trips are no answer to it. Only
        # a line with an ask gets the next thing; a statement keeps the guide it already had.
        if (understood is not None and not understood.get("asks")
                and not _A_QUESTION_OPENS.match(clean)):
            return "In %s: %s" % (city.title(),
                                  _without_the_season(CITIES[city],
                                                      _when_said(memory, understood or {})))
        next_thing = _the_next_card_about(city, memory, clean)
        if next_thing:
            return next_thing
        return None
    return f"In {city.title()}: {CITIES[city]}"


# "Any day trips" and "what else is there" are asking to leave the city; "what should i see" is
# asking about the city itself. The day trips answer the first and not the second: Edinburgh's
# Glasgow and Stirling are no answer to "anything we shouldn't miss" in Edinburgh.
MORE_PLACES = frozenset("""trip trips else other others another further afield nearby outside
countryside around surrounding surroundings excursion excursions""".split())


SEEING = frozenset("see seeing saw sight sights sightseeing visit visiting visited miss "
                   "missed seen".split())


def _wants_more_places(clean):
    """True when the line asks what is around the city rather than what is in it."""
    words = set(clean.split())
    if words & MORE_PLACES:
        return True
    return bool(re.search(r"\bday\s+(?:trip|trips|out)\b", clean))


def _the_stay_is_long(memory, city):
    """True when the stay is more days than the city fills, which is when the day trips fit.

    A city that fills a day (Bath) has days to spare on a weekend, and one that fills four
    (Paris) does not have them in a week: the room a person has for a day out is the length of
    the stay next to how long the city itself takes, not a fixed number of days.
    """
    fills = CITY_DAYS.get(city, 3)
    for turn in memory.get("turns") or []:
        if not isinstance(turn, dict):
            continue
        said = (turn.get("user") or "").lower()
        days = next((count for phrase, count in sorted(TRIP_UNITS, key=lambda item: -len(item[0]))
                     if phrase in said), None)
        if days is None:
            more = re.search(r"\b(\d{1,2}|%s)\s+(?:days|nights)\b"
                             % "|".join(_NUMBER_WORD), said)
            if more:
                word = more.group(1)
                days = int(word) if word.isdigit() else _NUMBER_WORD.index(word) + 1
        if days and days >= max(2, 2 * fills):
            return True
    return False


def _said_in_this_chat(memory, text):
    """True when the bot has already said this, so saying it again is the repeat to avoid."""
    head = text[:40].lower()
    for turn in memory.get("turns") or []:
        if isinstance(turn, dict) and head and head in (turn.get("bot") or "").lower():
            return True
    return False


def _the_next_card_about(city, memory, clean):
    """The next thing about the city this chat has not had, in the order a person wants them."""
    place = CITY_COUNTRY.get(city, city)
    cards = []
    # "What should i see" after the guide is asking for more of the city, so the areas of it come
    # first: naming where to wander is the next thing to be seen, and the transport and the day
    # trips are answers to other questions. "Any day trips" or a long stay flips that round.
    areas = (f"In {city.title()}: by area, {CITY_AREA[city]}." if city in CITY_AREA else None)
    day_trips = (f"Day trips from {city.title()}: {DAY_TRIPS[city]}"
                 if city in DAY_TRIPS else None)
    if _wants_more_places(clean) or _the_stay_is_long(memory, city):
        cards += [day_trips, areas]
    elif set(clean.split()) & SEEING:
        # "What should i see" is about the city, so its own areas come before a day out of it.
        cards += [areas, day_trips]
    else:
        cards += [day_trips, areas]
    if city in CITY_TRANSIT:
        cards.append(f"In {city.title()}: {CITY_TRANSIT[city]}")
    if city in WHEN_TO_GO:
        cards.append(f"For {city.title()}: {WHEN_TO_GO[city]}")
    elif place in BEST_TIME:
        cards.append(f"For {city.title()}: {BEST_TIME[place]}")
    if city in CITY_CLIMATE and city in CLIMATES:
        cards.append(f"For {city.title()}: {CLIMATES[CITY_CLIMATE[city]]}")
    if city in DAILY_BUDGET:
        low, high, note = DAILY_BUDGET[city]
        cards.append(f"{city.title()} is about \u00a3{low} to \u00a3{high} a day per person on the "
                     f"ground, room aside. {note[0].upper() + note[1:]}.")
    for card in cards:
        if card and not _said_in_this_chat(memory, card):
            return card
    return None


def _guide_followup(memory, understood):
    """"What should we do there": the city is in the turn before, not in this line."""
    clean = understood.get("clean", "")
    if _find_in(clean, CITIES):
        return None  # the line names the place: city-guide answers that one
    # Pointing back has to be in the words: "and museums?", "what about the food", "anything
    # else there". A bare museum word is its own subject, whatever was said three turns ago.
    if not any(mark in clean for mark in FOLLOW_MARKS):
        return None
    city = _place_in(memory, understood, CITIES)
    if not city and SIGHTSEEING_ASK.search(clean):
        # "what should i see there" after the guide names no place either, and "there" is only
        # in the words: the place the store holds is the trip. A food or drink ask keeps its own
        # answer, which is why only the sightseeing ask is read this way.
        city = _the_place_held(memory)
    if not city:
        return None
    if (_already_guided(memory, city) and SIGHTSEEING_ASK.search(clean)
            and _guided_off_a_question(memory, city)):
        # The sights were asked for already, so the answer is that answer again: it comes back
        # framed as the repeat it is ("same as before"), not as a new thing to see. The guide
        # coming from a statement ("im going to edinburgh in june") was not asked for, so the
        # sightseeing question after it is a new one, and the day trips are its answer.
        return f"In {city.title()}: {CITIES[city]}"
    return _about_city(city, memory, clean, understood)


# The sightseeing ask with no place in it: "what should i see", "what should we visit", "what
# is worth seeing". Not "what should i eat" or "where should i stay", which have answers of their
# own wherever the person is.
SIGHTSEEING_ASK = re.compile(
    r"\b(?:what|which|where)\s+(?:should|could|can|must|do)\s+(?:i|we|you)\s+"
    r"(?:see|visit|not miss)\b"
    r"|\bwhat(?:'s| is| are)\s+worth\s+seeing\b"
    r"|\bwhat(?:'s| is| are)\s+there\s+to\s+(?:see|visit)\b")


def _the_place_held(memory):
    """The place the trip is in: what the store holds for it, or the place they just said.

    "im going to rome in june" files "Rome", and the store is the first place to look. A stay
    files nothing - "three days in edinburgh next month" names the trip and the store has no
    place in it - so the city named in the two lines they said last is read as well. Both are
    narrow: a name in the store, or a name with a going word or a length of stay in front of it.
    """
    held = (memory.get("user") or {}).get("places") if isinstance(memory, dict) else None
    if isinstance(held, list) and held:
        newest = " ".join(str(held[-1] or "").lower().split())
        if newest in CITIES:
            return newest
    return _city_they_are_going_to(memory)


def _guide_next(memory, understood):
    """A short "what should we see" straight after the guide: the city is the one just guided.

    "we're going to rome in may" then "what should we see" is the same city, and the line has no
    place word in it at all, so nothing else reads it. The guide in the reply before is what
    proves the city, so a line with a place in it or a line two moves later is left alone.
    """
    clean = understood.get("clean", "")
    if len([word for word in clean.split() if word.isalpha()]) > 8:
        return None
    if _find_in(clean, CITIES):
        return None
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return None
    last = turns[-1] if isinstance(turns[-1], dict) else {}
    said = str(last.get("bot") or "").lower()
    for city in CITIES:
        if f"in {city}:" in said:
            return _about_city(city, memory, clean, understood)
    # The trip does not stop being the trip because they said something else about it: "im
    # going to rome in may", "its my first time flying alone", "what should i see" is still
    # Rome. A city named in the last two of their own lines is the city in hand, and when they
    # have not named one since, the place the store holds is:
    #
    #     im going to rome in june      In Rome: the Colosseum ...
    #     no, july sorry                Got it - you're going to Rome in July.
    #     how long is the flight        About two and a half hours ...
    #     what should i see             (main: "I don't know enough to answer that honestly")
    #
    # Only the sightseeing ask is read this way. "what should i eat" is a food question with an
    # answer wherever they are, so it is left to the food entries even on a trip.
    city = _city_they_are_going_to(memory)
    if not city and SIGHTSEEING_ASK.search(clean):
        city = _the_place_held(memory)
    if city and not _already_guided(memory, city):
        return f"In {city.title()}: {CITIES[city]}"
    if city:
        return _about_city(city, memory, clean, understood)
    return None


# The words that make a place the place they are going, rather than a place mentioned on the way
# past: a film set in Rome is not a trip. A length of stay is the other way people say it -
# "three days in edinburgh next month" has no going word in it at all, and the line is the trip.
GOING_TO_A_PLACE = re.compile(
    r"\b(?:going|go|off|heading|fly(?:ing)?|flying|travell?ing|trip|holiday|weekend|break|"
    r"visiting|visit|staying|renting|booked|booking|flight)\b"
    r"|\b(?:\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|a\s+few|a\s+couple\s+of)\s+"
    r"(?:days?|nights?|weeks?|weekends?|fortnight)\b")


def _city_they_are_going_to(memory):
    """The city named in the last two of the person's own lines, when a line says they go there."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return None
    for turn in reversed(turns[-2:]):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "").lower()
        city = _find_in(said, CITIES)
        if city and GOING_TO_A_PLACE.search(said):
            return city
    return None


# What to carry, said the same way wherever it is added to a number. The short form is the one
# that goes after a rate, because the rate is already a paragraph.
_CARRY_MONEY = ("Take two cards from different banks and a little local cash, and always pay in the "
                "local currency when the terminal offers to convert you - the \"pay in pounds\" "
                "option adds 3 to 5%. Use a bank ATM rather than a currency kiosk, and tell your "
                "bank you are travelling if it still asks.")

# The same question as "how much should i take", asked about losing it: one wallet in one pocket
# is the only real mistake, and the rest is where the money sits.
_KEEP_SAFE = ("Split it, so one loss is not the whole trip: a card and a day's cash on you, a second "
              "card in the hotel safe or packed separately, and a note of both card numbers and "
              "your bank's lost-card number somewhere offline. Carry a small amount in a front "
              "pocket or a zipped bag rather than a back pocket, use bank ATMs in daylight, and a "
              "money belt only if you will really wear it. If a card goes, freeze it in the app "
              "and ring the bank straight away, and check the phone before you fly: roaming on, "
              "a roaming pass for that country, and the bank app logged in, because that is how "
              "most of us pay now.")

_CARRY_SHORT = ("Take two cards from different banks and a little local cash, and pay in the local "
                "currency when the terminal offers to convert you.")


def _money_abroad(memory, understood):
    """"How much money should i take to spain" asks two things at once: an amount and how to carry
    it. The day rate in DAILY_BUDGET answers the amount, the cards advice answers the carrying, so
    the line gets both instead of the cards advice alone.
    """
    clean = (understood.get("clean") or "").lower()
    if re.search(r"\b(?:safe|safely|safety|stolen|theft|pickpocket|pickpockets|money belt|"
                 r"robbed|lose|lost|keep (?:my )?(?:money|cash|card))\b", clean):
        return _KEEP_SAFE
    if re.search(r"\bhow much\b", clean):
        # _trip_budget already refuses a line with no place or no cost word, so its answer is only
        # the rate when there is one to give.
        rate = _trip_budget(memory, understood)
        if rate:
            return rate + " " + _CARRY_SHORT
    return _CARRY_MONEY


def _trip_budget(memory, understood):
    """Is a stated amount enough for the trip, or what a trip costs: arithmetic over
    DAILY_BUDGET, not an opinion."""
    import re as _re
    clean = understood.get("clean", "")
    # A cost word has to be in the line itself: "is it warm enough for the beach" reached this
    # entry through the remembered place, and a daily rate is no answer to a weather question.
    cost_word = _re.search(r"\b(?:how much|cost|costs|costing|expensive|pricey|afford|budget|"
                           r"spend|spending|will that|does that|go far|saved|money|cheap|"
                           r"inexpensive|affordable)\b", clean)
    # "cheap flights to spain" and "a cheap hotel in rome" are about one part of the trip, not
    # about what a day there costs, so a day rate is no answer to them.
    if _re.search(r"\b(?:flight|flights|fly|flying|hotel|hotels|accommodation|apartment|"
                  r"villa|hostel|ticket|tickets|deal|deals|package|insurance|car hire)\b", clean):
        return None
    # "is 400 enough" is a cost question; "is it warm enough", "good enough", "big enough" are
    # not, and the remembered place is what let them reach this entry at all.
    quality = _re.search(r"\b(?:warm|cold|hot|good|bad|big|small|deep|strong|quick|fast|early|"
                         r"late|cheap|safe|close|near|light|heavy|bright|tall|old|fit|well|"
                         r"soon|long|clear|loud|quiet|tidy)\s+enough\b", clean)
    # A number with nothing after it is an amount of money: "is 400 enough for lisbon".
    amount = _re.search(r"[\u00a3$\u20ac]|\b\d{2,}\b", clean)
    if not cost_word and not amount and (quality or not _re.search(r"\benough\b", clean)):
        return None
    # "is four days enough for lisbon" is about time, not money: a day rate is no answer.
    if not cost_word and not amount and _re.search(
            r"\b(?:days|nights|how long|too long|too short)\b", clean):
        return None
    place = _place_in(memory, understood, DAILY_BUDGET)
    if not place:
        return None
    # The longest phrase wins: "a long weekend" is three days, not the "weekend" inside it.
    days = next((count for phrase, count in sorted(TRIP_UNITS, key=lambda item: -len(item[0]))
                 if phrase in clean), None)
    low, high, note = DAILY_BUDGET[place]
    if days is None:
        # No length stated: "is London expensive" wants a day rate, not a made-up week.
        return (f"{place.title()} is about \u00a3{low} to \u00a3{high} a day per person on the "
                f"ground, room aside. {note[0].upper() + note[1:]}.")
    low_total, high_total = low * days, high * days
    amount = next((int(m.replace(",", "")) for m in _re.findall(r"\d[\d,]*", clean)
                   if 50 <= int(m.replace(",", "")) <= 20000), None)
    if amount is None:
        return (f"{days} days in {place.title()} usually costs about \u00a3{low_total} to "
                f"\u00a3{high_total} per person on the ground, room aside. "
                f"{note[0].upper() + note[1:]}.")
    if amount >= high_total:
        verdict = "That is comfortable"
    elif amount >= low_total:
        verdict = "That works if you are careful"
    else:
        verdict = "That is tight"
    return (f"{verdict}: {days} days in {place.title()} usually costs about \u00a3{low_total} to "
            f"\u00a3{high_total} per person on the ground, room aside, and you have "
            f"\u00a3{amount}. {note[0].upper() + note[1:]}.")


def _month_in_the_chat(memory):
    """The month the chat has settled on, when this line does not name one.

    "im planning a trip to edinburgh in march" and then, two turns on, "do you think march is too
    cold": the month was read off the line only, so the judging frame got a shrug.
    """
    user = memory.get("user") if isinstance(memory, dict) else None
    texts = []
    if isinstance(user, dict):
        texts.append(str(user.get("the_plan") or ""))
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if isinstance(turns, list):
        for turn in reversed(turns[-4:]):
            if isinstance(turn, dict):
                texts.append(str(turn.get("user") or ""))
    for text in texts:
        text = text.lower()
        found = next((number for name, number in sorted(MONTHS.items(), key=lambda item: -len(item[0]))
                      if name in text), None)
        if found:
            return found
    return None


def _weather(memory, understood):
    clean = understood.get("clean", "")
    # The place and the month are the trip's as often as they are the line's: "is it too cold
    # there in april", "do you think march is too cold".
    city = (_find_in(clean, CITY_CLIMATE) or _place_in(memory, understood, CITY_CLIMATE)
            or _place_in_the_plan(memory, CITY_CLIMATE))
    month = next((number for name, number in sorted(MONTHS.items(), key=lambda item: -len(item[0]))
                  if name in clean), None)
    if month is None:
        month = _month_in_the_chat(memory)
    if not city or not month:
        return None
    low, high = CLIMATES[CITY_CLIMATE[city]][month]
    # "may" is the one month with no name longer than three letters, and reaching for a long
    # one left the line unanswered: "what's the weather like in rome in may" hedged on every
    # city the knowledge base has figures for.
    name = next((word for word, number in sorted(MONTHS.items(), key=lambda item: -len(item[0]))
                 if number == month and len(word) > 3), "May")
    return (f"{name.title()} in {city.title()} is usually about {low} to {high}C, and I can't see a "
            f"live forecast from here. Take a layer either way: evenings are cooler than the "
            f"afternoon, and a light rain jacket covers most days.")


def _cheap_trains(memory, understood):
    """A railcard question is about the card itself; anything else is about the fares."""
    text = understood.get("clean") or ""
    if re.search(r"\brail ?cards?\b", text):
        return ("A railcard costs about £30 and takes a third off most fares, so it pays for itself "
                "in two or three trips. Get the one for your age or your area (a Two Together card "
                "covers two named people travelling together) and load it as a digital card in the "
                "train company app.")
    return ("Book as early as you can: advance singles usually go on sale about twelve weeks ahead "
            "and are the cheapest fares. Travelling off-peak (in the UK, after 9:30am) avoids the "
            "peak price, a railcard pays for itself in a couple of trips, and a split-ticket site "
            "can cut the fare further by buying the same journey as two shorter tickets.")


def _suitcase_protect(memory, understood):
    """Packing so it survives the hold, or claiming for one that did not."""
    text = (understood.get("clean") or "").lower()
    broken = ("broke", "broken", "cracked", "damaged", "snapped", "torn", "ripped",
              "came back", "came off", "fell off")
    # "how do i keep a suitcase from being damaged" is the packing question, not a claim: a line
    # that says keep, stop or prevent is about the next trip whatever its past tense.
    keeping = ("how do i keep", "keep it from", "from being", "stop", "prevent", "protect",
               "avoid", "not get", "without")
    if any(word in text for word in broken) and not any(word in text for word in keeping):
        return ("If the airline did it, report it at the baggage desk before you leave the airport "
                "and photograph the damage there: the report number is what a claim needs, and "
                "under the Montreal rules the airline pays for repair or replacement. If it broke "
                "at home, a luggage repair shop fits new wheels, straps and zip pulls for far less "
                "than a new case.")
    return ("Do not fill it until it splits: a zip bursts from the inside, so leave a hand's width "
            "of give and put the heavy things at the wheel end. A luggage strap takes the strain "
            "off the zip, a hard shell or a padded cover protects what is fragile, and anything "
            "breakable goes in the middle wrapped in clothes. Photograph it open and closed before "
            "check-in, because that is what an airline asks for when you claim for the damage.")


def _flight_extras(memory, understood):
    """Which paid extra is worth it depends on which one the line names."""
    text = (understood.get("clean") or "").lower()
    if "legroom" in text or "leg room" in text or "exit row" in text:
        return ("Extra legroom earns its money on a flight over about four hours, or if you are "
                "tall; on a two-hour hop it buys very little. An exit row has the most space of all, "
                "but the seat next to you may not recline, the bags have to go in the overhead "
                "locker, and you have to be able and willing to open the door and help - so read the "
                "airline's rules before you pay.")
    if "priority" in text or "speedy" in text:
        return ("Priority boarding is worth paying for when you are travelling with only a cabin "
                "bag on a full flight: it gets you on early enough to find space overhead, and a bag "
                "that gets gate-checked is one you wait for at the carousel at the other end. With a "
                "checked bag in the hold there is nothing to win, so keep the money.")
    return ("Choosing your seat is worth paying for when you are travelling with somebody and want "
            "to sit together, or you want a window to sleep against; most airlines seat a child next "
            "to a parent for free, so a family does not need to buy it. On a short flight with an "
            "aisle seat left over anyway, save the money.")


def _passport_lost(memory, understood):
    """Today's emergency, or a passport that went missing long ago and needs replacing."""
    text = understood.get("clean") or ""
    if any(phrase in text for phrase in ("last year", "years ago", "a while ago", "long ago")) \
            or re.search(r"\b(?:19|20)\d{2}\b", text):
        return ("A passport reported lost stays cancelled even if it turns up, so you can't fly on "
                "it. Apply for a new one now and ask for an urgent appointment if the trip is "
                "close; take your old passport number and a police report if you have one.")
    return ("Report it to the local police and get a written report, then contact your embassy or "
            "consulate for an emergency travel document. Take the police report, a passport photo "
            "and any copy of the old passport. In most of Europe this takes a day or two; tell your "
            "airline and travel insurer as well, and keep the report for the insurance claim.")


# --- what you may carry on the plane ----------------------------------------------
#
# "can i take a razor in hand luggage", "can i take scissors in hand luggage" and "can i take a
# power bank on a plane" were the search hedge, and "can i take a penknife in hand luggage" and
# "can i take a screwdriver in hand luggage" were the size-and-weight allowance, which answers a
# different question. Security rules are a short list of named things, so they are kept as one
# table of (pattern, sentence) and read by the thing the line names.
_CABIN_RULES = (
    # batteries first: they are the one thing that must not go in the hold, whatever else the
    # line says ("can i take a power bank in my suitcase" is still a no)
    (r"\b(?:power banks?|batter(?:y|ies)|lithium|vapes?|e-?cigarettes?)\b",
     "Power banks and spare batteries go in the cabin bag and never in the hold, with the "
     "terminals taped or each one in its own bag; a vape goes in the cabin too, and its liquid "
     "has to fit in the 100ml bag."),
    (r"\b(?:laptops?|tablets?|ipads?|kindle|phones?|mobiles?|cameras?|hairdryers?|straighteners?|"
     r"chargers?|headphones?|e-?readers?)\b",
     "Electronics are fine in the cabin bag: a laptop, tablet, phone, camera, charger or "
     "hairdryer all go through security, though the laptop comes out of the bag into its own "
     "tray. A lithium battery is the only part that matters, and it stays with you in the cabin."),
    (r"\b(?:wine|beer|spirits|alcohol|whisky|whiskey|gin|vodka|rum)\b",
     "In the cabin bag only 100ml is allowed, so a bottle of wine goes in the suitcase, or buy it "
     "in the duty-free shop after security and keep the receipt and the sealed bag for the "
     "connection. Check your destination's duty-free allowance before you buy more than a couple."),
    (r"\b(?:disposable razors?|razors?|shaving|shave|shaver)\b",
     "A disposable or cartridge razor is fine in the cabin bag; loose blades are not, since they "
     "have to be in a cartridge, and a cut-throat razor goes in the hold."),
    (r"\b(?:scissors|scissor|nail scissors|craft scissors)\b",
     "Scissors are allowed in the cabin bag with blades under 6cm, which covers nail and most "
     "small craft scissors; a longer pair goes in the hold."),
    (r"\b(?:tweezers|nail clippers|clippers|nail file)\b",
     "Tweezers and nail clippers are fine in the cabin bag - they are on nobody's banned list."),
    (r"\b(?:knife|knives|penknife|pen knife|pocket knife|swiss army|multi ?tool|blades?)\b",
     "A knife or penknife is not allowed in the cabin: any blade over 6cm, and every folding "
     "pocket knife, goes in the hold, and a multi-tool with a blade goes with it. A blade that "
     "matters to you is worth putting in the suitcase rather than arguing at the tray."),
    (r"\b(?:corkscrew|bottle opener|waiter.s friend)\b",
     "A corkscrew is not allowed in the cabin bag in the UK, and a bottle opener with a blade on "
     "it is the same thing to a scanner: both go in the hold."),
    (r"\b(?:screwdrivers?|tools?|hammer|spanner|wrench|pliers|drill bits?|allen keys?)\b",
     "Tools go in the hold: a screwdriver, pliers, a spanner or a hammer will be taken off you at "
     "security. A small screwdriver for glasses is usually let through, but pack it rather than "
     "count on it."),
    (r"\b(?:lighters?|matches|lighter fluid|zippo)\b",
     "One disposable lighter can go on you, not in the cabin bag and not in the hold; matches are "
     "one small box on you. Lighter fuel and refillable lighters with fuel in them are not allowed "
     "at all, so leave them at home."),
    (r"\b(?:deodorant|perfume|aftershave|toothpaste|shampoo|shower gel|sun ?cream|sunscreen|"
     r"hand gel|hand sanitiser|make ?up|moisturiser|hairspray|spray|contact lens solution)\b",
     "Anything liquid, gel, paste or aerosol - deodorant, perfume, toothpaste, sun cream - has to "
     "go in the 100ml clear bag, so buy the travel size or decant it into a small bottle. A "
     "roll-on and a solid stick are not liquids and are easier to carry."),
    (r"\b(?:food|sandwiches?|snacks?|fruit|bananas?|apples?|oranges?|cheese|cake|chocolate|"
     r"biscuits?|crisps|nuts|chewing gum|sweets|milk|baby milk|breast milk)\b",
     "Food is fine in the cabin bag - sandwiches, fruit, cheese, cake, even a banana. Only "
     "liquids are limited, so a yoghurt or a drink still has to be 100ml, and there is a bin "
     "before security for anything over."),
    (r"\b(?:liquid|liquids|toiletries|100ml|100 ml)\b",
     "Only containers of 100ml or less, all fitting in one clear plastic bag, can go through "
     "security. Fill an empty bottle after security, or ask for water on the plane."),
    (r"\b(?:water bottles?|bottles?|water|drinks?|juice|squash)\b",
     "A bottle is fine through security as long as it is empty: fill it at a fountain after the "
     "checkpoint, or ask for water on the plane."),
)
# The banned list, said either way round: the line that names a thing is told yes first, and the
# line that asks what is banned gets the list without a "yes" in front of it.
_CABIN_NOT_ALLOWED = (
    "{yes}knives and penknives, tools, scissors with blades over 6cm, a corkscrew, more than "
    "100ml of liquid, lighters with fuel in them, and fireworks or flammables. Clothes, books, "
    "food, chargers and a laptop all go in the cabin bag. Power banks and spare batteries are the "
    "other way round - cabin bag only, never the hold. The rules are set per country, so a long "
    "connection is worth checking, and the airline's own page lists what it will not carry."
)
_CABIN_YES = ("Yes, unless it is one of the short banned list: ", "")
_CABIN_LIST = ("What is banned is a short list: ", "Below is the short banned list: ")
_IN_THE_HOLD_ITSELF = (
    "A bag goes in the hold as your checked bag: 20 to 23kg is the usual limit, and it is around "
    "£20 to £45 each way if you book it online with the ticket rather than at the desk. Keep the "
    "power banks, spare batteries and anything with a lithium cell in the cabin bag, not the hold."
)
_IN_THE_HOLD = (
    "In the suitcase it can go: the hold has no 100ml rule and no blade rule, and it is the cabin "
    "bag that is searched. Pack it so it cannot move - clothes round it, nothing sharp against the "
    "shell - and keep batteries, power banks and anything with a lithium cell out of the hold."
)


def _cabin_named(text):
    """The sentence for the thing the line names, or None when it names nothing this row knows."""
    for pattern, sentence in _CABIN_RULES:
        if re.search(pattern, text):
            return sentence
    return None


def _cabin_guard(understood):
    """Keep this row off the packing question, so `pack-hand-luggage` keeps the turn it has.

    "how do i pack for a week in hand luggage" names a bag and a verb this row keys on, and the
    answer it wants is a list of clothes. A line that names a thing - "can i pack a razor in hand
    luggage" - is still this row's, so only the packing line without a thing stands it down.
    """
    text = (understood.get("clean") or "").lower()
    if re.search(r"\b(?:pack|packs|packing|packed)\b", text) and not _cabin_named(text):
        return False
    return True


# "Take home" and "bring home" wear two hats: the allowance ("how much wine can i take home from
# france") and the wage ("what does take home mean", "i bring home about 1800"). The row's own pay
# fence catches the nouns - pay, salary, after tax - but not the definitional asks, which carry no
# pay word at all. A wage is only ever asked about with the verb and the ask against each other, so
# those patterns are matched next to each other rather than anywhere in the line: the reading a
# guard sees has the earlier turns' words carried along, and a loose test would fire on them.
_A_PAY_ASK_AT_HOME = re.compile(
    r"\bhow\s+much\s+(?:will|would|should|do|does|did)\s+(?:i|we)\s+(?:take|bring)\s+home\b"
    r"|\b(?:will|would|do|does|did)\s+(?:i|we)\s+(?:take|bring)\s+home\b"
    r"|\b(?:take|bring)\s+home\s+(?:mean|means|pay|after\s+tax|before\s+tax|net|gross)\b"
    r"|\bwhat\s+(?:does|do)\s+(?:that\s+|it\s+)?(?:mean\s+for\s+)?(?:my\s+|the\s+)?"
    r"(?:take|bring)\s+home\b"
    r"|\bwhat\s+does\s+(?:\w+\s+){0,4}mean\b.{0,24}\b(?:take|bring)s?\s+home\b"
    r"|\bmean\s+for\s+my\s+(?:take|bring)\s+home\b"
    r"|\b(?:take|bring)\s+home\s+(?:meaning|definition|defined)\b"
    r"|\bwhat\s+is\s+(?:my\s+|the\s+|a\s+)?(?:take|bring)\s+home\b"
    r"|\b(?:explain|define|meaning\s+of)\s+(?:the\s+|my\s+|a\s+)?(?:take|bring)\s+home\b"
    r"|\b(?:i|we)\s+(?:take|bring|takes|brings|took|brought)\s+home\s+"
    r"(?:\d|\u00a3|about|around|roughly|nearly)\b", re.I)
# The allowance is always asked about a thing you carry, or with the customs words in the line.
_A_GOODS_WORD = re.compile(
    r"\b(?:wine|wines|beer|beers|spirits|whisky|whiskey|vodka|gin|rum|alcohol|"
    r"cigarettes?|cigs?|tobacco|baccy|perfume|gifts?|presents?|souvenirs?|chocolates?|"
    r"coffee|tea|clothes|booze)\b", re.I)
_A_CUSTOMS_WORD = re.compile(
    r"\b(?:duty[- ]free|customs|allowance|allowances|limit|limits|declare|declaring|declared|"
    r"red\s+channel|green\s+channel|border|airport|abroad|overseas|back\s+from|home\s+from|"
    r"france|spain|portugal|greece|italy|ireland|germany|holland|belgium)\b", re.I)


def _not_a_wage(understood):
    """A pay question is not a customs question, even when both say "take home".

    "what does take home mean" is net pay and "what does that mean for my take home" is the same
    question with the phrase at the end; neither carries a pay word, so the fence above cannot see
    them and the customs table answered both. A line that names something to carry, or says
    customs at all, is still this row's: "how much wine can i take home from france" keeps its
    table, and nothing but the pay shapes is stood down.
    """
    text = (understood.get("clean") or "")
    if not _A_PAY_ASK_AT_HOME.search(text):
        return True
    return bool(_A_GOODS_WORD.search(text) or _A_CUSTOMS_WORD.search(text))


# The allowance row already has a guard of its own, and an entry takes only one `guard=`: the
# wage test is declared here by row id and folded into that guard when the knowledge base is
# read, so the two conditions both hold and neither line is written beside the other.
GUARD_FOLDS = {"duty-free": _not_a_wage}


def _cabin_rules(memory, understood):
    """Which named thing the line is about decides the sentence; a bare rule line gets the list."""
    text = (understood.get("clean") or "").lower()
    if re.search(r"\bhow (?:much|many)\b.{0,20}\b(?:liquid|liquids|water|drink|drinks|ml)\b",
                 text):
        return FLIGHT_LIQUIDS
    if re.search(r"\bhow (?:much|many|big|large|heavy)\b.{0,30}\b(?:luggage|baggage|bags?|"
                 r"cabin bag|kilos?|kg|weight)\b", text):
        # the size and weight of the bag is the allowance row's question
        return ""
    if re.search(r"\b(?:take (?:it |them |my \w+ )?out|out at security|out of my bag|"
                 r"out of the bag)\b", text):
        # what happens at the tray is the airport-security row, which also covers shoes and belts
        return ""
    # the packing question never reaches this row (see _cabin_guard), since the answer to it is
    # a list of clothes; a line that names a thing gets to it, "can i pack a razor in hand luggage"
    named = _cabin_named(text)
    # batteries and vapes are answered above and are held back from the hold, so the hold answer
    # belongs only to what may actually travel there
    if named and named.startswith(("Power banks", "In the cabin bag only 100ml")):
        return named
    hold = re.search(r"\b(?:suitcase|hold|checked bag|checked in luggage|checked luggage|"
                     r"holdall)\b", text)
    if hold and not named:
        return _IN_THE_HOLD_ITSELF
    if hold:
        return _IN_THE_HOLD
    if named:
        return named
    banned = re.search(r"\bnot allow|banned|prohibit|forbidden|cannot take|can.t take|"
                       r"not take|what can.t i|what can i not|what am i not", text)
    if banned:
        # "what am i not allowed to take on a plane" wants the list itself, and a yes in front of
        # it answers nothing
        return _CABIN_NOT_ALLOWED.format(yes=_CABIN_LIST[0])
    if re.search(r"\b(?:cabin bag|cabin bags|hand luggage|hand baggage|carry ?on|carry ?ons|"
                 r"luggage|baggage|backpack|suitcase|bag)\b", text):
        # "can i take a cabin bag" is the allowance question about the bag itself
        return ""
    # "can i take a coat on a plane" wants a yes in front of the list
    return _CABIN_NOT_ALLOWED.format(yes=_CABIN_YES[0])


# --- where to go in a given month -----------------------------------------
#
# "where should i go for a week in october" was a shrug. The bot knows a great deal about a place
# once it is named - when to go, what a day costs, what the weather does - but nothing about
# turning a month into three places worth considering, which is the question people actually send
# when they have a week off. Kept as data: one row per month, and the entry picks the row the
# line names, so a new month is a line of text rather than a rule.
_MONTH_PICKS = {
    "january": (
        "the Canaries for 20C and real sun, the Alps for snow, or Seville for a city break in "
        "warmth, and the first week of January is the cheapest week of the year to fly"),
    "february": (
        "the Canaries or Cape Verde for proper sun, Venice for carnival, or Marrakesh for 20C "
        "days, and half term is the one week to book around"),
    "march": (
        "Marrakesh or Seville at about 20C, Rome and Florence before the queues start, or "
        "Lanzarote for reliable sun"),
    "april": (
        "Lisbon or Andalusia at 20C, Sicily before the heat arrives, or the tulips in the "
        "Netherlands, and Easter moves the prices"),
    "may": (
        "Greece or Croatia before the crowds, the Algarve, or the Italian lakes, with the sea "
        "warm enough in the south by the end of the month"),
    "june": (
        "the Greek islands, the Algarve or the Baltic cities, and the first half of the month "
        "is quieter and cheaper than the second"),
    "july": (
        "Scotland or the Alps for cool walking, Norway and Denmark for cities, or the Atlantic "
        "coast of Portugal for a sea breeze - the Mediterranean is at its hottest now"),
    "august": (
        "Scotland, Ireland, the Alps or Norway: the Mediterranean is at its busiest, hottest "
        "and priciest, and Italian and Spanish towns close up at midday"),
    "september": (
        "Greece, Croatia or Italy, because the sea is at its warmest now and the families have "
        "gone home, so the same room costs less"),
    "october": (
        "Cyprus or Crete for 24C and a sea you can still swim in, the Canaries for the most "
        "reliable sun, or Seville and Marrakesh for warm cities without the crowds"),
    "november": (
        "the Canaries, Egypt or Cape Verde for sun, or Rome, Prague and Budapest for cheap "
        "cities without queues"),
    "december": (
        "the Canaries or Cape Verde for sun, the Alps for snow, or any big European city for "
        "the Christmas markets - book before the middle of the month"),
}
# "somewhere hot in december" is the same question with the sea and the temperature named, and
# sending it to the Alps would be the wrong half of the answer. The winter months have their own
# short list of places that are genuinely warm then; in the summer months the main list is
# already the warm answer.
_MONTH_SUN = {
    # Every month has a sun list, not just the winter ones: "where should i go in august for sun"
    # was picking up the August paragraph, which is Scotland and the Alps - the right answer for a
    # walk and the wrong one for a sun seeker.
    "january": ("the Canaries for 20C, Cape Verde for 25C, or Egypt for 22C and a sea you can "
                "swim in"),
    "february": ("the Canaries, Cape Verde or Egypt, all about 20 to 25C, and the Red Sea coast "
                 "is the warmest water"),
    "march": ("Lanzarote or the other Canaries for 20C, Marrakesh for 22C, or Dubai if you want "
              "30C in the shade"),
    "april": ("the Algarve or Andalusia for 22C, Malta for 20C, or the Canaries to be sure of it"),
    "may": ("Greece, Cyprus or southern Spain, 24-27C, with the sea warming up and the prices "
            "before the school holidays"),
    "june": ("the Greek islands, Croatia or Sicily, 27-30C and the sea warm enough to swim"),
    "july": ("the Algarve, Croatia or the Greek islands, 28-31C, with the sea at its warmest"),
    "august": ("Portugal, Croatia or Greece, 28-31C and reliably dry, or the Baltic if 30C is too "
               "much"),
    "september": ("Greece, Croatia or southern Italy, 26-29C, with the sea at its warmest now the "
                  "schools are back"),
    "october": ("Cyprus, Crete or the Canaries, 24-26C, and the sea is still swimmable"),
    "november": ("the Canaries, Egypt or Cape Verde, and the Red Sea is the warmest of the three"),
    "december": ("the Canaries or Cape Verde for 25C, Egypt for 22C, or the Caribbean if you want "
                 "guaranteed heat"),
}
_MONTH_SUN_ASK = ("sun", "sunny", "hot", "warm", "beach", "swim", "swimming", "heat", "tan",
                  "sunshine", "sea")

# The verdict on a month with no place named yet: "a cheap week away in august" then "is that a
# good time to go". The places for each month are already above; what the follow-up wants is
# whether, and the one trade-off the month brings, without the list read out a second time.
_MONTH_VERDICT = {
    "january": ("good for sun or snow and the cheapest, quietest month of the year, but the "
                "Mediterranean is cold and half shut"),
    "february": ("still low season, so cheap and quiet, with real sun only a few hours south "
                 "and half term the week everyone else books"),
    "march": ("spring arriving while the prices are still low, though the Mediterranean is "
              "mild rather than warm and Easter moves the cost"),
    "april": ("one of the best months for southern Europe - warm, quiet and cheaper than May - "
              "with Easter the week to book around"),
    "may": ("warm without the crowds, with the sea warm enough in the south by the end of it "
            "and the school holidays still a month away"),
    "june": ("the sweet spot before the schools break up: hot, long days and prices that have "
             "not caught up with July"),
    "july": ("high season, so hot, busy and priced for it, and the Mediterranean coast is at "
             "its fullest"),
    "august": ("the busiest, hottest and priciest month of the year, so go north, go high or go "
               "early"),
    "september": ("the best month of the year for most of Europe: the sea at its warmest, the "
                  "families gone and the rooms cheaper"),
    "october": ("still warm in the south with the crowds gone, though the north turns wet and "
                "some hotels shut for the winter"),
    "november": ("cheap and quiet with short days, and real sun only in the Canaries, Egypt or "
                 "the Cape Verde islands"),
    "december": ("cold at home and festive in the cities, with sun a few hours south and the "
                 "Christmas weeks to book early"),
}


_MONTH_ASK = ("where", "go", "going", "holiday", "away", "break", "week", "trip", "travel",
              "visit", "somewhere", "destination", "escape", "sun", "hot", "warm",
              "recommend", "suggest", "idea", "ideas", "good place", "best place", "good",
              "worth", "ok", "okay", "wise", "sensible",
              # "is cornwall nice in october" is the same ask as "is spain good in october" and
              # was the search hedge: the month and the place were both read, the verdict between
              # them was not. Bare "like" is deliberately not here - "i like spain in may" is not
              # a question.
              "nice", "nice in", "nice weather", "any good", "good in", "worth visiting",
              "worth going")

# A month plus one of these is a question about money or about booking, and the row that answers
# it holds the prices and the booking windows: "when should i book flights for august" is not a
# request for three places. Bare "cheap" is not here - "a cheap week in march" is the month's own
# question and the places answer it.
_MONTH_NOT_A_PLACE = ("book", "booking", "booked", "flight", "flights", "fly", "airfare",
                      "cheapest", "expensive", "price", "prices", "cost", "costs", "how much",
                      "much does", "spending", "spending money", "budget for",
                      "fare", "fares", "refund", "insurance", "visa")

# A phrase has to be found inside the sentence, not in its list of words: "how much is a week in
# october" opens with the phrase, and a bare " how much" test only found it in the middle.
_MONTH_NOT_A_PLACE_RE = re.compile(
    r"\b(?:%s)\b" % "|".join(re.escape(word) for word in _MONTH_NOT_A_PLACE))

# A month is the row's question only when the line is asking where. The words that ask are an ask
# word, a wish ("i want a holiday in october", "we should go away in june") or a plan with the place
# left open and no subject at all ("a holiday in october", "somewhere hot in december"). A line that
# speaks about their own plan - "we are going in june", "we are away in june for a week", "our
# holiday is in july", "i signed up in january and ive moved away" - gives the dates of a trip that
# is already decided, and the three places are an answer to a question nobody asked: the gym chat
# was handed January in the Canaries.
_WHERE_IN_THE_LINE = ("where", "which", "anywhere", "somewhere", "best place", "good place",
                      "nice place", "recommend", "suggest", "idea", "options", "worth",
                      "should", "shall", "could we", "can we", "do you think", "what about",
                      "how about", "want", "need", "fancy", "would like", "i'd like", "id like",
                      "thinking of", "thinking about", "looking for", "considering", "wondering",
                      "hoping", "planning", "keen", "interested", "hot enough", "warm enough")
# A line about their own plan has a person in it: "we", "my holiday", "i signed up". It is only a
# report when nothing in it asks for a place, which is why the two lists are read together.
_SAYS_THEIR_OWN_PLAN = re.compile(
    r"\b(?:i|im|i'm|i am|i've|ive|we|we're|we are|we've|weve|were|he|he's|she|she's|they|"
    r"they're|you|you're|my|our|his|her|their)\b", re.I)


# The words that make a month a month away rather than a month in a life: a trip named, or the
# person away. "ive moved away" is not one - the away has to be their own ("we are away", "im away").
_ABOUT_A_TRIP = re.compile(
    r"\b(?:going|go|goes|went|holiday|holidays|trip|trips|travel|travelling|traveling|fly|flying|"
    r"flight|flights|booked|vacation|getaway|honeymoon|city break|staying|visiting|visit|abroad)\b"
    r"|\b(?:im|i'm|i am|we are|we're|were|we've|we have|i've|ive)\s+(?:away|off)\b", re.I)


def _a_report_of_their_own(clean, month):
    """True when the month sits in a clause that speaks about the person's own plan.

    Only the clause the month is in counts: "we are going in june" is a report and gets the
    question back, and "we are flexible, a holiday in october" is the row's own question because
    the month is in the second clause and nothing in that clause is about a plan already made.
    """
    at = re.search(r"\b%s\b" % re.escape(month), clean)
    if not at:
        return False
    start = 0
    for edge in re.finditer(r"[,;:!?](?:\s|$)|\.(?:\s|$)", clean):
        if edge.end() <= at.start():
            start = edge.end()
        elif edge.start() >= at.end():
            return bool(_SAYS_THEIR_OWN_PLAN.search(clean[start:edge.start()]))
    return bool(_SAYS_THEIR_OWN_PLAN.search(clean[start:]))


def _named_place(text, table):
    """The keys of table the line names as whole words, longest first."""
    found = []
    for name in sorted(table, key=len, reverse=True):
        if re.search(r"\b%s\b" % re.escape(name), text) and _names_place(text, name):
            found.append(name)
    return found


_MONTH_WORSE = re.compile(
    r"\b(hot|hotter|hottest|packed|crowded|busy|busiest|wet|wettest|grey|rain|rainy|rains|cold|"
    r"coldest|freezing|closed|shut|avoid|peak|worst|humid|storm|hurricane|mosquitoes|insects|"
    r"dark|pricey|expensive|heat)\b", re.IGNORECASE)


# Whether the line put the month as a question. A verdict word answers a question: "No, August is
# not the best month for Cornwall" is the right reply to "is cornwall good in august", and a
# contradiction aimed at somebody who only said when they were going. The line's own kind is what
# tells the two apart, not a question word: "were planning a week in cornwall in august" is "we are
# planning" typed without the apostrophe and opens on a word that also opens a question.
#
# `_month_destination` is the only place that sets it, and both calls to the function below are
# inside it, so the reading is one line and no caller can pick up another turn's answer.
_MONTH_ASKED = True
# A finite verb in the first clause of a window: "June to August gives midnight sun" is a sentence
# of its own, where "April to June and September to October, when it is 20-28C" is a time phrase
# the sentence "The window is ..." can hold. Read only up to the first colon: "May, June: warm sea,
# open tavernas" is a time phrase with a description after it, not a clause of its own.
_A_CLAUSE_VERB = re.compile(
    r"\b(?:is|are|was|were|gives|give|gets|get|has|have|holds|means|brings|sees|closes|runs|"
    r"run|makes|make|leaves|leave)\b")


def _a_month_for_a_place(name, window, month):
    """What a month means for one place: a yes, a no, or the window itself.

    Shared by a place named in the line and a place the chat is already on, so the two cannot
    answer the same question differently.

    "is cornwall good in august" wants the verdict. The same words said to somebody who only
    told you the plan - "were planning a week in cornwall in august" - get the window without
    the verdict word in front, because the window is the whole of the answer either way and only
    the "No," is held back.
    """
    asked = _MONTH_ASKED
    if isinstance(window, tuple):
        window = window[-1]
    label = name if name[:1].isupper() else name.capitalize()
    # The window text gives the good months first and the ones to avoid after, so a yes or a no
    # is only claimed where the clause the month sits in says it: "July and August are 35C+
    # inland" is a no, "February and March are best for the northern lights" is a yes, and a
    # month in neither clause just gets the window.
    clauses = [part for part in re.split(r"(?<=[.;])\s+", window) if part.strip()]
    short = month[:3]
    month_here = re.compile(r"\b(?:%s|%s)\b" % (re.escape(month), re.escape(short)),
                            re.IGNORECASE)
    verdict = ("Yes, ", "No, ") if asked else ("", "")
    if clauses and month_here.search(clauses[0]):
        return f"{verdict[0]}{month.capitalize()} is in the good window for {label}: {window}"
    if any(month_here.search(part) and _MONTH_WORSE.search(part) for part in clauses[1:]):
        # The window can only follow "The window is" when it opens on a time phrase: "June to
        # August gives midnight sun" is a whole sentence, and "the window is June to August gives
        # midnight sun" is not English. Where the first clause has a verb the window goes on its
        # own after the verdict, and both forms are read back by _a_month_verdict_once.
        if _A_CLAUSE_VERB.search(re.split(r"[;.:]", window)[0]):
            return f"{verdict[1]}{month.capitalize()} is not the best month for {label}. {window}"
        return (f"{verdict[1]}{month.capitalize()} is not the best month for {label}. "
                f"The window is {window}")
    return f"{label}: {window}"


# The words that make a month ask a request for places rather than a question about the trip in
# hand: "where should i go in september" wants three ideas even after a trip was named, and the
# month tables are the answer to it.
_AN_OPEN_ASK = frozenset("""
where somewhere anywhere else ideas idea recommend recommends suggestion suggest destination
inspiration options decide choose
""".split())


def _the_place_in_the_chat(memory, table):
    """The place the chat is already on, from the plan or the places the person stated, or None.

    "we are thinking about portugal in august" then "what if we go in late september instead"
    names no place of its own, and the month tables answered it with Greece, Croatia and Italy -
    three places worth going to then, which is a different trip from the one on the table.
    """
    said = []
    user = memory.get("user") or {}
    for key in ("plan", "plans", "places", "city"):
        value = user.get(key)
        if isinstance(value, str):
            said.append(value)
        elif isinstance(value, (list, tuple)):
            said.extend(str(item) for item in value if item)
    text = " ".join(said).lower()
    if not text:
        return None
    return _find_in(text, table)
# --- a week at home, in a month ----------------------------------------------
# The month rows below turn a month into three places abroad worth considering - the right
# answer to "where should i go in october" and the wrong one to "a week in cornwall in
# august", which was handed Scotland, Ireland, the Alps and Norway. A person who has already
# chosen a place at home is asking what the month means for the week they have planned, so
# the answer is the season there, and the shape of the day it makes: book now or not, the
# coast or the hills, the one wet-day plan. Kept as data, one line per place, so a new place
# is a line of text rather than a rule.
_AT_HOME = {
    # the seaside
    "cornwall": "coast", "devon": "coast", "dorset": "coast", "norfolk": "coast",
    "suffolk": "coast", "sussex": "coast", "kent": "coast", "isle of wight": "coast",
    "pembrokeshire": "coast", "anglesey": "coast", "gower": "coast", "newquay": "coast",
    "st ives": "coast", "torquay": "coast", "bournemouth": "coast", "brighton": "coast",
    "blackpool": "coast", "scarborough": "coast", "whitby": "coast", "skegness": "coast",
    "great yarmouth": "coast", "bamburgh": "coast", "tenby": "coast", "aberystwyth": "coast",
    "brixham": "coast", "padstow": "coast", "exmouth": "coast", "falmouth": "coast",
    # the hills and the countryside
    "lake district": "country", "peak district": "country", "yorkshire dales": "country",
    "yorkshire": "country", "cotswolds": "country", "the cotswolds": "country",
    "snowdonia": "country", "brecon beacons": "country", "cumbria": "country",
    "northumberland": "country", "dartmoor": "country", "exmoor": "country",
    "new forest": "country", "the highlands": "country", "highlands": "country",
    "isle of skye": "country", "harrogate": "country", "ludlow": "country",
}
_UK_NATIONS = ("england", "scotland", "wales", "northern ireland")

# What the season changes: three seasons, because they are three different holidays.
_WEEKS_AT_HOME = {
    "peak": ("it is the most expensive and the busiest week or two of the year there, so book "
             "the place to stay now, because the good ones go first. Set off early and travel on "
             "a weekday if you can, book any table, boat or attraction you actually want at "
             "least a week ahead, and keep one wet-day plan in your pocket."),
    "shoulder": ("outside the school holidays it is quieter and a good deal cheaper. Some cafes, "
                 "boat trips and attractions keep weekend hours at the edges of the season, so "
                 "check anything you have your heart set on before you book, and keep one "
                 "wet-day plan."),
    "quiet": ("it is the cheapest and quietest time to go, but the days are short and a lot of "
              "places shut after the school holidays, so check what is open before you book and "
              "plan one thing a day rather than a list. Take waterproofs and boots, and treat a "
              "walk as the plan rather than the filler."),
}
# What the shape of the place changes: a coast has tides and a lifeguard, the hills have car
# parks that fill by ten.
_BY_KIND = {
    "coast": ("Pick your beaches by the tide times rather than by the car park, and swim where "
              "there is a lifeguard."),
    "country": ("The car parks at the popular walks are full by ten, so go early or later in the "
                "afternoon, and take a waterproof even on a fine forecast."),
}
_MONTH_SEASON = {
    "january": "quiet", "february": "quiet", "march": "quiet",
    "april": "shoulder", "may": "shoulder", "june": "shoulder",
    "july": "peak", "august": "peak",
    "september": "shoulder", "october": "shoulder",
    "november": "quiet", "december": "quiet",
}

def _a_week_at_home(name, month, kind):
    """A week the person has already chosen, at home, in the month they named."""
    label = " ".join(word.capitalize() for word in name.split())
    season = _MONTH_SEASON.get(month, "shoulder")
    said = [f"{label} in {month.capitalize()}: {_WEEKS_AT_HOME[season]}"]
    if kind == "coast":
        said.append(_BY_KIND["coast"])
        if month == "september":
            # The one month whose answer is the same everywhere on the coast, so it is said
            # once here rather than in every season's paragraph.
            said.append("The sea is at its warmest of the year in September.")
    else:
        said.append(_BY_KIND["country"])
    return " ".join(said)


# A month in a line about something else is still a travel question when the line names the trip
# itself: "i'm getting married in june and i don't know where to go for the honeymoon" is read as a
# wedding, and the honeymoon is the question. Bare "go" is deliberately not here - "should i keep
# going" is the phrase that put a half marathon in October, and "going" alone named no trip.
_A_TRIP_NAMED = re.compile(
    r"\b(?:holiday|holidays|trip|trips|honeymoon|vacation|getaway|break away|flight|flights|fly|"
    r"flying|abroad|city break|weekend away|booked|booking|staying|stay in|travel|travelling|"
    r"traveling|destination|sightseeing|cruise)\b", re.I)


def _month_destination(memory, understood):
    """The three places a month is good for, when no place is named.

    A place in the line is a different question and the rest of this file answers it better -
    "is spain good in october" wants Spain in October, not three places October suits - so a
    named place leaves this row alone.
    """
    global _MONTH_ASKED
    clean = understood.get("clean", "")
    # A month is this module's question only when the line is about something this module answers.
    # "i'm training for a half marathon in october and my knee hurts, should i keep going?" was
    # handed Cyprus and Crete: the month was read, the ask was in the second clause, and nothing
    # here looked at what the first clause was about. The understanding lane already says what a
    # line is about, and this module already declares the topics it answers in ANSWERS, so the two
    # are compared instead of keeping a list of things a month is not about. A line with no topic
    # at all - "a week in october", "somewhere hot in december" - is still this row's question, and
    # small talk is not a subject that can take a month away from it.
    topics = set((understood or {}).get("topics") or ()) - {"small-talk"}
    # A line that asks where is this module's question whatever else is in it: "where is cheap in
    # october" is read as money, and the place is still what was asked for.
    asks_a_place = any(word in _AN_OPEN_ASK for word in clean.split())
    # The month can sit in the lead-in or in the ask, and the reading already splits the line at
    # the question word: `focus` is the ask clause, and everything before it is context. When the
    # month is inside the ask it is what the person asked about - "is it too hot in august for a
    # baby" is read as family-and-parenting, and standing the row down on that topic handed a
    # weather question to the 38C fever card. When the month is in the lead-in it is the setting,
    # and the half marathon in October is the case this guard was built for. Clause position is a
    # property of the line, so no list of heat words has to be kept.
    ask_clause = " ".join((understood or {}).get("focus") or ())
    asks_the_month = bool(ask_clause) and any(
        re.search(r"\b%s\b" % re.escape(name), ask_clause) for name in MONTHS)
    if (topics and not (topics & set(ANSWERS)) and not asks_a_place
            and not asks_the_month and not _A_TRIP_NAMED.search(clean)):
        return None
    _MONTH_ASKED = (understood or {}).get("kind") == "question" or "?" in clean
    month = None
    found = []
    for name in sorted(MONTHS, key=len, reverse=True):
        match = re.search(r"\b%s\b" % re.escape(name), clean)
        if match:
            found.append((match.start(), match.end(), name))
            if month is None:
                month = name
    if not month:
        return None
    # A month plus a booking word or a price is that row's question, not the places: "when
    # should i book a flight for august" wants the six-to-eight-weeks rule and was being handed
    # the August paragraph. The row's own key is a month, so the line gets here first and the
    # refusal has to be here too.
    if _MONTH_NOT_A_PLACE_RE.search(clean):
        return None
    # Two months side by side is a comparison - "should i go away in august or september" - and
    # answering it with September's three places picks a winner they did not ask for. The word
    # between them is what makes it a pair, so "in august, though it may rain" stays one month.
    found.sort()
    if len(found) > 1:
        between = clean[found[0][1]:found[1][0]]
        if re.search(r"\bor\b|\bvs\b|versus|/", between):
            return None
    # A month with a place is that place's question, and this file has the answer. The place has
    # to be a whole word here: _find_in matches a bare substring, and "us" in "august" is how
    # "where should i go in august for sun" stopped being a month question at all.
    # A place and a month is "is spain good in october", and the honest answer is the window
    # this file already holds for that place plus whether the month sits inside it. Saying only
    # the window leaves the person to do the comparing, which is the work they asked for.
    for table in (WHEN_TO_GO, BEST_TIME):
        for name in _named_place(clean, table):
            return _a_month_for_a_place(name, table[name], month)
    # The place can be in the chat rather than in the line. Asking where to go is still a request
    # for places, so an open ask keeps the month tables even after a trip was named.
    if not any(word in _AN_OPEN_ASK for word in clean.split()):
        for table in (BEST_TIME, WHEN_TO_GO):
            in_hand = _the_place_in_the_chat(memory, table)
            if in_hand:
                return _a_month_for_a_place(in_hand, table[in_hand], month)
    # A place at home, from the line or from the chat: a trip named two turns ago and a month
    # asked about now is the same week with a different month on it, so it gets the season
    # there rather than three places abroad. Read after the windows, so a place with a best
    # time keeps it, and behind the open-ask guard above for the same reason.
    for name in _named_place(clean, _AT_HOME):
        return _a_week_at_home(name, month, _AT_HOME[name])
    for table in (CITY_COUNTRY, AIR_HOURS_CITY):
        for name in _named_place(clean, table):
            if table[name] in _UK_NATIONS:
                return _a_week_at_home(name, month, "country")
    if not any(word in _AN_OPEN_ASK for word in clean.split()):
        in_hand = _the_place_in_the_chat(memory, _AT_HOME)
        if in_hand:
            return _a_week_at_home(in_hand, month, _AT_HOME[in_hand])
        for table in (CITY_COUNTRY, AIR_HOURS_CITY):
            in_hand = _the_place_in_the_chat(memory, table)
            if in_hand and table[in_hand] in _UK_NATIONS:
                return _a_week_at_home(in_hand, month, "country")
    # anything else named is a place with its own question, and a month is not the way in
    for table in (WHERE_TO_GO, COUNTRY_ALIASES, CITIES, CAPITALS):
        if _named_place(clean, table):
            return None
    # A month inside a trip that is already settled is a date, and the three places are an answer
    # to a question the person did not ask. Only a line that asks where keeps the row, and a line
    # that gives the dates gets the one thing worth asking back: where, because the weather and the
    # cost of a day are the answers that follow from it and this file holds both.
    if _a_report_of_their_own(clean, month) and not any(word in clean
                                                        for word in _WHERE_IN_THE_LINE):
        # The plan is about a trip, so the question worth asking is where: this file answers the
        # weather and the cost of a day once the place is named. A month in a line about something
        # else entirely - "i signed up in january and ive moved away" - is somebody else's answer,
        # and asking them where they are going in January would be a worse reply than silence.
        if not _ABOUT_A_TRIP.search(clean):
            return None
        return (f"Where are you going in {month.capitalize()}? Tell me the place and I'll say what "
                f"the weather does there and what a day costs.")
    if "ski" in clean or "snow" in clean:
        return (f"In {month.capitalize()}: the Alps for snow, with a resort at 1,500m or above "
                f"for the best chance of it, and book the transfer with the room.")
    if month in _MONTH_SUN and any(word in clean.split() for word in _MONTH_SUN_ASK):
        return f"{month.capitalize()}: {_MONTH_SUN[month]}."
    picks = _MONTH_PICKS[month]
    return f"{month.capitalize()}: {picks}."


def _month_names():
    return tuple(sorted(MONTHS, key=len, reverse=True))


# --- the month pointed back at ------------------------------------------------
# The month row is keyed on a month being in the line, so the follow-up that points back at it -
# "we are thinking of a cheap week away in august" then "is that a good time to go", or "is it a
# good time of year" - had no month of its own to match and fell through to the punt. The month is
# one the person named a turn or two ago about the same trip, so the verdict is the answer they are
# asking for, and that sentence is the verdict row's own: this row only finds the month for it.
_A_MONTH_POINTED_AT = ("that one", "those dates", "those weeks", "the same", "the month",
                       # ... and the time itself, named without the month: "is it a good time of
                       # year" is the same ask as "is august a good time", and the year, the
                       # month and the season are the words it asks it with. A bare "it" or
                       # "that" is not on the list: "is it worth it" is asked about the gym, the
                       # house or the course in the chat, and a travel row that took it would
                       # stand in front of the answer they want.
                       "year", "month", "season", "time", "trip", "holiday", "week",
                       "away")
# The asks that word the question as a fault in the month - "is it too cold", "too busy", "will it
# rain" - rather than as a judgement of it. "Yes, for the place it suits" cannot lead one of those:
# yes to "too cold" says the month is too cold, and the clause after it says it is still warm in
# the south. What answers them is the trade-off the month brings, which is the verdict sentence
# itself, so it leads on its own. Bare "hot" and "warm" are not here: those are the sun asks, and
# the sun list is a better answer to "is it hot in august" than the trade-off is.
_A_MONTH_FAULT_ASK = ("too hot", "too cold", "too cool", "too wet", "too busy", "too crowded",
                      "too quiet", "too damp", "too rainy", "too windy", "rain", "raining",
                      "rains", "wet", "chilly", "muggy")
_A_TIME_VERDICT_ASK = ("good time", "good time to go", "good time of year", "good time to visit",
                       "worth it", "worth going", "worth a visit", "any good", "good idea",
                       "a good month", "good month", "bad time", "too hot", "too cold",
                       "too wet", "too busy", "rainy", "rain much", "sunny enough")
# The words a line can be made of and still be nothing but the ask: a line with any other word in
# it names something of its own, and the month's window says nothing about that thing.
_A_VERDICT_FILLER = frozenset("""
    is are was were be been am do does did the a an of to in on at for with about it that this
    these those there then so and but or we us our i my me you your they them he she his her
    good time year month season day days worth going go goes visit visiting trip holiday week
    weeks away any much too hot cold wet busy rainy sun sunnier sunny nice ok okay fine idea
    really still think sounds sound going then instead make difference much
""".split())
# How far back the month is looked for: the ask comes one or two turns after the month, and a month
# named four turns ago in the same trip is still the month they mean.
_MONTH_LOOKS_BACK = 4
# A month in a turn about a trip is the month of the trip; a month in any other turn is somebody
# else's answer, so the trip words are read on their own rather than borrowing _ABOUT_A_TRIP: the
# commonest way of naming a month for a trip names no verb at all ("a cheap week away in august").
_A_MONTH_OF_A_TRIP = re.compile(
    r"\b(?:week|weeks|weekend|weekends|break|holiday|holidays|trip|trips|travel|travelling|"
    r"traveling|abroad|getaway|honeymoon|fly|flying|flight|flights|visit|visiting|stay|staying|"
    r"days|away|time off|city break|somewhere"
    # "im going to spain in july" is how people name the month most often, and it names no noun of
    # the list: the going is the trip word. Kept to the going-towards-the-place forms ("going to",
    # "go to", "went to") so that "it went wrong in july" is not a trip.
    r"|going to|go to|goes to|went to|heading to|off to|flying to|travel to)\b", re.I)


def _the_month_named_in(text):
    """The month a piece of text names, read the way _time_terms reads one, or None.

    "may" and "march" are ordinary words as well as months, so a bare one is not a date and
    only a month the sentence puts in time ("in May", "early March") counts.
    """
    low = " ".join(str(text or "").lower().split())
    if not low:
        return None
    words = set(low.split())
    for match in _MONTH_IN_TEXT.finditer(low):
        return match.group(1)
    for name in _month_names():
        if name in AMBIGUOUS_MONTHS:
            continue
        if name in words:
            return name
    return None


def _the_month_in_the_chat(memory):
    """The month the person named a turn or two ago about a trip, or None.

    Only a month in a turn that is about a trip counts. "i moved in january" then "is that a good
    idea" is not a travel question, and the trip word is what tells the two apart.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return None
    said = []
    for turn in turns[-_MONTH_LOOKS_BACK:]:
        text = str((turn if isinstance(turn, dict) else {}).get("user") or "").lower()
        if text:
            said.append(text)
    for text in reversed(said):
        if not _A_MONTH_OF_A_TRIP.search(text):
            continue
        month = _the_month_named_in(text)
        if month:
            return month
    return None


def _the_verdict_on(month, memory, clean):
    """Whether a month is a good time, for the place the chat is on or in general."""
    # A place already in the chat is that place's question, and this file holds the window for it:
    # "we are going to portugal in august" then "is that a good time to go" wants whether August
    # sits inside Portugal's window, which is a better answer than any verdict about the month.
    for table in (BEST_TIME, WHEN_TO_GO):
        in_hand = _the_place_in_the_chat(memory, table)
        if in_hand:
            return _a_month_for_a_place(in_hand, table[in_hand], month)
    in_hand = _the_place_in_the_chat(memory, _AT_HOME)
    if in_hand:
        return _a_week_at_home(in_hand, month, _AT_HOME[in_hand])
    # The month was named for a place in an earlier turn and this line points back at it. The
    # places for each month are the answer to "where should i go", and they have just been read,
    # so what is left to answer is whether - and the one trade-off the month brings.
    if any(word in str(clean or "").split() for word in _MONTH_SUN_ASK):
        return f"{month.capitalize()}: {_MONTH_SUN[month]}."
    if any(ask in str(clean or "").lower() for ask in _A_MONTH_FAULT_ASK):
        # The trade-off is the answer here, and a "Yes" in front of it would say the opposite of
        # the clause that follows - see _A_MONTH_FAULT_ASK.
        return f"{month.capitalize()} is {_MONTH_VERDICT[month]}."
    return f"Yes, for the place it suits. {month.capitalize()} is {_MONTH_VERDICT[month]}."


def _a_month_verdict_pointed_at(memory, understood):
    """The verdict on the month the chat is on, when the line points back at it."""
    clean = str((understood or {}).get("clean") or "")
    if any(re.search(r"\b%s\b" % re.escape(name), clean.lower()) for name in MONTHS):
        return None  # the line names its own month, and the month row answers that one
    # The line has to be the ask and nothing else. "is the eden project worth it" after a week in
    # Cornwall in August points at nothing in the month answer - it names a thing of its own, and
    # the month's window is not an answer about the Eden Project.
    if any(word for word in clean.split()
           if len(word) > 2 and word.strip(".,!?'") not in _A_VERDICT_FILLER):
        return None
    month = _the_month_in_the_chat(memory)
    if not month:
        return None
    return _the_verdict_on(month, memory, clean)


# --- planning a trip -----------------------------------------------------------
# "how do i plan a trip to japan" is one of the commonest travel lines there is, and it is not a
# question about a place at all: it is about the shape of the trip - how many bases, what to book
# early, where to leave the loose days. The country tables say when to go, which is the other half.
# "itinerary" is in the shape list only: with it in both, it covered one position twice and
# "whats a good itinerary for three weeks" needed two, so the row answered nothing at all.
_PLAN_TALK = ("plan", "planning", "planned", "organise", "organising", "organize", "organizing",
              "put together", "help me", "give me", "want to", "need to", "best way",
              "figure out", "good", "great", "suggest", "recommend", "ideas",
              # "start" alone is a verb about anything that begins - a job, a course, a baby -
              # and the shape word that goes with it can be a length, so "my job starts in two
              # weeks" was planned as a trip. Only the starting of the planning is the ask.
              "start planning", "starting to plan", "start to plan", "where to start",
              "get started", "getting started")
_PLAN_SHAPE = ("trip", "trips", "holiday", "vacation", "time away", "days away", "week away",
               "two weeks", "itinerary", "city break")

# How long the trip is decides how many bases it takes. A number of days is read as a number of
# bases, which is the thing people get wrong: five cities in ten days is a coach tour, not a trip.
_TRIP_LENGTH = (
    (re.compile(r"\b(?:three|3)\s+weeks?\b|\b(?:20|21)\s+days\b"), "three weeks", 21),
    (re.compile(r"\b(?:two|2)\s+weeks?\b|\b(?:14|13|12|11|10)\s+days\b|\bten days\b"),
     "two weeks", 14),
    (re.compile(r"\b(?:one|1)\s+week\b|\ba week\b|\b(?:seven|7)\s+days\b"
                r"|\b(?:five|5)\s+days\b|\b(?:six|6)\s+days\b"), "a week", 7),
    (re.compile(r"\bweekend\b|\b(?:two|2|three|3)\s+nights\b"), "a weekend", 3),
)

# The words that make a length of time a trip rather than a deadline: "two weeks away", "a week in
# spain", "an itinerary for ten days". A length on its own is a date - a job starting, a baby due,
# a course beginning - and `_trip_plan` passes on it.
_TRIP_WORD = re.compile(
    r"\b(?:trip|trips|holiday|holidays|vacation|vacations|itinerary|travel|travelling|traveling"
    r"|travelled|traveled|away|abroad|fly|flying|flight|flights|hotel|hotels|hostel"
    r"|backpacking|honeymoon|city break|nights?|road trip|visiting|visit|tour|tours)\b", re.I)

# A place worth naming in the answer: "how do i plan a trip" with no place still gets the shape of
# a trip, and the window only when the file knows the country.
_DAYS_WORD = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}


def _trip_plan(memory, understood):
    """A trip planned by the shape of it, with the place's window when the file knows it."""
    text = str(understood.get("clean") or understood.get("text") or "").lower()
    city = _find_in(text, CITY_DAYS)
    length = None
    for pattern, name, _nights in _TRIP_LENGTH:
        if pattern.search(text):
            length = name
            break
    place = _find_in(text, BEST_TIME)
    if length and not place and not _TRIP_WORD.search(text):
        # A length of time is not a trip. "my job starts in two weeks" and "i start my new job in
        # two weeks" carry a talk word ("start") and a shape word ("two weeks") and nothing else
        # that says a trip, so they were answered with two or three bases and a travel day. A
        # window is only a trip when the line says trip, holiday, away, flights - or names a place,
        # which the tables above already read.
        return None
    if ("holiday" in text or "holidays" in text) and not length and not place:
        # "how do i plan my holiday" is the before-you-go checklist, which plans.py answers with
        # the passport, the insurance and the prescriptions. That is a different question from the
        # shape of a trip, and it keeps it.
        return None
    if length == "three weeks":
        shape = ("Three weeks is slow travel: pick a region and give each of two or three places a "
                 "week, so the trip has a rhythm instead of a list.")
    elif length == "two weeks":
        shape = ("Two or three bases for two weeks, with a travel day between them. More than that "
                 "and you spend the trip moving.")
    elif length == "a weekend":
        shape = "A weekend is one neighbourhood walked properly, not two cities."
    elif length == "a week":
        shape = ("One base and two or three day trips beats three cities in a week, because the day "
                 "you move is a day you lose.")
    else:
        shape = ("Work out how many nights you have first, then give each place at least three of "
                 "them: a base with day trips beats a list of cities, because every move costs you "
                 "half a day.")
    rest = ("Book the first two nights and the last night only, keep one day free in the middle, "
            "and sleep near the airport on the way home.")
    if city:
        # The city tables know how long it wants: "how do i plan a trip to rome" is a trip-shaped
        # question with an answer in the file, and the shape of the trip is what this row is for.
        days = CITY_DAYS[city]
        return f"{city.capitalize()} wants about {_DAYS_WORD[days]} full days. {rest}"
    if place:
        # The first clause of a window is the good months, which is all this needs: the months to
        # avoid are the other entry's job, and the whole paragraph swamps a trip-shaped answer.
        window = BEST_TIME[place].split(". ")[0].rstrip(".")
        return f"{shape} For {place.capitalize()} the window is {window}. {rest}"
    return f"{shape} {rest}"

# --- where to go, with nothing to go on -----------------------------------------
# "where should i go on holiday" was a search hedge while "where should i go in november" had a
# good answer: the month row needs a month, and the country row needs a country. This is the line
# with neither, which is how most people start. One reply per want, because a family of four and
# a honeymoon are not the same trip and the shortlist should not pretend they are.
HOLIDAY_ASK = ("where should i go", "where can i go", "where do i go", "where to go",
               "where should we go", "where can we go", "where would you go",
               "where would you recommend", "where do you recommend", "where do you suggest",
               "where would you suggest", "where shall i go", "where could i go",
               "suggest somewhere", "recommend somewhere", "anywhere youd recommend",
               "anywhere you would recommend", "somewhere to go", "where should i head",
               # the same question without a "where": "i want a holiday somewhere warm" was a
               # clarifying question, and the want is in the line
               "i want a holiday", "i need a holiday", "i fancy a holiday", "want a holiday",
               "need a holiday", "holiday ideas", "ideas for a holiday", "suggest a holiday",
               "recommend a holiday", "i want to go away", "want to go away", "where would be good",
               "where is good", "where would be nice", "somewhere i can go",
               # a sum of money with no place in it: "how far can i go on 300 pounds" is the same
               # shortlist question as "where should i go", and the line had no answer at all
               # (the weight row read its "how" and its "pounds" as a diet plan).
               "how far can i go", "how far can i get", "how far will i get",
               "how far will that get me", "how far would i get", "how far will",
               "how far would", "how far does",
               "how far does it go", "how far will 300 pounds go",
               # "any ideas for a staycation this summer" named the trip people are likeliest to
               # take and reached nothing: the shortlist under this row already answers the UK,
               # and the only words missing were the ones people put in front of it.
               # The ask has to carry a holiday word of its own as well (HOLIDAY_SHAPE), so
               # the bare "ideas" is not here: "i have 500 quid and no idea what to do with it"
               # is the windfall ladder, and "cheap city break ideas" already had its answer.
               "ideas for", "any ideas for", "suggestions for", "some ideas for",
               # "what could i do" is the same ask as "where could we go" when the line names a
               # trip and not when it names a sum: the guard holds out the money asks below.
               "what could i do", "where could we go", "where shall we go")
HOLIDAY_SHAPE = ("holiday", "holidays", "vacation", "break", "short break", "trip", "travel",
                 "week away", "week abroad", "getaway", "abroad", "in the sun", "somewhere warm",
                 "honeymoon", "weekend away", "day trip", "city break",
                 # The money a trip costs, when the line names it and no place: the sum is what
                 # decides how far it goes, and the shortlist below carries the cheap picks.
                 "pounds", "quid", "euros", "dollars", "budget",
                 # and the want said on its own: "where should i go skiing" is a holiday line
                 # with no holiday word in it, because the skiing is the holiday
                 "sun", "ski", "skiing", "snowboard", "snow", "walking", "hiking", "beach",
                 # "where should we go for a few days" names the length and no holiday word, so
                 # it was answered by the eating-out rule for picking a restaurant
                 "few days", "couple of days", "for a few days", "a week somewhere",
                 # "where should we go for our anniversary" was answered by the eating-out rule
                 # for picking a restaurant: the occasion is the shape of the trip here
                 "anniversary",
                 # the trip with no flight in it: "any ideas for a staycation" asks the same
                 # shortlist question as "where should i go on holiday", and the UK section of
                 # HOLIDAY_WANTS is already its answer
                 "staycation", "staycations", "holiday at home", "holidays at home",
                 "holiday in this country", "holiday in the uk", "break at home")
# The wants, in the order that gives the most specific answer: a honeymoon first, then children,
# then money, then the shape of the trip.
HOLIDAY_WANTS = (
    (("honeymoon", "romantic", "anniversary", "just the two of us"),
     "Santorini and the Amalfi coast are the postcard picks, and both are heaving in July and "
     "August: Italy's lakes or Puglia give you the same views and food with fewer people. For a "
     "beach honeymoon with guaranteed sun, the Maldives from January to April, or Zanzibar if "
     "you want something less built up."),
    (("toddler", "baby", "kids", "children", "child", "family", "teenager", "teenagers"),
     "With small children a short flight and a shallow beach beat a better destination: Menorca "
     "is the quietest of the Balearics, the Algarve has the sand and the short transfer, and a "
     "Center Parcs avoids the flight altogether. Book somewhere with a pool and a kitchen, and "
     "go in late May or September rather than the school summer, when it is warm but not 35C."),
    # A weekend is two nights, not a week in the sun, so the length comes before the money:
    # "any ideas for a cheap weekend away" was handed the cheap-sun shortlist, and the weekend's
    # own answer already says where the cheap fare is.
    (("weekend", "two nights", "long weekend", "few days"),
     "For a weekend the travel time is the whole trip, so pick somewhere under two hours door to "
     "door: Bath, York, the Cotswolds or the Norfolk coast at home, or Bruges, Lille or Amsterdam "
     "by train. Two nights is the right length, the train three or four weeks ahead is the cheap "
     "fare, and a room in the middle beats one with a car park."),
    (("cheap", "budget", "afford", "money", "cost", "broke", "save", "pounds", "quid",
      "euros", "dollars", "spare"),
     "The cheapest sun is the Algarve or the Costa Blanca outside July and August: May, June and "
     "late September cost half the school-holiday price, and flights booked six to eight weeks "
     "ahead are the other half. Albania and Bulgaria's Black Sea coast are the best-value "
     "beaches in Europe, and Prague, Krakow and Budapest the cheap city breaks."),
    # A quiet week is a want of its own, and the shortlist it got was the sunny one. Nothing
    # calm is in that list, so every "somewhere quiet" came back with Greece in September.
    (("quiet", "peaceful", "relaxing", "chill", "chilled", "calm", "restful", "escape it all",
      "away from crowds", "not too busy"),
     "Quiet comes from the place rather than the country: the north coast of Menorca and the "
     "Aran Islands are empty in June, the Alentejo and inland Andalucia have the heat without "
     "the resorts, and the Cotswolds, Northumberland or the far north of Scotland do it without "
     "a flight. Go in May, June or September - the same place in August is the crowd."),
    # "we want to go to the beach this weekend" got the weekend shortlist of towns, and a beach
    # is a coast rather than a town: the shape of the place is the question, not the length of the
    # trip.
    (("beach", "beaches", "seaside", "coast", "sand", "sandy", "by the sea"),
     "Pick a stretch of coast rather than a town: the Norfolk coast, Pembrokeshire, Cornwall and "
     "the Northumberland coast are the easy ones at home, and the Algarve or the Costa Blanca "
     "give you warm water outside July and August. The beach a ten-minute walk from the car park "
     "is empty by ten, and the one with the car park and the cafe is not."),
    (("city", "city break", "museums", "food", "restaurants", "culture", "shopping"),
     "Pick by what you want from a city: Lisbon for food and a short flight, Seville for heat and "
     "tapas, Prague or Budapest for grand streets at low prices, Copenhagen for design and "
     "cycling. Two nights is enough for any of them, and flying Tuesday to Thursday costs less "
     "than a weekend."),
    (("ski", "snow", "skiing", "snowboard"),
     "A resort at 1,500m or above is what makes the snow reliable, and January and March are "
     "cheaper than February half-term for the same mountain. The French Alps have the highest "
     "villages, Austria the better-value lift passes, and Italy the cheapest of the big three. "
     "Book the transfer with the room, because a separate one is where the money goes."),
    (("walking", "walk", "hike", "hiking", "mountains", "cycling", "outdoors"),
     "The Dolomites in late June or September for the big views and the huts, the Julian Alps for "
     "the same with fewer people, and the Lake District or the Peak District if you want a short "
     "break without a flight. Book the huts and the popular villages early, and carry the map on "
     "paper."),
    (("sun", "sunny", "warm", "hot", "beach", "beaches", "swim", "swimming", "tan"),
     "For real sun at any time of year, the Canaries are the safe pick and the water is warmest "
     "from late summer into October. Greece in June or September gives you 28C without the "
     "August crowds, and from November to March the short-haul sun is the Canaries, Cape Verde "
     "or Egypt, with the Red Sea the one to swim in."),
    (("uk", "britain", "england", "scotland", "wales", "staycation", "at home", "no flight"),
     "In the UK: Cornwall and the Pembrokeshire coast for beaches, the Lake District for walking, "
     "Northumberland for empty country and dark skies, and Edinburgh or Bath for a city. Book the "
     "coast two months ahead for a school holiday, and take the train where you can, because the "
     "drive is the part that eats the weekend."),
)
# A month is the month row's question and a named place is the city or country row's, so both
# leave this row alone, along with the packing, hotel and price lines.
HOLIDAY_NOT = (tuple(MONTHS) + tuple(WHERE_TO_GO)
               # "where can i go on holiday in the uk" is this row's: the UK is not a pick in the
               # country table, so holding it out left the line with no answer at all
               + tuple(word for word in COUNTRY_ALIASES if word not in ("uk", "britain"))
               + tuple(CITIES)
               # money spent on the car is not a trip: "how far can i go on 20 pounds of petrol"
               # is a tank, not a holiday
               # a sum with "what to do with" in front of it is money looking for somewhere to
               # go, not a place to go: "what could i do with 200 pounds" reached the cheap-sun
               # shortlist off the word "pounds" alone, and "i have 300 spare what do i do with
               # it" is the saving question. The ask has to be about going somewhere.
               + ("what could i do with", "what can i do with", "what should i do with",
                  "what shall i do with", "what do i do with", "what to do with",
                  "what would i do with", "what can we do with", "what should we do with")
               + ("petrol", "diesel", "fuel", "tank", "tankful", "charge", "miles", "per litre",
                  "litre", "gallons", "mpg",
                  # a day off is not a holiday: "where should i go on my day off" is a free
                  # afternoon, which the plans domain answers with what is on the doorstep.
                  # The bare "day off" is not held out, because a few days off with a price in
                  # the line is a trip: "i have 200 quid and a few days off where can i go" was
                  # left with no answer once the leave-request rows stood down. It is the day
                  # the person has to themselves that is not a holiday.
                  "my day off", "on a day off", "day to myself", "free time", "afternoon off")
               + ("when should i go", "when to go", "best time", "best month", "pack", "packing",
                  "suitcase", "luggage", "hotel", "hotels", "flights", "flight", "visa",
                  "how much", "insurance", "travelling with"))


CHEAPER_TRIP = ("The date is most of the price: a week either side of the school holidays, "
                "flying Tuesday or Wednesday rather than Friday, and booking the flight and the "
                "room together six to eight weeks ahead all come off the same trip. Then take "
                "hand luggage only, use the bus rather than the airport taxi, eat breakfast from "
                "a supermarket, and pay for one big thing a day instead of a package of five - "
                "that is where a week's money actually goes.")

# The trip the line itself names. "travel" and "away" are deliberately not here: "how do i travel
# around europe on a budget" is the getting-about answer (train or coach between cities) and
# "we're on a budget, about 300 each" is the sum to keep inside, and both were taken by this row
# while those words were in it.
_TRIP_IN_LINE = ("holiday", "holidays", "vacation", "week away", "getaway", "trip",
                 "a break", "city break", "abroad")


def _holiday_costs(memory, understood):
    """"How do i keep the cost of the trip down" - the week's price, not a live quote.

    The line has to name the trip as well as the cost: a bare "cheaper" or a budget with a figure
    in it is a narrowing question the other rows ask better, so this one leaves those alone.
    """
    clean = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if not any(re.search(r"\b%s\b" % re.escape(word), clean) for word in _TRIP_IN_LINE):
        return None
    return CHEAPER_TRIP

# The ask words this row gained for the ideas phrasing ("any ideas for a staycation", "what could
# i do on holiday") are vaguer than "where should i go", so a line that names a length and nothing
# else is somebody else's question: "any ideas for a few days away" is the trip-shape row's ("give
# each place at least three nights") and "any ideas for a day trip" is an afternoon, not a week's
# shortlist. A price in the line keeps this row, because a sum with no place is exactly the
# shortlist question - "i have 200 quid and a few days off where can i go" was this row's answer
# before the ideas phrasing existed, and it still is.
_A_LENGTH_ONLY = ("a few days", "few days", "couple of days", "a couple of days",
                  "day trip", "day trips", "day out", "day outs", "afternoon out")
# The asks this row gained that name no direction of their own. "Where should we go for a day
# trip" is still this row's question and keeps its answer; "any ideas for a day trip" is the same
# words with a vaguer ask, and the answer to that is the afternoon it names, not a week's
# shortlist.
_A_VAGUE_ASK = ("ideas", "idea", "suggestions", "suggestion", "what could i do",
                "what can i do", "what should i do")
_A_PRICE = ("pounds", "quid", "euros", "dollars", "budget", "cheap", "afford", "save up",
            "spare", "money")


def _a_shortlist_question(understood):
    """True unless the line is a vague ask that names only a length of trip.

    The length-of-trip questions have their own answer up the file ("give each place at least
    three nights"), and a price in the line keeps this row, because a sum with no place is exactly
    the shortlist question: "i have 200 quid and a few days off where can i go" is this row's.
    """
    clean = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(re.search(r"\b" + re.escape(word) + r"\b", clean) for word in _A_PRICE):
        return True
    if not any(re.search(r"\b" + re.escape(word) + r"\b", clean) for word in _A_VAGUE_ASK):
        return True
    return not any(re.search(r"\b" + re.escape(word) + r"\b", clean)
                   for word in _A_LENGTH_ONLY)

def _where_no_place(memory, understood):
    """A holiday with no month and no country named: the shortlist that fits what was asked."""
    clean = (understood.get("clean") or understood.get("text") or "").lower()
    for words, reply in HOLIDAY_WANTS:
        if any(re.search(r"\b%s\b" % re.escape(word), clean) for word in words):
            return reply
    return ("Two things decide it: how long you have, and whether you want sun or a city. With a "
            "week and a wish for sun, the Canaries, Greece or southern Spain; with a long "
            "weekend, Lisbon, Porto, Prague or Edinburgh; with children, a short flight to "
            "Menorca or the Algarve. Tell me the month and I will be more use than that.")


# A want is a different shape from a question: "i want to go somewhere warm", "my mates want a
# week in benidorm", "the lads want a stag do", "me and my wife want a few days away". The
# where-to-go row answers the question and this one answers the want, so the same shortlist is
# reachable both ways. A country or city in the tables is that row's own question and this one
# stands down; a place the tables do not hold is answered as a trip to book, since the facts
# about Benidorm itself are not what the line is asking for.
_WANT_TRIP_SAID = (
    # the want itself, in the shapes people say it in. Each is a whole phrase, because "want to go"
    # is also "i want to go to the gym" and the guard below is what tells those apart.
    "want to go", "wanted to go", "want to go away", "want to get away", "want to go somewhere",
    "want a few days", "want a couple of days", "want a week", "want a few weeks",
    "want a weekend away", "want a break away", "want a trip", "want to book a trip",
    "fancy a few days", "fancy going", "fancy a week", "fancy a weekend away",
    "week in the sun", "days in the sun", "cheap week", "cheap holiday", "week away",
    "somewhere warm", "somewhere quiet", "somewhere sunny", "somewhere hot",
    "somewhere with a beach", "somewhere near the sea", "somewhere by the sea",
    "stag do", "stag weekend", "hen do", "hen weekend",
    "the lads want", "my mates want", "the girls want", "my friends want",
    "thinking of going", "thinking about going")
# The same want with a place in it names no trip word at all, so the place is read off the line
# after the "go to" or the "week in": "my mates want to go to benidorm" has no holiday word in it
# and is a trip to Benidorm. The reading has to leave the words that are not places alone, because
# "i want to go to the gym three times a week" has a week in it and is not a week away, and neither
# is bed, work, school or the pub.
_PLACE_FILLER = frozenset("""
    the a an some any my our your his her their this that it
    somewhere anywhere nowhere everywhere there here abroad away travelling traveling
    to in into on at for with by about off from near around go going get getting fly flying
    book booked stay live move travel take going
""".split())
_NOT_A_PLACE = frozenset("""
    gym bed sleep work school college
    university class classes lesson lessons doctor doctors dentist hospital surgery toilet loo
    bathroom kitchen shop shops supermarket pub pubs cinema theatre church mosque prison home
    house town back out outside running walk swim swimming gymnasium office meeting
    park parks playground allotment allotments tip dump library bank market pool marina pier
    seafront promenade station airport petrol pharmacy garage salon barbers hairdresser
""".split())
# What the place stops at: the rest of the sentence after it.
_PLACE_ENDS = frozenset("""
    on at for in with next this that and or but then after before during from so of i we my our
    it is was would will can could should to a an the mates friends lads girls kids children
    family
""".split())
# A want that belongs to somebody else is not the trip the person in front of the bot is booking:
# "my daughter is 15 and wants to go to a festival with her mates" is a question about her, not a
# trip to a place called Festival Mates.
_SOMEONE_ELSE = frozenset("her his their she he".split())
# The same, said with the person named as the one who wants it: "my son wants to go to the park",
# "my daughter is 15 and wants to go to a festival". A peer group wanting one is the speaker's
# own trip ("my mates want to go to benidorm"), a family member who wants one is not.
_SOMEONE_WANTS = re.compile(
    r"\b(?:son|sons|daughter|daughters|kid|kids|child|children|toddler|teenager|teenagers|"
    r"mum|mom|dad|nan|gran|granny|grandad|grandma|niece|nephew|boy|girl|boyfriend|girlfriend)"
    r"\b[^.!?]{0,28}?\b(?:wants|want to|wanted to|would like|fancies|is keen|hoping)")
# A social booking is not a trip. On main, "i dont want to go to the party" answered "Party for a
# few days: fix the dates and pick one base, then book the flight" - the guard held out "the gym"
# and "work" but no party, and the negation in front of the want was not read at all. Both halves
# are the same mistake: the line names something to go to, and the person does not want to go.
_NOT_A_TRIP_EVENT = frozenset("""
    party parties wedding weddings funeral funerals christening christenings christening
    birthday birthdays dinner disco gig gigs concert concerts match matches game games
    appointment appointments interview interviews exam exams service barbecue bbq reunion
""".split())
# The want said in the negative, which no place word in the line can turn back into a trip:
# "i dont want to go to the party", "i cant face the wedding", "im dreading the christening".
# The negation is tied to the going, so "i want to go somewhere i dont want to cook" is still a
# trip wanted - there the "dont want" is about the cooking, not about going.
_NO_TRIP_WANTED = re.compile(
    r"\b(?:don'?t|dont|do not|doesn'?t|does not|didn'?t|did not)\s+(?:really\s+|actually\s+)?"
    r"(?:want|wanna|fancy|plan|intend)\s*(?:to\s+)?(?:go|going|be|come|travel)\b"
    r"|\bcan'?t face\b|\bcant face\b|\bdread(?:ing)?\b|\bnot going\b"
    r"|\bwould rather not go\b|\bno way i'?m going\b")
_TRIP_GO = re.compile(
    r"\b(?:go|goes|going|went|get|getting|got|fly|flying|flew|week|weeks|weekend|days|trip\s+to"
    r"|break)\s+(?:to|in|into)\s+(.{0,40})")


def _trip_place(clean):
    """The place a wanted trip is to ("benidorm", "lake district"), or ""."""
    match = _TRIP_GO.search(str(clean or "").lower())
    if not match:
        return ""
    tail = match.group(1)
    for place in sorted(AIR_HOURS_CITY, key=len, reverse=True):
        if re.search(r"\b%s\b" % re.escape(place), tail):
            return place
    words = [word for word in re.findall(r"[a-z][a-z-]*", tail)
             if word not in _PLACE_FILLER]
    if not words or words[0] in _NOT_A_PLACE or words[0] in _TRIP_SHAPE:
        return ""
    name = [words[0]]
    for word in words[1:3]:
        if word in _PLACE_ENDS or word in _NOT_A_PLACE:
            break
        name.append(word)
    return " ".join(name)


# The trip half of the key: what the want is about. "go to" is here because the place in "my mates
# want to go to benidorm" is the only other thing in the line, and the guard below is what keeps
# "i want to go to the gym" out of it.
_WANT_TRIP_SHAPE = (
    "away", "trip", "trips", "holiday", "holidays", "vacation", "week", "weeks", "weekend",
    "days", "sun", "warm", "quiet", "abroad", "getaway", "go to", "go somewhere", "days away",
    "week away", "weekend away", "in the sun", "stag", "hen")
# Words that say the line is about a trip. "want a break" is not one of them on its own - a break
# from work, from a person or from a diet is a different break.
_TRIP_SHAPE = frozenset("""
    away trip trips holiday holidays vacation week weeks weekend days sun sunny warm hot quiet
    abroad getaway beach beaches ski skiing snowboard city-break break-away stag hen
""".split())
# A trip already being packed for, priced or insured is another row's question: the suitcase is
# the packing list, the price is the budget, the flight is the airport.
_TRIP_OTHER_ROW = ("pack", "packing", "packed", "suitcase", "luggage", "what to bring",
                   "insurance", "passport", "visa", "flight", "flights", "hotel", "hotels",
                   "how much", "cost", "costs", "price", "checklist", "what do i need",
                   "booked", "already booked", "meal", "meals", "dinner", "dinners", "food",
                   "shop", "shopping", "recipe", "menu", "cook", "cooking",
                   # eating out, drinking out and a bed for the night are their own questions:
                   # "where can i eat somewhere quiet" is where to sit, not which coast
                   "eat", "eating", "eat out", "eating out", "restaurant", "restaurants",
                   "cafe", "cafes", "coffee", "drink", "drinks", "lunch", "breakfast",
                   "takeaway", "near me", "hostel", "hostels", "airbnb", "book a table",
                   "table for",
                   # "stay" on its own is one letter from "stag", and an avoid word is matched
                   # loosely: "the lads want a stag do" went to a greeting
                   "to stay", "place to stay", "somewhere to stay", "staying in", "staying near",
                   # a month named is the month row's question: "we want to go away in september
                   # with a baby" is what September is like, and this row was answering it with
                   # the shortlist for a family trip
                   ) + tuple(MONTHS)
_STAG_DO = (
    "Treat it as one city, two nights and one big thing booked ahead: Budapest, Krakow and Prague "
    "are the cheap three, Lisbon, Porto and Barcelona the ones with better weather, and anywhere "
    "in the sun is cheaper in May and September than in July. Book the rooms as a block, put the "
    "activity or the meal in the diary before anyone books a flight, and collect the money up "
    "front - the group chat will not pay you back afterwards.")


# A do somebody is trying not to go to is not a trip they want: "i dont want to go to the works
# christmas do" named an evening, and the trip reader took the words after "to the" for a place
# and offered a flight and a room. The refusal is read here so both halves of the trip reader
# stand down, and the refusal row in family.py answers it.
_A_REFUSAL = re.compile(
    r"\b(?:don'?t|do not|doesn'?t|didn'?t|would rather not)\s+want\s+to\s+go\b"
    r"|\bget(?:ting)?\s+out\s+of\s+(?:going\s+to\s+)?(?:the\s+|a\s+|my\s+|our\s+)?"
    r"(?:works?\s+)?(?:christmas\s+|leaving\s+|office\s+|staff\s+)?(?:do|party|night out|"
    r"meal|dinner|drinks|wedding|barbecue|bbq)\b"
    r"|\b(?:do|did)\s+i\s+have\s+to\s+go\b"
    r"|\bcan'?t\s+(?:come|make it|be there)\b"
    r"|\bmake\s+my\s+excuses\b|\bback\s+out\s+of\b"
    # The ask for the words to refuse it is the same question from the other side: "how do i
    # politely decline a hen do" and "how to turn down a stag do" were read as a do to plan,
    # and answered "treat it as one city, two nights and one big thing booked ahead". A trip
    # nobody is going on does not need booking.
    r"|\bhow\s+(?:to|do|can|should|would)\s+(?:i\s+)?(?:politely\s+|nicely\s+|tactfully\s+)?"
    r"(?:decline|refuse|turn\s+(?:(?:it|them|that|one)\s+)?down|say\s+no\s+to)\b", re.I)


def _a_trip_is_wanted(understood):
    """Whether the line is a trip wanted, rather than a want with a place that is not a trip."""
    clean = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    words = set(re.findall(r"[a-z']+", clean))
    if _A_REFUSAL.search(clean):
        return False      # a do they are trying not to go to is not a trip wanted
    if re.search(r"\bstag\b|\bhen (?:do|weekend|night)\b", clean):
        return True
    if words.intersection(_SOMEONE_ELSE) or _SOMEONE_WANTS.search(clean):
        return False      # somebody else's trip, not the one this person is going on
    if _NO_TRIP_WANTED.search(clean):
        # "i dont want to go to the party" is somebody not going, not a trip to a place called Party
        return False
    if words.intersection(_NOT_A_PLACE) or words.intersection(_NOT_A_TRIP_EVENT):
        # a week of the gym, a weekend off work, a few days in bed: the place named is not a trip -
        # and neither is a party, a wedding or a christening it is possible to go to
        return False
    # The place comes first: "i want to go to the gym three times a week" has the word "week" in
    # it, and a week of the gym is not a week away. A line that names a place nowhere else in the
    # tables is a trip to that place.
    place = _trip_place(clean)
    known = list(WHERE_TO_GO) + list(COUNTRY_ALIASES) + list(CITIES)
    if place and not any(re.search(r"\b%s\b" % re.escape(word), clean) for word in known):
        return True       # a place the guide does not hold is still a trip to it
    if words.intersection(_TRIP_SHAPE):
        # "i want to go home for the weekend" is home, not a holiday
        return not re.search(r"\b(?:go|going|get|getting)\s+(?:home|back|in|out)\b", clean)
    return False


def _want_a_trip(memory, understood):
    """A trip somebody wants, rather than a question about where to go."""
    clean = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _A_REFUSAL.search(clean):
        return None       # the invitation they are refusing is the refusal row's answer
    if re.search(r"\bstag\b|\bhen (?:do|weekend|night)\b", clean):
        return _STAG_DO
    known = list(WHERE_TO_GO) + list(COUNTRY_ALIASES) + list(CITIES)
    if any(re.search(r"\b%s\b" % re.escape(word), clean) for word in known):
        # a country or a city the guide already has is the guide's question, not this one
        return None
    place = _trip_place(clean)
    if place:
        name = place.title()
        return (name + " for a few days: fix the dates and pick one base, then book the flight "
                "and the room together six to eight weeks ahead, and agree the one thing you "
                "all want to do before anything else. The rest is food and wandering, and for "
                "a group that is the part that goes wrong - one person books, everyone pays "
                "into one pot, and keep the time on the ground to two or three nights.")
    return _where_no_place(memory, understood)


# "what should i pack for a week in spain in august" was told "one long-sleeved layer and a light
# waterproof, as October and May evenings turn cool even in Spain or Italy": the reason for the
# layer was a different month from the one they named, in the answer to their own question. The
# list is the same; the reason moves with the month, and in high summer the reason is a storm and
# air conditioning rather than a cool evening.
_WARM_WEEK = (
    "light cotton tops and shorts, one long-sleeved layer and a light waterproof, plus swimwear, "
    "a hat, high-factor sun cream and shoes you can walk in. Take two pairs of shoes at most and "
    "one smarter outfit if you plan to eat out; everything else can be washed.")


_FOOD_TO_CARRY = ("food", "foods", "snacks", "snack", "lunch", "dinner", "breakfast", "meal",
                  "meals", "picnic", "dish", "dishes", "something to eat", "anything to eat",
                  "cook", "cooking", "bake", "baking", "recipe", "recipes", "drinks")


def _not_a_food_to_carry(understood):
    """False when the line asks what food to take or cook for a place, not what kit to pack.

    The kit rows in this file own "what should i take to the beach", "what do i need to take
    camping" and "what should i pack for spain", and a food word in the same line is the picnic's
    or the guest's-dish question, not the kit's: "what food should i bring to the beach" came back
    as a warm-week clothes list and "what food should i bring camping" as a tent. A line that
    names food and asks what to carry or cook is answered by the food rows, so the kit stands
    aside - the same way the guest's dish stands aside for a cook ask.
    """
    line = understood or {}
    clean = str(line.get("clean") or line.get("text") or "").lower()
    words = set(re.findall(r"[a-z']+", clean))
    if not words.intersection(_FOOD_TO_CARRY):
        return True
    carry = ("bring", "brings", "bringing", "take", "takes", "taking", "carry", "food",
             "eat", "make", "makes", "cook", "bake")
    return not any(word in words for word in carry)


def _warm_week_pack(memory, understood):
    """What goes in the bag for a warm week, with the reason the weather gives for it."""
    clean = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    months, seasons = _time_terms(clean, loose=True)
    if months & {6, 7, 8} or seasons & {"summer", "high summer"}:
        return ("For a warm summer week: " + _WARM_WEEK.replace(
            "one long-sleeved layer and a light waterproof, plus",
            "one long-sleeved layer for air conditioning and a light waterproof for a "
            "thunderstorm, plus"))
    if months & {5, 9, 10}:
        return ("For a warm week out of high summer: " + _WARM_WEEK.replace(
            "one long-sleeved layer and a light waterproof, plus",
            "one long-sleeved layer and a light waterproof, as May and October evenings turn "
            "cool even in Spain or Italy, plus"))
    return "For a warm week: " + _WARM_WEEK


# Two cold-drink asks, one row: keeping a drink cold for later is the cool bag, and getting
# one cold in a hurry is the ice and salt. A single canned reply answered "how do i chill
# wine quickly" with the picnic advice, which is not what the person asked.
def _cold_drinks(memory, understood):
    said = str(understood.get("clean") or understood.get("text") or "").lower()
    if any(word in said for word in ("quick", "quickly", "fast", "in a hurry", "right now",
                                     "asap", "hurry", "minutes")):
        return ("Fastest is a bucket or a big bowl of cold water with ice in it and a good "
                "handful of salt: salt makes the water colder than ice alone, and a bottle "
                "or a glass drops to fridge-cold in about 15 minutes. No ice? Wet a tea "
                "towel, wring it out, wrap the bottle and stand it in the freezer for 10 to "
                "15 minutes, or stand the glass in iced water and stir.")
    return ("Chill it in the fridge first, then a cool bag or box with a frozen ice block or "
            "a bag of ice at the bottom and the drinks on top - ice above them, not under, "
            "since cold sinks. Fill bottles right to the top and keep the bag shut and out of "
            "the sun; a wrapped bottle holds the cold far longer than a bare one. For a "
            "party, chill half the bottles and freeze the other half: the frozen ones keep "
            "the box cold and thaw by the time you need them.")

# A month asked about a place answers with the verdict and the window behind it, and the window
# is three or four sentences. A follow-up that only swaps the month has read all of it already:
# "is spain good in october" then "and what about november" printed the Spain window a second
# time under a frame that put the month in a noun slot ("The same goes for the november: Spain:
# April to June and September to October"), which is both the paragraph they just read and a
# sentence nobody wrote. The verdict is the new part, so once the window is on the screen the
# verdict is the whole answer. Measured on main `d68a7e25`.
_YES_THE_WINDOW = " is in the good window for "
_NO_THE_WINDOW = " is not the best month for "


def _the_window_is_read(memory, window):
    """Whether the chat has already been given this window, or the part of it that carries."""
    said = str(window or "").strip().lower()
    first = re.split(r",? when |,? and (?:the|it) |\. ", said)[0].strip(" .;,")
    if len(first.split()) < 4:
        return False
    turns = [turn for turn in ((memory or {}).get("turns") or []) if isinstance(turn, dict)]
    for turn in turns[-5:]:
        if first in str(turn.get("bot") or "").lower():
            return True
    return False


def _the_same_verdict_was_given(memory, tail):
    """Whether a verdict in this shape about this place is already on the screen.

    Asked for one month after another, "No, December is not in the window for Spain: April to
    June and September to October" says the window a second time for nothing: "either" is the
    whole of what the third month adds.
    """
    said_tail = str(tail or "").strip().lower()
    if not said_tail:
        return False
    turns = [turn for turn in ((memory or {}).get("turns") or []) if isinstance(turn, dict)]
    return any(said_tail in str(turn.get("bot") or "").lower() for turn in turns[-5:])


def _a_month_verdict_once(memory, understood):
    """The month row, answering with the verdict alone when the window is already read."""
    # A follow-up reaches this row with the line before it joined on (answers' context path), so
    # the month can be in the reading while the line itself names none: "we fancy a break in
    # january" then "is that a good time of year". The month is the one asked about and the ask
    # is whether, so the verdict is the answer - the three places are the answer to "where", and
    # reading them out again is the paragraph they have just had.
    here = ""
    if isinstance(memory, dict):
        here = str((memory.get("understood") or {}).get("clean") or "")
    if (here and _the_month_of({"clean": here}) is None
            and any(ask in here for ask in _A_TIME_VERDICT_ASK)):
        month = _the_month_of(understood)
        if month:
            return _the_verdict_on(month, memory, here)
    said = _month_destination(memory, understood)
    if not said:
        return None
    if said.startswith("Yes, ") and _YES_THE_WINDOW in said:
        head, _, window = said.partition(": ")
        if not _the_window_is_read(memory, window):
            return said
        label = head.split(_YES_THE_WINDOW, 1)[1]
        tail = _YES_THE_WINDOW + label
        return head + (" too." if _the_same_verdict_was_given(memory, tail) else ".")
    if said.startswith("No, ") and _NO_THE_WINDOW in said:
        marker = next((one for one in (". The window is ", ". ") if one in said), "")
        head, _, rest = said.partition(marker) if marker else (said, "", "")
        if not rest or not _the_window_is_read(memory, rest):
            return said
        label = head.split(_NO_THE_WINDOW, 1)[1]
        tail = _NO_THE_WINDOW + label
        return head + (" either." if _the_same_verdict_was_given(memory, tail) else ".")
    # "Spain: <window>" is what a month in neither clause gets, and the window there is the
    # answer on the first ask. Asked again for another month it is the paragraph they read, and
    # the honest short answer is that this month is outside the window - only claimed where the
    # window names months to be outside of, since "all year round" names none.
    label, _, window = said.partition(": ")
    if not window or not _the_window_is_read(memory, window):
        return said
    month = _the_month_of(understood)
    first = re.split(r",? when |\. ", window)[0].split(":")[0].strip(" .;,")
    names_a_month = any(re.search(r"\b%s\b" % re.escape(name), first.lower())
                        for name in MONTHS)
    if month and names_a_month:
        outside = "is not in the window for " + label
        if _the_same_verdict_was_given(memory, outside):
            return f"No, {month.capitalize()} {outside} either."
        return f"No, {month.capitalize()} {outside}: {first}."
    return said


def _the_month_of(understood):
    """The month the line names, the longest name first, or None."""
    clean = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    for name in sorted(MONTHS, key=len, reverse=True):
        if re.search(r"\b%s\b" % re.escape(name), clean):
            return name
    return None
# ---- the way there is not the eating ----------------------------------------
#
# "cheapest way from london to manchester" named two cities and the word "cheapest", which is the
# eating row's second signal, so a route question was answered with street food. The words that
# mean getting somewhere stand the eating row down - unless the line also names eating, because
# "the cheapest way to eat well in paris" is the eating row's own question.
_A_WAY_THERE = re.compile(r"\b(?:get to|get from|getting to|getting from|way to get|way from|"
                          r"how do i get|how do you get|way there)\b")
_AN_EATING = re.compile(r"\b(?:eat|eats|eating|food|foods|meal|meals|restaurant|restaurants|"
                        r"lunch|dinner|breakfast|snack|snacks|menu|menus|dining)\b")


_VALUE_EATING = re.compile(r"\b(?:good value|value for money|cheap eats|cheapest eats)\b")


def _a_way_there_needs_no_eating(understood):
    """False for a line that does not mention eating.

    It began as a fence for a line about getting somewhere, because "how do i get from the
    airport to the centre of rome" has a city and a "cheap"-like word in no sense at all. Then
    "is budapest cheap" reached this row on the word "cheap" alone and was told three habits for
    eating cheaply in any city, when the question was what a day there costs: the same shape,
    with the way there replaced by the cost. So the row now wants an eating word in the line,
    which is the one thing both of those lines lack.
    """
    clean = (understood.get("clean") or "").lower()
    # "good value in rome" was this row's line before the eating word was required, and it is a
    # food question in the way people say it, so the value phrases count as one too.
    return bool(_AN_EATING.search(clean) or _VALUE_EATING.search(clean))


def _a_weight_is_the_kitchen(understood):
    """False for a line with a weight in it: "how long does a 5kg turkey take".

    Turkey is a country, so the stay-length rows read a bird for the oven as a holiday and
    answered "three full days in Istanbul, not counting the day you arrive". A weight is the
    one thing a stay is never asked with, so the row stands down and the cooking row gets it.
    """
    return not a_weight(understood)


# ---- weighing the train against the plane ------------------------------------
#
# The cheapest-way row is for a coach against a train, and it fenced "fly" and "flight" so that a
# question about one flight stayed with the fares card. But "is it cheaper to fly or take the
# train to edinburgh" is the same comparison with a plane in it, so the fence moved to a guard: a
# plane named with a way on the ground is a choice between two ways of getting there.
_A_PLANE = re.compile(r"\b(?:flight|flights|fly|flying|plane|planes|air fare|airfare)\b")
_A_WAY_ON_THE_GROUND = re.compile(r"\b(?:train|trains|rail|railway|coach|coaches|bus|buses|"
                                  r"drive|driving|car|cars)\b")


def _a_comparison_needs_two_ways(understood):
    """False when the line names a plane and no way to get there on the ground."""
    clean = (understood.get("clean") or "").lower()
    if not _A_PLANE.search(clean):
        return True
    return bool(_A_WAY_ON_THE_GROUND.search(clean))
def _a_place_it_might_not_be_safe(memory, understood):
    """"Is it safe there", "is lisbon safe": the habits, for the city the chat is on.

    No entry says a place is safe or unsafe, because nobody can: the answer is the habits that
    work anywhere and the hotel desk, which knows this week's streets. The city comes from the
    line or from the last few turns, so a question with no place in it ("i left the chicken out
    overnight" / "is it safe") is left to the entry that owns it.
    """
    clean = str((understood or {}).get("clean") or "").lower()
    city = _find_in(clean, CITIES)
    if not city:
        turns = memory.get("turns") if isinstance(memory, dict) else None
        for turn in reversed((turns or [])[-3:] if isinstance(turns, list) else []):
            if not isinstance(turn, dict):
                continue
            city = (_find_in(str(turn.get("user") or "").lower(), CITIES)
                    or _find_in(str(turn.get("bot") or "").lower(), CITIES))
            if city:
                break
    if not city:
        return None
    return (f"Nobody can promise {city.title()} is safe, and anyone selling that is selling "
            f"something. What keeps you out of trouble there is the ordinary kit: busy, lit "
            f"streets, more so after dark, the metro or a licensed taxi rather than a shortcut, "
            f"the phone out of sight and the bag in front of you, and the two or three streets "
            f"the hotel desk tells you to avoid - they know this week's answer better than any "
            f"guide. Keep the hotel's address on you and the local emergency number in your "
            f"phone.")
# "train" is a verb as often as it is a noun, and the verb is the commoner reading in a line about
# getting fit: "how long will it take to train" and "how many weeks do i need to train" were both
# answered with the packing list for a rail journey. A line that trains *for* something has no
# journey in it, so the row stands aside for it. A rail line keeps its own words - station,
# platform, ticket, delay - and "the train to Manchester" is still a journey.
_TRAINS_FOR = re.compile(
    r"\b(to|need to|have to|got to|going to|how long to|weeks to|time to|how to|back to)"
    r"\s+train\b"
    r"|\btrain(?:ing|ed)?\s+(?:for|hard|harder|again|towards|up for)\b"
    r"|\btrain(?:ing|ed)\s+(?:twice|three|four|every|each|most|more)\b")


# "do i need to treat the whole family for threadworms" is a question about the house, and the
# passport checklist answered it: the row's own avoid list names the illnesses it thought of
# (sick, fever, chickenpox, measles) and did not name the worms, the nits or the colds, so a
# family word plus "do i need" was all it took. A journey in the line keeps the card; an illness
# without one stands it down, which is the same rule the avoid list was reaching for.
_A_TREATMENT_AT_HOME = re.compile(
    r"\b(threadworms?|worms?|nits|head ?lice|lice|scabies|chickenpox|measles|mumps|"
    r"hand foot and mouth|conjunctivitis|norovirus|stomach bug|sick bug|rash|fever|temperature|"
    r"cold|flu|cough|vomit\w*|diarrhoea|diarrhea|infect\w*|isolat\w*|contagious|catching|"
    r"unwell|ill)\b")
_A_JOURNEY_SAID = re.compile(
    r"\b(holiday|holidays|abroad|trip|trips|travel|travelling|traveling|flight|flights|fly|"
    r"flying|airport|overseas|border|passport|passports|visa|destination|resort)\b")


def _a_journey_not_a_treatment(understood):
    """True unless the line is about an illness in the house and names no journey at all."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _A_JOURNEY_SAID.search(text):
        return True
    return not _A_TREATMENT_AT_HOME.search(text)


def _a_journey_not_training(understood):
    """True unless "train" in the line is the verb: training for something, not a rail trip."""
    text = (understood or {}).get("clean") or ""
    return not _TRAINS_FOR.search(text)


def _a_coach_is_a_journey(understood):
    """False when the "coach" in the line is a person who runs sessions, or a sofa.

    "i need a new coach for the living room" matched this row on "coach for" and was given a
    packing list for a long journey. A coach is three things and the rest of the sentence says
    which (bot/understanding/senses.py): a vehicle, the person who takes a session, and the old
    word for a sofa the line wants a new one of.
    """
    sense = (understood or {}).get("sense") or {}
    return sense.get("coach") not in ("teacher", "furniture")


def _the_journey_in_the_line(understood):
    """The row's one guard: a rail trip rather than training, and a coach that is a vehicle."""
    return _a_journey_not_training(understood) and _a_coach_is_a_journey(understood)

# Each of these situations has one first action that is different from the others, and the same
# four-second-gap paragraph sent to all of them is a card read aloud rather than an answer: easing
# off is the aquaplaning advice, letting them past is the tailgating advice, dipped lights and the
# 100-metre fog-light rule is the fog advice. So the reply opens on the situation the line named.
_TRAFFIC_SITUATIONS = (
    (("aquaplan", "hydroplan", "standing water", "puddle"),
     "Aquaplaning: ease off the accelerator, keep the wheel straight and do not brake until the "
     "tyres bite again. Then put the lights on, slow right down and leave twice the gap until the "
     "road has drained."),
    (("tailgat", "tailgater", "behind me", "right behind", "close behind", "up behind",
      "on my bumper", "bumper"),
     "Someone on your bumper: slow down gradually so there is room for both of you to stop, and let "
     "them past at the first chance you get. Never brake-check them - it turns a nuisance into a "
     "crash."),
    (("fog", "foggy"),
     "In fog: dipped headlights on, fog lights only once you cannot see more than about 100 metres, "
     "and drop to a speed you could stop at inside the distance you can see. Keep well back, because "
     "the car in front can stop sooner than you can see."),
    (("heavy rain", "raining", "rain", "wet road", "wet roads"),
     "In heavy rain: dipped headlights on, double the gap and lift off where the water gathers, "
     "because standing water is where aquaplaning starts. Slow down before a bend, not in it."),
    (("skid", "sliding", "slides"),
     "If the car slides: ease off the accelerator and steer where you want to go, and do not stamp "
     "on the brake - that is usually what started it. Then slow down and keep the wheel steady until "
     "the tyres grip again."),
    (("smart motorway", "red x", "red cross", "hard shoulder"),
     "On a smart motorway the red X means the lane is closed because somebody is in it, so obey it "
     "and expect the limit to drop with it. If you break down, get out on the left, behind the "
     "barrier, and call 999 from the nearest orange marker."),
    (("overtak", "overtaking"),
     "Overtaking: get past and back in with a gap you could pull into, rather than sitting alongside "
     "a lorry where the driver cannot see you. Leave four seconds in front and behind."),
    (("slip road", "merging", "merge", "join a motorway", "joining a motorway",
      "join the motorway", "joining the motorway", "merge onto", "merging onto"),
     "Joining the motorway: use the slip road to build up to the speed of the traffic and slot into a "
     "gap rather than stopping at the end of it. Move over a lane if you can to let somebody in."),
)

_JAM_REPLY = (
    "Traffic that crawls is a gap problem: count four seconds to the car in front and brake early "
    "and gently, so the person behind has time to do the same - most jams are made by that "
    "accordion, not by the crash. Stay in one lane where you can and watch the brake lights two "
    "cars ahead rather than the one in front. Add twenty minutes before you set off and plan a stop "
    "every two hours, which is what keeps the last hour the same as the first.")


def _drive_in_traffic(memory, understood):
    """The situation the line named opens the reply, so aquaplaning is not given the jam advice."""
    text = " ".join([str(understood.get("clean") or "").lower()]
                    + [str(word).lower() for word in (understood.get("words") or [])])
    for words, reply in _TRAFFIC_SITUATIONS:
        if any(word in text for word in words):
            return reply
    return _JAM_REPLY


# The plate is the follow-up everybody asks after a country, and nothing behind it was on the
# tourist's side: "im going to spain" then "what about food" was a search hedge, and "what should
# i eat there" reached the cook-what-is-in-the-fridge menu on the word "eat", which is a
# different question. The trip card lists cities and says nothing about eating, so this is the
# second half of the same entry: three named dishes with the place to eat each one, because
# "try the local food" is not advice. A table keyed by the country, so one fact answers every
# way of asking for it ("what do they eat in portugal", "good food in naples", "what should i
# eat there") and the same row serves the follow-up through the country the chat already named.
FOOD_IN = {
    "spain": ("Tapas at the bar - two or three plates between you - paella in Valencia and "
              "pintxos in San Sebasti\u00e1n. Jam\u00f3n and pimientos de Padr\u00f3n are the "
              "cheap way in."),
    "italy": ("Rome for cacio e pepe or carbonara, Naples for pizza and Bologna for rag\u00f9, "
              "with a coffee standing at the bar. Order the house wine; it is cheaper than water "
              "in some places."),
    "france": ("A bakery lunch, steak-frites in Paris and a bouchon in Lyon, with cider and cream "
               "in Normandy. The fixed-price lunch menu is where the value is."),
    "portugal": ("Past\u00e9is de nata and grilled sardines in Lisbon, a francesinha in Porto and "
                 "cataplana on the Algarve. Look for the prato do dia, a set lunch with wine for "
                 "very little."),
    "greece": ("Souvlaki, grilled octopus and a proper village salad: tomato, cucumber, onion and "
               "a slab of feta, no lettuce. Eat where the menu is short and the bread is fresh."),
    "turkey": ("Bal\u0131k ekmek - fish in bread - by the water in Istanbul, a breakfast of "
               "cheese, olives and menemen, and pistachio baklava in the south-east."),
    "morocco": ("Tagine, couscous on a Friday and mint tea poured from a height, with the evening "
                "food stalls in Marrakech the easy start. Bread and olives come with everything."),
    "egypt": ("Koshari from a street shop - rice, lentils and pasta with tomato sauce - ful "
              "medames for breakfast, and grilled fish by the Red Sea."),
    "japan": ("Sushi at a counter and a bowl of ramen in Tokyo, takoyaki and okonomiyaki in Osaka, "
              "tofu and kaiseki in Kyoto. Convenience-store food is genuinely good and cheap."),
    "thailand": ("Street food is the point: pad thai, som tam and moo ping, cooked in front of "
                 "you where it is busy. Say \"not spicy\" clearly, and eat breakfast at the "
                 "market."),
    "india": ("Dosa, idli and coconut curries in the south; butter chicken, chaat and tandoori "
              "bread in the north. Breakfast is the meal to try first."),
    "mexico": ("Tacos al pastor from a stand, tamales for breakfast and mole in Oaxaca, with the "
               "salsa on the side so you choose the heat."),
    "croatia": ("Grilled fish and black risotto on the coast, \u0107evapi inland, and a konoba "
                "with a short menu is the best bet. Pizza is everywhere and usually good."),
    "germany": ("Bratwurst from a stand, a proper schnitzel and rye bread with everything; in "
                "Bavaria a pretzel and a cold beer counts as lunch."),
    "netherlands": ("Bitterballen with a beer, raw herring with onions from a stall, and a "
                    "stroopwafel warm off the iron."),
    "ireland": ("Fish and chips, a full Irish breakfast, and brown bread with smoked salmon; "
                "chowder on the west coast."),
    "scotland": ("Fish and chips, a full Scottish breakfast, haggis with neeps and tatties, and "
                 "seafood in Oban or on the west coast."),
    "england": ("Fish and chips, a Sunday roast and a proper curry house; in London the markets "
                "are better eating than the streets around the sights."),
    "iceland": ("Lamb soup, skyr and a hot dog with everything from the stand in Reykjav\u00edk, "
                "with fish straight off the boat. It is expensive, so eat one good meal a day."),
    "poland": ("Pierogi, a bowl of \u017curek sour rye soup and kielbasa off a grill, with "
               "pierogi shops the cheapest full meal in town."),
    "vietnam": ("Ph\u1edf for breakfast in Hanoi, b\u00e1nh m\u00ec from a cart and fresh spring "
                "rolls down the middle of the country. Eat where the stools are small and the "
                "queue is long."),
    "china": ("Go regional: dim sum in Guangzhou and Hong Kong, hand-pulled noodles in Xi'an and "
              "a Sichuan hotpot in Chengdu. Order several dishes and share them."),
    "belgium": ("Mussels with chips, a waffle from a stall and frites with mayonnaise; the beer "
                "is the point, and every bar has its own glass."),
    "austria": ("Wiener schnitzel, a sausage from a stand and a slice of Sachertorte, with coffee "
                "and cake an entire afternoon."),
    "tunisia": ("Couscous on a Friday, a brik with an egg inside and harissa with everything, "
                "usually with bread and olives first."),
    "cuba": ("Ropa vieja, black beans with rice and a strong coffee; the paladares - private "
             "restaurants - beat the state ones."),
    "canada": ("Poutine in Quebec, salmon on the west coast and a proper diner breakfast; "
               "portions are big, so order less than you think."),
    "australia": ("Fish and chips on the coast, a meat pie and a flat white; the coffee is what "
                  "people miss when they leave."),
    "usa": ("Go regional: barbecue in Texas or Kansas City, a po'boy in New Orleans, pizza by the "
            "slice in New York, tacos in Los Angeles."),
    # The table is the answer to "what should i eat in <country>" for wherever the person is
    # going, and the countries below were the common ones it had nothing for: a search hedge to
    # "what should i eat in brazil" or "whats peruvian food like" is the worst answer of all.
    "argentina": ("Beef is the point: a parrilla grilled over coals with chimichurri, empanadas "
                  "from a bakery and a mate to carry round. Order the bife de chorizo and share "
                  "it, and eat late: nowhere is busy before nine."),
    "brazil": ("A kilo restaurant at lunch, where you pay by weight, is the cheap way in; feijoada "
               "on a Saturday, p\u00e3o de queijo and a\u00e7a\u00ed from a corner shop, and "
               "churrasco for a proper dinner."),
    "peru": ("Ceviche at lunch, never in the evening, with leche de tigre on the side; lomo saltado "
             "and a quinoa soup in the Andes. Lima is worth a whole day of eating."),
    "south korea": ("Barbecue you cook at the table, with lettuce leaves and a dozen little dishes "
                    "that come free; then fried chicken with beer, and street stalls for tteokbokki "
                    "and hotteok."),
    "lebanon": ("Mezze is the meal: hummus, tabbouleh, fattoush and grilled halloumi, then kibbeh "
                "and a plate of mixed grill. Order several small plates and share."),
    "israel": ("Hummus with a runny egg for breakfast, sabich and falafel in pita, and a market "
               "lunch of cheeses, olives and bread. Salads come with everything."),
    "nigeria": ("Jollof rice with fried plantain, a bowl of egusi with pounded yam and suya off a "
                "night grill. Eat where the queue is local and the pepper is not toned down."),
    "kenya": ("Nyama choma - grilled goat or beef - with kachumbari, plus ugali and sukuma wiki; "
              "in Mombasa the coast gives you biryani and coconut curries."),
    "south africa": ("A braai is the meal: grilled meat, a pap and relish on the side. Then bunny "
                     "chow in Durban, biltong from a butcher and a bobotie."),
    "wales": ("Cawl, the lamb and leek broth, with bread and cheese; Welsh rarebit on toast, "
              "laverbread for breakfast in the valleys, and Welsh cakes warm from the griddle."),
    "new zealand": ("A meat pie from a dairy, fish and chips on the beach and a h\u0101ngi if you "
                    "get invited; lamb is the dinner and the flat white is the coffee."),
    "sweden": ("Meatballs with lingonberry, pickled herring at midsummer and a kanelbulle with "
               "coffee; lunch is often a buffet table of salads and bread."),
    "denmark": ("Sm\u00f8rrebr\u00f8d - open sandwiches - for lunch, a hot dog from a stand and "
                "pastry from a proper bakery. New Nordic tasting menus cost a lot; the bakeries "
                "do not."),
    "norway": ("Salmon and cod, a brown cheese on toast for breakfast and a waffle with jam; "
               "eating out is very expensive, so the supermarket deli counter is how people "
               "lunch."),
    "switzerland": ("Fondue and raclette, r\u00f6sti with a fried egg and a plate of b\u00fcndner "
                    "fleisch; the supermarkets and bakery lunch are the only cheap meals."),
    "russia": ("Borscht with sour cream, pelmeni with butter and a blini from a street kiosk; a "
               "stolovaya canteen is cheap and filling, and the tea comes with everything."),
    "singapore": ("A hawker centre is the answer: chicken rice, laksa and char kway teow from "
                  "different stalls, all cheap. Order with tissue packets on the table to claim "
                  "a seat."),
    "malaysia": ("Nasi lemak for breakfast, char kway teow and laksa from the hawkers, and "
                 "roti canai at any hour; the food courts are where the good cheap eating is."),
    "indonesia": ("Nasi goreng and satay from a warung, rendang in Padang and gado-gado; eat where "
                  "the warung is busy and the price list is on the wall."),
    "philippines": ("Lechon for a celebration, adobo and sinigang at home, and halo-halo in the "
                    "heat; the malls have the air conditioning and the food halls."),
    "pakistan": ("Nihari and haleem for breakfast in Lahore, chaat from a stall and a plate of "
                 "biryani at lunch; the grill houses do seekh kebab and naan fresh from the "
                 "tandoor."),
    "sri lanka": ("Rice and curry, several dishes at once, with hoppers for breakfast and kottu "
                  "off a hotplate at night; the fish curry on the coast is the one to order."),
}
_FOOD_WORDS = ("food like", "dishes like", "cuisine like", "food",
               "foods", "eat", "eating", "dish", "dishes", "cuisine", "cuisines",
               "local food", "street food", "speciality", "specialities", "specialty",
               "specialties", "what do they eat", "what to eat", "restaurant", "restaurants",
               "menu", "what about food")
_FOOD_SHAPE = ("what", "about", "there", "should", "shall", "can", "could", "do", "does",
               "where", "best", "try", "local", "in", "good", "nice", "any", "the", "like")
# A kitchen line names food and asks what to cook with it: "what should i eat with rice", "what
# can i make with courgettes". The country in the chat is not what those are about.
_FOOD_NOT_A_TRIP = (
    "cook", "cooking", "cooked", "make", "made", "making", "recipe", "recipes", "bake", "baked",
    "baking", "oven", "fridge", "freezer", "supermarket", "shopping list", "meal plan",
    "meal prep", "batch", "leftovers", "tonight", "dinner tonight", "for dinner", "for tea",
    "for lunch", "for breakfast", "with rice", "with pasta", "with chicken", "in the oven",
    # A resident is not a tourist: "i live in spain, what should i eat" asks what to cook at
    # home, and dishes to try on holiday are the wrong card for them. The same words fence the
    # follow-up, where the country comes from a line two turns back.
    "live in", "i live", "we live", "moved to", "move to", "i'm from", "im from", "grew up",
    "my home", "back home", "at home in", "lived in", "living in", "have lived", "live here",
    "moved here", "here for years",
    # A line asking whether the food is safe, or what to avoid, is a traveller's-stomach
    # question: "is the food safe in mexico" and "what should i avoid eating in india" were
    # both given the dish card, and a menu is no answer to a worry about being ill.
    "safe", "unsafe", "ill", "sick", "sickness", "hygiene", "hygienic", "avoid", "avoiding",
    "tap water", "ice in", "food poisoning", "stomach", "dodgy", "risky",
    # Taking food into a country and bringing it back are customs rules, not a plate: "can i
    # take food into the eu" was answered with tapas, and the trip before it put the country
    # in the chat, so the row's own reading is what has to turn it down.
    "customs", "declare", "duty free", "take food", "bring food", "bring back", "bring home",
    "take into", "bring into", "allowed in", "allowance", "import", "food into", "ham",
    "cheese back", "meat into", "milk into")
# "What is Portuguese food like" names no country, only the adjective, and the table is keyed by
# the country: the adjectives are the same fact asked the other way round, so they are the same
# table's. The regular ones are built from the country name, and the handful that are not are
# spelled out, because a rule that guessed "italian" from "italy" would also guess "greece".
FOOD_ADJECTIVES = {
    "spanish": "spain", "italian": "italy", "french": "france", "greek": "greece",
    "turkish": "turkey", "moroccan": "morocco", "portuguese": "portugal",
    "english": "england", "scottish": "scotland", "irish": "ireland", "american": "usa",
    "cuban": "cuba",
    "egyptian": "egypt", "tunisian": "tunisia", "polish": "poland", "croatian": "croatia",
    "icelandic": "iceland", "thai": "thailand", "vietnamese": "vietnam", "chinese": "china",
    "japanese": "japan", "indian": "india", "mexican": "mexico", "austrian": "austria",
    "belgian": "belgium", "canadian": "canada", "australian": "australia",
    "argentinian": "argentina", "argentine": "argentina", "brazilian": "brazil",
    "peruvian": "peru", "korean": "south korea", "lebanese": "lebanon", "israeli": "israel",
    "nigerian": "nigeria", "kenyan": "kenya", "south african": "south africa",
    "welsh": "wales", "swedish": "sweden", "danish": "denmark", "swiss": "switzerland",
    "russian": "russia", "singaporean": "singapore", "malaysian": "malaysia",
    "indonesian": "indonesia", "filipino": "philippines", "pakistani": "pakistan",
    "sri lankan": "sri lanka", "norwegian": "norway", "zealand": "new zealand",
}
# The countries the table holds, so a line that names one wins the tie against a row keyed on
# the same ask words ("what can i eat in spain" against the leftover menu). The adjective is the
# same country, so "whats portuguese food like" is the same row as "what do they eat in portugal".
_A_COUNTRY = tuple(FOOD_IN) + ("britain", "holland") + tuple(FOOD_ADJECTIVES)


def _not_a_plate(clean):
    """True when a word in the line says it is about something other than the plate.

    The row is chosen on the country and an ask word, which is narrow enough for a line that
    names the country itself: "is the food safe in mexico", "what should i avoid eating in
    india", "can i take food into the eu" and "i'm from portugal, what should i eat" all name
    the country, so no fence on the row's choosing keeps the dish card off them. The same words
    that stand the row down at choosing time are read again here, in the one place every dish
    reply comes from, so a line the row should not answer gets its own answer back.
    """
    return any(re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", clean)
               for word in _FOOD_NOT_A_TRIP)


def _food_there(memory, understood):
    """What to eat in the country the line names, or the one the chat is going to."""
    clean = str(understood.get("clean") or understood.get("text") or "").lower()
    if _not_a_plate(clean):
        return None
    # A city is the city's question: the cheap-meal card is the meal in Rome, and the country's
    # dishes are no answer to a line that names the city ("is it expensive to eat in rome").
    if _find_in(clean, CHEAP_EATS):
        return None
    place = _find_in(clean, FOOD_IN)
    if not place:
        # the country by its adjective: "whats thai food like" asks the same thing
        place = FOOD_ADJECTIVES.get(_find_in(clean, FOOD_ADJECTIVES) or "", "")
    if not place:
        city = _find_in(clean, CITY_COUNTRY)
        place = CITY_COUNTRY.get(city or "", "")
    if not place:
        # "what about food" and "what should i eat there" name no country: the trip before them
        # does, and only a going-to line counts. "i live in spain" then "what should i eat" is a
        # person at home, and dishes to try on holiday is the wrong card for them.
        city = _place_in(memory, understood, CITY_COUNTRY)
        place = CITY_COUNTRY.get(city or "", "")
        if not place:
            place = _place_in(memory, understood, FOOD_IN)
        if place and not _a_trip_to(place, memory, understood):
            return None
    if place not in FOOD_IN:
        return None  # no country in the chat: the line is a food question about something else
    # "from portugal what should i eat" says the country is home without any of the resident
    # words above: the country follows "from", "born in" or "raised in", and a resident wants
    # what to cook at home, not the dishes to try on holiday.
    if re.search(r"(?<![a-z])(?:from|born in|raised in|grew up in)\s+(?:the\s+)?"
                 + re.escape(place), clean):
        return None
    name = "the USA" if place == "usa" else place.title()
    return f"In {name}: {FOOD_IN[place]}"


# "what do i need for a trip to italy" is the paperwork and the plug, not where to go: the country
# card answered with Rome, Florence and Naples, which is the answer to "where in Italy". The ask is
# a word for needing something plus a trip, and the answer is the short list everybody forgets -
# the passport's six months, the insurance, the plug - with the country named only for the plug and
# the tap water, from the tables the plug and water rows already keep.
_ESSENTIALS_ASK = ("essentials", "checklist", "what do i need", "what will i need", "do i need",
                   "will i need", "what do we need", "must i have", "have to have",
                   "what do i have to get", "what do i need to get", "what do i need to sort out",
                   # "do i need anything for the trip" is the same ask; the phrase, not the bare
                   # "anything", since "is there anything to do in Mexico" asks for a day out.
                   "need anything", "need something", "need to sort",
                   # The trip itself is in the ask as well as in the second part, because some of
                   # these lines say "before i go" and name no trip word at all.
                   "need for a trip", "need for the trip", "need for a holiday",
                   "need for the holiday", "need for a week in", "need before i go")


def _trip_essentials(memory, understood):
    """What to have with you before a trip, and the plug and water for the place they name."""
    # "a week away in cornwall" is the same question with nowhere foreign in it, so the lead
    # says what the passport is for rather than telling them to take one to Cornwall.
    text = ("Sort the paperwork first: anywhere abroad, that is a passport with six months left on "
            "it when you come back, travel insurance taken out the day you book rather than the day "
            "you fly, and your booking, policy and passport photo page saved on your phone so they "
            "work with no signal.")
    place = _place_in(memory, understood, PLUG_TYPES)
    if place:
        letter, shape, note = PLUG_TYPES[place]
        bits = []
        if letter != "G":
            bits.append(f"{place.title()} uses type {letter} sockets, so British plugs need an "
                        f"adapter")
        if place in WATER:
            if WATER[place]:
                bits.append("the tap water is fine to drink")
            else:
                bits.append("the tap water is not safe to drink, so bottled or filtered")
        if bits:
            text += " " + "; ".join(bits) + "."
    return text


# The walk is the subject here, so a line that says the word is not the flat you live in:
# "is there a flat walk near me" is a walk on flat ground, and "how do i clear the junk out of my
# flat" is the home. Only the second stands the row down.
_A_WALK_IS_SAID = re.compile(r"\b(walk|walks|walking|walked|stroll|strolls|strolling|"
                             r"path|paths|route|routes|rambl\w*|ramble|ramble)\b", re.IGNORECASE)


def _not_the_flat_the_ground(understood):
    """False when the line's "flat" is the home it lives in, or a thing that came out that way."""
    if isinstance(understood, dict):
        said = understood.get("text") or understood.get("clean") or ""
        if not said:
            said = " ".join(understood.get("words") or ())
        # A loaf, a cake or a Yorkshire pudding that came out flat is how a thing turned out, not
        # the ground underfoot: "the bread came out flat" was answered with a canal towpath, and
        # so were a cake, a pizza, a pudding and an omelette. The bake rows key their own names,
        # so this row only has to stand aside for them.
        if not not_the_flat_of_something_made(understood):
            return False
        if _A_WALK_IS_SAID.search(str(said)):
            return True
    return not_the_flat_you_live_in(understood)
def _a_visit_to_a_home(understood):
    """True when the reading has placed the line at somebody's care home rather than a border."""
    care = (understood or {}).get("care_home") if isinstance(understood, dict) else None
    return isinstance(care, dict) and str(care.get("shape") or "") == "bring"


# The six-month rule is the answer to "can i travel with two months left", and the card gives the
# rule rather than the answer: the person with two months on their passport read a paragraph about
# what most countries want to work out that the answer to their own question was no. The verdict is
# read off the time the line says is left and put in front (`lead=`); the card follows with the
# rule, the ten-year rule and what to do about it. A line that does not say how long is left (or
# says six months or more) keeps the card exactly as it was.
_A_TIME_LEFT = re.compile(
    r"\b(\d{1,3}|a|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*"
    r"(months?|weeks?|days?)\b", re.I)
# the line has to be about the passport being good enough, not a time mentioned in passing
_A_VALIDITY_WORD = re.compile(r"\bvalid\b|\bexpir|\bruns? out\b|\bleft\b|\benough\b"
                              r"|\bfly\b|\bflying\b|\btravel\b|\btrip\b|\bget in\b"
                              r"|\bget in to\b|\benter\b", re.I)
_UNDER_SIX = re.compile(r"\b(?:under|less than|fewer than|not)\s+(?:six|6)\b"
                        r"|\bshort of six\b", re.I)
# A line can hold two lengths - the time left on the passport and the length of the trip it is for
# ("can i fly if my trip is 10 days and my passport has 8 months left" read the first length and
# answered "No - too little time left" to eight months, thanks @cobalt-chicken). So the length that
# counts is the one nearest a word about the passport running out, not the first one said.
_ABOUT_THE_PASSPORT = re.compile(r"passports?|visas?|valid|expir\w*|renew\w*|enough"
                                 r"|left|remaining|runs?\b", re.I)
_ABOUT_THE_JOURNEY = re.compile(r"\bfly|\bflying|\btravel|\btrip\b|\bholiday|\bgo\b|\bgoing\b"
                               r"|\bget in\b|\benter\b|\baway\b|\babroad\b", re.I)
# how many words away from such a word a length can sit and still be its own
_NEAR_ENOUGH = 6
_NUMBER_WORDS = {"a": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                 "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def _the_time_left(said):
    """The (count, unit) the passport has left, or None when no length is about the passport.

    Every length in the line is weighed by how close it sits to a word about the passport running
    out ("passport", "valid", "expires", "left", "enough"); the nearest one wins, and a line
    whose only lengths sit far from any of those has said nothing about the time left. A journey
    word is the fallback set, so "can i fly with 2 months" is still read, and the trip's own
    length ("my trip is 10 days", "travel for 2 weeks") is never the one that counts.
    """
    words = said.split()
    marks = [i for i, word in enumerate(words) if _ABOUT_THE_PASSPORT.search(word)]
    if not marks:
        marks = [i for i, word in enumerate(words) if _ABOUT_THE_JOURNEY.search(word)]
    if not marks:
        return None
    best = None
    for match in _A_TIME_LEFT.finditer(said):
        first = len(said[:match.start()].split())
        last = first + len(match.group(0).split()) - 1
        away = min(abs(mark - word) for mark in marks for word in (first, last))
        if away > _NEAR_ENOUGH:
            continue
        if best is None or away < best[0]:
            best = (away, match.group(1), match.group(2).lower())
    if best is None:
        return None
    return best[1], best[2]


def _the_passport_verdict(understood):
    """No when the line says less than six months is left, and nothing it does not decide."""
    said = understood.get("text") or understood.get("clean") or "" \
        if isinstance(understood, dict) else ""
    said = " ".join(str(said).lower().replace("\u2019", "'").split())
    if not _A_VALIDITY_WORD.search(said):
        return ""
    too_little = "No - that is too little time left"
    if _UNDER_SIX.search(said):
        return too_little
    match = _the_time_left(said)
    if not match:
        return ""
    token, unit = match
    count = int(token) if token.isdigit() else _NUMBER_WORDS.get(token, 99)
    if unit.startswith("day"):
        return too_little
    if unit.startswith("week") and count < 26:
        return too_little
    if unit.startswith("month") and count < 6:
        return too_little
    return ""


ENTRIES = [

    # What to eat in the country the trip is to. The trip card lists cities and answers the
    # weather, the plugs and the money; the plate had nothing behind it, so "what about food"
    # after "im going to spain" was a search hedge and "what should i eat there" was the
    # cook-tonight menu. The callable reads the country from the line or from the trip before it
    # and turns down a line with no country in the chat, so a kitchen question still gets its own
    # answer.
    entry("food-in-the-country", (_FOOD_WORDS, _FOOD_SHAPE + _A_COUNTRY),
          _food_there,
          avoid=_FOOD_NOT_A_TRIP,
          # The country decides this row and no other row holds the plate: the risk of it winning
          # is a line with food words and no country, and its own callable turns that line down,
          # so a point of bias costs nothing and gets it in front of the leftover menu on the
          # "eat" word.
          bias=1),

    entry("where-in-month",
          (_month_names(), _MONTH_ASK),
          _a_month_verdict_once,
          # A month inside a named place is that place's question, and the fault, cost and
          # weather rows all name their own place. So are the two shapes a month word drifts
          # into: what to put in the case ("what should i pack for a week in spain in october"
          # lost its packing list to the October paragraph) and a trip already decided and
          # booked ("we are going to lisbon for four nights in may" lost the city guide, and the
          # guide was never given, so "what should we do there" had nothing to build on).
          avoid=("pack", "packing", "packed", "suitcase", "luggage", "what to bring",
                 "what to wear", "bring", "wear", "going to", "we are going", "we're going",
                 "im going", "i'm going", "nights", "night in", "booked", "booking", "book a",
                 "flights", "flight", "hotel"),
          bias=1),
    # The follow-up that points at the month the chat is already on: "is that a good time to go"
    # after "a cheap week away in august". The row above needs the month in its own line, so this
    # one finds it a turn or two back and hands the verdict row the month to answer with.
    entry("month-verdict-followup",
          (_A_MONTH_POINTED_AT, _A_TIME_VERDICT_ASK),
          _a_month_verdict_pointed_at,
          # a price or a booking is the cost row's question, and a place named in the line is the
          # guide's or the window's, so this row stands down for both.
          avoid=("book", "booking", "booked", "flight", "flights", "fly", "flying", "price",
                 "prices", "cost", "costs", "how much", "cheap", "cheapest", "expensive",
                 "visa", "insurance", "hotel", "hotels"),
          bias=4),
    # --- planning a trip ----------------------------------------------------------
    entry("plan-a-trip", (_PLAN_TALK, _PLAN_SHAPE), _trip_plan,
          # the before-you-go checklist is plans.py's holiday-countdown, and taking its lines
          # would trade a passport warning for an itinerary shape
          avoid=("passport", "insurance", "checklist", "before i go", "before we go",
                 "need to do", "what do i need", "prescriptions", "jabs", "visa",
                 # "where do i start" and "what should i do first" are the countdown, not the
                 # shape: the answer is the passport, the insurance and what sells out. A trip
                 # with kids or a baby is a family question with a family answer, and this row
                 # asks how many nights before it asks who is coming.
                 # A trip abroad is the checklist question, a city break is the weekend answer, and
                 # a trip with a dog is about the dog.
                 "where do i start", "do i start", "do first", "with kids", "with a baby",
                 "with a toddler", "with children", "abroad", "city break", "with a dog",
                 "with dogs", "with my dog", "with a pet", "with pets"),
          bias=1),

    # --- capitals and cities ------------------------------------------------------
    # "what is peru's capital" names no "of", so the country is in the key as well as the word
    # capital: a line naming a country in this table and asking about its capital is this entry's,
    # however it is phrased, and the country in the table also outweighs a history row that only
    # happens to contain the country's name ("whats the capital of south africa" was the
    # apartheid definition, because "what" and "south africa" were enough for it).
    entry("capital-city", (("capital", "capital city"),
                           tuple(CAPITALS) + ("of", "country")), _capital, bias=1,
          # "capital" has a second life in money, in law and in writing, and a country named
          # beside it made "do i pay capital gains tax in spain" and "what is capital
          # punishment in texas" the capital of the place: Madrid, and Austin.
          avoid=("gains", "tax", "taxes", "punishment", "death penalty", "letters",
                 "letter", "capitalise", "capitalize", "capitalism", "investment", "invest",
                 "investor", "business", "businesses", "start up", "startup", "fund",
                 "funding", "pension", "mortgage", "loan", "venture", "social capital",
                 "human capital", "how much")),
    # The second half is every shape of "what should I do there": a length of stay, a thing
    # they want there, or a request for the best of it. The city has to be named, so a line
    # about food or museums with no place in it never reaches this entry.
    entry("city-guide", (tuple(CITIES),
                         ("days", "day", "weekend", "week", "see", "miss", "visit", "going",
                          "trip", "holiday", "things to do", "to do in", "do in", "what should we",
                          "what should i", "what can we", "recommend", "recommendations",
                          "restaurants", "restaurant", "eat", "food", "museum", "museums",
                          "bars", "nightlife", "itinerary", "guide", "worth",
                          # The follow-up that names the city and nothing else: after "where
                          # should i go in spain" names three cities, "what about seville" asks
                          # for the same answer about a different one. The city still has to be
                          # in the line for the guide to answer it.
                          "what about", "how about", "thoughts on", "what do you think of",
                          "what do you reckon to",
                          # "im going to rome where do i start" is the guide's question, and
                          # "where do i start" was not one of its asking words
                          "where do i start", "where to start", "where should i start")),
          _guide, explain=True,
          # "bath" is a city and a thing you run, and "lag" is jet lag. The place has to be
          # the place meant, so the household words take the bath line away. Money words are
          # trip-budget's: "is 800 enough for a weekend in Lisbon" is a cost question.
          avoid=("jet lag", "jetlag", "lag", "hot bath", "bubble bath", "bath bomb",
                 "take a bath", "have a bath", "bath mat", "bathtub", "bath tub", "bathroom",
                 "clean the bath", "clean my bath", "soak", "shower", "enough", "afford",
                 "budget", "cost", "costs", "how much", "per day",
                 # What to pack is the packing list's, not the guide's: "what should I pack for
                 # a weekend in Edinburgh in December" is a suitcase question.
                 "pack", "packing", "suitcase", "luggage", "what to bring", "what to wear",
                 "bring", "wear",
                 # When to go is city-best-time's, and people phrase it as a visit: "best time
                 # to visit dubai" and "is october a good time to visit lisbon" both came back
                 # with the guide, which never says the month.
                 "best time", "good time", "time to visit", "time of year", "best season",
                 "what month", "which month", "best month", "month to visit",
                 "when should i go", "when should we go", "when to go", "too hot", "too cold",
                 "rainy season", "monsoon",
                 # A day trip is city-day-trip's question: with no row for this city it passes,
                 # rather than answering "day trips from Florence" with the Florence guide.
                 "day trip", "day trips", "day out", "nearby",
                 # How long to stay is city-stay's, and the guide took it: "how many days do i
                 # need in paris" was the Colosseum-and-museums card, which never says a number.
                 # A length word is the whole of that question, so the guide stands down for it
                 # and leaves the city to the days table. "days in" and "nights in" are left out
                 # on purpose: "what should i do in lisbon for 3 days" is a guide question.
                 "how many days", "how many nights", "how long", "how much time", "enough time",
                 "too long", "too short", "worth staying", "days do i need", "days should",
                 "days should i", "nights do i need",
                 # A trip being planned is city-stay's, and the guide took it: "im planning a
                 # trip to lisbon in may" was the sights card, and a later "back to lisbon,
                 # whats good to see" was the same card again, word for word, in one chat - the
                 # repeat guard in tests/test_long is what caught it. The planning words say the
                 # line is the plan, not the sights.
                 # A weekend being planned is still the city's: "we're planning a weekend in
                 # Lisbon in December" is the guide's question, and #7641 put it right. Only the
                 # trip being planned is fenced.
                 # "planning to go" is not fenced: it says what the person is doing, not
                 # what they want. "im planning to go to rome, what should i see" asks for the
                 # sights and this fence sent it to a punt.
                 "planning a trip", "planning our trip", "planning the trip",
                 "booked a trip", "booked flights"),
          # A city named is the one line this row is for, and the free-time rows were winning it:
          # "what should i do in lisbon for a weekend" was answered with "one thing out of the
          # house and one thing at home". Every other city question - when to go, what to pack,
          # the fares, the cheap eats, the day trips - is fenced above, so the guide can afford
          # to be the answer whenever the place is named and nothing else has claimed the line.
          bias=2),
    # "cheap places to eat in rome" was the guide, which answers with the Colosseum and a water
    # bottle: a good answer to another question. The city and an eating word are the question, and
    # the money, the diet and the one bad meal keep their own rows.
    entry("city-cheap-eats", (tuple(CHEAP_EATS) + tuple(CITIES) + ("eat there",),
                             ("eat", "eating", "eats", "food", "foods", "restaurant",
                              "restaurants", "lunch", "dinner", "cheap", "cheaply", "cheapest",
                              "good value", "street food", "market", "markets", "meal", "meals",
                              "breakfast", "snack", "snacks", "where to eat", "where should i eat",
                              "where can i eat", "places to eat", "something to eat")),
          _cheap_eats, bias=2, guard=_a_way_there_needs_no_eating,
          # A cost, a diet, a bad meal or a booking is another row's question, and the guide
          # sentence already mentions eating in a market street, so it is no help either way.
          avoid=("cost", "costs", "price", "prices", "how much", "expensive", "afford", "budget",
                 "tip", "tipping", "service charge", "book", "booking", "reservation",
                 "vegetarian", "vegan", "gluten", "gluten free", "allergy", "allergic", "halal",
                 "kosher", "diet", "food poisoning", "ill", "sick", "tummy", "stomach",
                 "dog", "cat", "toddler", "baby", "kids menu", "high chair", "water", "tap water",
                 "wine", "beer", "coffee", "breakfast in", "hotel breakfast",
                 # "i want a cheap flight to barcelona" is a flight, not a menu: the cheap word
                 # is the second signal and it was enough to take the line away from the fares
                 "flight", "flights", "fly", "flying", "airline", "airlines", "airfare",
                 "airport", "ticket", "tickets", "book a flight", "cheap flights",
                 "get there", "how do i get there", "getting there", "travel to",
                 # "cheapest way from london to manchester" named two cities and the word
                 # "cheapest", and this row took it for the eating answer: the way there is the
                 # fare comparison's question, so the getting itself stands this row down. The
                 # guard below keeps a line that names eating ("the cheapest way to eat well in
                 # paris"), where the same words are this row's own question.
                 "how do i get", "way to get", "way from", "get to", "get from", "getting from",
                 "train", "trains", "coach", "coaches", "bus", "buses", "drive", "driving")),
    # "is airport parking worth it" was the Citizens Advice card and "should i pay for airport
    # parking" was the savings ladder, because a "worth it" and a "pay" are money words before
    # they are travel ones. Parking at the airport is a travel decision with a known cheapest
    # shape, so it gets its own line.
    entry("airport-parking",
          (("airport parking", "parking at the airport", "park at the airport",
            "park the car at the airport", "parking for the airport", "airport car park",
            "airport carpark", "long stay parking", "long stay car park", "park and ride",
            "park and fly", "meet and greet parking"),
           ("worth", "cheaper", "cheapest", "cheap", "cost", "costs", "how much", "should i",
            "better", "taxi", "train", "bus", "compare", "book", "booking", "pre book",
            "prebook", "long stay", "week", "weeks", "days", "or", "pay", "paying", "parking")),
          ("Pre-book it: the price at the barrier is often two or three times the pre-booked "
           "price for the same space, and the cheapest of all is usually a park-and-ride a few "
           "minutes out with a shuttle. Compare the total against the alternatives before you "
           "choose, because a week of parking often costs about what a taxi costs each way, and "
           "for two or three days the taxi, the train or a lift from a friend usually wins. Check "
           "the drop-off charge too, since many airports now charge for the kiss-and-fly lane."),
          # "should i pay for airport parking" is a "pay" and a "should i" before it is a travel
          # decision, and money-for-a-big-buy read the two words and answered with the savings
          # rule, so the airport and the parking win the tie.
          bias=2,
          # An airport transfer, a flight problem and a car left running are other rows. The
          # airport's own name is not one of the words that says so: "long stay parking at
          # gatwick" is this question, and naming gatwick stood the row down on it.
          avoid=("terminal", "gate", "flight",
                 "flights", "delay", "delayed", "cancelled", "canceled", "lost", "stuck",
                 "check in", "checkin", "bag drop", "luggage", "baggage", "suitcase",
                 "transfer", "into the city", "to the city", "from the airport")),
    # A bare country with a trip in the line: "im going to spain" was an acknowledgement of the
    # news ("Good - that sounds like the right next step") and "we are going to greece in july"
    # was echoed back at the person. The country table has three places for each of them.
    entry("country-trip", (tuple(WHERE_TO_GO) + tuple(COUNTRY_ALIASES), COUNTRY_TRIP_WORDS),
          _country_trip,
          # a city inside the country is the city guide's question, and every other reason to
          # name a country has its own row
          avoid=tuple(CITIES) + NOT_A_COUNTRY_TRIP),
    # "Where should i go in spain": the country is named and the question is where in it. The
    # guide rows answer once a city is named, so before this the line that starts a trip was a
    # search hedge. The ask has to be a "where" phrase, so the weather, the money and the plugs
    # keep their country lines, and a city named in the line is the city guide's question.
    entry("country-where-to-go",
          (("where should i go", "where should we go", "where do i go", "where to go",
            "where would you go", "where should i head", "where should i go in",
            "where should we go in", "where do i go in", "where to go in",
            "where would you go in", "where should i head in",
            "where should i visit in", "where to visit in", "where should we visit in",
            "where in", "where abouts in", "what city should i visit in",
            "what cities should i visit in", "which city should i visit in",
            "which cities should i visit in", "which city in", "which cities in",
            "what city in", "what cities in", "what should i visit in",
            "best city in", "best cities in", "best place in", "best places in",
            "best place to go", "best places to go", "best city to go", "best cities to go",
            "where would you recommend", "where do you recommend", "where would you suggest",
            "where do you suggest",
            # "what about portugal", said straight after the Spain answer, is the same question
            # about the next country along: the country has to be named, so a city line stays
            # the city guide's (the avoid list holds every city name).
            "what about", "how about", "thoughts on", "what do you think of",
            "what do you reckon to", "anywhere in", "anywhere else in",
            "cities in", "places in"),
           tuple(WHERE_TO_GO) + tuple(COUNTRY_ALIASES)),
          _where_to_go,
          # a city that is named is the guide's, and when to go is the month tables' question
          avoid=tuple(CITIES) + ("best time", "best month", "when should i go", "when to go",
                                 "too hot", "too cold", "month", "weather in", "visa",
                                 "how much money", "water",
                                 # "what about" is also how people ask about living, driving
                                 # and safety: those are their own questions, not this table's
                                 "move to", "moving to", "live in", "living in", "place to live", "to live",
                                 "living costs", "emigrate",
                                 "residency", "driving", "drive", "car hire", "hire car",
                                 "licence", "insurance", "safety", "safe", "dangerous",
                                 "crime", "school", "schools", "job", "jobs", "work in",
                                 "hospital", "doctor")),
    # The trip is decided and the question is what it costs. "where-no-place" wants to know where
    # to go, and a line that asks how to spend less on the trip already booked got no answer at
    # all: "how do i keep costs down on holiday" was a shrug, "how do i make a holiday cheaper" the
    # same, and "how do i keep the cost of a holiday down" was told prices move too fast to know.
    entry("holiday-costs",
          (("costs down", "cost down", "cost of a holiday down", "keep the cost", "cut the cost",
            "cut costs", "reduce the cost", "cheaper", "spend less", "less money on",
            "on a budget", "a budget holiday", "holiday on a budget",
            # a bare "money off" was this row's key, and it took every discount question with an
            # asking word in it: "can i get money off a sofa" was told when to book a flight. The
            # trip has to be named for this row - everything else is the shop's discount row.
            "money off a holiday", "money off the holiday", "money off my holiday",
            "money off our holiday", "money off a trip", "money off the trip",
            "bring the cost", "cheapest way to book", "keep it cheap"),
           # the second signal is the asking word, not the subject: the subject is the trip, in
           # the line or in the turn before ("how do we keep the cost down" after the shortlist)
           ("how", "what", "should", "would", "could", "can", "do", "make", "keep", "get",
            "down", "we", "us", "i")),
          _holiday_costs,
          # the money is a sum to save for or a place it will reach, and those are other rows.
          # So is getting there by any one mode: "is it cheaper to travel by train than drive" is
          # the train-versus-car comparison, not a week away, and this row has nothing to say
          # about a journey that starts and ends the same day.
          avoid=("save up", "saving up", "how much", "how far", "where can i go",
                 "where should i go", "where should we go", "when should i go", "best time",
                 "train", "trains", "rail", "by rail", "coach", "coaches", "bus", "buses",
                 "drive", "driving", "by car", "car", "cars", "petrol", "diesel", "fly",
                 "flying", "flight", "flights", "airport", "commute", "commuting",
                 "season ticket", "parking"),
          # a discount on the trip and not money off a person: the same one test every price row
          # uses, so "should i borrow money off my mum" no longer gets the cheapest-week script.
          guard=a_price_not_a_loan,
          bias=2),
    # "Where should i go on holiday": no month, no country, which is how people start.
    entry("where-no-place", (HOLIDAY_ASK, HOLIDAY_SHAPE), _where_no_place,
          avoid=HOLIDAY_NOT, guard=_a_shortlist_question, bias=1),
    # The same want said as a want rather than a question: "i want to go somewhere warm", "my mates
    # want to go to benidorm", "the lads want a stag do", "me and my wife want a few days away".
    # Each line named no holiday word the asking row could meet ("somewhere warm" was chat's
    # smallest-version advice, "a few days away" was a greeting echo), so the want has its own row
    # with its own shortlist behind it.
    entry("want-a-trip", (_WANT_TRIP_SAID, _WANT_TRIP_SHAPE), _want_a_trip,
          # a trip already being packed for, priced or insured is another row's question, and so is
          # a week of dinners that happens to be cheap
          avoid=_TRIP_OTHER_ROW,
          guard=_a_trip_is_wanted, bias=1),
    # The follow-up after the city was named: "what should we do there", "and museums?".
    # "there" has to be in the line, so "what should we do this weekend" still passes.
    entry("city-followup", (("there", "that city"),
                            ("what should we do", "what should we see", "what should i do",
                             "what should i see", "what can i see", "what should i visit",
                             "what is there to see", "what is there to visit",
                             "what can we do", "recommend", "recommendations", "what about",
                             "anything else", "must see", "must do", "worth seeing",
                             "where should we eat", "what should we visit")),
          _guide_followup),
    # "what should we see" right after the guide: the sightseeing ask with no place in it, and
    # the city is the one in the reply before. The key is a thing-to-do word, not "do", so
    # "what do you think" and "how do I start" stay with whoever else answers them.
    entry("city-next", (("see", "visit", "eat", "miss", "walk", "stay"),
                        ("what", "should", "we", "i", "anything", "worth", "must", "now")),
          _guide_next,
          # "there" and the other follow-up words are city-followup's, and a day trip, a budget
          # or a suitcase is another entry's question about the same city.
          # A "how long" line is city-stay's question about the same city, and this row answered
          # "how long should i stay" after "im going to rome in may" with a list of day trips -
          # the words "stay" and "should" are in its key, and neither is what the line is about.
          avoid=("there", "day trip", "day trips", "days", "weekend", "budget", "cost", "costs",
                 "how long", "how many days", "how many nights", "how much time", "nights",
                 # a line about a child is not a line about a city: "how do i get my 3 year old to
                 # eat" met "get", "i" and "eat" here and was answered with a city guide.
                 "my son", "my daughter", "my kid", "my kids", "my child", "my children",
                 "toddler", "year old", "years old", "month old", "months old",
                 "how much", "pack", "packing", "airport", "flight", "hotel", "train",
                 "else", "another", "too",
                 # "miss" in this key is missing a city, and the habit word "streak" is not a
                 # place: "i missed my streak yesterday" was read as a city line. A streak, a
                 # habit and a diet are the person's own effort, not a destination.
                 "my streak", "the streak", "streak", "my habit", "my diet", "no sugar",
                 "my routine", "my resolution")),
    # "and what about museums" - a thing they want in the city named a turn ago.
    entry("city-detail", (("museums", "museum", "restaurants", "restaurant", "food", "bars",
                           "nightlife", "sights", "sightseeing", "shops", "shopping"),
                          ("there", "also", "too", "worth", "recommend", "what about", "any",
                           "should we", "can we", "anything")),
          _guide_followup),
    entry("city-best-time", (tuple(BEST_TIME) + tuple(CITY_COUNTRY) + tuple(WHEN_TO_GO),
                             ("best month", "best months", "best time", "when should i go",
                              "when to go", "when should we go", "when should you go",
                              "what month", "which month", "good time to go", "best season",
                              "good month", "best time of year", "what time of year",
                              "worth visiting", "worth a visit",
                              "worth going", "too hot", "too cold", "rainy season", "monsoon",
                              "time to visit", "good time", "time of year", "month to visit")),
          _best_time,
    # "What should we do in cornwall", "things to do in the lake district", "best beaches in
    # devon", "is padstow worth a visit": one card per region, in the region's own words.
          # A place plus a "which month" is a travel question, and the houseguest and moving
          # entries read "visit" and "month" too: the entry that names the place wins the tie.
          bias=1),
    entry("region-days",
          (tuple(REGION_PLACES), _DAYS_ASK),
          _region_days,
          # A trip already decided keeps the acknowledgement and the packing, and the when-to-go
          # row is the month question. The kitchen words keep a pasty or a pudding out of it.
          avoid=("best time", "best month", "when should i go", "when to go", "pack", "packing",
                 "suitcase", "hotel", "hotels", "cottage", "how long", "how many days",
                 "days in", "nights in", "cost", "costs", "how much", "budget", "price",
                 "flights", "flight", "train", "drive", "driving", "parking", "weather",
                 "rain", "rains", "raining", "pregnant", "dog", "dogs", "recipe", "recipes",
                 "pasty", "pastry", "pudding", "cook", "cooking", "bake", "baking",
                 # getting there is a transport question this card knows nothing about
                 "how do i get", "how do i get to", "get to", "how to get", "getting to",
                 "how far", "ferry", "ferries", "train", "bus", "drive", "driving"),
          bias=1),
    # "how long should i stay in paris" was a search hedge. The number is the city's, so it is a
    # table; the callable turns down "how long is the flight to rome", which shares the words.
    entry("city-stay", (tuple(CITY_DAYS),
                        ("how long", "how many days", "how many nights", "days should",
                         "days in", "nights in", "worth staying", "long should i stay",
                         "long should we stay", "enough time", "too long", "too short",
                         "how many days do i need", "how much time", "days", "nights")),
          _stay_length,
          # Sprouts are a city only by their first word: "how long do i roast brussels sprouts"
          # was two full days in Brussels. The oven words are what says the line is in the
          # kitchen, and no one asks how many days to stay in a vegetable.
          avoid=("roast", "roasted", "roasting", "oven", "bake", "baked", "baking", "boil",
                 "boiled", "boiling", "steam", "steamed", "fry", "fried", "frying", "grill",
                 "grilled", "sprout", "sprouts", "florets", "recipe", "recipes", "sauce",
                 "soup", "side dish", "air fryer"),
          # a weight in the line is a bird for the oven, not a city to stay in
          guard=_a_weight_is_the_kitchen),
    # A country is not a city, and the days table is keyed on cities, so "how many days should i
    # spend in portugal" reached the daily budget (the money row is keyed on the country and the
    # word "spend") and "how long should we go for" after the Portugal card reached a search
    # hedge. The length of a country trip is the length of the cities the card itself named, so
    # the row is keyed on the countries the card has and answers from the same days table.
    entry("country-stay-length", (tuple(WHERE_TO_GO),
                                  ("how long", "how many days", "how many nights",
                                   "how long should", "how long do", "days should", "days in",
                                   "nights in", "how much time", "how many days do we need",
                                   "enough time", "too long", "too short", "days", "nights")),
          _country_stay_length,
          # A turkey is a country and a Christmas dinner is not a holiday abroad: the same
          # kitchen words that keep "how long do i roast brussels sprouts" out of the city table.
          avoid=("roast", "roasted", "roasting", "oven", "bake", "baked", "baking", "boil",
                 "boiled", "boiling", "steam", "steamed", "fry", "fried", "frying", "grill",
                 "grilled", "recipe", "recipes", "sauce", "soup", "stuffing", "thaw", "thawed",
                 "defrost", "freezer", "cook", "cooked", "cooking", "dinner", "christmas",
                 "thanksgiving", "sandwich", "salad", "spice", "spices",
                 # a process that takes time is not a stay either: in a passport thread "how long
                 # does a renewal take" was answered with "Barcelona three full days, Seville
                 # two", because Spain was named two turns before and the country took the line
                 "renewal", "renewals", "renew", "renewing", "passport", "licence", "license",
                 "application", "applying", "paperwork", "post it off", "delivered",
                 "delivery estimate", "refund", "claim form", "probate", "mortgage offer",
                 "planning permission", "referral", "waiting list"),
          # "how long does a 5kg turkey take" is the Christmas bird: a table of days in Istanbul
          # answered it. The weight is what says the line is in the kitchen.
          guard=_a_weight_is_the_kitchen,
          bias=1),
    # "how long should i spend there" names no city, so the key is the pointing-back words and
    # the length words together, and the callable needs the city from the turns before.
    entry("city-stay-followup", (("there", "that city", "this city", "the city"),
                                 ("how long", "how many days", "how many nights", "enough time",
                                  "too long", "too short", "days", "nights", "stay", "spend")),
          _stay_there,
          # "there" and "day" are in half the lines people write about a child who will not
          # sleep, and "my toddler wakes up at 5am every day. is there a way to shift that
          # later?" was answered with this row's city question before it was a sleep line.
          avoid=("toddler", "baby", "newborn", "child", "children", "kid", "kids", "son",
                 "daughter", "wakes", "waking", "wake up", "bedtime", "nap", "naps", "sleep",
                 "slept", "asleep", "4am", "5am", "6am", "every morning")),
    # The clock question, which main answered with a search hedge: "how early should i get to
    # the airport". It shares "airport" and "get to" with the transfer entry, so that one avoids
    # the clock words rather than both being scored against each other.
    # The flight is in the key as well as the airport, because people ask the clock without
    # naming the airport: "how long before a flight should i arrive", "is 2 hours enough before a
    # flight", "will i miss my flight if i leave at 5". Each of those was a search hedge, and the
    # answer is the same rule plus the arithmetic the line makes possible.
    entry("airport-arrival", (("airport", "airports", "flight", "flights", "plane", "planes",
                               "fly", "flying", "flight's",
                               "boarding", "check in", "check-in", "checkin", "departure",
                               "gate"),
                              ("how early", "how long before", "what time", "when should",
                               "get to the airport", "arrive at the airport", "leave for the "
                               "airport", "before my flight", "before the flight", "hours before",
                               "how long do i need", "enough time", "too early", "enough",
                               "hours", "minutes", "how long", "leave at", "set off", "set out",
                               "miss my flight", "make my flight", "in time", "plenty of time",
                               "what time do i", "when do i", "when is", "how early do i",
                               "when does", "when do", "when will",
                               "leaving home", "leave home", "leaving at", "leaves at",
                               "leaving for the airport", "leave for the airport", "long flight",
                               "flight time", "how many hours", "is it a long")),
          _airport_early,
          # "what time is my flight" asks the bot to read a booking it cannot see, and an answer
          # about how early to arrive is no answer to it: that line has its own entry.
          avoid=("what time is my flight", "when is my flight", "what time is our flight",
                 "when is our flight", "what time do i fly", "when do i fly",
                 "what time am i flying", "when am i flying", "what time does my flight land",
                 "what gate", "which gate",
                 # the same question in the plural and with the flight as the subject: "when do
                 # we fly", "when do we fly out" and "what time is the flight" were all told how
                 # early to be at the airport, which is the deadline for a flight they have not
                 # named a time for. Two hours before what, was the answer they got.
                 "when do we fly", "when do we fly out", "when do we leave", "when are we flying",
                 "what time is the flight", "what time is our flight", "what time do we fly",
                 "what time are we flying", "what time do we leave"),
          # "we need to leave for the airport at 4" is a plan, not a question: the rule is no
          # answer to a plan, so the line has to be asking how early.
          ask=("how early", "how long", "what time", "when", "should", "do i need", "need to be",
               "enough", "too early", "advice", "hours", "minutes", "is it worth", "will i",
               "if i", "is it", "can i", "leave at", "leaving at", "leaves at", "set off",
               "setting off", "set out", "in time", "leave home", "leaving home",
               "leave the house", "leaving the house")),
    # The bot cannot see the booking, and a guessed time is the one answer that is worse than
    # none. "when is my flight" reached the fares entry through the word "when" and was told how
    # far ahead to book, which is an answer to a different question.
    entry("my-flight-time", (("flight", "flights", "plane", "flying", "boarding pass", "land",
                              "lands", "landing"),
                             ("what time is my", "when is my", "what time is the", "when is the",
                              "what time does my", "when does my", "what time do i fly",
                              "when do i fly", "what time am i flying", "when am i flying",
                              # the same question for two or more people, and with the flight
                              # rather than the person as the subject: "when do we fly",
                              # "what time is the flight", "when are we flying"
                              "when do we fly", "when do we fly out", "what time do we fly",
                              "when are we flying", "what time are we flying",
                              "when do we leave", "what time do we leave",
                              "what time is our flight", "when is our flight",
                              "what terminal", "which terminal", "what gate", "which gate",
                              "what time does the flight land", "what time does it land",
                              "what time do we land", "what time will we land",
                              "what time do i land", "when do we land", "when does the flight "
                              "land", "when do i land")),
          _my_flight_time),
    # "airport" alone is the place half, because the city and the airport are said in either
    # order: "from the airport to the city in barcelona" has no "barcelona airport" in it.
    entry("airport-to-city", (tuple(AIRPORT_TRANSFER) + ("airport",),
                              ("to the centre", "to central", "city centre", "into town",
                               "to the city", "from the airport", "airport to", "transfer",
                               "get to", "get from", "how do i get", "cheapest way", "taxi",
                               "train from", "bus from")),
          _airport,
          # Which airport a city has is city-airport's question, not a transfer note.
          avoid=("closest airport", "nearest airport", "which airport", "what airport",
                 "how early", "how long before", "how many hours before", "how soon",
                 "what time should i", "when should i get", "get there", "arrive at the airport",
                 "get around", "getting around", "get round", "getting round", "around town",
                 "airport to fly into", "airport do i", "airport should i", "airport closest",
                 "which london airport", "airport is closest", "airport is nearest",
                 "airport near the", "airport nearby",
                 # A scam or a rigged meter is taxi-abroad's question, and it must take only the
                 # scam words: "how much does a taxi cost from the airport in rome" is a price,
                 # and a named city is exactly when the transfer note has the number.
                 "scam", "scammed", "ripped off", "rip off", "overcharge", "overcharged",
                 "meter", "rigged", "cheated", "ripped me",
                 # "is a taxi from the airport expensive" asks what a cab costs, not the transfer,
                 # and taxi-abroad answers it with the warning or the city's fare.
                 "expensive", "how much is a taxi", "fare",
                 # a price, a fare or a cost wants a number and this answer has none; the
                 # advance-ticket row is the one that says how to get a cheap ticket
                 "how much", "cost", "costs", "price", "prices", "fares", "advance",
                 # "how do i get cheap flights to rome" asks about fares, not the transfer, and
                 # "cheapest way from the airport" is the transfer - so the fare nouns only.
                 "flights", "flight", "airline", "airlines", "fare", "fares", "deal", "deals",
                 "book", "booking", "compare",
                 # How early to be there is airport-arrival's question, not "how do i get in".
                 "how early", "how long before", "before my flight", "before the flight",
                 "what time should i", "arrive at the airport")),
    # Getting in from the station, the coach stop or the port with no city named: the four
    # questions in _arriving. "how do i get from the train station to the hotel" was the Spanish
    # phrase card and "how do i get from the station to my hotel" was a hotel-booking note.
    entry("arriving-into-town", (tuple(_ARRIVAL_KINDS) + ("train", "coach", "bus"),
                                 tuple(_ARRIVING_ASK)),
          _arriving,
          # Packing for the trip is the journey row's question, and a room to sleep in is the
          # hotel question: this row is the ride from the platform to the door.
          avoid=("pack", "packing", "what to take", "what should i take", "what do i need for a",
                 "hotel to stay", "which hotel", "best hotel", "cheap hotel", "book a hotel",
                 "where to stay", "price", "prices", "cheapest fare", "tickets to",
                 "how early", "how long before", "should i book", "worth visiting", "what to see",
                 "airport transfer", "from the airport", "parking", "left luggage", "lost property",
                 "journey", "long journey", "hours on the",
                 # An intercity trip is the coaches and trains question: "how do i get to london
                 # by coach" wants the fares, the hold bag and the 15 minutes early, not a
                 # station-to-hotel ride.
                 "by coach", "by train", "by bus", "by rail", "by car", "by plane",
                 "a train to", "a coach to", "a bus to", "coach to", "train to",
                 "overnight coach", "overnight train", "between two cities", "how long does",
                 # A ticket or a fare is the price question, and this answer is the ride from
                 # the platform: "how do i get cheap train tickets" was told the metro into
                 # town costs 2 to 5 euros, which is the wrong question answered well.
                 "ticket", "tickets", "railcard", "advance", "off-peak", "off peak",
                 "fares", "cheap train", "cheaper train", "cheapest train",
                 "train times", "timetable", "train prices",
                 # A card that will not go through on a bus or a train made this row the winner
                 # on the refund and the missed-last-bus lines (its key words are rarer once the
                 # transport words are shared), so the claim and the missed ride stay with the
                 # row that answers them.
                 "refund", "refunds", "refunded", "money back", "compensation", "claim",
                 "claims", "complain", "complaint", "delay", "delayed", "cancelled",
                 "canceled", "missed", "miss the", "last bus", "last train", "last coach",
                 "last tram", "stranded", "did not turn up", "didnt turn up",
                 "no bus came")),
    # "which airport do i fly into for porto" is a different question from "how do i get in":
    # it wants the name and the code, so it has its own table rather than a transfer note.
    entry("city-airport", (tuple(AIRPORT_NAME),
                           ("closest airport", "nearest airport", "which airport", "what airport",
                            "airport to fly into", "fly into", "airport do i", "airport should i",
                            "airport is closest")),
          _city_airport),
    # A named city beats a general plan for the day ("a day out with the kids near Manchester"
    # wants the trips out of Manchester, not advice to pack a picnic), so this entry carries a
    # bias against the family calendar entries that key the same words.
    entry("city-day-trip", (tuple(DAY_TRIPS),
                            ("day trip", "day trips", "day out", "nearby", "near here",
                             "close to", "what else")),
          _day_trip, bias=2),
    # "how do i get around paris" is not "how do i get in from the airport", which is what
    # airport-to-city answered it with. The city is the subject, so the key is the city plus a
    # word that only a getting-around question uses.
    entry("city-transit", (tuple(CITY_TRANSIT) + tuple(TRANSIT_CARDS) + CARD_NAMES,
                           ("get around", "getting around", "get about", "getting about",
                            "around town", "get round", "getting round",
                            "metro", "subway", "underground", "tube", "u-bahn", "tram", "trams",
                            "bus", "buses", "public transport", "transport", "transit",
                            "travelcard", "travel card", "day pass", "oyster", "metro card",
                            "how do i travel", "how do people travel",
                            # The card has a name of its own, and people ask about it by name:
                            # "should i get a suica card before i go" names no city at all.
                            "card", "cards", "pass", "top up", "contactless", "chipkaart")),
          _transit,
          # A transfer is airport-to-city's question, a train between cities is cheap-trains', and
          # a taxi or a hire car is neither. "get around" phrases survive, because the callable
          # only checks the airport and booking words it knows.
          avoid=("airport", "flight", "flights", "fly into", "train to", "train from",
                 "train ticket", "book", "booking", "hotel", "day trip", "day trips",
                 "worth visiting", "best time to go", "car hire", "rent a car", "hire a car",
                 "bus to", "bus from",
                 # A fare between two cities is not a ticket for the metro.
                 "cheapest", "cheap", "flight", "flights", "airline", "compare", "deal"),
          # "do i need a navigo card in paris" ties with the money answer on "card", and the
          # city with a transit word in it is the more specific question.
          bias=1),
    entry("trip-budget", (tuple(DAILY_BUDGET),
                          # "enough" alone is "is it warm enough for the beach", so only the
                          # cost words count; the callable checks the line again.
                          ("enough", "enough for", "will that be enough", "is that enough",
                           "budget",
                           "budget for", "cost", "costs", "afford", "money", "spend",
                           "spending", "expensive", "pricey", "will that do", "will that cover",
                           # "is budapest cheap" is the same question as "is budapest pricey":
                           # cheap is a cost word in the line, and the callable checks for a
                           # place and turns down a line about flights or a hotel.
                           "cheap", "cheaper", "inexpensive", "affordable", "worth it",
                           "does that cover", "go far", "saved", "pounds", "euros", "dollars",
                           # "how much is a week in Lisbon" is the same question as "how much
                           # does a week in Lisbon cost", and it used to reach the prices entry.
                           "how much is a week", "how much is a weekend", "how much is a trip",
                           "how much for a week", "how much for a weekend", "much is a week",
                           "much is a fortnight", "much is ten days", "much is five days",
                           "much is four days", "much is three days", "much is two weeks",
                           # "how much spending money for a week in rome" is the same question,
                           # and it tied with money's impulse-buying habit answer: the phrase is
                           # worth three points, and naming a place beats a habit.
                           "spending money", "spending cash")),
          _trip_budget,
          # "is budapest cheap" tied with the cheap-eats card, which answers about lunch: a
          # daily rate is the answer to what a place costs, and the callable has already turned
          # down every line without a place and a cost word in it.
          bias=1,
          # A train fare, a flight or a hotel is a price, not a daily budget: "cheap train to
          # paris" belongs with the rail and flight entries.
          # Money that is not spending money: a transfer to someone who lives there, rent, a
          # wage. A trip has a length and a purpose; these do not.
          avoid=("train", "trains", "flight", "flights", "ticket", "tickets", "fare", "fares",
                 "hotel", "hotels", "insurance", "passport", "visa",
                 "send money", "sending money", "send some money", "transfer", "transferring",
                 "remittance", "rent", "rents", "mortgage", "salary", "wage", "wages",
                 "cost of living", "live in", "lives in", "living in", "moved to",
                 "moving to", "exchange rate", "currency",
                 # Money you take with you is how to carry it and change it, not a daily budget:
                 # "how much money should i take to spain" was getting the daily rate instead.
                 "money should i take", "cash should i take", "money to take", "cash to take",
                 "how much cash", "take in cash",
                 # "whats the best way to carry money in italy" is about carrying it, not about
                 # the rate; the place in the line was the only thing the daily budget needed
                 "carry", "carrying", "carried", "money belt", "safe", "safely", "stolen",
                 "wallet", "pickpocket")),
    entry("pack-cold-city", (("pack", "packing", "take", "wear", "clothes", "bring",
                              "carry"),
                             ("cold", "winter", "december", "january", "february", "november")),
          ("Pack for 2 to 8C, wind and rain: a waterproof coat with a hood, warm layers you can "
           "take off indoors, and shoes you can walk a hill in. It gets dark around 4pm in "
           "December, so a small torch and plans for the afternoon indoors help."),
          # "take" is how people ask about medicine and "cold" is what they are ill with, so
          # without this the packing list answered "should i take ibuprofen for a cold". A
          # packing question names something you carry or wear; an illness or an occasion does not.
          ask=("pack", "packing", "take", "taking", "wear", "wearing", "bring", "carry",
               "coat", "clothes", "suitcase", "luggage", "shoes", "boots"),
          avoid=("ill", "illness", "sick", "symptom", "fever", "cough", "sore throat", "medicine",
                 "vitamin", "vitamins", "supplement", "supplements", "vaccine", "jab", "dose",
                 "tablet", "tablets", "medication",
                 "ibuprofen", "paracetamol", "antibiotic", "antibiotics", "doctor", "pharmacy",
                 "cold sore", "cold sores", "herpes", "lip", "lips",
                 "shower", "bath", "sauna", "beer", "drink", "day off", "wedding", "funeral",
                 "interview", "party",
                 # a vitamin, an inhaler or a hayfever tablet is never luggage, even when the
                 # line names a winter month ("should i take vitamin d in winter")
                 "inhaler", "insulin", "statin", "statins", "prescription", "hayfever",
                 "hay fever", "chest infection",
                 # food that has to stay cold is a lunchbox question, not a winter packing list:
                 # "how do i pack a lunch for work that stays cold" was the coat-and-torch answer
                 "lunch", "lunchbox", "lunch box", "packed lunch", "sandwich", "sandwiches",
                 "food", "leftovers", "meal",
                 # "what can i take for a cold" is the remedy question, and it tied this packing
                 # list on "take" and "cold". An illness said out loud - got a cold, flu, a blocked
                 # nose - is never luggage; cold weather and cold cities still are.
                 "got a cold", "have a cold", "caught a cold", "catch a cold", "my cold",
                 "cold and flu", "head cold", "chesty", "runny nose",
                 "blocked nose", "sneezing", "sniffles", "the flu", "got flu", "have flu",
                 # putting the winter clothes away in spring is a storing question, not a
                 # packing one: "how do i store winter clothes" was given the 2-to-8C packing list
                 "store", "storing", "storage", "put away", "pack away", "packed away",
                 "moth", "moths", "cedar", "loft", "under the bed"), bias=1),
    # A city break is a trip, and "take for a cold city break" is a packing question whatever
    # the weather: without this the row above tied with the cold remedy and lost, and "take on a
    # city break" reached the shift-break rule, because "break" is a work word. Keyed on the trip
    # itself ("city break") so that "what should i take for a cold" stays the cold.
    entry("pack-city-break", (("city break", "city trip", "citybreak"),
                              ("pack", "packing", "take", "taking", "wear", "wearing", "bring",
                               "carry", "clothes", "coat", "shoes", "boots", "bag", "case")),
          _city_pack,
          # "a city break in june with a toddler" is still packing, but the money lines name a
          # city break too: "how much spending money for a city break" is a budget, not a bag.
          avoid=("money", "budget", "spending", "cash", "cost", "hotel", "flight", "flights"),
          # "a cold city break" also reaches the cold remedy ("take for a cold"), so this row
          # has to be ahead of it rather than level with it.
          bias=1),
    # The bag for a train is not the bag for a city break: no flight, no 2-to-3-night list, and
    # a seat reservation and a screenshot of the ticket are the two things people forget.
    entry("train-journey-packing", (("train", "trains", "rail", "railway",
                                     # a coach for six hours is the same journey: the phrase
                                     # forms only, because a coach is also a sports coach and a
                                     # bus is also a line about losing something on one
                                     "coach trip", "coach journey", "by coach", "on a coach",
                                     "on the coach", "coach for", "trip on a coach",
                                     "coach to", "bus journey", "bus trip"),
                                    ("pack", "packing", "take", "bring", "need", "wear", "bag",
                                     # "ive got a long train journey on friday" says what it is
                                     # and never asks: the journey words are the ask as well
                                     "journey", "journeys", "ride", "trip", "tips", "advice",
                                     "hours", "for hours")),
          "Tickets first, with a screenshot as well as the app, because signal in a tunnel is not "
          "a plan. Then water and a snack, a layer you can take off, a charger and headphones, "
          "and your seat reservation if you have one. On a long journey add a pillow, a book and a "
          "spare top for a delay, and keep the bag small enough to lift overhead yourself.",
          # a train set, a pair of trainers and staff training are not a journey: note that
          # "trainers" and "training" cannot go in the avoid, because both fold back onto "train"
          # and would shut this row for every line it is for
          ask=("train", "trains", "rail", "railway", "coach trip", "coach journey",
               "by coach", "on a coach", "on the coach", "coach for", "trip on a coach",
               "coach to", "bus journey", "bus trip"),
          guard=_the_journey_in_the_line,
          avoid=("train set", "train sets", "potty", "toilet", "toilet training", "model",
                 # "how many hours should i train a week" is the verb: hours and a week were
                 # enough to make this row answer a workout question with a packing list
                 "train a week", "train every day", "train each day", "training for",
                 "how many hours", "should i train", "i train", "hours a week",
                 # a duration is a different question from what to put in the bag
                 "how long", "how far", "what time", "how much is", "how much does",
                 # "how do i pack for a coach trip" already has a weekend packing answer that
                 # says two or three nights, which is better than this card can be; a toddler
                 # and a baby have their own travel rows
                 "pack for", "packing for", "how do i pack", "what do i pack",
                 "with a toddler", "with a baby", "with my son", "with my daughter",
                 "my son", "my daughter", "my kids", "my children",
                 # a pushchair on a coach has its own answer, and it was better than this one
                 "pushchair", "pushchairs", "buggy", "buggies", "pram", "prams",
                 "stroller", "wheelchair", "mobility scooter",
                 # "how long to train" is a follow-up about a running plan: the word is a verb
                 "how long to train", "long to train", "how long to practice",
                 # "is that one good for a train journey", asked about a book the bot just
                 # named, is a reading question: the packing list was taking it. The fence is
                 # the shape of the ask about a thing already mentioned, not the word "book",
                 # because "what should i take on a train" is this row's own line.
                 "good for a", "good for the", "good for my", "that one good", "is that one",
                 "is this one", "would that one", "would this one",
                 "how much", "cost", "price", "fare", "fares", "ticket price", "delay", "delayed",
                 "cancelled", "cancellation", "strike", "strikes", "refund", "seat reservation only",
                 "dog", "cat", "bike", "bicycle")),
    # The judging frames are the same question about the world: "do you think march is too cold",
    # "is it too cold for a tent in april", "will it be warm enough in june". They are phrases,
    # never the bare "cold" or "hot" - "im too cold" and "the house is cold" are not weather.
    entry("city-weather", (("weather", "too cold", "too hot", "too wet", "too windy",
                            "too rainy", "too warm", "warm enough", "cold enough", "hot enough",
                            "cold in", "warm in", "hot in", "rainy in", "rain in"),
                           ("like", "usually", "month", "warm", "cold", "rain",
                            # the time of year is the other half of the ask
                            "go", "going", "visit", "visiting", "trip", "holiday", "there",
                            "time to", "worth")),
          _weather, bias=1),

    # --- flights and airports -----------------------------------------------------
    entry("jet-lag-east", (("jet lag", "jetlag"), JET_EAST_KEYS),
          ("Fly east and your body has to run ahead, so shift your bedtime 30 minutes earlier for "
           "a few nights before you go, then get out in morning light at the other end. Skip "
           "caffeine after midday there and stay up until at least 10pm local."), bias=1),
    entry("jet-lag-west", (("jet lag", "jetlag"), JET_WEST_KEYS),
          ("Flying west stretches your day, so go to bed an hour later than usual for the last two "
           "or three nights before you go, then sleep in a little at the other end and get "
           "afternoon daylight. Stay up to 10pm local on night one rather than napping, which is "
           "what leaves you awake at 3am."), bias=1),
    entry("jet-lag-baby", (("jet lag", "jetlag"),
                           ("baby", "babies", "toddler", "kid", "kids", "child", "children",
                            "newborn")),
          ("Keep the baby on their usual routine and move it by an hour a night once you land, "
           "feed on local meal times, and get them out in morning daylight: light does the work. "
           "A night flight that lands in the evening is easier than one that lands at noon, and "
           "plan one quiet day at the other end."), bias=1),
    entry("time-there", (("time difference", "time zone", "whats the time", "what time is it",
                          "what is the time", "the time in", "local time", "hours ahead",
                          "hours behind", "ahead of us", "behind us", "how many hours ahead",
                          "same time", "clock in", "morning or evening", "day or night",
                          "awake yet", "asleep yet"),
                         tuple(TIME_ZONES) + tuple(MULTI_ZONES)),
          _time_zone),
    # The same question with no city in it: "what time is it", "whats the time", "do you know the
    # time". Its own row, because the time-there key needs a place and there is none to find.
    entry("time-here", (("what time is it", "whats the time", "what is the time",
                         "the time now", "got the time", "know the time", "what oclock",
                         "what o'clock",
                         # the same question with a please in front of it: "can you tell me the
                         # time", "do you have the time", "the time please"
                         "tell me the time", "the time please", "have the time", "the time"),
                        ("time", "clock", "oclock", "o'clock", "now", "here")),
          _the_clock_here),
    entry("body-clock-travel", (("body clock", "internal clock", "time zone", "sleep clock"),
                         ("reset", "shift", "fix", "adjust", "all over", "wrong", "out of", "back",
                          "sort")),
          ("Fix it with light and meals rather than willpower: get outside in the morning, keep "
           "the evening dim, eat at the new meal times and move bedtime 30 minutes a night rather "
           "than all at once. No long naps, and no caffeine after lunch while it settles.")),
    entry("jet-lag", (("jet lag", "jetlag"), ("over", "cure", "fix", "avoid", "better", "help",
                                              "deal", "dealing", "tired", "sleep", "survive",
                                              # "how do i stop getting jet lag" hedged: the ask
                                              # was "stop" and "getting" and neither was here
                                              "stop", "prevent", "preventing", "getting",
                                              "beat", "reduce", "less", "worse")),
          ("Get daylight as soon as you can after landing, eat at local meal times, and keep "
           "caffeine to the local morning. Sleeping on arrival makes it worse; a short 20-minute "
           "nap before 3pm is the most you want.")),
    entry("eiffel-steps", (("eiffel tower", "eiffel"), ("steps", "stairs", "climb", "walk up",
                                                         "how many")),
          "674 steps to the second floor and 1,665 to the top. Most people walk up to the second "
          "floor (10 to 15 minutes and no queue) and take the lift from there; the stairs above "
          "the second floor are for the very keen."),
    entry("airport-security", (("security", "scanner", "pat-down"),
                               ("happens", "like", "through", "expect", "first", "what",
                                "take out", "laptop", "shoes", "belt", "liquids")),
          ("You put your bag in a tray, take out laptops and liquids (100ml in a clear bag), and "
           "walk through a scanner, sometimes with a pat-down. It takes ten minutes and nobody "
           "minds how nervous you are, so just follow what the staff say and give yourself two "
           "hours before the flight."),
          # "I've never flown before, what happens at security" is about the procedure, not
          # the nerves: it ties with flight-nervous on rank, and the specific answer should win.
          # Food through security belongs to flight-food and the 100ml rule belongs to
          # flight-liquids, so both stay out of this one; bias alone would steal the liquids tie.
          avoid=("sandwich", "sandwiches", "food", "snack", "snacks", "lunch", "picnic",
                 "bottle", "bottles", "water", "liquid", "liquids", "100ml",
                 "closest", "nearest", "into",
                 # "screen" is the screen of a laptop, not screening, and a cleaning or repair
                 # question is not the airport.
                 "screen", "monitor", "keyboard", "clean", "cleaning", "cracked", "repair",
                 "printer", "phone", "tv", "television", "password",
                 # A one-time code sent by text is not the scanner: "i keep getting security
                 # codes by text" is a phone or an account, and "what should i change first" is
                 # about that, not about a tray and a 100ml bag.
                 "code", "codes", "text", "texts", "texting", "message", "messages", "sms",
                 "otp", "pin", "pins", "login", "log-in", "account", "account", "hacked", "spam"),
          bias=1),
    # "take" and "bring" on their own are what every errand line uses ("should i take my
    # vitamins with food"), so these two need a word from the airport or the flight itself.
    # A lunch, a snack or a picnic carried onto a plane is the security question, not the
    # what-shall-i-have-for-lunch one: "can i take a packed lunch on a plane" was answered with
    # the five-minute packed lunch and "can i take my lunch on a plane" with the search hedge,
    # while "can i take sandwiches on a plane" had this row to itself.
    entry("flight-food", (("sandwiches", "food", "snacks", "snack", "packed lunch",
                           "packed lunches", "lunch", "lunches", "meal", "meals", "picnic",
                           "fruit", "crisps", "chocolate", "leftovers"), FLIGHT),
          FLIGHT_FOOD, bias=1),
    # "what are the liquid rules for hand luggage" was the science card for what a liquid is, so
    # the singular is keyed as well; it still needs a flight word, so "what is a liquid" stays.
    entry("flight-liquids", (("liquids", "liquid", "bottle", "water", "100ml", "100 ml",
                              "clear bag", "liquid rules"), FLIGHT), FLIGHT_LIQUIDS, bias=1),
    # A follow-up in a flight thread names no flight word itself ("can i take my own
    # sandwiches?"); it answers only when the turn before was about a flight, and passes on
    # the same words anywhere else, which is the gym, work or a picnic.
    entry("flight-food-followup", (("sandwiches", "snacks"), ("take", "bring", "own", "allowed")),
          _flight_followup(FLIGHT_FOOD), bias=-2),
    entry("flight-liquids-followup", (("liquids", "bottle", "water", "drink"),
                                      ("take", "bring", "own", "allowed")),
          _flight_followup(FLIGHT_LIQUIDS), bias=-2),
    entry("flight-nervous", (("never", "first time", "nervous", "scared"), ("flown", "flying",
                                                                           "flight", "plane")),
          ("It's genuinely a safe way to travel, and the first flight is mostly boring: check in, "
           "security, wait, board, sit. Tell the cabin crew it's your first time if you're "
           "nervous; they're used to it and always look after you.")),
    entry("plane-recline", (("recline", "reclining"), ("seat", "plane", "ok", "rude", "ever")),
          ("Leaning back is fine and nobody thinks worse of you, but do it slowly and check behind "
           "you, because it can land on someone's laptop. Avoid mealtimes if you can, and don't "
           "keep it back for the whole flight in the front row of economy.")),
    # "is it worth paying for priority boarding" was the money overpay answer, and extra legroom
    # the same, because "worth" plus "extra" is that entry's shape. Which extra is named decides
    # the answer, so one card holds all three and reads the line.
    entry("flight-extras",
          (("priority boarding", "priority boarding pass", "speedy boarding", "extra legroom",
            "legroom", "seat selection", "choose my seat", "pick my seat", "pay for a seat",
            "exit row", "extra leg room"),
           ("worth", "worth it", "pay", "paying", "paid", "extra", "should i", "is it", "buy")),
          _flight_extras, bias=1,
          avoid=("refund", "cancel", "compensation", "delay", "delayed", "lost", "hotel",
                 "car hire", "hire car", "insurance", "lounge", "fast track", "fast-track")),
    # The comfort of a long flight is the other half of a flight question, and "how do i survive a
    # long flight" reached nothing at all while the cheap-fares row took "tips for a long flight".
    # Keyed on the length of the flight itself, so the fares row keeps "cheap flights".
    entry("long-flight", (("long flight", "long flights", "10 hour flight",
                           "12 hour flight", "twelve hour flight", "fourteen hour flight",
                           "overnight flight", "night flight", "8 hour flight",
                           "how do i survive the flight", "survive a flight",
                           "comfortable flight", "flight comfortable"),
                          # The second part is the *other* signal, never the word the first
                          # part already holds: "flight" and "plane" here meant one token
                          # satisfied both parts, so the row took every line that mentioned a
                          # long flight - "what should i wear on a long flight" and "is a long
                          # flight bad for you" were answered with water, walking and socks,
                          # which is not what either asked.
                          ("how", "tips", "advice", "make", "get through", "survive", "cope",
                           "comfortable", "better",
                           # "what can i do on an 8 hour flight" is the same question as "how
                           # do i get through an 8 hour flight", said in the other shape
                           "what can i do", "what to do", "what do i do", "pass the time",
                           "keep busy", "keep occupied", "entertain", "keep a child busy",
                           "keep the kids busy")),
          "Book the seat you can sleep in if it is overnight, then treat it as a day with no work "
          "in it: water instead of the wine, a proper meal before you board rather than the tray, "
          "and stand up every couple of hours to walk to the back. Compression socks and shoes "
          "with room in them are worth more than any gadget; an eye mask, earplugs and a spare "
          "toothbrush turn the last three hours into a rest. Put a change of clothes, your "
          "medicines and a charger in the bag under the seat, and set your watch to the new time "
          "when you board.",
          # a swollen leg on a flight is a circulation question with its own answer, a fear of
          # flying is another, and the fares row is the other half of the shopping question
          avoid=("cheap", "cheapest", "cheaper", "fares", "price", "prices", "deal", "deals",
                 "book", "booking", "swollen", "swelling", "clot", "dvt", "calf", "leg pain",
                 "afraid", "scared", "fear of flying", "panic", "anxious", "turbulence",
                 "delayed", "delay", "cancelled", "compensation", "jet lag", "snore",
                 "baby", "toddler", "child", "kids", "dog", "pet", "luggage lost", "lost bag",
                 # what to wear or pack is a packing question, and whether flying is bad for you
                 # is a health one: neither is answered by the seat-and-water advice
                 "wear", "wearing", "clothes", "clothing", "pack", "packing", "take", "bring",
                 "luggage", "bad for you", "bad for me", "healthy", "unhealthy", "safe",
                 "dangerous", "pregnant", "pregnancy", "dvt risk",
                 # sleeping on a long flight has its own answer (set the watch, sleep to the
                 # new time) and this card mentions sleep only in passing, so the act of
                 # sleeping stands it down
                 "how do i sleep", "sleep on a", "sleep on the", "get to sleep", "fall asleep"),
          bias=1),
    entry("flight-tips", (("cheap", "cheapest", "tips"), ("flights", "flight", "flying")),
          ("Be flexible on dates and airports and book eight to six weeks ahead for Europe, longer "
           "for long-haul. Tuesday and Wednesday flights are usually cheapest, and luggage fees "
           "often close the gap between budget and full-service airlines.")),
    # "railcard" is the word people use for the card, so it is in the key: "is it worth getting a
    # railcard" has no other rail word in it at all.
    entry("cheap-trains", (("train", "trains", "rail", "railcard", "railcards", "rail card"),
                           ("cheap", "cheaper", "cheapest", "advance", "early", "book", "ticket",
                            "tickets", "save", "worth", "get", "pay", "pays", "much", "cost",
                            "costs")),
          _cheap_trains,
          avoid=("toy", "toys", "set", "sets", "model", "models", "wooden", "gym", "exercise",
                 "workout", "trainer", "trainers", "at home",
                 # "train" is a verb as well as a thing: how much to train a week or a month is
                 # practice, and a fares answer says nothing about it.
                 "train a week", "train a month", "train each week", "train every week",
                 "train twice", "train three", "train four", "how much should i train",
                 "how often should i train", "how many times a week should i train",
                 "run a week", "run each week", "run every week",
                 # "I need a book for the train" is a reading question, not a fares one.
                 "a book for", "book for the", "books for the", "something to read", "reading",
                 # "taxi or the train" is a choice between two ways of getting there.
                 "or the train", "or a train", "or the bus", "or a bus", "or the coach",
                 "or a coach", "or drive", "or park", "or walk", "or cycle",
                 # a refund, a cancelled train or a late one is train-refund's question, and
                 # "how do i get a refund for a train ticket" was getting the cheap-fares answer
                 "refund", "refunds", "money back", "delay repay", "cancelled", "canceled",
                 "delayed", "compensation")),
    entry("passport-lost", ("passport", ("lost", "lose", "losing", "stolen", "missing", "left")),
          _passport_lost, bias=1,
          # Left at home or in a hotel is not lost: the police-report answer is for a passport
          # that is gone, so those shapes pass instead of being told to go to an embassy.
          # "left" also means time left on it, which is the passport-valid entry below.
          avoid=("at home", "in my bag", "in my other", "back at", "in the hotel", "at the hotel",
                 "before i fly", "left it at",
                 "months left", "weeks left", "days left", "left on it", "valid", "expires",
                 "expiring", "runs out", "six months", "enough time")),
    # A passport left behind is not lost and not an emergency: it is a booking to save.
    entry("passport-left-behind", ("passport", ("at home", "forgot", "forgotten", "left it",
                                                "in the hotel", "at the hotel", "back at",
                                                "left behind", "on the kitchen table")),
          ("Tell the airline desk as soon as you know - the booking is still yours, so they can "
           "usually move you to a later flight, and someone can bring the passport to the airport "
           "if there is time. If it is at a hotel, ask them to hold it and courier it to you; a "
           "photo of it will not get you through security.")),
    entry("passport-valid", ("passport", ("valid", "still valid", "valid for", "six months",
                                          "enough time", "months left", "weeks left", "runs out",
                                          "expires", "expiring", "fly", "travel in",
                                          # the same question counted in days, and asked as what
                                          # you can travel with: "can i travel with 10 days left on
                                          # my passport" reached no row at all and got a punt about
                                          # the council's rules
                                          "days left", "days to go", "weeks to go",
                                          "travel with", "travel on", "fly with", "get in on")),
          ("Most countries want six months left on your passport beyond the day you plan to "
           "return, and some also want it issued within the last ten years. Check your "
           "destination's rule on its embassy site before you book: if you are close to the "
           "line, renew first rather than risk being turned away at the airport."),
          # a passport that has already run out is a renewal, not the six-month rule: "my passport
          # has expired" was answered with what other countries want on arrival.
          # a passport that has already gone is a renewal, not the six-month rule: "my passport
          # has expired" was answered with what other countries want on arrival. One that runs
          # out later stays here, because that line is about the trip.
          # the rule is the answer to a line that says how long is left, so the verdict for that
          # line goes in front of it - see `_the_passport_verdict`
          lead=("yesno", _the_passport_verdict),
          avoid=("lost", "stolen", "missing", "renew", "how long",
                 "expired", "has expired", "ran out", "out of date")),
    # Where to keep it while nothing has gone wrong is a fourth question: the three above answer
    # a passport that is lost, left behind or about to expire. "how do i keep my passport safe
    # when travelling" was reaching the older person's bus pass, on "pass" and "travel".
    entry("passport-safe",
          (("passport", "passports", "travel documents", "id card"),
           ("safe", "keep it safe", "keep safe", "keep my passport", "keep it",
            "where should i keep", "where to keep", "where do i keep", "carry", "on me",
            "inside pocket", "money belt", "beach", "pickpocket", "pickpockets",
            "hotel safe", "with me", "protect")),
          ("Carry it on you, in a zipped inside pocket or a money belt, and not in a back pocket or "
           "an open beach bag. Put a photo of the ID page in your own email: it makes a replacement "
           "far quicker and it costs nothing. A hotel safe is fine while you are in the room, but "
           "keep the passport with you on travel days. If it is taken, report it to the police and "
           "go to your embassy for an emergency travel document."),
          # a passport that has gone, is out of date or is left behind has its own entry
          avoid=("lost", "lose", "losing", "stolen", "missing", "left", "forgot",
                 "forgotten", "valid", "expires", "expiring", "runs out", "renew",
                 "renewal", "apply", "how long", "how much", "visa", "photo booth",
                 "change my name", "child", "baby")),

    # --- trips and packing -------------------------------------------------------
    # A suitcase that comes back broken is the airport's handling, not the packing: "how do i
    # protect my suitcase when flying" was answered with the fruit-fly trap, on "protect" and
    # "fly", and "how do i stop a suitcase zip bursting" with the computer unzip answer.
    entry("suitcase-protect",
          (("suitcase", "suitcases", "luggage", "baggage", "checked bag", "checked luggage",
            "hold bag", "holdall", "hold luggage"),
           ("protect", "damaged", "damage", "burst", "bursting", "bursts", "zip", "zips",
            "zipper", "strap", "cracked", "broken", "scratched", "wheel", "wheels",
            "thrown about", "rough handling", "airline broke", "came back broken",
            # one alternative per key part scores, so the zip phrases are spelled out: "zip"
            # alone ties with the computer unzip card, which carries a bias
            "zip bursting", "zip burst", "zip broke", "zip broken", "zip split",
            "replacement wheels", "lost wheel", "broken wheel")),
          # a case that has already broken is a claim, not a packing tip: the function reads
          # which of the two the line is
          _suitcase_protect,
          # a computer zip, a packing list and a bag that never arrived are other questions
          avoid=("zip file", "file", "files", "folder", "computer", "laptop", "password",
                 "pack", "packing", "what should i pack", "what to pack", "lost", "missing",
                 "never arrived", "delayed", "delayed flight", "tracker", "airtag",
                 "hand luggage", "carry on", "carry-on"),
          bias=1),

    entry("packing-a-car-journey",
          # "what should i take on a long car journey" was the search shrug: the packing entries
          # are keyed on a weekend and a week, and neither of them is how a drive is asked about.
          (("what should i take", "what do i take", "what should i pack", "what do i pack",
            "what do i need", "what should i bring", "what do i bring", "pack", "packing",
            "take with me", "bring with me"),
           ("car journey", "car trip", "long drive", "long car journey", "long journey",
            "drive down", "driving down", "in the car", "motorway", "driving holiday")),
          "Water and snacks that do not crumble, so nobody is eating crumbs at 70mph: a refillable "
          "bottle each, fruit, and something savoury in a tub. Then a phone cable and a power bank, "
          "the breakdown and insurance details, a blanket or a spare layer each, wet wipes and a "
          "bag for rubbish, sunglasses, and cash or a card for parking and toilets. Plan a stop "
          "every two hours, and put the first night's bag where you can reach it.",
          # a weekend, a week, a flight and a move are other entries, and a car that will not
          # start is the cars domain's question
          avoid=("weekend", "two nights", "three nights", "week away", "a week", "fortnight",
                 "flight", "flying", "plane", "airport", "hand luggage", "carry on", "carry-on",
                 "cabin bag", "moving house", "move house", "removal", "won't start", "wont start",
                 "battery", "flat tyre", "puncture", "overheat", "breakdown cover cost")),
    entry("packing-a-flight",
          # "what do i take to the airport" and "what should i take on a plane" were the shrug,
          # and "what should i pack for a flight" reached the food you carry to a picnic. The
          # rules of hand luggage are the baggage entry's; this is the list for the bag.
          (("what should i take", "what do i take", "what should i pack", "what do i pack",
            "what do i need", "what should i bring", "what do i bring", "pack", "packing",
            "take with me", "bring with me", "forgot to pack"),
           ("flight", "plane", "airport", "flying", "long flight", "flight bag", "holiday flight")),
          "Passport, the boarding pass on the phone and a screenshot of it, because the airport "
          "wifi is not a plan. Chargers and a power bank go in the cabin bag, not the hold, and so "
          "do medicines in their original boxes with the repeat slip. Liquids are 100ml each in "
          "one clear bag; a spare layer, an empty bottle to fill after security and a snack get "
          "you through a delay. Put one change of clothes in the cabin bag in case the suitcase "
          "takes a later flight.",
          # the baggage rules own the size and the allowances, and a car, a train and a week are
          # separate lists
          avoid=("hand luggage", "carry on", "carry-on", "cabin bag", "allowance", "how many ml",
                 "100ml", "liquid rules", "how much does", "car", "car journey", "long drive",
                 "week", "weekend", "train", "ferry", "moving house")),
    # A named city is a short trip with a climate, so the list is this one: "what should i pack for
    # lisbon" had no weekend word in it and reached nothing at all, while the nappy bag row's bare
    # "what should i pack" was answering it with four or five nappies.
    entry("packing-weekend", (("pack", "packing"),
                              ("weekend", "trip", "break", "days", "city") + tuple(CITIES)),
          ("For two or three nights: one change of clothes plus a layer, one pair of comfortable "
           "walking shoes, toiletries in a bag, phone charger and any tickets. Roll clothes to fit "
           "more in, and leave the \"just in case\" outfit at home."),
          # A weekend away is not a move: "no idea where to begin the packing" for a house move
          # was answered with this travel list, because it names a weekend and packing.
          # And "how do i pack plates so they dont break" is a box of crockery, not a suitcase.
          avoid=("house", "moving", "move", "moved", "flat", "home", "boxes", "removals",
                 "plates", "crockery", "mugs", "fragile",
                 # "i smoke a pack a day and cant stop" is a packet of cigarettes, and the
                 # suitcase list was answering it: a smoking line never wants a packing list
                 "smoke", "smoked", "smoker", "smokers", "smoking", "cigarette", "cigarettes",
                 "cigs", "nicotine", "vape", "vaping")),
    entry("packing-week", (("pack", "packing", "suitcase", "what should i take",
                            "what do i take", "what should i bring", "what do i bring"),
                           ("week", "week away", "a week", "two weeks", "10 days", "ten days",
                            "fortnight", "days away", "long trip", "holiday")),
          ("For a week: five tops, three bottoms, two layers, one pair of shoes you can walk in "
           "and one smarter pair, plus a waterproof, swimwear if there is water, chargers and any "
           "tickets. Plan to wash once on day three or four - a hostel or a launderette - and you "
           "can halve the clothes. Roll everything, put the first night's things on top, and "
           "leave the \"just in case\" outfit at home."),
          # a cold city, a warm beach, a weekend, a carry-on and children are their own entries,
          # and "pack for a week" must not take them
          avoid=("cold", "snow", "ski", "skiing", "winter", "december", "january", "february",
                 "november", "march", "hand luggage", "carry on", "carry-on", "cabin bag",
                 "weekend", "two nights", "three nights", "baby", "toddler", "kids", "children",
                 "wedding", "funeral", "interview", "dress code", "party", "work", "office",
                 "spain", "italy", "greece", "portugal", "turkey", "croatia", "france",
                 "canaries", "mallorca", "sicily", "cyprus", "malta", "summer", "beach", "sun",
                 "hot", "warm", "moving", "move", "house", "plates", "crockery", "hospital",
                 "medicine", "medication", "insulin", "inhaler", "epipen", "tablets",
                 # a cold country is usually named rather than called cold: "a week in iceland"
                 # was getting the generic week list when pack-cool-country has the better
                 # answer. Only the places that entry actually names, so a line it cannot answer
                 # keeps the week list rather than falling through to a shrug.
                 "scotland", "scottish", "edinburgh", "glasgow", "highlands", "iceland",
                 "reykjavik", "norway", "oslo", "sweden", "stockholm", "finland", "helsinki",
                 "ireland", "dublin", "denmark", "copenhagen", "greenland", "faroe", "wales",
                 "snowdonia")),

    # A drink that has to stay cold is a cool bag, and it had no row at all: "how do i keep my
    # drink cold" and "how do i keep drinks cold" were both a shrug, and "how do i keep my beer
    # cold" went to the beer shelf-life answer, which is months in the fridge and nothing about
    # the car, the picnic or the beach. The cold pack and the pre-chill are what people miss.
    entry("keep-drinks-cold",
          (("drinks", "a drink", "my drink", "the drink", "water", "water bottle", "bottle",
            "bottles", "a can", "the can", "cans", "juice", "fizzy", "cola", "lemonade", "beer", "wine",
            # "keep it cold" names the drink without naming it, which is how a follow-up in a
            # drinks chat arrives ("can you keep it cold", "can i keep it cold overnight"). The
            # bare "can" that used to do that job was the line's own question word as often as
            # not, so the phrase is the subject here and the question word is left alone.
            "keep it cold", "keep them cold", "keep it cool", "keep them cool",
            "keep it chilled", "keep it cold overnight",
            "white wine", "rose", "prosecco", "cool bag", "cool box", "cooler", "flask"),
           ("cold", "cool", "chill", "chilled", "icing", "ice", "ice pack", "ice block",
            "cooler", "picnic", "beach", "car", "car journey", "journey", "day out", "party",
            "barbecue", "bbq", "hot day", "heatwave", "summer", "warm", "travel",
            # "how do i keep my water cold" was the dry-eye row: "keep" and "water" are both
            # in its key, and the two entries tied, so the registry's order decided it. The
            # phrase is what says which of the two the line is about.
            "water cold", "water stays cold", "water cool", "keep water cold",
            "keep my water cold", "cold water bottle", "on a walk", "long walk", "hike")),
          _cold_drinks,
          # "what is the best way to keep drinks cold in the car" was reaching split-bill on
          # "way" and "drinks", so this row has to win the tie rather than draw it. The third
          # point is for the eyes: "how do i keep my water cold" ties with dry-eye on the words
          # ("keep" and "water" are in its key) and a flask is the likelier reading.
          bias=3,
          ask=("how", "what", "best", "keep", "stay", "stop", "make", "get", "should", "can i",
               "tips", "advice", "way"),
          # A cold food is not a cold drink: "what can i do with cold rice" reached this row on
          # "cold" and got the cool bag, which is no answer to a bowl of leftover rice. Only the
          # words that say the food is already cooked and left over stand the row down, so a
          # picnic line that names a food ("keep the chicken cold in the car") keeps the cool bag.
          # a drink that has gone off, a fridge that will not get cold, and a baby's bottle are
          # their own questions, and how long a thing keeps is the shelf life, not the cool bag
          avoid=("cold rice", "cold pizza", "cold chicken", "cold pasta", "cold potatoes",
                 "cold noodles", "cold soup", "cold curry", "leftover", "leftovers",
                 "left over", "left in the fridge", "from last night", "yesterdays",
                 "gone off", "gone bad", "out of date", "expire", "expiry", "sell by", "use by",
                 # a heating thing that "keeps going cold" is the heating's own question, not a
                 # drink to chill: on main "my hot water keeps going cold" got "Chill it in the
                 # fridge first, then a cool bag or box with a frozen ice block"
                 "radiator", "radiators", "heating", "central heating", "boiler", "hot water",
                 "hot tap", "hot taps", "thermostat", "immersion", "towel rail",
                 # a line that names the box is answered by home.py's cool-box-cold, which is
                 # the long answer about freezing the bottles and filling the empty space
                 "cool box", "coolbox", "cooler box", "cool bag", "cooler bag", "chiller bag",
                 "chiller box", "picnic bag", "picnic box", "ice box",
                 # "warm" is this row's word because a drink that has to stay cold is asked about
                 # in a warm car, and the bare word took a person who is cold: "i cant get warm"
                 # was told to chill a drink in the fridge. A body warming up is not a drink.
                 "get warm", "getting warm", "to get warm", "cant get warm", "can't get warm",
                 "never warm", "feel cold", "feeling cold", "im cold", "i am cold", "so cold",
                 "shivering", "freezing", "keep warm", "stay warm", "warm up", "warming up",
                 "hands are cold", "feet are cold", "cold hands", "cold feet",
                 # "best water bottle for a hike" is a shopping question, not a cool-bag one:
                 # the answer to it is which bottle to buy, and this row can only say how to
                 # chill a drink the person already has.
                 "best water bottle", "best bottle", "buy", "buying", "recommend",
                 "recommendation",
                 "off milk", "sour", "smells", "fridge not cold", "not cold enough", "freezer",
                 "freeze the", "can i freeze", "milk", "formula", "breast milk", "baby",
                 "how long does", "how long can", "how long will",
                 # how much to drink is a quantity, and this row can only say how to keep a drink
                 # cold: "how much water should i take on a hike" got the cool bag and a bag of
                 # ice while the day-out row held "half a litre an hour of walking". The
                 # quantity words stand this row down so the row that carries a figure answers.
                 "how much water", "how much should i drink", "how much to drink",
                 "how much liquid", "how many litres", "how many liters", "how much do i drink",
                 # a warm fridge full of ruined food is a claim, not a picnic: "fridge is warm
                 # and everything inside is ruined can i claim" reached this row on "can" (a can
                 # of drink) and "warm", and answered it with a cool bag and a bag of ice.
                 "ruin", "ruined", "claim", "claims", "refund", "money back", "compensat",
                 "who pays", "insurance", "insured", "wasted", "spoiled", "spoilt", "thawed",
                 "power cut", "power went off", "everything inside", "all the food",
                 # "car" is in the key for the car journey, and "can i" and "get" are ask words,
                 # so "can i haggle on a new car" was a cool bag and a bag of ice: buying a car
                 # is a price question, not a drink that has to stay cold.
                 "haggle", "haggling", "bargain", "bargaining", "negotiate", "negotiating",
                 "money off", "discount", "discounts", "new car", "new cars", "buy a car",
                 "buying a car", "car finance", "test drive", "dealer", "dealership",
                 "for sale", "price", "prices", "salesperson", "sales target",
                 # "can" is a modal verb far more often than it is a tin: "can i travel with 2
                 # months left on my passport" was answered with the cool bag, on "can" and
                 # "travel". A passport is never a drink.
                 "passport", "passports", "visa", "boarding pass",
                 # and neither is a car that will not start: "can i drive it" with a dead battery
                 # on the table was the cool bag and a frozen ice block, on "can" and "car". The
                 # words are the driving ones, not "car" alone, so a cold-drink question about a
                 # car journey still gets its answer.
                 "drive it", "drive my car", "drive the car", "can i drive", "drive home",
                 "wont start", "won't start", "not starting", "overheating", "overheated",
                 "breakdown", "broken down", "flat battery", "smoke", "steam",
                 # "can" is a modal verb far more often than it is a tin, and "can i run with a
                 # cold" was a cool bag and a bag of ice, so anything done with a body in it
                 # stands this row down and leaves it to the exercise answer
                 "run", "running", "jog", "jogging", "exercise", "gym", "train", "training",
                 "work out", "workout", "swim", "swimming", "cycle", "cycling", "football",
                 "play", "playing", "sick", "ill", "illness", "fever", "temperature",
                 # "cold water" is in this row's key and a wash line says it too, so "can i use
                 # fabric softener in cold water" was answered with the cool bag and a bag of
                 # ice. A drink is never the answer to a line about the wash, so the laundry
                 # words stand this row down and the softener row in cleaning.py answers it.
                 "fabric softener", "fabric conditioner", "softener", "conditioner",
                 "laundry", "washing machine", "washing", "wash", "clothes", "towels")),

    # A night under canvas is its own list: "what do i need to take camping" reached the
    # before-you-go checklist and got a passport and insurance, and "what should i pack for
    # camping" got a shrug. The tent, the mat and the torch are what people forget, so they come
    # first; the site's rules are the one thing to check before leaving.
    entry("camping-kit", (("camping", "campsite", "camp site", "wild camp", "wild camping",
                           "tent", "under canvas"),
                          ("pack", "packing", "need", "take", "taking", "bring", "gear", "kit",
                           "list", "first time", "what should i", "what do i")),
          ("Tent with its pegs and a mallet, a sleeping bag and a mat - a foam or inflatable one, "
           "not just the tent floor - a head torch, a stove with fuel and a lighter, and a water "
           "container. Take warm layers and a waterproof even in summer, boots you can walk in, "
           "bin bags, a small first-aid kit with blister plasters, and food in a cool box. Book "
           "the pitch ahead and check the site's rules on fires, dogs and arrival time."),
          bias=1, guard=_not_a_food_to_carry,
          # A day hike, a festival and a beach are packed for by their own entries, and a tent
          # in the garden is not a trip.
          avoid=("day hike", "hiking", "walk", "walking", "festival", "beach", "garden",
                 "back garden", "backyard", "kids", "children", "toddler", "baby")),

    # Camping with small children is not the kit list with a child's sleeping bag added, and the
    # row above stands itself down the moment a child is named, so "we are camping in july and the
    # kids are 4 and 6, what should we pack" reached nothing and got "I don't know enough to
    # answer that honestly". What a parent needs to know is the three things that stop a small
    # child's night going wrong, which is why this row keys on the children and the packing
    # together. A pitch that leaks, a broken pole and the price of a site are all other answers.
    entry("camping-with-kids",
          (("camping", "campsite", "camp site", "tent", "under canvas"),
           ("kids", "children", "childs", "child's", "child", "toddler", "toddlers", "baby",
            "babies", "family", "son", "daughter", "boys", "girls", "little ones",
            # The people who take children camping are often not their parents, and a grandparent
            # asks the same question in their own words: "taking the grandchildren camping, what
            # do we need" was the plain kit list for two adults, because no word in it named a
            # child. "kid", "boy" and "girl" are the same gap one size smaller.
            "kid", "boy", "girl", "grandchildren", "grandchild", "grandkids", "grandson",
            "granddaughter", "niece", "nephew", "teen", "teens", "teenager", "teenagers")),
          ("A tent and bags for everyone, plus what small children need on a campsite: a mat each, "
           "because they feel every root, warm layers and a hat for the night even in July, and a "
           "full change of clothes kept in the car so a wet sleeping bag is not the end of the "
           "trip. Take a torch each, wet wipes, a bin bag for wet things, breakfast that needs no "
           "cooking, and something to do after dark. Pitch in daylight, close to the toilets but "
           "not beside them, and let them run about before bed so they sleep."),
          ask=("pack", "packing", "need", "take", "taking", "bring", "gear", "kit", "list",
               "what should i", "what do i", "what to bring", "first time"),
          # a "week" and a "trip" are words the money rows and the weekend list also hold, and a
          # toddler brings the first-food rows out, so this row stands ahead of them all.
          bias=2,
          avoid=("hole", "holes", "leak", "leaking", "pole", "poles", "broke", "broken",
                 "repair", "fix", "book", "booking", "price", "cost", "how much", "where",
                 "dog", "dogs", "pitch up", "won't go up", "wont go up")),

    # A family under canvas is the same trip with a different list, and the row above stands down
    # for the child words, so this one takes it: "im going camping with the kids next month and it
    # might rain, what should i pack" was answered with what to feed a baby by age. The adult kit
    # is assumed; what a parent forgets is the second set of clothes and the wipes.
    entry("camping-with-children",
          (("camping", "campsite", "camp site", "wild camp", "wild camping", "tent",
            "under canvas"),
           ("pack", "packing", "need", "take", "taking", "bring", "kit", "gear", "list",
            "what should i", "what do i", "what do we")),
          ("Tent, sleeping bags and mats for everyone, a torch each so nobody is in the dark "
           "alone, and one full change of clothes per child per day plus two spare sets: that is "
           "what wet weather costs. Add wellies and a waterproof, wipes and nappy bags, a sun hat "
           "and cream, snacks and a water bottle each, their own pillow or blanket, Calpol and "
           "plasters, and a bag for wet things. Pitch near the toilets, take a mallet, and put "
           "the tent up at home once before you go."),
          # the child is what makes it this list rather than the plain one: a key of more than
          # one group only has to reach its first, so the family is an `ask` and not a third part
          ask=("kids", "kid", "children", "child", "toddler", "baby", "family", "families", "son",
               "daughter", "boys", "girls", "with the kids", "with kids", "little ones"),
          bias=2,
          # a safety question about a baby is not a kit list, and a tent in the garden is not a
          # trip
          avoid=("safe", "safety", "is it ok", "ok to", "too cold", "too young", "months old",
                 "weeks old", "cry", "crying", "feed", "feeding", "bottle", "garden",
                 "back garden", "backyard", "festival", "beach")),

    # A festival has its own kit, and the ask is "what should i take" / "what do i need", so
    # "should i take a tent to a festival" (a yes/no about one thing) is not this list.
    entry("festival-kit", (("festival", "festivals", "glastonbury", "reading festival",
                            "download festival", "camping festival"),
                           ("pack", "packing", "need", "bring", "gear", "kit", "list",
                            "what should i take", "what do i take", "what to take")),
          ("Ticket and ID, some cash because card readers fail in fields, a small tent with its "
           "pegs and a mallet, a sleeping bag and mat, earplugs and a power bank. Wellies, a "
           "waterproof and warm layers for the nights, plus sun cream and a hat for the days, wet "
           "wipes, toilet roll, blister plasters and bin bags; leave glass at home. Pack so you "
           "can carry it from the car park, and put your name on the tent bag."),
          bias=1,
          # A day out is not a festival, and neither is a campsite with no music.
          avoid=("day trip", "day out", "kids", "children", "toddler", "baby", "garden")),

    entry("car-journey-kids", (("car", "drive", "journey", "plane", "flight", "train", "ferry",
                                "road trip", "long drive", "long journey", "long flight"),
                               ("kids", "children", "toddler", "baby", "child", "them",
                                "busy", "occupied", "entertained")),
          ("Leave at nap time or early if you can, plan a stop or a walk about every two hours, "
           "and pack snacks, water, sunshades and a tablet with films downloaded. A surprise bag "
           "of small new things to hand out one at a time is the trick for the last hour."),
          # "my kids are driving me mad" is about the children, not about a journey. Only the
          # phrase where a person has had enough: bare "mad" or "crazy" is on the journey lines
          # themselves ("the kids go crazy on long car journeys").
          avoid=("driving me mad", "drive me mad", "drives me mad", "drive you mad",
                 "driving me crazy", "drive me crazy", "driving me up the wall",
                 "drive me up the wall", "drives me up the wall", "driving me insane",
                 "driving us mad", "drives us mad")),
    entry("car-sick", (("car", "motion"), ("sick", "sickness", "nausea", "dizzy", "vomit")),
          "Sit in the front seat, look at the horizon rather than a screen, and keep the air cool with the window down a little. Eat something plain beforehand, and stop for ten minutes if you feel bad.",
    ),
    # A country named with the plug question is one fact about that country: a table, so the same
    # question about thirty countries does not go to search.
    # "Where should we stay" with no city in it is about the city the last turn named, so the
    # shape alone is the key and the callable needs the city from memory.
    entry("where-to-stay-there", (("where should we stay", "where should i stay", "where do i stay",
                                   "where to stay", "best place to stay", "where shall we stay"),
                                  ("stay", "sleep", "sleeping", "hotel", "area", "neighbourhood",
                                   "neighborhood", "part of town")),
          _where_to_stay, bias=1),
    entry("where-to-stay", (WHERE_TO_STAY,
                            tuple(CITY_AREA) + ("there", "that city", "the city", "this city")),
          _where_to_stay,
          # "what area should i stay in in london" was answered by the card for an evening at
          # home, because "stay in" is in both lines and the evening card keys the word "what".
          # "where should i stay on a tight budget in lisbon" went to the card that splits a
          # monthly wage: the city is the subject, the budget is how.
          bias=2),
    # The same question about a town that has no card: the rules of picking a spot hold anywhere,
    # and a hedge is no use to somebody booking a weekend in Skegness.
    entry("where-to-stay-anywhere", (WHERE_TO_STAY,
                                     ("stay", "staying", "hotel", "hotels", "hostel", "b&b",
                                      "guest house", "caravan", "area", "town", "village",
                                      "seaside", "coast", "beach", "district", "in", "near",
                                      "somewhere", "accommodation",
                                      # the word people use for a night's stay when they are
                                      # not booking one: "where should i sleep", "where can i kip"
                                      "sleep", "sleeping", "kip", "crash")),
          _a_town_stay,
          # "where should i stay on a budget" was answered by the card that splits a monthly
          # wage, because "budget" is the loudest word in the line and the money row keys it.
          # Two is enough to put the booking back in front of a card about a wage.
          bias=3, guard=_a_town_stay_line,
          # a night in a hospital, a friend's spare room and a stop on a drive are not a booking
          avoid=("hospital", "ward", "sister", "brother", "mum", "dad", "mother", "father",
                 "friend", "friends", "relative", "in laws", "funeral", "wedding", "work",
                 "office", "airport", "stopover", "layby", "service station", "prison",
                 "uni", "university", "student", "hostel dorm")),
    # A night before an early flight is its own booking: the airport hotel with the shuttle, the
    # town a couple of stops away, or the car park with the transfer included. The general stay
    # paragraph stands down when the line says airport, so without this row the question of the
    # night before a flight reached nothing but a hedge.
    entry("a-night-near-the-airport",
          (("airport", "airport hotel", "terminal", "departure", "departures", "check in desk",
            "heathrow", "gatwick", "stansted", "luton airport", "liverpool airport", "prestwick",
            "flight", "flights", "flying",
            "early flight", "early start", "dawn flight", "red eye"),
           ("stay", "staying", "night", "sleep", "hotel", "hotels", "accommodation", "book",
            "booking", "near", "before", "overnight", "stop over", "stopover")),
          "For a night before an early flight, book an airport hotel with a shuttle and check the "
          "first and last shuttle times before you pay - a 4am shuttle that stops at 11pm is the "
          "usual trap, and so is a \"5 minutes from the terminal\" that is five minutes by car "
          "on a road with no pavement. A town two or three stops away on the train, or a "
          "park-and-fly with the transfer included, is usually about half the price; add up the "
          "transfer, the parking and the extra hour and pick on the total. Take the flexible rate "
          "if the flight is early, and get the shuttle time in writing.",
          bias=2, guard=_a_night_near_the_airport,
          # an airport is also where people complain about security queues, lost bags and the
          # price of a coffee, and none of those is a booking
          avoid=("queue", "queues", "security", "liquids", "laptop", "duty free", "lost",
                 "delayed", "delay", "cancelled", "cancel", "compensation", "baggage",
                 "hand luggage", "food", "eat", "coffee", "shops", "parking cost",
                 "how long", "what time", "get to", "get from", "transfer to")),

    entry("trip-essentials",
          (_ESSENTIALS_ASK,
           # a trip word, never a bare country: "do i need a jumper in mexico" is a packing
           # question and the country alone does not make it the paperwork list.
           ("trip", "holiday", "travel", "travelling", "going away", "time away", "abroad",
            "week away", "fly", "flying", "flight", "holidays",
            # "what do i need to sort out before i go to spain" names the going, not a country:
            # the going is what makes it a trip.
            "before i go", "before we go", "before i fly", "before we fly")),
          _trip_essentials,
          # A visa, a jab, a plug, a price or a packing list is its own question and keeps its own
          # row.
          bias=1,
          # "do i need travel insurance" is that question, and the row that names the GHIC card
          # answers it better than a general list.
          # A yellow card is the vaccination certificate and the row that names it answers better.
          avoid=("yellow card", "yellow fever", "certificate", "card",
                 "insurance", "cover", "ghic", "ehic",
                 "visa", "visas", "evisa", "esta", "etias", "entry requirements", "jab", "jabs",
                 "vaccine", "vaccines", "vaccination", "malaria", "yellow fever", "passport expired",
                 "passport expires", "renew", "renewing", "driving", "drive", "licence", "car hire",
                 "currency", "cash", "money", "cost", "costs", "cheap", "how much", "price",
                 "adapter", "adaptor", "plug", "plugs", "sockets", "charging", "pack", "packing",
                 "suitcase", "clothes", "wear", "bring", "take", "weather", "when to go",
                 "best time", "flight", "flights", "flying", "hotel", "hotels", "where to stay",
                 "house", "moving", "move", "moving house")),
    # The key is the plug and nothing else. "Same" and "different" were in it, and they are
    # comparison words: "is england the same as britain" was answered "England uses the same three
    # square pins as the UK, so what you bring from home fits", which is a confident answer to a
    # geography question. A plug question always names the plug - a socket, an adapter, a charger,
    # the voltage - so the comparison words are not needed here and belong to geography.
    entry("plug-country", (tuple(PLUG_TYPES),
                           ("adapter", "adaptor", "plug", "plugs", "socket", "sockets", "voltage",
                            "charger", "chargers")),
          _adapter, bias=1,
          # "how much cash should i take to turkey" is money: the plug words are the key, and
          # a bare "take" or "need" next to a country name is not one of them.
          avoid=("cash", "money", "currency", "spend", "budget", "much", "cost", "safe", "water",
                 "visa", "flight", "flights", "hotel", "train",
                 # which country is which is geography, and it names no plug at all
                 "difference between", "part of the uk", "british isles", "same as britain")),
    entry("travel-adapter", (("adapter", "plug", "sockets", "charger"),
                             ("europe", "abroad", "travel", "voltage", "uk", "italy", "france",
                              "spain", "greece", "portugal", "usa", "america")),
          ("Europe and many other countries use two round pins, the UK uses three square ones, and "
           "the US uses flat pins, so take a universal adapter. Check the voltage on your chargers: "
           "phone and laptop chargers handle 100-240V fine; hairdryers often don't.")),
    entry("travel-insurance", (("insurance", "travel insurance", "ehic", "ghic", "health card"),
                               ("travel", "abroad", "holiday", "trip", "worth", "get", "need",
                                # "what is the ghic card" names the card and nothing else, so the
                                # card words are the second half of the key; a bare "what is" is
                                # not, or every "what is <make> insurance" lands here
                                "card", "ghic", "ehic", "ghic card", "ehic card", "health card",
                                "what does the ghic", "what is the ghic", "what does the ehic",
                                "what is the ehic")),
          ("Take the free GHIC card for state healthcare in the EU and pair it with proper travel "
           "insurance: the card covers treatment, not getting you home. Buy insurance when you "
           "book so cancellation is included."),
          # "what insurance do i need for a car" matched insurance + need. Insurance on a car, a
          # pet, a phone or a house is its own question, and it is not about going abroad.
          # Whether to buy cover and how to claim on it are two different questions: this entry
          # answers the first, and a policy that will not pay out is a claim. "claim" is in the
          # keys of several money entries, so it is no longer a rare word and this entry was
          # winning those lines on the score alone.
          avoid=("car", "cars", "vehicle", "van", "motorbike", "driving", "drive", "pet", "pets",
                 "dog", "cat", "phone", "home", "house", "contents", "buildings", "boiler",
                 "life insurance", "breakdown", "dental", "business", "excess", "claim",
                 "claims", "renewal", "quote", "cheaper", "reduce the price",
                 # a national insurance number reached this because the line said "insurance"
                 # and "abroad", and it is not travel cover at all
                 "national insurance", "ni number", "insurance number",
                 "claimed", "claiming", "wont pay", "won't pay", "not paying",
                 "refused", "refuses", "rejected", "payout", "pay out",
                 "insurer", "wont cover", "won't cover")),
    entry("japan-rail-pass", (("rail pass", "jr pass"), ("japan", "worth", "need", "buy")),
          ("It's only worth it for long-distance trips: two or more shinkansen journeys make a "
           "7-day pass pay, but for Tokyo and Kyoto alone it usually doesn't. Buy it before you "
           "travel, and reserve seats for the busy holiday weeks.")),
    entry("japan-blossom", (("cherry blossom", "blossom", "sakura"), ("japan", "tokyo", "kyoto",
                                                                     "when", "season", "march")),
          ("Late March to early April, moving north as the season goes: Tokyo usually peaks around "
           "the end of March, Kyoto a few days later. Book accommodation months ahead, and be "
           "flexible, because a cold spring can delay it by a week or two."),
          avoid=("tree", "trees", "hedge", "hedgerow", "shrub", "bush", "plant", "flower",
                 "flowers", "white")),
    entry("edinburgh-winter", (("edinburgh",), ("december", "winter", "pack", "cold", "christmas")),
          ("Pack for 2 to 8C, wind and sideways rain: a waterproof coat, warm layers, and shoes "
           "you can walk up a hill in. It's dark by 4pm, so plan indoor things for the afternoon "
           "and take a torch for Arthur's Seat.")),

    # --- more everyday travel requests ---
    # "How do I pack a suitcase tightly" is not a question about kilos: the allowance row took it
    # because "pack" was one of the words that made it a question about the bag's limit, so
    # somebody asking how to fit a week into a case was told the cabin size. The two are
    # different rows now, and this one is the folding: it asks for the shape of the request -
    # "how do i pack", "tightly", "fit everything", "rucksack" - rather than the bag's name,
    # because the bag's name is what the allowance row is about.
    entry("pack-it-tight",
          (("pack", "packing", "packed", "fit", "squeeze", "cram"),
           ("tightly", "tight", "more in", "everything in", "fit everything", "fit it all",
            "no room", "rucksack", "backpack", "suitcase", "case", "hand luggage", "carry on",
            "holdall", "bag")),
          "Roll everything and stand the rolls on end like books on a shelf: a case is a box, and "
          "packing flat leaves a third of it empty. Shoes go heel to toe along the spine with "
          "socks and chargers inside them, the heavy end goes at the wheels, and whatever you "
          "might want out goes on top. In a rucksack the weight sits high and close to your back "
          "rather than at the bottom, with the waterproof and a change of clothes at the top. Wear "
          "the bulky shoes and the coat on the day.",
          ask=("how do i pack", "how to pack", "how do i fit", "how can i fit", "pack it",
               "pack more", "pack everything", "fit everything", "fit it all", "tightly", "tight",
               "squeeze", "cram", "in one bag", "rucksack", "backpack", "no room"),
          # a list of what to take is the packing-week rows' job, and "how do i pack light" is
          # its own card: this row is only the folding
          avoid=("for a week", "for two weeks", "for the weekend", "what should i", "how many",
                 "light", "list", "checklist",
                 # a bag for the hospital, a birth or a funeral is a list of what to take, and
                 # rolling a towel is not that question: those lines keep whatever they had
                 "hospital", "maternity", "labour", "labor bag", "birth", "funeral", "flight bag",
                 "school bag", "nappy bag", "diaper bag", "changing bag", "hospital bag"),
          bias=1),

    entry("packing-light", ("packing", "light", "carry", ("list")),
          ("Lay everything out and take half the clothes and twice the money: three tops, two "
           "bottoms, one warm layer and shoes you can walk in covers a week. Roll clothes, keep a "
           "change in your hand luggage, and buy anything you forget when you arrive.")),
    # "book" is a verb as well as a thing, and it is a form of the word "booking" too, so it
    # cannot be an "avoid": the ask gate asks for the words that make this a question about
    # fares ("when should i book flights for christmas" keeps its answer, "just booked flights
    # to Spain" is news and reaches nothing).
    # "how do i book a flight" had no answer of its own: it was reaching the football card in
    # sport.py, because "booked" matched "book" by prefix, and once that stopped it was a punt.
    # Booking is its own job - compare, then book with the airline, and know what the fees are
    # before paying - so it is its own row.
    # A ticket already bought is not a claim on the employer and not a fare to compare. The
    # expenses row keys "ticket" beside "train", so "i lost my train ticket", "can i change my
    # train ticket" and "is my train ticket valid on any train" were all told to check the
    # expense policy before spending, and a guard on that row now stands it down for them. What
    # is left is the ticket itself: lost, changed, or which train it is good for.
    entry("rail-ticket-help", (("train ticket", "train tickets", "rail ticket", "rail tickets",
                                "my ticket", "my train ticket", "advance ticket",
                                "off peak ticket", "return ticket", "single ticket",
                                "ticket", "tickets"),
                               ("lost", "lose", "losing", "left", "left it", "forgot",
                                "forgotten", "change", "changed", "changing", "amend", "amended",
                                "alter", "valid", "any train", "another train", "wrong train",
                                "missed", "earlier", "later", "different train", "print",
                                "printed", "phone", "mobile", "app", "e ticket", "eticket")),
          _a_ticket_already_bought,
          # a refund, a delay, a price and a claim belong to their own rows
          avoid=("refund", "refunds", "delay", "delayed", "cancel", "cancelled", "compensation",
                 "delay repay", "claim", "expenses", "receipt", "policy", "mileage", "price",
                 "prices", "cost", "cheap", "cheaper", "cheapest", "how much", "when do",
                 "go on sale", "book", "booking", "booked", "advance fare", "railcard",
                 "season ticket", "watch", "film", "cinema", "concert", "match", "parking",
                 "parking ticket", "speeding", "fine"),
          bias=1),

    # A ferry, a train and a coach are booked ahead of time, and none of them had an answer:
    # "do i need to book the ferry" was a punt, "should i book ahead for the ferry" was hedged
    # back at the person, and "do i need to book a train ticket" was the expenses-policy card
    # ("check the policy before you spend"), which is about claiming the money back afterwards.
    # The mode is read off the line, so one row answers every way of asking about a crossing, a
    # rail ticket or a coach seat.
    entry("book-a-journey", (JOURNEY_MODES + ("seat", "seats", "reservation"),
                             ("book", "booked", "booking", "reserve", "reservation",
                              "reservations", "seat", "seats", "ahead", "advance",
                              "in advance", "need to", "have to", "must i", "do i need",
                              "early", "now or", "turn up", "on the day",
                              # the moment the tickets go on sale is the same question: "when
                              # do train tickets go on sale" was the expenses-policy card, which
                              # is about claiming the money back
                              "on sale", "go on sale", "goes on sale", "when do", "when should",
                              "when can i", "how far",
                              # "how do i book a coach trip" is a booking question, and the
                              # packing row keys "coach trip" for the list of what to take: the
                              # phrase wins it back without touching that row.
                              "book a coach", "book coach", "book the coach", "book a train",
                              "book a ferry", "book the ferry", "book a ticket", "book tickets")),
          _book_a_journey,
          # a booked journey is news, and a fare, a delay or a packing list is another row
          avoid=("price", "prices", "cost", "how much", "much",
                 "delay", "delayed", "cancel", "cancelled", "missed", "refund", "pack",
                 "packing", "what should i take", "luggage", "suitcase", "already booked",
                 "ive booked", "i have booked", "we booked", "just booked",
                 # the reading sense of "book": a phrase, because a bare "books" folds onto
                 # this row's own "book" and would silence it
                 "book to read", "books to read", "what book", "which book", "reading",
                 "novel", "novels", "audiobook", "kindle",
                 # a table, a room and a taxi are booked an hour ahead and have their own rows
                 "table", "tables", "restaurant", "meal", "hotel", "room", "rooms", "taxi",
                 "haircut", "viewing", "appointment", "doctor", "dentist", "garage", "mot",
                 "parking",
                 # claiming the money back is the expenses row's question: "do i need receipts
                 # for a train ticket" was answered with how to book one until these words
                 # stood this row down
                 "receipt", "receipts", "claim", "claims", "claiming", "expense", "expenses",
                 "reimburse", "reimbursement", "tax back", "mileage"),
          bias=1),
    entry("book-a-flight",
          (("flight", "flights", "fly", "flying", "airfare", "airfares", "plane ticket"),
           ("book", "booked", "booking", "how do i book", "reserve", "buy", "purchase",
            "which site", "what site", "compare", "direct")),
          "Compare on a search site, then book on the airline's own site, because a booking agent's "
          "cheap fare usually costs more once its card fee and its no-changes rule are counted. "
          "Before you pay, add the baggage for each person and pick the seats: the headline fare "
          "often leaves both out, and that is where a cheap ticket stops being cheap. Pay by "
          "credit card if the fare is over £100, which gives you section 75 cover if the airline "
          "fails, and check every passenger's passport has six months left on it.",
          bias=1, guard=_the_booking_is_behind_them,
          # the cheapest time to book, the price of bags, the boarding clock and a delay are
          # other rows, and so is a flight already booked
          avoid=("cheap", "cheaper", "cheapest", "deal", "deals", "when to", "how early",
                 "how far ahead", "advance", "bag", "bags", "baggage", "luggage", "delay",
                 "delayed", "cancel", "cancelled", "boarding", "gate", "check in", "checkin",
                 "my flight", "our flight", "boarding pass", "missed", "change", "refund",
                 "seat", "seats", "legroom", "extra legroom", "jet lag", "jetlag",
                 "nervous", "scared", "afraid", "sick", "ill", "food", "liquids", "water",
                 "airport", "parking", "transfer", "passport", "visa", "insurance",
                 # a flight already booked is not a question about how to book one: "just booked
                 # flights to spain" is the person telling you their news and got the how-to
                 "just", "already",
                 # "what books are good for a flight" asks for reading, and "books" folds to
                 # "book": the flight row was answering it with the airline how-to
                 # "when should i book", "now or wait" and "ahead" ask about timing, and the
                 # advance-booking row answers all of them: a timing word stands this row down.
                 "when", "wait", "waiting", "now or", "best time", "cheapest time", "cheapest",
                 "how soon", "how long before", "ahead",
                 # "i want to book a flight to rome" reached the advance-booking card on main,
                 # and a wish to go somewhere is that card's question, not this how-to
                 "i want to", "i'd like to", "i would like to",
                 # a phrase holds a reading line out without the self-veto a bare "books" has:
                 # "books" folds to this row's own "book", and the whole row went silent. The
                 # two-word forms cannot fold onto it.
                 "what books", "which books", "good books for", "books for a flight",
                 "book to read", "books to read",
                 "read", "reading", "to read", "novel", "novels", "audiobook",
                 # not "books": a loose avoid matches the key word itself ("books" folds to
                 # "book"), and the whole flight row went silent. "what books are good for a
                 # flight" stays the honest punt it is on main; the reading rows do not reach
                 # it either.
                 )),
    entry("cheap-flights",
          (("flight", "flights", "fly", "flying", "airfare", "airfares", "plane ticket"),
           ("cheap", "cheaper", "cheapest", "book", "booking", "price", "prices", "deal",
            "deals", "much", "cost", "early", "advance", "ahead", "when")),
          ("Book six to eight weeks ahead for short-haul and two to four months for long-haul, and be "
           "flexible about the day: Tuesday and Wednesday are usually cheapest. Search one way at a "
           "time, and check the airport transfer before you commit to a bargain."),
          # "just booked flights to spain" is news, not a question about fares, so the entry
          # only answers once the line asks for a price or a good time to book.
          ask=("cheap", "cheaper", "cheapest", "cheaply", "when", "how early", "how far ahead",
               "price", "prices", "deal", "deals", "compare", "save", "cost", "much",
               "best time", "how far in advance", "advance"),
          # "when" alone is a loose ask, so "why do i always catch a cold when i fly" reached
          # the fares answer. Being ill, being frightened and being delayed are travel questions
          # but none of them is a fare, and each has its own entry.
          avoid=("sick", "ill", "illness", "cold", "colds", "flu", "covid", "germs", "catch",
                 "catching", "scared", "afraid", "nervous", "anxious", "panic", "turbulence",
                 "delay", "delayed", "cancel", "cancelled", "lost luggage", "legroom",
                 "jet lag", "jetlag", "travel sick", "travel sickness",
                 # "when is my flight" is the time of the flight they have booked, not how far
                 # ahead to book one, and the fares answer to it was an answer to another question.
                 "when is my flight", "when is our flight", "what time is my flight",
                 "what time is our flight", "what time do i fly", "when do i fly",
                 "what time am i flying", "when am i flying", "what time is the flight",
                 "when is the flight",
                 # The boarding clock is not a fare: "when does boarding start for a 6am flight"
                 # was told to book six to eight weeks ahead.
                 "boarding", "boards", "board the", "gate", "gates", "departure",
                 # "can i fly when pregnant" is the pregnancy row's question, not how far ahead
                 # to book: the fare card answered it with six to eight weeks
                 "pregnant", "pregnancy", "weeks pregnant", "trimester", "midwife", "due date",
                 # a cost shared between people is not a fare: "how do i split the cost of
                 # flights" was told to book six to eight weeks ahead
                 "split", "splitting", "share", "sharing", "halves", "who pays", "who owes",
                 "each pay", "chip in", "between us", "cost of the flights",
                 "cost of flights", "pay for the flights")),
    # A named region has its own answer (Africa's biggest country is Algeria, Europe's longest
    # river is the Volga), so the world record passes on those lines.
    # A region's river is its own: geography.region_extreme answers "the longest river in africa"
    # from the region table, and a region it has no fact for still passes rather than gets the Nile.
    entry("longest-river", ("longest", "river", "world"),
          region_extreme("river",
                         "The Nile, at about 6,650 km, is usually called the longest, with the "
                         "Amazon a close second and carrying far more water. Which one wins depends "
                         "on where you say the Amazon starts."),
          # The home islands now have their own rivers in geography's region table, so they are
          # not avoided any more; a named country the table has no fact for still passes.
          avoid=("china", "india",
                 "france", "italy", "spain", "germany", "egypt",
                 "how many rivers", "number of rivers", "count rivers",
                 # the longest bridge, tunnel and road are other records: the line said what it
                 # was longest of, and the Nile is the answer only to the longest river
                 "bridge", "bridges", "tunnel", "tunnels", "wall", "walls", "road", "roads",
                 "motorway", "motorways", "causeway", "pier", "piers", "coastline",
                 "border", "borders", "railway", "railways", "flight", "flights")),
    # The biggest country in a region is that region's own: geography.country_extreme answers the
    # continent the line names and leaves the Russia answer for the unqualified line.
    # "list the countries in africa by size" is the same record asked as a list: without "by size"
    # in the area group the line reached no entry at all and got a shrug.
    entry("biggest-country", ("country", "biggest", "area", ("largest", "world", "by size",
                                                             "by area", "size")),
          country_extreme("area", "Russia, at about 17 million square km, nearly twice the size of "
                                  "Canada in second place. China and the United States come next."),
          avoid=("uk", "britain", "england", "scotland", "wales", "ireland", "china", "india",
                 "france", "italy", "spain", "germany", "egypt",
                 "island", "islands", "lake", "lakes", "desert", "mountain", "river",
                 "ocean", "sea", "city", "continent", "continents",
                 # the biggest animal, bird or fish is a fact about the creature, not about a
                 # country: "whats the biggest animal in the world" reached Russia
                 "animal", "animals", "creature", "creatures", "whale", "elephant",
                 "bird", "fish", "shark", "dinosaur", "insect",
                 "how many countries", "number of countries",
                 "countries have", "countries with", "countries without",
                 # The end of the scale decides which row answers: "smallest country by area"
                 # names area as well, which tied with this row and handed the line the
                 # largest country in the world.
                 "smallest", "smallest by", "least", "fewest",
                 # Same for the measure: how many people live in a country is not its area.
                 "population", "populous", "people live", "most people")),
    entry("altitude-sickness", ("sickness", "altitude", "avoid", ("mountain")),
          ("Go up slowly: above 3,000m, sleep no more than 500m higher than the night before, and "
           "take a rest day every third day. Drink plenty, skip alcohol, and if you get a bad "
           "headache with nausea, go down rather than waiting it out.")),
    entry("driving-abroad", ("driving", "abroad", "permit", ("europe", "international")),
          ("You need your licence, insurance and usually a warning triangle, hi-vis vest and "
           "breathalyser kit; check whether your insurer covers abroad or you need a green card. An "
           "international driving permit costs a few pounds and is worth having in some countries, so "
           "check yours before you go.")),
    
    # Driving in traffic is a skill, not live information, and on main it was answered with
    # "I can't check live times or delays ... the operator's app has the next train" - a train
    # answer to a driving question. The words that make it an advice ask are the key, so "is
    # there traffic on the m25" and "what time is the next train" stay the live-information
    # answer: only a line that asks how to drive in it reaches this. The bare word "jam" is the
    # fruit set in a pan far more often than the road - "how do i set jam" and "any tips for making
    # jam" lost their cooking answer to this card - so only the phrase is a key word here.
    entry("driving-in-traffic",
          (("traffic", "traffic jam", "traffic jams", "gridlock", "motorway", "motorways",
            "red x", "red cross", "someone", "somebody", "a car", "car", "behind me",
            "behind", "bumper",
            "tailgating",
            "tailgated", "tailgate", "tailgates", "tailgaters", "overtaking",
            "aquaplaning", "hydroplaning", "standing water", "skidding", "skidded",
            "fog", "foggy", "driving in fog", "driving in the fog", "drive in fog",
            "heavy rain", "rain", "smart motorway",
            "lane", "lanes", "stop start", "stop-start", "morning traffic", "rush hour"),
           ("how do i", "how can i", "how to", "how should i", "what should i do",
            "what do i do", "what should i", "should i", "tips", "tip", "advice", "advise",
            "best way", "safest", "safe", "deal with", "cope with", "handle", "drive",
            "driving", "drove", "learn", "help", "any", "mean", "means",
            # a person describing the thing happening is asking what to do about it: "someone is
            # tailgating me" met the echo, because the line names the situation and asks nothing
            "tailgating", "tailgated", "tailgate", "tailgates", "tailgater", "tailgaters",
            "behind", "bumper")),
          _drive_in_traffic,
          # The driving words, and only those: "rain" and "fog" sat here first, which made any line
          # with the weather in it and a "should i" reach this card - "should i put the heating on
          # when it rains" is not a question about driving - so the weather words stay in the key,
          # where they still count once the line has said drive or traffic.
          ask=("drive", "driving", "drove", "traffic", "motorway", "aquaplaning", "skidding",
               "overtaking", "tailgate", "tailgates", "tailgated", "tailgating",
               "tailgaters", "merging", "slip road", "stay safe"),
          # a packed bag, a planned route, a train, a live traffic check and the weather at home
          # are other answers
          avoid=("pack", "packing", "what should i take", "what do i take", "plan", "planning",
                 "route", "stops", "overnight", "how long", "how far", "cost", "price", "fuel",
                 "insurance", "breakdown", "towing", "caravan", "trailer", "licence", "license",
                 "provisional", "test", "lessons", "abroad", "europe", "france",
                 # a car is the vehicle in the line, not the road it is on: "how do i drive an
                 # automatic car" lost its driving-lessons answer to the jam paragraph
                 "automatic", "manual", "gearbox", "clutch", "hill start", "parking", "reverse",
                 "three point turn", "3 point turn",
                 # a car that is overheating on the motorway is a fault, not a jam, and its own
                 # card is the one with the answer: stopping, cooling and the coolant level
                 "overheat", "overheats", "overheating", "overheated", "coolant",
                 "radiator", "temperature light", "temperature gauge", "steam", "steaming",
                 "smoking", "smoke", "warning light", "engine light",
                 # ice is the winter card's line, and its advice (brake early and lightly in a
                 # straight line) is the more specific one, so ice keeps its own answer
                 "ice", "icy", "black ice", "snow", "snowy", "snowing", "frost", "frosty",
                 "gritted", "gritting", "hail", "hailstones",
                 # the bare word "safe" used to be an ask word, which let any line with rain or
                 # fog in it through: "is it safe to swim in the rain" got "dipped headlights
                 # on". What is being done in the weather is what says which card it is -
                 # stout-door on #6636
                 "swim", "swimming", "swam", "pool", "beach", "sea", "lido", "run",
                 "running", "jog", "jogging", "cycle", "cycling", "dog", "dogs", "cat",
                 "cats", "pet", "pets", "baby", "babies",
                 "train", "trains", "bus", "coach", "plane", "flight", "holiday",
                 "is there", "is it busy", "delays", "delayed", "cancelled", "closed",
                 "kids", "children", "child", "baby", "toddler",
                 # a check before setting off is the live-information answer, not this one: a
                 # person asking how to look up the roads wants the app and the journey planner
                 "check traffic", "check the traffic", "check the roads", "before i leave",
                 "before we leave", "live", "how busy", "will it be busy",
                 # and the weather at home is the heating, the washing and the garden
                 "heating", "radiator", "radiators", "put the heating on", "washing",
                 "washing out", "wash", "umbrella", "umbrellas", "coat", "coats",
                 "barbecue", "bbq", "garden", "lawn", "hanging out", "dry the washing")),
    
    # --- the practical side of a trip: packing, money, getting there -----------------
    # Main already answers "how do i pack light"; this is the carry-on-only week, which it misses.
    # a medicine you have to carry is a question about the medicine, not about what fits in the
    # bag: it answers first, and the packing lists below stay away from the same words
    entry("fly-with-medicine", (("insulin", "inhaler", "inhalers", "epipen", "epi-pen", "epipens",
                                 "medication", "medications", "medicine", "medicines",
                                 "prescription", "prescriptions", "syringe", "syringes", "pills",
                                 "statins", "tablets", "paracetamol", "ibuprofen", "aspirin",
                                 "antihistamine", "antihistamines", "antibiotics", "epilepsy",
                                 "injection", "injections", "letter", "letters", "airline",
                                 "airlines", "flying with"),
                                # "do i need a letter for my insulin" names the paper, not the bag
                                ("letter", "letters", "note", "fit to fly"),
                                ("fly", "flying", "flight", "flights", "plane", "planes",
                                 "airport", "abroad", "travel", "travelling", "traveling",
                                 "holiday", "carry", "pack", "packing", "hand luggage",
                                 "carry on", "carry-on", "security", "suitcase", "bag", "bags")),
          ("Carry it in your hand luggage, never the hold, in its original box with the pharmacy "
           "label on it. Liquids over 100ml, insulin and anything injected need a doctor's letter "
           "or a copy of the prescription to get through security, and insulin travels in a cool "
           "bag but never touching ice. Pack a few days extra in case you are delayed, and check "
           "the country's rules for controlled medicines a couple of weeks ahead."), bias=1,
          # "the airline cancelled my flight what are my rights" is about the booking, not the
          # bag: "airline" and "flight" put it here, so the money words hand it back.
          # "how do i fly with a dog" was this card: "flying with" is in its key and a pet is
          # not a medicine, so the pet-travel row below is the answer
          avoid=("dog", "dogs", "cat", "cats", "puppy", "puppies", "kitten", "kittens",
                 "pet", "pets", "rabbit", "ferret", "hamster", "budgie", "parrot",
                 "cancelled", "canceled", "cancel", "refund", "refunds", "money back",
                 "compensation", "compensated", "rights", "delayed", "delay", "claim",
                 "rebook", "rebooking", "stranded", "missed my flight",
                 # a bag out of the hold that came back broken is the baggage claim, not the
                 # medicine you carry on: "the airline damaged my suitcase" was answered with a
                 # prescription letter, because "airline" and "suitcase" are this row's words
                 "damaged", "damage", "smashed", "ripped", "torn", "dented", "destroyed",
                 "broke", "broken",
                 # the same for a bag that never arrived: "the airline lost my suitcase" was the
                 # prescription letter too, because a lost bag carries none of its key's words
                 "lost my bag", "lost my bags", "lost my luggage", "lost my suitcase",
                 "lost my case", "bag never arrived", "bags never arrived",
                 "luggage never arrived", "suitcase never arrived", "bag didnt arrive",
                 "bag didn't arrive", "luggage didnt arrive", "luggage didn't arrive",
                 "bag went missing", "luggage went missing", "suitcase went missing")),
    entry("pack-hand-luggage", (("pack", "packing", "suitcase", "bag"),
                                ("hand luggage", "carry on", "carry-on", "one bag", "small bag",
                                 "cabin bag", "capsule")),
          ("For a week in a carry-on: two tops, one warm layer, one pair of trousers you can wear "
           "twice, and shoes you have already walked a mile in - then take a third of it out. Roll "
           "clothes instead of folding, take travel sizes, and plan to wash once. It also saves the "
           "wait at the belt."),
          # "can i take a cabin bag" asks what is allowed, which is the allowance entry's line: a
          # packing list does not answer it. The ask keeps the how-do-i-pack shapes.
          ask=("pack", "packing", "packed", "what to take", "what should i take", "what do i take",
               "what to bring", "what should i bring", "what do i bring", "fit in", "fit into",
               "light", "lightly", "minimal"),
          avoid=("insulin", "inhaler", "inhalers", "epipen", "epi-pen", "medication", "medicine",
                 "medicines", "prescription", "syringe", "pills", "statins", "tablets")),
    # A warm week abroad: the cold-city and the pack-light entries are main's, so this one keeps
    # its own words and passes on a cold or a skiing trip.
    # "wear" and "take" on their own belong to every other line ("what should i wear to a
    # wedding", "how many days should i take off"), so only the travel shapes are keys here.
    # A cool country in summer is sun cream's opposite: a warm layer, a waterproof, midges.
    entry("pack-cool-country", (("pack", "packing", "what should i take", "what to take",
                                 "what clothes", "which clothes", "wear", "bring"),
                                ("scotland", "scottish", "edinburgh", "glasgow", "highlands",
                                 "iceland", "reykjavik", "norway", "oslo", "sweden", "stockholm",
                                 "finland", "helsinki", "ireland", "dublin", "denmark",
                                 "copenhagen", "greenland", "faroe", "wales", "snowdonia")),
          ("Take a warm mid layer and a waterproof shell, plus long sleeves rather than vests - "
           "even in June the evenings drop to about 8C. Add a hat and gloves if you are going "
           # The row covers Iceland, Norway and Finland as well as Scotland, so the answer cannot
           # name one of them: "what should i pack for iceland" came back with midges "for the
           # west of Scotland", which reads as the wrong country.
           "high or out on the water, and midge repellent for anywhere damp and windless in high "
           "summer."),
          # The same countries are also a travel question about getting there.
          avoid=("how long", "how far", "drive", "driving", "flight", "flights", "fly", "train",
                 "coach", "ferry", "cost", "cheap", "hotel", "hotels", "stay in", "days in",
                 "weekend in", "weather like", "when to go", "best time")),
    entry("pack-warm-week", (("pack", "packing", "suitcase", "wear in", "wear to", "bring to",
                              "what should i take", "what should i wear",
                              # "what clothes should i take to portugal" is this question with the
                              # word for the thing in it: the clothes phrase is the ask, and the
                              # country or the month has to be named as well.
                              "what clothes should i take", "what clothes do i take",
                              "what clothes to take", "what clothes should i bring",
                              "what clothes do i bring", "what clothes should i pack",
                              "what clothes should i wear"),
                             ("spain", "italy", "greece", "portugal", "turkey", "croatia",
                              "france", "canaries", "mallorca", "sicily", "cyprus", "malta",
                              "october", "september", "may", "june", "july", "august", "summer",
                              "warm", "hot", "beach", "sun", "sunshine")),
          _warm_week_pack, guard=_not_a_food_to_carry,
          # "what should i take for a week in spain in august" names a warm place and a month, and
          # it tied on score with money's weekly saving rate, which keys "a week" and "should":
          # naming where and when is worth the point that tells a packing list from a rate.
          bias=1,
          avoid=("cold", "snow", "ski", "skiing", "winter", "december", "january", "february",
                 "march", "november", "rain", "wet", "hand luggage", "carry on", "carry-on",
                 "pack light", "first time", "baby", "toddler", "kids", "children", "wedding",
                 "funeral", "interview", "dress code", "party", "work", "office",
                 # Baltic, Atlantic and northern places are not a warm week, whatever the month:
                 # "what should i pack for scotland in may" was getting shorts and sun cream.
                 "scotland", "scottish", "edinburgh", "glasgow", "highlands", "iceland",
                 "reykjavik", "norway", "sweden", "finland", "denmark", "copenhagen", "oslo",
                 "stockholm", "helsinki", "ireland", "dublin", "england", "wales", "britain",
                 "uk", "london", "cornwall", "devon", "yorkshire", "lake district", "alps",
                 "greenland", "canada", "new zealand", "estonia", "latvia", "lithuania",
                 "poland", "russia", "germany", "netherlands", "belgium", "austria",
                 "switzerland", "czech", "prague")),    # A London word has to be in the line: "what airport is closest to lisbon" is not this.
    entry("london-airport", (("heathrow", "gatwick", "stansted", "luton", "london city", "london"),
                             ("closest", "nearest", "central london", "into london", "to london",
                              "get to london", "transfer", "which airport", "how do i get",
                              "how do i",
                              # the fare is the question people actually ask about an airport
                              # run: "whats the cheapest way to get to heathrow" was answered
                              # with the cheapest dinners, because no phrase here asked a price
                              # and none said "get to" without "london" after it.
                              "get to", "getting to", "get from", "cheapest", "cheap", "cheaper",
                              "best way", "way to get", "early flight", "early in the morning",
                              # not a bare "how much" or "price": those are the fare cards'
                              # questions ("how much is a flight to heathrow" is when to book,
                              # and adding them here took that line)
                              "taxi")),
          _london_airport),
    # "drive to london or train" is a choice about a city, not a flight, and the either-or
    # reading answered it with "Either works, so take the one that's less fuss", which is
    # nothing. The answer is a comparison: parking and the charge against a train fare.
    entry("london-car-or-train",
          (("london", "the city", "central london", "into london"),
           # "tube" is in the avoid list below (a Tube question is the contactless card's), so
           # it is not also in the key where the two would cancel out
           ("drive", "driving", "car", "by car", "train", "by train", "parking",
            "which is", "better", "or train", "or drive", "cheaper", "worth", "should i")),
          "Take the train into the centre: parking runs twenty to thirty pounds for a day, the "
          "congestion charge is on top of that, and then you are still looking for a space. Drive "
          "only if you are heading somewhere outside the centre or carrying things - and then "
          "park at a Tube or rail station on the edge and finish by train. Book the train two or "
          "three weeks ahead and it is usually cheaper than the fuel plus parking.",
          # an airport question is the airport card's, and a coach question is the coach answer
          avoid=("airport", "heathrow", "gatwick", "stansted", "luton", "flight", "flights",
                 # a duration or a distance between two places is a journey question, not the
                 # car-or-train choice: "how long is the train from london to edinburgh" was
                 # answered with parking prices and the congestion charge.
                 "how long", "how far", "how many hours", "journey", "duration", "timetable",
                 "fly", "coach", "coaches", "megabus", "national express", "hotel",
                 "what is there to do", "visit",
                 # a coach or a bus question is the coach card's, not the car's
                 "bus", "buses", "tube", "oyster", "travelcard", "travel card")),

    # Tipping abroad is a different question from tipping at home, and the lifeadmin table owns
    # the home one (a restaurant here, a hairdresser, a cab). So this entry needs a country: with
    # none named it passes, and the everyday answer keeps "how much do you tip".
    # "any tips for a long car journey" is advice, not a tip, so those shapes pass too.
    entry("tipping-abroad", (("tip", "tipping", "gratuity"),
                             # "us" is the pronoun far more often than the country: "tell us a
                             # tip about saving money" must not get restaurant percentages, so
                             # the country is only ever "the us", "usa" or "america" here.
                             ("america", "american", "usa", "the us", "in us", "states",
                              "japan", "japanese", "tokyo", "kyoto", "europe", "france",
                              "paris", "spain", "italy", "rome", "portugal", "greece",
                              "germany", "netherlands", "amsterdam", "mexico", "thailand",
                              "turkey", "dubai", "india", "canada", "australia", "ireland",
                              "abroad", "overseas",
                              # A city is a country here: "how much do you tip in new york" was
                              # the UK rule, because the country list had no place in it.
                              "new york", "nyc", "las vegas", "vegas", "los angeles",
                              "san francisco", "miami", "chicago", "boston", "seattle",
                              "washington", "texas", "hawaii", "orlando", "florida",
                              "california", "toronto", "vancouver", "sydney", "melbourne",
                              "brisbane", "perth", "auckland", "bali", "phuket", "singapore",
                              "hong kong", "seoul", "lisbon", "barcelona", "madrid", "berlin",
                              "munich", "florence", "venice", "athens", "crete", "malta",
                              "cyprus", "croatia", "dubrovnik", "prague", "vienna", "zurich",
                              "geneva", "brussels", "copenhagen", "stockholm", "oslo",
                              "helsinki", "warsaw", "budapest", "istanbul", "egypt", "morocco",
                              "brazil", "argentina", "peru", "cuba", "jamaica", "barbados",
                              "maldives", "sri lanka", "vietnam", "cambodia", "malaysia",
                              "indonesia", "philippines", "qatar", "israel", "jordan", "kenya",
                              "iceland", "norway", "sweden", "denmark", "finland", "poland",
                              "czech", "austria", "switzerland", "belgium",
                              # a hotel and a tour are where a traveller meets a tip, and those
                              # lines are read as this domain's, so this row has to hold them
                              "hotel", "housekeeping", "porter", "concierge", "bellboy",
                              "room service", "tour guide", "tour", "excursion", "walking tour",
                              "coach driver", "mover", "movers", "removal men")),
          _tipping,
          avoid=("any tips", "tips for", "tips on", "tips to", "a few tips", "some tips",
                 "hairdresser", "barber", "haircut", "barista")),
    # "How much spending money should i take to spain" is the same carrying question with a
    # "spending" in front of it, and the phrase sent it to money's impulse-buying answer.
    entry("money-abroad", (("money", "cash", "currency", "card", "cards", "atm", "spending money",
                            "spending cash"),
                           ("abroad", "travelling", "travel", "holiday", "exchange", "change",
                            "safe", "safely", "safety", "stolen", "theft", "pickpocket",
                            "pickpockets", "money belt", "fee", "fees",
                            "commission", "local currency",
                            # "how much money should i take" names no place and got a hedge: the
                            # carrying words are the question, and the reply says both parts.
                            "take", "bring", "carry", "carrying", "with me", "spain",
                            "italy", "rome", "france", "paris", "greece", "portugal", "turkey",
                            "croatia", "germany", "netherlands", "japan", "thailand", "mexico",
                            "america", "usa", "europe")),
          _money_abroad,
          # Sending money to someone is a transfer, not what to carry: that is send-money-abroad.
          # A job, a promotion or a pay trade is a decision, not holiday spending: "should i take
          # the job with more money and more travel" is not a question about cards and cash, and
          # a bare "money" beside a bare "travel" is a pair of loose words, not a topic.
          avoid=("send", "sends", "sending", "sent", "transfer", "transfers", "transferring",
                 "wire", "wiring", "job", "jobs", "job offer", "promotion", "promoted",
                 "career", "salary", "employer", "boss", "pay cut", "offer letter",
                 "interview",
                 # Shopping online at home is not what to carry abroad: "how do i keep my card
                 # safe when shopping online" took the two-cards-and-local-cash answer.
                 "online", "website", "websites", "internet", "phishing", "shopping online",
                 # "how do i get a travel card" is a scheme to apply for, not advice on what to
                 # carry: the word travel alone is not the subject.
                 "travel card", "travelcard", "oyster", "bus pass", "railcard", "season ticket",
                 # A wage is not what to carry abroad: "im worried about money" then "we bring
                 # home 3000 between us a month" reached this entry through the money word of the
                 # turn before and the bare "bring" of its own, and got the two-cards answer. The
                 # period is not the test on its own - "spending money for a week in rome" has
                 # one - so the verb and the word home are.
                 "bring home", "brings home", "bringing home", "brought home",
                 "take home", "takes home", "taking home", "took home",
                 "earn", "earns", "earning", "earned", "wage", "wages", "payslip", "payslips",
                 "after tax", "before tax", "monthly pay", "payday",
                 # A card that holds files is not a card you spend: "does my phone take an sd
                 # card" was answered with two cards and some local cash, because "card" and
                 # "take" are both in the key.
                 "sd card", "sd cards", "memory card", "memory cards", "micro sd", "microsd",
                 "sim card", "sim cards", "storage card", "flash card", "usb stick",
                 "hard drive", "ssd")),
    entry("send-money-abroad", (("send", "sends", "sending", "sent", "transfer", "transfers",
                                 "transferring", "wire", "wiring", "remit"),
                                # The people are named with the country ("to my sister in spain"):
                                # a bare "sister" is a gift or card question, not a transfer.
                                ("money", "cash", "euros", "dollars", "pounds", "funds",
                                 "abroad", "overseas", "spain", "france", "italy",
                                 "poland", "romania", "portugal", "turkey", "nigeria", "india",
                                 # the country the money is going to is the word that separates
                                 # a transfer from pocket money or a holiday budget, so the
                                 # countries people actually send money to are named
                                 "australia", "canada", "usa", "america", "brazil", "pakistan",
                                 "bangladesh", "philippines", "ireland", "germany",
                                 "netherlands", "japan", "china", "kenya", "ghana",
                                 "south africa", "new zealand", "dubai", "uae", "jamaica",
                                 "morocco", "egypt", "sri lanka", "nepal", "vietnam",
                                 "thailand", "mexico", "zimbabwe", "uganda")),
          ("Use a transfer app such as Wise or Revolut for a normal amount: you get the real "
           "exchange rate and pay a small fee, and it lands in their bank account in a day or two. "
           "Compare the fee and the rate together, because a \"no fee\" transfer usually carries a "
           "worse rate, and use your own bank for large sums where you want the paper trail."),
          # Sending a parcel or a letter is a post office question, not a transfer one.
          avoid=("parcel", "parcels", "package", "packages", "letter", "post office", "flowers",
                 "email", "text", "message", "gift")),
    # "taxi or the train" is a choice between two ways of getting there, not a taxi question.
    entry("taxi-abroad", (("taxi", "cab", "uber", "ride hailing", "driver"),
                          ("abroad", "airport", "ripped", "overcharge", "price", "fare", "meter",
                           "scam", "safe", "expensive", "cost", "costs")),
          _taxi_abroad, bias=1,
          avoid=("or the train", "or a train", "or the bus", "or a bus", "or drive", "or park",
                 "or cycle", "or walk", "should i get a taxi", "is it cheaper")),
    entry("visa-check", (("visa", "entry requirements", "evisa"),
                         ("need", "required", "apply", "how do i", "do i", "get", "check")),
          ("It depends on your passport and where you are going, and the rules change often, so "
           "check the destination's official government site - with a UK passport, the gov.uk "
           "travel advice page links to it. Most tourist visas are applied for online a few days "
           "ahead; some countries charge a small fee on arrival instead.")),
    entry("baby-on-plane", (("baby", "babies", "infant", "toddler", "newborn"),
                            ("plane", "flight", "flying", "long haul", "take off", "travel",
                             "travelling", "traveling", "holiday", "abroad", "trip")),
          ("Ask for a bassinet seat at booking if they are under two: it is free on most airlines "
           "and gives you a bed and floor space. Feed or offer a dummy at take-off and landing "
           "for the ears, pack twice the nappies you think you need, and take a change of "
           "clothes for yourself as well as for them.")),
    # "how do i claim delay repay" names no train word, so the flight bands took it: the
    # scheme's own name gets its own entry, and the train words stay with `train-refund`.
    entry("delay-repay",
          (("delay", "delayed", "late"),
           ("repay", "delay repay", "delayrepay", "compensation for the delay",
            "money back for the delay")),
          "Delay Repay is the train operators' scheme: on most of them you can claim from 15 "
          "minutes late, and some pay from 30. Claim on the operator's own site within 28 days, "
          "with the ticket or booking reference and the time you actually arrived, and it comes "
          "back as cash, a voucher or a free ticket depending on the operator.",
          # a flight, a hotel, a shop or a plain refund is a different set of rules, and a line
          # that names a train is `train-refund`'s, which has the Delay Repay paragraph in it.
          avoid=("flight", "flights", "airline", "plane", "hotel", "holiday", "faulty",
                 "broken", "shop", "item", "online order", "train", "trains", "rail",
                 "railway", "refund", "cancelled", "cancel")),
    entry("flight-delay-claim", (("delay", "delayed", "cancelled", "cancellation", "compensation",
                                 # "complain" is how most people ask it, and every other
                                 # complaint entry stands down when a flight is named
                                 "complain", "complaining", "complaint", "complain about"),
                                 ("flight", "plane", "airline", "claim", "owed", "entitled")),
          ("Under UK and EU rules you are owed 220 to 520 pounds per person when a flight arrives "
           "three hours or more late, unless the cause was extraordinary (weather, air traffic "
           "control, a security alert). Claim from the airline yourself with the booking reference "
           "and boarding pass; you usually have up to six years."),
          # A delayed train, bus or ferry is not this rule, and "delayed" plus "claim" was
          # bringing them here: only a flight word may own the answer.
          avoid=("train", "trains", "rail", "railway", "railcard", "tube", "underground",
                 "bus", "coach", "ferry", "tram", "cruise", "package holiday", "hotel",
                 "luggage", "baggage", "parcel", "delivery",
                 # a claim from the post office is the carrier's, not the airline's: "how do i
                 # claim compensation from royal mail" was answered with the flight bands.
                 "royal mail", "post office", "postal", "parcelforce", "courier", "evri",
                 "dpd", "yodel", "letter", "letters", "package",
                 # "delay repay" is the name of the train scheme: the line names no train word,
                 # and "how do i claim delay repay" was answered with the flight bands. A line
                 # that does name a flight is this row's, though, and the train row above stands
                 # down on it, so "flight delay compensation" and "how do i complain about a
                 # delayed flight" both belong here.
                 "delay repay", "repay", "minutes late", "hours late")),
    # Being bumped off a full flight is not being delayed: it has its own rule, with cash
    # compensation on top of the re-routing, and "my flight was overbooked what are my rights"
    # was a shrug. Denied boarding is EU 261 (kept in UK law) whatever the cause.
    entry("denied-boarding",
          # The bare "bumped" is not enough to mean a seat: "i bumped into my ex at the airport"
          # is not a denied-boarding question, so the shapes that do mean it are written out.
          (("overbooked", "overbooking", "denied boarding", "denied",
            "bumped off", "bumped from", "bumped me", "bumped to a later flight", "bump me",
            "no seat", "seats were full", "seats full", "over sold", "oversold",
            "volunteered", "volunteer"),
           ("flight", "flights", "plane", "airline", "airlines", "airport", "boarding",
            "rights", "compensation", "claim", "owed", "entitled", "what can i", "gate")),
          "You are owed a choice on the spot: a full refund of the ticket, or a new flight as "
          "soon as one is available, plus 220 to 520 pounds per person in cash, not a voucher. "
          "While you wait the airline pays for meals and two calls, and a hotel if the new "
          "flight is the next day. Ask for the reason in writing and keep the boarding pass; if "
          "they refuse, complain to the CAA - you have up to six years.",
          # The ask is the gate on a line that is not shaped like a question at all, and it has
          # to carry every way of naming the cause: "the flight was oversold" names the flight
          # and the cause and nothing else, so "oversold" belongs here as well as in the key.
          ask=("overbooked", "overbooking", "denied boarding", "denied",
               "bumped off", "bumped from", "bumped me", "bumped to a later flight", "bump me",
               "no seat", "seats were full", "seats full", "over sold", "oversold",
               "volunteer", "volunteered"),
          avoid=("train", "trains", "rail", "railway", "tube", "underground", "bus", "coach",
                 "ferry", "tram", "cruise", "hotel", "hotels", "luggage", "baggage",
                 "parcel", "delivery", "restaurant", "concert", "ticket for")),
    # "can i get a refund on a hotel booking" had no answer: the room was going to the
    # faulty-goods law. Flexible rates are free to cancel until a stated day; the cheap ones are
    # not, and that difference is the point.
    entry("hotel-refund",
          (("refund", "refunds", "money back", "cancel", "cancelling", "cancelled", "called off"),
           ("hotel", "hotels", "booking.com", "room", "rooms", "accommodation", "guest house",
            "airbnb", "b and b")),
          "Check the rate you booked: a flexible rate is free to cancel up to a stated day, "
          "usually 24 to 48 hours before, and a saver rate is usually non-refundable - that is why "
          "it was cheaper. Cancel in the app rather than by phone so you have the confirmation, and "
          "if the hotel cancels on you, ask for a room of the same standard or a full refund plus "
          "the cost of a replacement if nothing is left.",
          avoid=("flight", "flights", "airline", "train", "trains", "faulty", "broken", "shop",
                 "item", "online order")),
    # Trains had no refund answer at all: "how do i get a refund for a train ticket" was getting
    # the faulty-goods law, and a cancelled train got "book early for cheap fares". Delay Repay is
    # the part people do not know they are owed.
    entry("train-refund",
          (("refund", "refunds", "money back", "delay repay", "compensation", "compensated",
            "cancelled", "canceled", "delayed", "missed", "late", "running late",
            "minutes late", "hours late"),
           # not bare "ticket": "whats the refund policy for a concert ticket" is not a train,
           # a gig or a festival is the concert answer's, and the train words are enough on
           # their own ("can i get a refund on my train ticket" keys on "train").
           ("train", "trains", "rail", "railway", "railcard", "journey", "operator",
            "commute")),
          "Two different claims. Before you travel, a refund is usually allowed less than an admin "
          "fee (up to £10) on an unused ticket, and advance tickets are often non-refundable but "
          "changeable. For a late train, Delay Repay pays out from 15 minutes late on most "
          "operators - claim on the operator's site within 28 days with your ticket and the delay.",
          # A flight is the other set of rules, and the faulty-goods refund law is not a ticket.
          avoid=("flight", "flights", "airline", "plane", "faulty", "broken", "shop", "item",
                 "online order", "hotel", "holiday", "luggage",
                 "concert", "gig", "festival", "theatre", "theater", "cinema", "match",
                 "season ticket", "event", "show")),
    # A ticket to a show is not a journey: nobody at a theatre runs Delay Repay, and the
    # question is the seller's terms.
    entry("event-ticket-refund",
          (("refund", "refunds", "money back", "cancel", "cancelled", "canceled", "cancelling",
            "resell", "resale", "exchange", "swap",
            # a show that is moved or put back is the same question as one that is cancelled,
            # and without these words it fell to "Rotten luck."
            "postponed", "postponement", "rescheduled", "reschedule", "moved to",
            "new date", "new venue", "venue changed", "cancelled the gig"),
           ("concert", "gig", "gigs", "festival", "theatre", "theater", "cinema", "match",
            "stadium", "show", "comedy", "musical", "opera", "ballet", "event")),
          "Go back to whoever sold you the ticket - the box office or the agency, not the venue - "
          "because their terms decide it, and a ticket is usually non-refundable if you simply "
          "cannot go. If the show is cancelled or moved you are owed the face value back, and "
          "whether the booking fee comes too depends on the seller; ask for a refund rather than a "
          "credit note. If you just cannot make it, some sellers run an official resale or ticket "
          "exchange, which gets you more than nothing.",
          # a journey is not a show, and the journey answers hold those.
          # "how do i resell my ticket" and "can i sell my concert ticket" are a sale, not a
          # refund, so those go to resell-ticket.
          avoid=("train", "trains", "rail", "railway", "flight", "flights", "airline", "plane",
                 "bus", "coach", "ferry", "hotel", "parking", "season ticket", "loyalty",
                 "resell", "resale", "reselling", "sell", "selling", "sold", "give my ticket",
                 "pass on", "transfer"),
          # the general consumer refund in money.py matches "money back" word for word, so a
          # show ticket has to outrank it rather than tie with it.
          bias=1),
    # "can i get a refund on my ticket" names no kind of ticket: the honest answer is that it
    # depends, and which of the sets of rules it is. The train, flight and show entries own their
    # own words, so this one only holds the bare ticket.
    entry("ticket-refund-general",
          (("refund", "refunds", "money back", "cancel", "cancelled", "canceled", "cancelling"),
           ("ticket", "tickets")),
          "Tell me what the ticket is for and I will be exact, because the rules differ: a train "
          "is a refund less a small admin fee, a flight follows the fare's own rules, and a gig or "
          "theatre ticket is the seller's terms. What is the same everywhere is that if the "
          "company cancels on you, you are owed your money back.",
          avoid=("train", "trains", "rail", "railway", "railcard", "flight", "flights", "flying",
                 "airline", "airlines", "plane", "airport", "bus", "coach", "ferry", "tram",
                 "hotel", "concert", "gig", "festival", "theatre", "theater", "cinema", "match",
                 "stadium", "show", "event", "comedy", "musical", "opera", "ballet",
                 "parking", "season ticket", "lottery", "raffle")),

    # "how do i resell my ticket" was answered with the expenses policy in money.py, because a
    # receipt and a claim for it look like a ticket to sell. A ticket changes hands by the
    # seller's own rules, so this is the travel-and-events answer.
    entry("resell-ticket",
          # the second group has to hold the ticket, so "how do i sell my old phone" and a car
          # stay with their own answers; "sell" alone is enough with a ticket word beside it.
          (("resell", "resale", "reselling", "sell", "selling", "sold", "sell out",
            "give my ticket", "give my tickets", "give it to a friend", "give them to a friend",
            "pass on", "pass my ticket", "transfer", "transferring", "name change",
            "get rid of my ticket", "hand over"),
           ("ticket", "tickets", "seat", "seats")),
          "Sell it back through the seller, not on social media: the box office, the agent's own "
          "fan-to-fan resale, or a face-value site, because a ticket sold in a Facebook group can "
          "be refused at the door when the name does not match. Most tickets are "
          "non-transferable, so read the terms first and ask for a name change in writing if they "
          "allow one. Sell at or below face value and keep the sale inside the platform, so the "
          "buyer is covered and you cannot be blamed for a ticket that does not scan. An unused "
          "advance train ticket can sometimes be changed for a fee instead, which is often worth "
          "more than reselling it.",
          # a receipt you claim back, a phone on ebay and a house are other answers
          avoid=("expenses", "expense", "receipt", "receipts", "mileage", "claim back",
                 "reimburse", "car", "phone", "laptop", "house", "shares", "stocks", "season ticket",
                 "railcard", "advance ticket")),

    # A cancellation is a refund question first and a compensation question second, and the two
    # were one entry: "how do i claim a refund for a cancelled flight" was going to the 30-day
    # faulty-goods law in money.py. The refund-or-replacement choice gets its own answer.
    entry("flight-cancelled-refund",
          (("refund", "refunds", "money back", "reimbursed", "reimbursement", "cancelled",
            "canceled", "cancel", "cancelling"),
           # the same for the plane: a booking with a flight in it is a flight, and a concert
           # or a gig ticket has no airline to ring
           ("flight", "flights", "airline", "airlines", "plane", "booking", "holiday")),
          "A cancellation is your choice of a full refund or a replacement flight, and the airline "
          "has to pay the money back within seven days - ask in writing with the booking reference "
          "and keep it. You may also be owed 220 to 520 pounds per person if they told you less "
          "than 14 days before, unless the cause was extraordinary like weather or air traffic "
          "control. Do not accept a voucher if you would rather have the cash.",
          # A faulty kettle, a delayed train and a hotel booking are not a cancelled flight.
          # "am i owed anything" asks for the compensation bands, which the delay rule holds.
          avoid=("owed", "am i owed", "entitled", "faulty", "broke", "broken", "kettle",
                 "train", "trains", "rail", "railway",
                 "bus", "coach", "ferry", "tram", "hotel", "package holiday", "luggage",
                 "baggage", "parcel", "delivery", "shop", "online order", "sale",
                 # somebody asking what compensation they can claim wants the delay bands,
                 # not the refund choice
                 "compensation", "compensated", "claim compensation",
                 # "what are my rights" wants the whole set, which the compensation rule opens
                 "rights", "what am i entitled", "am i entitled",
                 # leave cancelled by an employer is not a flight: "my manager cancelled my
                 # holiday" was getting the airline refund, and work.py's shifts-changed answers
                 # the employment side
                 "my manager", "my boss", "my employer", "annual leave", "day off", "days off",
                 "rota", "shift", "shifts", "my job", "called in",
                 # the same leave, said the other way round: "my holiday got cancelled by work"
                 "by work", "because of work", "work cancelled", "work has cancelled",
                 "work said no", "my work",
                 # not a plane: a concert, gig, festival or match ticket is somebody else's rules
                 "concert", "gig", "festival", "theatre", "theater", "cinema", "match",
                 "season ticket", "event", "show",
                 # and neither is a course, a class or a club: "can i cancel a course i
                 # booked" got the airline's refund choice because "cancel" and "booked" are
                 # the flight row's two words
                 "course", "courses", "class", "classes", "lesson", "lessons", "member",
                 "membership", "club", "gym", "school", "nursery", "subscription"),
          # a refund ask matches the compensation rule word for word, so the
          # refund-or-replacement answer has to outrank it rather than tie with it.
          bias=1),
    # The traveller's own change: a date moved, a flight missed, money back. This is not the
    # compensation rule above (that is the airline's fault), so it avoids the delay words.
    entry("flight-change",
          (("change", "changes", "cancel", "cancelling", "cancelled", "refund", "refunded",
            "move", "postpone", "switch", "amend"),
           # not bare "my ticket": "can i get a refund on my ticket" names no kind of ticket,
           # and `ticket-refund-general` answers that one.
           ("my flight", "my flights", "the flight", "flight date", "the date", "my booking",
            "the booking", "my fare", "flight")),
          ("Ring the airline as soon as you know: a cheap fare is usually changeable for a fee plus "
           "any difference in fare, and often not refundable at all, so ask before you cancel. "
           "Flexible fares cost more on the day but pay for themselves once plans move. If the "
           "reason is illness or a bereavement, check your travel insurance before you ring."),
          avoid=("train", "trains", "rail", "railway", "tube", "bus", "coach", "ferry",
                 "hotel", "booking.com", "hire car", "car hire", "rental", "name", "address",
                 "password", "booking reference", "seat", "currency", "money", "appointment",
                 "compensation", "compensated", "claim", "claiming", "owed", "entitled",
                 "delay", "delayed", "rights", "eu261")),
    # A no-show is the one that costs people the whole ticket, so it gets its own answer.
    # The key is the missing plus the flight, in two parts, because saying it is the question:
    # "i missed my flight", "we missed our flight" and "my flight was delayed and i missed it"
    # name the trouble and stop. Keyed as whole phrases ("missed my flight") the one loaded part
    # scored 3 and the gate is 4, so they got "Rotten luck." and nothing else.
    #
    # The miss is in as "missed" and as the phrases, and the bag words are in avoid: the matcher
    # reads "missing" as a form of "missed", so a line about a bag that did not come off the belt
    # would reach this answer, and a no-show speech would be the wrong thing entirely.
    entry("missed-flight",
          (("missed", "miss my flight", "miss the flight",
            "missed my flight", "missed the flight", "miss my plane", "miss the plane",
            "missed my plane", "missed the plane", "miss a flight", "missed a flight",
            "missing my flight", "missing the flight", "missing a flight",
            "missing my plane", "missing the plane", "missed our flight",
            "miss our flight", "missing our flight",
            "too late for my flight", "too late for the flight", "no show", "no-show",
            "late for my flight", "late for the flight"),
           # not bare "connection": a missed connection is the next entry's, because the
           # first leg was late and there is somebody to ask.
           ("flight", "flights", "plane", "planes", "airline", "airlines", "boarding",
            "check in", "check-in", "departure", "gate")),
          ("A no-show usually voids the ticket, so ring the airline the moment you know rather than "
           "at the airport: many will move you to a later flight for a fee, and a flexible fare may "
           "let you do it free. Check the check-in closing time, which is often 45 to 60 minutes "
           "before departure, and see whether your insurance covers the reason you were late."),
          # A flight still ahead is a different question: "will i miss my flight if i leave at
          # 5" and "how early should i get to the airport" are about getting there in time.
          avoid=("will i", "if i leave", "if i set off", "how early", "how long before",
                 "what time should i", "leave at", "set off", "traffic on the way",
                 "check in online", "bag drop", "too early", "get there",
                 # a bag is missing off a flight, and "my bag is missing off my flight" is a
                 # lost-property question: the miss is the bag's, not the person's, so this
                 # answer about their own no-show would be the wrong answer entirely.
                 "bag", "bags", "baggage", "suitcase", "suitcases", "luggage", "holdall",
                 "rucksack", "backpack", "carousel")),
    # A flight somebody decided not to take is neither a cancellation nor a delay: the airline
    # did nothing wrong, so nothing is owed but the tax, and the answer is what is genuinely
    # claimable. "can i get a refund on a flight i didnt take" was reaching the picnic list in
    # meals.py, because it carries both "flight" and "take".
    entry("flight-not-taken",
          (("didnt take", "didn't take", "did not take", "didnt use", "didn't use",
            "did not use", "didnt go", "didn't go", "did not go", "couldnt take",
            "couldn't take", "could not take", "couldnt go", "couldn't go",
            "could not go", "not going to take", "decided not to go"),
           ("flight", "flights", "plane", "planes", "airline", "airlines", "flying")),
          ("The fare is usually gone, but the tax and the airport charges come back: ask the airline "
           "in writing with the booking reference and most refund those even on a non-refundable "
           "ticket, often 30 to 60 pounds on a short-haul. Ring them before departure if you can, "
           "because many will move you to a later flight for a fee, and check whether your travel "
           "insurance covers the reason you could not go."),
          # "didnt take" scores the same as the bare refund wording in the cancellation entry,
          # so the tie has to go to the no-show: it is the more specific reading of the line.
          bias=1),
    # Seats and sleep: the two things people ask about a flight that are not rules or prices.
    # A missed connection is not a no-show: the first leg was late, so there is somebody to ask.
    entry("missed-connection",
          (("miss my connecting flight", "missed my connecting flight", "miss the connecting flight",
            "missed connecting flight", "miss a connection",
            "missed a connection", "miss the connection", "missed the connection",
            "miss my connection", "missed my connection", "connecting flight"),
           ("what", "what happens", "what do i do", "what should i do", "who pays", "hotel",
            "rebook", "next", "now", "entitled", "compensation", "help", "late", "delayed")),
          "Go straight to the airline's desk or app before the next one closes: when both legs are "
          "on one ticket the airline has to put you on the next available seat, and pay for a hotel "
          "and meals if the wait is overnight. On two separate tickets the second one is a no-show "
          "and nobody owes you a seat, so ring that airline and ask anyway. Keep every receipt.",
          # a delayed or cancelled flight on its own is the compensation line, not this one
          avoid=("delay pay", "compensation for", "how much compensation", "ehic", "insurance")),

    entry("plane-seat",
          (("seat", "seats", "sit", "sitting"),
           ("best", "better", "window", "aisle", "middle", "pick", "choose", "legroom",
            "exit row", "on a plane", "on the plane", "on a flight", "on a long flight")),
          ("Take an aisle seat if you get up, want to stretch a leg out, or are tall; a window if "
           "you want to sleep against the wall and not be climbed over. The middle seat is the one "
           "to avoid. An exit row buys legroom but no bag under the seat in front."),
          avoid=("train", "trains", "rail", "railway", "tube", "underground", "bus", "coach",
                 "ferry", "boat", "theatre", "theater", "cinema", "concert", "stadium",
                 "restaurant",
                 # an exercise is not a seat: "is a plank better than a sit up" keys `sit` and
                 # `better` here, and the core moves have their own rows in fitness.py
                 "sit up", "sit ups", "plank", "planks", "squat", "squats", "crunch",
                 "crunches", "press up", "deadlift", "workout", "gym")),
    entry("sleep-on-a-plane",
          (("sleep", "sleeping", "get some sleep", "fall asleep"),
           ("plane", "planes", "flight", "flights", "flying", "red eye", "red-eye",
            "night flight", "overnight flight", "long haul")),
          ("Set your watch to the time where you are going as soon as you board, and sleep to that "
           "clock rather than the one at home. Earplugs and an eye mask do more than any gadget, "
           "and skip the wine: it helps you drop off and wakes you at 3am. Book an aisle or window "
           "seat, keep the shoes loose, and take the coffee at the end, not the start.")),
    entry("business-class",
          (("business class", "first class", "premium economy", "club class"),
           ("worth", "worth it", "better", "upgrade", "cost", "pay", "cheap", "cheaper")),
          ("On a long overnight it buys sleep, and that is usually the whole point: a flat bed and "
           "a lounge shower on an eight-hour flight is worth more than on a two-hour hop. On a "
           "daytime short-haul it buys a bigger seat and a meal, which is rarely worth the money. "
           "Look at premium economy before you decide."),
          # Two other "first class" things key on the same two words and this row was answering
           # for them. The post's: `first class post cost` was told about a flat bed and a lounge
           # shower, where the postage card is the answer. And a degree's: `is a first class degree
           # worth it` was told the same, where study.py's pass-mark card is the answer. Neither
           # names a journey, so the words that make them a post or a grade stand this row down,
           # and every line that does name a journey keeps it.
           avoid=("post", "posts", "postage", "post office", "postbox", "post box", "letter",
                  "letters", "parcel", "parcels", "stamp", "stamps", "envelope", "envelopes",
                  "royal mail", "signed for", "recorded delivery", "special delivery", "delivery",
                  "duty free", "customs",
                  "degree", "degrees", "university", "uni", "honours", "honors", "bachelor",
                  # "ba" is not here on its own: it is British Airways to anyone booking a seat,
                  # and "is first class worth it on ba" lost the flight card to it. "bsc" and
                  # "msc" name nothing but a degree, so they stay.
                  "bsc", "msc", "grade", "grades", "gpa", "undergraduate", "graduate",
                  "dissertation", "thesis", "exam", "exams", "pass mark", "classification")),
    # "Is it safe to go" is a question about the country now, not about crime in general: the
    # Foreign Office page is the answer every insurer and employer reads, whatever the country.
    entry("travel-advice-abroad",
          (("safe to travel", "safe to visit", "safe to go", "is it safe in", "travel advice",
            "travel warning", "travel advisory", "foreign office", "advisory"),
           tuple(sorted(WATER))),
          _travel_advice),
    # What you can carry, on you and in the bag, before the allowance matters at all.
    entry("vape-on-a-plane",
          (("vape", "vapes", "vaping", "e-cigarette", "e-cigarettes", "ecig", "ecigs", "e cig",
            "vape pen", "eliquid", "e-liquid", "nicotine"),
           ("plane", "planes", "flight", "flights", "fly", "flying", "airport", "security",
            "hand luggage", "carry on", "cabin", "hold", "luggage", "bag", "bags", "abroad",
            "allowed", "take")),
          "Vapes travel in your hand luggage, never in the hold: the device and any spare "
          "batteries in the cabin, and the liquid in the 100 ml bag. Do not use it on the plane or "
          "in the terminal, including the toilets, because most airlines treat it as smoking. A "
          "few countries ban them completely, so check the arrival country's rules as well as "
          "your airline's own.",
          avoid=("smoking", "quit", "stop smoking", "cigarette", "cigarettes", "give up",
                 "withdrawal", "nicotine patch", "price", "cost", "where to buy", "cheapest",
                 # "take a vape" is also "take it into hospital", and a ward is not an airport:
                 # the key's only travel word in that line is "take", so every other place has to
                 # stand this answer down rather than be told about the 100 ml bag.
                 "hospital", "ward", "hospice", "clinic", "care home", "the ward",
                 # A bag at home is not the cabin bag: "i found a vape in my daughters bag" is a
                 # parent's question, and the school bag is not a suitcase either
                 "found", "found a vape", "my daughter", "my daughters", "my son", "my sons",
                 "my child", "my children", "my kid", "my kids", "teenager", "teen", "school bag",
                 "schoolbag", "backpack", "rucksack",
                 "train", "tube", "bus", "coach", "ferry", "pub", "restaurant", "festival",
                 "concert", "gig", "school", "work", "office", "in the building"),
          # science.py's stop-smoking entry keys on "vape" and "how", and its answer is a quit
          # plan, so a travel question about a vape has to outrank it rather than lose the tie.
          bias=2),

    # Bringing it home: the UK allowance is a fixed table, and it is the same for every trip.
    entry("duty-free",
          (("duty free", "duty-free", "customs allowance", "duty free allowance", "bring back",
            "bring home", "declare at customs", "goods allowance",
            # "personal allowance" was here and took the income-tax question, which shares the
            # word and nothing else: the customs table is a goods allowance
            "customs limit", "alcohol allowance", "tobacco allowance",
            # "bring wine back from france" puts a word between "bring" and "back", so the phrase
            # never matched and the commonest way of asking the allowance was a search hedge.
            # The bare verb is safe here because the second group still has to be met, and the
            # food that comes home the other way is fenced below.
            #
            # "bring", not "take": a bare "take" met "what can i" in the second group and answered
            # the airport security question with the customs table - "what can i take through
            # security" came back as 4 litres of spirits. Everything the allowance is asked about
            # ("wine back from france", "spirits home from spain", "how much can i bring") says
            # bring, and nothing that says take is a customs line.
            # "take back" and "take home" are the same verb with the customs word beside it, and
            # those two are safe because the phrase names the direction
            "bring", "brings", "bringing", "brought",
            "take back", "takes back", "taking back", "took back",
            "take home", "takes home", "taking home", "took home"),
           ("uk", "home", "britain", "england", "alcohol", "wine", "spirits", "cigarettes",
            "tobacco", "limit", "allowance", "how much", "what can i", "back")),
          ("Coming into the UK you can bring 4 litres of spirits, 18 litres of wine or 42 litres of "
           "beer, 200 cigarettes, and other goods - perfume and gifts count here - up to 390 "
           "pounds, all per person. Anything above "
           "that you declare in the red channel and pay duty on. Keep the receipts, and note that "
           "the person carrying it must own it."),
          # "how much wine can i bring back from france" and "is there a limit on alcohol i can
          # bring home" both share "wine"/"alcohol" and "limit" with the weekly-units answer, which
          # outscored this table: the word "bring" is what makes it a customs question, and the
          # weekly-units row still outscores it on "alcohol ... limit", so the bias is two
          bias=2,
          # a line whose whole subject the reading has placed in a care home is a visit, not a
          # border: the word "bring" is the only thing this row and that line have in common
          guard=lambda understood: not _a_visit_to_a_home(understood),
          # the bare "bring"/"take" in the key would otherwise take the food that comes the other
          # way: meat, dairy and plants are a customs question with a different answer, and a
          # "can i bring my dog to france" line is not an allowance line at all
          # the airport's own list is the other side of the same verb: nothing you can carry
          # through security is a customs allowance, so the security words hold this row down
          avoid=("through security", "security", "hand luggage", "cabin bag", "cabin bags",
                 # "they keep borrowing my tools and never bring them back" has the bare "bring"
                 # and the bare "back" of the key and nothing else the allowance is about: what
                 # somebody hands back is the family file's line, not a customs table
                 "keeps borrowing", "keeps taking", "borrows my", "borrowing my", "borrowed my",
                 "lends out", "never brings it back", "never bring them back",
                 "never brings them back", "never gives it back", "never give them back",
                 # "what should i bring her" after "my mum moved into a home last month" is a
                 # visit, and the only word in it that means anything to this row is "bring":
                 # the reading has already said the whole line is about that visit
                 # (`care_home`, shape "bring"), and the bring-to-the-home answer is the one it
                 # was asking for.
                 "banned", "confiscated", "scanner", "scanned", "liquid", "liquids",
                 "cheese", "cheeses", "meat", "meats", "ham", "bacon", "sausage", "sausages",
                 "milk", "butter", "cream", "yoghurt", "yogurt", "eggs", "food", "foods",
                 "sandwich", "sandwiches", "fruit", "vegetables", "veg", "plants", "plant",
                 "seeds", "flowers", "bulbs", "potato", "potatoes", "my dog", "my cat", "pets",
                 "medicine", "medicines", "prescription", "cash", "how much money", "currency",
                 # A place in this country is not a border: "can i bring my own alcohol to a
                 # restaurant" was answered with 4 litres of spirits, because the only travel
                 # word in it was "bring". The same list is on the meat-and-dairy row, which took
                 # "can i bring my own food to a restaurant" for the same reason.
                 # pay is the other "take home": "my take home pay is less" met "take home" and
                 # "home" and got the customs table, so the pay words hold this row down
                 "take home pay", "net pay", "my pay", "payslip", "pay slip", "wages",
                 "salary", "income", "tax code",
                 "restaurant", "restaurants", "cafe", "cafes", "café", "the pub", "pub lunch",
                 "cinema", "theatre", "theater", "gig", "concert", "festival", "party",
                 "wedding", "birthday", "barbecue", "bbq", "picnic", "office", "at work",
                 "to work", "school", "college", "university", "hospital", "ward", "appointment",
                 # an ordinary building named in full: "can i bring food into the library" kept
           # nothing after the guard let go of it, and a shelf of books is as everyday a
           # destination as an office
           "library", "libraries", "into the library", "the canteen", "staff room",
           "hotel room", "my hotel", "the hotel", "in the hotel", "airbnb", "campsite",
                 "football", "match", "church", "funeral",
                 # "how much more will i take home" is a pay question, not a customs one: "take
                 # home" is in this row's key and "how much" in the second group, so a pay rise
                 # met the customs table. The pay words stand this row aside and nothing
                 # travel-shaped does.
                 "pay", "payslip", "payslips", "salary", "wage", "wages", "rise", "raise",
                 "promotion", "overtime", "bonus", "tax code", "take home pay", "net pay",
                 "income tax", "national insurance", "employer", "employment",
                 # and the same line said with the other verb: "i bring home 2100 a month" is a
                 # wage, not a border crossing. The pay words above are only the nouns, so the
                 # amount and the period are what name a wage here, and no customs line counts
                 # its allowance in pounds a month.
                 "a month", "per month", "monthly", "a year", "per year", "a week", "per week",
                 "weekly", "an hour", "hourly", "after tax", "before tax", "gross")),
    # A bed for less: the same few levers answer every city.
    # A cheap weekend away is a plan, not a week of dinners: with the meal-plan entry holding
    # "week" and "cheap", "how do i plan a cheap weekend away" came back as the eight cheap foods
    # to buy. That entry now stands down on trip words, and this is where the line lands.
    entry("weekend-away",
          (("weekend away", "weekend break", "city break", "night away", "nights away",
            "mini break", "short break", "cheap weekend", "getaway", "days away",
            "couple of nights away", "two nights away"),
           ("cheap", "cheaper", "budget", "plan", "planning", "book", "booking", "where",
            "idea", "ideas", "afford", "organise", "organize")),
          ("Go the weekend after a bank holiday, or in the shoulder season, and book the train "
           "three or four weeks ahead with a railcard - it usually costs less than the petrol. "
           "Stay one town out from the famous one and travel in: a twenty-minute train is a few "
           "pounds and the same room is half the price. Two nights is plenty for a city, so pick "
           "one area to walk and one thing to go inside for, and eat the big meal at lunch, when "
           "set menus are cheapest. Two nights for two, with travel and a room, is about £250."),
          ask=("weekend away", "weekend break", "city break", "night away", "nights away",
               "mini break", "short break", "cheap weekend", "getaway", "days away",
               "couple of nights away", "two nights away"),
          # the food that goes in the weekend bag is the meal-plan question, not the trip
          avoid=("flights to", "cheap flights", "which city", "best city", "in the world",
                 "meal", "meals", "dinner", "dinners", "cook", "cooking", "food", "recipe",
                 "recipes", "lunch", "breakfast", "shop", "shopping", "supermarket")),

    # "how do i book a hotel cheaply" put the adverb where the key wanted the adjective, so the
    # commonest way of asking had no answer at all.
    entry("cheap-accommodation",
          (("cheap", "cheaper", "cheapest", "cheaply", "budget", "afford", "affordably"),
           ("accommodation", "hotel", "hotels", "somewhere to stay", "place to stay", "a bed",
            "guesthouse", "hostel", "hostels", "lodging", "room for the night")),
          ("Book direct with a small hotel or guesthouse once you know roughly where you want to "
           "be: a phone call often beats the price on the booking site, and it is the cheapest way "
           "in small towns. Hostels and apart-hotels win for a week, and a kitchen saves more than "
           "a lower nightly rate. Look at the total with tax and breakfast, not the headline."),
          avoid=("where should i stay", "which area", "best area", "where to stay",
                 "neighbourhood", "neighborhood", "rent", "mortgage", "buy", "flights", "flight")),

    # How far ahead to book a room had no answer of its own: "when should i book a hotel" and
    # "how far in advance do i book a hotel" both reached the entry about picking a good hotel,
    # which is a different question, and a wedding was a shrug. The plain "how do i book a hotel"
    # is still the pick-a-hotel answer: only the timing and the group are this entry's.
    entry("hotel-booking-when",
          # Not the bare word "wedding": a hotel row keyed on it answers the wedding itself -
          # "how many guests for a wedding" was four to six weeks' notice on booking a room.
          # Only the room shapes of a wedding are this row's.
          (("hotel", "hotels", "guesthouse", "guest house", "b&b", "hotel room", "a room",
            "rooms", "wedding guests", "wedding rooms", "the wedding party",
            "rooms for a wedding"),
           ("when should i book", "when do i book", "when to book", "how early", "how far in",
            "how far ahead", "how long before", "in advance", "weeks before", "months before",
            "book early", "book ahead", "last minute", "block of rooms", "for a wedding",
            "guests", "how many rooms")),
          ("Book the room as soon as the date is fixed if it is a weekend, a city or a wedding - "
           "four to six weeks ahead is enough for most trips, and three months or more for a "
           "popular place in summer or a bank holiday. Midweek and January are where last-minute "
           "hunting pays. If a booking site shows less than the hotel's own site, ring the desk: "
           "they usually match it, and the direct terms are better."),
          # a complaint, a dirty room, a cheap room and a cancelled booking are other answers
          avoid=("how many guests", "how many people", "guest list", "number of guests",
                 "how many to invite", "catering", "caterer", "the venue", "menu",
                 "complain", "complaint", "complaints", "dirty", "clean", "cleaned", "cleaning",
                 "bed bugs", "noise", "noisy", "rude staff", "cockroach", "cockroaches",
                 "cheap hotel", "cheap hotels", "cheaper hotel", "cheaper hotels", "cheaper room",
                 "cheap room", "cheapest", "budget", "somewhere to stay", "place to stay",
                 "cancel", "cancelled", "canceled", "refund", "refunded", "wifi", "wi-fi",
                 "address", "parking", "dog", "pets", "breakfast included",
                 # the wedding in the key is a room for the guests, and it also made this the
                 # answer to what to put in the envelope: "how much money should i give for a
                 # wedding" was told to book the room four to six weeks ahead. The present is
                 # the gift rows' question
                 "give", "giving", "as a gift", "as a present", "gift", "gifts",
                 # the music of a wedding is the entertainment rows' question: "songs for a
                 # wedding" was told to book the room four to six weeks ahead
                 "song", "songs", "music", "playlist", "band", "bands", "dj", "first dance",
                 "aisle", "register", "hymn", "hymns",
                 "present", "presents", "envelope", "how much money",
                 # What to wear to the wedding is the outfit entry's, not the room's: "is a
                 # jumpsuit ok for a wedding", "do i need a hat for a wedding" and "what should i
                 # wear to a wedding as a guest" all reached this entry on the phrase "for a
                 # wedding" and got four to six weeks ahead and a block of rooms.
                 "wear", "wearing", "outfit", "outfits", "dress", "dresses", "jumpsuit",
                 "jumpsuits", "hat", "hats", "fascinator", "shoes", "heel", "heels", "suit",
                 # and the small things put on with it: "which socks for a wedding" named the
                 # occasion and nothing else this row keys, so it was told when to book a room.
                 # The sock has its own card in clothing.py.
                 "sock", "socks", "tie", "ties", "waistcoat", "braces", "cufflinks",
                 "suits", "tie", "colour", "color", "dress code", "black tie",
                 # the same ask said with the verb: "what should i put on for a wedding"
                 "put on", "putting on", "clothes")),

    # "can i drink the water in spain" puts the water second, so the pair is any water word with
    # the drinking words: the callable turns down the bottle, the hot drink and the daily amount.
    # A named country with a row in WATER decides the answer, so this entry is nudged over the
    # general "is it safe to drink" answers: "is the water safe to drink in thailand" was coming
    # back as the drink-driving rule. The key is two common words, so the same bias keeps it ahead
    # of the entries that share them.
    # Not bare "ice" in the second part: "why does ice float on water" is the physics entry.
    entry("tap-water-abroad", (("water", "tap water", "ice"),
                               ("safe", "drink", "drinking", "ok", "okay", "fine",
                                "abroad", "holiday",
                                # the same tap at home: is it safe, and why is it brown
                                "brown", "rusty", "chlorine", "tastes", "taste", "smells of",
                                "bottled", "mains")),
          _tap_water, bias=2,
          # how much to drink in a day is the hydration figure, not a place: "should i drink more
          # water" and "how much water should i drink" both reached this entry's two plain words.
          avoid=("more water", "enough water", "glasses", "hydrated", "dehydrated",
                 "how much water", "litres", "liters",
                 # water with a meal is a myth about digestion, not a place to drink: "is it bad
                 # to drink water with meals" reached this entry on "water" and "drink"
                 "with meals", "with food", "with my meal", "with a meal", "during meals",
                 "before a meal", "before meals", "after a meal", "after meals", "while eating",
                 "float", "floats", "density", "freeze", "freezes", "frozen",
                 # "my tooth hurts when i drink water" is a tooth line: the water is the thing
                 # that hurts, not the subject of the question. The dental rows answer it.
                 "tooth", "teeth", "gums", "gum", "enamel", "dentist", "dentists",
                 "twinge", "toothache", "hurts to drink", "hurts when i drink",
                 # watering the garden is not a place to drink: "how do i keep my pots watered
                 # while im on holiday" reached this row on "water" and "holiday". Not a bare
                 # "watering" or "watered": an avoid word matches loosely, so its root "water"
                 # stands this row down on every tap-water line.
                 "pots", "pot pots", "plant pots", "plants", "garden",
                 "water the plants", "while im away", "while i am away", "greenhouse")),

    # --- the bag, and the car you pick up at the other end -------------------
    # "How much data do I have left?" is about a phone, not a suitcase, so the tech entry keeps
    # the data lines and this one takes only the words for luggage.
    entry("baggage-allowance",
          (("luggage", "baggage", "cabin bag", "hand luggage", "checked bag", "hold bag",
            "suitcase", "rucksack", "backpack", "backpacks", "daypack", "day pack",
            # "what happens if my bag is too heavy" is the same question asked from the other side
            "bag", "bags",
            # an airline names the rules to check: "what size bag can i take on ryanair" was a
            # hedge, and the airline is not the subject of anything else in this file
            "ryanair", "easyjet", "easy jet", "jet2", "wizz", "wizz air", "british airways",
            "tui", "aer lingus", "vueling", "norwegian", "loganair"),
           ("allowance", "limit", "how much", "how many", "weight", "size", "kg", "heavy",
            "take", "pack", "checked", "cabin", "hold", "big", "large", "how big", "how large",
            "dimensions", "measurements", "weigh", "weighing", "biggest",
            # a yes-or-no about the bag itself: "is a backpack ok as hand luggage" has no word
            # from the group above, so the soft words count as the shape of the ask
            "ok", "okay", "fine", "allowed", "suitable", "too heavy", "overweight", "excess",
            "over", "problem", "hand", "carry", "on the plane", "on a plane")),
          "Check the airline's own allowance on your booking: a cabin bag is usually around 55 x 40 "
          "x 20 cm and 7 to 10 kg, and a checked bag around 20 to 23 kg. Weigh the bag at home, "
          "because excess weight at the airport is expensive and adding a bag online beforehand is "
          "much cheaper. On a connecting flight the strictest airline's limit applies.",
          # the shape of the ask is a number - a weight, a size, a limit. "pack" and "take" were
          # in this group, and they are what every packing line says: "how do i pack a suitcase
          # tightly" and "how do i pack a rucksack" were both sent the allowance card, which
          # answers a question about kilos to somebody asking how to fit a week into a case.
          ask=("allowance", "limit", "how much", "how many", "weight", "size", "kg", "heavy",
               "big", "large", "how big", "how large", "dimensions", "measurements", "weigh",
               "weighing", "biggest", "what", "can i", "can we", "is there", "does",
               # the bag itself, asked as "is a backpack ok" or "what if my bag is too heavy"
               "ok", "okay", "allowed", "fine", "suitable", "count", "counts", "too heavy",
               "overweight", "excess", "over", "problem",
               # "is a backpack ok as hand luggage" has no "can i" in it, and the soft words
               # ("ok", "allowed", "fine") are normalised away before the ask list is read
               "hand", "luggage", "baggage", "backpack", "rucksack", "carry"),
          avoid=("cost", "price", "buy", "sale", "lost", "stolen", "damaged", "delayed",
                 "data", "phone", "mobile", "razor", "liquid", "liquids", "medicine",
                 "medication", "knife", "scissors", "battery", "batteries", "lighter",
                 "security", "train", "coach", "bus", "ferry", "cruise")),
    # The cabin-bag rules: what you may carry on the plane. A size or weight question is the
    # allowance row above and stays there, which is what these avoid words are for.
    entry("cabin-bag-rules",
          (("hand luggage", "cabin bag", "carry on", "carry-on", "hand baggage", "cabin",
            "on the plane", "on a plane", "on board", "through security", "at security",
            "the plane", "plane", "fly with", "take on the plane", "suitcase", "hold",
            "checked bag", "holdall"),
           ("take", "taking", "bring", "bringing", "carry", "carrying", "allowed", "allow",
            "permitted", "not allowed", "cant take", "can't take", "cannot take", "can i get",
            "am i allowed", "prohibited", "banned", "forbidden", "confiscated", "in my bag",
            "my bag", "pack", "packing", "put in", "go in", "goes in", "bring back",
            # the thing itself, so the row names it and outranks a neighbour that shares one
            # of its words: "can i take a power bank on a plane" reached a tariff row on "power"
            "razor", "razors", "scissors", "tweezers", "penknife", "knife", "corkscrew",
            "lighter", "matches", "power bank", "power banks", "battery", "batteries",
            "screwdriver", "tools", "deodorant", "perfume", "toothpaste", "sun cream",
            "medicine", "tablets", "food", "sandwiches", "bottle", "liquid", "vape",
            "nail scissors", "clippers", "multi tool", "swiss army")),
          _cabin_rules, bias=2, guard=_cabin_guard,
          ask=("take", "bring", "carry", "allowed", "banned", "not allowed", "can i",
               "am i", "pack", "put"),
          # the size and the weight are the allowance row's question, and a shopping line about
          # buying a bag is not a flight at all
          avoid=("size", "big", "large", "how big", "how large", "dimensions", "measurements",
                 # the bag itself is the allowance row's question: "is a backpack ok as hand
                 # luggage" is a yes-or-no about kilos and centimetres, and this row stands down
                 # and let it through (its guard already said so, but by then it had the turn)
                 "backpack", "backpacks", "rucksack", "rucksacks", "daypack", "day pack",
                 "is a bag", "my bag ok", "bag allowed",
                 "weight", "weigh", "weighing", "heavy", "allowance", "limit", "kg", "kilo",
                 "kilos", "kilogram", "how much does", "how many kilos",
                 "lost", "damaged", "delayed", "buy", "cheap", "cost", "price", "sale",
                 "repair", "wheel", "zipper", "zip", "handle", "lock", "padlock", "straps",
                 "train", "coach", "bus", "ferry", "cruise", "moving house",
                 # answered already, and better, by vape-on-a-plane, fly-with-medicine and
                 # flight-food: a named thing is not enough to take their turn
                 "vape", "vapes", "vaping", "e-cigarette", "e-cigarettes", "ecig", "ecigs",
                 "eliquid", "e-liquid", "nicotine",
                 "medicine", "medicines", "medication", "medications", "insulin", "inhaler",
                 "inhalers", "epipen", "epi-pen", "epipens", "tablets", "pills", "prescription",
                 "paracetamol", "ibuprofen", "aspirin", "painkillers", "antihistamine",
                 "hayfever", "hay fever", "antibiotics", "inhalers",
                 "food", "sandwich", "sandwiches", "snack", "snacks", "lunch", "picnic",
                 # the tray itself - shoes, belts, the scanner - is airport-security's answer
                 "shoes", "shoe", "belt", "boots", "scanner", "pat-down", "pat down", "trays",
                 "tray",
                 # a pram, a pet or an instrument has its own answer, or none, and the banned
                 # list is neither: it is about what the scanner takes off you
                 "pram", "prams", "pushchair", "pushchairs", "buggy", "stroller", "car seat",
                 # a small child on a plane is the travelling-with-a-baby row's question, not
                 # this one: "taking a toddler on a plane" was answered with the banned list
                 # because the row keys "on a plane" and "taking". "baby" and "babies" stay
                 # out of this fence, because "can i take baby formula on a plane" and "baby
                 # milk through security" are this row's own question.
                 "toddler", "toddlers", "infant", "infants", "newborn", "newborns",
                 "dog", "dogs", "cat", "cats", "pet", "pets", "rabbit", "hamster", "bird",
                 "parrot", "wheelchair", "mobility scooter", "crutches",
                 "guitar", "violin", "cello", "instrument", "instruments", "drums", "keyboard",
                 "bike", "bikes", "bicycle", "surfboard", "skis", "ski", "snowboard",
                 "paddleboard", "kayak")),
    # "how much does it cost to put a bag in the hold" was the dried-beans cupboard card and
    # "how much does a checked bag cost" was the 5p carrier-bag charge.
    entry("flight-bag-fee",
          (("checked bag", "checked bags", "checked baggage", "hold bag", "hold luggage",
            "checked luggage", "checked in bag", "bag in the hold", "baggage fee", "bag fee",
            "bag fees", "extra bag", "second bag", "suitcase in the hold"),
           ("cost", "costs", "price", "priced", "how much", "pay", "paying", "paid", "fee",
            "fees", "charge", "charged", "worth", "cheaper", "cheapest", "add a bag",
            "book a bag", "cost to", "how much does", "how much is", "put a bag",
            "extra luggage", "baggage")),
          "Booked online with the ticket, a 23kg bag is usually £20 to £45 each way on a budget "
          "airline, and £50 to £65 if you add it at the airport desk. A heavier bag costs more again, "
          "so weigh it at home. Compare that with a fare that includes a bag before you book: the "
          "cheap headline fare plus a suitcase often costs more than the fare that already has one.",
          bias=2,
          avoid=("reusable", "allowance", "how many kilos", "how much weight", "how heavy",
                 "how big", "how large", "size", "dimensions", "weight limit", "carrier", "supermarket", "for life", "shopping", "plastic bag",
                 "bin bag", "dog", "poo", "leaf", "leaves", "vacuum", "hoover", "storage",
                 "sleeping bag", "tea bag", "beans", "lentils", "pulses", "rice")),
    entry("car-hire",
          (("hire a car", "hire car", "rent a car", "rental car", "car hire", "car rental"),
           ("cost", "cheap", "how much", "book", "insurance", "deposit", "young driver",
            "age", "fuel", "abroad", "one way", "worth",
            # the deposit is held on a card, so "how do i hire a car without a credit card" is
            # this row's question - it was the chargeback card, because a credit card in a line
            # was read as a disputed payment
            "credit card", "debit card", "without a card", "no card", "card",
            "cost to hire", "cost of hiring", "cost of hire", "price of hire")),
          "Book early and compare the total with insurance included, not the headline daily rate. "
          "Check the excess and whether your own policy or a credit card already covers it. Pay the "
          "deposit on a credit card: it is usually a few hundred pounds or euros held on the card and "
          "released when you return the car. Photograph every panel before you drive off, return it "
          "full-to-full, and remember that a young or second driver usually costs extra.",
          avoid=("buy", "buying", "sell", "selling", "lease", "leasing", "my own car", "repair",
                 "breakdown", "parking", "mot", "tax")),
    # A day out on a hill wants water, food and a pace, not the six-glasses-a-day answer and not
    # the flight-liquids one: both of those took "how much water should i take on a hike" because
    # they own the word water.
    # A walk somebody can actually do is not a kit question, and it was answered as one: "my dad
    # cant walk far so we need somewhere flat" and "i cant walk far what do i need" both got the
    # walking-kit card (layers and a waterproof) from clothing.py, which keys `walk` and `need`.
    # hike-day already stands down for "cant walk"; this is the row those lines are for, so the
    # words that say a walk is short or hard going are a subject here rather than a veto.
    entry("an-easy-walk",
          (("walk", "walks", "walking", "stroll", "strolls", "outing", "day out",
            "somewhere to go", "where can we go", "where can i go", "place to walk",
            "somewhere flat", "flat walk", "easy walk"),
           # the limitation, or the ground that makes a walk easy: either one is the subject
           ("flat", "level", "easy", "gentle", "accessible", "wheelchair", "wheelchairs",
            "mobility", "scooter", "cant walk", "can't walk", "cannot walk", "walk far",
            "walking far", "slow walker", "bad knees",
            "bad hip", "bad back", "elderly", "keep up", "tires", "tired", "manage",
            "can manage", "manageable", "slow", "slowly", "steady", "pensioner", "nan",
            "granny", "grandma", "grandad", "buggy friendly")),
          "Go for a canal towpath, a country park or a flat riverside path: wide, level, benches "
          "along it and nothing to climb over, which is what a short walk needs. Check the surface "
          "and the slope on the site's own page before you set off, because a walk advertised as "
          "circular can still hide a stile or a flight of steps, and ring ahead if someone uses a "
          "wheelchair - big attractions, National Trust and English Heritage places among them, "
          "lend one for free if it is booked a day or two in advance. For someone who tires "
          "quickly, plan a there-and-back of half a mile with a seat at the turning point and pace "
          "it bench to bench rather than by distance. A stick helps if a hip or knee is the "
          "trouble: the handle wants to reach the crease of the wrist with the arm hanging down, "
          "it goes in the hand opposite the sore side, and the tip gets a new ferrule once it has "
          "gone smooth.",
          # a dog walk, a pram and a food-or-water question are other rows' answers: the pack and
          # the waterproof belong to the kit, which is the question this row takes away from
          avoid=("dog", "dogs", "puppy", "pram", "pushchair", "baby", "toddler", "calories",
                 "pedometer", "marathon", "parkrun", "race", "km", "miles", "water",
                 "waterproof", "boots", "jacket", "pack",
                 # whether walking is good or bad for a sore knee is a body question, and a
                 # symptom in the line is never a request for somewhere to walk
                 "hurts", "hurt", "ache", "aches", "aching", "pain", "painful", "sore",
                 "injury", "injured", "is it safe", "is it ok", "ok to walk", "should i walk",
                 "good for", "bad for", "make it worse", "damage",
                 # a holiday, a flight and getting around a city are
                 # away-with-someone-who-cannot-walk-far in this file, which is the better
                 # answer for them: this row is the walk on the day, not the trip
                 "holiday", "holidays", "away", "abroad", "trip", "trips", "flight", "flights",
                 "hotel", "hotels", "airport", "airports", "plane", "planes", "rollator",
                 "passenger", "abroad"),
          # "he can't walk far" on its own is a fact about a companion that the bot should note
          # and not answer: the reply is for a line that asks where to go, what to look for or
          # what to take, which is what these ask forms are. A statement about somebody's legs
          # carries the limitation and nothing else, and got a list of canal towpaths without it.
          ask=("how much", "how far", "how long", "what should i", "what do i", "what can i",
               "what to take", "what to wear", "what to bring", "what can we do",
               "where can i", "where can we", "where should", "where is", "is there a",
               "is there any", "are there", "anywhere", "somewhere", "can we go", "can i go",
               "can i take", "can we take", "we need", "i need", "looking for", "is it ok",
               "flat walk", "easy walk", "gentle walk", "short walk", "level walk",
               "accessible walk", "slow walk", "a walk", "day out", "outing",
               "things to do"),
          # "flat" is in the key twice over: it is the ground a walk is easy on and it is the
          # flat a person lives in, so "how do i clear the junk out of my flat" was answered
          # with "a canal towpath, a country park or a flat riverside path". The home is never
          # the ground, so this row stands down for it.
          guard=_not_the_flat_the_ground,
          bias=2),
    entry("hike-day", (("hike", "hiking", "hillwalk", "hill walk", "hill walking", "fell walk",
                        "trek", "trekking", "rambling", "ramblers", "day walk", "long walk",
                        "walks in the hills", "mountain walk", "munro", "ridge walk", "coast path",
                        "walking", "walk", "walked"),
                       ("water", "drink", "eat", "food", "snack", "snacks", "lunch", "carry",
                        "pack", "take", "bring", "fuel", "energy", "hungry", "kilos", "weight",
                        "how much water", "how much food", "how much liquid",
                        # a quantity asked for in litres is the same day-out question, and the
                        # line often names no water: "how many litres do i need for a long walk".
                        "litre", "litres", "liter", "liters", "how many litres",
                        "how much to drink")),
          _hike_day,
          # A walk to the shops, a dog, a pram, a flight and a water bill are other questions.
          avoid=("dog", "puppy", "pram", "pushchair", "baby", "toddler", "flight", "flying",
                 "airport", "hand luggage", "shop", "supermarket", "toilet", "nap", "sleep",
                 "bill", "meter", "leak", "boiler", "kettle", "plant", "plants", "bath",
                 # Someone who cannot walk far is not asking what to carry up a hill.
                 "cant walk", "can't walk", "cannot walk", "cant walk far", "walking far",
                 "mobility", "wheelchair", "disabled", "sticks", "slow walker"),
          # The day out is an answer to a how-much question; "she can't walk far" on a Rome
          # trip carries a walking word and would otherwise borrow it.
          ask=("how much", "how many", "what should i", "what do i need", "what to take",
               "what to bring", "what do i take", "what do i bring", "what should i take",
               "what should i bring", "what to pack", "should i take", "should i bring",
               "need to", "snack", "snacks", "food", "eat", "water",
               "drink", "drinking", "carry"),
          # "a day's walking" and the step target both key a walking word and a how-much word, and
          # the water in the line is what makes it the hill question.
          bias=1,
          # People type "hike" wrong far more than they type "walk" wrong, and a misspelt line
          # was reaching nothing.
          slips=("hikeing", "hikingg", "hikeing", "hikin", "hikes", "hiike", "hikey", "hikking",
                 "treking", "trecking", "rennwalking", "ramblin", "hillwalking")),
    # "why do i always catch a cold when i fly" said "fly", which was not a word of the key, so
    # the cheap-fares answer took it: the key word here is the verb as well as the noun.
    entry("ill-on-a-plane", (("plane", "planes", "flight", "flights", "flying", "fly", "flew",
                              "airplane", "aeroplane", "cabin"),
                             ("sick", "ill", "cold", "bug", "sniffles", "cough", "germs",
                              "catch", "avoid", "pick up")),
          "Wipe the tray table, the armrest and the seat-back pocket, which are cleaned rarely, and "
          "keep your hands off your face: the germs in a cabin come from the surfaces more than the "
          "air, which is filtered. Drink water rather than alcohol or coffee, take a window seat "
          "away from the aisle, and wear a mask on a packed winter flight, which is the single "
          "biggest thing you can do.",
          avoid=("travel sick", "travel sickness", "motion", "dizzy", "nauseous", "sick bag",
                 "vomit", "throw up", "ears", "jet lag", "jetlag", "scared", "afraid", "nervous")),

    # --- the bag that did not come out, the coach, and staying well ----------------
    # The allowance entry above turns down "lost", so this one owns a bag that did not arrive.
    # The ask has to be a question: "my bag is lost" is a statement and gets a person's sympathy,
    # not a list of what to do.
    entry("lost-luggage",
          (("suitcase", "suitcases", "bag", "bags", "luggage", "baggage", "case", "rucksack"),
           ("didnt arrive", "didn't arrive", "did not arrive", "hasnt arrived", "hasn't arrived",
            "never arrived", "not arrived", "went missing", "is missing", "gone missing",
            "lost", "lost my bag", "stolen", "left behind", "delayed", "was delayed",
            "still not here", "still hasnt arrived", "on the carousel")),
          ("Report it at the airline's desk in the baggage hall before you leave, with the bag tag "
           "and your boarding pass, and do not go home without a written report and a reference "
           "number: that number is what every later claim and refund hangs on. Ask what they will "
           "pay for clothes and toiletries in the meantime and keep every receipt. Most bags turn "
           "up within 24 to 48 hours; if it has not after 21 days, claim for it as lost."),
          ask=("what do i do", "what should i do", "what happens", "where do i", "how do i",
               "can i claim", "claim", "compensation", "report", "help", "now", "anything",
               "is it", "will i", "do i get", "who do i"),
          # A bag taken off you in the street is a police matter, not an airline one, and a
          # damaged bag needs the damage noted on the same report rather than a lost-bag script.
          avoid=("allowance", "limit", "how much", "weight", "kg", "cabin", "hand luggage",
                 "pack", "carry on", "data", "phone", "razor", "liquids", "lock", "padlock",
                 "on holiday", "pickpocket", "pickpocketed", "robbed", "mugged", "wallet",
                 "passport", "money", "damaged", "damage", "torn", "broken zip")),
    # Motion sickness is not the same as feeling ill on a plane: what helps is where you sit and
    # what you look at, and for a child the dose is a pharmacist's question, not mine.
    entry("travel-sickness",
          (("travel sick", "travel sickness", "motion sickness", "car sick", "carsick",
            "carsickness", "sea sick", "seasick", "seasickness", "motion sick",
            "sick in the car", "sick on the boat", "sick on a boat", "sick on the ferry",
            "sick on the plane", "sick on the bus", "dizzy in the car"),
           ("what can i", "what helps", "how do i", "prevent", "avoid", "stop", "help",
            "medicine", "tablets", "tablet", "give", "child", "children", "kid", "kids",
            "toddler", "my son", "my daughter", "pills", "bands")),
          ("Sit facing forward, as far forward and as low as you can, look at the horizon rather "
           "than a screen or a book, and get fresh air: those four do more than anything you can "
           "buy. Eat something plain before you go, not a big meal, and stop when you can. For a "
           "child ask a pharmacist which antihistamine suits their age and weight, and give it an "
           "hour before you set off, because the doses are not the adult ones."),
          avoid=("fever", "temperature", "vomiting", "diarrhoea", "diarrhea", "not eating",
                 "chest", "asthma", "breathing", "rash", "croup", "ear infection")),
    # A coach is the cheap way between two cities, and it is priced like a plane: book ahead.
    entry("coach-travel",
          (("coach", "coaches", "megabus", "national express", "flixbus", "bus"),
           ("book", "booking", "cheap", "cheaper", "cheapest", "cost", "how much", "how long",
            "luggage", "bags", "to ", "from ", "overnight", "airport")),
          ("Coaches are the cheapest way between two cities: booked two or three weeks ahead a "
           "long trip is often under 20 pounds when the train is over 60, and the overnight coach "
           "saves a hotel night as well. Book on the operator's own site or app, take the ticket "
           "on your phone, and put the big bag in the hold, which is included but has to be tagged. "
           "Arrive 15 minutes early: coaches leave on time and do not wait."),
          # "which is better the train or the coach" asks for the two weighed and the card is
          # the half of it that has a price, so a line that sets the coach against another way of
          # going is this row's question.
          ask=("book", "booking", "cheap", "cheaper", "cheapest", "cost", "how much", "how long",
               "to ", "from ", "overnight", "is it", "can i", "should i",
               "which is better", "which one", "vs", "versus", "compare", "difference",
               "or the train", "than the train", "train or"),
          # This is the plan-your-own-trip row: where to book and what to take. A child's fare on
          # a bus or a train is child-bus-travel's, and "how much is a child bus fare" was getting
          # "coaches are the cheapest way between two cities" through `bus` and `how much`.
          avoid=("tour bus", "sightseeing bus", "hop on", "school bus", "double decker",
                 "seat belt", "driving", "park", "parking", "route", "timetable", "live",
                 "running late", "cancelled",
                 "child", "children", "kids", "kid", "my son", "my daughter", "under 5s",
                 "under fives", "5 year old", "4 year old", "child fare", "child ticket",
                 # The row keys the bare word "bus" against "to ", so every bus question with a
                 # "to" in it was priced as a coach between two cities: "who do i complain to
                 # about a bus driver" was told coaches are cheaper than trains, and a route or
                 # a lost bag would have got the same. A complaint, a route and a lost bag are
                 # other answers, so the row stands down for them.
                 "complain", "complaint", "complaints", "report", "driver", "drivers",
                 "bus driver", "bus company", "bus operator", "rude", "shouted",
                 "left my bag", "lost property", "left it on", "left something on",
                 "which bus", "what bus", "bus route", "routes", "bus stop", "bus number",
                 "track", "tracking", "live times", "how often", "how far", "nearest",
                 "wheelchair", "pram", "pushchair", "mobility scooter", "school run")),
    # Staying well is a different question from whether the tap water is safe: it is the food,
    # the ice, the fruit, and what to carry in case it goes wrong anyway.
    entry("stay-well-abroad",
          (("avoid", "not get", "dont get", "don't get", "prevent", "stay well", "not catch",
            "get sick", "got sick", "food poisoning", "delhi belly", "bad stomach",
            "tummy bug", "stomach bug", "runs", "diarrhoea", "diarrhea",
            "safe to eat", "is it safe", "worth eating"),
           # The place has to be named. "food" alone is not one: the phrase in the first part
           # is "food poisoning", so a line that only says that handed the entry the word it was
           # keyed on and nothing else - "how do i defrost a chicken without giving myself food
           # poisoning" was answered with street-food advice for a trip abroad.
           ("abroad", "on holiday", "travelling", "traveling", "in mexico", "in india",
            "in egypt", "in thailand", "in turkey", "in morocco", "in peru", "in kenya",
            "in bali", "there", "street food", "eating out", "ice", "salad", "fruit",
            "water")),
          ("Eat where it is busy and freshly cooked, and have it hot: a queue and a hotplate are "
           "better signs than a clean table. Have bottled or filtered water and the ice made from "
           "it, peel your own fruit, and skip the raw salad that a kitchen has washed in tap water. "
           "Carry rehydration sachets and a hand gel, and check the vaccinations and malaria advice "
           "for that country about six weeks before you go."),
          # The water questions belong to tap-water-abroad; this entry is about food and habits.
          avoid=("pregnant", "pregnancy", "baby", "toddler", "child", "children", "asthma",
                 "allergy", "allergies", "tablet", "tablets", "medicine", "medication",
                 "insurance", "compensation", "flu", "covid", "vaccine", "vaccination",
                 "drink the water", "drinking water", "tap water", "water safe",
                 # "we keep running out of hot water" is the plumbing, not the tap water of a
                 # country: "runs" is a form of "running" and "water" sits in this row's place
                 # part, so a house with no hot water was told to eat where it is busy. The
                 # home rows own these lines; this one stands down.
                 "hot water", "running out of hot water", "run out of hot water", "boiler",
                 "stopcock", "immersion", "cylinder", "radiator", "radiators", "heating",
                 "kettle", "shower", "bath", "plumber", "tank", "no hot water",
                 # a card is money, not food: "is it safe to use my card abroad" reached the
                 # street-food answer because "is it safe" and "abroad" are all it had
                 "card", "cards", "wallet", "cash", "money", "atm", "atm machine", "currency",
                 "euros", "dollars", "pounds", "bank", "pay by card",
                 # "rinse the lentils until the water runs clear" is a kitchen instruction: the
                 # "runs" in the first part and the bare "water" in the place part were enough
                 # for it. Salad, fruit and the water itself stay here, because those are the
                 # street-food questions; the pulses and the phrase about the water are not.
                 "lentils", "chickpeas", "quinoa", "rice", "pasta", "spaghetti", "noodles",
                 "greens", "water runs clear", "runs clear")),
    # --- before you set off, and the paperwork nobody thinks of until it is late ------
    # The airport has its own entry (airport-arrival). A ferry, a cruise and the tunnel do not:
    # they close the doors on a timetable, and the answer is the number the operator publishes.
    entry("departure-check-in",
          (("check in", "checking", "check-in", "arrive", "get there", "be there", "how early",
            "how long before", "how late"),
           ("cruise", "ferry", "boat", "eurostar", "tunnel", "le shuttle", "port", "terminal",
            "coach station", "train station", "station")),
          ("Check your operator's own figure the day before, because it is the one that counts: a "
           "cruise wants you at the terminal two to three hours before, a ferry an hour with a car "
           "and about thirty minutes on foot, and Eurostar asks for 75 to 90 minutes. Boarding "
           "closes before departure and a ship or a coach will not wait, so aim to be there early "
           "and take a book rather than cutting it fine."),
          ask=("how early", "how long before", "how late", "what time", "when should", "should i",
               "do i need", "check in", "checking", "arrive"),
          avoid=("airport", "flight", "plane", "fly", "bag drop", "hotel", "check out",
                 "checkout", "hand luggage", "online check in")),
    # Checking in is a step with a deadline, and the deadline belongs to the airline rather than
    # to the airport: "how do i check in for a flight" passed on every entry and was a shrug.
    entry("flight-check-in",
          (("check in", "checking in", "check-in", "checkin", "boarding pass"),
           ("flight", "flights", "plane", "airline", "airport", "flying", "easyjet", "ryanair",
            "jet2", "online", "app", "before")),
          ("Check in online as soon as it opens, usually 24 to 48 hours before a short-haul flight "
           "and up to 72 on some, and save the boarding pass into your phone wallet as well as "
           "your email: a screenshot works when the signal does not. Have your passport details "
           "to hand. If you are checking a bag, drop it before the airline's cut-off, which is "
           "usually 45 to 60 minutes before departure and a full two hours at some airports, and "
           "if you would rather check in at the desk, get there about three hours before the "
           "flight: the desks close on that same timetable, queue and all."),
          ask=("how do i", "how to", "how can i", "what do i", "do i", "should i", "can i",
               "where do i", "when do i", "when should", "what time",
               # the fragment with no verb is the same ask: "check in online for a flight" was a
               # "say more if it helps" prompt. The past tense is not here, so "i checked in for
               # my flight" is not an ask.
               "check in", "check-in", "checkin", "checking in"),
          # a hotel, a cottage and a ferry each have their own check-in, and a checked bag's fee
          # is the baggage row's question
          avoid=("hotel", "check out", "checkout", "cruise", "ferry", "eurostar", "campsite",
                 "holiday cottage", "airbnb", "villa", "car hire", "hire car", "self catering",
                 "guest house", "bed and breakfast", "how much", "cost", "price", "fee", "fees",
                 "weight", "weigh", "allowance", "hand luggage", "cabin bag", "extra"),
          ),
    # A stopover is not automatically kinder to the body clock: a four-hour wait in an airport is
    # worse than none, and a night in a bed is better.
    entry("stopover-jet-lag",
          (("stopover", "stop over", "layover", "connecting flight", "connecting", "change planes",
            "breaks up", "break up"),
           ("jet lag", "jetlag", "jet-lagged", "body clock", "tired", "sleep", "help", "better",
            "worse", "should i", "worth it")),
          ("A stopover only helps if you can sleep in a bed: a night in a hotel halfway resets you "
           "gently, while a four-hour wait in an airport at 3am just breaks the journey. If you "
           "are stopping anyway, take the wait in daylight at the far end and set your watch to "
           "the destination as you board the last flight, then sleep on that leg if it is night "
           "there."),
          avoid=("flight cancelled", "missed my connection", "short connection", "bag",
                 "luggage", "hotel near", "airport hotel")),
    # The words on a booking are a vocabulary of their own, and the ones people meet on a cheap
    # fare are the ones nobody explains: a layover is a wait, a stopover is a night, and a
    # flexible ticket is the one you can change.
    entry("layover-meaning",
          (("layover", "layovers", "a layover", "stopover", "stop over", "stopovers",
            "connecting flight", "connecting flights", "my connection", "our connection",
            "flight connection", "connection flight", "connection time", "connection at",
            "connection between flights", "how long is my connection",
            "how long does a connection", "connection need", "connection needs",
            "how long between flights", "connection tight", "time between flights",
            "transit at the airport", "airside transit"),
           ("what", "whats", "what is", "mean", "means", "explain", "difference", "different",
            "vs", "versus", "how long", "counts as")),
          ("A layover, or a connection, is the wait at an airport between two flights, and a "
           "stopover is the same thing when it is long enough to leave the airport, usually a "
           "night or more. A connection under about two hours on the same ticket is the airline's "
           "problem if the first flight is late, so the risk is a tight change, not a long wait. "
           "On two separate tickets you are on your own for a missed second flight, so leave "
           "three hours or more."),
          avoid=("missed my connection", "short connection", "jet lag", "body clock", "sleep",
                 "hotel near", "airport hotel", "bag", "luggage")),
    entry("flexible-ticket",
          (("flexible ticket", "flexible tickets", "flexi ticket", "flex fare", "flexible fare",
            "change my flight", "change the date"),
           ("what", "whats", "mean", "means", "worth", "cost", "how much", "does it",
            "difference", "explain", "refundable", "should i")),
          ("A flexible ticket is the fare that lets you change the date, usually for no fee or a "
           "small one, where a cheap fare charges £30 to £70 plus any fare difference to change "
           "and often nothing back if you cancel. It is worth it when the date might move: work, "
           "a hospital appointment, a family thing. Check whether the fare is changeable or "
           "refundable, because they are not the same, and buy the cheaper ticket plus travel "
           "insurance when the difference is more than the change fee."),
          avoid=("how do i change", "how can i change", "my flight was cancelled", "cancel my")),
    # Paperwork is the one thing a person cannot fix on the day, and the answer is always "the
    # country's own site, applied for early" plus the timings that are stable.
    entry("visa-timing",
          (("esta", "visa", "evisa", "e-visa", "entry permit", "etias", "entry requirements",
            "tourist card", "visa waiver"),
           ("need", "apply", "how long", "how much", "cost", "when", "before", "do i",
            "still", "valid", "how many days", "how early")),
          ("Apply on the country's own government site, never a paid lookalike, and apply early: "
           "an ESTA for the USA is valid two years and should be done at least 72 hours before you "
           "fly, while a visa for most countries is a few weeks, so start six to eight weeks out. "
           "Check the entry rules for your own passport and any country you change planes in, and "
           "keep the approval on your phone and printed."),
          avoid=("passport renew", "passport expire", "renew my passport", "driving licence",
                 "insurance", "job", "work permit", "student visa for my course", "university")),
    # A package or a do-it-yourself trip: the trade is protection and transfers against price.
    entry("package-or-diy",
          (("package holiday", "package deal", "package", "all inclusive", "book a package",
            "diy", "do it myself", "book it myself", "separately"),
           ("cheaper", "worth it", "better", "should i", "or", "which", "protect", "protection",
            "atol", "flights and hotel", "hotel and flights", "risk")),
          ("A package buys you protection and less admin: the flights, the transfer and the hotel "
           "are one booking, and if the operator fails you are covered and brought home. Booking it "
           "yourself is usually cheaper, especially for a city break where you want a flat rather "
           "than a hotel, but you carry the risk - so book the flight on a credit card and check "
           "the hotel's own cancellation terms. For a beach week with children, the package "
           "usually wins on the day something goes wrong."),
          avoid=("parcel", "delivery", "courier", "my package", "package arrived", "software",
                 "install", "python"),
          guard=_a_trip_to_arrange),
    # A pushchair on a plane is a free, gate-checked item on almost every airline, and the one
    # thing people get wrong is handing it over too early.
    entry("pram-on-a-plane",
          (("pram", "pushchair", "buggy", "stroller", "travel system", "car seat"),
           # The plane has to be named. The verbs - take, bring, allowed, charge, free - named
           # nothing on their own: a pushchair and "take" is "can i take a pushchair on the
           # bus", which was answered with the hold and the aircraft door.
           ("plane", "planes", "flight", "flights", "fly", "flying", "airline", "airlines",
            "airport", "gate", "hand luggage", "hold", "cabin", "check in", "checking in",
            "ryanair", "easyjet", "jet2", "tui", "british airways")),
          ("Almost every airline carries a pushchair free, but it goes in the hold rather than the "
           "cabin: keep it until the aircraft door, where it is tagged and taken down the steps, "
           "and pick it up on the jetty or at the baggage belt at the other end. A car seat can fly "
           "with you if you bought it a seat, and a bag over the pushchair saves the fabric. Ask "
           "for the airline's own rule in writing if you are checking it in at the desk."),
          avoid=("pram wheels", "pram tyre", "second hand pram", "which pram should i buy",
                 "pram for sale", "buggy board")),

    # A pushchair and a bus is not a pushchair on a plane. With the plane named properly, the
    # bus and train lines stood down to a shrug, and "can i take a pushchair on the bus" is an
    # everyday question with a plain answer: fold it, and the wheelchair space outranks it.
    entry("pushchair-on-the-bus",
          (("pushchair", "pushchairs", "pram", "prams", "buggy", "buggies", "stroller",
            "strollers", "travel system"),
           ("bus", "buses", "coach", "coaches", "train", "trains", "tube",
            "underground", "tram", "trams", "metro", "public transport", "on the bus",
            "on a bus", "on the coach", "on the train", "double decker")),
          ("On a bus or a coach it travels folded, so have it down and the child out of it before "
           "the doors open: a driver can refuse a pushchair that is still open, and the space by "
           "the door belongs to a wheelchair user first. On trains and the underground a folded "
           "pushchair is free and goes in the luggage rack, and most stations have a lift, so use "
           "that rather than the escalator. For a coach trip the buggy goes in the hold - tell the "
           "driver at the door so it is not loaded under the luggage."),
          avoid=("pram wheels", "pram tyre", "which pram should i buy", "pram for sale",
                 "buggy board", "second hand pram", "sling", "car seat", "cot", "carrycot")),

    # "How do i travel with a baby" is an everyday question with a concrete answer, and on main
    # it reached the older person's bus pass through the word travel. The plane and the car are
    # the two places people ask about, and the ears on take-off is the bit nobody expects.
    entry("travel-with-a-baby",
          (("travel", "travelling", "traveling", "fly", "flying", "flight", "plane", "holiday",
            "abroad", "long journey", "trip", "airport"),
           ("baby", "babies", "infant", "newborn", "toddler", "month old", "months old",
            "year old")),
          ("Book the leg around their nap, feed or give a dummy at take-off and landing so their "
           "ears clear, and take a sling for the airport and a change of clothes in your hand "
           "luggage. Most airlines fly a baby from about two weeks old, on your lap or in a booked "
           "bassinet seat, and a pushchair goes free in the hold. In the car they need their own "
           "car seat, rear-facing until they are 15 months, and a stop every couple of hours."),
          avoid=("crying", "cries", "screams", "wont sleep", "won't sleep", "teething", "feeding",
                 "milk", "formula", "nappy", "nappies", "vaccine", "vaccinations", "jab", "colic",
                 "car seat", "car seats", "which car seat", "pram", "pushchair", "buggy", "sling",
                 "sleep", "routine", "temperature", "fever", "sick", "reflux", "weaning",
                 "cot", "moses basket", "baby monitor",
                 # The answer is the plane and the car ("take-off and landing", "a stop every
                 # couple of hours"), so a bus or a train is somebody else's question: "can my 5
                 # year old travel on the bus" reads travel plus "year old" and this row answered
                 # with the ears on take-off.
                 "bus", "buses", "coach", "coaches", "tram", "trams", "tube", "underground",
                 "bus fare", "bus pass", "train ticket", "child fare", "school bus",
                 # "fly" is a verb here and a fly spray is a can: "is fly spray safe with a baby"
                 # was an answer about clearing their ears on take-off.
                 "fly spray", "insect spray", "bug spray", "mosquito spray", "wasp spray",
                 "air freshener", "aerosol", "the spray",
                 # A tent is not a plane either. "what do i need for a camping trip with a
                 # toddler" and "what do i pack for a weekend camping trip with a baby" were both
                 # answered with "feed or give a dummy at take-off and landing", because this row
                 # holds "trip" and every word for a small child, and it is biased ahead of the
                 # campsite's own list.
                 "camping", "campsite", "camp site", "camp", "tent", "tents", "under canvas"),
          # fly-with-medicine holds the airline words too and reaches "can i fly with a newborn"
          # through them, so the baby's own row has to be the one that wins it.
          bias=3),

    # A holiday with children is paperwork before it is a holiday, and on main nothing claimed it:
    # "can i take my kids to spain", "taking kids abroad" and "family holiday checklist" were
    # shrugs, and "what do i need to take my kids abroad" was answered with a sleepover packing
    # list for a night at somebody else's house. The four things that catch people out are the
    # same four whatever the country, so it is one row rather than one per destination.
    entry("family-trip",
          (("kids", "children", "child", "family", "the kids", "my son", "my daughter",
            "toddlers", "teenagers", "teens", "under 16", "under 5", "school age",
            # the whole phrase, because a line that says "family holiday" is this row's question
            # even when the only other words in it are a generic "what do i need" or "sort"
            "family holiday", "family holidays", "family trip", "kids holiday",
            "holiday with the kids", "kids abroad", "children abroad"),
           ("holiday", "holidays", "abroad", "spain", "france", "greece", "portugal", "italy",
            "turkey", "cyprus", "canaries", "trip", "travel with children",
            "sort anything", "need to sort", "what do i need", "do i need")),
          ("Four things, all before you book: a passport each, because a child's lasts five years "
           "and takes a few weeks to arrive, so do not book flights until it is in your hand; a "
           "free GHIC card each for Europe, one per person; seats together, so ask when you book, "
           "since a child under 12 is meant to sit with their adult; and travel insurance that "
           "names every child. If you are crossing a border without the other parent, take a "
           "signed letter from them saying you have their permission. Photograph every passport "
           "and keep the pictures on your phone."),
          avoid=("plane", "planes", "flight", "flights", "flying", "fly", "airport", "ears",
                 "take-off", "take off", "baby", "babies", "infant", "newborn", "pram",
                 "pushchair", "car seat", "booster", "car", "cars", "driving", "bus", "coach",
                 "train", "ferry", "cruise", "sleepover", "staying over", "stay over", "babysit",
                 "bedtime", "routine", "school", "term time", "unauthorised", "fine", "fines",
                 "sick", "ill", "fever", "diarrhoea", "vaccine", "vaccinations", "jab", "jabs",
                 "measles", "chickenpox", "insurance", "ghic", "ehic", "cost", "costs",
                 "how much", "cheap", "cheaper", "budget", "where to stay", "hotel", "hostel",
                 "suncream", "sunburn", "nappies", "nappy", "milk", "food", "dog", "cat", "pet",
                 "pets", "divorce", "custody", "court order", "access", "compass",
                 # What to put in the suitcase is the packing card's question, not this one's:
                 # "what should i pack for a child on holiday" was the packing list on main and
                 # this row took it, because a child word and a holiday word are all it needs.
                 "pack", "packs", "packing", "packed", "what to pack", "suitcase", "luggage",
                 # A country plus "kids" is a verdict question - "is spain good for kids",
                 # "which is better for kids spain or portugal" - and a passport checklist is no
                 # answer to it. Those punted on main, and punting is better than this card.
                 "good for kids", "good with kids", "good for children", "good with children",
                 "better for kids", "best for kids", "good for families", "good for a family",
                 "where should we go", "which is better", "which is best",
                 # The document itself is another row's question: a child's passport asked for,
                 # renewed, checked for time left or photographed is the passport card, and the
                 # four-things list is a worse answer to it ("my daughters passport runs out next
                 # month" lost the six-months rule). A checklist line likewise has its own card.
                 "passport", "passports", "visa", "visas", "renew", "renewing", "renewed",
                 "runs out", "run out", "expires", "expiring", "photo", "photos",
                 "checklist",
                 # An outing is not a holiday: "take them", "take the kids" and "bring them" were
                 # travel words, so a family word plus any trip out ("can i take my kids to the
                 # pub / a wedding / the cinema") reached the passport list. The destination
                 # words do the work on their own.
                 "pub", "wedding", "cinema", "park", "swimming", "soft play", "restaurant",
                 "birthday party", "funeral", "church", "school run",
                 # A holiday at home needs no passport, so the card must not answer one: a UK
                 # trip and a club are the same shape as a foreign one ("holiday with kids in
                 # devon", "kids holiday club", "holiday without the kids"). A domestic place
                 # stands the row down and the line falls through as it does on main.
                 "cornwall", "devon", "wales", "scotland", "england", "yorkshire", "norfolk",
                 "suffolk", "dorset", "sussex", "kent", "cumbria", "lake district", "seaside",
                 "butlins", "haven", "pontins", "caravan", "camping", "campsite", "holiday club",
                 "holiday camp", "day trip", "weekend trip", "in the uk", "staycation",
                 "without the kids", "without children", "without my kids", "no kids",
                 "adults only", "grown ups"),
          # The passport list is a journey question: an illness in the house with no journey in
          # the line is the health rows' question, and this row took it.
          guard=_a_journey_not_a_treatment,
          bias=1),

    # A dog or a cat that comes on holiday is paperwork, not luggage: the chip and the rabies
    # jab are the two things people leave too late, and "can i take my dog to france" on main was
    # a search hedge. The rule that matters is always the two countries' own, so the answer says
    # where to look rather than guessing at one border.
    entry("pet-travel",
          (("dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets", "rabbit",
            "ferret", "hamster", "guinea pig", "budgie", "parrot", "tortoise", "snake"),
           # The travel word has to be there: "take", "bring" and "chip" read a cat bringing
           # birds in and a dog eating chips as a trip abroad.
           # "holiday" is not a travel word on its own: "im thinking of getting a cat" then
           # "what about holidays" is where the cat goes while the person is away, and this entry
           # answered it with a rabies vaccination. The going-away question is `pet-holiday`'s;
           # a line that names a country, a ferry, a plane or a passport still comes here.
           ("abroad", "france", "spain", "italy", "ireland", "europe", "travel",
            "travelling", "traveling", "travel with", "fly", "flying", "plane", "ferry",
            "tunnel", "pet passport", "rabies", "vaccination", "microchip",
            "out of the country", "another country")),
          ("For most of Europe the order is fixed: microchip first, then a rabies vaccination at "
           "least 21 days before you travel, then the paperwork - an EU pet passport or an animal "
           "health certificate from your own vet - and a tapeworm treatment for a dog on the way "
           "back from some countries. Check both countries' own rules, and the ferry or airline's, "
           "because each has its own kennel or cabin booking. Start six weeks out: the 21 days "
           "catches people, and nothing can be backdated."),
          # "fly" is the airline word here and a fly spray is a can of insecticide, which is the
          # household-chemical row's question: "is fly spray safe around cats" was a pet passport.
          avoid=("puppy food", "dog food", "cat food", "my dog is sick", "my cat is sick",
                 "dog training", "dog bark", "cat litter", "dog insurance", "vet bill",
                 "dog in the car", "car sick", "dog ate", "cat ate", "flea", "worming",
                 "separation anxiety", "boarding kennel", "put my dog", "put my cat",
                 "fly spray", "insect spray", "bug spray", "mosquito spray", "wasp spray",
                 "air freshener", "aerosol", "the spray"),
          bias=1),
    # "the cheapest way to get to X from Y" is a comparison between a coach, a train and a car,
    # and it is the same answer for any pair of cities in one country, so it is keyed on the
    # asking words rather than on a list of routes.
    entry("intercity-cheapest",
          (("cheapest way", "cheapest", "cheaper", "cheap way", "get to", "getting to",
            "travel to", "train or coach", "coach or train", "drive or train", "how do i get from",
            # The pair is asked with an article in it - "which is better the train or the coach" -
            # which is not the spelling the pair words above are keyed on. The asking words say
            # the comparison and the guard still needs two ways in the line, so the pair does not
            # have to be spelled the one way here.
            "which is better", "which is cheaper", "which one is better", "whats better",
            "what's better"),
           ("from", "train", "trains", "coach", "coaches", "bus", "buses", "plane", "flight",
            "flying", "driving", "london", "manchester", "edinburgh", "glasgow", "birmingham",
            "leeds", "bristol", "cardiff", "newcastle", "liverpool", "paris", "amsterdam",
            "berlin", "rome", "madrid", "barcelona", "dublin", "city", "town")),
          ("The coach is nearly always the cheapest and the train the fastest, and the price gap "
           "is all in how early you book: a coach booked a fortnight ahead is often a fiver, while "
           "a walk-up train fare on the day can be ten times that. Book a fixed-time train twelve "
           "weeks out for the cheap tiers, compare one change against a through train, and count "
           "the cost of getting to and from the stations before you decide."),
          ask=("cheapest", "cheaper", "cheap way", "which is cheaper", "which is better",
               "compare", "best way", "worth it", "train or coach", "coach or train",
               "drive or train", "or train", "or coach"),
          # "is it cheaper to fly or take the train to edinburgh" is the same comparison with a
          # plane in it, and the fence on "fly" and "flight" shut this row for it. A plane on its
          # own is still the fares card's line, which the guard below decides.
          guard=_a_comparison_needs_two_ways,
          avoid=("airport", "car park", "parking", "my car", "driving licence",
                 "how do i get to sleep", "how do i get to work", "promotion", "get to know"),
          # The general "book early" entry answers a line about one mode; a line that weighs
          # the coach against the train is this answer's own question.
          bias=1),

    # "how do i get from naples to sorrento" was answered with the Naples guide, which says
    # nothing about the train. The pair is the key, because the answer is about the journey.
    entry("route-between",
          (("how do i get", "how to get", "best way", "get from", "getting from", "travel from",
            "how do i travel", "how to travel", "train or", "ferry or", "bus or", "drive or",
            "how far", "how long does it take to get"),
           tuple(sorted({name for pair in ROUTE_BETWEEN for name in pair}))),
          _route_between,
          avoid=("airport", "flight", "flights", "fly into", "hotel", "hostel", "day trip",
                 "day trips", "worth visiting", "best time", "where to stay", "get around",
                 "getting around", "car hire", "rent a car", "hire a car"),
          bias=2),
    # "how do i get to the amalfi coast" names only the destination, so it is the way in.
    entry("get-to-place",
          (("how do i get to", "how do i get", "how to get to", "how do i reach", "getting to",
            "how do you get to", "best way to get to", "how do i travel to"),
           tuple(sorted(GET_TO))),
          _get_to,
          avoid=("airport", "hotel", "hostel", "day trip", "worth visiting", "best time",
                 "where to stay", "get around", "getting around"),
          bias=1),
    # The site, not the city: "is pompeii worth visiting" was "That's your call, not mine".
    entry("site-worth-visiting",
          (SITE_WORDS,
           ("worth visiting", "worth it", "worth seeing", "should i visit", "should we visit",
            "is it worth", "how long", "how much time", "do i need a ticket", "book",
            "booking", "tickets", "ticket", "visit", "see",
            # "is the vatican worth a whole day", "is 3 days enough for the vatican", "how long
            # does the vatican take": the site is named, so the bare words are safe here and the
            # note answers the length of the visit rather than the pope's name.
            "worth", "enough", "days", "whole day", "long", "take")),
          _site_note,
          # the city itself has its own guide, and a clock question about a journey is the route
          avoid=tuple(sorted(CITIES)) + ("flight", "hotel", "airport", "restaurant", "get from"),
          bias=1),
    # A safety question about the place the chat is on: "is it safe", "is lisbon safe", "is it
    # dangerous there". The night row owns "at night"; this one is the same habits for the rest of
    # the day, and it says nothing at all until a city is in the chat, so "is it safe" after a
    # chicken left out overnight keeps its food answer.
    entry("city-safe-in-the-day",
          (("safe", "unsafe", "dangerous", "risky", "danger", "crime", "dodgy",
            "is it safe", "is it dangerous", "is it risky", "safe there", "safe enough",
            "safe to walk", "much crime"),
           tuple(CITIES) + ("there", "the streets", "the area", "the city", "the centre",
                            "the center", "tourist", "tourists", "worth visiting", "trip",
                            "holiday")),
          _a_place_it_might_not_be_safe,
          avoid=("tap water", "the water", "water", "ice", "salad", "food", "eat", "tap",
                 "sun", "sunburn", "swim", "jellyfish", "pregnant", "vaccine", "malaria",
                 "jab", "mosquito", "insurance", "at night", "after dark", "night", "evening",
                 "walking back", "walk back", "on my own", "by myself", "alone",
                 # walking a city is the habits card's own question, and its first sentence is
                 # the streets: "is it safe to walk around naples" came here and got the verdict
                 # instead, where the card beside this one says what to do
                 "walk around", "walking around", "walk about", "walking about", "get around",
                 "getting around", "walk home", "walking home",
                 "travel to", "travel advice", "foreign office"),
          bias=1),
    # A named day trip is a place of its own, the same way a famous site is: "is sintra worth it"
    # and "how do we get to sintra" were answered with the Lisbon guide again, word for word, at
    # the end of a chat that had already been given it. The clause about the place is the answer,
    # and it costs nothing to keep: it is the city's own line, not new content.
    entry("day-trip-place",
          (tuple(sorted(DAY_TRIP_PLACES)),
           ("worth it", "worth visiting", "worth seeing", "worth going", "is it worth",
            "should i visit", "should we visit", "what is there", "what's there",
            "how do i get", "how do we get", "how do you get", "how to get", "how far",
            "day trip", "day out")),
          _day_trip_place,
          # the city itself has its own guide, and a flight or a hotel is another question
          avoid=tuple(sorted(CITIES)) + ("flight", "hotel", "hostel", "airport", "restaurant",
                                         "get from", "where to stay", "best time"),
          bias=1),
    # The second half of a question asked in two parts: "is sintra worth it" and then "and how
    # do we get there". The follow-up names no place, so the row above cannot be reached, and the
    # turn came back as "Same as before: From Lisbon: Sintra for the palaces (40 minutes by
    # train)" - the whole answer again where the line asked for the train. The place is read off
    # the last turns of the chat, and a line with no day trip behind it passes.
    entry("day-trip-way",
          (("how do i get there", "how do we get there", "how do you get there",
            "how do we get to it", "how do i get to it", "how far is it", "how far is that",
            "how long does it take to get there"),
           ("there", "it", "that")),
          _day_trip_place,
          avoid=tuple(sorted(CITIES)) + ("flight", "hotel", "airport"),
          bias=1),
    # "is it safe to walk around naples at night" got the Naples guide. No answer here says a
    # city is safe or unsafe: it is the habits, and the hotel desk knows the streets.
    entry("city-night-safety",
          (("safe", "unsafe", "dangerous", "risky", "ok to walk", "fine to walk"),
           ("at night", "after dark", "walk around", "walking around", "walk back",
            "walking back", "on my own", "by myself", "alone", "night", "evening")),
          ("Use the habits that work in any city after dark: stay on the busy, lit streets, take a "
           "licensed taxi or the metro rather than a shortcut, keep the phone out of sight and the "
           "bag in front of you, and ask the hotel desk which two or three streets to avoid - they "
           "know this week's answer better than any guide. Carry a card with the hotel address."),
          # "at night" and "night" are a time, not a subject: with "safe" in the asking arm, every
          # "is it safe to ... at night" line came here, the ones about roads included - "is it
          # safe to drive at night" was told to stay on the busy, lit streets. The habits below
          # are for walking a city, so a line that names a vehicle or a road is another question
          # and this card stands down. A bike stays in on purpose: "is it safe to cycle at night"
          # is a city at night, and these habits answer it.
          avoid=("tap water", "drink the water", "water", "ice", "salad", "food", "eat", "street "
                 "food", "tap", "sun", "sunburn", "swim", "jellyfish", "pregnant", "vaccine",
                 "malaria", "jab", "mosquito", "insurance", "at night in", "hotel room",
                 "walk the dog", "walk my dog", "neighbourhood", "which area", "where should i "
                 "stay",
                 "drive", "driving", "driver", "car", "cars", "van", "motor", "motorway",
                 "road", "roads", "lane", "lanes", "parking", "headlights", "towing",
                 "trailer"),
          bias=1),
    # "do kids travel free on buses" and "my child needs a bus pass" reached the older person's
    # scheme, because "free" and "bus" are its own words. A child on a bus is a different scheme:
    # under-fives ride free with an adult, 5 to 15 pay a child fare, and free travel to school is
    # judged on distance.
    #
    # The asking words are travel words and never the bare word "school". They were, and with
    # "my son" among the subjects every line about a child and school became a fare: 28 of the 110
    # deck rows that say school or nursery took this answer, from "my son is being bullied at
    # school" to "the kids are off school". A parent asking for a fare says bus, ticket, pass or
    # travel, so those words carry it and school on its own does not.
    entry("child-bus-travel",
          (("child", "children", "kids", "kid", "my son", "my daughter", "school child",
            "school children", "under 5", "under five", "under 5s", "under fives",
            "under-fives", "5 year old", "4 year old",
            # "is the school bus free" names the ride and not the child, and it reached nothing
            # at all, though free school travel is the second half of this answer.
            "school bus", "school buses", "school travel", "school transport", "school run",
            "family", "families",
            # A parent asks how the child gets there without naming the child twice: "how does he
            # get to school", "how will my son get to school", "getting to school in september".
            # The phrases name the journey, so they are a subject of their own here. The travel
            # half below carries them too, which is what lets the line match on the journey alone.
            "get to school", "gets to school", "getting to school", "get to school and back",
            "to school and back", "travel to school", "journey to school",
            # "is there a bus to school" is the journey, and it was answered with the coach
            # between two cities - the trip, not the school run
            "bus to school", "coach to school"),
           # The travel half has to name travel. It used to take `pass`, `pay`, `cost` and
           # `school` on their own, and a child word plus `passed` is "my son passed his driving
           # test" and "my son passed his exams" - good news to a parent, answered with the child
           # bus fare. So the words here are transport, or a ride that is free, and nothing else.
           ("bus", "buses", "coach", "coaches", "tram", "trams", "ferry", "ferries",
            "fare", "fares", "child fare", "ticket", "tickets", "season ticket", "bus pass",
            "school bus", "school travel", "school transport", "free travel", "travel free",
            "travels free", "travel for free", "ride free", "rides free", "rides for free",
            "goes free", "go free", "pay on the bus", "pay on buses", "on the bus",
            "on the coach",
            # the journey said as the journey: "how does he get to school", "getting to school",
            # "is there a bus to school", which named no fare and reached nothing at all
            "get to school", "gets to school", "getting to school", "to school and back",
            "travel to school", "journey to school", "get the bus to school",
            "catch the bus to school", "bus to school", "coach to school")),
          "Under-fives usually travel free on local buses with a paying adult, and 5 to 15 pay a "
          "child fare, often about half: the operator's own page gives the age and the price for "
          "your area. Free travel to school is a council decision and it turns on distance - "
          "usually over 2 miles for a child under 8 and over 3 miles for an 8 to 16 year old going "
          "to the nearest suitable school, or closer if the route is unsafe to walk. Ask the "
          "council's school travel team; a 16 to 18 year old in full-time education usually needs "
          "a council or operator discount card instead.",
          # the older person's pass, a train, and a plane are other answers
          avoid=("pensioner", "pensioners", "over 60", "over 65", "older person", "retired",
                 "freedom pass", "concessionary", "disabled", "train", "trains", "railcard",
                 "flight", "flights", "plane", "airport", "car seat", "hotel", "abroad",
                 "holiday abroad", "travel insurance", "school place", "school admission",
                 "school admissions",
                 # a child being bullied at school names a child and a school and has nothing to
                 # do with fares: "my son is being bullied at school" got the under-fives line
                 "bullied", "bullying", "being bullied", "bullies", "picked on", "picks on",
                 "mean to", "horrible to", "unkind to", "nasty to",
                 # A child plus a bus is a fare only if the child is well. "my child passed out on
                 # the bus" is a parent describing a collapse, and it was answered with the
                 # under-fives fare - the same shape as the good-news lines above, with the
                 # opposite meaning. These are the words that make the line about the child
                 # rather than about the ride.
                 "passed out", "passing out", "pass out", "faint", "faints", "fainted",
                 "fainting", "collapsed", "collapse", "collapses", "passed away",
                 "unwell", "poorly", "feeling ill", "feels ill", "felt ill", "being sick",
                 "was sick", "got sick", "threw up", "vomited", "diarrhoea", "diarrhea",
                 "temperature", "fever", "hospital", "ambulance", "111", "999", "a&e",
                 "seizure", "convulsion", "allergic reaction",
                 # And a child who will not get on the bus is not asking what the ride costs:
                 # "my daughter wont get on the bus to school" and "she is scared of the school
                 # bus" are the school-refusal answer's lines, and a fare paid on a bus the child
                 # will not board helps nobody. The refusal, not the bus, is what these name.
                 # The understanding layer expands "wont" to "will not" before the lookup, so
                 # the fence has to be written the expanded way too: "wont get on" alone stood
                 # the row down only when a test called the matcher by hand.
                 "not get on", "not get in", "not board", "not go", "crowded",
                 "wont get on", "won't get on", "wont get in", "won't get in", "wont go",
                 "won't go", "wont board", "won't board", "refuses to go", "refuses to get on",
                 "refusing to go", "refusing to get on", "refused to go", "refused to get on",
                 "scared of the bus", "scared of the school bus", "afraid of the bus",
                 "scared of school", "afraid of school", "school refusal", "anxious about school",
                 "anxious about the bus", "hates the bus", "hates school", "wont leave the house",
                 "won't leave the house",
                 # A thing the child has with them, named on a bus, is a lost-property
                 # question and not a fare: "my daughter had her phone stolen on the bus"
                 # is the find-it answer's line, and the child word plus "bus" alone gave
                 # it the under-fives fare. The fare is asked when the ride is, so any
                 # named thing they might lose stands this row down.
                 "phone", "phones", "mobile", "mobiles", "iphone", "smartphone", "tablet",
                 "ipad", "wallet", "purse", "handbag", "backpack", "school bag", "rucksack",
                 # The loss words are not here on purpose: "my son lost his bus pass" is a
                 # travel-admin question, and standing down for the bare word "lost" only moved
                 # it from the fare answer to a shrug. A named thing is what makes the key.
                 )),
    # "How do i travel cheap in europe" reached nothing, and "travel around europe on a budget"
    # reached the meal plan (the phrase "on a budget" and the word "budget" counted twice), so
    # this is the cheapest way round a continent rather than the cheapest way to eat for a week.
    entry("travel-cheaply",
          (("travel cheaply", "travel cheap", "travelling cheap", "traveling cheap",
            "travel on a budget", "travel around europe", "travelling around europe",
            "traveling around europe", "touring europe", "tour europe", "see europe",
            "get around europe", "europe on a budget", "cheap travel", "cheap holiday",
            "cheap trip", "backpacking", "backpack", "interrail", "eurail",
            "cheap places to go", "budget trip"),
           ("cheap", "cheaply", "cheapest", "budget", "save", "afford", "europe", "european",
            "hostel", "hostels", "train", "trains", "coach", "how", "ways", "tips")),
          "Take the train or the coach between cities instead of flying, book a month or two "
          "ahead, and stay in hostels or travel out of season: May, June and late September cost "
          "about half what August does. Eat where people work - market stalls, bakeries, a "
          "supermarket lunch - and choose one small town over a second capital. Cheapest weeks "
          "are midweek city breaks, Tuesday to Thursday.",
          # a single fare question, and a week of dinners, keep their own answers
          # "on a budget" is two key words to the week-of-dinners row and one to this, so the
          # travel answer takes the tie when a line is about a trip rather than a shop
          bias=1,
          # "backpack" is a rucksack as well as a way round Europe, and "pack" is in this row's
          # key by way of "ways" and "how": "how do i pack a backpack for hiking" was told to take
          # the coach between cities. A line about the folding is the packing row's.
          avoid=("flight", "flights", "airfare", "meal", "meals", "dinner", "cook", "cooking",
                 "recipe", "food shop", "week of", "meal plan", "hotel in", "which hotel",
                 "hiking", "hike", "hill", "walking boots", "rucksack", "pack a", "packing a",
                 "pack my", "how do i pack", "suitcase", "carry on")),
]
# "how do i find a decent hotel" was a hedge, and so was "where should i stay". The booking sites
# answer the price; what people want is how to tell a good one from a bad one before paying, and
# the neighbourhood entry next door already avoids "where should i stay" so this one owns it.
ENTRIES.append(entry(
    "pick-a-hotel",
    (("hotel", "hotels", "guesthouse", "guest house", "b&b", "bed and breakfast", "hostel",
      "place to stay", "somewhere to stay"),
     ("decent", "good", "choose", "choosing", "pick", "picking", "find", "finding", "best",
      "book", "booking", "which", "how do i", "safe", "recommend",
      "where should i", "avoid", "trust", "reviews", "worth it", "village", "city",
      "town", "night", "nights", "weekend", "holiday", "trip")),
    "Book from the hotel's own site once you know the name, then check three things: the last "
    "two months of reviews only (owners change, and old praise is stale), the map for the walk "
    "to the station or the old town, and the small print for a city tax and the cancellation "
    "date. A room away from the lift or the road is worth asking for in the booking notes, "
    "and ring the desk for anything that matters - they answer faster than the site.",
    # a hotel complaint, a hotel wifi and a hotel address are other entries' questions
    # Money is its own answer: "how do i find a cheap hotel" is answered by the entry that says
    # to book direct with a small hotel or guesthouse, so this one keeps only the lines about
    # which hotel to pick.
    avoid=("when should i book", "when do i book", "when to book", "how far in advance",
           "how far ahead", "how early", "weeks before", "months before", "book for a wedding",
           "block of rooms", "wedding guests",
           "complain", "complaint", "refund", "wifi", "wi-fi", "address", "cancel", "cancel my",
           "noise", "noisy", "dirty", "bed bugs", "reviews said", "left something",
           "cheapest flight", "flights", "airport", "dog", "parking", "pet",
           "cheap", "cheaper", "cheapest", "price", "prices", "cost", "budget", "deal", "deals",
           "discount", "how much",
           # "how do i" is in the key, so a job in a hotel landed here: the way into a hotel as
           # an employee is work's `job-in-a-place`, and it names none of the booking.
           "job", "jobs", "work at", "work in", "working in", "staff", "vacancy", "vacancies",
           "hiring", "apply", "application", "interview", "career", "cv", "rota", "shift"),
    ask=("decent", "good", "choose", "choosing", "pick", "picking", "find", "finding", "best",
         "book", "booking", "which", "how do i", "where should i", "recommend", "trust",
         "worth it", "avoid", "safe")))


# --- reading a timetable ------------------------------------------------------------
# People ask this about a bus, a train and a ferry, and "read" sent the line to the holiday
# reading list (book-holiday, in entertainment.py) which now stands down for it. Keyed on the
# timetable rather than the vehicle, so a coach, a tram or a ferry gets the same answer.
def _read_timetable(memory, understood):
    """The two wordings of the same answer, picked per conversation."""
    return pick([
        "Read a timetable by column, not by line: each column is one journey, so run your finger "
        "down it to see the time at your stop and the one after. Times after noon are often in "
        "24-hour form (17:40 is 5:40 in the evening), the small letters beside a time are "
        "explained in the key at the bottom - S for schooldays, NS for not Sundays - and Sunday "
        "and bank holiday services have their own table with the last bus much earlier. The "
        "operator's app or the display at the stop is the only thing that knows about today's "
        "delays.",
        "Find your stop's row first and read across it: the minutes are printed under the hour, "
        "so a column is one bus and a row is one stop. The letters next to a time are notes - "
        "schooldays only, not Saturdays, bank holidays - and there is usually a separate table "
        "for Sunday. Be at the stop five minutes early, because a bus that comes every half hour "
        "is the one you cannot afford to miss, and check live times on the operator's app before "
        "you set off: the printed table is the plan, not what is happening.",
    ], memory)


ENTRIES.append(entry(
    "read-a-timetable",
    (("timetable", "timetables", "time table", "bus times", "train times", "bus schedule",
      "train schedule", "departure board", "departures", "last bus", "next bus", "next train",
      "last train", "24 hour clock", "24-hour clock"),
     ("read", "reading", "how", "when", "what time", "next", "last", "which", "catch",
      "work out", "understand", "sunday", "night", "evening", "morning", "app")),
    _read_timetable,
    # This row answers the reading question, not a journey: a line that asks the time of a named
    # service ("what time is the next train to leeds") wants a live answer, and the live-times
    # card has it. So the ask needs a reading word in the line.
    ask=("read", "reading", "how do i", "how do you", "how to", "understand", "work out",
         "explain", "what does", "mean"),
    # a school timetable is not a journey, and a reading list is not a table of times
    # "reading" is not here: the matcher folds word forms, so an avoid of "reading" stands the
    # row down for its own line, "how do i read a bus timetable".
    avoid=("school", "exam", "exams", "class", "classes", "study", "revision",
           "book", "novel", "holiday read", "gym", "workout", "medication", "dose", "feed"),
    bias=1))


# --- the bag, from the hotel desk to the cabin ---------------------------------------
# "can i leave my luggage at the hotel after check out" was answered with the airline's
# baggage allowance, because the allowance row keys the word luggage and the line carried it.
# A bag left at the desk is a different question with a different answer (the hotel keeps it),
# so the two are split by the place the bag is in rather than by the word for the bag.
ENTRIES.append(entry(
    "left-luggage",
    (("luggage", "bags", "baggage", "bag", "suitcase", "suitcases", "rucksack", "holdall",
      "backpack", "cases"),
     ("hotel", "hotels", "hostel", "hostels", "guest house", "guesthouse", "reception",
      "front desk", "apartment", "apartments", "airbnb", "villa", "check out", "checkout",
      "check-out", "check in", "check-in", "left luggage", "luggage room", "concierge",
      "holiday let", "rental", "reception desk")),
    "Most hotels hold your bags free at reception, both before check-in and after you check out: "
    "ask them to tag them with your name and ask what time the desk closes, so you are back "
    "before then. Keep the passport, the money and anything you would hate to lose in your day "
    "bag rather than the big case, and if the hotel will not help, a station left-luggage desk or "
    "a locker is a few pounds for the day.",
    # an airline's allowance, a missing bag and a bag that broke are the other rows' questions,
    # and a bag left in a car, a taxi or on a train is a lost-property question
    avoid=("allowance", "how much", "how many", "weight", "kg", "cabin", "hand luggage",
           "carry on", "carry-on", "lost", "lose", "stolen", "missing", "damaged", "damage",
           "unattended", "carousel", "platform", "taxi", "boot of", "left behind", "forgot",
           "pick up", "collect it from the airport"),
    # the place is what makes it this row: a bag and a verb with no stay in the line is a
    # lost-property, a packing or a salad question ("how do i keep a bag of salad"), so the
    # second key part is the place alone and this row never needs the verb
    bias=2))

ENTRIES.append(entry(
    "cabin-bag",
    # the asking shape of "how big may my bag be" and "can my bag come in the cabin": both are
    # the same rule, so one row answers the size and the permission together
    (("suitcase", "suitcases", "cabin bag", "hand luggage", "carry on", "carry-on", "rucksack",
      "backpack", "holdall", "bag", "bags", "luggage"),
     ("how big", "how large", "how much can", "what size", "size", "dimensions", "cm",
      "centimetres", "centimeters", "too big", "too large", "fit", "fits", "fitting", "measure",
      "under the seat", "on the plane", "on board", "in the cabin", "onto the plane")),
    "The usual cabin limit is 55 x 40 x 20 cm including the wheels and the handle, plus one small "
    "bag under the seat at about 40 x 30 x 15 cm, and 7 to 10 kg in total - so yes, a rucksack or "
    "a small case comes on with you, as long as it fits the sizer at the gate. A soft bag squeezes "
    "into it and a hard case does not, so leave a centimetre of slack and weigh it at home.",
    avoid=("bin", "bin bag", "rubbish", "vacuum", "hoover", "tea bag", "dog", "sleeping bag",
           "freezer", "freezer bag", "ziplock", "zip lock", "food bag", "sugar", "flour",
           "compost", "peat", "cement", "sand", "soil", "potatoes", "charcoal", "ice", "food",
           "sandwich", "sandwiches", "drink", "drinks", "liquid", "liquids", "razor", "lighter",
           "medicine", "medication", "knife", "scissors", "battery", "batteries", "power bank",
           "phone", "laptop", "data", "baby", "pram", "pushchair", "damaged", "lost", "stolen",
           "missing", "delayed", "airport", "hotel", "flight"),
    bias=1))

ENTRIES.append(entry(
    "extra-bag-cost",
    (("extra bag", "extra luggage", "extra suitcase", "checked bag", "checked luggage",
      "bag to check", "add a bag", "add luggage", "second bag", "hold bag", "hold luggage",
      "put a case in the hold"),
     ("cost", "costs", "price", "prices", "how much", "pay", "fee", "fees", "charge", "charges",
      "expensive", "cheaper", "cheapest", "worth it")),
    "Book the bag with the ticket rather than at the airport: a checked bag is usually about £15 "
    "to £40 each way online and £40 to £65 at the desk, and on a short trip a 10 kg cabin bag with "
    "priority is often the cheaper way to take a case. Weigh it at home on the bathroom scales - a "
    "few kilos over is charged at the airport rate however you booked.",
    # the size rules, a bag that went missing, and a suitcase to buy are other rows' questions
    avoid=("allowance", "how big", "size", "dimensions", "kg can", "how many kg", "weight limit",
           "lost", "stolen", "missing", "damaged", "buy", "buying", "recommend", "which bag",
           "which suitcase", "hotel", "food", "pram", "pushchair", "carrier bag", "plastic bag",
           "5p", "5 pence", "shop", "supermarket", "charge for bags"),
    # a shop's carrier-bag charge keys the same "bag" and "cost" as a flight's extra bag, and
    # the line that names the airline has to be the airline's
    bias=2))

# A bag that has already been taken is the theft answer in lifeadmin; this is the question asked
# before the trip, and "how do i avoid pickpockets in rome" was a search punt.
ENTRIES.append(entry(
    "pickpockets-abroad",
    (("pickpocket", "pickpockets", "pickpocketing", "pickpockets in", "thieves", "thief",
      "muggers",
      # "scams" is deliberately not here, and it is the one word that must not be: it is a
      # general fraud word ("how do i spot a scam", "how do i avoid scams"), and beside the
      # avoid group it took those lines to a card about back pockets and cafe tables. A scam in
      # a city is caught by the pickpocket words people actually type with it; a scam without a
      # street in it is consumer.py's fraud answer, which is where it belongs.
      # the thing people ask about keeping safe, and the avoid keeps the theft answer apart
      "wallet", "wallets", "purse", "money belt"),
     ("avoid", "avoiding", "stop", "prevent", "safe", "safety", "keep my", "protect", "careful",
      "watch out", "beware", "tips", "how do i", "what should i", "scared", "worried",
      # "pickpockets in rome" names no verb at all, so the place is the second key word: without
      # it the shape people type most ("pickpockets in <city>") reaches nothing.
      "abroad", "holiday", "trip", "city", "cities", "rome", "paris", "barcelona", "madrid",
      "lisbon", "prague", "amsterdam", "naples", "athens", "istanbul", "berlin", "dublin",
      "london", "new york", "venice", "florence", "budapest", "brussels", "vienna")),
    ("Keep the phone out of a back pocket and the bag across your body with the zip in front, "
     "and split the cash into two places so one theft is not the whole trip. Never leave a phone "
     "on a cafe table or a bag on the back of a chair, carry a copy of the passport rather than "
     "the passport itself, and if someone bumps into you in a crowd, check your pocket at once - "
     "the bump is the trick."),
    bias=1,
    # a bag that is already gone, a stolen passport and a holiday scam are other answers
    avoid=("wallet was", "wallet stolen", "wallet gone", "purse was", "phone was",
           "was stolen", "got stolen", "snatched", "bag was", "robbed", "mugged",
           "passport", "insurance", "report")))

# --- away with someone who cannot walk far ---------------------------------------------------
# "she cant walk far what should we do on holiday" was answered with the 7,000-steps-a-day rule,
# "my dad cant walk far can we still go away" with "That's beyond what I know well", "accessible
# holidays for someone who cant walk far" was noted back and "best way to get around a city with
# someone who cant walk far" was a guess-hedge. The hiking row already stands down on
# "cant walk", so this row is the one that has to answer it.
ENTRIES.append(entry(
    "away-with-someone-who-cannot-walk-far",
    (("cant walk far", "can't walk far", "cannot walk far", "cant walk", "can't walk",
      "cannot walk", "struggles with walking", "struggles to walk", "struggle walking",
      "not good on their feet", "cant walk much", "wheelchair", "wheelchairs", "rollator",
      "walking stick", "walking frame", "mobility scooter", "mobility", "disabled",
      "bad knees", "hip replacement", "knee replacement", "slow walker", "gets tired walking",
      # the help that has to be booked is the same answer, and these lines carry no walking word
      "special assistance", "airport assistance", "help at the airport", "passenger assist",
      "help getting on the train", "help on the train", "help onto the train",
      "book assistance", "assistance booked", "airport special assistance"),
     ("holiday", "holidays", "away", "trip", "travel", "abroad", "city break", "day out",
      "get around", "getting around", "get about", "see", "visit", "day", "hotel",
      "flight", "flights", "train", "coach", "bus", "plane", "planes", "airport",
      "airports", "fly", "flying", "museum", "gallery", "how")),
    ("Plan for half the walking and twice the sitting: one or two things a day with a cafe or a "
     "bench between them, and a taxi or the hop-on bus for the long hops rather than marching "
     "between sights. Check step-free access before you book, because most museums, galleries and "
     "cathedrals publish it, ask the hotel for a room near the lift, and book help ahead on trains "
     "and at the airport - it is free, UK rail's Passenger Assist takes bookings up to 24 hours "
     "ahead and airports usually want 48. A folding wheelchair or rollator can be hired locally "
     "for a week for less than a day's car hire, a lot of places let a carer in free, and a "
     "folding stool in a bag turns an unplanned stop into a rest. Skip the walking tour and the "
     "climb, and book the view from a roof terrace or a cafe instead."),
    # flight socks, insurance, a passport and the step target are other answers
    avoid=("flight socks", "compression", "dvt", "blood clot", "swollen ankles", "insurance",
           "visa", "passport", "jet lag", "pram", "pushchair", "dog", "puppy", "how many steps",
           "step target", "10,000", "10000", "knees hurt", "hip hurts", "doctor"),
    bias=2))


# --- is it good for families ----------------------------------------------------------------
# "is rome good for families", "is it good for families" a turn after the city was named and
# "is lisbon good with kids" all got a search hedge, and the question a family holiday turns on
# is the one the bot had nothing for. `CITIES` holds what to see; a child needs to know something
# else - how far it is, whether the pram will do, when they will eat - so every city in that table
# gets one short verdict, and it is a verdict rather than a list of sights.
FAMILY_VERDICT = {
    "amsterdam": (
        "Amsterdam is easy with children: everything is close, the trams take a pram, and "
        "NEMO and the science museum are built for them. The bikes are the thing to watch - "
        "keep on the pavement side and hold hands at the crossings."),
    "athens": (
        "Athens is fine with older children and hard work with a toddler: the Acropolis is a "
        "stony climb with little shade and the pavements are narrow. Go at opening time, give "
        "the afternoon to the National Garden, and take taxis rather than walk the long "
        "blocks."),
    "bangkok": (
        "Bangkok is hot and loud and better with children than people expect: the river boats "
        "are the day out, the malls have play areas and aquariums, and taxis are cheap. "
        "Traffic is the enemy, so plan around the skytrain and the boats."),
    "barcelona": (
        "Barcelona is one of the easiest cities in Europe with children: the beach is on the "
        "metro, the Gothic Quarter is flat, and the Boqueria is a free hour of noise and "
        "fruit. The Sagrada Familia sells out, so book weeks ahead."),
    "bath": (
        "Bath is a good day out rather than a week: the Roman Baths run a family trail with "
        "an audio guide for children, and the baths, the abbey and the river are all within a "
        "mile. It is fine with a pram in the centre and steep on the hills out of it."),
    "berlin": (
        "Berlin works well with children and costs less than most of western Europe: the zoo "
        "is one of the best anywhere, the Technikmuseum has trains and planes to climb on, "
        "and the parks have playgrounds. It is spread out, so buy a day travel ticket."),
    "boston": (
        "Boston is a good family city: the Freedom Trail is a walk with stories in it, the "
        "harbour and the science museum fill a day, and the T takes a stroller. It is compact "
        "and walkable, which is the whole point of it with children."),
    "brussels": (
        "Brussels is underrated with children: the Grand Place, the comic strip museum and "
        "the Atomium are close, and the waffles do a lot of the work. Two days is enough, and "
        "it is an easy stop on a longer trip."),
    "budapest": (
        "Budapest is good with children who like water: the thermal baths take families, and "
        "Margaret Island is a park with pools, bikes and a musical fountain. The trams and "
        "metro are cheap and frequent."),
    "buenos aires": (
        "Buenos Aires is a big, late city with children: the parks and the zoo in Palermo are "
        "the easy days, and the buses and taxis are cheap. Dinner starts at nine or later, so "
        "plan an afternoon snack that counts as their meal."),
    "cape town": (
        "Cape Town is excellent with children if you have a car: the beaches, the cable car, "
        "the penguins at Boulders and the aquarium fill a week. The townships and the "
        "mountain roads are not a wander, so plan the drives in daylight."),
    "chicago": (
        "Chicago is a very good family city: the museums on the lakefront, the beach in "
        "summer, and the trains are easy with a stroller. The winter wind off the lake is the "
        "reason to go between May and September."),
    "copenhagen": (
        "Copenhagen is about as good as it gets for small children: Tivoli, the Little "
        "Mermaid on a flat seafront walk, and the harbour buses for the price of a metro "
        "ticket. It is flat, and prams go everywhere."),
    "dubai": (
        "Dubai is easy for families and hot for most of the year: the malls have indoor play, "
        "aquariums and a ski slope, so it works in August when nothing outdoors does. "
        "Anything outdoors belongs to the morning, and the good things need booking."),
    "dublin": (
        "Dublin is a two-day city with children: the Natural History Museum, the Phoenix Park "
        "and the zoo sit close together and cost little. The Guinness tour is not one for "
        "them, so split up or skip it."),
    "dubrovnik": (
        "Dubrovnik is beautiful and hard with a pram: the old town is all steps and the walls "
        "are a long, hot walk with no shade. Go at opening time or after five, and take the "
        "cable car for the view instead of walking the walls."),
    "edinburgh": (
        "Edinburgh is a good family city if you pace the hills: the castle is a climb but "
        "there is a lift up from the esplanade, the museum is free and built for children, "
        "and the Royal Mile is short. In August the festival makes it crowded and expensive."),
    "florence": (
        "Florence with children is one big sight a day and a lot of ice cream: the Duomo "
        "climb suits older ones and the Boboli gardens have space to run. The Uffizi is a "
        "hard sell under ten, so take them to the Palazzo Vecchio instead."),
    "granada": (
        "Granada is worth it with children for the Alhambra alone - book months ahead and go "
        "at opening time, because there is little shade. The city is hilly and the tapas come "
        "free with a drink, which makes dinner easy and early."),
    "hanoi": (
        "Hanoi is exciting and full-on with children: the scooters make crossing the road an "
        "event, and the old quarter is loud. The water puppet theatre and the parks are the "
        "easy wins, and a hotel with a pool earns its money."),
    "havana": (
        "Havana is a city of old cars, music and heat, and children tend to love the first "
        "two: the Malecon, the squares and the museums are cheap. Take the heat seriously and "
        "carry water, and expect the food to be plainer than the city suggests."),
    "helsinki": (
        "Helsinki is calm and easy with children: the ferries to the islands, the zoo on its "
        "own island, and playgrounds everywhere in a small, walkable centre. It is expensive, "
        "and the winter dark is the reason to go between May and September."),
    "istanbul": (
        "Istanbul is good with children who can walk: the ferries are the best value day out "
        "in the city, and the tram between Sultanahmet and the bazaar takes a pram. The "
        "bazaars are crowded and pushy, so go early in the day."),
    "krakow": (
        "Krakow is a good value family city: the main square is flat and car-free, the dragon "
        "under the castle breathes fire every few minutes, and the salt mine is a half day "
        "out. The camps nearby are not for young children."),
    "kyoto": (
        "Kyoto is quiet and beautiful and hard work with small children: the temples ask for "
        "quiet and the buses are packed. The monkey park and the bamboo grove suit them, and "
        "a stroller is more trouble than it is worth on temple steps."),
    "lisbon": (
        "Lisbon is good with children if you take the trams and the funicular rather than "
        "walk the hills: the castle, the aquarium and Belem fill two easy days. The pavements "
        "are slippery when wet, and the hills are real."),
    "ljubljana": (
        "Ljubljana is a small, gentle city with children: the centre is car-free, the river "
        "has cafes on it, and the castle funicular saves the climb. It is a good two-day stop "
        "on the way to the lakes or the coast."),
    "london": (
        "London is one of the best cities in the world with children: free museums, the "
        "parks, and a ride on the top deck of a bus is a day out on its own. The tube is not "
        "step-free everywhere, so check the station before planning a pram route."),
    "los angeles": (
        "Los Angeles is a driving city, so plan days out rather than wanders: the beach, the "
        "studios and the theme parks are each a half day with a car. Without one it is hard "
        "work with children."),
    "madrid": (
        "Madrid is good with children and cheap to eat: the Retiro has a lake with rowing "
        "boats and a playground, and the museums are free in the evenings. Dinner starts "
        "late, so plan a proper late-afternoon snack."),
    "marrakech": (
        "Marrakech is a lot with small children: the souks are hot, crowded and full of "
        "scooters, and the food is not always what they will eat. The gardens, the "
        "horse-drawn calèche rides and a pool at the hotel make it work."),
    "mexico city": (
        "Mexico City is huge and rewarding with children: the parks, the anthropology museum "
        "and the boats at Xochimilco fill days, and the metro is cheap. It is high up, so "
        "take the first day slowly, and eat where it is busy."),
    "milan": (
        "Milan is a short family stop rather than a holiday: the Duomo, the castle park and "
        "the science museum are close, and the trams take a pram. Two days, then on to the "
        "lakes."),
    "munich": (
        "Munich is easy and safe with children: the English Garden, the Deutsches Museum and "
        "the beer gardens, where children are welcome and there is usually a playground. The "
        "trains out to the lakes and the castles are part of the trip."),
    "naples": (
        "Naples is loud and fast and children tend to love it: the pizza is cheap, the "
        "seafront is a flat walk, and Pompeii and Herculaneum are a short train away. Traffic "
        "is the thing to watch and the pavements are narrow."),
    "new york": (
        "New York is great with children who can keep going: the parks, the Natural History "
        "Museum and the Staten Island ferry are cheap days out. Most subway stations have no "
        "lift, so plan the stroller around buses and taxis."),
    "oslo": (
        "Oslo is small, safe and expensive: the ferries, the opera house roof you can walk "
        "on, and the sculpture park are the easy days out, and the trams take a pram. A week "
        "of self-catering takes the edge off the prices."),
    "paris": (
        "Paris is good for families if you pick one thing a day: the Luxembourg gardens have "
        "boats and a playground, and the big museums are free for under-18s in the EU. Lunch "
        "is the easy meal out - restaurants are friendlier at midday than at eight."),
    "porto": (
        "Porto is a good short family break: the riverfront is flat, the boats and the old "
        "tram are the day out, and the port cellars are a walk across the bridge. The climb "
        "back up from the river is steep."),
    "prague": (
        "Prague is good value with children: the castle, the river and the old town are close "
        "together, the trams are cheap, and the toy museum is a good wet-afternoon stop. The "
        "cobbles are hard on a pram."),
    "reykjavik": (
        "Reykjavik is a good family base if you drive: the swimming pools are the thing, "
        "heated and outdoor and everywhere, and the whales, the glaciers and the golden "
        "circle are day trips from it. It is expensive, so an apartment helps."),
    "rio de janeiro": (
        "Rio is wonderful with children in the right places: the beaches, the cable car up "
        "Sugar Loaf and the botanical garden are the easy days. Take advice on which areas to "
        "walk and which to take a taxi through, and swim where the locals do."),
    "rome": (
        "Rome works with children if you keep the days short: the Colosseum and the Forum are "
        "one morning, the Pantheon and a gelato another, and the fountains give you free "
        "water. The cobbles are hard on a pram and the summer heat is real, so spring or "
        "autumn."),
    "san francisco": (
        "San Francisco is a good family city: the cable cars, the sea lions at Pier 39 and "
        "the science museum fill three days, and it is all close. The hills are steep and the "
        "summer fog makes it colder than people expect."),
    "san sebastian": (
        "San Sebastian is a seaside city built for families: the beach curls round the bay in "
        "the middle of town, the promenade is flat, and the old town tapas bars take children "
        "at the early end of the evening. It is a city for eating and swimming rather than "
        "for sights."),
    "santorini": (
        "Santorini is a honeymoon island more than a family one: the villages are steps and "
        "cliff paths with no shade, and the beaches are black stones. With children a resort "
        "with a pool on a flatter island works far better."),
    "seville": (
        "Seville is good with children from March to May: the Alcazar has gardens to run in, "
        "the Plaza de Espana has rowing boats, and the tapas are cheap and served early "
        "enough for them. July and August are too hot to sightsee with children."),
    "singapore": (
        "Singapore is one of the easiest cities in Asia with children: it is safe, the metro "
        "is step-free and air-conditioned, and the zoo, the aquarium and the gardens fill "
        "days. It is expensive, and the heat puts the outdoor plans in the morning."),
    "stockholm": (
        "Stockholm is lovely with children in summer: the ferries between the islands, the "
        "Vasa ship and the open-air museum at Skansen, and prams go everywhere. Winter is "
        "dark and cold, so go between May and September."),
    "sydney": (
        "Sydney is a great family city: the beaches, the ferry to Manly, the zoo on the "
        "harbour and the parks, most of it free or cheap. It is spread out, so plan each day "
        "around one beach or one ferry."),
    "tallinn": (
        "Tallinn is a good short family break: the old town is small and walkable, the towers "
        "and walls are climbable, and the ferries to Helsinki take two hours. Two days is "
        "plenty, and it is cheap by western European standards."),
    "tokyo": (
        "Tokyo is easier with children than people expect: the trains are safe and punctual, "
        "lifts and toilets are everywhere, and there is a small park on every block. The "
        "trains are packed at rush hour, so plan around eight in the morning and six at "
        "night."),
    "toronto": (
        "Toronto is a good, manageable family city: the islands by ferry, the aquarium, the "
        "science centre and the hockey museum fill days, and the subway takes a stroller. It "
        "is clean and English-speaking, which makes the first day easy."),
    "valencia": (
        "Valencia is a good family city that most people skip: the City of Arts and Sciences "
        "has an aquarium and a science museum built for children, and the old town is flat. "
        "The beach is a tram ride from the centre."),
    "venice": (
        "Venice with children is a day of boats and bridges: the water bus is the day out, St "
        "Mark's square has pigeons and space, and there are no cars to worry about. A pram is "
        "the problem - bridges with steps come every hundred metres, so a carrier is better."),
    "vienna": (
        "Vienna is quietly excellent with children: the zoo at Schonbrunn, the Prater's old "
        "ferris wheel and a playground in every park, with a metro that takes a pram "
        "everywhere. The cafes take children, and lunch is cheap at midday."),
    "zurich": (
        "Zurich is clean, safe and expensive with children: the lake boats, the zoo and the "
        "outdoor swimming baths are the days out, and the trams take a pram. A Swiss pass and "
        "a supermarket lunch keep the cost down."),
}

# The words that ask about a child rather than about a sight. A city break with a pram and a city
# break with two teenagers are different answers, but the verdict says what each of them needs.
FAMILY_ASK = ("families", "family", "kids", "children", "child", "toddler", "toddlers", "baby",
              "babies", "teenagers", "teens", "young children", "small children")


# A line that asks what to see is the city guide, not a verdict on the city: "what should we do
# in barcelona with kids" wants the list, and an avoid phrase cannot say that because these are
# made of the words an avoid list does not read ("what", "should", "things to do").
_GUIDE_ASK = re.compile(
    r"\b(?:what|where)\s+(?:should|could|can|shall|do|to)\s+(?:we|i|you)?\s*"
    r"(?:do|see|go|visit|eat)\b|\bthings\s+to\s+do\b|\bwhat(?:'s|\s+is)\s+there\s+to\s+do\b"
    r"|\bitinerary\b|\bsights\b|\bwhat\s+to\s+(?:do|see)\b|\bwhere\s+to\s+go\b", re.I)


def _a_verdict_not_a_guide(understood):
    """False when the line asks what to see, which is the city guide's line."""
    text = " " + " ".join(str((understood or {}).get("text") or "").lower().split()) + " "
    return not _GUIDE_ASK.search(text)


def _the_family_verdict(memory, understood):
    """The verdict for the city the line names, or the one the last turn or two named."""
    city = _place_in(memory, understood, FAMILY_VERDICT)
    if not city:
        return None
    return FAMILY_VERDICT[city]


# The city named in the line, or in the turn before: "is it good for families" after "we are
# thinking of Rome" is the same question, and it was a hedge. The bare ask is a second entry
# because a row's key cannot require a word the line does not have; it stands down by returning
# None when no city is in the conversation, which is what lets another module have the line.
ENTRIES.append(entry(
    "a-city-good-for-families",
    (tuple(FAMILY_VERDICT), FAMILY_ASK),
    _the_family_verdict,
    # a hotel, a flight, a cost, a school or a move is another answer, and so is a line that
    # asks what to see: "what should we do in barcelona with kids" is the city guide, and a
    # verdict on the city instead of the list it asked for is an answer to a narrower question
    # than the one put
    avoid=("hotel", "hotels", "apartment", "apartments", "flight", "flights", "plane", "airport",
           "cheap", "cheapest", "cost", "price", "budget", "insurance", "visa", "passport",
           "school", "schools", "move", "moving", "live", "living", "relocate", "rent", "job",
           "nursery", "childcare", "vaccine", "vaccines", "pushchair", "pram"),
    guard=_a_verdict_not_a_guide,
    bias=2))
ENTRIES.append(entry(
    "is-it-good-for-families",
    (("good for families", "good for kids", "good for children", "good for a family",
      "family friendly", "family-friendly", "kid friendly", "child friendly", "suitable for kids",
      "suitable for families", "family holiday", "family trip", "family break",
      "holiday with kids", "with kids", "with children"), FAMILY_ASK),
    _the_family_verdict,
    avoid=("hotel", "hotels", "apartment", "apartments", "flight", "flights", "cheap", "cheapest",
           "cost", "price", "budget", "insurance", "visa", "school", "schools", "move", "moving",
           "live", "living", "relocate", "rent", "job", "childcare", "vaccine", "pushchair",
           "pram", "toddler won't", "tantrum", "bedtime", "car seat"),
    guard=_a_verdict_not_a_guide,
    # "is it good with kids", a turn after the city was named, was read as "is it worth it" by
    # the viewing row, which asks the same question of a work nobody named; the family ask is
    # the narrower one and takes the line when a city is in the conversation (`_place_in` looks
    # back two turns, and returns None with no city, which leaves the line where it was).
    bias=3))
# --- what the customs hall will not let through --------------------------
# The cabin-bag half of this ("can i take a razor in my hand luggage") is answered by the
# cabin bag rules table, which covers the razor, the scissors, the corkscrew and the lighter in
# one row and is the better answer for all of them. This section is the customs hall only.
# "what do i do if my hotel is overbooked" was a shrug, and "the hotel has no room for us" was
# told where to put a shelf. Being walked to another hotel is a standard thing with an order.
ENTRIES.append(entry(
    # The consumer row in bot/knowledge/consumer.py keeps the id "hotel-overbooked" (two tests
    # pin its lines to it) and this row is the order of phone calls, so it needs its own id: two
    # entries with one id means one of them answers unseen and `test_knowledge_load` is red.
    "hotel-overbooked-steps",
    (("hotel", "hotels", "guesthouse", "guest house", "b&b", "bed and breakfast", "hostel",
      "hotel room", "hotel rooms", "room booking", "our booking", "my booking"),
     ("overbooked", "over booked", "double booked", "double-booked", "no room", "no rooms",
      "full", "turned away", "walked", "lost my booking", "cant find my booking",
      "can't find my booking", "no record", "not on the list", "gave my room away",
      "gave our room away")),
    "Ring the booking site or the hotel's own number straight away, then ask in this order: a "
    "comparable room nearby at their cost including the taxi, or a full refund for the night plus "
    "what you pay for the replacement. Walking a guest to another hotel is standard practice, so "
    "say the word \"walk\" and ask them to confirm it in writing before you leave the desk.",
    # choosing a hotel, a dirty room and a hotel refund are other answers
    avoid=("choose", "choosing", "which hotel", "best hotel", "where to stay", "cheap",
           "cheaper", "cheapest", "price", "cost", "how much", "dirty", "noise", "noisy",
           "complain", "complaint", "cancel my", "cancellation", "wifi", "wi-fi", "shelf",
           "wardrobe", "pack", "packing", "what to take"),
    ask=("overbooked", "over booked", "double booked", "double-booked", "no room", "no rooms",
         "full", "turned away", "walked", "lost my booking", "no record", "gave my room away",
         "gave our room away"),
    # the room-complaint card is keyed on the same words and won this line; a guest who is
    # walked has a different right (a room at their cost), so this row speaks first
    bias=2))

# "can i bring cheese back from france", "can i bring ham back from spain" and "can i bring
# sausages into the uk" all reached nothing: the duty free allowance and the food ban are two
# different rules and the food one is the one people get caught by.
#
# A line that carries food somewhere is the customs ban only when it crosses a border. "bringing"
# is read as "bring" by the word forms, so "what food should i bring" to a picnic reached this row
# and a party of ten children was told the EU ban on ham, cheese and milk. Carrying a dish to a do
# is not importing it.
#
# The reading of "a border is being crossed" is one function shared with the dish row that answers
# those same lines (occasions.py's `bring-dish`), because two lists of places cannot agree: with a
# list here and a list there, "can i bring food into brazil" was the customs row here and a traybake
# there, and no list of countries is ever complete. geography.py holds the shape - a crossing word,
# a travelling bag, or a direction followed by a place that is not an everyday room or do - and this
# row adds the one thing only it knows: the rule is the one for coming into Great Britain, so a
# destination that is named and is not Britain stands the row down and the bot hedges instead of
# giving one country's rule for another's.
def _comes_across_a_border(understood):
    line = str(understood.get("clean") or understood.get("text") or "").lower()
    return crosses_a_border(line) and not carries_it_out_of_britain(line)


ENTRIES.append(entry(
    "customs-food",
    (("cheese", "ham", "meat", "sausages", "sausage", "bacon", "dairy", "milk", "butter",
      "yoghurt", "sandwich", "sandwiches", "pate", "salami", "chorizo", "food"),
     ("bring back", "bringing back", "take back", "bringing", "into the uk", "into britain",
      "into england", "back home", "home", "customs", "declare", "allowed", "import",
      "from france", "from spain", "from italy", "from portugal", "from germany",
      "from greece", "from ireland", "from the eu", "from europe")),
    "Not meat or dairy: since 2021 you cannot bring ham, sausages, bacon, cheese, milk or butter "
    "into Great Britain from the EU, even for yourself, and a ham sandwich in your bag can be "
    "taken off you. Fish, eggs, fruit, vegetables, bread and cake are fine, and the alcohol "
    "allowance is its own question. If you are not sure, use the red channel and ask.",
    # cooking with it, keeping it fresh and a food allergy are other answers
    avoid=("cook", "cooking", "recipe", "recipes", "freeze", "frozen", "fridge", "keep fresh",
           "goes off", "allergy", "allergic", "lactose", "vegan", "vegetarian", "calories",
           "how long does", "best before", "use by", "shop", "supermarket", "buy",
           "party", "how much wine", "how many bottles", "hangover", "calories in",
           # the duty free allowance is its own row: "can i bring wine back from france" is
           # answered there, and this one is about food you cannot bring at all.
           "wine", "beer", "spirits", "alcohol", "cigarettes", "tobacco", "duty free",
           # a packed lunch is not an import: "can i bring a sandwich to work" was a hedge on main
           # and the meat-and-dairy ban here, so the everyday places a sandwich goes are named
           "to work", "at work", "for work", "office", "lunch", "lunchbox", "picnic",
           "school", "day out", "walk", "hike", "flight meal",
           # and the same list of places as the duty-free row: "can i bring my own food to a
           # restaurant" is a restaurant question, not a border one
           "restaurant", "restaurants", "cafe", "cafes", "café", "the pub", "pub lunch",
           "cinema", "theatre", "theater", "gig", "concert", "festival", "birthday",
           "barbecue", "bbq", "college", "university", "hospital", "ward", "appointment",
           "hotel room", "my hotel", "the hotel", "in the hotel", "airbnb", "campsite",
           "football", "match", "church", "funeral",
           # this is the rule for coming into the UK, and "into the eu" is in the key, so the
           # direction has to be checked: "can i bring cheese into the eu" and "can i bring ham
           # into spain" were answered with the Great Britain ban. A hedge beats the wrong
           # country's rule, so anywhere that is not Britain stands this row down.
           "into the eu", "into eu", "into europe", "into spain", "into france", "into italy",
           "into germany", "into portugal", "into greece", "into ireland", "into holland",
           "into the netherlands", "into belgium", "into poland", "into the usa", "into america",
           "into canada", "into australia", "into new zealand", "into japan", "into china",
           "into dubai", "into turkey", "into mexico", "into thailand", "into india",
           "to spain", "to france", "to italy", "to germany", "to portugal", "to greece",
           "to ireland", "to holland", "to the eu", "to europe", "to america", "to australia",
           "in spain", "in france", "in italy", "in germany", "in portugal", "in greece",
           "in the eu", "in europe"),
    ask=("bring back", "bringing back", "take back", "bringing", "into the uk", "into britain",
         "back home", "customs", "declare", "allowed", "import"),
    # "how much cheese can i bring home" and "how much ham can i bring home" are this rule asked
    # with "how much" in front, and a portion card (calories, 70g of red meat) outscored it: the
    # quantity in the question is how much you may carry, not how much you may eat.
    bias=3, guard=_comes_across_a_border))


# The same rule the other way round, and it is a different rule: the EU ban on personal imports of
# meat and dairy is stricter than the UK's, and it is the one people get caught by at a ferry port
# with a ham sandwich in a cool bag. "can i take meat and dairy into the eu", "can i bring a ham
# sandwich into spain" and "can i bring cheese into the eu" were all search hedges, because the
# customs row above is the into-Great-Britain rule and stands itself down on "into the eu" rather
# than answer with the wrong country's law.
ENTRIES.append(entry(
    "food-into-the-eu",
    (("meat", "meats", "ham", "sandwich", "sandwiches", "cheese", "milk", "butter", "dairy",
      "yoghurt", "yogurt", "sausages", "sausage", "bacon", "cream", "pate", "salami", "chorizo",
      "food", "foods", "snacks"),
     ("into the eu", "into eu", "to the eu", "into europe", "to europe", "into spain", "to spain",
      "into france", "to france", "into italy", "to italy", "into germany", "to germany",
      "into portugal", "to portugal", "into greece", "to greece", "into holland", "to holland",
      "into the netherlands", "to the netherlands", "into belgium", "to belgium", "into poland",
      "to poland", "into ireland", "to ireland", "into austria", "to austria", "into croatia",
      "to croatia", "into cyprus", "to cyprus", "abroad", "on the ferry", "at the border",
      "through customs", "declare")),
    "No - and a ham sandwich counts. Since Brexit you cannot take any meat, milk, cheese, butter, "
    "yoghurt or cream from Great Britain into the EU, even for yourself, and it is taken off you "
    "at the port with a fine. Eat the sandwich before you board. Fish, eggs, bread, cakes, fruit, "
    "vegetables and sweets are fine, and powdered baby milk, baby food and pet food for a medical "
    "reason are the exceptions. Coming back into the UK you may bring 2kg of meat or dairy per "
    "person, so buy the cheese for the trip home rather than taking it out.",
    # the everyday places a sandwich goes are not a border, and the cooking and the keeping of the
    # food are other rows: the same fences as the row above, in the same words
    avoid=("cook", "cooking", "recipe", "recipes", "freeze", "frozen", "fridge", "keep fresh",
           "goes off", "allergy", "allergic", "lactose", "vegan", "vegetarian", "calories",
           "how long does", "best before", "use by", "shop", "supermarket", "buy",
           "party", "wine", "beer", "spirits", "alcohol", "cigarettes", "tobacco", "duty free",
           "to work", "at work", "for work", "office", "lunch", "lunchbox", "picnic",
           "school", "day out", "walk", "hike", "flight meal", "through security", "security",
           "hand luggage", "cabin bag", "cabin bags", "liquids",
           "restaurant", "restaurants", "cafe", "cafes", "café", "the pub", "pub lunch",
           "cinema", "theatre", "theater", "gig", "concert", "festival", "birthday",
           "barbecue", "bbq", "college", "university", "hospital", "ward", "appointment",
           "hotel room", "my hotel", "the hotel", "in the hotel", "airbnb", "campsite",
           "football", "match", "church", "funeral", "my dog", "my cat", "pets",
           # breastfeeding and a baby's bottle are a health question with a number in it
           "breastfeeding", "breast feed", "formula", "baby bottle", "sterilise", "sterilize"),
    # the food ban is the rule people are caught by, and a portion card ("how much cheese can i
    # have") shares every word with it, so this row asks to be read first
    bias=2))


# ---- getting *to* the airport, and sleeping in one ---------------------------------------------
#
# "how do i get to the airport for an early flight" and "can i sleep at the airport" were search
# hedges. The transfer rows stand down on the word "flight" (the clock row owns it), so the other
# direction had nowhere to land, and nobody owns the night at an airport. Both are about the journey
# to the airport rather than out of it, which is why they sit together here.
# A flight at 6am is the early-flight problem - no first train, a taxi booked the night before. A
# station or a friend's lift at a normal hour is not, and it used to get the 5am paragraph because
# "to the airport" was the whole key.
_EARLY_FLIGHT = ("early flight", "early morning flight", "early flight", "6am", "5am", "4am",
                 "seven am", "6 am", "5 am", "before my flight", "night before", "first thing")
_TO_THE_AIRPORT = (
    "Sort the transfer when you book the flight rather than the day before: check the airport's own "
    "site for the trains, buses and the official taxi rank, then pick the one that gets you there "
    "with slack. Aim to be at the airport two hours before a short-haul flight and three before a "
    "long-haul one, and add the walk from the drop-off to the terminal plus the queue at bag drop. "
    "If someone is driving you, find out the drop-off point and any charge first, because at most big "
    "airports you cannot be dropped at the door.")


def _to_the_airport(understood):
    """Getting to the airport: the early-flight problem when the line says early."""
    words = [str(word).lower() for word in (understood.get("words") or ())]
    text = " ".join(words)
    if any(key in words or key in text for key in _EARLY_FLIGHT):
        return _AIRPORT_EARLY_REPLY
    return _TO_THE_AIRPORT


ENTRIES.append(entry(
    "to-the-airport",
    (("airport", "airports", "terminal", "terminals"),
     ("how do i get", "get to", "get there", "to the airport", "travel to the airport",
      "travel to the terminal", "getting to the airport", "for an early flight",
      "early flight", "early morning flight", "night before", "lift to the airport",
      "taxi to the airport")),
    lambda memory, understood: _to_the_airport(understood),
    # the clock is airport-arrival's question and the transfer out of the airport is
    # airport-to-city's, so both kinds of line must pass this one by
    avoid=("how early", "how long before", "how long", "what time", "when should", "hours before",
           "minutes before", "enough time", "too early", "miss my flight", "make my flight",
           "what gate", "which gate", "parking", "car park", "drop off charge", "pick up",
           "collect someone", "from the airport", "into town", "to the city", "to the centre",
           "airport lounge", "my flight land", "flight delayed", "flight cancelled")))
ENTRIES.append(entry(
    "sleep-at-the-airport",
    (("airport", "airports", "terminal", "terminals", "layover", "stopover"),
     ("sleep", "sleeping", "slept", "overnight", "spend the night", "stay the night",
      "night at the airport", "night in the airport", "sleep at", "sleep in", "kip", "nap",
      "a few hours sleep", "some sleep")),
    lambda memory, understood: _AIRPORT_SLEEP_REPLY,
    # a child who will not sleep in an airport is not a thing, but a child who will not sleep at all
    # is the sleep row's question, and the lines below are the ones that must not be taken for this
    avoid=("my son", "my daughter", "my child", "my baby", "my toddler", "bedtime", "night waking",
           "wakes up", "wake up", "insomnia", "can't sleep", "cannot sleep", "cant sleep",
           "jet lag", "on the plane", "on a plane", "in the car", "in a hotel", "at night")))

# --- how far it is from one place to another -----------------------------------------------
# Every "how far is cork from dublin" line on main reached the search shrug, because the places
# were kept as prose and prose cannot be subtracted. A city is a latitude, a longitude and a
# road group; the rest is arithmetic, so one table answers every pair of places in it. The
# coordinates are city-centre to the nearest tenth of a degree, which is a mile of slack on a
# straight-line estimate and invisible in the answer.
_PLACE = {
    # Britain and Ireland
    "london": (51.5, -0.1, "uk"), "manchester": (53.5, -2.2, "uk"),
    "birmingham": (52.5, -1.9, "uk"), "liverpool": (53.4, -3.0, "uk"),
    "leeds": (53.8, -1.5, "uk"), "sheffield": (53.4, -1.5, "uk"),
    "newcastle": (55.0, -1.6, "uk"), "nottingham": (53.0, -1.2, "uk"),
    "bristol": (51.5, -2.6, "uk"), "cardiff": (51.5, -3.2, "uk"),
    "swansea": (51.6, -4.0, "uk"), "edinburgh": (55.9, -3.2, "uk"),
    "glasgow": (55.9, -4.3, "uk"), "aberdeen": (57.1, -2.1, "uk"),
    "inverness": (57.5, -4.2, "uk"), "belfast": (54.6, -5.9, "uk"),
    "derry": (55.0, -7.3, "uk"), "cambridge": (52.2, 0.1, "uk"),
    "oxford": (51.8, -1.3, "uk"), "york": (53.9, -1.1, "uk"),
    "bath": (51.4, -2.4, "uk"), "brighton": (50.8, -0.1, "uk"),
    "southampton": (50.9, -1.4, "uk"), "portsmouth": (50.8, -1.1, "uk"),
    "plymouth": (50.4, -4.1, "uk"), "exeter": (50.7, -3.5, "uk"),
    "norwich": (52.6, 1.3, "uk"), "leicester": (52.6, -1.1, "uk"),
    "coventry": (52.4, -1.5, "uk"), "hull": (53.7, -0.3, "uk"),
    "preston": (53.8, -2.7, "uk"), "blackpool": (53.8, -3.1, "uk"),
    "milton keynes": (52.0, -0.8, "uk"), "reading": (51.5, -1.0, "uk"),
    "luton": (51.9, -0.4, "uk"), "stansted": (51.9, 0.2, "uk"),
    "heathrow": (51.5, -0.5, "uk"), "gatwick": (51.2, -0.2, "uk"),
    "dover": (51.1, 1.3, "uk"), "canterbury": (51.3, 1.1, "uk"),
    "windermere": (54.4, -2.9, "uk"), "keswick": (54.6, -3.1, "uk"),
    "snowdon": (53.1, -4.1, "uk"), "ben nevis": (56.8, -5.0, "uk"),
    "fort william": (56.8, -5.1, "uk"), "st ives": (50.2, -5.5, "uk"),
    "newquay": (50.4, -5.1, "uk"), "dublin": (53.3, -6.3, "ie"),
    "cork": (51.9, -8.5, "ie"), "galway": (53.3, -9.0, "ie"),
    "limerick": (52.7, -8.6, "ie"), "waterford": (52.3, -7.1, "ie"),
    "belfast city": (54.6, -5.9, "ie"), "kerry": (52.2, -9.7, "ie"),
    "sligo": (54.3, -8.5, "ie"), "donegal": (54.7, -8.1, "ie"),
    # Europe
    "paris": (48.9, 2.4, "eu"), "lyon": (45.8, 4.8, "eu"), "marseille": (43.3, 5.4, "eu"),
    "nice": (43.7, 7.3, "eu"), "bordeaux": (44.8, -0.6, "eu"), "toulouse": (43.6, 1.4, "eu"),
    "brussels": (50.8, 4.4, "eu"), "bruges": (51.2, 3.2, "eu"), "ghent": (51.1, 3.7, "eu"),
    "antwerp": (51.2, 4.4, "eu"), "amsterdam": (52.4, 4.9, "eu"),
    "rotterdam": (51.9, 4.5, "eu"), "the hague": (52.1, 4.3, "eu"),
    "eindhoven": (51.4, 5.5, "eu"), "luxembourg": (49.6, 6.1, "eu"),
    "berlin": (52.5, 13.4, "eu"), "munich": (48.1, 11.6, "eu"),
    "hamburg": (53.6, 10.0, "eu"), "frankfurt": (50.1, 8.7, "eu"),
    "cologne": (50.9, 6.9, "eu"), "dusseldorf": (51.2, 6.8, "eu"),
    "stuttgart": (48.8, 9.2, "eu"), "dresden": (51.1, 13.7, "eu"),
    "nuremberg": (49.5, 11.1, "eu"), "heidelberg": (49.4, 8.7, "eu"),
    "madrid": (40.4, -3.7, "eu"), "barcelona": (41.4, 2.2, "eu"),
    "seville": (37.4, -6.0, "eu"), "valencia": (39.5, -0.4, "eu"),
    "malaga": (36.7, -4.4, "eu"), "bilbao": (43.3, -2.9, "eu"),
    "granada": (37.2, -3.6, "eu"), "palma": (39.6, 2.7, "eu"),
    "lisbon": (38.7, -9.1, "eu"), "porto": (41.1, -8.6, "eu"),
    "faro": (37.0, -7.9, "eu"), "rome": (41.9, 12.5, "eu"),
    "milan": (45.5, 9.2, "eu"), "naples": (40.9, 14.3, "eu"),
    "venice": (45.4, 12.3, "eu"), "florence": (43.8, 11.3, "eu"),
    "bologna": (44.5, 11.3, "eu"), "turin": (45.1, 7.7, "eu"),
    "palermo": (38.1, 13.4, "eu"), "vienna": (48.2, 16.4, "eu"),
    "salzburg": (47.8, 13.0, "eu"), "innsbruck": (47.3, 11.4, "eu"),
    "zurich": (47.4, 8.5, "eu"), "geneva": (46.2, 6.1, "eu"),
    "bern": (46.9, 7.4, "eu"), "basel": (47.6, 7.6, "eu"),
    "prague": (50.1, 14.4, "eu"), "budapest": (47.5, 19.0, "eu"),
    "krakow": (50.1, 20.0, "eu"), "warsaw": (52.2, 21.0, "eu"),
    "danzig": (54.4, 18.7, "eu"), "bratislava": (48.1, 17.1, "eu"),
    "ljubljana": (46.1, 14.5, "eu"), "zagreb": (45.8, 16.0, "eu"),
    "dubrovnik": (42.6, 18.1, "eu"), "split": (43.5, 16.4, "eu"),
    "belgrade": (44.8, 20.5, "eu"), "bucharest": (44.4, 26.1, "eu"),
    "sofia": (42.7, 23.3, "eu"), "athens": (38.0, 23.7, "eu"),
    "thessaloniki": (40.6, 23.0, "eu"), "istanbul": (41.0, 29.0, "eu"),
    "copenhagen": (55.7, 12.6, "eu"), "aarhus": (56.2, 10.2, "eu"),
    "oslo": (59.9, 10.8, "eu"), "bergen": (60.4, 5.3, "eu"),
    "stockholm": (59.3, 18.1, "eu"), "gothenburg": (57.7, 12.0, "eu"),
    "helsinki": (60.2, 24.9, "eu"), "reykjavik": (64.1, -21.9, "eu"),
    "tallinn": (59.4, 24.8, "eu"), "riga": (56.9, 24.1, "eu"),
    "vilnius": (54.7, 25.3, "eu"), "kyiv": (50.5, 30.5, "eu"),
    "lviv": (49.8, 24.0, "eu"), "moscow": (55.8, 37.6, "eu"),
    "st petersburg": (59.9, 30.3, "eu"), "malta": (35.9, 14.5, "eu"),
    "valletta": (35.9, 14.5, "eu"), "nicosia": (35.2, 33.4, "eu"),
    # North America
    "new york": (40.7, -74.0, "us"), "boston": (42.4, -71.1, "us"),
    "washington": (38.9, -77.0, "us"), "philadelphia": (39.95, -75.2, "us"),
    "chicago": (41.9, -87.6, "us"), "detroit": (42.3, -83.0, "us"),
    "cleveland": (41.5, -81.7, "us"), "pittsburgh": (40.4, -80.0, "us"),
    "atlanta": (33.7, -84.4, "us"), "miami": (25.8, -80.2, "us"),
    "orlando": (28.5, -81.4, "us"), "tampa": (28.0, -82.5, "us"),
    "nashville": (36.2, -86.8, "us"), "memphis": (35.1, -90.0, "us"),
    "new orleans": (29.95, -90.1, "us"), "houston": (29.8, -95.4, "us"),
    "dallas": (32.8, -96.8, "us"), "austin": (30.3, -97.7, "us"),
    "san antonio": (29.4, -98.5, "us"), "denver": (39.7, -105.0, "us"),
    "salt lake city": (40.8, -111.9, "us"), "phoenix": (33.4, -112.1, "us"),
    "las vegas": (36.2, -115.1, "us"), "los angeles": (34.1, -118.2, "us"),
    "san diego": (32.7, -117.2, "us"), "san francisco": (37.8, -122.4, "us"),
    "seattle": (47.6, -122.3, "us"), "portland": (45.5, -122.7, "us"),
    "minneapolis": (45.0, -93.3, "us"), "st louis": (38.6, -90.2, "us"),
    "kansas city": (39.1, -94.6, "us"), "indianapolis": (39.8, -86.2, "us"),
    "columbus": (40.0, -83.0, "us"), "baltimore": (39.3, -76.6, "us"),
    "charleston": (32.8, -79.9, "us"), "savannah": (32.1, -81.1, "us"),
    "honolulu": (21.3, -157.9, "us"), "anchorage": (61.2, -149.9, "us"),
    "toronto": (43.7, -79.4, "ca"), "montreal": (45.5, -73.6, "ca"),
    "ottawa": (45.4, -75.7, "ca"), "quebec": (46.8, -71.2, "ca"),
    "vancouver": (49.3, -123.1, "ca"), "calgary": (51.0, -114.1, "ca"),
    "edmonton": (53.5, -113.5, "ca"), "winnipeg": (49.9, -97.1, "ca"),
    "halifax": (44.6, -63.6, "ca"), "banff": (51.2, -115.6, "ca"),
    "mexico city": (19.4, -99.1, "mx"), "cancun": (21.2, -86.8, "mx"),
    "havana": (23.1, -82.4, "other"), "san juan": (18.5, -66.1, "other"),
    # South America and Africa
    "rio de janeiro": (-22.9, -43.2, "other"), "sao paulo": (-23.6, -46.6, "other"),
    "buenos aires": (-34.6, -58.4, "other"), "lima": (-12.0, -77.0, "other"),
    "bogota": (4.7, -74.1, "other"), "santiago": (-33.4, -70.7, "other"),
    "cape town": (-33.9, 18.4, "other"), "johannesburg": (-26.2, 28.0, "other"),
    "durban": (-29.9, 31.0, "other"), "nairobi": (-1.3, 36.8, "other"),
    "lagos": (6.5, 3.4, "other"), "accra": (5.6, -0.2, "other"),
    "casablanca": (33.6, -7.6, "other"), "marrakesh": (31.6, -8.0, "other"),
    "tunis": (36.8, 10.2, "other"), "cairo": (30.0, 31.2, "other"),
    "hurghada": (27.3, 33.8, "other"), "addis ababa": (9.0, 38.7, "other"),
    "zanzibar": (-6.2, 39.2, "other"), "mauritius": (-20.2, 57.5, "other"),
    # Asia, the Middle East and Oceania
    "dubai": (25.2, 55.3, "other"), "abu dhabi": (24.5, 54.4, "other"),
    "doha": (25.3, 51.5, "other"), "tel aviv": (32.1, 34.8, "other"),
    "jerusalem": (31.8, 35.2, "other"), "ankara": (39.9, 32.9, "other"),
    "tehran": (35.7, 51.4, "other"), "delhi": (28.6, 77.2, "other"),
    "new delhi": (28.6, 77.2, "other"), "mumbai": (19.1, 72.9, "other"),
    "goa": (15.5, 73.8, "other"), "jaipur": (26.9, 75.8, "other"),
    "kolkata": (22.6, 88.4, "other"), "bengaluru": (13.0, 77.6, "other"),
    "kathmandu": (27.7, 85.3, "other"), "colombo": (6.9, 79.9, "other"),
    "bangkok": (13.8, 100.5, "other"), "chiang mai": (18.8, 99.0, "other"),
    "phuket": (7.9, 98.4, "other"), "kuala lumpur": (3.1, 101.7, "other"),
    "singapore": (1.35, 103.8, "other"), "jakarta": (-6.2, 106.8, "other"),
    "bali": (-8.7, 115.2, "other"), "manila": (14.6, 121.0, "other"),
    "hong kong": (22.3, 114.2, "other"), "shanghai": (31.2, 121.5, "other"),
    "beijing": (39.9, 116.4, "other"), "seoul": (37.6, 127.0, "other"),
    "tokyo": (35.7, 139.7, "other"), "osaka": (34.7, 135.5, "other"),
    "kyoto": (35.0, 135.8, "other"), "sapporo": (43.1, 141.4, "other"),
    "taipei": (25.0, 121.5, "other"), "sydney": (-33.9, 151.2, "au"),
    "melbourne": (-37.8, 145.0, "au"), "brisbane": (-27.5, 153.0, "au"),
    "perth": (-31.95, 115.9, "au"), "adelaide": (-34.9, 138.6, "au"),
    "cairns": (-16.9, 145.8, "au"), "hobart": (-42.9, 147.3, "au"),
    "auckland": (-36.8, 174.8, "nz"), "wellington": (-41.3, 174.8, "nz"),
    "christchurch": (-43.5, 172.6, "nz"), "queenstown": (-45.0, 168.7, "nz"),
    "fiji": (-17.7, 178.1, "other"),
}

# The two-place shape: "how far is cork from dublin", "distance between london and leeds",
# "how long does it take to drive to manchester from bristol". Worded as a phrase, because a bare
# "far" is in "how far can i go on 20 pounds of petrol", which is a money question.
_FAR_ASKED = ("how far is", "how far are", "how far from", "how far away is",
              "how far away are", "distance from", "distance between", "distance to",
              "the distance", "how long does it take to get", "how long does it take to drive",
              "how long does it take to travel", "how long to drive", "how long is the drive",
              "how long is the journey", "how many miles is", "how many miles from",
              "how many miles between", "how many km is", "how many kilometres is",
              "how far apart")

# Motorway averages for a network, in km/h, and named as the network is above.
_ROAD_SPEED = {"gb": 90, "ie": 85, "eu": 90, "na": 95, "au": 95, "nz": 85}

# A straight line leaves out every bend and both town centres, and the shorter the hop the
# bigger the share they are: a 15 km allowance plus a quarter covers Bristol to Cardiff
# and London to Edinburgh at once.
_ROAD_FACTOR, _ROAD_ALLOWANCE = 1.25, 15

# What you can drive to without a boat or a plane. Great Britain is one island and Ireland
# another, so Dublin is not a drive from London however the road number reads; a place that is
# its own island is its own network, which is what "other" stands for.
_NETWORK_NAME = {"uk": "gb", "ie": "ie", "eu": "eu", "us": "na", "ca": "na", "mx": "na",
                 "au": "au", "nz": "nz"}
_NETWORK_FIX = {"belfast": "ie", "belfast city": "ie", "derry": "ie"}


def _network(place):
    if place in _NETWORK_FIX:
        return _NETWORK_FIX[place]
    code = _PLACE[place][2]
    if code == "other":
        return place
    return _NETWORK_NAME.get(code, code)


def _places_named(said):
    """The place names in the line, longest first, so "new york" is not also "york"."""
    found = []
    for name in sorted(_PLACE, key=len, reverse=True):
        start = 0
        while True:
            at = said.find(name, start)
            if at < 0:
                break
            before = said[at - 1] if at else " "
            after = said[at + len(name):at + len(name) + 1]
            whole = (not before.isalnum()) and (not after.isalnum())
            overlaps = any(lo < at + len(name) and at < hi for lo, hi, _ in found)
            if whole and not overlaps:
                found.append((at, at + len(name), name))
            start = at + 1
    found.sort()
    return [name for _, _, name in found]


def _km(first, second):
    lat1, lon1, _ = _PLACE[first]
    lat2, lon2, _ = _PLACE[second]
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    h = (math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(h))


def _nearest_five(number):
    return int(round(number / 5.0) * 5)


def _miles(km):
    miles = km * 0.62137
    # Five-mile rungs are for a long drive. On a short hop they turn 3.8 miles into "5 miles",
    # which is 8 km: the number shown has to be the number meant.
    return _nearest_five(miles) if miles >= 20 else int(round(miles))


def _drive_time(km, group):
    return _duration(km / float(_ROAD_SPEED.get(group, 80)))


def _duration(hours):
    whole = int(hours)
    minutes = int(round((hours - whole) * 60 / 5.0) * 5)
    if minutes == 60:
        whole, minutes = whole + 1, 0
    if whole == 0:
        return "%d minutes" % minutes
    unit = "hour" if whole == 1 else "hours"
    if minutes == 0:
        return "%d %s" % (whole, unit)
    return "%d %s %d minutes" % (whole, unit, minutes)


def _distance_between(memory, understood):
    said = str(understood.get("clean") or understood.get("text") or "").lower()
    if not any(word in said for word in _FAR_ASKED):
        return None
    names = [name for name in _places_named(said) if name != "belfast city"]
    if len(names) < 2:
        return None
    first, second = names[0], names[1]
    if first == second:
        return None
    km = _km(first, second)
    miles = _miles(km)
    said_km = _nearest_five(km)
    net_one, net_two = _network(first), _network(second)
    there = "%s to %s" % (first.title(), second.title())
    road = _nearest_five(km * _ROAD_FACTOR + _ROAD_ALLOWANCE)
    # The short hop is a taxi or a bus, and a bike only where a bike is the honest answer: half
    # an hour of pedalling covers about 8 km, so a 40 km pair told to "get on a bike" is a false
    # promise. The bike time is worked out from the distance and only named under 10 km; the test
    # below the sentence uses the same rounded number the sentence shows.
    if said_km < 40:
        how = "a taxi or a bus"
        if said_km <= 10:
            how = "a taxi, a bus or about %s on a bike" % _duration(km / 16.0)
        return ("%s is only about %d km (%d miles) apart - closer than most people think, so it "
                "is %s rather than a journey." % (there, said_km, miles, how))
    if net_one == net_two and net_one in _ROAD_SPEED and km <= 1200:
        return ("%s is about %d km (%d miles) in a straight line and roughly %d km (%d miles) by "
                "road, so allow about %s of driving without stops. That is the motorway figure; "
                "town traffic or a slow A-road at either end adds to it."
                % (there, said_km, miles, road, _miles(road),
                   _drive_time(road, net_one)))
    if km <= 1200 and net_one != net_two:
        crossing = {net_one, net_two}
        air = _duration(km / 700.0 + 0.8)
        if crossing == {"gb", "ie"}:
            return ("%s is about %d km (%d miles) in a straight line, with the Irish Sea in "
                    "between: a flight is about %s once the airports are counted, and the ferry "
                    "runs to a timetable rather than a distance." % (there, said_km, miles, air))
        if crossing == {"gb", "eu"}:
            return ("%s is about %d km (%d miles) in a straight line, with the Channel in "
                    "between: the tunnel does take cars, but the Eurostar or a flight of about "
                    "%s beats driving it once the check-in and the parking are counted."
                    % (there, said_km, miles, air))
        return ("%s is about %d km (%d miles) in a straight line, with water in between: a "
                "flight is about %s once the airports are counted, and the ferry runs to a "
                "timetable rather than a distance." % (there, said_km, miles, air))
    if km <= 1200:
        return ("%s is about %d km (%d miles) in a straight line. The road route is longer than "
                "that - allow roughly %s of driving, or take the train, which is usually quicker "
                "between two cities that close."
                % (there, said_km, miles, _drive_time(road, "eu")))
    if km < 3500:
        return ("%s is about %d km (%d miles) in a straight line, so roughly %s in the air once "
                "the climb and the landing are counted - too far to drive in a day."
                % (there, said_km, miles, _duration(km / 800.0 + 1)))
    return ("%s is about %d km (%d miles) in a straight line, which is a long-haul flight of "
            "%.0f hours or more, and nobody drives it."
            % (there, said_km, miles, (km / 850.0) + 2))


ENTRIES.append(entry(
    "far-between-places", (_FAR_ASKED + ("how far", "miles apart", "far apart", "distance"),
                           tuple(sorted(_PLACE)) + ("miles", "km", "kilometres", "kilometers",
                                                    "between", "drive", "driving", "journey")),
    _distance_between,
    # a sum of money with no place in it is the petrol-budget row, and a cooking, charging or
    # healing question that happens to say "how long does it take" is not two places either
    avoid=("how far can i go", "how far will", "how much petrol", "fuel", "petrol",
           "on 20 pounds", "how long does it take to boil", "boil",
           "how long does it take to cook", "cook", "how long does it take to charge",
           "charge", "how long does it take to heal", "heal", "how long does it take to arrive",
           "how long does it take to get there", "how long does it take to learn",
           "how long does it take to bake", "how long does it take to digest")))

# An adapter changes the pins and nothing else: "how do i use a travel adaptor" and "will my
# hairdryer work abroad" were both a shrug, and the voltage is the thing that catches people out.
ENTRIES.append(entry(
    "using-an-adaptor",
    (("adapter", "adaptor", "hairdryer", "hair dryer", "straighteners", "curling tongs",
      "converter", "dual voltage", "electric shaver"),
     ("how do i use", "how to use", "use", "using", "work", "works", "working", "abroad",
      "away", "travel", "holiday", "trip", "voltage", "volts", "converter")),
    "The adapter changes the shape of the pins, not the voltage: put it in the wall socket, plug "
    "your own charger into it, and check the small print on the charger says 100-240V before you "
    "pack it. The things to check are the ones with a motor or a heating element - a hairdryer, "
    "straighteners, a kettle - because a 120V appliance from the US on a 230V supply needs a "
    "converter and not an adapter, while a dual-voltage travel hairdryer is cheaper and safer "
    "than a good converter.",
    bias=1,
    # which country uses which socket is the plug-country card's question, and a line that names
    # only the country is asking that, not how to use the thing
    avoid=("type c", "type g", "type e", "type f", "round pins", "square pins", "flat pins",
           "same as the uk", "sockets in"),
))
