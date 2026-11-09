---
name: project
description: Create or update a project in the right layer - goal, scope, owner, the key results it serves, linked solution, status log, milestones, and a card on the layer board; or summarize project status for a layer. Use for "new project", "update project X", "project status", "what projects serve this KR".
---

# Project

Schema: `type: project`. Folder: `Company/Projects/`, `Teams/<Team>/Projects/`, or `Personal/Projects/`.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Create
1. Layer: team by default (my team) if it is team work; company for cross-team initiatives; personal for my own side work.
2. Ask: name, owner, goal, the KR(s) it serves (offer the layer's current KRs), the solution it delivers (if it came from discovery), due date. Unknowns stay TBD.
3. `brain new project --layer <l> [--team T] --title "<Name>" --set owner="[[<Owner>]]" --set 'okrs=["[[<objective>#^krN]]"]' [--set solution="[[SOL - ...]]"] [--set due=<date>]`.
4. Fill goal, scope, people, milestones.
5. Propagate: a card on the layer board (`<Team> Board.md` or `My Board.md`) in Backlog or In progress; if `roadmap:` is set, the roadmap card; the solution's `project:` field.

## Update
Append a row to `## Status log` (date, status, note) for every status change; update `status:` frontmatter; decisions go to `## Decisions` (and the `decide` skill if significant). Completed: `status: completed`, a final status row with the result against its KR, the board card to Done.

## Status report
For a layer: active projects grouped by KR, with owner, last status row, due date, and anything overdue or without a status update in two weeks.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
