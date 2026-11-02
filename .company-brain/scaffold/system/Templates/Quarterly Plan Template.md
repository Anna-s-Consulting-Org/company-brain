<%*
const f = tp.file.folder(true);
const layer = f.startsWith("Company") ? "company" : f.startsWith("Teams") ? "team" : "personal";
const team = f.startsWith("Teams/") ? f.split("/")[1] : "";
const period = await tp.system.prompt("period: YYYY-Qn");
-%>
---
date: <% tp.date.now("YYYY-MM-DD") %>
type: plan
tags: [plan, planning]
ai-first: true
layer: <% layer %>
team: <% team ? '"[[' + team + ']]"' : "" %>
horizon: quarterly
period: <% period %>
status: draft
owner: "[[TBD]]"
---

# <% tp.file.title %>

## For future agent
This note is the quarterly plan for <% period %> at the <% layer %> layer. It records the review of the previous period, the choices for this one, and links to the objectives, discovery, and roadmap that carry it out. Status draft means choices are not committed yet.

## 1. Last quarter
| Objective | Final score | Lesson |
|---|---|---|
| TBD | TBD | TBD |

## 2. This quarter's objectives
Each quarterly objective ladders up to an annual objective KR via `parent:`. Team objectives then ladder up to these. Create with `/company-brain:okr`:
- TBD

## 3. Discovery focus
Outcomes to work on (one per key result worth discovery): [[Company Discovery]]
- TBD

## 4. Priorities and roadmap
- From [[Company Prioritization]]: quick wins to do now, big bets to slice: TBD
- [[Company Roadmap]] Now column after this plan: TBD

## 5. Capacity and dependencies
| Team | Owns | Depends on |
|---|---|---|
| TBD | TBD | TBD |

## 6. Cadence this quarter
- Weekly check-ins every TBD; mid-quarter review on TBD; scoring on TBD.

## 7. Risks
- TBD
