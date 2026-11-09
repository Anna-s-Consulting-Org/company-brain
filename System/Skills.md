---
date: {{TODAY}}
type: system
tags: [system]
ai-first: true
layer: company
---

# Skills

## For future agent
This note is the catalog of Company Brain skills: what each does and where it writes. Skills live in `.company-brain/skills/<name>/SKILL.md` and run as `/company-brain:<name>` in Claude Code, the Claude desktop app, and Cowork, or automatically when a request matches their description. The plugin provides them; Claude Code opened in the brain folder gets the same names without it from `.claude/commands/company-brain/`.

## Catalog
| Skill | Does | Writes to |
|---|---|---|
| `/company-brain:setup` | set up the brain, onboard a teammate, share content through Drive or a shared folder | `Personal/Me.md`, teams, `Company/company.yaml`, `brain.local.yaml` |
| `/company-brain:context` | load company context before strategic work | reads only |
| `/company-brain:daily` | today's note with calendar and focus | `Personal/Daily/` |
| `/company-brain:weekly` | weekly note from all your tools, action items, KR check-ins, team update | `Personal/Weekly/`, your board, KR lines, `Teams/<Team>/Weekly/` on approval |
| `/company-brain:team-weekly` | team roll-up from members' updates | `Teams/<Team>/Weekly/` |
| `/company-brain:okr` | create, check in, score, align OKRs | `Company/OKRs/`, `Teams/<Team>/OKRs/`, `Personal/Goals/` |
| `/company-brain:plan` | annual and quarterly planning | `<layer>/Planning/`, objectives, roadmap |
| `/company-brain:strategy` | mission, vision, values, strategy kernel, Playing to Win, BMC | `Company/`, `Company/Strategy/` |
| `/company-brain:vpc` | Value Proposition Canvas per segment | `<layer>/Strategy/VPC - <Segment>` |
| `/company-brain:ost` | opportunity solution trees | `<layer>/Discovery/` |
| `/company-brain:prioritize` | effort-impact matrix and RICE | scores on solutions and projects |
| `/company-brain:roadmap` | Now, Next, Later roadmap | roadmap boards |
| `/company-brain:org` | people, teams, org chart | `Company/Org/People/`, `Teams/` |
| `/company-brain:project` | projects and status | `<layer>/Projects/`, boards |
| `/company-brain:meeting` | meeting notes, 1:1s, actions and decisions | `<layer>/Meetings/`, `Personal/1-1s/` |
| `/company-brain:decide` | decision records | `<layer>/Decisions/` |
| `/company-brain:board` | kanban boards at any layer | boards |
| `/company-brain:promote` | share a personal note with the team or company | the target layer |
| `/company-brain:connect` | mount Desktop and Google Drive folders as sources | `Sources/`, `Company/company.yaml` |
| `/company-brain:ingest` | read a document, or a whole folder in resumable batches, into the brain (Word and OpenDocument too) | `<layer>/Knowledge/` and the notes it informs |
| `/company-brain:health` | check and repair the brain | fixes across the brain |
| `/company-brain:export` | Claude Project pack for claude.ai | `Exports/Claude Project/` |
| `/company-brain:checkin` | ask me whether the old notes I own still hold, and save the news | the notes I own, `.checkin.json` (local) |
| `/company-brain:reconcile` | find contradictions between notes, prove each with verbatim quotes, resolve or flag | the notes concerned, decision records for open conflicts |
| `/company-brain:crew` | one logbook shared by Claude Code, Codex, Cursor and Grok Bot | `Personal/Crew/` |
| `/company-brain:save` | save everything worth keeping from the conversation, each item in the right note and layer | the notes each item belongs in, today's daily note |
| `/company-brain:capture` | capture an idea in seconds | `Personal/Notes/Idea - <Title>`, today's daily note |
| `/company-brain:find` | search the brain, results with context and grouped by type | reads only |
| `/company-brain:recap` | summarize today, a week, a month or a quarter | reads only (saves on request) |
| `/company-brain:challenge` | red-team an idea or plan against strategy, decisions and experiments | today's daily note; a report on request |
| `/company-brain:task` | add one task to the right board | `Personal/My Board.md` (team board on approval), today's daily note |
| `/company-brain:contribute` | commit a system improvement (skill, template, command, engine, docs) to git without any company content | a git commit of system files, on your yes |

## How to run them
- **Claude Code / desktop app / Cowork**: type `/company-brain:weekly` (or any name above), or ask in plain words ("prepare my 1:1 with Sam", "prioritize the platform solutions"). This works with the plugin installed and, in Claude Code opened in the brain folder, without it: `.claude/commands/company-brain/` holds one generated command per skill (`./brain commands` rewrites them from the skills; CI fails if they are out of date). Cloud sessions on claude.ai load the plugins of your claude.ai account and organization, but not one installed on your machine or enabled by this repository, so unless company-brain is an account or organization plugin, the project commands are the route there.
- **Inside Obsidian**: run Claude in the vault folder (a terminal in this folder, or an Obsidian plugin that embeds Claude Code); the brain's `CLAUDE.md` and the plugin load automatically. Templates in `Templates/` work with Templater without Claude.
- **From the filesystem**: the `brain` CLI does the deterministic parts without Claude: `./brain period`, `./brain new objective ...`, `./brain promote <note> --to team` (dry run, then `--yes`), `./brain refresh`, `./brain check`, `./brain connect`, `./brain share` (link `Company/` and `Teams/` into a shared folder), `./brain git status` and `./brain git stage` (system changes only), `./brain export-pack`, `./brain upstream-check` (changes in obsidian-second-brain to the files Company Brain borrowed). Run `./brain --help`.
- **Claude Desktop chat (not Cowork)**: add the brain MCP server (see [[Setup]]); its `brain_list_skills` and `brain_get_skill` tools expose most skills as playbooks.

## Relationship to obsidian-second-brain
Company Brain vendors the AI-first rules, the write validator, and the vault MCP server from [[obsidian-second-brain]] and adds its own skills. The obsidian-second-brain commands (research, ingest of web sources, synthesis) still work on your personal vault; do not point them at this brain.

Commands taken over from obsidian-second-brain and adapted to the layers: `save`, `capture`, `find`, `recap`, `challenge` and `task`. Every upstream command has a recorded decision in `.company-brain/upstream.json` (`commands.map`): adapted into a skill, covered by an existing one, deferred, or declined with the reason (web and social research, codebase notes, personal thinking tools). `./brain upstream-check` lists new upstream commands that have no decision yet; `.company-brain/references/upstream-sync.md` says how to bring them in.
