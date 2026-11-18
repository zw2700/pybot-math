"""How an everyday thing works: the mechanism, said in one short card.

`explains.py` owns this question and its asking words, and these eight subjects had no row in
it, so the line fell through to the composer and came back as something else entirely:

    how does a hearing aid work        "Nothing of it reached me here, so tell me: how did it go?"
    how does a pacemaker work          the same card again
    how does a septic tank work        the same card again
    how does a sail work               "I wasn't there, so you're the one who knows"
    what is a spinning class           "I'm not sure about that one, sorry"
    what does cruise control do        "I don't know enough to answer that honestly"
    what is decaf coffee               "That's beyond what I know well, sorry"
    how does an induction hob work     the instructions for cleaning a hob

That last one is the worst of them: the hob's cleaning row keys the word "hob", so a person
asking how induction heats a pan was told to wipe it with hot soapy water. Each row here needs
the thing *and* the ask for its mechanism, so "how much does a hearing aid cost", "my septic
tank smells" and "how do i clean an induction hob" keep the answers they had.

A separate file rather than rows inside `explains.py` because that file is over 2,000 lines and
a new domain registers itself.
"""

# The asking words, as `explains.py` uses them: one has to be in the line beside the subject,
# so "i need a new hearing aid" is not a request to explain one. A bare "how" is deliberately
# not here - it is in every how-to, and "how do i clean an induction hob" is a cleaning line.
MECHANISM = (
    "work", "works", "working", "explain", "explains", "explained", "what is", "what are",
    "what's", "whats", "what does", "what do", "inside", "mean", "means", "actually",
    # "how does a radiator heat a room" is the same ask as "how does it work", and the third
    # person takes no "i", so a how-to cannot say it
    "how does", "how do they", "how do these", "how do those",
)

# Two signals are needed: the thing, and one of the asking words above. This is the second gate
# on top of that, and it is the one that keeps a fault line away from the mechanism: a person
# whose pacemaker is bleeping wants the clinic, not a diagram.
TROUBLE = (
    "not", "isnt", "isn't", "doesnt", "doesn't", "wont", "won't", "broken", "broke", "fault",
    "faulty", "error", "fix", "repair", "replacement", "replace", "leaking", "leak", "smell",
    "smells", "smelly", "noise", "noisy", "beep", "beeping", "stopped", "stopping", "help",
    "problem", "problem with", "wrong", "dead", "charge", "charging", "battery", "cost", "costs",
    "price", "much", "cheap", "cheapest", "buy", "buying", "best", "better", "worth", "review",
    "recommend", "deals",
)

from bot.knowledge.lookup import entry

ANSWERS = ("technology", "home-and-diy", "health", "food-and-drink", "sport")

A_HEARING_AID = (
    "A hearing aid is a microphone, an amplifier and a tiny speaker in your ear: the "
    "microphone picks up the room, the electronics boost the frequencies speech lives in and "
    "the speaker sends it down the canal louder. Digital ones split the sound into bands and "
    "turn down the background to suit the room. It does not give you normal hearing back, so "
    "it takes a few weeks of wearing it all day to stop noticing it. NHS aids are free."
)
A_PACEMAKER = (
    "A pacemaker is a matchbox-sized unit under the collarbone with one or two thin leads into "
    "the heart: it watches the beat and sends a small electrical pulse when it goes too slow or "
    "skips, so the heart keeps a steady 60 or so. Fitting one takes about an hour under a local "
    "anaesthetic, the battery lasts 8 to 12 years and is swapped with the whole unit, and a "
    "yearly check reads it through the skin."
)
A_SEPTIC_TANK = (
    "A septic tank is an underground tank for a house with no mains sewer: waste flows in, the "
    "solids sink and settle, bacteria break them down, and the clearer liquid runs out through "
    "pipes into a soakaway in the ground. Nothing goes in it but pee, poo and paper - wipes, fat "
    "and bleach are what kill the bacteria - and a tanker has to empty it every year or two. A "
    "blocked or smelly one is usually a soakaway that has had its chips."
)
A_SPIN_CLASS = (
    "A spinning class is indoor cycling on a fixed bike for about 45 minutes to music: the "
    "instructor calls out when to stand, sprint or add resistance, and you turn the resistance "
    "knob yourself, so the effort is as hard as you make it. Set the saddle to hip height, take "
    "a towel and water, and start with the resistance light enough that you could still talk."
)
A_SAIL = (
    "A sail works like a wing stood on end: the wind crossing the curved side travels further and "
    "faster than the wind on the other side, the pressure drops, and the sail is pulled forward. "
    "That is why a boat can head towards the wind but not straight into it - you work about 45 "
    "degrees off it and zigzag, turning through the wind to gain ground, which is tacking."
)
CRUISE_CONTROL = (
    "Cruise control holds the speed you set by working the throttle for you: get to the speed, "
    "press set, and the car holds it until you touch the brake or clutch, which cancels it. Use "
    "it on a motorway in dry weather, never in rain, traffic or on bends, because it will not "
    "slow for anything ahead - only the adaptive kind follows the car in front."
)
DECAF = (
    "Decaf is ordinary coffee with the caffeine taken out of the beans before roasting, usually "
    "by soaking them in water, a solvent or carbon dioxide: a mug has 2 to 15mg against about "
    "95mg in regular coffee, and the taste and antioxidants are much the same. It is the swap to "
    "make if caffeine is costing you sleep, without losing the ritual or the afternoon mug."
)
AN_INDUCTION_HOB = (
    "An induction hob makes the pan the heater: a coil under the glass sends a fast-changing "
    "magnetic field into the base, which sets up currents in the metal and heats it directly, so "
    "the glass around it stays cool enough to touch. It is quicker and more controllable than "
    "gas, and the pan must be magnetic - if a magnet sticks to its base, it will work."
)

ENTRIES = [
    entry("how-a-hearing-aid-works",
          (("hearing aid", "hearing aids", "a hearing aid", "hearing aids work"),
           MECHANISM),
          A_HEARING_AID, avoid=TROUBLE, ask=MECHANISM, bias=1),
    entry("how-a-pacemaker-works",
          (("pacemaker", "pacemakers", "a pacemaker", "heart pacemaker"),
           MECHANISM),
          A_PACEMAKER, avoid=TROUBLE, ask=MECHANISM, bias=1),
    entry("how-a-septic-tank-works",
          (("septic tank", "septic tanks", "a septic tank", "cesspit", "cess pool"),
           MECHANISM),
          A_SEPTIC_TANK, avoid=TROUBLE, ask=MECHANISM, bias=1),
    entry("what-a-spinning-class-is",
          (("spinning class", "spinning classes", "spin class", "spin classes",
            "spinning session", "indoor cycling class"),
           MECHANISM),
          A_SPIN_CLASS, avoid=TROUBLE, ask=MECHANISM, bias=1),
    entry("how-a-sail-works",
          (("how a sail works", "how sails work", "how sailing works", "a sail works",
            "how does a sail work", "how do sails work", "how does sailing work",
            "sail work", "sails work"),
           ("sail", "sails", "sailing", "sailboat", "yacht", "boat")),
          # "sailed" is deliberately not here: the matcher reads it as another form of "sail",
          # so it fenced the subject word itself and the row never fired for any line
          A_SAIL, avoid=TROUBLE + ("holiday", "holidays", "cruise", "ferry", "set sail",
                                   "sail away", "sail to", "sailing holiday"),
          ask=MECHANISM, bias=1),
    entry("what-cruise-control-does",
          (("cruise control", "adaptive cruise control", "speed limiter"),
           MECHANISM),
          CRUISE_CONTROL, avoid=TROUBLE, ask=MECHANISM, bias=1),
    entry("what-decaf-coffee-is",
          (("decaf", "decaffeinated", "decaf coffee", "decaf coffee work"),
           MECHANISM),
          DECAF, avoid=TROUBLE, ask=MECHANISM, bias=1),
    entry("how-an-induction-hob-works",
          (("induction hob", "induction hobs", "an induction hob", "induction cooker",
            "induction ring", "induction rings", "induction work"),
           MECHANISM),
          AN_INDUCTION_HOB,
          # the cleaning and pan-buying rows own those lines, and the word "hob" is in most of
          # them: "how do i clean an induction hob" is a how-to, and it answered this way once
          avoid=TROUBLE + ("clean", "cleaning", "cleaned", "wipe", "wiping", "burnt", "burned",
                           "scratch", "scratched", "scratches", "mark", "marks", "stain",
                           "stains", "pan", "pans", "saucepan", "wok", "fit", "install",
                           "installation", "socket", "wiring", "noise", "clicking"),
          ask=MECHANISM, bias=1),
]
