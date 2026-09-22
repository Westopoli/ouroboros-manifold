# card_lint.py run over every regenerated card

`scripts/specfactory/card_lint.py` run against every one of the 164
generated cards under this directory, `--project` the real
ouroboros-manifold checkout, `--queue` the real
`/home/westopoli/Projects/agora/queue` (read-only; nothing here was ever
written to that queue). Expected per the task: `MISSING_SNIPPET_FILE` (the
skeletons live on branch `skeletons-e03-e17-clean`, not on `main`) and/or
`ABI_GAP` (every real per-story symbol is genuinely undefined anywhere in
`csrc/*.c` today) for every card, since none of the 12 target modules exist
on `main`.

## FAIL counts across the 164 cards

| Code | Count | Expected? |
|---|---|---|
| MISSING_SNIPPET_FILE | 162 | yes (every card whose module doesn't exist) |
| ABI_GAP | 877 | yes (every genuinely unbuilt symbol) |
| SPANS_ANOTHER_CARD | 8 | **no -- real finding** |

(2 of 164 cards report `MISSING_SNIPPET_FILE` differently: see "no
acceptance commands" below, which short-circuits before the module-file
check can even run for the file that has zero commands.)

## Real finding 1: `SPANS_ANOTHER_CARD` (8 findings, 6 distinct symbols)

Every one of these is a cross-epic ownership collision also recorded in
`cross_epic.md`'s "Beyond the 12-epic scope" section -- a symbol this run's
card claims to build that a real, live E-04 or E-05 queue card already
claims:

- `213a-e03-worldgen-routes_carry_armies_trad`: `om_tick_friction`
  (owned by `206-e05-friction-admin`, a `.superseded` E-05 card that
  `card_lint`'s alphabetical scan happens to name first -- the real live
  owner is `206a-e05-border-friction.md.hold`; `card_lint`'s
  `find_owning_card` returns the first match it iterates, not necessarily
  the live one, a pre-existing tool quirk, not something this task touches)
- `220a-e06-diplomacy-three_ways_to_feel_about`: `om_tick_friction` (same)
- `223a2-e06-diplomacy-a_faction_s_technology_i`: `om_tick_events`
  (owned by `208b-e04-triggers`, superseded; live owner
  `208b3-e04-revolts-and-deltas.md.hold`)
- `230a-e07-lifecycle-a_revolt_can_birth_a_nat`: `om_event_queue_external`,
  `om_tick_pruned` (owned by `209-e04-queue-chains`, superseded; live
  owners `209c-e04-chain-spawns.md.hold` / `209b-e04-queue-resolution.md.hold`)
- `231a-e07-lifecycle-old_loyalties`: `om_event_queue_external` (same)
- `256a3-e09-chronicle-the_fragment_library_con`: `om_event_template_count`,
  `om_events_load_launch` (owned by `208a-e04-library`, superseded; live
  owner `208a-e04-library-load-readback.md.hold`)

Not decided here (see `cross_epic.md` for the full write-up and candidates).

## Real finding 2: two cards with zero acceptance commands (`card_lint` exit 2)

- `E-12/283a1-e12-fog-recon_then_fog.md`
- `E-15/313a1-e15-support-units_that_cannot_fight.md`

Both stories (S-092, S-129) have a test whose own symbol closure is wider
than one 5-symbol card, so under this tool's own "a test whose closure
spans later cards is listed under the last card it needs" rule, the whole
test lands on a later card and the earliest card in the split ends up with
symbols but no acceptance test of its own. `card_lint.py` treats an empty
`acceptance:` list as a parse error (exit 2, "no acceptance commands"),
not a FAIL finding -- a genuinely broken card as things stand. See each
story's own `report.md` ("Cards with no acceptance test of their own") for
the design-lane candidates; not decided here.

## Everything else: `LINT OK` modulo the two expected codes

No other FAIL code appeared. `SNIPPET_SYMBOL_UNDEFINED`, `CONST_ONLY`,
`BAD_NODE_ID`, and `SIZING_SYMBOLS`/`SIZING_LINES` never fired (sizing caps
were respected by construction; no card names a bad pytest node id since
every acceptance line was built from a symbol/test the tool itself parsed
out of the same test file).
