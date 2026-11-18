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

print("| Configuration | Values | Scope | Build | Options check | Tests run | Passed | Failed | Skipped | Line coverage | Lines covered / total | Function coverage |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for s in rows:
    vals = ", ".join(f"{k.replace('SQLITE_', '')}={v}" for k, v in s["values"].items())
    t, c = s.get("tests", {}), s.get("coverage", {})
    if c.get("status") == "ok":
        line = f"{c['line_percent']}%"
        lines = f"{c['lines_covered']:,} / {c['lines_total']:,}"
        func = f"{c['function_percent']}%"
    else:
        line = lines = func = f"n/a ({c.get('status', 'not run')})"
    n, e = t.get("tests"), t.get("errors")
    # The harness counts every executed test (incr_ntest in do_test) plus one extra count in
    # finalize_testing (test/tester.tcl:1298); errors are a subset of the executed tests.
    passed = f"{n - e - 1:,}" if isinstance(n, int) and isinstance(e, int) else "-"
    fmt = lambda v: f"{v:,}" if isinstance(v, int) else (v if v is not None else "-")
    print(f"| {s['configuration']} | {vals} | {s['scope']} | {s['build'].get('status')} | "
          f"{s['effective_options'].get('status', '-')} | {fmt(n)} | {passed} | {fmt(e)} | n/a | "
          f"{line} | {lines} | {func} |")
print()
print("'Tests run' and 'Failed' are the two numbers of the harness summary line "
      "\"N errors out of M tests\". **Passed** = Tests run - Failed - 1: the harness counts every "
      "executed test (`do_test` calls `incr_ntest`) plus one extra count when it finishes "
      "(`finalize_testing`, `test/tester.tcl:1298`), and every failure is one of the executed tests "
      "(`fail_test`). **Skipped** is not reported because SQLite's harness does not count it: "
      "`ifcapable` (`test/tester.tcl:1745`) simply does not run the guarded code, and the only "
      "\"Omitted\" list is for tests filtered out by name. The effect of skipping shows in "
      "'Tests run', which changes with the configuration (about 591k without FTS5, up to 761k with it).")
