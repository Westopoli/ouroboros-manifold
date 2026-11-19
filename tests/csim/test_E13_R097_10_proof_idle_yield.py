# Rule pins: R-097-10
"""E-13 R-097-10 proof (Round 5, G8: the seven qualifications of docs/method/requirements.md Proof): who takes the push of a colliding pair, and how long the push pass runs.

Rule word for word (docs/bible/epics/E-13-movement-and-command.md, R-097-10, as it reads on this branch):
  R-097-10  "Given one unit of the pair is stationary (no move target, or halted by engagement), When pushed, Then it moves 0 and the other takes the full displacement, except that an idle unit (no move target, not
            engaged) takes the full displacement from a mover of its own side and none from an enemy mover, which takes all of it; given both are stationary, they split the displacement equally (until 2026-11-18 only
            when either had been displaced earlier in the tick ...; DEC-draws-round6-2026-11-18). Every unit starts pair checks, moving or stopped, so a unit that walks into a stopped one is pushed out; the push pass repeats up to 10 times a tick until no pair is closer than 30 wu,
            or until a pass displaces no unit by more than `COLLISION_SETTLE_EPS = 0.1` wu (that pass is applied; ALG-68). This is a deliberate difference from the Python reference, whose rule let a higher-id unit stack on
            a stopped lower-id one (Westley, 2026-10-02)."
The proof is the one function `test_R_097_10_proof_*` below; the controls are the `test_R_097_10_control_*` functions, each of which changes one thing of a proof scene and asserts the opposite.

Clauses and the scene that asserts each one, every tick, through om_tactical_step (the tick, as play does):
  (1) a stationary unit moves 0 and the other takes the full displacement   scenes ENEMY (an idle enemy Supply) and ENGAGED (an own Vanguard that holds a target and fires): on every tick the stationary unit is where
      it was, bit for bit, and from the first contact on the pair is 30 wu apart (the mover alone gave way, by the whole overlap).
  (2) an idle unit takes the full displacement from a mover of its own side  scene OWN: M (side 0) walks to a point behind an idle side 0 Vanguard. On every tick M stands where it stands alone (the lone control run,
      same scene without the idle unit, within POS_TOL: it takes none), and the idle unit is moved along the line from M by exactly the overlap, whatever the id order.
  (3) none from an enemy mover, which takes all of it                       scene ENEMY (the idle unit and the mover are on different sides), and the control makes them one side.
  (4) both stationary: split equally  scene SPLIT: M pushes idle own I1 into idle own I2 (both stationary; here I1 was displaced earlier in the tick, the case the rule once required; the rule no longer asks it, and a pair nothing
      has displaced is the scene of tests/csim/test_E13_R097_10_halted_pair_separates.py): on every tick the three positions are those of the rule applied by the reference model below, which splits the I1/I2 overlap equally.
      A model that does not split gives other positions (control).
  (5) the pass repeats until no pair is closer than 30 wu, or a pass moves no unit by more than 0.1 wu         scene ROW: M walks into a row of four idle own units that are only 1 wu apart beyond 30; the model runs up to 10
      passes and stops by the two ends of the rule; on every tick the engine agrees with it to MODEL_TOL, and the model with 3 passes, or without the settle stop, or with a stricter one, disagrees (control).
  (Every unit starts pair checks: in OWN the mover is the one that walks into the stopped unit, whichever id is lower.)

Reference model (`_settle`): the rule applied by the test to the positions of the tick's step, ids ascending, partners ascending, live positions, up to 10 passes, a pass that moves nothing ends it, a pass that moves no unit by more
than 0.1 wu is applied and ends it. It restates the rule's text only; the engine's code is not read by the test. The mover's position is read from the engine after the tick, which is where it stood before the push because
the rule gives it none (clause 2), asserted in the same tick.

Configuration: the shipped one for a csim scene (what scripts/skilllab/arena/run.py `fight(.., "on")` sets, read 2026-11-17): a 2000 x 2000 canvas, abilities off, ground era (om_set_era_kind 1), the Vanguard
reach 0 up 1 down (the Supply is a type the engine takes no reach for), the Vanguard set to the walking kind (the lab's `walk_on_ground`), steering, route around terrain and targeting by sight at their defaults (on). What differs from the lab, and why: the geometry is units only,
no hill, box or obstacle (the push is between units; terrain adds the slide of R-001-07 that is not this rule's), and the side-1 Supply never fires and no other enemy exists, so that only the test decides who is idle.
Vanguard: 4 wu a tick, collision diameter 30 wu.

Detector bounds (not rules; Westley's to change): POS_TOL 0.05 wu (numeric slack of the C's cheap trig, as the PP files), CONTACT 0.5 wu (a pair within 30.5 wu has touched), MODEL_TOL 1e-6 wu (the model uses the engine's
own arithmetic; a pair resolved in a different order or share differs by far more), DRAFT-settle-residual: SETTLE_RESIDUAL = 0.25 wu (the most a pair may remain closer than 30 wu at a tick's end when the pass ended by the
settle rule; twice COLLISION_SETTLE_EPS plus slack).
Recorded breaks (each built in a scratch copy of csrc with `cc`, loaded through OM_CSIM_LIB, and run on 2026-11-17; the tree is untouched; red ids in parentheses):
  nosplit  two stationary units: the lower id takes all of the overlap instead of half (clause 4: the SPLIT and ROW proofs and the model control)
  noyield  om_move_yields returns 0, so an idle unit never yields (clause 2: both OWN proofs, SPLIT, ROW, both controls)
  anyside  om_move_yields without the same-side test (clause 3: the ENEMY proof)
  stathalf a stationary unit that does not yield takes half of the push, not 0 (clause 1: ENEMY and ENGAGED)
  engidle  the idle flag ignores a held target, so an engaged unit yields (clause 1, not-idle half: ENGAGED)
  passes3  COLLISION_PASSES 10 replaced by 3 (clause 5: SPLIT, ROW, the model control)
  eps0     COLLISION_SETTLE_EPS 0.1 replaced by 0.0 (clause 5: SPLIT, ROW, the model control)
"""
import copy
import ctypes
import math

import pytest

from conftest import OMFeature
from test_PP_unit_support import SUPPLY, VANGUARD, dest, pos, spawn, step
from test_E13_R099_05_giveup_counts_only_ticks_without_progress import check_destination_by_count

WALKING = 1                         # OM_MOVE_WALKING
ERA_GROUND = 1
CANVAS = 2000.0
DIAMETER = 30.0                     # R-097-05: 2 x radius 15
PASSES = 10                         # COLLISION_PASSES
SETTLE_EPS = 0.1                    # COLLISION_SETTLE_EPS
POS_TOL = 0.05                      # numeric slack, not a rule threshold
CONTACT = 0.5                       # detector bound
MODEL_TOL = 1e-6                    # detector bound
SETTLE_RESIDUAL = 0.25              # DRAFT-settle-residual
START = (300.0, 500.0)
IDLE_XY = (500.0, 500.0)
GOAL_BEHIND = (520.0, 500.0)        # 20 wu behind the idle unit: inside its 30 wu, reachable only by a push
GOAL_FAR = (1500.0, 500.0)          # the mover keeps walking through the whole run


# ------------------------------------------------------------------ harness

def _world(lib, wf):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    lib.om_tactical_disable_abilities(w)
    assert lib.om_set_era_kind(w, ERA_GROUND) == 0
    assert lib.om_roster_set_movement_kind(w, VANGUARD, WALKING) == 0
    assert lib.om_roster_set_reach(w, VANGUARD, 0, 1) == 0
    return w


def _move(lib, w, uid, x, y):
    arr = (ctypes.c_uint32 * 1)(uid)
    return lib.om_command_move.raw(w, arr, 1, float(x), float(y))


def _dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _run(lib, w, ids, ticks):
    """Per tick, after om_tactical_step: {"p": {id: (x, y)}, "has": {id: has a destination}}."""
    out = []
    for _ in range(ticks):
        step(lib, w)
        out.append({"p": {u: pos(lib, w, u) for u in ids}, "has": {u: dest(lib, w, u)[0] == 1 for u in ids}})
    return out


def _lone(lib, wf, goal, ticks):
    """The mover's positions with nothing in its way: the control run of the scene, per tick."""
    w = _world(lib, wf)
    m = spawn(lib, w, VANGUARD, 0, *START)
    assert _move(lib, w, m, *goal) == 0
    return [r["p"][m] for r in _run(lib, w, [m], ticks)]


def _scene(lib, wf, specs, mover_id_slot, goal):
    """Spawn `specs` ((unit type, side, x, y), in spawn order) and order the unit at index `mover_id_slot` to `goal`. Returns (world, [ids])."""
    w = _world(lib, wf)
    ids = [spawn(lib, w, t, f, x, y) for t, f, x, y in specs]
    assert _move(lib, w, ids[mover_id_slot], *goal) == 0
    return w, ids


# ------------------------------------------------------------------ the rule as a model (clauses 4 and 5, and the shape of 1 to 3)

def _settle(units, passes=PASSES, eps=SETTLE_EPS, split_stationary=True):
    """R-097-10 applied to `units`: a list (ascending id) of dicts x, y, stat (stationary), idle, side. Returns (positions, splits, ended): splits counts pair resolutions of two stationary units; ended is "clear" (a pass found
    no pair closer than 30 wu), "settled" (a pass moved no unit by more than eps) or "cap" (the passes ran out)."""
    u = copy.deepcopy(units)
    splits, ended = 0, "cap"
    for _ in range(passes):
        before = [(a["x"], a["y"]) for a in u]
        moved_any = False
        for i, a in enumerate(u):
            for b in u[i + 1:]:
                dx, dy = b["x"] - a["x"], b["y"] - a["y"]
                d = math.sqrt(dx * dx + dy * dy)
                if d >= DIAMETER:
                    continue
                assert d > 1e-9, "model scene broken: two units on one spot"
                ov = DIAMETER - d
                ux, uy = dx / d, dy / d
                if a["stat"] and b["stat"]:
                    splits += 1
                    if split_stationary:
                        sh_a = sh_b = 0.5
                    else:
                        sh_a, sh_b = 1.0, 0.0           # the break: the lower id takes it all
                elif a["stat"]:
                    sh_a, sh_b = (1.0, 0.0) if (a["idle"] and a["side"] == b["side"]) else (0.0, 1.0)
                elif b["stat"]:
                    sh_a, sh_b = (0.0, 1.0) if (b["idle"] and a["side"] == b["side"]) else (1.0, 0.0)
                else:
                    sh_a = sh_b = 0.5
                a["x"] -= ux * ov * sh_a; a["y"] -= uy * ov * sh_a
                b["x"] += ux * ov * sh_b; b["y"] += uy * ov * sh_b
                moved_any = True
        if not moved_any:
            ended = "clear"
            break
        if eps > 0 and all(math.hypot(a["x"] - bx, a["y"] - by) <= eps for a, (bx, by) in zip(u, before)):
            ended = "settled"
            break
    return [(a["x"], a["y"]) for a in u], splits, ended


def _model_trace(tr, ids, mover, idle_flags, sides, **kw):
    """For each tick the model's positions of `ids`, started from the tick's start positions (the previous tick's, the mover's own step taken from the engine's mover position). Returns (list of position lists, total splits, how each tick's pass ended)."""
    out, splits, ends = [], 0, []
    prev = None
    for k, row in enumerate(tr):
        start = {u: (prev[u] if prev else row["p"][u]) for u in ids}
        start[mover] = row["p"][mover]                   # the mover takes no push: where it stands after the tick is where its step ended
        units = [{"x": start[u][0], "y": start[u][1], "stat": u != mover, "idle": idle_flags[u], "side": sides[u]} for u in ids]
        pos_after, s, ended = _settle(units, **kw)
        splits += s
        out.append(pos_after)
        ends.append(ended)
        prev = {u: row["p"][u] for u in ids}
    return out, splits, ends


# ------------------------------------------------------------------ the proof

def _assert_own_idle_takes_everything(lib, wf, slot):
    """Clause 2, one id order: `slot` is the mover's index in the spawn order (0 mover first, 1 idle unit first)."""
    specs = [(VANGUARD, 0, *START), (VANGUARD, 0, *IDLE_XY)]
    if slot == 1:
        specs.reverse()
    w, ids = _scene(lib, wf, specs, slot, GOAL_BEHIND)
    m, idle = ids[slot], ids[1 - slot]
    ticks = 80
    lone = _lone(lib, wf, GOAL_BEHIND, ticks)
    tr = _run(lib, w, ids, ticks)
    prev_idle, touched = IDLE_XY, 0
    for k, row in enumerate(tr):
        if not row["has"][m]:
            break                                           # the mover has arrived on this tick, so it is stationary too (clause 4 takes over); the clause asserted here ends
        assert _dist(row["p"][m], lone[k]) <= POS_TOL, "tick %d: the mover took part of the push: at %s, alone it is at %s" % (k + 1, row["p"][m], lone[k])
        d_before = _dist(lone[k], prev_idle)
        ov = max(0.0, DIAMETER - d_before)
        got = _dist(row["p"][idle], prev_idle)
        assert abs(got - ov) <= POS_TOL, "tick %d: the idle own unit moved %.3f wu, the overlap was %.3f wu (it takes the full displacement)" % (k + 1, got, ov)
        if ov > 0:
            touched += 1
            ux, uy = (prev_idle[0] - lone[k][0]) / d_before, (prev_idle[1] - lone[k][1]) / d_before
            moved = (row["p"][idle][0] - prev_idle[0], row["p"][idle][1] - prev_idle[1])
            assert abs(moved[0] - ux * ov) <= POS_TOL and abs(moved[1] - uy * ov) <= POS_TOL, "tick %d: pushed along %s, the line from the mover is %s" % (k + 1, moved, (ux * ov, uy * ov))
        prev_idle = row["p"][idle]
    assert touched >= 5, "premise: the mover pushed the idle unit on only %d ticks" % touched
    assert not tr[-1]["has"][m] and _dist(tr[-1]["p"][m], GOAL_BEHIND) <= 5.0, "the mover did not arrive: at %s" % (tr[-1]["p"][m],)


def _assert_stationary_moves_zero(lib, wf, kind):
    """Clauses 1 and 3: an enemy idle unit (ENEMY) or an engaged own unit (ENGAGED) in the way of M, whose goal lies inside the unit's 30 wu. The unit moves exactly 0 on every tick, and from the first contact the pair is
    30 wu apart on every tick (the mover alone gave way)."""
    specs = [(VANGUARD, 0, *START)]
    if kind == "ENEMY":
        specs.append((SUPPLY, 1, *IDLE_XY))
    else:
        specs += [(VANGUARD, 0, *IDLE_XY), (SUPPLY, 1, 500.0, 700.0)]
    w, ids = _scene(lib, wf, specs, 0, IDLE_XY if kind == "ENGAGED" else GOAL_BEHIND)
    m, s = ids[0], ids[1]
    if kind == "ENGAGED":
        lib.om_unit_set_hp(w, ids[2], 1.0e6)
    held = []
    tr = []
    for _ in range(140):
        step(lib, w)
        tr.append({"p": {u: pos(lib, w, u) for u in ids}, "has": {u: dest(lib, w, u)[0] == 1 for u in ids}})
        held.append(lib.om_unit_get_target(w, s))
    if kind == "ENGAGED":
        assert held[0] == ids[2] and lib.om_unit_get_hp(w, ids[2]) < 1.0e6, "premise: the stationary Vanguard holds the Supply as its target and fires (target %s)" % held[0]
    else:
        assert all(h == 0 for h in held), "premise: the idle enemy Supply holds a target"
    pushed = 0
    for k, row in enumerate(tr):
        assert row["p"][s] == IDLE_XY, "tick %d: the stationary unit moved to %s (it moves 0)" % (k + 1, row["p"][s])
        d = _dist(row["p"][m], row["p"][s])
        assert d >= DIAMETER - POS_TOL, "tick %d: the pair is %.3f wu apart after the push (the mover takes the whole overlap)" % (k + 1, d)
        pushed += abs(d - DIAMETER) <= POS_TOL            # a tick on which the mover was pressed to the circle
    assert pushed >= 5, "premise: the mover was pushed out of the stationary unit on %d ticks only" % pushed
    goal = IDLE_XY if kind == "ENGAGED" else GOAL_BEHIND
    check_destination_by_count([r["has"][m] for r in tr], [r["p"][m] for r in tr], goal, START, "%s: the mover held at the stationary unit" % kind)


def _row_scene(lib, wf, mover_slot, specs_rest, ticks=90):
    specs = list(specs_rest)
    specs.insert(mover_slot, (VANGUARD, 0, *START))
    w, ids = _scene(lib, wf, specs, mover_slot, GOAL_FAR)
    return w, ids, _run(lib, w, ids, ticks)


# The walking mover bends away from the straight line (the lone run is at y 549 from x 500 on), so the idle units stand on its lone path.
SPLIT_REST = [(VANGUARD, 0, 560.0, 549.0), (VANGUARD, 0, 585.0, 569.0)]
ROW_REST = [(VANGUARD, 0, 560.0, 549.0), (VANGUARD, 0, 591.0, 549.0), (VANGUARD, 0, 622.0, 549.0), (VANGUARD, 0, 653.0, 549.0)]


def _model_run(lib, wf, rest, slot, **kw):
    w, ids, tr = _row_scene(lib, wf, slot, rest)
    m = ids[slot]
    idle = {u: u != m for u in ids}
    sides = {u: 0 for u in ids}
    return tr, ids, m, _model_trace(tr, ids, m, idle, sides, **kw)


def _max_gap(tr, ids, model_pos):
    """The largest distance between a unit's engine position and the model's, over every tick."""
    return max(_dist(row["p"][u], model_pos[k][i]) for k, row in enumerate(tr) for i, u in enumerate(ids))


@pytest.mark.parametrize("slot", [0, 1], ids=["mover_lower_id", "idle_lower_id"])
def test_R_097_10_proof_an_idle_unit_takes_the_full_displacement_from_a_mover_of_its_own_side(lib, world_factory, slot):
    """R-097-10 (full text in the module docstring), clause 2, every tick through om_tactical_step: "an idle unit (no move target, not engaged) takes the full displacement from a mover of its own side" and "Every unit
    starts pair checks, moving or stopped, so a unit that walks into a stopped one is pushed out". M (side 0) is ordered to a point 20 wu behind an idle side 0 Vanguard; on every tick M is where it is alone and the idle
    unit moved by exactly the overlap, along the line from M. Both id orders."""
    _assert_own_idle_takes_everything(lib, world_factory, slot)


@pytest.mark.parametrize("kind", ["ENEMY", "ENGAGED"])
def test_R_097_10_proof_a_stationary_unit_moves_0_the_other_takes_the_full_displacement_and_an_enemy_mover_takes_all(lib, world_factory, kind):
    """R-097-10 clauses 1 and 3, every tick: "Given one unit of the pair is stationary (no move target, or halted by engagement), When pushed, Then it moves 0 and the other takes the full displacement, except that an idle
    unit ... takes ... none from an enemy mover, which takes all of it". ENEMY: M (side 0) pushes against an idle side 1 Supply; ENGAGED: M pushes against an own Vanguard that holds a target and fires (halted by
    engagement; not idle). The stationary unit stands where it was on every tick, bit for bit; from the first contact the pair is 30 wu apart on every tick.
    The mover is a lone mover held inside the 75 wu disc of its point (30 wu away in ENGAGED, 10 wu in ENEMY), so its order ends by R-099-05 (Round 6 E2): its destination is kept on every tick through its 39th held
    tick (a tick on which it comes nearer is not counted), cleared on the 40th, and it is stationary after (Test-defect: until 2026-11-18 this asserted that it still had its destination at tick 100; the run is now 140 ticks)."""
    _assert_stationary_moves_zero(lib, world_factory, kind)


def _check_against_model(tr, ids, model):
    """Every tick: the engine's positions are the model's; a pass that ended "clear" left no pair closer than 30 wu; one that ended "settled" left none closer than 30 - SETTLE_RESIDUAL. Returns the endings seen."""
    model_pos, _, ends = model
    gap = _max_gap(tr, ids, model_pos)
    assert gap <= MODEL_TOL, "the engine's positions differ from the rule's by up to %.6f wu" % gap
    for k, row in enumerate(tr):
        ps = [row["p"][u] for u in ids]
        worst = min(_dist(ps[i], ps[j]) for i in range(len(ps)) for j in range(i + 1, len(ps)))
        if ends[k] == "clear":
            assert worst >= DIAMETER - POS_TOL, "tick %d: the pass ended with no pair closer than 30 wu, yet a pair is %.3f wu apart" % (k + 1, worst)
        elif ends[k] == "settled":
            assert worst >= DIAMETER - SETTLE_RESIDUAL, "tick %d: the pass settled, yet a pair is %.3f wu apart" % (k + 1, worst)
    return set(ends)


@pytest.mark.parametrize("slot", [0, 2], ids=["mover_lowest_id", "mover_highest_id"])
def test_R_097_10_proof_two_stationary_units_split_a_displacement_the_mover_gave_one_of_them(lib, world_factory, slot):
    """R-097-10 clause 4, every tick: "given both are stationary, they split the displacement equally" (the clause no longer asks that either was displaced earlier in the tick; this scene is one in which I1 was). M walks to the side 0 idle Vanguard I1 at (560,549); I2, also idle side 0,
    stands at (585,569), 32 wu from I1. M pushes I1 (the idle unit takes the full displacement), which brings I1 within 30 wu of I2: both stationary, I1 displaced earlier in the tick, so each takes half of that overlap, and the pass
    repeats. On every tick the three positions are the reference model's to MODEL_TOL (model: ids ascending, up to 10 passes). Premise: the model resolves a pair of two stationary units on 4 ticks or more of the run
    (the control tells the split from the lower id taking all)."""
    tr, ids, m, model = _model_run(lib, world_factory, SPLIT_REST, slot)
    assert model[1] >= 4, "premise: only %d resolutions of two stationary units in the run" % model[1]
    _check_against_model(tr, ids, model)


@pytest.mark.parametrize("slot", [0, 4], ids=["mover_lowest_id", "mover_highest_id"])
def test_R_097_10_proof_the_push_pass_repeats_until_no_pair_is_closer_than_30_wu_or_a_pass_moves_no_unit_over_0_1_wu(lib, world_factory, slot):
    """R-097-10 clause 5, every tick: "the push pass repeats up to 10 times a tick until no pair is closer than 30 wu, or until a pass displaces no unit by more than COLLISION_SETTLE_EPS = 0.1 wu (that pass is applied)".
    M walks into a row of four idle side 0 Vanguards 1 wu apart beyond 30 (560, 591, 622, 653; y 549, the mover's own line): the push has to travel down the row, which one pass cannot do. On every tick the engine's positions
    are the reference model's to MODEL_TOL, a tick the model ends with no pair under 30 wu has none in the engine, and one it ends by the settle rule leaves none closer than 30 - SETTLE_RESIDUAL. Premise: the run
    has ticks of every ending, the pass cap, the settle stop and the clear pass (this scene and the SPLIT one)."""
    tr, ids, m, model = _model_run(lib, world_factory, ROW_REST, slot)
    seen = _check_against_model(tr, ids, model)
    tr2, ids2, m2, model2 = _model_run(lib, world_factory, SPLIT_REST, 0)
    seen |= _check_against_model(tr2, ids2, model2)
    assert seen == {"clear", "settled", "cap"}, "premise: the scenes end the pass by %s only" % sorted(seen)


# ------------------------------------------------------------------ controls (filled: one change to a proof scene, the opposite outcome)

def test_R_097_10_control_the_unit_in_the_way_is_pushed_when_it_is_idle_and_of_the_movers_side(lib, world_factory):
    """Control for clauses 1 and 3 (ENEMY): the ENEMY scene with the Supply a side 0 Supply (idle, the mover's own side). It is pushed (it leaves its spot) and the mover walks on to its goal inside the old 30 wu, so
    the 'moves 0' assertion of the proof fails here. And for clause 1 (ENGAGED): the ENGAGED scene without the Supply to shoot at (the Vanguard is idle) is pushed too."""
    w, ids = _scene(lib, world_factory, [(VANGUARD, 0, *START), (SUPPLY, 0, *IDLE_XY)], 0, GOAL_BEHIND)
    tr = _run(lib, w, ids, 100)
    assert tr[-1]["p"][ids[1]] != IDLE_XY and _dist(tr[-1]["p"][ids[1]], IDLE_XY) >= 5.0, "an idle own unit was not pushed: at %s" % (tr[-1]["p"][ids[1]],)
    assert _dist(tr[-1]["p"][ids[0]], GOAL_BEHIND) <= 5.0 and not tr[-1]["has"][ids[0]], "the mover did not arrive"
    w, ids = _scene(lib, world_factory, [(VANGUARD, 0, *START), (VANGUARD, 0, *IDLE_XY)], 0, IDLE_XY)
    tr = _run(lib, w, ids, 100)
    assert lib.om_unit_get_target(w, ids[1]) == 0 and _dist(tr[-1]["p"][ids[1]], IDLE_XY) >= 5.0, "an own Vanguard with nothing to shoot at did not yield"


def test_R_097_10_control_the_model_tells_the_clauses_apart_on_the_engine_run(lib, world_factory):
    """Control for clauses 4 and 5: the engine run of the SPLIT and ROW scenes differs, by more than 1000 x MODEL_TOL on some tick, from the model with the lower id taking all of a two-stationary pair, from the model with
    3 passes, from the model with no settle stop (eps 0) and from the model with eps 0.5; and agrees with the model of the rule (the proof's assertion). The scenes therefore fail the proof against an engine with
    any of these breaks."""
    tr, ids, m, good = _model_run(lib, world_factory, SPLIT_REST, 0)
    assert _max_gap(tr, ids, good[0]) <= MODEL_TOL
    _, _, _, nosplit = _model_run(lib, world_factory, SPLIT_REST, 0, split_stationary=False)
    assert _max_gap(tr, ids, nosplit[0]) > 1000 * MODEL_TOL, "the SPLIT scene does not tell a split from the lower id taking all"
    tr, ids, m, good = _model_run(lib, world_factory, ROW_REST, 0)
    assert _max_gap(tr, ids, good[0]) <= MODEL_TOL
    for kw in ({"passes": 3}, {"eps": 0.0}, {"eps": 0.5}):
        _, _, _, alt = _model_run(lib, world_factory, ROW_REST, 0, **kw)
        assert _max_gap(tr, ids, alt[0]) > 1000 * MODEL_TOL, "the ROW scene does not tell the rule from %s" % (kw,)
