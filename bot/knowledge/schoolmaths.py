"""School maths: the method, when the question has no numbers in it.

"How do i solve for x", "what is pythagoras theorem", "how do i use a protractor" name a method
and give nothing to work out, so the arithmetic answers in maths.py have nothing to do and these
used to be shrugs. Two of them had another subject's answer: a square root came back as a plant's
roots, and the angles of a triangle came back as whatever row held "work out".

One row per method, keyed by what the person is asking about - the method's own name - with a
second group for the wording of the request, so "explain pythagoras", "how does pythagoras work"
and "what is the pythagoras theorem" are the same question. A sum with numbers in it is handled by
maths.py before this file is reached, which is why the square root of 144 is worked out rather
than explained.
"""
import re

from bot.knowledge.lookup import entry

ANSWERS = ("maths-and-numbers",)

# "brackets" is the punctuation mark more often than it is the algebra, and the mark's own
# questions ("when do i use brackets", "what are brackets for", "when should i use brackets")
# were reaching this row and getting the multiplication back. The maths reading is the one with a
# maths word or a figure in it, so the row answers only when one is there: "expand the brackets",
# "multiply out (x+2)(x+3)", "how do i simplify brackets", "do brackets mean multiply".
_BRACKET_MATHS = re.compile(
    r"\b(?:expand|expanding|expanded|simplify|simplifying|simplified|multiply|multiplying"
    r"|factorise|factorize|factorising|solving|solve|equation|equations|algebra|algebraic"
    r"|power|powers|term|terms|coefficient|coefficients|negative|negatives|out|maths|math"
    r"|sum|sums|calculate|number|numbers|expression|expressions|double|triple|understand"
    r"|working out|work out)\b"
    r"|\d", re.X)


def _a_bracket_is_a_sum(understood):
    """True when the line about a bracket is about the sum rather than the mark."""
    said = ""
    for name in ("plain", "clean", "text"):
        said = str((understood or {}).get(name) or "")
        if said:
            break
    return bool(_BRACKET_MATHS.search(said.lower()))


ENTRIES = [
    # --- the method, when no numbers are given -------------------------------
    # Every question below came back as a shrug or, worse, as another subject's answer: "how do i
    # find the square root of a number" got plant roots, "how do i work out angles in a triangle"
    # got the negative-numbers line. Each one is the same school method asked without a sum in it,
    # so the second group is the wording of a request rather than a number.
    entry("solve-for-x",
          (("solve for x", "solve x", "solve the equation", "solve this equation", "solve an equation",
            "algebra", "equations", "equation", "rearrange the formula", "rearrange a formula"),
           ("how", "solve", "what", "steps", "method", "start", "help", "stuck", "works",
            "explain", "beginner", "learn")),
          "Do the same thing to both sides until x is on its own: in 3x + 4 = 19 take 4 off both "
          "sides to get 3x = 15, then divide both by 3 for x = 5. Undo the adding and subtracting "
          "first and the multiplying or dividing second, then put the answer back in to check it.",
          avoid=("simultaneous", "quadratic", "percentage", "split", "share", "sharing",
                 "fair share")),
    entry("expand-brackets",
# The bracket is the subject and "expand" is only the request word: on its own
          # "expand" is a vocabulary, a business, a lung and a wardrobe far more often than it
          # is a bracket, and a word list of what it is not cannot catch them all.
          (("brackets", "bracket", "multiply out", "multiplying out", "double brackets",
            "expand and simplify"),
           ("expand", "expanding", "expanded", "how", "algebra", "method", "out", "do",
            "work out", "steps", "explain", "brackets", "bracket", "simplify")),
          "Multiply everything inside the bracket by what is outside it: 3(x + 4) is 3x + 12. "
          "With two brackets, (x + 2)(x + 3), multiply every pair, then add the like terms: "
          "x squared + 3x + 2x + 6, which is x squared + 5x + 6.",
          # "expand" is a business word too: "how do i expand my small business" is not a
          # bracket, and neither is a family that is growing.
          avoid=("shelf", "shelves", "wall", "drill", "picture", "tv", "teeth", "orthodontic",
                 "braces", "seating", "rows", "cupboard", "screws", "fixing", "business",
                 "businesses", "company", "shop", "cafe", "restaurant", "team", "staff",
                 "family", "branch", "premises", "grow", "growing", "staffing",
                 "photo", "photos", "image", "images", "canvas", "font", "print", "screen"),
          guard=_a_bracket_is_a_sum),
    entry("long-multiply",
          (("long multiplication", "long multiply", "multiply two digit", "two digit numbers",
            "multiplying by hand", "big numbers by hand"),
           ("how", "method", "do", "work out", "steps", "explain", "by hand",
            "without a calculator")),
          "Write one number above the other and take the digits of the bottom number one at a "
          "time: 34 x 26 is 34 x 6 = 204, then 34 x 20 = 680, and 204 + 680 = 884. Each row moves "
          "one place to the left, which is the nought on the end, so keep the columns lined up.",
          avoid=("times tables", "times table")),
    entry("pythagoras",
          (("pythagoras", "pythagorean", "hypotenuse", "pythagoras theorem", "pythagoras' theorem"),
           ("what", "theorem", "how", "explain", "use", "work out", "find", "side", "mean",
            "rule", "triangle")),
          "In a right-angled triangle the two shorter sides squared add up to the longest side "
          "squared: a squared + b squared = c squared. Sides of 3 and 4 give 9 + 16 = 25, so the "
          "longest side is 5; to find a shorter side, take one square away from the other instead."),
    entry("protractor",
          (("protractor", "measure an angle", "measure angles", "measuring angles",
            "read an angle"),
           ("how", "use", "read", "measure", "angle", "angles", "correctly", "zero", "which")),
          "Put the hole of the protractor on the point of the angle and line the 0 line up with "
          "one arm, then read the number the other arm crosses - use the scale that starts at 0 on "
          "that side, so the two rows of numbers do not fool you. Under 90 is acute, over 90 is "
          "obtuse, and exactly 90 is a right angle."),
    entry("square-root-how",
          (("square root", "square roots", "cube root", "root of a number", "root of 144"),
           ("how", "work out", "find", "calculate", "what is", "method", "mean",
            "without a calculator", "number", "big number")),
          "A square root is the number that times itself makes yours: the square root of 49 is 7 "
          "because 7 x 7 = 49. Learn the squares up to 12 x 12 and you can place anything between "
          "them by eye, and the root button gives the exact answer - so the square root of 50 is a "
          "little over 7.",
          # a plant's roots take up water: this is the number, not the garden
          avoid=("plant", "plants", "tree", "trees", "garden", "flower", "flowers", "cutting",
                 "cuttings", "water", "soil", "pot", "potted", "root bound", "rootbound",
                 "carrot", "parsnip", "beetroot", "hair", "ginger", "propagate")),
    entry("decimal-to-percent",
          (("decimal to percentage", "decimal to percent", "decimal as a percentage",
            "decimal as a percent", "turn a decimal", "convert a decimal", "into a percentage",
            "to a percentage", "as a percentage"),
           ("how", "percentage", "percent", "convert", "turn", "change", "do")),
          "Multiply the decimal by 100 and put a % sign on it: 0.35 is 35% and 0.07 is 7%. Going "
          "the other way, divide by 100 - so 62% is 0.62 - which is just the decimal point moving "
          "two places."),
    # Counting up is the method behind the till, and it had no row: "how do i count back change"
    # and "how much change should i get from 20" were shrugs, "how do i give change" was a hedge,
    # and "how do i work out change from a note" was answered "three half-hour sessions a week".
    # The sums are the same few every time, so the answer is the method with one worked example.
    entry("counting-up-change",
          (("change from", "change from a note", "change from a tenner", "change from a fiver",
            "count back change", "count up change", "count out change", "work out change",
            "work out the change", "give change", "giving change", "the change from",
            "change in a shop", "wrong change", "how much change", "much change",
            "change should i get", "change do i get", "change would i get", "my change"),
           ("how", "work out", "calculate", "much", "count", "do", "note", "till", "shop",
            "give", "back", "work", "right", "correct", "should", "get")),
          "Count up from the price to the note rather than subtracting: on £12.40 out of a £20, "
          "add 60p to reach £13, then £7 to reach £20 - so the change is £7.60. Counting up stops "
          "at the round numbers on the way, which is why it is easier to do in your head and "
          "easier to check: what you counted back plus the price should land on the note.",
          # "change" is a career, a nappy, a lock and a tyre more often than it is the money back,
          # so each of those readings is named here. An inflected form of the row's own subject
          # must NOT go in this list: "changing" carries the form "change", and on its own it
          # vetoed every line this row exists to answer.
          avoid=("career", "job", "jobs", "climate", "address", "nappy", "nappies", "baby",
                 "oil", "filter", "tyre", "tyres", "tire", "tires", "battery", "bulb",
                 "change my", "change the", "change of", "life", "mind", "opinion", "subject",
                 "school", "schools", "passport", "name", "energy", "provider", "supplier",
                 "bank", "account", "password", "lock", "train", "bus", "tube", "hair",
                 "sheets", "bed", "diet", "lose", "weight", "doctor", "dressing", "bandage",
                 "nurse", "shift", "rota", "clothes"),
          bias=1),
    # The other sum people do in their head at a table. The etiquette rows answer "should i tip"
    # and the sum on a named bill; this is the method when no bill is named, and it reached no
    # row at all: "how do i work out the tip" and "how do i work out a tip for a meal" got the
    # shrug. The key is the phrase, not the bare "work out", because "any tips for working out"
    # is exercise advice and the bare word would take it.
    entry("tip-arithmetic",
          (("tip", "tips", "tipping", "gratuity"),
           ("work out the tip", "work out a tip", "work out my tip", "work out tips",
            "work out the service", "work out a service", "calculate the tip", "calculate a tip",
            "calculated the tip", "calculating the tip", "figure out the tip", "figure out a tip",
            "how to work out the tip", "how do you work out a tip", "do the tip in my head",
            "tip in my head", "work out how much to tip", "work out what to tip")),
          "Ten percent is the easy part: move the decimal point one place, so a £46 bill is "
          "£4.60, and half of that again is five percent, so twelve and a half is £5.75. Check "
          "the bill for a service charge first, because that is the tip and you add nothing on "
          "top.",
          # The other "tip" is the place the rubbish goes, the end of a thing, and the advice
          # somebody wants rather than a sum: each has its own card and keeps its line.
          # "the tip" cannot be a bare avoid phrase: the row's own question has it in it
          # ("how do i work out the tip"), and it vetoed those lines. The place the rubbish goes
          # is named by the words around it instead.
          avoid=("to the tip", "at the tip", "the tip is", "the tip was", "the tip closes",
                 "tip run", "fly tip", "fly-tip", "rubbish tip", "recycling",
                 "tip of", "tips of", "white tips", "french tips", "fingertips", "finger tips",
                 "split ends", "nails", "nail", "hair", "hairdresser", "barber", "tip jar"),
          bias=1),
    entry("percentage-change",
          (("percentage increase", "percentage decrease", "percentage change", "percent increase",
            "percent decrease", "percentage difference", "percentage rise", "percentage drop"),
           ("how", "calculate", "work out", "formula", "find", "between", "old", "new", "do")),
          "Take the difference, divide it by the number you started with, then multiply by 100: "
          "40 to 50 is 10 more, 10 out of 40 is 0.25, so a 25% rise. To add a percentage on, "
          "multiply by 1 plus the rate - 80 plus 20% is 80 x 1.2 = 96 - and to take one off, "
          "multiply by 1 minus the rate.",
          bias=1),
    # "I can't do maths" is a request for a start, not a shrug. The rows above answer a method
    # when the line names one; this one answers the person who names none and says the whole
    # subject is beyond them. Every one of these lines used to get a nod or "I'm listening".
    # The key is the admission, never a sum: "what is 20% of 45" and "what is 2/3 of 12" name a
    # figure and are worked out before this row is reached, so the avoid list also fences the
    # words a real sum uses.
    entry("maths-from-scratch",
          (("cant do maths", "can't do maths", "cannot do maths", "can not do maths",
            "no good at maths", "bad at maths", "rubbish at maths", "hopeless at maths",
            "maths is not my thing", "maths isnt my thing", "maths is not my strong point",
            "struggle with maths", "struggled with maths", "maths is hard for me",
            "cant do sums", "cant do arithmetic", "cant do fractions", "cannot do fractions",
            "dont understand fractions", "dont get fractions", "never understood fractions",
            "cant do my times tables", "never learned my times tables",
            "never got maths", "failed maths", "hate maths", "afraid of numbers",
            "numbers scare me", "numbers confuse me"),
           ("cant", "can't", "cannot", "never", "no good", "bad", "rubbish", "hopeless",
            "dont", "don't", "struggle", "struggled", "hard", "hate", "failed", "confuse",
            "scare", "afraid", "start", "beginner", "at all", "help", "how", "learn",
            "not", "isnt", "strong point", "my thing")),
          "Numbers are rules you can look up, not a talent. A fraction is a part of a whole: the "
          "bottom is the size of the piece and the top is how many you have, so 2/3 of 12 is "
          "12 / 3 = 4, then 4 x 2 = 8. To add fractions, make the bottoms match first - 1/2 + 1/3 "
          "is 3/6 + 2/6 = 5/6 - and a percentage is per hundred, so 10% is the number with a zero "
          "knocked off, and 20% off 60 is 12 off, so 48. For times tables, learn 2, 5 and 10 "
          "first and double for the 4s and 8s.",
          avoid=("recipe", "recipes", "scale up", "double a recipe", "halve a recipe", "cup",
                 "cups", "grams", "ml", "ounces", "convert", "conversion", "unit", "units",
                 "square root", "pythagoras", "triangle", "algebra", "equation", "bracket",
                 "mean", "decimal", "percentage increase", "tax return", "spreadsheet"),
          bias=1),
]
