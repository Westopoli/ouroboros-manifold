"""H-066 qa-port-unique: two gates running at the same time never play on each
other's game. Hermetic: a scratch HOME (so the push root <HOME>/Projects/om-push
is scratch), a fake godot/xvfb-run on PATH (qa_port_fakes.py), a decoy foreign
listener in another session. No real Godot, no display.

The scope numbers (1)-(5) are the Architect's H-066 scope, 2026-11-02:
(1) pick_free_port: per-port flock on <push root>/tmp/qa_ports/<port>.lock held
for the process's life, bind probe, random order over 47500-47599, none free ->
`QA PORT REFUSED no free port`. (2) after wait_for_port, the pid owning the port
must be in the Popen's process group, else `QA PORT FOREIGN <port>`, stop, new
port, relaunch, 3 tries, then raise. (3) setup that raises leaves no game running.
(4) teardown waits for exit and a free port before the lock is released.
(5) early exit or stderr `cannot listen`: same path as (2).
Entry points are the existing sequence the fixtures use:
pick_free_port(); GodotGame(qa_port=...); .start(); .wait_for_port(timeout=...).
"""
from __future__ import annotations

import fcntl
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daemon_client  # noqa: E402
import qa_port_fakes as fk  # noqa: E402
from daemon_client import GodotGame, pick_free_port  # noqa: E402

LO, HI = 47500, 47599
HERE = Path(__file__).resolve().parent
WAIT_S = 6.0


def lock_path(home: Path, port: int) -> Path:
    return home / "Projects" / "om-push" / "tmp" / "qa_ports" / ("%d.lock" % port)


def lock_free(home: Path, port: int) -> bool:
    p = lock_path(home, port)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(p), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False
    finally:
        os.close(fd)


def bindable(port: int) -> bool:
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


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
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    games = []
    ns = type("Env", (), {})()
    ns.home, ns.state, ns.games = home, state, games

    def plan(p: str) -> None:
        monkeypatch.setenv("FAKE_GODOT_PLAN", p)
    ns.plan = plan

    def new_game() -> GodotGame:
        g = GodotGame(qa_port=pick_free_port(), seed=1)
        games.append(g)
        return g
    ns.new_game = new_game
    plan("listen")
    yield ns
    for g in games:
        g.stop()
    for port, pid, _ in fk.launches(state):
        fk.kill_group(pid)
    for pid in fk.decoy_pids(state):
        fk.kill_group(pid)


def run_picker_procs(home: Path, body: str, n: int = 8) -> list[str]:
    """n processes started together; each runs `body` (which prints one token),
    then holds its process open until stdin closes. Returns the n tokens."""
    code = (
        "import os,sys,time,random\n"
        "sys.path.insert(0, %r)\n"
        "while not os.path.exists(%r): time.sleep(0.01)\n"
        "random.seed(20261102)\n"
        "%s\n"
        "sys.stdout.flush()\n"
        "sys.stdin.read()\n"
    ) % (str(HERE), str(home / "go"), body)
    penv = dict(os.environ, HOME=str(home))
    procs = [subprocess.Popen([sys.executable, "-c", code], env=penv, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, text=True) for _ in range(n)]
    try:
        time.sleep(0.5)
        (home / "go").write_text("go")
        return [p.stdout.readline().strip() for p in procs]
    finally:
        for p in procs:
            p.stdin.close()
        for p in procs:
            p.wait(timeout=10)


OLD_PICKER = (
    "import socket\n"
    "def old():\n"
    "    for _ in range(50):\n"
    "        port = random.randint(47500, 47599)\n"
    "        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    "        try:\n"
    "            s.bind(('127.0.0.1', port)); s.close(); return port\n"
    "        except OSError:\n"
    "            s.close()\n"
    "print(old())"
)


# --- (1) unique picks ---------------------------------------------------------

def test_control_old_picker_collides(env):
    """CONTROL (H-066 scope 1): the old bind-and-close picker, run by eight
    processes with the same seed, returns the same port in at least two."""
    ports = run_picker_procs(env.home, OLD_PICKER)
    assert len(ports) - len(set(ports)) >= 1, ports


def test_scope1_same_seed_distinct_ports(env):
    """H-066 scope 1: 'N concurrent processes with the same random seed return
    distinct ports.'"""
    ports = run_picker_procs(env.home, "import daemon_client\nprint(daemon_client.pick_free_port())")
    assert all(p.isdigit() for p in ports), ports
    assert len(set(ports)) == 8, ports
    assert all(LO <= int(p) <= HI for p in ports), ports


def test_scope1_lock_file_per_port(env):
    """H-066 scope 1: 'per-port non-blocking flock on <push root>/tmp/qa_ports/<port>.lock
    held for the process's life'."""
    port = pick_free_port()
    assert lock_path(env.home, port).exists()
    assert not lock_free(env.home, port), "the picked port's lock must stay held"


def test_scope1_refused_when_all_locked(env):
    """H-066 scope 1: 'none free prints `QA PORT REFUSED no free port`'. The test
    holds all 100 locks."""
    fds = []
    try:
        for port in range(LO, HI + 1):
            assert lock_free(env.home, port)  # creates the file; control: lockable now
            p = lock_path(env.home, port)
            fd = os.open(str(p), os.O_RDWR)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fds.append(fd)
        with pytest.raises(Exception) as ei:
            pick_free_port()
        assert "QA PORT REFUSED no free port" in str(ei.value)
    finally:
        for fd in fds:
            os.close(fd)


# --- (2) identity check -------------------------------------------------------

def start_and_wait(g: GodotGame, timeout: float = WAIT_S) -> None:
    g.start()
    g.wait_for_port(timeout=timeout)


def test_control_no_decoy_no_retry(env):
    """CONTROL (H-066 scope 2): a game that listens normally is launched once and
    answers on its port."""
    env.plan("listen")
    g = env.new_game()
    start_and_wait(g)
    ls = fk.launches(env.state)
    assert len(ls) == 1 and ls[0][0] == g.qa_port
    assert fk.alive(ls[0][1])


def test_scope2_foreign_listener_detected_and_retried(env, capfd):
    """H-066 scope 2: 'otherwise print `QA PORT FOREIGN <port>`, stop the game,
    pick another port and relaunch'."""
    env.plan("decoy,listen")
    g = env.new_game()
    start_and_wait(g)
    ls = fk.launches(env.state)
    assert len(ls) == 2, ls
    first, second = ls
    out = capfd.readouterr()
    assert "QA PORT FOREIGN %d" % first[0] in out.out + out.err
    assert not fk.alive(first[1]), "the game that met a foreign listener must be stopped"
    assert second[0] != first[0]
    assert fk.alive(second[1])
    assert g.qa_port == second[0] and g.client.port == second[0]
    with socket.create_connection(("127.0.0.1", second[0]), timeout=2):
        pass


def test_scope2_three_foreign_in_a_row_raise(env):
    """H-066 scope 2: 'up to 3 tries, then raise'."""
    env.plan("decoy")
    g = env.new_game()
    with pytest.raises(Exception):
        start_and_wait(g)
    ls = fk.launches(env.state)
    assert len(ls) == 3, ls
    assert len({p for p, _, _ in ls}) == 3
    assert not any(fk.alive(pid) for _, pid, _ in ls)


# --- (3) setup that raises leaves nothing running ------------------------------

def test_control_leak_detector(env):
    """CONTROL (H-066 scope 3): the leak check sees a live fake game and then a
    dead one, so 'dead afterwards' below means something."""
    env.plan("never")
    g = env.new_game()
    g.start()
    time.sleep(0.5)
    pid = fk.launches(env.state)[0][1]
    assert fk.alive(pid)
    g.stop()
    assert not fk.alive(pid)


def test_scope3_setup_raise_leaves_no_game(env):
    """H-066 scope 3: 'the fixture stops the game when setup raises'. A game that
    never listens makes wait_for_port raise; with no stop() called by the caller
    the fake godot must be dead afterwards."""
    env.plan("never")
    g = env.new_game()
    g.start()
    with pytest.raises(Exception):
        g.wait_for_port(timeout=2.0)
    pids = [pid for _, pid, _ in fk.launches(env.state)]
    assert pids
    time.sleep(0.5)
    assert not any(fk.alive(p) for p in pids), "the failed setup leaked a game"


# --- (4) teardown ordering -----------------------------------------------------

def test_scope4_teardown_waits_before_releasing_lock(env):
    """H-066 scope 4: 'teardown waits for process exit (and the port to be free)
    before the lock is released': the first instant a second picker can take the
    port's lock, the game is dead and the port binds; and the lock is released."""
    env.plan("listen")
    g = env.new_game()
    start_and_wait(g)
    port, pid, _ = fk.launches(env.state)[0]
    assert not lock_free(env.home, port), "lock must be held while the game runs"
    seen = {}

    def watcher():
        while "t" not in seen:
            if lock_free(env.home, port):
                seen["t"] = (fk.alive(pid), bindable(port))
            else:
                time.sleep(0.0005)
    th = threading.Thread(target=watcher)
    th.start()
    g.stop()
    th.join(timeout=10)
    assert "t" in seen, "the lock was never released after stop()"
    assert seen["t"] == (False, True), "lock released while alive=%s bindable=%s" % seen["t"]


# --- (5) early exit / cannot listen --------------------------------------------

@pytest.mark.parametrize("mode", ["cannot_listen_alive", "cannot_listen_exit", "early_exit"])
def test_scope5_failed_listen_takes_retry_path(env, mode):
    """H-066 scope 5: 'if Godot exits early or its stderr holds `cannot listen`,
    same path as (2): stop, new port, retry.'"""
    env.plan(mode + ",listen")
    g = env.new_game()
    start_and_wait(g, timeout=5.0)
    ls = fk.launches(env.state)
    assert len(ls) == 2, ls
    assert not fk.alive(ls[0][1])
    assert ls[1][0] != ls[0][0] and fk.alive(ls[1][1])
    assert g.qa_port == ls[1][0]
