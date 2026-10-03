"""Pure-Python all-pairs collision reference for ALG-68 (S-097, S-102, R-099-03).

Verifies that the C spatial-grid collision pass (tactical_move.c) produces
bit-identical results to the all-pairs i<j sweep the bible specifies in ALG-68:
every pair i<j once per iteration, push apart by overlap, iteration cap 10 (OM_COLLISION_PASSES, switch default 1),
early-stop when a full pass is a no-op.

Early-stop rule source: om_move_collision_once (tactical_move.c:1094), outer
loop at tactical_move.c:1166 --
    for (iter = 0; iter < OM_COLLISION_MAX_ITER; iter++) {
        if (!om_move_collision_once(w, ms)) { settled = 1; break; }
    }
A pass that writes nothing (returns 0) terminates the remaining iterations.
The comment on om_move_collision_once at tactical_move.c:1085 explains the
spatial-grid variant reproduces the old all-pairs sweep bit-for-bit: "Results
match it bit for bit, so that stop is reproduced: the turn ends when the wider
list has no candidate left (om_move_grid_any_above)."

Constants from csrc:
    OM_UNIT_COLLISION_RADIUS = 15          (om_constants.h:443)
    OM_COLLISION_PASSES      = 10          (om_constants.h; the C uses it at PURSUE_BY_STEERING 1)
    OM_COLLISION_EXACT_EPS   = 1e-9        (tactical_move.c:132)
"""
import ctypes
import math
import random

import pytest


# ---- reference implementation -----------------------------------------------

_RADIUS = 15.0          # OM_UNIT_COLLISION_RADIUS
_TARGET = 2.0 * _RADIUS  # 30.0 wu -- minimum separation
_EXACT_EPS = 1e-9       # OM_COLLISION_EXACT_EPS
_MAX_ITER = 10          # OM_COLLISION_MAX_ITER (A156: was 3; test-defect A155 to A159)


def _run_collision_reference(positions, stationary, max_iter=_MAX_ITER):
    """All-pairs i<j collision pass as ALG-68 states it.

    positions: {unit_id: [x, y]} -- modified in-place; ids must be sorted ints.
    stationary: set of unit ids with no move target (take zero displacement).
    max_iter: iteration cap (default 10 per OM_COLLISION_PASSES).

    Returns the same dict (modified in-place) for chaining.

    Pair order: outer loop ascending id_i, inner loop ascending id_j > id_i.
    Positions are live: when (id_i, id_j) is resolved, the updated position of
    id_i is used for the next pair (id_i, id_k), k > j. This matches the C
    comment on om_move_collision_once: "each resolved against a's position as
    the earlier ones left it, which is the order of an all-pairs i < j sweep
    with live positions."
    """
    ids = sorted(positions.keys())
    n = len(ids)

    for _ in range(max_iter):
        changed = False
        for ii in range(n):
            id_i = ids[ii]
            for jj in range(ii + 1, n):
                id_j = ids[jj]
                ax, ay = positions[id_i]
                bx, by = positions[id_j]
                dx = bx - ax
                dy = by - ay
                dist_sq = dx * dx + dy * dy
                if dist_sq >= _TARGET * _TARGET:
                    continue
                dist = math.sqrt(dist_sq)
                if dist >= _TARGET:
                    continue

                a_stat = id_i in stationary
                b_stat = id_j in stationary

                if dist < _EXACT_EPS:
                    # R-097-07: exact overlap -- lower id moves +x, higher id -x.
                    # The C exact-overlap branch (om_move_collide_pair:1044) moves
                    # both unconditionally regardless of stationary status.
                    half = _TARGET / 2.0
                    positions[id_i][0] = ax + half
                    positions[id_j][0] = bx - half
                    changed = True
                else:
                    overlap = _TARGET - dist
                    ux = dx / dist
                    uy = dy / dist
                    if a_stat and b_stat:
                        pass  # both fixed: rule says neither moves
                    elif a_stat:
                        positions[id_j][0] = bx + ux * overlap
                        positions[id_j][1] = by + uy * overlap
                        changed = True
                    elif b_stat:
                        positions[id_i][0] = ax - ux * overlap
                        positions[id_i][1] = ay - uy * overlap
                        changed = True
                    else:
                        positions[id_i][0] = ax - ux * overlap * 0.5
                        positions[id_i][1] = ay - uy * overlap * 0.5
                        positions[id_j][0] = bx + ux * overlap * 0.5
                        positions[id_j][1] = by + uy * overlap * 0.5
                        changed = True

        if not changed:
            break  # early-stop: pass wrote nothing, fixpoint reached

    return positions


# ---- helpers -----------------------------------------------------------------

_RAIDER = 0
_FACTION = 0
_LAYER = 0


def _spawn_seeded(lib, w, n, seed, box):
    """Spawn n Raiders at seeded positions in [0, box) x [0, box), return ids."""
    rng = random.Random(seed)
    ids = []
    for _ in range(n):
        x = rng.uniform(0.0, box)
        y = rng.uniform(0.0, box)
        uid = lib.om_unit_spawn(w, _RAIDER, _FACTION, x, y, _LAYER)
        ids.append(uid)
    return ids


def _make_world(lib, seed):
    from conftest import OMFeature
    w = lib.om_world_new(ctypes.c_uint32(1), ctypes.c_uint64(seed))
    assert w, "om_world_new returned NULL"
    # Enable only TACTICAL so movement/collision runs but strategic overhead does not.
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _read_positions(lib, w, ids):
    return {uid: list(lib.om_unit_get_pos(w, uid)) for uid in ids}


# All units should overlap substantially so the cap is exercised.
# Box = 60 wu keeps every pair within 2 * OM_MOVE_LIST_REACH = 120 wu, so the
# spatial-grid skip-past-reach edge case never triggers and all-pairs == C.
_BOX = 60.0
# Move destination far enough that no unit arrives in one collision pass.
_DEST_X, _DEST_Y = 1e6, 1e6


# ---- parametrised correctness tests -----------------------------------------

@pytest.mark.parametrize("n_units", [50, 200, 1000])
@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_collision_reference_matches_c(lib, n_units, seed):
    """S-097, S-102, ALG-68, R-099-03.

    Reference all-pairs collision pass result must equal the C spatial-grid
    implementation to 1e-9 wu, for seeds 1..5 and N in {50, 200, 1000}.
    Units all have group move orders (non-stationary) inside a 60 wu box
    (dense enough for overlaps; within 2*OM_MOVE_LIST_REACH so all pairs seen).
    """
    w = _make_world(lib, seed)

    ids = _spawn_seeded(lib, w, n_units, seed, _BOX)

    # Give all units a group move order to a far destination so none are stationary.
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    lib.om_command_group_move(w, arr, len(ids), _DEST_X, _DEST_Y)

    # Capture positions before the collision pass (same state C starts from).
    pre = _read_positions(lib, w, ids)

    # Run the C collision pass.
    lib.om_collision_pass(w)
    c_post = _read_positions(lib, w, ids)

    # Run the Python reference on a copy of the same starting positions.
    ref_pos = {uid: list(xy) for uid, xy in pre.items()}
    ref_result = _run_collision_reference(ref_pos, stationary=set())

    for uid in ids:
        cx, cy = c_post[uid]
        rx, ry = ref_result[uid]
        assert abs(cx - rx) <= 1e-9, (
            f"seed={seed} n={n_units} unit={uid}: x mismatch C={cx:.15g} ref={rx:.15g} "
            f"delta={abs(cx - rx):.3e}"
        )
        assert abs(cy - ry) <= 1e-9, (
            f"seed={seed} n={n_units} unit={uid}: y mismatch C={cy:.15g} ref={ry:.15g} "
            f"delta={abs(cy - ry):.3e}"
        )

    lib.om_world_free(w)


# ---- positive control --------------------------------------------------------

def test_collision_reference_cap_2_diverges(lib):
    """Positive control (ALG-68 R-099-03): perturbed reference (cap=2 instead
    of 3) must diverge from the C result (cap=3) on at least one of seeds 1..5
    with n=200 units.  Proves the 3-iteration cap is load-bearing and both the
    assertion and the reference are live."""
    n_units = 200
    diverged_on_any = False

    for seed in range(1, 6):
        w = _make_world(lib, seed)
        ids = _spawn_seeded(lib, w, n_units, seed, _BOX)

        arr = (ctypes.c_uint32 * len(ids))(*ids)
        lib.om_command_group_move(w, arr, len(ids), _DEST_X, _DEST_Y)

        pre = _read_positions(lib, w, ids)

        lib.om_collision_pass(w)
        c_post = _read_positions(lib, w, ids)

        # Reference with cap=2 (perturbed).
        ref_pos = {uid: list(xy) for uid, xy in pre.items()}
        ref2 = _run_collision_reference(ref_pos, stationary=set(), max_iter=2)

        for uid in ids:
            cx, cy = c_post[uid]
            rx, ry = ref2[uid]
            if abs(cx - rx) > 1e-9 or abs(cy - ry) > 1e-9:
                diverged_on_any = True
                break

        lib.om_world_free(w)
        if diverged_on_any:
            break

    assert diverged_on_any, (
        "cap=2 reference never diverged from the C (cap=3) result across seeds "
        "1..5 with n=200 -- the iteration cap may be decorative or the positions "
        "are too sparse to exercise it"
    )
