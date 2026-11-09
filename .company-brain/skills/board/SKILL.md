---
name: board
description: Show or update kanban boards at any layer - my personal board, a team board, or a roadmap; flags overdue and stale cards, adds cards from the conversation, moves done work, and triages stale items in bulk. Use for "show my board", "team board", "add a task", "what's overdue", "clean up the board".
---

# Board

Boards use the Obsidian Kanban plugin format: `kanban-plugin: board` frontmatter, `## Column` headings, card checkboxes, no preamble (it would render as a phantom column). Card format: `references/propagation.md`.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Boards
| Board | Holds |
|---|---|
| `Personal/My Board.md` | my tasks and action items (Inbox, This week, In progress, Waiting, Done) |
| `Teams/<Team>/<Team> Board.md` | team commitments only |
| `Company/Roadmap/Company Roadmap.md`, `Teams/<Team>/<Team> Roadmap.md` | Now, Next, Later (use the `roadmap` skill) |

## Steps
1. Pick the board (default: mine). Read it: columns, card counts, overdue cards (past `@{date}`), Waiting cards older than a week (by their date stamp; there are no column timestamps, so do not guess dwell time).
2. **Add**: one card per task with priority (🔴 🟡 🟢), due date if stated, and links to the project, KR, or person. Team board cards need an owner.
3. **Move**: done cards go to `## ✅ Done` as `- [x] ~~**Title**~~ ✅ <Mon DD>`; never delete cards.
4. **Hygiene** (when asked or more than 20 open cards): list stale and overdue cards and offer per card: done, reschedule (new date), move to Waiting, or archive to Done with a note. Apply in one pass after the user answers.
5. Propagate: a finished card that belongs to a project adds a status-log row there.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
