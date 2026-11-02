<%*
const f = tp.file.folder(true);
const layer = f.startsWith("Company") ? "company" : f.startsWith("Teams") ? "team" : "personal";
const team = f.startsWith("Teams/") ? f.split("/")[1] : "";
const period = await tp.system.prompt("period: YYYY");
-%>
---
date: <% tp.date.now("YYYY-MM-DD") %>
type: plan
tags: [plan, planning]
ai-first: true
layer: <% layer %>
team: <% team ? '"[[' + team + ']]"' : "" %>
horizon: annual
period: <% period %>
status: draft
owner: "[[TBD]]"
---

# <% tp.file.title %>

## For future agent
This note is the annual plan for <% period %> at the <% layer %> layer. It records the review of the previous period, the choices for this one, and links to the objectives, discovery, and roadmap that carry it out. Status draft means choices are not committed yet.

## 1. Where we are
- Last year's objectives and final scores: TBD (link each objective)
- What changed in the market, customers, and team: TBD
- What the [[Strategy Kernel]] diagnosis says now: TBD

## 2. Mission, vision, strategy check
- [[Mission]] still right? TBD
- [[Vision]] signposts hit or missed: TBD
- Strategy changes (update [[Company Strategy]]): TBD

## 3. Annual objectives (3 to 5)
Create each with `/company-brain:okr` as `<YYYY> - Company - O<n> - <Title>`; list them here:
- TBD

## 4. Big bets and what we stop
- Bets (from [[Company Prioritization]] Big bets): TBD
- Stop doing: TBD

## 5. Organization and capacity
Teams, hires, and ownership changes needed: TBD ([[Organization]])

## 6. Quarter-by-quarter shape
| Quarter | Focus | Key milestones |
|---|---|---|
| Q1 | TBD | TBD |
| Q2 | TBD | TBD |
| Q3 | TBD | TBD |
| Q4 | TBD | TBD |

## 7. Risks and assumptions
- TBD
