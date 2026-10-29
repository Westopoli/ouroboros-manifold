#!/usr/bin/env python3
"""wt.py: HARNESS-wt-cap. The only way a worktree under ~/Projects/om-push/wt is created, finished or reaped.

`.wt-state` is `<active|pinned|finished> <YYYY-MM-DD> <owner> <purpose...>`; derived states pending (`.wt-done-pending`),
done (`.wt-done` only), unflagged (neither: it holds a slot), foreign, not-worktree. Subcommands: new, done, status, reap,
check. Exit 0 ok, 2 usage, 3 refused, 1 error or DRIFT. Caps are the named drafts below (spec: harness-enforcement-spec,
HARNESS-wt-cap); every cap has a CLI override.
"""
import argparse
import fcntl
import fnmatch
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

DRAFT_WT_ACTIVE_SLOTS = 12
DRAFT_WT_DISK_CAP_GB = 120
DRAFT_WT_SIZE_ESTIMATE_MB = 700
DRAFT_WT_FREE_FLOOR_GB = 60
DRAFT_WT_SIZE_CACHE_MIN = 60
DRAFT_WT_UNFLAGGED_GRACE_HOURS = 6
DRAFT_WT_MIGRATING_MAX_DAYS = 7
REAP_UNFLAGGED_DAYS = 3  # Westley 2026-10-21
DRAFT_WT_BUILD_OUTPUTS = [".godot/", "build/", "dist/", "obj/", "obj_dbg/", "*.import", "*.so", "*.o",
                          "pipe/ouroboros_pipe", "pipe/ouroboros_pipe_dbg", ".sdk_engineer_report.md",
                          ".wt-state", ".wt-done", ".wt-done-pending",
                          "*.uid", "landing-template.md"]  # rev 2, HARNESS-wt-cap-2
DEFAULT_ROOT = Path.home() / "Projects" / "om-push" / "wt"
REPO = Path(__file__).resolve().parents[2]
COLS = ["name", "state", "size_mb", "age_days", "branch", "on_origin", "dirty", "open_files"]


def git(*args, cwd=None):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def measure_dir_mb(path) -> int:
    r = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True)
    return int(r.stdout.split()[0]) // 1024 if r.stdout.split() else 0


def free_gb(path) -> float:
    return shutil.disk_usage(str(path)).free / 2**30


def open_files(path) -> bool:
    p, me = str(path).rstrip("/"), str(os.getpid())
    for pid in (d for d in os.listdir("/proc") if d.isdigit() and d != me):
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd")
            if cwd == p or cwd.startswith(p + "/"):
                return True
            if p in Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace"):
                return True
        except OSError:
            continue
    return False


def on_origin(repo, sha) -> bool:
    rc, out = git("branch", "-r", "--contains", sha, cwd=repo)
    return rc == 0 and any(ln.strip().startswith("origin/") and "->" not in ln for ln in out.splitlines())


def porcelain(path) -> list:
    rc, out = git("status", "--porcelain", "--untracked-files=all", cwd=path)
    return out.splitlines() if rc == 0 else []


def today() -> str:
    return date.today().isoformat()


def age_days(path) -> float:
    path = Path(path)
    for f in (".wt-state", ".wt-done"):
        try:
            return (time.time() - datetime.strptime(read_words(path / f)[0 if f == ".wt-done" else 1], "%Y-%m-%d").timestamp()) / 86400
        except (OSError, IndexError, ValueError):
            continue
    return (time.time() - (path / ".git").stat().st_mtime) / 86400


def read_words(f) -> list:
    return Path(f).read_text().split()


def is_build_output(line) -> bool:
    rel = line[3:].split(" -> ")[-1].strip('"')
    return any(rel.startswith(e) if e.endswith("/") else fnmatch.fnmatch(rel, e) for e in DRAFT_WT_BUILD_OUTPUTS)


def classify(root, repo, name) -> str:
    t = Path(root) / name
    g = t / ".git"
    if not g.is_file():
        return "not-worktree"
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=repo)[1]
    if not g.read_text().strip().startswith(f"gitdir: {common}/worktrees/"):
        return "foreign"
    if (t / ".wt-done-pending").exists():
        return "pending"
    if (t / ".wt-state").exists():
        return (read_words(t / ".wt-state") or ["unflagged"])[0]
    return "done" if (t / ".wt-done").exists() else "unflagged"


def trees(root) -> list:
    return sorted(p.name for p in Path(root).iterdir() if p.is_dir())


def sizes(root, names, remeasure, write=True) -> dict:
    cf = Path(root) / ".wt-sizes.json"
    try:
        cache = json.loads(cf.read_text())
    except (OSError, ValueError):
        cache = {}
    out, now = {}, time.time()
    for n in names:
        e = cache.get(n)
        if remeasure or not e or now - e["measured_at"] > cfg("cache_min") * 60:
            e = {"mb": int(measure_dir_mb(Path(root) / n)), "measured_at": int(now)}
        out[n] = cache[n] = e
    if write:
        cf.write_text(json.dumps({n: cache[n] for n in names}))
    return {n: e["mb"] for n, e in out.items()}


CFG = {}


def cfg(k):
    return CFG[k]


def headroom(root, mbs):
    return f"slots {{}}/{cfg('slots')} wt {sum(mbs.values()) / 1024:.1f}/{cfg('disk_cap_gb'):g} free {free_gb(root):.1f}"


def slots_used(root, repo, names):
    return sum(classify(root, repo, n) in ("active", "unflagged") for n in names)


def refuse(root, repo, names, mbs, reason):
    print(f"WT REFUSED {reason}")
    for n in names:
        if classify(root, repo, n) == "active":
            print("  " + (Path(root) / n / ".wt-state").read_text().strip() + f"  [{n}]")
    print(headroom(root, mbs).format(slots_used(root, repo, names)))
    return 3


def cmd_new(a, root, repo):
    root.mkdir(parents=True, exist_ok=True)
    with open(root / ".wt.lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        names = trees(root)
        mbs = sizes(root, names, False)
        used = slots_used(root, repo, names)
        migrating = (root / ".wt-migrating").exists()
        rf = lambda why: refuse(root, repo, names, mbs, why)  # noqa: E731
        if used >= cfg("slots"):
            return rf(f"slot cap: {used} of {cfg('slots')} slots held")
        if free_gb(root) < cfg("free_floor_gb"):
            return rf(f"free space {free_gb(root):.1f} GB under the floor {cfg('free_floor_gb'):g}")
        if not migrating and sum(mbs.values()) + cfg("estimate_mb") > cfg("disk_cap_gb") * 1024:
            return rf(f"disk cap: {sum(mbs.values())} MB plus {cfg('estimate_mb'):g} MB over {cfg('disk_cap_gb'):g} GB")
        if (root / a.name).exists():
            return rf(f"{root / a.name} exists")
        if migrating:
            print("WT WARN migrating: disk cap suspended")
        branch = a.branch or f"push/{a.name}"
        rc, out = git("-C", str(repo), "worktree", "add", "-q", "-b", branch, str(root / a.name), a.base)
        if rc:
            print(f"WT ERROR git worktree add failed: {out}")
            return 1
        (root / a.name / ".wt-state").write_text(f"active {today()} {a.owner} {' '.join(a.purpose)}\n")
    print(f"WT OK {root / a.name} {branch} " + headroom(root, mbs).format(used + 1))
    return 0


def cmd_done(a, root, repo):
    path = Path(a.path)
    state = classify(path.parent, repo, path.name) if path.is_dir() else "not-worktree"
    if state in ("not-worktree", "foreign", "pinned", "pending"):
        print(f"WT REFUSED {path} is {state}")
        return 3
    if not on_origin(repo, a.sha):
        print(f"WT REFUSED {a.sha} is not on any origin/* branch: push first")
        return 3
    branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=path)[1]
    words = read_words(path / ".wt-state") if (path / ".wt-state").exists() else []
    owner, purpose = (words[2], " ".join(words[3:])) if len(words) > 2 else ("unknown", "-")
    (path / ".wt-done").write_text(f"{today()} {branch} {a.sha}\n")
    (path / ".wt-state").write_text(f"finished {today()} {owner} {purpose}\n")
    print(f"WT OK {path} finished")
    return 0


def row(root, repo, name, mb):
    t, st = Path(root) / name, classify(root, repo, name)
    r = dict.fromkeys(COLS, "-")
    r.update(name=name, state=st, size_mb=mb, age_days=round(age_days(t), 1) if st != "not-worktree" else "-")
    if st not in ("foreign", "not-worktree"):
        sha = git("rev-parse", "HEAD", cwd=t)[1]
        r.update(branch=git("rev-parse", "--abbrev-ref", "HEAD", cwd=t)[1] or "-", on_origin=bool(sha and on_origin(repo, sha)),
                 dirty=any(not is_build_output(ln) for ln in porcelain(t)), open_files=bool(open_files(t)))
    return r


def totals(root, repo, names, mbs):
    return {"worktrees": len(names), "slots_used": slots_used(root, repo, names), "slots_cap": cfg("slots"),
            "wt_gb": sum(mbs.values()) / 1024, "wt_cap_gb": cfg("disk_cap_gb"), "free_gb": free_gb(root),
            "free_floor_gb": cfg("free_floor_gb")}


def cmd_status(a, root, repo):
    names = trees(root) if root.is_dir() else []
    mbs = sizes(root, names, True)
    rows = [row(root, repo, n, mbs[n]) for n in names]
    t = totals(root, repo, names, mbs)
    if a.json:
        print(json.dumps(rows + [{"totals": t}]))
        return 0
    fmt = lambda v: {True: "yes", False: "no"}.get(v, str(v))  # noqa: E731
    print(" ".join(COLS))
    for r in rows:
        print(" ".join(fmt(r[c]) for c in COLS))
    print(f"worktrees {t['worktrees']} slots {t['slots_used']}/{t['slots_cap']} wt {t['wt_gb']:.1f}/{t['wt_cap_gb']:g} "
          f"free {t['free_gb']:.1f}/{t['free_floor_gb']:g}")
    return 0


def cmd_reap(a, root, repo):
    verdicts, rc = [], 0
    for n in trees(root):
        t, st = root / n, classify(root, repo, n)
        why = st if st in ("not-worktree", "foreign", "active", "pinned", "pending") else None
        if not why and st == "unflagged" and age_days(t) <= REAP_UNFLAGGED_DAYS:
            why = "young"
        if not why and open_files(t):
            why = "open-files"
        if not why and not on_origin(repo, git("rev-parse", "HEAD", cwd=t)[1]):
            why = "not-on-origin"
        if not why and not all(is_build_output(ln) for ln in porcelain(t)):
            why = "dirty"
        verdicts.append((n, why))
    cands = sorted(((int(measure_dir_mb(root / n)), n) for n, why in verdicts if not why), reverse=True)
    removed = {n for _, n in cands[:a.max]} if a.max is not None else {n for _, n in cands}
    mb_of = {n: mb for mb, n in cands}
    for n, why in verdicts:
        if why or n not in removed:
            print(f"KEEP {n} {why or 'max'}")
            continue
        print(f"REMOVE {n} {mb_of[n]} MB" + (" (dry run)" if a.dry_run else ""))
        if a.dry_run:
            continue
        dirt = porcelain(root / n)
        if not all(is_build_output(ln) for ln in dirt):
            print(f"KEEP {n} dirty (changed since the check)")
            continue
        base = ["-C", str(repo), "worktree", "remove", str(root / n)]
        r = subprocess.run(["git", *base], capture_output=True, text=True)
        if r.returncode and dirt:  # --force ignores all dirt: only reached when every dirty line is a build output
            r = subprocess.run(["git", *base, "--force"], capture_output=True, text=True)
        if r.returncode:
            print(f"ERROR {n} git worktree remove failed: {r.stderr.strip()}")
            rc = 1
    if not a.dry_run:
        git("-C", str(repo), "worktree", "prune")
    return rc


def cmd_check(a, root, repo):
    if not root.is_dir():
        print("STATUS wt OK no root")
        return 0
    names = trees(root)
    mbs = sizes(root, names, False, write=False)
    t = totals(root, repo, names, mbs)
    drift, mig = [], root / ".wt-migrating"
    if mig.exists() and time.time() - mig.stat().st_mtime > DRAFT_WT_MIGRATING_MAX_DAYS * 86400:
        drift.append(f"migration marker older than {DRAFT_WT_MIGRATING_MAX_DAYS} days")
    elif not mig.exists() and t["wt_gb"] > t["wt_cap_gb"]:
        drift.append(f"wt {t['wt_gb']:.1f} GB over the cap {t['wt_cap_gb']:g}")
    if t["free_gb"] < t["free_floor_gb"]:
        drift.append(f"free {t['free_gb']:.1f} GB under the floor {t['free_floor_gb']:g}")
    if cfg("migration_date"):
        for n in names:
            if classify(root, repo, n) != "unflagged" or age_days(root / n) <= DRAFT_WT_UNFLAGGED_GRACE_HOURS / 24:
                continue
            if (date.fromisoformat(today()) - timedelta(days=age_days(root / n))).isoformat() >= cfg("migration_date"):
                drift.append(f"unflagged tree made after the migration date (bypass): {root / n}")
    head = f"slots {t['slots_used']}/{t['slots_cap']} wt {t['wt_gb']:.1f}/{t['wt_cap_gb']:g} free {t['free_gb']:.1f}/{t['free_floor_gb']:g}"
    if drift:
        print(f"STATUS wt DRIFT {'; '.join(drift)}; {head}")
        return 1
    print(f"STATUS wt {'WARN' if t['slots_used'] >= t['slots_cap'] else 'OK'} {head}")
    return 0


def main(argv=None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root")
    common.add_argument("--repo")
    common.add_argument("--slots", type=int)
    common.add_argument("--disk-cap-gb", type=float)
    common.add_argument("--free-floor-gb", type=float)
    common.add_argument("--estimate-mb", type=float)
    common.add_argument("--cache-min", type=float)
    common.add_argument("--migration-date")
    ap = argparse.ArgumentParser(prog="wt.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new", parents=[common])
    p.add_argument("name")
    p.add_argument("--owner", required=True)
    p.add_argument("--purpose", required=True, nargs="+")
    p.add_argument("--base", default="origin/main")
    p.add_argument("--branch")
    p = sub.add_parser("done", parents=[common])
    p.add_argument("path")
    p.add_argument("sha")
    p = sub.add_parser("status", parents=[common])
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("reap", parents=[common])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max", type=int)
    sub.add_parser("check", parents=[common])
    a = ap.parse_args(argv)
    root, repo = Path(a.root) if a.root else DEFAULT_ROOT, Path(a.repo) if a.repo else REPO
    md = a.migration_date
    if not md and (root / ".wt-migration-date").is_file():
        md = (root / ".wt-migration-date").read_text().split()[0]
    pick = lambda v, d: d if v is None else v  # noqa: E731
    CFG.update(slots=pick(a.slots, DRAFT_WT_ACTIVE_SLOTS), disk_cap_gb=pick(a.disk_cap_gb, DRAFT_WT_DISK_CAP_GB),
               free_floor_gb=pick(a.free_floor_gb, DRAFT_WT_FREE_FLOOR_GB), estimate_mb=pick(a.estimate_mb, DRAFT_WT_SIZE_ESTIMATE_MB),
               cache_min=pick(a.cache_min, DRAFT_WT_SIZE_CACHE_MIN), migration_date=md)
    return {"new": cmd_new, "done": cmd_done, "status": cmd_status, "reap": cmd_reap, "check": cmd_check}[a.cmd](a, root, repo)


if __name__ == "__main__":
    sys.exit(main())
