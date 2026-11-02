"""H-068 qa-pollers-self-connect: "A proof run never mistakes a socket talking to
itself for a game that is up." Hermetic: scratch HOME (so the push root is scratch),
fake godot/xvfb-run on PATH (tests/qa/desktop/qa_port_fakes.py), no real Godot, no
display. Items map to docs/stories/H-068.md "Tests" 1-6; the part-6 retry test
also covers the story's "Change" part 6.

Open entry-point questions are reported, not pinned: this file uses only the names
the story gives (`listening(port)`, CLI `python3 scripts/qa_wait_port.py PORT [timeout]`
printing `PORT READY <port>` / `PORT TIMEOUT <port>`, exit 0 / 1) and, for the
module, `import socket` as `socket` (the self-connect test swaps `qa_wait_port.socket`).
"""
from __future__ import annotations

import importlib.util
import os
import re
import socket
import subprocess
import sys
import textwrap
import time
import types
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DESKTOP = REPO / "tests" / "qa" / "desktop"
sys.path.insert(0, str(DESKTOP))
import qa_port_fakes as fk  # noqa: E402

WAIT_PY = REPO / "scripts" / "qa_wait_port.py"


def load_wait():
    assert WAIT_PY.exists(), "scripts/qa_wait_port.py does not exist (H-068 Change part 1)"
    spec = importlib.util.spec_from_file_location("qa_wait_port_under_test", WAIT_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def quiet_port() -> int:
    """A bindable port below the ephemeral range (32768-60999), so a closed-port connect cannot self-connect by luck."""
    for p in range(21000, 30000):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p))
            return p
        except OSError:
            continue
        finally:
            s.close()
    raise RuntimeError("no quiet port")


@pytest.fixture
def listener():
    port = quiet_port()
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
    s.listen(8)
    yield port
    s.close()


# ---- Test 1: listening(P) False on a self-connect; control: a real listener is True ----

def _self_connected(port: int) -> socket.socket:
    s = socket.socket()
    s.bind(("127.0.0.1", port))
    s.connect(("127.0.0.1", port))
    return s


def test_control_self_connect_premise_holds():
    """Control (green today): a socket bound to (127.0.0.1,P) and connected to the same P
    really is a self-connect on this kernel (getsockname()==getpeername()), so the
    tests below are about the right thing."""
    p = quiet_port()
    s = _self_connected(p)
    try:
        assert s.getsockname() == s.getpeername()
    finally:
        s.close()


def test_h068_1_listening_true_for_real_listener(listener):
    """H-068 Tests 1 (control): "a normal listener on P gives True"."""
    assert load_wait().listening(listener) is True


def test_h068_1_listening_false_when_nothing_listens():
    """H-068 Change 1: listening(port) "returns True only for a connect whose getsockname() differs from its getpeername()"; nothing listening is not True."""
    assert load_wait().listening(quiet_port()) is False


def test_h068_1_listening_false_for_story_literal_self_connect():
    """H-068 Tests 1: "A socket bound to (127.0.0.1, P) and connected to (127.0.0.1, P) makes listening(P) False"."""
    mod = load_wait()
    p = quiet_port()
    s = _self_connected(p)
    try:
        assert mod.listening(p) is False
    finally:
        s.close()


def test_h068_1_listening_false_when_the_connect_itself_self_connects():
    """H-068 Tests 1, deterministic form: the story's literal case only makes a
    third socket's connect be refused, which a naive poller also rejects. Here the
    module's own connect is made to self-connect (bind source port P, connect to P:
    a real kernel simultaneous open), the exact case a naive poller takes for a game."""
    mod = load_wait()
    p = quiet_port()
    real = socket

    class SelfSock(real.socket):
        def connect(self, addr):
            self.bind(("127.0.0.1", p))
            super().connect(addr)

    def fake_create_connection(addr, timeout=None, *a, **k):
        s = SelfSock()
        if timeout is not None:
            s.settimeout(timeout)
        s.connect(addr)
        return s

    shim = types.SimpleNamespace(**{k: getattr(real, k) for k in dir(real) if not k.startswith("__")})
    shim.socket = SelfSock
    shim.create_connection = fake_create_connection
    mod.socket = shim
    assert mod.listening(p) is False


# ---- Test 2: the CLI ----

def run_cli(*args, timeout=20):
    return subprocess.run([sys.executable, str(WAIT_PY), *map(str, args)],
                          capture_output=True, text=True, timeout=timeout)


def test_h068_2_cli_ready_for_listener(listener):
    """H-068 Tests 2: "The CLI prints PORT READY and exits 0 for a listener"."""
    assert WAIT_PY.exists(), "scripts/qa_wait_port.py does not exist (H-068 Change part 1)"
    r = run_cli(listener, 5)
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    assert "PORT READY %d" % listener in r.stdout


def test_h068_2_cli_timeout_for_unheld_port():
    """H-068 Tests 2: "prints PORT TIMEOUT and exits 1 for a port nobody holds (timeout 1 s)"."""
    assert WAIT_PY.exists(), "scripts/qa_wait_port.py does not exist (H-068 Change part 1)"
    p = quiet_port()
    t0 = time.monotonic()
    r = run_cli(p, 1)
    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
    assert "PORT TIMEOUT %d" % p in r.stdout
    assert time.monotonic() - t0 < 10


# ---- Test 3: the shells call the helper and lose their embedded polling loops ----

# Base (origin/main 2026-11-02) fragments, held as fixtures so the detectors have a positive control.
BASE_HARNESS_LOOP = textwrap.dedent('''\
    connected = False
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                connected = True
                break
        except OSError:
            time.sleep(0.25)
''')
BASE_PLAY_QA_SCENE = textwrap.dedent('''\
    qa_scene() {
      python3 -c '
    import json,socket,sys
    s=socket.create_connection(("127.0.0.1",int(sys.argv[1])),timeout=10)
    s.sendall(b"[\\"state\\"]\\n"); b=b""
    while not b.endswith(b"\\n"): b+=s.recv(65536)
    print(json.loads(b)["result"]["scene"])' "$1" 2>/dev/null
    }
''')
HARNESS_POLL_RE = re.compile(r"while time\.monotonic\(\) < deadline:\s*\n\s*try:\s*\n\s*with socket\.create_connection")


def qa_scene_body(text: str) -> str:
    m = re.search(r"^qa_scene\(\) \{.*?^\}", text, re.S | re.M)
    assert m, "qa_scene function not found in play.sh"
    return m.group(0)


def test_control_base_fixtures_trip_the_detectors():
    """Control (green today): the detectors below fire on the base fragments."""
    assert HARNESS_POLL_RE.search(BASE_HARNESS_LOOP)
    assert "qa_wait_port" not in qa_scene_body(BASE_PLAY_QA_SCENE)
    live_play = (REPO / "scripts" / "play.sh").read_text()
    assert "create_connection" in qa_scene_body(live_play) or "qa_wait_port" in qa_scene_body(live_play)


def test_h068_3_qa_harness_calls_helper_and_has_no_polling_loop():
    """H-068 Tests 3: "scripts/qa_harness.sh ... call scripts/qa_wait_port.py and no longer contain their embedded create_connection polling loops"."""
    text = (REPO / "scripts" / "qa_harness.sh").read_text()
    assert "qa_wait_port.py" in text, "qa_harness.sh does not call scripts/qa_wait_port.py"
    assert not HARNESS_POLL_RE.search(text), "qa_harness.sh still has the embedded create_connection polling loop"


def test_h068_3_play_sh_qa_scene_asks_helper_before_its_request():
    """H-068 Change 2: "qa_scene in play.sh asks the helper before it sends its state request"."""
    text = (REPO / "scripts" / "play.sh").read_text()
    body = qa_scene_body(text)
    assert "qa_wait_port.py" in body, "play.sh qa_scene does not call scripts/qa_wait_port.py"
    assert body.index("qa_wait_port.py") < body.index("create_connection"), "helper must come before the request"


# ---- Test 4: test_gate_userdir.py off the fixed ports ----

FIXED_PORTS_RE = re.compile(r"\b4759[0-3]\b")


def test_control_fixed_port_detector_fires_on_old_lines():
    """Control (green today): the detector matches the base lines of test_gate_userdir.py."""
    old = "def _make_game(port: int = 47590):\n    g1 = _make_game(47591)\n    g2 = _make_game(47592)\n    g = _make_game(47593)\n"
    assert len(FIXED_PORTS_RE.findall(old)) == 4


def test_h068_4_gate_userdir_has_no_fixed_ports():
    """H-068 Tests 4: "tests/specfactory/test_gate_userdir.py no longer names the literal ports 47590 to 47593"."""
    text = (REPO / "tests" / "specfactory" / "test_gate_userdir.py").read_text()
    assert not FIXED_PORTS_RE.search(text), "still names a fixed port: %s" % FIXED_PORTS_RE.findall(text)
    assert "pick_free_port" in text, "does not use pick_free_port"


# ---- Tests 5 and 6: daemon_client with the fake game ----

@pytest.fixture
def env(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    fk.install(tmp_path / "bin")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PATH", str(tmp_path / "bin") + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("FAKE_GODOT_STATE", str(state))
    monkeypatch.setenv("FAKE_GODOT_PLAN", "listen")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    ns = types.SimpleNamespace(home=home, state=state, games=[])
    yield ns
    for g in ns.games:
        g.stop()
    for _, pid, _ in fk.launches(state):
        fk.kill_group(pid)
    for pid in fk.decoy_pids(state):
        fk.kill_group(pid)


CHILD = '''
import sys
sys.path.insert(0, %(desktop)r)
from daemon_client import GodotGame, pick_free_port
g = GodotGame(qa_port=pick_free_port(), seed=1)
g.start()
g.wait_for_port(timeout=20)
mode = sys.argv[1]
if mode == "stop":
    g.stop()
elif mode == "raise":
    raise RuntimeError("first state() call failed")
'''


def child_leaves_game(env, mode: str) -> bool:
    """Runs a child python that starts the fake game, then ends per `mode`; True when the fake game is still alive after the child is gone."""
    r = subprocess.run([sys.executable, "-c", CHILD % {"desktop": str(DESKTOP)}, mode],
                       capture_output=True, text=True, timeout=40)
    ls = fk.launches(env.state)
    assert len(ls) == 1, (ls, r.stderr[-400:])
    pid = ls[0][1]
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and fk.alive(pid):
        time.sleep(0.1)
    return fk.alive(pid)


def test_control_explicit_stop_leaves_no_game(env):
    """Control (green today): a child that stops its game leaves no process, so a survivor in the tests below is a missing at-exit stop."""
    assert child_leaves_game(env, "stop") is False


def test_control_detector_sees_a_survivor(env):
    """Control (green today): the liveness detector reports a fake game that nobody stops."""
    port = quiet_port()
    p = subprocess.Popen([str(Path(env.home).parent / "bin" / "godot"), "--qa-port", str(port)],
                         start_new_session=True, env=dict(os.environ))
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not fk.launches(env.state):
            time.sleep(0.05)
        assert fk.alive(p.pid)
    finally:
        fk.kill_group(p.pid)
        p.wait()


@pytest.mark.parametrize("mode", ["exit", "raise"])
def test_h068_5_game_does_not_outlive_its_process(env, mode):
    """H-068 Change 5: "GodotGame.start ... registers an at-exit stop (atexit), so a game cannot outlive its pytest process, whatever a fixture does"."""
    assert child_leaves_game(env, mode) is False, "fake game survived its parent process (%s)" % mode


def test_h068_6_retry_stays_inside_callers_range(env, monkeypatch):
    """H-068 Change 6: "The retry inside wait_for_port draws from the lo/hi range the caller gave pick_free_port"."""
    import daemon_client as dc
    monkeypatch.setenv("FAKE_GODOT_PLAN", "decoy,listen")
    lo, hi = 47570, 47571
    g = dc.GodotGame(qa_port=dc.pick_free_port(lo, hi), seed=1)
    env.games.append(g)
    g.start()
    g.wait_for_port(timeout=20)
    ports = [p for p, _, _ in fk.launches(env.state)]
    assert len(ports) >= 2, "premise: the foreign listener should force a retry, launches=%r" % ports
    assert all(lo <= p <= hi for p in ports), "retry left [%d,%d]: launches on %r" % (lo, hi, ports)


def test_h068_6_default_range_when_none_given(env, monkeypatch):
    """H-068 Tests 6 (control): "the default range is used when none is given"."""
    import daemon_client as dc
    monkeypatch.setenv("FAKE_GODOT_PLAN", "decoy,listen")
    g = dc.GodotGame(qa_port=dc.pick_free_port(), seed=1)
    env.games.append(g)
    g.start()
    g.wait_for_port(timeout=20)
    ports = [p for p, _, _ in fk.launches(env.state)]
    assert len(ports) >= 2 and all(47500 <= p <= 47599 for p in ports), ports
