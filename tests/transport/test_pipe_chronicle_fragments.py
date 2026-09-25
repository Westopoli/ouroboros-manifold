"""T1-9: chronicle frame entries carry fragment_ids as a list of 3 ints.

Positive control: test is red on unmodified main because write_chronicle
emits "fragment": 0 (scalar) but not "fragment_ids" (list). After T1-9
the entry carries both: "fragment_ids": [id0, id1, id2] from
om_chronicle_entry_get, and "fragment": fragment_ids[0] kept for the
client until it switches.
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


def test_chronicle_entries_have_fragment_ids_list_of_3():
    """After set_seed + jump 50, every entry in the chronicle frame has a
    fragment_ids field that is a list of exactly 3 integers, and the scalar
    fragment key equals fragment_ids[0].
    At least one entry has a non-zero value in fragment_ids (verifies the
    text pass ran and real fragments were assigned).
    """
    cmds = [
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80,
         "features": FEATURES},
        {"type": "cmd", "name": "jump", "ticks": 50},
    ]
    frames = _run(cmds)
    chronicle = next((f for f in frames if f.get("type") == "chronicle"), None)
    assert chronicle is not None, f"no chronicle frame; types={[f.get('type') for f in frames]}"
    entries = chronicle.get("entries", [])
    assert entries, f"chronicle has no entries: {chronicle}"

    for ent in entries:
        fids = ent.get("fragment_ids")
        assert fids is not None, f"entry {ent.get('id')} missing fragment_ids: {ent}"
        assert isinstance(fids, list) and len(fids) == 3, (
            f"entry {ent.get('id')} fragment_ids not a list of 3: {fids}"
        )
        assert all(isinstance(v, int) for v in fids), (
            f"entry {ent.get('id')} fragment_ids contains non-int: {fids}"
        )
        # scalar fragment must match fragment_ids[0]
        frag = ent.get("fragment")
        assert frag == fids[0], (
            f"entry {ent.get('id')} fragment={frag} != fragment_ids[0]={fids[0]}"
        )

    # at least one non-zero value across all entries (text pass ran)
    all_ids = [v for ent in entries for v in ent.get("fragment_ids", [])]
    assert any(v > 0 for v in all_ids), (
        f"all fragment_ids are 0 or -1 -- text pass may not have run: "
        f"sample={[e.get('fragment_ids') for e in entries[:3]]}"
    )
