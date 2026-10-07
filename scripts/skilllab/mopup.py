"""Lab rule, provisional (v2; A199, A201, Architect): the re-order, a player's obvious next order after the clash.
A side re-orders when no unit of it has an enemy in attack range (same layer, within range, and able to shoot it: a wall
between the pair does not count) and it sees at least one enemy. A unit that still has a
destination blocks the re-order only if it moved at least MOVED_WU in the last WINDOW_TICKS. The order sends every unit of
the side at the position of the nearest seen enemy to the side's centroid (the enemy side's starting anchor when none is seen), with no chunk offsets (chunked only when the
side does not fit inside the scatter limit of E-13 R-095-03, each chunk aimed at that same point)."""

MOVED_WU = 30.0        # a unit with a destination counts as still moving if it covered this much ground
WINDOW_TICKS = 200     # ... over this many ticks (the mop-up interval, so the window is the last interval)
RULE_TEXT = ("Lab rule, provisional (v2): a side re-orders when none of its units has an enemy in attack range and it sees "
             "at least one enemy; a unit with a destination blocks the re-order only if it moved at least %d wu in the "
             "last %d ticks; the order sends every unit of the side at the position of the nearest seen enemy to the "
             "side's centroid, with no chunk offsets (one group if the side fits inside the 450 wu scatter limit of E-13 "
             "R-095-03, otherwise chunks all aimed at that point); considered every mopup_interval_ticks, counted per "
             "fight, same for both sides." % (MOVED_WU, WINDOW_TICKS))


def mopup_goal(engine, w, mine, theirs, ranges, alive, before=None, enemy_anchor=None):
    """The (x, y) to send `mine` at (nearest seen enemy to their centroid), or None when the rule does not apply now.
    `enemy_anchor` is the goal when no enemy is seen. `before` maps unit to its position WINDOW_TICKS ago; a unit missing from it counts as not having moved."""
    mine = [u for u in mine if u in alive]
    theirs = [e for e in theirs if e in alive]
    if not mine or not theirs:
        return None
    pos = {u: engine.unit_pos(w, u) for u in mine + theirs}
    before = before or {}
    for u in mine:
        if engine.unit_destination(w, u) is not None and u in before:
            if ((pos[u][0] - before[u][0]) ** 2 + (pos[u][1] - before[u][1]) ** 2) >= MOVED_WU * MOVED_WU:
                return None
    layer = {u: engine.unit_layer(w, u) for u in mine + theirs}
    for u in mine:
        for e in theirs:
            dx, dy = pos[e][0] - pos[u][0], pos[e][1] - pos[u][1]
            if layer[e] == layer[u] and dx * dx + dy * dy <= ranges[u] * ranges[u] and engine.can_shoot(w, u, e):
                return None
    seen = [e for e in theirs if any(engine.can_see(w, u, e) for u in mine)]
    if not seen:
        return enemy_anchor
    cx, cy = sum(pos[u][0] for u in mine) / len(mine), sum(pos[u][1] for u in mine) / len(mine)
    return min((pos[e] for e in seen), key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
