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


class Asteroid:
    __slots__ = ("asteroid_id", "cluster_id", "x", "y", "radius_xy", "height", "scale_class")

    def __init__(self, asteroid_id, cluster_id, x, y, radius_xy, height, scale_class):
        self.asteroid_id = asteroid_id
        self.cluster_id = cluster_id
        self.x = x
        self.y = y
        self.radius_xy = radius_xy
        self.height = height
        self.scale_class = scale_class  # "tiny" | "small" | "medium" | "huge"


class _AsteroidSpatialHash:
    # config.ASTEROID_SPATIAL_HASH_CELL not yet in config (L3 lands it); hardcoded 100.0.
    # See leaf-02.ASSUMPTIONS.md.
    _CELL = 100.0

    def __init__(self):
        self._cells: dict[tuple[int, int], list[int]] = {}

    def _key(self, x, y):
        return (int(x // self._CELL), int(y // self._CELL))

    def insert(self, asteroid_id: int, x: float, y: float):
        key = self._key(x, y)
        if key not in self._cells:
            self._cells[key] = []
        self._cells[key].append(asteroid_id)

    def query_bbox(self, x_min: float, y_min: float, x_max: float, y_max: float) -> set[int]:
        cx_min = int(x_min // self._CELL)
        cy_min = int(y_min // self._CELL)
        cx_max = int(x_max // self._CELL)
        cy_max = int(y_max // self._CELL)
        result: set[int] = set()
        for cx in range(cx_min, cx_max + 1):
            for cy in range(cy_min, cy_max + 1):
                cell = self._cells.get((cx, cy))
                if cell:
                    result.update(cell)
        return result


class AsteroidField:
    __slots__ = ("asteroids", "spatial_hash")

    def __init__(self, asteroids: list):
        self.asteroids = asteroids
        self.spatial_hash = _AsteroidSpatialHash()
        for ast in asteroids:
            self.spatial_hash.insert(ast.asteroid_id, ast.x, ast.y)


class TacticalMap:
    def __init__(self, width, height, gradient_sources=None, spine_nodes=None, layers=1,
                 drifting_nodes=None, edges=None, cover_polygons=None):
        # cover_polygons param accepted but ignored — polygon API retired (Wave 2.5R).
        # map_generator.py still passes it until L3 updates that caller.
        self.width = width
        self.height = height
        self.layers = layers
        self.gradient_sources = gradient_sources or []
        self.spine_nodes = spine_nodes or []
        self.drifting_nodes = drifting_nodes or []
        # list of (SpineNode_a, SpineNode_b, edge_type_str) — populated by map generator
        self.edges = edges or []
        self.asteroid_field = AsteroidField([])  # L3 overwrites with placed clusters
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

    def asteroid_blocks_los(self, ox: float, oy: float, oz: float,
                            tx: float, ty: float, tz: float) -> bool:
        """True if any asteroid cylinder blocks the ray (ox,oy,oz)→(tx,ty,tz).

        Algorithm per spec lines 170-178: 2D ray-circle closest-point check,
        then quadratic for s_enter/s_exit, then z-range check at intersection.
        """
        # Expand query bbox by 80wu (max huge-asteroid radius per D6).
        _MAX_R = 80.0
        x_min = min(ox, tx) - _MAX_R
        x_max = max(ox, tx) + _MAX_R
        y_min = min(oy, ty) - _MAX_R
        y_max = max(oy, ty) + _MAX_R
        candidates = self.asteroid_field.spatial_hash.query_bbox(x_min, y_min, x_max, y_max)
        if not candidates:
            return False

        ast_by_id = {a.asteroid_id: a for a in self.asteroid_field.asteroids}
        dx = tx - ox
        dy = ty - oy
        dz = tz - oz
        ray_len_sq = dx * dx + dy * dy
        # Degenerate ray (observer == target in 2D): no asteroid can block.
        if ray_len_sq == 0.0:
            return False

        for aid in candidates:
            ast = ast_by_id.get(aid)
            if ast is None:
                continue
            ax = ast.x - ox
            ay = ast.y - oy
            r = ast.radius_xy
            h = ast.height

            # Step 1: closest-point on 2D ray to asteroid center.
            s_close = max(0.0, min(1.0, (ax * dx + ay * dy) / ray_len_sq))
            cx = ox + s_close * dx - ast.x
            cy = oy + s_close * dy - ast.y
            if cx * cx + cy * cy > r * r:
                continue  # 2D miss

            # Step 2: quadratic for ray-circle intersection in 2D.
            # |O + s*(T-O) - A|^2 = r^2, rewrite in terms of (ax, ay) = A - O.
            # s^2*(dx^2+dy^2) - 2s*(ax*dx+ay*dy) + (ax^2+ay^2-r^2) = 0
            a_q = ray_len_sq
            b_q = -2.0 * (ax * dx + ay * dy)
            c_q = ax * ax + ay * ay - r * r
            disc = b_q * b_q - 4.0 * a_q * c_q
            if disc < 0.0:
                continue
            sqrt_disc = math.sqrt(disc)
            s_enter = max(0.0, (-b_q - sqrt_disc) / (2.0 * a_q))
            s_exit  = min(1.0, (-b_q + sqrt_disc) / (2.0 * a_q))
            if s_enter > s_exit:
                continue

            # Step 3: z-range at intersection.
            z_enter = oz + s_enter * dz
            z_exit  = oz + s_exit  * dz
            if min(z_enter, z_exit) > h:
                continue  # ray passes over cylinder top
            return True

        return False
