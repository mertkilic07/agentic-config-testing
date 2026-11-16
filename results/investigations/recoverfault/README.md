# Task F: the 4 baseline `recoverfault` errors

Checked 16 November 2026 (Emre). SQLite 3.46.1, Docker image `ens491-sqlite`, Windows 11 /
Docker Desktop, Linux x86_64. These are investigation runs, **not** part of the results table.

## Result in one sentence

The 4 errors are a **test-order dependency in SQLite's own test suite**, not a configuration
interaction and not shown to be a library defect: `ext/recover/recovercorrupt4.test` leaves a
truncated, corrupt `testdir/test.db2`, and `ext/recover/recoverfault.test`, which runs right
after it in `quick`, uses `test.db2` as its recovery output file without deleting it first.

## The errors

From the quick runs (default build on the team member's machine; acts-03 in
`results/acts/acts-03-quick/summary.json`):
`recoverfault-1-oom-persistent.N`, `recoverfault-1-oom-transient.N`,
`recoverfault-2-oom-persistent.N+1`, `recoverfault-2-oom-transient.N+1`
(N = 524 in acts-03). Each failure line has the form

```
! recoverfault-1-oom-persistent.435 expected: [0 ok]
! recoverfault-1-oom-persistent.435 got:      [1 {nfail=0 rc=1 result= list={0 {}} {1 {}} {1 {out of memory}}}]
```

`nfail=0` means: in this iteration no allocation failure was injected (the fault loop has
reached its end), so the recovery must succeed, but it returned an error with an empty message.

## What was run

Scripts in this folder, logs summarised in [runs.txt](runs.txt). All builds:
`configure --disable-shared` + `make testfixture`; "coverage" = the flags of
`scripts/run_config.py` (`-O0 -g --coverage -fprofile-update=atomic`, `LDFLAGS=--coverage`).

| # | Script | What | Result |
|---|---|---|---|
| 1 | `1_alone.sh` | Default build, `recoverfault.test` **alone**, without and with coverage | 0 errors / 7495 tests (both) |
| 2 | `2_quick_harness_only.sh` | `permutations.test quick recoverfault.test` (quick harness, only this file) | 0 errors / 7498 |
| 3 | `3_quick_subset.sh` | quick suite restricted with `SQLITE_TEST_PATTERN_LIST` to all files that run **before** `recoverfault.test` (`run_tests` sorts with `lsort`, so all `ext/` files come first) | **4 errors**, same 4 tests (N = 435) |
| 3 | same, one group at a time + `recoverfault.test` | `expert*`, `fts5*`, `intck*`, `lsm1*`, `rbu*` | 0 errors each |
| 3 | same | earlier `ext/recover` files + `recoverfault.test` | **4 errors** |
| 3 | same, one file at a time + `recoverfault.test` | `recover1`, `recoverbuild`, `recoverclobber`, `recovercorrupt2`, `recovercorrupt3` | 0 errors each |
| 3 | same | **`recovercorrupt4.test`** + `recoverfault.test` | **4 errors** |
| 4 | `4_causal_leftover_db2.sh` | Two **separate processes** in one directory: `recovercorrupt4.test`, then `recoverfault.test`; once keeping and once deleting `testdir/test.db2` in between; without and with coverage | keep → **4 errors**; delete → **0 errors** / 7495 (both builds) |
| 5 | `5_acts03_and_single_recovery.sh` | Same as 4 (keep) with acts-03 options (`-DSQLITE_ENABLE_FTS5 -DSQLITE_SECURE_DELETE`) and coverage | 4 errors, N = **524**, the same names as in the acts-03 quick run |
| 5 | same | One recovery into the leftover `test.db2`, no fault injection | `$R run` → errcode 11 (`SQLITE_CORRUPT`), empty errmsg; `$R finish` → rc=1, empty result |

Run 3 commands (each `LABEL "patterns"` pair is one quick run):
`bash 3_quick_subset.sh d_prefix_all "expert* fts5* intck* lsm1* rbu* recover1.test recoverbuild.test recoverclobber.test recovercorrupt*.test recoverfault.test"`,
then the groups and single files as listed above.
`4_causal_leftover_db2.sh` differs from the script that ran only in the line that prints the file
list (a quoting fix; the run's output is in `runs.txt`).

## Why it happens (source, 3.46.1)

1. Tests run in the subdirectory `testdir/` (`test/tester.tcl:561`), shared by all files of a run.
2. `recovercorrupt4.test` (added 2024-05-15) writes the first `size − 1024` bytes of `test.db`
   to `test.db2` (a truncated, corrupt copy, 3072 bytes here), recovers it into `test.db3`, and
   does not delete either file.
3. When `recoverfault.test` starts, `reset_db` (`test/tester.tcl:611`) deletes only `test.db`,
   `test.db-journal` and `test.db-wal`. The corrupt `test.db2` stays.
4. `faultsim_save_and_close` → `db_save` (`test/tester.tcl:2478`) copies **every** `test.db*`
   file, so the corrupt `test.db2` is saved too, and every `-prep` (`db_restore`) puts it back.
5. Each iteration therefore recovers *into* an existing corrupt database. Iterations with an
   injected fault are allowed to fail (`faultsim_test_result {0 {}} {1 {}}`), so the problem is
   only visible in the last iteration, where no fault is injected and success is required.
   The recovery stops early with `SQLITE_CORRUPT`, so fewer allocations are needed; that is why
   the loop ends at N≈435–525 instead of 1292 / 2454 when the file runs alone. N depends on the
   build (435 default, 524 with acts-03 options + coverage).

## Consequences for the experiment

- These 4 errors are expected in **every** covering-array row and in the default build whenever
  both files run in `quick`. Neither file has an `ifcapable` guard (`tests/existing`
  on branch `task-e-ifcapable-map`); `ext/recover/recover_common.tcl` only skips them if the Tcl
  command `sqlite3_recover_init` is missing, which does not depend on the pilot options. So they
  run in every configuration of the pilot model.
  Prediction, **confirmed** by the full table of 16 Nov: all 6 rows and the default build show
  them, with N between 435 and 563.
- They should be reported in the table as a known baseline/test-isolation failure, **kept** in
  the error counts (team rule: do not re-run until they disappear), with a note pointing here.
- They are not evidence of an option interaction.
- Whether a later SQLite version fixes the order dependency: **not verified**.
- The machine of the original default-build run (ARM64 Mac) was not used here; that its errors
  have the same cause is consistent with the identical test names but **not verified** on ARM64.
