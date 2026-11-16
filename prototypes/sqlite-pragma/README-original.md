# LLM-assisted CIT pipeline – first prototype (SQLite)

ENS491 #516 – Agentic AI for Detecting and Testing Configuration Option Interactions
Week of 11 November 2026

## What this is
A first end-to-end pipeline in which an LLM prepares everything needed for combinatorial
interaction testing (CIT) of one open-source configurable system:

1. **Configuration space model** (`model/model.json`): 9 runtime options of SQLite (PRAGMAs),
   their values, defaults, and 5 constraints/dependencies (C1–C5), extracted by the LLM from the
   SQLite PRAGMA documentation.
2. **Pairwise covering array** (`configs/configs.csv`): generated from the model;
   the same model is also exported in PICT format (`model/model.pict`).
3. **Scripts written by the LLM** (`scripts/`): apply a configuration to a fresh database,
   run a small workload, and compare the observed behavior with what the model predicts.
4. **Results** (`results/results.csv`).

## Run it
```
python3 scripts/generate_configs.py   # model -> pairwise configurations
python3 scripts/run_all.py            # run every configuration, write results/results.csv
```
Only Python 3 is needed (no extra packages); SQLite comes with Python.

## Result of the first run (SQLite 3.53.1)
- 9 options -> 5,184 configurations exhaustively; **20 configurations** cover all pairs.
- 20 configurations x 7 checks = 140 checks: **137 PASS, 0 FAIL, 3 SKIP**.
- The 3 SKIPs are the rollback check under `journal_mode=OFF`, where the model (C2) says
  rollback is not a valid oracle. Observation: in these runs rollback still restored the data.
- All requested settings were actually applied (no requested/effective mismatch).

## What each check tests
| Check | Model element |
|---|---|
| settings_applied | every requested PRAGMA value is the effective value |
| crud | basic create/insert/select works |
| rollback | ROLLBACK restores state (C2) |
| foreign_keys | orphan insert rejected iff foreign_keys=ON (C5) |
| auto_vacuum | freelist empty iff auto_vacuum=FULL (C4) |
| second_connection | second connection blocked iff locking_mode=EXCLUSIVE (C3) |
| integrity | PRAGMA integrity_check = ok |

## Limitations / next steps
- The model covers 9 of SQLite's many PRAGMAs and only runtime options; compile-time options
  (`SQLITE_*`) need one build per configuration.
- The workload is small and was written by the LLM; the existing SQLite test suite is not used yet.
- The model still has to be validated option by option against the documentation by the team.
- Next system: Apache ZooKeeper (runtime options in `zoo.cfg`; downloads were blocked in this
  environment, so it has to be set up on a team member's computer).
