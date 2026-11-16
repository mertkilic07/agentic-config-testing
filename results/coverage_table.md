| Configuration | Values | Scope | Build | Options check | Tests run | Errors | Line coverage | Lines covered / total | Function coverage |
|---|---|---|---|---|---|---|---|---|---|
| acts-01 | ENABLE_FTS5=off, ENABLE_RTREE=off, ENABLE_COLUMN_METADATA=on, SECURE_DELETE=on | test/quick.test | ok | ok | 615077 | 5 | 95.6% | 46,817 / 48,959 | 96.9% |
| acts-02 | ENABLE_FTS5=off, ENABLE_RTREE=on, ENABLE_COLUMN_METADATA=off, SECURE_DELETE=off | test/quick.test | ok | ok | 593195 | 5 | 95.8% | 48,491 / 50,617 | 97.1% |
| acts-03 | ENABLE_FTS5=on, ENABLE_RTREE=off, ENABLE_COLUMN_METADATA=off, SECURE_DELETE=on | test/quick.test | ok | ok | 755539 | 9 | 96.1% | 56,399 / 58,665 | 97.4% |
| acts-04 | ENABLE_FTS5=on, ENABLE_RTREE=on, ENABLE_COLUMN_METADATA=on, SECURE_DELETE=off | test/quick.test | ok | ok | 761095 | 9 | 96.2% | 58,078 / 60,387 | 97.5% |
| acts-05 | ENABLE_FTS5=on, ENABLE_RTREE=off, ENABLE_COLUMN_METADATA=on, SECURE_DELETE=off | test/quick.test | ok | ok | 758790 | 9 | 96.1% | 56,426 / 58,696 | 97.4% |
| acts-06 | ENABLE_FTS5=off, ENABLE_RTREE=on, ENABLE_COLUMN_METADATA=on, SECURE_DELETE=on | test/quick.test | ok | ok | 617349 | 5 | 95.8% | 48,516 / 50,650 | 97.1% |
| default | ENABLE_FTS5=off, ENABLE_RTREE=off, ENABLE_COLUMN_METADATA=off, SECURE_DELETE=off | test/quick.test | ok | ok | 590935 | 5 | 95.6% | 46,792 / 48,926 | 96.9% |

'Tests run' and 'Errors' are taken from the summary line of SQLite's Tcl test harness. Passed/skipped counts are not yet extracted reliably, so they are not reported.

## Failed tests per configuration

| Failing tests | Rows where they fail | Explanation |
|---|---|---|
| `recoverfault-1/2-oom-*` (4) | all 7, including default | Baseline failure, cause not established |
| `zipfile-6.0` (1) | all 7, including default | Timestamps differ by exactly 3600 s; likely time zone, **not verified** |
| `fts5corrupt3-74.1`, `-75.1` (2) | exactly the rows with `FTS5=on` (03, 04, 05) | Guarded only by `ifcapable fts5`, but expects the FTS3/4 `matchinfo()` error message. With FTS5 on and FTS3 off: `no such function: matchinfo` |
| `values-11.0`, `-11.1` (2) | exactly the rows with `FTS5=on` (03, 04, 05) | `test/values.test` line 383: block guarded by `ifcapable fts5` creates a table `USING fts3`. With FTS5 on and FTS3 off: `no such module: fts3` (**verified in the test source**) |

The last two rows are configuration-dependent failures of SQLite's own test suite: the tests
assume that FTS3 is available whenever FTS5 is. They only appear in configurations that
SQLite's standard test builds do not use (FTS5 on, FTS3 off).

Machine: Linux x86_64 cloud VM (2 cores), non-root user, SQLite 3.46.1, 16 Nov 2026.
Total run time of the 7 quick-suite runs: about 3.6 hours.
