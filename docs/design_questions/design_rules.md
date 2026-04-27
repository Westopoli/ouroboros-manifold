# Ouroboros Manifold — Design Rules

> **This document governs design brainstorming work.** The game bible says *what* to build. `dev_rules.md` says *how* to build it in code. This document says *how to decide what to build* when there are open questions — the brainstorming and decision process that runs in Claude.ai chats before implementation begins.
>
> **Every Claude chat doing design work on this game reads this file first.** It is the single source of truth for how design questions are surfaced, discussed, and resolved.

---

## When to Use This Document

Use this when:

- Starting a new stage spec and open design questions need resolving
- Revisiting a previous design decision that isn't working in practice
- Expanding an existing system (new mission archetypes, new eras, new mechanics)
- Any brainstorming session that will produce decisions written to the bible

Do NOT use this for:

- Implementation sessions (use `dev_rules.md`)
- Pure bug fixing (use `dev_rules.md`)
- Writing or reviewing code (use `dev_rules.md`)

---

## Starting a Design Chat — The Context-Setting Ritual

Every design chat begins with the same setup. Westley uploads (or the chat reads):

1. **`docs/bible/game_bible.md`** — the hub. Always.
2. **Relevant spoke files** — whichever `bible_*.md` spokes touch the system being discussed. The active design doc lists which ones are relevant.
3. **This file (`design_rules.md`)** — the rules of engagement.
4. **The active design doc** (`docs/design_questions/*.md`) — the working document for the current brainstorming effort. Contains open questions, resolved decisions, and the chat-to-chat handoff notes.

The chat's first action is to read these, then confirm to Westley what it understands the current state to be. No design work begins until this confirmation.

---

## How Design Questions Are Presented

Claude presents one design question at a time, not batches. Each question has this shape:

### Question Template

```
### Question N — [Short Descriptive Title]

**Context:**

[Plain-language explanation of the system this touches. Don't assume Westley
remembers exact bible sections — re-explain the relevant concept. Name the
bible file if useful, but explain what it says rather than sending him to
re-read it.]

[Why this question matters. What depends on the answer. What's downstream.]

**Options:**

**A — [Short name for the option]**
[One or two sentences describing what this option means concretely.]
- *Pros:* [...]
- *Cons:* [...]

**B — [Short name]**
[Description.]
- *Pros:* [...]
- *Cons:* [...]

[2–4 options total. More than 4 is usually a sign the question needs splitting.]

**Recommendation (optional):**
[If Claude has a strong recommendation, state it with reasoning. Westley
may accept, override, or riff off in a new direction.]
```

### Rules for Question Presentation

1. **One question at a time.** Westley answers, then Claude presents the next. No batches. Westley may want to riff on a question, and riffing is impossible if three more questions are stacked behind it.

2. **Context before options.** Don't assume Westley remembers the bible's exact specification of every system. Re-explain what the system is and why the question matters. A good rule of thumb: if Westley has to re-read a bible section to understand the question, the context section is too thin.

3. **2–4 options, labeled A–D.** One option is usually a cop-out. Five options means the question is too broad and should be split.

4. **Pros and cons, not preferences.** State the actual tradeoffs. Don't bury a recommendation inside the cons.

5. **Mark a recommendation if you have one.** Don't pretend to be neutral when you're not — Westley will see through it. But state the recommendation separately after the options, not inside them.

6. **Stop and wait.** After presenting, Claude stops. Does not write the spec, does not start on the next question, does not speculate about the answer. Waits for Westley.

7. **Keep it succinct.** Context should re-explain the concept, not lecture. Pros and cons should be one or two sentences each, not paragraphs. Recommendations should state the reasoning in a sentence or two. If an option description runs past three sentences, it's too long. Only include information that helps Westley make the decision — no filler, no restating things he already knows, no padding.

### What Westley Might Do

- **Pick an option** — "A" or "Option B" or similar. Write the answer to the design doc.
- **Riff off in a new direction** — "None of those. What about X?" Treat the riff as a new anchor and present fresh options around it.
- **Ask for more context** — "I don't understand what a layout is." Provide more context on the concept, not more options. Re-present the question once the concept is clear.
- **Defer** — "Let's come back to this one." Mark the question as deferred in the design doc and move on.
- **Question the question** — "Why are we deciding this now?" Sometimes a question shouldn't be answered at this stage. Re-evaluate scope.

---

## Decision Types

Not every implementation detail is a design decision. Classify each question:

### Design Decision (needs Westley)

The answer shapes how the game *feels* or *behaves* in ways the player would notice. Examples: "do reinforcement structures spawn pre-captured or neutral?" "how long does an engagement last?" "should the player see enemy intentions or only their positions?"

These MUST be surfaced as questions. Claude does not make design decisions.

### Engineering Decision (Claude can default)

The answer shapes how the code is *structured* but the player wouldn't notice the difference. Examples: "what file does the navmesh generator live in?" "JSON or msgpack for the WebSocket protocol?" "what's the spatial hash cell size?"

These get written into the stage spec as defaults with reasoning. Westley reviews them as part of the spec, not as standalone questions. If unsure whether something is a design or engineering decision, flag it. Borderline cases go to Westley.

### Tuning Value (deferred to implementation)

The answer is a number that will be adjusted through playtesting. Examples: "what's the capture zone radius?" "what's the structure HP?" "what's the threshold for composition reactivity?"

Write these as config values with proposed defaults and a note that they're tuning-stage decisions. Don't ask Westley to pick a number that will change anyway.

---

## The Answer Capture Workflow

Once a question is answered, the answer must be captured permanently. There are three possible destinations:

### 1. The Bible (for design decisions that change the game's design)

If the answer resolves something about how the game works at the design level — a mechanic's behavior, a system's scope, a design principle — the answer gets written into the appropriate bible spoke file. The hub's "Open Design Questions" section is updated or the question is removed if it was tracked there.

**Bible edits follow the bible's append-only rule.** Claude writes the resolution into the appropriate section of the spoke. Claude does not delete or overwrite existing decided content.

### 2. The Stage Spec (for implementation-level decisions)

If the answer is about how the stage implementation should work — file organization, interface shape, algorithm choice — it goes into the stage spec, not the bible. The bible stays conceptual.

### 3. The Active Design Doc (interim, until captured)

Before an answer lands in the bible or a spec, it lives in the active design doc. This is the working memory of the brainstorming effort. Once the stage spec is written, the design doc's resolved questions have been consumed and the doc can be archived.

**All three destinations get updated in the same session** unless Westley explicitly says otherwise. Don't let answers live only in a chat — chats are ephemeral.

---

## File Hierarchy

```
docs/
├── bible/
│   ├── game_bible.md                       ← Hub (the "what")
│   └── bible_*.md                          ← Spokes (full references)
├── dev_rules.md                            ← Implementation process
├── design_rules.md                         ← THIS FILE. Design process.
├── stage_specs/
│   └── stage_N_spec.md                     ← One per stage (the "how")
└── design_questions/                       ← Active brainstorming docs
    └── [topic]_design.md                   ← Transient, one per active effort
```

- **Bible + dev_rules + current stage spec** remain the three docs that govern the project at any time (per `dev_rules.md`).
- **`design_rules.md`** is a permanent process doc, sibling to `dev_rules.md`. It only comes into play during brainstorming, so it doesn't violate the "three governing docs" rule during implementation.
- **`design_questions/*.md`** are transient working documents. Similar to `continuation_context.md` — they bridge multiple chats during an extended brainstorming effort, then get deleted once their contents are merged into the bible and/or a stage spec.

---

## Design Question Lifecycle

Each question moves through these states. The active design doc tracks which state each question is in.

1. **[OPEN]** — Identified as something that needs a decision, not yet presented to Westley.
2. **[PRESENTED]** — Options have been laid out. Awaiting Westley's answer.
3. **[ANSWERED]** — Westley has chosen or riffed. Answer recorded in the design doc.
4. **[CAPTURED]** — Answer has been written into the bible and/or stage spec. Safe to remove from the design doc.

Claude should never skip the [ANSWERED] → [CAPTURED] transition. An answer that only lives in the design doc isn't final — the bible and spec must reflect it.

---

## Ending a Design Chat

Before ending a session (whether the brainstorming is complete or will continue in another chat), the chat must:

1. **Ensure all [ANSWERED] questions are [CAPTURED].** Write the decisions into the bible/spec.
2. **Update the active design doc** with the current state of every question (OPEN, PRESENTED, ANSWERED, or CAPTURED).
3. **Write a handoff note** at the top of the design doc summarizing: what was accomplished this session, what's open, what the next chat should tackle first.
4. **Confirm to Westley what's been changed.** List the files modified and the net state.

If brainstorming is complete (all questions resolved and captured), the design doc can be deleted — all decisions now live in the bible and/or stage spec. Otherwise, the design doc persists for the next chat.

---

## Anti-Patterns — What Not to Do

These are the failure modes this process exists to prevent. If a chat is doing any of these, stop and reset.

1. **Making design decisions without surfacing them to Westley.** If the bible doesn't answer it and it affects how the game feels, it's a question, not a default.

2. **Batching multiple questions before Westley has answered any.** One at a time. Always.

3. **Assuming Westley remembers the bible verbatim.** Re-explain concepts. The context section of every question is mandatory.

4. **Letting decisions live only in chat.** If a decision isn't written to a permanent file, it's lost. Every answer must be captured before the chat ends.

5. **Sliding into implementation.** Design chats produce decisions written to docs. They do not produce code. If a question can't be answered without writing code to test it, flag it as an implementation question and defer.

6. **Burying recommendations inside options.** State recommendations separately so Westley can see Claude's opinion without it contaminating the neutral option presentation.

7. **Re-opening captured decisions silently.** If a previous decision turns out to be wrong, say so explicitly. Don't quietly change the answer in the bible — the bible is append-only unless Westley approves a change.

---

## Summary — The One-Page Version

1. **Design rules govern brainstorming. Dev rules govern implementation. Bible governs the game.**
2. **One question at a time. Context, options, pros/cons, recommendation, stop.**
3. **Re-explain concepts. Don't expect Westley to re-read the bible.**
4. **Three decision types: design (Westley), engineering (Claude defaults), tuning (deferred).**
5. **Every answer must be captured — bible, spec, or both — before the chat ends.**
6. **Design docs are transient. They exist to bridge chats, then get deleted.**
7. **No implementation work in design chats.**
