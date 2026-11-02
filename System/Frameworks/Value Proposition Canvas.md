---
date: {{TODAY}}
type: framework
tags: [framework, strategy, customer-fit]
ai-first: true
layer: company
confidence: high
---

# Value Proposition Canvas

## For future agent
This note explains the Value Proposition Canvas (Osterwalder, Pigneur, Bernarda, Smith, Value Proposition Design, 2014): what it is, how to fill it from evidence, how to judge fit, and how Company Brain implements it (template, `vpc` skill, frontmatter). Theory is stable; the worked example is fictional.

## What it is
A tool for designing and testing the fit between what a customer segment needs and what you offer. It has two halves (Value Proposition Design, Wiley 2014; https://www.strategyzer.com/library/the-value-proposition-canvas):

```
 VALUE MAP (what we offer)            CUSTOMER PROFILE (what they need)
 ┌───────────────────────────┐        ┌───────────────────────────┐
 │ Gain creators             │  --->  │ Gains                     │
 │ Products and services     │        │ Customer jobs             │
 │ Pain relievers            │  --->  │ Pains                     │
 └───────────────────────────┘        └───────────────────────────┘
```

**Customer profile** (observe first, always from evidence):
- **Customer jobs**: what customers are trying to get done in their work or life. Functional (complete a task), social (look good, gain status), emotional (feel secure). Also supporting jobs (buying, co-creating, transferring value).
- **Pains**: undesired outcomes, obstacles, and risks before, during, or after the job. Rank by severity.
- **Gains**: outcomes and benefits customers want. Required (the job fails without it), expected, desired (they would love it), unexpected (beyond what they imagine). Rank by relevance.

**Value map** (design second):
- **Products and services** the value proposition is built on.
- **Pain relievers**: how they eliminate or reduce specific pains.
- **Gain creators**: how they produce specific gains.

**Fit** happens when relievers and creators address the jobs, pains, and gains that matter most. The book names three stages:
1. **Problem-solution fit**: evidence that customers care about these jobs, pains, and gains, and a value proposition on paper that addresses them.
2. **Product-market fit**: evidence that customers actually want and use the product.
3. **Business-model fit**: evidence that the value proposition can be delivered in a profitable, scalable business model (see [[Business Model Canvas]]).

## How to use it
1. Pick one segment. Be specific ("heads of professional services at 200 to 2000 person B2B software companies", not "enterprises"). One canvas per segment.
2. Fill the customer profile from evidence: interviews, call notes, support tickets, usage data. Mark anything without evidence as a hypothesis.
3. Rank jobs by importance, pains by severity, gains by relevance. Most canvases fail because everything is treated as equally important.
4. Fill the value map, naming for each reliever or creator the specific pain or gain it addresses. An item that addresses nothing on the left is decoration.
5. Assess fit: are the top three pains and gains covered? What important items are gaps?
6. List the riskiest assumptions and test them (in Company Brain: experiments in the [[Opportunity Solution Tree]]).

## Common mistakes
- Starting with the value map (the product) and back-filling the customer profile to match it.
- Mixing several segments into one canvas.
- Listing features as pain relievers without saying which pain they relieve.
- Treating the canvas as finished: it is a living hypothesis, updated as evidence arrives.

## Worked example (fictional)
Segment: operations leads at 50 to 200 person agencies. Top job: deliver client projects on time with a small team (functional, importance 5). Top pain: status reporting takes half a day each week (severity 4, five interviews). Top gain: clients see progress without asking (desired, relevance 4). Pain reliever: auto-generated weekly client report (relieves the status-reporting pain). Gain creator: shareable live project board (creates the visibility gain). Gap: no answer yet for resourcing conflicts (a pain of severity 3). Fit stage: problem-solution. Riskiest assumption: clients will open a live board instead of asking for a report.

## In Company Brain
- Template: `Templates/Value Proposition Canvas Template.md`. Notes: `<layer>/Strategy/VPC - <Segment>.md`, `type: vpc`.
- Fields: `segment`, `status` (hypothesis, partially-validated, validated, retired), `fit` (none, problem-solution, product-market, business-model), `evidence` (links), `strategy` (link).
- Skill: `/company-brain:vpc`. Assumptions flow into discovery via `/company-brain:ost`; gaps become opportunities.
- Hub: [[Company Strategy]] lists every canvas with its fit stage.

## References
- Osterwalder, Pigneur, Bernarda, Smith, Value Proposition Design, Wiley, 2014 (stated).
- Strategyzer, The Value Proposition Canvas, https://www.strategyzer.com/library/the-value-proposition-canvas.
