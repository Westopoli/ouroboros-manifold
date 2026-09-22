piece: B2 collisions (csrc/collision.c)
manager: M1

1. `algorithms.md` ALG-23 names `COLLISION_LOSER_TENSION_BASE` = 5.0 (the
   loser's per-collision tension hit, R-039-03: `Δt = 5.0 * commit/budget`
   on the loser's highest-military region). No `OM_COLLISION_LOSER_TENSION_BASE`
   (or equivalent) constant exists in `csrc/om_constants.h`'s ALG-23 block
   (only `OM_COLLISION_ECONOMY_CEILING`, `OM_COLLISION_ECONOMY_FLOOR`,
   `OM_COLLISION_NARROW_MARGIN`, `OM_COLLISION_NARROW_MIL_PENALTY`,
   `OM_COLLISION_RETENTION_MAX`, `OM_COLLISION_RETENTION_OPPOSITION_SCALE`
   are there). `alg_constants.py --lint` will flag a bare `5.0` in
   collision.c (no allowlist entry). Proposed fix: add
   `#define OM_COLLISION_LOSER_TENSION_BASE 5.0` under the ALG-23 comment.
