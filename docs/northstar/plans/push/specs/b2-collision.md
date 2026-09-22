# B2 collisions — csrc/collision.c

## Summary

E-05 S-039 multi-faction collision resolution: when two or more factions'
intents target the same region in one tick, resolve who wins, how much the
winner retains, what the losers pay, and (for an empty target) how strong
the new colony starts. Skeleton in `csrc/collision.c` (2 STUB functions).
Runs between `om_step_reinforce` (3e) and `om_step_resolve` (3f) — sim.c's
wiring already calls `om_step_collisions` there (F2 freeze; do not touch
sim.c). `om_step_collisions` groups `w->decisions[]` by target, resolves
every target with 2+ colliding intents (ALG-23/24), writes
`w->collisions[]`/`w->collisions_n`, and removes the colliding intents from
`w->decisions[]` so `om_step_resolve` never double-resolves them.

## Bible Compliance

- **Bible path:** `docs/bible/epics/E-05-faction-agents-and-conflict.md`
- **Sections referenced:** S-039 (R-039-01, R-039-02, R-039-03, R-039-04,
  R-039-06 — **R-039-05 excluded**, open flag Q-039-01, B5b follow-up).
- **Deliberate divergences:** none.

## Acceptance criteria

`tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py` (5 of 6
tests; `test_R_039_05*` skipped under Q-039-01) + `tests/csim/test_E05_S039_wiring.py`
(2 tests) = 7 node ids:

1. **R-039-01** — `algorithms.md` ALG-23, verbatim: for each colliding
   intent i of faction f, `eco_f = sum(economy of f's owned regions)`,
   `max_eco = max(eco_f over all colliders)` (1 if every collider's eco_f is
   0), `factor_i = OM_COLLISION_ECONOMY_FLOOR + (OM_COLLISION_ECONOMY_CEILING
   - OM_COLLISION_ECONOMY_FLOOR) * eco_f / max_eco` (0.4 + 0.6*eco_f/max_eco).
   `strength_i = commit_i * OM_ATTACK_EFFICIENCY * factor_i * tech_attack(f) *
   surprise_i`. Two factions commit 40/20, economies 200/100:
   `factor_0 = 0.4+0.6*200/200 = 1.0`, `factor_1 = 0.4+0.6*100/200 = 0.7`,
   `strength = 40, 14`. Winner drawn once with probability
   `strength_i / sum(strength)` (equal shares if the sum is 0) — 40/54 for
   collider 0 in this fixture.
2. **R-039-02** — `second = max(loser strengths)`; `margin = winner /
   (winner + second)`; `opp = sum(loser strengths) / winner` = 14/40 = 0.35;
   `ret_ceiling = OM_COLLISION_RETENTION_MAX * max(0, 1 - opp *
   OM_COLLISION_RETENTION_OPPOSITION_SCALE)` = 0.4*(1-0.35*0.6) = 0.316;
   `refund = winner_commit * U(0, ret_ceiling)` (one draw); winner spends
   `commit - refund`; every loser spends its full commit (no refund).
3. **R-039-03** — each loser's tension hit lands on its own highest-military
   region: `Δtension = OM_COLLISION_LOSER_TENSION_BASE * commit /
   faction_budget_at_commit_time` (base 5.0 — **not yet a named constant**,
   see NEEDS-HEADER item 1); budget 50, commit 20 -> 2.0 tension.
4. **R-039-04** — target unowned: winner colonizes per ALG-24
   (`OM_COLONY_START_MILITARY` 10.0 flat, `OM_COLONY_START_ECONOMY` 20.0,
   `OM_COLONY_START_TENSION` 20.0, `OM_COLONY_START_POPULATION` 25.0),
   except starter military is `OM_COLONY_START_MILITARY * U(OM_COLLISION_NARROW_MIL_PENALTY,
   0.70)` (0.5 to 0.70, one draw) when `margin < OM_COLLISION_NARROW_MARGIN`
   (0.6). margin 40/54 = 0.741 >= 0.6: flat 10.0. margin 0.55 < 0.6: drawn.
   The `0.70` upper bound has no named constant either (ALG-23 states it as
   a literal range end alongside the named `COLLISION_NARROW_MIL_PENALTY`
   floor) — same NEEDS-HEADER item 1 covers it, or treat `0.70` as the kind
   of magic-number-paired-with-a-named-floor the lint's existing allowlist
   mechanism is for; escalate rather than silently hardcode.
5. **R-039-06** — three or more colliders: identical weighted-draw and
   retention math; `second` and `opp` are computed the same way (max/sum
   over every loser, however many there are) — nothing here is a special
   case of the two-collider math, it already generalizes.
6. **Wiring** — `om_step_collisions` runs, and (control)
   `OM_BUG_COLLISION_AFTER_RESOLVE` (112) makes it run after
   `om_step_resolve` instead of before — sim.c's job to wire the branch, not
   this piece's; the wiring test only proves the call happens in the
   already-landed order.

## Contract (csrc/ouroboros_sim.h, unchanged)

- `om_collision` struct (`OM_MAX_COLLIDERS` 8): `tick`, `target_idx`,
  `n_colliders`, `faction[8]`, `commit[8]`, `economy_factor[8]`,
  `strength[8]`, `winner`, `margin`, `retention_ceiling`, `refund`,
  `loser_tension[8]`.
- `uint32_t om_tick_collisions(const om_world *w, om_collision *out, uint32_t max);`
- `void om_step_collisions(om_world *w);` (declared in `om_internal.h`,
  already wired into `sim.c`'s tick loop between 3e and 3f).
- Reads `w->decisions[]` / `w->decisions_n` (`om_decision`, declared
  elsewhere in the E-05 block — grep `ouroboros_sim.h` for `om_decision`)
  and `w->faction_budget[]`; writes `w->collisions[]` / `w->collisions_n`
  and mutates `w->decisions[]`/`w->decisions_n` to remove resolved entries.

## Controls (tests/csim/controls/, 1 file this piece owns)

`test_control_e05_collision_max_strength.py` — `OM_BUG_COLLISION_MAX_STRENGTH`
(104): winner must be a weighted draw on `strength[i]/sum`, not
`argmax(strength)`. Plant under `#ifdef OM_DEBUG_INJECT`, `w->inject ==
OM_BUG_COLLISION_MAX_STRENGTH`.

`test_control_e05_collision_after_resolve_trips_the_detector` (in
`test_E05_S039_wiring.py`, `OM_BUG_COLLISION_AFTER_RESOLVE` = 112) is a
sim.c tick-order control, not a branch this piece plants.

`tech_attack(f)` is `w->faction_tech_attack[f]`; `surprise_i` is 0.5 in
surprise mode else 1.0, same pattern as `csrc/resolve.c:374-382`'s
`surprise_mult` — mirror that file's reads, do not invent a different
field or a different surprise-mode test.

## Determinism

Exactly one weighted draw for the winner (R-039-01), one draw for the
refund fraction (R-039-02), and (narrow-margin colonize path) one draw for
starter military (R-039-04) — same RNG-draw contract `csrc/friction.c` and
`csrc/agent.c` already use. No extra draws, no draws skipped: `force_draws`
fixtures in the acceptance tests pin an exact draw sequence and will fail on
an off-by-one draw count.

## Out of scope

- R-039-05 (owned-target collision with post-damage conquest) — Q-039-01
  open, B5b follow-up piece.
- `csrc/ouroboros_sim.h`, `csrc/om_internal.h`, `csrc/om_constants.h`,
  `csrc/sim.c` (parent-owned; if a constant is missing, NEEDS-HEADER, never
  a hardcoded literal).
