Ouroboros Manifold — Friends Build
===================================

Thank you for playtesting.

Running the game
----------------
1. Extract the ZIP to a folder of your choice.
2. Double-click OuroborosManifold.exe.
3. On first launch you'll see a privacy notice. Read it, click "I Understand".
4. The loading screen starts the simulation. This can take up to 15 seconds.
5. Main menu — start a new game.

You don't need Python, Godot, or any other dev tools installed. The ZIP is
self-contained.

Hotkeys
-------
F3   Toggle the debug overlay (FPS, tick count, unit count, sim status)
F12  Capture a bug report ZIP. The ZIP lands in data/logs/reports/. After
     capture, the path is copied to your clipboard so you can paste it into
     Discord or email.
ESC  Pause menu (Resume / Settings / Exit to Main Menu).

Where the game writes files
---------------------------
Everything is local to the extracted folder. Nothing is sent anywhere.
- data/                   Saves, settings, privacy flag
- data/logs/godot.log     Godot's own log
- data/logs/sim_stderr.log Sim diagnostic output
- data/logs/crash_report.txt Sim crash report (if the sim ever crashes)
- data/logs/reports/       F12 bug report ZIPs

If the game won't start
-----------------------
1. Try running OuroborosManifold.exe again — first launch can be slow.
2. Press F3 once you reach the main menu to see whether the sim connected.
3. Look at data/logs/sim_stderr.log and data/logs/godot.log — these often say
   exactly what went wrong.
4. If the game crashes, send the entire data/logs/ folder back to Westley
   along with feedback.txt.

Sending feedback
----------------
Open feedback.txt in any text editor, fill in what you can remember, save,
and email it back to Westley. If you hit a bug, attach the F12 bug report
ZIP (data/logs/reports/<timestamp>.zip).

This is a private playtest build. Please don't redistribute.
