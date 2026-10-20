# Rule pins: R-087-05@6cbf99, R-087-08@d94418, R-087-09@47a492, R-097-03@6780d8, R-098-01@9bd56a, R-190-07@25c4a2
"""VG-T-R087-TESTS (Lane T, T5): R-087-09, steer to a clear line or drop a blocked target. PATH: PIPE.

Rule (docs/bible/epics/E-11-units-and-combat.md, word for word):
R-087-09  Given an idle or attack-moving unit with a target within its attack range whose line of fire is blocked by
units, cover or ground, When evaluated, Then it steers around the blockers by the probe of blocked movement (R-097-03)
until it reaches a spot with a clear line, and if it finds none within 1 s (20 ticks) it drops the target and acquires
another (Westley, 2026-10-07: blocked fire is handled like blocked movement; "a unit gives up to pick another target if
it can't find a firing spot within 1 second"). An obstacle is a detour, never a full stop (E-17 R-190-07).

Path: PIPE. Every scene is a mission started the way the client starts it (`set_seed`, `mission_start`,
`mission_begin`), driven only by `command` verbs and `tactical_step`, and read only from the tactical frames (unit
`x`, `y`, `hp`, `target`; `visible`). The wall is the mission's own terrain: the cover disc `map.cover[0]` of the
`mission_begin` frame (seed 20, centre (8000, 8000), r 400, h 5, class 2). No sim function is called by hand.

Why this is a new file: tests/csim/test_PP_unit_blocked_target.py (A171, R-087-05) calls the C functions with hand
placed walls and checks that an attack-moving unit keeps WALKING its route while its target is blocked. It says
nothing about steering to a clear line, the 20-tick give-up or re-acquiring (green-tests report D5d, N8).

Premise (dumped by running the scenes, 2026-10-20; every number below is asserted by `_premise` in every test, so a
sim change that moves the scene fails with "PREMISE", never with a rule failure):
  seed 20, n_regions 80, features 1..7, `set_seed` with new_campaign false, `step` 10, `mission_start` faction 0,
  `mission_begin`. Archetype 0 (canvas 16000): own faction 0 (45 units), enemy faction 2 (49 units). Cover disc
  (8000, 8000) r 400. The pipe accepts `command` verbs for ANY unit id (om_pipe.c handle_command checks no faction),
  which is how the scene is staged: enemy Raiders 52 (E0, the blocked target) and 46 (E1, the second enemy) are
  walked to their spots, and own Raider 1 (the spotter A) reveals them. The enemy macro re-orders its force every 40
  ticks (enemy_macro.c om_macro_issue_group_orders), so the scene re-issues the pins every 20 ticks (every tick
  during observation); the rest of the enemy force is pinned at its home corner (8000, 15900) the same way.
  U = own Bastion 45 (range 800, sensor 300, speed 40 wu/s = 2 wu per tick; its hp 1050 keeps it alive). E0 and E1
  are Raiders (range 200), so neither can hit U at 650 to 720 wu; the spotter stands 300 wu or more from both.
  E0 settles at (8329.6, 7719.6), 21.6 wu from where it was sent (a mover stops short of its point).
  Scenes (case: where U, E1 and the spotter stand; wu):
    nogap  U (7634.9, 7667.5)   E1 (7898.0, 6996.9)  A parks (10434, 7038) then (8634, 7038)
           U to E0 696.6, U to E1 720.3; the line U-E0 crosses the disc (blocked), U-E1 is clear; the nearest
           clear-line spot for U is 94 wu away (47 ticks at 2 wu per tick), counting spots inside the disc (a
           unit standing in cover is not hidden by it, tactical_move.c om_combat_cover_blocks).
    gap    U (7742.5, 7440.9)   E1 (8230.8, 6983.3)  A parks (10659, 7737) then (8920, 7272)
           U to E0 649.9, U to E1 669.2; blocked, with a clear-line spot 22 wu away (11 ticks).
    clear  U (7788.3, 7351.7)   E1 (8334.8, 6952.0)  A parks (10531, 8236) then (8972, 7336)
           the same scene with U moved off the shadow: the line to E0 is clear (the positive control).
  The spotter is the only own unit near: it walks from its park to its final spot (7.5 wu per tick), E0 is revealed
  first (tick 5024 or 5026) and E1 five or six ticks later (5030, 5031), so U (idle, no order, nothing visible before) takes
  E0, the nearer enemy (650 to 697 against 669 to 720), as its first target on its next 4-tick cohort turn.
  "The block" starts at t_b, the first tick the frame shows U with a target (tick 5028 in every scene; always E0, id 52);
  the assertions' deadline is
  t_b + 20 + OM_TARGETING_COHORT_COUNT = t_b + 24 = 5052 (see Deadline).
Attack-move (`am`) scenes send `attack_move` for U a few ticks before the reveal, to a point 400 wu beyond E0 on the
line from U through E0, so U is walking its route when it takes E0.

Positive controls (green today): each scene's `test_premise_*`, and `test_control_clear_line_target_is_fired_on_...`
(the clear scene: U takes E0 and E0's hp falls within 20 ticks), which proves the staging, the reveal, the tick count
and the hp read-out work, so a red rule test means the rule is missing and not that the harness is broken.

Red list (per the brief; pasted failing lines are in the VG-T-R087-TESTS report):
  test_R_087_09_blocked_target_is_dropped_for_the_second_enemy_within_20_ticks[idle] and [am]  (no gap)
  test_R_087_09_unit_steers_to_a_clear_line_and_fires_at_the_first_target[idle] and [am]       (gap under 20 ticks)
If the gap pair is also red the rule is not built (unit.c holds a blocked target for ever, nothing steers, nothing
gives up) and VG-T-R087-WIRE (T6) is the build.

Deadline (a reading, Westley to confirm; Architect 2026-10-20): the rule's 20 ticks is the give-up timer. Re-acquiring
is done on the unit's next 4-tick cohort turn, the engine's granularity (R-087-08), so every assertion's deadline is
t_b + 20 + OM_TARGETING_COHORT_COUNT = t_b + 24 (COHORT_TICKS below, csrc/om_constants.h:533). The 20 itself is not
changed, and the gap and the walking distance premises still use 20 ticks.

Status: the four red tests carry `xfail(strict=True)` (FINDING-r087-09-not-built, owner VG-T-R087-WIRE): the file
reports 6 passed and 4 xfailed, and the first test that passes because the rule is built turns into a failure
(XPASS strict) so the mark is removed in the same piece. Failing lines when run without the marks (--runxfail), deadline t_b + 24 = 5052 (tests/csim/test_R_087_09_blocked_line.py):
  [nogap idle], [nogap am] :373: AssertionError: R-087-09: still holding target 52 at tick 5052, the deadline (t_b 5028 + 20 + 4); E1 (46) never taken
  [gap idle] :392: AssertionError: R-087-09: E0 (52) was not fired on by tick 5052 (t_b 5028 + 20 + 4); U at 7742.5, 7440.9, a clear-line spot 22 wu away
  [gap am]   :392: AssertionError: R-087-09: E0 (52) was not fired on by tick 5052 (t_b 5028 + 20 + 4); U at 7805.7, 7470.9, a clear-line spot 22 wu away

Not tested here: units as blockers (R-098-01 says units never block fire), movement past idle own units (Q-087-02).
"""
import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
_spec = importlib.util.spec_from_file_location("long_harness", ROOT / "tests/long/harness.py")
_h = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_h)

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")

# ---- the staged mission: ids and numbers dumped from the pipe (see the docstring) ----
SEED = 20
FEATURES = [1, 2, 3, 4, 5, 6, 7]
U_ID, A_ID, E0_ID, E1_ID = 45, 1, 52, 46          # own Bastion, own Raider spotter, enemy Raiders
BASTION, RAIDER = 5, 0
DISC = (8000.0, 8000.0, 400.0)                     # centre x, y, r of map.cover[0]
HOME = (8000.0, 15900.0)                           # where the rest of the enemy force is pinned
E0_SENT = (8330.0, 7700.0)
A_PARK, U_PARK = (8300.0, 5000.0), (7670.0, 6500.0)   # where the spotter and U wait while E0 settles
BASTION_WU_PER_TICK = 40.0 / 20.0                  # OM_ROSTER_BASTION_SPEED 40 wu/s, 20 ticks/s
GIVE_UP_TICKS = 20                                 # R-087-09: "within 1 s (20 ticks)"; the rule's own number, untouched
# Re-acquisition runs on a 4-tick cohort turn (R-087-08), the engine's granularity: a unit that gives up at tick 20
# takes its next target on its next turn, up to OM_TARGETING_COHORT_COUNT ticks later. Source: csrc/om_constants.h:533
# `#define OM_TARGETING_COHORT_COUNT 4` (not exported by the library: ouroboros_sim.h has only the per-unit slot
# om_unit_targeting_cohort, line 2155). Defined once here; if the constant changes, so must this line.
COHORT_TICKS = 4
DEADLINE_TICKS = GIVE_UP_TICKS + COHORT_TICKS      # deadline = t_b + 20 + OM_TARGETING_COHORT_COUNT (a reading)
ATTACK_RANGE = 800.0                               # Bastion
FULL_HP = 250.0                                    # Raider max_hp (profiles in the mission_begin frame)
# scene -> where U is sent, where E1 is sent, the spotter's park and its final spot
SCENES = {
    "nogap": dict(u=(7634.0, 7689.0), e1=(7898.0, 6981.0), a_park=(10434.0, 7038.0), a_fin=(8634.0, 7038.0)),
    "gap": dict(u=(7742.0, 7463.0), e1=(8232.0, 6961.0), a_park=(10659.0, 7737.0), a_fin=(8920.0, 7272.0)),
    "clear": dict(u=(7788.0, 7374.0), e1=(8336.0, 6934.0), a_park=(10531.0, 8236.0), a_fin=(8972.0, 7336.0)),
}
T_PHASE1, T_PHASE2, T_STAGED = 1300, 2600, 4800    # ticks: E0 settles; E1 and U sent; scene staged


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _blocked(a, b):
    """The fire side of cover, as om_combat_cover_blocks (tactical_move.c): a disc blocks the segment when it passes
    through it and neither endpoint stands inside it (layer 0 is below the disc height 5)."""
    cx, cy, r = DISC
    if _dist(a, (cx, cy)) <= r or _dist(b, (cx, cy)) <= r:
        return False
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((cx - a[0]) * dx + (cy - a[1]) * dy) / l2)) if l2 else 0.0
    px, py = a[0] + dx * t - cx, a[1] + dy * t - cy
    return px * px + py * py < r * r


def _gap_wu(u, e0):
    """Walking distance from u to the nearest spot within range of e0 whose line to e0 is clear (spots inside the
    disc count: standing in cover hides nobody)."""
    for rad in range(0, 300, 2):
        for ang in range(0, 360, 3):
            p = (u[0] + rad * math.cos(math.radians(ang)), u[1] + rad * math.sin(math.radians(ang)))
            if _dist(p, e0) <= ATTACK_RANGE - 10.0 and not _blocked(p, e0):
                return float(rad)
    return 999.0


class _Mission:
    """A pipe-started mission; frames folded into a unit table as the client does (full frame, then deltas)."""

    def __init__(self):
        self.pp = _h.Pipe()
        self.fails = 0
        self.pp.cmd("set_seed", seed=SEED, n_regions=80, features=FEATURES, new_campaign=False)
        self.pp.cmd("step", n=10)
        while self.pp._read()["type"] != "ack":
            pass
        m = self.pp.send("mission_start", faction=0)
        assert m["type"] == "mission", m
        f = self.pp.send("mission_begin")
        assert f["type"] == "tactical" and f["full"], f
        self.units = {u["id"]: u for u in f["units"]}
        self.cover = f["map"]["cover"]
        self.vis = set(f["visible"]["0"])
        self.tick = f["tick"]

    def cmd(self, verb, ids, **kw):
        r = self.pp.send("command", verb=verb, units=list(ids), **kw)
        if r["type"] != "ack":
            self.fails += 1
        return r

    def step(self, n=1):
        f = self.pp.send("tactical_step", n=n)
        assert f["type"] == "tactical", f
        if f.get("full"):
            self.units = {u["id"]: u for u in f["units"]}
        else:
            for i in f.get("units_removed", []):
                self.units.pop(i, None)
            for u in f.get("units_changed", []):
                self.units[u["id"]] = u
        self.vis = set(f["visible"]["0"])
        self.tick = f["tick"]
        return f

    def pos(self, i):
        u = self.units[i]
        return (u["x"], u["y"])

    def pin_enemy_force(self):
        """The enemy macro re-orders its force every 40 ticks; this puts it back. Everything that is not E0/E1."""
        rest = [i for i, u in self.units.items() if u["faction"] != 0 and i not in (E0_ID, E1_ID)]
        if rest:
            self.cmd("move", rest, x=HOME[0], y=HOME[1])

    def close(self):
        self.pp.close()


_CACHE = {}


def _scene(case, mode):
    """Stage and run one scene; returns the premise facts and the per-tick trace from the reveal on."""
    key = (case, mode)
    if key not in _CACHE:
        _CACHE[key] = _run(case, mode)
    return _CACHE[key]


def _run(case, mode):
    sc = SCENES[case]
    m = _Mission()
    try:
        facts = dict(case=case, mode=mode, cover=m.cover, types={i: m.units[i]["type"] for i in (U_ID, A_ID, E0_ID, E1_ID)},
                     factions={i: m.units[i]["faction"] for i in (U_ID, A_ID, E0_ID, E1_ID)})
        # phase 1: E0 walks to its spot, everything else parks
        while m.tick < T_PHASE1:
            m.pin_enemy_force()
            m.cmd("move", [E0_ID], x=E0_SENT[0], y=E0_SENT[1])
            m.cmd("move", [A_ID], x=A_PARK[0], y=A_PARK[1])
            m.cmd("move", [U_ID], x=U_PARK[0], y=U_PARK[1])
            m.step(20)
        e0 = m.pos(E0_ID)
        # phase 2: E1 walks to its spot, U to its own
        while m.tick < T_PHASE2:
            m.pin_enemy_force()
            m.cmd("move", [E0_ID], x=e0[0], y=e0[1])
            m.cmd("move", [E1_ID], x=sc["e1"][0], y=sc["e1"][1])
            m.cmd("move", [A_ID], x=A_PARK[0], y=A_PARK[1])
            m.cmd("move", [U_ID], x=sc["u"][0], y=sc["u"][1])
            m.step(20)
        e1 = m.pos(E1_ID)
        # phase 3: the spotter goes to its park for this scene; U finishes its walk
        while m.tick < T_STAGED:
            m.pin_enemy_force()
            m.cmd("move", [E0_ID], x=e0[0], y=e0[1])
            m.cmd("move", [E1_ID], x=e1[0], y=e1[1])
            m.cmd("move", [A_ID], x=sc["a_park"][0], y=sc["a_park"][1])
            m.cmd("move", [U_ID], x=sc["u"][0], y=sc["u"][1])
            m.step(20)
        facts.update(staged_tick=m.tick, u=m.pos(U_ID), e0=m.pos(E0_ID), e1=m.pos(E1_ID), a=m.pos(A_ID),
                     u_target=m.units[U_ID]["target"], u_hp=m.units[U_ID]["hp"], vis_enemies=sorted(i for i in m.vis if m.units[i]["faction"] != 0),
                     gap=_gap_wu(m.pos(U_ID), m.pos(E0_ID)))
        goal = None
        if mode == "am":
            ux, uy = m.pos(U_ID)
            ex, ey = m.pos(E0_ID)
            d = _dist((ux, uy), (ex, ey))
            goal = (ex + 400.0 * (ex - ux) / d, ey + 400.0 * (ey - uy) / d)
            facts["goal"] = goal
        # phase 4: reveal and observe
        trace, am_sent, tb = [], False, None
        for k in range(700):
            if k % 20 == 0:
                m.pin_enemy_force()
            m.cmd("move", [E0_ID], x=m.pos(E0_ID)[0], y=m.pos(E0_ID)[1])
            m.cmd("move", [E1_ID], x=m.pos(E1_ID)[0], y=m.pos(E1_ID)[1])
            m.cmd("move", [A_ID], x=sc["a_fin"][0], y=sc["a_fin"][1])
            if goal and not am_sent and _dist(m.pos(A_ID), m.pos(E0_ID)) <= 850.0:
                m.cmd("attack_move", [U_ID], x=goal[0], y=goal[1])
                am_sent = True
            m.step(1)
            u = m.units[U_ID]
            trace.append(dict(t=m.tick, tgt=u["target"], u=(u["x"], u["y"]), uhp=u["hp"], e0=m.pos(E0_ID), e1=m.pos(E1_ID),
                              e0hp=m.units[E0_ID]["hp"], e1hp=m.units[E1_ID]["hp"], v0=E0_ID in m.vis, v1=E1_ID in m.vis,
                              vis_enemies=sorted(i for i in m.vis if m.units[i]["faction"] != 0)))
            if tb is None and u["target"] != -1:
                tb = len(trace) - 1
            if tb is not None and len(trace) - 1 >= tb + 80:
                break
        facts["tb"] = tb
        facts["am_sent"] = am_sent
        facts["pin_failures"] = m.fails
        return facts, trace
    finally:
        m.close()


def _premise(case, mode):
    """The scene is what the docstring says. A failure here is a broken scene, never a rule failure."""
    facts, trace = _scene(case, mode)
    why = []

    def need(ok, msg):
        if not ok:
            why.append(msg)

    need(facts["cover"] == [{"x": 8000, "y": 8000, "r": 400, "h": 5, "class": 2}], "cover %r" % (facts["cover"],))
    need(facts["types"] == {U_ID: BASTION, A_ID: RAIDER, E0_ID: RAIDER, E1_ID: RAIDER}, "unit types %r" % (facts["types"],))
    need(facts["factions"][U_ID] == 0 and facts["factions"][A_ID] == 0 and facts["factions"][E0_ID] != 0
         and facts["factions"][E1_ID] != 0, "factions %r" % (facts["factions"],))
    need(facts["u_target"] == -1 and facts["vis_enemies"] == [], "before the reveal U has target %r and the side sees %r"
         % (facts["u_target"], facts["vis_enemies"]))
    need(facts["u_hp"] == 1050, "U hp %r" % facts["u_hp"])
    u, e0, e1 = facts["u"], facts["e0"], facts["e1"]
    d0, d1 = _dist(u, e0), _dist(u, e1)
    need(d0 < d1 <= ATTACK_RANGE, "E0 must be the nearer and E1 within the Bastion's range 800: %.1f, %.1f" % (d0, d1))
    need(_dist(facts["a"], e0) > 900 and _dist(facts["a"], e1) > 900, "the spotter must start out of sensor range")
    tb = facts["tb"]
    need(tb is not None, "U never took a target in 700 ticks of reveal")
    if tb is not None:
        row = trace[tb]
        need(row["tgt"] == E0_ID, "U's first target is %r, not E0 (%d)" % (row["tgt"], E0_ID))
        win = trace[tb:tb + DEADLINE_TICKS + 1]
        need(len(win) == DEADLINE_TICKS + 1, "trace ends before t_b + 24")
        need(all(r["vis_enemies"] in ([E0_ID], [E1_ID], sorted([E0_ID, E1_ID])) for r in win), "another enemy became visible: %r"
             % [r["vis_enemies"] for r in win if r["vis_enemies"] not in ([E0_ID], [E1_ID], sorted([E0_ID, E1_ID]))][:2])
        need(any(r["v1"] for r in trace[tb:tb + 11]), "E1 is not visible within 10 ticks of t_b")
        if case != "clear":   # a Raider that is shot flinches; only the blocked scenes promise a still target
            need(all(r["e0"] == win[0]["e0"] and r["e1"] == win[0]["e1"] for r in win), "E0 or E1 moved during the window")
        need(all(r["uhp"] == 1050 for r in win), "U was hit")
        if mode == "am":
            need(facts["am_sent"], "the attack-move order was never sent")
            need(_dist(win[0]["u"], u) <= 40.0, "U walked %.1f wu before t_b" % _dist(win[0]["u"], u))
        else:
            need(all(r["u"] == win[0]["u"] for r in win), "an idle U moved")
        if case in ("nogap", "gap"):
            need(all(_blocked(r["u"], r["e0"]) for r in win), "the line U-E0 is not blocked on every tick of the window")
            need(all(not _blocked(r["u"], r["e1"]) for r in win), "the line U-E1 is not clear on every tick of the window")
        else:
            need(all(not _blocked(r["u"], r["e0"]) for r in win), "the line U-E0 is not clear on every tick of the window")
    if case == "nogap":
        need(facts["gap"] > BASTION_WU_PER_TICK * GIVE_UP_TICKS, "a clear-line spot is only %.0f wu away" % facts["gap"])
    elif case == "gap":
        need(0 < facts["gap"] < BASTION_WU_PER_TICK * GIVE_UP_TICKS, "the clear-line spot is %.0f wu away, not under 40" % facts["gap"])
    need(facts["pin_failures"] == 0, "%d pin commands refused" % facts["pin_failures"])
    return facts, trace, why


def _assert_premise(case, mode):
    facts, trace, why = _premise(case, mode)
    assert not why, "PREMISE broken (scene %s/%s): %s" % (case, mode, "; ".join(why))
    return facts, trace


def _first(trace, pred):
    for r in trace:
        if pred(r):
            return r
    return None


# ------------------------------------------------------------------ positive controls (green today)

@pytest.mark.parametrize("case,mode", [("nogap", "idle"), ("nogap", "am"), ("gap", "idle"), ("gap", "am"), ("clear", "idle")])
def test_premise_the_scene_is_staged_through_the_pipe_as_dumped(case, mode):
    """Control: the scene is what the docstring dumped (blocked or clear lines, the nearer first target, the second
    enemy visible and clear, the clear-line spot's distance). Green today."""
    _assert_premise(case, mode)


def test_control_clear_line_target_is_fired_on_idle():
    """Control (R-087-09 is about a BLOCKED line): the same scene with U off the shadow takes E0 and E0's hp falls
    within 20 ticks of t_b. Green today; it shows the reveal, the tick count and the hp read-out work."""
    facts, trace = _assert_premise("clear", "idle")
    tb = facts["tb"]
    hit = _first(trace[tb:], lambda r: r["e0hp"] < FULL_HP)
    assert hit is not None and hit["t"] <= trace[tb]["t"] + DEADLINE_TICKS, (
        "a clear line to E0 was not fired on within %d ticks of t_b %d" % (DEADLINE_TICKS, trace[tb]["t"]))


# ------------------------------------------------------------------ the rule (red today)

@pytest.mark.xfail(strict=True, reason="VG-T-R087-WIRE: R-087-09 not built, FINDING-r087-09-not-built")
@pytest.mark.parametrize("mode", ["idle", "am"])
def test_R_087_09_blocked_target_is_dropped_for_the_second_enemy_within_20_ticks(mode):
    """R-087-09, no gap: the line to E0 is blocked and the nearest clear-line spot is more than 20 ticks of walking
    away (94 wu against 40). E1 is visible, in range and clear. No later than 20 ticks after t_b the unit has dropped
    E0, targets E1 and has fired at it (E1's hp falls). Red today: unit.c keeps the blocked target for ever (an
    idle unit) or walks its route holding it (an attack-moving unit); nothing gives up."""
    facts, trace = _assert_premise("nogap", mode)
    tb = facts["tb"]
    deadline = trace[tb]["t"] + DEADLINE_TICKS
    switched = _first(trace[tb:], lambda r: r["tgt"] == E1_ID)
    assert switched is not None and switched["t"] <= deadline, (
        "R-087-09: still holding target %r at tick %d, the deadline (t_b %d + 20 + 4); E1 (%d) never taken"
        % (trace[tb + DEADLINE_TICKS]["tgt"], deadline, trace[tb]["t"], E1_ID))
    fired = _first(trace[tb:], lambda r: r["e1hp"] < FULL_HP)
    assert fired is not None and fired["t"] <= deadline, (
        "R-087-09: E1 (%d) was not fired on by tick %d (t_b %d + 20 + 4)" % (E1_ID, deadline, trace[tb]["t"]))


@pytest.mark.xfail(strict=True, reason="VG-T-R087-WIRE: R-087-09 not built, FINDING-r087-09-not-built")
@pytest.mark.parametrize("mode", ["idle", "am"])
def test_R_087_09_unit_steers_to_a_clear_line_and_fires_at_the_first_target(mode):
    """R-087-09, gap reachable: the line to E0 is blocked but a clear-line spot is 22 wu away (11 ticks, under the
    20 of the rule). The unit steers there and fires at E0, the first target, no later than 20 ticks after t_b, and
    does not fire at E1. Red today: nothing steers, the unit holds E0 behind the disc (the rule is not built if this
    is red, and VG-T-R087-WIRE is the build)."""
    facts, trace = _assert_premise("gap", mode)
    tb = facts["tb"]
    deadline = trace[tb]["t"] + DEADLINE_TICKS
    fired = _first(trace[tb:], lambda r: r["e0hp"] < FULL_HP)
    assert fired is not None and fired["t"] <= deadline, (
        "R-087-09: E0 (%d) was not fired on by tick %d (t_b %d + 20 + 4); U at %.1f, %.1f, a clear-line spot %.0f wu away"
        % (E0_ID, deadline, trace[tb]["t"], trace[tb + DEADLINE_TICKS]["u"][0], trace[tb + DEADLINE_TICKS]["u"][1], facts["gap"]))
    assert all(r["e1hp"] == FULL_HP for r in trace[tb:tb + DEADLINE_TICKS + 1]), "R-087-09: fired at E1 instead of steering"
