"""Trades: getting a plumber, an electrician or a locksmith to come out.

The answers lane owns this domain. The row is here rather than in `home.py` for the reason
`land.py` gives: `home.py` is what every property line already reaches, and this question -
when a trade comes and what they charge - is a service question, not a thing about the house.

The composer's hand-off to a trade ("a plumber or electrician will spot it in minutes") is
written for a line with something broken in it. This row answers first for the lines that ask
how to get hold of one, so the hand-off is only reached by a line that names a fault.
"""
from .lookup import entry

ANSWERS = ("home-and-diy", "money")

# A plumber at the weekend is a booking question, not a fault: "how do i get a plumber at the
# weekend" met the composer's hand-off ("a plumber or electrician will spot it in minutes"),
# which is written for a line with something broken in it. The trade's own question is when they
# come and what it costs, so this row answers that, and the fallback stands the hand-off down for
# the same lines (bot/compose/fallback.py, `_asks_to_find_one`).
ENTRIES = [entry(
    "trades-out-of-hours",
    (("plumber", "plumbers", "electrician", "electricians", "gas engineer", "gas man",
      "heating engineer", "boiler engineer", "handyman", "locksmith", "roofer", "joiner",
      "drain man", "drainage"),
     ("get", "getting", "find", "finding", "book", "booking", "hire", "hiring", "recommend",
      "recommendation", "weekend", "weekends", "saturday", "sundays", "sunday", "evening",
      "evenings", "tonight", "night", "bank holiday", "out of hours", "emergency", "call out",
      "callout", "near me", "same day", "today")),
    "Book early and ask two questions: the call-out charge and the hourly rate after the first "
    "hour, because a weekend call-out is usually about double the weekday one and the quote over "
    "the phone is what holds them to it. Ring three local firms from eight in the morning and "
    "say what is wrong and when you need someone; the one who can tell you what it probably is "
    "on the phone is the one to book. Anything with water coming through is worth a call "
    "straight away - turn the stopcock off first - and a smell of gas is the free 24-hour gas "
    "emergency line, 0800 111 999, not a plumber.",
    avoid=("fix", "mend", "repair", "unblock", "bleed", "install", "fit it", "myself", "my own",
           "how do i change", "quote", "cost", "charge", "how much", "salary", "training",
           "become a plumber", "become an electrician", "course", "apprenticeship", "what is",
           "what does a", "difference between", "wire a", "socket", "fuse box", "boiler is",
           "boiler makes", "boiler noise", "pressure", "radiator", "leak"))]
