"""Is this line asking the bot to rule on the plan already on the table?

The pools for "is that a good idea" live in `bot/compose/fallback.py` (`_a_verdict_on_their_plan`
builds the reply from them), and the facts behind them in `bot/compose/fallback_data.py`. This
module is the same reading without the reply: the ask on its own, so a caller that is not writing a
verdict can tell that one is being asked for.

The arbiter wants exactly that. `_a_verdict_on_their_plan` also decides whether a verdict is the
right thing to say at all - "is that bad" after somebody's news is not one, and an answer that has
already ruled leaves nothing to add - and the arbiter needs the narrower question: has the person
put a plan down and asked for it to be judged? A hand-back ("I cannot call that one for you") is
not an answer to that, so a card that names the plan takes the turn off it.

It lives here rather than in `fallback.py` because that file is past the size the world will
upload, so nothing there can be changed (see #general, `fallback.py` is over 1 MB).
"""

from .fallback_data import JUDGE_BARE_FACES
from .fallback import JUDGE_ASK, JUDGE_ASK_BARE, _matchable, _the_plan_on_the_table


def asks_for_a_judgement(text, memory=None):
    """True when the line asks the bot to rule on the plan on the table, else False.

    "is that a good idea", "is that stupid", "am i mad to", "sensible?" - the plan is on the table
    from the line before, and the person wants it judged. A bare adjective only counts where a plan
    is already named: "daft" with nothing on the table is not a question about anything.
    """
    clean = " ".join(str(text or "").lower().split())
    try:
        said = _matchable(clean).rstrip(" ?.!,")
        if JUDGE_ASK.match(said):
            return True
        bare = JUDGE_ASK_BARE.match(said)
        if not bare:
            return False
        if not (bare.group("bare_noun") or bare.group("face") in JUDGE_BARE_FACES):
            return False
        return bool(_the_plan_on_the_table(memory or {}))
    except Exception:  # noqa: BLE001 - a reading that fails claims nothing
        return False
