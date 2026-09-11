# Roman Era — Sloyd Prompt Batch Sheet

> Copy-paste prompts into Sloyd, check against "Look For," mark off when accepted.
>
> **Era identity:** Ancient Rome. Tier 1 = Republican Grit (plain, utilitarian, earth-toned). Tier 2 = Imperial Might (red and gold, segmented armor, eagles). Tier 3 = Late Imperial / Divine (ornamental excess, gilded, ceremonial decadence).
>
> **Humanoid animation workflow:** Bodies are generated in T-pose without weapons. Weapons are separate standalone props. Bodies go through Mixamo (FBX/OBJ upload → auto-rig → pick animations → download FBX at 30fps). Weapons attach at runtime in Godot via BoneAttachment3D on hand bones. See docs/bible_history/bible_2_00_ai_pipeline.md "Humanoid Unit Animation Pipeline" for full spec.

---

## Weapon Props

> Standalone assets, not attached to any unit. Shared across all units that carry them within a tier.

### Swords

#### Gladius T1
**Prompt:**
Simple Roman short sword, plain iron blade, basic wooden grip, no decoration. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Gladius T2
**Prompt:**
Roman gladius short sword, polished blade, leather-wrapped grip, simple pommel. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Gladius T3
**Prompt:**
Ornate Roman ceremonial sword, gold-inlaid blade, jeweled pommel, decorative guard. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Spatha (Cavalry Sword) T2
**Prompt:**
Roman spatha long sword, longer blade than a gladius, simple crossguard, leather grip. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Shields

#### Scutum T1
**Prompt:**
Large oval Roman shield, plain wood with simple iron boss, no decoration. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Scutum T2
**Prompt:**
Rectangular Roman scutum shield, curved face, painted red with gold wing design, iron boss and edging. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Scutum T3
**Prompt:**
Ornate Roman ceremonial shield, jeweled boss, gold leaf edges, purple and gold painted face. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Polearms & Ranged

#### Pilum T1
**Prompt:**
Simple Roman javelin, thin iron point on a wooden shaft, plain and crude. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Pilum T2
**Prompt:**
Roman pilum javelin, long iron shank on wooden shaft, properly weighted. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Lance T3
**Prompt:**
Ornate Roman cavalry lance, decorated shaft, gold-tipped point, decorative ribbons. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Recurve Bow T2
**Prompt:**
Roman auxiliary recurve bow, curved wooden limbs, simple string. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Composite Bow T3
**Prompt:**
Ornate eastern composite bow, decorated limbs, intricate curve. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Standards

#### Vexillum T1
**Prompt:**
Simple Roman vexillum, plain wooden pole with a cloth banner hanging from a crossbar. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Aquila T2
**Prompt:**
Roman golden eagle aquila on a tall pole, simple golden eagle on top. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

#### Aquila T3
**Prompt:**
Ornate Roman golden aquila standard with gemstones, laurel wreath below eagle, gold and purple ribbons. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

---

## Unit Bodies (T-Pose, No Weapons)

> All humanoid units generated WITHOUT weapons or shields. Arms open in T-pose for Mixamo.

### Legionary (Vanguard) — "The Wall"

#### T2
**Prompt:**
Roman legionary soldier in T-pose, lorica segmentata armor, crested galea helmet, military sandals, belt. No weapons, no shield, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Iconic legionary armor, front-heavy silhouette. Hands empty.

#### T1
**Prompt:**
Early Roman hastati soldier in T-pose, bronze chest plate, simple bronze helmet, plain tunic, military sandals. No weapons, no shield, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Plainer, utilitarian. Hands empty.

#### T3
**Prompt:**
Ornate Roman legionary in T-pose, gold-inlaid ceremonial armor, tall crested helmet, purple cloak. No weapons, no shield, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Gold and excess. Hands empty.

---

### Equites (Raider) — "The Knife"

#### T2
**Prompt:**
Roman auxiliary cavalry rider on horseback in T-pose, chainmail armor, light helmet, simple saddle. No weapons, no shield, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Rider on horse, narrow fast silhouette. Hands empty.

#### T1
**Prompt:**
Unarmored Roman cavalry rider on horseback in T-pose, simple tunic, no armor, light horse. No weapons, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Bare-bones cavalry. Hands empty.

#### T3
**Prompt:**
Roman cataphract-style rider on armored horse in T-pose, scale armor, golden horse mask. No weapons, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Heavy armor, gold horse mask. Hands empty.

---

### Velites (Interceptor) — "The Shield"

#### T2
**Prompt:**
Roman auxiliary archer in T-pose, leather cuirass, quiver of arrows on back, light helmet. No weapons in hands, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Light armor, quiver visible on back. Hands empty.

#### T1
**Prompt:**
Young Roman velites skirmisher in T-pose, bare-chested with wolf-skin cap, small pouch. No weapons, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Lightest equipped, wolf-skin cap identifier. Hands empty.

#### T3
**Prompt:**
Elite Roman eastern auxiliary in T-pose, decorated quiver on back, embroidered tunic, leather arm guards. No weapons in hands, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Exotic specialist, ornate gear. Hands empty.

---

### Signifer (Warden) — "The Hearth"

#### T2
**Prompt:**
Roman standard bearer in T-pose, bear pelt headdress, chainmail armor. No standard, no weapons, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Bear pelt is the identifier. Hands empty — standard attaches via BoneAttachment3D.

#### T1
**Prompt:**
Simple Roman standard bearer in T-pose, unarmored, practical tunic. No standard, no weapons, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Plain and utilitarian. Hands empty.

#### T3
**Prompt:**
Ornate Roman standard bearer in T-pose, elaborate lion pelt headdress, gilded armor. No standard, no weapons, arms spread. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Maximum opulence on the bearer. Hands empty.

---

## Non-Humanoid Units (Static Meshes, No Mixamo)

> These don't go through Mixamo. Generated as complete static assets.

### Scorpion / Ballista (Bombard) — "The Hammer"

#### T2
**Prompt:**
Roman iron-framed ballista siege weapon on a wheeled wooden cart, taut torsion ropes, bolt ammunition. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Longest silhouette, weapon dominates.

#### T1
**Prompt:**
Small crude Roman scorpion bolt-thrower, wooden frame, rope-wound torsion springs, simple tripod base. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Smaller, rougher, improvised.

#### T3
**Prompt:**
Massive Roman onager catapult battery on a reinforced platform, bronze-clad frame, multiple throwing arms, ornate metalwork. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Biggest artillery, bronze excess.

---

### Testudo / Castra (Bastion) — "The Mountain"

#### T2
**Prompt:**
Roman castra rampart fortification section with wooden palisade wall, gate tower, earthwork ditch. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Wider than long, immovable defensive position.

#### T1
**Prompt:**
Crude Roman marching camp defenses, wooden stakes in a ditch, improvised earth rampart, simple palisade. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Rough and improvised, stakes and dirt.

#### T3
**Prompt:**
Roman stone garrison fort section with corner towers, tiled roofs, carved eagle pediment, thick masonry walls. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

**Look for:** Permanent stone, imperial grandeur.

---

## Structures

### Castrum T2
**Prompt:**
Roman stone fort castrum, rectangular layout, wooden gate, watchtower, paved road leading in. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Castrum T1
**Prompt:**
Crude Roman timber marching camp, rough wooden palisade walls, dirt interior, simple gate. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Castrum T3
**Prompt:**
Grand Roman stone fortress with marble columns, tiled roof, carved eagle over gate, corner towers with banners. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Military Post T2
**Prompt:**
Roman military watchtower on a stone base, wooden upper platform, signal fire brazier on top. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Military Post T1
**Prompt:**
Crude Roman wooden watchtower, rough timber construction, simple observation platform. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Military Post T3
**Prompt:**
Ornate Roman stone signal tower, carved reliefs, bronze brazier, marble base, banner poles. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Resource Node T2
**Prompt:**
Roman quarry or mine entrance, stone-framed opening, wooden crane, stacked stone blocks, ox cart. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Resource Node T1
**Prompt:**
Crude Roman mining pit, rough timber shoring, piled earth, simple tools. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

### Resource Node T3
**Prompt:**
Grand Roman marble quarry, columned entrance, bronze-wheeled cranes, carved decorative stonework around the site. Flat angular faces, sharp clean edges, simple geometric shapes. Minimal detail.

---

## Environment

### Aqueduct Ruin
**Prompt:**
Collapsed Roman aqueduct arches, stone blocks, broken pillars. Flat angular faces, sharp clean edges, simple geometric shapes.

### Dry Stone Wall
**Prompt:**
Low Roman dry stone boundary wall, rough stacked stones. Flat angular faces, sharp clean edges, simple geometric shapes.

### Overturned Ox Cart
**Prompt:**
Overturned Roman ox cart, wooden wheels, scattered clay amphoras. Flat angular faces, sharp clean edges, simple geometric shapes.

### Olive Grove Trees
**Prompt:**
Small cluster of low olive trees, gnarled trunks, simple rounded canopies. Flat angular faces, sharp clean edges, simple geometric shapes.

### Forum Column Stumps
**Prompt:**
Broken Roman column stumps, marble bases, scattered capital fragments. Flat angular faces, sharp clean edges, simple geometric shapes.

### Milestone Marker
**Prompt:**
Roman road milestone, tall stone cylinder with carved text, simple base. Flat angular faces, sharp clean edges, simple geometric shapes.

### Triumphal Arch (T3 POI)
**Prompt:**
Roman triumphal arch, three openings, carved relief panels, Corinthian columns, inscribed top. Flat angular faces, sharp clean edges, simple geometric shapes.

### Temple (T3 POI)
**Prompt:**
Small Roman marble temple, Corinthian columns, triangular pediment, stepped base. Flat angular faces, sharp clean edges, simple geometric shapes.

### Clay Amphora Cluster
**Prompt:**
Cluster of Roman clay amphoras, tall pointed-bottom storage jars, stacked together. Flat angular faces, sharp clean edges, simple geometric shapes.

### Boundary Stone
**Prompt:**
Roman boundary stone marker, rough carved square pillar. Flat angular faces, sharp clean edges, simple geometric shapes.

---

## Tracking

| Weapon Props | T1 | T2 | T3 |
|-------------|----|----|-----|
| Gladius | | | |
| Spatha | — | | — |
| Scutum | | | |
| Pilum | | | — |
| Lance | — | — | |
| Bow | — | | |
| Standard | | | |

| Unit Body (T-pose) | T1 | T2 | T3 |
|---------------------|----|----|-----|
| Legionary (Vanguard) | | | |
| Equites (Raider) | | | |
| Velites (Interceptor) | | | |
| Signifer (Warden) | | | |

| Static Unit | T1 | T2 | T3 |
|-------------|----|----|-----|
| Ballista (Bombard) | | | |
| Castra (Bastion) | | | |

| Structure | T1 | T2 | T3 |
|-----------|----|----|-----|
| Castrum (Station) | | | |
| Military Post | | | |
| Resource Node | | | |

| Environment | Status |
|-------------|--------|
| Aqueduct Ruin | |
| Dry Stone Wall | |
| Ox Cart | |
| Olive Grove | |
| Column Stumps | |
| Milestone | |
| Triumphal Arch | |
| Temple | |
| Amphora Cluster | |
| Boundary Stone | |
