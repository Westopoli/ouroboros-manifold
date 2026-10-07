"""One tactical fight of one setup, stepped tick by tick (spec AC 5-11).
A Setup with approach > 0 is first opened by approach.approach_setup (move to a stop line, then attack_move)."""
import math
import random

from scripts.skilllab.approach import approach_setup
from scripts.skilllab.contract import (BLIND_TICKS, DRAW_BAND, HOLD_RADIUS, REISSUE_TICKS, SHIFT_MAX, TICKS_PER_SECOND, FightResult)
from scripts.skilllab.firing import count_able, count_able_weighted, unit_states, unit_weight
from scripts.skilllab.formations import place
from scripts.skilllab.mopup import mopup_goal
from scripts.skilllab.timeline import Timeline, first_anchors, validate

FIRST_CUSTOM_TYPE_ID = 100
SLOT_RADIUS = 440


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
            stats = {k: v for k, v in entry.items() if k != "reach"}
        engine.register_unit_type(w, next_id, stats)
        if "reach" in entry:
            engine.set_reach(w, next_id, *entry["reach"])
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
        goal = g.goal if g.goal is not None else first_anchor[1 - g.side]
        if g.order == "attack_move":
            issue = engine.order_attack_move
        elif g.order == "move":
            issue = engine.order_move
        elif g.order == "group_move":
            issue = engine.order_group_move
        else:
            raise ValueError("unknown order %r" % (g.order,))
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


def fight(setup, seed=0, swap=False, engine=None):
    heads = tuple(sum(g.count for g in setup.groups if g.side == s) for s in (0, 1))
    if min(heads) < 1:
        raise ValueError("each side needs at least one unit, got headcounts %r" % (heads,))
    if min(setup.max_ticks, setup.stalemate_ticks, setup.sample_every) < 1:
        raise ValueError("max_ticks, stalemate_ticks and sample_every must each be at least 1")
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
        mop_sides = (0, 1) if setup.mopup else ()
        setup = approach_setup(setup, {name: reach for name, (tid, reach) in types.items()})
        rng, ids_by_group, ranges = random.Random(seed), {}, {}
        for side in ((1, 0) if swap else (0, 1)):
            _spawn_side(engine, w, setup, side, types, rng, ids_by_group, ranges)
        goals = _issue_orders(engine, w, setup, ids_by_group)
        side_ids = tuple([u for gi, g in enumerate(setup.groups) if g.side == s for u in ids_by_group[gi]]
                         for s in (0, 1))
        start_hp = {u: engine.unit_hp(w, u) for ids in side_ids for u in ids}
        timeline = Timeline(engine, w, setup, ids_by_group, goals)
        wt = _weights(engine, w, setup, types, ids_by_group) if setup.weighted else None
        return _run(engine, w, setup, ids_by_group, side_ids, start_hp, ranges, heads, timeline, wt, mop_sides)
    finally:
        engine.free_world(w)


def _weights(engine, w, setup, types, ids_by_group):
    """(weights, reach) per unit id, read from the stats and reach of its type."""
    weights, reach, by_type = {}, {}, {}
    for gi, g in enumerate(setup.groups):
        tid = types[g.unit][0]
        if tid not in by_type:
            by_type[tid] = (unit_weight(engine.type_stats(w, tid)), engine.profile_reach(w, tid))
        for u in ids_by_group[gi]:
            weights[u], reach[u] = by_type[tid]
    return weights, reach


def _strength(hp, ids, start_hp, head):
    return sum(hp[u] / start_hp[u] for u in ids if hp[u] > 0) / head


def _sees(engine, w, side_ids, hp):
    """True when some living unit can see a living enemy."""
    living = [[u for u in ids if hp[u] > 0] for ids in side_ids]
    return any(engine.can_see(w, a, e) for s in (0, 1) for a in living[s] for e in living[1 - s])


def _winner(hp, side_ids):
    left = [sum(hp[u] for u in ids if hp[u] > 0) for ids in side_ids]
    if abs(left[0] - left[1]) <= DRAW_BAND * max(left):
        return "draw"
    return "side0" if left[0] > left[1] else "side1"


def _held(engine, w, setup, side_ids, hp, since_damage):
    """The defender holds its anchor: half its living units within HOLD_RADIUS of it, no living attacker that close."""
    if setup.hold_anchor is None or since_damage < setup.hold_ticks:
        return False
    ax, ay = setup.hold_anchor

    def near(u):
        x, y = engine.unit_pos(w, u)
        return math.hypot(x - ax, y - ay) <= HOLD_RADIUS

    mine = [u for u in side_ids[setup.defender_side] if hp[u] > 0]
    if sum(1 for u in mine if near(u)) * 2 < len(mine):
        return False
    return not any(near(u) for u in side_ids[1 - setup.defender_side] if hp[u] > 0)


def _run(engine, w, setup, ids_by_group, side_ids, start_hp, ranges, heads, timeline, wt=None, mop_sides=()):
    hp = dict(start_hp)
    living = [u for ids in side_ids for u in ids]
    firing, tick, quiet, outcome = [], 0, 0, None
    first_damage, blind_from, winner = None, None, None
    weighted = [] if wt else None
    trace, last = ([] if setup.trace else None), {}
    states, had_dest, ends = ([], set(), {}) if setup.states else (None, None, None)
    all_ids = sorted(living)
    alive_set = {u for u in living if hp[u] > 0}
    alive = [sum(1 for u in ids if hp[u] > 0) for ids in side_ids]
    unit_hp, step = engine.unit_hp, engine.step

    def record():
        for u in all_ids:
            if hp[u] > 0:
                x, y = engine.unit_pos(w, u)
                last[u] = (x, y, engine.unit_facing(w, u))
                trace.append((tick, u, x, y, engine.unit_target(w, u), last[u][2], True))
            else:
                trace.append((tick, u, last[u][0], last[u][1], 0, last[u][2], False))

    def sample():
        a0, a1 = count_able(engine, w, side_ids[0], side_ids[1], ranges, alive_set)
        firing.append((tick, a0, a1))
        if weighted is not None:
            weighted.append((tick,) + count_able_weighted(engine, w, side_ids[0], side_ids[1], ranges, wt[0], wt[1], alive_set))

    def record_states():
        for u, (state, dest) in sorted(unit_states(engine, w, side_ids[0], side_ids[1], ranges, alive_set).items()):
            states.append((tick, u, state))
            if dest is not None:
                had_dest.add(u)
            elif u in had_dest and u not in ends:
                ends[u] = tick

    mopup = [0] if setup.mopup else None
    before = [{u: engine.unit_pos(w, u) for u in all_ids}] if setup.mopup else None   # positions one interval ago

    def eligible(s):
        order = {gi: g.order for gi, g in enumerate(setup.groups) if g.side == s}
        for i, _tick in timeline.fired:
            st = setup.timeline[i]
            if st.group in order:
                order[st.group] = st.order
        return all(o == "attack_move" for o in order.values())

    def mop_up():
        for s in mop_sides:
            if not eligible(s):
                continue
            goal = mopup_goal(engine, w, side_ids[s], side_ids[1 - s], ranges, alive_set, before[0], timeline.anchors[1 - s])
            if goal is not None:
                for ids, _offset in _chunks(engine, w, [u for u in side_ids[s] if u in alive_set]):
                    engine.order_attack_move(w, ids, goal[0], goal[1])   # v2: no chunk offsets
                mopup[0] += 1
        before[0] = {u: engine.unit_pos(w, u) for u in living}

    def reissue():
        """Ruled 2026-10-07 (Westley 2026-10-06, attack-move all units to the same spot): every group of either side with an enemy in
        sight and no target attack-moves at the defender's anchor again."""
        for gi, g in enumerate(setup.groups):
            ids = [u for u in ids_by_group[gi] if hp[u] > 0]
            foes = [u for u in side_ids[1 - g.side] if hp[u] > 0]
            if ids and not any(engine.unit_target(w, u) for u in ids) and any(engine.can_see(w, a, e) for a in ids for e in foes):
                for chunk, (dx, dy) in _chunks(engine, w, ids):
                    engine.order_attack_move(w, chunk, setup.hold_anchor[0] + dx, setup.hold_anchor[1] + dy)

    damaged = False
    sample()
    if trace is not None:
        record()
    if states is not None:
        record_states()
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
            alive_set = set(living)
            alive = [sum(1 for u in ids if hp[u] > 0) for ids in side_ids]
        timeline.check(tick, hp)
        if mopup is not None and tick % setup.mopup_interval_ticks == 0:
            mop_up()
        if setup.decided_by_survivors and setup.hold_anchor is not None and tick % REISSUE_TICKS == 0 and alive[0] and alive[1]:
            reissue()
        if changed and not damaged:
            first_damage = tick
        damaged = damaged or changed
        quiet = 0 if changed or (setup.quiet_from_first_damage and not damaged) else quiet + 1   # flag set: the window opens at first damage
        if setup.decided_by_survivors and first_damage is not None and alive[0] and alive[1]:
            blind_from = None if _sees(engine, w, side_ids, hp) else tick if blind_from is None else blind_from
        if trace is not None:
            record()
        if states is not None:
            record_states()
        if alive[0] == 0 and alive[1] == 0:
            outcome = "draw"
        elif alive[1] == 0:
            outcome = "side0"
        elif alive[0] == 0:
            outcome = "side1"
        elif setup.decided_by_survivors and first_damage is not None and _held(engine, w, setup, side_ids, hp, tick - first_damage):
            outcome, winner = "held", "side%d" % setup.defender_side
        elif blind_from is not None and tick - blind_from >= BLIND_TICKS:
            outcome, winner = "decided", _winner(hp, side_ids)
        elif setup.decided_by_survivors and first_damage is not None and setup.silence_ticks and quiet >= setup.silence_ticks:
            outcome, winner = "decided", _winner(hp, side_ids)
        elif not setup.decided_by_survivors and quiet >= setup.stalemate_ticks:
            outcome = "stalemate"
        elif tick >= setup.max_ticks:
            outcome = "cap"
        if tick % setup.sample_every == 0:
            sample()

    strength = tuple(_strength(hp, side_ids[s], start_hp, heads[s]) for s in (0, 1))
    seconds = tuple(sum(row[1 + s] for row in firing) * setup.sample_every / TICKS_PER_SECOND for s in (0, 1))
    wsec = None if weighted is None else tuple(
        sum(row[1 + s] for row in weighted) * setup.sample_every / TICKS_PER_SECOND for s in (0, 1))
    contact = next((t for t, a0, a1 in firing if a0 + a1 > 0), -1)
    return FightResult(outcome=outcome, margin=strength[0] - strength[1], strength_left=strength,
                       survivors=tuple(alive), heads=heads, ticks=tick, first_contact_tick=contact,
                       firing=firing, firing_unit_seconds=seconds, trace=trace,
                       steps_fired=tuple(timeline.fired), weighted=weighted, weighted_unit_seconds=wsec,
                       states=states, order_ends=None if ends is None else tuple(sorted(ends.items())),
                       mopup_orders=None if mopup is None else mopup[0], winner=winner)
