# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, ruling 7, "Contract / Engine", Pieces row E4.
# piece LAB-REV2-E4 (radius guard); rule R-096-08 (E-13 S-096, restated by S-208 R-208-01), register Q-096-01 option b.
"""S-208 radius guard (R-096-08, Q-096-01 option b; Westley 2026-10-13: "guard as a radius: chases within N wu of its
spot, returns past it", "for the whole game, not just the simulator").

The rule as the Architect ruled it for this piece (2026-10-14, reading B): the radius bounds how far the guard may WALK
from its post. A guard (om_command_guard; the unit's position at the order is its post) engages what its side sees
(R-093-02), steps toward the target as far as GUARD_RADIUS from the post and no farther, fires whenever the target is in
weapon range, and returns to the post when the target dies or when engaging it would take the guard past the radius. It
never crosses the radius. Defaults the Architect accepted: the return is made at the unit's own speed; two visible
enemies are taken nearest-actable first; the step is a transient move with no stored order, and nothing is left as a goal
after the return; the radius is measured from the post to the GUARD'S OWN centre (the walk bound), the target's position
only decides whether a step is needed. So a target is stepped for when (post to target) <= attack range + GUARD_RADIUS.

Numbers. GUARD_RADIUS_DRAFT is the DRAFT-guard-radius (200 wu, the R-087-05 leash; Architect draft, Westley to rule). The
Raider (range 200, sensor 800, speed 150 wu/s = 7.5 wu per tick) and the Bastion (range 800, sensor 300, speed 40) come
from csrc/om_constants.h; the Interceptor spotter (sensor 1000, range 250) likewise. Fixture distances keep a margin of
10 wu or more from every boundary (range + radius = 400 for the Raider, 1000 for the Bastion). Targets are Supply units
with 5000 hp (never fire, do not die by accident); a test that needs a death calls kill().

Observables: positions each tick (distance from the post), hp of the target, om_unit_get_destination (has_dest) and the
unit's target. FLOAT_SLACK_WU is float-rounding slack on the "never crosses the radius" assertion, not a tolerance on
the rule.

Red today and why (the built guard holds and never steps, csrc/unit.c: acquisition by weapon range only, and a guard
drops a target that is out of range): every scene in which the guard must step to fire sees the enemy's hp never fall.
Green today: the controls (an enemy already in range does not make the guard step; a move order ends the guard) and the
hold cases (an enemy that needs more than range + radius is not stepped for; an unseen enemy is not stepped for), which
guard against an over-wide build.

SUPERSEDED / RECHECK LIST (docstring-only; none of these files is edited here):
  tests/csim/test_PP_unit_guard.py::test_R_096_05_guard_does_not_step_toward_an_enemy_that_stays_out_of_range
      (Vanguard, enemy 450 wu, range 300: the step needed is 150 <= 200) is SUPERSEDED by R-096-08 (2026-10-13).
  tests/csim/test_PP_unit_guard.py::test_R_096_05_guard_holds_while_an_enemy_stands_beyond_range
      (Vanguard, enemy 500 wu: the step needed is 200, the radius edge) is SUPERSEDED by R-096-08 (2026-10-13).
  tests/csim/test_PP_unit_guard.py::test_R_096_05_guard_that_loses_its_target_does_not_resume_any_march
      needs a RECHECK after E4 (its guard now returns to its post after the kill; the scene was built on a guard that
      never leaves it).
  tests/csim/test_PP_unit_guard.py::test_R_096_05_choke_guard_holds_the_gap_against_a_larger_line
      needs a RECHECK after E4 (defenders may now step out of the gap toward a line 600 wu off).
  tests/skilllab/test_guard_order.py and tests/skilllab/fakes_guard.py are lab fakes on the built order: not edited
      here; re-run after E4.
"""
from test_PP_unit_guard import guard, move
from test_PP_unit_support import BASTION, RAIDER, SUPPLY, dest, hp, kill, pos, spawn, step, target
from test_PP_C_g3_support import can_see, dist

INTERCEPTOR = 1
GUARD_RADIUS_DRAFT = 200.0   # Architect draft (DRAFT-guard-radius, the R-087-05 leash), Westley to rule
FLOAT_SLACK_WU = 0.01        # float rounding only
BIG_HP = 5000.0
POST = (0.0, 0.0)


def inert(lib, w, x, y, faction=1):
    uid = spawn(lib, w, SUPPLY, faction, x, y)
    lib.om_unit_set_hp(w, uid, BIG_HP)
    return uid


def walk(lib, w, u, n, post=POST):
    """Step n ticks; return the guard's distance from the post after each tick."""
    out = []
    for _ in range(n):
        step(lib, w)
        out.append(dist(pos(lib, w, u), post))
    return out


def run_until_hit(lib, w, u, enemy, limit, post=POST):
    """Step until the enemy's hp has fallen (or limit ticks); return (distances from the post, hit)."""
    before = hp(lib, w, enemy)
    ds = []
    for _ in range(limit):
        step(lib, w)
        ds.append(dist(pos(lib, w, u), post))
        if hp(lib, w, enemy) < before:
            return ds, True
    return ds, False


def assert_home_and_clean(lib, w, u, why, post=POST):
    """The guard is back on its post (within a wu), holds no goal, and stays put: nothing is left over."""
    here = pos(lib, w, u)
    assert dist(here, post) <= 1.0, f"{why}: the guard is at {here}, not back on its post {post}"
    assert dest(lib, w, u)[0] == 0, f"{why}: a destination is left after the return: {dest(lib, w, u)}"
    step(lib, w, 60)
    assert dist(pos(lib, w, u), post) <= 1.0 and dest(lib, w, u)[0] == 0, \
        f"{why}: the guard moved or took a goal after it was home: {pos(lib, w, u)}, {dest(lib, w, u)}"


# ---- (1) the step, the engagement, the return ----

def test_R_096_08_Q_096_01_guard_steps_to_engage_stays_inside_the_radius_and_returns(lib, world_factory):
    """Raider guard at the post; a seen enemy 350 wu off (range 200, so a step of 150 is needed, inside the radius).
    The guard steps, the enemy's hp falls, the guard is never farther than GUARD_RADIUS from the post at any tick,
    and after the enemy dies it walks home and holds no order or goal. Red today: the guard never steps, so the
    enemy's hp never falls."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, *POST)
    enemy = inert(lib, w, 350.0, 0.0)
    assert can_see(lib, w, u, enemy) == 1, "fixture: the Raider (sensor 800) must see the enemy itself"
    assert guard(lib, w, [u]) == 0
    ds, hit = run_until_hit(lib, w, u, enemy, 200)
    assert hit, f"R-096-08: the guard should step and engage a seen enemy 350 wu off; it never hurt it (at {pos(lib, w, u)})"
    needed = 350.0 - 200.0
    assert max(ds) >= needed - 5.0, f"the guard fired without stepping the {needed} wu it needs: max {max(ds)}"
    ds += walk(lib, w, u, 60)
    assert max(ds) <= GUARD_RADIUS_DRAFT + FLOAT_SLACK_WU, \
        f"R-096-08: the guard crossed the radius: {max(ds)} wu from the post"
    kill(lib, w, enemy)
    ds = walk(lib, w, u, 120)
    assert max(ds) <= GUARD_RADIUS_DRAFT + FLOAT_SLACK_WU
    assert_home_and_clean(lib, w, u, "after the target died")


def test_R_096_08_Q_096_01_an_enemy_just_inside_range_plus_radius_is_stepped_for(lib, world_factory):
    """Boundary with margin: the enemy 380 wu off (range + radius is 400) needs a step of 180, 20 wu inside the
    radius. The guard engages it and still never crosses the radius. Red today: no step, no hit."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, *POST)
    enemy = inert(lib, w, 380.0, 0.0)
    assert guard(lib, w, [u]) == 0
    ds, hit = run_until_hit(lib, w, u, enemy, 200)
    assert hit, "R-096-08: an enemy 380 wu off (step 180 <= 200) should be engaged"
    ds += walk(lib, w, u, 60)
    assert max(ds) <= GUARD_RADIUS_DRAFT + FLOAT_SLACK_WU, f"crossed the radius: {max(ds)}"


# ---- (2) too far to engage inside the radius ----

def test_R_096_08_Q_096_01_an_enemy_needing_more_than_range_plus_radius_is_not_stepped_for(lib, world_factory):
    """The enemy 450 wu off needs a step of 250 > 200 (range 200 + radius 200 = 400, 50 wu margin). The guard stays
    exactly at the post for 150 ticks and the enemy takes no damage. Green today (the built guard holds); it guards
    against a build that steps anyway. The positive control is the 380 wu scene above."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, *POST)
    enemy = inert(lib, w, 450.0, 0.0)
    assert can_see(lib, w, u, enemy) == 1, "fixture: the enemy is seen, so only the distance can keep the guard home"
    assert guard(lib, w, [u]) == 0
    ds = walk(lib, w, u, 150)
    assert max(ds) <= FLOAT_SLACK_WU, f"R-096-08: the guard walked {max(ds)} wu for an enemy it cannot engage inside the radius"
    assert hp(lib, w, enemy) == BIG_HP
    assert dest(lib, w, u)[0] == 0


# ---- (3) a target that retreats beyond range + radius ----

def test_R_096_08_Q_096_01_a_target_that_retreats_beyond_range_plus_radius_releases_the_guard(lib, world_factory):
    """The guard has stepped and is hitting an enemy 350 wu off. The enemy then moves to 460 wu from the post
    (range + radius 400, 60 wu margin). The guard drops it and walks home; it never crosses the radius, never
    hurts the enemy again, and leaves no goal. Red today: the guard never steps, so the first part fails."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, *POST)
    enemy = inert(lib, w, 350.0, 0.0)
    assert guard(lib, w, [u]) == 0
    ds, hit = run_until_hit(lib, w, u, enemy, 200)
    assert hit, "R-096-08: fixture: the guard should have stepped and hit the enemy before it retreats"
    lib.om_unit_teleport(w, enemy, 460.0, 0.0, 0)
    ds += walk(lib, w, u, 2)
    seen_hp = hp(lib, w, enemy)
    ds += walk(lib, w, u, 160)
    assert max(ds) <= GUARD_RADIUS_DRAFT + FLOAT_SLACK_WU, \
        f"R-096-08: the guard crossed the radius after the target retreated: {max(ds)}"
    assert hp(lib, w, enemy) == seen_hp, "the guard kept hitting a target it cannot engage inside the radius"
    assert_home_and_clean(lib, w, u, "after the target retreated")


# ---- (4) fog: only what the side sees ----

def test_R_096_08_Q_096_01_a_stealthed_enemy_is_not_stepped_for(lib, world_factory):
    """R-093-02: the enemy 350 wu off is stealthed, so nobody on the side sees it: no step, no damage. Green today;
    it guards against a build that acquires from the grid without the sight test. Positive control: the
    unstealthed scene (the first test) steps and hits."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, *POST)
    enemy = inert(lib, w, 350.0, 0.0)
    lib.om_unit_set_stealth(w, enemy, 1)
    assert guard(lib, w, [u]) == 0
    ds = walk(lib, w, u, 150)
    assert max(ds) <= FLOAT_SLACK_WU, f"the guard stepped toward an unseen enemy: {max(ds)} wu"
    assert hp(lib, w, enemy) == BIG_HP
    # fixture check: the engine really ignores a stealthed enemy (one already in weapon range is not hit either)
    w2 = world_factory(n_regions=1)
    u2 = spawn(lib, w2, RAIDER, 0, *POST)
    close = inert(lib, w2, 150.0, 0.0)
    lib.om_unit_set_stealth(w2, close, 1)
    assert guard(lib, w2, [u2]) == 0
    step(lib, w2, 100)
    assert hp(lib, w2, close) == BIG_HP, "fixture: stealth should hide the enemy from a guard"


def _bastion_scene(lib, w, spotter):
    """Bastion guard (range 800, sensor 300) with the enemy 950 wu off: a step of 150 is needed (inside the radius),
    and the enemy is far outside the Bastion's own sensor. The optional spotter is a friendly Interceptor (sensor
    1000, range 250) at x = 100: it sees the enemy (850 wu) and cannot fire at it."""
    u = spawn(lib, w, BASTION, 0, *POST)
    enemy = inert(lib, w, 950.0, 0.0)
    spot = spawn(lib, w, INTERCEPTOR, 0, 100.0, 0.0) if spotter else None
    assert can_see(lib, w, u, enemy) == 0, "fixture: the Bastion must not see the enemy itself"
    if spot is not None:
        assert can_see(lib, w, spot, enemy) == 1, "fixture: the spotter must see the enemy"
    return u, enemy


def test_R_096_08_Q_096_01_an_enemy_the_side_does_not_see_is_not_stepped_for(lib, world_factory):
    """Bastion guard, enemy 950 wu off, nobody on the side sees it: the guard stays at the post for 200 ticks, the
    enemy takes no damage. Green today; guards against stepping on unseen targets."""
    w = world_factory(n_regions=1)
    u, enemy = _bastion_scene(lib, w, spotter=False)
    assert guard(lib, w, [u]) == 0
    ds = walk(lib, w, u, 200)
    assert max(ds) <= FLOAT_SLACK_WU, f"the Bastion stepped toward an enemy its side does not see: {max(ds)} wu"
    assert hp(lib, w, enemy) == BIG_HP


def test_R_096_08_Q_096_01_an_enemy_seen_by_a_spotter_is_stepped_for(lib, world_factory):
    """Positive control for the unseen test (same scene plus a friendly spotter that sees the enemy): "engages any
    target its side can see" (R-096-08, R-093-02), so the Bastion steps the 150 wu it needs (2 wu per tick), hits
    the enemy, and never crosses the radius. Red today: the guard never steps."""
    w = world_factory(n_regions=1)
    u, enemy = _bastion_scene(lib, w, spotter=True)
    assert guard(lib, w, [u]) == 0
    ds, hit = run_until_hit(lib, w, u, enemy, 300)
    assert hit, f"R-096-08: the side sees the enemy, so the guard should step and fire; it is at {pos(lib, w, u)}"
    assert max(ds) >= 150.0 - 5.0
    ds += walk(lib, w, u, 60)
    assert max(ds) <= GUARD_RADIUS_DRAFT + FLOAT_SLACK_WU


# ---- (5) controls, green today ----

def test_control_R_096_08_Q_096_01_an_enemy_in_weapon_range_does_not_make_the_guard_step(lib, world_factory):
    """Control (green today and after): the enemy 150 wu off is inside range 200. The guard fires at once and does
    not move a wu: stepping is only for what is out of range. It also shows the hit detector reads a real hit."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, *POST)
    enemy = inert(lib, w, 150.0, 0.0)
    assert guard(lib, w, [u]) == 0
    ds, hit = run_until_hit(lib, w, u, enemy, 100)
    assert hit, "fixture: a guard fires at an enemy in weapon range"
    ds += walk(lib, w, u, 60)
    assert max(ds) <= FLOAT_SLACK_WU, f"the guard stepped though the enemy was in range: {max(ds)} wu"
    assert dest(lib, w, u)[0] == 0


def test_control_R_096_08_Q_096_01_a_move_order_ends_the_guard(lib, world_factory):
    """Control (green today and after): a guard with a seen enemy 350 wu off is given a move order to a point 600 wu
    from the post (past the radius; the radius binds the guard, not a move). The unit walks well past the radius (it
    parks a little short of the point, as moves do) and stays: the guard is over, so it neither stops at the radius
    nor returns to the old post."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, *POST)
    inert(lib, w, 350.0, 0.0)
    assert guard(lib, w, [u]) == 0
    step(lib, w, 10)
    assert move(lib, w, [u], 0.0, -600.0) == 0
    step(lib, w, 200)
    here = pos(lib, w, u)
    assert dist(here, POST) > GUARD_RADIUS_DRAFT + 100.0, \
        f"a move order is not bound by the guard radius, yet the unit is at {here}"
    step(lib, w, 100)
    assert dist(pos(lib, w, u), here) <= 1.0, "the unit moved on (back toward the old post?): the guard was not ended"


# ---- (6) two visible enemies: nearest actable first ----

def test_R_096_08_Q_096_01_two_visible_enemies_nearest_actable_is_taken_first(lib, world_factory):
    """Enemy B 300 wu south, enemy A 350 wu east (both need a step inside the radius; 50 wu apart). The guard takes
    the nearer, B, first: B's hp falls, A's does not (from the guard's stepped position A is out of range). Once B
    is killed the guard takes A, and stays inside the radius throughout. After A is killed it returns home. Red
    today: neither is reachable without a step, so B's hp never falls."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, RAIDER, 0, *POST)
    far_a = inert(lib, w, 350.0, 0.0)
    near_b = inert(lib, w, 0.0, -300.0)
    assert guard(lib, w, [u]) == 0
    ds, hit = run_until_hit(lib, w, u, near_b, 200)
    assert hit, "R-096-08: the nearer visible enemy (300 wu) should be engaged by a step"
    ds += walk(lib, w, u, 40)
    assert hp(lib, w, far_a) == BIG_HP, "the guard hit the farther enemy while the nearer one stood"
    assert target(lib, w, u) == near_b
    kill(lib, w, near_b)
    ds2, hit2 = run_until_hit(lib, w, u, far_a, 300)
    assert hit2, "R-096-08: once the nearer enemy is dead the guard should take the other"
    ds2 += walk(lib, w, u, 40)
    assert max(ds + ds2) <= GUARD_RADIUS_DRAFT + FLOAT_SLACK_WU, f"crossed the radius: {max(ds + ds2)}"
    kill(lib, w, far_a)
    walk(lib, w, u, 120)
    assert_home_and_clean(lib, w, u, "after both targets died")
