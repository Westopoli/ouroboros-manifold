"""Snapshot ticks for the H-024 match-replay page, read from the nine-field lab trace."""


def first_contact_tick(rows, side_a, side_b):
    best = None
    for row in rows:
        tick, unit, target, alive = row[0], row[1], row[4], row[6]
        if not alive or (best is not None and tick >= best):
            continue
        if (unit in side_a and target in side_b) or (unit in side_b and target in side_a):
            best = tick
    return best


def sample_ticks(first, last, contact, n_even=12, offsets=(-20, -10, 10, 20)):
    if n_even == 1:
        ticks = [first]
    else:
        ticks = [round(first + k * (last - first) / (n_even - 1)) for k in range(n_even)]
    if contact is not None:
        ticks += [contact + o for o in offsets]
    return sorted({t for t in ticks if first <= t <= last})
