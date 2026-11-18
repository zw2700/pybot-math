"""A bare figure of heat said beside how a person feels.

"its 20 degrees and im freezing" holds two halves: a figure of heat with nothing else around it,
and a person saying how they are. The figure is the weather or the room, and the state is the
person's, so what a friend does is one practical thing and one question about the situation.

The engine already reads the warmth of the person (`understood["warmth"]`), and the composer
already has the pools for a body state - but only for a line that is the state and nothing else
("im cold"). A figure in front of the state is what the two readings disagree about: the knowledge
base reads the figure as a subject ("Water freezes at 0C (32F)", and with a room named "A degree
passes at 40% in most UK universities"), and it still holds the turn because a card that matched a
word outranks the composer's pool. So the reading is done here, before the knowledge base: take the
bare figure out of the line, and ask the composer's own reader whether what is left is a body state.
That is the whole of the rule, and it needs no list of the substances a figure can be about:

* "its 20 degrees and im freezing" -> "and im freezing" -> cold -> the warm pool;
* "im freezing, its 20 degrees" -> "im freezing" -> cold;
* "its 30 degrees and im boiling" -> "and im boiling" -> hot -> the cool pool;
* "its 20 degrees and im hungry" -> hungry;
* but "the office is 20 degrees and im freezing" leaves "the office is and im freezing", and a
  room named is the heating answer's, so this passes;
* "what temperature does water freeze", "my pipes are freezing", "im roasting a chicken at 180
  degrees" and "is 20 degrees cold enough to freeze the pipes" have no state left, or no figure,
  and pass.

The words of the pools are the composer's: this module never writes a reply of its own.
"""
import re

PRIORITY = 1000  # above the knowledge base (0), below loss (2000), grief (2100) and safety (9000)

# The numbers people type for a temperature. The engine spells small numbers out ("its twenty
# degrees"), and a figure written as digits stays as it was typed, so both are read.
_NUMBER = (r"(?:\d+(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
           r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
           r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)")
# The unit is what makes the figure a temperature: a bare number is a price, a time or a count.
_UNIT = r"(?:degrees?|deg\b|°|celsius|centigrade|fahrenheit|c\b|f\b)"
# What a person puts in front of the figure when it is the weather: "its 20 degrees", "its about
# -3", "only 16 degrees". A noun in front of it ("the office is 20 degrees") is not that, so the
# lead holds nothing but these words and the line's own "and"/"outside".
_LEAD = (r"(?:its|it's|its\s+about|about|around|only|just|currently|still|nearly|almost|minus|"
         r"negative|plus|and|but|so|then|is|be)")
FIGURE = re.compile(rf"\b{_NUMBER}\s*{_UNIT}\b", re.I)
# A figure below zero is a temperature even when the unit is left off: "its -3 outside and im
# freezing" is the same line as "its -3 degrees...". Something has to say it is the weather - the
# word "minus", the weather word after it, or a unit - or "we lost 3 outside" would be a
# temperature, so the tail is required when neither of the others is there.
MINUS_FIGURE = re.compile(
    r"(?<![\w-])(?:minus\s+|[-\u2212]\s?)\d+\s*(?:degrees?)?"
    r"(?:\s*(?:outside|out\s+there|out|in\s+here|today|tonight|now))?", re.I)
MINUS_WORD = re.compile(r"(?<!\w)minus\s+\d+", re.I)
FIGURE_WITH_LEAD = re.compile(
    rf"\b(?:(?:{_LEAD})\s+)*{_NUMBER}\s*{_UNIT}\b(?:\s+(?:outside|out\s+there|in\s+here|here|"
    rf"today|tonight|now|outside|already|still))?", re.I)


def a_figure_of_heat(text):
    """True when the line says a temperature: "20 degrees", "20c", "minus three degrees"."""
    line = str(text or "")
    return bool(FIGURE.search(line) or MINUS_WORD.search(line) or MINUS_FIGURE.search(line))


def without_the_figure(text):
    """The line with a bare figure of heat taken out, and the join left tidy.

    Only the figure and the words that introduce it go, so the rest of the line reads as it did:
    "its 20 degrees and im freezing" is "and im freezing", and "im freezing, its 20 degrees" is
    "im freezing,". A figure inside a longer phrase ("at 180 degrees for an hour") is left alone
    by the caller's own reading, because what is left of the line is not a body state.
    """
    line = FIGURE_WITH_LEAD.sub(" ", str(text or ""))
    line = MINUS_FIGURE.sub(" ", line)
    line = re.sub(r"\s+", " ", line)
    # What is left in front of the state when the figure was the whole of the other half: "its
    # -3 outside and im freezing" leaves "its and im freezing", and "its" is the figure's own
    # word rather than the state's.
    line = re.sub(r"^[\s,;:-]*(?:(?:its|it|it's|is|was|there|and|but|so|then|about|around|only|"
                  r"just|still|currently|be)\b[\s,;:-]*)+", "", line.strip())
    line = re.sub(r"[\s,;:-]+$", "", line.strip())
    # The figure's own introducing word can be left behind when the figure was the second half:
    # "im freezing, its -3 outside" is "im freezing," once the figure goes.
    line = re.sub(r"[\s,;:-]+(?:(?:its|it|it's|is|was|there|about|around|only|just|still|"
                  r"currently|and|but|so|then)\b[\s,;:-]*)+$", "", line.strip())
    return line.strip()


def a_state_said_with_a_figure(text):
    """The body state the line says beside a figure ("cold", "hot"), or None.

    The composer's reader is the authority on what counts as a body state, so it is asked about
    the line with the figure taken out. A line with no figure at all is not this module's.
    """
    line = str(text or "")
    if not a_figure_of_heat(line):
        return None
    rest = without_the_figure(line)
    if not rest:
        return None
    # The composer's own reader, imported here so the two modules that share it are loaded in
    # their own order (fallback imports the chain, so the chain is never imported first).
    from ..compose import fallback  # noqa: F401 - loaded for its side of the pair
    from ..compose.fallback_chain import _body_state
    try:
        return _body_state(rest)
    except Exception:  # noqa: BLE001 - a reading that raises claims nothing
        return None


def respond(text, memory):
    """The body state's own pool for a line that says a figure of heat beside it, or None."""
    understood = memory.get("understood") or {}
    clean = understood.get("clean") or text
    state = a_state_said_with_a_figure(clean)
    if not state:
        return None
    from ..compose import fallback  # noqa: F401 - loaded for its side of the pair
    from ..compose.fallback_chain import _choose
    from ..compose.fallback_data import BODY_POOLS
    pool = BODY_POOLS.get(state)
    if not pool:
        return None
    try:
        return _choose(pool, memory, clean)
    except Exception:  # noqa: BLE001 - a pool that raises claims nothing
        return None


def takes_as_it_comes(text, memory):
    """Only on a line that says a figure of heat beside a body state, and nowhere else."""
    understood = memory.get("understood") or {}
    try:
        return bool(a_state_said_with_a_figure(understood.get("clean") or text))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


TAKES_AS_IT_COMES = takes_as_it_comes
