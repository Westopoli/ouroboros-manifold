"""One tactical fight of one setup, stepped tick by tick (spec AC 5-11; rev 2 spec 2026-10-14).
A fight ends by elimination only; reaching Setup.max_ticks is a cap, a lab defect to trace, never a result (Q-LAB-03)."""
import math
import random

from scripts.skilllab.contract import OPENING_WINDOW_TICKS, SHIFT_MAX, TICKS_PER_SECOND, FightResult
from scripts.skilllab.firing import count_able, count_weighted, states
from scripts.skilllab.formations import place
from scripts.skilllab.timeline import Timeline, first_anchors, validate

FIRST_CUSTOM_TYPE_ID = 100
SLOT_RADIUS = 440
WALKING_KIND = 1       # om_roster_set_movement_kind: 0 flying (the default), 1 walking


def _check_reach(setup):
    for name, entry in setup.unit_types.items():
        reach = entry.get("reach")
        if "reach" in entry and not (isinstance(reach, (tuple, list)) and len(reach) == 2):
            raise ValueError("unit type %r: reach must be (up, down), got %r" % (name, reach))


def _register_types(engine, w, setup):
    """Return {name: (type_id, attack_range)} for every unit name the groups use, ids from 100 in order of first use."""
    types, next_id = {}, FIRST_CUSTOM_TYPE_ID
    for g in setup.groups:
        name = g.unit
        if name in types:
            continue
        entry = setup.unit_types.get(name)
        if entry is None:
            tid = engine.type_id(name)
            types[name] = (tid, engine.type_stats(w, tid)["attack_range"])
            continue
        if "base" in entry:
            stats = dict(engine.type_stats(w, engine.type_id(entry["base"])))
            for op in ("scale", "set"):
                for stat, value in entry.get(op, {}).items():
                    if stat not in stats:
                        raise ValueError("unit type %r: base %r has no stat %r" % (name, entry["base"], stat))
                    stats[stat] = stats[stat] * value if op == "scale" else value
            stats["role"], stats["ability_id"] = entry["base"], 0
        else:
            stats = {k: v for k, v in entry.items() if k not in ("reach", "movement")}
        engine.register_unit_type(w, next_id, stats)
        if "reach" in entry:
            engine.set_reach(w, next_id, *entry["reach"])
        if entry.get("movement") == "walking":
            engine.set_movement_kind(w, next_id, WALKING_KIND)
        types[name] = (next_id, stats["attack_range"])
        next_id += 1
    return types


def _spawn_side(engine, w, setup, side, types, rng, ids_by_group, ranges):
    for gi, g in enumerate(setup.groups):
        if g.side != side:
            continue
        tid, reach = types[g.unit]
        ids = []
        for px, py in place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
            dx, dy = rng.uniform(-SHIFT_MAX, SHIFT_MAX), rng.uniform(-SHIFT_MAX, SHIFT_MAX)
            u = engine.spawn(w, tid, side, px + dx, py + dy, g.layer)
            if u == 0:
                raise RuntimeError("lab defect: spawn of %s at (%.0f, %.0f) layer %d returned unit id 0 (ground a walker cannot stand on); "
                                   "id 0 would be counted dead" % (g.unit, px + dx, py + dy, g.layer))
            ranges[u] = reach
            ids.append(u)
        ids_by_group[gi] = ids


def _centroid(points):
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


def _chunks(engine, w, ids):
    """Split ids into the fewest equal chunks along the wider axis so each stays within SLOT_RADIUS of its own centroid.

    The engine drops a group's slots to the click point past 450 wu from the centroid (R-095-03).
    """
    pos = {u: engine.unit_pos(w, u) for u in ids}
    cx, cy = _centroid(list(pos.values()))
    if all(math.hypot(x - cx, y - cy) <= SLOT_RADIUS for x, y in pos.values()):
        return [(ids, (0.0, 0.0))]
    axis = 0 if max(p[0] for p in pos.values()) - min(p[0] for p in pos.values()) >= \
        max(p[1] for p in pos.values()) - min(p[1] for p in pos.values()) else 1
    ordered = sorted(ids, key=lambda u: pos[u][axis])
    for k in range(2, len(ids) + 1):
        base, extra = divmod(len(ordered), k)
        chunks, at = [], 0
        for i in range(k):
            size = base + (1 if i < extra else 0)
            chunks.append(ordered[at:at + size])
            at += size
        centres = [_centroid([pos[u] for u in c]) for c in chunks]
        if all(math.hypot(pos[u][0] - ctr[0], pos[u][1] - ctr[1]) <= SLOT_RADIUS
               for c, ctr in zip(chunks, centres) for u in c):
            return [(c, (ctr[0] - cx, ctr[1] - cy)) for c, ctr in zip(chunks, centres)]
    return [([u], (pos[u][0] - cx, pos[u][1] - cy)) for u in ordered]


def _issue_orders(engine, w, setup, ids_by_group):
    first_anchor, goals = first_anchors(setup), {}
    for gi, g in enumerate(setup.groups):
        if g.order == "idle":
            continue
        if g.order == "guard":
            engine.order_guard(w, ids_by_group[gi])
            continue
        goal = g.goal if g.goal is not None else setup.point if setup.point is not None else first_anchor[1 - g.side]
        if g.order == "attack_move":
            issue = engine.order_attack_move
        elif g.order == "move":
            issue = engine.order_move
        elif g.order == "group_move":
            issue = engine.order_group_move
        else:
            raise ValueError("unknown order %r" % (g.order,))
        if g.order == "attack_move" and setup.orders_per_unit:
            for u in ids_by_group[gi]:
                issue(w, [u], goal[0], goal[1])
        else:
            for ids, (dx, dy) in _chunks(engine, w, ids_by_group[gi]):
                issue(w, ids, goal[0] + dx, goal[1] + dy)
        goals[gi] = goal
    return goals


def _check_target_policy(policy):
    if policy is None:
        return
    if not isinstance(policy, (tuple, list)) or len(policy) != 2 or any(p not in (None, 0, 1) or isinstance(p, bool) for p in policy):
        raise ValueError("target_policy must be None or a pair of None, 0 or 1, got %r" % (policy,))


def apply_target_policy(engine, w, setup):
    """Faction 0 reads OM_TP_TARGET_POLICY, faction 1 reads OM_TP_TARGET_POLICY_FACTION_1 (A196); None leaves a side unset."""
    for name, value in zip(("OM_TP_TARGET_POLICY", "OM_TP_TARGET_POLICY_FACTION_1"), setup.target_policy or (None, None)):
        if value is not None:
            engine.set_param(w, engine.param_id(name), float(value))


def _set_arc(engine, w, arc_deg):
    """OM_TP_FIRING_ARC_DEG exists from LAB-REV2-E0 on; a library without it keeps the 360 behaviour."""
    if arc_deg >= 360.0:
        return
    try:
        pid = engine.param_id("OM_TP_FIRING_ARC_DEG")
    except ValueError:
        return
    engine.set_param(w, pid, float(arc_deg))


def _apply_cone(engine, w, setup, types):
    for name, (rng, half_angle, share) in setup.cone.items():
        engine.set_cone(w, types[name][0], float(rng), float(half_angle), float(share))


def fight(setup, seed=0, swap=False, engine=None):
    heads = tuple(sum(g.count for g in setup.groups if g.side == s) for s in (0, 1))
    if min(heads) < 1:
        raise ValueError("each side needs at least one unit, got headcounts %r" % (heads,))
    if min(setup.max_ticks, setup.sample_every) < 1:
        raise ValueError("max_ticks and sample_every must each be at least 1")
    validate(setup)
    _check_reach(setup)
    _check_target_policy(setup.target_policy)
    if engine is None:
        from scripts.skilllab.engine import Engine
        engine = Engine()

    w = engine.new_world(seed)
    try:
        if not setup.abilities:
            engine.disable_abilities(w)
        for pid, value in [(engine.param_id(n), float(v)) for n, v in setup.settings.items()]:
            engine.set_param(w, pid, value)
        _set_arc(engine, w, setup.firing_arc_deg)
        apply_target_policy(engine, w, setup)
        if setup.terrain is not None:
            t = setup.terrain
            engine.set_canvas(w, t.canvas[0], t.canvas[1])
            if t.field_seed is not None:
                engine.terrain_generate(w, t.field_seed, t.canvas[0])
                engine.set_era_kind(w, 1)
            for b in t.blocks:
                engine.block_rect(w, b.x0, b.y0, b.x1, b.y1, b.layer_lo, b.layer_hi)
            for c in t.covers:
                engine.add_cover(w, c.x, c.y, c.radius, c.height)
        types = _register_types(engine, w, setup)
        _apply_cone(engine, w, setup, types)
        rng, ids_by_group, ranges = random.Random(seed), {}, {}
        for side in ((1, 0) if swap else (0, 1)):
            _spawn_side(engine, w, setup, side, types, rng, ids_by_group, ranges)
        goals = _issue_orders(engine, w, setup, ids_by_group)
        side_ids = tuple([u for gi, g in enumerate(setup.groups) if g.side == s for u in ids_by_group[gi]]
                         for s in (0, 1))
        start_hp = {u: engine.unit_hp(w, u) for ids in side_ids for u in ids}
        timeline = Timeline(engine, w, setup, ids_by_group, goals)
        return _run(engine, w, setup, side_ids, start_hp, heads, timeline)
    finally:
        engine.free_world(w)


def _strength(hp, ids, start_hp, head):
    return sum(hp[u] / start_hp[u] for u in ids if hp[u] > 0) / head


def _window_seconds(rows, first_contact, sample_every):
    """Unit-seconds of the (tick, v0, v1) samples in [first_contact, first_contact + OPENING_WINDOW_TICKS); (0.0, 0.0) without contact."""
    if first_contact < 0:
        return 0.0, 0.0
    inside = [r for r in rows if first_contact <= r[0] < first_contact + OPENING_WINDOW_TICKS]
    return tuple(sum(r[1 + s] for r in inside) * sample_every / TICKS_PER_SECOND for s in (0, 1))


def _predict(window):
    return "side0" if window[0] > window[1] else "side1" if window[1] > window[0] else "tie"


def _agreement(outcome, predicted_count, predicted_type):
    if outcome not in ("side0", "side1") or "tie" in (predicted_count, predicted_type):
        return "n/a"
    count_ok, type_ok = predicted_count == outcome, predicted_type == outcome
    if count_ok and type_ok:
        return "both_right"
    if type_ok:
        return "count_wrong_type_right"
    return "count_right_type_wrong" if count_ok else "both_wrong"


def _run(engine, w, setup, side_ids, start_hp, heads, timeline):
    hp = dict(start_hp)
    living = [u for ids in side_ids for u in ids]
    firing, weighted, tick, outcome = [], [], 0, None
    trace, last = ([] if setup.trace else None), {}
    state_rows = [] if setup.states else None
    all_ids = sorted(living)
    alive = [sum(1 for u in ids if hp[u] > 0) for ids in side_ids]
    unit_hp, step, arc = engine.unit_hp, engine.step, setup.firing_arc_deg

    def record():
        for u in all_ids:
            if hp[u] > 0:
                x, y = engine.unit_pos(w, u)
                last[u] = (x, y, engine.unit_facing(w, u))
                trace.append((tick, u, x, y, engine.unit_target(w, u), last[u][2], True))
            else:
                trace.append((tick, u, last[u][0], last[u][1], 0, last[u][2], False))

    def sample():
        firing.append((tick,) + tuple(count_able(engine, w, side_ids[0], side_ids[1], arc)))
        weighted.append((tick,) + tuple(count_weighted(engine, w, side_ids[0], side_ids[1], arc)))
        if state_rows is not None:
            state_rows.extend((tick, u, int(code)) for u, code in states(engine, w, side_ids[0], side_ids[1], arc))

    sample()
    if trace is not None:
        record()
    timeline.check(0, hp, zero=True)
    while outcome is None:
        step(w)
        tick += 1
        changed = False
        for u in living:
            h = unit_hp(w, u)
            if h != hp[u]:
                hp[u], changed = h, True
        if changed:
            living = [u for u in living if hp[u] > 0]
            alive = [sum(1 for u in ids if hp[u] > 0) for ids in side_ids]
        timeline.check(tick, hp)
        if trace is not None:
            record()
        if alive[0] == 0 and alive[1] == 0:
            outcome = "draw"
        elif alive[1] == 0:
            outcome = "side0"
        elif alive[0] == 0:
            outcome = "side1"
        elif tick >= setup.max_ticks:
            outcome = "cap"
        if tick % setup.sample_every == 0:
            sample()

    strength = tuple(_strength(hp, side_ids[s], start_hp, heads[s]) for s in (0, 1))
    seconds = tuple(sum(row[1 + s] for row in firing) * setup.sample_every / TICKS_PER_SECOND for s in (0, 1))
    wsec = tuple(sum(row[1 + s] for row in weighted) * setup.sample_every / TICKS_PER_SECOND for s in (0, 1))
    contact = next((t for t, a0, a1 in firing if a0 + a1 > 0), -1)
    fwin = _window_seconds(firing, contact, setup.sample_every)
    wwin = _window_seconds(weighted, contact, setup.sample_every)
    pcount, ptype = _predict(fwin), _predict(wwin)
    return FightResult(outcome=outcome, margin=strength[0] - strength[1], strength_left=strength,
                       survivors=tuple(alive), heads=heads, ticks=tick, first_contact_tick=contact,
                       firing=firing, firing_unit_seconds=seconds, trace=trace,
                       steps_fired=tuple(timeline.fired), weighted_unit_seconds=wsec, states=state_rows,
                       winner=outcome if outcome in ("side0", "side1") else None, firing_window=fwin,
                       weighted_window=wwin, predicted_count=pcount, predicted_type=ptype,
                       agreement=_agreement(outcome, pcount, ptype))
