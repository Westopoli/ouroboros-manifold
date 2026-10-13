# Method check at every compaction (Westley, 2026-10-10)

The nine method rev 2 rules were written on 2026-10-10 and both chats followed them that afternoon. Westley's concern is the week after: a chat that compacts five times a day keeps only what its summary kept, and the first rule it drops is the one it was breaking anyway. So the drift check gains a third half, beside the status diff after every landing and the weekly rulings audit: at every compaction, a hook runs a script over the chat's own transcript and prints, rule by rule, how many turns broke it since the previous compaction, with the decisive lines, followed by the role's rule list. The chat reads that before it reads anything else, so the rules re-enter context exactly where the summary could have lost them, and the count is computed, not remembered.

## Script: `scripts/specfactory/method_check.py`

Stdlib only. Exit status 0 always: a hook must never block a session. Input is the `SessionStart` hook's JSON on stdin (`transcript_path`, `session_id`, `source`) or `--transcript <path>`; options `--live-checkout <path>` (default `~/Projects/ouroboros-manifold`, resolved) and `--threshold <tokens>` (default 400000). Unreadable input prints one line, `METHOD error <reason>`, and exits 0.

The transcript is the session's `.jsonl`: one JSON object per line, skipped when it does not parse. Only entries with `type` `assistant` or `user` and `isSidechain` not true count (sub-agent turns live in their own files). A compaction marker is a `user` entry with `isCompactSummary` true. The entries split into spans at the markers; the reported **span** is the last span that holds at least one assistant entry, so a hook that fires right after a compaction reports the turns that led to it. **Session** is every entry in the file. An assistant entry's tool calls are the `tool_use` blocks of `message.content` (`name`, `input`); its context size is `message.usage` `input_tokens` plus `cache_read_input_tokens` plus `cache_creation_input_tokens`; its model is `message.model`.

Role: from the model of the span's last assistant entry (2026-10-12: the Dispatcher's session began with two Opus turns on 2026-10-06 before its Sonnet resume, and "any mix is unknown" demoted every Dispatcher-only check to REVIEW for six days). A model containing `sonnet` is the **dispatcher**; `fable` or `opus` is the **architect**; anything else is **unknown** (both rule lists print; the role-specific checks run as REVIEW). The header's `model` field names that last model; when the session holds more than one model, it reads `<last model> (session also <others>)`.

The live checkout path is compared after `os.path.realpath` on both sides; a path is "under" it when it equals it or starts with it plus a separator. A git checkout for the Dispatcher's repo-edit check means the live checkout or any path under `~/Projects/om-push/wt/`. The memory directory (`~/.claude/projects/`) and the scratchpad (`/tmp/`) are never repo paths.

Bash command text is matched after two reductions, so that a command that only mentions a word is not counted as running it (2026-10-10 smoke run: a heredoc writing this page counted as polling, and `grep merge_gate.sh` as a gate run). First, heredoc bodies are removed: from a `<<` or `<<-` operator and its terminator word to the line holding that terminator. Second, the remaining text is split into segments at `&&`, `||`, `;`, `|` and newlines, and each segment's first word is read (a leading `cd <path>` segment is just another segment). A segment counts for `polling` when its first word is `sleep` or `flock`, or when it names `gate.lock` and its first word is not a reader; for `gate_runs` when it names `merge_gate.sh` or `pre_gate.sh` and its first word is not a reader; for `live_reads` when its first word is a reader and it names a path under the live checkout. Readers are `cat`, `sed`, `head`, `tail`, `grep`, `ls`, `wc`, `echo`, `git`, `stat`, `du`, `find`, `awk`, `diff`, `python3`.

### Checks

Each check counts turns in the span and in the session. The verdict column says which count sets DRIFT; REVIEW checks print their counts and never set DRIFT.

| id | what is counted | roles | DRIFT when | rule line printed |
|---|---|---|---|---|
| `wakeups` | `ScheduleWakeup` calls | both | span count > 0 | No scheduled wakeups: the wait is the Workflow or Agent notification (CLAUDE.md Usage discipline; dispatcher.md step 3). |
| `polling` | `Monitor` calls; Bash commands containing the word `sleep`; Bash commands naming `gate.lock` | both | span count > 0 | No chat sits in a wait loop or polls a gate; clerks inside scripts do (dispatcher.md "What it never does"). |
| `gate_runs` | Bash commands naming `merge_gate.sh` or `pre_gate.sh` | both | span count > 0 | Gates run inside landing clerks, never in a chat (rules.md section (b)). |
| `spawn_model` | `Agent` calls whose input has no `model` | both | span count > 0 | Every spawn names its model (CLAUDE.md Task matching). |
| `fable_spawns` | `Agent` calls with `model` containing `fable` or `opus`, or `subagent_type` `fork`, except `subagent_type` `architect` when the role is dispatcher | both | span count > 0 | Engineers and doers are never Fable; `architect` is spawned only by the Dispatcher (CLAUDE.md Task matching). |
| `live_tree` | `Edit`, `Write`, `NotebookEdit` whose `file_path` is under the live checkout; Bash commands whose entry `cwd` is the live checkout, that contain `git` followed by one of `add`, `commit`, `push`, `checkout`, `switch`, `merge`, `stash`, `reset`, `rm`, `mv`, and that do not name `om-push` | both | span count > 0 | Never touch `~/Projects/ouroboros-manifold` as a working tree; work in a worktree under `~/Projects/om-push/wt/` (CLAUDE.md Git; dispatcher.md "What it never does"). |
| `code_edits` | `Edit`, `Write`, `NotebookEdit` whose `file_path` ends in `.c`, `.h`, `.gd`, `.py`, `.sh`, `.tscn`; Bash commands that redirect (`>`, `>>`) or `tee` into such a path | architect | span count > 0 | The Fable chat writes no code; Sonnet doers do. It writes specs, briefs, workflow scripts and docs (CLAUDE.md Task matching; `feedback-no-code-from-thinker`). |
| `repo_edits` | `Edit`, `Write`, `NotebookEdit` whose `file_path` is under any git checkout (live or `om-push/wt`) | dispatcher | span count > 0 | The Dispatcher edits nothing in the repo: tests, sources, bible, register, specs, scripts; record clerks do (dispatcher.md "What it never does"). |
| `main_push` | Bash commands containing `git push` whose refspec names `main` (`:main`, ` main`, `main ` after the remote) | dispatcher | span count > 0 | The Dispatcher never pushes to main; the landing clerk does (dispatcher.md "What it never does"). |
| `context` | assistant turns whose context size exceeds the threshold; the line also prints the span's largest | both | span count > 0 | Restart from memory past about 400k context; the compaction is not the restart (CLAUDE.md Usage discipline; dispatcher.md step 8). |
| `messages` | `SendMessage` calls | both | never (REVIEW) | Cross-chat messages are relayed by Westley; a chat that receives one pauses for him except for small blockers (CLAUDE.md Task matching). |
| `live_reads` | `Read` calls whose `file_path` is under the live checkout but not under its `.claude/`; Bash segments whose first word is a reader and that name a path under the live checkout | both | never (REVIEW) | Read `origin/main` (`git show origin/main:<path>`), not the live checkout, which lags main and carries Westley's uncommitted work (the two context files). |
| `workflows` | `Workflow` calls | both | never (REVIEW) | At most two build workflows and one landing in flight (CLAUDE.md Workflow specs). |

A role-specific check that does not apply to the detected role is not printed.

### Output

Plain text on stdout, every line prefixed `METHOD`, in this order:

```
METHOD role <dispatcher|architect|unknown> model <model or mixed> session <first 8 of session_id> span <k> of <n> turns <assistant turns in span> since <ISO timestamp of the span's first entry>
METHOD <check> <OK|DRIFT|REVIEW> span <count> session <count>  <rule line>
  <timestamp> <tool name> <excerpt>
METHOD verdict <OK|DRIFT>
METHOD rules <role>
- <rule line>
METHOD next: quote every DRIFT line to Westley in your first message after this compaction, before any other work, and stop the behaviour. A DRIFT line is never argued away: a rule change is Westley's to make; a justified exception is a ledger row.
```

The excerpt lines: at most three per check, from the span (from the session when the span count is 0 and the session count is not), each the entry's `timestamp`, the tool name and the first 100 characters of the command, path or agent input (model and subagent_type for `Agent`), on one line. The `context` check's excerpt is `<timestamp> context <size>` for the three largest turns. The verdict is DRIFT when any printed check is DRIFT on the span count.

`METHOD rules` prints, for the role, the rule lines of the checks that apply to it (the table's last column) and then these lines, which no count can verify:

- both: Answers are not a go; nothing launches or builds without Westley's explicit word (`feedback-answers-are-not-go`).
- both: Pre-flight before any launch, every precondition checked by reading or running, never from memory (CLAUDE.md Workflow specs).
- both: Sub-agents never spawn sub-agents; every brief says so (CLAUDE.md Task matching).
- both: Westley owns every threshold, tolerance and pass mark; a real finding is never reclassified as a skip (CLAUDE.md Tests are the spec).
- both: Agents report once, at the end; no interim notices, no background waits that wake the parent (CLAUDE.md Usage discipline).
- dispatcher: Status lives in the lane table only; the Dispatcher keeps no copy and decides nothing about rules, thresholds, specs or tests (dispatcher.md "What it owns").
- dispatcher: Consults go to `subagent_type: architect` with a brief under a page; contract changes and new spec sections go to the Architect chat (dispatcher.md step 5).
- architect: Specs and scripts are handed to the Dispatcher to launch; the Architect launches, polls, lands and keeps status for nothing (context_architect "What you do not do").
- architect: One lane's detail in context at a time; ledger, register and epic updates are committed and pushed as they happen (context_architect; CLAUDE.md Git).

For the unknown role, both lists print.

## Hook

`.claude/settings.json` registers it under `hooks.SessionStart` with matcher `compact`:

```
python3 "$CLAUDE_PROJECT_DIR/scripts/specfactory/method_check.py" 2>/dev/null || echo "METHOD error hook: method_check.py did not run from $CLAUDE_PROJECT_DIR (script missing or failed); run it by hand on this session and tell Westley"
```

A `SessionStart` hook's stdout enters the chat's context, so the report is the first thing the chat sees after its compaction. Claude Code reads the hook table when a session starts, from the project of the directory the session was started in: a chat started from another directory (the Dispatcher of 2026-10-10 to 10-12 ran from `~/Projects/Jarvis`) never loads this project's hooks, and a chat started before the hook landed, or in a checkout that has not pulled it, runs without it. Measured 2026-10-12, 36 hours after the landing: six compactions across the two chats, zero reports, for all three reasons. A chat that sees no `METHOD` lines after a compaction runs the script by hand on its own transcript and says so. The hook line echoes a `METHOD error hook:` line instead of staying silent when the script is missing. By hand, on any session: `python3 scripts/specfactory/method_check.py --transcript ~/.claude/projects/-home-westopoli-Projects-ouroboros-manifold/<session id>.jsonl`; Westley can ask either chat to run it on itself at any time.

## Test: `tests/specfactory/test_method_check.py`

Written by a Sonnet test writer before the script exists (rules.md section (d)); red on the tree without the script. Fixtures are synthetic `.jsonl` files built in `tmp_path` with the entry shapes named above; no test reads a real transcript. It covers: the positive control (a clean Dispatcher transcript prints every check `OK` and `METHOD verdict OK`); a Dispatcher transcript with one turn each of `wakeups`, `polling`, `spawn_model`, `fable_spawns`, `live_tree`, `main_push` and two turns over the threshold, ending in a compaction marker (span counts 1, 1, 1, 1, 1, 1, 2 and `verdict DRIFT`); the same file plus one clean turn after the marker (span counts 0, session counts unchanged, `verdict OK`); an Architect transcript with a `Write` to a `.gd` path, an `Agent` call with `subagent_type` `architect`, and a Bash `merge_gate.sh` run (`code_edits`, `fable_spawns`, `gate_runs` DRIFT; `repo_edits` and `main_push` not printed); role `unknown` for a model naming neither; role `dispatcher` when two early turns are `claude-opus-5-5` and the last is `claude-sonnet-5-5`, with the header model reading `claude-sonnet-5-5 (session also claude-opus-5-5)`; `--threshold`; the stdin JSON input; a missing path and a line that is not JSON (`METHOD error` or the line skipped, exit 0 either way); a Bash heredoc whose body says `sleep` and `merge_gate.sh`, a `grep merge_gate.sh scripts/x` segment and a `git show origin/main:scripts/specfactory/merge_gate.sh` segment count for nothing, while `sleep 120`, `flock ~/Projects/om-push/gate.lock x` and `cd /w && bash scripts/specfactory/merge_gate.sh wt main P` count for `polling`, `polling` and `gate_runs`; the rule lists (`METHOD rules dispatcher` holds "names its model" and "lane table"; `METHOD rules architect` holds "writes no code").

## Landing

Piece `HARNESS-methodcheck` in `pieces.toml` (owns the script, the test, the hook line in `.claude/settings.json` and this page). Docs touched in the same change: CLAUDE.md guard 7, the programme file (item 6 and guard 7), rules.md section (f), dispatcher.md step 8, `context_architect_2026-10-10.md`. The landing clerk runs `merge_gate.sh --revert` and the piece's test under the gate lock and pushes; the first real reports come from the two chats' next compactions.
