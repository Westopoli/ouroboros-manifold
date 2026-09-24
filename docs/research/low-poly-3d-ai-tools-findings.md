# AI 3D Model Generators for Low-Poly Game Assets — Findings Summary

Goal: replace Sloyd (unlimited volume, but 5K+ poly floor, weak prompt adherence) with a tool that can hit sub-1,000 triangles at high volume, for an Art of Rally / Age of Empires Online-style low-poly game.

## Myth-busting

- **"GPT Astra" (GPT-6 Astra, OpenAI, released Sept 2026)** is not a 3D asset generator. It's a general agentic model that writes Blender/CAD scripts and drives software UIs. Mixed accuracy, very high token cost per asset, no bulk-export workflow. Available via ChatGPT Plus ($20/mo), Pro (~$100/mo), or API. **Not viable for high-volume asset production.**
- **"Claude Design"** isn't a game-asset tool either. It's either Claude scripting Blender/CadQuery (CAD-precision parts, not stylized game art) or Anthropic's web-design/mockup artifact type (outputs HTML/CSS/JS, not downloadable meshes). Either way: excluded.
- **Gemini's research** (contrasted separately) agreed on both exclusions, and added a specific Blender-side technique that's worth keeping regardless of which generator you pick.

## Review volume & ratings (real numbers, checked directly)

| Tool | Rating | Review count | Note |
|---|---|---|---|
| Meshy | 4.7/5 (G2 & Trustpilot) | 3,735 (G2) / 3,582 (Trustpilot) | Largest, most consistent sample by far |
| Tripo3D | 4.6/5 (Trustpilot) | 615 | Solid, consistently positive |
| 3D AI Studio | 4.7/5 (Trustpilot) | 187 | Small but clean; aggregates other engines |
| Sloyd (baseline) | 3.7/5 (Trustpilot) | 18 | Small, polarized |
| Hyper3D Rodin | 2.9/5 (Trustpilot) | 60 | Polarized — mostly billing complaints, not model quality |
| CSM.ai | Unverifiable | ~0 real reviews | Any rating you see cited elsewhere is not trustworthy |
| Kaedim | 4.0/5 | 5 | Sample too small to mean anything; documented reliability complaints |

## Low-poly capability

- **Sloyd**: hard-capped by its procedural template library; floor is ~5K, team says they're pushing toward ~3K. Structurally can't do freeform sub-1K without breaking the model.
- **Meshy**: has a documented "Smart Topology" mode that generates directly at a target budget (not decimated after the fact), with custom targets **down to 100 faces**. Meshy's own docs admit "noticeable" to "severe" detail loss below ~5K — expect iteration, not one-shot results.
- **Tripo3D**: has an equivalent "Smart Mesh" / low-poly feature, independently praised for clean quad topology, but no publicly documented hard face-count floor (unlike Meshy's explicit 100-face number).
- **Disputed point (unresolved)**: A Reddit quote cited by a competing research pass claims "Meshy has horrendous low-poly topology masked by good textures/normals," implying Tripo is cleaner under the hood. I could not verify this quote directly (Reddit blocks my fetch tool). This is the single most decision-relevant open question — **test both yourself on 3–4 real assets, inspect wireframes, not shaded renders.**

## Pricing / economics at volume

| Tool | Entry paid tier | Included | Effective cost/model at scale |
|---|---|---|---|
| Sloyd | $15/mo | Unlimited | ~$0.015/model (wrong poly range though) |
| Meshy | ~$20/mo (Pro) | ~1,000 credits | ~$0.40–0.60/model depending on texture add-on |
| Tripo3D | $19.90/mo (Pro) | 3,000 credits (~120 models) | ~$0.20–0.24/model; Max tier $89.90/mo ≈ 1,000 models/mo |
| Rodin | $30/mo (Creator) | ~60 models/mo | Business $120/mo ≈ 416 models/mo |
| CSM | $15–49/mo | Thin public data | Not enough evidence to trust |

Sloyd's "33x cheaper" framing (from Sloyd's own blog) is accurate on raw cost but irrelevant since it can't hit your poly target at all.

## Free-tier testing (no subscription needed for a first look)

- **Tripo3D**: free plan (~200–300 credits/mo) lets you generate and download a test asset (CC BY 4.0). Smart Mesh/low-poly access may be limited to a 24-hour trial window after signup — fine for one test.
- **Meshy**: free plan (100 credits/mo) lets you *generate*, but downloads are capped at 10/month and only work for the lighter **"Meshy 6 Lite"** engine — the full Meshy 6/7 engine (the one under debate for quality) hits a paywall at download. Confirm which engine you're generating with before relying on a free test.

## Bottom line / recommendation

1. Exclude GPT-6 Astra, "Claude Design," CSM, and Kaedim from serious consideration for this pipeline.
2. Treat Sloyd as background/generic-prop filler only — not viable for the sub-1K, on-brand assets.
3. Head-to-head test Meshy vs. Tripo3D yourself on real assets (car, tree, small building) at a ~500–800 face target, on the **full-quality engine tier**, and judge by wireframe — this is where the two research passes disagreed and neither could be independently verified.
4. Regardless of winner, plan on a downstream automated pass (e.g., headless Blender script: Decimate/Collapse + triangulate + flat-shade + strip unused texture maps + LOD export) to guarantee every asset lands under budget rather than relying on one-shot AI generation.
