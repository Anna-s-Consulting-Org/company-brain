---
name: context
description: Load company context from the brain before strategic work - identity, mission, vision, values, current OKR cascade, strategy, VPCs, teams, roadmap - in progressive levels to save tokens. Use for "what is our strategy", "load company context", "remind me of our OKRs", "how does this fit our goals", or before drafting anything strategic.
---

# Context

Read-only. Loads the shared company layer into the conversation so answers are grounded in the brain, not in memory.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Levels (load the smallest that answers the question)
| Level | Loads | Command |
|---|---|---|
| 0 | who I am, my teams, today's period, sharing model | `brain whoami` |
| 1 | level 0 plus mission, vision, values, current-quarter OKR cascade | `brain context --level 1` |
| 2 | level 1 plus strategy notes and VPCs, team summaries, company roadmap | `brain context --level 2` |
| 3 | one area in depth: read the hub (`Company Strategy`, `<Team>`, `Company Discovery`) and the notes it lists | file reads |

## Steps
1. Pick the level from the question. Strategic drafting usually needs 2; "is this aligned?" needs 1; a team question needs 3 on that team.
2. Run the command. Read `index.md` if you need to find a specific note.
3. Answer with the sources named (`[[Mission]]`, `[[YYYY-Qn - Company - O1 - ...]]`). Flag anything still `TBD` or `status: draft` as not yet agreed.
4. Do not write notes in this skill. If the user wants to change something, hand off to `strategy`, `okr`, `vpc`, or `roadmap`.

Personal notes other than `Me.md` are never part of shared context; include the user's own Personal notes only when they ask about their own work.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
