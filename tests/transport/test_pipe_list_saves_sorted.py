"""C1 / gap-fix S4: `list_saves` answers slots sorted by slot name.

The sidecar `format_version` (OM_PIPE_SAVE_FORMAT_VERSION) and `chapter`
(om_chapter_get_number) already land (B6). What is still open is the order:
the pipe lists sidecars in readdir order, which differs per filesystem, so the
load screen's slot order is not stable.

Positive control: slots are saved in the order c, a, b and must come back
a, b, c. Ids: S4, R-111-01.
"""
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [{"type": "cmd", "name": "quit"}])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out


def test_s4_list_saves_sorted_by_slot_name():
    with tempfile.TemporaryDirectory() as d:
        names = ["slot_c", "slot_a", "slot_b", "slot_e", "slot_d"]
        cmds = [{"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES}]
        for n in names:
            cmds.append({"type": "cmd", "name": "save", "path": str(Path(d) / (n + ".omsave"))})
        cmds.append({"type": "cmd", "name": "list_saves", "dir": d})
        frames = _run(cmds)
        saves = next((f for f in frames if f.get("type") == "saves"), None)
        assert saves is not None, f"no saves frame; types={[f.get('type') for f in frames]}"
        paths = [s["path"] for s in saves["slots"]]
        assert len(paths) == len(names), f"expected {len(names)} slots, got {paths}"
        assert paths == sorted(paths), f"slots not sorted by name: {[Path(p).name for p in paths]}"
