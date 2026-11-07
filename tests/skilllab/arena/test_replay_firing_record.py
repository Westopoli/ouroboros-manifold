# spec: bug H-088 replay-firing-lines (Westley's replay recording, 2026-11-07): the replay drew a target line from every unit with a `target`, even one still walking toward it
# Rule pins: none (lab harness story H-088)
"""H-088 replay-firing-lines, part A: the fight file records who fired. Optional per-unit key `fired` (bool) on every unit row of every frame of an `om-fight-2` file.

RF-1 every unit row of every frame of every `run.fight` / closeup document carries a bool `fired`; frame 0 and every dead unit are False.
RF-2 `fired` is True iff the unit was the attacker of an engine tactical event of kind 0 (fire) on a tick t with previous_frame_tick < t <= frame_tick, and the unit is alive
     at the frame. The oracle below reads `om_tactical_event_count` / `om_tactical_event_get_at` itself after each `Engine.step` (it patches `Engine.step` for the run, so it
     does not depend on any helper the implementation adds), and the window is that of consecutive frames of the WRITTEN document.
RF-3 the same fight run twice gives the same `fired`; a closeup window (`--from-tick`) keeps each frame's `fired` as the full dense file has it.
RF-4 the OR of a K-tick dense file's `fired` over a normal frame's window equals the normal frame's `fired` (units alive at the normal frame; a unit that fired and then died in
     the window is False in the normal frame and True in the dense frames before its death).
RF-5 `snapshot.validate` accepts `fired` (bool) present or absent on om-fight-2, rejects a non-bool naming the key (not as an unknown key), rejects the key on om-fight-1.

Fixtures: OPEN and COVER of tests/skilllab/arena/test_closeup.py (OPEN sight off 585 ticks, 7 normal frames at 0, 100 ... 500, 585; COVER is thinned, 12 frames 400 apart).
COVER is checked with the one-sided invariant that holds whether a thinned file's window is the captured one or the written one (open question in the report).
Controls (green today): the v1 refusal of the key, the oracle seeing fire events at all."""
import contextlib
import ctypes
from pathlib import Path

import pytest

import h063_fixtures as fx  # noqa: F401  (puts the repository root on sys.path)
from scripts.skilllab import engine as engine_mod
from scripts.skilllab.arena import run as arena_run, snapshot
from test_closeup import Lab, _layout, closeup_main, by_tick  # noqa: F401

FIRE = 0   # csrc/unit.c OM_TAC_EV_FIRE


@contextlib.contextmanager
def recording():
    """Yields {tick: {attacker unit id}}: every fire event (kind 0) the engine reports after step number `tick` of the fight run inside the block (steps counted from 1 per Engine)."""
    fires = {}
    orig = engine_mod.Engine.step
    V, u32, i32, u64 = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint64

    def step(self, w):
        orig(self, w)
        lib = self._lib
        lib.om_tactical_event_count.restype, lib.om_tactical_event_count.argtypes = u32, [V]
        lib.om_tactical_event_get_at.restype = ctypes.c_int
        lib.om_tactical_event_get_at.argtypes = [V, u32, ctypes.POINTER(i32), ctypes.POINTER(u32), ctypes.POINTER(i32), ctypes.POINTER(u64)]
        self._rf_tick = getattr(self, "_rf_tick", 0) + 1
        kind, a, b, t = i32(), u32(), i32(), u64()
        for n in range(lib.om_tactical_event_count(w)):
            if lib.om_tactical_event_get_at(w, n, ctypes.byref(kind), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0 and kind.value == FIRE:
                fires.setdefault(self._rf_tick, set()).add(a.value)

    engine_mod.Engine.step = step
    try:
        yield fires
    finally:
        engine_mod.Engine.step = orig


def run_fight(case, sight, every=None):
    """(document, fires): the document `run._document` writes for the case (the closeup way when `every` is given) and the oracle's fire events of that run."""
    lay = _layout(case)
    with recording() as fires:
        args = (lay, 1, sight, 600) if every is None else (lay, 1, sight, 600, every)
        frames, last, end, orders = arena_run.fight(*args)
    doc = arena_run._document(lay, Path(lay["id"] + ".toml"), 1, sight, frames, last, end, orders, *([] if every is None else [every]))
    return doc, fires


def expected_fired(doc, fires):
    """{tick: [bool per unit row]} by the RF-2 rule on the document's own consecutive frames."""
    out, prev = {}, None
    for f in doc["frames"]:
        window = set() if prev is None else {u for t in range(prev + 1, f["tick"] + 1) for u in fires.get(t, ())}
        out[f["tick"]] = [bool(u["alive"]) and u["id"] in window for u in f["units"]]
        prev = f["tick"]
    return out


def fired_of(doc):
    return {f["tick"]: [u.get("fired") for u in f["units"]] for f in doc["frames"]}


@pytest.fixture(scope="module")
def lab(tmp_path_factory):
    return Lab(tmp_path_factory.mktemp("replay_firing"))


# ---------------------------------------------------------------- RF-1 the key is there

def test_control_the_oracle_sees_fire_events_in_the_open_fight():
    """CONTROL (green today): the oracle reads kind-0 events from the engine on OPEN (sight off) and the fight has frames after tick 0, so a red below is the missing key and not
    an oracle that sees nothing."""
    doc, fires = run_fight("open", "off")
    assert (bool(fires), len(doc["frames"]) > 2, min(fires, default=0) > 0) == (True, True, True)


@pytest.mark.parametrize("case,sight", [("open", "off"), ("open", "on"), ("open", "control"), ("cover", "on")])
def test_rf1_every_unit_row_of_every_normal_frame_has_a_bool_fired(lab, case, sight):
    """RF-1 ("Written by every run of run.fight, all sight modes"): in the normal fight file (run.main; sight control is `--sight on --control sight`) every unit row of every frame has
    `fired`, a bool; frame 0 and every dead unit are False."""
    doc = lab.normal(case, sight)[0]
    rows = [(f["tick"], u) for f in doc["frames"] for u in f["units"]]
    assert (all(isinstance(u.get("fired"), bool) for _, u in rows), all(u.get("fired") is False for t, u in rows if t == 0 or not u["alive"])) == (True, True)


@pytest.mark.parametrize("case,sight,k", [("open", "on", 10), ("open", "off", 7), ("cover", "on", 50)])
def test_rf1_every_unit_row_of_a_closeup_file_has_a_bool_fired(lab, case, sight, k):
    """RF-1 ("closeup dense files included"): the closeup CLI's file has the key on every unit row of every frame, False on frame 0 and on dead units."""
    doc = lab.ok(case, sight, k)
    rows = [(f["tick"], u) for f in doc["frames"] for u in f["units"]]
    assert (all(isinstance(u.get("fired"), bool) for _, u in rows), all(u.get("fired") is False for t, u in rows if t == 0 or not u["alive"])) == (True, True)


def test_rf1_somebody_fires_in_a_real_fight(lab):
    """RF-1/RF-2 non-vacuity: in the OPEN fight (a wipe) some unit row has `fired` True in the normal file and in the K 10 file, and not every row of the K 10 file is True."""
    normal, dense = lab.normal("open", "off")[0], lab.ok("open", "off", 10)
    flags = lambda d: [u.get("fired") for f in d["frames"] for u in f["units"]]
    assert (True in flags(normal), True in flags(dense), False in flags(dense)) == (True, True, True)


# ---------------------------------------------------------------- RF-2 who fired, by the engine's own events

@pytest.mark.parametrize("sight,every", [("off", None), ("on", None), ("control", None), ("on", 1), ("on", 10), ("off", 7)])
def test_rf2_fired_is_the_engine_fire_events_in_the_window_of_consecutive_frames(sight, every):
    """RF-2 ("True iff that unit fired (kind 0 with the unit as attacker) on any tick t with previous_frame_tick < t <= frame_tick; false on frame 0 and for dead units"): on OPEN,
    for the normal rule sets and for dense files K 1, 10 and 7, each unit row's `fired` equals the oracle's: the unit is an attacker of a fire event in (previous frame tick, frame
    tick] of the written document and is alive at the frame."""
    doc, fires = run_fight("open", sight, every)
    assert fired_of(doc) == expected_fired(doc, fires)


def test_rf2_dead_unit_that_fired_in_its_last_window_is_false_at_the_frame_it_is_dead_in():
    """RF-2 "false ... for dead units": the K 100 normal file of OPEN has a unit that fired in the window ending at a frame where it is dead (the oracle says so; a wipe fight kills
    firing units); the row says False."""
    doc, fires = run_fight("open", "off")
    died_firing = [(f["tick"], u["id"]) for p, f in zip(doc["frames"], doc["frames"][1:]) for u in f["units"]
                   if not u["alive"] and any(u["id"] in fires.get(t, ()) for t in range(p["tick"] + 1, f["tick"] + 1))]
    rows = {(f["tick"], u["id"]): u.get("fired") for f in doc["frames"] for u in f["units"]}
    assert (bool(died_firing), [rows[k] for k in died_firing]) == (True, [False] * len(died_firing))


def test_rf2_cover_thinned_file_never_marks_a_unit_that_did_not_fire_in_the_written_window():
    """RF-2 on the thinned COVER file (12 frames 400 ticks apart, captured every 100 before thinning): a unit marked `fired` fired inside the written window (previous written frame,
    this frame]; frame 0 has none; some unit is marked somewhere. (Holds for a captured-window implementation too: its window lies inside the written one.)"""
    doc, fires = run_fight("cover", "on")
    allowed, got = expected_fired(doc, fires), fired_of(doc)
    flat = [x for g in got.values() for x in g]
    assert (all(isinstance(x, bool) for x in flat), any(got[0]), all(not g or a for t in got for g, a in zip(got[t], allowed[t])), any(flat)) == (True, False, True, True)


# ---------------------------------------------------------------- RF-3 determinism, windows

def test_rf3_the_same_fight_run_twice_has_identical_fired():
    """RF-3 ("The same fight run twice gives identical `fired`"): two runs of OPEN sight on give the same `fired` on every row, and it is present (not two Nones)."""
    a, b = run_fight("open", "on")[0], run_fight("open", "on")[0]
    assert (fired_of(a) == fired_of(b), all(isinstance(x, bool) for g in fired_of(a).values() for x in g)) == (True, True)


def test_rf3_a_closeup_window_keeps_each_frames_fired_as_the_full_file_has_it(lab):
    """RF-3 / CL-3: the frames of `--from-tick 100 --to-tick 300` carry the same `fired` as the same ticks of the unwindowed K 10 file, the first frame of the window included
    (its window starts at the previous captured frame, not at the window's edge)."""
    full, part = by_tick(lab.ok("open", "on", 10)), by_tick(lab.ok("open", "on", 10, "--from-tick", 100, "--to-tick", 300))
    rows = lambda f: [u.get("fired") for u in f["units"]]
    assert (sorted(part), all(isinstance(x, bool) for t in part for x in rows(part[t])), all(rows(part[t]) == rows(full[t]) for t in part)) == (list(range(100, 301, 10)), True, True)


# ---------------------------------------------------------------- RF-4 dense windows OR to the normal frame

@pytest.mark.parametrize("sight,k", [("off", 10), ("on", 10), ("off", 5)])
def test_rf4_the_or_of_the_dense_windows_is_the_normal_frames_fired(lab, sight, k):
    """RF-4 ("the OR of the K-window dense `fired` values over a normal frame's window equals the normal frame's `fired` when windows align"): K divides the 100-tick spacing, and
    the last normal frame's window (500, 585] is also whole dense frames (the dense file ends on the last tick). For each normal frame after tick 0 and each unit alive at it,
    its `fired` is the OR of that unit's dense `fired` over the dense frames in (previous normal tick, normal tick]."""
    normal, dense = lab.normal("open", sight)[0], by_tick(lab.ok("open", sight, k))
    problems = []
    for p, f in zip(normal["frames"], normal["frames"][1:]):
        window = [dense[t] for t in sorted(dense) if p["tick"] < t <= f["tick"]]
        for n, u in enumerate(f["units"]):
            if u["alive"]:
                got = any(w["units"][n]["fired"] for w in window)
                if got is not u.get("fired"):
                    problems.append((f["tick"], u["id"], u.get("fired"), got))
    assert (problems, len(window) > 0) == ([], True)


# ---------------------------------------------------------------- RF-5 snapshot.validate

def v2_with(values):
    """An om-fight-2 example (3 frames, 4 units) whose unit rows carry `fired` per frame: values[n][i] for frame n, unit index i."""
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    for f, row in zip(doc["frames"], values):
        for u, v in zip(f["units"], row):
            u["fired"] = v
    return doc


GOOD = [[False] * 4, [True, False, True, False], [True, True, False, False]]


def test_rf5_validate_accepts_fired_present_and_absent_on_v2():
    """RF-5: a v2 example with a bool `fired` on every row validates; one with none still validates (CONTROL part, green today); one with `fired` on some rows only validates
    (the key is optional per row)."""
    partial = v2_with(GOOD)
    for u in partial["frames"][1]["units"]:
        del u["fired"]
    plain = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    assert [snapshot.validate(d) for d in (v2_with(GOOD), plain, partial)] == [[], [], []]


@pytest.mark.parametrize("bad", [1, 0, "true", None, [True], 1.0])
def test_rf5_validate_rejects_a_non_bool_fired_naming_the_key_as_a_bad_type(bad):
    """RF-5 ("rejects a non-bool"): the well-typed document is accepted first (so this is the type and not an unknown key), then `fired` set to a non-bool on one row is refused
    with a message that names `fired` and says bad type, not unknown key."""
    assert snapshot.validate(v2_with(GOOD)) == []
    doc = v2_with(GOOD)
    doc["frames"][1]["units"][2]["fired"] = bad
    errors = snapshot.validate(doc)
    assert [e for e in errors if "fired" in e and "bad type" in e] and not [e for e in errors if "unknown key" in e and "fired" in e], errors


def test_control_validate_rejects_fired_on_a_v1_document_naming_the_key():
    """CONTROL (green today, must stay green), RF-5 "rejects the key on om-fight-1": a v1 example with `fired` on a row is refused with a message naming `fired`."""
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA)
    doc["frames"][1]["units"][0]["fired"] = True
    errors = snapshot.validate(doc)
    assert errors and any("fired" in e for e in errors), errors


def test_rf5_a_written_document_with_fired_reads_back(tmp_path):
    """RF-5: `snapshot.write` then `snapshot.read` (which validates) round-trips `fired`."""
    path = tmp_path / "x.fight.json"
    snapshot.write(v2_with(GOOD), path)
    got = snapshot.read(path)
    assert [[u["fired"] for u in f["units"]] for f in got["frames"]] == GOOD


def test_rf5_the_runner_writes_a_file_the_checker_accepts(lab):
    """RF-5 / RF-1: the normal OPEN fight file as `run.main` wrote it (`fired` on every row) validates, so the runner and the checker agree (the closeup file is exempt: too many
    frames)."""
    doc = lab.normal("open", "off")[0]
    assert (snapshot.validate(doc), all("fired" in u for f in doc["frames"] for u in f["units"])) == ([], True)
