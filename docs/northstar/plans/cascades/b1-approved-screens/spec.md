# b1-approved-screens

Every role of this cascade runs on Sonnet 5.5 (`claude-sonnet-5-5`), named explicitly on each spawn. Sub-agents never spawn. Method: `docs/method/story_loop.md`. Story: `docs/stories/H-087.md` (rules R-087-01 to R-087-05). Contract: `contract.md` here. Umbrella: the `darwin` cases in `tests/method/test_setup_editor.py` (red on this branch's base commit). H-060 (`docs/stories/H-060.md`) is already built and merged into this branch (`107e7267`); it is NOT part of this cascade's build and its files are not touched.

## Summary

Beta stage B1 is delivered by H-060 (already built: the approved screens chained to an empty field) and H-087 (new: the project's editor setup runs on a Mac). This cascade builds only H-087: `scripts/setup_editor.sh` learns the Darwin route, `scripts/fetch_godotsteam.sh` learns `shasum`, and the README says what a Mac needs. One leaf.

## Acceptance criteria

1. R-087-01: on Darwin, `scripts/setup_editor.sh` builds through `scripts/build_pipe_macos.sh` with `ARCH` from `uname -m`, copies `dist/macos/ouroboros_pipe` to `pipe/ouroboros_pipe` by temporary name then move; Linux unchanged.
2. R-087-02: Godot is `godot.real` on PATH, else `$HOME/.local/bin/godot.real`, else on Darwin `$OM_GODOT_APP` (default `/Applications/Godot.app/Contents/MacOS/Godot`); with none, one line names `godot.real` and the app path, then `EDITOR SETUP FAILED import`.
3. R-087-03: `scripts/fetch_godotsteam.sh` uses `sha256sum` when present, else `shasum -a 256`; the pinned sha gates the unpack; Linux unchanged.
4. R-087-04: `--check` on Darwin prints the four lines of `contract.md`, exits 0, changes nothing.
5. R-087-05: `README.md` "Open in the editor" gains the Mac sentence: Godot 4.6.3 from godotengine.org in `/Applications`, the Xcode command line tools for `clang` (`xcode-select --install`), the same one command.
6. Every Linux case of `tests/method/test_setup_editor.py`, `tests/qa/test_beta_b1_chain.py` and `tests/method/test_beta_build_sha.py` stays green; the headless import of the tree is clean.

## Inputs / Outputs / Constraints / Out of scope

- Files the leaf writes: `scripts/setup_editor.sh`, `scripts/fetch_godotsteam.sh`, `README.md`. Nothing else.
- Pre-flight facts (read on this branch, 2026-11-05): `scripts/setup_editor.sh` is 38 lines, Linux only (`build_pipe_linux.sh`, `dist/linux/ouroboros_pipe`, `godot.real`, then `$HOME/.local/bin/godot.real`); `scripts/build_pipe_macos.sh` takes `ARCH` (default `arm64`) and writes `dist/macos/ouroboros_pipe`; `scripts/run_godot_tests.sh` lines 17-18 hold the Godot discovery order; `scripts/fetch_godotsteam.sh` line 20 calls `sha256sum "$zip" | cut -d' ' -f1`; `shasum -a 256` prints the same `<hex>  <file>` shape.
- Constraints: bash 3.2 (macOS) and BSD `find`/`cp`/`mktemp`: no `find -quit` (use `find ... | head -n1`), no `mapfile`, no associative arrays, no `${v,,}`. The Linux route's printed lines and behaviour are byte for byte as today. About 60 implementation lines.
- Out of scope: any change under `autoload/` or `scenes/`; a signed macOS export; running anything on the Mac; the Steam cache path (a Mac has none, so it takes the fetch route).

## Scale & Boundary Profile

unbounded-unknown — assert growth only, no absolutes. (A shell script run by hand once per pull; no hot path.)

## Bible Compliance

- **Bible path:** `docs/bible/game_bible.md`
- **Sections referenced:** none. This is harness and tooling; no bible rule is implemented or changed (E-16 screens are chained by H-060 and unchanged).
- **Deliberate divergences:** none.
