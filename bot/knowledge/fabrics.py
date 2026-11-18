"""What bedding, clothes and towels are made of, and what the numbers on the label mean.

The answers lane owns this domain. Nothing in the tree answered it: on main `4f06dd8` "what is a
tog rating", "what is thread count", "what does gsm mean in fabric", "what is viscose", "what is
linen made from", "what is bamboo fabric" and "what is the difference between cotton and
polyester" were all search hedges, and they are the questions a person has in a shop with a duvet
in one hand. The nearest cards - `clothing.py` on how to wash a thing, `home.py` on a bed - both
tell you what to do with a fabric you already own, not what the words on the packet mean.

The facts are keyed by the term or the fibre, never by the asking: "what is a tog rating", "what
tog for winter" and "what tog duvet should i buy" are one fact about togs. Every number here is
the ordinary retail one, because the point of the answer is that the shopper can act on it.

The `avoid` lists keep the neighbours out: a "gsm" line is about paper as often as fabric, "tog"
is not a tog, and "thread count" is a sewing question as well as a sheet one.
"""
import re

from .lookup import entry

# Both ids are declared by domains that already exist, so this file answers the lines those
# domains pass on: a duvet's tog is read as a home question, a towel's gsm as a shopping one.
ANSWERS = ("home-and-diy", "shopping")

# The words that ask what a term means, shared by the rows that are definitions.
DEFINE = ("what is", "whats", "what's", "what does", "what do", "mean", "means", "meaning",
          "definition", "define", "explain", "how much", "how many", "difference",
          "difference between", "which", "better", "should i", "do i need", "is", "are",
          "explained", "stand for", "stand for", "work", "works")


def _the_text(reading):
    """The line as it was said, from the reading every entry is handed."""
    if not isinstance(reading, dict):
        return ""
    text = reading.get("clean") or reading.get("text")
    if not text:
        words = reading.get("words")
        text = " ".join(words) if isinstance(words, (list, tuple)) else ""
    return str(text).lower()


# What the thing has to survive decides the fibre, so the table is keyed on the use. Each row is
# the one fact for that use and has to work as a sentence on its own.
USES = (
    (("sheet", "sheets", "bedsheet", "bedsheets", "bed sheet", "bed sheets", "bedding",
      "duvet cover", "duvet covers", "pillowcase", "pillowcases"),
     "For bedding, long-staple cotton in a percale weave is the cool, crisp choice and lasts; "
     "sateen is the smoother, warmer one if you sleep cold. Linen is the coolest in summer and "
     "softens for years but creases. Polycotton is cheap and needs little ironing, and it feels "
     "it - it traps heat."),
    (("towel", "towels", "bath towel", "hand towel"),
     "For towels, cotton terry at 500 to 600 GSM is the sweet spot: heavier is plusher but slow to "
     "dry, and anything under 400 is thin. Egyptian or Turkish cotton is a marketing label more "
     "than a guarantee - a long-staple cotton at 550 GSM beats a short-staple one at 700."),
    (("t-shirt", "tee", "tshirt", "tshirts", "underwear", "vest", "socks"),
     "For something worn all day next to the skin, cotton or a cotton-rich blend: it breathes and "
     "does not hold smell the way polyester does. 180 to 220 GSM cotton is a t-shirt that keeps "
     "its shape; a 2% to 5% elastane blend is what stops underwear going baggy."),
    (("curtain", "curtains", "cushion", "cushions", "upholstery", "sofa cover"),
     "For curtains and cushions, weight and light matter more than the fibre: a lining makes any "
     "fabric hang better and keeps the light out, and a polycotton or a linen-look weave is "
     "cheaper and does not fade the way a printed cotton does. For a sofa that gets sat on, a "
     "tight weave in a blend beats a loose linen."),
    (("winter coat", "coat", "jacket", "raincoat", "waterproof"),
     "For a coat, the outer layer does one job and the lining another: a tightly woven wool or a "
     "synthetic shell for wind and rain, and a smooth lining so it goes on over a jumper. Wool "
     "keeps you warm when damp, which is why it is still the best winter fabric; down is warmer "
     "for its weight but useless wet. Check the seams for taped ones on anything sold as "
     "waterproof."),
    (("baby", "babies", "newborn", "child", "children", "kid", "kids"),
     "For a baby, plain cotton next to the skin and nothing loose: cotton breathes and washes hot, "
     "and it does not hold the smell that polyester does. Avoid anything with a long pile or a "
     "loose trim, keep the bedding tight-fitting, and wash new clothes once before they go on."),
    (("gym", "sport", "running", "exercise", "workout", "cycling"),
     "For sport, polyester or a polyamide blend: it does not absorb sweat, so it dries fast and "
     "stays light, where cotton gets heavy and cold. Look for a mesh panel or a wicking finish, "
     "and wash it soon after - the smell that lingers in sports kit is oil trapped in the fibre, "
     "which a cool wash does not shift."),
)


def _the_use(memory, reading):
    """The fabric the line's own thing wants, or None when it names no use."""
    text = _the_text(reading)
    for words, reply in USES:
        if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in words):
            return reply
    return None


ENTRIES = [
    entry("tog-rating",
          (("tog", "togs", "tog rating", "tog value", "duvet rating", "duvet tog"),
           DEFINE),
          ("A tog is how well a duvet holds warmth, not how thick it is: 4.5 is a summer duvet, "
           "9 to 10.5 is spring and autumn, 13.5 is winter, and 15 is for a cold room. Most people "
           "are best off with a 10.5 for eight months of the year and a 4.5 for the hot ones, and "
           "two duvets - a 4.5 and a 9 - can be poppered together for winter instead of buying a "
           "13.5. Children under one should not have a duvet at all."),
          bias=3,
          # a "tog" is also a coat, a toga, and the verb; those lines name none of the numbers
          avoid=("toga", "togas", "together", "toggle", "toggles", "coat", "jacket", "sleeping bag",
                 "cot", "moses basket", "swaddle", "sleep bag", "grow bag")),
    entry("thread-count",
          (("thread count", "threadcount", "thread counts", "percale", "sateen", "weave"),
           DEFINE),
          ("Thread count is the number of threads woven into one square inch, and past about 300 "
           "it stops telling you anything: the count is easy to inflate by counting plied yarns "
           "twice, so a 1,000-count sheet is often a 500-count one with two threads twisted "
           "together. The fibre and the weave matter more - long-staple cotton in a percale weave "
           "is cool and crisp, sateen is smoother and warmer, and a 200-count percale lasts "
           "longer than a thin 800."),
          bias=3,
          avoid=("sewing thread", "cotton thread", "needle", "sewing machine", "embroidery",
                 "serger", "overlock", "knitting", "wool")),
    entry("gsm-fabric",
          (("gsm", "grams per square metre", "grams per square meter", "grammage",
            "fabric weight", "weight of the fabric"),
           DEFINE),
          ("GSM is grams per square metre, and it is how heavy a fabric is: a thin t-shirt is 140 "
           "to 180, a good everyday tee 180 to 220, a hoodie 300 to 400, and a heavy sweatshirt 400 "
           "or more. Towels run 400 to 600 GSM, and bedding 120 to 150. Higher is thicker, heavier "
           "and warmer, not automatically better - a 600 GSM towel takes forever to dry outdoors."),
          bias=3,
          avoid=("paper", "card", "cardstock", "stationery", "phone", "mobile", "network",
                 "signal", "sim", "printer", "printing", "photocopy")),
    entry("cotton-vs-polyester",
          (("cotton and polyester", "polyester and cotton", "cotton or polyester",
            "polyester", "polycotton", "poly cotton", "cotton vs polyester",
            "difference between cotton"),
           DEFINE),
          ("Cotton breathes, takes up water and gets softer with washing; polyester does not absorb "
           "water, so it dries fast and wicks sweat, but it holds body oils and smell, which is why "
           "a cheap polyester top pongs after one wear. A blend is the compromise most clothes are: "
           "60/40 polycotton creases less and dries faster than pure cotton, and 5% elastane in a "
           "cotton shirt is what stops it losing its shape. For sheets and summer shirts, cotton; "
           "for sportswear and rain jackets, polyester."),
          bias=3),
    entry("viscose-rayon",
          (("viscose", "rayon", "lyocell", "tencel", "modal", "cupro", "acetate",
            "bamboo fabric", "bamboo viscose", "bamboo lyocell"),
           DEFINE),
          ("Viscose, rayon, modal and lyocell are all made from wood or bamboo pulp dissolved and "
           "spun into fibre, which is why they feel cool and drape like silk; lyocell (Tencel) is "
           "the version made with a solvent that is recovered and reused. They are weak when wet, "
           "so wash them cool on a gentle cycle and never wring them, and dry them flat because "
           "they stretch out on a hanger. \"Bamboo fabric\" on a label is nearly always bamboo "
           "viscose, and it is not antibacterial however it is sold."),
          bias=3,
          avoid=("bamboo plant", "bamboo cane", "bamboo screen", "garden", "shoots", "panda",
                 "plant", "grow", "cut down")),
    entry("linen-fibre",
          (("linen", "flax", "linen fabric", "linen sheets"),
           DEFINE),
          ("Linen is woven from the fibres of the flax plant, which makes it the strongest of the "
           "plant fibres and the coolest in heat: it carries water away fast and does not cling. It "
           "creases the moment you move and feels stiff when new, and both of those go off with "
           "washing - a linen shirt gets softer every wash for years. Wash it at 30 or 40 and never "
           "tumble dry it hot, or it shrinks and goes brittle."),
          bias=3,
          avoid=("linen cupboard", "linen basket", "table linen", "bed linen", "towels",
                 "restaurant", "napkins", "hire", "laundry")),
    entry("elastane",
          (("elastane", "spandex", "lycra", "stretch fabric", "what is 5% elastane"),
           DEFINE),
          ("Elastane - sold as Lycra or Spandex - is the rubber-like fibre that makes a fabric "
           "stretch and spring back: 2% in a shirt keeps the shape, 5% in jeans lets you sit down, "
           "and 20% is sportswear. It is what wears out first, because heat and chlorine break it "
           "down: wash it cool and never tumble dry it, and it will keep its stretch for years "
           "instead of going baggy at the knees."),
          bias=3),
    entry("which-fabric-for",
          (("fabric for", "material for", "what fabric", "which fabric", "best fabric",
            "best material", "what material", "which material"),
           ("should", "use", "buy", "best", "for", "which", "what")),
          _the_use, bias=2,
          guard=lambda reading: bool(_the_use(None, reading))),
]
