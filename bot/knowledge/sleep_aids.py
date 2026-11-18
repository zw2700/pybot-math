"""A sleep that depends on a thing in the room is a question about that thing.

People say the aid and the sleep in one line: "i cant fall asleep without the telly on",
"i need the fan on to get to sleep", "i cant sleep, the light is too bright". The chat
module read the first of those as "i can't sleep" and offered the bad-week sympathy pool,
and the answers module had no row that named the telly, the fan or the lamp. This domain
holds the rows, keyed by the aid, the sleep, the dependence and the complaint.

A line that asks about the habit is not the same question: "is it bad to sleep with the tv
on" keeps the older `tv-sleep` card, and "how do i get to sleep without my phone" keeps the
sleep-hygiene advice, because it asks for a way to stop rather than reporting a dependence.
"""
import re

from .lookup import entry

ANSWERS = ("health", "sleep")

SLEEP_AID_SCREENS = ("telly", "phone", "screen", "laptop", "tablet", "ipad", "computer",
                     "monitor")
SLEEP_AID_SOUNDS = ("radio", "podcast", "music", "white noise", "fan", "audiobook")
SLEEP_AID_LIGHTS = ("light", "lights", "lamp", "lamps", "streetlight", "street light",
                    "daylight", "bright")
SLEEP_AID_TELEVISIONS = ("tv", "television", "telly")
SLEEP_AID_SLEEP = ("sleep", "sleeping", "asleep", "fall asleep", "get to sleep", "go to sleep",
                   "bed", "bedtime", "awake", "wake")
SLEEP_AID_DEPENDS = ("without", "with", "unless", "only", "need", "needs", "need it",
                     "have to have", "got to have", "because", "keeps me", "helps me",
                     "is on", "was on", "left on", "loud", "too bright", "too loud")
SLEEP_AID_NOISES = ("noise", "noisy")
SLEEP_AID_OUTSIDE = ("outside", "street", "road", "main road", "outside my window",
                     "outside the window")
SLEEP_AID_WALL = ("next door", "next room", "other room", "another room", "upstairs",
                  "downstairs")
# A machine or a room on the other side of a wall: the sound is the sleep question, whatever is
# making it.
SLEEP_AID_THROUGH_A_WALL = ("washing machine", "dishwasher", "tumble dryer", "hoover", "vacuum",
                            "music", "stereo", "party", "drilling", "diy")
SLEEP_AID_COMPLAINT = ("cant", "can't", "cannot", "can not", "struggle", "struggling",
                       "hard to", "unable", "need", "needs", "needed", "only", "have to",
                       "got to", "keeps me awake", "waking me", "wake me", "better")

SCREEN_REPLY = (
    "It isn't dangerous, but the light and the story keep your brain alert, so you fall asleep "
    "later and wake more in the night. If you need something playing, a podcast or radio set to "
    "a sleep timer is easier on sleep than a screen, and charging the phone across the room "
    "helps too."
)
TELLY_REPLY = (
    "It isn't dangerous, but the light and the story keep your brain alert, so you fall asleep "
    "later and wake more in the night. If you need something playing, a podcast or radio set to "
    "a sleep timer is easier on sleep than a screen."
)
SOUND_REPLY = (
    "A steady sound is easier on sleep than a screen, because there's nothing to watch. Keep the "
    "radio or podcast low and on a sleep timer; if it is a fan or white noise, point it away from "
    "your face. If the noise is a neighbour's, earplugs and a heavy curtain take the edge off."
)
NOISE_REPLY = (
    "If the noise is coming from outside your room, earplugs and a heavy curtain take the edge "
    "off, and a fan or white noise can mask it. If it is a neighbour and it happens often, your "
    "council's noise team can act on it; a short log of the times is what they ask for."
)
LIGHT_REPLY = (
    "Light tells your brain it is still daytime, so keep the room as dark as you can: a blackout "
    "curtain or an eye mask, and turn the lamp off rather than dimming it. If a streetlight gets "
    "in, a curtain that reaches the floor helps."
)
WALL_REPLY = (
    "Sound goes through a wall more than people expect: earplugs and a heavy curtain or a bookcase "
    "against the shared wall take the edge off, and a fan or white noise masks the rest. If it is "
    "the room next door, ask them once at a calm time to turn it down after a set hour; if it keeps "
    "happening, keep a short log of the times and your council's noise team can act on it."
)


def _words(names):
    return re.compile(r"\b(?:%s)\b" % "|".join(re.escape(name) for name in names), re.I)


_A_SCREEN = _words(SLEEP_AID_SCREENS)
_A_SOUND = _words(SLEEP_AID_SOUNDS)
_A_LIGHT = _words(SLEEP_AID_LIGHTS)
_A_TELLY = _words(SLEEP_AID_TELEVISIONS)
_A_SLEEP = _words(SLEEP_AID_SLEEP)
_A_DEPENDS = _words(SLEEP_AID_DEPENDS)
_A_COMPLAINT = _words(SLEEP_AID_COMPLAINT)
_A_NOISE = _words(SLEEP_AID_NOISES)
_A_OUTSIDE = _words(SLEEP_AID_OUTSIDE)
# A thing on the other side of a wall is not the aid in this room: the card for a fan or a
# sleep timer is not an answer about a neighbour's telly or the noise from the street.
_A_SOMEONE_ELSES = _words(("neighbour", "neighbor", "neighbours", "neighbors", "next door",
                           "next room", "other room", "another room", "outside", "upstairs",
                           "downstairs", "people", "someone", "somebody"))
# The room on the other side of a wall or a floor: a telly there is a noise, not the screen in
# their bedroom. "next door" is here too, but "neighbour" is not, because the neighbour card
# already says how to talk to them and is better than this one.
_A_WALL = _words(SLEEP_AID_WALL)
_A_THROUGH_A_WALL = _words(SLEEP_AID_THROUGH_A_WALL)


def a_sleep_that_needs_a_thing(text):
    """True when the line names an aid, the sleep, the dependence and the complaint."""
    said = str(text or "")
    if _A_SOMEONE_ELSES.search(said):
        return False
    return bool((_A_SCREEN.search(said) or _A_SOUND.search(said) or _A_LIGHT.search(said)
                 or _A_TELLY.search(said))
                and _A_SLEEP.search(said) and _A_DEPENDS.search(said)
                and _A_COMPLAINT.search(said))


def a_sleep_broken_by_a_noise(text):
    """True for a sleep broken by a noise from somewhere else, when no aid is in the room."""
    said = str(text or "")
    return bool(_A_SLEEP.search(said) and _A_COMPLAINT.search(said)
                and _A_NOISE.search(said) and _A_OUTSIDE.search(said))


def a_sleep_broken_by_a_thing_next_door(text):
    """True when an aid named with the sleep is on the other side of a wall, not in the room.

    "i cant sleep because the tv is on in the next room" names the telly, the sleep and the
    complaint, but the telly is not theirs to turn off: the answer is about sound through a wall,
    not about the light and the story keeping their own brain alert.
    """
    said = str(text or "")
    return bool((_A_TELLY.search(said) or _A_SCREEN.search(said) or _A_SOUND.search(said)
                 or _A_THROUGH_A_WALL.search(said))
                and _A_SLEEP.search(said) and _A_COMPLAINT.search(said)
                and _A_WALL.search(said))


def which_aid(text):
    """The aid the sleep depends on, or None when the line is not that complaint."""
    if not a_sleep_that_needs_a_thing(text):
        return None
    said = str(text or "")
    if _A_TELLY.search(said):
        return "telly"
    if _A_SCREEN.search(said):
        return "screen"
    if _A_SOUND.search(said):
        return "sound"
    if _A_LIGHT.search(said):
        return "light"
    return None


def answer_for(text, memory):
    """The card for a sleep that depends on a thing, or None for every other line."""
    reading = (memory or {}).get("understood") if isinstance(memory, dict) else None
    said = ""
    if isinstance(reading, dict):
        said = str(reading.get("text") or reading.get("clean") or "")
    aid = which_aid(said or text)
    if aid is None:
        if a_sleep_broken_by_a_thing_next_door(said or text):
            return WALL_REPLY
        if a_sleep_broken_by_a_noise(said or text):
            return NOISE_REPLY
        return None
    return {"telly": TELLY_REPLY, "screen": SCREEN_REPLY, "sound": SOUND_REPLY,
            "light": LIGHT_REPLY}[aid]


def _the_line_itself(understood):
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "")
    return a_sleep_that_needs_a_thing(said)


def _the_noise_line(understood):
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "")
    return a_sleep_broken_by_a_noise(said) and which_aid(said) is None


def _the_wall_line(understood):
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "")
    return a_sleep_broken_by_a_thing_next_door(said)


def _the_telly_line(understood):
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or "")
    # The telly has to be the one in their room: "my neighbours telly is on all night and i cant
    # sleep" is a noise complaint about next door, and the talk-to-them card is the answer.
    return bool(_A_TELLY.search(said) and _A_SLEEP.search(said) and _A_DEPENDS.search(said)
                and _A_COMPLAINT.search(said) and not _A_SOMEONE_ELSES.search(said))


ENTRIES = [
    entry("a-sleep-that-needs-a-screen", (SLEEP_AID_SCREENS, SLEEP_AID_SLEEP, SLEEP_AID_DEPENDS),
          SCREEN_REPLY, ask=SLEEP_AID_COMPLAINT, guard=_the_line_itself),
    entry("a-sleep-that-needs-the-telly", (SLEEP_AID_TELEVISIONS, SLEEP_AID_SLEEP,
                                           SLEEP_AID_DEPENDS),
          TELLY_REPLY, guard=_the_telly_line),
    entry("a-sleep-that-needs-a-sound", (SLEEP_AID_SOUNDS, SLEEP_AID_SLEEP, SLEEP_AID_DEPENDS),
          SOUND_REPLY, ask=SLEEP_AID_COMPLAINT, guard=_the_line_itself),
    entry("a-sleep-that-needs-a-light", (SLEEP_AID_LIGHTS, SLEEP_AID_SLEEP, SLEEP_AID_DEPENDS),
          LIGHT_REPLY, ask=SLEEP_AID_COMPLAINT, guard=_the_line_itself),
    entry("a-sleep-broken-by-a-thing-next-door", (SLEEP_AID_WALL, SLEEP_AID_SLEEP,
                                                   SLEEP_AID_COMPLAINT),
          WALL_REPLY, guard=_the_wall_line),
    entry("a-sleep-broken-by-a-noise", (SLEEP_AID_NOISES, SLEEP_AID_SLEEP,
                                         SLEEP_AID_COMPLAINT, SLEEP_AID_OUTSIDE),
          NOISE_REPLY, guard=_the_noise_line),
]
