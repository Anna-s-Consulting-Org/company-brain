<%*
const f = tp.file.folder(true);
const layer = f.startsWith("Company") ? "company" : f.startsWith("Teams") ? "team" : "personal";
const team = f.startsWith("Teams/") ? f.split("/")[1] : "";
const period = await tp.system.prompt("period: YYYY-Qn for a quarter, YYYY for annual");
const owner = await tp.system.prompt("owner as [[Full Name]]");
const parent = await tp.system.prompt("parent: the objective or KR this ladders up to, as [[Note#^kr1]]", "");
-%>
---
date: <% tp.date.now("YYYY-MM-DD") %>
type: objective
tags: [objective, okr]
ai-first: true
layer: <% layer %>
team: <% team ? '"[[' + team + ']]"' : "" %>
level: <% layer %>
period: <% period %>
owner: "<% owner %>"
parent: "<% parent %>"
status: on-track
last_checkin: <% tp.date.now("YYYY-MM-DD") %>
---

# <% tp.file.title %>

## For future agent
This note is a <% layer %>-level objective for <% period %>, owned by <% owner %>. It holds the key results with live progress fields, the check-in history, and what it ladders up to (<% parent %>). Progress values change weekly: trust the latest Check-ins row, not prose.

## Objective
TBD. Qualitative, inspiring, time-bound. Answers: what do we want to achieve this period, and why does it matter now?

## Why now
TBD. Link the strategy or diagnosis this serves, for example [[Company Strategy]].

## Key results
<!-- One line per KR. Keep the block id (^kr1) so other notes can link to one KR as note-name#^kr1.
Numeric KR: baseline, target, current. Milestone KR: progress 0.0-1.0. Confidence: high, medium, low. -->
- **KR1** TBD [baseline:: 0] [target:: 0] [current:: 0] [unit:: TBD] [confidence:: medium] [owner:: <% owner %>] ^kr1
- **KR2** TBD [progress:: 0] [confidence:: medium] [owner:: <% owner %>] ^kr2
- **KR3** TBD [baseline:: 0] [target:: 0] [current:: 0] [unit:: TBD] [confidence:: medium] [owner:: <% owner %>] ^kr3

## Supporting objectives
Objectives in other layers whose `parent:` points here:
```dataview
LIST FROM "Company" OR "Teams" OR "Personal/Goals"
WHERE type = "objective" AND contains(string(parent), this.file.name)
```

## Supporting projects and outcomes
```dataview
TABLE type, status, owner
FROM "Company" OR "Teams"
WHERE (type = "project" AND contains(string(okrs), this.file.name)) OR (type = "outcome" AND contains(string(kr), this.file.name))
```

## Check-ins
| Date | KR | Value | Confidence | Note |
|---|---|---|---|---|

## Retrospective
Filled at the end of the period: final score per KR, what worked, what we learned, what carries over.
