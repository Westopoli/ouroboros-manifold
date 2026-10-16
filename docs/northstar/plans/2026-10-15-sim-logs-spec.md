# SIM-LOGS: the jump-window logs (spec, rev 1, 2026-10-15)

**Status: drafted by the Architect from the 2026-10-15 pre-flight scout (read-only; every line on `origin/main` at `6a0673a4`); Sonnet audit next; Westley's go on the three rulings below; builds after LAB-REV2-E0 and CONTRACT-cone-state on the Linux box. Not launched.**

## Why

Sim lane ledger rows 3, 5, 6, 11, 12 (`sim_lane_2026-10-12/README.md`): the C port reads 0 where the reference read a log. `csrc/mission.c:509-511`: "the C ABI has no event/conquest log, so this reads the live region graph and faction stance only." Westley, 2026-10-15: "go" on SIM-LOGS, then the call sites, then `chronicle.c`'s own bugs.

What the reference did (`simulation/`, scout 2026-10-15): three plain lists filled by the harness for the whole run, never windowed, capped or cleared: attacks `{faction_id, action, target_region, budget_committed, tick}` appended when an attack *resolved* (`tick.py:153-165`, `:205-210`); events `{template_id, name, region_id, tick, field_deltas, chain_tag, ...}` (`events.py:582-595`); conquests `{region_id, new_faction_id, old_faction_id, garrison, tick}` (`intent_resolver.py:208-213`). Readers filtered by region and faction only (`mission_generator.py:37-73`). `chain_length` was never set (dead in the reference); `times_run` was incremented only by the harness (`test_checkpoint_g5.py:641`).

## Rulings needed from Westley before launch

- **W1 window and cap.** The reference kept everything. Draft: each log is a ring buffer, oldest overwritten, caps `DRAFT-log-attacks` 4,096, `DRAFT-log-conquests` 1,024, `DRAFT-log-events` 4,096 entries; readers take every entry since the campaign began that the ring still holds, filtered by region and faction as the Python did; nothing is cleared at a mission start. A 50-tick jump at 400 regions writes about 600 attacks and 1,100 events (sweep of 2026-10-15: 12,327 attacks and 22,683 events over 25 jumps), so a ring of 4,096 holds the last three to six jumps. (a) the draft; (b) window = the last jump only (cleared at each jump start); (c) other caps.
- **W2 the Defensive Stand trigger.** The reference let Defensive Stand into the pool only when the attack log held an attack on the region by a non-player faction (`mission_generator.py:81-96`); the C arm adds "or any hostile neighbour" (`mission.c:558-561`), and `tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py:60-100` pins that OR. (a) drop the OR, as the reference and E-10 R-073-01; the test is ruled a test-defect (`TD-SIM-1`) and rewritten to put an attack in the log; (b) keep the OR and give an unattacked stand the R-074-01 "otherwise" power so it composes. The Architect's lean is (a): the sim's "highly active regions" come from urgency (which the chain and attack terms now feed), not from a trigger that admits empty missions.
- **W3 chain length.** (a) parity: stays 0 as the reference's effective behaviour; (b) filled: an event's `chain_length` is the count of fired events sharing its `chain_tag` so far in the ring (what ALG-50's `0.1 × min(len, 5)` was written for; `generational.c:2002-2030` already counts chains per jump). Lean (b): the rule exists and the data is one lookup.

## The piece (contract-level; second-Fable audit before the build)

**Files.** New `csrc/simlog.c`, `csrc/simlog_internal.h`; `csrc/om_internal.h` (the store on `om_world`, pattern (a) as `om_economy_state`); `csrc/ouroboros_sim.h` and `docs/northstar/spec_factory/signatures.toml` (accessors, ABI bump); `csrc/save.c`, `csrc/checksum_full.c` (the block, `OM_SAVE_FORMAT_VERSION` next free at landing); `csrc/resolve.c` (two appends and the `previous_owner` fix); `csrc/events.c` (one append); `csrc/mission.c` (`om_mission_refresh_context` reads the logs; the trigger arm under W2; `times_run`); `csrc/chronicle.c:1669-1672` and `csrc/generational.c:2081` (the flags); `docs/architecture.md`; tests below. Owner `SIM-LOGS`; depends on LAB-REV2-E0 and CONTRACT-cone-state (save and ABI bumps, next free at landing), and is ordered with VG-CONTRACT-E7, VG-E-prodslot and VG-E-startforce on `mission.c` by the Dispatcher (one owner at a time).

**State** (`simlog_internal.h`, included by `om_internal.h`):
```c
typedef struct om_log_attack   { int64_t tick; int32_t attacker, target_region; double commit; int32_t conquest; } om_log_attack;   /* 32 B */
typedef struct om_log_conquest { int64_t tick; int32_t region, old_faction, new_faction; int32_t by_attack; } om_log_conquest;  /* 24 B; by_attack 1 from resolve, 0 from lifecycle */
typedef struct om_log_event    { int64_t tick; int32_t region, template_id; uint32_t chain_tag; int32_t chain_length; } om_log_event;  /* 24 B; chain_length per W3 */
#define OM_LOG_ATTACK_CAP 4096   /* DRAFT-log-attacks */
#define OM_LOG_CONQUEST_CAP 1024 /* DRAFT-log-conquests */
#define OM_LOG_EVENT_CAP 4096    /* DRAFT-log-events */
typedef struct om_simlog_state {
    uint32_t attack_head, attack_n;     om_log_attack   attacks[OM_LOG_ATTACK_CAP];
    uint32_t conquest_head, conquest_n; om_log_conquest conquests[OM_LOG_CONQUEST_CAP];
    uint32_t event_head, event_n;       om_log_event    events[OM_LOG_EVENT_CAP];
    uint16_t times_run[OM_MAX_LINEAGES][OM_ARCHETYPE_COUNT];   /* per lineage per archetype, incremented at mission_end; OM_MAX_LINEAGES and OM_ARCHETYPE_COUNT are the existing constants (the test writer names their lines) */
} om_simlog_state;   /* about 280 KB */
```
Ring rule: `head` is the next write slot, `n` saturates at the cap; iteration oldest to newest is `i = (head - n + k) mod cap`. No heap, no hash order, no wall clock.

**Appends** (the only writers, all in `simlog.c`, called from the sites named):
- `om_simlog_attack(w, tick, attacker, target, commit, conquest)` from `resolve.c` where `w->attacks[]` is filled for a resolved attack (the record site that feeds `om_tick_attacks`, `resolve.c:40-160`), and from `diplomacy.c:264-284` (a betrayal is an attack). One entry per resolved attack, as the reference logged resolved not declared attacks.
- `om_simlog_conquest(w, tick, region, old, new, by_attack)` from `resolve.c:479` (by_attack 1) and from `lifecycle.c:196, 238, 320` (by_attack 0). **`resolve.c:479` also gains `om_region_set_previous_owner(w, target, old)` before `om_region_set_owner`** (the C bug the scout found: attack conquests never set `previous_owner`; the reference's conquest log carried `old_faction_id`).
- `om_simlog_event(w, tick, region, template, chain_tag)` from the `fired[]` fill in `events.c:615`; `chain_length` per W3.
- `times_run[lineage][archetype] += 1` in the `mission_end` path (`om_pipe.c` handler or `mission.c`'s end function, the test writer names the line), for the lineage seated at the time.

**Readers** (replace the substitutes; `om_mission_refresh_context`, `mission.c:2201+`):
- `recent_attacks` and the committed budget for a region: attacks with `target_region == r` and `attacker != player`, as `mission_generator.py:81-96`; the conflict term of urgency `min(1, n·0.5 + Σcommit/600)` as `mission_generator.py:321-324` (`OM_MISSION_*` constants already carry 0.5 and 600 per the scout; the test writer confirms).
- Defensive Stand arm per W2; Multi-Front and Interception read the same count (`:595-607`), no neighbour OR.
- `adjacent_lost`: conquests with `old_faction == owner` and `region` among r's neighbours (`mission_generator.py:329-332`), replacing the `previous_owner` walk at `:2216-2224`; Reconquest: a conquest with `region == r` and `old_faction == player` (`:121-132`), replacing `:564-566`; Containment counts conquests with `new_faction == region.faction` (`:252-271`).
- `recent_revolt_events`: events with `region == r` and `template_id` in the revolt set (the eight ids of `mission_generator.py:10-14`; the C set the test writer finds beside `om_mission_set_revolt_events`, `mission.c:2184`, today never called).
- `times_run` passed at `mission.c:2261` from the store for the seated lineage.
- `chronicle.c:1671`: `chron_context_multiplier(in_mission_region, has_character, chain_length, has_lineage)` with the first from the event's region against the last mission region, the second from the event's character id when the event record carries one (else 0, as today), the third per W3.
- `generational.c:2081`: `has_conquest_or_revolt` = the region has a conquest or a revolt event in the log over the jump's ticks.

**Accessors** (`ouroboros_sim.h`, `signatures.toml`, one row each): `uint32_t om_simlog_attack_count(const om_world*)`, `int om_simlog_attack_get_at(const om_world*, uint32_t i, om_log_attack *out)` (0 ok, 1 bad index or NULL), and the same pair for conquests and events; `uint32_t om_simlog_times_run(const om_world*, int32_t lineage, int32_t archetype)`. The pipe gains nothing in this piece (the sim viewer's pool fields are an SV piece).

**Save and hash.** Appended as its own block after the economy block (`save.c:459`, `checksum_full.c:454`): the three `head, n` pairs, then `n` entries each oldest to newest (so a ring's physical layout never leaks into the hash), then `times_run` row-major. Load rejects `n` above its cap, a `head` at or above its cap, a region or faction index out of range. `OM_SAVE_FORMAT_VERSION` takes the next free number at landing (after E0 and cone-state); the pins that move (`OM_PIPE_SAVE_FORMAT_VERSION`, `load_game.gd`, `test_load_game_wrong_version.gd`, `test_E16_B5/C2_save_version.py`, `test_VG_E_ke3.py`, `test_PP_portability.py` `PINNED_FULL`) go under one row `TD-SIM-2` with this spec as the ruling. The world checksum changes, so every world-level hash pin re-records under the same row (the test writer lists them from a run on the built tree).

**Tests** (test writer, a different agent than the builder; red on the built tree because the symbols are missing): `tests/csim/test_SIM_logs_ring.py` (append past the cap keeps the newest, iteration order, determinism across two processes, save round trip byte-identical, load rejections); `test_SIM_logs_appends.py` (one resolved attack → one entry with its commit; a conquest by attack → an entry with `by_attack` 1 and `previous_owner` set; a lifecycle revolt → `by_attack` 0; a fired event → an entry with its template and tag; `times_run` rises by one at `mission_end` for the seated lineage only); `test_SIM_logs_readers.py` (R-073-01: a region with a hostile neighbour and no attack does **not** enter the pool as Defensive Stand and one with a logged attack does, under W2 (a); Reconquest enters after a logged attack conquest of the player's region; adjacent-lost counts a neighbour's logged loss; the urgency chain term is 0.3 per revolt event, capped; `times_run` lowers fit as ALG-55 states); `test_SIM_logs_chronicle.py` (the context multiplier reads the mission-region term; the faction-shift classifier gets the flag for a region with a logged conquest). Positive controls: a ring whose `head` is corrupted fails the load check; a build with the append at `resolve.c` removed fails the attack-reader test; the existing `test_E10_S072_a2_refresh_telegraph_defensive_stand.py` stays green (telegraphs still raise the conflict term). Re-pinned: `test_E10_S072_orders_come_from_where_the_world_hurts.py:60-100` under `TD-SIM-1` (W2 (a)); `test_E10_S072_a2_refresh_lost_quiet_lineage.py:34-48` (adjacent-lost now from the log; the test logs a conquest instead of calling `om_region_set_previous_owner`), same row.

**Acceptance.** The mission-choice sweep (`sim_lane_2026-10-12/finding_mission_choice.md` method) re-run on the built tree: 0 swapped missions in 100; Reconquest and Counterinsurgency appear in at least one pool; the chain term is non-zero in some rows; Q-072-02's row re-measured (expected to close on (a)). The chronicle sweep: the faction-shift class appears for regions that changed hands.

## Not in this piece

The `chronicle.c` bugs (family entry dropped past `CHRON_MAX_CANDIDATES`, chain clusters at score 0, blank shells on the pipe): rows 7 to 9, their own pieces after this one. The pipe's candidate-pool fields (SV). The opening-jump relevance order (row 4). Ripple and repeat rules (rows 10, 13, Westley's).
