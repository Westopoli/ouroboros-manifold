"""H-060 (docs/stories/H-060.md) ruling 4 and test 5: `scripts/beta_refresh.sh` writes `beta_build.txt` beside the exported binary.

Story ruling 4: "`scripts/beta_refresh.sh` writes it at export time: one line, the full sha".
Story ruling 6 / Tests 5: "`tests/method/test_beta_build_sha.py` (new): the fake-build route (stub `godot.real` and `build_pipe_linux.sh`, assert
`<root>/beta/<sha>/beta_build.txt` holds exactly the sha on one line); positive control: a stubbed export that fails writes no `beta_build.txt`."
Conventions of H-028's tests/method/test_beta_build.py: HOME and --root in tmpdirs, a stub `godot.real` first on PATH, a planted godotsteam cache so
no fetch runs. Nothing here runs Godot, opens a window or touches the real HOME or ~/Projects/om-push.
"""
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFRESH = ROOT / "scripts" / "beta_refresh.sh"
SHA = "0123abcd4567ef890123abcd4567ef890123abcd"  # full 40 hex
BINARY = "ouroboros_beta.x86_64"


def fake_build(export_ok):
    """Run the build phase on a fake tree and root. The stub godot.real writes the binary (last argument) and exits 0, or exits 1 when `export_ok` is
    false; the stub build_pipe_linux.sh writes dist/linux/ouroboros_pipe. Returns (completed process, root)."""
    base = Path(tempfile.mkdtemp(prefix="h060-sha-"))
    home, root, tree, bindir = base / "home", base / "om-push", base / "tree", base / "bin"
    (tree / "scripts").mkdir(parents=True)
    (root / "cache" / "godotsteam").mkdir(parents=True)
    bindir.mkdir()
    home.mkdir()
    (root / "cache" / "godotsteam" / "libgodotsteam.so").write_text("planted-library\n")
    pipe = tree / "scripts" / "build_pipe_linux.sh"
    pipe.write_text(f'#!/bin/sh\nmkdir -p "{tree}/dist/linux" && : > "{tree}/dist/linux/ouroboros_pipe"\n')
    pipe.chmod(0o755)
    stub = bindir / "godot.real"
    if export_ok:
        stub.write_text('#!/bin/bash\nout="${@: -1}"\nmkdir -p "$(dirname "$out")" && : > "$out" && chmod +x "$out"\nexit 0\n')
    else:
        stub.write_text("#!/bin/sh\nexit 1\n")
    stub.chmod(0o755)
    env = dict(os.environ, HOME=str(home), PATH=f"{bindir}:{os.environ['PATH']}")
    assert REFRESH.is_file(), f"{REFRESH} does not exist"
    r = subprocess.run([str(REFRESH), "--root", str(root), "--tree", str(tree), "--sha", SHA],
                       capture_output=True, text=True, timeout=60, env=env)
    return r, root


def test_control_fake_build_route_builds_the_binary_and_the_failing_export_fails():
    """H-060 test 5 positive control (green today): "a stubbed export that fails writes no `beta_build.txt`". The fake route works (the stubbed export
    builds `<root>/beta/<sha>/ouroboros_beta.x86_64` and the run exits 0), and a failing stubbed export exits non-zero with no `beta_build.txt` and no
    build dir. A red in the next test therefore means the script does not write the file, not that the fake route is broken."""
    ok, root_ok = fake_build(True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert (root_ok / "beta" / SHA / BINARY).is_file(), ok.stdout + ok.stderr
    bad, root_bad = fake_build(False)
    assert bad.returncode != 0, bad.stdout + bad.stderr
    assert not (root_bad / "beta" / SHA / "beta_build.txt").exists()


def test_build_phase_writes_beta_build_txt_holding_exactly_the_sha_on_one_line():
    """H-060 ruling 4 and test 5: "`scripts/beta_refresh.sh` writes it at export time: one line, the full sha"; "assert
    `<root>/beta/<sha>/beta_build.txt` holds exactly the sha on one line". RED today: the build phase writes no beta_build.txt."""
    r, root = fake_build(True)
    assert r.returncode == 0, r.stdout + r.stderr
    f = root / "beta" / SHA / "beta_build.txt"
    assert f.is_file(), "H-060: %s not written by the build phase; output = %s" % (f, r.stdout + r.stderr)
    assert f.read_text().splitlines() == [SHA], repr(f.read_text())
    assert f.read_text() in (SHA, SHA + "\n"), repr(f.read_text())
