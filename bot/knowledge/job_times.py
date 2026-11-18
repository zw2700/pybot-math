"""How long the everyday jobs in the house take, kept apart from the big home domain.

`bot/knowledge/home.py` is past the publisher's 1 MiB file limit, so a row added to it cannot
ship: this file answers the home job whose length people ask for - a house survey - and declares
the same topic, so it answers exactly what a row in `home.py` would. The row itself is built
from `JOB_TIMES` in `bot/knowledge/costs.py`, beside the prices for the same jobs, and a job's
row is only built where its length is missing from another card: the boiler service already has
its length on main, so it is not in that table.

Being a small separate domain has a second use: a mistake in an import line here loses this row
and nothing else, where a broken import in `home.py` would take the whole house with it
(`domains()` skips a module that fails to import).
"""

from .costs import time_entries

ANSWERS = ("home-and-diy",)

ENTRIES = time_entries("house-survey")
