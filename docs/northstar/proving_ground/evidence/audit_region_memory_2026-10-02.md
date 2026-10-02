# Audit: memory per region by save slot (origin/main, 2026-10-02)

Method: sizeof of the real structs (om_internal.h directly; the file-static module states by #including each .c into a throwaway program), plus real save sizes from the release `libouroboros.so` built from a clean worktree off origin/main (`om_save_state_size`, and the per-slot `*_state_size` hooks read through om_internal.h). Scratch programs lived in the session scratchpad and are not committed. All numbers are bytes. OM_MAX_REGIONS = 512, OM_MAX_FACTIONS = 64, save format v5.

## Headline

- A save file is almost fixed-size: about 1.13 MB of fixed content plus about 1.6 KB per region. At 512 regions (pinned, ungenerated) it measured 1,953,281 bytes; a generated 400-region world measured 1,777,169 fresh and 1,788,847 after one 50-tick jump. The 512 by 512 edge matrix alone is 1,048,576 bytes, about 54 to 59 percent of every save, written in full regardless of the real region count.
- The save contains three things per region: the om_region record (1,601 bytes written plus 4 per neighbour), held_since (8) and previous_owner (4). The 64-entry damage history is 1,536 of the 1,601.
- The chronicle, the time-jump ownership timeline, keyframes and the mission/fog/tactical modules are NOT in the save (details below). So a loaded save has no timeline and no chronicle text (consistent with docs/architecture.md).
- In memory one world is about 1.62 MB embedded struct plus 975 KB of region records plus module states (generational 718 KB, events 131 KB, chronicle 105 KB, mission 100 KB, fog 13 KB), roughly 3.7 MB at 512 regions before any timeline or trace.

## Table 1: per region

"Per region" is bytes for one region id. "Total at 512" is the whole item at 512 regions. "Saved" says whether it is in the save file and which slot.

| Item | Bytes per region | Total at 512 | Where stored | Saved? |
|---|---|---|---|---|
| om_region record (`w->regions`, calloc n) | 1,904 (sizeof) | 974,848 | heap, om_world | yes, body: 1,601 + 4 per neighbour written (tier 1, faction 4, 6 doubles 48, n_neighbors 4, damage head/len 8, damage ring 64 x 24 = 1,536) |
| of which damage-history ring | 1,536 | 786,432 | inside om_region | yes, body |
| of which neighbours[32] (capacity) | 128 | 65,536 | inside om_region | yes, only the used count x 4 |
| region_held_since (int64, lazy malloc n) | 8 | 4,096 | heap | yes, body, only if allocated |
| region_previous_owner (int32, lazy malloc n) | 4 | 2,048 | heap | yes, body, only if allocated |
| Edge matrix `region_edge[512][512]` (om_edge_type, 4 B) | 2,048 (one row) | 1,048,576 | embedded in om_world | yes, body, all 512 x 512 written always |
| Per-tick logs sized 512: decisions 80, telegraphs 32, attacks 120, collisions 336, reinforces 56, colonizations 32, frictions 24, admin_rolls 40, lc_revolts 64, lc_reversions 40, lc_absorptions 24 | 848 (sum of record sizes) | 434,176 | embedded in om_world | no (per-tick scratch, except telegraphs, which are saved by used count only) |
| Faction/world fixed arrays, event_queue (3,584), rng_forced (32,768), pop history etc. | n/a | about 137,500 | embedded in om_world | yes, body (about 85 KB of the 1.13 MB fixed part) |
| om_world struct total | n/a | 1,620,256 (sizeof) | heap | n/a |
| Generational `regional_commander[512]` | 4 | 2,048 | gen_state | yes, slot 1 |
| Generational state, whole (characters 4,096, lineages 512, deaths, etc.) | n/a | 717,696 (sizeof) | heap via `generational_state` | slot 1, used prefix only: 0 bytes fresh, 10,642 after the first jump |
| Time-jump ownership snapshots `own_snap` | 4 per snapshot (104 for a 50-tick jump, 26 snapshots) | 53,248 for 50 ticks; 514,048 for a 500-tick jump (251 snapshots) | malloc in gen_state, freed and rebuilt each jump; count = ticks / OM_OWNERSHIP_TIMELINE_STRIDE (2) + 1 | no (memory only, by design) |
| Events state, whole | n/a | 131,120 (sizeof) | heap via `events_state` | slot 2, 0 until the events module is used, then 4,316 in my run |
| of which per-region tables (noise, breached, last_fired, faction_pending, applied_delta, touched) | 1,320 | 84,480 for the 64 regions it covers (not 512, see flag) | events state | yes (rows for min(n, 64) regions) |
| Mission state, whole | n/a | 100,224 (sizeof) | heap via `mission_state` | slot 3, hook installed only once a mission state exists; 0 in all my runs |
| of which `region_ctx[512]` (56 B each) | 56 | 28,672 | mission state | no references in the save writer (not saved, by reading mission.c; not exercised at runtime) |
| Chronicle state, whole | no per-region arrays | 105,432 (sizeof) | heap via `chronicle_state` | NO. `chronicle_state_size` is never assigned anywhere but region.c (NULL), so slot 5 is always empty |
| of which keyframes (up to 256 x 8) | none | 2,048 capacity | chronicle state | no, per jump |
| of which candidates/clusters/text entries/full scroll text (16,384) | none | bulk of the 105 KB | chronicle state | no |
| Fog state | none | 12,744 (sizeof) | heap | no hook assigned (slot empty) |
| Tactical, move, macro, support, mapgen states | none per region | not measured (outside region scope) | heap | no hook assigned in csrc outside region.c; slots always 0 bytes |
| Pipe diff mirrors (prev_owner, prev_mil, prev_econ, prev_ten, prev_pop, prev_stab, prev_cap) | 4 + 6 x 8 = 52 | 26,624 | om_pipe.c process heap | no |
| Trace rows (only when trace is on; grows without bound) | 232 per region per tick | 118,784 per tick | `w->trace` | no |

## Table 2: save file size, measured

| World | Save bytes | Notes |
|---|---|---|
| 512 regions, pinned, fresh (no generate) | 1,953,281 | 3,815 bytes per region averaged; 1,127,425 fixed + 1,613 x 512 |
| 512 regions pinned, after 100 ticks | 1,953,281 to 1,961,045 | small drift as queues fill |
| 512, after one 50-tick jump | 1,963,923 | +10,642 all in generational slot |
| 400, generated (50 factions, 447 edges), fresh | 1,777,169 | 4,443 per region averaged |
| 400, after one 50-tick jump | 1,788,847 | |
| 400, after a further 500-tick jump | 1,794,759 | events slot now 4,316 |
| 300, generated, fresh | 1,616,269 | slope 400 to 300 is 1,609 bytes per region; fixed part about 1.13 MB |
| 128, generated, fresh | 1,339,521 | |

Reading: the marginal cost is about 1,609 bytes per added region (the 1,601-byte record, 12 bytes of held_since and previous_owner, plus 4 per neighbour; the generated 400 world has 447 edges, about 2.2 neighbours per region). Everything else is fixed.

## Save slot contents (OM_SAVE_SLOT_*)

| Slot | Module | Saved bytes observed |
|---|---|---|
| body (before slots) | om_world core: regions, edges, factions, event_queue, telegraphs | about 1.95 MB at 512 |
| 0 tactical | none (hook NULL) | 0 |
| 1 generational | gen_state used prefix | 0 fresh, 10,642 after first jump |
| 2 events | events state | 0 until used, 4,316 observed |
| 3 mission | mission state | 0 observed |
| 4 fog | none | 0 |
| 5 chronicle | none (never wired) | 0 |
| 6 to 9 move, macro, support, mapgen | none | 0 |

## Flags and uncertainty

1. Events state is sized for only OM_EVT_MAX_REGIONS = 64 regions (csrc/events.c line 23) while OM_MAX_REGIONS is 512. Every events loop is bounded by `r < OM_EVT_MAX_REGIONS`, so on a 128 to 400 region galaxy events never touch regions 64 and above. Not a memory problem, but likely a behaviour bug against the 512 bump (HDR5). I did not test event firing; this is by reading. Needs an Architect ruling.
2. Peak and live process RSS were not measured. `mallinfo2` is useless here (big blocks come from mmap) and I did not add a profiler. The in-memory numbers above are sizeof sums, not RSS. The `ownership` timeline on the wire and the pipe's own JSON buffers are not counted.
3. Pinned 512 regions cannot be generated (the generator derives its count from templates; with 64 factions the ceiling is below 512), and E-03's draw range tops at 400. So a "512-region world" here is a pinned, ungenerated world with zero neighbours; its save is representative for the fixed cost but understates neighbour data by about 3.6 KB. The 400-region generated rows are the realistic ones.
4. Mission and tactical-slot sizes in a live mission were not measured. The mission hook only appears after a mission is set up; the tactical-family states have no save hooks at all, so a save taken mid-mission loses them (existing design: the architecture allows saves only between missions).
5. Slot framing overhead per slot (id plus length, about 5 bytes each) is included in the totals but not separated.
