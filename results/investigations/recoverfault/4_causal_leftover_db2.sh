#!/bin/bash
# Causal check: leftover test.db2 from recovercorrupt4.test, separate processes, same directory.
set -u
SRC=/opt/sqlite-src-3460100
for v in "a_nocov:-O0 -g:" "b_cov:-O0 -g --coverage -fprofile-update=atomic:--coverage"; do
  IFS=: read name cflags ldflags <<< "$v"
  b=$HOME/rf/$name
  if [ ! -x $b/testfixture ]; then rm -rf $b; mkdir -p $b; cd $b
    $SRC/configure --disable-shared CFLAGS="$cflags" LDFLAGS="$ldflags" > build.log 2>&1 && make -j"$(nproc)" testfixture >> build.log 2>&1; fi
  for mode in keep delete; do
    r=$HOME/rf/causal_${name}_$mode; rm -rf $r; mkdir -p $r; cp $b/testfixture $r/; cd $r
    ./testfixture $SRC/ext/recover/recovercorrupt4.test > corrupt4.log 2>&1
    left=$(cd testdir && ls test.db* | tr '\n' ' '); sz=$(stat -c %s testdir/test.db2)
    [ $mode = delete ] && rm -f testdir/test.db2
    ./testfixture $SRC/ext/recover/recoverfault.test > /out/g_${name}_$mode.test.log 2>&1
    echo "== $name $mode: files after recovercorrupt4=[$left] test.db2=${sz}B -> $(grep -E '[0-9]+ errors? out of' /out/g_${name}_$mode.test.log | cut -d' ' -f1-6) | $(grep -oE '^! recoverfault-[^ ]+' /out/g_${name}_$mode.test.log | tr '\n' ' ')"
  done
done
