# models/

| File | What it is |
|---|---|
| `sqlite-acts.txt` | ACTS input: the 4 compile-time options of the pilot model and their values |
| `sqlite-build-mapping.json` | How each option value becomes compiler flags (`OPTS=...`) and which `PRAGMA compile_options` entry proves it was applied |

## Pilot model (draft)

| Option | Values | `on` | `off` |
|---|---|---|---|
| `SQLITE_ENABLE_FTS5` | off, on | `-DSQLITE_ENABLE_FTS5` | not defined |
| `SQLITE_ENABLE_RTREE` | off, on | `-DSQLITE_ENABLE_RTREE` | not defined |
| `SQLITE_ENABLE_COLUMN_METADATA` | off, on | `-DSQLITE_ENABLE_COLUMN_METADATA` | not defined |
| `SQLITE_SECURE_DELETE` | off, on | `-DSQLITE_SECURE_DELETE` | not defined |

**Why "off" means "not defined":** in SQLite 3.46.1 all four macros are checked with
`#ifdef` / `#ifndef` (in `src/`, `ext/rtree/`, `ext/fts5/`). A definition such as
`-DSQLITE_ENABLE_FTS5=0` would still count as *defined* and would turn the feature on.

`testfixture`'s own build flags (`TESTFIXTURE_FLAGS` in `Makefile.in`) do not force any of
these four options, so the "off" rows really build without them. `scripts/run_config.py`
checks this after every build with `PRAGMA compile_options`.

## Status and limitations

- Constraints: none modelled yet. An empty list does **not** prove the options are
  independent; it has not been investigated.
- ACTS Basic 1.0 does not support constraints. If constraints are added, a
  constraint-capable workflow is needed (ACTS advanced version, or a documented
  filtering step). Constraints must never be dropped silently.
- This is a small pilot model, not a complete SQLite configuration model.
