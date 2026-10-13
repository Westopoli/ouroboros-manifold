"""SV-3: scripts/simviewer/viewer.py, the sim viewer's state machine, band table and
drawing, driven headless.

Piece SV-3 of docs/northstar/plans/2026-10-12-simviewer-spec.md, sections
"Pre-flight corrections" and "SV-3 interfaces" (frozen API and phase machine).

Rules proved (spec; the viewer is tooling, R-077-01/02 supply the band shape):
  - pick_to_inputs(archetype, band) returns (completion, retention) in [0, 1] whose
    final = 0.75 c + 0.25 r classifies back to the band, for every mission
    archetype id the sim can draw and every band 0..4 (R-077-01, R-077-02);
  - BAND_THRESHOLDS equals the OM_MISSION_BAND_THRESHOLDS_* constants of
    csrc/om_constants.h as grouped by csrc/mission.c om_mission_classify_band;
  - ViewerState phase machine idle -> started -> debriefed -> idle on a fake
    session (frame shapes copied from the recorded real frames), rate ladder,
    pause, key map, inventory();
  - draw() produces a non-uniform 1280x720 frame in each mode and survives an
    empty History;
  - the same machine on the real pipe/ouroboros_pipe_dbg: the pipe's debrief band
    equals the pick;
  - `--shot DIR` writes tick_mode.png and mission_mode.png.

Part 1 positive controls: a shifted threshold table must be reported as a
mismatch; an all-black surface must fail the near-uniform check.

Red on the built tree: module scripts.simviewer.viewer does not exist
(ModuleNotFoundError).
"""
import copy
import json
import os
import re
import subprocess
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.simviewer.history import History  # noqa: E402
from scripts.simviewer.pipe_session import (  # noqa: E402
    DEFAULT_FEATURES,
    JUMP_TICKS,
    PipeSession,
)
from scripts.simviewer.viewer import (  # noqa: E402
    BAND_THRESHOLDS,
    RATES,
    ViewerState,
    draw,
    inventory,
    pick_to_inputs,
)

FIX = Path(__file__).resolve().parent / "fixtures"
PIPE_DBG = ROOT / "pipe/ouroboros_pipe_dbg"
MISSION_C = ROOT / "csrc/mission.c"
CONSTANTS_H = ROOT / "csrc/om_constants.h"


def _load(name):
    return json.loads((FIX / name).read_text())


# ------------------------------------------------------------ C source parsing

def _c_archetype_ids():
    """Mission archetype ids the sim can draw: the OM_MISSION_ARCH_* defines.
    (They live in csrc/mission.c, not csrc/ouroboros_sim.h; ouroboros_sim.h only
    has the faction OM_ARCH_* enum, which is unrelated.)"""
    ids = {m.group(1): int(m.group(2)) for m in re.finditer(
        r"^#define\s+OM_MISSION_ARCH_([A-Z_]+)\s+(\d+)\s*$",
        MISSION_C.read_text(), re.M) if m.group(1) != "COUNT"}
    assert len(ids) >= 10, ids
    return ids


def _c_group_constants():
    """group name -> (t1, t2, t3, t4) from the OM_MISSION_BAND_THRESHOLDS_* defines."""
    vals = {}
    for m in re.finditer(
            r"^#define\s+OM_MISSION_BAND_THRESHOLDS_([A-Z_]+)_T([1-4])\s+([0-9.]+)\s*$",
            CONSTANTS_H.read_text(), re.M):
        vals.setdefault(m.group(1), {})[int(m.group(2))] = float(m.group(3))
    return {g: tuple(t[i] for i in (1, 2, 3, 4)) for g, t in vals.items()}


def _c_case_groups():
    """archetype name -> group name, read from the switch in
    om_mission_classify_band; names not listed fall to the C default (STANDARD)."""
    src = MISSION_C.read_text()
    start = src.index("int32_t om_mission_classify_band(")
    body = src[start:src.index("\n}\n", start)]
    mapping, pending = {}, []
    for line in body.splitlines():
        c = re.match(r"\s*case\s+OM_MISSION_ARCH_([A-Z_]+)\s*:", line)
        if c:
            pending.append(c.group(1))
            continue
        t = re.search(r"t1\s*=\s*OM_MISSION_BAND_THRESHOLDS_([A-Z_]+)_T1", line)
        if t:
            for name in pending:
                mapping[name] = t.group(1)
            pending = []
    return mapping


def _c_thresholds():
    ids, groups, cases = _c_archetype_ids(), _c_group_constants(), _c_case_groups()
    assert {"STANDARD", "EVACUATION", "MULTI_FRONT", "RECONQUEST_ASSAULT"} <= set(groups)
    return {i: groups[cases.get(name, "STANDARD")] for name, i in ids.items()}


def _classify(table, archetype, final):
    t1, t2, t3, t4 = table[archetype]
    if final < t1:
        return 0
    if final < t2:
        return 1
    if final < t3:
        return 2
    if final < t4:
        return 3
    return 4


# ------------------------------------------------------------ 1. pick_to_inputs

def _pick_mismatches(table):
    """(archetype, band, why) for every archetype the sim can draw and band 0..4
    whose pick_to_inputs result does not classify back through `table`."""
    bad = []
    for arch in sorted(_c_archetype_ids().values()):
        for band in range(5):
            c, r = pick_to_inputs(arch, band)
            if not (0.0 <= c <= 1.0 and 0.0 <= r <= 1.0):
                bad.append((arch, band, "out of [0,1]: %r %r" % (c, r)))
                continue
            got = _classify(table, arch, 0.75 * c + 0.25 * r)
            if got != band:
                bad.append((arch, band, "classified %d" % got))
    return bad


def test_pick_to_inputs_classifies_back_to_the_band_for_every_archetype():
    """SV-3 / R-077-01, R-077-02: final = 0.75 c + 0.25 r lands in the picked band
    for every mission archetype id and band 0..4, with c and r in [0, 1]."""
    assert _pick_mismatches(BAND_THRESHOLDS) == []


def test_pick_to_inputs_positive_control_shifted_table_is_reported():
    """SV-3 positive control: the same check against a table shifted by +0.1 must
    report mismatches (else the check proves nothing)."""
    shifted = {a: tuple(t + 0.1 for t in row) for a, row in BAND_THRESHOLDS.items()}
    assert _pick_mismatches(shifted), "shifted table was not detected"


def test_pick_to_inputs_is_a_completion_retention_pair_of_the_documented_shape():
    """SV-3 frozen rule: target m = band midpoint; m >= 0.25 -> retention 1.0 and
    completion (m - 0.25) / 0.75, else retention 0.0 and completion m / 0.75."""
    for arch in sorted(_c_archetype_ids().values()):
        t = BAND_THRESHOLDS[arch]
        edges = (0.0,) + tuple(t) + (1.0,)
        for band in range(5):
            m = (edges[band] + edges[band + 1]) / 2
            c, r = pick_to_inputs(arch, band)
            if m >= 0.25:
                assert (r, c) == (1.0, pytest.approx((m - 0.25) / 0.75)), (arch, band)
            else:
                assert (r, c) == (0.0, pytest.approx(m / 0.75)), (arch, band)


# ------------------------------------------------------------ 2. table vs C source

def test_band_thresholds_equal_the_c_constants_per_archetype():
    """SV-3 / R-077-02: BAND_THRESHOLDS has a row for every archetype id and each
    equals the OM_MISSION_BAND_THRESHOLDS_* group csrc/mission.c selects for it
    (unlisted ids take STANDARD, as the C default does)."""
    want = _c_thresholds()
    for arch, row in sorted(want.items()):
        assert arch in BAND_THRESHOLDS, "no row for archetype %d" % arch
        assert tuple(BAND_THRESHOLDS[arch]) == row, arch
    # the C parse itself must see more than one group, or the check is vacuous
    assert len(set(want.values())) >= 3


# ------------------------------------------------------------ fake session

class FakeSession:
    """Canned frames shaped like the real ones (fixtures recorded from the dbg
    pipe); records every call as (name, fields)."""

    def __init__(self, archetype=5, region=56, n_objectives=2, debrief_band=None):
        self.calls = []
        self.archetype = archetype
        self.region = region
        self.n_objectives = n_objectives
        self.debrief_band = debrief_band      # None: echo the retention-derived band
        self._deltas = _load("deltas_t1_t20.json")
        self._i = 0
        self._last_retention = None

    def names(self):
        return [c[0] for c in self.calls]

    def fields(self, name):
        return [f for n, f in self.calls if n == name]

    def send(self, name, **fields):
        self.calls.append((name, dict(fields)))
        if name == "step":
            out = []
            for _ in range(fields.get("n", 1)):
                out.append(copy.deepcopy(self._deltas[self._i % len(self._deltas)]))
                self._i += 1
            return out + [{"type": "ack", "name": "step", "tick": out[-1]["tick"]}]
        if name == "mission_start":
            m = _load("mission_frame.json")
            m["archetype"] = self.archetype
            m["region"] = self.region
            m["objectives"] = [dict(m["objectives"][0], i=i)
                               for i in range(self.n_objectives)]
            return [m]
        if name == "objective_complete":
            return [{"type": "ack", "name": "objective_complete"}]
        if name in ("mission_end", "mission_refuse"):
            d = _load("debrief_frame.json")
            d["band"] = 5 if name == "mission_refuse" else self.debrief_band
            return [d, _load("snapshot_t20.json")]
        if name == "jump":
            return [_load("chronicle_frame.json"), _load("snapshot_after_jump.json")]
        raise AssertionError("unexpected verb %s" % name)


def _history_t0():
    h = History()
    h.apply(_load("snapshot_t0.json"))
    return h


def _state(**kw):
    sess = FakeSession(**kw)
    return ViewerState(_history_t0(), sess), sess


# ------------------------------------------------------------ 3. state machine

def test_viewer_state_defaults():
    """SV-3 frozen defaults: tick mode, rate 5, paused, no pick, phase idle."""
    st, _ = _state()
    assert (st.mode, st.rate, st.paused, st.pick, st.phase) == ("tick", 5, True, None, "idle")
    assert st.selected_region is None and st.last_debrief is None
    assert st.mismatch is False and st.pulse == {}
    assert RATES == (1, 2, 5, 10, 20, 50)


def test_toggle_mode_and_pause():
    """SV-3: toggle_mode flips tick/mission; toggle_pause flips paused."""
    st, _ = _state()
    st.toggle_mode()
    assert st.mode == "mission"
    st.toggle_mode()
    assert st.mode == "tick"
    st.toggle_pause()
    assert st.paused is False
    st.toggle_pause()
    assert st.paused is True


def test_rate_up_and_down_clamp_at_the_ladder_ends():
    """SV-3: rate_up / rate_down walk RATES and clamp at both ends."""
    st, _ = _state()
    for _ in range(len(RATES) + 3):
        st.rate_down()
    assert st.rate == RATES[0]
    st.rate_up()
    assert st.rate == RATES[1]
    for _ in range(len(RATES) + 3):
        st.rate_up()
    assert st.rate == RATES[-1]
    st.rate_down()
    assert st.rate == RATES[-2]


def test_tick_mode_advance_sends_one_step_and_folds_deltas_into_history():
    """SV-3: advance() in tick mode sends step n=1 and applies every returned
    frame to the History (tick moves, the delta's region values land)."""
    st, sess = _state()
    h = st.history
    before_tick = h.tick
    first = _load("deltas_t1_t20.json")[0]
    st.advance()
    assert sess.calls == [("step", {"n": 1})]
    assert h.tick == first["tick"] > before_tick
    r0 = first["regions"][0]
    assert h.regions[r0["i"]]["military"] == r0["military"]


def test_update_while_paused_sends_nothing():
    """SV-3: update(dt) with paused True sends no command."""
    st, sess = _state()
    assert st.paused
    st.update(5.0)
    assert sess.calls == []


def test_update_unpaused_at_rate_10_sends_ten_steps_per_second():
    """SV-3: tick mode, unpaused, rate 10, update(1.0) -> exactly 10 step calls."""
    st, sess = _state()
    st.rate_up()                      # 5 -> 10
    assert st.rate == 10
    st.toggle_pause()
    st.update(1.0)
    assert sess.names() == ["step"] * 10
    assert all(f == {"n": 1} for f in sess.fields("step"))


def test_mission_advance_from_idle_starts_the_mission_and_pulses_its_region():
    """SV-3: mission mode, phase idle: advance sends mission_start with a faction
    and era_kind 0, phase becomes started, selected_region is the mission's
    region and that region is pulsing."""
    st, sess = _state(region=56)
    st.toggle_mode()
    st.advance()
    assert sess.names() == ["mission_start"]
    f = sess.fields("mission_start")[0]
    assert isinstance(f["faction"], int) and f["era_kind"] == 0
    assert st.phase == "started"
    assert st.selected_region == 56
    assert 0.0 < st.pulse[56] <= 2.0


def test_mission_advance_started_without_a_pick_sends_nothing():
    """SV-3: phase started, pick None -> no command, phase stays, status asks."""
    st, sess = _state()
    st.toggle_mode()
    st.advance()
    n = len(sess.calls)
    st.advance()
    assert len(sess.calls) == n
    assert st.phase == "started"
    assert "pick" in st.status.lower()


@pytest.mark.parametrize("archetype,pick,n_obj", [(5, 3, 2), (7, 2, 1), (2, 4, 3), (0, 1, 2)])
def test_mission_pick_sends_objectives_then_mission_end_with_retention(archetype, pick, n_obj):
    """SV-3: phase started, pick p 0..4: one objective_complete per objective
    (objective index and the completion from pick_to_inputs), then mission_end
    carrying retention = pick_to_inputs' retention; phase debriefed; last_debrief
    set; mismatch False when the debrief band equals the pick."""
    st, sess = _state(archetype=archetype, n_objectives=n_obj, debrief_band=pick)
    st.toggle_mode()
    st.advance()
    st.set_pick(pick)
    assert st.pick == pick
    sess.calls.clear()
    st.advance()
    c, r = pick_to_inputs(archetype, pick)
    assert sess.names() == ["objective_complete"] * n_obj + ["mission_end"]
    for i, f in enumerate(sess.fields("objective_complete")):
        assert f["objective"] == i
        assert f["completion"] == pytest.approx(c)
    assert sess.fields("mission_end")[0]["retention"] == pytest.approx(r)
    assert st.phase == "debriefed"
    assert st.last_debrief["band"] == pick
    assert st.mismatch is False


def test_mission_with_no_listed_objectives_still_completes_objective_zero():
    """SV-3: n_objectives is at least 1 (objective index 0 is always completed)."""
    st, sess = _state(n_objectives=0, debrief_band=3)
    st.toggle_mode()
    st.advance()
    st.set_pick(3)
    sess.calls.clear()
    st.advance()
    assert sess.names() == ["objective_complete", "mission_end"]
    assert sess.fields("objective_complete")[0]["objective"] == 0


def test_mismatch_true_when_the_debrief_band_differs_from_the_pick():
    """SV-3: mismatch is True when the (fake) debrief band != pick."""
    st, sess = _state(debrief_band=1)
    st.toggle_mode()
    st.advance()
    st.set_pick(3)
    st.advance()
    assert st.last_debrief["band"] == 1
    assert st.mismatch is True


def test_debriefed_advance_jumps_and_returns_to_idle_with_no_pick():
    """SV-3: phase debriefed: advance sends jump ticks=50 (JUMP_TICKS), phase idle,
    pick None."""
    assert JUMP_TICKS == 50
    st, sess = _state(debrief_band=3)
    st.toggle_mode()
    st.advance()
    st.set_pick(3)
    st.advance()
    sess.calls.clear()
    st.advance()
    assert sess.calls == [("jump", {"ticks": 50})]
    assert st.phase == "idle"
    assert st.pick is None


def test_pick_5_sends_mission_refuse_and_no_objectives():
    """SV-3: pick 5 is refusal: mission_refuse only, debrief band 5, no mismatch."""
    st, sess = _state()
    st.toggle_mode()
    st.advance()
    st.set_pick(5)
    sess.calls.clear()
    st.advance()
    assert sess.names() == ["mission_refuse"]
    assert st.phase == "debriefed"
    assert st.last_debrief["band"] == 5
    assert st.mismatch is False


def test_debrief_pulses_the_regions_the_snapshot_diff_reports():
    """SV-3: after mission_end every region History.diff reports between the
    snapshot before and after is pulsing."""
    st, sess = _state(debrief_band=3)
    st.toggle_mode()
    st.advance()
    st.set_pick(3)
    before = copy.deepcopy(st.history.regions)
    st.advance()
    changed = History.diff(before, st.history.regions)
    assert changed, "fixture pair should differ (t0 vs t20)"
    assert set(changed) <= set(st.pulse)


def test_update_decays_the_pulse():
    """SV-3: update(dt) decays pulse seconds left; entries expire."""
    st, _ = _state()
    st.pulse = {4: 2.0, 9: 0.1}
    st.update(0.5)
    assert st.pulse.get(4) == pytest.approx(1.5)
    assert 9 not in st.pulse


# ------------------------------------------------------------ 4. handle_key

def test_handle_key_mapping():
    """SV-3: SPACE pause, brackets rate, RIGHT one tick, m mode, 1-5 -> pick 0-4,
    0 -> pick 5, RETURN advance in mission mode, f sidebar toggle."""
    import pygame
    st, sess = _state()
    st.handle_key(pygame.K_SPACE)
    assert st.paused is False
    st.handle_key(pygame.K_SPACE)
    assert st.paused is True
    st.handle_key(pygame.K_RIGHTBRACKET)
    assert st.rate == 10
    st.handle_key(pygame.K_LEFTBRACKET)
    st.handle_key(pygame.K_LEFTBRACKET)
    assert st.rate == 2
    st.handle_key(pygame.K_RIGHT)
    assert sess.calls == [("step", {"n": 1})]
    st.handle_key(pygame.K_m)
    assert st.mode == "mission"
    for key, pick in ((pygame.K_1, 0), (pygame.K_2, 1), (pygame.K_3, 2),
                      (pygame.K_4, 3), (pygame.K_5, 4), (pygame.K_0, 5)):
        st.handle_key(key)
        assert st.pick == pick, key
    sess.calls.clear()
    st.handle_key(pygame.K_f)
    st.handle_key(pygame.K_f)
    assert sess.calls == []
    st.handle_key(pygame.K_RETURN)
    assert sess.names()[:1] == ["mission_start"]
    st.handle_key(pygame.K_m)
    assert st.mode == "tick"


# ------------------------------------------------------------ 5. inventory

INVENTORY_KEYS = {"mode", "rate", "paused", "phase", "pick", "mismatch", "regions_drawn",
                  "factions_listed", "selected_region", "mission_rows", "pulsing"}


def test_inventory_has_the_documented_keys_and_counts_reflect_history():
    """SV-3: inventory(state, history) is display-free and reports 80 regions and
    the factions after the snapshot fixture, pulsing sorted, mission rows counted."""
    st, _ = _state()
    h = st.history
    inv = inventory(st, h)
    assert set(inv) == INVENTORY_KEYS
    assert inv["regions_drawn"] == 80
    assert inv["factions_listed"] > 0
    assert (inv["mode"], inv["rate"], inv["paused"], inv["phase"], inv["pick"]) == (
        "tick", 5, True, "idle", None)
    assert inv["mismatch"] is False and inv["selected_region"] is None
    assert inv["mission_rows"] == 0 and inv["pulsing"] == []
    st.pulse = {7: 1.0, 2: 0.5}
    st.selected_region = 7
    h.apply(_load("mission_frame.json"))
    h.apply(_load("debrief_frame.json"))
    inv = inventory(st, h)
    assert inv["pulsing"] == [2, 7]
    assert inv["selected_region"] == 7
    assert inv["mission_rows"] == 1 == len(h.missions)


def test_inventory_on_an_empty_history():
    """SV-3: an empty History inventories to zero regions and factions."""
    h = History()
    inv = inventory(ViewerState(h), h)
    assert set(inv) == INVENTORY_KEYS
    assert inv["regions_drawn"] == 0 and inv["factions_listed"] == 0


# ------------------------------------------------------------ 6. rendering

W, H = 1280, 720
MIN_COLOURS = 20


def _distinct_colours(surface):
    import pygame
    data = pygame.image.tobytes(surface, "RGB")
    return len(set(zip(data[0::3], data[1::3], data[2::3])))


def _near_uniform(surface):
    return _distinct_colours(surface) <= MIN_COLOURS


@pytest.fixture(scope="module")
def pg():
    import pygame
    pygame.init()
    yield pygame
    pygame.quit()


def _full_history():
    h = _history_t0()
    for d in _load("deltas_t1_t20.json"):
        h.apply(d)
    h.apply(_load("mission_frame.json"))
    h.apply(_load("debrief_frame.json"))
    return h


def test_draw_positive_control_a_black_surface_is_near_uniform(pg):
    """SV-3 positive control: an all-black surface fails the colour-count check."""
    s = pg.Surface((W, H))
    s.fill((0, 0, 0))
    assert _near_uniform(s)


def test_draw_tick_mode_is_not_near_uniform(pg):
    """SV-3: tick-mode frame at 1280x720 with fixtures applied has > 20 colours."""
    h = _full_history()
    st = ViewerState(h)
    st.selected_region = 3
    st.pulse = {3: 1.0}
    s = pg.Surface((W, H))
    s.fill((0, 0, 0))
    draw(st, h, s)
    assert not _near_uniform(s), _distinct_colours(s)


def test_draw_mission_mode_is_not_near_uniform(pg):
    """SV-3: mission-mode frame (started with a debrief shown) has > 20 colours."""
    h = _full_history()
    st = ViewerState(h)
    st.toggle_mode()
    st.phase = "debriefed"
    st.pick = 3
    st.selected_region = 56
    st.pulse = {56: 2.0, 10: 1.0}
    st.last_debrief = _load("debrief_frame.json")
    s = pg.Surface((W, H))
    s.fill((0, 0, 0))
    draw(st, h, s)
    assert not _near_uniform(s), _distinct_colours(s)


@pytest.mark.parametrize("mode", ["tick", "mission"])
def test_draw_does_not_raise_on_an_empty_history(pg, mode):
    """SV-3: draw never raises on an empty History, in either mode."""
    h = History()
    st = ViewerState(h)
    if mode == "mission":
        st.toggle_mode()
    s = pg.Surface((W, H))
    draw(st, h, s)


# ------------------------------------------------------------ 7. real dbg pipe

needs_pipe = pytest.mark.skipif(
    not PIPE_DBG.exists(),
    reason="pipe/ouroboros_pipe_dbg not built: run make pipe/ouroboros_pipe_dbg")


def _real_cycle(pick):
    """Fresh session: seed 1, 80 regions; idle -> started -> pick -> debriefed ->
    jump -> idle. Returns (state, band seen in the debrief)."""
    with PipeSession() as s:
        s.send("set_seed", seed=1, n_regions=80, features=DEFAULT_FEATURES)
        h = History()
        for fr in s.send("snapshot"):
            h.apply(fr)
        st = ViewerState(h, s)
        st.toggle_mode()
        st.advance()
        assert st.phase == "started"
        assert st.selected_region is not None and 0 <= st.selected_region < 80
        st.set_pick(pick)
        st.advance()
        assert st.phase == "debriefed"
        band = st.last_debrief["band"]
        mismatch = st.mismatch
        tick_before = h.tick
        st.advance()
        assert st.phase == "idle" and st.pick is None
        assert h.tick > tick_before
        return band, mismatch


@needs_pipe
@pytest.mark.parametrize("pick", [1, 2, 3, 4])
def test_real_pipe_cycle_debrief_band_equals_the_pick(pick):
    """SV-3 / R-077-02 on the real dbg pipe: the pipe's band for the (completion,
    retention) pair pick_to_inputs chose equals the pick; mismatch is False."""
    band, mismatch = _real_cycle(pick)
    assert band == pick
    assert mismatch is False


@needs_pipe
@pytest.mark.xfail(strict=False, reason="SV-0 retention override not landed")
def test_real_pipe_cycle_pick_0_total_failure():
    """SV-3: pick 0 needs retention 0 forced, which the pipe ignores until SV-0
    lands, so this is a known red (the tool's finding signal)."""
    band, mismatch = _real_cycle(0)
    assert band == 0
    assert mismatch is False


@needs_pipe
def test_real_pipe_pick_5_refuses_with_band_5():
    """SV-3: pick 5 sends mission_refuse; the pipe's debrief band is 5."""
    band, mismatch = _real_cycle(5)
    assert band == 5
    assert mismatch is False


# ------------------------------------------------------------ 8. --shot CLI

@needs_pipe
def test_shot_cli_writes_both_pngs(tmp_path):
    """SV-3: `--shot DIR` runs headless, exits 0 and writes tick_mode.png and
    mission_mode.png (non-empty PNGs). Runs in a child process with a 120 s guard."""
    code = ("import sys; from scripts.simviewer.__main__ import main; "
            "sys.exit(main(['--seed','1','--n-regions','80','--shot',%r]))" % str(tmp_path))
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    res = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), env=env,
                         capture_output=True, timeout=120)
    assert res.returncode == 0, res.stderr.decode()[-2000:]
    for name in ("tick_mode.png", "mission_mode.png"):
        data = (tmp_path / name).read_bytes()
        assert len(data) > 1000, name
        assert data[:8] == b"\x89PNG\r\n\x1a\n", name
