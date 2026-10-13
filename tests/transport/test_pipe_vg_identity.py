"""VG K-a identity (spec section 1, K-a gate): on a fixture with no deaths, the delta stream
reconstructs, tick by tick and in the final full frame, to the same unit views as main's pipe once
the keys K-a adds are stripped and `state` and `tier` are zeroed.

Main's pipe is the binary named by OM_MAIN_PIPE (a build of origin/main); the test skips without it."""
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NEW = ROOT / "pipe/ouroboros_pipe"
MAIN = Path(os.environ["OM_MAIN_PIPE"]) if os.environ.get("OM_MAIN_PIPE") else None
SEED, TICKS = 8, 310
NEW_KEYS = {"acd", "tl", "ld", "sight"}
CMDS = [
    {"type": "cmd", "name": "set_seed", "seed": SEED, "n_regions": 80, "features": [0, 1, 2, 3, 4, 5, 6, 7]},
    # TD-VG-D-11: era_kind 1 (ground), which lane D leaves unchanged; the space era differs by design (field, anchor spawns, objective pocket).
    {"type": "cmd", "name": "mission_start", "faction": 0, "era_kind": 1},
    {"type": "cmd", "name": "mission_begin"},
] + [{"type": "cmd", "name": "tactical_step", "n": 1}] * TICKS + [
    {"type": "cmd", "name": "tactical_step", "n": 0},
    {"type": "cmd", "name": "quit"},
]

pytestmark = pytest.mark.skipif(not NEW.exists() or MAIN is None or not MAIN.exists(),
                                reason="needs pipe/ouroboros_pipe and OM_MAIN_PIPE (main's build)")


def _frames(pipe):
    body = b"".join(len(b).to_bytes(4, "big") + b for b in (json.dumps(c).encode() for c in CMDS))
    data = subprocess.run([str(pipe)], input=body, capture_output=True, timeout=300).stdout
    out, i = [], 0
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return [f for f in out if f["type"] == "tactical"]


def _views(frames):
    units, views, removed = {}, [], 0
    for f in frames:
        if f["full"]:
            units = {u["id"]: u for u in f["units"]}
        else:
            for i in f["units_removed"]:
                units.pop(i, None)
            removed += len(f["units_removed"])
            for u in f["units_changed"]:
                units[u["id"]] = u
        views.append({i: {k: (0 if k in ("state", "tier") else v) for k, v in u.items() if k not in NEW_KEYS}
                      for i, u in units.items()})
    return views, removed


def test_new_pipe_views_equal_mains_without_the_new_keys():
    new, main = _frames(NEW), _frames(MAIN)
    assert len(new) == len(main) == TICKS + 2
    nv, nr = _views(new)
    mv, mr = _views(main)
    assert nr == 0 and mr == 0, "fixture must be death-free"
    assert nv[-1], "fixture has units"
    for t, (a, b) in enumerate(zip(nv, mv)):
        assert a == b, "views differ at frame %d" % t
    assert new[-1]["full"] and nv[-1] == nv[-2], "final full frame agrees with the delta stream"
