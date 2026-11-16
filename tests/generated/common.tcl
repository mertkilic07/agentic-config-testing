#=============================================================================
# common.tcl - shared setup for the LLM-generated tests in this folder
#=============================================================================
#
# Every generated test file starts with:
#
#     source [file join [file dirname [info script]] common.tcl]
#
# This loads SQLite's own test harness (test/tester.tcl), so the generated
# tests use exactly the same commands as SQLite's own tests:
#
#   do_execsql_test NAME SQL EXPECTED    run SQL, compare the result
#   do_catchsql_test NAME SQL EXPECTED   same, but an error is a result too
#   do_test NAME SCRIPT EXPECTED         run any Tcl script, compare result
#   ifcapable OPTION { ... }             run the block only if OPTION is
#                                        compiled into this build
#   reset_db                             start again with an empty test.db
#
# Requirement: the environment variable SQLITE_SRC must point to the SQLite
# source tree (in the Docker image: /opt/sqlite-src-3460100).
#
# How to run one file (from an empty working directory):
#
#     SQLITE_SRC=/opt/sqlite-src-3460100 path/to/testfixture gen_xxx.test
#=============================================================================

set testdir [file join $::env(SQLITE_SRC) test]
source $testdir/tester.tcl

# gen_file_contains FILENAME NEEDLE
#
# Returns 1 if the raw bytes of FILENAME contain the byte string NEEDLE,
# otherwise 0. Used to check whether deleted data is still physically
# present in the database file (secure_delete tests).
#
proc gen_file_contains {fname needle} {
  set fd [open $fname rb]
  set data [read $fd]
  close $fd
  expr {[string first $needle $data]>=0}
}

# gen_origins SQL
#
# Prepares SQL and returns, for every result column, the pair
#   {table-it-comes-from  column-it-comes-from}
# using sqlite3_column_table_name() and sqlite3_column_origin_name().
# Both functions exist only when SQLITE_ENABLE_COLUMN_METADATA is compiled
# in, so call this only inside "ifcapable columnmetadata".
#
proc gen_origins {sql} {
  set stmt [sqlite3_prepare_v2 db $sql -1 dummy]
  set res [list]
  for {set i 0} {$i < [sqlite3_column_count $stmt]} {incr i} {
    lappend res [sqlite3_column_table_name $stmt $i]
    lappend res [sqlite3_column_origin_name $stmt $i]
  }
  sqlite3_finalize $stmt
  set res
}
