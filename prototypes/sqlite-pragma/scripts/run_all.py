"""Run every configuration in configs/configs.csv and write results/results.csv.

Usage: python3 scripts/run_all.py
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_one import run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = list(csv.DictReader(open(os.path.join(ROOT, "configs", "configs.csv"))))
out = []
for r in rows:
    cid = r.pop("config_id")
    try:
        checks = run(r)
    except Exception as e:  # a crash is also a result
        checks = {"crash": ("FAIL", repr(e))}
    for check, (status, detail) in checks.items():
        out.append({"config_id": cid, **r, "check": check, "status": status, "detail": detail})

with open(os.path.join(ROOT, "results", "results.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader(); w.writerows(out)

fails = [o for o in out if o["status"] == "FAIL"]
print(f"{len(rows)} configurations, {len(out)} checks, {len(fails)} FAIL")
for o in fails:
    print(f"  {o['config_id']} {o['check']}: {o['detail']}")
