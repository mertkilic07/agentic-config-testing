# Team tasks

## Done so far (Mert, until 16 November 2026)

| Work | Where |
|---|---|
| Set up the repository and the Docker environment | `Dockerfile`, README |
| Prototype 0: SQLite PRAGMA model with LLM-written scripts, presented on 11 Nov | `prototypes/sqlite-pragma/` |
| Compared candidate systems (SQLite, BusyBox, ZooKeeper; curl as reference) | `docs/candidates.md` |
| Pinned SQLite 3.46.1, built it with coverage, ran SQLite's own `main.test` and `quick.test` | `docs/progress.md`, section 3 |
| Diagnosed and fixed the environment problems (bind-mount permissions, `backcompat.test`, gcovr version) | `docs/progress.md`, section 3 |
| Pilot model (4 compile-time options) and ACTS 2-way covering array (6 rows) | `models/`, `configs/` |
| Per-configuration runner, option-to-flag mapping, first smoke result | `scripts/run_config.py`, `results/acts/` |
| Option screening (16 candidates): found two silent constraints | `results/screening/` |
| Progress report | `docs/progress.md` |

## Remaining work (assigned at random, 16 November 2026)

The six open tasks were shuffled with Python (`random.Random(20261116)`) between Tuna and Emre.
Swap tasks among yourselves if needed, but update this table.

| Task | Owner | Depends on |
|---|---|---|
| A. Test-build the Dockerfile and run the smoke test | Tuna | – |
| B. Run all covering-array rows with the quick suite and make the results table | ~~Tuna~~ Mert: **done for the pilot model** (16 Nov). Tuna re-runs it after C | A, C |
| C. Grow the model, add constraints, generate the new ACTS covering array | Tuna | – |
| D. Write `docs/selection.md`: why SQLite, and why **not** BusyBox and ZooKeeper | Emre | – |
| E. Map existing tests to options (`ifcapable`) | Emre | – |
| F. Investigate the 4 baseline `recoverfault` failures | Emre | A (or Mert's container) |

Mert: review pull requests, prepare the Wednesday summary, help where someone is blocked.

## Rules for everyone

- Work on a branch and open a pull request; do not push to `main` directly.
- One person runs one complete results table on one machine. Never mix runs from different
  machines or architectures in one table (`summary.json` records the machine).
- Build failures, option mismatches, test errors and coverage failures are separate results.
  Write them down; do not re-run until they disappear.
- Do not invent constraints, results or sources. If something is not checked, write "not verified".

---

### A. Test-build the Dockerfile (Tuna)

```sh
git clone https://github.com/mertkilic07/agentic-config-testing.git
cd agentic-config-testing
docker build -t ens491-sqlite .
docker run --rm -it -v "${PWD}:/work" ens491-sqlite       # PowerShell
python3 scripts/run_config.py --row 1 --scope main
```
Report in the GitHub issue: did the image build, how long, did the smoke test pass
(build ok, options ok, 95 tests / 0 errors expected), and your machine (Windows, CPU).

### B. Run the experiment (Tuna)

After C has produced the new `configs/sqlite-pairwise.csv`:
```sh
python3 scripts/run_config.py --all --scope quick      # about 30-60 min per row, start in the evening
python3 scripts/make_table.py --scope quick > results/coverage_table.md
```
Commit `results/acts/*-quick/` (only small files are kept by `.gitignore`) and the table.

### C. Grow the model (Tuna)

1. Read `results/screening/screening.md`. All 16 candidates built alone; two silent
   constraints were found (GEOPOLY needs RTREE; OMIT_WAL ignores `journal_mode=WAL`).
2. Choose 10–15 options. For each one left out, write one line why.
3. The constraint "GEOPOLY on ⇒ RTREE on" must be in the model. ACTS Basic has no constraints:
   request the advanced ACTS version (email address on the NIST ACTS download page), **or**
   generate without constraints and document exactly which rows break the constraint and how
   they are fixed. Never drop it silently.
4. Update `models/sqlite-acts.txt` and `models/sqlite-build-mapping.json`
   (flags are in `models/sqlite-candidates.json`), run `bash scripts/generate_acts.sh`.

### D. Selection document (Emre)

Write `docs/selection.md`:
- Why SQLite: evidence from `docs/progress.md` and the screening (own test suite with
  `ifcapable`, compile-time and runtime options, `PRAGMA compile_options` as ground truth,
  constraints already found).
- **Why not BusyBox:** e.g. almost only compile-time options (Kconfig), test suite and
  coverage not checked yet, a coherent feature subset still to be chosen. Check each claim
  in BusyBox's documentation or source and cite it.
- **Why not Apache ZooKeeper:** e.g. runtime options must be passed into servers created by
  the tests, multi-server tests are slow and timing-dependent, numeric options need chosen
  value sets. Check and cite.
- Why not curl: studied by another group; used only as a methodological reference.
Write "not verified" next to any reason you could not check.

### E. Existing tests per option (Emre)

```sh
for k in fts5 rtree geopoly fts3 fts4 stat4 wal autovacuum; do
  echo "$k $(grep -l "ifcapable.*$k" /opt/sqlite-src-3460100/test/*.test | wc -l)"
done
```
Put the table (option → number of test files, example files) in `tests/existing/ifcapable-map.md`.
Check SQLite's `test/tester.tcl` / `src/test_config.c` for the exact `ifcapable` keyword of
each option.

### F. Baseline failures (Emre)

The default build's quick run reported 4 errors (`recoverfault-1/2-oom-*`). Build once
**without** `--coverage` and run only `ext/recover/recoverfault.test`. Record whether the
errors remain. "Cause not found" is an acceptable result if it is written down.
