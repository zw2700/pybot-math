"""Answer only quantitative narratives understood by an exact arithmetic skill."""
from ..math import solve

PRIORITY = 8500


def respond(text, memory):
    return solve(text)


def TAKES_AS_IT_COMES(text, memory):
    # The arbiter consults this only for a proposed reply. A solved word problem
    # should keep its arithmetic answer even when its story mentions a chat topic.
    return solve(text) is not None


def CLAIMS_INSTEAD(text, memory):
    # A generic price/advice card may pass the arbiter's answer-shape filter
    # even when a calculation already answered this quantitative narrative.
    # Use the same conservative gate as the proposal, below the safety band.
    return TAKES_AS_IT_COMES(text, memory)
