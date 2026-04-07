from sim_validator import run_recorded_scenario
from sim_tuner import SCENARIOS

sc = dict(SCENARIOS["08_lifecycle_2faction"])
sc["ticks"] = 300
sc["seed"] = 1
sc["features"] = dict(sc["features"])
sc["features"]["coherence_ledger"] = True

log = run_recorded_scenario("08_lifecycle_2faction", sc)

# Access the coherence ledger from the last tick's state — we need to
# reconstruct it. Instead, let's scan the trajectory log for event attachments.

total_attachments = 0
for snap in log.snapshots:
    for evt in snap.events_fired:
        if "character_id" in evt:
            total_attachments += 1

# Count unique characters seen in attachments
char_ids = set()
for snap in log.snapshots:
    for evt in snap.events_fired:
        if "character_id" in evt:
            char_ids.add(evt["character_id"])

print("=== Checkpoint C: Coherence Ledger Integration ===")
print(f"  Scenario: 08_lifecycle_2faction, 300 ticks, seed 1")
print(f"  Total ticks: {log.total_ticks}")
print(f"  Total event attachments: {total_attachments}")
print(f"  Unique characters attached: {len(char_ids)}")

# Show first 10 attachments
print("\n=== First 10 event attachments ===")
count = 0
for snap in log.snapshots:
    for evt in snap.events_fired:
        if "character_id" in evt:
            tid = evt.get("template_id", "?")
            cname = evt.get("character_name", "?")
            rid = evt.get("region_id", "?")
            print(f"  t={snap.tick}: {tid} in {rid} -> {cname} ({evt['character_id']})")
            count += 1
            if count >= 10:
                break
    if count >= 10:
        break

# Verify at least 1 attachment occurred
assert total_attachments > 0, "FAIL: No event attachments occurred"
print(f"\n  At least 1 event attachment: YES ({total_attachments} total)")

# Show factions at tick 300 with their leaders
print("\n=== Faction leaders at tick 300 ===")
final = log.snapshots[-1]
ledger = log.coherence_ledger
factions_with_leader = 0
factions_without_leader = 0
for fid, fdata in sorted(final.factions.items()):
    count = fdata["owned_region_count"]
    if count == 0:
        continue
    arch = fdata["archetype"]
    leader = ledger.get_faction_leader(fid) if ledger else None
    if leader:
        print(f"  {fid}: {count} regions, leader={leader.name} "
              f"(rank={leader.rank}, born_tick={leader.born_tick}, "
              f"region={leader.region_id})")
        factions_with_leader += 1
    else:
        print(f"  {fid}: {count} regions, leader=NONE")
        factions_without_leader += 1

print(f"\n  Factions with leader: {factions_with_leader}")
print(f"  Factions without leader: {factions_without_leader}")

# Show total character stats
if ledger:
    print(f"\n=== Ledger summary ===")
    print(f"  Active characters: {ledger.active_character_count()}")
    print(f"  Historical characters: {ledger.historical_character_count()}")
    total = ledger.active_character_count() + ledger.historical_character_count()
    print(f"  Total characters created: {total}")
    print(f"  Total event attachments: {ledger.total_event_attachments()}")

# Verify every faction with regions has a leader
if factions_without_leader > 0:
    print(f"\n  WARNING: {factions_without_leader} faction(s) with regions but no leader")
else:
    print(f"\n  Every faction with regions has a leader: YES")

print("\n=== Done ===")
