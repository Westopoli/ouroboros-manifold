#!/usr/bin/env python3
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import re
import sys
import random
from collections import Counter
import config

import world as world_mod
import faction as faction_mod
import events as _events
import naming_system as _naming_mod
import coherence_ledger as _ledger_mod
import tick as _tick
from time_jump import run_time_jump
from mission_generator import generate_mission, build_candidate_pool
from outcome_resolver import resolve_outcome
from generational import (GenerationalState, run_character_selection,
                           handle_commander_death, check_player_collapse)
from mission_contracts import MissionResult

WARMUP_TICKS  = 150
CYCLE_TICKS   = 100
N_CYCLES      = 6
OUTCOME_CYCLE = ["total_success", "strong_success", "partial_success",
                 "partial_failure", "total_failure", "total_success"]
KIA_CYCLE     = 3   # 0-indexed — force commander_survived=False on this cycle


# ── Output filtering ──────────────────────────────────────────────────────────

class _FilteredStdout:
    """Passes simulation output through, suppressing per-tick budget spam."""
    _SUPPRESS = re.compile(
        r'^\s*\[DRIFT t='           # drift diagnostic lines
        r'|^── t=\d+'               # bare tick header
        r'|^\s{4}\S+\s+\[\d+\]:'   # ownership grid   (    fid [N]: ...)
    )
    _INTERESTING = re.compile(
        r'TELEGRAPH|CONQUEST|surprise|coloniz|breakaway|collapse',
        re.IGNORECASE,
    )
    # Per-faction budget/action lines: "  t=NNNN fid   b=X.X  <act> ..."
    _BUDGET_LINE = re.compile(r'^\s+t=\s*\d+\s+\S+\s+b=')

    def __init__(self, real):
        self._real = real
        self._buf  = ""

    def write(self, text):
        self._buf += text
        while '\n' in self._buf:
            line, self._buf = self._buf.split('\n', 1)
            self._emit(line + '\n')

    def _emit(self, line):
        s = line.rstrip('\n\r')
        interesting = self._INTERESTING.search(s)
        if interesting:
            self._real.write(line)
            return
        if self._SUPPRESS.search(s):
            return
        if self._BUDGET_LINE.match(s):
            return
        self._real.write(line)

    def flush(self):
        if self._buf:
            self._emit(self._buf + '\n')
            self._buf = ""
        self._real.flush()


class suppress_sim_noise:
    def __enter__(self):
        self._orig = sys.stdout
        sys.stdout = _FilteredStdout(self._orig)
    def __exit__(self, *_):
        sys.stdout.flush()
        sys.stdout = self._orig


# ── World setup ───────────────────────────────────────────────────────────────

def setup_world(seed=42):
    config.ENABLE_EVENTS          = True
    config.ENABLE_FACTIONS        = True
    config.ENABLE_BORDER_FRICTION = True
    config.ENABLE_RECRUITMENT     = True
    config.ENABLE_ADJACENCY_BONUS = True
    config.ENABLE_OSCILLATION     = True
    config.ENABLE_TECHNOLOGY      = False
    config.ENABLE_DIPLOMACY       = False
    config.DIAGNOSTIC_PRINTS      = False   # suppress per-tick drift blocks

    w = world_mod.generate("four_way", seed=seed)
    factions = faction_mod.generate_starting_factions("four_way", rng=w.rng, world=w)
    registry = faction_mod.make_registry(*factions)

    ns = _naming_mod.NamingSystem()
    for fid in registry:
        for cat in ["people", "places", "factions"]:
            pool = [f"{cat}_{fid}_{i}" for i in range(400)]
            ns._pools.setdefault(fid, {})[cat] = {
                "available": list(pool), "used": [], "cooldown": [],
            }
    ledger = _ledger_mod.CoherenceLedger(ns)
    for fid, fac in registry.items():
        home_regions = [r for r in w.regions.values() if r.faction_id == fid]
        if home_regions:
            ledger.assign_faction_leader(fid, home_regions[0].id, 0, w.rng)

    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    trigger_state = {}
    pending_queue = _events.PendingQueue()

    player_fid = None
    for fid, fac in registry.items():
        if fac.archetype == "player_civilization":
            player_fid = fid
            break
    if not player_fid:
        player_fid = list(registry.keys())[0]

    leader = ledger.get_faction_leader(player_fid)
    player_lineage_id = ledger.create_lineage(leader.id) if leader else None

    gen_state = GenerationalState(player_fid, start_tick=0)
    if leader and player_lineage_id:
        gen_state.current_chapter["character_id"] = leader.id
        ledger.increment_chapter(player_lineage_id)

    return {
        "world": w,
        "registry": registry,
        "ledger": ledger,
        "ns": ns,
        "noise_offsets": noise_offsets,
        "trigger_state": trigger_state,
        "pending_queue": pending_queue,
        "player_fid": player_fid,
        "player_lineage_id": player_lineage_id,
        "gen_state": gen_state,
    }


def run_warmup(env, ticks, start_tick=0):
    w        = env["world"]
    registry = env["registry"]
    pending_telegraphs = []
    event_log    = []
    action_log   = []
    conquest_log = []

    with suppress_sim_noise():
        for t in range(start_tick + 1, start_tick + ticks + 1):
            log = _tick.run_tick(
                w, t,
                pending_queue=env["pending_queue"],
                noise_offsets=env["noise_offsets"],
                trigger_state=env["trigger_state"],
                registry=registry,
                pending_telegraphs=pending_telegraphs,
                coherence_ledger=env["ledger"],
            )
            for evt in log.get("events", []):
                event_log.append({**evt, "tick": t})
            for c in log.get("conquests", []):
                conquest_log.append({**c, "tick": t})
            for action in log.get("faction_actions", []):
                if action.get("action") == "attack" and action.get("budget_committed"):
                    action_log.append({
                        "faction_id":       action.get("faction_id"),
                        "action":           "attack",
                        "target_region":    action.get("target_region"),
                        "budget_committed": action.get("budget_committed", 200),
                        "tick":             t,
                    })

    return event_log, action_log, conquest_log


# ── Fixture repair ────────────────────────────────────────────────────────────

def _repair_player_position(w, registry, player_fid, current_tick):
    owned = w.regions_by_faction(player_fid)
    extra_actions, extra_events, extra_conquests = [], [], []

    if len(owned) < 3:
        player_rids = {r.id for r in owned}
        candidates = []
        for pr in owned:
            for nid in w.get_neighbors(pr.id):
                nr = w.regions.get(nid)
                if nr and nr.faction_id != player_fid and nid not in player_rids:
                    candidates.append(nid)
        needed = 3 - len(owned)
        seen = set()
        for rid in candidates:
            if len(extra_conquests) >= needed:
                break
            if rid in seen:
                continue
            seen.add(rid)
            r = w.regions[rid]
            old_fid = r.faction_id
            r.faction_id = player_fid
            r.fields["military"]   = 45.0
            r.fields["economy"]    = 50.0
            r.fields["tension"]    = 35.0
            r.fields["population"] = 55.0
            extra_conquests.append({
                "region_id": rid, "old_faction_id": old_fid,
                "new_faction_id": player_fid, "tick": current_tick,
            })
        owned = w.regions_by_faction(player_fid)

    non_player = [(fid, w.regions_by_faction(fid))
                  for fid in registry if fid != player_fid]
    non_player.sort(key=lambda x: -len(x[1]))

    enemy_fid    = None
    enemy_region = None
    for fid, regions in non_player:
        if not regions:
            continue
        for pr in owned:
            for nid in w.get_neighbors(pr.id):
                nr = w.regions.get(nid)
                if nr and nr.faction_id == fid:
                    enemy_fid, enemy_region = fid, nr
                    break
            if enemy_fid:
                break
        if enemy_fid:
            break

    if not enemy_fid and non_player:
        enemy_fid = non_player[0][0]
        for nid in w.get_neighbors(owned[0].id):
            nr = w.regions.get(nid)
            if nr and nr.faction_id != player_fid:
                nr.faction_id = enemy_fid
                enemy_region  = nr
                break

    if enemy_region:
        enemy_region.fields["military"] = 75.0
        enemy_region.fields["economy"]  = 65.0

    if enemy_fid and owned:
        target = owned[0]
        extra_actions.append({
            "faction_id": enemy_fid, "action": "attack",
            "target_region": target.id, "budget_committed": 350,
            "tick": current_tick,
        })
        print(f"  [fixture] attack injected: {enemy_fid} → {target.id}")

    if owned:
        revolt_target = owned[0].id
        for tmpl in ["evt_regional_revolt", "evt_revolt_entrenched"]:
            extra_events.append({
                "template_id": tmpl, "region_id": revolt_target,
                "tick": current_tick - 10,
            })
        w.regions[revolt_target].fields["tension"] = 72.0
        print(f"  [fixture] revolt events injected on {revolt_target}")

    return extra_actions, extra_events, extra_conquests


# ── Field delta helpers ───────────────────────────────────────────────────────

def _snapshot_fields(world, region_ids):
    snap = {}
    for rid in region_ids:
        r = world.regions.get(rid)
        if r:
            snap[rid] = dict(r.fields)
    return snap


def _compute_delta(world, snap_before, region_ids):
    total = 0.0
    for rid in region_ids:
        r = world.regions.get(rid)
        if not r or rid not in snap_before:
            continue
        for field, before in snap_before[rid].items():
            after = r.fields.get(field, before)
            total += abs(after - before)
    return total


def _lineage_watch_rids(world, ledger, lineage_id, fallback_rids):
    if not lineage_id:
        return fallback_rids
    history = ledger.get_lineage_history(lineage_id)
    if not history:
        return fallback_rids
    home_rid = history[0]
    rids = {home_rid}
    for nid in world.get_neighbors(home_rid):
        rids.add(nid)
    return rids


# ── Report helpers ────────────────────────────────────────────────────────────

def _region_phase(region):
    eco = region.fields.get("economy", 50)
    mil = region.fields.get("military", 50)
    if eco > 60 and mil > 55:
        return "expansion"
    if eco < 35 or mil < 30:
        return "contraction"
    return "stability"


def _format_trigger(archetype, ctx):
    parts = []
    if ctx.get("attacker_faction"):
        parts.append(f"attack from {ctx['attacker_faction']}")
    if ctx.get("revolt_events"):
        evts = ctx["revolt_events"]
        parts.append(f"revolt chain: {', '.join(evts[:2])}" +
                     (f" (+{len(evts)-2} more)" if len(evts) > 2 else ""))
    if ctx.get("target_faction"):
        parts.append(f"weak enemy territory: {ctx['target_faction']}")
    if ctx.get("conquering_faction"):
        parts.append(f"recently lost to {ctx['conquering_faction']}")
    if ctx.get("breakaway_faction"):
        parts.append(f"breakaway: {ctx['breakaway_faction']}")
    if ctx.get("expanding_faction"):
        parts.append(f"expanding faction: {ctx['expanding_faction']}")
    if ctx.get("hostile_neighbors"):
        parts.append(f"hostile neighbors: {ctx['hostile_neighbors']}")
    if ctx.get("ticks_under_pressure"):
        parts.append(f"under pressure {ctx['ticks_under_pressure']} ticks")
    return "; ".join(parts) if parts else "field threshold"


def _briefing_preview(briefing):
    situation = briefing.get("situation", "")
    sentences = re.split(r'(?<=[.!?])\s+', situation.strip())
    preview = " ".join(sentences[:2])
    return preview if preview else situation[:120]


def _top_deltas(applied_deltas, n=3):
    if not applied_deltas:
        return []
    return sorted(applied_deltas, key=lambda d: abs(d["delta"]), reverse=True)[:n]


def _crisis_check_str(world, ledger, lineage_id):
    if not lineage_id:
        return "none"
    history = ledger.get_lineage_history(lineage_id)
    if not history:
        return "none"
    home_rid = history[0]
    r = world.regions.get(home_rid)
    if not r:
        return "none"
    stab = r.composites.get("stability", 100 - r.fields.get("tension", 50))
    if stab < config.SELECTOR_CRISIS_THRESHOLD:
        return f"active: stability={stab:.0f} in {home_rid}"
    return f"none (stability={stab:.0f})"


def _rotation_reason_label(selection, cycle):
    if selection is None:
        return "none"
    reason = selection.rotation_reason
    if reason is None:
        return "first_mission" if cycle == 0 else "min_stay_or_stable"
    return reason


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'═'*70}")
    print(f"  Stage 5.5 Checkpoint G.5 — Character Selector Integration")
    print(f"{'═'*70}")

    env = setup_world(seed=42)
    w          = env["world"]
    registry   = env["registry"]
    ledger     = env["ledger"]
    player_fid = env["player_fid"]
    player_lineage_id = env["player_lineage_id"]
    gen_state  = env["gen_state"]

    print(f"\n  Player faction: {player_fid}  |  Starting lineage: {player_lineage_id}")
    print(f"  All factions: {list(registry.keys())}")

    # ── Warmup ───────────────────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f"  Warmup — {WARMUP_TICKS} ticks  (sim noise suppressed; interesting events shown below)")
    print(f"{'─'*70}")

    event_log, action_log, conquest_log = run_warmup(env, WARMUP_TICKS)
    current_tick = WARMUP_TICKS

    print(f"\n  Post-warmup: events={len(event_log)}  conquests={len(conquest_log)}")
    for fid in registry:
        owned = w.regions_by_faction(fid)
        if owned:
            avg_mil = sum(r.fields["military"] for r in owned) / len(owned)
            print(f"    {fid}: {len(owned)} regions  avg_mil={avg_mil:.0f}")

    # ── Fixture repair ────────────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f"  Fixture health check + repair")
    print(f"{'─'*70}")

    extra_actions, extra_events, extra_conquests = _repair_player_position(
        w, registry, player_fid, current_tick)
    action_log.extend(extra_actions)
    event_log.extend(extra_events)
    conquest_log.extend(extra_conquests)

    player_regions_now = w.regions_by_faction(player_fid)
    assert len(player_regions_now) >= 2, (
        f"Fixture invalid: player has {len(player_regions_now)} regions")
    pool_check = build_candidate_pool(
        w, registry, player_fid, event_log, action_log, conquest_log, current_tick)
    assert len(pool_check) >= 1, "Fixture invalid: candidate pool empty after repair"

    print(f"  Player regions: {len(player_regions_now)} ✓   Candidate pool: {len(pool_check)} ✓")

    # ── Generational cycles ───────────────────────────────────────────────────
    prefs = {"defensive_stand": 0.9, "assault": 0.8, "evacuation": "rare"}
    difficulty = "medium"
    current_lineage_id = player_lineage_id
    mission_history    = []
    lineage_timeline   = []
    pool_tally         = Counter()
    rotation_tally     = Counter()

    for cycle in range(N_CYCLES):
        outcome_band   = OUTCOME_CYCLE[cycle % len(OUTCOME_CYCLE)]
        kia_this_cycle = (cycle == KIA_CYCLE)

        print(f"\n{'═'*70}")
        print(f"  CYCLE {cycle + 1}/{N_CYCLES} — Tick {current_tick}"
              f"  (mock outcome: {outcome_band})" +
              (" [KIA forced]" if kia_this_cycle else ""))
        print(f"{'═'*70}")

        # Snapshot for delta
        watch_rids   = _lineage_watch_rids(w, ledger, current_lineage_id,
                                           {r.id for r in w.regions_by_faction(player_fid)[:1]})
        snap_before  = _snapshot_fields(w, watch_rids)

        # Time jump (filtered)
        last_m = mission_history[-1] if mission_history else None
        with suppress_sim_noise():
            jump_result = run_time_jump(
                world=w,
                n_ticks=CYCLE_TICKS,
                registry=registry,
                pending_queue=env["pending_queue"],
                noise_offsets=env["noise_offsets"],
                trigger_state=env["trigger_state"],
                stances=None,
                pending_telegraphs=[],
                rng=w.rng,
                start_tick=current_tick,
                coherence_ledger=ledger,
                naming_system=env["ns"],
                player_lineage_id=current_lineage_id,
                last_mission_region=last_m["region_id"] if last_m else None,
                last_mission_outcome=last_m["outcome_band"] if last_m else None,
                mission_info=({
                    "outcome":    last_m["outcome_band"],
                    "archetype":  last_m["archetype"],
                    "region":     last_m["region_id"],
                } if last_m else None),
            )
        current_tick = jump_result["end_tick"]
        event_log.extend(jump_result["events"])
        conquest_log.extend(jump_result["conquests"])

        region_field_delta = _compute_delta(w, snap_before, watch_rids)

        # Re-inject fixture attacks
        owned_now = w.regions_by_faction(player_fid)
        if owned_now and extra_actions:
            action_log.extend({**a, "tick": current_tick} for a in extra_actions)

        # Generate mission
        rng = random.Random(current_tick + cycle)
        mission_result = generate_mission(
            w, registry, player_fid, event_log, action_log,
            conquest_log, current_tick, difficulty, rng,
            ledger=ledger, current_lineage_id=current_lineage_id,
            player_preferences=prefs)

        if not mission_result:
            print(f"\n  WARNING: No mission generated in cycle {cycle + 1}")
            pl_rids = [r.id for r in w.regions_by_faction(player_fid)]
            print(f"  Player regions: {pl_rids}")
            continue

        setup    = mission_result["setup"]
        selected = mission_result["selected"]
        scored   = mission_result["scored_candidates"]
        region   = w.regions[setup.region_id]
        ctx      = selected.get("trigger_context", {})

        # Character selection
        selection = run_character_selection(
            gen_state, ledger, w, setup, rng, current_tick,
            current_lineage_id=current_lineage_id,
            region_field_delta=region_field_delta,
        )

        old_lineage_id = current_lineage_id
        old_faction_id = player_fid
        if selection:
            current_lineage_id = selection.lineage_id
            if selection.pool_used is not None:
                pool_tally[selection.pool_used] += 1
            else:
                pool_tally["_stay"] += 1
            r_label = _rotation_reason_label(selection, cycle)
            rotation_tally[r_label] += 1

        crisis_str   = _crisis_check_str(w, ledger, old_lineage_id)
        chapter_count = ledger.get_chapter_count(old_lineage_id) if old_lineage_id else 0

        # ── Mission Generation Review Report ──────────────────────────────────

        print(f"\n  Candidate pool (top {min(5, len(scored))} by score):")
        for i, s in enumerate(scored[:5]):
            marker = "  [SELECTED]" if s is selected else ""
            print(f"    {i+1}. ({s['region_id']}, {s['archetype']})"
                  f"  urgency={s['urgency']:.2f}"
                  f"  relevance={s['relevance']:.2f}"
                  f"  preference={s['preference']:.2f}"
                  f"  → score={s['score']:.3f}{marker}")

        stab  = region.composites.get("stability", 100 - region.fields.get("tension", 50))
        pop   = region.fields.get("population", 50)
        print(f"\n  Selected mission:")
        print(f"    Region:     {setup.region_id}"
              f"  (eco={region.fields.get('economy',0):.0f}"
              f"  ten={region.fields.get('tension',0):.0f}"
              f"  mil={region.fields.get('military',0):.0f}"
              f"  stab={stab:.0f}"
              f"  pop={pop:.0f}"
              f"  phase={_region_phase(region)})")
        print(f"    Archetype:  {setup.archetype}")
        print(f"    Trigger:    {_format_trigger(setup.archetype, ctx)}")

        if selection:
            new_lid = selection.lineage_id
            new_fid = selection.faction_id
            lid_same = "same" if new_lid == old_lineage_id else "different"
            fid_same = "same" if new_fid == old_faction_id else "different"
            cmdr_rec = ledger.get_character_by_id(selection.character_id)
            cmdr_age = (current_tick - cmdr_rec.born_tick) if cmdr_rec else "?"
            cmdr_home = cmdr_rec.region_id if cmdr_rec else "?"
            decision_str = "STAY" if not selection.rotation_reason else "ROTATE"
            reason_str = f"reason: {r_label}"
            pool_str = (selection.pool_used if selection.pool_used is not None else "—")
            print(f"\n  Commander selection:")
            print(f"    Decision:       {decision_str}  ({reason_str})")
            print(f"    Chapter count:  {chapter_count}  (prior lineage persistence)")
            print(f"    Total delta:    {region_field_delta:.1f}  (from last jump, watch={len(watch_rids)} regions)")
            print(f"    Crisis check:   {crisis_str}")
            if selection.pool_used is not None:
                print(f"    Pool used:      {selection.pool_used}  "
                      f"(weights prev={config.LINEAGE_POOL_WEIGHTS.get('previous_descendant',0):.2f}"
                      f"/nem={config.LINEAGE_POOL_WEIGHTS.get('nemesis_descendant',0):.2f}"
                      f"/unrel={config.LINEAGE_POOL_WEIGHTS.get('unrelated',0):.2f})")
            else:
                print(f"    Pool used:      — (stay / bloodline succession, no roll)")
            print(f"    Lineage:        {old_lineage_id}  →  {new_lid}  [{lid_same}]")
            print(f"    Faction:        {old_faction_id}  →  {new_fid}  [{fid_same}]")
            print(f"    Commander:      {selection.character_name}"
                  f"  (bloodline_id={new_lid}, age={cmdr_age}, home_region={cmdr_home})")
        else:
            print(f"\n  Commander selection:  FAILED (no candidate found)")

        pf = setup.player_force
        ef = setup.enemy_forces[0]
        from collections import Counter as C
        pt = C(u.unit_type for u in pf.units)
        et = C(u.unit_type for u in ef.units)
        parity = mission_result["allocation"]["parity_ratio"]
        pt_str = ", ".join(f"{n}×{t}" for t, n in sorted(pt.items()))
        et_str = ", ".join(f"{n}×{t}" for t, n in sorted(et.items()))
        print(f"\n  Force composition:")
        print(f"    Player: {pt_str or 'none'}  ({pf.total_power:.0f} power, {len(pf.units)} units)")
        print(f"    Enemy:  {et_str or 'none'}  ({ef.total_power:.0f} power, {len(ef.units)} units)")
        print(f"    Parity ratio: {parity:.2f}")

        print(f"\n  Briefing preview:")
        print(f"    {_briefing_preview(setup.briefing)}")

        # Resolve outcome
        commander_survived = not kia_this_cycle
        mock_result = MissionResult(
            mission_id=setup.mission_id,
            outcome_band=outcome_band,
            objective_score=0.7 if "success" in outcome_band else 0.3,
            force_retention=0.8 if "success" in outcome_band else 0.4,
            per_objective=[],
            commander_survived=commander_survived,
            ticks_elapsed=CYCLE_TICKS,
        )
        outcome = resolve_outcome(
            mock_result, setup.archetype, setup.region_id,
            w, player_fid, ledger=ledger,
            commander_id=selection.character_id if selection else None,
        )

        print(f"\n  Mock outcome:     {outcome_band}  commander_survived={commander_survived}")
        top3 = _top_deltas(outcome.get("applied_deltas", []))
        if top3:
            print(f"  Consequence preview (top 3 deltas):")
            for d in top3:
                print(f"    {d['region_id']}.{d['field']}: "
                      f"{d['old_value']:.1f} → {d['new_value']:.1f}  ({d['delta']:+.2f})")
        else:
            print(f"  Consequence preview: no field deltas applied")
        if outcome.get("region_transfer"):
            t = outcome["region_transfer"]
            print(f"  Region transfer: {t['region_id']}  {t['old_faction_id']} → {t['new_faction_id']}")

        # Record archetype for next cycle's relevance
        if current_lineage_id:
            ledger.record_archetype(current_lineage_id, setup.archetype)

        mission_history.append({
            "cycle":          cycle + 1,
            "region_id":      setup.region_id,
            "archetype":      setup.archetype,
            "outcome_band":   outcome_band,
            "score":          selected["score"],
            "lineage_id":     current_lineage_id,
            "old_lineage_id": old_lineage_id,
            "commander":      selection.character_name if selection else "unknown",
            "rotation":       (selection.rotation_reason or "stay") if selection else "—",
            "pool":           (selection.pool_used or "—") if selection else "—",
            "kia":            kia_this_cycle,
            "delta":          region_field_delta,
        })
        lineage_timeline.append((
            cycle + 1, current_lineage_id,
            selection.faction_id if selection else player_fid,
            selection.rotation_reason if selection else None,
        ))

    # ── Final summary ─────────────────────────────────────────────────────────
    print(f"\n{'═'*70}")
    print(f"  Summary")
    print(f"{'═'*70}")

    print(f"\n  Mission history:")
    hdr = f"  {'Cy':>2}  {'Region':<18} {'Archetype':<22} {'Outcome':<18} {'Commander':<22} {'Rotation':<20} Pool"
    print(hdr)
    print(f"  {'─'*2}  {'─'*18} {'─'*22} {'─'*18} {'─'*22} {'─'*20} {'─'*12}")
    for m in mission_history:
        kia = " ☠" if m["kia"] else ""
        print(f"  {m['cycle']:>2}  {m['region_id']:<18} {m['archetype']:<22} "
              f"{m['outcome_band']:<18} {m['commander']:<22} "
              f"{(m['rotation'] or 'stay'):<20} {m['pool']}{kia}")

    print(f"\n  Lineage timeline:")
    prev_lid = None
    for cycle_num, lid, fid, reason in lineage_timeline:
        if lid != prev_lid:
            marker = f" ← rotated ({reason})" if reason else " ← new"
        else:
            marker = ""
        print(f"    Cycle {cycle_num}: {lid}  [{fid}]{marker}")
        prev_lid = lid

    # Pool breakdown
    print(f"\n  Pool selection breakdown (rotations only):")
    valid_pools = {"previous_descendant", "nemesis_descendant", "unrelated"}
    for pool in ["previous_descendant", "nemesis_descendant", "unrelated"]:
        count = pool_tally.get(pool, 0)
        print(f"    {pool}: {count}")
    unexpected = {k for k in pool_tally if k not in valid_pools and k != "_stay"}
    for k in unexpected:
        print(f"    {k}: {pool_tally[k]}  ← ERROR: not in spec")
    print(f"    Stay decisions (no pool): {pool_tally.get('_stay', 0)}")

    # Rotation reason breakdown
    print(f"\n  Rotation reason breakdown:")
    for label in ["first_mission", "min_stay_or_stable", "delta_based", "normal",
                  "hard_cap", "commander_death", "forced", "crisis_veto_blocked"]:
        count = rotation_tally.get(label, 0)
        note = "  (tracking requires selector instrumentation)" if label == "crisis_veto_blocked" else ""
        print(f"    {label}: {count}{note}")

    # Lineage arc lengths
    print(f"\n  Lineage arc lengths:")
    arc_lengths = {}
    for m in mission_history:
        lid = m.get("lineage_id")
        if lid:
            arc_lengths[lid] = arc_lengths.get(lid, 0) + 1
    all_lens = list(arc_lengths.values())
    for lid, length in sorted(arc_lengths.items()):
        print(f"    {lid}: {length} chapter{'s' if length != 1 else ''}")
    if all_lens:
        print(f"    [min={min(all_lens)}, max={max(all_lens)} across all lineages]")

    # Invariant checks
    print(f"\n  Invariant checks:")

    # M14: 2–4 chapter arcs in most cases (hard cap = 6)
    violates_m14 = [lid for lid, n in arc_lengths.items() if n > 6]
    m14 = "PASS" if not violates_m14 else f"FAIL (>{6}: {violates_m14})"
    print(f"    M14 (no arc beyond hard_cap=6):       {m14}")

    # M15 alias: lineage_min_chapters honoured (no arc of 1 unless forced)
    arcs_of_one = [lid for lid, n in arc_lengths.items()
                   if n == 1 and not any(m["rotation"] in ("forced", "commander_death")
                                         and m["lineage_id"] == lid for m in mission_history)]
    m15 = "PASS" if not arcs_of_one else f"WARN (arcs of 1, possibly un-forced: {arcs_of_one})"
    print(f"    M15 (arcs ≥ min unless forced):        {m15}")

    # M17: first mission uses unrelated pool (no prior lineage exists)
    m17_pool = mission_history[0]["pool"] if mission_history else "—"
    m17 = "PASS" if m17_pool == "unrelated" else f"FAIL (pool={m17_pool})"
    print(f"    M17 (first mission unrelated pool):    {m17}")

    # M18: faction collapse reassignment (N/A if no collapse)
    collapse_happened = any(check_player_collapse(gen_state, w, registry) for _ in [0])
    m18 = "N/A — no collapse occurred" if not collapse_happened else "see collapse handling"
    print(f"    M18 (faction collapse reassignment):   {m18}")

    missions_generated = len(mission_history)
    if missions_generated < 3:
        print(f"\n  FAIL: Only {missions_generated}/6 missions generated")
    else:
        print(f"\n  Checkpoint G.5 output complete — {missions_generated}/6 missions generated")
    print(f"\n{'═'*70}\n")


if __name__ == "__main__":
    main()
