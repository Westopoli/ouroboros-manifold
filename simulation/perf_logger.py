# Tick-level JSONL logger for the tactical sim. One line per outgoing message
# (snapshot or delta). Read by simulation/perf_report.py. No dependencies —
# safe to import from run_debug_server.py before the socket server starts.

import json
import os
import time


_FH = None
_BUF: list[str] = []
_FLUSH_EVERY = 1
_START_MONOTONIC = 0.0


def start(path: str = "logs/sim_perf.jsonl"):
    global _FH, _BUF, _START_MONOTONIC
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    _FH = open(path, "w", encoding="utf-8", buffering=1)
    _BUF = []
    _START_MONOTONIC = time.monotonic()
    _FH.write(json.dumps({"type": "header", "wall_time": time.time()}) + "\n")


def log(rec: dict):
    if _FH is None:
        return
    rec["t_mono"] = round(time.monotonic() - _START_MONOTONIC, 6)
    _BUF.append(json.dumps(rec))
    if len(_BUF) >= _FLUSH_EVERY:
        flush()


def flush():
    global _BUF
    if _FH and _BUF:
        _FH.write("\n".join(_BUF) + "\n")
        _FH.flush()
        _BUF = []


def close():
    global _FH
    flush()
    if _FH:
        _FH.close()
        _FH = None
