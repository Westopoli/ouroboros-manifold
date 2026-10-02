"""One tactical fight of one setup, stepped tick by tick (spec AC 5-11)."""
import random

from scripts.skilllab.contract import SHIFT_MAX, TICKS_PER_SECOND, FightResult
from scripts.skilllab.firing import count_able
from scripts.skilllab.formations import place

FIRST_CUSTOM_TYPE_ID = 100


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
            stats = dict(entry)
        engine.register_unit_type(w, next_id, stats)
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


def _issue_orders(engine, w, setup, ids_by_group):
    first_anchor = {}
    for g in setup.groups:
        first_anchor.setdefault(g.side, (g.x, g.y))
    for gi, g in enumerate(setup.groups):
        if g.order == "idle":
            continue
        goal = g.goal if g.goal is not None else first_anchor[1 - g.side]
        if g.order == "attack_move":
            engine.order_attack_move(w, ids_by_group[gi], goal[0], goal[1])
        elif g.order == "move":
            engine.order_move(w, ids_by_group[gi], goal[0], goal[1])
        else:
            raise ValueError("unknown order %r" % (g.order,))


def fight(setup, seed=0, swap=False, engine=None):
    heads = tuple(sum(g.count for g in setup.groups if g.side == s) for s in (0, 1))
    if min(heads) < 1:
        raise ValueError("each side needs at least one unit, got headcounts %r" % (heads,))
    if min(setup.max_ticks, setup.stalemate_ticks, setup.sample_every) < 1:
        raise ValueError("max_ticks, stalemate_ticks and sample_every must each be at least 1")
    if engine is None:
        from scripts.skilllab.engine import Engine
        engine = Engine()

    w = engine.new_world(seed)
    try:
        if not setup.abilities:
            engine.disable_abilities(w)
        types = _register_types(engine, w, setup)
        rng, ids_by_group, ranges = random.Random(seed), {}, {}
        for side in ((1, 0) if swap else (0, 1)):
            _spawn_side(engine, w, setup, side, types, rng, ids_by_group, ranges)
        _issue_orders(engine, w, setup, ids_by_group)
        side_ids = tuple([u for gi, g in enumerate(setup.groups) if g.side == s for u in ids_by_group[gi]]
                         for s in (0, 1))
        start_hp = {u: engine.unit_hp(w, u) for ids in side_ids for u in ids}
        return _run(engine, w, setup, side_ids, start_hp, ranges, heads)
    finally:
        engine.free_world(w)


def _strength(hp, ids, start_hp, head):
    return sum(hp[u] / start_hp[u] for u in ids if hp[u] > 0) / head


def _run(engine, w, setup, side_ids, start_hp, ranges, heads):
    hp = dict(start_hp)
    living = [u for ids in side_ids for u in ids]
    firing, tick, quiet, outcome = [], 0, 0, None

    def sample():
        a0, a1 = count_able(engine, w, side_ids[0], side_ids[1], ranges)
        firing.append((tick, a0, a1))

    sample()
    while outcome is None:
        engine.step(w)
        tick += 1
        changed = False
        for u in living:
            h = engine.unit_hp(w, u)
            if h != hp[u]:
                hp[u], changed = h, True
        living = [u for u in living if hp[u] > 0]
        quiet = 0 if changed else quiet + 1
        alive = [sum(1 for u in ids if hp[u] > 0) for ids in side_ids]
        if alive[0] == 0 and alive[1] == 0:
            outcome = "stalemate"
        elif alive[1] == 0:
            outcome = "side0"
        elif alive[0] == 0:
            outcome = "side1"
        elif quiet >= setup.stalemate_ticks:
            outcome = "stalemate"
        elif tick >= setup.max_ticks:
            outcome = "cap"
        if tick % setup.sample_every == 0:
            sample()

    strength = tuple(_strength(hp, side_ids[s], start_hp, heads[s]) for s in (0, 1))
    seconds = tuple(sum(row[1 + s] for row in firing) * setup.sample_every / TICKS_PER_SECOND for s in (0, 1))
    contact = next((t for t, a0, a1 in firing if a0 + a1 > 0), -1)
    return FightResult(outcome=outcome, margin=strength[0] - strength[1], strength_left=strength,
                       survivors=tuple(alive), heads=heads, ticks=tick, first_contact_tick=contact,
                       firing=firing, firing_unit_seconds=seconds)
