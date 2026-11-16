#!/usr/bin/env python3
"""Map SQLite's own Tcl tests to the options they are guarded by (`ifcapable`).

SQLite's tests skip code with `ifcapable EXPR {BODY} ?else {ELSE}?` (proc in test/tester.tcl).
EXPR uses keywords from the Tcl array ::sqlite_options (set in src/test_config.c), combined
with `!`, `&&`, `||` and parentheses. This script reads every *.test file under test/ and
ext/ and, for each `ifcapable` and `[capable ...]` it finds, records:

  - the keywords in EXPR and, per keyword, its polarity:
      "needs_on"  : the guarded code runs only when the option is present,
      "needs_off" : the guarded code runs only when the option is absent,
      "mixed"     : polarity cannot be decided from the expression alone;
    For "file" guards the polarity describes the REST OF THE FILE (the tests that run),
    i.e. it is the negation of EXPR: `ifcapable !fts5 {finish_test; return}` -> fts5 needs_on.
  - the kind of guard:
      "file"  : BODY contains `finish_test` and `return` -> the rest of the file is skipped,
      "block" : BODY is a block of tests (or other code) that runs only when EXPR holds,
      "capable": `[capable EXPR]` used inside another expression (kind of use not classified).

Static text scan only: it does not execute Tcl. Guards built at run time (e.g. EXPR held in
a variable) are reported with their literal text and keyword "?".

Usage:  python3 scripts/map_ifcapable.py --src /opt/sqlite-src-3460100 \
            --json tests/existing/ifcapable-map.json
"""
import argparse, glob, json, os, re, sys

KEYWORD = re.compile(r"[A-Za-z0-9_]+")

# Helper procs that skip the rest of a file. Each is defined in a *_common.tcl file with an
# `ifcapable` (or other) check; the expression below is copied from that definition.
HELPER_GUARDS = {
    # ext/fts5/test/fts5_common.tcl:18  ifcapable !fts5 { proc return_if_no_fts5 ... finish_test; return }
    "return_if_no_fts5": ("fts5", "ext/fts5/test/fts5_common.tcl"),
    # ext/intck/intck_common.tcl:18     ifcapable !vtab||!pragma { proc return_if_no_intck ... }
    "return_if_no_intck": ("vtab&&pragma", "ext/intck/intck_common.tcl"),
    # ext/lsm1/test/lsm1_common.tcl:25  skips unless ../lsm.so exists (a file check, not an option)
    "return_if_no_lsm1": ("", "ext/lsm1/test/lsm1_common.tcl: skips unless lsm.so exists"),
}

# Options studied so far (pilot model + screening) -> ::sqlite_options keyword and the value of
# that keyword when the option is turned ON. Taken from src/test_config.c (line numbers for 3.46.1).
OPTIONS = [
    ("SQLITE_ENABLE_FTS5", "fts5", 1, "test_config.c:425"),
    ("SQLITE_ENABLE_RTREE", "rtree", 1, "test_config.c:564"),
    ("SQLITE_ENABLE_COLUMN_METADATA", "columnmetadata", 1, "test_config.c:342"),
    ("SQLITE_SECURE_DELETE", "secure_delete", 1, "test_config.c:734"),
    ("SQLITE_ENABLE_FTS3", "fts3", 1, "test_config.c:419"),
    ("SQLITE_ENABLE_FTS4", None, None, "no keyword; only fts4_deferred (test_config.c:437), which tracks SQLITE_DISABLE_FTS4_DEFERRED"),
    ("SQLITE_ENABLE_GEOPOLY", "geopoly", 1, "test_config.c:244"),
    ("SQLITE_ENABLE_STAT4", "stat4", 1, "test_config.c:594"),
    ("SQLITE_ENABLE_DBSTAT_VTAB", None, None, "no keyword in test_config.c"),
    ("SQLITE_ENABLE_UPDATE_DELETE_LIMIT", "update_delete_limit", 1, "test_config.c:716 (also needs !OMIT_SUBQUERY)"),
    ("SQLITE_DEFAULT_FOREIGN_KEYS", None, None, "no keyword; `foreignkey` (test_config.c:413) tracks SQLITE_OMIT_FOREIGN_KEY instead"),
    ("SQLITE_LIKE_DOESNT_MATCH_BLOBS", "like_match_blobs", 0, "test_config.c:258 (inverted: option on -> keyword 0)"),
    ("SQLITE_OMIT_WAL", "wal", 0, "test_config.c:704 (inverted)"),
    ("SQLITE_OMIT_AUTOVACUUM", "autovacuum", 0, "test_config.c:294 (inverted)"),
    ("SQLITE_ENABLE_NULL_TRIM", "null_trim", 1, "test_config.c:521"),
    ("SQLITE_ENABLE_SORTER_REFERENCES", None, None, "no keyword in test_config.c"),
]


def quick_suite_files(src):
    """Rebuild $allquicktests (= the `quick` suite, test/permutations.test:263) from the text of
    test/permutations.test, as test_set does: glob, then `array unset` with each exclude pattern
    and */pattern. Assumes a unix platform and no QUICKTEST_INCLUDE/QUICKTEST_OMIT variables."""
    import fnmatch
    perm = open(os.path.join(src, "test", "permutations.test")).read()
    a = perm.index("set alltests [list]")
    b = perm.index("set allquicktests [test_set $alltests -exclude {")
    head = perm[a:b]
    keys = {os.path.basename(f) for f in glob.glob(os.path.join(src, "test", "*.test"))}
    for pat in re.findall(r"\$testdir/\.\./(ext/[^\s\\\]]+\.test)", head):
        keys |= {"test/../" + os.path.relpath(f, src).replace(os.sep, "/")
                 for f in glob.glob(os.path.join(src, pat))}

    def exclude(keys, block):
        for p in block.split():
            keys = {k for k in keys if not (fnmatch.fnmatchcase(k, p) or fnmatch.fnmatchcase(k, "*/" + p))}
        return keys

    m = re.search(r"set alltests \[test_set \$alltests -exclude \{(.*?)\}\]", head, re.S)
    keys = exclude(keys, m.group(1))
    m = re.search(r"set allquicktests \[test_set \$alltests -exclude \{(.*?)\}\]", perm[b:], re.S)
    keys = exclude(keys, m.group(1))
    return {k[len("test/../"):] if k.startswith("test/../") else "test/" + k for k in keys}


def read_word(text, i):
    """Read one Tcl word starting at text[i] (after whitespace). Returns (word, end, braced)."""
    n = len(text)
    while i < n and text[i] in " \t":
        i += 1
    if i >= n:
        return None, i, False
    if text[i] == "{":
        depth, j = 0, i
        while j < n:
            c = text[j]
            if c == "\\":
                j += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[i + 1:j], j + 1, True
            j += 1
        return text[i + 1:], n, True
    if text[i] == '"':
        j = i + 1
        while j < n and text[j] != '"':
            j += 2 if text[j] == "\\" else 1
        return text[i + 1:j], j + 1, False
    j = i
    while j < n and text[j] not in " \t\n;":
        if text[j] == "\\" and j + 1 < n and text[j + 1] == "\n":
            break
        j += 1
    return text[i:j], j, False


def skip_continuations(text, i):
    """Skip spaces and backslash-newline continuations."""
    n = len(text)
    while i < n and (text[i] in " \t" or (text[i] == "\\" and i + 1 < n and text[i + 1] == "\n")):
        i += 2 if text[i] == "\\" else 1
    return i


def polarity(expr):
    """Return {keyword: needs_on|needs_off|mixed} for an ifcapable expression.

    A keyword is positive when it sits under an even number of `!` (a `!` applies to the next
    keyword or parenthesised group). Keywords appearing with both signs are "mixed"."""
    toks = re.findall(r"!|\(|\)|&&|\|\||[A-Za-z0-9_]+|\S", expr)
    result, pos = {}, 0

    def term(neg):
        nonlocal pos
        while pos < len(toks) and toks[pos] == "!":
            neg = not neg
            pos += 1
        if pos >= len(toks):
            return
        t = toks[pos]
        pos += 1
        if t == "(":
            disj(neg)
            if pos < len(toks) and toks[pos] == ")":
                pos += 1
        elif KEYWORD.fullmatch(t):
            p = "needs_off" if neg else "needs_on"
            result[t] = p if result.get(t, p) == p else "mixed"

    def disj(neg):
        nonlocal pos
        term(neg)
        while pos < len(toks) and toks[pos] in ("&&", "||"):
            pos += 1
            term(neg)

    while pos < len(toks):
        before = pos
        disj(False)
        if pos == before:  # unexpected token, skip it
            pos += 1
    return result


def scan_file(path, root):
    text = open(path, encoding="utf-8", errors="replace").read()
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    guards = []
    # `ifcapable` as a command word: line start, or after ; { [ with optional whitespace
    for m in re.finditer(r"(?:^|[;{\[])[ \t]*ifcapable\b", text, re.M):
        start = m.end()
        line = text.count("\n", 0, m.start()) + (1 if text[m.start()] == "\n" else 0) + 1
        line_start = text.rfind("\n", 0, m.start() + 1) + 1
        if text[line_start:m.start() + 1].lstrip().startswith("#"):
            continue  # commented out
        expr, i, _ = read_word(text, start)
        if expr is None:
            continue
        i = skip_continuations(text, i)
        body, i, braced = read_word(text, i) if i < len(text) and text[i] == "{" else ("", i, False)
        has_else = False
        j = skip_continuations(text, i)
        if text.startswith("else", j):
            has_else = True
        kind = "file" if re.search(r"\bfinish_test\b", body) and re.search(r"\breturn\b", body) else "block"
        dynamic = "$" in expr or "[" in expr
        kws = {"?": "mixed"} if dynamic else polarity(expr)
        if kind == "file":
            # BODY is the skip; the *rest of the file* runs only when EXPR is false
            flip = {"needs_on": "needs_off", "needs_off": "needs_on", "mixed": "mixed"}
            kws = {k: flip[p] for k, p in kws.items()}
        guards.append({
            "line": line, "expr": expr.strip(), "kind": kind, "else": has_else,
            "keywords": kws,
            "body_lines": body.count("\n") + 1 if body else 0,
        })
    # helper procs defined in *_common.tcl that end the file early (see HELPER_GUARDS)
    for name, (expr, note) in HELPER_GUARDS.items():
        for m in re.finditer(r"^[ \t]*" + name + r"\b", text, re.M):
            guards.append({"line": text.count("\n", 0, m.start()) + 1, "expr": expr,
                           "kind": "file", "else": False, "via": name, "note": note,
                           "keywords": polarity(expr) if expr else {}, "body_lines": 0})
    for m in re.finditer(r"\[\s*capable\s+", text):
        line = text.count("\n", 0, m.start()) + 1
        expr, _, _ = read_word(text, m.end())
        if expr is None:
            continue
        expr = expr.rstrip("]")
        dynamic = "$" in expr or "[" in expr
        guards.append({"line": line, "expr": expr.strip(), "kind": "capable", "else": False,
                       "keywords": {"?": "mixed"} if dynamic else polarity(expr), "body_lines": 0})
    return rel, guards


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", default="/opt/sqlite-src-3460100")
    ap.add_argument("--json", required=True, help="output JSON path")
    ap.add_argument("--md", help="output Markdown table path")
    a = ap.parse_args()

    files = sorted(set(glob.glob(os.path.join(a.src, "test", "*.test"))
                       + glob.glob(os.path.join(a.src, "ext", "**", "*.test"), recursive=True)))
    # ext/jni/src/tests/*.test are SQL scripts for the Java binding, not Tcl tests
    files = [f for f in files if "/ext/jni/" not in f.replace(os.sep, "/")]
    if not files:
        sys.exit(f"no *.test files under {a.src}")
    quick = quick_suite_files(a.src)
    version = open(os.path.join(a.src, "VERSION")).read().strip()
    out = {"sqlite_version": version, "files_scanned": len(files),
           "quick_suite_files": len(quick), "files": {}}
    for f in files:
        rel, guards = scan_file(f, a.src)
        out["files"][rel] = {"in_quick": rel in quick, "guards": guards}
    missing = sorted(quick - set(out["files"]))
    if missing:
        sys.exit(f"quick-suite files not found by the scan: {missing[:5]}")
    os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
    with open(a.json, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    n = sum(len(v["guards"]) for v in out["files"].values())
    print(f"{len(files)} test files ({len(quick)} in quick), {n} guards -> {a.json}")
    if a.md:
        with open(a.md, "w") as fh:
            fh.write(render_md(out))
        print(f"table -> {a.md}")


def keyword_stats(files, kw, only_quick):
    """Per keyword: sets of files by (kind, polarity)."""
    s = {k: set() for k in ("any", "file_on", "file_off", "block_on", "block_off", "mixed")}
    for f, v in files.items():
        if only_quick and not v["in_quick"]:
            continue
        for g in v["guards"]:
            p = g["keywords"].get(kw)
            if p is None:
                continue
            s["any"].add(f)
            if p == "mixed":
                s["mixed"].add(f)
            else:
                kind = "file" if g["kind"] == "file" else "block"
                s[f"{kind}_{'on' if p == 'needs_on' else 'off'}"].add(f)
    return s


def short(paths, n=3):
    p = sorted(paths)
    txt = ", ".join(f"`{x}`" for x in p[:n])
    return txt + (f" (+{len(p) - n})" if len(p) > n else "")


def render_md(out):
    files = out["files"]
    nq = sum(v["in_quick"] for v in files.values())
    L = []
    L.append(f"# Existing SQLite tests per option (`ifcapable` map, SQLite {out['sqlite_version']})\n")
    L.append("Generated by `scripts/map_ifcapable.py` (static scan of the test sources; nothing was "
             "executed). Raw data per file and per guard: `ifcapable-map.json`.\n")
    L.append(f"Scanned: {out['files_scanned']} `*.test` files under `test/` and `ext/`; "
             f"{nq} of them belong to the `quick` suite (rebuilt from `test/permutations.test`; the "
             "list was checked to be identical to the output of SQLite's own `test_set` Tcl code run in "
             "`tclsh`, but **not checked against a quick-run log**). `ext/jni/src/tests/*.test` "
             "(SQL scripts for the Java binding) are not Tcl tests and are left out.\n")
    L.append("## How to read the table\n")
    L.append("- **Keyword**: the `::sqlite_options` entry set by `src/test_config.c` for the option. "
             "`ifcapable EXPR` (`test/tester.tcl:1745`) runs code only if EXPR is true.")
    L.append("- **Inverted**: for `OMIT_*` and `LIKE_DOESNT_MATCH_BLOBS` the keyword is 1 when the "
             "option is *off*. Columns below are written in terms of the **option**, not the keyword.")
    L.append("- **File needs option on / off**: the whole rest of the file is skipped unless the option "
             "is on / off (`ifcapable !x {finish_test; return}` or a `return_if_no_*` helper).")
    L.append("- **Blocks need on / off**: individual blocks of tests guarded by the option.")
    L.append("- Counts are numbers of *files*; one file can be in several columns. Numbers in "
             "parentheses: all scanned files, including those not in `quick`.\n")
    L.append("## Options of the pilot model and the screening\n")
    L.append("| Option | Keyword | Files with any guard | File needs option on | File needs option off "
             "| Blocks need on | Blocks need off | Example files (quick) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for opt, kw, on_val, where in OPTIONS:
        if kw is None:
            L.append(f"| `{opt}` | – | – | – | – | – | – | {where} |")
            continue
        q, a = keyword_stats(files, kw, True), keyword_stats(files, kw, False)
        flip = on_val == 0
        def c(key):
            k = key
            if flip:
                k = key.replace("_on", "_TMP").replace("_off", "_on").replace("_TMP", "_off")
            return f"{len(q[k])} ({len(a[k])})"
        kwtxt = f"`{kw}`" + (" (inverted)" if flip else "")
        L.append(f"| `{opt}` | {kwtxt} | {len(q['any'])} ({len(a['any'])}) | {c('file_on')} | "
                 f"{c('file_off')} | {c('block_on')} | {c('block_off')} | {short(q['any'])} |")
    L.append("")
    L.append("Source of each keyword:\n")
    for opt, kw, on_val, where in OPTIONS:
        L.append(f"- `{opt}` → {('`' + kw + '`') if kw else 'none'}: {where}")
    L.append("")
    # Pairs of the pilot model (models/sqlite-acts.txt)
    pilot4 = [("FTS5", "fts5"), ("RTREE", "rtree"), ("COLUMN_METADATA", "columnmetadata"),
              ("SECURE_DELETE", "secure_delete")]
    L.append("## Pilot-model option pairs in the existing tests\n")
    L.append("For each pair of the 4 pilot options: quick-suite files that mention **both** keywords "
             "in one guard expression, and files that have guards on both keywords anywhere in the "
             "file. This only says where the tests *mention* both options; it does not show that the "
             "pair's interaction is tested.\n")
    L.append("| Pair | Same guard expression | Guards on both in one file |")
    L.append("|---|---|---|")
    for i in range(len(pilot4)):
        for j in range(i + 1, len(pilot4)):
            (na, ka), (nb, kb) = pilot4[i], pilot4[j]
            same, both = set(), set()
            for f, v in files.items():
                if not v["in_quick"]:
                    continue
                kws = [set(g["keywords"]) for g in v["guards"]]
                if any(ka in s and kb in s for s in kws):
                    same.add(f)
                if any(ka in s for s in kws) and any(kb in s for s in kws):
                    both.add(f)
            L.append(f"| {na} × {nb} | {len(same)}{(': ' + short(same)) if same else ''} | "
                     f"{len(both)}{(': ' + short(both)) if both else ''} |")
    L.append("")
    # Mixed / compound guards involving the pilot options
    pilot = {"fts5", "rtree", "columnmetadata", "secure_delete", "fts3", "geopoly", "wal"}
    comp = []
    for f, v in sorted(files.items()):
        for g in v["guards"]:
            ks = set(g["keywords"]) & pilot
            if ks and len(g["keywords"]) > 1:
                comp.append((f, g, v["in_quick"]))
    L.append("## Guards that combine a studied option with another keyword\n")
    L.append("These are the places where the existing tests already *name* an option combination.\n")
    L.append("| File | Line | Kind | Expression | In quick |")
    L.append("|---|---|---|---|---|")
    for f, g, inq in comp:
        L.append(f"| `{f}` | {g['line']} | {g['kind']} | `{g['expr']}` | {'yes' if inq else 'no'} |")
    L.append("")
    # all keywords
    allkw = {}
    for f, v in files.items():
        for g in v["guards"]:
            for k in g["keywords"]:
                allkw.setdefault(k, set()).add(f)
    L.append("## All keywords used in guards\n")
    L.append("Number of scanned files that mention each keyword in an `ifcapable`/`capable` guard.\n")
    L.append("| Keyword | Files | Keyword | Files | Keyword | Files |")
    L.append("|---|---|---|---|---|---|")
    items = sorted(allkw.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for i in range(0, len(items), 3):
        row = items[i:i + 3] + [("", set())] * (3 - len(items[i:i + 3]))
        L.append("| " + " | ".join(f"`{k}` | {len(s)}" if k else " | " for k, s in row) + " |")
    L.append("")
    unguarded = sum(1 for v in files.values() if v["in_quick"] and not v["guards"])
    L.append(f"Files in `quick` without any guard: {unguarded} of {nq}.\n")
    L.append("## Limits of this map\n")
    L.append("- Static text scan: it finds `ifcapable` and `capable` as written; guards computed at run "
             "time, `if {[permutation]==...}` checks and checks inside helper `.tcl` files other than "
             "the `return_if_no_*` procs are not counted.")
    L.append("- A guard says which tests are *skipped*; it does not prove that the remaining tests "
             "exercise the option, nor that unguarded tests are independent of it.")
    L.append("- The quick-suite list is rebuilt from the source text, assuming a unix platform and no "
             "`QUICKTEST_INCLUDE`/`QUICKTEST_OMIT`; not verified against a run log.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
