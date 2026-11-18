"""A pick asked for again: another film, another book, from the same table.

The answers lane owns this domain. "any other films" and "something else to watch" after a
recommendation are among the commonest follow-ups people send, and each of the mood tables in
bot/knowledge/entertainment.py holds more than the one reply that was given. Nothing new has to
be written down for it: this domain reads the pick already given, and hands over a part of the
same table the chat has not used yet. It is a domain of its own because it leans on the whole
chat (what was recommended, what mood was asked for) rather than on the line alone.

The key names the medium on purpose. A key of bare follow-up words ("anything else", "any other
ideas") would make the understanding engine read every such follow-up as naming a subject of
its own, which breaks follow-up detection for the whole chat: with that key, "its a work laptop
so i cant install much" stopped being a follow-up and lost its answer.
"""
import re

from .entertainment import BOOK_MOODS, FILM_MOODS, GRAVE
from .lookup import entry

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("entertainment", "creative")

PICKS = {"film": FILM_MOODS, "book": BOOK_MOODS}
MEDIUM_WORDS = {
    "film": ("film", "films", "movie", "movies", "watch", "watching", "netflix", "telly",
             "tv", "series", "cinema"),
    "book": ("book", "books", "read", "reading", "novel", "novels", "author", "audiobook"),
}
_TITLED = re.compile(r"\*([^*\n]{2,60})\*")
_MOOD_LEAD = re.compile(r"^for (?:a|an|the)[^:\n]{0,40}:\s*", re.I)
# Which mood to offer next when the chat asked for one: the neighbour a person would take
# after it, so a follow-up to "something funny" is not a film to cry at.
MOOD_NEAR = {
    "funny": ("light", "uplifting", "twist"),
    "light": ("uplifting", "funny", "short"),
    "uplifting": ("light", "funny", "romance"),
    "sad": ("romance", "think", "uplifting"),
    "think": ("twist", "true", "gripping"),
    "gripping": ("twist", "think", "true"),
    "twist": ("gripping", "think", "true"),
    "true": ("think", "gripping", "uplifting"),
    "short": ("light", "funny", "romance"),
    "romance": ("uplifting", "sad", "light"),
    "scary": ("think", "gripping", "twist"),
}
# Named apart from MOOD_ORDER above, which is the table's own order and is used elsewhere.
PICK_ORDER = ("light", "uplifting", "funny", "think", "gripping", "twist", "true", "short",
              "romance", "scary", "sad")
# A follow-up that names a channel or a series is a request the rest of the bot already answers
# well ("any other series" gets three series), so this entry keeps out of its way.
SERIES_SIDE = frozenset("""series sitcom episodes episode netflix iplayer prime tv telly channel
streaming broadcast""".split())


def _titles_in(text):
    """The works a reply names, which it writes between two asterisks."""
    return [one.strip() for one in _TITLED.findall(str(text or ""))]


def _medium_of(text):
    """Which table a line is asking from: "film" or "book", or None."""
    found = set(re.findall(r"[a-z']+", str(text or "").lower()))
    for medium, cues in MEDIUM_WORDS.items():
        if found & set(cues):
            return medium
    return None


def _the_line(understood, memory):
    """The line being answered: the reading carries it, since memory does not hold it yet."""
    if isinstance(understood, dict):
        for key in ("text", "clean", "line"):
            if isinstance(understood.get(key), str) and understood[key].strip():
                return understood[key]
    turns = [one for one in (memory.get("turns") or []) if isinstance(one, dict)]
    return str((turns[-1].get("user") if turns else "") or "")


def _pick_in_play(memory, understood=None):
    """The medium of the pick the last reply gave and the works it named: (medium, named).

    A reply that names fewer than two works is not a pick - it is a question about the one
    work, and a follow-up is about that work, not a list. The medium is the one the follow-up
    itself names first ("any other books" after a film is a book, not the film it came from),
    then the words the reply used ("a series", "by Richard Osman").
    """
    turns = [one for one in (memory.get("turns") or []) if isinstance(one, dict)]
    replies = [str(one.get("bot") or "") for one in turns if one.get("bot")]
    if not replies:
        return None, set()
    last = replies[-1]
    if len(_titles_in(last)) < 2:
        return None, set()
    # Every work the chat has already been given, so a second ask is a second list.
    named = {title.lower() for reply in replies for title in _titles_in(reply)}
    here = _the_line(understood, memory)
    medium = _medium_of(here) or _medium_of(last)
    return medium, named


def _moods_named(text, table):
    """The moods of the table a line names, in table order."""
    words = set(re.findall(r"[a-z']+", str(text or "").lower()))
    return [mood for mood in table if mood in words]


def _other_pick(memory, understood):
    """A second recommendation, from the same table as the pick just given.

    None when the last reply was not a list of picks, which is what keeps the entry off a
    follow-up about something else that happens to mention a film.
    """
    medium, named = _pick_in_play(memory, understood)
    if not medium:
        return None
    turns = [one for one in (memory.get("turns") or []) if isinstance(one, dict)]
    asked = _the_line(understood, memory)
    if set(re.findall(r"[a-z']+", asked.lower())) & SERIES_SIDE:
        return None
    table = PICKS[medium]
    before = [str(one.get("user") or "") for one in turns[:-1]]
    # A mood named lately is the one to keep, so the moods nearest it come first: the last
    # turn outranks the one before it, which outranks the rest of the chat.
    order = []
    for part in (asked, before[-1] if before else "", " ".join(before)):
        for mood in _moods_named(part, table):
            if mood in order:
                continue
            order.append(mood)
            order += [near for near in MOOD_NEAR.get(mood, ()) if near in table]
    order += [mood for mood in PICK_ORDER if mood in table]
    order += [mood for mood in table]
    seen_moods = set()
    listed = {title.lower() for title in named}
    for mood in order:
        if mood in seen_moods:
            continue
        seen_moods.add(mood)
        sentence = table[mood]
        titles = _titles_in(sentence)
        if not titles:
            continue
        if any(title.lower() in listed for title in titles):
            continue
        return "Something different then: " + _MOOD_LEAD.sub("", sentence)
    return None


ENTRIES = [
    # A pick is often asked for again. The follow-up names the medium ("any other films") but
    # no evening, no mood and no work, so the medium is the whole of what it says, and the
    # answer is another part of the table the pick came from. The medium in the key is what
    # keeps this off "anything else", which is a follow-up about whatever the chat was on.
    entry("another-pick",
          (("any other film", "any other films", "any other movie", "any other movies",
            "any other book", "any other books", "any other series",
            "another film", "another movie", "another book",
            "something else to watch", "anything else to watch", "something to watch after",
            "one more film", "one more book"),
           ("film", "films", "movie", "movies", "book", "books", "series", "watch", "read")),
          _other_pick, ask=("other", "another", "else", "more", "after", "next"),
          avoid=GRAVE + ("instead of", "rather than", "how do i", "how can i", "cancel",
                         "stop", "delete", "hide", "cheaper", "free", "where can i")),
]
