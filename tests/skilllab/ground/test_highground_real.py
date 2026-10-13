# spec: docs/northstar/plans/2026-10-05-proto-highground-spec.md::Build notes - positive controls (real engine)
"""The positive controls of the high-ground instrument, on the production C library. Each test fails with a clear
message while scripts/skilllab/ground/highground.py does not exist.

Readings of the spec the builder must confirm (see the report):
- run_fight returns an object with: winner ("attackers", "defenders" or another string for a draw or stalemate),
  survivors (attackers, defenders), ticks, first_damage_tick (None if nobody is hurt), first_shot_side
  ("attackers", "defenders" or None), climbers_halfway_tick (None under control), firing_unit_seconds (attackers,
  defenders). 'Attackers' are the 8 to 32 climbers; 'defenders' the 16 on layer 3.
- control 4 compares run_fight(control=True) with the lab's own fight of the same forces: asym_play(N, blob, blob)
  with guard_defenders, i.e. the landscape batch's open "blob_v_defenders" build with the roles of 16 and N swapped
  so that N is side 0 (attackers) and the 16 guards are side 1 (the build takes the guard side's headcount as its
  argument). Winner and survivors are compared; side 0 -> "attackers".
- control 6 measures the engine's flip of a unit to layer 3 on a clone type registered with layer_transition_time =
  climb seconds: the layer reads 3 at halfway, so halfway tick x 2 = the whole crossing = climb_seconds x 20 ticks
  within 2 ticks (so the flip lands at climb_seconds x 10, within 2). run_fight's climbers_halfway_tick is also
  required to be within 2 ticks of (order tick + climb_seconds x 10); the order tick is read as
  result.layer_order_tick if present, else the halfway tick minus climb x 10 is only required to be >= 0.
- control 7: run_batch(seed, workers, out_dir=..., smoke=True) returns {"csv": p, "run": p, "page": p}."""
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine  # noqa: E402

try:
    from scripts.skilllab.ground import highground as HG
except Exception as e:  # noqa: BLE001
    HG, HG_ERR = None, e

VANGUARD, TPS = 2, 20


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


def _need():
    assert HG is not None, "scripts/skilllab/ground/highground.py is missing or fails to import: %r" % (HG_ERR,)
    for n in ("HEIGHT_RULES", "CLIMB_SECONDS", "run_fight", "break_even", "run_batch"):
        assert hasattr(HG, n), "scripts/skilllab/ground/highground.py has no %s" % n


def test_control_1_h0_nobody_is_hurt_before_a_climber_is_halfway():
    _need()
    r = HG.run_fight("H0", 8, 16, 1)
    assert r.climbers_halfway_tick is not None and r.climbers_halfway_tick > 0
    assert r.first_damage_tick is None or r.first_damage_tick >= r.climbers_halfway_tick, \
        (r.first_damage_tick, r.climbers_halfway_tick)


def test_control_2_h2_defenders_fire_first_and_h0_nobody_fires_before_the_climb():
    _need()
    h2 = HG.run_fight("H2", 8, 16, 1)
    assert h2.first_shot_side == "defenders", h2.first_shot_side
    h0 = HG.run_fight("H0", 8, 16, 1)
    assert h0.first_damage_tick is None or h0.first_damage_tick >= h0.climbers_halfway_tick


def test_control_3_h0_a_longer_climb_never_raises_the_break_even():
    _need()
    assert HG.break_even("H0", 15, 1) <= HG.break_even("H0", 2, 1)


@pytest.mark.parametrize("attackers", [12, 16, 20])
def test_control_4_the_control_equals_the_labs_open_ground_guard_fight(attackers):
    _need()
    from scripts.skilllab.asym import Side, asym_play
    from scripts.skilllab.fight import fight
    from scripts.skilllab.scenes import guard_defenders
    seed = 3
    ref = fight(guard_defenders(asym_play(attackers, Side("blob"), Side("blob")))(16, False), seed, False)
    ours = HG.run_fight("H0", 8, attackers, seed, control=True)
    word = {"side0": "attackers", "side1": "defenders"}.get(ref.outcome, ref.outcome)
    assert ours.winner == word, (ours.winner, word)
    assert tuple(ours.survivors) == tuple(ref.survivors), (ours.survivors, ref.survivors)


def test_control_5_same_seed_same_inputs_identical_result():
    _need()
    a = HG.run_fight("H2", 4, 16, 5)
    b = HG.run_fight("H2", 4, 16, 5)
    assert a == b


@pytest.mark.parametrize("secs", [2, 8])
def test_control_6_the_layer_change_takes_climb_seconds(lib, secs):
    _need()
    w = lib.new_world(1)
    try:
        lib.disable_abilities(w)
        stats = dict(lib.type_stats(w, VANGUARD), attack_range=0.0, role="Vanguard", ability_id=0,
                     layer_transition_time=float(secs))
        lib.register_unit_type(w, 100, stats)
        u = lib.spawn(w, 100, 0, 6000.0, 6000.0, 2)
        lib.set_layer(w, [u], 3)
        flip = None
        for t in range(1, secs * TPS * 2):
            lib.step(w)
            if lib.unit_layer(w, u) == 3:
                flip = t
                break
    finally:
        lib.free_world(w)
    assert flip is not None, "the unit never reached layer 3"
    assert abs(2 * flip - secs * TPS) <= 2, (flip, secs)
    r = HG.run_fight("H0", secs, 16, 1)
    order = getattr(r, "layer_order_tick", None)
    assert r.climbers_halfway_tick is not None
    if order is not None:
        assert abs((r.climbers_halfway_tick - order) - secs * TPS // 2) <= 2, (order, r.climbers_halfway_tick)


class _Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.svg, self.bad = [], 0, False

    def handle_starttag(self, tag, attrs):
        if tag == "svg":
            self.svg += 1
        if tag not in ("meta", "link", "br", "hr", "img", "input", "path", "rect", "line", "circle", "polyline", "text"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ("path", "rect", "line", "circle", "polyline", "text"):
            return
        if not self.stack or self.stack.pop() != tag:
            self.bad = True


def test_control_7_smoke_batch_writes_files_and_workers_do_not_change_the_csv(tmp_path):
    _need()
    out = {}
    for workers in (1, 3):
        out[workers] = HG.run_batch(11, workers, out_dir=tmp_path / ("w%d" % workers), smoke=True)
        for k in ("csv", "run", "page"):
            assert k in out[workers] and Path(out[workers][k]).is_file(), (k, out[workers])
    html = Path(out[1]["page"]).read_text()
    p = _Tags()
    p.feed(html)
    assert not p.bad and not p.stack, "page is not well-formed: open %r" % (p.stack,)
    assert p.svg == 1, "page has %d svg elements" % p.svg
    assert Path(out[1]["csv"]).read_bytes() == Path(out[3]["csv"]).read_bytes()
