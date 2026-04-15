import math
import config


class GradientSource:
    __slots__ = ("position", "property_type", "radius", "intensity", "falloff")

    def __init__(self, position, property_type, radius, intensity, falloff="linear"):
        self.position = position
        self.property_type = property_type
        self.radius = radius
        self.intensity = intensity
        self.falloff = falloff


class SpineNode:
    __slots__ = ("position", "node_type", "properties")

    def __init__(self, position, node_type, properties=None):
        self.position = position
        self.node_type = node_type
        self.properties = properties or {}


class SpatialHash:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self._cells = {}

    def _key(self, x, y):
        return (int(x // self.cell_size), int(y // self.cell_size))

    def clear(self):
        self._cells.clear()

    def insert(self, unit_id, x, y):
        key = self._key(x, y)
        if key not in self._cells:
            self._cells[key] = []
        self._cells[key].append(unit_id)

    def query(self, x, y, radius):
        results = []
        cell_radius = int(math.ceil(radius / self.cell_size))
        cx, cy = self._key(x, y)
        r_sq = radius * radius
        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                cell = self._cells.get((cx + dx, cy + dy))
                if cell:
                    results.extend(cell)
        return results

    def query_outward(self, x, y, max_radius):
        """Yield unit IDs in outward ring order from (x, y).

        Ring 0 (own cell) first, then ring 1 (8 adjacent cells), etc.
        Yields directly from stored cell lists — no per-ring allocations.
        Callers break on the first valid hit to get the nearest target.
        """
        cx, cy = self._key(x, y)
        max_ring = int(math.ceil(max_radius / self.cell_size))
        for ring in range(max_ring + 1):
            if ring == 0:
                cell = self._cells.get((cx, cy))
                if cell: yield from cell
            else:
                for dx in range(-ring, ring + 1):
                    cell = self._cells.get((cx + dx, cy + ring))
                    if cell: yield from cell
                    cell = self._cells.get((cx + dx, cy - ring))
                    if cell: yield from cell
                for dy in range(-ring + 1, ring):
                    cell = self._cells.get((cx + ring, cy + dy))
                    if cell: yield from cell
                    cell = self._cells.get((cx - ring, cy + dy))
                    if cell: yield from cell

    def rebuild(self, positions):
        self.clear()
        for unit_id, (x, y) in positions.items():
            self.insert(unit_id, x, y)


class TacticalMap:
    def __init__(self, width, height, gradient_sources=None, spine_nodes=None, layers=1,
                 drifting_nodes=None, edges=None):
        self.width = width
        self.height = height
        self.layers = layers
        self.gradient_sources = gradient_sources or []
        self.spine_nodes = spine_nodes or []
        self.drifting_nodes = drifting_nodes or []
        # list of (SpineNode_a, SpineNode_b, edge_type_str) — populated by map generator
        self.edges = edges or []
        self._sources_by_type = {}
        for src in self.gradient_sources:
            if src.property_type not in self._sources_by_type:
                self._sources_by_type[src.property_type] = []
            self._sources_by_type[src.property_type].append(src)
        self.spatial_hash = SpatialHash(config.SPATIAL_HASH_CELL_SIZE)   # sensor-pursuit; large cells
        self.target_hash  = SpatialHash(config.TARGET_HASH_CELL_SIZE)    # attack-range ring search; small cells

    def _sample_gradient(self, x, y, property_type):
        sources = self._sources_by_type.get(property_type, [])
        if not sources:
            return 0.0
        total = 0.0
        for src in sources:
            dx = x - src.position[0]
            dy = y - src.position[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist >= src.radius:
                continue
            t = dist / src.radius
            if src.falloff == "linear":
                falloff = 1.0 - t
            elif src.falloff == "quadratic":
                falloff = (1.0 - t) ** 2
            elif src.falloff == "constant":
                falloff = 1.0
            else:
                falloff = 1.0 - t
            total += src.intensity * falloff
        return max(0.0, min(1.0, total))

    def sensor_interference(self, x, y):
        return self._sample_gradient(x, y, "sensor_interference")

    def elevation(self, x, y):
        return self._sample_gradient(x, y, "elevation")

    def obstacle_density(self, x, y):
        return self._sample_gradient(x, y, "obstacle_density")

    def cover_density(self, x, y):
        return self._sample_gradient(x, y, "cover_density")

    def layer_accessibility(self, x, y, layer):
        if layer < 0 or layer >= self.layers:
            return False
        if self.layers == 1:
            return layer == 0
        access_val = self._sample_gradient(x, y, f"layer_block_{layer}")
        return access_val < 0.5

    def get_spine_nodes_by_type(self, node_type):
        return [n for n in self.spine_nodes if n.node_type == node_type]

    def current_spine_node_positions(self, tick):
        return {dn.node_id: dn.position_at(tick) for dn in self.drifting_nodes}

    def in_bounds(self, x, y):
        return 0 <= x <= self.width and 0 <= y <= self.height
