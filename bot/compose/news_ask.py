"""A line that names the news and nothing else is the ask with the words left out.

"anything in the news", "the headlines", "news about the strike" carry no question mark, so the
asking gate in `bot/compose/fallback.py` dropped them and the line was met with a nod ("I'm
listening - say more if it helps") as though the person had told the bot something, or with the
nothing-much pool's "None that I know of", which claims the bot has looked and found nothing.

What makes a line this ask is its shape, not a list of phrasings: an asking frame, then the news
word, then nothing but where or when it is, or one thing it is about. A line that puts anything
else after the word is about the person's own business and keeps its own answer - "i have news"
is an announcement the nod answers, "news from the hospital" is about someone they know, "no
news yet" is a verdict they have already reached.

This module answers only the lines it is good at and says nothing about any other line.
"""

import re

# An asking frame in front of the news word: any, anything, got, is there, whats, tell me, the.
A_FRAME = re.compile(
    r"^(?:so|and|ok|okay|well|but)?\s*"
    r"(?:any|anything|got|get|is\s+there|are\s+there|whats?|what\s+(?:is|are)|tell\s+me|"
    r"you\s+got|have\s+you\s+got|more|the|some)?\s*"
    r"(?:in\s+the\s+|from\s+the\s+|on\s+the\s+|the\s+)?"
    r"(?:news|headlines?)"
    r"(?:\s+(?:about|on|of|regarding)\s+.*"
    r"|\s+(?:today|tonight|this\s+(?:morning|afternoon|evening)|at\s+the\s+moment|"
    r"right\s+now|please|then)\b.*)?$")

# The news doing something is a report, not an ask: "the news is getting me down", "the headlines
# are grim", "the news was awful".
A_NEWS_DOING = re.compile(
    r"\b(?:news|headlines?)\s+(?:is|are|was|were|has|have|had|gets?|got|makes?|made|keeps?|"
    r"puts?|bothered|upsets?|worries)\b")

# A verdict in front of the word is the person's own: "good news", "no news yet".
A_VERDICT = re.compile(
    r"\b(?:no|some|good|bad|great|awful|sad|terrible|nice|exciting|brilliant|lovely|fantastic|"
    r"amazing|grim|big)\s+(?:news|headlines?)\b")

# Their own news, or someone they know in it: "i have news", "we have news", "my son is in the
# news", "any news about my son".
THEIR_OWN = re.compile(
    r"\b(?:i|we|my|our|his|her|their)\b.*\b(?:news|headlines?)\b|"
    r"\b(?:news|headlines?)\b.*\b(?:my|our|his|her|their)\b")

# A verb of watching or reading makes it a story they told: "i watched the news last night",
# "i made headlines at work today", "did you hear the news".
A_REPORT_VERB = re.compile(
    r"\b(?:watched|watching|read|reading|heard|hear|told|saw|seen|made|missed|followed|"
    r"caught)\b")

# A year is not the day: "any news from 2001".
A_YEAR = re.compile(r"\b(?:19|20)\d\d\b")


def reads_as_an_ask_for_the_news(clean):
    """True when the line asks for the news and says nothing else about it."""
    said = (clean or "").strip().strip(" .!")
    if not A_FRAME.match(said):
        return False
    if A_NEWS_DOING.search(said) or A_VERDICT.search(said) or THEIR_OWN.search(said):
        return False
    if A_REPORT_VERB.search(said) or A_YEAR.search(said):
        return False
    return True
