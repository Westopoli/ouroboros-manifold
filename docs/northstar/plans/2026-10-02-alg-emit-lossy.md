# alg_constants.py --emit is lossy: diagnosis

Diagnosis only. Nothing was fixed; the evidence run wrote to a scratch file, not the repo.

## What happens

`--emit PATH` rebuilds the whole header from `docs/bible/algorithms.md` and overwrites PATH (`cmd_emit` calls `out_path.write_text(emit_header(...))`). It has no markers, no merge step, and no `--only` option. Its only modes are `--emit`, `--lint` and `--gen-allowlist`. `--lint` does not compare the header to the bible. It only checks `csrc/*.c` for bare numeric literals, and the merge gate runs it that way.

`csrc/om_constants.h` still says "GENERATED FILE -- do not edit by hand" on line 1, but it carries a hand-added part. Git shows two sources:
- Commit 48a3a0d7 (agora, CONST-1, 2026-09-26) added 154 lines: `OM_ALG21_*`, `OM_PCT_SCALE`, `OM_KNOWLEDGE_LOST_POP_WINDOW`, E-06 tech tiers, the E-09 `OM_CHRON_*` thresholds, `OM_MISSION_*`, `OM_BETRAYAL_*` and `OM_SIGNIFICANCE_*`. Some of these cite E-xx rules or Q-ids, not an ALG paragraph.
- Later commits such as 3f293bf8 (`OM_SAVE_FORMAT_VERSION`) did the same.

The F3b to F3f commits were different: they changed `algorithms.md`, then re-emitted. The leaf brief ("a value the bible pins in prose but the header lacks: a local #define") steers leaves away from the header, but CONST-1 and the save piece edited it directly anyway.

## Evidence

I ran `--emit` into a scratch copy with the 2026-10-01 bible (ALG-31 now reads (250, 400)), then diffed `#define` names against the committed header. 147 names exist only in the header, so the emitter drops them. 12 names exist only in the emission. Of those, `OM_WORLD_REGION_COUNT_RANGE_LO/HI` become 250 and 400, which is the intended change. The other ten are `OM_TACTICAL_TICK_RATE_*` and the ALG-76 `OM_OM_MACRO_*` pair; their names are doubled (`OM_OM_`), and the committed header has none of them. The Doer's figure of about 156 is the same drop, counted from a slightly different baseline. The emitter also reports 20 UNPARSED names, which are listed in its output.

## Answers

1. `--emit` regenerates the ALG-block constants only. It overwrites everything else, including the hand-added lines. Those lines live in the same file, with no fenced region.
2. This is a process gap, not an emitter bug. The emitter is documented as a whole-file generator and is deterministic. The header banner says not to edit by hand, and CONST-1 and the save piece broke that. The repo has no home for constants that come from epics or rules instead of an ALG paragraph.
3. Intended workflow for an ALG change: edit `algorithms.md`, run `--emit`, commit the regenerated header. That works only if every header constant is bible-derived. Today that is false, so the Doer's hand patch of `_LO`/`_HI` was the only safe move. Nothing checks the header against the bible: `--lint` and the merge gate never compare the two, so drift is invisible until someone re-emits.
4. Proposed fix, in order:
   - Move every hand-added constant to a new hand-owned header, for example `csrc/om_constants_extra.h`, included by `om_constants.h`'s consumers or at its end. Alternatively fence them in a `/* hand-maintained: begin ... end */` region that `--emit` copies through. The extra header is the lower-risk option because the generator needs no change.
   - Add a `--check PATH` mode that emits to memory and fails when PATH's generated part differs. Put it in `merge_gate.sh` next to the lint, so drift is caught at merge time.
   - Fix the `OM_OM_` double prefix in the ALG-76 names (the bible uses an `OM_` identifier, or the emitter should not prefix names that already start with `OM_`). It is a separate small change.
   - Owner: `scripts/specfactory/alg_constants.py`, `merge_gate.sh` and `tests/specfactory/` go to a harness piece. The move of the 147 constants is a header-contract change, since `csrc/om_constants.h` is a frozen-ish contract file, so it needs its own piece under M0 and `pieces.toml` ownership, and builds after it. Until that lands, an ALG change must be hand-patched into the header, as HDR5 did, followed by a `--check` run once it exists.
