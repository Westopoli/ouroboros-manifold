# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md G1 (rev 4) and
# docs/northstar/plans/preflight_2026-10-07/9-harness.md "Recommended numbers".
"""Proves what guard piece G1 builds in merge_gate.sh / merge_gate_support.py:

  * per-stage times: every `GATE <name> <STATUS> <detail>` line ends with
    ` [<N>s]` (elapsed seconds of that stage). The existing prefix
    `GATE <name> <STATUS>` is unchanged, so older checks keep matching.
  * `look` stage, warn-only until Westley's threshold lands: a new
    subcommand `merge_gate_support.py look <candidate_frames_dir>
    <base_frames_dir>` compares same-named PNG frames (same name = same play
    moment); a candidate frame blanker than main's is flagged. While
    warn-only it prints `WARN ...` (metric per frame, candidate frame paths
    attached) and exits 0; it never prints REJECT. merge_gate.sh prints a
    `GATE look` line that is never REJECT.
  * baseline cache keyed on the main sha, shared across merge roots: with
    env MERGE_GATE_BASELINE_CACHE=<dir> the cache lives there instead of
    under the candidate's own parent dir.
  * flake re-run: `merge_gate_support.py flake-rerun <candidate_dir>
    <test_id> [--python P]` re-runs ONLY that id, at most twice, stopping at
    the first pass. Passes on a re-run -> `WARN flake ...`, exit 0; red on
    both -> `REJECT ...`, exit 1.

Names of the new subcommands, the env var and the time suffix are this
file's reading of the G1 spec; the spec fixes the behaviour, not the spelling.
"""
import os
import re
import struct
import subprocess
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
GATE = REPO / "scripts" / "specfactory" / "merge_gate.sh"
SUPPORT = REPO / "scripts" / "specfactory" / "merge_gate_support.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_toy_root import fake_gate_root, gate_env  # noqa: E402

PY = sys.executable
TIME_SUFFIX = re.compile(r"\[(\d+(?:\.\d+)?)s\]\s*$")


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _support(*args, env=None, timeout=300):
    e = {**os.environ, **(env or {})}
    return subprocess.run([PY, str(SUPPORT), *map(str, args)], capture_output=True, text=True, env=e, timeout=timeout)


def _png(path: Path, pixels: list[tuple[int, int, int]], w: int, h: int) -> None:
    raw = b"".join(b"\x00" + b"".join(bytes(pixels[y * w + x]) for x in range(w)) for y in range(h))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _blank(path):
    _png(path, [(20, 20, 20)] * 256, 16, 16)


def _busy(path):
    _png(path, [((i * 7) % 256, (i * 13) % 256, (i * 29) % 256) for i in range(256)], 16, 16)


# ---------------------------------------------------------------- per-stage times

FAST_MAKEFILE = "libouroboros.so:\n\ttouch $@\nlibouroboros_dbg.so:\n\ttouch $@\n"
SLOW_MAKEFILE = "libouroboros.so:\n\tsleep 2 && touch $@\nlibouroboros_dbg.so:\n\ttouch $@\n"


def _fixture(base: Path, makefile: str) -> tuple[Path, Path]:
    repo = base / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "g@t")
    _git(repo, "config", "user.name", "g")
    (repo / "csrc").mkdir()
    (repo / "csrc" / "stub.c").write_text("int om_stub(void) { return 0; }\n")
    (repo / "Makefile").write_text(makefile)
    for d in ("tests/csim", "tests/qa/t1"):
        (repo / d).mkdir(parents=True)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "remote", "add", "origin", str(repo))
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    pieces = base / "pieces.toml"
    pieces.write_text('[[piece]]\nid = "B1"\nowns = ["csrc/stub.c"]\nacceptance = []\ndepends_on = []\n')
    return repo, pieces


def _run_gate(repo, pieces, **extra):
    env = {"MERGE_GATE_PIECES": str(pieces), "PATH": "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin", **extra}
    return subprocess.run(["bash", str(GATE), str(repo), "HEAD", "B1"], capture_output=True, text=True, env=env, timeout=120)


def _run_gate_through(tmp_path, repo, pieces):
    """Test-defect TD-HARNESS-gate-reorder-6 (ruler Architect 2026-10-29): `GATE look` prints after the early block, which
    ends the run on the toy repo (decisive line: `GATE early_exit REJECT allowlist_strict;sig_check;reach_lint;status;
    placeholder_controls`, then `merge_gate.sh: line 91: HOME: unbound variable`). Same fix as gate_toy_root.py."""
    gate = fake_gate_root(tmp_path)
    return subprocess.run(["bash", str(gate), str(repo), "HEAD", "B1"], capture_output=True, text=True,
                          env=gate_env(tmp_path, pieces), timeout=240)


def _line(out, step):
    return next((l for l in out.splitlines() if l.startswith(f"GATE {step} ")), "")


def test_gate_lines_end_with_elapsed_seconds(tmp_path):
    repo, pieces = _fixture(tmp_path, FAST_MAKEFILE)
    proc = _run_gate(repo, pieces)
    for step in ("make", "libm_lint", "alg_constants", "footprint", "symbol_ownership"):
        line = _line(proc.stdout, step)
        assert line, proc.stdout + proc.stderr
        assert TIME_SUFFIX.search(line), f"no [Ns] suffix: {line!r}"


def test_harness_line_also_carries_time(tmp_path):
    repo, pieces = _fixture(tmp_path, SLOW_MAKEFILE)
    proc = _run_gate(repo, pieces, MERGE_GATE_MAKE_TIMEOUT="1")
    line = _line(proc.stdout, "make")
    assert line.startswith("GATE make HARNESS") and TIME_SUFFIX.search(line), proc.stdout


def test_positive_control_reported_time_tracks_real_duration(tmp_path):
    """A 2 s make must show >= 2 in its own suffix, a no-op make must show less."""
    slow_repo, slow_p = _fixture(tmp_path / "slow", SLOW_MAKEFILE)
    fast_repo, fast_p = _fixture(tmp_path / "fast", FAST_MAKEFILE)
    slow = TIME_SUFFIX.search(_line(_run_gate(slow_repo, slow_p).stdout, "make"))
    fast = TIME_SUFFIX.search(_line(_run_gate(fast_repo, fast_p).stdout, "make"))
    assert slow and fast
    assert float(slow.group(1)) >= 2 and float(fast.group(1)) < 2


# ---------------------------------------------------------------- look stage (warn-only)

def test_look_flags_planted_blank_candidate_but_warns_only(tmp_path):
    cand, base = tmp_path / "cand", tmp_path / "base"
    _blank(cand / "moment_1.png")
    _busy(base / "moment_1.png")
    r = _support("look", cand, base)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("WARN") and "REJECT" not in r.stdout, r.stdout
    assert "moment_1.png" in r.stdout
    assert re.search(r"\d", r.stdout.split("moment_1.png", 1)[1]), "metric not reported"
    assert str(cand / "moment_1.png") in r.stdout, "candidate frame not attached by path"


def test_look_ok_when_candidate_matches_main(tmp_path):
    cand, base = tmp_path / "cand", tmp_path / "base"
    for d in (cand, base):
        _busy(d / "moment_1.png")
    r = _support("look", cand, base)
    assert r.returncode == 0 and r.stdout.startswith("OK"), r.stdout + r.stderr


def test_look_not_flagged_when_main_is_equally_blank(tmp_path):
    cand, base = tmp_path / "cand", tmp_path / "base"
    for d in (cand, base):
        _blank(d / "moment_1.png")
    r = _support("look", cand, base)
    assert r.returncode == 0 and r.stdout.startswith("OK"), "a candidate is only flagged when blanker than main"


def test_look_compares_same_named_frames_only(tmp_path):
    cand, base = tmp_path / "cand", tmp_path / "base"
    _busy(cand / "moment_1.png")
    _busy(base / "moment_1.png")
    _blank(cand / "moment_2.png")  # blank candidate frame, but main has busy moment_2
    _busy(base / "moment_2.png")
    r = _support("look", cand, base)
    first = r.stdout.splitlines()[0]
    assert first.startswith("WARN") and "moment_2.png" in first and "moment_1.png" not in first, r.stdout


def test_gate_prints_look_line_never_reject(tmp_path):
    repo, pieces = _fixture(tmp_path, FAST_MAKEFILE)
    line = _line(_run_gate_through(tmp_path, repo, pieces).stdout, "look")
    assert line, "merge_gate.sh prints no `GATE look` line"
    assert not line.startswith("GATE look REJECT") and not line.startswith("GATE look HARNESS"), line


# ---------------------------------------------------------------- baseline cache keyed on main sha

def _cache_repo(base: Path) -> Path:
    repo = base / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "g@t")
    _git(repo, "config", "user.name", "g")
    (repo / "tests" / "t").mkdir(parents=True)
    (repo / "tests" / "t" / "test_a.py").write_text("def test_a():\n    assert True\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "main")
    return repo


def _regress(repo, merge_root, env=None):
    return _support("regression", repo, "HEAD", "tests/t", "--python", PY, "--no-junit",
                    "--merge-root", merge_root, env=env)


def test_cache_shared_across_merge_roots_via_env(tmp_path):
    """Today the cache sits under the candidate's own parent dir, so two clerks
    on the same main sha never share it. With MERGE_GATE_BASELINE_CACHE both do."""
    repo = _cache_repo(tmp_path)
    shared = tmp_path / "shared_cache"
    env = {"MERGE_GATE_BASELINE_CACHE": str(shared)}
    sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    first = _regress(repo, tmp_path / "root_a", env)
    assert f"baseline: computed {sha}" in first.stdout, first.stdout + first.stderr
    assert (shared / f"{sha}.json").exists() or any(shared.rglob(f"{sha}.json")), "cache not written to the shared dir"
    second = _regress(repo, tmp_path / "root_b", env)
    assert f"baseline: cached {sha}" in second.stdout, second.stdout + second.stderr


def test_cache_key_follows_sha_not_ref_name(tmp_path):
    """Guard: same ref name, new main sha -> recomputed, then cached again."""
    repo = _cache_repo(tmp_path)
    shared = tmp_path / "shared_cache"
    env = {"MERGE_GATE_BASELINE_CACHE": str(shared)}
    old = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _regress(repo, tmp_path / "root", env)
    (repo / "tests" / "t" / "test_b.py").write_text("def test_b():\n    assert True\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "main moves")
    new = _git(repo, "rev-parse", "HEAD").stdout.strip()
    moved = _regress(repo, tmp_path / "root", env)
    assert f"baseline: computed {new}" in moved.stdout and new != old, moved.stdout + moved.stderr
    again = _regress(repo, tmp_path / "root", env)
    assert f"baseline: cached {new}" in again.stdout, again.stdout + again.stderr


# ---------------------------------------------------------------- flake re-run of one test id

def _flaky_repo(tmp_path: Path, fail_first: int) -> tuple[Path, Path, Path]:
    repo = tmp_path / "flaky"
    (repo / "tests").mkdir(parents=True)
    counter, sibling = tmp_path / "count.txt", tmp_path / "sibling_ran.txt"
    (repo / "tests" / "test_f.py").write_text(
        "from pathlib import Path\n"
        f"C = Path({str(counter)!r})\n"
        "def test_flaky():\n"
        "    n = int(C.read_text()) if C.exists() else 0\n"
        "    C.write_text(str(n + 1))\n"
        f"    assert n >= {fail_first}\n"
        "def test_sibling():\n"
        f"    Path({str(sibling)!r}).write_text('ran')\n"
    )
    return repo, counter, sibling


def _rerun(repo):
    return _support("flake-rerun", repo, "tests/test_f.py::test_flaky", "--python", PY)


def test_flake_passing_on_first_rerun_runs_once_and_warns(tmp_path):
    repo, counter, sibling = _flaky_repo(tmp_path, fail_first=0)
    r = _rerun(repo)
    assert r.returncode == 0 and r.stdout.startswith("WARN") and "flake" in r.stdout, r.stdout + r.stderr
    assert counter.read_text() == "1", "must stop at the first pass"
    assert not sibling.exists(), "only the named id may be re-run, never the stage"


def test_flake_passing_on_second_rerun_is_still_a_flake(tmp_path):
    repo, counter, _ = _flaky_repo(tmp_path, fail_first=1)
    r = _rerun(repo)
    assert r.returncode == 0 and r.stdout.startswith("WARN"), r.stdout + r.stderr
    assert counter.read_text() == "2"


def test_positive_control_real_red_rejects_after_exactly_two_reruns(tmp_path):
    repo, counter, sibling = _flaky_repo(tmp_path, fail_first=99)
    r = _rerun(repo)
    assert r.returncode == 1 and r.stdout.startswith("REJECT"), r.stdout + r.stderr
    assert counter.read_text() == "2", "up to twice, no more"
    assert not sibling.exists()
