"""Entertaining on request: a riddle, a fun fact, a quiz question, a toast, a debate.

"give me a riddle" and "tell me a fun fact" are the same ask as "tell me a joke": the line
wants an amusing thing to be said to it, not a fact looked up about a subject. `chat.py` keeps
the jokes, because a joke about a named subject has to be picked from the conversation; the
bot had nothing at all for a riddle or a fun fact, and those two lines got the search hedge.

So this is a table, not a mechanism. Two entries, each a pool of ready-made replies; the pool
is handed over whole and `pick` chooses from it, which is what keeps a person asking for three
riddles in a row from getting the same one twice. Nothing here reads the line's subject: the
entries only fire on the shape of the ask, so a line that names a subject ("tell me facts about
dogs") is left to a module that knows about dogs.

A riddle's answer goes in brackets right after the question. Given straight out, it is a riddle
the person can enjoy even if they do not want to guess; hidden behind a second turn, it would be
a question the bot cannot answer when they say "i give up".
"""
import re

from ..compose import pick
from ..compose import loss
from .lookup import entry
from .pets import ANIMAL_NOUNS

# The topic ids this domain answers (bot/understanding/topics.py).
ANSWERS = ("creative",)

# The words that make a line a request for one of these, and the words that stop it. "another"
# and "more" are here so the second request in a row works: "give me another riddle" is the same
# ask as the first one, and a pool that fires only on "give me a riddle" shrugs at it.
# A bare "like", "read" or "one" is a remark, not a request: "do you like riddles" and "i read a
# fun fact yesterday" are things people say about themselves, and a riddle there answers a question
# nobody asked. The request forms are written out instead.
ASKED = ("give", "tell", "know", "got", "have", "any", "another", "more", "share", "heard",
         "say", "suggest", "want", "wanted", "fancy", "hit", "need",
         "would like", "id like", "i d like", "read me")

# A line that wants the answer to a riddle it is holding, not a new one: "whats the answer to this
# riddle", "help me solve a riddle". Handing those a fresh riddle answers a question nobody asked.
SOLVE = ("answer", "solve", "solving", "solution", "figuring out", "guess", "guessing", "hint",
         "stuck on", "clue")

# "Is that a fact" is a raised eyebrow, not a request: the line says "I doubt it" in three words,
# and a riddle-pool fact there is an answer to a question nobody asked. "Is it a fact that ..." is
# a question about the world, which the pool cannot answer either.
DOUBTED = ("is that a fact", "thats a fact", "that s a fact", "is it a fact", "in fact",
           "fact is", "matter of fact", "as a fact", "the fact")

# "Tell me facts about dogs" is a question about dogs: the pool has no dog in it, and the reply
# would be a random fact about something else. The named subject is the giveaway.
ABOUT = ("about", "regarding", "on the subject")

# A line whose whole ask is "say something": no subject of its own to answer, and no kind named.
# Every word left after the ask vocabulary is gone is a subject, so the row stands down on
# anything that has one. The list below is only the words a bare ask is made of - the request
# (tell/give/say/know), the pronoun, the something, the qualifier, and the filler people type in
# front of it ("hey, ok so ..."). A word outside it ("work", "telly", "bees", "birthday") means
# the line is about something, and that is somebody else's answer.
_ASK_WORDS = frozenset("""
hey hi hello oi ok okay alright right so and now please go on come on then just
can could would will do you me us tell say give show share know
got have has any else
something anything a an the
interesting surprising surprise entertain amuse true cool weird mad strange lovely nice
once most thing
to hear read listen for is whats what's
id like want wanna
""".split())


def _the_line_is_only_the_ask(understood):
    """True when the line asks to be told something and names nothing itself.

    The reading's clean text, not the words the conversation added: a follow-up that leans on the
    last line is not this row's, because what it is asking about is in the other line.
    """
    clean = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    words = [word for word in re.findall(r"[a-z']+", clean.lower()) if word not in _ASK_WORDS]
    return not words


def _something_to_hear(memory, reading=None):
    """A fact or a riddle for a line that asked for something to hear, and nothing else.

    "entertain me" and "amuse me" are the two that want something to join in with, so they get a
    riddle; everything else in the row wants to be told something, so it gets a fact.

    Nothing here is given to a chat where somebody has just died. The person may still want to be
    taken out of themselves, but a fact about neutron stars read out two lines after "my mum died
    last week" is the bot talking over them, and the turn belongs to whatever reads the grief.
    """
    if loss.dying_in_the_chat(memory):
        return None
    for earlier in (memory.get("turns") or [])[-2:]:
        said = earlier.get("user") if isinstance(earlier, dict) else None
        if said and loss.reads_as_loss(said):
            return None
    text = ""
    if isinstance(reading, dict):
        text = str(reading.get("clean") or reading.get("text") or "").lower()
    if "entertain" in text or "amuse" in text:
        return pick(RIDDLES, memory, text)
    return pick(FUN_FACTS, memory, text)



# A tongue twister is the same ask as a riddle: a form the bot hands over, not a fact it looks
# up. On main "give me a tongue twister" got "That's beyond what I know well, sorry" (2026-11-09),
# and a twister is one sentence of data. Each one is a real twister plus the one instruction that
# makes it worth saying, so the reply opens with the twister itself.
TONGUE_TWISTERS = (
    "She sells sea shells by the sea shore. Say it three times, a bit faster each time.",
    "Red lorry, yellow lorry, red lorry, yellow lorry. Say it out loud five times and the "
    "fourth one catches almost everybody.",
    "Peter Piper picked a peck of pickled peppers. Start slowly and keep the p's crisp.",
    "How much wood would a woodchuck chuck, if a woodchuck could chuck wood? Try it with a "
    "biscuit in your mouth if it gets easy.",
    "A proper copper coffee pot. Short, and the hardest one here to say twice the same way.",
    "The sixth sick sheikh's sixth sheep's sick. Nobody gets through this one clean on the "
    "first go, so start it slowly.",
)

RIDDLES = (
    "What has hands but cannot clap? (A clock.) Ask for another whenever you want one.",
    "The more you take, the more you leave behind. What are they? (Footsteps.)",
    "What gets wetter the more it dries? (A towel.) Ask me for another if you fancy one.",
    "What has a head and a tail but no body? (A coin.)",
    "What has keys but cannot open a single lock? (A piano.) Another riddle is one word away.",
    "I am full of holes and still hold water. What am I? (A sponge.)",
    "What has to be broken before you can use it? (An egg.)",
    "What has one eye but cannot see? (A needle.) Ask for one more when you want it.",
    "What belongs to you, but other people use it more than you do? (Your name.)",
    "What can go all the way round the world and never leave its corner? (A stamp.)",
    "What has words but never speaks? (A book.) There are more of these if you want another.",
    "What goes up and never comes down? (Your age.)",
    "What has a neck but no head, and wears a cap? (A bottle.)",
    "What comes down but never goes up? (Rain.)",
    "Two fathers and two sons go fishing and catch three fish, one each. How? (They are a "
    "grandfather, a father and a son: three people, not four.)",
)

# Facts that are surprising and hold up. Short, one line, and each says the surprising part
# first, because that is the whole reason the person asked.
FUN_FACTS = (
    "Octopuses have three hearts and blue blood. Two hearts pump to the gills and one to the "
    "rest of the body, and the blood is blue because it carries oxygen on copper.",
    "Sharks are older than trees. Sharks have been around about 450 million years, trees about "
    "385 million.",
    "A day on Venus is longer than its year: it turns once every 243 Earth days and goes round "
    "the sun in 225.",
    "Bananas are berries and strawberries are not. Botanically a berry has its seeds inside, "
    "which a banana does and a strawberry, with its seeds on the outside, does not.",
    "Wombats do cube-shaped droppings, and the corners come from the shape of the last bit of "
    "their gut.",
    "A group of flamingos is called a flamboyance.",
    "The Eiffel Tower is about 15cm taller in summer, because the iron expands in the heat.",
    "A hummingbird's heart can beat more than 1,000 times a minute, and it can go into a sleep-like "
    "torpor at night to save energy.",
    "Sea otters hold hands while they sleep so they do not drift apart.",
    "The Moon moves about 3.8cm further away from the Earth every year. You can measure it with "
    "the mirrors the Apollo crews left behind.",
    "Honey does not go off: it is too sugary and too acidic for bacteria to grow in, so a sealed "
    "jar keeps for years - and pots from Egyptian tombs have been found still edible.",
    "Your body makes about a litre and a half of saliva a day, which is most of what you swallow.",
    "There are more possible games of chess than there are atoms in the observable universe, "
    "which is why nobody has solved it.",
    "A teaspoon of neutron star would weigh billions of tonnes on Earth, because the matter in it "
    "is packed as tightly as an atomic nucleus.",
    "Snails have thousands of teeth, arranged in rows on a ribbon called a radula, and they use "
    "them like a file.",
)

# A quiz question, for the lines that ask to be asked one: "give me a quiz question", "ask me a
# question", "quiz me", "test my knowledge". The person is the one who will answer, so the
# question goes out with its answer in brackets, the same way a riddle does: given straight out
# it is something to enjoy and check, while a question held back for a second turn is one the
# bot cannot answer when they say "i give up". Each is one line, and the checkable or surprising
# part comes first. The pool is seeded with the line, so two quiz asks in a row differ.
QUESTIONS = (
    "Which planet is tipped so far over that it rolls round the sun on its side? (Uranus - it "
    "is tilted about 98 degrees.) Ask for another whenever you like.",
    "Which is the largest ocean on Earth? (The Pacific - it covers about a third of the planet.)",
    "How many bones are there in an adult human body? (206 - a baby is born with about 300, and "
    "many of them fuse together.)",
    "What is the chemical symbol for gold? (Au, from the Latin aurum. Silver is Ag, from "
    "argentum.)",
    "Which is the only mammal that can truly fly? (The bat. A flying squirrel only glides.)",
    "What is the capital of Australia? (Canberra - not Sydney or Melbourne.) Another one is one "
    "word away.",
    "How long does sunlight take to reach the Earth? (About 8 minutes 20 seconds, so you always "
    "see the sun as it was eight minutes ago.)",
    "Which language has the most native speakers in the world? (Mandarin Chinese, with roughly "
    "940 million.)",
    "What is the smallest country in the world? (Vatican City, about 0.44 square kilometres.)",
    "Who wrote Romeo and Juliet? (William Shakespeare, around 1595.)",
    "What is the hardest natural substance on Earth? (Diamond - a 10 on the Mohs scale, with "
    "corundum, the stuff of rubies and sapphires, down at 9.)",
    "How many players from one side are on the pitch in a football match? (Eleven, goalkeeper "
    "included.)",
    "At what temperature does water boil at sea level? (100°C. On a mountain it boils lower, "
    "because there is less air pressing on it.)",
    "What gas do plants take out of the air to grow? (Carbon dioxide - they keep the carbon and "
    "give the oxygen back.)",
    "How many strings does a standard guitar have? (Six.)",
    "In which year did people first walk on the Moon? (1969 - Apollo 11, in July.)",
    "Which is the biggest planet in our solar system? (Jupiter - it is more than twice as heavy "
    "as all the other planets put together.)",
    "Which is longer, a mile or a kilometre? (A mile: about 1.6 kilometres, which is why a 5k run "
    "is a bit over three miles.)",
    "What is the tallest animal in the world? (The giraffe, up to about 5.5 metres.)",
    "How many sides does a hexagon have? (Six.) Ask for another if you fancy a harder one.",
    "What is the currency of Japan? (The yen.)",
    "Which sea has no coast? (The Sargasso Sea, in the middle of the Atlantic: it is held "
    "together by currents rather than by land.)",
)

# A fact about the thing that was named. "Tell me facts about dogs" used to be turned down on
# purpose - the fact pool above has no dog in it, so a random fact there answers a question nobody
# asked - and the line got the search hedge instead. The fix is the table, not a wider pool: keyed
# by the subject, one fact answers every way of asking for it ("fun fact about dogs", "tell me
# something interesting about bees", "did you know anything cool about space"), and a subject the
# table does not hold still gets its own answer from whatever row does hold it. Each entry is a
# tuple of the words people use for the subject and a pool of facts, so a second ask about the
# same subject moves to another fact rather than repeating.
FACTS_ABOUT = {
    "dogs": (("dog", "dogs", "puppy", "puppies", "pup", "pups", "doggy", "doggo"), (
        "A dog has about 300 million smell receptors in its nose, roughly forty times what a "
        "person has, which is why a walk is mostly reading.",
        "A dog's nose print is as individual as a fingerprint, and the wetness helps it work out "
        "which direction a smell came from.",
    )),
    "cats": (("cat", "cats", "kitten", "kittens", "kitty", "moggy"), (
        "A cat has about thirty muscles in each ear and can turn them most of the way round, and "
        "it spends two thirds of its life asleep - up to sixteen hours a day.",
        "A cat's purr runs at 25 to 150 vibrations a second, and cats also purr when they are "
        "hurt or frightened, not only when they are content.",
    )),
    "bees": (("bee", "bees", "honeybee", "honeybees", "bumblebee", "bumblebees", "bumble bee",
              "bumble bees"), (
        "A honeybee that finds food comes back and dances: a wiggle run straight up the comb "
        "means fly towards the sun, and how long she wiggles says how far.",
        "One worker bee makes about a twelfth of a teaspoon of honey in her whole life, which is "
        "why a jar is a lot of flying.",
    )),
    "elephants": (("elephant", "elephants"), (
        "Elephants talk in rumbles mostly too low for us to hear, and a herd can pick one up "
        "from several kilometres away through the ground as well as the air.",
        "An elephant's trunk has around 40,000 muscles in it and no bones at all, which is how it "
        "can pick up a single blade of grass and then lift a tree.",
    )),
    "spiders": (("spider", "spiders", "tarantula", "tarantulas"), (
        "A spider feels its web rather than sees it: one strand tells it the size of what landed "
        "and whether it is still struggling.",
        "Spider silk is stronger than steel for its weight and can stretch about four times its "
        "length before it breaks.",
    )),
    "birds": (("bird", "birds", "sparrow", "sparrows", "robin", "robins"), (
        "A bird's lungs fill in one direction only, with air sacs behind it, which is how a "
        "bar-tailed godwit flew 12,000 km without stopping.",
        "Most small birds weigh less than the batteries in a television remote, and a blue tit "
        "eats close to its own body weight in food every day in winter.",
    )),
    "whales": (("whale", "whales", "dolphin", "dolphins"), (
        "A blue whale's heart is about the size of a small car and slows to two beats a minute "
        "when it dives, and its call carries hundreds of kilometres through water.",
        "Dolphins sleep one half of the brain at a time, keeping the other half and one eye on "
        "watch so they remember to breathe.",
    )),
    "penguins": (("penguin", "penguins"), (
        "Penguins cannot taste sweetness - the gene for it is broken in them - and they can drink "
        "sea water because a gland above the eye filters the salt out.",
        "A penguin's knees and thighs are inside its body, which is why it looks like it has none "
        "and why it waddles instead of striding.",
    )),
    "butterflies": (("butterfly", "butterflies", "moth", "moths"), (
        "Butterflies taste with their feet, and they cannot fly once their body drops below about "
        "15C, which is why they sit with their wings open in the sun.",
        "A caterpillar turns almost all of itself into soup inside the chrysalis and rebuilds from "
        "the same cells, so the butterfly is not the caterpillar with wings on.",
    )),
    "trees": (("tree", "trees", "oak", "oaks", "forest", "forests", "woodland"), (
        "Trees pass sugar to each other through fungi in the soil: a beech can feed a shaded "
        "seedling of its own kind through that network.",
        "A big oak can pull hundreds of litres of water a day up its trunk, and the tallest trees "
        "are limited by how high water can be lifted, not by how strong the wood is.",
    )),
    "rain": (("rain", "raining", "rainy", "weather", "thunder", "thunderstorm", "lightning"), (
        "The smell after rain is not the rain: it is geosmin, made by soil bacteria, and a human "
        "nose can pick it out at a few parts per trillion.",
        "Lightning heats the air around it to about 30,000C, five times the surface of the sun, "
        "and the bang is that air expanding at once.",
    )),
    "sleep": (("sleep", "sleeping", "insomnia", "dream", "dreams", "dreaming"), (
        "After about seventeen hours awake, people perform about as badly as someone at the "
        "drink-drive limit, which is why a late night feels like a hangover.",
        "The brain flushes waste out of itself mostly while you sleep, using a channel that "
        "opens up in deep sleep and barely runs when you are awake.",
    )),
    "coffee": (("coffee", "caffeine", "espresso"), (
        "Caffeine does not give you energy: it blocks the receptor that tells you you are tired, "
        "so the tiredness piles up behind it and lands when the coffee wears off.",
        "Coffee was chewed, not drunk, for centuries before anyone thought to brew it, and the "
        "plant is a fruit stone: the bean is the seed of a cherry.",
    )),
    "chocolate": (("chocolate", "cocoa", "cacao"), (
        "Chocolate was drunk for most of its history - the Aztecs took it cold, bitter and spiced "
        "with chilli - and milk chocolate only arrived in 1875.",
        "Cocoa trees grow in the shade of taller ones, and a tree takes four or five years before "
        "it makes a pod worth picking.",
    )),
    "cheese": (("cheese", "cheddar", "brie"), (
        "Cheese is the same few ingredients with different bacteria, and much of the flavour is "
        "made at the rind: a washed rind is wiped with brine so the smellier bacteria win.",
        "Hard cheese keeps for months because most of the water has been pressed and salted out "
        "of it, which is what stops the mould that would spoil milk.",
    )),
    "brain": (("brain", "brains", "memory", "memories"), (
        "Your brain is about two per cent of your weight and uses about a fifth of your energy, "
        "and it has no pain receptors of its own - a headache comes from the layers and vessels "
        "around it.",
        "A memory is not stored in one place: remembering something re-runs the same pattern "
        "across the brain, which is why a memory changes a little each time you recall it.",
    )),
    "sun": (("sun", "sunlight", "sunshine"), (
        "The sunlight on your arm is old: the energy took tens of thousands of years to work its "
        "way out of the sun's core, and then eight minutes to cross to you.",
        "The sun is 99.8 per cent of the mass of the solar system - everything else, planets "
        "included, is the leftover dust.",
    )),
    "sea": (("sea", "ocean", "oceans", "seabed", "sea bed"), (
        "We have better maps of Mars than of the sea floor: about three quarters of it has never "
        "been surveyed in detail, and the deepest trench would swallow Everest with two "
        "kilometres to spare.",
        "The sea is salty because rain has been washing rock into it for billions of years, and "
        "the water that leaves by evaporation takes none of the salt with it.",
    )),
    "space": (("space", "universe", "galaxy", "galaxies", "star", "stars", "planet", "planets"), (
        "There are more stars in the observable universe than grains of sand on every beach on "
        "Earth, and the space between them is still stretching.",
        "A day on the International Space Station is 90 minutes long, because that is how long it "
        "takes to go round the Earth once.",
    )),
    "music": (("music", "song", "songs", "melody"), (
        "The shiver down your spine at a good bit of music comes before the moment you expect, "
        "not on it: the brain is rewarding itself for predicting what comes next.",
        "Music uses the same reward circuits as food and friends, which is why a song can lift a "
        "mood in seconds and a smell cannot.",
    )),
    "money": (("money", "cash", "banknotes", "coins"), (
        "Most money is not paper: only a small fraction of what is counted as money exists as "
        "notes and coins, and the rest is numbers in accounts.",
        "Notes are printed on cotton and linen, not wood pulp, which is why a note survives the "
        "wash better than a receipt does.",
    )),
    "beetles": (("beetle", "beetles", "insect", "insects", "bug", "bugs"), (
        "One in four of every animal species that has ever been named is a beetle - about "
        "400,000 of them - so a beetle is the safest guess for any unnamed insect.",
        "Insects breathe through holes in their sides instead of lungs, which is part of why "
        "there are no insects the size of a cat.",
    )),
    "dinosaurs": (("dinosaur", "dinosaurs", "t rex", "t-rex", "tyrannosaurus"), (
        "Birds are dinosaurs: the line that survived the asteroid is the one that became birds, "
        "which is why a chicken's skeleton is closer to a T. rex than a lizard's is.",
        "Many dinosaurs were feathered and coloured, not scaly and green: the skin we have fossil "
        "evidence for on several of them is a coat of feathers.",
    )),
    "mountains": (("mountain", "mountains", "everest", "himalayas", "alps"), (
        "Everest is the highest, not the tallest: from its base on the sea floor, Mauna Kea in "
        "Hawaii is over ten kilometres tall.",
        "Everest is still going up by a few millimetres a year as India pushes into Asia, and "
        "the summit is a marine limestone - it was sea floor once.",
    )),
    "water": (("water", "ice", "snow"), (
        "Water is the only common substance that is lighter as a solid, which is why ice floats "
        "and a pond freezes from the top down instead of from the bottom.",
        "Hot water can freeze faster than cold in some conditions - it has a name, the Mpemba "
        "effect - and nobody has a settled explanation for it.",
    )),
    "octopus": (("octopus", "octopuses", "octopi"), (
        "An octopus can change colour and the texture of its skin in under a second, and it is "
        "colour-blind - nobody knows for certain how it matches colours it cannot see.",
        "Two thirds of an octopus's neurons are in its arms, so an arm can taste what it touches "
        "and work on its own while the head does something else.",
    )),
    "bananas": (("banana", "bananas"), (
        "The banana plant is not a tree: it is the largest herb, and what looks like a trunk is "
        "the bases of the leaves packed together.",
        "A banana is slightly radioactive because it is rich in potassium, and so is a potato - "
        "the dose from either is far too small to matter.",
    )),
    "body": (("body", "bodies", "human body", "the body"), (
        "Your body makes about a litre of new bone a year of the two or so kilograms it carries, "
        "which is why a broken bone heals back stronger at the break.",
        "You are taller in the morning: the discs between your vertebrae squash flat over a day "
        "and spring back overnight, up to a centimetre and a half.",
    )),
    "chilli": (("chilli", "chilli pepper", "chillies", "chili", "chilies", "jalapeno",
                "jalapenos", "hot sauce"), (
        "Chilli heat is not a taste: capsaicin trips the receptor that senses a hot pan, which "
        "is why your mouth reads it as burning and why milk works where water does not.",
        "The hottest chillies are measured in Scoville units, and a habanero can be a hundred "
        "times hotter than a jalapeno that looks the same size.",
    )),
}

# The ask half of the row, kept to what a person says when they want to be told something. A bare
# "tell me" or "about" is not in it: those belong to whatever row holds the subject, so "tell me
# about my dog's food" and "how do i stop my dog pulling" keep their own answers.
_FACT_ASKS = ("fun fact", "fun facts", "random fact", "random facts", "interesting fact",
              "interesting facts", "true fact", "cool fact", "cool facts", "weird fact",
              "weird facts", "surprising fact", "surprising facts", "amazing fact",
              "amazing facts", "facts about", "fact about", "facts on", "fact on",
              "something interesting", "something cool", "something surprising",
              "something amazing", "did you know", "learn something", "a fact", "fact",
              "facts")

# A line with a dog in it is not automatically a line about dogs. The subject words here are
# common ones, so the fact row has to hear the line say it is a question about the animal and not
# a worry about one: "my dog is sick", "did you know my cat died" and "how do i stop the dog
# barking" are somebody's problem, and a fact about nose prints is an answer to nothing.
_FACT_NOT = ("died", "dead", "dying", "passed away", "put down", "euthan", "lost my", "grieving",
             "buried", "buried", "sick", "ill", "poorly", "vet", "vets", "hurt", "hurting",
             "allergic", "bite", "bites", "bitten", "sting", "stings", "stung", "attack",
             "attacked", "afraid", "scared", "phobia", "hate", "hates", "how do i", "how to",
             "how can i", "why does", "why do", "why is", "my dog", "my cat", "my puppy",
             "my kitten", "my child", "my son", "my daughter", "is it true", "is that true",
             "true that", "myth", "fact check", "in fact", "as a fact", "matter of fact",
             "the fact", "that s a fact", "myth or fact")


def _said_here(clean, word):
    """True when `word` is said in `clean` as a word, not inside a longer one."""
    return re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", clean) is not None


# A line that counts something out is asking for the number, and the row that knows it answers:
# "did you know octopuses have three hearts" was a fact about the arms, while the octopus rows
# give the three hearts and what each one pumps. The words are whole words, not `avoid` phrases,
# because "two" sits inside "towards" and "ten" inside "tenant".
_COUNTED = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
            "eleven", "twelve", "twenty", "hundred", "thousand", "million", "billion",
            "how many", "how much", "how long", "how old", "how tall", "how big", "how far")


def _the_line_does_not_state_the_fact(reading):
    """False when the line counts something out: that number has its own row."""
    reading = reading if isinstance(reading, dict) else {}
    clean = " " + str(reading.get("clean") or reading.get("text") or "").lower() + " "
    return not any(_said_here(clean, word) for word in _COUNTED)


def _a_fact_about(memory, reading):
    """A fact about the subject the line names, or None when it names none this table holds."""
    reading = reading if isinstance(reading, dict) else {}
    clean = " " + str(reading.get("clean") or reading.get("text") or "").lower() + " "
    if not any(_said_here(clean, ask) for ask in _FACT_ASKS):
        return None
    if any(_said_here(clean, word) for word in _FACT_NOT):
        return None
    for _subject, (words, facts) in FACTS_ABOUT.items():
        if any(_said_here(clean, word) for word in words):
            return pick(facts, memory, clean)
    return None


# The two halves of the ask, because one long phrase is worth the same as a short one and a row
# keyed on the phrase alone scored 3, under the matcher's minimum. "quiz me", "quiz question",
# "trivia" and "test me" are what is wanted; the second half is the person putting themselves
# forward for it ("me", "us", "another"). A line that only mentions a quiz ("the quiz starts at
# 8", "how do i make a quiz") names nothing from the second half, so it stays news or a how-to.
QUIZ_ASK = ("quiz me", "quiz", "quizzes", "quiz question", "quiz questions", "trivia",
            "trivia question", "trivia questions", "general knowledge",
            "general knowledge question", "test my knowledge", "test me",
            "ask me a question", "ask me some questions", "ask me something",
            "a question to answer", "questions to answer", "throw me a question",
            "throw me one", "send me a question", "give me a question",
            "chuck me a question", "hit me with a question", "ask us a question",
            "ask me another question", "ask me another one", "ask me something else")
QUIZ_ME = ("me", "us", "question", "questions", "quiz", "quizzes", "trivia", "something",
           "some", "any", "another", "more", "one", "please", "pls", "again", "knowledge")

# A line with a quiz in it that is not asking to be asked one: a pub quiz, a quiz night, a quiz
# on tomorrow, and one somebody wants help to write. Those are news or a request about the quiz
# itself, and a general-knowledge question there answers something nobody asked. The school
# subjects are here too, because "quiz me on my spellings" is a spelling question first, which
# the school rows answer better.
QUIZ_NOT_A_QUIZ = ("tomorrow", "tonight", "night", "pub", "starts", "started", "team", "show",
                   "revise", "revision", "revising", "exam", "exams", "make a quiz",
                   "writing a quiz", "write a quiz", "host", "rounds", "scores", "score",
                   "spellings", "spelling", "times tables", "maths", "any good", "good at")

# What a person names when it is not an animal: the pet row stands down for these by name, so the
# same three-name answer works for all of them. Nothing here is a suggestion about taste; it is the
# brief plus three names that fit it, which is what "help me name my boat" is asking for.
THING_NAMED = ("boat", "boats", "yacht", "kayak", "canoe", "band", "bands", "pub", "cafe",
               "café", "shop", "business", "company", "startup", "podcast", "quiz team",
               "team", "sourdough starter", "sourdough", "starter", "wifi", "wi-fi", "network",
               "campervan", "van", "motorhome", "car", "bike", "motorbike", "allotment plot",
               "house", "flat")

NAMING_ASKED = ("what should i name", "what should we name", "what should i call",
                "what should we call", "what to name", "what could i name", "name for my",
                "name my", "name our", "name ideas", "ideas for a name", "any good names",
                "good name", "good names", "help me name", "suggest a name",
                "suggest some names", "what would you call", "names for my", "names for a")

BOAT_NAMES = ("Second Wind", "Kittiwake", "Slow Motion")
BAND_NAMES = ("The Late Bus", "Half Hour", "Paper Lions")
SHOP_NAMES = ("Two Rivers", "The Workshop", "Day One")
TECH_NAMES = ("Tin Roof", "Long Way Round", "The Quiet Bit")
PODCAST_NAMES = ("Two Chairs", "The Long Way", "Kitchen Table")

GROUP_GAMES = (
    "Two truths and a lie: each of you says three things about yourself, two true and one made "
    "up, and the rest guess the lie - a point for each correct guess, and you tell them the "
    "answer before the next person goes. Three is the right number of players upwards, and the "
    "lies get better by the second round.",
    "Would you rather: one of you puts two bad options against each other and everybody has to "
    "pick one and say why in a sentence - 'would you rather be ten minutes late every day or "
    "an hour late once a week'. The reasons are the fun part, not the choice.",
    "Twenty questions: one person thinks of a person, a place or a thing, the others ask "
    "questions that can only be answered yes or no, and twenty questions has to be enough. It "
    "works in a car, at a table, and with children from about six.",
    "The alphabet game for a journey: find each letter of the alphabet in order on road signs, "
    "number plates or shop fronts, and nobody may use a word twice. First to Z wins, and the "
    "hard letters are the fun ones.",
)

DRAWING_PROMPTS = (
    "Draw an animal wearing a hat it would never choose. Give them three minutes and no "
    "sharpener: the limit is what gets a drawing finished, and a finished silly one beats a "
    "perfect blank page.",
    "Draw the kitchen as a mouse would see it - everything enormous and books on the floor. "
    "One shape to start with stops the 'I don't know what to draw' that a blank page causes.",
    "Draw a house for the person sitting next to you: what is on the roof, what is behind the "
    "door. Ask them what is missing afterwards and let them add it in pen.",
    # "what should i draw" was answered with the swap-one-line game, which needs a second
    # person: the pool is four things one person can sit down and do, so the last one is a
    # constraint rather than a game.
    "Draw the same mug three times: once in one line without lifting the pen, once looking only "
    "at the mug and never at the paper, once in under a minute. Three bad drawings beat one "
    "careful blank page, and the second one usually surprises you.",
)

WRITING_PROMPTS = (
    "Someone finds a key that fits no lock they own, and keeps it for a month before they find "
    "out what it opens. Two hundred words, no planning, and do not give it an ending - stop "
    "where the interesting part starts.",
    "Write the same small scene twice: once from the person who is late, once from the person "
    "waiting. Nothing has to happen in either; the two ways of seeing the same ten minutes are "
    "the whole exercise.",
    "A character has to tell a lie to somebody they love, on a day that is otherwise ordinary. "
    "Write the ten minutes before they do it and leave the lie out of the page.",
    "Describe a room from the point of view of the smell in it. Three hundred words, and no "
    "person may be named: it forces the details out of you.",
)


def _the_thing_being_named(understood):
    """The thing of the ones above that the line names, longest phrase first."""
    text = " " + str((understood or {}).get("clean") or "") + " "
    best = ""
    for one in THING_NAMED:
        if len(one) > len(best) and (" " + one + " ") in text.replace("'s", ""):
            best = one
    return best


def _the_game_the_line_names(memory, reading=None):
    """The game the line names, or one of the pool when it names none.

    "play two truths and a lie" is a request for that game, and a pool that only fires on the
    shape of the ask answered it with the alphabet game.
    """
    understood = reading if isinstance(reading, dict) else {}
    text = " " + str(understood.get("clean") or "") + " "
    for marks, line in ((("two truths", "2 truths", "truths and a lie", "truth or lie"),
                         GROUP_GAMES[0]),
                        (("would you rather",), GROUP_GAMES[1]),
                        (("twenty questions", "20 questions"), GROUP_GAMES[2]),
                        (("alphabet",), GROUP_GAMES[3])):
        for mark in marks:
            if mark in text:
                return line
    # the alphabet game is the one game in the pool that needs a journey to play, so a line about
    # a table or a rainy afternoon is offered the other three
    pool = GROUP_GAMES
    if not any(word in text for word in (" car", " journey", " travel", " flight", " drive",
                                         " road", " trip", " train", " plane", " airport")):
        pool = GROUP_GAMES[:3]
    return pick(pool, memory, text)


def _a_name_for_the_thing(memory, reading=None):
    """Three names and the rule they follow, for the thing the line names."""
    understood = reading if isinstance(reading, dict) else {}
    thing = _the_thing_being_named(understood)
    if thing in ("boat", "boats", "yacht", "kayak", "canoe"):
        lead, names = "a boat", BOAT_NAMES
    elif thing in ("band", "bands", "quiz team", "team"):
        lead, names = "a band", BAND_NAMES
    elif thing == "podcast":
        lead, names = "a podcast", PODCAST_NAMES
    elif thing in ("pub", "cafe", "café", "shop", "business", "company", "startup"):
        lead, names = "a business", SHOP_NAMES
    else:
        lead, names = "it", TECH_NAMES
    return ("Short, sayable and easy to spell beats clever: %s, %s or %s. Say it out loud in a "
            "sentence - 'this is %s' - before you commit, and check nobody selling the same thing "
            "already has it." % (names[0], names[1], names[2], names[0].lower()))


def _pool(options):
    """A reply that chooses from a pool, seeded with the line.

    Without the line, every first turn of every conversation chooses the same item - the seed is
    the turn number - so "give me a riddle" and "tell me a fun fact" would open alike and a chat
    of one riddle would always be the same riddle. With it, the choice moves with what was asked
    and stays the same for the same words, which is what a comparison run needs.
    """
    def choose(memory, reading=None):
        text = ""
        if isinstance(reading, dict):
            text = str(reading.get("text") or reading.get("clean") or "")
        return pick(options, memory, text)
    return choose


# "How do i make toast" is bread and "how do i run a pub quiz" is an evening's plan: the pools
# below only answer a line that asks to be given the thing itself.
HOW_TO = ("how do i", "how do you", "how to", "why does", "why do", "what is the best way",
          "recipe", "make", "making", "cook", "cooking", "recipe for")

# A toast is asked for with the occasion in the line - a wedding, a birthday, a retirement, a
# last day - so the pool is split by occasion: a wedding line handed the birthday toast reads as
# an answer to a question nobody asked. Each line is a toast that can be said out loud as it
# stands, because the person asked for one, not for advice on how to write one.
WEDDING_TOASTS = (
    "\"To Anna and James - may you always be as easy with each other as you were on the day you "
    "met.\" Raise the glass on the names and sit down: twenty seconds is a good toast.",
    "Name the couple and one thing you have watched them do well together, then finish with four "
    "words: \"To Sarah and Tom - to a long and happy life.\"",
    "\"To the two of you - may the good days outnumber the washing up.\" Short and warm beats "
    "clever, and everyone drinks on it.",
)
BIRTHDAY_TOASTS = (
    "\"To Dan - forty is the age where you finally stop pretending to like the music at "
    "parties.\" One line and one laugh, then everyone drinks and nobody has to answer.",
    "Name the person and one thing you like about them, then raise the glass: \"To Ruth - the "
    "only person here who would drive across town for a cake.\"",
)
RETIREMENT_TOASTS = (
    "\"To Brian - thirty years of getting there before the rest of us, and now every day is "
    "Saturday.\" Then hand over whatever joke present you brought.",
    "Name the years and one thing they were known for, then raise the glass: \"To Pat - the only "
    "person who could fix the printer. Enjoy the lie-ins.\"",
)
LEAVING_TOASTS = (
    "\"To Maya - the best thing about Mondays for four years. Don't be a stranger.\" Keep it to "
    "one detail you actually saw, and stop before it turns into a speech.",
    "Say what the team will miss in one sentence and finish with the glass: \"To Tom - the only "
    "one who ever read the whole email. Good luck out there.\"",
)
PLAIN_TOASTS = (
    "Name the person, one real thing they did that you saw yourself, then raise the glass: "
    "\"To Ruth - she has fed half this room and never once let on how much work it was.\" That "
    "is the whole toast.",
    "Three parts, in this order: who you are raising the glass to, one thing they did, and four "
    "words to finish - \"To Sarah and Tom.\" A toast is twenty seconds; a speech is longer and "
    "wants a joke at the start.",
    "If you are nervous, write five words on your hand and say them slowly: \"To health, "
    "happiness and a quiet Sunday.\" Said warmly, a short toast lands better than a long one read "
    "out.",
)

# The occasion words, most specific first: a wedding line that also says the word birthday (an
# anniversary next to a birthday) is still a wedding.
TOAST_OCCASIONS = (
    ("wedding", ("wedding", "bride", "groom", "married", "marriage", "couple", "engagement",
                 "anniversary"), WEDDING_TOASTS),
    ("birthday", ("birthday", "birthdays", "forty", "fifty", "sixty", "seventy", "eighteenth",
                  "eighteen", "twenty first", "21st", "40th", "50th", "60th", "70th"),
     BIRTHDAY_TOASTS),
    ("retirement", ("retirement", "retiring", "retired", "last day at work", "pension"),
     RETIREMENT_TOASTS),
    ("leaving", ("leaving", "new job", "moving on", "leaving do", "goodbye", "farewell",
                 "colleague"), LEAVING_TOASTS),
)


def _toast(memory, understood):
    """The toast for the occasion the line names, or a plain one when it names none."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    joined = " ".join(words)
    for _, occasion_words, pool in TOAST_OCCASIONS:
        if any(word in joined for word in occasion_words):
            return pick(pool, memory, joined)
    return pick(PLAIN_TOASTS, memory, joined)


DEBATE_TOPICS = (
    "This house would ban all cars from city centres. (Good for a school debate: clean arguments "
    "on both sides, air quality and business against freedom and disability access.)",
    "Social media does more harm than good to teenagers. (Evidence both ways, and everyone has a "
    "view - the safest topic for a group that does not agree on much.)",
    "This house believes homework should be scrapped for primary school children.",
    "University should be free for everyone, paid for by general taxation.",
    "This house would make voting compulsory, with a small fine for not voting.",
    "Artificial intelligence will do more good than harm to ordinary jobs over the next twenty years.",
    "This house believes professional athletes are paid too much.",
    "This house would tax sugary drinks to pay for free school meals.",
    "Zoos do more harm than good for the animals in them.",
    "This house believes that four-day working weeks should be the standard.",
)


def _the_person_is_the_one_quizzed(understood):
    """The row answers only when the line asks for a question to answer.

    The key words alone find "a question" and "me" in a line about somebody else: "she gave me a
    question to answer", "he asked me a question", "my daughter asked me a question" all carry
    them, and the person had said nothing about wanting to be quizzed. The reading says which
    way round it is (`wants_a_quiz`: the hand-over verb opens the line, or stands behind nothing
    but a modal or a courtesy), so a third person handing a question over gets its own answer
    back and the ask still gets a question.
    """
    return bool(understood.get("wants_a_quiz"))


# The asks that name no kind: "tell me something interesting", "surprise me", "got anything
# interesting". The phrases are the keys, and the guard below is what a line with a subject of
# its own has to get past.
SOMETHING_ASKED = ("something interesting", "anything interesting", "something surprising",
                   "tell me something", "say something", "something to tell me",
                   "surprise me", "entertain me", "amuse me",
                   # "whats the most interesting thing you know" is the same ask with the
                   # superlative in it, and "for once" is how a friendly demand is made
                   "interesting thing", "surprising thing",
                   # "tell me something cool" and "got anything cool to tell me" are the same
                   # ask in the word people use for it when they mean interesting
                   "something cool", "anything cool", "something mad", "anything mad",
                   "something weird", "anything weird")

ENTRIES = [
    # not a bare "few words": a parent saying "my 2 year old only says a few words" was given
    # a toast to read out. The words have to be asked for, which is what the longer phrases and
    # the second group together say.
    entry("toast", (("toast", "toasts", "few words for", "few words to say",
                     "few words about", "few words at", "few words on"),
                    ASKED + ("give me", "say", "write me")),
          _toast,
          # "toast" is bread far more often than it is a speech: the kitchen rows own the food,
          # and this pool only answers the ask for something to say out loud.
          # "toasted" is left out of this list on purpose: an avoid word is matched loosely, so
          # it would stand the row down for the ask itself ("give me a toast"), which is the same
          # word. "toaster" and the rest name the food and stay.
          # "draft" and "speech" are the asking-how row's words (wording.py's
          # write-a-toast), which gives a length and a structure rather than a toast to say; a
          # line that asks for one to say is this row's, and `bias` is what wins it the tie.
          avoid=HOW_TO + (
                          # "can i give him toast" is bread for a baby, and "give" is in ASKED:
                          # a toast handed to a person is never the speech.
                          "give him", "give her", "give them", "gives him", "gives her",
                          "him toast", "her toast", "my baby", "my son", "my daughter",
                          "my toddler", "toast fingers",
                          # A toast handed to an animal is its dinner, not a speech:
                          # "can i give my dog toast" and "should i give my golden retriever
                          # toast" were both the best-man card.
                          ) + ANIMAL_NOUNS + (
                          "bread", "cheese", "avocado", "butter", "toaster", "burnt",
                          "burn", "burned", "sandwich", "breakfast", "marmite", "beans",
                          "slice", "slices", "loaf", "egg on", "cinnamon",
                          # What the person eats with it, and when: "i usually have cereal and
                          # toast" reached this row through "have" and "toast" and was answered
                          # with a wedding toast to read out. The list above held the bread and
                          # the meal, so the words left out were the ones people say around it -
                          # the cereal, the jam, the time of day.
                          "cereal", "cereals", "cornflakes", "porridge", "granola", "weetabix",
                          "jam", "marmalade", "peanut butter", "honey", "banana", "yoghurt",
                          "yogurt", "fruit", "eggs", "scrambled", "poached", "fry up",
                          "every morning", "each morning", "in the morning", "for breakfast",
                          "usually have", "have toast", "had toast", "has toast", "eats toast",
                          "eating toast", "toast and", "and toast", "toast with", "toast on",
                          "plain toast", "dry toast", "piece of toast", "bit of toast",
                          "draft", "speech", "script"),
          bias=2),
    # "How do i raise a toast at a wedding" is the speech, and on main it was the pay-rise
    # card: "raise" was read as asking for more money, and the toast row had already stood
    # down for "how do i". The phrasal forms are always the glass, not bread or a pay review,
    # so they answer even when the line opens on how.
    entry("raise-a-toast",
          (("raise a toast", "raise the toast", "raise a glass", "raise the glass",
            "propose a toast", "propose the toast", "give a toast", "say a few words"),
           ("how do i", "how to", "wedding", "birthday", "dinner", "party", "speech",
            "what do i say", "say", "few words", "evening", "celebrate", "celebration")),
          _toast,
          avoid=("bread", "butter", "cheese", "avocado", "marmite", "beans", "slice",
                 "toaster", "burnt", "breakfast", "toast fingers", "pregnant", "baby"),
          bias=2),
    entry("debate-topic", (("debate", "debates", "debate topic", "debate topics",
                            "discussion topic", "discussion topics", "argument topic"),
                           ASKED + ("topic", "topics", "debate", "what should we", "suggest")),
          _pool(DEBATE_TOPICS),
          # "debating" is not in this list for the same reason: loosely matched it would take
          # "give me a topic for a debate" with it.
          # "for a class" and "for school" are how people say where the debate is, so those
          # words stay out of the avoid list; the essay and homework phrasings are a different
          # ask and are kept out by name.
          avoid=HOW_TO + ("essay", "essay title", "statement", "assignment",
                          "public speaking", "nerves", "nervous",
                          "speech", "argue with", "argument with", "my partner", "my friend",
                          "my mum", "my dad", "my boss")),
    entry("riddle", (("riddle", "riddles", "brain teaser", "brainteasers", "brain teasers",
                      "word puzzle", "lateral thinking puzzle",
                      # "entertain me" asks for something to do, and a riddle is the one thing
                      # in this domain that asks the person to join in
                      "entertain me", "amuse me"),
                     ASKED + ("entertain", "amuse")),
          _pool(RIDDLES), avoid=SOLVE + ABOUT),
    # "tongue twister" is a phrase worth 3 on its own, under the score an entry needs, so the
    # asking words above carry it: "give me a tongue twister", "know any tongue twisters".
    entry("tongue-twister", (("tongue twister", "tongue twisters", "twister", "twisters"),
                             ASKED + ("twister", "twisters", "tongue", "say", "hard")),
          _pool(TONGUE_TWISTERS),
          # a line about a twister somebody is practising or writing wants help with their own,
          # and "why do tongue twisters work" is a science question
          avoid=SOLVE + ABOUT + ("why do", "why does", "practice", "practising", "practicing",
                                 "write", "writing", "made up", "meaning", "mean")),
    # A fact about the thing the person named. The pool above answers "give me a fun fact" and
    # turns down anything with "about" in it, because a random fact is not a fact about dogs; with
    # the table keyed by the subject, the same row can hold both. It is a point of bias in front
    # of the random pool so "dogs fun fact" lands here and not on the pool.
    entry("fact-about-a-thing",
          (tuple(word for words, _facts in FACTS_ABOUT.values() for word in words),
           _FACT_ASKS),
          _a_fact_about, avoid=_FACT_NOT, bias=1,
          guard=_the_line_does_not_state_the_fact),
    entry("fun-fact", (("fun fact", "fun facts", "random fact", "random facts",
                        "interesting fact", "interesting facts", "a fact", "true fact"),
                       # "whats a fun fact" and "what is a random fact" name the thing and ask it
                       # with no request word in the line at all; the key was there, the ask not.
                       ASKED + ("what", "whats", "what's", "what is")),
          _pool(FUN_FACTS), avoid=ABOUT + DOUBTED),
    # The ask that names no kind at all: "tell me something interesting", "surprise me", "anything
    # interesting". Nothing in the line says whether it wants a fact or a riddle, and the pools are
    # exactly what was asked for. The guard is what keeps this row off the lines that only look
    # like it: "did you see anything interesting", "anything interesting happen at work today",
    # "she wants to surprise me" and "my son wont eat anything interesting" are all about
    # something else, so only a line with nothing in it but the ask is answered here.
    entry("something-to-hear", (SOMETHING_ASKED, ASKED + SOMETHING_ASKED),
          _something_to_hear, avoid=ABOUT + DOUBTED, guard=_the_line_is_only_the_ask),
    entry("quiz-question", (QUIZ_ASK, QUIZ_ME),
          _pool(QUESTIONS), avoid=QUIZ_NOT_A_QUIZ, guard=_the_person_is_the_one_quizzed),
    # "give me ideas for a quiz night" was the search hedge: the quiz row holds out the word
    # "night" on purpose, because a quiz that starts at eight is news rather than a request to be
    # quizzed, and no row answered someone putting a quiz on. Writing one is a shape, so the
    # rounds go in one answer.
    entry("quiz-night",
          (("quiz night", "pub quiz", "quiz idea", "quiz ideas", "quiz round", "quiz rounds",
            "quiz questions for", "quiz for a party", "family quiz", "quiz with friends",
            "write a quiz", "run a quiz", "host a quiz", "make a quiz", "a quiz for"),
           # the second half is a real ask, not the little words of a sentence: "me and my mate
           # are doing a pub quiz thursday" is somebody telling you their week, and "a" and "for"
           # were enough to make it a request to write one
           ("ideas", "idea", "rounds", "round", "questions", "how", "what should", "what rounds",
            "suggest", "help", "give me", "want some", "need some", "plan", "tips", "any",
            "good", "night", "party")),
          ("Six rounds of ten questions is the shape people finish: a picture round, a music "
           "intro round, general knowledge, a round about your own street or family that nobody "
           "can revise for, a true-or-false round, and one joker round where a wrong answer costs "
           "a point instead of scoring nothing. Teams of four to six, questions short enough to "
           "read aloud twice, the hardest round in the middle rather than at the end, and the "
           "answers written down as you go."),
          # "quiz me" is a request to be asked one, a team name has its own row, and a quiz
          # weighed up as a plan ("is a pub quiz a good idea for a birthday") is the party answer
          avoid=("quiz me", "quiz us", "team name", "team names", "name our", "name the",
                 "good idea", "bad idea", "worth it", "is it a good", "is a pub quiz a",
                 "should we do", "shall we do", "we are doing", "we're doing", "im doing",
                 "i'm doing")),

    # "what should i name my boat" was the search hedge: the pet-name row names boats in its
    # avoid list (rightly - a boat is not a pet), and nothing else answered a thing being named.
    entry("name-a-thing",
          (THING_NAMED, NAMING_ASKED),
          _a_name_for_the_thing,
          # a pet has its own answer, and an animal, a baby and a plant are somebody's pet,
          # child or garden rather than a thing with a name in it
          ask=THING_NAMED + ("name", "names", "named", "naming", "call", "called", "suggest",
                             "ideas", "idea", "any", "good", "clever", "help", "pick",
                             "come up with", "think of"),
          avoid=("cat", "cats", "kitten", "dog", "dogs", "puppy", "pup", "hamster", "rabbit",
                 "bunny", "guinea pig", "parrot", "budgie", "fish", "horse", "pony", "tortoise",
                 "pet", "pets", "baby", "babies", "child", "children", "son", "daughter",
                 "plant", "plants", "garden", "allotment",
                 # a name already given is the memory store's question, and a fact about a name
                 # is not a suggestion
                 "whats my", "what is my", "named after", "mean", "means", "meaning",
                 "how do i change", "change my", "rename",
                 # a band, a wifi network, a quiz team and a sourdough starter each have their
                 # own row, and those answers are better than three names off a list
                 "band", "bands", "wifi", "wi-fi", "network", "quiz team", "quiz teams",
                 "team", "teams", "sourdough", "sourdough starter", "starter")),
    # The games people ask for in a group that need nothing but the people in the room. Each line
    # is a game that can be played as it stands, because the ask is "play something with us".
    entry("group-game",
          (("two truths and a lie", "2 truths and a lie", "truths and a lie",
            "truth or lie", "would you rather", "never have i ever", "twenty questions",
            "20 questions", "alphabet game", "the alphabet game", "party game",
            "party games", "car game", "car games", "game for the car", "games for the car",
            "game for a long journey", "games for a long journey", "game for the kids",
            "games for the kids", "games for a group", "game for a group", "icebreaker",
            "ice breaker", "icebreakers", "games to play", "game", "games",
            # "what should i play with my kids" is the same ask as "games for the kids"
            "play with my kids", "play with the kids", "play with my children",
            "play with the children", "play with my family", "play with the family",
            "play a game", "play some games", "what can we play", "what should i play",
            "what shall we play", "what can i play"),
           # "whats a good icebreaker" carries no ask word from ASKED and no game word, so it
           # reached a shrug: a good one is what someone wants named
           ASKED + ("good", "best", "whats", "what's", "what is",
                    "play", "play a", "play some", "game", "games", "bored", "boring", "journey",
                    "car", "kids", "children", "group", "family", "rainy", "flight",
                    # "would you rather questions" and "twenty questions" name no game word
                    "question", "questions", "ask me", "ask us", "suggest", "ideas")),
          _the_game_the_line_names,
          # "indoor games for a rainy day" names a game, so the row must answer it: "rainy" and
          # "rainy day" stood the row down on the one line it is best at, and the long-afternoon
          # card answered with "a rainy Sunday is a good excuse to cook something". A line about
          # the weather alone names no game word, so the key keeps it out anyway.
          avoid=HOW_TO + ("bored", "boring", "nothing to do",
                          "climbing the walls", "stuck inside", "stuck indoors", "den",
                          "board game", "board games", "video game", "video games", "xbox",
                          "playstation", "nintendo", "switch", "console", "minecraft", "fortnite",
                          "game of thrones", "hunger games", "hunger", "the game", "football", "match", "ticket", "tickets",
                          # "good two player game for me and my partner" is one game for two
                          # people, not a party game: the two-player row names the boxes.
                          "two player", "two-player", "2 player", "2-player", "for two",
                          "the two of us", "just us", "partner", "couple",
                          # "what games can two people play" reached this row on "games" and
                          # "play", and a party game for a room of people is not a table of two
                          "two people", "2 people", "two of you", "the pair of you",
                          "scam", "gamble", "gambling", "bet", "betting", "rigged",
                          # "what should i play" is also a record, a sport or an instrument
                          "music", "guitar", "piano", "song", "songs", "album", "playlist",
                          "record", "vinyl", "tennis", "golf", "cricket", "darts", "poker",
                          "chess", "violin", "drums",
                          # a game for yourself on a quiet evening is not a party game: "a game to
                          # play when im stressed" and "a short game to play tonight" were
                          # handed "Would you rather" and "Twenty questions", which need other
                          # people in the room. The mood or the length in the line is the ask for
                          # one game you play alone, and the video-game row answers it.
                          "stressed", "anxious", "calm", "relax", "relaxing", "chill",
                          "wind down", "short", "quick", "solo", "alone", "by myself",
                          "on my own", "single player", "weeknight")),
    # A blank page is the hard part of drawing with children and of writing, so both asks get the
    # prompt itself plus the one rule that makes it work.
    entry("drawing-prompt",
          (("draw", "draws", "drawing", "doodle", "doodling", "sketch", "sketching", "pencil",
            "crayons", "colouring", "coloring", "something to draw", "what to draw"),
           ASKED + ("prompt", "prompts", "idea", "ideas", "suggest", "kids", "children",
                    "toddler", "bored", "rainy", "easy", "simple", "quick", "fun",
                    "what should i", "what can i",
                    # "something to draw" is the whole ask: there is no second word in it, and
                    # one of these is what the line already says
                    "something to draw", "to draw", "draw", "drawing", "doodle")),
          _pool(DRAWING_PROMPTS),
          avoid=HOW_TO + ("bath", "bathroom", "curtain", "curtains", "blind", "blinds",
                          "window", "money", "pension", "interest", "benefit", "salary",
                          "diagram", "plan", "will", "contract", "sign", "signature",
                          # "colouring" folds to "colour", so "i need to pick a paint colour
                          # for the hall" was answered with a drawing prompt: the colour of a
                          # wall is the paint question
                          "paint colour", "paint color", "pick a colour", "pick a color",
                          "colour scheme", "color scheme", "wall", "walls", "emulsion",
                          "gloss", "woodwork", "hall", "hallway", "front room", "bedroom",
                          "living room")),
    entry("writing-prompt",
          (("writing prompt", "writing prompts", "story prompt", "story prompts",
            "creative writing", "a prompt", "prompts", "something to write",
            "something to write about", "what should i write", "what can i write",
            "story idea", "story ideas", "writing idea", "writing ideas"),
           ASKED + ("write", "writing", "prompt", "prompts", "story", "stories", "blog",
                    "idea", "ideas", "suggest", "class", "group", "workshop", "practice")),
          _pool(WRITING_PROMPTS),
          avoid=HOW_TO + ("essay", "essays", "assignment", "homework", "coursework", "thesis",
                          "dissertation", "cv", "resume", "cover letter", "letter", "email",
                          "complaint", "card", "birthday", "wedding", "speech", "will",
                          "mortgage", "landlord", "school", "university", "application",
                          "personal statement", "diary", "journal")),
]
