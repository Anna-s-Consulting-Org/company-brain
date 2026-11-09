---
date: {{TODAY}}
type: system
tags: [system]
ai-first: true
layer: company
---

# Layers and privacy

## For future agent
This note is the human-readable version of the Company Brain layer model: what is shared, what stays personal, the link-direction rule, private sections, promotion, conflict-free teamwork, and the two channels: content through a shared folder (Google Shared Drive or another), the system through git. The binding spec is `.company-brain/references/layers.md`.

## What goes where
| Layer | Folder | Who sees it | Examples |
|---|---|---|---|
| Company | `Company/` | the whole company (through the shared folder) | [[Mission]], strategy, company OKRs, plans, roadmap, [[Org Chart]], people profiles, all-hands notes |
| Team | `Teams/<Team>/` | the whole company, owned by the team (through the shared folder) | team charter, team OKRs, projects, meetings, weekly updates and roll-ups, board, roadmap |
| Personal | `Personal/` | only you (never synced, never in git) | daily and weekly notes, 1:1s, private goals, drafts, inbox |

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

## Two channels: content and system
**Content travels through a shared folder.** Everything the company writes into the brain (people, teams, meetings, goals, decisions, and `Company/company.yaml` with the company's name and settings) lives in `Company/` and `Teams/`. `brain share --to <folder>` moves those two folders into a Google Shared Drive folder (`drive`) or any other shared folder such as OneDrive, Dropbox or a network share (`folder`) and links them back, so teammates see changes as soon as they sync. `Personal/` stays a normal local folder. There is no review step, so limit who can edit the company folder in Drive. With `local`, nothing is shared; good for trying the system alone.

**The system travels through git.** The engine, skills, templates, `System/` docs and `CLAUDE.md` live in a git repository, for example on GitHub, so improvements are versioned, reviewed and checked by CI. Git never carries content: `.gitignore` leaves out `Company/`, `Teams/` and `Personal/`, a pre-commit guard refuses any commit that holds content (or names a person, the company, or a company note in a system file), and CI checks every tracked file. To commit a system change, ask Claude (`/company-brain:contribute`) or run `./brain git stage`. Claude never pushes on its own.

The content choice is `sharing.model` in `brain.local.yaml` on each machine. What each model does step by step and a comparison: [[Sharing models]].

## What Claude pulls from your tools
The weekly and daily skills read calendar, Slack, email, Jira, Drive, and meeting notes only through the connectors you have enabled, and write what they find into your **personal** notes. Nothing from your messages reaches a team or company note unless you approve the team update or a promotion.
