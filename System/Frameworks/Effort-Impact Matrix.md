---
date: {{TODAY}}
type: framework
tags: [framework, prioritization]
ai-first: true
layer: company
confidence: high
---

# Effort-Impact Matrix

## For future agent
This note explains the effort-impact (impact-effort) prioritization matrix and the RICE score, the scales Company Brain uses (1-5, with 3 counting as high), how to read each quadrant, and how the matrix is generated from solution and project notes.

## What it is
A 2x2 that places each candidate piece of work by expected impact and required effort, so a team can see at a glance what to do first. It is a widely used product and operations heuristic (also called an action priority matrix); there is no single author.

```
 High impact │  QUICK WINS          │  BIG BETS
             │  do first            │  plan deliberately, slice
             ├──────────────────────┼──────────────────────
 Low impact  │  FILL-INS            │  MONEY PITS
             │  when there is slack │  avoid or rethink
             └──────────────────────┴──────────────────────
                 Low effort              High effort
```

## Scales in Company Brain
- **Impact 1-5**: expected effect on the outcome or key result the item serves. 1 barely noticeable, 3 a clear contribution, 5 moves the KR substantially on its own.
- **Effort 1-5**: relative cost: people, calendar time, dependencies, risk. Calibrate against an item the team has already shipped.
- A score of 3 counts as **high** on both axes (conservative: we assume work is bigger than it looks).

## RICE (optional, for finer ranking)
RICE was published by Intercom (Sean McBride, https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/): score = Reach x Impact x Confidence / Effort.
- Reach: people or events affected per period (for example per quarter).
- Impact: here the same 1-5 scale.
- Confidence: high 100 percent, medium 80 percent, low 50 percent.
- Effort: here the same 1-5 scale (Intercom uses person-months; keep one convention per brain).

## How to use it
1. Score only items tied to an outcome or KR; unanchored work has no impact to estimate.
2. Write the rationale next to each score. Scores are judgments; the rationale is what you can argue about.
3. Read quadrants, then decide: quick wins to Now; big bets sliced into experiments or smaller releases; fill-ins to backlog; money pits dropped (record the decision).
4. Re-score when evidence arrives (an experiment result, a new estimate), not to justify a preferred answer.

## Common mistakes
- Scoring everything 4: force a spread by comparing items to each other.
- Treating effort as only engineering time.
- Letting the matrix decide: it informs the roadmap conversation, it does not replace it.

## In Company Brain
- Fields on `solution` and `project` notes: `impact`, `effort`, optional `reach` and `confidence`.
- `brain refresh` writes a Mermaid quadrant chart, per-quadrant lists, and a RICE table to [[Company Prioritization]] and `<Team> Prioritization` (done, shipped, and dropped items are excluded).
- Skill: `/company-brain:prioritize`, then `/company-brain:roadmap` to act on it.

## References
- Intercom, RICE: Simple prioritization for product managers, https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/.
