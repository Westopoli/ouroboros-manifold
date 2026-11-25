# LI5 part 1 interface: `scripts/skilllab/arena/isolation_page.py` (2026-11-24)

The comparison table and the artifact page generator (spec section 5 and 6). Pinned by `tests/skilllab/integration/test_isolation_page_*.py` (helpers and the page checkers: `isolation_page_fixtures.py`; the standing page A-003 is copied to `tests/skilllab/integration/data/a003_page.html` as the form control). The implementer builds to this and reports a test that looks wrong as a `test-defect`, never edits it. Spec: `docs/northstar/plans/lab-isolation-2026-11-24/spec.md` sections 5, 6, 8. New file only; it reads LI4-FW rows (`isolation_fw.comparison_rows`), LI3 M summaries and V rows, the clip pipeline's `facts.json` files. No clock, no path, no hash order in any output byte. Clips (the render) are part 2; this piece only places finished clips.

## Names

```python
class PageError(ValueError)                                    # bad input; nothing is written (no index.html, no artifacts-row.md, no copied clip) when it is raised
BANNER_KINDS = ("decision", "ask")
draft_label(name) -> str                          # "DRAFT_OPENING_WINDOW_40" -> "DRAFT-opening-window-40"; ValueError when the name does not start DRAFT_
collect_drafts() -> {name: value}                              # every module-level DRAFT_* of isolation_measures and isolation_fw (and isolation_arms when importable), name as in the module
read_inputs(*, rows=(), m=(), v=(), repo=None) -> {"comparison": [...], "m_summaries": [...], "v_rows": [...]}
build_page(out_dir, *, banner, banner_kind="decision", inputs, clips=None, drafts=None, ledger) -> {"index": Path, "row": Path}
main(argv=None) -> int
```
- `rows`: LI4-FW rows files (JSONL, one row per line); `comparison` = `isolation_fw.comparison_rows(all rows, repo)`. `m`: JSON files, each a list of M summaries as `isolation_arms.scan_m` returns them. `v`: JSONL files of V rows (`run_v_flat`, `run_v_stage4`). A missing or unreadable file, or a line that is not JSON, is a `PageError` naming the file (and the line number for JSONL).
- `build_page`: `clips` is a manifest path or None; `drafts` is `{name: value}` or None (None means `collect_drafts()`); `ledger` is `{id, date, title, why?, url?}`; `id`, `date` (`YYYY-MM-DD`) and `title` are required (`PageError` otherwise); unknown `banner_kind` is a `PageError`. `out_dir` gets exactly `index.html`, `artifacts-row.md` and, with clips, the copied media; building again into the same dir gives the same bytes.
- CLI: `python -m scripts.skilllab.arena.isolation_page --out DIR --banner TEXT [--banner-kind decision|ask] [--rows F ...] [--m F ...] [--v F ...] [--clips MANIFEST] --id A-005 --date YYYY-MM-DD --title T [--why W] [--url U] [--repo P]`; exit 0, or 2 with the `PageError` message (it names the bad file) on stderr and nothing written.

## Clips manifest (the clip pipeline's facts files, `docs/reports/2026-11-24-clip-pipeline-interface.md`)

`{"sets": [{"id", "layout", "seed", "row", "why", "facts": [path, ...]}]}`; paths relative to the manifest; each is a `NAME.facts.json`; `video.file` and `poster.file` are base names beside it. The page reads from a facts file: `version`, `first_tick`, `last_frame_tick`, `engine_sha`, `video.file`, `video.sha256`, `poster.file` (a missing key or file is a `PageError` naming it). Media are copied byte for byte into `out_dir/clips/` (src and poster relative, `clips/<name>`); never decoded. `row` is the comparison-table row id (the layout); `why` is the label of the set (`changed`, `same`, `l0102`, `stopping`, or any text, shown).

## The page (HTML; one `index.html`)

Form: single file, theme tokens `--bg --panel --fg --muted --line --accent --blue --red --warn --warn-bg` on `:root`, the same tokens overridden under `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { ... } }` and in `:root[data-theme="dark"] { ... }`; `body { background: var(--bg) }`; no `100vh` or any viewport-height hero; fonts only from `fonts.googleapis.com`/`fonts.gstatic.com`; a `<script src>` only from cdnjs or jsdelivr with a pinned `x.y.z`; inline scripts allowed (the clip transport, as A-003); every table in a `.tablewrap { overflow-x: auto }`; a `max-width` media query; `video { max-width: 100% }`; every svg has a `viewBox` and no fixed pixel width. Every video has relative `src` and `poster`; every file exists in `out_dir`. Text is escaped.

Sections, in this order, each `<section data-section="...">`, each present once: `banner` (`data-banner` = kind; the passed-in text, first), `sentences` (one `<p data-sentence="L-####">` per layout, in soldiers: the survivor counts of then and now, no `%`, no ratio), `comparison`, then those of `arm-M`, `arm-V`, `arm-W`, `arm-F` that have input (W and F: when a comparison cell of that arm was run), `drafts`, `shas`, and `clips` (only with a manifest).

### comparison: `<table data-table="comparison">`

`th` and `td` carry `data-col`: `layout, ruling, then, now, [fix], change, first_arm` (spec 5; `fix` only when some row has a fix cell run). One `<tr data-layout="L-####">` per row of `comparison`, in its order; a row whose `same_or_changed` is `changed` is followed by `<tr data-layout=... data-variant="control">` with `then`, `now` (and `fix`) cells of `row["control"]`.
- `ruling`: `ruling.words` verbatim, `ruling.date`, `ruling.per_picture` (`no per-picture verdict` or his words), `predict_rate` as `{:g}`; the stage approval words and date.
- `then`, `now`, `fix`: `<winner> <a>:<b> t<last_tick>` of the headline cell (`A 21:0 t3394`, `cap 8:8 t12000`) and the winner counts `A 2, B 1` of `winners`; `not run` for a cell that is the string `not run`. A not-measured value renders by `not_measured_text` below; two zeros are never invented.
- `change`: `same` or `changed`, `N seeds flipped` for `changed`, and the rule name `DRAFT-same-or-changed-rule` (from `row["rule"]`); `not measured at ...` when the verdict is not measured; `not run`.
- `first_arm`: `row["first_differing_arm"]` verbatim.
- a changed row carries `<a data-clipset="<set id>" href="#<set id>">` for every clip set whose `row` equals its layout.

`not_measured_text(version, value)`, used for every cell of every table: a value that is not a string starting `not measured` is shown as is; `not measured at <version>` stays as it is; `not measured: <reason>` becomes `not measured at <version> (<reason>)` (an error row's `not measured: build: boom` gives `not measured at now (build: boom)`). Never `0`, `0:0` or a blank. The version is the cell's `version`.

### per-arm tables

- `arm-W` (`table[data-table="arm-W"]`) and `arm-F`: one `<tr data-layout data-variant data-version>` per run cell (W: `row[v]` and `row["control"][v]`; F: `row["f"][v]["layout"|"control"]`; only cells that were run). Columns `data-col`: `winner, survivors (a:b), last_tick, end, invalid, agreement, units_firing, flags`. `invalid`: the rule ids, `none` for `[]`, or the not-measured text. `agreement`: `predictions.agreement`. `units_firing`: for LI2's dict, an `<svg viewBox ... data-lines="units_firing">` with a `<polyline data-side="A">` and one for `B`, each with a point per `by_frame` entry in `points`, and `aria-label="side A units firing"` (`side B ...`), plus a text legend naming both; for a not-measured string the text only (no svg).
- `arm-M`: per summary a block `div[data-version]` (`data-multi-flip="true"` on the block when `multi_flip`) with `table[data-table="arm-M"]`, one `tr[data-enemy="N"]` per point in order, columns `enemy, won (won|lost|defect), flip, mean_margin, orders_ended_short`; `data-flip="true"` on the row that is the `after` of a flip, its `flip` cell holding the flip's `direction`; the stopping check line `orders ended short: N` (or the not-measured string of `rows[*].stopping`); every offender of `rows[*].stopping.units` as `<li data-unit-id="ID">` with its id, tick, x, y. Beats and loses-to appear as the points show them, never alone.
- `arm-V`: `table[data-table="arm-V"]`, one `tr[data-layout data-kind data-version]` per row, columns `part_word, sensor, notice, first_seen, standoff_count, first_shot_tick, twin, flags`; vision values that are strings are shown through `not_measured_text`.
- Flags: `<span class="flag" data-flag="NAME">signal: NAME</span>` (class list exactly `flag`). W/F: `defect` when the cell's `defect` is True, `invalid` when `invalid` is a non-empty list (a not-measured string is no flag); V and M rows: their `flags` lists. No element anywhere gets a class from `bad fail error pass ok danger`; the words `regressed` and `improved` never appear.
- The only badge named `blocks`: `<span class="badge blocks">blocks</span>`, once per M summary whose `blocks` is True, inside that summary's block. With no stopping-check hit the word `blocks` appears nowhere in the visible text and no element has that class or a `data-blocks` attribute. A V row's `blocks` (always False) draws nothing.

### drafts and shas

`drafts`: `<li data-draft="DRAFT-...">` per entry, its value shown (a tuple as `10, 1`); the section says the numbers are Westley's. `shas`: `<li data-version="then|now|fix">` with the full 40-hex `lab_sha` of that version's rows (lab and engine are one tree in LI1); each clip's `engine_sha` is also listed (so a clip of another tree shows its sha).

### clips: `<section data-section="clips">`

Per set, in manifest order, `<section id="<set id>">` holding: a caption per clip `<figcaption>` with layout, `seed N`, the version label, the tick range (`first_tick` to `last_frame_tick`), `row <row id>`, and the set's `why`. Two to four clips: `<div class="bench grid" data-bench="true" data-first=<first_tick> data-last=<last_frame_tick>>` of `<figure><video preload="metadata" playsinline muted poster= src=>` plus a `div.transport` with `[data-play]` and `[data-scrub]` (A-003 form; the inline script drives it); clips in facts order. One clip: a single `<figure>` with `<video controls>` and no bench or transport. More than four is a `PageError`.

## Ledger fragment: `artifacts-row.md`

One line, `\n`-terminated, ten cells in the ledger's column order (`docs/northstar/story_reviews/westley/artifacts.md`): `id`, `url and version` (the `url`, else `not published yet`), `date`, `title`, `shows` (`layouts L-0055, L-0084; arms M, V, F, W; N clip set(s)`, arms in `ARM_ORDER`), `why` (as passed, else `not recorded`; a `|` is written `\|`), `code` (each version's full lab sha, the video sha256 of each clip, `artifacts/<id>/page.html`), `his response` = `none yet`, `done` = `none yet`, `status` = `current`.

## Open for the chat (nobody decided; not tested)

- Arm R: LI4-R has no interface yet; the page has no `arm-R` section. When it lands, a section is added the same way.
- Real arms M and V are not run in these tests (LI3 is on its own branch, not in this branch's tree); their page code is tested on the shapes of the LI3 interface. After the merge, add one real M and one real V row to `test_isolation_page_real.py`.
- Clip selection (which runs get a set, "one `same` per layout, the L-0102 reproduction, one stopping offender") is the caller's; the page places what the manifest names.
- The M map marks the point after a flip; a multi-flip shows every flip.
