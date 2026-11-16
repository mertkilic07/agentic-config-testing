# results/

One folder per run: `results/acts/acts-<row>-<scope>/`

| File | Committed | Contents |
|---|---|---|
| `summary.json` | yes | values of the ACTS row, build status and flags, effective-option check, test summary, coverage summary, machine and timing |
| `compile-options.txt` | yes | `PRAGMA compile_options` of the built `testfixture` |
| `coverage/summary.json`, `coverage/gcovr.log` | yes | gcovr output for `sqlite3.c` |
| `build.log`, `tests.log` | no (too large) | full build and test output, kept on the machine that ran it |

`coverage_table.md` is generated with `python3 scripts/make_table.py`.

Never mix aborted or diagnostic runs into the table: re-run the configuration instead.
