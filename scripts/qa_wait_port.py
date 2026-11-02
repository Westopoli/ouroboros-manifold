#!/usr/bin/env python3
"""Wait until a QA daemon port is really listening.

A connect to a closed 127.0.0.1:P with P in the ephemeral range can be given source
port P and connect to itself (TCP simultaneous open); a naive poller takes that for a
game that is up. listening() refuses it.

See also: docs/stories/H-068.md, docs/stories/H-066.md (the same fix in daemon_client.wait_for_port)

Usage: python3 scripts/qa_wait_port.py PORT [TIMEOUT | --timeout S]   (default 60)
Prints "PORT READY <port>" and exits 0, or "PORT TIMEOUT <port>" and exits 1; bad arguments exit 2.
"""
import socket
import sys
import time


def listening(port):
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=1)
    except OSError:
        return False
    try:
        return s.getsockname() != s.getpeername()
    except OSError:
        return False
    finally:
        s.close()


def main(argv):
    try:
        port, timeout, seen_timeout = None, 60.0, False
        args = list(argv)
        while args:
            a = args.pop(0)
            if a == "--timeout":
                seen_timeout = True
                timeout = float(args.pop(0))
            elif port is None:
                port = int(a)
            elif not seen_timeout:
                timeout, seen_timeout = float(a), True
            else:
                raise ValueError(a)
        if port is None:
            raise ValueError("port")
    except (ValueError, IndexError):
        print("usage: qa_wait_port.py PORT [TIMEOUT | --timeout S]", file=sys.stderr)
        return 2
    deadline = time.monotonic() + timeout
    while True:
        if listening(port):
            print("PORT READY %d" % port)
            return 0
        if time.monotonic() >= deadline:
            print("PORT TIMEOUT %d" % port)
            return 1
        time.sleep(0.25)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
