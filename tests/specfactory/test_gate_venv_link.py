# spec: docs/northstar/plans/push_ledger_2026-09-22.md rows FINDING-gate-venv-link-vs-fresh-checkout,
#       TD-gate-known-red-empty-form and TD-gate-venv-unlink; piece HARNESS-gate-venv-link
#       (docs/northstar/plans/2026-10-07-visible-game-spec.md, lane H paragraph "HARNESS-gate-venv-link")
# Rule pins: none (this piece proves a ledger finding, not a bible rule)
"""HARNESS-gate-venv-link: the gate's godot_import step links the harness venv into the candidate
(`ok venv_link`) and the playthrough's test_fresh_checkout_boots_to_main_menu_without_numpy_or_logs asserts the
checkout has no .venv, so it rejected (FINDING-gate-venv-link-vs-fresh-checkout). The fix: the import block sets
VENV_LINK_MADE when it makes the link and a block above the playthrough stage removes only that link and prints
`ok venv_unlink`; the link stays for the import, acceptance, acceptance_godot, regression and transport stages.

Ledger words (FINDING-gate-venv-link-vs-fresh-checkout, day37): "When a piece's acceptance touches
tests/qa/desktop the gate's godot_import step links the harness venv into the candidate (gate log line
`ok venv_link ...`); the playthrough stage then runs test_fresh_checkout_boots_to_main_menu_without_numpy_or_logs,
which asserts the checkout has no .venv, and rejects ... With the link removed the same test passes alone."
TD-gate-venv-unlink: "The test now asserts the link is gone after the gate and no .venv exists in the
candidate; the positive control, a .venv that existed before the gate is still there after it, lives in
tests/specfactory/test_gate_venv_link.py (case C3)". TD-gate-known-red-empty-form: the empty-file form of the
playthrough known-red list is retired (case R4 asserts only that the one entry for this finding is gone).

The gate is driven the way tests/specfactory/test_merge_gate.py drives it (a fixture git repo, a fake godot on
PATH, MERGE_GATE_VENV pointing at a tmp dir, a fake repo root), with merge_gate_support.py replaced by a stub whose
`playthrough` subcommand records whether <candidate>/.venv exists when the stage runs; every other subcommand
os.exec-s the real script. No test here links, removes or reads the real ~/Projects/agora/.venv.

Cases. Controls, green on the base tree: C1 the link exists when import and acceptance need it; C2 the link
target survives; C3 a pre-existing real .venv directory stays; C6 a pre-existing dangling .venv symlink stays;
C4 a csim-only piece neither links nor unlinks; C5 the fresh-checkout test fixture (positive control of the
mechanism). Red until built: R1 no .venv when the playthrough stage runs; R2 `ok venv_unlink` between the
acceptance stage lines and the playthrough line; R3 the end-to-end playthrough stage is OK; R4 the real
playthrough_known_red.txt no longer lists the fresh-checkout test.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_toy_root import overlay_sweeps, write_story  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO / "scripts" / "specfactory"
KNOWN_RED = SPEC_DIR / "playthrough_known_red.txt"
FRESH_TEST = REPO / "tests" / "qa" / "desktop" / "test_fresh_checkout_boot.py"
GATE_PATH = "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"
FRESH_NAME = "test_fresh_checkout_boots_to_main_menu_without_numpy_or_logs"
FINDING = "FINDING-gate-venv-link-vs-fresh-checkout"
VENV_MESSAGE = "checkout has a .venv; not a fresh checkout"
GATE_TIMEOUT_S = 60  # tests/specfactory/test_merge_gate.py: the fixture gate run


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


FAST_MAKEFILE = """\
libouroboros.so:
\ttouch $@
libouroboros_dbg.so:
\ttouch $@
"""

# The fake godot records, per call, whether <candidate>/.venv is a symlink and where it points; the --path
# argument names the candidate.
FAKE_GODOT = """\
#!/usr/bin/env bash
echo "$@" >> "$GODOT_ARGS_LOG"
cand=""
prev=""
for a in "$@"; do
    if [[ "$prev" == "--path" ]]; then cand="$a"; fi
    prev="$a"
done
if [[ -L "$cand/.venv" ]]; then
    echo "symlink $(readlink -f "$cand/.venv")" >> "$GODOT_VENV_LOG"
else
    echo "nolink" >> "$GODOT_VENV_LOG"
fi
exit 0
"""

# Runs inside the candidate (its cwd) during the acceptance stage.
ACCEPTANCE_TEST = """\
import os


def test_pass():
    with open("acc_seen", "w") as f:
        f.write(str(os.path.islink(".venv")))
"""

# A stand-in for tests/qa/desktop/daemon_client.py: REPO_ROOT comes from the environment; the game start raises.
STUB_DAEMON_CLIENT = """\
import os
from pathlib import Path

REPO_ROOT = Path(os.environ["OM_FIXTURE_REPO_ROOT"])


class GodotGame:
    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        raise RuntimeError("FIXTURE_REACHED_GODOT")

    def wait_for_port(self, *args, **kwargs):
        pass

    def stop(self):
        pass


def control_center(*args, **kwargs):
    return (0, 0)


def find_control(*args, **kwargs):
    return None


def pick_free_port():
    return 0
"""

# merge_gate_support.py stub: `playthrough` records lexists(<candidate>/.venv) and runs PLAYTHROUGH_BODY;
# every other subcommand is the real script. argv[2] is the candidate directory.
SUPPORT_STUB = """\
import os
import sys
from pathlib import Path

REAL = {real!r}
HERE = Path(__file__).resolve().parent
if len(sys.argv) > 2 and sys.argv[1] == "playthrough":
    cand = sys.argv[2]
    (HERE / "playthrough_venv_seen").write_text(str(os.path.lexists(os.path.join(cand, ".venv"))))
{body}
os.execv(sys.executable, [sys.executable, REAL] + sys.argv[1:])
"""

PLAYTHROUGH_PLAIN = """\
    print("OK stub")
    sys.exit(0)
"""

# R3: the stub playthrough runs the C5 fixture inside the candidate (the fixture's REPO_ROOT is the candidate).
PLAYTHROUGH_FRESH = """\
    import subprocess
    env = dict(os.environ, OM_FIXTURE_REPO_ROOT=cand)
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--color=no",
                        {fixture_test!r}], cwd={fixture_dir!r}, env=env, capture_output=True, text=True)
    out = p.stdout + p.stderr
    if "FIXTURE_REACHED_GODOT" in out:
        print("OK fixture reached godot")
        sys.exit(0)
    print("REJECT " + ({message!r} if "AssertionError: " + {message!r} in out else out[-300:].replace(chr(10), " ")))
    sys.exit(1)
"""


# A lane D play (lane_plays.toml: scenes/space3d/**) that needs no .venv: it passes and records whether one exists.
LANE_PLAY = """\
import os


def test_play():
    with open("lane_play_seen", "w") as f:
        f.write(str(os.path.lexists(".venv")))
"""


def _init_fixture_repo(repo: Path, lane_play: bool = False) -> Path:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    (repo / "csrc").mkdir()
    (repo / "csrc" / "stub.c").write_text("int om_stub(void) { return 0; }\n")
    (repo / "Makefile").write_text(FAST_MAKEFILE)
    for d in ("tests/csim", "tests/qa/t1"):
        (repo / d).mkdir(parents=True)
    write_story(repo, "B1")  # H-020
    write_story(repo, "D1", tests="tests/qa/desktop/test_x.py::test_pass")  # H-020: the old row's acceptance
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "remote", "add", "origin", str(repo))
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    (repo / "tests" / "qa" / "desktop").mkdir()
    (repo / "tests" / "qa" / "desktop" / "test_x.py").write_text(ACCEPTANCE_TEST)
    if lane_play:
        (repo / "scenes" / "space3d").mkdir(parents=True)
        (repo / "scenes" / "space3d" / "a.gd").write_text("extends Node\n")
        (repo / "tests" / "qa" / "desktop" / "plays" / "D").mkdir(parents=True)
        (repo / "tests" / "qa" / "desktop" / "plays" / "D" / "test_play.py").write_text(LANE_PLAY)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")
    return repo


def _write_pieces(path: Path) -> None:
    path.write_text(
        '[[piece]]\nid = "D1"\nowns = ["tests/qa/desktop/test_x.py"]\n'
        'acceptance = ["tests/qa/desktop/test_x.py::test_pass"]\ndepends_on = []\n\n'
        '[[piece]]\nid = "B1"\nowns = ["csrc/stub.c"]\nacceptance = []\ndepends_on = []\n'
    )


def _fake_root(tmp_path: Path, stub_text: str) -> Path:
    """Fake repo root: docs/ and every scripts/specfactory file symlinked, except the stubbed merge_gate_support.py."""
    root = tmp_path / "fakeroot"
    (root / "scripts" / "specfactory").mkdir(parents=True)
    (root / "docs").symlink_to(REPO / "docs")
    overlay_sweeps(root)  # H-020: never the live sweeps.md
    for f in SPEC_DIR.iterdir():
        if f.name != "merge_gate_support.py":
            (root / "scripts" / "specfactory" / f.name).symlink_to(f)
    (root / "scripts" / "specfactory" / "merge_gate_support.py").write_text(stub_text)
    return root


def _fresh_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """C5 fixture: the real fresh-checkout test copied beside the stub daemon_client. Returns (dir, test file)."""
    fixture = tmp_path / "fresh_fixture"
    fixture.mkdir(parents=True)
    (fixture / "daemon_client.py").write_text(STUB_DAEMON_CLIENT)
    test_file = fixture / "test_fresh_checkout_boot.py"
    shutil.copyfile(FRESH_TEST, test_file)
    return fixture, test_file


class GateRun:
    def __init__(self, tmp_path, piece, *, pre=None, end_to_end=False, lane_play=False):
        self.tmp = tmp_path
        self.repo = _init_fixture_repo(tmp_path / "repo", lane_play)
        self.fake_venv = tmp_path / "fake_venv"
        self.fake_venv.mkdir()
        (self.fake_venv / "marker").write_text("target\n")
        if end_to_end:
            fixture_dir, fixture_test = _fresh_fixture(tmp_path)
            body = PLAYTHROUGH_FRESH.format(fixture_test=str(fixture_test), fixture_dir=str(fixture_dir),
                                            message=VENV_MESSAGE)
        else:
            body = PLAYTHROUGH_PLAIN
        self.root = _fake_root(tmp_path, SUPPORT_STUB.format(real=str(SPEC_DIR / "merge_gate_support.py"), body=body))
        pieces = tmp_path / "pieces.toml"
        _write_pieces(pieces)
        fake_bin = tmp_path / "fakebin"
        fake_bin.mkdir()
        (fake_bin / "godot").write_text(FAKE_GODOT)
        (fake_bin / "godot").chmod(0o755)
        self.args_log = tmp_path / "godot_args.log"
        self.venv_log = tmp_path / "godot_venv.log"
        if pre is not None:
            pre(self)
        env = {
            "MERGE_GATE_PIECES": str(pieces),
            "PATH": f"{fake_bin}:{GATE_PATH}",
            "GODOT_ARGS_LOG": str(self.args_log),
            "GODOT_VENV_LOG": str(self.venv_log),
            "MERGE_GATE_VENV": str(self.fake_venv),
        }
        self.proc = subprocess.run(
            ["bash", str(self.root / "scripts" / "specfactory" / "merge_gate.sh"), "--tier", "full", str(self.repo), "HEAD~1", piece],
            capture_output=True, text=True, env=env, timeout=GATE_TIMEOUT_S)
        self.lines = self.proc.stdout.splitlines()
        # the lines these cases are about; the fixture gate prints other stage lines (rejects of a fixture repo) that are noise
        self.out = "\n".join(l for l in self.lines if l.startswith(("ok venv", "GATE godot_import", "GATE acceptance",
                                                                    "GATE regression", "GATE transport",
                                                                    "GATE playthrough", "GATE lane_plays"))) \
            + "\n" + self.proc.stderr[-300:]

    def playthrough_saw_venv(self) -> str:
        return (self.root / "scripts" / "specfactory" / "playthrough_venv_seen").read_text()

    def index(self, prefix):
        return [i for i, l in enumerate(self.lines) if l.startswith(prefix)]


@pytest.fixture(scope="module")
def d1(tmp_path_factory):
    """The desktop piece D1 (acceptance under tests/qa/desktop), one gate run shared by C1, C2, R1, R2."""
    return GateRun(tmp_path_factory.mktemp("d1"), "D1")


# ---- controls, green on the base tree -------------------------------------------------------------------------

def test_C1_link_exists_when_import_and_acceptance_need_it(d1):
    """The desktop acceptance needs the venv (FINDING-gate-venv-link-vs-fresh-checkout): the fake godot import saw
    a symlink to MERGE_GATE_VENV, the acceptance test saw a link in its cwd, and the gate printed ok venv_link."""
    assert d1.venv_log.read_text().splitlines() == [f"symlink {d1.fake_venv.resolve()}"], d1.out
    assert (d1.repo / "acc_seen").read_text() == "True", d1.out
    assert f'ok venv_link "{d1.fake_venv}"' in d1.lines, d1.out


def test_C2_link_target_survives_the_gate(d1):
    """Only the link goes, never the target: the venv directory and its marker file are still there."""
    assert d1.fake_venv.is_dir() and (d1.fake_venv / "marker").read_text() == "target\n", d1.out


def test_C3_pre_existing_real_venv_directory_stays(tmp_path):
    """TD-gate-venv-unlink positive control: a .venv that existed before the gate is still there after it, and the
    gate neither linked nor unlinked anything."""
    def pre(g):
        (g.repo / ".venv").mkdir()
        (g.repo / ".venv" / "mine").write_text("keep\n")
    g = GateRun(tmp_path, "D1", pre=pre)
    assert (g.repo / ".venv").is_dir() and not (g.repo / ".venv").is_symlink(), g.out
    assert (g.repo / ".venv" / "mine").read_text() == "keep\n", g.out
    assert not any(l.startswith("ok venv_link") or l.startswith("ok venv_unlink") for l in g.lines), g.out


def test_C6_pre_existing_dangling_venv_symlink_stays(tmp_path):
    """A pre-existing dangling .venv symlink passes the `! -e` test, the ln -s fails (File exists), the flag stays 0:
    the symlink is still there with the same target and no ok venv_unlink was printed."""
    gone = tmp_path / "does_not_exist"

    def pre(g):
        os.symlink(gone, g.repo / ".venv")
    g = GateRun(tmp_path, "D1", pre=pre)
    assert (g.repo / ".venv").is_symlink() and os.readlink(g.repo / ".venv") == str(gone), g.out
    assert not any(l.startswith("ok venv_unlink") for l in g.lines), g.out


def test_C4_csim_only_piece_neither_links_nor_unlinks(tmp_path):
    g = GateRun(tmp_path, "B1")
    assert not any(l.startswith("ok venv_link") or l.startswith("ok venv_unlink") for l in g.lines), g.out
    assert g.playthrough_saw_venv() == "False", g.out
    assert g.index("GATE playthrough "), g.out


def test_C5_fresh_checkout_fixture_fails_with_a_venv_and_reaches_godot_without(tmp_path):
    """Positive control of the mechanism (W8): the real test_fresh_checkout_boot.py beside a stub daemon_client."""
    fixture, test_file = _fresh_fixture(tmp_path)
    repo_root = tmp_path / "fixture_repo"
    repo_root.mkdir()
    target = tmp_path / "some_dir"
    target.mkdir()
    env = dict(os.environ, OM_FIXTURE_REPO_ROOT=str(repo_root))
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--color=no", str(test_file)]

    (repo_root / ".venv").symlink_to(target)
    with_venv = subprocess.run(cmd, cwd=fixture, env=env, capture_output=True, text=True, timeout=120)
    assert with_venv.returncode != 0
    assert "AssertionError: " + VENV_MESSAGE in with_venv.stdout, with_venv.stdout
    assert "FIXTURE_REACHED_GODOT" not in with_venv.stdout, with_venv.stdout

    (repo_root / ".venv").unlink()
    without = subprocess.run(cmd, cwd=fixture, env=env, capture_output=True, text=True, timeout=120)
    assert "FIXTURE_REACHED_GODOT" in without.stdout, without.stdout
    # the traceback echoes the fixture's source, so the freshness assertion is looked for as a raised error
    assert "AssertionError" not in without.stdout, without.stdout


# ---- red until built ------------------------------------------------------------------------------------------

def test_R1_no_venv_when_the_playthrough_stage_runs(d1):
    """FINDING-gate-venv-link-vs-fresh-checkout: the link must be gone before the playthrough stage."""
    assert d1.playthrough_saw_venv() == "False", d1.out
    assert not (d1.repo / ".venv").exists() and not (d1.repo / ".venv").is_symlink(), d1.out


def test_R2_unlink_line_sits_between_the_acceptance_lines_and_the_playthrough_line(d1):
    """The link is made before godot_import and removed after every stage that needs it (acceptance,
    acceptance_godot, regression, transport) and before the playthrough stage; the line is raw, no GATE prefix."""
    link = d1.lines.index(f'ok venv_link "{d1.fake_venv}"')
    imports = d1.index("GATE godot_import ")
    assert imports and link < imports[0], d1.out
    unlinks = [i for i, l in enumerate(d1.lines) if l.startswith("ok venv_unlink")]
    assert len(unlinks) == 1 and d1.lines[unlinks[0]] == f'ok venv_unlink "{d1.fake_venv}"', d1.out
    unlink = unlinks[0]
    keep_link_stages = [i for st in ("acceptance", "acceptance_godot", "regression", "transport")
                        for i in d1.index(f"GATE {st} ")]
    assert d1.index("GATE acceptance ") and all(i < unlink for i in keep_link_stages), d1.out
    playthrough = d1.index("GATE playthrough ")
    assert len(playthrough) == 1 and unlink < playthrough[0], d1.out


def test_R3_playthrough_stage_ok_end_to_end(tmp_path):
    """The real fresh-checkout test, run by the stub playthrough inside the candidate, reaches the (stub) game
    start, so the stage is OK; on the base tree it is `GATE playthrough REJECT checkout has a .venv; not a
    fresh checkout`."""
    g = GateRun(tmp_path, "D1", end_to_end=True)
    stage = g.index("GATE playthrough ")
    assert len(stage) == 1 and g.lines[stage[0]].startswith("GATE playthrough OK"), \
        "\n".join(g.lines[stage[0]:stage[0] + 1] if stage else g.lines)


def test_R4_real_known_red_list_no_longer_lists_the_fresh_checkout_test():
    """The one entry of scripts/specfactory/playthrough_known_red.txt (FINDING-gate-venv-link-vs-fresh-checkout)
    leaves the list. Not asserted: that the file has no entry at all (the empty-file form is retired,
    TD-gate-known-red-empty-form)."""
    entries = [l for l in KNOWN_RED.read_text().splitlines() if l.strip() and not l.startswith("#")]
    named = [l for l in entries if FRESH_NAME in l or FINDING in l]
    assert named == [], named


def test_R5_lane_play_passes_with_no_venv_present(tmp_path):
    """HARNESS-gate-venv-link (Architect amendment 2026-10-23): the lane_plays stage runs after the unlink and needs
    no .venv (the client's C pipe path does not import the Python sim): the lane D play passes, the stage is OK, and
    the play saw no .venv. Positive control: R3 (the playthrough case, same unlink, end to end) and the same run
    with a pre-existing .venv, where the play sees it, so the assertion on the seen state can fail."""
    g = GateRun(tmp_path, "D1", lane_play=True)
    stage = g.index("GATE lane_plays ")
    assert len(stage) == 1 and g.lines[stage[0]].startswith("GATE lane_plays OK"), \
        "\n".join(g.lines[stage[0]:stage[0] + 1] if stage else g.lines)
    assert (g.repo / "lane_play_seen").read_text() == "False", g.out
    assert not (g.repo / ".venv").exists() and not (g.repo / ".venv").is_symlink(), g.out


def test_R5_control_lane_play_sees_a_pre_existing_venv(tmp_path):
    """Control for R5: with a real .venv in the candidate the play records True (and the gate keeps it), so R5's
    False is the unlink's doing, not a play that cannot see the directory."""
    g = GateRun(tmp_path, "D1", lane_play=True, pre=lambda g: (g.repo / ".venv").mkdir())
    assert (g.repo / "lane_play_seen").read_text() == "True", g.out
