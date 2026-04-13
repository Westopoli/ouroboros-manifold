"""
K7 Diagnostic — isolates why factions with territory end up leaderless.

Three hypotheses:
  A) Name pool exhaustion    — create_character returns None silently
  B) _succeed never called   — kill_character called without world/rng
  C) Succession fires but SC dies again before checkpoint

Run:
  python3 test_k7_diagnostic.py
"""
import sys
sys.path.insert(0, ".")

from sim_tuner import SCENARIOS
from sim_validator import run_recorded_scenario, _apply_features
from invariants import every_faction_has_leader
import coherence_ledger as cl_mod
import config

SCENARIO = "14_mission_calm"
SEED     = int(sys.argv[1]) if len(sys.argv) > 1 else 3

# ─── Patch points ─────────────────────────────────────────────────────────────

_succession_log = []   # [(tick, faction_id, reason, outcome)]
_null_names_log = []   # [(tick, faction_id, category)]

_orig_succeed          = cl_mod.CoherenceLedger._succeed
_orig_create_character = cl_mod.CoherenceLedger.create_character
_orig_kill_character   = cl_mod.CoherenceLedger.kill_character

def _patched_succeed(self, dead_rec, tick, world, rng):
    faction_id = dead_rec.faction_id
    regions    = world.regions_by_faction(faction_id)
    ns         = self._naming
    avail      = ns.available_count(faction_id, "people", tick)
    pool_size  = ns.pool_size(faction_id, "people")
    in_use_cnt = sum(1 for n in ns._pools.get((faction_id, "people"), []) if n in ns._in_use)

    before_count = sum(
        1 for c in self._characters.values()
        if c.faction_id == faction_id and c.rank == "supreme_commander" and c.status == "active"
    )

    _orig_succeed(self, dead_rec, tick, world, rng)

    after_count = sum(
        1 for c in self._characters.values()
        if c.faction_id == faction_id and c.rank == "supreme_commander" and c.status == "active"
    )

    outcome = "OK" if after_count > before_count else "FAILED"
    reason  = "pool_empty" if avail == 0 else ("no_regions" if not regions else "unknown")
    _succession_log.append((tick, faction_id, reason if outcome == "FAILED" else "—",
                             outcome, avail, pool_size, in_use_cnt, len(regions)))

def _patched_create_character(self, faction_id, region_id, rank, tick, rng, **kwargs):
    result = _orig_create_character(self, faction_id, region_id, rank, tick, rng, **kwargs)
    if result is None:
        _null_names_log.append((tick, faction_id, rank))
    return result

def _patched_kill_character(self, char_id, tick, world=None, rng=None):
    rec = self._characters.get(char_id)
    if rec and rec.rank == "supreme_commander" and world is None:
        _succession_log.append((tick, rec.faction_id, "no_world_arg", "FAILED", -1, -1, -1, -1))
    _orig_kill_character(self, char_id, tick, world=world, rng=rng)

cl_mod.CoherenceLedger._succeed          = _patched_succeed
cl_mod.CoherenceLedger.create_character  = _patched_create_character
cl_mod.CoherenceLedger.kill_character    = _patched_kill_character

# ─── Run ──────────────────────────────────────────────────────────────────────

print(f"\n{'═'*62}")
print(f"  K7 DIAGNOSTIC — {SCENARIO}  seed={SEED}")
print(f"{'═'*62}\n")

scenario = SCENARIOS[SCENARIO]
tlog     = run_recorded_scenario(SCENARIO, scenario, seed_override=SEED)
ledger   = tlog.coherence_ledger
ns       = ledger._naming

# ─── Section 1: K7 check ──────────────────────────────────────────────────────

k7 = every_faction_has_leader(tlog)
status = "PASS ✓" if k7.passed else "FAIL ✗"
print(f"K7 result: {status}  —  {k7.message}")
if not k7.passed:
    for f in (k7.details or {}).get("failures", []):
        print(f"  · {f}")

# ─── Section 2: Succession log ────────────────────────────────────────────────

print(f"\n{'─'*62}")
print("  SUCCESSION EVENTS")
print(f"{'─'*62}")
failed = [e for e in _succession_log if e[3] == "FAILED"]
ok     = [e for e in _succession_log if e[3] == "OK"]
print(f"  Total succession calls: {len(_succession_log)}  |  OK: {len(ok)}  |  FAILED: {len(failed)}")

if failed:
    print(f"\n  {'Tick':<8} {'Faction':<30} {'Reason':<20} {'Avail':>6} {'Pool':>6} {'InUse':>6} {'Rgns':>5}")
    print(f"  {'─'*8} {'─'*30} {'─'*20} {'─'*6} {'─'*6} {'─'*6} {'─'*5}")
    for (tick, fid, reason, outcome, avail, pool_sz, in_use, rgns) in failed:
        avail_s   = str(avail)   if avail  >= 0 else "N/A"
        pool_s    = str(pool_sz) if pool_sz >= 0 else "N/A"
        in_use_s  = str(in_use)  if in_use >= 0 else "N/A"
        print(f"  {tick:<8} {fid:<30} {reason:<20} {avail_s:>6} {pool_s:>6} {in_use_s:>6} {rgns:>5}")
else:
    print("  No failed successions recorded.")

# ─── Section 3: Null name calls ───────────────────────────────────────────────

print(f"\n{'─'*62}")
print("  CREATE_CHARACTER → None  (name pool returned nothing)")
print(f"{'─'*62}")
if _null_names_log:
    sc_nulls = [(t, f, r) for t, f, r in _null_names_log if r == "supreme_commander"]
    other_nulls = [(t, f, r) for t, f, r in _null_names_log if r != "supreme_commander"]
    print(f"  SC-rank nulls: {len(sc_nulls)}  |  Other-rank nulls: {len(other_nulls)}")
    if sc_nulls:
        print(f"\n  {'Tick':<8} {'Faction':<30} {'Rank'}")
        print(f"  {'─'*8} {'─'*30} {'─'*20}")
        for (t, f, r) in sc_nulls:
            print(f"  {t:<8} {f:<30} {r}")
else:
    print("  None — create_character never returned None.")

# ─── Section 4: Pool health at K7 failure points ─────────────────────────────

print(f"\n{'─'*62}")
print("  POOL HEALTH AT K7 FAILURE CHECKPOINTS")
print(f"{'─'*62}")

failing_cases = (k7.details or {}).get("failures", [])
if not failing_cases:
    print("  K7 passed — nothing to show.")
else:
    # Extract (jump_tick, end_tick, faction_id) from failure strings
    import re
    for failure_str in failing_cases:
        m = re.match(r"jump@(\d+): (\S+) has (\d+) regions", failure_str)
        if not m:
            print(f"  (could not parse: {failure_str})")
            continue
        jump_tick = int(m.group(1))
        fid       = m.group(2)
        rgn_count = int(m.group(3))

        # Find end_tick for this jump
        end_tick = jump_tick
        for tj in tlog.time_jump_results:
            if tj.get("jump_tick") == jump_tick:
                end_tick = tj.get("end_tick", jump_tick)
                break

        pool      = ns._pools.get((fid, "people"), [])
        avail     = ns.available_count(fid, "people", end_tick)
        in_use    = sum(1 for n in pool if n in ns._in_use)
        cooldown  = sum(1 for n in pool if n in ns._cooldowns
                        and end_tick < ns._cooldowns[n])
        free      = avail

        # Active characters for this faction
        chars = [c for c in ledger._characters.values() if c.faction_id == fid]
        active_sc = [c for c in chars
                     if c.rank == "supreme_commander" and c.status == "active"]
        dead_sc   = [c for c in chars
                     if c.rank == "supreme_commander" and c.status == "historical"]

        print(f"\n  jump@{jump_tick} → end_tick={end_tick}  faction={fid}  regions={rgn_count}")
        print(f"    Pool : {len(pool)} total | {free} available | {in_use} in-use | {cooldown} on cooldown")
        print(f"    SCs  : {len(active_sc)} active | {len(dead_sc)} historical")
        for sc in dead_sc[-3:]:
            cd = ns._cooldowns.get(sc.name)
            print(f"      dead SC '{sc.name}'  died_tick={sc.death_tick}  "
                  f"name_free_at={cd if cd else 'now'}")

# ─── Section 5: Global pool pressure ─────────────────────────────────────────

print(f"\n{'─'*62}")
print("  GLOBAL NAME PRESSURE (at end of run)")
print(f"{'─'*62}")
total_in_use = len(ns._in_use)
total_cooldown = len(ns._cooldowns)
total_pool_keys = len(ns._pools)
print(f"  Total names in-use  : {total_in_use}")
print(f"  Total names on cooldown : {total_cooldown}")
print(f"  Distinct faction×category pools : {total_pool_keys}")

# Count unique names across all pools (names are shared via _in_use)
all_names = set()
for pool in ns._pools.values():
    all_names.update(pool)
print(f"  Unique names across all pools   : {len(all_names)}")
print(f"  (If in-use ≈ unique names → pool is exhausted globally)")

print(f"\n{'═'*62}\n")
