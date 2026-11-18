"""A move is news, but it is not good news: the bot asks about it instead of cheering it.

`im moving out next month` was answered "That's lovely news - and something to look forward to. How
are the plans going?" (`NEWS_TO_COME`, reached through `goodnews.reads_as_news_to_come`, which only
asks whether the thing is ahead). People move out after a breakup, an eviction or a rent rise at
least as often as into their first flat, and the reader who is being evicted gets congratulated. The
move is the one thing ahead that a friend never cheers blind: they ask where to and how the person
feels about it.

What is here:

- `reads_as_a_move` - a move said as a thing ahead or just done, without a word that makes it good
  ("into our first flat", "finally", "we got the keys") and without the lines that are their own
  kind of news ("moving in with my girlfriend" is a step; "moving abroad" is a plan with a job in
  it). It also stands aside for a line that is clearly not glad (`_AHEAD_BAD`, and the mortal
  `goodnews` guards) because those keep the reading they already have.
- `reply_for` - the pool that asks, with the two halves of it named ("are you glad to be going, or
  is it just what has to happen"), so either reader gets an answer that fits.

The good reason keeps the congratulations: `we are moving into our first flat in june` is a thing to
look forward to and is answered by the card for it, and this module never takes a line another
module reads better (`greeting` only reaches here when nothing else answered).
"""
import re

from . import fallback
from . import goodnews

# The move itself: out, house, flat, home, in with somebody, back to a parent's. "moving on" and
# "moving forward" are not a move; "moving in with" is.
A_MOVE = re.compile(
    r"\b(?:i|we|they|he|she|im|i'm|we're|were|were)\s*(?:'m|'re|am|are|is)?\s*"
    r"(?:just\s+|finally\s+|now\s+|soon\s+|actually\s+|been\s+|have\s+|had\s+)?"
    r"mov(?:e|ed|ing)\s+"
    r"(?:out|houses?|household|flats?|home|abroad|in\b|into\b|back\s+(?:in\s+)?with|away)",
    re.I)
# The same said the other way round ("the move is next month", "we have a move coming up").
A_MOVE_NOUN = re.compile(
    r"\b(?:our|my|the)\s+move\s+(?:is|to|next|soon|coming|happens|happening)\b", re.I)
# A reason to be glad: the flat is theirs, it is finally happening, somebody is waiting for them.
GLAD = re.compile(
    r"\b(?:first\s+(?:flat|house|home|place)|our\s+own\s+(?:flat|house|place)|"
    r"dream|finally|cant\s+wait|can'?t\s+wait|so\s+excited|excited\s+to|looking\s+forward|"
    r"got\s+the\s+keys|we\s+got\s+it|brand\s+new|bigger|nicer|better\s+place|closer\s+to|"
    r"new\s+job|promotion|girlfriend|boyfriend|partner|fiance|fiancee|husband|wife)\b", re.I)
# Not glad: the move is somebody else's idea, or it is a loss.
NOT_GLAD = re.compile(
    r"\b(?:evict\w*|kicked\s+out|thrown\s+out|have\s+to|havent\s+got\s+a\s+choice|"
    r"no\s+choice|break\s*up|broke\s+up|divorce|separat\w*|lost\s+my\s+job|rent\s+(?:rise|went\s+up)|"
    r"dreading|cant\s+afford|can'?t\s+afford|sad|gutted|hate|awful|nightmare|"
    r"landlord|selling\s+up|sold\s+the\s+(?:flat|house)|for\s+work|because\s+of\s+work)\b", re.I)
# A question about moving is a question: "should i move out" wants the decision, not "where to".
ADVICE = re.compile(
    r"\b(?:should\s+(?:i|we)|shall\s+(?:i|we)|do\s+you\s+think|is\s+it\s+worth|"
    r"how\s+do\s+(?:i|we)|what\s+should|any\s+(?:advice|tips))\b", re.I)
# A move that is its own kind of news, with a question of its own somewhere else ("moving abroad"
# is the job and the visa, "moving in with my girlfriend" is the step).
ITS_OWN_NEWS = re.compile(
    r"\b(?:abroad|overseas|another\s+country|to\s+(?:spain|france|australia|canada|america|"
    r"portugal|italy|germany|ireland|scotland|wales)|"
    r"(?:in|into)\s+with\s+(?:my|her|his|our)\s+(?:girlfriend|boyfriend|partner|fiance|fiancee|"
    r"husband|wife|mum|mother|dad|father|parents))\b", re.I)

MANY = (
    "Big thing to have ahead of you. Where to, and are you glad to be going?",
    "That's a big change. Is it a move you wanted, or one that has to happen?",
    "Moving is a lot of work. Where are you off to, and how are you feeling about it?",
    "A move is never just a move. Where to, and is it a good thing for you?",
)


def reads_as_a_move(text):
    """True when the line is a move said without saying it is a glad one.

    The guards are the ones this reading needs to stay out of the way: a reason to be glad takes the
    line (the news-to-come pool and the card for a first flat both answer it better than a question
    that asks whether they are glad), and so does a line that is plainly not glad - those readers
    are already answered by the pools for a bad week, and asking "are you glad to be going" of
    somebody being evicted is the failure this module exists to prevent, said backwards.
    """
    clean = " ".join(str(text or "").lower().split())
    if not clean or "?" in clean:
        return False
    if not (A_MOVE.search(clean) or A_MOVE_NOUN.search(clean)):
        return False
    if GLAD.search(clean) or ITS_OWN_NEWS.search(clean):
        return False
    if NOT_GLAD.search(clean) or ADVICE.search(clean):
        return False
    return True


def reads_as_a_move_cheered(text):
    """The move the composer would have congratulated: the reading, and the pool behind the fault.

    A move said ahead is read as news to come by `goodnews.reads_as_news_to_come`, and that is what
    reached the pool which looks forward ("That's lovely news - and something to look forward to")
    at a person who may be leaving a marriage. Only that line is taken here: a move the composer
    files ("Noted: you move house on the 20th") keeps its filing, because the date is the thing to
    remember and a question about it loses the date; and a move already behind the person ("i moved
    house last september") is not ahead at all, so it never enters the reading.
    """
    clean = " ".join(str(text or "").lower().split())
    if not reads_as_a_move(clean):
        return False
    try:
        return bool(goodnews.ahead_of_now(clean))
    except Exception:  # noqa: BLE001 - a reading that fails claims no turn
        return False


def reply_for(text, memory=None):
    """One of the pool's lines for a move, or None when the line is something else."""
    if not reads_as_a_move_cheered(text):
        return None
    try:
        return fallback._choose(MANY, memory or {}, " ".join(str(text or "").lower().split()))
    except Exception:  # noqa: BLE001 - no line is better than a crash
        return None
