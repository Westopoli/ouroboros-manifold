# Gemini Deep Research prompts, 2026-10-24 (method investigation, external half)

Run the three in parallel. Save each report as Markdown under
`docs/northstar/plans/retro_2026-10-24/` with the file name given at the top of each prompt.

---

## Prompt 1, file `research_single_session_games.md`

You are researching, for a solo game developer who uses frontier coding agents, whether complete small games are really being built in a single agent session, and what that evidence is worth. Cover the period from mid 2025 to today.

Find documented cases where one AI coding agent session (Claude Code, Codex, Cursor agent, Gemini CLI, or similar) produced a playable game. For each case report: the game's scope (genre, approximate lines of code, number of scenes or levels, assets used and where they came from, playtime), the engine or framework, the model and any mode such as effort level or extended thinking, the wall-clock time and cost if stated, what the human did during the session (prompts, testing, fixes), what was skipped (automated tests, determinism, multiplayer, saving, content, performance), and what happened afterwards (was it extended, did it break, was it shipped or sold). Prefer primary sources: public repositories with commit history, published session transcripts, itch.io or Steam pages, talks, detailed blog posts. Downgrade claims that exist only as social posts or demo videos without a repository.

Then compare these cases against what a two-week "simple beta" would need for a deterministic real-time strategy game with a C simulation, a Godot 4 client over a JSON pipe, and lockstep multiplayer planned: which parts of such a game have been shown built in single sessions, and which have never been.

Output: a table of cases with an evidence grade per row (A: repository plus write-up, B: write-up only, C: social post or video), then a two-paragraph synthesis of what single-session builds have and have not demonstrated, then a list of every source URL. Under 1,500 words plus the table. State plainly where the evidence is thin.

---

## Prompt 2, file `research_solo_agent_method.md`

You are researching how experienced solo developers and small teams get the most output from frontier coding agents on multi-week software projects, with attention to games. Cover mid 2025 to today.

Questions to answer with sources:
1. Test-driven development with agents: what do practitioners report about writing tests before code, having a separate agent write tests, and fencing tests from the builder? Where is there evidence that heavy test suites pay for themselves, and where that they slow a project down? Any numbers on test-to-code ratios or on time spent fixing wrong tests.
2. Single long session versus many small agents: Anthropic's, OpenAI's and Cursor's own published guidance on long-running agent sessions, context size, effort or thinking levels, sub-agents and when each wins; practitioner reports of what broke at large context; any measured cost comparisons.
3. Planning weight: how much written specification, ownership rules, ledgers and process documentation successful solo-plus-agent projects carry, versus projects that run on a short plan and playtests; any reports of process overhead exceeding product output.
4. Integration cadence: merge gates, continuous integration time, branches and worktrees in agent-driven projects; what cadence practitioners settled on and why.
5. Game-specific practice: how agent-built games are verified (automated tests, screenshot comparison, scripted playthroughs, human playtest), and what verification caught real bugs.

Output: for each question, the three strongest sourced findings with an evidence grade (A: primary data or official documentation, B: detailed practitioner write-up, C: opinion or anecdote), then a one-page synthesis titled "What the evidence says a solo developer with agents should and should not do", then every source URL. Under 2,000 words. Separate what is measured from what is asserted.

---

## Prompt 3, file `research_combining_and_failures.md`

You are researching two things for a solo game developer who uses frontier coding agents. Cover mid 2025 to today.

Part A, combining codebases: find documented cases where AI agents merged, combined or ported whole games or sizeable codebases (two games into one, a game to a new engine, several prototypes into one product). For each: what was actually combined, how conflicts and architecture differences were handled, how long it took, what the human did, and what the result was afterwards. Prefer repositories and detailed write-ups over announcements.

Part B, failures: find reports of agent-built games or applications that could not be extended, collapsed under their own code, or had to be rewritten; reports of agent projects where process, planning or testing overhead consumed most of the effort; and postmortems that name the cause. Include any measured data on how agent-written code ages (defect rates, rewrite rates, maintainability studies).

Output: a table per part with an evidence grade per row (A: repository or data, B: detailed write-up, C: anecdote), a one-page synthesis of what the combining cases and the failures have in common, and every source URL. Under 1,500 words plus the tables. Say where you found nothing.
