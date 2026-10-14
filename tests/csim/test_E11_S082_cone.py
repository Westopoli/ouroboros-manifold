# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, ruling 9, "Contract / Engine" (om_roster_set_cone), Pieces row E2.
# piece LAB-REV2-E2 (cone area damage); rule R-082-06 DRAFT (E-11 S-082), register Q-082-06; Bombard disc R-084-03 / ALG-61.
"""S-082 cone area damage (R-082-06, DRAFT, Westley 2026-10-13; Q-082-06).

The rule (spec ruling 9 and the Pieces row E2): a type with a cone set (range above 0) attacks like this. Its target
of record takes the direct ALG-60 hit first, counted toward the cap; then every other enemy inside the circular
sector of `range` and `half_angle` about the attacker's facing (centre test, boundary inclusive, a dot product
against the stored cosine), within the attacker's reach offsets, takes base x share x the area offset multiplier, in
ascending unit id, until the running total reaches the cap, base x OM_AOE_DAMAGE_CAP_MULTIPLIER (the last hit is
truncated). No sight, stealth or line check for victims (as the disc). om_economy_on_area_hit is not called for a
cone. A half-angle of 180 is a disc about the ATTACKER (R-084-03's is about the target). Range 0 restores the disc.
om_roster_set_cone returns 0 ok, -1 unknown type, -2 refused value (range < 0, half-angle outside [1, 180], share
outside [0, 10]); range 0 clears.

Fixture numbers (named, not thresholds): cone range 400, half-angle 30 degrees, shares 0.5 / 1.0 / adaptive;
victims are Supply units (never fire, so nothing but the volley moves a hit-point total and the target of record is
the nearest one), each set to 1000 hit points so no hit is an overkill; the attacker is a Bombard (range 1200,
sensor 300, disc 150) facing +x with the target of record on the facing axis 200 wu out, so the face pass leaves the
facing untouched and the sector is where the fixture says. Damage is hit points lost on the tick of the attacker's
first shot.

What is deliberately NOT pinned: whether a cone victim also takes the category multiplier, the output multiplier and
the target's damage reduction (R-082-06 says "base damage times the share"; the spec row says "base x share x area
offset multiplier"; ALG-61 says the disc victims take ALG-60 damage). Every assertion below is relative: victims
against victims, a share against share 1.0, a victim on another layer against the same-layer victim, the target of
record against the disc control's target (which is a plain ALG-60 hit), and the cap in absolute terms only through
base x OM_AOE_DAMAGE_CAP_MULTIPLIER read from the headers. Reported as an open question, not guessed.

Red on the E0 tree: om_roster_set_cone is the stub and answers -1 (not built), so every scene that sets a cone stops
at the first assertion (the message names the -1). Green on the E0 tree: the three disc controls (the same scenes
with no cone), which are the measuring rig of every cone test."""
import ctypes
import math
import re

import pytest

from conftest import CSRC_DIR, OMFeature
from test_PP_unit_support import set_param, spawn, step

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION, SUPPLY = 0, 1, 2, 3, 4, 5, 6
FRIEND, ENEMY = 0, 1


def _const(name):
    m = re.search(rf"#define\s+{name}\s+([0-9.]+)", (CSRC_DIR / "om_constants.h").read_text())
    assert m, f"{name} not found in csrc/om_constants.h"
    return float(m.group(1))


BOMBARD_BASE = _const("OM_ROSTER_BOMBARD_DAMAGE")
CAP = BOMBARD_BASE * _const("OM_AOE_DAMAGE_CAP_MULTIPLIER")   # ALG-61: base x 4.0 = 70
CONE_RANGE, CONE_HALF = 400.0, 30.0
HP = 1000.0
UNKNOWN_TYPE = 99     # neither built in nor registered

# The main sector scene (attacker at the origin facing +x): name, x, y.
#   T: the target of record, nearest, on the axis.
#   S1..S3: inside the 30 degree, 400 wu sector (angles 18.4, 25.6, 23.2 degrees; distances 316, 277, 381).
#   O1, O2: 31.1 degrees either side (just outside the sector), but inside 150 wu of T (the disc takes them).
#   O3: 420 wu out on the axis (beyond the range); O4: behind the attacker (250 wu, farther than T).
SCENE = [("T", 200, 0), ("S1", 300, 100), ("S2", 250, -120), ("S3", 350, 150),
         ("O1", 214, 129), ("O2", 214, -129), ("O3", 420, 0), ("O4", -250, 0)]
SECTOR = {"T", "S1", "S2", "S3"}
DISC = {"T", "S1", "S2", "O1", "O2"}   # 150 wu about T: S1 141, S2 130, O1 129, O2 130 wu; S3 is 212 away


def _events(lib, w):
    out = []
    for i in range(lib.om_tactical_event_count(w)):
        k, a, b, t = ctypes.c_int32(), ctypes.c_uint32(), ctypes.c_int32(), ctypes.c_uint64()
        assert lib.om_tactical_event_get_at(w, i, ctypes.byref(k), ctypes.byref(a), ctypes.byref(b), ctypes.byref(t)) == 0
        out.append((k.value, a.value, b.value, t.value))
    return out


def set_cone(lib, w, utype, rng, half, share):
    return lib.om_roster_set_cone(w, utype, float(rng), float(half), float(share))


def volley(lib, world_factory, *, attacker=BOMBARD, cone=None, victims=SCENE, attacker_layer=0, layers=None,
           reach=None, params=None, stealth=(), cover=(), friendlies=(), cones_on=(), facing=0.0, fixture=None):
    """One shot of the attacker at the origin. `cone` is (range, half-angle degrees, share) set on the attacker's type
    (the call must return 0: on the E0 tree it returns -1 and the test fails here); `cones_on` is a list of
    (type, range, half, share) set on other types. `layers` maps a victim name to its layer (default the attacker's).
    `fixture` is called with (w, ids) after spawning, for setup a scene needs. Returns {name: hit points lost on the
    tick of the first shot, 'tick': that tick, 'T_is_target': whether the nearest victim named T was the target}."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    for name, value in (params or {}).items():
        assert set_param(lib, w, name, value) == 0
    if reach:
        assert lib.om_roster_set_reach(w, attacker, *reach) == 0
    if cone is not None:
        rc = set_cone(lib, w, attacker, *cone)
        assert rc == 0, f"om_roster_set_cone{(attacker,) + tuple(cone)} returned {rc} (-1 is the E0 stub: not built)"
    for (t, r, h, s) in cones_on:
        assert set_cone(lib, w, t, r, h, s) == 0
    a = spawn(lib, w, attacker, FRIEND, 0.0, 0.0, layer=attacker_layer)
    lib.om_unit_set_facing(w, a, facing)
    ids = {}
    for name, x, y in victims:
        u = spawn(lib, w, SUPPLY, ENEMY, float(x), float(y), layer=(layers or {}).get(name, attacker_layer))
        lib.om_unit_set_hp(w, u, HP)
        if name in stealth:
            lib.om_unit_set_stealth(w, u, 1)
        ids[name] = u
    for (x, y) in cover:
        lib.om_map_add_cover(w, float(x), float(y), 40.0, 5.0)
    friends = [spawn(lib, w, SUPPLY, FRIEND, float(x), float(y), layer=attacker_layer) for (x, y) in friendlies]
    for u in friends:
        lib.om_unit_set_hp(w, u, HP)
    if fixture:
        fixture(w, ids)
    watch = {**ids, **{f"friend{i}": u for i, u in enumerate(friends)}}
    for tick in range(1, 40):
        before = {n: lib.om_unit_get_hp(w, u) for n, u in watch.items()}
        step(lib, w)
        if any(k == 0 and sh == a for (k, sh, _t, _tk) in _events(lib, w)):
            out = {n: before[n] - lib.om_unit_get_hp(w, u) for n, u in watch.items()}
            out["tick"] = tick
            out["target"] = lib.om_unit_target(w, a)
            out["ids"] = ids
            return out
    pytest.fail("the attacker never fired in 39 ticks (scene setup)")


# ---------------------------------------------------------------- controls (green on the E0 tree)

def test_control_bombard_disc_on_the_scene_geometry(lib, world_factory):
    """R-084-03 / ALG-61 control: with no cone the Bombard's shot is the disc of 150 wu about its target: T, S1, S2, O1
    and O2 (all within 150 wu of T) each lose the same full amount, S3 (212 wu from T), O3 and O4 lose nothing. This is
    the measuring rig for every cone test below: the same scene, the same reader, only the cone differs."""
    r = volley(lib, world_factory)
    assert r["target"] == r["ids"]["T"]
    hit = {n for n, _x, _y in SCENE if r[n] > 0}
    assert hit == DISC, f"disc hit {sorted(hit)}, expected {sorted(DISC)}"
    full = r["T"]
    assert full > 0
    for n in DISC:
        assert r[n] == pytest.approx(full, rel=1e-12), f"{n} took {r[n]}, the target took {full}"


def test_R_082_06_a_cone_on_another_type_leaves_the_bombards_disc(lib, world_factory):
    """Spec ruling 9 'The Bombard's disc (R-084-03) stays until a cone is set on it': setting a cone on a DIFFERENT type
    (the Vanguard) leaves the Bombard's volley exactly the disc control. Red on the E0 tree through the cone call
    (-1); the volley it is compared with is the green disc control above."""
    base = volley(lib, world_factory)
    other = volley(lib, world_factory, cones_on=[(VANGUARD, CONE_RANGE, CONE_HALF, 1.0)])
    for n, _x, _y in SCENE:
        assert other[n] == pytest.approx(base[n], rel=1e-12), f"{n}: a Vanguard cone changed the Bombard's disc"


def test_control_reader_distinguishes_hit_from_not_hit(lib, world_factory):
    """Detector control: the volley reader reports a positive loss for a unit the disc hits and exactly 0 for one it
    does not, on the same shot (so 'did not lose hit points' below means 'was not hit')."""
    r = volley(lib, world_factory)
    assert r["T"] > 0 and r["S3"] == 0.0 and r["O4"] == 0.0


# ---------------------------------------------------------------- set_cone return values

VALID = [(CONE_RANGE, CONE_HALF, 1.0), (300.0, 45.0, 1.0), (150.0, 1.0, 0.0), (600.0, 180.0, 10.0), (0.5, 22.5, 0.25)]


@pytest.mark.parametrize("rng,half,share", VALID, ids=[f"{v[0]}-{v[1]}-{v[2]}" for v in VALID])
def test_R_082_06_set_cone_accepts_the_valid_bounds(lib, world_factory, rng, half, share):
    """R-082-06 / spec Contract: 0 for a known type with range >= 0, half-angle in [1, 180] and share in [0, 10], the
    bounds themselves included (half-angle 1 and 180, share 0 and 10). Red on the E0 tree: the stub answers -1."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    for t in (BOMBARD, VANGUARD, RAIDER):
        assert set_cone(lib, w, t, rng, half, share) == 0, f"type {t}: {(rng, half, share)} refused"


@pytest.mark.parametrize("bad_type", [UNKNOWN_TYPE, -1], ids=["type99", "type_minus1"])
def test_R_082_06_set_cone_unknown_type_is_minus_one(lib, world_factory, bad_type):
    """R-082-06 / spec Contract: -1 for a type that is neither built in nor registered. Paired with the same values on
    a known type returning 0, so the test is red on the E0 tree (where the stub answers -1 for both)."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert set_cone(lib, w, BOMBARD, CONE_RANGE, CONE_HALF, 1.0) == 0, "the known-type call must be accepted first"
    assert set_cone(lib, w, bad_type, CONE_RANGE, CONE_HALF, 1.0) == -1


REFUSED = [(-1.0, 30.0, 1.0), (-0.001, 30.0, 1.0), (400.0, 0.99, 1.0), (400.0, 0.0, 1.0), (400.0, 180.01, 1.0),
           (400.0, 360.0, 1.0), (400.0, 30.0, -0.01), (400.0, 30.0, 10.01)]


@pytest.mark.parametrize("rng,half,share", REFUSED, ids=[f"{v[0]}-{v[1]}-{v[2]}" for v in REFUSED])
def test_R_082_06_set_cone_refuses_a_value_outside_its_bounds(lib, world_factory, rng, half, share):
    """R-082-06 / spec Contract: -2 for range < 0, half-angle outside [1, 180] or share outside [0, 10], on a known
    type. Paired with an in-range call on the same type returning 0 (the control that the type is known). Red on
    the E0 tree: the stub answers -1."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert set_cone(lib, w, BOMBARD, CONE_RANGE, CONE_HALF, 1.0) == 0
    assert set_cone(lib, w, BOMBARD, rng, half, share) == -2


def test_R_082_06_range_zero_clears_and_is_accepted(lib, world_factory):
    """R-082-06 / spec Contract: range 0 clears the cone and returns 0 (with the other two values in bounds)."""
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert set_cone(lib, w, BOMBARD, CONE_RANGE, CONE_HALF, 1.0) == 0
    assert set_cone(lib, w, BOMBARD, 0.0, CONE_HALF, 1.0) == 0


# ---------------------------------------------------------------- the sector

@pytest.mark.parametrize("share", [0.25, 0.5, 1.0], ids=["share0.25", "share0.5", "share1"])
def test_R_082_06_three_in_the_sector_are_hit_at_share_one_outside_is_not(lib, world_factory, share):
    """R-082-06: with a cone (400 wu, 30 degrees, share s) on the Bombard, T (the target of record), S1, S2 and S3 lose
    hit points and O1..O4 lose none (O1 and O2 are inside the disc but 1.1 degrees outside the sector; O3 is 20 wu
    beyond the range; O4 is behind). The three sector victims lose identical amounts, in proportion to the share
    (s times what they lose at share 1.0), and the target of record loses exactly what the disc control's target
    loses: a single direct hit, not a direct hit plus a cone hit. Shares stay at or below 1.0 so that even the largest
    reading of a per-victim hit (base x share, no category multiplier) leaves the volley under the cap
    (T + 3 hits <= 3.5 + 3 x 17.5 = 56 < 70) and the whole sector is hit. Red on the E0 tree (the cone call answers -1)."""
    disc = volley(lib, world_factory)
    one = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, 1.0))
    r = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, share))
    assert r["target"] == r["ids"]["T"]
    assert {n for n, _x, _y in SCENE if r[n] > 0} == SECTOR, f"hit set {sorted(n for n, _x, _y in SCENE if r[n] > 0)}"
    assert r["T"] == pytest.approx(disc["T"], rel=1e-12), "the target of record was not hit by exactly one direct hit"
    x1 = one["S1"]
    assert x1 > 0 and one["S2"] == pytest.approx(x1, rel=1e-12) and one["S3"] == pytest.approx(x1, rel=1e-12)
    for n in ("S1", "S2", "S3"):
        assert r[n] == pytest.approx(share * x1, rel=1e-12), f"{n}: {r[n]} is not {share} x {x1}"


def test_R_082_06_share_zero_hits_only_the_target(lib, world_factory):
    """R-082-06: share 0 (a bound of the setting) leaves the sector victims untouched and the target of record takes
    its direct hit: the cone's whole effect scales with the share. Red on the E0 tree (cone call -1)."""
    disc = volley(lib, world_factory)
    r = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, 0.0))
    assert r["T"] == pytest.approx(disc["T"], rel=1e-12)
    assert all(r[n] == 0.0 for n, _x, _y in SCENE if n != "T")


def test_R_082_06_victims_are_hit_across_both_sides_of_the_facing_axis_and_inside_a_degree(lib, world_factory):
    """R-082-06: the sector is symmetric about the facing and its edge is the half-angle: victims at +29 and -29 degrees
    (250 wu out) are hit, at +31 and -31 degrees are not. Red on the E0 tree (cone call -1)."""
    def pt(deg):
        return (250.0 * math.cos(math.radians(deg)), 250.0 * math.sin(math.radians(deg)))
    victims = [("T", 200, 0)] + [(f"d{d}", *pt(d)) for d in (29, -29, 31, -31)]
    r = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, 1.0), victims=victims)
    assert r["d29"] > 0 and r["d-29"] > 0 and r["d31"] == 0.0 and r["d-31"] == 0.0


def test_R_082_06_the_range_edge_is_inclusive(lib, world_factory):
    """R-082-06 'boundary inclusive': a victim exactly 400 wu out on the axis (the cone range) is hit, one at 401 is
    not. Red on the E0 tree (cone call -1)."""
    victims = [("T", 200, 0), ("edge", 400, 0), ("past", 401, 0.0)]
    r = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, 1.0), victims=victims)
    assert r["edge"] > 0 and r["past"] == 0.0


def test_R_082_06_friendlies_in_the_sector_are_not_hit(lib, world_factory):
    """R-082-06 'every other enemy': a friendly unit in the sector loses nothing, on the same shot that hits the
    enemies there. Red on the E0 tree (cone call -1)."""
    r = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, 1.0), friendlies=[(300, 40)])
    assert r["S1"] > 0 and r["friend0"] == 0.0


def test_R_082_06_victims_need_no_sight_no_stealth_no_line(lib, world_factory):
    """R-082-06 / spec row E2: 'no sight, stealth or line check for victims (as the disc)'. Three victims in the
    sector are hit although (a) one stands 550 wu out, beyond the Bombard's 300 wu sensor and in no friendly's sight,
    (b) one is stealthed, (c) one has a cover disc across the line to it. The cone range is 600 so (a) is inside.
    Control: the same victims lose nothing when out of the sector. Red on the E0 tree (cone call -1)."""
    far = ("far", 550, 0)
    hidden = ("hidden", 300, 100)
    behind_cover = ("behind_cover", 450, -20)
    victims = [("T", 200, 0), far, hidden, behind_cover]
    r = volley(lib, world_factory, cone=(600.0, CONE_HALF, 1.0), victims=victims, stealth={"hidden"}, cover=[(350, -15)])
    assert r["far"] > 0, "a victim beyond every sight was spared"
    assert r["hidden"] > 0, "a stealthed victim was spared"
    assert r["behind_cover"] > 0, "a victim behind a cover disc was spared"


def test_R_082_06_ascending_unit_id_and_the_cap_with_the_target_counted_first(lib, world_factory):
    """R-082-06 / ALG-61: the target of record takes its direct hit first and it counts toward the cap; every other sector
    enemy follows in ASCENDING UNIT ID (not by distance, not by angle) until the running total reaches
    base x OM_AOE_DAMAGE_CAP_MULTIPLIER, the last hit truncated. The scene spawns the four sector victims Va..Vd
    BEFORE T (so T has the highest id) at distances 335, 316, 255, 380 (neither distance order nor id order is angle order).
    The share is derived from a measured reference run (share 0.1, hits are proportional to the share) so that each cone hit is 30 hit points (any reading of the
    per-victim formula then predicts the same sequence): with the cap 70 and T's direct hit, the prediction is
    min(30, cap - total) down the id list. Red on the E0 tree (cone call -1)."""
    victims = [("Va", 330, 60), ("Vb", 300, -100), ("Vc", 250, 50), ("Vd", 350, -150), ("T", 200, 0)]
    ref_share = 0.1     # small enough that the reference volley is far under the cap on any reading of the hit
    ref = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, ref_share), victims=victims)
    x_ref = ref["Va"]
    assert x_ref > 0 and all(ref[n] == pytest.approx(x_ref, rel=1e-12) for n in ("Vb", "Vc", "Vd"))
    share = 30.0 / x_ref * ref_share      # a cone hit is proportional to the share
    assert 0.0 <= share <= 10.0, f"fixture share {share} outside the setting's bounds (the reference hit is {x_ref})"
    r = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, share), victims=victims)
    direct = r["T"]
    assert direct == pytest.approx(ref["T"], rel=1e-12) and direct > 0
    total, expect = direct, {}
    for n in ("Va", "Vb", "Vc", "Vd"):        # ascending unit id: the spawn order above
        hit = min(30.0, max(0.0, CAP - total))
        expect[n] = hit
        total += hit
    for n in ("Va", "Vb", "Vc", "Vd"):
        assert r[n] == pytest.approx(expect[n], abs=1e-9), f"{n} lost {r[n]}, the ascending-id prediction is {expect[n]}"
    assert total == pytest.approx(CAP, abs=1e-9), "fixture does not reach the cap (setup)"
    assert direct + sum(r[n] for n in ("Va", "Vb", "Vc", "Vd")) == pytest.approx(CAP, abs=1e-9), "the volley did not stop at the cap"
    assert 0.0 < expect["Vc"] < 30.0 and expect["Vd"] == 0.0, "fixture: the cap should truncate Vc and spare Vd (setup)"
    assert r["Vd"] == 0.0, "the victim after the truncated one was hit: the volley did not stop at the cap"


def test_R_082_06_cap_binds_even_at_the_largest_share(lib, world_factory):
    """R-082-06 / ALG-61: the cap holds at the setting's maximum share (10): one volley over the whole scene never takes more
    than base x OM_AOE_DAMAGE_CAP_MULTIPLIER (70 for the Bombard) in total, and does reach it (the sector victims
    S1..S3 each at 10 x the share-1 hit exceed what is left). Red on the E0 tree (cone call -1)."""
    r = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, 10.0))
    total = sum(r[n] for n, _x, _y in SCENE)
    assert total == pytest.approx(CAP, abs=1e-9), f"total {total}, cap {CAP}"


def test_R_082_06_half_angle_180_is_a_disc_about_the_attacker(lib, world_factory):
    """spec Contract: 'half-angle 180 is a disc about the attacker, which differs from R-084-03's disc about the target'.
    With the cone (400 wu, 180 degrees) a victim exactly behind the attacker at 150 wu (350 wu from T, so no disc about
    T would reach it) is hit, as is one at 400 wu exactly (inclusive); one at 401 is not, and O3 at 420 neither.
    Red on the E0 tree (cone call -1)."""
    victims = [("T", 200, 0), ("behind", -150, 0), ("side", 0, 380), ("edge_back", -400, 0), ("past_back", -401, 0)]
    r = volley(lib, world_factory, cone=(CONE_RANGE, 180.0, 1.0), victims=victims)
    assert r["behind"] > 0 and r["side"] > 0 and r["edge_back"] > 0
    assert r["past_back"] == 0.0


def test_R_082_06_range_zero_restores_the_disc(lib, world_factory):
    """R-082-06 'range 0 restores [the disc]': after a cone is set and then cleared with range 0, the volley is the disc
    control, victim for victim and amount for amount; while the cone stands it is not (S3 is hit, O1 is not).
    Red on the E0 tree (cone call -1)."""
    disc = volley(lib, world_factory)
    cone = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, 1.0))
    assert cone["S3"] > 0 and cone["O1"] == 0.0 and disc["S3"] == 0.0 and disc["O1"] > 0
    cleared = volley(lib, world_factory, cones_on=[(BOMBARD, CONE_RANGE, CONE_HALF, 1.0), (BOMBARD, 0.0, CONE_HALF, 1.0)])
    for n, _x, _y in SCENE:
        assert cleared[n] == pytest.approx(disc[n], rel=1e-12), f"{n}: range 0 did not restore the disc"


def test_R_082_06_a_cone_attaches_to_any_type(lib, world_factory):
    """R-082-06 / Q-082-06 'something that can be added to any unit role': a Vanguard (range 300, a single-target type,
    no area attack today) with a cone hits the sector enemies; without it only its target loses hit points. Red on
    the E0 tree (cone call -1); the no-cone half is the control and is green."""
    victims = [("T", 200, 0), ("S1", 250, 60), ("S2", 260, -70), ("O4", -250, 0)]
    plain = volley(lib, world_factory, attacker=VANGUARD, victims=victims)
    assert plain["T"] > 0 and plain["S1"] == 0.0 and plain["S2"] == 0.0
    r = volley(lib, world_factory, attacker=VANGUARD, cone=(CONE_RANGE, CONE_HALF, 1.0), victims=victims)
    assert r["T"] == pytest.approx(plain["T"], rel=1e-12)
    assert r["S1"] > 0 and r["S2"] > 0 and r["O4"] == 0.0


# ---------------------------------------------------------------- reach offsets

def test_R_082_06_cone_victims_on_other_layers_follow_the_attackers_reach_and_the_area_multiplier(lib, world_factory):
    """R-082-06 'within the type's reach offsets' / spec: 'takes base x share x area offset multiplier'. The Bombard is on
    layer 2 with reach (up 2, down 1) and OM_TP_AREA_UP_2 = 0.25, OM_TP_AREA_DOWN_1 = 0.5; inside the sector stand a
    victim on its own layer (same), on layer 4 (up 2, in reach), on layer 1 (down 1, in reach) and, outside reach,
    on layer 0 (down 2). The in-reach victims lose 0.25 and 0.5 times what the same-layer victim loses; the down-2
    victim loses nothing. Control: the same-layer victim is hit. Red on the E0 tree (cone call -1)."""
    victims = [("T", 200, 0), ("same", 300, 60), ("up2", 300, -60), ("down1", 330, 20), ("down2", 340, -20)]
    layers = {"up2": 4, "down1": 1, "down2": 0}
    r = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, 1.0), victims=victims, attacker_layer=2, layers=layers,
               reach=(2, 1), params={"OM_TP_AREA_UP_2": 0.25, "OM_TP_AREA_DOWN_1": 0.5})
    assert r["same"] > 0
    assert r["up2"] == pytest.approx(0.25 * r["same"], rel=1e-9)
    assert r["down1"] == pytest.approx(0.5 * r["same"], rel=1e-9)
    assert r["down2"] == 0.0


def test_R_082_06_default_reach_zero_spares_every_other_layer(lib, world_factory):
    """R-082-06: with the Bombard's reach left at (0, 0) the cone reaches the attacker's own layer only: a sector victim one
    layer up and one layer down lose nothing while the same-layer ones are hit. Red on the E0 tree (cone call -1)."""
    victims = [("T", 200, 0), ("same", 300, 60), ("up1", 300, -60), ("down1", 330, 20)]
    r = volley(lib, world_factory, cone=(CONE_RANGE, CONE_HALF, 1.0), victims=victims, attacker_layer=2,
               layers={"up1": 3, "down1": 1})
    assert r["same"] > 0 and r["up1"] == 0.0 and r["down1"] == 0.0
