<%*
const f = tp.file.folder(true);
const layer = f.startsWith("Company") ? "company" : f.startsWith("Teams") ? "team" : "personal";
const team = f.startsWith("Teams/") ? f.split("/")[1] : "";
const owner = await tp.system.prompt("owner as [[Full Name]]");
const okrs = await tp.system.prompt("key result(s) this serves, as [[Objective#^kr1]]", "");
-%>
---
date: <% tp.date.now("YYYY-MM-DD") %>
type: project
tags: [project]
ai-first: true
layer: <% layer %>
team: <% team ? '"[[' + team + ']]"' : "" %>
owner: "<% owner %>"
status: planning
okrs: [<% okrs ? '"' + okrs + '"' : "" %>]
solution: ""
impact: 
effort: 
roadmap: none
start: <% tp.date.now("YYYY-MM-DD") %>
due: TBD
refs: []
---

# <% tp.file.title %>

## For future agent
This note is a <% layer %>-level project owned by <% owner %>, serving <% okrs %>. It holds the goal, scope, plan, status log, and decisions. Status values change: check the newest Status log row before trusting the frontmatter.

## Goal
TBD. The outcome this project delivers and how we will know it worked.

## Scope
- In: TBD
- Out: TBD

## People
| Role | Person |
|---|---|
| Owner | <% owner %> |
| Contributors | TBD |
| Stakeholders | TBD |

People profiles that record work on this project (from connected systems, via `brain person works-on`):
```dataview
TABLE WITHOUT ID file.link AS "Person", w.role AS "Role", w.confidence AS "Confidence", w.checked AS "As of"
FROM "Company/Org/People"
FLATTEN works_on AS w
WHERE type = "person" AND contains(string(w.project), this.file.name) AND (!w.until OR w.until = "present")
```

## Plan and milestones
| Milestone | Date | Status |
|---|---|---|
| TBD | TBD | TBD |

## Status log
| Date | Status | Note |
|---|---|---|
| <% tp.date.now("YYYY-MM-DD") %> | planning | created |

## Decisions
- None yet.

## Risks and dependencies
- TBD
