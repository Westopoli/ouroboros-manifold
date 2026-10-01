"""A1 (docs/northstar/plans/2026-09-30-mission-plays-plan.md): set_seed loads the
launch event library and applies the launch feature set, so events fire in play.

Proves R-030-01 (launch library loaded into the world at set_seed, 26 templates)
and R-067-03 / R-067-05 (event-derived chronicle clusters: chain clusters, and
regional growth/decline/stable clusters, as opposed to the ownership-change
`regional_faction_shift` cluster that exists without any event).

Reference-green: the same shape through the C-sim path (world_factory order:
om_world_new, features, om_world_generate, om_events_load_launch) gives 26
templates; with the launch library loaded the pipe's jump produces categories
21-23 (verified against a local pipe patched to call om_events_load_launch).
Red on unmodified main: no event library, so every jump entry is category 20.
"""
import ctypes
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
LIB = ROOT / "libouroboros.so"

pytestmark = pytest.mark.skipif(
    not (PIPE.exists() and LIB.exists()), reason="pipe/ouroboros_pipe not built (piece T1)"
)

FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
CTYPE_CHAIN = 2
CAT_REGIONAL_FACTION_SHIFT = 20
EVENT_REGIONAL_CATEGORIES = (21, 22, 23)  # growth, decline, stable (R-067-05)


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
    return out[1:]  # drop hello


def _set_seed(seed):
    return {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": 80,
            "features": FEATURES}


def _is_event_derived(entry):
    return (entry["cluster_type"] == CTYPE_CHAIN
            or entry["category"] in EVENT_REGIONAL_CATEGORIES)


def _reference_template_count():
    """The E-04 isolation test's expected count (tests/csim/
    test_E04_S030_the_launch_event_library.py), read off the C library the way
    world_factory builds a world."""
    lib = ctypes.CDLL(str(LIB))
    lib.om_world_new.argtypes = [ctypes.c_uint32, ctypes.c_uint64]
    lib.om_world_new.restype = ctypes.c_void_p
    lib.om_world_set_feature.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    lib.om_world_generate.argtypes = [ctypes.c_void_p]
    lib.om_events_load_launch.argtypes = [ctypes.c_void_p]
    lib.om_event_template_count.argtypes = [ctypes.c_void_p]
    lib.om_event_template_count.restype = ctypes.c_uint32
    lib.om_world_free.argtypes = [ctypes.c_void_p]
    w = lib.om_world_new(80, 1)
    try:
        for f in FEATURES:
            lib.om_world_set_feature(w, f, 1)
        lib.om_world_generate(w)
        lib.om_events_load_launch(w)
        return lib.om_event_template_count(w)
    finally:
        lib.om_world_free(w)


def test_control_event_derived_detector():
    """Positive control: the detector accepts event-derived entries and rejects
    the ownership-change cluster that exists with no event library."""
    assert _is_event_derived({"cluster_type": 3, "category": 21})
    assert _is_event_derived({"cluster_type": 2, "category": 12})
    assert not _is_event_derived({"cluster_type": 3, "category": CAT_REGIONAL_FACTION_SHIFT})


def test_control_reference_count_is_26():
    """Positive control: the reference path really yields the E-04 count (R-030-01)."""
    assert _reference_template_count() == 26


def test_R_030_01_set_seed_then_jump_chronicle_has_event_derived_entry():
    """R-030-01 / R-067-05: after set_seed + one jump through the pipe, the
    chronicle frame carries at least one event-derived entry."""
    frames = _run([_set_seed(1), {"type": "cmd", "name": "jump", "ticks": 50}])
    chronicle = next((f for f in frames if f.get("type") == "chronicle"), None)
    assert chronicle is not None, f"no chronicle frame; types={[f.get('type') for f in frames]}"
    entries = chronicle["entries"]
    assert any(_is_event_derived(e) for e in entries), (
        "no event-derived chronicle entry (chain cluster or regional category 21-23); "
        f"got (cluster_type, category) = {[(e['cluster_type'], e['category']) for e in entries]}"
    )


def test_R_030_01_in_play_templates_match_launch_library():
    """R-030-01: events fire in play, and every fired template id lies inside the
    26-template launch library the E-04 isolation test expects. The pipe exposes
    template ids on delta frames, not the loaded count (see report, ambiguity)."""
    expected = _reference_template_count()
    fired = []
    for seed in (1, 2, 3):
        frames = _run([_set_seed(seed)] + [{"type": "cmd", "name": "step", "ticks": 10}] * 40)
        fired += [e["template"] for f in frames for e in f.get("events", [])]
    assert fired, "no event fired in 400 ticks across 3 seeds: launch library not loaded in play"
    assert max(fired) < expected, f"template id {max(fired)} outside the {expected}-template launch library"
