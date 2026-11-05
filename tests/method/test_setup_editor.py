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
import pytest
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


# ================================================================ H-087: the beta runs on the Mac (red today)
# spec: docs/stories/H-087.md (R-087-01 to R-087-04), contract: docs/northstar/plans/cascades/b1-approved-screens/contract.md
# Nothing runs on a Mac: `uname` is a stub on PATH that answers Darwin and the architecture the case names, `clang` and `shasum` are stubs, and
# the macOS Godot is a stub file reached through OM_GODOT_APP (a test seam only, default /Applications/Godot.app/Contents/MacOS/Godot; the real
# path cannot be planted on this box). PATH is the stub bin plus a directory of symlinks to the ordinary tools the scripts use, so a case can
# leave `godot.real`, `clang` or `sha256sum` out. The rig and the Linux cases above are untouched; test names carry `darwin` for the umbrella (-k darwin).
APP_STUB_NAME = "app-godot"
BUILT_MAC = "BUILT-BY-MACOS-STUB\n"
TOOLS = ("bash", "env", "dirname", "find", "cp", "mv", "mkdir", "rm", "ls", "head", "cat", "cut", "tr", "sed", "grep", "awk", "mktemp",
         "unzip", "chmod", "touch", "sort", "wc", "basename", "readlink", "pwd", "sleep")
MAC_CHECK_PIPE = "step pipe: scripts/build_pipe_macos.sh (ARCH={arch}), then copy dist/macos/ouroboros_pipe to pipe/ouroboros_pipe"


def tools_dir(base, extra=()):
    d = base / "tools"
    d.mkdir(exist_ok=True)
    for name in (*TOOLS, *extra):
        src = shutil.which(name)
        if src and not (d / name).exists():
            (d / name).symlink_to(src)
    return d


class DarwinRig(Rig):
    """A Rig answering Darwin. godot: 'path' (godot.real on PATH), 'app' (only the OM_GODOT_APP stub exists), 'both', 'none'."""

    def __init__(self, arch="arm64", godot="path", clang=True, **kw):
        super().__init__(cache=kw.pop("cache", True), **kw)
        self.arch = arch
        self.app = self.base / "apps" / "Godot.app" / "Contents" / "MacOS" / "Godot"
        write_exec(self.bin / "uname", f'case "$1" in -m) echo {arch};; *) echo Darwin;; esac\n')
        write_exec(self.tree / "scripts" / "build_pipe_macos.sh",
                   f'echo "build-macos ARCH=$ARCH" >> {self.log}\ncd "$(dirname "$0")/.."; mkdir -p dist/macos; '
                   f'echo {BUILT_MAC.strip()} > dist/macos/ouroboros_pipe\necho dist/macos/ouroboros_pipe\n')
        if clang:
            write_exec(self.bin / "clang", "exit 0\n")
        if godot in ("app", "both"):
            write_exec(self.app, f'echo "{APP_STUB_NAME} $*" >> {self.log}\n')
        if godot in ("app", "none"):
            (self.bin / "godot.real").unlink()
        self.tools = tools_dir(self.base)
        # BSD find (macOS) has no `-quit`: a `find` that rejects it stands in for the symlinked GNU one (contract: staleness test runs under BSD find)
        (self.tools / "find").unlink()
        write_exec(self.bin / "find", f'for a; do [ "$a" = -quit ] && {{ echo "find: unknown primary or operator: -quit" >&2; exit 1; }}; done\n'
                   f'exec {shutil.which("find")} "$@"\n')

    def run(self, *args):
        env = {"HOME": str(self.home), "PATH": f"{self.bin}:{self.tools}", "OM_GODOT_APP": str(self.app)}
        assert SCRIPT.is_file(), f"{SCRIPT} does not exist"
        r = subprocess.run(["bash", str(self.tree / "scripts" / "setup_editor.sh"), *args], cwd=str(self.tree), env=env,
                           capture_output=True, text=True, timeout=60)
        r.lines = (r.stdout + r.stderr).splitlines()
        return r


def test_control_darwin_rig_answers_darwin_and_hides_what_it_leaves_out():
    """Positive control for every darwin case: the stubs answer as the cases assume. `uname -s` prints Darwin and `uname -m` the architecture; the
    macOS build stub logs the ARCH it was given and writes dist/macos/ouroboros_pipe; 'app' leaves no godot.real on the case PATH and plants the
    app stub; a rig without clang has no clang on PATH. A red darwin case below is the missing feature, not a broken rig."""
    r = DarwinRig(arch="x86_64", godot="app", clang=False)
    try:
        env = {"PATH": f"{r.bin}:{r.tools}", "ARCH": "x86_64"}
        out = lambda *a: subprocess.run(list(a), env=env, capture_output=True, text=True)
        assert out("uname", "-s").stdout.strip() == "Darwin" and out("uname", "-m").stdout.strip() == "x86_64"
        assert out("bash", "-c", "command -v clang").returncode != 0
        assert out("bash", "-c", "command -v godot.real").returncode != 0
        assert subprocess.run([str(r.tree / "scripts" / "build_pipe_macos.sh")], env=env, capture_output=True).returncode == 0
        assert (r.tree / "dist" / "macos" / "ouroboros_pipe").read_text() == BUILT_MAC
        assert subprocess.run([str(r.app), "--x"], capture_output=True).returncode == 0
        assert r.calls() == ["build-macos ARCH=x86_64", f"{APP_STUB_NAME} --x"], r.calls()
    finally:
        r.close()
    c = DarwinRig(godot="path", clang=True)
    try:
        env = {"PATH": f"{c.bin}:{c.tools}"}
        assert subprocess.run(["bash", "-c", "command -v clang && command -v godot.real"], env=env, capture_output=True).returncode == 0
    finally:
        c.close()


def test_darwin_check_prints_the_mac_build_line_the_godot_and_clang_and_changes_nothing():
    """H-087 R-087-04: `--check` on Darwin prints the Darwin build line, the Godot it would use, and clang present or missing; it changes nothing.
    The three lines are the contract's: the pipe step names scripts/build_pipe_macos.sh and the ARCH from `uname -m`; the import step names the
    Godot found on PATH; `clang: present`. Exit 0, no stub run, the scratch tree and HOME exactly as they were; the step names of H-067 remain."""
    r = DarwinRig(arch="arm64", pipe="stale")
    try:
        before = r.snapshot()
        p = r.run("--check")
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert any(l.startswith(MAC_CHECK_PIPE.format(arch="arm64")) for l in p.lines), p.lines
        assert any(l.startswith("step import:") and "godot.real" in l and "--headless --import --path ." in l for l in p.lines), p.lines
        assert "clang: present" in p.lines, p.lines
        assert not any("build_pipe_linux" in l for l in p.lines), p.lines
        for step in STEPS:
            assert any(re.search(rf"\b{step}\b", l) for l in p.lines), p.lines
        assert r.calls() == [], r.calls()
        assert r.snapshot() == before and r.pipe() == OLD
    finally:
        r.close()


def test_darwin_check_names_the_intel_architecture_when_uname_says_x86_64():
    """H-087 R-087-01/R-087-04: ARCH comes from `uname -m` and is not fixed: x86_64 appears in the pipe line; control: not arm64."""
    r = DarwinRig(arch="x86_64")
    try:
        p = r.run("--check")
        assert any(l.startswith(MAC_CHECK_PIPE.format(arch="x86_64")) for l in p.lines), p.lines
        assert not any("ARCH=arm64" in l for l in p.lines), p.lines
    finally:
        r.close()


def test_darwin_check_reports_clang_missing_and_still_exits_zero():
    """H-087 R-087-04: `clang: missing` when no clang is on PATH (positive control for 'present' above); `--check` still exits 0 and runs nothing."""
    r = DarwinRig(clang=False)
    try:
        p = r.run("--check")
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert "clang: missing" in p.lines and "clang: present" not in p.lines, p.lines
        assert r.calls() == [], r.calls()
    finally:
        r.close()


def test_darwin_check_names_the_app_godot_when_godot_real_is_not_on_path():
    """H-087 R-087-02/R-087-04: with only the app binary present the import step names it; with neither, the line says none was found and names
    both places (godot.real on PATH and the app path). `--check` exits 0 in both."""
    a = DarwinRig(godot="app")
    n = DarwinRig(godot="none")
    try:
        pa = a.run("--check")
        assert pa.returncode == 0 and any(l.startswith("step import:") and str(a.app) in l for l in pa.lines), pa.lines
        pn = n.run("--check")
        imp = [l for l in pn.lines if l.startswith("step import:")]
        assert pn.returncode == 0 and len(imp) == 1 and "godot.real" in imp[0] and str(n.app) in imp[0], pn.lines
    finally:
        a.close()
        n.close()


@pytest.mark.parametrize("arch", ["arm64", "x86_64"])
def test_darwin_run_builds_through_the_macos_script_with_the_uname_arch(arch):
    """H-087 R-087-01: on Darwin with no pipe copy, the run calls scripts/build_pipe_macos.sh with ARCH=<uname -m> (never build_pipe_linux.sh),
    copies dist/macos/ouroboros_pipe to pipe/ouroboros_pipe, leaves no temporary name behind, and ends `EDITOR READY <tree>`."""
    r = DarwinRig(arch=arch)
    try:
        p = r.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert r.calls().count(f"build-macos ARCH={arch}") == 1 and "build" not in r.calls(), r.calls()
        assert r.pipe() == BUILT_MAC
        assert [x.name for x in (r.tree / "pipe").iterdir()] == ["ouroboros_pipe"]
        assert f"EDITOR READY {r.tree}" in p.lines, p.lines
    finally:
        r.close()


def test_darwin_stale_pipe_is_rebuilt_and_a_fresh_one_is_not():
    """H-087 R-087-01 ("no pipe or a pipe older than csrc/"): stale copy rebuilt through the macOS script; fresh copy kept with its mtime and the run
    still ends `EDITOR READY`. The staleness test must work with the BSD find of macOS (no `-quit`): the case only checks behaviour here."""
    s = DarwinRig(pipe="stale")
    f = DarwinRig(pipe="fresh")
    try:
        ps = s.run()
        assert ps.returncode == 0 and s.calls().count("build-macos ARCH=arm64") == 1 and s.pipe() == BUILT_MAC, (ps.lines, s.calls())
        mtime = (f.tree / "pipe" / "ouroboros_pipe").stat().st_mtime_ns
        pf = f.run()
        assert pf.returncode == 0 and "build-macos ARCH=arm64" not in f.calls() and f.pipe() == OLD, (pf.lines, f.calls())
        assert (f.tree / "pipe" / "ouroboros_pipe").stat().st_mtime_ns == mtime
        assert f"EDITOR READY {f.tree}" in pf.lines
    finally:
        s.close()
        f.close()


def test_darwin_failing_macos_build_prints_editor_setup_failed_pipe():
    """H-087 R-087-01: a failing build_pipe_macos.sh gives `EDITOR SETUP FAILED pipe`, no `EDITOR READY`, no pipe copy (control: the Linux twin above)."""
    r = DarwinRig()
    try:
        write_exec(r.tree / "scripts" / "build_pipe_macos.sh", "exit 1\n")
        p = r.run()
        assert "EDITOR SETUP FAILED pipe" in p.lines, p.lines
        assert not any(l.startswith("EDITOR READY") for l in p.lines) and r.pipe() is None
    finally:
        r.close()


def test_darwin_import_uses_the_app_godot_when_godot_real_is_absent():
    """H-087 R-087-02: no godot.real on PATH, the app binary present: the import step runs it with `--headless --import --path .` once and the
    run ends `EDITOR READY <tree>`."""
    r = DarwinRig(godot="app")
    try:
        p = r.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert r.calls().count(f"{APP_STUB_NAME} --headless --import --path .") == 1, r.calls()
        assert f"EDITOR READY {r.tree}" in p.lines, p.lines
    finally:
        r.close()


def test_darwin_godot_real_on_path_beats_the_app():
    """H-087 R-087-02 (order of scripts/run_godot_tests.sh): both present, godot.real runs and the app binary does not."""
    r = DarwinRig(godot="both")
    try:
        p = r.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert "godot.real --headless --import --path ." in r.calls() and not any(c.startswith(APP_STUB_NAME) for c in r.calls()), r.calls()
    finally:
        r.close()


def test_darwin_no_godot_prints_setup_failed_import_and_names_both_places():
    """H-087 R-087-02: neither godot.real on PATH nor the app binary: `EDITOR SETUP FAILED import` is printed, a line names `godot.real` and the
    app path it looked at, and there is no `EDITOR READY`."""
    r = DarwinRig(godot="none")
    try:
        p = r.run()
        assert "EDITOR SETUP FAILED import" in p.lines, p.lines
        assert any("godot.real" in l and str(r.app) in l for l in p.lines), p.lines
        assert not any(l.startswith("EDITOR READY") for l in p.lines)
    finally:
        r.close()


def test_linux_is_unchanged_by_the_darwin_route():
    """H-087 R-087-01/R-087-02 "on Linux nothing changes" (control for the darwin cases): with `uname` answering Linux the Linux build script runs,
    the macOS one does not, and an app binary planted at OM_GODOT_APP is not consulted: with no godot.real the run fails at `import`."""
    r = DarwinRig(godot="app")
    try:
        write_exec(r.bin / "uname", 'case "$1" in -m) echo x86_64;; *) echo Linux;; esac\n')
        p = r.run()
        assert r.calls().count("build") == 1 and not any(c.startswith("build-macos") for c in r.calls()), r.calls()
        assert "EDITOR SETUP FAILED import" in p.lines and not any(c.startswith(APP_STUB_NAME) for c in r.calls()), (p.lines, r.calls())
    finally:
        r.close()


# ---------------------------------------------------------------- scripts/fetch_godotsteam.sh (R-087-03)

FETCH = ROOT / "scripts" / "fetch_godotsteam.sh"


class FetchRig:
    """A scratch tree with the real fetch_godotsteam.sh and a tiny zip holding addons/godotsteam/x.gdextension; the checksum tools are stubs."""

    def __init__(self, sha256sum, shasum, shasum_prints=None):
        import zipfile
        self.base = tmp("h087-fetch-").resolve()
        (self.base / "tree" / "scripts").mkdir(parents=True)
        shutil.copy2(FETCH, self.base / "tree" / "scripts" / "fetch_godotsteam.sh")
        self.pinned = re.search(r'SHA256="([0-9a-f]{64})"', FETCH.read_text()).group(1)
        self.zip = self.base / "g.zip"
        with zipfile.ZipFile(self.zip, "w") as z:
            z.writestr("addons/godotsteam/x.gdextension", "ext\n")
        self.log = self.base / "calls.log"
        self.log.write_text("")
        self.bin = self.base / "bin"
        shown = shasum_prints or self.pinned
        if shasum:  # BSD/macOS: only `shasum -a 256 <file>` is accepted
            write_exec(self.bin / "shasum", f'echo "shasum $*" >> {self.log}\n[ "$1 $2" = "-a 256" ] || exit 1\necho "{shown}  $3"\n')
        if sha256sum:
            write_exec(self.bin / "sha256sum", f'echo "sha256sum $*" >> {self.log}\necho "{shown}  $1"\n')
        self.tools = tools_dir(self.base)

    def run(self):
        env = {"PATH": f"{self.bin}:{self.tools}", "HOME": str(self.base)}
        return subprocess.run(["bash", str(self.base / "tree" / "scripts" / "fetch_godotsteam.sh"), str(self.zip)], env=env,
                              capture_output=True, text=True, timeout=60)

    def unpacked(self):
        return (self.base / "tree" / "addons" / "godotsteam" / "x.gdextension").is_file()

    def calls(self):
        return self.log.read_text().splitlines()

    def close(self):
        shutil.rmtree(self.base, ignore_errors=True)


def test_darwin_fetch_uses_shasum_when_sha256sum_is_absent_and_the_pinned_sha_gates_the_unpack():
    """H-087 R-087-03: no sha256sum on PATH, shasum present: the script calls `shasum -a 256 <zip>` and, the sum equal to the pinned one, unpacks.
    Control (the gate): the same rig with shasum printing another sum exits 1, says `sha256 mismatch` and unpacks nothing."""
    ok = FetchRig(sha256sum=False, shasum=True)
    bad = FetchRig(sha256sum=False, shasum=True, shasum_prints="0" * 64)
    try:
        p = ok.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert any(c.startswith("shasum -a 256 ") for c in ok.calls()) and ok.unpacked(), ok.calls()
        q = bad.run()
        assert q.returncode == 1 and "sha256 mismatch" in q.stderr and not bad.unpacked(), (q.returncode, q.stderr)
    finally:
        ok.close()
        bad.close()


def test_darwin_fetch_keeps_sha256sum_when_it_is_present():
    """H-087 R-087-03 "the Linux route is unchanged": both tools present, sha256sum is the one called and shasum is not; the unpack happens."""
    r = FetchRig(sha256sum=True, shasum=True)
    try:
        p = r.run()
        assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
        assert any(c.startswith("sha256sum ") for c in r.calls()) and not any(c.startswith("shasum") for c in r.calls()), r.calls()
        assert r.unpacked()
    finally:
        r.close()


def test_darwin_readme_open_in_the_editor_says_what_a_mac_needs():
    """H-087 R-087-05: the README "Open in the editor" section names Godot 4.6.3 in /Applications and the Xcode command line tools (clang), and
    still names the one command `scripts/setup_editor.sh`. Control: the section exists and already names the command today (so the red part is
    the Mac sentence only)."""
    text = (ROOT / "README.md").read_text()
    m = re.search(r"### Open in the editor\n(.*?)(?=\n## |\n### )", text, re.S)
    assert m, "README has no 'Open in the editor' section"
    sec = m.group(1)
    assert "scripts/setup_editor.sh" in sec
    assert "/Applications" in sec and "4.6.3" in sec and re.search(r"command line tools", sec, re.I) and "clang" in sec, sec
    assert "godotengine.org" in sec and "xcode-select --install" in sec, sec  # AC-5
