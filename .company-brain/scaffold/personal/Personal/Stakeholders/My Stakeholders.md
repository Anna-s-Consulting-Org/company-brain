---
date: {{TODAY}}
type: hub
tags: [hub, stakeholders]
ai-first: true
layer: personal
---

# My Stakeholders

## For future agent
This is the personal stakeholder map of {{ME}}: one `Stakeholder - <Name>` note per person whose support, input, or decisions matter to my work, with relationship, influence, interest, last interaction, and the next follow-up. It is local-only and never shared. Influence and interest are my judgment (high, medium, low); the approach column follows the power-interest grid. Create a stakeholder note with `/company-brain:org` ("track Jane Doe as a stakeholder") or `brain new stakeholder --title "<Full Name>"`.

## Follow-ups due
```dataview
TABLE WITHOUT ID file.link AS "Stakeholder", follow_up AS "Follow up", relationship, last_interaction AS "Last interaction"
FROM "Personal/Stakeholders"
WHERE type = "stakeholder" AND typeof(follow_up) = "date" AND follow_up <= date(today)
SORT follow_up ASC
```

## Map
```dataview
TABLE WITHOUT ID file.link AS "Stakeholder", choice(person.company, person.company, person.team) AS "Org",
  choice(influence = "high", choice(interest = "high", "Manage closely", "Keep satisfied"), choice(interest = "high", "Keep informed", "Monitor")) AS "Approach",
  influence, interest, relationship, last_interaction AS "Last interaction", follow_up AS "Follow up"
FROM "Personal/Stakeholders"
WHERE type = "stakeholder"
SORT influence ASC, interest ASC
```

## Going quiet
High-influence stakeholders with no recorded interaction in the last 30 days.
```dataview
TABLE WITHOUT ID file.link AS "Stakeholder", last_interaction AS "Last interaction", relationship
FROM "Personal/Stakeholders"
WHERE type = "stakeholder" AND influence = "high"
  AND (typeof(last_interaction) != "date" OR last_interaction < date(today) - dur(30 days))
SORT last_interaction ASC
```

## How to use it
- Before a meeting, read the person's stakeholder note and their shared profile ([[Organization]] lists every profile).
- After a meeting, the meeting skill updates `last_interaction` on each attendee's stakeholder note and adds new open asks.
- Daily and weekly notes list follow-ups due and high-influence people going quiet.
