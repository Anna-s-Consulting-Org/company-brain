---
name: org
description: Manage the organization in the brain - shared people profiles (role, team, manager, with bi-temporal history), team spaces and charters, and the generated org chart. Use for "add a person", "new team", "X moved to team Y", "who reports to", "org chart", "who is on the platform team".
argument-hint: "[add person | new team | X moved to Y]"
---

# Organization

Profiles: `Company/Org/People/<Full Name>.md` (`type: person`). Teams: `Teams/<Team>/<Team>.md` (`type: team`). Chart: `Company/Org/Org Chart.md` (generated).

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Modes
- **add person**: `brain person add "<Full Name>" --role "<Role>" --team "<Team>" --manager "<Manager>"`. Ask for anything missing; unknowns stay TBD.
- **change role, team, or manager**: never overwrite history. Update the current `role:`, `team:`, or `manager:` and append to `timeline:` (close the old fact with `until: <date>`, add the new one with `from:` and `learned: <today>`).
- **add team**: `brain team add "<Team>" --lead "<Lead>"`, then fill the charter mission (ask), `parent:` (department), rituals, and Slack channel.
- **show**: `brain refresh`, then present `Org Chart.md`, or a team's members (Dataview in the charter) and objectives.

## Directory lookups (optional)
If the user asks to fill profiles from a directory and a connector is available (company search such as Glean people search, a Slack profile, an org-users tool), propose the values and confirm before writing. Store only intranet-level facts: name, role, team, manager, location. Nothing about performance, compensation, health, or personal life: that never belongs in a shared profile, and in Personal/ only when the user explicitly writes it.

## Rules
- A profile is shared. Impressions, feedback, and 1:1 content go to `Personal/1-1s/1-1 - <Person>.md` via the `meeting` skill.
- Leavers: set `status: left`, close the timeline fact, keep the note (history stays traversable).
- `brain refresh` after every change (org chart, team pages).

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
