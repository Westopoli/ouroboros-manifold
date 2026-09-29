"""B8-9: chronicle entries after a jump have ticks within the jump window.

After a jump, entries whose cluster has no event ticks (start_tick==0,
end_tick==0 on om_chronicle_cluster -- all REGIONAL/LINEAGE/CONSEQUENCE
clusters are pushed with 0,0; only CHAIN clusters carry actual ticks) must
take the jump window (from_tick, to_tick) instead of 0/0.

Positive control: test is red on unmodified T1-9 base because write_chronicle
emits c.start_tick/c.end_tick raw, which are 0 for most entries.

Rule (M0): an entry whose cluster has no event ticks takes the jump window.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")

FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    quit_cmd = {"type": "cmd", "name": "quit"}
    script = b"".join(_frame(c) for c in cmds + [quit_cmd])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def test_jump_entry_ticks_within_jump_window():
    """After set_seed + jump 250 + jump 50, the second chronicle frame
    (from_tick=250, to_tick=300) has every entry satisfying:
        from_tick <= start_tick <= end_tick <= to_tick.
    Entries with no cluster event ticks (start_tick==end_tick==0 on the
    cluster) fall back to the jump window.
    """
    cmds = [
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80,
         "features": FEATURES, "new_campaign": False},
        {"type": "cmd", "name": "jump", "ticks": 250},
        {"type": "cmd", "name": "jump", "ticks": 50},
    ]
    frames = _run(cmds)
    chronicles = [f for f in frames if f.get("type") == "chronicle"]
    assert len(chronicles) == 2, f"expected 2 chronicle frames, got {len(chronicles)}"
    chron = chronicles[1]

    jump = chron.get("jump", {})
    from_tick = jump.get("from_tick")
    to_tick = jump.get("to_tick")
    assert from_tick is not None and to_tick is not None, f"missing jump ticks: {jump}"
    # The second jump is 50 ticks from tick 250: expect 250..300
    assert from_tick == 250, f"expected from_tick=250, got {from_tick}"
    assert to_tick == 300, f"expected to_tick=300, got {to_tick}"

    entries = chron.get("entries", [])
    assert entries, f"second chronicle has no entries: {chron}"

    for ent in entries:
        st = ent.get("start_tick")
        et = ent.get("end_tick")
        eid = ent.get("id")
        assert st is not None and et is not None, f"entry {eid} missing ticks: {ent}"
        assert from_tick <= st, f"entry {eid} start_tick={st} < from_tick={from_tick}"
        assert st <= et, f"entry {eid} start_tick={st} > end_tick={et}"
        assert et <= to_tick, f"entry {eid} end_tick={et} > to_tick={to_tick}"
