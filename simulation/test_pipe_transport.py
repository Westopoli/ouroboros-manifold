# Checkpoint A — Sim-Side Pipe Transport
# =========================================
# Tests:
#   1. Progress and ready messages arrive as properly framed length-prefix JSON
#   2. logs/sim_stderr.log is created and captures sim output
#   3. Stray print() is intercepted — does not appear as raw bytes in stdout
#   4. Crash handler writes logs/crash_report.txt with correct content and no sensitive paths
#
# Run from the project root:
#   python3 simulation/test_pipe_transport.py

import subprocess
import sys
import os
import json
import struct
import time
import threading
import queue as _queue
import getpass

SIMULATION_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SIMULATION_DIR)
PIPE_TRANSPORT = os.path.join(SIMULATION_DIR, "pipe_transport.py")
CRASH_LOG = os.path.join(PROJECT_ROOT, "logs", "crash_report.txt")
STDERR_LOG = os.path.join(PROJECT_ROOT, "logs", "sim_stderr.log")


def _banner(label):
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print("─" * 60)


def _result(label, passed, detail=""):
    tag = "[PASS]" if passed else "[FAIL]"
    suffix = f"  ← {detail}" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    return passed


def _read_framed_message(pipe) -> dict | None:
    """Read one length-prefixed JSON message from a binary pipe. Returns None on EOF/error."""
    try:
        header = pipe.read(4)
        if len(header) < 4:
            return None
        length = struct.unpack(">I", header)[0]
        if length > 10 * 1024 * 1024:  # sanity cap: 10 MB max message
            return None
        body = pipe.read(length)
        if len(body) < length:
            return None
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def _drain_until_ready(proc, timeout=20.0) -> list[dict]:
    """
    Read framed messages from proc.stdout until a 'ready' message or timeout.
    Returns the list of messages received (including ready if it arrived).
    """
    messages = []
    msg_queue = _queue.Queue()

    def _reader():
        while True:
            msg = _read_framed_message(proc.stdout)
            if msg is None:
                msg_queue.put(None)
                break
            msg_queue.put(msg)

    t = threading.Thread(target=_reader, daemon=True)
    t.start()

    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            msg = msg_queue.get(timeout=min(remaining, 1.0))
            if msg is None:
                break
            messages.append(msg)
            if msg.get("type") == "ready":
                break
        except _queue.Empty:
            break

    return messages


def _spawn(extra_args=None):
    """Spawn pipe_transport.py as a subprocess from the project root."""
    cmd = [sys.executable, PIPE_TRANSPORT] + (extra_args or [])
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,  # captured separately from sim's own log file
        cwd=PROJECT_ROOT,
    )


# ── Test 1: Progress and ready messages ───────────────────────────────────────

def test_progress_and_ready_framing():
    _banner("TEST 1 — Progress and ready messages: proper length-prefix framing")

    proc = _spawn()
    try:
        messages = _drain_until_ready(proc, timeout=20.0)
    finally:
        proc.kill()
        proc.wait()

    progress_msgs = [m for m in messages if m.get("type") == "progress"]
    ready_msgs = [m for m in messages if m.get("type") == "ready"]

    print(f"  total messages received before ready: {len(messages)}")
    for m in messages:
        if m.get("type") == "progress":
            print(f"    progress  step={m.get('step')!r:30s}  pct={m.get('pct')}")
        elif m.get("type") == "ready":
            print(f"    ready     version={m.get('version')!r}")

    _result(
        "at least one progress message received",
        len(progress_msgs) >= 1,
        f"got {len(progress_msgs)}",
    )
    _result(
        "exactly one ready message received",
        len(ready_msgs) == 1,
        f"got {len(ready_msgs)}",
    )

    for m in progress_msgs:
        step = m.get("step")
        pct = m.get("pct")
        _result(
            f"progress[{step!r}] has pct in [0.0, 1.0]",
            isinstance(pct, (int, float)) and 0.0 <= pct <= 1.0,
            f"pct={pct!r}",
        )

    if progress_msgs and ready_msgs:
        last_prog_idx = max(messages.index(m) for m in progress_msgs)
        ready_idx = messages.index(ready_msgs[0])
        _result(
            "all progress messages precede ready",
            last_prog_idx < ready_idx,
            f"last_progress_idx={last_prog_idx}, ready_idx={ready_idx}",
        )

    if ready_msgs:
        rm = ready_msgs[0]
        _result("ready message has 'version' field", "version" in rm, f"keys={list(rm.keys())}")


# ── Test 2: Stderr log created ────────────────────────────────────────────────

def test_stderr_log_created():
    _banner("TEST 2 — logs/sim_stderr.log created and captures sim output")

    if os.path.exists(STDERR_LOG):
        os.remove(STDERR_LOG)

    proc = _spawn()
    try:
        _drain_until_ready(proc, timeout=20.0)
    finally:
        proc.kill()
        proc.wait()

    time.sleep(0.15)  # let the log file flush

    exists = os.path.exists(STDERR_LOG)
    _result("logs/sim_stderr.log exists after sim startup", exists, f"path={STDERR_LOG}")

    if exists:
        with open(STDERR_LOG, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"  log file size  : {len(content)} bytes")
        print(f"  log contents   : {content[:300]!r}")
        _result("log file is not empty", len(content) > 0)
        _result("log contains expected 'ready' entry", "ready" in content.lower())


# ── Test 3: print() interception ─────────────────────────────────────────────

def test_print_interception():
    _banner("TEST 3 — stray print() intercepted: does not corrupt stdout, goes to log")

    if os.path.exists(STDERR_LOG):
        os.remove(STDERR_LOG)

    proc = _spawn(["--test-print"])
    try:
        messages = _drain_until_ready(proc, timeout=20.0)
    finally:
        proc.kill()
        proc.wait()

    ready_arrived = any(m.get("type") == "ready" for m in messages)
    _result(
        "ready message arrived despite print() call (stdout not corrupted)",
        ready_arrived,
        f"messages received: {len(messages)}",
    )

    time.sleep(0.15)

    if os.path.exists(STDERR_LOG):
        with open(STDERR_LOG, "r", encoding="utf-8") as f:
            log_content = f.read()
        intercepted = "debug_intercept_test" in log_content
        _result(
            "intercepted print() text appears in sim_stderr.log",
            intercepted,
            f"log excerpt: {log_content[:300]!r}",
        )
    else:
        _result("intercepted print() text appears in sim_stderr.log", False, "log file not found")


# ── Test 4: Crash handler ─────────────────────────────────────────────────────

def test_crash_handler():
    _banner("TEST 4 — crash handler writes logs/crash_report.txt with correct content")

    if os.path.exists(CRASH_LOG):
        os.remove(CRASH_LOG)

    proc = _spawn(["--crash"])
    try:
        messages = _drain_until_ready(proc, timeout=20.0)
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    finally:
        try:
            proc.kill()
            proc.wait()
        except Exception:
            pass

    ready_before_crash = any(m.get("type") == "ready" for m in messages)
    _result("ready message was sent before crash", ready_before_crash)

    time.sleep(0.3)  # give crash handler time to write the file

    crash_exists = os.path.exists(CRASH_LOG)
    _result("logs/crash_report.txt created", crash_exists, f"path={CRASH_LOG}")

    if not crash_exists:
        return

    with open(CRASH_LOG, "r", encoding="utf-8") as f:
        crash_content = f.read()

    print(f"\n  crash_report.txt contents:")
    for line in crash_content.splitlines():
        print(f"    {line}")
    print()

    # Required fields
    _result("crash report has 'sim_version:' line", "sim_version:" in crash_content)
    _result("crash report has 'os:' line", "os:" in crash_content)
    _result("crash report has 'python:' line", "python:" in crash_content)
    _result("crash report has '--- traceback ---' section", "--- traceback ---" in crash_content)
    _result("crash report traceback contains 'RuntimeError'", "RuntimeError" in crash_content)

    # Security: no absolute paths, no username
    tb_section = crash_content.split("--- traceback ---")[-1] if "--- traceback ---" in crash_content else crash_content
    username = getpass.getuser()
    home = os.path.expanduser("~")

    _result(
        "traceback does not contain home directory path",
        home not in tb_section,
        f"home={home!r}",
    )
    _result(
        "traceback does not contain username",
        username not in tb_section,
        f"username={username!r}",
    )

    # No absolute paths in File "..." lines
    abs_path_lines = [
        line for line in tb_section.splitlines()
        if 'File "' in line and (line.lstrip().startswith('File "/') or line.lstrip().startswith("File \"" + os.sep))
    ]
    _result(
        "traceback File lines have no absolute paths",
        len(abs_path_lines) == 0,
        f"found: {abs_path_lines}",
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n══════════════════════════════════════════════════════════")
    print("  Checkpoint A — Sim-Side Pipe Transport")
    print("══════════════════════════════════════════════════════════")
    print(f"  sim script   : simulation/pipe_transport.py")
    print(f"  project root : {PROJECT_ROOT}")
    print(f"  crash log    : logs/crash_report.txt")
    print(f"  stderr log   : logs/sim_stderr.log")

    test_progress_and_ready_framing()
    test_stderr_log_created()
    test_print_interception()
    test_crash_handler()

    print("\n══════════════════════════════════════════════════════════")
    print("  Checkpoint A complete — review [PASS]/[FAIL] above")
    print("══════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
