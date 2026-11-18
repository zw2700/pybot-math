"""The glass of a car, which is a question about light and weather, not about damage.

The claim row in `bot/knowledge/cars.py` keys the window itself - "car window", "my car window" -
and the word *car* inside that phrase also counts for the second half of the row's trigger, so one
phrase proved both halves of the match. Every question about a car window landed on the claim
card:

    can you tan through a car window       -> "Nobody was hurt, so this is a report and a claim"
    why do my car windows mist up          -> the same
    how do i stop my car window icing over -> the same

Three rows already answer those lines - the glass, the demister and the scraper - and none of them
got the line. So the row is held off by a reading rather than by a longer key list: a line that
names a car window and says nothing about damage is somebody else's answer.
"""
import re


# A window on a car is a thing people ask about long before it is a damage they report: "can you
# tan through a car window" wants the glass, "why do my car windows mist up" the demister, "how do
# i stop my car window icing over" the scraper. All of those reached the claim card, because the
# row keys "car window" itself and the word "car" inside that phrase also counts for the second
# half of the row's trigger, so one phrase proved both halves. The row is about damage, so a line
# whose window is the subject and which names no damage stands aside for the glass, the misting
# and the frost.
A_WINDOW_ON_A_CAR = re.compile(
    r"\bcar windows?\b|\bwindows? (?:on|of|in) (?:the|my|our|a) car\b", re.I)
# Somebody did it: the word for the person, or the verb only a person does to a car that is not
# theirs. A chip from a stone and a window that will not wind down are neither, and both were sent
# to ring 101 to photograph damage nobody had done.
_SOMEBODY_DID_IT = ("keyed", "keying", "smashed", "smash", "shattered", "knocked off",
                    "knocked out", "broke", "broken into", "break in", "steal", "stolen",
                    "nicked", "damaged", "vandalised", "vandalized", "reversed into", "took it",
                    "taken", "gone", "missing", "someone", "somebody", "thief", "thieves",
                    "burglary", "attempted")
# What the glass itself is asked about: light through it, what is on it, what it does in weather.
_THE_GLASS_ITSELF = ("tan", "tanned", "tanning", "suntan", "sun tan", " uv", " uva", " uvb",
                    "sunlight", "sun ", "sunny", "tint", "tints", "tinted", "tinting", "tint film",
                    "clean", "cleaning", "cleaner", "wash", "washing", "dirty", "smear", "smears",
                    "smudged", "squeak", "squeaky", "mist", "misted", "misting", "misty", "steam",
                    "steamed", "steaming", "steamy", "fog", "foggy", "fogged", "condensation",
                    "demist", "demister", "defrost", "frost", "frosted", "frosty", "frozen",
                    "ice", "iced", "icing", "wiper", "wipers", "reflection", "glare", "blind spot")
# A fault of the glass or of the frame around it is a repair, and the person wants the price, the
# part or the job rather than a crime number: a stone chips a windscreen, a seal perishes, and a
# window that will not wind down has a motor or a switch behind it.
_A_FAULT = _THE_GLASS_ITSELF + (
    "crack", "cracked", "cracks", "chip", "chipped", "chips", "stone chip", "star chip",
    "wont open", "wont close", "wont go", "wont wind", "wont shut", "doesnt open", "doesnt close",
    "does not open", "does not close", "stuck", "sticking", "jammed", "jam", "off its runner",
    "water", "leak", "leaks", "leaking", "letting in", "coming in", "seal", "seals", "rubber",
    "regulator", "switch", "handle", "whistle", "whistling", "noise",
    "rattles", "rattling", "squeaks", "squeaking", "repair", "repairs", "replace", "replacement",
    "how much", "cost", "price", "cheap", "cheapest", "fix")


def _names_one_of(said, parts):
    return any(" %s" % part in " %s" % said for part in parts)


def a_window_on_a_car_is_not_a_damage(understood):
    """False when the line is about the car's glass rather than about damage to it.

    The claim row keys the window itself, so every question about a car window landed on it. Both
    halves of that proof are in the reading, so the reading is where it is undone: a line that
    names a car window and asks about the glass or a fault of it, with nobody in the line doing
    anything, is somebody else's answer. A line that says somebody smashed, keyed or broke into
    the car keeps the claim card, because the person doing it is in the line.
    """
    if not isinstance(understood, dict):
        return True
    said = " ".join(str(part) for part in (
        understood.get("text"), understood.get("clean"), understood.get("raw"),
        " ".join(str(word) for word in (understood.get("words") or ()))) if part).lower()
    if not said.strip() or not A_WINDOW_ON_A_CAR.search(said):
        return True
    if _names_one_of(said, _SOMEBODY_DID_IT):
        return True
    return not _names_one_of(said, _A_FAULT)
