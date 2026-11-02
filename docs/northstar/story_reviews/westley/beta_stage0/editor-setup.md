# Run the chain from your editor (H-067)

What this gets you: your own checkout, `~/Projects/ouroboros-manifold`, open in your Godot editor (4.6.3), F5, and the game plays from the privacy screen through the galaxy, a mission, Deploy, a 2D match and the end of the mission.

Why a procedure and not just `git pull`: your checkout holds 175 `.uid` files that your earlier editor runs created. Main now carries those same files, so a plain `git pull` stops with "untracked working tree files would be overwritten". Main also changes `README.md` (a short "Open in the editor" paragraph), and your `README.md` has your own edits, so a plain `git pull` would stop there too. The commands below remove only the copies main replaces, set your `README.md` aside while the pull runs, and put it back. Nothing else of yours is touched.

## Type this

```
cd ~/Projects/ouroboros-manifold
git fetch origin
git diff --name-only --diff-filter=A -z HEAD origin/main -- '*.uid' | xargs -0 -r rm -f
git diff --name-only -z -- '*.import' | xargs -0 -r git checkout --
cp README.md ~/README.westley.md
git checkout -- README.md
git pull --ff-only origin main
cp ~/README.westley.md README.md
scripts/setup_editor.sh
```

What each line does:

- Line 3 deletes only the `.uid` files that main is about to add. It cannot reach anything main does not carry.
- Line 4 resets only `.import` files that your editor rewrote. (Your checkout showed none when this was written; the line is there in case one appears.)
- Lines 5, 6 and 8 keep your `README.md`: a copy goes to `~/README.westley.md`, the tracked one is restored so the pull can go through, then your copy is put back. If you would rather read main's README, skip line 8.
- Line 7 is the pull. It only fast-forwards, so it cannot make a merge.
- Line 9 rebuilds the pipe if it is older than the C code, fills the Steam libraries, imports the project once, and prints `EDITOR READY <your checkout>`. If it prints `EDITOR SETUP FAILED pipe`, `steam` or `import`, that word is the step that broke.

Then open `project.godot` in the editor and press F5.

Left alone on purpose: `README.md`, `.claude/settings.local.json`, `project.godot` (your `4.7` to `4.6` edit; the editor may keep rewriting it), and your untracked files. After the commands, `git status --short` should list only those and nothing ending in `.uid` or `.import`.

If the pull still stops, it names the files. Send me the list; do not delete anything the list shows that you wrote yourself.

## What to expect

The privacy screen, the main menu, New Game into the galaxy, a mission, Deploy, the 2D match, the end of the mission. While it runs the Output panel should show no `ERROR` and no `SCRIPT ERROR` lines. When you quit, some renderer leak lines (`Pages in use exist at exit`, shaders and RIDs not freed) will still print: that is a known separate finding, not part of this check. A `SceneRouter: queued 'main_menu' replaced by 'main_menu'` warning is also known (H-069).

If the galaxy shows `pipe binary is out of date (abi <n>, expected <m>): run scripts/setup_editor.sh`, the pipe is older than the C code: run the script again. If it shows `pipe binary missing: run scripts/setup_editor.sh`, the pipe was never built: same fix.

## Approve and deny

Approve means: you followed the commands, the editor opened, F5 walked the chain, and no `ERROR` or `SCRIPT ERROR` line appeared while it ran. The checkout is then a place you can run the beta from, and this story is Seen.

Deny means: tell me where it broke. The places to name are the pull (which files it listed), `scripts/setup_editor.sh` (which `EDITOR SETUP FAILED` step, or what it never printed), the editor open (what the Output panel said), or the chain (which screen, and the first `ERROR` line).
