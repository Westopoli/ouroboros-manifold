# Spec 01: land CLAUDE.md and the engineer agent definition on main

You are a Claude Sonnet 4.6 worker chat. You execute this spec directly. You do not spawn agents, redesign, or widen scope. You do exactly the steps below, then push and stop.

## Why

`~/Projects/ouroboros-manifold/CLAUDE.md` holds two edits that are not on main yet: a "Usage discipline" section under Task matching, and the Engineer tier moving from Sonnet 5 to Sonnet 5.5 (`TEST_WRITER = sonnet55`). `.claude/agents/engineer.md` is a new file pinning that tier to `model: claude-sonnet-5-5`. Both must land so every chat and agent reads the same rules.

## Where

Repo: `~/Projects/ouroboros-manifold`. This is Westley's live checkout and it has other uncommitted changes (`project.godot`, `.claude/settings.json`, `.claude/settings.local.json`, `.claude/agents/sonnet46-doer.md`, several `.uid` files, a `mockup_feedback` directory). **You do not touch any of those.** You do not pull, rebase, stash, or check out another branch in this checkout.

## Files you may stage

- `CLAUDE.md`
- `.claude/agents/engineer.md`

Nothing else.

## Steps

1. `cd ~/Projects/ouroboros-manifold && git status --short` and confirm both files appear (`M CLAUDE.md`, `?? .claude/agents/engineer.md`).
2. `git diff origin/main -- CLAUDE.md`. Expect exactly: the Engineer row says `(Sonnet 5.5)`, the line `` `DOER_BACKEND = sonnet46` · `TEST_WRITER = sonnet55` ``, and a new "Usage discipline" paragraph with four bullets. If the diff contains anything else, stop and report it; do not commit.
3. `cat .claude/agents/engineer.md`. Expect frontmatter with `model: claude-sonnet-5-5` and a `tools:` line that does not include `Agent`. If it differs, stop and report.
4. Stage only the two files: `git add CLAUDE.md .claude/agents/engineer.md`.
5. Commit with a temporary index that leaves the working tree as it was:
   ```
   git commit -m "CLAUDE.md: usage discipline rules, Engineer tier on Sonnet 5.5

   Adds the four usage-discipline bullets (builders push and stop, agents report once, waits poll every 3 to 5 minutes, restart a large coordinator) and pins the engineer agent definition to claude-sonnet-5-5.

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
   ```
   This commits on the local `main`, which is behind `origin/main`. That is expected.
6. Push the commit as a branch, not to main: `git push origin HEAD:refs/heads/relay/01-claude-md`.
7. Confirm with `git status --short` that the other uncommitted files are still there, untouched.

## Checks

- `git show --stat HEAD` lists exactly the two files.
- `git diff origin/main..relay/01-claude-md --stat` (after `git fetch origin`) lists exactly the two files.

## Report (your last message, nothing after it)

```
Branch: relay/01-claude-md (commit <hash>)
Files: CLAUDE.md, .claude/agents/engineer.md
Checks: <the two check outputs, verbatim>
Open: <anything unexpected, or "none">
```

Note for the overlord: local `main` in this checkout is behind `origin/main`, so this branch is based on an older commit. It fast-forwards only if `origin/main` has not touched `CLAUDE.md` since; if `git merge-base --is-ancestor origin/main origin/relay/01-claude-md` fails, land it with `git cherry-pick` of the one commit onto a scratch worktree at `origin/main` and push that. Do not rebase the live checkout.
