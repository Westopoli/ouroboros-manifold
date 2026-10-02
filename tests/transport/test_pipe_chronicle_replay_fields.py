"""G-C3 (A48 item 13): the chronicle frame carries "ownership" and "keyframes".

Contract: docs/architecture.md "chronicle frame". R-056-03 / ALG-45 (ownership
snapshot every 2 ticks, k = 0 pre-jump), R-069-05 (a keyframe at every ownership
change). The sim owns both lists; the client derives none.

Red on main: write_chronicle emits neither field. The test_control_ functions are
positive controls: they prove the snapshots hold real, changing ownership that
agrees with the snapshot frame, so an all-(-1) or constant list cannot pass.
"""
import json
import subprocess
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
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=120)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]


def _jump(seed, ticks, n_regions=80):
    frames = _run([
        {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": n_regions, "features": FEATURES},
        {"type": "cmd", "name": "jump", "ticks": ticks},
    ])
    chron = next((f for f in frames if f.get("type") == "chronicle"), None)
    assert chron is not None, f"no chronicle frame; types={[f.get('type') for f in frames]}"
    snap = [f for f in frames if f.get("type") == "snapshot"][-1]
    return chron, snap


def test_chronicle_frame_has_ownership_timeline():
    chron, _ = _jump(1, 50)
    own = chron.get("ownership")
    assert isinstance(own, dict), f"chronicle frame has no ownership field: keys={sorted(chron)}"
    jump = chron["jump"]
    assert own["stride"] == 2
    assert own["from_tick"] == jump["from_tick"]
    assert own["n_regions"] == 80
    snaps = own["snapshots"]
    assert len(snaps) == (jump["to_tick"] - jump["from_tick"]) // 2 + 1 == 26
    for k, s in enumerate(snaps):
        assert len(s) == 80, f"snapshot {k} has {len(s)} entries"
        assert all(isinstance(v, int) and v >= -1 for v in s), f"snapshot {k}: {s}"


def test_control_ownership_snapshots_are_real_and_match_the_world():
    """Positive control: some seed shows a region changing owner inside the jump,
    snapshot 0 differs from the last, and the last snapshot is the post-jump owner
    list the snapshot frame reports."""
    changed = False
    for seed in (1, 2, 3, 4):
        chron, snap = _jump(seed, 100)
        own = chron.get("ownership")
        assert isinstance(own, dict), "chronicle frame has no ownership field"
        snaps = own["snapshots"]
        assert len(snaps) == 51
        assert any(v >= 0 for v in snaps[0]), "snapshot 0 holds no owned region"
        world_owners = [r["owner"] for r in sorted(snap["regions"], key=lambda r: r["i"])]
        assert snaps[-1] == world_owners, f"seed {seed}: last snapshot is not the post-jump world"
        changed = changed or snaps[0] != snaps[-1]
    assert changed, "no seed changed ownership across a 100-tick jump (fixture too thin)"


def test_chronicle_frame_has_keyframes():
    chron, _ = _jump(1, 50)
    kfs = chron.get("keyframes")
    assert isinstance(kfs, list), f"chronicle frame has no keyframes field: keys={sorted(chron)}"
    assert all(isinstance(t, int) for t in kfs)
    jump = chron["jump"]
    assert all(jump["from_tick"] <= t <= jump["to_tick"] for t in kfs), kfs


def test_control_every_ownership_change_has_a_keyframe():
    """Positive control for R-069-05: wherever ownership changed between snapshot 0
    and the last snapshot, the frame lists at least one keyframe (a stub returning
    [] fails); a world with no change is allowed an empty list."""
    exercised = False
    for seed in (1, 2, 3, 4):
        chron, _ = _jump(seed, 100)
        own, kfs = chron.get("ownership"), chron.get("keyframes")
        assert isinstance(own, dict) and isinstance(kfs, list), "ownership or keyframes missing"
        n_changed = sum(1 for a, b in zip(own["snapshots"][0], own["snapshots"][-1]) if a != b)
        if n_changed:
            exercised = True
            assert kfs, f"seed {seed}: {n_changed} regions changed owner but keyframes is empty"
    assert exercised, "no seed changed ownership (fixture too thin)"
