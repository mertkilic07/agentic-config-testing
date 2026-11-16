"""Apply one SQLite configuration to a fresh database and run a small workload.

Each check compares the observed behavior with the behavior the configuration model
(model/model.json, constraints C1-C5) predicts. A FAIL means that the model and the real
system disagree for this configuration, which is either a model error or an interaction.
"""
import os, sqlite3, tempfile

ORDER = ["page_size", "auto_vacuum", "journal_mode", "synchronous", "locking_mode",
         "cache_size", "temp_store", "foreign_keys", "secure_delete"]  # C1: page_size/auto_vacuum first


def apply(conn, cfg):
    effective = {}
    for name in ORDER:
        conn.execute(f"PRAGMA {name} = {cfg[name]}")
    for name in ORDER:
        effective[name] = str(conn.execute(f"PRAGMA {name}").fetchone()[0])
    return effective


NUMERIC = {"auto_vacuum": {"0": "NONE", "1": "FULL", "2": "INCREMENTAL"},
           "synchronous": {"0": "OFF", "1": "NORMAL", "2": "FULL", "3": "EXTRA"},
           "temp_store": {"0": "DEFAULT", "1": "FILE", "2": "MEMORY"},
           "foreign_keys": {"0": "OFF", "1": "ON"}, "secure_delete": {"0": "OFF", "1": "ON"}}


def run(cfg):
    checks = {}
    tmp = tempfile.mkdtemp(prefix="cit_")
    path = os.path.join(tmp, "test.db")
    conn = sqlite3.connect(path, isolation_level=None, timeout=0.2)
    eff = apply(conn, cfg)

    # 0) were the requested settings actually applied?
    mism = []
    for k, v in eff.items():
        shown = NUMERIC.get(k, {}).get(v, v)
        if shown.upper() != str(cfg[k]).upper():
            mism.append(f"{k}: requested {cfg[k]}, effective {shown}")
    checks["settings_applied"] = ("PASS" if not mism else "FAIL", "; ".join(mism))

    # 1) basic create / insert / select
    conn.execute("CREATE TABLE parent(id INTEGER PRIMARY KEY)")
    conn.execute("CREATE TABLE child(id INTEGER PRIMARY KEY, pid INTEGER REFERENCES parent(id), data TEXT)")
    conn.execute("BEGIN")
    conn.executemany("INSERT INTO parent(id) VALUES (?)", [(i,) for i in range(1, 501)])
    conn.executemany("INSERT INTO child(pid, data) VALUES (?, ?)", [(i, "x" * 200) for i in range(1, 501)])
    conn.execute("COMMIT")
    n = conn.execute("SELECT count(*) FROM child").fetchone()[0]
    checks["crud"] = ("PASS" if n == 500 else "FAIL", f"rows={n}")

    # 2) rollback restores previous state (C2: not a valid oracle when journal_mode=OFF)
    conn.execute("BEGIN")
    conn.execute("INSERT INTO parent(id) VALUES (9999)")
    try:
        conn.execute("ROLLBACK")
        err = ""
    except sqlite3.Error as e:
        err = str(e)
    restored = conn.execute("SELECT count(*) FROM parent WHERE id = 9999").fetchone()[0] == 0
    if cfg["journal_mode"] == "OFF":
        checks["rollback"] = ("SKIP", f"C2; observed restored={restored} {err}".strip())
    else:
        checks["rollback"] = ("PASS" if restored else "FAIL", err)

    # 3) foreign keys (C5)
    try:
        conn.execute("INSERT INTO child(pid, data) VALUES (123456, 'orphan')")
        rejected = False
    except sqlite3.IntegrityError:
        rejected = True
    expected = cfg["foreign_keys"] == "ON"
    checks["foreign_keys"] = ("PASS" if rejected == expected else "FAIL",
                              f"rejected={rejected}, model expects rejected={expected}")

    # 4) free pages after delete (C4)
    conn.execute("DELETE FROM child WHERE id > 100")
    free = conn.execute("PRAGMA freelist_count").fetchone()[0]
    if cfg["auto_vacuum"] == "FULL":
        ok = free == 0
    else:
        ok = free > 0
    checks["auto_vacuum"] = ("PASS" if ok else "FAIL", f"freelist_count={free}")

    # 5) second connection (C3)
    try:
        c2 = sqlite3.connect(path, timeout=0.2)
        c2.execute("SELECT count(*) FROM parent").fetchone()
        c2.close()
        blocked = False
    except sqlite3.OperationalError:
        blocked = True
    expected_block = cfg["locking_mode"] == "EXCLUSIVE"
    checks["second_connection"] = ("PASS" if blocked == expected_block else "FAIL",
                                   f"blocked={blocked}, model expects blocked={expected_block}")

    # 6) integrity
    ic = conn.execute("PRAGMA integrity_check").fetchone()[0]
    checks["integrity"] = ("PASS" if ic == "ok" else "FAIL", ic)
    conn.close()
    return checks
