# `fts5corrupt3-74.1` / `75.1`: test depends on FTS3 but is guarded only on FTS5

Checked 16 November 2026 (Emre), SQLite 3.46.1, Docker image `ens491-sqlite` on Windows 11 /
Docker Desktop, x86_64. This is a check of two quick-suite errors seen in acts-03; it is **not**
part of the results table.

## Observation (from acts-03, quick suite)

acts-03 = FTS5 on, RTREE off, COLUMN_METADATA off, SECURE_DELETE on. Two of its 9 quick-suite
errors were `fts5corrupt3-74.1` and `fts5corrupt3-75.1`.

## What the tests do

`ext/fts5/test/fts5corrupt3.test` is skipped unless FTS5 is present (`ifcapable !fts5 {finish_test;
return}`, line 21). It has no guard on `fts3`.

Tests 74.0 / 75.0 open a fresh connection (`reset_db`, `sqlite3 db {}`) and deserialize a corrupt
database. Decoding the hex dumps shows `t1` is an **FTS5** table
(`CREATE VIRTUAL TABLE t1 USING fts5(a,b,c)`); the text `fts4` in the dump is row data.
Tests 74.1 / 75.1 then run

```sql
SELECT rowid, quote(matchinfo(t1,'...')) FROM t1 WHERE t1 MATCH 'e*';
```

and expect `1 {unable to use function matchinfo in the requested context}`.

## Why the expected message needs FTS3 (source, 3.46.1)

- That message is produced by the placeholder function that `sqlite3_overload_function()` installs
  (`src/main.c:2172`).
- For `matchinfo`, the placeholder is installed per connection by FTS3's init:
  `ext/fts3/fts3.c:4174-4175` (`sqlite3_overload_function(db, "matchinfo", 1)` and `..., 2)`).
- FTS5 installs a placeholder only for its registered auxiliary functions (`fts5CreateAux`,
  `ext/fts5/fts5_main.c:2756`). Its `matchinfo` demo is registered only by the Tcl command
  `sqlite3_fts5_register_matchinfo` (used at lines 8349 and 8553 of the test file, on earlier
  connections, not on the fresh connection of tests 74/75) or with `SQLITE_FTS5_ENABLE_TEST_MI`.
- So with FTS5 but without FTS3 there is no function `matchinfo` at all, and the statement
  fails at prepare time with `no such function: matchinfo`.

## Check (executed)

Two fast builds (`configure --disable-shared CFLAGS="-O0 -g"`, `make testfixture OPTS=...`, no
coverage), each running only `ext/fts5/test/fts5corrupt3.test`:

| Build | `OPTS` | Result |
|---|---|---|
| A (acts-03 flags) | `-DSQLITE_ENABLE_FTS5 -DSQLITE_SECURE_DELETE` | **2 errors out of 2012 tests**: 74.1 and 75.1, got `1 {no such function: matchinfo}` |
| B (A + FTS3) | `-DSQLITE_ENABLE_FTS5 -DSQLITE_SECURE_DELETE -DSQLITE_ENABLE_FTS3` | 0 errors out of 2012 tests |

Log lines from build A:

```
! fts5corrupt3-74.1 expected: [1 {unable to use function matchinfo in the requested context}]
! fts5corrupt3-74.1 got:      [1 {no such function: matchinfo}]
! fts5corrupt3-75.1 expected: [1 {unable to use function matchinfo in the requested context}]
! fts5corrupt3-75.1 got:      [1 {no such function: matchinfo}]
2 errors out of 2012 tests on ... Linux 64-bit little-endian
```

Limits: the `PRAGMA compile_options` check of these two builds was not recorded (the one-line
check printed nothing); that FTS3 was present in B is shown only indirectly by the changed result.
The builds had no coverage flags, unlike `run_config.py`.

## Conclusion

- The two errors are an **FTS5 × FTS3 interaction in the test suite**: the expected result of
  74.1/75.1 holds only when FTS3 is also compiled in, but the file is guarded only on FTS5.
  An `ifcapable fts3` guard on these two tests (or expecting either message) would remove them.
- In both builds SQLite returns an error for this query; only the message differs. This is
  **not** shown to be a defect in the library itself.
- Prediction for the pilot table (not verified until Mert's results are in): FTS3 is off in every
  row, so every row with FTS5 on (rows 3, 4, 5 of `configs/sqlite-pairwise.csv`) should show these
  two errors, and rows 1, 2, 6 should not (the file is skipped).
- Whether later SQLite versions changed these tests: **not verified**.
- For the model (task C): FTS3 is a candidate option whose pair with FTS5 is exercised by this
  test. The `ifcapable` map shows the FTS5 × FTS3 pair is also named together in
  `ext/fts5/test/fts5tok2.test` (`!fts5||!fts3`).
