"""T2g-2: `load` restores the world's tick, and the snapshot that answers it reports it.

Found while wiring the load-game screen (docs/architecture.md "Save slots (T2g-2
rulings)"): the pipe kept its own tick counter, so after a load the snapshot said tick 0
(or whatever the destination world had reached) while the world's state, and its
checksum, were the saved tick's. A client that reads `tick` from the snapshot then
shows the wrong time for every loaded campaign.

Positive control: the tick after a load must differ from the tick the destination
world was at before it, so a pipe that ignores the load's tick cannot pass.
"""
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _read_frames(data):
    out, i = [], 0
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [{"type": "cmd", "name": "quit"}])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    return _read_frames(proc.stdout)


@pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")
def test_load_restores_the_saved_tick_in_the_snapshot():
    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / "slot.omsave")
        seed = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES}
        saved = _run([seed, {"type": "cmd", "name": "step", "n": 10},
                      {"type": "cmd", "name": "save", "path": path}])
        assert any(f["type"] == "ack" and f["name"] == "save" and f["tick"] == 10 for f in saved)

        fresh = _run([seed, {"type": "cmd", "name": "step", "n": 3},
                      {"type": "cmd", "name": "load", "path": path}, {"type": "cmd", "name": "snapshot"}])
        snaps = [f for f in fresh if f["type"] == "snapshot"]
        assert len(snaps) == 2, "load and snapshot should each answer one snapshot frame, got %r" % [f["type"] for f in fresh]
        for snap in snaps:
            assert snap["tick"] == 10, "snapshot tick after loading a tick-10 save into a tick-3 world = %s" % snap["tick"]

        direct = _run([seed, {"type": "cmd", "name": "step", "n": 10}, {"type": "cmd", "name": "snapshot"}])
        want = [f for f in direct if f["type"] == "snapshot"][-1]["checksum"]
        assert snaps[-1]["checksum"] == want, "loaded world's checksum differs from the world that was saved"
