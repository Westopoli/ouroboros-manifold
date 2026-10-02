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
