"""The garden machines that are not a mower: a hedge trimmer, a strimmer, a leaf blower, a
chainsaw.

"can i keep a hedge trimmer in a shed" and "how do i use a hedge trimmer" were answered with the
beard-trimming card - "trim it dry, on a guard a couple of steps longer than the length you
want... take the neckline just above the Adam's apple" - because "trimmer" is in that row's key
and a garden machine is not a face. "how do i store my strimmer" and "how do i use a strimmer"
were the mower's air filter, "how do i sharpen my hedge trimmer" was the razor blade, and
"what is a strimmer", "do i need a leaf blower" and "how do i change the line on a strimmer"
were punts.

These machines share a mower's problems - a small engine, a cutting edge, a winter in a shed -
but not its answers, so they are their own domain with the machine named and the answer picked
from what the line asks: what it is, how it cuts, how it is looked after, how it is put away,
why it will not start, and which one to buy. The mower keeps its own rows in home.py, and the
hedge itself - how often to cut it, when, and what to plant - stays with garden.py.
"""
from bot.knowledge.lookup import entry



ENTRIES = []
# --- the garden machines that are not a mower ----------------------------------------------
# A hedge trimmer, a strimmer, a leaf blower and a chainsaw share a mower's problem - a small
# engine, a cutting edge and a winter in a shed - but they are not the mower's rows: "can i keep a
# hedge trimmer in a shed" was the beard-trimming card, "how do i use a strimmer" and "how do i
# store my strimmer" were the air filter, and "what is a strimmer" was a punt. One row, with the
# machine named, and the answer picked from what the line asks.

_GARDEN_MACHINES = ("hedge trimmer", "hedge trimmers", "hedge cutters", "strimmer", "strimmers",
                    "grass trimmer", "grass trimmers", "leaf blower", "leafblower",
                    "leaf blowers", "chainsaw", "chain saw", "chainsaws", "rotavator",
                    "garden tools", "garden tool", "garden machinery",
                    # the job with no machine named: "how do i cut a hedge", "how do i edge my lawn"
                    "cut a hedge", "cut the hedge", "cut my hedge", "trim a hedge",
                    "trim the hedge", "trim my hedge", "cut hedges", "hedge straight",
                    "edge my lawn", "edge the lawn", "edging a lawn", "lawn edges",
                    "edges of my lawn")
_STORE_IT = ("store", "storing", "stored", "storage", "keep it", "keep my", "keeping", "put away",
             "put it away", "over winter", "for the winter", "winter", "wintering", "winterise",
             "winterize", "shed", "garage", "damp", "rust", "rusty", "away until")
_CARE_IT = ("sharpen", "sharpening", "sharp", "sharper", "blunt", "blades", "blade", "oil",
            "oiling", "clean",
            "cleaning", "care", "look after", "last longer", "maintenance", "servicing",
            "jammed", "stuck", "which oil")
_USE_IT = ("how do i use", "how to use", "how do i cut", "how to cut", "how do i trim",
           "how to trim", "how do i edge", "straight", "technique", "right way", "hold it",
           "cut a hedge", "cut the hedge", "trim a hedge", "trim the hedge", "cut my hedge",
           "trim my hedge", "edge my lawn", "edges", "shape a hedge")
_FUEL_IT = ("wont start", "won t start", "not starting", "not start", "stalls", "stalling",
            "cutting out", "smoking", "smoke", "flooded")
# starting one from cold is its own question: "how do i start a strimmer" was answered with what a
# strimmer is, because none of the asking words above are in a how-to
_START_IT = ("how do i start", "how to start", "how do i get it started", "get it started",
             "start it from cold", "from cold", "cold start", "how do i start it",
             "starting from cold", "choke")
# a blade that tears instead of cutting is a fault, not a care question: "my hedge trimmer is not
# cutting" was answered with what a hedge trimmer is
_NOT_CUTTING = ("not cutting", "wont cut", "won t cut", "doesnt cut", "doesn t cut",
                "not cut", "tears the leaves", "tearing", "chews the", "bites the",
                "not cutting well", "stopped cutting", "not sharp", "judders", "juddering",
                "stops when i", "cuts out when i")
# grass that is wet is the one thing that stops a strimmer working: "can i use a strimmer on wet
# grass" was answered with what a strimmer is
_WET_IT = ("wet grass", "wet lawn", "wet cutting", "damp grass", "in the rain", "when its wet",
           "when it s wet", "after rain", "after the rain", "raining", "early morning dew",
           "dew")
# the spool is its own question: "how do i change the line on a strimmer" was answered with the
# old fuel, because "line" and "change" are words the fuel answer also looks for
_LINE_IT = ("new line", "change the line", "change line", "replace the line", "the line", "spool",
            "keeps snapping", "keeps breaking", "line snapping", "line breaking",
            "line keeps", "line breaks", "line break", "line snapped", "line too short",
            "line not coming out", "wind the line")
# a chain that will not stay on its bar is its own fault: "my chainsaw chain keeps coming off" was
# answered with what a chainsaw is
_CHAIN_OFF = ("chain keeps coming off", "chain coming off", "chain comes off", "chain fell off",
              "chain keeps jumping", "chain jumps off", "chain jumps", "chain falls off",
              "chain keeps coming loose", "chain loose", "chain slipping", "chain slips",
              "chain off the bar", "chain came off")
# a head that will not feed is a spool wound the wrong way, not a definition
_NOT_FEEDING = ("not feeding", "wont feed", "won t feed", "doesnt feed", "doesn t feed",
                "isn t feeding", "stopped feeding", "keeps stopping feeding", "line not feeding",
                "feeding the line", "feed the line", "line wont come out", "line stuck in the head")
# the line cutting into the beds is technique and a guard, and the definition answered it
_CUTS_PLANTS = ("cutting the plants", "cuts the plants", "cut the plants", "cutting my plants",
                "cut my plants", "cutting the flowers", "cuts the flowers", "cut my flowers",
                "cutting the border", "cutting into the border", "cutting the hedge plants",
                "line cuts", "cutting the shrubs", "cut the shrubs")
# a machine that has gone wrong is not asking what a machine is, whatever the fault is
_FAULT_IT = ("keeps coming off", "coming off", "keeps falling", "wont", "won t", "not working",
             "stopped working", "broken", "doesnt work", "doesn t work", "smoking", "smokes",
             "leaks", "leaking", "cuts out", "keeps cutting out", "rattles", "rattling",
             "vibrates", "seized", "seizing", "jammed", "not spinning", "not turning",
             "not feeding", "overheating", "gets hot")
_DEFINITION_IT = ("what is", "whats a", "what s a", "what's a", "what are", "what does",
                  "mean", "means", "definition", "called", "used for", "difference between")


def _the_guard_question(words, line):
    """True for the safety question: what to wear, and how not to cut yourself."""
    if words & {"safety", "protective", "goggles", "glasses", "visor", "chaps", "helmet",
               "defenders", "gloves", "ppE".lower()}:
        return True
    return any(phrase in line for phrase in (
        "safety gear", "safety equipment", "protective gear", "protective equipment",
        "what should i wear", "what do i wear", "cut my fingers", "cutting my fingers",
        "cut my leg", "cutting my leg", "keep catching", "slice my", "kickback", "kick back"))


def _garden_machine(memory, understood):
    """A hedge trimmer, a strimmer, a blower or a chainsaw: what it is, how it cuts, how it keeps."""
    reading = understood if isinstance(understood, dict) else {}
    said = [str(word).lower() for word in (reading.get("words") or [])]
    words = set(said)
    line = " " + " ".join(said) + " "

    def says(phrases):
        return any(" " + phrase + " " in line for phrase in phrases)

    # the words come apart in the tokeniser - "what is a leaf blower" is "leaf" and "blower" -
    # so a machine named in two words is looked for in the line as well as in the words
    hedge = bool(words & {"hedge", "hedges", "hedge trimmer", "hedge trimmers", "hedge cutters",
                          "trimming", "topiary"}) or says(("a hedge", "the hedge", "my hedge",
                                                           "hedges"))
    strimmer = bool(words & {"strimmer", "strimmers", "grass trimmer", "grass trimmers"}) or \
        says(("strimmer", "grass trimmer", "edge my lawn", "edge the lawn", "edging", "lawn edge",
              "lawn edges", "edges of my lawn"))
    # the edging job with no machine named is read by shape: "how do i edge a lawn" and "how do i
    # cut the edge of my lawn" are both strimmer work, and a list of phrases missed both and sent
    # them to the chainsaw
    if (words & {"edge", "edges", "edging"}) and (words & {"lawn", "lawns", "grass", "path",
                                                         "paths", "drive", "driveway",
                                                         "border", "borders", "kerb", "paving"}):
        strimmer = True
    blower = bool(words & {"leaf blower", "leafblower", "leaf blowers"}) or \
        says(("leaf blower", "leafblower", "blow the leaves", "blow leaves", "leaves off"))
    tiller = bool(words & {"rotavator", "rotovator", "rotavating", "rotovating", "tiller",
                           "cultivator"}) or \
        says(("rotavator", "rotovator", "dig over", "break up the soil"))
    saw = bool(words & {"chainsaw", "chain saw", "chainsaws"}) or \
        says(("chainsaw", "chain saw", "fell a tree", "cut a log", "cut logs"))

    if says(_LINE_IT) and (strimmer or not (hedge or blower or saw)):
        return ("Take the spool off the head, wind the new line on in the direction of the arrow on "
                "it, and hook each end through the eyelet on opposite sides so it cuts level. Leave "
                "about 10 to 15cm of line out on each side and let the head spin for a moment "
                "before you cut, because a line wound the wrong way will not feed. If it keeps "
                "snapping, it is usually too long, or the line is old and brittle.")
    if says(_FUEL_IT):
        if strimmer or saw:
            return ("Two-stroke machines are nine times in ten old fuel: the mix goes off in about "
                    "a month, so tip it out, put fresh petrol with the right two-stroke oil in it "
                    "(50:1 on most) and try again with the choke on for two pulls only, or the "
                    "engine floods. Then the spark plug out and dried, the air filter washed, and "
                    "on a strimmer the line trimmed to the right length so it is not grabbing the "
                    "guard.")
        return ("Nine times in ten it is the fuel: petrol goes off in about a month, so drain last "
                "year's half tank and refill. Then the spark plug out and cleaned or replaced, the "
                "air filter shaken out, and the blades checked for a jammed stem or a build-up of "
                "cuttings behind the guard, which drags the motor down and makes it stall.")
    # "how do i keep my hedge trimmer sharp" has the word "keep" in it, which is how a storage
    # question starts and not what it asks: a word that only means putting a machine away wins,
    # and a bare "keep" is read with the rest of the line
    putting_away = says(("store", "storing", "stored", "storage", "put away", "put it away",
                         "over winter", "for the winter", "winter", "wintering", "winterise",
                         "winterize", "shed", "garage", "rust", "rusty", "away until"))
    if says(_STORE_IT) and (putting_away or not says(_CARE_IT)):
        if blower:
            return ("Empty the bag and wipe the inside of the tube, because leaves left in it go "
                    "soggy and rot the housing. Run the tank dry if it is petrol, or charge the "
                    "battery to about half if it is not, and hang it in a dry shed rather than "
                    "standing it on a damp concrete floor.")
        if saw:
            return ("Empty the fuel tank and run it dry, because petrol left in a carburettor over "
                    "winter turns to varnish and that is what turns a spring start into a repair. "
                    "Clean the bar groove, oil the chain, slacken the chain tension so it is not "
                    "stretched over months, and store it with the bar in its cover in a dry shed.")
        if strimmer or hedge:
            return ("Empty the fuel tank and run the engine until it stops, because petrol left in a "
                    "carburettor over winter turns to varnish and that is what makes a spring "
                    "start-up a repair. Wipe the blades or the cutting head clean, oil the blades "
                    "with a rag and a few drops of three-in-one, and put the guard back on. Hang it "
                    "in a dry shed rather than standing it on a concrete floor, and charge a "
                    "battery tool to about half and keep it indoors, since a battery left flat in a "
                    "cold shed does not come back.")
        return ("Store garden machines the same way: fuel out and the engine run dry, blades wiped "
                "and oiled, guards on, and everything up off a damp concrete floor in a dry shed. "
                "Batteries come indoors at about half charge, because the cold is what kills them.")
    if says(_USE_IT):
        if tiller:
            return ("Go over the ground twice, the first pass shallow and slow with the tines just "
                    "breaking the surface and the second deeper, and only when the soil is damp but "
                    "not wet enough to smear. Take it in strips the width of the machine, keep the "
                    "tines clear of stones and roots, and let the soil settle a week or two before "
                    "planting or sowing.")
        if hedge:
            return ("Cut the sides first, bottom to top in a sweep with the blades at about 10 to "
                    "15 degrees to the hedge, then the top flat - working upwards throws the "
                    "cuttings clear instead of back in your face. A string line along the top and "
                    "one down each end is what makes a hedge look straight, and take the top back "
                    "to the same width as the bottom, so light reaches the base.")
        if strimmer:
            return ("Hold the head just off the ground and sweep it side to side from left to right "
                    "with the line hitting the grass at full speed, and work away from anything you "
                    "do not want cut. Edge along a path by walking it with the head turned 90 "
                    "degrees, and tap the line out on the ground rather than pulling it by hand.")
        if blower:
            return ("Work with the wind and from the edges inwards, holding the tube just off the "
                    "ground and using short sweeps rather than full power - and never blow "
                    "cuttings into a drain, a road or a neighbour's garden. Damp leaves want a rake "
                    "first, because a blower only moves them.")
        if saw:
            return ("Start the cut with the saw running at full speed and let the chain do the work, "
                    "keeping the bar out of the dirt and your body to one side of the cut. Cut from "
                    "the top down on a branch, keep the chain oiled and tensioned, and never cut "
                    "above shoulder height or with the tip, which is what causes kickback.")
    if says(_WET_IT) and (words & {"grass", "lawn", "lawns", "cut", "cutting", "strim",
                                 "strimming", "edge", "edging", "mow", "mowing"} or strimmer):
        return ("Wet grass clogs the guard and welts the line, so the head drags and the motor "
                "bogs down; leave it until it is dry and it cuts in half the time. If you have "
                "to, raise the head a notch, take a narrower strip, use the guard and clean the "
                "grass out of the spool housing before it sets. A petrol machine also cuts long "
                "wet grass badly, so a couple of passes at different heights beat one deep one.")
    if says(_NOT_CUTTING):
        if hedge:
            return ("A trimmer bar that tears rather than cuts is blunt, or the blades are loose "
                    "or jammed with sap: clean the bar with white spirit, check the bolts are "
                    "nipped up, and file each blade at the angle it already has. A hedge also "
                    "tears if you are cutting woody growth more than a finger thick, which wants "
                    "loppers or a saw first.")
        if strimmer:
            return ("A line that will not cut is usually too long, too old, or wound the wrong "
                    "way: trim it to about 12cm out of the head, wind it on in the direction of "
                    "the arrow, and if it is brittle, replace it. Check too that the line is not "
                    "welded into a lump in the spool, which happens when the head is held in long "
                    "grass.")
        if saw:
            return ("A chain that will not cut is blunt or too loose: file every tooth on the "
                    "angle marked on it, take the depth gauges down a touch behind the teeth, and "
                    "check the tension cold so it lifts about 3mm off the bar. A dry chain also "
                    "stretches and burns the bar, so keep the oil tank full.")
        return ("Clean the cutting head, check the blade or the line, and look for a jam: a "
                "build-up of cuttings behind the guard drags the motor down, a blunt blade or an "
                "old line tears instead of cutting, and a loose blade judders. Nothing sharp on a "
                "garden machine is worth using blunt, because a dull edge is what makes people "
                "push and slip.")
    if _the_guard_question(words, line):
        if saw:
            return ("Chaps or tough trousers over the legs, a helmet with a visor and ear "
                    "defenders, gloves and boots - and a first-aid kit within reach, because the "
                    "cut that goes wrong is the one on your own leg. Kickback comes from the tip "
                    "of the bar, so keep the tip out of the wood and stand to one side of the cut.")
        if hedge:
            return ("Gloves, eye protection and ear defenders, and the guard back on the blades "
                    "before you start. Keep the lead behind you and over your shoulder rather "
                    "than trailing in front, hold the trimmer with both hands and never reach "
                    "over the hedge to the far side, which is how fingers get between the blades.")
        if strimmer:
            return ("Eye protection, gloves and trousers rather than shorts, because the line "
                    "throws stones as well as grass. The guard stays on, the head stays below "
                    "waist height, and nobody else - child or pet - is in the same part of the "
                    "garden while it spins.")
        return ("Eye protection, gloves, ear defenders and boots, with the guard on and the lead "
                "behind you rather than in front, and nobody else in the garden while it is "
                "running.")
    if says(_START_IT):
        if saw or strimmer:
            return ("Cold start: choke fully out, two or three pulls only - any more and it "
                    "floods - then the choke half in and it should catch. If it fires and dies, "
                    "the mix is stale or the idle is set too low; if it does not fire at all, the "
                    "plug is wet or the air filter is clogged. A hedgetrimmer with a battery or a "
                    "lead has none of that: hold the trigger lock, squeeze, and if it is dead "
                    "check the lead and the breaker.")
        return ("Cold start: choke out, a couple of pulls, then choke half in. If it fires and "
                "dies the fuel is old, and if it does not fire the plug or the air filter is the "
                "next thing to look at.")
    if says(_CARE_IT):
        if hedge:
            return ("Take the blades off with the plug lead pulled or the battery out, clamp them "
                    "in a vice and run a flat file along each blade at the angle it already has, "
                    "about a dozen strokes, then a drop of oil along the bar and a run for a minute "
                    "to spread it. Clean the sap off with a rag and white spirit first, because "
                    "sap is what makes a trimmer bind.")
        if saw:
            return ("File every tooth on the same angle with a round file of the size the chain "
                    "says, two or three strokes each, and take the depth gauges down a touch behind "
                    "them so the teeth can bite. Check the tension cold - it should lift about 3mm "
                    "off the bar - and keep the oil tank full, because a dry chain stretches and "
                    "then breaks.")
        return ("Clean the cutting head and the air intake of grass and sap, oil the moving parts "
                "with a few drops, and check the blade or the line: a strimmer line that is too "
                "long drags the motor down and a blunt blade tears rather than cuts. A chain wants "
                "its tension checked every use and a file across the teeth every few tanks.")
    if says(("should i buy", "which one", "worth it", "to buy", "buy", "buying", "worth buying",
              "best one", "best to get", "should i get", "what should i get", "do i need",
              "need a", "or a", "instead of",
              "which is better", "recommend", "recommendation", "petrol or", "battery or",
              "corded or", "mains or")) or (words & {"which"}):
        if hedge:
            return ("Get a corded trimmer for one hedge under about 10 metres and a battery one if "
                    "the garden has no outdoor socket or the hedge is longer, because a cable "
                    "overhead is the thing that makes people put it off. Petrol only for a hedge "
                    "over about 2 metres or a long run of it.")
        if strimmer:
            return ("A mains strimmer is the cheapest and lightest for a small lawn, battery for "
                    "anything over about 50 metres of edge or where there is no outdoor socket, "
                    "and petrol only for rough ground and long sessions. A bump-feed head is worth "
                    "more than extra power for ordinary garden edging.")
        if blower:
            return ("You need one if leaves sit on gravel, decking or a lawn you want tidy, and you "
                    "do not if the garden is small enough to rake in ten minutes. A battery blower "
                    "is quieter and enough for a suburban garden; petrol only for a big garden and "
                    "a lot of leaves at once.")
        if saw:
            return ("A battery saw is enough for logs and a fallen branch up to about 20cm and is "
                    "the one most people use; petrol only for a lot of timber and a whole "
                    "afternoon of cutting. Get one with a chain brake whatever else you choose.")
        return ("Match the tool to the job and the size: mains for a small garden and a short run, "
                "battery where there is no outdoor socket or the run is long, and petrol only for "
                "a big garden where the noise and the fuel are worth it.")
    if says(_CHAIN_OFF) and (saw or words & {"chain", "chainsaw", "chain saw"}):
        return ("A chain that keeps coming off is loose tension or a worn drive sprocket: check "
                "the two bar nuts are nipped up, set the tension cold so the chain lifts only "
                "about 3mm off the bar, then turn the bar over and look at the nose sprocket, "
                "because a worn one lets the chain climb out of the groove. If it still jumps the "
                "chain is stretched or the sprocket is hooked, and either will wear the bar out if "
                "you keep cutting with it.")
    if says(_NOT_FEEDING):
        return ("A head that will not feed is usually wound the wrong way or the line has welded "
                "into one lump: take the spool off, pull all the line out, rewind it in the "
                "direction of the arrow moulded on the spool and leave about 10 to 15cm out on "
                "each side. Old line goes brittle and fuses when it is held in long grass, so cut "
                "off the fused part and rewind the rest, or fit new line of the thickness the head "
                "says.")
    if says(_CUTS_PLANTS) or (strimmer and says(("cutting the", "cuts the")) and
                              words & {"plants", "flowers", "shrubs", "border", "borders", "beds"}):
        return ("Keep the line off the beds by cutting the edge in two passes: the first with the "
                "head tilted so the line works the grass and not the soil, sweeping away from the "
                "border rather than along it. A line about 10cm long throws less than a long one, "
                "and a plant guard or a board stood along the edge catches what still flicks over; "
                "string a line between two canes where you cannot see the boundary.")
    if says(_FAULT_IT) and not says(_DEFINITION_IT):
        return ("Treat it as three things in order: is it getting fuel and spark, is the cutting "
                "edge free, is anything loose. Tip out old petrol before anything else, dry or "
                "change the plug, wash the air filter, then take the guard off and clear the "
                "cuttings and grass packed behind it, which is what makes a head drag and a motor "
                "bog down. Check every nut, bolt and the bar or blade mounting for slack, because a "
                "machine that rattles is one that is about to throw something.")
    named = []
    if strimmer:
        named.append("A strimmer cuts grass and edges of a lawn with a nylon line on a spinning "
                     "head")
    if hedge:
        named.append("a hedge trimmer is a bar of blades for the flat sides and top of a hedge")
    if blower:
        named.append("a leaf blower is a fan in a tube that shifts leaves off gravel, decking and "
                     "grass")
    if saw:
        named.append("a chainsaw is a loop of chain on a bar, for timber only")
    if tiller:
        named.append("a rotavator is a small engine turning a row of curved tines to break up and "
                     "mix soil before planting")
    if named:
        first = named[0]
        rest = named[1:]
        said_them = "" if not rest else " The others in the shed: " + "; ".join(rest) + "."
        warning = (" It is not a hedge tool - it chews small growth instead of cutting it "
                   "clean, and it kicks.") if saw else ""
        return first[0].upper() + first[1:] + "." + said_them + warning
    return ("A strimmer cuts grass and edges of a lawn with a nylon line on a spinning head, a "
            "hedge trimmer is a bar of blades for the flat sides and top of a hedge, a leaf blower "
            "is a fan in a tube, and a chainsaw is a loop of chain on a bar for timber. The "
            "strimmer is for grass, the trimmer for a hedge's shape, and the chainsaw only for "
            "wood - not for a hedge, where it chews the growth instead of cutting it clean.")


ENTRIES.append(entry(
    "garden-machine",
    (_GARDEN_MACHINES,
     ("how do i", "how to", "what is", "whats", "what's", "what does", "used for", "mean",
      "cut a hedge", "cut the hedge", "cut my hedge", "trim a hedge", "trim the hedge",
      "trim my hedge", "edge my lawn", "edge the lawn", "edging", "garden tools",
      "called", "store", "storing", "storage", "keep", "put away", "winter", "shed", "garage",
      "rust", "sharpen", "blade", "blunt", "oil", "clean", "care", "look after", "maintenance",
      "wont start", "won t start", "not starting", "stalls", "cut", "trim", "edge", "use",
      "spool", "line", "change the line",
      # a statement about the line rather than a question scored too low to be read: "my strimmer
      # line keeps snapping" was a reflection, because "line" on its own is a common word
      "snapping", "snapped", "snaps", "keeps breaking", "keeps snapping", "too short",
      "not cutting", "wont cut", "won t cut", "tears", "jammed", "wet grass", "wet lawn",
      "damp grass", "raining", "in the rain", "choke", "from cold", "to buy", "buy", "best",
      "straight", "line", "spool", "should i buy", "which", "worth it", "do i need")),
    _garden_machine,
    # a repair-or-replace decision, a price, a fault the shop fixes, and the hedge itself - how
    # often to cut it, when, and what to plant - are all other rows' lines
    avoid=("worth repairing", "repair or replace", "repair it or", "or replace", "scrap",
           "cheapest", "price", "cost", "review", "recommend", "how often", "how short",
           "best time", "when should i cut", "when to cut", "birds", "nesting", "moss", "weed",
           "weeds", "new lawn", "seed", "turf", "leaf mould", "compost", "what to plant",
           "which hedge", "fast growing", "privacy", "beard", "hair", "nose", "ear",
           "kitchen", "knife", "bread", "cheese", "tile", "metal", "pipe", "tree surgeon"),
    bias=3))

# The mower's own storage question: "how do i store my lawnmower" and "where do i keep my
# lawnmower in winter" were answered with the air filter - the right part for a mower that runs
# badly, and not an answer to putting it away. The mower's faults stay home.py's (the fuel, the
# blade, the filter, the oil); only the putting away is here.
_MOWER_PUT_AWAY = (
    "Run the tank dry, or fill it right up with a fuel stabiliser in it - a half-full tank of last "
    "autumn's petrol is what makes a spring start-up a repair. Then change the oil while the "
    "engine is still warm so the dirt comes out with it, scrape the grass from under the deck and "
    "oil the blade. Keep it in a dry shed or a garage on a shelf or a pallet rather than on a "
    "concrete floor, which holds damp and rusts the deck from underneath, and take the battery off "
    "and charge it once a month if it has one.")

ENTRIES.append(entry(
    "mower-put-away",
    (("lawnmower", "lawn mower", "lawnmowers", "mower", "mowers", "hover mower", "ride on mower"),
     ("store", "storing", "stored", "storage", "put away", "put it away", "over winter",
      "for the winter", "winter", "winterise", "winterize", "wintering", "keep it", "keep my",
      "where do i keep", "shed", "garage", "away until", "before winter")),
    _MOWER_PUT_AWAY,
    # a fault, a service and a blade are the mower's own rows in home.py, and a shop question is
    # a buying decision: this row only answers "where does it go for the winter"
    avoid=("filter", "air filter", "oil", "oil change", "spark plug", "blade", "sharpen",
           "sharp", "blunt", "wont start", "won t start", "not starting", "starts then",
           "service", "servicing", "clean", "cleaning", "broken", "repair", "replace", "buy",
           "cheapest", "best", "which", "worth"),
    bias=6))
