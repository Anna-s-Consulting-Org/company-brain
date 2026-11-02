<%*
const f = tp.file.folder(true);
const layer = f.startsWith("Company") ? "company" : f.startsWith("Teams") ? "team" : "personal";
const team = f.startsWith("Teams/") ? f.split("/")[1] : "";
const horizon = await tp.system.prompt("horizon, for example YYYY-YYYY");
-%>
---
date: <% tp.date.now("YYYY-MM-DD") %>
type: strategy
tags: [strategy]
ai-first: true
layer: <% layer %>
team: <% team ? '"[[' + team + ']]"' : "" %>
framework: kernel
horizon: <% horizon %>
status: draft
owner: "[[TBD]]"
---

# <% tp.file.title %>

## For future agent
This note is a strategy in Richard Rumelt's kernel form (diagnosis, guiding policy, coherent actions) for <% horizon %> at the <% layer %> layer. It explains how we intend to win, given the [[Mission]] and [[Vision]]. Draft until approved.

## Diagnosis
What is going on here? Name the critical challenge, not a list of goals. Cite evidence (sources, data, customer research) with dates.
- TBD

## Guiding policy
The overall approach that deals with the challenge. It rules options out as much as it rules them in.
- TBD

## Coherent actions
Coordinated steps that carry out the policy and reinforce each other. Each one should become an annual objective, a project, or a decision.
| Action | Becomes | Link |
|---|---|---|
| TBD | objective / project / decision | TBD |

## Bad-strategy check
- [ ] Not fluff (plain words, no buzzwords standing in for thinking)
- [ ] Faces the challenge (the diagnosis names it)
- [ ] Not a list of goals dressed up as strategy
- [ ] Objectives are achievable and address the challenge

## Customer fit
Value proposition canvases that support this strategy: TBD ([[Value Proposition Canvas]])

Method: [[Strategy Kernel]].
