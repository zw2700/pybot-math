"""History: the events and people ordinary people ask about, in a nutshell.

The answers lane owns this domain. One Entry per event or person, keyed by the words that
identify it, so "who built the pyramids", "when were the pyramids built" and "pyramids of
giza" all reach the same answer. Facts are the short version a friend would give: the date,
the who and the one thing that makes it make sense. Where a date is genuinely argued about
(for example the end of the Hundred Years War) the answer says so instead of picking a side.
"""
import re

from .lookup import entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("history",)

COLD_WAR = ("The Cold War was the long standoff between the United States and its allies and "
            "the Soviet Union from about 1947 to 1991. They never fought each other directly "
            "because both had nuclear weapons, so the conflict played out in proxy wars, the "
            "space race and propaganda.")
# who came out on top is only said when it is asked for: "what was it about" wants the standoff,
# and a card that ends on a winner reads as padding there.
COLD_WAR_WINNER = " The West won it: the Soviet Union broke up in 1991."
ASKS_WHO_WON = ("won", "win", "winner", "beat", "victor", "victory", "came out on top")


def _cold_war(memory, understood):
    said = " " + re.sub(r"[^a-z]+", " ", str(understood.get("text") or "").lower()) + " "
    won = any((" %s " % word) in said for word in ASKS_WHO_WON)
    return COLD_WAR + (COLD_WAR_WINNER if won else "")

# The vote row is Britain and women, and the country cannot be an `avoid` word: a line that
# reaches nothing is read a second time as the household version of itself, where "in the us"
# becomes "in the me" and the avoid word travels with it, so an American question was answered
# with 1918 and 1928. The guard reads the text the person typed, which is the same in every
# reading. "us" on its own is what everybody writes when they mean "tell us", so only the
# country's phrase stands the row down.
_OTHER_SEX = frozenset(("men", "man", "mens", "male", "males"))
# The age side is the other history: 1969 is when 18-year-olds got the vote, and "when did 18
# year olds get the vote" was answered with 1918 and 1928. A number with no age word in front of
# it ("when did women over 30 get the vote") is this row's own 1918, so only the age phrases and
# the age words stand it down.
_OTHER_AGE = frozenset(("18", "16", "17", "21", "eighteen", "sixteen", "seventeen", "age",
                        "aged", "ages", "old", "olds", "older", "young", "younger", "youth",
                        "teen", "teens", "teenager", "teenagers"))
_OTHER_COUNTRY = frozenset((
    "america", "american", "usa", "united", "states", "canada", "canadian", "australia",
    "australian", "zealand", "france", "french", "germany", "german", "india", "indian",
    "saudi", "ireland", "irish"))
_US = ("in the us", "in the usa", " the us ", " the usa ", "in us")
# The row is women's campaign. Any other group the line names - black people, immigrants, poor
# people, working people - is a different history in a different row (or nowhere yet), and
# "when did black people get the vote" was answered with the suffragists because no women word
# was in the fence at all: it only listed the groups that were wrong, never the one that is right.
# So the row now needs a women word in the line rather than merely the absence of others.
_WOMEN = frozenset(("women", "womens", "woman", "womans", "female", "females",
                    "suffragette", "suffragettes", "suffrage", "pankhurst"))


def _not_the_other_sex_or_country(understood):
    """True when the line is about women voting in Britain, the only vote this row has."""
    text = ""
    if isinstance(understood, dict):
        text = str(understood.get("text") or understood.get("clean") or "").lower()
    if not text:
        return False
    words = set(text.replace("?", " ").replace(",", " ").replace(".", " ").split())
    if not words & _WOMEN:
        return False
    if words & _OTHER_SEX or words & _OTHER_COUNTRY:
        return False
    if words & _OTHER_AGE:
        return False
    if any(phrase in " " + text + " " for phrase in _US):
        return False
    return True


# The franchise card in bot/knowledge/lifeadmin.py says what the age is now, and that is the
# answer to "what is the voting age" and "can a 16 year old vote": opening with 1969 gave the
# history of the change to somebody asking what the age is. The row below is the change itself,
# so it takes a line that is past tense or names the year, and leaves the present tense alone.
_HISTORY_OF_THE_VOTE = re.compile(
    r"\b(?:when did|when was|when were|what year|1969|1970|1968|1967|history|historically|"
    r"used to|came down|change|changed|changes|raised|lowered|lowed|became|become|introduced|"
    r"first|was the voting age|was the age)\b", re.I)


def _about_the_change(reading):
    """A guard: the history of the vote answers a line about the change, not the age today."""
    reading = reading or {}
    text = (reading.get("clean") or reading.get("text") or "").lower()
    return _HISTORY_OF_THE_VOTE.search(text) is not None


# "How long to walk the great wall" is asked for a time, and the wall's own length is a different
# answer: the length row below keys "how long", so that is the card the walking question reached
# and it answered with 21,196 km. The walking time belongs to the same card because it is the same
# wall, and it is said only when the line says walk, so the length question still gets the length.
_WALK_THE_WALL = re.compile(r"\b(?:walk|walks|walking|hike|hikes|hiking|hiked)\b", re.I)


def _how_long_to_walk_the_wall(understood):
    """The walking time when the line asks to walk it, and the length of the wall otherwise."""
    length = ("About 21,196 km of wall in all, counting every branch and trench: the restored "
              "stretch most visitors walk at Badaling near Beijing is a few kilometres of that, "
              "and nobody walks the whole thing.")
    text = " " + str(understood.get("clean") or understood.get("text") or "") + " "
    if not _WALK_THE_WALL.search(text):
        return length
    return ("Two to three hours on the restored stretch at Badaling, walking it end to end at an "
            "easy pace, and most people take the cable car up at Mutianyu and walk a section in "
            "half a day. That is the wall as a visit. The whole 21,196 km is not a walk anyone "
            "does: it is broken by valleys, roads and reservoirs, and the parts in the west are "
            "crumbling earth rather than stone.")


ENTRIES = [
    # --- the ancient world ---------------------------------------------------
    # "how old are the pyramids" is the plainest age question there is, and without the age
    # words the row never reached MIN_SCORE: the subject alone is one signal.
    entry("pyramids-giza", ("pyramid", ("giza", "egypt", "egyptian", "build", "built", "who", "when",
                                       "old", "older", "age", "how old")),
          "Ancient Egyptians built them about 4,500 years ago, around 2560 BC for the Great "
          "Pyramid of Giza, as a tomb for the pharaoh Khufu. The workers were organised, paid "
          "labourers, not slaves, hauling stone on ramps and sledges."),
    entry("roman-empire-split", ("roman", ("split", "east", "west", "divide", "divided")),
          "The empire had grown too big to govern from one place, so in 285 AD Diocletian split "
          "it into east and west, each with its own emperor; it divided for good in 395. The "
          "east, ruled from Constantinople, lasted another thousand years; the west fell in 476."),
    entry("roman-empire-fall", ("roman", ("fall", "fell", "end", "ended", "476")),
          "The western Roman Empire ended in 476 AD when the German leader Odoacer deposed the "
          "boy emperor Romulus Augustulus. It was less one collapse than a long squeeze: "
          "inflation, plague, civil wars and pressure from migrating peoples."),
    entry("stonehenge", ("stonehenge", ("built", "who", "why", "when", "old")),
          "Stonehenge was raised in stages between about 3000 and 2000 BC in what is now "
          "Wiltshire, by Neolithic and Bronze Age Britons whose names we don't know. It was a "
          "burial ground and a place aligned with the midsummer sunrise, probably for ceremonies."),
    entry("cleopatra", ("cleopatra", ("who", "was", "egypt", "queen")),
          "Cleopatra VII was the last active ruler of Ptolemaic Egypt, from 51 BC until her death "
          "in 30 BC. She was Greek, not Egyptian, spoke Egyptian, and allied with Julius Caesar "
          "and Mark Antony to keep Egypt independent of Rome."),
    entry("columbus", ("columbus", ("who", "when", "1492", "america", "discover", "sail")),
          "Christopher Columbus reached the Caribbean in 1492, sailing for Spain, and thought he "
          "had found a route to Asia. He never set foot in North America itself; the Vikings had "
          "reached Newfoundland about 500 years earlier."),

    # --- the middle ages -----------------------------------------------------
    entry("castles", ("castle", ("build", "built", "why", "start", "first", "why castles")),
          "Castles were built as fortified homes, not just forts: a lord needed somewhere his "
          "family could live that also held off raiders and rivals. The Normans brought them to "
          "England in 1066, first as quick earth-and-timber mounds, then in stone."),
    entry("magna-carta", ("magna carta", ("what", "when", "1215", "why", "king john")),
          "Magna Carta was a charter King John was forced to seal at Runnymede in 1215. It "
          "limited the king's power over his barons and is remembered because it put in writing "
          "that even the monarch is under the law."),
    entry("hundred-years-war", (("hundred years war", "hundred years"), ("long", "last", "how", "really",
                                                                       "when", "date", "start")),
          "The Hundred Years War actually ran 116 years, from 1337 to 1453, between England and "
          "France. It was not one continuous war but a series of campaigns, and it ended with "
          "England losing everything except Calais."),
    entry("black-death", (("black death", "bubonic plague", "the plague", "plague", "pestilence"),
                          ("what", "when", "1348", "kill", "england",
                                                             "spread", "how", "why", "rats", "fleas",
                                                             "stop", "end")),
          "The Black Death reached England in 1348 and killed perhaps a third to a half of "
          "Europe's people within a few years. It was bubonic plague, spread by fleas on rats "
          "and by coughing between people, and it burned out by the early 1350s: so many had "
          "died or recovered that it ran out of victims. It changed wages and land ownership for "
          "good, and the first forty-day ship quarantines came a generation later, at Ragusa in "
          "1377.",
          # "plague" alone is any plague, and a plague of locusts is a swarm: the bare word is
          # in the key because "what caused the plague" is how the Black Death is asked for,
          # so the other swarms are fenced here instead.
          avoid=("locust", "locusts", "frogs", "of locusts", "swarm", "swarms", "aphids")),
    entry("vikings", ("viking", ("who", "were", "raid", "when", "scandinavia", "norse")),
          "The Vikings were Norse traders, farmers and raiders from Denmark, Norway and Sweden "
          "who were active from about 793 to 1066. They raided monasteries but also traded, "
          "settled and founded towns as far apart as Dublin, Kiev and Newfoundland."),

    # --- the early modern world ---------------------------------------------
    entry("printing-press", (("printing press", "printing"), ("invent", "gutenberg", "when", "who", "1440")),
          "Johannes Gutenberg built the movable-type printing press in Mainz around 1440, and "
          "the first major book he printed was the Bible. Printing made copies cheap, which is "
          "what carried the Reformation and modern science across Europe."),
    entry("renaissance", ("renaissance", ("what", "when", "why", "start", "italy")),
          "The Renaissance was the revival of art, learning and science in Europe from roughly "
          "1400 to 1600, starting in the rich Italian city-states. It looked back to ancient "
          "Greece and Rome and put human experience, not just religion, at the centre."),
    entry("shakespeare", ("shakespeare", ("who", "was", "plays", "when", "wrote")),
          "William Shakespeare was an English playwright and poet, born in Stratford-upon-Avon in "
          "1564, who wrote about 39 plays including Hamlet, Macbeth and Romeo and Juliet. He "
          "worked in London from the 1590s and died in 1616."),
    entry("great-fire-london", (("great fire",), ("london", "1666", "when", "start", "how")),
          "The Great Fire of London broke out in a bakery on Pudding Lane on 2 September 1666 and "
          "burned for four days. It destroyed about 13,000 houses and St Paul's Cathedral, but "
          "official records list only a handful of deaths."),
    entry("gunpowder-plot", (("gunpowder plot", "bonfire night", "fifth of november",
                              "5th of november"), ("what", "1605", "guy fawkes", "why", "when")),
          "In 1605 a group of English Catholics, including Guy Fawkes, planned to blow up "
          "Parliament and King James I with barrels of gunpowder. The plot was discovered on 5 "
          "November, which is why Britain still has bonfire night."),
    entry("french-revolution", (("french revolution",), ("what", "why", "when", "1789", "start")),
          "The French Revolution began in 1789, when a bankrupt monarchy faced a hungry, "
          "taxed-out country and the Bastille was stormed on 14 July. It ended the monarchy, "
          "executed Louis XVI and Marie Antoinette, and spread the ideas of liberty and equality."),
    entry("the-reformation", (("reformation", "protestant reformation"),
                              ("what", "was", "when", "why", "1517", "luther", "cause", "causes",
                               "about", "start", "started", "begin", "began")),
          "The Reformation was the break-up of western Christianity in the 1500s. Martin Luther "
          "nailed his 95 complaints about the Church to a church door in Wittenberg in 1517, "
          "printing spread them across Europe, and the countries that followed him became "
          "Protestant. Henry VIII made England one of them in 1533, for reasons of his own."),
    # The three ages and the Middle Ages: each was "Ageing is the slow build-up of small
    # damage" (the ageing row's stem is "age") or a hedge. The Stone Age line is the one people
    # send most, so it carries where farming and writing come in.
    entry("stone-age", (("stone age", "palaeolithic", "palaeolithic", "neolithic", "mesolithic"),
                        ("what", "was", "when", "life", "people", "tools", "about", "end")),
          "The Stone Age is the long stretch of prehistory when people made their tools from "
          "stone: it starts with the first toolmakers over two million years ago and ends "
          "where farming and metalwork begin, around 4,000 BC in Britain. It covers most of "
          "human history, and it ends at different dates in different places."),
    entry("bronze-age", (("bronze age",), ("what", "was", "when", "people", "about", "end")),
          "The Bronze Age is when people learned to mix copper with tin to make bronze, from "
          "about 3,300 BC in the Middle East and about 2,200 BC in Britain. Bronze made better "
          "tools and weapons, trade grew to fetch the metals, and it ends around 800 BC in "
          "Britain, when ironworking took over."),
    entry("iron-age", (("iron age",), ("what", "was", "when", "people", "about", "end")),
          "The Iron Age is when iron replaced bronze for tools and weapons, from about 1,200 BC "
          "in the Middle East and 800 BC in Britain, where it ends with the Roman invasion in "
          "43 AD. Iron ore is common and iron is harder, so farms and fighting changed; most of "
          "the hill forts you can walk round are Iron Age."),
    entry("middle-ages", (("middle ages", "medieval", "mediaeval", "the medieval period"),
                          ("what", "was", "were", "when", "life", "about", "end", "start")),
          "The Middle Ages are the centuries between the fall of Rome and the Renaissance, "
          "roughly 500 to 1500, and in England they start with the Norman Conquest in 1066. "
          "Most people farmed, the Church ran schools and hospitals, and castles, cathedrals "
          "and the first universities were built."),
    # "d-day" as it is typed, plus the name the landings have on a map. The Beaches have their
    # own cards, so this one is the "what was it" answer.
    entry("d-day", (("d-day", "d day", "operation overlord", "normandy landings",
                     "normandy landing"),
                    ("what", "was", "when", "1944", "landing", "landings", "invasion", "about")),
          "D-Day was 6 June 1944, when about 156,000 Allied troops landed on five beaches in "
          "Normandy in northern France: Utah, Omaha, Gold, Juno and Sword. It opened the western "
          "front against Germany and by the end of August Paris was free."),
    entry("roaring-twenties", (("roaring twenties", "roaring 20s", "the twenties", "the 1920s",
                                "1920s", "jazz age"),
                               ("what", "was", "were", "when", "why", "about", "1920", "like")),
          "The Roaring Twenties were the 1920s in America: jazz, cinemas, cars, radios and short "
          "skirts, on borrowed money and with drink banned by Prohibition. It ended with the Wall "
          "Street crash of October 1929 and the Depression that followed."),
    entry("great-famine", (("potato famine", "irish famine", "great famine", "great hunger"),
                           ("what", "was", "when", "ireland", "irish", "1845", "cause", "causes",
                            "about", "why")),
          "The Great Famine was Ireland's potato blight years, 1845 to 1852. About a million "
          "people died of hunger and disease and another million emigrated, so the population "
          "fell by roughly a quarter and never recovered."),
    # The subject has to be the American word and the ask the independence word: with it the
    # other way round, "become independent" reached this row for India and answered 1776.
    entry("american-independence", (("american independence", "declaration of independence",
                                     "america", "american", "usa", "united states", "the colonies",
                                     "1776"),
                                    ("independence", "independent", "declaration of independence",
                                     "declare independence", "declared independence",
                                     "become independent", "became independent",
                                     "get independence", "gained independence", "1776")),
          "The American colonies declared independence from Britain on 4 July 1776, and won it "
          "after fighting until 1783. The Declaration's argument, that governments rule by the "
          "consent of the governed, is why the date still matters."),

    # --- the modern world ----------------------------------------------------
    entry("industrial-revolution", (("industrial revolution", "industrialisation"), ("what", "when", "start", "britain", "factory", "machine")),
          "The Industrial Revolution was the switch from hand tools and farms to machines and "
          "factories, starting in Britain around 1760. Steam power, coal and iron moved millions "
          "of people into cities and made goods cheap enough for ordinary homes."),
    entry("telephone", (("telephone", "phone"), ("invent", "invented", "invention", "bell", "1876")),
          "Alexander Graham Bell is credited with inventing the telephone and got the key patent "
          "in 1876, though Antonio Meucci had demonstrated a working voice device years earlier. "
          "Bell's patent, and the company built on it, is why his name stuck."),
    entry("ww1-start", (("world war one", "world war 1", "ww1", "first world war"),
                         ("start", "started", "why", "1914", "begin", "caused", "cause",
                          "causes")),
          "World War One began in 1914 after the heir to the Austro-Hungarian throne, Archduke "
          "Franz Ferdinand, was assassinated in Sarajevo. Alliances then pulled the great powers "
          "in: Austria attacked Serbia, Russia mobilised, and Germany declared war on Russia and "
          "France.",
          # "How should I start an essay about the causes of the First World War?" is a study
          # question and the facts above are not the answer to it: a line that says essay,
          # coursework or revision is asking how to write, so this row keeps out of it.
          avoid=("essay", "essays", "coursework", "assignment", "dissertation", "paragraph",
                 "paragraphs", "revise", "revision", "homework", "exam", "question paper"),
          # "when did the first world war start" is the start row's, and the end row reads "when"
          # too: with the end row at two, the start row has to be read as strongly or the first
          # question anyone asks about the war gets the armistice.
          bias=2),
    entry("ww1-end", (("world war one", "world war 1", "ww1", "first world war"),
                       ("end", "ended", "when", "1918", "armistice")),
          "World War One ended with the armistice on 11 November 1918, at 11am. The fighting "
          "stopped on the Western Front that morning, though the peace treaty was not signed "
          "until the following June.",
          avoid=("essay", "essays", "coursework", "assignment", "dissertation", "paragraph",
                 "paragraphs", "revise", "revision", "homework", "exam", "question paper"),
          # "how did the first world war end" and "what ended the first world war" scored the same
          # as the essay row, whose key reads "ending" as "end": a line that names the war and asks
          # how it ended is history, and the name is worth more than a tie. The number is worth
          # less than the name ("ww1" is one word where "first world war" is three), so the tie is
          # broken at two, for the lines said the short way round.
          bias=2),
    entry("ww2-start", (("world war two", "world war 2", "ww2", "second world war"),
                         ("start", "started", "why", "1939", "begin", "caused", "cause",
                          "causes")),
          "World War Two began in Europe on 1 September 1939, when Germany invaded Poland; "
          "Britain and France declared war two days later. Japan had already been at war with "
          "China since 1937, and the United States joined in December 1941 after Pearl Harbor.",
          avoid=("essay", "essays", "coursework", "assignment", "dissertation", "paragraph",
                 "paragraphs", "revise", "revision", "homework", "exam", "question paper"),
          bias=2),
    entry("ww2-end", (("world war two", "world war 2", "ww2", "second world war"),
                       ("end", "ended", "when", "1945", "over")),
          "World War Two in Europe ended on 8 May 1945, when Germany surrendered; Japan "
          "surrendered on 15 August after the atomic bombs, signing on 2 September. That autumn "
          "is when the war was finally over worldwide.",
          avoid=("essay", "essays", "coursework", "assignment", "dissertation", "paragraph",
                 "paragraphs", "revise", "revision", "homework", "exam", "question paper"),
          bias=2),
    # When it was built is a different year from when it sank, and "when" was enough to make
    # "when was the titanic built" the sinking: the sinking now refuses the building words, and
    # the building entry below answers them.
    entry("titanic", ("titanic", ("sink", "sank", "sinking", "sunk", "1912", "why", "hit",
                                  "iceberg", "who died",
                                  # the death toll is in this text, and "how many died on the
                                  # titanic" was a shrug beside it.
                                  "died", "deaths", "death toll", "how many died")),
          "Titanic struck an iceberg late on 14 April 1912 and sank in the early hours of 15 "
          "April, about 400 miles off Newfoundland. More than 1,500 people died, largely "
          "because there were far too few lifeboats for the 2,200 aboard.",
          avoid=("built", "build", "building", "launched", "launch", "constructed",
                 "how long to build", "who built", "made", "sail", "sailed", "set sail",
                 "depart", "departed")),
    # The lifeboat count is a question about a number, and the sinking text has its answer in
    # the middle of a paragraph: "how many lifeboats were on the titanic" got the sinking, which
    # never says how many, so the count is its own entry and it opens with the number.
    entry("titanic-lifeboats", ("titanic", ("lifeboats", "lifeboat", "life boats", "life boat",
                                            "boats", "how many lifeboats", "lifeboat count")),
          "Twenty: fourteen wooden lifeboats, two emergency cutters and four collapsible boats, "
          "with room for about 1,180 people, barely half of the 2,200 aboard. Every boat that got "
          "away went half empty, and that shortage is the reason more than 1,500 people died.",
          avoid=("sink", "sank", "sinking", "sunk", "iceberg", "why", "built", "build",
                 "launched", "how many died", "died", "died on the titanic")),
    # "when did the titanic sail" is a date question like "when was it built", and it belongs to
    # the entry whose text carries 10 April 1912 rather than to the night it sank.
    entry("titanic-built", ("titanic", ("built", "build", "building", "launched", "launch",
                                        "constructed", "how long to build", "who built",
                                        "sail", "sailed", "set sail", "depart", "departed")),
          "Titanic was built in Belfast by Harland and Wolff: laid down in March 1909, launched "
          "on 31 May 1911, and fitted out for another ten months before she sailed on 10 April "
          "1912. About 3,000 men worked on her, and the hull took roughly two years.",
          avoid=("sink", "sank", "sinking", "sunk", "iceberg", "lifeboats", "died")),
    # how and when it ended is "cold-war-end", and that card says it better: this one keeps the
    # winner, which nothing else answers.
    entry("cold-war", (("cold war",), ("what", "about", "why", "usa", "soviet", "russia", "when",
                                       "won", "win", "winner", "beat", "victor")),
          _cold_war, avoid=("end", "ended", "ending", "collapse", "collapsed", "over"), explain=True),
    # "why"/"when" belong to the wall going up ("berlin-wall-built", below); keeping them here
    # made "why was the berlin wall built" answer the coming-down, which is a different event.
    entry("berlin-wall", (("berlin wall",), ("fall", "fell", "came down", "come down", "coming down",
                                                "torn down", "1989", "happened", "still there")),
          "The Berlin Wall came down on the night of 9 November 1989, after mass protests across "
          "East Germany and a border announcement that was misread as immediate. Crowds crossed "
          "and began pulling the wall apart; Germany reunited the following year."),
    entry("moon-landing", (("moon", "landing"), ("apollo", "1969", "armstrong", "land", "landed", "landing",
                                             "walk", "step", "first", "person", "who")),
          "Apollo 11 landed on the Moon on 20 July 1969. Neil Armstrong and Buzz Aldrin walked "
          "on the surface while Michael Collins stayed in orbit; Armstrong's first step was the "
          "one everyone remembers."),
    entry("first-in-space", ("space", ("gagarin", "1961", "first", "person", "who", "orbit")),
          "Yuri Gagarin was the first person in space, on 12 April 1961, in the Soviet Vostok 1 "
          "capsule. He made one orbit of the Earth and came back down by parachute after ejecting, "
          "just under two hours after launch."),
    entry("mandela", ("mandela", ("who", "was", "apartheid", "south africa", "prison")),
          "Nelson Mandela was a South African lawyer and anti-apartheid leader who spent 27 years "
          "in prison before becoming the country's first black president in 1994. He shared the "
          "Nobel Peace Prize in 1993 for negotiating the end of apartheid peacefully."),

    # --- the vote, the empire's end, and the first things ever written --------
    # "when did women get the vote" is how nearly everyone asks this, and nobody types the word
    # in the key: the vote itself is the subject, so it is in the first part with the movement's
    # names. The second part still wants a question word or one of the names, so a line that
    # only says "vote" ("how do i vote in the general election") stays out.
    entry("suffragettes",
          (("suffragettes", "suffrage", "votes for women", "womens vote", "women vote",
            "vote", "votes"),
           ("who", "when", "what", "why"),
           ("vote", "votes", "women", "movement", "pankhurst")),
          "The campaign for women's votes split into the peaceful suffragists and the militant "
          "suffragettes led by Emmeline Pankhurst. In Britain, women over 30 with property got the "
          "vote in 1918, and all women over 21 in 1928.",
          # "when did women get the vote" never says *suffragette*, so the vote itself is a
          # first-part word. That alone would take "when do i vote" and "who can vote in the uk",
          # which are the register-to-vote question or a shrug: this row is history, so it wants
          # the historical shape of the ask.
          ask=("when did", "when was", "when were", "what year", "which year", "when could",
               "when couldn", "suffragettes", "suffrage", "history", "first get the vote",
               "win the vote", "won the vote", "got the vote"),
          # One country's history and one sex's campaign, and the guard below is what says so.
          # "when did men get the vote" and "when did women get the vote in america" are ordinary
          # things to ask, and each was answered here with 1918 and 1928 - a confident answer to
          # a different question is worse than the hedge it replaced.
          avoid=("men", "man", "mens", "male", "males", "working men", "white men", "everyone",
                 "black", "african", "america", "american"),
          guard=_not_the_other_sex_or_country),
    # The same question about the other half of the franchise, and the row above steps aside for
    # it: "when did men get the vote" and "when did poor people get the vote" were the hedge on
    # main, and the answer is the same list of dates the women's row has, from the other side.
    # Property is the whole story of the poor, so the dates are the Reform Acts.
    entry("the-franchise",
          (("vote", "votes", "franchise"),
           ("men", "man", "mens", "male", "males", "poor", "working class", "working",
            "labourers", "laborers", "everyone", "people")),
          "The vote came in steps and property was the bar: after the 1832 Reform Act about one "
          "man in five could vote, 1867 reached skilled town workers (about one in three), 1884 "
          "reached farm labourers (about two in three), and in 1918 every man over 21 got the "
          "vote whatever he owned, at the same time as women over 30. Women got it on the same "
          "terms as men in 1928.",
          # A date question about a group, not a request for an opinion: "should i vote" and
          # "how do i register to vote" are somebody else's question and stay out.
          ask=("when did", "when was", "when were", "when could", "when couldn", "what year",
               "which year", "history", "first get the vote", "got the vote", "win the vote"),
          # One country's franchise and the groups it is about. A women line is the row above,
          # a black or colonial line is another history, and an age line (1969) is another again.
          avoid=("women", "womens", "woman", "female", "females", "suffragette", "suffrage",
                 "black", "slave", "slaves", "slavery", "immigrant", "immigrants",
                 "america", "american", "usa", "united states", " the us", "canada",
                 "australia", "india", "france", "germany", "18", "16", "17", "21", "old",
                 "age", "aged", "young", "teen", "teenager", "local", "council",
                 "general election", "register")),
    # The other end of the same history, and the row above steps aside for the age words: "when
    # did 18 year olds get the vote" was the hedge on main, and the answer is one date and one
    # line about where 16-year-olds stand now.
    entry("vote-at-18",
          (("vote", "votes", "voting age"), ("18", "eighteen", "16", "sixteen", "vote at")),
          "The voting age in Britain came down from 21 to 18 in 1969. It has not gone lower for a "
          "UK general election, though 16-year-olds can vote in the Scottish Parliament and the "
          "Senedd elections in Wales.",
          ask=("when did", "when was", "when were", "when could", "what year", "which year",
               "when can", "should", "lower", "lowered"),
          # A line about the age someone votes is this row; an age inside a women's or a men's
          # line ("women over 30") is the other history, and a pension or a driving line is not
          # this one at all.
          avoid=("women", "womens", "woman", "female", "men over", "suffragette", "suffrage",
                 "america", "american", "usa", "united states", "canada", "australia", "india",
                 "driving", "drive", "pension", "retire", "retirement", "alcohol", "drink"),
          ),
    # The same question about another country's franchise, which the row above now stands aside
    # for: "when did black people get the vote" was the hedge on main, and it has two dates that
    # matter - the amendment and the year the South stopped keeping them off the roll.
    entry("black-vote",
          (("vote", "votes", "voting", "franchise"),
           ("black", "african american", "african americans")),
          "In law, black men in the United States got the vote in 1870 with the 15th Amendment, "
          "and black women with the 19th in 1920, but in the South poll taxes, literacy tests and "
          "violence kept most of them off the roll until the Voting Rights Act of 1965. In South "
          "Africa everyone of every race voted for the first time in 1994.",
          ask=("when did", "when was", "when were", "when could", "what year", "which year",
               "got the vote", "get the vote", "win the vote", "first vote"),
          # A British suffragist line and a South African apartheid line are the two rows either
          # side of this one, and a register-to-vote line is not history at all.
          avoid=("suffragette", "suffragettes", "suffrage", "pankhurst",
                 "apartheid", "mandela", "register", "registration",
                 "general election", "local"),
          ),
    # "when did the voting age change" and "was the voting age 21" were a search hedge, and the
    # row above does not reach them: it keys the ages themselves ("18 year old", "vote at 16")
    # and it stands aside on the word "age". This row is the phrase the question is actually
    # asked in - *the voting age* - and the guard keeps it on the change, so "what is the voting
    # age" still gets the franchise card in lifeadmin (the age today), not the history.
    entry("the-voting-age-changed",
          (("voting age", "vote aged", "votes aged", "age to vote", "old to vote"),
           ("vote", "votes", "voting", "election", "elections", "referendum")),
          "The voting age in the UK came down from 21 to 18 in 1969, under the Representation of "
          "the People Act 1969, and the first general election 18-year-olds could vote in was "
          "1970. Scotland and Wales let 16 and 17-year-olds vote in their own elections from 2015 "
          "and 2020; England and Northern Ireland still start at 18.",
          ask=("when", "year", "history", "change", "changed", "used to", "came down"),
          # the age rows either side of this one own the ages, and a sixteen-year-old with a job
          # or a bank account is not asking about the franchise
          avoid=("18 year old", "16 year old", "eighteen", "sixteen", "women", "womens", "woman",
                 "suffragette", "suffragettes", "suffrage", "men", "mens", "pankhurst",
                 "job", "jobs", "work", "bank", "account", "benefit", "benefits", "tax",
                 "apprentice", "apprenticeship", "driving", "drive", "car", "holiday"),
          guard=_about_the_change),
    entry("ottoman-empire", ("ottoman", ("empire", "sultan", "sultans", "istanbul", "turkey",
                                         "1300", "1922")),
          "A state that began in Anatolia around 1300 and grew to cover the Balkans, the Middle "
          "East and north Africa, ruled from Istanbul. It fought alongside Germany in the First "
          "World War and broke up in 1922, replaced by modern Turkey."),
    entry("apartheid", ("apartheid", ("who", "what", "when", "why", "end", "ended"),
                        ("south africa", "segregation")),
          "The system of racial segregation enforced in South Africa from 1948 to 1994, which kept "
          "black South Africans out of land, schools and votes. Nelson Mandela was released in "
          "1990 after 27 years in prison and became president in 1994."),
    entry("first-writing", ("writing", ("invented", "invent", "invention", "cuneiform",
                                        "mesopotamia", "sumer", "sumerians")),
          "Writing began around 3200 BC in Mesopotamia, as marks for accounting: quantities of "
          "grain and sheep. Independent systems appeared later in Egypt, China and Mesoamerica.", explain=True),
    entry("crusades", ("crusades", "crusade", "crusaders",
                       ("who", "what", "when", "why", "happen", "happened", "jerusalem")),
          "A series of religious wars from 1096 to the late 1200s, called by the papacy to take "
          "control of holy sites in the Middle East. The First Crusade captured Jerusalem in 1099; "
          "the rest largely failed, and the trade and ideas that moved both ways mattered as much "
          "as the fighting.", explain=True),
    entry("ancient-egypt-mummification", ("mummies", "mummification", "mummify", "mummified",
                                          ("egypt", "egyptians", "em-balming", "body", "bodies")),
          "Egyptians removed the organs, dried the body with salt for about 40 days, then wrapped "
          "it in linen with amulets between the layers. They kept the heart, which they believed "
          "was weighed against a feather in the afterlife.", explain=True),
    # --- the Tudors, which is a school question before it is a history one -------------
    entry("henry-viii", (("henry viii", "henry the eighth", "henry 8th", "henry the 8th"),
                         ("who", "was", "what", "did", "wives", "wife", "tudor", "do",
                          "six", "reformation", "church", "tell", "about", "known", "famous",
                          "remembered", "story")),
          "Henry VIII (1491-1547) was king of England from 1509 and is remembered for two things: "
          "six wives and the break with Rome. He wanted his first marriage annulled so he could "
          "marry Anne Boleyn, the Pope refused, and in 1533 he made himself head of the Church of "
          "England and closed the monasteries. Two of the six wives were executed, two divorced or "
          "annulled, one died in childbirth, and Catherine Parr outlived him. His children were "
          "Edward VI, Mary I and Elizabeth I, who was his daughter by Anne Boleyn."),
    entry("tudors", (("tudor", "tudors", "tudor dynasty"),
                     ("who", "what", "when", "were", "was", "dynasty", "kings", "queens",
                      "mean", "means", "family", "power", "rise", "start", "started",
                      "come", "came", "how")),
          "The Tudors took the crown when Henry Tudor beat Richard III at Bosworth in 1485, and "
          "held it until 1603: Henry VII, Henry VIII, Edward VI, Lady Jane Grey for nine days, "
          "Mary I and Elizabeth I. It was the century of the Reformation in England, the Armada, "
          "Shakespeare and the first voyages to America, and it ended when Elizabeth died "
          "childless and the Stuarts took over.", explain=True),

    # --- the bits of British and European history people ask for by name ------------
    entry("romans-left-britain", ("roman", ("britain", "leave", "left", "leaving", "410")),
          "The legions went in 410 AD, when Rome pulled its soldiers home to defend Italy and the "
          "emperor told the Britons to look to their own defences. Raids from Angles, Saxons and "
          "Jutes turned into settlement, and Roman towns and villas fell out of use within a "
          "generation or two.",
          # The duration question is the entry below ("nearly 400 years"). Only the duration
          # *shapes* are guarded here: a bare "year" is how the date question is put
          # ("what year did the romans leave"), and blocking it dropped that line to the hedge.
          # "britain" in the key above means this row also matches "what did the romans do for
          # britain", which is the in-britain row's line: the doing words are held off it here.
          avoid=("how long", "how many years", "for how many years", "how many centuries",
                 "do for", "did for", "do in britain", "did in britain", "build", "built",
                 "bring", "brought", "give", "gave", "roads", "baths", "towns")),
    entry("battle-hastings", (("hastings", "1066"), ("when", "battle", "william", "harold",
                                                      "happened", "why", "invasion", "norman")),
          "The Battle of Hastings was fought on 14 October 1066: William of Normandy beat King "
          "Harold, who was killed on the field, and was crowned on Christmas Day. It was the last "
          "successful invasion of England, and it replaced the English ruling class with a Norman "
          "one."),
    entry("trafalgar", ("trafalgar", ("when", "battle", "nelson", "happened", "who", "1805",
                                      "fought", "won")),
          "The Battle of Trafalgar was fought on 21 October 1805, when Nelson's fleet beat the "
          "French and Spanish off Cape Trafalgar and destroyed the fleet that was meant to cover "
          "an invasion of Britain. The invasion barges at Boulogne never sailed. "
          "Nelson was shot on his own deck and died that afternoon, and the victory is the one in "
          "the Trafalgar Square column."),
    entry("napoleon", ("napoleon", ("who", "was", "when", "what", "bonaparte")),
          "Napoleon Bonaparte (1769-1821) took power in France in 1799 and made himself emperor in "
          "1804, then beat most of Europe until the Russian winter and Waterloo in 1815 finished "
          "him. His civil code is still the base of law in much of Europe, and the British "
          "obsession with him is why we still read about Trafalgar."),
    entry("the-blitz", (("blitz", "the blitz"), ("what", "was", "when", "london", "bombing")),
          "The Blitz was the German bombing of British cities from September 1940 to May 1941, "
          "starting with 57 nights of raids on London. About 40,000 people were killed across the "
          "country, and the bombing never broke either the factories or the will to keep going."),
    # A Victorian house is an era, but a question about the building wants the building.
    entry("victorian-era", ("victorian", ("when", "era", "was", "start", "end")),
          "The Victorian era ran from 1837 to 1901, the years Queen Victoria was on the throne: "
          "railways, factories, the vote slowly widening, and an empire at its widest. Victoria "
          "herself reigned 63 years, longer than anyone before Elizabeth II.",
          avoid=("house", "houses", "building", "architecture", "terrace", "chimney", "fireplace",
                 "brick")),
    # "who is victoria beckham" is not the queen: the question has to say queen or reign.
    entry("queen-victoria", ("victoria", ("queen", "reign", "reigned", "throne")),
          "Queen Victoria reigned from 1837 to 1901, 63 years, and gave her name to the age. She "
          "had nine children, married Prince Albert, and after he died in 1861 spent years in "
          "mourning, which is why so many photos of her look the way they do."),
    # "who was the prime minister in ww2" names him without the name, and the table below leaves
    # Churchill to this row, which has the dates and the second term the table's line has not.
    entry("churchill", (("churchill", "prime minister in ww2", "prime minister during ww2",
                         "prime minister in world war two", "wartime prime minister",
                         "prime minister in the war"),
                        ("who", "was", "when", "what", "winston")),
          "Winston Churchill (1874-1965) was Britain's prime minister for most of World War Two, "
          "from 1940 to 1945, and again from 1951 to 1955. His speeches in 1940 held the country "
          "together in the year it stood alone, and he was voted out before the war in the Pacific "
          "had even ended."),
    # Bare "versailles" answered "what should i see at versailles" with the treaty, so the
    # treaty has to be named.
    entry("treaty-of-versailles", (("treaty of versailles", "versailles treaty"),
                                   ("what", "when", "why", "1919", "germany", "signed", "terms",
                                    "blame", "harsh")),
          "The Treaty of Versailles was signed in June 1919 and set the peace terms with Germany "
          "after World War One: it accepted German guilt, cut the army to 100,000 men and demanded "
          "reparations. The terms were seen as harsh in Germany and were used by later politicians "
          "to stir resentment."),
    entry("chernobyl", ("chernobyl", ("what", "when", "happened", "why", "1986", "explode")),
          "Reactor 4 at Chernobyl exploded on 26 April 1986 during an overnight safety test, and "
          "the graphite fire burned for days, spreading radiation across Europe. About 30 workers "
          "and firefighters died of acute radiation within weeks, and the 30km exclusion zone is "
          "still there."),
    entry("holocaust", ("holocaust", ("what", "was", "when", "why", "happened")),
          "The Holocaust was Nazi Germany's systematic murder of about six million Jews between "
          "1941 and 1945, along with Roma, disabled people, gay people and others they classed as "
          "enemies. It was organised by the state: round-ups, ghettos, mass shootings and the "
          "death camps in occupied Poland such as Auschwitz."),
    entry("julius-caesar", ("caesar", ("julius", "who", "was", "when", "what", "assassinated",
                                       "stabbed", "roman", "rome", "emperor", "ides", "rubicon")),
          "Julius Caesar (100-44 BC) was the Roman general who conquered Gaul, crossed the Rubicon "
          "in 49 BC and made himself dictator for life. A group of senators stabbed him to death on "
          "15 March 44 BC, and the republic never recovered from it.",
          # phrases, so the typo guard cannot widen them to other words
          avoid=("caesar salad", "caesar dressing", "salad dressing", "romaine", "croutons",
                 "little caesars", "caesars palace", "augustus")),
    # "when" is not in this key: it belongs to "when did the Roman Empire fall", which has its
    # own entry above.
    entry("roman-empire-start", (("roman empire", "rome"), ("start", "started", "begin", "began",
                                                           "first emperor", "augustus", "27 bc"),
                                ),
          "The Roman Empire is usually dated from 27 BC, when Octavian took the name Augustus and "
          "became the first emperor, though the republic had already been falling apart for "
          "decades. Rome itself was founded, by tradition, in 753 BC, which is why the years "
          "before 27 BC are dated from it.",
          # "im going to rome where do i start" is a trip: the bare "start" above took it and
          # answered with 27 BC. The history is asked as "how did rome start", never as "where
          # do i start" on the way there.
          avoid=("where do i start", "where to start", "where should i start", "going to",
                 "go to rome", "trip", "holiday", "visit", "visiting", "itinerary", "flight",
                 "hotel", "stay in", "days in", "things to do", "pack", "restaurant")),
    # "when did the romans first come to britain" is the arrival, and the duration and the
    # leaving are separate rows that share "roman" and "britain" with it.
    # "britain" is deliberately not in the key: the subject is already the Romans, and a second
    # part holding the place made this row answer "what did the romans build in britain" with the
    # date they arrived. The arrival is the when/first/come words and the year itself.
    entry("romans-invade-britain", (("romans", "roman"), ("when", "first", "come", "came",
                                                          "first come", "invade", "invaded",
                                                          "invasion", "arrive", "arrived",
                                                          "43", "43 ad", "claudius", "start",
                                                          "started")),
          "Julius Caesar raided Britain in 55 and 54 BC and left, and the invasion that stuck came "
          "in 43 AD under the emperor Claudius; most of England and Wales was Roman within a few "
          "decades. The legions stayed until 410, when Rome pulled them home.",
          # It has to beat two rows that share "roman"+"britain" with it, so the arrival words
          # are worth more here than on a lone row.
          bias=2,
          avoid=("leave", "left", "leaving", "long", "years", "centuries", "do for", "give",
                 "brought", "roads", "empire", "fall", "fell")),
    entry("space-race", ("space race", ("what", "was", "when", "why", "about")),
          "The space race was the contest between the Soviet Union and the United States from 1957 "
          "to 1969: Sputnik first, then Gagarin in orbit, then Apollo 11 on the Moon. It was "
          "politics with rockets, and most of the technology that followed came out of it."),
    entry("america-joins-ww2", (("america", "usa", "united states", "americans"),
                                ("ww2", "world war 2", "world war two", "world war ii",
                                 "pearl harbor", "pearl harbour",
                                 # "how do i enter america" is a visa question, so entering has
                                 # to be entering the war:
                                 "enter the war", "entered the war", "join the war",
                                 "joined the war", "enter ww2", "join ww2", "entered ww2")),
          "Japan attacked the US fleet at Pearl Harbor on 7 December 1941 and America declared war "
          "the next day; Germany declared war on America on 11 December. Until then the US had been "
          "lending Britain and Russia weapons, which is why it was already fighting in all but "
          "name.", bias=1),
    entry("aztecs", ("aztecs", "aztec", ("who", "were", "when", "what", "live", "lived", "mexico")),
          "The Aztecs ruled central Mexico from their city Tenochtitlan, which was built on an "
          "island in a lake and was home to 200,000 people by 1500. They farmed the lake on floating "
          "plots and paid for everything in tribute and human sacrifice, and Spanish forces under "
          "Cortes took the city in 1521."),
    entry("silk-road", ("silk road", ("what", "was", "when", "why", "trade")),
          "The Silk Road was not a road but a chain of trade routes between China and the "
          "Mediterranean, busiest from about 200 BC to 1400 AD. Silk went west and horses, glass and "
          "wool went east, and so did religions, paper-making and plagues."),
    entry("gandhi", ("gandhi", ("who", "was", "when", "what", "india")),
          "Mohandas Gandhi (1869-1948) led India's independence movement through non-violent "
          "protest, most famously the 1930 Salt March, and India was free in 1947. He was "
          "assassinated in January 1948, before the new country had settled."),
    entry("great-depression", (("great depression", "wall street crash"), ("what", "was", "when",
                                                                         "why", "cause", "caused")),
          "The Great Depression began with the Wall Street crash in October 1929 and lasted through "
          "the 1930s, with a third of American workers out of a job at its worst. Banks failed, "
          "prices fell, and trade shrank because every country tried to save itself alone."),
    # "when did slavery end in america" is 1865, so this entry only answers for Britain.
    entry("slavery-abolished", (("slavery", "slave trade", "abolition"),
                                ("britain", "british", "uk", "england", "english", "1833", "1807",
                                 "1834", "empire")),
          "Britain outlawed the slave trade in 1807 and slavery itself in the colonies in 1833, in "
          "force from 1 August 1834. The government paid 20 million pounds to the slave owners, "
          "about 40 percent of the state budget, and nothing to the enslaved people."),
    # Bare "civil war" answered the Spanish civil war, so an American word has to be there.
    entry("american-civil-war", (("american civil war", "the civil war", "us civil war", "1861"),
                                 ("what", "started", "why", "when", "about", "cause", "lincoln",
                                  "slavery", "south", "north", "1865")),
          "The American Civil War ran from 1861 to 1865, when eleven southern states left the Union "
          "rather than accept limits on slavery. The north blocked the ports with its navy, the "
          "slaves along the Mississippi were freed, and the war ended in April 1865 with about "
          "620,000 dead."),
    entry("kingdom-vs-empire", ("kingdom", ("empire", "difference", "between")),
          "An empire is one state ruling other peoples and places beyond its own borders, usually "
          "taken by force and governed from the centre; a kingdom is one country under a king or "
          "queen. Empires rarely last more than a few hundred years, because the parts stop needing "
          "the centre."),

    # --- a second pass: the events people ask about by name and never got --------------
    entry("cromwell", ("cromwell", ("who", "was", "what", "when", "oliver")),
          "Oliver Cromwell (1599-1658) was the parliamentary general who beat Charles I in the "
          "civil war; the king was executed in 1649. Cromwell then ruled as Lord Protector from "
          "1653 until his death, and his son lasted less than a year before the monarchy came "
          "back in 1660."),
    entry("norman-conquest", (("1066", "battle of hastings"), ("what", "happened", "when", "why",
                                                              "who", "invasion", "conquest")),
          "In 1066 Harold of England beat a Norwegian army at Stamford Bridge, then marched south and "
          "lost to William of Normandy at Hastings on 14 October, the last time England was "
          "conquered. William was crowned on Christmas Day, and within twenty years most of the "
          "English land had changed hands.",
          # "who won the battle of hastings" is the battle's own entry: this one is the wider
          # change that followed it, so the win belongs there.
          avoid=("how long", "how many years", "who won", "won", "winner", "beat", "defeated")),
    entry("elizabeth-i", (("elizabeth the first", "elizabeth i", "elizabeth 1st"),
                          ("who", "was", "when", "reign", "queen")),
          "Elizabeth I reigned from 1558 to 1603, the last Tudor: she settled the church, saw off "
          "the Armada in 1588, and never married, which is why the succession went to her cousin "
          "James of Scotland."),
    entry("martin-luther-king", (("martin luther king", "mlk"), ("who", "was", "when", "what",
                                                                "do", "did")),
          "Martin Luther King Jr (1929-1968) led the American civil rights movement without "
          "violence: the Montgomery bus boycott in 1955, the 1963 March on Washington, and the "
          "laws of 1964 and 1965 that ended legal segregation and barred the poll tax. He was "
          "shot in Memphis in April 1968."),
    entry("india-independence", (("india", "indian"), ("independence", "independent", "free",
                                                       "freedom", "1947", "partition")),
          "India became independent on 15 August 1947, and the country was split at the same time: "
          "Pakistan was created for Muslims, and the movement of people either way killed hundreds "
          "of thousands. Pakistan's own independence day is 14 August, a day earlier."),
    entry("iron-curtain", ("iron curtain", ("what", "was", "when", "why", "about")),
          "The Iron Curtain was the line dividing Soviet-controlled eastern Europe from the west "
          "from about 1945 to 1989. Churchill made the phrase famous in a speech in Fulton, "
          "Missouri, in March 1946, and the Berlin Wall was the most visible piece of it.", explain=True),
    # "who was the leader of germany in ww2" asks for the man without naming him.
    entry("hitler", (("hitler", "leader of germany in ww2", "german leader in ww2",
                      "leader of germany in world war two", "nazi leader", "fuhrer"),
                     ("who", "was", "what", "when")),
          "Adolf Hitler (1889-1945) led Nazi Germany from 1933 to 1945, started the Second World "
          "War, and ordered the Holocaust, in which about six million Jews were murdered along "
          "with Roma, disabled people and others. He killed himself in Berlin in April 1945 as "
          "the Soviet army reached the city.", explain=True),
    entry("battle-of-britain", ("battle of britain", ("what", "was", "when", "why", "won", "about")),
          "The Battle of Britain was fought in the air over southern England in the summer and "
          "autumn of 1940: the RAF against the Luftwaffe, with radar and ground control on the "
          "British side. Germany could not win the air superiority it needed to invade, so it "
          "turned to night bombing, and it was the first battle of the war that Germany lost.", explain=True),
    entry("spanish-armada", (("spanish armada", "armada"), ("what", "was", "when", "1588", "why",
                                                            "defeat", "defeated")),
          "The Spanish Armada was a fleet of about 130 ships sent by Philip II in 1588 to collect "
          "an army from the Netherlands and invade England. English fireships broke its formation "
          "at Calais, the fleet was driven north by the wind, and storms wrecked much of it on the "
          "way home.", explain=True),
    entry("tudor-end", (("tudor", "tudors", "elizabeth"), ("end", "ended", "finish", "last",
                                                           "lasted", "1603")),
          "The Tudor period ended in 1603, when Elizabeth I died without children and James VI of "
          "Scotland took the throne as James I. That joined the crowns of England and Scotland, "
          "though the two countries stayed separate until 1707.", bias=1),
    # "leave" stays with `romans-left-britain`, which answers it with the date in its first
    # sentence; the stay words ("stay", "long", "years", "centuries", "arrive") belong here,
    # because main answered "how long were the romans in britain" with the 410 answer, which never
    # says how long. "did" and "do" are what any "when did X happen in britain" line matches, so
    # the other dates in British history are named in the avoid list instead.
    entry("romans-in-britain", (("romans", "roman", "britain"), ("do", "did", "build", "built",
                                                                 "invade", "invaded", "roads",
                                                                 # "what were the romans famous
                                                                 # for" was a shrug, and the
                                                                 # towns and roads are the answer
                                                                 "famous", "famous for", "known for",
                                                                 "best known", "remembered for",
                                                                 "what did they do",
                                                                 "give", "bring", "stay", "stayed",
                                                                 "arrive", "arrived", "occupation",
                                                                 "long", "years", "centuries")),
          "The Romans held most of Britain for nearly 400 years and brought towns, straight roads, "
          "baths, central heating, stone buildings and writing. They never took the whole island "
          "(Hadrian's Wall was the northern edge), and the legions left in 410 to defend Italy, "
          "after which the towns emptied and the roads went back to mud.",
          # "leave" is a patent date question: the departure answer opens with 410 and this one
          # buries the date behind the towns and roads. `britain` alone already scores for both,
          # so only the avoid list can send those lines next door.
          avoid=("empire", "fall", "fell", "split", "collapse", "collapsed", "byzantine",
                 "leave", "leaves", "left", "leaving", "went home", "pulled out",
                 # every "in britain" question that is not about the Romans
                 "slavery", "slave", "slaves", "abolished", "abolition", "vote", "votes",
                 "suffragette", "suffragettes", "railway", "railways", "industrial", "tudor",
                 "victorians", "churchill", "brexit", "eu", "eec", "common market",
                 "first world war", "second world war", "ww1", "ww2", "norman", "hastings"),
          # this is the card for "the romans", so "tell me about the romans" is its question;
          # the dates and the departure keep their own rows, which say those in one sentence.
          explain=True),
    # Not "who": "who is the prime minister" asks about today, and the first one is 1721.
    # The reformer, not the civil rights leader: "who was martin luther" was "That part is
    # yours, not mine - I wasn't there", and MLK's row needs the whole name.
    entry("martin-luther", (("martin luther", "luther"), ("who", "was", "what", "did", "1517",
                                                          "theses", "reformation", "monk")),
          "Martin Luther (1483-1546) was a German monk and professor who in 1517 published 95 "
          "arguments against the Church selling forgiveness. Printing spread them across Europe, "
          "he was excommunicated, and the movement he started became Protestantism. He also "
          "translated the Bible into German, which shaped the modern language.",
          avoid=("king", "mlk", "civil rights", "i have a dream", "assassinated", "memphis",
                 "atlanta", "1963", "1968")),
    # "first" alone is not this row's word: it is a number in every "during the first world war"
    # line, so "who was the prime minister during the first world war" was answered with Walpole.
    # The row is about the first one as a thing in itself, and that is said as a phrase.
    entry("first-prime-minister", (("prime minister", "pm"),
                                   ("first prime minister", "first british prime minister",
                                    "first ever prime minister", "first pm", "walpole", "1721",
                                    "first one", "very first")),
          "Robert Walpole is counted as the first British prime minister: he ran the government "
          "from 1721 to 1742 and was called first lord of the treasury rather than prime minister, "
          "which was meant as an insult at the time.",
          avoid=("canada", "australia", "australian", "india", "indian", "israel", "zealand",
                 "france", "french", "germany", "german", "italy", "italian", "spain",
                 "spanish", "japan", "japanese", "ireland", "irish", "scotland", "scottish",
                 "wales", "welsh", "america", "american", "usa")),
    # "what was the berlin wall for" is the purpose question about the wall going up, and the
    # coming-down entry above answers a different event, so "for"/"purpose" belong here.
    entry("berlin-wall-built", ("berlin wall", ("built", "build", "up", "go up", "went up",
                                                "1961", "why", "for", "purpose", "point",
                                                "put up", "used",
                                                # the plainest way to ask, and the one that was a
                                                # search hedge once the phrase row stopped reading
                                                # the English "was" as German
                                                "what", "was", "what was", "tell me about")),
          "The Berlin Wall went up on the night of 13 August 1961, when East Germany sealed the "
          "border through the city with barbed wire and then concrete, to stop people leaving for "
          "the west. It stood for 28 years and came down on 9 November 1989."),
    entry("boston-tea-party", ("boston tea party", ("what", "was", "when", "why", "1773")),
          "The Boston Tea Party was a protest on 16 December 1773, when colonists dressed as "
          "Mohawks dumped 342 chests of taxed tea from three ships into Boston harbour. Britain "
          "closed the port in reply, and the two sides were at war within eighteen months.",
          avoid=("wear", "dress", "host", "attend", "invite", "hen", "birthday", "fancy")),
    # "what was the hundred years war" is the plainest phrasing there is, and without "what"
    # it fell between this entry and the length one and got the search hedge.
    entry("hundred-years-war-about", ("hundred years war", ("about", "fought over", "why", "over",
                                                           "what")),
          "The Hundred Years War was about who should be king of France: English kings claimed the "
          "French throne, and the fighting ran from 1337 to 1453 in bursts. England won the big "
          "battles, France won the war, and by the end England held only Calais."),

    # --- the people and first things a person asks about by name ---------------------
    # "who was einstein", "what did darwin do", "how did the cold war end" are the questions
    # people bring from school homework, a pub quiz or a headline, and each one used to get the
    # search hedge. The named key is the whole subject, so each row answers every way of asking
    # about that person, and the avoid lists keep a place, an object or a homograph that shares
    # the name with the person's answer (Darwin the city, Armstrong the trumpet, a light bulb
    # that needs changing).
    entry("einstein", ("einstein", ("who", "was", "is", "what", "did", "do", "discover",
                                    "discovered", "famous", "known", "theory", "relativity",
                                    "born", "die", "died", "invent")),
          "Albert Einstein (1879-1955) was the German-born physicist whose theory of relativity "
          "rewrote how we think about space, time and gravity, and whose E=mc2 links mass and "
          "energy. He won the 1921 Nobel Prize for work on light and the photoelectric effect, "
          "and left Germany for the United States in 1933."),
    # "newtons" is the unit of force, and a recipe or a physics sum about it is not this person.
    entry("newton", ("newton", ("who", "was", "is", "what", "did", "do", "discover", "famous",
                                 "known", "gravity", "laws", "motion", "principia", "born")),
          "Isaac Newton (1643-1727) worked out the three laws of motion and the law of gravity, "
          "showing that the same force pulls a falling apple and holds the Moon in its orbit. He "
          "published it in the Principia in 1687, and he also worked out calculus at the same "
          "time as, and independently of, Leibniz.",
          # A bare "newtons" in avoid would stand the row down for "who was newton" too, because
          # avoid words match loosely: the unit question names no word of the second key part,
          # so it never reaches this row anyway. Only the converting words are guarded.
          avoid=("kilonewtons", "unit", "units", "convert", "conversion", "per kilo", "per kg",
                 "force of", "metre", "metres", "meter", "meters")),
    entry("darwin", ("darwin", ("who", "was", "is", "what", "did", "do", "famous", "known",
                                 "evolution", "theory", "origin", "species", "born")),
          "Charles Darwin (1809-1882) was the naturalist whose 1859 book On the Origin of Species "
          "set out evolution by natural selection: the individuals best suited to their "
          "surroundings pass on their traits. He reached it after five years aboard HMS Beagle, "
          "and it is still the basis of all modern biology.",
          # Darwin is also a city in Australia and a word for a long-haul flight there.
          avoid=("flight", "flights", "fly", "airport", "hotel", "holiday", "weather",
                 "australia", "australian", "travel", "trip", "city", "move to")),
    entry("nightingale", ("nightingale", ("who", "was", "is", "nurse", "nursing", "hospital",
                                         "crimean", "famous", "known", "did", "do")),
          "Florence Nightingale (1820-1910) was the British nurse who reorganised the army "
          "hospital at Scutari in the Crimean War, where cleaning, fresh air and proper food cut "
          "the death rate. She then set up the first professional nursing school, at St Thomas's "
          "in London, and made nursing a trained job.",
          # a nightingale is a bird, and the singing one is not this person.
          avoid=("bird", "birds", "sing", "singing", "song", "garden", "heard")),
    entry("curie", ("curie", ("who", "was", "is", "what", "did", "do", "discover", "discovered",
                               "famous", "known", "nobel", "radioactivity", "radium")),
          "Marie Curie (1867-1934) discovered polonium and radium with her husband Pierre and "
          "named radioactivity, and she is the only person to win Nobel Prizes in two different "
          "sciences, physics in 1903 and chemistry in 1911. She died of aplastic anaemia caused "
          "by years of radiation exposure.",
          # the curie is a unit of radioactivity and the curie point is where a magnet loses its
          # pull: both carry her name and neither asks who she was
          avoid=("temperature", "point", "unit", "units", "becquerel", "magnet", "magnetic",
                 "tesla", "level", "levels", "measure", "measured")),
    entry("mozart", ("mozart", ("who", "was", "is", "what", "did", "do", "compose", "composed",
                                 "composer", "music", "famous", "known", "write", "wrote")),
          "Wolfgang Amadeus Mozart (1756-1791) was an Austrian composer who wrote more than 600 "
          "works in 35 years, including The Marriage of Figaro, Don Giovanni and the Requiem he "
          "left unfinished. He toured Europe as a child prodigy and died in Vienna at 35."),
    entry("beethoven", ("beethoven", ("who", "was", "is", "what", "did", "do", "compose",
                                       "composed", "composer", "music", "famous", "known", "deaf",
                                       "symphony", "write", "wrote")),
          "Ludwig van Beethoven (1770-1827) was the German composer who carried classical music "
          "into the romantic age, from the Fifth Symphony to the Ninth and its Ode to Joy. He "
          "was going deaf from his late twenties and still wrote some of his greatest music once "
          "he could no longer hear it played."),
    entry("van-gogh", (("van gogh", "vangogh"), ("who", "was", "is", "what", "did", "do", "paint",
                                                    "painted", "painter", "artist", "famous",
                                                    "known", "sunflowers", "starry night", "ear")),
          "Vincent van Gogh (1853-1890) was a Dutch painter whose The Starry Night, Sunflowers "
          "and self-portraits are among the most recognised pictures in the world. He sold "
          "almost nothing in his lifetime, cut off part of his own ear in 1888, and died at 37, "
          "with his fame arriving afterwards."),
    entry("picasso", ("picasso", ("who", "was", "is", "what", "did", "do", "paint", "painted",
                                   "painter", "artist", "cubism", "guernica", "famous", "known")),
          "Pablo Picasso (1881-1973) was a Spanish painter and sculptor who invented cubism with "
          "Georges Braque, breaking a subject into flat shapes seen from several sides at once. "
          "Guernica, his answer to the bombing of the Basque town in 1937, is his best-known work."),
    entry("da-vinci", (("da vinci", "davinci", "leonardo"), ("who", "was", "is", "what", "did",
                                                                "do", "paint", "painted", "painter",
                                                                "invent", "inventor", "mona lisa",
                                                                "famous", "known")),
          "Leonardo da Vinci (1452-1519) was an Italian painter, engineer and anatomist: the Mona "
          "Lisa and The Last Supper on one side, notebooks of flying machines and dissected "
          "bodies on the other. Fewer than twenty of his paintings survive, and it is the range "
          "of his curiosity that made him famous."),
    # "alexander" is a common first name, so the question has to be the king: the rest of the
    # key is what a line about a person called Alexander rarely says.
    entry("alexander-the-great", (("alexander the great", "alexander"),
                                  ("king", "macedon", "macedonia", "conquer", "conquered",
                                   "persia", "persian", "empire", "great", "who", "was")),
          "Alexander the Great (356-323 BC) was king of Macedon who conquered the Persian Empire "
          "by the age of 30, marching as far as the Indus. He died in Babylon at 32, and his "
          "generals split the empire between them.",
          avoid=("my son", "my grandson", "my nephew", "called", "named", "baby")),
    # Louis Armstrong is the trumpet player: the person has to be Neil, the Moon or Apollo.
    entry("neil-armstrong", (("neil armstrong", "armstrong"),
                             ("moon", "astronaut", "apollo", "1969", "space", "neil", "who",
                              "was", "famous", "known", "first")),
          "Neil Armstrong (1930-2012) was the American astronaut who took the first steps on the "
          "Moon on 20 July 1969, on Apollo 11. His line as he stepped down, about one small step "
          "and one giant leap for mankind, is one of the most quoted sentences of the century.",
          avoid=("louis", "jazz", "trumpet", "singer", "band", "music", "cornet")),
    # "change a light bulb" is a DIY job; only the inventing question is this row.
    entry("light-bulb", (("light bulb", "lightbulb", "light bulbs", "lightbulbs", "edison"),
                         ("invent", "invented", "invention", "inventor", "edison", "swan", "who")),
          "Thomas Edison's team made the first light bulb that lasted long enough to sell, in "
          "1879, with a carbon filament that burned for hours. Joseph Swan had shown a working "
          "bulb in Britain the year before, and Edison's real contribution was the power supply "
          "that made bulbs worth having.",
          avoid=("change", "changing", "replace", "replacing", "fit", "fitting", "fuse", "led",
                 "watt", "watts", "bright", "blown", "went", "broken", "ceiling", "lamp")),
    entry("great-wall-china", (("great wall of china", "great wall", "chinas wall"),
                               ("built", "build", "building", "why", "who", "when", "long",
                                "big", "old", "far", "for", "purpose")),
          "The Great Wall of China is not one wall but many, built over about 2,000 years: walls "
          "raised by separate states from the 7th century BC were joined under Qin Shi Huang "
          "around 220 BC. The stone and brick wall visitors walk today is mostly Ming work from "
          "the 1400s and 1500s.",
          avoid=("walk on", "walk along", "hike", "hiking", "visit", "tour", "trip", "holiday",
                 "hotel", "flight", "from beijing",
                 # "how long is the great wall of china" is the length, which has its own row
                 # below: this card answered it with two coats of paint, because the paint rows
                 # key "how long" too.
                 "how long", "how far", "long is", "length", "km", "kilometres", "kilometers",
                 "miles", "distance")),
    # The length is the one fact about the wall people ask for by itself, and it used to be
    # answered with the pace of a mile or with how long paint takes to dry.
    # "the wall" on its own is not keyed: "how long is the wall of hadrian" got 21,196 km that
    # way, and Hadrian's Wall is 117 km. "great wall" already matches "how long is the great
    # wall", and the other walls have their own sizes.
    entry("great-wall-length", (("great wall of china", "great wall", "chinas wall"),
                                ("how long", "how far", "long is", "length", "km", "kilometres",
                                 "kilometers", "miles", "distance")),
          lambda memory, understood: _how_long_to_walk_the_wall(understood),
          avoid=("visit", "tour", "trip", "holiday",
                 "hotel", "flight", "from beijing", "paint", "coats",
                 # The walking time is part of this card now, so a line asking how long a walk
                 # takes is not stood down for saying walk or hike. What is stood down is the
                 # question about whether to go: "is it worth walking the great wall" wants a yes
                 # or no and "can i walk on the great wall" wants a rule, and neither is a time.
                 "worth", "should i", "can i", "could i", "shall i", "do you recommend",
                 # another wall named in the line is the wall being asked about
                 "hadrian", "berlin", "offa",
                 # how long it took to build is the build row's card, not the length
                 "build", "built", "building it", "did it take", "how many years"),
          # The paint rows and the pace-of-a-mile row key "how long" as well, and either of them
          # won the tie on main.
          bias=1),
    # The duration is a different question from the fall (which has its own row), and it used to
    # be answered with the leaving-of-Britain date. Britain is the row next door.
    entry("roman-empire-duration", (("roman empire", "rome", "empire"),
                                    ("how long", "last", "lasted", "lasts", "duration", "years",
                                     "centuries")),
          "The Roman Empire in the west lasted about 500 years, from 27 BC to 476 AD, and its "
          "eastern half, ruled from Constantinople, went on until 1453, so the empire as a whole "
          "ran nearly 1,500 years. The republic that came before it had already lasted almost "
          "500 years.",
          # "rome" is a city people fly to as well as an empire, so the travel words stand aside:
          # "how long is the flight to rome" is the air time, not the duration of the empire.
          avoid=("britain", "british", "stay", "staying", "stayed", "nights", "how many days",
                 # The bare "need" was in here for "how long do i need" and it stood the row
                 # aside for its own question: "i need to know how long the roman empire
                 # lasted" lost its answer. The phrases below are what the stay ask says.
                 "how long do i need", "how long will i need", "how long would i need",
                 "how long do i need to stay", "how many days do i need",
                 "roman blind", "blinds", "blind", "letter", "numerals",
                 "candle", "soldier", "army", "fall", "fell", "flight", "flights", "fly",
                 "flying", "plane", "airport", "holiday", "holidays", "trip", "travel",
                 "visiting", "visit", "hotel", "city break", "train", "drive", "coach",
                 "ferry", "cruise", "take to get", "getting to", "how long to get",
                 # "how long do i need in rome" and "how long should i spend in rome" are the
                 # stay-length question, and the travel table answers them; length words alone
                 # reached the empire's duration first. Single words, because a two-word phrase
                 # does not bite a tokenised line.
                 "need", "spend", "days", "nights", "worth", "stay", "staying")),
    # "how did the cold war end" had no answer at all: the cold war row lists what it was and
    # when, never how it finished.
    entry("cold-war-end", ("cold war", ("end", "ended", "ends", "over", "finish", "finished",
                                        "how", "1991", "why")),
          "The Cold War ended between 1989 and 1991: the Berlin Wall fell in November 1989, the "
          "communist governments of eastern Europe collapsed one by one, and the Soviet Union "
          "broke up in December 1991. Years of arms spending and Gorbachev's reforms had already "
          "loosened the system from inside.",
          # the row's own key names the war, so the lift cannot take a line that does not, and
          # the frost row keys "cold" and "how" - "how did the cold war end" was frost advice
          # on tender plants once the work row stopped answering it
          bias=4,
          avoid=("what was", "about", "start", "started", "begin", "began", "cause", "caused",
                 # how long it ran is the other card, which has the dates at both ends
                 "how long", "last", "lasted", "duration")),
    entry("ww2-winner", (("world war two", "world war 2", "ww2", "second world war"),
                         ("won", "win", "winner", "winners", "victors", "allies", "who won")),
          "The Allies won the Second World War: Britain, the Soviet Union, the United States, "
          "China and others, against Germany, Italy and Japan. Germany surrendered in May 1945 "
          "and Japan in September, after the atomic bombs on Hiroshima and Nagasaki."),
    entry("ww1-winner", (("world war one", "world war 1", "ww1", "first world war"),
                         ("won", "win", "winner", "winners", "victors", "allies", "who won")),
          "The Allies won the First World War: Britain, France, Italy, Japan and, from 1917, the "
          "United States, against Germany and Austria-Hungary. The fighting stopped on 11 "
          "November 1918, and the peace terms were settled at Versailles the following year."),
    entry("ww2-deaths", (("world war two", "world war 2", "ww2", "second world war"),
                         ("how many", "died", "die", "deaths", "death toll", "killed",
                          "people died", "casualties")),
          "About 70 to 85 million people died in the Second World War, most of them civilians, "
          "which makes it the deadliest war ever fought. The Soviet Union lost around 27 million "
          "and China 15 to 20 million, and the Holocaust accounts for six million of the dead.",
          avoid=("start", "started", "end", "ended", "why")),
    entry("gutenberg", ("gutenberg", ("who", "was", "is", "printing", "press", "print",
                                       "invent", "invented", "bible")),
          "Johannes Gutenberg (about 1400-1468) was the German craftsman who built Europe's "
          "movable-type printing press in Mainz around 1440, starting with a Bible. Printing "
          "made books cheap enough for ideas to travel, which is what carried the Reformation "
          "and modern science across Europe."),
    entry("princess-diana", (("princess diana", "diana"), ("who", "was", "is", "died", "die",
                                                             "death", "charles", "royal", "wales",
                                                             "famous", "known", "1997")),
          "Diana, Princess of Wales (1961-1997) married Prince Charles in 1981 and became one of "
          "the most photographed people in the world, known for her charity work on AIDS and "
          "landmines. She died in a car crash in Paris in August 1997.",
          avoid=("my", "sister", "daughter", "friend", "called", "named", "aunty", "aunt")),
    entry("abraham-lincoln", (("abraham lincoln", "lincoln"), ("who", "was", "is", "president",
                                                                 "slavery", "civil war", "famous",
                                                                 "known", "assassinated", "died")),
          "Abraham Lincoln (1809-1865) was the American president through the Civil War, who "
          "issued the Emancipation Proclamation freeing the slaves in the rebel states in 1863. "
          "He was shot at Ford's Theatre in Washington in April 1865, days after the war ended.",
          avoid=("car", "cars", "city", "drive", "used", "dealership", "park", "road")),
    # The second batch: the names a quiz, a homework sheet or a film brings up.
    entry("aristotle", ("aristotle", ("who", "was", "is", "greek", "philosopher", "philosophy",
                                      "did", "teach", "taught", "famous", "known", "plato")),
          "Aristotle (384-322 BC) was a Greek philosopher who studied under Plato and taught "
          "Alexander the Great, and who set out logic, biology and politics in a way Europe used "
          "for 1,500 years. He taught that the Earth sat at the centre of the universe, which held "
          "astronomy back until Copernicus."),
    # "plate" is one slip from "plato", so a line about a plate is kept off this row by the
    # second part rather than by the name.
    entry("plato", ("plato", ("who", "was", "greek", "philosopher", "philosophy", "did",
                              "teach", "taught", "academy", "forms", "famous", "known",
                              "republic", "wrote", "write", "book", "books")),
          "Plato (about 428-348 BC) was a Greek philosopher, a student of Socrates and the teacher "
          "of Aristotle, who founded the Academy in Athens and wrote dialogues such as The "
          "Republic. His theory of Forms says the things we see are copies of perfect versions "
          "that exist only in thought.",
          # not a bare "plate" in avoid: avoid words match loosely, and "plate" is one slip
          # from "plato", so it stood the row down for "who was plato". A line about a plate
          # names no word of the second part, so it never reaches the row.
          avoid=("dishwasher", "dinner", "shelf", "sink", "my sister", "my brother", "my son",
                 "my daughter", "my nan", "my mum", "called", "named")),
    entry("socrates", (("socrates", "socratic"), ("who", "was", "is", "greek", "philosopher", "philosophy",
                                    "did", "teach", "taught", "method", "famous", "known", "die")),
          "Socrates (469-399 BC) was a Greek philosopher who wrote nothing and taught by asking "
          "questions until a person saw the hole in their own answer, which is still called the "
          "Socratic method. Athens tried and executed him in 399 BC for impiety and corrupting "
          "the young."),
    entry("genghis-khan", (("genghis khan", "genghis", "chinggis"), ("who", "was", "mongol",
                                                                   "mongolia", "khan", "empire",
                                                                   "conquer", "famous", "known",
                                                                   "did")),
          "Genghis Khan (about 1162-1227) was the Mongol leader who united the nomadic tribes and "
          "built the largest land empire in history, from China to eastern Europe. He was born "
          "Temujin, and his grandsons went on to take Baghdad and reach Hungary."),
    entry("karl-marx", (("karl marx", "marx"), ("who", "was", "is", "communist", "communism",
                                               "manifesto", "capital", "capitalism", "theory",
                                               "famous", "known", "did")),
          "Karl Marx (1818-1883) was a German philosopher and economist who wrote The Communist "
          "Manifesto with Friedrich Engels in 1848 and then Das Kapital, arguing that capitalism "
          "splits society into owners and workers and would be replaced. His ideas shaped the "
          "Soviet Union, China and the cold war that followed.",
          avoid=("groucho", "harpo", "chico", "brothers", "comedy", "comedian", "film", "joke")),
    entry("freud", (("sigmund freud", "freud"), ("who", "was", "is", "psychoanalysis", "psychology",
                                                "therapy", "dreams", "dream", "famous", "known",
                                                "did")),
          "Sigmund Freud (1856-1939) was an Austrian doctor who founded psychoanalysis, the talking "
          "cure built on the idea that dreams, slips of the tongue and early childhood shape adult "
          "behaviour. Many of his specific theories are now rejected, but therapy as a "
          "conversation starts with him."),
    entry("tesla", (("nikola tesla", "tesla"), ("who", "was", "is", "invent", "invented", "inventor",
                                               "electricity", "current", "ac", "engineer",
                                               "famous", "known", "did")),
          "Nikola Tesla (1856-1943) was a Serbian-American engineer who designed the "
          "alternating-current motor and supply that power grids still use, and gave his name to "
          "the unit of magnetic field. He died poor in a New York hotel, and his claims about "
          "sending power through the air were never shown to work.",
          avoid=("car", "cars", "charge", "charging", "charger", "model", "models", "buy",
                 "bought", "drive", "driving", "insurance", "battery", "supercharger",
                 "expensive", "cost", "price", "cheap", "warranty", "dealer", "lease")),
    entry("stephen-hawking", (("stephen hawking", "hawking"), ("who", "was", "is", "physicist",
                                                             "black hole", "black holes", "theory",
                                                             "book", "famous", "known", "did",
                                                             "stephen")),
          "Stephen Hawking (1942-2018) was a British physicist who showed that black holes give "
          "off radiation and slowly evaporate, now called Hawking radiation, and whose A Brief "
          "History of Time sold millions. He had motor neurone disease from 21 and wrote and spoke "
          "through a computer.",
          avoid=("sell", "selling", "hawker", "street", "market", "stall", "spit", "phlegm")),
    entry("guy-fawkes", (("guy fawkes", "fawkes"), ("who", "was", "is", "gunpowder", "plot",
                                                   "november", "bonfire", "remember", "famous",
                                                   "known")),
          "Guy Fawkes (1570-1606) was the Catholic soldier caught in the cellar under the Houses "
          "of Parliament on 5 November 1605 with 36 barrels of gunpowder, in a plot to blow up "
          "King James I. He was tortured, tried and hanged, and the night is still marked with "
          "bonfires."),
    entry("william-the-conqueror", (("william the conqueror", "william i", "the conqueror"),
                                    ("who", "was", "is", "1066", "hastings", "norman", "normandy",
                                     "king", "famous", "known", "did")),
          "William the Conqueror (about 1028-1087) was the Duke of Normandy who won the Battle of "
          "Hastings in 1066 and became the first Norman king of England. He had the Domesday Book "
          "compiled in 1086 to tax what he had taken, and his castles and French words reshaped "
          "England."),
    entry("emmeline-pankhurst", (("emmeline pankhurst", "pankhurst"), ("who", "was", "is",
                                                                     "suffragette", "suffragettes",
                                                                     "vote", "votes", "women",
                                                                     "famous", "known", "did")),
          "Emmeline Pankhurst (1858-1928) led the suffragettes, the Women's Social and Political "
          "Union, whose window-breaking and hunger strikes pushed the vote for women up the "
          "agenda. Some women got the vote in 1918 and all of them in 1928, weeks after she died."),
    entry("joan-of-arc", (("joan of arc", "joan"), ("who", "was", "is", "saint", "france", "french",
                                                   "orleans", "famous", "known", "did", "burned",
                                                   "burnt")),
          "Joan of Arc (about 1412-1431) was a French peasant girl who said the saints told her to "
          "drive the English out, and who led the relief of Orleans in 1429 in the Hundred Years "
          "War. The English burned her at Rouen at 19, and she was made a saint in 1920.",
          avoid=("my", "mum", "nan", "aunt", "aunty", "sister", "friend", "called", "named",
                 "wife", "daughter")),
    entry("tutankhamun", (("tutankhamun", "king tut", "tutenkhamun", "tutankhamen"),
                          ("who", "was", "is", "tomb", "pharaoh", "egypt", "egyptian", "mask",
                           "carter", "famous", "known")),
          "Tutankhamun (about 1341-1323 BC) was an Egyptian pharaoh who came to the throne at "
          "about nine and ruled for around nine years, and whose tomb Howard Carter found almost "
          "untouched in 1922. The gold mask and the grave goods are what taught us most of what we "
          "know about royal burials."),
    entry("marie-antoinette", (("marie antoinette", "antoinette"), ("who", "was", "is", "queen",
                                                                  "french", "france", "louis",
                                                                  "guillotine", "guillotined",
                                                                  "cake", "famous", "known")),
          "Marie Antoinette (1755-1793) was the Austrian-born queen of France, wife of Louis XVI, "
          "who was hated for her spending while the country went hungry, and who was guillotined in "
          "October 1793. There is no record of her ever saying that the hungry should eat cake.",
          avoid=("my", "called", "named", "birthday", "cake recipe")),
    entry("amelia-earhart", (("amelia earhart", "earhart"), ("who", "was", "is", "pilot", "flew",
                                                            "fly", "atlantic", "plane", "famous",
                                                            "known", "disappear")),
          "Amelia Earhart (1897-1937) was the American pilot who flew the Atlantic alone in 1932 "
          "and vanished over the Pacific in 1937 trying to fly round the world. No wreck or body "
          "was ever confirmed, which is why the search for her plane goes on."),
    entry("boudicca", (("boudicca", "boadicea", "budicca"), ("who", "was", "is", "roman",
                                                           "romans", "queen", "iceni", "revolt",
                                                           "famous", "known", "did")),
          "Boudicca (died about 61 AD) was queen of the Iceni in eastern Britain, who led a revolt "
          "against Roman rule after she was flogged and her daughters were assaulted, burning "
          "Colchester, London and St Albans. Her army was beaten by a much smaller Roman force, "
          "and she died soon after, by poison or illness."),
    entry("mother-teresa", (("mother teresa", "teresa"), ("who", "was", "is", "nun", "calcutta",
                                                         "india", "charity", "nobel", "saint",
                                                         "famous", "known", "did")),
          "Mother Teresa (1910-1997) was a nun born in Skopje who ran homes for the dying in "
          "Calcutta from 1950 and won the Nobel Peace Prize in 1979. Her order grew to hundreds of "
          "houses around the world, though critics said the care was basic and the money was not "
          "accounted for.",
          avoid=("my", "nan", "mum", "aunt", "aunty", "called", "named", "friend")),
    # --- who and when, the questions asked by name ---------------------------------
    # "who was the first king of england" was the search hedge: the answer is a person with a
    # date, and no other row names him.
    entry("first-king-england", (("first king", "first king of england", "athelstan",
                                  "king of england", "united england"),
                                 ("who", "when", "was", "which", "first")),
          "Athelstan, crowned in 927, is usually counted as the first king of a united England: he "
          "was a grandson of Alfred the Great and took York from the Vikings that year. Before him "
          "there were kings of Wessex, Mercia and Northumbria rather than of England.",
          avoid=("scotland", "scottish", "wales", "welsh", "ireland", "irish", "france", "french",
                 "spain", "spainish", "prussia", "rome", "roman")),
    # The Aztecs row above answers who they were; this one answers how they ended, and the
    # gravity row was taking "why did the aztecs fall" before it.
    entry("aztecs-fall", (("aztec", "aztecs", "tenochtitlan", "montezuma", "cortes", "cortez"),
                          ("fall", "fell", "end", "ended", "collapse", "collapsed", "conquered",
                           "defeated", "why", "how", "1521", "destroyed")),
          "The Aztec empire fell in 1521, when Spanish forces under Cortes took Tenochtitlan after "
          "a three-month siege. Cortes had only a few hundred Spaniards, so what did it was "
          "tens of thousands of local allies who resented Aztec tribute, plus smallpox, which "
          "killed a large share of the city before the fighting ended.",
          avoid=("recipe", "food", "chocolate")),
    entry("transatlantic-slave-trade",
          (("transatlantic slave trade", "slave trade", "slave ships", "middle passage",
            "triangle trade", "slavery in america"),
           ("what", "was", "how many", "when", "started", "begin", "end", "why", "about")),
          "The transatlantic slave trade carried about 12.5 million Africans to the Americas "
          "between roughly 1525 and 1867, and about 10.7 million survived the crossing. Britain "
          "was the biggest carrier in the 1700s, and it outlawed the trade in 1807 and slavery "
          "itself in its colonies in 1833.",
          avoid=("abolished", "abolition", "1833", "1807", "william wilberforce", "reparations")),
    entry("korean-war", (("korean war", "korea"), ("what", "was", "when", "started", "start",
                                                   "why", "end", "ended", "about", "1950")),
          "The Korean War ran from 1950 to 1953, when North Korea, backed by China and the Soviet "
          "Union, invaded South Korea, which was backed by the United States and other UN forces. "
          "It ended in an armistice in July 1953, not a peace treaty, with the border near where "
          "it started at the 38th parallel.",
          avoid=("visit", "holiday", "food", "travel", "k-pop", "language", "learn")),
    entry("dust-bowl", (("dust bowl", "dustbowl"), ("what", "was", "when", "why", "happened",
                                                     "caused", "about")),
          "The Dust Bowl was the drought and dust storms that hit the southern plains of the "
          "United States in the 1930s, worst in 1934 to 1936. Years of deep ploughing had killed "
          "the grass that held the soil, so when the rain stopped the wind took the topsoil in "
          "black blizzards, and a third of a million people left the region.",
          avoid=("clean", "hoover", "vacuum", "bowl in", "mix")),
    entry("waterloo", (("waterloo", "1815"), ("battle", "when", "who", "won", "what", "happened",
                                              "napoleon", "fought")),
          "The Battle of Waterloo was fought on 18 June 1815 near Brussels, when Wellington's army "
          "with Blucher's Prussians beat Napoleon. It ended his rule for good: he abdicated four "
          "days later and was exiled to Saint Helena, where he died in 1821.",
          avoid=("station", "train", "tube", "bridge", "abba", "song", "lyrics", "uni")),
    entry("ireland-partition", (("ireland", "irish", "northern ireland", "ulster", "eire"),
                                ("split", "partition", "partitioned", "divided", "divide",
                                 "separate", "separated", "why", "1921", "border")),
          "Ireland was partitioned in 1921 by the Anglo-Irish Treaty, which created the Irish Free "
          "State of 26 counties and left the six counties of Northern Ireland inside the United "
          "Kingdom. The Unionist majority in the north wanted to stay British, the nationalist "
          "majority in the south wanted home rule and then a republic, and a civil war followed.",
          avoid=("visit", "holiday", "travel", "drive", "trip", "ferry")),
    entry("inca-empire", (("inca", "incas", "inca empire", "cusco", "cuzco", "machu picchu"),
                          ("who", "what", "when", "how", "empire", "fall", "fell", "built",
                           "conquered")),
          "The Inca empire ran along the Andes from about 1438 to 1533, with its capital at Cusco "
          "and perhaps ten million people under it. It was held together by roads, storehouses and "
          "tax paid in labour rather than money, and recorded in knotted cords called quipu rather "
          "than writing; Spanish forces under Pizarro took it apart from 1532.",
          avoid=("visit", "holiday", "travel", "trip", "walk", "trek", "ticket")),
    entry("anglo-saxons", (("anglo saxon", "anglo saxons", "anglo-saxon", "anglo-saxons",
                            "saxons", "jutes"),
                           ("who", "were", "what", "when", "where", "from", "come", "came")),
          "The Anglo-Saxons were the Germanic peoples - Angles, Saxons and Jutes - who settled in "
          "Britain from about 450 AD after the Roman legions left, and whose kingdoms, Wessex, "
          "Mercia and Northumbria among them, became England. They converted to Christianity from "
          "597, and their rule ended with the Norman conquest in 1066.",
          avoid=("word", "words", "language", "old english", "name", "names", "translate")),
    entry("enlightenment", (("enlightenment", "age of reason"),
                            ("what", "was", "when", "about", "why", "who")),
          "The Enlightenment was the European movement of the 1600s and 1700s that put reason and "
          "evidence above inherited authority: Newton on physics, Locke on government, Voltaire "
          "and Rousseau on toleration and the people's will. Its ideas fed both the American and "
          "the French revolutions."),
    entry("opium-war", (("opium war", "opium wars"), ("what", "was", "when", "why", "about",
                                                       "happened", "china")),
          "The Opium Wars were fought by Britain against Qing China in 1839 to 1842 and again in "
          "1856 to 1860, to keep the opium trade that British merchants ran from India into China "
          "after China tried to stop it. Britain won, and the Treaty of Nanking in 1842 handed it "
          "Hong Kong and opened five ports."),
    # "why did the soviet union collapse" fell through to the money-and-employment fallback,
    # whose "union" row offered a union rep.
    entry("soviet-collapse", (("soviet union", "ussr", "soviet", "gorbachev", "perestroika",
                               "glasnost"),
                              ("collapse", "collapsed", "fall", "fell", "end", "ended", "why",
                               "how", "break up", "broke up", "dissolve", "dissolved", "1991")),
          "The Soviet Union broke up in December 1991 into fifteen separate countries. Gorbachev's "
          "reforms had loosened the party's control without fixing the economy, the republics "
          "elected their own governments, and after a failed coup in August 1991 they walked out; "
          "Russia took over the Soviet seat at the UN.",
          avoid=("trade union", "union rep", "union member", "join a union", "union dues")),
]

# --- a name is also a place, a pet, a car and a child in the room -----------------------
# Every row above that is about a person loses to these shapes, whatever its own avoid list
# says. It is one list because the same four words kept turning up on twenty rows, and the row
# that forgot them answered "my daughter is called darwin" with a biography of Charles Darwin.
# "where is darwin" is a place, "what is darwin like to visit" is a trip, and "my dog is called
# newton" is the dog: none of them asks who the man was.
NOT_A_PERSON = ("is called", "named", "we call", "name is", "where is", "where's", "live in",
                "lives in", "living in", "like to visit", "is it like", "whats it like",
                "is there a", "is there any", "visit", "visiting", "worth visiting",
                "things to do", "stay in",
                # A person's name is often a book title too: "what should i read after the da
                # vinci code" is a book asking for the next one. The frames only, never a bare
                # "book" or "read": those are also how a real question about the person is
                # worded, and "what books did einstein write" lost its biography to the bare
                # noun while it kept it behind the frames.
                "read after", "read next", "reading next", "what to read", "books like",
                "book like", "finished", "what next", "next book", "something similar")

PERSON_ROWS = frozenset((
    "einstein", "newton", "darwin", "nightingale", "curie", "mozart", "beethoven", "van-gogh",
    "picasso", "da-vinci", "alexander-the-great", "neil-armstrong", "gutenberg",
    "princess-diana", "abraham-lincoln",
    # the second batch of names, same rule: a place, a dog or a daughter is not the person
    "aristotle", "plato", "socrates", "genghis-khan", "karl-marx", "freud", "nikola-tesla",
    "stephen-hawking", "guy-fawkes", "william-the-conqueror", "emmeline-pankhurst",
    "joan-of-arc", "tutankhamun", "marie-antoinette", "amelia-earhart", "boudicca",
    "mother-teresa",
))

for _row in ENTRIES:
    if _row.id in PERSON_ROWS:
        _row.avoid = _row.avoid + NOT_A_PERSON


# --- the past by name, as data -----------------------------------------------
# "who was X" and "when was X" are among the commonest history lines people send, and one card
# per person never keeps up: lincoln, einstein, darwin, joan of arc, the great wall and waterloo
# all fell through to the search hedge. So the people and the events are a table, and the two
# entries below read it. The first answers a question about a thing named in the table by the
# shape of the question, so "when did ww2 end", "how long did the first world war last" and
# "how many people died in ww2" all come out of one row; the second answers "who invented it"
# for the things in the second table. A new person is a line of data, not a new entry.
#
# `tell` is the answer to the plainest question ("who was X", "what was X") and starts with the
# date or the name, so it also answers "when was X". `long` and `won` answer the figure
# questions and are only written where the row has the figure; the wars have cards of their own
# for the start, the end, the winner and the death toll, which is why their rows write none. `off` holds words that make a
# line about something else entirely: "waterloo station", "my first car".
PAST = {
    "world-war-one": {
        "names": ("world war one", "world war 1", "ww1", "wwi", "first world war", "great war"),
        # why it began is its own card, with the assassination and the alliances in order
        # the start, the end, the winner and the death toll each have a card of their own on
        # main, and each of them says more than one line of this row could; what is left here is
        # what the war was and how long it ran.
        # no card answers the toll of this war, so this row keeps it; the winner, the start and
        # the end each have one.
        "off": ("cause", "caused", "causes", "start", "started", "begin", "began", "trigger",
                "end", "ended", "over", "finish", "finished", "why", "won", "win", "winner",
                "beat", "victor", "victory", "prime minister", "leader", "president", "king",
                "emperor"),
        "tell": "World War One ran from 1914 to 1918. It began when Archduke Franz Ferdinand was "
                "assassinated and the alliances pulled the great powers in, and it ended with "
                "Germany's armistice on 11 November 1918.",
        "long": "World War One lasted four years and three months, from 28 July 1914 to the "
                "armistice on 11 November 1918.",
        "dead": "About 17 million people died in World War One, roughly 9 to 10 million of them "
                "soldiers, and about 20 million more were wounded.",
    },
    "world-war-two": {
        "names": ("world war two", "world war 2", "ww2", "wwii", "second world war"),
        # the start, the end, the winner and the death toll each have a card of their own on
        # main, and each of them says more than one line of this row could; what is left here is
        # what the war was and how long it ran.
        "off": ("cause", "caused", "causes", "start", "started", "begin", "began", "trigger",
                "end", "ended", "over", "finish", "finished", "why", "won", "win", "winner",
                "beat", "victor", "victory", "died", "die", "dead", "deaths", "death", "how many",
                "casualties", "killed", "prime minister", "leader", "president", "king",
                "emperor"),
        "tell": "World War Two ran from 1939 to 1945. Britain and France declared war on Germany "
                "after it invaded Poland, and it ended with Germany's surrender on 8 May 1945 "
                "and Japan's on 2 September.",
        "long": "World War Two lasted six years and a day, from 1 September 1939 to 2 September "
                "1945.",
    },
    "pepys": {
        "names": ("samuel pepys", "pepys"),
        "tell": "Samuel Pepys (1633-1703) was a London naval administrator whose diary, kept from 1660 "
                "to 1669 in shorthand, is the best eyewitness account we have of the plague, the Great "
                "Fire and the Restoration court. He gave it up because he thought he was going blind, "
                "and it was not read until the 1820s.",
    },
    # Four names of the school syllabus the table did not hold: "who was brunel" was a search
    # hedge, "who were the celts" and "what did the egyptians invent" were a hedge and a nod, and
    # "what was the doomsday book" was answered with a yellow card, because the only other place
    # the word appears in the tree is football.
    "brunel": {
        "names": ("isambard kingdom brunel", "brunel"),
        "tell": "Isambard Kingdom Brunel (1806-1859) was the Victorian engineer of the Great "
                "Western Railway, the Clifton Suspension Bridge, the SS Great Britain and the "
                "Great Eastern, and the tunnels and viaducts between them. He worked at a scale "
                "nobody had tried before, in a top hat, and died at 53 after a stroke, worn out "
                "by the Great Eastern.",
        "built": "Brunel built the Great Western Railway from London to Bristol, the Clifton "
                 "Suspension Bridge over the Avon, the SS Great Britain (the first iron ship to "
                 "cross the Atlantic under screw propeller), the Great Eastern, and the Box "
                 "Tunnel and the viaducts and bridges along the GWR route. His last was the "
                 "Royal Albert Bridge at Saltash, finished in the year he died.",
        # "who was brunel" then "when did he die" got the biography again, because the death
        # was only in the tell. A date is the one thing the story cannot carry.
        "dead": "Brunel died on 15 September 1859, aged 53, of a stroke, ten days after the "
                "first, unsuccessful launch of the Great Eastern. He had been ill for most of "
                "that year and the ship's failures were blamed for it. He is buried at Kensal "
                "Green; the Royal Albert Bridge at Saltash, finished in the year he died, is his "
                "last work.",
    },
    "celts": {
        "names": ("celts", "celtic people", "celtic britain", "ancient celts"),
        # a football club and a language course are not the Iron Age
        "off": ("celtic fc", "celtic park", "football", "team", "match", "rangers", "language",
                "course", "class", "music", "song"),
        "tell": "The Celts were the iron-working peoples of central Europe who spread west to "
                "Britain, Ireland, France and Spain from about 500 BC. They wrote nothing down "
                "themselves, so what is known comes from Roman writers and from their hillforts, "
                "torcs and burials - and from the Celtic languages still spoken in Wales, "
                "Scotland, Ireland and Cornwall.",
        "built": "The Celts built hillforts on high ground, with banks and ditches of earth and "
                 "timber - Maiden Castle in Dorset is the largest in Britain - and lived in "
                 "roundhouses of timber, wattle and thatch. They worked iron for swords, tools "
                 "and ploughs, and fired pots without a wheel.",
    },
    "ancient-egyptians": {
        "names": ("egyptians", "ancient egyptians", "egyptian people"),
        # the pyramids, the mummies and the pharaohs each have a card of their own
        "off": ("pyramid", "pyramids", "mummy", "mummies", "mummify", "mummification", "pharaoh",
                "hieroglyph", "hieroglyphs", "cleopatra", "tutankhamun"),
        "tell": "Ancient Egypt gave us the 365-day calendar, papyrus paper, hieroglyphic writing, "
                "glass and the water clock, and Egyptian surgeons were stitching wounds, setting "
                "broken bones and removing cataracts by about 2500 BC. Their maths was practical: "
                "fractions, a base of ten, and the 3-4-5 triangle for squaring a corner.",
    },
    "domesday-book": {
        "names": ("domesday book", "domesday", "doomsday book", "doomsday"),
        "off": ("doomsday clock", "prepper", "preppers", "film", "movie", "game", "song", "album"),
        "tell": "The Domesday Book is the survey William the Conqueror ordered at Christmas 1085 "
                "and finished the next year: who held every manor, field, mill, wood and pig in "
                "England, and what each was worth before and after the Norman conquest. It was "
                "called Domesday because, like the Last Judgement, there was no appeal from it.",
    },
    "norman-conquest": {
        "names": ("normans invade", "norman invasion", "norman conquest", "normans came"),
        "tell": "The Normans invaded England in 1066: William of Normandy landed in September, killed "
                "King Harold at Hastings on 14 October, and was crowned on Christmas Day. Within "
                "twenty years his barons had built the castles and taken the land in the Domesday survey.",
    },
    "edward-the-confessor": {
        "names": ("edward the confessor",),
        "tell": "Edward the Confessor was king of England from 1042 to 1066, the last of the old "
                "West Saxon line: he rebuilt Westminster Abbey, where he is buried, and died childless "
                "in January 1066, which is why three men fought over the crown that year.",
    },
    "nelson": {
        # the bare name was left out while the other Nelson was in the same table: it is in
        # `off` below, so "who was nelson mandela" still goes to his own row
        "names": ("admiral nelson", "horatio nelson", "lord nelson", "nelson"),
        "off": ("mandela", "nelson mandela", "rugby", "new zealand", "city of nelson"),
        "tell": "Horatio Nelson (1758-1805) was the British admiral who beat the French fleet at the "
                "Nile in 1798 and the combined French and Spanish fleet at Trafalgar in 1805, where he "
                "was shot and died on his own ship. He lost an arm and an eye in earlier actions and "
                "is remembered for the signal 'England expects that every man will do his duty'.",
        "dead": "Nelson was shot by a French marksman on the quarterdeck of HMS Victory at "
                "Trafalgar on 21 October 1805, and died below decks about three hours later, "
                "with the battle already won. His body was put in a barrel of brandy for the "
                "sail home.",
    },
    "richard-the-lionheart": {
        "names": ("richard the lionheart", "lionheart", "richard the first", "richard i"),
        "tell": "Richard I (1157-1199) was king of England for ten years and spent only about six "
                "months of them in England: he went on the Third Crusade, was captured on the way home "
                "and ransomed for a fortune, then died besieging a small castle in France.",
    },
    "saladin": {
        "names": ("saladin",),
        "tell": "Saladin (about 1137-1193) was the Kurdish sultan who united Egypt and Syria and took "
                "Jerusalem back from the crusaders at Hattin in 1187. He fought Richard the Lionheart "
                "to a standstill in the Third Crusade and let the people of Jerusalem go rather than "
                "massacre them, which is why he is remembered well on both sides.",
    },
    "suleiman": {
        "names": ("suleiman the magnificent", "suleiman"),
        "tell": "Suleiman the Magnificent (1494-1566) ruled the Ottoman Empire for 46 years, took "
                "Belgrade and Rhodes, besieged Vienna in 1529, and gave the empire the law code that "
                "had him called Suleiman the Lawgiver at home. It was the height of Ottoman power.",
    },
    "britain-left-india": {
        "names": ("britain leave india", "britain left india", "british leave india",
                  "british raj end", "british leave"),
        "tell": "Britain left India on 15 August 1947, when the country became independent and was "
                "partitioned into India and Pakistan at the same moment, which set off the largest "
                "migration and one of the worst episodes of violence of the century.",
    },
    "chamberlain": {
        "names": ("neville chamberlain", "chamberlain"),
        "off": ("job", "wages", "hiring"),
        "tell": "Neville Chamberlain (1869-1940) was British prime minister from 1937 to 1940. He flew "
                "to Germany three times in 1938 and came back promising 'peace for our time' from "
                "Munich, gave up the Sudetenland, and was forced out after the Norway campaign in 1940.",
    },
    "boer-war": {
        "names": ("boer war", "boers"),
        "off": ("memorial", "monument", "statue", "museum"),
        "tell": "The Boer War ran from 1899 to 1902: the British fought the Dutch-speaking Boer "
                "republics of the Transvaal and the Orange Free State over gold and empire. It took "
                "a quarter of a million soldiers to win, and the camps where Boer families were held "
                "killed about 26,000 people, mostly children.",
    },
    "franz-ferdinand": {
        "names": ("franz ferdinand", "archduke ferdinand"),
        "off": ("band", "song", "guitar", "the band"),
        "tell": "Archduke Franz Ferdinand of Austria-Hungary was shot in Sarajevo on 28 June 1914 by "
                "Gavrilo Princip, a Bosnian Serb nationalist. Austria-Hungary blamed Serbia, the "
                "alliances pulled every great power in, and the First World War began five weeks later.",
    },
    "russian-revolution": {
        "names": ("russian revolution", "bolshevik revolution", "october revolution"),
        "tell": "The Russian Revolution ran through 1917: in February strikes and mutinies pushed the "
                "tsar to abdicate, and in October the Bolsheviks under Lenin took over in Petrograd. "
                "A civil war followed, the USSR was formed in 1922, and the last tsar was shot with his "
                "family in 1918.",
    },
    "rasputin": {
        "names": ("rasputin",),
        "off": ("song", "boney m", "film"),
        "tell": "Grigori Rasputin (1869-1916) was a Siberian peasant who became the tsarina's closest "
                "adviser because he seemed able to stop the haemophilia bleeding of the heir, Alexei. "
                "By 1916 his influence at court had become a scandal, and a group of nobles poisoned "
                "him, shot him and threw him in the Neva.",
    },
    "attila": {
        "names": ("attila the hun", "attila"),
        "tell": "Attila (about 406-453) was king of the Huns, the horsemen from the steppe who "
                "extracted tribute from the Roman Empire rather than taking it. He raided across the "
                "Balkans and into Gaul, was beaten at Chalons in 451, and died in 453 - after which his "
                "empire fell apart within a generation.",
    },
    "pearl-harbour": {
        "names": ("pearl harbour", "pearl harbor"),
        "off": ("film", "movie"),
        "tell": "Japan attacked the US fleet at Pearl Harbor in Hawaii on 7 December 1941, sinking or "
                "damaging most of the battleships in a morning and killing about 2,400 people. The "
                "United States declared war the next day, which is how it entered the Second World War.",
    },
    "bismarck": {
        "names": ("otto von bismarck", "bismarck"),
        "off": ("battleship", "ship", "herring"),
        "tell": "Otto von Bismarck (1815-1898) was the Prussian statesman who united Germany in 1871 "
                "by three short wars and then ran it as chancellor until 1890. He called his method "
                "Realpolitik - what works rather than what is right - and built the welfare state and "
                "alliances that kept the peace in Europe for twenty years after he left.",
    },
    "ireland-republic": {
        "names": ("ireland become a republic", "ireland became a republic", "ireland a republic",
                  "republic of ireland", "irish republic"),
        "off": ("northern ireland", "holiday", "visit", "trip", "passport", "move to"),
        "tell": "Ireland became a republic on 18 April 1949, when the Republic of Ireland Act came "
                "into force and the country cut its last constitutional link with the Crown. It had "
                "been the Irish Free State since 1922, after the war of independence and the treaty.",
    },
    "depression-1929": {
        # the bare word is an illness; only the question about the slump reaches this row
        # "great depression" is a card of its own; this row only catches the bare word
        "names": ("the depression start", "the depression begin", "the depression happen",
                  "the depression end", "the depression finish"),
        "tell": "The Great Depression began with the Wall Street crash in October 1929 and lasted "
                "through the 1930s: banks failed, a quarter of American workers lost their jobs, and "
                "world trade shrank by two thirds. It ended only with the rearmament that came with "
                "the Second World War.",
    },
    "augustus": {
        "names": ("caesar augustus", "augustus", "octavian", "octavius", "first roman emperor"),
        "tell": "Augustus (63 BC-14 AD) was the first Roman emperor: Julius Caesar's adopted heir, "
                "who took the name Augustus when he came out on top of the civil wars in 27 BC and "
                "ruled for forty years. He kept the forms of the republic while holding the power of "
                "a king, and his reign opened the two centuries of peace Romans called the Pax Romana.",
    },
    "votes-for-women": {
        "names": ("women get the vote", "women got the vote", "women vote", "suffragettes",
                  "suffrage", "votes for women", "woman get the vote", "women the vote"),
        # a country named in the line is a country of its own: this row speaks for Britain
        # "in the us" is the phrase, because the word "us" alone is "tell us", and the age side
        # is the other history: 1969 is when 18-year-olds got the vote, and "when did 18 year
        # olds get the vote" was answered with 1918 and 1928.
        "off": ("america", "american", "usa", "in the us", "in the usa", "united states",
                # "when did black women get the vote" is the American franchise, not this one,
                # and black-vote is the row that has it.
                "black", "african",
                "australia", "aus", "new zealand", "nz", "canada",
                "france", "germany", "india", "ireland", "switzerland", "south africa",
                "18", "16", "17", "21 year", "year olds", "year old", "age", "aged", "old",
                "young people", "younger", "teenagers", "teenager"),
        "tell": "Women got the vote in Britain in two steps. In 1918 women over 30 who met a "
                "property test, and all men over 21, were given the vote; in 1928 women got it at 21, "
                "on the same terms as men. The suffragettes' campaign before the war, and women's "
                "work in the war, both pushed it through.",
    },
    "slavery-end": {
        "names": ("slave trade", "slavery", "slaves"),
        # A country in the line has its own answer ("slavery-abolished" above, the civil war
        # below), and those are better than a list of every date.
        "off": ("britain", "british", "uk", "england", "english", "empire", "transatlantic",
                "america",
                "american", "usa", "us", "united states", "france", "french", "spain",
                "spanish", "portugal", "brazil", "india", "canada", "australia", "1865",
                "1807", "1833", "civil war", "bible", "god", "jesus", "church", "quran",
                "islam", "sin", "moral", "reparations", "museum"),
        "tell": "It depends where: Britain banned the trade in 1807 and slavery in its colonies "
                "in 1833, France abolished it in 1848, the United States in 1865 with the 13th "
                "Amendment, and Brazil was last in 1888.",
    },

    "slavery-in-america": {
        # the card speaks for Britain, and a country named in the line is a country of its own
        "names": ("slavery in america", "american slavery", "slavery in the us",
                  "slavery in the united states", "america abolish slavery",
                  "america abolished slavery", "us abolish slavery", "us abolished slavery",
                  "thirteenth amendment", "13th amendment"),
        "tell": "The United States abolished slavery with the 13th Amendment, ratified in December "
                "1865, after the Civil War. The Emancipation Proclamation of 1863 had freed slaves "
                "only in the rebel states, so the amendment was what ended it everywhere.",
    },
    "rosa-parks": {
        "names": ("rosa parks",),
        "tell": "Rosa Parks was the black seamstress in Montgomery, Alabama, who on 1 December "
                "1955 refused to give up her bus seat to a white passenger. Her arrest set off "
                "the 381-day bus boycott led by a young Martin Luther King, and the Supreme "
                "Court struck down bus segregation the next year.",
    },
    "charles-dickens": {
        "names": ("charles dickens", "dickens"),
        "tell": "Charles Dickens (1812-1870) was the Victorian novelist who wrote Oliver Twist, "
                "A Christmas Carol, David Copperfield and Bleak House. He worked in a boot-polish "
                "factory as a boy, and that memory of child labour runs through his books, which "
                "were published in monthly parts and read aloud across the country.",
    },
    "stalin": {
        "names": ("stalin", "joseph stalin", "josef stalin"),
        "off": ("star trek", "or is it"),
        "tell": "Joseph Stalin (1878-1953) ruled the Soviet Union from the late 1920s until he "
                "died. He forced through collectivisation of farming and crash industrialisation, "
                "at the cost of famines that killed millions, then led the country through the "
                "Second World War after Hitler invaded in 1941.",
    },
    "lenin": {
        "names": ("lenin", "vladimir lenin"),
        "tell": "Vladimir Lenin (1870-1924) was the revolutionary who led the Bolsheviks to power "
                "in Russia in October 1917, pulled the country out of the First World War, and "
                "founded the Soviet state. He died in 1924 after a series of strokes, and Stalin "
                "took over the party machine.",
    },
    "world-wars-difference": {
        "names": ("difference between ww1 and ww2", "difference between the world wars",
                  "difference between world war one and world war two",
                  "how were the world wars different", "ww1 and ww2 difference"),
        "tell": "World War One was mostly trench fighting in France and Belgium, and it ended with "
                "Germany intact and a peace the next war was blamed on. World War Two was a war "
                "of movement, bombing and genocide across Europe, Africa and the Pacific, it "
                "ended with both aggressors occupied, and it killed about four times as many "
                "people.",
    },
    "vietnam-war": {
        "names": ("vietnam war", "war in vietnam"),
        "tell": "The Vietnam War ran from 1955 to 1975, when North Vietnam and the Viet Cong beat "
                "South Vietnam and its American backers. It killed about 3 million people, more "
                "than half of them Vietnamese civilians.",
        "long": "The Vietnam War ran about 20 years, from 1955 to the fall of Saigon on 30 April "
                "1975; American combat troops were there from 1965 to 1973.",
    },
    "colosseum": {
        "names": ("colosseum", "coliseum"),
        # whether it is worth the trip is a travel question, not a history one, and "is the
        # colosseum worth a day" and "how long does the colosseum take" are trips too: they were
        # told when it was built.
        "off": ("visit", "visiting", "worth seeing", "ticket", "tickets", "queue",
                "hotel", "crowds", "guided", "skip the line", "best time",
                "worth", "enough", "days", "whole day", "how long", "take"),
        "tell": "The Colosseum was built in Rome between 72 and 80 AD, under the emperors "
                "Vespasian and Titus, with loot from the Jewish temple in Jerusalem. It held "
                "about 50,000 people for gladiator fights and animal hunts.",
    },
    "tower-of-london": {
        "names": ("tower of london",),
        # whether it is worth the trip is a travel question, not a history one
        "off": ("visit", "visiting", "worth seeing", "ticket", "tickets", "queue",
                "hotel", "crowds", "guided", "skip the line", "best time"),
        "tell": "The Tower of London was started by William the Conqueror in the 1070s, and later "
                "kings ringed it with walls and towers. It has been a fortress, a palace, a "
                "prison and a mint, and it holds the Crown Jewels.",
    },
    "marshall-plan": {
        "names": ("marshall plan",),
        "tell": "The Marshall Plan was the American programme that sent about 13 billion dollars "
                "to western Europe between 1948 and 1952 to rebuild after the war. It was "
                "offered to the Soviet Union and its neighbours as well, and Stalin refused.",
    },
    "first-president": {
        "names": ("first president of the united states", "first president of the usa",
                  "first president of america", "first us president", "first american president",
                  "george washington", "first president of the us", "first president"),
        # "the first president of France" is a different person, and the line names which.
        "off": ("france", "french", "ireland", "irish", "mexico", "brazil", "india", "china",
                "russia", "south africa", "turkey", "israel", "egypt", "kenya", "nigeria",
                "ghana", "pakistan", "philippines", "korea", "singapore"),
        "tell": "George Washington was the first president of the United States, from 1789 to "
                "1797. The first electoral college chose him unanimously and he stepped down "
                "after two terms, which set the pattern every later president followed.",
    },
    "nickname": {
        "names": ("last tsar of russia", "last tsar", "tsar nicholas", "nicholas ii",
                  "tsar of russia", "nicholas the second"),
        "tell": "Nicholas II was the last tsar of Russia. He gave up the throne in March 1917 as "
                "the war and the bread queues broke his country, and he and his family were shot "
                "by the Bolsheviks in Yekaterinburg in July 1918.",
    },
    "jfk": {
        "names": ("jfk", "john f kennedy", "john fitzgerald kennedy", "president kennedy",
                  "kennedy"),
        "tell": "John F. Kennedy was the 35th US president, from 1961 until he was shot in Dallas "
                "on 22 November 1963. He faced the Soviet Union down over Cuba in 1962 and set "
                "the goal of landing a man on the moon before the decade was out.",
    },
    "anne-boleyn": {
        "names": ("anne boleyn",),
        "tell": "Anne Boleyn was Henry VIII's second wife, from 1533 to 1536, and the mother of "
                "Elizabeth I. When she gave him no son he had her tried for adultery and "
                "executed at the Tower of London in May 1536.",
    },
    "qin-shi-huang": {
        "names": ("first emperor of china", "qin shi huang", "qin shihuang", "emperor of china"),
        "tell": "Qin Shi Huang was the first emperor of a united China, from 221 to 210 BC. He "
                "standardised writing, money and weights, joined up the Great Wall, and was "
                "buried with the terracotta army.",
    },
}

# The things people ask who invented. Kept apart from PAST because these names are ordinary
# words too: "how do i change a light bulb" and "what is the best car" are not history, and
# this entry only answers when the line asks who made the thing or when it was first made.
MADE = {
    "aeroplane": {
        "names": ("aeroplane", "airplane", "first flight", "first plane"),
        "off": ("fly", "flying", "flight", "flights", "airport", "luggage", "bag", "book",
                "ticket", "seat", "carry", "delay", "cancel", "turbulence", "scared", "afraid"),
        "tell": "The Wright brothers, Orville and Wilbur, made the first powered aeroplane flight "
                "on 17 December 1903 at Kitty Hawk: 12 seconds and 36 metres. Their edge was "
                "working out how to control a wing, not just how to lift one.",
    },
    "car": {
        "names": ("car", "cars", "automobile", "motor car"),
        "off": ("my", "your", "our", "insurance", "mot", "tax", "lease", "hire", "buy",
                "buying", "second hand", "secondhand", "sell", "worth",
                # a car you are buying or haggling over is not a car that was invented:
                # "how much should i offer on a car" was answered with Karl Benz, and
                # "whats a good first car for a new driver" is a buying question too.
                "offer", "offering", "haggle", "haggling", "haggle over", "pay", "paying",
                "price", "prices", "cost", "costs", "how much should i pay", "deal", "dealer",
                "garage", "test drive", "finance", "part exchange", "part-exchange",
                "good", "best", "cheap", "cheapest", "affordable", "reliable", "recommend",
                "recommended", "advice", "new driver", "learner", "first time driver",
                # the shapes a short line takes when it is choosing rather than asking about
                # 1885: "bought" and "better" beside the words above cover "we bought a car",
                # and "which"/"should" cover "which car should i get".
                "bought", "better", "cheaper", "sensible", "practical", "which", "should"),
        "tell": "Karl Benz built the first car with a petrol engine in 1885 and patented it in "
                "1886, and his wife Bertha drove it 100 km the next year to prove it worked. "
                "Henry Ford's Model T, from 1908, was the one that made cars ordinary.",
    },
    "television": {
        "names": ("television", "tv"),
        "tell": "John Logie Baird gave the first public demonstration of television in London in "
                "1926, using a spinning disc. Philo Farnsworth's all-electronic system, shown in "
                "1927, is the one every modern set works on.",
    },
    "steam-engine": {
        "names": ("steam engine", "steam engines"),
        "tell": "Thomas Newcomen built the first practical steam engine in 1712, to pump water "
                "out of mines, and James Watt improved it from 1769 with a separate condenser "
                "that wasted far less heat. Watt's engine is the one that powered the Industrial "
                "Revolution.",
    },
    "electricity": {
        "names": ("electricity", "electric power"),
        "tell": "Nobody invented electricity: it is a force in nature, and people learned to make "
                "and use it over about 150 years. Franklin showed lightning was electric in "
                "1752, Volta made the first battery in 1800, Faraday built the first generator in "
                "1831, and Edison opened the first power station in 1882.",
    },
    "internet": {
        "names": ("internet", "world wide web", "the web"),
        "tell": "No one person invented the internet: ARPANET linked four American university "
                "computers in 1969 and the network grew from there. Tim Berners-Lee invented the "
                "world wide web on top of it in 1989, at CERN, so documents could be linked.",
    },
}

PAST_NAMES = tuple(name for row in PAST.values() for name in row["names"])
PAST_FOLLOW = ("he", "him", "his", "she", "her", "they", "them", "it", "its", "that man",
               "that woman")
MADE_NAMES = tuple(name for row in MADE.values() for name in row["names"])

# What makes a line a question about the thing it names. Without these, a line that happens to
# mention waterloo or slavery would be handed a history story it did not ask for.
PAST_ASK = ("who", "who was", "who is", "who won", "what", "what was", "what is", "what did",
            "when", "when was", "when did", "which", "why", "why did", "was", "is", "were",
            "did", "about", "tell me about", "born", "die", "died", "death", "how old",
            "how long", "how many", "long", "last", "lasted", "won", "win", "winner", "killed",
            "many", "old", "happened", "started", "start", "famous", "known for",
            # the plainest request to be told about a thing that happened: "explain the first
            # world war" and "describe the trenches" were answered by nothing at all, because
            # only "tell me about" counted as asking.
            "explain", "explained", "describe", "summarise", "summarize")
MADE_ASK = ("invent", "invented", "invention", "inventor", "discover", "discovered",
            "discovery", "first", "made", "created", "built", "who", "came up with")

# The shape of the question, not the words of the answer: "how long did it last" wants the
# length, "how many died" the deaths, "who won" the winner, and everything else the story.
PAST_LONG = re.compile(r"\b(?:how long|long|lasted|last)\b", re.I)
PAST_DEAD = re.compile(r"\b(?:how many|how much|died|die|dead|deaths|death toll|killed|"
                       r"casualties|lost)\b", re.I)
PAST_WON = re.compile(r"\b(?:who won|won|win|winner|victor|beat|defeat|defeated)\b", re.I)

# "what did he build" after "who was brunel" is the works, not the story again. The row's own
# tell had already been said, so the same reply came back, the repeat check threw it away and
# the second turn fell to a search punt.
PAST_BUILT = re.compile(r"\b(?:build|built|building|construct|constructed|constructing|"
                        r"design|designed|designing|engineer|engineered|famous for|known for)\b", re.I)


# A famous name is often a name someone is thinking of using, not a person they are asking about:
# "attila is a good name for a cat" wants a pet name, so it takes no row at all.
NOT_THE_THING = ("name for", "good name", "nice name", "call my", "middle name", "baby name",
                 "dog", "dogs", "cat", "cats", "puppy", "kitten", "hamster", "guinea pig",
                 "fish", "rabbit", "parrot", "horse")


def _named_row(table, text):
    """The table row a line names, longest name first, or None if it names none of them."""
    if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in NOT_THE_THING):
        return None
    best = None
    best_len = 0
    for row in table.values():
        if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in row.get("off", ())):
            continue  # "waterloo station" is not the battle
        for name in row["names"]:
            if len(name) > best_len and re.search(r"\b" + re.escape(name) + r"\b", text):
                best, best_len = row, len(name)
    return best


def _said(reading):
    """The line as read, plus the words before the reader repaired them.

    The reader turns a word ending in -in into -ing ("stalin" comes out "stalling", and "saladin"
    "salading"), which would lose a name the line plainly says. A name is a name in either form,
    so both are searched.
    """
    reading = reading or {}
    parts = (reading.get("plain"), reading.get("clean"), reading.get("text"))
    return " ".join(part for part in parts if part).lower()


def names_a_row(table):
    """A guard: the table takes a line only when the row it names is a row of its own.

    Reading the line again at the reply is not enough. An entry a callable declines has already
    won the line the lookup measured it against, so "why did world war one start" came back as
    the table (and passed the war's own cause card over) even though the table said nothing
    about it. The guard is asked while the line is being scored, so the table is not there.
    """
    def guard(reading):
        return _named_row(table, _said(reading)) is not None
    return guard


# A short question after a history answer is about the person or thing that answer named:
# "who was brunel" then "what did he build", "who was nelson" then "how did he die". The store
# does not resolve a bare "he", and the line on its own names nobody, so the row in memory is
# written into the line and the table answers it.
FOLLOW_ON_ASK = re.compile(
    r"\b(?:what did (?:he|she|it|they)|what was (?:he|she|it)|what is (?:he|she|it)|"
    r"what else|when did (?:he|she|it|they)|where did (?:he|she|it|they)|"
    r"how did (?:he|she|it|they)|how old (?:is|was|are|were) (?:he|she|it|they)|"
    r"who did (?:he|she)|why did (?:he|she|it|they)|"
    r"did (?:he|she|it|they)|was (?:he|she|it)|were (?:they|they)|what (?:was|is) that)\b",
    re.I)


def _asks_after_a_name(text):
    """Whether the line is a short question about somebody the last exchange already named."""
    return FOLLOW_ON_ASK.search(text) is not None


def names_a_row_or_a_question_after_one(table):
    """The table's guard, which also lets through a question about the last row it named.

    A bare "what did he build" names nobody, so the plain guard refuses it before the reply is
    written and the follow-up of a history answer can never reach the table. The reply itself
    reads memory, finds the row the last exchange named, and answers only when there is one.
    """
    def guard(reading):
        text = _said(reading)
        if _named_row(table, text) is not None:
            return True
        return _asks_after_a_name(text)
    return guard


def a_short_question_about_the_last_one(table):
    """The follow-up row's guard: a short question that names nothing, about the row just named.

    A long question that puts a subject of its own in the line is that subject's question, even
    when it has a "they" in it: "why did they build the berlin wall" is the wall's row, and the
    follow-up only took it because "they" and "build" were both there. Six words is the longest
    a question about a pronoun runs ("when did he finish the great eastern" is more than that).
    """
    def guard(reading):
        reading = reading or {}
        # The line as typed, not `_said`: that string holds the line up to three times over
        # (plain, clean and text), and a word count on it would never be short enough.
        text = (reading.get("clean") or reading.get("text") or "").lower()
        if _named_row(table, _said(reading)) is not None:
            return False
        if len(text.split()) > 6:
            return False
        return _asks_after_a_name(text)
    return guard


def _the_row_behind(memory, text):
    """The table row the last exchange named, when this line asks about it and names nobody."""
    if _named_row(PAST, text) is not None:
        return None
    if not _asks_after_a_name(text):
        return None
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return None
    last = turns[-1]
    if not isinstance(last, dict):
        return None
    before = " ".join(str(last.get(key) or "") for key in ("user", "bot")).lower()
    return _named_row(PAST, before)


def the_past_named(memory, reading):
    """The table's answer to the question the line asks about the thing it names."""
    text = _said(reading)
    row = _named_row(PAST, text)
    if row is None:
        row = _the_row_behind(memory, text)
    if row is None:
        return None
    if row.get("dead") and PAST_DEAD.search(text):
        return row["dead"]
    if row.get("won") and PAST_WON.search(text):
        return row["won"]
    if row.get("built") and PAST_BUILT.search(text):
        return row["built"]
    if row.get("long") and PAST_LONG.search(text):
        return row["long"]
    return row["tell"]


def the_inventor(memory, reading):
    """Who made the thing the line names, or None so another entry can answer."""
    text = (reading or {}).get("plain") or (reading or {}).get("text") or ""
    row = _named_row(MADE, text.lower())
    return row["tell"] if row is not None else None


# "Who was the first person to climb Everest" is a fact question about a deed, and the row that
# knows the deed is the answer: nothing in the knowledge base names Everest's summit, the North
# Pole or the Channel, so all three went to a greeting that read the line as the person's own
# trip ("I wasn't there, so you know better than I do. How was it?"). The deeds are the keys, so
# one row answers every way of asking who did it and when, and the reply carries the date,
# because "first" nearly always comes with "when".
#
# The deed word alone is not the question, though: "is it hard to climb everest" and "how do i
# train to climb everest" are keyed on the same two words and want their own answers, so the row
# also asks for the word that makes it a first (`FIRST_ASKS`). And a person the line mentions
# doing the deed themselves is not asking who did it first: "my sister swam the channel last
# year" is an answer about the sister, and it was given Matthew Webb's 1875 swim.
FIRST_ASKS = ("first", "firstly", "who", "whos", "who's", "when", "earliest")
FIRST_NOT_THEIRS = (
    "my sister", "my brother", "my mum", "my mom", "my mother", "my dad", "my father",
    "my son", "my daughter", "my friend", "my mate", "my husband", "my wife", "my partner",
    "my neighbour", "my neighbor", "my nan", "my gran", "my grandma", "my grandad",
    "my aunt", "my auntie", "my uncle", "my cousin", "my colleague", "my boss",
    "i swam", "i've swum", "i climbed", "i've climbed", "i flew", "i've flown",
    "she swam", "he swam", "we swam", "we climbed", "they climbed", "she climbed", "he climbed",
)
FIRST_DEEDS = [
    (("everest", "mount everest", "hillary", "tenzing"),
     "Edmund Hillary and Tenzing Norgay were the first to reach the top of Everest, on 29 May "
     "1953, at the end of the British expedition. Tenzing was a Sherpa climber from Nepal and "
     "the two of them stopped about fifteen minutes at the summit."),
    (("north pole", "arctic"),
     "Nobody can settle it. Robert Peary said he reached the North Pole in 1909, but his records "
     "were too rough to prove it, and the first party nobody disputes standing there is Ralph "
     "Plaisted's in 1968, by snowmobile. The first flight over it, and the first sighting nobody "
     "argues with, was Amundsen, Ellsworth and Nobile's airship in 1926."),
    (("south pole", "antarctic", "antarctica", "amundsen", "scott"),
     "Roald Amundsen's Norwegian team reached the South Pole first, on 14 December 1911, and "
     "Robert Scott's British team arrived on 17 January 1912 to find their tent and flag "
     "already there; Scott's party died on the way back."),
    (("channel", "english channel"),
     "Matthew Webb was the first to swim the English Channel without help, on 24 and 25 August "
     "1875, taking just under 22 hours. He swam breaststroke the whole way and was sick on the "
     "grease he was covered in."),
    (("round the world", "around the world", "circumnavigate", "circumnavigated",
      "circumnavigation", "magellan", "elcano"),
     "Ferdinand Magellan's expedition was the first to sail round the world, but he did not "
     "finish it: he was killed in the Philippines in 1521 and Juan Sebastian Elcano brought the "
     "one remaining ship, Victoria, home to Spain in September 1522."),
    (("aeroplane", "airplane", "plane", "planes", "flight", "flights", "flew",
      "wright brothers", "kitty hawk"),
     "The Wright brothers made the first powered flight on 17 December 1903 at Kitty Hawk, "
     "North Carolina: Orville flew for twelve seconds and about 36 metres, and the brothers "
     "took turns for four flights that morning, the longest fifty-nine seconds."),
    (("woman in space", "women in space", "tereshkova"),
     "Valentina Tereshkova was the first woman in space, on 16 June 1963, in Vostok 6. She "
     "orbited the Earth 48 times over almost three days, and it was another nineteen years "
     "before a second woman, Svetlana Savitskaya, flew."),
]

ENTRIES += [
    *[
        entry("first-to-" + deed[0][0].replace(" ", "-"), (deed[0], FIRST_ASKS), deed[1],
              ask=FIRST_ASKS, avoid=FIRST_NOT_THEIRS)
        for deed in FIRST_DEEDS
    ],
]

ENTRIES += [
    # A line that names the thing wants the entry about that thing: "who was the first
    # president of the united states" also reaches the row about the fifty states, and the row
    # that names the president is the answer. The bias buys the row that place; it cannot make
    # it reach a line the table names nothing in.
    entry("the-past-named", (PAST_NAMES, PAST_ASK), the_past_named, bias=2,
          guard=names_a_row_or_a_question_after_one(PAST)),

    # The same table, reached by a follow-up that names nobody: "who was nelson" then "how did
    # he die". The row's own key needs a name in the line, so the pronoun gets it a second way
    # in; the reply answers only when the last exchange named a row, so a stray "it" is nothing.
    entry("the-past-follow-on", (PAST_FOLLOW, PAST_ASK), the_past_named, bias=1,
          guard=a_short_question_about_the_last_one(PAST)),
    entry("who-invented-it", (MADE_NAMES, MADE_ASK), the_inventor, bias=2,
          guard=names_a_row(MADE)),
]
