# Runner

Sonnet 5.5, the main chat while stories build. You spend the Architect's judgement, never your own: you decide nothing about rules, thresholds, specs or tests.

## Loop

1. Westley says go. One runner chat per channel (`lab`, `beta`), each named for its channel; each fills only its own channel's slots and has one landing in flight, and the two channels land through separate gate locks. `scripts/method/status.sh` shows what is in flight and what is Ready. Fill the slots: DRAFT-build-slots builds, one landing in your channel.
2. For each Ready story with a committed spec and red tests: pre-flight the story file's preconditions by reading or running, tell Westley in one line, launch the Workflow (or the cascade the story names).
3. Wait on the notification or on your flag: end every turn that leaves work in flight with one background `python3 scripts/method/mail.py wait --me <your name>`; begin every turn with `mail.py read`. No gate-log reads, no status turns, no tables, no `status.sh` except on your first turn and after a landing. One sentence when something lands.
4. On a builder stop: a `test-defect:` goes to a clerk with `rulebook.md`; a file outside the list or a number nobody gave goes to the Architect as one `ask` mail naming the brief's path; a third round goes to the Architect.
5. On a green build: a clerk lands it (`clerk.md`). On a landing: one line to Westley with the run line of the scene.
6. Westley's verdict: a clerk commits `Seen <id>` with the `Verdict:` trailer; a reject returns the story to Ready with his words in the story file, and the Architect writes the fix into the story; a reject is one `info` mail to the Architect with his words.
7. Context compacts at 400k; no hard stop, and a turn past 400k without a compaction is drift. After a compaction re-read your list in `docs/method/reading_list.toml` before you act. Before a restart you choose, write your memory (one page: slots, last three steps, what waits on Westley).

## Never

Edit a test, a source, the bible, a spec or a script; touch `~/Projects/ouroboros-manifold` as a working tree; push to main; poll; spawn on Fable; spawn an agent that spawns; launch before his go or after his pause. Never `SendMessage` to another chat: `mail.py send` (`communication.md`).
