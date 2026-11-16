#!/bin/bash
# Default build (no OPTS), twice: without and with coverage flags. Run only ext/recover/recoverfault.test.
set -u
SRC=/opt/sqlite-src-3460100
for v in "a_nocov:-O0 -g:" "b_cov:-O0 -g --coverage -fprofile-update=atomic:--coverage"; do
  IFS=: read name cflags ldflags <<< "$v"
  b=$HOME/rf/$name; rm -rf $b; mkdir -p $b; cd $b
  $SRC/configure --disable-shared CFLAGS="$cflags" LDFLAGS="$ldflags" > build.log 2>&1 && make -j"$(nproc)" testfixture >> build.log 2>&1
  echo "== $name CFLAGS=[$cflags] LDFLAGS=[$ldflags] build_rc=$?"
  mkdir -p run && cp testfixture run/ && cd run
  echo 'sqlite3 db :memory:; puts [db eval {PRAGMA compile_options}]; db close' > co.tcl; ./testfixture co.tcl > /out/$name.compile_options.txt 2>&1
  echo "compile_options: $(wc -w < /out/$name.compile_options.txt) entries"
  timeout 1800 ./testfixture $SRC/ext/recover/recoverfault.test > /out/$name.test.log 2>&1
  echo "test_rc=$?"; grep -E "errors out of|^! " /out/$name.test.log | head -12
done
