# Rule pins: 
# spec: docs/northstar/plans/2026-10-29-layered-gate-spec.md sections 2 (layer 1), 4 (the HARNESS-gate-flag paragraph) and 8 (F4, F5, F6, N14, N15, N17, N20)
"""HARNESS-gate-flag (lane H unit 5): the per-piece `impact` flag, verified by the two determinism traces against the
base and by the diff footprint, and the tier the flag picks. Tests first; red on the stacked tree because
`scripts/specfactory/gate_flag.py` and the merge gate's `flag` stage do not exist.

INTERFACES FIXED HERE (all from the spec; where it is silent the test asserts less, see the gaps list in the report)
  gate_flag.py impact <pieces.toml> <id>[,<id>...]   stdout: the strictest flag (contract > sim > client > harness,
                                                     a missing key is sim); exit 2 on a value outside the four.
  gate_flag.py verdict <candidate> <base_ref> <impact> --merge-root <dir> --lib <path>
                                                     stdout: a line `flag <impact> traces <same|differ> footprint
                                                     <ok|first offending path> <OK|REJECT> <reason>`; exit 0 OK, 1 REJECT.
                                                     Traces: checksum_trace.py (seed 1, 60 regions, 500 ticks, features 6)
                                                     and tactical_trace.py (seed 1, 1500 ticks) on --lib, compared with the
                                                     base's pair by the tools' own --compare.
  trace cache (section 8 N17, which overrides section 2/4 "<sha>"): <merge-root>/trace_cache/<csrc tree id>-<Makefile
                                                     blob id>.{strategic,tactical}.txt, both ids from `git rev-parse
                                                     <sha>:csrc` and `git rev-parse <sha>:Makefile`; the files hold the
                                                     trace tools' stdout, header line included.
  footprint (section 8 F5): harness -> empty diff under csrc/ autoload/ scenes/ project.godot (the Makefile is OUTSIDE it);
                                                     client -> empty diff under csrc/.
  pin files (section 2 + N20): csrc/ouroboros_sim.h docs/northstar/spec_factory/signatures.toml csrc/om_internal.h
                                                     csrc/pipe/pipe_internal.h docs/architecture.md.
  merge_gate.sh: stage `flag` right after `make`: `GATE flag OK|REJECT <the verdict line>`; `GATE flag SKIP revert mode`
                                                     under --revert (F4); with no --tier the flag picks the suites,
                                                     `--tier full` wins over the flag. The piece's flag comes from the
                                                     `impact` key of its row in MERGE_GATE_PIECES.

FIXTURES. The verdict is driven on small git repos whose Makefile copies a prebuilt real libouroboros.so (built once per
session from this tree's csrc; libB has one constant moved so its tactical trace differs, libC lacks
om_world_checksum_full, libE returns NULL from om_world_new for 60 regions so the strategic trace tool fails). The gate
stage is driven on the gate-repo fixture of test_gate_reorder.py (`_build`), whose base Makefile is replaced by the same
copying Makefile. Footprint rejects run with --lib pointing at nothing: a trace attempt would show as a different line.

POSITIVE CONTROLS: a Makefile edit that keeps the trace is OK under harness (g1); a sim-flagged edit that moves the trace
writes the trace cache while the footprint reject writes none (g5); `--tier full` prints today's stage list under a harness
flag (g9); the same diff without --revert REJECTs (g10); a good lib raises none of the failure verdicts (g11 to g13).
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO / "scripts" / "specfactory"
GATE_FLAG = SPEC_DIR / "gate_flag.py"
PIECES_PY = SPEC_DIR / "pieces.py"
CHECKSUM_TRACE = SPEC_DIR / "checksum_trace.py"
TACTICAL_TRACE = SPEC_DIR / "tactical_trace.py"
GATE = SPEC_DIR / "merge_gate.sh"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_gate_reorder as tgr  # noqa: E402  (the gate-repo fixture: _build, _pieces)

PY = sys.executable
REAL_GIT = shutil.which("git")
# Trace parameters of the spec (section 2 layer 1 and the HARNESS-gate-flag paragraph); they show in the tools' header lines.
STRATEGIC_ARGS = ["--seed", "1", "--regions", "60", "--ticks", "500", "--features", "6"]
TACTICAL_ARGS = ["--seed", "1", "--ticks", "1500"]
STRATEGIC_HEADER = re.compile(r"seed=1 regions=60 ticks=500")
TACTICAL_HEADER = re.compile(r"seed=1 ticks=1500")
PIN_FILES = ["csrc/ouroboros_sim.h", "docs/northstar/spec_factory/signatures.toml", "csrc/om_internal.h",
             "csrc/pipe/pipe_internal.h", "docs/architecture.md"]
VERDICT_TIMEOUT_S = 300
GATE_TIMEOUT_S = 600


# ------------------------------------------------------------------ the libraries (built once per session)

def _traces(lib: Path):
    s = subprocess.run([PY, str(CHECKSUM_TRACE), "--lib", str(lib), *STRATEGIC_ARGS], capture_output=True, text=True)
    t = subprocess.run([PY, str(TACTICAL_TRACE), "--lib", str(lib), *TACTICAL_ARGS], capture_output=True, text=True)
    assert s.returncode == 0 and t.returncode == 0, (s.stderr[-400:], t.stderr[-400:])
    return s.stdout, t.stdout


def _sed(path: Path, old: str, new: str):
    text = path.read_text()
    assert old in text, f"fixture patch target gone from {path}: {old}"
    path.write_text(text.replace(old, new))


@pytest.fixture(scope="session")
def libs(tmp_path_factory):
    """{A, B, C, E: Path to a real libouroboros.so}. A: this tree. B: OM_ECON_OSCILLATION_AMPLITUDE 6.0 -> 6.5 (tactical
    trace differs from A). C: om_world_checksum_full renamed away. E: om_world_new returns NULL for 60 regions."""
    root = tmp_path_factory.mktemp("flaglibs")
    dirs = {}
    for name in "ABCE":
        d = root / name
        shutil.copytree(REPO / "csrc", d / "csrc", ignore=shutil.ignore_patterns("pipe"))
        shutil.copy(REPO / "Makefile", d / "Makefile")
        dirs[name] = d
    _sed(dirs["B"] / "csrc" / "om_constants.h", "OM_ECON_OSCILLATION_AMPLITUDE 6.0", "OM_ECON_OSCILLATION_AMPLITUDE 6.5")
    for f in (dirs["C"] / "csrc" / "checksum_full.c", dirs["C"] / "csrc" / "ouroboros_sim.h"):
        f.write_text(f.read_text().replace("om_world_checksum_full", "om_world_checksum_fullx"))
    _sed(dirs["E"] / "csrc" / "region.c", "om_world *om_world_new(uint32_t n_regions, uint64_t seed) {",
         "om_world *om_world_new(uint32_t n_regions, uint64_t seed) {\n    if (n_regions == 60u) return NULL;")
    procs = {n: subprocess.Popen(["make", "-s", "-C", str(d), "libouroboros.so"], stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True) for n, d in dirs.items()}
    for n, p in procs.items():
        out, _ = p.communicate(timeout=300)
        assert p.returncode == 0, f"fixture lib {n} did not build: {out[-600:]}"
    out = {n: dirs[n] / "libouroboros.so" for n in dirs}
    a_s, a_t = _traces(out["A"])
    b_s, b_t = _traces(out["B"])
    assert (a_s, a_t) != (b_s, b_t), "fixture libB does not move any trace: the 'differ' tests would be vacuous"
    return out


# ------------------------------------------------------------------ a small repo for the verdict

def _git(cwd, *args, check=True):
    r = subprocess.run([REAL_GIT, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                       cwd=str(cwd), capture_output=True, text=True, check=check)
    return r.stdout.strip()


def _mk(lib: Path, extra: str = "") -> str:
    """A Makefile whose build copies a prebuilt library; the second target is the gate's debug-build stage."""
    return f"libouroboros.so:\n\tcp {lib} $@\nlibouroboros_dbg.so:\n\ttouch $@\n{extra}"


def _commit(repo: Path, files: dict, msg: str = "c") -> str:
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


def _repo(tmp_path: Path, base_lib: Path, base_makefile: str | None = None):
    """(repo, base sha): Makefile copying base_lib, a stub csrc, one doc, one pin file."""
    repo = tmp_path / "vrepo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    base = _commit(repo, {"Makefile": base_makefile if base_makefile is not None else _mk(base_lib),
                          "csrc/stub.c": "int om_stub(void) { return 0; }\n",
                          "csrc/ouroboros_sim.h": "/* header */\n",
                          "docs/readme.md": "base\n"}, "base")
    return repo, base


def _shim(tmp_path: Path):
    """(env, log path): a `git` ahead on PATH that records every invocation then runs the real git."""
    d = tmp_path / "shim"
    d.mkdir()
    log = tmp_path / "git_calls.log"
    log.write_text("")
    (d / "git").write_text(f'#!/bin/bash\necho "$@" >> {log}\nexec {REAL_GIT} "$@"\n')
    (d / "git").chmod(0o755)
    return {**os.environ, "PATH": f"{d}:{os.environ['PATH']}"}, log


def _verdict(repo: Path, base: str, impact: str, lib: Path, merge_root: Path, env=None):
    r = subprocess.run([PY, str(GATE_FLAG), "verdict", str(repo), base, impact, "--merge-root", str(merge_root),
                        "--lib", str(lib)], capture_output=True, text=True, env=env, timeout=VERDICT_TIMEOUT_S)
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith("flag ")]
    return r.returncode, (lines[0] if lines else ""), r.stdout + r.stderr


def _rejects(line: str) -> bool:
    return re.search(r"\bREJECT\b", line) is not None


def _key(repo: Path, ref: str) -> str:
    return f"{_git(repo, 'rev-parse', ref + ':csrc')}-{_git(repo, 'rev-parse', ref + ':Makefile')}"


def _cache_files(merge_root: Path):
    d = merge_root / "trace_cache"
    return sorted(p.name for p in d.iterdir()) if d.is_dir() else []


def _worktree_adds(log: Path) -> int:
    return sum(1 for ln in log.read_text().splitlines() if "worktree" in ln and " add" in " " + ln.split("worktree", 1)[1])


# ------------------------------------------------------------------ group 1 (F5): harness, Makefile edit that moves the trace

def test_g1_harness_makefile_edit_that_moves_the_trace_rejects_traces_differ(tmp_path, libs):
    """Section 8 F5 group (1): a `harness` diff that edits only the Makefile so the built trace moves is REJECT with
    `traces differ`; the Makefile is outside the harness footprint, so the footprint field is ok."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"Makefile": _mk(libs["B"])})
    rc, line, out = _verdict(repo, base, "harness", libs["B"], tmp_path / "mr")
    assert rc == 1, out
    assert line.startswith("flag harness ") and "traces differ" in line and "footprint ok" in line, out
    assert _rejects(line), out


def test_g1_control_harness_makefile_edit_that_keeps_the_trace_is_ok(tmp_path, libs):
    """Positive control for g1: the same harness flag with a Makefile edit that does not move the trace is OK, traces same."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"Makefile": _mk(libs["A"], "# comment only\n")})
    rc, line, out = _verdict(repo, base, "harness", libs["A"], tmp_path / "mr")
    assert rc == 0, out
    assert "traces same" in line and "footprint ok" in line and not _rejects(line), out


def test_g1_gate_stage_rejects_harness_flag_with_a_moved_trace(tmp_path, libs):
    """Group (1) through the gate: `GATE flag REJECT ... traces differ` on the gate-repo fixture, exit 1."""
    rc, lines, out = _gate(tmp_path, libs, "harness", {"Makefile": _mk(libs["B"])})
    flag = _flag_line(lines)
    assert flag.startswith("GATE flag REJECT") and "traces differ" in flag, out
    assert rc == 1, out


# ------------------------------------------------------------------ group 2: the same diff flagged sim

def test_g2_sim_flag_with_a_moved_trace_is_ok_and_names_the_first_differing_tick(tmp_path, libs):
    """Group (2): the group (1) diff flagged `sim` is OK and the line names the first differing tick (libB moves the
    tactical trace at tick 10)."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"Makefile": _mk(libs["B"])})
    rc, line, out = _verdict(repo, base, "sim", libs["B"], tmp_path / "mr")
    assert rc == 0, out
    assert "traces differ" in line and not _rejects(line), out
    assert re.search(r"tick 10\b", line), out


def test_g2_control_sim_flag_with_the_same_trace_is_ok_traces_same(tmp_path, libs):
    """Negative control for g2: sim with an unmoved trace is OK and does not claim a difference."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"Makefile": _mk(libs["A"], "# comment only\n")})
    rc, line, out = _verdict(repo, base, "sim", libs["A"], tmp_path / "mr")
    assert rc == 0 and "traces same" in line and "traces differ" not in line, out


def test_g2_gate_stage_accepts_sim_flag_with_a_moved_trace(tmp_path, libs):
    """Group (2) through the gate: `GATE flag OK ... traces differ`."""
    rc, lines, out = _gate(tmp_path, libs, "sim", {"Makefile": _mk(libs["B"])})
    flag = _flag_line(lines)
    assert flag.startswith("GATE flag OK") and "traces differ" in flag, out


# ------------------------------------------------------------------ group 3: contract needs a pin file in the diff

def test_g3_contract_flag_without_a_pin_file_rejects(tmp_path, libs):
    """Group (3): a `contract` diff with no pin file is REJECT `contract flag without a contract change`."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"csrc/stub.c": "int om_stub(void) { return 1; }\n"})
    rc, line, out = _verdict(repo, base, "contract", libs["A"], tmp_path / "mr")
    assert rc == 1 and _rejects(line), out
    assert "contract flag without a contract change" in line, out


@pytest.mark.parametrize("pin", PIN_FILES)
def test_g3_contract_flag_with_a_pin_file_in_the_diff_is_ok(tmp_path, libs, pin):
    """Group (3) positive: any of the five pin files in the diff makes `contract` OK (section 2 list plus N20's docs/architecture.md)."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {pin: "changed pin file\n"})
    rc, line, out = _verdict(repo, base, "contract", libs["A"], tmp_path / "mr")
    assert rc == 0 and not _rejects(line), out


def test_g3_contract_flag_may_move_the_trace(tmp_path, libs):
    """Group (3): a contract diff with a pin file and a moved trace is OK (`contract` may differ)."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"csrc/ouroboros_sim.h": "/* header v2 */\n", "Makefile": _mk(libs["B"])})
    rc, line, out = _verdict(repo, base, "contract", libs["B"], tmp_path / "mr")
    assert rc == 0 and "traces differ" in line and not _rejects(line), out


def test_g3_gate_stage_contract_without_and_with_a_pin_file(tmp_path, libs):
    """Group (3) through the gate: REJECT without a pin file, OK with csrc/ouroboros_sim.h in the diff."""
    rc, lines, out = _gate(tmp_path / "no_pin", libs, "contract", {"csrc/stub.c": "int om_stub(void) { return 2; }\n"})
    assert _flag_line(lines).startswith("GATE flag REJECT") and "contract flag without a contract change" in _flag_line(lines), out
    rc, lines, out = _gate(tmp_path / "pin", libs, "contract", {"csrc/ouroboros_sim.h": (REPO / "csrc/ouroboros_sim.h").read_text() + "\n/* pin touched */\n"})
    assert _flag_line(lines).startswith("GATE flag OK"), out


# ------------------------------------------------------------------ group 4 (F5): docs-only diff

@pytest.mark.parametrize("impact", ["harness", "client", "sim"])
def test_g4_docs_only_diff_is_ok_under_harness_client_and_sim(tmp_path, libs, impact):
    """Group (4) as amended by F5: a docs-only diff is OK under harness, client and sim, with traces same."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"docs/readme.md": "edited\n"})
    rc, line, out = _verdict(repo, base, impact, libs["A"], tmp_path / "mr")
    assert rc == 0 and f"flag {impact} " in line and "traces same" in line and not _rejects(line), out


def test_g4_docs_only_diff_under_contract_rejects(tmp_path, libs):
    """Group (4) as amended by F5: under `contract` a docs-only diff is REJECT `contract flag without a contract change`."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"docs/readme.md": "edited\n"})
    rc, line, out = _verdict(repo, base, "contract", libs["A"], tmp_path / "mr")
    assert rc == 1 and _rejects(line) and "contract flag without a contract change" in line, out


def test_g4_gate_stage_docs_only_diff_under_harness_is_ok(tmp_path, libs):
    """Group (4) through the gate (the positive control of the stage): `GATE flag OK ... traces same`."""
    rc, lines, out = _gate(tmp_path, libs, "harness", {"docs/x.md": "docs only\n"})
    flag = _flag_line(lines)
    assert flag.startswith("GATE flag OK") and "traces same" in flag, out


# ------------------------------------------------------------------ group 5: footprint rejects before any trace

FOOTPRINT_REJECTS = [("harness", "csrc/x.c"), ("harness", "autoload/x.gd"), ("harness", "scenes/x.tscn"),
                     ("harness", "project.godot"), ("client", "csrc/x.c")]


@pytest.mark.parametrize("impact,path", FOOTPRINT_REJECTS)
def test_g5_footprint_reject_comes_before_any_trace(tmp_path, libs, impact, path):
    """Group (5): a harness (client) diff under its footprint is REJECT naming the first offending path; no trace ran:
    --lib points at nothing and the verdict is not `trace failed`, the trace cache stays empty, no base worktree was added."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {path: "x\n"})
    env, log = _shim(tmp_path)
    rc, line, out = _verdict(repo, base, impact, tmp_path / "no_such_lib.so", tmp_path / "mr", env)
    assert rc == 1 and _rejects(line) and path in line, out
    assert "trace failed" not in out and "cannot verify" not in out, out
    assert _cache_files(tmp_path / "mr") == [], "a trace was written before the footprint reject"
    assert _worktree_adds(log) == 0, log.read_text()


def test_g5_control_the_same_diff_under_sim_does_run_the_traces(tmp_path, libs):
    """Positive control for g5's 'no trace ran' detector: the autoload diff under `sim` (no footprint) writes the trace cache
    and builds the base worktree, so an empty cache in g5 means the traces were skipped."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"autoload/x.gd": "x\n"})
    env, log = _shim(tmp_path)
    rc, line, out = _verdict(repo, base, "sim", libs["A"], tmp_path / "mr", env)
    assert rc == 0, out
    assert _cache_files(tmp_path / "mr"), "sim run left no trace cache"
    assert _worktree_adds(log) >= 1, log.read_text()


@pytest.mark.parametrize("impact,path", [("client", "autoload/x.gd"), ("harness", "tests/specfactory/test_x.py"),
                                         ("harness", "Makefile")])
def test_g5_negative_control_paths_outside_the_footprint_do_not_reject(tmp_path, libs, impact, path):
    """Negative control for g5 (F5): client may touch autoload/, harness may touch tests/ and the Makefile (rewritten
    to a copy of the same library, so the trace is unmoved): no footprint reject, footprint field ok."""
    repo, base = _repo(tmp_path, libs["A"])
    files = {path: _mk(libs["A"], "# same lib\n")} if path == "Makefile" else {path: "x\n"}
    _commit(repo, files)
    rc, line, out = _verdict(repo, base, impact, libs["A"], tmp_path / "mr")
    assert rc == 0 and "footprint ok" in line and not _rejects(line), out


def test_g5_gate_stage_harness_diff_under_autoload_rejects_without_a_trace(tmp_path, libs):
    """Group (5) through the gate: `GATE flag REJECT` naming autoload/x.gd, and the gate's merge root has no trace cache."""
    rc, lines, out = _gate(tmp_path, libs, "harness", {"autoload/x.gd": "x\n"})
    flag = _flag_line(lines)
    assert flag.startswith("GATE flag REJECT") and "autoload/x.gd" in flag, out
    assert _cache_files(tmp_path) == [], out


# ------------------------------------------------------------------ group 6: the trace cache

def test_g6_first_run_builds_the_base_once_and_writes_both_pairs(tmp_path, libs):
    """Group (6) first half (and section 8 N17): with an empty cache the base is built in one throwaway worktree, its pair
    is written under its key and the candidate's pair under the candidate's key; the files carry the spec's trace parameters."""
    repo, base = _repo(tmp_path, libs["A"])
    cand = _commit(repo, {"Makefile": _mk(libs["A"], "# edit\n")})
    env, log = _shim(tmp_path)
    mr = tmp_path / "mr"
    rc, line, out = _verdict(repo, base, "harness", libs["A"], mr, env)
    assert rc == 0, out
    assert _worktree_adds(log) == 1, log.read_text()
    bk, ck = _key(repo, base), _key(repo, cand)
    assert bk != ck
    for key in (bk, ck):
        assert (mr / "trace_cache" / f"{key}.strategic.txt").is_file(), _cache_files(mr)
        assert (mr / "trace_cache" / f"{key}.tactical.txt").is_file(), _cache_files(mr)
    assert STRATEGIC_HEADER.search((mr / "trace_cache" / f"{ck}.strategic.txt").read_text())
    assert TACTICAL_HEADER.search((mr / "trace_cache" / f"{ck}.tactical.txt").read_text())


def test_g6_second_run_against_the_same_base_reads_the_cache(tmp_path, libs):
    """Group (6) second half: a second candidate on the same base runs with no `git worktree add`, its own pair is
    written, and the verdict is unchanged."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"Makefile": _mk(libs["A"], "# edit one\n")})
    env, log = _shim(tmp_path)
    mr = tmp_path / "mr"
    rc1, line1, out1 = _verdict(repo, base, "harness", libs["A"], mr, env)
    assert rc1 == 0 and _worktree_adds(log) == 1, out1
    cand2 = _commit(repo, {"Makefile": _mk(libs["A"], "# edit two\n")})
    rc2, line2, out2 = _verdict(repo, base, "harness", libs["A"], mr, env)
    assert rc2 == 0 and "traces same" in line2, out2
    assert _worktree_adds(log) == 1, "the base was built again:\n" + log.read_text()
    assert (mr / "trace_cache" / f"{_key(repo, cand2)}.strategic.txt").is_file()


@pytest.mark.parametrize("seed_lib,expect_rc,expect", [("B", 1, "traces differ"), ("A", 0, "traces same")])
def test_g6_the_verdict_uses_the_cached_base_pair(tmp_path, libs, seed_lib, expect_rc, expect):
    """Group (6): the base pair comes from the cache, not from a rebuild. The cache entry of the base key is seeded with
    libB's traces (control: libA's); the candidate's library is libA. Seeded B -> differ (REJECT under harness); seeded A -> same.
    No worktree is added in either case."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"Makefile": _mk(libs["A"], "# edit\n")})
    mr = tmp_path / "mr"
    (mr / "trace_cache").mkdir(parents=True)
    s, t = _traces(libs[seed_lib])
    (mr / "trace_cache" / f"{_key(repo, base)}.strategic.txt").write_text(s)
    (mr / "trace_cache" / f"{_key(repo, base)}.tactical.txt").write_text(t)
    env, log = _shim(tmp_path)
    rc, line, out = _verdict(repo, base, "harness", libs["A"], mr, env)
    assert rc == expect_rc and expect in line, out
    assert _worktree_adds(log) == 0, log.read_text()


def test_g6_a_records_commit_on_main_does_not_miss_the_cache(tmp_path, libs):
    """Section 8 N17: the key is the csrc tree plus the Makefile blob, so a base that only differs by a docs commit finds the
    entry the previous base wrote: no `git worktree add` for the second base."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"Makefile": _mk(libs["A"], "# first candidate\n")})
    env, log = _shim(tmp_path)
    mr = tmp_path / "mr"
    rc, line, out = _verdict(repo, base, "harness", libs["A"], mr, env)
    assert rc == 0 and _worktree_adds(log) == 1, out
    records = _commit(repo, {"docs/readme.md": "a records push\n"})
    _commit(repo, {"Makefile": _mk(libs["A"], "# second candidate\n")})
    rc, line, out = _verdict(repo, records, "harness", libs["A"], mr, env)
    assert rc == 0 and "traces same" in line, out
    assert _worktree_adds(log) == 1, "a docs-only base commit forced a rebuild:\n" + log.read_text()


# ------------------------------------------------------------------ group 7: gate_flag.py impact

def _pieces_toml(tmp_path: Path, rows: dict) -> Path:
    text = ""
    for pid, impact in rows.items():
        text += f'[[piece]]\nid = "{pid}"\nowns = []\nacceptance = []\ndepends_on = []\n'
        if impact is not None:
            text += f'impact = "{impact}"\n'
        text += 'status = { state = "queued" }\n\n'
    f = tmp_path / "pieces.toml"
    f.write_text(text)
    return f


def _impact(toml: Path, ids: str):
    r = subprocess.run([PY, str(GATE_FLAG), "impact", str(toml), ids], capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stdout + r.stderr


@pytest.mark.parametrize("ids,expect", [("H,C", "client"), ("H,S", "sim"), ("H,K", "contract"), ("C,S,K", "contract"),
                                        ("H,N", "sim"), ("H", "harness"), ("H,H2", "harness"), ("N", "sim"), ("K", "contract")])
def test_g7_impact_returns_the_strictest_flag_of_a_comma_list(tmp_path, ids, expect):
    """Group (7): the strictest of contract > sim > client > harness; a row without the key counts as sim (N)."""
    toml = _pieces_toml(tmp_path, {"H": "harness", "H2": "harness", "C": "client", "S": "sim", "K": "contract", "N": None})
    rc, out, raw = _impact(toml, ids)
    assert rc == 0 and out == expect, raw


def test_g7_impact_exits_2_on_a_value_outside_the_four(tmp_path):
    """Group (7): `impact = "bogus"` exits 2, alone or inside a list of valid rows; positive control: the four values exit 0."""
    toml = _pieces_toml(tmp_path, {"H": "harness", "B": "bogus"})
    assert _impact(toml, "B")[0] == 2
    assert _impact(toml, "H,B")[0] == 2
    (tmp_path / "ok").mkdir()
    assert _impact(_pieces_toml(tmp_path / "ok", {"H": "harness"}), "H")[0] == 0


# ------------------------------------------------------------------ group 8: pieces.py --check

def _pieces_check(tmp_path: Path, rows: list):
    """rows: [(id, state, impact or None)]."""
    text = ""
    for pid, state, impact in rows:
        text += f'[[piece]]\nid = "{pid}"\nowns = ["x/{pid}.txt"]\nacceptance = []\ndepends_on = []\n'
        if impact is not None:
            text += f'impact = "{impact}"\n'
        text += f'status = {{ state = "{state}" }}\n\n'
    f = tmp_path / "pieces.toml"
    f.write_text(text)
    r = subprocess.run([PY, str(PIECES_PY), "--check", "--pieces", str(f), "--project", str(tmp_path)],
                       capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr


def test_g8_pieces_check_warns_on_a_queued_row_without_the_key(tmp_path):
    """Group (8): a queued row without `impact` WARNs `impact missing (treated as sim)`, exit 0."""
    rc, out = _pieces_check(tmp_path, [("Q1", "queued", None)])
    assert re.search(r"WARN Q1:? impact missing \(treated as sim\)", out), out
    assert rc == 0, out


def test_g8_pieces_check_fails_on_a_value_outside_the_four(tmp_path):
    """Group (8): `impact = "bogus"` FAILs, exit 1, naming the row."""
    rc, out = _pieces_check(tmp_path, [("Q1", "queued", "bogus")])
    assert rc == 1 and re.search(r"FAIL Q1", out), out


@pytest.mark.parametrize("impact", ["harness", "client", "sim", "contract"])
def test_g8_control_the_four_values_raise_neither_warn_nor_fail(tmp_path, impact):
    """Negative control for g8: each of the four values passes silently about `impact`."""
    rc, out = _pieces_check(tmp_path, [("Q1", "queued", impact)])
    assert rc == 0 and "impact" not in out, out


def test_g8_control_an_attached_row_without_the_key_is_not_warned(tmp_path):
    """Negative control for g8: the WARN is for queued or in-flight rows; an attached (done) row without the key is silent."""
    rc, out = _pieces_check(tmp_path, [("A1", "attached", None)])
    assert rc == 0 and "impact" not in out, out


# ------------------------------------------------------------------ the gate-repo fixture (groups 1 to 5, 9, 10)

def _gate(tmp_path: Path, libs, impact, candidate_files: dict, pre_args=(), stubs=None):
    """(rc, stdout lines, stdout+stderr) of merge_gate.sh on the test_gate_reorder.py gate-repo fixture, base Makefile
    copying libA, the piece's row carrying `impact` (None: no key). Merge root is tmp_path."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    # H-006 / DEC-ownership-by-conflict-2026-10-30: the flag comes from the story file's Machine lines block in the candidate.
    story = "# B1: fixture\n\n## Machine lines\n\n" + (f"Flag: {impact}\n" if impact else "") + "Tests: tests/csim/test_fixture.py\n"
    candidate_files = {**candidate_files, "docs/stories/B1.md": story}
    gate, cand = tgr._build(tmp_path, drift=False, gate_script=GATE, candidate_files=candidate_files,
                            base_files={"Makefile": _mk(libs["A"]), "tests/csim/test_fixture.py": "def test_fixture():\n    assert True\n"},
                            stubs=stubs)
    env = {"PATH": tgr.GATE_PATH, "HOME": str(Path.home()), "MERGE_GATE_RUNS_CSV": str(tmp_path / "runs.csv"),
           "MERGE_GATE_PLACEHOLDERS": str(tmp_path / "placeholders.txt")}
    r = subprocess.run(["bash", str(gate), *pre_args, str(cand), "origin/main", "B1"], capture_output=True, text=True,
                       env=env, timeout=GATE_TIMEOUT_S)
    return r.returncode, r.stdout.splitlines(), r.stdout + r.stderr


def _flag_line(lines):
    return next((ln for ln in lines if ln.startswith("GATE flag ")), "")


def _has(lines, stage):
    return any(ln.startswith(f"GATE {stage} ") for ln in lines)


# ------------------------------------------------------------------ group 9: the tier from the flag

ALL_SUITES = ["regression_csim", "regression_lab", "specfactory_regression", "transport", "playthrough", "lane_plays"]


def test_g9_harness_runs_specfactory_only(tmp_path, libs):
    """Group (9) + N15: under `harness` no GATE line for regression_csim, transport, playthrough, regression_lab, lane_plays
    or regression_qa_t1; `GATE specfactory_regression` prints."""
    rc, lines, out = _gate(tmp_path, libs, "harness", {"docs/x.md": "docs only\n"})
    assert _flag_line(lines).startswith("GATE flag OK"), out
    for stage in ["regression_csim", "regression_lab", "transport", "playthrough", "lane_plays", "regression_qa_t1"]:
        assert not _has(lines, stage), f"GATE {stage} printed under a harness flag:\n{out}"
    assert _has(lines, "specfactory_regression"), out


def test_g9_control_explicit_full_tier_prints_todays_list_under_a_harness_flag(tmp_path, libs):
    """Group (9) positive control: `--tier full` wins over the flag and prints today's list (the step-order test
    test_gate_a94_steps.py:304 stays green)."""
    rc, lines, out = _gate(tmp_path, libs, "harness", {"docs/x.md": "docs only\n"}, pre_args=("--tier", "full"))
    for stage in ALL_SUITES + ["regression_qa_t1"]:
        assert _has(lines, stage), f"GATE {stage} missing under --tier full:\n{out}"


def test_g9_client_skips_csim_lab_and_specfactory_and_runs_transport_only_when_touched(tmp_path, libs):
    """Group (9) + N14 + N15: under `client` regression_csim, regression_lab and specfactory_regression are skipped;
    regression_qa_t1 runs; a docs-only diff prints no `GATE transport`. (The paragraph's autoload/ trigger cannot be
    reached on a fixture: the playthrough stage it also triggers rejects a repo without the desktop suite; N14's
    tests/transport/ trigger is used in the next test.)"""
    rc, lines, out = _gate(tmp_path, libs, "client", {"docs/x.md": "docs only\n"})
    for stage in ["regression_csim", "regression_lab", "specfactory_regression", "transport"]:
        assert not _has(lines, stage), f"GATE {stage} printed under a client flag with a docs-only diff:\n{out}"
    assert _has(lines, "regression_qa_t1"), out


def test_g9_client_diff_under_tests_transport_runs_transport(tmp_path, libs):
    """Group (9) positive for the client transport trigger (N14: a diff touching tests/transport/): `GATE transport`
    prints, and csim, lab and specfactory stay skipped."""
    rc, lines, out = _gate(tmp_path, libs, "client", {"tests/transport/test_x.py": "def test_x():\n    assert True\n"})
    assert _has(lines, "transport"), out
    for stage in ["regression_csim", "regression_lab", "specfactory_regression"]:
        assert not _has(lines, stage), f"GATE {stage} printed under a client flag:\n{out}"


# ------------------------------------------------------------------ group 10 (F4): revert mode skips the stage

def test_g10_revert_mode_skips_the_flag_stage(tmp_path, libs):
    """Group (10) (F4): under --revert the stage prints `GATE flag SKIP revert mode` and never REJECTs, even for a diff the
    stage would reject; no trace cache is written."""
    rc, lines, out = _gate(tmp_path, libs, "harness", {"Makefile": _mk(libs["B"])}, pre_args=("--revert",))
    assert _flag_line(lines).startswith("GATE flag SKIP revert mode"), out
    assert not any(ln.startswith("GATE flag REJECT") for ln in lines), out
    assert _cache_files(tmp_path) == [], out


def test_g10_control_the_same_diff_without_revert_rejects(tmp_path, libs):
    """Positive control for g10: the identical fixture without --revert is `GATE flag REJECT`."""
    rc, lines, out = _gate(tmp_path, libs, "harness", {"Makefile": _mk(libs["B"])})
    assert _flag_line(lines).startswith("GATE flag REJECT"), out


# ------------------------------------------------------------------ group 11 (F6): a trace tool fails

@pytest.mark.parametrize("impact", ["harness", "sim"])
def test_g11_trace_tool_failure_rejects_with_tool_and_rc(tmp_path, libs, impact):
    """Group (11) (F6): a trace tool exiting non-zero is REJECT `trace failed <tool> rc <n>`, under any flag. libE makes the
    strategic tool (60 regions) assert on a NULL world."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"docs/readme.md": "edited\n"})
    rc, line, out = _verdict(repo, base, impact, libs["E"], tmp_path / "mr")
    assert rc == 1 and _rejects(line), out
    assert re.search(r"trace failed checksum_trace(\.py)? rc [1-9]", line), out


def test_g11_control_a_working_library_raises_no_trace_failure(tmp_path, libs):
    """Negative control for g11: libA on the same diff does not say `trace failed`."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"docs/readme.md": "edited\n"})
    rc, line, out = _verdict(repo, base, "harness", libs["A"], tmp_path / "mr")
    assert rc == 0 and "trace failed" not in out, out


# ------------------------------------------------------------------ group 12 (F6): the base does not build

@pytest.mark.parametrize("impact", ["harness", "sim"])
def test_g12_base_make_failure_rejects_naming_the_base_sha(tmp_path, libs, impact):
    """Group (12) (F6): a base worktree whose `make` fails is REJECT `base unbuildable <sha>` (main must build)."""
    repo, base = _repo(tmp_path, libs["A"], base_makefile="libouroboros.so:\n\tfalse\n")
    _commit(repo, {"Makefile": _mk(libs["A"])})
    rc, line, out = _verdict(repo, base, impact, libs["A"], tmp_path / "mr")
    assert rc == 1 and _rejects(line), out
    m = re.search(r"base unbuildable ([0-9a-f]{7,40})", line)
    assert m and base.startswith(m.group(1)), out


def test_g12_control_a_building_base_is_not_called_unbuildable(tmp_path, libs):
    """Negative control for g12: the same shape with a base that builds gives no `base unbuildable`."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"Makefile": _mk(libs["A"], "# edit\n")})
    rc, line, out = _verdict(repo, base, "harness", libs["A"], tmp_path / "mr")
    assert rc == 0 and "unbuildable" not in out, out


# ------------------------------------------------------------------ group 13 (F6): om_world_checksum_full missing

CANNOT_VERIFY = "cannot verify flag: checksum entry point missing"


@pytest.mark.parametrize("impact", ["harness", "client"])
def test_g13_missing_checksum_entry_point_rejects_harness_and_client(tmp_path, libs, impact):
    """Group (13) (F6): a library without om_world_checksum_full cannot verify a harness or client flag: REJECT."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"docs/readme.md": "edited\n"})
    rc, line, out = _verdict(repo, base, impact, libs["C"], tmp_path / "mr")
    assert rc == 1 and _rejects(line) and CANNOT_VERIFY in line, out


def test_g13_missing_checksum_entry_point_warns_and_runs_as_differ_for_sim(tmp_path, libs):
    """Group (13) (F6): under `sim` the same library WARNs and the stage runs as if the traces differ: exit 0."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"docs/readme.md": "edited\n"})
    rc, line, out = _verdict(repo, base, "sim", libs["C"], tmp_path / "mr")
    assert rc == 0 and not _rejects(line), out
    assert "WARN" in line and "traces differ" in line, out


def test_g13_missing_checksum_entry_point_warns_for_contract_with_a_pin_file(tmp_path, libs):
    """Group (13) (F6): under `contract` (pin file in the diff) the missing entry point is a WARN, exit 0."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"csrc/ouroboros_sim.h": "/* header v2 */\n"})
    rc, line, out = _verdict(repo, base, "contract", libs["C"], tmp_path / "mr")
    assert rc == 0 and not _rejects(line) and "WARN" in line, out


def test_g13_control_a_library_with_the_entry_point_is_not_flagged(tmp_path, libs):
    """Negative control for g13: libA under harness gives no `cannot verify` and no WARN."""
    repo, base = _repo(tmp_path, libs["A"])
    _commit(repo, {"docs/readme.md": "edited\n"})
    rc, line, out = _verdict(repo, base, "harness", libs["A"], tmp_path / "mr")
    assert rc == 0 and "cannot verify" not in out and "WARN" not in line, out
