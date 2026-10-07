# spec: Architect rulings A199, A201 (lab rule, provisional: mop-up order) through the production library
"""A side may re-issue its attack-move at the centroid of the enemies it sees once its units have stopped, none has an
enemy in attack range and at least one enemy is seen (no more often than mopup_interval_ticks). mopup=False is today's
single-order play exactly. EXPECTED RED until Setup.mopup, FightResult.mopup_orders and the fight loop land."""
import dataclasses
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, engine, fight, plays, scan  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402

# sha256 over the fights of blob_play(12) scan 11..13, replicates 2, recorded on push/pa-tests-2 before the mop-up existed
OFF_DIGEST = "1e22d27f09d9fe5241c6e970a96599d64105a358e858c73804284404ffa5a54d"


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _with(build, **kw):
    def wrapped(enemy_heads, swap):
        return dataclasses.replace(build(enemy_heads, swap), settings=batches.BASE_SETTINGS, **kw)
    return wrapped


def _digest(result):
    h = hashlib.sha256()
    for c in result.cells:
        for f in c.fights:
            h.update(repr((f.outcome, f.margin, f.strength_left, f.survivors, f.ticks, f.first_contact_tick,
                           f.firing)).encode())
    return h.hexdigest()


def test_off_reproduces_the_single_order_results_byte_for_byte():
    result = scan.scan(_with(plays.blob_play(12, mopup=False)), 12, 11, 13, replicates=2)
    assert _digest(result) == OFF_DIGEST
    assert all(f.mopup_orders is None for c in result.cells for f in c.fights)


def test_the_plays_default_to_mopup_on_and_record_the_interval():
    s = plays.blob_play(8)(8, False)
    assert s.mopup is True and s.mopup_interval_ticks == plays.MOPUP_INTERVAL_TICKS == 200
    assert Setup.__dataclass_fields__["mopup"].default is False   # a bare Setup stays the single-order play


@pytest.fixture(scope="module")
def identical_16_v_8(library):
    return scan.scan(_with(plays.blob_play(16)), 16, 8, 8, replicates=10)


def test_16_against_8_has_no_stalemate_and_16_wins_every_fight(identical_16_v_8):
    fights = identical_16_v_8.cells[0].fights
    assert len(fights) == 20
    assert [f.outcome for f in fights] == ["side0"] * 20


def test_positive_control_without_mopup_the_same_scan_stalls_somewhere(library):
    # the detector control: the stalemates the mop-up removes exist in this lab, at 16 against 16 (A199, 20 of 20)
    off = scan.scan(_with(plays.blob_play(16, mopup=False)), 16, 16, 16, replicates=3)
    assert any(f.outcome == "stalemate" for f in off.cells[0].fights)


def test_mop_up_orders_are_counted_and_bounded_by_the_interval(identical_16_v_8):
    fights = identical_16_v_8.cells[0].fights
    assert all(isinstance(f.mopup_orders, int) and f.mopup_orders >= 0 for f in fights)
    assert sum(f.mopup_orders for f in fights) > 0
    # two sides, one order at most per interval each
    assert all(f.mopup_orders <= 2 * (f.ticks // 200 + 1) for f in fights)


def test_a_side_that_sees_nothing_attack_moves_to_the_enemy_anchor_and_the_fight_resolves(library):
    far = [Group(side=s, unit="Vanguard", count=4, formation="blob", x=x, y=0.0, facing_deg=0.0, layer=0,
                 order="attack_move", goal=(x, 0.0), params={"radius": 100.0}) for s, x in ((0, -1000.0), (1, 1000.0))]
    result = fight.fight(Setup(groups=tuple(far), unit_types={}, mopup=True, settings=batches.BASE_SETTINGS),
                         0, False, engine=library)
    # Lab rule (Westley, Architect 2026-10-07): an unseen side attack-moves to the enemy's starting anchor.  2000 wu apart: unseen, yet close enough to cross inside the stalemate window (6000 wu apart cannot).
    assert result.mopup_orders > 0
    assert result.outcome != "stalemate"


def test_the_rule_is_symmetric_swapping_the_sides_swaps_the_result(library):
    def build(big_side):
        s = plays.blob_play(16)(8, False)
        g0, g1 = s.groups
        sizes = {big_side: 16, 1 - big_side: 8}
        groups = (dataclasses.replace(g0, count=sizes[0]), dataclasses.replace(g1, count=sizes[1]))
        return dataclasses.replace(s, groups=groups, settings=batches.BASE_SETTINGS)
    a = fight.fight(build(0), 3, False, engine=library)
    b = fight.fight(build(1), 3, False, engine=library)
    assert (a.outcome, b.outcome) == ("side0", "side1")
    assert a.survivors == b.survivors[::-1]
    assert a.mopup_orders >= 0 and b.mopup_orders >= 0


def test_rows_and_pages_record_the_setting(tmp_path):
    from scripts.skilllab import rows
    f = scan.scan(_with(plays.blob_play(8)), 8, 8, 8, replicates=1).cells[0].fights[0]
    assert "mopup_orders" in rows.fight_row(f, cell="c")
    assert "mopup_interval_ticks" in batches.MOPUP_NOTE and "Lab rule, provisional" in batches.MOPUP_NOTE


# ---- rule v2 (Architect, provisional): finish fights the wrap and the stuck unit used to leave unfinished ----
def _wrap_setup(mopup, spacing=60.0):
    # a 32-unit line (1860 wu wide at 60: past the 450 wu scatter limit, so it is chunked) against 3 idle units
    line = Group(side=0, unit="Vanguard", count=32, formation="line", x=-400.0, y=0.0, facing_deg=0.0, layer=0,
                 order="attack_move", goal=(-100.0, 0.0), params={"spacing": spacing})
    rem = Group(side=1, unit="Vanguard", count=3, formation="blob", x=400.0, y=0.0, facing_deg=180.0, layer=0,
                order="idle", goal=None, params={"radius": 20.0})
    return Setup(groups=(line, rem), unit_types={}, mopup=mopup, settings=batches.BASE_SETTINGS, max_ticks=6000)


class _Spy:
    """The library, recording the attack-move goals issued after the first step (the re-orders)."""
    def __init__(self, inner):
        self._inner, self.stepped, self.goals = inner, False, []
    def __getattr__(self, name):
        return getattr(self._inner, name)
    def step(self, w):
        self.stepped = True
        return self._inner.step(w)
    def order_attack_move(self, w, ids, x, y):
        if self.stepped:
            self.goals.append((round(x, 3), round(y, 3)))
        return self._inner.order_attack_move(w, ids, x, y)


def test_the_wrap_case_finishes_with_the_rule_and_does_not_without_it(library):
    on = fight.fight(_wrap_setup(True), 1, False, engine=library)
    assert on.outcome == "side0" and on.survivors == (32, 0) and on.mopup_orders >= 1
    off = fight.fight(_wrap_setup(False), 1, False, engine=library)
    assert off.outcome == "stalemate"   # positive control: the single order leaves the remnant standing


def test_every_chunk_of_a_re_order_is_aimed_at_the_same_point_with_no_offset(library):
    spy = _Spy(library)
    fight.fight(_wrap_setup(True), 1, False, engine=spy)
    assert len(spy.goals) >= 2 and len(set(spy.goals)) == 1   # several chunks, one point


class _Stub:
    """An engine with fixed positions; unit 1 (mine) has a destination, enemies at the given points."""
    def __init__(self, pos, dest):
        self.pos, self.dest = pos, dest
    def unit_pos(self, w, u): return self.pos[u]
    def unit_layer(self, w, u): return 0
    def unit_destination(self, w, u): return self.dest.get(u)
    def can_see(self, w, u, e): return True


def test_a_unit_with_a_destination_that_has_not_moved_does_not_block_the_re_order():
    from scripts.skilllab import mopup
    eng = _Stub({1: (0.0, 0.0), 2: (10.0, 0.0), 10: (900.0, 0.0), 11: (700.0, 0.0)}, {1: (900.0, 0.0)})
    ranges = {1: 100.0, 2: 100.0}
    alive = {1, 2, 10, 11}
    still = {1: (0.0, 0.0), 2: (10.0, 0.0)}
    assert mopup.mopup_goal(eng, None, [1, 2], [10, 11], ranges, alive, still) == (700.0, 0.0)   # nearest to the centroid
    moving = {1: (-31.0, 0.0), 2: (10.0, 0.0)}
    assert mopup.mopup_goal(eng, None, [1, 2], [10, 11], ranges, alive, moving) is None           # moved 31 wu: blocks


def test_the_rule_text_is_printed_in_the_header():
    assert "Lab rule, provisional (v2)" in batches.MOPUP_NOTE
