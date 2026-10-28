# Method rev 3 rule text, landed 2026-10-28

The retro commit for the rev 3 rule changes (CLAUDE.md "Method text changes only in a commit that also adds to a `retro_*` folder"). Westley's word: "finish #4" (2026-10-28), meaning Phase 4 of the rev 3 plan, 4c the rule text.

- CLAUDE.md: the ten sentences of `method_rev3_2026-10-26/spec.md` "Rule-text diffs" (gaps G01, G02, G03, G04, G07, G11, G12, G19, G21, G23), each replacing the exact old sentence; every one pinned in `method_rev3_2026-10-26/pins.toml` with `since = "2026-10-28"`, so `status_check.py` check `method_pins` fails a later edit that drops one. The G08 item (cap at 120 lines by moving history out) needs nothing: the file is under 120 lines. The trim draft (`method_rev3_2026-10-26/CLAUDE_trim_draft.md`) is not applied; Westley asked for CLAUDE.md to keep its form.
- `workflows_2026-10-07/dispatcher.md`: the landing clerk's steps (gate row, one rerun, the clerk rules test-defects, background gate wait).
- Decisions that the text records: DEC-method-rev3-plan, DEC-piece-size-rule, DEC-thresholds-approved-2026-10-28.
