---
date: {{TODAY}}
type: hub
tags: [hub, org]
ai-first: true
layer: company
---

# Organization

## For future agent
This is the organization hub: the generated org chart, the list of teams, every shared people profile, and the generated map of who works on what. Profiles hold intranet-level facts only; private impressions and stakeholder notes live in each person's own Personal/Stakeholders and Personal/1-1s notes. The Who works on what block is rebuilt by `brain refresh` from project and objective notes and from work recorded on profiles from connected systems; edit those, not the block.

- [[Org Chart]] (generated from `manager:` and `team:` on profiles)
- [[Teams]]

## People
```dataview
TABLE role, team, manager
FROM "Company/Org/People"
WHERE type = "person"
SORT team ASC, file.name ASC
```

## Profiles missing basics
```dataview
LIST FROM "Company/Org/People"
WHERE type = "person" AND (role = "TBD" OR !role OR !team OR team = "TBD")
```

## Who works on what
<!-- brain:auto:start work-map -->
No people yet. Add profiles with `/company-brain:org` or `brain person add`.
<!-- brain:auto:end work-map -->

Add or update people with `/company-brain:org`. It also records who works on what from connected systems (project trackers, code hosts, shared docs) when the match is confident.
