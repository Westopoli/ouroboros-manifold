# Spec 02: write four of Westley's answers into the register and the bible

You are a Claude Sonnet 4.6 worker chat. You execute this spec directly. You do not spawn agents, redesign, or widen scope. Docs only; you touch no code and no tests.

## Why

Westley answered four ambiguity flags on 2026-09-28. The answers were recorded in a chat's notes but never written into `docs/northstar/ambiguity_register.md` or the epic files, so the flags still read `open` on main and the rules they change still carry the old text. The bible describes what the game does now; this closes the gap.

## Where

Your own clone, never `~/Projects/ouroboros-manifold` (Westley's live checkout):
```
git clone --branch main "$(git -C ~/Projects/ouroboros-manifold remote get-url origin)" ~/Projects/relay-02
cd ~/Projects/relay-02 && git checkout -b relay/02-register-answers
```

Branch: `relay/02-register-answers`.

## Files you may edit

- `docs/northstar/ambiguity_register.md`
- `docs/bible/epics/E-03-world-generation.md`
- `docs/bible/epics/E-10-missions.md`
- `docs/bible/epics/E-16-client-camera-hud-and-world-view.md`
- `docs/bible/epics/E-09-chronicle.md`

Nothing else. If an answer forces a change in another file, list it under Open in your report instead of making it.

## Bible editing rules (from CLAUDE.md)

- Rewrite, never append. Replace the old wording; do not add "update:" notes beside it.
- Ambiguity is flagged, never guessed. If an answer below does not settle something a rule needs, add a new `Q-` row with two or three candidate answers and status `open`, and leave the rule pointing at it.
- Register rows keep their schema: `| Flag | Epic / story | Question | Candidate answers | Status | Answer |`. Closing a row means status `closed` and an Answer cell that quotes Westley and gives the date.

## The four answers (Westley, 2026-09-28; quote these)

**Q-021-08** (E-03, budgets at 400 regions):
> Governing budget: a time jump of 150 ticks (1 tick = 1 in-world year, R-056-01) at 400 regions completes in under 2 s. During that wait a transition animation plays, stubbed for now by reusing the boot loading animation, and "boots up" the galaxy view. Per-module micro budgets are informational under it. Measured cost is about 2 ms per pipe step, so about 0.3 s for 150 ticks.

**Q-077-02** (E-10, the commander unit):
> The player picks which ship the commander is in, and can move them from ship to ship. Later (stub in the bible as "to be determined"): the commander's fate is not the ship's health but a chance of being wounded or killed, rising the more fire the ship takes (a falling beam, being in a destroyed section). For the MVP, R-077-05 changes from a "dedicated unit" to "the player assigns the commander to a unit and may reassign it".

**Q-106-02** (E-16, galaxy fps budget at 250 to 400 systems):
> 60 fps on a GTX 1070 with automatic fallback, confirmed. Much more visual and algorithm-efficiency work comes before launch.

**Q-068-02** (E-09, how a chronicle entry names a character):
> Option (b): the sim records the actual character on each chronicle entry.

## Steps

1. Register: for each of the four rows, set Status to `closed` and fill Answer with the quote above, prefixed `Answered by Westley, 2026-09-28.` Keep the Question and Candidate answers cells as they are.
2. E-03: find the budget paragraph that starts `Confirmed by Westley, 2026-09-15` (around line 131) and any `[Q-021-08 ...]` reference. Rewrite the budget so it states the governing budget (a 150-tick jump at 400 regions completes in under 2 s, with the transition animation, stubbed by the boot loading animation, covering the wait) and says the per-module micro budgets are informational under it. Keep the existing generation budget sentence if the answer does not contradict it. Remove the Q-021-08 flag from any "Open flags" line in that epic.
3. E-10: rewrite R-077-05 (around line 122) so the rule reads that the player assigns the commander to one of their units at deploy and may reassign them to another unit during the mission, that the assigned unit's id is held in mission state, and that R-077-03 reads commander fate from it. Delete the `[Q-077-02 ...]` bracket and the `(Westley, 2026-09-28: a dedicated unit.)` note. Add one sentence marking the chance-based fate as to be determined after the MVP: the fate will be a chance of wounding or death that rises with the fire the unit takes, not the unit's own survival. Update the S-077 "Open flags" line so it no longer lists Q-077-02 (Q-077-01 stays only if the register still shows it open; check).
4. E-16: find the fps budget sentence (around line 202, "galaxy view at 60 fps with 60 systems") and rewrite it to 60 fps at 250 to 400 systems on a GTX 1070 with the automatic quality fallback allowed. Remove Q-106-02 from any "Open flags" line.
5. E-09: find where Q-068-02 is referenced (grep; it may be only in the register). If a rule near R-068-03 says entries carry only a lineage ref, rewrite it so each chronicle entry records the character it concerns and `{character_name}` renders from that. If the epic has no such rule, add nothing to the epic and note it under Open.
6. `grep -rn "Q-021-08\|Q-077-02\|Q-106-02\|Q-068-02" docs/` and confirm every remaining mention is in a closed context (a register row, or a "closed by" note), not an open flag.
7. Commit the five files (stage them by name) with a plain-prose message ending `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`, then `git push origin HEAD:refs/heads/relay/02-register-answers`. Stop.

## Checks

- Step 6's grep output.
- `git diff origin/main --stat` lists only files from the allowed list.

## Report (your last message, nothing after it)

```
Branch: relay/02-register-answers (commit <hash>)
Files: <list>
Checks: <grep output; diff --stat>
Open: <new Q- rows you added, files you could not change, or "none">
```
