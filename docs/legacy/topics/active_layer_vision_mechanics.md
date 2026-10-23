---
name: Active Layer Vision Mechanics
description: How shipped games make a player act to see, hide in, or use a layer or region — priced reveal abilities and cheap scouts, sensing that gives the sensor away, and games with stacked layers, depths or altitudes — and what the evidence says about whether that adds depth. Gathered for register flag Q-005-03 (the layers need an action from the player).
type: topic_brief
captured_at: 2026-10-01
contributor: Research Lane, queue Q78; three gathering sub-agents, brief written by the main chat
---

# Active Layer Vision Mechanics

## What this brief is

Requested by Westley on 2026-10-01 with his sketch of a targeted ping (select units, choose the ping, press a layer number, click a place, get a very short burst of vision there; free scouts in eras without the technology). It reports what shipped games do. It makes no design recommendation. Feeds register flag `Q-005-03`.

Full report with every source link: `docs/research/reports/Active layer vision mechanics.md`. Gathering notes: `docs/research/research_notes/Active layer vision mechanics/` (three files). Tags: VERIFIED (read in a primary or authoritative source), REPORTED (secondary), ESTIMATED (the notes' own derivation), AMBIGUOUS (sources disagree).

One limit applies to everything below: there is no telemetry, experiment or developer postmortem in the material on whether forcing an action adds depth. Every judgment of depth is a reviewer's, player's or wiki author's opinion.

## 1. Paid reveals: common, exactly priced, thinly praised

- **StarCraft II Scanner Sweep.** 50 energy, any point on the map, radius 13, 12.3 seconds, reveals cloaked and burrowed units. The same 50 energy buys a MULE worth about 225 minerals, so a scan is paid for in income. [VERIFIED on a community wiki] Brood War's Comsat uses the same cost but stores up to four scans. [VERIFIED for cost; duration AMBIGUOUS]
- **Dota 2 Scan.** A team ability: 900 radius, 8 seconds, answers only "is any enemy hero here", no count and no identity, and the enemy is not told. Started on a 4.5 minute cooldown; now two charges at 210 seconds. [VERIFIED for the original; later values REPORTED]
- **Wards (Dota 2, League of Legends).** Placed, persistent vision (a Dota observer ward lasts 360 seconds) with a separate, rewarded game of finding and removing the enemy's. Riot scores both vision provided and vision denied. [VERIFIED]
- **Homeworld Remastered.** The nearest match to the sketch. A passive sensor array became select-and-press: a ping shows enemies for a few seconds. One player called it a downgrade from always-on; no developer reason was found. [REPORTED; numbers AMBIGUOUS]
- **Company of Heroes 2, World in Conflict.** Short recon sweeps bought with a scarce resource. A fan guide calls the CoH2 sweep "lackluster"; a fan summary calls World in Conflict's aerial recon "mostly regarded as a waste of points" because units that scout persistently see more for longer. [VERIFIED and REPORTED as community opinion]
- **Cheap scouts.** None is free in everything. The StarCraft II Changeling costs no minerals, gas or supply but needs an Overseer and its energy; its counter is the opponent noticing it. [REPORTED]

Pattern in the complaints, as the notes read it: a short reveal priced in a scarce resource loses to a persistent scout that does the same job. [ESTIMATED]

## 2. Sensing that gives the sensor away

- **The real rule.** An active sonar pulse reveals the emitter at about twice the range at which it can itself detect; a radar's echo falls with the fourth power of range while an interceptor hears the pulse falling with the square. "Twice" is a rule of thumb. [VERIFIED as stated by Wikipedia; ratio ESTIMATED]
- **Submarine games.** Going active trades secrecy for a fast fix. Cold Waters players: the pinged side gets a bearing line, and "the moment I go active they launch on me". [REPORTED]
- **Fleet games.** Nebulous: "It's either Stealth or detection"; radar off leaks nothing electronic and blinds some missile seekers. HighFleet: radar has graded modes (continuous, single sweep, sector, off) and passive receivers hear a radar at 1.4 to 2 times its range. [REPORTED]
- **Starsector's Active Sensor Burst.** The clearest short, player-triggered burst with a stated cost: a large jump in sensor strength and a larger jump in the fleet's own visibility, a one-day cooldown, the fleet slowed, and hostile fleets come to investigate. Players use it as bait. [VERIFIED on a community wiki]
- **EVE Online.** The free, constant scan does not warn the target; the precise probes are visible to it. [VERIFIED]
- **Supreme Commander, Beyond All Reason.** Intel is split into channels: vision identifies, radar gives unidentified blips that are inaccurate to shoot at, sonar sees underwater, stealth hides from radar and cloak hides from sight. Jammers cost upkeep. [VERIFIED for Beyond All Reason; Supreme Commander REPORTED]

How a scan warns its target differs in every game: a bearing line, a flag on the contact, a visible probe, or the enemy AI coming to look. [ESTIMATED]

## 3. Games with stacked layers

Layers that changed play each came with an explicit rule, a cost and a named counter:

- **The submarine thermal layer.** Which side of the layer you are on decides who can hear you: go below it to hide from a surface ship, above it to hide from a deep submarine. Depth costs noise at speed. Some sensors can be lowered across it. [VERIFIED as player statements; details AMBIGUOUS]
- **Supreme Commander and Beyond All Reason.** Five engine layers in Supreme Commander (seabed, submerged, water, land, air). Each weapon lists which layers it can hit from which layer. Counterplay comes from units that cross layers (torpedo bombers, amphibious tanks) and units that sit where most weapons cannot reach (hovercraft cannot be torpedoed). Sonar is rarer and shorter-ranged than sight. [REPORTED for Supreme Commander; VERIFIED for Beyond All Reason] The water layer went underused in Forged Alliance until it held resources worth fighting over. [VERIFIED, one review]
- **StarCraft II high ground.** Ground units cannot see up a cliff; a low-ground army "can be ambushed and cannot counterattack unless vision is gained" by a flyer, a scan, or a unit on the ledge; firing from above reveals the shooter. [REPORTED]
- **Wargame helicopters.** Three altitudes: high sees and shoots over cover but is easy to spot, low hides behind terrain. Players complain that helicopters drop altitude on their own. [REPORTED]
- **Planetary Annihilation's orbital layer.** Reviewers split between "the strongest system" and a forced layer with tedious transport. Units arriving in orbit cannot act for several seconds, which is the defender's window. [VERIFIED as opinions]

Reasons a layered or 3D battlefield was judged a gimmick [ESTIMATED from a handful of opinions]:

1. The camera and the unit AI absorb the extra axis (Homeworld 3: "it seldom comes up in actual gameplay").
2. Nothing strategic depends on it (Falling Frontier players: a flat map gives chokepoints to work with).
3. The game chooses the altitude for the player (Ancient Space).
4. Using the layer feels like a tax, or the layer holds nothing worth contesting.

Homeworld players disagree on whether the vertical axis matters: "by no means CRITICAL" against "a good player will slip a fleet above or below you". [AMBIGUOUS]

## Gaps

No game found with five stacked layers and a targeted per-layer vision burst, or with free scouts only in eras lacking the technology. No developer statement on any cited change. No case of a shipped game removing an active reveal for being busywork. Many wiki pages were blocked, so a share of the REPORTED items rest on search summaries. Not found: Halo Wars reveal powers, Harpoon altitude rules, usage data on how often players change layer in any game.
