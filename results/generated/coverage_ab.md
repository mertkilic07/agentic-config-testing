# Coverage before / after adding the generated tests

**Before**: SQLite's own `quick.test` (counters of the runs in `results/acts/*-quick`, restored
from a copy). **After**: the same counters plus one run of the 6 files in
[tests/generated](../../tests/generated/) with the same `testfixture`. Coverage of `sqlite3.c`,
gcovr 8.3, same machine as the results table, 16–17 Nov 2026.

| Config | Options on | Lines before | Lines after | New lines | Functions before → after | Branches before → after | Generated-test errors |
|---|---|---|---|---|---|---|---|
| default | – | 46,792 / 48,926 | 46,792 | 0 | 2,524 → 2,524 | 29,791 → 29,791 | 0 (all skipped) |
| acts-01 | COLMETA, SECDEL | 46,817 / 48,959 | 46,817 | 0 | 2,529 → 2,529 | 29,786 → 29,788 | 0 |
| acts-02 | RTREE | 48,491 / 50,617 | 48,496 | 5 | 2,634 → 2,634 | 30,748 → 30,751 | 1 (`gen_rtree_secdel-1.5`) |
| acts-03 | FTS5, SECDEL | 56,399 / 58,665 | 56,399 | 0 | 3,108 → 3,108 | 36,059 → 36,061 | 0 |
| acts-04 | FTS5, RTREE, COLMETA | 58,078 / 60,387 | 58,083 | 5 | 3,225 → 3,225 | 36,994 → 36,997 | 1 (`gen_rtree_secdel-1.5`) |
| acts-05 | FTS5, COLMETA | 56,426 / 58,696 | 56,431 | 5 | 3,113 → 3,113 | 36,070 → 36,073 | 0 |
| acts-06 | RTREE, COLMETA, SECDEL | 48,516 / 50,650 | 48,523 | 7 | 2,639 → **2,640** | 30,744 → 30,755 | 2 (`gen_rtree_secdel-1.3`, `-1.5`) |

## What the new lines are

- **acts-06 (SECURE_DELETE compiled in):** `sqlite3PagerDontWrite()` and its call in
  `freePage2()` (`if( pPage && (pBt->btsFlags & BTS_SECURE_DELETE)==0 )`). In a build where
  secure_delete is on by default, SQLite's quick suite never frees a page with secure_delete
  switched **off** at runtime. The generated tests run both runtime values, so they reach this
  path. This is a compile-time × runtime gap: which runtime branch the existing tests cover
  depends on the compile-time default.
- **acts-02/04/05 (SECURE_DELETE not compiled in):** the secure-delete branch of
  `balance_nonroot()` (`BTS_FAST_SECURE`) and the `memset` in `zeroPage()`, reached by the
  generated tests that switch secure_delete **on** at runtime while deleting FTS5/R-tree data.

## Reading the numbers

- The gain is small (0–7 lines of about 50,000–60,000): the quick suite already covers about
  96 % of `sqlite3.c`, and the generated tests are 6 short files. The point of this iteration
  is *where* the new lines are (option-dependent branches) and the R-tree finding, not the
  percentage.
- Coverage only measures `sqlite3.c`; `ext/rtree` and FTS5 code are inside it in this build.
- The generated tests' own failures (`gen_rtree_secdel-1.3/1.5`) are the finding described in
  [tests/generated/README.md](../../tests/generated/README.md#5-finding-deleted-r-tree-entries-survive-secure_delete);
  they are intended to fail.
