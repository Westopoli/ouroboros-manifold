# Rule pins: docs/stories/H-006.md
"""H-006 (the gate without pieces.toml): "The gate reads the story's flag from the story file and the merge message; it
needs no pieces row and no owner table, so a story branch lands by itself." Tests first; red on the base because
`merge_gate.sh` still reads the flag and the owners from pieces.toml and `story_flag` / `story_tests` do not exist.

INTERFACES FIXED HERE (from the story's "Story file lines the gate reads" and "Files")
  docs/stories/<id>.md on the candidate: lines `Flag: harness|client|sim|contract` (missing: sim), `Tests: <path> ...`.
  merge_gate_support.story_flag(path) -> str      the Flag value, `sim` when the line is missing.
  merge_gate_support.story_tests(path) -> list    the Tests paths, in order.
  merge_gate.sh <cand> origin/main <story id>     third argument is the story id; `GATE story REJECT missing <key>`.
The exact text after `GATE flag OK` is not stated by the story beyond "the current output line ... unchanged apart from the
source word": the tests match on `flag <impact> ` inside the line, as test_gate_flag.py does.

FIXTURE: the gate-repo of test_gate_reorder.py (`_build`) with test_gate_flag.py's copying Makefile. Story id B1.

POSITIVE CONTROLS (green today): the harness fixture's `GATE flag OK flag harness traces same footprint ok OK` line under
a pieces.toml row; the stage 0 base reject for a candidate missing the current origin/main; a complete story file raises
no `GATE story REJECT` line.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_gate_reorder as tgr  # noqa: E402
import test_gate_flag as tgf  # noqa: E402
from test_gate_flag import libs  # noqa: E402,F401  (session fixture: the prebuilt libraries)

REPO = tgf.REPO
GATE = tgf.GATE
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))
STORY_ID = "B1"
TEST_STUB = "def test_b1_ok():\n    assert True\n"
TEST_PATH = "tests/csim/test_b1_ok.py"


def _story(flag: str | None = "harness", tests: str | None = TEST_PATH) -> str:
    lines = ["# B1: fixture story", ""]
    if flag is not None:
        lines.append(f"Flag: {flag}")
    if tests is not None:
        lines.append(f"Tests: {tests}")
    lines.append("Scene: res://scenes/none.tscn")
    return "\n".join(lines) + "\n"


def _gate_story(tmp_path: Path, libs, story: str, candidate_files=None, pieces: str | None = "none", drop_pieces=True,
                gate_flags=()):
    """(rc, stdout lines, stdout+stderr) of merge_gate.sh on the gate-repo fixture whose candidate carries
    docs/stories/B1.md = story. pieces: "none" -> no pieces.toml at all (the gate repo's copy is deleted and
    MERGE_GATE_PIECES unset); a text -> that pieces.toml is overlaid and MERGE_GATE_PIECES points at it."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    files = {f"docs/stories/{STORY_ID}.md": story, TEST_PATH: TEST_STUB, **(candidate_files or {})}
    gate, cand = tgr._build(tmp_path, drift=False, gate_script=GATE, candidate_files=files,
                            base_files={"Makefile": tgf._mk(libs["A"])},
                            pieces=pieces if pieces != "none" else tgr.PIECES)
    env = {"PATH": tgr.GATE_PATH, "HOME": str(Path.home()), "MERGE_GATE_RUNS_CSV": str(tmp_path / "runs.csv"),
           "MERGE_GATE_PLACEHOLDERS": str(tmp_path / "placeholders.txt")}
    if pieces == "none":
        gate_root = gate.parent.parent.parent
        (gate_root / "docs" / "northstar" / "plans" / "push" / "pieces.toml").unlink()
        (tmp_path / "pieces.toml").unlink()
    else:
        env["MERGE_GATE_PIECES"] = str(tmp_path / "pieces.toml")
    r = subprocess.run(["bash", str(gate), *gate_flags, str(cand), "origin/main", STORY_ID], capture_output=True,
                       text=True, env=env, timeout=tgf.GATE_TIMEOUT_S)
    return r.returncode, r.stdout.splitlines(), r.stdout + r.stderr


# PREMISE (dumped): on this base the fixture's copied CLAUDE.md makes `GATE status REJECT STATUS method_pins DRIFT G01
# sentence missing ...:CLAUDE.md` in every run, so `rc == 0` is unreachable here whatever H-006 does. The OK tests therefore
# assert no REJECT line from any stage except status and the early_exit summary that repeats it.
def _rejects(lines):
    return [ln for ln in lines if re.match(r"GATE (?!row |status |early_exit )\S+ REJECT", ln)]


# ------------------------------------------------------------------ the readers

def test_story_flag_reads_the_flag_line_and_defaults_to_sim(tmp_path):
    """H-006 "the flag stage reads `Flag:` from `docs/stories/<id>.md` on the candidate (a missing line is `sim`)":
    story_flag(path) returns the value of the Flag line; a file without one returns `sim`."""
    import merge_gate_support as msp
    for flag in ("harness", "client", "sim", "contract"):
        p = tmp_path / f"{flag}.md"
        p.write_text(_story(flag))
        assert msp.story_flag(p) == flag
    p = tmp_path / "noflag.md"
    p.write_text(_story(None))
    assert msp.story_flag(p) == "sim"


def test_story_tests_reads_the_tests_paths(tmp_path):
    """H-006 "acceptance ids are the `Tests:` paths of the story file": story_tests(path) returns them in order."""
    import merge_gate_support as msp
    p = tmp_path / "s.md"
    p.write_text(_story("harness", "tests/a/test_a.py tests/b/test_b.py"))
    assert list(msp.story_tests(p)) == ["tests/a/test_a.py", "tests/b/test_b.py"]


# ------------------------------------------------------------------ the flag stage from the story file

def test_client_story_prints_the_client_flag_and_runs_the_client_list(tmp_path, libs):
    """H-006 Tests bullet 1: "A fixture candidate with a story file `Flag: client` runs the client tier list and prints
    `GATE flag client`". No pieces.toml exists: the client list (no regression_csim, no regression_lab) can only come from
    the story file."""
    rc, lines, out = _gate_story(tmp_path, libs, _story("client"), {"docs/x.md": "docs only\n"})
    flag = tgf._flag_line(lines)
    assert flag.startswith("GATE flag OK") and "flag client " in flag, out
    for stage in ("regression_csim", "regression_lab"):
        assert not tgf._has(lines, stage), f"GATE {stage} printed under a client story:\n{out}"


def test_contract_story_prints_the_contract_flag(tmp_path, libs):
    """H-006 Tests bullet 1: "`Flag: contract` prints the contract list": the flag line names contract and, a pin file
    being in the diff, is OK."""
    rc, lines, out = _gate_story(tmp_path, libs, _story("contract"),
                                 {"csrc/ouroboros_sim.h": (REPO / "csrc/ouroboros_sim.h").read_text() + "\n/* pin */\n"})
    flag = tgf._flag_line(lines)
    assert flag.startswith("GATE flag OK") and "flag contract " in flag, out


def test_control_harness_fast_tier_line_is_unchanged_under_a_pieces_row(tmp_path, libs):
    """Positive control (H-006 Tests bullet 1, parenthesis): "the current `--tier fast` output line for a `harness`
    fixture is unchanged apart from the source word". Green today from the pieces.toml row; the story file says the same."""
    pieces = tgr._pieces("csrc/stub.c", "docs/x.md", f"docs/stories/{STORY_ID}.md", TEST_PATH) + 'impact = "harness"\n'
    rc, lines, out = _gate_story(tmp_path, libs, _story("harness"), {"docs/x.md": "docs only\n"}, pieces=pieces)
    flag = tgf._flag_line(lines)
    assert re.match(r"GATE flag OK flag harness traces same footprint ok OK ", flag), out


# ------------------------------------------------------------------ no pieces.toml, no owner table

def test_no_pieces_toml_at_all_gates_to_ok(tmp_path, libs):
    """H-006 Tests bullet 2: "A fixture with no pieces.toml at all gates to OK (the dependency is gone)"."""
    rc, lines, out = _gate_story(tmp_path, libs, _story("harness"), {"docs/x.md": "docs only\n"})
    assert not _rejects(lines), out


def test_a_file_no_story_names_is_not_a_reject(tmp_path, libs):
    """H-006 Tests bullet 3: "A diff touching a file no story names is not a reject (owner_lint gone)". The pieces row
    here owns only csrc/stub.c; the diff adds unowned.txt."""
    pieces = tgr._pieces("csrc/stub.c")
    rc, lines, out = _gate_story(tmp_path, libs, _story("harness"), {"unowned.txt": "nobody owns me\n"}, pieces=pieces)
    assert not _rejects(lines), out
    assert not tgf._has(lines, "owner_lint"), f"stage 5c owner_lint still prints:\n{out}"


def test_control_stage0_rejects_a_candidate_missing_origin_main(tmp_path, libs, tmp_path_factory):
    """Positive control (H-006 Tests bullet 3, second half): "the existing footprint fence still rejects a candidate
    missing the current origin/main (stage 0 unchanged)": origin gains a commit the candidate does not contain, the gate
    prints `GATE base REJECT` and exits 1. Green today."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    files = {f"docs/stories/{STORY_ID}.md": _story("harness"), TEST_PATH: TEST_STUB}
    gate, cand = tgr._build(tmp_path, drift=False, gate_script=GATE, candidate_files=files,
                            base_files={"Makefile": tgf._mk(libs["A"])}, pieces=tgr.PIECES)
    other = tmp_path_factory.mktemp("other")
    tgr._git(other, "clone", "-q", str(tmp_path / "origin.git"), "o")
    tgr._commit(other / "o", "newer.txt", "origin moved on\n")
    tgr._git(other / "o", "push", "-q", "origin", "main")
    env = {"PATH": tgr.GATE_PATH, "HOME": str(Path.home()), "MERGE_GATE_RUNS_CSV": str(tmp_path / "runs.csv"),
           "MERGE_GATE_PIECES": str(tmp_path / "pieces.toml"),
           "MERGE_GATE_PLACEHOLDERS": str(tmp_path / "placeholders.txt")}
    r = subprocess.run(["bash", str(gate), str(cand), "origin/main", STORY_ID], capture_output=True, text=True, env=env,
                       timeout=tgf.GATE_TIMEOUT_S)
    assert any(ln.startswith("GATE base REJECT") for ln in r.stdout.splitlines()), r.stdout + r.stderr
    assert r.returncode == 1, r.stdout + r.stderr


# ------------------------------------------------------------------ a story file missing a key

@pytest.mark.parametrize("key,story", [("Tests", _story("harness", None)), ("Flag", _story(None, TEST_PATH))])
def test_story_file_missing_a_key_rejects(tmp_path, libs, key, story):
    """H-006 "A story file missing `Flag:` or `Tests:` is `GATE story REJECT missing <key>`" (Tests bullet 4)."""
    pieces = tgr._pieces("csrc/stub.c", "docs/x.md", f"docs/stories/{STORY_ID}.md", TEST_PATH) + 'impact = "harness"\n'
    rc, lines, out = _gate_story(tmp_path, libs, story, {"docs/x.md": "docs only\n"}, pieces=pieces)
    assert any(ln.startswith(f"GATE story REJECT missing {key}") for ln in lines), out
    assert rc == 1, out


def test_control_a_complete_story_file_raises_no_story_reject(tmp_path, libs):
    """Positive control for the missing-key detector: the same fixture with both keys prints no `GATE story REJECT`."""
    pieces = tgr._pieces("csrc/stub.c", "docs/x.md", f"docs/stories/{STORY_ID}.md", TEST_PATH) + 'impact = "harness"\n'
    rc, lines, out = _gate_story(tmp_path, libs, _story("harness"), {"docs/x.md": "docs only\n"}, pieces=pieces)
    assert not any(ln.startswith("GATE story REJECT") for ln in lines), out


# ------------------------------------------------------------------ H-020: the story that fixes a red sweep

SWEPT_SHA = "c4131ea5a0e1eb8098688c43c093c80892ae92ad"  # the swept sha of the REJECT row (docs/stories/H-020.md Machine lines)
OTHER_SHA = "0123456789abcdef0123456789abcdef01234567"
SWEEPS_REL = "docs/northstar/plans/push/sweeps.md"
# Row shape of sweeps.md on origin/main: | Date-time UTC | Main sha | Verdict | New | Red | Red ids |
SWEEPS_HEADER = "| Date-time UTC | Main sha | Verdict | New | Red | Red ids |\n|---|---|---|---|---|---|\n"


def _gate_sweep(tmp_path: Path, libs, story: str):
    """(lines, out) of the gate on the gate-repo fixture whose own sweeps.md (the file the status stage reads from the gate
    repo) ends in a REJECT row at SWEPT_SHA with red: 3, and whose candidate carries `story` as docs/stories/B1.md."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    files = {f"docs/stories/{STORY_ID}.md": story, TEST_PATH: TEST_STUB, "docs/x.md": "docs only\n"}
    gate, cand = tgr._build(tmp_path, drift=False, gate_script=GATE, candidate_files=files,
                            base_files={"Makefile": tgf._mk(libs["A"])}, pieces=tgr.PIECES)
    # _overlay replaces the symlink to this tree's sweeps.md; a plain write_text would write through it.
    tgr._overlay(gate.parent.parent.parent, SWEEPS_REL,
                 SWEEPS_HEADER + f"| 2026-10-30 16:12 | {SWEPT_SHA} | REJECT | new: tests/x.py::t | red: 3 | |\n")
    env = {"PATH": tgr.GATE_PATH, "HOME": str(Path.home()), "MERGE_GATE_RUNS_CSV": str(tmp_path / "runs.csv"),
           "MERGE_GATE_PIECES": str(tmp_path / "pieces.toml"),
           "MERGE_GATE_PLACEHOLDERS": str(tmp_path / "placeholders.txt")}
    r = subprocess.run(["bash", str(gate), str(cand), "origin/main", STORY_ID], capture_output=True, text=True, env=env,
                       timeout=tgf.GATE_TIMEOUT_S)
    return r.stdout.splitlines(), r.stdout + r.stderr


def test_h020_fixes_sweep_equal_to_the_reject_row_passes_status_as_warn(tmp_path, libs):
    """H-020 (a): "a candidate story with `Fixes-sweep:` equal to the REJECT row's sha passes the status stage as WARN with
    the line `GATE status WARN sweep red <n> at <sha> fixed by <story id>`" (DEC-sweep-fix-exemption-2026-10-30)."""
    lines, out = _gate_sweep(tmp_path, libs, _story("harness") + f"Fixes-sweep: {SWEPT_SHA}\n")
    want = f"GATE status WARN sweep red 3 at {SWEPT_SHA} fixed by {STORY_ID}"
    assert any(ln.startswith(want) for ln in lines), out
    assert not any(ln.startswith("GATE status REJECT sweep red") for ln in lines), out


def test_h020_fixes_sweep_of_another_sha_still_rejects(tmp_path, libs):
    """H-020 (b): "a different sha still rejects `GATE status REJECT sweep red`": the exemption is for the story that fixes
    this sweep only. Green today (no exemption exists) and stays green."""
    lines, out = _gate_sweep(tmp_path, libs, _story("harness") + f"Fixes-sweep: {OTHER_SHA}\n")
    assert any(ln.startswith("GATE status REJECT sweep red") for ln in lines), out


def test_h020_control_no_fixes_sweep_line_rejects_on_a_reject_row(tmp_path, libs):
    """H-020 (c), positive control: no Fixes-sweep line and a REJECT last row is still `GATE status REJECT sweep red 3 at
    <sha>`, so a red (a) means the exemption is missing, not that the fixture lost the row. Green today."""
    lines, out = _gate_sweep(tmp_path, libs, _story("harness"))
    assert any(ln.startswith(f"GATE status REJECT sweep red 3 at {SWEPT_SHA}") for ln in lines), out


def test_h020_malformed_fixes_sweep_rejects_as_bad_fixes_sweep(tmp_path, libs):
    """H-020 (d): "a malformed line rejects `bad fixes-sweep`" (story-check accepts an optional 40-hex Fixes-sweep line)."""
    lines, out = _gate_sweep(tmp_path, libs, _story("harness") + "Fixes-sweep: nope\n")
    assert any(ln.startswith("GATE story REJECT") and "bad fixes-sweep" in ln for ln in lines), out


# ------------------------------------------------------------------ H-020 round 2: a given tier skips the flag stage

def test_h020_tier_given_skips_the_flag_stage_and_runs_no_trace(tmp_path, libs):
    """H-020 (e), DEC-gate-tier-given-skips-flag-2026-10-30: "`--tier full` with a valid harness story prints `GATE flag SKIP
    tier given` and runs no flag trace". The story stage still ran (the story is valid) and the tier is the given one."""
    rc, lines, out = _gate_story(tmp_path, libs, _story("harness"), {"docs/x.md": "docs only\n"},
                                 gate_flags=("--tier", "full"))
    assert "GATE tier full" in lines, out
    assert any(ln.startswith("GATE flag SKIP tier given") for ln in lines), out
    assert not any(re.match(r"GATE flag (OK|REJECT)", ln) for ln in lines), out
    # The flag stage's traces would print `trace failed checksum_trace.py` on the toy library; the full tier's own
    # `GATE checksum_trace` stage is a different stage and may print.
    assert "trace failed" not in out and "traces " not in "\n".join(l for l in lines if l.startswith("GATE flag")), out


def test_h020_control_no_tier_given_runs_the_flag_stage(tmp_path, libs):
    """H-020 (f), positive control for (e): the same candidate without `--tier` runs the flag stage (it prints `GATE flag`
    and not `SKIP`; on a toy library it may reject). Green today."""
    rc, lines, out = _gate_story(tmp_path, libs, _story("harness"), {"docs/x.md": "docs only\n"})
    flag = [ln for ln in lines if ln.startswith("GATE flag ")]
    assert flag and not flag[0].startswith("GATE flag SKIP"), out
