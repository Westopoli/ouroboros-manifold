# Probe J — e2e drafting from an epic

**Proves.** `agy` can draft an e2e file from an epic file and the e2e template alone, without inventing a value for an input the epic leaves implicit.

**Fixture.** Toy epic, 8 rules, one deliberately implicit input (a rule that depends on a value the epic never states a range or source for). Target is a toy e2e template matching `docs/northstar/e2e/E-##.md`'s section list.

**Pass criterion.** The draft has every template section non-empty, cites every one of the 8 rule ids, and lists the implicit input as a question (a candidate `Q-###-##` row) rather than inventing a value for it. Negative control: a complete toy epic with no implicit input yields zero questions.

**Blocked today.** No `draft_e2e.md` prompt or schema exists yet (`docs/northstar/spec_factory.md` notes these are written once a real epic reaches this step; E-03, the first epic run through the factory, got blocked earlier in the pipeline — folding answers — and never reached draft-e2e). Runs after the prompt and schema land.
