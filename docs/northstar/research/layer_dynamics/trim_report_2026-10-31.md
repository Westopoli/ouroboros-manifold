# Simulation lab: architecture and trim report (Architect, 2026-10-31)

Westley asked: "How is the simulation lab architected? It seems like a relatively small/straight-forward piece of software in my mind, yet it's taking weeks to build. I'm wondering if there are things that we're including that aren't necessary to measure/produce relative to the goal of the simulation lab." Inventory by a read-only Sonnet engineer over main 559e0a25; judgements are the Architect's; Westley rules at the end.

## How it is built today

Six layers. (1) Engine bridge: the C sim through ctypes, one fight stepped by tick, trace rows, a process pool; about 1,200 lines; sound. (2) Setups: fourteen scripted plays with five skills, ten roster mixes, hand-built scenes, formations, a space-map sampler, pre-flight refusals; about 1,700 lines. (3) Measurement: an enemy-headcount scan against a fixed 16, break-even refinement, eight knob-sweep families, firing-count predictions over a 40-tick window; about 1,400 lines. (4) Judgement: conditions C0 to C9 with pass marks, the 32-subset skill-stacking profile, naive baselines, a ceiling marker, decision-tree and region tools; about 1,000 lines. (5) Output: HTML page, charts, an SVG per notable layout; about 1,100 lines. (6) The 2026-10-30 lane from Westley's words: unit scale scene H-023, replay and snapshots H-024, layout catalogue H-025; about 700 lines plus Godot scenes.

Totals: 51 code files, 8,767 lines; 190 test files, 41,059 lines; about 500,000 lines of committed run data under `runs/` and `catalogue/` although section 9 of the README says nothing generated is committed; about 20 plan documents. 338 commits since 2026-10-02. One real batch ever ran (layout run 1, 2026-10-08); its chart was never shown to Westley.

## Why it took weeks

Not the fight runner. The question changed: the lab was built to answer "does layer skill beat numbers in space, over fourteen plays, with pass marks", and Westley's 2026-10-30 words ask "where does positioning stop deciding, on land, on layouts I approve, shown as snapshots". Layers 2 to 4 answer the old question. Batch one was gated on seven things (E2 and E4 engine pieces, vision plays, Rev 3 C, R9 re-engagement, goldens, xdist, speed marks, unit scale), none of them a layout he could look at. And the spend went to tests, docs and data: 41k test lines, 24k doc lines, 500k data lines against 8.7k code lines.

## What the goal needs (keep)

Fight on the real sim, deterministic (done). Layouts Westley approves with a predicted winner (H-025 round two, in build). Headcounts 8 to 256 each side, both varied (decided; the code still scans 8 to 48 against 16). Ten to twenty snapshots per fight, 3D, with positions, facing, layer and type (H-024, built, held on the eyes gate). Unit scale locked first (H-023 landed; his tuning session pending). A picture per crossing with the findings beside it (the report layer exists and is re-pointed at snapshots).

## Not needed for that answer

Conditions C0 to C9 and pass marks (about 450 lines; the marks were never his, DEC-Q156). The skill-stacking profile (about 200). The fourteen plays, ten mixes and five-layer space plays (about 900; Architect drafts). Naive baselines and the ceiling marker (about 300; the ceiling is already retired by DEC-lab-no-ceiling). The eight knob-sweep families (about 750). The ping search scene (about 720; nobody fires, unreachable from the CLI). Region search, decision tree, transfer, guard, mapreport (about 290; on no CLI path). Layout run 1's sampler and the 500k data lines (superseded by hand-approved layouts). The queued engine-behaviour pieces LAB-REV2 E2, E4, L7B and LAB-REV3 B, C: they change fights, not positioning, and can wait for the first crossings. About 4,000 of the 8,767 code lines and most of the 41k test lines serve the old question.

## The trimmed path to the first answer

1. H-023: Westley's scale session; values written. 2. H-025 round two lands; he approves a batch of layouts. 3. H-024 lands; snapshots are the output. 4. One new small story: run each approved layout across a headcount grid (8 to 256 both sides, DRAFT 8 points a side: 8, 16, 24, 32, 48, 64, 128, 256), record the winner and the snapshot set, emit the crossing picture per layout; reuses layers 1 and 5 only. 5. A findings page per layout: his prediction against the sim's winner, the crossing, the snapshots. Everything else stays in git history.

## Rulings Westley is asked for

1. Park layers 2 to 4 (plays, conditions, skills, sweeps, baselines, search) and their tests: removed from the CLI and the test runs, kept in history.
2. Park the queued engine pieces until the first crossings exist.
3. Delete the committed run data (keep the 2026-10-08 chart as history).
4. The headcount grid of step 4 (8 points a side is the Architect's draft).
5. Whether the first batch runs only on land presets, with vantage and slope as the only height features.
