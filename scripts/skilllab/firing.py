"""Units able to fire at one instant (spec AC 10)."""


def _living(engine, w, units, ranges):
    out = []
    for u in units:
        if engine.unit_alive(w, u):
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


def count_able(engine, w, units0, units1, ranges):
    side0 = _living(engine, w, units0, ranges)
    side1 = _living(engine, w, units1, ranges)
    return _able(engine, w, side0, side1), _able(engine, w, side1, side0)


def unit_weight(stats):
    """A unit's damage rate, base_damage per attack_interval."""
    if stats["attack_interval"] <= 0:
        raise ValueError("attack_interval must be positive, got %r" % (stats["attack_interval"],))
    return stats["base_damage"] / stats["attack_interval"]


def _seen(engine, w, friends, targets):
    """Targets (by unit id) that any living friend sees; one scan of the friends per target."""
    return {e for e, *_ in targets if any(engine.can_see(w, f, e) for f, *_ in friends)}


def _able_weighted(engine, w, shooters, targets, seen, weights, reach):
    total = 0.0
    for u, x, y, layer, rng in shooters:
        up, down = reach.get(u, (0, 0)) if reach else (0, 0)
        for e, ex, ey, elayer, _ in targets:
            if not -down <= elayer - layer <= up or e not in seen:
                continue
            dx, dy = ex - x, ey - y
            if dx * dx + dy * dy <= rng * rng and engine.can_shoot(w, u, e):
                total += weights[u]
                break
    return float(total)


def count_able_weighted(engine, w, units0, units1, ranges, weights, reach=None):
    """Sum of weights of units with a seen, shootable enemy in range and layer reach; sight is shared by the side."""
    side0 = _living(engine, w, units0, ranges)
    side1 = _living(engine, w, units1, ranges)
    seen0, seen1 = _seen(engine, w, side0, side1), _seen(engine, w, side1, side0)
    return (_able_weighted(engine, w, side0, side1, seen0, weights, reach),
            _able_weighted(engine, w, side1, side0, seen1, weights, reach))
