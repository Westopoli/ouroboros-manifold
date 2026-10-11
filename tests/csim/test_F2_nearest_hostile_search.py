"""F2 (A7 sim-step fix 2, architect rulings 2 Addendum 3 A5/A6; profile docs/northstar/plans/
2026-10-01-a7-sim-profile.md "fix 2"): the AI target search in csrc/unit.c (B10) stops walking
candidates that can never be the answer. About 71% of sim self time was circle-query candidate
walking in om_tactical_ai_tick -> om_tac_nearest_hostile -> om_tac_nearest_scan_cell /
om_tac_dist_le / om_grid_iter_next, most of it same-faction rows.

THE RULE (quoted from csrc/unit.c so the Python reference below is exact). Once per unit per
OM_TARGETING_COHORT_COUNT (4) ticks (the unit's id % 4 == tick % 4), a live unit whose
target_id is 0, whose order is not ATTACK_TARGET, and which is not noncombat or flinching,
calls om_tac_nearest_hostile(self, attack_range) and stores the answer in target_id
(om_unit_get_target reads it). The answer:

  candidates  = every unit row with dist(self, cand)^2 <= r^2 (dx*dx + dy*dy <= r*r, inclusive),
                hp > 0, stealth off, both factions >= 0 and different, same layer
  reference   = the ORDERED scan: candidates in ascending unit id; the first becomes the best;
                a later one replaces it only when d2 < best_d2 - OM_TIE_EPSILON (1e-12)
  fast path   = the unordered grid walk returns the lowest id among the candidates at the minimum
                d2 (the (d2, id) tie-break). It is exact only while no other candidate lies within
                OM_TIE_SCAN_WINDOW (4 * OM_TIE_EPSILON = 4e-12) above the minimum d2; when the
                second-smallest distinct d2 minus the smallest is <= the window, the code falls
                back to the ordered scan (the "window fallback"). So the library answer ALWAYS
                equals the ordered reference, including its chain effect: a candidate within
                1e-12 below the current best does NOT replace it, even though it is nearer.

The fix keeps that answer exactly and only skips candidates that cannot be it (a row of the
searcher's own faction, a neutral row, a farther row). No constant, cell size or tick rate changes.

Groups:
1. equivalence (GREEN on main, must stay green): the library's target_id after the four cohort
   ticks equals the ordered reference for every unit, in clash, spread, lattice (exact equal
   distances) and window (distances within the scan window, sub-epsilon chains) scenes at 100,
   1,000 and 5,000 units, seeds 1 and 2. The units are a custom type that never fires (attack
   interval 1e9), so hp never changes and the only target source is this search.
2. positive control: a reference with the wrong tie-break (highest id) and one that ignores the
   window fallback (strict (d2, id) minimum) each differ from the library in at least one scene
   (and the window scene guard proves both altered references are caught).
3. golden: full unit-state hash (position, hp, target, alive) plus om_world_checksum after 400
   ticks of a clash and a spread scene (raiders, with an attack-move order so the sensor-radius
   search is exercised), recorded on main (GREEN on main, must stay green).
4. the skip, observed without timing (RED on main): a probe build counts every distance test
   (om_tac_dist_le) issued while the four cohort ticks run the searches. The searching units are
   a custom type with no ability, so the only other callers are the two in-range checks per
   targeted unit per tick. On main every same-faction row inside a cell is tested.
   The probe is the same csrc/*.c build with one counter line injected into a copy of unit.c at the
   om_tac_dist_le definition (a static function in the same translation unit as its callers, so
   the -Wl,--wrap technique of test_F3/test_F1 cannot reach it).
"""
import ctypes
import hashlib
import math
import re
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
CUSTOM = 100
PLAYER_FAC = 0
ENEMY_FAC = 1
NEUTRAL_FAC = -1
RANGE = 200.0
DEFENSIVE_STAND = 0
OM_MACRO_ADVANCE = 0
OM_MACRO_MOD_CAUTIOUS = 0
TIE_EPS = 1e-12
TIE_WINDOW = 4.0 * TIE_EPS
COHORT_TICKS = 4


def _world(lib, factory, seed, custom=True):
    w = factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    lib.om_mission_setup(w, 0, DEFENSIVE_STAND, 0)
    lib.om_mission_set_phase(w, 1)
    if custom:
        # strike category, 250 hp, never fires (interval 1e9), no ability, range 200, speed 0
        rc = lib.om_roster_register_custom_unit(w, CUSTOM, 0, b"idler", 250.0, 9.0, 1.0e9, RANGE,
                                                0.0, 800.0, 1.0, 0.0, 0)
        assert rc == 0
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


def _all_ids(lib, w):
    out = []
    total = lib.om_unit_count(w)
    i = 0
    while len(out) < total:
        uid = lib.om_unit_id_at(w, i)
        i += 1
        if uid:
            out.append(uid)
    return out


def _spawn(lib, w, fac, x, y, utype=CUSTOM):
    uid = lib.om_unit_spawn(w, utype, fac, x, y, 0)
    assert uid, f"spawn failed at ({x}, {y}) (map or unit cap)"
    return uid


def _decorate(lib, w, ids, rng, every_dead=23, every_stealth=29):
    """Some units dead (hp 0), some stealthy; both must be ignored as candidates."""
    for k, uid in enumerate(ids):
        if k % every_dead == 7:
            lib.om_unit_set_hp(w, uid, 0.0)
        elif k % every_stealth == 11:
            lib.om_unit_set_stealth(w, uid, 1)


def _step_ulps(x, k, toward):
    for _ in range(k):
        x = math.nextafter(x, toward)
    return x


def build_scene(lib, w, kind, n, seed, utype=CUSTOM):
    """clash: two blocks, one per faction, touching at the front. spread: uniform scatter, about
    half an enemy per search circle. lattice: factions at random on a 40-unit grid, so equal
    distances (exact ties) are everywhere. window: patches of one searcher ringed by four enemies
    at one distance, two of them nudged 0 to 3 units in the last place of x: equal d2, gaps under
    OM_TIE_EPSILON (the chain case) and gaps inside OM_TIE_SCAN_WINDOW."""
    rng = _Xorshift(seed)
    ids = []
    if kind == "clash":
        half = n // 2
        cols = max(1, int(half ** 0.5))
        rows = (half + cols - 1) // cols
        for fac, oy in ((ENEMY_FAC, 6000.0), (PLAYER_FAC, 6000.0 - rows * 40.0 - 20.0)):
            for i in range(half):
                x = 6000.0 + (i % cols) * 40.0 + rng.unit() * 10.0
                y = oy + (i // cols) * 40.0 + rng.unit() * 10.0
                ids.append(_spawn(lib, w, fac, x, y, utype))
    elif kind == "spread":
        side = 150.0 * (n ** 0.5)
        for _ in range(n):
            fac = PLAYER_FAC if rng.next() & 1 else ENEMY_FAC
            ids.append(_spawn(lib, w, fac, 1000.0 + rng.unit() * side, 1000.0 + rng.unit() * side, utype))
    elif kind == "far":
        # Two blocks 600 apart (3 x the range): every search circle holds only own-faction rows.
        half = n // 2
        cols = max(1, int(half ** 0.5))
        for fac, ox in ((ENEMY_FAC, 6000.0), (PLAYER_FAC, 6600.0 + cols * 40.0)):
            for i in range(half):
                ids.append(_spawn(lib, w, fac, ox + (i % cols) * 40.0 + rng.unit() * 10.0,
                                  6000.0 + (i // cols) * 40.0 + rng.unit() * 10.0, utype))
    elif kind == "lattice":
        cols = max(1, int(n ** 0.5))
        for i in range(n):
            r = rng.next() % 5
            fac = NEUTRAL_FAC if r == 0 else (PLAYER_FAC if r % 2 else ENEMY_FAC)
            ids.append(_spawn(lib, w, fac, 1000.0 + (i % cols) * 40.0, 1000.0 + (i // cols) * 40.0, utype))
    elif kind == "window":
        # One 5-unit patch per 150 units of y, all searcher/enemy x coordinates below 128 so one
        # ulp of x moves a squared distance by under OM_TIE_EPSILON (2 * D * ulp(x) with D <= 56);
        # unit spacing is far above the collision diameter (30), so nothing is pushed.
        for j in range(max(1, n // 5)):
            cy = 200.0 + 150.0 * j
            fa, fb = (PLAYER_FAC, ENEMY_FAC) if rng.next() & 1 else (ENEMY_FAC, PLAYER_FAC)
            dd = 40.0 + 8.0 * (rng.next() % 3)
            ka, kb = rng.next() % 4, rng.next() % 4
            ids.append(_spawn(lib, w, fa, 64.0, cy, utype))
            ids.append(_spawn(lib, w, fb, _step_ulps(64.0 + dd, ka, math.inf), cy, utype))
            ids.append(_spawn(lib, w, fb, _step_ulps(64.0 - dd, kb, -math.inf), cy, utype))
            ids.append(_spawn(lib, w, fb, 64.0, cy + dd, utype))
            ids.append(_spawn(lib, w, fb, 64.0, cy - dd, utype))
    else:
        raise ValueError(kind)
    _decorate(lib, w, ids, rng)
    return ids


# ---- the reference: the ORDERED scan of csrc/unit.c, in Python (do not "improve") ------

def snapshot(lib, w):
    """id -> (x, y, hp, faction, stealth). Stealth is tracked by the scene builder through
    om_unit_set_stealth; the library has no stealth getter, so build_scene records it."""
    rows = {}
    for u in _all_ids(lib, w):
        x, y = lib.om_unit_get_pos(w, u)
        rows[u] = (x, y, lib.om_unit_get_hp(w, u), lib.om_unit_get_faction(w, u))
    return rows


def _stealth_ids(ids):
    return {uid for k, uid in enumerate(ids) if k % 23 != 7 and k % 29 == 11}


def reference_targets(rows, stealth, r=RANGE, mode="old"):
    """Target id (0 = none) the search yields for every live unit. mode: old (the ordered scan),
    highid (ties to the HIGHEST id), strict (min (d2, id): the window fallback ignored)."""
    cell = r
    cells = {}
    for u in sorted(rows):
        x, y, hp, fac = rows[u]
        cells.setdefault((int(x // cell), int(y // cell)), []).append(u)
    out = {}
    for u in sorted(rows):
        sx, sy, shp, sfac = rows[u]
        if shp <= 0.0:
            out[u] = 0
            continue
        cx, cy = int(sx // cell), int(sy // cell)
        cands = []
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                cands.extend(cells.get((gx, gy), ()))
        cands.sort()
        best, best_d2 = 0, 0.0
        for c in cands:
            x, y, hp, fac = rows[c]
            dx = x - sx
            dy = y - sy
            d2 = dx * dx + dy * dy
            if not d2 <= r * r:
                continue
            if hp <= 0.0 or c in stealth:
                continue
            if not (sfac >= 0 and fac >= 0 and fac != sfac):
                continue
            if mode == "old":
                if best == 0 or d2 < best_d2 - TIE_EPS:
                    best, best_d2 = c, d2
            elif mode == "strict":
                if best == 0 or d2 < best_d2:
                    best, best_d2 = c, d2
            elif mode == "highid":
                if best == 0 or d2 < best_d2 - TIE_EPS or (abs(d2 - best_d2) <= TIE_EPS and c > best):
                    best, best_d2 = c, d2
        out[u] = best
    return out


def library_targets(lib, w):
    return {u: lib.om_unit_get_target(w, u) for u in _all_ids(lib, w)}


def run_search(lib, w):
    """Four ticks: every unit's cohort tick comes up once. Nobody moves or fires."""
    # Test-defect, A127: with OM_TP_PURSUE_BY_STEERING on (default 1) a unit in range fires its first shot on
    # the first tick (R-084-01) and units move during the four cohort ticks, so the equivalence below would
    # compare against a fight, not a search. Baseline mode (0) keeps the four-tick search this test was written
    # for; the search rule itself is untouched.
    assert lib.om_tactical_set_param(w, 0, 0.0) == 0
    # The scene runs y past the 16000 canvas: with OM_TP_ROUTE_AROUND_TERRAIN on every off-canvas unit is
    # relocated to the edge on tick 1 (R-097-09), so the reference would see stale positions. Baseline too.
    assert lib.om_tactical_set_param(w, 1, 0.0) == 0
    lib.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
    lib.om_tactical_tick_to(w, COHORT_TICKS)


SCENE_KINDS = ("clash", "spread", "lattice", "window")
COUNTS = (100, 1000, 5000)


def _diff(got, want):
    bad = [u for u in sorted(want) if got.get(u) != want[u]]
    return bad, [(u, got.get(u), want[u]) for u in bad[:4]]


def _prepared(lib, factory, kind, n, seed):
    w = _world(lib, factory, seed)
    if kind == "window":
        # PP: scene is off canvas; baseline routing (A147 option c', test-defect)
        assert lib.om_tactical_set_param(w, 1, 0.0) == 0  # OM_TP_ROUTE_AROUND_TERRAIN
    ids = build_scene(lib, w, kind, n, seed)
    stealth = _stealth_ids(ids)
    rows = snapshot(lib, w)
    run_search(lib, w)
    return w, ids, rows, stealth


@pytest.mark.parametrize("n", COUNTS)
@pytest.mark.parametrize("kind", SCENE_KINDS)
def test_F2_equivalence_target_choice_matches_ordered_reference(lib, world_factory, kind, n):
    """Every unit's target after the cohort ticks equals the ordered-scan reference (nearest live
    hostile in range, (d2, id) tie-break, window fallback), clash/spread/lattice/window scenes,
    seeds 1 and 2. Scene guards: the scenes must actually contain targets, and the tie scenes
    must contain equal-distance and in-window candidates."""
    for seed in (1, 2):
        w, ids, rows, stealth = _prepared(lib, world_factory, kind, n, seed)
        want = reference_targets(rows, stealth)
        got = library_targets(lib, w)
        bad, sample = _diff(got, want)
        assert not bad, (f"{kind} n={n} seed={seed}: {len(bad)} units chose a different target than "
                         f"the ordered reference (unit, library, reference): {sample}")
        have = sum(1 for t in want.values() if t)
        assert have >= max(5, len(want) // 20), (
            f"scene guard {kind} n={n} seed={seed}: only {have} of {len(want)} units have a hostile "
            f"in range; the scene would not exercise the search")


def _tie_stats(rows, stealth, r=RANGE):
    """(searches with >=2 candidates at exactly the minimum d2, searches whose two smallest distinct
    d2 differ by at most the scan window)."""
    exact = window = 0
    ids = sorted(rows)
    cells = {}
    for u in ids:
        cells.setdefault((int(rows[u][0] // r), int(rows[u][1] // r)), []).append(u)
    for u in ids:
        sx, sy, shp, sfac = rows[u]
        if shp <= 0.0:
            continue
        ds = []
        for gx in (int(sx // r) - 1, int(sx // r), int(sx // r) + 1):
            for gy in (int(sy // r) - 1, int(sy // r), int(sy // r) + 1):
                for c in cells.get((gx, gy), ()):
                    x, y, hp, fac = rows[c]
                    d2 = (x - sx) ** 2 + (y - sy) ** 2
                    if d2 <= r * r and hp > 0.0 and c not in stealth and sfac >= 0 and fac >= 0 and fac != sfac:
                        ds.append(d2)
        ds.sort()
        if len(ds) >= 2 and ds[0] == ds[1]:
            exact += 1
        distinct = sorted(set(ds))
        if len(distinct) >= 2 and distinct[1] - distinct[0] <= TIE_WINDOW:
            window += 1
    return exact, window


def test_F2_scene_guards_the_tie_and_window_scenes_contain_the_cases(lib, world_factory):
    """The lattice scene has exact equal-distance pairs; the window scene has pairs inside the
    scan window (non-zero gap <= 4e-12) and equal pairs. Without these the equivalence test could
    not exercise the tie-break or the fallback."""
    w, ids, rows, stealth = _prepared(lib, world_factory, "lattice", 1000, 1)
    exact, _ = _tie_stats(rows, stealth)
    assert exact >= 50, f"lattice scene: only {exact} searches have an exact equal-distance pair"
    w, ids, rows, stealth = _prepared(lib, world_factory, "window", 1000, 1)
    exact, window = _tie_stats(rows, stealth)
    assert window >= 20, f"window scene: only {window} searches have a two-smallest gap inside the scan window"
    assert exact >= 5, f"window scene: only {exact} searches have an exact equal-distance pair"


@pytest.mark.parametrize("mode", ["highid", "strict"])
def test_F2_positive_control_altered_reference_is_caught(lib, world_factory, mode):
    """A reference with the wrong tie-break (highest id) or with the window fallback ignored
    (strict (d2, id) minimum) must differ from the library in at least one scene; otherwise the
    equivalence test could not have caught a search that broke either rule."""
    differing = 0
    for kind in SCENE_KINDS:
        w, ids, rows, stealth = _prepared(lib, world_factory, kind, 1000, 1)
        got = library_targets(lib, w)
        if got != reference_targets(rows, stealth, mode=mode):
            differing += 1
    assert differing > 0, f"altered reference '{mode}' agreed with the library in every scene"


def test_F2_positive_control_window_scene_separates_both_alterations(lib, world_factory):
    """The window scene alone catches 'ignore the window fallback', and the lattice scene alone
    catches 'highest id wins ties': each rule has a scene that depends on it."""
    w, ids, rows, stealth = _prepared(lib, world_factory, "window", 1000, 1)
    got = library_targets(lib, w)
    assert got == reference_targets(rows, stealth)
    assert got != reference_targets(rows, stealth, mode="strict"), "window scene does not depend on the fallback"
    w, ids, rows, stealth = _prepared(lib, world_factory, "lattice", 1000, 1)
    got = library_targets(lib, w)
    assert got == reference_targets(rows, stealth)
    assert got != reference_targets(rows, stealth, mode="highid"), "lattice scene does not depend on the id tie-break"


def test_F2_equidistant_targets_break_ties_by_lowest_id(lib, world_factory):
    """Four enemies at exactly the same distance around one searcher: the lowest id is chosen,
    whichever compass side it stands on."""
    for order in range(4):
        w = _world(lib, world_factory, 1)
        obs = _spawn(lib, w, PLAYER_FAC, 3000.0, 3000.0)
        spots = [(3100.0, 3000.0), (3000.0, 3100.0), (2900.0, 3000.0), (3000.0, 2900.0)]
        spots = spots[order:] + spots[:order]
        es = [_spawn(lib, w, ENEMY_FAC, x, y) for x, y in spots]
        run_search(lib, w)
        assert lib.om_unit_get_target(w, obs) == min(es), f"rotation {order}: tie did not go to the lowest id"


# ---- golden: full run after 400 ticks, recorded on main before the change -------------

def _state_hash(lib, w):
    h = hashlib.sha256()
    for uid in _all_ids(lib, w):
        x, y = lib.om_unit_get_pos(w, uid)
        h.update(struct.pack("<IddddII", uid, x, y, lib.om_unit_get_hp(w, uid), 0.0,
                             lib.om_unit_get_target(w, uid), lib.om_unit_alive(w, uid)))
    h.update(struct.pack("<Q", lib.om_world_checksum(w)))
    return h.hexdigest()


# Re-recorded A155 to A159 on push/pp-a5-land at default OM_TP_PURSUE_BY_STEERING 1 (was: recorded on origin/main b1d53b7e).
# Re-recorded day20 on push/pp-c3-land (parity wave, leash anchor, give-up rule moved target choice and paths on purpose; baseline_hashes.json still green with both switches at 0; was: A155 to A159 recorded).
# Re-recorded day21 on push/pp-settle-gold (A184 collision settle epsilon 0.1 wu ends the push sequence early; was: day20 pp-c3-land recorded).
# Re-recorded day22 on push/pl-land (A188 leash tests the unit's own distance; clash 37bc9238 -> e1377247; spread unchanged; was: day21 pp-settle-gold recorded).
# Re-recorded day23 on push/pa-land (A199: an attack-mover no longer walks toward an enemy it merely sees, R-087-04; was: day21 pp-settle-gold and day22 pl-land recorded). TD-PP-A199-rerecord.
GOLDEN = {
    "clash": "078776355f08bcc9978634e8d50cac48b2a62b8f674659273ba281fe32ecebdd",
    "spread": "bb85256fd29a1b754468f8adf3388aba58ce94c7552cd7f8382a42b634bcedf5",
}


def _full_run(lib, w, kind):
    ids = build_scene(lib, w, kind, 600, 7, utype=RAIDER)
    mine = [u for u in ids if lib.om_unit_get_faction(w, u) == PLAYER_FAC and lib.om_unit_alive(w, u)]
    lib.om_command_attack_move(w, mine, len(mine), 6200.0, 6300.0 if kind == "clash" else 9000.0)
    lib.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
    lib.om_tactical_tick_to(w, 400)
    return _state_hash(lib, w)


@pytest.mark.parametrize("kind", ["clash", "spread"])
def test_F2_full_run_state_is_byte_identical_to_golden(lib, world_factory, kind):
    """Unit-state hash (position, hp, target, alive) plus om_world_checksum after 400 ticks of a
    600-raider scene with an attack-move order (units fight, so the nearest-hostile choice feeds
    the hash; the attack-move units exercise the sensor-radius search)."""
    got = _full_run(lib, _world(lib, world_factory, 1, custom=False), kind)
    again = _full_run(lib, _world(lib, world_factory, 1, custom=False), kind)
    assert got == again, "run is not even self-deterministic"
    assert got == GOLDEN[kind], f"{kind}: state hash {got} != golden {GOLDEN[kind]}"


# ---- the skip: how many distance tests do the target searches run? --------------------

_ANCHOR = re.compile(r"static int om_tac_dist_le\(double dx, double dy, double r\) \{")
_COUNTER = ("unsigned long om_f2_dist_n;\n"
            "unsigned long om_f2_dist_calls(void) { return om_f2_dist_n; }\n"
            "void om_f2_reset(void) { om_f2_dist_n = 0; }\n"
            "static int om_tac_dist_le(double dx, double dy, double r) {\n    om_f2_dist_n++;")


@pytest.fixture(scope="module")
def probe(tmp_path_factory):
    d = tmp_path_factory.mktemp("f2probe")
    text = (REPO_ROOT / "csrc" / "unit.c").read_text()
    assert _ANCHOR.search(text), ("probe anchor missing: csrc/unit.c no longer defines om_tac_dist_le with "
                                  "that exact signature line; update the probe in test_F2_nearest_hostile_search.py")
    patched = d / "unit.c"
    patched.write_text(_ANCHOR.sub(lambda m: _COUNTER, text, count=1))
    so = d / "libouroboros_f2probe.so"
    srcs = sorted(str(p) for p in (REPO_ROOT / "csrc").glob("*.c") if p.name != "unit.c")
    cmd = ["cc", "-std=c11", "-Wall", "-Wextra", "-I" + str(REPO_ROOT / "csrc"), "-fPIC", "-O2",
           "-fno-fast-math", "-ffp-contract=off", "-fexcess-precision=standard", "-msse2",
           "-mfpmath=sse", "-fno-math-errno", "-shared", "-o", str(so)] + srcs + [str(patched)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, "probe build failed:\n" + r.stderr
    handle = ctypes.CDLL(str(so))
    _configure_common(handle)
    _bind_generated(handle)
    handle.om_f2_dist_calls.restype = ctypes.c_ulong
    handle.om_f2_dist_calls.argtypes = []
    handle.om_f2_reset.restype = None
    handle.om_f2_reset.argtypes = []
    make, created = _world_factory_for(handle, None)
    yield handle, make
    for w in created:
        handle.om_world_free(w)


def _hostile_in_circle_total(rows, stealth, r=RANGE):
    """Sum over live units of the live, non-stealth, hostile rows inside its search circle."""
    total = 0
    ids = sorted(rows)
    cells = {}
    for u in ids:
        cells.setdefault((int(rows[u][0] // r), int(rows[u][1] // r)), []).append(u)
    for u in ids:
        sx, sy, shp, sfac = rows[u]
        if shp <= 0.0:
            continue
        for gx in (int(sx // r) - 1, int(sx // r), int(sx // r) + 1):
            for gy in (int(sy // r) - 1, int(sy // r), int(sy // r) + 1):
                for c in cells.get((gx, gy), ()):
                    x, y, hp, fac = rows[c]
                    if ((x - sx) ** 2 + (y - sy) ** 2 <= r * r and hp > 0.0 and c not in stealth
                            and sfac >= 0 and fac >= 0 and fac != sfac):
                        total += 1
    return total


def _counted_search(handle, make, kind, n, seed=1):
    w = _world(handle, make, seed)
    ids = build_scene(handle, w, kind, n, seed)
    rows = snapshot(handle, w)
    handle.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
    handle.om_f2_reset()
    handle.om_tactical_tick_to(w, COHORT_TICKS)
    return handle.om_f2_dist_calls(), rows, _stealth_ids(ids)


def _budget(rows, stealth, searchers):
    """Distance tests a hostile-only search needs: at most four per eligible hostile row inside a
    search circle (cell-granularity extras) plus nine per unit (one per own search, two in-range
    checks per targeted unit per tick over four ticks)."""
    return 4 * _hostile_in_circle_total(rows, stealth) + 9 * searchers


def test_F2_search_does_not_distance_test_same_faction_candidates(probe):
    """Run the four cohort ticks of a 1,000-unit scene of two blocks too far apart to see each
    other. The searches may distance-test about as many rows as there are eligible hostile rows in
    the circles (none here); they must not distance-test the searcher's own faction (every unit
    has dozens of own-faction neighbours inside its circle)."""
    handle, make = probe
    kind = "far"
    calls, rows, stealth = _counted_search(handle, make, kind, 1000)
    live = sum(1 for r in rows.values() if r[2] > 0.0)
    budget = _budget(rows, stealth, live)
    assert calls <= budget, (
        f"{kind}: {calls} distance tests for {live} searches, budget {budget} "
        f"(hostile rows in circles: {_hostile_in_circle_total(rows, stealth)})")


def _own_faction_in_circle_total(rows, r=RANGE):
    total = 0
    for u, (sx, sy, shp, sfac) in rows.items():
        if shp <= 0.0:
            continue
        for c, (x, y, hp, fac) in rows.items():
            if c != u and fac == sfac and hp > 0.0 and (x - sx) ** 2 + (y - sy) ** 2 <= r * r:
                total += 1
    return total


def test_F2_probe_positive_control_counter_and_budget_can_tell_the_walk(probe):
    """Control for the counter and the budget: the counter fires when hostile rows are in
    range (clash scene), and the far scene holds many times more same-faction rows inside the search circles than the
    budget allows, so a search that distance-tests them cannot fit the budget."""
    handle, make = probe
    calls, _rows, _stealth = _counted_search(handle, make, "clash", 400)
    assert calls > 0, "the probe counter never fired (the clash scene has hostile rows in range)"
    _calls, rows, stealth = _counted_search(handle, make, "far", 400)
    live = sum(1 for r in rows.values() if r[2] > 0.0)
    own = _own_faction_in_circle_total(rows)
    assert own > 3 * _budget(rows, stealth, live), (
        f"scene guard: {own} same-faction in-circle rows vs budget {_budget(rows, stealth, live)}")
