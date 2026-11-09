---
date: {{TODAY}}
type: system
tags: [system]
ai-first: true
layer: company
---

# How Company Brain works

## For future agent
This note is the plain-language overview of Company Brain: what it is, the three ways to use it (Obsidian, Claude, a Claude Project), the layer model, the operating rhythm, and how the pieces connect into one graph. Start here before reading the specs in `.company-brain/references/`.

## In one paragraph
Company Brain is a folder of markdown notes that holds a company's mission, strategy, goals, discovery, roadmap, organization, projects, meetings, and weekly work, all linked so it reads like one network. People browse and edit it in [[Obsidian]]; Claude reads and writes it through the Company Brain plugin (skills, hooks, an MCP server, and the `brain` CLI); colleagues who only use claude.ai can get a read-only snapshot as a Claude Project. It is built on the single-person [[obsidian-second-brain]] engine and adds team and company layers.

## Three ways in
| Surface | Who | Can write | How |
|---|---|---|---|
| Obsidian | everyone | yes | open this folder as a vault; Dataview hubs, Kanban boards, Templater templates, graph colour-coded by layer |
| Claude (Claude Code CLI, desktop app, Cowork) | anyone with the plugin | yes | `/company-brain:<skill>`, or just ask ("write my weekly note") |
| Claude Project on claude.ai | colleagues without Claude Code | no | upload the pack from `/company-brain:export` |

## Layers
- **Company** (`Company/`): shared with everyone.
- **Team** (`Teams/<Team>/`): shared with everyone, owned by the team.
- **Personal** (`Personal/`): yours only, never leaves your machine.
Links point up the stack, never down. Details: [[Layers and privacy]].

## Two channels
- **Content** (`Company/`, `Teams/`) reaches teammates through a Google Shared Drive or another shared folder (`./brain share`).
- **The system** (engine, skills, templates, these `System/` notes) travels through git. Git never carries content: a pre-commit guard and CI enforce it. Details: [[Sharing models]].

## The operating rhythm
| When | You run | What happens |
|---|---|---|
| Daily | `/company-brain:daily` | today's note: calendar, top three focus items linked to key results |
| Weekly | `/company-brain:weekly` | pulls the week from calendar, Slack, email, Jira, Drive, meeting notes; action items to your board; KR check-ins; drafts and publishes your team update |
| Weekly (lead) | `/company-brain:team-weekly` | team roll-up from everyone's updates, KR trends, risks, decisions needed |
| Per meeting | `/company-brain:meeting` | meeting note in the right layer, decisions and actions routed |
| Quarterly | `/company-brain:plan quarterly` | score, set OKRs top-down, discovery focus, prioritize, roadmap |
| Annually | `/company-brain:plan annual` | mission, vision, strategy review, annual objectives |
| Any time | `/company-brain:health` | leaks, broken links, unaligned OKRs, rebuild generated views |

## How it becomes a brain
Every note links to what it serves. A weekly note links key results; a key result belongs to an objective whose `parent:` is a company key result; that ladders to an annual objective, which serves the [[Mission]]. Discovery nodes link outcome, opportunity, solution, experiment. Projects link solutions and key results. People link teams and managers, and each profile lists the work the person does, from project and objective notes and from what connected systems show. Hubs ([[Company]], [[Company OKRs]], [[Company Discovery]], [[Organization]]) gather each area with live Dataview tables. `brain refresh` regenerates the views that tie it together: OKR trees, discovery trees and canvases, the prioritization matrix, the org chart, and `index.md`.

## Where things live
- Notes: `Company/`, `Teams/` (shared folder), `Personal/` (this machine). Company settings: `Company/company.yaml`; this machine's sharing setup: `brain.local.yaml`.
- External files: `Sources/` (symlinks to Desktop and Google Drive folders, read-only).
- Method: [[Frameworks]]. Templates: `Templates/`. Skills catalog: [[Skills]]. Automations: [[Automations]]. Setup: [[Setup]].
- Engine (hidden in Obsidian): `.company-brain/` holds the plugin, CLI, hooks, MCP server, and specs. System settings: `brain.yaml`.
