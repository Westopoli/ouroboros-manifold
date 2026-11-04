# spec: docs/stories/H-067.md (part 2, the client refuses a stale pipe)
"""H-067 part 2: the client refuses a stale pipe, and the expected abi lives in one constant pinned to the C header.

Story H-067, Tests line proved here: "`tests/qa/test_pipe_abi_check.py` (new): a stub pipe reporting a wrong abi gives the ErrorPanel text with both
numbers; control: a matching abi shows no error; the GDScript constant equals `OM_ABI_VERSION` in `csrc/ouroboros_sim.h`."
Story Change part 2: "a mismatch with the expected value shows the ErrorPanel text `pipe binary is out of date (abi <n>, expected <m>): run
scripts/setup_editor.sh`. The expected value lives in ONE GDScript constant, and a test pins it equal to `OM_ABI_VERSION` in `csrc/ouroboros_sim.h`,
so a header bump without the client fails the gate."

The seam (the story's STOP condition does not fire): the hello frame IS visible to GDScript today. `autoload/c_bridge.gd` `_reader_loop` queues every
decoded frame, and `pump()` has no `hello` branch but ends every frame with `frame_received.emit(frame)`, so the hello (with its `abi`) reaches any
listener and the builder may read it there or in `open_session`. These tests are site-agnostic: they observe only the player-visible result, the
galaxy's ErrorPanel (`scenes/galaxy/galaxy_view.gd` `_show_load_error`, `qa_state()["error_panel"]` and the `ErrorReason` label's text in the qa
daemon's control tree). The stub pipe is a relay (a python script the game runs through the `OM_PIPE` override in `c_bridge._pipe_path()`): it execs the
real built pipe, forwards frames both ways untouched, and rewrites only the `abi` of the first (hello) frame.

Premises dumped on the built tree (base b0d2727f, 2026-11-02, dist/linux/ouroboros_pipe built from csrc/):
  real pipe, first frame: {'type': 'hello', 'abi': 9, 'layout_ok': True, 'seed': 0, 'n_regions': 0, 'features': [], 'checksum_cadence': 10,
  'player_faction': -1}; OM_ABI_VERSION in csrc/ouroboros_sim.h line 32 = 9.
  c_bridge.gd open_session line 235: `_last_error = "pipe binary missing"` (the string H-067 part 5 rewrites; shown by galaxy_view._show_load_error).
Assertion with NO seam today: none. The one thing these tests cannot pin is WHERE the check sits (open_session or a frame_received listener); they do
not need to. Not tested (the story gives no test): that a stale pipe stops the session from running, and the exit-time behaviour.
"""
from __future__ import annotations

import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "qa" / "desktop"))

from daemon_client import GodotGame, control_center, find_control, pick_free_port, wait_for  # noqa: E402

HEADER = ROOT / "csrc" / "ouroboros_sim.h"
GALAXY_SCENE = "res://scenes/galaxy/galaxy_view.tscn"
MAIN_MENU_SCENE = "res://scenes/main_menu/main_menu.tscn"
PRIVACY_MODAL_SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"
# Waits copied from tests/qa/desktop/test_galaxy_conquest.py (boot to the galaxy); LOAD_S is how long the galaxy gets to either load a world or
# show its error before the verdict is read. Test mechanics, not a rule threshold.
BOOT_TIMEOUT_S = 45.0
STEP_TIMEOUT_S = 10.0
LOAD_S = 30.0
STALE_TEXT = "pipe binary is out of date (abi %d, expected %d): run scripts/setup_editor.sh"

RELAY = '''#!{python}
"""H-067 stub pipe: run the real pipe, forward frames untouched, rewrite only the abi of the first (hello) frame."""
import json, struct, subprocess, sys, threading

REAL, ABI = {real!r}, {abi!r}
child = subprocess.Popen([REAL], stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def pump_in():
    try:
        while True:
            chunk = sys.stdin.buffer.read1(65536)
            if not chunk:
                break
            child.stdin.write(chunk)
            child.stdin.flush()
    except (BrokenPipeError, OSError):
        pass
    try:
        child.stdin.close()
    except OSError:
        pass


threading.Thread(target=pump_in, daemon=True).start()
first = True
try:
    while True:
        head = child.stdout.read(4)
        if len(head) < 4:
            break
        body = child.stdout.read(struct.unpack(">I", head)[0])
        if first and ABI is not None:
            frame = json.loads(body)
            frame["abi"] = ABI
            body = json.dumps(frame).encode()
        first = False
        sys.stdout.buffer.write(struct.pack(">I", len(body)) + body)
        sys.stdout.buffer.flush()
except (BrokenPipeError, OSError):
    pass
finally:
    child.kill()
'''


def header_abi() -> int:
    m = re.search(r"^#define\s+OM_ABI_VERSION\s+(\d+)\b", HEADER.read_text(), re.M)
    assert m, "no `#define OM_ABI_VERSION <n>` in %s" % HEADER
    return int(m.group(1))


def gdscript_abi_constants(files) -> list[tuple[str, int]]:
    """(file:line, value) of every `const <NAME with ABI as a whole _-token> [: int] := <digits>` (so `ABILITY_*` does not match) in the given GDScript files."""
    pat = re.compile(r"^\s*const\s+(?:\w+_)?abi(?:_\w+)?\s*(?::\s*int\s*)?:?=\s*(\d+)\s*(?:#.*)?$", re.I)
    found = []
    for f in files:
        for n, line in enumerate(Path(f).read_text(errors="replace").splitlines(), 1):
            m = pat.match(line)
            if m:
                found.append(("%s:%d" % (f, n), int(m.group(1))))
    return found


def client_gd_files():
    return sorted(list((ROOT / "autoload").rglob("*.gd")) + list((ROOT / "scenes").rglob("*.gd")))


@pytest.fixture(scope="module")
def real_pipe() -> Path:
    """The real pipe the relay execs: pipe/ or dist/linux/ when built, else built once with scripts/build_pipe_linux.sh."""
    for cand in (ROOT / "pipe" / "ouroboros_pipe", ROOT / "dist" / "linux" / "ouroboros_pipe"):
        if cand.is_file():
            return cand
    subprocess.run([str(ROOT / "scripts" / "build_pipe_linux.sh")], check=True, capture_output=True, timeout=600)
    return ROOT / "dist" / "linux" / "ouroboros_pipe"


def make_relay(real: Path, abi: int | None) -> Path:
    d = Path(tempfile.mkdtemp(prefix="h067-relay-"))
    p = d / "ouroboros_pipe"
    p.write_text(RELAY.format(python=sys.executable, real=str(real), abi=abi))
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return p


def boot_to_galaxy(game: GodotGame) -> None:
    client = game.client
    deadline = time.monotonic() + BOOT_TIMEOUT_S
    clicked = False
    while time.monotonic() < deadline:
        scene = client.state()["result"].get("scene")
        if scene == MAIN_MENU_SCENE:
            break
        if scene == PRIVACY_MODAL_SCENE and not clicked:
            accept = find_control(client.tree(), "AcceptButton")
            if accept is not None:
                client.click(*control_center(accept))
                clicked = True
        time.sleep(0.5)
    else:
        raise AssertionError("never reached the main menu")
    time.sleep(2.0)
    client.click(*control_center(find_control(client.tree(), "NewGame")))
    wait_for(client, lambda s: s.get("scene") == GALAXY_SCENE, STEP_TIMEOUT_S, label="galaxy")


def galaxy_verdict(game: GodotGame) -> dict:
    """Wait until the galaxy has either loaded a world (qa `owners` non-empty) or shown its ErrorPanel, then return
    {panel: bool, text: str, loaded: bool}; `text` is the ErrorReason label's text."""
    client = game.client
    deadline = time.monotonic() + LOAD_S
    qa: dict = {}
    while time.monotonic() < deadline:
        qa = client.state()["result"].get("qa", {})
        if qa.get("error_panel") or qa.get("owners"):
            break
        time.sleep(0.5)
    reason = find_control(client.tree(), "ErrorReason")
    return {"panel": bool(qa.get("error_panel")), "text": "" if reason is None else str(reason.get("text", "")), "loaded": bool(qa.get("owners"))}


@pytest.fixture
def play(monkeypatch, real_pipe):
    """play(pipe_path) launches the game with OM_PIPE=pipe_path, walks boot -> NewGame -> galaxy and returns galaxy_verdict()."""
    games: list[GodotGame] = []
    relays: list[Path] = []

    def _play(pipe: Path | str) -> dict:
        monkeypatch.setenv("OM_PIPE", str(pipe))
        g = GodotGame(qa_port=pick_free_port(), seed=1)
        games.append(g)
        g.start()
        g.wait_for_port(timeout=60.0)
        boot_to_galaxy(g)
        return galaxy_verdict(g)

    _play.relay = lambda abi: relays.append(make_relay(real_pipe, abi)) or relays[-1]
    yield _play
    for g in games:
        g.stop()
        shutil.rmtree(g.scratch, ignore_errors=True)
    for r in relays:
        shutil.rmtree(r.parent, ignore_errors=True)


# ---------------------------------------------------------------- positive controls (green today)

def test_control_header_abi_and_constant_scanner():
    """Positive control for the constant test (H-067 Tests: "the GDScript constant equals `OM_ABI_VERSION` in `csrc/ouroboros_sim.h`"): the header
    parser reads the live value (an int >= 1; 9 on the built tree), and the scanner finds a planted constant in the spellings the builder may
    write while ignoring a comment, an unrelated constant and a var."""
    assert header_abi() >= 1
    d = Path(tempfile.mkdtemp(prefix="h067-scan-"))
    try:
        f = d / "x.gd"
        f.write_text("const EXPECTED_PIPE_ABI := 9\nconst OTHER_ABI: int = 7 # why\n# const FAKE_ABI := 1\nconst LIMIT := 4\nconst ABILITY_MAX := 3\nvar abi := 5\n")
        assert [v for _, v in gdscript_abi_constants([f])] == [9, 7]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_control_missing_pipe_shows_text_in_the_error_panel(play):
    """Positive control for the ErrorPanel detector (H-067 Tests: "a stub pipe reporting a wrong abi gives the ErrorPanel text with both numbers"):
    with OM_PIPE pointing at nothing, today's galaxy shows its ErrorPanel and `galaxy_verdict` reads the label text `pipe binary missing`
    (autoload/c_bridge.gd open_session). Proves the detector can see a panel and its text, so a red below is the missing check, not the harness."""
    v = play("/nonexistent/h067/ouroboros_pipe")
    assert v["panel"], "no ErrorPanel for a missing pipe: %r" % (v,)
    assert "pipe binary missing" in v["text"], v


def test_matching_abi_shows_no_error(play):
    """H-067 Tests control: "a matching abi shows no error". The relay forwards the real hello (abi == OM_ABI_VERSION) untouched; the galaxy loads
    a world and shows no ErrorPanel. Green today and after the change."""
    v = play(play.relay(None))
    assert v["loaded"] and not v["panel"], "matching abi must load the galaxy with no ErrorPanel: %r" % (v,)
    assert v["text"] == "" or "out of date" not in v["text"], v


# ---------------------------------------------------------------- the feature (red today)

@pytest.mark.parametrize("wrong", [3, 10])
def test_wrong_abi_shows_the_stale_pipe_text_with_both_numbers(play, wrong):
    """H-067 Tests: "a stub pipe reporting a wrong abi gives the ErrorPanel text with both numbers". Change part 2: the ErrorPanel text is
    `pipe binary is out of date (abi <n>, expected <m>): run scripts/setup_editor.sh`, n the pipe's abi, m the client's. An older (3) and a newer
    (10) pipe both refuse; m is read from the C header so the client constant and this test move together."""
    expected = header_abi()
    assert wrong != expected
    v = play(play.relay(wrong))
    assert v["panel"], "H-067: abi %d against expected %d shows no ErrorPanel (the stale pipe is not refused): %r" % (wrong, expected, v)
    assert v["text"] == STALE_TEXT % (wrong, expected), "H-067: ErrorPanel text %r, wanted %r" % (v["text"], STALE_TEXT % (wrong, expected))


def test_gdscript_abi_constant_equals_the_header():
    """H-067 Tests: "the GDScript constant equals `OM_ABI_VERSION` in `csrc/ouroboros_sim.h`". Change part 2: "The expected value lives in ONE GDScript
    constant ... so a header bump without the client fails the gate." Exactly one `const ...ABI... := <int>` under autoload/ and scenes/, and it
    equals the header's value. (The builder says which file; the scan covers both trees.)"""
    found = gdscript_abi_constants(client_gd_files())
    assert len(found) == 1, "H-067: wanted exactly one GDScript abi constant under autoload/ and scenes/, found %r" % (found,)
    where, value = found[0]
    assert value == header_abi(), "H-067: %s = %d but OM_ABI_VERSION = %d" % (where, value, header_abi())
