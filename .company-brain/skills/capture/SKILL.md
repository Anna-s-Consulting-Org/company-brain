---
name: capture
description: Capture an idea in seconds - appends to a related idea note if one exists, otherwise writes a short personal idea note in Personal/Notes, and mentions it in today's daily note; later the idea can become an opportunity, a solution, or a project, or be promoted. Use for "capture this", "quick idea", "note this idea", "jot this down", "idea:".
---

# Capture

Zero friction: one idea, one line or a few, saved where it can be found again. The idea is personal until the user decides otherwise. Enrichment happens later, when the idea graduates.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. **Take the idea** from the argument. With no argument, take the most recent idea, thought, or "what if" from the conversation and say which one you picked. A task is not an idea: send it to `Personal/My Board.md` (Inbox) as a card instead (`board` skill), and say so.
2. **Search for a related idea** (`brain search "<key words>"`, then `grep -ril` in `Personal/Notes/` for the main terms). If a note on the same idea exists, append a dated bullet (`- YYYY-MM-DD: <the new angle>`) under its `## Idea` section, and stop at step 5.
3. **Create the note**: `brain new knowledge --title "Idea - <Short title>" --layer personal --set source_type=conversation --set source_path=conversation --set confidence=speculation`. Then edit it:
   - add `idea` to `tags` (`tags: [knowledge, idea]`);
   - replace the template preamble with 2-3 sentences: what the idea is, where it came from (this conversation, today's date), and that it is unvalidated;
   - replace the template sections with `## Idea` (the idea in the user's words, no embellishment), `## Context` (what prompted it, with `[[wikilinks]]` to the people, projects, objectives, or opportunities it touches), and `## Next step` (`TBD`, or one of: explore as an opportunity with `ost`, turn into a project with `project`, share with `promote`).
4. Do not research, score, or expand the idea now. Do not invent context the conversation did not give.
5. **Mention it in today's daily note** under `## Notes and captures` (`brain new daily` if the note does not exist): `- Idea: [[Idea - <Short title>]]`.
6. Return the path in one line. If the idea plainly answers a customer problem or serves a current key result, say which and offer the next step; do not take it unasked.

The note stays in `Personal/`. Sharing it with a team or the company is the `promote` skill's job, on the user's explicit yes.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
