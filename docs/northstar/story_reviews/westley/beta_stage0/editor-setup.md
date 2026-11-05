# Run the chain from your editor (H-067)

What this gets you: your own checkout, `~/Projects/ouroboros-manifold`, open in your Godot editor (4.6.3), F5, and the game plays from the privacy screen through the galaxy, a mission, Deploy, a 2D match and the end of the mission.

Why a procedure and not just `git pull`: your checkout holds 175 `.uid` files that your earlier editor runs created. Main now carries those same files, so a plain `git pull` stops with "untracked working tree files would be overwritten". Main also changes `README.md` (a short "Open in the editor" paragraph), and your `README.md` has your own edits, so a plain `git pull` would stop there too. Once the beta-flag story (H-060) is on main it will stop on `project.godot` the same way. The commands below remove only the copies main replaces, set your `README.md` aside while the pull runs, and put it back. Nothing else of yours is touched.

## Look first (read-only)

```
cd ~/Projects/ouroboros-manifold
git diff project.godot
```

Expected: exactly one changed line, the engine tag in `config/features`. Your 4.6.3 editor re-saved it:

```
-config/features=PackedStringArray("4.7", "Forward Plus")
+config/features=PackedStringArray("4.6", "Forward Plus")
```

If anything else differs in `project.godot`, stop and send me the output; do not run the commands below.

## Type this

```
cd ~/Projects/ouroboros-manifold
git fetch origin
git restore -- project.godot
git diff --name-only --diff-filter=A -z HEAD origin/main -- '*.uid' | xargs -0 -r rm -f
git diff --name-only -z -- '*.import' | xargs -0 -r git checkout --
cp README.md ~/README.westley.md
git checkout -- README.md
git pull --ff-only origin main
cp ~/README.westley.md README.md
scripts/setup_editor.sh
```

What each line does:

- Line 3 throws away your local edit of `project.godot` (the tag line above) and nothing else; it touches that one file. Main keeps the `4.7` tag, and H-060 adds its `[editor]` block to the same file, which is why this line comes before the pull.
- Line 4 deletes only the `.uid` files that main is about to add. It cannot reach anything main does not carry.
- Line 5 resets only `.import` files that your editor rewrote. (Your checkout showed none when this was written; the line is there in case one appears.)
- Lines 6, 7 and 9 keep your `README.md`: a copy goes to `~/README.westley.md`, the tracked one is restored so the pull can go through, then your copy is put back. If you would rather read main's README, skip line 9.
- Line 8 is the pull. It only fast-forwards, so it cannot make a merge.
- Line 10 rebuilds the pipe if it is older than the C code, fills the Steam libraries, imports the project once, and prints `EDITOR READY <your checkout>`. If it prints `EDITOR SETUP FAILED pipe`, `steam` or `import`, that word is the step that broke.

Then open `project.godot` in the editor and press F5.

Left alone on purpose: `README.md`, `.claude/settings.local.json` and your untracked files. After the commands, `git status --short` should list only those and nothing ending in `.uid` or `.import`.

Your 4.6.3 editor may re-save the tag in `project.godot` again (4.7 to 4.6) the next time it saves the project settings. That is harmless: it is the same one-line difference. Before your next `git pull`, run `git diff project.godot`; if it is only that line, run `git restore -- project.godot` first. What I could check without a window: on a tree tagged `4.7`, a headless `godot.real` 4.6.3 editor open and a headless game run both left `project.godot` byte-for-byte unchanged, so the tag is not rewritten by opening or importing. Whether your windowed editor rewrites it on open, or only when you save, only you can see.

If the pull still stops, it names the files. Send me the list; do not delete anything the list shows that you wrote yourself.

## What to expect

The privacy screen, the main menu, New Game into the galaxy, a mission, Deploy, the 2D match, the end of the mission. While it runs the Output panel should show no `ERROR` and no `SCRIPT ERROR` lines. When you quit, some renderer leak lines (`Pages in use exist at exit`, shaders and RIDs not freed) will still print: that is a known separate finding, not part of this check. A `SceneRouter: queued 'main_menu' replaced by 'main_menu'` warning is also known (H-069).

If the galaxy shows `pipe binary is out of date (abi <n>, expected <m>): run scripts/setup_editor.sh`, the pipe is older than the C code: run the script again. If it shows `pipe binary missing: run scripts/setup_editor.sh`, the pipe was never built: same fix.

## Report back (yours only)

Two things only you can see in the real editor, and I need your word on them:

1. Once H-060 is on main: press F5 in the editor. Does the game start as the beta (the variant picker shows, which means F5 passed `--om-beta`)? That is the real-editor check of H-060 ruling 8.
2. After the pull, open `project.godot` once and run `git diff project.godot`. Does the windowed editor change the tag line on open, or only when you save? (A headless open did not; see above. Also tell me if it shows any "newer version" warning when you open the project.)

## Approve and deny

Approve means: you followed the commands, the editor opened, F5 walked the chain, and no `ERROR` or `SCRIPT ERROR` line appeared while it ran. The checkout is then a place you can run the beta from, and this story is Seen.

Deny means: tell me where it broke. The places to name are the pull (which files it listed), `scripts/setup_editor.sh` (which `EDITOR SETUP FAILED` step, or what it never printed), the editor open (what the Output panel said), or the chain (which screen, and the first `ERROR` line).
