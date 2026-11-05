"""
Algorithmic fairness scoring for generated maps.

All metrics return player_value / enemy_value ratios (not symmetry scores).
Each ratio is checked against the archetype's FairnessTargetProfile.
Aggregate passes only when all four metrics fall within their tolerances.

Metrics:
  path_balance    — max-flow edge-disjoint path count from each side to objectives
  travel_time     — BFS hop count to nearest chokepoint (fallback: objective)
  vantage_balance — vantage nodes closer to player vs closer to enemy (proximity split)
  hazard_balance  — hazard_zone_anchor nodes closer to player vs closer to enemy
"""
import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collections import deque
from dataclasses import dataclass
from layout_instantiator import InstantiatedLayout
from archetype_filters import get_fairness_profile


# See also: docs/legacy/stage_specs/stage_11e_fairness_reconciliation_spec.md — D1 zero-count scope-narrowing
@dataclass
class FairnessScore:
    path_balance_ratio:   float
    path_balance_target:  tuple
    path_balance_pass:    bool
    path_balance_skipped: bool

    travel_time_ratio:    float
    travel_time_target:   tuple
    travel_time_pass:     bool
    travel_time_skipped:  bool

    vantage_ratio:        float
    vantage_target:       tuple
    vantage_pass:         bool
    vantage_skipped:      bool

    hazard_ratio:         float
    hazard_target:        tuple
    hazard_pass:          bool
    hazard_skipped:       bool

    archetype_profile:    str
    all_metrics_pass:     bool


def evaluate_fairness(inst: InstantiatedLayout, archetype: str) -> FairnessScore:
    profile = get_fairness_profile(archetype)

    player_nodes = [n for n in inst.spine_nodes if n.node_type == "staging"]
    enemy_nodes  = [n for n in inst.spine_nodes if n.node_type == "spawn_point"]
    objectives   = [n for n in inst.spine_nodes if n.node_type == "objective"]
    chokepoints  = [n for n in inst.spine_nodes if n.node_type == "chokepoint"]
    vantages     = [n for n in inst.spine_nodes if n.node_type == "vantage"]
    hazards      = [n for n in inst.spine_nodes if n.node_type == "hazard_zone_anchor"]

    adj = _build_adj(inst)

    player_ids    = {n.properties["zone_id"] for n in player_nodes}
    enemy_ids     = {n.properties["zone_id"] for n in enemy_nodes}
    objective_ids = {n.properties["zone_id"] for n in objectives}
    choke_ids     = {n.properties["zone_id"] for n in chokepoints}

    # "Front" = chokepoints if any, else objectives — measures time to reach the fight
    front_ids = choke_ids if choke_ids else objective_ids

    path_ratio   = _path_balance(player_ids, enemy_ids, objective_ids, adj)
    travel_ratio = _travel_time_balance(player_ids, enemy_ids, front_ids, adj)
    vant_ratio   = _proximity_balance(player_nodes, enemy_nodes, vantages)
    haz_ratio    = _proximity_balance(player_nodes, enemy_nodes, hazards)

    # Both-sides-zero → skip (D1: metric undefined when the node type is absent)
    vant_skipped = len(vantages) == 0
    haz_skipped  = len(hazards) == 0
    pb_skipped   = len(objective_ids) == 0
    tt_skipped   = len(front_ids) == 0

    def passes(ratio, profile_field):
        target, tol = profile_field
        return abs(ratio - target) <= tol

    pb_pass = passes(path_ratio,   profile.path_balance) if not pb_skipped else True
    tt_pass = passes(travel_ratio, profile.travel_time_balance) if not tt_skipped else True
    vb_pass = passes(vant_ratio,   profile.vantage_balance) if not vant_skipped else True
    hb_pass = passes(haz_ratio,    profile.hazard_balance) if not haz_skipped else True

    non_skipped = []
    if not pb_skipped:   non_skipped.append(pb_pass)
    if not tt_skipped:   non_skipped.append(tt_pass)
    if not vant_skipped: non_skipped.append(vb_pass)
    if not haz_skipped:  non_skipped.append(hb_pass)

    return FairnessScore(
        path_balance_ratio   = path_ratio,
        path_balance_target  = profile.path_balance,
        path_balance_pass    = pb_pass,
        path_balance_skipped = pb_skipped,
        travel_time_ratio    = travel_ratio,
        travel_time_target   = profile.travel_time_balance,
        travel_time_pass     = tt_pass,
        travel_time_skipped  = tt_skipped,
        vantage_ratio        = vant_ratio,
        vantage_target       = profile.vantage_balance,
        vantage_pass         = vb_pass,
        vantage_skipped      = vant_skipped,
        hazard_ratio         = haz_ratio,
        hazard_target        = profile.hazard_balance,
        hazard_pass          = hb_pass,
        hazard_skipped       = haz_skipped,
        archetype_profile    = archetype,
        all_metrics_pass     = all(non_skipped) if non_skipped else False,
    )


def is_acceptable(score: FairnessScore) -> bool:
    return score.all_metrics_pass


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_adj(inst: InstantiatedLayout) -> dict:
    adj = {}
    for e in inst.edges:
        n1 = inst.node_id_map.get(e.from_zone)
        n2 = inst.node_id_map.get(e.to_zone)
        if not n1 or not n2:
            continue
        adj.setdefault(e.from_zone, []).append(e.to_zone)
        adj.setdefault(e.to_zone,   []).append(e.from_zone)
    return adj


def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _safe_ratio(player_val, enemy_val):
    if enemy_val == 0 and player_val == 0:
        return 1.0
    if enemy_val == 0:
        return 2.0
    return player_val / enemy_val


def _bfs_min_hops(start_ids, target_ids, adj):
    """Return minimum BFS hop count from any start to any target."""
    dist = {s: 0 for s in start_ids}
    queue = deque(start_ids)
    while queue:
        zid = queue.popleft()
        if zid in target_ids:
            return dist[zid]
        for neighbor in adj.get(zid, []):
            if neighbor not in dist:
                dist[neighbor] = dist[zid] + 1
                queue.append(neighbor)
    return math.inf


def _travel_time_balance(player_ids, enemy_ids, front_ids, adj):
    p = _bfs_min_hops(player_ids, front_ids, adj)
    e = _bfs_min_hops(enemy_ids,  front_ids, adj)
    if p == math.inf and e == math.inf:
        return 1.0
    if e == 0:
        return 1.0
    if p == math.inf:
        return 2.0
    if e == math.inf:
        return 0.5
    return p / e


def _max_flow(source_ids, sink_ids, adj):
    """Count edge-disjoint paths from any source to any sink (BFS augmenting paths)."""
    # Build residual graph with unit capacity on each directed edge
    residual = {}
    for zid, neighbors in adj.items():
        for nid in neighbors:
            residual.setdefault(zid, {})[nid] = residual.setdefault(zid, {}).get(nid, 0) + 1

    # Add super-source S and super-sink T
    S, T = "__S__", "__T__"
    for s in source_ids:
        residual.setdefault(S, {})[s] = len(adj)   # effectively unlimited capacity
    for t in sink_ids:
        residual.setdefault(t, {})[T] = len(adj)

    flow = 0
    while True:
        # BFS to find an augmenting path S → T
        parent = {S: None}
        queue = deque([S])
        while queue and T not in parent:
            node = queue.popleft()
            for neighbor, cap in residual.get(node, {}).items():
                if cap > 0 and neighbor not in parent:
                    parent[neighbor] = node
                    queue.append(neighbor)

        if T not in parent:
            break

        # Augment along the path (capacity 1)
        node = T
        while parent[node] is not None:
            prev = parent[node]
            residual[prev][node] -= 1
            residual.setdefault(node, {})[prev] = residual.get(node, {}).get(prev, 0) + 1
            node = prev
        flow += 1

    return flow


def _path_balance(player_ids, enemy_ids, objective_ids, adj):
    p = _max_flow(player_ids, objective_ids, adj)
    e = _max_flow(enemy_ids,  objective_ids, adj)
    return _safe_ratio(p, e)


def _nearest_dist(node, reference_nodes):
    if not reference_nodes:
        return math.inf
    return min(_dist(node.position, r.position) for r in reference_nodes)


def _proximity_balance(player_nodes, enemy_nodes, feature_nodes):
    player_count = 0
    enemy_count  = 0
    tied         = 0
    for fn in feature_nodes:
        pd = _nearest_dist(fn, player_nodes)
        ed = _nearest_dist(fn, enemy_nodes)
        if pd < ed:
            player_count += 1
        elif ed < pd:
            enemy_count += 1
        else:
            tied += 1
    player_count += tied / 2
    enemy_count  += tied / 2
    return _safe_ratio(player_count, enemy_count)
