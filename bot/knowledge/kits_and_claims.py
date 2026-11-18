"""Three questions people ask that the neighbouring cards could not answer, as data.

Each row here answers a line that was reaching a card about something next door:

- a car the person's own insurer has written off is a settlement question. `write-off-category`
  explains Cat S and Cat N, the dealer row in `consumer.py` is about buying one, and
  `repair-or-scrap` in `cars.py` is the decision to mend or sell, so "my car was written off, do
  i get a payout" was answered with the dealer's duty and "how much will my insurer pay" with a
  savings ladder.
- "what do i need for a home office" is a shopping list, and `work-from-home-council` answered it
  with council tax.
- "what do i need for a day case" is a bag, and the 111 line answered it while "what should i
  take to hospital for an operation" got the gift card.

They live in one module rather than three because each is a single row and a row belongs beside
the rows it shares words with, which here is nothing: the three subjects have no keys in common.
"""

from .lookup import entry

ENTRIES = [
    entry("car-write-off-payout",
          (("written off", "write off", "wrote it off", "wrote off", "total loss", "write-off",
            "cat s", "cat n",
            # "the insurer wrote my car off, how much will i get" says it with the car inside the
            # phrase, which none of the shorter forms match
            "wrote my car off", "wrote the car off", "wrote my van off", "write my car off",
            "writing my car off", "wrote mine off", "write it off"),
           ("payout", "pay out", "paid out", "how much", "settlement", "settle", "offer",
            "do i get", "get the money", "market value", "keep the car", "buy it back",
            "salvage", "argue", "appeal", "disagree", "too low", "process", "what now",
            "what happens", "accept")),
          "The insurer settles at the car's market value just before the crash, not what you "
          "paid for it: check their offer against three or four adverts for the same age, "
          "mileage and trim, and send them the links if it is low. Repairs can be offered "
          "instead when they are cheaper and safe. Ask what the salvage is worth if you want to "
          "keep the car - you buy it back, and it usually becomes Cat S or Cat N.",
          # the category explanation and the sold-as-clean line are other questions
          avoid=("dealer", "dealership", "forecourt", "sold me", "sold as seen",
                 "what does", "what is cat", "difference between", "mean"),
          # the dealer's duty scores the same 6 as this row on "my car was written off, do i get
          # a payout", and "can i keep my car after it was written off" was reaching the Cat S/N
          # explanation, so the settlement is the card for these lines
          bias=2,
          ask=("car", "van", "vehicle", "insurer", "insurance", "payout", "settle", "offer",
               "salvage", "written off", "write off", "total loss")),

    entry("home-office-desk",
          (("home office", "office at home", "desk setup", "desk set up", "wfh",
            "work from home", "working from home", "homeworking"),
           # a how-to ("how do i set up a home office") is the posture row's: this row answers
           # the shopping list only
           ("need", "buy", "get", "kit", "what do i need", "what should i", "essentials")),
          "Get the chair right first and the rest is cheap: an adjustable one so your feet are "
          "flat and the arms sit at elbow height, the screen top at eye level, a stack of books "
          "or a riser under a laptop, and a lamp beside your writing hand rather than behind "
          "you. A separate keyboard and mouse are the other fix worth paying for.",
          # the tax line is the council-tax row's, a room being built or painted is building
          # work, and "homework" carries home and work: a child's homework got the desk kit
          avoid=("council tax", "business rates", "tax", "expenses", "allowance", "claim",
                 "employer", "extension", "convert", "conversion", "loft", "build", "building",
                 "paint", "decorate", "rent", "landlord", "homework", "school", "teacher",
                 "year old", "kids", "children", "child", "revision", "exam", "study",
                 "toddler")),

    entry("hospital-bag-for-an-operation",
          (("hospital", "operation", "surgery", "day case", "day surgery", "admitted",
            "admission", "procedure", "overnight stay"),
           ("take", "bring", "pack", "bag", "need", "what to take", "what should i take",
            "what do i bring", "what to bring", "what do i need", "come in with")),
          "Take your medicines in their boxes, the admission letter, phone and charger, and "
          "loose clothes you can get on one-handed; for a day case add slippers with a back and "
          "a named bag for your clothes. Leave valuables at home, and ask the ward what they "
          "provide before you pack towels and toiletries.",
          # the pregnancy bag, the gift, a visit and the decision to go in are other rows
          avoid=("hospital bag", "maternity", "labour", "birth", "baby", "pregnant",
                 "pregnancy", "visit", "visiting", "gift", "present", "flowers", "should i go",
                 "do i need to go", "a and e", "casualty", "111", "999", "ambulance"),
          # level with the 111 line and the gift card on the same words, so the bag is what is
          # given rather than an appointment or a present
          bias=2,
          ask=("take", "bring", "pack", "bag", "need", "hospital", "operation", "surgery")),
]
