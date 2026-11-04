# spec: docs/stories/H-067.md (part 1, scripts/setup_editor.sh)
"""H-067 part 1: `scripts/setup_editor.sh` sets a tree up for the Godot editor.

Story H-067, Tests line proved here: "`tests/method/test_setup_editor.py` (new): `--check` lists the steps and changes nothing; a stubbed build route
produces `EDITOR READY`; a failing build produces `EDITOR SETUP FAILED pipe`; a stale pipe (older than `csrc/`) is rebuilt and a fresh one is not; a
missing cache falls back to the fetch script (stubbed); a positive control for each."
Story Change part 1: "It builds the pipe with `scripts/build_pipe_linux.sh` and copies `dist/linux/ouroboros_pipe` to `pipe/ouroboros_pipe` (atomic ...)
when `csrc/` is newer than the copy or the copy is missing; fills `addons/godotsteam/` from `$HOME/Projects/om-push/cache/godotsteam/` with `cp -a`,
falling back to `scripts/fetch_godotsteam.sh`; runs `godot.real --headless --import --path .` once; prints `EDITOR READY <tree>` or `EDITOR SETUP
FAILED <step>` (steps `pipe`, `steam`, `import`). `--check` prints the steps and changes nothing."

Nothing here runs Godot, builds C or touches the real HOME, `~/Projects/om-push` or this checkout: each case builds a SCRATCH TREE
(`<tmp>/tree/{scripts,csrc}`), copies the real `scripts/setup_editor.sh` into it, and stubs the three things it calls: `scripts/build_pipe_linux.sh`
and `scripts/fetch_godotsteam.sh` (sibling scripts in the scratch tree, which the real ones are: they `cd "$(dirname "$0")/.."`) and `godot.real` (first
on PATH). HOME is `<tmp>/home`. Each stub appends its name to `<tmp>/calls.log`.

Premises the tests rely on (read from the repo, not guessed): scripts/build_pipe_linux.sh does `cd "$(dirname "$0")/.."` and writes
`dist/linux/ouroboros_pipe`; scripts/fetch_godotsteam.sh unpacks into `<tree>/addons/godotsteam`; the cache dir is `$HOME/Projects/om-push/cache/godotsteam/`
(story Change part 1; the same path scripts/beta_refresh.sh uses). Premises the story does not state and these tests therefore do NOT pin: the exit
code of a failed setup, the format of the `--check` listing beyond naming the three steps, whether the cache is copied as contents or as the directory
(the test needs the cached file at `addons/godotsteam/<name>`), and the order of the steps. Red today for the missing-feature reason:
`scripts/setup_editor.sh` does not exist.
"""
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "setup_editor.sh"
STEPS = ("pipe", "steam", "import")
BUILT = "BUILT-BY-STUB\n"
OLD = "OLD-PIPE\n"
LONG_AGO = 1_000_000_000  # an mtime well before any file written now


def tmp(prefix="h067-setup-"):
    return Path(tempfile.mkdtemp(prefix=prefix))


def write_exec(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class Rig:
    """A scratch tree with the real setup_editor.sh (when it exists) and stubbed collaborators."""

    def __init__(self, build_ok=True, import_ok=True, cache=False, pipe=None, csrc_newer=True):
        self.base = tmp().resolve()
        self.tree = self.base / "tree"
        self.home = self.base / "home"
        self.bin = self.base / "bin"
        self.log = self.base / "calls.log"
        self.log.write_text("")
        self.home.mkdir()
        for d in ("scripts", "csrc", "addons/godotsteam"):
            (self.tree / d).mkdir(parents=True)
        if SCRIPT.is_file():
            shutil.copy2(SCRIPT, self.tree / "scripts" / "setup_editor.sh")
        write_exec(self.tree / "scripts" / "build_pipe_linux.sh",
                   f'echo build >> {self.log}\n{"" if build_ok else "exit 1"}\n'
                   f'cd "$(dirname "$0")/.."; mkdir -p dist/linux; echo {BUILT.strip()} > dist/linux/ouroboros_pipe\n'
                   'echo dist/linux/ouroboros_pipe\n')
        write_exec(self.tree / "scripts" / "fetch_godotsteam.sh",
                   f'echo fetch >> {self.log}\ncd "$(dirname "$0")/.."; mkdir -p addons/godotsteam; echo fetched > addons/godotsteam/fetched.so\n')
        write_exec(self.bin / "godot.real", f'echo "godot.real $*" >> {self.log}\n{"" if import_ok else "exit 1"}\n')
        (self.tree / "csrc" / "sim.c").write_text("int x;\n")
        pipe_file = self.tree / "pipe" / "ouroboros_pipe"
        if pipe is not None:
            pipe_file.parent.mkdir()
            pipe_file.write_text(OLD)
            old, new = (LONG_AGO, LONG_AGO + 1000)
            # pipe == "stale": the csrc file is newer than the copy; pipe == "fresh": the copy is newer than every csrc file
            src_time, pipe_time = (new, old) if pipe == "stale" else (old, new)
            os.utime(self.tree / "csrc" / "sim.c", (src_time, src_time))
            os.utime(pipe_file, (pipe_time, pipe_time))
        if cache:
            c = self.home / "Projects" / "om-push" / "cache" / "godotsteam"
            c.mkdir(parents=True)
            (c / "libgodotsteam.so").write_text("CACHED\n")

    def run(self, *args):
        env = dict(os.environ, HOME=str(self.home), PATH=f"{self.bin}:{os.environ['PATH']}")
        assert SCRIPT.is_file(), f"{SCRIPT} does not exist"
        r = subprocess.run(["bash", str(self.tree / "scripts" / "setup_editor.sh"), *args], cwd=str(self.tree), env=env,
                           capture_output=True, text=True, timeout=60)
        r.lines = (r.stdout + r.stderr).splitlines()
        return r

    def calls(self):
        return self.log.read_text().splitlines()

    def snapshot(self):
        """Every path under the scratch base, files with size and mtime: any create, delete or write changes it."""
        out = {}
        for p in sorted(self.base.rglob("*")):
            if p == self.log:
                continue
            s = p.lstat()
            out[str(p.relative_to(self.base))] = None if p.is_dir() else (s.st_size, s.st_mtime_ns)  # a directory's own mtime is not content
        return out

    def pipe(self):
        p = self.tree / "pipe" / "ouroboros_pipe"
        return p.read_text() if p.is_file() else None

    def close(self):
        shutil.rmtree(self.base, ignore_errors=True)


# ---------------------------------------------------------------- positive controls (green today)

def test_control_rig_stubs_work():
    """Positive control for every case below (H-067 Tests: "a positive control for each"): without the script, the scratch tree's stubs behave as
    the cases assume. The build stub writes dist/linux/ouroboros_pipe and logs once; a failing build stub exits 1 and writes nothing; the fetch stub
    fills addons/godotsteam and logs; the godot.real stub on PATH logs its arguments; a cache plants its file under HOME. A red case below is the
    missing script, not a broken rig."""
    r = Rig()
    try:
        assert subprocess.run([str(r.tree / "scripts" / "build_pipe_linux.sh")], capture_output=True).returncode == 0
        assert (r.tree / "dist" / "linux" / "ouroboros_pipe").read_text() == BUILT
        assert subprocess.run([str(r.tree / "scripts" / "fetch_godotsteam.sh")], capture_output=True).returncode == 0
        assert (r.tree / "addons" / "godotsteam" / "fetched.so").is_file()
        env = dict(os.environ, PATH=f"{r.bin}:{os.environ['PATH']}")
        assert subprocess.run(["godot.real", "--headless", "--import", "--path", "."], env=env, capture_output=True).returncode == 0
        assert r.calls() == ["build", "fetch", "godot.real --headless --import --path ."], r.calls()
    finally:
        r.close()
    bad = Rig(build_ok=False, import_ok=False, cache=True)
    try:
        assert subprocess.run([str(bad.tree / "scripts" / "build_pipe_linux.sh")], capture_output=True).returncode == 1
        assert not (bad.tree / "dist").exists()
        env = dict(os.environ, PATH=f"{bad.bin}:{os.environ['PATH']}")
        assert subprocess.run(["godot.real"], env=env, capture_output=True).returncode == 1
        assert (bad.home / "Projects/om-push/cache/godotsteam/libgodotsteam.so").read_text() == "CACHED\n"
    finally:
        bad.close()


def test_control_snapshot_sees_a_change_and_stale_fixture_is_ordered():
    """Positive control for the `--check` case (H-067 Tests: "`--check` lists the steps and changes nothing"): the snapshot differs after a planted
    file, a rewrite and a delete, so an equal snapshot means nothing changed. And the stale/fresh fixtures order the mtimes the way the stale-pipe
    cases need (stale: csrc newer than the pipe copy; fresh: the reverse)."""
    r = Rig(pipe="stale")
    try:
        before = r.snapshot()
        (r.tree / "planted").write_text("x")
        assert r.snapshot() != before
        (r.tree / "planted").unlink()
        assert r.snapshot() == before
        (r.tree / "csrc" / "sim.c").write_text("int y;\n")
        assert r.snapshot() != before
        assert (r.tree / "csrc" / "sim.c").stat().st_mtime > (r.tree / "pipe" / "ouroboros_pipe").stat().st_mtime
    finally:
        r.close()
    f = Rig(pipe="fresh")
    try:
        assert (f.tree / "csrc" / "sim.c").stat().st_mtime < (f.tree / "pipe" / "ouroboros_pipe").stat().st_mtime
    finally:
        f.close()


# ---------------------------------------------------------------- the script (red today: it does not exist)

def test_setup_script_exists_and_is_executable():
    """H-067 Tests / Files: `scripts/setup_editor.sh` is new (part 1) and is run directly by the player ("runs `scripts/setup_editor.sh`")."""
    assert SCRIPT.is_file(), f"{SCRIPT} does not exist"
    assert os.access(SCRIPT, os.X_OK), f"{SCRIPT} is not executable"


def test_check_lists_the_steps_and_changes_nothing():
    """H-067 Tests: "`--check` lists the steps and changes nothing". Change part 1: "`--check` prints the steps and changes nothing" (steps `pipe`,
    `steam`, `import`). The run exits 0, names each of the three steps in its output, runs no stub (no build, fetch or godot.real call) and leaves
    the scratch tree and HOME exactly as they were (a stale pipe, no cache, so a real run would have changed all three)."""
    r = Rig(pipe="stale")
    try:
        before = r.snapshot()
        p = r.run("--check")
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        for step in STEPS:
            assert any(re.search(rf"\b{step}\b", l) for l in p.lines), f"--check does not list the step {step!r}: {p.lines}"
        assert r.calls() == [], r.calls()
        assert r.snapshot() == before, "--check changed the scratch tree or HOME"
        assert r.pipe() == OLD
    finally:
        r.close()


def test_stubbed_build_route_prints_editor_ready():
    """H-067 Tests: "a stubbed build route produces `EDITOR READY`". Change part 1: "prints `EDITOR READY <tree>`". With a working build, a cache and a
    working godot.real on a tree with no pipe copy, the run exits 0, prints the line `EDITOR READY <tree>` (tree = the scratch tree), copies the built
    pipe to pipe/ouroboros_pipe ("or the copy is missing"), fills addons/godotsteam from the cache, runs `godot.real --headless --import --path .`
    once, and does not print EDITOR SETUP FAILED."""
    r = Rig(cache=True)
    try:
        p = r.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert f"EDITOR READY {r.tree}" in p.lines, p.lines
        assert not any("EDITOR SETUP FAILED" in l for l in p.lines), p.lines
        assert r.pipe() == BUILT
        assert (r.tree / "addons" / "godotsteam" / "libgodotsteam.so").read_text() == "CACHED\n"
        assert r.calls().count("godot.real --headless --import --path .") == 1, r.calls()
    finally:
        r.close()


def test_failing_build_prints_editor_setup_failed_pipe():
    """H-067 Tests: "a failing build produces `EDITOR SETUP FAILED pipe`". Change part 1: "prints ... `EDITOR SETUP FAILED <step>` (steps `pipe`,
    `steam`, `import`)". With build_pipe_linux.sh exiting 1 the output has the line `EDITOR SETUP FAILED pipe` and no `EDITOR READY`, and no pipe copy
    appears. (The exit code is not pinned: the story does not give one.)"""
    r = Rig(build_ok=False, cache=True)
    try:
        p = r.run()
        assert "EDITOR SETUP FAILED pipe" in p.lines, p.lines
        assert not any(l.startswith("EDITOR READY") for l in p.lines), p.lines
        assert r.pipe() is None
    finally:
        r.close()


def test_stale_pipe_is_rebuilt():
    """H-067 Tests: "a stale pipe (older than `csrc/`) is rebuilt". Change part 1: build and copy "when `csrc/` is newer than the copy". The copy is
    older than csrc/sim.c: the build stub runs and pipe/ouroboros_pipe now holds its output."""
    r = Rig(pipe="stale", cache=True)
    try:
        p = r.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert r.calls().count("build") == 1, r.calls()
        assert r.pipe() == BUILT, r.pipe()
    finally:
        r.close()


def test_fresh_pipe_is_not_rebuilt():
    """H-067 Tests: "... and a fresh one is not". The copy is newer than every file in csrc/: the build stub does not run, the pipe copy keeps its
    content and its mtime, and the run still ends `EDITOR READY <tree>` (a fresh pipe is not a failure)."""
    r = Rig(pipe="fresh", cache=True)
    try:
        pipe_file = r.tree / "pipe" / "ouroboros_pipe"
        mtime = pipe_file.stat().st_mtime_ns
        p = r.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert "build" not in r.calls(), r.calls()
        assert r.pipe() == OLD
        assert pipe_file.stat().st_mtime_ns == mtime
        assert f"EDITOR READY {r.tree}" in p.lines, p.lines
    finally:
        r.close()


def test_present_cache_is_copied_and_the_fetch_script_is_not_run():
    """H-067 Tests (control for the fallback): with `$HOME/Projects/om-push/cache/godotsteam/` present, `addons/godotsteam/` is filled from it
    ("`cp -a`") and the fetch script is NOT run."""
    r = Rig(cache=True)
    try:
        p = r.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert (r.tree / "addons" / "godotsteam" / "libgodotsteam.so").read_text() == "CACHED\n"
        assert "fetch" not in r.calls(), r.calls()
    finally:
        r.close()


def test_missing_cache_falls_back_to_the_fetch_script():
    """H-067 Tests: "a missing cache falls back to the fetch script (stubbed)". Change part 1: "fills `addons/godotsteam/` from
    `$HOME/Projects/om-push/cache/godotsteam/` with `cp -a`, falling back to `scripts/fetch_godotsteam.sh`". HOME has no cache: the fetch stub runs
    once, fills addons/godotsteam, and the run ends `EDITOR READY <tree>`."""
    r = Rig(cache=False)
    try:
        p = r.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert r.calls().count("fetch") == 1, r.calls()
        assert (r.tree / "addons" / "godotsteam" / "fetched.so").is_file()
        assert f"EDITOR READY {r.tree}" in p.lines, p.lines
    finally:
        r.close()
