# spec: docs/northstar/plans/2026-10-19-harness-enforcement-spec.md section 1 HARNESS-C4 (rev 3a), sections 3 and 5(d)
# Rule pins: R-990-01@?, R-991-01@?
"""Tests for scripts/specfactory/launch_check.sh (HARNESS-C4, the launch tool).

Fixture ids R-990-01 and R-991-01 are the gap ids written into the fixture args files (a fixture id, not a bible
rule: pinned @? above). No bible rule states the tool; the authority is the enforcement spec paragraph, quoted per
case. Every case builds a throwaway git repo `work` with a bare `origin` and a push (the test_pre_gate.py:29-45
pattern plus `git remote add origin` and a push), so `origin/main` exists, and runs the script DIRECTLY by its repo
path (a missing script is FileNotFoundError from subprocess.run; the file needs its exec bit).

The paragraph, by sentence, with the case that proves it:
  "a script identical on main prints `LAUNCH OK <sha> -` equal to `sha256sum`"        test_identical_script_*
  "one changed byte prints `LAUNCH REJECT ... differs`"                               test_one_changed_byte_*
  "a path not on main prints `not on origin/main`"                                    test_path_not_on_main_*
  "a script outside the workflows dir rejects"                                        test_script_outside_*
  "outside any checkout rejects"                                                      test_script_outside_any_checkout_*
  "an args file with the object form passes when the line holds the id and rejects
   when not, a plain string gives WARN"                                               test_args_*
  section 5(d): "`launch_check.sh` outside a checkout and with no `origin`"          test_no_origin_*
  "the same two for the args file when given"                                         test_args_file_*

UNSTATED INTERFACES (reported): output goes to stdout, one `LAUNCH ...` line per finding; a REJECT exits non-zero
and a clean run (WARN included) exits 0; the `<file>:<line>` of a gap spec is 1-based and relative to the repo
root; `gaps` is a top-level key of the args JSON; the script is run directly, so it needs its exec bit; the
reject text of the script-not-under-dir case is the spec's, `script not under
docs/northstar/plans/workflows_2026-10-07/`, with that trailing slash.

Controls (green without the script): the throwaway world builds, `origin/main` exists and holds the script, the
sha256 of the file equals the sha256 of `git show origin/main:<path>`, and a changed byte breaks `cmp`; both
planted violations are visible to plain git. Every other case needs the script.
"""
import hashlib
import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "specfactory" / "launch_check.sh"

WF = "docs/northstar/plans/workflows_2026-10-07"
JS_REL = f"{WF}/vg-fixture.js"
JS_TEXT = "// fixture workflow script\nconst x = 1\n"
ARGS_REL = f"{WF}/vg-fixture.args.json"
SPEC_REL = "docs/spec.md"
SPEC_TEXT = "# Spec\n\nGap R-990-01 is ruled here.\nGap R-991-01 is ruled there.\n"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _env(tmp_path: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CEILING_DIRECTORIES"] = str(tmp_path)  # a "no checkout" dir under tmp_path never finds a repo above
    return env


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com",
                           "-c", "commit.gpgsign=false", *args],
                          check=True, capture_output=True, text=True).stdout


def _put(repo: Path, rel: str, text: str) -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p


def make_world(tmp_path: Path, files=None, origin=True) -> Path:
    """`work` repo on main with `files` committed; with origin, a bare origin.git, `remote add origin` and a push."""
    work = tmp_path / "work"
    work.mkdir()
    _git(work, "init", "-q", "-b", "main")
    for rel, text in (files if files is not None else {JS_REL: JS_TEXT}).items():
        _put(work, rel, text)
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "first")
    if origin:
        bare = tmp_path / "origin.git"
        subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(bare)], check=True, capture_output=True,
                       env=_env(tmp_path))
        _git(work, "remote", "add", "origin", str(bare))
        _git(work, "push", "-q", "origin", "main")
    return work


def run_launch(tmp_path: Path, *args, cwd=None) -> subprocess.CompletedProcess:
    cwd = cwd if cwd is not None else tmp_path
    return subprocess.run([str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd,
                          env=_env(tmp_path), timeout=60)


def launch_lines(res) -> list:
    return [ln for ln in res.stdout.splitlines() if ln.startswith("LAUNCH ")]


def args_json(gaps) -> str:
    return json.dumps({"stage": "contract", "gaps": gaps}, indent=2) + "\n"


# ---------------------------------------------------------------- controls (green without the script)

def test_control_world_builds_with_the_script_on_origin_main(tmp_path):
    work = make_world(tmp_path)
    shown = subprocess.run(["git", "-C", str(work), "show", f"origin/main:{JS_REL}"], capture_output=True,
                           check=True).stdout
    assert shown == (work / JS_REL).read_bytes()
    assert hashlib.sha256(shown).hexdigest() == sha256_of(work / JS_REL)


def test_control_plain_git_sees_both_planted_violations(tmp_path):
    work = make_world(tmp_path)
    cat = lambda rel: subprocess.run(["git", "-C", str(work), "cat-file", "-e", f"origin/main:{rel}"],
                                     capture_output=True).returncode
    assert cat(JS_REL) == 0
    _put(work, f"{WF}/vg-new.js", "x\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "ahead")
    assert cat(f"{WF}/vg-new.js") != 0  # committed, not pushed: not on origin/main
    (work / JS_REL).write_text(JS_TEXT.replace("1", "2"))
    shown = subprocess.run(["git", "-C", str(work), "show", f"origin/main:{JS_REL}"], capture_output=True).stdout
    assert shown != (work / JS_REL).read_bytes()  # one changed byte: differs


# ---------------------------------------------------------------- the script, no args

def test_identical_script_prints_launch_ok_with_its_sha256_and_a_dash(tmp_path):
    # "a script identical on main prints `LAUNCH OK <sha> -` equal to `sha256sum`" (run from a dir that is no
    # checkout: the checkout is the script's, "git -C dirname rev-parse --show-toplevel")
    work = make_world(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    res = run_launch(tmp_path, work / JS_REL, cwd=elsewhere)
    sha = hashlib.sha256(JS_TEXT.encode()).hexdigest()
    assert launch_lines(res) == [f"LAUNCH OK {sha} -"], (res.stdout, res.stderr)
    assert res.returncode == 0, res.stdout + res.stderr


def test_identical_script_sha_equals_sha256sum_of_the_file(tmp_path):
    work = make_world(tmp_path)
    res = run_launch(tmp_path, work / JS_REL)
    out = subprocess.run(["sha256sum", str(work / JS_REL)], capture_output=True, text=True, check=True).stdout
    assert launch_lines(res) == [f"LAUNCH OK {out.split()[0]} -"], (res.stdout, res.stderr)


def test_one_changed_byte_is_rejected_as_differing_from_origin_main(tmp_path):
    # "one changed byte prints `LAUNCH REJECT ... differs`": reason `<path> differs from origin/main` (section 1)
    for how in ("uncommitted", "committed, not pushed"):
        sub = tmp_path / how.split(",")[0]
        sub.mkdir()
        work = make_world(sub)
        (work / JS_REL).write_text(JS_TEXT.replace("1", "2"))
        if how != "uncommitted":
            _git(work, "commit", "-q", "-am", "one byte")
        res = run_launch(sub, work / JS_REL)
        assert f"LAUNCH REJECT {JS_REL} differs from origin/main" in launch_lines(res), (how, res.stdout, res.stderr)
        assert not any(ln.startswith("LAUNCH OK") for ln in launch_lines(res)), (how, res.stdout)
        assert res.returncode != 0, (how, res.stdout + res.stderr)


def test_path_not_on_main_is_rejected_as_not_on_origin_main(tmp_path):
    # "a path not on main prints `not on origin/main`": untracked, and committed but not pushed
    for how in ("untracked", "committed"):
        sub = tmp_path / how
        sub.mkdir()
        work = make_world(sub)
        new = f"{WF}/vg-new.js"
        _put(work, new, "// new\n")
        if how == "committed":
            _git(work, "add", "-A")
            _git(work, "commit", "-q", "-m", "ahead of origin")
        res = run_launch(sub, work / new)
        assert f"LAUNCH REJECT {new} not on origin/main" in launch_lines(res), (how, res.stdout, res.stderr)
        assert not any(ln.startswith("LAUNCH OK") for ln in launch_lines(res)), (how, res.stdout)
        assert res.returncode != 0, (how, res.stdout + res.stderr)


def test_script_outside_the_workflows_dir_is_rejected(tmp_path):
    # "a script outside the workflows dir rejects": on main and identical, so only the directory rule can fire;
    # a sibling directory that merely starts with the same name is outside too.
    outside = ["scripts/vg-fixture.js", f"{WF}-evil/vg-fixture.js"]
    work = make_world(tmp_path, {JS_REL: JS_TEXT, **{rel: JS_TEXT for rel in outside}})
    for rel in outside:
        res = run_launch(tmp_path, work / rel)
        assert ("LAUNCH REJECT script not under docs/northstar/plans/workflows_2026-10-07/" in launch_lines(res)), \
            (rel, res.stdout, res.stderr)
        assert not any(ln.startswith("LAUNCH OK") for ln in launch_lines(res)), (rel, res.stdout)
        assert res.returncode != 0, (rel, res.stdout + res.stderr)


def test_script_outside_any_checkout_is_rejected(tmp_path):
    # "outside any checkout rejects": reason `not inside a checkout`
    nogit = tmp_path / "nogit"
    nogit.mkdir()
    js = _put(nogit, "vg-fixture.js", JS_TEXT)
    res = run_launch(tmp_path, js)
    assert "LAUNCH REJECT not inside a checkout" in launch_lines(res), (res.stdout, res.stderr)
    assert not any(ln.startswith("LAUNCH OK") for ln in launch_lines(res)), res.stdout
    assert res.returncode != 0, res.stdout + res.stderr


def test_no_origin_is_rejected(tmp_path):
    # section 5(d): "launch_check.sh outside a checkout and with no origin"; "`git fetch -q origin` (REJECT
    # `no origin` if it fails)": no remote at all, and a remote whose url does not exist.
    work = make_world(tmp_path, origin=False)
    res = run_launch(tmp_path, work / JS_REL)
    assert "LAUNCH REJECT no origin" in launch_lines(res), (res.stdout, res.stderr)
    assert not any(ln.startswith("LAUNCH OK") for ln in launch_lines(res)), res.stdout
    assert res.returncode != 0, res.stdout + res.stderr
    sub = tmp_path / "dead"
    sub.mkdir()
    dead = make_world(sub, origin=False)
    _git(dead, "remote", "add", "origin", str(sub / "does-not-exist.git"))
    res = run_launch(sub, dead / JS_REL)
    assert "LAUNCH REJECT no origin" in launch_lines(res), (res.stdout, res.stderr)
    assert res.returncode != 0, res.stdout + res.stderr


# ---------------------------------------------------------------- the args file

def _args_world(tmp_path: Path, gaps, spec_text=SPEC_TEXT) -> Path:
    return make_world(tmp_path, {JS_REL: JS_TEXT, ARGS_REL: args_json(gaps), SPEC_REL: spec_text})


def test_args_without_gaps_prints_launch_ok_with_both_shas(tmp_path):
    # "`LAUNCH OK <sha256 of script> <sha256 of args or ->`": the args sha is of the file
    work = make_world(tmp_path, {JS_REL: JS_TEXT, ARGS_REL: '{"stage": "contract"}\n'})
    res = run_launch(tmp_path, work / JS_REL, work / ARGS_REL)
    want = f"LAUNCH OK {sha256_of(work / JS_REL)} {sha256_of(work / ARGS_REL)}"
    assert launch_lines(res) == [want], (res.stdout, res.stderr)
    assert res.returncode == 0, res.stdout + res.stderr


def test_args_object_form_passes_when_the_named_line_holds_the_id(tmp_path):
    # "an args file with the object form passes when the line holds the id" (line 3 holds R-990-01, line 4 R-991-01)
    gaps = {"R-990-01": {"text": "ruled", "spec": f"{SPEC_REL}:3"},
            "R-991-01": {"text": "ruled too", "spec": f"{SPEC_REL}:4"}}
    work = _args_world(tmp_path, gaps)
    res = run_launch(tmp_path, work / JS_REL, work / ARGS_REL)
    want = f"LAUNCH OK {sha256_of(work / JS_REL)} {sha256_of(work / ARGS_REL)}"
    assert launch_lines(res) == [want], (res.stdout, res.stderr)
    assert res.returncode == 0, res.stdout + res.stderr


def test_args_object_form_rejects_when_the_named_line_lacks_the_id(tmp_path):
    # "... and rejects when not": reason `gap <id> not in the spec on main` (line 3 holds R-990-01, not R-991-01)
    gaps = {"R-990-01": {"text": "ruled", "spec": f"{SPEC_REL}:3"},
            "R-991-01": {"text": "wrong line", "spec": f"{SPEC_REL}:3"}}
    work = _args_world(tmp_path, gaps)
    res = run_launch(tmp_path, work / JS_REL, work / ARGS_REL)
    assert "LAUNCH REJECT gap R-991-01 not in the spec on main" in launch_lines(res), (res.stdout, res.stderr)
    assert "LAUNCH REJECT gap R-990-01 not in the spec on main" not in launch_lines(res), res.stdout
    assert not any(ln.startswith("LAUNCH OK") for ln in launch_lines(res)), res.stdout
    assert res.returncode != 0, res.stdout + res.stderr


def test_args_gap_line_is_read_from_origin_main_not_the_working_tree(tmp_path):
    # "the named line of <file> on `origin/main` must contain <id>": the working copy holds the id, main does not
    gaps = {"R-990-01": {"text": "ruled", "spec": f"{SPEC_REL}:2"}}  # line 2 of the pushed spec is blank
    work = _args_world(tmp_path, gaps)
    (work / SPEC_REL).write_text("# Spec\nGap R-990-01 added only here.\n")
    res = run_launch(tmp_path, work / JS_REL, work / ARGS_REL)
    assert "LAUNCH REJECT gap R-990-01 not in the spec on main" in launch_lines(res), (res.stdout, res.stderr)
    assert res.returncode != 0, res.stdout + res.stderr


def test_args_plain_string_gap_gives_a_warn_and_still_passes(tmp_path):
    # "a gap written as a plain string prints `LAUNCH WARN gap <id> has no spec line`" (and the run is OK: exit 0)
    gaps = {"R-990-01": "a ruling with no spec line", "R-991-01": {"text": "ruled", "spec": f"{SPEC_REL}:4"}}
    work = _args_world(tmp_path, gaps)
    res = run_launch(tmp_path, work / JS_REL, work / ARGS_REL)
    ok = f"LAUNCH OK {sha256_of(work / JS_REL)} {sha256_of(work / ARGS_REL)}"
    assert "LAUNCH WARN gap R-990-01 has no spec line" in launch_lines(res), (res.stdout, res.stderr)
    assert not any("R-991-01" in ln for ln in launch_lines(res)), res.stdout
    assert ok in launch_lines(res), (res.stdout, res.stderr)
    assert res.returncode == 0, res.stdout + res.stderr


def test_args_file_not_on_main_or_differing_is_rejected_like_the_script(tmp_path):
    # "the same two for the args file when given": `<path> not on origin/main`, `<path> differs from origin/main`
    work = make_world(tmp_path, {JS_REL: JS_TEXT, ARGS_REL: '{"stage": "contract"}\n'})
    (work / ARGS_REL).write_text('{"stage": "contracT"}\n')
    res = run_launch(tmp_path, work / JS_REL, work / ARGS_REL)
    assert f"LAUNCH REJECT {ARGS_REL} differs from origin/main" in launch_lines(res), (res.stdout, res.stderr)
    assert not any(ln.startswith("LAUNCH OK") for ln in launch_lines(res)), res.stdout
    assert res.returncode != 0, res.stdout + res.stderr
    sub = tmp_path / "new"
    sub.mkdir()
    work = make_world(sub)
    new = f"{WF}/vg-new.args.json"
    _put(work, new, "{}\n")
    res = run_launch(sub, work / JS_REL, work / new)
    assert f"LAUNCH REJECT {new} not on origin/main" in launch_lines(res), (res.stdout, res.stderr)
    assert not any(ln.startswith("LAUNCH OK") for ln in launch_lines(res)), res.stdout
    assert res.returncode != 0, res.stdout + res.stderr


# ---------------------------------------------------------------- method rev 3, HARNESS-mm-5 (spec G12)
# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md G12 "Fix" and "Pieces and owners" (HARNESS-mm-5)
# Interfaces fixed here (the spec leaves them open): the args JSON gains a top-level key `preflight`:
# {"files": [repo paths the spec names], "functions": [{"file": ..., "name": ...}], "fenced_tests": ["path::test"]};
# each check prints `LAUNCH REJECT <reason>` naming the file, function or test; a clean run still prints
# `LAUNCH OK`. Owner rows are read from docs/northstar/plans/push/pieces.toml on origin/main (owns and owns_glob);
# a function is found when `git show origin/main:<file>` has `def <name>` (py), `func <name>` (gd) or `<name>(`
# (c, sh); a fenced test is red at the base when pytest on a checkout of origin/main fails it (the python is
# $MERGE_GATE_PYTHON). The free-enum-slot check named in the spec has no input format and no case here.
PIECES_REL_MM = "docs/northstar/plans/push/pieces.toml"
PIECES_MM = ('[[piece]]\nid = "P-OWN"\nowns = ["scripts/owned.py"]\nowns_glob = ["lib/*.c"]\nacceptance = []\n'
             'depends_on = []\nstatus = { state = "queued" }\n')
PY_BASE = "def present_fn():\n    return 1\n"
RED_TEST = "def test_red():\n    assert False, 'not built yet'\n"
GREEN_TEST = "def test_green():\n    assert True\n"


def preflight_args(**pf):
    return json.dumps({"stage": "contract", "gaps": {}, "preflight": pf}, indent=2) + "\n"


def mm_world(tmp_path, **pf):
    files = {JS_REL: JS_TEXT, ARGS_REL: preflight_args(**pf), PIECES_REL_MM: PIECES_MM,
             "scripts/owned.py": PY_BASE, "lib/a.c": "int x;\n", "tests/t_red.py": RED_TEST,
             "tests/t_green.py": GREEN_TEST}
    return make_world(tmp_path, files=files)


def mm_run(tmp_path, work):
    env_py = {"MERGE_GATE_PYTHON": __import__("sys").executable}
    res = subprocess.run([str(SCRIPT), str(work / JS_REL), str(work / ARGS_REL)], capture_output=True, text=True,
                         cwd=tmp_path, env={**_env(tmp_path), **env_py}, timeout=120)
    return res, launch_lines(res)


def test_mm5_control_clean_preflight_still_prints_launch_ok(tmp_path):
    work = mm_world(tmp_path, files=["scripts/owned.py", "lib/a.c"],
                    functions=[{"file": "scripts/owned.py", "name": "present_fn"}],
                    fenced_tests=["tests/t_red.py::test_red"])
    res, ln = mm_run(tmp_path, work)
    assert ln and ln[-1].startswith("LAUNCH OK") and res.returncode == 0, (res.stdout, res.stderr)


def test_mm5_file_without_an_owner_row_rejects(tmp_path):
    work = mm_world(tmp_path, files=["scripts/owned.py", "scripts/unowned.py"])
    res, ln = mm_run(tmp_path, work)
    assert any(l.startswith("LAUNCH REJECT") and "scripts/unowned.py" in l for l in ln), (res.stdout, res.stderr)
    assert not any("scripts/owned.py" in l and "REJECT" in l for l in ln)
    assert res.returncode != 0


def test_mm5_named_function_missing_at_the_base_rejects(tmp_path):
    work = mm_world(tmp_path, functions=[{"file": "scripts/owned.py", "name": "absent_fn"}])
    res, ln = mm_run(tmp_path, work)
    assert any(l.startswith("LAUNCH REJECT") and "absent_fn" in l for l in ln), (res.stdout, res.stderr)
    assert res.returncode != 0


def test_mm5_fenced_test_that_is_green_at_the_base_rejects(tmp_path):
    work = mm_world(tmp_path, fenced_tests=["tests/t_green.py::test_green"])
    res, ln = mm_run(tmp_path, work)
    assert any(l.startswith("LAUNCH REJECT") and "test_green" in l for l in ln), (res.stdout, res.stderr)
    assert res.returncode != 0
