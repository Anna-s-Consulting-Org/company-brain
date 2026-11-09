---
name: daily
description: Create or update today's personal daily note - calendar, focus items linked to the key results they move, due and overdue board cards, carry-over from yesterday, and captures from the conversation. Use for "daily note", "plan my day", "what's on today", "start my day".
---

# Daily

The daily note is personal (`Personal/Daily/<YYYY-MM-DD>.md`) and never shared.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. `brain period`. If today's note does not exist: `brain new daily`. If it exists, update it in place (inject into sections, never overwrite what the user wrote).
2. **Calendar**: if a calendar connector is available (for example Google Calendar `list_events` for today in the user's timezone), list each event as `HH:MM Title - attendees`. Link attendees who have a profile in `Company/Org/People/`; leave others as plain names. No connector: skip silently.
3. **Focus**: collect cards due today or overdue (`@{date}`) from `Personal/My Board.md` and cards assigned to me on my team board, plus yesterday's `## Tomorrow` items. Propose a top three, each linked to the KR it moves (`[[<objective>#^krN]]`) from the objectives I own or my team owns this quarter. Ask before dropping a carried-over item.
4. **Captures**: add decisions, people, and tasks from the current conversation under `## Notes and captures`. New tasks go to `Personal/My Board.md` (Inbox column) as cards.
5. **Prep links**: for each meeting today that has an existing note or a 1:1 file (`Personal/1-1s/1-1 - <Person>.md`), link it, and link each attendee's stakeholder note (`Personal/Stakeholders/Stakeholder - <Person>.md`) when one exists.
6. **Stakeholder follow-ups**: list stakeholder notes whose `follow_up:` is today or earlier, with the open asks, under `## Notes and captures`. Ask before moving a follow-up date.
7. Return the path, the top three, follow-ups due, and anything overdue.

Do not write to Company/ or Teams/ in this skill, except moving my own cards on my team board when the user asks.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
