"""The things a line says the person has already tried, so nothing takes one for what they want.

"we tried a bath n a story", "ive tried the plunger", "i tried the cream" - the thing is named
as done with. Every reader that looks for what a line is about finds the tried thing first,
because it is a plain noun in the middle of a sentence, and it is the one word in the line the
person has just said is behind them:

* "we tried a bath n a story" after advice about a toddler who will not sleep was answered with
  a story made up on the spot, which is the thing they had already done at bedtime;
* "ive tried the cream" after advice about a skin problem was answered with macaroni cheese, on
  the word "cream";
* "i tried to bleed the rad but no water came out" was answered with how to bleed a radiator.

So this reads the words of the attempt and publishes them as `tried`: the words are what the
line says is finished, not what it is asking about. A reader that offers a thing on purpose asks
this reading first (`bot/knowledge/entertainment.py`, where the fixed forms - a story, a poem, a
rap, a song - stand down for the form the line says it has already had). Nothing else consults
it yet: the knowledge lookup still reads the line exactly as it did, so the three lines above are
answered as before, and this is the reading to hang those fixes on.

Only a report is read, never a question: "have you tried turning it off and on" is the bot being
asked, and "what should i try" asks for an idea, so neither has anything behind it. And only the
past tense, because "i try to walk every day" is a habit, not a step behind them.

The same line is often a report and an ask at once - "i tried a haiku but it was rubbish can you
do one" - so `asks_for_one_more` says whether the words after the attempt hand the making over
and ask for one more, which is the reading a reader needs before it stands down for a try.
"""
import re

# The words after "tried" that end the attempt: the person has turned to what happened next, or
# to a limit on it. "and" is not one of them, because "a bath and a story" is two things tried,
# while "and it doesnt help" and "and nothing worked" are the next clause.
ENDS_THE_ATTEMPT = frozenset("""
but though although however yet still whereas while because since
""".split())
# A pronoun or a new subject after "tried" starts the next clause: "i tried the cream and it
# stung", "ive tried that but she wont". The words before it are the attempt.
STARTS_A_CLAUSE = frozenset("""
i we it he she they you that this there its im hes shes thatll even though
her him them me us my our
""".split())
# What may follow "and" and still be part of the attempt: two nouns joined ("a bath and a story"),
# as against the next clause ("and it doesnt help", "and now hes worse").
NOT_A_CLAUSE_AFTER_AND = frozenset("""
still now nothing no none neither nor so then he she they it its i we you that this there
everything anything anymore
""".split())
# The words of a report that name no thing tried.
NOT_A_THING = frozenset("""
a an the it them that this those these one ones thing stuff and or but so
already again twice once too also just even really very much more some any all lot lots bit
bits quite rather sort kind my our your his her their of to in on at for with off out up down
not no yeah ok okay well then now since yesterday today tonight morning afternoon evening night
week weeks month months year years hour hours day days time times earlier later sooner
everything anything something nothing anyone someone everyone
about around through over back away before after first last both either
""".split())
# The subject that makes a line the person's own report. "have you tried" and "has he tried" are
# about somebody else, and nothing of theirs is behind them.
REPORT_SUBJECTS = frozenset("""i we ive i've weve we've id wed""".split())
LOOK_BACK = 4


def _tokens(norm):
    out = []
    for word in norm or ():
        if not isinstance(word, str):
            continue
        word = word.strip().lower()
        if word:
            out.append(word)
    return out


def _a_report(words, at):
    """True when the "tried" at `at` is the person's own report of what they did."""
    if at == 0:
        # "tried it, no luck" - the subject is the person, typed out of the line.
        return True
    return any(word in REPORT_SUBJECTS for word in words[max(0, at - LOOK_BACK):at])


# The words a line asks for one more of the thing in, once the try is behind it: "write me
# another", "can you do one", "one more please", "do it again".
ONE_MORE = frozenset("""
another one more again instead
""".split())
# Handing the making over, which is what turns the rest of the line into an ask for the thing.
HANDS_OVER = frozenset("""
write tell make give do sing rap read say come think have got need want
""".split())
# A question opener ends the attempt the way a new clause does: "we tried the rhyme game whats
# another one" asks for one more, and "whats" is not a thing that was tried.
STARTS_A_QUESTION = frozenset("""
what whats which how who where when why can could would shall should whether any anything
""".split())


def _where_the_attempt_ends(words, at):
    """The index of the first word after the thing the "tried" at `at` was done to.

    A hand-over of the making ends it as surely as a new clause does: "we tried a bath n a story
    write me another" is a report and then an ask, and "write" is not a thing that was tried.
    """
    for index in range(at + 1, len(words)):
        word = words[index]
        if word in ENDS_THE_ATTEMPT or word in STARTS_A_CLAUSE:
            return index
        if word == "and" and (index + 1 == len(words)
                              or words[index + 1] in NOT_A_CLAUSE_AFTER_AND):
            return index
        if word in STARTS_A_QUESTION:
            # A question opener starts the ask, but only where it can start a clause: "i tried a
            # can of lager" is a noun, and the word before it is why the two are told apart.
            before = words[index - 1] if index else ""
            if (index == at + 1
                    or before in ("and", "but", "so", "then", "now", "everything", "anything",
                                  "something", "that", "this", "it")
                    or any(other in ONE_MORE for other in words[index + 1:index + 5])):
                return index
        if word in HANDS_OVER and any(other in ONE_MORE
                                      for other in words[index + 1:index + 5]):
            return index
    return len(words)


def the_things_they_tried(norm):
    """The words of the things the line says were tried, in the order said: `["bath", "story"]`.

    Only words that name something are kept: "i tried that" and "ive tried everything" name no
    thing, and a line with nothing to drop hands back an empty list.
    """
    words = _tokens(norm)
    tried = []
    for at, word in enumerate(words):
        if word != "tried" or not _a_report(words, at):
            continue
        for index in range(at + 1, _where_the_attempt_ends(words, at)):
            word = words[index]
            if word in NOT_A_THING or len(word) < 3 or not word.isalpha():
                continue
            if word not in tried:
                tried.append(word)
    return tried


def the_rest_after_the_try(norm):
    """The words left in the line once the thing it says was tried is behind it.

    "i tried a rap but it was rubbish write me another" is a report and an ask in one line, and
    only the report is finished with. This hands back the ask - the words after the attempt -
    so a reader that stood down for the try can see the person asking for one anyway.
    """
    words = _tokens(norm)
    for at, word in enumerate(words):
        if word != "tried" or not _a_report(words, at):
            continue
        return words[_where_the_attempt_ends(words, at):]
    return []


def asks_for_one_more(norm):
    """True when the line, past whatever was tried, asks for one more of it.

    Needs both halves: handing the making over ("write", "do", "can you") and the word for one
    more ("another", "one more", "again", "instead"). A line that only asks what to do about the
    try ("i tried the cream and it stung, what now") asks for nothing more, so the reader that
    offered the tried thing still stands down for it.
    """
    rest = the_rest_after_the_try(norm)
    if not rest:
        return False
    if not any(word in ONE_MORE for word in rest):
        return False
    if any(word in HANDS_OVER for word in rest):
        return True
    joined = " ".join(rest)
    if re.search(r"\b(?:can|could|would|will)\s+(?:you|u)\b", joined):
        return True
    # "whats another one", "which one instead": a question opener and the word for one more is
    # an ask, whether or not a verb of making stands between them.
    if any(word in STARTS_A_QUESTION for word in rest):
        return True
    # "i tried to write a poem and couldnt - can you do it for me" asks for the thing by asking
    # for the maker, without the word "one" or "another" in it.
    if any(word in HANDS_OVER for word in rest) and re.search(r"\bfor (?:me|us)\b|\bplease\b",
                                                             joined):
        return True
    return False


# The most of a line this reading will look at: a long story with "tried" in the middle of it is
# not the report of a step, and its nouns are the story's own.
MOST_WORDS = 24


def things_tried(text, norm=None):
    """`the_things_they_tried` for a typed line, or [] when the line is too long to be a report."""
    words = _tokens(norm) if norm is not None else _tokens(
        re.findall(r"[a-z']+", str(text or "").lower().replace("\u2019", "'")))
    if not words or len(words) > MOST_WORDS or "tried" not in words:
        return []
    return the_things_they_tried(words)
