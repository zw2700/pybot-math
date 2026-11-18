"""How high the screen sits, asked as "should i get a laptop stand".

science.py's posture row already says what to do - screen at eye level, feet flat, elbows at
ninety degrees - but it is keyed on the complaint ("my back aches at my desk"), so the question
people actually ask when they are about to spend money, "should i get a laptop stand", scored on
"get" and "laptop" and landed on the laptop buying card with 16GB of RAM in it.
"""
from .lookup import entry

ANSWERS = ("technology", "home-and-diy", "everyday-help")

_RAISE = ("screen", "monitor", "stand", "riser", "raiser", "laptop stand", "laptop riser", "laptop raiser", "monitor stand", "monitor riser",
          "screen stand", "screen riser",
          "raise my screen", "raise the screen", "screen height", "screen is low",
          "screen too low", "screen quite low", "screen is quite low", "laptop on books",
          "laptop on a box", "screen at eye level")

# "laptop stand" on its own is the whole question - the subject is the purchase and nothing else is
# said, so the subject's own words have to count as the asking part too, the way "what about the
# slugs" counts in the pest domain.
_ASKING = ("should i", "worth", "worth it", "get", "buy", "need", "any good", "help", "good idea",
           "does it help", "is it better", "which", "stand", "riser", "raiser", "height",
           # a screen that is "quite low on the desk" is the statement of the same problem, and
           # it was a chat ack: the subject matched and there was no asking word at all
           "low", "too low", "quite low", "hurts", "hurting", "aching", "aching away")

ENTRIES = [
    entry("desk-screen-height", (_RAISE, _ASKING),
          "Yes, if your screen is below eye level: a stand or a pile of books brings the top of the "
          "screen to eye level, an external keyboard and mouse go at elbow height, and that is what "
          "stops the neck craning down all day. A laptop alone is always too low for long sessions, "
          "so the cheap version - box under the laptop, separate keyboard - does most of the job; buy "
          "the stand if you want it to look tidy or to swing up and down.",
          avoid=("battery", "charger", "crash", "won't turn on", "wont turn on", "bulging",
                 "overheating", "fan", "hard drive", "ssd", "ram", "memory upgrade", "spec",
                 "specs", "new laptop", "recommend a laptop",
                 # a standing desk has its own answer in science.py and it is not a pile of books
                 "standing desk", "standing desks", "sit stand", "sit-stand", "sit to stand",
                 "walking pad", "treadmill desk", "desk you stand at",
                 # a broken screen and a bigger screen are other questions
                 "cracked", "crack", "tv", "telly", "phone", "broken", "flickering", "flicker",
                 "bigger", "larger", "4k", "resolution", "frozen", "black screen",
                 # a second screen is another purchase and another answer
                 "second monitor", "second screen", "two screens", "two monitors",
                 "dual monitor", "dual screen", "dual monitors", "extra screen",
                 "another monitor", "another screen", "third screen"),
          bias=4),
]
