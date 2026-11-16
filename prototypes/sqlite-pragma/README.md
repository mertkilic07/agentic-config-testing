# Prototype 0: SQLite runtime options (PRAGMA), 10–11 November 2026

**Status: historical, superseded.** Kept to document how the project started.

What it did:
- An LLM wrote a model of 9 runtime options (PRAGMAs) with 5 constraints (`model/model.json`).
- A small greedy pairwise generator (`scripts/generate_configs.py`) reduced
  5,184 possible configurations to 20.
- LLM-written scripts applied each configuration to a fresh database and ran
  **7 small checks written by the LLM** (`scripts/run_one.py`).
- Result reported to the advisor on 11 November: 20 × 7 = 140 checks, 137 PASS, 3 SKIP, 0 FAIL.

Why it was superseded:
- It did **not** use SQLite's own test suite, so the numbers say little about how well
  SQLite's real tests cover option interactions. The advisor asked for each configuration
  to be built and tested with the system's own tests, with coverage per configuration.
- It used our own pairwise generator instead of NIST ACTS.

The current pipeline (compile-time options, ACTS, SQLite's own Tcl tests, coverage) is
described in the main [README](../../README.md). The PRAGMA model has not been transferred
into the current model.

The original README of the prototype is in [README-original.md](README-original.md).
