"""The people and numbers in the news: who holds an office, who plays a part, how big a city is.

These are the questions whose answer is a name or a figure rather than a method, and nobody in the
tree answered them. Asked on main, every one of these got a shrug or a card about something else:

    who is the prime minister      -> "I'm not sure about that one, sorry"
    who is the king                -> the same
    who plays iron man             -> the same
    who plays harry potter         -> "Harry Potter is by JK Rowling" (the author's answer)
    who plays sherlock holmes      -> "Sherlock Holmes is by Arthur Conan Doyle" (the same)
    how many people live in manchester  -> "That's beyond what I know well"

So there are three tables here, and each is keyed by meaning rather than by wording: the office
(`uk-prime-minister`, `us-president`), the part (`plays-iron-man`, `plays-batman`), the city
(`population-london`, `population-paris`). The words that ask the question - "who", "plays", "how
many people" - are shared by every row in their table, so one row answers "who is the prime
minister", "who's the PM" and "is starmer still prime minister" without three keys.

Two things make this safe to have. **Dated facts are written as the appointment, not as "now".**
"Keir Starmer, in office since July 2024" stays true after the next election in a way that "the
current prime minister" does not; every reply that can change says when it started and, where it
is known, when it must change next. And **the neighbouring rows are held out.** A king on a
chessboard, a B&B, a burger, a lion and a prom are not the monarch; the vice president is not the
president; "who wrote Harry Potter" is the author's answer and this domain answers only the
playing of the part. Each `avoid` list is the specific letter-shaped line the entry would
otherwise take, and the bare words are kept out of them, because a bare `avoid` word vetoes the
whole row and has to be judged by the commonest line that contains it.

`ANSWERS` names the three topic ids these lines are read as, all of them ids another domain
already declares, so the union answers.py publishes does not change.
"""
from .lookup import entry

ANSWERS = ("entertainment", "geography-and-travel", "history")

ENTRIES = []


def _row(*args, **kwargs):
    """Keep one entry. `entry()` builds it and returns it; the domain needs the list."""
    ENTRIES.append(entry(*args, **kwargs))

# The words that ask who is in an office. They name the ask and no subject, so every office row
# shares them and the office word decides the answer.
WHO = ("who", "who's", "whos", "current", "still", "now", "today", "name", "is",
       "at the moment", "at the minute")

# The words that ask who plays a part. "plays" is what separates the actor's answer from the
# author's: the who-wrote row in entertainment.py keys on "who", and a line that says "plays" is
# asking about the screen, so these rows also carry a bias to win the tie with it.
# The words that ask who plays a part. They have to be the question and not the bare verb: this
# group sits in the key, and "play" on its own let two statements through as questions -
# "i play five a side on wednesday" was answered "Jenna Ortega plays Wednesday Addams in
# Wednesday (2022)", and "they play eleven a side in cricket" was answered with Eleven from
# Stranger Things. A key part is a flat OR, so a bare "play" is a subject, not an ask.
# "actor" and "actress" stay bare because a statement does not name one, and "film"/"series" are
# gone with "play": "my favourite film is batman" is not a who-plays question either.
CAST = ("who plays", "who play", "who played", "who's playing", "whos playing", "who is playing",
        "who was playing", "who starred", "who stars", "who voices", "who does the voice",
        "who was the voice", "the actor who", "the actor that", "actor who plays", "that plays",
        "which actor", "which actress", "name the actor", "tell me the actor", "the guy who plays",
        "the girl who plays", "the woman who plays", "the man who plays", "played by",
        "cast of", "the cast", "who was in", "who is in", "starring", "starred in",
        "actor", "actress")

# The countries a line can name instead of ours. An office question about another country is one
# this file cannot answer, and a confident wrong name is the worst reply the bot can give: "who is
# the prime minister of india" was answered "Keir Starmer is the prime minister". So every office
# row holds these out and the line falls back to the honest hedge it had before. The country and
# the word for its people are both here, because people write "the indian prime minister" as
# often as "the prime minister of india".
# Ours are deliberately absent: "uk", "britain", "england", "america" and "the states" are what
# make these rows answer at all. A country is not the office, so this tuple is only in an avoid.
OTHER_PLACES = tuple(
    "india indian china chinese japan japanese russia russian ukraine ukrainian france french "
    "germany german spain spanish italy italian portugal portuguese greece greek ireland irish "
    "canada canadian australia australian new zealand brazil brazilian mexico mexican "
    "south africa israel israeli iran iranian iraq syria syrian turkey turkish egypt egyptian "
    "saudi saudi arabia pakistan pakistani bangladesh nigeria kenya ghana netherlands dutch "
    "holland belgium belgian sweden swedish norway norwegian denmark danish finland finnish "
    "poland polish hungary austria austrian switzerland swiss argentina chile colombia peru "
    "cuba cuban indonesia philippines vietnam thailand thai malaysia singapore hong korea "
    "korean taiwan afghanistan lebanon palestine morocco ethiopia somalia sudan zimbabwe qatar "
    "dubai emirates czech romania bulgaria croatia serbia lithuania latvia estonia slovakia "
    "slovenia iceland luxembourg malta cyprus".split())
# "hong kong" was in this list and it stood the whole monarch row down: the slip reader reads a
# line word that is no key word and one edit from an avoid word as that avoid word, and "king" is
# one letter from "kong". A place whose name is a slip away from the office word cannot be a guard
# on that office. So the phrase is "hong" alone, and the same care is worth taking with any place
# added here: "chile" is one edit from "chime", "peru" from "perch", and neither is an office.

# The words that ask how many people live somewhere. "many people" is the phrase, because "how
# many people" alone is also a portion question ("how many people does this serve").
CROWD = ("population", "people live", "many people", "many people live", "inhabitants",
         "how big is", "big is")


# --- who holds the office -------------------------------------------------------------------
# Each reply gives the office, the name, the party where there is one, and the date it started.
# "The next general election has to be held by August 2029" is the half that keeps the answer
# honest after it goes out of date: a reader can see that the fact has an expiry.
_row("uk-prime-minister", (("prime minister", "the pm", "uk pm", "british pm", "pm"), WHO),
      "Keir Starmer is the prime minister - Labour, in office since July 2024, when his party won "
      "the general election. The next one has to be held by August 2029.",
      bias=2,
      # The first prime minister is history's answer ("Robert Walpole, 1721"), and a line that
      # asks about a past one names it or says "was"/"did".
      avoid=("first", "walpole", "churchill", "thatcher", "blair", "was", "did", "history",
             "ww2", "war",
             # and neither is the person in charge of the asker's own office: "who is the pm of
             # my office" was answered "Keir Starmer is the prime minister"
             "my office", "our office", "office manager", "workplace", "at work", "my company",
             "our company", "my team", "our team", "tenants", "residents", "association",
             "committee") + OTHER_PLACES)

_row("uk-monarch", (("king", "queen", "monarch", "royal family"), WHO),
      "Charles III is the king: he became monarch in September 2022, when Elizabeth II died. "
      "Camilla is queen, and the heir is Prince William.",
      bias=2,
      # The king on a chessboard, a king-size bed, a burger, a lion, a prawn, a card game, a
      # drag act and a prom are all "king" or "queen" and none of them is the monarch. Every
      # one of these is the specific line the entry would otherwise take.
      avoid=("chess", "check", "bed", "size", "size bed", "burger", "lion", "prawn",
             "prawns", "card", "cards", "poker", "hearts", "spades", "drag", "prom", "band",
             "bohemian", "bee", "bees", "henry", "victoria", "elizabeth", "tudor", "cleopatra",
             "arthur", "luther", "stephen", "bb", "awards", "speech", "xmas speech",
             "king of the", "queen of the",
             # the first king of England is Athelstan in 927, a history question, and the
             # row for him cannot answer a line this one has taken
             "first", "athelstan", "first king",
             # the monarch is not a dog, not a pub and not the person in charge of the asker's
             # own small outfit: "the king charles spaniel is called alfie" was answered with
             # Charles III. "my king" is a phrase and not the bare "my", because "who is my
             # prime minister" is a real question.
             "spaniel", "cavalier", "king charles spaniel", "dog", "dogs", "puppy",
             "my king", "our king", "my queen", "our queen", "pub", "hotel") + OTHER_PLACES)

_row("us-president", (("president", "potus", "us president", "american president",
                       "president of the united states", "president of america", "us president"), WHO),
      "Donald Trump is the US president: he took office in January 2025 for a second term, after "
      "beating Kamala Harris in November 2024. JD Vance is vice president. A president serves "
      "four years and can be elected twice.",
      bias=1,
      # The vice president has its own row below, and a club, a society, a union or a company has
      # a president who is not the American one.
      avoid=("vice", "club", "society", "company", "union", "student", "board", "obama",
             "biden", "lincoln", "kennedy", "washington", "assassinated", "election",
             "elections", "who won", "vote",
             # the president of the asker's own small organisation is not the American one:
             # "who is the president of my tenants association" was answered "Donald Trump is
             # the US president". These are phrases and words that no American question uses.
             "my tenants", "tenants", "residents", "association", "committee", "my office",
             "our office", "office manager", "workplace", "at work", "my company", "our company",
             "my club", "our club", "golf", "darts", "pigeon", "tenants association",
             # a commission, a council or a court has a president too, and none of them is the
             # American one: "who is the president of the european commission" was answered
             # "Donald Trump is the US president"
             "commission", "council", "court", "european") + OTHER_PLACES)

_row("us-vice-president", (("vice president", "vp"), WHO),
      "JD Vance is the US vice president, sworn in in January 2025 alongside Donald Trump. The "
      "job is to take over if the president cannot serve, and to break ties in the Senate.",
      bias=3,
      avoid=OTHER_PLACES)

_row("uk-chancellor", (("chancellor", "exchequer"), WHO),
      "Rachel Reeves is the chancellor of the exchequer - Labour, in office since July 2024, and "
      "the first woman to hold the job. The chancellor writes the budget and sets the tax rules.",
      bias=2,
      # A university chancellor, a German chancellor and the chancellor of a court are all other
      # chancellors; the German one has no answer here, so it falls through rather than lying.
      avoid=("university", "german", "germany", "berlin", "merkel", "scholz", "merz", "court",
             "vice chancellor", "degree", "graduation") + OTHER_PLACES)

_row("scotland-first-minister", (("first minister", "fm", "prime minister", "pm", "leader"),
                                ("scotland", "scottish", "holyrood", "snp", "swinney", "sturgeon")),
      "John Swinney is Scotland's first minister - SNP, in office since May 2024, when Humza "
      "Yousaf resigned. The Scottish parliament sits at Holyrood in Edinburgh.",
      bias=2,
      # Northern Ireland's first minister and Wales's have their own rows; a care home has a
      # manager, not a first minister.
      avoid=("northern ireland", "wales", "welsh") + OTHER_PLACES)

_row("wales-first-minister", (("first minister", "fm"), ("wales", "welsh", "senedd", "morgan")),
      "Eluned Morgan is Wales's first minister - Labour, in office since August 2024, and the "
      "first woman to hold the job. The Welsh parliament is the Senedd, in Cardiff Bay.",
      bias=2,
      avoid=OTHER_PLACES)

_row("ni-first-minister", (("first minister", "fm"), ("northern ireland", "ni", "stormont",
                                                          "oneill", "oneil", "sinn fein")),
      "Michelle O'Neill is Northern Ireland's first minister - Sinn Féin, in office since "
      "February 2024, with Emma Little-Pengelly of the DUP as deputy first minister. The two "
      "jobs are always held by the two biggest parties.",
      bias=2,
      # Northern Ireland is the one office whose own name is a country in the list above, and
      # "iceland" is one letter from "ireland" so the slip reader turned this row off on its own
      # lines. A guard has to be the countries that are not this one.
      avoid=tuple(word for word in OTHER_PLACES
                  if word not in ("ireland", "irish", "iceland")))

# "who is the first minister" on its own names no country, so instead of a shrug it gives the
# three names and asks which was meant. The country rows above carry a bias, so a line that does
# name one is still answered by that country's row.
_row("first-minister-which", (("first minister",), WHO), bias=0,
     ask=("who", "who's", "whos", "current", "still", "now", "which", "name", "is"),
     reply="There are three. Scotland's is John Swinney (SNP), Wales's is Eluned Morgan "
           "(Labour), and Northern Ireland's is Michelle O'Neill (Sinn Féin), with Emma "
           "Little-Pengelly as deputy. Which one did you mean?",
     avoid=("scotland", "scottish", "wales", "welsh", "northern ireland", "stormont",
            "senedd", "holyrood"))

_row("home-secretary", (("home secretary",), WHO),
      "Yvette Cooper is the home secretary - Labour, in office since July 2024. The Home Office "
      "covers the police, the borders, immigration and passports.",
      bias=2,
      avoid=OTHER_PLACES)

_row("london-mayor", (("mayor of london", "london mayor"), WHO),
      "Sadiq Khan is the mayor of London: first elected in 2016 and re-elected in May 2024. The "
      "job covers transport, policing and planning for the whole of London.",
      bias=3,
      avoid=OTHER_PLACES)

# a bare "vatican" is the place, not the office: "is the vatican a country" is geography's and
# "is the vatican worth a whole day" is travel's. The office questions all say pope or pontiff,
# and "who is the pope in the vatican" still reaches this row through "pope".
_row("pope", (("pope", "pontiff"), WHO),
      "Leo XIV is the pope: elected in May 2025 and taking the name Leo XIV, after Francis. He "
      "was Cardinal Robert Prevost, and he is the first pope from the United States.",
      bias=2,
      # "the pope said" is a quotation and "pope's hat" is a costume; neither is the office.
      # A sightseeing question about the Vatican is not the office either: "is the vatican worth
      # a whole day" and "is 3 days enough for the vatican" were both told who the pope is, so
      # the visit words stand this row down and travel's site note answers it instead.
      avoid=("said", "quote", "hat", "costume", "fancy dress", "card", "who was",
             "worth", "days", "enough", "visit", "visiting", "tour", "trip", "open", "hours",
             "long", "tickets", "museum", "museums", "basilica", "sistine", "sightseeing",
             "whole day"))


# --- who plays the part ---------------------------------------------------------------------
# One row per part, because the part is the meaning and the actor is the fact. Every reply names
# the part back (so a reader who typed a different spelling sees what was answered) and gives the
# actor plus the films they did it in - which is what someone asking "who plays batman" wants to
# know when there have been several.
_row("plays-iron-man", (("iron man", "tony stark"), CAST),
      "Robert Downey Jr plays Tony Stark: Iron Man (2008) through Avengers: Endgame (2019). He "
      "started the Marvel film run and was in nine of them.",
      bias=3,
      # "how do i make an iron man suit" is a costume, and "who wrote iron man" is the comic.
      avoid=("costume", "suit", "make", "made", "draw", "wrote", "comic", "toy"))

_row("plays-batman", (("batman", "bruce wayne", "dark knight"), CAST),
      "Robert Pattinson plays Batman in The Batman (2022). Before him: Christian Bale in the Dark "
      "Knight trilogy (2005-2012), Ben Affleck in the two Justice League-era films, and Michael "
      "Keaton in 1989 and 1992.",
      bias=3,
      # A line that names the trilogy is asking about the man in it. The answer above leads with
      # the newest Batman, so "who played batman in the dark knight" put the wrong name first;
      # the trilogy's own row below answers that, and these phrases send the line there.
      avoid=("costume", "suit", "make", "draw", "wrote", "comic", "toy", "cartoon", "lego",
             "dark knight rises", "batman begins", "the dark knight", "christian bale", "bale",
             "trilogy", "2008", "2012", "2005"))

# The part named wins over the series it is in, and the film named wins over the whole run: someone
# who types "the dark knight" wants the Batman of that film, not a list with the newest one first.
_row("plays-batman-dark-knight",
     (("batman", "bruce wayne", "dark knight", "batman begins"),
      ("dark knight", "dark knight rises", "batman begins")),
      "Christian Bale plays Batman in the Dark Knight trilogy: Batman Begins (2005), The Dark "
      "Knight (2008) and The Dark Knight Rises (2012). Heath Ledger played the Joker in The Dark "
      "Knight, and Tom Hardy played Bane.",
      bias=6,
      ask=("dark knight", "dark knight rises", "batman begins", "bale", "trilogy", "2008",
           "2012", "2005"),
      avoid=("costume", "suit", "make", "draw", "wrote", "comic", "toy", "cartoon", "lego",
             "joker", "who plays the joker", "bane", "heath ledger"))

_row("plays-thor", (("thor",), CAST),
      "Chris Hemsworth plays Thor, from Thor (2011) to Thor: Love and Thunder (2022).",
      bias=3,
      avoid=("costume", "hammer", "norse", "myth", "god of thunder", "wrote", "comic"))

_row("plays-captain-america", (("captain america",), CAST),
      "Chris Evans plays Captain America: The First Avenger (2011) through Avengers: Endgame "
      "(2019).",
      bias=3,
      avoid=("costume", "make", "draw", "wrote", "comic"))

_row("plays-spider-man", (("spider man", "spiderman", "peter parker"), CAST),
      "Tom Holland plays Spider-Man in the three Home films (2017-2021). Andrew Garfield did the "
      "two Amazing Spider-Man films, and Tobey Maguire the three before those.",
      bias=3,
      avoid=("costume", "make", "draw", "wrote", "comic", "spider in my", "bite"))

_row("plays-wonder-woman", (("wonder woman", "diana prince"), CAST),
      "Gal Gadot plays Wonder Woman: Batman v Superman (2016), her own film in 2017, and 1984 in "
      "2020.",
      bias=3)

_row("plays-harry-potter", (("harry potter",), CAST),
      "Daniel Radcliffe plays Harry Potter in all eight films (2001-2011). He was eleven when the "
      "first one was shot and twenty-one by the last.",
      bias=4,
      # The author's answer holds "harry potter" too, and it fires on "who wrote"/"who is".
      # The other people in the same films hold this row's two words as well - "who plays snape in
      # harry potter" names Snape, so it is Snape's row, and the same for the rest of the cast.
      avoid=("wrote", "written", "author", "book", "books", "read", "reading", "rowling",
             "snape", "severus", "hermione", "granger", "hagrid", "dumbledore", "malfoy",
             "draco", "voldemort", "dobby", "mcgonagall", "weasley", "ron", "ginny",
             "professor"))

_row("plays-sherlock", (("sherlock", "holmes"), CAST),
      "Benedict Cumberbatch plays Sherlock Holmes in the BBC series (2010-2017), with Martin "
      "Freeman as Watson. Robert Downey Jr played him in the two Guy Ritchie films, and Jeremy "
      "Brett in the 1980s series.",
      bias=4,
      # Arthur Conan Doyle's answer holds "sherlock holmes" too; this row is the screen only.
      avoid=("wrote", "written", "author", "book", "books", "read", "reading", "doyle",
             "stories"))

_row("plays-james-bond", (("james bond", "007"), CAST),
      "Daniel Craig played James Bond in five films, Casino Royale (2006) to No Time to Die "
      "(2021). The next Bond has not been announced. Before Craig: Pierce Brosnan, Timothy "
      "Dalton, Roger Moore, George Lazenby and Sean Connery.",
      bias=3,
      avoid=("wrote", "author", "book", "books", "ian fleming", "fleming", "car", "watch"))

_row("plays-dumbledore", (("dumbledore",), CAST),
      "Michael Gambon played Dumbledore in six of the eight Harry Potter films, taking over from "
      "Richard Harris, who died after the second. Jude Law plays him young in the Fantastic "
      "Beasts films.",
      bias=3,
      avoid=("wrote", "author", "book", "books", "dumbledore quote", "said"))

_row("plays-doctor-who", (("doctor who", "the doctor"), CAST),
      "Ncuti Gatwa plays the Doctor, from the 2023 Christmas special on. Before him: Jodie "
      "Whitaker, Peter Capaldi, Matt Smith, David Tennant and Christopher Eccleston since the "
      "series came back in 2005.",
      bias=3,
      avoid=("watch", "wrote", "author", "book", "episode order", "start"))

_row("plays-shrek", (("shrek",), CAST),
      "Mike Myers voices Shrek, with Eddie Murphy as Donkey and Cameron Diaz as Fiona, in the four "
      "films from 2001 to 2010.",
      bias=3)

_row("plays-joker", (("joker",), CAST),
      "Joaquin Phoenix plays the Joker in Joker (2019) and Folie a Deux (2024). Heath Ledger did "
      "it in The Dark Knight (2008), Jack Nicholson in 1989 and Jared Leto in Suicide Squad.",
      bias=3,
      avoid=("card", "cards", "joke", "pun", "costume"))


_row("plays-wednesday", (("wednesday addams", "wednesday"), CAST),
     "Jenna Ortega plays Wednesday Addams in Wednesday (2022), the Netflix series. Christina "
     "Ricci, who was Wednesday in the two 1990s films, plays her mother in it.",
     bias=3,
     # A Wednesday lunch, a Wednesday off, Wednesday as the day: the part is the name alone only
     # when the line is asking who plays her, and the cast words are what say so.
     # A listings question is the one that shares the day: "whats on tv wednesday night" has a
     # cast word ("tv") and the day, so the day alone would have read it as the part.
     avoid=("day", "days", "lunch", "dinner", "off", "bank holiday", "week", "on tv",
            "whats on", "tonight", "night", "listings", "channel", "ash wednesday", "wrote",
            "book"))

_row("plays-eleven", (("eleven", "stranger things"), CAST),
     "Millie Bobby Brown plays Eleven in Stranger Things (2016-2025).",
     bias=3,
     avoid=("number", "count", "counting", "wrote", "book"))

_row("plays-gollum", (("gollum", "smeagol", "lord of the rings"), CAST),
     "Andy Serkis plays Gollum: the voice and the motion capture in The Lord of the Rings and The "
     "Hobbit films. He also second-unit directed parts of the Hobbit trilogy.",
     bias=2,
     avoid=("wrote", "book", "books", "tolkien", "read"))

_row("plays-jack-sparrow", (("jack sparrow", "pirates of the caribbean"), CAST),
     "Johnny Depp plays Jack Sparrow, in all five Pirates of the Caribbean films (2003-2017).",
     bias=3)

_row("plays-katniss", (("katniss", "hunger games"), CAST),
     "Jennifer Lawrence plays Katniss Everdeen in the four Hunger Games films (2012-2015).",
     bias=3,
     avoid=("wrote", "book", "books", "read"))

_row("plays-neo", (("neo", "the matrix"), CAST),
     "Keanu Reeves plays Neo in The Matrix (1999) and its three sequels, and again in Resurrections "
     "(2021).",
     bias=3)

_row("plays-harley-quinn", (("harley quinn",), CAST),
     "Margot Robbie plays Harley Quinn in Suicide Squad (2016), Birds of Prey (2020) and The "
     "Suicide Squad (2021). Lady Gaga plays her in Joker: Folie a Deux.",
     bias=3,
     avoid=("costume", "make up", "costume make up", "wrote", "comic", "cartoon"))

_row("plays-john-wick", (("john wick",), CAST),
     "Keanu Reeves plays John Wick, in all four films (2014-2023).",
     bias=3)

_row("plays-elsa", (("elsa", "frozen"),
                    CAST + ("from",
                            # the film is also asked about without a part in it: its songs, its
                            # certificate, and when it came out. Without these, "is frozen
                            # suitable for a 3 year old" was answered by the freezer card.
                            "song", "songs", "sing", "sings", "sang", "soundtrack",
                            "come out", "came out", "release", "released", "when did",
                            "suitable for", "ok for", "scary", "3 year old", "4 year old",
                            "5 year old", "toddler", "sequel", "plot", "about", "ending")),
     "Idina Menzel is the voice of Elsa in Frozen (2013) and Frozen 2 (2019) and sings Let It Go; "
     "Kristen Bell is Anna. Both films are U certificates of about 100 minutes, so they are fine "
     "for a three year old - the ice monster in the first one is the only bit that frightens some "
     "small children.",
     bias=3,
    avoid=("frozen food", "freezer", "wrote", "book",
            # "from" is one of the cast words, so "frozen" plus "from" made every "can i cook it
            # from frozen" line a who-plays question: mince, sausages, a chop, a turkey and a
            # chicken all got Idina Menzel. The film is asked about with a part in it ("who plays
            # elsa", "who is elsa from frozen"), so a cooking verb or the food itself takes the
            # line away from this row and back to the kitchen.
            "cook", "cooking", "cooked", "roast", "roasted", "oven", "fry", "fried", "bake",
            "baked", "grill", "microwave", "air fryer", "slow cooker", "defrost", "defrosted",
            "thaw", "thawed", "still frozen", "cook from frozen", "cooked from frozen",
            "cooking from frozen", "roast from frozen", "straight from frozen",
            "chicken", "turkey", "duck", "meat", "beef", "pork", "lamb", "fish", "salmon",
            "cod", "prawn", "prawns", "shrimp", "sausage", "sausages", "mince", "chop", "chops",
            "turkey", "bacon", "joint", "steak", "steaks", "liver", "kidneys",
            # the food on its own, with no cooking verb: "frozen prawns straight from frozen" is
            # a person about to cook, not a question about a 2013 film
            "chips", "peas", "veg", "vegetables", "spinach", "berries", "fruit", "bread",
            "rolls", "pastry", "pizza", "lasagne", "curry", "rice", "pie", "raw", "eat",
            "eaten", "edible",
            # "about", "toddler" and "suitable for" are new keys here, so a pudding and a
            # shoulder are named too: "is frozen yoghurt ok for a toddler" is a food question
            "yoghurt", "yogurt", "ice cream", "ice lolly", "shoulder", "freezer", "ice",
            "fish fingers", "pudding", "dessert", "smoothie", "berries"))

_row("plays-hermione", (("hermione", "granger"), CAST),
     "Emma Watson plays Hermione Granger in all eight Harry Potter films (2001-2011).",
     bias=3,
     avoid=("wrote", "book", "books", "rowling"))

_row("plays-ron", (("ron", "rupert grint", "weasley"), CAST),
     "Rupert Grint plays Ron Weasley in all eight Harry Potter films (2001-2011).",
     bias=3,
     avoid=("wrote", "book", "books", "rowling", "ronaldo", "ronan", "ronnie", "veronica"))

_row("plays-snape", (("snape", "severus"), CAST),
     "Alan Rickman plays Severus Snape in all eight Harry Potter films (2001-2011).",
     bias=3,
     avoid=("wrote", "book", "books", "rowling"))

_row("plays-homer-simpson", (("homer simpson", "the simpsons"), CAST),
     "Dan Castellaneta voices Homer Simpson, and has since the first short in 1987 - he also does "
     "Grampa, Krusty and Barney.",
     bias=4,
     avoid=("odyssey", "iliad", "greek", "poet", "wrote"))

_row("plays-geralt", (("geralt", "the witcher"), CAST),
     "Henry Cavill plays Geralt in the first three series of The Witcher (2019-2023); Liam "
     "Hemsworth took the part from series four.",
     bias=3,
     avoid=("wrote", "book", "books", "read", "game"))

# --- how many people live there -------------------------------------------------------------
# One row per city, keyed by the city and one of the words that asks how big it is. The figures
# are the city's own and, where the two differ by a lot, the wider area's too, because "how many
# people live in london" means either and the difference is the interesting part.
CITIES = {
    "london": "London has about 8.9 million people, and about 14 million in the wider area "
              "around it. It is the biggest city in the UK by a long way - Birmingham, the "
              "second, has about 1.1 million.",
    "manchester": "Manchester itself has about 550,000 people; Greater Manchester, the whole "
                  "cluster of towns around it, has about 2.9 million.",
    "birmingham": "Birmingham has about 1.15 million people, which makes it the second biggest "
                  "city in the UK after London.",
    "leeds": "Leeds has about 810,000 people, the biggest of the Yorkshire cities.",
    "glasgow": "Glasgow has about 635,000 people, and about 1.7 million in the wider Clyde "
               "valley. It is Scotland's biggest city.",
    "edinburgh": "Edinburgh has about 510,000 people - smaller than Glasgow, though it is the "
                 "capital, and the festival more than doubles it in August.",
    "cardiff": "Cardiff has about 370,000 people, and about 1.1 million in the wider south "
               "Wales area.",
    "belfast": "Belfast has about 350,000 people, and about 670,000 in the wider area.",
    "new york": "New York City has about 8.3 million people - 8.3 million in the five "
                "boroughs, and around 19 million in the metro area. It is the biggest city in "
                "the United States.",
    "paris": "Paris has about 2.1 million people inside the city limits, and about 11 million in "
             "the whole metro area - the city proper is small, and the suburbs are where most "
             "Parisians live.",
    "tokyo": "Tokyo has about 14 million people in the city, and about 37 million in the wider "
             "metro area, which makes it the biggest in the world.",
    "sydney": "Sydney has about 5.3 million people, the biggest city in Australia.",
    "berlin": "Berlin has about 3.8 million people, the biggest city in Germany and about eight "
              "times the size of Frankfurt.",
    "dublin": "Dublin has about 590,000 in the city and about 1.5 million in the county, which is "
              "roughly a third of the people in Ireland.",
}

for _city, _fact in CITIES.items():
    _row(
        f"population-{_city.replace(' ', '-')}", (_city, CROWD), _fact,
        # A serving suggestion is the kitchen's question, and a city's population is not.
        avoid=("serve", "serves", "serving", "recipe", "dinner", "cook", "feed", "portions",
               "guests", "how many people for"))
del _city, _fact


_row("eu-commission-president", (("president of the european commission",
                                  "european commission", "eu commission", "brussels",
                                  "president of the eu", "eu president"), WHO),
      "Ursula von der Leyen is the president of the European Commission: in office since "
      "December 2019, and given a second five-year term from December 2024 after the European "
      "elections in June. The commission proposes EU law; the parliament and the member states' "
      "governments pass it.",
      bias=2,
      avoid=("club", "society", "company", "union", "student", "board", "golf", "council",
             "court", "charity"))


# --- who leads the other countries ----------------------------------------------------------
# Every office row above holds out `OTHER_PLACES`, and it has to: a confident wrong name is the
# worst reply the bot can give, so "who is the president of france" used to fall back to the
# honest hedge rather than to Keir Starmer. The hedge is not an answer, though. People ask who
# runs a country all the time, and it is a name and a date - the same shape as the rows above -
# so the countries get one row each, in the same form: the office, the name, when it started,
# and the one fact that makes it make sense (how long the term is, or who really holds the power).
#
# Every reply is written as the appointment, not as "now", for the reason at the top of this
# file: "in office since May 2025" stays true after the next election in a way "the current
# chancellor" does not.
LEADER_WORDS = ("president", "prime minister", "pm", "chancellor", "leader", "taoiseach",
                "king", "queen", "monarch", "head of state", "first minister", "emperor",
                "supreme leader", "general secretary", "in charge", "runs the country",
                "running the country", "who leads", "government")

# The country in the first part and the office in the second, so "who is the president of france",
# "the french president" and "who runs france" are one row apiece without three keys each.
LEADERS = {
    "france": (("france", "french"),
               "Emmanuel Macron is the president of France: elected in 2017 and re-elected in "
               "2022. A French president serves five years, so the next election is due in 2027, "
               "and the prime minister, who runs the day-to-day government, is appointed by the "
               "president."),
    "germany": (("germany", "german"),
                "Friedrich Merz is the chancellor of Germany: in office since May 2025, after his "
                "CDU/CSU bloc won the February 2025 election. The president, whose job is mostly "
                "ceremonial, is Frank-Walter Steinmeier."),
    "italy": (("italy", "italian"),
              "Giorgia Meloni is the prime minister of Italy: in office since October 2022, "
              "leading a coalition built round her Brothers of Italy party. The president, who "
              "picks the prime minister after an election, is Sergio Mattarella."),
    "spain": (("spain", "spanish"),
              "Pedro Sanchez is the prime minister of Spain: in office since 2018, and back in "
              "office after the 2023 election. The head of state is King Felipe VI, whose role is "
              "ceremonial."),
    # Northern Ireland is not Ireland and has neither a president nor a taoiseach: its offices
    # are the first minister and the Secretary of State, and the row for them is above.
    "ireland": (("ireland", "irish", "taoiseach"),
                "Micheal Martin is the taoiseach, or prime minister, of Ireland: in office since "
                "January 2025. The president, a largely ceremonial role, is Catherine Connolly, "
                "elected in October 2025.",
                ("northern ireland", "northern irish", "belfast", "stormont", "ulster")),
    "canada": (("canada", "canadian"),
               "Mark Carney is the prime minister of Canada: in office since March 2025, and his "
               "Liberal party won the April 2025 election. He took over from Justin Trudeau, who "
               "resigned after nine years."),
    "australia": (("australia", "australian", "aussie"),
                  "Anthony Albanese is the prime minister of Australia: in office since May 2022 "
                  "and re-elected in May 2025. The head of state is King Charles III, represented "
                  "there by a governor-general."),
    "new zealand": (("new zealand", "new zealander", "kiwi"),
                    "Christopher Luxon is the prime minister of New Zealand: in office since "
                    "November 2023, leading a National-led coalition. The head of state is King "
                    "Charles III, represented by a governor-general."),
    "india": (("india", "indian"),
              "Narendra Modi is the prime minister of India: in office since 2014, and in his "
              "third term since June 2024. The president, whose role is largely ceremonial, is "
              "Droupadi Murmu."),
    "china": (("china", "chinese"),
              "Xi Jinping is the president of China: in office since 2013, and general secretary "
              "of the Communist Party since 2012. The party holds the power, and since 2018 there "
              "is no limit on his terms."),
    "japan": (("japan", "japanese"),
              "Sanae Takaichi is the prime minister of Japan: in office since October 2025, and "
              "the first woman to hold the job. The head of state is the emperor, Naruhito."),
    "russia": (("russia", "russian"),
               "Vladimir Putin is the president of Russia: in office since 2000, with four years "
               "as prime minister under Dmitry Medvedev in the middle. His current term runs to "
               "2030."),
    "ukraine": (("ukraine", "ukrainian"),
                "Volodymyr Zelenskyy is the president of Ukraine: elected in 2019. A presidential "
                "election is due, but it cannot be held while martial law is in force."),
    "turkey": (("turkey", "turkish", "turkiye"),
               "Recep Tayyip Erdogan is the president of Turkey: in office since 2014, and prime "
               "minister before that from 2003. The presidency became the centre of power after "
               "the 2017 referendum."),
    "greece": (("greece", "greek"),
               "Kyriakos Mitsotakis is the prime minister of Greece: in office since 2019 and "
               "re-elected in June 2023, leading New Democracy. The president, a ceremonial role, "
               "is chosen by parliament."),
    "poland": (("poland", "polish"),
               "Donald Tusk is the prime minister of Poland: in office since December 2023, after "
               "the October 2023 election. The president is Karol Nawrocki, elected in June 2025."),
    "sweden": (("sweden", "swedish"),
               "Ulf Kristersson is the prime minister of Sweden: in office since October 2022, "
               "leading a coalition that the Sweden Democrats support from outside it. The head "
               "of state is King Carl XVI Gustaf."),
    "norway": (("norway", "norwegian"),
               "Jonas Gahr Store is the prime minister of Norway: in office since 2021, and Labour "
               "won the September 2025 election, so he carried on. The head of state is King "
               "Harald V."),
    "denmark": (("denmark", "danish"),
                "Mette Frederiksen is the prime minister of Denmark: in office since 2019. The "
                "head of state is King Frederik X, who took over in January 2024."),
    "belgium": (("belgium", "belgian"),
                "Bart De Wever is the prime minister of Belgium: in office since February 2025, "
                "after seven months of coalition talks. The head of state is King Philippe."),
    "portugal": (("portugal", "portuguese"),
                 "Luis Montenegro is the prime minister of Portugal: in office since April 2024 "
                 "and re-elected in May 2025. The president, who can dissolve parliament, is "
                 "Marcelo Rebelo de Sousa."),
    "mexico": (("mexico", "mexican"),
               "Claudia Sheinbaum is the president of Mexico: in office since October 2024, and "
               "the first woman to hold the job. A Mexican president serves one six-year term and "
               "cannot stand again."),
    "brazil": (("brazil", "brazilian"),
               "Luiz Inacio Lula da Silva is the president of Brazil: in office since January "
               "2023, his third term. A Brazilian president serves four years and can be "
               "re-elected once in a row."),
    "argentina": (("argentina", "argentinian", "argentine"),
                  "Javier Milei is the president of Argentina: in office since December 2023. He "
                  "won on a promise to dollarise the economy and cut the state back."),
    "south africa": (("south africa", "south african"),
                     "Cyril Ramaphosa is the president of South Africa: in office since 2018, and "
                     "chosen again by parliament in June 2024 after the ANC lost its majority. The "
                     "ANC has governed since 1994."),
    "nigeria": (("nigeria", "nigerian"),
                "Bola Tinubu is the president of Nigeria: in office since May 2023. A Nigerian "
                "president serves four years and can stand for a second term."),
    "kenya": (("kenya", "kenyan"),
              "William Ruto is the president of Kenya: in office since September 2022. A Kenyan "
              "president serves a maximum of two five-year terms."),
    "egypt": (("egypt", "egyptian"),
              "Abdel Fattah el-Sisi is the president of Egypt: in office since 2014, after leading "
              "the 2013 takeover. The president holds most of the power, and the army is a large "
              "part of the economy."),
    "israel": (("israel", "israeli"),
               "Benjamin Netanyahu is the prime minister of Israel: in office since December 2022, "
               "and the longest-serving prime minister the country has had. Israel has a "
               "president too - Isaac Herzog - but that job is ceremonial."),
    "iran": (("iran", "iranian"),
             "Masoud Pezeshkian is the president of Iran: in office since July 2024. The man with "
             "the final say is the supreme leader, Ali Khamenei, and the president runs the "
             "government under him."),
    "saudi arabia": (("saudi arabia", "saudi", "saudi arabian"),
                     "King Salman is the king of Saudi Arabia, but his son Mohammed bin Salman - "
                     "crown prince, and prime minister since 2022 - runs the country day to day."),
    # "korea" alone reaches this row too, so the north has to be held out here and answered by
    # its own row: Kim Jong Un is nobody's president, and the line is a common one.
    "south korea": (("south korea", "korea", "korean"),
                    "Lee Jae-myung is the president of South Korea: in office since June 2025, "
                    "after winning the snap election that followed Yoon Suk Yeol's impeachment. A "
                    "South Korean president serves one five-year term.",
                    ("north", "north korea", "kim jong", "pyongyang", "dprk")),
    "north korea": (("north korea", "north korean"),
                    "Kim Jong Un has led North Korea since 2011, when his father Kim Jong Il died. "
                    "He is not the head of state on paper: the constitution gives that title to "
                    "the president of the presidium of the Supreme People's Assembly, Choe Ryong "
                    "Hae. The Workers' Party is the only party that decides anything."),
    "pakistan": (("pakistan", "pakistani"),
                 "Shehbaz Sharif is the prime minister of Pakistan: in office since March 2024. "
                 "The president is a ceremonial role; the prime minister runs the government, "
                 "though the army has a large say."),
    "indonesia": (("indonesia", "indonesian"),
                  "Prabowo Subianto is the president of Indonesia: in office since October 2024, "
                  "after winning the February 2024 election. A president serves five years and can "
                  "be re-elected once."),
    "singapore": (("singapore", "singaporean"),
                  "Lawrence Wong is the prime minister of Singapore: in office since May 2024, "
                  "when Lee Hsien Loong stepped down after twenty years. The PAP has governed "
                  "since independence in 1965."),
    "malaysia": (("malaysia", "malaysian"),
                 "Anwar Ibrahim is the prime minister of Malaysia: in office since November 2022, "
                 "after decades in opposition. The king, whose crown rotates every five years "
                 "between the state rulers, is the head of state."),
    "philippines": (("philippines", "filipino"),
                    "Ferdinand Marcos Jr is the president of the Philippines: in office since June "
                    "2022. A Philippine president serves one six-year term."),
}

# The lines where the office word is not a state's: a club's, a company's, a union's, a board's,
# a school's. Kept in one place because every row below needs all of it, and a row that is missing
# one of these answers a line it should have passed on.
_LEADER_AVOID = ("club", "society", "company", "union", "student", "board", "golf", "darts",
                 "my office", "our office", "workplace", "at work", "my company", "our company",
                 "my team", "our team", "committee", "association", "residents", "tenants",
                 "university", "cricket", "football", "charity", "history", "was the",
                 "first president", "first prime minister", "war", "recipe",
                 # "who is the school council president" is a school's, and it used to be answered
                 # by the American president's row before that row was fenced
                 "school", "school council", "parish", "tenants association")

for _place, _row_data in LEADERS.items():
    _words, _reply = _row_data[0], _row_data[1]
    # a third item holds out the other country that uses the same short name - see the two
    # entries that have one
    _extra = _row_data[2] if len(_row_data) > 2 else ()
    _row("leader-" + _place.replace(" ", "-"), (_words, LEADER_WORDS), _reply,
         # the country is named, so the office in the line is that country's: these only hold out
         # the lines where the word is not the country at all, or where it is a company's, a
         # club's, a union's or a board's president rather than a state's
         avoid=_LEADER_AVOID + tuple(_extra))
del _place, _row_data, _words, _reply, _extra


# Where a country has a second office that people ask about by name, the first sentence above
# would be about the wrong one: "who is the president of germany" is Steinmeier, not the
# chancellor. Each of these is the same shape and a higher bias, so the office word in the line
# decides which of the two answers.
LEADERS_SECOND = {
    "germany-president": (("germany", "german"), ("president",),
                          "Frank-Walter Steinmeier is the president of Germany: in office since "
                          "2017 and re-elected in 2022. The job is mostly ceremonial - the "
                          "chancellor, Friedrich Merz, runs the government."),
    "spain-king": (("spain", "spanish"), ("king", "queen", "monarch", "head of state"),
                   "Felipe VI is the king of Spain: he took the throne in June 2014 when his "
                   "father Juan Carlos abdicated. The king is head of state but does not run the "
                   "government - the prime minister, Pedro Sanchez, does."),
    "italy-president": (("italy", "italian"), ("president",),
                        "Sergio Mattarella is the president of Italy: in office since 2015 and "
                        "re-elected in 2022. The president is head of state and picks the prime "
                        "minister after an election; Giorgia Meloni runs the government."),
    "ireland-president": (("ireland", "irish"), ("president",),
                          "Catherine Connolly is the president of Ireland: elected in October "
                          "2025. The job is largely ceremonial - the taoiseach, Micheal Martin, "
                          "runs the government.", ("northern ireland", "northern", "belfast",
                                                   "stormont", "ulster")),
    "israel-president": (("israel", "israeli"), ("president",),
                         "Isaac Herzog is the president of Israel: in office since 2021. The job "
                         "is ceremonial - the prime minister, Benjamin Netanyahu, runs the "
                         "government."),
    "portugal-president": (("portugal", "portuguese"), ("president",),
                           "Marcelo Rebelo de Sousa is the president of Portugal: in office since "
                           "2016 and re-elected in 2021. Unlike most ceremonial presidents he has "
                           "real power, including the right to dissolve parliament; the prime "
                           "minister is Luis Montenegro."),
    "japan-emperor": (("japan", "japanese"), ("emperor", "empress", "head of state"),
                      "Naruhito is the emperor of Japan: he took the throne in May 2019, when his "
                      "father Akihito stepped down. The emperor is a symbol of the state and has "
                      "no political power - the prime minister, Sanae Takaichi, runs the "
                      "government."),
    "poland-president": (("poland", "polish"), ("president",),
                         "Karol Nawrocki is the president of Poland: elected in June 2025. The "
                         "president can veto laws, and the prime minister, Donald Tusk, runs the "
                         "government."),
}

for _name, _row_data in LEADERS_SECOND.items():
    _words, _offices, _reply = _row_data[0], _row_data[1], _row_data[2]
    _extra = _row_data[3] if len(_row_data) > 3 else ()
    _row(_name, (_words, _offices), _reply, bias=1, avoid=_LEADER_AVOID + tuple(_extra))
del _name, _row_data, _words, _offices, _reply, _extra
