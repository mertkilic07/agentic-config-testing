"""Generate a pairwise (2-way) covering array from model/model.json.

Usage: python3 scripts/generate_configs.py
Writes configs/configs.csv and model/model.pict (PICT format, for use with microsoft/pict).
No external packages needed: a simple greedy pairwise algorithm is included below.
"""
import csv, itertools, json, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model = json.load(open(os.path.join(ROOT, "model", "model.json")))
names = [o["name"] for o in model["options"]]
values = [o["values"] for o in model["options"]]
k = len(names)

# PICT version of the same model (so the team can compare with microsoft/pict)
with open(os.path.join(ROOT, "model", "model.pict"), "w") as f:
    for n, v in zip(names, values):
        f.write(f"{n}: {', '.join(v)}\n")

# every pair of (option i = value a, option j = value b) that must appear in some configuration
uncovered = {(i, a, j, b) for i, j in itertools.combinations(range(k), 2)
             for a in range(len(values[i])) for b in range(len(values[j]))}


def new_pairs(row, i, a):
    return sum((min(i, j), a if i < j else row[j], max(i, j), row[j] if i < j else a) in uncovered
               for j in range(k) if row[j] is not None and j != i)


rng = random.Random(491)  # fixed seed -> same result every run
rows = []
while uncovered:
    best, best_gain = None, -1
    for _ in range(60):  # try several greedy candidates, keep the best one
        i0, a0, j0, b0 = rng.choice(sorted(uncovered))
        row = [None] * k
        row[i0], row[j0] = a0, b0
        for i in rng.sample(range(k), k):
            if row[i] is None:
                row[i] = max(range(len(values[i])), key=lambda a: (new_pairs(row, i, a), rng.random()))
        gain = sum((i, row[i], j, row[j]) in uncovered for i, j in itertools.combinations(range(k), 2))
        if gain > best_gain:
            best, best_gain = row, gain
    rows.append(best)
    uncovered -= {(i, best[i], j, best[j]) for i, j in itertools.combinations(range(k), 2)}

with open(os.path.join(ROOT, "configs", "configs.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["config_id"] + names)
    for n, r in enumerate(rows, 1):
        w.writerow([f"C{n:02d}"] + [values[i][r[i]] for i in range(k)])

total = 1
for v in values:
    total *= len(v)
print(f"{k} options, exhaustive = {total} configurations, pairwise = {len(rows)} configurations")
