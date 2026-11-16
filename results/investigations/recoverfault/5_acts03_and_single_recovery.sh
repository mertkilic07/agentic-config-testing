#!/bin/bash
# (1) acts-03 options with coverage: iteration numbers of the failure.
# (2) one recovery into the leftover test.db2 without fault injection: error code/message.
set -u
SRC=/opt/sqlite-src-3460100
b=$HOME/rf/acts03cov; mkdir -p $b; cd $b
$SRC/configure --disable-shared CFLAGS="-O0 -g --coverage -fprofile-update=atomic" LDFLAGS="--coverage" > build.log 2>&1 && make -j"$(nproc)" testfixture OPTS="-DSQLITE_ENABLE_FTS5 -DSQLITE_SECURE_DELETE" >> build.log 2>&1
r=$HOME/rf/acts03_keep; mkdir -p $r; cp testfixture $r/; cd $r
./testfixture $SRC/ext/recover/recovercorrupt4.test > corrupt4.log 2>&1
./testfixture $SRC/ext/recover/recoverfault.test > /out/h_acts03cov_keep.test.log 2>&1
echo "== acts03 opts + coverage, keep: $(grep -E '[0-9]+ errors? out of' /out/h_acts03cov_keep.test.log | cut -d' ' -f1-6) | $(grep -oE '^! recoverfault-[^ ]+' /out/h_acts03cov_keep.test.log | sort -u | tr '\n' ' ')"
r=$HOME/rf/one; mkdir -p $r/testdir; cp $b/testfixture $r/; cd $r
./testfixture $SRC/ext/recover/recovercorrupt4.test > /dev/null 2>&1
cd testdir
cat > one.tcl <<'TCL'
sqlite3 db test.db
db eval { CREATE TABLE t1(a INTEGER PRIMARY KEY, b, c); INSERT INTO t1 VALUES(1, 2, 3); }
set R [sqlite3_recover_init db main test.db2]
set rc [catch {$R run} r1]
puts "run: rc=$rc result=$r1 errcode=[$R errcode] errmsg=[$R errmsg]"
set rc [catch {$R finish} r2]
puts "finish: rc=$rc result=$r2"
TCL
echo "== single recovery into leftover test.db2 ($(stat -c %s test.db2) bytes):"; ../testfixture one.tcl 2>&1
