"""
Checkpoint A — Socket Server Scaffold
======================================
Verifies the bare socket_server.py skeleton:
  - server starts and binds to the configured port
  - client connects and receives a {"type": "hello"} packet
  - server closes the connection cleanly (no zombie sockets)
  - server can be restarted on the same port (no port-reuse errors)

Output legend
  [PASS]  assertion met
  [FAIL]  assertion failed — detail on same line
"""

import asyncio
import json
import sys
import threading
import time

sys.path.insert(0, ".")
import config
from socket_server import SocketServer

# ── helpers ──────────────────────────────────────────────────────────────────

TEST_PORT = 18765   # distinct from the default so this test never stomps a live server

def _banner(label):
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print('─' * 60)

def _result(label, passed, detail=""):
    tag = "[PASS]" if passed else "[FAIL]"
    suffix = f"  ← {detail}" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    return passed

# ── server lifecycle helpers ──────────────────────────────────────────────────

class _ServerThread:
    """Runs SocketServer in a background thread so the test can drive it."""

    def __init__(self, port):
        self._server = SocketServer(host="127.0.0.1", port=port)
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._ready = threading.Event()

    def _run(self):
        async def _main():
            self._ready.set()
            await self._server.start()

        self._loop.run_until_complete(_main())

    def start(self):
        self._thread.start()
        self._ready.wait(timeout=2.0)
        time.sleep(0.05)   # give asyncio a moment to bind

    def stop(self):
        self._server.stop()
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=2.0)


async def _connect_and_read(port, timeout_sec=2.0):
    """Opens a raw TCP connection, reads one newline-delimited JSON line, closes."""
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection("127.0.0.1", port), timeout=timeout_sec
    )
    addr = writer.get_extra_info("peername")
    raw = await asyncio.wait_for(reader.readline(), timeout=timeout_sec)
    writer.close()
    try:
        await writer.wait_closed()
    except Exception:
        pass
    return addr, raw.decode().strip()


# ── tests ─────────────────────────────────────────────────────────────────────

def test_hello_packet():
    _banner("TEST 1 — connect, receive hello packet, disconnect cleanly")

    srv = _ServerThread(TEST_PORT)
    srv.start()

    try:
        addr, raw = asyncio.run(_connect_and_read(TEST_PORT))

        print(f"  server addr  : {addr}")
        print(f"  raw packet   : {raw!r}")

        # parse
        try:
            packet = json.loads(raw)
            parsed_ok = True
        except json.JSONDecodeError as exc:
            packet = {}
            parsed_ok = _result("packet is valid JSON", False, str(exc))

        if parsed_ok:
            _result("packet is valid JSON", True)

        _result(
            'packet type == "hello"',
            packet.get("type") == "hello",
            f"got {packet.get('type')!r}",
        )

    except Exception as exc:
        _result("connection + hello succeeded", False, str(exc))
    finally:
        srv.stop()


def test_no_zombie_sockets():
    _banner("TEST 2 — no zombie sockets: start, stop, restart on same port")

    for attempt in (1, 2):
        srv = _ServerThread(TEST_PORT)
        srv.start()
        try:
            _, raw = asyncio.run(_connect_and_read(TEST_PORT))
            packet = json.loads(raw)
            ok = packet.get("type") == "hello"
            _result(f"attempt {attempt}: hello received", ok)
        except Exception as exc:
            _result(f"attempt {attempt}: hello received", False, str(exc))
            break
        finally:
            srv.stop()
        time.sleep(0.1)   # brief pause between attempts


def test_reconnect():
    _banner("TEST 3 — multiple sequential client connections to the same server")

    srv = _ServerThread(TEST_PORT)
    srv.start()

    results = []
    try:
        for i in range(3):
            try:
                _, raw = asyncio.run(_connect_and_read(TEST_PORT))
                packet = json.loads(raw)
                results.append(packet.get("type") == "hello")
            except Exception as exc:
                results.append(False)
                print(f"    connection {i+1} error: {exc}")

        for i, ok in enumerate(results, 1):
            _result(f"connection {i} hello received", ok)

    finally:
        srv.stop()


# ── summary ───────────────────────────────────────────────────────────────────

def main():
    print("\n══════════════════════════════════════════════════════════")
    print("  Checkpoint A — Socket Server Scaffold")
    print("══════════════════════════════════════════════════════════")
    print(f"  server config: {config.SOCKET_HOST}:{config.SOCKET_PORT}")
    print(f"  test port    : {TEST_PORT}  (isolated from live server)")

    test_hello_packet()
    test_no_zombie_sockets()
    test_reconnect()

    print("\n══════════════════════════════════════════════════════════")
    print("  Checkpoint A complete — review [PASS]/[FAIL] above")
    print("══════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
