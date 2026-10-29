# Probe G — Rules-file comprehension (director mode)

**Proves.** A distilled per-feature rules file is enough for DeepSeek to write a mission whose directives cover every "ways this could be wrong" item, and for the local executor to perform them with evidence.

**Fixture.** `agora/projects/proving-ground/rules/toy-scene.md` (5 rules, 5 ways-this-could-be-wrong) and `qa.toml` (desktop profile draft) in `~/Projects/agora-proving-ground`. Target is the probe D scene.

**Pass criterion.** Mission covers all 5 items with concrete directives; executor performs each; verdict backed by screenshot plus port state; on the buggy build two findings, on clean none.

**Blocked today.** Agora director mode is `status: pending` (campaign 002, `specs/cascade-director.md`); no `qa_director.py`; no desktop tool type. Runs after those land.
