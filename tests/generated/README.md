# LLM-generated tests for untested option pairs (first agentic iteration)

Created 16–17 November 2026. This is the first, manual-loop version of the project's agentic
step: an LLM selects option pairs that SQLite's own tests do not exercise, writes tests for
them in SQLite's own Tcl format, runs them on every configuration of the covering array, and
the results are measured as before/after coverage.

**Who wrote the tests:** Claude (model `claude-opus-5-5`) in a Claude Code session driven by
Mert. The session had the repository, the SQLite 3.46.1 source and the built `testfixture`
binaries. It was not an autonomous agent program yet; the loop
(select gap → write → run → revise) was carried out step by step in the session. The
revisions are listed below so that nothing is hidden.

## 1. Gap selection

Input: [tests/existing/ifcapable-map.md](../existing/ifcapable-map.md) (task E). For the 4
pilot options, 5 of the 6 pairs are never guarded together in any quick-suite file:

| Pair | Files guarding both | Generated file |
|---|---|---|
| FTS5 × RTREE | 6 | – (already exercised) |
| FTS5 × COLUMN_METADATA | 0 | `gen_fts5_colmeta.test` |
| FTS5 × SECURE_DELETE | 0 | `gen_fts5_secdel.test` |
| RTREE × COLUMN_METADATA | 0 | `gen_rtree_colmeta.test` |
| RTREE × SECURE_DELETE | 0 | `gen_rtree_secdel.test` |
| COLUMN_METADATA × SECURE_DELETE | 0 | `gen_colmeta_secdel.test` |

Plus `gen_fts5_fts3.test` for FTS5 × FTS3 (outside the pilot model), the pair behind the
`fts5corrupt3` failures of the results table.

A guard on both keywords is only a proxy: a file may exercise a pair without guarding on it.

## 2. Test design

- Same harness as SQLite's own tests (`tester.tcl`, `do_execsql_test`, `ifcapable`), shared
  setup in `common.tcl`. Every file guards itself, so it runs in every configuration and
  skips the parts whose options are off.
- Oracle: SQLite's documentation (e.g. PRAGMA `secure_delete`: "SQLite overwrites deleted
  content with zeros"). Where the documentation does not fix a value, the test is marked
  **CHARACTERIZATION** (observed behaviour) in a comment.

## 3. Validation (each file × each of the 7 configurations)

| Round | Problem | Kind | Action |
|---|---|---|---|
| 1 | `gen_colmeta_secdel-1.0/2.0`: `PRAGMA secure_delete=N` returns N, the test expected no output | **invalid test** (LLM error) | expectation fixed |
| 1 | `gen_rtree_colmeta-2.1`: expected declared type `TEXT` for auxiliary column `+label TEXT`, got empty | **wrong expectation** (LLM error); the R-tree module declares auxiliary columns by name only (`ext/rtree/rtree.c:3664`) | expectation fixed, reason in comment |
| 1 | `gen_rtree_secdel-1.3` fails on acts-06 (RTREE on, SECURE_DELETE on) | **finding**, see section 5 | kept failing on purpose; runtime-pragma variant 1.4/1.5 added |
| 2 | only `gen_rtree_secdel-1.3/1.5` fail, on exactly the configurations where they run | expected | – |

Round 2 result (errors / test cases; a file that is skipped reports 1 test):

| Config | colmeta_secdel | fts5_colmeta | fts5_fts3 | fts5_secdel | rtree_colmeta | rtree_secdel |
|---|---|---|---|---|---|---|
| default | skip | skip | skip | skip | skip | skip |
| acts-01 (COLMETA, SECDEL) | 0 / 7 | skip | skip | skip | skip | skip |
| acts-02 (RTREE) | skip | skip | skip | skip | 0 / 4 | **1** / 12 |
| acts-03 (FTS5, SECDEL) | skip | 0 / 5 | 0 / 4 | 0 / 12 | skip | skip |
| acts-04 (FTS5, RTREE, COLMETA) | 0 / 7 | 0 / 9 | 0 / 4 | 0 / 11 | 0 / 7 | **1** / 12 |
| acts-05 (FTS5, COLMETA) | 0 / 7 | 0 / 9 | 0 / 4 | 0 / 11 | skip | skip |
| acts-06 (RTREE, COLMETA, SECDEL) | 0 / 7 | skip | skip | skip | 0 / 7 | **2** / 13 |

`gen_colmeta_secdel` runs whenever COLUMN_METADATA is on (it tests both secure_delete values
at runtime). Control check (acts-04 build): with `secure_delete=0` the deleted FTS5 term and
R-tree id are found in the file, so the file checks are not vacuous; with `secure_delete=1`
the FTS5 term is gone.

## 4. Coverage before / after

See [results/generated/coverage_ab.md](../../results/generated/coverage_ab.md).

## 5. Finding: deleted R-tree entries survive `secure_delete`

With `PRAGMA secure_delete=ON` (or the compile-time option `SQLITE_SECURE_DELETE`), deleting
the R-tree entry that occupies the last cell of a node leaves its id and coordinates inside
the node: `SELECT count(*) FROM rt_node WHERE instr(data, x'5A5A5A5A5A5A5A5A')>0` returns 1
after the row was deleted.

Cause (source, 3.46.1): `nodeDeleteCell()` (`ext/rtree/rtree.c:834`) moves the following
cells forward with `memmove()` and decrements the cell count, but does not clear the slot that
becomes unused. The stale bytes are part of the live `rt_node` blob, so page-level
secure_delete has nothing to overwrite. FTS5 under the same test removes the data
(`gen_fts5_secdel` passes).

- Seen with the compile-time option only in acts-06, the one covering-array row with
  RTREE × SECURE_DELETE; reproduced with the runtime pragma on every RTREE build.
- No existing quick-suite test checks this pair (section 1).
- Whether the SQLite developers regard this as a defect (the documentation promises zeroed
  *deleted content*), and whether later versions changed it: **not verified**.
- Only the case "deleted entry was the last cell of its node" is shown; other cases leave a
  copy of a different, still-live cell in the unused slot.
