---
name: Lanchester and Combat Theory
description: What military operations research says decides an engagement — Lanchester's square and linear laws and how a frontage cap switches between them, concentration and defeat in detail, ambush models where one side cannot see (Deitchman and successors), Hughes's naval salvo model and scouting, and air-combat energy theory on what altitude is worth. Gathered for the layer lab's firing-share hypothesis.
type: topic_brief
captured_at: 2026-10-01
contributor: Research Lane, queue Q77; five gathering sub-agents, brief written by the main chat
---

# Lanchester and Combat Theory

## What this brief is

Requested by Westley on 2026-09-30 while the layer lab (`docs/northstar/research/layer_dynamics/README.md`) tests its firing-share hypothesis (§6.1): that an engagement is decided by how many units on each side can get shots off. This brief reports what five bodies of military theory say about that quantity. It makes no design recommendation. Feeds register flags `Q-008-02` and `Q-008-03`.

The full report, with every source link, is `docs/research/reports/Lanchester and combat theory.md`. The gathering notes are in `docs/research/research_notes/Lanchester and combat theory/` (five files). Confidence tags: VERIFIED (read in a primary or authoritative source), REPORTED (stated by a secondary source), ESTIMATED (arithmetic done in the notes, shown there), AMBIGUOUS (sources disagree).

## 1. The square law, the linear law, and what a choke does

Lanchester (1914, book 1916) derived the square law from aimed fire: each side's loss rate is proportional to the number of enemy units firing, so the difference of squares is conserved and fighting strength is unit quality times numbers squared. [VERIFIED, primary text] The law assumes every unit can engage any enemy and several can focus on one. [VERIFIED, Atkinson, Kress and MacKay 2020]

The linear law, where strength is quality times plain numbers, arises two ways: unaimed fire into an area, and one-on-one combat where geometry stops many attacking one. [VERIFIED, Washburn 2000; Mesterton-Gibbons 2016] Lanchester's own description of the second is "the number of men actually wielding their weapons at any given instant ... was, roughly speaking, the same on both sides." [VERIFIED]

The quality-for-numbers trade follows. Outnumbered 2 to 1, a side needs units 4 times as effective under the square law and 2 times under the linear law; at 3 to 1, 9 times and 3 times. [VERIFIED for 3 to 1; the table ESTIMATED]

A cap on how many units can engage is modelled as a switch between regimes, not as an exponent between 1 and 2. In Atkinson, Kress and MacKay's deployment-constrained model, units beyond the cap wait in reserve, neither firing nor exposed, and replace casualties: the fight is linear while both sides are above their caps, mixed when one falls below, and square when both are below. With a cap on one side only, that side's parity condition worsens by the factor mu(2 − mu), where mu is the fraction of its force that can engage; at half engaged the factor is 3/4. [VERIFIED] In Kress's narrow-passage case, where the defender concentrates on a single lead attacker, the attacker needs a force on the order of the square of the defender's. [VERIFIED] The notes' own integration shows the slide: 1,000 against 500 at equal quality leaves 866 survivors with no cap and 505 with an engaged width of 10, against a pure linear answer of 500. [ESTIMATED] No source derives a fractional exponent from a frontage width.

Fitted exponents exist but come from curve-fitting. StarCraft battles fit an attrition order of about 1.56, which the authors attribute to focus fire on damaged units, not to range. [VERIFIED, Stanescu, Barriga and Buro 2015]

## 2. Concentration, defeat in detail, and piecemeal arrival

Under the square law, forces that fight separately in time add as squares. A force of 1,000 that meets an equal enemy in two halves loses about 134 beating the first half and finishes with 707; fought undivided, the two annihilate each other. [VERIFIED, Lanchester 1916] A divided force needs about 40 percent more strength to draw. [VERIFIED] For an equal enemy arriving in k equal parts, the concentrated side keeps a fraction sqrt(1 − 1/k): 0.707 for two parts, 0.816 for three, 0.949 for ten. [ESTIMATED; no source states the general formula] In the limit of a trickle, arrivals add nothing, which Lanchester calls "the complete impotence of small forces in the presence of one of overwhelming power"; he states that this fails for small forces that are concealed or dug in. [VERIFIED] Under the linear law, splitting changes nothing. [VERIFIED, Stanescu et al. 2015]

Timing sets the size of the penalty: it is the attrition the early packet suffers while the later one is absent. In the notes' integration, 100 defenders against 120 attackers delivered as 60 and 60 lose if the second 60 arrive together with the first and win once the delay is long enough. [ESTIMATED]

Historical fit is poor. No basic Lanchester law fits two-sided daily battle data well (Ardennes, Kursk, Inchon-Seoul); phase, terrain and posture explain more. [VERIFIED, Lucas and Turkes 2004] The laws fit short, fully engaged fights better than multi-day battles. In real-time strategy, Lanchester-based predictors reach about 90 to 94 percent winner accuracy on StarCraft combats, and every one of them ignores unit positions; no published analysis treats chokes, surrounds, concaves or high ground in Lanchester terms. [VERIFIED as the papers' stated limits] About 71 percent of StarCraft replay combats in one dataset ended by reinforcement. [VERIFIED, Uriarte and Ontañón]

Dupuy's alternative is judgment multipliers: defensive posture 1.3 (hasty), 1.5 (prepared), 1.6 (fortified); surprise about 1.1 to 2.2 or 2.5 depending on the model version, decaying over three days. He did not validate the surprise values against his data. [REPORTED; versions AMBIGUOUS]

## 3. When one side cannot see: ambush models

Deitchman (1962) pairs a hidden side that aims (square law) with an exposed side that fires into an area (linear law). In the standard normalization the hidden side's advantage is bounded: the exposed side reaches parity by doubling its kill rate or raising its numbers by a factor of sqrt(2). [VERIFIED via Kress 2020 and Atkinson et al. 2020; Deitchman's own text not read] In raw-coefficient form the same model produces dramatic examples (10 hidden beating 100), so any quoted ratio needs its normalization. [AMBIGUOUS in presentation]

Successors make visibility a continuum. In the Kress and MacKay generalized model the exposed side has information mu from 0 (blind) to 1 (aimed). The extra kill rate it needs for parity falls from 100 percent at mu = 0 to about 65 percent at 0.1, 23 percent at 0.5, and 7 percent at 0.8. [VERIFIED for the model; values ESTIMATED, matching Kress's quoted figures] Their stated conclusion: a small increase in kill rate is worth more than an equal proportional increase in targeting information, unless information is poor. [VERIFIED] Imperfect targeting gives a square law with a penalty factor, not a linear law. [VERIFIED, Atkinson et al.]

Acquisition-time models give the mechanism: a unit's kill rate is kills per engagement cycle divided by cycle length, and time spent acquiring a target is part of the cycle. When targets are plentiful the rate saturates (square law); when acquisition is the bottleneck it scales with visible targets (linear law). [VERIFIED for the definition, Taylor and Neta 2001; reduction ESTIMATED]

Duel models treat first detection as a head start. With equal kill rates, an undetected head start worth one mean kill time raises the win chance from 0.50 to about 0.82. The advantage is a one-time window, unlike Deitchman's, which lasts as long as the hiding does. [ESTIMATED] No source integrates a hidden side being revealed over time into a Lanchester system.

## 4. Naval salvo theory

Naval officers stated the square law before Lanchester (Chase 1902, Fiske 1905), on the condition that "every engaged ship is able to fire at every engaged enemy ship." [VERIFIED via Hughes 1995] Crossing the T is the geometry that breaks that condition for one side: the crossing line's broadsides bear while the enemy replies with forward guns only. [REPORTED] Jutland-era doctrine aimed for a geometry "where all one's big guns bear while the enemy's do not." [VERIFIED, MacKay, Price and Wood 2016]

Hughes's salvo model (1995) for missile combat is discrete and linear in unit counts: a side's losses are (enemy missiles well aimed − missiles its own defences stop) / hits needed to disable a unit. Doubling every per-unit attribute is offset by doubling numbers, not quadrupling. [VERIFIED] When striking power is large relative to staying power the model is unstable: the stronger side can lose, and "even a superior force must ... attack decisively first." Where one unit can disable several per salvo, "all classical concepts of force concentration are suspect." [VERIFIED] Over many salvos, aimed fire recovers square-law behaviour and area fire approximately linear. [REPORTED, Armstrong 2013 abstract]

Scouting enters as multipliers between 0 and 1: scouting effectiveness on one's own striking power, alertness on the defender's counterfire. Hughes gives no numbers for them and calls the mathematics of degrading enemy scouting "weak and undeveloped." [VERIFIED] In *Fleet Tactics*, "attack effectively first" is the essence of tactical success, and better scouting, "more than maneuver, as much as weapons range," decides who does. [REPORTED; no edition read]

Validation is calibration to known outcomes. In 1942 one carrier air wing "rather consistently" put one enemy carrier out of action; a stochastic refit of Coral Sea gives a 0 to 2 ship loss interval for each side with identical forces. [VERIFIED] Attacking first there was worth more than an extra carrier. [REPORTED, Armstrong 2014 abstract] Missile hit probability falls from about 0.91 against defenceless ships to 0.68 against defended-but-not-alert and 0.26 against alert defenders. [VERIFIED, Schulte 1994; secondary sources print other values, AMBIGUOUS]

## 5. Air combat: what altitude is worth

Energy-maneuverability theory puts height and speed on one scale: specific energy = height + speed² / 2g. [VERIFIED for the definition, Shaw 1985; original Boyd report not read] In the ideal case 10,000 ft of height converts a 400-knot fighter to about 620 knots. [ESTIMATED] Regaining height costs more time than spending it; the notes' illustrative ratio of about 3.4 to 1 rests on an assumed climb rate. [ESTIMATED]

Sources value height as initiative, not as a number. Malan's rule: "Height gives You the initiative." [REPORTED] Shaw: a height edge pays for a diving attack only once it roughly equals the attacker's minimum turn radius; the lower fighter should "work below the bogey, make it come down to engage." [VERIFIED] Vertical splits within a formation trade defence for offence: the lower aircraft cannot climb to help in time, but an enemy is "less likely to see both aircraft simultaneously." [VERIFIED]

Detection is where height has numbers. Radar horizon grows with the square roots of both heights: about 426 nautical miles between two aircraft at 30,000 ft, about 25 between two at 100 ft. [REPORTED formula; values ESTIMATED] Uncued visual detection is about 2 nautical miles. [VERIFIED, CSBA 2015] The claim that 80 to 90 percent of victims never saw their attacker rests on one unnamed 1970s analysis of 112 Vietnam engagements and on pilots' estimates; a survey of aces reports about 20 percent. [AMBIGUOUS]

No source gives a closed-form value of height, a formal model with an altitude term, or a doctrine of five layers.

## What the five agree on, and where they differ

All five put the deciding quantity where the firing-share hypothesis does: units delivering effective fire at a given moment, not units present. They differ in how it enters. In Lanchester it is the number engaged and how fast each acquires targets. In the ambush models it is the acquisition term. In Hughes it is hits per salvo net of defence, with scouting multipliers that can zero the reply. In air combat it is first sight plus the energy to convert it. Only the first two give squared returns to numbers; the salvo model is linear by design.

Theory outruns test everywhere. The mathematics is consistent and often verified in primary sources; historical validation is weak, RTS work is position-blind, and surprise and altitude values rest on judgment or contested counts.

## Gaps

Not read: Deitchman's paper body, Osipov's 1915 text (sources disagree on whether he found a square law or a 3/2 power), any edition of *Fleet Tactics*, the Project Red Baron reports, Taylor 1983, Washburn and Kress 2009. Unresolved: Hughes's "42 ships" against a recomputed 25 in his own worked example; the Dupuy surprise-multiplier versions. Absent from the literature found: any model combining height, visibility and frontage; any Lanchester analysis of chokes or high ground in an RTS.
