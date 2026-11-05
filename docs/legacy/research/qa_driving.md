# R1 — QA Driving on Forge

How the local model "is the user": launches the game, clicks, presses keys, looks at the screen, and compares what it sees to what the state says. Feeds Stage 0 probe D, Stage 3 watch-fors, and Sprint 0.

## Decided

- Visual QA (T2) runs on forge under an Xorg virtual screen on the RTX 3060 (nvidia xorg.conf with a dummy monitor). Real GPU, Forward+ renderer, unattended.
- State QA (T1) drives the C sim directly with no rendering and detects bugs from traces. T1 runs first and most.

## Questions to answer

1. **Install.** Godot 4.6 Linux binary location and version pin. Nvidia Xorg config for a headless virtual screen at 1920x1080. xdotool, ffmpeg, optional tesseract. How the `agora-dispatcher` systemd user service gets `DISPLAY` and `XAUTHORITY`.
2. **Game-side hooks.** A debug command port the QA harness can use: spawn unit, teleport, read unit state, set seed, set time scale, pause, trigger screenshot, dump trace window. Deterministic replay from a command log. Where this lives so Agora cannot break it.
3. **Observation.** Screenshot cadence per action. Video capture window around each action (ffmpeg on the virtual screen). Which local vision model fits 12 GB VRAM alongside the worker model (evaluate the qwen2.5-vl 7B class) versus DeepSeek vision for T2 judgments. When a T1 trace rule is preferable to any vision call.
4. **Detector mapping.** For each entry in `rts_bug_catalog.md`, the T1 rule or T2 check, the evidence captured, and the positive control.
5. **Agora integration.** A new `tool:` type for desktop QA beyond Playwright: session launch, action verbs (click at, key, drag, wait, screenshot, read state), finding shape, fingerprinting for desktop findings. What changes in `qa_explore.py` and `cascade_types.py`, listed as Agora PRs.

## Spike proof (gates Stage 0 probe D)

An Agora session launches Godot on the virtual screen, clicks a menu button via xdotool, saves a screenshot, reads one state value over the debug port, and writes a finding row. Record the run id here.

## Findings

**2026-09-10 spike (route 2, live session).** From a plain shell as the same user, `DISPLAY=:0` plus `XAUTHORITY=/run/user/1000/.mutter-Xwaylandauth.*` gives xdotool the live desktop (2560×1440) and Godot 4.6.3 the real GPU: `OpenGL API 3.3.0 NVIDIA 595.84 - Compatibility - Using Device: NVIDIA GeForce RTX 3060`. No Xorg dummy config, no install. Cost: the model shares Westley's mouse and keyboard while a session runs, and a screen lock or logout kills it. The Xorg-virtual-screen route (decided earlier) stays the collision-free option and still needs the nvidia dummy-monitor config; it is no longer required to start T2 work on the GPU.

**Still open for R1:** the desktop QA tool type in Agora (launch, actions, screenshot, debug port, findings) does not exist; `agora-proving-ground/probe_d/run_probe_d.sh` is the seed. Local vision model for T2 judgments untested. `DISPLAY=:1` hangs (second Xwayland socket, not usable).
