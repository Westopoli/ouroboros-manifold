# Menus mockup QA checklist

Placeholder. Filled with real measured numbers after the clean and planted Xvfb runs (build order step "smoke, checklist, screenshots, README").

| id | check | clean result | plant | planted result |
|---|---|---|---|---|
| DET-1 | resolve(0.9, medium, 11, T) twice equal; seed 12 differs; same seed same band | TBD | band-random | TBD |
| EDGES-2 | every allowed edge transitions; disallowed rejected with a reason; title to briefing direct rejected | TBD | flow-skips-setup | TBD |
| SETUP-3 | difficulty in campaign record; changes resolve score | TBD | difficulty-dropped | TBD |
| SECT-4 | briefing renders exactly Situation, Objective, Assets; attacker named | TBD | briefing-two-sections | TBD |
| DIGITS-5 | no digit in briefing or debrief text | TBD | digits-in-prose | TBD |
| BANDS-6 | finals map to five bands in order; monotone in parity | TBD | four-bands | TBD |
| WEIGHTS-7 | E-10 60-second example: o=1.0, r=0.67 -> final 0.9175, total_success | TBD | none | TBD |
| CONTROLS-8 | title controls exactly New Campaign/Continue/Settings/Quit; briefing exactly Accept/Refuse | TBD | none | TBD |
| CAMP-9 | two started campaigns listed with chapter/last_band; Resume reaches briefing | TBD | none | TBD |
| JSON-10 | qa_state() round-trips JSON with every key; qa_plant('nope') false; every PLANTS id true | TBD | none | TBD |

## Xvfb oracles

| id | oracle | clean | plant | planted |
|---|---|---|---|---|
| SCREENS-X | each screen screenshot differs from the previous, diff >= 0.05 | TBD | flow-skips-setup | TBD (setup == briefing) |
| BAND-X | resolve card crop contains the band colour named in state | TBD | four-bands | TBD |
| SECT-X | briefing screenshot has three heading crops | TBD | briefing-two-sections | TBD (third is background) |
| ERR-0 | errors.txt count, exit.txt, no UNIFORM | TBD | none | TBD |
| GPU-0 | _qa.adapter contains llvmpipe | TBD | none | TBD |
| DET-1 pixel | two clean runs match on hash and screenshots | TBD | none | TBD |

## Visual questions

| q | question | answer | proving screenshot |
|---|---|---|---|
| Q1 | title keeps the reference's shape | TBD | TBD |
| Q2 | briefing reads as orders, not a menu | TBD | TBD |
| Q3 | setup asks one thing, says the rest comes later | TBD | TBD |
| Q4 | band card readable in five seconds | TBD | TBD |
| Q5 | prose has the hub's dry wit, not cringe | TBD | TBD |
| Q6 | no clipped/overlapping text at 720p; no digits in prose | TBD | TBD |

**HELD:** TBD

## Timings

`timing_ms`, `fps_ms` under llvmpipe at 720p: TBD.
