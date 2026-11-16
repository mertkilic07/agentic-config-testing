# System selection: SQLite

Written 16 November 2026 (Emre, task D). This page records **why we study SQLite** and why we
do **not** study BusyBox or Apache ZooKeeper, against the criteria of
[candidates.md](candidates.md). Every claim is marked:

- **Measured**: we ran it (environment named);
- **Source**: read in the system's own source or documentation (file and line given);
- **Not verified**: plausible, but not checked.

Versions read: SQLite 3.46.1 (`sqlite-src-3460100.zip`, as in the Dockerfile),
BusyBox 1.36.1 (latest stable release; `busybox-1.36.1.tar.bz2` from busybox.net, SHA-256
checked against the published `.sha256`), ZooKeeper `release-3.9.7` (tag in the official
`apache/zookeeper` repository). Nothing was built or run for BusyBox or ZooKeeper.

## Decision

We study **SQLite 3.46.1, compile-time options**. It is the only candidate for which the whole
pipeline the advisor asked for (ACTS covering array → build → own test suite → per-configuration
outcomes and coverage) already runs end to end, and its tests contain a machine-readable link
from tests to options (`ifcapable`). BusyBox is a credible second choice; ZooKeeper is the
weakest fit for the current method.

## Comparison against the selection criteria

| Criterion | SQLite | BusyBox | ZooKeeper |
|---|---|---|---|
| Options with finite domains | Compile-time macros, defined / not defined; 16 screened, all built alone (**measured**) | 1078 Kconfig entries: 1022 `bool`, 26 `int`, 25 `string` (**source**, counted in `Config.src`/`Config.in` and `//config:` blocks) | 186 documented options in the admin guide, many numeric (e.g. `tickTime` in ms, `initLimit`/`syncLimit` in ticks) (**source**, `zookeeperAdmin.md:591, 1298, 1365`) |
| Dependencies / constraints | Mostly undeclared; two **silent** constraints found by screening (**measured**) | Declared: 588 `depends on`, 50 `select` (**source**) | Some described in prose (e.g. `initLimit` in units of `tickTime`) (**source**); no machine-readable list found (**not verified**) |
| Own test suite | Tcl suite in the source tree; `quick` = 1313 files, 755,539 test cases on acts-03 (**measured**) | `make check` → `testsuite/runtest`: 65 `*.tests` (699 `testing` calls) + 41 old-style dirs (164 files) (**source**); shell suites `shell/ash_test` (335), `shell/hush_test` (357) have their own `run-all` and are not called by `make check` (**source**) | JUnit/Maven; 341 `*Test.java` classes in `zookeeper-server` (65 under `quorum/`) (**source**, tag tree) |
| Tests aware of the configuration | `ifcapable` guards with keywords from `src/test_config.c` (**source**, see `tests/existing` on branch `task-e-ifcapable-map`) | Yes: `runtest` exports the `CONFIG_*` names of `.config` as `OPTIONFLAGS` (`testsuite/runtest:135-138`); `optional X` skips a test if `X` is not set (`testsuite/testing.sh:55-65`); tests of applets not built are `SKIPPED`/`UNTESTED` (`runtest:23-33, 152`) (**source**) | Configuration is written by the test fixtures themselves (see below) (**source**) |
| Effective configuration can be checked | `PRAGMA compile_options` (**measured**; but it reports `ENABLE_GEOPOLY` even when geopoly does not work, so it shows the macros, not the features) | `.config` of the build (**source**); a runtime check like `compile_options` not found (**not verified**) | Server logs / four-letter-word `conf` command (**not verified**) |
| Coverage | gcov + gcovr on `sqlite3.c`, 96.1 % lines on acts-03 quick (**measured**) | No coverage support in the build files (`Makefile*`, `scripts/Makefile*`: no `gcov`/`--coverage`/`-fprofile`) (**source**); adding `--coverage` through `CFLAGS` is probably possible (**not verified**) | OpenClover profile in the root POM (`pom.xml:448-507`) (**source**); not run (**not verified**) |
| Cost per configuration | Build 22 s, `quick` 38 min with coverage, Linux x86_64 VM (**measured**, `results/acts/acts-03-quick/summary.json`) | Not measured | No rebuild for runtime options; test time not measured (**not verified**) |
| Team experience | PRAGMA prototype, now the full pipeline | None | None |

## Why SQLite

1. **The pipeline works.** One command builds a configuration with coverage, checks the options,
   runs SQLite's own tests and measures coverage (`scripts/run_config.py`; acts-03 result in
   `docs/progress.md` §5).
2. **Tests are linked to options.** `ifcapable EXPR` (`test/tester.tcl:1745`) skips code unless
   the option keywords set in `src/test_config.c` are true. This gives the test-gap analysis
   (phase 2) a ground truth for which tests *depend on* an option. Measured on branch
   `task-e-ifcapable-map`: FTS5 is named in guards of 146 quick-suite files, RTREE in 38.
3. **Configuration problems are visible in the output.** The pipeline already found two silent
   constraints (GEOPOLY needs RTREE; OMIT_WAL + `journal_mode=WAL`) and one confirmed test-suite
   interaction (`fts5corrupt3-74.1/75.1` need FTS3 as well as FTS5; reproduced on branch
   `task-e-ifcapable-map`). These are the kind of interactions the agent is meant to find.
4. **Two configuration levels.** Compile-time macros and runtime `PRAGMA`s; the OMIT_WAL finding
   crosses the two, which keeps a later runtime extension of the model possible.
5. **Each configuration is self-contained.** One process, one directory, no network, no ports;
   builds are short (22 s measured).

## Why not BusyBox

BusyBox's strengths should be stated: its test harness *is* configuration-aware (`OPTIONFLAGS`,
`optional`), and its dependencies are declared (`depends on`, `select`), which SQLite's are not.
We still prefer SQLite, because:

1. **The model would be almost entirely Kconfig `bool` options with many declared dependencies**
   (1022 of 1078 entries `bool`; 588 `depends on`, 50 `select`) (**source**). A coherent subset
   must be chosen and every dependency inside it must become an ACTS constraint. ACTS Basic, the
   version we have, has no constraint support (`models/README.md`), so most rows would have to be
   repaired by hand. We have not tried to choose such a subset (**not verified** how many
   constraints a 10–15 option subset would need).
2. **No coverage support in the build** (**source**: no coverage flags in any Makefile).
   Coverage would have to be added and validated by us (**not verified** that `CFLAGS=--coverage`
   works with its build).
3. **The test suite is small and partly split.** `make check` runs 65 new-style files (699
   `testing` calls) and 164 old-style test files (**source**). The two shell suites
   (692 files) have separate runners and are not part of `make check` (**source**). SQLite's
   `quick` run alone executed 755,539 test cases (**measured**). Test counts are not directly
   comparable (a SQLite "test" is often one SQL statement), so this is an indication only.
4. **Hand-written configuration checks in tests can silently disable them.**
   `testsuite/ash.tests:11-13` tests `x"CONFIG_SCRIPT" = x"y"` (without `$`): the literal string
   never equals `y`, so the file exits at line 11 without running its tests. Found by reading
   only, **not verified** by running.
5. **No team experience** with BusyBox's build; the feasibility steps of `candidates.md`
   (build, run tests, collect outcomes and coverage) were not done (**not verified**).

## Why not Apache ZooKeeper

ZooKeeper has strengths too: it needs no rebuild per configuration (runtime options), and it has
a coverage profile (OpenClover) in its build (**source**). We still exclude it, because:

1. **The tests choose their own configuration.** The standalone test base starts servers with a
   fixed `tickTime` of 3000 ms (`zookeeper-server/src/test/java/org/apache/zookeeper/test/ClientBase.java:423`,
   `new ZooKeeperServer(dataDir, dataDir, 3000)`), and the quorum test base writes `zoo.cfg` with
   `initLimit=10`, `syncLimit=5` and `tickTime=4000`
   (`.../server/quorum/QuorumPeerTestBase.java:126-129, 215-218`) (**source**). A configuration
   from a covering array would not reach these tests without changing the fixtures, i.e. without
   changing the system's own test suite.
2. **Only some options can be injected from outside.** The admin guide names a Java system
   property for 117 option entries ("Java system property:" or "properties:") and states "No Java system property" for 16
   (`zookeeperAdmin.md`), among them `initLimit`, `syncLimit` and `maxClientCnxns` (**source**).
   System properties could be passed to all test JVMs through Surefire's `argLine`
   (`zookeeper-server/pom.xml:280`), but whether test-created servers then use them, or tests
   override them, is **not verified**.
3. **Numeric options need chosen value sets.** `tickTime`, `initLimit`, `syncLimit`,
   `maxClientCnxns`, `snapCount` and many others are numbers (**source**); ACTS needs a small
   justified set of values per option, and timing options interact with test timeouts
   (`CONNECTION_TIMEOUT = 30000` in `ClientBase.java:73`) (**source**; effect **not verified**).
4. **Multi-server tests are slow and timing-dependent.** 65 of the 341 server test classes are in
   `quorum/` (**source**); the build runs tests in 8 forked JVMs without fork reuse
   (`pom.xml:549`, `zookeeper-server/pom.xml:278-280`) (**source**). Run time and flakiness were
   **not measured** (**not verified**).

## Why not curl

curl is studied by the other project group. We use their work only as a methodological reference
(model documentation, per-configuration reporting, before/after evaluation); their code and
measurements are not ours (`candidates.md`).

## Risks of choosing SQLite

- **Long runs:** the `quick` suite takes 30–60 minutes per configuration with coverage (38 min
  measured for acts-03); a larger covering array costs hours per run.
- **Undeclared constraints:** SQLite does not declare most option dependencies; they must be found
  by screening, as with GEOPOLY → RTREE. Some may still be missing from the model.
- **Not every option has an `ifcapable` keyword:** ENABLE_FTS4, ENABLE_DBSTAT_VTAB,
  DEFAULT_FOREIGN_KEYS and ENABLE_SORTER_REFERENCES have none (`src/test_config.c`), so tests
  depending on them cannot be found through guards.
- **Baseline noise in the test suite:** 4 `recoverfault` errors in every run are a test-order
  dependency (`recovercorrupt4.test` leaves a corrupt `test.db2`), not an option interaction
  (branch `task-f-recoverfault`). Such errors must be separated from interaction effects.
- **TH3** (SQLite's proprietary test harness) is not available to us; we use only the public Tcl
  tests.

## Sources

SQLite 3.46.1: `test/tester.tcl`, `src/test_config.c`, `test/permutations.test`; project
results in `docs/progress.md`, `results/screening/screening.md`, `results/acts/`.

BusyBox 1.36.1 (https://busybox.net/downloads/busybox-1.36.1.tar.bz2,
SHA-256 `b8cc24c9574d809e7279c3be349795c5d5ceb6fdf19ca709f80cde50e47de314`):
`testsuite/runtest`, `testsuite/testing.sh`, `testsuite/ash.tests`,
`Makefile.custom:71-75` (`check test:` target), `Config.in` / `Config.src` / `//config:` blocks;
FAQ: https://busybox.net/FAQ.html ("How do I configure Busybox?").

Apache ZooKeeper `release-3.9.7` (https://github.com/apache/zookeeper/tree/release-3.9.7):
`pom.xml`, `zookeeper-server/pom.xml`,
`zookeeper-server/src/test/java/org/apache/zookeeper/test/ClientBase.java`,
`zookeeper-server/src/test/java/org/apache/zookeeper/server/quorum/QuorumPeerTestBase.java`,
`zookeeper-docs/src/main/resources/markdown/zookeeperAdmin.md`.

NIST ACTS: see `models/README.md` and `candidates.md`.
