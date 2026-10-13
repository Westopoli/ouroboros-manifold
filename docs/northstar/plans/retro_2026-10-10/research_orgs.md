# Research: how large parallel orgs build big products (2026-10-10)

Evidence grade: P = primary page read; S = secondary or search-snippet only. Numbers are as the source states them.

## 1. Game studios

- Milestone ladder: prototype, first playable, vertical slice, alpha (feature-complete, start-to-finish playable), beta (content-complete, stabilise), gold. Terms vary by studio. Vertical slice = "some subset of the final game exists, is fully reflective of the final product, and can be played as such". [S] https://learn.unity.com/course/game-development-in-a-nutshell/tutorial/production-and-post-release
- Double Fine used "first playable" for an area built to test pipelines across departments, and avoided "vertical slice" as implying too much polish. That is a walking skeleton under another name. [S] https://gematsu.com/2017/10/psychonauts-2-first-playable-milestone-gameplay
- Slice risk: months spent polishing a slice eat main production ("demo hell"); worked example is an 18-month game with 5 months pre-dev; agree quality/time/budget per milestone up front. [P] https://gamedeveloper.com/production/do-you-have-a-firm-definition-of-your-milestones-
- A shut-down indie's postmortem says the polished slice "lied": it hid how much content and systems work remained. [S, single anecdote] https://mipmap.substack.com/p/red-wastes-starting-development
- Riot, Legends of Runeterra (the one concrete studio integration model found, P): Git LFS monorepo, ~100 GB, ~1,000,000 files, ~700 branches; ~100 full pipeline runs/day, ~60 min average. Developers branch off shared team branches; a daily job auto-merges each parent into its children; team branches merge to main regularly. They stopped branching directly from main because it broke the main build too often. A "Merge Readiness" build (static analysis, asset validation, unit, perf and functional tests) is required before merge. A shared Production Engineering team (PE:STAB) owns cross-team tooling. Takeaway: game studios are not pure trunk; they use team-level integration tiers. https://www.riotgames.com/en/news/legends-runeterra-cicd-pipeline
- Riot uses Perforce for the League client/server (large binary assets, fine-grained access) and Git for services. [S] https://www.riotgames.com/en/news/using-perforce-complex-jenkins-pipeline
- Epic: Perforce plus Robomerge, which auto-merges between branches per changelist, plus Horde CI. [S, vendor page] https://www.perforce.com/node/3335
- Ubisoft: lead-studio model (Montreal led Brotherhood with Bucharest, Singapore, Quebec, Annecy supporting; Black Flag used 7 studios; lead keeps creative control), moving to cross-studio co-development for Infinity. No build-integration detail published in what I found. [S] https://www.gamedeveloper.com/game-platforms/-i-assassin-s-creed-i-becomes-a-cross-studio-project-starting-with-i-assassin-s-creed-infinity-i-
- Valve (2012 handbook): no managers, employees green-light projects, desks on wheels. Self-organising; critics doubted it scales. [S] https://bit-tech.net/news/gaming/valve-employee-handbook/1/
- Discipline vs feature teams: many studios are discipline-organised, so production must coordinate each feature across departments; cross-functional Scrum teams of 5 to 9 reduce delay. Blog-level evidence only. [S] https://gamedeveloper.com/production/why-cross-functional-
- Daily build: McConnell 1996 describes compile, link and smoke-test every day as common at Microsoft; a broken build becomes top priority; the smoke test grows over time. Microsoft 1989-95 used a designated "buildmeister". [S] https://www.oreilly.com/library/view/rapid-development-taming/9780735634725/ch18.html and https://trunkbaseddevelopment.com/game-changers/
- Gap: I found no primary source on Blizzard, id or Valve integration cadence. Do not infer from this section about them.

## 2. Big tech

- Google: ~50,000 engineers in one repo, 60,000-70,000 commits per workday, >80 TB, ~1,000 teams, fewer than 10 keep a long-lived dev branch. Dev branches for stability called "inherently misguided". "One Version" rule: developers never choose a dependency version. [P] https://abseil.io/resources/swe-book/html/ch16.html
- Facebook: pushes from master; >1,000 diffs/day to master; weekly pushes of up to 10,000 diffs; 100% of web servers on push-from-master in April 2017. [S] https://engineering.fb.com/2017/08/31/web/rapid-release-at-massive-scale/
- DORA trunk-based development: branches live "no more than a few hours"; three or fewer active branches; merge at least daily; no code freeze or integration phase; build and test in "a few minutes". Correlational; no effect sizes on the page. [P] https://dora.dev/capabilities/trunk-based-development/
- DORA small batches: hours to a couple of days; "any batch over a week is too big"; integrate at least daily; amplifies AI's positive effect. No effect sizes. [P] https://dora.dev/capabilities/working-in-small-batches/
- DORA 2025: AI is an amplifier; ~5,000 respondents; 90% adoption; one analysis says only 2 of 7 team clusters gain throughput without more instability. [S] https://blog.robbowley.net/2025/10/01/dora-2025-ai-assisted-dev-report-some-benefit-most-dont/
- Fowler on CI: commit to mainline at least daily; "twice as much code to integrate... four times as long"; ten-minute build; "nobody has a higher priority task than fixing the build", usually by reverting; long branches are only "semi-integration". [P] https://martinfowler.com/articles/continuousIntegration.html
- HP LaserJet firmware: 400+ engineers, 10M+ lines, 10+ long-lived branches, 1-week builds; after moving to trunk, 1-hour builds and 10-15 builds/day. [S] https://trunkbaseddevelopment.com/game-changers/
- Amazon: API-only service interfaces (~2002, from Yegge's recollection) and two-pizza teams; both second-hand. [S] https://blog.axway.com/amplify-products/api-management/jeff-bezos-api-mandate
- Conway evidence: on Windows Vista, organisational-structure metrics predicted failure-proneness better than churn, complexity, coverage, dependencies and pre-release bugs (Nagappan, Murphy, Basili, ICSE 2008). [S] https://www.microsoft.com/en-us/research/?p=153188
- Team Topologies: four team types (stream-aligned, enabling, complicated-subsystem, platform); three interaction modes (collaboration, X-as-a-Service, facilitation); overloaded teams behave like overloaded CPUs; "thinnest viable platform". [P] https://teamtopologies.com/key-concepts
- Brooks: coordination paths n(n-1)/2, so 5 to 10 people almost quadruples paths; splitting gains O(N) but coordination and merging cost O(N^2). [S] https://www.projectwizards.net/en/project-management-glossary/brooks-law and https://www.catb.org/jargon/html/B/Brookss-Law.html

## 3. Flow and batch size

- Little's law: WIP = throughput x lead time. At fixed throughput, more WIP only lengthens cycle time. [S] https://thinkinsights.net/leadership/littles-law
- Theory of Constraints: identify, exploit, subordinate, elevate, repeat. Non-constraints should not outrun the constraint; surplus piles up in front of it. [S] https://www.tocinstitute.org/five-focusing-steps.html
- Reinertsen: queue size multiplies delay cost (20 queued jobs, a 5-minute delay costs 100 minutes; with 2 jobs, 10). Small batches speed feedback and shrink queues. Batch size is an economic trade-off (U-shaped cost; attack the fixed per-batch overhead). Product development is biased toward large batches. [S] https://ardalis.com/principles-of-product-development-flow-book-review/ and https://accelconf.web.cern.ch/IPAC2011/papers/weib02.pdf
- Reinertsen on utilisation: processes typically run above 95% to 98%, which drives queue time (secondhand figure; the "80%" rule of thumb is not in what I found). [S] https://www.softhouse.se/en/getting-flow-into-your-product-development/
- Integration cost is superlinear in divergence (Fowler, section 2) and the reason for merge frequency: "integration hell, where every time they fix an integration bug, two more pop up".
- Walking skeleton (Cockburn): a tiny end-to-end implementation linking the main architectural components; architecture and functionality then evolve in parallel; kept, not thrown away. [S] https://henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html
- Tracer bullets (Hunt and Thomas): lean but production-quality end-to-end code that stays in the system; prototypes are discarded. Early end-to-end feedback surfaces integration problems while the code is small. [S] https://www.artima.com/intv/tracer.html

## 4. Multi-agent AI coding (2025-2026)

- Anthropic research system: agents use ~4x chat tokens, multi-agent ~15x. Opus lead plus Sonnet subagents beat single Opus by 90.2% on the internal eval. Token use alone explained 80% of variance on BrowseComp. Poor fit: "domains that require all agents to share the same context"; coding has fewer parallelisable subtasks. Vague delegation causes duplicated work and gaps; "errors compound"; the lead cannot steer subagents mid-run. [P] https://www.anthropic.com/engineering/multi-agent-research-system
- Anthropic, building effective agents: orchestrator-workers fits tasks "where you can't predict the subtasks" (example: multi-file coding changes); "find the simplest solution possible", add complexity only when it demonstrably improves outcomes. [P] https://www.anthropic.com/engineering/building-effective-agents
- Claude Code best practices: context "fills up fast, and performance degrades as it fills"; give the agent a pass/fail check; a fresh-context reviewer avoids author bias; specs should be self-contained, naming files and interfaces; after two failed corrections, clear and restart; `/batch` splits work across 5 to 30 subagents, each in its own worktree. [P] https://code.claude.com/docs/en/best-practices
- Subagent guidance: use for 10+ files or 3+ independent pieces; avoid for sequential or small tasks; "two subagents editing the same file in parallel is a recipe for conflict". [P] https://claude.com/blog/how-and-when-to-use-subagents-in-claude-code
- Agent-teams docs: start with 3 to 5 teammates; 5 to 6 tasks each; give each teammate a distinct file set; sequential, same-file or dependency-heavy work belongs in one session; tokens scale linearly with teammates; task claiming uses file locking. [P] https://code.claude.com/docs/en/agent-teams
- Carlini C compiler: 16 parallel agents, ~2,000 sessions, two weeks, ~2B input and 140M output tokens, just under $20,000 (about $10 per session, my arithmetic), ~100,000-line Rust compiler that builds Linux 6.9. Git-file task locks; "merge conflicts are frequent" but resolved by the agents. The verifier must be near-perfect or agents solve the wrong problem; new features often broke old ones, so CI was tightened. On the kernel, 16 agents "were stuck solving the same task" until GCC served as an oracle to split the work. A dedicated agent merged duplicate code. [P] https://www.anthropic.com/engineering/building-c-compiler
- Cursor scaling agents: lock-based coordination made "twenty agents... slow down to the effective throughput of two or three"; a dedicated integrator role "created more bottlenecks than it solved"; planner/worker/judge with a fresh start each iteration; "periodic fresh starts" fight drift; non-overlapping chunks are the key to width. Browser project ~1M lines, 1,000+ files; "trillions of tokens", no dollar figure. [P] https://cursor.com/blog/scaling-agents
- Worktree failure mode: clean git merges can hide semantic breakage (a rename in one worktree broke a call site in another). [S, vendor anecdote] https://www.indiehackers.com/product/conflict-check
- Productivity: METR trial, 16 experienced developers, 246 tasks, 19% slower with AI (they felt ~20% faster). Faros telemetry, 10,000+ developers: PRs merged +98%, PR size +154%, review time +91%, company-level DORA metrics flat. [S] https://www.faros.ai/blog/lab-vs-reality-ai-productivity-study-findings
- Cost per feature: no credible per-feature figure found. Only Carlini's totals above and a blog estimate that teams cost 3x to 4x a single agent. [S] https://fast.io/resources/claude-code-agent-teams-setup/

## Principles that transfer to a one-person-plus-agents studio

1. Integrate small and often: hours-sized batches, merged at least daily; integration cost grows faster than divergence (sections 2, 3).
2. Keep the integration gate fast (about 10 minutes) and treat a red mainline as top priority, reverting first (sections 1, 2).
3. A single serialised gate is fine only while it is not the constraint; measure the queue in front of it and cap WIP at its capacity (sections 3, 4).
4. Freeze interfaces between owners, but derive them from a running thin end-to-end slice; contracts-first is Amazon-style and Conway-aligned, but unproven contracts are the risk (sections 2, 3).
5. Build the skeleton or first playable before fanning out, and time-box the vertical slice to avoid demo hell (sections 1, 3).
6. Parallelise only independent work with disjoint file ownership; when every agent hits the same problem, find an oracle or decompose instead of adding agents (section 4).
7. Write the verifier first and make it near-perfect: agents solve exactly the test they are given (section 4).
8. Keep agent contexts small and short-lived, with self-contained briefs (objective, output format, boundaries) and periodic fresh starts against drift (section 4).
9. Add a coordination role only after a measured failure, and delete roles that become bottlenecks (sections 3, 4).
10. The human is the scarcest, least-parallel resource: size work to review bandwidth, ask for evidence rather than assertions, and cut cognitive load (sections 2, 4).

## Where the 3-day programme most likely diverged (hypotheses from the brief; I have not seen the programme's data)

1. One lock plus per-lane landing clerks puts two queues ahead of the single constraint; Cursor saw locks collapse 20 agents to 2-3 effective, and Reinertsen/ToC predict queue delay there (sections 3, 4).
2. Clerks, gate agents, drift auditors and test authors are many coordination roles; Cursor removed its integrator and Anthropic advises the simplest design that works (section 4).
3. Freezing headers before any end-to-end run inverts the skeleton/tracer sequence; contracts evolve with a running slice, and a slice that "lied" is the known failure (sections 1, 3).
4. 3 days and ~120 pieces is far shorter than the published runs (2 weeks, ~2,000 sessions); regressions from new features breaking old ones and drift appear later, and no cost-per-piece baseline exists to compare (section 4).
5. Lanes split by file ownership are component teams, not stream-aligned slices; Team Topologies and Conway predict hand-off cost at lane boundaries, and the single human reviewer is the likely true constraint (sections 2, 4).
