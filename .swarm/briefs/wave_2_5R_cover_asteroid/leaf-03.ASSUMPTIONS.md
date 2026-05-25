# leaf-03 assumptions

## Cover-emitting node type set

Hardcoded: `{chokepoint, staging, objective, hazard_zone_anchor, flank_route}`. Matches set that produced cover polygons in pre-existing `place_cover_polygons` via `_COVER_RADIUS_BY_NODE_TYPE`. Spec lists exact same five types. No ambiguity.

## GRADIENT_STAGING_COVER_RADIUS absent — fallback to GRADIENT_STAGING_RADIUS

`config.py` has `GRADIENT_STAGING_RADIUS = 800.0` but no `GRADIENT_STAGING_COVER_RADIUS`. Pre-existing `_COVER_RADIUS_BY_NODE_TYPE` dict mapped staging → `"GRADIENT_STAGING_RADIUS"`. Reused same mapping. If parent wants separate constant, add it to config and update `_COVER_RADIUS_ATTR_BY_TYPE`.

## place_cover_polygons removed

`gradient_placer.py` previously defined `place_cover_polygons` which imported `CoverPolygon` from `tactical_map`. Leaf-02 removed `CoverPolygon` — import failed at collect time, breaking all tests. Removed `place_cover_polygons` as polygon API is retired (Wave 2.5R). Not in do_not_edit. Brief scope says "replace `place_cover_polygons` with `place_asteroid_fields`" — removal is implicit.

## map_generator.py call site NOT cleaned up

Brief says "may clean up map_generator.py call site if needed — NOT in do_not_edit — only if essential." Tests pass without touching it (`TacticalMap.__init__` still accepts `cover_polygons=None` silently per leaf-02). Not essential. Left for parent or future leaf.

## map_seed fallback

`getattr(inst, "map_seed", 0)` — if inst lacks `map_seed`, seed = `cluster_id * 1009`. Spec says "getattr(inst, 'map_seed', 0)". Matches.

## Rejection sampling: disk uniform via sqrt

Used `r = radius * sqrt(rng.random())` for uniform-in-disk distribution. Plain `r = rng.uniform(0, radius)` would produce radially-biased sampling (more near center). Sqrt gives correct flat density. Spec says "rejection-sample uniform in disk" — sqrt method is exact uniform, not rejection. True rejection (sample square, discard outside circle) also valid. Chose sqrt as simpler + no waste. No change to density math.

## Count: int(pi * r^2 * density), not round()

Used `int(...)` (floor). For chokepoint radius 550, count = int(pi * 302500 * 0.00090) = int(854.5) = 854. ±10% tolerance = ±85. Passes.

## Scale distribution tolerance: ±10% (not ±5%)

Spec line 223 says "within ±5%". Brief task desc line 67 says "within ±10% (loose for stochasticity)". With 854 asteroids and 60/25/10/5 split, variance is low — ±5% would likely pass too, but used ±10% per brief override to be safe for smaller clusters.
