#!/bin/bash
# Default build without coverage; run recoverfault.test through the quick suite harness only.
set -u
SRC=/opt/sqlite-src-3460100
b=$HOME/rf/a_nocov; rm -rf $b; mkdir -p $b; cd $b
$SRC/configure --disable-shared CFLAGS="-O0 -g" > build.log 2>&1 && make -j"$(nproc)" testfixture >> build.log 2>&1
mkdir -p run && cp testfixture run/ && cd run
timeout 1800 ./testfixture $SRC/test/permutations.test quick recoverfault.test > /out/c_quick_only.test.log 2>&1
echo "permutations quick recoverfault.test: rc=$?"; grep -E "errors out of|^! " /out/c_quick_only.test.log | head -12
