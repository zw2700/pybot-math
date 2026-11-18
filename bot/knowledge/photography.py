"""Photography: how to take a better photo with the phone that is already in your pocket.

A camera question is not a screen-time question and it is not all one question either. These are
the four shapes people send: the landscape that came out flat, the selfie, the portrait-mode blur,
and the moon. Each key is the meaning of the ask (a photo, a selfie, a mode, a small bright thing
in a dark sky), not a phrasing, so "why are my pictures hazy" and "how do i make my photos
sharper" reach the same row.

The module-level tests are in tests/test_photo_questions.py.
"""
from .lookup import entry

# Camera questions are technology in the understanding engine's topics; the phone rows that are
# about bills, storage or screen time stay in technology.py and routines.py, and the camera words
# are in those entries' avoid so they keep their own lines.
ANSWERS = ("technology",)

ENTRIES = (
    entry("photo-better", (("photo", "photos", "picture", "pictures", "camera", "photography",
                             "shots"),
                            ("better", "good", "great", "sharper", "sharp", "clear", "nicer",
                             "take", "taking", "improve", "tips", "professional", "like a pro",
                             "blurry", "blurred", "fuzzy", "smudged", "grainy", "come out",
                             # how people describe a photo that disappoints: flat, washed out,
                             # hazy, muddy - all of them are the smeared lens and the wrong focus
                             "flat", "washed out", "hazy", "muddy", "soft")),
          "Get closer and hold the phone still: brace it against a wall, a table or your chest, "
          "and tap the screen on the person or thing you are shooting so the brightness is set "
          "for that and not for the sky behind. Wipe the lens on your sleeve first, because a "
          "smeared lens is what makes phone photos look flat and hazy. Take three and keep the "
          "sharpest - it costs nothing.",
          bias=1,
          avoid=("storage", "space", "full", "icloud", "cloud", "backup", "back up", "delete",
                 "deleting", "recover", "deleted", "transfer", "print", "printing", "printer",
                 "passport", "security camera", "doorbell", "dashcam", "webcam", "lens for",
                 "which camera", "what camera", "worth", "cost", "price", "buy", "buying",
                 # the webcam and video-call blur belongs to webcam-blurry, which is keyed on
                 # exactly those words
                 "video call", "video calls", "teams", "zoom", "laptop", "call with",
                 # and the night photo keeps its own answer, which is the one with the exposure
                 # slider in it
                 "night", "nights", "at night", "dark", "in the dark", "evening", "low light",
                 "fireworks", "christmas lights", "camera is blurry", "camera blurry",
                 # A telly has a picture too. "why is my tv picture blurry" was "get closer and
                 # hold the phone still", and the set's own answer is `tv-picture` in
                 # technology.py: one channel going funny is the aerial, the box or the set.
                 # "taking a picture of my tv screen" is neither - that is `photo-screen` below.
                 "tv", "telly", "television", "tv screen", "freeview", "sky box",
                 "set top box")),
    # A screen is a thing to photograph, and it is a different job from a soft photo: the
    # flash bounces straight back, the glass mirrors the room, and the panel's flicker draws
    # bands. "taking a picture of my tv screen" was the set's fault row, then a pass.
    entry("photo-screen", (("screen", "screens", "tv", "telly", "television", "monitor"),
                           ("photo", "photos", "picture", "pictures", "photograph",
                            "photographing", "take a picture", "take a photo",
                            "taking a picture", "taking a photo", "snap", "shot of",
                            "capture")),
          "Turn the flash off and light the room from one side, because a bare flash on glass "
          "is just a white rectangle. Rest the phone on something solid, tap the screen to "
          "focus on a crisp corner, and stand a little to one side so the window behind you is "
          "not the thing in the glass. If bands crawl across the picture, that is the panel's "
          "flicker: step back and zoom instead, or film a second and keep a frame.",
          ask=("screen", "screens", "tv", "telly", "television", "monitor", "tablet"),
          # a set that has gone wrong is not a photograph, and a soft photo is not a screen
          avoid=("blurry", "blurred", "fuzzy", "signal", "aerial", "channel", "channels",
                 "no sound", "remote", "netflix", "screenshot", "webcam", "video call",
                 "white screen", "black screen", "cracked", "phone", "iphone", "android",
                 "app", "apps", "settings",
                 # a setting in the set is the set's answer, and "picture mode" is a setting
                 "reset", "mode", "picture mode", "brightness", "contrast", "tint", "colour",
                 "color", "source", "hdmi", "retune", "keeps going", "gone dark",
                 "gone funny", "went funny", "dark", "dim",
                 # a show is a listings question, not a screen to photograph
                 "show", "shows", "programme", "programmes", "episode", "listings",
                 "series")),
    # the moon is a small bright thing in a dark sky: "get closer" is worse than useless
    entry("photo-moon-stars",
          (("moon", "stars", "starry sky", "milky way"),
           # The ask is the camera, not the word "how": "how" is the interrogative of every
           # question in the language, so a key of "moon" plus "how" answered "how old is the
           # moon", "how much does the moon weigh" and "how many moons does earth have" with a
           # lesson on shutter speed. What makes a line a photo question is that it asks to
           # take, shoot, capture or photograph something.
           ("photo", "photos", "photograph", "photographs", "photographing", "photography",
            "picture", "pictures", "pic", "pics", "take", "takes", "taking", "shoot", "shoots",
            "shooting", "capture", "capturing", "snap", "snaps", "snapping", "camera", "phone",
            "how do i get", "how to get", "get a shot", "get the shot", "in a photo")),
          "A phone will not fill the frame with the moon: zoom to 10x or more, rest the phone on "
          "a wall, a fence or a tripod, turn the flash off, then press and hold on the moon until "
          "the focus locks and drag the little sun slider down until the moon is a white disc and "
          "not a glowing blob. A full moon is the worst night for detail - at half you get the "
          "craters along the shadow line. For stars, put the phone on something solid, use night "
          "mode, and give it the full few seconds it asks for.",
          bias=1,
          # every astronomy line about the moon stays with the science table: this entry is the
          # camera, and "how many moons does earth have" is not a photo question
          avoid=("phase", "phases", "moon sign", "full moon party", "moon landing", "moon in",
                 "astrology", "how many", "planet", "planets", "jupiter", "saturn",
                 "mars", "earth", "orbit", "solar system", "made of", "surface", "gravity",
                 "tide", "tides", "crater", "craters", "why does",
                 # how far away the moon is is a science fact, and this entry reads a bare
                 # "how" as a request for a photo, so it was taking "how far is the moon"
                 "far", "how far", "how far away", "distance", "away", "km", "miles",
                 # a question about the moon itself is a fact with a page of its own: the age,
                 # the size, the weight, the mass, what it is made of
                 "how old", "age", "how big", "how large", "how heavy", "how much does",
                 "how much is", "weigh", "weighs", "weight", "mass", "diameter", "size",
                 "how many", "what is", "whats", "when was", "when did", "who discovered",
                 "formed", "orbit", "distance from"),
          ),
    # a selfie is its own question: the light is on the front of the face and the phone is in
    # your hand, so "get closer and hold still" is not the advice that helps.
    entry("phone-selfie",
          (("selfie", "selfies", "photo of myself", "photos of myself", "picture of myself",
            "picture of yourself", "photos of yourself"),
           ("good", "better", "great", "nice", "take", "taking", "how", "tips", "look",
            "flattering", "blurry", "blurred", "grainy", "dark", "come out", "turn out",
            "sharp")),
          "Hold the phone at eye level and a little above, just past arm's length, and turn your "
          "face towards a window or a lamp rather than towards the screen: light on the front of "
          "the face is the whole difference. Tap your face on the screen first, so the camera sets "
          "the brightness for your skin and not for the sky behind you, and take three or four - "
          "one will have your eyes open. Wipe the lens on your sleeve before you start.",
          bias=1,
          # no night words here on purpose: a selfie in the dark still wants the light in front
          # of the face, and "photos at night" never names a selfie, so that entry keeps its line
          avoid=("storage", "space", "delete", "print", "passport", "low light"),
          ),
    # "portrait mode" reached the maths mean-median-mode entry, which is the wrong kind of mode.
    entry("portrait-mode",
          (("portrait mode", "portrait", "bokeh", "background blur", "blurry background",
            "blur the background", "depth effect"),
           ("photo", "photos", "camera", "phone", "iphone", "android", "picture", "pictures",
            "use", "turn on", "switch on", "find", "how", "take", "selfie", "where", "worth")),
          "In the camera app it is the row of modes above the shutter: swipe to Portrait and wait "
          "for the yellow box to say Depth effect before you shoot, because a photo taken too "
          "early comes out with no blur. It works best a metre or two from the person with a "
          "plain background behind them, and on most phones you can tap the f-number afterwards "
          "to change how much is blurred. For two people, keep both faces the same distance away.",
          bias=1,
          avoid=("screen", "brightness", "rotate", "rotation", "airplane", "flight mode",
                 "silent", "vibrate", "do not disturb", "data saver", "battery saver",
                 "developer", "recovery"),
          ),
)


# --- a box of old photographs ----------------------------------------------------------------
# "what should i do with old photos" was a search hedge: the rows above answer how to take one,
# back one up and get one off a phone, and nothing answered the box in the cupboard. It is not
# storage and it is not a lost file: the question is which of the prints are worth keeping and how
# to keep them, so the row is keyed on the paper words (prints, negatives, slides, album) and the
# sorting verbs, and fenced off the phone's own questions.

OLD_PHOTOS = (
    "Sort first, digitise second, and keep the paper: tip the lot onto a table and pull out the "
    "faces you cannot lose - the ones people will want in fifty years - then photograph each of "
    "those on a phone against a plain background, or use a flatbed scanner for the important "
    "ones. Store the prints in an acid-free box somewhere dry and dark rather than a hot loft, "
    "write the names and dates on the back of the keepers in pencil, and give the duplicates to "
    "the cousins who are in them. Digitising takes a phone app and an afternoon, and a box worth "
    "keeping usually shrinks by two thirds.")

# `ENTRIES` is a tuple in this module, so the new row is added by rebuilding it
ENTRIES = ENTRIES + (entry(
    "old-photos",
    # a bare "photos" is too common a word in this domain to be a signal of its own ("which photos
    # should i keep" reached nothing at all), so the paper side is named as phrases
    ((("old photos", "old photo", "old photographs", "old pictures", "old picture",
       "photo album", "photo albums", "old family photos", "old family photographs",
       "family photos", "family photographs", "photos from my parents",
       "boxes of photographs", "box of photographs", "box of family photos",
       "box of old photos",
       "photos to keep", "what photos", "which photos", "photos in a box", "photos in the loft",
       "what do i keep", "what should i keep",
       "photographs", "prints", "negatives", "slides", "box of photos"),
      ("what should i do", "what do i do", "what to do", "store", "storing", "keep",
       "keeping", "get rid", "throw", "throw away", "digitise", "digitize", "scan",
       "scanning", "sort", "organise", "organize", "preserve", "save"))),
    OLD_PHOTOS,
    ask=("photo", "photos", "photograph", "photographs", "picture", "pictures", "album",
         "slides", "negatives", "prints"),
    # a phone that has lost them, a phone that will not send them and a camera's settings are
    # other rows, and a photo frame or a canvas is somebody buying something. Scanning is here
    # too: "how do i scan old photos" already had a good answer about a phone's scanner, and
    # this row was taking it, so the how-to-scan phrasings are left to it while "should i scan
    # them" and "scan or bin them" still reach the sorting answer.
    avoid=("lost", "deleted", "delete", "recover", "icloud", "cloud", "backup", "back up",
           "transfer", "send", "share", "whatsapp", "email", "blurry", "blurred", "dark",
           "quality", "camera", "lens", "shutter", "selfie", "canvas", "frame",
           "how do i take", "better photos", "moon", "stars",
           "how do i scan", "how to scan", "how can i scan", "best way to scan",
           "scan document", "scanner",
           # "how do i organise slides for a presentation" is a talk, not a box of prints: the
           # sequencing row for a talk answered it on base, and "slides" in this row's subject
           # took the line and told a speaker to sort the paper first.
           "presentation", "presentations", "slide deck", "slides for", "powerpoint", "keynote",
           "the slides", "my slides", "talk", "speech", "pitch", "webinar", "conference"),
    bias=2),)
