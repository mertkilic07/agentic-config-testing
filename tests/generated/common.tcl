# Shared setup for LLM-generated tests. SQLITE_SRC must point to the SQLite source tree.
set testdir [file join $::env(SQLITE_SRC) test]
source $testdir/tester.tcl

# 1 if the raw bytes of file $fname contain $needle (a byte string), else 0.
proc gen_file_contains {fname needle} {
  set fd [open $fname rb]
  set data [read $fd]
  close $fd
  expr {[string first $needle $data]>=0}
}
