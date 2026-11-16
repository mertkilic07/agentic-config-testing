# Progress report (until 16 November 2026)

This page tells the story of the project so far, step by step: what the advisor asked,
what we did, what we measured, and what is still open. Completed work and plans are kept
apart; anything not verified is marked as such.

## 1. The task

Project #516 asks whether an AI agent can find configuration-option interactions that a
program's own tests do not check, and write tests for them. Before an agent can be built
or evaluated, we need an experimental setup that answers, for a given program:

> If we build/configure the program in configuration *C* and run **its own** test suite,
> which tests run, which fail, and how much code do they cover?

The advisor's concrete requirements (meetings of 4 and 11 November):

1. Study combinatorial interaction testing (CIT) and covering arrays.
2. Pick an open-source configurable system and write down its configuration space model.
3. Use **NIST ACTS** to compute a **2-way covering array** from that model.
4. For each configuration: build/configure the system, run its **own** test suite, collect
   test outcomes and coverage, and report them in one table
   (Configuration / Tests run / Passed / Failed / Skipped / Line coverage / Lines covered /
   Function coverage).

## 2. Timeline

| Date | Step | Outcome |
|---|---|---|
| 30 Oct | Kick-off meeting | Topic: generative AI + CIT for highly configurable systems. Reading on CIT assigned |
| 1 Nov | Draft proposal | Submitted (course deliverable) |
| 4 Nov | Meeting | Read about CIT, compile-time vs runtime options, find configurable systems; by 11 Nov: one system, its model, LLM-generated scripts |
| 10–11 Nov | Prototype 0 (SQLite PRAGMA) | See [prototypes/sqlite-pragma](../prototypes/sqlite-pragma/). Presented on 11 Nov |
| 11 Nov | Meeting | Feedback: use the system's **own** test suite, report coverage per configuration (curl table of another group shown as example). New task: covering arrays + NIST ACTS |
| 16 Nov | Candidate comparison | [candidates.md](candidates.md): SQLite, BusyBox, Apache ZooKeeper; curl only as reference (used by another group) |
| 16 Nov | SQLite baseline | Pinned SQLite 3.46.1, built with coverage, own Tcl tests run (section 3) |
| 16 Nov | Pilot model + ACTS | 4 compile-time options, 6-row 2-way covering array (section 4) |
| 16 Nov | Runner | `scripts/run_config.py`, first smoke result (section 5) |
| 16 Nov | Model growth started | Screening of 16 candidate options (section 6) |

## 3. SQLite baseline (default build)

Environment: Docker, Ubuntu 24.04, Linux ARM64 on a MacBook Pro (M1 Pro), SQLite **3.46.1**
from the official archive `sqlite-src-3460100.zip`, built with
`configure --disable-shared CFLAGS="-O0 -g --coverage" LDFLAGS="--coverage"` and
`make sqlite3 testfixture`.

| Run | Result | Coverage of `sqlite3.c` |
|---|---|---|
| `test/main.test` | 95 tests, 0 errors | lines 21.5% (10,505 / 48,917), functions 34.9% (909 / 2,604), branches 14.7% |
| `test/quick.test` | 4 errors out of 591,311 tests | **not available** (measurement failed, see below) |

Problems found and how they were handled:

| Problem | Cause | Fix |
|---|---|---|
| `attach.test` aborted: "Tests do not work when run as root" | The test checks that a file is no longer writable after `chmod 0000`. On the Mac bind mount the file stays writable, also for a non-root user | Tests run in a fresh directory on the container's own filesystem (`/tmp`, later `~/ens491-work`) |
| `backcompat.test` tried to execute `testfixture-test_config.gcno` | It runs every `testfixture?*` file next to the executable; coverage files on the bind mount looked executable | `testfixture` is copied into a separate directory before running |
| gcovr 7.0 failed with `UnknownLineType` | gcovr version | gcovr 8.3 in a virtual environment |
| gcovr 8.3 failed on the quick run with negative and very large counters | Non-atomic counters with threads (negatives); genuinely huge loop counts (suspicious) | `-fprofile-update=atomic` (fixed negatives) + raised suspicious-hits threshold |

The 4 quick-suite errors (`recoverfault-1/2-oom-*`, in `ext/recover/recoverfault.test`)
are deliberate allocation-failure tests. They are recorded as baseline failures, not as
interaction bugs. Cause (task F, checked on x86_64): a test-order dependency in SQLite's own
suite. `recovercorrupt4.test` leaves a corrupt `testdir/test.db2`, which `recoverfault.test`
then uses as its output file; deleting that file in between gives 0 errors. Details:
[results/investigations/recoverfault](../results/investigations/recoverfault/README.md).

## 4. Pilot model and ACTS covering array

Model (`models/sqlite-acts.txt`): four binary compile-time options

| Option | `on` | `off` |
|---|---|---|
| `SQLITE_ENABLE_FTS5` | `-DSQLITE_ENABLE_FTS5` | not defined |
| `SQLITE_ENABLE_RTREE` | `-DSQLITE_ENABLE_RTREE` | not defined |
| `SQLITE_ENABLE_COLUMN_METADATA` | `-DSQLITE_ENABLE_COLUMN_METADATA` | not defined |
| `SQLITE_SECURE_DELETE` | `-DSQLITE_SECURE_DELETE` | not defined |

All four macros are checked with `#ifdef` in SQLite 3.46.1, so `off` must mean *not defined*
(`=0` would turn the feature on). No constraints were modelled; this does not prove the
options are independent.

ACTS Basic 1.0 (official NIST download), command in `scripts/generate_acts.sh`, reported:
strength 2, algorithm IPOG, 24 covered tuples, **6 configurations** instead of 16,
"Coverage has been verified!". Result: `configs/sqlite-pairwise.csv`.
This is *configuration-pair* coverage, not code coverage.

## 5. Automated per-configuration runner

`scripts/run_config.py` (details in the README): for one ACTS row it builds `testfixture` in a
fresh directory, checks the effective options with `PRAGMA compile_options`, runs SQLite's own
Tcl tests on the container filesystem, measures coverage of `sqlite3.c`, and writes
`results/acts/<config>-<scope>/summary.json` with separate statuses.

First result (Linux x86_64 VM, not a team laptop):

| Configuration | Values | Scope | Options check | Tests | Errors | Line coverage | Function coverage |
|---|---|---|---|---|---|---|---|
| acts-03 | FTS5=on, RTREE=off, COLUMN_METADATA=off, SECURE_DELETE=on | `main.test` | 4/4 as requested | 95 | 0 | 18.1% (10,618 / 58,665) | 28.8% |
| acts-03 | same | `quick.test` (38 min) | 4/4 as requested | 755,539 | 9 | 96.1% (56,399 / 58,665) | 97.4% |

Note: the number of lines in `sqlite3.c` depends on the configuration (58,665 here vs
48,917 in the baseline), so coverage percentages must always be read together with the
line counts.

Quick-suite errors of acts-03: 4 × `recoverfault` (same as baseline), `zipfile-6.0`
(timestamps differ by exactly 3600 s, likely time zone, not verified), and
`fts5corrupt3-74.1/75.1` (expect an FTS3/4 `matchinfo` error message; this row has FTS5 but
not FTS3/4).

The `fts5corrupt3` cause is now **verified** (task E): the expected message exists only when
FTS3 is compiled in (`ext/fts3/fts3.c:4174`), but the file is guarded only on FTS5. Running
only that file on fast builds (no coverage, x86_64): FTS5 + SECURE_DELETE → these 2 errors
(`no such function: matchinfo`); adding FTS3 → 0 errors. This is an FTS5 × FTS3 interaction
in the test suite, not shown to be a library defect. Since FTS3 is off in every row, rows 3–5
(FTS5 on) were expected to show it; the full table confirms this (section 5b). Details:
[tests/existing/fts5corrupt3-matchinfo.md](../tests/existing/fts5corrupt3-matchinfo.md).

Coverage fix: with `-fprofile-update=atomic` there are no more negative counters. gcovr still
rejected some genuine counts (~9.9 × 10⁹ hits) as "suspicious", so the runner now passes
`--gcov-suspicious-hits-threshold 1e11` and records it in `summary.json`.

## 5b. Full results table (16 November 2026)

All 6 covering-array rows and the default build were run with `test/quick.test` on one machine.
Table and failure analysis: [results/coverage_table.md](../results/coverage_table.md).

- Every build succeeded and every option was confirmed by `PRAGMA compile_options`.
- 590,935 – 761,095 tests per configuration; line coverage of `sqlite3.c` 95.6 – 96.2%,
  function coverage 96.9 – 97.5%.
- The default build and the FTS5=off rows have 5 errors (4 `recoverfault`, `zipfile-6.0`).
- The three FTS5=on rows have 4 extra errors (`fts5corrupt3-74.1/75.1`, `values-11.0/11.1`).
  Both tests are guarded by `ifcapable fts5` but use FTS3 features. This is a
  configuration-dependent defect **in the test suite** (FTS5 on, FTS3 off), verified for
  `values.test` in the source.
- Runner fix: failed test names are now read from the harness line "Failures on these tests";
  the earlier pattern missed tests that fail with an error message.

## 6. Option screening: two silent constraints

Before an option may enter the model, it is built alone and checked
(`scripts/screen_options.py`, candidates in `models/sqlite-candidates.json`, full table in
[results/screening/screening.md](../results/screening/screening.md)): does it build, is it
reported by `PRAGMA compile_options`, does a small functional probe work, does `main.test` pass?

All 16 candidates built and passed `main.test` alone. Two pair checks revealed **silent**
behaviour, where the build or the pragma succeeds but the requested feature is missing:

| Combination | What happens | Why (source) |
|---|---|---|
| `ENABLE_GEOPOLY` without `ENABLE_RTREE` | Build succeeds and `compile_options` reports `ENABLE_GEOPOLY`, but `geopoly_area()` does not exist | geopoly is compiled from inside `ext/rtree/rtree.c`, behind `#ifdef SQLITE_ENABLE_GEOPOLY` |
| `OMIT_WAL` (compile-time) + `PRAGMA journal_mode=WAL` (runtime) | No error; the pragma returns `delete` and WAL is not used | WAL code removed at compile time; the pragma keeps the old mode |

The second one crosses the compile-time / runtime boundary. Both are candidates for the
constraint list of the model and for the later test-gap analysis. These checks ran on a
Linux x86_64 VM.

## 6b. First AI-generated tests (16–17 November 2026)

Gap: 5 of the 6 pilot option pairs are never guarded together in the quick suite (task E map).
An LLM (Claude, in the working session) wrote 6 Tcl test files for them plus FTS5 × FTS3,
validated them on all 7 configurations and measured before/after coverage. Details:
[tests/generated/README.md](../tests/generated/README.md),
[results/generated/coverage_ab.md](../results/generated/coverage_ab.md).

- 2 of the generated tests were wrong in round 1 (one wrong expected output, one wrong
  assumption about R-tree column types) and were corrected; recorded, not hidden.
- **Finding:** deleting an R-tree entry with `secure_delete` on leaves the entry in the live
  `rt_node` blob (`nodeDeleteCell()` does not clear the freed slot, `ext/rtree/rtree.c:834`).
  With the compile-time option it shows only in acts-06, the covering-array row with
  RTREE × SECURE_DELETE. Whether SQLite considers this a defect: not verified.
- Coverage gain is small (0–7 lines per configuration) but lands on option-dependent branches,
  e.g. the `secure_delete=OFF` page-free path that the quick suite never runs in a
  SECURE_DELETE build.

## 7. What is not done yet

- Passed/skipped counts (the harness only prints "N errors out of M tests").
- Constraints in the model.
- An autonomous agent loop (the first iteration was run step by step in a session).
- A larger model, so the gap analysis has more pairs.

Who does what next: [team-tasks.md](team-tasks.md).
