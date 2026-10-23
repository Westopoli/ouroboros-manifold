# C4-E3: rules whose only tests E3 deletes (proposed C6 work-list gap rows, A47)

Source: `push/C4-E3-tests2`. E3 retires `tests/test_cover_render.gd`, `tests/test_input_router_selection.gd` and `tests/test_input_router_control_groups.gd` (each with its .tscn) and `simulation/test_wave3_blockers_umbrella.py::test_umbrella_f_tactical_emits_unit_signals`. None of those files cites an R-id; the rule is the one the behaviour belongs to, checked against `docs/bible/epics/E-16-*.md` and a grep of every other test (`tests/`, `tests/csim/`, `tests/qa/`) for the id. Nothing below is rebuilt in E3, none is counted proven or skipped.

Columns as in `docs/northstar/plans/archive/2026-09-30-work-list.md` (item, area, rule, cluster, plan item, note). These are client gaps, so there is no `om_*` symbol; cluster 7 (misc).

| Item | Area | Rule | Cluster | Plan item | Note |
|---|---|---|---|---|---|
| client: bind a control group (Ctrl+digit), exclusive membership, recall | input | R-105-02 | 7 | C6 (sweep) | only tests were the legacy `_bind_group`/`_recall_group` ones. tactical_c has no control groups (test_tactical_view header: "no control groups"); Q-110-04 defers key rebinding, not the groups. Press-twice-centers-camera was never tested. Needs a ruling: build in tactical_c, or defer the rule |
| client: Shift+click adds to or removes from the selection | input | R-105-05 | 7 | C6 (sweep) | only the legacy `_click_select` additive tests (replace, additive keeps existing, additive dedupes) covered it. tactical_c has no Shift-click test |
| client: click a friendly unit makes it the selection (click half of R-105-01) | input | R-105-01 | 7 | C6 (sweep) | the box half stays proven (test_tactical_view `_check_box_select_then_move_R105_01`); the click half was proven only by legacy `_test_click_replace`. Partial gap |
| client: cover clusters drawn on the mission map | render | none in E-16; nearest R-092-01 (recon shows every cover cluster) | 7 | C6 (sweep) | legacy `terrain_renderer._scatter_cover_asteroids` (4 MultiMesh scale classes) was the only code and test. tactical_c draws no cover. The bible has no client rule that says cover is drawn in play outside recon; Architect to say whether a rule needs writing (Principle: ambiguity is flagged, so no Q row added here) |

Not gaps (they had no test before E3 either, so E3 changes nothing): R-105-03, R-105-06, R-105-07, R-105-08, R-104-07. R-105-04 and R-089-04 stay proven by `tests/test_tactical_view.gd`.

The python umbrella test checked that legacy tactical.gd mentioned the tutorial signals `first_unit_visible` and `first_unit_selected`. It cites no rule, and the tutorial chain is parked (G3 removed Replay Tutorial). Not a rule gap.
