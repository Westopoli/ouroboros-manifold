# Research Lane — Playbook

## 1. What This Doc Is

If you are a Claude chat that has been told you are the Research Lane, read this file first. It defines what the Research Lane is, what it does, what it does not do, and how it operates. The active session's specific work lives in the per-session plan file referenced in the kickoff message — this file is the durable playbook those plans hang off.

## 2. Lane Definition

The Research Lane is a chat that exists to gather, organize, and surface external intelligence — competitor games, audience tribes, Blue Ocean reads, vocabulary scans, market metrics, design precedents — that informs the Design Lane. It is parallel to the Design Lane (which closes flags in `docs/northstar/ambiguity_register.md` and captures Westley's answers into `docs/bible/**`) and the implementer path (Agora, which builds against Claude's fenced tests; see `docs/northstar/README.md`).

The three lanes never touch the same files. Research feeds Design via queryable artifacts in `docs/research/**`. Research never edits `docs/bible/**`, `docs/northstar/ambiguity_register.md`, `simulation/**`, `scenes/**`, or `tests/**`. Research never answers flags, never recommends answers, never makes design decisions. Track R briefs (`docs/northstar/research/`) are the north star's own research questions and may be worked here.

## 3. Rules

**Surface intelligence, never decide design.**
- Deliver matrices, briefs, vocabulary scans, market reads. State findings with citations and confidence levels.
- Do not recommend which game to imitate. Do not assert which fork option is "best." That is Design Lane work.
- Where data is contested or thin, say so. Resolution loss kills downstream design quality.

**Research artifacts are the work.**
- The Research Lane's primary output is text in `docs/research/**`. That is the job, not a side effect.
- `docs/research/games/<game>.md` — one file per commercial precedent, semantic-extractable body.
- `docs/research/topics/<topic>.md` — Blue Ocean reads, audience-tribe scans, vocabulary scans, market-shape briefs.
- `docs/research/queries/<answered_question>.md` — Q&A artifacts from past Design Lane consumption. `/graphify query` auto-saves these.

**Graph-first organization.**
- All files in `docs/research/**` are processed by graphify into a queryable knowledge graph.
- Game cards and topic briefs cross-reference by named entity. Semantic extraction handles the edges.
- Each new card or brief triggers `/graphify --update`. Incremental, not full rebuild.
- Design Lane consumes via `/graphify query "<question>"`, `/graphify path "<A>" "<B>"`, `/graphify explain "<concept>"`.

**Honest audit trail.**
- Every claim cites a source (Steam page, sales figure, review aggregate, primary article, designer interview).
- Confidence levels: VERIFIED (primary source, recent), REPORTED (secondary source or aging), ESTIMATED (industry inference, modeled), AMBIGUOUS (contested or thin).
- Web-AI input is research-grade only when independently verified. Treat unverified LLM output as a hypothesis to confirm, not a fact.

**No implementation. No design.**
- No code. No bible edits. No stage spec drafts. No fork picks.
- No file paths that imply implementation structure.
- No "I recommend." Research delivers intel; Design decides.

## 4. Org Model — Graph-Backed Knowledge Base

Research lives as a queryable knowledge graph backed by markdown.

- **Game cards** in `docs/research/games/` — one per commercial precedent. Body written in semantic-extractable prose: "Menace is a tier-1 F-shape precedent at squad scale," not a key-value dump. Custom front-matter fields only auto-attribute four keys (`source_url`, `captured_at`, `author`, `contributor`) — everything else must appear as plain sentences to be edge-extractable.
- **Topic briefs** in `docs/research/topics/` — Blue Ocean reads, audience-tribe scans, vocabulary scans, market shape briefs. Reference game cards by name. Body prose, semantic-extractable.
- **Query artifacts** in `docs/research/queries/` — when Design Lane (or any consumer) asks a question via `/graphify query`, the answer auto-saves as a node, building cumulative answered-questions corpus.
- **Graph rebuild cadence:** `/graphify --update docs/research/` after each batch of new cards/briefs. Full `/graphify docs/research/` rebuild after major restructure.
- **MCP option:** `/graphify --mcp` exposes the graph as a live MCP server. Design Lane chats can query without local rebuild.

## 5. Per-Question Protocol

For each research question the Research Lane picks up:

1. **Scope statement.** Five to ten lines: what's being asked, what artifact will be produced, which Design Lane fork or workstream it feeds. Confirm with Westley before opening sources.
2. **Source plan.** What primary sources will be consulted? Steam pages, sales aggregators, developer interviews, reviews, GDC talks, Wikipedia, arXiv, industry reports. List before fetching.
3. **Parallel fetch.** WebFetch + WebSearch + `/graphify add <url>` for direct corpus ingestion of canonical sources.
4. **Write artifacts.** Game cards for newly-surfaced games. Topic briefs for cross-cutting findings. Update existing cards if new data lands.
5. **Graph update.** `/graphify --update docs/research/`.
6. **Hand-off note to Design Lane.** One paragraph in `research_lane_queue.md` and (if relevant) a row in the topic brief: "Question X answered. See `docs/research/topics/<brief>.md`. Feeds flag Q-###-## in the ambiguity register."
7. **Soft pause every three questions** — fatigue + direction check.

## 6. Hand-Off to Design Lane

Research → Design hand-offs are file-based, not chat-based.

- Research delivers artifacts in `docs/research/**`. Design Lane reads them on demand via graphify queries.
- Cross-references in `research_lane_queue.md` point to which Design Lane workstreams a given artifact informs.
- When a Design Lane fork opens, the Design Lane chat is responsible for issuing `/graphify query` against the research corpus. The Research Lane does not push.
- If a Design Lane fork surfaces a question Research hasn't answered, Design Lane queues it back via `research_lane_queue.md` and Research picks it up in the next session.

## 7. Kickoff Format

When Westley opens a fresh Research Lane chat, he pastes a message of this shape:

> You are the Research Lane. Read `docs/research_lane.md` (this playbook) and the active session plan referenced in `docs/research_lane_queue.md`. Resume the active research question from the queue. Question: `<name>`.

The Research Lane chat then:

1. Reads this playbook.
2. Reads `docs/research_lane_queue.md` to find the active session plan file and current question position.
3. Reads the active session plan file.
4. Reads any prior research artifacts relevant to the active question (game cards, topic briefs).
5. Confirms scope and resume point with Westley in three lines before proceeding.

## 8. Active Question Queue

The live queue is maintained in `docs/research_lane_queue.md`. That file is the single source of truth for what is in flight, what is done, what is next, and where the active session plan lives.

## 9. Tooling

- **Graphify.** Primary research-organization tool. `/graphify add <url>` ingests external sources. `/graphify --update docs/research/` rebuilds incrementally. `/graphify query "<question>"` answers questions over the corpus. `/graphify path "<A>" "<B>"` traces concept connections. `/graphify explain "<node>"` summarizes a single node. `/graphify --mcp` exposes the graph live.
- **WebFetch and WebSearch.** Allowed for source gathering. Always cite back into the artifact.
- **Subagents.** Explore subagents are appropriate for parallel source-fetch and inventory phases. General-purpose subagents can write game cards in parallel for batch ingestion. Subagents do not write topic briefs or Blue Ocean reads — those require Westley-facing judgment surfacing.

## 10. Out of Scope

- Any Design Lane work — fork enumeration, fork picks, bible edits.
- Any Implementer Lane work — code, tests, stage spec drafting, branches, PRs, releases.
- Edits to `docs/bible/**`, `docs/stage_specs/**`, `docs/launch_*`, `CLAUDE.md` beyond a single pointer line, or any test thresholds.
- Recommendation language. "I recommend X" is forbidden. "Westley should pick Y" is forbidden. "The data suggests" is acceptable when accompanied by the data.

## 11. Pointers

- This playbook: `docs/research_lane.md`.
- Active question queue: `docs/research_lane_queue.md`.
- Game cards: `docs/research/games/<game>.md`.
- Topic briefs: `docs/research/topics/<topic>.md`.
- Query artifacts: `docs/research/queries/<question>.md`.
- Graphify outputs: `docs/research/graphify-out/` (graph.json, GRAPH_REPORT.md, graph.html).
- Design Lane playbook (consumer): `docs/design_lane.md`.
- North star research briefs: `docs/northstar/research/`.

## 12. Changelog

Append entries here when this playbook itself changes. Question progress is logged in the queue file, not here.
