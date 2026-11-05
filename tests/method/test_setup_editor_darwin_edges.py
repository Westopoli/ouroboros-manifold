# spec: docs/northstar/plans/cascades/b1-approved-screens/spec.md::Acceptance criteria::AC-1
"""H-087 boundary cases the umbrella (`darwin` cases of tests/method/test_setup_editor.py) does not reach.

Same rigs as the umbrella (imported, not copied): `uname`, `clang`, `shasum` and the macOS Godot are stubs on a scratch PATH; nothing runs on a Mac.
Every case here is behavioural: it runs the script and asserts on printed lines, files and the stub call log. Each case is RED today for the
missing Darwin route unless its name or docstring says CONTROL (green today, guards the Linux route or a boundary the new code must not move).
Boundaries the spec is silent on are not tested; they are in .swarm/b1-approved-screens/audits/wave-1/default/BOUNDARIES.md as questions.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests.method.test_setup_editor import (  # noqa: E402  (helpers only; no test functions are imported)
    BUILT_MAC, LONG_AGO, OLD, SCRIPT, FETCH, DarwinRig, FetchRig, write_exec,
)

DEFAULT_APP = "/Applications/Godot.app/Contents/MacOS/Godot"
IMPORT_ARGS = "--headless --import --path ."


def pipe_line(arch):
    return (f"step pipe: scripts/build_pipe_macos.sh (ARCH={arch}), then copy dist/macos/ouroboros_pipe to pipe/ouroboros_pipe "
            "(only when csrc/ is newer than the copy or the copy is missing)")


def steam_line(rig):
    cache = rig.home / "Projects" / "om-push" / "cache" / "godotsteam"
    return f"step steam: copy {cache} to addons/godotsteam (cp -a); on a cache miss run scripts/fetch_godotsteam.sh"


def run_without_app_seam(rig, *args):
    """Like DarwinRig.run but OM_GODOT_APP is unset, so the script's own default app path applies."""
    env = {"HOME": str(rig.home), "PATH": f"{rig.bin}:{rig.tools}"}
    r = subprocess.run(["bash", str(rig.tree / "scripts" / "setup_editor.sh"), *args], cwd=str(rig.tree), env=env,
                       capture_output=True, text=True, timeout=60)
    r.lines = (r.stdout + r.stderr).splitlines()
    return r


# ---------------------------------------------------------------- Linux route stays byte for byte (CONTROLS, green today)

@pytest.mark.parametrize("uname_s", ["Linux", "FreeBSD", "darwin"])
def test_control_non_darwin_check_prints_the_three_linux_lines_only(uname_s):
    """CONTROL. spec AC-1 / contract Detection: "Any other answer is the Linux route, byte for byte as on main." `uname -s` of Linux, an unknown OS
    and a lowercase `darwin` (not `Darwin`) all give exactly the three H-067 lines: no `clang:` line, no build_pipe_macos."""
    r = DarwinRig()
    try:
        write_exec(r.bin / "uname", f'case "$1" in -m) echo arm64;; *) echo {uname_s};; esac\n')
        p = r.run("--check")
        want = ["step pipe: scripts/build_pipe_linux.sh, then copy dist/linux/ouroboros_pipe to pipe/ouroboros_pipe "
                "(only when csrc/ is newer than the copy or the copy is missing)",
                steam_line(r), f"step import: godot.real {IMPORT_ARGS}"]
        assert (p.returncode, p.lines) == (0, want), (p.returncode, p.lines)
    finally:
        r.close()


# ---------------------------------------------------------------- --check on Darwin (R-087-04)

def test_darwin_check_prints_exactly_the_four_contract_lines_in_order():
    """spec AC-4 / contract `--check` output: four lines, in the order pipe, steam, import, clang; the steam line is the Linux line unchanged; the
    import line names the godot the run would use (absolute path or the PATH name)."""
    r = DarwinRig(arch="arm64", pipe="stale")
    try:
        p = r.run("--check")
        assert len(p.lines) == 4 and [p.lines[0], p.lines[1], p.lines[3]] == [pipe_line("arm64"), steam_line(r), "clang: present"], p.lines
        assert re.fullmatch(rf"step import: (godot\.real|{re.escape(str(r.bin / 'godot.real'))}) {re.escape(IMPORT_ARGS)}", p.lines[2]), p.lines
    finally:
        r.close()


@pytest.mark.parametrize("pipe_state", [None, "fresh", "stale"])
def test_darwin_check_is_the_same_and_inert_whether_the_pipe_is_absent_fresh_or_stale(pipe_state):
    """spec AC-4 / contract: the pipe line is constant text ("only when ... is missing"), so absent, fresh and stale copies print the same line; exit
    0; no stub runs; scratch tree and HOME untouched."""
    r = DarwinRig(arch="x86_64", pipe=pipe_state)
    try:
        before = r.snapshot()
        p = r.run("--check")
        assert p.returncode == 0 and p.lines[0] == pipe_line("x86_64"), (p.returncode, p.lines)
        assert r.calls() == [] and r.snapshot() == before, r.calls()
    finally:
        r.close()


def test_darwin_check_exits_zero_with_everything_missing_and_says_so():
    """spec AC-4 ("exits 0, changes nothing") / contract: no godot anywhere, no clang, no steam cache, no pipe: `--check` still exits 0 and prints
    the none-found line naming `godot.real` on PATH and the app path, and `clang: missing`; nothing changes."""
    r = DarwinRig(godot="none", clang=False, cache=False)
    try:
        before = r.snapshot()
        p = r.run("--check")
        want = [pipe_line("arm64"), steam_line(r), f"step import: none found (looked at: godot.real on PATH, {r.app})", "clang: missing"]
        assert (p.returncode, p.lines) == (0, want), (p.returncode, p.lines)
        assert r.calls() == [] and r.snapshot() == before
    finally:
        r.close()


def test_darwin_check_default_app_path_is_applications_when_om_godot_app_is_unset():
    """spec AC-2 / contract: `<app path>` is `$OM_GODOT_APP`, default `/Applications/Godot.app/Contents/MacOS/Godot`."""
    r = DarwinRig(godot="none")
    try:
        p = run_without_app_seam(r, "--check")
        assert f"step import: none found (looked at: godot.real on PATH, {DEFAULT_APP})" in p.lines, p.lines
    finally:
        r.close()


# ---------------------------------------------------------------- Godot discovery (R-087-02)

def test_darwin_run_failure_line_names_godot_real_and_the_default_app_path_once_before_the_failed_line():
    """spec AC-2: with OM_GODOT_APP unset and no Godot, exactly one line names `godot.real` and `/Applications/Godot.app/Contents/MacOS/Godot`, and
    it comes before `EDITOR SETUP FAILED import`."""
    r = DarwinRig(godot="none")
    try:
        p = run_without_app_seam(r)
        named = [i for i, l in enumerate(p.lines) if "godot.real" in l and DEFAULT_APP in l]
        assert len(named) == 1 and "EDITOR SETUP FAILED import" in p.lines and named[0] < p.lines.index("EDITOR SETUP FAILED import"), p.lines
    finally:
        r.close()


def test_darwin_home_local_bin_godot_real_beats_the_app():
    """spec AC-2 order: godot.real on PATH, else $HOME/.local/bin/godot.real, else the app. With only the home copy and the app present, the home copy
    runs the import and the app does not; the run took the Darwin pipe route (that is the red part)."""
    r = DarwinRig(godot="app")
    try:
        write_exec(r.home / ".local" / "bin" / "godot.real", f'echo "home-godot $*" >> {r.log}\n')
        p = r.run()
        assert p.returncode == 0 and f"home-godot {IMPORT_ARGS}" in r.calls() and not any(c.startswith("app-godot") for c in r.calls()), r.calls()
        assert r.calls().count("build-macos ARCH=arm64") == 1, r.calls()
    finally:
        r.close()


# ---------------------------------------------------------------- pipe step (R-087-01)

def test_darwin_uname_m_value_is_passed_through_as_arch():
    """spec AC-1 / contract `ARCH=<uname -m>`: an architecture other than arm64/x86_64 is not rewritten: --check shows it and the build stub gets it."""
    r = DarwinRig(arch="i386")
    try:
        assert r.run("--check").lines[0] == pipe_line("i386")
        p = r.run()
        assert p.returncode == 0 and r.calls().count("build-macos ARCH=i386") == 1 and r.pipe() == BUILT_MAC, (p.lines, r.calls())
    finally:
        r.close()


def test_darwin_failed_copy_removes_the_temporary_name_keeps_the_old_pipe_and_fails_pipe():
    """spec AC-1 ("copies ... by temporary name then move", the same as Linux, whose failure path removes `pipe/ouroboros_pipe.new.$$`): a `cp`
    that leaves a partial temporary file and fails gives `EDITOR SETUP FAILED pipe`, no leftover `ouroboros_pipe.new.*`, the old pipe untouched."""
    r = DarwinRig(pipe="stale")
    try:
        write_exec(r.bin / "cp", 'for last; do :; done\n: > "$last"\nexit 1\n')
        p = r.run()
        assert "EDITOR SETUP FAILED pipe" in p.lines, p.lines
        assert r.calls() == ["build-macos ARCH=arm64"] and r.pipe() == OLD, r.calls()
        assert sorted(x.name for x in (r.tree / "pipe").iterdir()) == ["ouroboros_pipe"]
    finally:
        r.close()


def test_darwin_build_that_leaves_no_artifact_fails_pipe():
    """spec AC-1 / contract ("failure prints EDITOR SETUP FAILED pipe"): build_pipe_macos.sh exits 0 but writes no dist/macos/ouroboros_pipe: the
    copy fails, the run says `EDITOR SETUP FAILED pipe` and no pipe copy appears."""
    r = DarwinRig()
    try:
        write_exec(r.tree / "scripts" / "build_pipe_macos.sh", f'echo "build-macos ARCH=$ARCH" >> {r.log}\n')
        p = r.run()
        assert "EDITOR SETUP FAILED pipe" in p.lines and r.pipe() is None, p.lines
    finally:
        r.close()


def test_darwin_a_newer_file_nested_under_csrc_makes_the_pipe_stale():
    """spec AC-1 ("older than csrc/"): the newer file is in a subdirectory (csrc/pipe/), not at the top: the macOS build runs and the copy is replaced."""
    r = DarwinRig(pipe="fresh")
    try:
        nested = r.tree / "csrc" / "pipe" / "om_pipe.c"
        nested.parent.mkdir()
        nested.write_text("int y;\n")
        os.utime(nested, (LONG_AGO + 2000, LONG_AGO + 2000))
        p = r.run()
        assert p.returncode == 0 and r.calls().count("build-macos ARCH=arm64") == 1 and r.pipe() == BUILT_MAC, (p.lines, r.calls())
    finally:
        r.close()


def test_control_darwin_pipe_exactly_as_old_as_csrc_is_not_stale():
    """CONTROL (green today; guards `older than` as strict `<`): the copy and the only csrc file carry the identical mtime: nothing is rebuilt and the
    old copy stays."""
    r = DarwinRig(pipe="fresh")
    try:
        same = (r.tree / "pipe" / "ouroboros_pipe").stat().st_mtime_ns
        os.utime(r.tree / "csrc" / "sim.c", ns=(same, same))
        p = r.run()
        assert p.returncode == 0 and "build-macos ARCH=arm64" not in r.calls() and r.pipe() == OLD, (p.lines, r.calls())
    finally:
        r.close()


def test_darwin_empty_csrc_and_no_pipe_still_builds():
    """spec AC-1 ("with no pipe"): the staleness test finds no csrc file at all, yet a missing copy is built."""
    r = DarwinRig()
    try:
        (r.tree / "csrc" / "sim.c").unlink()
        p = r.run()
        assert p.returncode == 0 and r.calls().count("build-macos ARCH=arm64") == 1 and r.pipe() == BUILT_MAC, (p.lines, r.calls())
    finally:
        r.close()


@pytest.mark.parametrize("cache", [True, False])
def test_darwin_steps_run_in_order_and_a_mac_without_a_steam_cache_takes_the_fetch_route(cache):
    """spec Out of scope ("a Mac has none, so it takes the fetch route") + contract (steam line unchanged): pipe build, then fetch only on a cache
    miss, then the import, in that order."""
    r = DarwinRig(cache=cache)
    try:
        p = r.run()
        want = ["build-macos ARCH=arm64", *([] if cache else ["fetch"]), f"godot.real {IMPORT_ARGS}"]
        assert (p.returncode, r.calls()) == (0, want), (p.lines, r.calls())
    finally:
        r.close()


# ---------------------------------------------------------------- fetch_godotsteam.sh (R-087-03)

def test_darwin_fetch_mismatch_with_shasum_exits_1_and_names_expected_and_got_exactly():
    """spec AC-3 / contract: with only `shasum`, a wrong sum prints `sha256 mismatch: expected <pinned>, got <sum>` to stderr, exits 1, unpacks nothing."""
    r = FetchRig(sha256sum=False, shasum=True, shasum_prints="0" * 64)
    try:
        p = r.run()
        assert p.returncode == 1 and f"sha256 mismatch: expected {r.pinned}, got {'0' * 64}" in p.stderr, (p.returncode, p.stderr)
        assert not r.unpacked()
    finally:
        r.close()


def test_darwin_fetch_with_shasum_and_a_missing_zip_fails_and_unpacks_nothing():
    """spec AC-3 ("nothing is unpacked before the comparison passes"): shasum is consulted for the missing zip, fails as the real one does, and the
    run exits non-zero without unpacking."""
    r = FetchRig(sha256sum=False, shasum=True)
    try:
        write_exec(r.bin / "shasum", f'echo "shasum $*" >> {r.log}\n[ -f "$3" ] || {{ echo "shasum: $3: No such file" >&2; exit 1; }}\n'
                   f'echo "{r.pinned}  $3"\n')
        r.zip = r.base / "absent.zip"
        p = r.run()
        assert p.returncode != 0 and not r.unpacked(), (p.returncode, p.stderr)
        assert any(c.startswith("shasum -a 256 ") for c in r.calls()), r.calls()
    finally:
        r.close()


def test_control_fetch_prefers_sha256sum_over_shasum_when_both_exist():
    """CONTROL (green today): both tools present, sha256sum answers a wrong sum and shasum the right one: sha256sum decides, so the run mismatches,
    exits 1, unpacks nothing and shasum is never called (guards "uses sha256sum when present")."""
    r = FetchRig(sha256sum=True, shasum=True, shasum_prints="0" * 64)
    try:
        write_exec(r.bin / "shasum", f'echo "shasum $*" >> {r.log}\necho "{r.pinned}  $3"\n')
        p = r.run()
        assert p.returncode == 1 and not r.unpacked(), (p.returncode, p.stderr)
        assert not any(c.startswith("shasum") for c in r.calls()), r.calls()
    finally:
        r.close()
