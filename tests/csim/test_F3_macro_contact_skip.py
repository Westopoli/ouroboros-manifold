# Rule pins: R-087-04@74cc9c, R-120-02@5c2e20
"""F3 (A7 sim-step fix 3, architect rulings 2 Addendum 3 A5/A6): skip the all-pairs
om_unit_can_see contact loop in om_macro_issue_group_orders (csrc/enemy_macro.c, B13)
once the force's sticky has_contact is already set. Profile: docs/northstar/plans/
2026-10-01-a7-sim-profile.md (0 ms on 19 steps in 20, 18 to 42 ms on the 20th).

Three groups of tests:

1. Equivalence (GREEN on main, must stay green after the change). REFERENCE_contact_now
   below is the OLD contact computation, kept verbatim in the test tree as a Python
   reference over unit state read through ctypes: contact_now = (force hp sum fell since
   the previous evaluation) or (any live force unit om_unit_can_see any live player unit);
   has_contact is sticky (|=). The force's has_contact is observable through an AMBUSH
   force: om_macro_trigger_ambush flips its behavior to ADVANCE exactly when has_contact
   is set (R-120-02), so per evaluation the observed behavior must equal the reference's
   sticky flag. Seeded clash scenes (two armies in sight) and spread scenes (no sight,
   contact only by damage or by the player walking into range at a chosen evaluation) at
   several unit counts. A full tactical run also pins a byte-identical unit-state hash to
   a golden recorded on main before the change (the same golden must hold after).
2. Positive control: a deliberately altered reference (ignoring sight, or ignoring damage)
   must disagree with the library in at least one scene; otherwise the equivalence test
   could not have caught a wrong skip.
3. The skip itself (RED on main): a probe build of csrc/*.c linked with
   -Wl,--wrap=om_unit_can_see counts the calls enemy_macro.c makes (a --wrap only
   rewrites undefined references across translation units, so fog.c's own internal
   calls are not counted). No header counter, no csrc edit. After has_contact is set
   and the player units are out of sight and undamaged, a later evaluation must make
   zero can_see calls; on main it makes n_force * n_player.
"""
import ctypes
import hashlib
import pathlib
import struct
import subprocess

import pytest

from conftest import (
    OMArchetype,
    OMEdge,
    OMFeature,
    REPO_ROOT,
    _bind_generated,
    _configure_common,
    _world_factory_for,
    set_edge,
    set_faction,
    set_owner,
)

RAIDER = 0
PLAYER_FAC = 0
ENEMY_FAC = 1
DEFENSIVE_STAND = 0
OM_MACRO_ADVANCE = 0
OM_MACRO_AMBUSH = 3
OM_MACRO_MOD_CAUTIOUS = 0
EVAL = 40  # OM_SCRIPT_EVAL_INTERVAL_TICKS (csrc/om_constants.h)

ENEMY_ORIGIN = (6000.0, 14000.0)
NEAR_ORIGIN = (6000.0, 13300.0)   # inside RAIDER sensor (800) of the enemy block
FAR_ORIGIN = (6000.0, 1000.0)     # about 13,000 wu away
SPACING = 40.0


def _world(lib, factory, seed):
    w = factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    lib.om_mission_setup(w, 0, DEFENSIVE_STAND, 0)
    lib.om_mission_set_phase(w, 1)
    return w


class _Xorshift:
    def __init__(self, seed):
        self.s = (seed * 2654435761 + 88172645463325252) & 0xFFFFFFFFFFFFFFFF

    def next(self):
        s = self.s
        s ^= (s << 13) & 0xFFFFFFFFFFFFFFFF
        s ^= s >> 7
        s ^= (s << 17) & 0xFFFFFFFFFFFFFFFF
        self.s = s
        return s

    def unit(self):
        return (self.next() >> 11) / float(1 << 53)


def _block(lib, w, n, fac, origin, rng):
    cols = max(1, int(n ** 0.5))
    ids = []
    for i in range(n):
        jx, jy = rng.unit() * 10.0, rng.unit() * 10.0
        x = origin[0] + (i % cols) * SPACING + jx
        y = origin[1] + (i // cols) * SPACING + jy
        ids.append(lib.om_unit_spawn(w, RAIDER, fac, x, y, 0))
    return ids


def _place(lib, w, ids, origin):
    cols = max(1, int(len(ids) ** 0.5))
    for i, u in enumerate(ids):
        lib.om_unit_teleport(w, u, origin[0] + (i % cols) * SPACING, origin[1] + (i // cols) * SPACING, 0)


def _live(lib, w, faction):
    out = []
    total = lib.om_unit_count(w)
    seen = 0
    i = 0
    while seen < total:
        uid = lib.om_unit_id_at(w, i)
        i += 1
        if not uid:
            continue
        seen += 1
        if lib.om_unit_get_faction(w, uid) == faction and lib.om_unit_alive(w, uid):
            out.append(uid)
    return out


# ---- the OLD contact computation, kept as the reference (do not "improve") ------------

def reference_contact_now(lib, w, hp_last, ignore_sight=False, ignore_damage=False):
    """Old om_macro_issue_group_orders contact block over ctypes. Returns
    (contact_now, hp_sum). hp_last is None before the first evaluation."""
    force = _live(lib, w, ENEMY_FAC)
    player = _live(lib, w, lib.om_player_faction(w))
    hp_sum = 0.0
    for u in force:
        hp_sum += lib.om_unit_get_hp(w, u)
    contact = False
    if not ignore_damage and hp_last is not None and hp_sum < hp_last:
        contact = True
    if not ignore_sight:
        for u in force:
            if contact:
                break
            for p in player:
                if lib.om_unit_can_see(w, u, p):
                    contact = True
                    break
    return contact, hp_sum


# scenario: (name, player start, event) where event = (eval index, "approach"|"wound"|None)
SCENES = [
    ("clash_in_sight", NEAR_ORIGIN, None),
    ("spread_none", FAR_ORIGIN, None),
    ("spread_approach_eval3", FAR_ORIGIN, (3, "approach")),
    ("spread_wound_eval2", FAR_ORIGIN, (2, "wound")),
]
COUNTS = (12, 60, 240)
N_EVALS = 6


def _run_scene(lib, w, n, scene, seed, ref_kwargs):
    """Returns (list of (observed_flag, reference_flag) per evaluation, flip eval or None)."""
    _name, player_origin, event = scene
    rng = _Xorshift(seed)
    enemy = _block(lib, w, n, ENEMY_FAC, ENEMY_ORIGIN, rng)
    player = _block(lib, w, n, PLAYER_FAC, player_origin, rng)
    lib.om_macro_set_state(w, 0, OM_MACRO_AMBUSH, OM_MACRO_MOD_CAUTIOUS)
    ref_flag = False
    hp_last = None
    pairs = []
    flip = None
    for k in range(N_EVALS):
        if event and event[0] == k:
            if event[1] == "approach":
                _place(lib, w, player, NEAR_ORIGIN)
            else:
                victim = enemy[rng.next() % len(enemy)]
                lib.om_unit_set_hp(w, victim, lib.om_unit_get_hp(w, victim) - 5.0)
        contact, hp_last = reference_contact_now(lib, w, hp_last, **ref_kwargs)
        ref_flag = ref_flag or contact
        lib.om_macro_tick(w, EVAL * (k + 1))
        observed = lib.om_macro_get_behavior(w, 0) == OM_MACRO_ADVANCE
        pairs.append((observed, ref_flag))
        if observed and flip is None:
            flip = k
    return pairs, flip


@pytest.mark.parametrize("n", COUNTS)
@pytest.mark.parametrize("scene", SCENES, ids=[s[0] for s in SCENES])
def test_F3_equivalence_new_contact_matches_old_reference(lib, world_factory, scene, n):
    """The observed sticky has_contact (ambush trigger) equals the OLD reference after
    every evaluation, in clash and spread scenes at every unit count."""
    for seed in (1, 2, 3):
        w = _world(lib, world_factory, seed)
        pairs, flip = _run_scene(lib, w, n, scene, seed, {})
        for k, (observed, ref_flag) in enumerate(pairs):
            assert observed == ref_flag, (
                f"{scene[0]} n={n} seed={seed} eval {k}: library has_contact={observed}, "
                f"old reference={ref_flag}"
            )
        name, _, event = scene
        expect = {"clash_in_sight": 0, "spread_none": None}.get(name, event[0] if event else None)
        assert flip == expect, f"{name} n={n} seed={seed}: scene guard, flipped at {flip}, expected {expect}"


@pytest.mark.parametrize("kwargs", [{"ignore_sight": True}, {"ignore_damage": True}],
                         ids=["ignores_sight", "ignores_damage"])
def test_F3_positive_control_altered_reference_is_caught(lib, world_factory, kwargs):
    """A reference that drops the sight clause (or the damage clause) must disagree with
    the library in at least one scene, proving the equivalence test can fail."""
    mismatches = 0
    for scene in SCENES:
        w = _world(lib, world_factory, 1)
        pairs, _ = _run_scene(lib, w, 60, scene, 1, kwargs)
        mismatches += sum(1 for observed, ref_flag in pairs if observed != ref_flag)
    assert mismatches > 0, f"altered reference {kwargs} agreed with the library everywhere"


# ---- byte-identical full-run state (golden recorded on main before the change) --------

def _state_hash(lib, w):
    h = hashlib.sha256()
    total = lib.om_unit_count(w)
    seen = 0
    i = 0
    while seen < total:
        uid = lib.om_unit_id_at(w, i)
        i += 1
        if not uid:
            continue
        seen += 1
        x, y = lib.om_unit_get_pos(w, uid)
        h.update(struct.pack("<IddddI", uid, x, y, lib.om_unit_get_hp(w, uid), 0.0,
                             lib.om_unit_alive(w, uid)))
    h.update(struct.pack("<Q", lib.om_world_checksum(w)))
    return h.hexdigest()


# Re-recorded A155 to A159 on push/pp-a5-land at default OM_TP_PURSUE_BY_STEERING 1 (was: recorded on origin/main before the F3 change).
# Re-recorded day20 on push/pp-c3-land (parity wave, leash anchor, give-up rule moved target choice and paths on purpose; baseline_hashes.json still green with both switches at 0; was: A155 to A159 recorded).
# Re-recorded day21 on push/pp-settle-gold (A184 collision settle epsilon 0.1 wu ends the push sequence early; was: day20 pp-c3-land recorded).
# Re-recorded day23 on push/pa-land (A199: an attack-mover no longer walks toward an enemy it merely sees, R-087-04; was: day21 pp-settle-gold recorded). TD-PP-A199-rerecord.
# Re-recorded 2026-11-08 (engine rule fixes F2, F3, F4; the new clash run has 0 R-207-06, R-087-04, R-084-04, R-087-03, R-083-03 violations by scripts/skilllab/invariants.py; was: day23 recorded: clash d6ac88b5; spread 12ad27cb unchanged). Test-defect.
GOLDEN = {
    "clash": "ec37b6038acaaa0d6a0b6eab93bfa0c744966a3d8e9b025984258b71d0c8d3c0",
    "spread": "12ad27cb5f68afb9e32c68dbd9c38cf22ccaa61cbda43a18e7409024a861cceb",
}


def _full_run(lib, w, kind):
    rng = _Xorshift(7)
    _block(lib, w, 80, ENEMY_FAC, ENEMY_ORIGIN, rng)
    _block(lib, w, 80, PLAYER_FAC, NEAR_ORIGIN if kind == "clash" else FAR_ORIGIN, rng)
    lib.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
    lib.om_tactical_tick_to(w, 400)  # ten macro evaluations
    return _state_hash(lib, w)


@pytest.mark.parametrize("kind", ["clash", "spread"])
def test_F3_full_run_unit_state_is_byte_identical_to_golden(lib, world_factory, kind):
    got = _full_run(lib, _world(lib, world_factory, 1), kind)
    again = _full_run(lib, _world(lib, world_factory, 1), kind)
    assert got == again, "run is not even self-deterministic"
    assert got == GOLDEN[kind], f"{kind}: unit-state hash {got} != golden {GOLDEN[kind]}"


# ---- the skip: count enemy_macro.c's om_unit_can_see calls via a --wrap probe build ---

_SHIM = r"""
#include <stdint.h>
typedef struct om_world om_world;
int __real_om_unit_can_see(const om_world *w, uint32_t o, uint32_t t);
static unsigned long long calls;
int __wrap_om_unit_can_see(const om_world *w, uint32_t o, uint32_t t) { calls++; return __real_om_unit_can_see(w, o, t); }
unsigned long long om_f3_can_see_calls(void) { return calls; }
void om_f3_reset(void) { calls = 0; }
"""


@pytest.fixture(scope="module")
def probe(tmp_path_factory):
    d = tmp_path_factory.mktemp("f3probe")
    shim = d / "shim.c"
    shim.write_text(_SHIM)
    so = d / "libouroboros_f3probe.so"
    srcs = sorted(str(p) for p in (REPO_ROOT / "csrc").glob("*.c"))
    cmd = ["cc", "-std=c11", "-Wall", "-Wextra", "-I" + str(REPO_ROOT / "csrc"), "-fPIC", "-O2",
           "-fno-fast-math", "-ffp-contract=off", "-fexcess-precision=standard", "-msse2",
           "-mfpmath=sse", "-fno-math-errno", "-shared", "-Wl,--wrap=om_unit_can_see",
           "-o", str(so)] + srcs + [str(shim)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, "probe build failed:\n" + r.stderr
    handle = ctypes.CDLL(str(so))
    _configure_common(handle)
    _bind_generated(handle)
    handle.om_f3_can_see_calls.restype = ctypes.c_ulonglong
    handle.om_f3_can_see_calls.argtypes = []
    handle.om_f3_reset.restype = None
    handle.om_f3_reset.argtypes = []
    make, created = _world_factory_for(handle, None)
    yield handle, make
    for w in created:
        handle.om_world_free(w)


def test_F3_contact_loop_is_skipped_once_has_contact_is_set(probe):
    """Eval 0: a player unit is in sight, so has_contact is set (the loop exits on its
    first hit). Then every player unit is moved far away: no sight, no damage. Evaluation 1
    must not run the all-pairs can_see loop: zero calls. On main it makes n_force *
    n_player calls (every pair, none visible)."""
    handle, make = probe
    n = 50
    w = _world(handle, make, 1)
    rng = _Xorshift(1)
    _block(handle, w, n, ENEMY_FAC, ENEMY_ORIGIN, rng)
    player = _block(handle, w, n, PLAYER_FAC, NEAR_ORIGIN, rng)
    handle.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)

    handle.om_f3_reset()
    handle.om_macro_tick(w, EVAL)
    first = handle.om_f3_can_see_calls()
    assert first >= 1, "setup check: eval 0 should have exercised the contact test"

    _place(handle, w, player, FAR_ORIGIN)
    assert not any(handle.om_unit_can_see(w, u, p) for u in _live(handle, w, ENEMY_FAC)[:3]
                   for p in player[:3]), "setup check: player must be out of sight"

    handle.om_f3_reset()
    handle.om_macro_tick(w, 2 * EVAL)
    second = handle.om_f3_can_see_calls()
    assert second == 0, (
        f"has_contact already set, yet eval 1 made {second} om_unit_can_see calls "
        f"(all-pairs would be {n * n})"
    )


def test_F3_probe_positive_control_counts_calls_while_contact_unset(probe):
    """Positive control for the counter: with no sight and no damage, has_contact never
    sets, so the contact check keeps running every evaluation; two identical runs count the same,
    and the probe registers om_unit_can_see calls when a player unit is in sight. The exact all-pairs figure
    (2 * n * n) is NOT asserted: A99 replaces the all-pairs loop with a grid query, so the
    call count legitimately drops (test-defect TD-A99-F3, push ledger)."""
    handle, make = probe
    n = 30
    w = _world(handle, make, 1)
    rng = _Xorshift(1)
    _block(handle, w, n, ENEMY_FAC, ENEMY_ORIGIN, rng)
    _block(handle, w, n, PLAYER_FAC, FAR_ORIGIN, rng)
    handle.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
    counts = []
    for run in range(2):
        if run:
            w = _world(handle, make, 1)
            rng = _Xorshift(1)
            _block(handle, w, n, ENEMY_FAC, ENEMY_ORIGIN, rng)
            _block(handle, w, n, PLAYER_FAC, FAR_ORIGIN, rng)
            handle.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
        handle.om_f3_reset()
        handle.om_macro_tick(w, EVAL)
        handle.om_macro_tick(w, 2 * EVAL)
        counts.append(handle.om_f3_can_see_calls())
    assert counts[0] == counts[1], f"probe counts differ between identical runs: {counts}"
    # the counter itself is live: with the player in sight the contact check must register calls
    w = _world(handle, make, 1)
    rng = _Xorshift(1)
    _block(handle, w, n, ENEMY_FAC, ENEMY_ORIGIN, rng)
    _block(handle, w, n, PLAYER_FAC, NEAR_ORIGIN, rng)
    handle.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
    handle.om_f3_reset()
    handle.om_macro_tick(w, EVAL)
    assert handle.om_f3_can_see_calls() >= 1, "probe registered no om_unit_can_see calls"
