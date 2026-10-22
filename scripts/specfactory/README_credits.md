# Console-credit tools

`sdk_engineer.py` and `batch_review.py` spend the Console credits instead of the subscription. Both are dry-run
safe: `sdk_engineer.py --dry-run` and every `batch_review.py` build (the default) touch no network and need no key.

## The plan

Judgement and building stay in the subscription chats. The credits pay for two kinds of work that suit them.
**SDK engineers** (`sdk_engineer.py`): a Claude Code agent in a throwaway worktree for read-heavy clerk work (audits,
grep-and-report, drift checks, landing clerks), one brief in, one report out, capped by `--max-budget-usd` and
`--max-turns`; one run has a floor near four cents (one measured "say hello" run on Sonnet 5.5: $0.04, about 21k
tokens of Claude Code prompt and tool definitions). **Batch** (`batch_review.py`): work that needs no tools and
no waiting at half price, results in about an hour: one drift audit per epic and one review per story shot.

## Setup

`python3 -m venv` fails on this machine (no `python3.14-venv`), so the tools' environment is built with uv:
`uv venv --python 3.12 ~/Projects/om-push/venv-sdk` then `uv pip install --python ~/Projects/om-push/venv-sdk/bin/python anthropic claude-agent-sdk pillow`
(installed 2026-10-21: anthropic 2.0.0, claude-agent-sdk 0.2.170 with Claude Code CLI 2.1.306 bundled, Pillow 13.0.0).
Dry runs and the tests need none of these packages (Pillow only to scale a shot wider than 1280 px). Below, `V` is
`~/Projects/om-push/venv-sdk/bin/python`.

## The key file

`~/.config/anthropic/api_key`: one line, the key and nothing else, mode 600, created by Westley:

    mkdir -p ~/.config/anthropic
    (umask 077; read -rsp 'API key: ' k; echo; printf '%s\n' "$k" > ~/.config/anthropic/api_key)
    chmod 600 ~/.config/anthropic/api_key

The tools read it only there, only at run time, only for a real run (`sdk_engineer.py` without `--dry-run`,
`batch_review.py --submit` or `fetch`), and refuse with this instruction if the file is missing, not mode 600, or
holds more than one word. Never `export ANTHROPIC_API_KEY` and never put it in a settings file or an `env` block:
Claude Code ranks the variable above the subscription login, so every chat that sees it silently bills the Console.
`sdk_engineer.py` hands the key to the agent process alone, as `env={"ANTHROPIC_API_KEY": key}`, and refuses to run
when `ANTHROPIC_AUTH_TOKEN` is set (Claude Code ranks that above the key).

## sdk_engineer.py

    V scripts/specfactory/sdk_engineer.py --worktree ~/Projects/om-push/wt/<name> --brief <brief.md> \
        [--model claude-sonnet-5-5] [--max-budget-usd 5] [--max-turns 60] \
        [--allowed-tools Bash,Read,Edit,Write,Grep,Glob] [--dry-run]

The worktree must be a linked worktree (a main checkout is refused). The agent runs with the standard Claude Code
prompt, `permission_mode="acceptEdits"`, `setting_sources=["project"]` (the worktree's `.claude/settings.json` deny
rules and git-guard hook, and its CLAUDE.md; nothing from `~/.claude`), and only the tools in `--allowed-tools`
(passed as both `tools` and `allowed_tools`, so there is no Task tool and no sub-agent). It has the same Bash a chat
has: the brief must name what it may touch. Assistant text streams to stdout; the result, token usage and cost land
in `<worktree>/.sdk_engineer_report.md` (untracked, delete it before the worktree is cleaned; the cost is the SDK's
client-side estimate, not a bill). Exit 0 ok; 1 agent error (budget or turn limit included) or bad arguments;
2 key file refused.

`--dry-run` output (no key read):

    {
      "cwd": "~/Projects/om-push/wt/arch-credits",
      "model": "claude-sonnet-5-5",
      "max_turns": 60,
      "max_budget_usd": 5.0,
      "tools": ["Bash", "Edit", "Glob", "Grep", "Read", "Write"],
      "allowed_tools": ["Bash", "Read", "Edit", "Write", "Grep", "Glob"],
      "permission_mode": "acceptEdits",
      "setting_sources": ["project"],
      "system_prompt": {"type": "preset", "preset": "claude_code"},
      "env": {"ANTHROPIC_API_KEY": "<read from ~/.config/anthropic/api_key at run time>"}
    }
    brief: <brief file> (20 chars); key file: ok (mode 600)

(The real output spreads each list over lines.)

## batch_review.py

    V scripts/specfactory/batch_review.py audit-epics   --out DIR [--samples N] [--model M] [--max-tokens N] [--root R] [--dry-run | --submit]
    V scripts/specfactory/batch_review.py story-reviews --out DIR [--model M] [--max-tokens N] [--root R] [--dry-run | --submit]
    V scripts/specfactory/batch_review.py fetch BATCH_ID --out DIR     # needs the key; never polls, run it again later
    V scripts/specfactory/batch_review.py digest --out DIR             # rebuild digest.md from DIR/results.jsonl, offline

`--model` is `claude-sonnet-5-5` (default) or `claude-fable-5-1`. A build writes `DIR/requests.jsonl` (the Batch API
request list) and `DIR/index.json` (what each custom_id is, used by the digest), prints the count and the estimate,
and stops. `--submit` also sends the batch and writes `DIR/batch_id.txt`; `fetch` (same `--out`) writes
`results.jsonl` and `digest.md` once the batch has ended. The estimate uses chars/4 plus 2,700 tokens per image for
input (dense JSON tokenises worse than prose, so read the shots' input as a floor) and `--max-tokens` (8000 for
epics, 1500 for shots) for every request's output (a ceiling), at batch rates (Sonnet 5.5 $1/$5, Fable 5.1 $5/$25
per MTok in/out). A batch is limited to 100,000 requests or 256 MB.

**audit-epics**: one request per `docs/bible/epics/E-*.md`: the epic text plus the rows of
`docs/northstar/plans/push_ledger_2026-09-22.md` that name one of the epic's own rule ids (the `- R-###-##` lines),
asking for a table of drift between the rules and those rulings. `--samples N` repeats each epic with a different
system nonce. Most ledger rows report tests and builds rather than rulings, so expect sparse drift; E-02 and E-21
have no rows and are still sent.

**story-reviews**: one request per shot, the newest run per file stem under
`docs/northstar/story_reviews/shots/`: the PNG (scaled to 1280 wide if wider), its state json (`<stem>.state.json`,
`<stem>.json` or `<stem>.qa_state.json`), the story's words from `docs/bible/stories.md` and the epic's rule lines
for it. The story id comes from the file name (`S-103`, `s010`) or from the lane row in
`docs/northstar/story_reviews/*.md` that lists the PNG. The reply is one line, `yes.` / `no.` / `unclear.` plus
evidence; the digest turns each into a queue row (lane from an earlier row naming the story, else `?`; Westley
verdict `pending`) for a clerk to paste into the lane file. Shots with no story id or no state json are listed as
skipped, never silently dropped. References images (`docs/bible/references/E-##/`) are not included.

Dry runs against this checkout (2026-10-21; `V` any Python 3.10+ for the build, Pillow for the 1920-wide shots):

    audit-epics: 22 requests, model claude-sonnet-5-5, max_tokens 8000, 0.8 MB, 0 skipped
    estimate (batch rates $1/$5 per MTok): input ~205,380 tok = $0.21, output at most 176,000 tok = $0.88, total ~$1.09
    story-reviews: 34 requests, model claude-sonnet-5-5, max_tokens 1500, 20.4 MB, 16 skipped
    estimate (batch rates $1/$5 per MTok): input ~1,060,365 tok = $1.06, output at most 51,000 tok = $0.26, total ~$1.32

With `--model claude-fable-5-1` the same builds estimate about $5.43 (epics) and $6.58 (shots); `--samples 2` doubles
the epic build (44 requests, about $2.17 on Sonnet 5.5). The 16 skipped shots are prototype and mode shots with no
story id, and `S-108-galaxy.png` (its newest run has no state json).

## Checked, and not

Tests: `tests/specfactory/test_credits_tools.py` (key-file rule, both builds, digest, `sdk_engineer --dry-run`; no
network). Submit and fetch were run once against a mock HTTP transport with the real `anthropic` client types, not
against the API. Nothing here has run a batch. One `sdk_engineer.py` run has gone through to the API (the "say hello"
run above) and the Claude Code CLI accepted every option it passes. Before the first paid batch, read one request in
`requests.jsonl`.
