---
date: {{TODAY}}
type: framework
tags: [framework, discovery, product]
ai-first: true
layer: company
confidence: high
---

# Opportunity Solution Tree

## For future agent
This note explains the Opportunity Solution Tree (Teresa Torres, Product Talk, 2016; Continuous Discovery Habits, 2021): the outcome, opportunity, solution, and assumption-test layers, how to grow and prune a tree, and how Company Brain stores each node as a linked note rendered as a Mermaid tree and an Obsidian canvas.

## What it is
A visual map from a desired outcome to the customer needs that could drive it, the solutions that could address those needs, and the tests that de-risk each solution (Teresa Torres, https://www.producttalk.org/opportunity-solution-trees/; Continuous Discovery Habits, Product Talk LLC, 2021).

```
                 Outcome (a measurable result, usually one KR)
                /                    |                    \
        Opportunity            Opportunity            Opportunity     customer needs, pains, desires
         /      \                  |
   Sub-opp     Sub-opp           ...
    /   |   \
 Solution Solution Solution                                           ways to address one opportunity
    |
 Assumption tests                                                      fast experiments on the riskiest assumptions
```

- **Outcome**: a product or business outcome the team can influence (for example "increase week-2 retention of new teams"), not an output ("ship onboarding v2").
- **Opportunities**: customer needs, pain points, and desires discovered through research, framed from the customer's perspective. They form a hierarchy: big opportunities break into smaller, more solvable sub-opportunities.
- **Solutions**: possible ways to address one target opportunity. Torres recommends generating several and comparing them ("compare and contrast") rather than falling in love with the first.
- **Assumption tests**: small experiments that test the riskiest assumptions behind a solution: desirability, viability, feasibility, usability, and ethical assumptions.

## How to use it
1. Start from one outcome, ideally a key result the team owns.
2. Interview customers continuously (Torres: weekly). Map opportunities you hear, with evidence. Never write a solution in an opportunity node.
3. Structure the opportunity space: group related needs, split vague ones into sub-opportunities.
4. Choose a target opportunity by comparing opportunity size, market factors, company factors, and customer factors.
5. Generate at least three solutions for it. Story-map each and list its assumptions.
6. Test the riskiest assumptions first with the cheapest test that could prove them wrong (prototype tests, one-question surveys, data mining).
7. Keep the tree current: it is a thinking tool for this week's decisions, not a one-off document.

## Common mistakes
- Solutions disguised as opportunities ("users need a dashboard").
- Opportunities with no customer evidence.
- One solution per opportunity (no comparison, so no learning).
- Testing whole ideas instead of individual assumptions.
- A tree so wide no one can read it: prune, and keep parked branches marked.

## Worked example (fictional)
Outcome: median time to first shared board falls from 3 days to 1 day (KR2 of a team objective). Opportunity: "I do not know which template fits my workshop" (evidence: 6 of 10 interviews). Solutions: a template picker quiz (impact 3, effort 2), a guided first board (impact 4, effort 3), an onboarding call for teams over 20 seats (impact 4, effort 4). Experiment on the guided first board: usability assumption "new admins finish the 5-step guide in one sitting", success criteria 4 of 5 testers under 10 minutes.

## In Company Brain
- One note per node in `<layer>/Discovery/`: `OUT - ...` (`type: outcome`, `kr:`), `OPP - ...` (`type: opportunity`, `parent:`, `evidence:`, `opportunity_size:`), `SOL - ...` (`type: solution`, `parent:`, `impact:`, `effort:`, `confidence:`, `status:`, `roadmap:`), `EXP - ...` (`type: experiment`, `parent:`, `assumption_type:`, `result:`).
- `brain refresh` draws every tree as Mermaid in the discovery hub ([[Company Discovery]] or `<Team> Discovery`) and writes `OST - <outcome>.canvas`, whose cards are the real notes.
- Skill: `/company-brain:ost`. Scored solutions flow to the [[Effort-Impact Matrix]] and the [[Now-Next-Later Roadmap]].

## References
- Teresa Torres, Continuous Discovery Habits, Product Talk LLC, 2021 (stated).
- Product Talk, Opportunity Solution Trees, https://www.producttalk.org/opportunity-solution-trees/.
