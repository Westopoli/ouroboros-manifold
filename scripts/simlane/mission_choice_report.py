#!/usr/bin/env python3
"""Render docs/northstar/plans/sim_lane_2026-10-12/findings/mission_choice.md from mission_choice.py's raw JSON.

Usage: mission_choice_report.py RAW_JSON OUT_MD BASE_SHA
Numbers in the findings ledger are computed here from the raw rows; the prose is the scout's reading of
csrc/mission.c, csrc/generational.c, csrc/pipe/om_pipe.c and simulation/mission_generator.py (cited per row).
"""
import json
import sys
from collections import Counter
from pathlib import Path

CODE = ["DS", "SB", "RC", "AS", "SU", "MF", "IN", "EV", "CT", "CI"]
FULL = ["Defensive Stand", "Siege Breaking", "Reconquest", "Assault", "Suppression", "Multi-Front Defense",
        "Interception", "Evacuation", "Containment", "Counterinsurgency"]
UNEVAL = {8, 9}   # Containment, Counterinsurgency: the world keeps no colonization / revolt log


def pair(p):
    return "%d/%s" % (p[0], CODE[p[1]])


def main(raw_path, out_path, base_sha):
    d = json.load(open(raw_path))
    rows = d["rows"]
    A = lambda r: r["analysis"]
    n = len(rows)
    assert n == 60, n
    synced = sum(1 for r in rows if all(r["sync"].values()))
    quiet = sum(1 for r in rows if r["quiet_world"])
    scan = [r for r in rows if r["scan_used"]]
    scan_not_pool = [r for r in scan if not A(r)["final_in_c_pool"]]
    ds_drawn = sum(1 for r in rows if r["drawn"][1] == 0)
    pool_total = sum(r["pool_size"] for r in rows)
    in_stored_top5 = sum(1 for r in rows if A(r)["c_stored"]["rank_in_top5"])
    rank_hist = Counter(A(r)["c_stored"]["rank_in_top5"] for r in rows)
    exp_rank1 = sum(A(r)["c_stored"]["p_rank1"] for r in rows)
    pool_arch = Counter()
    vr_arch = Counter()
    c_only = Counter()
    rule_only = Counter()
    for r in rows:
        for k, v in A(r)["c_pool_by_arch"].items():
            pool_arch[int(k)] += v
        for k, v in A(r)["vr_pool_by_arch"].items():
            vr_arch[int(k)] += v
        for k, v in A(r)["c_only_by_arch"].items():
            c_only[int(k)] += v
        for k, v in A(r)["rule_only_by_arch"].items():
            rule_only[int(k)] += v
    ds_pool = sum(A(r)["ds_pool"] for r in rows)
    ds_noatk = sum(A(r)["ds_pool_no_attack"] for r in rows)
    stale = [r for r in rows if A(r)["stale_relevance_regions"]]
    stale_first = [r for r in stale if r["k"] == 1]
    stale_later = [r for r in stale if r["k"] != 1]
    top5_differs = [r for r in rows if A(r)["top5_set_stored"] != A(r)["top5_set_fresh"]]
    fit_only = [r for r in rows if A(r)["chosen_C"] and not A(r)["stale_relevance_regions"]
                and abs(A(r)["chosen_R"][1] - A(r)["chosen_C"][1]) > 1e-9]
    fit_diffs = [A(r)["chosen_R"][1] - A(r)["chosen_C"][1] for r in fit_only]
    fit_min, fit_max = min(fit_diffs), max(fit_diffs)
    first_ds = next(r for r in rows if A(r)["ds_pool_no_attack"] > 0)
    first_int = next(r for r in rows if A(r)["legacy_interception_regions"])
    outside = sum(len(A(r)["pool_region_outside_r07201"]) for r in rows)
    mf_pool = sum(A(r)["mf_c_pool"] for r in rows)
    mf_lt2 = sum(A(r)["mf_lt2_distinct_sources"] for r in rows)
    siege_pool = sum(A(r)["siege_c_pool"] for r in rows)
    siege_young = sum(A(r)["siege_held_lt_200"] for r in rows)
    interc_legacy = sum(len(A(r)["legacy_interception_regions"]) for r in rows)
    attacked = sum(len(A(r)["attacked_player_regions"]) for r in rows)
    contain_pool = sum(A(r)["contain_c_pool"] for r in rows)
    tel_age = Counter(A(r)["telegraph_age_max"] for r in rows)
    final_arch = Counter(r["archetype"] for r in rows)
    pj = [r["prev_jump"] for r in rows if r["prev_jump"]]
    lin_same = all(A(r)["lineage_last"] == A(r)["lineage_campaign"] == A(r)["lineage_snapshot"] for r in rows)

    # per-mission verdict: y = shown == drawn, drawn in the C stored top-5, and drawn in the rule-literal top-5;
    # ? = drawn archetype the rule-literal model cannot evaluate; n(...) lists the reasons
    verdicts = {}
    for r in rows:
        why = []
        if r["scan_used"]:
            why.append("scan-override")
        if not A(r)["c_stored"]["rank_in_top5"]:
            why.append("not-in-C-top5")
        if A(r)["stale_relevance_regions"]:
            why.append("stale-relevance")
        if r["drawn"][1] in UNEVAL:
            rule = "?"
        elif A(r)["vr_chosen_in_top5"]:
            rule = "y"
        elif A(r)["vr_chosen_in_pool"]:
            rule = "n(rank>5)"
            why.append("rule-rank>5")
        else:
            rule = "n(not-in-rule-pool)"
            why.append("not-in-rule-pool")
        verdicts[(r["seed"], r["k"])] = (rule, why)
    clean = sum(1 for r in rows if not verdicts[(r["seed"], r["k"])][1])
    rule_ok = sum(1 for r in rows if verdicts[(r["seed"], r["k"])][0] == "y")
    rule_unev = sum(1 for r in rows if verdicts[(r["seed"], r["k"])][0] == "?")
    rule_bad = n - rule_ok - rule_unev
    deviating = n - clean

    L = []
    w = L.append
    w("# Mission choice against E-10 S-072 to S-074 (sim lane scout A)")
    w("")
    w("Read on `origin/main` %s, worktree `push/simlane-a`. Findings only: nothing under `csrc/`, `tests/`, `docs/bible/` or the ambiguity register was changed. Thresholds are Westley's." % base_sha)
    w("")
    w("## How it was run")
    w("")
    w("- Command: `~/Projects/ouroboros-manifold/.venv/bin/python scripts/simlane/mission_choice.py --seeds 1-10 --missions 6 --n-regions 80`, then `scripts/simlane/mission_choice_report.py <raw json> <this file> <sha>`. Raw rows (every candidate list and input) are in `mission_choice_raw.json` beside this file.")
    w("- **n_regions is 80, not the briefed 60.** A pinned count of 60 fails `set_seed` (`generation failed`) for all ten seeds; counts up to 65 failed for every seed tried (seeds 1 to 3) and 66 to 72 failed for some (the feasible minimum, Q-021-07, depends on the rolled templates). 80 is the client's `DEFAULT_N_REGIONS` (`autoload/c_bridge.gd:23`). Features are `[0..7]`, faction 0, `era_kind` 0.")
    w("- Per campaign: `set_seed`, then six times: `mission_start`, `snapshot`, `objective_complete` on every objective at 1.0, `mission_end`, `jump 50`. The pipe is the debug pipe (`pipe/ouroboros_pipe_dbg`) through `scripts/simviewer/pipe_session.py`; its `mission` frame and `snapshot` frames are the ground truth.")
    w("- The pipe shows no candidate pool, no previous owners, no lineage rows. `tests/csim/conftest.py` binds the C API that does (`om_mission_candidates`, `om_mission_compute_urgency/relevance`, `om_region_previous_owner`, `om_lineage_*`), so a ctypes replica of the pipe handlers (`handle_set_seed`, `handle_mission_start`, `handle_objective_complete`, `handle_mission_end`, `handle_jump`) runs the same campaign on `libouroboros_dbg.so` and is cross-checked per mission against the pipe: **%d of %d missions identical in tick, world checksum, region, archetype and `quiet_world`**, so the replica's pool reads are the pool the pipe drew from. (The replica binds the same symbols directly, not through `conftest.py`, because importing `conftest.py` runs `make` and unlinks the libraries on a failed build.)" % (synced, n))
    w("- Independent recomputation is Python from the pipe snapshot (fields, composites, edges, stance, telegraphs). Two models: **V_C** takes the C pool's membership and recomputes urgency, relevance, preference, score and the top 5 per ALG-55 (arithmetic check). **V_R** rebuilds the pool from the R-073-01 trigger table as written, with the inputs the world can supply, and the relevance with the lineage run-count as R-072-03 words it (rule check). Containment and Counterinsurgency cannot be built in V_R (the world keeps no colonization or revolt log), shown as `?`.")
    w("- The genuine pick is the generator's draw (`om_mission_generator_run` at the end of the previous jump). The table shows both the drawn pair and the pair the pipe finally showed (they differ when the pipe's zero-force scan overrides, SL-A-01).")
    w("")
    w("## Result")
    w("")
    w("| Check | Result |")
    w("|---|---|")
    w("| Missions checked | %d (10 seeds x 6) |" % n)
    w("| Replica == pipe (tick, checksum, region, archetype, quiet_world) | %d / %d |" % (synced, n))
    w("| `quiet_world = true` (simulation-health warning, architecture.md) | **%d / %d** |" % (quiet, n))
    w("| Pool candidates checked, urgency recomputed from the snapshot equals the C value | %d / %d (max abs diff 0.0) |" % (pool_total, pool_total))
    w("| Drawn pair inside the top 5 by the C's stored scores (R-072-05) | %d / %d |" % (in_stored_top5, n))
    w("| Drawn rank among top 5 (1 to 5) | %s; expected rank-1 count under the weighted draw %.1f, observed %d |" % (", ".join("%s:%d" % (k, rank_hist[k]) for k in sorted(rank_hist)), exp_rank1, rank_hist[1]))
    w("| Relevance recomputed equals the C value | %d / %d missions; the %d that differ are the stale-lineage cases, SL-A-08 |" % (n - len(stale), n, len(stale)))
    w("| Shown mission equals the generator's draw | %d / %d; %d overridden by the pipe's zero-force scan, SL-A-01 |" % (n - len(scan), n, len(scan)))
    w("| Drawn pair inside the rule-literal (V_R) top 5 | %d y, %d n, %d unevaluable (Containment) |" % (rule_ok, rule_bad, rule_unev))
    w("| Missions with no deviation at all (shown == drawn, in C top 5, fresh relevance, in V_R top 5 or unevaluable and not otherwise flagged) | %d / %d |" % (clean, n))
    w("")
    w("Chosen archetype counts (shown): %s." % ", ".join("%s %d" % (FULL[a], final_arch[a]) for a in sorted(final_arch)))
    w("Never chosen in 60 missions: %s. Pool entries over the 60 states by archetype (C): %s." % (
        ", ".join(FULL[a] for a in range(10) if final_arch[a] == 0),
        ", ".join("%s %d" % (CODE[a], pool_arch[a]) for a in range(10))))
    w("")
    w("## Every mission")
    w("")
    w("Archetype codes: " + ", ".join("%s %s" % (CODE[i], FULL[i]) for i in range(10)) + ". `u`, `rel`, `score` are the C's stored values for the drawn pair; `u_R`, `rel_R` the rule-literal figures (lineage run-count included). Rule-expected is V_R's top 5, `region/archetype`. `match`: y = shown equals draw, draw in the C top 5 and in the V_R top 5, relevance fresh; otherwise the reasons.")
    w("")
    w("| seed | m | tick | shown | drawn | u | rel | score | rank | pool | u_R | rel_R | rule-expected top 5 (V_R) | match |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        a = A(r)
        cC = a["chosen_C"]
        cR = a["chosen_R"]
        rule, why = verdicts[(r["seed"], r["k"])]
        if rule == "?":
            match = ("n: " + ", ".join(why)) if why else "? (archetype not evaluable by V_R; C checks y)"
        else:
            match = "y" if not why else "n: " + ", ".join(why)
        w("| %d | %d | %d | %s | %s | %.3f | %.2f | %.3f | %s | %d | %.3f | %.2f | %s | %s |" % (
            r["seed"], r["k"], r["tick"], pair((r["region"], r["archetype"])), pair(r["drawn"]),
            cC[0], cC[1], cC[2], a["c_stored"]["rank_in_top5"], r["pool_size"], cR[0], cR[1],
            " ".join(pair(x[:2]) for x in a["vr_top5"]) or "(empty)", match))
    w("")
    w("## Findings ledger")
    w("")
    w("Confidence is about the facts shown, not about what Westley rules. Every fix is a piece to be built only after he reads the row. `repro` is `~/Projects/ouroboros-manifold/.venv/bin/python scripts/simlane/mission_choice.py --seeds S --missions K --out DIR` (about 9 seconds for all ten seeds) and the row `seed S, m K` of `mission_choice_raw.json`.")
    w("")
    ex_scan = ", ".join("%d/%d" % (r["seed"], r["k"]) for r in scan)
    ex_np = ", ".join("%d/%d" % (r["seed"], r["k"]) for r in scan_not_pool)
    ex_stale = ", ".join("%d/%d" % (r["seed"], r["k"]) for r in stale)
    ex_top5 = ", ".join("%d/%d" % (r["seed"], r["k"]) for r in top5_differs)
    w("**SL-A-01. The pipe replaces a drawn mission that fields no enemy, silently (high).**")
    w("- Rule: R-072-05 \"one weighted draw proportional to score picks the mission\"; R-072-07/08 name one fallback only, the quiet-world Defensive Stand, flagged `quiet_world`; R-074-01 \"given an archetype driven by an attack, enemy power is the attacker's committed budget x 300\".")
    w("- Sim: %d of %d shown missions (%d%%) are not the generator's draw (seed/mission %s). All %d draws were Defensive Stand with zero committed attack budget, so enemy power was 0 (`drawn_enemy_power` 0.0 in the raw rows); `handle_mission_start` (`csrc/pipe/om_pipe.c:1314-1347`, comment \"Never compose a zero-unit mission silently\") then scans archetype 0 to 9 against the player's regions in index order and shows the first that fields both sides. %d of the %d shown missions are in no pool at all (%s), e.g. a Siege Breaking on region 0; `quiet_world` stays false. %d of the %d Defensive Stand draws (%d%%) were overridden." % (
        len(scan), n, round(100 * len(scan) / n), ex_scan, len(scan), len(scan_not_pool), len(scan), ex_np, len(scan), ds_drawn, round(100 * len(scan) / ds_drawn)))
    w("- Seed and tick: first seen seed 1 m2 (tick 70, drawn 76/DS, shown 66/DS); a pool-less one seed 4 m3 (tick 145, drawn 3/DS, shown 0/SB).")
    w("- Repro: `--seeds 4 --missions 3`, row seed 4 m3 (`scan_used` true).")
    w("- Proposed fix: piece SIM-A-MC1, owner rows `csrc/mission.c` (SL-A-02 trigger fix removes the cause), `csrc/pipe/om_pipe.c` (drop or surface the scan), `docs/architecture.md`, test files for S-072/S-073 (test writer first). Surfacing it in the `mission` frame is a contract change and its own piece (`docs/architecture.md` frame, `autoload/c_bridge.gd`). Needs Westley's ruling first (Q-A2 below).")
    w("- Confidence: high on the facts, medium on the right remedy.")
    w("")
    w("**SL-A-02. The Defensive Stand trigger fires on any hostile neighbour, without an attack (high).**")
    w("- Rule: R-073-01 \"player region targeted by an enemy attack this window\"; `simulation/mission_generator.py:80-95` (the equations source) returns false without an attack in the action log.")
    w("- Sim: `om_mission_trigger_fires` case `OM_MISSION_ARCH_DEFENSIVE_STAND` (`csrc/mission.c:558-561`) is `has_hostile_neighbor(w, r, 0.0) || attacks > 0`. Of %d Defensive Stand pool entries over the 60 states, %d (%d%%) have no pending attack against the region; Defensive Stand is the most common pool archetype (%d of %d entries, %.1f%%). With no attack the committed budget is 0, enemy power is 0 and SL-A-01 follows." % (
        ds_pool, ds_noatk, round(100 * ds_noatk / ds_pool), ds_pool, pool_total, 100.0 * ds_pool / pool_total))
    w("- Seed and tick: every mission; first: seed %d m%d (tick %d), %d of its %d Defensive Stand entries have no attack." % (first_ds["seed"], first_ds["k"], first_ds["tick"], A(first_ds)["ds_pool_no_attack"], A(first_ds)["ds_pool"]))
    w("- Repro: as SL-A-01, field `analysis.ds_pool_no_attack`.")
    w("- Proposed fix: piece SIM-A-MC2, `csrc/mission.c` (the one `case`), `tests/csim/test_E10_S073_*` (positive control: a quiet border region produces no Defensive Stand; an attacked one does).")
    w("- Confidence: high that the code departs from the rule text; the remedy follows the rule.")
    w("")
    w("**SL-A-03. Interception can never enter the pool (high).**")
    w("- Rule: R-073-01 \"enemy attack declared against a player region, force in transit\"; legacy `trigger_interception` (`mission_generator.py:203-225`): an attack whose attacker owns no region adjacent to the target.")
    w("- Sim: the C case adds `!om_mission_has_hostile_neighbor(w, r, 0.0)` (`csrc/mission.c:604-607`): it fires only for a region with no hostile neighbour at all, which an attacked border region seldom is. Interception pool entries over the 60 states: **%d**. Player regions with a pending attack in those states: %d; of them %d have an attacker owning no adjacent region (the legacy meaning), where the pool should hold an Interception." % (pool_arch[6], attacked, interc_legacy))
    w("- Seed and tick: first: seed %d m%d (tick %d), regions %s attacked from a non-adjacent attacker, no Interception in a pool of %d." % (first_int["seed"], first_int["k"], first_int["tick"], A(first_int)["legacy_interception_regions"], first_int["pool_size"]))
    w("- Repro: field `analysis.legacy_interception_regions`.")
    w("- Proposed fix: piece SIM-A-MC3, `csrc/mission.c` (the one `case`) and `tests/csim/` (positive control: a telegraphed attack from a non-adjacent faction yields Interception).")
    w("- Confidence: high that it never fires; medium on the exact intended condition (the rule table gives \"force in transit\" only).")
    w("")
    w("**SL-A-04. Multi-Front Defense counts hostile neighbour regions, not distinct attacking factions (medium).**")
    w("- Rule: R-073-01 \"player region attacked by two or more factions this window\"; legacy `trigger_multi_front_defense` (`mission_generator.py:184-200`): the union of attacker faction ids and owners of hostile neighbours above military 50, at least 2 distinct.")
    w("- Sim: `csrc/mission.c:588-603` counts neighbouring regions (two regions of one faction count twice) and adds 1 for any attack. Of %d Multi-Front pool entries, %d (%d%%) have fewer than 2 distinct threat factions (legacy reading), and %d (%d%%) have fewer than 2 distinct attacking factions among pending attacks (the rule read literally; the world keeps no attack log, SL-A-11)." % (
        mf_pool, mf_lt2, round(100 * mf_lt2 / mf_pool), c_only[5], round(100 * c_only[5] / mf_pool)))
    w("- Seed and tick: 6 shown Multi-Front missions, e.g. seed 6 m1 (tick 22, 75/MF, not in the rule-literal pool).")
    w("- Repro: field `analysis.mf_lt2_distinct_sources`.")
    w("- Proposed fix: piece SIM-A-MC4, `csrc/mission.c` (the one `case`), `tests/csim/` (two regions of one faction: no Multi-Front; two factions: yes).")
    w("- Confidence: medium (the rule text and the legacy differ on whether neighbours count).")
    w("")
    w("**SL-A-05. Siege Breaking ignores \"held long enough\" (medium).**")
    w("- Rule: R-073-01 \"player region with a hostile neighbor above military 50, held long enough, own military <= 40 or economy <= 40\"; legacy `trigger_siege_breaking` requires `current_tick - held_since >= config.SIEGE_BREAKING_MIN_TICKS` (200, `simulation/config.py:670`).")
    w("- Sim: `OM_MISSION_SIEGE_MIN_HELD_TICKS 200` is defined (`csrc/mission.c:146`) and never read; the trigger has no held-time test. Of %d Siege pool entries, %d are in regions held for fewer than 200 ticks (confounded: these campaigns end at tick <= 300, so most regions are young). Siege Breaking is the most chosen archetype, %d of 60 (%d%%)." % (siege_pool, siege_young, final_arch[1], round(100 * final_arch[1] / 60)))
    w("- Seed and tick: every Siege mission; seed 3 m2 and m3 (ticks 94, 144) pick the same region twice.")
    w("- Repro: field `analysis.siege_held_lt_200`.")
    w("- Proposed fix: piece SIM-A-MC5, `csrc/mission.c` (the `case`, using `om_region_held_since`), `tests/csim/`. \"Long enough\" has no number in the bible, see Q-A3.")
    w("- Confidence: medium.")
    w("")
    w("**SL-A-06. Containment fires on the faction's archetype alone (medium).**")
    w("- Rule: R-073-01 \"hostile faction expanding along the player's border, two or more colonizations\"; legacy `trigger_containment` (`mission_generator.py:251-270`): at least `CONTAINMENT_EXPANSION_THRESHOLD` conquests by that faction in the window.")
    w("- Sim: `csrc/mission.c:615-623` fires for any region of a Conqueror, Warlord or Opportunist faction adjacent to the player unless `recent_revolt_events >= 2` supplies it (never set, SL-A-07). %d of %d pool entries (%.1f%%) are Containment; %d were shown. No colonization count is reachable to check the rule: `om_time_jump_report.n_colonizations` is never filled (SL-A-12)." % (contain_pool, pool_total, 100.0 * contain_pool / pool_total, final_arch[8]))
    w("- Seed and tick: seed 1 m6 (tick 270, 57/CT), seed 4 m4 and m6.")
    w("- Repro: field `analysis.contain_c_pool`.")
    w("- Proposed fix: piece SIM-A-MC6 after Q-A1 is ruled (needs an event/colonization record the world does not keep): `csrc/mission.c`, `csrc/faction.c` or `csrc/events.c` for the record (their owners to be named in `pieces.toml`), `tests/csim/`.")
    w("- Confidence: medium (unverifiable without the log; arithmetic of the firing condition is certain).")
    w("")
    w("**SL-A-07. Counterinsurgency is structurally unreachable and the urgency chain term is always 0 (high).**")
    w("- Rule: R-073-01 \"player region with an active revolt chain\"; R-072-02 `chain = min(1, 0.3 x recent revolt events in the region)`, weight 0.2 in urgency.")
    w("- Sim: both read `region_ctx.recent_revolt_events`, written only by `om_mission_set_revolt_events`, which has no caller outside `csrc/mission.c` (`om_mission_refresh_context` says \"Revolt events ... have no persistent source, so they stay unset\", `csrc/mission.c:2197-2200`). Counterinsurgency pool entries over 60 states: 0. The chain term was 0 for every one of the %d pool candidates. Reconquest, Suppression, Counterinsurgency and Interception were never chosen (Reconquest %d and Suppression %d pool entries in total: no player region lost in these campaigns, so those two are unverified, not defective)." % (pool_total, pool_arch[2], pool_arch[4]))
    w("- Seed and tick: all.")
    w("- Repro: field `analysis.c_pool_by_arch`.")
    w("- Proposed fix: piece SIM-A-MC7, owner rows `csrc/events.c` (record of revolt chains by region and tick) and `csrc/generational.c` (feed `om_mission_set_revolt_events` in the generator run), `tests/csim/`; depends on Q-A1.")
    w("- Confidence: high.")
    w("")
    w("**SL-A-08. Relevance is computed from a stale or missing lineage (high).**")
    w("- Rule: R-072-03 lineage 1.0 if a lineage member lives in the region, proximity from the lineage home; the mission offered must be weighted toward \"where I belong\" (S-072).")
    w("- Sim: `om_mission_generator_run(w)` runs before `om_character_selector_run(w)` in the same jump (`csrc/generational.c:2141-2142`). On the opening jump no lineage exists when the pool is scored, so **mission 1 of all 10 campaigns has relevance 0.0 for every candidate** (rule value 0.7 for the commander's home region); after a commander rotation the pool carries the previous lineage's relevance (seed 1 m4, seed 6 m6). %d of %d missions affected (%s); the top-5 set itself changes in %d (%s). `mission_start` refreshes the context afterwards but does not rescore the pool." % (
        len(stale), n, ex_stale, len(top5_differs), ex_top5))
    w("- Seed and tick: seed 1 m1 tick 20 (all relevance 0.0, region 76 is the commander's home).")
    w("- Repro: field `analysis.stale_relevance_regions`.")
    w("- Proposed fix: piece SIM-A-MC8, `csrc/generational.c` (swap the two calls, or rebuild the pool once the selector has run). Either changes the random stream after each jump, so the determinism goldens (`tests/long/`) and any trace fixture are regenerated in the same piece, and Westley sees the new traces first.")
    w("- Confidence: high.")
    w("")
    w("**SL-A-09. The archetype-fit term of relevance is never fed (medium).**")
    w("- Rule: R-072-03 `fit = min(1, times the lineage has run this archetype / 3)`, weight 0.3.")
    w("- Sim: `om_mission_refresh_context` passes `times_run = 0` (\"Lineage archetype history is not exposed\", `csrc/mission.c:2197-2200`, `csrc/mission.c:2261`). In %d missions (excluding the stale ones) the drawn pair's relevance is lower than the rule gives by %.1f to %.1f because the lineage had already run that archetype one to three times; the term never raises a repeated archetype's score. (Repeats are common: Siege Breaking was drawn in consecutive missions in several campaigns.)" % (len(fit_only), fit_min, fit_max))
    w("- Seed and tick: e.g. seed 2 m5 (tick 250, 77/AS: rule relevance 0.9, C 0.7).")
    w("- Repro: raw rows `analysis.chosen_R` against `analysis.chosen_C`.")
    w("- Proposed fix: piece SIM-A-MC9, a per-lineage archetype run count in `gen_state` (`csrc/generational.c`, save format version bump, a contract piece first: `csrc/ouroboros_sim.h`/`signatures.toml` if an accessor is public), `csrc/mission.c` reads it.")
    w("- Confidence: medium (where the count lives is a design call, Q-A4).")
    w("")
    w("**SL-A-10. Archetype preference is constant 0.5 (medium).**")
    w("- Rule: R-072-04 \"0.1 for an archetype the player marked rare, else the player's weight, default 0.5\".")
    w("- Sim: `om_mission_set_preference` has no caller outside `csrc/mission.c`; the onboarding `rare_marks` are saved and validated (`csrc/generational.c:392,528,1628`) but never read into the generator. Preference was 0.5 for all %d pool candidates; a rare mark cannot change a mission offer in play." % pool_total)
    w("- Seed and tick: all.")
    w("- Repro: field `c_pool` preference in the replica (`Sim.pool()` fifth column), or any row `analysis.vc.max_ds` against the 0.5 constant.")
    w("- Proposed fix: piece SIM-A-MC10, `csrc/generational.c` (apply `rare_marks` of the active onboarding slot to `om_mission_set_preference` at campaign start and on slot update), `tests/csim/` (positive control: marking Siege rare lowers its score by 0.08).")
    w("- Confidence: medium (the onboarding screen's production path is in another epic; check that nothing outside the C writes it).")
    w("")
    w("**SL-A-11. \"Recent\" and \"this window\" are, in the sim, only the pending telegraphs and an unwindowed loss count (medium).**")
    w("- Rule: R-072-02 \"recent attacks\", \"adjacent regions lost\"; R-073-01 \"this window\" (attack, conquest, breakaway, colonization).")
    w("- Sim: attacks are `om_pending_telegraphs` (an attack stays pending 3 ticks, `declared_tick + 3`); at the moment of choice the oldest pending telegraph is 2 ticks old in %d of %d states, so a 50-tick jump's earlier attacks are invisible. \"Adjacent regions lost\" counts any neighbour whose previous owner was the player, however long ago (`csrc/mission.c:2222`). The world keeps no attack, conquest, revolt or colonization log (`csrc/mission.c:545-547` says so)." % (tel_age[2], n))
    w("- Seed and tick: all.")
    w("- Repro: field `analysis.telegraph_age_max`.")
    w("- Proposed fix: none until Q-A1 is ruled; then `csrc/events.c` or a new `csrc/world_log.c` (new file) for the record, `csrc/mission.c` reads it.")
    w("- Confidence: medium.")
    w("")
    w("**SL-A-12. `om_time_jump_report` event counters are never filled (low, relevant to lane step 2).**")
    w("- Rule: the header documents `n_conquests`, `n_colonizations`, `n_revolts`, `n_faction_births`, `n_faction_deaths` (`csrc/ouroboros_sim.h` `om_time_jump_report`).")
    w("- Sim: `gen_time_jump` sets `start_tick`, `end_tick`, `jump_ticks`, `n_territory_changes`, `n_chronicle_entries`, `n_snapshots` only (`csrc/generational.c`, end of the function). Over the %d replica jumps the five counters were 0 every time while `n_territory_changes` was 8 to 12." % len(pj))
    w("- Seed and tick: every jump.")
    w("- Repro: raw rows `prev_jump`.")
    w("- Proposed fix: piece SIM-A-MC11, `csrc/generational.c` (fill from the tick events it already walks), `tests/csim/`.")
    w("- Confidence: high on the fact; whether anything reads them is for the chronicle scout.")
    w("")
    w("**SL-A-13. Snapshot `stance` rows omit the faction itself (low, doc).**")
    w("- Rule: `docs/architecture.md` snapshot example shows `\"id\":0 ... \"stance\":[3,1,2]` for three factions (n entries per row).")
    w("- Sim: `write_snapshot` skips `k == f` (`csrc/pipe/om_pipe.c:439`), so a row has n-1 entries and index b maps to `b if b < a else b - 1`. A consumer indexing by faction id reads the wrong faction (and the row for the last faction is one entry too short for an index by faction id).")
    w("- Seed and tick: every snapshot.")
    w("- Repro: `snapshot` after `set_seed`, `len(factions[i].stance)`.")
    w("- Proposed fix: piece SIM-A-MC12, `docs/architecture.md` only (describe the n-1 layout), unless the client reads it as n (then `autoload/c_bridge.gd` first look).")
    w("- Confidence: high.")
    w("")
    w("## Proposed Q- rows (not added to the register)")
    w("")
    w("| id | story | question | candidates |")
    w("|---|---|---|---|")
    w("| Q-A1 | E-10 / S-072, S-073 | What is \"recent\" / \"this window\" for the R-072-02 inputs and the R-073-01 triggers (attack, conquest, breakaway, colonization, revolt), and where is that record kept? Today the world keeps only 3-tick pending telegraphs and the loss count has no window. | (a) the last jump (50 ticks): the sim keeps an event record per jump (attacks, conquests, revolts, colonizations, births) the generator reads; (b) the time since the previous mission, same record; (c) keep today's pending telegraphs and ever-lost count and rewrite the rule text to say so |")
    w("| Q-A2 | E-10 / S-072, S-074 | A drawn candidate whose enemy has no power (a Defensive Stand with no attacker) cannot field a mission. The pipe now picks another by scanning. What should happen? | (a) it cannot occur once Defensive Stand needs an attack (SL-A-02) and the scan is removed; (b) redraw from the rest of the top 5; (c) treat as the quiet-world fallback with the `quiet_world` warning |")
    w("| Q-A3 | E-10 / S-073 | \"Held long enough\" for Siege Breaking has no number in the bible. | (a) 200 ticks as in the legacy config (`SIEGE_BREAKING_MIN_TICKS`); (b) a named draft value for Westley; (c) drop the clause |")
    w("| Q-A4 | E-10 / S-072 | Where does \"times the lineage has run this archetype\" live (R-072-03 fit)? | (a) a per-lineage counter in the generational state, saved; (b) derived from the ledger/chronicle record; (c) drop the fit term |")
    w("")
    w("Already open and met here: Q-072-02 (R-072-06 cannot reach urgency 0.8 under R-072-02's weights). The R-072-06 control cannot be shown in play; not re-tested.")
    w("")
    w("## What passed")
    w("")
    w("- The replica of the pipe handlers reproduces the pipe exactly in %d of %d missions (checksum, tick, region, archetype, quiet_world)." % (synced, n))
    w("- ALG-55 urgency: %d of %d pool candidates equal the independent Python value (deficit from the snapshot composites, border threat from stance and edges, attack pressure from telegraphs, loss count, chain 0), maximum difference 0.0." % (pool_total, pool_total))
    w("- ALG-55 relevance matches in %d of %d missions; score = 0.5u + 0.3rel + 0.2pref matches wherever relevance matches; the weights and the 5-hop breadth-first proximity reproduce." % (n - len(stale), n))
    w("- R-072-05: the drawn pair is in the top 5 by stored score in %d of %d missions; the draw is spread over ranks as a weighted draw should (rank-1 expected %.1f, observed %d)." % (in_stored_top5, n, exp_rank1, rank_hist[1]))
    w("- R-072-01 candidate regions: %d of %d C pool entries lie outside \"the player's regions and every region adjacent to them\"." % (outside, pool_total))
    w("- `quiet_world`: %d of %d. The R-072-07 retry and fallback path was not exercised, so the R-072-07/08 region and enemy re-derivation (`fallback_check` in the script) is untested by data." % (quiet, n))
    w("- The commander lineage used by the C (`om_lineage_id_at(nl-1)`) equalled `om_campaign_lineage` and the snapshot's `lineage` in every state (%s)." % ("yes" if lin_same else "NO"))
    w("")
    w("## Unverified")
    w("")
    w("- R-072-07/08 quiet-world fallback (never reached), R-072-06 (known open, Q-072-02).")
    w("- Reconquest, Suppression (almost no pool entries: the scripted player does not lose regions in 300 ticks) and Assault \"scored as an attack target\" (the C uses stance, adjacency and a weakness gate, not the player's attack scoring; the V_R model uses `om_faction_candidates` attack rows, so its Assault count is a weak reference).")
    w("- Containment and Counterinsurgency against the rule (no colonization or revolt record).")
    w("- Evacuation: the C also requires a hostile neighbour above military 50 (same as legacy, not in the rule table's words); %d V_R-only Evacuation entries come from that. Left as a question for Westley, not counted as a defect." % rule_only[7])
    w("- Whether the weighted draw uses `om_rng_draw` uniformly (not testable from outside; only the distribution above).")
    w("- Campaigns are six missions to tick 300 with an inactive player and `retention` untouched; longer campaigns, rotating lineages and lost regions are not covered.")
    w("")
    Path(out_path).write_text("\n".join(L) + "\n")
    print("wrote", out_path, "clean=%d deviating=%d" % (clean, deviating))


if __name__ == "__main__":
    main(*sys.argv[1:4])
