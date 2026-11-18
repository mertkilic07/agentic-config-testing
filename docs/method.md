# How the experiment works

This page explains the pipeline behind `scripts/run_config.py` and the known open issues.

## What `run_config.py` does for one configuration

1. Reads one row of `configs/sqlite-pairwise.csv` (ACTS comment lines are skipped).
2. Turns each value into compiler flags using `models/sqlite-build-mapping.json`.
3. Builds `testfixture` in a fresh directory with
   `CFLAGS="-O0 -g --coverage -fprofile-update=atomic"`.
4. Asks the built `testfixture` for `PRAGMA compile_options` and checks that every option is
   on/off as requested. If not, the run stops and the mismatch is recorded.
5. Deletes the coverage counters written by that check.
6. Runs `test/<scope>.test` from a fresh directory on the container's own filesystem.
7. Measures line and function coverage of `sqlite3.c` only (same boundary for every row).
8. Writes `results/acts/<config>-<scope>/summary.json` with **separate** statuses for build,
   option check, tests and coverage.


## Known open issues

- **Baseline failures:** a team member's quick-suite run on the default build reported
  4 errors out of 591,311 tests (`recoverfault-*` allocation-failure tests in
  `ext/recover/recoverfault.test`). Cause found (task F): `recovercorrupt4.test` leaves a
  corrupt `testdir/test.db2` that `recoverfault.test` reuses; a test-order dependency, not a
  configuration interaction. Expected in every row; keep them in the error counts with a note.
  See [results/investigations/recoverfault](../results/investigations/recoverfault/README.md).
- **Quick-suite coverage (resolved):** an earlier attempt failed in gcovr with negative and
  suspiciously large counters. The runner builds with `-fprofile-update=atomic` (thread-safe
  coverage counters, `testfixture` uses threads) and passes
  `--gcov-suspicious-hits-threshold 1e11`; coverage status is `ok` in all 7 quick runs.
- **Passed / skipped counts:** SQLite's harness prints "N errors out of M tests". Passed is
  derived as M − N − 1 (the harness adds one count when it finishes, `test/tester.tcl:1298`).
  Skipped cannot be reported: `ifcapable` does not run the guarded code and nothing counts it.
  See the note under [results/coverage_table.md](../results/coverage_table.md).
- **Architecture:** the image is built for the host's architecture (ARM64 on Apple Silicon,
  AMD64 on most Windows PCs). Results from different architectures should not be mixed in one
  comparison.
