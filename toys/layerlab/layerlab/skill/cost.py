"""Force by heads, with cost reported beside it (SPEC.md sections 14.1 and 14.5)."""
import math

_COST_DIVISOR = 31.25


def _type(scn, name):
    return {**scn.get("type_defaults", {}), **scn["types"][name]}


def unit_cost(scn, type_name):
    t = _type(scn, type_name)
    if "cost" in t:
        return float(t["cost"])
    return float(t["hp"]) * float(t["dmg"]) / float(t["interval_s"]) / _COST_DIVISOR


def side_units(scn):
    rows = []
    for gi, g in enumerate(scn.get("groups", [])):
        side = 0 if g["side"] == "A" else 1
        cost = unit_cost(scn, g["type"])
        hp0 = float(_type(scn, g["type"])["hp"])
        for _ in range(int(g["count"])):
            rows.append({"side": side, "type": g["type"], "cost": cost, "hp0": hp0, "group": gi})
    return rows


def force_cost(scn, side):
    return sum(r["cost"] for r in side_units(scn) if r["side"] == side)


def counts_for_cost(shares, total_cost, scn):
    """Largest-remainder rounding on cost shares; every positive share gets at least one unit."""
    pos = {t: s for t, s in shares.items() if s > 0}
    if total_cost <= 0 or not pos:
        return {}
    norm = sum(pos.values())
    cost = {t: unit_cost(scn, t) for t in pos}
    ideal = {t: pos[t] / norm * total_cost / cost[t] for t in pos}
    count = {t: max(1, math.floor(ideal[t] + 1e-9)) for t in pos}
    order = {t: i for i, t in enumerate(pos)}
    total = sum(count[t] * cost[t] for t in pos)
    while True:
        gap = abs(total - total_cost)
        for t in sorted(pos, key=lambda t: (-(ideal[t] - count[t]), order[t])):
            if abs(total + cost[t] - total_cost) < gap - 1e-12:
                count[t] += 1
                total += cost[t]
                break
        else:
            return count


def counts_for_heads(shares, n, scn):
    """Largest-remainder rounding of shares * n; a positive share gets at least one head when n covers the types."""
    pos = {t: s for t, s in shares.items() if s > 0}
    if n <= 0 or not pos:
        return {}
    norm = sum(pos.values())
    ideal = {t: pos[t] / norm * n for t in pos}
    floor = 1 if n >= len(pos) else 0
    count = {t: max(floor, math.floor(ideal[t] + 1e-9)) for t in pos}
    order = {t: i for i, t in enumerate(pos)}
    while sum(count.values()) < n:
        t = min(pos, key=lambda t: (-(ideal[t] - count[t]), order[t]))
        count[t] += 1
    while sum(count.values()) > n:
        t = min((t for t in pos if count[t] > floor), key=lambda t: (ideal[t] - count[t], -order[t]))
        count[t] -= 1
    return {t: c for t, c in count.items() if c > 0}
