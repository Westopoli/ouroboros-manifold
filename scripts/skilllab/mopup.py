"""Lab rule, provisional (A199, A201): the mop-up order, a player's obvious next order after the clash.
A side whose units have all stopped, none with an enemy in attack range, and that sees at least one enemy, re-issues its
attack-move at the centroid of the enemies it sees (the side's shared sight: an enemy any of its units can see)."""


def mopup_goal(engine, w, mine, theirs, ranges, alive):
    """The centroid (x, y) of the enemies `mine` sees, or None when the rule does not apply to this side now."""
    mine = [u for u in mine if u in alive]
    theirs = [e for e in theirs if e in alive]
    if not mine or not theirs or any(engine.unit_destination(w, u) is not None for u in mine):
        return None
    pos = {u: engine.unit_pos(w, u) for u in mine + theirs}
    layer = {u: engine.unit_layer(w, u) for u in mine + theirs}
    for u in mine:
        for e in theirs:
            dx, dy = pos[e][0] - pos[u][0], pos[e][1] - pos[u][1]
            if layer[e] == layer[u] and dx * dx + dy * dy <= ranges[u] * ranges[u]:
                return None
    seen = [e for e in theirs if any(engine.can_see(w, u, e) for u in mine)]
    if not seen:
        return None
    return sum(pos[e][0] for e in seen) / len(seen), sum(pos[e][1] for e in seen) / len(seen)
