from dataclasses import dataclass
import config

DRIFTABLE_NODE_TYPES = {"objective", "reinforcement_structure"}


@dataclass
class DriftingNode:
    node_id: str
    node_type: str       # must be in DRIFTABLE_NODE_TYPES
    spine_node: object   # reference to the SpineNode in TacticalMap.spine_nodes
    waypoints: list      # list of (x, y) absolute canvas positions
    period_ticks: int
    mode: str            # "ping_pong" or "loop"

    def position_at(self, tick):
        t = tick % self.period_ticks
        if self.mode == "ping_pong":
            return _ping_pong(self.waypoints, self.period_ticks, t)
        return _loop(self.waypoints, self.period_ticks, t)


def _ping_pong(waypoints, period_ticks, t):
    n = len(waypoints)
    num_seg = 2 * (n - 1)
    seg_len = period_ticks / num_seg
    seg_idx = min(int(t / seg_len), num_seg - 1)
    seg_t   = max(0.0, min(1.0, (t - seg_idx * seg_len) / seg_len))

    if seg_idx < n - 1:
        wp_a = waypoints[seg_idx]
        wp_b = waypoints[seg_idx + 1]
    else:
        back = seg_idx - (n - 1)
        wp_a = waypoints[n - 1 - back]
        wp_b = waypoints[n - 2 - back]

    return (wp_a[0] + (wp_b[0] - wp_a[0]) * seg_t,
            wp_a[1] + (wp_b[1] - wp_a[1]) * seg_t)


def _loop(waypoints, period_ticks, t):
    n = len(waypoints)
    seg_len = period_ticks / n
    seg_idx = min(int(t / seg_len), n - 1)
    seg_t   = max(0.0, min(1.0, (t - seg_idx * seg_len) / seg_len))

    wp_a = waypoints[seg_idx]
    wp_b = waypoints[(seg_idx + 1) % n]

    return (wp_a[0] + (wp_b[0] - wp_a[0]) * seg_t,
            wp_a[1] + (wp_b[1] - wp_a[1]) * seg_t)


def update_drifting_nodes(engine, tick):
    for dnode in engine.map.drifting_nodes:
        dnode.spine_node.position = dnode.position_at(tick)
