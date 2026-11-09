<%*
const person = await tp.system.prompt("person as [[Full Name]]");
-%>
---
date: <% tp.date.now("YYYY-MM-DD") %>
type: stakeholder
tags: [stakeholder]
ai-first: true
layer: personal
person: "<% person %>"
relationship: TBD
influence: TBD
interest: TBD
last_interaction: TBD
follow_up: TBD
---

# <% tp.file.title %>

## For future agent
This note is my personal stakeholder view of <% person %>: what they care about, how we can help each other, how to work with them, and open asks in both directions. It is local-only and never shared; the shared, intranet-level profile is <% person %>. relationship (weak, medium, strong), influence and interest (high, medium, low) are my judgment and change over time; check last_interaction and the dates on each line before relying on them.

## What they care about
- TBD. Their goals, priorities, and pressures as I understand them, each with where I learned it and when.

## How we can help each other
- What I can offer them: TBD
- What I need from them: TBD

## How to work with them
- TBD. What lands, what to avoid, preferred channel and format, how they like decisions brought to them.

## Open asks
- [ ] TBD

## Notes
- TBD

## Interactions
```dataview
TABLE WITHOUT ID file.link AS "Note", type, date
FROM "Personal" OR "Company" OR "Teams"
WHERE (type = "meeting" OR type = "one-on-one" OR type = "daily" OR type = "weekly")
  AND (contains(file.outlinks, this.person) OR contains(file.outlinks, this.file.link))
SORT date DESC
LIMIT 15
```

## Private
Candid notes that must never leave this file.
