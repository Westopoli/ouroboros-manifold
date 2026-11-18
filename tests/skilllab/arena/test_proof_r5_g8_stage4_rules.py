# Rule pins: R-093-02, R-008-04, R-084-04, R-083-03, R-096-08
"""Round 5, G8: the proof tests of five stage 4 rules, whole fights in the lab configuration (docs/method/requirements.md, Proof, seven qualifications; audit docs/reports/2026-11-17-requirement-audit.md).

Each rule has one named function that quotes the rule as it reads on this branch, asserts its Then on every tick of real fights, and one filled control that plants the violation in the same
fight and shows the same assertion catch it. The judge is `engine_rules_oracle` (a recorder of `Engine.step`, from engine state: not the checker `scripts/skilllab/invariants.py`, so the
checker cannot hide a bug). Nothing here replaces a per-tick assertion with a final-state one; the older tests of these rules (test_invariants_round2_wiring.py, test_engine_rules_f2/f4/f6) stay as they are.

Configuration (scripts/skilllab/arena/run.py `fight`, read 2026-11-17): `run.fight(layout, seed 1, sight "on", ..)` is the stage 4 rule set: OM_TP_TARGET_BY_SIGHT at its default 1, abilities off, ground era
(`set_era_kind 1`), every role walking, the preset's canvas, features laid exact (planar boxes on the 100 wu grid, the `vantage` as terrain), reach 0 up 1 down, orders `both_same_point` attack-move or
`hold:A` (the holder on `order_guard`). Sight "control" is the same with OM_TP_TARGET_BY_SIGHT 0: the engine break the controls of R-093-02 and R-008-04 use.

DRAFT numbers (Westley's): MIN_JUDGED 20 and MIN_PICKS 40 (a control that the fight exercised the rule, not that it was clean because nothing happened), GUARD_SLACK 1 wu (DRAFT-guard-leash-slack, as
test_engine_rules_f6_guard.py), HEAL_TOL 1e-6, DAMAGE_TOL 1e-6 (arithmetic slack, not rules).
"""
import collections
import ctypes
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402

SECONDS = 100
MIN_JUDGED = 20          # DRAFT-g8-min-judged
MIN_PICKS = 40           # DRAFT-g8-min-picks (L-0039 seed 1 has 49 in 100 s)
GUARD_RADIUS = 200.0     # R-096-08 (DRAFT-guard-radius)
GUARD_SLACK = 1.0        # DRAFT-guard-leash-slack
WARDEN, AURA_R = 3, 300.0
HEAL = oracle.HEAL_ONE
TOL = 1e-6


def _plant_run(layout_name, sight, seconds, plant):
    """A whole fight, recorded, in which `plant(engine, world, n)` runs after step n of the engine (n from 1): the plant is part of that step as the recorder sees it."""
    real, count = Engine.step, [0]

    def step(self, w):
        real(self, w)
        count[0] += 1
        plant(self, w, count[0])
    Engine.step = step
    try:
        return oracle.fight_layout(oracle.catalogue(layout_name), sight, seconds)
    finally:
        Engine.step = real


def _lib(eng):
    eng._lib.om_unit_set_pos.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
    eng._lib.om_unit_set_hp.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double]
    return eng._lib


# ------------------------------------------------------------------ R-093-02 and R-008-04: sight

def unseen_acts(rec):
    """[(tick, unit, what, target)]: a shot at, a new pick of, or a held target that the unit's side did not see in the state before the step (om_player_can_see, per side)."""
    out = []
    for tk in rec.ticks:
        for a, b in tk["fires"]:
            if not tk["vis_pre"].get((rec.side[a], b)):
                out.append((tk["n"], a, "fire", b))
        for u in rec.ids:
            p0, p1 = tk["pre"][u], tk["post"][u]
            t = p1["tgt"] if p1["alive"] else 0
            if t and tk["pre"][t]["alive"] and rec.side[t] != rec.side[u] and not tk["vis_pre"].get((rec.side[u], t)):
                out.append((tk["n"], u, "hold" if p0["tgt"] == t else "pick", t))
    return out


def test_R_093_02_every_pick_every_held_target_and_every_shot_is_in_the_sides_visible_set():
    """R-093-02 "Given any unit of any side, When it acquires, pursues or fires at a target, Then the target is in its side's visible set: the union of what that side's living units see (R-089-01, E-01 S-005) and what its
    pings reveal (E-01 S-162); the rule is the same for the player's units and the enemy's (Westley, 2026-10-02). A unit whose sensor is shorter than its range (Bombard, Bastion: sensor 300) fires beyond its sensor
    only at what another friendly unit or a ping sees." Lab configuration: L-0039 (boxes) and L-0061 (hill), seed 1, sight on, 100 s, every tick. Then asserted with no tick of lag: no shot, no new pick and no held target
    that its side did not see before the step. Premises: more than MIN_PICKS picks, and in L-0039 shots beyond the shooter's own sensor (the second sentence of the rule). Control: test_R_093_02_control_*."""
    for name in ("L-0039", "L-0061"):
        rec = oracle.played(name, "on", SECONDS)
        bad = unseen_acts(rec)
        assert not bad, "%s: %d unit-ticks at a target the side did not see, first %s" % (name, len(bad), bad[:3])
        picks = sum(1 for tk in rec.ticks for u in rec.ids if tk["pre"][u]["alive"] and tk["post"][u]["tgt"] and tk["post"][u]["tgt"] != tk["pre"][u]["tgt"])
        assert picks > MIN_PICKS, "%s: only %d picks, the run does not exercise the rule" % (name, picks)
    rec = oracle.played("L-0039", "on", SECONDS)
    far = sum(1 for tk in rec.ticks for a, b in tk["fires"]
              if math.hypot(tk["pre"][a]["x"] - tk["pre"][b]["x"], tk["pre"][a]["y"] - tk["pre"][b]["y"]) > rec.stats[rec.typ[a]]["sensor_radius"])
    assert far > MIN_JUDGED, "no shot beyond the shooter's own sensor: the 'seen by another friendly unit' clause is not exercised"


def test_R_093_02_control_with_targeting_by_sight_off_the_same_assertion_finds_unseen_targets():
    """Control (filled) for R-093-02, the engine break: L-0039 seed 1 with the engine's switch OM_TP_TARGET_BY_SIGHT 0 (sight "control": stage 4's rule set with targeting by sight off) acts on targets its side did not
    see: the assertion's predicate `unseen_acts` finds picks, held targets and shots (10, 648 and 5 of them when measured 2026-11-17)."""
    bad = unseen_acts(oracle.played("L-0039", "control", SECONDS))
    kinds = collections.Counter(k for _, _, k, _ in bad)
    assert kinds["fire"] and kinds["pick"] and kinds["hold"], dict(kinds)


def test_R_008_04_no_unit_fires_at_a_target_its_side_cannot_see_on_its_own_layer_or_another():
    """R-008-04 "Given an attacker whose side cannot see a target (S-005, E-12 R-093-02), When it would attack that target, Then it does not: a unit never fires at a target its side cannot see, on its own layer or another;
    a target seen by any friendly unit or revealed by a ping may be fired at." Lab configuration: L-0039 (own-layer shots) and L-0061 (own-layer and downhill shots, reach 0 up 1 down), seed 1, sight on, 100 s,
    every shot of every tick: its target is in the shooter's side's visible set before the step, for shots on the shooter's own layer and for shots across layers separately. Premises asserted: both kinds of shot occur,
    and some shots are at a target the shooter itself is too far from to sense (seen by a friend). Control: test_R_008_04_control_*."""
    cross = same = 0
    for name in ("L-0039", "L-0061"):
        rec = oracle.played(name, "on", SECONDS)
        for tk in rec.ticks:
            for a, b in tk["fires"]:
                kind = "cross" if tk["pre"][a]["layer"] != tk["pre"][b]["layer"] else "same"
                assert tk["vis_pre"].get((rec.side[a], b)), "%s tick %d: unit %d fired at %d on %s layer, which its side did not see" % (name, tk["n"], a, b, kind)
                cross, same = cross + (kind == "cross"), same + (kind == "same")
    assert cross > 0 and same > 0, "the fights have %d cross-layer and %d own-layer shots: the rule's two cases are not both exercised" % (cross, same)
    rec = oracle.played("L-0039", "on", SECONDS)
    assert sum(1 for tk in rec.ticks for a, b in tk["fires"]
               if math.hypot(tk["pre"][a]["x"] - tk["pre"][b]["x"], tk["pre"][a]["y"] - tk["pre"][b]["y"]) > rec.stats[rec.typ[a]]["sensor_radius"]) > MIN_JUDGED


def test_R_008_04_control_with_targeting_by_sight_off_units_fire_at_unseen_targets():
    """Control (filled) for R-008-04, the engine break: L-0039 seed 1 sight "control" (OM_TP_TARGET_BY_SIGHT 0): the same per-shot test finds shots at a target the shooter's side did not see (5 when measured 2026-11-17)."""
    rec = oracle.played("L-0039", "control", SECONDS)
    assert sum(1 for tk in rec.ticks for a, b in tk["fires"] if not tk["vis_pre"].get((rec.side[a], b))) > 0


# ------------------------------------------------------------------ R-084-04: backswing

def judged_backswing_ticks(rec):
    """Unit-ticks inside a backswing window (1 to 9 ticks after a shot) that the predicate can judge: alive, not firing, no unit within PUSH_RADIUS (a push is excused)."""
    n, last = 0, {}
    for tk in rec.ticks:
        fired = {a for a, _ in tk["fires"]}
        for u in rec.ids:
            lf = last.get(u)
            if tk["pre"][u]["alive"] and u not in fired and lf is not None and 1 <= tk["n"] - lf <= oracle.BACKSWING_TICKS - 1 and not oracle._pushed(rec, tk, u):
                n += 1
        for a in fired:
            last[a] = tk["n"]
    return n


def test_R_084_04_a_unit_that_fired_does_not_move_under_its_own_power_for_the_next_nine_ticks():
    """R-084-04 "Given a unit fires, When the attack lands, Then the unit pauses movement for 0.5 s (backswing)." Lab configuration: L-0039 and L-0079 (boxes, Wardens, Bombards), seed 1, sight on, 100 s,
    walkers, attack-moved as one group per side. Then, every tick: no unit moves more than 0.5 wu under its own power (a neighbour within 40 wu excuses a push, DRAFT-inv-push-radius) in ticks 1 to 9 after a shot
    (the shot's own tick is the tick it lands, 0.5 s = 10 ticks). Premise: more than MIN_JUDGED unit-ticks inside a window that the predicate can judge (a fight whose every window is excused proves nothing)."""
    for name in ("L-0039", "L-0079"):
        rec = oracle.played(name, "on", SECONDS)
        bad = oracle.moved_in_backswing(rec)
        assert not bad, "%s: %d unit-ticks of own-power movement in the pause, first %s" % (name, len(bad), bad[:3])
        assert judged_backswing_ticks(rec) > MIN_JUDGED, "%s: %d judgeable pause unit-ticks" % (name, judged_backswing_ticks(rec))


def test_R_084_04_control_a_unit_set_down_3_wu_forward_three_ticks_after_its_shot_is_caught():
    """Control (filled) for R-084-04: in the real L-0039 fight the engine world is changed (om_unit_set_pos, +3 wu in x) for one shooter that no neighbour crowds, three ticks after its shot (the same
    deterministic fight, so the shot and the tick are those of the clean run); the assertion's predicate reports that unit at that tick."""
    base = oracle.played("L-0039", "on", SECONDS)
    pick = None
    for tk in base.ticks:
        for a, _ in tk["fires"]:
            nxt = base.ticks[tk["n"] + 2] if tk["n"] + 3 <= len(base.ticks) else None
            if nxt and nxt["pre"][a]["alive"] and nxt["post"][a]["alive"] and not oracle._pushed(base, nxt, a) and oracle._disp(nxt["pre"][a], nxt["post"][a]) <= oracle.OWN_MOVE:
                pick = (tk["n"], a)
                break
        if pick:
            break
    assert pick, "scene broken: no shooter standing 3 ticks after its shot with no neighbour"
    n, u = pick

    def plant(eng, w, k):
        if k == n + 3:
            x, y = eng.unit_pos(w, u)
            _lib(eng).om_unit_set_pos(w, u, x + 3.0, y)
    rec = _plant_run("L-0039", "on", (n + 4) // 20 + 1, plant)
    assert [(t, a) for t, a, _ in oracle.moved_in_backswing(rec)][:1] == [(n + 3, u)], oracle.moved_in_backswing(rec)[:3]


# ------------------------------------------------------------------ R-083-03: Wardens

def warden_cover(rec, tk, u):
    """Living friendly Wardens other than `u` within 300 wu of `u` (flat distance, state before the step)."""
    p = tk["pre"][u]
    return [w for w in rec.ids if w != u and rec.typ[w] == WARDEN and rec.side[w] == rec.side[u] and tk["pre"][w]["alive"] and math.hypot(tk["pre"][w]["x"] - p["x"], tk["pre"][w]["y"] - p["y"]) <= AURA_R]


def _single_hits(rec):
    """[(tick, attacker, victim, covering wardens, hp lost)] for non-Warden victims hit once in a tick with no area attack fired in it, alive after."""
    out = []
    for tk in rec.ticks:
        if any(rec.stats[rec.typ[a]]["aoe_radius"] > 0 for a, _ in tk["fires"]):
            continue
        by = collections.Counter(b for _, b in tk["fires"])
        for a, b in tk["fires"]:
            p0, p1 = tk["pre"][b], tk["post"][b]
            if by[b] == 1 and p0["alive"] and p1["alive"] and rec.typ[b] != WARDEN:   # a Warden is its own aura's unit (it regains 0.075 beside no other Warden): its loss is read through its heal, not here
                out.append((tk["n"], a, b, len(warden_cover(rec, tk, b)), p0["hp"] - p1["hp"]))
    return out


def warden_breaks(recs, reference=None):
    """[(fight, tick, unit, what)]: a unit that nothing hurt regains other than 0.075 hp (capped at max hp) with a Warden within 300 wu, or other than 0 with none (a Warden itself: never more than 0.075);
    a unit hit once loses other than 0.9 of what the same attacker type takes from the same victim type with no Warden near (read from the same fights), however many Wardens are near."""
    out, free = [], dict(reference or {})   # `reference`: the {(attacker type, victim type): loss with no Warden near} of other fights
    for name, rec in recs.items():
        for _, a, b, nw, lost in _single_hits(rec):
            if nw == 0:
                free[(rec.typ[a], rec.typ[b])] = lost
    for name, rec in recs.items():
        for tk in rec.ticks:
            hit = {b for _, b in tk["fires"]}
            for u in rec.ids:
                p0, p1 = tk["pre"][u], tk["post"][u]
                if not (p0["alive"] and p1["alive"]) or u in hit or p1["hp"] < p0["hp"] - TOL:
                    continue
                gain, room = p1["hp"] - p0["hp"], rec.stats[rec.typ[u]]["max_hp"] - p0["hp"]
                if rec.typ[u] == WARDEN:
                    ok = gain <= HEAL + TOL
                else:
                    ok = abs(gain - (min(HEAL, room) if warden_cover(rec, tk, u) else 0.0)) <= TOL
                if not ok:
                    out.append((name, tk["n"], u, "regained %.4f with %d Wardens near" % (gain, len(warden_cover(rec, tk, u)))))
        for n, a, b, nw, lost in _single_hits(rec):
            ref = free.get((rec.typ[a], rec.typ[b]))
            if nw and ref is not None and min(abs(lost - 0.9 * ref), abs(lost + HEAL - 0.9 * ref)) > TOL:
                out.append((name, n, b, "lost %.4f of %.4f with %d Wardens near" % (lost, ref, nw)))
    return out


def _warden_fights():
    return {n: oracle.played(n, "on", SECONDS) for n in ("L-0039", "L-0040", "L-0079")}


def test_R_083_03_a_unit_near_wardens_takes_a_tenth_less_and_regains_0_075_once_however_many_are_near():
    """R-083-03 "Given a Warden, When any friendly unit is within 300 wu, Then that unit takes 10 percent less damage and regains 0.075 HP per tick (the Warden's passive aura); a second Warden in range adds nothing: the aura
    does not stack, so a player who spreads Wardens out covers more of the army; the player sees each Warden's 300 wu radius as a circle on the field (Westley, 2026-10-20: "they do not stack, but they have a visible
    circular radius of influence and if a player spreads them out better they'll get better healing coverage over more of their army")." (The circle is the client's and is not proved here.) Lab configuration: L-0039,
    L-0040, L-0079, seed 1, sight on, 100 s. Then, every tick: a non-Warden unit nothing hurt regains exactly 0.075 hp (to its max hp) with a friendly Warden within 300 wu and exactly 0 with none, a Warden never more
    than 0.075; a unit hit once, with no area attack in the tick, loses exactly 0.9 of what the same attacker type takes from the same victim type with no Warden near, with one, two or three Wardens near.
    Premises: more than MIN_JUDGED covered hits with two or more Wardens near, and more than MIN_JUDGED with one."""
    recs = _warden_fights()
    bad = warden_breaks(recs)
    assert not bad, "%d breaks, first %s" % (len(bad), bad[:3])
    hits = [h for rec in recs.values() for h in _single_hits(rec)]
    assert sum(1 for h in hits if h[3] >= 2) > MIN_JUDGED and sum(1 for h in hits if h[3] == 1) > MIN_JUDGED, collections.Counter(min(h[3], 3) for h in hits)


def test_R_083_03_control_a_second_warden_that_heals_or_a_reduction_that_is_too_small_is_caught():
    """Control (filled) for R-083-03: in the real L-0039 fight the engine world is changed (om_unit_set_hp) after one tick: (a) +0.075 on a unit a Warden is healing (a second heal), caught as a regain of 0.15;
    (b) +10 percent of the reference damage given back to a unit a Warden covers that was hit once (a reduction of 0.8), caught as a loss of 0.8 of the reference. Each plant is its own run (the changed hp changes
    what the fight does afterwards). The same predicate `warden_breaks`."""
    base = {"L-0039": oracle.played("L-0039", "on", SECONDS)}
    fights = _warden_fights()
    free = {}
    for rec in fights.values():
        for _, a, b, nw, lost in _single_hits(rec):
            if nw == 0:
                free[(rec.typ[a], rec.typ[b])] = lost
    rec0 = base["L-0039"]
    heal = next((tk["n"], u) for tk in rec0.ticks for u in rec0.ids if rec0.typ[u] != WARDEN and tk["pre"][u]["alive"] and tk["post"][u]["alive"]
                and abs(tk["post"][u]["hp"] - tk["pre"][u]["hp"] - HEAL) < TOL and u not in {b for _, b in tk["fires"]})
    cut = next((n, a, b, lost, free[(rec0.typ[a], rec0.typ[b])]) for n, a, b, nw, lost in _single_hits(rec0) if nw >= 1 and (rec0.typ[a], rec0.typ[b]) in free)

    def plant_heal(eng, w, k):
        if k == heal[0]:
            _lib(eng).om_unit_set_hp(w, heal[1], eng.unit_hp(w, heal[1]) + HEAL)

    def plant_cut(eng, w, k):
        if k == cut[0]:
            _lib(eng).om_unit_set_hp(w, cut[2], eng.unit_hp(w, cut[2]) + 0.1 * cut[4])
    others = {k: v for k, v in fights.items() if k != "L-0039"}
    got_heal = {(t, u) for _, t, u, _ in warden_breaks({"L-0039": _plant_run("L-0039", "on", heal[0] // 20 + 1, plant_heal), **others}, free)}
    got_cut = {(t, u) for _, t, u, _ in warden_breaks({"L-0039": _plant_run("L-0039", "on", cut[0] // 20 + 1, plant_cut), **others}, free)}
    assert (heal[0], heal[1]) in got_heal, (heal, sorted(got_heal)[:4])
    assert (cut[0], cut[2]) in got_cut, (cut, sorted(got_cut)[:4])


# ------------------------------------------------------------------ R-096-08: guard

def guard_breaks(rec, posts):
    """[(tick, unit, what)] over every tick: a guard ends a tick more than GUARD_RADIUS + GUARD_SLACK wu from its post; one with no target, standing on its post, moves under its own power ("never marches");
    one with no target off its post moves away from it (returns); a pick of an enemy beyond its notice distance that did not hit it (acquires as every unit does)."""
    out = []
    for tk in rec.ticks:
        for u, (px, py) in posts.items():
            p0, p1 = tk["pre"][u], tk["post"][u]
            if not (p0["alive"] and p1["alive"]):
                continue
            d0, d1 = math.hypot(p0["x"] - px, p0["y"] - py), math.hypot(p1["x"] - px, p1["y"] - py)
            if d1 > GUARD_RADIUS + GUARD_SLACK:
                out.append((tk["n"], u, "ended %.1f wu from the post" % d1))
            own = oracle._disp(p0, p1) > oracle.OWN_MOVE and not oracle._pushed(rec, tk, u)
            if own and not p0["tgt"] and not p1["tgt"]:
                if d0 <= GUARD_SLACK:
                    out.append((tk["n"], u, "marched off its post with no target"))
                elif d1 > d0 + 0.05:
                    out.append((tk["n"], u, "moved away from its post with no target"))
    out += [(t, u, "picked %d beyond its notice distance (%s of %s)" % (e, d, lim)) for t, u, e, d, lim in oracle.picks_beyond_notice(rec) if u in posts]
    return sorted(out)


def _l61():
    rec = oracle.played("L-0061", "on", SECONDS)
    return rec, {u: (rec.ticks[0]["pre"][u]["x"], rec.ticks[0]["pre"][u]["y"]) for u in rec.ids if rec.side[u] == 0}


def test_R_096_08_a_guard_acquires_as_every_unit_does_never_crosses_the_radius_and_never_marches():
    """R-096-08 "Given a guard order, When issued to a selection, Then each unit takes its position as its post and acquires as every unit does, an enemy its side can see (E-12 R-093-02) within its notice distance (E-11 R-087-04), stepping toward it no farther than `GUARD_RADIUS` = 200 wu from the post (DRAFT-guard-radius, Westley's number to change; the radius bounds the guard's own walk, measured post to the guard's centre, ruled 2026-10-14 for E4), firing whenever the target is in range, returning to the post when the lock ends (E-11 R-087-03) or when engaging the target would take the guard past the radius; it never crosses the radius and never marches; the target may be on its own layer or another, where reach and range allow (Westley, 2026-11-08, on a cross-layer target: "only if the enemy unit is within vision"; 2026-11-17, Q-096-02: "the unit only steps out when the enemy unit enters it's firing radius, and it only runs after it for 200 leash"; before then a guard walked toward any target its side saw); a move, attack-move, attack-target or layer order ends the guard; return fire (R-087-06) is untouched. Ruled by Westley, 2026-10-13: a guard stance as a radius (option b of Q-096-01), "for the whole game, not just the simulator". A seen enemy the guard cannot engage even from the edge of its radius leaves it at its post; a collision push never carries a guard past the radius (DRAFT readings, DEC-engine-rules-round2-2026-11-11, Westley may veto)." Lab configuration: L-0061 (hold:A: the 24 units of side A, on the hill, are ordered to
    guard; side B attack-moves at them), seed 1, sight on, 100 s, every tick, the oracle's rows: no guard ends a tick beyond 200 wu (+1 slack) of its post, none with no target marches off its post or moves away from it, none picks
    an enemy beyond its notice distance that did not hit it. Premises: the orders are hold:A, 24 guards, more than MIN_PICKS guard picks. NOT proved here, named so the Proof line can say it: the step toward a target out of range and the
    return after a chase, which L-0061 does not exercise (the guards stay within 20 wu of their posts because the enemy walks to them): the scenarios are tests/csim/test_E13_R096_08_guard_steps_and_returns.py."""
    rec, posts = _l61()
    assert oracle.catalogue("L-0061")["orders"] == "hold:A" and len(posts) == 24
    bad = guard_breaks(rec, posts)
    assert not bad, "%d guard breaks, first %s" % (len(bad), bad[:3])
    picks = sum(1 for tk in rec.ticks for u in posts if tk["pre"][u]["alive"] and tk["post"][u]["tgt"] and tk["post"][u]["tgt"] != tk["pre"][u]["tgt"])
    assert picks > MIN_PICKS, picks


def test_R_096_08_control_a_guard_set_down_400_wu_from_its_post_or_marched_off_it_is_caught():
    """Control (filled) for R-096-08: in the real L-0061 fight the engine world is changed (om_unit_set_pos) after step 5: (a) one guard is set 400 wu from its post, caught as a unit ended beyond the radius; (b) after step 3
    another guard standing on its post with no target is set 12 wu along x (an own-power step the test cannot excuse: a unit set down in the open beyond 40 wu of any neighbour is the one the plant picks), caught as
    marching or leaving. The same predicate `guard_breaks`."""
    base, posts = _l61()
    first = sorted(posts)
    far = {u for u in first if all(math.hypot(base.ticks[2]["pre"][u]["x"] - base.ticks[2]["pre"][o]["x"], base.ticks[2]["pre"][u]["y"] - base.ticks[2]["pre"][o]["y"]) >= oracle.PUSH_RADIUS + 12
                                  for o in base.ids if o != u and base.ticks[2]["pre"][o]["alive"])}

    def plant(eng, w, k):
        if k == 3 and far:
            x, y = eng.unit_pos(w, sorted(far)[0])
            _lib(eng).om_unit_set_pos(w, sorted(far)[0], x + 12.0, y)
        if k == 5:
            x, y = eng.unit_pos(w, first[0])
            _lib(eng).om_unit_set_pos(w, first[0], x - 400.0, y)
    rec = _plant_run("L-0061", "on", 2, plant)
    got = guard_breaks(rec, posts)
    assert any(u == first[0] and "wu from the post" in what for _, u, what in got), got[:4]
