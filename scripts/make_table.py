#!/usr/bin/env python3
"""Build the per-configuration results table from results/acts/*/summary.json.

Usage: python3 scripts/make_table.py [--scope quick] > results/coverage_table.md
"""
import argparse, glob, json, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--scope", default=None, help="only rows run with this test scope, e.g. quick")
a = ap.parse_args()

rows = []
for path in sorted(glob.glob(os.path.join(REPO, "results", "acts", "*", "summary.json"))):
    s = json.load(open(path))
    if a.scope and s["scope"] != f"test/{a.scope}.test":
        continue
    rows.append(s)

print("| Configuration | Values | Scope | Build | Options check | Tests run | Errors | Line coverage | Lines covered / total | Function coverage |")
print("|---|---|---|---|---|---|---|---|---|---|")
for s in rows:
    vals = ", ".join(f"{k.replace('SQLITE_', '')}={v}" for k, v in s["values"].items())
    t, c = s.get("tests", {}), s.get("coverage", {})
    if c.get("status") == "ok":
        line = f"{c['line_percent']}%"
        lines = f"{c['lines_covered']:,} / {c['lines_total']:,}"
        func = f"{c['function_percent']}%"
    else:
        line = lines = func = f"n/a ({c.get('status', 'not run')})"
    print(f"| {s['configuration']} | {vals} | {s['scope']} | {s['build'].get('status')} | "
          f"{s['effective_options'].get('status', '-')} | {t.get('tests', '-')} | {t.get('errors', '-')} | "
          f"{line} | {lines} | {func} |")
print()
print("'Tests run' and 'Errors' are taken from the summary line of SQLite's Tcl test harness. "
      "Passed/skipped counts are not yet extracted reliably, so they are not reported.")
