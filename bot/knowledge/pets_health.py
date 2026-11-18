"""A cat or a dog with kidney disease, which is the commonest long illness an old pet has.

`tools/candidates.py` found this one in the deck: `my cat has kidney disease` was answered with
"You're worried about your cat... is it eating and drinking as usual", and every question after
it went somewhere else - "how long has he got" got the *lifespan* card ("an indoor cat lives
about 12 to 15 years"), "what should i feed him" got the ordinary portion card ("3 or 4 pouches
of 85g"), "how often should he see the vet" got the yearly-booster card, and "what is chronic
kidney disease in cats" got the search hedge. Chronic kidney disease is not a small thing to
guess at: it is the diagnosis behind a large share of the last years of a cat's life, and the
few things that actually help (a renal diet, water, blood pressure, the bloods every few months,
and taking a cat that stops eating to the vet the same day) are all cheap to say.

The rows live here rather than in `pets.py` because that file is at the size limit and waiting to
be split; nothing about them is specific to this file.

What these rows do not take: a person's own kidneys (that is `body.py`), a dog or a rabbit
asking about cats (each has its own row here, and the cat row stands down on the other animals),
and a line about what a pet should eat in general, which the feeding rows answer.
"""
from .lookup import entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("pets",)

# The names of the illness, as an owner says them: the vet's words and the plain ones.
_KIDNEY = ("chronic kidney disease", "kidney disease", "kidney failure", "renal failure",
           "renal disease", "kidney problem", "kidney trouble", "ckd", "kidneys are failing",
           "kidneys failing", "kidney damage", "renal")

# What an owner asks about it, and the words that make a bare mention a question.
_ASKING = ("what is", "whats", "what's", "what does", "mean", "means", "how long", "how often",
           "feed", "food", "diet", "eat", "eating", "appetite", "water", "drink", "drinking",
           "thirsty", "stage", "stages", "treat", "treated", "treatment", "medicine",
           "symptoms", "signs", "vet", "manage", "managing", "slow", "slowing", "worse",
           "quality of life", "put to sleep", "painful", "in pain", "cope", "help", "do",
           "should i", "can i", "is it", "how do i", "what can i", "supplements", "phosphate",
           "blood pressure", "bloods", "test", "tests", "diagnosed", "what now", "next")

_CAT = ("cat", "cats", "kitten", "kittens", "kitty", "puss", "moggy", "tabby", "tomcat",
        "siamese", "bengal", "ragdoll", "persian")
_DOG = ("dog", "dogs", "puppy", "pup", "pups", "bitch", "collie", "labrador", "terrier",
        "spaniel", "retriever", "jack russell", "poodle", "beagle", "greyhound", "staffie",
        "cocker", "cavapoo", "cockapoo")

# A person's own kidneys have their own cards, and so does every other animal.
_NOT_A_PET = ("my dad", "my mum", "my mother", "my father", "my husband", "my wife", "my nan",
              "my grandad", "my grandma", "my brother", "my sister", "my son", "my daughter",
              "i have", "i've got", "ive got", "myself", "my own kidneys", "human", "dialysis",
              # a baby with kidney problems is a paediatric question, and the row answered
              # "my baby has kidney problems" with the cat's card before these were here
              "transplant", "nephrotic", "egfr", "creatinine", "my baby", "baby", "babies",
              "toddler", "child", "children", "my son", "my daughter", "neonate", "newborn")

_NOT_THE_OTHER_ANIMAL = ("rabbit", "hamster", "guinea pig", "ferret", "parrot", "fish", "horse",
                         "tortoise", "lizard", "snake", "rat", "mouse", "chinchilla")


ENTRIES = [
entry("cat-kidney-disease",
      (_KIDNEY,
       _CAT + _ASKING),
      ("Chronic kidney disease is the kidneys slowly losing their filtering over months to years: "
       "it is the commonest long illness of an older cat, it is found on bloods rather than by "
       "looking, and most cats found early live for years with it. A prescription renal diet - "
       "wet food lower in phosphate and protein - is the one thing shown to slow it, and any wet "
       "food she will eat beats dry. Have the vet check her blood pressure and her urine protein "
       "as well as the bloods, since high blood pressure is treatable and causes the sudden "
       "blindness. Bloods and urine every three to six months, and her weight once a month at "
       "home. Ring the vet this week if she stops eating, loses weight, drinks and wees far more, "
       "vomits or starts hiding away, and the same day if she has not eaten for a whole day or her "
       "breath smells of ammonia - not eating is what makes them worse fastest."),
      avoid=_NOT_A_PET + _DOG + _NOT_THE_OTHER_ANIMAL,
      report=True, explain=True, bias=1),

entry("dog-kidney-disease",
      (_KIDNEY,
       _DOG + _ASKING),
      ("Chronic kidney disease in a dog is the kidneys losing their filtering slowly, usually "
       "found on a blood test in an older dog, and it is managed rather than cured - many dogs "
       "live comfortably for a year or two, some much longer. A prescription renal diet is the "
       "main thing: lower phosphate and moderate protein, and it works best started early, so ask "
       "the vet whether to switch now. Have the blood pressure and the urine protein checked too, "
       "because both are treatable and both make it worse; phosphate binders, a potassium "
       "supplement and something for sickness are added if needed. Bloods every three to six "
       "months, and the weight at home. Ring the vet this week if your dog stops eating, loses "
       "weight, is sick, drinks far more or seems dull, and the same day if it has not eaten for a "
       "whole day."),
      avoid=_NOT_A_PET + _CAT + _NOT_THE_OTHER_ANIMAL,
      report=True, explain=True, bias=1)
]
