"""Build the fixed eval splits from the raw downloads in data/.

    python3 prepare.py

Writes splits/*.jsonl, one {"id", "question", "answer"} per line (answer is a number, or
null for chat prompts):

  splits/train     GSM8K train (7473)          agents may read freely
  splits/chat      SmolTalkBench (1000)        ordinary chat prompts; regression check
  hidden/test      GSM8K test (1319)           agents NEVER read; aggregate score only
  hidden/symbolic  GSM-Symbolic main (5000)    renumbered/renamed variants of 100 test
                                               problems; agents NEVER read; memorisation check
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "splits")
HIDDEN = os.path.join(HERE, "hidden")


def gold(answer_text):
    """GSM8K-style answers end in '#### <number>'."""
    tail = answer_text.split("####")[-1].strip().replace(",", "").replace("$", "")
    value = float(tail)
    return int(value) if value == int(value) else value


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def write(name, rows, folder=None):
    with open(os.path.join(folder or OUT, name + ".jsonl"), "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    print("%-9s %5d" % (name, len(rows)))


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(HIDDEN, exist_ok=True)

    train = [{"id": "train-%04d" % i, "question": r["question"], "answer": gold(r["answer"]),
              "solution": r["answer"]}
             for i, r in enumerate(read_jsonl(os.path.join(DATA, "train.jsonl")))]
    write("train", train)

    write("test", [{"id": "test-%04d" % i, "question": r["question"], "answer": gold(r["answer"])}
                   for i, r in enumerate(read_jsonl(os.path.join(DATA, "test.jsonl")))], HIDDEN)

    write("symbolic", [{"id": "sym-%03d-%02d" % (r["id"], r["instance"]), "question": r["question"],
                        "answer": gold(r["answer"]), "template": r["id"],
                        "original_test_index": r["original_id"]}
                       for r in read_jsonl(os.path.join(DATA, "symbolic", "main.jsonl"))], HIDDEN)

    import pyarrow.parquet as pq  # only needed here, not by the eval
    chat = pq.read_table(os.path.join(DATA, "smoltalk", "test.parquet")).to_pylist()
    write("chat", [{"id": r["id"], "question": r["instruction"], "answer": None,
                    "category": r["category"]} for r in chat])


if __name__ == "__main__":
    main()
