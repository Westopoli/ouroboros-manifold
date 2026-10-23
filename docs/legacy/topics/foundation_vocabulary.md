---
name: Foundation Vocabulary Scan
description: Thematic vocabulary scan for Foundation/hard-SF tribe register vs heroic/empire-building register. Informs progression/achievement/goal-legibility forks in Design Lane WS5.
type: topic_brief
captured_at: 2026-05-17
contributor: Research Lane Q3 capture
---

# Foundation / Hard-SF Vocabulary Scan

## What this brief is

A vocabulary scan distinguishing the Foundation / hard-SF literary register from the heroic / empire-building register that dominates the generational/legacy strategy genre. Ouroboros' niche target includes a Foundation/hard-SF tribe (r/asimov, r/printSF, r/IsaacArthur) as the secondary thematic differentiator on top of the primary generational-strategy intersection. Vocabulary choices in progression UI, achievement names, goal labels, and chronicle prose encode which tribe the game is signaling to.

This brief does not pick which register Ouroboros uses where. The Design Lane decides on a fork-by-fork basis (Forks 2, 5, 6, 9 in WS5). The brief surfaces the two registers, their semantic load, and the games / texts that anchor each.

## Method

Source-scanned: Asimov's Foundation cycle (1942–1993) for the cyclical/predictive/archival lexicon; Vernor Vinge, Olaf Stapledon, Isaac Arthur YouTube channel for adjacent hard-SF tribe vocabulary; CK3, Wildermyth, Battle Brothers, Old World UI text + achievement lists for the heroic/empire-building lexicon. No primary surveys — this is a register characterization, not a tribe preference study.

## The two registers

### Heroic / empire-building register (genre default)

Verbs: **conquer, forge, rule, claim, build, expand, defend, lead, vanquish, ascend, found, restore, glorify**. Nouns: **dynasty, lineage, kingdom, empire, throne, banner, conquest, glory, legacy, hero, founder, ancestor, heir.** Tense and framing: imperative ("Forge an empire!"), present-active, you-do-the-thing.

Anchors: Crusader Kings 3 achievement names ("World Conqueror," "Mongol World Conqueror," "Restoration of the Roman Empire"); Wildermyth chapter titles ("The Brigands of Bremen," "The Coming of the Morthagi"); Battle Brothers crisis names ("The Greenskin Invasion"); Old World ambition system ("Conquer X cities," "Found Y wonders").

Semantic load: agency, conquest, person-as-protagonist, civilization-as-project, time-as-arrow-of-progress.

### Cyclical / predictive / archival register (Foundation tribe)

Verbs: **observe, predict, calculate, project, record, catalogue, archive, model, anticipate, preserve, recur, cycle, repeat, mirror, foresee, encode, transmit**. Nouns: **cycle, era, epoch, archive, codex, register, chronicle, sequence, projection, model, pattern, fall, decline, recurrence, foundation, vault, fragment, transmission, repository, observer.** Tense and framing: past-perfect ("had risen and fallen"), passive-observational ("The Third Cycle ended in..."), the-thing-happened-and-was-recorded.

Anchors: Asimov's Foundation — psychohistory, the Encyclopedia Galactica, the Seldon Plan, the Mule, the Second Foundation. Stapledon's Last and First Men + Star Maker — civilizational rise/fall at species scale. Vinge's Marooned in Realtime — bobble-archived observers across geological time. Isaac Arthur — futurism vocabulary (Dyson, K-scale, megastructure, posthuman, far-future). RimWorld archotech relics + lore tabs lean this direction. Stellaris fallen-empires lore leans this direction.

Semantic load: pattern over event, system over person, time-as-cycle, civilization-as-specimen, observer/recorder as protagonist not actor.

## Cross-register patterns

- **"Legacy" sits between.** Used heavily by both registers — heroic ("my legacy as king") and archival ("the legacy of the Third Empire's collapse"). Not a tribe signal on its own.
- **"Founder/foundation."** Heroic register: a person who founds. Foundation register: an institution that preserves. The same word, different semantic load. Useful in Ouroboros' niche specifically because both readings work.
- **"Era" vs "age" vs "epoch."** Heroic register prefers "age" (Age of Discovery, Age of Iron). Foundation register prefers "epoch" (the Encyclopedia Galactica records epochs). "Era" is neutral. Era-naming is a tribe-signal lever in Fork 6 (era unlocking shape).
- **"Chronicle" already chosen.** Ouroboros' bible already names the persistent-narrative-record system "Chronicle." This is solidly in the Foundation register — chronicle vs. ledger vs. saga vs. annals. The choice is already a tribe signal.

## Tribe-signal levers in WS5 forks

Bringing the vocabulary scan into the design forks:

- **Fork 2 (Victory condition).** Heroic register implies hard-victory screens with conqueror titles. Foundation register implies cyclical or observational endings ("The Cycle Closes," "The Archive Endures") or anti-victory by design. The pick on victory-vocabulary is a register pick.
- **Fork 5 (Achievement philosophy).** Steam achievement names are the most visible vocabulary surface. Heroic names ("Conqueror of the Settled Reach") vs. archival names ("Recorded the Fall of the Third Cycle") signal hard.
- **Fork 6 (Era unlocking).** "Unlock the Age of X" vs. "Witnessed the Onset of Epoch N" are different sentences. Era-naming convention is a load-bearing choice.
- **Fork 9 (Goal legibility).** Heroic register supports explicit goal panes ("Goal: Conquer 5 regions"). Foundation register supports emergent-after-the-fact framing ("The chronicle will reveal what was significant"). The legibility-vs-opacity trade-off and the register choice are entangled.

## What is already built and which register it sits in

- **Chronicle.** Foundation register (chronicle = archival noun).
- **Settled Reach** (world name). Slightly Foundation-leaning ("reach" implies extent and edge, observer-oriented; "settled" implies an objective rather than a heroic claim).
- **Tier system, region/faction language.** Genre-neutral; not a register signal.
- **Lieutenant System.** Currently genre-neutral noun. The personality system + named lieutenants will inevitably pull toward heroic register in player-perception unless Ouroboros explicitly frames lieutenants in observational/archival vocabulary (e.g., the chronicle records what each lieutenant did; the player commands but does not become them).
- **Currently no era names exist.** Era system is greenfield — Fork 6 chooses both shape and vocabulary register.

## Cross-cutting findings

- **Ouroboros' niche-target intersection means register choice is per-surface, not per-game.** The generational/legacy tribe accepts heroic register; the Foundation tribe requires archival register. Mixing per-surface (chronicle = archival, lieutenant names = heroic-tolerant) is a viable strategy but consistent register inside any one UI surface matters more than register choice across the game.
- **The most legible Foundation-register lever is achievement naming.** Steam reviewers and the Foundation tribe both pattern-match on achievement lists. Heroic achievement names will read as "yet another empire-builder" to the Foundation tribe regardless of how Foundation-coded the rest of the game is.
- **"Chronicle" is already a Foundation-register anchor; the game is partly committed.** Renaming away from chronicle would be costly and would weaken Foundation-tribe signaling. Decisions in adjacent forks should treat chronicle as a fixed Foundation-register node and design outward from it.

## Caveats

- This is a register characterization, not a tribe-preference survey. No reader-side data on which register Ouroboros' actual target audience prefers — only on which register the source material uses. Confidence on register characterization: VERIFIED. Confidence on tribe-preference inference: ESTIMATED.
- The two registers are not mutually exclusive — a single game can use both at different surfaces. Per-surface register discipline matters more than global purity.
- Foundation/hard-SF tribe is heterogeneous. The Asimov reader subset prefers cyclical/predictive vocabulary; the Isaac Arthur viewer subset prefers far-future/megastructure vocabulary; the Vinge reader subset prefers observer-archive vocabulary. Per-tribe vocabulary fine-tuning is out of scope for this brief.

## Feeds Design Lane

This brief feeds Design Lane WS5 Forks 2 (victory), 5 (achievements), 6 (era unlocking), 9 (goal legibility), and any future fork where UI-text or labeling decisions are made. It does not pick a register for any fork. The Design Lane decides per fork.
