"""Answer only quantitative narratives understood by an exact arithmetic skill."""
from ..math import solve

PRIORITY = 8500


def respond(text, memory):
    return solve(text)


def TAKES_AS_IT_COMES(text, memory):
    # The arbiter consults this only for a proposed reply. A solved word problem
    # should keep its arithmetic answer even when its story mentions a chat topic.
    return solve(text) is not None
