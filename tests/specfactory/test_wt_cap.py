# spec: docs/northstar/plans/2026-10-19-harness-enforcement-spec.md ### HARNESS-wt-cap, the worktree disk cap (rev 2)
# Rule pins: R-990-01@?
"""Tests for scripts/specfactory/wt.py (HARNESS-wt-cap): twelve cases, test_01 to test_12.

Fixture: a work repo with a bare origin and one push (test_pre_gate.py:29-45 and test_launch_check.py pattern);
worktrees are real `git worktree add` under tmp_path/wt. Cases 1, 3, 7, 9, 10 stub the module seams (measure_dir_mb,
free_gb, open_files, on_origin, porcelain, today, age_days) with monkeypatch(raising=False); cases 4, 5, 6, 8, 11 run
the CLI by subprocess with no stubs. Nothing touches ~/Projects/om-push/wt. Case 7's finished-open tree is held by a
real `sleep` whose cwd is <tree>/sub and the REAL open_files is used for it (the /proc scan works in tmp_path).
Case 11's first half is the control: it is green on the stub, and so is the exit-2 check of case 4's last line.

UNSTATED INTERFACE (reported; the builder implements exactly these):
- wt.main(argv=None) -> int is the entry point; it prints to stdout and returns the exit code (a SystemExit is
  also accepted); `python3 wt.py ...` is sys.exit(main()).
- Seam shapes: measure_dir_mb(path) -> number of MB; free_gb(path) -> number; open_files(path) -> bool;
  on_origin(repo, sha) -> bool; porcelain(path) -> list[str] of `git status --porcelain` lines (e.g. " M src.c",
  "?? .godot/"); today() -> "YYYY-MM-DD" str; age_days(path) -> float days. Path args may be str or Path.
  Age of an unflagged tree for the bypass rule is today() minus age_days(path); "older than 6 hours" is age_days > 0.25.
- --purpose takes the rest words (nargs="+"); the .wt-state purpose is them joined by single spaces.
- `new` prints `WT OK <path> <branch> slots <used>/<cap> wt <GB>/<cap> free <GB>`; GB are plain numbers.
  The refusal table names every active tree by directory name on the lines after `WT REFUSED`.
- `reap` prints one line per non-file directory under the root containing the directory name as a whole word:
  a removal (also in --dry-run) has the token REMOVE and the size in MB as an integer; a kept tree has the token
  KEEP and the reason word from the spec (active, pinned, pending, dirty, open-files, young, foreign, not-worktree).
- `status` table: a header line whose whitespace tokens are exactly the nine column names; one row per directory,
  tokens in column order (branch has no spaces); then a line starting `worktrees <n> slots <u>/<c> wt <g>/<c> free
  <g>/<f>` where n is the number of rows. `--json` prints one JSON document (a list), rows keyed by the column
  names, last element {"totals": {...}}. wt_gb is the sum of per-tree MB / 1024.
- The stub accepts every option the paragraph lists after the subcommand (the five subcommands the paragraph
  names: new, done, status, reap, check; the "six" of the brief has no sixth name).
- Fresh cache entries are used by `new` without calling measure_dir_mb; `new` creates the root files itself.
- An unflagged tree counts as young when today() - age_days >= --migration-date.
"""
import importlib.util
import json
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "wt.py"
_spec = importlib.util.spec_from_file_location("wt", SCRIPT)
wt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wt)

OWNER_PURPOSE = ["--owner", "me", "--purpose", "some words here"]


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


class World:
    def __init__(self, tmp_path):
        self.work = tmp_path / "work"
        self.origin = tmp_path / "origin.git"
        self.root = tmp_path / "wt"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", "--bare", str(self.origin)], check=True)
        self.work.mkdir()
        _git(self.work, "init", "-q", "-b", "main")
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        _git(self.work, "config", "commit.gpgsign", "false")
        (self.work / "src.c").write_text("int x;\n")
        _git(self.work, "add", "src.c")
        _git(self.work, "commit", "-q", "-m", "base")
        _git(self.work, "remote", "add", "origin", str(self.origin))
        _git(self.work, "push", "-q", "origin", "main")
        _git(self.work, "fetch", "-q", "origin")

    def add(self, name, state=None, owner="o", purpose="p words", marker=None):
        path = self.root / name
        _git(self.work, "worktree", "add", "-q", "-b", f"push/{name}", str(path), "origin/main")
        if state:
            (path / ".wt-state").write_text(f"{state} 2026-10-01 {owner} {purpose}\n")
        if marker:
            (path / marker).write_text("2026-10-01 push/x abc\n")
        return path

    def args(self, *more):
        return ["--root", str(self.root), "--repo", str(self.work), *more]

    def cli(self, *argv):
        r = subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True, timeout=120)
        return r.returncode, r.stdout, r.stderr


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def run_main(capsys, argv):
    try:
        rc = wt.main(argv)
    except SystemExit as e:
        rc = e.code
    return rc, capsys.readouterr().out


def stub(monkeypatch, *, mb=100, free=500.0, open_=False, on_origin=True, porcelain=None, today="2026-10-24", age=5.0):
    """Stub the seven seams; mb, porcelain and age may be dicts keyed by tree directory name."""
    def by_name(v, default):
        return lambda p, *a: v.get(Path(p).name, default) if isinstance(v, dict) else v
    set_ = lambda n, f: monkeypatch.setattr(wt, n, f, raising=False)  # noqa: E731
    set_("measure_dir_mb", by_name(mb, 100))
    set_("free_gb", (lambda p: free))
    set_("open_files", by_name(open_, False))
    set_("on_origin", lambda repo, sha: on_origin)
    set_("porcelain", by_name(porcelain or {}, []))
    set_("today", lambda: today)
    set_("age_days", by_name(age, 5.0))


def test_01_new_refuses_at_the_slot_cap_and_names_active_trees(world, monkeypatch, capsys):
    world.add("a1", "active")
    world.add("a2", "active")
    world.add("u1")  # unflagged: counts as a slot
    world.add("p1", "pinned")
    world.add("f1", "finished")
    stub(monkeypatch)
    rc, out = run_main(capsys, ["new", "t1_new", *OWNER_PURPOSE, *world.args("--slots", "3")])
    assert rc == 3, f"Westley 2026-10-24: only allocating a specific amount of those active flags to enforce the cap; exit {rc}: {out!r}"
    assert "WT REFUSED" in out
    assert "a1" in out and "a2" in out
    assert not (world.root / "t1_new").exists()
    # control: one more slot lets the same call through
    rc, out = run_main(capsys, ["new", "t1_new", *OWNER_PURPOSE, *world.args("--slots", "4")])
    assert rc == 0, f"exit {rc}: {out!r}"
    assert (world.root / "t1_new").is_dir()


def test_02_new_refuses_under_the_free_floor(world, monkeypatch, capsys):
    stub(monkeypatch, free=10.0)
    rc, out = run_main(capsys, ["new", "t2_new", *OWNER_PURPOSE, *world.args("--free-floor-gb", "60")])
    assert rc == 3, f"exit {rc}: {out!r}"
    assert "WT REFUSED" in out
    assert not (world.root / "t2_new").exists()


def test_03_new_refuses_over_disk_cap_unless_migrating(world, monkeypatch, capsys):
    world.add("a", "finished")
    (world.root / ".wt-sizes.json").write_text(json.dumps({"a": {"mb": 600, "measured_at": int(time.time())}}))
    stub(monkeypatch)

    def boom(p):
        raise AssertionError("fresh cache entry was re-measured")
    monkeypatch.setattr(wt, "measure_dir_mb", boom, raising=False)
    argv = ["new", "t3_new", *OWNER_PURPOSE, *world.args("--disk-cap-gb", "1", "--estimate-mb", "700")]
    rc, out = run_main(capsys, argv)  # 600 + 700 > 1024
    assert rc == 3, f"exit {rc}: {out!r}"
    assert "WT REFUSED" in out and not (world.root / "t3_new").exists()
    (world.root / ".wt-migrating").write_text("x\n")
    rc, out = run_main(capsys, argv)
    assert rc == 0, f"exit {rc}: {out!r}"
    assert "WT WARN migrating" in out
    assert (world.root / "t3_new").is_dir()


def test_04_new_creates_the_worktree_and_flag(world):
    rc, out, err = world.cli("new", "t4", *OWNER_PURPOSE, *world.args("--slots", "12", "--free-floor-gb", "0"))
    assert rc == 0, f"exit {rc}: {out!r} {err!r}"
    path = world.root / "t4"
    assert re.search(rf"^WT OK {re.escape(str(path))} push/t4 slots 1/12 wt \S+/\S+ free \S+", out, re.M), out
    assert (path / ".git").exists()
    assert (path / ".wt-state").read_text().strip() == f"active {date.today().isoformat()} me some words here"
    assert _git(world.work, "rev-parse", "push/t4").strip() == _git(world.work, "rev-parse", "origin/main").strip()
    rc, out, err = world.cli("new", "t4b", "--purpose", "x", *world.args())
    assert rc == 2, f"missing --owner must be a usage error, exit {rc}"


def test_05_done_refuses_a_sha_not_on_origin(world):
    path = world.add("t5", "active", "me", "build it")
    (path / "new.txt").write_text("x\n")
    _git(path, "add", "new.txt")
    _git(path, "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-q", "-m", "local only")
    sha = _git(path, "rev-parse", "HEAD").strip()
    before = (path / ".wt-state").read_text()
    rc, out, err = world.cli("done", str(path), sha, *world.args())
    assert rc == 3, f"exit {rc}: {out!r} {err!r}"
    assert "WT REFUSED" in out
    assert not (path / ".wt-done").exists()
    assert (path / ".wt-state").read_text() == before


def test_06_done_writes_marker_and_finishes_the_flag(world):
    path = world.add("t6", "active", "me", "build it now")
    sha = _git(path, "rev-parse", "HEAD").strip()  # origin/main itself: on origin
    rc, out, err = world.cli("done", str(path), sha, *world.args())
    assert rc == 0, f"exit {rc}: {out!r} {err!r}"
    assert (path / ".wt-done").read_text() == f"{date.today().isoformat()} push/t6 {sha}\n"
    assert (path / ".wt-state").read_text().strip() == f"finished {date.today().isoformat()} me build it now"
    assert _git(world.work, "rev-parse", "--verify", "push/t6").strip() == sha  # local branch left alone


def test_07_reap_dry_run_classifies_every_tree(world, monkeypatch, capsys):
    world.add("t_active", "active")
    world.add("t_pinned", "pinned")
    world.add("t_pending", marker=".wt-done-pending")
    world.add("t_done", marker=".wt-done")
    world.add("t_fin_clean", "finished")
    world.add("t_fin_dirty", "finished")
    fo = world.add("t_fin_open", "finished")
    world.add("t_unfl_old")
    world.add("t_unfl_young")
    foreign = world.root / "t_foreign"
    foreign.mkdir()
    (foreign / ".git").write_text("gitdir: /nonexistent/other/.git/worktrees/x\n")
    (world.root / "t_notwt").mkdir()
    (world.root / "loose.log").write_text("ignored\n")  # non-directory: ignored
    real_open = getattr(wt, "open_files", None)
    assert callable(real_open), "wt.open_files is not built"
    stub(monkeypatch, mb={"t_done": 500}, porcelain={"t_fin_dirty": [" M src.c"]},
         age={"t_unfl_old": 10.0, "t_unfl_young": 1.0})
    monkeypatch.setattr(wt, "open_files", lambda p: real_open(p) if Path(p).name == "t_fin_open" else False,
                        raising=False)
    (fo / "sub").mkdir()
    proc = subprocess.Popen(["sleep", "60"], cwd=fo / "sub")
    try:
        before = sorted(p.name for p in world.root.iterdir())
        rc, out = run_main(capsys, ["reap", "--dry-run", *world.args()])
        assert rc == 0, f"exit {rc}: {out!r}"
        lines = {}
        for name in ["t_active", "t_pinned", "t_pending", "t_done", "t_fin_clean", "t_fin_dirty", "t_fin_open",
                     "t_unfl_old", "t_unfl_young", "t_foreign", "t_notwt"]:
            hits = [ln for ln in out.splitlines() if re.search(rf"\b{name}\b", ln)]
            assert len(hits) == 1, f"{name}: {hits!r}\n{out}"
            lines[name] = hits[0]
        for name in ["t_done", "t_fin_clean", "t_unfl_old"]:
            assert "REMOVE" in lines[name] and "KEEP" not in lines[name], lines[name]
        assert "500" in lines["t_done"]
        for name, reason in [("t_active", "active"), ("t_pinned", "pinned"), ("t_pending", "pending"),
                             ("t_fin_dirty", "dirty"), ("t_fin_open", "open-files"), ("t_unfl_young", "young"),
                             ("t_foreign", "foreign"), ("t_notwt", "not-worktree")]:
            assert "KEEP" in lines[name] and reason in lines[name] and "REMOVE" not in lines[name], lines[name]
        assert sorted(p.name for p in world.root.iterdir() if p.name != ".wt-sizes.json") == \
            sorted(n for n in before if n != ".wt-sizes.json")
    finally:
        proc.terminate()
        proc.wait()


def test_08_reap_removes_build_output_dirt_only(world):
    fin = world.add("t8_fin", "finished")
    act = world.add("t8_act", "active")
    dirt = world.add("t8_dirt", "finished")
    (fin / ".godot").mkdir()
    (fin / ".godot" / "cache.bin").write_text("x\n")
    (dirt / "src.c").write_text("int y;\n")
    rc, out, err = world.cli("reap", *world.args())
    assert rc == 0, f"exit {rc}: {out!r} {err!r}"
    listing = _git(world.work, "worktree", "list", "--porcelain")
    assert str(fin) not in listing and not fin.exists()
    assert str(act) in listing and act.is_dir()
    assert str(dirt) in listing and (dirt / "src.c").read_text() == "int y;\n"
    assert listing.count("worktree ") == 3  # main checkout plus the two kept


def test_09_status_totals_in_table_and_json(world, monkeypatch, capsys):
    world.add("s_a1", "active")
    world.add("s_a2", "active")
    world.add("s_unfl")
    world.add("s_pin", "pinned")
    world.add("s_fin", "finished")
    world.add("s_pend", marker=".wt-done-pending")
    world.add("s_done", marker=".wt-done")
    mbs = {"s_a1": 1024, "s_a2": 1024, "s_unfl": 1024, "s_pin": 512, "s_fin": 1024, "s_pend": 256, "s_done": 256}
    stub(monkeypatch, mb=mbs, free=100.0, age=2.0)
    flags = world.args("--slots", "12", "--disk-cap-gb", "120", "--free-floor-gb", "60")
    rc, out = run_main(capsys, ["status", *flags])
    assert rc == 0, f"exit {rc}: {out!r}"
    lines = out.splitlines()
    cols = ["name", "state", "channel", "size_mb", "age_days", "branch", "on_origin", "dirty", "open_files"]
    assert any(ln.split() == cols for ln in lines), out
    expect = {"s_a1": "active", "s_a2": "active", "s_unfl": "unflagged", "s_pin": "pinned", "s_fin": "finished",
              "s_pend": "pending", "s_done": "done"}
    for name, state in expect.items():
        row = [ln.split() for ln in lines if ln.split()[:1] == [name]]
        assert len(row) == 1 and len(row[0]) == 9, (name, row)
        assert row[0][1] == state and int(float(row[0][3])) == mbs[name], row[0]
    assert re.search(r"^worktrees 7 slots 3/12 wt 5(\.0+)?/120(\.0+)? free 100(\.0+)?/60(\.0+)?\s*$", out, re.M), out
    rc, out = run_main(capsys, ["status", "--json", *flags])
    assert rc == 0, f"exit {rc}: {out!r}"
    data = json.loads(out)
    rows = {r["name"]: r for r in data[:-1]}
    assert set(rows) == set(expect) and all(set(cols) <= set(r) for r in rows.values())
    assert {n: r["state"] for n, r in rows.items()} == expect
    t = data[-1]["totals"]
    assert (t["worktrees"], t["slots_used"], t["slots_cap"]) == (7, 3, 12)
    assert abs(t["wt_gb"] - 5.0) < 0.01 and t["wt_cap_gb"] == 120
    assert t["free_gb"] == 100 and t["free_floor_gb"] == 60


def test_10_check_ok_warn_and_drift_cases(world, monkeypatch, capsys):
    world.add("c_a1", "active")
    world.add("c_a2", "active")
    base = world.args("--slots", "12", "--disk-cap-gb", "120", "--free-floor-gb", "60")

    def check(*more, **kw):
        stub(monkeypatch, **kw)
        rc, out = run_main(capsys, ["check", *base, *more])
        lines = [ln for ln in out.splitlines() if ln.startswith("STATUS wt")]
        assert len(lines) == 1, out
        return rc, lines[0]

    rc, line = check()
    assert rc == 0 and line.startswith("STATUS wt OK"), (rc, line)
    rc, line = check("--slots", "2")
    assert rc == 0 and line.startswith("STATUS wt WARN"), (rc, line)
    rc, line = check(mb=2048, free=500.0, **{})  # 2 trees x 2048 MB = 4 GB
    assert rc == 0 and line.startswith("STATUS wt OK"), (rc, line)
    rc, line = check("--disk-cap-gb", "1", mb=2048)
    assert rc == 1 and line.startswith("STATUS wt DRIFT"), (rc, line)
    rc, line = check(free=10.0)
    assert rc == 1 and line.startswith("STATUS wt DRIFT"), (rc, line)
    # bypass rule: unflagged tree created on or after the migration date and older than 6 hours
    world.add("c_unfl")
    md = ("--migration-date", "2026-10-20")
    rc, line = check(*md, age={"c_unfl": 2.0})
    assert rc == 1 and line.startswith("STATUS wt DRIFT") and "c_unfl" in line, (rc, line)
    rc, line = check(*md, age={"c_unfl": 0.1})  # 2.4 hours: inside the grace
    assert rc == 0 and line.startswith("STATUS wt OK"), (rc, line)
    rc, line = check(*md, age={"c_unfl": 9.0})  # created before the migration date: legacy
    assert rc == 0 and line.startswith("STATUS wt OK"), (rc, line)
    rc, line = check(age={"c_unfl": 2.0})  # no migration date: the rule is off
    assert rc == 0 and line.startswith("STATUS wt OK"), (rc, line)


def test_11_bare_worktree_add_makes_no_flag_and_status_sees_it_unflagged(world):
    path = world.add("t11")
    assert (path / ".git").exists() and not (path / ".wt-state").exists()  # control, green on the stub
    rc, out, err = world.cli("status", "--json", *world.args())
    assert rc == 0, f"exit {rc}: {out!r} {err!r}"
    data = json.loads(out)
    rows = {r["name"]: r for r in data[:-1]}
    assert rows["t11"]["state"] == "unflagged"
    assert data[-1]["totals"]["slots_used"] == 1


def test_12_check_with_missing_root_is_ok(tmp_path):
    rc = subprocess.run([sys.executable, str(SCRIPT), "check", "--root", str(tmp_path / "nope")],
                        capture_output=True, text=True, timeout=60)
    assert rc.returncode == 0, f"exit {rc.returncode}: {rc.stdout!r}"
    assert "STATUS wt OK no root" in rc.stdout


def test_13_untracked_pipe_binaries_and_uid_sidecars_are_build_outputs(world):
    def listed(name):
        rc, out, err = world.cli("reap", "--dry-run", *world.args())
        assert rc == 0, f"exit {rc}: {out!r} {err!r}"
        return [ln for ln in out.splitlines() if re.search(rf"\b{name}\b", ln)]

    def dirty(name):
        rc, out, err = world.cli("status", "--json", *world.args())
        assert rc == 0, f"exit {rc}: {out!r} {err!r}"
        return {r["name"]: r for r in json.loads(out)[:-1]}[name]["dirty"]

    t = world.add("t13_out", "finished")
    (t / "pipe").mkdir()
    (t / "pipe" / "ouroboros_pipe_dbg").write_bytes(b"\x7fELF-not-really")
    (t / "scenes").mkdir()
    (t / "scenes" / "x.gd.uid").write_text("uid://abc\n")
    (t / "landing-template.md").write_text("template\n")
    hits = listed("t13_out")
    assert len(hits) == 1 and hits[0].startswith("REMOVE t13_out"), \
        f"Westley 2026-10-21: Godot .import sidecars and dist/ count as build outputs for removal; untracked pipe binaries, .uid sidecars and landing-template.md are judged dirty: {hits!r}"
    assert dirty("t13_out") is False
    (t / "scenes" / "x.gd").write_text("extends Node\n")  # a .uid with its new script is real work
    hits = listed("t13_out")
    assert len(hits) == 1 and hits[0].startswith("KEEP t13_out dirty"), hits
    assert dirty("t13_out") is True
    c = world.add("t13_src", "finished")  # control: a modified tracked source file
    (c / "src.c").write_text("int changed;\n")
    hits = listed("t13_src")
    assert len(hits) == 1 and hits[0].startswith("KEEP t13_src dirty"), hits
    assert dirty("t13_src") is True
