# The economy: ten things that are yours to rule before it is built (2026-11-08)

You asked whether the economy is defined well enough to build before the beta staircase reaches it. Most of it is: the three resources, the workers, the one cap, the families, the bases, the doctrines, the shipments, the enemy on your rules. Ten things are not, and each would show up in play. For each, say the letter, or your own words. Everything else found (the engine's traps, the stage list) was decided by the Architect and logged; you may veto any row by a word. The full investigation is `docs/reports/2026-11-08-economy-readiness.md`.

Not urgent: nothing here blocks the lab or stages B2 to B8. Rule before the first economy stage is planned.

| # | What you would see in play | Your options |
|---|---|---|
| 1 | **The dial.** Alone in command, you have one control for how your base spends: on growing, on technology, on the army. What is it? | (a) three positions per axis (low, even, high); (b) one slider per axis; (c) one point you drag inside a triangle whose corners are economy, technology, army |
| 2 | **Who builds.** You see a house go up. Did a worker walk off the fields to raise it, or did it rise on its own while every worker kept gathering? | (a) workers build: one worker per site, two finish in half the time, and the site stalls with nobody at it; (b) buildings rise alone, paid at placement, and workers never leave gathering; (c) workers build in the paired seat, buildings rise alone when the rules run the base |
| 3 | **Where each resource comes from.** You watch workers at the sources. What are they standing at for Food, for Wood, for Coin, and which of those run out? | (a) Food from forage patches that run out and farms that do not; Wood from stands that run out and a lumber yard that does not; Coin from mines that run out and a market or mint that does not (every resource has a wild and a built form); (b) Food and Wood as in (a), Coin only from finite mines and from trade (caravans and shipments), never built; (c) your own split. And the main base's slow decline ("never runs dry but yields less"): (i) each built source yields less the longer it has run, down to a floor; (ii) the base's whole income declines by age; (iii) only wild sources run out and built sources never decline (then the sentence is wrong) |
| 4 | **Technology in the beta.** Your dial has a technology corner. Does it do anything before the beta is done? | (a) out of the beta: the dial has two corners (economy, army) until technology is designed; (b) in, minimal: one level up per match, and a level is a flat upgrade to every unit's hit points and damage (a number you set); (c) in, as written: a wide ladder of levels, each doing something you design now |
| 5 | **Whose hands in the beta.** The staircase's economy stages are judged by you alone in command: the dial, the doctrine, the three requests, the two switches. The second player's hands-on economy (placing buildings, planning the timelines, picking technology, disguising) comes with multiplayer. Agree? | (a) yes, the solo hand only, the paired seat after the staircase; (b) no, the paired seat's screen is a stage of the staircase too, after the production line |
| 6 | **Taking a town, losing a base.** A neutral town becomes yours after you hold it "uncontested for a time"; your base is "occupied" when the enemy "holds its central zone for a time". What does the game count? | (a) one rule for both: no enemy soldier within a fixed radius of the town's or base's main building for a fixed time (draft: 1,200 wu and 2 minutes for a town, 800 wu and 1 minute for a base), and the base is taken when, on top of that, its main building is destroyed or captured as the mission type says (draft column: destroyed in Assault and Reconquest, captured elsewhere); (b) different radii and times per mission type, a table you fill; (c) your own reading |
| 7 | **The villagers of a town you won.** The rule says they "become part of the winning team". | (a) they become your workers: they gather for you and count against your cap; (b) they stay the town's people: you get its lots, its yields and a place to build, and your cap is untouched; (c) a share of them become workers (a number) and the rest stay |
| 8 | **Seeing your own shipment.** On 2026-10-02 you said your side cannot see its own shipment on the way, no vision at all. On 2026-10-06 you said a shipment is visible on the map to both sides like any unit, gives its own side no vision, and nobody is told when it dies. The epics carry both. Which stands? | (a) 2026-10-06: both sides see it on the map where they have sight, it sees nothing itself, no word when it dies; (b) 2026-10-02: the receiving side never sees it at all, only the enemy can |
| 9 | **Two frame rates.** One epic says 60 frames a second with 1,000 units on screen; another says a 30 frames a second floor at 1,000 units with reduced detail. Both are dated to you on 2026-09-14. | (a) 60 at 1,000 is the mark, 30 is the floor the game must never cross under load; (b) 30 at 1,000 is the mark, 60 is for 200 against 200; (c) your own numbers |
| 10 | **The numbers.** Nine economy quantities were closed on 2026-10-21 as "a draft you tune by feel", and no draft was ever written, so no test can be written. Below is one table of drafts, anchored on what you already set: a mission runs 30 to 60 minutes, and the starting force is about a fifth of what a full mission fields, production paying for the rest. | (a) approve the table as drafts, you tune by feel in the stage you play, every change logged; (b) amend rows now, then (a); (c) you write your own table |

## The draft table (item 10)

Every value is a draft until you rule; each becomes a `DRAFT-econ-*` constant with your verdict beside it. Walk speeds are the roles' own. Prices use the ground era's names; the space era maps one to one (Metal for Food, Water for Wood, Uranium for Coin).

Pacing anchor: a side starts with about 50 to 80 soldiers and must be able to produce 200 to 300 more over a 40-minute mission, about 6 units a minute at full flow. At the prices below that is about 1,200 resources a minute, which 60 workers deliver at 20 each.

| Quantity | Draft | What it means in play |
|---|---|---|
| Worker | trains in 15 s at the main building, costs 50 Food, carries 10, counts 1 against the cap | a worker is cheap and quick, and losing ten hurts the flow for a minute |
| Starting workers | 12 per base, 6 at a forward base | the base starts gathering at once |
| Workers the rules keep | boom 80, balanced 60, fortify 50, press 40 | the doctrine shows at the sources |
| Yield by walk | full 10 within 300 wu of a drop-off; minus 1 per further 100 wu; floor 4 at 900 wu and beyond | a far source is worth less than half a near one, so drop-offs matter |
| Wild sources | a forage patch holds 1,500 Food, a stand 2,000 Wood, a mine 1,000 Coin; a worker gathers 10 per trip, trip time by distance | a patch feeds twelve workers for about 15 minutes |
| Built sources | a farm or yard yields 10 per trip forever, half a wild patch's rate until the patch is gone; the main base's built sources lose 5 percent of yield every 5 minutes down to a floor of 50 percent | the switch from foraging to farming is a timing; staying home slowly starves |
| Expansion sources | wild patches at 60 percent size, no decline, no built sources except by the owner's placement | quick to take, quick to fizzle |
| Population | Strike and Line soldiers weigh 1, Siege 2, workers 1; starting cap 40; a house adds 10; ceiling 2,000 | the cap is hit in the first minutes unless housing is ahead |
| Housing | costs 60 Wood, rises in 20 s | the rules build the next house at 80 percent of the cap |
| Drop-off | costs 80 Wood, rises in 25 s | one per cluster of sources |
| Production building | costs 150 Wood and 50 Coin, rises in 45 s, one per 15 workers under the rules | a base of 60 workers runs four lines |
| Construction | rises alone in five stages (item 2 may change this), paid at placement | a placed building is a visible promise |
| Unit costs | Strike roles 60 Food and 40 Wood; Line roles 50 Food and 60 Wood; Bombard 80 Wood and 60 Coin; Bastion 80 Food and 60 Coin | heavy Coin gathering means siege is coming |
| Unit build time | Strike 20 s, Line 25 s, Siege 40 s, one at a time per building | a line makes about three Strike a minute |
| Family change | 30 s retool, the building idle meanwhile | changing your mind costs a unit and a half |
| Timeline | 5 minutes ahead per building; a planned slot changes free before it starts; changing the running item loses its progress | the economy player thinks five minutes ahead |
| Wall | 10 Wood per 100 wu segment, rises in 8 s, 1,000 hit points, blocks every unit | a lane walled in a minute |
| Gate | 30 Wood, 15 s, 600 hit points, opens for its side, shuts when an enemy is within 200 wu | your workers pass, raiders do not |
| Tower | 120 Wood, 40 s, 800 hit points, fires at 600 wu with a Line role's damage, spherical range | one tower holds a lane against a small raid, not a push |
| Doctrine spending (economy / technology / army) | balanced 40/20/40; boom 60/15/25; fortify 35/15/50 plus walls and a tower on each own lane; press 25/15/60 plus forward works at the first expansion | the dial moves these by up to 20 points per corner |
| Standing habits (every doctrine) | no worker idle; a house at 80 percent of the cap; a drop-off per source cluster; a production building per 15 workers; expand when the main base's yield has fallen 25 percent; retool a line only when the target mix is off by a whole unit | perfect hands, no foresight |
| Counter shift | after 5 enemy units of one family are seen, the next production slot of the countering family is doubled, decaying over 2 minutes | what you have seen changes what arrives |
| Requests | expand here: the nearest settlement or source cluster within 1,500 wu of the mark; fortify this pass: walls across the lane's narrowest 300 wu within 600 wu of the mark plus one tower; siege at this gate: the next three Siege units walk to the mark | the ticker says which and when, from these times |
| Caravan | walks base to settlement and back, pays 5 Coin per 1,000 wu of route per round trip, 400 hit points, no vision | long routes pay and bleed |
| Shipment | one per 8 minutes from the civilization, 300 of each common and 100 of the rare, walking from the map edge nearest the home region at a worker's speed | waiting for one is a risk |
| Promotion and occupation | see item 6 | |
| Engine budgets | economy step under 2 ms with 400 workers and 2,000 lots at 1,000 units; worker route cache hit above 95 percent; 20 wall segments in 20 ticks keep movement under its 3 ms budget | the base never slows the fight |

Rule of record: these are the Architect's drafts for your verdict (CLAUDE.md, "Westley owns every threshold"). Your answers are written as `Decision:` rows and the epics' rules carry the values the same day.
