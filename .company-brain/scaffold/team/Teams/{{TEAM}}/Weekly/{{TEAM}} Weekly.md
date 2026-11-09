---
date: {{TODAY}}
type: hub
tags: [hub, weekly]
ai-first: true
layer: team
team: "[[{{TEAM}}]]"
---

# {{TEAM}} Weekly

## For future agent
This is the {{TEAM}} weekly hub: one update file per member per week and one team roll-up per week. Separate files per person mean two people never edit the same file in the shared folder.

## Roll-ups
```dataview
TABLE week, contributors
FROM "Teams/{{TEAM}}/Weekly"
WHERE type = "team-weekly"
SORT week DESC
LIMIT 12
```

## Member updates this week
```dataview
TABLE author, krs
FROM "Teams/{{TEAM}}/Weekly"
WHERE type = "team-update" AND week = dateformat(date(today), "kkkk-'W'WW")
```

Members publish with `/company-brain:weekly` (final step) or `/company-brain:promote`; the lead rolls up with `/company-brain:team-weekly`. Part of [[{{TEAM}}]].
