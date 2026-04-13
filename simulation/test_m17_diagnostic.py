"""
M17 Diagnostic — isolates why the first mission produces no commander selection.

Three hypotheses:
  A) setup is None    — generate_mission() returned nothing, guard never reached
  B) gen_state is None — no player_civilization faction found at sim init
  C) run_selection returns None — select_commander exhausted all pools

The leading suspect is C, specifically: the "unrelated" pool in select_commander
calls create_character(..., tick=0, rng) with hardcoded tick=0. By tick 2000,
all name cooldowns have expiry > 0, so tick=0 sees zero available names.

Run:
  python3 test_m17_diagnostic.py
"""
import sys
sys.path.insert(0, ".")

from sim_tuner import SCENARIOS
from sim_validator import run_recorded_scenario
import character_selector as cs_mod
import coherence_ledger as cl_mod

SCENARIO = "14_mission_calm"
SEED     = int(sys.argv[1]) if len(sys.argv) > 1 else 3

# ─── Patch points ─────────────────────────────────────────────────────────────

_selection_log = []   # one entry per run_selection call
_create_log    = []   # one entry per create_character call from select_commander context

_orig_run_selection   = cs_mod.run_selection
_orig_select_cmd      = cs_mod.select_commander
_orig_create_char     = cl_mod.CoherenceLedger.create_character

_in_select_cmd = [False]  # simple flag to scope create_character logging

def _patched_select_commander(gen_state, ledger, world, region_id, rng):
    _in_select_cmd[0] = True
    result = _orig_select_cmd(gen_state, ledger, world, region_id, rng)
    _in_select_cmd[0] = False
    return result

def _patched_create_character(self, faction_id, region_id, rank, tick, rng, **kwargs):
    result = _orig_create_char(self, faction_id, region_id, rank, tick, rng, **kwargs)
    if _in_select_cmd[0]:
        _create_log.append({
            "faction_id": faction_id,
            "region_id":  region_id,
            "rank":       rank,
            "tick_used":  tick,
            "result":     result.name if result else None,
            "avail_at_tick": self._naming.available_count(faction_id, "people", tick),
            "avail_at_2000": self._naming.available_count(faction_id, "people", 2000),
        })
    return result

def _patched_run_selection(gen_state, ledger, world, region_id, rng, tick,
                           current_lineage_id=None, region_field_delta=0.0):
    chapter  = gen_state.current_chapter
    char_id  = chapter.get("character_id")
    rec      = ledger.get_character_by_id(char_id) if char_id else None
    lin_id   = current_lineage_id or (rec.lineage_id if rec else None)
    cold_start = (not lin_id and not rec)

    result = _orig_run_selection(gen_state, ledger, world, region_id, rng, tick,
                                 current_lineage_id=current_lineage_id,
                                 region_field_delta=region_field_delta)
    _selection_log.append({
        "tick":        tick,
        "region_id":   region_id,
        "char_id":     char_id,
        "rec_status":  rec.status if rec else None,
        "lineage_id":  lin_id,
        "cold_start":  cold_start,
        "result":      result,
    })
    return result

cs_mod.run_selection      = _patched_run_selection
cs_mod.select_commander   = _patched_select_commander
cl_mod.CoherenceLedger.create_character = _patched_create_character

# ─── Run ──────────────────────────────────────────────────────────────────────

print(f"\n{'═'*62}")
print(f"  M17 DIAGNOSTIC — {SCENARIO}  seed={SEED}")
print(f"{'═'*62}\n")

scenario = SCENARIOS[SCENARIO]
tlog     = run_recorded_scenario(SCENARIO, scenario, seed_override=SEED)
ledger   = tlog.coherence_ledger
ns       = ledger._naming

# ─── Section 1: Guard state at mission review entry ───────────────────────────

print(f"{'─'*62}")
print("  SECTION 1 — GUARD STATE AT MISSION REVIEW ENTRY")
print(f"{'─'*62}")

# Determine player_fid (same logic as sim_validator)
import faction as faction_mod
player_fid = None
for fid, fac in tlog.snapshots[-1].factions.items():
    if fac.get("archetype") == "player_civilization":
        player_fid = fid
        break

print(f"  player_fid detected       : {player_fid}")
print(f"  gen_state present         : {'yes' if tlog.coherence_ledger else 'NO — hypothesis B'}")

# gen_state details from mission_reviews (we patched run_selection so we can infer)
if tlog.mission_reviews:
    first_rev = tlog.mission_reviews[0]
    setup     = first_rev.get("setup")
    cmdr_sel  = first_rev.get("commander_selection")
    print(f"  setup (mission 1) present : {'yes — ' + setup.archetype if setup else 'NO — hypothesis A'}")
    print(f"  commander_selection       : {'present' if cmdr_sel else 'None — M17 fail'}")
else:
    print("  No mission reviews recorded at all.")

# Player faction regions at tick 2000
last_snap   = tlog.snapshots[-1]
player_rgns = [rid for rid, rd in last_snap.regions.items()
               if rd.get("faction_id") == player_fid]
print(f"  player faction regions    : {len(player_rgns)}  ({', '.join(player_rgns[:4])})")

# Player deaths / reassignments (check for multiple chapters)
deaths = tlog.player_deaths if hasattr(tlog, "player_deaths") else []
print(f"  player faction collapses  : {len(deaths)}" +
      (f"  at ticks {[d['tick'] for d in deaths]}" if deaths else ""))

# ─── Section 2: run_selection trace (first 3 calls) ──────────────────────────

print(f"\n{'─'*62}")
print("  SECTION 2 — run_selection TRACE (first 3 mission slots)")
print(f"{'─'*62}")

for i, entry in enumerate(_selection_log[:3]):
    outcome = entry["result"]
    status  = ("✓ " + (outcome.pool_used or "stay")) if outcome else "✗ None"
    print(f"\n  Mission {i+1} (tick={entry['tick']}, region={entry['region_id']})")
    print(f"    char_id in chapter : {entry['char_id']}")
    print(f"    rec status         : {entry['rec_status']}")
    print(f"    lineage_id         : {entry['lineage_id']}")
    print(f"    cold start path    : {entry['cold_start']}")
    print(f"    result             : {status}")

if not _selection_log:
    print("  run_selection was never called (setup or gen_state was None — see Section 1)")

# ─── Section 3: create_character calls from within select_commander ───────────

print(f"\n{'─'*62}")
print("  SECTION 3 — create_character CALLS FROM select_commander")
print(f"{'─'*62}")

if _create_log:
    print(f"  {'Faction':<28} {'Region':<20} {'Rank':<16} {'Tick':>6}  "
          f"{'Avail@tick':>10}  {'Avail@2000':>10}  Result")
    print(f"  {'─'*28} {'─'*20} {'─'*16} {'─'*6}  {'─'*10}  {'─'*10}  {'─'*12}")
    for c in _create_log:
        res = c["result"] if c["result"] else "None ✗"
        print(f"  {str(c['faction_id']):<28} {str(c['region_id']):<20} "
              f"{c['rank']:<16} {c['tick_used']:>6}  "
              f"{c['avail_at_tick']:>10}  {c['avail_at_2000']:>10}  {res}")
else:
    print("  select_commander was never reached (earlier guard failed)")

# ─── Section 4: Name pool health at tick 0 vs tick 2000 ──────────────────────

print(f"\n{'─'*62}")
print("  SECTION 4 — NAME POOL HEALTH: tick=0 vs tick=2000")
print(f"{'─'*62}")
print("  (The 'unrelated' pool calls create_character with hardcoded tick=0)")
print()

factions_to_check = set()
if player_fid:
    factions_to_check.add(player_fid)
if _create_log:
    for c in _create_log:
        factions_to_check.add(c["faction_id"])

for fid in sorted(factions_to_check):
    pool  = ns._pools.get((fid, "people"), [])
    a0    = ns.available_count(fid, "people", 0)
    a2000 = ns.available_count(fid, "people", 2000)
    in_use = sum(1 for n in pool if n in ns._in_use)
    cd     = sum(1 for n in pool if n in ns._cooldowns)
    free   = len(pool) - in_use - cd
    print(f"  Faction: {fid}")
    print(f"    Pool size                  : {len(pool)}")
    print(f"    In-use                     : {in_use}")
    print(f"    On cooldown (expiry > 0)   : {cd}")
    print(f"    Never used (no cooldown)   : {free}")
    print(f"    Available at tick=0        : {a0}   ← what 'unrelated' pool sees")
    print(f"    Available at tick=2000     : {a2000}")
    if a0 == 0 and a2000 > 0:
        print(f"    !! Tick=0 sees empty pool; tick=2000 sees {a2000} names.")
        print(f"       Root cause: hardcoded tick=0 in select_commander line 246.")
    print()

# ─── Section 5: Summary ───────────────────────────────────────────────────────

print(f"{'─'*62}")
print("  SUMMARY")
print(f"{'─'*62}")

first_sel_none = (tlog.mission_reviews and
                  tlog.mission_reviews[0].get("commander_selection") is None)

if not first_sel_none:
    print("  M17 passed in this run — no failure to diagnose.")
else:
    first_rev  = tlog.mission_reviews[0]
    setup_none = first_rev.get("setup") is None
    gs_none    = not tlog.coherence_ledger

    if gs_none:
        print("  Hypothesis B CONFIRMED: gen_state was None (no player faction)")
    elif setup_none:
        print("  Hypothesis A CONFIRMED: generate_mission returned None")
    elif not _selection_log:
        print("  Hypothesis A or B: run_selection never called (guard check failed)")
    elif _selection_log and _selection_log[0]["result"] is None:
        # Check create_character results
        null_creates = [c for c in _create_log if c["result"] is None]
        tick0_empty  = any(c["avail_at_tick"] == 0 and c["avail_at_2000"] > 0
                           for c in null_creates)
        if tick0_empty:
            print("  Hypothesis C CONFIRMED: select_commander's 'unrelated' pool")
            print("    called create_character with tick=0, which sees 0 available names.")
            print("    The same pool at tick=2000 has names available.")
            print("    Fix: pass current tick through select_commander instead of hardcoding 0.")
        elif null_creates:
            print("  Hypothesis C CONFIRMED: create_character returned None")
            print("    (but tick issue unclear — check Section 3 for details)")
        else:
            print("  Hypothesis C: run_selection returned None but create_character succeeded?")
            print("    Check Section 2 for the exact failure path.")
    else:
        print("  M17 actually passed in this diagnostic run.")
        print("  Compare against test_validate.py to check for false-flag pattern.")

print(f"\n{'═'*62}\n")
