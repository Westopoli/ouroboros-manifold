"""C1 / gap-fix S3: the chronicle frame carries faction refs.

Chronicle entries carry `refs.factions` from the entry's `faction_ref`
(`om_chronicle_entry_get`, the owner of the cluster's region when the text pass
ran). Today the pipe writes `refs.factions` as `[]` for every entry, so the
client prints the `[faction]` fallback after a jump (docs/architecture.md
"Chronicle frame", currently documents the empty list).

Positive control: the test is red while every entry's factions list is empty.
Ids: S3, R-067-01 (chronicle refs).
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
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]


def _jump(seed):
    frames = _run([
        {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": 80, "features": FEATURES},
        {"type": "cmd", "name": "jump", "ticks": 50},
    ])
    chron = next((f for f in frames if f.get("type") == "chronicle"), None)
    assert chron is not None, f"no chronicle frame; types={[f.get('type') for f in frames]}"
    snap = [f for f in frames if f.get("type") == "snapshot"][-1]
    return chron, snap


def test_s3_jump_entries_carry_faction_refs():
    """After a 50-tick jump at least one entry names a faction, every faction
    ref is a valid faction index, and no entry lists more than its own owner."""
    for seed in (1, 2, 3):
        chron, snap = _jump(seed)
        entries = chron["entries"]
        assert entries, f"seed {seed}: chronicle has no entries"
        n_factions = len(snap["factions"])
        named = 0
        for ent in entries:
            facs = ent["refs"]["factions"]
            assert isinstance(facs, list) and len(facs) <= 1, f"entry {ent['id']}: factions={facs}"
            for fid in facs:
                assert isinstance(fid, int) and 0 <= fid < n_factions, (
                    f"entry {ent['id']}: faction ref {fid} outside 0..{n_factions - 1}")
            named += bool(facs)
        assert named > 0, f"seed {seed}: all {len(entries)} entries have refs.factions == [] (client prints [faction])"


def test_s3_owned_region_entry_names_its_owner():
    """An entry whose region is owned in the post-jump snapshot lists that owner
    for the majority of owned-region entries (faction_ref is the region owner)."""
    chron, snap = _jump(1)
    owners = {r["i"]: r["owner"] for r in snap["regions"]}
    owned = [e for e in chron["entries"] if owners.get(e["refs"]["regions"][0], -1) >= 0]
    assert owned, "no entry sits on an owned region (fixture too thin)"
    hits = sum(1 for e in owned if e["refs"]["factions"] == [owners[e["refs"]["regions"][0]]])
    assert hits * 2 > len(owned), f"only {hits}/{len(owned)} owned-region entries name their owner"
