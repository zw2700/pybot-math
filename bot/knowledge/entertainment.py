"""Films, TV, books, podcasts and games: what to watch, read or play next.

The answers lane owns this domain. One Entry per taste, keyed by the thing someone is
looking for (a funny family film, something like The Martian, a short-rule board game),
and named works in the reply so there is always something concrete to pick up.
"""
import re

from ..compose.repair import owns_the_deed
from ..understanding.attempts import asks_for_one_more
from .lookup import entry


# A weekend in a city is the city guide's question, and "for the weekend" beat it: "what should i
# do in lisbon for a weekend" and "what should i do in rome for a weekend" were answered with "one
# thing out of the house and one thing at home". The city is the thing the free time is for, the
# same way a holiday and a trip already are, and there are too many city names to list here - so
# the row asks travel's own table whether the line named one.
_AMBIGUOUS_CITY_WORDS = ("bath",)


def _a_chess_line(understood):
    """True when "castle" means the chess move, not the building you visit.

    "what is a castle" is history, and it was the castling card because the row keys the noun.
    A chess word in the line settles it, and so does the verb: "how do i castle", "when should i
    castle" are the move even though they name no piece.
    """
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text")).lower()
    if _CHESS_WORDS.search(said):
        return True
    return bool(_CASTLING_VERB.search(said))


_CHESS_WORDS = re.compile(r"\b(chess|chessboard|rook|rooks|king|kings|kingside|queenside|"
                          r"queen|pawn|pawns|bishop|knight|checkmate|check mate|castling|"
                          r"moves?)\b")
_CASTLING_VERB = re.compile(r"\b(how|when|can i|should i|do i|where do i|why)\b[^.?!]{0,18}"
                            r"\bcastl(e|es|ed|ing)\b")


def _no_city_is_named(understood):
    """False when the line names a city a guide answers for: that is where the weekend is."""
    from .travel import CITIES

    clean = " %s " % str(understood.get("clean") or "").lower().replace("-", " ")
    for city in CITIES:
        if city in _AMBIGUOUS_CITY_WORDS:
            continue
        if re.search(r"(?<![a-z])%s(?![a-z])" % re.escape(city), clean):
            return False
    return True


# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("entertainment", "creative")

# Statements about watching something that is already chosen are not requests for a pick.
WATCHING = ("i'm watching", "im watching", "are watching", "i was watching",
            "we were watching", "we watched a", "we watched the",
            "i watched a", "i watched the")

# A child in the line needs a family pick, not the adult list. Name the people a child is
# actually called ("my daughter is 5") as well as the plain words.
CHILD = ("child", "children", "kid", "kids", "year old", "year-old", "toddler",
         "baby", "grandchild", "grandchildren", "daughter", "son", "niece", "nephew",
         "grandson", "granddaughter")

# "My kids watch too much tv" is a screen-time line, not a request for a film. A bare
# "hours" used to be here, and it took every limit off a pick as well: "a christmas film under
# two hours" is a kind of film with an evening's length in it, not a screen-time worry, so the
# hours are read as the shapes a worry about them takes.
SCREEN_TIME = ("too much", "screen time", "all day", "hours a day", "how many hours",
               "hours of screen", "hours of tv", "hours watching", "hours in front",
               "bedtime", "limit", "how long should", "how long can")

# A sports line wants the match, not a film list.
SPORT = ("cricket", "football", "rugby", "tennis", "match", "darts", "golf", "boxing",
         "race", "f1", "grand prix", "sport")

# --- who made it -------------------------------------------------------------
# People ask for the maker of a named work, not for a fact about a subject: "who wrote
# 1984", "who painted the mona lisa", "who composed the ninth symphony". One table keyed
# by the work answers every way of asking, so a new work is one line of data and no new
# entry: the entry below only has to find the work in the line.
#
# (maker, the one detail worth adding, the kind of thing it is)
WORKS = {
    # books
    "1984": ("George Orwell", "published in 1949; his real name was Eric Blair",
             "novel"),
    "nineteen eighty four": ("George Orwell", "published in 1949", "novel"),
    "animal farm": ("George Orwell", "published in 1945", "novel"),
    "pride and prejudice": ("Jane Austen", "published in 1813", "novel"),
    "jane eyre": ("Charlotte Bronte", "published in 1847 under the name Currer Bell",
                  "novel"),
    "wuthering heights": ("Emily Bronte", "her only novel, published in 1847", "novel"),
    "great expectations": ("Charles Dickens", "published in 1861", "novel"),
    "a christmas carol": ("Charles Dickens", "published in 1843", "novella"),
    "oliver twist": ("Charles Dickens", "published in 1838", "novel"),
    "moby dick": ("Herman Melville", "published in 1851", "novel"),
    "the hobbit": ("J. R. R. Tolkien", "published in 1937", "book"),
    "lord of the rings": ("J. R. R. Tolkien", "published in three parts in 1954 and 1955",
                          "book"),
    "harry potter": ("J. K. Rowling", "the first one came out in 1997", "book"),
    "to kill a mockingbird": ("Harper Lee", "published in 1960", "novel"),
    "the great gatsby": ("F. Scott Fitzgerald", "published in 1925", "novel"),
    "of mice and men": ("John Steinbeck", "published in 1937", "novella"),
    "the catcher in the rye": ("J. D. Salinger", "published in 1951", "novel"),
    "war and peace": ("Leo Tolstoy", "published in 1869", "novel"),
    "crime and punishment": ("Fyodor Dostoevsky", "published in 1866", "novel"),
    "frankenstein": ("Mary Shelley", "published in 1818, when she was 20", "novel"),
    "dracula": ("Bram Stoker", "published in 1897", "novel"),
    "the handmaids tale": ("Margaret Atwood", "published in 1985", "novel"),
    "brave new world": ("Aldous Huxley", "published in 1932", "novel"),
    "dune": ("Frank Herbert", "published in 1965", "novel"),
    "the hitchhikers guide to the galaxy": ("Douglas Adams", "it began as a radio series in 1978",
                                           "book"),
    "sherlock holmes": ("Arthur Conan Doyle", "the first story came out in 1887", "character"),
    "the diary of a young girl": ("Anne Frank", "written in hiding in Amsterdam, 1942 to 1944",
                                  "diary"),
    "the very hungry caterpillar": ("Eric Carle", "published in 1969", "picture book"),
    "the gruffalo": ("Julia Donaldson", "published in 1999, with pictures by Axel Scheffler",
                     "picture book"),
    "matilda": ("Roald Dahl", "published in 1988", "children's book"),
    "charlie and the chocolate factory": ("Roald Dahl", "published in 1964", "children's book"),
    "the lion the witch and the wardrobe": ("C. S. Lewis", "published in 1950", "book"),
    # plays and poems
    "hamlet": ("William Shakespeare", "written around 1600", "play"),
    "macbeth": ("William Shakespeare", "written around 1606", "play"),
    "romeo and juliet": ("William Shakespeare", "written in the 1590s", "play"),
    "king lear": ("William Shakespeare", "written around 1605", "play"),
    "a midsummer nights dream": ("William Shakespeare", "written in the 1590s", "play"),
    "the raven": ("Edgar Allan Poe", "published in 1845", "poem"),
    # paintings
    "mona lisa": ("Leonardo da Vinci", "painted around 1503 to 1519, and it hangs in the Louvre",
                  "painting"),
    "the last supper": ("Leonardo da Vinci", "painted in the 1490s in Milan", "painting"),
    "starry night": ("Vincent van Gogh", "painted in 1889 from the window of an asylum",
                     "painting"),
    "sunflowers": ("Vincent van Gogh", "painted in Arles in 1888", "painting"),
    "the scream": ("Edvard Munch", "painted in 1893", "painting"),
    "girl with a pearl earring": ("Johannes Vermeer", "painted around 1665", "painting"),
    "the birth of venus": ("Sandro Botticelli", "painted in the 1480s", "painting"),
    "guernica": ("Pablo Picasso", "painted in 1937 after the bombing of the town", "painting"),
    "the night watch": ("Rembrandt", "finished in 1642", "painting"),
    # music
    "ninth symphony": ("Ludwig van Beethoven", "first performed in 1824, when he was deaf",
                       "symphony"),
    "moonlight sonata": ("Ludwig van Beethoven", "written in 1801", "sonata"),
    "the four seasons": ("Antonio Vivaldi", "written around 1725", "set of concertos"),
    "bohemian rhapsody": ("Queen", "released in 1975, written by Freddie Mercury", "song"),
    "hey jude": ("the Beatles", "written by Paul McCartney and credited to Lennon and McCartney",
                 "song"),
    "the magic flute": ("Wolfgang Amadeus Mozart", "first performed in 1791", "opera"),
    # films
    "jurassic park": ("Steven Spielberg", "released in 1993", "film"),
    "the godfather": ("Francis Ford Coppola", "released in 1972", "film"),
    "titanic": ("James Cameron", "released in 1997", "film"),
    "jaws": ("Steven Spielberg", "released in 1975", "film"),
    "e.t.": ("Steven Spielberg", "released in 1982", "film"),
    "schindlers list": ("Steven Spielberg", "released in 1993, in black and white", "film"),
    "pulp fiction": ("Quentin Tarantino", "released in 1994", "film"),
    "the shawshank redemption": ("Frank Darabont", "released in 1994", "film"),
    "star wars": ("George Lucas", "the first one came out in 1977", "film"),
    "the wizard of oz": ("Victor Fleming", "released in 1939", "film"),
    "casablanca": ("Michael Curtiz", "released in 1942", "film"),
    "psycho": ("Alfred Hitchcock", "released in 1960", "film"),
    "gone with the wind": ("Victor Fleming", "released in 1939", "film"),
    "the sound of music": ("Robert Wise", "released in 1965", "film"),
    "mary poppins": ("Robert Stevenson", "released in 1964", "film"),
    "toy story": ("John Lasseter", "released in 1995, the first fully computer-animated "
                  "feature", "film"),
    "finding nemo": ("Andrew Stanton", "released in 2003", "film"),
    "frozen": ("Chris Buck and Jennifer Lee", "released in 2013", "film"),
    "the lion king": ("Roger Allers and Rob Minkoff", "released in 1994", "film"),
    "paddington": ("Paul King", "released in 2014", "film"),
    "the dark knight": ("Christopher Nolan", "released in 2008", "film"),
    "inception": ("Christopher Nolan", "released in 2010", "film"),
    "avatar": ("James Cameron", "released in 2009", "film"),
    "back to the future": ("Robert Zemeckis", "released in 1985", "film"),
    # more books people are set at school
    "lord of the flies": ("William Golding", "published in 1954", "novel"),
    "an inspector calls": ("J. B. Priestley", "first staged in 1945, in Moscow", "play"),
    "the old man and the sea": ("Ernest Hemingway", "published in 1952", "novella"),
    "a view from the bridge": ("Arthur Miller", "first staged in 1955", "play"),
    "the color purple": ("Alice Walker", "published in 1982", "novel"),
    "things fall apart": ("Chinua Achebe", "published in 1958", "novel"),
    # more paintings and songs
    "the persistence of memory": ("Salvador Dali", "painted in 1931", "painting"),
    "the kiss": ("Gustav Klimt", "painted in 1907 and 1908", "painting"),
    "imagine": ("John Lennon", "released in 1971", "song"),
    "wonderwall": ("Oasis", "released in 1995, written by Noel Gallagher", "song"),
    "smells like teen spirit": ("Nirvana", "released in 1991, written by Kurt Cobain",
                               "song"),
    "like a rolling stone": ("Bob Dylan", "released in 1965", "song"),
}

# The words that make a line the who-made-it question. Kept narrow: "who wrote to the
# council" is a letter, so the line also has to name something in the table.
# "band" stays out of this tuple: it is in the first part of the key, and as a maker word it
# would make "what should i name my band" a question about a song.
WHO_MAKERS = ("wrote", "written", "author", "painted", "composed", "composer", "sculpted",
              "made", "directed", "director", "sang", "sung", "singer", "by")


# --- is it worth watching -------------------------------------------------------------
# "is it worth watching the wire" asks for a view on one named work, and nobody's taste but
# this bot's is asked for, so the answer is one line of opinion plus what makes it worth the
# time. One row per work means a new title is data, not a new entry. Only titles that are
# unlikely to be anything else are here: a common word (frozen, friends, lost) would let
# "is frozen food any good" read as a question about a film.
VIEWS = {
    "the wire": ("*The Wire* is worth it, and the slow start is the point - give it four or "
                 "five episodes. Five series, a whole city in it, and it does not go soft at "
                 "the end."),
    "breaking bad": ("Yes. Short episodes, five series, and it gets darker every year without "
                     "losing the plot; Bryan Cranston is the reason it works."),
    "better call saul": ("Slower than *Breaking Bad* on purpose, and worth the patience if you "
                         "liked that one: it is a long, careful fall and it sticks the ending."),
    "the sopranos": ("Yes - the drama that started the run of great telly. Six series, and a "
                     "last scene people are still arguing about."),
    "succession": ("Yes: four series of a family at each other's throats, and much funnier "
                   "than it sounds. If you liked *The Thick of It*, start tonight."),
    "fleabag": ("An easy yes, and it takes about one evening: two series of six short "
                "episodes, funny first and then quietly devastating."),
    "happy valley": ("Three series and Sarah Lancashire is extraordinary in it; the third is "
                     "the best of them."),
    "line of duty": ("Six series of interviews and bent coppers - start at the first one, "
                     "because the story builds rather than resets."),
    "peaky blinders": ("Six series, very stylish, and a bit of a slog in the middle; Cillian "
                       "Murphy is the reason to watch it."),
    "chernobyl": ("Five episodes and the best short drama about a disaster ever made. Worth "
                  "one evening even if you think you know the story."),
    "the bear": ("Yes, and the episodes are about half an hour: loud, stressful, and really "
                 "about a family, with a sandwich shop round it."),
    "ted lasso": ("Warm and funny, and the first series is the best of the three - if you want "
                  "something kind on a wet evening, this is it."),
    "schitts creek": ("Worth it, but start knowing the first series is the weakest: it finds "
                      "its feet in the second and the last one is a joy."),
    "derry girls": ("Three short series and properly funny; the last one has the Good Friday "
                    "Agreement underneath it and still makes you laugh."),
    "game of thrones": ("Worth it, with a warning: most people hate the last series. The first "
                        "six are as good as television gets."),
    "the crown": ("Six series, each with a new cast, and the first two with Claire Foy are the "
                  "best; watch those and decide whether to go on."),
    "stranger things": ("The first series is the one - 80s, kids on bikes, a monster. It gets "
                        "bigger and sillier after that, so treat the later ones as a bonus."),
    "sherlock": ("Four short series of 90-minute episodes, and the first two are the good ones; "
                 "start with 'A Study in Pink'."),
    "black mirror": ("It is an anthology, so pick the standouts first - 'San Junipero' and "
                     "'USS Callister' - and skip around rather than in order."),
    "killing eve": ("The first series is brilliant; it gets weaker after that, but Jodie Comer "
                    "is worth staying for."),
    "mad men": ("Seven series in a 1960s ad agency: slow, stylish and really about people lying "
                "to themselves. Give it three episodes."),
    "downton abbey": ("Six series of a country house upstairs and down; gentle, easy and very "
                      "watchable if you want something undemanding."),
    "only murders in the building": ("Yes - a funny whodunnit with two older men and a young "
                                     "woman, three series of short episodes."),
    "the traitors": ("Genuinely gripping for a reality show; the UK version is the one to start "
                     "with and the round tables are the best part."),
    "doctor who": ("Start with the 2005 revival rather than the old ones: each episode stands "
                   "alone, and the first series with Christopher Eccleston is a good way in."),
    "pride and prejudice": ("Worth reading, and funnier than school makes it sound - give it "
                            "three chapters and you will know whether you get on with it."),
    "1984": ("Yes, and it is shorter and bleaker than most people expect; the middle is a long "
             "essay about power and the story around it is what stays."),
    "to kill a mockingbird": ("Worth it: a child's-eye view of a court case, and the first half "
                              "is slow on purpose - it is setting up what you will care about."),
    "dune": ("Worth it either way: the film tells the story cleanly and you do not need the book "
             "first. The book is denser and better on the politics, and both start slowly."),
    "the office": ("Yes, and start with the UK one - twelve episodes and then it is over, so it "
                   "costs you an evening to find out. The US one is gentler and much longer."),
    "oppenheimer": ("Worth it in a cinema if you can, because the sound is half of it; three "
                    "hours of men in rooms that somehow never drags."),
    "the godfather": ("Yes, and it holds up: the first two are the ones. Part three is the one "
                      "people argue about, so leave it until you care."),
    "lord of the rings": ("The fellowship one is the place to start, and the extended cut is "
                          "worth it once you know you like it - three hours a film, so give it "
                          "a free evening."),
    "harry potter": ("Worth it, and the books hold up better than the films for a reader past "
                     "ten; the third book is where it gets properly good."),
    "gone girl": ("Worth it: a thriller that turns halfway and takes you with it. The film is "
                  "faithful, so pick either one and skip the other."),
    # The films and series people ask about by name that had no view at all: "is my neighbour
    # totoro worth watching" was a hedge while forty other titles had an answer. One row per
    # work, so a new title is data.
    "my neighbour totoro": ("Worth it at any age: gentle, almost nothing goes wrong, and it is "
                            "the film for a rainy afternoon or after a bad week. 86 minutes, and "
                            "no baddie to speak of."),
    "spirited away": ("Yes - the best way into Studio Ghibli and the one that wins over people "
                      "who say they do not like animation. Subtitled if you can; the English "
                      "voices are good too."),
    "parasite": ("Yes, and go in knowing nothing: it turns about halfway and the less you know "
                 "the better. Subtitles, two hours, and it never feels long."),
    "paddington 2": ("The rare sequel better than the first: warm, funny, and Hugh Grant having "
                     "the time of his life. The safest film there is for a mixed-age evening."),
    "everything everywhere all at once": ("Worth it if you have the energy for it: two hours "
                                          "twenty of noise, jokes and feeling, and the last "
                                          "twenty minutes earn all of it. Have tissues."),    "squid game": ("Yes - the first series is the one to start with: one game an episode, and "
                   "the tension is in the rules rather than the blood. The later series are "
                   "slower, so only go on if you liked the first."),
    "the last of us": ("Worth it even if you never played the game: nine episodes, and the third "
                       "one is a whole love story with almost nobody else in it. Bleak, so not a "
                       "background watch."),
    "shogun": ("Yes - a stranger in a strange court, and it is about power and translation more "
               "than battles. Partly subtitled, and better for it."),
    "slow horses": ("Yes: Gary Oldman as a filthy, brilliant spymaster, six short series, and it "
                    "gets funnier as it gets darker. Start at the first."),
    "severance": ("Worth it: office workers whose memories are split between work and home, and "
                  "the slowest drip of information you will be glad of. Short episodes, and pay "
                  "attention."),
    "the boys": ("Yes if you like your superheroes filthy and angry - it is a satire with a lot "
                 "of gore. If you want charm, this is not it."),
    "money heist": ("Worth it for the first two parts, which are one long heist with a hostage "
                    "negotiator; the later parts stretch a good idea a long way. Try the "
                    "original audio rather than the dub."),
    "bridgerton": ("Yes if you want gorgeous, silly, warm romance: each series is one couple and "
                   "a lot of string-quartet pop. It is not trying to be serious."),
    "the witcher": ("The first series is confusing on purpose and settles by the second; watch "
                    "it for the monster-of-the-week episodes and Henry Cavill's growl."),
    "gilmore girls": ("Worth it: seven series of very fast talking, a small town, and a mother "
                      "and daughter who are friends. Comfort television rather than plot."),
    "sex education": ("Yes - four series, funny and kind, about a teenager running an advice "
                      "clinic at school, with Gillian Anderson as his mother."),
    "normal people": ("Worth it: two people circling each other over twelve short episodes, and "
                      "the most honest silences on television. Bleak in a quiet way."),
    "bluey": ("Yes, and not only for the children: seven-minute episodes about a family of dogs "
              "that are funnier and sadder than they need to be, and a parent gets more out of "
              "it than the child."),
    "avatar the last airbender": ("Worth it: three series of a cartoon that is really a war "
                                  "story with a twelve-year-old in the middle, and it earns its "
                                  "ending. Start at episode one, not the film."),
    "the matrix": ("Yes, and it holds up: the first film is the one, and the effects still work "
                   "because they serve the story. The sequels are for people who want more of "
                   "the world."),
    "inception": ("Worth it: a heist inside dreams, and it explains its own rules as it goes. "
                  "Watch it without your phone and the ending lands."),
    "interstellar": ("Yes, on the biggest screen you can: a father-and-daughter story with a "
                     "black hole in the middle, and the sound is half of it. The middle act is "
                     "slow."),
    "everything everywhere all at once": ("Yes, and give it twenty minutes: it is silly and fast "
                                          "and then it is about a mother and a daughter and you "
                                          "are crying. The middle is a lot of noise."),
    "barbie": ("Worth it: funny and strange and about more than the doll, and Ryan Gosling steals "
               "it. Two hours, and it knows exactly what it is doing."),
    "wonka": ("Worth it for a family evening: warm, colourful, songs you half know, and "
              "Chalamet is charming. Nobody needed it, but it is a good time."),
    "the holdovers": ("Yes - a grumpy teacher, a stranded student and a cook at a boarding school "
                      "over Christmas. Small, funny, and it earns its ending."),
    "past lives": ("Worth it: two childhood friends in different countries and twenty years of "
                   "what-ifs. Quiet, short, and it does not go where you expect."),
    "where the crawdads sing": ("Worth it if you want a slow, sad mystery about a girl raising "
                                "herself in a marsh. The book is better and the film is "
                                "faithful to it."),
    "the midnight library": ("Worth it: a woman between life and death tries the lives she did "
                             "not live. Gentle, quick, and the ending is the argument."),
    "lessons in chemistry": ("Yes - a chemist in the 1960s turns a cooking show into a lecture, "
                             "and it is funny and angry at once. A dog narrates a chapter."),
    "the seven husbands of evelyn hugo": ("Worth it: an old film star tells her life story to a "
                                          "reporter, and it is a soap opera in the best sense."),
    "tomorrow and tomorrow and tomorrow": ("Yes - two friends making video games over thirty "
                                           "years, and it is really about work, and love, and "
                                           "the friend you do not marry."),
    "a little life": ("Worth it, but be warned: it is long, it is about damage, and it is "
                      "relentless. Read it when you have a fortnight and somebody to talk to "
                      "about it."),
    "klara and the sun": ("Worth it: an artificial friend watches a family and misunderstands "
                          "beautifully. Quiet, and the ending stays with you."),
    "the song of achilles": ("Yes - the Iliad told by Patroclus, and it is a love story first and "
                             "a war epic second. Have the tissues ready."),
    "circe": ("Worth it: the witch of the Odyssey tells her own story, and it is about power and "
              "exile. Slow to start, then it grips."),
    "piranesi": ("Worth it, and go in knowing nothing: a man lives in an infinite house of "
                 "statues. Short, strange, and the reveal is the reward."),
    "project hail mary": ("Yes - a man wakes alone on a spaceship and has to science his way out, "
                          "with one very funny alien. Best read cold."),
    "the martian": ("Worth it: one man, one planet, and a lot of problem-solving, and the most "
                    "cheerful survival story there is."),
    "sapiens": ("Worth it as an argument rather than a history: bracing and readable, and "
                "confidently wrong in places, so read it with a pinch of salt."),

}

# The ask that wants a view on a named work. Kept to phrases with a judgement in them, so a
# report ("i watched the wire last night") never reaches the table.
JUDGE_ASKS = ("worth watching", "worth a watch", "worth reading", "worth a read",
              "worth playing", "worth seeing", "any good", "is it good", "is it any good",
              "should i watch", "should i read", "should i start", "is it worth")

# The words that make a line an ask for a view. They are the second key part, so a work in the
# table plus one of these is the entry's line, and a work named with no judgement at all ("i
# watched the wire last night") is not.
JUDGE_WORDS = ("good", "worth", "worthwhile", "like", "boring", "rubbish", "any", "better",
               "watch", "watching", "read", "reading", "see", "start", "best", "should")

# A named work can be an ordinary phrase: "the office" is a workplace in "should i go back to
# the office tomorrow", and a modal like "should" was enough to make that a verdict on the
# series. So the words that ask for a view are named here without the bare modals and the
# loose comparatives, and the two halves of a request are written as phrases instead.
VERDICT_ASKS = ("worth", "worthwhile", "good", "any good", "any cop", "like", "boring",
                "rubbish", "bother", "should i watch", "should i read", "should i start",
                "should i see", "shall i watch", "shall i read", "is it any good",
                "is it good", "worth watching", "worth reading", "worth a watch",
                "worth a read")

# One work in the table shares its name with a place people go every day: *The Office* is a
# series, and "the office" is where someone works. The place is the commoner subject by a long
# way, and a verdict on the series is no help at all to it: "i kind of like the office but the
# commute is 90 minutes each way" was told to start with the UK one, twelve episodes and then it
# is over. A workplace detail in the line means the place, so neither verdict entry may answer -
# the judgement "like" is about the job, not about a programme.
A_PLACE_NOT_A_WORK = ("commute", "commuting", "each way", "into the office", "to the office",
                      "in the office", "at the office", "from the office", "office days",
                      "days a week", "my desk", "work from home", "working from home", "hybrid",
                      "my boss", "canteen", "open plan")

# "the office is" on its own is too wide a phrase for the list above: "the office is on netflix,
# is it good" is the series, and it is exactly the line a person writes. What makes the place is
# how the place is ("the office is freezing") or how far it is ("the office is 40 minutes away"),
# so the sentence has to carry one of those.
_THE_OFFICE_IS = re.compile(
    r"the office (?:is|was|'s)\s+(?:(?:so|too|really|quite|very|only|about|just|always)\s+)?"
    r"(?:\d+\s*(?:minute|min|hour)|cold|freezing|boiling|hot|stuffy|noisy|loud|quiet|far|"
    r"near|closer|close|empty|dead|busy|full|open plan|tiny|huge|big|grim|depressing|miserable)")

# A medium with no mood in the line ("i want a film", "im in the mood for a book", "give me a
# podcast") is a request for that medium's picks, and the pick rows for each medium read these
# words, so one list answers every medium.
WANT_ASKS = ("want", "wanted", "fancy", "fancied", "feel like", "in the mood", "mood for",
             "need", "would love", "id love", "i'd love", "looking for", "after a", "give me",
             "craving")
# The words that make a line a request for a thing rather than a report about one, so "that was
# funny" is not a want of something funny. They carry no medium, so the medium comes from the
# chat (see `_the_medium`).
ANY_MOOD_ASKS = ("something", "anything", "some", "in the mood", "fancy", "want", "wanted",
                 "need", "recommend", "suggest", "ideas", "any", "give me", "what should i",
                 "looking for", "feel like", "would love", "id love", "i'd love",
                 "put me in the mood", "mood for", "shorter", "quicker")
# A mood word in a line that names a medium is that medium's row; one in a line about a joke,
# a piece of news, a present or somebody's own feeling belongs to another table.
NOT_A_MOOD_PICK = (
    "film", "films", "movie", "movies", "cinema", "watch", "watching", "watched",
    "tv", "telly", "series", "show", "shows", "boxset", "box set", "binge", "episode",
    "episodes", "netflix", "iplayer", "streaming", "book", "books", "novel", "novels",
    "read", "reading", "audiobook", "audiobooks", "podcast", "podcasts", "album", "albums",
    "song", "songs", "playlist", "game", "games", "board game",
    # "say something funny" and "tell me something funny" want a joke, and a story that
    # happened to somebody is news
    "say", "tell me", "joke", "jokes", "story", "stories", "happened", "happens",
    "happening", "at work",
    # "i need a hand with moving house" has the mood word "need" and the ask word, and a hand is
    # not a mood: it got "What kind of hand do you usually go for?"
    "hand", "hands", "a hand with", "lend a hand", "give me a hand", "help me with",
    # a present, or a person it is for, is the gift rows' ask
    "present", "gift", "birthday", "anniversary", "christmas", "valentine", "for my wife",
    "for my husband", "for my partner", "for my mum", "for my dad",
    # somebody's own state is not a request for something to watch
    "im feeling", "i am feeling", "feel sad", "feel down", "feel low", "feeling sad",
    "feeling down", "feeling low", "scared", "frightened", "terrified", "worried",
    "to be happy", "be happy", "depressed", "anxious",
    # a journey is a stretch of time with the children in it, not a mood: "any tips for a long
    # car journey with small kids" carried "any" and "long", so the pick-anything row handed
    # four tired parents a film. A journey, a flight and a drive have their own answers.
    "journey", "long journey", "long drive", "car journey", "car ride", "road trip",
    "motorway", "on the motorway", "flight", "flights", "plane", "ferry",
    "train journey", "on the train",
    # A piece of news is somebody's life, not a mood to be met with a watchlist. "i have some sad
    # news" carries "some" - an ask word - and "sad", a mood word, and it was answered with
    # *Manchester by the Sea* and *Never Let Me Go*: the cruellest reply in the bot, because it
    # treats a bereavement as a browsing filter. The news words are fenced, not the ask word
    # tightened, because "some"/"any" in front of news is the shape that carries a life into the
    # line. The bare "news" is fenced too: "i have news" is the same shape with the feeling kept
    # for the person to say, and a film list guesses what it was.
    "news", "sad news", "bad news", "no news", "the news", "heard the news", "some news",
    "any news", "news about", "news that", "good news",
    "passed away", "passed on", "died", "death", "funeral", "burial", "cremation",
    "bereaved", "bereavement", "grief", "grieving", "mourning", "widow", "widowed",
    "diagnosed", "diagnosis", "hospice", "in hospital", "terminally", "miscarriage",
    "stillborn", "broke up", "broken up", "split up", "divorce", "divorced",
    "lost my job", "redundant", "made redundant", "evicted",
)
# A pick of anything ("whats a good film", "any good films on netflix") names no work at all, so
# it is not a verdict on one: the entry stays out of scoring for it, and the entries that make a
# pick answer. Also here are the asks for the best of a kind, which pick one for you.
# Named here without the bare plurals ("films", "books"): a plural is a loose form of the
# singular, so "is dune a good book" would be thrown out with "any good books for a 10 year old".
PICK_ASKS = ("a film", "a movie", "a book", "a series", "a show", "a podcast",
             "a documentary", "best film", "best movie", "best series", "best show",
             "to watch", "to read", "anything", "something", "recommend", "suggest",
             "what should", "whats on", "netflix", "iplayer", "prime video", "disney",
             "streaming", "on telly")

# The asks the second entry answers with no work named: each one carries watching or reading
# in it. "is it worth" on its own is left out, because that is how people ask about a laptop
# repair and a hundred other things.
UNNAMED_ASKS = ("worth watching", "worth a watch", "worth reading", "worth a read",
                "worth playing", "worth seeing", "should i watch", "should i read",
                "any good", "is it any good", "is it good")

# A question about whether a habit is good for you ("is reading good for you", "is it good to
# read before bed") is not a verdict on a work either, and the entries that know about screen
# time, sleep and reading answer it.
HABIT_ASKS = ("for you", "for me", "for kids", "for a child", "healthy", "unhealthy",
              "bad for", "good for", "before bed", "help me", "improve", "screen time",
              "too much")
# The plurals are for the reply alone: as avoid words they are loose forms of the singular, so
# "is dune a good book" would be turned away with "any good books for a 10 year old".
NOT_A_VERDICT = HABIT_ASKS + ("films", "movies", "books", "shows", "podcasts", "documentaries")

# A line that reports on something already seen or read wants to talk about it, not to be told
# whether to start it.
SEEN_ALREADY = re.compile(r"\b(?:i|we|he|she|they)\s+(?:have\s+|had\s+|just\s+|finally\s+|"
                          r"already\s+)?(?:watched|saw|seen|read|finished|binged)\b")
# "should i read normal people" is a question that says "i read" in the middle of it, so the
# report is only a report when the line is not asking.
# A work is not one question for every age: "is harry potter good for a 7 year old" is about the
# child, and the children's book entries know what suits which age.
AGE_ASK = re.compile(r"\b\d+ ?(?:year|yr)s?[ -]?old\b|\b(?:toddler|baby|teenager|teen)\b")

ASKING_FIRST = re.compile(r"\b(?:should|shall|can|could|would|do|does|did|might|may|any|worth|"
                          r"good|what|which)\b")

_SMALL = {"and", "the", "of", "a", "an", "in", "on", "to", "for", "with"}


def _title(work):
    """The work the way it is written on a shelf: Mona Lisa, Pride and Prejudice, 1984."""
    words = work.split()
    if words and words[0].isdigit():
        return work
    return " ".join(word if (i and word in _SMALL) else word[:1].upper() + word[1:]
                    for i, word in enumerate(words))


def who_made(memory, understood):
    """The maker of the work the line names, or None so another entry can answer."""
    clean = (understood or {}).get("clean") or (understood or {}).get("text") or ""
    clean = clean.lower().replace("'", "").replace("\u2019", "")
    best = None
    for work in WORKS:
        if re.search(r"\b" + re.escape(work) + r"\b", clean):
            if best is None or len(work) > len(best):
                best = work
    if best is None:
        return None
    maker, detail, kind = WORKS[best]
    name = _title(best)
    article = "an" if kind[:1] in "aeiou" else "a"
    return (f"{name} is {article} {kind} by {maker}, {detail}.")


# Who wrote it, keyed by the title: one table answers "who wrote pride and prejudice", "who
# is the author of 1984", "did jane austen write emma" and "what else did jane austen write",
# because every answer is a lookup in the same rows. The author's surname is the key for the
# person, so "rowling" and "austen" are found however the rest of the name is typed.
BOOK_AUTHORS = (
    ("pride and prejudice", "Jane Austen"),
    ("sense and sensibility", "Jane Austen"),
    ("emma", "Jane Austen"),
    ("persuasion", "Jane Austen"),
    ("mansfield park", "Jane Austen"),
    ("northanger abbey", "Jane Austen"),
    ("oliver twist", "Charles Dickens"),
    ("great expectations", "Charles Dickens"),
    ("a christmas carol", "Charles Dickens"),
    ("david copperfield", "Charles Dickens"),
    ("a tale of two cities", "Charles Dickens"),
    ("bleak house", "Charles Dickens"),
    ("1984", "George Orwell"),
    ("animal farm", "George Orwell"),
    ("down and out in paris and london", "George Orwell"),
    ("to kill a mockingbird", "Harper Lee"),
    ("jane eyre", "Charlotte Bronte"),
    ("wuthering heights", "Emily Bronte"),
    ("the great gatsby", "F. Scott Fitzgerald"),
    ("moby dick", "Herman Melville"),
    ("frankenstein", "Mary Shelley"),
    ("dracula", "Bram Stoker"),
    ("little women", "Louisa May Alcott"),
    ("the hobbit", "J.R.R. Tolkien"),
    ("the lord of the rings", "J.R.R. Tolkien"),
    ("the fellowship of the ring", "J.R.R. Tolkien"),
    ("harry potter and the philosopher's stone", "J.K. Rowling"),
    ("harry potter", "J.K. Rowling"),
    ("a game of thrones", "George R.R. Martin"),
    ("the hunger games", "Suzanne Collins"),
    ("the shining", "Stephen King"),
    ("misery", "Stephen King"),
    ("carrie", "Stephen King"),
    ("murder on the orient express", "Agatha Christie"),
    ("and then there were none", "Agatha Christie"),
    ("the murder of roger ackroyd", "Agatha Christie"),
    ("the hound of the baskervilles", "Arthur Conan Doyle"),
    ("sherlock holmes", "Arthur Conan Doyle"),
    ("the adventures of tom sawyer", "Mark Twain"),
    ("adventures of huckleberry finn", "Mark Twain"),
    ("of mice and men", "John Steinbeck"),
    ("the grapes of wrath", "John Steinbeck"),
    ("lord of the flies", "William Golding"),
    ("brave new world", "Aldous Huxley"),
    ("fahrenheit 451", "Ray Bradbury"),
    ("the handmaid's tale", "Margaret Atwood"),
    ("beloved", "Toni Morrison"),
    ("half of a yellow sun", "Chimamanda Ngozi Adichie"),
    ("americanah", "Chimamanda Ngozi Adichie"),
    ("the kite runner", "Khaled Hosseini"),
    ("life of pi", "Yann Martel"),
    ("the martian", "Andy Weir"),
    ("project hail mary", "Andy Weir"),
    ("normal people", "Sally Rooney"),
    ("eleanor oliphant is completely fine", "Gail Honeyman"),
    ("the midnight library", "Matt Haig"),
    ("where the crawdads sing", "Delia Owens"),
    ("the thursday murder club", "Richard Osman"),
    ("the secret history", "Donna Tartt"),
    ("the goldfinch", "Donna Tartt"),
    ("a little life", "Hanya Yanagihara"),
    ("the book thief", "Markus Zusak"),
    ("the alchemist", "Paulo Coelho"),
    ("one hundred years of solitude", "Gabriel Garcia Marquez"),
    ("the road", "Cormac McCarthy"),
    ("never let me go", "Kazuo Ishiguro"),
    ("the remains of the day", "Kazuo Ishiguro"),
    ("romeo and juliet", "William Shakespeare"),
    ("hamlet", "William Shakespeare"),
    ("macbeth", "William Shakespeare"),
    ("king lear", "William Shakespeare"),
    ("othello", "William Shakespeare"),
    ("a midsummer night's dream", "William Shakespeare"),
    ("julius caesar", "William Shakespeare"),
    ("the tempest", "William Shakespeare"),
    ("twelfth night", "William Shakespeare"),
    ("the odyssey", "Homer"),
    ("the iliad", "Homer"),
    ("the canterbury tales", "Geoffrey Chaucer"),
    ("paradise lost", "John Milton"),
    ("sapiens", "Yuval Noah Harari"),
    ("becoming", "Michelle Obama"),
    ("the diary of a young girl", "Anne Frank"),
    ("the bell jar", "Sylvia Plath"),
    ("mrs dalloway", "Virginia Woolf"),
    ("to the lighthouse", "Virginia Woolf"),
    ("the picture of dorian gray", "Oscar Wilde"),
    ("the importance of being earnest", "Oscar Wilde"),
    ("treasure island", "Robert Louis Stevenson"),
    ("dr jekyll and mr hyde", "Robert Louis Stevenson"),
    ("alice in wonderland", "Lewis Carroll"),
    ("alice's adventures in wonderland", "Lewis Carroll"),
    ("through the looking glass", "Lewis Carroll"),
    ("the wizard of oz", "L. Frank Baum"),
    ("the secret garden", "Frances Hodgson Burnett"),
    ("charlie and the chocolate factory", "Roald Dahl"),
    ("matilda", "Roald Dahl"),
    ("the bfg", "Roald Dahl"),
    ("james and the giant peach", "Roald Dahl"),
    ("the witches", "Roald Dahl"),
    ("gangsta granny", "David Walliams"),
    ("the gruffalo", "Julia Donaldson"),
    ("the very hungry caterpillar", "Eric Carle"),
    ("the tale of peter rabbit", "Beatrix Potter"),
    ("war horse", "Michael Morpurgo"),
    ("the lion the witch and the wardrobe", "C.S. Lewis"),
    ("northern lights", "Philip Pullman"),
    ("percy jackson", "Rick Riordan"),
    ("diary of a wimpy kid", "Jeff Kinney"),
    ("a brief history of time", "Stephen Hawking"),
    ("the catcher in the rye", "J.D. Salinger"),
    ("the old man and the sea", "Ernest Hemingway"),
    ("anna karenina", "Leo Tolstoy"),
    ("crime and punishment", "Fyodor Dostoevsky"),
    ("the count of monte cristo", "Alexandre Dumas"),
    ("les miserables", "Victor Hugo"),
    ("don quixote", "Miguel de Cervantes"),
    ("middlemarch", "George Eliot"),
    ("things fall apart", "Chinua Achebe"),
    # The Color Purple is Alice Walker, and the table said Toni Morrison here while the table
    # said Alice Walker for the colour spelling further up: one title, two authors, and the
    # lookup read the wrong one ("who wrote the color purple" answered Morrison).
    ("the colour purple", "Alice Walker"),
    ("gone girl", "Gillian Flynn"),
    ("the girl on the train", "Paula Hawkins"),
    ("the silent patient", "Alex Michaelides"),
    ("lessons in chemistry", "Bonnie Garmus"),
    ("klara and the sun", "Kazuo Ishiguro"),
    ("a thousand splendid suns", "Khaled Hosseini"),
    ("the seven husbands of evelyn hugo", "Taylor Jenkins Reid"),
    ("the little prince", "Antoine de Saint-Exupery"),
    ("the selfish gene", "Richard Dawkins"),
    ("the origin of species", "Charles Darwin"),
    ("a short history of nearly everything", "Bill Bryson"),
)

# The same title written another way: folded before the lookup, so one row answers both.
TITLE_SPELLING = {"the color purple": "the colour purple"}

# A person can be named by surname alone, and the surnames of the table are the words that
# make a line about authorship on their own: "did jane austen write emma" has no "who" in it.
AUTHOR_KEYS = tuple(dict.fromkeys(writer.split()[-1].lower()
                                  for _title, writer in BOOK_AUTHORS))
AUTHOR_ALSO = {"doyle": "conan doyle", "rowling": "jk rowling", "martin": "george rr martin",
               "fitzgerald": "scott fitzgerald", "lewis": "cs lewis"}

# The words a line uses to ask who wrote something or what else an author wrote.
ASKED_WROTE = ("write", "wrote", "written", "writes", "writing", "author", "authors",
               "book", "books", "novel", "novels", "play", "plays", "poem", "poems",
               "story", "stories", "else", "other", "also", "more", "by")


def _author_key(author):
    """The word a person is known by: the surname, without the initials."""
    return author.split()[-1].lower()


def _titles_of(author):
    return [title for title, writer in BOOK_AUTHORS if writer == author]


def _title_in(clean):
    """The longest title the line names, with its author: (title, author) or None."""
    best = None
    for title, author in BOOK_AUTHORS:
        if re.search(r"(?<![a-z0-9])" + re.escape(title) + r"(?![a-z0-9])", clean):
            if best is None or len(title) > len(best[0]):
                best = (title, author)
    return best


def _author_in(clean, title=None):
    """The author the line names, by surname or by the surname people say with it.

    A surname inside the title does not name anyone: "who wrote harry potter" names a
    book, not Beatrix Potter.
    """
    for author in dict.fromkeys(writer for _title, writer in BOOK_AUTHORS):
        key = _author_key(author)
        words = [key]
        also = AUTHOR_ALSO.get(key)
        if also:
            words.append(also)
        for word in words:
            if title and word in title:
                continue
            if re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", clean):
                return author
    return None


# A title that capitals alone would spoil.
TITLE_AS = {"the bfg": "The BFG", "dr jekyll and mr hyde": "Dr Jekyll and Mr Hyde",
            "1984": "1984", "jk rowling": "J.K. Rowling"}

# The small words a title keeps in lower case, and the one that starts it in capitals.
TITLE_SMALL = ("and", "of", "the", "a", "an", "in", "to", "on", "for", "at", "with")


def _display(text):
    """"pride and prejudice" as a title someone would write: Pride and Prejudice."""
    if text in TITLE_AS:
        return TITLE_AS[text]
    words = text.split()
    out = [words[0][:1].upper() + words[0][1:]]
    for word in words[1:]:
        out.append(word if word in TITLE_SMALL else word[:1].upper() + word[1:])
    return " ".join(out)


def _said(text):
    """"J.K. Rowling" without the full stops, which are read back as letters otherwise."""
    return text.replace(".", "")


def _list_words(items):
    items = list(items)
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _who_wrote(memory, understood):
    """Who wrote a book, whether a name is right, or what else an author wrote.

    Every answer is a lookup in BOOK_AUTHORS: a title names its author, an author names
    their titles, and a title with a wrong author is corrected. Without a title or an
    author in the table there is nothing to say, and the line falls through to the pick.
    """
    # "pride & prejudice" is the same book as "pride and prejudice", and the American spelling
    # of a title is the same book too; neither should stop the lookup or list the book twice.
    clean = (understood.get("clean") or "").replace(" & ", " and ")
    for spelling, standard in TITLE_SPELLING.items():
        clean = clean.replace(spelling, standard)
    found = _title_in(clean)
    named = _author_in(clean, found[0] if found else None)
    if found:
        title, author = found
        # A row that is only part of the title just read is not "another book": the answer to
        # "who wrote harry potter and the philosopher's stone" must not offer "Harry Potter".
        others = [t for t in _titles_of(author)
                  if t != title and title not in t and not t.startswith(title)
                  and not title.startswith(t)]
        rest = (f" Other books by {_said(author)}: "
                f"{_list_words(_display(t) for t in others[:3])}." if others else "")
        if named and named != author:
            return (f"Not quite - {_display(title)} is by {_said(author)}, not "
                    f"{_said(named)}.{rest}")
        if named:
            return f"Yes - {_display(title)} is by {_said(author)}.{rest}"
        return f"{_display(title)} is by {_said(author)}.{rest}"
    if not named:
        return None
    titles = _titles_of(named)
    if not titles:
        return None
    said = _list_words(_display(t) for t in titles[:5])
    more = "" if len(titles) <= 5 else ", among others"
    return f"{_said(named)} wrote {said}{more}."


# A book named by somebody who liked it wants the book that follows, and the titles people name
# are a small set that does not change much. One table answers every "a book like X", "i loved X,
# what next" and "something similar to X": the row is keyed on the title, so the wording of the
# ask never has to be listed, and a new title is one line.
BOOK_MATCHES = (
    ("normal people",
     "If you liked *Normal People*, *Conversations with Friends* is the same author on the same "
     "ground, and *Exciting Times* by Naoise Dolan has the same cool, sharp voice about love and "
     "money. For warmth too, *The Rachel Incident* by Caroline O'Donoghue."),
    ("the midnight library",
     "*The Humans* by the same author is the closest, and *A Man Called Ove* by Fredrik Backman "
     "has the same kind of kindness in it. *Eleanor Oliphant Is Completely Fine* if you want "
     "another odd person finding their way."),
    ("gone girl",
     "Try *The Silent Patient* by Alex Michaelides: short chapters, an unreliable narrator and a "
     "twist you won't see coming. *The Girl on the Train* by Paula Hawkins is the other obvious "
     "next step, and *Sharp Objects* is the same author as Gone Girl and nastier."),
    ("the thursday murder club",
     "The next one is *The Man Who Died Twice* by Richard Osman, the same four friends again. "
     "For a different author, *The Marlow Murder Club* by Robert Thorogood is close in tone, or "
     "*The Silent Patient* if you want a darker twist."),
    ("the martian",
     "Try *Project Hail Mary* by Andy Weir, the same author: one man solving one problem at a "
     "time, funnier than The Martian. For something bigger but just as engineering-minded, "
     "*Seveneves* by Neal Stephenson."),
    ("project hail mary",
     "*The Martian* is the same author and the same kind of puzzle-solving, and *Children of "
     "Time* by Adrian Tchaikovsky is the step up: bigger ideas, still easy to read."),
    ("harry potter",
     "*His Dark Materials* by Philip Pullman is the next step: magic, a child at the centre of "
     "it and better writing. *Percy Jackson* by Rick Riordan is easier and funnier, and *The "
     "Worst Witch* suits a younger reader."),
    ("klara and the sun",
     "*Never Let Me Go* is the same author on the same question, and quieter. *Machines Like Me* "
     "by Ian McEwan is the other one about a machine in a family."),
    ("never let me go",
     "*Klara and the Sun* and *The Remains of the Day* are the same author, and both are about "
     "somebody who only sees the truth too late. *The Road* by Cormac McCarthy if you want the "
     "same quiet grief."),
    ("the secret history",
     "*If We Were Villains* by M. L. Rio is the closest thing to it, and *The Likeness* by Tana "
     "French has the same closed group of clever friends. *The Goldfinch* is the same author and "
     "longer."),
    ("where the crawdads sing",
     "*The Great Alone* by Kristin Hannah has the same wild setting and the same lone girl, and "
     "*The Marsh King's Daughter* by Karen Dionne is the darker version."),
    ("eleanor oliphant is completely fine",
     "*A Man Called Ove* by Fredrik Backman is the same lonely person, warmer, and *The Rosie "
     "Project* by Graeme Simsion is funnier. Both are easy to read."),
    ("the song of achilles",
     "*Circe* is the same author and just as good, and *The Silence of the Girls* by Pat Barker "
     "tells the same war from the women's side."),
    ("the silent patient",
     "*The Girl on the Train* by Paula Hawkins and *The Guest List* by Lucy Foley both keep the "
     "twist hidden, and both are quick. *Gone Girl* if you want the coldest narrator of the lot."),
    ("a little life",
     "*Shuggie Bain* by Douglas Stuart is the same weight of sadness and just as well written, "
     "and *The Goldfinch* by Donna Tartt is the other long one people finish and then sit still."),
    ("the book thief",
     "*All the Light We Cannot See* by Anthony Doerr is the closest in feeling, and *The Boy in "
     "the Striped Pyjamas* is easier if it is for a younger reader."),
    ("lessons in chemistry",
     "*Remarkably Bright Creatures* by Shelby Van Pelt has the same warmth and a woman who "
     "carries on her own, and *Eleanor Oliphant Is Completely Fine* the same odd, funny voice."),
    ("the seven husbands of evelyn hugo",
     "*Daisy Jones and the Six* by Taylor Jenkins Reid is the same author and the same glamour "
     "with a dark edge, and *City of Girls* by Elizabeth Gilbert is the other long, warm life "
     "story."),
    ("conversations with friends",
     "*Normal People* is the same author and easier, and *Exciting Times* by Naoise Dolan has "
     "the same clever young people making a mess of it."),
    ("it ends with us",
     "*Me Before You* by Jojo Moyes is the one everyone else starts with, and *The Last Letter "
     "from Your Lover* is the same kind of love story with a hard centre."),
    ("the hunger games",
     "*Divergent* by Veronica Roth is the closest to it, and *The Giver* by Lois Lowry is "
     "shorter and stranger. For a grown-up version, *The Handmaid's Tale*."),
    ("the girl with the dragon tattoo",
     "*The Girl on the Train* moves faster, and *The Silence of the Lambs* is the colder one. "
     "*Sharp Objects* by Gillian Flynn if you want a family full of secrets."),
    ("the glass hotel",
     "*Station Eleven* is the same author and the better one to read first: the same quiet "
     "collapse and the same people holding on. *Cloud Atlas* by David Mitchell is the other "
     "one that moves between times like this."),
    ("station eleven",
     "*The Glass Hotel* is the same author, and *The Road* by Cormac McCarthy is the harsher, "
     "shorter version of the same world. *Severance* by Ling Ma is the funnier one."),
    ("verity",
     "The same kind of twist, done colder: *The Housemaid* by Freida McFadden, or *The Last "
     "Mrs Parrish* by Liv Constantine. *The Silent Patient* if you have not read it yet."),
    ("the housemaid",
     "*Verity* by Colleen Hoover is the closest and the fastest, and *The Last Mrs Parrish* by "
     "Liv Constantine has the same servant-in-the-house trick with more bite."),
    ("fourth wing",
     "*A Court of Thorns and Roses* by Sarah J. Maas is the same author-on-romance-and-war "
     "shape and the usual next step, and *Throne of Glass* is the same author, longer."),
    ("the da vinci code",
     "*Angels and Demons* is the same author and the same puzzle chase. For the real thing, "
     "*The Name of the Rose* by Umberto Eco is the same story with more history."),
    ("to kill a mockingbird",
     "*Of Mice and Men* is shorter and just as much about who gets a fair go, and *The Book "
     "Thief* is the other one about a child watching a town fail."),
    ("of mice and men",
     "*To Kill a Mockingbird* is the other short one about fairness, and *The Grapes of Wrath* "
     "is the same author and the same journey, much longer."),
    ("lord of the flies",
     "*The Hunger Games* does the same thing with a plot, and *The Graveyard Book* by Neil "
     "Gaiman suits a reader who wants it darker but shorter."),
    ("life of pi",
     "*The Old Man and the Sea* is the short one with the same sea and the same stubborn man, "
     "and *The Alchemist* is the other fable people read next."),
    ("the kite runner",
     "*A Thousand Splendid Suns* is the same author and better, and *And the Mountains Echoed* "
     "is the third one. *The Bookseller of Kabul* if you want the true version."),
    ("the alchemist",
     "*Life of Pi* has the same fable feel with a story that holds, and *Siddhartha* by Hermann "
     "Hesse is the short one behind it."),
    ("percy jackson",
     "*Magnus Chase* by Rick Riordan is the same author doing Norse myth, *Artemis Fowl* by "
     "Eoin Colfer is cleverer and funnier, and *Nevermoor* by Jessica Townsend is the safest "
     "pick for a younger reader."),
    ("the maze runner",
     "*The Hunger Games* by Suzanne Collins if you have not read it, *Divergent* by Veronica "
     "Roth next, and *Scythe* by Neal Shusterman when you want the same idea with more "
     "thinking in it."),
    ("divergent",
     "*The Hunger Games* is the one to read first if you skipped it, *Legend* by Marie Lu is "
     "the closest in shape, and *The Darkest Minds* by Alexandra Bracken has the same "
     "runaways-with-powers feel."),
    ("twilight",
     "*The Mortal Instruments* by Cassandra Clare is the next step for most readers, "
     "*Vampire Academy* by Richelle Mead is lighter and funnier, and *Crave* by Tracy Wolff "
     "is the newer, sillier version."),
    ("lord of the rings",
     "*The Hobbit* first if you have not read it. After that *The Name of the Wind* by "
     "Patrick Rothfuss for the prose, or *A Wizard of Earthsea* by Ursula K. Le Guin if you "
     "want the whole thing in 200 pages."),
    ("the hobbit",
     "*The Lord of the Rings* is the sequel and the reason to read it. *The Chronicles of "
     "Narnia* if you want shorter and lighter, or *A Wizard of Earthsea* for a quieter kind "
     "of magic."),
    ("game of thrones",
     "*The Blade Itself* by Joe Abercrombie for the same grim humour with fewer characters "
     "to keep track of, *The Name of the Wind* for one voice telling its own story, or *The "
     "Priory of the Orange Tree* if you want dragons in a single volume."),
    ("dune",
     "*Foundation* by Isaac Asimov for the politics across centuries, *Hyperion* by Dan "
     "Simmons for the strangeness, and *Children of Time* by Adrian Tchaikovsky for the "
     "biology."),
    ("1984",
     "*Animal Farm* by the same author first, because it is one evening's reading and the "
     "same argument. Then *Brave New World* by Aldous Huxley, and *Fahrenheit 451* by Ray "
     "Bradbury for the shortest of the three."),
    ("animal farm",
     "*1984* by the same author is the longer version of the same warning, then *Brave New "
     "World* by Aldous Huxley, or *Fahrenheit 451* by Ray Bradbury if you want it short."),
    ("brave new world",
     "*1984* by George Orwell is the pair everyone reads next, *Fahrenheit 451* by Ray "
     "Bradbury is shorter, and *The Handmaid's Tale* by Margaret Atwood is the one that "
     "still feels closest to now."),
    ("the handmaid's tale",
     "*The Testaments* by Margaret Atwood is the sequel from 2019 and answers what happened. "
     "*Vox* by Christina Dalcher is the same idea done faster, and *Red Clocks* by Leni "
     "Zumas is the quieter one."),
    ("pride and prejudice",
     "*Persuasion* is the next Austen - shorter and sadder. *Jane Eyre* by Charlotte Bronte "
     "for the gothic version, or *Bridget Jones's Diary* for the modern retelling."),
    ("the great gatsby",
     "*The Sun Also Rises* by Hemingway for the same lost generation, *Mrs Dalloway* by "
     "Virginia Woolf for a party that holds a whole life, or *Rules of Civility* by Amor "
     "Towles for the modern version."),
    ("diary of a wimpy kid",
     "*Tom Gates* by Liz Pichon is the same diary shape with more doodles, *Big Nate* by "
     "Lincoln Peirce is the school one, and *Captain Underpants* by Dav Pilkey if they want "
     "sillier."),
    ("alex rider",
     "*Cherub* by Robert Muchamore is the closest: teenagers trained as agents, more brutal "
     "than it looks. *Young Bond* by Charlie Higson for the origin story, or *Artemis Fowl* "
     "if they would rather be the genius."),
    ("jacqueline wilson",
     "*Cathy Cassidy* next for the same warm, short chapters, *The Suitcase Kid* or *Double "
     "Act* if they want another Wilson, or *Once* by Morris Gleitzman when they are ready "
     "for something harder."),
    ("agatha christie",
     "*The Thursday Murder Club* by Richard Osman for the modern cosy version, *Strong "
     "Poison* by Dorothy L. Sayers for the classic one, or *Magpie Murders* by Anthony "
     "Horowitz, which is a Christie puzzle inside a Christie puzzle."),
    ("stephen king",
     "*11.22.63* is his best if the storytelling was the draw, *The Shining* for the proper "
     "horror, and *Heart-Shaped Box* by Joe Hill - his son - for the same voice."),
    ("the fault in our stars",
     "*Eleanor & Park* by Rainbow Rowell is the closest in feeling, *Me and Earl and the "
     "Dying Girl* by Jesse Andrews if you want it funny as well as sad, and *Five Feet "
     "Apart* by Rachael Lippincott for the same story again."),
    ("the hate u give",
     "*Dear Martin* by Nic Stone is the closest next read, *The Poet X* by Elizabeth Acevedo "
     "if the voice is what you liked, and *Long Way Down* by Jason Reynolds, which is one "
     "elevator ride in verse."),
    ("wonder",
     "*Out of My Mind* by Sharon M. Draper, *Fish in a Tree* by Lynda Mullaly Hunt and *The "
     "Goldfish Boy* by Lisa Thompson all do the same thing: a child nobody expects much "
     "from, telling it themselves."),
    ("the catcher in the rye",
     "*The Perks of Being a Wallflower* by Stephen Chbosky is the closest in voice, *Looking "
     "for Alaska* by John Green for the same boy at boarding school, and *The Bell Jar* by "
     "Sylvia Plath when you want the darker one."),
    ("little women",
     "*Anne of Green Gables* by L. M. Montgomery, *Pride and Prejudice* for the sisters and "
     "the wit, or *The Railway Children* by E. Nesbit for the family doing without."),
    ("anne of green gables",
     "*Emily of New Moon* is the same author's other girl and most people who love Anne love "
     "her too. *Little Women* next, or *Pollyanna* for the same bright stubbornness."),
    ("the secret garden",
     "*The Railway Children* by E. Nesbit, *Anne of Green Gables* for another child sent "
     "somewhere she does not want to be, or *Tom's Midnight Garden* by Philippa Pearce."),
    ("narnia",
     "*The Hobbit* is the obvious next one, *A Wizard of Earthsea* by Ursula K. Le Guin for "
     "the quieter magic, and *His Dark Materials* by Philip Pullman when they are a year or "
     "two older."),
    ("his dark materials",
     "*The Chronicles of Narnia* for the other world through a door, *A Wizard of Earthsea* "
     "for the magic with a price, and *The Lie Tree* by Frances Hardinge for the historical "
     "version."),
    ("ready player one",
     "*Snow Crash* by Neal Stephenson is the book it borrows from, *Ender's Game* by Orson "
     "Scott Card is the training-school one, and *The Martian* if the problem-solving was "
     "the best part."),
)

# How a line asks for the next one, and what it calls the thing it wants. A title of the table is
# a thing to ask about too ("i loved normal people, what next" names no book at all).
# "she liked the thursday murder club" is the same request as "i loved it": the past tense of
# like was missing, so the one follow-up a person makes after being given a book was answered by
# the small-talk rows. The present tense is here for the same reason ("my mum likes thrillers").
BOOK_LIKE_ASKS = ("like", "liked", "likes", "similar", "similar to", "something like",
                  "anything like", "after", "next", "what next", "loved", "loves", "enjoyed",
                  "recommend", "recommendation")
BOOK_LIKE_THINGS = (("book", "books", "novel", "novels", "read", "reading")
                    + tuple(title for title, _reply in BOOK_MATCHES))

# "a book like X" and "something similar to X": the ask names the book it follows. The book word
# has to come first, so "i like reading before bed" is not a request for a book like reading.
LIKE_A_NAMED_BOOK = re.compile(
    r"\b(?:books?|novels?|reading|read)\s+(?:like|similar to|after)\s+([a-z0-9'&: -]{2,40})"
    r"|\b(?:something|anything)\s+(?:like|similar to)\s+([a-z0-9'&: -]{2,40})")


def _book_title_named(text):
    """The longest title of the table the line names, or "" for a line naming none of ours."""
    best = ""
    for title, _reply in BOOK_MATCHES:
        if len(title) > len(best) and re.search(r"(?<![a-z0-9])" + re.escape(title)
                                                + r"(?![a-z0-9])", text):
            best = title
    return best


def _book_like(memory, understood):
    """The book that follows the one the line names, or an honest question about that one.

    The same dozen titles are named over and over, so they have a pick prepared. One nobody here
    knows is answered honestly where the line reaches this row at all: a made-up match is worse
    than asking, and asking what they liked about it is the step that gets to a book that fits.
    """
    # The line as it was typed, not the tidied copy beside it: reading both together runs the
    # title into the second copy ("*The Seven Husbands Of Evelyn Hugo A Book Like The*").
    text = (understood.get("clean") or understood.get("norm_text") or "").lower()
    # "for a 9 year old", "for a kid": the age makes it the books-for-a-child question, which has
    # its own answer and its own shorter, funnier picks. A bare "kid" would also fence the title
    # "diary of a wimpy kid", so the phrase is spelled out.
    named = _book_title_named(text)
    scan = text.replace(named, " ") if named else text
    if re.search(r"\b\d+ ?year old|\byear olds?\b|\bkids?\b|\bchildren?\b|"
                 r"\btoddlers?\b|\bbab(?:y|ies)\b|\b(?:my|our|his|her|their) "
                 r"(?:son|daughter|child|boy|girl|grandson|granddaughter|niece|nephew)\b",
                 scan):
        return ""
    for title, reply in BOOK_MATCHES:
        if title == named:
            return reply
    found = LIKE_A_NAMED_BOOK.search(text)
    said = ""
    if found:
        said = (found.group(1) or found.group(2) or "").strip(" .?!")
        said = re.split(r"\b(?:but|that|which|without|and|because)\b", said)[0].strip(" .?!")
    if said:
        return ("I don't know *%s* well enough to match it, and a guess would waste your evening. "
                "Tell me what you liked about it - the people, the pace, or the writing - and "
                "I'll pick something close." % said.title())
    return ""


CHILD_WORDS = ("kid", "kids", "child", "children", "toddler", "toddlers", "preschooler",
               "preschoolers", "baby", "babies", "little one", "little ones", "school", "reception",
               "nursery", "year old", "year olds", "years old", "year old's", "yr old",
               # "my daughters 6th birthday" names the child by the party's own words
               "daughter", "son", "girl", "girls", "boy", "boys", "grandchild", "grandchildren",
               "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th")


# The age the line gives, in any of the shapes people write it: "a 5 year old", "my 6th
# birthday", "she is turning 4", "age 7", "7yr old". The age is what makes a party's games one
# thing or another, so it is read out of the line rather than remembered as a fact.
_AGE_SHAPES = (
    r"\b(\d{1,2})\s*(?:st|nd|rd|th)\b",                       # 6th birthday
    r"\b(\d{1,2})\s*(?:year|yr)s?[ -]old\b",                  # 6 year old, 6yr old
    r"\b(\d{1,2})\s*(?:year|yr)s?\s*olds?\b",                # 6 years old
    r"\bage[d]?\s*(\d{1,2})\b",                              # age 6, aged 6
    r"\bturning\s+(\d{1,2})\b",                              # turning 6
    r"\b(?:is|she is|hes|he is|they are)\s+(\d{1,2})\b",      # she is 6
)

_PARTY_TINY = ("Keep each game to five minutes and let everyone win: pass the parcel with a "
               "sweet in every layer, musical statues where you freeze in a silly shape, "
               "sleeping lions, and a treasure hunt of pictures taped at their height round one "
               "room. Cake and food first, games after, is easier at that age.")
_PARTY_MIDDLE = ("Ten minutes a game is plenty at that age: musical statues, pass the parcel with "
                 "a sweet in every layer, pin the tail on the donkey, and a treasure hunt of "
                 "picture clues round the garden. Sleeping lions calms them down before food, and "
                 "Simon Says fills the gap while the cake comes out.")
_PARTY_OLDER = ("At that age they want to win something: a treasure hunt with written clues, a "
                "relay or an obstacle race in the garden, and musical chairs with music they "
                "picked. Have two prizes a game so nobody is out early for long, and keep one "
                "quiet game for the end, when the sugar has worn off.")
_PARTY_ANY = ("Ten minutes a game is plenty: musical statues, pass the parcel with a sweet in "
              "every layer, pin the tail on the donkey, and a treasure hunt of picture clues "
              "round the garden. Sleeping lions calms them down before food, and Simon Says "
              "fills the gap while the cake comes out. Tell me the age and I'll pitch it right.")


def _age_in(line):
    """The child's age the line gives, or None."""
    for shape in _AGE_SHAPES:
        found = re.search(shape, line)
        if found:
            years = int(found.group(1))
            if 1 <= years <= 16:
                return years
    return None


def _party_games_for_kids(memory, understood):
    """The party games for a child, or "" when the line names no child and no age."""
    line = ((understood.get("clean") or understood.get("text") or "")).lower()
    if not any(word in line for word in CHILD_WORDS):
        return ""
    # a grown-up's party that happens to mention a child in it ("my 6 year old wants games for
    # the grown ups") is still the group list
    if "adult" in line or "grown up" in line or "grown-up" in line:
        return ""
    years = _age_in(line)
    if years is None:
        if any(word in line for word in ("toddler", "toddlers", "baby", "babies", "nursery")):
            years = 2
        else:
            said = _PARTY_ANY
            return _indoors(said, line) if "indoor" in line else said
    if years <= 4:
        said = _PARTY_TINY
    elif years <= 7:
        said = _PARTY_MIDDLE
    else:
        said = _PARTY_OLDER
    return _indoors(said, line)


def _indoors(said, line):
    """An indoor party is not a treasure hunt round the garden."""
    if "indoor" in line or "indoors" in line or "inside" in line or "flat" in line:
        return said.replace("round the garden", "round the house")
    return said


def _listen_when(memory, understood):
    """A pick for the moment the line names: a long drive, cooking, a run."""
    line = ((understood.get("clean") or understood.get("text") or "")).lower()
    # "a podcast about cooking" names the subject, not the moment, and this row read "cooking"
    # as when to listen: the podcast subject rows answer the subject ask, so this one passes.
    if "podcast" in line or "podcasts" in line:
        said = " %s " % " ".join(line.split())
        if " about " in said or " on " in said:
            return None
    if any(word in line for word in ("drive", "driving", "car", "road trip", "motorway")):
        return ("For a long drive: *Rumours* by Fleetwood Mac and *Graceland* by Paul Simon "
                "are both easy to sing along to, and *The Rest Is History* if you would rather "
                "have talking than music. Make one playlist before you go, because changing it "
                "at 70mph is the annoying part.")
    # "what music should i put on at a dinner party" was the dinner plan's answer - a tray of
    # chicken thighs - because "dinner party" is the dinner row's subject and the music word was
    # never the thing being asked about. A party is a moment to listen, and the music is what was
    # asked for, so it comes before the cooking branch (a dinner party has "dinner" in it).
    if any(word in line for word in ("kids party", "kids' party", "childrens party",
                                     "children's party", "childs party", "child's party",
                                     "toddler party", "party for kids", "party for children",
                                     "kids birthday", "childrens birthday")):
        return ("For a children's party the music wants to be louder and shorter than you think: "
                "a 60 to 90 minute playlist of songs they already know - *The Greatest Showman*, "
                "*Frozen*, Taylor Swift, whatever the school run plays - from a phone on a "
                "speaker away from the food table, started the moment they arrive. Cue musical "
                "statues about halfway through: it costs nothing and it resets a room that is "
                "getting wild.")
    # Walking in is a different moment from the first dance: "what music should i walk down the
    # aisle to" was the commute answer (it has "walk" in it), and the aisle wants an entrance.
    if any(word in line for word in ("aisle", "walking in", "processional", "walk in to",
                                     "coming in to")) and "first dance" not in line:
        return ("For the aisle pick the entrance, not a favourite song: *Canon in D* (Pachelbel) "
                "is the default for good reason, *Here Comes the Bride* (Bridal Chorus) is the one "
                "everybody knows, *A Thousand Years* (Christina Perri) or *Sweet Disposition* "
                "(Temper Trap) for something modern, or a string version of a song you love if "
                "the room is small. Two minutes is plenty, and play it again as you leave.")
    # A funeral is music asked for by the occasion, and "what is a good song for a funeral" was
    # the cost of a funeral: the money row owns the word and this is the music.
    if any(word in line for word in ("funeral", "memorial", "cremation", "crematorium", "burial",
                                     "church service", "send off", "wake")):
        return ("Three songs is the usual shape: one going in, one for the reflection or the "
                "photos, one to walk out to. *Somewhere Over the Rainbow* (the Israel "
                "Kamakawiwo'ole version) or *Ave Maria* suit a church, *Fix You* and *Everybody "
                "Hurts* suit a room that wants to cry, *My Way* (Sinatra) or *Thank You for the "
                "Days* (the Kinks) walk people out smiling. Give the funeral director titles, "
                "artists and exact versions a week ahead.")
    # "whats a good first dance song" was answered with the split-the-day advice, which is about
    # the playlist as a whole: the person asked for songs to pick from, so name some.
    if "first dance" in line:
        return ("The song you both already sing badly in the car beats any list, but if you want "
                "somewhere to start: *At Last* by Etta James, *You Are the Best Thing* by Ray "
                "LaMontagne, *Can't Help Falling in Love* by Elvis, *Tenerife Sea* by Ed Sheeran, "
                "*The Book of Love* by Peter Gabriel for something quieter, or *You're My Best "
                "Friend* by Queen for a room that will sing along. Play each one all the way "
                "through and pick the one you can sway to for three minutes without counting the "
                "beats, then give the DJ that exact version - a remix has ruined more first dances "
                "than bad dancing.")
    # "what is a good wedding song" and "songs for a wedding" were the plan - split the day, ask
    # the couple for five songs - which is advice about a playlist rather than a song. A person
    # asking for a wedding song wants titles, so the moments get titles.
    if any(word in line for word in ("signing of the register", "sign the register",
                                     "register signing", "signing the register")):
        return ("For the register, something the room knows and can hum while they wait: *A "
                "Thousand Years* (Christina Perri), *Make You Feel My Love* (Adele), *Jesu, Joy "
                "of Man's Desiring* if it is a church, or *Better Together* (Jack Johnson). Two "
                "songs is right - one while the first people sign, one for the second - because "
                "signing takes longer than anyone plans for.")
    if ("wedding" in line or "marrying" in line) and any(
            word in line for word in ("music", "song", "songs", "playlist", "band", "dj")):
        return ("Three moments, three songs: walk in - *Canon in D*, or the *Trumpet Voluntary* if "
                "it is grand; sign the register - *A Thousand Years* or *Make You Feel My Love*; "
                "walk out - *Signed, Sealed, Delivered* or *This Will Be*. For the evening, the "
                "songs everyone already knows (ABBA, Queen, *Mr Brightside*) fill a floor better "
                "than anything tasteful. Ask the couple which three songs they would dance to in "
                "an empty kitchen.")
    if any(word in line for word in ("wedding song", "wedding songs", "songs for a wedding",
                                     "wedding music", "music for a wedding", "song for a wedding",
                                     "ceremony music", "song for my wedding")):
        return ("Three moments, three songs: walk in - *Canon in D*, or the *Trumpet Voluntary* if "
                "it is grand; sign the register - *A Thousand Years* or *Make You Feel My Love*; "
                "walk out - *Signed, Sealed, Delivered* or *This Will Be*. For the evening, the "
                "songs everyone already knows (ABBA, Queen, *Mr Brightside*) fill a floor better "
                "than anything tasteful. Ask the couple which three songs they would dance to in "
                "an empty kitchen.")
    # A wedding is two rooms in one day and the wallpaper answer is wrong for both: nobody can
    # talk over a first dance, and the drinks after the meal is exactly the talking room.
    if any(word in line for word in ("wedding", "first dance", "reception", "bridal")):
        return ("Split the day, because a wedding is two different rooms: for the ceremony and the "
                "meal, something quiet and familiar that nobody has to listen to - a solo piano or "
                "string version of songs the couple likes - and for the evening, the songs everyone "
                "already knows so the dance floor fills. Ask the couple for five songs they both "
                "love and build the evening around those, keep a do-not-play list, and have the "
                "first dance track loaded and cued rather than searched for on the night.")
    if any(word in line for word in ("dinner party", "party", "barbecue", "bbq", "guests",
                                     "drinks", "buffet")):
        return ("For a room with people talking in it, the music is wallpaper, not the show: "
                "something familiar and mid-tempo that nobody has to listen to - a Motown or "
                "soul compilation, *Rumours*, or any 'dinner party' playlist in the 90 to 110 "
                "beats-per-minute range. Start it thirty minutes before people arrive, keep it "
                "quiet enough to talk over while you eat, and turn it up once the plates are "
                "cleared.")
    # a wet afternoon is a moment for an album rather than a playlist, and it is the one moment
    # asked for as a statement ("rainy day music") as often as a question. A podcast ask is the
    # podcast rows' line, so this branch passes those on rather than handing them albums.
    if "podcast" not in line and any(word in line for word in (
            "rainy day", "rainy afternoon", "rainy sunday", "rainy weekend", "rainy morning",
            "wet afternoon", "wet day", "wet weekend", "snowy day", "stuck indoors")):
        return ("For a rainy day: *Rumours* by Fleetwood Mac, *Blue* by Joni Mitchell if you "
                "want something quieter, or *Graceland* by Paul Simon for a kitchen that needs "
                "waking up. Rain is the one day a whole album beats a playlist, so put one on "
                "and leave it alone.")
    if any(word in line for word in ("cook", "cooking", "kitchen", "dinner")):
        return ("While you cook: *Kind of Blue* by Miles Davis, *The Köln Concert* by Keith "
                "Jarrett, or any Motown compilation. All of them have no words to follow, so "
                "you can still hear the timer.")
    if any(word in line for word in ("run", "running", "jog", "gym", "workout")):
        return ("For a run: something around 160 to 170 beats per minute keeps the pace steady, "
                "so *Mr Brightside*, *Titanium* and *Don't Stop Me Now* all work, or a Daft Punk "
                "album run straight through if you would rather not think about it.")
    if any(word in line for word in ("walk", "walking", "way to work", "walk to work",
                                     "commute", "commuting", "journey to work")):
        return ("For a commute: *The Rest Is History* or *Desert Island Discs* if you want "
                "talking, *Rumours* if you want music. Podcasts beat music for a commute because "
                "the time passes without you counting it.")
    return ("For a long listen: *Rumours* by Fleetwood Mac, *Graceland* by Paul Simon, or *The "
            "Rest Is History* if you would rather hear talking. Tell me what the journey is and "
            "I'll make it specific.")


def _family_film(memory, understood):
    """A funny film, child-shaped only when a child is actually in the line."""
    clean = understood.get("clean") or ""
    said = " ".join(str((understood or {}).get(key) or "") for key in ("clean", "text"))
    # a teenager is what a child grows into, and "a film for my teenage son" has no small-child
    # word in it, so the teen words open the door as well
    if not any(word in said for word in CHILD + ("family", "teenager", "teenagers", "teen", "teens")):
        return _films_within(
            "For a laugh: *Groundhog Day* is the funniest safe pick, *The Grand Budapest Hotel* "
            "if you want something stylish with the same warmth, and *Paddington 2* if you want "
            "to laugh from the first minute. All three are fine with anyone in the room.", said)
    # A teenager is named far more often than a child of a given age, and the 8-to-11 reply read
    # to a parent of a fifteen-year-old as advice for a small child. Teens first, then the age.
    if re.search(r"\bteen\w*|\badolescen\w*|\b1[3-9]\s*(?:year|yr)"
                 r"|\b(?:aged|age)\s*1[3-9]\b", clean):
        return ("With teenagers in the room: *Spider-Man: Into the Spider-Verse* (funny, fast and "
                "genuinely good), *Knives Out* if they will sit through a 12A whodunnit, and "
                "*Back to the Future* for the one everybody ends up watching. *The Mitchells vs "
                "the Machines* is the safe pick for a mixed-age sofa, and *Paddington 2* still "
                "works on a teenager who has not seen it.")
    # Every age in the line, not the first one: "i have a 4 year old and a 6 year old" read the
    # 6 and answered a five-or-six-year-old, and "my son is 4" read nothing and answered the
    # 8-to-11 reply. The youngest is who the film has to suit.
    ages = [int(a or b or c) for a, b, c in re.findall(
        r"\b(\d{1,2})\s*(?:year|yr)s?[ -]old\b|\bage[d]?\s*(\d{1,2})\b"
        r"|\b(?:is|are)\s+(\d{1,2})\b", clean)]
    ages = sorted(set(n for n in ages if 1 <= n <= 16))
    if ages:
        years = ages[0]
        if years <= 4:
            return ("For a four-year-old: *The Gruffalo* and *Room on the Broom* (both about 25 "
                    "minutes) and *The Snail and the Whale* are the safest, then *Zootropolis* or "
                    "*Paddington 2* for a full film. Save *Matilda* and *The Mitchells vs the "
                    "Machines* for a year or two.")
        if years <= 7:
            return ("For a five- or six-year-old: *Paddington 2* (funny, warm, no real peril), "
                    "*The Gruffalo* and *Room on the Broom* (both about 25 minutes), and "
                    "*Zootropolis* if you want a full film. Save *Matilda* for a year or two.")
    return ("*Paddington 2*: funny for the adults too, and nothing in it will scare an 8- or "
            "11-year-old. *The Mitchells vs the Machines* or *Matilda* are good backups.")


# A named film gets a pick that matches it. The old entry answered every "a film like ..."
# with the Paddington reply, which is only right when Paddington is the film they mean.
FILM_MATCHES = (
    ("paddington", "If you liked *Paddington*, try *The Mitchells vs the Machines* or *Matilda*: "
                   "warm, funny and nothing scary. For a clever, warm film, *Knives Out* or *The "
                   "Grand Budapest Hotel* are the next step."),
    ("martian", "If you liked *The Martian*, try *Apollo 13* (tense and practical), *Arrival* "
                "(clever and quiet) or *Gravity* (a tight 90 minutes). All solve problems rather "
                "than fight."),
    ("get out", "If you liked *Get Out*, *Us* and *Nope* are the closest Jordan Peele follow-ups, "
                "and *Sorry to Bother You* is stranger and sharper. All three are unsettling "
                "rather than gory."),
    ("john wick", "If you liked *John Wick*, try *Atomic Blonde* or *Nobody* for the same close-up "
                  "action, or *The Raid* if you want the fights turned up. Short on plot, long on "
                  "choreography."),
    ("interstellar", "If you liked *Interstellar*, try *Arrival* for the ideas, *Contact* for the "
                     "wonder and *Moon* for a small, tense one. All quieter than *Interstellar*."),
    ("knives out", "If you liked *Knives Out*, *Glass Onion* is the direct sequel; *The Grand "
                   "Budapest Hotel* has the same wit, and *Clue* is the silly classic."),
    ("godfather", "If you liked *The Godfather*, try *Goodfellas* or *The Departed* for crime with "
                  "momentum, or *Heat* for the bank job and the shootout."),
    ("mean girls", "If you liked *Mean Girls*, try *Clueless*, *Easy A* or *Booksmart*: the same "
                   "sharp high-school comedy, all easy to like."),
    # People name a series as often as a film, and "I liked Breaking Bad, what next" is the same
    # question, so the series are rows in the same table.
    ("breaking bad", "After *Breaking Bad*: *Better Call Saul* first (same world, slower and just "
                     "as good), then *Ozark* for the same dread, or *Narcos* if you want the real "
                     "story. *The Wire* is the step up if you have not seen it."),
    ("the bear", "After *The Bear*: *Boiling Point* (the film, one unbroken take), *Burnt* for a "
                 "lighter kitchen, or *The Bear*'s closest cousin *Shameless* (US) for a family "
                 "that shouts. All short episodes."),
    ("happy valley", "After *Happy Valley*: *Sherwood*, *Bodyguard* or *Line of Duty* for British "
                     "tension, and *Unforgotten* if you want the detective work without the "
                     "violence. *Scott & Bailey* is the gentler one."),
    ("succession", "After *Succession*: *The Thick of It* (same writer, sharper jokes), "
                   "*Billions* for the money, or *Industry* for the young version. *Veep* if you "
                   "want the comedy turned up."),
    ("stranger things", "After *Stranger Things*: *Dark* (German, twistier), *The OA*, or "
                        "*Super 8* for the film version. *Paper Girls* is the closest comic-book "
                        "feel."),
    ("the crown", "After *The Crown*: *The Queen* and *The Iron Lady* for the same world in film "
                  "form, *Victoria* for the earlier reign, or *A Very English Scandal* for the "
                  "same era and wit."),
    ("line of duty", "After *Line of Duty*: *Happy Valley* first, then *Bodyguard*, *Sherwood* or "
                     "*Vigil*. All British, all tense, none gory."),
    ("peaky blinders", "After *Peaky Blinders*: *Boardwalk Empire* (the American version), "
                       "*Gangs of London* for the violence, or *Taboo* with the same lead actor. "
                       "*Ripper Street* for the period."),
    ("game of thrones", "After *Game of Thrones*: *House of the Dragon* is the direct prequel; "
                        "*The Last Kingdom* is the better-paced one, and *Rome* is the closest in "
                        "scheming."),
    ("friends", "After *Friends*: *Brooklyn Nine-Nine* for the same comfort, *Parks and "
                "Recreation* (start at series 2), or *Schitt's Creek*, which gets funny fast. "
                "*How I Met Your Mother* if you want the same shape."),
    ("the office", "After *The Office*: the UK original if you have only seen the US one, then "
                   "*Parks and Recreation*, *Brooklyn Nine-Nine* or *Superstore*. All the same "
                   "mockumentary warmth."),
    ("derry girls", "After *Derry Girls*: *The Young Offenders*, *Moone Boy* or *This Way Up* for "
                    "the same sharp Irish comedy. *Bad Sisters* if you want a darker one."),
    ("friday night dinner", "After *Friday Night Dinner*: *The Inbetweeners* or *Gavin & Stacey* "
                            "for the same family shouting, and *Plebs* if you want the silly "
                            "version."),
    ("ted lasso", "After *Ted Lasso*: *Schitt's Creek* (the same kindness arriving slowly), "
                  "*Detectorists* for the gentle British version, or *The Good Place* if you want "
                  "the jokes and the thinking."),
    ("the wire", "After *The Wire*: *The Shield* and *Generation Kill* (same creator), *Bosch* for "
                 "the police work, or *Oz* for the same prison-city sweep."),
)
# A line that only says it loved a title ("I loved Breaking Bad", "finished the crown") has no
# second half of its own: the title is the subject. The table above is the list, so the titles go
# into the key as phrases and a new title is still one row.
AFTER_TITLE_WORDS = tuple(title for title, _ in FILM_MATCHES)

# Seven of those titles are ordinary English as well as titles, and the people sense is commoner
# than the programme: "my friends loved it" and "i loved the office" carry both halves of the
# key, so the table answered them with a pick. A title that is also a plain phrase only counts
# when the line says it is a work - a screen or reading word, or a finishing one - or when it
# asks for the next thing, which only makes sense of a work.
PLAIN_TITLES = frozenset((
    "friends", "the office", "the crown", "the bear", "the wire", "get out"))
# The phrases that make the plain sense certain, so a line with one of them never reaches the
# table even when it also says "film": "my friends loved the film" is a night out, not *Friends*.
PLAIN_SENSE = {
    "friends": ("my friends", "our friends", "his friends", "her friends", "their friends",
                "your friends", "make friends", "new friends", "best friends", "best friend",
                "friends are", "friends came", "friends and family", "a few friends"),
    "the office": ("my office", "our office", "your office", "his office", "her office",
                   "their office", "new office", "back to the office", "at the office",
                   "in the office", "the office is", "office job", "office chair", "office move",
                   "office party"),
    "the crown": ("my crown", "the crown of", "crown court", "crown jewels", "crown fell",
                  "half crown", "crown is loose", "crown came off"),
    "the bear": ("a bear", "the bear is", "bears are", "bear attack", "polar bear", "teddy",
                 # a bear claw is a pastry, and the title is a word inside it
                 "bear claw", "bear claws", "claw"),
    "the wire": ("a wire", "the wire is", "wires", "wiring", "rewire", "live wire", "wire wool"),
    "get out": ("get out of", "got out of", "getting out of", "get out the", "get out more"),
    "knives out": ("knives out for", "sharp knives", "kitchen knives"),
}
WORK_EVIDENCE = (
    "watch", "watched", "watching", "film", "films", "movie", "movies", "series", "show",
    "shows", "episode", "episodes", "season", "seasons", "binge", "binged", "bingeing",
    "stream", "streamed", "netflix", "tv", "telly", "iplayer", "prime video", "read", "reading",
    "book", "books", "novel", "novels", "chapter", "finished", "finishing", "seen", "started",
    "caught up", "got through", "box set")
NEXT_EVIDENCE = (
    "what next", "what now", "what else", "anything else", "something else", "similar",
    "anything like", "something like", "like that", "recommend", "recommendation",
    "recommendations", "suggestion", "suggestions", "what should i watch")


# A person inventing something is asking for help with their own story, not about a book that
# exists, so these lines must not reach the author lookup at all.
MAKING_UP = ("i'm writing", "im writing", "i am writing", "i'm trying to write",
             "im trying to write", "writing a story", "writing a novel", "writing a book",
             "write a story", "write a novel", "help me write", "my own story", "my novel",
             "my story", "my character", "my main character", "in my story", "for my story",
             "a story where", "a story set in", "story where", "script", "screenplay",
             "short story", "plot", "villain", "poem about")



# The list the general film pick gives. Named once, because a line that asks for films without
# naming a mood is answered with it from two rows: the general pick, and the follow-up on a liked
# work when the line turns out to be a fresh ask for films rather than a follow-up at all.
EASY_FILM_LIST = ("If you want something easy and good tonight: *Groundhog Day* for comedy, "
                  "*Knives Out* for a clever whodunnit, or *Arrival* if you'd rather think. All "
                  "three work on a sofa with no planning.")


# A line asking for a film, as against one that only mentions one: "i want a film", "what's a good
# film", "any film recommendations". The reading glues the chat's last subject onto the line, so
# "they liked the one with the hotel in it" arrives as "the film watch liked the one with the
# hotel in it" and a bare mention of the medium is not an ask for one.
_ASKS_FOR_A_FILM = re.compile(
    r"\b(?:want|wants|need|needs|fancy|looking for|after|recommend|recommendation|suggest|"
    r"should i|shall i|can you|could you|give me|got any|any|what|which|good|best|decent|"
    r"mood for|in the mood)\b")


# The answer to a line that turns a scare down. It says what the person wants, never what they
# turned down: it used to open "Skip horror and gore ... without any blood", and the next line of
# the conversation read that word back as the subject - "i dont want a scary film what should i
# watch" then "anything a bit lighter" answered with *Get Out* and *The Haunting of Hill House*.
# A follow-up is read with the turn before it, so the bot's own turn must not name the thing the
# person just refused.
GENTLE_LIST = ("*Knives Out*, *The Grand Budapest Hotel* and *Paddington 2* are warm, funny and "
               "tense in the right places, and nothing that will keep you up. For a series, *The "
               "Detectorists* is gentle and very good, *Ghosts* is daft and kind, and *Happy "
               "Valley* is the tense British crime one.")


def _the_gentle_list(memory, understood):
    """The gentle list, or the lighter shelf when that is the answer the chat already has.

    "what else is good" after this answer is somebody who wants another shelf, not the same one
    read out again: the composer catches the repeat and answers with a shrug, which is the one
    reply that ignores the question. The lighter table is a different list of titles, so it is a
    real second answer.
    """
    last = memory.get("last_answer") if isinstance(memory, dict) else None
    said = str((last or {}).get("reply") or "") if isinstance(last, dict) else ""
    if said and _plain_words(said) == _plain_words(GENTLE_LIST):
        # A line that names a series or a book asks for that half of this answer, and the
        # composer takes the sentence about it out of the copy above, so the copy stays. The
        # follow-up arrives with the turn before it on the front, and that turn says "films", so
        # only a medium other than the film counts here: "and a series" keeps the copy, "what
        # else is good" gets the other shelf.
        if _pick_kind(" ".join(_own_texts(understood))) not in ("", "film"):
            return GENTLE_LIST
        # Not the light list: it shares *Paddington 2* and *The Detectorists* with the copy above,
        # and the composer reads two answers that overlap that much as the same answer given
        # twice, so the second one comes back as a shrug. The funny shelf names three different
        # films, which is what "what else is good" is asking for.
        other = FILM_MOODS.get("funny") or ""
        if other and _plain_words(other) != _plain_words(GENTLE_LIST):
            return other
        return None
    return GENTLE_LIST


def _the_chat_turned_down(names, memory, after=None):
    """Whether a recent turn named one of `names` only to turn it down.

    A follow-up does not keep the words it was written in. "i dont want to watch a musical" then
    "what else" reaches a row as "what else what else watch musical", so no refusal is left beside
    the word and a reader that only looks at the line has to guess: the musical shelf answered a
    person who had just said no to musicals with three of them. The turns themselves are kept, so
    the refusal is read there.

    The newest turn that names the thing decides: a chat that turned musicals down and then asked
    about one positively is asking about it.
    """
    topics = memory.get("topics") if isinstance(memory, dict) else None
    if not isinstance(topics, list):
        return False
    names = frozenset(names)
    for topic in reversed(topics):
        text = str(topic.get("text") or "") if isinstance(topic, dict) else ""
        if not text:
            continue
        if not (names & frozenset(_plain_words(text).split())):
            continue
        return _a_word_is_turned_down(text, names, after)
    return False


def _the_mood_the_chat_turned_down(memory):
    """Whether a recent turn turned a mood down, newest first.

    The other end of `_the_mood_the_chat_holds`: "i dont want a scary film" then "anything a bit
    lighter" has no mood in its own words, and the mood it wants is the one at the far end of the
    one that was refused. Without this the follow-up got the scare list, and once the scare list
    stopped being read off the glued line it got a shrug instead.
    """
    topics = memory.get("topics") if isinstance(memory, dict) else None
    if not isinstance(topics, list):
        return False
    for topic in reversed(topics):
        text = str(topic.get("text") or "") if isinstance(topic, dict) else ""
        if not text:
            continue
        got = _mood_of(text)
        if got:
            return bool(got[1])
    return False


def _the_mood_the_chat_holds(memory):
    """The mood a recent turn named, or None.

    "any films for the flight" comes after "something funny rather than crime", and the mood is
    still the best clue there is about what to offer: the list it gets should be the funny one,
    not the general one. Only what the person said is looked at, newest first, and a mood they
    turned down does not count as one they want.
    """
    topics = memory.get("topics") if isinstance(memory, dict) else None
    if not isinstance(topics, list):
        return None
    for topic in reversed(topics):
        text = str(topic.get("text") or "") if isinstance(topic, dict) else ""
        if not text:
            continue
        got = _mood_of(text)
        if got and not got[1]:
            return got[0]
    return None


def _film_like(memory, understood):
    """A pick that follows the named film, or an honest question when it is not one we know."""
    # The raw line and the tidied one are read one at a time. Joined into a single string the
    # tail of the first runs into the head of the second, so "a film like inception" came out
    # as the title *Inception A Film Like Inception*.
    texts = [one.lower() for one in (understood.get("clean") or "",
                                     understood.get("norm_text") or "") if one]
    if not _the_liked_thing_is_asked_about(understood):
        # The line asks for films in the plural and brings no liked thing of its own, so it is
        # not a follow-up however the word "liked" reached this row: the general list is the
        # answer, and asking what they liked about the last one answers a question nobody asked.
        held = _the_mood_the_chat_holds(memory)
        if held:
            picks = FILM_MOODS.get(held)
            if picks:
                return _films_within(picks, str(understood.get("clean") or ""))
        return EASY_FILM_LIST
    for text in texts:
        pick = _table_pick(text)
        if pick:
            return pick
    for text in texts:
        named = re.search(r"\b(?:film|movie|show|series|programme)s?\s+(?:like|similar to)\s+"
                          r"([a-z0-9'&: -]{2,40})", text)
        if named:
            title = re.split(r"\b(?:but|that|which|without|and|or|please)\b"
                             r"|\b(?:film|movie|show|series|programme)s?\b",
                             named.group(1))[0].strip(" .?!")
            if title:
                return ("I don't know *%s* well enough to match it. Tell me what you liked about "
                        "it: the story, the jokes, or how tense it was, and I'll pick something "
                        "close." % title.title())
    # The ask-back is for a line asking for a film with no film named. A line that names no
    # medium at all reached this row only because the chat is holding the word "liked" - "they
    # liked the one with the hotel in it" got "Tell me what you liked about the last film you
    # enjoyed", a question in place of an answer - so the turn goes on to the rows that answer
    # the line as it was typed.
    own = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    if not (_ASKS_FOR_A_FILM.search(own) and re.search(r"\b(?:films?|movies?)\b", own)):
        return ""
    return ("Tell me what you liked about the last film you enjoyed: the story, the jokes, or how "
            "tense it was. Name one and I'll suggest something close.")


# A scare is the mood people turn down as often as they ask for it, and they turn it down in
# dozens of ways: "not a scary one", "a film but no horror", "anything but horror", "i hate scary
# films", "scary films are not for me", "something to watch that isnt scary". Held as a list of
# avoided phrases the reading is one wording out of date: every new way of saying it left the
# scare word alone in the line, the row keyed on "scary" won on that word, and a person who asked
# to be spared a scare was handed *Get Out*, *A Quiet Place* and *Hereditary*. So the turn-down is
# read off the line instead - the scare word, then a refusal in the few words either side of it -
# and the row for the scary picks stands down for every wording, including ones nobody has typed
# yet. `_mood_of` already reads the same refusal; the trouble was that the mood row lost the
# ranking to a row keyed on the scare word, so the test belongs on that row as a guard.
SCARE_WORDS = frozenset(("scary", "scariest", "scare", "scares", "scared", "horror", "horrifying",
                         "horrific", "frightening", "frightened", "creepy", "terrifying", "spooky",
                         "gory", "gore", "blood", "bloody", "haunted", "slasher", "zombie",
                         "ghost", "jump scare"))
# Refusals that NEGATORS does not carry: the ones that turn a mood down without a "not" in them.
SCARE_TURNED_DOWN = frozenset(("dislike", "dislikes", "loathe", "detest", "bored", "sick",
                               "tired", "over", "spare", "except", "against", "refuse", "stop",
                               "done", "meh", "avoid"))
# And the refusals that come *after* the scare word. These are phrases, not single words, because
# a "not" after it usually turns down something else: "i want a scary film not a comedy" refuses
# the comedy, and reading its "not" as a refusal of the scare answered with the gentle list.
SCARE_REFUSED_AFTER = re.compile(
    r"\b(?:is|are|was|were)?\s*(?:not|never)\s+(?:really\s+)?(?:for\s+(?:me|us)|my\s+(?:thing|"
    r"sort|cuppa|cup|kind)|what\s+i|something\s+i|anything\s+i|a\s+fan|keen|into\s+it)\b"
    r"|\bis\s+out\b|\bare\s+out\b|\btoo\s+much\b|\btoo\s+scary\b|\bscares?\s+me\b"
    r"|\bmakes?\s+me\s+(?:jump|nervous)\b|\bgives?\s+me\s+nightmares\b|\bover\s+the\s+top\b",
    re.I)
# "not sure" and "no idea" are not turn-downs: they are how a person opens the ask ("not sure what
# to watch, something scary?"), and a line like that still wants the scary picks.
NOT_A_TURN_DOWN = re.compile(
    r"\b(?:not\s+(?:really\s+)?sure|no\s+idea|no\s+clue|not\s+bothered|do\s+not\s+mind|"
    r"do\s+not\s+care|not\s+fussed)\b", re.I)


# A turn-down said as a want rather than as a "not": these are the ways people type "i do not want
# that", and reading them as one word is what lets the same reader answer every "not that" here.
TURNED_DOWN_WANT = ("dont really want", "do not really want", "dont want", "do not want",
                    "dont fancy", "do not fancy", "dont feel like", "do not feel like",
                    "not in the mood for", "not really in the mood for", "not into",
                    "bored of", "bored with", "tired of", "sick of", "no more",
                    "anything but", "apart from", "other than", "except for", "nothing with",
                    "dont like", "do not like", "cant stand", "can not stand", "cannot stand")


# The words that turn a line back round: everything before one of these is about something the
# person has already left behind ("i dont want a comedy but a film about war" wants the war).
TURNS_BACK = frozenset(("but", "instead", "rather", "prefer", "preferably", "though", "however",
                        "actually", "or"))


def _a_word_is_turned_down(text, names, after=None):
    """True when the line names one of `names` only to turn it down.

    The same reading answers every "not that" in this module. The word is found first, then a
    refusal in the four words before it, or one of the phrases in `after` in the eight words
    following. *"i fancy a film but not a scary one"* and *"scary films are not for me"* both
    name the scare only to leave it out, and *"i dont want a musical"* names the musical.
    """
    names = frozenset(names)
    if not names or not isinstance(text, str) or not text:
        return False
    plain = NOT_A_TURN_DOWN.sub(" ", _plain_words(text))
    # A turn-down said as a want ("i dont want a musical", "i dont fancy anything christmassy") has
    # no "not" of its own once the phrase is read, so it is turned into one here. "anything but
    # horror" and "apart from horror" are the same shape.
    for phrase in TURNED_DOWN_WANT:
        plain = plain.replace(phrase, " not ")
    words = plain.split()
    for at, word in enumerate(words):
        if word not in names and word.rstrip("s") not in names:
            continue
        # Four words back covers every ordinary wording ("but not a scary one", "no scary films",
        # "i hate scary films", "i can not stand horror") and is short enough that a "no"
        # belonging to something else stays out of the window: "no plans tonight, something
        # scary?" is a want, and so is "not sure what to watch, something scary?".
        # A subject is named with more words between it and the refusal than a mood is -
        # "i dont want to watch a film about war" puts five in between - so the window is eight
        # words and it stops at the first word that turns the line back round. "i dont want a
        # comedy but a film about war" refuses the comedy and wants the war, and the "but" is
        # what says so.
        before = words[max(0, at - 8):at]
        for cut in range(len(before) - 1, -1, -1):
            if before[cut] in TURNS_BACK:
                before = before[cut + 1:]
                break
        if any(one in NEGATORS or one in SCARE_TURNED_DOWN for one in before):
            return True
        if after is not None and after.search(" ".join(words[at + 1:at + 9])):
            return True
    return False


def _own_texts(understood):
    """The line's own words, without the context a follow-up carries.

    A follow-up reaches the tables with the turn before it glued on the end of `clean`:
    *"he has never done anything to it"* arrives as "he has never done anything to it dog scared",
    and a refusal read off that is a refusal of the turn before, not of this one. `text` and
    `norm_text` are the line itself.
    """
    understood = understood if isinstance(understood, dict) else {}
    text = understood.get("text")
    if isinstance(text, str) and text.strip():
        return [text]
    texts = []
    for key in ("norm_text", "clean"):
        value = understood.get(key)
        if isinstance(value, str) and value and value not in texts:
            texts.append(value)
    return texts


def _the_scare_is_refused(understood):
    """True when the line names a scare only to turn one down.

    *"i fancy a film but not a scary one"* and *"scary films are not for me"* are both asks for a
    film; the scare word in them is the thing to leave out, not the thing to fetch.
    """
    for text in _own_texts(understood):
        if _a_word_is_turned_down(text, SCARE_WORDS, SCARE_REFUSED_AFTER):
            return True
    return False

# The medium words the gentle list may answer on. It is the row for a film ask that turns a scare
# down, so a line naming neither a medium nor a scare of its own is somebody else's question: a
# follow-up like "he has never done anything to it" carries the "scared" of the turn before it and
# no medium at all, and the wide key alone handed a puppy question the gentle film list.
FILM_ASK_WORDS = frozenset(("film", "films", "movie", "movies", "series", "watch", "watching",
                            "telly", "tv", "netflix", "boxset", "episode", "episodes", "iplayer"))


def _a_film_ask(understood):
    """The guard on the gentle list: the line has to name a medium, or turn a scare down itself."""
    for text in _own_texts(understood):
        plain = " " + _plain_words(text) + " "
        if any((" " + word + " ") in plain for word in FILM_ASK_WORDS):
            return True
    return _the_scare_is_refused(understood)


def _the_scare_is_wanted(understood):
    """The guard on the scary picks: a line that turns a scare down is asking the other row."""
    return not _the_scare_is_refused(understood)


def _work_named(text):
    """The longest title of the table the line names, or "" for a line that names none."""
    best = ""
    for title in VIEWS:
        if len(title) > len(best) and re.search(r"(?<![a-z0-9])" + re.escape(title)
                                                + r"(?![a-z0-9])", text):
            best = title
    return best


# The follow-up on a liked work keys the bare "liked", and the chat holds that word for several
# turns after somebody says it: "any films for the flight" is a request for a list, and it was
# answered with "Tell me what you liked about the last film you enjoyed". A line that asks for the
# list in the plural, and brings no like verb and no title of its own, is the list row's question.
_FRESH_LIST = re.compile(
    r"\b(?:any|some|more|which|what)\s+(?:good\s+|other\s+|different\s+)?(?:films?|movies?|"
    r"books?|novels?|series|shows?|programmes?|programs?|podcasts?)\b"
    r"|\b(?:films?|movies?|books?|novels?|series|shows?|programmes?|programs?|podcasts?)\s+"
    r"(?:for|to watch|to read|to listen|on the|for the)\b")


def _the_liked_thing_is_asked_about(understood):
    """False for a fresh ask for a list, which is not a follow-up on the work the chat liked.

    The guard keeps the good half of the row - "i loved it, what next", "she liked the one with
    the hotel in it", a named title - and stands it down only where the line asks for the list
    itself: a plural medium word with no like verb and no title in it.

    The line as typed, not `clean`: the reading glues the word the chat is holding onto the end
    of it, so "any films for the flight" arrives as "any films for the flight liked" and every
    guard read off it would be a guard about the turn before.
    """
    reading = understood if isinstance(understood, dict) else {}
    own = str(reading.get("text") or reading.get("clean") or "").lower()
    if not _FRESH_LIST.search(own):
        return True
    if re.search(r"\b(?:like|likes|liked|loves?|loved|enjoyed|similar)\b", own):
        return True
    return bool(_book_title_named(own) or _work_named(own))


# "is it worth seeing someone" asks about a person to consult, not a verdict on a work: the
# object of "seeing" is a doctor, a physio, a vet, somebody at all. Read before the judge asks,
# because "worth seeing" is one of them.
A_PERSON_TO_CONSULT = re.compile(
    r"\b(?:see|seeing|visit)\s+(?:someone|somebody|anyone|anybody|him|her|them|"
    r"(?:a|the|my|your)\s+(?:doctor|gp|dentist|nurse|physio\w*|specialist|consultant|surgeon|"
    r"optician|vet|midwife|pharmacist|counsellor|therapist|chiropractor|osteopath))\b")


def _about_a_person(text):
    """True for a line asking what suits somebody else, which is not a verdict on a work."""
    if AGE_ASK.search(text):
        return True
    return bool(not ASKING_FIRST.search(text) and SEEN_ALREADY.search(text))


def _a_place_not_a_work(text):
    """True when the line is about going to work rather than about watching or reading.

    Two works in the table have an everyday meaning as well, and one of them is a place: *The
    Office*. A line that names a commute, a boss or a set of office days is about the job, and a
    verdict on the series answers a question nobody asked, so this hands it back.
    """
    return bool(_THE_OFFICE_IS.search(text)
                or any(phrase in text for phrase in A_PLACE_NOT_A_WORK))


# Where a person starts with a kind of music they have never listened to. The genre is the
# whole subject ("how do i get into jazz" names no album, band or song), so the answer has to
# name a first record and say how to listen to it, not list the genre's greatest hits.
GENRE_START = {
    "jazz": ("*Kind of Blue* by Miles Davis is the one to start with: quiet, unhurried, and every "
             "tune is a simple theme with the solos built on it. Then *Blue Train* by John "
             "Coltrane for something with more muscle, and *Ella and Louis* if you would rather "
             "hear a voice first. Play one album right through twice before you decide - jazz "
             "gives up its tune on the second listen."),
    "classical": ("Start with the short, loud, famous pieces rather than a symphony: Vivaldi's "
                  "*Four Seasons*, the first movement of Beethoven's fifth, and Holst's *The "
                  "Planets*. Then sit with one symphony whole - Beethoven's seventh, or Dvorak's "
                  "*New World* - because the point of the long form is how it carries you from "
                  "the first minute to the last. Films are a good way in too: most film scores "
                  "are classical music that already has your attention."),
    "hip hop": ("*Illmatic* by Nas for words and storytelling, *The Miseducation of Lauryn Hill* "
                "for singing and soul, and *good kid, m.A.A.d city* by Kendrick Lamar for a whole "
                "album that tells one story. Read the words once on paper - rap is the one pop "
                "form where the writing rewards a second pass."),
    "rap": ("*Illmatic* by Nas for words and storytelling, *The Miseducation of Lauryn Hill* for "
            "singing and soul, and *good kid, m.A.A.d city* by Kendrick Lamar for a whole album "
            "that tells one story. Read the words once on paper: rap is the one pop form where "
            "the writing rewards a second pass."),
    "country": ("*Live at Folsom Prison* by Johnny Cash is the doorway: no polish, all story. Then "
                "Dolly Parton's *Jolene* for the songwriting, and Chris Stapleton's *Traveller* if "
                "you want the modern, soul-tinged end of it. Country is story-first, so listen to "
                "the words before the twang."),
    "metal": ("*Paranoid* by Black Sabbath for where it came from, *Master of Puppets* by "
              "Metallica for the playing, and *The Number of the Beast* by Iron Maiden for the "
              "melody. Start with one band, not a playlist: metal makes more sense album by album."),
    "soul": ("*What's Going On* by Marvin Gaye, *Otis Blue* by Otis Redding, and Stevie Wonder's "
             "*Songs in the Key of Life* cover the whole of it - protest, heartbreak and joy. "
             "Motown's *The Ultimate Collection* of singles is the cheap way in if you only know "
             "the hooks."),
    "motown": ("Start with the singles: *The Ultimate Collection* by The Supremes or a Motown "
               "greatest-hits record, then *What's Going On* by Marvin Gaye and Stevie Wonder's "
               "*Songs in the Key of Life* for what the hit factory turned into."),
    "blues": ("*King of the Delta Blues* by Robert Johnson for the source, *Live at the Regal* by "
              "B.B. King for what a guitar can say to a room, and *At Newport* by Muddy Waters for "
              "the electric jump from country blues to the band that became rock."),
    "folk": ("*Pink Moon* by Nick Drake for voice and guitar alone, *Blood on the Tracks* by Bob "
             "Dylan for words, and Fleet Foxes' first album if you want harmony. Folk is words and "
             "one instrument, so start with one person and a guitar."),
    "reggae": ("*Exodus* by Bob Marley and the Wailers is the album, and *Legend* is the singles if "
               "you want the familiar ones first. Then Toots and the Maytals' *Funky Kingston* for "
               "the voice, which is the best shouting in the genre."),
    "punk": ("*Never Mind the Bollocks* by the Sex Pistols for the noise, *London Calling* by The "
             "Clash for what punk did with the rest of music, and *Rocket to Russia* by the "
             "Ramones for songs under three minutes. Loud, short, and it makes sense in a car."),
    "electronic": ("*Discovery* by Daft Punk for tunes, *Selected Ambient Works 85-92* by Aphex "
                   "Twin for the quiet end, and The Chemical Brothers' *Dig Your Own Hole* for the "
                   "big-beat one. Dance music is built to be heard whole, so let an album run."),
    "techno": ("Start with the compilations rather than a single artist: a *Fabric* or *Global "
               "Underground* mix, then Jeff Mills' *The Occurrence* for how stripped back it can "
               "be. Techno is about the build over eight minutes, so give it time."),
    "house": ("*Discovery* by Daft Punk and a *Defected* house compilation cover the friendly end, "
              "then Frankie Knuckles' *Best of* for where the sound started. House is warm and "
              "repetitive on purpose - let it run and it works."),
    "opera": ("Start with *La Boheme* or *Carmen* - two or three hours, famous tunes, and a story "
              "you can follow without the plot notes. Watch a filmed production rather than "
              "listening only, because a lot of what happens is on the faces. Subtitles are normal, "
              "not cheating."),
    "k-pop": ("Start with one group and one record: *Love Yourself: Tear* by BTS, or *Born Pink* by "
              "BLACKPINK if you want the louder one. Watch the videos as well as playing the album -"
              " the visuals are half of what the form is."),
    "gospel": ("*Amazing Grace* by Aretha Franklin, then *The Gospel According to...* by the "
               "Staple Singers, and Mahalia Jackson's *Greatest Hits* for the voice that set the "
               "standard. It is church music first, so the live recordings beat the studio ones."),
    "disco": ("*Saturday Night Fever* is the honest starting point, then Chic's *Risque* for the "
              "guitar and Donna Summer's *Bad Girls* for the voice. Disco is a rhythm, so play it "
              "loud in the kitchen and it explains itself."),
    "indie": ("*Funeral* by Arcade Fire, *Is This It* by The Strokes, and *For Emma, Forever Ago* "
              "by Bon Iver cover the three strands: the big one, the fast one and the quiet one."),
}
# The words that make a named genre a request for somewhere to start rather than a remark
# ("i like jazz") or a definition question ("what is jazz", which has no word of these).
# The second half of the key: a word that makes the line a request rather than a remark. "show
# me", "give me" and "any good" are deliberately not here - they are keys of the boxset and film
# rows, and a word in two keys loses the rarity point the row that was winning on it had, which
# turned "any good shows to watch" into the film list.
MUSIC_START_ASKS = ("get into", "getting into", "start", "starting", "begin", "beginner",
                    "listen", "listening", "recommend", "suggest", "where do i", "where should i",
                    "what should", "which album", "first album", "appreciate", "learn about",
                    "introduce",
                    # "whats the difference between jazz and blues" asks about two genres, not
                    # about where to start with one, and it had no answer at all. A comparing
                    # word in the same ask group lets the one row answer both questions.
                    "difference", "different", "differ", "vs", "versus", "compared")

# The pairs people actually put side by side, and how the two differ. A pair is answered only
# when both names are in the line and a comparing word is too, so "how do i get into jazz" and
# "how do i get into blues" keep their own first record.
MUSIC_PAIRS = (
    (("jazz", "blues"),
     "They are cousins and the blues is the older one. Blues is a form: twelve bars, three "
     "chords, a singer telling you what went wrong, and the words matter more than the playing - "
     "start with Robert Johnson or Muddy Waters. Jazz took that feeling and gave the players room "
     "to invent on top of it, so the same tune is different every night - start with *Kind of "
     "Blue*. If you hear a voice carrying the song it is probably the blues; if you hear an "
     "instrument wander off and come back, it is jazz."),
    (("rap", "hip hop"),
     "Rap is the act - someone talking in time over a beat. Hip hop is the whole culture around "
     "it: the beat, the DJ, the dancing, the graffiti, the way people dress. So every rap record "
     "is hip hop, and a hip hop night can go hours without a rapper. For the words, start with "
     "*Illmatic*; for the sound, *The Miseducation of Lauryn Hill*."),
    (("classical", "opera"),
     "Classical is the whole tradition of written music played by an orchestra; opera is the part "
     "of it that is sung on a stage as a play, with costumes and a plot. An opera is classical "
     "music, but most classical music has nobody singing. Start the orchestral side with "
     "Vivaldi's *Four Seasons* and the sung side with *Carmen*."),
)

# The named card games, with the rules in three sentences: the point of the answer is that
# somebody can start playing, so it is deal, play, win, in that order.
CARD_GAMES = {
    "uno": ("Deal seven cards each and turn one over as the pile. On your turn put down a card "
            "matching the top one in colour or number, or use the action card you are holding: "
            "skip, reverse, and the +2 make the next player miss or draw. You win by getting rid "
            "of every card, and you must call 'uno' when you are down to one - that is the rule "
            "everyone forgets."),
    "solitaire": ("Deal seven columns of one to seven cards, only the top card of each face up, and "
                  "the rest of the pack face down as the stock. Build the columns downwards in "
                  "alternating colours and the four piles upwards from ace in one suit, moving "
                  "cards between columns as they turn over. Turn the stock one card at a time - "
                  "that is the version most people play; the win is all four suits stacked to "
                  "king."),
    "rummy": ("Deal ten cards each and turn one card face up to start the discard pile. On your "
              "turn draw one from the pack or take the top discard, then throw one away, and lay "
              "down any sets of three or more of the same number or runs of three in one suit when "
              "you can. The first player to get rid of every card wins the hand."),
    "snap": ("Deal the whole pack out between you and turn cards face up into the middle one at a "
             "time. When two cards of the same number land on top of each other, the first person "
             "to shout 'snap' and put a hand flat on the pile takes it. Whoever ends up with "
             "every card wins, and small children are much better at this than adults."),
    "go fish": ("Deal five cards each and spread the rest face down in the middle. On your turn ask "
                "one player for a number you already hold, and if they have it you take the card "
                "and ask again; if not they say 'go fish' and you take one from the middle. Lay "
                "down every pair you complete, and the most pairs at the end wins."),
    "blackjack": ("The aim is to get closer to 21 than the dealer without going over: number cards "
                  "count their number, picture cards ten, and an ace is 1 or 11, whichever helps. "
                  "You are dealt two cards and choose hit or stand; the dealer must draw to 16 and "
                  "stop on 17. Over 21 is a bust and you lose at once, which is why 16 is a bad "
                  "hand to be brave on."),
}
CARD_ASKS = ("rules", "how do i play", "how to play", "how do you play", "how does", "deal",
             "score", "scoring", "win", "wins", "set up", "set up", "start", "teach me",
             "explain")

# How an instrument gets in tune, and what to do when it will not stay there. A tuner is the
# whole answer for most people, so the string order is the thing worth writing down.
IN_TUNE = {
    "guitar": ("Clip a tuner on the headstock and take the string order low to high: E, A, D, G, "
               "B, E - the sixth string is the thick one, and the top E is the thin one. Turn the "
               "peg slowly and always come up to the note from below, because slackening down to "
               "it leaves the string ready to slip. Ten seconds a string, and tune every time you "
               "pick it up; guitars move with the room."),
    "bass": ("A clip-on tuner and the string order low to high: E, A, D, G. Turn the peg slowly and "
             "come up to each note from below rather than down onto it. A bass needs tuning less "
             "often than a guitar but goes out if the room changes temperature."),
    "ukulele": ("Clip-on tuner, and the four strings low to high are G, C, E, A - the top G is the "
                "one people get wrong, because on a ukulele it is the higher G, not the lowest "
                "note. Turn the peg in small movements and check the string again after you play a "
                "chord: nylon strings settle slowly and need a week of retuning when they are new."),
    "violin": ("A clip-on tuner and the order G, D, A, E from the lowest string up - and the pegs "
               "are for the big jumps while the fine tuners at the tailpiece do the last bit. Turn "
               "the peg with a little inward pressure so it grips, or it will slip as soon as you "
               "let go."),
    "piano": ("An upright or grand is a job for a tuner, not for you: an annual visit, and twice a "
              "year if it is in a room that gets hot in summer. A digital piano needs nothing. If "
              "one note has gone badly wrong on an acoustic, stop playing it and get the tuner in, "
              "because it is usually a string or a hammer rather than the tuning."),
}
TUNE_ASKS = ("tune", "tuning", "in tune", "out of tune", "stay in tune", "keep in tune",
             "tuned", "sounds wrong", "flat", "sharp", "pitch")

# Why a string buzzes. The order matters: the cheap causes are checked first, because they are
# the ones a person can fix at home this afternoon.
BUZZ_ASKS = ("buzz", "buzzing", "buzzes", "rattles", "rattling", "rattle", "dead note",
             "fret buzz", "sounds tinny", "fret noise")


# "how do i get into birdwatching" is the same ask as "i want a new hobby", one level down:
# the person has picked the thing and wants the first practical step. Every activity in the table
# gets the same shape of answer - where to try it before you buy anything, and the one purchase
# worth making - because that is the step people get stuck on.
ACTIVITY_START = {
    "birdwatching": ("Go out with binoculars borrowed from a friend or a reserve's visitor centre "
                     "first, and start with the birds in your own street: the RSPB and the "
                     "Woodland Trust both have a garden bird sheet for free. A pair of 8x42 "
                     "binoculars for about a hundred pounds is the one purchase, second hand is "
                     "fine, and early morning in spring is when everything is singing."),
    "photography": ("Use the phone you already have for a month and finish one project - a colour, "
                    "a street, one tree every day - before you buy a camera. Then a second-hand "
                    "body with a single 35mm or 50mm lens beats a new camera with two bad ones. "
                    "Learn three things first: light behind you, get closer than feels natural, "
                    "and take ten shots of one thing instead of one shot of ten things."),
    "knitting": ("A pair of 4mm needles and a ball of smooth aran wool is the whole kit, about ten "
                 "pounds, and a plain square is the first project. Watch one slow video of knit "
                 "and purl rather than reading about it, make a dishcloth, and only then start a "
                 "scarf. Wool shops and libraries both run free sit-and-knit groups, which is how "
                 "most people get past the first mess."),
    "pottery": ("Book a one-off taster session before you buy anything: most cities have a studio "
                "that runs two-hour wheel evenings for about thirty pounds. If you like it, a "
                "six-week course teaches more than a year of videos, and hand-building at home "
                "needs only clay, a board and a cheap kiln share from the same studio."),
    "woodworking": ("Start with one joint and one small thing - a box, a stool - using hand tools: a "
                    "hardpoint saw, a chisel, a square and a bench hook will do more than a garage "
                    "of machines. Men's sheds and community workshops hire out bench time and "
                    "somebody to ask, which is worth more than the tools when you are starting."),
    "fishing": ("In England and Wales you need a rod licence first - about seven pounds for a "
                "day, from the Environment Agency online - and then a day ticket at a local club "
                "water and a beginner's float rod set for about forty pounds. Go with somebody "
                "who fishes if you can, and learn one knot (the improved clinch), one rig and one "
                "bait before buying anything else. Go in the morning in summer: fishing is mostly "
                "about being somewhere quiet, so the first trip is a success if you enjoy it."),
    "climbing": ("Go to an indoor wall with hired shoes and a taster session first, about twenty "
                 "pounds, and try bouldering: it needs no partner and the routes are the height of "
                 "a room. Give it three visits before you buy shoes, and only then a pair that fits "
                 "tightly. Outdoors comes later, with somebody who already knows how to belay."),
    "painting": ("Start with acrylics: they dry in minutes, clean up with water, and a starter set "
                 "is under twenty pounds. If it is watercolour you want, the paper decides "
                 "everything - cold-pressed 300gsm and no cheaper - and you work light to dark "
                 "because you cannot paint white back in. Either way, paint the same simple thing "
                 "- one mug, one window - five times instead of five different things, and work "
                 "bigger than feels comfortable with one brush that holds a point."),
    "singing": ("Find a choir rather than a teacher first: most towns have a community choir that "
                "takes people who have never sung, no audition, about five pounds a session. "
                "Singing with others teaches pitch faster than singing alone, and the confidence is "
                "most of it. Take a teacher later if you want to sing on your own."),
    "dancing": ("Pick a class that runs a free taster and go with no partner - most salsa, swing and "
                "ceroc nights rotate partners anyway. Wear smooth soles and give it three weeks "
                "before deciding, because the first lesson is always clumsy. A weekly class beats "
                "a course of videos, since the whole thing is other people's timing."),
    "baking": ("Weigh 500g strong white flour, 7g dried yeast, 10g salt and 350ml warm-not-hot "
               "water: that is the whole recipe, and a scale is the only kit you need. Knead ten "
               "minutes, leave it two hours somewhere warm until it has doubled, shape it and bake "
               "it hot. Then bake that same loaf five times rather than five different things - the "
               "first is usually dense and the fifth is usually good, so the only way to fail is "
               "to stop at the first."),
    "sewing": ("A basic machine with a straight stitch and a zigzag is all anyone needs, and a "
               "second-hand one from a repair shop costs less than a new cheap one. Start on "
               "scraps, not clothes: stitch straight lines, then a cushion cover, then take in a "
               "hem on something you do not mind ruining. A local sewing shop's two-hour beginner "
               "class is worth more than a video, because someone sets the tension for you."),
    "board games": ("Go to a board-game cafe or a club night once before buying a box: most of them "
                    "have a shelf and someone who will teach a game in ten minutes. Then buy one "
                    "small game for the people you actually play with, not the one with the best "
                    "reviews. Codenames, Patchwork and Ticket to Ride cover most groups."),
    # The two practices people take up at home with nothing to buy but a mat, and a gap in this
    # table: "how do i start yoga" and "how do i start pilates" fell through to the greeting,
    # which shrugged at two of the questions a person asks most here. A class is the first step
    # for both, because a teacher has to see your back. Meditation is not here: its own row
    # answers "how do i start meditating" with the sit itself, and a table entry in this one
    # replaced that answer with a thinner one.
    "yoga": ("Book a beginners' class rather than a video: most studios run a drop-in hatha or "
             "beginner class for about ten to fifteen pounds, and a teacher can see your back, "
             "which a video cannot. Wear something you can move in and borrow a mat - a cheap "
             "6mm mat is the only thing worth buying - and go twice a week for a month before "
             "you judge it. Skip any pose that hurts and tell the teacher about a bad back or "
             "neck before you start."),
    "pilates": ("Start with a beginner mat class, not the reformer: a mat class is about ten to "
                "fifteen pounds, needs only a mat and a cushion, and a teacher who watches you is "
                "the point of it. The one thing to learn first is the breath - wide into the ribs "
                "on the effort, with the belly gently held, never sucked in hard. Twice a week "
                "for a month, and tell the teacher about any back or neck trouble beforehand."),
}
ACTIVITY_ASKS = ("get into", "getting into", "start", "starting", "begin", "beginner", "take up",
                 "taking up", "how do i", "where do i", "any tips", "learn", "try",
                 # The plain admission, which is how most people say it and which used to fall
                 # through to the listening reply: "i cant sing", "i cant bake", "i cant dance".
                 "cant", "can't", "cannot", "never learnt", "never learned", "never tried")


# The verbs in ACTIVITY_VERBS are jobs as well as hobbies, and it is the thing after the verb that
# decides it. "How do i paint a shed" is a fence to treat, "how do i paint over damp" is water to
# find first, and "how do i paint my kitchen cupboards" is a sanding job - the acrylics starter set
# is the answer to a different question, and it was given to all of them. A surface, or a fault on
# one, is the tell: no line that is asking how to begin painting names a shed.
_PAINTED_SURFACES = frozenset((
    "shed", "sheds", "fence", "fences", "wall", "walls", "door", "doors", "ceiling", "ceilings",
    "cupboard", "cupboards", "cabinet", "cabinets", "tile", "tiles", "radiator", "radiators",
    "bench", "benches", "gate", "gates", "garage", "garages", "greenhouse", "greenhouses",
    "wardrobe", "wardrobes", "skirting", "banister", "banisters", "stairs", "floor", "floors",
    "floorboards", "decking", "deck", "windowsill", "windowsills", "woodwork", "wallpaper",
    # A hall, a landing and a corridor are not in this list: no row answers a hall yet, and
    # standing the hobby row down without a row behind it turns the acrylics card into a punt,
    # which is worse than a wrong answer. They keep the hobby card until the hall has a row.
    "kitchen", "bathroom", "bedroom", "shelf", "shelves",
    "table", "tables", "chair", "chairs", "toy", "toys",
    # The rest of the pieces and rooms a person names when they mean a job rather than a hobby.
    # Every one of these stood the hobby row down and then had no row behind it, so the line was
    # a punt (snug-parrot on #7159); each now reaches the sanding, priming or shopping-list row.
    "stool", "stools", "desk", "desks", "bed", "beds", "cot", "cots", "crib", "cribs",
    "toy box", "toybox", "chest", "trunk", "drawers", "dressing table", "bedside table",
    "picture frame", "photo frame", "mirror frame", "unit", "units", "kitchen unit",
    "kitchen units", "front room", "living room", "lounge", "dining room", "corridor",
    "spare room", "nursery", "staircase", "stair treads", "steps",
    # the one word that carries the phrase: a picture frame is a frame, and the front room is a
    # room, so the hobby row stands down on the token as well as on the phrase.
    "frame", "frames", "room", "rooms"))
_PAINTED_FAULTS = frozenset((
    "mould", "mold", "mildew", "damp", "creosote", "rust", "peeling", "flaking", "blistering",
    # Paint that is already there to be dealt with - stripped, removed, or taken to the tip - is
    # a job too, and these two lines were punts on main's own red tests: "how do i strip old
    # paint" and "where do i take old paint" were both handed the acrylics starter set.
    "stripper", "stripping", "strip", "strips"))
# The same thing said in two words, which is how people say paint that is already on something.
_PAINTED_PHRASES = (
    "old paint", "paint stripper", "leftover paint", "left over paint", "spare paint",
    "tin of paint", "tins of paint", "paint tin", "paint tins", "unused paint", "half a tin")


# Only the painting verbs take a surface this way; "i cant sing in my kitchen" is still the choir.
_PAINT_VERBS = frozenset(("paint", "paints", "painted", "painting", "repaint", "repaints",
                          "repainting", "varnish", "varnishing"))


# The hobby of baking is about baked goods, and "bake" is also the verb for putting anything at all
# in the oven: "how do i bake a potato", "how do i bake an aubergine", "how do i bake a chicken"
# and "how do i bake a beetroot" were all given the sourdough-first answer, because "bake" is a
# verb in the table below and a `how do i` in front of it is all this row asks. What tells the two
# apart is whether the verb has a thing after it: "i cant bake" and "how do i start baking" name
# no thing and are the hobby, while "bake a potato" names dinner and the kitchen answers it. Bread
# and cakes are the same reading twice over - their own words are in the avoid list below.
_A_THING_IS_BEING_BAKED = re.compile(
    r"\b(?:bake|bakes|baked|baking)\s+"
    r"(?:a|an|the|my|our|your|his|her|their|some|these|those|two|three|four|half)\s+"
    r"([a-z][a-z'-]*)")
# The words that can follow the verb there and name nothing to put in the oven: "how do i get into
# baking a bit more", "how do i bake a lot at once", "how do i bake a good loaf". The last is a
# loaf and is left alone - "loaf" is in the avoid list below - so only a quantity word stands here.
_NOTHING_TO_BAKE = frozenset((
    "bit", "bits", "lot", "lots", "few", "couple", "little", "while", "moment", "time",
    "times", "start", "living", "change", "break", "go", "try", "batch", "whole", "good",
    "better", "decent", "simple", "basic", "proper", "quick", "easy", "beginning",
))


def _a_thing_is_being_baked(text):
    """Whether the line puts a thing in the oven rather than asking how to take baking up."""
    for hit in _A_THING_IS_BEING_BAKED.finditer(text):
        if hit.group(1) not in _NOTHING_TO_BAKE:
            return True
    return False


def _a_surface_is_being_painted(words, padded):
    """Whether the painting in the line is a job on a thing rather than taking the hobby up."""
    if not (words & _PAINT_VERBS):
        return False
    if words & _PAINTED_SURFACES or words & _PAINTED_FAULTS:
        return True
    # "old paint" and "a tin of paint" are two words each, and a set of single tokens can never
    # hold them: "where do i take old paint" kept the starter set for want of a phrase.
    return any(phrase in padded for phrase in _PAINTED_PHRASES)


def _activity_start(memory, understood):
    """The first practical step into the one activity the line names."""
    # A dish named in the line is the kitchen's, even when its name is a verb at the same time:
    # "how do i make fish pie" was answered with a rod licence and a day ticket, because "fish"
    # is in the verb table below and a `how do i` in front of it is all this row asks. The recipe
    # table is the list of dishes the kitchen knows by name, so a line naming one has a subject
    # of its own, and the first step into a hobby is not the answer to a method question.
    from .cooking import names_a_dish  # circular otherwise
    if names_a_dish(understood):
        return None
    text = ((understood.get("clean") or "") + " " + (understood.get("norm_text") or "")).lower()
    if _a_thing_is_being_baked(text):
        # "how do i bake a potato" is the potato's question, not a first step into baking: the
        # verb is shared by every food there is and the noun after it is what tells them apart.
        return None
    # Whole words, not substrings: "sing" sits inside "using" and "bake" inside "baked beans",
    # so a plain `in` handed an oven question a choir, which is how this list used to be read.
    words = set(re.findall(r"[a-z']+", text))
    padded = " %s " % " ".join(re.findall(r"[a-z']+", text))
    if _a_surface_is_being_painted(words, padded):
        # "how do i paint a shed" is the shed row's question, not a first step into painting: the
        # verb is shared and the noun after it is what tells the two apart.
        return None
    # The table's own order, so a row added to it is a row this answers: the names used to be
    # written out here as well, and an activity in the table with no line in this list was a
    # reply function that could never reach it.
    for name in ACTIVITY_START:
        if (" %s " % name) in padded:
            return ACTIVITY_START[name]
    # The plain verb, which is how a person says it when they are admitting they cannot do the
    # thing at all: "i cant sing", "i cant bake", "i want to learn to sew". Except "paint", which
    # is a decorating verb as often as a craft one: "paint a window frame", "paint the shed" and
    # "paint a door" are jobs on the thing named, and the house has an answer for each. So the
    # verb only starts the craft when the line is not about painting one of those things.
    for name in ACTIVITY_VERBS:
        if name in words:
            if name in _FISH_VERBS and _FISH_IS_DINNER.search(text):
                # "how do i stop fish falling apart" is the frying pan, not a day ticket: the
                # verb "fish" is in the table, and a `how do i` in front of it was all this row
                # asked. A fish being cooked is the kitchen's line.
                return None
            if name in _PAINT_VERBS and _paints_a_thing(text):
                return None
            return ACTIVITY_START[ACTIVITY_VERBS[name]]
    # the same first step under the other name people give it.
    for name, real in ACTIVITY_OTHER_NAMES.items():
        if (" %s " % name) in padded:
            return ACTIVITY_START[real]
    return None


# "Fish" is an activity and a dinner: the day ticket is the answer to one and the pan to the
# other, and the kitchen words are what tell them apart.
_FISH_VERBS = frozenset(("fish", "fishing", "fished"))
_FISH_IS_DINNER = re.compile(
    r"\b(?:cook|cooks|cooked|cooking|fry|fries|fried|frying|bake|baked|baking|poach|poached|"
    r"steam|steamed|grill|grilled|oven|pan|pan[s]?|skillet|dinner|tea|supper|lunch|recipe|"
    r"falls? apart|falling apart|breaks? up|breaking up|to bits|crumbles?)\b")


# The verb that is two jobs at once. Painting a window, a door or a shed is decorators' work with
# an answer of its own in the house domain, and "start with acrylics" was the reply to all of them.
_PAINT_VERBS = frozenset(("paint", "paints", "painting", "painted", "repaint", "repainting"))
_PAINTED_THINGS = re.compile(
    r"\b(?:paint|paints|painting|painted|repaint|repainting)\s+(?:a|an|the|my|our|his|her|their|"
    r"this|that|these|those|its|it)\s+(?:[a-z]+\s+)?(?:window|windows|sash|casement|door|doors|"
    r"wall|walls|ceiling|ceilings|shed|sheds|fence|fences|gate|garage|radiator|radiators|"
    r"skirting|trim|woodwork|wood|cupboard|cupboards|cabinets|cabinet|wardrobe|wardrobes|"
    r"table|tables|chair|chairs|furniture|floor|floors|floorboards|banister|banisters|"
    r"frame|frames|sill|sills|panel|panels|front door|garage door|back door|french doors|"
    r"patio|deck|decking\b)")


# And the same word is the stuff in the tin, which is not an activity at all: "how do i get rid of
# paint" and "where do i take old paint" were both told to start with acrylics, which is an answer
# to a question nobody asked. What gives the noun away is the word next to it - a determiner like
# "old" or "leftover", a tin, or a verb that gets rid of it or prices it.
_PAINT_AS_A_THING = re.compile(
    r"\b(?:get rid of|dispose of|throw away|throwing away|throw out|bin|recycle|take|taking|"
    r"old|leftover|left over|spare|unused|surplus|half a tin|half used|" 
    r"tin of|tins of|paint tin|paint tins|tin|tins|pot of|tube of|" 
    r"how much|how many|much does|cost of|price of|litres|liters|gallons|coverage|" 
    r"which|what kind of|best|cheapest|store|storing|keep|keeping|freeze|frozen|skin on|"
    r"goes off|gone off|gone hard|separated)\s+(?:[a-z]+\s+){0,2}paint\b")


# And the third reading of the word is the decorating question, not the craft one: "how do i
# choose a paint colour", "how do i pick a paint colour" and "how do i choose a paint colour for
# my living room" were all told to start with acrylics. Nothing in them names a thing to paint or
# a tin, so the two tests above missed them; what marks them is the word colour sitting next to
# paint, or the scheme the colour is for.
_PAINT_COLOURS = re.compile(
    r"\bpaint(?:s|ed|ing)?\b(?:\s+[a-z']+){0,2}\s+colou?rs?\b"
    r"|\bcolou?r(?:s|ed)?\b(?:\s+[a-z']+){0,2}\s+paint(?:s|ed|ing)?\b"
    r"|\bcolou?r\s+scheme\b|\bpaint\s+scheme\b|\bcolou?r\s+palette\b")


def _paints_a_thing(text):
    """True when the paint verb is being applied to a thing, names the paint in the tin, or is
    the decorating question about a colour."""
    return bool(_PAINTED_THINGS.search(text) or _PAINT_AS_A_THING.search(text)
                or _PAINT_COLOURS.search(text))


# The bare verb to the activity it starts: "i cant dance" names dancing and nothing else.
ACTIVITY_VERBS = {
    "sing": "singing", "sings": "singing", "dance": "dancing", "dances": "dancing",
    "bake": "baking", "bakes": "baking", "knit": "knitting", "knits": "knitting",
    "paint": "painting", "paints": "painting", "sew": "sewing", "sews": "sewing",
    "photograph": "photography", "pottery": "pottery", "fish": "fishing", "climb": "climbing",
}


# The second name for an activity in the table above: "how do i join a choir" is the singing
# answer, and an allotment is where the gardening answer starts.
ACTIVITY_OTHER_NAMES = {
    "choir": "singing", "singing lessons": "singing", "choir practice": "singing",
    "watercolour": "painting", "watercolours": "painting", "watercolors": "painting",
    "acrylics": "painting", "acrylic paint": "painting",
    "fly fishing": "fishing", "sea fishing": "fishing", "bouldering": "climbing",
}


# Half the genre names are ordinary words too, so the ask alone does not settle which one the line
# means: "how do i get into metal" is the music, "how do i start house hunting" is the building.
# A genre standing on its own is the music; a genre with a word after it that no music sentence
# would put there, or a "a/the/my" in front of it, is the ordinary word, and the other rows keep
# the answer. The list of words that do go after a genre is what stops the rule taking "metal
# guitar" and "country music" away.
ORDINARY_GENRES = ("house", "country", "soul", "metal", "folk", "gospel", "punk", "indie")
# The other kinds of music that follow a genre in a sentence: "how do i get into punk rock" is
# the music twice over, and without these the row read "rock" as an ordinary word after "punk"
# and stood itself down. Longest first is not needed - only the first word after the genre is
# read - but the two-word kinds are here because "drum and bass" and "hip hop" are said whole.
MUSIC_KINDS_AFTER = ("rock", "pop", "ska", "reggae", "techno", "disco", "grime", "hip hop",
                     "hip-hop", "classical", "opera", "rap", "jazz", "blues", "soul", "metal",
                     "punk", "house", "country", "folk", "indie", "gospel", "dance", "electronic",
                     "edm", "r&b", "rnb", "swing", "bluegrass", "ambient", "trance", "dubstep",
                     "drum and bass", "dnb", "hardcore", "shoegaze", "motown", "afrobeat")
GENRE_WORDS_AFTER = MUSIC_KINDS_AFTER + (
                     "music", "dj", "djs", "track", "tracks", "album", "albums", "mix", "mixes",
                     "tune", "tunes", "band", "bands", "sound", "sounds", "scene", "song",
                     "songs", "record", "records", "remix", "label", "vinyl", "era",
                     "compilation", "classics", "classic", "genre", "guitar", "piano", "singing",
                     "vocals", "drums", "artists", "artist", "singers", "singer", "history",
                     "set", "sets", "festival", "gig", "gigs", "club", "clubs", "instruments",
                     "legends", "standards", "pioneers", "era")
# An article or a possessive in front of the name settles it on its own: "a house or a flat" is
# two homes. A quantity word does not - "recommend some house" is a person asking for music, and
# `some`, `any`, `every` and `one` sat in this list and turned four recommendation lines into a
# hedge (wide-pineapple) - so they are left out and the word after the name decides.
GENRE_NAMES_BEFORE = ("a", "an", "the", "my", "our", "your", "his", "her", "their", "this",
                      "that", "these", "those", "another")
# A word after the name that says nothing about the thing itself: "any house you'd recommend" is
# a request for music, and read as a noun the pronoun would have made it a property question.
GENRE_NOT_DESCRIBED_BY = ("you", "youd", "youll", "youve", "your", "i", "im", "id", "ill",
                          "we", "weve", "wed", "they", "theyd", "he", "she", "it", "could",
                          "would", "should", "can", "will", "shall", "might", "must", "please",
                          "recommend", "suggest", "thanks", "thank", "then", "too", "even")


def _an_ordinary_word(name, text):
    """Is this the everyday word, and not the kind of music?"""
    if name not in ORDINARY_GENRES:
        return False
    for hit in re.finditer(r"\b" + name + r"\b", text):
        after = text[hit.end():].split()
        follows = after[0].strip(",.!?;:") if after else ""
        before = text[:hit.start()].split()
        # a music noun after the name is the music, whatever word is in front of it: "recommend
        # a house track" and "a house tune" are asks for the sound, and the article in front of
        # them was read first and stood the row down (emerald-bat, polite-compass).
        if follows in GENRE_WORDS_AFTER:
            continue
        # then a determiner in front of the name settles it on its own: "a house or a flat" is a
        # choice between two homes (the word after the name there is "or", not a music noun).
        if before and before[-1].strip(",.!?;:") in GENRE_NAMES_BEFORE:
            return True
        if follows in ("and", "or", "vs", "versus", "is") or follows in GENRE_NOT_DESCRIBED_BY:
            continue
        if follows:
            return True
    return False


def _genre_start(memory, understood):
    """Where to start with the one kind of music the line names."""
    text = ((understood.get("clean") or "") + " " + (understood.get("norm_text") or "")).lower()
    if "countryside" in text or "village" in text or "walk in the country" in text:
        return None
    # two names and a comparing word is the difference question, not a start-with one
    comparing = any(w in text for w in ("difference", "different", "differ", " vs ", "versus",
                                        "compared", "compare"))
    if comparing:
        for pair, difference in MUSIC_PAIRS:
            if all(name in text for name in pair):
                return difference
    # the most specific name wins: "hip hop" before "hop", "house music" before "house"
    for name in ("hip hop", "k-pop", "kpop", "r&b", "house music", "dance music", "electronic",
                 "techno", "classical", "country", "metal", "motown", "soul", "blues", "folk",
                 "reggae", "opera", "punk", "indie", "gospel", "disco", "jazz", "rap", "house"):
        if name in GENRE_START and name in text:
            # the words the person typed, once: the text here is the line twice over, and the
            # end of the first copy is not the end of the line
            typed = (understood.get("clean") or understood.get("norm_text") or text).lower()
            if _an_ordinary_word(name, typed):
                return None
            return GENRE_START[name]
    return None


def _card_game(memory, understood):
    """The rules of the one card game the line names."""
    text = ((understood.get("clean") or "") + " " + (understood.get("norm_text") or "")).lower()
    # the name in the line, and the game in the table that answers it: pontoon and twenty-one
    # are blackjack, and patience is solitaire.
    for name, game in (("uno", "uno"), ("solitaire", "solitaire"), ("patience", "solitaire"),
                       ("rummy", "rummy"), ("snap", "snap"), ("go fish", "go fish"),
                       ("blackjack", "blackjack"), ("pontoon", "blackjack"),
                       ("twenty one", "blackjack")):
        if name in text:
            return CARD_GAMES.get(game)
    return None


def _in_tune(memory, understood):
    """How to tune the instrument the line names, or what to do when it will not hold."""
    text = ((understood.get("clean") or "") + " " + (understood.get("norm_text") or "")).lower()
    if "piano" in text or "keyboard" in text:
        return IN_TUNE["piano"]
    for name in ("guitar", "bass", "ukulele", "violin", "fiddle", "cello", "banjo", "mandolin"):
        if name in text:
            if name in ("bass",):
                return IN_TUNE["bass"]
            if name in ("violin", "fiddle", "cello"):
                return IN_TUNE["violin"]
            return IN_TUNE["guitar" if name in ("banjo", "mandolin") else name]
    return None


def _buzz(memory, understood):
    """A string that buzzes, in the order of the things a person can check at home."""
    text = ((understood.get("clean") or "") + " " + (understood.get("norm_text") or "")).lower()
    return ("One buzzing string is usually that string: old, kinked, or sitting too low in its "
            "nut, so change it first and see. Buzz that follows one fret up and down the neck is "
            "that fret or the neck; buzz on every note is usually how hard you are picking, so try "
            "a lighter touch and press just behind the fret rather than on top of it. If it still "
            "rattles in the same place with a new string, the action is too low or the neck has "
            "moved - a shop sets that up for about forty pounds, and it is worth it, because no "
            "amount of technique fixes a guitar set up badly.")


def _worth_it(memory, understood):
    """A view on the one work the line names.

    People ask this about something they are about to spend an evening on, so the answer is a
    yes or a no with the reason, never a list of other things: "is it worth watching the wire"
    is not "what should I watch". Only a work in the table gets here; one nobody here knows is
    the other entry's business, and a report of something already seen wants to talk.
    """
    text = (understood.get("clean") or understood.get("norm_text") or "").lower()
    if _about_a_person(text) or _a_place_not_a_work(text):
        return None
    title = _work_named(text)
    return VIEWS[title] if title else None


def _worth_it_unnamed(memory, understood):
    """An honest line about a work the table does not know, or about one only called "it".

    The table cannot hold every film and book, and inventing a verdict is worse than saying
    which of the two this is, so the line names the work when the ask named it and always
    offers a way to judge it. A pick of anything ("whats a good film"), a gift, tonight's
    telly and a question about whether reading is good for you all have their own entries.
    """
    text = (understood.get("clean") or understood.get("norm_text") or "").lower()
    if _about_a_person(text) or _work_named(text) or _a_place_not_a_work(text):
        return None
    if any(word in text for word in NOT_A_VERDICT):
        return None
    if A_PERSON_TO_CONSULT.search(text):
        return None
    if not any(phrase in text for phrase in JUDGE_ASKS):
        return None
    named = _named_work(text)
    if named:
        return ("I don't know *%s* well enough to call it honestly. Tell me what you liked about "
                "the last thing you enjoyed and I'll say whether it's that kind." % named)
    return ("Not one I can call honestly, sorry. Name the last thing you enjoyed and I'll say "
            "whether this one is that kind of thing.")


def _named_work(text):
    """The work a judging line names, as it should be written, or "".

    The title sits before the ask in one shape ("is oppenheimer worth watching") and after the
    verb in the other ("should i watch the wire"), so both are read; the words that make the
    line an ask (worth, good, any good) and the place and time words are cut off, because
    "is oppenheimer worth watching" would otherwise name a film called *Is Oppenheimer Worth
    Watching*.
    """
    # A possessive ends the title: "is it worth watching my watch get repaired" is about the
    # thing on the person's wrist, and no work is called *My Watch Get Repaired*.
    cuts = ("worth", "any good", "good", "boring", "like", "as good", "better", "any cop",
            "in the", "or", "on", "at", "tonight", "with", "because", "before", "after", "if",
            "but", "for me", "or not", "yet", "then",
            "my", "your", "his", "her", "our", "their")
    patterns = (r"\b(?:is|are|was)\s+((?:the\s+|this\s+|that\s+)?[a-z0-9'&: -]{2,40})",
                r"\b(?:watch|watching|read|reading|see|play)\s+((?:the\s+|a\s+)?"
                r"[a-z0-9'&: -]{2,40})")
    for pattern in patterns:
        found = re.search(pattern, text)
        if not found:
            continue
        title = found.group(1)
        for cut in cuts:
            title = re.split(r"\b" + re.escape(cut) + r"\b", title)[0]
        title = title.strip(" .?!,-\t")
        if not title or title in ("it", "this", "that", "something", "anything", "one",
                                 "worth", "the", "a", "an"):
            continue
        return _display(title)


def _table_pick(text):
    """The pick for the title this line really names, or "" for a line that names none of ours.

    Both the pick-that-follows row and the film-like row read the same table, so both ask this
    one question: a title that is also a plain phrase has to be a work in the line as well.
    """
    about_a_work = (any(word in text for word in WORK_EVIDENCE)
                    or any(phrase in text for phrase in NEXT_EVIDENCE))
    for title, reply in FILM_MATCHES:
        # The title has to be a word of its own: "the bear" sits inside "the beard" and "the
        # wire" inside "the wireless", and neither of those is a programme.
        if not re.search(r"\b" + re.escape(title) + r"\b", text):
            continue
        if title in PLAIN_TITLES:
            if any(phrase in text for phrase in PLAIN_SENSE[title]):
                continue
            if not about_a_work:
                continue
        return reply
    return ""


def _after_named(memory, understood):
    """The pick that follows a title the line names, or "" so a lower entry gets the turn."""
    text = ((understood.get("clean") or "") + " " + (understood.get("norm_text") or "")).lower()
    return _table_pick(text)


# A book about the thing itself, not a novel: "whats a good book about gardening", "good books
# for beginners at chess", "a book on learning to draw". The pick is read off the subject the
# line names, with the same names as ACTIVITY_START where the two overlap, so one phrase list
# answers "how do i get into fishing" and "a book about fishing". A subject we have no pick for
# stands the line down, because handing somebody a novel when they asked about gardening
# answers a different question. The exchange is the same in every row: one title, why it is
# that one, and the second title or the kit if there is one.
SUBJECT_BOOKS = {
    "psychology": ("*Thinking, Fast and Slow* by Daniel Kahneman is the one that changes how you "
                   "see your own decisions, though it is a long read; *The Man Who Mistook His "
                   "Wife for a Hat* by Oliver Sacks is the shorter, stranger way in."),
    "philosophy": ("*Think* by Simon Blackburn is written for someone who has never read any: a "
                   "chapter a question, no jargon. *Sophie's World* by Jostein Gaarder tells the "
                   "whole history of it as a novel if you want the story instead."),
    "economics": ("*The Undercover Economist* by Tim Harford explains prices, markets and why "
                  "things cost what they do without a single equation. *The Armchair Economist* "
                  "by Steven Landsburg is the more argumentative one."),
    "science": ("*A Short History of Nearly Everything* by Bill Bryson is the one to start with: "
                "how we know what we know, and funny throughout. *The Selfish Gene* by Richard "
                "Dawkins if it is evolution you want."),
    "climate": ("*How to Avoid a Climate Disaster* by Bill Gates is the plainest account of where "
                "the emissions actually come from and what would fix each one, without the "
                "gloom. *The Uninhabitable Earth* by David Wallace-Wells is the bleak one."),
    "maths": ("*Alex's Adventures in Numberland* by Alex Bellos is maths as stories about people "
              "and puzzles, so nothing feels like homework. *How Not to Be Wrong* by Jordan "
              "Ellenberg is the one about using it to think."),
    "politics": ("*How Westminster Works... and Why It Doesn't* by Ian Dunt is the short angry "
                 "guide to how British government actually runs. *The Prince* by Machiavelli if "
                 "you want the old one people still quote."),
    "poetry": ("*Staying Alive* edited by Neil Astley is the anthology to start with: modern poems "
               "in English, sorted by what they are about rather than by poet. Read one a night "
               "and skip anything that does not land."),
    "language": ("*The Language Instinct* by Steven Pinker is the readable one on how language "
                 "works in the head, and *Mother Tongue* by Bill Bryson is the fun history of "
                 "English if that is the half you want."),
    "gardening": ("*How to Garden* (DK) is the beginner's standard: a photograph for every job, "
                  "month by month, and no assumed knowledge. *The Allotment Book* by Andi Clevely "
                  "if it is a plot rather than a border."),
    "chess": ("*Bobby Fischer Teaches Chess* is all positions and no theory, so you learn by "
              "doing, and free games online afterwards make it stick. *Chess for Dummies* if you "
              "want the openings named as well."),
    "knitting": ("*Stitch 'n Bitch* by Debbie Stoller: cast on, knit, purl, then patterns you can "
                 "actually finish. A pair of 4mm needles and a ball of aran wool is the whole kit "
                 "and it costs about ten pounds."),
    "crochet": ("*The Happy Hooker* by Debbie Stoller is the crochet one from the same series: the "
                "stitches step by step, then small things worth making. One 4mm hook and a ball of "
                "aran wool to start."),
    "sewing": ("*The Sewing Book* by Alison Smith (DK) photographs every technique from a hem to a "
               "zip, so it stays useful for years. Practise on an old pillowcase rather than good "
               "fabric."),
    "drawing": ("*Drawing on the Right Side of the Brain* by Betty Edwards, because beginners draw "
                "what they think is there instead of what is, which is the thing the exercises "
                "fix. A 2B pencil and cheap paper is the kit."),
    "painting": ("*Watercolour for the Absolute Beginner* by Matthew Palmer: three washes and you "
                 "have painted something, with nothing assumed. Cold-pressed 300gsm paper decides "
                 "more than the paints do, and acrylics are the easier way in."),
    "photography": ("*Understanding Exposure* by Bryan Peterson, since exposure is what separates a "
                    "snapshot from a photograph and the book works on any camera, phone included."),
    "guitar": ("*Hal Leonard Guitar Method, Book 1*: chords and songs from the first pages, with the "
               "audio included. Any cheap acoustic plays well enough to learn on."),
    "piano": ("*Alfred's Basic Adult Piano Course, Book 1* starts at the very beginning and has "
              "both hands together within a few pages. A 61-key keyboard is enough to learn on."),
    "baking": ("*Flour Water Salt Yeast* by Ken Forkish for bread: four ingredients, a schedule, and "
               "a loaf that tastes like a bakery's. *The Great British Bake Off: How to Bake* if it "
               "is cakes and pastry you want."),
    "cooking": ("*Salt, Fat, Acid, Heat* by Samin Nosrat teaches why a dish works, so you stop "
                "following recipes. *Delia's Complete Cookery Course* if you would rather be told "
                "exactly what to do."),
    "running": ("*Run Walk Run* by Jeff Galloway: walking breaks get a beginner to 5k without the "
                "injuries that stop people. Get shoes fitted at a running shop rather than bought "
                "from a supermarket."),
    "yoga": ("*Light on Yoga* by B.K.S. Iyengar is the classic reference, but go to two or three "
             "classes first, because a book cannot see your back."),
    "dog training": ("*Perfect Puppy* by Gwen Bailey covers the first weeks, house training and the "
                     "five things to teach first. *The Dog Listener* by Jan Fennell if the dog is "
                     "out of puppyhood already."),
    "birdwatching": ("*The RSPB Pocket Guide to British Birds* names what you are looking at, and a "
                     "pair of 8x42 binoculars is the one purchase: second hand is fine, and the "
                     "garden birds are the place to start."),
    "astronomy": ("*Turn Left at Orion* by Guy Consolmagno: what to look for first from a back "
                  "garden, and where it is. Binoculars find most of it, so no telescope yet."),
    "coding": ("*Python Crash Course* by Eric Matthes, which has you build a game and a small web "
               "app instead of reading about variables. Free tutorials afterwards are fine."),
    "investing": ("*Smarter Investing* by Tim Hale: the boring index-fund argument, with the numbers "
                  "and the costs. Nothing else is needed until that makes sense."),
    "money": ("*Money: A User's Guide* by Laura Whateley takes bills, debt, pensions and savings in "
              "the order they matter for somebody in the UK."),
    "history": ("*A Little History of the World* by E. H. Gombrich: short chapters, written for a "
                "child but never childish, and it gives you the map everything else hangs on."),
    "wine": ("*Wine Folly* by Madeline Puckette shows the grapes and regions as pictures, which is "
             "how they stick, and the tasting words come after."),
    "woodworking": ("*Woodworking Basics* by Peter Korn takes one joint at a time with hand tools, "
                    "which is the right order. A hardpoint saw, a chisel, a square and a bench hook "
                    "do more than a garage of machines."),
    "fishing": ("*Fishing for Dummies* covers the rig, the bait and the knots for coarse fishing, and "
                "a day ticket at a club water is the way to try it. Rod licence first if you are in "
                "England or Wales."),
    "climbing": ("*How to Rock Climb!* by John Long is the standard for the basics, ropes and knots. "
                 "Go to an indoor wall with hired shoes and try bouldering first, since it needs no "
                 "partner."),
    "diy": ("*The Reader's Digest Complete DIY Manual* covers the jobs in a house from a shelf to a "
            "radiator, and a Haynes manual for your own model if it is the car."),
    "car": ("A Haynes manual for your exact model, since the engine has to match, plus a socket set. "
            "That covers servicing, brakes and most of an MOT."),
}
# The words people use for each subject. Order does not matter here: the longest phrase that
# appears in the line wins, so "dog training" beats "dog".
SUBJECT_BOOK_NAMES = {
    # The subjects people ask a book for and there was no pick for: "a book about psychology"
    # and "a good book about philosophy" were a shrug, and the hobby list above is all doing.
    "psychology": "psychology", "the mind": "psychology", "the brain": "psychology",
    "neuroscience": "psychology", "human behaviour": "psychology", "human behavior": "psychology",
    "philosophy": "philosophy", "philosophers": "philosophy",
    "economics": "economics", "the economy": "economics",
    "science": "science", "physics": "science", "chemistry": "science",
    "biology": "science", "evolution": "science", "the universe": "science",
    "climate change": "climate", "climate": "climate", "the climate": "climate",
    "maths": "maths", "mathematics": "maths", "numbers": "maths",
    "politics": "politics", "government": "politics",
    "poetry": "poetry", "poems": "poetry",
    "language": "language", "linguistics": "language", "grammar": "language",
    "gardening": "gardening", "allotment": "gardening", "allotments": "gardening",
    "grow your own": "gardening", "vegetable patch": "gardening", "veg patch": "gardening",
    "vegetable garden": "gardening", "garden": "gardening",
    "chess": "chess",
    "knitting": "knitting", "knit": "knitting",
    "crochet": "crochet",
    "sewing": "sewing", "sew": "sewing", "dressmaking": "sewing",
    "drawing": "drawing", "draw": "drawing", "sketching": "drawing", "sketch": "drawing",
    "watercolour": "painting", "watercolours": "painting", "watercolor": "painting",
    "painting": "painting", "paint": "painting", "acrylics": "painting",
    "photography": "photography",
    "guitar": "guitar",
    "piano": "piano", "keyboard": "piano",
    "bread": "baking", "breadmaking": "baking", "baking": "baking", "bake": "baking",
    "cooking": "cooking", "cook": "cooking",
    "running": "running", "run": "running", "jogging": "running",
    "yoga": "yoga",
    "dog training": "dog training", "training a puppy": "dog training",
    "puppy training": "dog training",
    "birdwatching": "birdwatching", "bird watching": "birdwatching", "birds": "birdwatching",
    "astronomy": "astronomy", "stargazing": "astronomy", "the stars": "astronomy",
    "coding": "coding", "programming": "coding", "python": "coding", "javascript": "coding",
    "code": "coding", "web design": "coding",
    "investing": "investing", "investment": "investing", "index funds": "investing",
    "stocks and shares": "investing",
    "money": "money", "budgeting": "money", "personal finance": "money",
    "history": "history",
    "wine": "wine",
    "woodworking": "woodworking", "carpentry": "woodworking", "woodwork": "woodworking",
    "fishing": "fishing", "fly fishing": "fishing", "sea fishing": "fishing",
    "climbing": "climbing", "bouldering": "climbing",
    "diy": "diy", "home repairs": "diy", "plumbing": "diy", "tiling": "diy",
    "car maintenance": "car", "servicing my car": "car", "car": "car",
}
# Subjects people ask for a book about that we have no pick for. The line stands down rather
# than getting a novel, and another module or an honest "I don't know" takes the turn.
SUBJECT_BOOK_UNCOVERED = ("pottery", "ceramics", "singing", "dancing", "board games",
                          "poker", "bridge", "golf", "tennis", "beekeeping", "calligraphy",
                          "horse riding", "skiing", "snowboarding", "surfing", "boxing",
                          "martial arts", "meditation", "wild swimming", "swimming", "snooker",
                          "darts", "genealogy", "family history", "astrology", "tarot",
                          "public speaking", "origami", "embroidery", "quilting", "rug making",
                          "home brewing", "beer brewing", "foraging", "mushrooms", "mycology",
                          "bees", "chickens", "keeping chickens", "allotmenteering",
                          "second world war", "world war", "first world war", "ww2", "ww1",
                          "war", "wars")
_SUBJECT_BOOK_ORDER = sorted(SUBJECT_BOOK_NAMES, key=len, reverse=True)
_SUBJECT_UNCOVERED_ORDER = sorted(SUBJECT_BOOK_UNCOVERED, key=len, reverse=True)
# The words that introduce the subject, so a line that merely mentions a car is not a book
# about car maintenance: "a book to read in the car" has no anchor and gets the general pick.
_BOOK_ANCHOR = re.compile(
    r"\b(?:about|on|covering|teach(?:es)?|"
    r"for beginners? (?:at|in|to)|"
    r"beginners? (?:guide to|book (?:on|about))|"
    # who the book is for, with the subject after it: "a book for someone who likes history",
    # "a book for my dad who is into fishing", "for anyone who loves gardening", "books for
    # people interested in the stars", "what to read if i like history". The person is why the
    # subject is named, not a present, so the anchor reads past them to the subject the table
    # knows. A present with no such clause still has no anchor and stands down, which is why
    # the who-likes shapes are spelled out and the bare word "for" is not enough.
    r"for (?:someone|somebody|anyone|anybody|people|a person"
    r"|my (?:mum|mom|dad|mother|father|brother|sister|son|daughter|wife|husband|partner"
    r"|friend|nan|gran|grandad|grandma|grandpa))"
    r" (?:who|that) (?:likes?|loves?|enjoys?|is into|is a fan of|is interested in|is keen on)|"
    r"(?:who|that) (?:likes?|loves?|enjoys?|is into|is a fan of|is interested in|is keen on)|"
    r"(?:someone|somebody|anyone|anybody|people|a person)"
    r" (?:interested in|keen on|into)|"
    r"(?:if|when) (?:i|you|they|he|she|im|i'm) (?:like|love|enjoy|am into|are into|is into)|"
    r"a fan of|interested in|keen on|"
    r"(?:to|for) learn(?:ing)?)\b\s+(.{0,40})")


def _says(phrase, text):
    """The phrase as whole words in the text, so "car" does not answer "carpet"."""
    return re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", text) is not None


# A subject can sit in front of the word as well as after an "about": "recommend a poetry book"
# is a book about poetry, and it was answered with a murder mystery because the pick needs the
# anchor word and this line has none. The words just before "book" are the subject in that shape.
_BOOK_SUBJECT_BEFORE = re.compile(r"([a-z' ]{0,40})\bbooks?\b")


def _book_subject(text):
    """(the pick, True) when the line asks for a book about a subject, (None, True) when the
    subject is one we have no pick for, and (None, False) when no subject is named."""
    match = _BOOK_ANCHOR.search(text)
    if match:
        tail = match.group(1)
    else:
        before = _BOOK_SUBJECT_BEFORE.search(text)
        if not before:
            return None, False
        tail = before.group(1)
    for phrase in _SUBJECT_BOOK_ORDER:
        if _says(phrase, tail):
            return SUBJECT_BOOKS[SUBJECT_BOOK_NAMES[phrase]], True
    for phrase in _SUBJECT_UNCOVERED_ORDER:
        if _says(phrase, tail):
            return None, True
    return None, False


def _book_thriller(memory, understood):
    """A thriller pick that does not recommend the book the line says they just finished."""
    text = ((understood.get("clean") or "") + " " + (understood.get("norm_text") or "")).lower()
    if "thursday murder club" in text:
        return ("The next one is *The Man Who Died Twice* by Richard Osman, the same four friends "
                "again. For a different author, *The Marlow Murder Club* by Robert Thorogood is "
                "close in tone, or *The Silent Patient* if you want a darker twist.")
    return ("*The Silent Patient* by Alex Michaelides and *The Thursday Murder Club* by Richard "
            "Osman are both quick and hard to put down; the second one is much funnier. Tana "
            "French's *In the Woods* if you want something longer and darker.")


def _book_about(memory, understood):
    """The first book on the subject the line names, or None so the line is passed on."""
    # A kind of book is not a subject: "what book should i read if i like science fiction" read
    # "science" as the subject and answered *A Short History of Nearly Everything*, which is a
    # different shelf from the one the person asked about. The genre rows know their own picks,
    # so this row stands down and lets them answer (see BOOK_GENRES).
    if not _a_genre_is_the_taste(understood):
        return None
    text = ((understood.get("clean") or "") + " "
            + (understood.get("norm_text") or "")).lower()
    pick, _named = _book_subject(text)
    return pick


# "book" is a thing you read and a thing you do, and the same word cannot be both. Every
# reservation line carries the noun this row keys on - "i need to book a hotel for the night",
# "book a table for six", "i have to book a ferry" - and got a novel back. The row asks whether
# the line is doing the verb: the word with a determiner after it ("book a", "book the"), or the
# infinitive ("to book"). "a book for the train" and "a book to read on the plane" keep the noun
# because neither carries that shape.
_RESERVING_PHRASES = ("book a", "book an", "book the", "book my", "book our", "book some",
                      "to book", "booking a", "booking the", "booked a", "booked the",
                      "book it", "reserve a", "reserve the", "reserved a",
                      # a booking already made says when it is, and the thing booked comes
                      # before the verb: "physio booked for friday", "the room is booked for
                      # saturday", "we are booked in for the 3rd". Without these the line is a
                      # book subject to the pick - "physio booked for friday" got a novel.
                      "booked for", "booked in", "booked up", "booked with", "is booked",
                      "are booked", "was booked", "were booked", "be booked", "got booked")

# The same verb with nothing after it: a modal or the person in front ("should we book", "can i
# book", "do we need to book", "worth booking"), or the time of it after ("book first", "book
# ahead", "book early", "book online", "book tickets"). Neither shape takes a determiner, so
# "a book first" and "the book first" keep the noun: the word before it is what decides, which
# is why the adverbial shapes are checked rather than trusted.
_BOOK_VERB_BEFORE = re.compile(
    r"\b(?:should|shall|can|could|must|might|would|will|do|does|did|need|needs|needed|"
    r"worth|to|lets|let's)\s+(?:we\s+|i\s+|you\s+|they\s+|he\s+|she\s+|it\s+)?"
    r"book(?:ing|ed)?\b")
_BOOK_VERB_AFTER = re.compile(
    r"\bbook(?:ing|ed)?\s+(?:first|now|ahead|early|before|soon|online|today|tonight|"
    r"tickets?|in advance|up)\b")
_A_DETERMINER_JUST_BEFORE = re.compile(
    r"\b(?:a|an|the|this|that|my|our|your|his|her|their|its|any|some|no|each|every|"
    r"another|one|same|next|other|good|great|new|second|third)\s+(?:\w+\s+)?$")

def _not_a_reservation(understood):
    """True when the line is not reserving something, for the row that answers book subjects."""
    if _a_judged_work_named(understood):
        return False
    return not the_book_is_a_reservation(understood)


def _a_judged_work_named(understood):
    """True when the line names a work of the table and asks for a view on it.

    "is dune a good book" names *Dune* and carries a judgement, so it is a question about that
    book and the verdict row answers it. The subject row matched it as well - "book" plus "good"
    - and won on its bias, so `lookup.find` handed back a row whose reply then stood down for
    want of a subject, and the answer underneath was correct while the row that gave it was not.
    A line that names a work *and* judges it is never a request for a book on a subject, so this
    row stands down instead. "recommend a book about the office" carries no judgement word and
    is not touched.
    """
    text = ((understood.get("clean") or "") + " "
            + (understood.get("norm_text") or "")).lower()
    if not _work_named(text):
        return False
    return any(_says(word, text) for word in JUDGE_WORDS)


def the_book_is_a_reservation(understood):
    """True when the line is reserving something, which is the booking rows' question.

    The word "book" is a thing you read and a thing you do, and the two readings of a line are
    searched one at a time, never joined: put end to end, the last word of one is followed by the
    first of the other, and `the film first or the book` read as `book the film` - a reservation
    that is not in the line at all.
    """
    for reading in (understood.get("clean"), understood.get("norm_text")):
        if _a_reservation(str(reading or "").lower()):
            return True
    return False


def _a_reservation(text):
    """Whether this one reading of the line is reserving something."""
    if not text.strip():
        return False
    # whole words: "book a" is inside "book about", so a plain substring test made every
    # "a book about history" look like a reservation and stood the subject table down
    if any(_says(phrase, text) for phrase in _RESERVING_PHRASES):
        return True
    # The verb with nothing after it: a modal or the person in front ("should we book", "can i
    # book", "worth booking"), or the time of it after ("book first", "book online"). Neither
    # shape takes a determiner, so "a book first" and "the book first" keep the noun.
    if _BOOK_VERB_BEFORE.search(text):
        return True
    for match in _BOOK_VERB_AFTER.finditer(text):
        before = text[:match.start()]
        if not _A_DETERMINER_JUST_BEFORE.search(before):
            return True
    return False





# A place someone says instead of a name: "near me", "nearby", "round here". The listings row
# carries them as subjects, because "whats on near me tonight" names no venue and no town - the
# nearest thing to a place in the line is the person. They are not in its avoid list any more,
# which means the row now reads every line with one of them in it, and two of those lines are a
# different question: "is there a cinema near me" and "cheapest cinema near me" ask *where* one
# is, which is a map's job, and "whats on near me tonight" asks *what is on*, which is this row.
# So the ask decides, and only for a line that says near at all: every other line reaches this
# row exactly as it did before, near or not.
_NEAR_ME = re.compile(r"\bnear(?:\s+me|\s+here|by)\b|\bnear\s+where\s+i", re.I)
_SAYS_WHAT_IS_ON = re.compile(
    r"\b(?:on|showing|playing|listings|line[- ]?up|schedule)\b"
    r"|\b(?:tonight|today|this\s+(?:week|weekend|month))\b", re.I)
# Whether a place is open is the clock's question and not a listing: "is there a pharmacy open
# near me on Sunday" has the near-phrase and the day in it, and the one thing the row knows - the
# venue's own page has the times - is not the answer to a chemist's opening hours.
_ASKS_IF_OPEN = re.compile(
    r"\b(?:open|opens|opening|closed|closes|closing|shut|hours|times)\b", re.I)


def _a_listings_ask_near_me(understood):
    """Whether a line that says "near me" is asking what is on rather than where a place is."""
    text = " ".join(str((understood or {}).get("clean") or "").lower().split())
    if not _NEAR_ME.search(text):
        return True
    if _ASKS_IF_OPEN.search(text):
        return False
    return bool(_SAYS_WHAT_IS_ON.search(text))


# A book in the hand that is not working is a complaint, not an ask: "my book is boring",
# "this book is rubbish", "i cant get into it". The pick is the second thing wanted, and a line
# that asks for a recommendation is not this, so both readers have to agree.
_A_BOOK_I_AM_NOT_ENJOYING = re.compile(
    r"\b(?:boring|bored\s+(?:of|with)|a\s+slog|so\s+slow|really\s+slow|not\s+enjoying|"
    r"can'?t\s+get\s+into|cant\s+get\s+into|gave\s+up\s+on|rubbish|terrible|awful|dull)\b")
_ASKS_FOR_A_PICK = re.compile(
    r"\b(?:recommend|suggest|suggestion|any\s+good|something|what\s+should\s+i\s+read|"
    r"what\s+to\s+read|what\s+can\s+i\s+read|a\s+book\s+(?:that|to|for|about)|"
    r"what\s+book|which\s+book|any\s+ideas|ideas\s+for)\b")


def _book_recommend(memory, understood):
    """A generic pick, unless the line asks about a subject or a child's reading."""
    earlier = " ".join(str(turn.get("user") or "")
                        for turn in (memory.get("turns") or [])[-3:])
    said = ((understood.get("clean") or "") + " "
            + (understood.get("norm_text") or "")).lower()
    pick, named = _book_subject(said)
    if named:
        # a book about gardening is not a novel, and one we have no pick for is passed on
        return pick
    if _A_BOOK_I_AM_NOT_ENJOYING.search(said) and not _ASKS_FOR_A_PICK.search(said):
        # "my book is boring" is a complaint about the book in hand, not a request for a
        # recommendation: the first thing wanted is permission to stop, and the pick is the
        # second. A line that asks for something ("a book that isnt boring", "recommend a book")
        # is left to the pick and the mood table.
        return ("Put it down - finishing a book you are not enjoying is not a virtue, and 50 "
                "pages is a fair trial before you give up on it. If you want another: *The "
                "Thursday Murder Club* by Richard Osman is funny with short chapters, *The "
                "Silent Patient* if you want a twist, and *The Midnight Library* by Matt Haig if "
                "you want something to think about. What did the last one you loved have that "
                "this one has not?")
    context = ((understood.get("clean") or "") + " " + earlier).lower()
    # A title the table knows is the table's question: "diary of a wimpy kid" has the word "kid"
    # in it, and the child pick took it before the table could, so the titles come out of the
    # context first. A real child in the line ("my son", "for a 9 year old") stays.
    named = _book_title_named(context)
    if named:
        context = context.replace(named, " ")
        if not any(word in context for word in ("son", "daughter", "child", "kid", "year old",
                                                "grandson", "granddaughter", "niece", "nephew",
                                                "teenager")):
            # the table answers: a title it knows is the table's question, and handing it back
            # here keeps the row whichever of the two cards wins the line
            return _book_like(memory, understood)
    # A baby or a toddler is not a young reader: the answer is a board book with nothing to chew
    # off, and a class is a book that reads aloud. Both were being answered with a novel for a
    # ten-year-old, and "what book should i read to my baby" with the health visitor.
    if any(word in context for word in ("baby", "babies", "toddler", "one year old",
                                        "two year old", "18 months", "six months",
                                        "nine months", "newborn")):
        return ("For a baby, board books that survive being chewed and pulled: *The Very Hungry "
                "Caterpillar* by Eric Carle, *Dear Zoo* by Rod Campbell, *Where's Spot?* by Eric "
                "Hill, or any of the *That's Not My...* touchy-feely books. Read the same three or "
                "four over and over - the repetition is the point at that age - and let them turn "
                "the pages, even if it slows you down.")
    if any(word in context for word in ("my class", "the class", "assembly", "story time",
                                        "storytime", "reception class", "nursery")):
        return ("For reading aloud to a group: *The Gruffalo* by Julia Donaldson for the rhymes, "
                "*The Tiger Who Came to Tea* by Judith Kerr for the pause at the doorbell, and "
                "*Oi Frog!* by Kes Gray for the joke on every page. *The Gruffalo* is the safest "
                "one for a mixed group: the rhythm carries it and there is a repeated line they "
                "can join in with.")
    if any(word in context for word in ("daughter", "son", "child", "kid", "year old",
                                        "grandson", "granddaughter", "niece", "nephew",
                                        "teenager")):
        return ("For a younger reader: *The Bolds* by Julian Clary (funny on every page), "
                "*The Worst Witch* (short chapters), *The Explorer* by Katherine Rundell for "
                "animals and adventure, or *Dog Man* if comics are easier. Start with *The Bolds* "
                "or *Dog Man*: jokes first, and no long descriptions to get through.")
    return ("*The Thursday Murder Club* by Richard Osman is the safest pick: funny, short "
            "chapters, easy to pick up. For something darker, *The Silent Patient*; for a "
            "younger reader, *Wonder* by R. J. Palacio or *The Explorer* by Katherine Rundell. "
            "Tell me what you last enjoyed and I'll narrow it down.")


# --- the mood they want it in -------------------------------------------------
# People ask for a pick by the feeling it should leave them with, not by genre: "something
# sad to watch", "a book that makes you think", "a film thats not too long". One table
# keyed by the mood the line names, with a pick for each medium, answers every way of
# asking for it; the medium is read off the line, so a new mood is one row of words and one
# reply per medium rather than a new rule per phrasing.
MOODS = {
    "sad": ("sad", "cry", "crying", "cries", "tears", "tearjerker", "tear jerker",
            "heartbreaking", "heartbroken", "heartbreak", "emotional", "moving", "weepy",
            "sob", "sob story", "devastating", "break my heart", "breaks my heart",
            "make me cry", "makes me cry", "made me cry"),
    "funny": ("funny", "laugh", "laughing", "laughs", "hilarious", "comedy", "comedies",
              "cheer me up", "cheering up", "makes me laugh", "make me laugh"),
    "scary": ("scary", "scariest", "scare", "scares", "horror", "frightening", "creepy",
              "terrifying", "spooky", "jump scares", "ghost story", "halloween"),
    "think": ("makes me think", "make me think", "makes you think", "make you think",
              "thought provoking", "clever", "thoughtful", "philosophical", "mind bending"),
    "uplifting": ("uplifting", "uplifted", "cheerful", "feel good", "feelgood",
                  "heartwarming", "heart warming", "happy", "hopeful", "comforting",
                  # asked the other way round: "a book thats not depressing", "nothing
                  # miserable", "something that isnt gloomy". The negation is part of the mood.
                  "not depressing", "isnt depressing", "isn't depressing", "nothing depressing",
                  "not miserable", "nothing miserable", "not gloomy", "nothing gloomy",
                  "not bleak", "not heavy", "nothing heavy", "nothing sad"),
    "gripping": ("gripping", "page turner", "page turners", "pageturner", "not put it down",
                 "not put down", "not stop reading", "unputdownable", "exciting", "addictive",
                 "tense", "edge of my seat", "hard to put down", "able to put down",
                 "up all night reading", "read in one sitting", "read it in one go",
                 "read at one go"),
    "short": ("short", "shortest", "quick", "quickest", "not too long", "one sitting"),
    "true": ("true story", "true stories", "based on a true story", "real story", "real life",
             "nonfiction", "non fiction", "biography", "memoir", "documentary"),
    "twist": ("twist", "twists", "twisty", "surprise ending", "shock ending"),
    "romance": ("romantic", "romance", "love story", "rom com", "romcom"),
    "light": ("light", "lighthearted", "cosy", "cozy", "gentle", "relaxing", "relaxed",
              "unwind", "wind down", "chill", "chill out", "easy going", "easy watching",
              "fall asleep", "asleep", "to sleep to", "drowse off", "doze",
              "easy read", "nothing heavy", "easy to watch", "switch my brain off",
              "switch off to", "turn my brain off", "brain off", "no thinking",
              "dont want to think", "nothing demanding"),
}
# The order a line naming more than one mood is read in: the stronger feeling first.
MOOD_ORDER = ("sad", "funny", "scary", "think", "uplifting", "gripping", "short", "true",
              "twist", "romance", "light")
NEGATORS = frozenset(("not", "no", "never", "without", "nothing", "none", "hate", "hates",
                      "avoid", "hardly", "barely"))
# "isn't" and "isnt" are both "is not" before any word is read, so a line written either way is
# turned down the same way.
CONTRACTIONS = {
    "aint": "are not", "arent": "are not", "cant": "can not", "couldnt": "could not",
    "didnt": "did not", "doesnt": "does not", "dont": "do not", "hadnt": "had not",
    "hasnt": "has not", "havent": "have not", "isnt": "is not", "shouldnt": "should not",
    "wasnt": "was not", "werent": "were not", "wont": "will not", "wouldnt": "would not",
}
# Words that sit between a "not" and the mood it turns down ("not too scary", "not very sad").
# Only these let a negator two words back count, so "wont be able to put down" stays a request
# for a gripping book rather than a refusal of one.
SOFT = frozenset(("too", "very", "that", "so", "much", "a", "really", "quite", "at", "all"))
# A refusal is not always "not too sad". People say "i dont want a scary film" and "i dont like
# horror films", where a wanting verb stands between the negator and the mood it turns down: the
# mood was read as a request and the person asking for something that is not scary was given the
# scariest list on the shelf. Only these verbs may stand in that gap.
WANTING = frozenset(("want", "wanted", "wants", "like", "likes", "liked", "fancy", "enjoy", "mind"))

# A pick for each mood, per medium. Named works only: a mood list that names nothing to pick
# up is no help to a person standing in a shop or holding a remote.
FILM_MOODS = {
    "sad": ("For a good cry: *Manchester by the Sea* is quiet and devastating, *Atonement* lands "
            "its ending like a brick, and *Up* does it in the first ten minutes. Have tissues "
            "ready."),
    "funny": ("For laughs: *What We Do in the Shadows* (a daft vampire mockumentary), *The Nice "
              "Guys* (funny and twisty) or *Paddington 2*, which makes almost everyone laugh."),
    "think": ("*Arrival* (would you want to know the future?), *12 Angry Men* (one room, all "
              "talk, gripping) or *Ex Machina* (quiet, unsettling science fiction). All three "
              "stay with you afterwards."),
    "uplifting": ("*Hunt for the Wilderpeople* (funny and warm), *The Shawshank Redemption* (hope "
                  "you have to earn) or *Sing Street* (music, first love and a big grin at the "
                  "end)."),
    "gripping": ("*Prisoners* is tense from the first scene, *Gone Girl* keeps you guessing to "
                 "the end, and *Sicario* turns the screw for two hours straight."),
    "short": ("*Before Sunset* runs 80 minutes, *Locke* is 85 with one man in a car, and *Toy "
              "Story* is 81. All three are short and none of them asks much of a tired evening."),
    "true": ("*Zodiac* (the investigation, not the killings), *Catch Me If You Can* (light and a "
             "lot of fun) or *127 Hours* if you want to be on the edge of your seat."),
    "twist": ("*The Sixth Sense*, *The Prestige* and *Gone Girl* all turn on a twist you will "
              "not see coming. Start with *The Prestige*."),
    "romance": ("*Before Sunrise* (two people talking all night), *When Harry Met Sally* (the "
                "funny one) or *Pride & Prejudice* (2005) for the longing and the costumes."),
    "light": ("*Paddington 2*, *Chef* or *The Detectorists* (a series): warm, low-stakes and easy "
              "to watch, and nothing bad happens in any of them."),
}
BOOK_MOODS = {
    "sad": ("*A Little Life* is the one people sob through, *Never Let Me Go* hurts quietly, and "
            "*The Kite Runner* if you want it to hit hard."),
    "scary": ("*The Haunting of Hill House* is creepy rather than gory, *Bird Box* is fast and "
              "tense, and *The Shining* if you want the classic."),
    "think": ("*Klara and the Sun* (what makes someone human), *The Remains of the Day* (a whole "
              "life looked back on) or *Sapiens* if you would rather have ideas than a story."),
    "uplifting": ("*The Midnight Library* (gentle and hopeful), *Lessons in Chemistry* (funny and "
                  "big-hearted) or *The Hundred-Year-Old Man Who Climbed Out of the Window and "
                  "Disappeared* (daft and warm)."),
    "gripping": ("*Gone Girl* (twisty from page one), *The Martian* (problem-solving and very "
                 "hard to put down) or any *Jack Reacher* book by Lee Child."),
    "short": ("*Of Mice and Men* is about 100 pages, *The Old Man and the Sea* is short and "
              "perfect, and *Small Things Like These* is under 120 pages."),
    "true": ("*Educated* by Tara Westover, *Into the Wild* by Jon Krakauer or *The Diary of a "
             "Young Girl* by Anne Frank: all real, all hard to stop reading."),
    "twist": ("*The Silent Patient* and *Gone Girl* both turn on a twist; *The Seven Husbands of "
              "Evelyn Hugo* if you want the reveal to make you cry as well."),
    "romance": ("*The Flatshare* (funny and warm), *Beach Read* (a bit sharper) or *Pride and "
                "Prejudice* if you want the classic."),
    "light": ("*The Thursday Murder Club* (funny and gentle), *The Midnight Library* or *The No. "
              "1 Ladies' Detective Agency*: easy to pick up and nothing grim."),
}
# A series is its own medium, and so is a podcast: "a funny series" and "something gentle on
# telly" had no table to answer them at all.
TV_MOODS = {
    "sad": ("*This Is Us* is built to make you cry weekly, *Normal People* hurts quietly, and "
            "*After Life* mixes the sad with real jokes."),
    "funny": ("*Schitt's Creek* starts daft and gets warmer, *Derry Girls* is sharp and short, "
              "and *The Detectorists* is gentle comedy."),
    "think": ("*Severance* (what work does to a person), *Chernobyl* (how a system fails) or "
              "*The Wire* if you want a whole city to think about."),
    "uplifting": ("*Ted Lasso* is kind and funny, *The Repair Shop* is people mending things "
                  "that matter to them, and *Call the Midwife* if you want warmth and a cry."),
    "gripping": ("*Happy Valley* is tense from the first scene, *The Night Of* does not let go, "
                 "and *Bodyguard* starts at a sprint and stays there."),
    "short": ("Episodes beat films when the evening is short: *The Bear* is 25 minutes an "
              "episode, *Derry Girls* is 22, and *Inside No. 9* is half an hour with a twist."),
    "true": ("*The Long Shadow*, *Des* or *Mr Bates vs The Post Office*: true stories told "
             "straight, all of them hard to stop watching."),
    "twist": ("*Line of Duty* for the reveal at the end of every series, *Severance* for the "
              "strangest one, and *Broadchurch* if you like a whole town hiding something."),
    "romance": ("*Normal People* for the intense one, *Starstruck* for the funny one, and "
                "*Bridgerton* if you want the frocks and the gossip."),
    "scary": ("*The Haunting of Hill House* for dread, *Midnight Mass* if you want one with "
              "ideas in it, and *Inside No. 9* for half-hour creepers."),
    "light": ("*The Detectorists* is the gentlest thing on telly, *Mortimer & Whitehouse: Gone "
              "Fishing* is two friends chatting, and *The Great British Bake Off* needs no "
              "attention at all."),
}
# The funny row is used twice: by the podcast shelf ("a funny podcast") and by a mood the chat
# was already on, so the picks are written once here.
PODCAST_FUNNY = ("For funny: *No Such Thing as a Fish* (four people, one bizarre fact each, about "
                 "half an hour), *The Adam Buxton Podcast* for long chats that wander, or *Off "
                 "Menu* where guests order their dream meal. All easy to dip in and out of.")
# A crime podcast asked for by its subject. `podcast-history` holds the word "true" and
# `podcast-mood` reads "true crime" as the real-lives mood, so the subject row was the one thing
# missing: "true crime podcast" was three interviews and "crime podcast" was nothing at all.
PODCAST_CRIME = ("*Serial* series one is where to start: one murder, a year of reporting, and the "
                 "reason everyone else started making them. Then *Casefile* (calm, one case an "
                 "episode), *Criminal* (short, strange cases, less grim) or *The Teacher's Pet* "
                 "if you want one long story done properly.")
PODCAST_MOODS = {
    "funny": PODCAST_FUNNY,
    "think": ("*The Rest Is History* (history with jokes), *Hidden Brain* (why people do what "
              "they do) or *More or Less* if you like numbers checked."),
    "scary": ("*The Battersea Poltergeist* tells one haunting week by week, *Uncanny* collects "
              "real people's stories, and *Lore* does folk tales."),
    "true": ("*The Diary of a CEO* for long interviews, *Desert Island Discs* for real lives in "
             "an hour, or *This American Life* for one story told properly."),
    "gripping": ("*Serial* (the first series) started the genre, *The Teacher's Pet* is grim and "
                 "gripping, and *Sweet Bobby* has a twist you will not believe."),
    "light": ("*Desert Island Discs* is a gentle hour of somebody's life, *Nothing Much Happens* "
              "is made for falling asleep to, and *The Archers* if you want a story to drift "
              "with."),
    "sad": ("*Terrible, Thanks for Asking* is people telling hard things honestly, and *The "
            "Moth* is five-minute true stories, many of which land hard."),
}
# Every mood in a medium's table, by the medium a line or the line before it names. A new
# medium is one row here plus its table; the entry below does not change.
MOOD_TABLES = {"film": FILM_MOODS, "book": BOOK_MOODS, "tv": TV_MOODS,
               "podcast": PODCAST_MOODS}
# The medium nobody named: one line per mood naming a pick from two or three of them.
ANY_MOODS = {
    "sad": ("For a good cry: *Manchester by the Sea* on film, *Normal People* as a series, or "
            "*Never Let Me Go* if you would rather read."),
    "funny": ("For a laugh: *Groundhog Day* on film, *Schitt's Creek* on telly, or *The "
              "Thursday Murder Club* if you would rather read. Say which and I'll pick one."),
    "scary": ("Scary: *Get Out* on film, *The Haunting of Hill House* as a series or as the "
              "Shirley Jackson novel, and *Uncanny* if you want it in headphones. Which "
              "suits?"),
    "think": ("Something to think about: *Arrival* on film, *Severance* as a series, or *Klara "
              "and the Sun* to read. None of them tells you what to think."),
    "uplifting": ("Something hopeful: *Hunt for the Wilderpeople* on film, *Ted Lasso* as a "
                  "series, or *The Midnight Library* to read. All three leave you better than "
                  "they found you."),
    "gripping": ("Hard to stop: *Prisoners* on film, *Happy Valley* as a series, or *Gone Girl* "
                 "to read. Give any of them an evening you have nothing else planned for."),
    "short": ("Short and good: *Before Sunset* (80 minutes) on film, *The Bear* (25-minute "
              "episodes) as a series, or *Of Mice and Men* (about 100 pages) to read."),
    "true": ("True stories: *Zodiac* on film, *Mr Bates vs The Post Office* as a series, or "
             "*Educated* by Tara Westover to read."),
    "twist": ("With a twist: *The Prestige* on film, *Line of Duty* as a series, or *Gone Girl* "
              "to read. All three keep the reveal for the end."),
    "romance": ("Romantic: *Before Sunrise* on film, *Starstruck* as a series, or *The Flatshare* "
                "to read."),
    "light": ("Something easy: *Paddington 2* on film, *The Detectorists* on telly, or *The "
              "Thursday Murder Club* to read. None of them asks anything of you."),
}

# Which medium a line names. Read on the line itself first, and, when the line names none,
# on the line before it: "something funny" after a question about tonight's telly is a
# request for a programme, and after a question about books it is a request for a book.
MEDIUM_WORDS = (
    ("podcast", ("podcast", "podcasts", "listen", "listening")),
    ("book", ("book", "books", "novel", "novels", "read", "reading", "audiobook",
              "audiobooks")),
    ("tv", ("tv", "telly", "series", "show", "shows", "boxset", "box set", "binge",
            "episode", "episodes", "netflix", "iplayer")),
    ("film", ("film", "films", "movie", "movies", "cinema", "watch", "watching")),
    # no table of its own yet: a mood in the music chat reaches the cross-medium line
    ("music", ("music", "song", "songs", "album", "albums", "playlist")),
)

# The words a mood entry is keyed on: every mood word, so the entry only reaches a line that
# names a mood as well as the medium.
# The words a line can use to name a mood, minus the ones that only glue a sentence together.
# A key is read word by word, so "not" and "much" in a key would only ever match a line by
# accident, and a key word's weight falls as more entries use it: a mood word in the key can
# take the weight off an older entry that shares it, which is how "nothing on tv tonight"
# stopped reaching the easy-watching answer. The phrases themselves are read in full below.
MOOD_GLUE = frozenset("""a an the it its i me my im i'm you your he she him her they them we
us our want wants wanted would like likes to of for and or but so really very much too not no
never nothing none dont doesnt didnt hardly barely some something that this these those there
here is are was were am be been being do does did have has had will can could should may might
get gets got able one ones make makes made in on at up down out off over with by from as if
than then when while all night""".split())
def _mood_key_words(moods, drop=()):
    """The words an entry is keyed on, so a line naming a mood of this kind reaches it.

    Only the words that carry the mood: "nothing heavy" is keyed as "heavy", because a key is
    read word by word and "nothing" in a key is a word another entry may be the only one to
    use. A key word's weight falls as more entries share it, so taking "nothing" here took the
    weight off the easy-watching answer and "nothing on tv tonight" changed its mind about what
    it was asking. The phrases themselves are read whole by `_mood_of`, which is where "nothing
    heavy" means what it says.
    """
    shut = {word for phrase in drop for word in str(phrase).split()}
    found = []
    for mood in MOOD_ORDER:
        if mood not in moods:
            continue
        for phrase in moods[mood]:
            for word in str(phrase).split():
                if word in MOOD_GLUE or word in found or word in shut:
                    continue
                found.append(word)
    return tuple(found)


MOOD_WORDS = _mood_key_words(MOODS)


# Filled in below, once `_mood_of` reads them: `_mood_signals` calls `_mood_of`, so both maps are
# empty while they are being worked out and hold only what the phrase table knows.
MOOD_BY_WORD = {}
MOOD_SIGNAL_SET = set()


def _mood_signals(words):
    """The words that name a mood on their own.

    `MOOD_WORDS` lifts single words out of phrases, so "turn my brain off" contributes "turn" and
    "keep me on the edge of my seat" contributes "edge". That is harmless where the entry also
    needs a medium ("a series to turn on"), and wrong where the mood is the whole question: "my
    son is turning 7 and i have no idea what to get him" is a present, not a pick. A word that
    answers as a mood by itself is one `_mood_of` recognises alone, so the test is the reader
    itself rather than a list kept by hand.
    """
    return tuple(word for word in words
                 if _mood_of(word) or _mood_of("not too " + word) or _mood_of("nothing " + word))


def _negated(tokens, start, phrase):
    """True when the words just before this phrase turn it down ("not too scary", "isn't sad").

    A phrase that carries its own negation is a positive ask - "not too long" is a request for
    something short - so only what comes before it counts."""
    if not start or phrase[0] in NEGATORS:
        return False
    if tokens[start - 1] in NEGATORS:
        return True
    if start > 1 and tokens[start - 2] in NEGATORS and tokens[start - 1] in SOFT:
        return True
    # "i dont want a scary film", "i dont like horror films", "im not into anything scary": the
    # negator is up to two words further back, with a wanting verb next to the mood.
    # "i dont want a scary film", "i dont want to watch anything sad tonight": the wanting verb
    # can be one to four words before the mood, and the negator sits directly before it. The gap
    # is what "a", "to watch" and "anything" fill, so the walk back covers those and no further.
    for back in (1, 2, 3, 4):
        if start > back and tokens[start - back] in WANTING and tokens[start - back - 1] in NEGATORS:
            return True
    return False


# The words a line has to say for itself. A card about the weather or about an evening is only
# the answer when the line names the weather or the evening: the reading carries a topic from
# turns back, so "so what should i do" arrived at the wet-day card from a line about rain three
# turns up, and a haircut gets advice for a rainy afternoon.
_WET_WORDS = ("rain", "rainy", "raining", "rains", "showers", "drizzle", "drizzling",
              "pouring", "downpour", "storm", "storms", "sleeting", "sleet", "snowing")
# "wet" on its own is a state of a thing, not weather: a wall is wet, a cellar is wet, and a
# child wets the bed. Only a day, a weekend or the air said with it is the weather, so the word
# is here as those phrases and not bare. It matters past the guard: a follow-up line that lends
# the topic's word ("what can i do" after "my son wets the bed") reaches a row whose key holds
# the bare word and then stands down, and the widened reading that would have answered it is
# never built.
_WET_PHRASES = ("wet day", "wet days", "wet weekend", "wet weekends", "wet afternoon",
                "wet weather", "wet out", "wet one")
_EVENING_WORDS = ("night in", "tonight", "evening", "at home",
                  "indoors", "cosy", "cozy", "this afternoon in", "day in",
                  # "stay in" on its own is not the evening: it is the verb in every
                  # timetable question ("how long do stitches stay in", "how long can you
                  # leave a tampon in"), and it was pulling those onto the evening card.
                  # The evening is said with a person and a time round it.
                  "we are staying in", "were staying in", "im staying in",
                  "i am staying in", "staying in tonight", "stay in tonight",
                  "staying in this evening", "stay in this evening", "staying in all")


def _typed_line(understood):
    """The line as the person typed it, lower case, one space either side."""
    if not isinstance(understood, dict):
        return " "
    said = understood.get("text") or understood.get("clean") or ""
    return " %s " % _plain_words(said)


def _names_the_weather(understood):
    """True when this line says the weather, not when a topic from earlier turns does."""
    line = _typed_line(understood)
    return (any((" %s " % word) in line for word in _WET_WORDS)
            or any(phrase in line for phrase in _WET_PHRASES))


def _names_the_evening(understood):
    """True when this line says the evening, not when a topic from earlier turns does."""
    line = _typed_line(understood)
    return any((" %s " % word) in line for word in _EVENING_WORDS)


def _plain_words(line):
    """A line as plain words, with every contraction written out ("isn't" -> "is not")."""
    plain = str(line or "").lower().replace("\u2019", "'").replace("-", " ")
    plain = re.sub(r"n'\s*t\b", "nt", plain)
    plain = plain.replace("'", "")
    words = []
    for word in re.findall(r"[a-z0-9]+", plain):
        words.extend(CONTRACTIONS.get(word, word).split())
    return " ".join(words)


def _mood_of(line):
    """The mood a line asks for, or None: (mood, turned down).

    A mood the line turns down ("not too sad", "nothing scary") is answered with the light list
    rather than with the mood it refused - a friend who hears "nothing heavy tonight" offers
    something easy, not silence. A medium with no light row is left to its own entries."""
    plain = _plain_words(line)
    tokens = plain.split()
    if not tokens:
        return None
    refused = None
    for mood in MOOD_ORDER:
        for phrase in MOODS[mood]:
            words = re.findall(r"[a-z0-9]+", re.sub(r"[-']", " ", phrase))
            if not words:
                continue
            for start in range(len(tokens) - len(words) + 1):
                if tokens[start:start + len(words)] != words:
                    continue
                if _negated(tokens, start, words):
                    refused = refused or mood
                    continue
                return (mood, False)
    # A mood word with no phrase around it: "not too heavy for bedtime" says the same as
    # "nothing heavy", and the phrase table only has the second one. A word counts here only if
    # it names a mood on its own (see `_mood_signals`), so "my son is turning 7" is not a mood.
    for at, token in enumerate(tokens):
        if token not in MOOD_SIGNAL_SET:
            continue
        mood = MOOD_BY_WORD.get(token)
        if _negated(tokens, at, [token]):
            # "not too heavy" is the light end of a mood the phrase table only spells as
            # "nothing heavy", so a refused signal word is a refusal, not a want.
            refused = refused or mood or token
            continue
        if mood is not None:
            return (mood, False)
    # Any mood the line turns down is a request for something else, not silence. Only four
    # moods used to have a way out, so "i dont want to watch a documentary" - a refused mood
    # with nowhere to go - reached the composer as a bare follow-up and got "I'm listening".
    # A person who says what they do not want is still asking for a film, and the floor for
    # that is the easy list: it answers "not a documentary", "not a musical", "nothing heavy"
    # and "i dont want anything sad" with the same three warm picks.
    if refused:
        return ("light", True)
    return None


MOOD_SIGNALS = _mood_signals(MOOD_WORDS)
MOOD_SIGNAL_SET.update(MOOD_SIGNALS)
# The mood each of those words names, for a line that says the mood without its phrase. Only a
# word listed on its own that means the mood positively: "long" is a word of "not too long" and
# nothing else, so "how long was it" stays a question about a film and not a want of a short one.
for _mood in MOOD_ORDER:
    for _word in MOODS[_mood]:
        if (isinstance(_word, str) and " " not in _word and _word not in MOOD_BY_WORD
                and _mood_of(_word) == (_mood, False)):
            MOOD_BY_WORD[_word] = _mood


def _no_named_mood(understood):
    """False when the line names a mood, so the general pick is not the answer.

    "give me a film that will make me cry" was the easy-tonight list, because "give me" is a
    key word of the general row and the mood row only ties with it: the want is read as the
    whole ask and the mood was the part that said what to pick. A line that names a mood - said
    out ("something sad") or turned down ("nothing too heavy") - belongs to the mood entries,
    and this row is only for the line that names none.
    """
    said = " ".join(str(word) for word in (understood.get("words") or ()))
    return _mood_of(said) is None


# How long each film these rows name actually runs. A mood or a kind said with a length is still
# that mood or kind ("something sad under 90 minutes" is a cry, not a runtime), but the answer has
# to keep to the minutes asked for: a list whose every film overruns the limit is a list that
# ignored half the line. The runtimes are here rather than inside each sentence so one number
# serves every row that names the same film.
FILM_MINUTES = {
    "Manchester by the Sea": 137, "Atonement": 123, "Up": 96,
    "What We Do in the Shadows": 86, "The Nice Guys": 116, "Paddington 2": 103,
    "Arrival": 116, "12 Angry Men": 96, "Ex Machina": 108,
    "Hunt for the Wilderpeople": 101, "The Shawshank Redemption": 142, "Sing Street": 106,
    "Prisoners": 153, "Gone Girl": 149, "Sicario": 121,
    "Before Sunset": 80, "Locke": 85, "Toy Story": 81,
    "Zodiac": 157, "Catch Me If You Can": 141, "127 Hours": 94,
    "The Sixth Sense": 107, "The Prestige": 130,
    "Before Sunrise": 101, "When Harry Met Sally": 96, "Pride & Prejudice": 129,
    "Chef": 114, "Groundhog Day": 101, "The Grand Budapest Hotel": 99,
    "Get Out": 104, "A Quiet Place": 90, "Hereditary": 127, "The Others": 104,
    "The Mitchells vs the Machines": 114, "Matilda": 102, "Zootropolis": 108,
}


def _films_within(text, line):
    """A reply that names films, cut to the ones that fit the minutes the line states.

    The films a row names are its answer, so the whole list is kept when every one of them fits,
    and a reply that names a book, a series or a film with no runtime here is left alone. What
    changes is only this: a film longer than the limit is dropped and named as longer, and when
    none of them fits the shortest is named with its runtime rather than a list that overruns.
    """
    if not text or not isinstance(line, str):
        return text
    limit, strict = _limit_wanted(line)
    if not limit:
        return text
    named = []
    for title in re.findall(r"\*([^*]{2,60})\*", text):
        if title not in named:
            named.append(title)
    if not named or any(title not in FILM_MINUTES for title in named):
        return text
    fit = [title for title in named
           if (FILM_MINUTES[title] < limit if strict else FILM_MINUTES[title] <= limit)]
    if len(fit) == len(named):
        return text
    over = len(named) - len(fit)
    lead = text.split(":")[0].strip()
    has_lead = ":" in text and 0 < len(lead) <= 40 and "*" not in lead
    short = min(named, key=lambda title: FILM_MINUTES[title])
    if not fit:
        if has_lead:
            return ("%s, nothing there comes in %s %d minutes - the shortest is *%s* at %d. Say "
                    "another mood and I will look again."
                    % (lead, "under" if strict else "at", limit, short, FILM_MINUTES[short]))
        return ("Nothing in that list comes in %s %d minutes - the shortest is *%s* at %d. Say "
                "another mood and I will look again."
                % ("under" if strict else "at", limit, short, FILM_MINUTES[short]))
    said_fit = ["*%s* (%d minutes)" % (title, FILM_MINUTES[title]) for title in fit]
    body = said_fit[0] if len(said_fit) == 1 else ", ".join(said_fit[:-1]) + " or " + said_fit[-1]
    if has_lead:
        return ("%s, %s %d minutes: %s. The other %s run%s longer, so say if you would rather "
                "have one of those." % (lead, "under" if strict else "up to", limit, body,
                                        "one" if over == 1 else "two",
                                        "s" if over == 1 else ""))
    return ("Films that fit %s %d minutes: %s. The rest of that list run%s longer, so say if you "
            "would rather have one of those."
            % ("under" if strict else "up to", limit, body, "s" if over == 1 else ""))


def _mood_pick(picks):
    """An entry reply that answers the mood the line names from one medium's table."""
    def pick(memory, understood):
        line = ((understood.get("clean") or "") + " " + (understood.get("norm_text") or ""))
        got = _mood_of(line)
        if not got:
            return None
        mood = "light" if got[1] else got[0]
        return _films_within(picks.get(mood), line) if mood else None
    return pick


def _medium_named(text):
    """Which medium a line names, or None.

    A reply that names several ("*Get Out* on film, *Hill House* as a series or the novel") is
    about the one it leads with, so the medium that comes first in the line is the one it is
    about, not the first one in the table below."""
    said = " %s " % _plain_words(text)
    best, where = None, len(said) + 1
    for medium, words in MEDIUM_WORDS:
        for word in words:
            at = said.find(" %s " % word)
            if at >= 0 and at < where:
                best, where = medium, at
    return best


def _the_medium(understood, memory):
    """The medium an ask about a mood is about: this line, or what the chat was already on."""
    understood = understood if isinstance(understood, dict) else {}
    order = ["%s %s" % (understood.get("clean") or "", understood.get("norm_text") or "")]
    lean = understood.get("leans_on") if isinstance(understood.get("leans_on"), dict) else {}
    if lean.get("text"):
        order.append(str(lean.get("text") or ""))
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if isinstance(turns, list) and turns and isinstance(turns[-1], dict):
        order.append(str(turns[-1].get("user") or ""))
        order.append(str(turns[-1].get("bot") or ""))
    for text in order:
        medium = _medium_named(text)
        if medium:
            return medium
    # An answer that never says the word ("Start with *The Rest Is History*") still says which
    # medium the chat is on by the picks it names, and by the entry that gave it: every pick
    # entry is named for its medium.
    for text in order:
        medium = _title_medium(text)
        if medium:
            return medium
    last = memory.get("last_answer") if isinstance(memory, dict) else None
    last = last if isinstance(last, dict) else {}
    named = str(last.get("id") or "").split("-")[0]
    for medium, words in MEDIUM_WORDS:
        if named and named in [word.split()[0] for word in words]:
            return medium
    return None


# The picks of every table, by title, so a reply that names one says which medium it is about
# even when it never says the word ("*Schitt's Creek* starts daft..." is a series).
def _picks_by_title():
    found = {}
    for medium, table in MOOD_TABLES.items():
        for moods in table.values():
            for title in re.findall(r"\*([^*]{2,60})\*", moods):
                # A one-word title like "Up" would be found in "wake up in the night", so the map
                # keeps only names long enough to be a title rather than a word.
                if len(title) >= 6:
                    found.setdefault(_plain_words(title), medium)
    return found


PICK_TITLES = _picks_by_title()


def _title_medium(text):
    """Which medium a reply is about, by the picks it names.

    An answer that says "*Schitt's Creek* starts daft..." never says "series", and the follow-up
    ("which one first") is about that medium. Every pick in the tables above is scanned once, so
    a new pick in a table is known to its medium without another line of code.
    """
    said = " %s " % _plain_words(text)
    best, where = None, len(said) + 1
    for title, medium in PICK_TITLES.items():
        at = said.find(" %s " % title)
        if at >= 0 and at < where:
            best, where = medium, at
    return best


def _chat_is_about_a_pick(understood, memory):
    """Whether what has been talked about so far was something to watch, read or listen to.

    A mood word on its own ("something quick") is a request in a chat about films and a
    recipe ask in a chat about cooking, so the chat decides. An answer from another domain
    is another domain's conversation, and a line that reads as a feeling is not a mood word
    that went wrong."""
    understood = understood if isinstance(understood, dict) else {}
    last = memory.get("last_answer") if isinstance(memory, dict) else None
    last = last if isinstance(last, dict) else {}
    domain = str(last.get("domain") or "")
    topic = str(understood.get("topic") or "")
    if not topic:
        lean = understood.get("leans_on") if isinstance(understood.get("leans_on"), dict) else {}
        topic = str(lean.get("topic") or "")
    if domain == "entertainment" or topic == "entertainment":
        return True
    # With nothing talked about yet, or a mood the understanding engine read as a feeling,
    # the mood word is all there is to go on.
    return not domain and topic in ("", "feelings")


# "no not too scary", "nothing too sad": after a pick the person turns the mood down, and what
# they want is the far end of it in the same medium rather than the pick said again. The words
# that turn a mood down are here, so the same mood words in a line that asks for them ("a really
# scary film") are left to the mood rows.
TURNS_IT_DOWN = ("no", "not", "nothing", "dont", "don't", "rather not", "no thanks", "too much",
                 "isnt", "isn't", "wasnt", "wasn't", "cant stand", "can't stand", "hate",
                 "sick of", "bored of", "no more", "anything but", "not really")
# A length asked to be short is the length machinery's line ("not too long", "nothing too long"),
# not a mood turned down, and so is a refusal of a thing rather than of a mood.
TURNED_DOWN_KEEPS_ITS_OWN = NOT_A_MOOD_PICK + (
    "not too long", "nothing too long", "not long", "not too big", "not too expensive",
    "not too many", "not too much", "nothing too much",
)


def _a_pick_of_the_other_mood(memory, understood):
    """The picks at the far end of a mood the line turns down: "no not too scary" after a scare."""
    understood = understood if isinstance(understood, dict) else {}
    line = "%s %s" % (understood.get("clean") or "", understood.get("norm_text") or "")
    got = _mood_of(line)
    if not got or not got[1]:
        # An affirmed mood is the mood rows' ask, not this one's.
        return None
    return _a_pick_in_any_medium(memory, understood)


# The mood that is a length rather than a kind. A length says nothing about what the thing is,
# so it is only an ask for a pick when the line or the chat names something to pick.
A_LENGTH_MOOD = ("short",)


def _a_pick_in_any_medium(memory, understood):
    """Something in the mood they named, in whichever medium the chat was already on."""
    understood = understood if isinstance(understood, dict) else {}
    line = "%s %s" % (understood.get("clean") or "", understood.get("norm_text") or "")
    got = _mood_of(line)
    if not got or not _chat_is_about_a_pick(understood, memory):
        return None
    # "short" is the one mood here that is a length, and every other mood says what the thing is
    # like. A length describes anything - a walk, a nap, a recipe - so on a line that names
    # nothing to pick, it is not a pick: "i fancy something spicy but quick" reached the film,
    # series and book row through "quick" alone and answered a cooking line with *Before Sunset*,
    # while "i fancy something spicy" without the length word gets the chilli. A medium named
    # ("anything quick to read") or a chat already about a pick ("something shorter" after a
    # list) still carries it.
    if got[0] in A_LENGTH_MOOD and not (_pick_kind(line) or _pick_carry(memory, line)):
        return None
    # The mood has to be the person's own. A follow-up reaches this row with the turn before it
    # glued onto the line, so "i dont want a scary film what should i watch" then "anything a bit
    # lighter" arrived with the word "scary" in it twice and no refusal beside it: the row read
    # the scare as wanted and answered a person who had just turned one down with *Get Out* and
    # *The Haunting of Hill House*. Read the line's own words first, and when they name no mood,
    # take one from the earlier turns only if that turn wanted it.
    own = _mood_of(" ".join(_own_texts(understood)))
    if own and own[1]:
        mood = "light"
    elif own:
        mood = own[0]
    else:
        mood = _the_mood_the_chat_holds(memory)
        if not mood:
            if not _the_mood_the_chat_turned_down(memory):
                return None
            # "anything a bit lighter" after "i dont want a scary film" wants the lighter end
            mood = "light"
    # A length limit is a thing only a film has here: "something funny under two hours" is the
    # evening's runtime, and a mixed list ("on film, on telly, or ...") cannot keep to the
    # minutes the person gave. So a limit with no medium named is read off the film table, the
    # one table that carries runtimes (see _films_within). A medium named or carried stays its
    # own question.
    if _limit_wanted(line)[0] and not _pick_kind(line) and not _pick_carry(memory, line):
        picks = MOOD_TABLES.get("film") or {}
    else:
        picks = MOOD_TABLES.get(_the_medium(understood, memory)) or {}
    said = picks.get(mood) or ANY_MOODS.get(mood)
    last = memory.get("last_answer") if isinstance(memory, dict) else None
    last = last if isinstance(last, dict) else {}
    said = _films_within(said, line)
    if said and _plain_words(said) == _plain_words(str(last.get("reply") or "")):
        # The same picks a second turn running: a subjectless follow-up ("whos in it") is read as
        # the line before it, and handing the same list back is the one reply that says nothing.
        # One of them is chosen instead, which is what the follow-up was asking for anyway.
        first = re.search(r"\*([^*]{2,60})\*", said)
        if first:
            return "Of those, I'd start with *%s*." % first.group(1)
        return None
    return said


# "what should I watch for overnight" is being alert to a symptom, not a viewing request.
NOT_WATCHING = ("watch for", "watching for", "watch out", "look out for", "keep an eye out",
                "signs of", "symptoms", "what to look")

# ... but "a film to watch for the kids" is still a film. Only the *asking* form - "what should I
# watch for", "what signs", "look out for", "keep an eye on" - is the alert, so that is what the
# guard reads, and a line naming something to watch keeps the film rows whatever else it says.
VIEWING = ("film", "films", "movie", "movies", "tv", "telly", "tele", "show", "shows", "series",
           "episode", "episodes", "netflix", "dvd", "cinema", "documentary", "programme",
           "programmes", "box set", "boxset", "sitcom", "cartoon", "cartoons")

# "what should i watch" alone is a viewing ask ("what should i watch with my kids tonight"), so
# every phrase here carries the sense of being alert: a "for", a sign, a symptom or an eye.
ASKING_TO_WATCH_FOR = ("what should i watch for", "what do i watch for", "what to watch for",
                       "what should i watch out", "what do i watch out", "watch out for",
                       "look out for", "sign", "symptom", "keep an eye",
                       "what to look for", "what should i look for", "what should i be looking")


def not_asking_what_to_watch_for(understood):
    """True unless the line asks what to be alert to and names nothing to watch."""
    if not isinstance(understood, dict):
        return True
    said = str(understood.get("text") or understood.get("clean") or understood.get("norm_text")
               or " ".join(understood.get("words") or ())).lower()
    if not said:
        return True
    if any(word in said for word in VIEWING):
        return True
    return not any(asked in said for asked in ASKING_TO_WATCH_FOR)

# --- quick creative asks ------------------------------------------------------
# "Write me a haiku about rain" is not a fact question: no table of facts answers it and a
# search cannot either, because what it wants is a form and a subject. The subject is the thing
# named after "about", and the form is a syllable count or a rhyme, so the forms are written
# out here as data keyed by the thing the poem is about - one row per form, and a new subject
# is one line of data rather than a new entry.
#
# Every line below is counted by hand and checked by a counter in tests/test_creative_asks.py,
# because a haiku that does not scan is worse than the shrug it replaces.

HAIKU = {
    "rain": ("Rain on the window,",
             "a hundred small taps, all night,",
             "and the garden drinks."),
    "sea": ("The sea keeps its own",
            "slow time, and the tide turns twice",
            "before anyone looks."),
    "ocean": ("The sea keeps its own",
              "slow time, and the tide turns twice",
              "before anyone looks."),
    "cat": ("Cat on the warm sill,",
            "one eye on the garden birds,",
            "both ears fast asleep."),
    "kitten": ("Cat on the warm sill,",
               "one eye on the garden birds,",
               "both ears fast asleep."),
    "dog": ("Wet nose at the door,",
            "the whole day arrives at once,",
            "tail first, always first."),
    "puppy": ("Wet nose at the door,",
              "the whole day arrives at once,",
              "tail first, always first."),
    "autumn": ("Autumn in the park,",
               "the trees hand back what they took,",
               "and the air smells cold."),
    "winter": ("Winter on the glass,",
               "the kettle keeps its own time,",
               "and the cat agrees."),
    "snow": ("First snow on the street,",
             "the world turned down to a hush,",
             "footprints, and then none."),
    "spring": ("Spring in the hedges,",
               "green shoots pushing through the dark,",
               "nothing asks to stay."),
    "summer": ("Summer on the lane,",
               "the long evening will not end,",
               "and nobody minds."),
    "night": ("Moon over the roof,",
              "the house settles into dark,",
              "one light left upstairs."),
    "moon": ("Moon over the roof,",
             "the house settles into dark,",
             "one light left upstairs."),
    "sun": ("The sun on my back,",
            "and a chair that is too warm",
            "to do anything."),
    "morning": ("Morning in the house,",
                "the kettle takes its time now,",
                "a sock on the stairs."),
    "tea": ("Steam from the mug climbs,",
            "the morning waits in the pot,",
            "nothing is urgent."),
    "coffee": ("First cup of the day,",
               "the desk, the list, the phone calls,",
               "all of it can wait."),
    "garden": ("Garden after rain,",
               "the snail crosses the whole path,",
               "taking its own time."),
    "city": ("The city at six,",
             "every window lights up late,",
             "one streetlamp still out."),
    "friend": ("Good friend on the phone,",
               "an hour goes like ten minutes,",
               "and nothing was fixed."),
    "mum": ("Mum in the kitchen,",
            "sings the wrong words on purpose,",
            "and I sing them too."),
    "mother": ("Mum in the kitchen,",
               "sings the wrong words on purpose,",
               "and I sing them too."),
    "work": ("The desk light is on,",
             "the list grows shorter, then long,",
             "and five o'clock comes."),
    "job": ("The desk light is on,",
            "the list grows shorter, then long,",
            "and five o'clock comes."),
    "running": ("Legs heavy, lungs loud,",
                "the last mile always uphill,",
                "and the door, and home."),
    "gym": ("Legs heavy, lungs loud,",
            "the last mile always uphill,",
            "and the door, and home."),
    "school": ("School bag by the door,",
               "a hundred small things to learn,",
               "and one of them stays."),
    "baby": ("Small hands on my face,",
             "the whole night in one held breath,",
             "then a milky sleep."),
    "love": ("Love is a kettle",
             "put on without being asked,",
             "and the chair pulled out."),
    "birthday": ("One more candle lit,",
                 "the cake leans under the wish,",
                 "and everyone sings."),
}
# A haiku is counted in sounds, so two words share an answer when they name the same thing.
HAIKU["kids"] = HAIKU["baby"]
HAIKU["bed"] = HAIKU["night"]
HAIKU["river"] = HAIKU["sea"]

# The same subjects as a short rhymed poem, for the lines that ask for a poem rather than a
# haiku: two couplets, said plainly, which is what people want for a card or a reading.
POEMS = {
    "sea": ("The sea is loud and never still,",
            "it takes the sand against its will.",
            "It keeps it for a day or three,",
            "then hands it back to you and me."),
    "rain": ("The rain comes down on everything,",
             "on roof, on road, on outstretched wing.",
             "It does not ask who wants it here,",
             "it just arrives, and then it's clear."),
    "autumn": ("The leaves let go without a sound",
               "and lie in gold across the ground.",
               "The trees stand bare and do not mind:",
               "there is another spring behind."),
    "night": ("The night comes in and closes shop,",
              "the street goes quiet, the traffic stops.",
              "One window keeps its light on late",
              "for someone who is coming in the gate."),
    "cat": ("The cat has found the warmest chair",
            "and settled in it, without care.",
            "The chair was yours an hour ago.",
            "The cat does not believe it so."),
    "mum": ("My mum has heard it all before",
            "and still she stands inside the door.",
            "She says the small things can all wait,",
            "and then she makes the small things fit -",
            "and that is why I ring her late,",
            "and why she never mentions it."),
    "friend": ("A friend is someone at the door",
               "who does not need to say what for.",
               "You put the kettle on for two",
               "and half the weight comes off of you."),
    "garden": ("The garden does not need a plan,",
               "it fills the space up while it can.",
               "A weed is just a plant that knows",
               "the better spot, and simply grows."),
    "winter": ("The winter takes the light away",
               "and gives it back a bit each day.",
               "The cold is honest, and the frost",
               "draws on the glass and counts no cost."),
    "work": ("The work comes in and fills the day,",
             "and takes the evening half away.",
             "I do the bit that's in my hand",
             "and leave the rest where it can stand."),
    "birthday": ("Another year, and here you are,",
                 "with all the miles and all the scars.",
                 "The cake is small, the wish is too:",
                 "more of the good ones, sent to you."),
    "dad": ("My dad will fix it if he can,",
            "and if he can't, he'll have a plan.",
            "He says the worst is never true,",
            "and mostly, it turns out he knew."),
}

# Limericks are the form people ask for by name and the one a table of facts cannot fake, so
# they are written out too. Each is a real limerick: aabba, the two short lines in the middle.
LIMERICKS = {
    "cat": ("There once was a cat on a chair,",
            "who hadn't a worry or care.",
            "When the postman came by,",
            "it opened one eye,",
            "and gave him a very long stare."),
    "kitten": ("There once was a cat on a chair,",
               "who hadn't a worry or care.",
               "When the postman came by,",
               "it opened one eye,",
               "and gave him a very long stare."),
    "dog": ("There once was a dog called Ned,",
            "who slept at the end of the bed.",
            "He dreamt of a cat,",
            "of a bone, and of that",
            "half a sausage he thought he'd been fed."),
    "puppy": ("There once was a dog called Ned,",
              "who slept at the end of the bed.",
              "He dreamt of a cat,",
              "of a bone, and of that",
              "half a sausage he thought he'd been fed."),
    "rain": ("There once was a cloud over Crewe",
             "that had far too much rain to do.",
             "It rained on the park",
             "from morning till dark,",
             "and then, just for fun, rained on you."),
    "tea": ("There once was a builder called Len",
            "who brewed up a pot now and then.",
            "When the tea was stewed",
            "it improved his mood,",
            "and he put the kettle on then."),
    "work": ("There once was a report I should write",
             "whose deadline was Tuesday at night.",
             "I opened the file,",
             "stared at it a while,",
             "and closed it again out of spite."),
    "baby": ("There once was a baby called Rose,",
             "who slept like a dream, I suppose.",
             "Till somebody said",
             "'she's asleep!' and instead",
             "she woke up, as everyone knows."),
}
LIMERICKS["job"] = LIMERICKS["work"]
LIMERICKS["mum"] = LIMERICKS["baby"]

# A limerick for a subject with none of its own. The rhymes are fixed words rather than
# invented ones, so the line scans whatever noun the person typed, and their own word is the
# one the poem is about.
GENERIC_LIMERICK = ("There once was a {thing} I knew,",
                    "whose stories were never quite true.",
                    "They wandered the day,",
                    "and took their own way,",
                    "and honestly, what can you do?")

# The poem for any other subject: two couplets that lean on the same two rhymes, so it is a poem
# rather than a list of lines, and the person's own word is named three times.
# A second verse about the same thing, for "one more about the moon" after the first one: the
# table holds one poem per thing, so the thing with no poem of its own comes back in this shape
# the second time rather than word for word.
GENERIC_POEM_TWO = ("The {thing} is here and the {thing} is plain,",
                    "it comes round slowly and it comes round again.",
                    "I have no better answer to give it than this,",
                    "so I put it in a line and I let it exist.")
GENERIC_POEM = ("I keep a little {thing} in mind,",
                "the sort of {thing} that's hard to find.",
                "It does not shout, it does not boast,",
                "and that's the {thing} I like the most.")

# The people people write poems about. "I keep a little wife in mind" is a joke at her expense,
# and a poem about a person is a warm thing or nothing, so a person the tables do not name gets
# this verse and never the comic one.
PEOPLE = ("wife", "husband", "partner", "girlfriend", "boyfriend", "fiance", "fiancee",
          "love", "son", "daughter", "child", "kid", "baby", "sister", "brother",
          "grandma", "grandmother", "nan", "gran", "grandad", "grandfather", "friend",
          "best friend", "mate", "mother", "mum", "mom", "father", "dad")
WARM_POEM = ("You are the one I tell things to,",
             "the dull ones and the hard ones too;",
             "the day can take whatever's spare,",
             "and still I'm glad you're there.")

# A card stands a poem down when the card is the thing being written: "write a rhyme for a
# birthday card" and "what do i write in my card" want the line that goes inside it, and the card
# rows answer that well. What is not that ask is a card named only as where the thing goes, with
# no occasion and no writing word: "can you write a short poem about autumn for my daughter's
# card" got no poem and no card line either on main (2026-11-06), because the card rows key on an
# occasion or a leaving and the line has neither, so a person asking for a poem about autumn was
# told it was beyond what the bot knows. Hence the occasion phrases and the writing-in phrases,
# all adjacent, rather than the bare word.
# One occasion per card row, wherever in bot/knowledge that row lives: a new card row's occasion
# belongs here too, or the forms answer over the top of it ("write a poem for a christening card"
# got the template verse while the christening row sat right behind it).
CARD_OCCASIONS = ("birthday", "christmas", "xmas", "new baby", "wedding", "engagement",
                  "christening", "baptism", "naming ceremony", "communion", "anniversary",
                  "valentines", "valentine's", "mothers day", "mother's day", "fathers day",
                  "father's day", "new home", "housewarming", "graduation", "new job",
                  "promotion", "get well", "get better", "good luck", "retirement",
                  "leaving", "condolence", "sympathy", "thank you", "thankyou")
CARD = (tuple(one + " card" for one in CARD_OCCASIONS) +
        ("in a card", "in my card", "in the card", "in this card", "on a card", "on my card",
         "on the card", "inside the card", "card message", "card wording", "card line",
         "card lines"))

# Subjects a fixed-rhyme verse cannot carry. "I keep a little lockdown in mind" is a joke about
# the shape of the template, not about lockdown, and the honest thing is to ask for one real
# detail to build the verse round. A concrete thing the tables do not know still gets the
# template, because that is what it is for.
ABSTRACT = ("lockdown", "pandemic", "covid", "coronavirus", "virus", "grief", "loss", "love",
            "hope", "fear", "anxiety", "depression", "stress", "time", "memory", "memories",
            "childhood", "future", "past", "war", "peace", "freedom", "illness", "cancer",
            "dementia", "addiction", "recovery", "friendship", "marriage", "divorce", "work",
            "school", "unemployment", "poverty", "climate", "world", "life", "age", "ageing",
            "motherhood", "fatherhood", "loneliness", "happiness", "sadness", "anger", "regret",
            "guilt", "change", "growing", "job", "money", "death")

# A story is a form like the poems: the shape is fixed and the thing slots into it, so the story
# scans whatever noun they typed. Two openings, chosen by the word, so the same ask gets the same
# story and a different ask gets a different one.
STORY_OPENINGS = (
    "It started with {a_thing} nobody in the house had planned for.\n"
    "The Tuesday came and went, and it was still there on the Wednesday.\n"
    "By Friday the whole street had an opinion, and no two of them matched.\n"
    "In the end they kept it, and it kept them.",
    "{The_thing} arrived in a box with no sender and no note.\n"
    "It sat in the hall for a week, and then it started to hum.\n"
    "She unscrewed one corner, looked inside, and sat down on the floor.\n"
    "\"Well,\" she said to nobody at all, \"that changes the week.\"",
    "He had carried {the_thing} from one flat to another for eleven years.\n"
    "The morning he finally opened it, the kettle boiled and the phone rang at the same time.\n"
    "He let the kettle win, and the phone stopped.\n"
    "Then he sat at the table with {the_thing} and read the whole thing twice.",
)

# A possessive is the person's own, so it is read off the line rather than guessed from the noun:
# "write a rap about my nan" came back as "Yo, the nan is back and it is here to stay", and the
# first fix answered that with a list of person words - which then gave "Yo, my baby is back" to a
# line that said "write a rap about a baby", and "my nurse" to "the nurse". A possessive is only
# there when the person typed it. Each of these is followed by the thing, so "my brother" and
# "my little brother" both keep it and "mum's garden" keeps the owner.
POSSESSIVE = ("my ", "your ", "our ", "his ", "her ", "their ", "its ", "mum's ", "dad's ",
              "nan's ", "gran's ", "mum’s ", "dad’s ")

# A verse with no thing named in it used to read the template's fill-in word out loud ("Yo, the
# small thing is back"), which sounds like a form letter. A rap leans on the beat and a song on
# the tune instead, the way the words would go if a person were making one up on the spot.
NO_THING_IN_A_VERSE = {"rap": "beat", "song": "tune"}


def _the_possessive_phrase(thing, said):
    """"my nan", "his nurse", "my little brother" - the phrase as the person wrote it.

    The possessive has to be theirs and it has to be attached: "write a story about my little
    brother" is "my little brother" and not "the brother", while "my friend wants a rap about a
    bike" is still "a bike", because two words are all that may sit between the possessive and
    the thing.
    """
    if not said or not thing:
        return ""
    for word in POSSESSIVE:
        start = 0
        while True:
            at = said.find(word, start)
            if at < 0:
                break
            rest = said[at + len(word):]
            spot = rest.find(thing)
            if spot >= 0 and len(rest[:spot].split()) <= 2:
                end = at + len(word) + spot + len(thing)
                return " ".join(said[at:end].split())
            start = at + 1
    return ""


def _article_for(thing, article="the", clean=""):
    """The article a thing takes in these templates, as both a mid-sentence and a lead word.

    The person's own possessive, when the line has one - "my nan", "his nurse", "mum's garden" -
    and otherwise the article the template asked for, so "the sea", "a bike", "a baby" and "the
    wedding" read as they did. Returned as a dict of the phrases the templates interpolate,
    because "My nan arrived" at the start of a line needs the capital and "with my nan" in the
    middle does not.
    """
    said = (clean or "").lower()
    theirs = _the_possessive_phrase(thing, said)
    if theirs:
        return {"a_thing": theirs, "the_thing": theirs,
                "The_thing": theirs[:1].upper() + theirs[1:]}
    their = article + " "
    return {"a_thing": "a " + thing, "the_thing": their + thing,
            "The_thing": (their + thing)[:1].upper() + (their + thing)[1:]}

# The verse, asked to be longer. "tell me a longer one", "can you make it longer", "write a
# longer one", "and make it longer", "longer please": after a story or a poem this is the
# commonest follow-up there is, and each of them answered with something else - the search hedge
# ("I don't know enough to answer that honestly"), the listening line ("Thanks for telling me"),
# and on "and make it longer" the hair-growth card. What "it" is is the verse just given, so the
# continuation is written in the same form and about the same thing, and it is added to the verse
# rather than replacing it: the person asked for more of what they were given.
STORY_LONGER = (
    "The weeks went by and it stopped being strange.\n"
    "Things settled into a shape nobody had chosen, and the shape held.\n"
    "Then one quiet morning there was nothing to decide,\n"
    "and they found they missed the deciding more than they had expected.",
    "There was a phone call in the spring that changed the plan.\n"
    "Nothing was thrown out, though a few things were put away.\n"
    "By summer the {thing} had a place of its own in the house,\n"
    "and nobody could remember what had stood there before it.",
    "It came up again at dinner, the way these things do.\n"
    "Somebody said it out loud and everybody laughed, and then carried on eating,\n"
    "which is how a thing stops being news.\n"
    "After that the {thing} was simply part of the room.",
    "Years later somebody asked where it had come from\n"
    "and got four different answers, all of them true.\n"
    "They settled on the shortest one, because it was the one\n"
    "that left the {thing} where it was.",
)
VERSE_LONGER = (
    "The {thing} is not what the morning planned,\n"
    "it sits in the light and it will not be banned.\n"
    "It is stubborn and it is small and it is here to stay,\n"
    "and I have stopped arguing with it anyway.",
    "There is more to the {thing} than the shape it shows,\n"
    "more than the part that anybody knows.\n"
    "So leave a little room and leave a little light,\n"
    "and the {thing} will get through the rest of the night.",
    "I said what I said and I meant every word,\n"
    "the {thing} is not finished, or so I have heard.\n"
    "So here is one more, and I will keep it plain,\n"
    "for the {thing} and the weather it cannot explain.",
    "The {thing} does not hurry and does not explain,\n"
    "it takes the long way round and it comes back again.\n"
    "So let the day go where it wants to go,\n"
    "the {thing} knows the way and it is not slow.",
)

# A rap and a song work the same way: the rhyme words are fixed and the thing slots in where they
# cannot break the rhyme, so the beat holds whatever noun the person typed.
# A wedding, a funeral, a speech: the line has its own answer somewhere in the bot, and a rhyme
# handed to someone standing up at one of those is a worse reply than that answer.
OCCASION = ("wedding", "weddings", "best man", "maid of honour", "toast", "speech", "vows",
            "eulogy", "anniversary", "retirement")

# A line that wants a pick from someone else is not a line that wants one made up.
PICK_WORDS = ("recommend", "recommends", "recommendation", "recommendations", "suggest", "suggests",
              "suggestion", "playlist", "best", "good song", "good songs", "ideas", "any ideas",
              "what should i listen", "album", "albums", "artist", "artists")

STORY_LEADING = {"story": "A short story about {subject}:",
                 "rap": "A rap about {subject}:",
                 "song": "A song about {subject}:"}
# The lead for the same two forms when the line names nothing: "write me a rap" filled the subject
# with the template's fill-in word and said "A rap about small thing:", which reads like a mistake
# rather than like a verse. The words are the same either way; only the lead changes.
NO_SUBJECT_LEADING = {"rap": "A rap, then:", "song": "A song, then:",
                      "story": "Here is one, made up on the spot:"}
GENERIC_RAP = ("Yo, {the_thing} is back and it is here to stay,",
               "I have been up since six and I am out all day.",
               "They said it was nothing, I said it was mine,",
               "so {the_thing} and me, we are doing just fine.")
# "I put the dog down" is what you say at the vet's, and a song about a dog is not that, so the
# template leans on the thing instead of putting it anywhere.
GENERIC_SONG = ("Verse:\nIt was a Tuesday, nothing much to say,\n"
                "I thought about {the_thing} and I walked away.\n"
                "Chorus:\nOh, {the_thing}, {the_thing},\nit comes back around,\n"
                "{the_thing} comes back around.")
GENERIC_STORY_THING = "small thing"

# A nickname is a thing people ask for and then write on a card, so it is two word lists and a
# rule, not advice about nicknames.
NICK_FIRST = ("Captain", "Big", "Tiny", "Old", "Sir", "Lady", "Doctor", "Saint")
NICK_LAST = ("Chaos", "Thunder", "Biscuit", "Trouble", "Sunshine", "Nonsense", "Legend",
             "Saturday", "Pockets", "Rocket")

# A rhyme is the ending, not the meaning, so this is keyed by ending: the last sound of the word
# is what someone is stuck on. "Orange" is the famous one and gets the true answer.
RHYMES_BY_ENDING = {
    "ight": ("light", "night", "bright", "kite", "fright", "tight", "quite"),
    "ay": ("day", "way", "play", "away", "grey", "stay", "today"),
    "ee": ("tree", "see", "me", "free", "three", "agree"),
    "oo": ("blue", "true", "you", "shoe", "through", "new"),
    "ing": ("king", "sing", "ring", "spring", "wing", "thing"),
    "ain": ("rain", "train", "again", "plain", "chain", "brain"),
    "ame": ("name", "game", "same", "flame", "came"),
    "old": ("gold", "cold", "told", "bold", "hold"),
    "ine": ("line", "mine", "shine", "fine", "wine", "nine"),
    "ime": ("time", "climb", "lime", "dime", "rhyme"),
    "ake": ("cake", "lake", "make", "take", "wake", "break"),
    "eat": ("seat", "heat", "street", "meet", "treat", "wheat"),
    "one": ("bone", "stone", "phone", "alone", "own", "thrown"),
    "ate": ("late", "gate", "wait", "plate", "eight", "straight"),
    "ill": ("still", "hill", "will", "fill", "until"),
    "and": ("hand", "sand", "stand", "land", "band"),
    "art": ("heart", "start", "part", "smart", "apart"),
    "eet": ("feet", "street", "sweet", "meet", "sheet"),
    "ide": ("side", "wide", "hide", "ride", "guide"),
    "ound": ("sound", "round", "ground", "found", "around"),
    "own": ("town", "down", "clown", "crown", "brown"),
    "ue": ("blue", "true", "glue", "clue", "view"),
    "at": ("cat", "hat", "mat", "flat", "that", "bat"),
    "og": ("dog", "log", "fog", "jog", "bog"),
    "un": ("sun", "fun", "run", "bun", "one"),
    "ouse": ("house", "mouse", "blouse", "spouse"),
    "ock": ("clock", "sock", "rock", "block", "stock"),
    "air": ("chair", "hair", "fair", "care", "there"),
    "ell": ("bell", "well", "tell", "shell", "fell"),
    "ent": ("tent", "went", "sent", "bent", "spent"),
    "ore": ("door", "shore", "more", "floor", "before"),
    "end": ("friend", "end", "send", "bend", "spend"),
    "ove": ("love", "glove", "above", "dove", "shove"),
    "ome": ("home", "come", "some", "roam", "foam"),
    "oney": ("honey", "money", "sunny", "funny"),
    "eep": ("sleep", "deep", "keep", "sheep", "cheap"),
    "ife": ("life", "wife", "knife", "strife"),
    "ow": ("now", "how", "cow", "allow", "vow"),
    "oon": ("moon", "soon", "spoon", "June", "tune"),
    "all": ("small", "tall", "ball", "fall", "hall"),
    "ess": ("less", "dress", "mess", "press", "guess"),
    "ip": ("ship", "trip", "slip", "chip", "grip"),
    "op": ("shop", "stop", "top", "drop", "chop"),
    "ug": ("hug", "mug", "rug", "bug", "plug"),
    "an": ("man", "plan", "van", "ran", "tan"),
    "ear": ("year", "hear", "near", "clear", "fear"),
}
# The famous one: nothing in English rhymes with it exactly.
NO_RHYME = {
    "orange": ("Nothing rhymes exactly with *orange*. The near ones are *sporange* (a spore case "
               "on a fern), *Blorenge* (a hill in Wales) and the two-word *door hinge*. If you "
               "need it for a poem, put *orange* at the end of a line that does not have to "
               "rhyme, and rhyme the line before it with something else."),
    "purple": ("Nothing rhymes exactly with *purple*. *Curple* (a horse's strap) is the "
               "one word that nearly does, and *hirple* (to limp) is a Scottish near miss. In a "
               "poem, end the line on *purple* and rhyme the other line of the pair instead."),
    "silver": ("Nothing rhymes exactly with *silver*. *Chilver* (a ewe lamb) is the near miss, "
               "and most poets rhyme it with *river* or *deliver* and let the vowel do the work."),
    "month": ("Nothing rhymes exactly with *month*. *Oneth* is not a word, and the usual fix is "
              "to end the line on *month* and rhyme the other line of the pair."),
}

# Story ideas, for the lines that ask for one rather than for a story. Two are picked by the
# line itself, so the same question gets the same pair and a new question gets new ones.
STORY_IDEAS = (
    "A person finds a door in their own house that they have never opened, and the key is in "
    "their coat pocket.",
    "Two neighbours share a wall and a secret, and only one of them knows it is shared.",
    "A letter arrives forty years late, and the person it was meant for is still at the same "
    "address.",
    "Someone who has never left their village has to cross a city in one night.",
    "A family inherits a shop that comes with one customer who will not go away.",
    "A rescue dog remembers the person who lost it, and finds them in a supermarket queue.",
    "The last person on a night shift starts getting phone calls from the empty office upstairs.",
    "A cook loses their sense of taste the week they are cooking for the person they want to "
    "impress.",
    "A child's imaginary friend turns up at the school gate, and only the child can see them.",
    "A retired teacher keeps the exercise books of one pupil, and finally works out why.",
    "A train stops at a station that is not on the map, and one passenger gets off.",
    "Two strangers are given the same locker key at a swimming pool.",
    "A man who fixes everything in the street cannot fix the one thing in his own house.",
    "A woman starts receiving post addressed to her in her own handwriting, dated next year.",
    "A wedding photographer finds someone in the background of every photo who was never "
    "invited.",
    "A town agrees to forget one thing together, and one person refuses.",
)

# Names for a quiz team: people want something to write on the sheet, not advice.
QUIZ_NAMES = ("Quizteam Aguilera", "Les Quizerables", "Norfolk 'n' Chance", "The Quizzly Bears",
              "Sultans of Quiz", "Trivia Newton-John", "University of Trivia", "Agatha Quiztie",
              "Let's Get Quizzical", "The Also Rans")

# Not every team is a quiz team. A netball shirt, a work five-a-side and a football team want a
# name people can say and spell, and a quiz pun on a netball shirt is the wrong joke. These are
# ordinary team names that fit any side; the quiz puns stay for lines that name a quiz.
TEAM_NAMES = ("The Long Shots", "Second Wind", "The Underdogs", "The Night Owls",
              "The Wild Cards", "The Try Hards", "The Comeback Club", "The Early Birds")

# A poem is the wrong shape for a death, a diagnosis or a war. Those lines want a person to
# talk to, so the forms stand down and let the rest of the bot answer them.
GRAVE = ("funeral", "death", "dead", "died", "dying", "cancer", "war", "killed", "ill",
         "sick", "hospital", "grief", "bereaved", "suicide", "miss him", "miss her")

# A word that joins two subjects ("a boy and his dog") is never the thing the poem is about.
CONNECTORS = {"and", "with", "his", "hers", "their", "our", "who", "in", "at", "for", "to", "a",
              "an", "the"}

SUBJECT_STOP = {"a", "an", "the", "my", "our", "your", "his", "her", "their", "some", "this",
                "that", "of", "about", "on", "called", "named", "please", "thanks", "now",
                "today", "tonight", "too", "really"}
SUBJECT_TAIL = {"please", "thanks", "now", "today", "tonight", "too", "really", "and", "for",
                "about", "card", "me",
                # "a limerick about a man from spain" is about the man: a poem whose subject is
                # "from" reads as nonsense, and the place is a detail of the line.
                "from", "in", "at", "near", "by", "across", "over", "under", "behind",
                "with"}
# The words that end a subject: everything after one of these is the rest of the question, so
# "what book of poems should i get" is about poems and not about getting.
SUBJECT_END = {"should", "can", "could", "would", "will", "i", "you", "we", "he", "she", "they",
               "do", "does", "did", "is", "are", "was", "were", "get", "buy", "want", "need",
               "have", "has", "to", "that", "which", "what", "how", "when", "if", "says"}

# A subject made only of a determiner or a possessive is not a subject: "write a poem for my
# card" is about a card, not about "my", and a form that fires on it writes "A short poem about
# my". The tail words are cut first, so what is left can be a single one of these.
EMPTY_SUBJECT = {"my", "our", "your", "his", "her", "their", "the", "a", "an", "this", "that",
                 "these", "those", "it", "its", "me", "us", "them", "him", "one", "some"}

# An -ing word that is a noun, not a doing, so the trailing-word rule below leaves it where it
# is: "write a poem about my favourite thing" was a poem about "favourite", and "a song about
# sam's wedding" a song about sam. A list of things is smaller than the rule it protects, and
# these are the ones an everyday ask reaches for.
ING_NOUNS = {"anything", "beginning", "being", "blessing", "booking", "building", "ceiling",
             "clothing", "darling", "dressing", "earring", "ending", "evening", "feeling",
             "filling", "finding", "gathering", "going", "grandchild", "heading", "hearing",
             "king", "landing", "lightning", "meeting", "morning", "nothing", "offering",
             "opening", "outing", "painting", "pudding", "queen", "ring", "saying",
             "setting", "sibling", "spring", "staffing", "stocking", "string", "stuffing",
             "sung", "thing", "topping", "training", "warning", "wedding", "whatever",
             "wing", "writing", "young"}


def _subject_words(text):
    """The words of a subject, stopped at the first word that starts the rest of the question."""
    words = re.findall(r"[a-z']+", text)
    for place, word in enumerate(words):
        if word in SUBJECT_END:
            words = words[:place]
            break
    # "a boy and his dog" is a story about the boy: a joining word ends the subject.
    for place, word in enumerate(words):
        if place and word in CONNECTORS:
            words = words[:place]
            break
    # The cut comes first: "a man from spain" has to become "a man" before the trailing "from"
    # can be seen, or the strip never fires and the poem is about a preposition.
    words = words[:3]
    while words and (words[-1] in SUBJECT_TAIL or words[-1] in CONNECTORS):
        words.pop()
    # A word in -ing on the end of a subject is the doing, not the thing: "my dog learning
    # tricks" gave a poem about "learning" ("I keep a little learning in mind") and "my sister
    # getting married" a song about "the getting". It is dropped only when something else is
    # left to be about, so "a poem about cooking" and "about the morning" keep their word.
    if (len(words) > 1 and words[-1].endswith("ing") and len(words[-1]) > 4
            and words[-1] not in ING_NOUNS):
        if any(word not in SUBJECT_STOP and word not in EMPTY_SUBJECT for word in words[:-1]):
            words.pop()
    return words


# A verse for a form asked for with nothing named at all: "give me a limerick", "write me a
# poem", "make up a rhyme". The line names a form and the form is still what was asked for, so
# it gets a verse about nothing in particular rather than the search hedge it got on main
# (2026-11-09: "write me a limerick" and "give me a haiku" both got "I'm not sure about that
# one, sorry"). The lines are counted by tests/test_creative_asks.py like the tables above.
NO_SUBJECT_VERSE = {
    "haiku": ("Cold tap in the yard,",
              "the kettle ticks itself warm,",
              "morning starts again."),
    "limerick": ("There once was a fellow called Stan,",
                 "who swapped his old bike for a van.",
                 "It rattles, it groans,",
                 "on cobbles and stones,",
                 "and it still beats the bus, said his gran."),
    "poem": ("Some days are quiet, some are loud,",
             "and some you spend inside a cloud.",
             "The kettle helps, the window too,",
             "and so, quite honestly, do you."),
}


def _no_subject_verse(form, noun=None):
    """The verse for a form whose line named no subject, or None for a form with none."""
    lines = NO_SUBJECT_VERSE.get(form)
    if not lines:
        return None
    lead = {"haiku": "A haiku, then:", "limerick": "A limerick, then:"}.get(form,
                                                                          "A short poem, then:")
    if noun == "rhyme":
        lead = "A rhyme, then:"
    return _lines(lines, lead)


# The words each form answers to, and every other form a line can name instead. "write me a
# sonnet" reached the poem card's verse for a poem about nothing, because a line that named a
# form named one of *a* kind and this card only asked whether a subject was there: a sonnet is
# fourteen lines and a short rhymed poem is not one, and the sonnet card's own answer was
# better. A line that names a form that is not this one is that form's, so this card passes.
VERSE_FORM_WORDS = {
    "haiku": ("haiku", "haikus"),
    "limerick": ("limerick", "limericks"),
    "poem": ("poem", "poems", "poetry", "verse", "rhyme", "rhymes", "rhyming", "song", "rap",
             "ode", "odes"),
}
# forms with a card of their own and no verse here
_OTHER_FORM_WORDS = ("sonnet", "sonnets", "ballad", "ballads", "couplet", "couplets",
                     "acrostic", "acrostics", "elegy", "elegies", "epic", "epics",
                     "tanka", "sestina", "villanelle", "clerihew", "quatrain", "haibun")


def _names_another_form(clean, form):
    """True when the line names a verse form that is not `form`."""
    words = re.findall(r"[a-z']+", clean or "")
    mine = set(VERSE_FORM_WORDS.get(form, ())) | set(VERSE_FORM_WORDS.get("poem", ())) \
        if form == "poem" else set(VERSE_FORM_WORDS.get(form, ()))
    for word in words:
        if word in mine:
            continue
        if word in _OTHER_FORM_WORDS:
            return True
        for name, others in VERSE_FORM_WORDS.items():
            if name != form and word in others:
                return True
    return False


def _asks_for_a_verse(clean, form, noun=None):
    """The no-subject verse when the line asks for the form and names nothing else.

    "write a poem about my" names a possessive and stops: a verse that fills the gap with
    nothing ("A short poem about my") is worse than the shrug, so a half-named subject gets
    none. "write a poem for me" and "give me a haiku" name nobody and get the verse.

    Three kinds of line hold a form word and still want no verse: a how-to ("how do i write a
    poem" is the advice row's, and the verse took it from them), a remark about somebody
    else's verse ("my sister writes limericks" - one-slip repair reads "writes" as "write",
    so the row fires on it), and a half-named subject.
    """
    if _names_another_form(clean, form):
        return None
    if re.search(r"\b(?:how do i|how to|how can i|how should i|tips for|advice on|"
                 r"writes|wrote|writing|written|reads|reading)\b", clean):
        return None
    found = re.search(r"\b(?:about|of|on|regarding|describing|named|called|for)\s+(.+)$", clean)
    if found:
        words = _subject_words(found.group(1))
        if words and not (len(words) == 1 and words[0] in WHOM_IT_IS_FOR):
            return None
    return _no_subject_verse(form, noun)


# The words that finish a request for a verse rather than naming a subject: "write a poem for
# me" is whole, "write a poem for my" is not.
WHOM_IT_IS_FOR = frozenset(("me", "us", "you", "him", "her", "them", "one"))


def _subject(clean):
    """The thing a poem is about, as the person said it: "my cat", "the sea", "autumn".

    Their own words go back in the lead ("A poem about the sea:"), because a poem about "sea"
    reads like a form letter.
    """
    found = re.search(r"\b(?:about|of|on|regarding|describing|for|named|called)\s+(.+)$", clean)
    if not found:
        return ""
    words = _subject_words(found.group(1))
    if words and all(word in EMPTY_SUBJECT for word in words):
        return ""
    return " ".join(words)


# Nouns that end in s and are not plurals, so the singular form must not be invented for them.
S_FINAL_SINGULARS = frozenset((
    "christmas", "xmas", "tennis", "news", "series", "canvas", "atlas", "alias", "gas", "lens",
    "bias", "chaos", "ethics", "maths", "aerobics", "measles", "diabetes", "always",
))


def _thing(clean):
    """The subject as one bare noun, which is what the form tables are keyed by."""
    found = re.search(r"\b(?:about|of|on|regarding|describing|for|named|called)\s+(.+)$",
                      clean)
    if not found:
        return ""
    words = _subject_words(found.group(1))
    if not words:
        return ""
    word = words[-1]
    while word in CONNECTORS and len(words) > 1:
        words = words[:-1]
        word = words[-1]
    if word.endswith("'s"):
        word = word[:-2]
    while word in SUBJECT_STOP and len(words) > 1:
        words = words[:-1]
        word = words[-1]
        if word.endswith("'s"):
            word = word[:-2]
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    # A word that ends in s is not always a plural: "a poem about christmas" was "a christma".
    # The endings that cannot be a plural cover most of them; the short list holds the rest.
    if (word.endswith("s") and not word.endswith(("ss", "is", "us"))
            and word not in S_FINAL_SINGULARS and len(word) > 3):
        return word[:-1]
    return word


def _named_nothing(clean):
    """True when the line names a thing with about/for and that thing is only a possessive.

    "write a rap for my card" names the card, not "my": the subject comes out empty, and a form
    that falls back to the bare word then writes "A rap about my". So the form stands down and
    the line gets the same honest answer it got before the card phrases were narrowed.
    """
    found = re.search(r"\b(?:about|of|on|regarding|describing|for|named|called)\s+(.+)$", clean)
    if not found:
        return False
    words = _subject_words(found.group(1))
    return bool(words) and all(word in EMPTY_SUBJECT for word in words)


def _lines(lines, lead=None):
    """A poem as one line of reply: the form on the first line, then the lines themselves."""
    return (lead + "\n" if lead else "") + "\n".join(lines)


def _haiku(memory, understood):
    """A haiku about the thing named, counted 5-7-5."""
    clean = understood.get("clean") or ""
    if _a_report_of_the_habit(clean):
        return _a_report_answered(clean, understood)
    subject = _subject(clean)
    if not subject:
        return _asks_for_a_verse(clean, "haiku")
    return _say("haiku", _thing(clean), subject)


def _limerick(memory, understood):
    """A limerick about the thing named, and one that scans for anything else."""
    clean = understood.get("clean") or ""
    if _a_report_of_the_habit(clean):
        return _a_report_answered(clean, understood)
    subject = _subject(clean)
    if not subject:
        return _asks_for_a_verse(clean, "limerick")
    return _say("limerick", _thing(clean), subject)


def _poem(memory, understood):
    """A short rhymed poem about the thing named."""
    clean = understood.get("clean") or ""
    if _a_report_of_the_habit(clean):
        return _a_report_answered(clean, understood)
    subject = _subject(clean)
    if not subject:
        return _asks_for_a_verse(clean, "poem", noun="rhyme" if "rhyme" in clean else "poem")
    return _say("poem", _thing(clean), subject,
                noun="rhyme" if "rhyme" in clean else "poem")


def _rhyme(memory, understood):
    """What rhymes with a word, by its ending."""
    clean = understood.get("clean") or ""
    found = re.search(r"rhyme\w*\s+(?:with|for|to)\s+([a-z']+)", clean)
    if not found:
        return None
    word = found.group(1)
    if word in NO_RHYME:
        return NO_RHYME[word]
    # "love" is an -ove ending even though its last letter is the silent e, so the word is tried
    # as typed and with the e taken off.
    bare = word[:-1] if word.endswith("e") and len(word) > 3 else word
    for ending in sorted(RHYMES_BY_ENDING, key=len, reverse=True):
        if word.endswith(ending) or bare.endswith(ending):
            picks = [one for one in RHYMES_BY_ENDING[ending] if one != word][:5]
            if picks:
                return ("Words that rhyme with *%s*: %s. For a poem, the easiest thing is to put "
                        "*%s* at the end of a line and pick the rhyme that says what you mean."
                        % (word, _list_words(picks), word))
    return None


def _story_idea(memory, understood):
    """Two story ideas, picked by the line so the same question gets the same answer."""
    clean = understood.get("clean") or ""
    seed = sum(ord(one) for one in clean) or 1
    first = STORY_IDEAS[seed % len(STORY_IDEAS)]
    second = STORY_IDEAS[(seed + 7) % len(STORY_IDEAS)]
    return ("Two to start with:\n- %s\n- %s\nWhich one sounds like yours? I can help you find "
            "the first scene, or the thing that goes wrong." % (first, second))


BRIGHT = ("sun", "birthday", "friend", "summer", "spring")
CALM = ("garden", "tea", "sea", "night", "morning")
FORMS = {"haiku": HAIKU, "limerick": LIMERICKS, "poem": POEMS}


# The lead a verse is written under: "A short story about a dog:", "A haiku about the sea,
# 5-7-5:". Read off the bot's own reply, it says which form was written without another word
# list to keep, and it is what a second one asked for in three words ("one more about a dog",
# "another one about a dog") has to be written in.
_A_VERSE_LEAD = re.compile(
    r"^\s*(?:A|An)\s+(?:\w+\s+){0,2}(story|poem|haiku|limerick|rap|song|rhyme)\b", re.I)


def _the_form_last_time(memory):
    """The form of the verse the last exchange was about, if it was about one."""
    turns = [one for one in (memory.get("turns") or [])[-2:] if isinstance(one, dict)]
    for turn in reversed(turns):
        bot = str(turn.get("bot") or "")
        written = _A_VERSE_LEAD.match(bot)
        if written:
            return written.group(1).lower()
        said = (str(turn.get("user") or "") + " " + bot).lower()
        for form in ("haiku", "limerick", "poem"):
            if form in said:
                return form
    return None


def _lead(form, subject):
    if form == "haiku":
        return "A haiku about %s, 5-7-5:" % subject
    if form == "limerick":
        return "A limerick about %s:" % subject
    return "A short poem about %s:" % subject


def _offer(form, subject):
    """The one detail the verse needs, for a subject a fixed-rhyme form cannot carry."""
    name = {"haiku": "haiku", "limerick": "limerick", "rap": "rap", "song": "song",
            "story": "story"}.get(form, "poem")
    return ("A %s about %s needs one real thing in it: give me a sound, a smell or a day from it "
            "and I'll build the %s round that." % (name, subject, name))


def _say(form, thing, subject, noun=None):
    """The form's own answer about a thing, or None when the form has nothing for it."""
    form = noun or form
    known = (form in FORMS and thing in FORMS[form]) or thing in POEMS or thing in PEOPLE
    if not known and (thing in ABSTRACT or subject.split()[-1:] and
                      subject.split()[-1] in ABSTRACT):
        return _offer(form, subject)
    if form == "haiku":
        found = HAIKU.get(thing)
        return _lines(found, _lead(form, subject)) if found else None
    if form not in FORMS:
        # a rhyme is a poem with a different name on the front
        thing_line = POEMS.get(thing)
        lead = "A rhyme about %s:" % subject
        if thing_line:
            return _lines(thing_line, lead)
        if thing in PEOPLE:
            return _lines(WARM_POEM, lead)
        return _lines([one.format(thing=thing) for one in GENERIC_POEM], lead)
    if thing in FORMS[form]:
        return _lines(FORMS[form][thing], _lead(form, subject))
    if form != "limerick" and thing in PEOPLE:
        return _lines(WARM_POEM, _lead(form, subject))
    if form == "limerick":
        return _lines([one.format(thing=thing) for one in GENERIC_LIMERICK], _lead(form, subject))
    return _lines([one.format(thing=thing) for one in GENERIC_POEM], _lead(form, subject))


def _picked(choices, clean):
    """The same line gets the same answer, and a different line gets a different one."""
    place = sum(ord(one) for one in clean) % len(choices) if clean else 0
    return choices[place]


# "tell me a short story for a 5 year old" is not a story about a year old: the person a story is
# for is the listener, and the subject words after "for" read as the thing the story is about. A
# listener named that way gets a story written for that listener instead.
_A_LISTENER_IS_NAMED = re.compile(
    r"\b(?:for|to)\s+(?:my|our|a|the|his|her|their)?\s*(?:\d+|one|two|three|four|five|six|seven|"
    r"eight|nine|ten)\s*(?:year|yr)s?[ -]?old\b|"
    r"\b(?:for|to)\s+(?:my|our|the)\s+(?:kids?|children|child|toddler|baby|grandchildren|"
    r"grandson|granddaughter|niece|nephew|son|daughter|class|nursery)\b|"
    r"\bbedtime story\b|\bbedtime\b")

CHILD_STORIES = (
    "Once there was a small bear who could not sleep because the moon was too bright. He tried a "
    "hat, a blanket over his eyes and sleeping under the bed, and then he found that the moon was "
    "only a night light, and he was allowed to keep it on. Three minutes, one small problem, and "
    "the bear is safe at the end - which is the whole of what a story for a five year old needs.",
    "The duck who had forgotten how to quack found a frog who could only croak, and between them "
    "they made a noise that woke the whole pond. It ends with everybody laughing rather than with "
    "anybody taught a lesson. About three minutes long, said slowly, with a quack every time the "
    "duck tries.",
    "A little girl put a pea in her pocket and it grew all the way up to the ceiling of her "
    "bedroom, where it turned into a beanstalk with a door in it. She did not go in, because it "
    "was bedtime, and that is the end. A story for a five year old wants one idea, one small "
    "problem, and a safe last line rather than a moral.",
)


# The child pool above has no slot for a subject, so a child listener with a subject named after
# it was handed the adult opening: "a bedtime story for my son about a dinosaur" came back as a
# dinosaur carried from flat to flat for eleven years, which is the wrong register for the listener
# and the wrong story for a bedtime. These keep the one idea, one small problem and safe last line
# of the pool, with the subject slotted in.
CHILD_STORY_OPENINGS = (
    "Once there was a {thing} that could not sleep because the moon was too bright.\n"
    "It tried a hat, a blanket over its eyes and sleeping under the bed, and then it found that "
    "the moon was only a night light, and it was allowed to keep it on.",
    "There was a {thing} in the garden one Tuesday, and nobody in the house had seen one before.\n"
    "The dog said hello first, then everybody did, and by bedtime it had a name and a place by "
    "the door.",
    "A little girl found a {thing} in her pocket one morning and it grew all the way up to the "
    "ceiling of her bedroom.\n"
    "It was bedtime, so she did not climb it. She said goodnight to it instead, and in the "
    "morning it was exactly the same size.",
)


def _the_listener_lead(clean):
    """How a story for the child in the line is introduced."""
    age = re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b", clean)
    return "A short one for a child" if not age else "A short one for a %s year old" % age.group(1)


def _a_story_for_the_listener(clean):
    """A story for the child named in the line, seeded by the line's own words."""
    return _the_listener_lead(clean) + ": " + _picked(CHILD_STORIES, clean)


def _a_child_story_about(clean, thing):
    """A story for the child named in the line, about the thing that is also named."""
    opening = _picked(CHILD_STORY_OPENINGS, clean + thing)
    return _the_listener_lead(clean) + ": " + opening.format(thing=thing)


# A question about stories is not a request for one: "what makes a good story" and "how long should
# a story be" were handed a made-up story the moment the story row started reaching them.
_ASKS_ABOUT_A_STORY = re.compile(
    r"\b(?:what makes|how long (?:should|do|does|is)|how (?:do|can|would) (?:i|you|we) "
    r"(?:write|start|plan)|how to (?:write|start|plan)|what should (?:a|my|the) story|"
    r"where do i start|story structure|structure a story)\b", re.I)

# A story somebody reports is not a story to write either. "my son keeps telling the same story"
# and "we tried a bath and a story" were answered with a made-up one, which is the bot talking over
# the person. The shapes below are the ones that ask for a story; a line with none of them is
# somebody else's turn to answer.
ASKS_FOR_A_STORY = re.compile(
    r"\btell\s+(?:me|us)\b|\btell\s+(?:\w+\s+){0,3}(?:a |another |one more )?(?:story|stories|tale)\b"
    r"|\b(?:give|write|read|make up|do|need|want|hear|fancy|have|get)\w*\s+"
    r"(?:\w+\s+){0,3}(?:story|stories|tale)\b|\b(?:story|stories|tale)\s+(?:about|for|of)\b|"
    r"\bbedtime story\b|\banother story\b|\bone more story\b|\bstor(?:y|ies) please\b|"
    r"\b(?:short|quick|little)\s+(?:story|stories|tale)\b|"
    r"\b(?:any|some) (?:good |short |quick |nice |funny )?(?:story|stories)\b")

# "my son keeps telling the same story about school" has the asking shape - a story and the word
# for it - but the telling already happened, so a hearing word means the story is in the room,
# unless the line also asks the bot for one.
A_STORY_ALREADY_TOLD = re.compile(r"\b(?:telling|tells|told|reading|reads|read|heard|hears)\b")
# The hearing word and the request can be in the same line: "i read him a story every night,
# write one for his birthday" reports the habit and then asks for a story, and the request is
# what the person wants answered. A line that asks for one to be written, told, read or given
# is an ask whatever it also reports, so the ask is looked for first.
A_NEW_ONE_ASKED_FOR = re.compile(
    r"\b(?:write|wrote|make\s+up|made\s+up|compose|draft)\s+(?:me\s+|us\s+)?(?:one|another|a|an|some)\b"
    r"|\b(?:tell|read|give)\s+(?:me|us)\b"
    r"|\b(?:one\s+more|another\s+one|one\s+other)\b"
    r"|\bwant\s+(?:a|another|one\s+more)\b", re.I)
ASKS_THE_BOT = re.compile(r"\b(?:tell|read)\s+(?:me|us)\b")
# "did you hear the story about the dog" is somebody asking whether the bot heard their news, and
# the bot answered with a made-up story about a dog. "hear" cannot go in the list above because
# "i want to hear a story" is a request: only the question shape means the story is there already.
A_STORY_ALREADY_HEARD = re.compile(r"\b(?:did|do|have|has|had) you (?:ever )?hear(?:d)?\b")


# ...and the answer to news is that the bot has not heard it, not a story it makes up on the spot.
HEARD_IT_ALREADY = (
    "I haven't heard that one - go on, tell me. You'll tell it better than I could make it up.",
    "No, and now I want to. Go on.",
)


def _a_story_is_asked_for(clean):
    """True when the line asks for a story rather than reporting one."""
    if not ASKS_FOR_A_STORY.search(clean):
        return False
    if ASKS_THE_BOT.search(clean):
        return True
    if A_STORY_ALREADY_HEARD.search(clean):
        return False
    if A_NEW_ONE_ASKED_FOR.search(clean):
        return True
    return not A_STORY_ALREADY_TOLD.search(clean)


_SECOND_STORY = re.compile(
    r"^(?:and|then|also|ok|okay|now|so)?\s*(?:one more|one other|another one|one)\s+about\b",
    re.I)
_A_STORY_WORD = re.compile(r"\b(?:story|stories|tale|tales)\b", re.I)


def _the_line_to_read_for_a_story(understood):
    """The words to take the subject from, which are not always the reading's own.

    A follow-up is understood with the line it leans on folded in, and for "another one about a
    ship" after "tell me a story about a lighthouse" the reading comes back as "another one about
    a ship tell story": honest about what the chat is on, useless as a subject. The typed line is
    the one that names the ship, so when the line asks for a second story the typed words are the
    ones read - "A short story about a ship", not "A short story about a ship tell".
    """
    typed = str((understood or {}).get("text") or "").strip()
    clean = str((understood or {}).get("clean") or "")
    if typed and typed != clean and _SECOND_STORY.search(typed.lower()):
        return typed
    return clean


def _the_story_was_just_told(memory):
    """True when the last thing the bot said was a story, which is what "one more" points at."""
    for turn in reversed(list((memory or {}).get("turns") or [])):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("bot") or "")
        if said:
            return bool(re.search(r"\bstory\b", said, re.I))
    return False


# "a story about anything" names no subject: the word after "about" is where the subject would be,
# and a placeholder there means the person asked for a story and left the choice to us.
_PLACEHOLDER_SUBJECT = frozenset((
    "anything", "something", "nothing", "anyone", "someone", "somebody", "everyone",
    "everybody", "anybody", "nobody", "whatever", "whichever", "whoever", "it", "that", "this",
    "more", "else", "surprise", "me", "them", "us",
))


def _a_placeholder_word(subject):
    """True when what follows "about" is a placeholder rather than a thing."""
    words = subject.split()
    if not words:
        return True
    return words[0].strip(".,!?;:'\"").lower() in _PLACEHOLDER_SUBJECT


# A line that reports what somebody does with a verse is not a request for one. "my son keeps
# telling the same story", "we tried a bath and a story", "she tells me the same story every time"
# and "he keeps making up raps" are the person telling the bot about their evening, and each was
# answered with a story or a rap ("Here is one, made up on the spot", "A rap about small thing").
# The report is read from its own shape rather than from a list of the forms, so a new form is
# covered the day it is written: somebody doing the thing (tried/read/told/watched/sang/heard),
# keeps/kept doing it, or a named person who tells/reads/sings/makes it up. A line that asks as
# well as reports keeps the form - "i read him a story every night, write one for his birthday"
# wants a story - so the gate turns on a report with no ask of its own beside it.
REPORTS_ON_A_FORM = re.compile(
    r"\b(?:i|we|he|she|they)\s+(?:tried|read|told|watched|listened\s+to|sang|heard)\b"
    r"|\b(?:keeps?|kept)\s+(?:telling|reading|saying|making|watching|singing|doing)\b"
    r"|\b(?:my|our|his|her|the)\s+\w+\s+(?:tells?|told|reads?|sings?|sang|made\s+up)\b"
    r"|\b(?:he|she|they)\s+(?:tells?|reads?|sings?|makes?\s+up|told|read|sang)\b")
ASKS_FOR_ONE = re.compile(
    r"\b(?:write|written|make\s+up|compose|draft|give\s+me|tell\s+me|read\s+me|"
    r"can\s+you|could\s+you|would\s+you|i\s+(?:want|need|would\s+like)|"
    r"any\s+ideas?|what\s+(?:about|should))\b")


def _a_report_of_the_habit(clean):
    """True for a line that reports the form rather than asking for one."""
    line = str(clean or "")
    return bool(REPORTS_ON_A_FORM.search(line)) and not ASKS_FOR_ONE.search(line)


def _the_last_line_reported_a_form(memory):
    """True when the person's own last line reported a form rather than asking for one."""
    turns = [one for one in (memory or {}).get("turns") or [] if isinstance(one, dict)]
    for turn in reversed(turns):
        said = str(turn.get("user") or "")
        if not said:
            continue
        # the line being answered is not the one before it
        if not str(turn.get("bot") or "").strip() and turn is turns[-1]:
            continue
        return _a_report_of_the_habit(said)
    return False


# The report is answered by the form's own module rather than passed on. Standing the verse down
# and returning None left the line to the next thing that matched it, and what matched
# "he keeps making up raps" was a card about creams, on the shared verb "keeps": "Most creams keep
# about 30 months sealed and 12 months once they are open". "they keep singing the same song" got
# "I'm listening - say more if it helps" instead, which has nothing of the line in it. The form
# module knows what the report is about, so it says back what the person said and asks the one
# thing a friend would ask. The pool is picked by the line, so the same line always gets the same
# answer, and each form has its own.
REPORT_BACK = {
    "story": (
        "A story they ask for again and again is the good kind - they know it by heart by now. "
        "What's it about?",
        "That's a bedtime routine doing its job. Does it have to be word for word, or does it "
        "change a bit each night?",
        "The same story over and over is how a favourite works - they are hearing the bits they "
        "like. Do you get a say in which one?",
        "The same story at the same time every night is a habit worth having. Do they join in on "
        "the lines they know yet?",
    ),
    "rap": (
        "Raps made up at home are words and rhythm at the same time, which is a good sign. What do "
        "they rap about?",
        "Making up raps is how a lot of people find their voice. Does any of it stick, or is it "
        "all gone the moment it's said?",
        "A kid with a rap habit is usually listening to words in a different way to everyone else. "
        "Do you get to hear them?",
    ),
    "song": (
        "The same song on repeat is exactly how a favourite works. Which one is it?",
        "A song sung the same way every time has properly stuck. Do you join in, or is it theirs "
        "alone?",
        "That's a good sign - singing the same thing over is how words and tune get learned. Is it "
        "one you know too?",
    ),
    "poem": (
        "Poems made up at home are somebody playing with words, which is worth a lot. Do you get to "
        "hear them?",
        "A child writing poems is noticing things most people walk past. What are they about?",
        "That's the age poems start, usually - bad ones, brilliant ones, all of them out loud. Does "
        "she read them to you?",
    ),
    "haiku": (
        "Haikus at home is a lovely habit - counting the sounds is half the fun of it. Do you get "
        "to hear them?",
        "A haiku habit means someone has been listening closely to how a line sounds. What do they "
        "write them about?",
    ),
    "limerick": (
        "Limericks are the form people make up without being asked, so that habit usually runs. Do "
        "you get the rude ones?",
        "A limerick habit at home is a good sign - the rhythm does most of the work and the joke "
        "does the rest. Who do they do them for?",
    ),
    "rhyme": (
        "Rhymes made up as they go is how the sound of words gets learned. Do they keep them, or "
        "does each one vanish?",
        "A rhyming habit is a good one to have around. Do you get to hear the new ones?",
    ),
}

# A report of one telling is not a habit, and the answers are not interchangeable: "she told me a
# story" was answered with "The same story over and over is how a favourite works", which asks
# about a nightly routine the person never mentioned. The words for a habit are what separate the
# two, so the pool is picked by them.
A_REPEATED_REPORT = re.compile(
    r"\bkeeps?\b|\bkept\b|\b(?:the\s+)?same\b|\bevery\s+(?:night|day|time|evening|week)\b"
    r"|\bagain\s+and\s+again\b|\bover\s+and\s+over\b|\bevery\s+time\b|\bagain\b", re.I)

# One telling, once. The subject is often already said ("a story about her childhood"), so these
# pick up what was said rather than asking for it again.
REPORT_ONCE_BACK = {
    "story": (
        "Go on - what was the bit you liked best?",
        "Those are the good ones, the ones that turn up out of nowhere. What's stuck with you "
        "from it?",
    ),
}
REPORT_ONCE_GENERIC = (
    "A %s out of nowhere is the best kind. What was it about?",
    "I like that - a bit of a %s in the middle of the day. Did anyone else get to hear it?",
)

# Which form the report is about, from the word the person used. The first match wins, so a line
# naming two forms is answered about the one it names first in this list - a rap is a rap.
_A_FORM_IN_THE_REPORT = (
    ("haiku", re.compile(r"\bhaikus?\b", re.I)),
    ("limerick", re.compile(r"\blimericks?\b", re.I)),
    ("rap", re.compile(r"\braps?\b|\brapping\b", re.I)),
    ("song", re.compile(r"\bsongs?\b|\bsing(?:ing|s|)\b|\bsang\b", re.I)),
    ("rhyme", re.compile(r"\brhym(?:e|es|ing)\b", re.I)),
    ("poem", re.compile(r"\bpoems?\b|\bpoetry\b", re.I)),
    ("story", re.compile(r"\bstor(?:y|ies)\b|\btales?\b", re.I)),
)


# A reading routine is not a report about a form. "i read him a story every night" is the habit
# the reading card answers ("Ten minutes a night, the same time, with them reading out loud to
# you"), and a warm question back would drop that advice for a line that asked for nothing else.
# Only the making-up and the telling habits are answered here.
A_READING_ROUTINE = re.compile(r"\bread(?:s|ing)?\b|\blistened\s+to\b|\bwatched\b", re.I)
A_MAKING_UP = re.compile(r"\bmak(?:e|es|ing)\s+up\b|\bmade\s+up\b|\bsing|\btells?\b|\btelling\b",
                         re.I)


# A report with a question beside it is a question. The reading of a follow-up has the line it
# leans on folded in, so the report can be in the chat rather than in this line: after "my son
# keeps telling the same story about school", "should i just let him" is read as the whole of that
# plus the question, and the report answer went out again as if the question had not been asked.
# The question is the person's turn, so it is answered somewhere else.
A_QUESTION_BESIDE_THE_REPORT = re.compile(
    r"\b(?:should|shall|can|could|would|will|is|are|am|do|does|did|what|why|how|when|where|who"
    r"|which|if)\b", re.I)


def _a_report_answered(clean, understood=None):
    """What the form's own module says to a line that reports the habit, or None."""
    if not _a_report_of_the_habit(clean):
        return None
    line = str(clean or "")
    if A_QUESTION_BESIDE_THE_REPORT.search(line):
        return None
    if A_READING_ROUTINE.search(line) and not A_MAKING_UP.search(line):
        return None  # a reading routine has its own card, and it is the better answer
    form = "story"
    for name, shape in _A_FORM_IN_THE_REPORT:
        if shape.search(line):
            form = name
            break
    if not A_REPEATED_REPORT.search(line):
        once = REPORT_ONCE_BACK.get(form)
        if once:
            return _picked(once, line)
        return _picked(REPORT_ONCE_GENERIC, line) % form
    return _picked(REPORT_BACK[form], line)


def _story(memory, understood):
    """A very short story about the thing named, or about a small thing if none is named."""
    clean = _the_line_to_read_for_a_story(understood)
    if _a_report_of_the_habit(clean):
        return _a_report_answered(clean, understood)
    if (_the_last_line_reported_a_form(memory) and not ASKS_FOR_ONE.search(clean)
            and not _SECOND_STORY.match(str((understood or {}).get("plain") or "").strip())):
        # The chat is on a report and this line asks for nothing of its own: the story word in
        # the reading came from the line before it, and a made-up story is not an answer to
        # "is that just what kids do".
        return None
    # `plain` is the line as typed; `text` and `clean` are the reading, which for a follow-up has
    # the line it leans on folded in ("is the tell story every just what kids do").
    typed = str((understood or {}).get("plain") or (understood or {}).get("text") or "")
    if typed and typed != clean and not _A_STORY_WORD.search(typed):
        # A story word that came from an earlier line is what the chat is on, not what this line
        # asks for: after "she tells me the same story every time", the follow-up "is that just
        # what kids do" was answered with a made-up story because the folded reading carried the
        # word. A second story asked for without the word is still a story.
        if not _SECOND_STORY.match(typed.strip()) or not _the_story_was_just_told(memory):
            return None
    if not _A_STORY_WORD.search(clean):
        # Asked for without the word, so the last exchange has to be the story it points at - and
        # a phrase that names no form is a story only when the story was just told, because after
        # a turn about dogs "one more about the dog" wants more about the dog.
        if not _SECOND_STORY.match(clean.strip()):
            return None
        if not _the_story_was_just_told(memory):
            return None
    if _ASKS_ABOUT_A_STORY.search(clean):
        return None
    if A_STORY_ALREADY_HEARD.search(clean) and ASKS_FOR_A_STORY.search(clean):
        return _picked(HEARD_IT_ALREADY, clean)
    if not _a_story_is_asked_for(clean):
        return None
    if _A_LISTENER_IS_NAMED.search(clean):
        # A listener named before the subject is not the subject. "a bedtime story for my son
        # about a dinosaur" was a story about a son, because _thing takes the earliest cue word in
        # the line; cutting at the about-phrase leaves the dinosaur. A line that names no subject
        # after the listener is a story for the listener, which is what the child-story pool is.
        #
        # A placeholder is not a subject either: "tell me a bedtime story about anything" is a
        # bedtime story that names nothing, and it was a story about an "anything" that had been
        # carried from one flat to another. The pool is the answer to every one of those.
        named = re.search(r"\b(?:about|of|on|regarding)\s+(?P<subject>\S.*)$", clean)
        if not named or _a_placeholder_word(named.group("subject")):
            return _a_story_for_the_listener(clean)
        # A child listener keeps the child register even when a subject is named: the adult
        # openings are four lines about a thing arriving, and a bedtime story for a six year old
        # wants the one idea and the safe last line instead, with the subject in it.
        child_thing = _thing(named.group(0))
        if child_thing and not _a_placeholder_word(child_thing):
            return _a_child_story_about(clean, child_thing)
        return _a_story_for_the_listener(clean)
    thing = _thing(clean) or GENERIC_STORY_THING
    if _a_placeholder_word(thing):
        # "tell me a story about anything" was a story about an anything: the choice of subject
        # is the bot's to make, and it is made the way a story with no subject at all is made.
        thing = GENERIC_STORY_THING
    subject = _subject(clean)
    if subject and _a_placeholder_word(subject):
        # "a story about anything" has no subject to name back, so it is not named
        subject = None
    if thing in ABSTRACT and subject:
        return _offer("story", subject)
    lead = (STORY_LEADING["story"].format(subject=subject) if subject
            else "Here is one, made up on the spot:")
    opening = _the_opening_not_said_yet(thing, memory, clean)
    return lead + "\n" + opening


def _the_opening_not_said_yet(thing, memory, clean=""):
    """The opening for `thing`, unless it is already on the screen: then the next one.

    "tell me a story about a cat" then "another one about a cat" was the same story twice,
    and the composer framed the second one "Same answer, and it covers this" - which is what
    a machine says. A second story is another story, so the openings rotate past the ones this
    chat has already been told, and only come back round when all of them have been used.
    """
    start = sum(ord(one) for one in thing) % len(STORY_OPENINGS) if thing else 0
    told = " ".join(str(turn.get("bot") or "") for turn in ((memory or {}).get("turns") or [])
                    if isinstance(turn, dict))
    filled = dict(thing=thing, **_article_for(thing, clean=clean))
    for step in range(len(STORY_OPENINGS)):
        one = STORY_OPENINGS[(start + step) % len(STORY_OPENINGS)].format(**filled)
        if one.split("\n", 1)[0] not in told:
            return one
    return STORY_OPENINGS[start].format(**filled)


def _rap(memory, understood):
    """Four lines of rap about the thing named, with the rhyme words fixed in the template."""
    clean = understood.get("clean") or ""
    if _a_report_of_the_habit(clean):
        return _a_report_answered(clean, understood)
    if _named_nothing(clean):
        return None
    thing = _thing(clean) or NO_THING_IN_A_VERSE["rap"]
    subject = _subject(clean) or thing
    if thing in ABSTRACT:
        return _offer("rap", subject)
    lines = [one.format(thing=thing, **_article_for(thing, clean=clean)) for one in GENERIC_RAP]
    lead = (STORY_LEADING["rap"].format(subject=subject) if _subject(clean)
            else NO_SUBJECT_LEADING["rap"])
    return _lines(lines, lead)


def _song(memory, understood):
    """A verse and a chorus about the thing named."""
    clean = understood.get("clean") or ""
    if _a_report_of_the_habit(clean):
        return _a_report_answered(clean, understood)
    if _named_nothing(clean):
        return None
    thing = _thing(clean) or NO_THING_IN_A_VERSE["song"]
    subject = _subject(clean) or thing
    if thing in ABSTRACT:
        return _offer("song", subject)
    lead = (STORY_LEADING["song"].format(subject=subject) if _subject(clean)
            else NO_SUBJECT_LEADING["song"])
    return lead + "\n" + GENERIC_SONG.format(thing=thing, **_article_for(thing, clean=clean))


CHARACTER_NAME_RULES = (
    "Pick a plain first name and a surname that says what they do or where they are from: Nell "
    "Harrow, Amos Pike, Ivy Sanderson. Write down three and the story usually picks one itself - "
    "and say the full name out loud twice, because a name you stumble over is one the reader will "
    "too.",
    "A name that is easy to say and slightly odd is the one that sticks: Ruth Okonkwo, Samuel "
    "Beck, Ada Pryce. Give the villain the smoother name and the hero the plainer one, and skip "
    "the apostrophes - nobody remembers how to spell them.",
    "Old-fashioned first names worn by young people: Walter, Mabel, Agnes, Ernest. It does the "
    "work of a description in one word, because the reader fills in the corners, and it fits "
    "every kind of story from a farm to a space station.",
)


def _character_name(memory, understood):
    """A name to put in a story, with the rule that makes one easy to choose."""
    clean = str((understood or {}).get("clean") or "")
    # A villain or a hero is named by the rule written for it rather than by the line's hash:
    # "whats a good character name for a villain" got the old-fashioned first names, and the
    # smoother-name-for-the-villain rule reads made for that line.
    if re.search(r"\b(?:villain|villainess|baddie|antagonist|hero|heroine)\b", clean, re.I):
        return CHARACTER_NAME_RULES[1]
    return _picked(CHARACTER_NAME_RULES, clean)


def _nickname(memory, understood):
    """Three nicknames, two words each, in the same order every time for the same line."""
    clean = understood.get("clean") or ""
    picks = []
    for step in range(3):
        first = NICK_FIRST[(sum(ord(one) for one in clean) + step * 3) % len(NICK_FIRST)]
        last = NICK_LAST[(sum(ord(one) for one in clean) // 7 + step * 5) % len(NICK_LAST)]
        picks.append("%s %s" % (first, last))
    return ("Start with *%s*; *%s* and *%s* if it sticks. A nickname works best when it comes "
            "from something only you two know." % (picks[0], picks[1], picks[2]))


# A second one, asked for in the words people use: "one more about a dog", "another one about a
# dog", "now one about a cat", "can you do one about the sea". The extra words in front are the
# natural way to ask ("can you do one about", "go on, another one about") and none of them is a
# subject, so they are stepped over. The subject is the tail kept as the person said it: "a dog",
# not "dog", because the verse's lead reads "A short story about a dog:".
_A_SECOND_ONE = re.compile(
    r"^\s*(?:(?:and|then|also|ok|okay|now|so|go on|come on|can you|could you|would you|please|"
    r"do|give me|write|make|sing|tell|create)\b[\s,]*)*"
    r"(?:one\s+more|one\s+other|another\s+one|another|one)\b"
    r"(?:\s*(?:about|of|on)\s+(.+?))?\s*[.!?]*\s*$", re.I)
# Neither of these is a verse: "one more thing", "one more question" is the other topic they are
# on about, and "one more beer please" names a thing of its own.
_NOT_A_VERSE_ASK = re.compile(
    r"\b(?:thing|question|quick\s+question|moment|minute|sec|favour|favor|idea|point|"
    r"thought|ask|time)\b", re.I)
_ANOTHER_FORM = {"story": "_story", "poem": "_poem", "haiku": "_haiku",
                 "limerick": "_limerick", "rap": "_rap", "song": "_song", "rhyme": "_rhyme"}


def _the_second_one_asked_for(understood):
    """The subject of a "one more about X" ask: "" when the line is not one, None for a bare one.

    A bare "one more" is a second one with no subject, so it comes back as None and the caller
    writes the same form again about something of its own choosing. The typed line is `plain` on
    most turns, but a follow-up the reading has rewritten keeps its own words in `text` and the
    folded line in `plain` ("write me a limerick about a one more about a dog"), and the folded
    line cannot match a pattern anchored at both ends; every field is tried until one is the line.
    """
    for field in ("text", "plain", "clean"):
        typed = " ".join(str((understood or {}).get(field) or "").split())
        if not typed or _NOT_A_VERSE_ASK.search(typed):
            continue
        found = _A_SECOND_ONE.match(typed)
        if found:
            return (found.group(1) or "").strip(" .,!?") or None
    return ""


def _another_one(memory, understood):
    """"Another one", or "do one about the sea", after a poem: the same form, a new subject.

    A follow-up like this carries no form word of its own ("can you do one about the sea"), so
    the form has to come from the last exchange, which is the one thing the poem had that the
    question does not. A story, a rap and a song are written the same way: "one more about a dog"
    after a story is another story, and it used to be read as "one more" and handed the words
    "more tell story" as its subject.
    """
    form = _the_form_last_time(memory)
    if not form:
        return None
    second = _the_second_one_asked_for(understood)
    writer = globals().get(_ANOTHER_FORM.get(form, ""))
    if second != "" and writer:
        asked = "a %s about %s" % (form, second) if second else "a %s" % form
        said = writer(memory, {"clean": asked, "text": asked})
        if said:
            return said
    clean = understood.get("clean") or ""
    thing = _thing(clean)
    if thing:
        return _say(form, thing, _subject(clean))
    # No subject: they asked for a change of mood, so pick from the form's own list, and a
    # brighter one when they asked for something happier. A line that asks for neither is not
    # asking for a verse at all - "one more beer please" after a haiku was handed a quiet one
    # instead of the beer - so the row stands aside and the turn is read as the line it is.
    brighter = re.search(r"happ|bright|cheer|funny|nicer|lighter|lift", clean)
    calmer = brighter or re.search(r"calm|quiet|sooth|gentl|soft|slower|easier", clean)
    if not calmer:
        return None
    for key in (BRIGHT if brighter else CALM):
        if key in FORMS.get(form, {}):
            lead = "Something brighter, then." if brighter else "Something quieter, then."
            return _lines(FORMS[form][key], lead)
    return None


def _quiz_name(memory, understood):
    """Something to write on the team sheet, with the joke only when the team is a quiz team."""
    clean = understood.get("clean") or ""
    seed = sum(ord(one) for one in clean) or 1
    # "pub quiz", "quiz" and "trivia" are what make the pun land. A bare "team" is a netball,
    # football or work team as often as a quiz one, and "name ideas for our netball team" once
    # got "Trivia Newton-John". The same reply shape, without the quiz puns, fits any team.
    names = QUIZ_NAMES if re.search(r"\b(?:quiz|trivia)\b", clean) else TEAM_NAMES
    picks = [names[(seed + step) % len(names)] for step in (0, 3, 6)]
    return ("For the sheet: *%s*. Others that go down well: *%s* and *%s*."
            % (picks[0], picks[1], picks[2]))


# --- what a light fixed-rhyme verse can carry ---------------------------------
# The guard above turns a subject away from the fixed-rhyme forms when a light verse about it
# would be glib or hurtful: a grief, a lockdown, a diagnosis, a marriage breaking up, because
# then the joke lands on the person. It is not "is the word abstract" - a job, a life and a
# school are what people ask for a verse about, and for one round those were handed the ask
# instead of the verse. So the ordinary words come back here, and a verse about one of them ends
# by asking for the one real detail the template cannot know, which is what the guard was asking
# for in the first place, now with the verse there to redraft.
_ALL_ABSTRACT = ABSTRACT
_GLIB = ("lockdown", "pandemic", "covid", "coronavirus", "virus", "grief", "loss", "fear",
         "anxiety", "depression", "stress", "illness", "cancer", "dementia", "addiction",
         "recovery", "divorce", "marriage", "war", "unemployment", "poverty", "loneliness",
         "sadness", "anger", "regret", "guilt", "death", "memories", "memory", "past",
         "childhood", "friendship", "motherhood", "fatherhood", "ageing")
ABSTRACT = tuple(word for word in _ALL_ABSTRACT if word in _GLIB)
_OFFERED = tuple(word for word in _ALL_ABSTRACT if word not in _GLIB)
_OFFER_TAIL = ("\nGive me one real thing from it - a sound, a smell or a day - and I will "
               "write the {form} round that.")


def _asked_for_what_they_already_tried(understood, *things):
    """True when the thing a verse would be about is a thing the line says was already tried.

    "we tried a bath n a story" at bedtime came back as a story made up on the spot: the word
    "story" is a request to every reader that offers one, and the one line where it is not is the
    line that says the story was already tried. The reading hands over the words of the attempt
    (understanding/attempts.py), so an offer of one of them can stand down and let the line be
    answered as a report.
    """
    tried = understood.get("tried")
    if not isinstance(tried, list) or not tried:
        return False
    # A line that names a form, says it was rubbish and asks for another one in the same breath
    # ("i tried a haiku but it was rubbish can you do one") is a person wanting one, not a person
    # reporting the step they have finished with.
    if asks_for_one_more(understood.get("norm")):
        return False
    tried = {str(word).lower() for word in tried}
    for thing in things:
        for word in re.findall(r"[a-z']+", str(thing or "").lower()):
            if word in tried:
                return True
    return False


# The words a line may use to ask for each of the fixed forms, so the offer of one can stand down
# when the line says that form was already tried.
_THE_FORM_NAMED = {
    "story": ("story", "stories", "tale", "tales"),
    "poem": ("poem", "poems", "verse", "sonnet", "ode", "couplet", "rhyme", "rhymes"),
    "rhyme": ("rhyme", "rhymes", "rhyming"),
    "haiku": ("haiku", "haikus"),
    "limerick": ("limerick", "limericks"),
    "rap": ("rap", "raps", "rapping"),
    "song": ("song", "songs", "lyric", "lyrics"),
}


def _with_the_detail_asked_for(build, form):
    """The verse, then the one thing the template cannot know, asked for by name."""
    names = _THE_FORM_NAMED[form] if form in _THE_FORM_NAMED else (form, form + "s")

    def answer(memory, understood):
        if _asked_for_what_they_already_tried(understood, *names):
            return None
        reply = build(memory, understood)
        if not reply:
            return reply
        clean = understood.get("clean") or ""
        if _a_report_of_the_habit(clean):
            return reply  # a report is answered in words, and there is no verse to fill in
        subject = _subject(clean) or ""
        thing = _thing(clean) or ""
        words = subject.split()[-1:]
        if thing in _OFFERED or (words and words[0] in _OFFERED):
            reply = reply + _OFFER_TAIL.format(form=form)
        return reply
    return answer


def _a_second_one_read_first(writer, form):
    """The form's own writer, with a second-one ask ("one more about a dog") read first.

    Which entry a second-one line reaches first is not what decides the form: the row for a
    limerick answers "one more about a dog" after a limerick from the folded reading and makes it
    "A limerick about a one more", while the row for a story answers a second haiku as readily as
    a second story. The form read off the last reply is the one that answers, and a bare "one
    more" is written the same way about something the writer chooses.
    """
    def write(memory, understood):
        second = _the_second_one_asked_for(understood)
        if second != "":
            chosen = _the_form_last_time(memory)
            if chosen and chosen != form and chosen in _ANOTHER_FORM:
                # The form just written answers, or nothing does: a rhyme has no verse for
                # "stars", and the row for a story in its place wrote a story instead of the
                # rhyme the person asked for a second of.
                asked = ("a %s about %s" % (chosen, second) if second else "a %s" % chosen)
                return globals()[_ANOTHER_FORM[chosen]](memory, {"clean": asked, "text": asked})
            asked = "a %s about %s" % (form, second) if second else "a %s" % form
            said = writer(memory, {"clean": asked, "text": asked})
            # A bare "one more" with nothing written for it is read by the caller's own tables,
            # not by the folded line: handed "one more", the story writer took "more tell story"
            # for its subject.
            return said if said else (None if second is None else writer(memory, understood))
        return writer(memory, understood)
    return write


_haiku = _with_the_detail_asked_for(_haiku, "haiku")
_limerick = _with_the_detail_asked_for(_limerick, "limerick")
_poem = _with_the_detail_asked_for(_poem, "poem")
_story = _with_the_detail_asked_for(_story, "story")
_rap = _with_the_detail_asked_for(_rap, "rap")
_song = _with_the_detail_asked_for(_song, "song")

for _form_name, _form_word in (("_haiku", "haiku"), ("_limerick", "limerick"),
                               ("_poem", "poem"), ("_story", "story"), ("_rap", "rap"),
                               ("_song", "song"), ("_rhyme", "rhyme")):
    globals()[_form_name] = _a_second_one_read_first(globals()[_form_name], _form_word)
del _form_name, _form_word

# --- what to watch or read, asked by company or by a limit ---------------------
# The mood tables above answer a feeling ("something funny", "a film thats not too sad"). Most
# picks are not asked that way. People say who is in the room ("a film to watch with my parents")
# or they name the shape of the ask ("im looking for a book for me", "any series
# recommendations"), and those lines carry the medium and nothing the entries above are keyed on,
# so they were filed as a receipt ("Noted: you're looking for a film to watch with your parents")
# or answered with a punt. One table of works, tagged with who a pick suits and what it costs to
# watch, answers all of them. A second entry answers a limit said on its own ("we only have bbc
# and itv", "my mum doesnt like subtitles"), which the composer read as a complaint about a
# person rather than as what can be watched.

# What is wanted. "Something" is left out on purpose: it is the word in front of anything, and a
# key word of its own would make every "something" line a pick.
PICK_MEDIUM = ("film", "films", "movie", "movies", "series", "boxset", "box set", "show",
               "shows", "telly", "book", "books", "novel", "novels", "read", "reading",
               "documentary", "documentaries", "watch", "watching")

# How the ask is shaped, and what it asks for.
PICK_ASK = ("looking for", "looking", "after", "want", "wanted", "wanting", "fancy",
            "fancied", "in the mood", "in the mood for", "need", "need something", "ideas",
            "idea", "any ideas", "recommend", "recommended", "recommendation",
            "recommendations", "suggest", "suggestion", "suggestions", "pick", "picks",
            "decent", "good", "any", "anything", "to watch", "to read")

# Who the pick is for. A parent, a partner and a friend ask for different evenings, and the line
# says which one it is. Children are not here: a film for a child of a given age has its own
# entries, and they know what suits which age.
PICK_WHO = ("with my parents", "my parents", "parents", "with my mum", "with my dad",
            "with my mother", "with my father", "in laws", "my in laws",
            "with my wife", "with my husband", "with my partner",
            "partner", "with my girlfriend", "with my boyfriend", "with friends",
            "my friends", "friends", "for me", "for myself", "just me", "on my own",
            "by myself")

# A limit on what can be watched, said either with the ask ("a film to watch with my parents, we
# only have bbc") or on its own a turn later ("we only have bbc and itv"). Read by _pick_limit
# for the pick, and answered on its own by the `pick-limit` entry below.
FREE_TELLS = ("only have bbc", "only got bbc", "only bbc", "bbc and itv", "bbc itv",
              "just bbc", "just itv", "only itv", "freeview", "free to air", "free-to-air",
              "terrestrial", "normal telly", "normal tv", "no subscription", "no subscriptions",
              "dont have netflix", "don't have netflix", "no netflix", "canceled netflix",
              "cancelled netflix", "cant afford netflix", "can't afford netflix",
              "only iplayer", "only channel 4", "no sky", "dont have sky", "don't have sky",
              "no streaming", "dont have any subscriptions", "no disney", "no prime")
SUBS_TELLS = ("no subtitles", "not subtitles", "without subtitles", "hate subtitles",
              "do not like subtitles", "does not like subtitles", "do not do subtitles",
              "does not do subtitles", "cannot stand subtitles", "can not stand subtitles",
              "do not want subtitles", "does not want subtitles",
              "hates subtitles", "hate foreign", "hates foreign", "no foreign films",
              "nothing foreign", "dont like subtitles", "doesnt like subtitles",
              "doesn't like subtitles", "dont do subtitles", "doesnt do subtitles",
              "cant stand subtitles", "cannot stand subtitles", "cant read subtitles",
              "no reading subtitles", "turned off by subtitles", "put off by subtitles",
              "wont watch subtitles", "wont watch foreign", "doesnt want subtitles",
              "dont want subtitles", "no dubbing", "prefers dubbing")

# A country named for the watch asks for that country's films: "good french films" was answered
# with *Paddington 2*, which is a confident wrong answer to a line that named France. The words
# people type are in here, and the row a country keeps its films on is the same PICKS table, so a
# new country is one entry here and one row there - not a new entry, a new key list and a new
# reply sentence. The adjective is what the reply says; the second is what the rows are tagged
# with, so "french" and "france" reach the same films.
CINEMA = {
    "french": ("French", "France", "French"), "france": ("French", "France", "French"),
    "italian": ("Italian", "Italy", "Italian"), "italy": ("Italian", "Italy", "Italian"),
    "spanish": ("Spanish", "Spain", "Spanish"), "spain": ("Spanish", "Spain", "Spanish"),
    "german": ("German", "Germany", "German"), "germany": ("German", "Germany", "German"),
    "japanese": ("Japanese", "Japan", "Japanese"), "japan": ("Japanese", "Japan", "Japanese"),
    "korean": ("Korean", "Korea", "Korean"), "korea": ("Korean", "Korea", "Korean"),
    "chinese": ("Chinese", "China", "Mandarin"), "china": ("Chinese", "China", "Mandarin"),
    "iranian": ("Iranian", "Iran", "Persian"), "iran": ("Iranian", "Iran", "Persian"),
    "danish": ("Danish", "Denmark", "Danish"), "denmark": ("Danish", "Denmark", "Danish"),
    "brazilian": ("Brazilian", "Brazil", "Portuguese"), "brazil": ("Brazilian", "Brazil", "Portuguese"),
    "polish": ("Polish", "Poland", "Polish"), "poland": ("Polish", "Poland", "Polish"),
    "russian": ("Russian", "Russia", "Russian"), "russia": ("Russian", "Russia", "Russian"),
    "swedish": ("Swedish", "Sweden", "Swedish"), "sweden": ("Swedish", "Sweden", "Swedish"),
    "mexican": ("Mexican", "Mexico", "Spanish"), "mexico": ("Mexican", "Mexico", "Spanish"),
    "turkish": ("Turkish", "Turkey", "Turkish"), "turkey": ("Turkish", "Turkey", "Turkish"),
    "greek": ("Greek", "Greece", "Greek"), "greece": ("Greek", "Greece", "Greek"),
    "irish": ("Irish", "Ireland", "English"), "ireland": ("Irish", "Ireland", "English"),
    "nigerian": ("Nigerian", "Nigeria", "English"), "nigeria": ("Nigerian", "Nigeria", "English"),
    "vietnamese": ("Vietnamese", "Vietnam", "Vietnamese"), "vietnam": ("Vietnamese", "Vietnam", "Vietnamese"),
    "thai": ("Thai", "Thailand", "Thai"), "thailand": ("Thai", "Thailand", "Thai"),
    "israeli": ("Israeli", "Israel", "Hebrew"), "israel": ("Israeli", "Israel", "Hebrew"),
    "lebanese": ("Lebanese", "Lebanon", "Arabic"), "lebanon": ("Lebanese", "Lebanon", "Arabic"),
    "indian": ("Indian", "India", "Hindi"), "india": ("Indian", "India", "Hindi"),
    "bollywood": ("Bollywood", "India", "Hindi"),
    "czech": ("Czech", "Czechia", "Czech"), "czechia": ("Czech", "Czechia", "Czech"),
}
CINEMA_WORDS = tuple(CINEMA)

# A country adjective is usually an ordinary word doing its day job. "how do i polish out a
# scratch on my watch" was answered with *Ida* and *Cold War* - a confident wrong answer to a
# watch question - because "polish" is a country and "watch" is a medium, and nothing asked which
# one the line meant. The test is what sits right after the country word: a pronoun, an article
# or a little word means the word is a verb or a modifier ("polish out", "polish my", "french
# beans"), while a medium or an ask word after it ("french films", "french ones", "french to
# watch") means the country. A country word followed by a thing is a thing: greek yoghurt, thai
# curry and turkish delight are food, and german measles and japanese knotweed are neither films
# nor countries.
_COUNTRY_AFTER_A_LITTLE_WORD = (
    "out", "up", "off", "it", "them", "the", "my", "our", "your", "his", "her", "their",
    "a", "an", "this", "that", "these", "those", "into", "onto", "again", "properly", "well",
)
_COUNTRY_BEFORE_A_THING = (
    "yoghurt", "yogurt", "salad", "bread", "cheese", "dressing", "sauce", "takeaway",
    "food", "curry", "stew", "sausage", "ham", "mustard", "wine", "beer", "coffee",
    "meatballs", "omelette", "toast", "stick", "beans", "bath", "delight", "barber",
    "massage", "shepherd", "measles", "knotweed", "roulette", "linen", "polish", "plait",
    "onion", "fries", "toast", "press", "cuff",
)


def _a_country_is_a_country(understood):
    """False when the country word in the line is a verb, a modifier or a thing."""
    words = [w.lower() for w in (understood.get("words") or ())]
    for i, word in enumerate(words[:-1]):
        if word not in CINEMA:
            continue
        after = words[i + 1]
        if after in _COUNTRY_AFTER_A_LITTLE_WORD:
            return False
        if after in _COUNTRY_BEFORE_A_THING:
            return False
    return True


# The films themselves, one row per work, tagged with the country whose cinema it is: (title,
# country, why it is the pick). A country with no row here is said honestly rather than filled
# with the nearest famous film, because "I have not got a list for Czech cinema" is a better
# answer than *Paddington 2* to somebody who asked about Czech films.
NATIONAL_CINEMA = (
    ("Amelie", "France", "Paris, whimsical, and the film most people mean by a French film"),
    ("The Intouchables", "France", "warm, very funny, and the biggest French hit abroad"),
    ("Portrait of a Lady on Fire", "France", "slow, beautiful, and two hours of looking"),
    ("Cinema Paradiso", "Italy", "a small-town cinema and a whole life in it, and the ending lands"),
    ("The Great Beauty", "Italy", "Rome at its most beautiful and most empty"),
    ("Pans Labyrinth", "Spain", "a fairy tale under a war, and not for young children"),
    ("All About My Mother", "Spain", "Almodovar at his warmest, and it moves fast"),
    ("Good Bye Lenin", "Germany", "funny, about a whole country changing in a year"),
    ("Run Lola Run", "Germany", "81 minutes, fast, and impossible to look away from"),
    ("Spirited Away", "Japan", "the animated one everyone should see once"),
    ("Seven Samurai", "Japan", "the film every action film borrows from"),
    ("Shoplifters", "Japan", "a family that is not quite a family, and very warm"),
    ("Parasite", "Korea", "a comedy that turns into something else, and won Best Picture"),
    ("The Handmaiden", "Korea", "twisty, stylish and not for a family evening"),
    ("Crouching Tiger Hidden Dragon", "China", "the sword fights float, and the story holds"),
    ("Raise the Red Lantern", "China", "beautiful and hard, and it stays with you"),
    ("A Separation", "Iran", "two families and one lie, and nothing else needed"),
    ("Children of Heaven", "Iran", "gentle, about a lost pair of shoes, and safe for children"),
    ("Another Round", "Denmark", "four teachers and a bottle, funny and then serious"),
    ("The Hunt", "Denmark", "Mads Mikkelsen, a small town and a rumour, and it is gripping"),
    ("City of God", "Brazil", "fast, brutal and brilliant, and not a gentle evening"),
    ("Central Station", "Brazil", "a road film about a boy and a woman who writes letters"),
    ("Ida", "Poland", "80 minutes, black and white, and quiet in a good way"),
    ("Cold War", "Poland", "two people across years and borders, and the music"),
    ("Solaris", "Russia", "slow science fiction, for a patient evening"),
    ("Leviathan", "Russia", "a house, a mayor and a bottle, and very Russian"),
    ("The Seventh Seal", "Sweden", "the chess game with Death, and shorter than it sounds"),
    ("Let the Right One In", "Sweden", "a vampire film that is really about being twelve"),
    ("Roma", "Mexico", "a year in one household, and the sea scene alone is worth it"),
    ("Y Tu Mama Tambien", "Mexico", "a road trip that turns, and not for a family evening"),
    ("Once Upon a Time in Anatolia", "Turkey", "slow, patient and worth it"),
    ("Mustang", "Turkey", "five sisters, and it is angry and funny at once"),
    ("Zorba the Greek", "Greece", "the dancing-on-the-beach one, and it is about saying yes"),
    ("The Commitments", "Ireland", "a Dublin soul band, and the songs are the point"),
    ("Lionheart", "Nigeria", "Nollywood's best known, and it is on Netflix"),
    ("The Scent of Green Papaya", "Vietnam", "quiet and beautiful, and very little happens"),
    ("Uncle Boonmee", "Thailand", "slow and strange, for somebody who likes that"),
    ("Waltz with Bashir", "Israel", "animation about memory and war, and it is not gentle"),
    ("Capernaum", "Lebanon", "a child sues his parents, and it is hard but worth it"),
    ("Lagaan", "India", "a village cricket match against the British, and nearly four hours"),
    ("Dangal", "India", "a father, two daughters and wrestling, and it is a true story"),
)

# A kind of film is a shelf, not a sentence per kind: "a christmas film", "something western" and
# "good action films" all name one, and the shelf is the answer. (minutes, why it is the pick) -
# the runtime is in the row because half the reason people pick a kind is how long they have.
FILM_KINDS = {
    "christmas": ("Christmas", "a Christmas film", (
        ("The Muppet Christmas Carol", 85, "funny, warm, and the songs stay with you"),
        ("It's a Wonderful Life", 130, "the one everyone ends on, and it earns the ending"),
        ("Home Alone", 103, "daft, and everyone in the room has seen it before"),
    )),
    "musical": ("musical", "a musical", (
        ("Singin' in the Rain", 103, "the one that makes people like musicals"),
        ("La La Land", 128, "bright, sad at the end, and easy to follow"),
        ("The Sound of Music", 174, "long, which is what a wet Sunday wants"),
    )),
    "action": ("action", "an action film", (
        ("Die Hard", 132, "still the best one, and it is a Christmas film too"),
        ("Mad Max: Fury Road", 120, "one long chase, and it never drags"),
        ("John Wick", 101, "short, clean, and all about the fighting"),
    )),
    "western": ("western", "a western", (
        ("High Noon", 85, "short, tense, and over in an hour and a half"),
        ("True Grit", 110, "the newer one: funny, and a girl who outtalks everyone"),
        ("Unforgiven", 130, "the one that turns the western over"),
    )),
    "superhero": ("superhero", "a superhero film", (
        ("Spider-Man: Into the Spider-Verse", 117, "the animation is worth it on its own"),
        ("The Incredibles", 115, "works for adults and children in the same room"),
        ("Guardians of the Galaxy", 121, "funny first and superhero second"),
    )),
}
# A kind can be said as a noun or as an adjective, and the matcher folds a plural onto its stem but
# not one part of speech onto another, so "animated" and "animation" are two keys onto one shelf
# with the rows written once. A documentary is deliberately not one of these: `PICK_OTHER_MEDIUM`
# says a documentary is another medium, and the true-story mood row already answers for it.
ANIMATION_ROWS = (
    ("Spirited Away", 125, "the one that turns people who say they do not like animation"),
    ("The Mitchells vs the Machines", 114, "fast, funny, and a robot apocalypse a family can watch"),
    ("Toy Story", 81, "short, and it still holds up"),
)
# A thriller is a kind of film people ask for by name, and its three picks are the tense ones
# rather than the scare and the laugh the mood rows already carry.
FILM_KINDS["thriller"] = ("thriller", "a thriller", (
    ("Sicario", 121, "cold and relentless, and it never lets you settle"),
    ("Prisoners", 153, "a kidnapping and a father who will not stop looking"),
    ("Gone Girl", 149, "a marriage thriller that keeps turning on you"),
))
FILM_KINDS["animated"] = FILM_KINDS["animation"] = (
    "animated", "an animated film", ANIMATION_ROWS)
# A western said as "a cowboy film" is the same shelf, and the word is not a kind of its own.
FILM_KINDS["cowboy"] = FILM_KINDS["western"]
# "christmassy" is the adjective people use for that shelf, and it is the same shelf.
FILM_KINDS["christmassy"] = FILM_KINDS["christmas"]

FILM_KIND_WORDS = tuple(FILM_KINDS)


def _kind_words(kind):
    """Every way a line can name this shelf: the key, its plural, and how the shelf says it."""
    label, said_as, _rows = FILM_KINDS.get(kind, ("", "", ()))
    words = {kind, kind + "s", label, label + "s", said_as}
    return frozenset(word for word in words if word)


# The refusals that come after the kind word: "the musicals are not for me", "christmas films are
# out". Phrases rather than single words, for the reason the scare list is: a "not" after the kind
# usually turns down something else ("a christmas film, not a horror").
KIND_REFUSED_AFTER = re.compile(
    r"\b(?:is|are|was|were)?\s*(?:not|never)\s+(?:really\s+)?(?:for\s+(?:me|us)|my\s+(?:thing|"
    r"sort|cuppa|cup|kind)|what\s+i|something\s+i|anything\s+i|a\s+fan|keen|into\s+it)\b"
    r"|\bis\s+out\b|\bare\s+out\b|\btoo\s+much\b|\bover\s+the\s+top\b", re.I)

# A subject is turned down as often as a mood and a kind are: "i dont want to watch a documentary"
# and "i dont want a film about war" name the subject only to leave it out, and both were answered
# with the picks for that very subject - three documentaries for a person asking for anything but.
# The reader is the same one, so the subjects are read as one table and the rows that answer them
# stand down on the same test.
def _the_subject_is_wanted(understood):
    """The guard on the subject picks: a subject turned down is asking the other row."""
    for text in _own_texts(understood):
        if _a_word_is_turned_down(text, tuple(SHOW_SUBJECT_NAMES), KIND_REFUSED_AFTER):
            return False
    return True


DOCUMENTARY_WORDS = ("documentary", "documentaries", "docuseries", "docu series", "docu-series")


def _a_documentary_is_wanted(understood):
    """The guard on the documentary shelf: a documentary turned down is asking the other row.

    "documentary" is a medium and not one of SHOW_SUBJECT_NAMES, so the shared guard above never
    read it as a subject: "i dont want to watch a documentary" was answered with three
    documentaries. The word is turned down in the same shapes as any other subject, so it is read
    with the same reader.
    """
    for text in _own_texts(understood):
        if _a_word_is_turned_down(text, DOCUMENTARY_WORDS, KIND_REFUSED_AFTER):
            return False
    return True


# The kinds above are also ordinary words in a meal, a tree and a shopping list: "christmas dinner
# ideas" is a meal plan and "christmas decorations" is a box in the loft, and neither is a film
# request. An avoid word is a loose form, which is why the food is named rather than the film.
KIND_AVOID = ("dinner", "lunch", "tea", "supper", "breakfast", "recipe", "recipes", "cook",
              "cooking", "roast", "turkey", "stuffing", "pudding", "cake", "mince pies",
              "menu", "meal", "meals", "food", "sauce", "gravy", "table", "tree",
              "decorations", "decorate", "decorating", "presents", "present", "gift",
              "gifts", "cards", "shopping", "buy", "bought", "budget", "leftovers",
              "timing", "opening hours", "church", "midnight mass",
              # a kind is also a party theme and a costume
              "party", "parties", "fancy dress", "costume", "costumes", "themed")

# How a length limit is worded. The pair with the unit words in the film-length key is what makes
# "something under two hours" a limit and "hours" alone not - and the operator has to be one that
# limits a length, not a phrase holding a duration. "an hour" and "two hours" used to be in this
# list, which turned "my boss wants replies within an hour" into a shelf of short films; a bare
# duration is an ordinary thing to say and only "under", "max" and their cousins make it a limit.
# A genre said with the medium is a shelf of its own as well - "a scifi film", "a space film"
# have their picks in `film-space` - so a limit on the evening is read off that shelf rather than
# off the length table. These are the genre keys the film rows already answer.
#
# The genres with no shelf of their own are here too, and for the other half of the same reason:
# "a war film under two hours" names a shelf this table cannot make, and the length table would
# answer it with three films from every corner of the table ("The King's Speech, Spider-Man or
# Arrival") that are not war films at all. A genre word nobody has picks for stands the table
# down, so the line goes wherever it went before rather than to a wrong list. A shelf added for
# one of these wants its key taken out of this tuple, not a second list.
FILM_GENRE_WORDS = ("space", "sci-fi", "sci fi", "scifi", "science fiction",
                    "war", "heist", "spy", "gangster", "biopic", "romcom")


def _names_a_film_genre(line):
    """True when the line names a film genre that has picks of its own (see film-space)."""
    words = " " + _plain_words(line) + " "
    return any(re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", words)
               for word in FILM_GENRE_WORDS)


LIMIT_WORDS = ("under", "less than", "no longer than", "shorter than", "max", "maximum",
               "at most")


# How long they run, in one table, shortest first: the film kind shelves above are in it too (see
# _film_minutes), so a runtime stated in one answer is the same number in the other. A limit is
# about a person's evening, so the number has to be right rather than round: *Toy Story* is 81
# and not "about 90", or somebody with 85 minutes gets a film that does not fit.
FILM_RUNTIME = (
    ("A Grand Day Out", 23, "Wallace and Gromit, and it is over in twenty minutes"),
    ("The Snowman", 27, "the animation, no words, and it is a Christmas thing"),
    ("Sherlock Jr.", 45, "Buster Keaton, silent, and funnier than most films twice as long"),
    ("Before Sunset", 80, "two people talking for the whole film, and it flies"),
    ("Ida", 80, "black and white, quiet, and 80 minutes is the whole of it"),
    ("Toy Story", 81, "the first one, and it has not dated"),
    ("Run Lola Run", 81, "loud, fast, and the same twenty minutes three times"),
    ("Locke", 85, "one man, one car, one phone call after another"),
    ("The Iron Giant", 86, "animation that adults take to as much as children"),
    ("The Muppet Christmas Carol", 85, "funny, warm, and the songs stay with you"),
    ("High Noon", 85, "short, tense, and over in an hour and a half"),
    ("Cold War", 88, "Polish, black and white, and short for how much it holds"),
    ("12 Angry Men", 96, "one room and twelve men, and it never sits still"),
    ("When Harry Met Sally", 96, "the funny one about two people taking years"),
    ("The Grand Budapest Hotel", 99, "stylish, funny, and over before anyone is tired"),
    ("Groundhog Day", 101, "funny from the first scene and easy to talk over"),
    ("Before Sunrise", 101, "the first of the two, and the one to start with"),
    ("Hunt for the Wilderpeople", 101, "daft, warm, and it moves"),
    ("John Wick", 101, "short, clean, and all about the fighting"),
    ("Paddington 2", 103, "warm, funny, and good at any age"),
    ("Singin' in the Rain", 103, "the one that makes people like musicals"),
    ("Home Alone", 103, "daft, and everyone in the room has seen it before"),
    ("True Grit", 110, "funny, and a girl who outtalks everyone"),
    ("The Mitchells vs the Machines", 114, "fast, funny, and a robot apocalypse a family can watch"),
    ("The Incredibles", 115, "works for adults and children in the same room"),
    ("Arrival", 116, "quiet science fiction, for an evening when you would rather think"),
    ("Spider-Man: Into the Spider-Verse", 117, "the animation is worth it on its own"),
    ("The King's Speech", 118, "a true story that gives everyone something to talk about"),
    ("Mad Max: Fury Road", 120, "one long chase, and it never drags"),
    ("Guardians of the Galaxy", 121, "funny first and superhero second"),
    ("Sicario", 121, "cold all the way through, and it does not let you settle"),
    ("Gone Girl", 149, "a marriage thriller that keeps turning on you"),
    ("Prisoners", 153, "a kidnapping and a father who will not stop looking"),
    ("Amelie", 122, "Paris, whimsical, and the film most people mean by a French film"),
    ("Spirited Away", 125, "the one to show someone who says they do not like animation"),
    ("La La Land", 128, "bright, sad at the end, and easy to follow"),
    ("Unforgiven", 130, "the one that turns the western over"),
    ("Knives Out", 130, "a whodunnit everyone can follow, with jokes all the way through"),
    ("It's a Wonderful Life", 130, "the one everyone ends on, and it earns the ending"),
    ("Die Hard", 132, "still the best one, and it is a Christmas film too"),
    ("Parasite", 132, "funny until it is not, and worth the two hours"),
    ("The Sound of Music", 174, "long, which is what a wet Sunday wants"),
    ("Seven Samurai", 207, "three and a half hours, and not one of them is wasted"),
)

# (title, medium, who it suits, on free-to-air telly, in English, why it is the pick). One row
# per work, so a second question about the same film is a tag and not another paragraph. "free"
# means it turns up on BBC, ITV or Channel 4 rather than only behind a subscription.
PICKS = (
    ("Paddington 2", "film", ("parents", "friends", "partner", ""), True, True,
     "warm, funny, and good at any age"),
    ("Knives Out", "film", ("parents", "friends", ""), False, True,
     "a whodunnit everyone can follow, with jokes all the way through"),
    ("The King's Speech", "film", ("parents", ""), True, True,
     "a true story that gives everyone something to talk about afterwards"),
    ("The Grand Budapest Hotel", "film", ("friends", "partner", ""), False, True,
     "stylish and funny, and under 100 minutes"),
    ("The Best Exotic Marigold Hotel", "film", ("parents",), True, True,
     "gentle comedy about starting again at 60, which parents usually take to"),
    ("When Harry Met Sally", "film", ("partner",), True, True,
     "the funny one: two people taking years to notice each other"),
    ("Groundhog Day", "film", ("friends", ""), True, True,
     "funny from the first scene and easy to talk over"),
    ("Hunt for the Wilderpeople", "film", ("friends", "partner"), False, True,
     "daft, warm and over before anyone gets restless"),
    ("Arrival", "film", ("partner", ""), False, True,
     "quiet science fiction, for an evening when you would rather think"),
    ("Happy Valley", "series", ("parents", ""), True, True,
     "tense British crime, six episodes a series, and it grips from the first ten minutes"),
    ("Ghosts", "series", ("parents", "friends", "partner"), True, True,
     "silly and warm in 25-minute episodes, which is what a mixed room wants"),
    ("The Detectorists", "series", ("parents", "friends"), True, True,
     "gentle and very funny, and nothing in it is upsetting"),
    ("The Bear", "series", ("friends", ""), False, True,
     "short, intense episodes that pull you through a whole series in a weekend"),
    ("The Thursday Murder Club", "book", ("parents", ""), True, True,
     "funny with short chapters, so it is easy to pick up and easy to put down"),
    ("Lessons in Chemistry", "book", ("friends", "partner"), True, True,
     "funny and big-hearted, and everyone in a book group has an opinion on it"),
    ("The Midnight Library", "book", ("", "partner"), True, True,
     "gentle and hopeful, and readable in a few evenings"),
    ("Small Things Like These", "book", ("parents",), True, True,
     "under 120 pages and it stays with you for weeks"),
    ("The Silent Patient", "book", ("friends",), True, True,
     "a twist that lands, which is what a reader who wants to be gripped is after"),
)

# A mood word in one of these lines is the mood tables' question, so this entry stays out of it:
# "a film thats not too sad" already has an answer, and one pick row for every feeling would be
# a second, worse copy of it. Only the words that name a feeling are here. MOOD_WORDS also holds
# the glue of the phrases it was built from ("hard", "go", "put", "seat"), and an avoid word is a
# loose form, so a pick turned away for the word "hard" in passing would be a worse fault than
# the one this entry fixes.
PICK_MOODS = ("sad", "crying", "cry", "tears", "tearjerker", "heartbreaking", "weepy", "sob",
              "devastating", "emotional", "moving", "funny", "laugh", "laughing", "laughs",
              "hilarious", "comedy", "comedies", "sitcom", "scary", "scariest", "scares",
              "horror", "frightening", "creepy", "terrifying", "spooky", "halloween",
              "uplifting", "uplifted", "cheerful", "heartwarming", "happy", "hopeful",
              "comforting", "gripping", "unputdownable", "exciting", "addictive", "tense",
              "short", "shortest", "twisty", "romantic", "rom com", "romcom", "lighthearted",
              "cosy", "cozy", "easy watching", "nothing heavy", "switch off", "feelgood",
              "feel good", "thought provoking", "mind bending", "page turner", "true story")

# The shared "not this answer" lists, read as they are except for one word: an avoid word is
# matched by its loose form, "boxing" folds to "box", and "boxset" reads as "box", so keeping it
# would turn every boxset line away from the pick that is meant to answer it.
_PICK_AVOID = tuple(word for word in WATCHING + SPORT + CHILD + SCREEN_TIME + NOT_WATCHING
                    + MAKING_UP if word != "boxing")


# A medium the table has nothing in. It holds films, series and books, so a line that asks for a
# documentary, a podcast or an audiobook passes rather than being handed the nearest thing to it:
# "any good documentaries" is not a request for Paddington 2.
PICK_OTHER_MEDIUM = ("documentary", "documentaries", "docuseries", "docu series", "podcast",
                     "podcasts", "audiobook", "audiobooks", "true crime", "nature", "stand up",
                     "standup", "anime", "reality tv", "soap")

# A subject is the question, and no row in the table has a subject in it. "a book about the war"
# and "a documentary about space" are asks for a thing about something, so they pass: a murder
# mystery for a book about the war, or Paddington 2 for space, is confident and wrong, and main
# already answers "a book about space" with a book that is about space.
PICK_SUBJECT = ("about", "to do with", "set in", "based on", "starring")


# A subject is the kind of thing somebody wants to watch, and it is a different question from a
# mood: "is there a good cooking show" was handed *Happy Valley* and "what documentary should i
# watch" a film. The mood tables answer "something funny" and "something sad", where the person
# has a feeling and no subject; this is the other way round. Every pick is a real programme of
# that kind, so a subject we have nothing for passes rather than borrowing a neighbour's answer.
SHOW_SUBJECTS = {
    "cooking": ("For cooking: *MasterChef: The Professionals* is the one about the cooking itself, "
                "*The Great British Bake Off* for baking and *Saturday Kitchen* for a lazy "
                "morning, all of them long-running and easy to start anywhere."),
    "baking": ("*The Great British Bake Off* is the gentle one everybody watches, *Bake Off: The "
               "Professionals* if you want skill, and *Paul Hollywood* travel shows if it is the "
               "bread you care about."),
    "gardening": ("*Gardeners' World* is the one that tells you what to do this week, *Beechgrove* "
                  "for a colder climate and *Love Your Garden* for the before-and-after. Start "
                  "with Gardeners' World and its monthly jobs."),
    "nature": ("*Planet Earth II* is the best of them, *Blue Planet II* for the sea and "
               "*Springwatch* for British wildlife in real time. The first two look astonishing "
               "on any television."),
    "history": ("*The World at War* is the one people still cite, *Time Team* for digging and "
                "Lucy Worsley's series for the social side. All three are old and none of them "
                "feel dated."),
    "science": ("Brian Cox's *The Planets* is the easy way into space, *Forces of Nature* for "
                "how the world works, and *Chemistry: A Volatile History* if you would rather "
                "have the story of the ideas."),
    "sport": ("*The Last Dance* is the one that grips people who do not follow basketball, "
              "*Sunderland 'Til I Die* for football and *Welcome to Wrexham* if you want to "
              "enjoy one. All three are about the people, not the scores."),
    "true crime": ("*The Jinx* is the one with the ending nobody saw coming, *The Staircase* for "
                   "the long haul, and *Des* for a British one with David Tennant. All three are "
                   "about the case rather than the killings."),
    "quiz": ("*Only Connect* is the cleverest thing on television, *Would I Lie to You?* is the "
             "funniest panel show and *University Challenge* the most tense. Start with Would I "
             "Lie to You? for a group."),
    "property": ("*Grand Designs* for the build, *Location, Location, Location* for the search and "
                 "*The Great Interior Design Challenge* if you want the rooms. Grand Designs is "
                 "the one with the arguments."),
    "travel": ("*Travel Man* for a city in 48 hours, *Race Across the World* for the long way "
               "round and any of Michael Palin's journeys for the old-fashioned version. Travel "
               "Man is the short one."),
    "repair": ("*The Repair Shop* is the warm one about people mending things that matter to "
               "them, *Long Lost Family* for the other kind of mending, and *Salvage Hunters* if "
               "you like the hunt."),
    "documentary": ("*Free Solo* for one man on a cliff, *The Jinx* for a case that turns, and "
                    "*Planet Earth II* for the pictures. None of the three needs any background "
                    "to enjoy."),
}
# The words people use for each subject. "cook" is in here as a stem because the front of a
# longer line word is what matches, and a cooking programme is said as "cookery" and "cooking"
# both.
SHOW_SUBJECT_NAMES = {
    "cook": "cooking", "cooks": "cooking", "cooking": "cooking", "cookery": "cooking",
    "chef": "cooking", "chefs": "cooking", "kitchen": "cooking", "food": "cooking",
    "bake": "baking", "bakes": "baking", "baking": "baking", "bread": "baking",
    "cake": "baking", "cakes": "baking",
    "garden": "gardening", "gardens": "gardening", "gardening": "gardening",
    "gardeners": "gardening", "allotment": "gardening", "allotments": "gardening",
    "nature": "nature", "wildlife": "nature", "animals": "nature", "planet": "nature",
    "history": "history", "historical": "history", "war": "history", "wars": "history",
    "science": "science", "space": "science", "physics": "science", "universe": "science",
    "sport": "sport", "sports": "sport", "football": "sport", "rugby": "sport",
    "cricket": "sport", "tennis": "sport", "boxing": "sport", "racing": "sport",
    "crime": "true crime", "murder": "true crime", "murders": "true crime",
    "detective": "true crime", "police": "true crime",
    "quiz": "quiz", "quizzes": "quiz", "panel": "quiz", "game show": "quiz",
    "property": "property", "properties": "property", "house": "property",
    "houses": "property", "homes": "property", "renovation": "property",
    "travel": "travel", "travels": "travel", "holiday": "travel", "holidays": "travel",
    "repair": "repair", "repairs": "repair", "restoration": "repair", "antiques": "repair",
    # "documentary" is deliberately absent: it is the medium, so a documentary with no subject
    # is the a-documentary-pick row's question below, and one with a subject is that subject's.
    # It was here as
    # a subject name, and since it comes before the subject in the line the scan stopped on it,
    # so "a good documentary about space" got the no-subject card.
}
# The medium is half the key, so a line that names a subject and no medium is somebody else's
# question: "how do i cook a chicken" is cooking, not a programme.
# Only words for the medium itself: "good", "best", "any" and "something" are how a person asks
# for anything at all, and a quality word beside a subject word ("a good garden hose", "best way
# to cook a chicken", "good food for a puppy") is not a request for a programme.
SHOW_MEDIUM_WORDS = ("show", "shows", "series", "programme", "programmes", "telly", "tv",
                     "watch", "watching", "boxset", "box set", "netflix", "iplayer",
                     "documentary", "documentaries", "docuseries", "docu series")
# A word counts once, and the part it counts for is the first that asks for it, so a line whose
# medium and whose subject are the same word ("what documentary should i watch") leaves the
# subject part with nothing: the asking words are the medium there, and this row is the one for
# a documentary with no subject on it.
SHOW_DOC_ASK_WORDS = ("what", "which", "any", "good", "best", "something", "recommend",
                      "recommendation", "should i watch", "to watch", "worth watching",
                      "documentary night")

# What a subject line is not: a fault with the set, a subscription bill, a night out, and the
# cooking and gardening questions themselves, which have cards of their own.
SHOW_SUBJECT_AVOID = (
    "how do i", "how to", "how do you", "cant", "wont", "broken", "repair my", "fix",
    "my tv", "the tv", "signal", "aerial", "remote", "licence", "license", "cancel",
    "subscription", "how much", "cost", "bill", "price", "password", "account",
    "turn on", "switch on", "not working", "no picture", "settings", "channel 4",
    "theatre", "theater", "cinema", "west end", "tickets", "on at",
    # the subject's own card is the recipe or the job, not a programme about it
    "plant", "plants", "sow", "prune", "recipe", "recipes", "sauce", "oven", "roast",
    "in my garden", "my garden", "my lawn", "my allotment", "my house", "my kitchen",
    "my oven", "boil", "bake a", "bake an", "frosting",
    # a book about history is a book, and there is a shelf of those with its own answer
    "book", "books", "novel", "novels", "read", "reading", "author", "chapters",
    # a film about war is a film: the other medium's shelf, not a programme about it, and the
    # same for a movie. "i want to watch a film about war" was handed *The World at War*.
    "film", "films", "movie", "movies", "cinema", "soundtrack",
    # A line that asks what a sport is, or how it is played, names the sport as the thing to
    # understand and not as a subject to watch: "how would you explain cricket to someone who
    # only watches football" was handed the sport documentaries, because "watches" is the medium
    # and "cricket" is the subject, and both were read as what the line wanted.
    "explain", "explaining", "explained", "rules of", "the rules", "how is it played",
    "how do you play", "how does it work", "how it works", "to someone who",
    "someone who only", "never watched", "dont understand", "don't understand",
    "what does it mean",
)


# A person saying what they are doing is not asking for a programme. "what should i eat before a
# football match" then "im playing, not watching" was handed *The Last Dance*, because the subject
# in the chat is sport and the line holds the word "watching": the row cannot tell a viewer from a
# player, and the participation or the negation is what says which.
_PLAYING_NOT_WATCHING = re.compile(
    r"\b(?:i'?m|im|i am|we'?re|were|we are)\s+"
    r"(?:playing|training|coaching|refereeing|running|swimming|cycling|rowing|competing|"
    r"sailing|climbing|dancing)\b"
    r"|\bnot watch(?:ing)?\b|\b(?:dont|don't) watch\b")


def _a_programme_is_wanted(understood):
    """False when the line is about taking part, or says nobody is watching: not a show to pick."""
    text = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    return not _PLAYING_NOT_WATCHING.search(text)


def _show_subject(line):
    """The subject the line names, or "" if it names none we have picks for."""
    words = re.findall(r"[a-z0-9']+", _plain_words(line))
    for word in words:
        # "a good documentary about space" is about space, not about documentaries
        if word in SHOW_SUBJECT_NAMES and word not in SHOW_MEDIUM_WORDS:
            return SHOW_SUBJECT_NAMES[word]
    return ""


# "Is there a good cooking show" asks whether there is one, and the picks answered it with a
# list: the answer in the first sentence is the yes, and the pick follows it. "What should i
# watch about cooking" is the other way round and keeps the list it asked for.
_SHOW_YES_OR_NO = re.compile(
    r"\b(?:is|are) there (?:a|any|anything)\b|\bany good\b|\banything good\b|"
    r"\bis (?:it|that|this) (?:a )?good\b", re.I)
_SHOW_SUBJECT_LEAD = re.compile(r"^(?:For|On|About) [a-z]+: ", re.I)


def _show_about(memory, reading):
    subject = _show_subject(reading)
    if not subject:
        return None
    pick = SHOW_SUBJECTS.get(subject)
    if not pick:
        return None
    said = reading.get("clean") or reading.get("text") or "" if isinstance(reading, dict) else ""
    if _SHOW_YES_OR_NO.search(str(said)):
        return "Yes - " + _SHOW_SUBJECT_LEAD.sub("", pick)
    return pick


def _pick_kind(line):
    """Film, series or book: whichever the line asks about first."""
    for word in re.findall(r"[a-z0-9']+", _plain_words(line)):
        if word in ("book", "books", "novel", "novels", "read", "reading"):
            return "book"
        if word in ("series", "boxset", "show", "shows", "telly", "episode", "episodes"):
            return "series"
        if word in ("podcast", "podcasts"):
            return "podcast"
        if word in ("film", "films", "movie", "movies", "watch", "watching"):
            return "film"
    return ""


# "not a series", "no box sets", "anything but a movie tonight": the medium is the one being
# ruled out, and `_pick_kind` reads the word as the ask - a person who says "not a series" after
# a list of series was handed another list of series. The refusal is read before the medium is,
# and the pick moves to the other screen medium, which is the only thing the word can mean there.
_REFUSED_KIND = re.compile(
    r"\b(?:not|no|dont want|don't want|do not want|rather not|anything but|except|instead of|"
    r"i dont want|im not after|not after|sick of|tired of|bored of|watched all|seen all)\s+"
    r"(?:a|an|any|another|the|more|of|some)?\s*"
    r"(?P<kind>films?|movies?|series|box ?sets?|shows?|telly|episodes?|books?|novels?|"
    r"podcasts?)\b")


def _pick_refused(line):
    """The medium the line rules out, or "" - "not a series" is not a request for a series."""
    found = _REFUSED_KIND.search(" " + _plain_words(line) + " ")
    return _pick_kind(found.group("kind")) if found else ""


def _pick_who(line):
    """Who the evening is for, read off the line: parents, partner, friends, or "" for no one.

    "The family" is not here on purpose: with children in the house it means the children are in
    the room, and there is a row that knows what will not scare an eight-year-old, so a family line
    is left to it rather than answered with a pick for a parent.
    """
    said = " " + _plain_words(line) + " "
    if any(tell in said for tell in ("parents", " my mum", " my dad", " my mother",
                                     " my father", "in laws", "in law")):
        return "parents"
    if any(tell in said for tell in ("partner", "wife", "husband", "girlfriend",
                                     "boyfriend", "my other half")):
        return "partner"
    if any(tell in said for tell in (" friends", " mate", "mates", "everyone", "the girls",
                                     "the lads")):
        return "friends"
    return ""


def _pick_limit(line, memory=None):
    """The limit the line, or a turn just before it, puts on what can be watched.

    "we only have bbc and itv" and "my mum doesnt like subtitles" are the same kind of line: a
    constraint, not a request. A pick made a turn later still has to respect it, so the last two
    things the person typed are read too.
    """
    # Both spellings are read: "doesnt like subtitles" is typed as written and the matcher's
    # own form writes it out as "does not like subtitles", and a tell has to be found either way.
    said = " " + str(line).lower().replace("\u2019", "'") + " " + _plain_words(line) + " "
    if any(tell in said for tell in SUBS_TELLS):
        return "nosubs"
    if any(tell in said for tell in FREE_TELLS):
        return "free"
    # The memory holds the turns before this one, so the limit said a turn ago is the last of
    # them; a turn that repeats this line (a replayed answer carries its own text) is not read.
    turns = memory.get("turns") if isinstance(memory, dict) else None
    mine = _plain_words(line).strip()
    for turn in (turns or [])[-2:]:
        user = str((turn or {}).get("user") or "")
        if _plain_words(user).strip() == mine:
            continue
        said = (" " + user.lower().replace("\u2019", "'") + " " + _plain_words(user) + " ")
        if any(tell in said for tell in SUBS_TELLS):
            return "nosubs"
        if any(tell in said for tell in FREE_TELLS):
            return "free"
    return ""


# A line that asks for subtitles, as opposed to one that refuses them (SUBS_TELLS). Both read
# "subtitles", so the want is only read when no tell in SUBS_TELLS is in the line.
SUBS_WANT = ("with subtitles", "subtitled", "subtitles", "foreign film", "foreign films",
             "foreign language", "world cinema", "not dubbed")

# What the entry is keyed on. A bare "subtitles" is not here: it is in the nosubs tells as often
# as it is a want, and "no subtitles" is the pick-limit entry's question, not this one's.
SUBS_KEY = ("with subtitles", "subtitled", "foreign film", "foreign films", "foreign language",
            "world cinema")


# A refusal does not have to be the phrase listed. "doesnt like subtitles" is in SUBS_TELLS and
# "doesnt like anything with subtitles" is not, and the bare "subtitles" in SUBS_WANT then read a
# refusal as a want: asked for a film for a 78-year-old mother, "she doesnt like anything with
# subtitles" was answered "Subtitled, then: *Amelie*...". One word in the middle of a phrase is not
# a different opinion, so the negator is read where it is, up to four words before the noun.
SUBS_TURNED_DOWN = re.compile(
    r"\b(?:not|no|never|dont|doesnt|didnt|isnt|arent|without|hate|hates|hated|cant|cannot|stand|"
    r"tired of|sick of|fed up with)\b(?!\s+mind\b)(?:\s+[\w']+){0,4}\s+"
    r"(?:subtitles?|subtitled|foreign films?|foreign language|world cinema|dubbed|subs)\b")

# The want phrases that carry the want in themselves, and the bare nouns that only do when the
# line is about watching something. The nouns of the last few turns are carried into the line the
# matcher reads, so a boiler follow-up ("does that mean its dead") arrived as "does that mean its
# dead subtitles" a minute after a film question, and was answered with three foreign films. A
# bare noun is not a want on its own; "with subtitles" and "subtitled" are.
SUBS_WANT = ("with subtitles", "subtitled", "foreign film", "foreign films", "world cinema",
             "not dubbed", "subtitles please")
SUBS_WANT_IF_WATCHING = ("subtitles", "subtitle", "foreign language")
WATCHES_SOMETHING = re.compile(
    r"\b(?:film|films|movie|movies|watch|watching|watched|series|boxset|box set|cinema|telly|tv|"
    r"screen|show|shows|streaming|netflix|dvd)\b", re.I)


def _wants_subtitles(line):
    """True when the line asks for a subtitled film rather than turning one down."""
    words = " " + _plain_words(line) + " "
    if any(tell in words for tell in SUBS_TELLS) or SUBS_TURNED_DOWN.search(words):
        return False
    if any(tell in words for tell in SUBS_WANT):
        return True
    return bool(WATCHES_SOMETHING.search(words)
                and any(tell in words for tell in SUBS_WANT_IF_WATCHING))


def _cinema_of(line):
    """The country whose films the line names, or None: "good french films" names France.

    A country the person turned down is not a request for it - "no french films tonight" - so a
    negator in front of the word passes the line to whatever else can answer it.
    """
    words = " " + _plain_words(line) + " "
    for word, said in CINEMA.items():
        at = words.find(" " + word + " ")
        if at < 0:
            continue
        before = words[:at].split()[-2:]
        if any(one in NEGATORS for one in before):
            continue
        return said
    return None


def _rows_from_cinema(country):
    """The national films of one country, in the same shape as a PICKS row."""
    return [(title, "film", (), False, False, reason)
            for title, of, reason in NATIONAL_CINEMA if of == country]


def _pick_rows(kind, who, limit, count=3, country=""):
    """The three rows that fit the medium, the company and the limit, wordiest first row last.

    A limit is about watching, so it is read for films and series only: a book has no channel in
    the way of it, and telling someone a paperback is free-to-air because it says so on iPlayer
    would be a plain mistake.
    """
    if country:
        # a country named is its own cinema, and the company and the channel have no bearing on
        # it: the three rows come from that country's list, and an empty list stays empty so the
        # caller can say so
        return _rows_from_cinema(country)[:count]
    rows = [row for row in PICKS if row[1] == kind]
    if kind not in ("film", "series"):
        limit = ""
    if limit == "free":
        free = [row for row in rows if row[3]]
        rows = free or rows
    if limit == "nosubs":
        rows = [row for row in rows if row[4]] or rows
    if who:
        suited = [row for row in rows if who in row[2]]
        rows = suited + [row for row in rows if row not in suited]
    return rows[:count]


def _pick_list(rows):
    """Three picks as one sentence: the title, then the reason it is there."""
    said = ["*%s* (%s)" % (row[0], row[5]) for row in rows]
    if len(said) < 2:
        return said[0] if said else ""
    return ", ".join(said[:-1]) + " or " + said[-1]


# "Safe with a parent" said for a book is a film sentence: the verb has to follow the medium.
_PICK_PARENT_VERB = {"film": "watch with a parent", "series": "watch with a parent",
                     "book": "hand to a parent", "podcast": "put on with a parent"}


def _subs_sentence(count, language):
    """How many of them there are, and that they are subtitled, in one sentence."""
    if count == 1:
        return "It is in %s with subtitles." % language
    if count == 2:
        return "Both are in %s with subtitles." % language
    return "All three are in %s with subtitles." % language


def _pick_reply(kind, who, limit, rows, country="", language=""):
    """The pick, in the shape the line asks for: the answer first, then one line to narrow it."""
    if kind == "series":
        head = "For a series"
    elif kind == "book":
        head = "For a book"
    elif kind == "podcast":
        head = "For a podcast"
    else:
        head = "For a film"
    if who == "parents":
        head += " with your parents"
    elif who == "partner":
        head += " for the two of you"
    elif who == "friends":
        head += " with friends"
    if country:
        # "an Italian film", not "a Italian film": the article follows the word it introduces
        head = "For %s %s film" % ("an" if country[:1].lower() in "aeiou" else "a", country)
    said = head + ": " + _pick_list(rows) + "."
    if country:
        said += " " + _subs_sentence(len(rows), language)
    if limit == "free" and kind in ("film", "series"):
        said += (" All three are free-to-air rather than behind a subscription, and iPlayer and "
                 "ITVX are both free - rights move, so check iPlayer first.")
    elif limit == "nosubs" and kind in ("film", "series"):
        said += (" Nothing there needs subtitles: all of them are in English and none of them is "
                 "harder to follow than a chat show.")
    elif who == "parents":
        # A book is not watched: the sentence has to follow the medium the line asked for.
        said += " All of them are safe to %s, and none needs any explaining." % _PICK_PARENT_VERB[kind]
    elif kind == "book":
        said += " Tell me the last one you enjoyed and I'll match the next."
    else:
        said += " Say the mood and I'll narrow it down."
    return said


# A line about something already watched is a chat, not a request: "it was a good film actually"
# and "we went to the cinema on saturday" mention a film and say "good", which is what the key
# reads, so without this the pick answers a reaction with a list of three films. `good` and
# `any` cannot be taken out of the ask list (they are how half the requests are worded), so the
# reaction is what is held out.
PICK_REACT = ("it was", "that was", "we went", "i went", "i watched", "we watched",
              "i saw", "we saw", "ive seen", "i've seen", "i have seen", "i read", "ive read",
              "i've read", "we read", "i finished", "we finished", "i loved", "i enjoyed",
              "loved it", "enjoyed it", "it is on", "its on at")

# The screen-time list holds "hours" and "hour", which is what a length limit is said in: an avoid
# word is a loose form, so keeping them would stand every limit line down. The rest of the shared
# lists are kept, because a limit is still about watching rather than about the screen habits.
_LENGTH_AVOID = tuple(word for word in _PICK_AVOID + PICK_REACT + KIND_AVOID
                      if word not in ("hours", "hour", "hrs", "hr", "minutes", "minute",
                                      "mins", "min"))



def _pick_carry(memory, line):
    """The medium asked about a turn ago, for a follow-up that names none of its own.

    "what should i read next, something funny" then "anything shorter": the second line is a book
    request with the noun left out, and answered as a film it is the wrong medium. The last two
    things the person typed are read, the same way the limit is.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    mine = _plain_words(line).strip()
    for turn in (turns or [])[-2:]:
        user = str((turn or {}).get("user") or "")
        if not user or _plain_words(user).strip() == mine:
            continue
        kind = _pick_kind(user)
        if kind:
            return kind
    return ""


# "Book" is both a medium and a verb, and the key cannot tell them apart: "i still need to book the
# kennels" was read as a request for a book, and the pick stood over the honest "Worth doing" line.
# A booking names what is being booked, so a determiner or a thing straight after "book" is the
# verb, and so is "to book" or the -ed/-ing forms. A book being read never has one of those next to
# it: "a book to read on the train", "any book recommendations", "im looking for a good book".
BOOK_AS_VERB = re.compile(
    r"\bbook (?:a|an|the|my|your|our|their|his|her|its|it|us|me|them|some|two|three|four)\b"
    r"|\bto book\b|\bbooked\b|\bbooking\b")


def _pick_stands_down(line):
    """True when the line names something the table cannot hold, so the pick keeps out of it.

    Three shapes: a medium the table has no rows for, a subject ("about the war"), and children in
    the room. Each of them has a better answer elsewhere - the row that knows what suits an
    eight-year-old, or the entry that answers the subject itself - so the pick passes and lets
    that one speak.
    """
    words = " " + _plain_words(line) + " "
    if BOOK_AS_VERB.search(words):
        return True
    if any(tell in words for tell in PICK_OTHER_MEDIUM):
        return True
    if any((" " + tell + " ") in words for tell in PICK_SUBJECT):
        return True
    if any((" " + tell + " ") in words for tell in PICK_REACT):
        return True
    return any(tell in words for tell in ("family", "the kids", "kids", "children", "child"))


# A length is a number and a kind word is also an ordinary word, so both film rows took lines
# about something else: "a train journey under two hours" was handed a shelf of short films and
# "a western restaurant" got *High Noon*. Neither row can ask for a film word in its key - "a
# film under two hours" and "something under two hours" are the same ask - so the other subject
# is what stands the row down. It only does so when the line names no film at all: "a film for
# the flight that is under two hours" is still a film ask and keeps its shelf.
OTHER_SUBJECT = ("journey", "journeys", "train", "trains", "walk", "walks", "drive", "drives",
                 "flight", "flights", "game", "games", "board game", "board games", "lecture",
                 "lectures", "meeting", "meetings", "shift", "shifts", "page", "pages",
                 "restaurant", "restaurants", "menu", "menus", "music", "spotify", "album",
                 "albums", "playlist", "playlists", "plan", "plans", "planning",
                 "book", "books", "novel", "novels", "podcast", "podcasts")
FILM_SAID = ("film", "films", "movie", "movies", "cinema", "watch", "watches", "watching",
             "watched", "netflix", "screen", "telly", "tv")


def _another_subject(line):
    """True when the line is about a length or a thing that is not a film."""
    words = " %s " % _plain_words(line)
    if any((" %s " % word) in words for word in FILM_SAID):
        return False
    return any((" %s " % word) in words for word in OTHER_SUBJECT)


def _pick_line(understood):
    """The line as the person typed it, with the reading's own rewrites alongside.

    A reader earlier in the turn can rewrite `clean` - "i dont like subtitles" comes back from one
    as "what can i make without like subtitles" - and a tell the person did type is then gone. The
    typed line is read first, so the words that were actually sent are the ones the limit is read
    from.
    """
    if not isinstance(understood, dict):
        return ""
    said = [understood.get("text") or "", understood.get("clean") or "",
            understood.get("norm_text") or ""]
    return " ".join(part for part in said if part)


def _film_kind(line):
    """The kind of film the line names (a key of FILM_KINDS), or "".

    A kind the person turned down is not a request for it - "not a musical", "i dont like
    christmas films" - so a negator just before the word passes the line on, the same way the
    country word is read.
    """
    words = " " + _plain_words(line) + " "
    for kind in FILM_KIND_WORDS:
        # the plural too: "good westerns" and "good superheroes" are the same shelf, and a plain
        # substring test reads only the singular the table is written in
        found = re.search(r"(?<![a-z0-9])" + kind + r"(?:s|es)?(?![a-z0-9])", words)
        if not found:
            continue
        before = words[:found.start()].split()[-2:]
        if any(one in NEGATORS for one in before):
            continue
        return kind
    return ""


_MINUTES = re.compile(r"(\d{2,3})\s*(?:minutes|minute|mins|min)\b")
# The same limit said without an "under": "a thriller i can watch in 90 minutes", "a horror film
# of about 95 minutes", "a comedy that runs under 100 minutes". The shelf card names runtimes, and
# a card whose films all overrun the number just given is confidently wrong, so any of these
# shapes is read as the limit it is. The word has to be one of these: "a film that is 90 minutes"
# describes a runtime, it does not ask for one, and a bare duration is still not a limit.
_LIMIT_CUE = re.compile(r"(in|of about|of|runs|running|lasts|lasting|for)"
                        r"\s+(?:about\s+|around\s+|roughly\s+|just\s+)?([a-z0-9. ]{1,24})")
# "within an hour" and "inside of two hours" are how a deadline is given, not how a film is
# described, so they are not limits here.
_UNDER = re.compile(r"(under|less than|no longer than|shorter than|max|maximum|at most)"
                    r"\s+(?:about\s+|just\s+)?([a-z0-9. ]{1,24})")
# Two ways to give the same number, and they are not the same limit: "under two hours" excludes
# the film that runs exactly two hours and "max two hours" allows it. One reviewer found *Mad Max:
# Fury Road* (120 minutes) sitting at the top of an "Under 120 minutes" list.
STRICT_LIMIT = frozenset(("under", "less than", "shorter than"))
_HOUR_WORDS = {
    "an hour": 60, "one hour": 60, "1 hour": 60, "hour and a half": 90,
    "an hour and a half": 90, "one and a half hours": 90, "1.5 hours": 90,
    "two hours": 120, "2 hours": 120, "two hour": 120, "2 hour": 120,
}
_HOUR_MINUTES = re.compile(r"(\d(?:\.\d)?)\s*(?:hours|hour|hrs|hr)\b")


def _limit_wanted(line):
    """The minutes the line allows and whether that wording excludes the number itself.

    A limit is said three ways - "under 100 minutes", "under two hours", "no longer than an
    hour and a half" - and all three are the same number here. A runtime named without an "under"
    ("a film that is 90 minutes") is not a limit, so it reads as none and the line is not this
    entry's question. The second half of the answer is the wording: "under" and "less than" rule
    out a film of exactly that length, "max" and "no longer than" do not.
    """
    words = " " + _plain_words(line) + " "
    found = _UNDER.search(words)
    if found:
        strict = found.group(1) in STRICT_LIMIT
        tail = found.group(2).strip()
    else:
        # no "under": "in 90 minutes", "of about 95 minutes" and "runs 100 minutes" all allow a
        # film of exactly that length, so none of them is strict
        found = _LIMIT_CUE.search(words)
        if not found:
            return 0, False
        strict = False
        tail = found.group(2).strip()
    number = re.match(r"(\d{2,3})\b", tail)
    if number:
        return int(number.group(1)), strict
    # longest phrase first: "an hour and a half" starts with "an hour", and the shorter reading
    # would answer 60 minutes to somebody who allowed 90
    for phrase in sorted(_HOUR_WORDS, key=len, reverse=True):
        if tail.startswith(phrase):
            return _HOUR_WORDS[phrase], strict
    hours = _HOUR_MINUTES.match(tail)
    if hours:
        try:
            return int(round(float(hours.group(1)) * 60)), strict
        except ValueError:
            return 0, False
    return 0, False


def _minutes_wanted(line):
    """The length limit the line states in minutes, or 0 when it states none."""
    return _limit_wanted(line)[0]


def _film_under(memory, understood):
    """Films that fit the minutes the line allows, with the runtime beside each title.

    The number is the answer, so a limit nothing fits says so rather than stretching the nearest
    film over it: the shortest thing in the table is 23 minutes, and "*Toy Story* is 81" is not an
    answer to somebody with half an hour.
    """
    line = _pick_line(understood)
    if _pick_stands_down(line):
        return None
    if _another_subject(line):
        return None
    limit, strict = _limit_wanted(line)
    if not limit:
        return None
    # A shelf named with the limit is that shelf's question: "a horror film under 100 minutes"
    # is a scare first, and three short films that are not scary answer a question nobody asked.
    # The kind rows read the limit off their own runtimes, and a mood list is short enough that
    # the limit is beside the point - so this table answers only a limit that names no shelf.
    #
    # The kind is read here rather than left to the kind row, because the kind row is keyed on the
    # medium as well: "a western under two hours" and "a thriller under 100 minutes" have no
    # medium word, so that row never fired and the shelf went unanswered. The limit is the ask in
    # those lines and the shelf is the subject, so the shelf answers, read for the minutes.
    kind = _film_kind(line)
    if kind:
        return _film_kind_reply(memory, understood)
    if _mood_of(line):
        # "a comedy under two hours" names the mood but not the "something" the mood rows are
        # keyed on, so no mood row scored and this row, which owns the minutes, answered the line
        # with a shrug. The film table is the one that carries runtimes, so the mood's own films
        # are read for the minutes here, which is what the mood row does with its own words.
        if _pick_kind(line) or _pick_carry(memory, line):
            # a medium named ("a scary film") or carried is that medium's own row
            return None
        return _a_pick_in_any_medium(memory, understood)
    if _names_a_film_genre(line):
        return None
    # The shelf the chat is already on is read like the medium: "good westerns" then "under two
    # hours" is a western question, and the general table answers a question nobody asked.
    carried = _kind_carry(memory, line)
    if carried:
        within = _shelf_within(carried, limit, strict)
        if within:
            return within
    rows = [row for row in FILM_RUNTIME
            if (row[1] < limit if strict else row[1] <= limit)]
    if not rows:
        return ("Nothing I know comes in %s %d minutes. The shortest I have is *A Grand Day "
                "Out* at 23 minutes, and *The Snowman* at 27 - say the number again if I have "
                "read it wrong." % ("under" if strict else "at", limit))
    # the longest that still fits, and two more from the same shelf, so the limit is used and the
    # choice is not three films that all finish an hour early
    picked = rows[-3:]
    picked.reverse()
    said = ["*%s* (%d minutes)" % (row[0], row[1]) for row in picked]
    if len(said) == 1:
        body = said[0]
    else:
        body = ", ".join(said[:-1]) + " or " + said[-1]
    # the heading has to be the limit the person gave: a film of exactly 120 minutes is not
    # "under two hours", and a list headed "Under 120 minutes" must not open with one
    # the films come first and the limit after them: a reply that opens "Up to 95 minutes:" is
    # read by the memory store as the length of the answer, and a later "i have 90 minutes" then
    # tells the person the films want longer than their budget when none of them does
    return ("%s - all %s %d minutes. Say what you feel like and I will pick one."
            % (body, "under" if strict else "up to", limit))


def _shelf_within(kind, limit, strict):
    """The shelf a kind names, read for a runtime limit: the films that fit, or the shortest one.

    The kind rows and a follow-up that says only the limit both want this, so it is one reply:
    "good westerns" then "under two hours" is a western question with no kind word in it.
    """
    label, said_as, rows = FILM_KINDS[kind]
    fit = [row for row in rows if (row[1] < limit if strict else row[1] <= limit)]
    if not fit:
        shortest = min(rows, key=lambda row: row[1])
        return ("Nothing on the %s shelf comes in %s %d minutes - the shortest is *%s* at %d. "
                "Say the number again if I have read it wrong, or name another kind."
                % (label, "under" if strict else "at", limit, shortest[0], shortest[1]))
    if len(fit) == len(rows):
        return None
    said = ["*%s* (%d minutes, %s)" % (title, minutes, reason)
            for title, minutes, reason in fit]
    body = said[0] if len(said) == 1 else ", ".join(said[:-1]) + " or " + said[-1]
    # films first, limit after: see _film_under - a reply that opens with the limit is read by
    # the memory store as the length of the answer. The shelf is still named, in the sentence
    # that carries the limit.
    return ("%s. %s %s %d minutes, and the other %s on that shelf run%s longer, so say if "
            "you would rather have one of those."
            % (body, said_as[0].upper() + said_as[1:], "under" if strict else "up to", limit,
               "one" if len(rows) - len(fit) == 1 else "two",
               "s" if len(rows) - len(fit) == 1 else ""))


def _kind_carry(memory, line):
    """The kind of film asked about a turn ago, for a follow-up that says only a limit.

    "good westerns" then "under two hours" is a western question with the kind left out, and the
    length table answered it with *The King's Speech*: the shelf is what the chat is about, read
    the same way the medium and the limit already are.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    mine = _plain_words(line).strip()
    for turn in (turns or [])[-2:]:
        user = str((turn or {}).get("user") or "")
        if not user or _plain_words(user).strip() == mine:
            continue
        kind = _film_kind(user)
        if kind:
            return kind
    return ""


# "which one is shortest" after a shelf names no kind, no mood and no limit - it is a question
# about the three films just given, and their runtimes are already on the screen. The kind travels
# with the chat, so this row is where it lands ("good westerns" then "which one is shortest"), and
# the whole shelf is the wrong answer to it. Only an ask *about* the shelf, so "the shortest route
# to the airport" is untouched: the word has to be one of these and about one of these.
SHORTEST_WORDS = ("shortest", "quickest", "fastest", "shorter one", "shortest one")


def _shortest_wanted(line):
    """True when the line asks which of the films just given is the shortest."""
    if not any(re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", line)
               for word in SHORTEST_WORDS):
        return False
    return any(re.search(r"(?<![a-z0-9])" + word + r"(?![a-z0-9])", line)
               for word in ("one", "ones", "film", "films", "those", "these", "them", "pick",
                            "of", "which", "what", "three", "any", "any of"))


def _film_kind_reply(memory, understood):
    """The shelf a kind names, three films from it, and how long each one runs."""
    line = _pick_line(understood)
    if _pick_stands_down(line):
        return None
    if _another_subject(line):
        return None
    words = " " + _plain_words(line) + " "
    kind = _film_kind(line)
    if not kind:
        return None
    if _pick_kind(line) not in ("film", ""):
        return None
    # "is die hard a christmas film" asks whether one named film belongs on the shelf, and a
    # shelf of three is not an answer to that: the line is a yes-or-no about a film the person
    # already has in mind, so this entry leaves it to whoever can answer it.
    if re.match(r"\s*(?:is|was|are|were|isnt|wasnt)\b", _plain_words(line)) \
            and (" " + kind + " ") in words:
        return None
    if _a_word_is_turned_down(line, _kind_words(kind), KIND_REFUSED_AFTER) \
            or _the_chat_turned_down(_kind_words(kind), memory, KIND_REFUSED_AFTER):
        # "i dont want to watch a musical" names the shelf only to turn it down, and the shelf
        # answered it with the musicals: the same fault as the scary picks, where the key wins the
        # ranking on the kind word and the turn-down is thrown away. `film-dont-want` holds the
        # answer for this shape, so the shelf stands down and lets it through.
        return None
    label, said_as, rows = FILM_KINDS[kind]
    # "which one is shortest" is the one ask about a shelf that a shelf cannot answer: the whole
    # list comes back a second time, with the runtimes the person has just read, and the number
    # they asked for is in there unread. The shortest is named with its runtime, and the next one
    # up is named beside it so there is somewhere to go if the evening is not that tight.
    if _shortest_wanted(words):
        shortest = min(rows, key=lambda row: row[1])
        longer = [row for row in rows if row[0] != shortest[0]]
        said = ("The shortest on that shelf is *%s* at %d minutes, %s"
                % (shortest[0], shortest[1], shortest[2]))
        if longer:
            said += (". *%s* runs %d if you have the time."
                     % (longer[0][0], longer[0][1]))
        return said
    # "a horror film under 100 minutes" is a kind *and* a limit, and the kind is the question: a
    # shelf, read for the runtimes it already carries, is the answer both readings want. The
    # length table below answers only a limit that names no shelf (see _film_under).
    limit, strict = _limit_wanted(line)
    if limit:
        within = _shelf_within(kind, limit, strict)
        if within:
            return within
        # every film on the shelf fits, so the limit has taken nothing away and the shelf is the
        # whole answer
    said = ["*%s* (%d minutes, %s)" % (title, minutes, reason)
            for title, minutes, reason in rows]
    return ("For %s: %s, or %s. Any of them is a good way in, and I can go shorter or pick one if "
            "you tell me the mood." % (said_as, ", ".join(said[:-1]), said[-1]))


def _pick_plain(memory, understood):
    """A pick for a line that names the medium and who it is for, with no mood in it."""
    line = _pick_line(understood)
    if _pick_stands_down(line):
        return None
    # A feeling anywhere in the line is the mood rows' question, whatever word spells it: the
    # hand list above misses "something that makes me think", and the plain pick then offered
    # three easy films and asked for the mood the person had just given.
    if _mood_of(line) is not None:
        return None
    # The medium is this line's, or the one asked about a turn ago: "anything shorter" after a
    # book question is a book, and a pick in the wrong medium is worse than no pick. A line with
    # no medium anywhere is not a request this entry can honour, so it passes.
    kind = _pick_kind(line) or _pick_carry(memory, line)
    refused = _pick_refused(line)
    if refused and kind == refused:
        # A medium behind a negator is not the medium being asked for: "not a book" never asked
        # for a book, it took the word book. One turn after a film question it is still a film
        # question, so the medium asked about a turn ago is what to answer with; with nothing to
        # carry, a screen medium ruled out leaves the other screen, and a book or a podcast
        # ruled out is not something this shelf can answer round.
        carried = _pick_carry(memory, line)
        if carried and carried != refused:
            kind = carried
        elif refused in ("film", "series"):
            kind = "series" if refused == "film" else "film"
        else:
            return None
    if not kind or kind == "podcast":
        return None
    cinema = _cinema_of(line)
    if cinema and kind == "film":
        adjective, country, language = cinema
        rows = _pick_rows("film", "", "", country=country)
        if not rows:
            # a country the table has no list for. Saying so, and naming the countries it does
            # have, is a better answer than the nearest famous film: *Amelie* to somebody asking
            # about Czech cinema is a confident wrong answer.
            have = []
            for title, of, reason in NATIONAL_CINEMA:
                if of not in have:
                    have.append(of)
            heard = have[0] + ", " + have[1] + " or " + have[2]
            rest = len(have) - 3
            more = " and %d other countries" % rest if rest > 0 else ""
            return ("I have not got a %s list, and I would rather say so than hand you the wrong "
                    "film. I do have %s%s - tell me a %s film you liked and I will match the next "
                    "one." % (adjective, heard, more, adjective))
        return _pick_reply("film", "", "", rows, country=adjective, language=language)
    if kind == "film" and _wants_subtitles(line):
        # "a film with subtitles", "something foreign": the table itself is the answer, and the
        # country each film is from is the reason it is there
        picked = NATIONAL_CINEMA[:9:4]
        rows = [(title, "film", (), False, False, "%s: %s" % (of, reason))
                for title, of, reason in picked]
        return ("Subtitled, then: " + _pick_list(rows) + ". Tell me a country and I will give you "
                "three of its films.")
    who = _pick_who(line)
    limit = _pick_limit(line, memory)
    rows = _pick_rows(kind, who, limit)
    if not rows:
        return None
    return _pick_reply(kind, who, limit, rows)


def _pick_limit_reply(memory, understood):
    """A limit said on its own: what is left to watch once it is respected.

    No limit found means the line only looked like one (a reading rewritten by a reader earlier in
    the turn), and the entry stands down rather than guessing: "i dont like subtitles" must never
    be answered with what is on iPlayer and ITVX, because nobody said anything about a channel.
    """
    line = _pick_line(understood)
    if _pick_stands_down(line):
        return None
    limit = _pick_limit(line, memory)
    if not limit:
        return None
    kind = _pick_kind(line)
    if kind == "book":
        # A book was named and the limit was about telly, so answer the book: there is no channel
        # in the way of a book, and "book recommendations, we only have bbc and itv" is a person
        # asking for something to read.
        return _pick_reply("book", "", "", _pick_rows("book", "", ""))
    if limit == "nosubs":
        rows = _pick_rows("film", "", "nosubs")
        return ("Nothing that needs subtitles, then: " + _pick_list(rows[:3]) + ". All three are "
                "in English, so nobody has to read the screen to follow them.")
    rows = _pick_rows(kind if kind in ("film", "series") else "series", "", "free")
    return ("Then it is iPlayer and ITVX, and both are free. " + _pick_list(rows[:3]) + ". All "
            "three are BBC, so they are on iPlayer, and a film on ITV turns up most weeks too - "
            "check iPlayer rather than trusting a listing, because rights move.")


# The age in the line is the whole question, and a reader of fourteen is not a reader of seven:
# the reply has to lead with the band that was asked for. A number can never be a key word, so the
# age is read here rather than matched, and thirteen and over is not this row's (a teenager's book
# is the reader's own answer, and "books for a 14 year old" was being given The Worst Witch).
_AGE_BANDS = (
    # A child under five is read to, not reading alone, and the answer the oldest band gave a
    # three-year-old was a chapter book for a six-year-old. The age is named, so the answer can
    # match it: board books for the very young and picture books for the rest.
    (1, 4, "Under five wants picture books and board books, read together: *The Very Hungry "
            "Caterpillar* by Eric Carle, *Dear Zoo* by Rod Campbell, *Each Peach Pear Plum* by "
            "Janet and Allan Ahlberg, or any of the *That's Not My...* books. Read the same three "
            "or four over and over - the repetition is the point at that age - and let them turn "
            "the pages."),
    (5, 7, "Five to seven wants short chapters and a picture every few pages: *The Worst Witch*, "
            "*Mr Gum*, *Dog Man* or *Captain Underpants*."),
    (8, 9, "Eight and nine: *The Boy at the Back of the Class*, *Horrible Histories* or *Percy "
            "Jackson*, and *Dog Man* still works for a reader who wants pictures."),
    (10, 12, "Ten to twelve: *Wonder*, *Artemis Fowl* or *Skulduggery Pleasant*, and anything by "
             "Jacqueline Wilson or David Walliams for a reader who likes a series."),
    # Thirteen and over were left to nobody: the row stood itself down for a teenager and the
    # line then reached the bot counting the child back ("One kid, 14. What are they into at the
    # moment?"), or, for 17, the five-to-seven paragraph. A teenager's book is still a book for
    # a named age, so it answers here, with the books that hold a teenager.
    (13, 15, "Thirteen to fifteen is when the book has to be theirs: *The Hunger Games*, "
             "*Northern Lights* and *The Book Thief* are the safe three, and *The Hate U Give* "
             "or *Six of Crows* if they want something current."),
    (16, 18, "Sixteen to eighteen: *The Book Thief*, *The Hate U Give* and *Normal People*, or "
             "*Educated* by Tara Westover if they would rather read something true."),
)
_WORD_AGES = {"five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
              "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
              "seventeen": 17, "eighteen": 18}


def _the_reader_age(line):
    match = re.search(r"\b(\d{1,2})\s*(?:-|\s)?\s*(?:year|years|yr)s?\s*-?\s*old\b", line)
    if match:
        return int(match.group(1))
    # "a book for my son who is 9" and "book for my daughter aged 12" name the age without the
    # words "year old", and both were given the five-to-seven paragraph
    match = re.search(r"\b(?:aged|age|who is|who's|is)\s+(\d{1,2})\b", line)
    if match:
        return int(match.group(1))
    for word, age in _WORD_AGES.items():
        if word in line:
            return age
    return 0


def _book_for_the_age(memory, understood):
    reading = understood if isinstance(understood, dict) else {}
    line = str(reading.get("clean") or reading.get("text") or "").lower()
    age = _the_reader_age(line)
    if not age and re.search(r"\bteen(?:ager)?s?\b", line):
        # "books for teenagers" and "a good book for a teenager" name the reader without a
        # number, so they get the teen band rather than the whole ladder from five upwards.
        age = 13
    for low, high, lead in _AGE_BANDS:
        # No age in the line ("a book for my son") is not a toddler: the wide answer names
        # every band instead of guessing at the youngest.
        if age and low <= age <= high:
            close = (" Take them to a bookshop and let them pick the first one themselves: the "
                     "series they choose is the one they read.")
            return lead + close
    return ("Short chapters and a picture every few pages are what a 5 to 7 year old reading "
            "alone wants: *The Worst Witch*, *Mr Gum*, *Dog Man* or *Captain Underpants*. For 8 "
            "to 9, *The Boy at the Back of the Class*, *Horrible Histories* or *Percy Jackson*. "
            "For 10 to 12, *Wonder*, *Artemis Fowl* or *Skulduggery Pleasant*. For 13 and over, "
            "*The Hunger Games*, *Northern Lights* or *The Book Thief*. Take them to a bookshop "
            "and let them pick the first one themselves; the series they choose is the one they "
            "read.")


# A spare hour is the same question as a spare day with less of it, and the day's answer ("one
# thing out of the house and one thing at home") does not fit in one. The free time is what the
# line has, so it is the line that decides which of the two is said.
# Only the hour itself: an afternoon already has its own answer ("put two things in the
# afternoon"), and an evening has too.
_A_SHORT_TIME = re.compile(
    r"\b(?:an?|one|two|three|couple of|few) hours?\b|\bhalf an hour\b")

_AN_HOUR = (
    "For an hour, pick one thing you can finish inside it rather than a plan: a walk round the "
    "block with a podcast, one drawer or one shelf, a chapter, or the phone call you keep putting "
    "off. It ends when the hour does, which is the point. Are you on your own, or is someone with "
    "you?")
_A_DAY = (
    "One thing out of the house and one thing at home usually fills it. Out: a walk somewhere you "
    "have not been, a Saturday market, or a museum or gallery - most are free and good for an hour "
    "or two. Home: something to cook properly, a film, or a jigsaw with the radio on. Rain only "
    "moves the walk to a pool or a cinema. Is it just you, or is someone coming with you?")


def _an_hour_or_a_day(memory, understood):
    reading = understood if isinstance(understood, dict) else {}
    line = str(reading.get("clean") or reading.get("text") or "").lower()
    if _A_SHORT_TIME.search(line):
        return _AN_HOUR
    return _A_DAY
# A comic for a child and a comic for a teenager are not the same pick: Dog Man is the answer for
# a seven-year-old and an insult to a fifteen-year-old, so the row answers whichever young reader
# the line names.
_COMIC_FOR_A_CHILD = (
    "For a child, *Dog Man* by Dav Pilkey is the one that gets read to bits, and *Hilda* by Luke "
    "Pearson is the warmer, stranger alternative. *Naruto* or *One Piece* if they want manga to "
    "live in. A library will lend all of these, and a finished single story is easier to hand "
    "over than a long superhero run.")
_COMIC_FOR_A_TEEN = (
    "*Heartstopper* by Alice Oseman is the warmest place to start: a school story that reads fast "
    "and is kind about being a teenager. *One Piece* if they want a long one to live in, "
    "*Fullmetal Alchemist* if they would rather finish something, and *Persepolis* if they like "
    "real life. A library will lend all of these.")
_TEEN_WORDS = frozenset(("teen", "teens", "teenager", "teenagers", "teenaged", "sixteen",
                         "fifteen", "fourteen", "thirteen", "seventeen", "eighteen"))


# The plurals matter as much as the singulars: a parent asks "best kids comics" and "comics for
# children" far more often than "for a kid", and without them those lines read as an adult asking
# and got *Saga* and *Watchmen* - an adult pick handed to a parent, which is worse than a hedge.
_CHILD_OF_THEIRS = frozenset(("son", "daughter", "kid", "child", "boy", "girl", "teen",
                              "teenager", "kids", "children", "boys", "girls", "tween", "tweens",
                              "youngster", "youngsters", "grandchild", "grandchildren", "niece",
                              "nephew", "godson", "goddaughter"))
_LIKING = frozenset(("loves", "love", "likes", "like", "enjoys", "enjoy", "adores", "adores",
                     "reads", "read", "devours", "obsessed", "into"))
# Not `_ASKS_FOR_A_PICK`: that name is the regex above, and rebinding it here left the complaint
# reader calling `.search` on a frozenset, so every "my book is boring" line raised and the whole
# answers module dropped out for the turn.
_ASKS_FOR_A_PICK_WORDS = frozenset(("recommend", "suggest", "what", "which", "best", "good",
                                    "any", "for", "start", "should", "idea", "ideas", "next"))


def _a_child_who_reads_already(understood):
    """True when the line is a parent saying what their child reads, not asking for a pick."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    if not _CHILD_OF_THEIRS.intersection(words):
        return False
    if "my" not in words and "our" not in words:
        return False
    if not _LIKING.intersection(words):
        return False
    return not _ASKS_FOR_A_PICK_WORDS.intersection(words)


# "is manga ok for kids", "is watchmen suitable for a child", "what age is manga suitable for"
# are not pick questions: they ask what is in the thing and whether it is right for an age. The
# adult shelf was the answer to one of them ("what age is manga suitable for" got *Saga* and
# *Watchmen*), which tells a parent nothing about the age. The rating on the back, the titles that
# are safe from each age, and the one sentence about what to check is the answer.
_COMIC_SUITABILITY = (
    "Judge it by the age rating on the back - 8+, 12+ and 16+ - and by what the child already "
    "reads, then read or skim the first few pages yourself for the two things that matter, sex "
    "and violence. *Dog Man* and *Hilda* are safe from about seven, *Heartstopper* and "
    "*Fullmetal Alchemist* from about twelve, and *Watchmen* and *Saga* are the ones to leave "
    "until they are older - *Watchmen* has sexual violence in it. A librarian will tell you what "
    "is in a title in about a minute, and will not mind being asked.")

_SUITABILITY_ASK = re.compile(
    r"\b(?:is|are|was|were|would)\b[^?.!]{0,40}?"
    r"\b(?:ok|okay|suitable|appropriate|fine|alright|all right)\b[^?.!]{0,20}?\bfor\b"
    r"|\b(?:what|which) age\b[^?.!]{0,40}\b(?:suitable|appropriate|ok|okay|right)\b"
    r"|\b(?:too old|too young|right age|age range|age rating)\b"
    r"|\bfor (?:a|an) \d{1,2} ?(?:year|yr)s? ?old\b[^?.!]{0,20}\b(?:ok|okay|suitable)\b")


def _asks_if_a_comic_suits_an_age(understood):
    """True when the line asks whether the thing is right for an age, not for a pick."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    return bool(_SUITABILITY_ASK.search(said.lower()))

_COMIC_FOR_A_GROWN_UP = (
    "*Saga* by Brian K. Vaughan is the usual first pick for an adult: a space story with a family "
    "at its centre and art that carries the plot. *Watchmen* if you want the one that changed "
    "what comics could do, *Persepolis* by Marjane Satrapi for a memoir told this way, and "
    "*Heartstopper* by Alice Oseman for a warm school romance. For manga, *Death Note* or "
    "*One Piece* is where most people start. Begin with a complete story rather than a forty-year "
    "superhero run, and a library will lend all of these.")


# A grown-up asking for a comic is given one adult shelf (*Saga*, *Watchmen*, *Persepolis*), so a
# person who names the kind they want gets an answer about something else: "what manga should i
# read" and "good manga to read" were both handed *Saga*, a western comic, and the same card came
# back for "any marvel comics worth reading" and "best marvel comics of all time". The kind named
# is the pick, and there is one card for each of the three kinds people ask for by name.
_COMIC_MANGA = (
    "*Death Note* (a notebook that kills, and the duel that follows) is the usual first manga: "
    "twelve volumes, a clean ending, and nothing to know beforehand. *One Piece* if they want a "
    "long one to live in, or *Fullmetal Alchemist* if they would rather have something they can "
    "finish. Read right to left, back to front - the pages are printed the Japanese way.")
_COMIC_MARVEL = (
    "*Daredevil: Born Again* by Frank Miller is the one to start with: short, brutal and complete "
    "in itself. *Hawkeye* by Matt Fraction if you want funny, *Ms Marvel* by G. Willow Wilson if "
    "you want a teenager finding her feet. Skip the crossover events - they assume forty years of "
    "reading behind them.")
_COMIC_DC = (
    "*Batman: Year One* by Frank Miller is the cleanest way in: one short story, no homework. "
    "*All-Star Superman* by Grant Morrison if you want the character at his best, *Swamp Thing* "
    "by Alan Moore if you want something strange and grown-up. *Watchmen* is the other DC one "
    "worth the time.")
_COMIC_BEGINNER = (
    "*Bone* by Jeff Smith is the easiest place to start: one long story, funny, and it looks like "
    "a children's book until you are deep in it. *Persepolis* by Marjane Satrapi if you want "
    "something true, *Saga* if you want a space story. A library will have all three, and one "
    "complete story is a better first comic than a run of forty issues.")

# The definition, which no row answered: "what is a graphic novel" and "what is manga" were both
# handed *Saga* and *Watchmen* as if the person had asked for something to read.
_COMIC_MEANING = (
    "A graphic novel is one whole story told in comic panels and published as a single book rather "
    "than a monthly issue - *Persepolis* and *Watchmen* are the classic examples. Manga is "
    "Japanese comics, usually printed right to left, and *Death Note* is an easy first one.")
# Anchored at the end of the line on purpose: "what is a graphic novel" asks for a definition and
# "what is the best manga" asks for a pick, and only the first of those ends on the noun.
_COMIC_MEANING_ASK = re.compile(
    r"\bwhat(?:'s| is| are)\s+(?:a|an|the)?\s*"
    r"(?:graphic novels?|mangas?|comic books?|comics?|webtoons?)\s*[?.!]*\s*$"
    r"|\bdifference between\b")
_KIND_WORDS = {"manga": _COMIC_MANGA, "marvel": _COMIC_MARVEL, "dc": _COMIC_DC,
               "batman": _COMIC_DC, "superman": _COMIC_DC}
_BEGINNER_WORDS = frozenset(("beginner", "beginners", "newcomer", "newbie"))
# The ask a pick is wanted with, kept tight so a line that only mentions the kind stands down.
_KIND_ASKS = frozenset(("recommend", "recommendation", "recommendations", "suggest", "what",
                        "which", "good", "best", "read", "reading", "start", "started", "try",
                        "worth", "any", "into", "first", "beginner", "beginners", "next"))


def _the_kind_named(understood):
    """The card for the kind of comic the line names, or "" for a line that names none."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if _COMIC_MEANING_ASK.search(said):
        return _COMIC_MEANING
    words = [str(word).lower() for word in ((understood or {}).get("words") or [])]
    if not _KIND_ASKS.intersection(words):
        return ""
    for word, card in _KIND_WORDS.items():
        if word in words:
            return card
    if _BEGINNER_WORDS.intersection(words) or "where do i start" in said \
            or "where to start" in said:
        return _COMIC_BEGINNER
    return ""


def _reader_named(words, numbers=()):
    """Which young reader these words name: "teen", "child", or "" for a grown-up line."""
    if _TEEN_WORDS.intersection(words):
        return "teen"
    for figure in numbers or ():
        if isinstance(figure, dict) and figure.get("unit") == "years":
            try:
                age = int(figure.get("value"))
            except (TypeError, ValueError):
                continue
            if 13 <= age <= 19:
                return "teen"
            if age <= 12:
                return "child"
    if _CHILD_OF_THEIRS.intersection(words):
        return "child"
    return ""


def _comic_pick(memory, understood):
    """The comic shelf, for the reader the line is for.

    A pick for a grown-up is no use to a seven-year-old and Dog Man is an insult to a teenager,
    so the row reads who it is for: the line first, and then the turns before it, because "my son
    is 8 and hates reading" then "what about comics" carries the child over and the pick is still
    for that child.
    """
    # "is manga ok for kids" wants to know what is in it and what age it suits, and a shelf of
    # three titles does not answer that - least of all the adult one
    if _asks_if_a_comic_suits_an_age(understood):
        return _COMIC_SUITABILITY
    # A child or a teenager is picked for first: Dog Man beats a manga shelf for a seven-year-old,
    # and "best manga for a teen" is a teen's shelf rather than a named-kind one.
    words = [str(word).lower() for word in (understood.get("words") or [])]
    if not _reader_named(words, understood.get("numbers") or ()):
        named = _the_kind_named(understood)
        if named:
            return named
    reader = _reader_named(words, understood.get("numbers") or ())
    if not reader:
        for turn in reversed((memory or {}).get("turns") or []):
            said = str((turn or {}).get("user") or "").lower()
            earlier = [word for word in re.split(r"[^a-z']+", said) if word]
            reader = _reader_named(earlier)
            if reader:
                break
    if reader == "teen":
        return _COMIC_FOR_A_TEEN
    if reader == "child":
        return _COMIC_FOR_A_CHILD
    return _COMIC_FOR_A_GROWN_UP


# "what should i read if i like sci fi" says the taste and asks for the book that follows it, and
# `book-like` took it: it answers a line that names a book with the next one, and read as one of
# those it answered a science-fiction ask with *The Thursday Murder Club*. A genre is not a title -
# the genre rows know their own three picks - so the like-a-book row stands down when the thing
# after "like" is a kind of book rather than a book.
BOOK_GENRES = ("sci fi", "sci-fi", "scifi", "science fiction", "fantasy", "thriller", "thrillers",
               "crime", "crime fiction", "murder mystery", "mystery", "mysteries", "horror",
               "romance", "romantic", "graphic novel", "graphic novels", "comics", "comic books")
_LIKE_A_GENRE = re.compile(
    r"\b(?:like|similar to|anything like|something like|after)\s+(?:a |an |some |any )?(?:"
    + "|".join(re.escape(word) for word in BOOK_GENRES) + r")\b")


def _a_genre_is_the_taste(understood):
    """False when the thing the line likes is a kind of book, which the genre rows answer."""
    text = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return not _LIKE_A_GENRE.search(text)

# --- the verse asked for again, but longer ------------------------------------------------
# "longer" is a length in eleven other senses before it is one about a verse (an essay, a phone
# cable, a warranty, the days), so the line has to ask for more of the thing and the last turn has
# to have been a verse. A haiku and a limerick are fixed counts of lines, so there is no longer
# one to give, and those keep whatever answer they had.
# "One more verse" is another verse, not a longer one: it is the count asked for again, and a
# second verse of the same length is the ask (`the_next_verse` below). Only "add a verse" and
# "longer" ask for the verse already on the screen with a part on the end.
_LONGER_ASK = re.compile(
    r"\b(?:a\s+)?longer(?:\s+(?:one|version|story|poem|verse|rhyme))?\b"
    r"|\badd\s+(?:a\s+)?(?:verse|stanza)\b", re.I)
_LONGER_NOT_THIS = ("essay", "essays", "letter", "hair", "lashes", "nails", "battery",
                    "cable", "cables", "warranty", "warranties", "opening hours", "term",
                    "sentence", "sentences", "trousers", "legs", "days", "hours", "holiday",
                    "delay", "wait", "queue", "sleep", "run", "drive", "flight", "shift")
_FIXED_COUNT_FORM = re.compile(r"\b(haiku|limerick)\b", re.I)
# The form the verse announced in its own first line, which is what says which pool the extra part
# comes from: "A short story about a dog:" takes the story lines, "A short poem about the sea:"
# takes the rhymed ones.
_POEM_FORM = re.compile(r"\b(poem|poems|poetry|rhyme|rhymes|verse|verses|rap|song|ode|sonnet|"
                        r"ballad|couplet)\b", re.I)
_VERSE_IN_THE_LAST_TURN = re.compile(
    r"\b(story|stories|tale|tales|poem|poems|poetry|rhyme|rhymes|rap|song|verse|verses|"
    r"limerick|haiku|couplet|ode|sonnet)\b", re.I)


def the_verse_longer(text, memory):
    """The verse just given with another part on the end, or None when that is not the ask.

    The verse is kept rather than replaced: "make it longer" wants more of what was read out,
    not a different one. The extra part is picked by the thing the verse was about, so the same
    story asked for longer twice grows the same way.

    Read by `bot/modules/answers.py` before any entry does, and given the typed line rather than
    the reading: a reading of a follow-up leans on the last ask, so "tell me a story about my
    holiday" would put "holiday" in the line and fence off the very ask that follows it.
    """
    line = " ".join(str(text or "").lower().split())
    if not _LONGER_ASK.search(line):
        return None
    if any(one in line for one in _LONGER_NOT_THIS):
        return None
    said = ""
    thing = ""
    for turn in reversed([one for one in ((memory or {}).get("turns") or [])
                         if isinstance(one, dict)]):
        said = str(turn.get("bot") or "")
        if said:
            thing = _thing(str(turn.get("user") or ""))
            break
    if not said or "\n" not in said:
        return None
    if said.startswith("Once more"):
        # the verse said again by the row above: its own lead is the second line
        said = said.split("\n", 1)[1] if "\n" in said else said
    lead, rest = (said.split("\n", 1) + [""])[:2] if "\n" in said else ("", said)
    if not lead.rstrip().endswith(":"):
        lead, rest = "", said
    if not _VERSE_IN_THE_LAST_TURN.search(lead or rest.split("\n", 1)[0]):
        return None
    if _FIXED_COUNT_FORM.search(lead):
        return None
    thing = thing or GENERIC_STORY_THING
    pool = VERSE_LONGER if _POEM_FORM.search(lead) else STORY_LONGER
    more = _picked(pool, thing).format(thing=thing)
    return (lead + "\n" + rest + "\n" + more) if lead else (rest + "\n" + more)


# --- the same thing asked for another poem of ---------------------------------------------
# "one more about the moon" after a poem about the moon answered "Got it - one more about the
# moon." on main: the phrase names a subject and no form, so no row read it as a request, and the
# story row stands down because the last verse was a poem. The form just given is the form asked
# for again, and the table holds one poem per thing, so the second one is the generic verse with
# the thing in it - a different one from the poem that is already on the screen.
_SECOND_VERSE_ABOUT = re.compile(
    r"\b(?:one\s+more|another\s+one|one\s+other|another|one)\s+about\b", re.I)
# The subject of the verse on the screen, read out of its own lead: "A short story about a fox:"
# was about a fox, so "one more" is another one about the fox.
_THE_SUBJECT_IN_A_LEAD = re.compile(
    r"\b(?:about|of|on|describing|called|named)\s+(.+?)\s*:\s*$", re.I)
# The count asked for again ("one more", "another one") is a second verse in the form just given
# whatever it names; a plain "one about the night" is the follow-up machinery's line, which writes
# the same form about the new subject under its own lead ("A short poem about the night:").
_THE_COUNT_AGAIN = re.compile(r"\b(?:one\s+more|another\s+one|one\s+other|another)\b", re.I)
# The count asked for and nothing else: "one more", "another one", "one more please". These name
# no subject at all, so the subject is the one the verse on the screen was about, taken from its
# own lead. Read as words, "one more" is a subject like any other, and the line was given
# "A short poem about more poem:" - the filler and the form word, with the thing missing.
_THE_COUNT_WORDS = (
    r"(?:one\s+more|another\s+one|another|one\s+other|again|once\s+more|more|go\s+on|"
    r"(?:tell|give|do|write|make|say)\s+(?:me\s+)?(?:another|one\s+more|one\s+other))")
# The form the ask names for itself can come after the count: "another poem", "one more story".
_THE_FORM_AFTER_THE_COUNT = (
    r"(?:\s+(?:poem|poems|verse|verses|story|stories|rap|song|rhyme|rhymes|tale|haiku|"
    r"limerick|one))*")
_BARE_COUNT_AGAIN = re.compile(
    r"^(?:(?:ok|okay|yes|yeah|and|so|just|great|nice|lovely|good|perfect)\s+)?"
    + _THE_COUNT_WORDS + _THE_FORM_AFTER_THE_COUNT +
    r"(?:\s+(?:please|then|thanks|thank\s+you))?$")


def _a_second_verse_is_asked_for(text):
    """True when the line asks for another verse, about the thing it names or the last one's.

    "tell me more about the moon" is a question about the moon and keeps whatever answer it had;
    the ask has to be the count of verses ("one more", "another one"), not more of the subject.
    A bare count names no subject, which is the same ask about the verse already on the screen,
    and it is read first: "write me another" is the ask, not a request to be told how to write.
    """
    line = " ".join(str(text or "").lower().split())
    if not line:
        return False
    if _BARE_COUNT_AGAIN.match(line):
        return True
    if re.search(r"\b(?:tell me more|more information|what else|explain|meaning|why is|how do i|"
                 r"how to|write|writing|wrote|read|reading|book|books)\b", line):
        return False
    return bool(_SECOND_VERSE_ABOUT.search(line))


# The words people put around the thing they name: "one more about rain please" names rain, and a
# poem about "rain please" is not a thing anybody writes.
_ASK_POLITENESS = re.compile(r"\b(?:please|thanks|thank you|ta|too|as well|also|again|now|then|"
                             r"for me|for us|if you can|quick|quickly)\b", re.I)
# A subject that points at something else named in an earlier turn is not a subject: there is no
# poem about "it" or "that", so the line keeps whatever answer it had.
_NO_SUBJECT = re.compile(r"^(?:it|its|it's|that|this|them|those|these|him|her|they|one|"
                         r"the same|the other|the first|the last|another)$", re.I)


def _the_subject_from_the_ask(after_the_ask):
    """The thing a second-verse ask names: "one more about rain please" names rain."""
    words = [one for one in str(after_the_ask or "").split() if not _ASK_POLITENESS.search(one)]
    subject = " ".join(words).strip(" ,.!?;:")
    if not subject or _NO_SUBJECT.match(subject):
        return ""
    return subject


def _the_second_one_short(lead):
    """The reply for a verse asked for again when its lead named nothing to be another of.

    "tell me a poem" then "one more" wrote "A short poem about more:" - the ask read as a
    subject. A verse about nothing has nothing to be another of, so the one word it needs is
    asked for, which is what `_offer` does for a subject the form cannot carry.
    """
    form = "limerick" if re.search(r"\blimerick\b", lead, re.I) else \
        "haiku" if re.search(r"\bhaiku\b", lead, re.I) else "poem"
    return ("That last one was about nothing in particular - give me one word (the sea, my nan, "
            "the bus) and the next %s will be about that." % form)


def _a_child_story_lead(said):
    """The lead of a story written for a listener ("A short one for a 5 year old: ..."), or ""."""
    found = re.match(r"(A short one for [^:]{1,40}):\s", str(said or ""), re.I)
    return found.group(1) + ":" if found else ""


# The form a repeat ask names for itself: "another poem" after a story is a poem, and "one more
# story" after a poem is a story. The name is the ask's, and the form just given is only the
# answer when the ask names none.
_FORM_OF_A_WORD = {
    "poem": "poem", "poems": "poem", "poetry": "poem", "verse": "poem", "verses": "poem",
    "ode": "poem", "odes": "poem", "sonnet": "poem", "sonnets": "poem", "ballad": "poem",
    "rhyme": "rhyme", "rhymes": "rhyme", "rap": "rap", "raps": "rap", "song": "song",
    "songs": "song", "lyric": "song", "lyrics": "song",
    "story": "story", "stories": "story", "tale": "story", "tales": "story",
    "limerick": "limerick", "limericks": "limerick", "haiku": "haiku",
}


def _the_form_a_repeat_ask_names(line):
    """The form the ask names for itself ("another poem"), or "" when it names none."""
    named = ""
    for word in re.findall(r"[a-z']+", str(line or "")):
        named = _FORM_OF_A_WORD.get(word) or named
    return named


def _the_form_of_the_lead(lead):
    """The form the verse on the screen was written in, read out of its own lead."""
    if re.search(r"\bhaiku\b", lead, re.I):
        return "haiku"
    if re.search(r"\blimerick\b", lead, re.I):
        return "limerick"
    if re.search(r"\bstor(?:y|ies)\b|\btale\b", lead, re.I) or re.match(
            r"here is one\b", lead, re.I):
        return "story"
    if re.search(r"\brap\b", lead, re.I):
        return "rap"
    if re.search(r"\bsong\b", lead, re.I):
        return "song"
    if re.search(r"\brhyme\b", lead, re.I):
        return "rhyme"
    if _POEM_FORM.search(lead):
        return "poem"
    return ""


def the_next_verse(text, memory):
    """Another verse, in the form asked for or the form just given, or None.

    A poem asked for "one more about the moon" gets a second poem about the moon and a story asked
    the same way gets a second story, told from an opening this chat has not had yet. A bare count
    ("one more", "again", "more please") is the same ask with the thing left out: the thing is the
    one the verse on the screen was about, read from its own lead, because read as words "one more"
    is a subject like any other and "A short poem about more poem:" is what that earns. The form
    is the one the ask names ("another story" after a poem) and otherwise the one just given. A
    haiku and a limerick are fixed counts of lines, so their second one comes from the form's own
    list rather than from the table of things.
    """
    if not _a_second_verse_is_asked_for(text):
        return None
    line = " ".join(str(text or "").lower().split())
    said = ""
    for turn in reversed([one for one in ((memory or {}).get("turns") or [])
                         if isinstance(one, dict)]):
        said = str(turn.get("bot") or "")
        if said:
            break
    if not said:
        return None
    told = " ".join(str(turn.get("bot") or "") for turn in ((memory or {}).get("turns") or [])
                    if isinstance(turn, dict))
    # A story for a named listener is written on one line ("A short one for a 5 year old: The duck
    # who had forgotten how to quack ..."), so it has no lead to read and the second one is another
    # story from the child pool. Read as a verse with no subject it was handed "He had carried the
    # short from one flat to another", which is nobody's bedtime story.
    child = _a_child_story_lead(said)
    if child:
        for story in CHILD_STORIES:
            if story[:70] not in told:
                return child + " " + story
        return None
    if "\n" not in said:
        return None
    lead = said.split("\n", 1)[0]
    if not lead.rstrip().endswith(":"):
        return None
    form = _the_form_a_repeat_ask_names(line) or _the_form_of_the_lead(lead)
    if not form:
        return None
    # The subject is whatever the ask asks about, taken from the typed line itself: "one more
    # about the moon" and "and one about a dog" both end in the thing, and the reading's own
    # subject reader keeps the filler ("and one about") when the line is a follow-up.
    found = _SECOND_VERSE_ABOUT.search(line)
    subject = _the_subject_from_the_ask(line[found.end():] if found else "")
    # `_thing` reads a subject out of a phrase that names it, so a subject the ask named is read
    # from the line and a subject taken from the lead is handed back as one: "the sea" is a
    # subject and "one more" is not. A pointer ("another one about it") names nothing, and the
    # verse on the screen is what it points at.
    thing = _thing(line) if subject else ""
    if not subject:
        # The verse this chat is on, not only the last line of it: after "Another haiku:" (a lead
        # with no subject in it) the subject is still the one the verse before that named, and
        # asking for the word again two turns after it was given reads as not listening.
        for one in reversed([str(turn.get("bot") or "")
                             for turn in ((memory or {}).get("turns") or [])
                             if isinstance(turn, dict) and turn.get("bot")]):
            named = _THE_SUBJECT_IN_A_LEAD.search(one.split("\n", 1)[0])
            if not named:
                continue
            # A fixed-count form's lead carries its own note after the subject ("A haiku about
            # the sea, 5-7-5:"), and read as part of the subject it was asked back a second
            # time: "A haiku about the sea, 5-7-5, 5-7-5".
            subject = _the_subject_from_the_ask(named.group(1)).split(",")[0].strip()
            if subject:
                break
    if not thing and subject:
        thing = _thing("about " + subject)
    if form in ("haiku", "limerick"):
        # A fixed-count form with a subject named gets the form's own verse about it ("A haiku
        # about the sea", "A limerick about my tortoise"); only when that one is already on the
        # screen is there nothing left but another from the form's list.
        about_it = _say(form, thing, subject) if subject and thing else None
        if about_it and "\n" in about_it and about_it not in told:
            return about_it
        lines = NO_SUBJECT_VERSE.get(form)
        if lines and lines[0] not in told:
            return "Another %s:\n" % form + "\n".join(lines)
        # Every verse of that form is spent, and the subject is still the one asked about: say so
        # and write the short poem about it rather than shrug at a subject it has just answered.
        verse = POEMS.get(thing) if thing else None
        if verse:
            lines = [one.format(thing=thing) for one in verse]
            if lines[0] not in told:
                return ("That is every %s I have about %s - a short poem about it instead:\n"
                        % (form, subject)) + "\n".join(lines)
        return _the_second_one_short(lead)
    if form == "story":
        if not subject or not thing:
            return _the_second_one_short(lead)
        return (STORY_LEADING["story"].format(subject=subject) + "\n" +
                _the_opening_not_said_yet(thing, memory))
    if not (_THE_COUNT_AGAIN.search(line) or _BARE_COUNT_AGAIN.match(line)):
        # "one about the night" after a poem about the sea is a new poem about a new subject, and
        # the follow-up machinery already writes it under "A short poem about the night:"
        return None
    if not subject or not thing:
        return _the_second_one_short(lead)
    # The second verse keeps the name it was given: a rap about your nan is another rap, and
    # "another poem about my nan" after a rap is the wrong form handed back.
    noun = form
    for verse in (POEMS.get(thing), GENERIC_POEM, GENERIC_POEM_TWO):
        if not verse:
            continue
        lines = [one.format(thing=thing) for one in verse]
        if lines[0] not in told:
            return "Another %s about %s:\n" % (noun, subject) + "\n".join(lines)
    return "Another %s about %s:\n" % (noun, subject) + "\n".join(
        one.format(thing=thing) for one in GENERIC_POEM_TWO)


ENTRIES = [
    # "how do i make a birthday card" was given the traybake: the word "birthday" keys the cake
    # rows and "make" is how a cake is asked for, so a crafts question got a recipe. A card that
    # is being made is card stock and a pen, and the writing-in rows are a different ask.
    entry("make-a-card",
          (tuple(one + " card" for one in CARD_OCCASIONS) +
           ("homemade card", "handmade card", "make a card", "make cards", "make my own card",
            "card for my", "cards for"),
           ("make", "makes", "making", "made", "homemade", "handmade", "craft", "glue", "cut out",
            "design", "how do i make", "how to make")),
          "Fold a sheet of A5 thick paper in half, press the crease under a book, and write inside "
          "before you stick anything on - ink on a finished card is the usual ruin. One bold thing "
          "on the front, a cut shape or a photo or thick pen, and three lines inside naming "
          "something you did together beats a lot of stickers.",
          # the line that goes *inside* a card is the wording rows' question, and a playing,
          # bank or gift card is not a card anyone makes
          avoid=("write in", "writing in", "wording", "message", "poem", "verse", "rhyme",
                 "say in", "what do i write", "what should i write", "playing card",
                 "card game", "bank card", "gift card", "sim card", "memory card", "sd card",
                 "business card", "credit card", "debit card", "card payment", "birthday cake",
                 "party bag", "bake", "recipe"),
          bias=1),
    # --- films ------------------------------------------------------------------
    entry("film-family-funny", (("film", "movie"),
                                ("family", "kids", "children", "funny", "comedy") + CHILD
                                # "a film for teenagers" is the same ask for a bigger child, and
                                # it reached nothing at all
                                + ("teenager", "teenagers", "teen", "teens", "teenage")),
          _family_film, avoid=WATCHING + SPORT + SCREEN_TIME,
          guard=not_asking_what_to_watch_for, bias=1),
    # A "watch ... with my daughter" line has no "film" in it, so it needs its own way in.
    # "a film to watch for the kids" is still a film, and "what should I watch for with my
    # daughter" is a parent asking which symptoms to be alert to. The word list cannot tell them
    # apart - "watch for" stands in both - so the guard reads the asking form and a viewing noun,
    # and this row stands aside only for the ask that names nothing to watch.
    entry("watch-family", (("watch", "watching"),
                           ("family", "kids", "children") + CHILD),
          _family_film, avoid=WATCHING + SPORT + SCREEN_TIME,
          guard=not_asking_what_to_watch_for, bias=1),
    # "is it worth watching the wire", "should i read 1984", "whats the wire like": one
    # table of named works answers every way of asking for a view on one, and the ask phrases
    # are the entry's key, so a report ("i watched the wire last night") never reaches it.
    entry("worth-it",
          # the work first, the words that ask for a view on it second
          (tuple(VIEWS), JUDGE_WORDS),
          _worth_it, bias=2,
          ask=VERDICT_ASKS,
          # a gift and tonight's telly have their own entries, and neither asks what one named
          # thing is like
          avoid=("tonight", "evening", "for my", "kids", "children", "gift", "present",
                 "ticket", "cinema", "how long", "how much",
                 # "i finished breaking bad what next" names the work and the verb, and a verdict
                 # on the thing they have already watched is not the answer: the next pick is
                 "what next", "next", "what else", "anything else", "something else", "similar",
                 "like that", "recommend", "recommendation", "recommendations", "suggestions",
                 "now what",
                 # and a line that has already watched it is past the verdict: "watched all of
                 # the office" wants the next one, and a yes-or-no on starting it is no answer
                 "watched all", "seen all", "watched it all", "seen it all", "watched the lot",
                 "binged", "binge watched", "already watched", "already seen", "finished",
                 "got through", "caught up",
                 # "what should i read if i liked harry potter" names the book and asks for the
                 # next one: a verdict on the book they have just said they liked is no answer
                 "if i liked", "if i loved", "i liked", "i loved", "read after", "read next",
                 "what should i read", "recommend something like")),
    # the same ask about a work the table does not know, or one the line only calls "it"
    # the second part is only the words that stand in for a work nobody has named: a word like
    # "film" here would cost the entries that own it the rarity that ranks them
    entry("worth-it-unnamed", (UNNAMED_ASKS, ("it", "this", "that", "one", "thing")),
          _worth_it_unnamed, bias=1,
          # a pick of anything, a gift, tonight's telly and a question about a habit have their
          # own entries, and the plural is an avoid word here because no work is named anyway
          avoid=PICK_ASKS + HABIT_ASKS + ("films", "movies", "books", "shows", "series",
                                          "podcasts", "documentaries", "tonight", "evening",
                                          "for my", "gift", "present", "ticket",
                                          # "is it worth buying a smart watch" is about the
                                          # thing on the wrist, and shopping answers it
                                          "buy", "buying", "bought", "cost", "price",
                                          "spend", "subscription",
                                          # "is it worth watching my watch get repaired" is a
                                          # repair question with the viewing verb in passing
                                          "repair", "repaired", "fix", "fixing", "mend",
                                          "service",
                                          # cinema or sofa is answered on its own terms, and it
                                          # names no work at all
                                          "cinema", "at home", "on tv", "telly")),
    entry("film-tonight", (("film", "movie", "watch", "watching", "netflix"),
                           ("tonight", "evening", "something", "later", "rainy", "sunday",
                            "afternoon", "hangover", "sick day", "day off", "friday",
                            "saturday", "weekend", "night in",
                            # "recommend a film" and "what's a good film" name no evening at
                            # all, and they were the two commonest asks this entry missed.
                            "good", "recommend", "recommended", "suggest", "best",
                            # "how do i choose a film to watch" is the same request: the film and
                            # the watching were both in the line, but the choosing was the only
                            # thing it said about what it wanted.
                            "choose", "choosing", "pick", "picking", "decide", "deciding",
                            # "i want a film" and "i'm in the mood for a film" name no
                            # evening and no mood: the want is the whole ask
                            ) + WANT_ASKS + (
                            # the same present shape as a book: "a film for my dad who is 85"
                            "for my mum", "for my mother", "for my dad", "for my father",
                            "for my mum who", "for my dad who", "for my mother who",
                            "for my father who", "for my gran", "for my nan", "for my grandma",
                            "for my grandad", "for my grandpa", "for my parents",
                            "for an older", "for someone who", "for my aunt",
                            "for my uncle")),
          EASY_FILM_LIST,
          avoid=SPORT + CHILD + NOT_WATCHING
          # "i watched a film last night, it was good" and "it was a good film actually" are
          # reports, not requests
          + WATCHING
          + ("it was a", "it was good", "was a good", "went to the cinema", "went to see",
             "saw a film", "i saw", "we saw", "already seen", "have seen",
             # a mood the line turns down is the mood entries' line, and the general list is
             # the one answer that ignores what was asked for
             "isnt scary", "isn't scary", "not scary", "no scary", "nothing scary",
             "not too scary", "nothing too scary", "isnt sad", "isn't sad", "not sad",
             "nothing sad", "not too sad", "nothing too sad", "no blood", "no gore",
             "not gory", "without the gore", "not too long", "nothing heavy", "isnt funny",
             "isn't funny", "not funny", "nothing funny")
          # a series on a Friday night is the series entry's question, not the film one; and a
          # line that names a service belongs to the streaming pick, good or not
          + ("series", "show", "shows", "on telly", "on tv", "boxset", "box set", "binge",
             "episode", "episodes", "season",
             "netflix", "iplayer", "prime", "disney", "now tv", "nowtv", "streaming",
             "apple tv", "all 4", "channel 4", "paramount"),
          guard=_no_named_mood),
    # "what's on the telly tonight" names the box and nothing else, so it needs its own way in;
    # the asks about a set that will not work are about the hardware, not tonight's listings.
    entry("tv-tonight", (("tv", "telly", "television"),
                         ("on", "tonight", "whats", "what's", "anything", "showing",
                          "listings")),
          ("I can't see tonight's listings, so here is what I would start instead: *Happy Valley* "
           "if you want tense, *The Detectorists* if you want gentle, or *Groundhog Day* if you "
           "want a film you can rely on. Tell me the mood and I'll narrow it."),
          avoid=("licence", "license", "aerial", "signal", "reception", "freeview", "remote",
                 # the key holds a bare "whats", which is how every complaint is asked: "whats
                 # wrong with my tv" and "nobody will tell me whats wrong with the boiler" were
                 # both answered with tonight's listings, and the boiler one lost a correct
                 # answer to it when the rarity table shifted under a merge. A set that is not
                 # working is the fault cards' question, and they answer it well ("my tv is
                 # broken" -> the plug and the fuse), so this row stands down on the fault.
                 "wrong", "wrong with", "fault", "faulty", "broken", "broke", "gone wrong",
                 "not working", "isnt working", "isn't working", "stopped working",
                 "problem with", "keeps cutting out", "keeps going off", "keeps turning off",
                 # a set whose picture has gone wrong is a fault, not a night in: "the colour has
                 # gone on my tv" was read as tonight's listings
                 "colour", "color", "colours", "picture", "pictures", "flicker", "flickering",
                 "blank", "fuzzy", "gone funny", "patchy", "banding", "pixelated", "retune",
                 "retuning", "tuning",
                 "bracket", "wall mount", "too loud", "sound", "keeps turning",
                 # putting a set up on a wall is a DIY fixing job, not tonight's listings:
                 # "how do i hang a tv on the wall" was read as "what's on tv"
                 "wall", "walls", "hang", "hanging", "mount", "mounting", "drill", "rawplug",
                 # "the adverts on my telly are much louder" is the volume row, not tonight's
                 # listings
                 "adverts", "advert", "volume", "much louder", "louder",
                 "turns itself", "turning itself", "wont turn on", "won't turn on", "no picture",
                 "screen", "smart tv", "brand", "buy", "cheapest", "which tv",
                 # A set that will not switch on is a fault, not a night in: one word each, because
                 # a phrase in chat-speak ("wont turn on") is read back as "will not turn on" and
                 # never matches the avoid list.
                 "turn", "turns", "turning", "switch", "switching", "power", "dead", "broken",
                 "broke", "repair", "fault", "faulty", "working", "channels",
                 # a series to watch with someone is the series entry's question
                 "series", "boxset", "box set", "binge", "partner", "episode", "season")),
    # A listings ask names a place rather than a programme: "whats playing at the cinema tonight",
    # "is there anything on at the theatre" and "whats on bbc tonight" were answered with a plan
    # for a free weekend and, for the channel, with what the letters stand for. Nobody here sees
    # tonight's times, and a made-up showing is worse than the truth, so the answer says what it
    # cannot see, where the times are, and keeps the half it can still do: choose, once they know
    # what is on. The venue word is the whole subject, so it is not in tv-tonight's taxen.
    entry("listings-at-a-venue",
          (("cinema", "cinemas", "pictures", "theatre", "theater", "matinee", "gig", "gigs",
            "concert", "concerts", "arena", "playhouse", "comedy club", "comedy night",
            "arts centre", "arts center",
            # a chain or a room is the venue said by name, and the name is all some lines carry:
            # "whats showing at the odeon", "whats on at the o2 next month" and "is there a show
            # on at the o2" reached the series pick or the search hedge, because the row knew the
            # word "cinema" and not the names people actually say.
            "odeon", "vue", "cineworld", "everyman", "curzon", "picturehouse", "showcase",
            "o2", "apollo", "hippodrome", "village hall", "town hall", "venue", "venues",
            # the town said vaguely is where the listings are as well: "whats on round here" was
            # the search hedge. "near me" and "nearby" are the same word said from where the
            # person is standing - "whats on near me tonight" names no venue at all - and the
            # guard below keeps the map question ("is there a cinema near me") out of this row.
            "in town", "round here", "in the area", "locally",
            "near me", "near here", "nearby", "near where i",
            # the thing that is on instead of the place it is on at: "any events on this weekend"
            # got the nod. A "show" on its own is not a venue - "any shows on tonight" usually
            # means the telly, and the box's own row answers it - so it is a key rather than a
            # subject, and "any shows on in town" reaches this row through the town.
            "event", "events"),
           ("whats on", "what's on", "what is on", "anything on", "any on", "whats showing",
            "what's showing", "what is showing", "showing at", "showing",
            "whats playing", "what's playing", "what is playing", "playing at", "listings",
            "anything good", "are on", "is on", "show on", "shows on",
            # "any" on its own used to key this row, and with the vague place words as subjects
            # it took asks that are not listings at all: "any chance of rain in town today" got
            # the venue line, and so did "any chemist in the area" and "any plumber round here".
            # The "any" that carries a listing names the thing that is on, so that is what the
            # keys say instead.
            "any events", "any event", "any shows on", "any show on", "any gig", "any gigs",
            "any concert", "any concerts", "any play", "any film", "any films",
            "on tonight", "on at", "on friday", "on saturday", "on sunday",
            "this weekend", "on this week",
            # the place said after the ask: "is there a gig on near here" carries no ask word
            # the row knew, so the two halves only meet when they are read together.
            "on near me", "on near here", "on nearby", "on locally", "on round here")),
          ("I can't see what's on at your local venues from here, sorry. The venue's own site or a "
           "listings app has the times and the tickets, and it is the same page for a film, a play "
           "or a gig. Once you know what is on, tell me the mood or two of the names and I'll say "
           "which to go for."),
          # a ticket problem, a report of a night already had and the clothes for it are other
          # answers that name the same place: "what should i wear to the cinema" was offered a
          # film in the cinema's listings, and "can i get a refund on a theatre ticket" a night
          # out to plan. A plan already made is not a listings ask either: "me and sarah are
          # going to the cinema on friday" is the diary, and it was answered with the times
          # instead of "Noted: you and sarah are going to the cinema on friday".
          avoid=("refund", "refunds", "money back", "ticket", "tickets", "cancelled",
                 "cancel", "lost", "sell", "selling", "sold", "queer", "wear", "wearing",
                 "wore", "dress", "outfit", "sad", "weird", "alone", "on your own",
                 "on my own", "worth it", "reviews", "review", "spoiler", "spoilers",
                 "nearest", "the nearest",
                 "i have", "we have", "ive got", "i've got", "we've got", "weve got",
                 "im going", "i'm going", "we are going", "we're going", "were going",
                 "going to", "me and", "booked",
                 # a night already had is a report, and a thing seen at one is a thing seen
                 "went to", "been to", "we saw", "i saw", "watched", "last night i",
                 # the box at home is not a venue: "is there a show on tv tonight" is tonight's
                 # telly and its own row answers it with three things to watch, so the set and
                 # the services stand this row down.
                 " tv", "tv ", "on telly", "the telly", "telly", "iplayer", "netflix",
                 "prime video", "disney+", "now tv", "channel", "channels", "freeview",
                 # an event of their own is theirs and not a public listing: "any events planned
                 # at work" is about the office, and the venue line was no answer to it.
                 "at work", "for work", "work event", "work do", "office", "my team",
                 "in the office"),
          guard=_a_listings_ask_near_me),
    # The channel is the same gap said the other way round: "whats on bbc tonight" is the guide
    # that is on the telly, not the letters. Named channels only, because a bare "whats on" is
    # the diary's ask and the box's own entry already answers it.
    entry("listings-on-a-channel",
          (("bbc", "bbc one", "bbc1", "bbc two", "bbc2", "bbc four", "itv", "channel 4",
            "channel four", "c4", "channel 5", "channel five", "sky", "dave", "itv2",
            "itvbe", "more 4", "film4", "quest", "radio", "radio 4", "radio 2",
            "local radio", "talksport"),
           ("whats on", "what's on", "what is on", "anything on", "whats showing",
            "what's showing", "whats playing", "what's playing", "on tonight", "tonight",
            "listings", "schedule", "schedules", "showing", "playing")),
          ("I can't see the schedule from here, sorry. The guide on the telly, or the station's "
           "own app, has the times, and the catch-up players - iPlayer, ITVX, Channel 4, BBC "
           "Sounds - keep the same list on the front page. Tell me the mood and I'll name "
           "something worth catching."),
          avoid=("stand for", "stands for", "mean", "means", "licence", "license", "fee",
                 "adverts", "advertising", "remote", "aerial", "signal", "reception",
                 "freeview", "retune", "retuning", "tuning", "channel changer", "tune to",
                 "no signal", "wont", "won't", "broken", "repair")),
    # Which service to take out at all is a different question from what to watch on one:
    # "which streaming service should i get" named a service and then asked about none of them.
    # The answer is the one that is true whichever house it is - nobody can tell you the best
    # one, but a month at a time and one at once can be worked out for free.
    entry("pick-a-streaming-service",
          (("streaming service", "streaming services", "streaming subscription",
            "streaming subscriptions", "streaming", "netflix", "disney", "prime video",
            "now tv", "nowtv", "apple tv", "iplayer", "subscription"),
           ("which", "what", "best", "worth it", "should i get", "should i have",
            "should i pay", "choose", "pick", "worth", "get", "need", "one")),
          ("Take one at a time, a month at a time, and cancel when the series ends: almost every "
           "service sells monthly with no contract, so a year of switching costs far less than a "
           "year of all of them. Two are worth keeping at once at most - one for the family "
           "boxsets and one for what you watch live, football or the soaps. Check the service "
           "you already pay for through the TV or broadband bundle before adding another, "
           "because that is where the cheapest month usually hides."),
          # a pick on a named service, a series, a film, a price and cancelling are their own
          # questions, and the licence is not a subscription. Two services named with "or" is a
          # choice between them, which this card (how to buy) does not answer.
          avoid=("good", "anything", "recommend", "watch", "watching", "film", "films", "series",
                 "show", "shows", "boxset", "box set", "episode", "cancel", "cancelling",
                 "expensive", "price", "cost", "cheap", "deal", "free", "licence", "license",
                 "tonight", "movie", "movies", "comedy", "documentary", "sport",
                 "netflix or", "or netflix", "iplayer or", "or iplayer", "prime or", "or prime",
                 "disney or", "or disney", "nowtv or", "or nowtv", "britbox or", "or britbox",
                 "apple tv or", "or apple tv", "paramount or", "or paramount"),
          bias=1),
    # A streaming service plus "anything good" is a pick, not a subscription question.
    entry("streaming-good", (("netflix", "iplayer", "prime", "disney", "now tv", "nowtv",
                              "streaming", "apple tv", "all 4", "channel 4", "paramount"),
                             ("good", "anything", "what", "whats", "what's", "recommend",
                              "suggest", "worth watching", "watch", "tonight", "best",
                              # "any netflix recommendations" names the service and asks for a
                              # pick, and the noun "recommendations" is not a form of the verb
                              # "recommend", so the row missed the commonest way people ask it
                              # and the line got the chat nod: "Got it. Is there anything you'd
                              # like a hand with?"
                              "recommendation", "recommendations", "suggestion",
                              "suggestions", "ideas")),
          ("On any of them: *Knives Out* for a whodunnit everyone enjoys, *Happy Valley* or *The "
           "Bear* for a series you'll finish, *Paddington 2* if children are in the room. Say "
           "which service and the mood and I'll narrow it down."),
          avoid=("cancel", "subscription", "how much", "cost", "price", "password", "account",
                 "log in", "login", "signed out", "not working", "wont load", "won't load",
                 "buffering", "download", "free trial", "worth it", "scam", "charge",
                 # a named mood is the mood entry's question, not this one
                 "comedy", "comedies", "funny", "sitcom", "laugh", "scary", "horror",
                 "thriller", "romance", "romantic", "documentary") + CHILD),
    entry("watch-tonight", (("watch", "watching"), ("tonight", "evening", "what", "should")),
          ("For tonight: *Groundhog Day* (funny), *Knives Out* (a clever whodunnit) or *Arrival* "
           "(if you want to think). On a series instead, *Happy Valley* is tense and *The "
           "Detectorists* is gentle. All easy picks with no homework needed."),
          avoid=WATCHING + CHILD + SPORT + NOT_WATCHING),
    # A streaming service plus a comedy is a series request, not a film one.
    entry("streaming-comedy", (("netflix", "iplayer", "prime", "disney", "now tv", "nowtv",
                                "streaming", "hayu", "apple tv"),
                               ("comedy", "comedies", "funny", "sitcom", "laugh")),
          ("*Schitt's Creek* is the safe pick: short episodes, funny from the first series. "
           "*Derry Girls* if you want something sharper, or *Paddington 2* if it's a film "
           "tonight rather than a series."),
          avoid=("cancel", "subscription", "how much", "cost", "worth it", "password",
                 "account") + WATCHING),
    entry("film-like", (("film", "movie"), ("like", "liked", "likes", "similar", "loved",
                                           "loves", "enjoyed")),
          _film_like,
          avoid=("gift", "present", "birthday", "christmas", "get my", "buy", "for my dad",
                 "for my mum") + CHILD),
    # "scary" cuts both ways: a person asking *for* a scare wants a different answer from
    # one asking to be spared it, so the two asks are separate entries and this one only
    # answers a line that actually wants to be frightened.
    entry("film-want-scary", (("film", "movie", "series", "watch", "watching"),
                              ("scary", "scariest", "scare", "scares", "horror", "horrifying",
                               "frightening", "creepy", "terrifying", "spooky", "jump scares")),
          ("For a proper scare: *Get Out* is the smart one and not gory, *A Quiet Place* is jumpy "
           "from the first minute, and *Hereditary* is the genuinely unnerving one. For an "
           "old-fashioned ghost story, *The Others*."),
          # "i dont want a scary film" refuses the scare: the wanting verb hides the negator from
          # the mood reader, and this row keyed "scary" alone answered with the scariest picks.
          avoid=("dont want a scary", "dont want scary", "dont want a horror", "dont want horror",
                 "dont want anything scary", "dont want to be scared",
                 "dont want a film that is scary", "do not want a scary", "do not want scary",
                 "dont want a sad one", "dont want anything sad",
                 "not scary", "isnt scary", "isn't scary", "no scary", "nothing scary",
                 "without the scary", "scared of", "hate horror", "dont like horror",
                 "don't like horror", "cant stand horror", "can't stand horror", "no gore",
                 "gory", "blood", "hate scary", "scared easily", "scare easily",
                 "easily scared", "frightened easily", "easily frightened", "get scared",
                 "gets scared", "scare me", "scares me", "not too scary",
                 "nothing too scary") + CHILD,
          ask=("want", "recommend", "suggest", "good", "something", "any", "worth", "fancy",
               "in the mood", "looking for", "tonight", "whats", "what film", "what movie",
               "which", "should i watch", "anything", "be scared", "be frightened",
               # naming the scare is asking for one: "a scary film" has no other ask word
               "scary", "scariest", "horror", "creepy", "spooky", "terrifying", "frightening",
               "jump scares",
               # a night that is for being frightened names no ask word of its own
               "halloween", "spooky night", "fright night"),
          # A line that names a scare to turn it down is the other row's question, whatever words
          # it uses to do it. The avoid list above still carries the wordings it was written for;
          # this is what catches the next one.
          guard=_the_scare_is_wanted,
          bias=2),
    # The gentle list is for a line that asks to be SPARED a scare. Without its own ask words
    # it claimed every film line with "scary" in it and turned down people who wanted one:
    # "a scary film for halloween" got "Skip horror and gore".
    # The gentle list is the answer to every line that turns a scare down, however it says so, so
    # its key holds the words a person watches with rather than only the word "film": "something
    # not scary to watch" and "anything but horror please" name no film at all, and both fell
    # through to "I'm listening" while the scare word in them was plain to read.
    entry("film-nothing-scary", (("film", "films", "movie", "movies", "series", "watch",
                                  "watching", "telly", "tv",
                                  "netflix", "something", "anything",
                                  # A turn-down inside an ask for a film is the whole line, and
                                  # the ask words alone are cheap enough that a row sharing only
                                  # one of them outranked this one: "im not into scary stuff what
                                  # should i watch" went to a stuffing recipe, because "stuffing"
                                  # and "stuff" are the same word to the matcher and the recipe's
                                  # ask part took the rest. So the ask phrases are here, and the
                                  # row carries `bias=2` to be worth more than the word "stuff".
                                  # They are in THIS group and not a group of their own: score()
                                  # wants two covered words across the key and does not want one
                                  # per group, so a third group let this row in on a film word
                                  # plus an ask phrase with no scare word in the line at all, and
                                  # every other turn-down got the horror answer - "im not into
                                  # rom coms what should i watch", "i dont want anything sad what
                                  # should i watch", "i dont like sci fi", "im not into musicals".
                                  # The scare word is the subject, so the subject group has to be
                                  # the one that is always read.
                                  # Not "what to watch": "not sure what to watch, something
                                  # scary?" wants the scare, and the ask phrase is the only part
                                  # of this key it shares.
                                  "what should i watch", "should i watch", "should we watch",
                                  "anything to watch", "something to watch"),
                                 ("gory", "scary", "horror", "blood", "scare", "spooky", "creepy",
                                  "frightening", "terrifying", "scared", "haunted")),
          # The answer says what the person wants, never what they turned down. It used to open
          # "Skip horror and gore ... without any blood", and the next line of the conversation
          # read that word back as the subject: "i dont want a scary film what should i watch"
          # then "anything a bit lighter" answered with *Get Out* and *The Haunting of Hill
          # House*. A follow-up is read with the turn before it, so the bot's own turn must not
          # name the thing the person just refused.
          _the_gentle_list,
          bias=2,
          # "what else is good" after this answer is somebody who wants another shelf, and the
          # row is the one that keeps the refusal the chat is on, so it answers that too.
          ask=("not", "isnt", "isn't", "no", "without", "nothing", "hate", "dont", "don't",
               "else", "another", "other", "more",
               "cant", "can't", "easily", "gore", "gory", "blood", "scared", "frightened",
               "anything but", "apart from", "except", "other than", "not for me", "avoid",
               "spare me", "too much"),
          guard=_a_film_ask, avoid=CHILD),
        # "sci fi" written as two words is the same ask as "sci-fi", and the hyphen was the only
    # spelling these two entries took: "any good sci fi films" reached the general film list
    # instead, and "any sci fi books" reached the general book list.
    # A person who says what they do NOT want is still asking for a film. The mood reader
    # answers the refused moods it can name, and the kinds of film that are not moods at all -
    # a documentary, a musical, a cartoon, anything with subtitles - had no way out: the line
    # reached the composer as a bare follow-up and got "I'm listening". This is the floor for
    # that shape, and it offers the easy three rather than asking a question back.
    entry("film-dont-want", (("film", "films", "movie", "movies", "watch", "watching",
                              "netflix", "telly", "tv",
                              # a kind of programme named on its own is still an ask for
                              # something else to watch: "i dont want a cartoon"
                              "cartoon", "cartoons", "documentary", "documentaries",
                              "musical", "musicals", "anime", "sitcom", "thriller"),
                             ("dont want", "do not want", "dont really want", "dont fancy",
                              "dont feel like", "not in the mood for", "bored of",
                              "bored with", "tired of", "sick of", "no more", "anything but",
                              "nothing with", "not into", "dont like",
                              # "christmas films are not for me" turns the shelf down with no
                              # "want" in it, and once the shelf stands down for that reading
                              # this row is the one that has to catch it, or the line gets an ack.
                              "not for me", "are not for me", "is not for me", "not my thing",
                              "not my kind of film", "not my cup of tea", "not my sort")),
          FILM_MOODS["light"],
          # the refusals that name a mood with a list of its own keep that answer, and so do
          # the kinds of film another row already answers, a child's film, a sport, and a report
          # of what was already watched
          avoid=("sad", "scary", "horror", "gore", "gory", "blood", "heavy", "cry", "funny",
                 "romance", "rom com", "romcom", "series", "boxset", "box set",
                 # "i dont want to see them again" is about a person, and the two-word rule was
                 # satisfied by the phrase alone: "dont want" covers two words, so a refusal
                 # with no film in it got a light film. The refusals that name a person are
                 # listed, not the bare words, because "a film for a date night" is still a film.
                 "them again", "him again", "her again", "me again", "this person", "this guy",
                 "this girl", "the guy", "the girl", "my ex", "ex boyfriend", "ex girlfriend",
                 "break up", "breaking up", "broke up", "dump", "dumped", "tell someone",
                 "let them know", "gently", "let him down", "let her down")
          + CHILD + SPORT + NOT_WATCHING + WATCHING),
    entry("film-space", (("film", "movie"), ("space", "sci-fi", "sci fi", "scifi",
                                             "science fiction")),
          ("*Arrival* is the smartest one, *Apollo 13* the most tense, and *Interstellar* the "
           "biggest. For something lighter, *Galaxy Quest* is a lovely comedy about actors on a "
           "spaceship.")),
    # "something sad to watch", "a film that makes you think", "a film thats not too long":
    # the mood is the ask and the medium is read off the line, so one entry answers every
    # phrasing of it (see MOODS above).
    # "give me something funny to watch" was the one mood ask that got the general tonight list:
    # the film-tonight row counts the ask phrase "give me" and this one did not, so it scored one
    # point more and the laugh list lost the line to *Groundhog Day*, *Knives Out* and *Arrival*.
    # The ask form belongs in this key as well.
    entry("film-mood", (("film", "films", "movie", "movies", "watch", "watching",
                         "something to watch", "give me something", "give me a film",
                         "give me a movie"),
                        # a scare has its own two entries, which tell a want from a worry
                        _mood_key_words({m: MOODS[m] for m in MOOD_ORDER if m != "scary"},
                                        drop=MOODS["scary"])),
          _mood_pick(FILM_MOODS), bias=1,
          avoid=WATCHING + CHILD + SPORT + SCREEN_TIME + NOT_WATCHING
          + ("gift", "present", "birthday", "christmas", "for my", "for someone",
             "my tv", "telly", "aerial", "remote", "noise", "sound", "picture", "broken",
             "broke", "repair", "fault", "faulty", "not working", "subscription", "cancel",
             "password", "account", "licence", "license", "record", "make a film",
             "make a video", "edit a video", "watch for", "symptoms", "signs of")),
    # "who wrote pride and prejudice", "who is the author of 1984": the ask words are the key,
    # and the reply is a lookup, so a line about a book nobody wrote here falls through.
    entry("who-wrote-book",
          (("who", "who's", "whos", "whose", "which author"),
           ("wrote", "write", "writes", "written", "author", "authors", "book", "books",
            "novel", "novels", "play", "plays", "poem", "poems", "story", "stories")),
          _who_wrote, bias=1,
          # "can you recommend a book for my dad who never reads" has a "who" and a "book" in
          # it and is asking for a pick, not for an author.
          avoid=("recommend", "suggest", "pick", "read next", "should i read", "to read",
                 "for my", "for a", "for someone", "gift", "present", "never reads",
                 "not a reader", "doesn't read", "doesnt read")),
    # "did jane austen write emma", "what else did roald dahl write": the author's own name is
    # the signal, so only a line naming someone in the table reaches this one at all. Someone
    # writing their own story is not asking about a published one, even when a name in the table
    # turns up in it ("a story where the villain poisons the king" is not Stephen King).
    entry("author-other-books", (AUTHOR_KEYS, ASKED_WROTE), _who_wrote, bias=1,
          avoid=MAKING_UP),
    # A book named by somebody who liked it wants the one that follows, whatever words the ask
    # uses. The table holds the titles; a title nobody here knows gets an honest question rather
    # than a made-up match, and a line that names no book at all falls through to the pick below.
    entry("book-like", (BOOK_LIKE_THINGS, BOOK_LIKE_ASKS), _book_like, bias=3,
          guard=_a_genre_is_the_taste,
          avoid=("gift", "present", "birthday", "christmas", "get my", "buy", "for my dad",
                 "for my mum", "read to", "reading to", "aloud", "learn to read", "writing",
                 "write a", "book a hotel", "hotel room", "hotels in", "a hotel in", "stay in",
                 # not the bare word "hotel": *The Glass Hotel* is a title, and
                 # "something like the glass hotel" is a book question
                 "flight", "flights", "tickets",
                 # the film table answers for films: "a film like the martian" wants films
                 "film", "films", "movie", "movies", "watch", "watching", "series", "tv",
                 "telly", "cinema", "netflix", "episode", "episodes", "box set", "actor",
                 "actors")
          # not CHILD as a blanket: "diary of a wimpy kid" is a title, and the child words in a
          # title used to stand the whole table down for it. The callable stands down for a real
          # child in the line instead, with the titles taken out first.
          + WATCHING),
    entry("book-recommend", (("book", "books", "read", "reading", "novel"),
                              # "i want a book" and "i fancy a book" name no mood and no kind:
                              # the want is the whole ask
                              WANT_ASKS + (
                               "recommend", "suggest", "good", "next", "something", "what should",
                               # "what book should i read" names the book and the verb and no ask
                               # word at all, and it is how most people put it
                               "what book", "what books", "any books",
                               "book to read", "books to read",
                               # "should i read" was here and is a shape, not a topic: every
                               # line that says it reached a novel, and "should i read the
                               # instructions" and "which email should i read first" lost their
                               # own answers to *The Thursday Murder Club*. The ask that names
                               # the book stays: "what should" covers "what novel should i read"
                               # and "which should i read", and neither can be said about an
                               # email or a set of instructions.
                               "what should", "which should i read", "which book",
                               # the words that name the thing itself are the safest ask there
                               # is: nobody says "novel" about an email or a set of instructions
                               "novel", "novels",
                               "worth reading", "is it worth reading",
                               # a book to read *to* someone names the listener, and it is the
                               # same request for a pick
                               "read to", "reading to", "read aloud",
                               # "a book for my mum who is 80" names the reader instead of the
                               # mood: the present words below still hold out the gift shape.
                               "for my mum", "for my mother", "for my dad", "for my father",
                               "for my mum who", "for my dad who", "for my mother who",
                               "for my father who", "for my gran", "for my nan", "for my grandma",
                               "for my grandad", "for my grandpa", "for my parents",
                               "for an older", "for someone who", "for my aunt",
                               "for my uncle",
                               # "what about a book for her" carries the book and the person
                               # and no ask word at all: a follow-up that changes the medium
                               # says "what about", which is the whole ask.
                               "what about", "how about", "for her", "for him", "for them",
                               # "my book is boring" names the book and how it is going, and
                               # the pick is what follows: no ask word at all is in the line.
                               "boring", "dull", "slow", "not enjoying", "struggling with",
                               # the ask said as the state it leaves them in: "i finished my
                               # book and now i dont know what to read" is a statement as often
                               # as a question, so the want is the whole ask again. A mood word
                               # such as "not depressing" stays out: the mood rows answer that
                               # one better than the general pick does.
                               "what to read", "to read next", "read next", "finished")),
          _book_recommend,
          # a reservation is not a read, and the booking rows answer those lines
          guard=lambda understood: (not the_book_is_a_reservation(understood)
                                    and _no_named_mood(understood)),
          avoid=("gift", "present", "birthday", "christmas", "get my", "buy",
                 # "read to" and "reading to" used to be here, and "what book should i read to my
                 # class" was a punt because of it: reading aloud to somebody is a book pick, and
                 # a key part that the same row vetoes can never answer anything. "learn to read"
                 # stays, because teaching a child to read is a different question.
                 "learn to read", "short", "sci-fi",
                 "scifi", "science fiction", "space", "fantasy", "dragons", "magic",
                 "thriller", "crime", "murder", "twist", "romance", "horror", "war",
                 "history", "funny", "comedy",
                 # a book for the flight is the holiday reading answer, not the general pick
                 "holiday", "holidays", "beach", "flight", "flights", "plane", "on holiday",
                 # a mood the line turns down is the mood entries' line
                 "isnt scary", "isn't scary", "not scary", "nothing scary", "not too scary",
                 "nothing too scary", "isnt sad", "isn't sad", "not sad", "nothing sad",
                 "not too sad", "nothing too sad", "not too long", "nothing heavy",
                 "isnt funny", "isn't funny", "not funny", "nothing funny",
                 # "read" is not always a book: the word in the line after it says what is being
                 # read, and a label, the news, a meter or a set of instructions is answered by
                 # its own row or by nobody. "can you read the label for me" and "i want to read
                 # the news" both got *The Thursday Murder Club* before these.
                 "label", "labels", "news", "meter", "map", "maps", "instructions", "manual",
                 "recipe", "recipes", "menu", "spreadsheet", "report", "email", "emails",
                 "letter", "sign", "timetable", "bill", "invoice", "forecast", "thermometer",
                 "gauge", "the room", "situation", "contract", "terms and conditions",
                 "small print", "balance", "statement", "essay", "exam paper",
                 # a funeral is not a reading list either: "any ideas for a reading at the
                 # funeral" was answered with *The Thursday Murder Club*, and the reading at a
                 # service is its own row in the family entries
                 "funeral", "funerals", "memorial service", "eulogy", "cremation", "burial",
                 "graveside")),
    # "whats a good book about gardening", "best book for learning guitar", "a book on chess":
    # the subject is the question, and the tips for the hobby itself are a different answer.
    # The pick comes from SUBJECT_BOOKS, and a subject we have no pick for returns None so the
    # line falls through instead of getting a novel.
    entry("book-about-a-subject", (("book", "books", "novel", "read", "reading"),
                                   # the second key is how the subject is introduced: "a book
                                   # about X", and also who the book is for - "a book for my dad
                                   # who likes history" names a subject, and the who-likes words
                                   # are what the anchor reads past to reach it. The row stands
                                   # down on its own when no subject follows (`_book_about`
                                   # returns None), so the wider key costs nothing.
                                   # "recommend a poetry book" names the subject in front of the
                                   # word and has no "about" in it, so the asking words are in
                                   # this second position too.
                                   ("about", "on", "covering", "learn", "learning",
                                    "beginners", "beginner", "guide", "introduction",
                                    "who likes", "who loves", "who enjoys", "who is into",
                                    "a fan of", "likes", "loves", "enjoys", "into",
                                    "interested in", "keen on", "interested", "keen",
                                    "recommend", "recommended", "suggest", "suggestion",
                                    "best", "good", "any", "one")),
          _book_about, bias=3,
          # a book for a present, for a holiday or for a child is its own answer; the subject
          # table has nothing to say about who it is for. "for my dad" is out of this list on
          # purpose: with a who-likes clause after it the subject is the question, and without
          # one the row stands down by itself.
          avoid=("gift", "present", "birthday", "christmas", "holiday", "holidays", "beach",
                 "flight", "train", "bus", "commute", "journey", "audio book", "audiobook",
                 "read to", "reading to", "learn to read", "my son", "my daughter",
                 "for a child", "for kids"),
          # "i need to book a hotel for my dad who likes history" is a hotel: the who-likes
          # clause now reads as a subject, and the verb "book" is what the line is really doing
          guard=_not_a_reservation),
    entry("book-thriller", (("book", "novel", "read", "reading"),
                            ("thriller", "twist", "crime", "murder")),
          _book_thriller),
    # A book read by the mood it should leave: "a really sad book", "a book that makes you
    # think", "a short book". The holiday, gift, child and habit lines keep their own entries.
    entry("book-mood", (("book", "books", "novel", "novels", "read", "reading"),
                         # "funny" is the book-funny entry's, which names its own three
                         _mood_key_words({m: MOODS[m] for m in MOOD_ORDER if m != "funny"},
                                         drop=MOODS["funny"])),
          _mood_pick(BOOK_MOODS), bias=1,
          avoid=("funny", "comedy", "laugh", "hilarious", "gift", "present", "birthday",
                 "christmas", "for my", "for someone", "read to", "reading to",
                 "learn to read", "aloud", "how do i read", "how to read", "writing",
                 "write a", "hotel", "flight", "flights", "appointment", "who wrote", "author",
                 # a journey has the holiday-read answer, which names easier books
                 "train", "holiday", "holidays", "beach", "plane", "commute", "journey",
                 # a title that has slipped wants the name back, not a book to read next:
                 # "i cant think of the name of a book" and "i forgot the name of a book i read"
                 # were both answered with three mood picks. None of these is a word this row's
                 # own key needs ("book", "read", "novel" are the key and stay out of this list).
                 "the name of", "name of that", "name of a", "name of the", "name of my",
                 "remember the name", "what was that called", "whats it called",
                 "what's it called", "cant think of the name", "can't think of the name")
          + CHILD),
    # "a funny series", "something gentle on telly": a series is its own medium with its own
    # picks, and a line naming one used to reach no table at all. A line naming a streaming
    # service keeps the entry below it, which names three comedy series.
    # "is there a good cooking show" was answered with a tense crime drama and "what documentary
    # should i watch" with a film: a subject named by the person is the question, and the mood
    # tables only answer the other way round. Above the mood rows so the subject wins the tie.
    entry("show-about-a-subject", (SHOW_MEDIUM_WORDS, tuple(SHOW_SUBJECT_NAMES)),
          _show_about, bias=2, avoid=SHOW_SUBJECT_AVOID, guard=_a_programme_is_wanted),
    entry("a-documentary-pick", (SHOW_DOC_ASK_WORDS,
                                ("documentary", "documentaries", "docuseries", "docu series")),
          SHOW_SUBJECTS["documentary"], bias=2, avoid=SHOW_SUBJECT_AVOID,
          guard=_a_documentary_is_wanted),
    entry("tv-mood", (("series", "show", "shows", "boxset", "box set", "binge", "episode",
                       "episodes", "telly", "on tv"),
                      MOOD_SIGNALS),
          _mood_pick(TV_MOODS), bias=1,
          # a set that will not work is the repair answer's line, and a mood word in it ("wont
          # turn on" carries the "turn" of "turn my brain off") must not turn it into a pick
          avoid=SCREEN_TIME + CHILD + SPORT
          + ("netflix", "iplayer", "streaming", "cancel", "subscription", "password",
             "account", "aerial", "remote", "repair", "broken", "not working", "noise",
             "sound", "picture", "licence", "license", "how much", "cost", "worth it",
             "how many episodes", "how long",
             "turn on", "turns on", "turn it on", "wont turn", "will not turn", "not turning",
             "switch on", "switched on", "switching on", "wont switch", "plug", "fuse",
             "signal", "channels", "channel", "standby", "blank", "black screen", "screen",
             "freezing", "frozen", "keeps going off", "turns itself off", "is dead", "died",
             # a person who is frightened by horror wants to be spared it, not given more
             "scares me", "scare me", "scared of", "scared easily", "easily scared",
             "frightened of", "hate horror", "not scary", "nothing scary", "cant stand horror",
             "hate scary", "no horror", "no gore")),
    # "a podcast thats scary", "something gripping to listen to": the same table for the third
    # medium. "funny" has its own podcast entry that names three funnier shows.
    entry("podcast-mood", (("podcast", "podcasts"),
                           _mood_key_words({m: MOODS[m] for m in MOOD_ORDER
                                            if m != "funny"},
                                           drop=MOODS["funny"])),
          _mood_pick(PODCAST_MOODS), bias=1,
          avoid=("how do i", "how to", "start a", "make a", "record", "edit", "mic",
                 "microphone", "upload", "spotify", "apple", "listen to music") + CHILD),
    # "something funny" with no film, book or podcast in it is still a request for one: the
    # chat has already said which medium it is on, and the table above answers for it. A line
    # that names a medium is the film, book, series or podcast row's own question, and a chat
    # about something else is somebody else's.
    entry("a-mood-anywhere", (MOOD_SIGNALS, ANY_MOOD_ASKS), _a_pick_in_any_medium,
          avoid=NOT_A_MOOD_PICK, bias=1),
    # The turn after a pick, when the mood is turned down ("no not too scary"): the same table at
    # its other end, because handing the same scary list back is the one reply that ignores what
    # the person said. `a-mood-anywhere` needs an ask word and a refusal has none.
    entry("a-mood-turned-down", (MOOD_SIGNALS, TURNS_IT_DOWN), _a_pick_of_the_other_mood,
          avoid=TURNED_DOWN_KEEPS_ITS_OWN, bias=1),
    # "book" is a verb as well as a thing, so a bare "book" key let "just booked flights to Spain"
    # and "we booked a table" reach the reading list; since the knowledge base declares its topics
    # (#54) that entry wins the turn, so the wrong answer is the one the person gets. The first
    # part asks for reading intent and the phrase "book for" needs the book sense, while a flight
    # stays where a book is read ("what should i read on the flight").
    entry("book-holiday", (("read", "reading", "novel", "book for", "books for",
                            "book on the", "books on the", "book to", "book should i",
                            "book recommendation", "book recommendations"),
                           ("holiday", "beach", "flight", "flights", "plane", "easy", "light",
                            "holiday reading", "holiday read", "train", "bus", "coach",
                            "journey", "commute", "tube")),
          ("For a holiday read: *The Thursday Murder Club* (funny, short chapters), *Lessons in "
           "Chemistry* (warm and clever), or *The Midnight Library* (gentle and quick). All three "
           "are easy to pick up and put down."),
          # "how do I book holiday at work" is a time-off question, not a reading one.
          ask=("read", "reading", "reads", "recommend", "recommendation", "recommendations",
               "novel", "fiction", "book", "books", "should i read", "worth reading"),
          # The object of "read" decides the meaning: a bus or train timetable, a schedule and a
          # map are read on the way somewhere and none of them is a book, so "how do i read a
          # bus timetable" was getting the Thursday Murder Club. Reading a thing that is not a
          # book is its own answer (read-a-timetable, in travel.py, and read-a-craft-pattern in
          # home.py), and this entry stands down for it.
          avoid=("timetable", "timetables", "schedule", "schedules", "departure board",
                 "departures", "bus times", "train times", "time table", "pattern",
                 "patterns", "map", "maps", "knitting", "crochet", "sewing", "ruler",
                 "tape measure", "spirit level", "meter", "recipe", "chart")),
    # Giving up on a book is its own question - how long to give it, and permission to stop -
    # and it was reaching the lapsed-reader row, which answers "what should I read next".
    entry("book-abandon", (("book", "books", "novel", "novels", "read", "reading",
                            "audiobook", "audiobooks"),
                           ("give up", "gave up", "finish", "finishing", "losing interest",
                            "lost interest", "bored", "boring", "slog", "struggling",
                            "dont like", "don't like", "not enjoying", "not into it",
                            "abandon", "put it down", "halfway", "half way", "started and")),
          ("Give it about 50 pages, or a tenth of the book if it is a long one, and then stop "
           "without guilt if you still do not care: there are more books than evenings. Halfway "
           "through and dreading it is as clear a sign as you get - put it down, and keep it for "
           "a long train journey in case you come back to it. Finishing a book you dislike is not "
           "a virtue, and nobody is marking it."),
          ask=("should i", "is it ok", "is it okay", "do i", "when", "how long", "how many",
               "worth", "or not"),
          bias=1),
    entry("book-not-a-reader", (("book", "read", "reading", "into reading",
                                "get into reading", "back into reading"),
                               ("rarely", "not much", "hardly", "never", "doesn't read",
                                "dont read", "short", "again", "habit", "lapsed",
                                "used to read", "haven't read", "havent read",
                                "stopped reading", "finish a book", "get back into",
                                "back into")),
          ("Start with something short and gripping: *Of Mice and Men* (about 100 pages), *The "
           "Curious Incident of the Dog in the Night-Time*, or any *Reacher* book by Lee Child. "
           "Short chapters and a fast plot matter more than literary prizes when you're out of "
           "the habit."),
          # Reading is also something an eye operation interrupts and something a child needs
          # doing for them, and neither of those is a lapsed reading habit.
          avoid=("eye", "eyes", "eyesight", "surgery", "operation", "glasses", "contact lens",
                 "aloud", "out loud", "to my child", "to my son", "to my daughter", "my kid",
                 "my son", "my daughter", "toddler", "year old", "years old", "school",
                 "podcast", "audiobook", "listen", "film", "series", "after a stroke",
                 # giving up on a book is book-abandon's question, not "what next"
                 "give up", "gave up", "losing interest", "lost interest", "bored", "boring",
                 "halfway", "half way", "finish it", "dont like", "don't like", "not enjoying",
                 "slog", "struggling"),
          # "a present for my dad who never reads" is a book question that the gift rows tie
          # with on "present" and "dad": the words "never reads" are what makes it one, and
          # they are in this entry's key, so the tie goes to the books.
          bias=1),
    entry("book-funny", (("book", "books", "novel", "read", "reading", "recommend"),
                        ("funny", "comedy", "laugh", "light-hearted", "lighthearted",
                         "cheerful", "feel-good", "feelgood")),
          ("For funny, *The Thursday Murder Club* by Richard Osman is the easy pick: short "
           "chapters, a mystery that keeps moving, and jokes on every page. *Three Men in a Boat* "
           "if you want an old one that still makes people laugh out loud, or *Good Omens* by "
           "Pratchett and Gaiman for something daft and warm."),
          # An adult pick is no use to a seven-year-old, so a child in the line passes.
          # So does a line that names another medium: "recommend" alone is not a book word,
          # and "recommend a funny podcast" must not get a novel.
          avoid=("kid", "kids", "child", "children", "son", "daughter", "toddler", "teen",
                 "teenager", "year old", "years old", "grandchild", "boy", "girl", "school",
                 "podcast", "podcasts", "listen", "listening", "audiobook", "audiobooks",
                 "film", "films", "movie", "movies", "series", "netflix", "iplayer",
                 "stream", "streaming", "tv",
                 # A comic is a medium, not a mood. "would a comic count as reading" was answered
                 # with The Thursday Murder Club because "comic" sat in this entry's key beside
                 # nothing that picked the sense, so a comic line is left to the book-comics row
                 # and to the count-as row in study.py rather than given a novel (found on
                 # `0231e351`).
                 "comic", "comics", "comic book", "comic books", "graphic novel", "graphic novels",
                 "manga",
                 "count as reading", "counts as reading", "count as a book", "count as books",
                 "still reading", "proper reading", "reading practice", "reading practise")),
    # A comic is a medium, and the answer to "recommend a comic" is a comic. It used to be a
    # parent's reading card (a comic in study.py's child key) or *The Thursday Murder Club* (a
    # comic in the mood of the row above), which are both answers about something that was not
    # asked. A pick for a child and a question about whether a medium counts are not this row.
    entry("book-comics",
          (("comic", "comics", "comic book", "comic books", "graphic novel", "graphic novels",
            "manga", "webtoon",
            # people come back with a title as often as with the medium: "i finished watchmen
            # what next" was answered "That's great news - nice one. What's next?", and
            # "graphic novel for a beginner" with "Thanks for telling me".
            "watchmen", "maus", "persepolis", "saga", "one piece", "naruto", "dog man", "hilda",
            "fullmetal alchemist"),
           ("read", "reading", "recommend", "suggest", "what", "which", "good", "best", "start",
            "started", "something", "any", "want", "like", "into", "try", "first", "worth",
            "next", "finished", "beginner", "beginners",
            # the reader the pick is for: "recommend a comic for a kid" was "That's beyond what I
            # know well", and "best manga for a teen" was told to search
            "kid", "kids", "child", "children", "son", "daughter", "boy", "girl", "teen",
            "teenager", "year old", "years old", "grandchild", "niece", "nephew", "tween",
            "school", "for")),
          _comic_pick,
          bias=2,
          # A parent's question about a child's reading, and a question about whether a medium
          # counts, both have their own rows: this one only picks. "my son loves comics" is a
          # parent telling the bot about their child, not asking for a pick.
          guard=lambda understood: not _a_child_who_reads_already(understood),
          avoid=("only reads", "hates reading", "wont read", "won't read", "reluctant",
                 "refuses", "struggling",
                 "count as reading", "counts as reading", "count as a book", "count as books",
                 "still reading", "proper reading", "reading practice", "reading practise",
                 "film", "films", "movie", "movies", "series", "netflix", "iplayer", "stream",
                 "streaming", "tv",
                 # a making question is not a pick
                 "make a comic", "make comics", "draw a comic", "draw comics", "write a comic",
                 "comic strip", "comic strips", "drawing")),
    # The kind named is the question, so this row outranks the general book pick on its own
    # genres: "what should i read if i like sci fi" went to the general row and came back with
    # *The Thursday Murder Club*, which is a crime novel.
    entry("book-sci-fi", (("book", "read", "novel"), ("sci-fi", "sci fi", "scifi", "science fiction",
                                                     "space")),
          ("*Project Hail Mary* by Andy Weir is the safest recommendation: funny, fast and full of "
           "problem-solving. *The Left Hand of Darkness* by Ursula K. Le Guin if you want something "
           "deeper."), bias=2),
    entry("book-fantasy", (("book", "read", "novel"), ("fantasy", "magic", "dragons")),
          ("*The Hobbit* is the easiest way in, *Mistborn* by Brandon Sanderson if you want a big "
           "magic system to learn, and *Piranesi* by Susanna Clarke if you'd rather have something "
           "short and strange. All three are fine for adults and teenagers.")),

    # --- TV ---------------------------------------------------------------------
    entry("tv-line-of-duty", (("line of duty",), ("watch", "series", "next", "like", "liked")),
          ("*Happy Valley* is the closest in quality: British, tense, brilliantly acted, and less "
           "gory than Line of Duty. *Sherwood* and *Bodyguard* are the other two to try next."),
          bias=1),
    entry("tv-series", (("series", "boxset", "binge", "box set", "show", "shows"),
                            ("watch", "next", "recommend", "partner", "couple", "suggest",
                             "suggestion", "good", "any", "what", "binge", "bingeing",
                             "to binge",
                             # "i need a boxset for a rainy weekend" names the thing and what it
                             # is for, and never says watch: the occasion is the ask. Phrases, not
                             # bare "need"/"want", because "i want to show him" is not a boxset.
                             "rainy weekend", "rainy day", "wet afternoon", "stuck in",
                             "something to watch", "for the weekend", "long weekend",
                             "a night in")),
          ("*Happy Valley* for tense British crime, *The Bear* for short, intense episodes, or "
           "*Detectorists* if you want something gentle and funny. All three are easy to watch "
           "with a partner."),
          # "any good shows on at the theatre" is a night out, not a boxset.
          avoid=("theatre", "theater", "west end", "gig", "concert", "tickets", "on at",
                 "cinema", "in town")),
    entry("tv-background", (("tv", "series", "watch"), ("background", "relax", "easy", "nothing",
                                                        "tired")),
          ("*The Detectorists*, *Mortimer & Whitehouse: Gone Fishing* or *The Great British Bake "
           "Off*: all warm, low-stakes and easy to follow when you're tired. Nothing in them needs "
           "your full attention.")),

    # --- podcasts and audio ------------------------------------------------------
    entry("podcast-history", (("podcast",), ("history", "historical", "true", "stories", "commute")),
          ("*The Rest Is History* is the best all-round history podcast, with two hosts who are "
           "funny as well as accurate. For true stories, *Casefile* for crime and *This American "
           "Life* for real people's lives."), bias=1),
    entry("podcast-crime", (("podcast", "podcasts", "listen", "listening"),
                           ("true crime", "crime", "crimes", "murder", "murders", "serial killer",
                            "serial killers", "killing", "homicide", "unsolved", "casefile",
                            "like serial", "detective", "investigation")),
          PODCAST_CRIME,
          # A crime book, film, series or documentary is that medium's own question, and a murder
          # mystery night is a party rather than a listen.
          avoid=("book", "books", "novel", "novels", "read", "reading", "film", "films",
                 "movie", "movies", "series", "netflix", "tv", "documentary", "documentaries",
                 "drama", "mystery", "mystery night", "party", "how do i", "how to", "start a",
                 "record", "edit", "mic", "microphone", "upload", "spotify", "apple"),
          # "true" belongs to podcast-history and podcast-mood as well, and the subject the
          # person named is the one they want, so this row outranks both of them.
          bias=3),
    # A podcast asked for by its moment is still a podcast: "a podcast for a long drive" was
    # answered "For a long drive: *Rumours* by Fleetwood Mac and *Graceland* by Paul Simon",
    # because `listen-when` borrows the word "podcast" and its reply is albums. The shows win
    # here by naming the same moments, and with the same tie-break the music row has, so the
    # line about the drive reaches the shows and the line about the music is untouched.
    entry("podcast-commute", (("podcast", "podcasts"),
                              ("commute", "car", "drive", "short", "walk", "road trip",
                               "long drive", "journey", "car ride", "car journey", "flight",
                               "plane", "train", "long listen")),
          ("For a commute: *The Rest Is History* (30 to 50 minutes, always interesting), *The "
           "Diary of a CEO* for long interviews, or *Short History Of...* for 40-minute stories. "
           "All work with one earbud in."), bias=3),
    entry("podcast-funny", (("podcast", "podcasts", "listen", "listening"),
                           ("funny", "comedy", "laugh", "light-hearted", "lighthearted")),
          PODCAST_FUNNY,
          # Same the other way: a line about a book or something on screen is not a listen ask.
          avoid=("book", "books", "novel", "novels", "read", "reading", "film", "films",
                 "movie", "movies", "series", "netflix", "tv"),
          # "funny" is the word that picks this row out, so it outranks the general podcast
          # row ("recommend a funny podcast") and the moment-to-listen row ("something funny
          # to listen to on the drive"), which answers *when* rather than *what*.
          bias=2),
    entry("music-focus", (("music", "playlist"), ("focus", "study", "work", "concentrate",
                                                  "background")),
          ("Anything without words works best for focus: lo-fi hip hop, film scores by Hans Zimmer "
           "or Ólafur Arnalds, or ambient Brian Eno. Words compete with reading in a way that "
           "instrumentals don't.")),
    # "what should i listen to" names no album, band or genre, and it was a shrug on main: the
    # plain ask goes in the second half beside the music word.
    entry("music-recommend", (("music", "album", "band", "artist", "listen", "songs"),
                              ("recommend", "new", "something", "good", "albums", "records",
                               "what", "should i", "suggest", "any", "ideas")),
          ("Give *Rumours* by Fleetwood Mac a go if you've never sat with it, *Blonde* by Frank "
           "Ocean for something slower, or *The Köln Concert* by Keith Jarrett if you want piano "
           "you can work to. Tell me what you already like and I'll narrow it down."),
          # "listen" is in the key here, so "what podcasts should i listen to" was three albums.
          # A podcast is the podcast rows' question, whatever else the line says. So is the person
          # learning to play: "what should i practise first" in a conversation about a piano was
          # three albums to listen to, because the music in the conversation's topic carried the
          # key. Anything about playing, practising or learning an instrument is not a request for
          # something to listen to.
          # A word of the theory is a definition question too, and music-terms owns those: "what is
          # a chord in music" was answered with three albums, off "music" and "what".
          avoid=("podcast", "podcasts", "practise", "practice", "learn", "learning", "learnt",
                 "lesson", "lessons", "instrument", "rehearse", "rehearsing", "rehearsal",
                 "chord", "chords", "octave", "octaves", "time signature", "tempo", "bpm",
                 "harmony", "melody", "scale", "scales", "fingering", "what does", "mean",
                 "meaning", "definition", "key of",
                 # a song for one moment of a wedding is the listen-when row's, not three albums
                 "wedding", "marrying", "register", "ceremony", "aisle", "first dance",
                 "funeral", "memorial", "christening")),
    # "what should I listen to while I drive" is a request for sound, not a listening test:
    # the second half of the line is the moment, and there is no music word in it at all.
    entry("listen-when", (("listen", "listening", "music", "playlist", "album", "albums",
                           "podcast", "songs", "song", "hymn", "hymns", "tune", "tunes"),
                          ("drive", "driving", "car", "road trip", "cook", "cooking", "kitchen",
                           "running", "run", "gym", "workout", "jog", "walk",
                           # "how long before I could play a simple song" is not a moment to
                           # listen to something: the length has to belong to the trip.
                           "long drive", "long journey", "long flight", "long trip",
                           "long car ride", "long car journey",
                           # the trip to and from work names the moment without a drive in it
                           "commute", "commuting", "way to work", "walk to work",
                           "journey to work",
                           # an occasion is a moment too: the dinner party, the barbecue and
                           # the drinks before people arrive are when the music goes on
                           "dinner party", "party", "barbecue", "bbq", "guests", "guest",
                           "drinks", "wedding", "buffet", "birthday",
                           # a wedding is asked for by its moments, not by the word: "what
                           # music for a first dance" is the same request as "songs for a
                           # wedding", and the branch in _listen_when answers both.
                           "first dance", "reception", "bridal",
                           # a wet day is a moment to listen too, and it is asked as a statement
                           # as often as a question: "music for a rainy day", "rainy day music"
                           # and "a playlist for a rainy day" all reached nothing at all.
                           "rainy day", "rainy afternoon", "rainy sunday", "rainy weekend",
                           "rainy morning", "wet afternoon", "wet day", "wet weekend",
                           "snowy day", "stuck indoors",
                           # a funeral is a moment with music in it, and only a line with a
                           # music word in it reaches here: "how much is a funeral" has none,
                           # so the cost row keeps it.
                           "funeral", "memorial", "cremation", "burial", "wake", "send off",
                           "aisle",
                           # the signing of the register is a moment in the ceremony with music
                           # under it: "what song for the signing of the register" had no row
                           "register", "signing of the register", "sign the register",
                           "signing the register", "ceremony")),
          # bias 2 rather than 1: the poem rows added entries that use the word "song", and a
          # key word's weight falls as more entries in the domain use it, so "recommend a song
          # for a long drive" had started going to the "how long until I can play a song" row.
          # "podcast" is in this key because a drive is a moment to listen to something, and it
          # was answering "whats a good podcast for a long drive" with three albums. A podcast
          # is the podcast rows' question whatever the moment is - the same rule music-recommend
          # follows - and "something to listen to on the drive" still has no podcast word in it.
          _listen_when,
          avoid=("podcast", "podcasts"), bias=2),
    # "a good podcast about money" names the subject before it says the word podcast.
    entry("podcast-any", (("podcast", "podcasts"),
                          # "i'm in the mood for a podcast" is the same ask as "any good
                          # podcast", with the mood left out
                          WANT_ASKS + ("any", "good", "recommend", "suggest", "like", "liked",
                                       "what", "something", "listen", "new"
                                       # The moment a podcast is asked for carries the ask on its
                                       # own: "a podcast for a wet weekend" names the occasion and
                                       # no want word at all, and
                                       # with the wet-day words on listen-when (which holds
                                       # podcasts out) the line fell between the two rows and
                                       # reached the stock nod. The words stop at the weather on
                                       # purpose: "cooking", "the train", "driving", "for a" and
                                       # "to listen" are subjects and asks of their own, and with
                                       # them here "what podcast should i listen to while cooking"
                                       # came to these general picks instead of the food row's.
                                       "wet day", "wet days", "wet afternoon", "wet weekend",
                                       "snowy day", "stuck indoors")),
          ("Start with *The Rest Is History* (two funny historians), *Desert Island Discs* for "
           "people talking about their lives, or *Casefile* if you want a true crime story told "
           "straight. Tell me what you usually listen to and I'll aim closer."), bias=1,
          # A podcast somebody says they want to make is a wish to talk about, not a pick of
          # something to listen to. Only the wish stands down: "how do i start a podcast" and
          # "what microphone for a podcast" keep the picks, because the row that would answer a
          # how-to does not, and a clumsy pick beats "I'd rather not guess" - the review at
          # 3a881bb4 caught the wider list doing exactly that. "subscribe" is a picks ask
          # ("what podcasts should i subscribe to") and is not here either.
          avoid=("want to start a podcast", "want to make a podcast", "wanna start a podcast",
                 "thinking of starting a podcast", "thinking about starting a podcast",
                 "should i start a podcast", "start my own podcast", "make my own podcast")),
    # "whats a good podcast for learning spanish" was answered with the general picks - a history
    # show, Desert Island Discs and a true-crime one, none of which teaches a word. Learning a
    # language is its own request and has its own shows, and the ones below exist in several
    # languages, which is why the row answers a language it was not told about.
    entry("podcast-language", (("podcast", "podcasts", "listen", "listening"),
                               # "learn" belongs with the language, not with the podcast: "how do
                               # i learn spanish" is the study plan's question, and with "learn"
                               # in the first group this row took it.
                               ("spanish", "french", "german", "italian", "portuguese", "japanese",
                                "language", "languages", "another language", "learning a language",
                                "learn", "learning", "learn spanish", "learn french",
                                "my spanish", "my french", "my german", "my italian")),
          ("The Coffee Break series - Spanish, French, German, Italian - is the place to start: "
           "15 to 20 minutes a lesson, from hello upwards. Then the Duolingo Spanish Podcast for "
           "real stories told slowly in Spanish with English in between, and *InnerFrench* once "
           "you can follow a two-minute story in French. News in Slow Spanish and News in Slow "
           "French come next, and playing one episode twice beats five played once."),
          # a podcast ABOUT a country or its history is not a lesson in its language
          avoid=("history", "civil war", "war", "news", "commute", "car", "kids", "children",
                 "crime", "murder", "comedy", "football"),
          bias=2),
    entry("podcast-money", (("podcast", "podcasts"),
                            ("money", "finance", "financial", "business", "economics",
                             "investing", "saving", "boring", "bored")),
          ("*The Money To The Masses Podcast* is the plain-English one, *Meaningful Money* for "
           "pensions and savings, and *Moneybox* for news you can use. All three skip the jargon "
           "and none of them tries to sell you anything."), bias=1),

    # --- games ------------------------------------------------------------------
    # "long" is not one of the ask words: "how long is a game" asks for a length, and every
    # sport answers it with its own quarters or halves. The card still answers "rules", "easy"
    # and "learn" ("a board game for 4 adults who hate long rules" keeps the word long).
    entry("board-game-short-rules", (("board game", "game"), ("rules", "easy", "learn", "quick",
                                                              "adults", "simple")),
          ("*Codenames* (2 minutes to learn, works with any group), *Ticket to Ride* (simple, "
           "satisfying trains) and *Sushi Go!* (fast, small, cheap) are the three to start with. "
           "All are done in under an hour."), bias=1,
          # a game with a ball is a sport, and its length or its rules are the sport's answer:
          # "how long is a netball game" and "how long is a basketball game" were both sent to
          # the board games list on "game" and "long".
          avoid=("netball", "basketball", "football", "soccer", "rugby", "cricket", "hockey",
                 "tennis", "badminton", "volleyball", "rounders", "darts", "snooker", "golf",
                 "match", "matches", "sport", "sports", "league", "quarters", "innings",
                 "offside")),
    # "raining" and "rains" are spelled out: a card keyed "rainy" used to catch them through the
    # "-y" fold, and with the fold gone the row would have lost "what games can we play inside
    # when its raining".
    entry("game-kids", (("game",), ("kids", "children", "rainy", "rain", "raining", "rains",
                                    "family", "bored")),
          ("*Dobble*, *UNO* and *Snakes and Ladders* work for a range of ages, and *Catan Junior* "
           "if they are ready for a proper board game. For a rainy afternoon, a treasure hunt "
           "round the house costs nothing and takes the longest.")),
    entry("game-two-people", (("game", "games", "board game", "board games",
                               # "what can two people play with cards" named no board and no kit,
                               # so the row never saw it and the line was a search hedge
                               "card game", "card games", "cards", "with cards",
                               "something to play", "a game for",
                               # "what can me and my partner play" names no game at all, so
                               # the asking verb is the only word there is to key on, and the
                               # second group still has to name the pair
                               "play", "to play"),
                              ("two", "couple", "partner", "2", "two of us", "both of us",
                               "two people", "2 people", "for two", "two players",
                               "two player", "2 players", "2 player", "the two of us",
                               # "what can me and my partner play" is the same table of two,
                               # said as the pair rather than as the number
                               "me and my partner", "with my partner", "me and my wife",
                               "me and my husband", "me and my friend")),
          ("*Patchwork*, *Jaipur* and *Hive* are the three best two-player games that are quick to "
           "learn. For a card game with no kit, gin rummy works just fine.")),
    # "board game ideas", "a good board game for tonight" and "what board game should i get" all
    # reached nothing at all: every game row above needs somebody named - children, a partner, a
    # group - and the person who has not worked out who is coming yet names nobody. The general
    # card answers the ask and asks the one thing that narrows it, which is how many are playing.
    entry("game-pick", (("board game", "board games", "boardgame", "boardgames",
                         "family game", "family games",
                         # A line that asks for something to play names no game at all:
                         # "something to play after dinner" was answered with the quick-dinner
                         # list, because "after dinner" is a meal and nothing else was named.
                         "something to play", "anything to play", "a game to play",
                         "games to play", "what to play", "what can we play",
                         "what should we play", "what shall we play"),
                        PICK_ASK + ("what", "which", "best", "should i get", "should we get",
                                    "to play", "to buy", "for christmas", "for a present",
                                    "for a gift", "worth")),
          ("*Codenames* is the safest buy: two teams, one grid of words, five minutes to learn, "
           "and it works from four players up. *Ticket to Ride* if you want a proper board with "
           "a bit of thinking in it, and *Just One* if the table is mixed ages and nobody wants "
           "a rulebook. Tell me how many of you there are and how long you have, and I will pick "
           "one."),
          bias=1,
          # the rows above say more once the table is known, and a game with a ball is a sport
          avoid=("kids", "children", "child", "toddler", "rainy", "bored",
                 "two", "couple", "partner", "for 2", "2 player", "two player",
                 "group", "friends", "mates", "party", "everyone", "people",
                 "rules", "easy", "learn", "quick", "simple", "adults",
                 "netball", "basketball", "football", "soccer", "rugby", "cricket",
                 "hockey", "tennis", "badminton", "volleyball", "rounders", "darts",
                 "snooker", "golf", "match", "matches", "sport", "sports", "league")),
    entry("game-kids-rainy", (("rainy day", "bored", "all day", "keep busy", "entertain",
                               "afternoon", "busy",
                               # the same ask with the activity left unsaid: "what can i do with
                               # a 4 year old" was a search hedge, and the age alone was already
                               # enough for this card's second group.
                               "what can i do with", "what do i do with", "what to do with",
                               "things to do with"),
                              # "at home" alone is not enough: "how do i keep busy at home" is
                              # a grown-up with a free afternoon, not this answer.
                              ("kids", "children", "afternoon", "toddler", "toddlers",
                               # a baby cannot hunt for treasure, so no "baby" here
                               "preschooler", "4 year old", "3 year old", "5 year old",
                               "2 year old", "6 year old", "him", "her", "them")),
          ("A treasure hunt round the house costs nothing and takes longest: ten clues written on "
           "cards, ending in a small prize. For a quieter hour, *Dobble* or a box of felt tips and "
           "a roll of wallpaper."),
          # "what do i do with him all day" and "what can i do with a 4 year old" are the same
          # ask as "a rainy day with the kids": one child named by age or by pronoun is enough.
          avoid=("game", "games", "board", "phone", "screen", "ipad", "tablet", "tv",
                 # "my toddler sleeps all day" was a treasure hunt: a child's sleep is the sleep
                 # rows' question, and "all day" in it is the length of a nap, not a free afternoon.
                 "sleep", "sleeps", "sleeping", "slept", "sleepy", "nap", "naps", "napping",
                 "bedtime", "bed time", "night waking", "wakes up", "waking",
                 # A treasure hunt round the house is no use in a moving car, and "how do i keep
                 # kids entertained on a long drive" was getting it. The phrases say journey
                 # rather than naming the vehicle: a bare "car" stood this card down for "how do
                 # i keep kids busy in the car", which is a car journey and is answered by
                 # travel's car-journey-kids, not by the car-budget row that took it next.
                 "drive", "driving", "long drive", "car journey", "long journey", "road trip",
                 "motorway", "in the car", "back seat", "backseat", "plane journey",
                 "long flight", "on a plane", "train journey", "long train", "on the ferry",
                 # The vehicle on its own is a journey too: "how do i keep kids busy on the
                 # train" and "...children busy on a ferry" kept the treasure hunt round the
                 # house, because only the phrase forms were here and travel's bare train and
                 # ferry lost on score to this card.
                 "train", "on a train", "by train", "ferry", "on a ferry", "by ferry",
                 "flight", "on the plane")),

    # "party games for a 6 year old" is not the group-game list: the games for a five-year-old's
    # party are the ones with running and a prize, and Codenames is no use to them. It is not the
    # buffet either, which the words party, kids and games used to reach (cooking.py's party-food
    # stands aside for them now). The age or the child is what makes it this question, and no key
    # can demand a word, so the line is read here before the answer is given.
    # "party ideas for a 4 year old" and "how do i keep kids busy at a party" are the same
    # question as "party games for kids": a plan for a child's party, and keeping them busy is
    # what the games are for. "ideas" is in the key rather than the food rows being narrowed,
    # and the food words in the avoid list keep "party food ideas for kids" on the buffet.
    entry("party-games-kids", (("party", "birthday"),
                               ("game", "games", "play", "playing", "activities", "activity",
                                "entertain", "entertainment", "fun", "idea", "ideas", "busy",
                                "occupy", "distract", "keep them happy", "keep kids happy")),
          _party_games_for_kids, bias=2,
          # "i missed my daughters school play" names a child and a play, and it is the speaker's
          # own deed: the games for a party that has not happened are no answer to it, and the
          # repair in bot/compose/repair.py is (owns_the_deed).
          guard=lambda reading: not owns_the_deed(reading),
          avoid=("food", "foods", "snack", "snacks", "buffet", "menu", "eat", "eating", "cook",
                 "cooking", "adults", "grown ups", "adult", "teenagers", "teenager", "teens",
                 "teen", "friends", "mates", "everyone", "work party", "office",
                 # "birthday cake ideas for a 5 year old" is the cake, not the games: an idea for
                 # a child's birthday can be either, and the cake words are what tells them apart
                 "cake", "cakes", "bake", "baking", "icing", "frosting", "decorate", "decorating",
                 "candles", "cupcakes", "themed cake", "party bags", "party bag", "favours",
                 "goody bag", "present", "presents", "gift", "gifts",
                 # "what music should i play at a dinner party" is the music, not the games: a
                 # line that names a medium is asking what to put on, and the games row only
                 # shares the word party with it
                 "music", "playlist", "songs", "spotify", "tunes", "album", "dj")),
    # An audiobook is not a podcast and not a book: the narrator and the length are the whole
    # answer, and nothing on main had them. "an audiobook for a long drive", "audiobook for the
    # car" and "what audiobook should i get" were a shrug each.
    entry("audiobook", (("audiobook", "audiobooks", "audio book", "audio books",
                         "listen to a book", "listening to a book", "book on tape"),
                        ("drive", "driving", "car", "commute", "commuting", "journey",
                         "long drive", "flight", "plane", "holiday", "walk", "walking",
                         "what", "which", "any", "good", "best", "recommend", "suggest",
                         "something", "should i", "for a long", "to listen")),
          "For a long drive, a narrator who can hold a voice for hours beats a famous book: "
          "*The Thursday Murder Club* (Lesley Manville, about 7 hours) is easy to follow with "
          "traffic about; *Project Hail Mary* (Ray Porter, about 16 hours) is the one people "
          "finish and start again; *Circe* (Perdita Weeks, about 13 hours) if they want "
          "something with a story to it. Pick something 8 hours or longer for a drive of that "
          "length, and listen to ten minutes of the sample before you commit.",
          # a podcast is its own answer, and a paper book for the trip is the holiday reading
          avoid=("podcast", "podcasts", "radio", "spotify", "playlist", "music", "song",
                 "songs", "album", "kindle", "library", "borrow", "free", "cheap",
                 "for a child", "for my child", "kids", "children", "bedtime")),

    # "a book for a 7 year old" was answered by the bot counting the child back at them ("One
    # kid, seven"), and "what book for my 6 year old" got the football yellow-card rule, because
    # "book" next to a number reads as a booking. The reader's age is the whole question here.
    entry("book-for-a-child", (("book", "books", "novel", "read", "reading", "story",
                                "stories", "chapter book"),
                               ("year old", "year-old", "years old", "yr old",
                                "6 year old", "seven year old", "7 year old",
                                "8 year old", "eight year old", "9 year old",
                                "nine year old", "10 year old", "ten year old",
                                "11 year old", "12 year old", "eleven year old",
                                "twelve year old", "for my son", "for my daughter",
                                "for my grandson", "for my granddaughter", "for my niece",
                                "for my nephew",
                                # the teenager asked for by age, or just as a teenager: "books
                                # for a 14 year old" and "novel for a 15 year old boy" reached
                                # the bot counting the child back, and "books for teenagers" got
                                # "I'm listening"
                                "13 year old", "thirteen year old", "14 year old",
                                "fourteen year old", "15 year old", "fifteen year old",
                                "16 year old", "sixteen year old", "17 year old",
                                "seventeen year old", "18 year old", "eighteen year old",
                                "for a teenager", "for my teenager", "for a teen",
                                "teenager", "teenagers", "teens", "teen")),
          _book_for_the_age,
          # a book for the grown-up, a parent's own reading and a bed-time routine are other rows.
          # The ages are no longer fenced off: a teenager's question was reaching an echo of the
          # child's age instead, which is the one thing worse than handing them The Worst Witch.
          avoid=("for me", "for myself", "my own reading", "bedtime story", "bedtime routine",
                 "read to sleep", "bath", "potty", "toilet training", "school report",
                 "reading age", "struggling", "dyslexia", "reluctant reader",
                 # a line that asks for a story to be written is not a book to read: "can you
                 # write a story about a dinosaur for my son" wanted the story, and the reading
                 # row took it on "story" and "for my son"
                 "write a story", "write me a story", "write us a story", "make up a story",
                 "tell me a story", "tell us a story", "write a poem", "write me a poem",
                 # and the same ask with the subject after it: "give me a story for my grandson
                 # about a tractor" and "write me a short story about a robot for my son" both
                 # reached the reading ladder on "story" and "for my son"/"for my grandson"
                 "give me a story", "give us a story", "a story about", "stories about",
                 "short story", "story for my")),

    entry("game-group", (("game", "games", "board game", "board games", "play", "playing"),
                         ("friends", "group", "party", "everyone", "mates", "people",
                          "mixed ages",
                          # a table counted rather than named: "a game for the four of us",
                          # "a board game night for four", "what can four of us play tonight"
                          # reached nothing at all, and one of them was answered with the
                          # bedtime-phone advice because "night" and "phone" were the only
                          # words left. The count is the table.
                          "three", "four", "five", "six", "seven", "eight",
                          "3", "4", "5", "6", "7", "8", "of us", "our lot", "after dinner")),
          ("*Codenames* is the one to bring to a group: two teams, one word grid, and it works "
           "from four players up. *Wavelength* and *Just One* are the same idea for people who "
           "do not like arguing, and for a big party *Werewolf* or *Mafia* needs nothing but a "
           "deck of cards."),
          # two players and children have their own answers, which say more, and "my friends are
          # coming over" is news that needs no game list.
          #
          # The ask gate used to need a question word, so the way people actually ask for one -
          # naming the occasion and no question at all - was ignored: "party games" got the
          # condolence opener, "board games for a group" got "I'm listening", and "games for a
          # party with friends" was noted back at them. The occasion is the ask.
          ask=("what", "which", "any", "best", "good", "suggest", "recommend",
               "game for", "games for", "board game for", "board games for",
               "party game", "party games", "game night", "games night", "for a group",
               "for a party", "for friends", "to play with"),
          avoid=("two", "couple", "partner", "kids", "children")),
    # "what is a good chess opening" was a hedge: chess-improve wanted a word about getting
    # better, and the opening is a separate question with its own answer.
    entry("chess-opening",
          (("chess",), ("opening", "openings", "first move", "opening moves", "best first move",
                        "e4", "d4", "start as white", "start as black")),
          "For white, e4 or d4 - both free your pieces and give you a plan - and for black answer "
          "e4 with e5 or the Sicilian, and d4 with d5 or the King's Indian. Learn one opening "
          "each side by its ideas rather than its moves: what the pawns are doing, where the "
          "pieces belong, and which piece you are happy to trade. Ten moves you understand beat "
          "forty you cannot remember.",
          ask=("what", "which", "any", "best", "good", "should", "suggest"),
          avoid=("book", "books", "read", "reading", "course", "set", "board", "computer"),
          bias=1),
    # The words of the game itself: a person playing a first game meets all four of them in the
    # first hour, and "what is checkmate" was the search hedge.
    entry("chess-checkmate",
          (("checkmate", "check mate", "in check", "out of check", "being in check",
            "check in chess", "a check in chess", "checks the king", "check the king"),
           ("what", "whats", "mean", "means", "explain", "difference", "different", "vs",
            "versus", "is it", "how do i", "avoid", "get out of", "stuck in", "in check")),
          "Checkmate is a king in check with no legal way out: no square to move to, nothing to "
          "block with, and nothing that can take the piece giving check. Being in check is not "
           "checkmate - you can move the king, block the line or take the attacker, and only if "
           "none of those work is the game over. Stalemate is the other ending, and it is a draw: "
           "the king is not in check but has no legal move, which is why you never chase a lone "
           "king into the corner without giving it a square.",
          ask=("what", "whats", "how", "can", "is", "difference", "explain"),
          avoid=("book", "books", "read", "reading", "opening", "openings", "grandmaster",
                 "tournament", "club", "clock", "board game"),
          bias=1),
    entry("chess-stalemate",
          (("stalemate",),
           ("what", "whats", "mean", "means", "explain", "difference", "different", "vs",
            "versus", "is it", "draw", "how do i")),
          "Stalemate is a draw: the side to move is not in check but has no legal move at all, and "
           "the game ends level even if they are a queen down. It usually happens with a lone king "
           "in front of the enemy king with no square to go to. If you are winning, leave the "
           "other king a square or move a pawn, and if you are losing, look for it on purpose - it "
           "is half a point from nowhere.",
          ask=("what", "whats", "how", "can", "is", "explain"),
          avoid=("book", "books", "read", "reading", "opening", "openings", "talks", "negotiation"),
          bias=1),
    entry("chess-castling",
          (("castle", "castles", "castling", "castled"),
           ("what", "whats", "how", "when", "can i", "do i", "should i", "work", "works",
            "why", "move", "rook", "king", "long", "short", "queenside", "kingside")),
          "Castling moves the king two squares towards a rook and puts that rook on the other side "
           "of it, and it is the one move where two pieces go at once. It takes one move, it is "
           "only legal if neither the king nor that rook has moved, nothing is between them, the "
           "king is not in check, and the king does not pass through or land on a square that is "
           "attacked. Do it early, usually within the first ten moves: it puts the king behind "
           "pawns and brings the rook into the game.",
          ask=("what", "whats", "how", "when", "can", "do", "should", "why", "is"),
          avoid=("sand", "beach", "scotland", "wales", "wedding", "visit", "hotel", "ruins",
                 "book", "books", "read", "reading"),
          guard=_a_chess_line,
          bias=1),
    entry("chess-pawn-moves",
          (("pawn", "pawns", "en passant", "enpassant", "passant"),
           ("move", "moves", "backwards", "backward", "forward", "two squares", "first move",
            "how", "can", "why", "work", "works", "explain", "mean", "means", "promote",
            "promotion", "take", "what", "whats", "what is", "is it", "a pawn")),
          "A pawn moves one square forward and takes one square diagonally forward, so a pawn never "
           "moves or captures backwards. From its starting square only it may go two squares, and "
           "that is what lets the en passant rule exist: if a pawn goes two squares and lands "
           "beside an enemy pawn, that pawn may take it as if it had moved one, on that move only. "
           "Getting to the far end promotes it to a queen, rook, bishop or knight, and a queen is "
           "almost always right.",
          ask=("what", "whats", "how", "when", "can", "do", "why", "is"),
          avoid=("book", "books", "read", "reading", "mortgage", "loan", "car", "camera",
                 "pawn shop", "pawnbroker", "pawnbrokers", "uncle"),
          bias=1),
    entry("chess-improve", (("chess",),
                            ("better", "improve", "learn", "start", "tips", "practise", "practice",
                             "beginner", "good at", "get into", "getting into", "begin")),
          ("Two things move the needle: fifteen minutes of tactical puzzles a day on Lichess or "
           "Chess.com, and playing long games rather than blitz, then looking at where you lost. "
           "Learn the ideas behind one opening for white and one for black instead of memorising "
           "moves, and always ask what your opponent's last move was threatening."),
          ask=("how", "what", "any", "tips", "should", "best", "can")),
    entry("learn-guitar", (("guitar",),
                           ("learn", "start", "beginner", "how long", "take", "teach",
                            "learn to play", "hard")),
          ("Ten to fifteen minutes a day beats one long session a week: learn the four chords G, "
           "C, D and Em first, then play songs that use them, since songs keep you going where "
           "scales do not. Most people can strum through a simple song in two or three months "
           "that way; sore fingertips for the first fortnight are normal."),
          # a question, not an introduction ("hi, I'm Tom and I'm trying to learn the guitar"),
          # and buying one is a different question.
          ask=("how", "what", "any", "should", "best", "can", "tips"),
          avoid=("buy", "buying", "bought", "price", "cost", "which one", "second hand",
                 "second-hand", "restring", "string", "tune", "amp", "amplifier")),

    # --- where to start with music, cards, drawing and an instrument ------------
    # A genre is the whole subject: "how do i get into jazz" names no album, band or song, so
    # the music rows could not reach it. The ask gate is what keeps a remark ("i like jazz") and
    # a definition ("what is jazz") away from a row that answers with somewhere to start.
    # bias=2, not 1, for one reason: `_rank` gives a point for every key word that no other
    # entry uses, and a genre name that is also an everyday noun is a word another row likes to
    # key. When the show table took "house" for a property show, the music row lost that point
    # and a line it should answer went to the listen-better card instead: "how do i start
    # listening to house" was answered "stop preparing your reply while they are still talking",
    # from a row that is about a conversation and not about music (#6957 did that, and
    # tests/test_a_house_is_not_a_kind_of_music.py has been red on main since). The genre word
    # plus the ask word is the whole question here, so this row reaches ahead of a row that
    # matched the same line on one of the ordinary senses of the word.
    entry("music-genre-start", (tuple(GENRE_START), MUSIC_START_ASKS),
          _genre_start, bias=2,
          # a gig, a ticket and a present are other questions, and a film about music is not
          # this one either
          avoid=("gig", "gigs", "ticket", "tickets", "concert", "present", "birthday",
                 "film", "films", "documentary", "book", "books", "podcast", "playlist",
                 # Half the genre names are ordinary words too, and the key only needs the genre
                 # plus an ask word, so "how do i start decorating my house" won this row and got
                 # Daft Punk. Each line below is a word that means the genre only in a music
                 # sentence, so the row stands down and the other domain keeps its answer: the
                 # garden, the walk, the dance class, the wall of the house.
                 "country walk", "country walks", "country park", "country garden",
                 "country house", "the country", "countryside", "village", "walk in the country",
                 "my house", "our house", "your house", "decorate", "decorating",
                 "decoration", "decorations", "renovate", "renovating", "renovation",
                 "house prices", "house price", "buy a house", "buying a house", "sell my house",
                 # ... and a house being bought is the row above's own neighbours: the money
                 # words were missing, so "i want to save for a house deposit, where do i
                 # start" read "house" + "where do i start" and got a genre to begin with.
                 "deposit", "house deposit", "mortgage", "remortgage", "save up", "saving up",
                 "savings", "first home", "first house", "first flat", "stamp duty",
                 "buying a flat", "buy a flat", "getting on the ladder", "housing ladder",
                 "selling my house", "moving house", "house plant", "house plants",
                 "housework", "rent", "landlord",
                 "metal band", "metal detector", "metal detecting", "detector", "detecting",
                 "scrap metal", "metal gate", "metal roof",
                 "metal work", "metalwork", "welding", "welder",
                 "folk dance", "folk dancing", "folk tale", "folk tales", "folk story",
                 "folk stories", "folk medicine", "folk remedy", "folk art",
                 "soul food", "soul mate", "soul mates", "gospel truth", "baby blues",
                 "winter blues", "the blues after", "rap sheet", "take the rap", "indie shop",
                 "indie store", "punk kid", "punk kids",
                 # a night out is not an album: "how do i start a house music night"
                 "music night", "club night", "promoter", "night out", "nightclub")),
    # "how do you play snap" and "what are the rules of uno" are the same ask, and the answer
    # is the deal, the turn and the win. The named game is the key, so no card word is needed.
    entry("card-game-rules", (tuple(CARD_GAMES) + ("patience", "pontoon", "twenty one"),
                              CARD_ASKS),
          _card_game, bias=1,
          # a board game, a party game and a game with the kids are other rows, and a gambling
          # question about blackjack is not the rules of it
          avoid=("board game", "board games", "kids", "children", "toddler", "party", "drinking",
                 "bet", "betting", "casino", "real money", "wager", "odds",
                 # the money side of it is a gambling question, and a shrug is better than the
                 # rules of the game handed over as if that were the answer
                 "for money", "gambling", "poker", "winnings")),
    # "how do i learn to draw" was a shrug, and it is a practice question like handwriting:
    # something to draw, for ten minutes, every day.
    entry("learn-to-draw", (("draw", "drawing", "sketch", "sketching", "sketches", "doodle",
                             "doodling", "pencil drawing", "line drawing"),
                            # not "good at": "good" is a key word of the boxset row, and a
                            # second entry using it took the rarity point that row was winning on,
                            # which turned "any good shows to watch" into the film list.
                            ("learn", "start", "starting", "beginner", "better", "improve",
                             "practice", "practise", "talent", "tips", "teach", "how do i",
                             # "i cant draw" is the same ask as "how do i learn to draw"
                             "cant", "can't", "cannot", "never learnt", "never learned")
                            # a child's drawing and a picture of the family dog are other
                            # questions, and this advice is for the person holding the pencil
                            ),
          ("Draw what is in front of you, not from memory: a mug, your own hand, the chair "
           "opposite. Ten minutes a day beats a long session at the weekend, one object a day for a "
           "fortnight, and use a soft pencil (2B) on cheap paper so you are not afraid of it. Copy "
           "one drawing you admire every week and do not rub anything out - the wrong line next to "
           "the right one is how you learn to see."),
          # the draw of a curtain, a bath and a pension are not this, and a game that ends in a
          # draw is not either
          avoid=("curtain", "curtains", "bath", "baths", "bathroom", "pension", "money out",
                 "cash", "card", "tie", "match", "game", "lottery", "raffle", "winner",
                 # a child's drawing, a school project and a picture of someone are other
                 # questions, and this advice is for the person holding the pencil
                 "kids", "kid", "children", "child", "toddler", "my son", "my daughter",
                 "my boy", "my girl", "school", "nursery", "colouring", "coloring",
                 "draw a picture of my", "draw up", "draw out", "draw in")),
    # The first step into a named activity is not "pick a hobby": the person has chosen already
    # and wants to know what to do on Saturday. Two words are needed - the activity and a word
    # for starting - so a line about liking it, or a present for someone who does it, stays out.
    entry("activity-start", (tuple(ACTIVITY_START) + tuple(ACTIVITY_OTHER_NAMES), ACTIVITY_ASKS),
          _activity_start, bias=1,
          # buying a gift, watching a programme about it and a child's class are other questions,
          # and a recipe or a sourdough starter is the cooking domain's answer, which says more
          avoid=("present", "birthday", "christmas", "gift", "documentary", "film", "programme",
                 "my son", "my daughter", "my kid", "my child", "kids", "children", "school",
                 # a line naming bread or a cake is the cooking domain's, and this module's
                 # answer gets vetoed as off-topic there, which left the line with a shrug
                 "recipe", "flour", "yeast", "sourdough", "starter", "oven", "grams", "500g",
                 "bread", "loaf", "dough", "cake", "cakes", "pastry", "biscuit", "roast",
                 # starting a choir or a club is setting something up, not learning it
                 "at work", "set up", "start a choir", "start a club", "start a group",
                 "start a class",
                 # mending is a how-to, not a hobby to learn: "how do i sew a button on" was
                 # answered with the first step into sewing while the mending row sat unused
                 "button", "buttons", "hem", "hems", "patch", "patches", "darn", "zip", "zips",
                 "seam", "seams", "unpick", "mend", "alteration", "alterations",
                 # a wall, a door, a room and a radiator are things to paint, not hobbies to
                 # learn: "how do i paint a door" was the learn-something-new answer while
                 # paint-door and paint-room sat unused
                 "a door", "the door", "my door", "a wall", "the wall", "the walls", "my walls",
                 "a room", "the room", "skirting", "ceiling", "radiator", "fence",
                 # a coat on a nail is a manicure, not the hobby: "how do i paint my nails" and
                 # "how do i paint my toenails" were taught to start with acrylics and a mug,
                 # because "paint" is the painting activity and "nails" said nothing to this row
                 "nails", "nail", "fingernails", "fingernail", "toenails", "toenail",
                 "manicure", "pedicure", "nail polish", "nail varnish",
                 # paint that is coming off a wall is a decorating job and not a hobby to take
                 # up: "how do i stop the paint flaking" was this row's answer, because
                 # "painting" is one of the activities and "how do i" reads as starting it,
                 # while the flaking-paint row sat unused with the reason and the fix in it.
                 "the paint", "paint is", "paint on the", "flaking", "flaky", "flake", "peeling",
                 "peels", "bubbling", "blistering", "chipping", "coming off", "coming away",
                 # "how do i use a sewing machine" is threading and tension, not a first step
                 # into a hobby: a line about using the thing, or the tool itself, is the
                 # instruction question and home's craft row answers it ("how do i use circular
                 # needles" is the knitting answer, "how do i thread a sewing machine" the order).
                 "use", "using", "thread", "threading", "tension",
                 # a climbing rose is a plant, not a wall to start on: "how do i prune a
                 # climbing rose" was told to hire shoes and try bouldering, while the rose
                 # entry that knows the answer sat unused one word away
                 "rose", "roses", "climbing rose", "climber", "clematis", "wisteria", "vine",
                 "ivy", "shrub", "shrubs", "prune", "pruning", "plant", "plants", "garden",
                 "seedling", "seedlings", "cutting", "cuttings", "greenhouse", "allotment",
                 # nails are a technique of their own and this row took them once painting was
                 # an activity: "how do i paint my nails" was the first-step-into-painting card
                 "nails", "nail", "fingernails", "toenails", "manicure", "pedicure",
                 "nail polish", "nail varnish",
                 # "learn to fish" is a hobby and a fish tank is not: "how do i clean a fish
                 # tank" was this row's, because "fish" is one of the activities and "how do i
                 # clean" reads as starting it.
                 "fish tank", "fish tanks", "aquarium", "tank", "tanks", "goldfish", "pond",
                 # and a fish that is dinner is the kitchen's, not a hobby: "how do i get rid of
                 # the smell of fish in the kitchen" was this row's answer, because "fish" is an
                 # activity and "how do i" reads as starting it, while the fish-smell card sat
                 # unused with the pan of lemon and vinegar in it.
                 "smell", "smells", "smelling", "smelly", "stinks", "stink", "get rid",
                 "get rid of", "fishy", "tastes", "taste", "cooked", "fillet", "batter",
                 "chips", "monger", "fish market", "freezer", "kitchen smells",
                 "house smells", "after cooking",
                 # the room an activity leaves behind is a job, not the first step into the
                 # activity: "how do i clean up after baking" and "how do i bake without making
                 # a mess" were told how to weigh the flour, because "baking" is an activity and
                 # "how do i" reads as starting it. A cleaning verb with the activity's mess is
                 # the kitchen's answer, and the mess-free-bakes row has the other one.
                 "clean up", "cleaning up", "cleaned up", "clear up", "clearing up", "tidy up",
                 "tidying up", "washing up", "wash up", "the wash up", "make a mess",
                 "making a mess", "made a mess", "the mess", "a mess", "messy", "covered in",
                 "all over the", "after baking", "after making", "clean the kitchen",
                 # and a fish to cook is the cooking domain's: "how do i cook fish" was the first
                 # step into angling, rod licence and day ticket, and "how do i know when fish is
                 # done" with it. The words are the cooking ones beside the fish, not "cooking"
                 # alone, because "how do i get into cooking" is a real activity ask.
                 "cook fish", "cooks fish", "cooking fish", "cooked fish", "cook a fish",
                 "cook the fish", "cook my fish", "fry fish", "frying fish", "bake fish",
                 "baked fish", "grill fish", "grilled fish", "fish is done", "fish is cooked",
                 "fish for dinner", "fish for tea", "fish pie", "fishcakes", "fish cakes")),
    # "how do i play chess" and "what are the rules of chess" had no answer at all, because the
    # improving row keys on getting better. This is the game in one paragraph.
    entry("chess-play", (("chess",),
                         ("how do i play", "how to play", "how do you play", "rules", "how does",
                          "the moves", "set up", "move the pieces", "win")),
          ("The aim is to trap the other king so it cannot move and cannot escape being taken - "
           "that is checkmate, and you do not capture the king. Pawns go forward one square (two on "
           "their first move) and take diagonally; knights jump in an L; bishops go diagonally any "
           "distance; rooks in straight lines; the queen both ways; the king one square. Set up with "
           "a white square at the bottom right and the queen on her own colour, then play ten games "
           "on Lichess against people at your level - the moves stick after a few losses."),
          bias=1,
          # getting better at it, a set to buy and a child's club are other rows
          avoid=("better", "improve", "good at", "tips", "practise", "practice", "buy",
                 "buying", "set", "club", "kids", "children", "school")),
    # A tuning question names the instrument, so the entry keys on the instrument plus a word for
    # pitch; the string order is the part people actually need.
    entry("instrument-in-tune", (("guitar", "ukulele", "violin", "fiddle", "bass", "cello",
                                  "banjo", "mandolin", "piano", "keyboard"),
                                 TUNE_ASKS),
          _in_tune, bias=1,
          # a car needs a tune-up, a radio needs a station, and tuning a TV is not this
          avoid=("car", "engine", "radio", "station", "tv", "television", "freeview", "aerial",
                 "sat nav", "satnav", "channel")),
    # "it will not stay in tune" is a fault, not the lesson in tuning: new strings stretch, a
    # nut pinches, and a peg slips. It wins over the tuning row because it names the slipping.
    entry("instrument-slips", (("guitar", "ukulele", "violin", "fiddle", "bass", "banjo",
                                "mandolin", "cello"),
                               ("wont stay in tune", "won't stay in tune", "wont hold tune",
                                "keeps going out of tune", "goes out of tune", "out of tune all",
                                "slips", "slipping", "wont tune", "will not stay in tune",
                                "doesnt stay in tune", "doesn't stay in tune")),
          ("Nine times in ten it is the strings: new ones stretch for a week, so tune up, bend "
           "every string a little, and tune again - three or four times the first evening. Old "
           "strings go dead and stop holding pitch, so if they are more than a few months old, "
           "change them. If one string pings as it slips it is catching in the nut, and a pencil "
           "lead scribbled in the slot fixes that tonight. Still slipping with new strings is a "
           "worn peg or a tuner screw, which is a shop job."),
          bias=3,
          avoid=("car", "engine", "radio", "station", "tv", "sat nav")),

    # The buzz is a fault, not a lesson, and the answer is the order of the cheap causes.
    entry("guitar-buzz", (("guitar", "bass", "ukulele", "banjo", "mandolin", "violin"),
                          BUZZ_ASKS),
          _buzz, bias=2,
          avoid=("amp", "amplifier", "speaker", "headphones", "phone", "doorbell", "buzzer",
                 "intercom", "bee", "bees", "wasp")),

    # --- sport and learning ---


    # --- who made it -------------------------------------------------------------
    entry("who-made-it", (("who", "name", "band"), WHO_MAKERS),
          who_made,
          # "who wrote to the council" is a letter, "who wrote that" is a quote, and "who
          # painted the fence" is a job: the table has to name the work for this to fire.
          avoid=("council", "letter", "email", "wrote to", "that", "this", "quote", "fence",
                 "wall", "door", "house", "room", "shed", "whose", "cake", "dinner", "mess")),

    # --- quick creative asks ----------------------------------------------------
    # The forms are asked for by name, so the row keys on the name of the form and on the words
    # that make it a request rather than a remark ("I like haikus" is not one).
    # "What is a haiku" is a question about the form, so the answer is the rule plus one, and it
    # has to win over the row that writes one, which has no subject to write about.
    entry("poetry-kids", (("poetry", "poems", "poem", "rhymes", "rhyming", "nursery rhymes"),
                          ("kids", "children", "child", "toddler", "toddlers", "baby", "babies",
                           "good for", "worth it", "benefit", "help them", "teach")),
          ("Yes, and it is the sound that does the work: rhymes teach a child that words are made "
           "of parts, which is the same skill reading needs. Read one aloud and let them finish "
           "the rhymes, keep it to a couple of minutes, and do not ask them to explain it. Silly "
           "wins - a poem they can shout is one they will remember."), bias=1),
    entry("poem-what", (("poem", "poems", "poetry", "verse"), ("what", "is", "explain", "mean",
                                                             "definition", "form", "rule")),
          ("A poem leans on sound as well as meaning: rhythm, rhyme if you want it, and the line "
           "breaks doing some of the work. No rules you have to follow - the two forms with rules "
           "are the haiku (three lines, 5-7-5) and the limerick (five lines, aabba). Ask me for "
           "either and I'll write one."), bias=2,
          # "I don't like poetry, what should I read" is a reading question with a "what" in it.
          avoid=("read", "reading", "recommend", "book", "books", "novel", "novels",
                 "good for", "worth it", "any good", "benefit", "benefits", "should i")),
    entry("haiku-what", (("haiku", "haikus"), ("what", "is", "explain", "mean", "definition",
                                              "form", "rule", "structure")),
          ("A haiku is three lines counted in sounds: five, then seven, then five, usually about "
           "one moment rather than a story:\nRain on the window,\na hundred small taps, all "
           "night,\nand the garden drinks."), bias=2,
          avoid=("read", "reading", "book", "books")),
    entry("limerick-what", (("limerick", "limericks"), ("what", "is", "explain", "mean",
                                                       "definition", "form", "rule",
                                                       "structure")),
          ("A limerick is five lines that rhyme aabba, with the two in the middle short: it is a "
           "joke in verse.\nThere once was a cloud over Crewe\nthat had far too much rain to "
           "do.\nIt rained on the park\nfrom morning till dark,\nand then, just for fun, rained "
           "on you."), bias=2,
          avoid=("read", "reading", "book", "books")),
    # A bare "a" was one of the request words these two keyed on, and "what is a haiku" holds
    # one, so a question about the form scored as a request for one. Without it they can outrank
    # the subject rows they were losing to: "give me a haiku about my cat" was the cat's feeding
    # card (two measured meals a day), which is a fact about a cat rather than a poem about one.
    entry("haiku-on", (("haiku", "haikus"), ("about", "of", "on", "write", "make", "give", "one",
                                             "want", "need", "help", "me", "a")),
          _haiku, bias=6,
          # a definition question names the form, it does not ask for one: "what is a haiku" is
          # the count and an example, which `haiku-what` above answers
          avoid=GRAVE + OCCASION + CARD + ("what is", "whats a", "what's a", "meaning",
                                           "definition", "define", "explain", "rule", "rules",
                                           "how many")),
    entry("limerick-on", (("limerick", "limericks"), ("about", "of", "on", "write", "make", "give",
                                                      "one", "want", "need", "help", "me", "a")),
          _limerick, bias=6,
          avoid=GRAVE + OCCASION + CARD + ("what is", "whats a", "what's a", "meaning",
                                           "definition", "define", "explain", "rule", "rules",
                                           "how many")),
    # "what rhymes with orange" is a rhyme question, not a poem request, and it needs "with" so
    # that "a poem with rhymes" stays a poem.
    entry("rhyme-word", (("rhyme", "rhymes", "rhyming"), ("with", "for", "word", "does")),
          # "what rhymes with light" was the science card for light: a rare key word ("light")
          # beats a common one ("rhyme") on score, and a rhyme question is what "rhymes with"
          # asks whatever noun follows it, so this row carries enough bias to win that.
          _rhyme, bias=5),
    entry("poem-on", (("poem", "poems", "verse", "sonnet", "ode", "couplet", "rhyme", "rhymes",
                       "rhyming"),
                      ("about", "of", "on", "write", "make", "give", "one", "want", "need",
                       "short", "help", "me", "a")),
          _poem, bias=3,
          # "I'm writing a poem about my mum" is someone working, not someone asking: they want
          # help with their own line, not a poem handed to them.
          avoid=GRAVE + OCCASION + CARD + ("i'm writing", "im writing", "i am writing", "writing my",
                         "my own", "i have to write", "i've got to write", "help me write",
                         "book", "books", "reading", "recommend",
                         # a definition question names a form, it does not ask for a poem:
                         # "what is a sonnet" was handed a sonnet about autumn
                         "what is", "what are", "whats a", "what's a", "meaning", "definition",
                         "define", "explain", "difference", "how many lines")),
    # A poem written to go in a card: "write a short poem about autumn for my daughter's card"
    # names the subject and the card, and the card answer is a line or two rather than a poem.
    # When a subject is named, a poem is what was asked for; without one ("a rhyme for a
    # birthday card") the card answer keeps the line.
    entry("poem-for-a-card",
          (("poem", "poems", "verse", "rhyme", "rhymes", "rhyming", "sonnet", "ode", "couplet"),
           ("about", "of", "on")),
          _poem, bias=2, ask=("card", "cards"),
          avoid=GRAVE + OCCASION + ("i'm writing", "im writing", "i am writing", "writing my",
                                    "my own", "i have to write", "i've got to write",
                                    "help me write", "book", "books", "reading", "recommend")),
    # A poem is often asked for again: "can you do one about the sea", "something happier". The
    # line carries no form word, so the row asks the last exchange for the form.
    entry("one-more-like-that", (("one about", "another one", "do one about", "one for",
                                 "something happier", "something brighter", "something calmer",
                                 "one more please", "one more", "one other", "now one about",
                                 # A second one with its subject on it, in the words people
                                 # use: the phrase carries the "about", so the row still scores
                                 # when the subject is the only other word in the line.
                                 "one more about", "another one about", "and one about",
                                 "one other about"),
                                ("about", "can", "do", "another", "please", "mood", "happier",
                                 "more", "one")),
          _another_one, avoid=GRAVE),
    # Stories, raps and songs are the same shape of ask as a poem, so they share the mechanism:
    # a fixed form with the person's own noun slotted in where the rhyme cannot break.
    entry("story-on", (("story", "stories", "tale", "tales",
                        # A second story asked for without the word: "and one about a boat",
                        # "one more about the dog". The phrase names no form, so `_story` takes
                        # it only when a story was just told and passes on it otherwise, which
                        # is how "one about a dog" stays with the dog.
                        "one more about", "another one about", "and one about", "one about"),
                      ("about", "write", "tell", "make", "short", "one", "give", "me", "a",
                       "funny", "own", "good", "any", "some", "please", "have", "get")),
          _story, bias=1,
          # A grave line and a line asking for a pick are not a story. The child a story is for
          # used to be kept out too, on the grounds that a bedtime story had its own answer; it
          # did not - "a bedtime story for my daughter" met the hedge - and `_story` now writes
          # for the listener named.
          avoid=GRAVE + PICK_WORDS + CARD + ("story idea", "idea for a story")),
    # A song or a rap has to be asked for as one to be written: "recommend a song for a long drive"
    # and "songs for a kids party" want a pick, and `listen-when` answers those.
    entry("rap-on", (("rap", "raps", "rapping"), ("write", "make", "compose", "up", "sing", "one",
                                                "give me", "for me")),
          # "give me a rap name" wants a stage name, and the nickname row can answer that.
          _rap, bias=1, avoid=GRAVE + PICK_WORDS + OCCASION + CARD + ("name", "names",
                                                         "called")),
    entry("song-on", (("song", "songs", "lyric", "lyrics"), ("write", "make", "compose", "up",
                                                           "sing", "one", "give me", "for me")),
          _song, bias=1, avoid=GRAVE + PICK_WORDS + OCCASION + CARD),
    # "make up a character name" got the pipe, the hash and the tilde, because `language.py`
    # `mark-unnamed` keys on the word "character". The bare word is not enough on its own -
    # "how do i describe a character in a story" is the describing card's - so the key is the
    # name asked for.
    entry("character-name", (("character name", "character names", "name for my character",
                              "name for a character", "name my character", "name a character",
                              "name my protagonist", "name for my protagonist",
                              "protagonist name"),
                             ("make", "up", "invent", "suggest", "give", "think", "need",
                              "want", "call", "called", "help", "ideas", "names", "name",
                              "story", "book", "novel", "script", "villain", "hero", "heroine")),
          _character_name, bias=1,
          avoid=("biscuit", "cat", "cats", "dog", "dogs", "horse", "hamster", "rabbit", "pet",
                 "band", "stage", "rap", "nickname", "variable", "password", "domain",
                 "username", "wifi", "baby", "boy", "girl", "child", "children", "baby name")),
    entry("nickname", (("nickname", "nicknames", "nick name", "nick names", "rap name",
                        "stage name", "band name", "dj name"),
                      ("make", "up", "invent", "suggest", "give", "think", "me", "a", "for",
                       "need", "want", "call", "called")),
          _nickname, bias=1),
    entry("story-idea", (("story idea", "story ideas", "plot idea", "idea for a story",
                         "short story idea", "idea for my story"),
                        ("give", "need", "want", "help", "any", "what", "some", "me")),
          # "give me a story idea" was answered by creative.py's craft row (a want, a wall and a
          # turn): both rows scored the same and that one came first. The craft row is right for
          # "i'm writing a story and i'm stuck"; a line that asks for an idea wants ideas, which
          # is what this row has, so it carries the weight to win that.
          _story_idea, bias=3),
    # A quiz team needs a naming ask in the line, and the third part stays a phrase: "good"
    # and "best" are bare adjectives, and with "idea" in the second part two scattered words
    # made "is X a good idea" a quiz. The gate is the shape of the ask, not a quiz word -
    # "is a pub quiz a good idea for a birthday" names a quiz and still wants a party answer,
    # not a team name.
    entry("quiz-team-name", (("pub quiz", "quiz team", "team name", "quiz name", "quiz", "team"),
                            ("name", "names", "called", "call", "idea"),
                            ("team", "our team")),
          _quiz_name,
          # The gate has to cover the verb form as well as the noun one: "name our team",
          # "help us name our quiz" and "what should we call the team" are how people ask, and a
          # gate of noun phrases only sent four real asks to a hedge and a fifth to the baby
          # names. The noun phrases stay because "got any funny team names" has no verb in it.
          # The gate is a naming ask, written as the verb-and-object shapes people use rather
          # than whole phrases, because a follow-up adds words in the middle of them: "and the
          # second team" after "what should we name our quiz team" is read with the subject put
          # back in as "what should we name our second team team", and a list of full phrases
          # ("name our quiz team") missed it and lost the second name. The noun shapes stay for
          # "got any funny team names" and the bare "pub quiz team", which ask nothing else.
          ask=("name our", "name the", "name a", "name an", "name my", "name this",
               "names for", "name for", "naming", "call our", "call the", "call a", "call my",
               "call us", "help us name", "help me name", "help us call", "help me call",
               "what to name", "what should we call", "what should i call", "what should we name",
               "what should i name", "what would you call", "what would you name",
               "come up with a name", "come up with names", "think of a name", "any name",
               "needs a name", "need a name", "name ideas", "idea for a name", "ideas for a name",
               "team name", "team names", "quiz name", "quiz names", "quiz team name",
               "quiz team names", "pub quiz name", "pub quiz team name", "pub quiz team",
               "quiz team", "quiz teams", "funny name", "funny names", "pun name", "punny name"),
          # "help us name our baby" and "name our baby" are the noun-and-verb shapes of the
          # gate, so the things people name that are not a quiz team come out here instead: a
          # baby, a dog, a boat and a business are all somebody else's answer.
          avoid=("baby", "babies", "child", "children", "kid", "kids", "dog", "dogs", "cat",
                 "cats", "kitten", "puppy", "puppies", "business", "company", "shop", "boat",
                 "wifi", "network", "band", "song", "album", "podcast", "cocktail", "pet",
                 # A group and the word "names" is not always a naming ask: "how do i remember the
                 # names of my team" is the memorising-names card's question with a team in it,
                 # and "names" alone reached this row through its second part. The remembering
                 # words are the guard, so the memory card keeps its own question.
                 "remember", "remembering", "memorise", "memorize", "recall", "forget",
                 "forgetting", "keep forgetting"),
          bias=1),
    entry("band-name", (("band", "bands", "group", "act", "duo", "trio"),
                        ("name", "named", "naming", "call it", "call us", "call my",
                         "call the", "call ourselves", "come up with", "think of")),
          ("Short, sayable and easy to spell is the whole brief: two words, no apostrophes, and "
           "nothing you have to explain down a phone. Say 'we are the ...' out loud and get a "
           "friend to spell it back after hearing it once, then search it and check it is not "
           "another band or a trademark, because a name you cannot print on a poster is not a "
           "name."),
          # the question has to be asking for a suggestion: "what is my dog called" and
          # "whats my cats name" are the memory store's, and it answers them right
          ask=("should i name", "should we name", "should i call", "should we call",
               "what should i name", "what should i call", "what to name", "what could i name",
               "suggest", "ideas", "idea", "any name", "good name", "nice name", "name for my",
               "name my", "help me name", "help me pick", "recommend", "come up with",
               "think of a name", "how do i name", "rename", "what would you call"),
          # a member's name, a band's own history, and the other things people name are not this
          avoid=("member", "members", "singer", "drummer", "guitarist", "bassist", "song",
                 "songs", "album", "track", "wifi", "network", "boat", "starter", "podcast",
                 "cat", "dog", "kitten", "puppy", "baby", "business", "company", "band camp",
                 "mean", "means", "meaning", "history", "started", "formed", "origin"),
          bias=1),


    # --- buying a machine to play on, and reading more ---
    entry("gaming-platform",
          # "switch" alone is also the verb in "switching energy supplier", so it is the console's
          # full name here and the energy lines are kept out by name below
          (("console", "consoles", "playstation", "ps5", "ps4", "xbox", "nintendo",
            "nintendo switch", "switch 2", "switch lite", "gaming pc", "steam deck", "handheld"),
           ("better", "worth", "should i get", "should i buy", "or", "vs", "versus", "which",
            "choose", "buy", "getting", "get", "instead", "difference")),
          "A console is cheaper and simpler: it plays everything at good quality for years, no "
          "upgrades, and you can sell it on. A gaming PC costs more up front but gets cheaper "
          "games, higher settings and mods, and doubles as a work machine - so pick the console "
          "for a shared living room and the PC if you already sit at a desk with a monitor.",
          # a broken machine is the repair answer, and a gift is a present answer
          avoid=("broken", "fix", "repair", "not working", "boot", "screen", "overheat",
                 "energy", "supplier", "suppliers", "tariff", "broadband", "bank account",
                 "phone", "insurance", "electricity", "gas", "provider", "mobile",
                 "for my son", "for my daughter", "for a kid", "for kids", "for christmas",
                 "birthday", "present", "gift", "how much is", "price of")),
    entry("read-more-books",
          (("book", "books", "read", "reading", "novel", "novels"),
           ("more", "habit", "regularly", "again", "start", "started", "stopped", "get back",
            "get into", "tips")),
          "Keep the book where you idle - beside the kettle, in your bag, by the bed - and read in "
          "the small gaps instead of waiting for a free evening. Quit a book at about 50 pages if "
          "it has not gripped you: forcing yourself to finish things you dislike is what stops "
          "the habit.",
          # what to read next, and a book for a person, are the recommendation answers
          ask=("more", "habit", "tips", "want", "wants", "get back", "get into", "again",
               "started", "stopped", "regularly"),
          avoid=("recommend", "recommendation", "suggest", "what should i read", "good book",
                 # starting a book club is the club's own row below: this one is about the habit
                 "book club", "book clubs", "reading group", "book group", "reading club",
                 "for my mum", "for my dad", "for her", "for him", "present", "gift", "read to",
                 "reading to", "bedtime story", "learn to read", "struggling", "dyslexia",
                 # helping a child read is the school answer, and it is a parent's question
                 "help my", "help him", "help her", "help them", "his reading", "her reading",
                 "their reading", "year old", "son", "daughter", "child", "children", "kid",
                 "kids", "toddler", "pupil", "school", "phonics", "aloud",
                 # "book" is a verb as well as a thing: a table, a hotel, a flight and a doctor's
                 # appointment are all booked, and none of them is the reading habit
                 "book a", "book an", "book my", "booking a", "booked a", "appointment", "table",
                 "hotel", "flight", "flights", "reserve", "in a week")),

    # "I liked Breaking Bad, what next" names no film and no series word, so the words alone
    # cannot find it. One table of titles answers every way of asking about one, and this entry
    # stands down when the line names none of them, so a booking or a play still gets its own
    # answer.
    entry("after-named-title",
          (("liked", "loved", "enjoyed", "finished", "just finished", "binged", "got through",
            "what next", "what else", "anything else", "anything similar", "next one",
            "similar to", "like", "anything like", "after", "watch after", "next after"),
           ("what next", "what else", "anything else", "anything similar", "watch", "watching",
            "series", "tv", "telly", "film", "movie", "netflix",
            "season", "episode", "programme", "program",
            # "I just finished Line of Duty" names no medium at all, and the series is the thing
            # being finished, so the finishing words count as the second half of the key too.
            "just finished", "just watched", "just binged", "finished watching", "watched all",
            "watched the whole", "binged the whole",
            "anything like", "like this", "like that", "next after", "next one", "next")
           + AFTER_TITLE_WORDS),
          # The table only knows the titles in it, so a line naming none of them is somebody
          # else's question: "i finished my essay, what next" and "i just finished a book and
          # don't know what to read next" are about a piece of work and about books in general,
          # and each already had an answer before this entry existed.
          _after_named, ask=AFTER_TITLE_WORDS, bias=1),
    # "what hobby should i take up" and "i need a new hobby" were shrugs on main: the answer is
    # not a list of hobbies, it is how to make one stick. Kept away from the boredom line ("i'm
    # bored") and from the career questions ("should i change career").
    entry("new-hobby",
          # "take up" is an asking word, not a topic: with it in the first half, "i'm 45 and
          # thinking about taking up the piano" lost its piano answer to this. The ask goes in
          # the second half, beside the hobby noun it needs.
          # "how do i find a hobby" and "how do i get a hobby i will stick to" were both shrugs:
          # the ask is a finding word, not only a starting one. The hobby noun still gates it, so
          # a line about somebody else's hobby, or one that names the hobby, is untouched.
          (("hobby", "hobbies", "pastime", "something new to do"),
           ("new", "start", "take up", "should i", "what", "which", "ideas", "suggest",
            "learn", "beginner", "any",
            # "i need a hobby", "i want a hobby" and "how do i find a hobby" are the same ask in
            # other words, and each got something else: a question back ("What kind of hobby do
            # you usually go for?") and a search hedge on main.
            "need", "want", "find",
            # and the same ask with the words a person actually uses about keeping one going
            "how", "get a", "get into", "looking for", "fancy", "stick", "sticks",
            "stuck with", "keep up", "advice", "recommend")),
          "Pick the one thing you would happily be bad at, and buy the cheapest version: a ten "
          "pound ukulele, a second-hand chess set, a supermarket sketchbook and pencils. Keep it "
          "in the room where you sit, and give it twenty minutes twice a week. The hobby that "
          "sticks is the one with the shortest walk to it, not the one you researched most.",
          # Two kinds of line stand this card down, and neither is "the line names a person":
          # "hobby ideas for kids" and "what hobby should i take up with my kids" are the same
          # advice and it is as good with the kids as alone. What does not fit is a line where
          # the money has run out ("i need a hobby but im broke" is the money rows' question)
          # and a line that wants the hobby shared with friends, which is the club answer.
          avoid=("no money", "broke", "skint", "friend", "friends")),
    # "what should i do this weekend" was the commonest everyday ask on the deck with no
    # answer: main said "I'd rather not guess. A quick search online..." to it. Nothing in it
    # is a fact to look up - it is the friend's answer, one thing out of the house and one for
    # the evening - and the question form is the only part that missed, because "i'm bored this
    # weekend" already had a good answer.
    #
    # The entry is the ASKING shape plus the time, not the time word plus any old ask word: a
    # first cut keyed on "weekend"/"saturday" with "can i do"/"any ideas" in the second half
    # and took "i have toothache at the weekend, what can i do", "ive got half a cabbage left
    # from sunday, what can i do with it" and "were having a bbq saturday but its ment to rain,
    # any ideas" with it. Those name a thing to deal with, and the free time is only when it
    # happens.
    entry("weekend-do",
          (("should i do", "can i do", "shall i do", "shall we do", "what do i do", "what to do",
            "anything to do", "something to do", "things to do"),
           ("weekend", "weekends", "this weekend", "next weekend", "at the weekend",
            "on the weekend", "for the weekend", "saturday", "sundays", "sunday", "this saturday",
            "this sunday", "day off", "day off on", "free day", "free saturday", "free sunday",
            # A spare hour is the same question with less of it: "what can i do for an hour"
            # and "i have an hour to kill what can i do" were the hourly-pay row, which told
            # the person how to divide a salary by 37.5 hours a week.
            "an hour", "half an hour", "an hour to", "an hour or two", "a couple of hours",
            "couple of hours", "two hours", "three hours", "a few hours", "spare hour",
            "free hour")),
          _an_hour_or_a_day,
          ask=("what", "any", "ideas", "suggest", "recommend", "how"),
          # "what can i do with it" and "what can i do with them" are about the thing named,
          # and "what should i do there" is about the place: the free time in all three is only
          # when it happens. A body word or a trip is somebody else's answer for the same
          # reason, and each of these is a word another entry keys on.
          avoid=("with it", "with them", "with that", "what should i do there", "there",
                 "toothache", "tooth", "teeth", "pain", "hurts", "hurting", "ache", "aches",
                 "sick", "ill", "unwell", "doctor", "dentist", "hospital", "pharmacy",
                 "cook", "cooking", "eat", "eating", "recipe", "dinner", "lunch", "breakfast",
                 "bbq", "barbecue", "roast", "cabbage",
                 "watch", "watching", "film", "films", "series", "boxset", "box set", "netflix",
                 "read", "reading", "book", "books", "wear", "outfit", "plant", "plants",
                 "garden", "weeds", "mow", "prune", "clean", "cleaning", "tidy", "paint",
                 "decorate", "away", "holiday", "holidays", "trip", "abroad", "kids",
                 "children", "child", "toddler", "baby", "family", "work", "working", "shift",
                 "overtime", "homework", "revision", "study", "exam", "gym", "run", "running",
                 "exercise", "weight", "budget", "money", "afford", "shop", "shopping", "buy",
                 "buying", "book a", "book an", "booking", "leave", "annual leave", "birthday",
                 "present", "gift", "on tv"),
          # The leave entry also reaches "ive got a day off on friday, what should i do", and
          # outranks this one there: a line asking what to DO with the day wants the day.
          guard=_no_city_is_named,
          bias=1),
    # "any ideas for a fun night in" and "what can i do for a fun night in" reached nothing, so
    # the composer's tips branch answered a request for ideas with a troubleshooting question
    # ("What usually goes wrong? Start there, not with the whole list."). The evening at home is
    # its own want: not the weekend (out and home), not the thing to watch, not the thing to cook.
    # The ask has to be an ask, and kids, a night out, a hotel and a night in a fridge are other
    # questions, so the second half of the key and the avoid list both do work here.
    entry("evening-in",
          (("night in", "evening in", "night at home", "evening at home", "staying in",
            "stay in tonight", "staying in tonight", "cosy night", "cozy night",
            "cosy evening", "cozy evening", "quiet night in", "night indoors"),
           ("ideas", "idea", "what", "any", "something", "suggest", "recommend", "fun",
            "to do", "can do", "can we do", "plan", "anything", "whats", "what's")),
          "Three things, and the cooking is what makes it an evening rather than a sofa: a "
          "supermarket dough ball each to top yourselves, a slow thing in the oven, or a "
          "cocktail that takes two people. Then one film nobody in the house has seen, started "
          "before nine, and a game that is not a screen - cards, a jigsaw, or a quiz you write "
          "for each other.",
          # "nights" is not in this list although "night out" is: the avoid words are matched
          # in their plural forms too, so a bare "nights" stood this row down on its own key
          # ("any ideas for a fun night in" matched "night in" and "nights" both).
          guard=_names_the_evening,
          avoid=("night out", "night away", "night shift", "hotel", "hospital",
                 "stay in bed", "overnight", "in the fridge", "in the oven", "marinade",
                 "kids", "kid", "children", "child", "toddler", "baby", "teen", "teenager",
                 "family", "with my parents", "babysit", "romantic", "proposal",
                 # a night in is also when people cook the thing they asked about: "how do i
                 # cook a chicken for a night in" is the chicken, not the evening
                 "cook", "cooking", "roast", "bake", "oven", "recipe", "marinade", "dinner",
                 "supper", "eat", "eating", "make for")),
    # "any ideas for things to do in the rain" and "it is raining what can i do" were the tips
    # branch's troubleshooting question, and the card that answers a wet day with children in it
    # (family.py, kids-day-out-budget) is a different answer: one thing with a roof, one without.
    # A wet day on your own wants one thing out and one long thing in, so the children's words
    # hold this row off and the point of the day is the shape of the answers.
    entry("wet-day",
          (("rain", "raining", "rains", "rainy", "pouring", "drizzle", "drizzling",
            "showers", "storm", "storms", "wet day", "wet days", "wet weekend",
            "wet weekends", "wet afternoon", "wet weather", "wet out", "wet one"),
           ("things to do", "something to do", "what can i do", "what can we do",
            "what shall we do", "what should i do", "what to do", "ideas", "idea", "bored",
            "fill the day", "day off", "is there to do", "there to do", "anything to do")),
          "One thing out of the house and one long thing at home is what saves a wet day. Out: "
          "the swimming pool, the library, a free museum gallery, or a walk in proper "
          "waterproofs, because a wet park is empty. Home: something with a start and an end, a "
          "whole film, a proper cook, a board game, or the job you keep not doing. Decide both "
          "in the morning, or the afternoon goes to the sofa and a phone.",
          guard=_names_the_weather,
          avoid=("kid", "kids", "child", "children", "toddler", "baby", "family", "teen",
                 "school holiday", "half term", "leak", "leaking", "roof", "gutter",
                 "gutters", "damp", "flood", "flooded", "puddle", "washing", "laundry",
                 "dry my", "drying", "put the washing", "line", "umbrella", "coat",
                 "jacket", "boots", "waterproof", "commute", "drive", "driving", "cycle",
                 "cycling", "bike", "motorbike", "bbq", "barbecue", "wedding", "fete",
                 "match", "pitch", "cricket", "tennis", "golf", "picnic", "camping",
                 "tent", "garden", "plants", "sow", "plant out", "hose", "water the",
                 "windscreen", "car", "roof rack", "drain", "drains", "gutter down",
                 "sports day", "walk to work", "school run",
                 # "a rainy day" is an idiom for the money kept for trouble, so a line with a
                 # saving word in it is the savings question even with "what can i do" in front:
                 # "what can i do to save for a rainy day" was the day-out plan.
                 "save", "saves", "saving", "savings", "put by", "put away", "set aside",
                 "rainy day fund", "emergency fund", "fund", "invest", "pension", "budget",
                 "afford", "debt", "pay off", "overdraft", "credit card", "interest",
                 # water inside the house, not weather: the words above are about the sky, so
                 # "the attic is wet what should i do" and "what can i do about a wet wall"
                 # read as a wet day out and got the day-out plan instead of the repair. The
                 # word to keep clear is the room or the surface it is on, not the water.
                 "basement", "cellar", "attic", "loft", "wall", "walls", "ceiling",
                 "ceilings", "floor", "floors", "floorboard", "floorboards", "carpet",
                 "soaked", "condensation", "radiator", "pipe", "pipes", "plumbing",
                 "water coming in", "water coming through", "water coming up",
                 "coming through the", "coming in through", "sodden", "wet patch",
                 "damp patch", "mould", "mold", "smell of damp")),
    # "how do i start a book club" was answered by the reading-habit row ("keep the book where
    # you idle - beside the kettle"), which is advice for one person reading, not for a group.
    entry("start-a-book-club",
          (("book club", "book clubs", "reading group", "reading club", "book group",
            "book circle"),
           ("start", "starting", "set up", "setup", "run", "running", "first meeting",
            "how do i", "how to", "choose books", "pick books", "organise", "organize")),
          "Ask four or five people, not a crowd, and fix the next date before the first meeting "
          "ends - a club that meets every six weeks at a set day keeps going, one that waits for "
          "everyone to be free does not. Pick short books to begin with, let whoever chose it "
          "lead for ten minutes, and bring one question rather than a summary: \"who did you "
          "believe?\", \"what would you have done?\". Rotate who chooses, keep food simple, and "
          "let people come having only read half. To join one instead of starting one, ask at "
          "the library and the independent bookshop: both keep a list, and a group of five "
          "usually has room.",
          ask=("start", "starting", "set up", "setup", "run", "running", "first meeting",
               "how do i", "how to", "organise", "organize", "choose books", "pick books"),
          # a book to recommend, a reading habit, and reading to a child are other answers
          avoid=("recommend", "recommendation", "what should i read", "good book", "for my mum",
                 "for my dad", "present", "gift", "read to", "reading to", "bedtime story",
                 "learn to read", "struggling", "dyslexia", "audiobook", "kindle", "library",
                 "how many books", "how long to read")),
    # --- a pick asked for by company, or by a limit -----------------------------
    # "A film to watch with my parents", "im looking for a book for me", "any series
    # recommendations": the medium plus who it is for, or the medium plus the shape of the ask.
    # The mood tables keep the lines with a feeling in them (see PICK_MOODS), and everything that
    # is not a request - a gift, a repair, a booking, a subscription, the habit of reading - has
    # its own answer, so it is all held out by name.
    # "good french films" then "any japanese ones": the second line names the country and leaves
    # the medium to the turn before it, so the country is its own way in. The pair is the country
    # word and an ask, and the medium is carried (see _pick_carry), which is the same reading the
    # limit entries do.
    entry("pick-country", (CINEMA_WORDS, PICK_ASK + ("ones", "one", "more", "another", "other")),
          _pick_plain, bias=1, guard=_a_country_is_a_country,
          avoid=_PICK_AVOID + ("seen", "watched", "liked", "loved")),
    # A kind of film - "a christmas film", "good action films", "something western" - is a
    # shelf, and the shelf answers with its own three films. It sits ahead of pick-plain, which
    # would otherwise hand the same three general films to every kind somebody names.
    # The kind is the first part, so the kind is what has to be said: with the medium first,
    # "i want a film that isnt scary" reached this row on "film" and "want" and took a line that
    # belongs to `film-nothing-scary`, and "i want to watch something that makes me think" took
    # one that belongs to the mood table. A kind named with no medium ("good westerns") still
    # reaches it, because an ask word is as good as a medium for the second part.
    entry("film-kind", (FILM_KIND_WORDS, PICK_MEDIUM + PICK_ASK),
          _film_kind_reply, bias=2,
          # a kind of *evening* is not a kind of film: a flight to book for christmas is the
          # travel answer, and the words that ask for a booking are the ones that say so
          avoid=_PICK_AVOID + PICK_REACT + KIND_AVOID
          + ("flight", "flights", "hotel", "hotels", "taxi", "ticket", "tickets",
             "book a", "book my", "book the", "booking", "reserve", "table for",
             "appointment",
             # a christmas do is an evening somebody has been asked to, not a film: "i dont
             # want to go to the works christmas do" was answered with three Christmas films.
             # The kind of evening named by "do" or "night out" is the refusal row's line.
             "works do", "work do", "christmas do", "office party", "christmas party",
             "night out", "dont want to go", "don't want to go", "do i have to go",
             "get out of", "make my excuses", "cant come", "can't come")),

    # A length limit is a number, and the number is the answer: "a film under 100 minutes" and
    # "something under two hours" both get films that fit, with the runtime beside each one.
    # `bias` is what keeps a bare "something under two hours" here: the plan-ideas entry answers
    # it with "Got it", and a limit that says the number is a question this table can settle.
    entry("film-length", (PICK_MEDIUM + LIMIT_WORDS, (
                              "minutes", "minute", "mins", "min",
                              "hours", "hour", "hrs", "hr")),
          _film_under, bias=3, avoid=_LENGTH_AVOID),

    entry("pick-plain", (PICK_MEDIUM, PICK_ASK + PICK_WHO + CINEMA_WORDS + SUBS_KEY),
          _pick_plain, bias=1, guard=_a_country_is_a_country,
          avoid=_PICK_AVOID + PICK_MOODS
          + ("gift", "presents", "birthday", "christmas", "buy", "bought", "buying",
             "for my mum", "for my dad", "for her", "for him",
             # tonight, a Friday and a wet Sunday are the occasion entries' questions, and they
             # answer with the same three films
             "tonight", "evening", "night in", "weekend", "saturday", "sunday", "afternoon",
             "later on", "this evening",
             # a limit read as a complaint is the entry below; the pick answers it in passing
             "subscription", "subscriptions", "cancel", "netflix", "prime", "disney", "now tv",
             "apple tv", "streaming", "iplayer", "all 4", "itvx", "channel 4",
             # how to watch something is a streaming question, not a pick
             "abroad", "outside the uk", "vpn", "in spain", "in france", "in america",
             "in australia", "in canada", "download", "record", "not working", "wont play",
             "won't play", "wont load", "buffering", "no signal", "aerial", "licence",
             "license", "password", "account", "log in", "login", "cost", "price",
             "how much", "free trial", "scam", "charge",
             # a habit and a goal are not a pick, and both have an answer of their own
             "more", "this year", "habit", "every day", "resolution", "get back into",
             "get into", "started", "stopped", "concentration", "focus", "before bed",
             "for you", "good for", "bad for", "healthy", "unhealthy", "screen time",
             "help me", "improve", "worth reading",
             "aloud", "read to", "reading to", "learn to read", "struggling", "dyslexia",
             "phonics", "bedtime story",
             # "book" is a verb: a table, a hotel, a flight and a doctor are all booked
             # ("booked" and "booking" are not here: both fold to "book", and an avoid word
             # is matched by its loose form, so either one would turn every book line away.)
             "book a", "book an", "book my", "hotel", "table", "flight",
             "flights", "train", "taxi", "ticket", "tickets", "appointment", "reserve",
             # a journey has the holiday-read answer, which names the easier books, and a
             # reading *skill* is a study question: "something to read on the plane" and "i need
             # to read for my exam" are not asks about what to read next. The same words are
             # held out of `book-mood` for the same reason.
             "holiday", "holidays", "beach", "pool", "plane", "journey", "commute",
             "exam", "exams", "revision", "revise", "revising", "study", "studying",
             "remember", "forget", "forgetting", "memorise", "memorize", "concentrate",
             # "read" is not always a book: the word after it says what is being read, and a
             # label, the news, a meter or a set of instructions is answered by its own row or
             # by nobody. "can you read the label for me" and "i want to read the news" both got
             # the book pick before these.
             "label", "labels", "news", "meter", "map", "maps", "instructions", "manual",
             "recipe", "recipes", "menu", "spreadsheet", "report", "email", "emails",
             "letter", "sign", "timetable", "bill", "invoice", "forecast", "thermometer",
             "gauge", "contract", "terms and conditions", "small print", "balance", "statement",
             # watching a thing that is not a programme
             "weight", "diet", "dieting", "calories", "what i eat",
             "repair", "fix", "broken", "fault", "faulty", "broken down")),
    # "we only have bbc and itv", "my mum doesnt like subtitles": a limit, said on its own, one
    # turn after the ask. It was read as a complaint about a person and answered with a question,
    # when what the person needs is the pick that fits. The phrases are the key, so a fault
    # ("the subtitles wont turn off") and a licence question stay with the entries that know them.
    entry("pick-limit", (FREE_TELLS + SUBS_TELLS,
                         ("only", "just", "got", "have", "no", "not", "dont", "doesnt", "cant",
                          "never", "hate", "hates", "without", "like", "want", "watching")),
          _pick_limit_reply, bias=1,
          avoid=("not working", "wont play", "won't play", "wont load", "not loading",
                 "no signal", "aerial", "licence", "license", "log in", "login", "password",
                 "account", "how much", "cost", "price", "abroad", "outside the uk", "vpn",
                 "in spain", "in france", "turn off", "turned off", "turn on", "turned on",
                 "enable", "disable", "size", "colour", "color", "sync", "delay", "tiny",
                 "missing", "gone", "wont turn", "won't turn", "appear", "come back")),
    # A costume for a party is a make-it-yourself question and the bot had nothing for it: "how do
    # i make a costume" and "my daughter has a party friday and wants a costume, what can i make
    # at home" both reached "I don't know enough to answer that honestly", and "how do i make a
    # fancy dress costume" was answered with salad dressing. The key is the costume plus the making
    # of it, so a costume somebody is buying, hiring or wearing needs no change of its own.
    entry("costume-at-home",
          (("costume", "costumes", "fancy dress", "dress up", "dressing up", "world book day",
            "what can i be", "what shall i be"),
           ("make", "making", "made", "homemade", "home made", "at home", "last minute", "cheap",
            "cheaply", "diy", "ideas", "what can i", "how do i", "out of things", "from things",
            "no time", "quick")),
          ("Make the shape, not the whole outfit: black leggings and a black top read as almost "
           "anything, then one thing does the work - a cardboard box for a robot or a rocket, a "
           "bin bag and a belt for a cape, a paper plate and elastic for a mask, a stripy top and "
           "an eye patch for a pirate. Paint it the night before, not the morning of, and ask the "
           "party's theme first. If it is for world book day, check the school's rules, because "
           "some ban masks and face paint."),
          # buying one, hiring one and getting paint out of one are other answers
          avoid=("buy", "buying", "bought", "shop", "hire", "hiring", "rent", "price", "cost",
                 "how much", "where can i", "in the wash", "stain", "stains", "too small",
                 "alter", "altering", "hem", "sew", "sewing machine", "photo", "photos")),

]


def _film_list(text):
    """An entry reply that keeps to a length the line states.

    A row whose answer is a list of films was written without a limit in mind, and the person who
    says "under two hours" gets a list that ignores it. One wrapper over the reply fixes every
    such row at once, and the list is untouched on a line that states no length.
    """
    def said(memory, understood):
        line = "%s %s" % ((understood.get("clean") or "") if isinstance(understood, dict) else "",
                          (understood.get("norm_text") or "") if isinstance(understood, dict) else "")
        return _films_within(text, line)
    return said


# Every row whose answer names two films this module knows the runtime of is read against a limit
# the line states. The names are the ones in `FILM_MINUTES`, so the wrapper only ever trims a list
# whose runtimes are known, and a row of books, series or podcasts is left exactly as written.
for _e in ENTRIES:
    if isinstance(_e.reply, str) and len(set(re.findall(r"\*([^*]{2,60})\*", _e.reply))
                                        & set(FILM_MINUTES)) >= 2:
        _e.reply = _film_list(_e.reply)
# The words of the music itself, as opposed to a pick of what to listen to: "what is a chord in
# music" was three albums (off "music" and "what") and "what is an octave" was a search hedge.
# One answer per word, like the grammar terms in bot/knowledge/language.py.
MUSIC_TERMS = {
    "chord": ("A chord is three or more notes played together: C major is C, E and G, all at "
              "once. Major chords sound settled and minor ones sound sad, which is most of why a "
              "song has a mood at all."),
    "key": ("The key is the home note a piece is built around and comes back to: a song in C "
            "keeps landing on C. The notes it uses are that key's scale, and a key change lifts "
            "the whole song."),
    "scale": ("A scale is the ladder of notes a key is made of, up or down: do re mi fa sol la "
              "ti do. A major scale sounds bright and a minor one darker, and both are eight "
              "notes with the first repeated at the top."),
    "octave": ("An octave is the gap between a note and the same note higher or lower, eight "
              "notes up the scale. It sounds like the same note because the frequency exactly "
              "doubles: A is 440 vibrations a second, the A above it 880."),
    "time signature": ("The two numbers at the start of the music. The top one is how many beats "
                       "are in a bar and the bottom one which note gets the beat, so 4/4 is four "
                       "quarter notes to the bar (most pop) and 3/4 is a waltz."),
    "bar": ("A bar is one group of beats, marked off by the bar lines on the page: in 4/4 that "
            "is four beats to a bar, which is why eight bars is the length of most pop verses. A "
            "bar and a measure are the same thing."),
    "beat": ("The beat is the steady pulse you clap or tap along to; the rhythm is the pattern "
             "played on top of it. Four beats to the bar is most pop, three is a waltz, and a "
             "drummer keeps the beat while everyone else plays around it."),
    "tempo": ("Tempo is how fast the music goes, counted in beats per minute: 60 is one a second "
              "and a ballad, 120 is two a second and a dance track. A metronome clicks it for you."),
    "bpm": ("BPM is beats per minute, how fast the music goes: 60 is one a second and a ballad, "
            "120 is two a second and a dance track. A metronome clicks it for you."),
    "pitch": ("Pitch is how high or low a note is, set by how fast the sound vibrates: a short "
              "string or a tight one vibrates faster and sounds higher."),
    "melody": ("The melody is the tune - the line of single notes you could sing on its own. The "
               "harmony is the chords underneath it, and the rhythm is the pattern in time."),
    "harmony": ("Harmony is two or more notes sounding together, usually as the chords under the "
                "melody. It is what makes a bare tune sound full, and what a second singer adds."),
    "rhythm": ("Rhythm is the pattern of the music in time - where the beats fall and which are "
               "strong. A drummer keeps it, and you can clap it without knowing any notes."),
    "pre chorus": ("The pre-chorus is the short section between the verse and the chorus that "
                   "builds towards it: the words change each time, the music lifts, and then the "
                   "chorus lands. It is the ramp rather than the hook."),
    "chorus": ("The chorus is the part that comes round again with the same words - the bit you "
               "can sing back after one listen, and usually the title. The verses in between "
               "change each time and carry the story, and a bridge is the one different section "
               "near the end."),
    "hook": ("The hook is the short phrase that catches you: a chorus line, a riff or a bit of "
             "vocal you find yourself humming. A producer will often make it the first thing you "
             "hear in the song."),
    "riff": ("A riff is a short repeated phrase of notes, usually on guitar or keys, that a song "
             "is built on: the opening of *Smoke on the Water* or *Seven Nation Army*. It is a "
             "hook you can play rather than sing."),
    "sample": ("A sample is a piece of an existing recording lifted into a new track - a drum "
               "break, a vocal line or a chord. Hip hop and dance music are built on them, and "
               "the original artist is usually credited and paid."),
    "progression": ("A chord progression is the order the chords come in, usually a short loop "
                    "that repeats: C, G, A minor, F is the one behind a thousand pop songs. The "
                    "loop is what the melody and the words sit on, and changing one chord changes "
                    "the whole mood."),
    "key signature": ("The key signature is the sharps or flats written at the start of every "
                      "line of music, and they say which key the piece is in: one sharp is G "
                      "major, one flat is F major, none is C major. It saves writing the same "
                      "sharp or flat beside every note."),
    "arpeggio": ("An arpeggio is a chord played one note at a time instead of all together: C, "
                 "E, G, one after another, low to high. It is what fingerpicking is made of and "
                 "what you hear when a piano player rolls through the chords."),
    "tab": ("Tab (tablature) is guitar music written as six lines for the six strings, with a "
            "number on a line meaning that fret on that string: a 3 on the top line is the third "
            "fret of the top string. It is read left to right like a sentence, it skips the "
            "rhythm, and it is how most people learn a song by ear-free copying."),
    "interval": ("An interval is the distance between two notes, counted in the steps of the "
                 "scale: C up to G is a fifth, C up to E a third, and the same note twice an "
                 "octave. Every chord and tune is made of them, so learning their sounds by ear "
                 "is the single most useful bit of theory there is."),
    "clef": ("A clef is the sign at the start of the staff that says which lines are which notes. "
             "Treble clef curls round the second line up, which is G, and is used for the right "
             "hand of a piano, the violin and most singing; bass clef covers the low lines for the "
             "left hand, the cello and the bass."),
    "middle c": ("Middle C is the C nearest the middle of a piano keyboard, the one four white "
                 "keys in from the left of the group of two black keys in the middle. Written in "
                 "treble clef it sits on its own short line just below the staff, and in bass clef "
                 "on a short line just above it, which is why it is the note that joins the two "
                 "hands."),
    "transpose": ("To transpose is to move a whole piece into a different key, keeping the tune "
                  "and the shapes of the chords the same and shifting every note by the same "
                  "amount - usually so a singer can reach it. On a guitar a capo transposes "
                  "without changing anything you play; a keyboard has a transpose button that "
                  "does it for you."),
    "metronome": ("A metronome clicks a steady beat at whatever speed you set, in beats per minute, "
                  "so you can hear whether you are rushing. Practise the hard bar at a speed you "
                  "can play it clean three times running, then nudge it up five at a time - it is "
                  "the cheapest way to get faster, and a phone app does the job."),
    "producer": ("The producer is the person who shapes the recording: the arrangement, the "
                 "sounds, how the parts fit, and the mix at the end. They are not the songwriter "
                 "and not the engineer. In film the word means the person who runs the money and "
                 "the schedule, a different job."),
}
# "what is transposing" is the same question as "what is a transpose", and the words list holds
# the exact spelling, so the -ing form gets its own key rather than its own paragraph.
MUSIC_TERMS["transposing"] = MUSIC_TERMS["transpose"]

_MUSIC_ASKS = ("what is", "whats", "what's", "what are", "mean", "meaning", "definition",
               "define", "explain", "difference", "simple terms", "music", "theory",
               # "where is middle c", "how do i use a metronome": the same word, asked as a
               # practical question rather than a definition
               "where is", "where's", "how do i use", "how di i use", "how to use")


# A word that only means the music word when the music is in the line: a producer makes a film
# or a record, and "what does a film producer do" was handed the studio answer.
_MUSIC_WORD_BESIDE = {
    "producer": ("music", "song", "songs", "album", "record", "records", "band", "studio",
                 "track", "single", "beats", "rap", "mix", "mixing"),
}
_MUSIC_ALL = ("music", "song", "songs", "album", "albums", "record", "band", "track")
# Gear is a shopping question, not a definition: "what is a good chorus pedal" was the chorus.
_MUSIC_GEAR = ("pedal", "pedals", "amp", "amps", "amplifier", "string", "strings", "case",
               "stand", "pick", "picks", "capo", "tuner")

# The other job each word does in ordinary English. A pitch is a sales talk and a football field,
# a key opens a door, harmony at home is not a chord, and a scale weighs you: each of those was
# answered with the music word (or, for the pitch in football, nothing at all), so the row stands
# down when the line says the other thing and lets that question's own row answer it.
_MUSIC_ELSEWHERE = {
    "pitch": ("sales", "sell", "selling", "sold", "football", "soccer", "rugby", "hockey",
              "tent", "roof", "mortgage", "elevator", "throw", "pitcher", "baseball", "cricket",
              "market", "investor", "investors", "deck", "campaign"),
    "key": ("house", "home", "door", "doors", "car", "cut", "spare", "locked", "lock", "lost",
            "keyboard", "fob", "window", "safe", "padlock", "gate", "bike", "shed", "rental",
            # "what is a key on a keyboard" is the row above the letters, not the home note
            "shift", "ctrl", "alt", "enter", "tab", "caps", "typing", "laptop", "computer",
            # the key to a good marriage, the key to success: a how-to, not the home note
            "marriage", "success", "happiness", "key to", "key to a", "to a good",
            "relationship", "friendship", "healthy", "losing weight", "weight loss"),
    "harmony": ("home", "family", "relationship", "marriage", "team", "office", "work",
                "neighbours", "neighbors", "kids", "children", "household", "flat", "staff"),
    "scale": ("kettle", "weigh", "weight", "kitchen", "bathroom", "pay", "salary", "wage",
              # the white scale in a house is not the ladder of notes: "what can i do about the
              # scale on my taps" was answered with do re mi, because the plumbing had no word
              # in this list - only the kettle did
              "tap", "taps", "shower", "showers", "shower head", "showerhead", "boiler",
              "radiator", "radiators", "washing machine", "dishwasher", "toilet", "bath",
              "limescale", "descale", "descaling", "furred", "furring", "chalky", "hard water",
              "white marks", "white stuff", "water",
              "business", "map", "model", "ladder", "fish", "economies", "earthquake",
              # the maths scale and the drawing scale are not the ladder of notes
              "maths", "math", "mathematics", "graph", "axis", "ruler", "drawing", "draw",
              "plan", "measurement", "measure", "richter", "temperature",
              # the pH scale, the Beaufort scale and the Likert scale are not the ladder of notes
              "ph", "ph scale", "ph of", "ph value", "ph level", "acidity", "acid", "alkaline",
              "litmus", "chemistry", "chemical", "beaufort", "wind", "likert", "survey",
              "pain", "rating"),
    "tempo": ("temperature", "fever", "symptom", "symptoms",
              # a tempo run and the tempo of a chess game are not beats per minute
              "run", "runs", "running", "ran", "jog", "jogging", "marathon", "5k", "10k",
              "race", "parkrun", "threshold", "interval", "intervals", "splits", "pace",
              "pacing", "mile", "miles", "training", "workout", "gym", "cycling", "swim",
              "swimming", "chess", "move", "moves", "board", "opening", "endgame", "game"),
    # a hook is also the thing on a coat, a curtain, a punch, a golf shot and a fish
    # a chorus is also what a cold does to your voice, and bpm is a heart rate on a watch
    "chorus": ("cold", "colds", "chest", "cough", "coughing", "throat", "sore throat",
               "flu", "covid", "symptom", "symptoms", "fever", "blocked", "runny",
               # a chorus line is the dancers on a stage, and a chorus girl is one of them
               "line", "lines", "chorus girl", "girls", "dancers", "dancer", "choreography",
               "stage", "theatre", "theater", "west end", "broadway", "musical"),
    # a career progression is not a chord progression, and a disease progresses
    "progression": ("career", "job", "work", "promotion", "training", "disease", "diseases",
                    "illness", "condition", "symptoms", "cancer", "treatment", "patients"),
    # a riff on a subject is a comedian's joke, and an essay opens with its own hook
    "riff": ("comedy", "comedian", "comedians", "joke", "jokes", "humour", "humor", "rant",
             "stand up", "stand-up", "satire", "parody", "improvise"),
    "bpm": ("watch", "smartwatch", "fitness", "tracker", "heart", "pulse", "resting",
            "exercise", "cardio", "fat burn", "zone", "run", "runs", "running", "jog",
            "jogging", "pace", "marathon", "5k", "10k", "training"),
    # a bar is a pub, a slab of chocolate or soap, a gold ingot, an exam and a chart; a beat is
    # what you do to an egg, a policeman's round and someone you beat at tennis
    "bar": ("pub", "pint", "chocolate", "soap", "gold", "silver", "iron", "exam", "chart",
            "graph", "code", "barcode", "sandwich", "protein", "cereal", "snack", "cafe",
            "restaurant", "drinks", "beer", "wine", "cocktail", "nightclub", "crowbar",
            "tow bar", "handlebar", "sandbar", "bar chart", "bar exam", "bar of"),
    "beat": ("eggs", "egg", "whisk", "police", "cop", "cops", "officer", "officers",
             "patrol", "patrols", "village", "constable", "cheat", "defeat", "beaten", "boxing",
             "record", "records", "opponent", "tennis", "chess", "game", "score", "team",
             "traffic", "heart", "rate", "price", "expectations", "inflation"),
    # short words are left out on purpose: the check is a substring of the whole line, so "hat"
    # matches "what" and "bra" matches "brass", and a music question stands down for no reason.
    "hook": ("coats", "coat hook", "curtain", "curtains", "curtain hook", "towels",
             "hangers", "hanger", "boxing", "punches", "punch", "jabbed", "left hook",
             "right hook", "golf", "tennis", "fishing", "fishes", "crane", "hoist",
             "crochet", "knitting", "sewing", "dressing gown", "picture hook", "ceiling",
             "hook up", "wall hook", "lifting", "climbing", "cargo", "scaffold",
             "python", "programming", "plugin", "react hook", "git hook", "hooks in",
             # the hook of an essay is its opening, and a writer hooks a reader
             "writing", "essay", "essays", "story", "paragraph", "introduction", "headline",
             "blog", "article", "opening line", "reader"),
    # a chord is also a straight line across a circle, and that question came out as the notes
    "chord": ("spinal", "vocal", "struck", "touch", "geometry", "circle", "triangle", "arc",
              "angle", "angles", "maths", "math", "radius", "diameter", "theorem"),
    # a tab is a browser tab, a bar tab and a pickup truck, and the interval that matters most
    # is the one in a running plan
    "tab": ("browser", "chrome", "firefox", "safari", "window", "windows", "bar tab",
            "run a tab", "pickup", "truck", "tablet", "tabs open"),
    "interval": ("run", "runs", "running", "jog", "jogging", "cycling", "walking", "training",
                 "workout", "gym", "sprint", "sprints", "5k", "10k", "marathon", "parkrun",
                 "hiit", "rest", "reps", "sets", "blood", "screening", "appointment"),
    # a sample is also a pot of soil or a swab at the doctor, and "what is a sample of soil" was
    # handed the recording answer
    "sample": ("soil", "blood", "urine", "swab", "dna", "water", "rock", "seed", "lab",
               "laboratory", "testing", "tested", "statistics", "survey", "data"),
}


# The words that make a line a music question even when the term is an everyday word too: with
# one of these in it, the glossary answers whatever else is there. This is the positive half of
# the gate, and it is what fixes the two senses a list of other-sense words cannot: a coat hook
# is "a hook on a coat", and a list that holds "coats" misses the singular, while a fish hook and
# a hook in hockey are fishing and hockey rather than music.
_A_MUSIC_WORD = ("music", "musical", "song", "songs", "tune", "tunes", "melody", "chorus",
                 "verse", "band", "guitar", "piano", "drums", "singing", "singer", "album",
                 "track", "rhythm", "bars", "notes", "orchestra", "violin", "lyrics", "gig",
                 "concert", "playlist", "bpm", "beats per minute", "time signature", "octave",
                 "chord", "scale", "harmony", "key of")

# Terms whose everyday sense is as common as the music one, and where the bare question has no
# answer that fits both: "a hook" is fishing, boxing and a coat as often as it is a chorus, and
# "a beat" is an egg, a policeman's round and a drummer. These wait for the music word; the rest
# of the glossary still answers on its own, which is how "what is a tempo" keeps its answer.
_NEEDS_A_MUSIC_WORD = frozenset(("hook", "beat", "riff", "sample", "tab", "interval"))


# A thing of theirs in front of the word is the object, not the term: a key that is "my keys" is
# a door key and a scale that is "my scale" is the bathroom one, and "wheres my keys" was answered
# with the music definition. Only the words that are also an everyday possession are held back,
# so "what key is my song in" and "what scale is that solo in" still get the music.
# The words that make the next noun somebody's own thing ("my keys") rather than the name of a
# music word. The two-word ones are here because "my mum's keys" is said as "my mums keys" and the
# word straight in front of the noun is then "mums", which on its own is nobody's.
_POSSESSIVE = ("my", "our", "his", "her", "their", "your", "my mums", "my dads", "our mums",
               "our dads", "his mums", "her mums", "his dads", "her dads")
_A_THING_OF_THEIRS = ("key", "keys", "scale", "scales")

# `your` is the one possessive that is also how a definition is asked ("what is your key" is
# nobody's keyring), so it only stands the row down in a line that is looking for the thing.
_LOOKING_FOR_THE_THING = ("wheres", "where's", "where", "lost", "find", "seen", "mislaid",
                          "misplaced", "cant", "can't", "missing", "look", "looking")


def _somebodys_own_thing(said, at):
    """True when the noun at `said[at]` is the person's own, so the music row is not the answer."""
    if not at:
        return False
    before = said[at - 1]
    if before not in _POSSESSIVE and not (at >= 2 and " ".join(said[at - 2:at]) in _POSSESSIVE):
        return False
    if before == "your" or " ".join(said[at - 2:at]).endswith("your"):
        return any(one in said for one in _LOOKING_FOR_THE_THING)
    return True


def _music_elsewhere(understood):
    """False when the line's key word is the everyday word rather than the music one."""
    said = [str(word).lower() for word in (understood.get("words") or ())]
    flat = " ".join(said)
    for word in sorted(MUSIC_TERMS, key=len, reverse=True):
        # The row matches the plural of the same word ("keys" for "key") and the lookup adds the
        # stem it matched to the words, so the guard has to read both forms and the word in front
        # of whichever one is there - or the line that stands the row down never reaches it.
        forms = [at for at, one in enumerate(said) if one == word or one == word + "s"]
        if forms or (" " in word and word in flat):
            # A line that also names a song or a tune is asking about the music even when it
            # says "my keys" first: "wheres my keys and what key is this song in" is two
            # questions and the music row answers one of them.
            elsewhere = [one for one in _A_MUSIC_WORD if one not in (word, word + "s")]
            if word in _A_THING_OF_THEIRS and any(
                    _somebodys_own_thing(said, at) for at in forms) and not any(
                        one in said or one in flat for one in elsewhere):
                return False
            if word in _NEEDS_A_MUSIC_WORD and not any(
                    one in said or one in flat for one in _A_MUSIC_WORD):
                return False
            return not any(one in said or one in flat
                           for one in _MUSIC_ELSEWHERE.get(word, ()))
    return True


def _music_term(memory, understood):
    said = [str(word).lower() for word in (understood.get("words") or ())]
    flat = " ".join(said)
    # the longest name first: "time signature" before a bare word, "bpm" before "tempo"
    for word in sorted(MUSIC_TERMS, key=len, reverse=True):
        if word in said or (" " in word and word in flat):
            beside = _MUSIC_WORD_BESIDE.get(word)
            if beside and not any(one in said or one in flat for one in beside):
                continue
            return MUSIC_TERMS[word]
    return ("A chord is three or more notes together, the key is the home note a song keeps "
            "returning to, and an octave is the same note higher or lower. The time signature "
            "says how many beats are in a bar. Ask about one and I'll give you its answer.")


# The words that need the music beside them get their own row, so a film question never lands
# on the studio answer (and never on the glossary list either).
_MUSIC_TERM_KEY = tuple(word for word in MUSIC_TERMS if word not in _MUSIC_WORD_BESIDE)

ENTRIES.append(entry("music-term", (_MUSIC_TERM_KEY + ("music theory",), _MUSIC_ASKS),
                     _music_term,
                     avoid=("podcast", "podcasts", "recommend", "should i listen",
                            "what should i listen", "playlist", "spotify",
                            # "what scales should i learn on guitar" asks how to practise, not
                            # what a scale is, and the glossary answered it with three definitions
                            "practise", "practice", "learn to play", "should i learn",
                            "how do i get better") + _MUSIC_GEAR,
                     ask=_MUSIC_ASKS,
                     # the sales pitch, the front door key and harmony at home are other questions
                     guard=_music_elsewhere))

ENTRIES.append(entry("music-producer", (("producer", "producers", "music producer"),
                                        _MUSIC_WORD_BESIDE["producer"] + ("do", "does", "did")),
                     MUSIC_TERMS["producer"],
                     # the two names have to be the same thing: a film producer is a film job
                     avoid=("film producer", "film", "films", "movie", "movies", "tv",
                            "television", "documentary")))

# "what is a bridge in a song" was the album list, and "a bridge" alone is a card game, a dental
# job and a river crossing as well, so the song beside it is part of the key.
def _a_bridge_in_music(understood):
    """"what is a bridge" on its own is a river crossing, a card game or a dental job.

    The row's second pair of words was meant to hold it back, and it did not: a one-word key
    clears the threshold on its own, so the bare question came back as the section of a song.
    The music word has to be somewhere in the line for this row to answer.
    """
    clean = understood.get("clean")
    if not isinstance(clean, str):
        return False
    low = " " + clean.lower() + " "
    return any(" %s " % word in low or low.strip().startswith(word + " ")
               for word in ("song", "songs", "chorus", "verse", "music", "musical", "track",
                            "tune", "album", "band", "bridge of the song", "in the song"))


ENTRIES.append(entry("song-bridge", (("bridge",), ("song", "songs", "chorus", "verse", "music",
                                                  "track", "tune")),
                     "A bridge is the section that comes once, usually after the second chorus, "
                     "and sounds like neither the verse nor the chorus - it is there to stop the "
                     "song repeating itself before the last chorus, and it often changes key or "
                     "drops to a quiet moment first.",
                     guard=_a_bridge_in_music))

# How many strings, or keys, the thing has. "how many strings on a violin" was a search hedge
# while the instrument rows answered tuning and practice: the count is its own question.
_INSTRUMENT_COUNTS = {
    "violin": "A violin has four strings, tuned G, D, A and E from the lowest up.",
    "fiddle": "A fiddle is a violin, so four strings: G, D, A and E from the lowest up.",
    "viola": "A viola has four strings, C, G, D and A - a fifth lower than a violin.",
    "cello": "A cello has four strings, C, G, D and A, an octave below a viola.",
    "double bass": "A double bass has four strings, E, A, D and G, and some have a fifth.",
    "bass": "A bass guitar has four strings, E, A, D and G - the same notes as the bottom four "
            "of a guitar, an octave lower.",
    "guitar": "A guitar has six strings, E, A, D, G, B and E from the thickest up. A 12-string "
              "guitar has twelve, in six pairs.",
    "ukulele": "A ukulele has four strings, G, C, E and A.",
    "banjo": "A five-string banjo has five, with the short fifth string partway up the neck.",
    "mandolin": "A mandolin has eight strings in four pairs, tuned like a violin: G, D, A, E.",
    "piano": "A piano has 88 keys: 52 white and 36 black, seven and a bit octaves from A0 to C8.",
    "keyboard": "A full-size piano keyboard has 88 keys; a smaller synth or starter keyboard "
                "usually has 61 or 49.",
    "harp": "A concert harp has 47 strings, six and a half octaves.",
}
_COUNT_ASKS = ("how many", "number of", "how much", "count")


def _instrument_count(memory, understood):
    said = [str(word).lower() for word in (understood.get("words") or ())]
    flat = " ".join(said)
    for name in sorted(_INSTRUMENT_COUNTS, key=len, reverse=True):
        if name in said or name in flat:
            return _INSTRUMENT_COUNTS[name]
    return ("A guitar has six strings, a violin four, a bass four and a piano 88 keys. Ask me "
            "about the one you have and I'll tell you the count and the tuning.")


# Practising an instrument is its own job: "how do i practise piano", "how do i practice scales"
# and "how do i get better at guitar" were all a shrug, and "how do i learn to read music" got the
# card for a child reading aloud (its key holds the phrase "learn to read").
_PRACTICE_INSTRUMENTS = ("piano", "guitar", "violin", "cello", "viola", "double bass",
                         "bass guitar", "drums", "drum kit", "flute", "clarinet", "saxophone",
                         "sax", "trumpet", "trombone", "keyboard", "ukulele", "banjo",
                         "mandolin", "harp", "oboe", "bassoon", "recorder", "harmonica",
                         "instrument", "instruments", "music", "scales", "metronome",
                         "sheet music", "strumming", "picking", "fingerpicking",
                         "chord changes", "barre chord", "barre chords", "sight reading")

_PRACTICE_ASKS = ("practise", "practice", "practising", "practicing", "get better",
                  "better at", "improve", "how long should i practise", "how often should i practise",
                  "how long should i practice", "how often should i practice",
                  "what scales", "which scales", "scales to learn", "routine", "warm up",
                  "warm-up", "learn to read music", "read music", "reading music",
                  "sight read", "sight-read", "sight reading")

_PRACTICE_READ_MUSIC = ("Start with the rhythm, not the notes: clap a line of the music while a "
                        "metronome clicks, because the note names are the easy half. Then learn "
                        "the five lines of the treble staff with a mnemonic you make up, ten "
                        "minutes a day, and read one new short piece slowly each day rather than "
                        "the same one until it is perfect - reading is the skill of playing what "
                        "you have not seen before.")

_PRACTICE_CORE = ("Fifteen to twenty minutes a day beats two hours on Sunday, and start with the "
                  "hardest four bars rather than the beginning: play them slowly enough to get "
                  "them right, four times in a row, then put them back in the piece. Use a "
                  "metronome at a speed you can play cleanly and nudge it up two beats a minute, "
                  "because sloppy and fast teaches sloppy. Scales and one technical exercise "
                  "first warm the hands up, and finish on something you enjoy so you want to come "
                  "back tomorrow.")


_READ_MUSIC_WORDS = ("read music", "reading music", "sight read", "sight-read",
                     "sight reading", "learn to read", "sheet music")


def _music_practice(memory, understood):
    said = " ".join(str(word).lower() for word in (understood.get("words") or ()))
    if any(word in said for word in _READ_MUSIC_WORDS):
        return _PRACTICE_READ_MUSIC + " " + _PRACTICE_CORE
    return _PRACTICE_CORE


ENTRIES.append(entry("instrument-count", (tuple(_INSTRUMENT_COUNTS), _COUNT_ASKS),
                     _instrument_count,
                     ask=_COUNT_ASKS,
                     # "how much are violin lessons" is a price question, not a count of the
                     # strings, and the count card answered it with four strings
                     avoid=("lesson", "lessons", "teacher", "cost", "price", "expensive",
                            "cheap", "buy", "hire", "rent", "worth", "learn",
                            # how many are in an orchestra is a different count
                            "orchestra", "orchestras", "band", "choir", "ensemble")))


# --- a kite is not a fly ------------------------------------------------------
# home.py's fruit-flies row keys on the bare noun "fly", so "how do i fly a kite" was answered
# with cider vinegar in a glass and "what is a good first kite for a child" reached nothing.
# The fly row names a kite in its own avoid, and these two rows own the kite lines.
ENTRIES.append(entry(
    "fly-a-kite",
    (("kite", "kites", "kite flying"), ("fly", "flying", "how do i", "how to", "launch",
                                        "get it up", "wont go up", "won't go up", "keep it up",
                                        "wont stay up", "wind", "first time", "stuck",
                                        "up in the air", "get up", "goes up", "air")),
    "Fly it in open ground away from trees and power lines, with the wind at your back. Let out "
    "ten or fifteen metres of line, have someone hold the kite up and walk back until the line is "
    "tight, then pull gently and let line run through your hands as it climbs. A steady 8-20 mph "
    "is the sweet spot: if it loops and dives, let out line, and if it will not rise at all, wait "
    "for more wind rather than running.",
    # a book title is not a how-to, and a kite-mark is a mark on a plug
    avoid=("kite runner", "book", "novel", "film", "movie", "author", "kite mark",
           "kite-mark", "kite marked", "kite-marked")))
ENTRIES.append(entry(
    "first-kite",
    (("kite", "kites"), ("buy", "buying", "first", "for a child", "for my son", "for my daughter",
                         "for a 5 year old", "for a 6 year old", "for a 7 year old",
                         "recommend", "which", "best", "beginner", "easy", "present")),
    "A diamond or a delta, about 1.2 to 1.5 metres across, is the usual first kite: it launches "
    "easily, flies in light wind and costs about fifteen to twenty-five pounds. Look for one "
    "with a long tail (it steadies the flight for a child) and a line of at least 30 metres on a "
    "winder. Skip the stunt kites and the two-line ones: they need more wind and a lot more "
    "practice. A cheap supermarket delta is fine to learn on - you can spend more when they ask "
    "for a second one.",
    avoid=("kite runner", "book", "novel", "film", "movie", "author", "kite mark",
           "kite-mark", "kite marked", "kite-marked"),
    bias=1))


# A genre word with no shelf of its own leaves a film ask echoing the line back, and the length
# table stands down for a genre it does not know. A war film is the gap people ask about most, and
# the answer is a shelf: short first, the battle never required.
ENTRIES.append(entry("film-war", (("war", "wartime"),
                                  ("film", "films", "movie", "movies", "watch", "watching",
                                   "recommend", "suggest", "suggestion", "good", "best",
                                   "something", "tonight")),
                     ("*Paths of Glory* is the one to start with: Kubrick, the WWI trenches, 88 "
                      "minutes. *Went the Day Well?* (92 minutes) is a British village invasion "
                      "story from 1942, and *Journey's End* (107 minutes) stays in one dugout and "
                      "never shows the battle. All three fit inside two hours, and *Full Metal "
                      "Jacket* is 116 if you want the training half too."),
                     bias=2, guard=_the_subject_is_wanted,
                     avoid=WATCHING + CHILD + SPORT + SCREEN_TIME + NOT_WATCHING +
                           ("board game", "computer game", "video game", "toy", "poppy",
                            "memorial", "war on", "war on drugs", "war on obesity")))
# The name of a film, a song or a book that has slipped is not a memory question about people, and
# it is not a reading question either. On main `i cant remember the name of that film` was answered
# with "Use the name out loud in the first minute - 'Nice to meet you, Sarah'" (the card for
# remembering somebody's name as you are introduced), `i cant remember what that film was called`
# with the note-taking card, and `i forgot the name of that show` with the science of forgetting.
# What the person wants is the name back, and the way to get it is to describe the thing well
# enough for a search or a forum to recognise it.
ENTRIES.append(entry(
    "cant-recall-the-name",
    (("remember", "forgot", "forget", "forgotten", "forgetting", "recall", "cant think",
      "can't think", "think of", "thinking of", "name", "named", "called", "what was that",
      "whats that", "what's that", "which was that", "half remember", "half-remember"),
     ("film", "films", "movie", "movies", "song", "songs", "tune", "album", "band", "book",
      "books", "novel", "show", "shows", "series", "programme", "program", "episode",
      "actor", "actress", "documentary", "cartoon", "title", "sitcom", "podcast")),
    ("Describe it to a search instead of reaching for the name: the year, one scene you are "
     "sure of, an actor's face. \"film where a boy finds a whale, 90s\" finds it, and IMDb's "
     "advanced plot search takes one detail at a time.",
     # Both ways say the same first thing, because it is the answer: describe it well enough for
     # somebody else to recognise. The tongue is not a memory that failed - the name comes back
     # when the chasing stops - so the second way gives that, and the tool for each medium.
     "Say what you do remember out loud - a scene, a voice, where you were when you saw it - and "
     "put that into a search or a forum; somebody always knows it. The name usually surfaces once "
     "you stop chasing it, and running the alphabet for the first letter shakes it loose. For a "
     "song, hum it into a song-finder app; for a book, the cover colour and the shop are as good "
     "as the title."),
    ask=("remember", "forgot", "forget", "recall", "cant think", "can't think", "think of",
         "name", "called", "what", "which", "half"),
    # A name for a baby, a pet, a company or a team is a naming question with an answer, not a
    # lost title: those rows own it. "The name of that film" is this row, so nothing bare here
    # may be a word the other rows need.
    avoid=("baby", "babies", "puppy", "kitten", "dog", "cat", "company", "business", "domain",
           "website", "username", "password", "team", "band name", "middle name", "surname",
           "first name", "nickname", "pet", "boat", "house name", "wifi", "recommend",
           "recommendation", "what should i watch", "what should i read", "watch tonight",
           "read next", "something to watch", "something to read")))

# The strings themselves: "my guitar strings keep breaking" was an empty nod, and "how often
# should i change guitar strings" was a shrug, because the tuning row asked about tuning and the
# count row about how many. This one asks about the wire.
ENTRIES.append(entry("instrument-strings", (("string", "strings", "guitar string",
                                             "guitar strings", "bass string", "bass strings",
                                             "violin string", "violin strings"),
                                            ("breaking", "break", "breaks", "broke", "snapped",
                                             "snap", "snapping", "change", "changed", "replace",
                                             "how often", "how long", "rusty", "corroded", "dull",
                                             "dead", "dirty", "old")),
                     "Change them every one to three months of near-daily playing, or when they "
                     "look dull or rusty and go out of tune within minutes - a set is six to ten "
                     "pounds. A string that keeps breaking at the same place means a sharp edge on "
                     "the saddle or the nut, or a burr in the tuning peg, so run a fingernail along "
                     "each and file any catch smooth. Change one at a time so the neck keeps its "
                     "tension, and stretch each new string by pulling it gently away from the "
                     "board before you tune it up.",
                     # no ask: the fault word is in the key already, and a statement of it
                     # ("my violin string snapped") is the question
                     # tuning, the count of them and an orchestra's strings are other questions
                     avoid=("tune", "tuning", "tuner", "in tune", "out of tune", "stay in tune",
                            "buzz", "buzzing", "fret buzz", "how many", "count", "number of",
                            "orchestra", "orchestras", "string section", "piece of string",
                            "on a string", "no strings",
                            # a string that has just gone is the repair card's line, and it is
                            # the better answer: it says what to do with the loose end now.
                            # This row is the "how often" question, so it stands down for it.
                            "snapped", "snap", "snaps", "snapping", "broke", "broken",
                            "breaking", "breaks", "keep breaking", "keeps breaking",
                            "keep snapping", "keeps snapping", "bust")))


# Practising: "how do i practise piano" and "how do i practice scales" were a shrug each. The
# instrument has to be in the line, so a bare "how long should i practise" stays with whoever
# else can answer it.
ENTRIES.append(entry("music-practice", (_PRACTICE_INSTRUMENTS, _PRACTICE_ASKS), _music_practice,
                     ask=("practise", "practice", "get better", "improve", "how long", "how often",
                          "scales", "read music"),
                     # a lesson, a teacher, the price of an instrument, tuning it and the count of
                     # its strings are other questions with their own rows
                     avoid=("lesson", "lessons", "teacher", "tutor", "cost", "price", "expensive",
                            "cheap", "free", "buy", "hire", "rent", "worth",
                            "which instrument", "guitar or piano", "piano or guitar",
                            "learn guitar", "learn piano", "learn to play",
                            "tune", "tuning", "tuner", "in tune", "out of tune", "stay in tune",
                            "buzz", "buzzing", "string", "strings", "restring",
                            "singing", "sing", "voice", "choir", "how many", "count",
                            # taste and what to listen to is the recommendation row's job
                            "taste", "recommend", "playlist", "listen", "spotify",
                            "what should i listen",
                            # "what scales are there" asks what a scale is, not how to practise
                            "what scales are there", "which scales are there",
                            "what are the scales", "how many scales")))

# --- a podcast about a subject -----------------------------------------------------------
# "a podcast about science", "a podcast about food", "a podcast about sleep" and nine more were
# a shrug, a "Got it", or the wrong medium's answer on main: the podcast rows key on the word
# podcast plus a mood (funny), a moment (a commute) or a subject with a row of its own (history,
# money, a language), so the subject in the middle of the line was read by nobody. One row per
# subject, keyed by the subject rather than the wording, and the shows are named because a
# recommendation that does not name one is not an answer.
_PODCAST_SUBJECTS = (
    ("science",
     ("science", "scientific", "physics", "chemistry", "biology", "space", "astronomy",
      "the universe", "nature", "wildlife", "animals", "climate", "climate change",
      "environment", "ecology", "engineering", "maths", "mathematics"),
     "For science with jokes: *The Infinite Monkey Cage*, a physicist and a comedian on one "
     "question in 45 minutes. *Science Vs* takes one claim an episode and weighs the evidence, "
     "and *Ologies* is a long friendly interview with a scientist each time. For space, *13 "
     "Minutes to the Moon* is the best thing made about Apollo."),
    ("food",
     ("food", "foods", "cooking", "cook", "chef", "chefs", "baking", "bake", "recipes",
      "recipe", "kitchen", "restaurants", "eating"),
     "*Home Cooking* (Samin Nosrat and Hrishikesh Hirway) answers listeners' kitchen questions "
     "and is the friendliest place to start. *The Sporkful* is about how and why people eat what "
     "they eat, and *Gastropod* takes one food an episode and does its history and science."),
    ("health",
     ("health", "healthy", "medicine", "medical", "doctor", "sleep", "insomnia", "fitness",
      "exercise", "running", "nutrition", "diet", "weight", "mental health", "anxiety",
      "stress", "wellbeing"),
     "For health with the evidence shown: *Zoe Science & Nutrition*, one food or habit an "
     "episode with a scientist and a doctor. For sleep, *Nothing Much Happens* reads quiet "
     "stories slowly and *Sleep With Me* rambles on purpose, both made to send you off rather "
     "than to be listened to."),
    ("sport",
     ("sport", "sports", "football", "cricket", "rugby", "tennis", "f1", "formula 1", "boxing",
      "golf", "athletics", "cycling", "match", "matches"),
     "For football, *Football Weekly* from the Guardian is twice a week, quick and funny, and "
     "*The Rest Is Football* is Lineker, Richards and Shearer talking. For cricket, *Tailenders* "
     "is the one people who do not like cricket listen to."),
    ("technology",
     ("tech", "technology", "technologies", "gadgets", "computer", "computers", "phone",
      "phones", "ai", "artificial intelligence", "internet", "software", "programming",
      "coding", "cyber", "hacking"),
     "*Hard Fork* (Kevin Roose and Casey Newton) is the weekly one on what the tech companies "
     "just did, and it is funny. *Darknet Diaries* is true stories of hacks and the people who "
     "did them, and *The Vergecast* is the long argument about gadgets."),
    ("news",
     # business, finance and economics are the business row's: two rows keyed on "business"
     # meant whichever came first answered it, and "a podcast about business" got the news one.
     ("news", "politics", "political", "current affairs", "world", "election", "elections",
      "government"),
     "*The Daily* takes one story a day and reports it properly in 20 minutes, *Today in Focus* "
     "does the same from a British side, and *The Briefing Room* explains one running story with "
     "the people who know it. For business, *The Bottom Line* puts three chief executives in a "
     "room and asks them the same question."),
    ("people",
     ("psychology", "psychologist", "human behaviour", "human behavior", "behaviour", "behavior",
      "relationships", "relationship", "feelings", "emotions", "people", "mindfulness",
      "meditation", "habits"),
     "*Hidden Brain* is the one to start with: one piece of psychology an episode, told as a "
     "story. *The Happiness Lab* is the research on what actually makes people happier, and "
     "*Where Should We Begin?* is Esther Perel with one real couple in a single session."),
    ("parenting",
     ("parenting", "parent", "parents", "babies", "baby", "newborn", "toddler", "kids",
      "children", "family", "families", "motherhood", "fatherhood"),
     "*Parenting Hell* (Rob Beckett and Josh Widdicombe) is two fathers being honest about how "
     "badly it is going, which is the most reassuring thing on the subject. *Happy Mum Happy "
     "Baby* is the calmer interview version, one parent an episode."),
    ("music",
     ("music", "songs", "song", "albums", "album", "bands", "band", "guitar", "singing"),
     "*Song Exploder* takes one song and has the person who made it pull it apart, track by "
     "track, in 20 minutes. *Desert Island Discs* is the long interview with the music choices in "
     "it, and *All Songs Considered* is the weekly new-music one."),
    ("business",
     ("business", "businesses", "company", "companies", "startup", "startups", "start a business",
      "starting a business", "entrepreneur", "entrepreneurs", "selling", "sales", "marketing",
      "the economy", "economy", "economics", "finance", "financial"),
     "*How I Built This* has the founder of one company telling how it actually started, in an "
     "hour, and it is the most useful one if you are thinking of starting something. *The Bottom "
     "Line* puts three bosses in a room and asks them the same question, and *StartUp* follows "
     "one company from the first day, mistakes included."),
    ("gardening",
     ("garden", "gardening", "gardens", "allotment", "allotments", "vegetables", "plants",
      "lawn", "grow your own"),
     "*Gardeners' Question Time* is the one to start with: three experts answering listeners' "
     "questions, so you get the answer to the thing you were wondering about. *Talking Gardens* "
     "is the interview version and *The RHS Podcast* the seasonal jobs."),
    ("film",
     ("film", "films", "movie", "movies", "cinema", "tv", "television", "series", "telly"),
     "*The Rewatchables* is one film an episode and why it still works, which is the best "
     "listen for someone who likes films. *Kermode & Mayo's Take* reviews what is out now, and "
     "*You Must Remember This* tells the old Hollywood stories properly."),
)

# a podcast to put on for a child is not a podcast about children: "what podcasts are good for
# kids" is the one ask here that names the listener rather than the subject, and it has its own
# shows. Both rows that would read "kids" as their subject stand down on these words.
_PODCAST_FOR_KIDS = (
    "for kids", "for children", "for a child", "for my kids", "for my children", "for my son",
    "for my daughter", "with my kids", "with my children", "kids podcast", "kids podcasts",
    "podcast for kids", "podcasts for kids", "childrens podcast", "children's podcast",
    "child friendly", "family friendly", "my 5 year old", "my 6 year old", "my 7 year old",
    "my 8 year old", "a childrens", "a kids",
    # the age is how a parent names the listener: "a podcast for a 6 year old"
    "for a 4 year old", "for a 5 year old", "for a 6 year old", "for a 7 year old",
    "for an 8 year old", "for a 9 year old", "for a 10 year old",
    "4 year old", "5 year old", "6 year old", "7 year old")

_PODCAST_NOT_THIS = {"parenting": _PODCAST_FOR_KIDS, "people": _PODCAST_FOR_KIDS,
                     "science": _PODCAST_FOR_KIDS, "film": _PODCAST_FOR_KIDS}

ENTRIES.append(entry(
    "podcast-for-kids",
    (("podcast", "podcasts", "listen", "listening"), _PODCAST_FOR_KIDS),
    "*Wow in the World* is the best one to start with: science stories with two silly hosts, made "
    "for 5 to 8 year olds. *Story Pirates* turns stories children send in into sketches and songs, "
    "and *Circle Round* tells a folk tale in fifteen minutes with a proper cast. *But Why* answers "
    "the questions children actually ask, and *Smash Boom Best* is two things argued over by "
    "comedians with your child as the judge.",
    bias=3))

# The loop names are prefixed on purpose: this file already has a `_subject(clean)` that reads the
# thing a verse is about, and a bare `for _subject, ... in` here rebound it to a string at import
# time, so every creative ask after this line died with "'str' object is not callable".
for _podcast_subject, _podcast_words, _podcast_reply in _PODCAST_SUBJECTS:
    ENTRIES.append(entry(
        "podcast-" + _podcast_subject,
        (("podcast", "podcasts"), _podcast_words),
        _podcast_reply,
        # a book, a film or a series is another medium's ask, whatever subject it shares
        avoid=("book", "books", "novel", "novels", "read", "reading", "audiobook", "audiobooks",
               "recipe", "recipes to", "tonight", "watch")
               + _PODCAST_NOT_THIS.get(_podcast_subject, ()),
        bias=2))
# --- which game to play ---------------------------------------------------------------
# "recommend a board game", "any good video games", "what game should i play" and "what should i
# play on my switch" are among the commonest asks about an evening, and every one of them was a
# shrug or the party-games card ("Twenty questions: one person thinks of a person"): the rows for
# a group, for two people, for children and for short rules all need the company in the line, and
# a plain ask for a game names none of them. The kind of game is the key, the ask is the second
# half, and the shape of the answer is what the line says about it - a platform, a mood, or a
# second player.
GAME_KINDS = ("game", "games", "board game", "board games", "video game", "video games",
              "computer game", "computer games", "console", "playstation", "ps4", "ps5", "xbox",
              "nintendo", "steam", "puzzle game", "puzzle games", "co-op", "coop", "co op",
              "switch game", "switch games", "on my switch", "on the switch")
# "switch" on its own is the everyday verb - "how do i switch off in the evening" was handed
# *Animal Crossing* - so the console is only named with the word "game" beside it. The bare verbs
# "play" and "playing" are out for the same reason: they are a guitar, a school play and the
# cinema ("whats playing at the cinema tonight"), and every one of those got *Hades*.
GAME_ASKS = ("recommend", "recommended", "recommendation", "recommendations", "suggest",
             "suggestion", "suggestions", "what should i", "what can i", "what to", "which",
             "any good", "any decent", "good", "best", "worth", "new", "next", "start",
             "beginner", "i need", "i want", "to play", "should i play", "buy",
             "getting", "something", "any", "new", "tonight", "evening", "weekend",
             "for a while", "to fill", "can i", "should i",
             # the mood or the shape asked for is the ask itself: "any calm games", "a short
             # game to play tonight", "a game to play when im stressed"
             "calm", "relax", "relaxing", "chill", "stressed", "anxious", "short", "quick",
             "story", "co-op", "coop", "co op", "puzzle", "puzzles", "two of us", "together",
             # "a game for me and my wife" is a game for two however it is put
             "me and my", "for the two", "for two",
             # A bare genre is the whole question when it is the whole line: "board games",
             # "puzzle games", "co-op games" with nothing else in it. The kind word names the
             # subject, so a line that only says the kind also has to reach here.
             "board games", "board game", "puzzle games", "co-op games", "coop games",
             "co op games", "video games", "switch games", "card games", "two player games")
# Everything that only sounds like a game: a game of football, a game show, a gambling game, the
# games people play with each other, a TV series with "game" in its name, and the party, group,
# two-player, children's and short-rules rows that already answer their own lines.
NOT_A_GAME_PICK = ("football", "soccer", "rugby", "cricket", "tennis", "badminton", "netball",
                   "basketball", "hockey", "golf", "darts", "snooker", "sport", "sports",
                   "match", "matches", "league", "team", "played for", "cup final",
                   "bet", "betting", "gamble", "gambling", "casino", "poker", "roulette",
                   "lottery", "scratchcard", "odds", "winnings",
                   "hunting", "game pie", "venison", "pheasant", "rabbit", "deer",
                   "party", "parties", "friends", "group", "grown ups", "kids", "children",
                   "toddler", "family", "two", "couple", "partner", "chess", "rules", "long",
                   "easy to learn", "simple", "parental", "controls", "restrict", "limit",
                   "addicted", "addiction", "screen time", "hours", "set up", "safely",
                   "how much", "price", "cost", "expensive", "cheap", "thrones", "squid game",
                   "mind games", "playing games", "game plan", "the game is",
                   "wedding", "funeral", "playlist", "music", "song", "songs", "radio",
                   # the Co-op is also the shop: a line about the place being open, shut or
                   # bought from is a venue question, whatever genre its name spells
                   "opening", "opens", "opened", "open on", "open today", "open till",
                   "closed", "closes", "closing", "shut", "shuts", "shutting", "what time",
                   "shop", "shops", "store", "supermarket", "aisle", "aisles", "checkout",
                   "meal deal", "sandwich", "milk", "bread", "receipt", "parking",
                   "nearest", "near me", "closest", "postcode", "address", "directions",
                   "whats the address", "which one is",
                   # a job or a shift at the branch is about the place, not about a game
                   "job", "jobs", "work at", "works at", "working at", "shift", "shifts",
                   "the guitar", "piano", "instrument", "character", "part in",
                   # a game for a child is the kids row's, and a list of video games is the
                   # wrong answer to "what can i play with my son who is 6"
                   "my son", "my daughter", "my kid", "my kids", "my child", "my children",
                   "year old", "toddler", "grandson", "granddaughter", "niece", "nephew",
                   "nursery", "birthday", "five a side", "five-a-side", "five aside",
                   "switch off", "switch on", "switching off", "jigsaw", "jigsaw puzzle",
                   # a title with "games" in it, and the two things "play" belongs to
                   "hunger games", "guitar", "piano", "drums", "cinema", "whats playing",
                   "what's playing", "school play",
                   # a console bought rather than a game played: "is it worth getting a console
                   # or a pc for gaming" is a buying question, and its own row answers it
                   "worth getting", "worth buying", "console or", "pc or", "gaming pc",
                   "which console", "or a pc", "or console",
                   # a record question is a fact, not a request for a pick: "what is the best
                   # selling video game" and "which video game sold the most" were both given
                   # *Hades* and *Stardew Valley*, because "best" is in the ask list
                   "sell", "sells", "sold", "selling", "bestseller", "best seller",
                   "best selling", "best-selling", "top selling", "copies sold", "units sold",
                   # a game at a gathering is the party rows' line, and the occasion alone says
                   # so: "any games at christmas" and "games for new year" were both handed
                   # *Hades*, which nobody plays with the family round a table
                   "at christmas", "on christmas", "christmas day", "christmas eve",
                   "for christmas", "over christmas", "xmas eve", "at new year",
                   "for new year", "new years eve", "new year's eve", "on new years eve",
                   # an opinion about games is not a request for one: "video games make you
                   # violent" was handed *Hades* once the word "games" counted as the ask
                   "make you", "makes you", "making you", "make people", "makes people",
                   "violent", "violence", "bad for you", "bad for kids", "rot your",
                   "are addictive", "too much screen", "ruin",
                   # a game bought as a present is the gift row's line: "recommend a game as a
                   # christmas present" got *Hades* while main gave the how-to-choose-a-gift card
                   "present", "presents", "gift", "gifts", "stocking filler", "stocking fillers",
                   "secret santa")
# The platform or the mood a line names, and the pick each one gets.
GAME_PICKS = (
    (("switch", "nintendo", "mario"),
     "On a Switch: *Animal Crossing: New Horizons* to wind down, *Mario Kart 8 Deluxe* for "
     "people in the room, and *The Legend of Zelda: Breath of the Wild* for a big adventure."),
    (("xbox", "playstation", "ps4", "ps5", "console", "big screen"),
     "On a console: *Hades* for short, fast runs, *The Last of Us* if you want a story to sit "
     "through, and *Elden Ring* if you want a huge, hard world. *Hades* is the one I'd start "
     "with."),
    (("pc", "steam", "laptop", "computer"),
     "On a PC: *Stardew Valley* for something calm that never ends, *Portal 2* for puzzles, and "
     "*Disco Elysium* if you want to read as much as you play. *Stardew Valley* is the easy "
     "pick."),
    (("puzzle", "puzzles", "brain", "think"),
     "For puzzles: *Portal* (short, funny, brilliant), *The Witness* if you want to be stuck "
     "properly, or *Baba Is You* for something unlike anything else. *Monument Valley* on a "
     "phone if you only have ten minutes."),
    (("co-op", "coop", "co op", "girlfriend", "boyfriend", "wife", "husband", "together",
      "with my other half"),
     "For two of you: *It Takes Two* is built for exactly that, *Overcooked 2* if you want to "
     "shout at each other and laugh, and *Portal 2* for puzzles you solve as a pair. *It Takes "
     "Two* first."),
    (("calm", "relax", "relaxing", "cosy", "cozy", "chill", "stressed", "wind down", "anxious"),
     "*Stardew Valley* is the one for that: farm, fish, befriend the village, nothing is timed "
     "against you. *Animal Crossing* on a phone or a Switch, or *Unpacking* if you want "
     "something short and gentle."),
    (("story", "narrative", "plot", "emotional", "sad", "cry", "film like", "like a film"),
     "For a story: *The Last of Us* (grief and a road trip), *Red Dead Redemption 2* (a slow "
     "western with a lot of heart), or *Disco Elysium* if you would rather read. *The Last of "
     "Us* is the one people finish and then sit still for a while."),
    (("short", "quick", "evening", "few hours", "one sitting"),
     "Short ones: *Unpacking* (about three hours, and it says more than it sounds like it "
     "would), *Portal* (also about three), or *Firewatch* (an evening, and it stays with you)."),
    (("board", "boardgame", "boardgames", "tabletop", "card game", "cards"),
     "On a table: *Ticket to Ride* (trains, simple, satisfying), *Codenames* (two teams, one "
     "word grid) and *Azul* (tiles, quick, sharp). *Ticket to Ride* is the safest box for a "
     "household."),
)


def _not_a_crowd(understood):
    """False when the conversation the line sits in is a party, friends over, or a child.

    "any games" on its own is a request for a game to play, but three deck chats send it at the
    end of one about a birthday party ("im planning a kids party" / "any games"), and a real chat
    sends it after "weve got friends over saturday" / "five of us". A short line carries almost
    none of that: the standing topic says family-and-parenting or friends-and-relationships for
    those chats and entertainment for a bare "any games", and when the topic does not say it, the
    line the question leans on still names the crowd. Those turns belong to the party, group and
    children's rows, which answer them with games for the people in the room.
    """
    if str(understood.get("topic") or "") == "family-and-parenting":
        return False
    leaning = understood.get("leans_on") or {}
    if isinstance(leaning, dict):
        words = [str(word).lower() for word in (leaning.get("words") or ())]
        words.append(str(leaning.get("subject") or "").lower())
        words.append(str(leaning.get("text") or "").lower())
        flat = " ".join(words)
        if any(word in flat for word in _A_CROWD):
            return False
    return True


# The words that mean there are other people in the room, or a child in the house.
_A_CROWD = ("kids", "kid", "child", "children", "toddler", "boy", "girl", "son",
            "daughter", "grandchild", "party", "friends", "friend", "group", "family",
            "guests", "cousins", "nieces", "nephews", "playdate", "birthday")


# A child named in the chat, which the line asking for a game often only hints at.
_CHILD_WORDS = ("my son", "my daughter", "my boy", "my girl", "my kid", "my kids",
                "my child", "my children", "toddler", "grandson", "granddaughter",
                "with the kids", "with my kids", "playdate")


def _a_child_in_the_chat(memory):
    """True when a child has been named in this conversation, and not as a teenager.

    "my boy is 9 and into dinosaurs" / "what should we do at the weekend" / "any games" wants
    *Dobble* and a treasure hunt, not *Hades*: a game for a grown-up alone is the wrong pick for a
    nine year old, and the line that named the child is two turns back.
    """
    for said in (memory.get("turns") or ())[-8:]:
        words = str((said or {}).get("user") or "").lower()
        if not words or not any(word in words for word in _CHILD_WORDS):
            continue
        ages = [int(age) for age in re.findall(r"\b(\d{1,2})\s*(?:years? old|year old|yo)\b",
                                               words)]
        if ages and min(ages) >= 13:
            continue
        return True
    return False


def _the_game_pick(memory, reading):
    """A game for what the line says about it: a platform, a mood, or someone to play with."""
    from .kept_animals import keeping_an_animal
    if keeping_an_animal(reading):
        # "do i need a coop for chickens" is a hen house, not a co-op game: a word that is also a
        # keeper's word belongs to the keeper's line, and that row answers it.
        return ""
    line = "%s %s" % (reading.get("clean") or "", reading.get("norm_text") or "")
    line = line.lower()
    if _a_child_in_the_chat(memory):
        return ("*Dobble*, *UNO* and *Jenga* work from about five up, and *Catan Junior* if they "
                "are ready for a proper board game. A treasure hunt round the house costs "
                "nothing and takes the longest.")
    for words, said in GAME_PICKS:
        if any(word in line for word in words):
            return said
    return ("*Hades* is the one I'd hand you first: fast, short runs, and it never wastes your "
            "time. *Stardew Valley* if you want calm, and *The Last of Us* if you want a story "
            "to sit through.")


# The titles a person asks *about* rather than for. "is monopoly a good game" and "is catan any
# good" name the game they already have in mind, so a list of other picks is no answer to either.
NAMED_GAME_TITLES = ("monopoly", "catan", "settlers", "scrabble", "cluedo", "clue", "uno",
                     "risk", "ticket to ride", "azul", "codenames", "dixit", "carcassonne",
                     "pandemic", "boggle", "rummikub", "draughts", "checkers", "chess",
                     "minecraft", "fortnite", "roblox", "zelda", "mario", "animal crossing",
                     "hades", "stardew", "among us", "fifa", "call of duty")

# The shape that asks what a game one already has is like, rather than which one to get.
GAME_JUDGED = ("is it any good", "good game", "good games", "any good", "worth it",
               "worth playing", "worth buying", "what do you think of", "what's it like",
               "whats it like", "like it")


# A platform named together with a buying word is a hardware question, and a list of games to
# play is not an answer to it: "should i buy a ps5 or an xbox" was given "On a console: *Hades*
# for short, fast runs", and so were "ps5 vs xbox which is better", "should i get a nintendo
# switch or a steam deck", "whats the best console to buy", "is xbox game pass worth it", "is the
# xbox series s worth it" and "should i upgrade to a ps5". The platform is in the key of this row
# because "what should i play on my switch" is a pick, so the buying shape is what tells the two
# apart: a console named with no buying word is still a request for a game.
_PLATFORMS = ("console", "consoles", "xbox", "playstation", "ps4", "ps5", "switch",
              "nintendo", "steam deck", "steam", "pc", "gaming pc", "gaming laptop",
              "graphics card", "controller", "controllers", "handheld", "game pass",
              "series s", "series x", "vr headset", "meta quest")
# "buy a switch" is a machine and "buy a game for my switch" is a game, so the buying verb has to
# take the machine as its object: the article and the platform together, right after the verb.
_BUYING_THE_MACHINE = re.compile(
    r"\b(?:buy|buying|bought|get|getting|upgrade(?:d|s)?\s+to|upgrading\s+to|"
    r"should\s+i\s+(?:buy|get))\s+(?:a|an|the|another|a\s+new|the\s+new)?\s*"
    r"(?:%s)\b" % "|".join(re.escape(word) for word in _PLATFORMS))
# The rest of the hardware shapes carry their own buying or comparing sense with no verb to read.
_MACHINE_SHAPES = (" worth it", " is it worth", " worth buying", " worth getting", "price of",
                   "how much does", "how much is a", "how much are", " best console",
                   " which console", " cheapest console", " cheaper ", " vs ", " versus ",
                   " or a ", " or an ", " cost ")


def _a_hardware_decision(understood):
    """True when the line is about which machine to buy, not which game to play."""
    clean = " %s " % str(understood.get("clean") or "").lower().replace("-", " ")
    if not any(word in clean for word in _PLATFORMS):
        return False
    if _BUYING_THE_MACHINE.search(clean):
        return True
    return any(shape in clean for shape in _MACHINE_SHAPES)


def _a_game_pick_line(understood):
    """False when the line is not asking for a pick: a crowd, a named title, or a skill question.

    "what can i play on my own" was answered with loneliness advice, "is monopoly a good game"
    with *Hades* and *Stardew Valley*, and "how do i get better at video games" with the same
    pick list. None of the three is a request for a game to buy: the first names nobody to play
    with, the second is a question about a game the person already knows, and the third asks how
    to improve. All three stand down here so the row that answers them can.
    """
    if not _not_a_crowd(understood):
        return False
    if _a_hardware_decision(understood):
        return False
    clean = " %s " % str(understood.get("clean") or "").lower().replace("-", " ")
    if any(shape in clean for shape in (" get better at ", " get good at ",
                                        " how do i improve ", " how can i improve ")):
        return False
    judged = any(shape in clean for shape in GAME_JUDGED)
    if judged:
        for title in NAMED_GAME_TITLES:
            if re.search(r"(?<![a-z])%s(?![a-z])" % re.escape(title), clean):
                return False
    return True


# One person, no second player: the picks for a table are the wrong ones for a line that says
# nobody else is playing. "what can i play on my own" got loneliness advice and "what can i play
# by myself" the search hedge, so the phrase names the kind of game here as well as the console.
GAME_SOLO_WORDS = ("on my own", "by myself", "by my self", "alone", "solo", "single player",
                   "singleplayer", "on my tod", "no one to play with", "nobody to play with",
                   "no one else to play with", "nothing to do with no one")
GAME_SOLO_ASKS = ("game", "games", "play", "playing", "board game", "video game")


def _the_solo_game(memory, reading):
    """A game one person can play tonight."""
    if _a_child_in_the_chat(memory):
        return ("*Dobble* is fine with one player as a speed game, and *UNO* works solo if you "
                "play the house down. *Catan Junior* really needs two, though.")
    return ("*Stardew Valley* is the one: farm, fish, befriend the village, nothing timed against "
            "you, and it runs on almost anything. *Hades* if you want ten-minute runs with a "
            "fight in them, or *Unpacking* for an evening of something quiet.")


# The key alone is not the ask: "im 5 foot 6 and i play five a side" names playing and a game
# word, and a person telling you about their week does not want *Hades*. The ask has to be in the
# line as well, so a line that only mentions playing stands down.
ENTRIES.append(entry("game-picks", (GAME_KINDS, GAME_ASKS), _the_game_pick,
                     ask=GAME_ASKS, avoid=NOT_A_GAME_PICK, bias=2,
                     guard=_a_game_pick_line))
# Its own row, not a pick inside the one above: the solo phrase has to carry a game word as well,
# so "i live alone and the evenings are long" stays with the row that answers loneliness.
ENTRIES.append(entry("game-solo", (GAME_SOLO_WORDS, GAME_SOLO_ASKS), _the_solo_game,
                     avoid=NOT_A_GAME_PICK, bias=3))


# --- a phrase from a book review -----------------------------------------------------------
# "what is a page turner" was a search hedge while "a gripping book" was already answered: the
# word is a review's shorthand, so the answer says what it means and what to pick next.
ENTRIES.append(entry(
    "page-turner",
    (("page turner", "page turners", "pageturner", "page-turner", "page-turners",
      "unputdownable", "cant put it down book"),
     ("what is", "whats", "what does", "mean", "means", "recommend", "suggest", "which",
      "any", "good", "best", "book", "books", "novel", "read", "reading", "holiday")),
    "A page turner is a book whose plot pulls you through - short chapters, a question you want "
    "answered, a twist you did not see - rather than one you admire slowly. The shorthand comes "
    "from book reviews because it says nothing about quality: a thriller can be a page turner and "
    "so can a good memoir. If you want one, say what you last could not put down and I will find "
    "something in the same shape; if you want a specific book, tell me the kind of story rather "
    "than the word.",
    # a bookmark, a page number and a printer are other things with the word page in them
    avoid=("bookmark", "page number", "printer", "paper", "print", "browser", "website",
           "web page", "homepage", "kindle", "page count"),
    bias=1))
