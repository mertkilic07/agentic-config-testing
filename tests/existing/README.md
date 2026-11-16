# Existing tests per option (task E)

Which of SQLite's own Tcl tests depend on which compile-time option, from the `ifcapable`
guards in the test sources (SQLite 3.46.1). Static scan, produced by
`scripts/map_ifcapable.py` inside the Docker image:

```sh
python3 scripts/map_ifcapable.py --src /opt/sqlite-src-3460100 \
    --json tests/existing/ifcapable-map.json --md tests/existing/ifcapable-map.md
```

| File | Contents |
|---|---|
| [ifcapable-map.md](ifcapable-map.md) | Table option → keyword → number of guarded files (file-level / block-level, on / off), pilot-pair table, all keywords |
| `ifcapable-map.json` | Every guard: file, line, expression, kind, polarity per keyword, quick-suite membership |
| [fts5corrupt3-matchinfo.md](fts5corrupt3-matchinfo.md) | Check of the acts-03 errors `fts5corrupt3-74.1/75.1` (FTS5 × FTS3, executed) |

## Main points

1. **The keyword is not always the option name.** From `src/test_config.c`:
   COLUMN_METADATA → `columnmetadata`; LIKE_DOESNT_MATCH_BLOBS → `like_match_blobs`
   (inverted); OMIT_WAL → `wal` and OMIT_AUTOVACUUM → `autovacuum` (inverted: 1 when the option
   is *off*). **No keyword exists** for ENABLE_FTS4, ENABLE_DBSTAT_VTAB, DEFAULT_FOREIGN_KEYS and
   ENABLE_SORTER_REFERENCES, so their tests cannot be found through `ifcapable`.
2. **The grep in `docs/team-tasks.md` undercounts.** It reads only `test/*.test`, but `quick`
   also runs `ext/fts5/test`, `ext/rtree`, `ext/session`, `ext/rbu`, `ext/recover`, `ext/intck`,
   `ext/expert` and `ext/lsm1/test` (`test/permutations.test:91-103`). It also ignores polarity
   (`!x`) and substrings (`fts4` matches `fts4_deferred`). Same source, same keywords:

   | Keyword | grep `ifcapable.*k` in `test/*.test` | this map (all `*.test`) |
   |---|---|---|
   | `fts5` | 15 | 150 |
   | `rtree` | 12 | 41 |
   | `geopoly` | 0 | 1 |
   | `fts4` | 8 | 0 (no such keyword) |

   Nine FTS5 files skip themselves through the helper `return_if_no_fts5`
   (`ext/fts5/test/fts5_common.tcl`), not through `ifcapable`; the map counts these.
3. **The pilot options are guarded very unevenly** (quick-suite files): FTS5 146, RTREE 38,
   COLUMN_METADATA 3, SECURE_DELETE 3.
4. **Of the 6 pilot pairs, only FTS5 × RTREE is named together** in a guard (2 files:
   `ext/rbu/rbudiff.test`, `test/vtabK.test`). The other 5 pairs never appear together in a guard.
   This says nothing yet about whether a pair's interaction is *tested*; that is Phase 2.
5. **First confirmed test-suite interaction:** `fts5corrupt3-74.1/75.1` need FTS3 as well as FTS5
   but are guarded only on FTS5. Reproduced: FTS5+SECURE_DELETE → 2 errors, + FTS3 → 0 errors.
   Details in [fts5corrupt3-matchinfo.md](fts5corrupt3-matchinfo.md).

## Limits

- Static scan: guards built at run time, `if {[permutation]==...}` checks and checks inside
  helper `.tcl` files (other than `return_if_no_*`) are not counted.
- A guard shows which tests are *skipped*; it does not prove the remaining tests exercise the
  option, or that unguarded tests do not depend on it (point 5 is a counterexample).
- The quick-suite list (1313 files) is identical to the output of SQLite's own `test_set` code run
  in `tclsh` (unix, no `QUICKTEST_*` variables), but has **not** been checked against a quick-run log.
