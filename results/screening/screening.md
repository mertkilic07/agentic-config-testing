# Option screening (SQLite 3.46.1)

Each candidate was built alone with `scripts/screen_options.py` (fast build, no coverage) on a Linux x86_64 VM, 16 November 2026. Probe = small functional check; it prints 1 when the feature works.

| Candidate | Flags | Build | Reported by compile_options | Probe | main.test |
|---|---|---|---|---|---|
| SQLITE_ENABLE_FTS5 | `-DSQLITE_ENABLE_FTS5` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_ENABLE_RTREE | `-DSQLITE_ENABLE_RTREE` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_ENABLE_COLUMN_METADATA | `-DSQLITE_ENABLE_COLUMN_METADATA` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_SECURE_DELETE | `-DSQLITE_SECURE_DELETE` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_ENABLE_FTS3 | `-DSQLITE_ENABLE_FTS3` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_ENABLE_FTS4 | `-DSQLITE_ENABLE_FTS4` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_ENABLE_GEOPOLY | `-DSQLITE_ENABLE_GEOPOLY` | ok | True | ERROR: no such function: geopoly_area | 0 errors / 95 tests |
| SQLITE_ENABLE_STAT4 | `-DSQLITE_ENABLE_STAT4=1` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_ENABLE_DBSTAT_VTAB | `-DSQLITE_ENABLE_DBSTAT_VTAB` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_ENABLE_UPDATE_DELETE_LIMIT | `-DSQLITE_ENABLE_UPDATE_DELETE_LIMIT` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_DEFAULT_FOREIGN_KEYS | `-DSQLITE_DEFAULT_FOREIGN_KEYS=1` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_LIKE_DOESNT_MATCH_BLOBS | `-DSQLITE_LIKE_DOESNT_MATCH_BLOBS` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_OMIT_WAL | `-DSQLITE_OMIT_WAL` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_OMIT_AUTOVACUUM | `-DSQLITE_OMIT_AUTOVACUUM` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_ENABLE_NULL_TRIM | `-DSQLITE_ENABLE_NULL_TRIM` | ok | True | 1 | 0 errors / 95 tests |
| SQLITE_ENABLE_SORTER_REFERENCES | `-DSQLITE_ENABLE_SORTER_REFERENCES` | ok | True | 1 | 0 errors / 95 tests |
| GEOPOLY without RTREE | `-DSQLITE_ENABLE_GEOPOLY` | ok | - | ERROR: no such function: geopoly_area | 0 errors / 95 tests |
| GEOPOLY with RTREE | `-DSQLITE_ENABLE_GEOPOLY -DSQLITE_ENABLE_RTREE` | ok | - | 1 | 0 errors / 95 tests |
| OMIT_WAL, then PRAGMA journal_mode=WAL | `-DSQLITE_OMIT_WAL` | ok | - | delete | 0 errors / 95 tests |

## Findings

1. **Silent constraint: GEOPOLY requires RTREE.** With only `-DSQLITE_ENABLE_GEOPOLY` the build succeeds and `PRAGMA compile_options` reports `ENABLE_GEOPOLY`, but `geopoly_area()` does not exist. With RTREE also enabled it works. Reason in the source: the geopoly code is included from `ext/rtree/rtree.c` behind `#ifdef SQLITE_ENABLE_GEOPOLY`.
2. **Silent cross-level interaction: OMIT_WAL + `PRAGMA journal_mode=WAL`.** On a build with `-DSQLITE_OMIT_WAL`, requesting WAL at runtime gives no error; the pragma returns `delete` and the database stays in rollback-journal mode.
3. The other 15 candidates built alone, were reported by `compile_options`, passed their probe and `main.test` (0 errors / 95 tests). Passing alone does **not** prove they are free of constraints with each other.
