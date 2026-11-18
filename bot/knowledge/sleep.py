"""Sleep: the habits, the hours and the things that keep people awake.

The answers lane owns this domain. Everything here is data: one Entry per thing people ask
about (waking at 3am, a toddler up at 5, caffeine, snoring), keyed by meaning and phrased the
way a sensible friend would answer. Nothing here needs a diagnosis; a symptom that could be
serious belongs to bot/modules/safety.py."""
import re

from .lookup import entry, not_the_heat_of_an_argument

# The topics this domain answers, as ids from bot/understanding/topics.py.
ANSWERS = ("sleep",)

# A baby that will not wake, is floppy or has a temperature is a 999 call, not a sleep problem:
# those lines must fall through to bot/modules/safety.py, so every child entry avoids them.
INFANT_RED_FLAGS = ("floppy", "flopp", "limp", "unresponsive", "wont wake", "won't wake",
                    "cant wake", "can't wake", "cannot wake", "not waking", "wouldnt wake",
                    "wouldn't wake", "temperature", "fever", "rash", "breathing", "ambulance",
                    "blue", "39", "40")

# A child saying their own age is still a child: "i am 8 and i had a nightmare" was reaching the
# adult answer, which talks about alcohol and a heavy film. A parent's line is caught by the
# words the child entries already avoid; this is the first-person form, and it is generated so
# every age is covered rather than the one number somebody happened to test.
_AGE_WORDS = ("three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
              "twelve", "thirteen", "fourteen", "fifteen")
SELF_IS_A_CHILD = tuple(
    "%s %s" % (lead, age)
    for age in [str(number) for number in range(3, 16)] + list(_AGE_WORDS)
    for lead in ("am", "im", "i'm", "aged")
)
# How a person says their sleep is going without asking anything: "i sleep badly", "i dont sleep
# well", "my sleep is bad at the moment". Each of these is one phrase that says the whole thing,
# so it is keyed as a phrase in both halves of the row - the row needs a sleep word and a
# something-is-wrong word, and the phrase is both at once. Without it the line had no ask in it
# and the bot answered "I'm listening - say more if it helps" to the plainest description of
# insomnia there is.
# "slept badly" is deliberately not here: it is about one night, and that has its own answer
# ("Go easy on yourself today and aim for bed an hour earlier tonight").
SLEEPING_BADLY = ("sleep badly", "sleeps badly", "sleeping badly", "sleep terribly",
                  "sleeps terribly", "sleep is bad", "sleep has been bad", "sleep is terrible",
                  "sleep is rubbish", "sleep is awful", "sleep is not great",
                  "sleep has been terrible", "sleep has been awful", "sleep has been rubbish",
                  "sleep is still bad", "sleep is still rubbish", "sleep is still terrible",
                  "dont sleep well", "don't sleep well", "doesnt sleep well",
                  "not sleeping well", "not sleeping properly", "sleeping badly",
                  "sleep poorly", "sleeps poorly", "poor sleep", "bad sleep", "bad nights",
                  "broken sleep", "sleep is broken",
                  # How it is described when the line never says the word: "how do i stop
                  # tossing and turning" is the whole complaint, and a row that needs a sleep
                  # word in it could not reach the line at all.
                  "tossing and turning", "tossing and turning all night", "toss and turn",
                  "toss and turn all night", "tosses and turns", "cant stay asleep",
                  "can't stay asleep", "cannot stay asleep")


# A statement of a bedtime is a time, and the useful answer is arithmetic on that time rather
# than a routine: "i go to bed at 1am" is six hours by a seven o'clock start. The guard reads the
# clock (or the "late" that stands for one) and the reply says the number back.
_BED_CLOCK = re.compile(r"\b([01]?\d|2[0-3])\s*(am|pm|o'?clock)\b", re.IGNORECASE)
_BED_AT_HOUR = re.compile(r"\b(?:at|till|until|by|around|about)\s+([01]?\d|2[0-3])\b",
                          re.IGNORECASE)
_BED_WORD_HOUR = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "eleven": 11,
                  "twelve": 12, "ten": 10, "nine": 9, "eight": 8,
                  "seven": 7, "six": 6}
_HOUR_WORDS = {4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
               10: "ten", 11: "eleven", 12: "twelve"}
_WIDE_OPEN = ("all over the place", "varies", "different every night", "no set time",
              "whenever", "when i feel like it", "at different times")


def _clock_said(hour):
    if hour == 0:
        return "midnight"
    if hour == 12:
        return "noon"
    if hour > 12:
        return "%dpm" % (hour - 12)
    return "%dam" % hour


def _bedtime_said(memory, understood):
    """The bedtime arithmetic, said back with the number it gives."""
    line = _line(understood)
    hour = None
    found = _BED_CLOCK.search(line)
    if found:
        hour = int(found.group(1))
        when = found.group(2).lower()
        if when.startswith("p") and hour < 12:
            hour += 12
        elif when.startswith("a") and hour == 12:
            hour = 0
    if hour is None:
        half = re.search(r"\bhalf\s+(\d{1,2})\b", line)
        if half:
            hour = int(half.group(1))
            if hour <= 11:
                hour += 12
    if hour is None and re.search(r"\bmidnight\b", line):
        hour = 0
    if hour is None:
        found = _BED_AT_HOUR.search(line)
        if found:
            hour = int(found.group(1))
            if hour == 12:
                hour = 0
            elif 6 <= hour <= 11:
                hour += 12
    if hour is None:
        for word, number in _BED_WORD_HOUR.items():
            if re.search(r"\b%s\b" % word, line):
                hour = number
                if hour == 12:
                    hour = 0
                elif 6 <= hour <= 11:
                    hour += 12
                break
    if hour is None:
        if any(w in line for w in _WIDE_OPEN):
            return ("A bedtime that moves every night is harder to sleep on than a late one that "
                    "holds: fix the wake-up time first and keep it seven days a week, get daylight "
                    "before noon, and let the bedtime find its own level. Move it 15 minutes "
                    "earlier every few nights rather than all at once.")
        return ("Late enough that it is the hours rather than the sleep itself: pick a wake-up "
                "time you can keep seven days a week and the bedtime follows within a week or "
                "two, because the morning light is what sets the clock. No caffeine after two.")
    hours = (7 - hour) % 24
    said = _clock_said(hour)
    count = _HOUR_WORDS.get(hours, str(hours))
    if hours >= 7:
        return ("%s is a good bedtime - %s hours before a seven o'clock start - and keeping it the "
                "same seven days a week matters more than the exact hour: dark, cool room, phone "
                "outside the bedroom." % (said.capitalize(), count))
    return ("Bed at %s is %s hours if you are up at seven, and most adults need seven to nine. "
            "Don't force an early night: get up at the same time every day, daylight before noon, "
            "no caffeine after two, and the bedtime follows the wake-up time within a week or "
            "two." % (said, count))


def _the_clock_i_go_to_bed(understood):
    """True only when the line names a bedtime: a clock, or the word late for one."""
    line = _line(understood)
    if any(w in line for w in _WIDE_OPEN):
        return True
    if _BED_CLOCK.search(line) or _BED_AT_HOUR.search(line):
        return True
    if re.search(r"\b(late|later|midnight)\b", line):
        return True
    return bool(re.search(r"\b(?:one|two|three|eleven|twelve)\b", line))


def _line(understood):
    """The repaired line, lower case, with a space at each end, for a whole-word search."""
    text = understood.get("plain") or understood.get("clean") or ""
    return " " + str(text).lower() + " "


# The two halves of the caffeine timeline, in the order the person asked: a cup's half-life is
# five hours, and the headache that a stopped cup brings has a timeline of its own. One card that
# always led with the half-life told somebody asking "how long do caffeine headaches last" the
# half-life first, so the half asked about comes first here.
_CUP_GOES = ("Half a cup of coffee is gone in about five hours, so a 4pm cup is still a quarter "
             "in you at 2am, which is why early afternoon is the cutoff for sleep.")
_CUTTING_DOWN = ("Cutting down or quitting brings a headache 12 to 24 hours after the last cup, "
                 "worst on day one or two and gone in one to two weeks: take one cup off every "
                 "couple of days, not all at once, and sleep is better within a few days.")


def _caffeine_timeline(memory, understood):
    text = _line(understood)
    if re.search(r"\bheadache|headaches|withdrawal|withdrawals|shaky|irritable|"
                 r"stopped|stopping|quit|quitting|without|cut(ting)? (down|out|back)\b", text):
        return _CUTTING_DOWN
    return _CUP_GOES


# The machines a household has. A line that names one and says it is switched on is asking about
# the machine, and the fall-asleep row is keyed on "nothing happens", which is the commonest way to
# say a machine has stopped: "the washing machine light is on but nothing happens" was answered with
# a bowl of ice and a fan in front of a machine that was not going round. The machine is not the
# whole fence - "a warm shower before bed and nothing happens" is somebody saying the routine is not
# working, and that is this row's line - so the machine has to be switched on in the line too. The
# shower and the taps are left out of the list for the same reason.
MACHINES = ("washing machine", "washer dryer", "washer", "tumble dryer", "dryer", "dishwasher",
            "boiler", "fridge freezer", "fridge", "freezer", "oven", "hob", "cooker",
            "microwave", "kettle", "toaster", "hoover", "vacuum", "radiator", "air fryer",
            "immersion", "appliance", "machine")
SWITCHED_ON = ("is on", "s on", "on but", "on and nothing", "switched on", "turned on",
               "running", "started", "comes on", "switches on", "light is on", "powers on")


# The person's own sleeplessness, said plainly. A line with one of these is about them however
# many machines it names: "i cant sleep because the washing machine is on next door" wants one of
# the sleep rows and not a card about the machine.
SLEEPLESS = ("cant sleep", "can't sleep", "cannot sleep", "cant get to sleep",
             "can't get to sleep", "lie awake", "lying awake", "wide awake", "asleep",
             "insomnia", "in bed", "to bed", "bedtime")


def _a_machine_that_is_on_is_not_a_sleeper(understood):
    """False when the line names a machine in the house, says it is switched on, and is not
    somebody saying they themselves cannot sleep."""
    text = " " + str((understood or {}).get("text") or "").lower() + " "
    if any(phrase in text for phrase in SLEEPLESS):
        return True
    if not any(" " + name + " " in text or " " + name + "s " in text for name in MACHINES):
        return True
    return not any(phrase in text for phrase in SWITCHED_ON)


ENTRIES = [
    entry("night-wee", (("pee", "weeing", "toilet", "wee", "bathroom", "bladder", "loo",
                         # the whole sentence wins over "keep waking up", which is sleep-hygiene
                         "for a wee", "to wee", "need a wee", "needing a wee", "a wee in the night",
                         "wee in the night", "up for a wee", "up in the night for a wee",
                         "wake up for a wee", "waking up for a wee", "wake up to wee"),
                        ("night", "nights", "nighttime", "wake", "waking", "woken")),
          "Stop drinking anything an hour or two before bed, cut the evening cup of tea and any "
          "alcohol, and empty your bladder just before you lie down. If you are up two or more "
          "times a night most nights, or it is new, see a GP: it can be an infection, an enlarged "
          "prostate or diabetes, and it is worth checking rather than just putting up with.",
          # "up" was in the key, so "how do i stop my bathroom mirror fogging up" was a night
          # weeing question; a bathroom is not a symptom.
          avoid=("baby", "toddler", "child", "son", "daughter", "dog", "cat", "puppy",
                 "pregnant", "nappy", "nursery", "mirror", "fog", "fogging", "condensation",
                 "steam", "shower", "window", "lens", "glasses")),

    entry("snooze-alarm", (("snooze", "snoozing", "alarm"),
                           ("stop", "how", "keep", "should", "turn off", "five more",
                            "hit", "hitting", "morning")),
          "Put the alarm across the room so you have to stand up, and set it for the last minute "
          "you can actually get up: snoozing for nine minutes at a time just restarts the groggy "
          "part. Going to bed 30 minutes earlier fixes the reason you want to snooze better than "
          "any alarm app.",
          # a snooze is never a price question, and "how much do those pendant alarms cost" was
          # getting "put the alarm across the room": a pendant alarm is the falls answer in
          # lifeadmin.py, so the cost and the care words stand this entry down
          avoid=("baby", "toddler", "child", "phone", "notifications", "neighbour", "neighbor",
                 "car", "fire", "pendant", "personal alarm", "telecare", "lifeline",
                 "careline", "falls alarm", "panic alarm",
                 # a house alarm that keeps going off is home.py's `burglar-alarm-going-off`:
                 # "my burglar alarm keeps going off at 3 in the morning" was told to put the
                 # alarm across the room. The words of the house, the panel and the sound a
                 # sensor makes stand this entry down, not just the word "alarm".
                 "burglar", "burglar alarm", "intruder", "house alarm", "home alarm",
                 "security alarm", "security system", "alarm system", "alarm panel",
                 "control panel", "the panel", "keypad", "sensor", "sensors", "cctv",
                 "smoke", "smoke alarm", "smoke detector", "carbon monoxide", "beeping",
                 "chirping",
                 # the sound an alarm makes is the technology lane's `alarm-sound`; the bare
                 # "alarm" key here was taking "how do i set a different alarm sound"
                 "sound", "sounds", "song", "tune", "ringtone", "music", "louder", "quieter",
                 "volume", "silent")),

    # "what time should i go to bed" was a shrug: the sleep advice was keyed on sleep trouble
    # and routines, not on the clock time someone picks.
    entry("bedtime-said", (("go to bed", "get to bed", "go to sleep at", "bedtime", "bed time",
                            "stay up", "up till", "up until", "lights out", "turn in"),
                           ("am", "pm", "at", "midnight", "late", "later", "till", "until",
                            "oclock", "o'clock", "usually", "every night", "every day",
                            "all over the place", "varies", "whenever", "no set time")),
          _bedtime_said,
          # A statement of the time somebody goes to bed is the same question as "what time
          # should i go to bed" asked from the other side, and it had no row at all: "i go to bed
          # at 1am", "i go to bed late", "i stay up till 1" and "il go to bed at 1 usually" all
          # got "Got it. Is there anything you'd like a hand with?" or "I'm listening".
          # The rows next door already answer the shapes below, so this one stands aside for
          # them: a wake time in the line is the body-clock row's, a child's bedtime is the
          # child's, and a night shift or a sleep trouble is not a bedtime somebody chose.
          guard=_the_clock_i_go_to_bed,
          avoid=("wake", "wakes", "waking", "woke", "get up", "up at", "alarm", "snooze",
                 "baby", "babies", "toddler", "child", "children", "my son", "my daughter",
                 "newborn", "school", "shift", "night shift", "nights",
                 "cant sleep", "can't sleep", "cannot sleep", "insomnia", "cant get to sleep",
                 "tossing", "wake up", "hour", "hours", "enough", "nap", "naps", "jet lag",
                 # "i stay up late on my phone" is the phone-in-bed answer, which says where the
                 # charger goes; the hours are not what that line is about
                 "phone", "phones", "scroll", "scrolling", "screen", "screens", "tv", "telly",
                 "laptop", "ipad", "tablet", "games", "gaming",
                 "how many", "how much", "how long", "should i", "what time", "when should")),

    entry("bedtime-clock", (("what time should i go to bed", "what time to go to bed",
                             "when should i go to bed", "time to go to bed",
                             "good time to go to bed", "time should i be in bed"),
                            ("sleep", "bed", "night", "work", "morning", "up", "good")),
          "Count back about eight hours from the time you have to get up, and keep that bedtime "
          "the same seven days a week: the regularity matters more than the exact hour. If you lie "
          "there awake, go to bed half an hour later rather than earlier, so bed means sleep again.",
          avoid=("baby", "toddler", "child", "shift", "nap")),

    entry("sleep-schedule", (("sleep schedule", "body clock", "sleep routine", "sleep pattern",
                              "circadian", "back into a routine", "fix my sleep"),
                             ("fix", "reset", "how", "back", "help", "should", "get", "regular")),
          "Pick one wake-up time and keep it every day for two weeks, weekends included: the "
          "morning light is what sets the clock. Then move bedtime 15 minutes earlier every few "
          "nights, keep the room dark and cool, and take a short walk in daylight before noon. "
          "Melatonin half an hour before bed helps some people while the habit sets.",
          avoid=("baby", "toddler", "child", "shift work", "night shift")),

    # "what is a sleep cycle" was a shrug: `sleep-schedule` keys the words people use for the
    # habit ("sleep pattern", "body clock", "routine") and the cycle itself - the ninety minutes
    # the night runs in - had nothing behind it. It is a definition, so it explains itself back
    # to a plain request ("what is a sleep cycle", "explain rem sleep"), and it holds the answer
    # to "why do i wake at four" as well, because that is the same fact asked the other way.
    entry("sleep-cycle",
          (("sleep cycle", "sleep cycles", "sleep stage", "sleep stages", "stages of sleep",
            "rem sleep", "deep sleep", "light sleep", "dream sleep"),
           ("what", "why", "how long", "long", "mean", "means", "explain", "normal", "wake",
            "waking", "work")),
          "A night runs in cycles of about ninety minutes: light sleep, then deeper sleep, then a "
          "stretch of REM where you dream, and round again. The deep sleep is heaviest in the "
          "first half of the night and the dream stretches get longer towards morning, which is "
          "why a 6am wake with a dream still in your head is normal and why the last hour feels "
          "so strange to be woken out of. Waking between cycles feels much better than waking in "
          "the middle of deep sleep, so count back in ninety-minute blocks from your alarm: five "
          "is seven and a half hours of sleep, which is why 11pm to 6.30am often feels better "
          "than 11pm to 6am.",
          explain=True),

    entry("nightmares", (("nightmare", "nightmares", "bad dream", "bad dreams", "night terror"),
                         ("keep", "always", "how", "stop", "why", "every", "about", "having",
                          # "i had a nightmare last night" is the plain statement of the same
                          # thing, and it was falling through to the listening line
                          "had", "have", "got", "last night", "woke", "waking", "keeps",
                          "often", "scary", "terrifying", "vivid", "upset")),
          "Nightmares usually follow stress, late food, alcohol or a heavy film before bed, so "
          "start there. If the same one keeps coming back, write it down in the day and rehearse a "
          "different ending a few times: that is the technique that works. See a GP if they are "
          "waking you most nights or coming with flashbacks.",
          # a child's nightmare is the parent's answer, and "my 4 year old had a nightmare" was
          # reaching this one once the plain statement was keyed in
          avoid=("baby", "toddler", "child", "son", "daughter", "kid", "kids", "dog", "cat",
                 "year old", "years old", "my boy", "my girl", "grandson", "granddaughter",
                 "niece", "nephew", "pupil", "school",
                 # "my little girl had a bad dream" is a parent's line too, and the adult
                 # answer (late food, alcohol, a heavy film) is the wrong advice for a child
                 "little girl", "little boy", "little one", "little lad", "my little",
                 "girl", "boy", "lad") + SELF_IS_A_CHILD),

    entry("bedtime-routine", (("before bed", "bedtime routine", "wind down", "get ready for bed",
                               "bedtime"),
                              ("should", "what", "how", "do", "routine", "tips", "best")),
          "The routine matters less than the regularity: same time, lights down, screens off, and "
          "something calm for the last half hour, like a shower, a few pages of a book or the "
          "dishes. Keep the bed for sleeping, and if you are not asleep in 20 minutes get up and "
          "read somewhere dim until you are sleepy.",
          avoid=("baby", "toddler", "child", "son", "daughter", "tea", "coffee", "drink",
                 "phone", "tv", "wine", "alcohol", "beer", "glass")),

    entry("switch-off", (("switch off", "mind racing", "racing mind", "mind is racing",
                          "brain is racing", "head is racing", "thoughts racing",
                          "overthinking", "my brain wont", "my brain won't", "head won't stop",
                          # a head to clear at night is the same ask as a mind that will not
                          # stop, and it was a search punt on main: the daytime "clear my head"
                          # is the stress card, and the words "at night", "before bed" and "to
                          # sleep" are on that row's avoid list, so only the bedroom version
                          # reaches this one
                          "clear my head at night", "clear my mind at night",
                          "clear my head before bed", "clear my mind before bed",
                          "clear my head before sleep", "clear my mind before sleep",
                          "clear my head to sleep", "clear my mind to sleep",
                          "clear my thoughts before bed", "clear my head for bed"),
                         ("night", "bed", "sleep", "how", "cant", "can't", "help", "should",
                          "off", "wont", "won't")),
          "Write tomorrow's list down before bed: most of the racing is your head keeping the "
          "list for you. Then a slow breathing pattern, in for four and out for six, for a couple "
          "of minutes, and get up rather than lie there arguing with yourself if it goes on past "
          "20 minutes.",
          # "how do i switch off mobile data" is a phone setting, not a night habit
          avoid=("work", "boss", "meeting", "email", "deadline", "mobile data", "data",
                 "mobile", "phone setting", "settings", "wi-fi", "wifi", "bluetooth",
                 "airplane", "roaming", "power", "light switch", "plug",
                 # main's cant-switch-off entry answers the "i can't stop thinking" shapes
                 "stop thinking", "thinking about",
                 # "my phone wont switch off" is a device, not a mind
                 "phone", "mobile", "battery", "charger", "charging", "laptop", "tv", "telly",
                 "screen", "appliance", "kettle", "boiler", "car", "engine", "light",
                 # and a house is full of things you switch off that are not your mind:
                 # "how do i switch off the water at the mains" was getting the racing-mind
                 # answer, which is confident, wrong and about a different subject entirely
                 "water", "mains", "stopcock", "stop tap", "stop valve", "tap", "taps", "pipe",
                 "pipes", "plumbing", "valve", "radiator", "heating", "gas", "electricity",
                 "electric", "lectric", "supply", "fuse", "fuse box", "circuit",
                 "socket", "sockets", "alarm", "timer")),

    entry("wake-earlier", (("wake up earlier", "get up earlier", "wake earlier", "wake up at 5",
                            "wake up at 6", "become a morning person", "early riser"),
                           ("how", "should", "want", "help", "tips", "can i")),
          "Shift it 15 minutes at a time, not an hour: set the alarm a quarter of an hour earlier "
          "every three or four days and go to bed a quarter earlier too, or you just lose sleep. "
          "Get daylight on your face within half an hour of waking, and keep the new time at "
          "weekends or Monday undoes it.",
          avoid=("baby", "toddler", "child", "son", "daughter", "kid")),

    # "how do i get out of bed in the morning" and "why is it so hard to get up in the morning"
    # were both shrugs. Getting up earlier is a different question from getting up at all, and the
    # study row wants a revision word beside it, so the plain ask reached nothing at all. This row
    # answers the getting-up itself, whatever makes it hard.
    entry("get-up-in-the-morning",
          (("get out of bed", "getting out of bed", "out of bed", "get up in the morning",
            "getting up in the morning", "get up when", "getting up when", "hard to get up",
            "struggle to get up", "struggling to get up", "cant get out of bed",
            "can't get out of bed", "get myself up", "get going in the morning",
            "cannot get up", "cant get up", "can't get up"),
           ("how", "should", "want", "help", "tips", "can i", "why", "what can",
            "morning", "mornings", "in the morning", "every morning", "myself")),
          "Stand up as soon as the alarm goes, before you have thought about it: that heavy, "
          "can't-move feeling is sleep inertia and it lifts about fifteen minutes after you are "
          "upright. Alarm across the room, curtains open, and the same wake time every day. If "
          "every morning is like that with no energy at all, a blood test for thyroid and "
          "anaemia is the next step.", bias=1,
          # a person who cannot get up and feels awful is a low-mood line, and the snooze row, the
          # study row, the pets, the aches and the coasters keep their own lines
          avoid=("feel", "feeling", "feels", "depressed", "depression", "hopeless", "worthless",
                 "anxious", "anxiety", "panic", "no point", "miserable", "unhappy", "sad all",
                 "cant face", "can't face", "dread", "dreading", "hangover", "hungover",
                 "baby", "babies", "toddler", "toddlers", "child", "children", "kid", "kids",
                 "son", "daughter", "dog", "dogs", "puppy", "cat", "cats", "pet", "pets",
                 "snooze", "snoozing", "alarm", "tired all the time",
                 "my back", "my knee", "my hip", "my neck", "shower", "shaving")),

    entry("hot-night", (("night", "sleep", "sleeping", "bed", "bedroom", "asleep",
                         # "how do i get better sleep in the heat" was the sleep-debt card ("an
                         # extra hour or two is usually the good call after a short night") and
                         # "how do i stay cool in bed" was the washing-machine temperature: both
                         # name the hot night in a way the key had no phrase for
                         "sleep in the heat", "sleeping in the heat", "better sleep in the heat",
                         "in the heat", "in this heat", "hot weather", "warm night", "warm nights",
                         "cool in bed", "stay cool", "keep cool", "cool down at night",
                         # the heat named as the thing doing it: "the heat is keeping me awake"
                         # named no night word at all and was answered "Got it. Is there anything
                         # you'd like a hand with?"
                         # (the sweating words stay out: "i keep waking up sweating" is the
                         # night-sweats answer, which names the fever and the duvet, and this
                         # card would have taken it on "sweating" alone)
                         "keeping me awake", "keeps me awake", "keeping me up", "hot in bed",
                         "too hot to sleep"),
                        ("too hot", "so hot", "its hot", "is hot", "getting hot", "hot night",
                         "hot nights", "boiling hot", "heatwave",
                         "heat", "cool",
                         "sweating", "sweaty", "sticky", "fan", "no air", "hot night")),
          "Cool the room rather than the bed: open windows on both sides for a through draught, "
          "keep the curtains shut in the day, and put a bowl of ice in front of a fan. A lukewarm "
          "shower before bed, cotton sheets and a hot water bottle filled with cold water at your "
          "feet all help more than sleeping with no cover at all.",
          # "cool" was in the key, so "cool cool, anyway I'm off to bed" got the hot-night
          # answer. "heating" and "boiling" are left out of the key on purpose: avoid and key
          # words are matched loosely, so "heating" would cancel the "heat" this entry is about
          # and "boiling" would take a line about boiling a potato.
          avoid=("goodnight", "night night", "off to bed", "im off", "bedtime for me", "see you",
                 "bye", "good night", "baby", "toddler", "child", "fever", "radiator", "boiler",
                 # a dressing question is the clothes, whatever the weather: "what should i wear
                 # to a funeral in the heat" and "what should i wear to a wedding abroad in the
                 # heat" were told to cool the room rather than the bed, because the hot day is
                 # in this card's subject group and the two questions only say "what to wear"
                 "wear", "wearing", "what to wear", "should i wear", "outfit", "outfits",
                 "what do i wear", "what shall i wear", "dress code",
                 "water bottle", "hot flush", "menopause",
                 # a sleeping person asking about the heating is the heating's question: the
                 # thermostat answer had "should i turn the heating off at night" as a bowl of
                 # ice in front of a fan, because "heating" reads as "heat"
                 # bare "heating" is not in the list: avoid words are matched loosely, so it
                 # cancelled the "heat" every hot-night line names ("how do i get better sleep
                 # in the heat" scored nothing at all), and the phrases below are what a heating
                 # question actually says
                 "thermostat", "put the heating", "turn the heating", "heating off",
                 "heating on", "heating bill", "heating cost", "radiator valve",
                 # cooling the room in the day is a different answer, and it already had one:
                 # "how do i cool my bedroom down" was better before this row reached it
                 "cool the room", "cool my bedroom down", "keep the room cool",
                 "keep the house cool", "keep my bedroom cool",
                 # the room being warmed, not a person being cooled: "how do i heat my bedroom"
                 # was answered "cool the room rather than the bed", which is the opposite advice
                 "heat my", "heat the room", "heat the house", "heat a room", "how do i heat",
                 "heating the", "warm my bedroom", "warm the room",
                 # an animal is not a person in bed: "how do i keep my dog cool in the heat"
                 # got a person's hot-night card
                 "dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets", "rabbit",
                 # and neither is a car: "how do i keep cool in the car" was the same card
                 "in the car", "my car", "the car", "car seat"),
          # a washing-machine row keys "hot" and "cool" as temperatures with a bias of its own,
          # so "how do i stay cool in bed" was a 30C wash: this row is the night's question
          # whenever the line also names sleep or a bed
          # a row that got heated is an argument, not a warm night: "my husband got heated at
          # the table last night" was this card's own advice about cooling the bedroom.
          guard=not_the_heat_of_an_argument,
          bias=2),
    # "how do i get to sleep faster" and "i cant fall asleep" were shrugs: the sleep advice
    # existed, but keyed on "sleep trouble" and "mind racing", not on falling asleep.
    entry("toddler-wakes", (("wakes up at", "wakes at", "waking at", "wakes in the night",
                             "wakes every night", "still wakes", "up at night"),
                            ("toddler", "2 year old", "two year old", "3 year old",
                             "three year old", "18 months", "one year old", "she", "he", "her",
                             "him", "night")),
          "A toddler who goes down at seven and is awake again at ten is usually treating bedtime "
          "as a nap: push bedtime later by 15 minutes every few days, keep the room dark and the "
          "last hour quiet, and make the 10pm wake-up boring - a quick cuddle in the dark, no "
          "lights, no play. Ask your health visitor if it is still happening after two weeks.",
          # the subject has to be a child: "i wake up at 3 every night" is the adult answer
          ask=("toddler", "child", "baby", "son", "daughter", "kid", "she", "he", "her", "him",
               "year old", "months old"),
          avoid=("died", "grief", "funeral", "widow", "miss him", "miss her", "passed away",
                 "hospital", "pain", "teething", "ill",
                 # waking at five in the morning is the other half of the night, and
                 # family.early-waking writes that answer: "my 3 year old wakes up at 5 every
                 # morning" was getting the 10pm bedtime-as-a-nap card instead
                 "up at 4", "up at 5", "up at 6", "at 4am", "at 5am", "at 6am", "at 4 am",
                 "at 5 am", "at 6 am", "4am", "5am", "6am", "early waking", "every morning at",
                 # a cat that keeps someone awake is not a toddler: the second group holds the
                 # bare pronouns `she` and `he`, so `my cat is called milly and she keeps me up
                 # at night` landed here once the cat-in-season row stood aside for the name
                 "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies",
                 "pet", "pets", "rabbit", "hamster", "guinea pig", "parrot")),

    entry("fall-asleep", (("fall asleep", "get to sleep", "drop off", "nod off", "drift off",
                           "go to sleep", "lie there", "lying there", "lie awake", "lying awake",
                           "still awake", "wide awake", "nothing happens"),
                          ("cant", "can't", "cannot", "fast", "faster", "quick", "quickly",
                           "hours", "struggle", "hard", "help", "how", "nothing", "happens",
                           "what if", "then what", "just", "awake", "bed", "night",
                           "thinking", "worries", "worrying")),
          "Get up after 20 minutes of lying there awake and do something dull in low light until "
          "you feel sleepy, then go back: staying in bed teaches your brain that bed is where you "
          "lie awake. Keep the wake-up time the same every day, dim the lights an hour before, "
          "and park tomorrow's worries on paper before you get in.",
          avoid=("baby", "babies", "toddler", "child", "children", "kid", "kids", "died",
                 "death", "grief", "passed away", "funeral", "widow", "miss him", "miss her",
                 # "i lie there and nothing happens" is only about sleep with a sleep word or
                 # the bed itself in it; anything else that lies there is something else
                 "dog", "cat", "puppy", "book", "exercise", "yoga", "massage", "phone",
                 "battery", "charger", "engine", "car", "tv", "telly", "screen",
                 "button", "press", "remote", "keyboard", "mouse", "reset", "reboot",
                 "switch on", "turn on", "wont start", "will not start"),
          guard=_a_machine_that_is_on_is_not_a_sleeper),

    entry("sleep-trouble",
          (("sleep", "sleeping", "insomnia", "awake") + SLEEPING_BADLY,
           ("trouble", "can't", "cant", "cannot", "struggle", "problems",
            "better", "at all", "half the night", "help",
            # the adverb form of the same report: "i sleep very badly" and "i sleep so badly"
            # are the phrase above with a word in the middle, and the two words either side of
            # it score the same as the phrase
            "badly", "bad", "poorly", "terribly", "awful", "horribly",
            "have", "got", "ive got", "i've got", "suffer", "suffering",
            "chronic", "years", "mild", "real", "sometimes",
            # How a person asks for a better night: the word for wanting it ("improve",
            # "fix", "sort out") is a way of asking, not the subject, and the subject is the
            # sleep. "how do i improve my sleep" was the search hedge while "how can i sleep
            # better" - the same question in another phrasing - was answered here.
            "improve", "improves", "improving", "improvement", "better sleep",
            "sleep well", "sleeping well", "get more sleep", "more sleep", "need more sleep",
            "make myself sleep", "sort my sleep", "sort out my sleep",
            "reset my sleep", "catch up on sleep", "rest better",
            # The same for the other ask-shapes: "cure", "get rid of" and "stop" are how
            # somebody asks for the end of a bad night, and "tossing and turning" is what
            # they call it. None of them names a subject of its own.
            "cure", "cured", "curing", "get rid of", "stopped",
            "tossing", "turning", "stay asleep", "staying asleep",
            # Being kept awake is the same report as not sleeping, and the line usually blames
            # something for it - the moon, a neighbour, the heat. Without these the blame got the
            # answer: "the full moon keeps me awake" was told the length of a lunar cycle.
            "keeps me awake", "keep me awake", "kept me awake", "wide awake",
            "awake all night", "awake half the night",
            # "what should i do about insomnia" is the plainest ask there is. The list carried
            # the want words ("cure", "get rid of", "improve") and no plain ask, so the shortest
            # question anyone asks about a bad night was a search hedge. health.PLAIN_DO_ASK is
            # the same tuple, kept here so this module needs nothing from health.
            "what should i do", "what can i do", "what do i do", "what shall i do",
            "what would you do", "do about", "anything i can do", "any tips", "any advice")
           + SLEEPING_BADLY),
          "The things that work: same wake-up time every day, no caffeine after early afternoon, "
          "not much alcohol in the evening (it wakes you in the second half of the night), a "
          "cool dark room, and getting out of bed if you're awake for more than 20 minutes. Screens "
          "off half an hour before bed and a short walk most days help more than any app. If you're "
          "worn out all day too, or it has gone on for weeks, ask a GP: they can check your bloods, "
          "and broken sleep plus no energy is worth ruling out.",
          avoid=("baby", "toddler", "child", "nap", "died", "death", "grief", "passed away",
                 "funeral", "lost my", "widow", "miss him", "miss her",
                 # "i cant sleep because i miss my mum" was getting sleep hygiene; the loss
                 # answer is the one that helps, so any "miss my ..." stands this down
                 "miss my", "miss them", "still miss", "thinking about my",
                 # waking at a set time is chat's line, and chat answers it with the memory of
                 # the conversation ("i cant get out of bed most mornings" then "waking at 5")
                 "waking up at", "wake up at", "waking at", "wake at", "up at 3", "up at 4",
                 "up at 5", "at 3am", "at 4am", "at 5am", "at 6am",
                 "fever", "flu", "cough", "chesty", "sore throat",
                 # "have" and "got" are in the key so a plain "i have insomnia" answers, but
                 # they also met anything else with the word sleep in it: where you sleep, what
                 # you wear or carry to bed, and the device you sleep with
                 "sofa", "couch", "settee", "car", "floor", "tent", "sleeping bag",
                 "tracker", "watch", "fitbit", "app", "study", "test",
                 "make up", "makeup", "contacts", "contact lenses", "lenses", "fan",
                 "window", "heating", "air con", "radiator", "shift", "night shift",
                 # a machine that will not stay awake is the laptop power setting, not a night:
                 # "how do i stop my laptop going to sleep" is answered in technology
                 "laptop", "computer", "macbook", "pc", "monitor", "keyboard", "router",
                 # a single bad night is a comfort line, not a habit to overhaul: "i got no sleep
                 # last night" lost the short answer and got the whole routine instead
                 "last night", "tonight", "no sleep", "not slept", "didnt sleep",
                 "didn't sleep", "couldnt sleep", "couldn't sleep", "havent slept",
                 "haven't slept", "one night", "jet lag", "jetlag",
                 # "i havent been sleeping" wants the warm line and the offer of a GP, which
                 # the comfort answer already gives: a person who says that has told you it has
                 # been going on, so a hygiene list is a lecture rather than an answer
                 # "been sleeping" alone cannot be in the avoid: "i have been sleeping badly
                 # for weeks" is the same plain report as "i sleep badly", and it was standing
                 # the row down for an echo. The negative forms below are what the comfort line
                 # is for, and each of them is a phrase of its own.
                 "havent been sleeping", "haven't been sleeping",
                 "not been sleeping", "not sleeping at all", "able to sleep",
                 # a better answer already owns these: revision has the exam-night answer, a
                 # plane has the jet-lag one, and a baby or a child in the line is a parent's
                 # question ("i have insomnia and a newborn" wants the acknowledgement first).
                 # "i cant sleep before a flight" stays here: the night before a flight is at
                 # home, and "set your watch when you board" answers a different question
                 "exam", "exams", "revision", "revise", "cramming", "cram", "mock",
                 "mocks", "coursework", "dissertation", "thesis", "revision notes",
                 "plane", "airport", "hotel", "hotels",
                 "time zone", "timezone", "travelling", "traveling",
                 "newborn", "new baby", "son", "daughter", "stepson", "stepdaughter",
                 "grandson", "granddaughter", "year old", "years old", "kids",
                 "my boy", "my girl", "my little one",
                 # "i sleep badly and feel tired all the time" is answered better by the tired
                 # row, which is about the daytime cost rather than the night
                 "tired", "exhausted", "no energy", "fatigue",
                 # a named cause has its own card, and its card is better than this one:
                 # "i dont sleep well when its hot" wants the cool-room answer, "i sleep badly
                 # when i drink" wants the caffeine cut-off, "i sleep badly on night shifts"
                 # wants the daytime-sleep plan
                 "hot", "heat", "heatwave", "humid", "boiling", "warm room",
                 # "when i drink" is the evening glass, and the habits answer says the same
                 # thing in one line; the named drinks are what the caffeine card is for.
                 "alcohol", "beer", "wine", "tea", "coffee",
                 "caffeine", "espresso", "latte",
                 # a bad back is answered by the back card, and each line below names it
                 "back", "backs", "sore back", "back pain", "backache", "lower back",
                 "back hurts", "back hurt", "back aches", "back ache", "sciatica",
                 "night shift", "night shifts", "nightshift", "shifts", "shift work",
                 "jet lag", "jetlag",
                 # The same rule for the other half of the sentence: the bare report is only
                 # answered here when the line names no cause and no daytime cost. A snoring
                 # partner, a back that hurts, exams, stress and a feeling of low mood all name
                 # a better card, and so does a dog or a cat, whose sleep is its own answer.
                 "snore", "snores", "snoring", "snorer", "partner snores",
                 "back", "back pain", "backache", "lower back", "sore back",
                 "pain", "pains", "painful", "hurts", "hurting", "ache", "aches", "aching",
                 "exam", "exams", "revision", "revising", "deadline", "deadlines",
                 # stress and worry are deliberately not in this list: their cards sometimes
                 # only say "that's a lot to carry, what would help today", and an answer about
                 # sleep is worth more than an acknowledgement. The daytime cost below is not:
                 # that card talks about the tiredness itself, which is the same complaint.
                 "knackered", "shattered", "wiped out", "done in", "worn out", "drained",
                 "feel low", "feeling low", "low mood", "depressed", "miserable",
                 "hayfever", "hay fever", "allergy", "allergies", "allergic",
                 # the night before a flight is the jet-lag card's question; "i cant sleep
                 # before a flight" is not, because that is the night at home, so the phrase
                 # is the night rather than the word.
                 "night before a flight", "before an early flight", "early flight",
                 "neighbour", "neighbours", "neighbors", "noisy", "noise", "loud music",
                 "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens",
                 "pet", "pets", "vet",
                 # a child's or a partner's sleep is not the person's own report
                 "my son", "my daughter", "my husband", "my wife", "my partner", "my mum",
                 "my dad")),
    entry("baby-sleep-night", (("baby", "babies", "newborn", "toddler", "toddlers",
                                "1 year old", "2 year old", "two year old"),
                               ("sleep", "night", "nighttime", "through", "wakes", "waking",
                                "wake up")),
          "For a baby over six months, a consistent wind-down, dim lights and a fixed bedtime help "
          "more than any trick; feedings at night are normal for much longer than people expect. "
          "Ask your health visitor or GP if you're worried, and never use anything that promises a "
          "quick fix for a very young baby.",
          # a baby who coughs, wheezes or sounds congested at night is an illness question for the
          # health visitor, not the sleep-habit answer, and "how many hours" asks for a figure
          avoid=INFANT_RED_FLAGS + ("not feeding", "grunt", "grunting", "grunts", "snorting",
                                    "gasping", "cough", "coughs", "coughing", "cold", "colds",
                                    "fever", "temperature", "rash", "wheeze", "wheezing",
                                    "congested", "congestion", "blocked nose", "runny nose",
                                    "chesty", "breathing", "breath", "vomiting", "being sick",
                                    "reflux", "colic", "teething", "ill", "poorly", "unwell",
                                    "how many hours", "how much sleep", "hours a day",
                                    # a toddler woken at five is the early-waking row's question
                                    "toddler", "toddlers", "three year old", "3 year old",
                                    "two year old", "2 year old", "four year old", "4 year old",
                                    # Grinding teeth at night is the dentist's row: "my baby
                                    # grinds her teeth at night" was the sleep card, because
                                    # the night word is in the key and teething is the only
                                    # tooth word here.
                                    "grind", "grinds", "grinding", "grinds her teeth",
                                    "grinds his teeth", "grinding her teeth",
                                    "grinding his teeth",
                                    "preschooler", "preschool", "early waking", "wakes at 5",
                                    "wakes up at 5", "wakes at 4", "wakes up at 4")),
    entry("tv-sleep", (("tv", "television"), ("sleep", "bed", "bad", "before bed")),
          "It isn't dangerous, but the light and the story keep your brain alert, so you fall "
          "asleep later and wake more in the night. If you need something playing, a podcast or "
          "radio set to sleep is easier on sleep than a screen."),
    # Reading is the wind-down most people already have, and asking whether it is bad for
    # sleep got a novel: "is it bad to read in bed" was `pick-plain`, "reading before sleep good
    # or bad" was a book "about" sleep, and "how do i stop reading so late" was the lapsed-reader
    # answer. The medium is the whole question - paper in low light is fine, a backlit screen and
    # a page-turner at bedtime are not - so the entry is a sleep answer beside the tv one.
    entry("read-bedtime",
          (("read", "reading", "reads", "book", "books", "novel", "kindle", "ereader",
            "e-reader", "chapter", "chapters", "audiobook", "audio book"),
           ("bed", "in bed", "before bed", "bedtime", "night", "sleep", "asleep", "late",
            "sleeping", "fall asleep", "wind down", "evening", "bad", "good", "ok", "okay",
            "stop")),
          ("Reading on paper in low light is one of the better wind-downs there is, and a book you "
           "have read before is easier to put down than a new one. It is the backlit screen and "
           "the scrolling that delay sleep, so a phone or tablet story is the one to move; an "
           "e-reader on a warm setting is much closer to paper. If a book hooks you so hard you "
           "are still going at 2am, keep a dull one by the bed and save the page-turner for the "
           "daytime."),
          # a child's bedtime story, a book to read next and a present are three other answers,
          # and so is a line about a light that will not switch off
          avoid=("kid", "kids", "child", "children", "son", "daughter", "toddler", "baby",
                 "teenager", "teen", "year old", "years old", "read to", "reading to",
                 "aloud", "out loud", "stories for", "bedtime story", "bedtime stories",
                 "recommend", "suggest", "what book", "which book", "what should i read",
                 # a line that asks for a book to read is a pick, and the setting it names
                 # ("in bed", "before bed") does not turn it into a question about sleep
                 "good book", "book to read", "books to read", "something to read", "any book",
                 "a book for", "some book", "reading list",
                 "gift", "present", "birthday", "christmas", "library", "bookshop",
                 "book club", "lamp", "bulb", "light", "lights", "torch", "curtain", "blind",
                 "shut", "broken", "battery", "glasses", "eyes", "eye test", "sight",
                 "how do i read", "how to read", "learn to read", "dyslexia",
                 "finished", "finish a book", "gave up", "give up"),
          bias=1),
    # The afternoon dip is a time of day, not a feeling: "how do i stop feeling tired in the
    # afternoon" is nobody's idea of how to have a difficult conversation, but the bag of words
    # "how i feel" in that row's key read it that way, and this answer did not exist to win.
    entry("afternoon-slump",
          (("afternoon", "after lunch", "after my lunch", "3pm", "3 pm", "three o'clock",
            "mid afternoon", "midafternoon", "post lunch", "2pm", "2 pm", "4pm", "4 pm",
            "late afternoon", "middle of the day", "after eating", "tired in the afternoon",
            "sleepy in the afternoon", "afternoon slump", "afternoon dip"),
           ("tired", "sleepy", "slump", "sluggish", "drained", "flagging", "yawn", "yawning",
            "crash", "nod off", "no energy", "low energy", "knackered", "exhausted", "feel",
            "feeling", "focus", "concentrate", "foggy", "brain fog", "drowsy", "stop", "beat",
            "avoid", "fix", "cure"),
           # The "how do i stop" third part is what makes this beat the row that read "feeling
           # tired" as the "feelings" you share with a partner: two parts each, and that row
           # won the tie. A line that says the day and asks how is this answer's.
           ("how do i stop", "how do i", "how can i", "how to", "what can i do", "tips",
            "ways", "best way", "help")),
          "The dip after lunch is your body clock, not laziness: eat a lunch with protein and "
          "fibre in it rather than a big pile of white carbs, and go outside for ten minutes "
          "afterwards, because daylight and moving your legs take the dip down most. A coffee "
          "before 2pm helps, one after 3pm costs you tonight's sleep. If it happens every day for "
          "weeks, get your iron and thyroid checked.",
          # the dips that belong to a baby, a child or a pregnancy are their own answers
          avoid=("toddler", "child", "kid", "baby", "year old", "son", "daughter", "pregnant",
                 "pregnancy", "expecting", "breastfeeding", "nursing", "newborn", "my mum",
                 "my dad", "my husband", "my wife", "elderly", "dementia",
                 # a headache, a nap or the night's sleep are answered better elsewhere
                 "headache", "migraine", "nap", "naps", "nap", "can't sleep", "cant sleep",
                 "wake up", "waking", "insomnia", "at night", "before bed")),
    entry("nap", (("nap", "naps", "napping", "power nap", "siesta"),
                  ("groggy", "afternoon", "how long", "20 minutes", "best way", "refreshed",
                   "sleepy", "tired", "before", "after lunch", "feel", "wake up",
                   # "is it ok to nap in the day" asks what "how long should a nap be" asks:
                   # the second word was the only thing missing, and it was the search hedge
                   "day", "in the day", "during the day", "ok", "okay", "alright", "bad",
                   "good", "harm", "healthy", "worth it", "should i", "is it ok")),
          "Keep a nap to 20 minutes and take it before 3pm, or you'll feel groggy and sleep worse "
          "that night; 30 to 60 minutes is where the grogginess lives, so set an alarm. Skip it if you "
          "already lie awake at night, and if you need one every afternoon for weeks, that is "
          "worth a word with the GP, especially with low mood, thirst or weight loss.",
          # a nap is only this entry when the line is about an adult's nap: "what about naps,
          # should i cut them" in a chat about a 3 year old belongs to the child bedtime answer
          avoid=("toddler", "child", "kid", "baby", "year old", "son", "daughter", "she", "he",
                 "her", "him", "pregnant", "pregnancy", "expecting", "breastfeeding", "nursing",
                 "cut them", "cut it",
                 # how to stop napping is a habit question, not a "should I nap" one: the
                 # answer is how to cut a habit down, not 20 minutes before 3pm
                 "stop napping", "stop taking naps", "stop my naps", "give up naps",
                 "stop napping in", "quit napping")),
    # Cola and energy drinks share the question this answers. Tea does not: chamomile and the
    # bedtime teas have no caffeine at all, and "is chamomile tea good for sleep" was being told
    # the half-life of a drink it does not contain. The tea-before-bed entry below is the one
    # that names the drink and the hour.
    entry("caffeine-sleep", (("caffeine", "coffee", "espresso", "energy drink", "energy drinks",
                              "cola", "diet coke"),
                             ("sleep", "afternoon", "cut", "stop", "bed", "keep me up", "up",
                              "would that", "keep me awake", "keep you up", "keep you awake",
                              "keeps me awake", "keeps you awake", "awake at night", "cant sleep",
                              "can't sleep", "not sleep", "wake up")),
          "Caffeine has a half-life of about five hours, so a 4pm coffee is still in your system "
          "at bedtime: stop by early afternoon. Cutting down gradually over a week avoids the "
          "headaches that a sudden stop brings.",
          # "keep" is the only word this question shares with the shelf-life table, and
          # "does coffee keep you up" was answered with the airtight tin and the freezer.
          bias=1),
    # The timeline of caffeine itself: how long a cup lasts, and how long the headaches last when
    # it goes. "how long till it helps", two turns after "should i cut down", was answered with
    # "Ground coffee is at its best in the 2 weeks after opening" - the shelf-life table took the
    # carried word "coffee" and the "how long". "how long does caffeine last" was the same card
    # read out as a bare "2 weeks.", and "how long does caffeine stay in your system", "how long
    # before caffeine wears off" and "i stopped drinking coffee and i have a headache" were shrugs
    # or the general tension-headache card.
    entry("caffeine-how-long", (("caffeine", "coffee", "coffees", "espresso", "caffeinated",
                                "energy drink", "energy drinks", "cola", "diet coke"),
                               ("how long", "how soon", "how many hours", "last", "lasts",
                                # the widener hands this one over as "how long till it helps
                                # coffee": the subject is carried, the timeline phrase is in the
                                # line, and a bare tie with the keeping card lost it.
                                "till it helps", "until it helps", "how long till",
                                "how long until", "till i feel", "until i feel",
                                "wears off", "wear off", "worn off", "system", "withdrawal",
                                "withdrawals", "skip", "skipped", "skipping", "stopped",
                                "stopped drinking", "quit", "gone", "missing", "missed",
                                "dont drink", "without"),
                               # the third part is the complaint or the ask, so "why do i get
                               # headaches when i skip coffee" is this answer rather than the
                               # general tension-headache card
                               ("headache", "headaches", "head", "tired", "irritable", "grumpy",
                                "helps", "feel", "long", "shaky")),
          _caffeine_timeline,
          # The shelf-life table shares "how long" and the carried "coffee", and it is the card
          # that was winning: "how long does coffee keep" is the one question here that is not
          # about the person.
          avoid=("keep", "keeps", "kept", "stored", "store", "beans", "ground", "grounds",
                 "brewing", "brew", "pot", "mug", "fridge", "freezer", "shop", "cafe",
                 "price", "cost", "pods", "pod", "machine", "maker", "makers", "grinder",
                 # "how long is coffee good for after opening" is the tin, not the half-life
                 "after opening", "once opened", "opened", "good for", "shelf life", "shelf",
                 # a sleep question has its own two answers (the half-life at bedtime, and
                 # adenosine): this row is the timeline, not the reason
                 "sleep", "sleeping", "sleepy", "bed", "bedtime", "awake", "insomnia",
                 "dehydrate", "dehydration", "addicted", "addiction", "bad for", "safe", "limit",
                 "much", "many", "pregnant", "pregnancy", "breastfeeding"),
          # The keeping card scores the same five on "how long till it helps" with the subject
          # carried, and so does the container follow-up row: the tie is broken on bias, and this
          # is the answer the line is asking for.
          bias=3),
    # "is a lie in at the weekend ok" was a shrug, and it is the commonest sleep question after a
    # bad week. The answer is the body clock one: an hour is free, two is borrowed from Monday.
    entry("lie-in", (("lie in", "lie-in", "lying in", "lay in", "sleep in", "sleeping in",
                      "slept in", "longer in bed", "stay in bed", "catch up on sleep",
                      "catch up on my sleep"),
                     ("weekend", "ok", "okay", "bad", "harm", "saturday", "sunday", "allowed",
                      "matter", "should i", "is it ok", "can i")),
          "Up to an hour later is free; two hours or more moves your body clock, so Sunday night "
          "is harder and Monday morning feels like jet lag. If you are short of sleep, an earlier "
          "night is worth more than a long lie-in, and a 20-minute nap in the afternoon gets you "
          "through without shifting the clock.",
          # a child who will not stay in bed, and a care or hospital line, are other answers
          avoid=("toddler", "child", "kid", "baby", "year old", "son", "daughter", "school",
                 "teenager", "dog", "cat", "pet", "hospital", "care home", "car", "van")),
    entry("alcohol-sleep", (("alcohol", "wine", "beer"),
                            ("sleep", "drink", "night", "bed", "wind down", "winding down",
                             "relax")),
          "A drink helps you fall asleep but breaks it up later: expect to wake around 3am and "
          "sleep less deeply. Leaving three hours between your last drink and bed, with water in "
          "between, makes a clear difference.",
          # medicine, pregnancy and breastfeeding are safety questions, not sleep ones
          avoid=("pregnant", "pregnancy", "expecting", "breastfeeding", "breast feeding",
                 "nursing", "antibiotics", "tablets", "medication", "medicine", "pills",
                 # a named painkiller is the same safety question, and "is it ok to drink wine
                 # with paracetamol" was answered with this card: a drink breaking up sleep is
                 # not what somebody holding a packet of paracetamol asked
                 "paracetamol", "ibuprofen", "nurofen", "painkiller", "painkillers",
                 "co-codamol", "co codamol", "codamol", "aspirin", "antihistamine",
                 "doctor", "driving", "drive")),
    entry("screen-bedtime", (("phone", "phones", "screens", "screen", "scroll", "scrolling",
                              "doomscroll", "doom scrolling", "tiktok", "instagram", "reels",
                              "youtube", "facebook"),
                             ("bed", "sleep", "before bed", "evening", "night")),
          "The light isn't the main problem; the scrolling is, because it keeps your mind busy. Try "
          "putting the phone on charge outside the bedroom for a week, or set a timer 30 minutes "
          "before bed and read on paper instead.",
          avoid=("died", "battery", "charger", "broken", "lost", "cracked", "contract", "bill",
                 # "i left my phone in a taxi last night" is the lost-phone answer, not a sleep
                 # habit: the word night alone must not make this the answer
                 "left", "left it", "taxi", "cab", "stolen", "stole", "theft", "robbed",
                 "missing", "found", "hand it in", "dropped", "airport", "train", "bus",
                 "block", "blocked", "sim", "police",
                 # a phone that wakes you with notifications is technology's notifications answer.
                 # "pings" and "pings all night" belong with it: "my phone pings all night" was
                 # the scrolling card, which is about the evening, not about being woken.
                 "notification", "notifications", "do not disturb", "alert", "alerts",
                 "ringing", "rings", "buzzing", "buzzes", "vibrating", "vibrates",
                 "ping", "pings", "pinging", "pinged",
                 "wakes me", "waking me", "woke me", "keeps waking", "keep waking",
                 "woken up by", "being woken",
                 # a parent's line about a child's phone is the family limit question
                 "kid", "kids", "child", "children", "son", "daughter", "teenager", "teen",
                 # taking photos of the night sky is the camera's question
                 "photo", "photos", "picture", "pictures", "camera", "night mode", "video",
                 # an argument is its own answer, and "on the phone" plus "last night" is not a
                 # bedtime habit: "i had a proper row with my sister on the phone last night" was
                 # the scrolling card. Only the argument words, never a bare "row".
                 "a row", "row with", "row about", "had a row", "proper row", "right row",
                 "argued", "arguing", "argues", "argument", "arguments", "quarrel",
                 "quarrelled", "quarreling", "fell out", "falling out", "fight with",
                 "fought", "cross with", "angry with",
                 "my boy", "my girl")),
    entry("wake-up-tired", (("wake up", "waking up", "wake", "woke up", "get up", "morning",
                             "even after", "even though", "hours sleep", "8 hours", "seven hours",
                             "8hrs", "seven hours sleep"),
                            ("tired", "knackered", "exhausted", "groggy", "drained", "shattered",
                             "not rested", "more tired", "worse than", "no energy", "unrested")),
          "Waking up tired usually means broken sleep rather than too little: a warm room, a drink "
          "in the evening, a snoring partner and a phone in bed all fragment it. Try a cooler "
          "bedroom, no alcohol within three hours of bed, and the same wake time every day for two "
          "weeks, because that last one is what rebuilds a steady night.",
          avoid=INFANT_RED_FLAGS + ("baby", "toddler", "child", "children", "kid", "kids", "son",
                                    "daughter", "puppy", "cat", "dog")),
    entry("wake-middle-night", (("middle of the night", "in the middle of the night",
                                 "wake up in the middle of the night", "waking in the night",
                                 "wake in the night", "cant stay asleep", "can't stay asleep",
                                 "wake several times", "waking several times"),
                                ("night", "why", "how", "stop", "keep", "help", "always",
                                 "every", "sleep", "again")),
          "Waking in the middle of the night is normal - the trick is what you do next: stay in "
          "bed, keep the room dark, and do not look at the clock or your phone, because that is "
          "what teaches your brain to be awake at 3am. If you are awake more than 20 minutes, get "
          "up and sit somewhere dim until you feel sleepy. Alcohol, a late meal and a warm bedroom "
          "are the usual culprits.",
          ask=("wake", "waking", "woke", "awake", "night", "asleep"),
          avoid=("baby", "toddler", "child", "children", "kid", "kids", "son", "daughter",
                 "dog", "cat", "nightmare", "pregnant", "pregnancy")),

    entry("night-shift-sleep", (("work nights", "working nights", "work nights", "night shift",
                                "night shifts", "nightshifts", "on nights", "on shifts",
                                "shift work", "shift pattern", "rotating shifts"),
                               ("sleep", "sleeping", "day", "daytime", "cant", "can't", "never",
                                "tired", "rest")),
          "Pick one stretch of daytime to sleep and guard it like a night: straight home, dark "
          "room, phone off, and the same hours seven days a week, including days off, so your body "
          "clock settles. Wear sunglasses on the way home and keep the bedroom cold, and take a "
          "short nap before the shift rather than a long one after it.",
          # "its worse at night and im not sleeping" is about the cough, not a shift pattern
          avoid=("baby", "toddler", "child", "newborn", "cough", "cold", "worse at night",
                 "hurts", "pain", "ache")),

    # A duvet is chosen by tog, and nobody knows the numbers: "which duvet tog for winter" and
    # "what bedding is warmest" were both a hedge, while "how do i wash a duvet" is the cleaning
    # row's line. The warmth words are the key's second half here and the washing words stand the
    # row down, so the two questions about one duvet stay apart.
    entry("duvet-tog",
          (("duvet", "duvets", "quilt", "quilts", "bedding"),
           ("tog", "togs", "warm", "warmest", "warmer", "winter", "cold", "cosy",
            "thick", "thicker", "summer")),
          "A 13.5 tog duvet is the winter one, 4.5 tog is for summer and 10.5 tog or two thin ones "
          "that button together cover the rest of the year. Tog measures warmth for its weight, "
          "not how heavy it feels, so a 13.5 tog feather duvet and a 13.5 tog hollowfibre one are "
          "equally warm - buy the filling you can wash and dry. For a cold bedroom, a second "
          "lighter duvet on top or a hot water bottle at your feet warms you faster than a heavier "
          "one over your whole body.",
          # a duvet that is washed, stained or smelly is the cleaning row's; a baby's bedding and
          # the safe-sleep rules are the baby rows'; a fever is not a tog
          avoid=("wash", "washing", "washed", "clean", "cleaning", "stain", "stains",
                 "smell", "smells", "musty", "yellow", "dryer", "tumble", "machine",
                 "baby", "babies", "newborn", "toddler", "cot", "crib", "moses",
                 "fever", "temperature", "sweat", "sweating", "night sweats", "allergy",
                 "allergic", "feather allergy", "dust mite",
                 # being cold in bed is a bedding question only while it is about the bedding:
                 # "i am always cold in bed" is the always-cold symptom row's line, whose answer
                 # is thyroid, iron and the doctor, and a tog is no answer to it
                 "always cold", "always so cold", "all the time", "constantly", "cold hands",
                 "cold feet", "cold all", "feel the cold", "thyroid", "iron", "anaemic",
                 "anemic", "circulation", "shivering", "shiver", "tired all", "exhausted",
                 "cold sweats", "cant get warm", "can't get warm", "never warm"),
          bias=1),
    entry("bedroom-temp", (("bedroom", "room temperature", "my room"), ("warm", "warmth",
                            "temperature", "degrees", "hot", "cold", "how warm", "how cool",
                            # A bedroom said to be freezing is this row's question, not the
                            # cold house's: the bedroom has its own answer and "freezing" is
                            # the word people use for it. Every phrase names the bedroom, so
                            # "my room is freezing" keeps the room-heating card it had.
                            "bedroom is freezing", "bedroom is freezing cold",
                            "bedroom freezing", "freezing bedroom", "bedroom is so cold",
                            "bedroom is too cold", "bedroom is baltic", "bedroom is chilly",
                            "bedroom is always freezing", "bedroom is freezing at night",
                            "bedroom is cold at night",
                            # A bedroom's temperature said as a picture, which is how most
                            # people say it: "my bedroom is like an oven", "its like a fridge in
                            # my bedroom". The appliance words below are the ones that used to
                            # read these as a question about the fridge.
                            "like a fridge", "like a freezer", "like an oven", "like a sauna",
                            "like a furnace", "like the arctic", "icebox", "an icebox")),
          "A bedroom around 16 to 18C suits most people for sleep: cool enough that you need a "
          "duvet, not so cold you wake up. Cracking a window for ten minutes before bed, a lighter "
          "duvet in summer and a hot water bottle rather than a hot room all help, and a warm "
          "bath an hour before bed sends you to sleep faster than a warm bedroom does.",
          ask=("bedroom", "room temperature", "my room"),
          # a baby's bedroom is the safe-sleep questions', not an adult's duvet
          avoid=("baby", "babies", "newborn", "toddler", "cot", "crib", "nursery", "infant",
                 "child", "children", "kid", "kids",
                 # "room temperature" is also how a recipe talks about butter, eggs and meat, and
                 # "how do i get butter to room temperature" was answered with a bedroom that
                 # suits most adults for sleep. Food words are the food rows'.
                 "butter", "cake", "meat", "chicken", "egg", "eggs", "milk", "cheese", "dough",
                 "yeast", "batter", "chocolate", "wine", "beer", "yoghurt", "yogurt", "roast",
                 "baking", "thaw", "defrost",
                 # the appliance the food is in, not a bedroom described as one: a bare "fridge"
                 # took "its like a fridge in my bedroom" out of this row and left it a shrug
                 "in the fridge", "the fridge", "my fridge", "fridge is", "fridge not",
                 "fridge door", "in the freezer", "the freezer", "my freezer", "freezer is",
                 # "should i let my steak come to room temperature" is a kitchen instruction and
                 # was still read as a bedroom: the cuts are not the word "meat", so each one
                 # has to be named for the food rows to keep their own line.
                 "steak", "steaks", "beef", "pork", "lamb", "turkey", "bacon", "sausage",
                 "sausages", "fish", "salmon", "pastry", "cream", "cook", "cooking", "oven",
                 "recipe", "soften", "mayonnaise",
                 # a radiator that will not heat is the heating rows' question, whatever room it
                 # is in: "the radiator in my room is cold" was answered with the temperature a
                 # bedroom should be for sleep, which is not what was asked. So is every other
                 # part of the system a person names when a room is cold.
                 "radiator", "radiators", "heating", "boiler", "thermostat", "thermostatic",
                 "bleed", "bleeding", "trv", "valve", "valves"),
          bias=1),

    # "does tea keep you up" asks about tea and sleep at once, and the caffeine entry no longer
    # answers for tea: the answer here names the drink and the hour, which is right for chamomile
    # and for a builder's as well.
    entry("tea-bedtime", (("tea", "coffee", "drink"), ("bed", "sleep", "night", "bedtime",
                                                       "before", "keep you up", "keep me up",
                                                       "keep you awake", "keep me awake",
                                                       "keeps you awake", "keeps me awake",
                                                       "late at night", "late")),
          "Tea has enough caffeine to keep you awake if it's after about 2pm, so switch to a herbal "
          "one or a warm drink without caffeine in the evening. A milky drink is fine; it's the "
          "caffeine and the late loo trip that cost you sleep.",
          bias=1),

    # --- everyday body care ------------------------------------------------
    # Waking because something hurts is not a sleep habit: the night-waking answer was the
    # clock-and-light advice for "i keep waking at 3am with pain", and the pain is the cause.
    entry("wake-in-pain",
          # The hour is the shape of the waking, not the reason for it. With "at 3am" in the
          # pain group, "i keep waking up at 3am and cant get back to sleep" met it - one word
          # from each group - and was told to take a painkiller, when nothing hurt. The hour
          # now sits with the waking words, so this row needs a word that says pain.
          (("keep waking", "wake up", "waking up", "wake at", "waking at", "woken up",
            "wide awake", "up in the night", "in the night", "at 3am", "at 2am", "at 4am",
            "at 3", "at 2", "at 4", "3am", "2am", "4am", "3 am", "2 am", "4 am"),
           # "back" on its own is "cant get back to sleep", which is why every back here is
           # said with the pain: "i keep waking up at 3am and cant get back to sleep" was a
           # painkiller a half hour before bed.
           ("pain", "painful", "ache", "aching", "hurts", "hurting", "sore", "stiff",
            # "cant get back to sleep" made this entry answer a night waking that never
            # mentioned pain: "back" is the particle in "get back", "go back" and "come
            # back". A body part counts where the line says whose it is or that it hurts.
            "my back", "bad back", "back pain", "backache", "aching back", "sore back",
            "stiff back", "lower back", "back problem", "back trouble",
            "shoulder", "hip", "knee", "legs", "leg", "arm", "neck", "cramp", "cramps",
            "pins and needles", "heartburn", "reflux", "toothache")),
          "If pain is what wakes you, treat the pain rather than the sleep: take a painkiller half "
          "an hour before bed if you can, prop the sore part on a pillow and put a rolled towel "
          "under a bad back. Warm bath and gentle stretches before bed loosen a stiff shoulder or "
          "hip. If it wakes you most nights for weeks, or comes with numbness, weakness or weight "
          "loss, get it looked at.",
          bias=3,
          # a hot swollen calf, chest pain, a fever or a cough is a different answer, and so is a
          # child's night, which is the family domain's
          avoid=("calf", "calves", "swollen", "swelling", "chest", "breathless", "fever",
                 "cough", "coughing", "baby", "toddler", "child", "children", "son", "daughter",
                 "mum", "dad", "partner", "husband", "wife", "dog", "cat", "pregnant",
                 "morning", "mornings", "first thing", "all over", "get out of bed",
                 # a sore throat in the morning is the health domain's, not pain that wakes you
                 "throat", "voice", "hoarse", "croaky", "sore throat",
                 # a cramp waking someone has its own answer, which says what a cramp is and how
                 # to stop it, and "treat the pain before bed" is not the same help
                 "cramp", "cramps", "cramping", "leg cramp", "leg cramps", "charley horse",
                 ) + INFANT_RED_FLAGS),

]

ENTRIES.append(entry(
    "sleep-position",
    (("front", "on my front", "on your front", "on my back", "on your back", "on my side",
      "on your side", "stomach", "sleeping position", "position to sleep", "best position",
      "which side", "side to sleep"),
     ("sleep", "sleeping", "slept", "asleep", "bed", "night", "bad", "best", "should i",
      "better", "position", "healthy", "okay", "ok")),
    "On your side is the best default: it keeps the airway open and takes the load off your "
    "lower back, and a pillow between the knees keeps the hips level. Front sleeping leaves the "
    "neck turned for hours, which is why front sleepers wake with a stiff neck, and on your back "
    "snoring and heartburn are worse. The position you can stay asleep in beats the perfect one - "
    "and if you wake with a sore neck or back, the pillow is usually the thing to change first.",
    ask=("sleep", "sleeping", "slept", "asleep", "bed", "night", "position", "nap"),
    # A pregnancy has its own advice and it is not this card's to give, and a line about
    # wrinkles is asking about skin, so both stand this row down rather than take a general
    # answer they did not ask for.
    # A baby on its front is the one sleep question with a hard answer of its own, and an adult's
    # side-sleeping default is not it: every word here stands this row down so the baby-sleep card
    # answers, which is what main did before this row existed. A symptom is not a position either
    # - "my stomach hurts at night" is the stomach card and "sleeping on my side hurts my shoulder"
    # is the shoulder card - so the complaint words stand down too.
    avoid=("my back hurts", "back pain", "sore back", "back ache", "lower back", "back door",
           "front door", "back garden", "front garden", "come back", "go back", "back to work",
           "back home", "back from", "on the front", "front room", "back room", "back seat",
           "pregnant", "pregnancy", "expecting", "wrinkle", "wrinkles", "wrinkly", "skin",
           "baby", "babies", "newborn", "new born", "infant", "cot", "cot death", "toddler",
           "my son", "my daughter", "my child", "children", "kids", "my boy", "my girl",
           "hurts", "hurt", "hurting", "pain", "painful", "sore", "ache", "aches", "aching",
           "stiff"),
    bias=1))

# --- what the hour before bed should hold ----------------------------------
# "whats a good night routine" and "whats a good evening routine" reached the habit row in
# `routines.py`, which answers how to *build* a habit rather than what the hour should contain.
ENTRIES.append(entry(
    "a-night-routine",
    (("routine", "routines", "ritual", "wind down", "winddown", "wind-down", "what should i do"),
     ("night", "nights", "evening", "evenings", "before bed", "bedtime", "sleep", "bed")),
    "The same hour in the same order every night: screens off 45 minutes before bed, the lights "
    "down, and three small things done the same way - teeth, tomorrow's clothes out, ten minutes "
    "of a book. Keep the bedroom cool, dark and quiet, and put the phone on charge in another "
    "room, because the check at 11pm is what stretches the hour. If you are not asleep in about "
    "twenty minutes, get up and read somewhere dim until you are sleepy rather than lying there "
    "watching the clock.",
    bias=3,
    avoid=("baby", "babies", "newborn", "infant", "cot", "toddler", "child", "children", "kids",
           "my son", "my daughter", "pregnant", "pregnancy", "shift", "night shift",
           "work nights", "worked nights", "insomnia", "cant sleep", "can't sleep",
           "wake up", "waking", "woke up", "hot", "sweating", "pain", "ache", "snore",
           "snoring", "nap", "naps",
           # A thing that goes wrong in the evening is that thing's card, not the hour before
           # bed: "the wifi drops every evening when everyone is home, what should i do" was
           # answered with this routine, because the row claims the ask ("what should i do")
           # and the evening, so two setting words were enough to reach it. Nothing below is a
           # bedtime question.
           "wifi", "wi fi", "wi-fi", "internet", "broadband", "router", "connection",
           "phone signal", "mobile signal", "boiler", "heating", "radiator", "radiators",
           "thermostat", "tap", "taps", "drip", "drips", "dripping", "leak", "leaks", "leaking",
           "fridge", "freezer", "washing machine", "washer", "dishwasher", "tumble dryer",
           "oven", "hob", "cooker", "kettle", "telly", "tv", "television", "printer", "laptop",
           "computer", "bulb", "bulbs", "flicker", "flickering", "flickers", "clicking",
           "clicks", "banging", "bangs", "rattling", "rattles", "humming", "hums"),
    ask=("whats a good", "what is a good", "what's a good", "good", "best", "recommend",
         "suggest", "what should i do", "look like", "help me", "give me")))
