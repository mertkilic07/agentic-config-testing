#!/bin/bash
# Default build without coverage; quick suite restricted by SQLITE_TEST_PATTERN_LIST.
# Usage: run3.sh LABEL "pattern list"
set -u
SRC=/opt/sqlite-src-3460100
b=$HOME/rf/a_nocov
if [ ! -x $b/testfixture ]; then rm -rf $b; mkdir -p $b; cd $b
  $SRC/configure --disable-shared CFLAGS="-O0 -g" > build.log 2>&1 && make -j"$(nproc)" testfixture >> build.log 2>&1; fi
shift 0
while [ $# -ge 2 ]; do
  label=$1; pats=$2; shift 2
  r=$HOME/rf/run_$label; rm -rf $r; mkdir -p $r; cp $b/testfixture $r/; cd $r
  start=$(date +%s)
  SQLITE_TEST_PATTERN_LIST="$pats" timeout 3000 ./testfixture $SRC/test/permutations.test quick > /out/$label.test.log 2>&1
  echo "== $label patterns=[$pats] rc=$? seconds=$(( $(date +%s)-start ))"
  grep -E "errors out of|^! " /out/$label.test.log | head -8
done
