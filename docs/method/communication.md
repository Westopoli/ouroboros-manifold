# Communication: mail and station

How chats talk to each other and when a chat wakes. Written 2026-11-03 from the plan "the mail-and-station communication method" (Westley approved 2026-11-03; DEC-mail-station-2026-11-03). Lands in five stories, H-077 to H-081 (`harness.md`); until each lands, the sentence it owns is a design, and the card it rewrites still says the old thing. Where a card and this page disagree before the story lands, the card wins; after, this page.

## Why

In the week of 2026-10-27 the chat layer (Architect, two Dispatchers) cost seven times the builder layer per landing: 94 chat turns per landing at a median 168k context, woken 686 times by sub-agent completions and 386 times by cross-chat messages; 643 messages sent, a quarter restating what `git log` already holds. A message is a wakeup, a wakeup is a whole-context re-read, and most messages did not need one.

## The rule

1. **Blackboard first.** State lives in git and is read with `scripts/method/status.sh`. A message that says something git can answer (landed, pushed, in flight, slots, sweep result) is not sent; `mail.py` refuses it. Rulings go into the story file and `decisions.md`; the message, if any, is one line pointing there.
2. **Mail, not messages.** Chats write to each other only through `scripts/method/mail.py send`. Cross-session `SendMessage` is denied by a hook (H-077). Sub-agents have no mailbox: they report once and stop.
3. **Woken, never polling.** A chat wakes on its own background completion (a Workflow or Agent result) or on its flag. The station raises the flag at once for a `block`, an `ask` to an agent with `rules = true`, and Westley's words; `info` waits for DRAFT-mail-linger or DRAFT-mail-batch. No Monitor, no scheduled wakeup, no `flock` wait, no `status.sh` turn.
4. **Every wakeup drains the mailbox.** The first tool call of every turn is `mail.py read --me <agent>`; a turn that leaves work in flight ends with one background `mail.py wait --me <agent>`, whose completion is the next wake, but only when the `read` ended with `WAIT none` (with `WAIT armed <n>` a wait is already armed and a second is not). A chat with nothing in flight and no unread mail stops; Westley's `go` restarts it.
5. **One launch per landing.** The runner launches `land_story` once per Ready story and hears about it once (H-079). The gate is a queue the clerk hands a ticket to (H-080).
6. **Kills are evidenced.** Processes are started through `proc.py start` and ended only by `proc.py reap` on recorded evidence (H-081).

## Agents and mailboxes

`docs/method/agents.toml` is the registry; one table per named chat. Adding a recipient is one table plus `mail.py register <name>`; the station re-reads the registry every loop, so no restart. Nothing in `mail.py` or `station.py` names an agent; every rule reads the registry.

```toml
[architect]
role = "architect.md"
rules = true                        # may receive `ask`; a second architect is one more table
wake = ["block", "ask", "westley"]  # classes that raise the flag at once
linger_min = 20                     # optional overrides of DRAFT-mail-linger / DRAFT-mail-batch
batch = 5
senders = ["*"]

[runner-lab]
role = "runner.md"
rules = false

[runner-beta]
role = "runner.md"
rules = false

[westley]
senders = []                        # nothing writes to him through mail

[gate-queue]                        # H-080's daemon; sends `info`, receives nothing
rules = false
senders = []
```

A planner that hands files to the Architect is `[planner]` with `rules = false`, sending `info` or `ask` with `--attach <path>`. `ask` is routed by role: `--to rules` reaches every agent with `rules = true`; the first to rule writes the story file and the others see it on the blackboard.

## Classes

| Class | Who sends | Flag | Example |
|---|---|---|---|
| `block` | a chat that cannot proceed | at once | "lab: GPU memory below 3 GiB, every landing waits; need a word on killing `wt/c-s2run`" |
| `ask` | a chat that needs a ruling | at once, `rules = true` agents only | "H-063 builder blocked: `terrain_set_heights` MUTATOR or read-only? story file line 40" |
| `westley` | the chat Westley typed in, relaying his words | at once | "Westley: go on H-077" |
| `info` | anyone | at linger or batch | "H-057 landed 3fa2c1; stack gate next" is refused (blackboard); "H-063 pictures for Westley are in westley/ at commit 9ab1" is allowed |

Mail is one JSON line in `~/Projects/om-push/mail/<agent>/inbox.jsonl`: `id`, `ts`, `from`, `to`, `class`, `re` (story id), `text` (under DRAFT-mail-max characters; longer text is a file and the mail carries the path), `attach`, `read`. The station logs every flag with its reason in `~/Projects/om-push/mail/station.log`. `mail.py` and `station.py` interfaces in full: `docs/stories/H-077.md`.

## Reading and waiting

Amended 2026-11-04 by H-086 (DEC-mailbox-fixes-2026-11-04) after a measured review of the shipped H-077 code against the plan. Until H-086 lands this section is a design: the code still cuts the digest at 200 characters, leaves the flag up after a read and lets waits pile up.

- **The digest is whole.** `read` and `wait` print every unread mail with its full text, one `MAIL <class> <from> <re> <ts>: <text>` line each, then `[attach: <paths>]`. The 1,500-character limit is enforced when sending, so nothing is cut when reading. (Before: the text was cut at 200 characters with no mark, and a ruling in the cut part never arrived.)
- **A read lowers the flag.** `read` moves the unread lines to `delivered.jsonl` and removes `mail/<agent>/flag`, under the agent's lock. The station takes the same lock, looks at the inbox again and raises the flag only if mail is still unread, so a flag never outlives the mail it was raised for. (Before: a chat that read at the top of a turn and then armed a wait was woken at once by an empty flag.)
- **One wait per chat, and a flag is taken once.** `wait` records itself in `mail/<agent>/waits/<pid>` (pid, start time, expiry, the chat process it belongs to). Of several waits armed for one agent only the one whose own removal of the flag succeeds returns with the mail; the others keep waiting. `read` ends its output with `WAIT none` or `WAIT armed <n>`; a chat arms a wait only after `WAIT none`. A record whose process is gone is dropped by whoever reads it.
- **A wait ends.** Without `--max` a wait ends after DRAFT-mail-wait-max (4 h) with `MAIL idle <s>s`. A wait whose chat process has ended exits at once and silently, never taking a flag or reading mail, so a restarted chat's mail is not swallowed by a wait nobody hears. `OM_MAIL_ANCHOR_PID` names the chat process in tests.

## Numbers

In the README register: DRAFT-build-slots 8, DRAFT-mail-linger 20 min, DRAFT-mail-batch 5, DRAFT-mail-max 1,500 characters, DRAFT-mail-stale 30 min, DRAFT-mail-wait-max 4 h, DRAFT-wakeups-per-landing 10, DRAFT-proc-ttl 4 h, DRAFT-queue-lookahead 1. The nightly report prints `wakeups_per_landing` and `messages_per_landing` (H-078) beside the week-of-10-27 baseline, 94 and 17.

## Enforcement

- Hook `.claude/hooks/mail-guard.sh` denies cross-session `SendMessage` (H-077); `.claude/hooks/kill-guard.sh` denies `kill`, `pkill`, `killall`, `fuser -k` outside `proc.py reap` (H-081).
- `scripts/specfactory/method_check.py` at every compaction: `comm_send` (a cross-session SendMessage), `comm_state_checks` (more than three state-check commands in one wakeup), `comm_mail_first` (a wakeup whose first tool call is not `mail.py read`); each a DRIFT line quoted to Westley.
- `scripts/specfactory/status_check.py`: `STATUS mail DRIFT <agent> <class> unread <min>m` when a `block` or `ask` is unread past DRAFT-mail-stale, or a sender is not in the registry; gates reject on any DRIFT.
- Nightly: over DRAFT-wakeups-per-landing is a method defect; the Architect names the wake source that grew and proposes the cut.

## Transition (2026-11-03)

The three chats in flight wrote handoff memories (`continuation-2026-11-03-{lab,beta,architect}-handoff.md` in the project memory directory) and stopped. H-077 and H-078 land under the old path with the hook in H-077's last (wiring) commit, so nothing mid-landing is denied. The three chats restart fresh under the rewritten cards; their first turn is `status.sh` then `mail.py read`. Landings in flight finish as they started; new launches go through `land_story` once H-079 lands and through the gate queue once H-080's daemon holds the channel locks.
