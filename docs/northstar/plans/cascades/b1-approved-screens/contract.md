# Contract: the Darwin lines of `scripts/setup_editor.sh`

Cascade b1-approved-screens, story H-087. The contract is what the script prints and the one variable it reads; the umbrella is the `darwin` cases in `tests/method/test_setup_editor.py`. Everything else in the script is unchanged. Rule ids are in `docs/stories/H-087.md`.

## Detection

`uname -s` printing `Darwin` selects the Mac route (R-087-01). Any other answer is the Linux route, byte for byte as on main. The architecture is `uname -m` (`arm64` or `x86_64`).

## `--check` output on Darwin (R-087-04; exit 0, changes nothing)

Four lines, in this order, each starting exactly as shown (`<...>` is filled in):

```
step pipe: scripts/build_pipe_macos.sh (ARCH=<uname -m>), then copy dist/macos/ouroboros_pipe to pipe/ouroboros_pipe (only when csrc/ is newer than the copy or the copy is missing)
step steam: <the Linux line, unchanged>
step import: <godot> --headless --import --path .
clang: present
```

- `<godot>` is the binary the run would use, as an absolute path or the name found on PATH by `command -v`; when none is found the line is `step import: none found (looked at: godot.real on PATH, <app path>)`.
- The last line is `clang: present` when `command -v clang` succeeds, else `clang: missing`.
- `<app path>` is `$OM_GODOT_APP`, default `/Applications/Godot.app/Contents/MacOS/Godot`.

## Run on Darwin

- pipe (R-087-01): when `pipe/ouroboros_pipe` is missing or older than a file in `csrc/`, run `ARCH=<uname -m> scripts/build_pipe_macos.sh`; copy `dist/macos/ouroboros_pipe` to `pipe/ouroboros_pipe.new.$$` then `mv -f` onto `pipe/ouroboros_pipe`; failure prints `EDITOR SETUP FAILED pipe`. The staleness test must run under BSD `find` and bash 3.2 (no `-quit`, no associative arrays, no `mapfile`).
- Godot (R-087-02): `godot.real` on PATH, else `$HOME/.local/bin/godot.real` (existing Linux fallback), else on Darwin `$OM_GODOT_APP`. When none exists the import step prints one line naming `godot.real` and the app path, then `EDITOR SETUP FAILED import`.
- `OM_GODOT_APP` is a test seam only; a comment at the read site says so (as for `OM_BETA_BUILD_FILE`). The Linux route never reads it.

## `scripts/fetch_godotsteam.sh` (R-087-03)

The sum is taken with `sha256sum` when it exists, else `shasum -a 256`; the output is compared to the pinned `SHA256` exactly as today, a mismatch prints `sha256 mismatch: expected ..., got ...` to stderr and exits 1, and nothing is unpacked before the comparison passes.
