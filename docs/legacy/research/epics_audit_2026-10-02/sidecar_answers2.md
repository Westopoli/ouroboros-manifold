# Sidecar: second set of answers, 2026-10-02 (Engineer, bible edit)

## Register rows for new flags

| Q-177-05 | E-22 / S-177, E-10 S-210 | At how many regions of supply distance (the number of regions between the mission's region and the nearest region the civilization owns) does the kind of base change: where does "next to an owned region" end and "deep in foreign ground" begin? | (a) 0 is owned, 1 is next to it, 2 or more is deep; (b) 0 and 1 generate on site, 2 and 3 are supplied, 4 or more live on shipments; (c) set per archetype in the library entry | open | |
| Q-193-04 | E-17 / S-193, E-02 S-222 | How much do dense districts slow units? | (a) a fixed fraction of speed per density step; (b) the existing obstacle field read at the density; (c) set per era kit | open | |
| Q-193-05 | E-17 / S-193, E-02 S-222 | How much cover do dense districts give? | (a) a fixed cover value per density step; (b) the existing cover field read at the density; (c) set per era kit | open | |
| Q-193-06 | E-17 / S-193, E-02 S-222 | How are natural paths through a settlement guaranteed for armies and units, so dense districts are never annoying? | (a) the generator leaves open streets along the contour lines and rivers by rule; (b) a route check on the finished district that opens a lane if none exists; (c) density never exceeds a cap on a lane the route grid names | open | |

## Register rows to close or reword (the register is not mine to edit)

- Q-159-14, Q-166-03, Q-210-01, Q-238-02, Q-241-03, Q-149-03, Q-119-02: closed by the answers; the register already says so.
- Q-166-04 stays open: its question is now how each number scales with step height, measured by the skill lab (the epics say this).
- Q-119-02 closed with "the layout library is not replaced"; Q-191-04 now asks how terrain and layouts combine (the epic text says this). The register text of Q-191-04 still says "Q-119-02 closing removes the library" and its candidates assume a generator without layouts. Reword it.
- Q-210-05 register text says "With no skeleton library". The epics now say how an archetype shapes a map made from layouts and terrain-first generation together. Reword it.
- Q-175-03 register text says "what a forward base consists of". Rename to "forward works" (E-22 S-175 title and rules).
- Q-242-03 register text mentions "a team of 6". The epic now says "a team of 4, and later of 6".
- Q-238-02 candidate (b) and its "how an arrived shipment is drawn" part were dropped with the closure. R-238-02 no longer says how an arrival is drawn.
- Q-241-03 closure: teams of 2 or 4 at launch, 6 a desired future feature.

## Catalog rows changed in stories.md

S-112 to S-119 (status text), S-147 (summary), S-175 (summary), S-176 (summary), S-177 (flags), S-178 (summary), S-193 (summary and flags), S-210 (flags), S-214 (flags), S-222 (flags), S-223 (status and flags), S-238 (flags), S-241 (summary and flags). S-175's title is now "Expansions and forward works" (epic heading; the catalog row has no title).

## Files changed (all under docs/bible/)

game_bible.md, stories.md, epics/E-01, E-02, E-03, E-08, E-10, E-14, E-15, E-16, E-17, E-18, E-19, E-20, E-21, E-22.

## Tested rules left with a note

R-112-01 to R-119-02 (all of S-112 to S-119) and R-073-03 keep their text. Their notes now say the layout library, the spine, the nine kinds, the gradients, the drift and the fairness check stay and terrain-first generation is added, with the combination at Q-191-04. S-118 gained such a note (it had none).

## Needs a ledger row

R-112-01 to R-112-06, R-113-01 to R-113-05, R-114-01 to R-114-05, R-115-01 to R-115-03, R-116-01, R-116-02, R-117-01 to R-117-03, R-118-01 to R-118-03, R-119-01, R-119-02, R-073-03: direction is now "stay, with terrain-first generation added", not "replaced". If the earlier ledger rows said "replaced", they need correcting.

## Findings resolved

1. Supply distance: done. E-03 S-223 holds the definition; E-22 S-177 (R-177-03, Inputs, table) and E-10 S-210 (R-210-01, Inputs, table) cite it. Thresholds flagged as Q-177-05.
2. Density field: done. E-17 R-193-08, new R-193-09, Invariants, Outputs, Ways; E-02 R-222-03. Flags Q-193-04 to Q-193-06.
3. Fitted bands: done. E-17 R-188-04; E-01 gate row, S-004, S-005, reach story, S-200 flag lines and R-200-01. Q-166-04 stays open.
4. Counter what has been seen: done. E-22 R-179-06 and R-180-06.
5. Names: done. "Forward works" in E-22 S-175 (title, R-175-03, R-175-04), S-178, E-10, E-14, E-15, E-16, hub. "Forward base" kept for the attacker's starting base. Cap note in E-10 R-212-01 and E-22 R-178-06.
6. Q-210-01: done. E-10 R-210-02, flags.
7. Layout library: done, see above. E-17 Purpose, 60-second test, S-186 (R-186-03), S-191, S-192 (R-192-02 flag), S-197, Inputs, Outputs, Invariants, Ways, Depends; E-10 S-073 note; E-21 R-153 flags paragraph.
8. Blind shipments: done. E-22 R-176-02, R-176-03, Outputs; E-18 R-238-02.
9. Peers: done. E-19 Purpose, R-141-01, R-159-01, R-241-01, R-241-04, Inputs, Scale; E-08 S-228; E-10 S-214; E-17 Inputs; hub. The 64,000 wu canvas rule for "4 to 6 players" is Westley's verbatim number and was left.
10. Price: done. E-20 Purpose, S-147 (R-147-01), S-149 (R-149-01, R-149-02), gate; E-21 purpose; hub Monetization.

## Could not do or left

- E-14 R-215-03 and R-215-05 say an enemy economy with foresight off never counter-shifts production. E-22 R-179-06 now says the rules counter what the commander's forces have seen as the one exception. Whether that exception covers the enemy's economy with foresight off is not decided. Left as written, flagged here.
- Whether the supply distance is counted as hops (E-03 R-223-01) or as the regions strictly between is not stated by the decision. S-223 uses Westley's wording and leaves R-223-01 as it was.
- E-17 gate counts (30 new flags, 29 in the terrain-first stories) are recounted from the Open ambiguity flags list. The earlier counts (26 and 25) did not match that list.
- The "4 to 6 players" wording in E-17, E-10 and E-22 stays. Since teams of 6 are a future feature, only 4 players falls in that range today.
