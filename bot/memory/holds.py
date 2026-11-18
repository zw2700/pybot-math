"""The earlier turns: one check for "was this said before the line I am answering?".

A loan, not a home. `bot/memory/prior.py` (#12130) is where this check is going for the whole
swarm, and this reading folds onto it the day it lands - so this file keeps the smallest set of
names that reading needs, and it is deliberately called `holds` rather than `earlier` so it does
not take the path another branch is landing the same idea on.

Every memory-based reply asks the same question first - did the chat already hold this, or is
this the first line? - and until now each module answered it for itself, with its own walk over
`memory["turns"]`. The walks drifted: one took `turns[-1]`, another `turns[-3:]`, a third forgot
that a turn may not be a dict, and a fourth read a name out of the store without knowing whether
the line it came from was the one being answered or one from earlier.

So the question has one home. A reply that recalls something asks this module:

    from bot.memory import holds as earlier

    if not earlier.there_is_one(memory):
        return None            # nothing has been said yet: there is nothing to recall
    line = earlier.the_line(memory, MY_PATTERN)     # the earlier line that says it, or ""
    if earlier.says(memory, name):
        ...                    # the name came from the chat, not from this line

The turns here are the turns that came *before* the line being answered: the runtime appends the
current turn after the modules have replied, so `memory["turns"]` is already only the earlier
ones - and this module is the one place that says so, so a module that recalls can stop worrying
about where the current line sits.
"""
import re


def turns(memory):
    """The turns before this one, oldest first, every one a dict."""
    held = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(held, list):
        return []
    return [one for one in held if isinstance(one, dict)]


def there_is_one(memory):
    """Whether the chat has an earlier turn at all.

    A reply that says it remembers something, or says back what the person told it, cannot be
    right on the first line: there is nothing before it to remember.
    """
    return bool(turns(memory))


def lines(memory):
    """What the person said, before this line, oldest first, each one tidied to one line."""
    said = []
    for turn in turns(memory):
        line = " ".join(str(turn.get("user") or "").split())
        if line:
            said.append(line)
    return said


def the_bot_lines(memory):
    """What the bot said before this line, oldest first."""
    said = []
    for turn in turns(memory):
        line = " ".join(str(turn.get("bot") or "").split())
        if line:
            said.append(line)
    return said


def last_reply(memory):
    """The bot's last line, or "" at the start of a chat."""
    held = the_bot_lines(memory)
    return held[-1] if held else ""


def last_module(memory):
    """The module that answered the last line, or "" at the start of a chat."""
    held = turns(memory)
    return str(held[-1].get("module") or "") if held else ""


def recent(memory, n=3):
    """The last `n` turns as text, the person's line and the bot's answer, in order."""
    said = []
    for turn in turns(memory)[-n:]:
        for key in ("user", "bot"):
            part = " ".join(str(turn.get(key) or "").split())
            if part:
                said.append(part)
    return " ".join(said)


def says(memory, word):
    """Whether an earlier line of theirs names this word, as a word."""
    word = str(word or "").strip().lower()
    if not word:
        return False
    pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.I)
    return any(pattern.search(line) for line in lines(memory))


def the_line(memory, pattern):
    """The first earlier line of theirs that matches `pattern`, or "" when none does."""
    for line in lines(memory):
        if pattern.search(line):
            return line
    return ""


def the_last_line(memory, pattern):
    """The most recent earlier line of theirs that matches `pattern`, or ""."""
    for line in reversed(lines(memory)):
        if pattern.search(line):
            return line
    return ""
