"""The baking faults, kept apart from the rest of the cooking cards.

A baking fault is the fault *and* the bake it happened in: a crack in a cheesecake is not a crack
in a macaron, a meringue that weeps is not a pastry that shrinks. `cooking.py` keeps the one entry
(`bake-fault`) that reaches the dispatcher below; the tables live here because that file sits on
the uploader's 1 MiB ceiling, and a card nobody can upload helps nobody.

Nothing changed in the move: the same keys, the same paragraph per bake, and `_same` is the same
loose match the cooking cards use (eggs/egg, meringues/meringue).
"""


def _same(word, wanted):
    """One word matches another loosely: eggs/egg, potatoes/potato, minced/mince."""
    return bool(word) and bool(wanted) and (word == wanted or word.startswith(wanted))


# A baking fault is the fault and the bake it happened in: a crack in a cheesecake is not a crack
# in a macaron, a meringue that weeps is not a pastry that shrinks, and each one has its own cause.
# The entry is one, so a line that names a bake and a fault reaches the one dispatcher below and
# nothing else in the file has to know about it.
_BAKE_THING = ("cheesecake", "cheesecakes", "ganache", "meringue", "meringues", "macaron",
               "macarons", "choux", "profiteroles", "profiterole", "eclairs", "eclair",
               "pastry", "pastry case", "tart", "tarts", "pie crust", "pie shell",
               "brownie", "brownies",
               "cake mixture", "cake batter", "sponge mixture")
_BAKE_FAULT = ("crack", "cracked", "cracks", "cracking", "split", "splits", "curdled", "curdles",
               "curdling", "weeping", "wept", "weeps", "beading", "beads", "shrank", "shrunk",
               "shrinking", "didnt puff", "didn't puff", "did not puff", "didnt rise",
               "didn't rise", "did not rise", "no feet", "hollow", "didnt set", "didn't set",
               "not set", "wont set", "won't set", "sank", "sunken", "watery", "grainy", "gritty",
               # a meringue that went soft, chewy or sticky is the same kind of line as one that
               # weeps, and it reached the gluey-starch answer instead: "my meringue went sticky"
               # was told to drain its rice. The words that name the fault go here, once.
               "soft", "softened", "softening", "went soft", "goes soft", "gone soft",
               "soggy", "sticky", "sticking to", "chewy", "floppy", "limp", "collapsed")


def _bake_fault(memory, understood):
    """Eight baking faults that came back as a shrug, each with its own cause and its own fix."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    said = " ".join(words)

    def has(*wanted):
        return any(_same(word, want) for word in words for want in wanted)

    def says(*phrases):
        return any(phrase in said for phrase in phrases)

    if has("cheesecake", "cheesecakes"):
        if has("grainy", "gritty", "curdled"):
            return ("A grainy cheesecake has curdled: the oven was too hot, or it was beaten too "
                    "long after the eggs went in. Bake it at 150C (130C fan) in a water bath, mix "
                    "only until each thing is just in, and let it cool in the oven with the door "
                    "ajar so it sets slowly. It is still good to eat - a grainy one is a texture, "
                    "not a fault to throw away.")
        if has("watery", "soggy", "set"):
            return ("A watery cheesecake was underbaked or it went into the fridge too soon: it "
                    "needs to set in the oven until only the middle wobbles, then cool in the tin "
                    "an hour before it sees the cold. Bake it in a water bath at 150C (130C fan), "
                    "because the steam is what makes it dense and creamy rather than grainy, and "
                    "drain the tin well before it is chilled.")
        return ("A cheesecake cracks when it is baked too hot or cooled too fast: bake it at 150C "
                "(130C fan) in a water bath, and when only the middle still wobbles turn the oven "
                "off and leave it in there with the door ajar for an hour. A crack is cosmetic - a "
                "cold cheesecake and a spoon of sour cream over the top covers it - and the next "
                "one will not crack if it cools slowly.")
    if has("ganache"):
        return ("A split ganache got too hot, or cold cream went into warm chocolate: warm it "
                "gently over barely simmering water, off the heat, and stir in a tablespoon of warm "
                "milk or cream until it comes back together. Next time pour hot cream over chopped "
                "chocolate, wait a minute, then stir from the middle outwards, and keep every "
                "spoon and bowl dry.")
    if has("meringue", "meringues"):
        weeping = ("A meringue weeps when the sugar was not fully dissolved or it was underbaked: "
                   "rub a little between your fingers and it should feel smooth, not gritty, "
                   "before it goes in. Bake it low and slow, 100C (80C fan) for an hour and a "
                   "half, then leave it in the oven with the door ajar to cool, and make it on a "
                   "dry day.")
        # a weeping, beaded meringue is the sugar, not the storage: "my meringues weeped sticky
        # beads overnight" says both, and the sugar is the cause of the beads
        if has("weeping", "weeped", "weeps", "wept", "beading", "beaded", "beads", "gritty",
               "grainy"):
            return weeping
        if has("soft", "softened", "soggy", "sticky", "chewy", "floppy", "limp", "collapsed"):
            return ("A meringue goes soft when it has not dried out enough, or it was stored where "
                    "the air is damp: bake it at 100C (80C fan) for an hour and a half and lift "
                    "one off the paper to check it comes away clean, then cool it in the oven with "
                    "the door ajar and keep it in an airtight tin - never the fridge, which is "
                    "what makes it collapse. A sticky one wants 15 minutes more at the same heat, "
                    "and a chewy one wants the sugar whisked in more slowly and a longer, slower "
                    "bake.")
        return weeping
    if has("macaron", "macarons"):
        # A cracked shell and a soft or hollow one are different faults with different causes, and
        # two reviewers of this branch said so: "my macarons went soft" was told they crack when
        # the oven is too hot. A soft one is covered first, because a shell that has been filled
        # a day softens on purpose, and that is the commoner reading of the line.
        if has("hollow"):
            # a hollow one is its own fault in a macaron and neither of the other two sentences
            # names it: it is in the shared key words, and the crack answer only had a trailing
            # clause about it.
            return ("A hollow macaron was underbaked, or the whites were whipped too stiff and "
                    "the shell set before the inside could come up: whip to soft to medium peaks, "
                    "fold the batter until it ribbons and settles back in about 20 seconds, and "
                    "bake at 150C (130C fan) for a minute or two longer, resting the shells only "
                    "until a skin forms - much longer than that and they go hollow instead of "
                    "getting feet.")
        if has("soft", "softened", "softening", "soggy", "sticky", "chewy",
               "limp", "floppy", "collapsed", "sank"):
            return ("A macaron that goes soft a day after it is filled is the filling's moisture "
                    "working into the shell, which is what a macaron is meant to do: keep them in "
                    "an airtight box and eat them within two or three days, and take them out of "
                    "the fridge 20 minutes before you do, because cold makes a shell chewy. One "
                    "that comes out of the oven soft was underbaked or the shells were not left "
                    "long enough to form a skin: rest them 30 to 60 minutes until they are dry to "
                    "the touch, then bake at 150C (130C fan) for 2 minutes longer than you did "
                    "and check one at the back of the tray.")
        return ("Macarons crack when the oven is too hot or the piped shells were not rested: tap "
                "the tray, leave them 30 to 60 minutes until a skin forms, then bake at 150C (130C "
                "fan) with the door propped a crack. Fold the batter until it ribbons slowly off "
                "the spatula - overmixed and they spread, undermixed and they crack - and a hollow "
                "one usually wants 5C less and two minutes more.")
    if has("choux", "profiteroles", "profiterole", "eclairs", "eclair"):
        return ("Choux does not puff when the dough is too wet or the oven door is opened: dry the "
                "pan over the heat for a minute once the flour is in, beat in the eggs until it "
                "just falls off the spoon in a V, and keep the door shut for the first 20 minutes "
                "at 200C (180C fan). A wet dough steams instead of setting, and a cool oven lets "
                "it slide.")
    if has("brownie", "brownies"):
        return ("Brownies that will not set are underbaked: 20 to 25 minutes at 180C (160C fan), "
                "until a skewer comes out with a few moist crumbs and no wet batter, then cool "
                "them completely in the tin - an hour in the fridge if you are in a hurry - "
                "because they firm up as they cool. A runny middle is warm butter and sugar, so "
                "give them 5 more minutes rather than more flour.")
    if has("pastry", "tart", "tarts", "pie") or says("pie crust", "pie shell", "pastry case"):
        # Soft or greasy pastry is too much fat or water and warm hands, not shrinkage or dryness:
        # "my pastry is soft" was answered with the shrinking card, which names the wrong fault.
        if has("soft", "softened", "soggy", "sticky", "greasy", "wet", "limp"):
            return ("Soft pastry is too much fat or water, or the fat got warm: use about half the "
                    "weight of butter to flour, cut it in cold until it looks like breadcrumbs, "
                    "and add iced water a spoon at a time until it only just comes together. "
                    "Handle it as little as you can, rest it 20 minutes in the fridge, and roll it "
                    "on a floured surface rather than pressing it - warm butter is what makes it "
                    "limp, so cool the bowl and your hands if the kitchen is hot.")
        # Pastry cracking while it is rolled out is dryness or warmth, not shrinkage, and main's
        # own answer for it is the right one.
        if has("crack", "cracked", "cracks") and not has("shrank", "shrunk", "shrinking"):
            return ""
        return ("Pastry shrinks when the gluten is worked too much or it is stretched into the "
                "tin: rest it 20 minutes in the fridge before rolling, ease it in rather than "
                "pulling it, and let it hang over the edge instead of pressing it up the sides. "
                "Chill the lined tin 15 minutes before it bakes and it will hold its shape.")
    if has("cake mixture", "cake batter", "sponge mixture") or says("cake mixture", "cake batter"):
        return ("A curdled cake mixture is cold eggs going into warm butter too fast, and it comes "
                "back easily: beat in a tablespoon of the weighed flour, and stand the bowl in warm "
                "water for a minute. Next time use eggs at room temperature and add them a little "
                "at a time, beating well after each one, and it will not split.")
    return ""

_BAKE_FAULT_FAMILIES = (
    (("dry", "dried out", "overcooked", "over-cooked", "hard", "tough"),
     "It is nearly always the time in the oven, or flour scooped rather than weighed",
     "take it out 5 minutes before the recipe says, weigh the flour instead of scooping it, and "
     "brush the top with milk or syrup while it is still warm",
     "serve it with custard, cream or a spoon of jam, or crumble it into a trifle"),
    (("crumbly", "crumbs", "crumbles", "falling apart", "fell apart", "sandy", "dry and crumbly"),
     "Too little fat or egg to hold it together, or it was cut while it was still warm",
     "weigh the butter and sugar, add an extra yolk, and leave it 10 minutes in the tin before "
     "turning it out",
     "eat it in a bowl with fruit and cream, or use it as the base of a trifle"),
    (("sank", "sunk", "sunken", "sinking", "sink", "collapsed"),
     "It is underbaked, or the oven door was opened in the first 20 minutes, or there is too much "
     "raising agent in it, and all three make a bake rise fast and then drop",
     "bake it at 180C (160C fan) without opening the door, fill the tin two-thirds full, and "
     "check it with a skewer before it comes out",
     "fill the dip with jam and cream, or serve it warm as a pudding"),
    (("flat", "didnt rise", "didn't rise", "not risen", "no rise"),
     "The baking powder is past its date, the flour was beaten in too hard, or the oven was not "
     "up to heat",
     "use a teaspoon of baking powder to 150g of plain flour, fold the flour in with a spoon, and "
     "let the oven come fully up to heat first",
     "split and fill it, tear it into a trifle, or serve it warm with custard"),
    (("gummy", "clammy", "wet in the middle", "soggy in the middle", "stodgy", "doughy",
      "raw in the middle", "soggy", "wet inside", "squidgy", "not cooked in the middle"),
     "It needed longer, not a hotter oven: the outside set while the middle was still wet, and a "
     "mixture weighed by eye goes in wetter than the recipe meant",
     "give it 5 to 10 more minutes at the same heat with foil over the top, weigh the milk, "
     "butter and flour, and use a skewer in the centre not at the edge",
     "back in the oven at 160C for 10 minutes with foil over the top, or eat it warm as a "
     "pudding with custard"),
    (("pale", "palest", "no colour", "white on top", "pale on top", "blond", "not brown"),
     "It is short of heat or short of sugar: a pale bake was on too low a shelf or the oven was "
     "under its temperature, and a recipe cut down on sugar browns slowly",
     "bake it one shelf up at the heat the recipe says, and check the oven with a thermometer - "
     "an oven that reads 160C when it says 180C gives a pale bake every time",
     "it is still good to eat, and a minute under the grill browns the top of a sponge"),
    (("bicarbonate", "bicarb", "soda", "soapy", "tastes of soap", "tastes of baking soda",
      "tastes of bicarbonate", "chemical taste", "metallic"),
     "There is too much bicarbonate in it, or nothing acid for it to react with, and both leave "
     "that soapy taste behind",
     "use a level teaspoon to 150g of plain flour, keep it for recipes with buttermilk, yoghurt, "
     "lemon or cocoa in them, and use baking powder when nothing in the mix is acid",
     "a soapy taste is not dangerous - a spoon of jam or a glaze covers most of it"),
    (("stuck", "sticking", "sticks", "broke", "broken"),
     "The tin was not greased all over, or it was turned out while it was still hot",
     "grease the tin and cut a strip of baking paper across the base and up two sides, then run a "
     "knife round the edge and wait 10 minutes before turning it out",
     "glue the broken pieces back together with jam or buttercream and nobody will know"),
)


def _bake_always(memory, understood):
    """The cause and the next-time fix for the fault in "everything i bake comes out ..."."""
    said = " ".join(str(word).lower() for word in ((understood or {}).get("words") or []))
    line = str((understood or {}).get("text") or (understood or {}).get("clean") or "").lower()
    both = said + " " + line
    for words, cause, fix, _use in _BAKE_FAULT_FAMILIES:
        if any(word in both for word in words):
            return "%s. Next time: %s." % (cause, fix)
    return ""
