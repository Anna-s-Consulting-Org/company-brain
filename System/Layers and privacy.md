---
date: {{TODAY}}
type: system
tags: [system]
ai-first: true
layer: company
---

# Layers and privacy

## For future agent
This note is the human-readable version of the Company Brain layer model: what is shared, what stays personal, the link-direction rule, private sections, promotion, conflict-free teamwork, and the two sharing transports (git and Google Drive). The binding spec is `.company-brain/references/layers.md`.

## What goes where
| Layer | Folder | Who sees it | Examples |
|---|---|---|---|
| Company | `Company/` | the whole company | [[Mission]], strategy, company OKRs, plans, roadmap, [[Org Chart]], people profiles, all-hands notes |
| Team | `Teams/<Team>/` | the whole company, owned by the team | team charter, team OKRs, projects, meetings, weekly updates and roll-ups, board, roadmap |
| Personal | `Personal/` | only you (gitignored, never synced) | daily and weekly notes, 1:1s, private goals, drafts, inbox |

Your identity lives in `Personal/Me.md`; your public profile lives in `Company/Org/People/<Your Name>.md`.

## The one rule: links point up
Your personal notes can link to anything. Shared notes can never link to personal notes: for everyone else the link is broken, and its title alone can leak something (a 1:1 title, a draft decision). The layer guard hook warns Claude the moment a shared note breaks this, and `brain check` scans the whole brain.

## Private sections
Inside a personal note, anything under a `## Private` heading never leaves that note, not even when you promote the note.

## Sharing on purpose: promotion
Personal to team to company is always deliberate. Ask Claude to share or publish a note (`/company-brain:promote`): it builds a clean copy without private sections or personal links, shows you the diff, and writes it to the team or company only after you say yes. Your weekly note ends with a drafted team update that is published the same way.

## Working together without conflicts
- Everyone publishes their own weekly update file; the lead writes the roll-up.
- KR owners edit only their own KR line and add one check-in row.
- One note per meeting, written by the note-taker.
- Generated views (`OKR Tree`, prioritization, org chart, discovery canvases) are rebuilt by `brain refresh`; never merge them by hand.

## Sharing transports
**Git (default, recommended).** The brain is a private git repository. `Company/`, `Teams/`, `System/`, `Templates/`, and `.company-brain/` are committed; `Personal/`, `Sources/`, `Exports/`, `index.md`, and `log.md` are gitignored. Company-layer changes go through pull requests so the company layer has review. In Obsidian, the Obsidian Git community plugin can pull and push on a schedule. Claude never pushes on its own.

**Google Shared Drive.** For teams that do not use git: put `Company/` and each `Teams/<Team>/` in Shared Drive folders and replace the local folders with symlinks to them (Drive for Desktop, mirror mode). Keep `Personal/` a normal local folder. There is no review step, so limit who can edit the company folder in Drive.

**Local.** Nothing is shared; good for trying the system alone.

The choice is `sharing.model` in `brain.yaml`. What each model does step by step, what drive mode leaves manual, and a comparison: [[Sharing models]].

## What Claude pulls from your tools
The weekly and daily skills read calendar, Slack, email, Jira, Drive, and meeting notes only through the connectors you have enabled, and write what they find into your **personal** notes. Nothing from your messages reaches a team or company note unless you approve the team update or a promotion.
