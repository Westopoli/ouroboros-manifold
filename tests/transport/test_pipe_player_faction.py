"""T1-14: pipe session reports the real player faction.

(a) hello before set_seed carries player_faction == -1 (no world yet).
(b) snapshot after set_seed carries player_faction == 0 (worldgen assigns
    OM_ARCH_PLAYER to faction 0); the tactical frame's visible dict is keyed
    by faction-id strings, and "0" is the player's key.
(c) [held: no reachable -1 scenario exists through the pipe after a
    successful set_seed -- worldgen always assigns OM_ARCH_PLAYER to
    faction 0 before generation returns; a pinned n_regions below the
    feasible minimum makes generation fail and set_seed answers error,
    so the world is never configured in that case. Test (c) requires a
    world where om_player_faction returns -1 before mission_start so the
    pipe can set it to the client-named faction. No such world is reachable.]

Positive controls: (a) fails on a pipe whose hello frame lacks player_faction;
(b) fails on a pipe whose snapshot lacks player_faction or whose snapshot
carries a static -1 instead of the real value.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES}
SNAPSHOT = {"type": "cmd", "name": "snapshot"}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
QUIT = {"type": "cmd", "name": "quit"}

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run_raw(cmds):
    """Run cmds + quit; return ALL frames including hello."""
    script = b"".join(_frame(c) for c in cmds + [QUIT])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out


def test_hello_player_faction_is_minus_one():
    """(a) hello is emitted before any set_seed; world does not exist yet;
    player_faction must be -1.  Fails if the key is absent or has any
    other value (e.g. a leftover 0 from a stale world)."""
    frames = _run_raw([])
    assert len(frames) >= 1 and frames[0]["type"] == "hello", frames
    hello = frames[0]
    assert "player_faction" in hello, "player_faction key absent from hello: %r" % hello
    assert hello["player_faction"] == -1, (
        "hello player_faction should be -1 before set_seed, got %r" % hello["player_faction"]
    )


def test_snapshot_after_set_seed_reports_real_player_faction():
    """(b) snapshot emitted after set_seed must carry player_faction == 0.
    Worldgen always assigns OM_ARCH_PLAYER (archetype id 0) to faction 0,
    so om_player_faction returns 0.  Fails if the key is absent (not yet
    emitted) or if it is a static -1 (the pre-T1-14 hello-time value)."""
    frames = _run_raw([SET_SEED, SNAPSHOT])
    snaps = [f for f in frames if f["type"] == "snapshot"]
    assert snaps, "no snapshot frame: %r" % [f["type"] for f in frames]
    snap = snaps[0]
    assert "player_faction" in snap, (
        "player_faction key absent from snapshot: %r" % list(snap.keys())
    )
    assert snap["player_faction"] == 0, (
        "snapshot player_faction should be 0 after set_seed (worldgen assigns "
        "OM_ARCH_PLAYER to faction 0), got %r" % snap["player_faction"]
    )


def test_tactical_visible_is_keyed_by_faction_id_strings():
    """(b continued) tactical frame's visible dict uses faction-id strings as
    keys; the player's key would be str(player_faction) == '0'.  When units
    exist their entries appear under the owning faction's string key.  Even
    with zero units visible must be a dict (not a list), consistent with the
    protocol shape in docs/architecture.md."""
    frames = _run_raw([SET_SEED, START, BEGIN])
    tacticals = [f for f in frames if f["type"] == "tactical"]
    assert tacticals, "no tactical frame: %r" % [f["type"] for f in frames]
    visible = tacticals[0]["visible"]
    assert isinstance(visible, dict), "visible should be a dict, got %r" % type(visible)
    # All keys present must be faction-id strings (digits only).
    for k in visible:
        assert k.lstrip("-").isdigit(), "visible key is not a faction id string: %r" % k
    # If the player faction has units, its key "0" must appear.
    if visible:
        assert "0" in visible, (
            "player faction 0 has units but '0' is absent from visible: %r" % visible
        )
