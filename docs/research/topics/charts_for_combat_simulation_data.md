---
name: Charts for Combat Simulation Data
description: How game-balance research, combat-simulation studies and the visualization literature present "who beats whom, by how much, and under which settings", and what is known about charts a non-specialist can read at a glance. Gathered after the first layer lab sample charts proved hard to read.
type: topic_brief
captured_at: 2026-10-01
contributor: Research Lane, queue Q79; three gathering sub-agents, brief written by the main chat from their notes (no separate synthesized report)
---

# Charts for Combat Simulation Data

## What this brief is

Westley, 2026-10-01, on the first sample charts from the layer lab: "it doesn't read well, I had to stare at it to figure out what it meant, research similar data sets and find out how they visualize it, research/scientific papers might be a good source." This brief reports what the sources show. It makes no design recommendation. Notes, with every source link: `docs/research/research_notes/Charts for combat simulation data/` (three files). Tags: VERIFIED (read in the source), REPORTED (secondary), ESTIMATED (inferred, for example from a caption), AMBIGUOUS. The gatherers could not see images; figure descriptions come from captions and surrounding text.

## 1. What makes a chart readable at a glance

- **Counts beat ratios.** Stating a problem in natural frequencies ("10 out of 1,000") instead of probabilities raised correct answers from 16 to 28 percent up to 46 to 50 percent. [VERIFIED, Gigerenzer and Hoffrage 1995; replicated in managers, Hoffrage 2015]
- **Position on a common scale is read most accurately**, ahead of length; angle and area are worse. [VERIFIED via Heer and Bostock 2010, replicating Cleveland and McGill 1984]
- **A title that states the finding helps.** Descriptions of charts were better with titles than without (1.90 against 1.30), though the study was observational. A finding as headline, the relevant data highlighted, and a note on the chart improved recall of the pattern. A title's slant changes what readers take away. [VERIFIED, Borkin 2016; Ajani 2022; Kong 2018]
- **Direct labels, plain words, no dual axes** are expert guidance (UK Analysis Function, Datawrapper, Few), not experiment. [VERIFIED as guidance]
- **Scatter plots and log scales lose readers.** 63 percent of US adults read a scatter plot correctly, about half of those with high school or less. About a third of adults have low graph literacy. Log scales reduced understanding. [VERIFIED, Pew 2015; Galesic 2011; Romano 2020]
- **Small multiples are read more accurately than animation**; animation is quick for presentation and error-prone for analysis. [VERIFIED, Robertson 2008]
- **Icon arrays have mixed evidence.** [VERIFIED, Galesic 2009 positive; Ruiz 2013 negative]
- No lay-reader evidence was found for tornado, contour, feasible-region, ratio-axis or signed-share-axis charts.

## 2. How combat-simulation studies present results

- **Strength against time, one curve per side**, is the standard Lanchester picture. [VERIFIED, Washburn's notes]
- **The phase plane:** one side's strength on each axis, each battle a path, and a straight line (the separatrix) dividing the starts from which each side wins. [VERIFIED by caption, Kress et al.]
- **A map of who wins by two inputs.** Mesterton-Gibbons plots numbers ratio against fighting-ability ratio and shades the regions where each side wins. Sanchez and Lucas plot initial Red size against initial Blue size for a deterministic model and colour by winner; the winner flips back and forth along some lines, non-monotone in 5 of 9 slices, which they trace to chaotic battle paths. [VERIFIED]
- **A decision tree with green, yellow and red leaves** is what the Naval Postgraduate School data-farming group calls "useful for succinctly presenting results to decision-makers"; the briefing version strips the statistics. [VERIFIED, Cioppa, Lucas and Sanchez 2004]
- **Also used by that group:** grids of small interaction plots; contour plots of two factors with a plain-English reading; trellis plots conditioned on a third factor; a table of factors marked significant or not. Their advice: gridded designs are the easiest to explain to non-statisticians, and single runs or sparse samples mislead. [VERIFIED]
- **Force-ratio tables** with a verbal result per band (Dupuy Institute). [REPORTED]

## 3. How game-balance work presents results

- **A table with an "Interpretation" column** beside each row of numbers. [VERIFIED, Jaffe et al. 2012]
- **The same number can mislead in one form and inform in another.** A bar chart of average kills per character would have led designers to weaken the wrong character; the same quantity drawn against player skill fixed it. [VERIFIED, Jaffe dissertation 2013]
- **A band of acceptable balance (45 to 55 percent) drawn on a plane, repeated for three values of one design parameter**, is the closest form found to "how balance moves as a knob moves". [VERIFIED, Jaffe 2013]
- **Matchup grids:** rows against columns, each cell a win rate, coloured on a diverging scale with a neutral middle, rows sorted by strength. Used for skill against skill (Sorochan et al.), for agents (AlphaStar's payoff matrix), and for characters or units (fighting-game and auto-battler community charts, the latter using letter grades for how much health the winner keeps). [VERIFIED and REPORTED]
- The StarCraft combat-prediction papers show accuracy curves and tables only; no break-even or army-size plots were found, and no tool that shows a designer a balance landscape with sliders.

## Gaps

No study tests whether game designers understand any of these forms. Search limits cut all three threads short: the Hughes and Armstrong salvo presentations, GDC balance talks from the large studios, and several standard visualization books were not reached. Several entries on chart types rest on encyclopedia summaries and are tagged REPORTED in the notes.
