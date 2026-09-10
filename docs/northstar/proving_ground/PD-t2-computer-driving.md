# Probe D — T2 computer driving

**Proves.** A script can launch a Godot window, click, press a key, screenshot, read state over a debug port, and flag a planted visual bug on the buggy build only.

**Fixture.** `~/Projects/agora-proving-ground`/probe_d: `toy_scene/` (Godot 4.6, gl_compatibility; button, status label, red dot on two layer heights, TCP debug port 47001), `run_probe_d.sh` (xdotool + import), `check_d.py` (pixel scan for the dot, state compare), `tests/test_probe_d.py` (runs both builds under Xvfb).

**Planted condition.** `TOY_BUG=1`: dot drawn at layer-1 height while state says layer 2; label stops updating after the second click.

**Pass criterion.** Clean findings empty; bug findings exactly {layer-elevation-mismatch, hud-stale}.

**Result 2026-09-10.** 1 passed in 16 s under `xvfb-run` with Mesa llvmpipe. Clean state `{"clicks":2,"layer":2,"dot_y":300}`; bug state reports layer 2 while pixels show the dot at y=600 and the label reads "clicks: 1".

**Gaps.** Ran on Xvfb (software GL), not the Xorg-virtual-screen-on-GPU target; `DISPLAY=:0` refused without XAUTHORITY. Agora has no desktop QA tool type; this script is its seed. Window-offset tolerance is ±20 px on x; a real window manager may need a window-relative screenshot.
