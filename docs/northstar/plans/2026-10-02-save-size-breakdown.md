# Save-size breakdown by slot (INV-savesize)

Read-only investigation of test_scale_E02.py::test_e02_memory_per_region_under_256_bytes, which measures a marginal save-state cost of 1,601 B per region. Branch base: origin/push/HDR5 (e3b6de2d, OM_MAX_REGIONS 512, save version 5). Nothing here proposes a fix.

## Method

A scratch harness (not committed) copies csrc/save.c, inserts size marks into sv_write_body and sv_write_one_slot, and links it with the rest of csrc. It builds worlds with om_world_new(n, 2026091460) at n = 60, 250, 400 and 512 and reads each section's size from the size pass. The slot sizes are the real per-module size hooks. The sections sum exactly to om_save_state_size in every run, and fixture A reproduces the test's own totals (60 regions: 1,229,629 B; 512 regions: 1,953,281 B).

Fixtures: A is the test's world (all features off, DRIFT on, regions filled with fixed fields only). C is a generated world with all features on, 30 ticks stepped, then om_events_load_launch, two characters and 30 more ticks, so the lazily allocated events and generational slots are non-empty. C at n = 60 is not generated (generation fails below its feasibility floor at 60), so C is quoted from 250 up.

## Fixture A (the test's world), bytes per section

| Section | 60 | 250 | 400 | 512 | Growth |
|---|---|---|---|---|---|
| header (magic, version, tick, seed, rng, counts) | 56 | 56 | 56 | 56 | constant |
| rng_forced | 4 | 4 | 4 | 4 | constant |
| region fields (loop over live n_regions) | 96,060 | 400,250 | 640,400 | 819,712 | linear in n, 1,601 B per region |
| held_since / previous_owner (absent here) | 2 | 2 | 2 | 2 | constant when absent, 12 B per region when present |
| region_edge matrix | 1,048,576 | 1,048,576 | 1,048,576 | 1,048,576 | constant |
| features | 9 | 9 | 9 | 9 | constant |
| faction state (64 factions, fixed-size arrays) | 84,864 | 84,864 | 84,864 | 84,864 | constant |
| event_queue, telegraphs | 8 | 8 | 8 | 8 | constant (empty) |
| slots, 10 headers of 5 B each, all blobs empty | 50 | 50 | 50 | 50 | constant |
| Total | 1,229,629 | 1,533,819 | 1,773,969 | 1,953,281 | |

Marginal bytes per region between sizes: 60 to 250, 250 to 400 and 400 to 512 are all 1,601 B per region. The whole marginal is the region loop.

## What the 1,601 B per region is

Per region the writer emits tier (1), faction_id (4), six f64 fields (48), n_neighbors (4), damage_head and damage_len (8), then a full OM_DAMAGE_HISTORY_CAP (64) damage ring of tick u64 + military f64 + economy f64 = 24 B per entry, written for every slot whether used or not. That is 65 B of fields plus 1,536 B of damage ring (95.9 percent), plus 4 B per neighbor. The test world has no neighbors, so 1,601 B is the floor for a region.

## Slots (the ten slot blobs)

Only three modules assign a size hook in csrc on this branch: events (events.c), generational (generational.c) and mission (mission.c). The other seven slots (tactical, fog, chronicle, move, macro, support, mapgen) are never wired, so they are always an empty blob and cost their 5 B header. There is no separate region-history ring in a slot: the only history ring in the region path is the damage ring above, inside the core region section. The faction pop history ring (50 f64 per faction slot) is inside the 84,864 B faction section.

Fixture C slot sizes (bytes):

| Slot | 250 | 400 | 512 | Growth |
|---|---|---|---|---|
| generational (2 characters) | 10,894 | 10,894 | 10,894 | constant: regional_commander is sized by GEN_REGION_CAP (512), not n; 512 x 4 B of that is a fixed floor |
| events (launch library, 26 templates) | 36,288 | 36,364 | 36,440 | constant plus small drift: per-region noise, breached, last_fired and applied_delta tables are written for min(n, OM_EVT_MAX_REGIONS = 64) regions, so the cost stops growing at 64 regions; the drift is fired-event records |
| mission | 0 | 0 | 0 | constant: 16 B when a resolved result exists (band, region, fate, flags), 0 otherwise, including the new mission-result hooks |
| other seven | 0 | 0 | 0 | not wired |

Fixture C totals: 1,584,149 (250), 1,825,771 (400), 2,006,503 (512). Marginal per region: 250 to 400 is 1,610.8 B, 400 to 512 is 1,613.7 B. The excess over 1,601 B is held_since (8 B per region once allocated in a generated world) and a growing event_queue from the stepped world, not any slot.

## Top three by marginal bytes per region at 512

1. Region damage rings, 1,536 B per region (95.9 percent of 1,601).
2. Region scalar fields and counts, 65 B per region, plus 4 B per neighbor.
3. region_held_since 8 B and region_previous_owner 4 B per region, when allocated (zero in the test world). No slot contributes anything per region at 512.

## Quadratic question

The saved region_edge matrix is sized by the cap, not the live n: save.c loops a and b from 0 to OM_MAX_REGIONS and writes every cell, 512 x 512 x 4 B = 1,048,576 B regardless of n_regions. It is therefore constant in n and contributes 0 B to the marginal per region. It is quadratic only in the cap: it is 85.3 percent of the save at 60 regions, 53.7 percent at 512, and rises with the square of OM_MAX_REGIONS (before the HDR5 bump OM_MAX_REGIONS was 128, so the matrix was 65,536 B). The quadratic share of the marginal cost is zero; the quadratic share of the absolute save is 1,048,576 of 1,953,281 B at 512 (53.7 percent). The faction matrices are 64 x 64, also cap-sized and constant.

The test's marginal (size_big - size_small) / (n_big - n_small) therefore does not see the matrix at all; it sees only the linear region loop, dominated by the unconditional 64-entry damage ring.

Finding about the test itself: the test's big world is CONTROL_N_REGIONS = 600, above the 512 cap, and om_world_new now returns NULL above OM_MAX_REGIONS (region.c). Run on this branch, the test fails today at `assert w, "om_world_new returned NULL"` in _scale_helpers.raw_world, before it measures anything; it never reaches the memory assertion. The 1,601 B figure comes from measuring 60 against 512 (what this report did) or any pair under the cap, not from the test as written. This is reported only; nothing was edited.

## Open points

Fixture C at 60 regions was not generated and is omitted. The mission slot was not populated with a result in the harness (16 B by reading the size hook).
