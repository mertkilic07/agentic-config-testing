# Team tasks (week of 16–18 November 2026)

Goal for the Wednesday meeting: a **per-configuration results table** for SQLite, where the
configurations come from an **ACTS 2-way covering array** of a **larger, screened model**, and
every number comes from SQLite's **own** Tcl tests.

Read the [README](../README.md) first; it explains the pipeline and the setup.

## Rules for everyone

- Work on a branch and open a pull request; do not push to `main` directly.
- Never mix runs from different machines/architectures in one table. Each table row records
  the machine in `summary.json`; one person runs one complete table on one machine.
- Do not hide problems: build failures, option mismatches, test errors and coverage failures
  are separate results. Write them down instead of re-running until they disappear.
- Do not invent constraints or results. If something is unclear, write "not verified".

## Task 1 – Run the experiment (owner: Emre)

1. Build the image and start the container (README, "Getting started").
2. Smoke test: `python3 scripts/run_config.py --row 1 --scope main` (about 1 minute).
   Report in the issue: did the image build, did the smoke test pass?
3. When Task 2 has produced the new covering array, start all rows in the evening:
   `python3 scripts/run_config.py --all --scope quick`
   (about 30–60 minutes per row; the machine must stay awake).
4. Make the table: `python3 scripts/make_table.py --scope quick > results/coverage_table.md`
5. Commit `results/acts/*-quick/` (summary files only, see `.gitignore`) and the table in a PR.

## Task 2 – Grow the model (owner: Tuna)

1. Read `results/screening/screening.md`: every candidate option was built alone and checked.
2. Choose the options for the new model: an option enters only if it **builds**, is
   **reported by `PRAGMA compile_options`**, its **probe** works, and `main.test` has 0 errors.
   For every candidate that is left out, write one line why.
3. Constraints found during screening (e.g. GEOPOLY needs RTREE) must be in the model.
   ACTS Basic does not support constraints, so either
   - request the advanced ACTS version (email address on the NIST ACTS download page), or
   - generate without constraints and document exactly which rows are invalid and how they
     are replaced. Never drop a constraint silently.
4. Update `models/sqlite-acts.txt` and `models/sqlite-build-mapping.json`, then run
   `bash scripts/generate_acts.sh` and commit the new `configs/sqlite-pairwise.csv`.
5. Write `docs/selection.md`: why SQLite, which options, which constraints, and the evidence
   (source file and line for each option).

## Task 3 – Prepare the test-gap analysis (owner: Mert)

1. SQLite tests skip themselves with `ifcapable <feature> { ... }`. For every option in the
   model, list which test files use the matching `ifcapable` keyword:
   `grep -l "ifcapable fts5" /opt/sqlite-src-3460100/test/*.test`
2. Put the result in `tests/existing/ifcapable-map.md` (option → number of test files,
   example file names). This is our version of the other group's "Stage 2" analysis.
3. Investigate the 4 baseline `recoverfault` failures: do they also appear in an
   uninstrumented build (without `--coverage`)? Record the answer, solved or not.
4. Prepare the Wednesday summary: what is done, the table, the open issues.
