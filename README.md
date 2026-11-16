<div align="center">

# Agentic Config Testing

**Can an AI agent find the configuration-option interactions that a program's own tests miss?**

ENS 491/492 Graduation Project · Sabancı University · Project #516

![System](https://img.shields.io/badge/system-SQLite%203.46.1-003B57)
![Covering arrays](https://img.shields.io/badge/covering%20arrays-NIST%20ACTS-6f42c1)
![Environment](https://img.shields.io/badge/environment-Docker-2496ED)
![Status](https://img.shields.io/badge/phase-2%20of%204-orange)

[What we did](#1-what-we-did) ·
[How](#2-how-we-did-it) ·
[Results](#3-results) ·
[Findings](#4-findings) ·
[AI-generated tests](#5-ai-generated-tests) ·
[Next](#6-what-is-next) ·
[Run it yourself](#run-it-yourself)

</div>

---

## 1. What we did

Configurable software can be built in thousands of ways, and some bugs appear only when
certain options are **combined**. Testing every combination is impossible, so two questions follow:

1. Which combinations do the program's own tests actually exercise?
2. Can an AI find the combinations they miss and write tests for them?

We study **SQLite 3.46.1** and four of its compile-time options:

| Option | What it adds |
|---|---|
| `SQLITE_ENABLE_FTS5` | full-text search tables |
| `SQLITE_ENABLE_RTREE` | spatial (rectangle) index tables |
| `SQLITE_ENABLE_COLUMN_METADATA` | functions that tell which table/column a query result comes from |
| `SQLITE_SECURE_DELETE` | deleted data is overwritten with zeros by default |

## 2. How we did it

```
 configuration model ──► NIST ACTS ──► 6 configurations ──► for each one:
 (4 options, on/off)     2-way           (instead of 16)        build SQLite
                         covering array                          check options really on (PRAGMA compile_options)
                                                                 run SQLite's OWN test suite (quick.test)
                                                                 measure code coverage (gcov/gcovr)
                                                                        │
                                                                        ▼
                                          results table ──► gap analysis ──► AI writes tests ──► before/after coverage
```

- **Covering array.** ACTS chose 6 configurations in which every on/off combination of every
  *pair* of options appears at least once (all 16 would be needed for every combination).
  → [configs/sqlite-pairwise.csv](configs/sqlite-pairwise.csv)
- **One command per configuration.** `scripts/run_config.py` builds, checks, tests and measures.
  → [docs/method.md](docs/method.md)
- **Same machine, same conditions** for all runs (Docker, Linux x86_64, non-root user).

## 3. Results

SQLite's own `quick` test suite on all 6 covering-array configurations plus the default build
(✓ = option on). Full table with failure causes: [results/coverage_table.md](results/coverage_table.md)

| Config | FTS5 | RTREE | COL_META | SEC_DEL | Tests run | Errors | Line coverage | Function coverage |
|---|:-:|:-:|:-:|:-:|--:|--:|--:|--:|
| default | | | | | 590,935 | 5 | 95.6% | 96.9% |
| acts-01 | | | ✓ | ✓ | 615,077 | 5 | 95.6% | 96.9% |
| acts-02 | | ✓ | | | 593,195 | 5 | 95.8% | 97.1% |
| acts-03 | ✓ | | | ✓ | 755,539 | **9** | 96.1% | 97.4% |
| acts-04 | ✓ | ✓ | ✓ | | 761,095 | **9** | 96.2% | 97.5% |
| acts-05 | ✓ | | ✓ | | 758,790 | **9** | 96.1% | 97.4% |
| acts-06 | | ✓ | ✓ | ✓ | 617,349 | 5 | 95.8% | 97.1% |

- Every build succeeded, and every option was confirmed to be really on or off.
- The options change **which tests run**: about 590k tests without FTS5, up to 761k with it.
- 5 errors appear in **every** configuration, so they are not caused by the options
  (explained in [Findings](#4-findings), 4.4).
- 4 extra errors appear **only** where FTS5 is on (finding 4.1).

## 4. Findings

### 4.1 SQLite's own tests break when FTS5 is on and FTS3 is off &nbsp;·&nbsp; *found by the covering array*

`fts5corrupt3-74.1/75.1` and `values-11.0/11.1` fail in exactly the three FTS5 configurations.
The tests check only "is FTS5 there?", but they also use FTS3 features. SQLite's developers
always build FTS3 and FTS5 together, so they never see this combination.

Verified: adding FTS3 to the build removes the errors; the wrong guard is visible in the test
source (`test/values.test:383`). → [details](tests/existing/fts5corrupt3-matchinfo.md)

### 4.2 Deleted R-tree data survives `secure_delete` &nbsp;·&nbsp; *found by the AI-generated tests*

With `secure_delete` on, SQLite promises to overwrite deleted data with zeros. For FTS5 this
works. For an R-tree, the deleted entry **stays in the database file** and can even be read
back with SQL from the R-tree's internal table.

Cause: `nodeDeleteCell()` (`ext/rtree/rtree.c:834`) never clears the slot it frees. With the
compile-time option, this shows up **only in acts-06**, the one configuration with both
RTREE and SECURE_DELETE. No existing SQLite test covers this pair.
Whether SQLite's developers regard it as a defect: *not verified*.
→ [details](tests/generated/README.md#5-finding-deleted-r-tree-entries-survive-secure_delete)

### 4.3 Two silent constraints &nbsp;·&nbsp; *found by option screening*

The build or the setting succeeds and nothing reports an error, but the feature is missing:

| Combination | What happens |
|---|---|
| `ENABLE_GEOPOLY` without `ENABLE_RTREE` | builds, is reported as enabled, but no geopoly function exists |
| `OMIT_WAL` (compile time) + `PRAGMA journal_mode=WAL` (runtime) | no error; SQLite silently keeps the old journal mode |

→ [screening of 16 options](results/screening/screening.md)

### 4.4 The errors in every configuration are test-suite noise

The 4 `recoverfault` errors come from test order: one test file leaves a corrupt database file
that the next one reuses. Deleting that file between them removes the errors.
→ [investigation](results/investigations/recoverfault/README.md).
The remaining error (`zipfile-6.0`, a 1-hour timestamp difference) is probably a time-zone effect, *not verified*.

## 5. AI-generated tests

| Step | Result |
|---|---|
| **Find the gaps** | We mapped every SQLite test to the options it depends on ([`ifcapable` map](tests/existing/ifcapable-map.md)). **5 of the 6 option pairs** are never tested together. |
| **Write tests** | An LLM wrote 6 test files in SQLite's own test format, one per gap, plus FTS5 × FTS3. → [tests/generated](tests/generated/) |
| **Validate** | Every file was run on all 7 configurations. 2 tests were wrong at first (the LLM's mistake) and were corrected; this is recorded, not hidden. |
| **Find** | The R-tree / secure_delete behaviour (finding 4.2). |
| **Measure** | Coverage before vs. after adding the tests: +0 to +7 lines per configuration. The gain is small because SQLite's tests already cover about 96%, but the new lines are **option-dependent branches**. For example, in a SECURE_DELETE build SQLite's tests never run the "secure_delete switched off" code path. → [before/after](results/generated/coverage_ab.md) |

In this first round the AI worked step by step in a session; it is not yet an autonomous agent.

## 6. What is next

- [x] **Phase 1:** experiment infrastructure, ACTS, results table for all configurations
- [x] First gap analysis and AI-generated tests, with before/after coverage
- [ ] Bigger model: 10–15 options with constraints (for example, GEOPOLY requires RTREE)
- [ ] **Phase 3:** an autonomous agent loop (find gap → write test → run → revise)
- [ ] **Phase 4:** evaluation: how many real gaps are found, how many generated tests are valid, coverage gain

---

## Run it yourself

Requirements: [Docker Desktop](https://www.docker.com/products/docker-desktop/) and git.

```sh
git clone https://github.com/mertkilic07/agentic-config-testing.git
cd agentic-config-testing
docker build -t ens491-sqlite .
docker run --rm -it -v "$PWD:/work" ens491-sqlite      # Windows PowerShell: -v "${PWD}:/work"
python3 scripts/run_config.py --row 1 --scope main     # inside the container: smoke test, ~1 minute
```

| Goal | Command |
|---|---|
| Generate the covering array | `bash scripts/generate_acts.sh` |
| Run one configuration | `python3 scripts/run_config.py --row 3 --scope quick` |
| Run all configurations / the default build | `--all` / `--default` instead of `--row N` |
| Build the results table | `python3 scripts/make_table.py --scope quick > results/coverage_table.md` |
| Screen new candidate options | `python3 scripts/screen_options.py` |
| Map existing tests to options | `python3 scripts/map_ifcapable.py --json tests/existing/ifcapable-map.json --md tests/existing/ifcapable-map.md` |

`--scope main` takes seconds (95 tests); `--scope quick` takes 25–40 minutes per configuration.

<details>
<summary><b>Repository structure</b></summary>

```
.
├── Dockerfile            # pinned environment: SQLite 3.46.1, Tcl, gcovr, Java, ACTS
├── configs/              # covering arrays generated by ACTS
├── docs/                 # progress report, method, system selection, glossary, team tasks
├── models/               # configuration model, ACTS input, option-to-flag mapping
├── prototypes/           # earlier PRAGMA prototype (historical)
├── results/              # results table, per-run folders, screening, investigations, generated-test coverage
├── scripts/              # ACTS, runner, screening, results table, ifcapable map
└── tests/
    ├── existing/         # which existing SQLite tests depend on which option
    └── generated/        # AI-generated tests for untested option pairs
```
</details>

<details>
<summary><b>All documents</b></summary>

| Document | Contents |
|---|---|
| [Progress report](docs/progress.md) | The full project story, timeline and problems |
| [Method](docs/method.md) | How the pipeline works, known open issues |
| [System selection](docs/selection.md) | Why SQLite, and why not BusyBox or ZooKeeper (with sources) |
| [Candidate systems](docs/candidates.md) | First comparison of candidate systems |
| [Glossary](docs/glossary.md) | Terms used in this project |
| [Team tasks](docs/team-tasks.md) | Who did and does what |
</details>

## Team

**Mert Can Kılıç** · **Tuna Erol** · **Mehmet Emre Tekeşin**
Advisor: **Prof. Cemal Yılmaz**
