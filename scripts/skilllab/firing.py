"""Units able to fire at one instant (spec AC 10)."""


def _living(engine, w, units, ranges, alive=None):
    out = []
    for u in units:
        if (u in alive) if alive is not None else engine.unit_alive(w, u):
            x, y = engine.unit_pos(w, u)
            out.append((u, x, y, engine.unit_layer(w, u), ranges[u]))
    return out


def _able(engine, w, shooters, targets):
    count = 0
    for u, x, y, layer, reach in shooters:
        reach_sq = reach * reach
        for e, ex, ey, elayer, _ in targets:
            if elayer != layer:
                continue
            dx, dy = ex - x, ey - y
            if dx * dx + dy * dy <= reach_sq and engine.can_shoot(w, u, e):
                count += 1
                break
    return count


def unit_states(engine, w, units0, units1, ranges, alive=None):
    """{unit: (state, destination)} for each living unit: can fire, blocked, walking or no target."""
    side0 = _living(engine, w, units0, ranges, alive)
    side1 = _living(engine, w, units1, ranges, alive)
    out = {}
    for shooters, targets in ((side0, side1), (side1, side0)):
        for u, x, y, layer, reach in shooters:
            in_range = shootable = False
            for e, ex, ey, elayer, _ in targets:
                dx, dy = ex - x, ey - y
                if elayer == layer and dx * dx + dy * dy <= reach * reach:
                    in_range = True
                    if engine.can_shoot(w, u, e):
                        shootable = True
                        break
            dest = engine.unit_destination(w, u)
            state = ("can fire" if shootable else "blocked" if in_range
                     else "walking" if dest is not None else "no target")
            out[u] = (state, dest)
    return out


def count_able(engine, w, units0, units1, ranges, alive=None):
    side0 = _living(engine, w, units0, ranges, alive)
    side1 = _living(engine, w, units1, ranges, alive)
    return _able(engine, w, side0, side1), _able(engine, w, side1, side0)


def unit_weight(stats):
    """A unit's damage rate, base_damage per attack_interval."""
    if stats["attack_interval"] <= 0:
        raise ValueError("attack_interval must be positive, got %r" % (stats["attack_interval"],))
    return stats["base_damage"] / stats["attack_interval"]


def _able_weighted(engine, w, shooters, targets, weights, reach):
    by_id = {e: (ex, ey, elayer) for e, ex, ey, elayer, _ in targets}
    total = 0.0
    for u, x, y, layer, rng in shooters:
        t = engine.unit_target(w, u)
        if t not in by_id:
            continue
        ex, ey, elayer = by_id[t]
        up, down = reach.get(u, (0, 0)) if reach else (0, 0)
        dx, dy = ex - x, ey - y
        if -down <= elayer - layer <= up and dx * dx + dy * dy <= rng * rng and engine.can_shoot(w, u, t):
            total += weights[u]
    return float(total)


def count_able_weighted(engine, w, units0, units1, ranges, weights, reach=None, alive=None):
    """Sum of weights of units whose engine target is a living enemy in range and layer reach that they can shoot."""
    side0 = _living(engine, w, units0, ranges, alive)
    side1 = _living(engine, w, units1, ranges, alive)
    return (_able_weighted(engine, w, side0, side1, weights, reach),
            _able_weighted(engine, w, side1, side0, weights, reach))
