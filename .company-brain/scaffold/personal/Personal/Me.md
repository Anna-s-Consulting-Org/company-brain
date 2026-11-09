---
date: {{TODAY}}
type: me
tags: [me]
ai-first: true
layer: personal
person: "[[{{ME}}]]"
teams: {{TEAMS_YAML}}
role: "{{ROLE}}"
manager: "[[{{MANAGER}}]]"
timezone: {{TIMEZONE}}
---

# Me

## For future agent
This is the identity record of the person who owns this copy of the brain ({{ME}}). Every Company Brain skill reads it first to know who "me" and "my team" are. It lives in Personal/, so it never goes to git or the shared folder; the shared profile is [[{{ME}}]].

## Working context
- Role: {{ROLE}}
- Home team: [[{{FIRST_TEAM}}]]
- Manager: [[{{MANAGER}}]]
- Timezone: {{TIMEZONE}}

## Preferences for the brain
- Weekly note day: Friday
- Sources to pull in weekly notes: calendar, Slack, email, Jira, Google Drive, meeting notes (remove what you do not use)
- Default layer for new notes when unclear: personal

## Private
Anything here stays local. Examples: career goals, notes to self about how you like to work.
