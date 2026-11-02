---
date: {{TODAY}}
type: framework
tags: [framework, okr, goals]
ai-first: true
layer: company
confidence: high
---

# OKRs

## For future agent
This note explains Objectives and Key Results (Andy Grove at Intel; popularized by John Doerr, Measure What Matters, 2018): how to write objectives and key results, how they cascade across company, team, and personal layers, how to check in and score, and how Company Brain stores them (one note per objective, KRs as list items with inline fields and block ids).

## What it is
A goal system with two parts. The **objective** says what you want to achieve: qualitative, significant, motivating. The **key results** say how you will know: measurable, time-bound, usually two to four per objective. Grove developed the practice at Intel (High Output Management, 1983); Doerr brought it to Google and wrote Measure What Matters (Portfolio, 2018). Google's public guide: https://rework.withgoogle.com/intl/en/guides/set-goals-with-okrs.

## Writing them
- Objective: one line, no numbers, worth getting out of bed for. "Make onboarding effortless for new teams."
- Key result: an outcome with a baseline and a target, "Week-2 retention of new teams from 38 percent to 50 percent". Milestone KRs ("migration complete") are allowed but should be the minority.
- Outputs are not key results: "launch the new checklist" is a project; its KR is the change it should cause.
- Scoring: Google's `re:Work` guide puts the sweet spot for the average score across OKRs at 0.6 to 0.7; scoring 1.0 every time means the goals were not ambitious enough (rework.withgoogle.com).
- Committed vs aspirational: many teams mark committed OKRs (expected to hit 1.0) separately from aspirational ones (expected to fall short). Say which kind each objective is.

## The cascade in Company Brain
```
Mission / Vision
  └─ Annual company objective (YYYY)                 Company/OKRs
       └─ Quarterly company objective (YYYY-Qn)     parent: annual KR
            └─ Team objective (YYYY-Qn)              Teams/<Team>/OKRs, parent: company KR
                 └─ Personal goal (YYYY-Qn)          Personal/Goals, parent: team KR (local only)
                      └─ projects, solutions, weekly work linked to the KR
```
Alignment, not command: teams propose their objectives and link them to the company KR they serve. A team objective with no parent is flagged by `brain check`.

## Rhythm
- **Set**: at quarterly planning (`/company-brain:plan`).
- **Check in weekly**: current value and confidence per KR, one row in the objective's Check-ins table (`/company-brain:okr checkin`, part of `/company-brain:weekly`).
- **Score at the end**: 0.0 to 1.0 per KR, objective score is the mean, plus a short retrospective.

## Status heuristic
Compare progress with time elapsed in the period. Clearly behind pace, or confidence low: at-risk. Far behind with no recovery plan: off-track. Status is a conversation starter, not a grade.

## Common mistakes
- Too many: more than five objectives per level means no priorities.
- Task lists dressed up as KRs.
- Sandbagged targets that always score 1.0.
- Set and forget: no weekly check-ins, so the end-of-quarter score is a surprise.
- Personal OKRs tied to performance reviews (people then sandbag). Keep personal goals in the personal layer.

## In Company Brain
- One note per objective, `type: objective`, named `<period> - <Owner> - O<n> - <Title>`. KRs are list items under `## Key results` with inline fields `[baseline:: ] [target:: ] [current:: ] [progress:: ] [confidence:: ] [owner:: ]` and a block id `^kr1`, so any note can link to one KR as `[[<objective>#^kr1]]`.
- `brain refresh` writes the cascade to `OKR Tree - <period>` (shared, without personal goals) and `Personal/Goals/My OKR Tree - <period>` (with them).
- Skill: `/company-brain:okr`. Hub: [[Company OKRs]].

## References
- John Doerr, Measure What Matters, Portfolio, 2018 (stated).
- Andy Grove, High Output Management, Random House, 1983 (stated).
- Google `re:Work`, Set goals with OKRs, https://rework.withgoogle.com/intl/en/guides/set-goals-with-okrs.
- What Matters, What is an OKR? Definition and examples, https://www.whatmatters.com/faqs/okr-meaning-definition-example.
