"""Writing craft: why a draft feels flat, and how to get a story moving.

The verse requests are already answered (`bot/knowledge/entertainment.py` has the poem, limerick,
haiku and rhyme tables), so nothing here writes anything for you. What was still a shrug is the
craft question underneath: "how do i make my writing less boring" came back as "I'd rather not
guess", and "how do i start a story" got a sample story rather than the thing that makes one run.

Two entries only, both about the writing rather than the subject, and both pass (return None) on
anything that names a subject to write about, so entertainment.py keeps every verse request.
"""

import re

from .lookup import entry

ANSWERS = ("creative", "language-and-writing")


def _story(memory, understood):
    """A story that holds up: the engine, and what makes a detail believable."""
    return ("Build it from a want, a wall and a turn: what the character wants in the first "
            "scene, what stops them, and the one thing that changes the plan. A plot that sounds "
            "far-fetched is usually missing the practical steps - the key, the alibi, the person "
            "who noticed - so make the method vague and the aftermath exact: the cup half drunk, "
            "the dog still alive, the wrong person blamed. If you want a villain's plan to be "
            "believable, give them one small mistake a careful reader could spot on a second "
            "read, and let a minor character be the one who spots it.")


def _prose(memory, understood):
    """How to make flat writing less flat, in the order that changes the most per minute."""
    return ("Cut the adverbs and put one thing a reader can see in every paragraph: not 'the "
            "kitchen was messy' but 'the bin was full of cereal boxes'. Then vary the sentence "
            "length - short where it is tense, longer where it is calm - and read it aloud, "
            "because the sentence you stumble on is the one to fix. That is three passes, and "
            "they fix most flat writing.")


def _naming(memory, understood):
    """A name for a shop, a band, a stall: the method, with the examples that show it."""
    return ("Name the thing, not the idea: a bakery called Crust, a cafe called The Second Cup, "
            "a band called The Rosy Hours. Two short words joined - place plus trade, your own "
            "name plus what you sell - beats anything clever, because people have to say it out "
            "loud and spell it down a phone. Say it with 'I'm just going to' in front of it, check "
            "that the domain and the social handle are free before you fall in love with it, and "
            "check Companies House for the limited company: a name can be yours to trade under "
            "and still be taken as a company.")


# A child's costume is clothes they already own with one big shape on top, and the shapes are the
# same handful every autumn: a pirate, a superhero, an angel for the nativity, a character for
# World Book Day. On main `f2e7b389` those lines reached nothing - "how do i make a world book day
# costume from what we have at home" was the stain card, "easy nativity costume for my son" was
# "Noted: ...", and "what can i make a pirate costume out of" was an honest shrug - because no row
# anywhere names the costume. So the method is one answer and each character is a line of data in
# `_COSTUME_TIPS`, which is the shape of the thing: one row, a table, not a card per character.
_THE_METHOD = (
    "Ordinary clothes plus one big shape, and nothing to sew: a black hoodie with ears on a "
    "headband is a cat, a cardboard box is a robot, a dressing gown and a towel round the head is "
    "a shepherd. Hats, ears and face paint do more than the outfit, and one prop - a cardboard "
    "sword, a wooden spoon, a stack of books - tells everyone who it is meant to be.")

# The character the line names, and the one thing that makes that costume read. The words are
# matched from the left, so the more particular costume sits above the general one.
_COSTUME_TIPS = (
    (("world book day", "book day", "book character", "book week", "world book"),
     "For World Book Day pick a character who wears normal clothes - Matilda with a stack of "
     "books, the Worst Witch in school uniform, the Tiger Who Came to Tea with whiskers of face "
     "paint - because the book under the arm does the rest of the work."),
    (("nativity", "shepherd", "shepherds", "wise man", "angel", "angels"),
     "A shepherd is a dressing gown, a towel round the head and a tea towel for a belt; an angel "
     "is white clothes, wings bent out of wire coat hangers and tights, and tinsel on a headband "
     "for a halo."),
    (("pirate", "pirates"),
     "Pirate: a striped top, a scarf knotted as a bandana, an eye patch cut from card, and a sword "
     "of rolled card or a wooden spoon."),
    (("superhero", "superheroes", "super hero", "cape", "batman", "spiderman", "spider man"),
     "Superhero: a plain t-shirt with a paper logo taped on, leggings, and a cape cut from an old "
     "sheet pinned at the shoulders - pinned, never tied round the neck."),
    (("witch", "witches", "wizard", "harry potter"),
     "Witch: black clothes, a cone of card for a hat, and a broom of a stick and a bundle of straw."),
    (("dinosaur", "dinosaurs", "dragon", "dragons"),
     "Dinosaur: a hoodie with triangles of paper or felt down the back of the hood, and a tail "
     "pinned to the trousers."),
    (("robot", "robots", "astronaut", "spaceman"),
     "Robot: a box over the head with eye holes cut out, foil taped on the arms and legs, and "
     "bottle tops glued on for buttons."),
    (("cat", "cats", "dog", "dogs", "mouse", "bunny", "rabbit", "animal", "animals"),
     "Cat or dog: black or brown clothes, ears cut from card on a headband, and whiskers in face "
     "paint."),
    (("princess", "princesses", "fairy", "fairies"),
     "Princess or fairy: a long dress or a sheet, a crown of card and foil, and a sash of ribbon."),
    (("cowboy", "cowgirl", "indian", "sheriff"),
     "Cowboy: jeans, a checked shirt, a scarf at the neck, and a hat of card with a brim."),
    (("skeleton", "ghost", "zombie"),
     "Skeleton: black clothes with bones painted on in white face paint, or cut from paper and "
     "pinned on."),
)


# Which of the table's characters the line names, if any.
def _costume_word(line):
    """The tip for the character the line names, or "" when it names none of them."""
    for words, tip in _COSTUME_TIPS:
        for word in words:
            if re.search(r"\b" + re.escape(word) + r"\b", line):
                return tip
    return ""


# The words that say the line is about making or wearing the thing, not about the day it is worn
# on: "what can we do with the kids at halloween" names halloween and asks for something to do, so
# it is not this row's line even though no `avoid` word in it could say so.
_COSTUME_MAKING = re.compile(
    r"\b(?:costumes?|fancy dress|dress(?:ed)? (?:up|as)|dressing up|outfits?|"
    r"make|makes|making|made|diy|sew|sewing|sewn|put together|throw together|improvise|"
    r"knock up|out of|ideas?|go(?:es|ing)? as|want(?:s)? to be|be a|wear|wearing|need|needs|"
    r"provide|ourselves|myself|cheap|cheaply|easy|last minute|no sewing)\b", re.I)


def _making_a_costume(understood):
    """Whether the line asks for a costume to be made or worn, not for what to do that day."""
    line = (understood or {}).get("clean") or (understood or {}).get("text") or ""
    return bool(_COSTUME_MAKING.search(str(line)))


def _a_costume(memory, understood):
    """How to make a costume at home: the method, then the character if the line names one."""
    line = str(understood.get("clean") or understood.get("text") or "").lower()
    tip = _costume_word(line)
    if tip:
        return _THE_METHOD + " " + tip
    return _THE_METHOD


ENTRIES = [
    entry("story-craft",
          (("story", "stories", "plot", "novel", "script", "screenplay", "character", "fiction",
            "villain", "chapter"),
           ("stuck", "idea", "ideas", "start", "where do i start", "believable", "realistic",
            "convincing", "plot", "plan", "help me", "help", "how do i write", "what should",
            "make it work", "going nowhere")),
          _story, bias=1,
          # A request for a story, or for a book to read, is not a question about how stories
          # work: entertainment.py writes the sample and the recommendation entries pick the book.
          # The verb in an avoid list is matched loosely, so "write a story" also turned away
          # "im writing a story where the villain poisons the king" - the very line this entry
          # is for. Only the request shapes are listed.
          avoid=("write me a story", "write us a story", "tell me a story", "make up a story",
                 "read next", "recommend", "suggest", "should i read", "to read", "book for",
                 "gift", "present", "book club", "audio book", "audiobook")),
    entry("make-writing-better",
          # "how do i make my essay more interesting" is answered by the essay-plan entry, and
          # that plan-first answer is the better one for it, so "essay" stays out of this key.
          (("writing", "prose", "description", "paragraph", "paragraphs", "draft", "blog post"),
           ("boring", "flat", "dull", "better", "improve", "punchier", "livelier", "read better",
            "less boring", "more interesting", "tighten", "bland")),
          _prose, bias=1,
          # "how do i make my writing smaller" is a handwriting question, and a spelling or
          # grammar question is language.py's.
          avoid=("handwriting", "smaller", "neater", "pen", "spelling", "grammar", "font",
                 "size")),

    entry("name-a-business",
          # "suggest a name for a small bakery" and "name ideas for a band" were honest passes.
          # The thing named sits in the second arm so the first can stay about naming.
          (("name", "names", "naming", "call it", "called", "what to call"),
           # a band, a group, a duo is `band-name` in entertainment.py, which already answers it;
           # this row is the shop on the corner
           ("business", "shop", "bakery", "cafe", "caf", "restaurant", "company", "brand",
            "team", "podcast", "blog", "stall", "startup", "start up", "etsy", "pub",
            "salon", "studio", "brand name", "small business", "side hustle", "market stall",
            "youtube channel", "newsletter")),
          _naming, bias=1,
          # asking for the name of a shop they already have, or a name for a pet or a baby, is
          # another module's question
          avoid=("puppy", "kitten", "dog", "cat", "hamster", "rabbit", "guinea", "parrot",
                 "budgie", "horse", "pony", "tortoise", "baby", "baby name", "baby names",
                 "what is it called", "whats it called", "what is the name of", "called again"),
          ask=("suggest", "suggestion", "suggestions", "ideas", "idea", "any", "good",
               "help me", "come up with", "think of", "what should i", "what could i",
               "what would you", "how do i name", "name for", "name ideas", "pick a name",
               "choose a name", "shortlist")),

    entry("a-costume-at-home",
          # The thing in the line is a costume, a dressing-up day or the character itself, and the
          # asking is what is made of it. Both are needed, so a line about a costume being cleaned,
          # hired or bought is not this row.
          (("costume", "costumes", "fancy dress", "outfit", "dressing up", "dress up box",
            "world book day", "book day", "book character", "book week", "nativity",
            "school play", "halloween", "party costume",
            "pirate", "pirates", "superhero", "superheroes", "cape", "angel", "shepherd",
            "witch", "wizard", "dinosaur", "robot", "princess", "cowboy", "skeleton"),
           ("make", "makes", "making", "made", "diy", "sew", "sewing", "put together",
            "throw together", "improvise", "knock up", "out of", "from what we have",
            "from what i have", "what can i", "what should", "what do i", "how do i",
            "how can i", "go as", "goes as", "going as", "dress as", "dressed as", "ideas", "idea",
            "want to be", "wants to be", "be a", "provide", "ourselves", "myself", "need",
            "easy", "cheap", "last minute", "no sewing")),
          _a_costume, bias=1, guard=_making_a_costume,
          # Washing it, hiring it, buying it and eating at the party it is worn to are somebody
          # else's question: the swimming costume is the chlorine rinse in odours.py, and "party
          # food" is the party.
          avoid=("swimming", "swimsuit", "swimwear", "bikini", "trunks", "wetsuit",
                 "pool", "chlorine", "wash", "washing", "clean", "stain", "stains", "smell",
                 "smells", "smelly", "iron", "ironing", "mend", "repair", "alter", "tailor",
                 "hire", "hiring", "rent", "rental", "buy", "buying", "shop", "online",
                 "amazon", "where can i get", "where to buy", "sale", "price", "cost",
                 "cake", "cakes", "cupcake", "bake", "baking", "sandwich", "party food",
                 "trick or treat", "sweets", "balloons", "bunting", "decorations",
                 "present", "gift", "what to wear to", "activities", "things to do", "party games",
                 "trick or treating", "carve", "pumpkin")),
]
