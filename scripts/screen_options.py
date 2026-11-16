#!/usr/bin/env python3
"""Screen candidate compile-time options before they enter the ACTS model.

For every candidate (alone) and every pair listed in models/sqlite-candidates.json:
  1. build testfixture with only that option turned on (fast build, no coverage),
  2. check that PRAGMA compile_options reports it,
  3. run a small functional probe (does the feature really work?),
  4. run SQLite's test/main.test as a smoke test.
Writes results/screening/screening.json and results/screening/screening.md.

Usage (inside the container, non-root):  python3 scripts/screen_options.py [--only NAME ...]
"""
import argparse, json, os, re, shutil, subprocess, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(src, work, name, flags, jobs):
    d = os.path.join(work, "screen", re.sub(r"[^A-Za-z0-9_]+", "_", name))
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    log = open(os.path.join(d, "build.log"), "w")
    rc = subprocess.run([os.path.join(src, "configure"), "--disable-shared", "CFLAGS=-O0 -g"],
                        cwd=d, stdout=log, stderr=subprocess.STDOUT).returncode
    if rc == 0:
        rc = subprocess.run(["make", f"-j{jobs}", "testfixture", "OPTS=" + " ".join(flags)],
                            cwd=d, stdout=log, stderr=subprocess.STDOUT).returncode
    tail = open(os.path.join(d, "build.log"), errors="replace").read()[-600:]
    return d, rc, tail


def tcl(tf, cwd, body):
    p = os.path.join(cwd, "probe.tcl")
    open(p, "w").write("sqlite3 db :memory:\nif {[catch {" + body + "} e]} {puts \"ERROR: $e\"}\ndb close\n")
    r = subprocess.run([tf, p], cwd=cwd, capture_output=True, text=True, timeout=120)
    return (r.stdout + r.stderr).strip()


def screen(src, work, name, flags, compile_option, probe, jobs):
    t = time.time()
    d, rc, tail = build(src, work, name, flags, jobs)
    res = {"name": name, "flags": flags, "build": "ok" if rc == 0 else "failed"}
    if rc != 0:
        res["build_error_tail"] = tail
        return res
    tf = os.path.join(d, "testfixture")
    opts = tcl(tf, d, "foreach o [db eval {PRAGMA compile_options}] {puts $o}").split()
    if compile_option:
        res["compile_option_reported"] = compile_option in opts
    if probe:
        res["probe_output"] = tcl(tf, d, probe)
    rundir = os.path.join(d, "run"); os.makedirs(rundir)
    out = subprocess.run([tf, os.path.join(src, "test", "main.test")], cwd=rundir,
                         capture_output=True, text=True, timeout=1800).stdout
    m = re.findall(r"(\d+) errors? out of (\d+) tests", out)
    res["main_test"] = f"{m[-1][0]} errors / {m[-1][1]} tests" if m else "no summary line"
    res["seconds"] = round(time.time() - t)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="/opt/sqlite-src-3460100")
    ap.add_argument("--work", default=os.path.expanduser("~/ens491-work"))
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise SystemExit("error: run as a non-root user")
    c = json.load(open(os.path.join(REPO, "models", "sqlite-candidates.json")))
    out_dir = os.path.join(REPO, "results", "screening"); os.makedirs(out_dir, exist_ok=True)
    results = []
    for name, spec in c["candidates"].items():
        if a.only and name not in a.only:
            continue
        print(f"[screen] {name}", flush=True)
        results.append(screen(a.src, a.work, name, spec["on"], spec["compile_option"], spec.get("probe"), a.jobs))
    for p in c.get("pairs_to_check", []):
        if a.only and p["name"] not in a.only:
            continue
        print(f"[screen] {p['name']}", flush=True)
        probe = p.get("probe") or c["candidates"]["SQLITE_ENABLE_GEOPOLY"]["probe"]
        results.append(screen(a.src, a.work, p["name"], p["flags"], None, probe, a.jobs))
    json.dump(results, open(os.path.join(out_dir, "screening.json"), "w"), indent=2)
    with open(os.path.join(out_dir, "screening.md"), "w") as f:
        f.write("| Candidate | Flags | Build | Reported by compile_options | Probe | main.test |\n|---|---|---|---|---|---|\n")
        for r in results:
            f.write(f"| {r['name']} | `{' '.join(r['flags'])}` | {r['build']} | {r.get('compile_option_reported', '-')} | "
                    f"{str(r.get('probe_output', '-')).replace('|', '/')[:80]} | {r.get('main_test', '-')} |\n")
    print(open(os.path.join(out_dir, "screening.md")).read())


if __name__ == "__main__":
    main()
