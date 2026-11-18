"""Everyday lines that another card was answering: a benefit, a leave plan, a full stomach.

A line reaches the matcher as words, and the card that scores them can be about something else
entirely: "how do i apply for pip" is the benefit and not the seed, "im on annual leave next
week" is the plan and not the letter that ends a job, and "i ate too much at lunch" is the hour
after the meal and not the pot to put it in. The rows here are the ones those lines are about:
each names its own subject and the words that make the line a question about it, so a line that
only brushes past a word is left to the card that was already answering it.
"""
from .lookup import entry

# The topic ids this domain answers (bot/understanding/topics.py).
ANSWERS = ("money", "work", "health-and-fitness")

ENTRIES = [
    # "how do i apply for pip", "how long does pip take" and "can i get pip" reached a filler and
    # a hedge: the benefit's name is three letters that are also a seed, a bird and a package.
    entry("pip-claim-steps",
          (("apply for pip", "claim pip", "claiming pip", "pip claim", "pip application",
            "personal independence payment", "pip form", "pip forms", "pip assessment",
            "pip decision", "pip review", "pip waiting", "wait for pip", "how long does pip",
            "get pip", "on pip"),
           ("how", "apply", "claim", "start", "get", "can i", "should i", "am i", "long",
            "wait", "waiting", "assessment", "form", "forms", "eligible", "qualify", "evidence",
            "phone", "online", "process", "steps", "much")),
          "Ring the DWP on 0800 917 2222 and say you want to claim PIP - there is no online form - "
          "and from that call to a decision is usually two to four months. They post out a long "
          "form about how your condition affects you day to day, and you have a month to send it "
          "back with any evidence you have: letters from a GP, consultant or therapist, and a "
          "diary of a bad day. You can claim from 16 up to state pension age, and the difficulty "
          "has to have lasted or be expected to last 12 months. Most people are then asked to an "
          "assessment, by phone, video or in person. Keep a copy of everything you send, and if "
          "it is turned down ask for a mandatory reconsideration within a month.",
          bias=2,
          # the same three letters are a seed, a bird and a python package
          avoid=("apple", "apples", "orange", "oranges", "lemon", "lemons", "pear", "pears",
                 "fruit", "seed", "seeds", "raspberry", "cider", "picture", "screen", "monitor",
                 "chicken", "hen", "hens", "chick", "chicks", "incubator", "hatch", "hatching",
                 "bird", "birds", "parrot", "budgie", "install", "python", "package",
                 "pip install", "terminal", "command line")),
    # A holiday booked and a holiday owed at the end of a job are two different answers, and the
    # notice card was taking the booked one on the words "holiday" and "leave" alone.
    entry("leave-already-booked",
          (("annual leave", "on leave", "on holiday", "on holidays", "days off", "time off",
            "day off", "off work"),
           ("next week", "this week", "tomorrow", "next month", "this month", "next monday",
            "next friday", "coming week", "im on", "im off", "i am on", "i am off", "she is on",
            "he is on", "my wife", "my husband", "my partner", "back from", "going on", "booked",
            "approved", "entitlement", "how many days", "20 days", "25 days", "28 days",
            "carry over", "carried over", "use it or lose it")),
          "Take the days you have booked as booked: your employer approved them, and leave that "
          "was agreed before the notice went in is normally still yours to take, or to be paid "
          "for if the last day falls before the holiday does. Check your contract or staff "
          "handbook for how much notice they want for leave - often twice the length of the "
          "holiday - and give it in writing. A full-time job is entitled to 28 days a year "
          "including bank holidays, so if you are offered less than that, that is the thing worth "
          "asking about. Days you have not taken when you leave are paid at your normal rate.",
          bias=1,
          avoid=("notice period", "working my notice", "handed my notice", "handing in my notice",
                 "gave my notice", "given my notice", "my last day", "resign", "resigning",
                 "redundancy", "redundant", "sacked", "dismissed", "leaving the job")),
    # "i ate too much at lunch" was told how to store the leftovers.
    entry("too-much-at-one-meal",
          (("ate too much", "eaten too much", "eating too much", "too full", "so full",
            "feel full", "feel bloated", "stuffed", "food coma", "overate", "overdid it",
            "pigged out", "second helping", "went back for"),
           ("lunch", "dinner", "tea", "supper", "breakfast", "meal", "now", "tonight", "last night",
            "yesterday", "today", "weekend", "party", "takeaway", "curry", "pizza", "chinese",
            "chocolate", "sweets", "dessert", "pudding", "seconds", "again", "how do i",
            "what can i", "feel", "feeling", "better")),
          "It passes in an hour or two. Stay upright rather than lying down, sip water or "
          "peppermint tea rather than a fizzy drink, and take a slow ten-minute walk: that is "
          "what moves it along. Loosen your waistband, and skip the next snack rather than "
          "skipping the next meal, because going hungry all day usually ends in a bigger evening. "
          "A teaspoon of bicarbonate in water helps wind, and so does lying on your left side.",
          bias=2,
          # a pot of food, a shop, a drink and money are other questions
          avoid=("soup", "chilli", "stew", "curry for", "made too much", "leftover", "leftovers",
                 "freeze", "fridge", "keep", "store", "storage", "batch", "portion", "portions",
                 "spent", "spend", "budget", "money", "sugar", "drink", "drinking", "wine", "beer",
                 "bingeing", "binge", "disorder", "anorexic", "bulimic")),
]
