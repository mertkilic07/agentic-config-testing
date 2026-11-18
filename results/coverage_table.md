| Configuration | Values | Scope | Build | Options check | Tests run | Passed | Failed | Skipped | Line coverage | Lines covered / total | Function coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| acts-01 | ENABLE_FTS5=off, ENABLE_RTREE=off, ENABLE_COLUMN_METADATA=on, SECURE_DELETE=on | test/quick.test | ok | ok | 615,077 | 615,071 | 5 | n/a | 95.6% | 46,817 / 48,959 | 96.9% |
| acts-02 | ENABLE_FTS5=off, ENABLE_RTREE=on, ENABLE_COLUMN_METADATA=off, SECURE_DELETE=off | test/quick.test | ok | ok | 593,195 | 593,189 | 5 | n/a | 95.8% | 48,491 / 50,617 | 97.1% |
| acts-03 | ENABLE_FTS5=on, ENABLE_RTREE=off, ENABLE_COLUMN_METADATA=off, SECURE_DELETE=on | test/quick.test | ok | ok | 755,539 | 755,529 | 9 | n/a | 96.1% | 56,399 / 58,665 | 97.4% |
| acts-04 | ENABLE_FTS5=on, ENABLE_RTREE=on, ENABLE_COLUMN_METADATA=on, SECURE_DELETE=off | test/quick.test | ok | ok | 761,095 | 761,085 | 9 | n/a | 96.2% | 58,078 / 60,387 | 97.5% |
| acts-05 | ENABLE_FTS5=on, ENABLE_RTREE=off, ENABLE_COLUMN_METADATA=on, SECURE_DELETE=off | test/quick.test | ok | ok | 758,790 | 758,780 | 9 | n/a | 96.1% | 56,426 / 58,696 | 97.4% |
| acts-06 | ENABLE_FTS5=off, ENABLE_RTREE=on, ENABLE_COLUMN_METADATA=on, SECURE_DELETE=on | test/quick.test | ok | ok | 617,349 | 617,343 | 5 | n/a | 95.8% | 48,516 / 50,650 | 97.1% |
| default | ENABLE_FTS5=off, ENABLE_RTREE=off, ENABLE_COLUMN_METADATA=off, SECURE_DELETE=off | test/quick.test | ok | ok | 590,935 | 590,929 | 5 | n/a | 95.6% | 46,792 / 48,926 | 96.9% |

'Tests run' and 'Failed' are the two numbers of the harness summary line "N errors out of M tests". **Passed** = Tests run - Failed - 1: the harness counts every executed test (`do_test` calls `incr_ntest`) plus one extra count when it finishes (`finalize_testing`, `test/tester.tcl:1298`), and every failure is one of the executed tests (`fail_test`). **Skipped** is not reported because SQLite's harness does not count it: `ifcapable` (`test/tester.tcl:1745`) simply does not run the guarded code, and the only "Omitted" list is for tests filtered out by name. The effect of skipping shows in 'Tests run', which changes with the configuration (about 591k without FTS5, up to 761k with it).

## Failed tests per configuration

| Failing tests | Rows where they fail | Explanation |
|---|---|---|
| `recoverfault-1/2-oom-*` (4) | all 7, including default | Test-order dependency in SQLite's suite: `recovercorrupt4.test` leaves a corrupt `test.db2` that `recoverfault.test` reuses ([investigation](investigations/recoverfault/README.md)) |
| `zipfile-6.0` (1) | all 7, including default | Timestamps differ by exactly 3600 s; likely time zone, **not verified** |
| `fts5corrupt3-74.1`, `-75.1` (2) | exactly the rows with `FTS5=on` (03, 04, 05) | Guarded only by `ifcapable fts5`, but expects the FTS3 `matchinfo()` error message. With FTS5 on and FTS3 off: `no such function: matchinfo` (**verified**: adding FTS3 removes the errors, [details](../tests/existing/fts5corrupt3-matchinfo.md)) |
| `values-11.0`, `-11.1` (2) | exactly the rows with `FTS5=on` (03, 04, 05) | `test/values.test` line 383: block guarded by `ifcapable fts5` creates a table `USING fts3`. With FTS5 on and FTS3 off: `no such module: fts3` (**verified in the test source**) |

The last two rows are configuration-dependent failures of SQLite's own test suite: the tests
assume that FTS3 is available whenever FTS5 is. They only appear in configurations that
SQLite's standard test builds do not use (FTS5 on, FTS3 off).

Machine: Linux x86_64 cloud VM (2 cores), non-root user, SQLite 3.46.1, 16 Nov 2026.
Total run time of the 7 quick-suite runs: about 3.6 hours.
