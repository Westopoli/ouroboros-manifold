# Chronicle internals: ledger rows 7, 8, 9

Run: `chronicle_twin.py --seeds 1-5 --chapters 3` (15 jumps, output `/tmp/chr2`). Real candidate counts came from a scratch copy of `csrc/` in `/tmp/chr2/b` with a drop counter and a print before selection. The repo C is untouched. The pipe resolves `libouroboros_dbg.so` relative to its cwd, so the scratch run had to start in the scratch dir. `libouroboros_dbg.so` exposes no candidate count or debug counter (grep `n_candidates|OM_DEBUG` finds only `OM_DEBUG_INJECT` at `chronicle.c:2412`).

## Push order and the cap (`generational.c:1990-2118`, `chronicle.c:1588`)

1. During the jump loop, ownership changes are logged via `om_chronicle_add_ownership_change_event`. These are not candidates.
2. `om_chronicle_distill_candidates`.
3. Consequence: 1 candidate for the mission region, plus ripple candidates for adjacent regions that had an event.
4. Regional, per active region r in index order: `om_chronicle_add_event(r, peak)` (CTYPE_REGIONAL, `:1985`). Then, if the owner is unchanged and the category is growth or decline, a second `om_chronicle_add_regional_event`. That is up to 2 per region.
5. Chain clusters: `build_chain_clusters` pushes one per merged (region, category), at score 0.0 (`:1641`), up to 32 tags (`GEN_JUMP_CHAIN_CAP`).
6. Lineage: one per used lineage, score 0.0, pushed last (`generational.c` lineage loop, then `chron_push_lineage_candidate` `:1603`).
7. Padding for `OM_CHRONICLE_MIN_ENTRIES` (5).
8. `assemble` runs `chron_run_selection`. `chron_add_quiet_lineage_cluster` also pushes there.

The cap check is `chronicle.c:1590`: `if (n_candidates >= 256) return;`. A push past the cap returns void, increments nothing, logs nothing and leaves no counter. `om_chronicle_add_regional_event` (`:2496`) returns 0, but `generational.c` ignores it.

## Row 7: lineage entry dropped by the cap

| field | content |
|---|---|
| hypothesis | The lineage candidate is pushed after hundreds of regionals and silently dropped at 256. |
| evidence | Real counts at selection, 15 jumps. 14 of 15 hit n_cand = 256 exactly. The 15th (seed 1 ch 1) had 243 with the lineage candidate present, and it is the only jump with a family entry (ct1 = 1). Regional candidates were 249 to 256 in the capped jumps. Pushes dropped per jump: lineage 1 to 3 (14 of 14 capped jumps lost at least 1), chain 26 to 31, regional 5 to 133, consequence 0. Active regions (event or owner change) were 210 to 287 of 284 to 383 regions. In the uncapped jump they were 173, which is why my first upper-bound estimate (active regions only, mostly under 256) did not decide it: the second growth/decline push per region is what fills the pool. |
| verdict | **Confirmed.** |
| smallest fix | Push consequence, lineage and chain candidates before the regionals, or keep them in their own pools so the 256 cap applies to regionals only. |

## Row 8: chain clusters score 0.0 and sort last

| field | content |
|---|---|
| hypothesis | Chain clusters are pushed with `peak_score` 0.0 and the selector sorts them last. |
| evidence | `chronicle.c:1641`: `chron_push_candidate(st, CTYPE_CHAIN, groups[g].category, groups[g].region, 0.0, groups[g].tag, groups[g].lo, groups[g].hi)`. `groups[g].lo/hi` are set to 0 at `:1624` and never updated, so `start_tick` and `end_tick` are 0 too. The score is never computed from the chain's events. The raw chain events carry no score (`chron_raw_chain_event` has tag, region, category only). Selection sorts "others" by `peak_score` descending (`:1700`), so chains land after every scored regional. In practice the stronger cause is the cap: in 14 of 15 jumps all 26 to 31 chain pushes were dropped before selection (0 chain candidates survived). In the one uncapped jump, chain candidates survived but no chain entry reached the output: ct2 = 0 across all 144 entries. `generational.c` accumulates `chains[g].mil/eco/ten` but passes none of it as a score. |
| verdict | **Confirmed (two stacked causes: the cap drop, then the 0.0 score).** |
| smallest fix | Give chain clusters a score from their events (for example the max `om_chronicle_score_event` over the tag), and push them ahead of the regionals. |

## Row 9: blank shells

| field | content |
|---|---|
| hypothesis | `n_entries = n_clusters` while `entry_valid` is 0, and the pipe emits the shell. |
| evidence | `chronicle.c:1870`: `st->n_entries = st->n_clusters;` followed by `memset(entry_valid, 0)`. `entry_valid[i] = 1` is set only after the `ok[i]` check and the word-overlap dedup (`:1873-1896`). A cluster that is not ok, or is dropped as a duplicate, stays invalid. `om_chronicle_entry_count` returns `n_clusters` (`:2191`). `om_chronicle_get_cluster` does not check `entry_valid` (`:2280`). Pipe `om_pipe.c:929-946`: `for i < entry_count`, `if (!get_cluster) continue;`, then `if (entry_get(...)) {...}` with no else. The cluster is emitted anyway with an empty `text` and fragment ids -1. Nothing checks `entry_valid` on the pipe side. Count in this run: 30 blank entries of 144 across 15 jumps, matching the summary (blank_entries = 30). The probe's `blank_text` class shows 14 jumps with a blank entry. Only seed 4 ch 2 had none. I did not separate not-ok from dedup as the cause. |
| verdict | **Confirmed** (mechanism and count). |
| smallest fix | Skip clusters with no valid entry in the pipe emit loop, or compact `clusters[]` to the valid entries before `n_entries` is set. |
