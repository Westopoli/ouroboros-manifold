# Display fault: context for the debugging chat (2026-10-31)

Written by the Architect for Westley and a Sonnet chat (Claude Code or Claude Desktop with computer control) that will isolate the fault together, one hypothesis at a time, and report back. Everything below is measured unless marked "guess". Record every run's result in the log table at the end of this file; the Architect reads this file, nothing else.

## The symptom, in one line

`scripts/play.sh --story H-023` opens a Godot window on Westley's desktop that shows only the Godot boot splash (blue robot, "GODOT Game engine") and never the game, while Godot's own loop reports 116 to 146 fps.

## What is known

Machine: GNOME Shell 50.1 on Wayland, two monitors (four entries in `~/.config/monitors.xml`), NVIDIA RTX 3060, driver 595.91.07. Godot 4.6.3 stable at `~/.local/bin/godot.real`. Project `~/Projects/om-push/main` (a plain clone of origin/main, pulled with `git pull --ff-only`). Renderer Forward Plus (Vulkan). `project.godot`: main scene `res://scenes/privacy_modal/privacy_modal.tscn`, `window/size/viewport_width=1920`, `viewport_height=1080`, `window/size/mode=3` (fullscreen), `window/stretch/mode="canvas_items"`.

The launcher `scripts/play.sh` (story H-001, first H-031 piece landed 2026-10-31 60479600): when `WAYLAND_DISPLAY` is set it runs `godot.real --path <tree> --display-driver wayland --windowed --resolution 1920x1080 --print-fps <scene> -- <story args>` detached with `setsid nohup`, output to `<tree>/.play.log`; `--dry-run` prints the exact line. For `--story H-023` the scene is `res://scenes/proto/unit_scale/unit_scale.tscn`.

Measured on Westley's desktop, night of 2026-10-30 (story file `docs/stories/H-031.md`, section Finding):

1. Default X11 driver (Xwayland): the window is created and stays IsUnMapped / Iconic, Vulkan or opengl3, windowed or not.
2. `--display-driver wayland`: a window appears.
3. `--display-driver wayland --windowed --resolution 1280x720`: the H-023 stage was fully drawn. Westley saw it. This is the only sighting of game content so far.
4. Same without `--windowed` (project default, fullscreen): only the Godot splash.
5. Godot's loop runs at about 140 fps in every case (`--print-fps`), so the game does not stall; frames are rendered but not presented, or the splash layer is never replaced.
6. A two-line control project presents fine under the same driver.
7. Today, 2026-10-31 13:28, `--display-driver wayland --windowed --resolution 1920x1080` (play.sh's new default): only the Godot splash. Log clean apart from the known `godotsteam.gdextension` not-found lines and `xdg-toplevel-icon protocol not found`.
8. No saved game settings exist on this machine: there is no `settings.cfg` under any `~/.local/share/godot/app_userdata/*/`, so `autoload/ui_data_bus.gd` takes its defaults branch (fullscreen false) and `_apply_stored_settings()` (line 115, the fullscreen-or-windowed flip at 122 to 126) is NOT called. The stored-settings flip is ruled out for the default profile.
9. No screen capture works from an agent process (org.gnome.Shell.Screenshot refuses non-session callers; no grim, gnome-screenshot or spectacle installed). The person at the desk is the only reader of the screen.

What differs between the one success (item 3) and the failures (4, 7): the window size. 1280x720 draws; 1920x1080 and fullscreen do not. Both monitors are, guess, 1920x1080, so a windowed 1920x1080 window equals the monitor and Mutter may treat it as fullscreen.

## Hypotheses, in the order to test them

H1 (most likely). A Godot window whose size equals the monitor under GNOME Wayland is auto-fullscreened or maximised by Mutter, and the fullscreen path never presents a second frame (same fault as item 4). Prediction: 1280x720 shows the game; 1920x1080 shows the splash; 1900x1060 shows the game.

H2. The fullscreen fault is Godot's Wayland fullscreen under NVIDIA (swapchain never recreated after the mode change), not Mutter. Prediction: `--rendering-driver opengl3` in fullscreen shows the game; Vulkan fullscreen does not.

H3. The splash stays because the first presented frame is the splash and the swapchain stalls after the window's first configure event (a Wayland `xdg_toplevel.configure` with a size that differs from the requested one). Prediction: `WAYLAND_DEBUG=1` output shows a configure to a different size right before the fps lines start, and `--resolution` matching that size draws.

H4. The X11 (Xwayland) unmapped window is a different fault: the launch is detached (`setsid nohup`) and Mutter withholds focus and mapping from a window with no startup token. Prediction: the same X11 launch typed directly in Westley's terminal without `setsid nohup` maps and draws.

## The runs

Each run is one line. Before each, close every Godot window (`pkill -f godot.real` is safe: nothing else runs Godot). Run from Westley's own terminal, on his desktop, not from an agent shell, unless the test is about the agent shell. Replace `TREE` with `~/Projects/om-push/main`. `SCENE` is `res://scenes/proto/unit_scale/unit_scale.tscn`.

```
R1  ~/.local/bin/godot.real --path TREE --display-driver wayland --windowed --resolution 1280x720 --print-fps SCENE
R2  ~/.local/bin/godot.real --path TREE --display-driver wayland --windowed --resolution 1920x1080 --print-fps SCENE
R3  ~/.local/bin/godot.real --path TREE --display-driver wayland --windowed --resolution 1900x1060 --print-fps SCENE
R4  ~/.local/bin/godot.real --path TREE --display-driver wayland --print-fps SCENE                       (fullscreen, Vulkan)
R5  ~/.local/bin/godot.real --path TREE --display-driver wayland --rendering-driver opengl3 --print-fps SCENE
R6  ~/.local/bin/godot.real --path TREE --display-driver wayland --rendering-driver opengl3 --windowed --resolution 1920x1080 --print-fps SCENE
R7  WAYLAND_DEBUG=1 ~/.local/bin/godot.real --path TREE --display-driver wayland --windowed --resolution 1920x1080 SCENE 2>&1 | grep -E 'configure|fullscreen|maximiz' | head -20
R8  ~/.local/bin/godot.real --path TREE --display-driver x11 --windowed --resolution 1280x720 --print-fps SCENE      (typed, not detached)
R9  same as R8 but with the main scene (omit SCENE): does the privacy modal draw?
R10 same as R1 with the main scene (omit SCENE): does the privacy modal draw at 1280x720 under Wayland?
```

For each run record: draws the game / splash only / no window; fps line present yes or no; anything printed that is not the godotsteam or icon lines. R1 is the control (expected: draws). If R1 does not draw today, stop and report: the fault moved and the table above is stale.

Decision from the results: R1 draws and R2 does not and R3 draws: H1 confirmed (fix is in play.sh: never request the monitor's size; DRAFT-play-resolution becomes 1600x900 or the monitor size minus a margin). R4 splash and R5 draws: H2 confirmed (fix: opengl3 for fullscreen, or Vulkan fullscreen bug report upstream). R7 shows a configure to a different size: H3 supports H1. R8 draws: H4 confirmed for the agent-launched X11 case.

## What the debugging chat may and may not do

- May: run the lines above, read `.play.log`, read `scripts/play.sh`, `project.godot`, `autoload/ui_data_bus.gd`, `scenes/proto/unit_scale/*`; try other flags; take screenshots with the desktop's own tools (PrtSc, GNOME's screenshot UI); install a capture tool if Westley agrees (`gnome-screenshot` or `grim` makes H-031 round two possible).
- May not: edit any file under `~/Projects/om-push/main` or `~/Projects/ouroboros-manifold`; commit or push; change `project.godot`; edit tests. A proposed fix goes in the report as a diff in words, and the Architect writes the story for it.
- Reports once, at the end, by filling the table below and the "Conclusion" line, in this file, on a branch pushed as `push/display-debug-2026-10-31` (the Sonnet chat may do that one git action, nothing else), or by pasting the table into the Architect chat.

## Log

| Run | Window | Draws (game / splash / none) | fps lines | Notes |
|---|---|---|---|---|
| R1 | | | | |
| R2 | | | | |
| R3 | | | | |
| R4 | | | | |
| R5 | | | | |
| R6 | | | | |
| R7 | | | | |
| R8 | | | | |
| R9 | | | | |
| R10 | | | | |

Conclusion: (which hypothesis held, the decisive run, the proposed fix in one sentence)
