# CC Paste: Implement RVO Local Steering (Replace Reactive Collision)

## Context

We're replacing the current reactive push-apart collision system with proactive RVO (Reciprocal Velocity Obstacle) local steering — the same approach SC2 uses. This produces smooth unit flow, natural concave formations, and speed-dependent spreading (faster units fan out sooner). The current system pushes overlapping units apart after the fact; RVO adjusts velocities *before* movement to prevent overlaps entirely.

This also completes the removal of LOS blocking — the previous paste removed the damage-side LOS code, this paste replaces the movement-side collision code with the system that makes formations work without LOS blocking.

## Reference implementation

The algorithm is ORCA (Optimal Reciprocal Collision Avoidance), the refined version of RVO. Reference: https://github.com/MengGuo/RVO_Py_MAS — Python, plug-and-play, ~150 lines of core logic. The paper is van den Berg et al. 2011, "Reciprocal n-body collision avoidance."

The RVO2 library (https://gamma.cs.unc.edu/RVO2/) has Python bindings via pip: `pip install rvo2`. If the pip package is available and works in our environment, use it — it's C++ underneath and will be faster than pure Python. If not, implement the core algorithm in pure Python/numpy following the reference repo.

**Try this first:**
```
pip install rvo2 --break-system-packages
```
If that works, use the library. If not, implement from scratch — the algorithm is straightforward.

## What to remove from `movement.py`

1. **`_resolve_collisions()`** — delete the entire function. This is the post-movement push-apart loop (3 iterations over all unit pairs, overlap/2 displacement). RVO replaces it entirely.

2. **Soft separation steering** — the existing separation force in the fine-layer steering (steering weight currently 0.5, was 0.8 before 6J). Delete it. RVO subsumes this.

3. **Config flags to delete:**
   - `HARD_COLLISION_ENABLED`
   - `COLLISION_RESOLUTION_ITERATIONS`
   - Remove the `_resolve_collisions()` call at the end of `update_movement()`

## What to keep

- `UNIT_COLLISION_RADIUS` (15 wu) — becomes the agent radius for RVO
- `STEERING_SEPARATION_RADIUS` (30 wu) — can repurpose as RVO neighbor distance, or replace with new config
- `STEERING_OBSTACLE_AVOIDANCE_RANGE` (50 wu) — keep for navmesh obstacle avoidance (separate from inter-unit avoidance)
- `has_combat_los()` for terrain LOS — keep
- Navmesh, A* pathfinding, waypoint following — all keep. RVO operates on the fine-layer steering, not the coarse pathfinding.

## What to implement

### New function: `compute_rvo_velocities(store, active, dt)`

This runs once per tick, before position updates. For each active unit, it takes the unit's "preferred velocity" (what it wants to do) and returns an "adjusted velocity" (what it should actually do to avoid collisions with nearby friendly units).

**Per-unit logic each tick:**

```
For each active unit A:
    1. Compute preferred_velocity:
       - If A has a movement target (waypoint, command target):
           preferred_velocity = direction_to_target * A.speed
       - If A is holding position (no target, or target reached):
           preferred_velocity = (0, 0)
    
    2. Find neighbors:
       - All active units within RVO_NEIGHBOR_DIST of A, same layer
       - Use the existing spatial hash for efficiency
       - IMPORTANT: Include BOTH friendly AND enemy units as obstacles
         (units physically collide with everyone, not just friendlies)
    
    3. For each neighbor B, compute ORCA half-plane constraint:
       - relative_position = B.pos - A.pos
       - relative_velocity = A.vel - B.vel
       - combined_radius = UNIT_COLLISION_RADIUS * 2  (both agents have radius)
       - time_horizon = RVO_TIME_HORIZON
       - Compute the half-plane (line + direction) that A's velocity 
         must satisfy to avoid collision with B within time_horizon
    
    4. Solve linear program:
       - Find velocity closest to preferred_velocity that satisfies 
         ALL half-plane constraints
       - If infeasible (very dense packing): find the "safest" velocity
         that minimizes maximum constraint violation
    
    5. adjusted_velocity = LP solution
       - Clamp magnitude to A.max_speed
```

### Integration into `update_movement()`

Replace the current flow:
```
OLD:
  1. Compute direction to waypoint
  2. Apply steering behaviors (seek + separation + obstacle avoidance)
  3. Update position: pos += velocity * dt
  4. _resolve_collisions()  (push apart)

NEW:
  1. Compute preferred_velocity (direction to waypoint * speed)
  2. compute_rvo_velocities() adjusts preferred into collision-free velocity
  3. Apply navmesh obstacle avoidance on top (terrain only, not units)
  4. Update position: pos += adjusted_velocity * dt
  5. NO post-movement collision resolution needed
```

### Cross-faction collision

Both friendly and enemy units are RVO neighbors. A Raider closing on a Vanguard will steer *around* the Vanguard if there are other Vanguards in the way, but will still move *toward* its target. The preferred velocity points at the enemy; the RVO constraints prevent physical overlap. This is correct — units don't pass through each other but they don't stop trying to reach their target.

### Static obstacle handling

ORCA supports static obstacles as line segments. If the navmesh boundary data is accessible as line segments, feed them into the ORCA computation. Otherwise, keep the existing navmesh obstacle avoidance steering as a separate layer applied after RVO (check adjusted velocity against navmesh walkability, clamp if needed). The second approach is simpler and fine for our unit counts.

## New config parameters

```python
# ── RVO Local Steering ──────────────────────────────────────────
RVO_NEIGHBOR_DIST    = 200    # wu — how far each unit looks for neighbors to avoid
RVO_TIME_HORIZON     = 3.0    # seconds — how far ahead to predict collisions
RVO_MAX_NEIGHBORS    = 10     # max neighbors per unit per tick (performance cap)
# UNIT_COLLISION_RADIUS already exists at 15 wu — used as agent radius
```

**Tuning notes:**
- `RVO_NEIGHBOR_DIST` at 200 is close to Raider's weapon range — units start avoiding each other at roughly combat distance. Can increase if units still clump.
- `RVO_TIME_HORIZON` at 3.0 seconds means units plan ~60 ticks ahead. Higher = smoother avoidance, start earlier. Lower = more aggressive closing, later avoidance. 2-4 seconds is the typical game range.
- `RVO_MAX_NEIGHBORS` at 10 is fine for our unit counts. Even at 100v100, each unit only considers its 10 nearest neighbors.

## Determinism

RVO/ORCA is deterministic given the same inputs. Same positions, same preferred velocities, same neighbor set = same output velocities. This preserves the replay system. The linear program solver must use deterministic tie-breaking (no random choices). The reference implementations are deterministic.

## Test sequence

1. **Basic movement test** — 10 units, all moving to same point. Verify they converge without overlapping, form a cluster at the destination. No unit should pass through another.

2. **Two groups head-on** — 10 units moving east, 10 units moving west, on a collision course. Verify they flow around each other (the classic ORCA demo). Groups should interleave and pass through smoothly, not deadlock.

3. **Run `test_checkpoint_6b.py`** (or equivalent movement test) — verify speeds are correct, units reach destinations, no stacking.

4. **Run `test_6j_gradient.py`** — the real test. With RVO, Strike units should flow around the Line blob faster (higher speed = faster avoidance resolution), naturally forming a wider concave. T2 (wall-backed Line) should now show meaningful advantage over T1.

5. **Run `test_checkpoint_6d.py`** — engagement durations. RVO shouldn't change these much since it affects approach, not combat DPS. But verify.

6. **Run `test_checkpoint_6c.py`** — RPS directions still hold.

## Expected behavior changes

**Approach phase:** Units moving toward enemies will smoothly fan out as they approach friendlies in front of them, rather than stacking up and getting pushed apart. The approach should look like a wave spreading around obstacles.

**Combat phase:** Units in weapon range stop moving (preferred velocity = 0 since they're holding position to shoot). RVO keeps them separated in place. No more units jittering from post-hoc push-apart.

**Speed advantage:** Faster units resolve their avoidance constraints faster (they have more velocity budget to work with). A Raider at 150 speed has more room to steer laterally than a Vanguard at 80 speed. This naturally means Strike forms its concave faster than Line — which is exactly the bible behavior we want.

## If the rvo2 pip package doesn't work

Implement the core ORCA algorithm directly in `movement.py`. The essential functions are:

1. `_compute_orca_line(pos_a, vel_a, pos_b, vel_b, radius_a, radius_b, time_horizon)` — returns a half-plane constraint (point, direction) for agent A relative to agent B

2. `_solve_linear_program_2d(lines, preferred_vel, max_speed)` — finds the velocity closest to preferred_vel that satisfies all half-plane constraints, clamped to max_speed

3. `compute_rvo_velocities(store, active, dt)` — the per-tick driver that calls the above for each unit

Total: ~150-200 lines of numpy-vectorized Python. The math is 2D vector geometry — dot products, cross products, line-point distances. No complex dependencies.
