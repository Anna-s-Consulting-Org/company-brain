---
name: task
description: Add one task to the right board in seconds - parses the task, infers priority, due date, and the project, key result, or person it belongs to, adds a card to my board (or to the team board after asking), and links it from today's daily note. Use for "add a task", "remind me to", "todo", "put this on my board".
argument-hint: "<task>"
---

# Task

A shortcut for the `board` skill's Add step, for one task. For anything more (several cards, moving cards, hygiene), use `board`.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. **Take the task** from the argument. With no argument, take the latest task or action item from the conversation and say which one you picked. An idea is not a task: send it to the `capture` skill instead, and say so.
2. **Infer the card**: `brain period` for today. Priority 🔴 (urgent or blocking), 🟡 (this week or next), 🟢 (whenever); a due date only when one was stated or implied by a named day ("by Friday": work out the date from today and the week `brain period` prints); otherwise no date. Links: search for the project, KR (`[[<objective>#^krN]]`), or person it concerns and link only notes that exist.
3. **Pick the board**: `Personal/My Board.md` by default. A commitment the team made goes on `Teams/<Team>/<Team> Board.md` only after the user says yes, and needs an owner. Column: `## This week` when due within 7 days, otherwise `## Inbox`.
4. **Search the board first** for the same task; update that card rather than adding a second one.
5. **Add the card** in the card format of `references/propagation.md`: `- [ ] <priority> **Title** · @{YYYY-MM-DD}` (leave out `· @{...}` when there is no due date), with an indented context line holding the links.
6. **Link it from today**: add `- Task: **Title** on [[My Board]]` (or the team board) under `## Notes and captures` in today's daily note (`brain new daily` if it does not exist).
7. Return the board, the column, and the card in one line.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
