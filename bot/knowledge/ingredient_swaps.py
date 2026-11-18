"""What stands in for an ingredient: the sugar a recipe runs out of, and the flour.

The rest of the swap family (butter, egg, milk, yeast, self-raising) lives in
bot/knowledge/cooking.py. These two are here because they were the shapes that had no answer
at all: "i ran out of sugar" was read as a feeling and answered "Nice one - how did that feel?",
"out of sugar" got "I'm listening", and "what can i use instead of sugar" reached the
cut-down-on-sugar card in nutrition, which is a diet question and the wrong job for someone
mid-recipe with a cake in the bowl.

A shortage and a swap are the same question - "im out of sugar", "no sugar, what can i use",
"can i use granulated instead of caster sugar" - so both rows are keyed on the ingredient plus a
shortage-or-swap phrase. The diet lines keep their own answer in nutrition, and a flourless
recipe keeps its own answer, so the sugar row stands down on "cut down", "give up", "sweets" and
on comparison questions ("difference", "vs", "same as"), and the flour row stands down on
"without flour" and "flourless".
"""
from .lookup import entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("cooking", "food-and-drink")

# How a swap is asked: "what can i use instead", "can i use X instead", "what else can i use".
SWAP_ASK = ("instead", "substitute", "swap", "replace", "alternative", "what can i use",
            "what do i use", "what should i use", "what else can i use", "use in place of",
            "stand-in", "stand in")
# How a shortage is said: "im out of sugar", "ran out of flour", "no sugar left".
# "gone" alone is not a shortage ask: "my sugar has gone hard" is the hardening question, and the
# keeping row in cooking.py answers it.
# The bare words are not here: "no", "left" and "without" on their own are a way of taking
# coffee ("i take no sugar"), a quantity ("how much sugar is left in a bottle of ketchup") and a
# recipe with a limitation in it ("icing without icing sugar"). A shortage names the ingredient
# in the same breath, so the phrase carries the name.
OUT_ASK = ("out of", "ran out", "run out", "none left", "nothing left",
           "havent got", "haven't got", "dont have", "don't have",
           "no sugar", "no flour", "no honey", "no icing sugar", "no caster sugar",
           "no plain flour", "no sugar left", "no flour left", "no honey left")
ASK = SWAP_ASK + OUT_ASK

# A diet question about sugar is nutrition's: "how do i cut down on sugar", "how do i stop
# eating sweets", "i want less sugar in my diet". The sugar a recipe runs out of is not that.
NOT_A_DIET = ("cut down", "cut out", "give up", "less sugar", "reduce", "diet", "dieting",
              "calories", "sweets", "sweets and", "biscuits", "chocolate", "cravings", "crave",
              "stop eating", "healthy", "healthier", "lose weight",
              # "i cut sugar out of my tea" is about the drinking, not about a bake with none in
              # the house, and "cut out" in avoid only matches when the words are contiguous.
              "cut sugar", "cut the sugar", "cutting sugar", "add sugar", "no idea",
              # "i take no sugar in my coffee" is how someone drinks it, not a bake with none in
              "in my coffee", "in my tea", "take no sugar", "takes no sugar")
# The difference between two sugars is the comparison question's own answer, and a flourless
# recipe needs no stand-in at all.
# "can i use honey instead of sugar in a cake" already had its own answer - three-quarters of
# the weight, a spoonful less liquid, bake cooler - so neither row takes a line that names honey
# as the substitute waiting to come in.
HONEY_COMES_IN = ("use honey", "using honey", "honey instead", "honey rather")
NOT_A_SWAP = ("difference", "different", "same as", "vs", "versus", "better for you",
              # sugar or flour that has set hard is the keeping question, and cooking.py answers it
              "gone hard", "set hard", "hard as", "lumpy", "caked", "clumped", "goes hard",
              "go hard", "how do i store", "keep it soft", "storing",
              # something burnt on to the pan is a cleaning job, not a swap: "get burnt sugar
              # out of a pan" was told that caster and granulated weigh the same.
              "burnt", "burned", "burnt on", "stuck on", "stuck to", "scorched", "charred",
              "clean""out of date", "use by", "use-by", "past its date", "past the date", "best before",
              "gone past")