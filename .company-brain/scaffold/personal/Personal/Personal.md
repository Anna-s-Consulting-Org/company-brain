---
date: {{TODAY}}
type: hub
tags: [hub, personal]
ai-first: true
layer: personal
---

# Personal

## For future agent
This is the personal dashboard of {{ME}}: today, this week, goals, the personal board, 1:1s, and stakeholders. Everything under Personal/ is local-only and gitignored. Shared notes never link here; this note links up freely.

## Now
- Today: run `/company-brain:daily`; this week: `/company-brain:weekly`
- Board: [[My Board]] | Identity: [[Me]] | Stakeholders: [[My Stakeholders]]
- Team: [[{{FIRST_TEAM}}]] | Company: [[Company|{{COMPANY}}]]

## Recent daily notes
```dataview
LIST FROM "Personal/Daily" SORT file.name DESC LIMIT 7
```

## Weekly notes
```dataview
TABLE period, krs
FROM "Personal/Weekly"
WHERE type = "weekly"
SORT week DESC
LIMIT 8
```

## Key results I own (all layers)
```dataview
TABLE WITHOUT ID file.link AS "Objective", L.text AS "Key result", L.confidence AS "Confidence"
FROM "Company/OKRs" OR "Teams" OR "Personal/Goals"
FLATTEN file.lists AS L
WHERE type = "objective" AND contains(string(L.owner), "{{ME}}")
```

## 1:1s
```dataview
TABLE person, cadence
FROM "Personal/1-1s"
WHERE type = "one-on-one"
```

## Stakeholder follow-ups due
```dataview
TABLE WITHOUT ID file.link AS "Stakeholder", follow_up AS "Follow up", relationship
FROM "Personal/Stakeholders"
WHERE type = "stakeholder" AND typeof(follow_up) = "date" AND follow_up <= date(today)
SORT follow_up ASC
```
