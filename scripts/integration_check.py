"""Tier 2 integration check (docs/northstar/regression.md): run every suite,
write docs/northstar/baselines/<date>_<name>.{json,md}, compare to the newest
earlier baseline, exit 0 PASS / 1 REGRESSION."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "specfactory"))
import suite_regression as sr  # noqa: E402

PY = os.environ.get("PY", sr.DEFAULT_PYTHON)
BASE_DIR = ROOT / "docs" / "northstar" / "baselines"
SCOPE = ["systemd-run", "--user", "--scope", "-q", "-p", "MemoryMax=6G", "-p", "MemorySwapMax=0", "--"]
SUITES = ["csim", "scale", "transport", "t1", "specfactory", "desktop", "long", "godot", "mockups", "net", "tactical_trace"]
PYTEST = [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
PYTEST_SUITES = {  # key: (limit_s, pre-args, test path, env, extra pytest flags)
    "csim": (1500, [], "tests/csim", {}, ["-rfE"]),
    "scale": (1200, [], "tests/csim/scale", {"OM_SCALE": "1"}, ["-rfEs"]),
    "transport": (1200, [], "tests/transport", {}, []),
    "t1": (900, [], "tests/qa/t1", {}, []),
    "specfactory": (1500, [], "tests/specfactory", {}, []),
    "desktop": (900, ["xvfb-run", "-a"], "tests/qa/desktop", {}, []),
    "net": (1200, [], "tests/net", {}, []),
}
BUDGET_RE = re.compile(r"raw median ([\d.]+)us exceeds the min-spec budget [\d.]+us scaled to ([\d.]+)us")
TIME_SOFT_RE = re.compile(r"took \d+ms, expected <")


def run(argv, limit, cwd=ROOT, env=None, cwd_override=None):
    e = dict(os.environ, **(env or {}))
    t0 = time.time()
    try:
        r = subprocess.run(SCOPE + ["timeout", str(limit)] + argv, cwd=str(cwd_override or cwd),
                           capture_output=True, text=True, env=e)
        rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as ex:  # systemd-run missing etc.
        rc, out = 125, f"launch failed: {ex}"
    return rc, out, round(time.time() - t0, 1)


def empty(cmd, rc=0, wall=0.0):
    return {"cmd": cmd, "rc": rc, "wall_s": wall, "passed": 0, "failed": 0, "skipped": 0,
            "xfailed": 0, "aborted": 0, "failing_ids": []}


def pytest_suite(key):
    limit, pre, path, env, flags = PYTEST_SUITES[key]
    if not (ROOT / path).exists():
        return {"status": "absent", **empty("(absent)")}
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "j.xml"
        argv = pre + PYTEST + flags + [path, f"--junitxml={xml}"]
        rc, out, wall = run(argv, limit, env=env)
        res = empty(" ".join(argv), rc, wall)
        passed, failed, ids = sr.parse_pytest(out)
        first, skipped, xfailed = sr.parse_junit_extra(xml)
        res.update(passed=passed, failed=failed, skipped=skipped, xfailed=xfailed,
                   failing_ids=sorted(set(ids) | set(first)))
        if passed + failed == 0 and rc != 0:
            res["failed"] = 1
            res["failing_ids"] = ["<suite did not run: rc=%d>" % rc]
        if key == "scale":
            res["scale_failures"] = {}
            for nid, msg in first.items():
                m = BUDGET_RE.search(msg)
                res["scale_failures"][nid] = (
                    {"kind": "budget", "measured_us": float(m.group(1)), "limit_us": float(m.group(2))}
                    if m else {"kind": "other"})
        res["status"] = "pass" if rc == 0 else "fail"
        return res


def long_suite():
    with tempfile.TemporaryDirectory() as tmp:
        jl = Path(tmp) / "long.jsonl"
        argv = PYTEST + [".", f"--junitxml={Path(tmp) / 'j.xml'}"]
        rc, out, wall = run(argv, 2400, env={"OM_LONG_RESULTS": str(jl)}, cwd_override=ROOT / "tests" / "long")
        res = empty("cd tests/long && " + " ".join(argv), rc, wall)
        passed, failed, ids = sr.parse_pytest(out)
        first, skipped, xfailed = sr.parse_junit_extra(Path(tmp) / "j.xml")
        res.update(passed=passed, failed=failed, skipped=skipped, xfailed=xfailed,
                   failing_ids=sorted(set(ids) | set(first)))
        seeds = {}
        if jl.exists():
            for line in jl.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    seeds[str(r.get("seed"))] = {k: r.get(k) for k in ("archetype", "end", "ticks", "alive", "wall_s")}
        res["seeds"] = seeds
        res["status"] = "pass" if rc == 0 else "fail"
        return res


def godot_suite():
    scripts = sorted(p.name for p in (ROOT / "tests").glob("*.gd"))
    per, wall, ids = {}, 0.0, []
    for s in scripts:
        rc, out, w = run(["scripts/run_godot_tests.sh", f"tests/{s}"], 420)
        wall += w
        sums = re.findall(r"^PASS: (\d+) +FAIL: (\d+)$", out, re.M)
        if sums:
            p, f = int(sums[-1][0]), int(sums[-1][1])
        else:
            p = len(re.findall(r"^\S+: PASS\s*$", out, re.M))
            f = len(re.findall(r"^\S+: FAIL\b", out, re.M))
        if "no summary: aborted" in out or (rc != 0 and not sums and not f):
            status = "aborted"
        elif rc == 0 and f == 0:
            status = "pass"
        else:
            status = "fail"
        per[s] = {"pass": p, "fail": f, "status": status}
    res = empty("scripts/run_godot_tests.sh tests/X.gd (each)", 0, round(wall, 1))
    res["passed"] = sum(1 for v in per.values() if v["status"] == "pass")
    res["failed"] = sum(1 for v in per.values() if v["status"] == "fail")
    res["aborted"] = sum(1 for v in per.values() if v["status"] == "aborted")
    res["failing_ids"] = sorted(k for k, v in per.items() if v["status"] != "pass")
    res["scripts"] = per
    res["status"] = "pass" if not res["failing_ids"] else "fail"
    return res


def mockup_suite():
    names = sorted(p.parent.name for p in (ROOT / "scenes" / "mockups").glob("*/verify.gd"))
    per, wall = {}, 0.0
    for n in names:
        rc, out, w = run(["scripts/mockup_verify.sh", n], 300)
        wall += w
        ok = rc == 0 and re.search(r"^VERIFY OK$", out, re.M) is not None
        first = ""
        if not ok:
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            first = next((l for l in lines if "FAIL" in l or "took" in l), lines[-1] if lines else "")
        per[n] = {"ok": ok, "first_fail": first}
    res = empty("scripts/mockup_verify.sh <name> (each)", 0, round(wall, 1))
    res["passed"] = sum(1 for v in per.values() if v["ok"])
    res["failed"] = len(per) - res["passed"]
    res["failing_ids"] = sorted(k for k, v in per.items() if not v["ok"])
    res["mockups"] = per
    res["status"] = "pass" if not res["failing_ids"] else "fail"
    return res


def trace_suite():
    tt = ROOT / "scripts" / "specfactory" / "tactical_trace.py"
    if not tt.exists():
        return {"status": "absent", **empty("(absent)")}
    t0 = time.time()
    rc, out, _ = run(["make", "-s", "build/O0/libouroboros.so", "build/O2/libouroboros.so"], 600)
    if rc != 0:
        r = empty("make build/O0 build/O2", rc, round(time.time() - t0, 1))
        r.update(status="fail", failed=1, failing_ids=["build"])
        return r
    args = ["--seed", "1", "--regions", "60", "--ticks", "500", "--features", "6"]
    with tempfile.TemporaryDirectory() as tmp:
        outs = []
        for o in ("O0", "O2"):
            rc, out, _ = run([PY, str(tt), "--lib", f"build/{o}/libouroboros.so", *args], 900)
            f = Path(tmp) / f"{o}.txt"
            f.write_text(out)
            outs.append(f)
        rc, out, _ = run([PY, str(tt), "--compare", str(outs[0]), str(outs[1])], 300)
    r = empty("tactical_trace.py O0 vs O2", rc, round(time.time() - t0, 1))
    r["status"] = "pass" if rc == 0 else "fail"
    if rc != 0:
        r.update(failed=1, failing_ids=["O0_vs_O2"])
    else:
        r["passed"] = 1
    return r


def run_suite(key):
    if key in ("long",):
        return long_suite()
    if key == "godot":
        return godot_suite()
    if key == "mockups":
        return mockup_suite()
    if key == "tactical_trace":
        return trace_suite()
    return pytest_suite(key)


def total(s):
    return s.get("passed", 0) + s.get("failed", 0) + s.get("skipped", 0) + s.get("xfailed", 0) + s.get("aborted", 0)


def declared_match(tokens, name):
    return any(t == name or name.endswith("::" + t) or name.endswith("/" + t) or t == name.split("::")[-1]
               for t in tokens)


def compare(prev, cur, declared=()):
    """Return (regressions, declared_hits, soft). Lists of strings."""
    reg, decl, soft = [], [], []
    dec = set(declared)

    def flag(label, name):
        (decl if declared_match(dec, name) else reg).append(f"{label}: {name}")

    for key, c in cur["suites"].items():
        p = prev["suites"].get(key)
        if p is None:
            continue
        if key in ("net", "tactical_trace"):
            if p.get("status") in ("pass",) and c.get("status") != "pass":
                flag(f"{key} was passing, now {c.get('status')}", key)
            continue
        if c.get("status") == "absent":
            continue
        if total(c) < total(p):
            flag(f"{key} has fewer tests ({total(p)} -> {total(c)})", key)
        if key == "mockups":
            for n, v in c["mockups"].items():
                pv = p["mockups"].get(n)
                if pv and pv["ok"] and not v["ok"]:
                    if TIME_SOFT_RE.search(v["first_fail"] or ""):
                        soft.append(f"mockup time budget: {n}")
                    else:
                        flag("mockup newly failing", n)
            continue
        if key == "godot":
            for n, v in c["scripts"].items():
                pv = p["scripts"].get(n)
                if pv and pv["status"] == "pass" and v["status"] != "pass":
                    flag(f"godot script now {v['status']}", n)
            continue
        if key == "long":
            for sd, v in c.get("seeds", {}).items():
                pv = p.get("seeds", {}).get(sd)
                if pv and (pv.get("end") != v.get("end") or pv.get("ticks") != v.get("ticks")):
                    flag(f"long seed {sd} changed ({pv.get('end')},{pv.get('ticks')} -> {v.get('end')},{v.get('ticks')})",
                         f"seed:{sd}" if not declared_match(dec, sd) else sd)
            for sd in p.get("seeds", {}):
                if sd not in c.get("seeds", {}):
                    flag(f"long seed {sd} missing now", f"seed:{sd}")
        sf = c.get("scale_failures", {})
        for nid in sorted(set(c["failing_ids"]) - set(p["failing_ids"])):
            if key == "scale" and sf.get(nid, {}).get("kind") == "budget":
                soft.append(f"scale budget: {nid}")
            else:
                flag(f"{key} newly failing", nid)
    return reg, decl, soft


def verdict(prev, cur, declared=()):
    reg, decl, soft = compare(prev, cur, declared)
    return ("REGRESSION" if reg else "PASS"), reg, decl, soft


def markdown(rec, v=None):
    L = [f"# Integration baseline {rec['name']} ({rec['date']})", "",
         f"sha {rec['sha']}, OM_SCALE_CPU_FACTOR {rec['OM_SCALE_CPU_FACTOR']}, loadavg {rec['loadavg']}", "",
         "| suite | status | pass | fail | skip | xfail | abort | wall s |", "|---|---|---|---|---|---|---|---|"]
    for k, s in rec["suites"].items():
        L.append(f"| {k} | {s.get('status')} | {s['passed']} | {s['failed']} | {s['skipped']} | "
                 f"{s['xfailed']} | {s['aborted']} | {s['wall_s']} |")
    L += ["", f"Total wall: {sum(s['wall_s'] for s in rec['suites'].values()):.0f} s", ""]
    for k, s in rec["suites"].items():
        if s["failing_ids"]:
            L += [f"## {k}: failing", ""] + [f"- {i}" for i in s["failing_ids"]] + [""]
    if "seeds" in rec["suites"].get("long", {}):
        L += ["## long seeds", "", "| seed | archetype | end | ticks | alive | wall s |", "|---|---|---|---|---|---|"]
        for sd, r in rec["suites"]["long"]["seeds"].items():
            L.append(f"| {sd} | {r['archetype']} | {r['end']} | {r['ticks']} | {r['alive']} | {r['wall_s']} |")
        L.append("")
    if v:
        L += [f"## Verdict: {v[0]}", ""] + [f"- REGRESSION {x}" for x in v[1]] + [f"- declared {x}" for x in v[2]] \
            + [f"- soft {x}" for x in v[3]] + [""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--only", default="")
    ap.add_argument("--no-compare", action="store_true")
    ap.add_argument("--declare", default="")
    a = ap.parse_args()
    keys = [k for k in SUITES if not a.only or k in a.only.split(",")]
    declared = [l.strip() for l in Path(a.declare).read_text().splitlines() if l.strip() and not l.startswith("#")] \
        if a.declare else []
    date = subprocess.run(["date", "+%Y-%m-%d"], capture_output=True, text=True).stdout.strip()
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    rec = {"sha": sha, "date": date, "name": a.name,
           "OM_SCALE_CPU_FACTOR": os.environ.get("OM_SCALE_CPU_FACTOR", "1.35"),
           "loadavg": os.getloadavg(), "suites": {}}
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    prev = None
    if not a.no_compare:
        older = sorted(p for p in BASE_DIR.glob("*.json") if p.name != f"{date}_{a.name}.json")
        if older:
            prev = json.loads(older[-1].read_text())
    for k in keys:
        print(f"[integration_check] {k} ...", flush=True)
        rec["suites"][k] = run_suite(k)
        s = rec["suites"][k]
        print(f"[integration_check] {k}: {s['status']} pass={s['passed']} fail={s['failed']} wall={s['wall_s']}s", flush=True)
    v = None
    if prev:
        for k in list(prev["suites"]):
            if k not in rec["suites"]:
                del prev["suites"][k]
        v = verdict(prev, rec, declared)
    (BASE_DIR / f"{date}_{a.name}.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    (BASE_DIR / f"{date}_{a.name}.md").write_text(markdown(rec, v))
    if v is None:
        print("VERDICT: PASS (no comparison)")
        return 0
    print("VERDICT:", v[0])
    for x in v[1]:
        print("  REGRESSION", x)
    for x in v[2]:
        print("  declared", x)
    for x in v[3]:
        print("  soft", x)
    return 0 if v[0] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
