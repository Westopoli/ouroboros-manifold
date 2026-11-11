# Rule pins: R-096-08, R-208-01, R-093-02
"""Engine rule fixes 2026-11-08, F6, a whole fight: the guards of L-0061 step toward a seen enemy, fire, and keep their post's radius.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F6" ("L-0061's four idle guard Vanguards with a seen enemy 301 to 357 wu away step and
fire"; "a guard never ends a tick more than 200 wu from its post (R-096-08 leash check, the sweep's I26 stays clean)"). The single geometry is
tests/csim/test_E13_R096_08_guard_steps_and_returns.py.

Rule words (docs/bible/epics/E-13-movement-and-command.md, as rewritten 2026-11-08):
  R-096-08  "... each unit takes its position as its post and engages any target its side can see (E-12 R-093-02), stepping toward it no farther than
            `GUARD_RADIUS` = 200 wu from the post (...), firing whenever the target is in range, returning to the post when the target dies or when
            engaging it would take the guard past the radius; it never crosses the radius and never marches; the walk is toward any target its side
            can see within vision, on its own layer or another, as far as the radius allows, and it fires when reach and range allow (...)"
  R-208-01  "... the units hold the post and engage what their side can see (E-12 R-093-02) within `GUARD_RADIUS` of it, returning to the post when the
            target dies or leaves the radius, never chasing past it (R-096-08)."

Configuration: `run.fight(L-0061, seed 1, sight "on", 100 simulated seconds)`: the lab's stage 4 rule set, walking units, the hill, targeting by sight on.
L-0061 is `orders = "hold:A"`: side A (24 units, layer 1, on the hill) is ordered to guard, side B attack-moves to side A's centroid. Nothing is switched off.

Premises dumped from the unfixed tree (2026-11-11; this file asserts them in the control):
  side A is 12 Vanguards and 12 Wardens on layer 1; side B on layer 0. Every side-A unit has a maximum displacement of 0.0 wu over the whole fight
  (the guard never steps). Each of the 12 Vanguards sees (the side sees) a layer-0 enemy 353 to 357 wu away on some tick between 55 and 85, and fires for
  the first time on tick 103 or 105. The spec's "four" is the count of an earlier reading; the dump is 12 and the test takes every one it finds.

THE CHECK THIS FILE PINS (the test writer's design, as narrow as the spec allows; the implementer builds to it, the chat may rename). The F0 checker
(scripts/skilllab/invariants.py) has no guard-leash check. A new one is named `R-096-08`:
    RULES gains "R-096-08"
    Rules(..., guards=None)      {unit id: (post x, post y)}; a unit with no entry is not a guard
    R-096-08   a living guard ends a frame more than 200 wu (GUARD_RADIUS) + 1 wu (DRAFT-guard-leash-slack) from its post
    Monitor    fills `guards` from the units the lab ordered to guard (run.fight's `engine.order_guard`), post = where each stood when ordered
Detector bounds (not rules; Westley's to change): LEASH_SLACK 1 wu, STEP_MIN_LAB 10 wu and STEP_WINDOW 40 ticks (the enemy walks toward the hill
too, so the guard may need to step only a short way), SEEN 301..357 wu (the spec's figures).
"""
import ctypes
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
from scripts.skilllab import invariants  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402

NAME = "L-0061"
GUARD_RADIUS = 200.0                # R-096-08 (DRAFT-guard-radius, Westley's)
LEASH_SLACK = 1.0                   # DRAFT-guard-leash-slack, detector bound
SEEN_MIN, SEEN_MAX = 301.0, 357.0   # spec F6
STEP_MIN_LAB = 10.0                 # detector bound
STEP_WINDOW = 40                    # detector bound
VANGUARD = 2                        # the roster's type id (oracle.typ)
PLANT_STEP = 5


def played():
    return oracle.played(NAME, "on")


def guards(rec):
    """The side-A units (the layout's orders hold:A guard them all) and where each stood before the first step: its post."""
    posts = {u: (rec.ticks[0]["pre"][u]["x"], rec.ticks[0]["pre"][u]["y"]) for u in rec.ids if rec.side[u] == 0}
    return posts


def first_sights(rec):
    """{guard Vanguard: (tick, enemy, distance)}: the first tick (state before the step) at which the guard's side sees a living enemy SEEN_MIN..SEEN_MAX wu away."""
    out = {}
    for tk in rec.ticks:
        for u in rec.ids:
            if rec.side[u] != 0 or rec.typ[u] != VANGUARD or u in out or not tk["pre"][u]["alive"]:
                continue
            p = tk["pre"][u]
            for e in rec.ids:
                if rec.side[e] == 0 or not tk["pre"][e]["alive"] or not tk["vis_pre"].get((0, e)):
                    continue
                d = math.hypot(tk["pre"][e]["x"] - p["x"], tk["pre"][e]["y"] - p["y"])
                if SEEN_MIN <= d <= SEEN_MAX:
                    out[u] = (tk["n"], e, d)
                    break
    return out


def first_shot(rec, u):
    return next((tk["n"] for tk in rec.ticks if any(a == u for a, _ in tk["fires"])), None)


def _wander(rec, posts):
    """[(tick, unit, distance from the post)] for every living unit of `posts` that ends a tick farther than GUARD_RADIUS + LEASH_SLACK from its post."""
    return [(tk["n"], u, round(math.hypot(tk["post"][u]["x"] - px, tk["post"][u]["y"] - py), 1)) for tk in rec.ticks for u, (px, py) in posts.items()
            if tk["post"][u]["alive"] and math.hypot(tk["post"][u]["x"] - px, tk["post"][u]["y"] - py) > GUARD_RADIUS + LEASH_SLACK]


# ------------------------------------------------------------------ controls: green today

def test_R_096_08_control_the_L0061_guards_see_an_enemy_beyond_range_and_the_scene_is_as_dumped():
    """Control (green today): L-0061 sight on, 2000 ticks; side A is 12 Vanguards and 12 Wardens on layer 1 ordered to guard; at least four guard Vanguards
    see an enemy 301..357 wu away before they first shoot; every guard fires in the end. Proves the recorder, the sight reading and the scene."""
    rec = played()
    posts = guards(rec)
    kinds = sorted(rec.typ[u] for u in posts)
    seen = first_sights(rec)
    shots = {u: first_shot(rec, u) for u in seen}
    print("premises: %d side-A units (types %s), %d guard Vanguards see an enemy %g..%g wu away, first sights %s, first shots %s" % (
        len(posts), sorted(set(kinds)), len(seen), SEEN_MIN, SEEN_MAX, {u: s[0] for u, s in seen.items()}, shots))
    assert len(rec.ticks) > 1000, "scene broken: the fight is %d ticks long" % len(rec.ticks)
    assert len(posts) == 24 and {rec.typ[u] for u in posts} == {VANGUARD, 3}, "scene broken: side A is not 12 Vanguards and 12 Wardens"
    assert all(rec.ticks[0]["pre"][u]["layer"] == 1 for u in posts), "scene broken: a guard is not on the hill (layer 1)"
    assert len(seen) >= 4, "scene broken: only %d guard Vanguards ever see an enemy %g..%g wu away" % (len(seen), SEEN_MIN, SEEN_MAX)
    assert all(s is not None and s > seen[u][0] for u, s in shots.items()), "scene broken: a guard Vanguard never fired after sighting the enemy"


def test_R_096_08_control_unguarded_units_of_the_same_layout_do_leave_a_radius_of_200_wu():
    """Control for the leash test (green today): the same layout with both sides attack-moving to one point (nobody guards): side A units end ticks
    farther than 200 wu from where they started. The detector `_wander` can read a breach in a real fight."""
    layout = dict(oracle.catalogue(NAME), orders="both_same_point")
    rec = oracle.fight_layout(layout, "on", oracle.FIGHT_SECONDS)
    posts = guards(rec)
    gone = _wander(rec, posts)
    assert len({u for _, u, _ in gone}) >= 4, "scene broken: only %d unguarded units ever went beyond %g wu" % (len({u for _, u, _ in gone}), GUARD_RADIUS)


def test_R_096_08_the_leash_holds_for_every_guard_on_every_tick():
    """R-096-08: 'it never crosses the radius and never marches', whole fight, every tick, all 24 guards of L-0061, sight on, the hill: no guard ends a
    tick more than 200 wu (+ the 1 wu detector slack) from where it stood when ordered. Green today (the guards hold still); it is the never rule and
    must stay green when the guards step. It goes red against a guard that steps without the clamp (the break the report names)."""
    rec = played()
    bad = _wander(rec, guards(rec))
    assert not bad, "%d unit-ticks beyond %g wu from the post, %d units, first %s" % (len(bad), GUARD_RADIUS, len({u for _, u, _ in bad}), bad[:3])


# ------------------------------------------------------------------ red today: the guards step and fire

def test_R_096_08_the_guard_vanguards_with_a_seen_enemy_beyond_range_step_toward_it():
    """R-096-08 / spec F6: each guard Vanguard that sees an enemy 301..357 wu away (on the layer below, within vision) steps toward it: within
    STEP_WINDOW ticks of the first sighting it stands at least STEP_MIN_LAB wu from where it stood at the sighting. Whole fight, sight on, the hill.
    Red today: all 12 hold the post for the whole fight (0.0 wu)."""
    rec = played()
    seen = first_sights(rec)
    assert seen, "scene broken: no guard Vanguard sees an enemy %g..%g wu away" % (SEEN_MIN, SEEN_MAX)
    still = []
    for u, (n, e, d) in seen.items():
        at = rec.ticks[n - 1]["pre"][u]
        best = max(math.hypot(tk["post"][u]["x"] - at["x"], tk["post"][u]["y"] - at["y"]) for tk in rec.ticks[n - 1:n - 1 + STEP_WINDOW])
        if best < STEP_MIN_LAB:
            still.append((u, n, e, round(d, 1), round(best, 1)))
    assert not still, "%d of %d guard Vanguards did not step within %d ticks of seeing an enemy beyond range (unit, tick, enemy, wu, moved): %s" % (
        len(still), len(seen), STEP_WINDOW, still[:3])


def test_R_096_08_the_guard_vanguards_fire_from_a_spot_they_stepped_to():
    """R-096-08: 'it fires when reach and range allow'. Each guard Vanguard of the control fires at some tick, and at its first shot it stands at least
    STEP_MIN_LAB wu from its post (it stepped to a spot with the enemy in range), and no farther than 200 wu. Red today: every first shot is taken from the
    post itself."""
    rec = played()
    posts = guards(rec)
    seen = first_sights(rec)
    assert seen, "scene broken: no guard Vanguard sees an enemy %g..%g wu away" % (SEEN_MIN, SEEN_MAX)
    from_post = []
    for u in seen:
        n = first_shot(rec, u)
        assert n is not None, "guard %d never fired" % u
        p = rec.ticks[n - 1]["post"][u]
        away = math.hypot(p["x"] - posts[u][0], p["y"] - posts[u][1])
        if away < STEP_MIN_LAB:
            from_post.append((u, n, round(away, 1)))
        assert away <= GUARD_RADIUS + LEASH_SLACK, "guard %d fired at tick %d from %.1f wu beyond its post" % (u, n, away)
    assert not from_post, "%d of %d guard Vanguards took their first shot from their post (unit, tick, wu from post): %s" % (len(from_post), len(seen), from_post[:3])


# ------------------------------------------------------------------ red today: the checker has the guard-leash check

def test_R_096_08_the_checker_has_a_guard_leash_check_that_fires_on_a_planted_trace_and_not_on_a_clean_one():
    """R-096-08 in scripts/skilllab/invariants.py (the pinned design in the module docstring): `RULES` names it; a guard 260 wu from its post is a
    violation of it at that frame; the same guard at 150 wu is not (the clean twin). Red today: the checker has no `R-096-08`."""
    assert "R-096-08" in invariants.RULES, "scripts/skilllab/invariants.py has no R-096-08 check (RULES = %s)" % (invariants.RULES,)

    def frames(dist):
        row = lambda x: {"x": x, "y": 1000.0, "layer": 1, "alive": True, "hp": 100.0, "side": 0, "target": 0}
        return [{"tick": n, "units": {1: row(1000.0 + (dist if n >= 2 else 0.0))}, "fires": []} for n in range(4)]

    rules = invariants.Rules(4000.0, 4000.0, guards={1: (1000.0, 1000.0)})
    bad = invariants.check(frames(260.0), rules, only=["R-096-08"])
    assert [(v["rule"], v["tick"], v["unit"]) for v in bad.violations][:1] == [("R-096-08", 2, 1)], bad.violations
    clean = invariants.check(frames(150.0), rules, only=["R-096-08"])
    assert not clean.violations, clean.violations
    unguarded = invariants.check(frames(260.0), invariants.Rules(4000.0, 4000.0), only=["R-096-08"])
    assert not unguarded.violations, "a unit with no guard entry was judged: %s" % unguarded.violations


def test_R_096_08_the_online_monitor_flags_a_planted_guard_breach_on_L0061(monkeypatch):
    """R-096-08 wiring: after step 5 of the L-0061 fight a guard (side A's first unit, ordered to guard by the lab) is set down 400 wu from its post; the
    monitor `run.fight` uses reports R-096-08 for that unit at its tick 5. Proves the lab's guard orders reach the checker. Red today: no such rule."""
    real, seen, caught = Engine.step, {}, []

    def step(self, w):
        real(self, w)
        step.n += 1
        if step.n == PLANT_STEP:
            lib = self._lib
            lib.om_unit_set_pos.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
            seen["unit"] = sorted(self._own[(w.value, 0)])[0]
            x, y = self.unit_pos(w, seen["unit"])
            lib.om_unit_set_pos(w, seen["unit"], x - 400.0, y)
    step.n = 0

    class Capture(invariants.Monitor):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            caught.append(self)

    monkeypatch.setattr(Engine, "step", step)
    monkeypatch.setattr(invariants, "Monitor", Capture)
    run.fight(oracle.catalogue(NAME), 1, "on", 2, 100000)
    assert len(caught) == 1
    hit = [v for v in caught[0].violations if v["rule"] == "R-096-08"]
    assert hit and (hit[0]["tick"], hit[0]["unit"]) == (PLANT_STEP, seen["unit"]), "the monitor did not flag the planted breach: R-096-08 violations %s, all rules %s" % (
        hit[:2], sorted({v["rule"] for v in caught[0].violations}))
