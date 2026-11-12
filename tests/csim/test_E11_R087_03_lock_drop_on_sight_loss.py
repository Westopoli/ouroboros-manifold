"""E-11 R-087-03 / R-087-08 (engine rules round 3, T9 item 1): a lock ends when the target leaves its side's sight, on that tick or the next.

Rule words, word for word (docs/bible/epics/E-11-units-and-combat.md):
  R-087-03  "... the target is a lock: the unit keeps it, whatever else comes nearer, until the target dies, leaves its side's sight, or the player gives the unit a new order ..."
  R-087-08  "... each unit validates its lock every tick (R-087-03) ..."
Rule pins: R-087-03, R-087-08, R-093-02.

This file holds ONLY the green control of the defect. The defect itself (a lock dropped one tick early, on a sight check made inside the holder's AI turn on half-moved positions: an observer
of lower id has stepped, the target of higher id has not) is proved by tests/skilllab/arena/test_engine_rules_r3_sight_lock.py on L-0084 seed 1. A csim scene of the small geometry could not be
built within reason, measured 2026-11-11 on main 7ba38983:
  * a unit ordered to move (or attack-move) steps in the movement pass, after every AI turn, so an observer and a target that both walk never show a half-moved pair to the holder;
  * only a unit that steps INSIDE its AI turn (a guard returning to its post, a spot or flinch step: csrc/unit.c om_tac_step_leashed) leaves the mixed state, and only for the targets of higher id
    that then still stand on the old place; with a wall (om_map_block_rect, blocks at 100 wu cell granularity) between guard-observer O, holder G (a guard, behind the wall, range 300) and a walking
    target T, about 300 scenes were swept (O start y 440 to 543, T y 505, 515 and 530; Raider and Warden observers, guard and idle holders) and none showed a drop with the side seeing T at both ends of the tick: the observer's
    return step moved in x or y by the route planner's choice, not along the line the geometry needs, and T's first step after an order is 18.7 wu, not its pace. No tuning of the sweep produced the
    pair "seen before, blocked half-moved, seen after".
Scene (the existing lock control of tests/csim/test_E11_R087_03_target_lock.py, with the tick counted): a 2000 x 2000 canvas, an idle Raider U at (260, 400), two tough Supplies of faction 1,
BEHIND at (440, 400) and OTHER at (260, 640); targeting by sight on (the default). U locks BEHIND (the nearest); a wall (cell column 300..400, y 300..500) is then built between them.
Measured 2026-11-11 (main 7ba38983): the side sees BEHIND before the wall and not after it; U's target per step after the wall is none, none, none, OTHER (it drops BEHIND on the first step and takes OTHER at its cohort turn).
"""
from conftest import OMFeature
from test_PP_unit_support import RAIDER, SUPPLY, spawn, step, target

BIG_HP = 1.0e6
ACQUIRE_TICKS = 12
LAG_TICKS = 1      # DRAFT-lock-lag-ticks: dropped on the tick the sight is gone or the next


def _scene(lib, wf):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, 2000.0, 2000.0) == 0
    u = spawn(lib, w, RAIDER, 0, 260, 400)
    behind = spawn(lib, w, SUPPLY, 1, 440, 400)
    other = spawn(lib, w, SUPPLY, 1, 260, 640)
    for x in (behind, other):
        lib.om_unit_set_hp(w, x, BIG_HP)
    for _ in range(ACQUIRE_TICKS):
        step(lib, w)
        if target(lib, w, u) == behind:
            break
    assert target(lib, w, u) == behind, "scene broken: U did not lock the nearer Supply BEHIND (target %s)" % target(lib, w, u)
    return w, u, behind, other


def test_R_087_03_control_a_target_the_side_stops_seeing_is_dropped_on_that_tick_or_the_next(lib, world_factory):
    """R-087-03 'until the target ... leaves its side's sight' + R-087-08 'validates its lock every tick' (control, green today and after): a wall between U and the Supply it locks blinds the side to it
    (premise: om_player_can_see 1 before the wall, 0 after, and 1 for OTHER); within LAG_TICKS = 1 ticks after the tick at whose end the side no longer sees it, U no longer holds it. Proves a lock does
    end when the sight goes (a fix that never drops, or drops only on a cohort turn, turns it red)."""
    w, u, behind, other = _scene(lib, world_factory)
    assert lib.om_player_can_see(w, 0, behind) == 1, "premise: the side sees BEHIND before the wall"
    assert lib.om_map_block_rect(w, 310.0, 310.0, 390.0, 490.0, 0, 4) == 0
    assert lib.om_player_can_see(w, 0, behind) == 0, "premise: the wall blinds the side to BEHIND"
    assert lib.om_player_can_see(w, 0, other) == 1, "premise: the side still sees OTHER"
    held = []
    for _ in range(1 + LAG_TICKS):
        step(lib, w)
        held.append(target(lib, w, u))
    assert held[-1] != behind, "U still holds the Supply the side stopped seeing, %d tick(s) after: targets per tick %s" % (1 + LAG_TICKS, held)
