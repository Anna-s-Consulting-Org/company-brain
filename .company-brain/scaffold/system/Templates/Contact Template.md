<%*
const role = await tp.system.prompt("role at their organisation");
const company = await tp.system.prompt("company as [[Organisation]]", "TBD");
const owner = await tp.system.prompt("owner on our side as [[Full Name]]", "TBD");
-%>
---
date: <% tp.date.now("YYYY-MM-DD") %>
type: person
tags: [person, contact]
ai-first: true
layer: company
company: "<% company %>"
role: "<% role %>"
owner: "<% owner %>"
email: TBD
aliases: []
handles: []
timeline:
  - fact: "<% role %>"
    from: TBD
    until: present
    learned: <% tp.date.now("YYYY-MM-DD") %>
---

# <% tp.file.title %>

## For future agent
This note is the shared contact card of <% tp.file.title %> (<% role %> at <% company %>), someone outside the company we work with: business-card facts only (role, organisation, work email, who on our side owns the relationship), used by the org page and the People Directory. How anyone relates to them (what they care about, how we can help each other, open asks) lives in each colleague's own Personal/Stakeholders, never here.

## Role and context
- TBD

## Shared meetings
```dataview
TABLE date, meeting_type
FROM "Company" OR "Teams"
WHERE type = "meeting" AND (contains(attendees, this.file.link) OR contains(string(attendees), "[[" + this.file.name + "]]"))
SORT date DESC
LIMIT 10
```

## My notes on them
Visible only to you: this query reads your own Personal/ folder, which is never shared.
```dataview
TABLE WITHOUT ID file.link AS "Note", type, relationship, last_interaction, follow_up
FROM "Personal"
WHERE (type = "stakeholder" OR type = "one-on-one")
  AND (person = this.file.link OR contains(string(person), "[[" + this.file.name + "]]") OR person = this.file.name)
```
