#!/usr/bin/env python3
"""Build SQLite's testfixture for one ACTS row, verify the effective options,
run SQLite's own Tcl tests, and collect coverage of sqlite3.c.

Usage (inside the container, as a non-root user):
  python3 scripts/run_config.py --row 1 --scope main      # smoke test
  python3 scripts/run_config.py --row 1 --scope quick     # agreed scope
  python3 scripts/run_config.py --all --scope quick

Paths (override with flags):
  --csv      configs/sqlite-pairwise.csv          ACTS output (comment lines start with '#')
  --mapping  models/sqlite-build-mapping.json     option value -> compiler flags
  --src      /opt/sqlite-src-3460100              pinned SQLite source (inside the Docker image)
  --work     /home/tester/ens491-work             builds and test runs (Linux filesystem, NOT the Mac bind mount)
  --results  results/acts                         one folder per configuration, copied into the repo

Each configuration gets results/<name>/summary.json with separate statuses for
build, effective-option check, tests and coverage. A failure in one stage is
recorded, never hidden, and later stages are skipped.
"""
import argparse, csv, datetime, json, os, platform, re, shutil, subprocess, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUSPICIOUS_HITS_THRESHOLD = 10**11


def sh(cmd, cwd, log, env=None, timeout=None):
    """Run a command, append its output to log, return exit code."""
    with open(log, "a") as f:
        f.write(f"\n$ {' '.join(cmd)}\n")
        f.flush()
        try:
            return subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT,
                                  env=env, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            f.write("TIMEOUT\n")
            return 124


def read_acts_csv(path):
    lines = [l for l in open(path) if l.strip() and not l.lstrip().startswith("#")]
    rows = list(csv.reader(lines))
    return rows[0], rows[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(REPO, "configs/sqlite-pairwise.csv"))
    ap.add_argument("--mapping", default=os.path.join(REPO, "models/sqlite-build-mapping.json"))
    ap.add_argument("--src", default="/opt/sqlite-src-3460100")
    ap.add_argument("--work", default=os.path.expanduser("~/ens491-work"))
    ap.add_argument("--results", default=os.path.join(REPO, "results/acts"))
    ap.add_argument("--scope", default="main", help="test/<scope>.test, e.g. main (smoke) or quick")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--row", type=int, help="1-based ACTS row number")
    g.add_argument("--all", action="store_true")
    ap.add_argument("--allow-root", action="store_true", help="SQLite permission tests fail as root")
    a = ap.parse_args()

    if hasattr(os, "geteuid") and os.geteuid() == 0 and not a.allow_root:
        sys.exit("error: run as a non-root user (e.g. 'su - tester'); some SQLite tests abort as root")

    mapping = json.load(open(a.mapping))
    header, rows = read_acts_csv(a.csv)
    unknown = [h for h in header if h not in mapping["options"]]
    if unknown:
        sys.exit(f"error: no build mapping for {unknown}")
    todo = range(1, len(rows) + 1) if a.all else [a.row]
    for n in todo:
        run_one(a, mapping, header, rows[n - 1], n)


def run_one(a, mapping, header, row, n):
    cfg = dict(zip(header, row))
    name = f"acts-{n:02d}"
    res = os.path.join(a.results, f"{name}-{a.scope}")
    shutil.rmtree(res, ignore_errors=True); os.makedirs(res)
    build = os.path.join(a.work, "builds", name)
    shutil.rmtree(build, ignore_errors=True); os.makedirs(build)
    log_build = os.path.join(res, "build.log")
    summary = {
        "configuration": name, "acts_row": n, "values": cfg, "scope": f"test/{a.scope}.test",
        "sqlite_source": a.src, "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "machine": f"{platform.system()} {platform.machine()}", "user": os.environ.get("USER", ""),
        "build": {}, "effective_options": {}, "tests": {}, "coverage": {},
    }
    flags = [f for opt in header for f in mapping["options"][opt][cfg[opt]]]
    summary["build"]["opts"] = " ".join(flags)
    print(f"[{name}] {cfg}")

    # 1. build (fresh directory, coverage with thread-safe counters)
    cflags = "-O0 -g --coverage -fprofile-update=atomic"
    t = time.time()
    rc = sh([os.path.join(a.src, "configure"), "--disable-shared",
             f"CFLAGS={cflags}", "LDFLAGS=--coverage"], build, log_build)
    if rc == 0:
        rc = sh(["make", f"-j{a.jobs}", "testfixture", f"OPTS={' '.join(flags)}"], build, log_build)
    summary["build"].update({"cflags": cflags, "exit_code": rc, "seconds": round(time.time() - t),
                             "status": "ok" if rc == 0 else "failed"})
    if rc != 0:
        return finish(summary, res, "build failed")

    # 2. copy the binary away from *.gcno files (backcompat.test runs every testfixture?* it finds)
    bindir = os.path.join(a.work, "bin", name)
    shutil.rmtree(bindir, ignore_errors=True); os.makedirs(bindir)
    tf = os.path.join(bindir, "testfixture")
    shutil.copy2(os.path.join(build, "testfixture"), tf)

    # 3. effective options, read from testfixture itself
    probe = os.path.join(bindir, "probe.tcl")
    open(probe, "w").write("sqlite3 db :memory:\nforeach o [db eval {PRAGMA compile_options}] {puts $o}\ndb close\n")
    out = subprocess.run([tf, probe], capture_output=True, text=True).stdout.split()
    open(os.path.join(res, "compile-options.txt"), "w").write("\n".join(out) + "\n")
    mism = []
    for opt in header:
        want = cfg[opt] == "on"
        have = mapping["options"][opt]["compile_option"] in out
        summary["effective_options"][opt] = {"requested": cfg[opt], "present": have}
        if want != have:
            mism.append(opt)
    summary["effective_options"]["status"] = "ok" if not mism else "mismatch: " + ", ".join(mism)
    # the probe itself wrote coverage counters: remove them before the real run
    for root, _, files in os.walk(build):
        for f in files:
            if f.endswith(".gcda"):
                os.remove(os.path.join(root, f))
    if mism:
        return finish(summary, res, "effective options differ from the ACTS row")

    # 4. run SQLite's own tests from a fresh directory on the Linux filesystem
    rundir = os.path.join(a.work, "runs", f"{name}-{a.scope}")
    shutil.rmtree(rundir, ignore_errors=True); os.makedirs(rundir)
    test_log = os.path.join(res, "tests.log")
    t = time.time()
    with open(test_log, "w") as f:
        rc = subprocess.run([tf, os.path.join(a.src, "test", f"{a.scope}.test")],
                            cwd=rundir, stdout=f, stderr=subprocess.STDOUT).returncode
    secs = round(time.time() - t)
    text = open(test_log, errors="replace").read()
    m = re.findall(r"(\d+) errors? out of (\d+) tests", text)
    failed_names = sorted(set(re.findall(r"^! (\S+) expected", text, re.M)))
    summary["tests"] = {
        "exit_code": rc, "seconds": secs,
        "errors": int(m[-1][0]) if m else None, "tests": int(m[-1][1]) if m else None,
        "failed_test_names": failed_names,
        "omitted_lines": len(re.findall(r"^Omitting", text, re.M)),
        "status": "completed" if m else "no summary line (aborted?)",
        "note": "'tests' and 'errors' come from the harness summary line; skip semantics are not yet extracted",
    }

    # 5. coverage of sqlite3.c only (same boundary for every configuration)
    cov = os.path.join(res, "coverage"); os.makedirs(cov)
    gcda = os.path.join(build, "testfixture-sqlite3.gcda")
    # SQLite's quick suite really executes some loops ~1e10 times; gcovr's default
    # "suspicious hits" limit (2^32) would reject these genuine counts.
    r = subprocess.run(["gcovr", "--root", build, "--filter", re.escape(build) + r"/sqlite3\.c$",
                        "--gcov-suspicious-hits-threshold", str(SUSPICIOUS_HITS_THRESHOLD),
                        "--json-summary", os.path.join(cov, "summary.json"), "--print-summary", gcda],
                       capture_output=True, text=True)
    open(os.path.join(cov, "gcovr.log"), "w").write(r.stdout + r.stderr)
    if r.returncode == 0 and os.path.exists(os.path.join(cov, "summary.json")):
        s = json.load(open(os.path.join(cov, "summary.json")))
        summary["coverage"] = {"status": "ok", "tool": "gcovr 8.3", "file": "sqlite3.c",
                               "suspicious_hits_threshold": SUSPICIOUS_HITS_THRESHOLD,
                               "line_percent": s.get("line_percent"),
                               "lines_covered": s.get("line_covered"), "lines_total": s.get("line_total"),
                               "function_percent": s.get("function_percent"),
                               "functions_covered": s.get("function_covered"), "functions_total": s.get("function_total")}
    else:
        summary["coverage"] = {"status": "failed", "error": (r.stderr or r.stdout)[-800:]}
    return finish(summary, res, "done")


def finish(summary, res, msg):
    summary["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
    summary["result"] = msg
    json.dump(summary, open(os.path.join(res, "summary.json"), "w"), indent=2)
    print(f"  -> {msg}: build={summary['build'].get('status')} options={summary['effective_options'].get('status')} "
          f"tests={summary['tests'].get('errors')}/{summary['tests'].get('tests')} coverage={summary['coverage'].get('status')}")


if __name__ == "__main__":
    main()
