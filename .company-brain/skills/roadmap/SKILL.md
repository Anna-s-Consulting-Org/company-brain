---
name: roadmap
description: Maintain an outcome-based Now, Next, Later roadmap for the company or a team - syncs cards with solutions and projects, keeps each card tied to the key result it serves, moves shipped work, and summarizes the roadmap. Use for "roadmap", "update the roadmap", "what's now next later", "move X to now".
argument-hint: "[company | team]"
---

# Roadmap

Theory: `System/Frameworks/Now-Next-Later Roadmap.md`. Boards: `Company/Roadmap/Company Roadmap.md`, `Teams/<Team>/<Team> Roadmap.md` (Kanban plugin format: columns `## Now`, `## Next`, `## Later`, `## ✅ Shipped`).

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Card format
```markdown
- [ ] **<Title>** · [[SOL - ...]] or [[Project]]
	Outcome: <what changes for customers> · KR [[<objective>#^krN]] · Owner [[<Person>]]
```
The board file has no preamble (kanban exception). Never put a `## For future agent` heading in it.

## Steps
1. Read the board and every solution and project in the layer with `roadmap:` set.
2. **Sync**: each item with `roadmap: now|next|later` has exactly one card in that column; each card links its note. Report cards without a note and notes without a card, and fix with the user.
3. **Moves**: when the user moves an item, update both the card and the note's `roadmap:` (and `status:`: `planned` for Next and Now, `building` when work starts). A project starting work gets a `project` note if it has none.
4. **Shipped**: move to `## ✅ Shipped` as `- [x] ~~**Title**~~ ✅ <Mon DD>` with the result; set the note's status `shipped` and record the outcome (did the KR move?) in the note.
5. **Check**: Now should fit capacity (ask how many items the team can run in parallel); every Now card serves a current KR; Later items older than two quarters are candidates to drop.
6. Summarize: Now (with owners), Next, notable Later, and anything that lost its KR.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
