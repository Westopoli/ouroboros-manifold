from naming_system import NamingSystem
from coherence_ledger import CoherenceLedger, RANKS
import random

ns = NamingSystem()

f1_names = ['Kaelith Vorn', 'Suranna Deshkov', 'Toryn Ashemark', 'Velan Koss',
            'Mireth Solane', 'Draven Thurik', 'Olenna Brask', 'Fendric Hale',
            'Cassia Vrenn', 'Aldric Mourne']
f2_names = ['Zhara Okun', 'Brin Tasev', 'Lunara Chelk', 'Demaris Vyth',
            'Korren Sable', 'Ithara Goss', 'Tyven Marsh', 'Sariel Donn',
            'Quillon Pask', 'Elanda Rieve']
ns.load_pool('faction_1', 'people', f1_names)
ns.load_pool('faction_2', 'people', f2_names)

ledger = CoherenceLedger(ns)
rng = random.Random(42)

print(f'=== Rank enum: {RANKS} ===')
assert 'garrison_officer' in RANKS

print('\n=== Create faction leaders ===')
leader1 = ledger.assign_faction_leader('faction_1', 'region_home_f1', tick=0, rng=rng)
leader2 = ledger.assign_faction_leader('faction_2', 'region_home_f2', tick=0, rng=rng)
print(f'  F1 leader: {leader1.name} (rank={leader1.rank}, born_tick={leader1.born_tick}, '
      f'lifespan={leader1.lifespan_ticks})')
print(f'  F2 leader: {leader2.name} (rank={leader2.rank}, born_tick={leader2.born_tick}, '
      f'lifespan={leader2.lifespan_ticks})')

print('\n=== Create regional commander ===')
rc = ledger.assign_regional_commander('faction_1', 'region_border_01', tick=0, rng=rng)
print(f'  {rc.name} (rank={rc.rank}, born_tick={rc.born_tick}, lifespan={rc.lifespan_ticks})')

print('\n=== Kill regional commander ===')
ledger.kill_character(rc.id, tick=50)
print(f'  {rc.name}: status={rc.status}, death_tick={rc.death_tick}')
avail_50 = ns.is_available(rc.name, current_tick=50)
avail_551 = ns.is_available(rc.name, current_tick=551)
print(f'  Name available at tick 50: {avail_50} (expected False)')
print(f'  Name available at tick 551: {avail_551} (expected True)')

print('\n=== Create lineage with 3 members ===')
root = ledger.create_character('faction_1', 'region_home_f1', 'lineage_member',
                               tick=0, rng=rng)
lineage_id = ledger.create_lineage(root.id)
print(f'  Root: {root.name} (id={root.id}, lineage={lineage_id})')
child1 = ledger.create_character('faction_1', 'region_home_f1', 'lineage_member',
                                 tick=10, rng=rng, lineage_id=lineage_id,
                                 parent_id=root.id, generation=1)
child2 = ledger.create_character('faction_1', 'region_border_01', 'lineage_member',
                                 tick=10, rng=rng, lineage_id=lineage_id,
                                 parent_id=root.id, generation=1)
print(f'  Child 1: {child1.name} (parent={root.name}, gen={child1.generation})')
print(f'  Child 2: {child2.name} (parent={root.name}, gen={child2.generation})')
children_names = [ledger.get_character_by_id(cid).name for cid in root.children_ids]
print(f'  Root children: {children_names}')
member_names = [m.name for m in ledger.get_lineage_members(lineage_id)]
print(f'  All lineage members: {member_names}')
print(f'  Lineage regions: {ledger.get_lineage_history(lineage_id)}')

print('\n=== Event attachment ===')
evt = {'template_id': 'evt_tension_threshold', 'region_id': 'region_home_f1',
       'significance_tier': 3, 'field_deltas': {'tension': 10}}
attached = ledger.attach_event(evt, 'region_home_f1', tick=20)
print(f'  Tier-3 event: attached to {attached.name} (rank={attached.rank})')
print(f'  Event character_id={evt["character_id"]}, character_name={evt["character_name"]}')

low_evt = {'template_id': 'evt_minor', 'region_id': 'region_home_f1',
           'significance_tier': 2}
result = ledger.attach_event(low_evt, 'region_home_f1', tick=21)
print(f'  Tier-2 event: attached={result} (expected None)')

print('\n=== Summary ===')
active = ledger.active_character_count()
hist = ledger.historical_character_count()
attachments = ledger.total_event_attachments()
print(f'  Active: {active}, Historical: {hist}, Attachments: {attachments}')

print('\n=== All character records ===')
for c in ledger._characters.values():
    lin = c.lineage_id or "-"
    print(f'  {c.id}: {c.name:<20} rank={c.rank:<20} status={c.status:<12} '
          f'born_tick={c.born_tick:<6} lifespan={c.lifespan_ticks:<6} lineage={lin}')

# Verify no ID gaps
ids = sorted(int(c.id.split("_")[1]) for c in ledger._characters.values())
print(f'\n=== ID sequence: {ids} ===')
for i in range(len(ids) - 1):
    assert ids[i + 1] == ids[i] + 1, f'ID gap between char_{ids[i]} and char_{ids[i+1]}'
print('  No ID gaps: YES')
