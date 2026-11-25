# LI1 interface: `scripts/skilllab/arena/isolation_runner.py` (2026-11-24)

What the later pieces (LI2 measures, LI3 arms M and V, LI4 arms R, F, W, P, LI5 table and page) call. Pinned by `tests/skilllab/integration/test_isolation_runner_*.py`; the implementer builds to this and reports a test that looks wrong as a `test-defect`, never edits it. Spec: `docs/northstar/plans/lab-isolation-2026-11-24/spec.md` section 7.

## Names

```python
THEN_SHA = "4fa618ce78349fcc077ce552753131e737ae2cea"
class Version(NamedTuple): name: str; sha: str                    # sha is the full 40 hex
class BuildError(Exception): stage: str                           # stage in resolve, archive, build, layout, fight; .args[0] is the message

resolve_version(name, ref=None, repo=None) -> Version             # then -> THEN_SHA; now -> rev-parse origin/main in repo; fix -> ref (branch or sha) made full; else ValueError (also fix without ref)
build_version(version, scratch_root, repo=None) -> Path           # tree at scratch_root/<name containing the sha>; git archive of csrc, Makefile, scripts, the layer_dynamics catalogue, situations and arena dirs; `make libouroboros.so` in it;
                                                                  # cached by sha (same tree for two names, nothing rebuilt, no .git); a failed build is never cached as good; raises BuildError
run_one(name, layout, seed, scratch_root, *, arm="W", ref=None, repo=None, out_dir=None) -> dict   # one row; NEVER raises for a run that fails: it returns an error row
run_matrix(names, layouts, seeds, scratch_root, rows_path, *, arm="W", refs=None, repo=None, out_dir=None) -> list[dict]   # names x layouts x seeds, in that nesting order; rows_path is rewritten, a line appended and flushed per run; refs = {name: ref}
units_firing(doc, version_name) -> dict | str                     # from a fight document (see below)
row_key(row) -> (version, lab_sha, arm, layout, seed)
read_rows(path) -> list[dict]; write_rows(rows, path)
```

CLI (exit 0 when every row is ok, 1 when any row is an error row; rows are written either way):
`python -m scripts.skilllab.arena.isolation_runner --version then|now|fix [--ref REF] --layout L-0047|SIT-0106 --seed N [--arm W] --scratch DIR --rows FILE [--repo PATH] [--out DIR]`.

`layout` is a catalogue id (`L-0047`) or a situation id (`SIT-0106`, converted by that version's own `situations` converter into the scratch tree). The version's lab runs as `python -m scripts.skilllab.arena.run --layout ... --seed N --out ...` inside its own tree, with the one order a side the lab gives (no second click, ever). `arm` is a free label (`M`, `V`, `R`, `F`, `P`, `W`), copied to the row; LI1 does nothing with it. Default out dir: under the scratch root. `repo` defaults to the repository of the module (read with `git archive`, `rev-parse`; never written; never checked out).

## Row (one JSON object per line, `json.dumps(row, sort_keys=True)`)

| key | value |
|---|---|
| version | `then`, `now` or `fix` |
| lab_sha | the full sha of the tree the lab ran from; `null` only when the ref did not resolve |
| arm, layout, seed | as asked (layout as given: `L-0047` or `SIT-0106`) |
| result | `{winner, survivors [a, b], last_tick, end}` copied from the fight file's `result` (`winner` A, B, none, stall or draw; `end` wipe, apart, silence or cap); `null` on error |
| margin | `survivors[0] - survivors[1]` (side A minus side B; positive means A ended ahead); `null` on error |
| units_firing | `{"by_frame": [[tick, A units that fired, B units that fired], ...], "peak": [maxA, maxB]}` from the per-unit `fired` flag of each frame; the string `not measured at <version name>` when the version's fight file has no `fired` (`then`); `null` only on error; never 0 |
| fight_path | absolute path of the fight file under the scratch root; `null` on error |
| fight_sha256 | sha256 of that file; `null` on error |
| error | `null`, or `{stage, message}` (stage as BuildError; message is the lab's or compiler's reason, non-empty) |

Equal runs give equal rows ignoring only `fight_path`, and equal fight files, whichever out dir or scratch root: nothing from the clock, the scratch path or hash order may reach the fight file or the row.

## Open for the chat (nobody decided)

- `margin` is defined above as A minus B survivors; if Westley's scoring wants the winner's margin, the sign changes in one place.
- `draw` and `cap` cells are marked `defect` by LI4 from `result.end` (spec section 4); LI1 reports them as they come.
- The LI1 controls (`test_isolation_runner_controls.py`) pin today's lab: if the lab's file names or `layout_path` form change, they go red first.
