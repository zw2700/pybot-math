"""A word that names two everyday things, read from the whole line rather than the word.

Some words are the name of one thing in a line and another thing in the next. "room" is the space
in a kitchen and a bed for the night; "bat" is a wooden thing you hit a ball with even though the
line says nothing about a game. The knowledge base matches on words, so a row that owns one sense
answers the other sense's line: "i have no room in my kitchen" was sent the hotel-overbooking card,
because "room" and "no room" are that row's key, and the same line typed "no room in my kitchen"
reached the storage answer. The rows had fenced each other with phrases ("have no room" was on the
storage row's `avoid` list to stop a hotel line being told to put a shelf up), so the same words
meant two things and only the phrase said which.

Which sense a line means is not in the word: it is in the rest of the sentence. "in my kitchen",
"cupboard", "put away", "too much stuff" say the space; "hotel", "booking", "two nights",
"reception" say the bed. So this module reads the whole line - every word of it, wherever the word
stands - and reports the sense the line supports.

The trick is the word nobody says: a line that says nothing either way gets **no reading**, and the
rows that own a sense stand aside instead of guessing. "my bat is broken" names a bat and a break,
and nothing in it says the animal or the game, so `senses()` says nothing about it and a row keyed
on the game does not answer it. Guessing is what put the cricket coaching on a broken bat.

`understand()` reports the lot under one key, `sense`: a dict of word to the sense the line
supports, holding only the words the line actually settles. A row guards on it with a plain test,
so a word added here is a row's guard away from fixing every line about it.
"""

# The words that carry two everyday senses, each with the words that say its sense. A cue is any
# word of the line, in any order: the point of the reading is that the subject is the rest of the
# sentence, not the neighbour of the ambiguous word.
#
# One word must not cue two senses of the same word, or the line it is meant to settle reads as a
# tie and nothing is reported.
CUES = {
    # The space in a place, against a bed for the night. A size word says the space when the person
    # is talking about the room they have ("our hotel room is tiny"), and says nothing about it when
    # they are asking for one ("i need a small hotel room"), so the words for wanting one are cues
    # on the booking side along with the place and the luggage a bed for the night comes with.
    "room": {
        "space": frozenset("""
            kitchen kitchens bedroom bedrooms bathroom bathrooms cupboard cupboards wardrobe
            wardrobes freezer fridge car boot shed garage loft attic cellar hall hallway landing
            landing flat house home drawer drawers shelf shelves cupboard worktop bench desk
            storage store storing put fit fits fitting tidy tidier tidy-up clutter stuff boxes
            box cupboard space cramped clutter pots pans utensils microwave toaster kettle
            small tiny little cramped narrow cramped squeeze squashed poky pokey tight
            """.split()),
        "booking": frozenset("""
            hotel hotels motel hostel guest house booking bookings booked book reservation
            reservations reception receptionist desk check checkin check-in concierge night
            nights twin double suite ensuite en-suite overbooked upgrade holiday stay staying
            need needs needed want wants wanted prefer rather looking searching
            traveller traveler luggage suitcase suitcases case cases bags abroad airport
            flight trip refunded
            """.split()),
    },
    # A wooden thing for a ball, against the animal.
    "bat": {
        "sport": frozenset("""
            cricket bowling bowler batsman batsmen innings wicket wickets pitch stumps willow
            grip oiling oil knocked-in handle tennis ping pong table shot cover drive yorker
            spinner seamer nets net match club league batting batsman's bails crease
            """.split()),
        "animal": frozenset("""
            flew fly flying loft attic roof rafters eaves belfry wings wing bitten rabies
            droppings squeaking squeak colony pup hibernating hibernate dusk rescued
            hedgehog tree trees garden shed hole
            """.split()),
    },
    # The bus, the person who runs the session, and the old word for a sofa.
    "coach": {
        "vehicle": frozenset("""
            train trains rail railway station stations platform platform ticket tickets journey
            journeys seat seats carriage carriages bus buses megabus national-express travel
            travelling traveling trip legroom route timetable delay delays luggage left-luggage
            book booked booking reservations departures
            """.split()),
        "teacher": frozenset("""
            football rugby netball cricket hockey tennis kids child children junior juniors
            under u7 u8 u9 u10 u11 u12 u13 u14 u15 u16 session sessions drill drills players
            squad tactics coaching goalkeeper striker defenders midfield training skills
            """.split()),
        "furniture": frozenset("""
            sofa settee couch lounge upholstery reupholster reupholstered fabric cushions
            cushion seater armchair furniture corner three-piece living rooms room front-room
            """.split()),
    },
    # The heat in the air, against the qualification, against the corner of a shape. The line
    # settles it: a season, the weather or the heat says the air; uni, a course or a class says
    # the qualification. A figure in front of the plural settles it on its own ("35 degrees"),
    # which is what a forecast and a wedding abroad have in common and nothing else does.
    "degrees": {
        "temperature": frozenset("""
            hot cold warm warmer warmest freezing boiling heat humid humidity celsius
            fahrenheit weather forecast summer winter autumn spring sunny sun shade outside
            today tonight tomorrow thermometers thermometer fever thermostat oven roasting
            heatwave heatwaves sweaty sunscreen brollies
            """.split()),
        "university": frozenset("""
            uni university universities college ucas graduate graduates graduated graduation
            student students masters bachelors bachelor bsc ba ma phd honours honours-degree
            dissertation campus term semester freshers results classified first-class 2:1
            studying studied study course courses academic tutor lecturer professor
            """.split()),
        "angle": frozenset("""
            angle angles geometry triangle protractor rotate rotation rotated rotation
            turnaround corner corners bend bends slope sloped incline gradient
            """.split()),
    },
    # Late for something, against late in the cycle. One word, and the rest of the line says
    # which: a boss, a bus, a meeting and a deadline are things a person is late *for*, while a
    # period, a test and a pill are the cycle. Without it the cycle card answered "they fired me
    # for being late every day" with the advice for a period that has not come, which is the
    # opposite of what the line was about - and "im late for work again" with it too.
    #
    # The two lists are the named things only. "days" and "weeks" are out of it, and so are a
    # bare "again" and "every day": "every day" is the shape of a job ("fired for being late
    # every day") as much as of a cycle, and "two days late" is a parcel as often as a period.
    # A line that says nothing either way keeps no reading, so every row that asks this question
    # answers it exactly as it did before.
    "late": {
        "time": frozenset("""
            work job boss manager office meeting interview deadline shift roster rota overtime
            colleague bus buses train tram tube flight plane ferry fired sacked redundant
            school class lesson nursery childcare pickup collection homework exam detention
            court dentist hairdresser barber cinema theatre match kickoff traffic jam queue
            road motorway accident closed cancelled overslept alarm form
            """.split()),
        "cycle": frozenset("""
            period missed pregnant pregnancy test bleed bleeding spotting cramp pill
            contraceptive ovulate ovulating ovulation conceive conceiving conception cycle
            womb trimester midwife
            """.split()),
    },
}

# A measure word with a figure in front of it is the measure, and only the measure: "its 35
# degrees" is the heat in the air, and so is "wedding in italy 35 degrees". The figure settles
# nothing when the line says another sense in words - "i got 35 degrees from uni" - so this is a
# fallback for a line that would otherwise read neither way.
CUES_AFTER_A_FIGURE = {"degrees": "temperature"}
_A_FIGURE = frozenset("""
    one two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty
    sixty seventy eighty ninety hundred thousand zero
    """.split())


def _a_figure_before(line, word):
    """Whether a figure stands right in front of `word` in the line as typed."""
    forms = _forms(word)
    for i, token in enumerate((line.get("norm") or [])):
        if str(token).lower() not in forms or i == 0:
            continue
        before = str(line["norm"][i - 1]).lower().strip(".,!?;:")
        if before.isdigit() or before in _A_FIGURE:
            return True
    return False


def _forms(word):
    """The word and the plain form the readers compare it by ("nights" is "night")."""
    forms = {word}
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        forms.add(word[:-1])
    if len(word) > 5 and word.endswith("es"):
        forms.add(word[:-2])
    return forms


def _the_words(line):
    """Every word of the line, from the reading, folded to the forms a cue is written in."""
    words = []
    for word in (line.get("norm") or []):
        words.append(str(word).lower())
    clean = str(line.get("clean") or "").lower()
    if clean:
        words.extend(clean.split())
    return {form for word in words for form in _forms(word)}


def _how_many_words(cues, words):
    """How many of the line's words one sense accounts for, each one counted once.

    A cue list is written in the forms a person types, so it often holds a word and its plural
    beside each other ("hotel hotels", "kitchen kitchens"). Counting the list rather than the
    words then lets one word said once outvote a line that says two other things: "my hotel room
    is too small" scored booking 2 and space 1 on the word `hotel` alone.
    """
    return len({form for cue in cues for form in (_forms(cue) & words)})


def senses(line):
    """`{word: sense}` for each two-sense word whose sense the whole line supports.

    The line is the `normalise()` reading, so `norm` and `clean` are both read. A sense needs one
    more cue than the other sense of the same word: a tie is a line that says both (or neither),
    and there the honest answer is no reading at all.
    """
    if not isinstance(line, dict):
        return {}
    words = _the_words(line)
    if not words:
        return {}
    found = {}
    for word, by_sense in CUES.items():
        if not (_forms(word) & words):
            continue
        scored = sorted(((_how_many_words(cues, words), sense)
                         for sense, cues in by_sense.items()), reverse=True)
        if len(scored) < 2:
            continue
        if scored[0][0] == 0:
            # Nothing in the line says either sense in words: a figure in front of the measure
            # word is the one thing that still settles it ("35 degrees" is the heat in the air).
            if word in CUES_AFTER_A_FIGURE and _a_figure_before(line, word):
                found[word] = CUES_AFTER_A_FIGURE[word]
            continue
        if scored[0][0] == scored[1][0]:
            continue
        found[word] = scored[0][1]
    return found
