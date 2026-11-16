# Glossary

Short definitions of the terms used in this repository, with SQLite examples.

**Configuration option**  
A setting that changes how a program is built or how it behaves. *Example:* "include full-text search (FTS5) or not".

**Compile-time option**  
Chosen before building; decides which code is in the program at all. *Example:* `-DSQLITE_ENABLE_FTS5`.

**Runtime option**  
Chosen while the program runs. *Example:* `PRAGMA journal_mode=WAL`.

**Configuration**  
One concrete choice for every option. *Example:* FTS5 on, R-tree off, ....

**Covering array (2-way)**  
A small set of configurations in which every pair of option values appears at least once. *Example:* 6 rows instead of 16 for 4 on/off options.

**ACTS**  
NIST's free tool that computes covering arrays. *Example:* `scripts/generate_acts.sh`.

**Constraint**  
A rule that some combinations are not allowed or do not do what was asked. *Example:* to be found by screening.

**Test suite**  
The tests written by the program's developers. *Example:* SQLite's Tcl tests (`test/*.test`).

**`testfixture`**  
SQLite's test program: a Tcl interpreter with SQLite built in. *Example:* built for every configuration.

**Code coverage**  
How much of the code the tests actually run. *Example:* "18.1% of the lines of `sqlite3.c`".

